"""
Cluster Profiling Module
Profiles clusters and generates optimization recommendations.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def profile_clusters(features: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """
    Profile each cluster using statistical summaries.
    
    Args:
        features: DataFrame with engineered features (including consumer_id)
        labels: Cluster labels
        
    Returns:
        DataFrame with cluster profiles
    """
    logger.info("Profiling clusters")
    
    # Add labels to features
    features_with_labels = features.copy()
    features_with_labels['cluster'] = labels
    
    # Calculate cluster profiles
    cluster_profiles = []
    
    for cluster_id in sorted(np.unique(labels)):
        cluster_data = features_with_labels[features_with_labels['cluster'] == cluster_id]
        
        profile = {
            'cluster': cluster_id,
            'size': len(cluster_data),
            'size_percentage': len(cluster_data) / len(features_with_labels) * 100
        }
        
        # Consumption statistics
        if 'energy_consumption_kwh_mean' in cluster_data.columns:
            profile['avg_consumption'] = cluster_data['energy_consumption_kwh_mean'].mean()
            profile['peak_consumption'] = cluster_data['energy_consumption_kwh_max'].mean()
            profile['min_consumption'] = cluster_data['energy_consumption_kwh_min'].mean()
            profile['consumption_std'] = cluster_data['energy_consumption_kwh_std'].mean()
        
        # Variability
        if 'coefficient_of_variation' in cluster_data.columns:
            profile['avg_cv'] = cluster_data['coefficient_of_variation'].mean()
        
        if 'peak_to_avg_ratio' in cluster_data.columns:
            profile['avg_peak_to_avg'] = cluster_data['peak_to_avg_ratio'].mean()
        
        # Temporal patterns
        if 'morning_usage' in cluster_data.columns:
            profile['morning_usage'] = cluster_data['morning_usage'].mean()
            profile['afternoon_usage'] = cluster_data['afternoon_usage'].mean()
            profile['evening_usage'] = cluster_data['evening_usage'].mean()
            profile['night_usage'] = cluster_data['night_usage'].mean()
        
        if 'weekend_ratio' in cluster_data.columns:
            profile['weekend_ratio'] = cluster_data['weekend_ratio'].mean()
        
        # Other features
        if 'temperature_c_mean' in cluster_data.columns:
            profile['avg_temperature'] = cluster_data['temperature_c_mean'].mean()
        
        cluster_profiles.append(profile)
    
    profiles_df = pd.DataFrame(cluster_profiles)
    
    logger.info(f"Cluster profiling completed. {len(profiles_df)} clusters profiled")
    return profiles_df


def interpret_cluster(profile: dict) -> str:
    """
    Generate a textual interpretation of a cluster based on its profile.
    
    Args:
        profile: Dictionary containing cluster profile
        
    Returns:
        Textual interpretation of the cluster
    """
    interpretations = []
    
    # Consumption level
    avg_consumption = profile.get('avg_consumption', 0)
    if avg_consumption < 1.0:
        interpretations.append("Low consumption consumers")
    elif avg_consumption < 1.5:
        interpretations.append("Moderate consumption consumers")
    else:
        interpretations.append("High consumption consumers")
    
    # Variability
    cv = profile.get('avg_cv', 0)
    if cv < 0.3:
        interpretations.append("with stable usage patterns")
    elif cv < 0.5:
        interpretations.append("with moderate variability")
    else:
        interpretations.append("with highly variable usage")
    
    # Peak patterns
    peak_to_avg = profile.get('avg_peak_to_avg', 1)
    if peak_to_avg > 2.0:
        interpretations.append("and significant peak loads")
    
    # Temporal patterns
    morning = profile.get('morning_usage', 0)
    evening = profile.get('evening_usage', 0)
    night = profile.get('night_usage', 0)
    
    if morning > evening and morning > night:
        interpretations.append("with morning-heavy usage")
    elif evening > morning and evening > night:
        interpretations.append("with evening-heavy usage")
    elif night > morning and night > evening:
        interpretations.append("with night-heavy usage")
    
    weekend_ratio = profile.get('weekend_ratio', 1.0)
    if weekend_ratio > 1.15:
        interpretations.append("and weekend-oriented energy intensity")
    elif weekend_ratio < 0.85:
        interpretations.append("and weekday-oriented energy intensity")
    
    return " ".join(interpretations)


def generate_recommendations(profile: dict) -> list:
    """
    Generate evidence-based energy optimization recommendations specific to cluster profile.
    No generic recommendations - only those supported by cluster characteristics.
    
    Args:
        profile: Dictionary containing cluster profile
        
    Returns:
        List of specific recommendations
    """
    recommendations = []
    
    avg_consumption = profile.get('avg_consumption', 0)
    cv = profile.get('avg_cv', 0)
    peak_to_avg = profile.get('avg_peak_to_avg', 1)
    evening = profile.get('evening_usage', 0)
    morning = profile.get('morning_usage', 0)
    weekend_ratio = profile.get('weekend_ratio', 0)
    
    # High consumption recommendations (only if truly high)
    if avg_consumption > 2.0:
        recommendations.append("Consider energy efficiency audits to identify reduction opportunities")
        recommendations.append("Evaluate equipment upgrades for more efficient alternatives")
    
    # High variability recommendations (only if truly variable)
    if cv > 0.6:
        recommendations.append("Implement load monitoring to understand usage patterns")
        recommendations.append("Consider energy storage to smooth demand fluctuations")
    
    # High peak-to-average recommendations (only if truly high)
    if peak_to_avg > 2.5:
        recommendations.append("Implement peak-load shifting strategies")
        recommendations.append("Consider demand-response programs to reduce peak charges")
        recommendations.append("Schedule high-energy tasks during off-peak hours")
    
    # Evening-heavy usage recommendations (only if significantly evening-heavy)
    if evening > morning * 1.5 and evening > 0.5:
        recommendations.append("Consider shifting evening loads to earlier hours")
        recommendations.append("Implement smart scheduling for appliances")
    
    # Weekend-specific recommendations
    if weekend_ratio > 1.2:
        recommendations.append("Weekend-dominant usage: Consider time-of-use optimization")
    elif weekend_ratio < 0.8:
        recommendations.append("Weekday-dominant usage: Consider weekend load shifting")
    
    # Only add recommendations if there are specific characteristics to address
    return recommendations


def name_cluster(profile: dict, population: dict = None) -> str:
    """
    Generate a descriptive name from measured behavioral traits.
    Uses weekend ratio and peakiness when absolute scale is compressed
    (normalized behavioral experiments often share low absolute kWh means).
    """
    if population is None:
        population = {}

    weekend_ratio = float(profile.get('weekend_ratio', 1.0) or 1.0)
    peak_to_avg = float(profile.get('avg_peak_to_avg', 0) or 0)
    cv = float(profile.get('avg_cv', 0) or 0)
    avg_consumption = float(profile.get('avg_consumption', 0) or 0)

    morning = float(profile.get('morning_usage', 0) or 0)
    afternoon = float(profile.get('afternoon_usage', 0) or 0)
    evening = float(profile.get('evening_usage', 0) or 0)
    night = float(profile.get('night_usage', 0) or 0)
    max_period = max(morning, afternoon, evening, night)

    if weekend_ratio >= 1.15:
        primary = "Weekend-Oriented"
    elif weekend_ratio <= 0.85:
        primary = "Weekday-Oriented"
    elif max_period == evening and evening > 0:
        primary = "Evening-Peak"
    elif max_period == morning and morning > 0:
        primary = "Morning-Peak"
    elif max_period == afternoon and afternoon > 0:
        primary = "Afternoon-Peak"
    elif max_period == night and night > 0:
        primary = "Night-Peak"
    else:
        primary = "Balanced-Timing"

    if peak_to_avg >= 9.0 or cv >= 1.2:
        secondary = "Spiky-Variable"
    elif peak_to_avg <= 5.0 and cv <= 0.8:
        secondary = "Flat-Stable"
    elif cv >= 1.0:
        secondary = "High-Variability"
    else:
        secondary = "Moderate-Variability"

    # Optional scale tag only when magnitude actually differs across clusters
    pop_mean = population.get('avg_consumption')
    if pop_mean and avg_consumption > 0:
        if avg_consumption < 0.85 * pop_mean:
            scale = "Lower-Scale"
        elif avg_consumption > 1.15 * pop_mean:
            scale = "Higher-Scale"
        else:
            scale = None
    else:
        scale = None

    parts = [primary, secondary] if scale is None else [scale, primary, secondary]
    return " ".join(parts)


def save_cluster_profiles(profiles: pd.DataFrame, output_dir: str = 'outputs/reports') -> pd.DataFrame:
    """
    Save cluster profiles to CSV with descriptive names.
    
    Args:
        profiles: DataFrame with cluster profiles
        output_dir: Directory to save reports
        
    Returns:
        DataFrame with cluster names added
    """
    logger.info("Saving cluster profiles")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    population = {
        'avg_consumption': float(profiles['avg_consumption'].median())
        if 'avg_consumption' in profiles.columns else None
    }
    profiles_with_names = profiles.copy()
    profiles_with_names['cluster_name'] = profiles_with_names.apply(
        lambda row: name_cluster(row.to_dict(), population), axis=1
    )
    
    profiles_with_names.to_csv(Path(output_dir) / 'cluster_profiles.csv', index=False)
    
    logger.info(f"Cluster profiles saved to {output_dir}")
    return profiles_with_names


def save_cluster_insights(profiles: pd.DataFrame, output_dir: str = 'outputs/reports'):
    """
    Save detailed cluster insights including interpretations and recommendations.
    
    Args:
        profiles: DataFrame with cluster profiles
        output_dir: Directory to save reports
    """
    logger.info("Generating cluster insights")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    insights = []
    for _, profile in profiles.iterrows():
        profile_dict = profile.to_dict()
        interpretation = interpret_cluster(profile_dict)
        recommendations = generate_recommendations(profile_dict)
        
        insight = {
            'cluster': profile_dict['cluster'],
            'interpretation': interpretation,
            'recommendations': '; '.join(recommendations)
        }
        insights.append(insight)
    
    insights_df = pd.DataFrame(insights)
    insights_df.to_csv(Path(output_dir) / 'cluster_insights.csv', index=False)
    
    logger.info(f"Cluster insights saved to {output_dir}")
    return insights_df


def run_cluster_profiling(features: pd.DataFrame, labels: np.ndarray,
                         output_dir: str = 'outputs/reports') -> tuple:
    """
    Run complete cluster profiling pipeline.
    
    Args:
        features: DataFrame with engineered features
        labels: Cluster labels
        output_dir: Directory to save outputs
        
    Returns:
        Tuple of (profiles_df_with_names, insights_df)
    """
    logger.info("Starting cluster profiling pipeline")
    
    # Profile clusters
    profiles = profile_clusters(features, labels)
    
    # Save profiles with names
    profiles_with_names = save_cluster_profiles(profiles, output_dir)
    
    # Generate and save insights
    insights = save_cluster_insights(profiles_with_names, output_dir)
    
    logger.info("Cluster profiling pipeline completed")
    return profiles_with_names, insights


if __name__ == "__main__":
    # Test cluster profiling with combined features for complete profiling
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    from clustering import run_clustering_pipeline
    
    synthetic_data = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(synthetic_data.drop(columns=['archetype']))
    
    # Use behavioral features for clustering (more meaningful for behavioral patterns)
    features_behavioral = engineer_all_features(preprocessed, feature_set='behavioral')
    features_behavioral_selected = select_features(features_behavioral, feature_group='behavioral')
    
    X_pca, pca, scaler, n_components = run_pca_pipeline(features_behavioral_selected)
    kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores, ch_scores, db_scores, stability_results = run_clustering_pipeline(X_pca, test_stability=False)
    
    # Use combined features for profiling (includes scale features for complete profile)
    features_combined = engineer_all_features(preprocessed, feature_set='combined')
    
    profiles, insights = run_cluster_profiling(features_combined, labels)
    
    print("\nCluster Profiles:")
    print(profiles.to_string(index=False))
    
    print("\nCluster Insights:")
    for _, row in insights.iterrows():
        print(f"\nCluster {row['cluster']}:")
        print(f"  Name: {profiles[profiles['cluster'] == row['cluster']]['cluster_name'].values[0]}")
        print(f"  Interpretation: {row['interpretation']}")
        print(f"  Recommendations: {row['recommendations'] if row['recommendations'] else 'No specific recommendations for this cluster'}")
