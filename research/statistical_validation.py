#!/usr/bin/env python3
"""
Statistical validation and uncertainty quantification.

Provides bootstrap confidence intervals, effect size calculations,
and statistical tests for research claims.

Usage:
    python research/statistical_validation.py
"""

import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "metrics"
RESEARCH_DIR = PROJECT_ROOT / "research"

def bootstrap_confidence_interval(data, metric_fn, n_bootstrap=1000, alpha=0.05):
    """
    Compute bootstrap confidence interval for a metric.
    
    Parameters:
    -----------
    data : array-like
        Input data
    metric_fn : callable
        Function to compute metric (e.g., np.mean, np.median)
    n_bootstrap : int
        Number of bootstrap samples
    alpha : float
        Significance level (0.05 for 95% CI)
    
    Returns:
    --------
    dict with 'mean', 'ci_lower', 'ci_upper', 'std'
    """
    bootstrap_estimates = []
    n = len(data)
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_estimates.append(metric_fn(sample))
    
    bootstrap_estimates = np.array(bootstrap_estimates)
    
    return {
        "mean": metric_fn(data),
        "ci_lower": np.percentile(bootstrap_estimates, 100 * alpha / 2),
        "ci_upper": np.percentile(bootstrap_estimates, 100 * (1 - alpha / 2)),
        "std": np.std(bootstrap_estimates)
    }


def cohen_d(group1, group2):
    """
    Calculate Cohen's d effect size between two groups.
    
    Interpretation:
    - Small effect: d ~ 0.2
    - Medium effect: d ~ 0.5  
    - Large effect: d ~ 0.8
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    d = (np.mean(group1) - np.mean(group2)) / pooled_std
    return d


def paired_permutation_test(group1, group2, n_permutations=10000):
    """
    Paired permutation test for comparing two related samples.
    
    Returns:
    --------
    dict with 'test_statistic', 'p_value', 'significant'
    """
    observed_diff = np.mean(group1) - np.mean(group2)
    
    permuted_diffs = []
    for _ in range(n_permutations):
        # Randomly flip signs
        signs = np.random.choice([-1, 1], size=len(group1))
        diffs = (group1 - group2) * signs
        permuted_diffs.append(np.mean(diffs))
    
    permuted_diffs = np.array(permuted_diffs)
    p_value = np.mean(np.abs(permuted_diffs) >= np.abs(observed_diff))
    
    return {
        "test_statistic": observed_diff,
        "p_value": p_value,
        "significant": p_value < 0.05
    }


def analyze_robustness_study():
    """Analyze seed robustness results with statistical validation"""
    print("=" * 70)
    print("Statistical Validation: Seed Robustness Study")
    print("=" * 70)
    
    # Load robustness data
    robustness_file = OUTPUTS_DIR / "seed_robustness_by_seed.csv"
    if not robustness_file.exists():
        print(f"ERROR: {robustness_file} not found")
        return
    
    df = pd.read_csv(robustness_file)
    
    # Extract feature sets
    feature_sets = df['feature_set'].unique()
    
    print(f"\nDatasets: {len(df['dataset_seed'].unique())}")
    print(f"Feature sets: {', '.join(feature_sets)}")
    print()
    
    results = {}
    
    for fs in feature_sets:
        fs_data = df[df['feature_set'] == fs]['archetype_ari'].values
        
        # Bootstrap CI
        ci = bootstrap_confidence_interval(fs_data, np.mean, n_bootstrap=5000)
        
        results[fs] = {
            "mean": ci["mean"],
            "ci_95_lower": ci["ci_lower"],
            "ci_95_upper": ci["ci_upper"],
            "std": ci["std"],
            "n": len(fs_data)
        }
        
        print(f"{fs:15s}: ARI = {ci['mean']:.3f} "
              f"[95% CI: {ci['ci_lower']:.3f}, {ci['ci_upper']:.3f}], "
              f"SD = {ci['std']:.3f}")
    
    print()
    print("-" * 70)
    print("Pairwise Comparisons (Permutation Tests)")
    print("-" * 70)
    
    # Compare behavioral vs others
    behavioral_data = df[df['feature_set'] == 'behavioral']['archetype_ari'].values
    
    comparisons = []
    for fs in feature_sets:
        if fs == 'behavioral':
            continue
        
        fs_data = df[df['feature_set'] == fs]['archetype_ari'].values
        
        # Permutation test
        perm = paired_permutation_test(behavioral_data, fs_data, n_permutations=10000)
        
        # Effect size
        effect = cohen_d(behavioral_data, fs_data)
        
        comparisons.append({
            "comparison": f"behavioral vs {fs}",
            "mean_diff": perm["test_statistic"],
            "p_value": perm["p_value"],
            "cohens_d": effect,
            "significant": perm["significant"]
        })
        
        sig_marker = "***" if perm["p_value"] < 0.001 else \
                     "**" if perm["p_value"] < 0.01 else \
                     "*" if perm["p_value"] < 0.05 else "ns"
        
        print(f"behavioral vs {fs:12s}: "
              f"Δ={perm['test_statistic']:+.3f}, "
              f"p={perm['p_value']:.4f} {sig_marker}, "
              f"d={effect:.2f}")
    
    # Save results
    output = {
        "analysis": "seed_robustness_statistical_validation",
        "n_datasets": int(len(df['dataset_seed'].unique())),
        "bootstrap_ci": {fs: {k: float(v) if isinstance(v, (np.floating, float)) else int(v) 
                              for k, v in vals.items()} 
                        for fs, vals in results.items()},
        "pairwise_comparisons": comparisons
    }
    
    output_file = RESEARCH_DIR / "robustness_statistical_validation.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print()
    print(f"✓ Results saved: {output_file}")
    print()
    print("Interpretation:")
    print("  *** p < 0.001 (highly significant)")
    print("  **  p < 0.01  (significant)")
    print("  *   p < 0.05  (significant)")
    print("  ns         (not significant)")
    print()
    print("Cohen's d effect size:")
    print("  Small: ~0.2, Medium: ~0.5, Large: ~0.8")


def analyze_stability_metrics():
    """Bootstrap CIs for stability metrics"""
    print("=" * 70)
    print("Statistical Validation: Stability Metrics")
    print("=" * 70)
    
    # This would require re-running clustering with different seeds
    # For now, document the approach
    print("""
To compute bootstrap CIs for flagship stability metrics:

1. Multi-seed stability (currently: mean ARI 0.9947 ± 0.0071):
   - Already computed from 10 restarts
   - 95% CI can be approximated from SD assuming normal distribution
   - CI ≈ [0.9947 - 1.96*0.0071, 0.9947 + 1.96*0.0071]
   - CI ≈ [0.980, 1.000] (clipped at 1.0)

2. Temporal stability (currently: mean ARI 0.882 from 4 segments):
   - Small sample (n=4 quarters)
   - Bootstrap CI with n=4 has high variance
   - Recommend longer observation for tighter CI

3. Ground truth recovery (currently: ARI 0.813):
   - Single run on flagship dataset
   - To compute CI: bootstrap resample consumers, refit clustering
   - Computationally expensive but provides uncertainty bound
   
Implementation: research/bootstrap_flagship_uncertainty.py (future work)
""")


def main():
    """Run all statistical validation analyses"""
    analyze_robustness_study()
    print()
    analyze_stability_metrics()


if __name__ == "__main__":
    main()
