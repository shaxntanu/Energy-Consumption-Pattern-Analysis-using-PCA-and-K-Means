# Required Figures for Scientific Reports Paper

This document lists all figures referenced in `paper_scientific_reports.tex` with specifications for generation.

## 📊 Figure List (7 Figures Total)

### Figure 1: Sample Time Series
**File**: `outputs/figures/sample_time_series.png`  
**Location**: Section 2.1 (Methods - Dataset)  
**Label**: `fig:sample_timeseries`  
**Specifications**:
- Width: 0.8\textwidth
- Content: Three representative household time series over one week
- X-axis: Time (hourly, 7 days = 168 hours)
- Y-axis: Energy consumption (kWh)
- Elements:
  - Three colored lines (one per household)
  - Show diurnal patterns (day/night cycles)
  - Highlight weekend effect (days 6-7)
  - Legend with household IDs
- Purpose: Demonstrate synthetic data realism and temporal variability

**Generation script**: `scripts/generate_figures.py::plot_sample_timeseries()`

---

### Figure 2: PCA Scree Plot
**File**: `outputs/figures/pca_scree_plot.png`  
**Location**: Section 4.1 (Results - PCA)  
**Label**: `fig:pca_scree`  
**Specifications**:
- Width: 0.9\textwidth
- Content: Explained variance by principal component
- X-axis: Component number (1-15)
- Y-axis: Explained variance ratio (%)
- Elements:
  - Bar chart with explained variance per component
  - Line plot showing cumulative variance
  - Vertical dashed line at component 6 (95.6% threshold)
  - Annotations: PC1 (65.3%), cumulative at PC6 (95.6%)
- Purpose: Justify dimensionality reduction to 6 components

**Data source**: `baseline/metrics/pca_results.csv`  
**Generation script**: `scripts/generate_figures.py::plot_pca_scree()`

---

### Figure 3: Cluster Validation Metrics
**File**: `outputs/figures/cluster_validation_metrics.png`  
**Location**: Section 4.2 (Results - Cluster Validation)  
**Label**: `fig:validation_metrics`  
**Specifications**:
- Width: 0.9\textwidth (3 subplots)
- Content: Three validation metrics vs K
- Subplots (a, b, c):
  - (a) Silhouette score vs K (2-6)
  - (b) Calinski-Harabasz index vs K
  - (c) Davies-Bouldin index vs K
- X-axis: Number of clusters K
- Y-axis: Metric value
- Elements:
  - Line plots with markers
  - Optimal K=3 highlighted (vertical line or marker)
  - Grid for readability
- Purpose: Show convergence of metrics at K=3

**Data source**: Multiple K runs or `baseline/metrics/clustering_metrics.csv`  
**Generation script**: `scripts/generate_figures.py::plot_validation_metrics()`

---

### Figure 4: Cluster Scatter Plot
**File**: `outputs/figures/cluster_scatter_pc1_pc2.png`  
**Location**: Section 4.3 (Results - Cluster Characterization)  
**Label**: `fig:cluster_scatter`  
**Specifications**:
- Width: 0.9\textwidth
- Content: 2D projection of clusters in PC1-PC2 space
- X-axis: Principal Component 1 (65.3% variance)
- Y-axis: Principal Component 2 (10.8% variance)
- Elements:
  - Scatter points colored by cluster (3 colors)
  - Large markers for cluster centroids
  - Legend: Cluster 0 (30%), Cluster 1 (45%), Cluster 2 (25%)
  - Semi-transparent points for overlap visibility
  - Axis labels with explained variance
- Purpose: Visualize cluster separation and overlap

**Data source**: PCA-transformed data + cluster labels from `baseline/models/`  
**Generation script**: `scripts/generate_figures.py::plot_cluster_scatter()`

---

### Figure 5: Cluster Feature Heatmap
**File**: `outputs/figures/cluster_feature_heatmap.png`  
**Location**: Section 4.3 (Results - Cluster Characterization)  
**Label**: `fig:cluster_heatmap`  
**Specifications**:
- Width: 0.9\textwidth
- Content: Feature comparison across clusters
- Rows: 15 features (standardized z-scores)
- Columns: 3 clusters (0, 1, 2)
- Colormap: Blue (below mean) → White (mean) → Red (above mean)
- Elements:
  - Annotated cells with z-score values
  - Feature categories marked (Level, Variability, Temporal)
  - Colorbar with scale
- Purpose: Compare cluster profiles across all features

**Data source**: `baseline/reports/cluster_profiles.csv` (standardized)  
**Generation script**: `scripts/generate_figures.py::plot_cluster_heatmap()`

---

### Figure 6: Time-of-Use Profiles
**File**: `outputs/figures/time_of_use_profiles.png`  
**Location**: Section 4.4 (Results - Temporal Patterns)  
**Label**: `fig:time_of_use`  
**Specifications**:
- Width: 0.9\textwidth
- Content: Average hourly consumption by cluster
- X-axis: Hour of day (0-23)
- Y-axis: Average consumption (kWh)
- Elements:
  - Three colored lines (one per cluster)
  - Shaded regions: ±1 std deviation
  - Vertical shaded bands for time periods (morning, afternoon, evening, night)
  - Legend: Cluster labels with mean consumption
  - Grid for readability
- Purpose: Show similar temporal patterns across clusters

**Data source**: Raw hourly data grouped by cluster  
**Generation script**: `scripts/generate_figures.py::plot_time_of_use()`

---

### Figure 7: Silhouette Analysis
**File**: `outputs/figures/silhouette_analysis.png`  
**Location**: Section 4.4 (Results - Temporal Patterns)  
**Label**: `fig:silhouette`  
**Specifications**:
- Width: 0.9\textwidth
- Content: Silhouette coefficients for all households
- X-axis: Silhouette coefficient (-1 to 1)
- Y-axis: Household index (grouped by cluster)
- Elements:
  - Horizontal bars colored by cluster
  - Vertical dashed line at overall average (0.312)
  - Cluster separators (horizontal lines)
  - Cluster labels on y-axis
  - Sorted within each cluster by coefficient
- Purpose: Visualize within-cluster cohesion and between-cluster separation

**Data source**: Silhouette scores from sklearn  
**Generation script**: `scripts/generate_figures.py::plot_silhouette_analysis()`

---

### Figure 8: Computational Speedup (Optional)
**File**: `outputs/figures/computational_speedup.png`  
**Location**: Section 2.6 (Methods - Software Implementation)  
**Label**: `fig:speedup`  
**Specifications**:
- Width: 0.8\textwidth
- Content: C++ vs Python performance comparison
- X-axis: Dataset size (households, log scale)
- Y-axis: Speedup factor (×)
- Elements:
  - Two line plots: PCA speedup, K-means speedup
  - Error bars (±1 std over 10 runs)
  - Horizontal dashed line at 1× (baseline)
  - Legend
  - Annotations at key points (e.g., 10K households: 8.5×)
- Purpose: Demonstrate scalability of C++ engine

**Data source**: Benchmark results (to be generated)  
**Generation script**: `scripts/benchmark_cpp.py` → `scripts/generate_figures.py::plot_speedup()`

---

## 🎨 Style Guidelines

All figures should follow these specifications:

### General
- **DPI**: 300 (publication quality)
- **Format**: PNG (with transparency if needed)
- **Font**: Default matplotlib (DejaVu Sans) or Arial, size 10-12pt
- **Line width**: 1.5-2pt for main lines, 1pt for grid
- **Marker size**: 6-8pt

### Colors
Use colorblind-friendly palette:
- **Cluster 0**: `#1f77b4` (blue)
- **Cluster 1**: `#ff7f0e` (orange)
- **Cluster 2**: `#2ca02c` (green)
- **Grid**: `#cccccc` (light gray)
- **Highlights**: `#d62728` (red)

### Layout
- Tight layout to maximize figure area
- Legends: upper right or best position
- Axis labels: clear and units specified
- Titles: Optional (caption provides context)

---

## 📝 Generation Script Template

Create `paper/scripts/generate_figures.py`:

```python
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("colorblind")

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
METRICS_DIR = BASE_DIR / "baseline" / "metrics"
REPORTS_DIR = BASE_DIR / "baseline" / "reports"
MODELS_DIR = BASE_DIR / "baseline" / "models"
OUTPUT_DIR = BASE_DIR / "outputs" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def plot_sample_timeseries():
    """Figure 1: Sample time series"""
    # Load data and plot
    # ...
    plt.savefig(OUTPUT_DIR / "sample_time_series.png", dpi=300, bbox_inches='tight')
    plt.close()

def plot_pca_scree():
    """Figure 2: PCA scree plot"""
    df = pd.read_csv(METRICS_DIR / "pca_results.csv")
    # Create plot
    # ...
    plt.savefig(OUTPUT_DIR / "pca_scree_plot.png", dpi=300, bbox_inches='tight')
    plt.close()

# ... more functions ...

if __name__ == "__main__":
    print("Generating all figures...")
    plot_sample_timeseries()
    plot_pca_scree()
    plot_validation_metrics()
    plot_cluster_scatter()
    plot_cluster_heatmap()
    plot_time_of_use()
    plot_silhouette_analysis()
    # plot_speedup()  # Optional
    print("Done! All figures saved to outputs/figures/")
```

---

## ✅ Checklist

Before compiling the paper:

- [ ] All 7 required figures generated
- [ ] Figures match specified dimensions (0.8-0.9\textwidth)
- [ ] DPI is 300 for publication quality
- [ ] File paths in LaTeX match actual files
- [ ] Figures referenced correctly with `\ref{fig:label}`
- [ ] Captions are descriptive and stand-alone
- [ ] Color scheme is colorblind-friendly
- [ ] All axis labels include units
- [ ] Legends are clear and positioned well

---

## 🔧 Quick Generation

```bash
# Generate all figures
cd paper/scripts/
python generate_figures.py

# Verify outputs
ls -lh ../../outputs/figures/

# Compile paper
cd ../
pdflatex paper_scientific_reports.tex
```

---

**Note**: Figures 1-7 are **required** for the paper to compile correctly. Figure 8 (speedup) is optional and can be commented out if benchmark data is unavailable.

**Last Updated**: 2026-09-24
