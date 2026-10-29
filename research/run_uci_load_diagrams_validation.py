"""Run the project's real-data pathway on UCI ElectricityLoadDiagrams20112014.

The source archive is not committed. Download it from the UCI page and pass
either the ZIP archive or its extracted ``LD2011_2014.txt`` file:

    python research/run_uci_load_diagrams_validation.py \
        --source C:/data/electricityloaddiagrams20112014.zip

By default this creates a seeded sample of 120 clients for calendar year 2012.
The UCI source contains 15-minute mean-power values in kW. Each value is
converted to quarter-hour kWh (kW / 4), assigned to the preceding interval, and
summed into local-clock-hour energy before the shared analysis pipeline runs.
The client IDs, source hash, and complete run configuration are recorded in the
JSON sidecar. No synthetic archetype labels or ARI/NMI ground-truth scores are
used for this dataset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import zipfile
import platform
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd
import sklearn
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realworld_validate import run_real_world_study, write_report  # noqa: E402

logger = logging.getLogger(__name__)

DATASET_URL = "https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014"
DATASET_CITATION = (
    "Trindade, A. (2015). ElectricityLoadDiagrams20112014 [Dataset]. "
    "UCI Machine Learning Repository. https://doi.org/10.24432/C58C86."
)
DATASET_LICENSE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
SOURCE_FILENAME = "LD2011_2014.txt"


def save_cluster_shape_figure(profiles: pd.DataFrame, output: Path) -> Path:
    """Save a paper-ready plot of mean normalized hourly profiles."""
    shape_columns = [f"mean_hour_{hour}_shape" for hour in range(24)]
    missing = [column for column in shape_columns if column not in profiles.columns]
    if missing:
        raise ValueError(f"Cluster profile output lacks shape columns: {missing}")

    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for _, row in profiles.sort_values("cluster").iterrows():
        values = row[shape_columns].to_numpy(dtype=float)
        ax.plot(
            np.arange(24),
            values,
            marker="o",
            markersize=3,
            linewidth=2,
            label=f"Cluster {int(row['cluster'])} (n={int(row['size'])})",
        )
    ax.set(
        xlabel="Local clock hour",
        ylabel="Mean share of daily energy",
        title="UCI client load shapes by cluster",
        xticks=np.arange(0, 24, 2),
    )
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncols=2)
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output


@contextmanager
def _open_source(source: Path) -> Iterator[tuple[object, str]]:
    """Open either the UCI ZIP archive or its extracted text file."""
    if zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            matches = [
                name for name in archive.namelist()
                if Path(name).name == SOURCE_FILENAME and "__MACOSX" not in name
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one {SOURCE_FILENAME} in {source}; found {matches}."
                )
            with archive.open(matches[0]) as stream:
                yield stream, matches[0]
        return

    if source.name != SOURCE_FILENAME:
        raise ValueError(
            f"Pass the UCI ZIP archive or the extracted {SOURCE_FILENAME} file."
        )
    with source.open("rb") as stream:
        yield stream, source.name


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_uci_panel(
    source: Path,
    *,
    start: str,
    end: str,
    n_meters: int,
    sample_seed: int,
    chunk_days: int = 30,
) -> tuple[pd.DataFrame, dict]:
    """Read a deterministic client sample and return hourly kWh panel data.

    Client sampling is uniform without replacement from the UCI column list.
    The UCI timestamps are quarter-hour interval labels; the final quarter-hour
    value ending at a timestamp is assigned to the interval immediately before
    that timestamp, then grouped into local-clock hours.
    """
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(source)
    if n_meters < 8:
        raise ValueError("At least 8 clients are required for K values 2 through 8.")
    if chunk_days < 1:
        raise ValueError("chunk_days must be positive.")

    start_at = pd.Timestamp(start).normalize()
    end_exclusive = pd.Timestamp(end).normalize() + pd.Timedelta(days=1)
    if start_at >= end_exclusive:
        raise ValueError("start must be on or before end.")

    with _open_source(source) as (stream, member):
        header = pd.read_csv(stream, sep=";", nrows=0, encoding="utf-8-sig")
    if len(header.columns) < 9:
        raise ValueError(f"Expected timestamp plus at least 8 clients; got {len(header.columns)} columns.")

    timestamp_col = header.columns[0]
    all_meters = [str(col) for col in header.columns[1:]]
    count = min(n_meters, len(all_meters))
    rng = np.random.default_rng(sample_seed)
    chosen_ix = np.sort(rng.choice(len(all_meters), size=count, replace=False))
    selected_meters = [all_meters[int(i)] for i in chosen_ix]
    usecols = [timestamp_col, *selected_meters]

    hourly_parts: list[pd.DataFrame] = []
    raw_rows_in_window = 0
    n_invalid = 0
    chunk_size = 96 * chunk_days  # UCI documents 96 quarter-hour readings/day.

    with _open_source(source) as (stream, member):
        chunks = pd.read_csv(
            stream,
            sep=";",
            usecols=usecols,
            chunksize=chunk_size,
            low_memory=False,
            encoding="utf-8-sig",
            decimal=",",
        )
        for chunk_index, chunk in enumerate(chunks, start=1):
            labels = pd.to_datetime(chunk[timestamp_col], errors="raise")
            interval_start = labels - pd.Timedelta(minutes=15)
            keep = (interval_start >= start_at) & (interval_start < end_exclusive)
            if not keep.any():
                continue

            raw_rows_in_window += int(keep.sum())
            starts = interval_start.loc[keep]
            power_kw = chunk.loc[keep, selected_meters].apply(pd.to_numeric, errors="coerce")
            invalid = power_kw.isna() | ~np.isfinite(power_kw)
            n_invalid += int(invalid.to_numpy().sum())
            negative = power_kw < 0
            n_invalid += int(negative.to_numpy().sum())
            if n_invalid:
                raise ValueError(
                    "Selected UCI rows contain missing, non-finite, or negative values; "
                    "stop rather than silently changing the load profiles."
                )

            # Convert each 15-minute mean kW to kWh, then sum the four
            # quarter-hour intervals belonging to each clock hour.
            quarter_kwh = power_kw.astype("float64") / 4.0
            hour_bins = starts.dt.floor("h")
            hourly = quarter_kwh.groupby(hour_bins, sort=True).sum(min_count=4)
            if hourly.isna().any().any():
                incomplete = int(hourly.isna().any(axis=1).sum())
                raise ValueError(
                    f"Found {incomplete} incomplete meter-hour groups in chunk {chunk_index}; "
                    "check timestamp alignment and source completeness."
                )

            values = hourly.to_numpy(dtype=np.float64, copy=False)
            hourly_parts.append(pd.DataFrame({
                "meter_id": np.tile(selected_meters, len(hourly.index)),
                "timestamp": np.repeat(hourly.index.to_numpy(), len(selected_meters)),
                "energy_consumption_kwh": values.reshape(-1),
            }))
            if chunk_index % 4 == 0:
                logger.info("Read %d source chunks", chunk_index)

    if not hourly_parts:
        raise ValueError(f"No readings found between {start} and {end}.")

    panel = pd.concat(hourly_parts, ignore_index=True)
    duplicate_rows = int(panel.duplicated(["meter_id", "timestamp"]).sum())
    if duplicate_rows:
        panel = (panel.groupby(["meter_id", "timestamp"], as_index=False)
                 ["energy_consumption_kwh"].sum())
    panel = panel.sort_values(["meter_id", "timestamp"]).reset_index(drop=True)

    # UCI encodes readings before some clients' commissioning as zero. An
    # all-zero client has no defined normalized daily shape and would form a
    # meaningless cluster of its own, so retain the seeded sample for audit
    # while excluding those clients from clustering.
    client_totals = panel.groupby("meter_id", sort=False)["energy_consumption_kwh"].sum()
    zero_consumption_clients = sorted(
        str(client_id) for client_id in client_totals.index[client_totals <= 0]
    )
    zero_consumption_set = set(zero_consumption_clients)
    selected_clients = [str(client_id) for client_id in client_totals.index]
    active_clients = [client_id for client_id in selected_clients
                      if client_id not in zero_consumption_set]
    panel = panel[panel["meter_id"].isin(active_clients)].reset_index(drop=True)
    if len(active_clients) < 8:
        raise ValueError(
            f"Only {len(active_clients)} sampled clients have positive consumption; "
            "at least 8 are needed for this analysis."
        )

    facts = {
        "source": "public:uci_electricity_load_diagrams_2011_2014",
        "source_name": "UCI ElectricityLoadDiagrams20112014",
        "description": (
            "Real 15-minute electricity consumption for 370 anonymized points/clients; "
            "the source does not establish that every client is a household."
        ),
        "citation": DATASET_CITATION,
        "url": DATASET_URL,
        "license": DATASET_LICENSE,
        "archive_sha256": _sha256(source),
        "source_member": member,
        "rows_read_in_window": raw_rows_in_window,
        "rows_after_hourly_aggregation": int(len(panel)),
        "meters": int(panel["meter_id"].nunique()),
        "zero_consumption_clients_excluded": zero_consumption_clients,
        "date_start": str(panel["timestamp"].min()),
        "date_end": str(panel["timestamp"].max()),
        "raw_missing_or_negative_values": n_invalid,
        "duplicate_meter_hour_rows_merged": duplicate_rows,
        "sampling": {
            "method": "uniform sample without replacement from UCI client columns",
            "seed": sample_seed,
            "requested_clients": n_meters,
            "sampled_clients": selected_clients,
            "zero_consumption_clients_excluded": zero_consumption_clients,
            "analyzed_clients": active_clients,
        },
        "conversion": {
            "source_unit": "kW mean power per 15-minute interval",
            "quarter_hour_kwh": "source_kW / 4",
            "hourly_kwh": "sum of four quarter-hour kWh readings",
            "timestamp_assumption": "each timestamp labels the interval ending then; shift back 15 minutes",
            "time_zone": "Portuguese local clock as supplied by UCI; no timezone conversion",
        },
        "config": {
            "start_inclusive": str(start_at.date()),
            "end_inclusive": str((end_exclusive - pd.Timedelta(days=1)).date()),
            "chunk_days": chunk_days,
        },
        "preprocessing": {
            "energy_upper_bound_kwh": None,
            "outlier_detection": "IQR diagnostic only; no removal",
            "invalid_raw_values": "finite and non-negative checked during import",
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "validation_notes": [
            "No synthetic archetype labels are available or used.",
            "ARI/NMI are not computed against inferred labels.",
            "Client IDs are sampled reproducibly and retained in the JSON sidecar.",
        ],
    }
    return panel, facts


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path,
                        help="UCI ZIP archive or extracted LD2011_2014.txt file.")
    parser.add_argument("--start", default="2012-01-01", help="Inclusive start date.")
    parser.add_argument("--end", default="2012-12-31", help="Inclusive end date.")
    parser.add_argument("--n-meters", type=int, default=120,
                        help="Number of randomly sampled clients (default: 120).")
    parser.add_argument("--sample-seed", type=int, default=42,
                        help="Seed controlling the client sample (default: 42).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Seed for the clustering analysis.")
    parser.add_argument("--chunk-days", type=int, default=30,
                        help="Source rows are processed in this many-day chunks.")
    parser.add_argument("--k-min", type=int, default=2)
    parser.add_argument("--k-max", type=int, default=8)
    parser.add_argument("--stability-runs", type=int, default=8)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "outputs/reports/real_world_uci_load_diagrams_2012.md")
    parser.add_argument("--json", type=Path,
                        default=ROOT / "outputs/reports/real_world_uci_load_diagrams_2012.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _build_parser().parse_args(argv)
    panel, facts = load_uci_panel(
        args.source,
        start=args.start,
        end=args.end,
        n_meters=args.n_meters,
        sample_seed=args.sample_seed,
        chunk_days=args.chunk_days,
    )
    logger.info("Prepared %s: %d clients, %d meter-hours", facts["source_name"],
                facts["meters"], len(panel))

    study = run_real_world_study(
        panel,
        facts,
        k_range=(args.k_min, args.k_max + 1),
        random_state=args.seed,
        stability_runs=args.stability_runs,
    )
    shape_figure = save_cluster_shape_figure(
        study.cluster_profiles,
        ROOT / "outputs/figures/real_world/cluster_load_shapes.png",
    )
    report_text = write_report(study, str(args.out))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        report_text + "\n\n## Data provenance and protocol\n\n"
        + f"- Dataset: {facts['description']}\n"
        + f"- Citation: {facts['citation']}\n"
        + f"- Source: {facts['url']}\n"
        + f"- License: {facts['license']}\n"
        + f"- Raw archive SHA-256: `{facts['archive_sha256']}`\n"
        + f"- Window: {facts['config']['start_inclusive']} to {facts['config']['end_inclusive']} (inclusive)\n"
        + f"- Sampling: {facts['sampling']['method']}; n={facts['meters']}, seed={facts['sampling']['seed']}\n"
        + f"- Zero-consumption sampled clients excluded: {len(facts['zero_consumption_clients_excluded'])}\n"
        + "- Conversion: quarter-hour mean kW divided by four to kWh, then four intervals summed per local-clock hour; timestamps are assumed to mark interval ends.\n"
        + "- Limitation: UCI identifies points/clients, not residential households; there are no behavioral labels, so this is an unsupervised stability and interpretability analysis rather than ground-truth recovery.\n"
        + f"\n![Mean normalized client load shapes]({Path(os.path.relpath(shape_figure, args.out.parent)).as_posix()})\n",
        encoding="utf-8",
    )

    summary = {
        "source": facts,
        "meters": study.n_meters,
        "records": study.n_records,
        "features": study.feature_names,
        "pca_components": study.n_pca_components,
        "pca_cumulative_variance": study.pca_cumulative_variance,
        "k_values": study.k_values,
        "optimal_k": study.optimal_k,
        "internal_scores": study.internal_scores(),
        "silhouette_by_k": study.silhouette_by_k,
        "calinski_harabasz_by_k": study.ch_by_k,
        "davies_bouldin_by_k": study.db_by_k,
        "seed_stability": study.seed_stability_at_k,
        "temporal_stability": study.temporal_stability_at_k,
        "selection_trace": study.selection_trace,
        "cluster_profiles": study.cluster_profiles.to_dict(orient="records"),
        "cluster_shape_figure": str(shape_figure.relative_to(ROOT)),
        "warnings": study.warnings,
        "report_markdown": str(args.out.relative_to(ROOT)) if args.out.is_relative_to(ROOT) else str(args.out),
        "analysis_config": {
            "random_seed": args.seed,
            "k_min": args.k_min,
            "k_max": args.k_max,
            "stability_runs": args.stability_runs,
        },
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"Report: {args.out}")
    print(f"Summary: {args.json}")
    print(study.markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
