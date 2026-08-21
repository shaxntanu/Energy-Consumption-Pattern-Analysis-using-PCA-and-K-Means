"""
Data Loader Module
Loads energy consumption data from CSV files and generates archetype-based synthetic data.
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


def generate_archetype_24h_profile(archetype: str, random_seed: int = None) -> np.ndarray:
    """
    Generate a 24-hour load profile template for a given archetype.
    
    Args:
        archetype: One of 'daytime', 'evening', 'flat', 'weekend'
        random_seed: Random seed for perturbations
        
    Returns:
        24-element array representing hourly load shape (normalized to sum to 1)
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    hours = np.arange(24)
    
    if archetype == 'daytime':
        # Peak during business hours (9-17)
        profile = np.zeros(24)
        profile[9:17] = 1.0
        profile[7:9] = 0.5
        profile[17:19] = 0.5
        profile[0:7] = 0.2
        profile[19:24] = 0.3
        
    elif archetype == 'evening':
        # Peak during evening hours (18-22)
        profile = np.zeros(24)
        profile[18:22] = 1.0
        profile[16:18] = 0.6
        profile[22:24] = 0.4
        profile[0:8] = 0.15
        profile[8:16] = 0.4
        
    elif archetype == 'flat':
        # Industrial-like flat profile with small variation
        profile = np.ones(24) * 0.8
        profile[0:6] = 0.6  # Slight dip at night
        profile[12:14] = 0.9  # Slight bump at lunch
        
    elif archetype == 'weekend':
        # Higher on weekends, moderate weekday
        profile = np.zeros(24)
        profile[10:20] = 0.8  # Weekend-like pattern
        profile[0:10] = 0.4
        profile[20:24] = 0.5
        
    else:
        raise ValueError(f"Unknown archetype: {archetype}")
    
    # Normalize to sum to 1
    profile = profile / profile.sum()
    
    return profile


def perturb_profile(profile: np.ndarray, perturbation_strength: float = 0.15) -> np.ndarray:
    """
    Apply random perturbations to a load profile to create continuous variation.
    
    Args:
        profile: 24-hour load profile
        perturbation_strength: Strength of random perturbation
        
    Returns:
        Perturbed profile (still normalized)
    """
    perturbation = np.random.normal(0, perturbation_strength, 24)
    perturbed = profile + perturbation
    perturbed = np.maximum(perturbed, 0.01)  # Ensure positive
    perturbed = perturbed / perturbed.sum()  # Renormalize
    
    return perturbed


def shift_peak_timing(profile: np.ndarray, max_shift: int = 2) -> np.ndarray:
    """
    Randomly shift peak timing by a few hours.
    
    Args:
        profile: 24-hour load profile
        max_shift: Maximum hours to shift (positive or negative)
        
    Returns:
        Profile with shifted peak
    """
    shift = np.random.randint(-max_shift, max_shift + 1)
    if shift == 0:
        return profile
    
    return np.roll(profile, shift)


def generate_synthetic_data_archetype_based(
    n_consumers: int = 500, 
    n_days: int = 30, 
    hourly_records: bool = True, 
    random_seed: int = 42,
    archetype_distribution: dict = None
) -> pd.DataFrame:
    """
    Generate archetype-based synthetic energy consumption data with genuine behavioral variation.
    
    Archetypes:
    - 'daytime': Business-hours dominant consumers
    - 'evening': Evening-peak consumers (residential)
    - 'flat': Industrial-like flat load
    - 'weekend': Weekend-oriented consumers
    
    Pipeline per consumer:
    latent archetype → 24h load-shape template → individual amplitude
      → peak-timing perturbation → shape perturbation
      → weekday/weekend modifier → individual variability → noise
      → occasional realistic spikes → hourly energy series
    
    Args:
        n_consumers: Number of consumers/buildings
        n_days: Number of days of data
        hourly_records: If True, generate hourly records; otherwise daily
        random_seed: Random seed for reproducibility
        archetype_distribution: Dict mapping archetype to proportion (default: equal)
        
    Returns:
        DataFrame with synthetic energy consumption data and archetype labels (hidden)
    """
    np.random.seed(random_seed)
    
    logger.info(f"Generating archetype-based synthetic data for {n_consumers} consumers over {n_days} days")
    
    # Default archetype distribution (equal)
    if archetype_distribution is None:
        archetype_distribution = {'daytime': 0.25, 'evening': 0.25, 'flat': 0.25, 'weekend': 0.25}
    
    # Validate distribution
    if not np.isclose(sum(archetype_distribution.values()), 1.0):
        raise ValueError("Archetype distribution must sum to 1.0")
    
    records_per_day = 24 if hourly_records else 1
    n_records = n_consumers * n_days * records_per_day
    
    # Assign archetypes to consumers
    archetypes = []
    archetype_counts = {}
    remaining = n_consumers
    
    for arch, prop in archetype_distribution.items():
        count = int(prop * n_consumers)
        if arch == list(archetype_distribution.keys())[-1]:
            count = remaining  # Assign remainder to last archetype
        archetypes.extend([arch] * count)
        archetype_counts[arch] = count
        remaining -= count
    
    np.random.shuffle(archetypes)
    
    # Generate timestamps
    if hourly_records:
        dates = pd.date_range(start='2024-01-01', periods=n_days * records_per_day, freq='h')
        timestamps = np.tile(dates, n_consumers)
    else:
        dates = pd.date_range(start='2024-01-01', periods=n_days, freq='D')
        timestamps = np.tile(dates, n_consumers)
    
    consumer_ids = np.repeat(np.arange(1, n_consumers + 1), n_days * records_per_day)
    
    # Generate energy consumption per consumer
    energy_consumption = []
    archetype_labels = []
    
    for i, consumer_id in enumerate(range(1, n_consumers + 1)):
        archetype = archetypes[i-1]
        archetype_labels.append(archetype)
        
        # Set random seed for this consumer for reproducibility
        consumer_seed = random_seed + consumer_id * 1000
        np.random.seed(consumer_seed)
        
        # Get base profile for archetype
        base_profile = generate_archetype_24h_profile(archetype, consumer_seed)
        
        # Apply perturbations for individual variation
        profile = perturb_profile(base_profile, perturbation_strength=0.15)
        profile = shift_peak_timing(profile, max_shift=2)
        
        # Individual amplitude (scale)
        amplitude = np.random.uniform(0.8, 2.5)
        
        # Generate daily series
        daily_consumption = []
        for day in range(n_days):
            # Day-specific variation
            day_variation = np.random.uniform(0.9, 1.1)
            
            # Check if this day is weekend
            day_timestamp = dates[day * records_per_day] if hourly_records else dates[day]
            is_weekend = day_timestamp.dayofweek >= 5
            
            # Weekend modifier (archetype-specific)
            if archetype == 'weekend':
                weekend_modifier = 1.3 if is_weekend else 0.8
            elif archetype == 'daytime':
                weekend_modifier = 0.7 if is_weekend else 1.0
            else:
                weekend_modifier = 0.9 if is_weekend else 1.0
            
            # Generate hourly values
            if hourly_records:
                for hour in range(24):
                    base_value = profile[hour] * amplitude * day_variation * weekend_modifier
                    
                    # Add individual variability
                    variability = np.random.lognormal(0, 0.15)
                    
                    # Add noise
                    noise = np.random.normal(1.0, 0.1)
                    
                    # Occasional realistic spikes (5% chance)
                    if np.random.random() < 0.05:
                        spike = np.random.uniform(1.5, 2.5)
                        base_value *= spike
                    
                    value = base_value * variability * noise
                    value = max(0.01, value)  # Ensure positive
                    daily_consumption.append(value)
            else:
                # Daily aggregation
                base_value = profile.sum() * amplitude * day_variation * weekend_modifier
                variability = np.random.lognormal(0, 0.1)
                noise = np.random.normal(1.0, 0.05)
                value = base_value * variability * noise
                value = max(0.01, value)
                daily_consumption.append(value)
        
        energy_consumption.extend(daily_consumption)
    
    # Generate temperature from actual timestamp (same for all consumers at same time)
    if hourly_records:
        temperature_by_hour = {}
        for timestamp in dates:
            # Temperature varies by hour of day and day of year
            hour_temp = 20 + 5 * np.sin(2 * np.pi * (timestamp.hour - 14) / 24)
            seasonal_temp = 5 * np.sin(2 * np.pi * (timestamp.dayofyear - 172) / 365)
            temp = hour_temp + seasonal_temp + np.random.normal(0, 1)
            temperature_by_hour[timestamp] = temp
        
        temperature = [temperature_by_hour[t] for t in timestamps]
    else:
        temperature = 20 + 5 * np.sin(2 * np.pi * np.arange(n_records) % n_days / n_days) + np.random.normal(0, 1, n_records)
    
    # Generate electrical features (physically consistent)
    voltage = np.random.normal(230, 5, n_records)
    # Current derived from energy with power factor (physically consistent)
    power_factor = np.random.uniform(0.85, 0.98, n_records)
    # Power (kW) = Energy (kWh) / time (h) for hourly data
    if hourly_records:
        power_kw = np.array(energy_consumption)  # kWh per hour = kW
        current = (power_kw * 1000) / (voltage * power_factor)  # I = P / (V * PF)
    else:
        # For daily, approximate average power
        power_kw = np.array(energy_consumption) / 24
        current = (power_kw * 1000) / (voltage * power_factor)
    
    df = pd.DataFrame({
        'consumer_id': consumer_ids,
        'timestamp': timestamps,
        'energy_consumption_kwh': energy_consumption,
        'voltage_v': voltage,
        'current_a': current,
        'power_factor': power_factor,
        'temperature_c': temperature,
        'archetype': np.repeat(archetype_labels, n_days * records_per_day)  # Hidden ground truth
    })
    
    # Add some missing values to simulate real data (only in voltage, not energy)
    missing_idx = np.random.choice(df.index, size=int(0.01 * n_records), replace=False)
    df.loc[missing_idx, 'voltage_v'] = np.nan
    
    logger.info(f"Generated synthetic data with shape: {df.shape}")
    logger.info(f"Archetype distribution: {archetype_counts}")
    
    return df


def generate_synthetic_data(n_consumers: int = 500, n_days: int = 30, 
                           hourly_records: bool = True, 
                           random_seed: int = 42) -> pd.DataFrame:
    """
    Legacy wrapper for backward compatibility. Uses archetype-based generation.
    
    Args:
        n_consumers: Number of consumers/buildings
        n_days: Number of days of data
        hourly_records: If True, generate hourly records; otherwise daily
        random_seed: Random seed for reproducibility
        
    Returns:
        DataFrame with synthetic energy consumption data
    """
    return generate_synthetic_data_archetype_based(
        n_consumers=n_consumers,
        n_days=n_days,
        hourly_records=hourly_records,
        random_seed=random_seed
    )


if __name__ == "__main__":
    # Test data generation
    synthetic_data = generate_synthetic_data(n_consumers=100, n_days=7, hourly_records=True)
    print(synthetic_data.head())
    print(f"\nData shape: {synthetic_data.shape}")
    print(f"\nData types:\n{synthetic_data.dtypes}")
    print(f"\nMissing values:\n{synthetic_data.isnull().sum()}")
