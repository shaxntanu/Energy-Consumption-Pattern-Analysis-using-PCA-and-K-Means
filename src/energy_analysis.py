"""
Analysis Orchestration Module

Runs the whole pipeline in one place and returns a single AnalysisResults object.
Everything downstream, including the dashboard, reads from that object, so there
is exactly one set of numbers in play at any time: the numbers from the most
recent run.

This is the IMPROVED copy of the project. Two future improvements are wired in on
top of the original pipeline:

    1. Longer / configurable observation period. AnalysisConfig gains `start_date`
       (first day of the window) and `n_days` is documented against the horizons
       in data_loader.VALID_HORIZONS_DAYS (30/90/180/365). When the window is long
       enough (>= LONGITUDINAL_MIN_DAYS) a longitudinal analysis step measures how
       stable the recovered clusters are across time within that window.

    2. Interpretable seasonal variation. AnalysisConfig gains a `seasonal`
       SeasonalConfig (default: enabled). The generator applies a documented
       seasonal model (magnitude swing + a shift of the daily peak hours, both
       drawn per-consumer independently of archetype). A seasonal analysis step
       then estimates the magnitude channel and the timing channel from the data
       and, when the hidden seasonal_phase column is present, validates its
       estimate against it, exactly as the archetype check validates clustering.

Both improvements only ADD steps and metadata; the core pipeline order is
unchanged and the dashboard continues to read from AnalysisResults.

Pipeline order:

    generate -> preprocess -> engineer features -> select feature group
    -> standardize and fit PCA -> sweep K and select
    -> [Bonus] explain the clusters (post-hoc XAI/SHAP surrogate)
    -> profile clusters -> derive recommendations -> validate against the hidden archetypes
    -> [Improvement 2] seasonal analysis
    -> [Improvement 1] longitudinal analysis (long windows only)

Every committed run also exports the stable web/ artifact contract (manifest.json
plus the pca/clustering/profiles/validation/seasonal/longitudinal/explainability
JSON files under web/public/data/), which the Vercel explorer reads. See
export_artifacts.py.

The archetype check in the validation step is only possible because the data is
synthetic. It compares the recovered clusters with the archetypes the generator
used, which is a check on the analysis and not part of it: the archetype column
(and the hidden seasonal_phase column) are dropped before preprocessing and never
reach the scaler, PCA or K-Means.
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from cluster_profiling import cluster_load_shapes, run_cluster_profiling
from clustering import run_clustering_pipeline
from data_loader import SeasonalConfig, VALID_HORIZONS_DAYS, generate_synthetic_data
from explainability import run_explainability
from export_artifacts import export_artifacts
from feature_engineering import engineer_all_features, select_features
from longitudinal_analysis import run_longitudinal_analysis
from pca_analysis import loading_table, run_pca_pipeline
from preprocessing import preprocess_pipeline
from recommendation_engine import run_recommendation_engine
from seasonal_analysis import run_seasonal_analysis
from validation import recovery_crosstab, run_validation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARCHETYPE_COL = 'archetype'
SEASONAL_PHASE_COL = 'seasonal_phase'
SEASON_COL = 'season'

# Longitudinal analysis needs a long enough window to be split into several
# meaningful segments. Short windows are the original 30-day baseline and the
# one-season 90-day horizon; 180 days (two seasons) and 365 days (a full year)
# are where longitudinal structure becomes meaningful.
LONGITUDINAL_MIN_DAYS = 180


def ensure_output_dirs(base: str = 'outputs', model_dir: str = 'models') -> dict:
    """Create every directory the pipeline writes to.

    Args:
        base: Root output directory.
        model_dir: Directory for fitted models.

    Returns:
        Mapping of role to Path.
    """
    paths = {
        'figures': Path(base) / 'figures',
        'metrics': Path(base) / 'metrics',
        'reports': Path(base) / 'reports',
        'models': Path(model_dir),
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def get_package_versions() -> dict:
    """Return the installed version of every package the results depend on."""
    versions = {}
    for name, module_name in [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('scikit-learn', 'sklearn'),
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
        ('plotly', 'plotly'),
        ('streamlit', 'streamlit'),
        ('joblib', 'joblib'),
    ]:
        try:
            module = __import__(module_name)
            versions[name] = getattr(module, '__version__', 'unknown')
        except ImportError:
            versions[name] = 'not-installed'
    return versions


@dataclass
class AnalysisConfig:
    """Every choice that affects the numbers, in one place.

    Attributes:
        n_consumers: Consumers to generate.
        n_days: Days of data per consumer.
        hourly_records: Hourly records when True, one record per day when False.
        random_seed: Seed for generation and for every model fit.
        feature_set: 'behavioral', 'scale' or 'combined'. The primary experiment
            is behavioral; the other two exist for the ablation study.
        pca_variance_threshold: Cumulative variance target for component count.
        k_range: Half-open (min, max) range of candidate K.
        test_stability: Whether to measure multi-seed stability at every K.
        output_dir: Root output directory.
        model_dir: Directory for fitted models.
        remove_outliers: Whether preprocessing drops extreme records. Default
            False, because a genuine consumption spike is behaviour, not an error.
        experiment_name: Label recorded in the metadata.
        start_date: First day of the observation window (Improvement 1).
        seasonal: Seasonal model (Improvement 2). None or
            SeasonalConfig(enabled=False) disables it.
        run_longitudinal: Whether to run the longitudinal analysis step for long
            windows (Improvement 1). Only actually runs when n_days >=
            LONGITUDINAL_MIN_DAYS.
    """

    n_consumers: int = 200
    n_days: int = 30
    hourly_records: bool = True
    random_seed: int = 42
    feature_set: str = 'behavioral'
    pca_variance_threshold: float = 0.95
    k_range: tuple = (2, 11)
    test_stability: bool = True
    output_dir: str = 'outputs'
    model_dir: str = 'models'
    remove_outliers: bool = False
    experiment_name: str = 'behavioral_primary'
    start_date: str = '2024-01-01'
    seasonal: Optional[SeasonalConfig] = field(default_factory=SeasonalConfig)
    run_longitudinal: bool = True

    def config_hash(self) -> str:
        """Short deterministic hash of every field that changes the results.

        Used to invalidate cached dashboard state. Fields that only affect where
        files are written are excluded, since they do not change the numbers.

        Returns:
            First 16 hex characters of the SHA-256 of the settings.
        """
        payload = {
            'n_consumers': self.n_consumers,
            'n_days': self.n_days,
            'hourly_records': self.hourly_records,
            'random_seed': self.random_seed,
            'feature_set': self.feature_set,
            'pca_variance_threshold': self.pca_variance_threshold,
            'k_range': list(self.k_range),
            'test_stability': self.test_stability,
            'remove_outliers': self.remove_outliers,
            'experiment_name': self.experiment_name,
            'start_date': self.start_date,
            'seasonal': None if self.seasonal is None else asdict(self.seasonal),
            'run_longitudinal': self.run_longitudinal,
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]

    def window_label(self) -> str:
        """Human-readable description of the configured observation window."""
        start = pd.Timestamp(self.start_date)
        end = start + pd.Timedelta(days=self.n_days - 1)
        return f"{start:%Y-%m-%d} to {end:%Y-%m-%d} ({self.n_days} days)"


@dataclass
class AnalysisResults:
    """The complete output of one run. The single source of truth for reporting."""

    raw_data: pd.DataFrame
    preprocessed_data: pd.DataFrame
    features: pd.DataFrame
    features_combined: pd.DataFrame
    feature_names: list
    pca_transformed: np.ndarray
    pca_model: object
    scaler: object
    n_pca_components: int
    pca_loadings: pd.DataFrame
    cluster_labels: np.ndarray
    kmeans_model: object
    optimal_k: int
    k_values: list
    inertia_by_k: dict
    silhouette_by_k: dict
    ch_by_k: dict
    db_by_k: dict
    stability_by_k: dict
    k_selection_trace: dict
    cluster_profiles: pd.DataFrame
    cluster_insights: pd.DataFrame
    population_baseline: dict
    cluster_shapes: pd.DataFrame
    recommendations: pd.DataFrame
    true_archetypes: Optional[pd.Series]
    archetype_recovery: Optional[pd.DataFrame]
    archetype_crosstab: Optional[pd.DataFrame]
    config: AnalysisConfig
    metadata: dict
    stability_results: Optional[dict] = field(default=None)
    # Improvements: populated by the seasonal (2) and longitudinal (1) steps.
    seasonal_results: Optional[dict] = field(default=None)
    longitudinal_results: Optional[dict] = field(default=None)
    # Bonus: populated by the post-hoc explainability (XAI/SHAP) step.
    explainability_results: Optional[dict] = field(default=None)

    def silhouette_for_k(self, k: int) -> float:
        """Look up the silhouette score for a given K by key, never by position.

        Args:
            k: Number of clusters.

        Returns:
            Silhouette score.

        Raises:
            KeyError: If that K was not evaluated.
        """
        if k not in self.silhouette_by_k:
            raise KeyError(
                f"No silhouette score stored for K={k}. Evaluated: {sorted(self.silhouette_by_k)}"
            )
        return self.silhouette_by_k[k]

    def cluster_sizes(self) -> list:
        """Cluster sizes in cluster-ID order."""
        return np.bincount(self.cluster_labels, minlength=self.optimal_k).tolist()

    def ari_for_k(self, k: int) -> Optional[float]:
        """Adjusted Rand Index against the hidden archetypes for a given K.

        Returns:
            The ARI, or None when no ground truth is available.
        """
        if self.archetype_recovery is None:
            return None
        match = self.archetype_recovery.loc[self.archetype_recovery['K'] == k, 'ari']
        return float(match.iloc[0]) if len(match) else None


class EnergyAnalysis:
    """Runs the pipeline described in the module docstring."""

    def __init__(self, config: AnalysisConfig):
        """Store the configuration.

        Args:
            config: Settings for this run.
        """
        self.config = config
        self.results: Optional[AnalysisResults] = None
        logger.info(f"Configured run '{config.experiment_name}' (hash {config.config_hash()})")

    def run(self) -> AnalysisResults:
        """Execute every step and persist the artifacts.

        Returns:
            AnalysisResults for this run.
        """
        config = self.config
        logger.info("=" * 70)
        logger.info(f"Starting analysis: {config.experiment_name}")
        logger.info(f"Observation window: {config.window_label()}")
        logger.info("=" * 70)

        dirs = ensure_output_dirs(config.output_dir, config.model_dir)

        logger.info("[1/11] Generating synthetic data")
        raw_data = generate_synthetic_data(
            n_consumers=config.n_consumers,
            n_days=config.n_days,
            hourly_records=config.hourly_records,
            random_seed=config.random_seed,
            start_date=config.start_date,
            seasonal=config.seasonal,
        )

        true_archetypes = None
        if ARCHETYPE_COL in raw_data.columns:
            true_archetypes = raw_data.groupby('consumer_id')[ARCHETYPE_COL].first()

        logger.info("[2/11] Preprocessing")
        # Drop the hidden truth columns (archetype and, when present, the hidden
        # seasonal phase) but KEEP the derived `season` column, which is a
        # legitimate grouping variable for the seasonal/longitudinal analysis.
        hidden_truth_cols = [c for c in (ARCHETYPE_COL, SEASONAL_PHASE_COL)
                             if c in raw_data.columns]
        preprocessed = preprocess_pipeline(
            raw_data.drop(columns=hidden_truth_cols, errors='ignore'),
            remove_outliers_flag=config.remove_outliers,
        )

        logger.info("[3/11] Engineering features")
        features = engineer_all_features(preprocessed, feature_set=config.feature_set)
        features_selected = select_features(features, feature_group=config.feature_set)
        feature_names = [c for c in features_selected.columns if c != 'consumer_id']
        consumer_order = features_selected['consumer_id'].tolist()

        logger.info("[4/11] Standardizing and fitting PCA")
        X_pca, pca_model, scaler, n_components = run_pca_pipeline(
            features_selected,
            variance_threshold=config.pca_variance_threshold,
            output_dir=str(dirs['figures']),
            model_dir=str(dirs['models']),
            metrics_dir=str(dirs['metrics']),
        )
        loadings = loading_table(pca_model, feature_names)

        logger.info("[5/11] Sweeping K and selecting")
        clustering = run_clustering_pipeline(
            X_pca,
            k_range=config.k_range,
            random_state=config.random_seed,
            test_stability=config.test_stability,
            output_dir=str(dirs['figures']),
            model_dir=str(dirs['models']),
            metrics_dir=str(dirs['metrics']),
        )
        labels = clustering.labels

        # Bonus: explain the clusters in feature units. A small post-hoc surrogate
        # forest predicts the recovered labels from the same behavioural features
        # the pipeline used, and SHAP (or a permutation fallback) explains it. The
        # surrogate never feeds back into PCA or K-Means, so this step cannot
        # change any cluster.
        logger.info("[6/11] Explaining the clusters (XAI)")
        explainability_results = run_explainability(
            features_selected, labels,
            feature_names=feature_names,
            output_dir=str(dirs['figures']),
            reports_dir=str(dirs['reports']),
            metrics_dir=str(dirs['metrics']),
        )

        logger.info("[7/11] Profiling clusters")
        features_combined = engineer_all_features(preprocessed, feature_set='combined')
        features_combined = features_combined.set_index('consumer_id').reindex(consumer_order).reset_index()
        profiles, insights, baseline = run_cluster_profiling(
            features_combined, labels,
            output_dir=str(dirs['reports']),
            metrics_dir=str(dirs['metrics']),
        )
        shapes = cluster_load_shapes(features_combined, labels)

        logger.info("[8/11] Deriving recommendations")
        recommendations = run_recommendation_engine(
            profiles, baseline, output_dir=str(dirs['reports'])
        )

        logger.info("[9/11] Validating against the hidden archetypes")
        recovery, crosstab = None, None
        if true_archetypes is not None:
            truth = true_archetypes.reindex(consumer_order).to_numpy()
            recovery = run_validation(
                X_pca, labels, truth,
                selected_k=clustering.optimal_k,
                k_values=clustering.k_values,
                random_state=config.random_seed,
                output_dir=config.output_dir,
            )
            crosstab = recovery_crosstab(labels, truth)
        else:
            logger.warning("No archetype column found, skipping the ground-truth check")

        # Improvement 2: seasonal analysis. Runs when the seasonal model is
        # enabled. Estimates the magnitude and timing channels from the data and,
        # when the raw data carries the hidden seasonal_phase column, validates
        # its phase estimate against it.
        logger.info("[10/11] Seasonal analysis")
        seasonal_results = None
        if config.seasonal is not None and config.seasonal.enabled:
            seasonal_results = run_seasonal_analysis(
                raw_data=raw_data,
                preprocessed=preprocessed,
                labels=labels,
                consumer_order=consumer_order,
                output_dir=str(dirs['figures']),
                reports_dir=str(dirs['reports']),
                metrics_dir=str(dirs['metrics']),
            )
        else:
            logger.info("Seasonal analysis skipped (seasonality disabled)")

        # Improvement 1: longitudinal analysis. Only meaningful for long windows.
        logger.info("[11/11] Longitudinal analysis")
        longitudinal_results = None
        if config.run_longitudinal and config.n_days >= LONGITUDINAL_MIN_DAYS:
            longitudinal_results = run_longitudinal_analysis(
                preprocessed=preprocessed,
                labels=labels,
                consumer_order=consumer_order,
                optimal_k=clustering.optimal_k,
                random_seed=config.random_seed,
                output_dir=str(dirs['figures']),
                reports_dir=str(dirs['reports']),
                metrics_dir=str(dirs['metrics']),
            )
        else:
            logger.info(
                f"Longitudinal analysis skipped: needs >= {LONGITUDINAL_MIN_DAYS} days "
                f"(have {config.n_days}). Try one of the longer horizons {list(VALID_HORIZONS_DAYS)}."
            )

        metadata = {
            'dataset_source': 'SYNTHETIC, generated by src/data_loader.py',
            'experiment_name': config.experiment_name,
            'config_hash': config.config_hash(),
            'random_seed': config.random_seed,
            'n_consumers': config.n_consumers,
            'n_days': config.n_days,
            'window_start': str(pd.Timestamp(config.start_date).date()),
            'window_label': config.window_label(),
            'seasonal': None if config.seasonal is None else asdict(config.seasonal),
            'n_records': int(len(preprocessed)),
            'feature_set': config.feature_set,
            'n_features': len(feature_names),
            'feature_list': feature_names,
            'pca_variance_threshold': config.pca_variance_threshold,
            'pca_components': int(n_components),
            'pca_cumulative_variance': float(np.cumsum(pca_model.explained_variance_ratio_)[-1]),
            'k_range': list(config.k_range),
            'selected_k': int(clustering.optimal_k),
            'k_selection_trace': clustering.selection_trace,
            'silhouette_at_selected_k': clustering.silhouette_by_k[clustering.optimal_k],
            'cluster_sizes': np.bincount(labels).tolist(),
            'cluster_names': profiles['cluster_name'].tolist(),
            'stability_at_selected_k': clustering.stability,
            'ari_vs_archetypes_at_selected_k': (
                float(recovery.loc[recovery['K'] == clustering.optimal_k, 'ari'].iloc[0])
                if recovery is not None else None
            ),
            'seasonal_amplitude_estimate': (
                seasonal_results.get('amplitude_estimate')
                if seasonal_results and seasonal_results.get('seasonal') else None
            ),
            'seasonal_phase_recovery_corr': (
                seasonal_results.get('phase_recovery_corr')
                if seasonal_results and seasonal_results.get('seasonal') else None
            ),
            'longitudinal_temporal_stability_ari': (
                longitudinal_results.get('mean_temporal_stability_ari')
                if longitudinal_results else None
            ),
            'explainability_method': (
                explainability_results.get('method')
                if explainability_results and explainability_results.get('method') != 'not_run'
                else None
            ),
            'explainability_cv_accuracy': (
                explainability_results.get('cv_balanced_accuracy')
                if explainability_results else None
            ),
            'n_recommendations': int(len(recommendations)),
            'package_versions': get_package_versions(),
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        }
        self._save_metadata(metadata, dirs['models'] / 'analysis_metadata.json')

        self.results = AnalysisResults(
            raw_data=raw_data,
            preprocessed_data=preprocessed,
            features=features,
            features_combined=features_combined,
            feature_names=feature_names,
            pca_transformed=X_pca,
            pca_model=pca_model,
            scaler=scaler,
            n_pca_components=n_components,
            pca_loadings=loadings,
            cluster_labels=labels,
            kmeans_model=clustering.model,
            optimal_k=clustering.optimal_k,
            k_values=clustering.k_values,
            inertia_by_k=clustering.inertia_by_k,
            silhouette_by_k=clustering.silhouette_by_k,
            ch_by_k=clustering.ch_by_k,
            db_by_k=clustering.db_by_k,
            stability_by_k=clustering.stability_by_k,
            k_selection_trace=clustering.selection_trace,
            cluster_profiles=profiles,
            cluster_insights=insights,
            population_baseline=baseline,
            cluster_shapes=shapes,
            recommendations=recommendations,
            true_archetypes=true_archetypes,
            archetype_recovery=recovery,
            archetype_crosstab=crosstab,
            config=config,
            metadata=metadata,
            stability_results=clustering.stability,
            seasonal_results=seasonal_results,
            longitudinal_results=longitudinal_results,
            explainability_results=explainability_results,
        )

        logger.info("=" * 70)
        logger.info(
            f"Finished: K={clustering.optimal_k}, sizes={np.bincount(labels).tolist()}, "
            f"silhouette={clustering.silhouette_by_k[clustering.optimal_k]:.4f}"
        )
        if seasonal_results and seasonal_results.get('seasonal'):
            logger.info(f"  seasonal: amplitude estimate {seasonal_results['amplitude_estimate']:.3f}")
        elif seasonal_results and not seasonal_results.get('seasonal'):
            logger.info(f"  seasonal: skipped ({seasonal_results.get('reason', 'no season column')})")
        if longitudinal_results:
            logger.info(
                f"  longitudinal: temporal stability ARI "
                f"{longitudinal_results['mean_temporal_stability_ari']:.4f}"
            )
        else:
            logger.info("  longitudinal: skipped (requires >= 180-day window)")
        if explainability_results and explainability_results.get('method') != 'not_run':
            logger.info(
                f"  explainability: {explainability_results['method']} "
                f"(surrogate cv balanced accuracy "
                f"{explainability_results.get('cv_balanced_accuracy', float('nan')):.3f})"
            )
        logger.info("=" * 70)

        # Every committed run leaves the stable web/ artifact contract behind, so
        # the Vercel explorer always describes the same run as the README.
        try:
            exported = export_artifacts()
            logger.info(
                f"Artifact contract exported: {len(exported) - 2} JSON files, "
                f"{len(exported.get('csv_mirrors', []))} CSV mirrors"
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Could not export the artifact contract: {exc}")

        return self.results

    @staticmethod
    def _save_metadata(metadata: dict, path: Path) -> None:
        """Write the run metadata as JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(metadata, indent=2, default=str), encoding='utf-8')
        logger.info(f"Run metadata saved to {path}")

    def get_summary(self) -> dict:
        """Return the headline numbers for this run.

        Raises:
            ValueError: If run() has not been called.
        """
        if self.results is None:
            raise ValueError("Analysis has not been run yet. Call run() first.")

        results = self.results
        return {
            'experiment_name': self.config.experiment_name,
            'config_hash': self.config.config_hash(),
            'n_consumers': self.config.n_consumers,
            'n_days': self.config.n_days,
            'window_label': self.config.window_label(),
            'n_records': len(results.preprocessed_data),
            'feature_set': self.config.feature_set,
            'n_features': len(results.feature_names),
            'n_pca_components': results.n_pca_components,
            'pca_cumulative_variance': results.metadata['pca_cumulative_variance'],
            'optimal_k': results.optimal_k,
            'silhouette_at_optimal': results.silhouette_for_k(results.optimal_k),
            'cluster_sizes': results.cluster_sizes(),
            'stability_ari': (results.stability_results or {}).get('mean_ari'),
            'ari_vs_archetypes': results.ari_for_k(results.optimal_k),
            'n_recommendations': len(results.recommendations),
            'seasonal_enabled': bool(results.seasonal_results),
            'seasonal_amplitude_estimate': (
                results.seasonal_results.get('amplitude_estimate')
                if results.seasonal_results else None
            ),
            'seasonal_phase_recovery_corr': (
                results.seasonal_results.get('phase_recovery_corr')
                if results.seasonal_results else None
            ),
            'longitudinal_temporal_stability_ari': (
                results.longitudinal_results.get('mean_temporal_stability_ari')
                if results.longitudinal_results else None
            ),
            'explainability_method': (
                results.explainability_results.get('method')
                if results.explainability_results
                and results.explainability_results.get('method') != 'not_run'
                else None
            ),
            'explainability_cv_accuracy': (
                results.explainability_results.get('cv_balanced_accuracy')
                if results.explainability_results else None
            ),
        }

    def save_summary(self, output_path: Optional[str] = None) -> Path:
        """Write the authoritative results summary in markdown.

        This file is the one place other documents should quote numbers from.

        Args:
            output_path: Destination. Defaults to
                <output_dir>/reports/analysis_summary.md.

        Returns:
            The path written.

        Raises:
            ValueError: If run() has not been called.
        """
        if self.results is None:
            raise ValueError("Analysis has not been run yet. Call run() first.")

        results = self.results
        summary = self.get_summary()
        path = (Path(output_path) if output_path
                else Path(self.config.output_dir) / 'reports' / 'analysis_summary.md')
        path.parent.mkdir(parents=True, exist_ok=True)

        trace = results.k_selection_trace
        baseline = results.population_baseline

        lines = [
            "# Analysis Summary",
            "",
            "This file is generated by the pipeline and is the authoritative record of the",
            "most recent run. Every number quoted in the README, the docs or the dashboard",
            "should match this file. If they disagree, this file is right and the other",
            "document is stale.",
            "",
            "THIS IS SYNTHETIC DATA. The consumers below do not exist. Nothing here is",
            "evidence about real-world household behaviour.",
            "",
            "## Run configuration",
            "",
            f"- Experiment: {summary['experiment_name']}",
            f"- Config hash: {summary['config_hash']}",
            f"- Consumers: {summary['n_consumers']}",
            f"- Days: {summary['n_days']}",
            f"- Observation window: {summary['window_label']}",
            f"- Records after preprocessing: {summary['n_records']:,}",
            f"- Feature set: {summary['feature_set']}",
            f"- Random seed: {self.config.random_seed}",
            f"- Package versions: "
            + ", ".join(f"{k} {v}" for k, v in results.metadata['package_versions'].items()),
            f"- Generated: {results.metadata['timestamp_utc']}",
            "",
            "## Dimensionality reduction",
            "",
            f"- Features into PCA: {summary['n_features']}",
            f"- Components retained: {summary['n_pca_components']} "
            f"(target {self.config.pca_variance_threshold:.0%} cumulative variance)",
            f"- Cumulative variance retained: {summary['pca_cumulative_variance']:.4f}",
            "",
            "## Choice of K",
            "",
            f"- Candidates evaluated: K = {min(results.k_values)} to {max(results.k_values)}",
            f"- Selected K: {summary['optimal_k']}",
            f"- Silhouette at selected K: {summary['silhouette_at_optimal']:.4f}",
            f"- Cluster sizes: {summary['cluster_sizes']}",
        ]

        if summary['stability_ari'] is not None:
            stability = results.stability_results
            lines.append(
                f"- Stability across {stability['n_runs']} restarts: mean pairwise ARI "
                f"{stability['mean_ari']:.4f} (sd {stability['std_ari']:.4f}), "
                f"assignment agreement {stability['mean_agreement']:.3f}"
            )
        if trace.get('elbow_k') is not None:
            lines.append(f"- Inertia elbow, reported for comparison: K={int(trace['elbow_k'])}")
        if trace.get('after_balance_filter'):
            rejected = sorted(set(trace['candidates']) - set(trace['after_balance_filter']))
            if rejected:
                lines.append(f"- Rejected for producing a cluster below 5% of consumers: K={rejected}")
        if trace.get('relaxed_filters'):
            lines.append(
                f"- Filters that had to be relaxed because no candidate passed: "
                f"{trace['relaxed_filters']}. Treat this run's K as weakly supported."
            )

        lines += [
            "",
            "### Full sweep",
            "",
            "| K | Inertia | Silhouette | Calinski-Harabasz | Davies-Bouldin | Stability ARI |",
            "| - | ------- | ---------- | ----------------- | -------------- | ------------- |",
        ]
        for k in results.k_values:
            stability = results.stability_by_k.get(k, {})
            ari = stability.get('mean_ari')
            marker = " (selected)" if k == results.optimal_k else ""
            lines.append(
                f"| {k}{marker} | {results.inertia_by_k[k]:.1f} | "
                f"{results.silhouette_by_k[k]:.4f} | {results.ch_by_k[k]:.1f} | "
                f"{results.db_by_k[k]:.4f} | "
                + (f"{ari:.4f} |" if ari is not None else "not measured |")
            )

        lines += ["", "## Cluster profiles", ""]
        for _, profile in results.cluster_profiles.iterrows():
            lines += [
                f"### Cluster {int(profile['cluster'])}: {profile['cluster_name']}",
                "",
                f"- Size: {int(profile['size'])} consumers ({profile['size_share']:.1%})",
            ]
            if 'peak_hour' in profile:
                lines.append(f"- Peak hour of the mean load shape: {int(profile['peak_hour'])}")
            for label, key in [
                ('Evening share of daily energy', 'evening_share'),
                ('Afternoon share', 'afternoon_share'),
                ('Morning share', 'morning_share'),
                ('Night share', 'night_share'),
                ('Weekend to weekday energy ratio', 'weekend_ratio'),
                ('Peak-to-average ratio', 'peak_to_avg_ratio'),
                ('Coefficient of variation', 'coefficient_of_variation'),
                ('Mean kWh per record (context only)', 'mean_kwh'),
            ]:
                if key in profile and pd.notna(profile[key]):
                    reference = baseline.get(key)
                    suffix = f" (population {reference:.4f})" if reference else ""
                    lines.append(f"- {label}: {profile[key]:.4f}{suffix}")
            lines.append("")

        if results.archetype_recovery is not None:
            lines += [
                "## Validation against the hidden archetypes",
                "",
                "The generator assigned each consumer a latent archetype. That column is",
                "dropped before preprocessing and never reaches the scaler, PCA or K-Means,",
                "so comparing it with the recovered clusters is an independent check. This",
                "check exists only because the data is synthetic; it is not available on a",
                "real dataset.",
                "",
                "| K | Adjusted Rand Index | Normalized Mutual Information |",
                "| - | ------------------- | ----------------------------- |",
            ]
            for _, row in results.archetype_recovery.iterrows():
                marker = " (selected)" if int(row['K']) == results.optimal_k else ""
                lines.append(f"| {int(row['K'])}{marker} | {row['ari']:.4f} | {row['nmi']:.4f} |")
            lines += [
                "",
                f"At the selected K={results.optimal_k} the Adjusted Rand Index against the "
                f"archetypes is {summary['ari_vs_archetypes']:.4f}.",
                "",
                "### Cluster against archetype",
                "",
                "```",
                results.archetype_crosstab.to_string(),
                "```",
                "",
            ]

        # Bonus: explainability (XAI) block.
        explain = getattr(results, 'explainability_results', None)
        if explain and explain.get('method') and explain.get('method') != 'not_run':
            lines += [
                "## Explainability (XAI / SHAP)",
                "",
                "The clustering is unsupervised and has no feature importance. A small",
                "post-hoc surrogate forest predicts the recovered cluster labels from the",
                "same behavioural features the pipeline used, and the surrogate is then",
                "explained in feature units. The surrogate never feeds back into PCA or",
                "K-Means, so it cannot change any cluster.",
                "",
                f"- Method: {explain.get('method')}",
                f"- Cross-validated balanced accuracy of the surrogate: "
                f"{explain.get('cv_balanced_accuracy'):.3f} (the honest ceiling on how "
                f"much of the grouping the features can be said to explain)",
                "- Details: reports/explainability_report.md, outputs/metrics/explainability.json",
                "",
            ]

        # Improvement 2: seasonal analysis block.
        seasonal = getattr(results, 'seasonal_results', None)
        if seasonal:
            if seasonal.get('seasonal'):
                s = seasonal
                lines += [
                    "## Seasonal analysis (Improvement 2)",
                    "",
                    "The seasonal model has two separately-estimated channels, both drawn per",
                    "consumer independently of archetype. Estimates below are made from the data",
                    "alone; when the hidden seasonal_phase column is present it is used only as",
                    "an independent check.",
                    "",
                    f"- Mean daily kWh by season: {s.get('mean_daily_kwh_by_season')}",
                    f"- Estimated magnitude amplitude (fractional daily swing): "
                    f"{(s.get('amplitude_estimate') if s.get('amplitude_estimate') is not None else float('nan')):.4f}",
                    f"- Mean peak hour by season: {s.get('peak_hour_by_season')}",
                ]
                if s.get('phase_recovery_corr') is not None:
                    lines.append(
                        f"- Seasonal phase recovery: Pearson r = {s['phase_recovery_corr']:.4f}, "
                        f"peak-season agreement {s['phase_accuracy']:.3f} "
                        f"(hidden seasonal_phase used as ground truth, available only because "
                        f"the data is synthetic)."
                    )
                lines.append(
                    "- The magnitude channel is mean-corrected over the window, so it cannot inflate "
                    "or create a spurious cluster from scale differences. The timing channel shifts "
                    "the daily peak hours and is what changes the normalized load shape across seasons."
                )
                lines.append("")
            else:
                lines += [
                    "## Seasonal analysis (Improvement 2)",
                    "",
                    f"Skipped: {seasonal.get('reason', 'no season column')}.",
                    "",
                ]

        # Improvement 1: longitudinal analysis block.
        longitudinal = getattr(results, 'longitudinal_results', None)
        if longitudinal is not None:
            lines += [
                "## Longitudinal analysis (Improvement 1)",
                "",
                "The observation window was split into time segments; behavioural features were",
                "re-engineered and re-clustered within each segment, and the recovered labels were",
                "compared with the full-window labels.",
                "",
                f"- Segments: {longitudinal.get('n_segments')} (window {summary['window_label']})",
                f"- Temporal cluster stability (mean ARI of segment labels vs full window): "
                f"{longitudinal.get('mean_temporal_stability_ari'):.4f}",
                f"- Per-segment ARI: {longitudinal.get('segment_ari_vs_full')}",
                f"- Mean daily kWh by month: {longitudinal.get('monthly_mean_daily_kwh')}",
                "",
            ]

        lines += [
            "## Recommendations",
            "",
            f"- Rows generated: {summary['n_recommendations']}",
            "- See reports/recommendations_report.md. No savings figures and no causal",
            "  claims are made anywhere in that file.",
            "",
        ]

        path.write_text("\n".join(lines), encoding='utf-8')
        logger.info(f"Analysis summary saved to {path}")
        return path


if __name__ == "__main__":
    import argparse
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    parser = argparse.ArgumentParser(description="Energy consumption pattern analysis")
    parser.add_argument('--n_days', type=int, default=30,
                        help='Observation window length in days (default 30). '
                             'Use 365 to exercise Improvements 1+2 end-to-end.')
    parser.add_argument('--n_consumers', type=int, default=200)
    args = parser.parse_args()

    analysis = EnergyAnalysis(AnalysisConfig(
        n_consumers=args.n_consumers,
        n_days=args.n_days,
        feature_set='behavioral',
        test_stability=True,
        experiment_name='behavioral_primary',
    ))
    results = analysis.run()
    analysis.save_summary()

    print("\nSummary:")
    for key, value in analysis.get_summary().items():
        print(f"  {key}: {value}")