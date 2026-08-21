"""
Clustering Module
Performs K-Means clustering on PCA-transformed data.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def find_optimal_k(X: np.ndarray, k_range: tuple = (2, 11), 
                   random_state: int = 42) -> tuple:
    """
    Find optimal K using elbow method and silhouette score.
    
    Args:
        X: PCA-transformed data
        k_range: Range of K values to test (min, max)
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (k_values, inertia_values, silhouette_scores)
    """
    logger.info(f"Finding optimal K in range {k_range}")
    
    k_values = range(k_range[0], k_range[1])
    inertia_values = []
    silhouette_scores = []
    
    for k in k_values:
        logger.info(f"Testing K={k}")
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        kmeans.fit(X)
        
        inertia_values.append(kmeans.inertia_)
        
        # Calculate silhouette score
        from sklearn.metrics import silhouette_score
        silhouette = silhouette_score(X, kmeans.labels_)
        silhouette_scores.append(silhouette)
        
        logger.info(f"  K={k}: Inertia={kmeans.inertia_:.2f}, Silhouette={silhouette:.4f}")
    
    return k_values, inertia_values, silhouette_scores


def plot_elbow_curve(k_values: list, inertia_values: list, 
                     output_dir: str = 'outputs/figures'):
    """
    Plot elbow curve for K selection.
    
    Args:
        k_values: List of K values
        inertia_values: List of inertia values
        output_dir: Directory to save plots
    """
    logger.info("Plotting elbow curve")
    
    plt.figure(figsize=(10, 6))
    plt.plot(k_values, inertia_values, marker='o', linewidth=2, markersize=8, color='steelblue')
    plt.xlabel('Number of Clusters (K)')
    plt.ylabel('Inertia')
    plt.title('Elbow Curve for Optimal K Selection')
    plt.grid(True, alpha=0.3)
    plt.xticks(k_values)
    
    output_path = Path(output_dir) / 'elbow_curve.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved elbow curve to {output_path}")


def plot_silhouette_scores(k_values: list, silhouette_scores: list,
                          output_dir: str = 'outputs/figures'):
    """
    Plot silhouette scores for K selection.
    
    Args:
        k_values: List of K values
        silhouette_scores: List of silhouette scores
        output_dir: Directory to save plots
    """
    logger.info("Plotting silhouette scores")
    
    plt.figure(figsize=(10, 6))
    plt.plot(k_values, silhouette_scores, marker='o', linewidth=2, markersize=8, color='darkred')
    plt.xlabel('Number of Clusters (K)')
    plt.ylabel('Silhouette Score')
    plt.title('Silhouette Scores for Optimal K Selection')
    plt.grid(True, alpha=0.3)
    plt.xticks(k_values)
    
    # Highlight maximum
    max_idx = np.argmax(silhouette_scores)
    plt.scatter(k_values[max_idx], silhouette_scores[max_idx], 
               color='green', s=200, zorder=5, label=f'Max: K={k_values[max_idx]}')
    plt.legend()
    
    output_path = Path(output_dir) / 'silhouette_scores.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved silhouette scores plot to {output_path}")


def select_optimal_k(k_values: list, inertia_values: list, 
                    silhouette_scores: list) -> int:
    """
    Select optimal K based on quantitative metrics and interpretability.
    
    Args:
        k_values: List of K values
        inertia_values: List of inertia values
        silhouette_scores: List of silhouette scores
        
    Returns:
        Optimal K value
    """
    logger.info("Selecting optimal K")
    
    # Find K with maximum silhouette score
    max_silhouette_idx = np.argmax(silhouette_scores)
    best_silhouette_k = k_values[max_silhouette_idx]
    
    # Use elbow method for inertia (find point of maximum curvature)
    # Simplified: find where the rate of decrease slows significantly
    inertia_diffs = np.diff(inertia_values)
    inertia_diffs2 = np.diff(inertia_diffs)
    
    # Find elbow point (maximum second derivative)
    if len(inertia_diffs2) > 0:
        elbow_idx = np.argmax(inertia_diffs2) + 1  # +1 due to double diff
        best_elbow_k = k_values[elbow_idx]
    else:
        best_elbow_k = best_silhouette_k
    
    logger.info(f"Best silhouette K: {best_silhouette_k} (score: {silhouette_scores[max_silhouette_idx]:.4f})")
    logger.info(f"Best elbow K: {best_elbow_k}")
    
    # Prioritize silhouette score but consider interpretability
    # Prefer K between 3-6 for interpretability unless silhouette strongly suggests otherwise
    if 3 <= best_silhouette_k <= 6:
        optimal_k = best_silhouette_k
    elif best_elbow_k >= 3 and best_elbow_k <= 6:
        optimal_k = best_elbow_k
    else:
        # Default to silhouette recommendation
        optimal_k = best_silhouette_k
    
    logger.info(f"Selected optimal K: {optimal_k}")
    return optimal_k


def perform_kmeans(X: np.ndarray, n_clusters: int, 
                   random_state: int = 42) -> tuple:
    """
    Perform final K-Means clustering.
    
    Args:
        X: PCA-transformed data
        n_clusters: Number of clusters
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (kmeans_model, cluster_labels)
    """
    logger.info(f"Performing K-Means with K={n_clusters}")
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(X)
    
    logger.info(f"K-Means completed. Cluster sizes: {np.bincount(labels)}")
    
    return kmeans, labels


def plot_cluster_visualization(X_pca: np.ndarray, labels: np.ndarray,
                               output_dir: str = 'outputs/figures'):
    """
    Plot 2D cluster visualization.
    
    Args:
        X_pca: PCA-transformed data (at least 2 components)
        labels: Cluster labels
        output_dir: Directory to save plots
    """
    logger.info("Plotting cluster visualization")
    
    if X_pca.shape[1] < 2:
        logger.warning("Need at least 2 components for 2D visualization")
        return
    
    n_clusters = len(np.unique(labels))
    colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))
    
    plt.figure(figsize=(12, 8))
    
    for i in range(n_clusters):
        mask = labels == i
        plt.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                   c=[colors[i]], label=f'Cluster {i}', 
                   alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
    
    # Plot centroids
    from sklearn.cluster import KMeans
    kmeans_temp = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans_temp.fit(X_pca)
    centroids = kmeans_temp.cluster_centers_
    plt.scatter(centroids[:, 0], centroids[:, 1], 
               c='red', marker='X', s=200, linewidths=3, 
               edgecolors='black', label='Centroids', zorder=10)
    
    plt.xlabel(f'PC1')
    plt.ylabel(f'PC2')
    plt.title('2D Cluster Visualization')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_path = Path(output_dir) / 'cluster_visualization_2d.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved cluster visualization to {output_path}")


def save_clustering_model(kmeans: KMeans, labels: np.ndarray, 
                          model_dir: str = 'models'):
    """
    Save K-Means model and labels.
    
    Args:
        kmeans: Fitted K-Means model
        labels: Cluster labels
        model_dir: Directory to save models
    """
    logger.info("Saving clustering model")
    
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    
    joblib.dump(kmeans, Path(model_dir) / 'kmeans_model.pkl')
    np.save(Path(model_dir) / 'cluster_labels.npy', labels)
    
    logger.info(f"Clustering model saved to {model_dir}")


def run_clustering_pipeline(X_pca: np.ndarray, k_range: tuple = (2, 11),
                           random_state: int = 42,
                           output_dir: str = 'outputs/figures',
                           model_dir: str = 'models') -> tuple:
    """
    Run complete clustering pipeline.
    
    Args:
        X_pca: PCA-transformed data
        k_range: Range of K values to test
        random_state: Random seed for reproducibility
        output_dir: Directory to save plots
        model_dir: Directory to save models
        
    Returns:
        Tuple of (kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores)
    """
    logger.info("Starting clustering pipeline")
    
    # Create output directories
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    
    # Find optimal K
    k_values, inertia_values, silhouette_scores = find_optimal_k(X_pca, k_range, random_state)
    
    # Plot selection metrics
    plot_elbow_curve(k_values, inertia_values, output_dir)
    plot_silhouette_scores(k_values, silhouette_scores, output_dir)
    
    # Select optimal K
    optimal_k = select_optimal_k(k_values, inertia_values, silhouette_scores)
    
    # Perform final clustering
    kmeans, labels = perform_kmeans(X_pca, optimal_k, random_state)
    
    # Visualize clusters
    plot_cluster_visualization(X_pca, labels, output_dir)
    
    # Save model
    save_clustering_model(kmeans, labels, model_dir)
    
    # Save clustering metrics
    clustering_metrics = pd.DataFrame({
        'K': k_values,
        'Inertia': inertia_values,
        'Silhouette_Score': silhouette_scores
    })
    clustering_metrics.to_csv(Path(output_dir).parent / 'metrics' / 'clustering_metrics.csv', index=False)
    
    logger.info("Clustering pipeline completed")
    return kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores


if __name__ == "__main__":
    # Test clustering
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    
    synthetic_data = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(synthetic_data)
    features = engineer_all_features(preprocessed)
    features_selected = select_features(features)
    
    X_pca, pca, scaler, n_components = run_pca_pipeline(features_selected)
    
    kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores = run_clustering_pipeline(X_pca)
    
    print(f"\nClustering Results:")
    print(f"Optimal K: {optimal_k}")
    print(f"Cluster sizes: {np.bincount(labels)}")
    print(f"Final inertia: {kmeans.inertia_:.2f}")
