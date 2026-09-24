# Household Energy Consumption - Synthetic Behavioral Dataset

## Overview

This dataset contains **synthetic hourly energy consumption data** for 200 households over a full year (365 days), designed for unsupervised learning, clustering, and behavioral pattern analysis. The data mimics realistic temporal dynamics including diurnal cycles, weekend effects, and seasonal variations.

**WARNING: This is synthetically generated data, NOT real household measurements.**

## Dataset Specifications

| Property | Value |
|----------|-------|
| **Type** | Synthetic (controlled generation) |
| **Consumers** | 200 households |
| **Observations** | 1,752,000 hourly records |
| **Time Period** | January 1, 2024 - December 30, 2024 (365 days) |
| **Resolution** | Hourly |
| **File Format** | CSV (UTF-8) |
| **Size** | ~83.9 MB |

## Files

### 1. `energy_consumption_hourly.csv` (Main Dataset)

The primary dataset with 1,752,000 hourly consumption records.

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
E(consumer, hour) = baseline × diurnal(hour) × weekend(day) × seasonal(date) × (1 + noise)
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
@misc{shantanu2026energy,
  author = {Shantanu},
  title = {Shape-First Behavioral Segmentation of Household Energy Consumption},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means},
  note = {Flagship configuration: 99c7a6631340d301}
}
```

## Quick Start

```python
import pandas as pd

# Load main dataset
df = pd.read_csv('energy_consumption_hourly.csv', parse_dates=['timestamp'])

# Load ground truth (for validation only)
archetypes = pd.read_csv('ground_truth_archetypes.csv')

# Basic exploration
print(f"Shape: {df.shape}")
print(f"Consumers: {df['consumer_id'].nunique()}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

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
**Email**: shaxntanu@gmail.com  
**ORCID**: [0009-0008-4403-0670](https://orcid.org/0009-0008-4403-0670)  
**GitHub**: [@shaxntanu](https://github.com/shaxntanu)

For questions, issues, or contributions, please open an issue on the [GitHub repository](https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means/issues).

---

**Dataset Version**: 1.0.0  
**Release Date**: 2026-09-24  
**Configuration Hash**: 99c7a6631340d301  
**Generator**: `data_loader.py::generate_synthetic_data`
