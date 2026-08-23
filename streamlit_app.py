"""Streamlit dashboard for the energy load-shape study.

The interface is a research instrument: it runs the pipeline once per set of
settings and then reads everything from that single AnalysisResults object, so
there is exactly one set of numbers in play at a time. PCA and K-Means are never
recomputed for a single chart.

At its default settings the run reproduces the committed reference run
(config hash 6dff8faaa470d418), so the dashboard, the landing page and the
README all show the same numbers. Changing a setting in the sidebar starts a new
run in a private temporary directory; the committed artifacts under outputs/ and
models/ are never overwritten by the dashboard.

Vercel cannot host this file: Streamlit is a long-running server, not a Python
serverless handler. Use Streamlit Community Cloud, Render, Docker, or run locally.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))

from energy_analysis import AnalysisConfig, AnalysisResults, EnergyAnalysis  # noqa: E402
import dashboard_ui as ui  # noqa: E402
import dashboard_charts as ch  # noqa: E402
import dashboard_content as content  # noqa: E402

st.set_page_config(
    page_title="Energy load-shape study",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.inject_theme()

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


# --- run plumbing ------------------------------------------------------------

def _session_workdir() -> str:
    """A private temp directory for this session's runs, so in-dashboard runs
    never overwrite the committed outputs/ and models/ artifacts. config_hash
    excludes these paths, so routing here does not change any number."""
    wd = st.session_state.get("_workdir")
    if not wd or not Path(wd).exists():
        wd = tempfile.mkdtemp(prefix="energy_dash_")
        st.session_state["_workdir"] = wd
    return wd


def build_config_from_sidebar() -> AnalysisConfig:
    st.sidebar.markdown(
        '<div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;'
        'letter-spacing:0.2em;text-transform:uppercase;color:#3BC9DE;font-weight:600">'
        "Load-shape study</div>"
        '<div style="color:#8A93A6;font-size:0.82rem;margin:0.35rem 0 0.9rem">'
        "Synthetic data. PCA + K-Means on the shape of the day.</div>",
        unsafe_allow_html=True,
    )

    render_nav()

    with st.sidebar.expander("Adjust the run", expanded=False):
        st.caption(
            "Defaults reproduce the committed reference run. Changing anything "
            "starts a fresh run in a private temporary folder."
        )
        n_consumers = st.slider("Consumers", 50, 500, 200, step=10)
        n_days = st.slider("Days", 7, 90, 30)
        feature_set = st.selectbox(
            "Feature set", ["behavioral", "scale", "combined"], index=0,
            help="The primary study is behavioral (shape). scale and combined exist for the ablation.",
        )
        random_seed = st.number_input("Random seed", min_value=0, value=42, step=1)
        test_stability = st.checkbox(
            "Measure clustering stability", value=True,
            help="Repeats K-Means from several seeds at each K. Off is faster but drops the stability view.",
        )

    experiment = "behavioral_primary" if feature_set == "behavioral" else f"{feature_set}_ablation"
    wd = Path(_session_workdir())
    return AnalysisConfig(
        n_consumers=int(n_consumers),
        n_days=int(n_days),
        hourly_records=True,
        feature_set=feature_set,
        random_seed=int(random_seed),
        test_stability=bool(test_stability),
        experiment_name=experiment,
        output_dir=str(wd / "outputs"),
        model_dir=str(wd / "models"),
    )


@st.cache_resource(show_spinner=False)
def _run(cfg_hash: str, _config: AnalysisConfig) -> AnalysisResults:
    """Run the pipeline once per config hash. Cached across reruns so a chart
    interaction never recomputes the models. The hash is the cache key; the
    config is passed for the actual run and deliberately not hashed by Streamlit."""
    return EnergyAnalysis(_config).run()


def get_or_run_analysis(config: AnalysisConfig) -> AnalysisResults:
    cfg_hash = config.config_hash()
    is_default = cfg_hash == REFERENCE_HASH
    if cfg_hash not in st.session_state.get("_seen_hashes", set()):
        label = "reference run" if is_default else "new settings"
        with st.spinner(f"Running the pipeline ({label})..."):
            results = _run(cfg_hash, config)
        st.session_state.setdefault("_seen_hashes", set()).add(cfg_hash)
    else:
        results = _run(cfg_hash, config)
    return results


REFERENCE_HASH = "6dff8faaa470d418"


# --- small helpers -----------------------------------------------------------

def _plot(fig):
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)


def _pct(x) -> str:
    return f"{float(x) * 100:.1f}%"


def _num(x, dp: int = 3) -> str:
    return f"{float(x):.{dp}f}"


def _baseline(results, key):
    return (results.population_baseline or {}).get(key)


def _peak_label(profile, results) -> str:
    ratio = profile.get("peak_to_avg_ratio_vs_population")
    if ratio is not None and pd.notna(ratio) and float(ratio) < 0.85:
        return "near-flat"
    return f"peaks {int(profile['peak_hour']):02d}:00"


BULLET_DESCRIPTORS = [
    ("Evening share", "evening_share", "pct"),
    ("Afternoon share", "afternoon_share", "pct"),
    ("Morning share", "morning_share", "pct"),
    ("Night share", "night_share", "pct"),
    ("Base-load share", "base_load_share", "pct"),
    ("Peak-to-average", "peak_to_avg_ratio", "ratio"),
    ("Hour-to-hour variation", "coefficient_of_variation", "ratio"),
    ("Weekend/weekday energy", "weekend_ratio", "ratio"),
]


def _fmt_value(kind: str, value: float) -> str:
    return _pct(value) if kind == "pct" else _num(value, 2)


def _cluster_bullets(profile, results, n: int = 3) -> list:
    """The n most distinctive descriptors for a cluster, each against population."""
    scored = []
    for label, key, kind in BULLET_DESCRIPTORS:
        if key not in profile or pd.isna(profile[key]):
            continue
        base = _baseline(results, key)
        dev = abs(float(profile[key]) / float(base) - 1.0) if base else 0.0
        scored.append((dev, label, key, kind))
    scored.sort(reverse=True)
    bullets = []
    for _, label, key, kind in scored[:n]:
        base = _baseline(results, key)
        cval = _fmt_value(kind, profile[key])
        bval = _fmt_value(kind, base) if base is not None else "-"
        bullets.append(f"{label} <b>{cval}</b> <span>vs {bval} population</span>")
    return bullets


# --- navigation --------------------------------------------------------------
# One navigation, in the sidebar, grouped under the same top-level headings the
# landing page used. The masthead deliberately carries no page links: two menus
# for one set of pages is two things to keep in step.

NAV_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Start", ("Home", "How to use this simulator")),
    ("Simulator", ("Overview", "Dataset", "Data provenance", "Features")),
    ("Method", ("How it works", "Principal components", "Choosing K")),
    ("Clusters", ("The clusters", "Insights")),
    ("Validation", ("Stability", "Validation", "Limitations")),
    ("Research", ("Research",)),
)

HOME_PAGE = "Home"

PAGES = [name for _, names in NAV_GROUPS for name in names]

SECTION_OF_PAGE = {name: group for group, names in NAV_GROUPS for name in names}


def current_page() -> str:
    """The page being shown, defaulting to Home on first load."""
    page = st.session_state.get("_page", HOME_PAGE)
    return page if page in PAGES else HOME_PAGE


def goto(page: str) -> None:
    """Switch pages and rerun.

    Rerunning immediately keeps the highlighted navigation item and the rendered
    page in step; without it the run that handles the click would still be
    drawing the previous page's chrome. The analysis itself is cached on the
    config hash, so a page change never recomputes a model.
    """
    st.session_state["_page"] = page
    st.rerun()


def render_nav() -> None:
    """Draw the grouped sidebar navigation."""
    active = current_page()
    for group, names in NAV_GROUPS:
        ui.nav_group(group)
        for name in names:
            if st.sidebar.button(
                name, key=f"nav::{name}",
                type="primary" if name == active else "secondary",
            ):
                goto(name)


def nav_button(label: str, page: str, key: str) -> None:
    """A main-area call to action that moves to another page."""
    if st.button(label, key=key):
        goto(page)


# --- pages -------------------------------------------------------------------

def page_home(results: AnalysisResults):
    """The landing story, carried over from the static site.

    The static page had to hard-code its figures into JavaScript. Here every
    figure in the prose and every chart is read from the run that is currently
    loaded, so the story cannot fall out of step with the analysis it describes.
    """
    ui.kicker("PCA + K-Means &middot; synthetic study")
    ui.hero(
        'Energy has a <span class="accent">rhythm</span>.',
        "Two homes can use the same amount of electricity and behave nothing alike. "
        "This study groups consumers by the shape of their day, not by how much they use.",
    )
    ui.synthetic_badge("Synthetic data - not real households")
    st.write("")

    cta_left, cta_right, _ = st.columns([1, 1, 2])
    with cta_left:
        nav_button("Explore the data", "Overview", "cta::overview")
    with cta_right:
        nav_button("Read the method", "How it works", "cta::method")

    _plot(ch.load_shape_chart(results))
    st.caption(
        "Each coloured line is one cluster's average day; the dotted line is the "
        "population. Drag to zoom, double-click to reset."
    )

    for i, step in enumerate(content.story_steps(results), 1):
        ui.chapter(i, step["kicker"], step["title"], step.get("body", ""))
        if step.get("tiles"):
            ui.metric_cards(step["tiles"])
        if step.get("pipeline"):
            ui.pipeline(step["pipeline"])
        if step.get("warn"):
            ui.note(step["warn"], warn=True)
        if step.get("note"):
            ui.note(step["note"])
        _home_chapter_figure(i, results)

    ui.hairline()
    ui.section(
        "Where the method comes from",
        "Seven verified studies stand behind the choices made here.",
        eyebrow="Further reading",
    )
    nav_button("Open the references", "Research", "cta::research")


def _home_chapter_figure(index: int, results: AnalysisResults) -> None:
    """The live figure that belongs to one story chapter, if it has one.

    Kept apart from the prose so the words stay in dashboard_content and the
    charts stay in dashboard_charts, with only this mapping in between.
    """
    if index == 3:
        _plot(ch.eda_hourly_chart(results))
        ui.note(
            "That chart is in kilowatt-hours, and it is the one thing the clustering "
            "never sees. Divide each consumer's day by its own total and the size drops "
            "out, leaving the proportions that every other chart here is drawn from."
        )
    elif index == 6:
        profiles = results.cluster_profiles.sort_values("cluster")
        for col, (_, prof) in zip(st.columns(len(profiles)), profiles.iterrows()):
            cid = int(prof["cluster"])
            meta = (f"{int(prof['size'])} consumers &middot; {prof['size_share']:.1%} "
                    f"&middot; {_peak_label(prof, results)}")
            with col:
                ui.archetype_card(str(prof["cluster_name"]), ui.cluster_color(cid), meta,
                                  _cluster_bullets(prof, results))
        _plot(ch.hour_by_cluster_heatmap(results))
    elif index == 7:
        _plot(ch.stability_by_k_chart(results) if results.stability_results
              else ch.k_composite_chart(results))


def page_how_to(results: AnalysisResults):
    """A guide for a reader who knows what electricity is and nothing about ML.

    Fifteen chapters in a fixed order, because each one depends on the one before
    it. The prose lives in dashboard_content; this function decides where a live
    chart earns its place and where the reader should be sent next.
    """
    ui.kicker("Start here")
    ui.hero(
        'How to use this <span class="accent">simulator</span>.',
        "Every page here runs a real analysis on real code. This explains what it is "
        "doing, in order, assuming you know what a kilowatt-hour is and nothing about "
        "machine learning.",
    )

    st.write("")
    steps = content.how_to_use_quickstart()
    for i, (col, (title, body)) in enumerate(zip(st.columns(len(steps)), steps), 1):
        with col:
            ui.step_card(i, title, body)

    ui.hairline()
    chapters = content.how_to_use_chapters(results)
    ui.section(
        "The long version",
        f"{len(chapters)} short chapters, in order. Each one assumes the one before it.",
        eyebrow="Contents",
    )
    _contents_list(chapters)

    for i, chap in enumerate(chapters, 1):
        ui.chapter(i, HOW_TO_KICKERS[i], chap["title"])
        st.markdown(chap["body"])
        _how_to_chapter_extra(i, results)

    ui.hairline()
    ui.section(
        "Now go and look",
        "The guide is finished. The analysis is one click away.",
        eyebrow="Next",
    )
    left, middle, _ = st.columns([1, 1, 2])
    with left:
        nav_button("Open the dataset", "Dataset", "howto::dataset")
    with middle:
        nav_button("See the clusters", "The clusters", "howto::clusters")


HOW_TO_KICKERS = {
    1: "The question", 2: "The measurement", 3: "The shape", 4: "The table",
    5: "The numbers", 6: "The reason", 7: "Step one", 8: "Step two",
    9: "The result", 10: "Reading the charts", 11: "The controls",
    12: "Cause and effect", 13: "The scores", 14: "The findings", 15: "The caveats",
}

# Where a live chart says it better than another paragraph would.
HOW_TO_FIGURES = {
    3: ch.eda_hourly_chart,
    7: ch.pca_variance_chart,
    8: ch.pca_projection_chart,
    9: ch.load_shape_chart,
    13: ch.k_composite_chart,
}

HOW_TO_FIGURE_CAPTIONS = {
    3: "The average day across every consumer, in kilowatt-hours. This is a load "
       "profile: consumption against the hour it happened in.",
    7: "PCA's own report card. Each bar is one component's share of the variance; "
       "the line is the running total, and the analysis keeps components until it "
       "crosses 95 per cent.",
    8: "The first two components, with each point one consumer, coloured by the "
       "cluster K-Means put it in. This is the space the grouping happens in.",
    9: "One coloured line per cluster: the average day of everyone in it, as a share "
       "of their own daily total. This is the answer the whole pipeline exists to "
       "produce.",
    13: "The three scores that chose K, each rescaled to a common range so they can "
        "be read together. Drag to zoom, double-click to reset.",
}

HOW_TO_JUMPS = {
    4: ("Look at the rows", "Dataset", "howto::jump-dataset"),
    10: ("See them all at once", "Overview", "howto::jump-overview"),
    11: ("Try the controls", "Overview", "howto::jump-controls"),
    15: ("Read the full limitations", "Limitations", "howto::jump-limits"),
}


def _contents_list(chapters: list) -> None:
    """A numbered list of what follows.

    Streamlit reruns on every interaction and has no in-page anchor navigation, so
    this is a map rather than a set of links: it tells a reader how long the guide
    is and lets them decide where to start scrolling.
    """
    halves = (chapters[:8], chapters[8:])
    for col, half in zip(st.columns(2), halves):
        offset = 1 if half is halves[0] else 9
        with col:
            st.markdown("\n".join(
                f"{i}. {chap['title']}" for i, chap in enumerate(half, offset)
            ))


def _how_to_chapter_extra(index: int, results: AnalysisResults) -> None:
    """The chart or the onward link that belongs to one chapter of the guide."""
    figure = HOW_TO_FIGURES.get(index)
    if figure is not None:
        _plot(figure(results))
        caption = HOW_TO_FIGURE_CAPTIONS.get(index)
        if caption:
            st.caption(caption)
    jump = HOW_TO_JUMPS.get(index)
    if jump is not None:
        nav_button(*jump)


def page_dataset(results: AnalysisResults):
    """The dataset itself, open to inspection.

    Every other page shows an aggregate. This one shows the rows, so a reader can
    pick a consumer, look at its actual readings, and check the analysis against
    them rather than taking the summaries on trust.
    """
    ui.section(
        "The dataset",
        "The readings the analysis runs on, row by row. Pick a consumer and follow "
        "it from raw kilowatt-hours through to the cluster it lands in.",
        eyebrow="Inspect the data",
    )
    ui.note(
        "<strong>This is synthetic data.</strong> Every row below was generated by "
        "<code>src/data_loader.py</code> from a hidden archetype, not measured from a "
        "real meter. It is shown in full so the method can be checked, not because the "
        "consumers exist.",
        warn=True,
    )

    raw = results.raw_data
    pp = results.preprocessed_data
    ui.metric_cards([
        {"label": "Rows", "value": f"{len(pp):,}", "sub": "one per consumer-hour"},
        {"label": "Consumers", "value": f"{pp['consumer_id'].nunique()}"},
        {"label": "Days", "value": f"{pp['timestamp'].dt.date.nunique()}"},
        {"label": "Columns", "value": f"{pp.shape[1]}", "sub": "after preprocessing"},
        {"label": "Missing values", "value": f"{int(pp.isna().sum().sum())}",
         "sub": "filled within each consumer"},
        {"label": "First reading", "value": f"{pp['timestamp'].min():%Y-%m-%d}"},
        {"label": "Last reading", "value": f"{pp['timestamp'].max():%Y-%m-%d}"},
        {"label": "Total energy", "value": f"{pp['energy_consumption_kwh'].sum():,.0f}",
         "sub": "kWh across the panel"},
    ])

    tab_rows, tab_one, tab_features, tab_clusters = st.tabs(
        ["Readings", "One consumer", "Engineered features", "Cluster assignment"]
    )

    with tab_rows:
        st.markdown(
            "The table below is the preprocessed panel: timestamps parsed, records "
            "sorted within each consumer, gaps filled from that consumer's own history. "
            "The clustering only ever uses `energy_consumption_kwh`, `hour` and "
            "`is_weekend`; the electrical columns are carried along as context."
        )
        n_rows = st.slider("Rows to show", 20, 500, 100, step=20, key="ds::rows")
        consumer_filter = st.multiselect(
            "Limit to consumers (leave empty for all)",
            options=ch.consumer_ids(results), default=[], key="ds::filter",
        )
        view = pp[pp["consumer_id"].isin(consumer_filter)] if consumer_filter else pp
        st.caption(f"Showing {min(n_rows, len(view)):,} of {len(view):,} rows.")
        st.dataframe(view.head(n_rows), width="stretch", hide_index=True)

        ui.section("What each column is")
        st.dataframe(_schema_table(pp), width="stretch", hide_index=True)
        _download("Download the preprocessed panel (CSV)", pp, "preprocessed_panel.csv",
                  results.config.config_hash())

        if "archetype" in raw.columns:
            ui.section("The held-out answer key")
            ui.note(
                "The generator's archetype label is dropped before preprocessing and never "
                "reaches the scaler, PCA or K-Means. It is shown here because it is part of "
                "the dataset, and used only at the very end on the Validation page as an "
                "independent check."
            )
            truth = (raw.groupby("consumer_id")["archetype"].first()
                     .rename("archetype").reset_index())
            counts = truth["archetype"].value_counts().rename_axis("archetype")
            st.dataframe(counts.rename("consumers").reset_index(),
                         width="stretch", hide_index=True)

    with tab_one:
        ids = ch.consumer_ids(results)
        picked = st.selectbox("Consumer", ids, index=0, key="ds::consumer",
                              format_func=lambda c: f"Consumer {c}")
        cluster_of = ch.consumer_cluster_map(results)
        cid = cluster_of.get(int(picked))
        name_by_id = {int(p["cluster"]): str(p["cluster_name"])
                      for _, p in results.cluster_profiles.iterrows()}
        mine = pp[pp["consumer_id"] == int(picked)]
        day_totals = mine.groupby(mine["timestamp"].dt.date)["energy_consumption_kwh"].sum()
        hourly_mean = mine.groupby("hour")["energy_consumption_kwh"].mean()
        cards = [
            {"label": "Readings", "value": f"{len(mine):,}"},
            {"label": "Mean daily energy", "value": f"{day_totals.mean():.2f}", "sub": "kWh"},
            {"label": "Busiest hour", "value": f"{int(hourly_mean.idxmax()):02d}:00"},
            {"label": "Assigned cluster",
             "value": name_by_id.get(cid, "-") if cid is not None else "-",
             "accent": True},
        ]
        if "archetype" in raw.columns:
            truth = raw.loc[raw["consumer_id"] == int(picked), "archetype"]
            if len(truth):
                cards.append({"label": "Hidden archetype", "value": str(truth.iloc[0]),
                              "sub": "held out from the model"})
        ui.metric_cards(cards)

        _plot(ch.consumer_profile_chart(results, picked))
        _plot(ch.consumer_shape_chart(results, picked))
        ui.note(
            "The first chart is in kilowatt-hours and includes this consumer's size. The "
            "second divides that away, leaving the share of the day in each hour - and that "
            "is the only version the model ever sees. A consumer whose dark line tracks its "
            "cluster's colour closely is a typical member; one that wanders between two "
            "coloured lines is the overlap the modest silhouette is measuring."
        )
        _plot(ch.consumer_day_heatmap(results, picked))
        with st.expander(f"Every reading for consumer {picked}"):
            st.dataframe(mine, width="stretch", hide_index=True)

    with tab_features:
        st.markdown(
            f"One row per consumer, {len(results.feature_names)} columns describing the "
            "shape of its day. This is the table that is standardised and passed to PCA. "
            "The Features page explains what the columns mean."
        )
        feats = results.features_combined
        st.dataframe(feats, width="stretch", hide_index=True)
        st.caption(f"{feats.shape[0]:,} consumers x {feats.shape[1]} columns.")
        _download("Download the feature matrix (CSV)", feats, "consumer_features.csv",
                  results.config.config_hash())

    with tab_clusters:
        st.markdown(
            "Where each consumer ended up. The label comes from the fitted K-Means model, "
            "so this table is the model's output, not a recomputation of it."
        )
        _plot(ch.cluster_size_chart(results))
        assignment = _assignment_table(results)
        st.dataframe(assignment, width="stretch", hide_index=True)
        _download("Download the cluster assignment (CSV)", assignment,
                  "cluster_assignment.csv", results.config.config_hash())


COLUMN_NOTES = {
    "consumer_id": "Which consumer the reading belongs to.",
    "timestamp": "When the hour began.",
    "energy_consumption_kwh": "Energy used in that hour, in kilowatt-hours. The measurement everything else is derived from.",
    "voltage_v": "Supply voltage, in volts. Context only; not used in the clustering.",
    "current_a": "Current drawn, in amperes. Context only.",
    "power_factor": "Ratio of real to apparent power. Context only.",
    "temperature_c": "Ambient temperature, in degrees Celsius. Context only.",
    "hour": "Hour of the day, 0 to 23. Derived from the timestamp.",
    "day_of_week": "Monday is 0. Derived from the timestamp.",
    "is_weekend": "True on Saturday and Sunday. Used by the weekend features.",
    "month": "Calendar month. Derived from the timestamp.",
}


def _schema_table(df: pd.DataFrame) -> pd.DataFrame:
    """Columns, types and a plain-language note, for the dataset explorer."""
    return pd.DataFrame({
        "column": df.columns,
        "type": [str(t) for t in df.dtypes],
        "non-null": [int(df[c].notna().sum()) for c in df.columns],
        "what it is": [COLUMN_NOTES.get(c, "") for c in df.columns],
    })


def _assignment_table(results: AnalysisResults) -> pd.DataFrame:
    """consumer_id, cluster and cluster name, read from the fitted model."""
    cluster_of = ch.consumer_cluster_map(results)
    name_by_id = {int(p["cluster"]): str(p["cluster_name"])
                  for _, p in results.cluster_profiles.iterrows()}
    rows = pd.DataFrame({
        "consumer_id": list(cluster_of),
        "cluster": [cluster_of[c] for c in cluster_of],
    })
    rows["cluster_name"] = rows["cluster"].map(name_by_id)
    if "archetype" in results.raw_data.columns:
        truth = results.raw_data.groupby("consumer_id")["archetype"].first()
        rows["hidden_archetype"] = rows["consumer_id"].map(truth)
    return rows.sort_values("consumer_id").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _to_csv(_df: pd.DataFrame, cache_key: str) -> bytes:
    """Encode a frame once per run rather than on every rerun.

    The frame is passed with a leading underscore so Streamlit does not try to
    hash it; the config hash plus the file name is the cache key.
    """
    return _df.to_csv(index=False).encode("utf-8")


def _download(label: str, df: pd.DataFrame, filename: str, cfg_hash: str) -> None:
    st.download_button(label, data=_to_csv(df, f"{cfg_hash}:{filename}"),
                       file_name=filename, mime="text/csv", key=f"dl::{filename}")


def page_overview(results: AnalysisResults):
    ui.kicker("PCA + K-Means &middot; synthetic study")
    ui.hero(
        'Energy has a <span class="accent">rhythm</span>.',
        "Two homes can use the same amount of electricity and behave nothing alike. "
        "This study groups consumers by the shape of their day, not by how much they use.",
    )
    ui.synthetic_badge("Synthetic data - not real households")

    sizes = results.cluster_sizes()
    stability = results.stability_results or {}
    ari = results.ari_for_k(results.optimal_k)
    ui.metric_cards([
        {"label": "Records", "value": f"{len(results.preprocessed_data):,}"},
        {"label": "Consumers", "value": f"{results.preprocessed_data['consumer_id'].nunique()}"},
        {"label": "Features", "value": len(results.feature_names), "sub": "behavioural, shape only"},
        {"label": "PCA components", "value": results.n_pca_components,
         "sub": f"{results.metadata['pca_cumulative_variance']:.1%} variance"},
        {"label": "Clusters", "value": results.optimal_k, "accent": True,
         "sub": f"sizes {sizes}"},
        {"label": "Silhouette", "value": _num(results.silhouette_for_k(results.optimal_k)),
         "sub": "separation, modest"},
        {"label": "Stability ARI", "value": _num(stability.get("mean_ari", float("nan"))),
         "sub": "across restarts"},
        {"label": "Archetype ARI", "value": _num(ari) if ari is not None else "-",
         "sub": "agreement with hidden truth"},
    ])

    ui.section("The shape of a day", "Each cluster's mean day, over the population average.")
    _plot(ch.load_shape_chart(results))
    ui.note(
        "Every consumer's 24 hourly values are scaled to sum to one before anything "
        "else, so what is grouped is the <strong>shape</strong> of the day, not its size. "
        "The clusters below are three different daily rhythms, not big, medium and small."
    )
    st.caption(
        f"Config hash `{results.config.config_hash()}` &middot; "
        f"generated {results.metadata['timestamp_utc']}"
    )


def page_how_it_works(results: AnalysisResults):
    ui.section("How it works", "The whole method in plain terms, then as steps.", eyebrow="Beginner mode")
    st.markdown(
        "A household's day can be drawn as a curve: how much electricity it uses in "
        "each hour. If you scale that curve so the whole day adds up to one, you throw "
        "away the size and keep only the **timing** - when the household is busy. This "
        "study describes each consumer's timing with a set of numbers, compresses those "
        "numbers so the redundant ones do not dominate, and then looks for groups of "
        "consumers whose timing is alike."
    )
    st.markdown(
        "- **PCA** finds the few combinations of features that carry most of the variation, "
        "so clustering happens in a compact, less redundant space.\n"
        "- **K-Means** puts each consumer in the nearest of K groups; the number of groups K "
        "is chosen by a rule fixed in advance, not to make the picture tidy.\n"
        "- **Silhouette** measures how cleanly separated the groups are (higher is better).\n"
        "- **Stability** measures whether the same groups reappear when the algorithm is "
        "restarted; it is not a confidence that any one consumer is correctly placed.\n"
        "- **Adjusted Rand Index** checks the groups against the hidden archetypes the "
        "generator used - a check only possible because the data is synthetic."
    )
    ui.section("The pipeline")
    ui.pipeline([
        ("Generate", "A synthetic panel of consumers drawn from four hidden archetypes."),
        ("Preprocess", "Sort by consumer and time; impute within a consumer only."),
        ("Engineer features", f"{len(results.feature_names)} behavioural descriptors of the daily shape."),
        ("Reduce", f"Standardise, then PCA to {results.metadata['pca_cumulative_variance']:.0%} variance "
                   f"({results.n_pca_components} components)."),
        ("Sweep K", f"K-Means for K = {min(results.k_values)} to {max(results.k_values)}, four internal metrics."),
        ("Select", "A pre-registered rule, then a multi-seed stability check."),
        ("Profile", "Describe each cluster in real units, against the population."),
        ("Validate", "Compare with the hidden archetypes (synthetic data only)."),
    ])
    ui.note(
        "The archetype label is dropped before preprocessing and never reaches the "
        "scaler, PCA or K-Means. It is used only at the end, as an independent check."
    )


def page_data(results: AnalysisResults):
    ui.section("Data provenance", "Where the readings come from, and what they look like in aggregate.",
               eyebrow="How it was made")
    ui.note(
        "<strong>This is synthetic data.</strong> The consumers do not exist. Nothing here "
        "is evidence about real-world household behaviour; it is a test of whether the "
        "method recovers structure that was deliberately built in.",
        warn=True,
    )
    ui.metric_cards([
        {"label": "Consumers", "value": f"{results.config.n_consumers}"},
        {"label": "Days", "value": f"{results.config.n_days}", "sub": "hourly records"},
        {"label": "Records", "value": f"{len(results.preprocessed_data):,}"},
        {"label": "Hidden archetypes", "value": "4", "sub": "daytime, evening, flat, weekend"},
    ])
    col1, col2 = st.columns(2)
    with col1:
        _plot(ch.eda_hourly_chart(results))
    with col2:
        _plot(ch.eda_weekend_chart(results))
    ui.section("How the shape descriptors move together")
    _plot(ch.correlation_heatmap(results))
    ui.note(
        "These are the interpretable shape descriptors, and they are correlated by "
        "construction (the period shares sum to one, peakiness and variation track each "
        "other). That correlation is exactly why the next step reduces the dimensions "
        "before clustering."
    )


def page_features(results: AnalysisResults):
    ui.section(
        "Features",
        f"{len(results.feature_names)} numbers describe each consumer's daily shape - and not one is the raw size.",
        eyebrow="What is measured",
    )
    ui.tags([
        "24 hourly shape bins", "4 period shares", "peakiness", "entropy and inequality",
        "Fourier harmonics", "wavelet detail energy", "weekend shape distance",
        "dispersion", "base-load share",
    ])
    st.write("")
    interpretable = [
        ("Evening share of daily energy", "evening_share"),
        ("Afternoon share", "afternoon_share"),
        ("Morning share", "morning_share"),
        ("Night share", "night_share"),
        ("Base-load share", "base_load_share"),
        ("Peak-to-average ratio", "peak_to_avg_ratio"),
        ("Hour-to-hour variation (CV)", "coefficient_of_variation"),
        ("Weekend to weekday energy", "weekend_ratio"),
        ("Shape inequality (Gini)", "shape_gini"),
        ("Shape entropy", "shape_entropy"),
        ("Peak concentration", "peak_concentration"),
    ]
    present = [(lbl, key) for lbl, key in interpretable if key in results.features_combined.columns]
    labels = [lbl for lbl, _ in present]
    chosen = st.selectbox("Show the spread of", labels, index=0)
    key = dict(present)[chosen]
    _plot(ch.feature_distribution_chart(results, key))
    ui.note(
        "Each box is one cluster; the dotted line is the population value. The clusters "
        "were not formed from any single feature - they come from the compressed "
        "combination of all of them - so a feature that separates the boxes well is "
        "describing the grouping, not defining it."
    )


def page_pca(results: AnalysisResults):
    ui.section(
        "Principal components",
        f"Standardise the {len(results.feature_names)} features, then keep the components that hold the variance.",
        eyebrow="Dimensionality reduction",
    )
    ui.metric_cards([
        {"label": "Components kept", "value": results.n_pca_components, "accent": True},
        {"label": "Cumulative variance", "value": f"{results.metadata['pca_cumulative_variance']:.2%}"},
        {"label": "Input features", "value": len(results.feature_names)},
    ])
    _plot(ch.pca_variance_chart(results))
    ui.section("What the axes mean")
    loadings = ch._loadings(results)
    pcs = [c for c in loadings.columns if str(c).upper().startswith("PC")][:6]
    pc = st.selectbox("Component", pcs, index=0)
    _plot(ch.pca_loadings_chart(results, pc))
    ui.note(
        "A component is a direction in feature space. The features with the largest "
        "positive and negative loadings are what that direction contrasts - for example "
        "a peaky, high-variation evening against a flat, high-base-load night."
    )
    ui.section("The consumers in that space")
    _plot(ch.pca_projection_chart(results, color_by_cluster=False))


def page_k(results: AnalysisResults):
    ui.section(
        "Choosing K",
        "The number of clusters is chosen by a rule fixed in advance, and the awkward numbers are shown too.",
        eyebrow="Model selection",
    )
    sizes = results.cluster_sizes()
    ui.metric_cards([
        {"label": "Candidates", "value": f"{min(results.k_values)}-{max(results.k_values)}"},
        {"label": "Selected K", "value": results.optimal_k, "accent": True},
        {"label": "Silhouette @ K", "value": _num(results.silhouette_for_k(results.optimal_k), 4),
         "sub": "modest separation"},
        {"label": "Cluster sizes", "value": str(sizes)},
    ])
    _plot(ch.k_composite_chart(results))
    trace = results.k_selection_trace
    rejected = sorted(set(trace.get("candidates", [])) - set(trace.get("after_balance_filter", [])))
    elbow = trace.get("elbow_k")
    ui.note(
        f"The composite score combines silhouette, Calinski-Harabasz and Davies-Bouldin, "
        f"normalised across candidates. It is only computed for K that first pass the "
        f"filters: candidates {rejected} were rejected for producing a cluster below 5% "
        f"of consumers. The score picks K={trace.get('best_k_by_score', results.optimal_k)}, "
        f"while the inertia elbow points at K={int(elbow) if elbow else '-'} - reported for "
        f"comparison, not used to decide."
    )
    metric = st.selectbox(
        "Metric across the sweep",
        ["silhouette", "inertia", "calinski_harabasz", "davies_bouldin"],
        format_func=lambda m: m.replace("_", " ").title(),
    )
    _plot(ch.k_metric_chart(results, metric))
    ui.section("The clusters in component space")
    _plot(ch.pca_projection_chart(results, color_by_cluster=True))


def page_clusters(results: AnalysisResults):
    ui.section("The clusters", "Three daily rhythms, each named for its own characteristics.", eyebrow="Result")
    profiles = results.cluster_profiles.sort_values("cluster")
    cols = st.columns(len(profiles))
    for col, (_, prof) in zip(cols, profiles.iterrows()):
        cid = int(prof["cluster"])
        meta = f"{int(prof['size'])} consumers &middot; {prof['size_share']:.1%} &middot; {_peak_label(prof, results)}"
        with col:
            ui.archetype_card(str(prof["cluster_name"]), ui.cluster_color(cid), meta,
                              _cluster_bullets(prof, results))

    _plot(ch.load_shape_chart(results))
    _plot(ch.hour_by_cluster_heatmap(results))

    ui.section("Compare clusters", "Pick clusters to line their numbers up against the population.")
    name_by_id = {int(p["cluster"]): str(p["cluster_name"]) for _, p in profiles.iterrows()}
    picked = st.multiselect(
        "Clusters", options=list(name_by_id), default=list(name_by_id),
        format_func=lambda cid: name_by_id[cid],
    )
    if picked:
        _plot(_comparison_table(results, picked))

    ui.section("Read each cluster")
    insights = results.cluster_insights.set_index("cluster")
    for _, prof in profiles.iterrows():
        cid = int(prof["cluster"])
        with st.expander(f"{prof['cluster_name']}  -  {int(prof['size'])} consumers"):
            if cid in insights.index:
                st.markdown(str(insights.loc[cid, "interpretation"]))


def _comparison_table(results, picked):
    profiles = results.cluster_profiles
    rows = [
        ("Share of consumers", "size_share", "pct"),
        ("Peak hour", "peak_hour", "hour"),
        ("Evening share", "evening_share", "pct"),
        ("Afternoon share", "afternoon_share", "pct"),
        ("Night share", "night_share", "pct"),
        ("Base-load share", "base_load_share", "pct"),
        ("Peak-to-average", "peak_to_avg_ratio", "num"),
        ("Hour-to-hour variation", "coefficient_of_variation", "num"),
        ("Weekend/weekday energy", "weekend_ratio", "num"),
    ]
    import plotly.graph_objects as go
    header_names = [profiles.loc[profiles["cluster"] == cid, "cluster_name"].iloc[0] for cid in picked]
    header = ["Metric"] + header_names + ["Population"]

    def cell(kind, val):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "-"
        if kind == "pct":
            return _pct(val)
        if kind == "hour":
            return f"{int(val):02d}:00"
        return _num(val, 2)

    table_cols = [[label for label, _, _ in rows]]
    for cid in picked:
        prof = profiles.loc[profiles["cluster"] == cid].iloc[0]
        table_cols.append([cell(kind, prof.get(key)) for _, key, kind in rows])
    table_cols.append([cell(kind, _baseline(results, key)) if kind != "hour" else "-"
                       for _, key, kind in rows])

    fig = go.Figure(go.Table(
        header=dict(values=header, fill_color=ui.PANEL_HI, align="left",
                    font=dict(color=ui.INK, family="IBM Plex Mono, monospace", size=12),
                    line_color=ui.LINE),
        cells=dict(values=table_cols, fill_color=ui.PANEL, align="left",
                   font=dict(color=ui.INK, size=12), line_color=ui.LINE, height=30),
    ))
    fig.update_layout(height=40 + 32 * (len(rows) + 1), margin=dict(l=0, r=0, t=8, b=0))
    return fig


def page_stability(results: AnalysisResults):
    ui.section(
        "Stability",
        "Whether the same clusters reappear when the algorithm is restarted.",
        eyebrow="Robustness",
    )
    stability = results.stability_results or {}
    if not stability:
        ui.note("Stability was not measured for this run. Turn on "
                "\"Measure clustering stability\" in the sidebar to compute it.", warn=True)
        return
    ui.metric_cards([
        {"label": "Mean pairwise ARI", "value": _num(stability.get("mean_ari", float("nan"))),
         "accent": True, "sub": "1.0 is identical every restart"},
        {"label": "Assignment agreement", "value": _num(stability.get("mean_agreement", float("nan")))},
        {"label": "Restarts", "value": stability.get("n_runs", "-")},
        {"label": "Lowest pair ARI", "value": _num(stability.get("min_ari", float("nan")))
         if stability.get("min_ari") is not None else "-"},
    ])
    _plot(ch.stability_by_k_chart(results))
    ui.note(
        "Stability is a property of the <strong>clustering</strong>: it says the same "
        "groups keep forming. It is not a per-consumer confidence, and it does not say "
        "the groups are well separated - that is the silhouette, which is only modest here. "
        "A clustering can be highly stable and only moderately separated at the same time, "
        "and this one is."
    )


def page_validation(results: AnalysisResults):
    ui.section(
        "Validation",
        "Comparing the recovered clusters with the hidden archetypes - possible only because the data is synthetic.",
        eyebrow="Ground-truth check",
    )
    recovery = results.archetype_recovery
    if recovery is not None:
        import plotly.graph_objects as go
        ks = recovery["K"].astype(int).tolist()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ks, y=recovery["ari"], mode="lines+markers", name="Adjusted Rand Index",
                                 line=dict(color=ui.GREEN, width=2.4)))
        fig.add_trace(go.Scatter(x=ks, y=recovery["nmi"], mode="lines+markers", name="Normalised Mutual Information",
                                 line=dict(color=ui.CYAN, width=2.4)))
        fig.add_vline(x=results.optimal_k, line_dash="dash", line_color=ui.MIST,
                      annotation_text=f"selected K={results.optimal_k}", annotation_font_color=ui.MIST)
        fig.update_layout(title="Agreement with the hidden archetypes by K",
                          xaxis=dict(title="K", dtick=1), yaxis=dict(title="Score", range=[0, 1.05]),
                          height=380, legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
        _plot(fig)

        ari = results.ari_for_k(results.optimal_k)
        ui.note(
            f"At the selected K={results.optimal_k}, the Adjusted Rand Index against the "
            f"archetypes is {_num(ari, 4)}. That is moderate: the recovered clusters line up "
            f"with the built-in structure well above chance, but they are not the same "
            f"partition. The four archetypes and three clusters do not map one to one, which "
            f"the cross-tabulation below makes visible."
        )
        if results.archetype_crosstab is not None:
            st.markdown("**Cluster against archetype**")
            st.dataframe(results.archetype_crosstab, width="stretch")

    _external_report("Ablation study", ROOT / "outputs" / "reports" / "ablation_study_report.md")
    _external_report("Seed robustness", ROOT / "outputs" / "reports" / "seed_robustness_report.md")


def _external_report(title: str, path: Path):
    if not path.exists():
        return
    ui.section(title)
    with st.expander(f"Read the {title.lower()} report"):
        st.markdown(path.read_text(encoding="utf-8"))


def page_insights(results: AnalysisResults):
    ui.section(
        "Insights",
        "Each is a measured deviation from the population, not a cause and not a saving.",
        eyebrow="Observation to action",
    )
    ui.note(
        "The engine only raises a point when a cluster's characteristic differs enough "
        "from the population. It makes no causal claim and quotes no savings figure. Where "
        "a cluster sits close to the population, it stays silent - that silence is a result too."
    )
    recs = results.recommendations
    profiles = results.cluster_profiles.sort_values("cluster")
    for _, prof in profiles.iterrows():
        cid = int(prof["cluster"])
        color = ui.cluster_color(cid)
        ui.section(str(prof["cluster_name"]))
        cluster_recs = recs[recs["cluster"] == cid] if "cluster" in recs.columns else recs.iloc[0:0]
        if not len(cluster_recs):
            ui.note(
                "No point was raised for this cluster: on every measured characteristic it "
                "sits close enough to the population that the engine stayed silent."
            )
            continue
        for _, row in cluster_recs.iterrows():
            head = f"{str(row['category']).replace('_', ' ').title()} &middot; {row['priority']} priority"
            ui.insight_block(
                head=head, color=color,
                observation=str(row["observation"]),
                evidence=str(row["evidence"]),
                action=str(row["action"]),
            )


def page_research(results: AnalysisResults):
    ui.section(
        "Research",
        "Where the method comes from, and the work worth comparing it against.",
        eyebrow="References",
    )
    ui.note(
        "Every reference below was checked against Crossref for its title, authors, year, "
        "venue and DOI. These are real-world studies; this project is synthetic, so they "
        "are context and lineage for the method, not evidence for any result shown here."
    )
    ui.research_grid(content.REFERENCES)
    ui.note(content.REFERENCES_OMITTED_NOTE)


def page_limitations(results: AnalysisResults):
    ui.section("Limitations", "What this study does not show.", eyebrow="Honesty")
    sil = results.silhouette_for_k(results.optimal_k)
    st.markdown(
        f"""
- **Synthetic data.** The archetypes are designed; a real grid may differ. The source is
  labelled synthetic everywhere, and no result here is evidence about real households.
- **Modest separation.** The silhouette at K={results.optimal_k} is {sil:.4f}. The clusters
  are stable but they overlap at their edges; they are tendencies, not sharp categories.
- **Clustering is not causation.** The insights are correlational descriptions of a group,
  never a claim that a pattern causes an outcome or that acting on it saves a fixed amount.
- **One synthetic window.** A single generated panel of {results.config.n_days} days. The
  seed-robustness study repeats the generation, but this is not a multi-season claim.
- **Feature dependence.** The result depends on the behavioural feature set; the scale and
  combined sets behave differently, which is the point of the ablation.
- **Session safety.** Changing a sidebar setting starts a fresh run in a private temporary
  folder (current hash `{results.config.config_hash()}`); the committed artifacts are untouched.
        """
    )


# Keyed by page name, in the same order as NAV_GROUPS so the two can be read
# side by side.
PAGE_FUNCS = {
    "Home": page_home,
    "How to use this simulator": page_how_to,
    "Overview": page_overview,
    "Dataset": page_dataset,
    "Data provenance": page_data,
    "Features": page_features,
    "How it works": page_how_it_works,
    "Principal components": page_pca,
    "Choosing K": page_k,
    "The clusters": page_clusters,
    "Insights": page_insights,
    "Stability": page_stability,
    "Validation": page_validation,
    "Limitations": page_limitations,
    "Research": page_research,
}

MASTHEAD_LINKS = (
    ("Landing page", "https://energy-pattern-analysis.vercel.app"),
    ("Repository", content.REPO_URL),
)


def main():
    config = build_config_from_sidebar()
    page = current_page()
    ui.masthead(SECTION_OF_PAGE.get(page, "Start"), MASTHEAD_LINKS)
    results = get_or_run_analysis(config)
    PAGE_FUNCS[page](results)
    ui.footer(
        run_line=f"Synthetic study &middot; PCA + K-Means &middot; run {config.config_hash()}",
        tagline="Grouped by the shape of the day, not the size of the bill.",
        links=(("Read the code", content.REPO_URL),),
    )


if __name__ == "__main__":
    main()
