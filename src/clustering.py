"""
Clustering Module
Performs K-Means clustering on PCA-transformed data.
"""

import os
os.environ.setdefault('MPLBACKEND', 'Agg')

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import matplotlib
matplotlib.use('Agg', force=True)
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
    Find optimal K using multiple metrics: silhouette, inertia, Calinski-Harabasz, Davies-Bouldin.
    
    Args:
        X: PCA-transformed data
        k_range: Range of K values to test (min, max)
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (k_values, inertia_values, silhouette_scores, ch_scores, db_scores)
    """
    logger.info(f"Finding optimal K in range {k_range}")
    
    k_values = range(k_range[0], k_range[1])
    inertia_values = []
    silhouette_scores = []
    ch_scores = []
    db_scores = []
    
    for k in k_values:
        logger.info(f"Testing K={k}")
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        kmeans.fit(X)
        
        inertia_values.append(kmeans.inertia_)
        
        # Calculate multiple metrics
        from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
        silhouette = silhouette_score(X, kmeans.labels_)
        ch = calinski_harabasz_score(X, kmeans.labels_)
        db = davies_bouldin_score(X, kmeans.labels_)
        
        silhouette_scores.append(silhouette)
        ch_scores.append(ch)
        db_scores.append(db)
        
        logger.info(f"  K={k}: Inertia={kmeans.inertia_:.2f}, Silhouette={silhouette:.4f}, CH={ch:.2f}, DB={db:.4f}")
    
    return k_values, inertia_values, silhouette_scores, ch_scores, db_scores


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
                    silhouette_scores: list, ch_scores: list, db_scores: list) -> int:
    """
    Select optimal K based on multi-metric consensus without hard-coded preferences.
    
    K Selection Rationale:
    - Uses consensus of multiple metrics: silhouette (higher better), CH (higher better), DB (lower better)
    - No hard-coded range preferences - lets metrics drive the decision
    - Consensus approach: K that appears in top 3 for most metrics is selected
    
    Args:
        k_values: List of K values
        inertia_values: List of inertia values
        silhouette_scores: List of silhouette scores
        ch_scores: List of Calinski-Harabasz scores
        db_scores: List of Davies-Bouldin scores
        
    Returns:
        Optimal K value
    """
    logger.info("Selecting optimal K using multi-metric consensus")
    
    # Find top 3 K for each metric
    top_silhouette = sorted(zip(k_values, silhouette_scores), key=lambda x: x[1], reverse=True)[:3]
    top_ch = sorted(zip(k_values, ch_scores), key=lambda x: x[1], reverse=True)[:3]
    top_db = sorted(zip(k_values, db_scores), key=lambda x: x[1])[:3]  # Lower is better
    
    logger.info(f"Top 3 by Silhouette: {[k for k, _ in top_silhouette]}")
    logger.info(f"Top 3 by Calinski-Harabasz: {[k for k, _ in top_ch]}")
    logger.info(f"Top 3 by Davies-Bouldin: {[k for k, _ in top_db]}")
    
    # Count votes for each K
    votes = {}
    for k, _ in top_silhouette:
        votes[k] = votes.get(k, 0) + 1
    for k, _ in top_ch:
        votes[k] = votes.get(k, 0) + 1
    for k, _ in top_db:
        votes[k] = votes.get(k, 0) + 1
    
    # Select K with most votes
    optimal_k = max(votes.items(), key=lambda x: x[1])[0]
    
    logger.info(f"Vote counts: {votes}")
    logger.info(f"Selected optimal K: {optimal_k}")
    
    return optimal_k


def test_cluster_stability(X: np.ndarray, n_clusters: int, n_runs: int = 10,
                          random_state: int = 42) -> dict:
    """
    Test cluster stability across multiple random initializations.
    
    Args:
        X: PCA-transformed data
        n_clusters: Number of clusters to test
        n_runs: Number of random initializations
        random_state: Base random seed
        
    Returns:
        Dictionary with stability metrics
    """
    logger.info(f"Testing cluster stability for K={n_clusters} with {n_runs} runs")
    
    from sklearn.metrics import adjusted_rand_score
    
    all_labels = []
    all_inertias = []
    
    for i in range(n_runs):
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state + i, n_init=10)
        labels = kmeans.fit_predict(X)
        all_labels.append(labels)
        all_inertias.append(kmeans.inertia_)
    
    # Calculate pairwise Adjusted Rand Index (ARI) between runs
    ari_scores = []
    for i in range(n_runs):
        for j in range(i + 1, n_runs):
            ari = adjusted_rand_score(all_labels[i], all_labels[j])
            ari_scores.append(ari)
    
    mean_ari = np.mean(ari_scores)
    std_ari = np.std(ari_scores)
    mean_inertia = np.mean(all_inertias)
    std_inertia = np.std(all_inertias)
    
    stability_results = {
        'n_clusters': n_clusters,
        'mean_ari': mean_ari,
        'std_ari': std_ari,
        'mean_inertia': mean_inertia,
        'std_inertia': std_inertia,
        'n_runs': n_runs
    }
    
    logger.info(f"Stability for K={n_clusters}: Mean ARI={mean_ari:.4f} (±{std_ari:.4f})")
    logger.info(f"  Inertia: {mean_inertia:.2f} (±{std_inertia:.2f})")
    
    return stability_results


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
                           test_stability: bool = True,
                           output_dir: str = 'outputs/figures',
                           model_dir: str = 'models') -> tuple:
    """
    Run complete clustering pipeline with multi-metric selection and stability testing.
    
    Args:
        X_pca: PCA-transformed data
        k_range: Range of K values to test
        random_state: Random seed for reproducibility
        test_stability: Whether to test cluster stability
        output_dir: Directory to save plots
        model_dir: Directory to save models
        
    Returns:
        Tuple of (kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores, ch_scores, db_scores, stability_results)
    """
    logger.info("Starting clustering pipeline")
    
    # Create output directories (never assume they exist)
    metrics_dir = Path(output_dir).parent / 'metrics'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    # Find optimal K using multiple metrics
    k_values, inertia_values, silhouette_scores, ch_scores, db_scores = find_optimal_k(X_pca, k_range, random_state)
    k_values = list(k_values)
    
    # Plot selection metrics
    plot_elbow_curve(k_values, inertia_values, output_dir)
    plot_silhouette_scores(k_values, silhouette_scores, output_dir)
    
    # Select optimal K using multi-metric consensus
    optimal_k = select_optimal_k(k_values, inertia_values, silhouette_scores, ch_scores, db_scores)
    
    # Test cluster stability
    stability_results = None
    if test_stability:
        stability_results = test_cluster_stability(X_pca, optimal_k, n_runs=10, random_state=random_state)
    
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
        'Silhouette_Score': silhouette_scores,
        'Calinski_Harabasz_Score': ch_scores,
        'Davies_Bouldin_Score': db_scores
    })
    clustering_metrics.to_csv(metrics_dir / 'clustering_metrics.csv', index=False)
    
    # Save stability results if available
    if stability_results:
        stability_df = pd.DataFrame([stability_results])
        stability_df.to_csv(metrics_dir / 'stability_results.csv', index=False)
    
    logger.info("Clustering pipeline completed")
    return kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores, ch_scores, db_scores, stability_results


if __name__ == "__main__":
    # Test clustering with new multi-metric selection
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    
    synthetic_data = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(synthetic_data.drop(columns=['archetype']))
    features = engineer_all_features(preprocessed, feature_set='behavioral')
    features_selected = select_features(features, feature_group='behavioral')
    
    X_pca, pca, scaler, n_components = run_pca_pipeline(features_selected)
    
    kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores, ch_scores, db_scores, stability_results = run_clustering_pipeline(X_pca, test_stability=True)
    
    print(f"\nClustering Results:")
    print(f"Optimal K: {optimal_k}")
    print(f"Cluster sizes: {np.bincount(labels)}")
    print(f"Final inertia: {kmeans.inertia_:.2f}")
    if stability_results:
        print(f"Stability (Mean ARI): {stability_results['mean_ari']:.4f} (±{stability_results['std_ari']:.4f})")
