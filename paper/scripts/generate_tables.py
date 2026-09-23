#!/usr/bin/env python3
"""
Generate LaTeX tables from experimental results.

This script reads actual experimental data and generates properly formatted
LaTeX tables for inclusion in the manuscript.

Usage:
    python paper/scripts/generate_tables.py

Output: paper/tables/*.tex
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
WEB_DATA_DIR = PROJECT_ROOT / "web" / "public" / "data"
TABLES_DIR = PROJECT_ROOT / "paper" / "tables"

# Create tables directory
TABLES_DIR.mkdir(parents=True, exist_ok=True)

def load_web_artifact(filename):
    """Load JSON artifact from web/public/data/"""
    path = WEB_DATA_DIR / filename
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)

def load_output_csv(filename):
    """Load CSV from outputs/metrics/"""
    path = OUTPUTS_DIR / "metrics" / filename
    if not path.exists():
        return None
    return pd.read_csv(path)

def table_dataset_config():
    """Table: Dataset Configuration"""
    print("Generating: dataset_config.tex")
    
    manifest = load_web_artifact("manifest.json")
    if not manifest:
        print("  Skipped: manifest.json not found")
        return
    
    config = manifest.get("configuration", {})
    
    latex = r"""\begin{table}[h]
\centering
\caption{Flagship Dataset Configuration}
\label{tab:dataset_config}
\begin{tabular}{@{}ll@{}}
\toprule
Parameter & Value \\
\midrule
Consumers (N) & """ + str(config.get("n_consumers", "N/A")) + r""" \\
Observation window & """ + str(config.get("duration_days", "N/A")) + r""" days \\
Date range & """ + config.get("date_start", "N/A") + r""" to """ + config.get("date_end", "N/A") + r""" \\
Sampling frequency & Hourly \\
Total records & """ + f"{config.get('total_records', 0):,}" + r""" \\
Hidden archetypes & 4 (daytime, evening, flat, weekend) \\
Random seed & """ + str(config.get("random_seed", 42)) + r""" \\
Configuration hash & \texttt{""" + config.get("config_hash", "N/A") + r"""} \\
\bottomrule
\end{tabular}
\end{table}
"""
    
    with open(TABLES_DIR / "dataset_config.tex", "w") as f:
        f.write(latex)
    print("  ✓ Created dataset_config.tex")

def table_k_selection_sweep():
    """Table: K-Selection Sweep Results"""
    print("Generating: k_selection_sweep.tex")
    
    clustering = load_web_artifact("clustering.json")
    if not clustering:
        print("  Skipped: clustering.json not found")
        return
    
    k_metrics = clustering.get("k_selection_metrics", {})
    selected_k = clustering.get("selected_k", 4)
    
    latex = r"""\begin{table}[h]
\centering
\small
\caption{K-Selection Metrics Sweep}
\label{tab:k_sweep_full}
\begin{tabular}{@{}cccccc@{}}
\toprule
K & Inertia & Silhouette & CH & DB & Stability ARI \\
\midrule
"""
    
    for k in sorted([int(kk) for kk in k_metrics.keys()]):
        metrics = k_metrics[str(k)]
        row_prefix = r"\textbf{" if k == selected_k else ""
        row_suffix = r"}" if k == selected_k else ""
        
        latex += f"{row_prefix}{k}{row_suffix} & "
        latex += f"{row_prefix}{metrics.get('inertia', 0):.1f}{row_suffix} & "
        latex += f"{row_prefix}{metrics.get('silhouette', 0):.4f}{row_suffix} & "
        latex += f"{row_prefix}{metrics.get('calinski_harabasz', 0):.1f}{row_suffix} & "
        latex += f"{row_prefix}{metrics.get('davies_bouldin', 0):.4f}{row_suffix} & "
        latex += f"{row_prefix}{metrics.get('stability_ari', 0):.4f}{row_suffix} \\\\\n"
    
    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""
    
    with open(TABLES_DIR / "k_selection_sweep.tex", "w") as f:
        f.write(latex)
    print("  ✓ Created k_selection_sweep.tex")

def table_cluster_profiles_summary():
    """Table: Cluster Profiles Summary"""
    print("Generating: cluster_profiles_summary.tex")
    
    profiles = load_web_artifact("profiles.json")
    if not profiles:
        print("  Skipped: profiles.json not found")
        return
    
    clusters = profiles.get("clusters", [])
    
    latex = r"""\begin{table}[h]
\centering
\small
\caption{Cluster Profile Summary}
\label{tab:cluster_summary}
\begin{tabular}{@{}lcccccc@{}}
\toprule
Cluster & Size & Peak & Evening & Weekend & Peak-to- & CV \\
 & (N) & Hour & Share & Ratio & Avg & \\
\midrule
"""
    
    for cluster in clusters:
        cid = cluster["cluster_id"]
        size = cluster.get("size", 0)
        peak_hour = cluster.get("peak_hour", 0)
        evening_share = cluster.get("evening_share", 0)
        weekend_ratio = cluster.get("weekend_ratio", 1.0)
        peak_to_avg = cluster.get("peak_to_average_ratio", 0)
        cv = cluster.get("coefficient_of_variation", 0)
        
        latex += f"{cid} & {size} & {peak_hour:02d}:00 & "
        latex += f"{evening_share:.3f} & {weekend_ratio:.3f} & "
        latex += f"{peak_to_avg:.2f} & {cv:.3f} \\\\\n"
    
    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""
    
    with open(TABLES_DIR / "cluster_profiles_summary.tex", "w") as f:
        f.write(latex)
    print("  ✓ Created cluster_profiles_summary.tex")

def table_ablation_results():
    """Table: Ablation Study Results"""
    print("Generating: ablation_results.tex")
    
    ablation_csv = load_output_csv("ablation_study_results.csv")
    if ablation_csv is None:
        print("  Skipped: ablation_study_results.csv not found")
        return
    
    latex = r"""\begin{table}[h]
\centering
\small
\caption{Ablation Study: Feature Set Comparison}
\label{tab:ablation_full}
\begin{tabular}{@{}lccccc@{}}
\toprule
Feature Set & Features & K & Silhouette & Stability & Archetype \\
 & (N) &  &  & ARI & ARI \\
\midrule
"""
    
    for _, row in ablation_csv.iterrows():
        arm = row['feature_set']
        n_features = row['n_features']
        k = row['optimal_k']
        sil = row['silhouette']
        stab = row['stability_ari']
        arch = row['archetype_ari']
        
        # Bold behavioral (shipped)
        if arm == 'behavioral':
            latex += r"\textbf{" + arm + r"} & \textbf{" + str(n_features) + r"} & "
            latex += r"\textbf{" + str(k) + r"} & \textbf{" + f"{sil:.3f}" + r"} & "
            latex += r"\textbf{" + f"{stab:.3f}" + r"} & \textbf{" + f"{arch:.3f}" + r"} \\"
        else:
            latex += f"{arm} & {n_features} & {k} & {sil:.3f} & {stab:.3f} & {arch:.3f} \\\\"
        latex += "\n"
    
    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""
    
    with open(TABLES_DIR / "ablation_results.tex", "w") as f:
        f.write(latex)
    print("  ✓ Created ablation_results.tex")

def table_robustness_summary():
    """Table: Seed Robustness Summary"""
    print("Generating: robustness_summary.tex")
    
    robustness_csv = load_output_csv("seed_robustness_summary.csv")
    if robustness_csv is None:
        print("  Skipped: seed_robustness_summary.csv not found")
        return
    
    latex = r"""\begin{table}[h]
\centering
\small
\caption{Robustness Across 20 Independent Datasets (Mean $\pm$ SD)}
\label{tab:robustness_full}
\begin{tabular}{@{}lcccc@{}}
\toprule
Feature Set & Archetype ARI & Silhouette & Stability & K Modal \\
 & (Mean $\pm$ SD) & (Mean) & (Mean) & (Range) \\
\midrule
"""
    
    for _, row in robustness_csv.iterrows():
        arm = row['feature_set']
        ari_mean = row['archetype_ari_mean']
        ari_std = row['archetype_ari_std']
        sil = row['silhouette_mean']
        stab = row['stability_mean']
        k_modal = row['k_modal']
        k_min = row['k_min']
        k_max = row['k_max']
        
        if arm == 'behavioral':
            latex += r"\textbf{" + arm + r"} & "
            latex += r"\textbf{" + f"{ari_mean:.3f} $\\pm$ {ari_std:.3f}" + r"} & "
            latex += r"\textbf{" + f"{sil:.3f}" + r"} & "
            latex += r"\textbf{" + f"{stab:.3f}" + r"} & "
            latex += r"\textbf{" + f"{k_modal} ({k_min}-{k_max})" + r"} \\"
        else:
            latex += f"{arm} & {ari_mean:.3f} $\\pm$ {ari_std:.3f} & "
            latex += f"{sil:.3f} & {stab:.3f} & {k_modal} ({k_min}-{k_max}) \\\\"
        latex += "\n"
    
    latex += r"""\bottomrule
\end{tabular}
\end{table}
"""
    
    with open(TABLES_DIR / "robustness_summary.tex", "w") as f:
        f.write(latex)
    print("  ✓ Created robustness_summary.tex")

def main():
    """Generate all LaTeX tables"""
    print("=" * 60)
    print("LaTeX Table Generation")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Output directory: {TABLES_DIR}")
    print()
    
    # Generate tables
    table_dataset_config()
    table_k_selection_sweep()
    table_cluster_profiles_summary()
    table_ablation_results()
    table_robustness_summary()
    
    print()
    print("=" * 60)
    print(f"✓ Table generation complete")
    print(f"  Output: {TABLES_DIR}")
    print(f"  Format: LaTeX (.tex files)")
    print(f"  Include in paper: \\input{{tables/filename.tex}}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
