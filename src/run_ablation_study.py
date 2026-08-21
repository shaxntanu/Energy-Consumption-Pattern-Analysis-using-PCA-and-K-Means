"""
Ablation Study Module
Compares clustering performance across different feature sets.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from data_loader import generate_synthetic_data
from preprocessing import preprocess_pipeline
from feature_engineering import engineer_all_features, select_features
from pca_analysis import run_pca_pipeline
from clustering import run_clustering_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_ablation_study(n_consumers: int = 200, n_days: int = 30, 
                      hourly_records: bool = True, random_seed: int = 42,
                      output_dir: str = 'outputs/reports') -> pd.DataFrame:
    """
    Run ablation study comparing different feature sets.
    
    Feature Sets to Compare:
    - behavioral: Shape-only features (normalized 24h profiles, temporal patterns, variability)
    - scale: Magnitude features (mean, max, sum, electrical features)
    - combined: Both behavioral and scale features
    
    Metrics to Compare:
    - Optimal K (selected by multi-metric consensus)
    - Silhouette score at optimal K
    - Calinski-Harabasz score at optimal K
    - Davies-Bouldin score at optimal K
    - Stability (Mean ARI across 10 runs)
    - Cluster size distribution
    
    Args:
        n_consumers: Number of consumers
        n_days: Number of days
        hourly_records: Whether to use hourly data
        random_seed: Random seed for reproducibility
        output_dir: Directory to save results
        
    Returns:
        DataFrame with ablation study results
    """
    logger.info("Starting ablation study")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic data (once, for all feature sets)
    synthetic_data = generate_synthetic_data(
        n_consumers=n_consumers, 
        n_days=n_days, 
        hourly_records=hourly_records, 
        random_seed=random_seed
    )
    
    # Preprocess (drop archetype to prevent leakage)
    preprocessed = preprocess_pipeline(synthetic_data.drop(columns=['archetype']))
    
    # Feature sets to test
    feature_sets = ['behavioral', 'scale', 'combined']
    
    results = []
    
    for feature_set in feature_sets:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing feature set: {feature_set}")
        logger.info(f"{'='*60}")
        
        # Engineer features
        features = engineer_all_features(preprocessed, feature_set=feature_set)
        features_selected = select_features(features, feature_group=feature_set)
        
        logger.info(f"Feature set shape: {features_selected.shape}")
        
        # Isolate artifacts under outputs/ablation/<set>/ (never overwrite primary models/)
        ablation_root = Path(output_dir).parent / 'ablation' / feature_set
        run_figures = str(ablation_root / 'figures')
        run_models = str(ablation_root / 'models')
        Path(run_figures).mkdir(parents=True, exist_ok=True)
        Path(run_models).mkdir(parents=True, exist_ok=True)

        # Run PCA
        X_pca, pca, scaler, n_components = run_pca_pipeline(
            features_selected, output_dir=run_figures, model_dir=run_models
        )
        
        # Run clustering
        kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores, ch_scores, db_scores, stability_results = run_clustering_pipeline(
            X_pca, test_stability=True, output_dir=run_figures, model_dir=run_models
        )
        
        k_values = list(k_values)
        # Collect results
        result = {
            'feature_set': feature_set,
            'n_features': features_selected.drop(columns=['consumer_id'], errors='ignore').shape[1],
            'n_pca_components': n_components,
            'optimal_k': optimal_k,
            'silhouette_at_optimal': silhouette_scores[k_values.index(optimal_k)],
            'ch_at_optimal': ch_scores[k_values.index(optimal_k)],
            'db_at_optimal': db_scores[k_values.index(optimal_k)],
            'stability_mean_ari': stability_results['mean_ari'] if stability_results else None,
            'stability_std_ari': stability_results['std_ari'] if stability_results else None,
            'cluster_sizes': str(np.bincount(labels).tolist()),
            'cluster_balance': np.min(np.bincount(labels)) / np.max(np.bincount(labels))
        }
        
        results.append(result)
        logger.info(f"Results for {feature_set}: {result}")
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Save results
    results_df.to_csv(Path(output_dir) / 'ablation_study_results.csv', index=False)
    
    # Generate summary report
    generate_ablation_report(results_df, output_dir)
    
    logger.info("Ablation study completed")
    return results_df


def generate_ablation_report(results_df: pd.DataFrame, output_dir: str):
    """
    Generate human-readable ablation study report.
    
    Args:
        results_df: DataFrame with ablation study results
        output_dir: Directory to save report
    """
    logger.info("Generating ablation study report")
    
    report_lines = [
        "# Ablation Study Report",
        "",
        "## Objective",
        "Compare clustering performance across different feature engineering approaches",
        "to identify which feature set yields the most meaningful, stable clusters.",
        "",
        "## Feature Sets Compared",
        "- **behavioral**: Shape-only features (normalized 24h profiles, temporal patterns, variability metrics)",
        "- **scale**: Magnitude features (mean, max, sum, electrical features)",
        "- **combined**: Both behavioral and scale features",
        "",
        "## Metrics",
        "- **Optimal K**: Number of clusters selected by multi-metric consensus",
        "- **Silhouette**: Higher is better (cluster separation)",
        "- **Calinski-Harabasz**: Higher is better (cluster compactness/separation)",
        "- **Davies-Bouldin**: Lower is better (cluster similarity)",
        "- **Stability (ARI)**: Higher is better (consistency across runs)",
        "- **Cluster Balance**: Ratio of smallest to largest cluster (closer to 1 is better)",
        "",
        "## Results",
        "",
        results_df.to_string(index=False),
        "",
        "## Analysis",
        ""
    ]
    
    # Add analysis
    best_silhouette = results_df.loc[results_df['silhouette_at_optimal'].idxmax()]
    best_stability = results_df.loc[results_df['stability_mean_ari'].idxmax()]
    best_balance = results_df.loc[results_df['cluster_balance'].idxmax()]
    
    report_lines.extend([
        f"**Best Silhouette Score**: {best_silhouette['feature_set']} ({best_silhouette['silhouette_at_optimal']:.4f})",
        f"**Best Stability**: {best_stability['feature_set']} (ARI={best_stability['stability_mean_ari']:.4f})",
        f"**Best Cluster Balance**: {best_balance['feature_set']} (balance={best_balance['cluster_balance']:.4f})",
        "",
        "## Recommendation",
        ""
    ])
    
    # Primary recommendation follows the project objective (pattern segmentation),
    # not whichever set maximizes silhouette via magnitude.
    recommended = 'behavioral'
    reason = (
        "Project objective is usage-pattern segmentation. "
        "Scale often wins raw silhouette because magnitude separates cleanly; "
        "behavioral is the scientifically correct primary experiment."
    )
    scientific_note = (
        f"Metric leaders — silhouette: {best_silhouette['feature_set']} "
        f"({best_silhouette['silhouette_at_optimal']:.4f}); "
        f"stability: {best_stability['feature_set']} "
        f"(ARI={best_stability['stability_mean_ari']:.4f}); "
        f"balance: {best_balance['feature_set']} "
        f"({best_balance['cluster_balance']:.4f}). "
        "Higher scale metrics demonstrate the magnitude baseline, not the preferred story."
    )
    
    report_lines.extend([
        f"**Primary Feature Set (for this project)**: {recommended}",
        f"**Rationale**: {reason}",
        "",
        scientific_note,
        "",
        "## Conclusion",
        "Use **behavioral** features for the final analysis and viva defense.",
        "Report scale/combined as ablation controls that show why feature engineering",
        "changes the question from 'who consumes more?' to 'how do consumers consume differently?'.",
    ])
    
    report_text = "\n".join(report_lines)
    
    with open(Path(output_dir) / 'ablation_study_report.md', 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    logger.info(f"Saved ablation study report to {output_dir}")


if __name__ == "__main__":
    # Run ablation study
    results = run_ablation_study(n_consumers=200, n_days=30, hourly_records=True)
    
    print("\nAblation Study Results:")
    print(results.to_string(index=False))
    
    print("\nPrimary feature set (project objective): behavioral")
    print("Metric-best by stability ARI:", results.loc[results['stability_mean_ari'].idxmax(), 'feature_set'])
