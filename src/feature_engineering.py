"""
Feature Engineering Module
Creates behavioral features with scale/shape separation.
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def engineer_normalized_load_shape(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer normalized 24-hour load profile (shape-only feature).
    This separates timing from magnitude - the core behavioral feature.
    
    Args:
        df: Input DataFrame with consumer_id, hour, and energy_consumption_kwh
        
    Returns:
        DataFrame with 24 normalized hourly features per consumer
    """
    logger.info("Engineering normalized load shape (24-hour profile)")
    
    # Calculate average hourly consumption per consumer
    hourly_profile = df.groupby(['consumer_id', 'hour'])['energy_consumption_kwh'].mean().reset_index()
    
    # Normalize each consumer's profile to sum to 1 (shape-only)
    hourly_profile['normalized_energy'] = hourly_profile.groupby('consumer_id')['energy_consumption_kwh'].transform(
        lambda x: x / x.sum()
    )
    
    # Pivot to wide format (one column per hour)
    shape_features = hourly_profile.pivot(index='consumer_id', columns='hour', values='normalized_energy').reset_index()
    shape_features.columns = [f'hour_{int(h)}_shape' if h != 'consumer_id' else h for h in shape_features.columns]
    
    # Fill any missing hours with 0
    for h in range(24):
        col = f'hour_{h}_shape'
        if col not in shape_features.columns:
            shape_features[col] = 0.0
    
    logger.info(f"Created 24-hour shape features. Shape: {shape_features.shape}")
    return shape_features


def engineer_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer temporal features with energy-based weekend ratio.
    
    Args:
        df: Input DataFrame with temporal features
        
    Returns:
        DataFrame with temporal features
    """
    logger.info("Engineering temporal features")
    
    df_feat = df.copy()
    
    # Time-of-day usage patterns
    if 'hour' in df_feat.columns:
        df_feat['is_morning'] = (df_feat['hour'] >= 6) & (df_feat['hour'] < 12)
        df_feat['is_afternoon'] = (df_feat['hour'] >= 12) & (df_feat['hour'] < 18)
        df_feat['is_evening'] = (df_feat['hour'] >= 18) & (df_feat['hour'] < 24)
        df_feat['is_night'] = (df_feat['hour'] >= 0) & (df_feat['hour'] < 6)
    
    # Aggregate temporal patterns by consumer
    if 'consumer_id' in df_feat.columns:
        temporal_agg = df_feat.groupby('consumer_id').agg({
            'energy_consumption_kwh': [
                lambda x: x[df_feat.loc[x.index, 'is_morning']].mean() if 'is_morning' in df_feat.columns else np.nan,
                lambda x: x[df_feat.loc[x.index, 'is_afternoon']].mean() if 'is_afternoon' in df_feat.columns else np.nan,
                lambda x: x[df_feat.loc[x.index, 'is_evening']].mean() if 'is_evening' in df_feat.columns else np.nan,
                lambda x: x[df_feat.loc[x.index, 'is_night']].mean() if 'is_night' in df_feat.columns else np.nan,
            ],
        }).reset_index()
        
        temporal_agg.columns = ['consumer_id', 'morning_usage', 'afternoon_usage', 
                               'evening_usage', 'night_usage']
        
        # Energy-based weekend ratio: weekend energy / weekday energy
        weekend_energy = df_feat[df_feat['is_weekend']].groupby('consumer_id')['energy_consumption_kwh'].mean()
        weekday_energy = df_feat[~df_feat['is_weekend']].groupby('consumer_id')['energy_consumption_kwh'].mean()
        
        weekend_ratio = (weekend_energy / weekday_energy).rename('weekend_ratio')
        temporal_agg = temporal_agg.set_index('consumer_id').join(weekend_ratio).reset_index()
        
        return temporal_agg
    
    return df_feat


def engineer_load_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer load variability features (shape-based, not scale-based).
    
    Args:
        df: Input DataFrame with energy consumption
        
    Returns:
        DataFrame with load features
    """
    logger.info("Engineering load features")
    
    df_feat = df.copy()
    
    if 'consumer_id' in df_feat.columns:
        load_features = df_feat.groupby('consumer_id').agg({
            'energy_consumption_kwh': [
                lambda x: x.max() / x.mean() if x.mean() > 0 else np.nan,  # Peak-to-average ratio
                lambda x: x.std() / x.mean() if x.mean() > 0 else np.nan,  # Coefficient of variation
                'skew',
                lambda x: x.kurt() if len(x) > 3 else np.nan  # Kurtosis
            ]
        }).reset_index()
        
        load_features.columns = ['consumer_id', 'peak_to_avg_ratio', 
                                 'coefficient_of_variation', 'skewness', 'kurtosis']
        
        return load_features
    
    return df_feat


def engineer_scale_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer scale/context features (magnitude-based).
    These are kept separate from behavioral features.
    
    Args:
        df: Input DataFrame with consumer_id
        
    Returns:
        DataFrame with scale features
    """
    logger.info("Engineering scale features")
    
    scale_features = df.groupby('consumer_id').agg({
        'energy_consumption_kwh': ['mean', 'max', 'min', 'median', 'std', 'sum'],
        'voltage_v': 'mean',
        'current_a': 'mean',
        'power_factor': 'mean',
        'temperature_c': 'mean'
    }).reset_index()
    
    # Flatten column names
    scale_features.columns = ['_'.join(col).strip('_') for col in scale_features.columns.values]
    
    logger.info(f"Scale features shape: {scale_features.shape}")
    return scale_features


def engineer_all_features(df: pd.DataFrame, feature_set: str = 'behavioral') -> pd.DataFrame:
    """
    Complete feature engineering pipeline with scale/shape separation.
    
    Args:
        df: Preprocessed DataFrame
        feature_set: Which feature set to return:
                    - 'behavioral': Shape-only features (normalized profiles, timing, variability)
                    - 'scale': Magnitude features (mean, max, total energy)
                    - 'combined': Both behavioral and scale features
        
    Returns:
        DataFrame with engineered features
    """
    logger.info(f"Starting feature engineering pipeline (feature_set: {feature_set})")
    
    # Engineer shape features (behavioral)
    shape_features = engineer_normalized_load_shape(df)
    temporal_features = engineer_temporal_features(df)
    load_features = engineer_load_features(df)
    
    # Merge behavioral features
    behavioral_features = shape_features.merge(temporal_features, on='consumer_id', how='left')
    behavioral_features = behavioral_features.merge(load_features, on='consumer_id', how='left')
    
    # Engineer scale features (magnitude)
    scale_features = engineer_scale_features(df)
    
    # Select feature set
    if feature_set == 'behavioral':
        features = behavioral_features
    elif feature_set == 'scale':
        features = scale_features
    elif feature_set == 'combined':
        features = behavioral_features.merge(scale_features, on='consumer_id', how='left')
    else:
        raise ValueError(f"Unknown feature_set: {feature_set}")
    
    # Remove constant columns (e.g., month if all same)
    features = features.loc[:, features.nunique() > 1]
    
    # Handle NaN values
    features = features.fillna(0)
    
    logger.info(f"Feature engineering complete. Shape: {features.shape}")
    logger.info(f"Feature columns: {features.columns.tolist()}")
    
    return features


def select_features(df: pd.DataFrame, exclude_cols: list = None, 
                   feature_group: str = 'all') -> pd.DataFrame:
    """
    Select relevant features for analysis by group.
    
    Args:
        df: DataFrame with all features
        exclude_cols: Columns to exclude from selection
        feature_group: Which feature group to select:
                      - 'behavioral': Shape-only features (hour_*_shape, temporal, variability)
                      - 'scale': Magnitude features (mean, max, sum, etc.)
                      - 'all': All features except excluded
        
    Returns:
        DataFrame with selected features
    """
    if exclude_cols is None:
        exclude_cols = ['consumer_id']
    
    if feature_group == 'behavioral':
        # Select shape features (hour_*_shape, temporal, variability)
        selected_cols = [col for col in df.columns 
                        if (col.startswith('hour_') and '_shape' in col) or
                           col in ['morning_usage', 'afternoon_usage', 'evening_usage', 
                                  'night_usage', 'weekend_ratio', 'peak_to_avg_ratio',
                                  'coefficient_of_variation', 'skewness', 'kurtosis']]
    elif feature_group == 'scale':
        # Select scale features (mean, max, sum, etc.)
        selected_cols = [col for col in df.columns 
                        if any(x in col for x in ['mean', 'max', 'min', 'median', 'std', 'sum'])]
    else:
        selected_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Ensure consumer_id is included for merging
    if 'consumer_id' in df.columns and 'consumer_id' not in selected_cols:
        selected_cols = ['consumer_id'] + selected_cols
    
    logger.info(f"Selected {len(selected_cols)} features for analysis (group: {feature_group})")
    return df[selected_cols]


if __name__ == "__main__":
    # Test feature engineering
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    
    synthetic_data = generate_synthetic_data(n_consumers=50, n_days=7, hourly_records=True)
    # Drop archetype column before preprocessing (keep consumer_id)
    preprocessed = preprocess_pipeline(synthetic_data.drop(columns=['archetype']))
    
    print(f"Preprocessed columns: {preprocessed.columns.tolist()}")
    print(f"Has consumer_id: {'consumer_id' in preprocessed.columns}")
    
    # Test different feature sets
    for feature_set in ['behavioral', 'scale', 'combined']:
        features = engineer_all_features(preprocessed, feature_set=feature_set)
        print(f"\n{feature_set.capitalize()} features shape: {features.shape}")
        print(f"Columns: {features.columns.tolist()[:10]}...")
