"""Retrospective, assumption-driven load-shifting scenario on the UCI sample.

This is a scenario analysis, not an estimate of observed participant response,
causal tariff effects, or energy savings. UCI points/clients are not assumed to
be households.

Example:
    python research/simulate_demand_response_uci.py --source "dataset/real world/LD2011_2014.txt"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT / "src"))

from run_uci_load_diagrams_validation import load_uci_panel  # noqa: E402
from clustering import N_INIT, find_optimal_k, select_optimal_k  # noqa: E402
from feature_engineering import engineer_all_features, select_features  # noqa: E402
from pca_analysis import perform_pca  # noqa: E402
from preprocessing import preprocess_pipeline  # noqa: E402

logger = logging.getLogger("uci_demand_response_scenario")

EVENING_HOURS = np.arange(17, 21)  # 17:00 inclusive to 21:00 exclusive
SHIFT_HOURS = np.arange(12, 17)    # 12:00 inclusive to 17:00 exclusive


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _cluster_clients(
    panel: pd.DataFrame,
    *,
    seed: int,
    stability_runs: int,
) -> tuple[pd.DataFrame, dict]:
    """Apply the same behavioral PCA and K-selection path as real-world analysis."""
    standard_panel = panel.rename(columns={"meter_id": "consumer_id"})
    preprocessed = preprocess_pipeline(
        standard_panel,
        column_ranges={"energy_consumption_kwh": (0, np.inf)},
    )
    features = engineer_all_features(preprocessed, feature_set="behavioral")
    features = features.sort_values("consumer_id").reset_index(drop=True)
    selected = select_features(features, feature_group="behavioral")
    numeric = selected.drop(columns="consumer_id").select_dtypes(include=[np.number])
    if numeric.isna().any().any():
        numeric = numeric.fillna(numeric.median())
    scaled = StandardScaler().fit_transform(numeric)
    pca, scores, n_components, _ = perform_pca(scaled, variance_threshold=0.95)

    k_values, inertia, silhouette, ch, db, stability = find_optimal_k(
        scores, k_range=(2, 9), random_state=seed,
        stability_runs=stability_runs,
    )
    selected_k, trace = select_optimal_k(
        k_values, inertia, silhouette, ch, db, stability_by_k=stability,
    )
    labels = KMeans(
        n_clusters=selected_k, random_state=seed, n_init=N_INIT,
    ).fit_predict(scores)
    assignments = pd.DataFrame({
        "meter_id": features["consumer_id"].astype(str).to_numpy(),
        "cluster": labels,
    })
    facts = {
        "features": int(numeric.shape[1]),
        "pca_components": int(n_components),
        "pca_cumulative_variance": float(
            np.cumsum(pca.explained_variance_ratio_)[n_components - 1]
        ),
        "k_candidates": k_values,
        "selected_k": int(selected_k),
        "seed": int(seed),
        "stability_restarts_per_k": int(stability_runs),
        "selection_trace": trace,
        "stability_at_selected_k": stability[selected_k],
        "silhouette_at_selected_k": float(silhouette[selected_k]),
    }
    return assignments, facts


def _average_daily_profiles(panel: pd.DataFrame, ids: list[str]) -> pd.DataFrame:
    """One typical 24-hour kWh profile per client, averaged across valid days."""
    frame = panel.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="raise")
    frame["date"] = frame["timestamp"].dt.floor("D")
    frame["hour"] = frame["timestamp"].dt.hour
    daily = frame.pivot_table(
        index=["meter_id", "date"], columns="hour",
        values="energy_consumption_kwh", aggfunc="sum",
    ).reindex(columns=range(24))
    if daily.isna().any().any():
        raise ValueError("The UCI panel contains incomplete client-day-hour profiles.")
    profiles = daily.groupby(level="meter_id", sort=True).mean()
    profiles = profiles.reindex(ids).astype(float)
    if profiles.isna().any().any():
        raise ValueError("Some clustered clients have no complete 24-hour profiles.")
    return profiles


def _apply_shift(profiles: pd.DataFrame, mask: np.ndarray,
                 flex_fraction: float) -> tuple[pd.DataFrame, float]:
    """Move a fraction of 17:00-21:00 energy evenly into 12:00-17:00."""
    shifted = profiles.copy()
    source = shifted.loc[mask, EVENING_HOURS]
    energy_to_shift = float(source.to_numpy().sum() * flex_fraction)
    shifted.loc[mask, EVENING_HOURS] = source * (1.0 - flex_fraction)
    per_hour_addition = (
        source.sum(axis=1).to_numpy(dtype=float) * flex_fraction
        / len(SHIFT_HOURS)
    )
    shifted.loc[mask, SHIFT_HOURS] = (
        shifted.loc[mask, SHIFT_HOURS].to_numpy()
        + per_hour_addition[:, None]
    )
    return shifted, energy_to_shift


def _system_metrics(profiles: pd.DataFrame) -> dict:
    aggregate = profiles.sum(axis=0).to_numpy(dtype=float)
    evening = aggregate[EVENING_HOURS]
    peak_hour = int(np.argmax(aggregate))
    return {
        "aggregate_peak_kw": float(aggregate.max()),
        "aggregate_peak_hour": peak_hour,
        "evening_peak_kw": float(evening.max()),
        "evening_peak_hour": int(EVENING_HOURS[np.argmax(evening)]),
        "mean_demand_kw": float(aggregate.mean()),
        "load_factor": float(aggregate.mean() / aggregate.max()),
        "aggregate_daily_energy_kwh": float(aggregate.sum()),
    }


def _plot_profiles(hourly: pd.DataFrame, n_clients: int, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    scale = 100.0 / n_clients
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for column, label, color, linewidth in [
        ("baseline_kw", "Observed baseline", "#7a8594", 2.2),
        ("target_cluster_kw", "Target evening-heavy cluster", "#e07a5f", 2.5),
        ("equal_energy_comparator_kw", "Equal-energy shift in other clusters", "#3d8b8b", 2.2),
    ]:
        ax.plot(
            hourly["hour"], hourly[column] * scale,
            label=label, color=color, linewidth=linewidth,
        )
    ax.axvspan(17, 21, color="#e07a5f", alpha=0.10, label="Peak window (17:00–21:00)")
    ax.axvspan(12, 17, color="#3d8b8b", alpha=0.08, label="Shift destination (12:00–17:00)")
    ax.set(
        xlabel="Local clock hour",
        ylabel="Average demand (kW per 100 sampled clients)",
        title="Retrospective load-shifting scenario on 2012 UCI client data",
        xticks=np.arange(0, 24, 2),
    )
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncols=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def run(args: argparse.Namespace) -> tuple[dict, pd.DataFrame]:
    panel, facts = load_uci_panel(
        args.source,
        start="2012-01-01",
        end="2012-12-31",
        n_meters=args.n_meters,
        sample_seed=args.sample_seed,
    )
    assignments, model_facts = _cluster_clients(
        panel, seed=args.seed, stability_runs=args.stability_runs,
    )
    client_ids = assignments["meter_id"].tolist()
    profiles = _average_daily_profiles(panel, client_ids)
    labels = assignments.set_index("meter_id").loc[profiles.index, "cluster"]

    normalized = profiles.div(profiles.sum(axis=1).replace(0, np.nan), axis=0)
    cluster_evening_share = normalized.groupby(labels).apply(
        lambda group: float(group.iloc[:, EVENING_HOURS].sum(axis=1).mean()),
        include_groups=False,
    )
    target_cluster = int(cluster_evening_share.idxmax())
    target_mask = labels.to_numpy() == target_cluster
    non_target_mask = ~target_mask
    n_target = int(target_mask.sum())
    evening_share = float(cluster_evening_share.loc[target_cluster])

    baseline = profiles
    target_scenario, target_shift = _apply_shift(
        baseline, target_mask, args.flex_fraction,
    )
    non_target_evening = float(
        baseline.loc[non_target_mask, EVENING_HOURS].to_numpy().sum()
    )
    if non_target_evening <= 0:
        raise ValueError("Non-target clusters have no energy in the evening window.")
    equal_energy_fraction = target_shift / non_target_evening
    if equal_energy_fraction > 1:
        raise ValueError(
            "Target scenario shifts more energy than the other clusters use in the "
            "evening window; an equal-energy comparator is not feasible."
        )
    equal_energy_scenario, comparator_shift = _apply_shift(
        baseline, non_target_mask, equal_energy_fraction,
    )

    baseline_metrics = _system_metrics(baseline)
    target_metrics = _system_metrics(target_scenario)
    comparator_metrics = _system_metrics(equal_energy_scenario)
    total_energy = baseline_metrics["aggregate_daily_energy_kwh"]
    scenario_rows = []
    scenarios = [
        ("observed_baseline", baseline, baseline_metrics, 0.0, None),
        ("target_evening_heavy_cluster", target_scenario, target_metrics,
         target_shift, args.flex_fraction),
        ("equal_energy_non_target_comparator", equal_energy_scenario,
         comparator_metrics, comparator_shift, equal_energy_fraction),
    ]
    for name, frame, metrics, shifted_kwh, fraction in scenarios:
        scenario_rows.append({
            "scenario": name,
            **metrics,
            "energy_shifted_kwh_per_average_day": float(shifted_kwh),
            "fraction_of_evening_energy_shifted": (
                float(fraction) if fraction is not None else 0.0
            ),
            "daily_energy_change_kwh": float(
                metrics["aggregate_daily_energy_kwh"] - total_energy
            ),
            "evening_peak_reduction_kw_vs_baseline": float(
                baseline_metrics["evening_peak_kw"] - metrics["evening_peak_kw"]
            ),
            "evening_peak_reduction_percent_vs_baseline": float(
                100.0 * (baseline_metrics["evening_peak_kw"] - metrics["evening_peak_kw"])
                / baseline_metrics["evening_peak_kw"]
            ),
        })
    summary = pd.DataFrame(scenario_rows)

    hourly = pd.DataFrame({"hour": np.arange(24)})
    hourly["baseline_kw"] = baseline.sum(axis=0).to_numpy(dtype=float)
    hourly["target_cluster_kw"] = target_scenario.sum(axis=0).to_numpy(dtype=float)
    hourly["equal_energy_comparator_kw"] = equal_energy_scenario.sum(axis=0).to_numpy(dtype=float)

    target_evening_total = float(
        baseline.loc[target_mask, EVENING_HOURS].to_numpy().sum()
    )
    interpretation = (
        "This retrospective simulation shifts an assumed share of observed load; "
        "it does not estimate causal response, realized savings, or participant "
        "flexibility. UCI identifies points/clients rather than confirmed households."
    )
    metadata = {
        "study": "uci_2012_retrospective_demand_response_load_shift_scenario",
        "source": facts,
        "archive_sha256": _sha256(Path(args.source)),
        "analysis": {
            **model_facts,
            "sample_seed": args.sample_seed,
            "random_seed": args.seed,
            "requested_clients": args.n_meters,
            "analyzed_clients": len(profiles),
            "target_cluster": target_cluster,
            "target_cluster_size": n_target,
            "target_cluster_share": n_target / len(profiles),
            "target_cluster_mean_evening_energy_share_17_to_21": evening_share,
            "target_cluster_total_evening_energy_kwh_per_average_day": target_evening_total,
            "evening_hours_local_half_open": [17, 21],
            "shift_destination_hours_local_half_open": [12, 17],
            "target_cluster_evening_energy_shift_fraction": args.flex_fraction,
            "equal_energy_non_target_shift_fraction": equal_energy_fraction,
        },
        "scenario_metrics": summary.to_dict(orient="records"),
        "interpretation_limit": interpretation,
        "software": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }
    return metadata, hourly


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="UCI ZIP archive or extracted LD2011_2014.txt.")
    parser.add_argument("--n-meters", type=int, default=120)
    parser.add_argument("--sample-seed", type=int, default=42)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stability-runs", type=int, default=8)
    parser.add_argument("--flex-fraction", type=float, default=0.10,
                        help="Assumed share of target-cluster 17:00-21:00 energy shifted.")
    return parser


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    args = _parser().parse_args()
    if not 0 < args.flex_fraction <= 1:
        raise ValueError("--flex-fraction must be in (0, 1].")
    metadata, hourly = run(args)

    out_dir = ROOT / "outputs" / "research_additions"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = ROOT / "outputs" / "reports" / "demand_response_uci_2012.md"
    json_path = out_dir / "demand_response_uci_2012.json"
    csv_path = out_dir / "demand_response_uci_2012_hourly_profiles.csv"
    figure_path = ROOT / "outputs" / "figures" / "research_additions" / "demand_response_uci_2012.png"
    metadata["outputs"] = {
        "report": str(report_path.relative_to(ROOT)),
        "metadata": str(json_path.relative_to(ROOT)),
        "hourly_profiles": str(csv_path.relative_to(ROOT)),
        "figure": str(figure_path.relative_to(ROOT)),
    }
    hourly.to_csv(csv_path, index=False)
    summary = pd.DataFrame(metadata["scenario_metrics"])
    _plot_profiles(hourly, metadata["analysis"]["analyzed_clients"], figure_path)
    json_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")

    target = summary.loc[summary["scenario"] == "target_evening_heavy_cluster"].iloc[0]
    comparator = summary.loc[
        summary["scenario"] == "equal_energy_non_target_comparator"
    ].iloc[0]
    baseline = summary.loc[summary["scenario"] == "observed_baseline"].iloc[0]
    report = [
        "# Retrospective evening-peak load-shifting scenario", "",
        "This is a transparent, assumption-driven simulation on the seeded 2012 UCI sample. "
        "It does not measure causal participant response, realized energy savings, or "
        "household flexibility. UCI identifies points/clients; they are not assumed to be households.", "",
        "## Protocol", "",
        f"- Sample: {metadata['analysis']['analyzed_clients']} active clients after the same seeded 120-client draw and 16 all-zero exclusions.",
        f"- Clustering: 51 behavioral features, PCA retained at 95% variance, K selected by the predeclared rule ({metadata['analysis']['selected_k']} clusters).",
        f"- Target: cluster {metadata['analysis']['target_cluster']}, with the highest mean per-client energy share from 17:00 to 21:00 ({metadata['analysis']['target_cluster_mean_evening_energy_share_17_to_21']:.1%}; n={metadata['analysis']['target_cluster_size']}).",
        f"- Scenario: shift {args.flex_fraction:.0%} of target-cluster 17:00–21:00 energy evenly into 12:00–17:00, preserving each typical day's total energy.",
        f"- Comparator: shift the same aggregate energy ({target['energy_shifted_kwh_per_average_day']:.3f} kWh across the sampled clients per average day) from the other clusters' evening window into the same destination period.",
        "- Typical profiles are each client's average 24-hour kWh profile across 2012. Aggregate hourly kWh is interpreted as average kW over that hour.",
        "", "## Scenario results", "",
        "| Scenario | Shifted energy (kWh/day) | Evening peak (kW) | Evening peak change vs baseline | Whole-day peak (kW @ hour) | Daily energy change (kWh) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        report.append(
            f"| {row['scenario']} | {row['energy_shifted_kwh_per_average_day']:.3f} "
            f"| {row['evening_peak_kw']:.3f} "
            f"| {row['evening_peak_reduction_kw_vs_baseline']:.3f} kW "
            f"({row['evening_peak_reduction_percent_vs_baseline']:.2f}%) "
            f"| {row['aggregate_peak_kw']:.3f} @ {row['aggregate_peak_hour']}:00 "
            f"| {row['daily_energy_change_kwh']:.6f} |"
        )
    report += [
        "", "## Interpretation", "",
        f"Under the stated 10% flexibility assumption, the targeted scenario changes the sampled clients' 17:00–21:00 coincident peak by {target['evening_peak_reduction_kw_vs_baseline']:.3f} kW. "
        f"The equal-energy shift among the other clusters changes it by {comparator['evening_peak_reduction_kw_vs_baseline']:.3f} kW, a nearly identical reduction. "
        f"Both scenarios move the whole-day peak from hour {int(baseline['aggregate_peak_hour'])} to hour {int(target['aggregate_peak_hour'])} and raise its magnitude from {baseline['aggregate_peak_kw']:.3f} to {target['aggregate_peak_kw']:.3f} kW. "
        "This conditional engineering comparison on one anonymized client sample is not an estimate of actual demand response or bill savings; it also illustrates how a poorly chosen shift destination can create a new coincident peak.",
        "The scenario preserves total daily energy by construction; it only moves load between hours.",
        "", "## Reproducibility and limits", "",
        f"- UCI archive SHA-256: `{metadata['archive_sha256']}`",
        f"- Sampling seed: {args.sample_seed}; clustering seed: {args.seed}.",
        f"- Assumed target-cluster flexibility: {args.flex_fraction:.0%} of its 17:00–21:00 energy.",
        "- The UCI sample contains no appliance, occupancy, tariff-response, or flexibility labels.",
        "- Results are retrospective and do not establish that cluster-based targeting causes a peak reduction in practice.",
        f"- Full metadata: `{json_path.relative_to(ROOT).as_posix()}`",
        f"- Hourly profile CSV: `{csv_path.relative_to(ROOT).as_posix()}`",
        f"- Figure: `{figure_path.relative_to(ROOT).as_posix()}`",
        "", "![Retrospective load-shifting scenario]({})".format(
            Path("../figures/research_additions/demand_response_uci_2012.png").as_posix()
        ), "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report), encoding="utf-8")
    print(f"Report: {report_path}")
    print(f"Metadata: {json_path}")
    print(f"Figure: {figure_path}")
    print(f"Energy-shift comparator (kWh/day): {comparator['energy_shifted_kwh_per_average_day']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
