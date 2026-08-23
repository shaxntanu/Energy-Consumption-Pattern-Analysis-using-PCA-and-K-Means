"""Chart factory for the Streamlit dashboard.

Every figure the dashboard draws is built here, so the visual language lives in
one place and the page code stays a sequence of calls. Each function takes the
single AnalysisResults object and returns a styled Plotly figure; nothing here
computes a result, it only shapes numbers the pipeline already produced.

Two conventions hold throughout:

- Any figure whose x-axis is the hour of the day gets the four faint
  time-of-day bands behind it (the project's signature), via dashboard_ui.
- Cluster identity is colour *and* the cluster's name, never colour alone.

The helpers that read cluster_shapes and pca_loadings are deliberately defensive
about whether the cluster label or feature name arrives as a column or as the
index, so the module does not care which way the pipeline handed the frame over.
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go

import dashboard_ui as ui

HOURS = list(range(24))


# --- shared parsing ----------------------------------------------------------

def _shape_matrix(results) -> tuple[pd.DataFrame, list]:
    """Return cluster_shapes indexed by string cluster label, plus the ordered
    list of hour columns. Works whether 'cluster' is a column or the index."""
    df = results.cluster_shapes.copy()
    if "cluster" in df.columns:
        df = df.set_index("cluster")
    df.index = df.index.map(str)
    hour_cols = [c for c in df.columns if str(c).lstrip("-").isdigit()]
    hour_cols = sorted(hour_cols, key=lambda c: int(str(c)))
    return df, hour_cols


def _population_shape(results, df: pd.DataFrame, hour_cols: list) -> np.ndarray:
    """The population's mean day, from the population row if present, otherwise
    the size-weighted average of the cluster shapes."""
    if "population" in df.index:
        return df.loc["population", hour_cols].astype(float).to_numpy()
    profiles = results.cluster_profiles
    weights = profiles.set_index(profiles["cluster"].map(str))["size"]
    rows, ws = [], []
    for cid in weights.index:
        if cid in df.index:
            rows.append(df.loc[cid, hour_cols].astype(float).to_numpy())
            ws.append(float(weights.loc[cid]))
    stacked = np.vstack(rows)
    return np.average(stacked, axis=0, weights=ws)


def _cluster_rows(results, df: pd.DataFrame, hour_cols: list):
    """Yield (cluster_id, name, colour, 24-value array) in cluster-ID order."""
    for _, prof in results.cluster_profiles.sort_values("cluster").iterrows():
        cid = int(prof["cluster"])
        key = str(cid)
        if key not in df.index:
            continue
        yield (cid, str(prof["cluster_name"]), ui.cluster_color(cid),
               df.loc[key, hour_cols].astype(float).to_numpy())


def _loadings(results) -> pd.DataFrame:
    """pca_loadings indexed by feature name, columns PC1.. ."""
    df = results.pca_loadings.copy()
    if "feature" in df.columns:
        df = df.set_index("feature")
    return df


def _day_ramp_colorscale() -> list:
    return [[pos, col] for pos, col in ui.DAY_RAMP]


# --- the signature: cluster load shapes --------------------------------------

def load_shape_chart(results) -> go.Figure:
    """The signature figure. Each cluster's mean normalised day as a line in its
    own colour, the population average dashed behind, over the day-part bands."""
    df, hour_cols = _shape_matrix(results)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=HOURS, y=_population_shape(results, df, hour_cols),
        name="Population", mode="lines",
        line=dict(color=ui.SLATE, width=1.6, dash="dot"), hoverinfo="skip",
    ))
    for cid, name, color, vals in _cluster_rows(results, df, hour_cols):
        fig.add_trace(go.Scatter(
            x=HOURS, y=vals, name=name, mode="lines",
            line=dict(color=color, width=2.8, shape="spline", smoothing=0.6),
            hovertemplate=f"{name}<br>%{{x}}:00 &middot; %{{y:.3f}} of daily energy<extra></extra>",
        ))
    ui.add_time_of_day_bands(fig)
    fig.update_layout(
        title="Mean load shape by cluster",
        xaxis=dict(title="Hour of day", tickmode="array", tickvals=[0, 6, 12, 18, 23], range=[0, 23]),
        yaxis=dict(title="Share of daily energy", tickformat=".0%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=460,
    )
    return fig


def cluster_shape_mini(results, cluster_id: int) -> go.Figure:
    """A small single-cluster curve against the population, for a card."""
    df, hour_cols = _shape_matrix(results)
    color = ui.cluster_color(cluster_id)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=HOURS, y=_population_shape(results, df, hour_cols),
                             mode="lines", line=dict(color=ui.SLATE, width=1.2, dash="dot"),
                             hoverinfo="skip", showlegend=False))
    if str(cluster_id) in df.index:
        fig.add_trace(go.Scatter(x=HOURS, y=df.loc[str(cluster_id), hour_cols].astype(float),
                                 mode="lines", line=dict(color=color, width=2.6, shape="spline"),
                                 hoverinfo="skip", showlegend=False))
    ui.add_time_of_day_bands(fig)
    fig.update_layout(height=150, margin=dict(l=8, r=8, t=8, b=20),
                      xaxis=dict(showticklabels=False, range=[0, 23]),
                      yaxis=dict(showticklabels=False))
    return fig


def hour_by_cluster_heatmap(results) -> go.Figure:
    """Clusters against hours, coloured by share of daily energy. Shows at a
    glance where each cluster's day is heaviest."""
    df, hour_cols = _shape_matrix(results)
    rows = list(_cluster_rows(results, df, hour_cols))
    z = [vals for _, _, _, vals in rows]
    names = [name for _, name, _, _ in rows]
    fig = go.Figure(go.Heatmap(
        z=z, x=HOURS, y=names, colorscale=_day_ramp_colorscale(),
        colorbar=dict(title="share", tickformat=".0%"),
        hovertemplate="%{y}<br>%{x}:00 &middot; %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title="Where each cluster's day is heaviest",
        xaxis=dict(title="Hour of day", tickvals=[0, 6, 12, 18, 23]),
        yaxis=dict(title=""), height=280,
    )
    return fig


# --- PCA ---------------------------------------------------------------------

def pca_variance_chart(results) -> go.Figure:
    """Per-component and cumulative explained variance, with the retention line."""
    evr = results.pca_model.explained_variance_ratio_
    xs = list(range(1, len(evr) + 1))
    cum = np.cumsum(evr)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=evr, name="Per component", marker_color=ui.CYAN_DEEP))
    fig.add_trace(go.Scatter(x=xs, y=cum, name="Cumulative", mode="lines+markers",
                             line=dict(color=ui.CYAN, width=2.4)))
    fig.add_hline(y=results.config.pca_variance_threshold, line_dash="dash", line_color=ui.GREEN,
                  annotation_text=f"{results.config.pca_variance_threshold:.0%} target",
                  annotation_font_color=ui.GREEN)
    fig.add_vline(x=results.n_pca_components, line_dash="dot", line_color=ui.MIST,
                  annotation_text=f"{results.n_pca_components} kept", annotation_font_color=ui.MIST)
    fig.update_layout(title="Explained variance", xaxis_title="Principal component",
                      yaxis=dict(title="Variance", tickformat=".0%"), height=380,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return fig


def pca_projection_chart(results, color_by_cluster: bool = True) -> go.Figure:
    """Consumers in the plane of the first two components."""
    xp = results.pca_transformed
    fig = go.Figure()
    if color_by_cluster:
        for _, prof in results.cluster_profiles.sort_values("cluster").iterrows():
            cid = int(prof["cluster"])
            mask = results.cluster_labels == cid
            fig.add_trace(go.Scatter(
                x=xp[mask, 0], y=xp[mask, 1], mode="markers", name=str(prof["cluster_name"]),
                marker=dict(color=ui.cluster_color(cid), size=7, opacity=0.75,
                            line=dict(width=0.5, color=ui.MIDNIGHT)),
            ))
    else:
        fig.add_trace(go.Scatter(x=xp[:, 0], y=xp[:, 1], mode="markers",
                                 marker=dict(color=ui.CYAN, size=7, opacity=0.6), showlegend=False))
    fig.update_layout(title="Consumers in the first two components",
                      xaxis_title="PC1", yaxis_title="PC2", height=460,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return fig


def pca_loadings_chart(results, pc: str = "PC1", top_n: int = 12) -> go.Figure:
    """The features that most define one component, positive and negative."""
    loadings = _loadings(results)
    if pc not in loadings.columns:
        pc = loadings.columns[0]
    series = loadings[pc].sort_values()
    picked = pd.concat([series.head(top_n // 2), series.tail(top_n // 2)])
    colors = [ui.ROSE if v < 0 else ui.CYAN for v in picked.values]
    fig = go.Figure(go.Bar(x=picked.values, y=list(picked.index), orientation="h",
                           marker_color=colors,
                           hovertemplate="%{y}<br>%{x:.2f}<extra></extra>"))
    fig.update_layout(title=f"What {pc} is made of", xaxis_title="Loading",
                      yaxis=dict(title=""), height=460, margin=dict(l=200))
    return fig


# --- choice of K -------------------------------------------------------------

def k_composite_chart(results) -> go.Figure:
    """The pre-registered composite score per candidate K. Only candidates that
    passed the balance and stability filters have a score; the rest are absent
    and that absence is stated in the page, not hidden here."""
    scores = results.k_selection_trace.get("composite_scores", {})
    ks = sorted(int(k) for k in scores)
    ys = [scores[str(k)] if str(k) in scores else scores.get(k) for k in ks]
    colors = [ui.CYAN if k == results.optimal_k else ui.PANEL_HI for k in ks]
    fig = go.Figure(go.Bar(x=ks, y=ys, marker_color=colors,
                           text=[f"{y:.3f}" for y in ys], textposition="outside",
                           textfont=dict(color=ui.INK)))
    fig.update_layout(title="Composite selection score by K (higher is better)",
                      xaxis=dict(title="K", dtick=1), yaxis=dict(title="Composite score", range=[0, 1.05]),
                      height=360)
    return fig


def k_metric_chart(results, metric: str) -> go.Figure:
    """One internal metric across the full K sweep, with the selected K marked."""
    lookup = {
        "silhouette": (results.silhouette_by_k, "Silhouette (higher is better)"),
        "inertia": (results.inertia_by_k, "Inertia / elbow (lower is better)"),
        "calinski_harabasz": (results.ch_by_k, "Calinski-Harabasz (higher is better)"),
        "davies_bouldin": (results.db_by_k, "Davies-Bouldin (lower is better)"),
    }
    data, title = lookup[metric]
    ks = results.k_values
    fig = go.Figure(go.Scatter(x=ks, y=[data[k] for k in ks], mode="lines+markers",
                               line=dict(color=ui.CYAN, width=2.4), showlegend=False))
    fig.add_vline(x=results.optimal_k, line_dash="dash", line_color=ui.GREEN,
                  annotation_text=f"K={results.optimal_k}", annotation_font_color=ui.GREEN)
    if metric == "inertia":
        elbow = results.k_selection_trace.get("elbow_k")
        if elbow:
            fig.add_vline(x=float(elbow), line_dash="dot", line_color=ui.AMBER,
                          annotation_text=f"elbow K={int(elbow)}", annotation_font_color=ui.AMBER)
    fig.update_layout(title=title, xaxis=dict(title="K", dtick=1), height=320)
    return fig


def stability_by_k_chart(results) -> go.Figure:
    """Mean pairwise ARI across restarts at each K, with the 0.60 floor drawn."""
    ks, means, stds = [], [], []
    for k in results.k_values:
        s = results.stability_by_k.get(k) or {}
        if "mean_ari" in s:
            ks.append(k)
            means.append(s["mean_ari"])
            stds.append(s.get("std_ari", 0.0))
    fig = go.Figure(go.Scatter(
        x=ks, y=means, mode="lines+markers", line=dict(color=ui.GREEN, width=2.4),
        error_y=dict(type="data", array=stds, color=ui.GREEN_DEEP, thickness=1),
        showlegend=False))
    floor = results.k_selection_trace.get("rules", {}).get("min_stability_ari", 0.6)
    fig.add_hline(y=floor, line_dash="dash", line_color=ui.AMBER,
                  annotation_text=f"{floor:.2f} floor", annotation_font_color=ui.AMBER)
    fig.add_vline(x=results.optimal_k, line_dash="dash", line_color=ui.CYAN,
                  annotation_text=f"K={results.optimal_k}", annotation_font_color=ui.CYAN)
    fig.update_layout(title="Clustering stability by K (mean pairwise ARI over restarts)",
                      xaxis=dict(title="K", dtick=1), yaxis=dict(title="ARI", range=[0, 1.05]),
                      height=360)
    return fig


# --- features ----------------------------------------------------------------

def _features_with_labels(results) -> pd.DataFrame:
    fc = results.features_combined.copy()
    fc = fc.reset_index(drop=True)
    fc["cluster"] = results.cluster_labels
    name_by_id = {int(p["cluster"]): str(p["cluster_name"])
                  for _, p in results.cluster_profiles.iterrows()}
    fc["cluster_name"] = fc["cluster"].map(name_by_id)
    return fc


def feature_distribution_chart(results, feature: str) -> go.Figure:
    """The spread of one feature within each cluster, as box plots."""
    fc = _features_with_labels(results)
    fig = go.Figure()
    for _, prof in results.cluster_profiles.sort_values("cluster").iterrows():
        cid = int(prof["cluster"])
        name = str(prof["cluster_name"])
        vals = fc.loc[fc["cluster"] == cid, feature].astype(float)
        fig.add_trace(go.Box(y=vals, name=name, marker_color=ui.cluster_color(cid),
                             boxpoints="outliers", line=dict(width=1.4)))
    base = (results.population_baseline or {}).get(feature)
    if base is not None:
        fig.add_hline(y=base, line_dash="dot", line_color=ui.MIST,
                      annotation_text="population", annotation_font_color=ui.MIST)
    fig.update_layout(title=f"{feature} by cluster", yaxis_title=feature,
                      xaxis_title="", height=420, showlegend=False)
    return fig


CORRELATION_FEATURES = [
    "night_share", "morning_share", "afternoon_share", "evening_share",
    "weekend_ratio", "peak_to_avg_ratio", "coefficient_of_variation",
    "base_load_share", "shape_gini", "shape_entropy",
]


def correlation_heatmap(results) -> go.Figure:
    """Correlations among the interpretable shape descriptors that actually exist
    in the feature frame. (The previous dashboard referenced *_usage columns that
    the feature engineering never produced; these are the real *_share names.)"""
    fc = results.features_combined
    cols = [c for c in CORRELATION_FEATURES if c in fc.columns]
    corr = fc[cols].corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=cols, y=cols, zmin=-1, zmax=1,
        colorscale=[[0, ui.ROSE], [0.5, ui.PANEL], [1, ui.CYAN]],
        colorbar=dict(title="r"),
        hovertemplate="%{y} vs %{x}<br>r = %{z:.2f}<extra></extra>",
    ))
    fig.update_layout(title="How the shape descriptors move together", height=520,
                      margin=dict(l=180, b=140))
    return fig


# --- one consumer at a time (the dataset explorer) ---------------------------
# These are the only charts that show a single row of the dataset rather than an
# aggregate. They exist so a reader can check the analysis against the raw
# readings for a consumer they picked themselves, instead of taking the
# population summaries on trust.

def consumer_cluster_map(results) -> dict:
    """consumer_id -> cluster label, taken from the frame the model was fitted on.

    The mapping is read from the same frame and in the same row order that
    produced ``cluster_labels``, so it cannot drift from the fitted assignment.
    """
    for frame in (results.features_combined, results.features):
        if frame is not None and "consumer_id" in frame.columns:
            ids = frame["consumer_id"].to_numpy()
            if len(ids) == len(results.cluster_labels):
                return {int(c): int(k) for c, k in zip(ids, results.cluster_labels)}
    return {}


def consumer_ids(results) -> list:
    """Every consumer in the dataset, in ascending order."""
    return sorted(int(c) for c in results.preprocessed_data["consumer_id"].unique())


def consumer_profile_chart(results, consumer_id: int) -> go.Figure:
    """One consumer's average day in kWh, against the population average.

    This is the raw magnitude the clustering never sees, shown so the reader can
    tell how much of the difference between consumers is size.
    """
    pp = results.preprocessed_data
    mine = pp.loc[pp["consumer_id"] == int(consumer_id)].groupby("hour")["energy_consumption_kwh"].mean()
    everyone = pp.groupby("hour")["energy_consumption_kwh"].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=everyone.index, y=everyone.values, name="Population", mode="lines",
        line=dict(color=ui.SLATE, width=1.6, dash="dot"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=mine.index, y=mine.values, name=f"Consumer {int(consumer_id)}", mode="lines",
        line=dict(color=ui.CYAN, width=2.8, shape="spline", smoothing=0.6),
        fill="tonexty", fillcolor="rgba(59,201,222,0.07)",
        hovertemplate="%{x}:00 &middot; %{y:.3f} kWh<extra></extra>"))
    ui.add_time_of_day_bands(fig)
    fig.update_layout(
        title=f"Consumer {int(consumer_id)}: average day in kWh (magnitude)",
        xaxis=dict(title="Hour of day", tickvals=[0, 6, 12, 18, 23], range=[0, 23]),
        yaxis=dict(title="Mean kWh"), height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return fig


def consumer_shape_chart(results, consumer_id: int) -> go.Figure:
    """One consumer's normalised day against its own cluster and the population.

    The point of the chart is the comparison: this is what the model actually
    clustered on, so a reader can see why a consumer landed where it did - and
    where it sits awkwardly between two groups.
    """
    pp = results.preprocessed_data
    mine = pp.loc[pp["consumer_id"] == int(consumer_id)].groupby("hour")["energy_consumption_kwh"].mean()
    total = float(mine.sum())
    shape = (mine / total) if total else mine

    df, hour_cols = _shape_matrix(results)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=HOURS, y=_population_shape(results, df, hour_cols), name="Population",
        mode="lines", line=dict(color=ui.SLATE, width=1.6, dash="dot"), hoverinfo="skip"))

    cid = consumer_cluster_map(results).get(int(consumer_id))
    if cid is not None and str(cid) in df.index:
        name_by_id = {int(p["cluster"]): str(p["cluster_name"])
                      for _, p in results.cluster_profiles.iterrows()}
        fig.add_trace(go.Scatter(
            x=HOURS, y=df.loc[str(cid), hour_cols].astype(float),
            name=f"{name_by_id.get(cid, f'Cluster {cid}')} (mean)", mode="lines",
            line=dict(color=ui.cluster_color(cid), width=2.6, shape="spline", smoothing=0.6),
            hoverinfo="skip"))

    fig.add_trace(go.Scatter(
        x=shape.index, y=shape.values, name=f"Consumer {int(consumer_id)}",
        mode="lines+markers", line=dict(color=ui.INK, width=2.2),
        marker=dict(size=5, color=ui.INK),
        hovertemplate="%{x}:00 &middot; %{y:.1%} of daily energy<extra></extra>"))

    ui.add_time_of_day_bands(fig)
    fig.update_layout(
        title=f"Consumer {int(consumer_id)}: share of the day (what the model sees)",
        xaxis=dict(title="Hour of day", tickvals=[0, 6, 12, 18, 23], range=[0, 23]),
        yaxis=dict(title="Share of daily energy", tickformat=".0%"), height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return fig


def consumer_day_heatmap(results, consumer_id: int) -> go.Figure:
    """Every recorded day for one consumer, as day against hour.

    Shows the day-to-day variation that the mean profile hides, including the
    weekend rows.
    """
    pp = results.preprocessed_data
    mine = pp.loc[pp["consumer_id"] == int(consumer_id)].copy()
    mine["date"] = mine["timestamp"].dt.date
    grid = mine.pivot_table(index="date", columns="hour",
                            values="energy_consumption_kwh", aggfunc="mean")
    grid = grid.reindex(columns=HOURS)
    weekend = (mine.groupby("date")["is_weekend"].first()
               .reindex(grid.index).fillna(False).astype(bool))
    labels = [f"{d.isoformat()}{'  (weekend)' if w else ''}"
              for d, w in zip(grid.index, weekend)]
    fig = go.Figure(go.Heatmap(
        z=grid.to_numpy(), x=HOURS, y=labels, colorscale=_day_ramp_colorscale(),
        colorbar=dict(title="kWh"),
        hovertemplate="%{y}<br>%{x}:00 &middot; %{z:.3f} kWh<extra></extra>"))
    fig.update_layout(
        title=f"Consumer {int(consumer_id)}: every day on record (kWh)",
        xaxis=dict(title="Hour of day", tickvals=[0, 6, 12, 18, 23]),
        # type="category" is required: most of these labels parse as dates, so
        # Plotly would guess a date axis, thin the ticks and mangle the rows
        # carrying the weekend suffix.
        yaxis=dict(title="", type="category", autorange="reversed",
                   tickmode="array", tickvals=labels, ticktext=labels,
                   tickfont=dict(family="IBM Plex Mono, monospace", size=10)),
        height=max(260, 22 * len(labels) + 110), margin=dict(l=170))
    return fig


def cluster_size_chart(results) -> go.Figure:
    """How the dataset's consumers divide between the clusters."""
    profiles = results.cluster_profiles.sort_values("cluster")
    names = [str(p["cluster_name"]) for _, p in profiles.iterrows()]
    sizes = [int(p["size"]) for _, p in profiles.iterrows()]
    colors = [ui.cluster_color(int(p["cluster"])) for _, p in profiles.iterrows()]
    fig = go.Figure(go.Bar(
        x=sizes, y=names, orientation="h", marker_color=colors,
        text=[f"{s}" for s in sizes], textposition="outside", textfont=dict(color=ui.INK),
        hovertemplate="%{y}<br>%{x} consumers<extra></extra>"))
    fig.update_layout(title="Consumers per cluster", xaxis_title="Consumers",
                      yaxis=dict(title="", autorange="reversed"), height=260,
                      margin=dict(l=150))
    return fig


# --- exploratory (raw magnitude, clearly labelled as such) -------------------

def eda_hourly_chart(results) -> go.Figure:
    """Average consumption by hour, in kWh. This is magnitude, not shape; it is
    shown for context, and the clustering never uses magnitude."""
    pp = results.preprocessed_data
    hourly = pp.groupby("hour")["energy_consumption_kwh"].mean()
    fig = go.Figure(go.Scatter(x=hourly.index, y=hourly.values, mode="lines",
                               line=dict(color=ui.CYAN, width=2.6, shape="spline"),
                               fill="tozeroy", fillcolor="rgba(59,201,222,0.08)", showlegend=False))
    ui.add_time_of_day_bands(fig)
    fig.update_layout(title="Average consumption by hour (context only, kWh)",
                      xaxis=dict(title="Hour of day", tickvals=[0, 6, 12, 18, 23], range=[0, 23]),
                      yaxis_title="Mean kWh per record", height=380)
    return fig


def eda_weekend_chart(results) -> go.Figure:
    """Weekday against weekend mean consumption, in kWh."""
    pp = results.preprocessed_data
    comp = pp.groupby("is_weekend")["energy_consumption_kwh"].mean()
    labels = ["Weekday", "Weekend"]
    vals = [comp.get(False, comp.get(0, np.nan)), comp.get(True, comp.get(1, np.nan))]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=[ui.CYAN_DEEP, ui.AMBER],
                           text=[f"{v:.3f}" for v in vals], textposition="outside",
                           textfont=dict(color=ui.INK)))
    fig.update_layout(title="Weekday vs weekend (context only, kWh)", yaxis_title="Mean kWh per record",
                      xaxis_title="", height=340, showlegend=False)
    return fig
