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


def handle_missing_values(df: pd.DataFrame, strategy: str = 'forward_fill') -> pd.DataFrame:
    """
    Handle missing values in the DataFrame.
    
    Args:
        df: Input DataFrame
        strategy: Strategy for handling missing values ('forward_fill', 'backward_fill', 'mean', 'drop')
        
    Returns:
        DataFrame with missing values handled
    """
    logger.info(f"Handling missing values with strategy: {strategy}")
    logger.info(f"Missing values before: {df.isnull().sum().sum()}")
    
    df_clean = df.copy()
    
    if strategy == 'forward_fill':
        df_clean = df_clean.ffill().bfill()
    elif strategy == 'backward_fill':
        df_clean = df_clean.bfill().ffill()
    elif strategy == 'mean':
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        df_clean[numeric_cols] = df_clean[numeric_cols].fillna(df_clean[numeric_cols].mean())
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
        df: Input DataFrame
        column_ranges: Dictionary mapping column names to (min, max) tuples
        
    Returns:
        DataFrame with invalid values set to NaN
    """
    if column_ranges is None:
        column_ranges = {
            'energy_consumption_kwh': (0, 100),
            'voltage_v': (200, 250),
            'current_a': (0, 100),
            'power_factor': (0, 1),
            'temperature_c': (-20, 50)
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
                    threshold: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers from a specific column.
    
    Args:
        df: Input DataFrame
        column: Column name to check for outliers
        method: Method for outlier detection ('iqr' or 'zscore')
        threshold: Threshold for outlier detection
        
    Returns:
        DataFrame with outliers removed
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
    df_clean = df_clean[~outlier_mask]
    
    logger.info(f"Removed {n_outliers} outliers from column '{column}'")
    return df_clean


def preprocess_pipeline(df: pd.DataFrame, required_columns: list = None) -> pd.DataFrame:
    """
    Complete preprocessing pipeline.
    
    Args:
        df: Input DataFrame
        required_columns: List of required columns for validation
        
    Returns:
        Preprocessed DataFrame
    """
    logger.info("Starting preprocessing pipeline")
    logger.info(f"Initial shape: {df.shape}")
    
    if required_columns:
        validate_schema(df, required_columns)
    
    # Remove duplicates
    df = remove_duplicates(df)
    
    # Parse timestamps
    df = parse_timestamps(df)
    
    # Detect invalid values
    df = detect_invalid_values(df)
    
    # Handle missing values
    df = handle_missing_values(df, strategy='forward_fill')
    
    # Remove extreme outliers from energy consumption
    df = remove_outliers(df, 'energy_consumption_kwh', method='iqr', threshold=3.0)
    
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
