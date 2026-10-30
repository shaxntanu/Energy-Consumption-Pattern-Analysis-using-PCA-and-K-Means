# Current manuscript audit

**Updated:** 2026-10-30 | **Canonical source:** paper/MAIN.tex | **Status:** Active revision; not submission-ready.

## Scope and claims

The manuscript separates synthetic recovery evidence from unlabeled measured-data descriptions. UCI electricity points are called clients, not assumed to be households. London results are an exploratory household subset. The singleton selected cluster and truncated archive are disclosed. The K-selection tolerance is heuristic; post-clustering feature comparisons are descriptive and not independent validation. The manuscript makes no measured energy-savings or causal demand-response claim.

## Evidence record

- 365-day synthetic replication: 20 independent generator seeds. Behavioral 51-feature + PCA fixed-K=4 ARI 0.854 [0.825, 0.880]; normalized 24-bin no-PCA baseline ARI 0.693 [0.655, 0.732]; paired difference 0.161 [0.125, 0.201]. CIs bootstrap seeds and do not quantify household-population uncertainty.
- UCI: 104 active clients from a seeded 120-client 2012 sample; 16 all-zero columns excluded; 913,536 meter-hours; K=2; restart ARI 1.000; three-window mean pairwise ARI 0.288.
- London: 292 coverage-eligible households across 11 recovered complete CSV members; 319 IDs observed; K=3 cluster sizes 11/280/1 after relaxing the five-percent size filter; restart ARI 0.979; monthly mean ARI 0.609, range about 0.000-0.957. The source archive is incomplete and the subset is not representative.
- UCI peak-shift simulation: equal-energy target/comparator evening-peak reductions 5.64% and 5.62%; the whole-day peak rises and shifts to 16:00 in both scenarios.
- London peak-shift simulation: assumed 10% shifts preserve daily energy by construction; comparator moves a different amount of energy. No causal or realized savings estimate is made.

## Data and reproducibility

UCI ElectricityLoadDiagrams20112014 source data are included in dataset/real world/ under CC BY 4.0 with attribution and SHA-256. The London dataset source is cited in paper/references.bib; raw readings are not redistributed. UCI and London analysis metadata record sampling and transformation assumptions. No synthetic labels are assigned to measured-data records.

## Compilation

The built-in compiler generated a partial XDV and stopped because Biber is unavailable. Citations and bibliography were therefore unresolved in that run; paper/MAIN.pdf remains unverified and stale. Recompile with a complete TeX/Biber toolchain and inspect overfull boxes and figures before submission. The manuscript still uses its generic article class; a target venue template has not been selected.
