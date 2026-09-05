"""
Real-world model evaluation (Improvement 3, validation layer).

Real consumption data has no ground-truth archetype, so a real-world result must
never be graded with ARI/NMI against invented groups, as that would be
reporting a score the data could not have produced. This module instead evaluates the
recovered clustering with the evidence the data *does* give:

- internal quality: silhouette, Calinski-Harabasz, Davies-Bouldin (the same
  indices the K-selection rule already computes),
- seed stability: does the same K reappear across K-Means random restarts
  (mean pairwise ARI over restarts; ARI *within* the algorithm's own restarts,
  not against any label),
- temporal stability: does the segmentation persist when the model is refit on
  earlier vs later slices of the same meters (a real-world analogue of
  reproducibility that synthetic data cannot test), and
- interpretability: are the clusters compact, balanced, and describable in
  real units against the population.

Together these answer "is this a stable, interpretable partition of real load
shapes?", the question real-world validation can legitimately ask. It never
answers "did we recover the truth?", because no real dataset provides it.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from clustering import (
    find_optimal_k,
    measure_cluster_stability,
    perform_kmeans,
    select_optimal_k,
)
from feature_engineering import engineer_all_features, select_features
from pca_analysis import run_pca_pipeline
from preprocessing import preprocess_pipeline
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# how the real branch chooses K (same rule as the synthetic branch)
DEFAULT_K_RANGE = (2, 8)
DEFAULT_STABILITY_RUNS = 8
TEMPORAL_SPLITS = 3            # number of equal time windows for temporal stability


@dataclass
class RealWorldReport:
    """The full result of a real-world study, for reporting.

    Holds no class labels and never references an archetype: there is none here.
    """

    source_name: str
    ingestion_facts: dict = field(default_factory=dict)
    n_meters: int = 0
    n_records: int = 0
    feature_names: list = field(default_factory=list)
    n_pca_components: int = 0
    pca_cumulative_variance: float = float("nan")
    k_values: list = field(default_factory=list)
    optimal_k: int = 0
    silhouette_by_k: dict = field(default_factory=dict)
    ch_by_k: dict = field(default_factory=dict)
    db_by_k: dict = field(default_factory=dict)
    inertia_by_k: dict = field(default_factory=dict)
    stability_by_k: dict = field(default_factory=dict)
    selection_trace: dict = field(default_factory=dict)
    seed_stability_at_k: dict = field(default_factory=dict)
    temporal_stability_at_k: dict = field(default_factory=dict)
    cluster_profiles: pd.DataFrame = field(default_factory=pd.DataFrame)
    population_baseline: dict = field(default_factory=dict)
    cluster_size_shares: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def internal_scores(self) -> dict:
        k = self.optimal_k
        return {
            "K": k,
            "silhouette": self.silhouette_by_k.get(k),
            "calinski_harabasz": self.ch_by_k.get(k),
            "davies_bouldin": self.db_by_k.get(k),
            "seed_stability_mean_ari": self.seed_stability_at_k.get(k, {}).get("mean_ari"),
        }

    def markdown(self) -> str:
        """A self-contained report for the real-world pathway."""
        k = self.optimal_k
        lines = []
        lines.append(f"# Real-world validation report: {self.source_name}")
        lines.append("")
        lines.append("_No ARI/NMI is reported here: real data has no ground-truth "
                     "archetype. Scores are internal quality + restart stability + "
                     "temporal stability only._")
        lines.append("")
        lines.append(f"- Meters: {self.n_meters}")
        lines.append(f"- Records (meter-hours): {self.n_records:,}")
        lines.append(f"- Features per meter: {len(self.feature_names)}")
        lines.append(f"- PCA components kept: {self.n_pca_components} "
                     f"({self.pca_cumulative_variance:.1%} variance)")
        lines.append(f"- K selected: {k}  (candidates {min(self.k_values)}-{max(self.k_values)})")
        lines.append("")
        lines.append("## Internal quality (higher silhouette / CH is better; lower DB is better)")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Silhouette @ K={k} | {self.silhouette_by_k.get(k):.4f} |")
        lines.append(f"| Calinski-Harabasz @ K={k} | {self.ch_by_k.get(k):.1f} |")
        lines.append(f"| Davies-Bouldin @ K={k} | {self.db_by_k.get(k):.4f} |")
        lines.append("")
        lines.append("## Restart stability (mean pairwise ARI over K-Means seeds @ K)")
        lines.append("")
        lines.append(f"- Seed-stability ARI: {self.seed_stability_at_k.get(k, {}).get('mean_ari', float('nan')):.4f}"
                     f" (1.0 = identical partition every restart)")
        ts = self.temporal_stability_at_k.get(k, {})
        lines.append(f"- Temporal stability (partitions across {TEMPORAL_SPLITS} time "
                     f"windows): mean pairwise ARI {ts.get('mean_ari', float('nan')):.4f}")
        lines.append("")
        lines.append("## Cluster interpretability")
        lines.append("")
        lines.append("| Cluster | Share | Peak hour | Evening share |"
                     " Peak-to-avg | CV | Weekend ratio |")
        lines.append("|---------:|------:|----------:|--------------:|-----------:|----:|--------------:|")
        for _, prof in self.cluster_profiles.sort_values("cluster").iterrows():
            peak = prof.get("peak_hour")
            peak_txt = f"{int(peak):02d}:00" if pd.notna(peak) else "-"
            lines.append(
                f"| {int(prof['cluster'])} | {prof.get('size_share', 0):.0%} |"
                f" {peak_txt} |"
                f" {prof.get('evening_share', 0) if pd.notna(prof.get('evening_share')) else float('nan'):.0%} |"
                f" {prof.get('peak_to_avg_ratio', 0) if pd.notna(prof.get('peak_to_avg_ratio')) else float('nan'):.2f} |"
                f" {prof.get('coefficient_of_variation', 0) if pd.notna(prof.get('coefficient_of_variation')) else float('nan'):.2f} |"
                f" {prof.get('weekend_ratio', 0) if pd.notna(prof.get('weekend_ratio')) else float('nan'):.2f} |"
            )
        lines.append("")
        if self.warnings:
            lines.append("## Warnings")
            for w in self.warnings:
                lines.append(f"- {w}")
            lines.append("")
        return "\n".join(lines)


def _profile_clusters(preprocessed: pd.DataFrame, labels: np.ndarray,
                      k: int) -> tuple[pd.DataFrame, dict]:
    """Per-cluster descriptive profile in real units, against population.

    Features that are undefined for a source (e.g. no weekends in the window, or a
    feature dropped as constant) are reported as NaN rather than crashing the report,
    since a real dataset has no guarantee that every behavioural feature is defined.
    """
    feats = engineer_all_features(preprocessed, feature_set="behavioral")
    feats = feats.reset_index(drop=True)
    if "consumer_id" in feats.columns:
        feats = feats.sort_values("consumer_id").reset_index(drop=True)
    feats["_cluster"] = labels

    # Peak hour derived from the normalized 24h shape (always present), rather
    # than from a single timing feature that may have been dropped as constant.
    shape_cols = [f"hour_{h}_shape" for h in range(24)]
    if all(c in feats.columns for c in shape_cols):
        feats["_peak_hour"] = feats[shape_cols].values.argmax(axis=1)

    def _mean(frame: pd.DataFrame, col: str) -> float:
        """Mean of a column, or NaN if the source lacks the feature entirely."""
        return float(frame[col].mean()) if col in frame.columns else float("nan")

    profile_cols = ["evening_share", "afternoon_share", "morning_share", "night_share",
                    "peak_to_avg_ratio", "coefficient_of_variation", "weekend_ratio"]
    baseline = {col: _mean(feats, col) for col in profile_cols}

    rows = []
    for c in range(k):
        sub = feats[feats["_cluster"] == c]
        rows.append({
            "cluster": c,
            "size": int(len(sub)),
            "size_share": float(len(sub)) / len(feats),
            "peak_hour": (_mean(sub, "_peak_hour") if "_peak_hour" in sub.columns
                          else float("nan")),
            **{col: _mean(sub, col) for col in profile_cols},
        })
    profiles = pd.DataFrame(rows)
    for c in range(k):
        share = profiles.loc[profiles["cluster"] == c, "size_share"].iloc[0]
        if share < 0.05:
            logger.warning("Real cluster %d holds %.0f%% of meters (<5%%); flag it.", c, share * 100)
    return profiles, baseline


def temporal_stability(preprocessed: pd.DataFrame, features: pd.DataFrame,
                       k: int, random_state: int, trace: dict) -> dict:
    """Refit K-Means on each of a few equal time windows and compare partitions.

    The synthetic branch cannot do this (its archetypes are static); here it is
    the natural reproducibility check: does the same segmentation reappear when
    the model is rebuilt on earlier vs later months of the same meters?
    """
    preprocessed = preprocessed.copy()
    preprocessed["timestamp"] = pd.to_datetime(preprocessed["timestamp"])
    # Split on the TIME domain, not on row index. The panel is sorted by
    # (consumer_id, timestamp), so a row-index split would slice different
    # consumers into different windows and measure nothing about time at all.
    # Splitting timestamps keeps every meter in every window and makes each
    # window a different time interval over the SAME meters, the actual
    # question ("does the segmentation persist across earlier vs later time?").
    times = preprocessed["timestamp"]
    t_start, t_end = times.min(), times.max()
    if t_start >= t_end:
        return {"mean_ari": float("nan"), "windows": 0, "note": "single timestamp, cannot split time"}
    edges = [t_start + (t_end - t_start) * (i / TEMPORAL_SPLITS)
             for i in range(TEMPORAL_SPLITS + 1)]
    windows = [
        preprocessed[(times >= edges[i]) & (times < edges[i + 1])].copy()
        for i in range(len(edges) - 1)
    ]
    valid = [w for w in windows if len(w) > 0]

    all_labels = []
    for w in valid:
        wf = engineer_all_features(w, feature_set="behavioral").reset_index(drop=True)
        if len(wf) < 2 or "consumer_id" not in wf.columns:
            continue
        wf = wf.sort_values("consumer_id")
        sel = select_features(wf, feature_group="behavioral")
        if sel.shape[1] < 3:            # consumer_id + at least two features
            continue
        # Inline scale + PCA (no disk writes): the temporal check only needs a
        # low-dimensional score matrix, not the pipeline's figures and models.
        numeric = sel.drop(columns=["consumer_id"]).select_dtypes("number")
        _num = numeric.fillna(numeric.median()) if numeric.isnull().any().any() else numeric
        Xw = PCA(n_components=min(numeric.shape[1], 6)).fit_transform(
            StandardScaler().fit_transform(_num)
        )
        if Xw.shape[1] < 2:
            continue
        _m, lab = perform_kmeans(Xw, k, random_state)
        all_labels.append(lab)

    if len(all_labels) < 2:
        return {"mean_ari": float("nan"), "windows": len(all_labels), "note": "too few valid windows"}
    ari = []
    for i in range(len(all_labels)):
        for j in range(i + 1, len(all_labels)):
            ari.append(adjusted_rand_score(all_labels[i], all_labels[j]))
    return {"mean_ari": float(np.mean(ari)), "std_ari": float(np.std(ari)),
            "windows": len(all_labels), "n_pairs": len(ari)}


def run_real_world_study(panel: pd.DataFrame, facts: dict,
                         feature_names: Optional[list] = None,
                         k_range: tuple = DEFAULT_K_RANGE,
                         random_state: int = 42,
                         stability_runs: int = DEFAULT_STABILITY_RUNS,
                         profile: bool = True) -> RealWorldReport:
    """Run the real-world validation pathway end to end.

    Args:
        panel: The validated long panel from :func:`realworld_ingest.ingest`.
        facts: The ingestion facts dict from the same call.
        feature_names: Optional subset of features to use (a *behavioral* subset
            is recommended so the real study shares the synthetic branch's
            shape-not-size premise).
        k_range: Candidate K range (half-open min, max).
        random_state: Seed for all fits.
        stability_runs: Restarts per K for seed stability.
        profile: Whether to build the interpretable cluster profile (slower).

    Returns:
        A RealWorldReport ready to render to markdown.
    """
    # 1. preprocess (reuses the same within-meter imputation as the synthetic path)
    #    The ingested panel uses 'meter_id'; the shared pipeline groups on
    #    'consumer_id' for within-meter imputation, so rename before cleaning.
    if "meter_id" in panel.columns and "consumer_id" not in panel.columns:
        panel = panel.rename(columns={"meter_id": "consumer_id"})
    preprocessed = preprocess_pipeline(panel)

    n_consumers = int(preprocessed["consumer_id"].nunique())
    if n_consumers < k_range[1]:
        raise ValueError(
            f"Real-world clustering needs at least {k_range[1]} meters to evaluate "
            f"K up to {k_range[1] - 1}; this source has {n_consumers}. "
            f"Single-house sources (e.g. the UCI archive) describe one consumer "
            f"and cannot be clustered; use a multi-meter dataset, or raise "
            f"k_range for a larger source."
        )

    # 2. features
    feats_all = engineer_all_features(preprocessed, feature_set="behavioral")
    feats_all = feats_all.reset_index(drop=True).sort_values("consumer_id")
    if feature_names:
        # Keep only the requested behavioural subset that actually exist.
        present = [c for c in feature_names if c in feats_all.columns and c != "consumer_id"]
        feats = feats_all[["consumer_id"] + present].copy()
    else:
        feats = feats_all.copy()

    # 3. scale + PCA
    # The real-world study keeps its own figures/models/tables under a
    # real_world/ subtree instead of the shared outputs/metrics + models paths,
    # so a real-world run can never overwrite the synthetic branch's committed
    # artifact contract (the exporter reads those shared paths against the
    # synthetic run's metadata).
    X_pca, pca, _scaler, n_components = run_pca_pipeline(
        feats,
        output_dir='outputs/figures/real_world',
        model_dir='outputs/real_world/models',
        metrics_dir='outputs/metrics/real_world',
    )

    # 4. clustering with the shared K-selection rule
    k_values, inertia, silhouette, ch, db, stability = find_optimal_k(
        X_pca, k_range, random_state, stability_runs=stability_runs)
    optimal_k, trace = select_optimal_k(
        k_values, inertia, silhouette, ch, db, stability_by_k=stability)

    report = RealWorldReport(
        source_name=facts.get("source_name", "real_world"),
        ingestion_facts=facts,
        n_meters=facts.get("meters", panel["consumer_id"].nunique()),
        n_records=len(panel),
        feature_names=[c for c in feats.columns if c != "consumer_id"],
        n_pca_components=n_components,
        pca_cumulative_variance=float(np.cumsum(pca.explained_variance_ratio_)[n_components - 1]),
        k_values=k_values,
        optimal_k=optimal_k,
        silhouette_by_k=silhouette,
        ch_by_k=ch,
        db_by_k=db,
        inertia_by_k=inertia,
        stability_by_k=stability,
        selection_trace=trace,
    )

    # 5. seed stability at the chosen K (restart reproducibility)
    report.seed_stability_at_k = {optimal_k:
        measure_cluster_stability(X_pca, optimal_k, stability_runs, random_state)}

    # 6. temporal stability across time windows
    report.temporal_stability_at_k = {optimal_k:
        temporal_stability(preprocessed, feats, optimal_k, random_state, trace)}

    # 7. cluster profile (interpretability in real units)
    if profile:
        _, labels = perform_kmeans(X_pca, optimal_k, random_state)
        report.cluster_profiles, report.population_baseline = _profile_clusters(
            preprocessed, labels, optimal_k)
        report.cluster_size_shares = (np.bincount(labels, minlength=optimal_k) / len(labels)).tolist()

    # 8. warnings from the selection rule and any tiny clusters
    report.warnings = list(trace.get("relaxed_filters", []))
    small = [s for s in report.cluster_size_shares if s < 0.05]
    if small:
        report.warnings.append(f"Cluster(s) hold <5% of meters: {[round(s, 3) for s in small]}")

    logger.info(
        "Real-world study '%s': K=%d, silhouette=%.4f, seed-ARI=%.4f, temporal-ARI=%.4f",
        report.source_name, optimal_k,
        report.silhouette_by_k.get(optimal_k, float("nan")),
        report.seed_stability_at_k[optimal_k].get("mean_ari", float("nan")),
        report.temporal_stability_at_k[optimal_k].get("mean_ari", float("nan")),
    )
    return report


def write_report(report: RealWorldReport, out_path: Optional[str] = None) -> str:
    """Write the report to markdown and return the text.

    Args:
        report: A RealWorldReport.
        out_path: Where to write the .md. Defaults to outputs/reports/.

    Returns:
        The markdown text.
    """
    if out_path is None:
        out_path = f"outputs/reports/real_world_{report.source_name}.md"
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = report.markdown()
    path.write_text(text, encoding="utf-8")
    logger.info("Wrote real-world report to %s", path)
    return text