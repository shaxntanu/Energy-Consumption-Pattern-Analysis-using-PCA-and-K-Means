# Energy Consumption Pattern Analysis - Kaggle Notebook

This directory contains a Kaggle-compatible notebook for analyzing household energy consumption patterns using PCA and K-Means clustering.

## Overview

```plantuml
@startuml
skinparam backgroundColor #f8f9fa
skinparam activityBackgroundColor #48d7c2
skinparam activityBorderColor #48d7c2
skinparam activityFontColor #1a1a1a
skinparam noteBackgroundColor #e3f2fd
skinparam noteBorderColor #2196f3
skinparam noteFontColor #1a1a1a

start
:**Data Loading**;
note right
  energy_consumption_hourly.csv
  ground_truth_archetypes.csv
end note

:**Exploration**;
note right
  Statistics
  Load shapes
  Distributions
end note

:**Feature Engineering**;
note right
  Scale features (6)
  Shape features (24)
  Summary features (3)
  Behavioral features (5)
  Combined (38)
end note

:**PCA**;
note right
  StandardScaler
  95% variance threshold
  Dimensionality reduction
end note

:**K-Means Clustering**;
note right
  K = 2..10
  Silhouette optimization
  Stability check
end note

:**Validation**;
note right
  ARI vs archetypes
  NMI
  Cross-tabulation
end note

:**Profiling**;
note right
  Cluster characteristics
  Load shapes
  Naming
end note

:**Explainability**;
note right
  Permutation importance
  Feature ranking
end note

:**Ablation Study**;
note right
  Compare feature sets
  Scale vs Shape vs Behavioral
end note

:**Longitudinal**;
note right
  Time segments
  Temporal stability
end note

stop
@enduml
```

## Contents

- **`energy_consumption_clustering.ipynb`**: Complete analysis notebook covering:
  - Data loading and exploration
  - Feature engineering (scale, shape, summary, behavioral features)
  - Principal Component Analysis (PCA)
  - K-Means clustering with K-selection
  - Cluster validation using Adjusted Rand Index (ARI)
  - Cluster profiling and interpretation
  - Explainability using permutation importance
  - Ablation study comparing feature sets
  - Longitudinal analysis for temporal stability

- **`dataset/`**: Synthetic dataset directory
  - `energy_consumption_hourly.csv`: Hourly energy consumption data
  - `ground_truth_archetypes.csv`: Ground truth labels for validation
  - `README.md`: Detailed dataset documentation
  - `dataset_metadata.json`: Dataset metadata
  - `LICENSE`: Dataset license

## Usage on Kaggle

1. Create a new Kaggle dataset using the files in `dataset/`
2. Upload the notebook to Kaggle
3. Link the dataset to the notebook
4. Run the notebook end-to-end

## Key Features

- **Self-contained**: All feature engineering and analysis logic is included in the notebook
- **Visualizations**: Multiple plots for data exploration, clustering results, and validation
- **Validation**: Uses ground truth archetypes to measure clustering quality
- **Explainability**: Identifies which features drive cluster assignments
- **Robustness Analysis**: Includes ablation study and longitudinal stability checks

## Requirements

The notebook requires the following Python packages:
- numpy
- pandas
- matplotlib
- seaborn
- scikit-learn

These are typically available in Kaggle's default environment.

## Dataset Details

The synthetic dataset contains:
- 200 consumers
- 30 days of hourly energy consumption records
- 5 hidden archetypes for validation

See `dataset/README.md` for more details.

## Note

This notebook is a simplified version of the full pipeline in the `src/` directory. For production use or more advanced analyses (seed robustness, detailed reports), refer to the main project scripts.
