# Seasonal Analysis Report (Improvement 2)

This file is generated from the data alone. The hidden seasonal_phase
column (synthetic data only) is used strictly as ground truth to score
the estimate, never as an input.

- Seasons present: ['winter', 'spring', 'summer', 'autumn']
- Mean daily kWh by season: {'winter': 26.571, 'spring': 35.1668, 'summer': 38.0142, 'autumn': 29.433}
- Estimated magnitude amplitude (fractional swing of daily totals): 0.20178864227863696
- Mean peak hour by season: {'autumn': 19, 'spring': 20, 'summer': 20, 'winter': 19}

## Phase recovery (synthetic ground truth only)

- Pearson r between season-level estimate and hidden phase: 0.6780669314235555
- Peak-season label agreement: 0.885 (over 185 consumers with a hidden phase)

The estimate is deliberately coarse (one of four seasons), so a
moderate r is expected and correct.

## Cluster x season cross-check

Because the seasonal phase is drawn independently of archetype, the
seasonal swing should be the same for every cluster. The table below is
the evidence for that: mean daily kWh per (cluster, season).

```
season   winter  spring  summer  autumn
cluster                                
0        25.757  33.738  36.674  28.473
1        27.041  36.167  39.120  30.088
2        26.811  35.773  39.220  30.440
3        26.507  34.767  37.016  28.725
```

- Median seasonal amplitude per cluster: {0: 0.17516552646228636, 1: 0.18243387245526, 2: 0.1876786778035001, 3: 0.16547529820722312}

## Channel interpretation

- Magnitude channel: mean-corrected over the window, so it changes WHEN
  energy is used, not the long-run average. It cannot inflate or create a
  spurious cluster from scale differences.
- Timing channel: moves the daily peak hours across the year and is what
  changes the normalized load shape. It is renormalised so it never
  changes a daily total.
