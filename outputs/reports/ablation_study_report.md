# Ablation Study

THIS IS SYNTHETIC DATA. What follows shows how the pipeline behaves under
different inputs. It is not evidence about real households.

## The question

Does the feature engineering change what the clustering finds, or would any
set of columns have produced a similar answer? Three arms run on the same
generated data, with the same seed and the same K selection rule, so the only
thing that varies is which columns go in.

- A, scale only: magnitude summaries, the naive baseline
- B, behavioral only: normalized shape and timing, magnitude divided out
- C, combined: both groups together

## The decision rule, fixed before the run

1. Reject an arm whose partition is unstable across restarts (mean pairwise ARI below 0.6) or which leaves a cluster below 5% of consumers.
2. Among the survivors, prefer the arm that best serves the research question:
   grouping consumers by when they use energy rather than how much. On
   synthetic data that is measured directly, as agreement with the hidden
   archetypes. Without ground truth, fall back to shape separation.
3. Report silhouette for every arm but do not let it decide. Silhouette
   rewards separation in whatever space it is given, so an arm that separates
   cleanly on magnitude scores well while answering a different question.

## Results

       arm  n_features  n_pca_components  optimal_k  silhouette  calinski_harabasz  davies_bouldin  stability_mean_ari  archetype_ari  scale_separation  shape_separation cluster_sizes
     scale           7                 2          2    0.520702         230.172551        0.782948            0.983328      -0.003554          0.795873          0.040740     [64, 136]
behavioral          39                11          3    0.311574          82.029734        1.218674            0.984605       0.636393          0.055358          0.608920  [53, 87, 60]
  combined          46                12          3    0.270703          66.382538        1.378859            1.000000       0.623345          0.065896          0.608866  [62, 53, 85]

### Reading the columns

- silhouette, Calinski-Harabasz, Davies-Bouldin: internal quality at the
  selected K. Higher, higher, lower is better.
- stability_mean_ari: mean pairwise Adjusted Rand Index across restarts from
  different seeds. How much the partition moves when only the seed changes.
- archetype_ari: agreement with the archetypes the generator drew from. That
  column is dropped before preprocessing and never reaches the model, so this
  is an independent check. It exists only because the data is synthetic.
- scale_separation, shape_separation: between-cluster spread of mean kWh and
  of the normalized 24-hour shape, each divided by the spread across all
  consumers. These say whether an arm sorted consumers by magnitude or by
  timing. Both are computed from the same combined feature table for every
  arm, so the arms are comparable.

## Which arm the rule selects

- Step 2 selected behavioral on agreement with the hidden archetypes: ARI 0.6364, the highest among the arms that survived step 1.
- Step 3, for the record: scale has the highest silhouette score (0.5207 against 0.3116 for behavioral). Silhouette did not decide the choice, and this is the case the rule was written for. The scale arm separates its own feature space more cleanly while answering a different question.
- The diagnostics show what each arm keyed on. Magnitude separation is highest for scale (0.796); shape separation is highest for behavioral (0.609).
- Worth stating plainly: the scale arm scores -0.0036 against the archetypes. The Adjusted Rand Index is corrected for chance, so a value at or below zero means that partition carries no information about the groups the data was built from, despite its silhouette score of 0.5207.

Selected arm: behavioral.

## What this does and does not establish

It establishes that the choice of feature set changes the answer, and that on
this dataset the arm serving the stated research question is not the arm with
the best internal score. That is the case worth knowing about, because a
pipeline tuned on silhouette alone would have picked the other one.

It does not establish that behavioral features are the right choice for every
energy segmentation problem. The generator built this data with timing
differences in it, so an arm that reads timing is bound to do well here. On a
real dataset the archetype column does not exist and the question would have to
be settled on the shape separation diagnostic and on whether the resulting
clusters are interpretable.
