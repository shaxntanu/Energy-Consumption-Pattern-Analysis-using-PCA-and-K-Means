# Validation Against the Hidden Archetypes

THIS IS SYNTHETIC DATA. The check below is possible only because the generator
recorded which archetype each consumer was drawn from. That column is dropped
before preprocessing and never reaches the scaler, PCA or K-Means.

## What the numbers say

The generator drew consumers from 4 archetypes. The pipeline selected K=3 using internal indices only, and at that K the Adjusted Rand Index against the archetypes is 0.6364.

Recovery is highest at K=4 (ARI 0.8123), while the silhouette score is highest at K=3.

The two disagree, and that disagreement is the result rather than a problem to hide. Internal indices reward compact, well-separated clusters. They have no way to know how many groups the data was built from, so when two archetypes differ along a direction that occupies a small part of the feature space, merging them raises the silhouette score even though it loses a real distinction.

At the selected K each archetype falls out as follows:

- daytime -> cluster 2 (100%)
- evening -> cluster 1 (98%)
- flat -> cluster 0 (100%)
- weekend -> cluster 1 (76%)

The practical reading: on this dataset the internal indices under-count the groups. On a real dataset there would be no way to detect that, which is a limit of unsupervised clustering and not of this implementation.

## Recovery by K

| K | Adjusted Rand Index | Normalized Mutual Information | Silhouette |
| - | ------------------- | ----------------------------- | ---------- |
| 2 | 0.3875 | 0.5229 | 0.2319 |
| 3 (selected) | 0.6364 | 0.7144 | 0.3116 |
| 4 | 0.8123 | 0.8198 | 0.2937 |
| 5 | 0.8005 | 0.8235 | 0.2994 |
| 6 | 0.7521 | 0.7998 | 0.2872 |
| 7 | 0.7102 | 0.7766 | 0.2884 |
| 8 | 0.5675 | 0.7066 | 0.2363 |
| 9 | 0.6551 | 0.7357 | 0.2871 |
| 10 | 0.5234 | 0.6887 | 0.2309 |

## Cluster against archetype at the selected K

```
cluster     0   1   2
archetype            
daytime     0   0  50
evening     0  49   1
flat       50   0   0
weekend     3  38   9
```
