"""Regenerate the two seasonal chart arrays the web app needs.

The pipeline's seasonal_analysis.py now exports `mean_shape_by_season`
(per-season 24h normalized load shapes) and `phase_recovery_points`
(per-consumer hidden-phase / estimated-peak pairs), but the on-disk flagship
artifacts predate those keys. The arrays depend only on the deterministic
generation + preprocessing path (seed 42, 200 consumers x 365 days), not on
clustering, so this script recomputes them directly with the pipeline's own
helpers and patches them into:

    outputs/metrics/seasonal_analysis_metrics.json
    web/public/data/seasonal.json

Honesty gate: before writing anything it recomputes mean daily kWh by season
and the amplitude from the same data path and refuses to write unless they
match the stored flagship values. A match proves the regenerated arrays are
exactly what a full pipeline re-run would have exported.

Run from the project root:  py src/patch_seasonal_contract.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from data_loader import SeasonalConfig, generate_synthetic_data  # noqa: E402
from preprocessing import preprocess_pipeline  # noqa: E402
from seasonal_analysis import (  # noqa: E402
    SEASON_ORDER,
    _daily_energy_by_season,
    _mean_shape_by_season,
    _recover_phase_from_seasons,
    _seasonal_amplitude_per_consumer,
)

METRICS = ROOT / 'outputs' / 'metrics' / 'seasonal_analysis_metrics.json'
CONTRACT = ROOT / 'web' / 'public' / 'data' / 'seasonal.json'

stored = json.loads(METRICS.read_text(encoding='utf-8'))

# Same calls energy_analysis.run() makes for the 365-day flagship.
raw = generate_synthetic_data(
    n_consumers=200,
    n_days=365,
    start_date='2024-01-01',
    seasonal=SeasonalConfig(enabled=True),
)
clean = preprocess_pipeline(
    raw.drop(columns=['archetype', 'seasonal_phase'], errors='ignore'),
)

daily = _daily_energy_by_season(clean)
seasons_present = [s for s in SEASON_ORDER if s in set(daily['season'])]
mean_by_season = (daily.groupby('season')['mean_daily_kwh'].mean()
                  .reindex(seasons_present).round(4))
amplitude = _seasonal_amplitude_per_consumer(daily).median()

# --- Honesty gate: the deterministic data path must reproduce the stored
# --- flagship magnitudes before anything is patched.
stored_mean = {k: round(v, 4) for k, v in stored['mean_daily_kwh_by_season'].items()}
computed_mean = {k: round(float(v), 4) for k, v in mean_by_season.items()}
if computed_mean != stored_mean:
    sys.exit(
        f"REFUSING to patch: recomputed mean daily kWh {computed_mean} does not "
        f"match the stored flagship {stored_mean}. The data path has drifted; "
        f"run the full pipeline (py run_module.py energy_analysis "
        f"--n_days 365 --n_consumers 200) instead."
    )
if abs(float(amplitude) - float(stored['amplitude_estimate'])) > 1e-6:
    sys.exit(
        f"REFUSING to patch: recomputed amplitude {amplitude} does not match "
        f"stored {stored['amplitude_estimate']}."
    )

# --- The two new arrays, rounded exactly like seasonal_analysis.py rounds them.
shape_by_season = {r['season']: r['share'] for r in _mean_shape_by_season(clean)}
mean_shape = [
    {'season': s, 'shape': [round(float(v), 6) for v in shape_by_season[s]]}
    for s in seasons_present
]

est = _recover_phase_from_seasons(daily)
truth = raw.groupby('consumer_id')['seasonal_phase'].first().dropna()
joined = pd.concat([est.rename('est'), truth.rename('truth')], axis=1).dropna()
points = [[round(float(t), 2), round(float(e), 2)]
          for t, e in zip(joined['truth'], joined['est'])]
recomputed_r = float(joined['truth'].corr(joined['est']))

# --- Patch both JSONs.
for path in (METRICS, CONTRACT):
    payload = json.loads(path.read_text(encoding='utf-8'))
    payload['mean_shape_by_season'] = mean_shape
    payload['phase_recovery_points'] = points
    path.write_text(json.dumps(payload, indent=2, default=str), encoding='utf-8')
    print(f"patched {path}")

print(f"seasons: {seasons_present}")
print(f"shape check (hour 0 share per season): "
      f"{ {s['season']: s['shape'][0] for s in mean_shape} }")
print(f"phase points: {len(points)} pairs")
print(f"phase r recomputed (unrounded): {recomputed_r:.6f} "
      f"(stored: {stored['phase_recovery_corr']})")