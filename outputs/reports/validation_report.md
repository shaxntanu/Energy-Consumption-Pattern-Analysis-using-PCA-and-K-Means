# Validation Against the Hidden Archetypes

THIS IS SYNTHETIC DATA. The check below is possible only because the generator
recorded which archetype each consumer was drawn from. That column is dropped
before preprocessing and never reaches the scaler, PCA or K-Means.

## What the numbers say

The generator drew consumers from 4 archetypes. The pipeline selected K=4 using internal indices only, and at that K the Adjusted Rand Index against the archetypes is 0.8127.

Recovery is highest at K=4 (ARI 0.8127), while the silhouette score is highest at K=5.

The pipeline's choice of K matches the number of archetypes, so on this dataset the internal indices agree with the ground truth. That agreement is not guaranteed in general and should not be assumed for other data.

## Recovery by K

| K | Adjusted Rand Index | Normalized Mutual Information | Silhouette |
| - | ------------------- | ----------------------------- | ---------- |
| 2 | 0.2875 | 0.4565 | 0.2939 |
| 3 | 0.6017 | 0.6801 | 0.3305 |
| 4 (selected) | 0.8127 | 0.8284 | 0.3283 |
| 5 | 0.7653 | 0.8021 | 0.3352 |
| 6 | 0.7528 | 0.7816 | 0.3238 |
| 7 | 0.7347 | 0.7768 | 0.3164 |
| 8 | 0.6915 | 0.7534 | 0.3072 |
| 9 | 0.6760 | 0.7543 | 0.3111 |
| 10 | 0.5978 | 0.7301 | 0.2760 |

## Cluster against archetype at the selected K

```
cluster     0   1   2   3
archetype                
daytime    39   1   0  10
evening     0   0  47   3
flat        0  50   0   0
weekend     0   1   0  49
```
