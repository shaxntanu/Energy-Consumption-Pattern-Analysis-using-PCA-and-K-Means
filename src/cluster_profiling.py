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
    
    weekend_ratio = profile.get('weekend_ratio', 0)
    if weekend_ratio > 0.6:
        interpretations.append("and higher weekend activity")
    elif weekend_ratio < 0.4:
        interpretations.append("and higher weekday activity")
    
    return " ".join(interpretations)


def generate_recommendations(profile: dict) -> list:
    """
    Generate energy optimization recommendations based on cluster profile.
    
    Args:
        profile: Dictionary containing cluster profile
        
    Returns:
        List of recommendations
    """
    recommendations = []
    
    avg_consumption = profile.get('avg_consumption', 0)
    cv = profile.get('avg_cv', 0)
    peak_to_avg = profile.get('avg_peak_to_avg', 1)
    evening = profile.get('evening_usage', 0)
    morning = profile.get('morning_usage', 0)
    
    # High consumption recommendations
    if avg_consumption > 1.5:
        recommendations.append("Consider energy efficiency audits to identify reduction opportunities")
        recommendations.append("Evaluate equipment upgrades for more efficient alternatives")
    
    # High variability recommendations
    if cv > 0.5:
        recommendations.append("Implement load monitoring to understand usage patterns")
        recommendations.append("Consider energy storage to smooth demand fluctuations")
    
    # High peak-to-average recommendations
    if peak_to_avg > 2.0:
        recommendations.append("Implement peak-load shifting strategies")
        recommendations.append("Consider demand-response programs to reduce peak charges")
        recommendations.append("Schedule high-energy tasks during off-peak hours")
    
    # Evening-heavy usage recommendations
    if evening > morning and evening > 0.5:
        recommendations.append("Consider shifting evening loads to earlier hours")
        recommendations.append("Implement smart scheduling for appliances")
    
    # General recommendations
    recommendations.append("Install smart meters for real-time consumption monitoring")
    recommendations.append("Set up automated alerts for unusual consumption patterns")
    recommendations.append("Consider renewable energy integration where feasible")
    
    return recommendations


def save_cluster_profiles(profiles: pd.DataFrame, output_dir: str = 'outputs/reports'):
    """
    Save cluster profiles to CSV.
    
    Args:
        profiles: DataFrame with cluster profiles
        output_dir: Directory to save reports
    """
    logger.info("Saving cluster profiles")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    profiles.to_csv(Path(output_dir) / 'cluster_profiles.csv', index=False)
    
    logger.info(f"Cluster profiles saved to {output_dir}")


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
        Tuple of (profiles_df, insights_df)
    """
    logger.info("Starting cluster profiling pipeline")
    
    # Profile clusters
    profiles = profile_clusters(features, labels)
    
    # Save profiles
    save_cluster_profiles(profiles, output_dir)
    
    # Generate and save insights
    insights = save_cluster_insights(profiles, output_dir)
    
    logger.info("Cluster profiling pipeline completed")
    return profiles, insights


if __name__ == "__main__":
    # Test cluster profiling
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    from feature_engineering import engineer_all_features
    from pca_analysis import run_pca_pipeline
    from clustering import run_clustering_pipeline
    from sklearn.preprocessing import StandardScaler
    
    synthetic_data = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(synthetic_data)
    features = engineer_all_features(preprocessed)
    
    # Select features for PCA (exclude consumer_id)
    from feature_engineering import select_features
    features_selected = select_features(features)
    
    X_pca, pca, scaler, n_components = run_pca_pipeline(features_selected)
    kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores = run_clustering_pipeline(X_pca)
    
    profiles, insights = run_cluster_profiling(features, labels)
    
    print("\nCluster Profiles:")
    print(profiles.to_string(index=False))
    
    print("\nCluster Insights:")
    for _, row in insights.iterrows():
        print(f"\nCluster {row['cluster']}:")
        print(f"  Interpretation: {row['interpretation']}")
        print(f"  Recommendations: {row['recommendations']}")
