"""
Streamlit Dashboard
Interactive dashboard for Energy Consumption Pattern Analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from data_loader import generate_synthetic_data
from preprocessing import preprocess_pipeline
from feature_engineering import engineer_all_features, select_features
from pca_analysis import run_pca_pipeline
from clustering import run_clustering_pipeline
from cluster_profiling import run_cluster_profiling
from evaluation import calculate_clustering_metrics

# Page configuration
st.set_page_config(
    page_title="Energy Consumption Pattern Analysis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        padding: 1rem 0 0.5rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def load_data_sidebar():
    """Sidebar for data loading parameters."""
    st.sidebar.header("Data Parameters")
    
    n_consumers = st.sidebar.slider("Number of Consumers", 50, 500, 200)
    n_days = st.sidebar.slider("Number of Days", 7, 90, 30)
    hourly_records = st.sidebar.checkbox("Hourly Records", value=True)
    
    return n_consumers, n_days, hourly_records


@st.cache_data
def get_processed_data(n_consumers, n_days, hourly_records):
    """Load and process data with caching."""
    synthetic_data = generate_synthetic_data(n_consumers, n_days, hourly_records)
    preprocessed = preprocess_pipeline(synthetic_data)
    features = engineer_all_features(preprocessed)
    return preprocessed, features


def overview_page(preprocessed, features):
    """Overview page with dataset statistics."""
    st.markdown('<div class="main-header">⚡ Energy Consumption Pattern Analysis</div>', 
                unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Dataset Overview</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{len(preprocessed):,}")
    with col2:
        st.metric("Unique Consumers", f"{preprocessed['consumer_id'].nunique()}")
    with col3:
        st.metric("Date Range", f"{preprocessed['timestamp'].min().date()} to {preprocessed['timestamp'].max().date()}")
    with col4:
        st.metric("Avg Consumption", f"{preprocessed['energy_consumption_kwh'].mean():.3f} kWh")
    
    st.markdown('<div class="section-header">Data Sample</div>', unsafe_allow_html=True)
    st.dataframe(preprocessed.head(10), use_container_width=True)
    
    st.markdown('<div class="section-header">Feature Summary</div>', unsafe_allow_html=True)
    st.dataframe(features.describe(), use_container_width=True)


def eda_page(preprocessed):
    """EDA page with visualizations."""
    st.markdown('<div class="section-header">Exploratory Data Analysis</div>', unsafe_allow_html=True)
    
    # Hourly patterns
    st.subheader("Hourly Consumption Patterns")
    hourly_avg = preprocessed.groupby('hour')['energy_consumption_kwh'].mean()
    fig_hourly = px.line(x=hourly_avg.index, y=hourly_avg.values,
                        labels={'x': 'Hour of Day', 'y': 'Avg Consumption (kWh)'},
                        title='Average Hourly Energy Consumption')
    fig_hourly.update_traces(line=dict(width=3), marker=dict(size=8))
    st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Weekday vs Weekend
    st.subheader("Weekday vs Weekend Comparison")
    weekend_comp = preprocessed.groupby('is_weekend')['energy_consumption_kwh'].mean()
    fig_weekend = px.bar(x=['Weekday', 'Weekend'], y=weekend_comp.values,
                        labels={'x': 'Day Type', 'y': 'Avg Consumption (kWh)'},
                        title='Weekday vs Weekend Consumption',
                        color=['Weekday', 'Weekend'])
    st.plotly_chart(fig_weekend, use_container_width=True)
    
    # Distribution
    st.subheader("Consumption Distribution")
    fig_dist = px.histogram(preprocessed, x='energy_consumption_kwh', nbins=50,
                           title='Energy Consumption Distribution')
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # Correlation heatmap
    st.subheader("Feature Correlations")
    numeric_cols = preprocessed.select_dtypes(include=[np.number]).columns
    corr_matrix = preprocessed[numeric_cols].corr()
    fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto",
                        title='Correlation Heatmap')
    st.plotly_chart(fig_corr, use_container_width=True)


def pca_page(features):
    """PCA analysis page."""
    st.markdown('<div class="section-header">PCA Analysis</div>', unsafe_allow_html=True)
    
    # Run PCA
    features_selected = select_features(features)
    X_pca, pca, scaler, n_components = run_pca_pipeline(features_selected)
    
    # Display PCA results
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Components Selected", n_components)
    with col2:
        st.metric("Cumulative Variance", f"{np.cumsum(pca.explained_variance_ratio_)[-1]:.2%}")
    with col3:
        st.metric("Original Features", features_selected.shape[1])
    
    # Explained variance plot
    st.subheader("Explained Variance")
    fig_var = go.Figure()
    fig_var.add_trace(go.Bar(x=list(range(1, len(pca.explained_variance_ratio_) + 1)),
                             y=pca.explained_variance_ratio_,
                             name='Individual Variance'))
    fig_var.add_trace(go.Scatter(x=list(range(1, len(pca.explained_variance_ratio_) + 1)),
                                y=np.cumsum(pca.explained_variance_ratio_),
                                mode='lines+markers',
                                name='Cumulative Variance'))
    fig_var.update_layout(title='Explained Variance by Component',
                         xaxis_title='Principal Component',
                         yaxis_title='Variance Ratio')
    st.plotly_chart(fig_var, use_container_width=True)
    
    # 2D Projection
    if X_pca.shape[1] >= 2:
        st.subheader("2D PCA Projection")
        fig_pca = px.scatter(x=X_pca[:, 0], y=X_pca[:, 1],
                            labels={'x': 'PC1', 'y': 'PC2'},
                            title='2D PCA Projection',
                            opacity=0.6)
        st.plotly_chart(fig_pca, use_container_width=True)
    
    return X_pca


def clustering_page(X_pca):
    """Clustering analysis page."""
    st.markdown('<div class="section-header">K-Means Clustering</div>', unsafe_allow_html=True)
    
    # Run clustering
    kmeans, labels, optimal_k, k_values, inertia_values, silhouette_scores = run_clustering_pipeline(X_pca)
    
    # Display clustering results
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Optimal K", optimal_k)
    with col2:
        st.metric("Silhouette Score", f"{silhouette_scores[optimal_k-2]:.4f}")
    with col3:
        st.metric("Cluster Sizes", str(np.bincount(labels)))
    
    # Elbow curve
    st.subheader("Elbow Curve")
    fig_elbow = px.line(x=k_values, y=inertia_values,
                        labels={'x': 'Number of Clusters (K)', 'y': 'Inertia'},
                        title='Elbow Curve for K Selection',
                        markers=True)
    fig_elbow.update_traces(line=dict(width=3), marker=dict(size=8))
    st.plotly_chart(fig_elbow, use_container_width=True)
    
    # Silhouette scores
    st.subheader("Silhouette Scores")
    fig_sil = px.line(x=k_values, y=silhouette_scores,
                      labels={'x': 'Number of Clusters (K)', 'y': 'Silhouette Score'},
                      title='Silhouette Scores by K',
                      markers=True)
    fig_sil.update_traces(line=dict(width=3), marker=dict(size=8))
    st.plotly_chart(fig_sil, use_container_width=True)
    
    # Cluster visualization
    if X_pca.shape[1] >= 2:
        st.subheader("Cluster Visualization")
        fig_clusters = px.scatter(x=X_pca[:, 0], y=X_pca[:, 1], color=labels,
                                  labels={'x': 'PC1', 'y': 'PC2', 'color': 'Cluster'},
                                  title='2D Cluster Visualization',
                                  opacity=0.7)
        st.plotly_chart(fig_clusters, use_container_width=True)
    
    return labels


def cluster_insights_page(features, labels):
    """Cluster insights page."""
    st.markdown('<div class="section-header">Cluster Insights & Recommendations</div>', unsafe_allow_html=True)
    
    # Run cluster profiling
    profiles, insights = run_cluster_profiling(features, labels)
    
    # Display cluster profiles
    st.subheader("Cluster Profiles")
    st.dataframe(profiles, use_container_width=True)
    
    # Display insights
    st.subheader("Cluster Interpretations & Recommendations")
    
    for _, row in insights.iterrows():
        with st.expander(f"Cluster {int(row['cluster'])} - {row['interpretation']}"):
            st.write("**Recommendations:**")
            recommendations = row['recommendations'].split('; ')
            for rec in recommendations:
                st.write(f"• {rec}")
    
    # Evaluation metrics
    st.subheader("Clustering Evaluation Metrics")
    from feature_engineering import select_features
    features_selected = select_features(features)
    from pca_analysis import standardize_features
    X_scaled, _ = standardize_features(features_selected)
    from sklearn.decomposition import PCA
    pca_temp = PCA(n_components=6)
    X_pca_temp = pca_temp.fit_transform(X_scaled)
    
    metrics = calculate_clustering_metrics(X_pca_temp, labels)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Silhouette Score", f"{metrics['silhouette_score']:.4f}")
    with col2:
        st.metric("Calinski-Harabasz", f"{metrics['calinski_harabasz_score']:.2f}")
    with col3:
        st.metric("Davies-Bouldin", f"{metrics['davies_bouldin_score']:.4f}")
    with col4:
        st.metric("Inertia", f"{metrics['inertia']:.2f}")


def main():
    """Main application."""
    # Sidebar
    n_consumers, n_days, hourly_records = load_data_sidebar()
    
    # Load data
    with st.spinner("Loading and processing data..."):
        preprocessed, features = get_processed_data(n_consumers, n_days, hourly_records)
    
    # Page navigation
    page = st.sidebar.radio("Navigate", ["Overview", "EDA", "PCA", "Clustering", "Cluster Insights"])
    
    if page == "Overview":
        overview_page(preprocessed, features)
    elif page == "EDA":
        eda_page(preprocessed)
    elif page == "PCA":
        X_pca = pca_page(features)
        st.session_state['X_pca'] = X_pca
    elif page == "Clustering":
        if 'X_pca' not in st.session_state:
            features_selected = select_features(features)
            X_pca, _, _, _ = run_pca_pipeline(features_selected)
            st.session_state['X_pca'] = X_pca
        labels = clustering_page(st.session_state['X_pca'])
        st.session_state['labels'] = labels
    elif page == "Cluster Insights":
        if 'labels' not in st.session_state:
            features_selected = select_features(features)
            X_pca, _, _, _ = run_pca_pipeline(features_selected)
            _, labels, _, _, _, _ = run_clustering_pipeline(X_pca)
            st.session_state['labels'] = labels
        cluster_insights_page(features, st.session_state['labels'])


if __name__ == "__main__":
    main()
