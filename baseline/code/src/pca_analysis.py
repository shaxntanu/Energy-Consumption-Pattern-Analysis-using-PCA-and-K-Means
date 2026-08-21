"""
PCA Analysis Module
Performs dimensionality reduction using PCA.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
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


def standardize_features(df: pd.DataFrame) -> tuple:
    """
    Standardize numerical features using StandardScaler.
    
    Args:
        df: Input DataFrame with features
        
    Returns:
        Tuple of (scaled_array, scaler_object)
    """
    logger.info("Standardizing features")
    
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df)
    
    logger.info(f"Features standardized. Shape: {scaled_data.shape}")
    return scaled_data, scaler


def perform_pca(X: np.ndarray, variance_threshold: float = 0.95) -> tuple:
    """
    Perform PCA and determine optimal number of components.
    
    Args:
        X: Scaled feature matrix
        variance_threshold: Minimum cumulative variance to retain
        
    Returns:
        Tuple of (pca_object, transformed_data, n_components)
    """
    logger.info("Performing PCA")
    
    # Start with all components
    pca = PCA()
    pca.fit(X)
    
    # Calculate cumulative explained variance
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
    
    # Find number of components for threshold
    n_components = np.argmax(cumulative_variance >= variance_threshold) + 1
    logger.info(f"Selected {n_components} components for {variance_threshold:.0%} variance")
    
    # Fit PCA with selected components
    pca_final = PCA(n_components=n_components)
    X_pca = pca_final.fit_transform(X)
    
    logger.info(f"PCA completed. Transformed shape: {X_pca.shape}")
    logger.info(f"Explained variance ratio: {pca_final.explained_variance_ratio_}")
    logger.info(f"Cumulative explained variance: {cumulative_variance[n_components-1]:.4f}")
    
    return pca_final, X_pca, n_components


def plot_explained_variance(pca: PCA, output_dir: str = 'outputs/figures'):
    """
    Plot explained variance ratio and cumulative variance.
    
    Args:
        pca: Fitted PCA object
        output_dir: Directory to save plots
    """
    logger.info("Plotting explained variance")
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Individual explained variance
    axes[0].bar(range(1, len(pca.explained_variance_ratio_) + 1), 
                pca.explained_variance_ratio_, alpha=0.7, color='steelblue')
    axes[0].set_xlabel('Principal Component')
    axes[0].set_ylabel('Explained Variance Ratio')
    axes[0].set_title('Individual Explained Variance by Component')
    axes[0].grid(True, alpha=0.3)
    
    # Cumulative explained variance
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
    axes[1].plot(range(1, len(cumulative_variance) + 1), cumulative_variance, 
                marker='o', linewidth=2, markersize=8, color='darkred')
    axes[1].axhline(y=0.95, color='green', linestyle='--', label='95% Threshold')
    axes[1].axhline(y=0.90, color='orange', linestyle='--', label='90% Threshold')
    axes[1].set_xlabel('Number of Components')
    axes[1].set_ylabel('Cumulative Explained Variance')
    axes[1].set_title('Cumulative Explained Variance')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'explained_variance.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved explained variance plot to {output_path}")


def plot_pca_projection(X_pca: np.ndarray, output_dir: str = 'outputs/figures'):
    """
    Plot 2D PCA projection.
    
    Args:
        X_pca: PCA-transformed data
        output_dir: Directory to save plots
    """
    logger.info("Plotting PCA projection")
    
    if X_pca.shape[1] < 2:
        logger.warning("Need at least 2 components for 2D projection")
        return
    
    plt.figure(figsize=(10, 8))
    plt.scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
    plt.xlabel(f'PC1 ({X_pca[:, 0].var():.4f} variance)')
    plt.ylabel(f'PC2 ({X_pca[:, 1].var():.4f} variance)')
    plt.title('2D PCA Projection')
    plt.grid(True, alpha=0.3)
    
    output_path = Path(output_dir) / 'pca_projection_2d.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved 2D PCA projection to {output_path}")


def plot_component_loadings(pca: PCA, feature_names: list, output_dir: str = 'outputs/figures'):
    """
    Plot PCA component loadings.
    
    Args:
        pca: Fitted PCA object
        feature_names: List of feature names
        output_dir: Directory to save plots
    """
    logger.info("Plotting component loadings")
    
    n_components = min(3, pca.n_components_)
    n_features = len(feature_names)
    
    fig, axes = plt.subplots(1, n_components, figsize=(6 * n_components, 8))
    if n_components == 1:
        axes = [axes]
    
    for i in range(n_components):
        loadings = pca.components_[i]
        axes[i].barh(range(n_features), loadings, color='steelblue')
        axes[i].set_yticks(range(n_features))
        axes[i].set_yticklabels(feature_names, fontsize=8)
        axes[i].set_xlabel(f'Loading for PC{i+1}')
        axes[i].set_title(f'Component {i+1} Loadings')
        axes[i].grid(True, alpha=0.3, axis='x')
        axes[i].axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'component_loadings.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved component loadings plot to {output_path}")


def save_models(scaler: StandardScaler, pca: PCA, model_dir: str = 'models'):
    """
    Save scaler and PCA models.
    
    Args:
        scaler: Fitted StandardScaler
        pca: Fitted PCA object
        model_dir: Directory to save models
    """
    logger.info("Saving PCA models")
    
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    
    joblib.dump(scaler, Path(model_dir) / 'scaler.pkl')
    joblib.dump(pca, Path(model_dir) / 'pca_model.pkl')
    
    logger.info(f"Models saved to {model_dir}")


def run_pca_pipeline(df: pd.DataFrame, variance_threshold: float = 0.95,
                    output_dir: str = 'outputs/figures', 
                    model_dir: str = 'models') -> tuple:
    """
    Run complete PCA pipeline.
    
    Args:
        df: DataFrame with engineered features (excluding consumer_id)
        variance_threshold: Minimum cumulative variance to retain
        output_dir: Directory to save plots
        model_dir: Directory to save models
        
    Returns:
        Tuple of (X_pca, pca, scaler, n_components)
    """
    logger.info("Starting PCA pipeline")
    
    # Create output directories
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    
    # Standardize features
    X_scaled, scaler = standardize_features(df)
    
    # Perform PCA
    pca, X_pca, n_components = perform_pca(X_scaled, variance_threshold)
    
    # Generate visualizations
    plot_explained_variance(pca, output_dir)
    plot_pca_projection(X_pca, output_dir)
    plot_component_loadings(pca, df.columns.tolist(), output_dir)
    
    # Save models
    save_models(scaler, pca, model_dir)
    
    # Save PCA results
    pca_results = pd.DataFrame({
        'Component': range(1, n_components + 1),
        'Explained_Variance_Ratio': pca.explained_variance_ratio_,
        'Cumulative_Variance': np.cumsum(pca.explained_variance_ratio_)
    })
    pca_results.to_csv(Path(output_dir).parent / 'metrics' / 'pca_results.csv', index=False)
    
    logger.info("PCA pipeline completed")
    return X_pca, pca, scaler, n_components


if __name__ == "__main__":
    # Test PCA
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    from feature_engineering import engineer_all_features, select_features
    
    synthetic_data = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(synthetic_data)
    features = engineer_all_features(preprocessed)
    features_selected = select_features(features)
    
    X_pca, pca, scaler, n_components = run_pca_pipeline(features_selected)
    
    print(f"\nPCA Results:")
    print(f"Number of components: {n_components}")
    print(f"Explained variance ratio: {pca.explained_variance_ratio_}")
    print(f"Cumulative variance: {np.cumsum(pca.explained_variance_ratio_)[-1]:.4f}")
    print(f"Transformed data shape: {X_pca.shape}")
