"""
Data Loader Module

Loads energy consumption data from CSV files and generates archetype-based
synthetic data.

THIS MODULE PRODUCES SYNTHETIC DATA. The archetypes below are designed by hand.
They are a controlled test bed for the clustering pipeline, not a measurement of
real household or building behaviour.

Generative model (one consumer at a time):

    latent archetype
      -> per-consumer shape parameters drawn from that archetype's distributions
         (baseline level, morning/midday/evening bump amplitude, peak hour,
          peak width, weekend energy ratio, weekend timing shift,
          hour-to-hour variability, spike rate)
      -> blend a random fraction of the population-average shape back in,
         so some consumers sit between archetypes
      -> separate weekday and weekend 24-hour shapes
      -> individual amplitude (kWh scale), drawn independently of archetype
      -> day-to-day factor, hourly multiplicative noise, occasional spikes
      -> hourly energy series

Two design choices matter for the experiment:

1. Amplitude (how much a consumer uses) is drawn from the same distribution for
   every archetype. Magnitude therefore carries no archetype information, and
   the ablation study can show that magnitude features cannot recover the
   groups even when they score well on silhouette.
2. Consumers are blended towards the population-average shape by a random
   amount. Archetypes overlap, so the clustering problem is not trivial.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARCHETYPE_NAMES: Tuple[str, ...] = ('daytime', 'evening', 'flat', 'weekend')

# Fraction of the population-average shape mixed into each consumer's own shape
# is drawn from Beta(BLEND_A, BLEND_B). Mean is about 0.22, so most consumers
# keep their archetype but a tail of them are genuinely ambiguous.
BLEND_A = 1.4
BLEND_B = 5.0

# Amplitude is the consumer's mean hourly energy in kWh. Same for all
# archetypes on purpose: scale must not leak archetype identity.
AMPLITUDE_LOG_MEAN = np.log(1.2)
AMPLITUDE_LOG_SIGMA = 0.45

DAY_FACTOR_SIGMA = 0.08
SPIKE_MULTIPLIER_RANGE = (1.8, 4.0)
MIN_ENERGY_KWH = 0.01


@dataclass(frozen=True)
class BumpSpec:
    """A Gaussian bump on the 24-hour clock, described by mean and spread.

    Each field is a (mean, sd) pair. The mean is the archetype's typical value
    and the sd is how much individual consumers of that archetype differ.
    """

    amplitude: Tuple[float, float]
    center_hour: Tuple[float, float]
    width_hours: Tuple[float, float]


@dataclass(frozen=True)
class ArchetypeSpec:
    """Distributions that define one behavioural archetype."""

    name: str
    baseline: Tuple[float, float]
    bumps: Tuple[BumpSpec, ...]
    weekend_energy_ratio: Tuple[float, float]
    weekend_shift_hours: Tuple[float, float]
    noise_sigma: Tuple[float, float]
    spike_rate: Tuple[float, float]
    description: str


ARCHETYPE_SPECS: Dict[str, ArchetypeSpec] = {
    'daytime': ArchetypeSpec(
        name='daytime',
        baseline=(0.30, 0.07),
        bumps=(
            BumpSpec(amplitude=(0.35, 0.12), center_hour=(7.5, 0.9), width_hours=(1.6, 0.35)),
            BumpSpec(amplitude=(1.00, 0.22), center_hour=(13.0, 1.1), width_hours=(3.4, 0.60)),
            BumpSpec(amplitude=(0.30, 0.12), center_hour=(19.0, 1.0), width_hours=(1.8, 0.40)),
        ),
        weekend_energy_ratio=(0.78, 0.10),
        weekend_shift_hours=(0.5, 0.5),
        noise_sigma=(0.22, 0.05),
        spike_rate=(0.020, 0.010),
        description='Business-hours dominant. Broad midday peak, quiet weekends.',
    ),
    'evening': ArchetypeSpec(
        name='evening',
        baseline=(0.22, 0.06),
        bumps=(
            BumpSpec(amplitude=(0.55, 0.16), center_hour=(7.0, 0.9), width_hours=(1.4, 0.30)),
            BumpSpec(amplitude=(0.20, 0.10), center_hour=(13.0, 1.4), width_hours=(3.0, 0.60)),
            BumpSpec(amplitude=(1.10, 0.24), center_hour=(19.5, 1.0), width_hours=(2.0, 0.40)),
        ),
        weekend_energy_ratio=(1.02, 0.10),
        weekend_shift_hours=(1.0, 0.6),
        noise_sigma=(0.26, 0.06),
        spike_rate=(0.030, 0.015),
        description='Residential shape. Morning and evening peaks, low midday.',
    ),
    'flat': ArchetypeSpec(
        name='flat',
        baseline=(0.85, 0.12),
        bumps=(
            BumpSpec(amplitude=(0.15, 0.07), center_hour=(8.0, 1.5), width_hours=(2.0, 0.50)),
            BumpSpec(amplitude=(0.20, 0.09), center_hour=(13.0, 1.6), width_hours=(4.0, 0.80)),
            BumpSpec(amplitude=(0.15, 0.07), center_hour=(19.0, 1.5), width_hours=(2.0, 0.50)),
        ),
        weekend_energy_ratio=(0.95, 0.07),
        weekend_shift_hours=(0.0, 0.4),
        noise_sigma=(0.12, 0.04),
        spike_rate=(0.005, 0.004),
        description='Continuous-process shape. High night baseline, shallow peaks.',
    ),
    'weekend': ArchetypeSpec(
        name='weekend',
        baseline=(0.35, 0.08),
        bumps=(
            BumpSpec(amplitude=(0.25, 0.10), center_hour=(9.0, 1.2), width_hours=(2.0, 0.50)),
            BumpSpec(amplitude=(0.55, 0.18), center_hour=(14.0, 1.3), width_hours=(4.5, 0.80)),
            BumpSpec(amplitude=(0.55, 0.18), center_hour=(19.5, 1.2), width_hours=(2.5, 0.50)),
        ),
        weekend_energy_ratio=(1.45, 0.13),
        weekend_shift_hours=(1.5, 0.7),
        noise_sigma=(0.24, 0.06),
        spike_rate=(0.025, 0.012),
        description='Leisure shape. Clearly heavier weekends, late and broad daytime use.',
    ),
}


def load_data(file_path: str) -> pd.DataFrame:
    """Load energy consumption data from a CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        DataFrame containing the loaded data.
    """
    logger.info(f"Loading data from {file_path}")

    if not Path(file_path).exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(file_path)

    df = pd.read_csv(file_path)
    logger.info(f"Data loaded successfully. Shape: {df.shape}")
    logger.info(f"Columns: {df.columns.tolist()}")
    return df


def _circular_hour_distance(hours: np.ndarray, center: float) -> np.ndarray:
    """Distance in hours on a 24-hour clock, so 23:00 is one hour from 00:00."""
    raw = np.abs(hours - center)
    return np.minimum(raw, 24.0 - raw)


def build_load_shape(baseline: float,
                     bumps: Sequence[Tuple[float, float, float]]) -> np.ndarray:
    """Build a normalized 24-hour load shape from a baseline plus Gaussian bumps.

    Args:
        baseline: Flat level present at every hour before bumps are added.
        bumps: Sequence of (amplitude, center_hour, width_hours) triples.

    Returns:
        24-element array that sums to 1.
    """
    hours = np.arange(24, dtype=float)
    shape = np.full(24, float(baseline))
    for amplitude, center, width in bumps:
        width = max(float(width), 0.4)
        shape += float(amplitude) * np.exp(
            -0.5 * (_circular_hour_distance(hours, float(center)) / width) ** 2
        )
    shape = np.maximum(shape, 1e-6)
    return shape / shape.sum()


def archetype_template_shape(archetype: str) -> np.ndarray:
    """Return the mean 24-hour shape of an archetype (no individual variation).

    This is the reference template used for documentation and validation. Real
    consumers are drawn around it, never equal to it.

    Args:
        archetype: One of ARCHETYPE_NAMES.

    Returns:
        24-element array that sums to 1.
    """
    if archetype not in ARCHETYPE_SPECS:
        raise ValueError(f"Unknown archetype: {archetype}. Known: {list(ARCHETYPE_SPECS)}")
    spec = ARCHETYPE_SPECS[archetype]
    bumps = [(b.amplitude[0], b.center_hour[0], b.width_hours[0]) for b in spec.bumps]
    return build_load_shape(spec.baseline[0], bumps)


def population_mean_shape() -> np.ndarray:
    """Average of the four archetype templates, normalized to sum to 1."""
    stacked = np.vstack([archetype_template_shape(name) for name in ARCHETYPE_NAMES])
    mean_shape = stacked.mean(axis=0)
    return mean_shape / mean_shape.sum()


def draw_consumer_parameters(spec: ArchetypeSpec, rng: np.random.Generator) -> dict:
    """Draw one consumer's behavioural parameters from an archetype's distributions.

    Args:
        spec: Archetype specification.
        rng: Consumer-specific random generator.

    Returns:
        Dictionary of scalar parameters describing this consumer.
    """
    baseline = max(rng.normal(*spec.baseline), 0.03)

    bumps = []
    for bump in spec.bumps:
        amplitude = max(rng.normal(*bump.amplitude), 0.0)
        center = rng.normal(*bump.center_hour) % 24.0
        width = max(rng.normal(*bump.width_hours), 0.5)
        bumps.append((amplitude, center, width))

    return {
        'archetype': spec.name,
        'baseline': baseline,
        'bumps': bumps,
        'blend': float(rng.beta(BLEND_A, BLEND_B)),
        'weekend_energy_ratio': max(rng.normal(*spec.weekend_energy_ratio), 0.35),
        'weekend_shift_hours': rng.normal(*spec.weekend_shift_hours),
        'noise_sigma': float(np.clip(rng.normal(*spec.noise_sigma), 0.04, 0.60)),
        'spike_rate': float(np.clip(rng.normal(*spec.spike_rate), 0.0, 0.12)),
        'amplitude_kwh': float(rng.lognormal(AMPLITUDE_LOG_MEAN, AMPLITUDE_LOG_SIGMA)),
        'power_factor': float(rng.uniform(0.85, 0.98)),
    }


def consumer_load_shapes(params: dict, pop_shape: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Build a consumer's weekday and weekend 24-hour shapes.

    The weekend shape reuses the same bumps with their centres shifted later and
    a slightly higher baseline, which is what "weekend behaviour" means here:
    the same household or site, waking up later and spreading its use out.

    Args:
        params: Output of draw_consumer_parameters.
        pop_shape: Population-average shape used for archetype blending.

    Returns:
        Tuple of (weekday_shape, weekend_shape), each summing to 1.
    """
    weekday = build_load_shape(params['baseline'], params['bumps'])

    shift = params['weekend_shift_hours']
    weekend_bumps = [(amp, center + shift, width) for amp, center, width in params['bumps']]
    weekend = build_load_shape(params['baseline'] * 1.15, weekend_bumps)

    blend = params['blend']
    weekday = (1.0 - blend) * weekday + blend * pop_shape
    weekend = (1.0 - blend) * weekend + blend * pop_shape

    return weekday / weekday.sum(), weekend / weekend.sum()


def _simulate_consumer_series(params: dict,
                              pop_shape: np.ndarray,
                              is_weekend_by_day: np.ndarray,
                              rng: np.random.Generator) -> np.ndarray:
    """Simulate one consumer's hourly energy series.

    Every multiplicative effect is mean-corrected so that the consumer's mean
    hourly energy stays equal to amplitude_kwh. Without this correction a high
    weekend ratio or high variability would also raise total consumption, and
    magnitude features would partly encode archetype identity.

    Args:
        params: Output of draw_consumer_parameters.
        pop_shape: Population-average shape used for archetype blending.
        is_weekend_by_day: Boolean array, one entry per simulated day.
        rng: Consumer-specific random generator.

    Returns:
        Array of length 24 * n_days with hourly kWh values.
    """
    weekday_shape, weekend_shape = consumer_load_shapes(params, pop_shape)
    amplitude = params['amplitude_kwh']

    n_days = len(is_weekend_by_day)
    n_weekend = int(is_weekend_by_day.sum())
    n_weekday = n_days - n_weekend
    ratio = params['weekend_energy_ratio']

    # Split the weekend ratio around 1 so it changes when energy is used, not
    # how much is used in total.
    weekend_mean = (n_weekday + n_weekend * ratio) / n_days
    weekday_factor = 1.0 / weekend_mean
    weekend_factor = ratio / weekend_mean

    sigma = params['noise_sigma']
    noise_correction = np.exp(-0.5 * sigma ** 2)
    day_correction = np.exp(-0.5 * DAY_FACTOR_SIGMA ** 2)
    mean_spike = 0.5 * (SPIKE_MULTIPLIER_RANGE[0] + SPIKE_MULTIPLIER_RANGE[1])
    spike_correction = 1.0 / (1.0 + params['spike_rate'] * (mean_spike - 1.0))
    correction = noise_correction * day_correction * spike_correction

    series = np.empty(24 * n_days, dtype=float)

    for day_index, is_weekend in enumerate(is_weekend_by_day):
        shape = weekend_shape if is_weekend else weekday_shape
        energy_factor = weekend_factor if is_weekend else weekday_factor
        day_factor = rng.lognormal(0.0, DAY_FACTOR_SIGMA)

        # shape sums to 1 over 24 hours, so multiplying by 24 * amplitude makes
        # amplitude the consumer's mean hourly kWh.
        hourly = shape * 24.0 * amplitude * day_factor * energy_factor * correction
        hourly = hourly * rng.lognormal(0.0, sigma, 24)

        spike_mask = rng.random(24) < params['spike_rate']
        if spike_mask.any():
            hourly[spike_mask] *= rng.uniform(*SPIKE_MULTIPLIER_RANGE, spike_mask.sum())

        start = day_index * 24
        series[start:start + 24] = np.maximum(hourly, MIN_ENERGY_KWH)

    return series


def assign_archetypes(n_consumers: int,
                      archetype_distribution: Dict[str, float],
                      rng: np.random.Generator) -> np.ndarray:
    """Assign an archetype to every consumer, then shuffle so IDs carry no signal.

    Args:
        n_consumers: Number of consumers.
        archetype_distribution: Mapping of archetype name to proportion.
        rng: Random generator.

    Returns:
        Array of archetype names, one per consumer, in consumer_id order.
    """
    if not np.isclose(sum(archetype_distribution.values()), 1.0):
        raise ValueError("Archetype distribution must sum to 1.0")

    names = list(archetype_distribution)
    counts = {name: int(archetype_distribution[name] * n_consumers) for name in names}
    counts[names[-1]] += n_consumers - sum(counts.values())

    labels = np.array([name for name in names for _ in range(counts[name])])
    rng.shuffle(labels)
    return labels


def generate_synthetic_data_archetype_based(
    n_consumers: int = 200,
    n_days: int = 30,
    hourly_records: bool = True,
    random_seed: int = 42,
    archetype_distribution: Optional[Dict[str, float]] = None,
    missing_voltage_fraction: float = 0.01,
    missing_energy_fraction: float = 0.005,
) -> pd.DataFrame:
    """Generate synthetic energy consumption data with recoverable archetypes.

    THIS IS SYNTHETIC DATA. The archetype column is hidden ground truth. It is
    used only to validate the pipeline and is dropped before preprocessing.

    Args:
        n_consumers: Number of consumers.
        n_days: Number of days, starting 2024-01-01.
        hourly_records: If True, emit one record per hour; otherwise per day.
        random_seed: Seed controlling every random draw.
        archetype_distribution: Archetype proportions. Defaults to equal shares.
        missing_voltage_fraction: Share of records with voltage set to NaN.
        missing_energy_fraction: Share of records with energy set to NaN.

    Returns:
        DataFrame with consumer_id, timestamp, energy_consumption_kwh, voltage_v,
        current_a, power_factor, temperature_c and archetype.
    """
    if n_consumers < 1 or n_days < 1:
        raise ValueError("n_consumers and n_days must both be at least 1")

    if archetype_distribution is None:
        archetype_distribution = {name: 0.25 for name in ARCHETYPE_NAMES}

    logger.info(
        f"Generating archetype-based synthetic data: {n_consumers} consumers, {n_days} days, "
        f"{'hourly' if hourly_records else 'daily'} records, seed {random_seed}"
    )

    # One independent stream per consumer plus two shared streams. Consumer
    # streams do not depend on loop order, so results are reproducible.
    root = np.random.SeedSequence(random_seed)
    assign_seed, shared_seed, *consumer_seeds = root.spawn(n_consumers + 2)
    assign_rng = np.random.default_rng(assign_seed)
    shared_rng = np.random.default_rng(shared_seed)

    archetype_labels = assign_archetypes(n_consumers, archetype_distribution, assign_rng)

    hourly_index = pd.date_range(start='2024-01-01', periods=n_days * 24, freq='h')
    day_index = pd.date_range(start='2024-01-01', periods=n_days, freq='D')
    is_weekend_by_day = np.asarray(day_index.dayofweek) >= 5

    pop_shape = population_mean_shape()

    hourly_series = []
    consumer_params = []
    for consumer_index in range(n_consumers):
        rng = np.random.default_rng(consumer_seeds[consumer_index])
        spec = ARCHETYPE_SPECS[archetype_labels[consumer_index]]
        params = draw_consumer_parameters(spec, rng)
        consumer_params.append(params)
        hourly_series.append(_simulate_consumer_series(params, pop_shape, is_weekend_by_day, rng))

    if hourly_records:
        energy = np.concatenate(hourly_series)
        timestamps = np.tile(hourly_index.to_numpy(), n_consumers)
        records_per_consumer = n_days * 24
    else:
        energy = np.concatenate([s.reshape(n_days, 24).sum(axis=1) for s in hourly_series])
        timestamps = np.tile(day_index.to_numpy(), n_consumers)
        records_per_consumer = n_days

    consumer_ids = np.repeat(np.arange(1, n_consumers + 1), records_per_consumer)
    n_records = len(energy)

    # Temperature depends only on the timestamp, so every consumer sees the same
    # weather. It is context, not a per-consumer behavioural feature.
    stamp_index = hourly_index if hourly_records else day_index
    diurnal = 20.0 + 5.0 * np.sin(2 * np.pi * (np.asarray(stamp_index.hour) - 14) / 24)
    seasonal = 5.0 * np.sin(2 * np.pi * (np.asarray(stamp_index.dayofyear) - 172) / 365)
    weather = diurnal + seasonal + shared_rng.normal(0.0, 1.0, len(stamp_index))
    temperature = np.tile(weather, n_consumers)

    voltage = shared_rng.normal(230.0, 5.0, n_records)

    # Power factor is a property of the site's equipment, so it is drawn once per
    # consumer with small measurement jitter rather than fresh for every row.
    pf_by_consumer = np.array([p['power_factor'] for p in consumer_params])
    power_factor = np.repeat(pf_by_consumer, records_per_consumer)
    power_factor = np.clip(power_factor + shared_rng.normal(0.0, 0.005, n_records), 0.80, 0.99)

    hours_per_record = 1.0 if hourly_records else 24.0
    power_kw = energy / hours_per_record
    current = (power_kw * 1000.0) / (voltage * power_factor)

    df = pd.DataFrame({
        'consumer_id': consumer_ids,
        'timestamp': timestamps,
        'energy_consumption_kwh': energy,
        'voltage_v': voltage,
        'current_a': current,
        'power_factor': power_factor,
        'temperature_c': temperature,
        'archetype': np.repeat(archetype_labels, records_per_consumer),
    })

    # Gaps of the kind a real meter feed has. Imputation is done per consumer in
    # preprocessing, so these never mix one consumer's data into another's.
    for column, fraction in (('voltage_v', missing_voltage_fraction),
                             ('energy_consumption_kwh', missing_energy_fraction)):
        n_missing = int(fraction * n_records)
        if n_missing > 0:
            idx = shared_rng.choice(n_records, size=n_missing, replace=False)
            df.loc[idx, column] = np.nan

    counts = df.groupby('archetype')['consumer_id'].nunique().to_dict()
    logger.info(f"Generated synthetic data with shape: {df.shape}")
    logger.info(f"Consumers per archetype: {counts}")

    return df


def generate_synthetic_data(n_consumers: int = 200,
                            n_days: int = 30,
                            hourly_records: bool = True,
                            random_seed: int = 42) -> pd.DataFrame:
    """Generate synthetic data with default archetype proportions.

    Args:
        n_consumers: Number of consumers.
        n_days: Number of days.
        hourly_records: If True, emit one record per hour; otherwise per day.
        random_seed: Seed controlling every random draw.

    Returns:
        DataFrame of synthetic energy consumption records.
    """
    return generate_synthetic_data_archetype_based(
        n_consumers=n_consumers,
        n_days=n_days,
        hourly_records=hourly_records,
        random_seed=random_seed,
    )


if __name__ == "__main__":
    data = generate_synthetic_data(n_consumers=100, n_days=7, hourly_records=True)
    print(data.head())
    print(f"\nShape: {data.shape}")
    print(f"\nMissing values:\n{data.isnull().sum()}")
    print("\nArchetype template shapes (percent of daily energy per hour):")
    for name in ARCHETYPE_NAMES:
        shape = archetype_template_shape(name) * 100
        print(f"  {name:8s} peak hour {int(np.argmax(shape)):2d}  " +
              " ".join(f"{v:4.1f}" for v in shape))
