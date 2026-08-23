# Validation Against the Hidden Archetypes

THIS IS SYNTHETIC DATA. The check below is possible only because the generator
recorded which archetype each consumer was drawn from. That column is dropped
before preprocessing and never reaches the scaler, PCA or K-Means.

## What the numbers say

The generator drew consumers from 4 archetypes. The pipeline selected K=3 using internal indices only, and at that K the Adjusted Rand Index against the archetypes is 0.6140.

Recovery is highest at K=4 (ARI 0.8713), while the silhouette score is highest at K=3.

The two disagree, and that disagreement is the result rather than a problem to hide. Internal indices reward compact, well-separated clusters. They have no way to know how many groups the data was built from, so when two archetypes differ along a direction that occupies a small part of the feature space, merging them raises the silhouette score even though it loses a real distinction.

At the selected K each archetype falls out as follows:

- daytime -> cluster 0 (100%)
- evening -> cluster 2 (94%)
- flat -> cluster 1 (100%)
- weekend -> cluster 0 (82%)

The practical reading: on this dataset the internal indices under-count the groups. On a real dataset there would be no way to detect that, which is a limit of unsupervised clustering and not of this implementation.

## Recovery by K

| K | Adjusted Rand Index | Normalized Mutual Information | Silhouette |
| - | ------------------- | ----------------------------- | ---------- |
| 2 | 0.3243 | 0.5421 | 0.2582 |
| 3 (selected) | 0.6140 | 0.7029 | 0.3124 |
| 4 | 0.8713 | 0.8507 | 0.2916 |
| 5 | 0.8078 | 0.8273 | 0.3005 |
| 6 | 0.7508 | 0.7812 | 0.2888 |
| 7 | 0.7031 | 0.7427 | 0.2726 |
| 8 | 0.6859 | 0.7495 | 0.2702 |
| 9 | 0.5331 | 0.6948 | 0.2136 |
| 10 | 0.5166 | 0.6828 | 0.2179 |

## Cluster against archetype at the selected K

```
cluster     0   1   2
archetype            
daytime    50   0   0
evening     3   0  47
flat        0  50   0
weekend    41   7   2
```
