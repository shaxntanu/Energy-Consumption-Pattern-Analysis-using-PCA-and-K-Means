"""
Analysis Orchestration Module

Runs the whole pipeline in one place and returns a single AnalysisResults object.
Everything downstream, including the dashboard, reads from that object, so there
is exactly one set of numbers in play at any time: the numbers from the most
recent run.

Pipeline order:

    generate -> preprocess -> engineer features -> select feature group
    -> standardize and fit PCA -> sweep K and select -> profile clusters
    -> derive recommendations -> validate against the hidden archetypes

The last step is only possible because the data is synthetic. It compares the
recovered clusters with the archetypes the generator used, which is a check on
the analysis and not part of it: the archetype column is dropped before
preprocessing and never reaches the scaler, PCA or K-Means.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from cluster_profiling import cluster_load_shapes, run_cluster_profiling
from clustering import run_clustering_pipeline
from data_loader import generate_synthetic_data
from feature_engineering import engineer_all_features, select_features
from pca_analysis import loading_table, run_pca_pipeline
from preprocessing import preprocess_pipeline
from recommendation_engine import run_recommendation_engine
from validation import recovery_crosstab, run_validation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARCHETYPE_COL = 'archetype'


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
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]


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
        logger.info("=" * 70)

        dirs = ensure_output_dirs(config.output_dir, config.model_dir)

        logger.info("[1/8] Generating synthetic data")
        raw_data = generate_synthetic_data(
            n_consumers=config.n_consumers,
            n_days=config.n_days,
            hourly_records=config.hourly_records,
            random_seed=config.random_seed,
        )

        true_archetypes = None
        if ARCHETYPE_COL in raw_data.columns:
            true_archetypes = raw_data.groupby('consumer_id')[ARCHETYPE_COL].first()

        logger.info("[2/8] Preprocessing")
        preprocessed = preprocess_pipeline(
            raw_data.drop(columns=[ARCHETYPE_COL], errors='ignore'),
            remove_outliers_flag=config.remove_outliers,
        )

        logger.info("[3/8] Engineering features")
        features = engineer_all_features(preprocessed, feature_set=config.feature_set)
        features_selected = select_features(features, feature_group=config.feature_set)
        feature_names = [c for c in features_selected.columns if c != 'consumer_id']
        consumer_order = features_selected['consumer_id'].tolist()

        logger.info("[4/8] Standardizing and fitting PCA")
        X_pca, pca_model, scaler, n_components = run_pca_pipeline(
            features_selected,
            variance_threshold=config.pca_variance_threshold,
            output_dir=str(dirs['figures']),
            model_dir=str(dirs['models']),
            metrics_dir=str(dirs['metrics']),
        )
        loadings = loading_table(pca_model, feature_names)

        logger.info("[5/8] Sweeping K and selecting")
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

        logger.info("[6/8] Profiling clusters")
        features_combined = engineer_all_features(preprocessed, feature_set='combined')
        features_combined = features_combined.set_index('consumer_id').reindex(consumer_order).reset_index()
        profiles, insights, baseline = run_cluster_profiling(
            features_combined, labels,
            output_dir=str(dirs['reports']),
            metrics_dir=str(dirs['metrics']),
        )
        shapes = cluster_load_shapes(features_combined, labels)

        logger.info("[7/8] Deriving recommendations")
        recommendations = run_recommendation_engine(
            profiles, baseline, output_dir=str(dirs['reports'])
        )

        logger.info("[8/8] Validating against the hidden archetypes")
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

        metadata = {
            'dataset_source': 'SYNTHETIC, generated by src/data_loader.py',
            'experiment_name': config.experiment_name,
            'config_hash': config.config_hash(),
            'random_seed': config.random_seed,
            'n_consumers': config.n_consumers,
            'n_days': config.n_days,
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
        )

        logger.info("=" * 70)
        logger.info(
            f"Finished: K={clustering.optimal_k}, sizes={np.bincount(labels).tolist()}, "
            f"silhouette={clustering.silhouette_by_k[clustering.optimal_k]:.4f}"
        )
        logger.info("=" * 70)

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
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    analysis = EnergyAnalysis(AnalysisConfig(
        n_consumers=200,
        n_days=30,
        feature_set='behavioral',
        test_stability=True,
        experiment_name='behavioral_primary',
    ))
    results = analysis.run()
    analysis.save_summary()

    print("\nSummary:")
    for key, value in analysis.get_summary().items():
        print(f"  {key}: {value}")
