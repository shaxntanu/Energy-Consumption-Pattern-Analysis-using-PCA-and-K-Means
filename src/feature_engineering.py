"""
Feature Engineering Module
Creates behavioral features from energy consumption data.
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def aggregate_by_consumer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate hourly/daily records to consumer-level features.
    
    Args:
        df: Input DataFrame with consumer_id and timestamp
        
    Returns:
        DataFrame aggregated by consumer_id
    """
    logger.info("Aggregating data by consumer")
    
    # Group by consumer_id
    consumer_features = df.groupby('consumer_id').agg({
        'energy_consumption_kwh': [
            'mean', 'max', 'min', 'median', 'std'
        ],
        'voltage_v': 'mean',
        'current_a': 'mean',
        'power_factor': 'mean',
        'temperature_c': 'mean'
    }).reset_index()
    
    # Flatten column names
    consumer_features.columns = ['_'.join(col).strip('_') for col in consumer_features.columns.values]
    
    logger.info(f"Aggregated to {len(consumer_features)} consumers")
    return consumer_features


def engineer_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer time-based consumption features.
    
    Args:
        df: Input DataFrame with temporal features
        
    Returns:
        DataFrame with additional temporal features
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
            'is_weekend': 'mean'
        }).reset_index()
        
        temporal_agg.columns = ['consumer_id', 'morning_usage', 'afternoon_usage', 
                               'evening_usage', 'night_usage', 'weekend_ratio']
        
        return temporal_agg
    
    return df_feat


def engineer_load_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer load-related features.
    
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


def engineer_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Complete feature engineering pipeline.
    
    Args:
        df: Preprocessed DataFrame
        
    Returns:
        DataFrame with all engineered features
    """
    logger.info("Starting feature engineering pipeline")
    
    # Aggregate basic statistics
    consumer_stats = aggregate_by_consumer(df)
    
    # Engineer temporal features
    temporal_features = engineer_temporal_features(df)
    
    # Engineer load features
    load_features = engineer_load_features(df)
    
    # Merge all features
    features = consumer_stats.merge(temporal_features, on='consumer_id', how='left')
    features = features.merge(load_features, on='consumer_id', how='left')
    
    # Handle any remaining NaN values
    features = features.fillna(0)
    
    logger.info(f"Feature engineering complete. Shape: {features.shape}")
    logger.info(f"Feature columns: {features.columns.tolist()}")
    
    return features


def select_features(df: pd.DataFrame, exclude_cols: list = None) -> pd.DataFrame:
    """
    Select relevant features for analysis.
    
    Args:
        df: DataFrame with all features
        exclude_cols: Columns to exclude from selection
        
    Returns:
        DataFrame with selected features
    """
    if exclude_cols is None:
        exclude_cols = ['consumer_id']
    
    selected_cols = [col for col in df.columns if col not in exclude_cols]
    
    logger.info(f"Selected {len(selected_cols)} features for analysis")
    return df[selected_cols]


if __name__ == "__main__":
    # Test feature engineering
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline
    
    synthetic_data = generate_synthetic_data(n_consumers=50, n_days=7, hourly_records=True)
    preprocessed = preprocess_pipeline(synthetic_data)
    
    features = engineer_all_features(preprocessed)
    print("Engineered features shape:", features.shape)
    print("\nFeature columns:")
    print(features.columns.tolist())
    print("\nSample features:")
    print(features.head())
