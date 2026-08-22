"""
Streamlit dashboard for Energy Consumption Pattern Analysis.

All pages read from a single AnalysisResults object. PCA / K-Means are never
recomputed independently for display. Parameter changes invalidate via config hash.

Vercel cannot host this file: Streamlit is a long-running server, not a
Python serverless handler. Use Streamlit Community Cloud, Render, Docker, or run locally.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from energy_analysis import AnalysisConfig, EnergyAnalysis, AnalysisResults

st.set_page_config(
    page_title="Energy Consumption Pattern Analysis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; padding: 1rem 0; }
    .section-header { font-size: 1.5rem; font-weight: bold; color: #2c3e50; padding: 1rem 0 0.5rem 0; }
</style>
""",
    unsafe_allow_html=True,
)


def build_config_from_sidebar() -> AnalysisConfig:
    st.sidebar.header("Analysis Parameters")
    n_consumers = st.sidebar.slider("Number of Consumers", 50, 500, 200)
    n_days = st.sidebar.slider("Number of Days", 7, 90, 30)
    hourly_records = st.sidebar.checkbox("Hourly Records", value=True)
    feature_set = st.sidebar.selectbox(
        "Feature Set",
        options=["behavioral", "scale", "combined"],
        index=0,
        help="Primary experiment uses behavioral (shape) features.",
    )
    random_seed = st.sidebar.number_input("Random Seed", min_value=0, value=42, step=1)
    return AnalysisConfig(
        n_consumers=int(n_consumers),
        n_days=int(n_days),
        hourly_records=bool(hourly_records),
        feature_set=feature_set,
        random_seed=int(random_seed),
        test_stability=False,
        experiment_name=f"dashboard_{feature_set}",
    )


def get_or_run_analysis(config: AnalysisConfig) -> AnalysisResults:
    """
    Single analysis object in session state.
    Regenerates fully when config hash changes. Never keeps stale models or labels.
    """
    cfg_hash = config.config_hash()
    cached = st.session_state.get("analysis_results")
    cached_hash = st.session_state.get("analysis_config_hash")

    if cached is None or cached_hash != cfg_hash:
        with st.spinner("Running full analysis pipeline (invalidating prior session state)..."):
            analysis = EnergyAnalysis(config)
            results = analysis.run()
        st.session_state["analysis_results"] = results
        st.session_state["analysis_config_hash"] = cfg_hash
        for key in ("X_pca", "labels", "pca", "kmeans"):
            st.session_state.pop(key, None)
    return st.session_state["analysis_results"]


def overview_page(results: AnalysisResults):
    st.markdown(
        '<div class="main-header">⚡ Energy Consumption Pattern Analysis</div>',
        unsafe_allow_html=True,
    )
    st.info(
        "**Data source: Synthetic (archetype-based).** "
        "Latent archetypes are hidden ground truth and are never passed to K-Means."
    )

    st.markdown(
        "Objective: recover meaningful *usage-pattern* groups (when/how energy is used), "
        "not merely low/medium/high magnitude splits. PCA + K-Means remain the core methods."
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Records", f"{len(results.preprocessed_data):,}")
    with col2:
        st.metric("Consumers", f"{results.preprocessed_data['consumer_id'].nunique()}")
    with col3:
        st.metric("Features", len(results.feature_names))
    with col4:
        st.metric("Selected K", results.optimal_k)
    with col5:
        st.metric("Silhouette @ K", f"{results.silhouette_for_k(results.optimal_k):.4f}")

    st.caption(
        f"Config hash: `{results.config.config_hash()}` · PCA components: {results.n_pca_components}"
    )


def methodology_page(results: AnalysisResults):
    st.markdown('<div class="section-header">Methodology</div>', unsafe_allow_html=True)
    st.markdown(
        """
1. **Synthetic panel data** with four latent archetypes (daytime, evening, flat, weekend-heavy).
2. **Panel-aware preprocessing**: sort by consumer/time; impute within consumer only.
3. **Feature engineering**: behavioral shape (normalized load profile, weekend energy ratio, variability) separate from scale.
4. **Standardization**: zero-mean, unit-variance features before PCA.
5. **PCA**: retain components to a documented cumulative-variance threshold (default 95%).
6. **K-Means**: evaluate K=2..10 with inertia, silhouette, Calinski-Harabasz, Davies-Bouldin; select by multi-metric consensus; optional multi-seed stability (ARI).
7. **Profiling and recommendations**: in original feature space; recommendations triggered by measured deviations.
        """
    )
    st.json(
        {
            "feature_set": results.config.feature_set,
            "n_features": len(results.feature_names),
            "pca_components": results.n_pca_components,
            "optimal_k": results.optimal_k,
            "k_range": list(results.config.k_range),
        }
    )


def eda_page(results: AnalysisResults):
    st.markdown('<div class="section-header">Exploratory Data Analysis</div>', unsafe_allow_html=True)
    preprocessed = results.preprocessed_data

    hourly_avg = preprocessed.groupby("hour")["energy_consumption_kwh"].mean()
    fig_hourly = px.line(
        x=hourly_avg.index,
        y=hourly_avg.values,
        labels={"x": "Hour", "y": "Avg kWh"},
        title="Average Hourly Consumption",
    )
    st.plotly_chart(fig_hourly, use_container_width=True)

    weekend_comp = preprocessed.groupby("is_weekend")["energy_consumption_kwh"].mean()
    fig_weekend = px.bar(
        x=["Weekday", "Weekend"],
        y=weekend_comp.values,
        title="Weekday vs Weekend Consumption",
    )
    st.plotly_chart(fig_weekend, use_container_width=True)

    feat = results.features.drop(columns=["consumer_id"], errors="ignore")
    numeric = feat.select_dtypes(include=[np.number])
    corr_cols = [
        c
        for c in numeric.columns
        if c
        in (
            "morning_usage",
            "afternoon_usage",
            "evening_usage",
            "night_usage",
            "weekend_ratio",
            "peak_to_avg_ratio",
            "coefficient_of_variation",
        )
        or c.startswith("hour_")
    ][:12]
    if corr_cols:
        corr = numeric[corr_cols].corr()
        st.plotly_chart(
            px.imshow(corr, text_auto=True, aspect="auto", title="Engineered Feature Correlations (no IDs)"),
            use_container_width=True,
        )


def pca_page(results: AnalysisResults):
    st.markdown('<div class="section-header">PCA</div>', unsafe_allow_html=True)
    pca = results.pca_model
    X_pca = results.pca_transformed

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Components Retained", results.n_pca_components)
    with col2:
        st.metric("Cumulative Variance", f"{np.cumsum(pca.explained_variance_ratio_)[-1]:.2%}")
    with col3:
        st.metric("Input Features", len(results.feature_names))

    fig_var = go.Figure()
    xs = list(range(1, len(pca.explained_variance_ratio_) + 1))
    fig_var.add_trace(go.Bar(x=xs, y=pca.explained_variance_ratio_, name="Individual"))
    fig_var.add_trace(
        go.Scatter(
            x=xs,
            y=np.cumsum(pca.explained_variance_ratio_),
            mode="lines+markers",
            name="Cumulative",
        )
    )
    fig_var.update_layout(title="Explained Variance (from fitted analysis object)")
    st.plotly_chart(fig_var, use_container_width=True)

    if X_pca.shape[1] >= 2:
        fig = px.scatter(
            x=X_pca[:, 0],
            y=X_pca[:, 1],
            opacity=0.6,
            labels={"x": "PC1", "y": "PC2"},
            title="2D PCA Projection",
        )
        st.plotly_chart(fig, use_container_width=True)


def k_selection_page(results: AnalysisResults):
    st.markdown('<div class="section-header">K Selection</div>', unsafe_allow_html=True)

    sil_at_k = results.silhouette_for_k(results.optimal_k)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Selected K", results.optimal_k)
    with col2:
        st.metric("Silhouette @ Selected K", f"{sil_at_k:.4f}")
    with col3:
        st.metric("Cluster Sizes", str(np.bincount(results.cluster_labels).tolist()))

    k_vals = results.k_values
    fig_elbow = px.line(
        x=k_vals,
        y=[results.inertia_by_k[k] for k in k_vals],
        markers=True,
        title="Elbow (Inertia vs K)",
        labels={"x": "K", "y": "Inertia"},
    )
    st.plotly_chart(fig_elbow, use_container_width=True)

    fig_sil = px.line(
        x=k_vals,
        y=[results.silhouette_by_k[k] for k in k_vals],
        markers=True,
        title="Silhouette vs K (dictionary lookup)",
        labels={"x": "K", "y": "Silhouette"},
    )
    fig_sil.add_vline(
        x=results.optimal_k,
        line_dash="dash",
        annotation_text=f"Selected K={results.optimal_k}",
    )
    st.plotly_chart(fig_sil, use_container_width=True)

    if results.pca_transformed.shape[1] >= 2:
        fig = px.scatter(
            x=results.pca_transformed[:, 0],
            y=results.pca_transformed[:, 1],
            color=results.cluster_labels.astype(str),
            title="Clusters (labels from fitted K-Means)",
            labels={"x": "PC1", "y": "PC2", "color": "Cluster"},
            opacity=0.7,
        )
        st.plotly_chart(fig, use_container_width=True)


def profiles_page(results: AnalysisResults):
    st.markdown('<div class="section-header">Cluster Profiles</div>', unsafe_allow_html=True)
    st.dataframe(results.cluster_profiles, use_container_width=True)
    st.dataframe(results.cluster_insights, use_container_width=True)


def recommendations_page(results: AnalysisResults):
    st.markdown(
        '<div class="section-header">Evidence-Based Recommendations</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Each recommendation is triggered by a measured cluster characteristic. No causal savings claims."
    )
    st.dataframe(results.recommendations, use_container_width=True)


def validation_page():
    st.markdown('<div class="section-header">Validation / Ablation</div>', unsafe_allow_html=True)
    report_path = Path(__file__).resolve().parent / "outputs" / "reports" / "ablation_study_report.md"
    if report_path.exists():
        st.markdown(report_path.read_text(encoding="utf-8"))
    else:
        st.warning("Ablation report not found. Run `py src/run_ablation_study.py` offline.")


def limitations_page(results: AnalysisResults):
    st.markdown('<div class="section-header">Limitations</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
- **Synthetic data**: archetypes are designed; real grids may differ. Source labeled as synthetic.
- **Weak separation possible**: behavioral silhouette at K={results.optimal_k} is
  {results.silhouette_for_k(results.optimal_k):.4f} (reported honestly, not inflated).
- **Clustering is not causation**: recommendations are correlational suggestions only.
- **Feature dependence**: results depend on the chosen feature set (see ablation).
- **Generalization**: single synthetic window ({results.config.n_days} days); no multi-season claim.
- **Session safety**: changing sidebar parameters regenerates the full analysis object (hash `{results.config.config_hash()}`).
        """
    )


def main():
    config = build_config_from_sidebar()
    results = get_or_run_analysis(config)

    page = st.sidebar.radio(
        "Navigate",
        [
            "Overview",
            "Methodology",
            "EDA",
            "PCA",
            "K Selection",
            "Cluster Profiles",
            "Recommendations",
            "Validation/Ablation",
            "Limitations",
        ],
    )

    if page == "Overview":
        overview_page(results)
    elif page == "Methodology":
        methodology_page(results)
    elif page == "EDA":
        eda_page(results)
    elif page == "PCA":
        pca_page(results)
    elif page == "K Selection":
        k_selection_page(results)
    elif page == "Cluster Profiles":
        profiles_page(results)
    elif page == "Recommendations":
        recommendations_page(results)
    elif page == "Validation/Ablation":
        validation_page()
    elif page == "Limitations":
        limitations_page(results)


if __name__ == "__main__":
    main()
