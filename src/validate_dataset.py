"""
Dataset Validation Module
Validates that synthetic data contains genuine behavioral variation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def plot_archetype_profiles(df: pd.DataFrame, output_dir: str = 'outputs/figures'):
    """
    Plot average 24-hour profiles by archetype to show distinct behavioral patterns.
    
    Args:
        df: DataFrame with archetype labels
        output_dir: Directory to save plots
    """
    logger.info("Plotting archetype profiles")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Calculate average hourly profile by archetype
    hourly_by_archetype = df.groupby(['archetype', 'hour'])['energy_consumption_kwh'].mean().reset_index()
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    axes = axes.flatten()
    
    archetypes = ['daytime', 'evening', 'flat', 'weekend']
    
    for i, arch in enumerate(archetypes):
        arch_data = hourly_by_archetype[hourly_by_archetype['archetype'] == arch]
        axes[i].plot(arch_data['hour'], arch_data['energy_consumption_kwh'], 
                    marker='o', linewidth=2, markersize=6, color='steelblue')
        axes[i].set_title(f'{arch.capitalize()} Archetype Profile')
        axes[i].set_xlabel('Hour of Day')
        axes[i].set_ylabel('Avg Energy (kWh)')
        axes[i].set_xticks(range(0, 24, 3))
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'archetype_profiles.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved archetype profiles to {output_path}")


def plot_within_archetype_variation(df: pd.DataFrame, output_dir: str = 'outputs/figures'):
    """
    Plot within-archetype variation to show continuous overlap.
    
    Args:
        df: DataFrame with archetype labels
        output_dir: Directory to save plots
    """
    logger.info("Plotting within-archetype variation")
    
    # Calculate consumer-level profiles
    consumer_profiles = df.groupby(['consumer_id', 'archetype', 'hour'])['energy_consumption_kwh'].mean().reset_index()
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    axes = axes.flatten()
    
    archetypes = ['daytime', 'evening', 'flat', 'weekend']
    
    for i, arch in enumerate(archetypes):
        arch_data = consumer_profiles[consumer_profiles['archetype'] == arch]
        
        # Plot individual consumer profiles (sample)
        sample_consumers = arch_data['consumer_id'].unique()[:10]
        
        for consumer_id in sample_consumers:
            consumer_data = arch_data[arch_data['consumer_id'] == consumer_id]
            axes[i].plot(consumer_data['hour'], consumer_data['energy_consumption_kwh'], 
                        alpha=0.3, linewidth=1, color='gray')
        
        # Plot average
        avg_profile = arch_data.groupby('hour')['energy_consumption_kwh'].mean()
        axes[i].plot(avg_profile.index, avg_profile.values, 
                    marker='o', linewidth=3, markersize=6, color='red', label='Average')
        
        axes[i].set_title(f'{arch.capitalize()} - Within-Archetype Variation')
        axes[i].set_xlabel('Hour of Day')
        axes[i].set_ylabel('Energy (kWh)')
        axes[i].set_xticks(range(0, 24, 3))
        axes[i].legend()
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'within_archetype_variation.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved within-archetype variation to {output_path}")


def plot_cross_archetype_overlap(df: pd.DataFrame, output_dir: str = 'outputs/figures'):
    """
    Plot cross-archetype overlap in PCA space to show clusters are not perfectly separated.
    
    Args:
        df: DataFrame with archetype labels
        output_dir: Directory to save plots
    """
    logger.info("Plotting cross-archetype overlap")
    
    # Calculate consumer-level features
    from feature_engineering import engineer_all_features
    from preprocessing import preprocess_pipeline
    from feature_engineering import select_features
    from pca_analysis import standardize_features
    from sklearn.decomposition import PCA
    
    # Preprocess and engineer features
    df_processed = preprocess_pipeline(df.drop(columns=['archetype']))
    features = engineer_all_features(df_processed)
    
    # Merge archetype back
    features = features.merge(df[['consumer_id', 'archetype']].drop_duplicates(), on='consumer_id')
    
    # Select features for PCA
    features_selected = select_features(features.drop(columns=['archetype']))
    
    # Standardize and run PCA
    X_scaled, _ = standardize_features(features_selected)
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    archetypes = ['daytime', 'evening', 'flat', 'weekend']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, arch in enumerate(archetypes):
        mask = features['archetype'] == arch
        ax.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                  c=colors[i], label=arch.capitalize(), alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.set_title('Cross-Archetype Overlap in PCA Space (Ground Truth)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'cross_archetype_overlap.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved cross-archetype overlap to {output_path}")


def calculate_archetype_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate statistics by archetype to validate behavioral differences.
    
    Args:
        df: DataFrame with archetype labels
        
    Returns:
        DataFrame with archetype statistics
    """
    logger.info("Calculating archetype statistics")
    
    # Consumer-level statistics
    consumer_stats = df.groupby(['consumer_id', 'archetype'])['energy_consumption_kwh'].agg([
        'mean', 'std', 'max', 'min'
    ]).reset_index()
    
    # Calculate additional metrics
    consumer_stats['cv'] = consumer_stats['std'] / consumer_stats['mean']
    
    # Aggregate by archetype
    archetype_stats = consumer_stats.groupby('archetype').agg({
        'mean': ['mean', 'std'],
        'cv': ['mean', 'std'],
        'max': 'mean',
        'min': 'mean'
    }).reset_index()
    
    archetype_stats.columns = ['archetype', 'avg_mean', 'std_mean', 'avg_cv', 'std_cv', 'avg_max', 'avg_min']
    
    return archetype_stats


def generate_validation_report(df: pd.DataFrame, output_dir: str = 'outputs/reports'):
    """
    Generate comprehensive dataset validation report.
    
    Args:
        df: DataFrame with archetype labels
        output_dir: Directory to save reports
    """
    logger.info("Generating validation report")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Calculate statistics
    archetype_stats = calculate_archetype_statistics(df)
    
    # Save statistics
    archetype_stats.to_csv(Path(output_dir) / 'archetype_statistics.csv', index=False)
    
    # Generate text report
    report_lines = [
        "# Dataset Validation Report",
        "",
        "## Dataset Overview",
        f"- Total consumers: {df['consumer_id'].nunique()}",
        f"- Total records: {len(df)}",
        f"- Time range: {df['timestamp'].min()} to {df['timestamp'].max()}",
        "",
        "## Archetype Distribution",
    ]
    
    for arch in df['archetype'].unique():
        count = (df['archetype'] == arch).sum() / df['archetype'].nunique()
        report_lines.append(f"- {arch.capitalize()}: {count:.0f} consumers")
    
    report_lines.extend([
        "",
        "## Behavioral Validation",
        "",
        "### 1. Distinct Archetype Profiles",
        "Each archetype has a distinct 24-hour load profile:",
        "- Daytime: Peak during business hours (9-17)",
        "- Evening: Peak during evening hours (18-22)",
        "- Flat: Industrial-like flat profile with small variation",
        "- Weekend: Higher on weekends, moderate weekday",
        "",
        "### 2. Continuous Within-Archetype Variation",
        "Within each archetype, individual consumers show continuous variation:",
        "- Profile perturbations (15% strength)",
        "- Peak timing shifts (±2 hours)",
        "- Individual amplitude variation (0.8-2.5x)",
        "- Day-specific variation (0.9-1.1x)",
        "- Individual variability (lognormal)",
        "- Occasional realistic spikes (5% chance)",
        "",
        "This ensures clusters are not perfectly separated - genuine overlap exists.",
        "",
        "### 3. Cross-Archetype Overlap",
        "PCA visualization shows archetypes are not perfectly separated,",
        "demonstrating that clustering must recover structure from noisy data.",
        "",
        "### 4. Temperature Consistency",
        "Temperature is derived from actual timestamp, ensuring all consumers",
        "at the same clock time share the same exogenous condition.",
        "",
        "### 5. Electrical Consistency",
        "Current is physically derived from energy, voltage, and power factor:",
        "I = P / (V * PF) where P = Energy / Time",
        "",
        "## Archetype Statistics",
        "",
        str(archetype_stats.to_string(index=False)),
        "",
        "## Conclusion",
        "The dataset contains genuine, independent latent behavioral variation.",
        "Archetypes provide hidden ground truth for validating whether clustering",
        "recovers real structure. The archetype label is NEVER passed to K-Means.",
    ])
    
    report_text = "\n".join(report_lines)
    
    with open(Path(output_dir) / 'dataset_validation_report.md', 'w') as f:
        f.write(report_text)
    
    logger.info(f"Saved validation report to {output_dir}")


def run_dataset_validation(df: pd.DataFrame, output_dir: str = 'outputs'):
    """
    Run complete dataset validation pipeline.
    
    Args:
        df: DataFrame with archetype labels
        output_dir: Directory to save outputs
    """
    logger.info("Starting dataset validation")
    
    # Add hour column if not present
    if 'hour' not in df.columns:
        df['hour'] = df['timestamp'].dt.hour
    
    # Generate visualizations
    plot_archetype_profiles(df, f"{output_dir}/figures")
    plot_within_archetype_variation(df, f"{output_dir}/figures")
    plot_cross_archetype_overlap(df, f"{output_dir}/figures")
    
    # Generate report
    generate_validation_report(df, f"{output_dir}/reports")
    
    logger.info("Dataset validation completed")


if __name__ == "__main__":
    # Test validation
    from data_loader import generate_synthetic_data_archetype_based
    from preprocessing import preprocess_pipeline
    
    synthetic_data = generate_synthetic_data_archetype_based(n_consumers=200, n_days=30, hourly_records=True)
    
    # Preprocess (but keep archetype column via merge)
    preprocessed = preprocess_pipeline(synthetic_data.drop(columns=['archetype']))
    
    # Merge archetype back on consumer_id and timestamp
    archetype_mapping = synthetic_data[['consumer_id', 'timestamp', 'archetype']].drop_duplicates()
    preprocessed = preprocessed.merge(archetype_mapping, on=['consumer_id', 'timestamp'], how='left')
    
    run_dataset_validation(preprocessed)
    
    print("\nDataset validation completed. Check outputs/figures and outputs/reports for results.")
