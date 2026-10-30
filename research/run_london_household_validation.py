"""Validate shape-first clustering on a seeded London household subset.

The run uses a fixed set of complete member CSVs from the official 168-file
London SmartMeter archive. The official resource is too large for some download
paths; the exact members are listed in each result sidecar. No raw readings are
stored in the repository.

Example:
    python research/run_london_household_validation.py --source C:/data/Partitioned-LCL.zip
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import struct
import sys
import zipfile
import zlib
from collections import defaultdict
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clustering import N_INIT, find_optimal_k, select_optimal_k  # noqa: E402
from feature_engineering import engineer_all_features, select_features  # noqa: E402
from pca_analysis import perform_pca  # noqa: E402
from preprocessing import preprocess_pipeline  # noqa: E402

logger = logging.getLogger("london_household_validation")

DATASET_URL = "https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d"
DATASET_TITLE = "SmartMeter Energy Consumption Data in London Households"
DATASET_LICENSE = "Creative Commons Attribution"
MEMBER_INDICES = [0, 1, 10, 100, 101, 102, 103, 104, 105, 106, 107]
MEMBERS = [f"Small LCL Data/LCL-June2015v2_{i}.csv" for i in MEMBER_INDICES]
EXPECTED_HALF_HOURS_2013 = 365 * 48
MIN_COVERAGE = 0.996
EVENING_SLOTS = np.arange(34, 42)  # 17:00 inclusive to 21:00 exclusive
SHIFT_SLOTS = np.arange(24, 34)    # 12:00 inclusive to 17:00 exclusive


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _iter_member_bytes(source: Path, wanted: list[str]):
    """Yield requested CSV member bytes from a complete or prefix ZIP archive."""
    wanted_set = set(wanted)
    found: set[str] = set()
    try:
        with zipfile.ZipFile(source) as archive:
            for name in wanted:
                if name not in archive.namelist():
                    raise ValueError(f"Required archive member is missing: {name}")
                with archive.open(name) as stream:
                    data = stream.read()
                found.add(name)
                yield name, data
    except zipfile.BadZipFile:
        # The active source may be a transport-truncated ZIP. Its local entries
        # are independently valid through the last complete CSV; parse only the
        # fixed, predeclared member set and stop at the first incomplete member.
        archive_size = source.stat().st_size
        with source.open("rb") as stream:
            while True:
                header = stream.read(30)
                if len(header) != 30:
                    break
                (signature, version, flags, method, mtime, mdate, crc,
                 compressed_size, uncompressed_size, name_length,
                 extra_length) = struct.unpack("<IHHHHHIIIHH", header)
                if signature != 0x04034B50:
                    break
                name = stream.read(name_length).decode("utf-8", "replace")
                stream.seek(extra_length, 1)
                if flags & 0x08:
                    raise ValueError("ZIP data-descriptor entries are not supported.")
                if stream.tell() + compressed_size > archive_size:
                    break
                compressed = stream.read(compressed_size)
                if name not in wanted_set:
                    continue
                if method == 8:
                    data = zlib.decompress(compressed, -15)
                elif method == 0:
                    data = compressed
                else:
                    raise ValueError(f"Unsupported ZIP compression method {method} for {name}.")
                if len(data) != uncompressed_size:
                    raise ValueError(f"Uncompressed size mismatch for {name}.")
                found.add(name)
                yield name, data
        missing = wanted_set - found
        if missing:
            raise ValueError(
                "The available archive does not contain all predeclared complete "
                f"members. Missing: {sorted(missing)}"
            )


def _read_csv_chunks(data: bytes, *, usecols: set[str], chunksize: int):
    reader = pd.read_csv(
        BytesIO(data),
        chunksize=chunksize,
        low_memory=False,
        skipinitialspace=True,
        usecols=lambda column: column.strip() in usecols,
        dtype={"LCLid": "string", "DateTime": "string"},
    )
    for chunk in reader:
        chunk.columns = [str(column).strip() for column in chunk.columns]
        yield chunk


def _discover_eligible_households(source: Path, *, min_coverage: float) -> tuple[list[str], dict]:
    counts: dict[str, int] = defaultdict(int)
    months: dict[str, set[int]] = defaultdict(set)
    member_facts = []
    for name, data in _iter_member_bytes(source, MEMBERS):
        member_count = 0
        for chunk in _read_csv_chunks(data, usecols={"LCLid", "DateTime"}, chunksize=200_000):
            text = chunk["DateTime"].astype("string")
            in_year = text.str.startswith("2013", na=False)
            if not in_year.any():
                continue
            ids = chunk.loc[in_year, "LCLid"].astype(str)
            month = pd.to_numeric(text.loc[in_year].str.slice(5, 7), errors="coerce")
            member_count += int(len(ids))
            local_counts = ids.value_counts(sort=False)
            for household, count in local_counts.items():
                counts[str(household)] += int(count)
            for household, month_value in zip(ids.to_numpy(), month.to_numpy()):
                if np.isfinite(month_value):
                    months[str(household)].add(int(month_value))
        member_facts.append({"member": name, "rows_in_2013": member_count,
                             "uncompressed_sha256": hashlib.sha256(data).hexdigest()})

    threshold = int(np.ceil(EXPECTED_HALF_HOURS_2013 * min_coverage))
    eligible = sorted(
        household for household, count in counts.items()
        if count >= threshold and len(months[household]) == 12
    )
    facts = {
        "member_files": member_facts,
        "households_observed": int(len(counts)),
        "coverage_threshold_halfhour_rows": threshold,
        "eligible_households": int(len(eligible)),
        "eligible_household_ids": eligible,
        "row_count_quantiles": {
            str(q): float(np.quantile(list(counts.values()), q))
            for q in (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0)
        },
        "eligible_month_requirement": "at least one source reading in every calendar month of 2013",
    }
    return eligible, facts


def _load_sample(source: Path, *, n_households: int, sample_seed: int,
                 min_coverage: float) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    eligible, discovery = _discover_eligible_households(source, min_coverage=min_coverage)
    if len(eligible) < 8:
        raise ValueError(f"Only {len(eligible)} households pass coverage checks.")
    rng = np.random.default_rng(sample_seed)
    sample_size = min(n_households, len(eligible))
    selected = sorted(rng.choice(eligible, size=sample_size, replace=False).tolist())

    parts = []
    invalid = 0
    for name, data in _iter_member_bytes(source, MEMBERS):
        for chunk in _read_csv_chunks(
            data,
            usecols={"LCLid", "stdorToU", "DateTime", "KWH/hh (per half hour)"},
            chunksize=200_000,
        ):
            chunk = chunk.rename(columns={"KWH/hh (per half hour)": "energy_kwh_halfhour"})
            times = chunk["DateTime"].astype("string")
            mask = chunk["LCLid"].astype(str).isin(selected) & times.str.startswith("2013", na=False)
            if not mask.any():
                continue
            take = chunk.loc[mask, ["LCLid", "stdorToU", "DateTime", "energy_kwh_halfhour"]].copy()
            take["timestamp"] = pd.to_datetime(take["DateTime"], errors="coerce")
            take["energy_kwh_halfhour"] = pd.to_numeric(
                take["energy_kwh_halfhour"], errors="coerce"
            )
            invalid_mask = (
                take["timestamp"].isna()
                | take["energy_kwh_halfhour"].isna()
                | ~np.isfinite(take["energy_kwh_halfhour"].to_numpy(dtype=float))
                | (take["energy_kwh_halfhour"] < 0)
            )
            invalid += int(invalid_mask.sum())
            take = take.loc[~invalid_mask]
            take["consumer_id"] = take["LCLid"].astype(str)
            take["timestamp"] = take["timestamp"] - pd.Timedelta(minutes=30)
            parts.append(take[["consumer_id", "timestamp", "energy_kwh_halfhour", "stdorToU"]])
    if invalid:
        raise ValueError(f"Found {invalid} invalid readings in the selected 2013 sample.")
    if not parts:
        raise ValueError("No selected household records were found in the requested archive members.")

    halfhour = pd.concat(parts, ignore_index=True)
    exact_duplicates = int(
        halfhour.duplicated(
            ["consumer_id", "timestamp", "energy_kwh_halfhour", "stdorToU"]
        ).sum()
    )
    halfhour = halfhour.drop_duplicates(
        ["consumer_id", "timestamp", "energy_kwh_halfhour", "stdorToU"], keep="first"
    )
    halfhour = halfhour.sort_values(["consumer_id", "timestamp"]).reset_index(drop=True)

    coverage = halfhour.groupby("consumer_id").size()
    months_seen = halfhour.groupby("consumer_id")["timestamp"].apply(
        lambda values: int(values.dt.month.nunique())
    )
    threshold = int(np.ceil(EXPECTED_HALF_HOURS_2013 * min_coverage))
    retained = sorted(
        household for household in selected
        if coverage.get(household, 0) >= threshold and months_seen.get(household, 0) == 12
    )
    if len(retained) < 8:
        raise ValueError("Fewer than eight sampled households remain after exact duplicate removal.")
    halfhour = halfhour[halfhour["consumer_id"].isin(retained)].reset_index(drop=True)

    # Aggregate each two half-hour kWh readings into the hour they cover. The
    # source timestamps denote interval ends; interval start is used here.
    hourly = (halfhour.assign(hour_timestamp=halfhour["timestamp"].dt.floor("h"))
              .groupby(["consumer_id", "hour_timestamp"], as_index=False)
              ["energy_kwh_halfhour"].sum(min_count=1)
              .rename(columns={"hour_timestamp": "timestamp"})
              .rename(columns={"energy_kwh_halfhour": "energy_consumption_kwh"}))
    facts = {
        "source_name": DATASET_TITLE,
        "source_url": DATASET_URL,
        "license": DATASET_LICENSE,
        "data_period": "2013-01-01 through 2013-12-31",
        "selected_archive_members": MEMBERS,
        "selected_member_indices": MEMBER_INDICES,
        "households_observed_in_members": discovery["households_observed"],
        "coverage_eligible_households": discovery["eligible_households"],
        "requested_households": int(n_households),
        "sampled_households_before_postcheck": selected,
        "analyzed_households": int(len(retained)),
        "analyzed_household_ids": retained,
        "sampling": {
            "method": "uniform seeded sample without replacement from coverage-eligible households in the selected complete archive members",
            "seed": int(sample_seed),
        },
        "coverage": {
            "expected_halfhour_records": EXPECTED_HALF_HOURS_2013,
            "minimum_fraction": float(min_coverage),
            "minimum_records": threshold,
            "selected_record_count_min": int(coverage.reindex(retained).min()),
            "selected_record_count_median": float(coverage.reindex(retained).median()),
            "selected_record_count_max": int(coverage.reindex(retained).max()),
            "months_per_retained_household": 12,
        },
        "exact_duplicate_rows_removed": exact_duplicates,
        "invalid_rows": int(invalid),
        "half_hour_rows_after_cleaning": int(len(halfhour)),
        "hourly_records": int(len(hourly)),
        "hourly_households": int(hourly["consumer_id"].nunique()),
        "tariff_categories": sorted(halfhour["stdorToU"].dropna().astype(str).unique().tolist()),
        "timestamp_conversion": (
            "Source timestamp is treated as the end of its 30-minute kWh interval; "
            "30 minutes are subtracted, then two intervals are summed to hourly kWh. "
            "No external timezone or daylight-saving correction is applied."
        ),
        "member_facts": discovery["member_files"],
    }
    return hourly, facts, halfhour


def _features(panel: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, object, int]:
    preprocessed = preprocess_pipeline(
        panel,
        column_ranges={"energy_consumption_kwh": (0, np.inf)},
    )
    engineered = engineer_all_features(preprocessed, feature_set="behavioral")
    engineered = engineered.sort_values("consumer_id").reset_index(drop=True)
    selected = select_features(engineered, feature_group="behavioral")
    numeric = selected.drop(columns="consumer_id").select_dtypes(include=[np.number])
    if numeric.isna().any().any():
        numeric = numeric.fillna(numeric.median())
    scaled = StandardScaler().fit_transform(numeric)
    pca, scores, n_components, _ = perform_pca(scaled, variance_threshold=0.95)
    return engineered, scores, pca, n_components


def _monthly_stability(panel: pd.DataFrame, full_labels: np.ndarray,
                       household_ids: list[str], k: int, seed: int,
                       bootstrap_seed: int, draws: int = 2000) -> list[dict]:
    rng = np.random.default_rng(bootstrap_seed)
    rows = []
    for month in range(1, 13):
        subset = panel[pd.to_datetime(panel["timestamp"]).dt.month == month].copy()
        subset = preprocess_pipeline(
            subset,
            column_ranges={"energy_consumption_kwh": (0, np.inf)},
        )
        engineered = engineer_all_features(subset, feature_set="behavioral")
        engineered = engineered.sort_values("consumer_id").reset_index(drop=True)
        engineered = engineered.set_index("consumer_id").reindex(household_ids).reset_index()
        selected = select_features(engineered, feature_group="behavioral")
        numeric = selected.drop(columns="consumer_id").select_dtypes(include=[np.number])
        if numeric.isna().any().any():
            numeric = numeric.fillna(numeric.median()).fillna(0.0)
        scaled = StandardScaler().fit_transform(numeric)
        _, scores, _, _ = perform_pca(scaled, variance_threshold=0.95)
        labels = KMeans(n_clusters=k, random_state=seed, n_init=N_INIT).fit_predict(scores)
        ari = float(adjusted_rand_score(full_labels, labels))
        bootstrap = []
        n = len(full_labels)
        for _ in range(draws):
            sample = rng.integers(0, n, size=n)
            bootstrap.append(adjusted_rand_score(full_labels[sample], labels[sample]))
        rows.append({
            "month": month,
            "n_days": int(subset["timestamp"].dt.day.nunique()),
            "ari_vs_full_year_partition": ari,
            "bootstrap_ci95_low": float(np.quantile(bootstrap, 0.025)),
            "bootstrap_ci95_high": float(np.quantile(bootstrap, 0.975)),
            "household_bootstrap_draws": int(draws),
        })
    return rows


def _cluster_profiles(engineered: pd.DataFrame, labels: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    annotated = engineered.copy()
    annotated["cluster"] = labels
    shape_columns = [f"hour_{hour}_shape" for hour in range(24)]
    profile_rows = []
    for cluster, group in annotated.groupby("cluster", sort=True):
        row = {
            "cluster": int(cluster),
            "households": int(len(group)),
            "share": float(len(group) / len(annotated)),
            "mean_evening_share_18_to_24": float(group["evening_share"].mean()),
            "mean_peak_hour": float(group[shape_columns].to_numpy().argmax(axis=1).mean()),
            "mean_weekend_ratio": float(group["weekend_ratio"].mean()),
        }
        profile_rows.append(row)
    return pd.DataFrame(profile_rows), annotated


def _daily_halfhour_profiles(half_hour: pd.DataFrame, household_ids: list[str]) -> pd.DataFrame:
    data = half_hour.copy()
    data["date"] = data["timestamp"].dt.floor("D")
    data["slot"] = data["timestamp"].dt.hour * 2 + data["timestamp"].dt.minute // 30
    daily = data.pivot_table(
        index=["consumer_id", "date"], columns="slot",
        values="energy_kwh_halfhour", aggfunc="sum",
    ).reindex(columns=range(48))
    profiles = daily.groupby(level="consumer_id", sort=True).mean()
    profiles = profiles.reindex(household_ids)
    if profiles.isna().any().any():
        profiles = profiles.fillna(profiles.median()).fillna(0.0)
    return profiles.astype(float)


def _apply_shift(profiles: pd.DataFrame, mask: np.ndarray,
                 fraction: float) -> tuple[pd.DataFrame, float]:
    changed = profiles.copy()
    source = changed.loc[mask, EVENING_SLOTS]
    moved = float(source.to_numpy().sum() * fraction)
    changed.loc[mask, EVENING_SLOTS] = source * (1.0 - fraction)
    additions = source.sum(axis=1).to_numpy(dtype=float) * fraction / len(SHIFT_SLOTS)
    changed.loc[mask, SHIFT_SLOTS] = (
        changed.loc[mask, SHIFT_SLOTS].to_numpy() + additions[:, None]
    )
    return changed, moved


def _system_metrics(profiles: pd.DataFrame) -> dict:
    # Each half-hour value is kWh, so multiplying by two gives mean kW in that interval.
    aggregate_kw = profiles.sum(axis=0).to_numpy(dtype=float) * 2.0
    evening = aggregate_kw[EVENING_SLOTS]
    return {
        "aggregate_peak_kw": float(aggregate_kw.max()),
        "aggregate_peak_slot": int(np.argmax(aggregate_kw)),
        "evening_peak_kw": float(evening.max()),
        "evening_peak_hour": float(EVENING_SLOTS[np.argmax(evening)] / 2),
        "mean_demand_kw": float(aggregate_kw.mean()),
        "load_factor": float(aggregate_kw.mean() / aggregate_kw.max()),
        "daily_energy_kwh": float(profiles.to_numpy().sum()),
    }


def _plot_cluster_profiles(engineered: pd.DataFrame, labels: np.ndarray,
                           output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    shape_cols = [f"hour_{hour}_shape" for hour in range(24)]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for cluster in sorted(np.unique(labels)):
        values = engineered.loc[labels == cluster, shape_cols].mean(axis=0).to_numpy()
        ax.plot(np.arange(24), values, marker="o", markersize=3,
                linewidth=2, label=f"Cluster {cluster} (n={(labels == cluster).sum()})")
    ax.set(xlabel="Source clock hour", ylabel="Mean normalized hourly energy",
           title="London household profiles by unsupervised cluster",
           xticks=np.arange(0, 24, 2))
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncols=2)
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_monthly(months: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    x = months["month"].to_numpy()
    y = months["ari_vs_full_year_partition"].to_numpy()
    low = months["bootstrap_ci95_low"].to_numpy()
    high = months["bootstrap_ci95_high"].to_numpy()
    ax.errorbar(x, y, yerr=np.vstack([y - low, high - y]), fmt="o-",
                capsize=3, color="#3d8b8b", linewidth=2)
    ax.set(xlabel="Month in 2013", ylabel="ARI vs full-year partition",
           title="Monthly partition agreement across the same households",
           xticks=np.arange(1, 13), ylim=(-0.05, 1.0))
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_demand_response(hourly: pd.DataFrame, n_households: int,
                          output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    scale = 100.0 / n_households
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for column, label, color in [
        ("baseline_kw", "Observed baseline", "#7a8594"),
        ("target_cluster_kw", "Target evening-heavy cluster", "#e07a5f"),
        ("equal_fraction_comparator_kw", "Same flex fraction in other clusters", "#3d8b8b"),
    ]:
        ax.plot(hourly["slot"] / 2, hourly[column] * scale,
                label=label, color=color, linewidth=2.2)
    ax.axvspan(17, 21, color="#e07a5f", alpha=0.10, label="Peak window")
    ax.axvspan(12, 17, color="#3d8b8b", alpha=0.08, label="Shift destination")
    ax.set(xlabel="Source clock hour", ylabel="Average kW per 100 sampled households",
           title="Retrospective London household load-shift scenario",
           xticks=np.arange(0, 24, 2))
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncols=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def run(args: argparse.Namespace) -> tuple[
    dict, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray
]:
    hourly, facts, half_hour = _load_sample(
        args.source, n_households=args.n_households,
        sample_seed=args.sample_seed, min_coverage=args.min_coverage,
    )
    engineered, scores, pca, n_components = _features(hourly)
    household_ids = engineered["consumer_id"].astype(str).tolist()
    k_values, inertia, silhouette, ch, db, stability = find_optimal_k(
        scores, k_range=(2, 9), random_state=args.seed,
        stability_runs=args.stability_runs,
    )
    selected_k, trace = select_optimal_k(
        k_values, inertia, silhouette, ch, db, stability_by_k=stability,
    )
    labels = KMeans(n_clusters=selected_k, random_state=args.seed,
                    n_init=N_INIT).fit_predict(scores)
    cluster_profiles, annotated = _cluster_profiles(engineered, labels)

    monthly_rows = _monthly_stability(
        hourly, labels, household_ids, selected_k, args.seed,
        bootstrap_seed=args.bootstrap_seed,
    )
    monthly = pd.DataFrame(monthly_rows)

    # Use the actual half-hour household series for the scenario. The target
    # cluster is selected by its mean per-household share in 17:00-21:00.
    half_profiles = _daily_halfhour_profiles(half_hour, household_ids)
    normalized = half_profiles.div(half_profiles.sum(axis=1).replace(0, np.nan), axis=0)
    profile_labels = pd.Series(labels, index=household_ids)
    cluster_evening_share = normalized.groupby(profile_labels).apply(
        lambda frame: float(frame.iloc[:, EVENING_SLOTS].sum(axis=1).mean()),
        include_groups=False,
    )
    target_cluster = int(cluster_evening_share.idxmax())
    target_mask = labels == target_cluster
    other_mask = ~target_mask
    baseline_metrics = _system_metrics(half_profiles)
    target_scenario, target_shift = _apply_shift(half_profiles, target_mask, args.flex_fraction)
    comparator_fraction = args.flex_fraction
    comparator, comparator_shift = _apply_shift(half_profiles, other_mask, comparator_fraction)

    scenario_records = []
    for name, profile, moved, fraction in [
        ("observed_baseline", half_profiles, 0.0, 0.0),
        ("target_evening_heavy_cluster", target_scenario, target_shift, args.flex_fraction),
        ("same_fraction_non_target_comparator", comparator, comparator_shift, comparator_fraction),
    ]:
        metrics = _system_metrics(profile)
        scenario_records.append({
            "scenario": name,
            **metrics,
            "energy_shifted_kwh_per_average_day": float(moved),
            "fraction_of_evening_energy_shifted": float(fraction),
            "evening_peak_reduction_kw_vs_baseline": float(
                baseline_metrics["evening_peak_kw"] - metrics["evening_peak_kw"]
            ),
            "evening_peak_reduction_percent_vs_baseline": float(
                100 * (baseline_metrics["evening_peak_kw"] - metrics["evening_peak_kw"])
                / baseline_metrics["evening_peak_kw"]
            ),
            "daily_energy_change_kwh": float(
                metrics["daily_energy_kwh"] - baseline_metrics["daily_energy_kwh"]
            ),
            "evening_peak_reduction_kw_per_mwh_shifted": (
                float(1000.0 * (baseline_metrics["evening_peak_kw"] - metrics["evening_peak_kw"]) / moved)
                if moved > 0 else 0.0
            ),
        })
    scenarios = pd.DataFrame(scenario_records)

    demand_profiles = pd.DataFrame({"slot": np.arange(48)})
    demand_profiles["baseline_kw"] = half_profiles.sum(axis=0).to_numpy(dtype=float) * 2
    demand_profiles["target_cluster_kw"] = target_scenario.sum(axis=0).to_numpy(dtype=float) * 2
    demand_profiles["equal_fraction_comparator_kw"] = comparator.sum(axis=0).to_numpy(dtype=float) * 2

    metadata = {
        "study": "london_smartmeter_household_2013_shape_clustering_and_peak_shift_scenario",
        "dataset": {
            "title": DATASET_TITLE,
            "url": DATASET_URL,
            "license": DATASET_LICENSE,
            "original_population_size_reported_by_source": 5567,
            "interval": "30-minute kWh per household",
        },
        "source_file": {
            "filename": args.source.name,
            "size_bytes": int(args.source.stat().st_size),
            "sha256": _sha256(args.source),
            "complete_archive_available": bool(zipfile.is_zipfile(args.source)),
            "note": (
                "This analysis used only the 11 predeclared complete CSV members listed in selected_archive_members. "
                "The local official ZIP prefix was transport-truncated; this convenience subset is not a random sample "
                "of the full 5,567-household population."
            ),
        },
        "sampling_and_coverage": facts,
        "clustering": {
            "feature_count": int(len([c for c in engineered.columns if c != "consumer_id"])),
            "feature_set": "51 scale-invariant behavioral features",
            "pca_components": int(n_components),
            "pca_cumulative_variance": float(np.cumsum(pca.explained_variance_ratio_)[n_components - 1]),
            "k_candidates": k_values,
            "selected_k": int(selected_k),
            "selection_trace": trace,
            "silhouette_at_selected_k": float(silhouette[selected_k]),
            "stability_at_selected_k": stability[selected_k],
            "seed": int(args.seed),
            "stability_restarts_per_k": int(args.stability_runs),
        },
        "cluster_profiles": cluster_profiles.to_dict(orient="records"),
        "monthly_partition_agreement": monthly.to_dict(orient="records"),
        "demand_response_scenario": {
            "target_cluster": target_cluster,
            "target_cluster_size": int(target_mask.sum()),
            "target_cluster_mean_17_to_21_energy_share": float(cluster_evening_share.loc[target_cluster]),
            "evening_slots_half_open": [17, 21],
            "destination_slots_half_open": [12, 17],
            "assumed_target_flex_fraction": float(args.flex_fraction),
            "same_fraction_non_target_flex_fraction": float(comparator_fraction),
            "metrics": scenarios.to_dict(orient="records"),
            "interpretation_limit": (
                "This is an assumption-driven retrospective shift of observed load. It does not estimate "
                "causal tariff response, realized savings, or household flexibility."
            ),
        },
        "bootstrap": {
            "unit": "household, conditional on the full-year clustering and selected K",
            "draws_per_month": 2000,
            "seed": int(args.bootstrap_seed),
            "interval": "percentile 95% confidence interval for monthly ARI",
        },
        "software": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "interpretation_limit": (
            "Unlabeled clusters describe this seeded subset only. Household bootstrap intervals quantify sample "
            "variation conditional on the selected archive members, feature pipeline, and annual K; they do not "
            "measure uncertainty for all London households or validate behavioral meaning."
        ),
    }
    return metadata, monthly, cluster_profiles, scenarios, demand_profiles, engineered, labels


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="Official partitioned London ZIP (complete or a prefix with all required members).")
    parser.add_argument("--n-households", type=int, default=120)
    parser.add_argument("--sample-seed", type=int, default=42)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-seed", type=int, default=20261029)
    parser.add_argument("--stability-runs", type=int, default=8)
    parser.add_argument("--min-coverage", type=float, default=MIN_COVERAGE)
    parser.add_argument("--flex-fraction", type=float, default=0.10)
    return parser


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    args = _parser().parse_args()
    if args.n_households < 8:
        raise ValueError("At least eight households are required for clustering.")
    if not 0 < args.min_coverage <= 1:
        raise ValueError("--min-coverage must be in (0, 1].")
    if not 0 < args.flex_fraction <= 1:
        raise ValueError("--flex-fraction must be in (0, 1].")
    metadata, monthly, profiles, scenarios, demand_profiles, engineered, labels = run(args)

    out_dir = ROOT / "outputs" / "research_additions"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = ROOT / "outputs" / "reports" / "london_household_validation_2013.md"
    metadata_path = out_dir / "london_household_validation_2013.json"
    monthly_path = out_dir / "london_household_monthly_stability_2013.csv"
    profile_path = out_dir / "london_household_cluster_profiles_2013.csv"
    scenario_path = out_dir / "london_household_demand_response_2013.csv"
    hourly_path = out_dir / "london_household_demand_response_profiles_2013.csv"
    cluster_fig = ROOT / "outputs" / "figures" / "research_additions" / "london_household_clusters_2013.png"
    monthly_fig = ROOT / "outputs" / "figures" / "research_additions" / "london_household_monthly_stability_2013.png"
    scenario_fig = ROOT / "outputs" / "figures" / "research_additions" / "london_household_demand_response_2013.png"
    metadata["outputs"] = {
        "report": str(report_path.relative_to(ROOT)),
        "metadata": str(metadata_path.relative_to(ROOT)),
        "monthly_stability_csv": str(monthly_path.relative_to(ROOT)),
        "cluster_profiles_csv": str(profile_path.relative_to(ROOT)),
        "scenario_csv": str(scenario_path.relative_to(ROOT)),
        "hourly_profiles_csv": str(hourly_path.relative_to(ROOT)),
        "cluster_figure": str(cluster_fig.relative_to(ROOT)),
        "monthly_stability_figure": str(monthly_fig.relative_to(ROOT)),
        "scenario_figure": str(scenario_fig.relative_to(ROOT)),
    }
    monthly.to_csv(monthly_path, index=False)
    profiles.to_csv(profile_path, index=False)
    scenarios.to_csv(scenario_path, index=False)
    demand_profiles.to_csv(hourly_path, index=False)
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")

    _plot_cluster_profiles(engineered, labels, cluster_fig)
    _plot_monthly(monthly, monthly_fig)
    _plot_demand_response(
        demand_profiles, metadata["sampling_and_coverage"]["analyzed_households"], scenario_fig,
    )

    target = scenarios.loc[scenarios["scenario"] == "target_evening_heavy_cluster"].iloc[0]
    comparator = scenarios.loc[
        scenarios["scenario"] == "same_fraction_non_target_comparator"
    ].iloc[0]
    report = [
        "# London household validation and retrospective peak-shift scenario", "",
        f"The public dataset reports 5,567 households with half-hourly kWh readings. This run analyzes "
        f"{metadata['sampling_and_coverage']['analyzed_households']} seeded households from 11 complete CSV members "
        "of the archive. The archive download was truncated after those members; this subset is not a random draw "
        "from the full London population, so results are exploratory and should not be generalized to all 5,567 homes.", "",
        "## Data and clustering protocol", "",
        f"- Period: calendar year 2013; {metadata['sampling_and_coverage']['half_hour_rows_after_cleaning']:,} half-hour records, aggregated into {metadata['sampling_and_coverage']['hourly_records']:,} household-hours.",
        f"- Coverage: each retained household has at least {args.min_coverage:.1%} of expected half-hour readings and at least one reading in every month.",
        f"- Sample: uniform seeded sample without replacement (seed {args.sample_seed}) from coverage-eligible households in the selected archive members.",
        f"- Features: 51 scale-invariant behavioral features; PCA retained {metadata['clustering']['pca_components']} components ({metadata['clustering']['pca_cumulative_variance']:.1%} variance).",
        f"- K selection: candidates 2–8, {args.stability_runs} restart runs per K; selected K={metadata['clustering']['selected_k']}; silhouette={metadata['clustering']['silhouette_at_selected_k']:.3f}.",
        f"- Restart stability at selected K: mean pairwise ARI {metadata['clustering']['stability_at_selected_k']['mean_ari']:.3f}.",
        "- The data have no behavioral ground-truth labels; no ARI/NMI against invented labels is reported.",
        "", "## Cluster profiles", "",
        "| Cluster | Households | Share | Mean peak hour | Mean 18:00–24:00 share | Mean weekend ratio |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in profiles.sort_values("cluster").iterrows():
        report.append(
            f"| {int(row['cluster'])} | {int(row['households'])} | {row['share']:.1%} | "
            f"{row['mean_peak_hour']:.1f} | {row['mean_evening_share_18_to_24']:.3f} | {row['mean_weekend_ratio']:.3f} |"
        )
    report += [
        "", "## Month-by-month partition agreement", "",
        "Each month's 51-feature pipeline is refit on the same household IDs with annual K fixed. ARI measures agreement with the full-year partition, not ground-truth behavior. Bootstrap intervals resample households and are conditional on the selected members, annual K, and full-year assignment.", "",
        "| Month | ARI vs full year | Household-bootstrap 95% CI |",
        "|---:|---:|---:|",
    ]
    for _, row in monthly.iterrows():
        report.append(
            f"| {int(row['month'])} | {row['ari_vs_full_year_partition']:.3f} | "
            f"[{row['bootstrap_ci95_low']:.3f}, {row['bootstrap_ci95_high']:.3f}] |"
        )
    report += [
        "", "## Retrospective load-shifting scenario", "",
        f"The evening-heavy cluster was selected by its highest mean household share of 17:00–21:00 energy. The targeted scenario shifts {args.flex_fraction:.0%} of that cluster's energy in this window evenly into 12:00–17:00. The comparator applies the same {args.flex_fraction:.0%} fraction to the other clusters, so aggregate kWh shifted can differ. Both preserve daily energy by construction and do not estimate actual response or savings.", "",
        "| Scenario | Shifted energy (kWh per average day) | Evening peak (kW) | Evening peak change | Reduction per MWh shifted (kW) | Whole-day peak (kW) | Whole-day peak hour | Daily energy change (kWh) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in scenarios.iterrows():
        report.append(
            f"| {row['scenario']} | {row['energy_shifted_kwh_per_average_day']:.3f} | "
            f"{row['evening_peak_kw']:.3f} | {row['evening_peak_reduction_kw_vs_baseline']:.3f} kW "
            f"({row['evening_peak_reduction_percent_vs_baseline']:.2f}%) | "
            f"{row['evening_peak_reduction_kw_per_mwh_shifted']:.3f} | "
            f"{row['aggregate_peak_kw']:.3f} | {row['aggregate_peak_slot'] / 2:.1f} | "
            f"{row['daily_energy_change_kwh']:.6f} |"
        )
    report += [
        "", f"Under the assumed flexibility, the targeted scenario changes the sampled households' evening coincident peak by {target['evening_peak_reduction_kw_vs_baseline']:.3f} kW and the same-fraction comparator changes it by {comparator['evening_peak_reduction_kw_vs_baseline']:.3f} kW. Compare peak change per MWh shifted because aggregate shifted energy differs. The scenario is conditional on an assumed shift and is not evidence that consumers can or will deliver it.",
        "", "## Reproducibility and limits", "",
        f"- Official dataset: [{DATASET_TITLE}]({DATASET_URL}); license: {DATASET_LICENSE}.",
        f"- Selected member names, member hashes, household IDs, coverage checks, archive size/hash, and transformations are recorded in `{metadata_path.relative_to(ROOT).as_posix()}`.",
        "- Raw meter data are not redistributed in this repository.",
        "- The archive prefix contains members 0, 1, 10, and 100–107 only; this subset does not support population-level claims.",
        "- All clusters remain unlabeled; their descriptions are load-shape summaries only.",
        "- Demand response is a counterfactual shift simulation; it does not estimate tariff effects, actual savings, or flexibility.",
        "", "## Figures", "",
        f"![London household cluster profiles]({Path('../figures/research_additions/london_household_clusters_2013.png').as_posix()})", "",
        f"![Monthly partition agreement]({Path('../figures/research_additions/london_household_monthly_stability_2013.png').as_posix()})", "",
        f"![Retrospective demand-response scenario]({Path('../figures/research_additions/london_household_demand_response_2013.png').as_posix()})", "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report), encoding="utf-8")
    print(f"Report: {report_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Households: {metadata['sampling_and_coverage']['analyzed_households']}")
    print(f"Selected K: {metadata['clustering']['selected_k']}")
    print(f"Mean monthly ARI: {monthly['ari_vs_full_year_partition'].mean():.3f}")
    print(f"Evening peak reduction (targeted): {target['evening_peak_reduction_kw_vs_baseline']:.3f} kW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
