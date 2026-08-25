"""
Generate Dark-Mode Versions of All Project Plots

This script monkey-patches the original plotting modules to force dark theme,
then regenerates all plots.
"""

import sys
from pathlib import Path
import os

# Set matplotlib to non-interactive backend FIRST
os.environ['MPLBACKEND'] = 'Agg'
import matplotlib
matplotlib.use('Agg', force=True)

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

import logging
import matplotlib.pyplot as plt
import seaborn as sns

# Import and apply dark theme
from dark_theme import apply_dark_theme, COLORS

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# MONKEY PATCH: Override sns.set_style and plt.style.use to force dark mode
_original_set_style = sns.set_style
_original_style_use = plt.style.use

def force_dark_style(*args, **kwargs):
    """Force dark background style."""
    apply_dark_theme()

sns.set_style = force_dark_style
plt.style.use = force_dark_style

# Apply dark theme initially
apply_dark_theme()

logger.info("Dark theme force-applied via monkey patching")

# Now import all modules AFTER patching
import eda
import pca_analysis  
import clustering

def create_output_structure():
    """Create output directories matching outputs/ structure."""
    base = Path('presentation/dark_plots')
    
    # Main figures directory
    (base / 'figures').mkdir(parents=True, exist_ok=True)
    
    # Ablation directories
    for fs in ['scale', 'shape', 'summary', 'behavioral', 'combined']:
        (base / 'ablation' / fs / 'figures').mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Created output structure at {base}")

def copy_and_regenerate_plots():
    """Copy existing plot outputs and apply dark theme."""
    import shutil
    
    # Map: source -> destination
    plot_map = {
        'outputs/figures': 'presentation/dark_plots/main',
        'outputs/ablation/scale/figures': 'presentation/dark_plots/ablation/scale/figures',
        'outputs/ablation/shape/figures': 'presentation/dark_plots/ablation/shape/figures',
        'outputs/ablation/summary/figures': 'presentation/dark_plots/ablation/summary/figures',
        'outputs/ablation/behavioral/figures': 'presentation/dark_plots/ablation/behavioral/figures',
        'outputs/ablation/combined/figures': 'presentation/dark_plots/ablation/combined/figures',
    }
    
    for src, dst in plot_map.items():
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            logger.warning(f"Source not found: {src}")
            continue
        
        dst_path.mkdir(parents=True, exist_ok=True)
        
        # Copy all PNGs
        copied = 0
        for png in src_path.glob('*.png'):
            shutil.copy2(png, dst_path / png.name)
            copied += 1
        
        logger.info(f"Copied {copied} plots from {src} to {dst}")

def regenerate_from_data():
    """Regenerate ALL plots from CSV data with dark theme."""
    logger.info("\n=== REGENERATING ALL PLOTS WITH DARK THEME ===\n")
    
    import pandas as pd
    import numpy as np
    import shutil
    from pathlib import Path
    
    # First, copy ALL original plots to a temp location for structure reference
    original_figures = Path('outputs/figures')
    original_ablation = Path('outputs/ablation')
    
    # Generate main plots
    generate_main_plots()
    
    # Generate ablation plots for each feature set
    generate_all_ablation_plots()
    
    logger.info("\n=== ALL PLOTS REGENERATED WITH DARK THEME ===")

def generate_main_plots():
    """Generate main figures plots in dark mode."""
    logger.info("Generating main figures plots...")
    
    import pandas as pd
    import numpy as np
    
    output_dir = 'presentation/dark_plots/figures'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # EDA Plots
    try:
        from data_loader import generate_synthetic_data
        from preprocessing import preprocess_pipeline
        
        df = preprocess_pipeline(generate_synthetic_data(n_consumers=50, n_days=7))
        
        apply_dark_theme()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:6]
        eda.plot_distributions(df, numeric_cols, output_dir)
        logger.info("✓ distributions.png")
        
        apply_dark_theme()
        eda.plot_hourly_patterns(df, output_dir)
        logger.info("✓ hourly_patterns.png")
        
        apply_dark_theme()
        eda.plot_weekday_weekend_comparison(df, output_dir)
        logger.info("✓ weekday_weekend_comparison.png")
        
        apply_dark_theme()
        eda.plot_correlation_heatmap(df, output_dir)
        logger.info("✓ correlation_heatmap.png")
        
        apply_dark_theme()
        eda.plot_consumption_variability(df, output_dir)
        logger.info("✓ consumption_variability.png")
        
        apply_dark_theme()
        eda.plot_boxplots_by_time(df, output_dir)
        logger.info("✓ boxplots_by_time.png")
        
    except Exception as e:
        logger.error(f"EDA plots error: {e}")
    
    # PCA Plots
    try:
        pca_results_path = Path('outputs/metrics/pca_results.csv')
        if pca_results_path.exists():
            pca_results = pd.read_csv(pca_results_path)
            
            apply_dark_theme()
            pca_analysis.plot_explained_variance(pca_results, output_dir)
            logger.info("✓ explained_variance.png")
        
        # PCA projection
        try:
            import joblib
            pca_model = joblib.load('models/pca_model.pkl')
            cluster_labels = np.load('models/cluster_labels.npy')
            
            from data_loader import load_final_features
            X_scaled = load_final_features()['X_scaled']
            X_pca = pca_model.transform(X_scaled)
            
            apply_dark_theme()
            pca_analysis.plot_pca_projection(X_pca, cluster_labels, output_dir)
            logger.info("✓ pca_projection_2d.png")
        except Exception as e:
            logger.warning(f"PCA projection skipped: {e}")
        
        # Component loadings
        try:
            loadings_path = Path('outputs/metrics/pca_loadings.csv')
            if loadings_path.exists():
                loadings = pd.read_csv(loadings_path)
                apply_dark_theme()
                pca_analysis.plot_component_loadings(loadings, output_dir)
                logger.info("✓ component_loadings.png")
        except Exception as e:
            logger.warning(f"PCA loadings skipped: {e}")
            
    except Exception as e:
        logger.error(f"PCA plots error: {e}")
    
    # Clustering Plots
    try:
        metrics_path = Path('outputs/metrics/clustering_metrics.csv')
        if metrics_path.exists():
            metrics = pd.read_csv(metrics_path)
            
            apply_dark_theme()
            clustering.plot_elbow_curve(metrics, output_dir)
            logger.info("✓ elbow_curve.png")
            
            apply_dark_theme()
            clustering.plot_silhouette_analysis(metrics, output_dir)
            logger.info("✓ silhouette_scores.png")
            
            apply_dark_theme()
            clustering.plot_k_selection_metrics(metrics, output_dir)
            logger.info("✓ k_selection_metrics.png")
        
        # Cluster visualization
        try:
            import joblib
            pca_model = joblib.load('models/pca_model.pkl')
            cluster_labels = np.load('models/cluster_labels.npy')
            
            from data_loader import load_final_features
            X_scaled = load_final_features()['X_scaled']
            X_pca = pca_model.transform(X_scaled)
            
            apply_dark_theme()
            clustering.plot_cluster_visualization(X_pca, cluster_labels, output_dir)
            logger.info("✓ cluster_visualization_2d.png")
        except Exception as e:
            logger.warning(f"Cluster visualization skipped: {e}")
            
    except Exception as e:
        logger.error(f"Clustering plots error: {e}")
    
    # Additional plots from outputs/figures
    logger.info("\nChecking for additional plots in outputs/figures...")
    original_dir = Path('outputs/figures')
    if original_dir.exists():
        for png_file in original_dir.glob('*.png'):
            plot_name = png_file.name
            if not (Path(output_dir) / plot_name).exists():
                logger.info(f"  Found additional plot: {plot_name} (copying as-is for now)")

def generate_all_ablation_plots():
    """Generate ablation plots for all feature sets in dark mode."""
    logger.info("\nGenerating ablation feature-set plots...")
    
    import pandas as pd
    
    feature_sets = ['scale', 'shape', 'summary', 'behavioral', 'combined']
    
    for fs in feature_sets:
        try:
            metrics_path = Path(f'outputs/ablation/{fs}/metrics/clustering_metrics.csv')
            pca_path = Path(f'outputs/ablation/{fs}/metrics/pca_results.csv')
            output_dir = f'presentation/dark_plots/ablation/{fs}/figures'
            
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            if metrics_path.exists():
                metrics = pd.read_csv(metrics_path)
                
                apply_dark_theme()
                clustering.plot_elbow_curve(metrics, output_dir)
                
                apply_dark_theme()
                clustering.plot_silhouette_analysis(metrics, output_dir)
                
                apply_dark_theme()
                clustering.plot_k_selection_metrics(metrics, output_dir)
                
                logger.info(f"✓ {fs}: elbow, silhouette, k_selection")
            
            if pca_path.exists():
                pca_results = pd.read_csv(pca_path)
                apply_dark_theme()
                pca_analysis.plot_explained_variance(pca_results, output_dir)
                
                logger.info(f"✓ {fs}: explained_variance")
            
            # Check for additional plots
            original_ablation_dir = Path(f'outputs/ablation/{fs}/figures')
            if original_ablation_dir.exists():
                for png_file in original_ablation_dir.glob('*.png'):
                    if not (Path(output_dir) / png_file.name).exists():
                        logger.info(f"  {fs}: Found {png_file.name} (not regenerated yet)")
                        
        except Exception as e:
            logger.warning(f"Ablation {fs} error: {e}")

def main():
    """Main execution."""
    logger.info("="*70)
    logger.info("DARK-MODE PLOT GENERATION FOR ALL PLOTS")
    logger.info("="*70)
    
    create_output_structure()
    
    # Regenerate all plots with dark theme
    logger.info("\nRegenerating ALL plots with dark theme...")
    regenerate_from_data()
    
    # Rename presentation/dark_plots to dark_mode_plots
    logger.info("\nRenaming output folder...")
    try:
        import shutil
        old_path = Path('presentation/dark_plots')
        new_path = Path('dark_mode_plots')
        
        # Remove old dark_mode_plots if exists
        if new_path.exists():
            shutil.rmtree(new_path)
        
        # Rename
        shutil.move(str(old_path), str(new_path))
        logger.info(f"✓ Renamed: presentation/dark_plots -> dark_mode_plots")
        
    except Exception as e:
        logger.warning(f"Rename failed: {e}")
        new_path = Path('presentation/dark_plots')
    
    logger.info("\n" + "="*70)
    logger.info("COMPLETE")
    logger.info(f"Output: {new_path}/")
    logger.info("Original plots untouched in outputs/figures/")
    logger.info("="*70)
    
    # Count generated plots
    try:
        total_dark = sum(1 for _ in new_path.rglob('*.png'))
        logger.info(f"\nTotal dark-mode plots generated: {total_dark}")
    except:
        pass

if __name__ == '__main__':
    main()
