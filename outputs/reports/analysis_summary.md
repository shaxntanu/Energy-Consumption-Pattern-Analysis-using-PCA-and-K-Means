# Energy Consumption Analysis Summary

## Configuration
- Consumers: 200
- Days: 30
- Feature Set: behavioral
- Random Seed: 42
- Config Hash: 5dea3511b183602d
- Data Source: Synthetic (archetype-based)

## Results
- Features Engineered: 33
- PCA Components: 25 (95% variance threshold)
- Optimal K: 2
- Silhouette at Optimal K: 0.1055
- Cluster Sizes: [135, 65]
- Recommendations Generated: 4

## Cluster Profiles

### Afternoon-Peak High-Variability (Cluster 0)
- Size: 135 (67.5%)
- Avg Consumption: 0.0714 kWh
- Peak-to-Avg Ratio: 7.11
- Coefficient of Variation: 1.07
- Weekend Ratio: 0.952

### Weekend-Oriented Spiky-Variable (Cluster 1)
- Size: 65 (32.5%)
- Avg Consumption: 0.0767 kWh
- Peak-to-Avg Ratio: 10.64
- Coefficient of Variation: 1.32
- Weekend Ratio: 1.196
