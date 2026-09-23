#!/usr/bin/env python3
"""
Generate publication-quality figures for research paper.

This script reads actual experimental results and generates vector-format
figures suitable for LaTeX inclusion. All figures trace to committed artifacts.

Usage:
    python paper/scripts/generate_figures.py

Output: paper/figures/*.pdf (vector format for LaTeX)
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path

# Configure matplotlib for publication quality
mpl.rcParams['figure.dpi'] = 300
mpl.rcParams['savefig.dpi'] = 300
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.size'] = 10
mpl.rcParams['axes.labelsize'] = 10
mpl.rcParams['axes.titlesize'] = 11
mpl.rcParams['xtick.labelsize'] = 9
mpl.rcParams['ytick.labelsize'] = 9
mpl.rcParams['legend.fontsize'] = 9
mpl.rcParams['figure.titlesize'] = 11

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
WEB_DATA_DIR = PROJECT_ROOT / "web" / "public" / "data"
FIGURES_DIR = PROJECT_ROOT / "paper" / "figures"

# Create figures directory
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def load_web_artifact(filename):
    """Load JSON artifact from web/public/data/"""
    path = WEB_DATA_DIR / filename
    if not path.exists():
        print(f"Warning: {filename} not found in {WEB_DATA_DIR}")
        return None
    with open(path) as f:
        return json.load(f)

def load_output_csv(filename):
    """Load CSV from outputs/metrics/"""
    path = OUTPUTS_DIR / "metrics" / filename
    if not path.exists():
        print(f"Warning: {filename} not found")
        return None
    return pd.read_csv(path)

def figure_pca_variance():
    """Figure: PCA Explained and Cumulative Variance"""
    print("Generating: pca_variance.pdf")
    
    pca_data = load_web_artifact("pca.json")
    if not pca_data or not pca_data.get("available"):
        print("  Skipped: PCA data not available")
        return
    
    explained_var = pca_data["explained_variance"]
    cumulative_var = pca_data["cumulative_variance"]
    n_components = len(explained_var)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # Explained variance
    ax1.bar(range(1, n_components + 1), explained_var, 
            color='steelblue', edgecolor='black', linewidth=0.5)
    ax1.axhline(y=0.05, color='red', linestyle='--', linewidth=1, 
                label='5% threshold')
    ax1.set_xlabel('Principal Component')
    ax1.set_ylabel('Explained Variance Ratio')
    ax1.set_title('(a) Explained Variance per Component')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Cumulative variance
    ax2.plot(range(1, n_components + 1), cumulative_var, 
             marker='o', color='darkgreen', linewidth=2, markersize=4)
    ax2.axhline(y=0.95, color='red', linestyle='--', linewidth=1,
                label='95% threshold')
    retained = pca_data.get("n_components_retained", 10)
    ax2.axvline(x=retained, color='orange', linestyle=':', linewidth=1.5,
                label=f'{retained} components')
    ax2.set_xlabel('Number of Components')
    ax2.set_ylabel('Cumulative Variance Explained')
    ax2.set_title('(b) Cumulative Variance Curve')
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "pca_variance.pdf", bbox_inches='tight')
    plt.close()
    print("  ✓ Created pca_variance.pdf")

def figure_k_selection():
    """Figure: K-Selection Metrics Sweep"""
    print("Generating: k_selection_metrics.pdf")
    
    clustering_data = load_web_artifact("clustering.json")
    if not clustering_data or not clustering_data.get("available"):
        print("  Skipped: Clustering data not available")
        return
    
    k_metrics = clustering_data.get("k_selection_metrics", {})
    if not k_metrics:
        print("  Skipped: K-selection metrics not found")
        return
    
    k_values = sorted([int(k) for k in k_metrics.keys()])
    silhouette = [k_metrics[str(k)]["silhouette"] for k in k_values]
    ch_index = [k_metrics[str(k)]["calinski_harabasz"] for k in k_values]
    db_index = [k_metrics[str(k)]["davies_bouldin"] for k in k_values]
    
    selected_k = clustering_data.get("selected_k", 4)
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    
    # Silhouette
    ax = axes[0, 0]
    ax.plot(k_values, silhouette, marker='o', color='steelblue', linewidth=2)
    ax.axvline(x=selected_k, color='red', linestyle='--', linewidth=1.5,
               label=f'Selected K={selected_k}')
    ax.set_xlabel('Number of Clusters (K)')
    ax.set_ylabel('Silhouette Score')
    ax.set_title('(a) Silhouette Coefficient')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Calinski-Harabasz
    ax = axes[0, 1]
    ax.plot(k_values, ch_index, marker='s', color='darkgreen', linewidth=2)
    ax.axvline(x=selected_k, color='red', linestyle='--', linewidth=1.5,
               label=f'Selected K={selected_k}')
    ax.set_xlabel('Number of Clusters (K)')
    ax.set_ylabel('Calinski-Harabasz Index')
    ax.set_title('(b) Calinski-Harabasz (Variance Ratio)')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Davies-Bouldin
    ax = axes[1, 0]
    ax.plot(k_values, db_index, marker='^', color='darkorange', linewidth=2)
    ax.axvline(x=selected_k, color='red', linestyle='--', linewidth=1.5,
               label=f'Selected K={selected_k}')
    ax.set_xlabel('Number of Clusters (K)')
    ax.set_ylabel('Davies-Bouldin Index')
    ax.set_title('(c) Davies-Bouldin (Lower is Better)')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Composite score
    ax = axes[1, 1]
    if "composite_scores" in clustering_data:
        composite = clustering_data["composite_scores"]
        comp_k = sorted([int(k) for k in composite.keys()])
        comp_values = [composite[str(k)] for k in comp_k]
        ax.plot(comp_k, comp_values, marker='D', color='purple', linewidth=2)
        ax.axvline(x=selected_k, color='red', linestyle='--', linewidth=1.5,
                   label=f'Selected K={selected_k}')
        ax.set_xlabel('Number of Clusters (K)')
        ax.set_ylabel('Composite Score')
        ax.set_title('(d) Normalized Composite Score')
        ax.legend()
        ax.grid(alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'Composite scores\nnot available',
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title('(d) Composite Score (N/A)')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "k_selection_metrics.pdf", bbox_inches='tight')
    plt.close()
    print("  ✓ Created k_selection_metrics.pdf")

def figure_cluster_profiles():
    """Figure: Cluster Average Daily Profiles"""
    print("Generating: cluster_profiles.pdf")
    
    profiles_data = load_web_artifact("profiles.json")
    if not profiles_data or not profiles_data.get("available"):
        print("  Skipped: Profiles data not available")
        return
    
    clusters = profiles_data.get("clusters", [])
    if not clusters:
        print("  Skipped: No cluster data")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    hours = np.arange(24)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for idx, cluster in enumerate(clusters):
        cluster_id = cluster["cluster_id"]
        name = cluster.get("name", f"Cluster {cluster_id}")
        shape = cluster.get("mean_hourly_shape", [])
        
        if len(shape) == 24:
            color = colors[idx % len(colors)]
            ax.plot(hours, shape, marker='o', linewidth=2, markersize=4,
                   label=f"Cluster {cluster_id}: {name}", color=color)
    
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Normalized Load (Fraction of Daily Total)')
    ax.set_title('Mean 24-Hour Load Profiles by Cluster')
    ax.set_xticks(range(0, 24, 2))
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "cluster_profiles.pdf", bbox_inches='tight')
    plt.close()
    print("  ✓ Created cluster_profiles.pdf")

def figure_archetype_recovery():
    """Figure: ARI/NMI vs K (Ground Truth Recovery)"""
    print("Generating: archetype_recovery.pdf")
    
    validation_data = load_web_artifact("validation.json")
    if not validation_data or not validation_data.get("available"):
        print("  Skipped: Validation data not available")
        return
    
    recovery_by_k = validation_data.get("recovery_by_k", {})
    if not recovery_by_k:
        print("  Skipped: Recovery metrics not found")
        return
    
    k_values = sorted([int(k) for k in recovery_by_k.keys()])
    ari_values = [recovery_by_k[str(k)]["ari"] for k in k_values]
    nmi_values = [recovery_by_k[str(k)]["nmi"] for k in k_values]
    
    clustering_data = load_web_artifact("clustering.json")
    selected_k = clustering_data.get("selected_k", 4) if clustering_data else 4
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.plot(k_values, ari_values, marker='o', linewidth=2, markersize=6,
            label='Adjusted Rand Index (ARI)', color='steelblue')
    ax.plot(k_values, nmi_values, marker='s', linewidth=2, markersize=6,
            label='Normalized Mutual Information (NMI)', color='darkgreen')
    ax.axvline(x=selected_k, color='red', linestyle='--', linewidth=1.5,
               label=f'Selected K={selected_k}')
    
    # Mark maximum
    max_ari_k = k_values[np.argmax(ari_values)]
    max_ari = max(ari_values)
    ax.plot(max_ari_k, max_ari, marker='*', markersize=15, color='gold',
            markeredgecolor='black', markeredgewidth=1, label='Max ARI')
    
    ax.set_xlabel('Number of Clusters (K)')
    ax.set_ylabel('Recovery Score')
    ax.set_title('Ground Truth Recovery: ARI and NMI vs K')
    ax.legend(loc='best')
    ax.grid(alpha=0.3)
    ax.set_ylim([0, 1.0])
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "archetype_recovery.pdf", bbox_inches='tight')
    plt.close()
    print("  ✓ Created archetype_recovery.pdf")

def figure_ablation_comparison():
    """Figure: Ablation Study - Feature Set Comparison"""
    print("Generating: ablation_comparison.pdf")
    
    ablation_csv = load_output_csv("ablation_study_results.csv")
    if ablation_csv is None:
        print("  Skipped: ablation_study_results.csv not found")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    
    arms = ablation_csv['feature_set'].tolist()
    silhouette = ablation_csv['silhouette'].tolist()
    archetype_ari = ablation_csv['archetype_ari'].tolist()
    stability = ablation_csv['stability_ari'].tolist()
    
    colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4', '#9467bd']
    
    # Silhouette
    ax = axes[0]
    bars = ax.bar(arms, silhouette, color=colors, edgecolor='black', linewidth=0.7)
    ax.set_ylabel('Silhouette Score')
    ax.set_title('(a) Internal Quality (Silhouette)')
    ax.set_ylim([0, max(silhouette) * 1.1])
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    
    # Archetype ARI
    ax = axes[1]
    bars = ax.bar(arms, archetype_ari, color=colors, edgecolor='black', linewidth=0.7)
    ax.set_ylabel('Archetype ARI')
    ax.set_title('(b) Ground Truth Recovery')
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax.set_ylim([min(archetype_ari) - 0.1, max(archetype_ari) * 1.1])
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    
    # Stability
    ax = axes[2]
    bars = ax.bar(arms, stability, color=colors, edgecolor='black', linewidth=0.7)
    ax.set_ylabel('Stability ARI')
    ax.set_title('(c) Multi-Seed Stability')
    ax.set_ylim([0.9, 1.0])
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "ablation_comparison.pdf", bbox_inches='tight')
    plt.close()
    print("  ✓ Created ablation_comparison.pdf")

def figure_temporal_stability():
    """Figure: Temporal Stability Across Segments"""
    print("Generating: temporal_stability.pdf")
    
    longitudinal_data = load_web_artifact("longitudinal.json")
    if not longitudinal_data or not longitudinal_data.get("available"):
        print("  Skipped: Longitudinal data not available")
        return
    
    segments = longitudinal_data.get("segments", [])
    if not segments:
        print("  Skipped: No segment data")
        return
    
    segment_names = [f"Q{i+1}" for i in range(len(segments))]
    ari_values = [seg["ari_vs_full"] for seg in segments]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    bars = ax.bar(segment_names, ari_values, color='steelblue',
                   edgecolor='black', linewidth=1)
    ax.axhline(y=np.mean(ari_values), color='red', linestyle='--',
               linewidth=2, label=f'Mean ARI = {np.mean(ari_values):.3f}')
    ax.set_xlabel('Quarterly Segment')
    ax.set_ylabel('ARI vs Full Window')
    ax.set_title('Temporal Stability: Segment Partitions vs Full Window')
    ax.set_ylim([0.7, 1.0])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "temporal_stability.pdf", bbox_inches='tight')
    plt.close()
    print("  ✓ Created temporal_stability.pdf")

def main():
    """Generate all publication figures"""
    print("=" * 60)
    print("Publication Figure Generation")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Output directory: {FIGURES_DIR}")
    print()
    
    # Check data availability
    if not WEB_DATA_DIR.exists():
        print(f"ERROR: {WEB_DATA_DIR} not found")
        print("Run 'python src/energy_analysis.py' first to generate artifacts")
        return 1
    
    # Generate figures
    figure_pca_variance()
    figure_k_selection()
    figure_cluster_profiles()
    figure_archetype_recovery()
    figure_ablation_comparison()
    figure_temporal_stability()
    
    print()
    print("=" * 60)
    print(f"✓ Figure generation complete")
    print(f"  Output: {FIGURES_DIR}")
    print(f"  Format: PDF (vector, suitable for LaTeX)")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
