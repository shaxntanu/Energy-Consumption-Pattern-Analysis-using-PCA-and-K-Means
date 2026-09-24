"""
Export the flagship synthetic dataset for Kaggle upload.

This script generates the exact 365-day, 200-consumer dataset used in the
flagship experiment (config hash: 99c7a6631340d301) and exports it with
comprehensive documentation for Kaggle.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

import pandas as pd
import numpy as np
import json
from datetime import datetime

from data_loader import generate_synthetic_data, SeasonalConfig


def export_kaggle_dataset():
    """Generate and export the flagship dataset to kaggle/dataset/"""
    
    print("=" * 70)
    print("KAGGLE DATASET EXPORT - Flagship Configuration")
    print("=" * 70)
    
    # Flagship configuration (matches models/analysis_metadata.json)
    config = {
        'n_consumers': 200,
        'n_days': 365,
        'start_date': '2024-01-01',
        'random_seed': 42,
        'hourly_records': True,
        'seasonal': SeasonalConfig(
            enabled=True,
            annual_amplitude=0.25,
            shape_shift_hours=1.0,
            hemisphere='northern',
            phase_std_days=20.0,
            participation=0.9
        )
    }
    
    print(f"\nGenerating synthetic dataset...")
    print(f"  Consumers: {config['n_consumers']}")
    print(f"  Days: {config['n_days']}")
    print(f"  Period: {config['start_date']} to 2024-12-30")
    print(f"  Seed: {config['random_seed']}")
    print(f"  Seasonal: Enabled")
    
    # Generate data
    df = generate_synthetic_data(
        n_consumers=config['n_consumers'],
        n_days=config['n_days'],
        start_date=config['start_date'],
        hourly_records=config['hourly_records'],
        random_seed=config['random_seed'],
        seasonal=config['seasonal']
    )
    
    print(f"\nGenerated {len(df):,} records")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    
    # Create output directory
    output_dir = project_root / 'kaggle' / 'dataset'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export main dataset (DROP archetype and seasonal_phase - they're ground truth for validation only)
    dataset_df = df[['consumer_id', 'timestamp', 'energy_consumption_kwh', 'season']].copy()
    
    # Also save a separate ground truth file for validation purposes
    ground_truth_df = df[['consumer_id', 'archetype']].drop_duplicates().sort_values('consumer_id')
    
    dataset_path = output_dir / 'energy_consumption_hourly.csv'
    ground_truth_path = output_dir / 'ground_truth_archetypes.csv'
    
    print(f"\nExporting dataset files...")
    dataset_df.to_csv(dataset_path, index=False)
    ground_truth_df.to_csv(ground_truth_path, index=False)
    
    print(f"  {dataset_path.name} ({len(dataset_df):,} rows)")
    print(f"  {ground_truth_path.name} ({len(ground_truth_df)} consumers)")
    
    # Validation
    print(f"\nValidation:")
    print(f"  Unique consumers: {dataset_df['consumer_id'].nunique()}")
    print(f"  Date range: {dataset_df['timestamp'].min()} to {dataset_df['timestamp'].max()}")
    print(f"  Missing values: {dataset_df.isnull().sum().sum()}")
    print(f"  Duplicate rows: {dataset_df.duplicated().sum()}")
    print(f"  Energy range: {dataset_df['energy_consumption_kwh'].min():.4f} to {dataset_df['energy_consumption_kwh'].max():.4f} kWh")
    print(f"  Archetypes: {ground_truth_df['archetype'].value_counts().to_dict()}")
    
    # Create metadata
    metadata = {
        "name": "Household Energy Consumption - Synthetic Behavioral Dataset",
        "version": "1.0.0",
        "dataset_type": "synthetic",
        "generation_date": datetime.utcnow().isoformat() + "Z",
        "source_repository": "https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means",
        "release": "v1.0.0",
        "config_hash": "99c7a6631340d301",
        "dimensions": {
            "consumers": int(config['n_consumers']),
            "observations": int(len(dataset_df)),
            "time_resolution": "hourly",
            "observation_period_days": int(config['n_days']),
            "start_date": config['start_date'],
            "end_date": "2024-12-30"
        },
        "schema": {
            "consumer_id": {"type": "int64", "description": "Unique household identifier (0-199)"},
            "timestamp": {"type": "datetime64", "description": "Hourly timestamp (UTC)"},
            "energy_consumption_kwh": {"type": "float64", "description": "Energy consumption in kilowatt-hours"},
            "season": {"type": "string", "description": "Season derived from Zephyr Station weather data (spring/summer/fall/winter)"}
        },
        "ground_truth": {
            "available": True,
            "file": "ground_truth_archetypes.csv",
            "description": "Hidden behavioral archetypes used only for external validation (flat, daytime, evening, weekend)",
            "archetypes": {
                "flat": "Uniform consumption across all hours",
                "daytime": "Peak consumption 9am-5pm",
                "evening": "Peak consumption 5pm-10pm",
                "weekend": "Increased weekend consumption"
            }
        },
        "generation": {
            "method": "Controlled synthetic generation with realistic temporal dynamics",
            "generator": "src/data_loader.py::generate_synthetic_data_archetype_based",
            "random_seed": config['random_seed'],
            "seasonal_model": "Enabled with 25% amplitude variation",
            "noise": "Gaussian noise with 10% standard deviation"
        },
        "intended_uses": [
            "Unsupervised clustering and behavioral segmentation",
            "Principal Component Analysis (PCA) benchmarking",
            "Time-series pattern discovery",
            "Smart grid load profiling",
            "Explainable AI (XAI) demonstrations",
            "Reproducible machine learning research"
        ],
        "limitations": [
            "Synthetic data - not real household measurements",
            "Four predefined archetypes may not capture all real-world patterns",
            "Seasonal model is simplified (single sinusoidal component)",
            "No appliance-level granularity",
            "Uniform hourly sampling (no sub-hourly dynamics)"
        ],
        "license": "MIT",
        "citation": {
            "text": "Shantanu. (2026). Shape-First Behavioral Segmentation of Household Energy Consumption. https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means",
            "bibtex": "@misc{shantanu2026energy,\\n  author = {Shantanu},\\n  title = {Shape-First Behavioral Segmentation of Household Energy Consumption},\\n  year = {2026},\\n  publisher = {GitHub},\\n  url = {https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means}\\n}"
        }
    }
    
    metadata_path = output_dir / 'dataset_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  {metadata_path.name}")
    
    # Create README
    readme_content = f"""# Household Energy Consumption - Synthetic Behavioral Dataset

## Overview

This dataset contains **synthetic hourly energy consumption data** for 200 households over a full year (365 days), designed for unsupervised learning, clustering, and behavioral pattern analysis. The data mimics realistic temporal dynamics including diurnal cycles, weekend effects, and seasonal variations.

**WARNING: This is synthetically generated data, NOT real household measurements.**

## Dataset Specifications

| Property | Value |
|----------|-------|
| **Type** | Synthetic (controlled generation) |
| **Consumers** | 200 households |
| **Observations** | {len(dataset_df):,} hourly records |
| **Time Period** | January 1, 2024 - December 30, 2024 (365 days) |
| **Resolution** | Hourly |
| **File Format** | CSV (UTF-8) |
| **Size** | ~{dataset_path.stat().st_size / 1024 / 1024:.1f} MB |

## Files

### 1. `energy_consumption_hourly.csv` (Main Dataset)

The primary dataset with {len(dataset_df):,} hourly consumption records.

| Column | Type | Description |
|--------|------|-------------|
| `consumer_id` | int64 | Unique household identifier (0-199) |
| `timestamp` | datetime64 | Hourly timestamp in UTC |
| `energy_consumption_kwh` | float64 | Energy consumption in kilowatt-hours |
| `season` | string | Season (spring/summer/fall/winter) from Zephyr Station weather API |

**Sample:**
```
consumer_id,timestamp,energy_consumption_kwh,season
0,2024-01-01 00:00:00,1.234,winter
0,2024-01-01 01:00:00,0.987,winter
1,2024-01-01 00:00:00,2.156,winter
...
```

### 2. `ground_truth_archetypes.csv` (Validation Labels)

Hidden behavioral archetypes for external validation purposes only. **These labels are NOT used during clustering** - they exist only to validate that unsupervised methods can recover the true groupings.

| Column | Type | Description |
|--------|------|-------------|
| `consumer_id` | int64 | Household identifier |
| `archetype` | string | Behavioral pattern (flat/daytime/evening/weekend) |

**Archetypes:**
- **flat**: Uniform consumption throughout the day
- **daytime**: Peak consumption during 9am-5pm (business hours)
- **evening**: Peak consumption during 5pm-10pm (residential peak)
- **weekend**: Increased weekend consumption with shifted patterns

## Generation Method

The dataset is generated using a controlled synthetic model implemented in `src/data_loader.py`:

```
E(consumer, hour) = baseline x diurnal(hour) x weekend(day) x seasonal(date) x (1 + noise)
```

**Components:**
- **Baseline**: Per-consumer average consumption (uniform distribution)
- **Diurnal cycle**: Hourly pattern specific to behavioral archetype
- **Weekend factor**: 15% increase on Saturdays and Sundays
- **Seasonal model**: Sinusoidal variation with 25% amplitude over the year
- **Noise**: Gaussian noise (10% std) for realistic variability

**Reproducibility:**
- Random seed: `42`
- Configuration hash: `99c7a6631340d301`
- Generator: `data_loader.py::generate_synthetic_data_archetype_based`

## Intended Uses

This dataset is designed for:

- **Unsupervised clustering** - Discover behavioral patterns without labels  
- **PCA/dimensionality reduction** - Test variance-preserving transformations  
- **Time-series analysis** - Hourly temporal pattern discovery  
- **Explainable AI (XAI)** - SHAP/LIME feature importance demonstrations  
- **Smart grid analytics** - Load profiling and demand response research  
- **Reproducible research** - Controlled experiments with known ground truth  

## Limitations

- **Not real data** - Synthetic generation may not capture all real-world complexities  
- **Fixed archetypes** - Only 4 behavioral patterns (real households are more diverse)  
- **Simplified seasonal model** - Single sinusoid (real patterns have multiple cycles)  
- **No appliance breakdown** - Aggregated household consumption only  
- **No socioeconomic factors** - Income, household size, building characteristics not modeled  
- **Uniform sampling** - Hourly resolution (no sub-hourly dynamics or missing data)  

## Validation Results

When this exact dataset is processed through the full pipeline:

- **Optimal K**: 4 clusters (evidence-based selection)
- **Silhouette Score**: 0.328
- **ARI vs Ground Truth**: 0.813 (strong archetype recovery)
- **Stability ARI**: 0.995 (highly stable across re-runs)
- **PCA Components**: 10 (95% variance retained)

See the [full project repository](https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means) for complete analysis and interactive visualization.

## Related Resources

- **Interactive Explorer**: https://energy-consumption-pattern.vercel.app
- **Streamlit Simulator**: https://energy-consumption-pattern-vqrh.streamlit.app/
- **Source Code**: https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means
- **Presentation**: [Google Slides](https://docs.google.com/presentation/d/1MDuqluVIVA2VCmYWPoI2TEvCN6ZLHZWgzFX1eGzS4PQ/edit)
- **Weather API**: [Zephyr Station](https://github.com/shaxntanu/Zephyr-Station) (source of season data)

## License

This dataset is released under the **MIT License**, consistent with the source repository.

```
MIT License

Copyright (c) 2026 Shantanu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Citation

If you use this dataset in your research or project, please cite:

**Text:**
```
Shantanu. (2026). Household Energy Consumption - Synthetic Behavioral Dataset.
GitHub. https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means
```

**BibTeX:**
```bibtex
@misc{{shantanu2026energy,
  author = {{Shantanu}},
  title = {{Shape-First Behavioral Segmentation of Household Energy Consumption}},
  year = {{2026}},
  publisher = {{GitHub}},
  url = {{https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means}},
  note = {{Flagship configuration: 99c7a6631340d301}}
}}
```

## Quick Start

```python
import pandas as pd

# Load main dataset
df = pd.read_csv('energy_consumption_hourly.csv', parse_dates=['timestamp'])

# Load ground truth (for validation only)
archetypes = pd.read_csv('ground_truth_archetypes.csv')

# Basic exploration
print(f"Shape: {{df.shape}}")
print(f"Consumers: {{df['consumer_id'].nunique()}}")
print(f"Date range: {{df['timestamp'].min()}} to {{df['timestamp'].max()}}")

# Aggregate to daily
daily = df.groupby(['consumer_id', df['timestamp'].dt.date])['energy_consumption_kwh'].sum()

# Compute hourly load shape per consumer
hourly_shape = df.pivot_table(
    values='energy_consumption_kwh',
    index='consumer_id',
    columns=df['timestamp'].dt.hour,
    aggfunc='mean'
)
```

## Contact

**Author**: Shantanu  
**Email**: shxntanu@gmail.com  
**ORCID**: [0009-0008-4403-0670](https://orcid.org/0009-0008-4403-0670)  
**GitHub**: [@shaxntanu](https://github.com/shaxntanu)

For questions, issues, or contributions, please open an issue on the [GitHub repository](https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means/issues).

---

**Dataset Version**: 1.0.0  
**Release Date**: {datetime.now().strftime('%Y-%m-%d')}  
**Configuration Hash**: 99c7a6631340d301  
**Generator**: `data_loader.py::generate_synthetic_data`
"""
    
    readme_path = output_dir / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"  {readme_path.name}")
    
    # Copy LICENSE
    license_source = project_root / 'LICENSE'
    license_dest = output_dir / 'LICENSE'
    if license_source.exists():
        license_dest.write_text(license_source.read_text())
        print(f"  {license_dest.name}")
    
    print(f"\n{'=' * 70}")
    print(f"Kaggle dataset package created successfully!")
    print(f"{'=' * 70}")
    print(f"\nLocation: {output_dir.relative_to(project_root)}/")
    print(f"\nContents:")
    for file in sorted(output_dir.iterdir()):
        size = file.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / 1024 / 1024:.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        print(f"  - {file.name:40s} {size_str:>10s}")
    
    print(f"\nReady for Kaggle upload:")
    print(f"   1. Navigate to: https://www.kaggle.com/datasets")
    print(f"   2. Click 'New Dataset'")
    print(f"   3. Upload the entire 'kaggle/dataset/' folder")
    print(f"   4. Title: 'Household Energy Consumption - Synthetic Behavioral Dataset'")
    print(f"   5. Subtitle: 'Hourly energy data for 200 households with behavioral archetypes'")
    
    return output_dir


if __name__ == '__main__':
    try:
        output_dir = export_kaggle_dataset()
        print(f"\nSuccess! Dataset exported to: {output_dir}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
