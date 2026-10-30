"""
Evidence-Based Recommendation Engine Module
Generates prioritized recommendations with clear evidence links.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_evidence_based_recommendation(profile: dict) -> dict:
    """
    Generate a single evidence-based recommendation with clear justification.
    
    Args:
        profile: Dictionary containing cluster profile
        
    Returns:
        Dictionary with recommendation, evidence, and priority
    """
    recommendations = []
    
    avg_consumption = profile.get('avg_consumption', 0)
    cv = profile.get('avg_cv', 0)
    peak_to_avg = profile.get('avg_peak_to_avg', 1)
    evening = profile.get('evening_usage', 0)
    morning = profile.get('morning_usage', 0)
    weekend_ratio = profile.get('weekend_ratio', 0)
    
    # High consumption with evidence
    if avg_consumption > 2.0:
        recommendations.append({
            'recommendation': 'Conduct energy efficiency audit',
            'evidence': f'Average consumption {avg_consumption:.2f} kWh exceeds 2.0 kWh threshold',
            'priority': 'high',
            'category': 'consumption'
        })
    
    # High variability with evidence
    if cv > 0.6:
        recommendations.append({
            'recommendation': 'Implement load monitoring and energy storage',
            'evidence': f'Coefficient of variation {cv:.2f} indicates high usage volatility',
            'priority': 'high',
            'category': 'variability'
        })
    
    # High peak-to-average with evidence
    if peak_to_avg > 2.5:
        recommendations.append({
            'recommendation': 'Implement peak-load shifting and demand-response programs',
            'evidence': f'Peak-to-average ratio {peak_to_avg:.2f} indicates significant peak loads',
            'priority': 'high',
            'category': 'peak_management'
        })
    
    # Evening-heavy with evidence
    if evening > morning * 1.5 and evening > 0.5:
        recommendations.append({
            'recommendation': 'Shift evening loads to off-peak hours',
            'evidence': f'Evening usage ({evening:.3f}) is {evening/morning:.1f}x higher than morning usage',
            'priority': 'medium',
            'category': 'temporal'
        })
    
    # Weekend-dominant with evidence
    if weekend_ratio > 1.2:
        recommendations.append({
            'recommendation': 'Optimize time-of-use scheduling for weekend patterns',
            'evidence': f'Weekend-to-weekday ratio {weekend_ratio:.2f} indicates weekend-dominant usage',
            'priority': 'medium',
            'category': 'temporal'
        })
    
    return recommendations


def prioritize_recommendations(recommendations: list) -> list:
    """
    Prioritize recommendations by impact and category.
    
    Priority order: high > medium > low
    Within priority: consumption > peak_management > variability > temporal
    
    Args:
        recommendations: List of recommendation dictionaries
        
    Returns:
        Prioritized list of recommendations
    """
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    category_order = {'consumption': 0, 'peak_management': 1, 'variability': 2, 'temporal': 3}
    
    return sorted(recommendations, key=lambda x: (
        priority_order.get(x.get('priority', 'low'), 2),
        category_order.get(x.get('category', 'temporal'), 3)
    ))


def generate_cluster_recommendations(profiles: pd.DataFrame) -> pd.DataFrame:
    """
    Generate evidence-based recommendations for all clusters.
    
    Args:
        profiles: DataFrame with cluster profiles
        
    Returns:
        DataFrame with recommendations for each cluster
    """
    logger.info("Generating evidence-based recommendations for all clusters")
    
    all_recommendations = []
    
    for _, profile in profiles.iterrows():
        profile_dict = profile.to_dict()
        cluster_id = profile_dict['cluster']
        cluster_name = profile_dict.get('cluster_name', f'Cluster {cluster_id}')
        
        recommendations = generate_evidence_based_recommendation(profile_dict)
        prioritized = prioritize_recommendations(recommendations)
        
        for i, rec in enumerate(prioritized):
            all_recommendations.append({
                'cluster': cluster_id,
                'cluster_name': cluster_name,
                'recommendation': rec['recommendation'],
                'evidence': rec['evidence'],
                'priority': rec['priority'],
                'category': rec['category'],
                'rank': i + 1
            })
    
    recommendations_df = pd.DataFrame(all_recommendations)
    
    logger.info(f"Generated {len(recommendations_df)} recommendations across {len(profiles)} clusters")
    return recommendations_df


def save_recommendations(recommendations: pd.DataFrame, output_dir: str = 'outputs/reports'):
    """
    Save recommendations to CSV and markdown report.
    
    Args:
        recommendations: DataFrame with recommendations
        output_dir: Directory to save reports
    """
    logger.info("Saving recommendations")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    recommendations.to_csv(Path(output_dir) / 'recommendations.csv', index=False)
    
    # Generate markdown report
    generate_recommendations_report(recommendations, output_dir)
    
    logger.info(f"Recommendations saved to {output_dir}")


def generate_recommendations_report(recommendations: pd.DataFrame, output_dir: str):
    """
    Generate human-readable recommendations report.
    
    Args:
        recommendations: DataFrame with recommendations
        output_dir: Directory to save report
    """
    logger.info("Generating recommendations report")
    
    report_lines = [
        "# Evidence-Based Recommendations Report",
        "",
        "## Methodology",
        "Recommendations are generated based on cluster profile characteristics.",
        "Each recommendation includes:",
        "- **Recommendation**: Specific action to take",
        "- **Evidence**: Quantitative justification from cluster profile",
        "- **Priority**: High/Medium/Low based on impact",
        "- **Category**: Type of recommendation (consumption, peak_management, variability, temporal)",
        "",
        "## Recommendations by Cluster",
        ""
    ]
    
    for cluster_id in sorted(recommendations['cluster'].unique()):
        cluster_recs = recommendations[recommendations['cluster'] == cluster_id].sort_values('rank')
        cluster_name = cluster_recs.iloc[0]['cluster_name']
        
        report_lines.extend([
            f"### {cluster_name} (Cluster {cluster_id})",
            ""
        ])
        
        for _, rec in cluster_recs.iterrows():
            report_lines.extend([
                f"**{rec['rank']}. {rec['recommendation']}** [{rec['priority'].upper()}]",
                f"- Evidence: {rec['evidence']}",
                f"- Category: {rec['category']}",
                ""
            ])
    
    report_text = "\n".join(report_lines)
    
    with open(Path(output_dir) / 'recommendations_report.md', 'w') as f:
        f.write(report_text)
    
    logger.info(f"Recommendations report saved to {output_dir}")


def run_recommendation_engine(profiles: pd.DataFrame, output_dir: str = 'outputs/reports') -> pd.DataFrame:
    """
    Run complete recommendation engine pipeline.
    
    Args:
        profiles: DataFrame with cluster profiles
        output_dir: Directory to save outputs
        
    Returns:
        DataFrame with recommendations
    """
    logger.info("Starting recommendation engine")
    
    # Generate recommendations
    recommendations = generate_cluster_recommendations(profiles)
    
    # Save recommendations
    save_recommendations(recommendations, output_dir)
    
    logger.info("Recommendation engine completed")
    return recommendations


if __name__ == "__main__":
    # Test recommendation engine
    from cluster_profiling import run_cluster_profiling
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    from clustering import run_clustering_pipeline
    
    synthetic_data = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(synthetic_data.drop(columns=['archetype']))
    
    features_behavioral = engineer_all_features(preprocessed, feature_set='behavioral')
    features_behavioral_selected = select_features(features_behavioral, feature_group='behavioral')
    
    X_pca, pca, scaler, n_components = run_pca_pipeline(features_behavioral_selected)
    kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores, ch_scores, db_scores, stability_results = run_clustering_pipeline(X_pca, test_stability=False)
    
    features_combined = engineer_all_features(preprocessed, feature_set='combined')
    profiles, insights = run_cluster_profiling(features_combined, labels)
    
    recommendations = run_recommendation_engine(profiles)
    
    print("\nRecommendations:")
    print(recommendations.to_string(index=False))
