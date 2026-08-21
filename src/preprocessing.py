"""
Preprocessing Module
Handles data cleaning, validation, and preprocessing.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_schema(df: pd.DataFrame, required_columns: list) -> bool:
    """
    Validate that the DataFrame contains required columns.
    
    Args:
        df: Input DataFrame
        required_columns: List of required column names
        
    Returns:
        True if schema is valid, raises ValueError otherwise
    """
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    logger.info("Schema validation passed")
    return True


def handle_missing_values(df: pd.DataFrame, strategy: str = 'forward_fill', 
                          group_by: str = 'consumer_id') -> pd.DataFrame:
    """
    Handle missing values with within-group awareness to prevent cross-consumer leakage.
    
    Args:
        df: DataFrame with potential missing values
        strategy: Strategy for handling missing values ('forward_fill', 'backward_fill', 'mean', 'drop')
        group_by: Column to group by for within-group operations (default: consumer_id)
        
    Returns:
        DataFrame with missing values handled
    """
    logger.info(f"Handling missing values with strategy: {strategy} (grouped by {group_by})")
    logger.info(f"Missing values before: {df.isnull().sum().sum()}")
    
    df_clean = df.copy()
    
    if group_by not in df_clean.columns:
        logger.warning(f"Group column '{group_by}' not found, falling back to global operation")
        group_by = None
    
    if strategy == 'forward_fill':
        if group_by:
            # Within-consumer forward fill, then backward fill for remaining
            # Use transform to preserve group column
            for col in df_clean.columns:
                if col != group_by and df_clean[col].isnull().any():
                    df_clean[col] = df_clean.groupby(group_by)[col].transform(
                        lambda x: x.ffill().bfill()
                    )
        else:
            df_clean = df_clean.ffill().bfill()
    elif strategy == 'backward_fill':
        if group_by:
            for col in df_clean.columns:
                if col != group_by and df_clean[col].isnull().any():
                    df_clean[col] = df_clean.groupby(group_by)[col].transform(
                        lambda x: x.bfill().ffill()
                    )
        else:
            df_clean = df_clean.bfill().ffill()
    elif strategy == 'mean':
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        if group_by:
            # Fill with group-specific mean
            for col in numeric_cols:
                if col != group_by:
                    df_clean[col] = df_clean.groupby(group_by)[col].transform(
                        lambda x: x.fillna(x.mean())
                    )
            # Fill remaining with global mean
            df_clean[numeric_cols] = df_clean[numeric_cols].fillna(
                df_clean[numeric_cols].mean()
            )
        else:
            df_clean[numeric_cols] = df_clean[numeric_cols].fillna(
                df_clean[numeric_cols].mean()
            )
    elif strategy == 'drop':
        df_clean = df_clean.dropna()
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    logger.info(f"Missing values after: {df_clean.isnull().sum().sum()}")
    return df_clean


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate records from the DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with duplicates removed
    """
    n_before = len(df)
    df_clean = df.drop_duplicates()
    n_removed = n_before - len(df_clean)
    
    logger.info(f"Removed {n_removed} duplicate records")
    return df_clean


def detect_invalid_values(df: pd.DataFrame, column_ranges: dict = None) -> pd.DataFrame:
    """
    Detect and handle invalid values based on column ranges.
    
    Args:
        df: DataFrame to validate
        column_ranges: Dict mapping column names to (min, max) valid ranges.
                      If None, uses conservative physical limits.
        
    Returns:
        DataFrame with invalid values marked as NaN
    """
    if column_ranges is None:
        # Conservative physical limits - only mark truly impossible values
        column_ranges = {
            'energy_consumption_kwh': (0, 1000),  # Very high upper limit to avoid removing legitimate peaks
            'voltage_v': (0, 500),  # Allow wider range
            'current_a': (0, 500),  # Allow wider range
            'power_factor': (0, 1.1),  # Slightly above 1 for measurement error
            'temperature_c': (-50, 60)  # Wider physical range
        }
    
    df_clean = df.copy()
    invalid_count = 0
    
    for col, (min_val, max_val) in column_ranges.items():
        if col in df_clean.columns:
            invalid_mask = (df_clean[col] < min_val) | (df_clean[col] > max_val)
            invalid_count += invalid_mask.sum()
            df_clean.loc[invalid_mask, col] = np.nan
    
    logger.info(f"Detected and marked {invalid_count} invalid values")
    return df_clean


def parse_timestamps(df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
    """
    Parse timestamp column to datetime objects.
    
    Args:
        df: Input DataFrame
        timestamp_col: Name of the timestamp column
        
    Returns:
        DataFrame with parsed timestamps
    """
    logger.info(f"Parsing timestamps from column: {timestamp_col}")
    
    df_clean = df.copy()
    
    if timestamp_col in df_clean.columns:
        df_clean[timestamp_col] = pd.to_datetime(df_clean[timestamp_col], errors='coerce')
        
        # Extract temporal features
        df_clean['hour'] = df_clean[timestamp_col].dt.hour
        df_clean['day_of_week'] = df_clean[timestamp_col].dt.dayofweek
        df_clean['is_weekend'] = df_clean['day_of_week'] >= 5
        df_clean['month'] = df_clean[timestamp_col].dt.month
        
        logger.info("Timestamps parsed and temporal features extracted")
    else:
        logger.warning(f"Timestamp column '{timestamp_col}' not found")
    
    return df_clean


def remove_outliers(df: pd.DataFrame, column: str, method: str = 'iqr', 
                    threshold: float = 5.0, remove: bool = False) -> pd.DataFrame:
    """
    Detect outliers using IQR or Z-score method.
    By default, only logs outliers without removing them to preserve behavioral extremes.
    
    Args:
        df: Input DataFrame
        column: Column name to check for outliers
        method: Method for outlier detection ('iqr' or 'zscore')
        threshold: Threshold for outlier detection (default 5.0 for IQR to be conservative)
        remove: If True, remove outliers; if False, only log them
        
    Returns:
        DataFrame with outliers optionally removed
    """
    df_clean = df.copy()
    
    if column not in df_clean.columns:
        logger.warning(f"Column '{column}' not found")
        return df_clean
    
    if method == 'iqr':
        Q1 = df_clean[column].quantile(0.25)
        Q3 = df_clean[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        outlier_mask = (df_clean[column] < lower_bound) | (df_clean[column] > upper_bound)
    elif method == 'zscore':
        z_scores = np.abs((df_clean[column] - df_clean[column].mean()) / df_clean[column].std())
        outlier_mask = z_scores > threshold
    else:
        raise ValueError(f"Unknown method: {method}")
    
    n_outliers = outlier_mask.sum()
    
    if remove:
        df_clean = df_clean[~outlier_mask]
        logger.info(f"Removed {n_outliers} outliers from column '{column}'")
    else:
        logger.info(f"Detected {n_outliers} outliers in column '{column}' (not removed)")
        logger.info(f"Outlier bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
    
    return df_clean


def preprocess_pipeline(df: pd.DataFrame, required_columns: list = None, 
                        remove_outliers_flag: bool = False) -> pd.DataFrame:
    """
    Complete preprocessing pipeline with panel/time-series awareness.
    
    Args:
        df: Input DataFrame
        required_columns: List of required columns for validation
        remove_outliers_flag: If True, remove outliers; if False, only detect and log
        
    Returns:
        Preprocessed DataFrame
    """
    logger.info("Starting preprocessing pipeline")
    logger.info(f"Initial shape: {df.shape}")
    logger.info(f"Initial columns: {df.columns.tolist()}")
    
    if required_columns:
        validate_schema(df, required_columns)
    
    # Remove duplicates
    df = remove_duplicates(df)
    logger.info(f"After remove_duplicates: {df.columns.tolist()}")
    
    # Parse timestamps
    df = parse_timestamps(df)
    logger.info(f"After parse_timestamps: {df.columns.tolist()}")
    
    # Sort panel data before any temporal operations (prevents cross-consumer leakage)
    sort_cols = [c for c in ['consumer_id', 'timestamp'] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)
        logger.info(f"Sorted by {sort_cols}")
    
    # Detect invalid values (only truly impossible values)
    df = detect_invalid_values(df)
    logger.info(f"After detect_invalid_values: {df.columns.tolist()}")
    
    # Handle missing values with within-consumer awareness
    df = handle_missing_values(df, strategy='forward_fill', group_by='consumer_id')
    logger.info(f"After handle_missing_values: {df.columns.tolist()}")
    
    # Detect outliers (by default, only log without removing to preserve behavioral extremes)
    df = remove_outliers(df, 'energy_consumption_kwh', method='iqr', threshold=5.0, remove=remove_outliers_flag)
    logger.info(f"After remove_outliers: {df.columns.tolist()}")
    
    logger.info(f"Final shape after preprocessing: {df.shape}")
    return df


if __name__ == "__main__":
    # Test preprocessing
    from data_loader import generate_synthetic_data
    
    synthetic_data = generate_synthetic_data(n_consumers=50, n_days=5, hourly_records=True)
    print("Original data shape:", synthetic_data.shape)
    
    preprocessed = preprocess_pipeline(synthetic_data)
    print("Preprocessed data shape:", preprocessed.shape)
    print("\nPreprocessed data sample:")
    print(preprocessed.head())
