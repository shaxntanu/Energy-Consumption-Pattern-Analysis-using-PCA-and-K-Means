"""
Unified Energy Consumption Analysis Module
Orchestrates the complete analysis pipeline from data to recommendations.
"""

import json
import hashlib
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from data_loader import generate_synthetic_data
from preprocessing import preprocess_pipeline
from feature_engineering import engineer_all_features, select_features
from pca_analysis import run_pca_pipeline
from clustering import run_clustering_pipeline
from cluster_profiling import run_cluster_profiling
from recommendation_engine import run_recommendation_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_output_dirs(base: str = 'outputs', model_dir: str = 'models') -> dict:
    """Create all required output directories before writing artifacts."""
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
    """Return pinned package versions currently installed."""
    versions = {}
    for name, module_name in [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('scikit-learn', 'sklearn'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
        ('plotly', 'plotly'),
        ('streamlit', 'streamlit'),
        ('joblib', 'joblib'),
    ]:
        try:
            mod = __import__(module_name)
            versions[name] = getattr(mod, '__version__', 'unknown')
        except ImportError:
            versions[name] = 'not-installed'
    return versions


@dataclass
class AnalysisConfig:
    """Configuration for energy consumption analysis."""
    n_consumers: int = 200
    n_days: int = 30
    hourly_records: bool = True
    random_seed: int = 42
    feature_set: str = 'behavioral'  # 'behavioral', 'scale', or 'combined'
    pca_variance_threshold: float = 0.95
    k_range: tuple = (2, 11)
    test_stability: bool = True
    output_dir: str = 'outputs'
    model_dir: str = 'models'
    remove_outliers: bool = False
    experiment_name: str = 'behavioral_primary'

    def config_hash(self) -> str:
        """Deterministic hash for session-state invalidation."""
        payload = {
            'n_consumers': self.n_consumers,
            'n_days': self.n_days,
            'hourly_records': self.hourly_records,
            'random_seed': self.random_seed,
            'feature_set': self.feature_set,
            'pca_variance_threshold': self.pca_variance_threshold,
            'k_range': list(self.k_range),
            'remove_outliers': self.remove_outliers,
            'experiment_name': self.experiment_name,
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]


@dataclass
class AnalysisResults:
    """Container for all analysis results — single source of truth for dashboard/offline."""
    raw_data: pd.DataFrame
    preprocessed_data: pd.DataFrame
    features: pd.DataFrame
    feature_names: list
    pca_transformed: np.ndarray
    pca_model: object
    scaler: object
    n_pca_components: int
    cluster_labels: np.ndarray
    kmeans_model: object
    optimal_k: int
    k_values: list
    inertia_by_k: dict
    silhouette_by_k: dict
    ch_by_k: dict
    db_by_k: dict
    stability_results: Optional[dict]
    cluster_profiles: pd.DataFrame
    cluster_insights: pd.DataFrame
    recommendations: pd.DataFrame
    config: AnalysisConfig
    metadata: dict

    def silhouette_for_k(self, k: int) -> float:
        """Explicit K→metric lookup (never positional index assumption)."""
        if k not in self.silhouette_by_k:
            raise KeyError(f"No silhouette score stored for K={k}. Known keys: {sorted(self.silhouette_by_k)}")
        return self.silhouette_by_k[k]


class EnergyAnalysis:
    """
    Unified energy consumption analysis pipeline.
    
    This class orchestrates the complete analysis from data generation
    through clustering to recommendations, using scientifically defensible
    methods throughout.
    """
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.results: Optional[AnalysisResults] = None
        np.random.seed(config.random_seed)
        logger.info(f"Initialized EnergyAnalysis with config: {config}")
    
    def run(self) -> AnalysisResults:
        """Run complete analysis pipeline and persist artifacts + metadata."""
        logger.info("=" * 60)
        logger.info("Starting Energy Consumption Analysis Pipeline")
        logger.info("=" * 60)
        
        dirs = ensure_output_dirs(self.config.output_dir, self.config.model_dir)
        
        # Step 1: Generate or load data
        logger.info("\n[Step 1/7] Data Generation")
        raw_data = generate_synthetic_data(
            n_consumers=self.config.n_consumers,
            n_days=self.config.n_days,
            hourly_records=self.config.hourly_records,
            random_seed=self.config.random_seed
        )
        
        # Step 2: Preprocess
        logger.info("\n[Step 2/7] Preprocessing")
        preprocessed = preprocess_pipeline(
            raw_data.drop(columns=['archetype']),
            remove_outliers_flag=self.config.remove_outliers
        )
        
        # Step 3: Feature Engineering
        logger.info("\n[Step 3/7] Feature Engineering")
        features = engineer_all_features(preprocessed, feature_set=self.config.feature_set)
        features_selected = select_features(features, feature_group=self.config.feature_set)
        feature_names = [c for c in features_selected.columns if c != 'consumer_id']
        
        # Step 4: PCA
        logger.info("\n[Step 4/7] PCA Dimensionality Reduction")
        X_pca, pca_model, scaler, n_components = run_pca_pipeline(
            features_selected,
            variance_threshold=self.config.pca_variance_threshold,
            output_dir=str(dirs['figures']),
            model_dir=str(dirs['models']),
        )
        
        # Step 5: Clustering
        logger.info("\n[Step 5/7] Clustering")
        (kmeans_model, labels, optimal_k, k_values, inertia_values,
         silhouette_scores, ch_scores, db_scores, stability_results) = run_clustering_pipeline(
            X_pca,
            k_range=self.config.k_range,
            test_stability=self.config.test_stability,
            output_dir=str(dirs['figures']),
            model_dir=str(dirs['models']),
        )
        k_values = list(k_values)
        inertia_by_k = dict(zip(k_values, inertia_values))
        silhouette_by_k = dict(zip(k_values, silhouette_scores))
        ch_by_k = dict(zip(k_values, ch_scores))
        db_by_k = dict(zip(k_values, db_scores))
        
        # Step 6: Cluster Profiling
        logger.info("\n[Step 6/7] Cluster Profiling")
        features_combined = engineer_all_features(preprocessed, feature_set='combined')
        profiles, insights = run_cluster_profiling(
            features_combined, labels, output_dir=str(dirs['reports'])
        )
        
        # Step 7: Recommendations
        logger.info("\n[Step 7/7] Recommendation Generation")
        recommendations = run_recommendation_engine(
            profiles, output_dir=str(dirs['reports'])
        )
        
        metadata = {
            'dataset_source': 'Synthetic (archetype-based)',
            'feature_list': feature_names,
            'feature_set': self.config.feature_set,
            'pca_components': int(n_components),
            'pca_variance_threshold': self.config.pca_variance_threshold,
            'selected_k': int(optimal_k),
            'random_seed': self.config.random_seed,
            'package_versions': get_package_versions(),
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'experiment_name': self.config.experiment_name,
            'config_hash': self.config.config_hash(),
            'n_consumers': self.config.n_consumers,
            'n_days': self.config.n_days,
            'cluster_sizes': np.bincount(labels).tolist(),
        }
        self._save_metadata(metadata, dirs['models'] / 'analysis_metadata.json')
        
        self.results = AnalysisResults(
            raw_data=raw_data,
            preprocessed_data=preprocessed,
            features=features,
            feature_names=feature_names,
            pca_transformed=X_pca,
            pca_model=pca_model,
            scaler=scaler,
            n_pca_components=n_components,
            cluster_labels=labels,
            kmeans_model=kmeans_model,
            optimal_k=optimal_k,
            k_values=k_values,
            inertia_by_k=inertia_by_k,
            silhouette_by_k=silhouette_by_k,
            ch_by_k=ch_by_k,
            db_by_k=db_by_k,
            stability_results=stability_results,
            cluster_profiles=profiles,
            cluster_insights=insights,
            recommendations=recommendations,
            config=self.config,
            metadata=metadata,
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("Analysis Pipeline Completed Successfully")
        logger.info("=" * 60)
        
        return self.results
    
    @staticmethod
    def _save_metadata(metadata: dict, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Analysis metadata saved to {path}")
    
    def get_summary(self) -> dict:
        if self.results is None:
            raise ValueError("Analysis not run yet. Call run() first.")
        
        return {
            'n_consumers': self.config.n_consumers,
            'n_days': self.config.n_days,
            'feature_set': self.config.feature_set,
            'n_features': len(self.results.feature_names),
            'n_pca_components': self.results.n_pca_components,
            'optimal_k': self.results.optimal_k,
            'silhouette_at_optimal': self.results.silhouette_for_k(self.results.optimal_k),
            'cluster_sizes': np.bincount(self.results.cluster_labels).tolist(),
            'n_recommendations': len(self.results.recommendations),
            'config_hash': self.config.config_hash(),
        }
    
    def save_summary(self, output_path: Optional[str] = None):
        if self.results is None:
            raise ValueError("Analysis not run yet. Call run() first.")
        
        if output_path is None:
            output_path = Path(self.config.output_dir) / 'reports' / 'analysis_summary.md'
        else:
            output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary = self.get_summary()
        
        lines = [
            "# Energy Consumption Analysis Summary",
            "",
            "## Configuration",
            f"- Consumers: {summary['n_consumers']}",
            f"- Days: {summary['n_days']}",
            f"- Feature Set: {summary['feature_set']}",
            f"- Random Seed: {self.config.random_seed}",
            f"- Config Hash: {summary['config_hash']}",
            f"- Data Source: Synthetic (archetype-based)",
            "",
            "## Results",
            f"- Features Engineered: {summary['n_features']}",
            f"- PCA Components: {summary['n_pca_components']} "
            f"({self.config.pca_variance_threshold:.0%} variance threshold)",
            f"- Optimal K: {summary['optimal_k']}",
            f"- Silhouette at Optimal K: {summary['silhouette_at_optimal']:.4f}",
            f"- Cluster Sizes: {summary['cluster_sizes']}",
            f"- Recommendations Generated: {summary['n_recommendations']}",
            "",
            "## Cluster Profiles",
            ""
        ]
        
        for _, profile in self.results.cluster_profiles.iterrows():
            lines.extend([
                f"### {profile['cluster_name']} (Cluster {profile['cluster']})",
                f"- Size: {profile['size']} ({profile['size_percentage']:.1f}%)",
                f"- Avg Consumption: {profile['avg_consumption']:.4f} kWh",
                f"- Peak-to-Avg Ratio: {profile['avg_peak_to_avg']:.2f}",
                f"- Coefficient of Variation: {profile['avg_cv']:.2f}",
                f"- Weekend Ratio: {profile['weekend_ratio']:.3f}",
                ""
            ])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Analysis summary saved to {output_path}")


if __name__ == "__main__":
    config = AnalysisConfig(
        n_consumers=200,
        n_days=30,
        feature_set='behavioral',
        test_stability=True,
        experiment_name='behavioral_primary',
    )
    
    analysis = EnergyAnalysis(config)
    results = analysis.run()
    
    print("\nAnalysis Summary:")
    summary = analysis.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    analysis.save_summary()
