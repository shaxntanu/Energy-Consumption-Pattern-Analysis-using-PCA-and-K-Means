# Validation Against the Hidden Archetypes

THIS IS SYNTHETIC DATA. The check below is possible only because the generator
recorded which archetype each consumer was drawn from. That column is dropped
before preprocessing and never reaches the scaler, PCA or K-Means.

## What the numbers say

The generator drew consumers from 4 archetypes. The pipeline selected K=2 using internal indices only, and at that K the Adjusted Rand Index against the archetypes is 0.3138.

Recovery is highest at K=4 (ARI 0.8376), while the silhouette score is highest at K=7.

The two disagree, and that disagreement is the result rather than a problem to hide. Internal indices reward compact, well-separated clusters. They have no way to know how many groups the data was built from, so when two archetypes differ along a direction that occupies a small part of the feature space, merging them raises the silhouette score even though it loses a real distinction.

At the selected K each archetype falls out as follows:

- daytime -> cluster 0 (100%)
- evening -> cluster 0 (98%)
- flat -> cluster 1 (100%)
- weekend -> cluster 0 (90%)

The practical reading: on this dataset the internal indices under-count the groups. On a real dataset there would be no way to detect that, which is a limit of unsupervised clustering and not of this implementation.

## Recovery by K

| K | Adjusted Rand Index | Normalized Mutual Information | Silhouette |
| - | ------------------- | ----------------------------- | ---------- |
| 2 (selected) | 0.3138 | 0.4923 | 0.2967 |
| 3 | 0.5852 | 0.6570 | 0.3134 |
| 4 | 0.8376 | 0.8271 | 0.2945 |
| 5 | 0.7629 | 0.7844 | 0.3142 |
| 6 | 0.7439 | 0.7798 | 0.3167 |
| 7 | 0.6983 | 0.7431 | 0.3167 |
| 8 | 0.7004 | 0.7676 | 0.2723 |
| 9 | 0.5752 | 0.7191 | 0.2114 |
| 10 | 0.5725 | 0.7165 | 0.2100 |

## Cluster against archetype at the selected K

```
cluster     0   1
archetype        
daytime    50   0
evening    49   1
flat        0  50
weekend    45   5
```
