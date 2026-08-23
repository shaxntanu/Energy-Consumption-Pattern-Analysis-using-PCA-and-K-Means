# Ablation Study

THIS IS SYNTHETIC DATA. What follows shows how the pipeline behaves under
different inputs. It is not evidence about real households.

## The question

Does the feature engineering change what the clustering finds, or would any
set of columns have produced a similar answer? 5 arms run on the same
generated data, with the same seed and the same K selection rule, so the only
thing that varies is which columns go in.

- A, scale only: magnitude summaries, the naive baseline
- B, shape only: the normalized 24-hour profile, nothing else
- C, summary only: the scalars derived from the profile, without the profile
- D, behavioral: shape and summary together, what the pipeline uses
- E, combined: behaviour and magnitude together

## The decision rule, fixed before the run

1. Reject an arm whose partition is unstable across restarts (mean pairwise ARI below 0.6) or which leaves a cluster below 5% of consumers.
2. Among the survivors, prefer the arm that best serves the research question:
   grouping consumers by when they use energy rather than how much. On
   synthetic data that is measured directly, as agreement with the hidden
   archetypes. Without ground truth, fall back to shape separation.
3. Treat arms within 0.02 of the best value as tied and prefer
   the smaller feature set. A gap that size is not resolvable on this many
   consumers, and every extra feature takes a share of the distance budget.
4. Report silhouette for every arm but do not let it decide. Silhouette
   rewards separation in whatever space it is given, so an arm that separates
   cleanly on magnitude scores well while answering a different question.

## Results

       arm  n_features  n_pca_components  optimal_k  silhouette  calinski_harabasz  davies_bouldin  stability_mean_ari  archetype_ari  scale_separation  shape_separation    cluster_sizes
     scale           7                 2          2    0.520702         230.172551        0.782948            0.983328      -0.003554          0.795873          0.040740        [64, 136]
     shape          24                 8          4    0.323465          81.603518        1.189371            0.986849       0.645539          0.046659          0.712656 [59, 59, 35, 47]
   summary          27                11          2    0.321496          97.684464        1.085069            0.986010       0.321098          0.019939          0.302040        [147, 53]
behavioral          51                14          3    0.312421          86.386025        1.254081            0.988367       0.613974          0.024234          0.617356     [94, 57, 49]
  combined          58                15          3    0.278630          72.575885        1.386416            0.982911       0.623465          0.037745          0.614820     [96, 55, 49]

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

- Step 2 ranked the survivors on agreement with the hidden archetypes. The best value is 0.6455, from shape.
- Step 3 found no other arm within 0.02 of the best value, so the parsimony tie-break does not apply and shape is selected outright with ARI 0.6455.
- Step 4, for the record: scale has the highest silhouette score (0.5207 against 0.3235 for shape). Silhouette did not decide the choice, and this is the case the rule was written for. The scale arm separates its own feature space more cleanly while answering a different question.
- The diagnostics show what each arm keyed on. Magnitude separation is highest for scale (0.796); shape separation is highest for shape (0.713).
- Worth stating plainly: the scale arm scores -0.0036 against the archetypes. The Adjusted Rand Index is corrected for chance, so a value at or below zero means that partition carries no information about the groups the data was built from, despite its silhouette score of 0.5207.

Selected arm on this single dataset: shape.

This is the arm the rule returns on one draw of the generator (seed 42), and
it is not the arm the project ships. The same rule run across 20 independent
draws does not settle on one arm: it picks summary, behavioral and shape on
different datasets, and on this particular draw it happens to land on shape. The pipeline's feature_set is fixed from that wider study, in
outputs/reports/seed_robustness_report.md, which selects behavioral on the
pooled evidence and treats any single-dataset selection here, including this
one, as superseded wherever the two disagree. Read this report for the effect
of the feature set on one draw, not for the choice of feature set.

## What this does and does not establish

It establishes that the choice of feature set changes the answer. The arms
differ in K, in cluster sizes, in what they sort consumers by, and in how well
they recover the groups the data was built from, all from the same 200
consumers under the same rule.

It also establishes that on this dataset the arm serving the stated research
question (shape) is not the arm with the best internal score
(scale). That is the case worth knowing about, because a
pipeline tuned on silhouette alone would have picked the other one.

It does not establish that behavioral features are the right choice for every
energy segmentation problem. The generator built this data with timing
differences in it, so an arm that reads timing is bound to do well here. On a
real dataset the archetype column does not exist and the question would have to
be settled on the shape separation diagnostic and on whether the resulting
clusters are interpretable.

It also does not establish that the selected feature set is minimal. The arms
test 5 specific groupings, not every subset of the columns, and a
search over subsets guided by archetype agreement would be using the labels to
build the model.
