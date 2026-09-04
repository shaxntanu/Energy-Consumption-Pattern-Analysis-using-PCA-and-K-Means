"""
Artifact Export Module (stable data contract for the Vercel explorer)

Turns the on-disk outputs of the most recent pipeline run into a small,
versioned set of JSON/CSV files under web/public/data/. The Vercel app reads
ONLY these files - it never runs sklearn, never re-runs the pipeline, and never
needs the models directory. This is the single contract between Python and the
web app.

Design rules for the contract:

1. Append-only and typed. Every artifact file has a fixed top-level shape and
   the same keys across runs. New keys may be added, existing keys never change
   meaning. Nullable fields are explicitly null (never an empty string or a
   made-up number), and skipped analysis steps carry a `reason` explaining why.
2. Values come from the committed run artifacts (models/analysis_metadata.json
   plus the CSV/JSON under outputs/). Nothing here is recomputed: exporting
   cannot change a number, and re-running export on the same run is idempotent.
3. The CSV mirrors under web/public/data/csv/ are copies of the pipeline's own
   output tables, so a reader can download the exact table a figure was drawn
   from.
4. A manifest.json records which run the files describe (config hash, window,
   timestamp, package versions) so a stale set of files can be spotted by
   comparing the manifest hash with the README.

Run via:  py run_module.py export_artifacts
It is also invoked at the end of EnergyAnalysis.run() so every committed run
leaves a consistent web/ contract behind.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONTRACT_VERSION = '1.0.0'
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = PROJECT_ROOT / 'web' / 'public' / 'data'

# CSV tables copied verbatim into web/public/data/csv/ when they exist.
CSV_MIRRORS = [
    'pca_results.csv',
    'pca_loadings.csv',
    'clustering_metrics.csv',
    'stability_results.csv',
    'k_selection_trace.json',   # JSON, kept alongside the CSV mirrors for download
    'cluster_load_shapes.csv',
    'shap_importance.csv',
    'archetype_recovery.csv',
    'archetype_crosstab.csv',
]


def _read_json(path: Path) -> Optional[dict]:
    """Read a JSON artifact, returning None when missing or unreadable."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(f"Could not read {path}: {exc}")
        return None


def _read_csv_records(path: Path) -> Optional[List[dict]]:
    """Read a CSV as a list of records, or None when missing."""
    if not path.exists():
        return None
    try:
        return pd.read_csv(path).to_dict(orient='records')
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(f"Could not read {path}: {exc}")
        return None


def _csv_to_records(path: Path) -> Optional[List[dict]]:
    """CSV rows with NaN/None normalized to JSON-safe values."""
    records = _read_csv_records(path)
    if records is None:
        return None
    cleaned = []
    for row in records:
        clean = {}
        for key, value in row.items():
            if isinstance(value, float) and pd.isna(value):
                clean[key] = None
            elif isinstance(key, str) and key.endswith('.1') and key.replace('.1', '') in row:
                continue  # duplicated unnamed index columns
            else:
                clean[key] = value
        cleaned.append(clean)
    return cleaned


def _manifest(metadata: dict) -> dict:
    """Top-level record of which run produced these files."""
    return {
        'contract_version': CONTRACT_VERSION,
        'experiment_name': metadata.get('experiment_name'),
        'config_hash': metadata.get('config_hash'),
        'random_seed': metadata.get('random_seed'),
        'n_consumers': metadata.get('n_consumers'),
        'n_days': metadata.get('n_days'),
        'window_start': metadata.get('window_start'),
        'window_label': metadata.get('window_label'),
        'n_records': metadata.get('n_records'),
        'feature_set': metadata.get('feature_set'),
        'n_features': metadata.get('n_features'),
        'dataset_source': metadata.get('dataset_source'),
        'package_versions': metadata.get('package_versions'),
        'generated_utc': metadata.get('timestamp_utc'),
    }


def _pca(metadata: dict) -> dict:
    """Component counts, variance curve and top loadings per component."""
    out = {
        'n_input_features': metadata.get('n_features'),
        'variance_threshold': metadata.get('pca_variance_threshold'),
        'n_components_retained': metadata.get('pca_components'),
        'cumulative_variance_retained': metadata.get('pca_cumulative_variance'),
        'component_count_by_criterion': None,
        'component_descriptions': None,
        'variance_curve': None,
        'top_loadings_per_component': None,
    }

    pca_meta = _read_json(PROJECT_ROOT / 'models' / 'pca_metadata.json')
    if pca_meta:
        out['component_count_by_criterion'] = pca_meta.get('component_count_by_criterion')
        out['component_descriptions'] = pca_meta.get('component_descriptions')

    variance = _csv_to_records(PROJECT_ROOT / 'outputs' / 'metrics' / 'pca_results.csv')
    if variance is not None:
        out['variance_curve'] = variance

    loadings = _read_csv_records(PROJECT_ROOT / 'outputs' / 'metrics' / 'pca_loadings.csv')
    if loadings:
        # Top-5 absolute loadings per retained component.
        per_component = []
        pc_cols = [c for c in loadings[0].keys() if str(c).upper().startswith('PC')]
        for pc in pc_cols:
            ranked = sorted(loadings, key=lambda row: -abs(row.get(pc) or 0.0))[:5]
            per_component.append({
                'component': pc,
                'top_loadings': [
                    {'feature': row.get('feature'), 'loading': row.get(pc)}
                    for row in ranked
                ],
            })
        out['top_loadings_per_component'] = per_component
    return out


def _clustering(metadata: dict) -> dict:
    """Full K sweep, selection trace and the chosen K."""
    out = {
        'k_range': metadata.get('k_range'),
        'selected_k': metadata.get('selected_k'),
        'silhouette_at_selected_k': metadata.get('silhouette_at_selected_k'),
        'cluster_sizes': metadata.get('cluster_sizes'),
        'cluster_names': metadata.get('cluster_names'),
        'stability_at_selected_k': metadata.get('stability_at_selected_k'),
        'k_selection_trace': metadata.get('k_selection_trace'),
        'metrics_by_k': None,
        'stability_by_k': None,
    }
    metrics = _csv_to_records(PROJECT_ROOT / 'outputs' / 'metrics' / 'clustering_metrics.csv')
    if metrics is not None:
        out['metrics_by_k'] = metrics
    stability = _csv_to_records(PROJECT_ROOT / 'outputs' / 'metrics' / 'stability_results.csv')
    if stability is not None:
        out['stability_by_k'] = stability
    return out


def _profiles(metadata: dict) -> dict:
    """Per-cluster profiles, load shapes and the population baseline."""
    out = {
        'cluster_profiles': None,
        'cluster_load_shapes': None,
        'population_baseline': None,
    }
    profiles = _csv_to_records(PROJECT_ROOT / 'outputs' / 'reports' / 'cluster_profiles.csv')
    if profiles is not None:
        out['cluster_profiles'] = profiles

    shapes = _csv_to_records(PROJECT_ROOT / 'outputs' / 'metrics' / 'cluster_load_shapes.csv')
    if shapes:
        # Rows are cluster id + 24 hour columns; expose as {"cluster", "shape": [...]}.
        # The CSV header names the hour columns "0".."23" (strings after read_csv),
        # so look them up by string, with the int key as a fallback for any writer
        # that produced integer column names.
        rows = []
        for row in shapes:
            cluster = row.get('cluster')
            if cluster is None:
                continue
            shape = [row.get(str(h), row.get(h)) for h in range(24)]
            rows.append({'cluster': str(cluster), 'shape': shape})
        out['cluster_load_shapes'] = rows

    baseline = _read_json(PROJECT_ROOT / 'outputs' / 'reports' / 'population_baseline.json')
    if baseline is not None:
        out['population_baseline'] = baseline
    return out


def _validation(metadata: dict) -> dict:
    """Recovery against the hidden archetypes (synthetic data only).

    Same trust boundary as _seasonal/_longitudinal/_explainability: the run
    metadata is the authoritative record of whether THIS run computed archetype
    recovery. ari_vs_archetypes_at_selected_k is only non-null when the pipeline
    actually found a hidden archetype column and ran the recovery check, so a
    stale archetype_recovery.csv left on disk by an earlier synthetic run cannot
    be reported as the result of a run that skipped the check (e.g. real data
    with no archetype column).
    """
    ari_at_selected_k = metadata.get('ari_vs_archetypes_at_selected_k')
    if ari_at_selected_k is None:
        return {
            'available': False,
            'reason': 'No archetype ground truth: this run has no hidden archetype column '
                      '(real-world data, or the check was skipped).',
            'recovery_by_k': None,
            'crosstab': None,
            'selected_k_ari': None,
            'n_true_archetypes': None,
        }

    recovery = _csv_to_records(PROJECT_ROOT / 'outputs' / 'metrics' / 'archetype_recovery.csv')
    crosstab = _read_csv_records(PROJECT_ROOT / 'outputs' / 'metrics' / 'archetype_crosstab.csv')

    if not recovery:
        return {
            'available': False,
            'reason': 'Metadata records archetype recovery for this run, but the recovery '
                      'table is missing from disk.',
            'recovery_by_k': None,
            'crosstab': None,
            'selected_k_ari': ari_at_selected_k,
            'n_true_archetypes': None,
        }

    selected_k = metadata.get('selected_k')
    selected_ari = next(
        (r.get('ari') for r in recovery if int(r.get('K')) == int(selected_k)), None)
    n_true = recovery[0].get('n_true_archetypes') if recovery else None
    best = max(recovery, key=lambda r: r.get('ari') or 0.0) if recovery else None

    return {
        'available': True,
        'reason': 'Synthetic data only: comparing clusters with the generator\'s '
                  'hidden archetypes is an independent check that a real dataset cannot offer.',
        'recovery_by_k': recovery,
        'crosstab': crosstab,
        'selected_k_ari': selected_ari,
        'n_true_archetypes': n_true,
        'best_recovery_k': int(best['K']) if best else None,
        'best_recovery_ari': best.get('ari') if best else None,
        'descriptive_paragraph': (
            f"The generator drew consumers from {n_true} archetypes. The pipeline "
            f"selected K={selected_k} using internal indices only, and at that K the "
            f"Adjusted Rand Index against the archetypes is {selected_ari:.4f}."
            if selected_ari is not None else None
        ),
    }


def _seasonal(metadata: dict) -> dict:
    """Seasonal estimates, or an explicit skip reason when not available.

    Trust boundary: the run metadata is the authoritative record of whether THIS
    run computed seasonal estimates. The metrics file on disk is only written
    when seasonal analysis actually ran (see seasonal_analysis.py), so an older,
    longer run can leave a stale file behind that a later short run does not
    overwrite. Reading it unconditionally would leak numbers from a different
    run into the contract - so the file is only trusted when the metadata's
    seasonal_amplitude_estimate is non-null.
    """
    amplitude = metadata.get('seasonal_amplitude_estimate')
    if amplitude is None:
        return {
            'available': False,
            'reason': 'Seasonal analysis was not run for this window (short horizon, '
                      'seasonality disabled, or no season column with >= 2 distinct values).',
            'seasons_present': None,
            'mean_daily_kwh_by_season': None,
            'peak_hour_by_season': None,
            'amplitude_estimate': None,
            'phase_recovery_corr': None,
        }
    metrics = _read_json(PROJECT_ROOT / 'outputs' / 'metrics' / 'seasonal_analysis_metrics.json')
    if metrics is None:
        return {
            'available': False,
            'reason': 'Seasonal metrics file missing for a run that recorded an amplitude estimate.',
            'seasons_present': None,
            'mean_daily_kwh_by_season': None,
            'peak_hour_by_season': None,
            'amplitude_estimate': amplitude,
            'phase_recovery_corr': metadata.get('seasonal_phase_recovery_corr'),
        }
    return {
        'available': True,
        'seasons_present': metrics.get('seasons_present'),
        'mean_daily_kwh_by_season': metrics.get('mean_daily_kwh_by_season'),
        'peak_hour_by_season': metrics.get('peak_hour_by_season'),
        'amplitude_estimate': metrics.get('amplitude_estimate'),
        'amplitude_estimate_q25': metrics.get('amplitude_estimate_q25'),
        'amplitude_estimate_q75': metrics.get('amplitude_estimate_q75'),
        'n_consumers_with_amplitude': metrics.get('n_consumers_with_amplitude'),
        'phase_recovery_corr': metrics.get('phase_recovery_corr'),
        'phase_accuracy': metrics.get('phase_accuracy'),
        'n_truth_consumers': metrics.get('n_truth_consumers'),
    }


def _longitudinal(metadata: dict) -> dict:
    """Longitudinal stability, or an explicit skip reason when not available.

    Same trust boundary as _seasonal: gate on the metadata (authoritative for
    THIS run) so a stale longitudinal_analysis_metrics.json left behind by an
    earlier longer run cannot be reported as this run's result.
    """
    lon = metadata.get('longitudinal_temporal_stability_ari')
    if lon is None:
        return {
            'available': False,
            'reason': 'Longitudinal analysis was not run for this window (needs a window >= 180 days).',
            'n_segments': None,
            'segment_ari_vs_full': None,
            'mean_temporal_stability_ari': None,
            'monthly_mean_daily_kwh': None,
        }
    metrics = _read_json(PROJECT_ROOT / 'outputs' / 'metrics' / 'longitudinal_analysis_metrics.json')
    if metrics is None:
        return {
            'available': False,
            'reason': 'Longitudinal metrics file missing for a run that recorded a temporal stability ARI.',
            'n_segments': None,
            'segment_ari_vs_full': None,
            'mean_temporal_stability_ari': lon,
            'monthly_mean_daily_kwh': None,
        }
    return {
        'available': True,
        'n_segments': metrics.get('n_segments'),
        'segment_ari_vs_full': metrics.get('segment_ari_vs_full'),
        'segment_labels': metrics.get('segment_labels'),
        'mean_temporal_stability_ari': metrics.get('mean_temporal_stability_ari'),
        'monthly_mean_daily_kwh': metrics.get('monthly_mean_daily_kwh'),
        'n_consumers_per_segment': metrics.get('n_consumers_per_segment'),
        'optimal_k': metrics.get('optimal_k'),
        'feature_set': metrics.get('feature_set'),
    }


def _explainability(metadata: dict) -> dict:
    """Per-cluster feature importance, with an honest method flag.

    Same trust boundary as _seasonal/_longitudinal: the run metadata's
    explainability_method is authoritative for THIS run. The metrics file on
    disk is only written when the step actually ran (explainability.py writes it
    on the success path only), so reading it unconditionally could leak an older
    run's SHAP numbers into a run that skipped the step. The metadata records
    method=None for a skipped step, which flips this to the honest empty state.
    """
    method = metadata.get('explainability_method')
    if not method:
        return {
            'available': False,
            'reason': 'Explainability was not run for this window.',
            'method': None,
            'cv_balanced_accuracy': None,
            'per_cluster': None,
            'global_importance': None,
        }
    metrics = _read_json(PROJECT_ROOT / 'outputs' / 'metrics' / 'explainability.json')
    if metrics is None or metrics.get('method') != method:
        return {
            'available': False,
            'reason': 'Explainability metrics file missing for a run that recorded a method.',
            'method': method,
            'cv_balanced_accuracy': metadata.get('explainability_cv_accuracy'),
            'per_cluster': None,
            'global_importance': None,
        }
    return {
        'available': True,
        'method': metrics.get('method'),
        'surrogate': metrics.get('surrogate'),
        'n_features': metrics.get('n_features'),
        'n_clusters': metrics.get('n_clusters'),
        'n_consumers': metrics.get('n_consumers'),
        'cv_balanced_accuracy': metrics.get('cv_balanced_accuracy'),
        'per_cluster': metrics.get('per_cluster'),
        'global_importance': metrics.get('global_importance'),
    }


def _write_json(out_dir: Path, name: str, payload: dict) -> None:
    (out_dir / name).write_text(json.dumps(payload, indent=2, default=str), encoding='utf-8')


def export_artifacts(out_dir: str = None, metadata_path: str = None) -> dict:
    """Assemble and write the full artifact contract.

    Args:
        out_dir: Destination directory. Defaults to web/public/data under the
            project root.
        metadata_path: Run metadata JSON. Defaults to models/analysis_metadata.json.

    Returns:
        Dict mapping artifact file name to the number of keys written, plus the
        manifest, for logging and testing.
    """
    out = Path(out_dir) if out_dir else DEFAULT_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / 'csv').mkdir(parents=True, exist_ok=True)

    meta_path = Path(metadata_path) if metadata_path else PROJECT_ROOT / 'models' / 'analysis_metadata.json'
    metadata = _read_json(meta_path)
    if metadata is None:
        raise FileNotFoundError(
            f"No run metadata found at {meta_path}. Run the pipeline first "
            "(py run_module.py energy_analysis) or pass --metadata.")

    artifacts = {
        'manifest.json': _manifest(metadata),
        'pca.json': _pca(metadata),
        'clustering.json': _clustering(metadata),
        'profiles.json': _profiles(metadata),
        'validation.json': _validation(metadata),
        'seasonal.json': _seasonal(metadata),
        'longitudinal.json': _longitudinal(metadata),
        'explainability.json': _explainability(metadata),
    }

    summary = {}
    for name, payload in artifacts.items():
        _write_json(out, name, payload)
        summary[name] = len(payload)
        logger.info(f"Wrote {out / name} ({len(payload)} top-level keys)")

    # CSV mirrors for download.
    copied = []
    for filename in CSV_MIRRORS:
        source = PROJECT_ROOT / 'outputs' / 'metrics' / filename
        if source.exists():
            target = out / 'csv' / filename
            target.write_bytes(source.read_bytes())
            copied.append(filename)
    logger.info(f"Copied {len(copied)} CSV/JSON mirrors to {out / 'csv'}")

    summary['csv_mirrors'] = copied
    summary['manifest'] = artifacts['manifest.json']
    return summary


if __name__ == "__main__":
    import argparse
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    parser = argparse.ArgumentParser(description="Export the stable artifact contract for the Vercel explorer")
    parser.add_argument('--out', default=None, help='Output directory (default web/public/data)')
    parser.add_argument('--metadata', default=None,
                        help='Run metadata JSON (default models/analysis_metadata.json)')
    args = parser.parse_args()

    result = export_artifacts(out_dir=args.out, metadata_path=args.metadata)
    print(json.dumps(result, indent=2))