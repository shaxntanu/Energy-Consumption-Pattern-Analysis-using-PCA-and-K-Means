"""
Data Loader Module
Loads energy consumption data from CSV files.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data(file_path: str) -> pd.DataFrame:
    """
    Load energy consumption data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame containing the loaded data
    """
    logger.info(f"Loading data from {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Data loaded successfully. Shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise


def generate_synthetic_data(n_consumers: int = 500, n_days: int = 30, 
                           hourly_records: bool = True, 
                           random_seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic energy consumption data for testing.
    
    Args:
        n_consumers: Number of consumers/buildings
        n_days: Number of days of data
        hourly_records: If True, generate hourly records; otherwise daily
        random_seed: Random seed for reproducibility
        
    Returns:
        DataFrame with synthetic energy consumption data
    """
    np.random.seed(random_seed)
    
    logger.info(f"Generating synthetic data for {n_consumers} consumers over {n_days} days")
    
    records_per_day = 24 if hourly_records else 1
    n_records = n_consumers * n_days * records_per_day
    
    consumer_ids = np.repeat(np.arange(1, n_consumers + 1), n_days * records_per_day)
    
    # Generate timestamps
    if hourly_records:
        dates = pd.date_range(start='2024-01-01', periods=n_days * records_per_day, freq='h')
        timestamps = np.tile(dates, n_consumers)
    else:
        dates = pd.date_range(start='2024-01-01', periods=n_days, freq='D')
        timestamps = np.tile(dates, n_consumers)
    
    # Generate energy consumption with realistic patterns
    base_consumption = np.random.uniform(0.5, 3.0, n_consumers)
    base_consumption = np.repeat(base_consumption, n_days * records_per_day)
    
    # Add time-of-day patterns
    if hourly_records:
        hour = pd.Series(timestamps).dt.hour.values
        time_factor = 0.7 + 0.6 * np.sin(2 * np.pi * (hour - 6) / 24)
        time_factor = np.where((hour >= 7) & (hour <= 21), time_factor, 0.4)
    else:
        time_factor = 1.0
    
    # Add weekday/weekend patterns
    day_of_week = pd.Series(timestamps).dt.dayofweek.values
    is_weekend = day_of_week >= 5
    weekend_factor = np.where(is_weekend, 0.8, 1.0)
    
    # Add random variation
    noise = np.random.lognormal(0, 0.2, n_records)
    
    energy_consumption = base_consumption * time_factor * weekend_factor * noise
    
    # Generate other features
    voltage = np.random.normal(230, 5, n_records)
    current = energy_consumption / voltage * 1000  # Approximate
    power_factor = np.random.uniform(0.85, 0.98, n_records)
    temperature = 20 + 10 * np.sin(2 * np.pi * np.arange(n_records) % (24 * n_days) / (24 * n_days)) + np.random.normal(0, 2, n_records)
    
    df = pd.DataFrame({
        'consumer_id': consumer_ids,
        'timestamp': timestamps,
        'energy_consumption_kwh': energy_consumption,
        'voltage_v': voltage,
        'current_a': current,
        'power_factor': power_factor,
        'temperature_c': temperature
    })
    
    # Add some missing values to simulate real data
    missing_idx = np.random.choice(df.index, size=int(0.02 * n_records), replace=False)
    df.loc[missing_idx, 'voltage_v'] = np.nan
    
    logger.info(f"Generated synthetic data with shape: {df.shape}")
    return df


if __name__ == "__main__":
    # Test data generation
    synthetic_data = generate_synthetic_data(n_consumers=100, n_days=7, hourly_records=True)
    print(synthetic_data.head())
    print(f"\nData shape: {synthetic_data.shape}")
    print(f"\nData types:\n{synthetic_data.dtypes}")
    print(f"\nMissing values:\n{synthetic_data.isnull().sum()}")
