# Seed Robustness of the Feature Set Choice

THIS IS SYNTHETIC DATA. Agreement with the hidden archetypes can only be
measured because the generator recorded which archetype each consumer was drawn
from. None of these numbers exist on a real dataset.

## Why this exists

The ablation study compares feature sets on one generated dataset. That is
enough to show the feature set changes what the clustering finds. It is not
enough to decide which feature set to use, because a single dataset is a single
draw and the arms are close enough that the ranking can turn over between draws.

Here the same 5 arms, the same K selection rule and the same arm
selection rule are applied unchanged to 20 independent datasets, each
with its own generator seed. Nothing is refitted or retuned per dataset.

Seeds: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 42. Seed 42 is the one the primary
analysis uses; the rest are a plain range, so no favourable subset can have been
chosen after the fact.

## Per-arm results across datasets

       arm  n_features  archetype_ari_mean  archetype_ari_sd  archetype_ari_min  archetype_ari_max  silhouette_mean  stability_mean  shape_separation_mean  k_modal k_range  times_rule_selected
behavioral          51            0.640842          0.115316           0.531091           0.959813         0.310918        0.987422               0.633420        3  3 to 4                    7
   summary          27            0.609692          0.239581           0.311888           0.960067         0.318875        0.994136               0.540101        3  2 to 4                    9
  combined          58            0.601082          0.032010           0.530537           0.658444         0.279021        0.985831               0.620099        3  3 to 3                    0
     shape          24            0.589492          0.072869           0.463946           0.741666         0.317389        0.978476               0.661735        3  3 to 5                    4
     scale           7            0.013326          0.036118          -0.005444           0.133030         0.520898        0.987267               0.085168        2  2 to 6                    0

### Reading the columns

- archetype_ari_mean, _sd, _min, _max: agreement with the hidden archetypes,
  summarized over datasets. The sd is the number to read a single-dataset gap
  against.
- silhouette_mean, stability_mean: internal quality and restart stability,
  averaged over datasets, at whichever K the rule chose on each.
- shape_separation_mean: how strongly the arm sorted consumers by the shape of
  their day rather than by how much they used.
- k_modal, k_range: the K the rule most often chose, and the full spread. An arm
  whose K moves between datasets is describing a less stable structure.
- times_rule_selected: datasets on which the pre-registered arm rule picked this
  arm, out of 20.

## Does the feature set matter at all

Friedman test on archetype_ari, blocking on dataset: statistic 42.1010, p 1.59e-08, 20 blocks, 5 arms.

## Pairwise comparisons

Wilcoxon signed-rank on every pair, Holm corrected across all 10 tests. Every pair is listed, not only the interesting ones. The
method column records whether the exact distribution was used.

     arm_a      arm_b  mean_difference  wins_a  wins_b  ties method    p_raw   p_holm  significant
     scale      shape        -0.576166       0      20     0  exact 0.000002 0.000019         True
     scale    summary        -0.596366       0      20     0  exact 0.000002 0.000019         True
     scale behavioral        -0.627516       0      20     0  exact 0.000002 0.000019         True
     scale   combined        -0.587756       0      20     0  exact 0.000002 0.000019         True
     shape behavioral        -0.051350       7      13     0  exact 0.123093 0.738556        False
     shape    summary        -0.020201       9      11     0  exact 0.784126 1.000000        False
     shape   combined        -0.011591       7      13     0  exact 0.294252 1.000000        False
   summary behavioral        -0.031150       8      12     0  exact 0.498009 1.000000        False
   summary   combined         0.008610      10      10     0  exact 0.898317 1.000000        False
behavioral   combined         0.039760       8       8     4  exact 0.860260 1.000000        False

wins_a and wins_b count the datasets on which each arm of the pair came out
ahead. A large mean difference carried by a minority of datasets is a different
finding from a small one that holds on almost all of them, and the two columns
are there so those cases can be told apart.

## Which arm the project uses

The pre-registered arm rule, applied to all of these datasets at once rather
than to one of them.

- Step 1 filtered on stability ARI at least 0.6 and a smallest cluster of at least 5%. Datasets passed per arm: behavioral 20/20, combined 20/20, scale 20/20, shape 20/20, summary 20/20.
  Requiring every dataset and requiring a majority give the same set, so nothing rests on which reading is used.
- Step 2 ranked the survivors on mean archetype_ari across 20 datasets. The best value is 0.6408, from behavioral.
- Step 3 found no other arm within 0.02 of that value, so the parsimony tie-break does not apply and behavioral is selected outright with mean archetype_ari 0.6408.
- Step 4, for the record: scale has the highest mean silhouette (0.5209 against 0.3109 for behavioral). Silhouette did not decide the choice.

The rule selects behavioral. Of the 4 pairwise tests involving it, 1 reject the hypothesis that the two arms perform alike after Holm correction: against scale (adjusted p 1.91e-05).
The remaining 3 are not separated by the evidence: shape (adjusted p 0.739), summary (adjusted p 1), combined (adjusted p 1). So behavioral is the arm the rule returns and the arm with the best mean, but it has not been shown to beat those. Reporting it as the demonstrated best feature set would overstate the result.

The pipeline's feature_set is therefore behavioral, and the ablation study's
single-dataset selection is superseded by this one wherever the two disagree.

## What this supports

Ranked on mean archetype_ari, the order is behavioral 0.6408, summary 0.6097, combined 0.6011, shape 0.5895, scale 0.0133.

Friedman rejects the hypothesis that all 5 arms perform alike (statistic 42.101, p 1.59e-08 over 20 datasets), so the arms are not interchangeable.

The gap between the top two arms, behavioral and summary, does not survive correction: mean difference 0.0311, Holm-adjusted p 1, with the leader ahead on only 12 of 20 datasets. Choosing between those two on this evidence is not supported.

The pre-registered arm rule did not settle on one answer either. Over 20 datasets it selected behavioral 7 times, summary 9 times, shape 4 times. A rule that changes its mind between draws of the same generator is not identifying a property of the feature sets, and reporting the arm that won once would overstate what was measured.

## Limits

20 datasets from one generator is not 20 datasets from the world.
Every draw shares the same four archetypes, the same noise model and the same
200 consumers over 30 days, so this measures how much the arm ranking moves
under resampling of that generator and nothing wider. A feature set that wins
here has been shown to suit this generator, which is a weaker claim than suiting
household electricity data.

The tests are paired across datasets, which is the right structure, but the
blocks are 20 draws from one process rather than independent studies, so
the p-values describe sampling variation inside the simulation.

Archetype agreement is used as the criterion because the labels exist. It is not
available on real data, and an arm cannot be chosen this way outside a
simulation. The shape separation column is reported for exactly that reason: it
is the diagnostic that survives the move to real data.
