# Longitudinal Analysis Report (Improvement 1)

The observation window was split into time segments. Behavioural
features were re-engineered and the standardize -> PCA -> K-Means recipe
re-fit inside each segment, then the segment labels were compared with
the full-window labels using the Adjusted Rand Index (permutation-
invariant, so no label-matching step is needed).

- Window segments: ['0: 2024-01-01 to 2024-04-01', '1: 2024-04-01 to 2024-07-01', '2: 2024-07-01 to 2024-09-30', '3: 2024-09-30 to 2024-12-30']
- Consumers per segment: [200, 200, 200, 200]
- Optimal K (from the full-window run): 4
- Segment ARI vs full window: [0.837784535882258, 0.8923577410330173, 0.945638839182731, 0.8509767826476764]
- Mean temporal cluster stability (ARI): 0.8816894746864208

Interpretation: A high, flat value means the consumer groups are a
property of the consumers, not of the month or season; a value that
collapses in one segment means the structure is not stable across time
within this window.

## Mean daily energy by month

```
2024-01    26.067
2024-02    28.417
2024-03    31.883
2024-04    35.448
2024-05    38.178
2024-06    39.406
2024-07    38.549
2024-08    36.132
2024-09    32.679
2024-10    29.151
2024-11    26.478
2024-12    25.307
```
