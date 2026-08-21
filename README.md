# Energy Consumption Pattern Analysis using PCA and K-Means

Repository for MINI Project for AI-ML For Engineers

## Overview

This project analyzes energy consumption patterns using Principal Component Analysis (PCA) for dimensionality reduction and K-Means clustering to identify distinct consumer usage patterns. The analysis provides data-driven insights for energy optimization strategies.

## Project Structure

```
energy-pattern-analysis/
├── data/
│   ├── raw/                    # Raw data files
│   └── processed/              # Processed data files
├── notebooks/                  # Jupyter notebooks for exploration
├── src/                        # Source code modules
│   ├── data_loader.py         # Data loading and synthetic data generation
│   ├── preprocessing.py       # Data cleaning and preprocessing
│   ├── feature_engineering.py # Feature engineering
│   ├── eda.py                 # Exploratory data analysis
│   ├── pca_analysis.py        # PCA dimensionality reduction
│   ├── clustering.py          # K-Means clustering
│   ├── evaluation.py          # Clustering evaluation metrics
│   └── cluster_profiling.py   # Cluster profiling and recommendations
├── models/                     # Saved models (scaler, PCA, K-Means)
├── outputs/
│   ├── figures/               # Generated visualizations
│   ├── metrics/               # Evaluation metrics
│   └── reports/               # Analysis reports
├── app/
│   └── app.py                 # Streamlit dashboard
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Installation

### Prerequisites

- Python 3.14 or higher
- pip package manager

### Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means
```

2. Install dependencies:
```bash
py -m pip install -r requirements.txt
```

## Usage

### Running Individual Components

Each component can be run independently for testing:

```bash
# Data loading
py src/data_loader.py

# Preprocessing
py src/preprocessing.py

# Feature engineering
py src/feature_engineering.py

# EDA
py src/eda.py

# PCA analysis
py src/pca_analysis.py

# Clustering
py src/clustering.py

# Evaluation
py src/evaluation.py

# Cluster profiling
py src/cluster_profiling.py
```

### Running the Streamlit Dashboard

Launch the interactive dashboard:

```bash
py -m streamlit run app/app.py
```

The dashboard will be available at `http://localhost:8501`

### Dashboard Pages

1. **Overview**: Dataset statistics and summary
2. **EDA**: Exploratory data analysis with visualizations
3. **PCA**: Principal Component Analysis results
4. **Clustering**: K-Means clustering analysis
5. **Cluster Insights**: Cluster profiles and optimization recommendations

## Pipeline Overview

The analysis follows this pipeline:

1. **Data Engineering**: Load/clean data, handle missing values, parse timestamps
2. **Feature Engineering**: Create behavioral features (consumption patterns, temporal features, load variability)
3. **EDA**: Analyze distributions, patterns, correlations
4. **PCA**: Standardize features, apply PCA, select components based on explained variance
5. **Clustering**: Test K=2..10, select optimal K using silhouette score and elbow method
6. **Evaluation**: Calculate clustering quality metrics
7. **Cluster Profiling**: Profile clusters, generate interpretations and recommendations

## Key Features

- **Synthetic Data Generation**: Realistic energy consumption data with temporal patterns
- **Comprehensive Preprocessing**: Missing value handling, outlier detection, timestamp parsing
- **Rich Feature Engineering**: 18+ behavioral features including temporal patterns and load variability
- **PCA Dimensionality Reduction**: Automatic component selection based on variance threshold
- **Optimal K Selection**: Combines silhouette score and elbow method for robust K selection
- **Cluster Intelligence**: Evidence-based interpretations and optimization recommendations
- **Interactive Dashboard**: Streamlit-based visualization and exploration

## Technical Stack

- Python 3.14
- Pandas, NumPy
- Scikit-learn
- Matplotlib, Seaborn, Plotly
- Streamlit
- Joblib

## Data Format

The project expects energy consumption data with the following columns:
- `consumer_id`: Unique identifier for each consumer/building
- `timestamp`: DateTime of the measurement
- `energy_consumption_kwh`: Energy consumption in kilowatt-hours
- `voltage_v`: Voltage in volts
- `current_a`: Current in amperes
- `power_factor`: Power factor (0-1)
- `temperature_c`: Temperature in Celsius

## Output Files

- `outputs/figures/`: All visualization plots (PNG format)
- `outputs/metrics/`: PCA results, clustering metrics, evaluation scores
- `outputs/reports/`: Statistical summaries, cluster profiles, insights
- `models/`: Saved scaler, PCA model, K-Means model, cluster labels

## Academic Integrity

This project follows strict academic integrity guidelines:
- All results are generated from actual code execution
- No fabricated statistics, PCA variance, silhouette scores, or cluster sizes
- Synthetic data is clearly identified as synthetic
- Recommendations are evidence-based and avoid unsupported causal claims

## License

See LICENSE file for details.

## Build Instructions

See `Build Instructions/` directory for detailed project requirements and development documentation:
- `01_Project_PRD.md`: Product Requirements Document
- `02_Five_Component_Development_Document.md`: Component breakdown
- `03_Cursor_Master_Prompt.md`: Development guidelines
