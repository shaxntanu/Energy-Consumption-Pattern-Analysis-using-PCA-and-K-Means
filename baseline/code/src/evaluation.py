"""
Evaluation Module
Provides additional clustering evaluation metrics.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_clustering_metrics(X: np.ndarray, labels: np.ndarray) -> dict:
    """
    Calculate comprehensive clustering evaluation metrics.
    
    Args:
        X: Feature matrix
        labels: Cluster labels
        
    Returns:
        Dictionary of evaluation metrics
    """
    logger.info("Calculating clustering evaluation metrics")
    
    metrics = {}
    
    # Silhouette Score
    from sklearn.metrics import silhouette_score
    metrics['silhouette_score'] = silhouette_score(X, labels)
    
    # Calinski-Harabasz Score (higher is better)
    metrics['calinski_harabasz_score'] = calinski_harabasz_score(X, labels)
    
    # Davies-Bouldin Score (lower is better)
    metrics['davies_bouldin_score'] = davies_bouldin_score(X, labels)
    
    # Inertia
    from sklearn.cluster import KMeans
    kmeans_temp = KMeans(n_clusters=len(np.unique(labels)), random_state=42, n_init=10)
    kmeans_temp.fit(X)
    metrics['inertia'] = kmeans_temp.inertia_
    
    logger.info(f"Silhouette Score: {metrics['silhouette_score']:.4f}")
    logger.info(f"Calinski-Harabasz Score: {metrics['calinski_harabasz_score']:.4f}")
    logger.info(f"Davies-Bouldin Score: {metrics['davies_bouldin_score']:.4f}")
    logger.info(f"Inertia: {metrics['inertia']:.4f}")
    
    return metrics


def save_evaluation_metrics(metrics: dict, output_dir: str = 'outputs/metrics'):
    """
    Save evaluation metrics to CSV.
    
    Args:
        metrics: Dictionary of metrics
        output_dir: Directory to save metrics
    """
    logger.info("Saving evaluation metrics")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(Path(output_dir) / 'evaluation_metrics.csv', index=False)
    
    logger.info(f"Evaluation metrics saved to {output_dir}")


if __name__ == "__main__":
    # Test evaluation
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    from clustering import run_clustering_pipeline
    
    synthetic_data = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(synthetic_data)
    features = engineer_all_features(preprocessed)
    features_selected = select_features(features)
    
    X_pca, pca, scaler, n_components = run_pca_pipeline(features_selected)
    kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores = run_clustering_pipeline(X_pca)
    
    metrics = calculate_clustering_metrics(X_pca, labels)
    save_evaluation_metrics(metrics)
    
    print("\nEvaluation Metrics:")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")
