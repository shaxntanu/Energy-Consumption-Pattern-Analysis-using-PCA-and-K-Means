# Current manuscript audit

**Updated:** 2026-10-29
**Canonical source:** `paper/MAIN.tex`
**Status:** Active revision; not submission-ready.

## Scope and claims

The manuscript now separates controlled synthetic results from the unlabeled UCI client-data analysis. It does not treat UCI clients as households or report ARI/NMI against fabricated labels. It describes cluster profiles as descriptive, changes the K-selection tolerance to a heuristic rather than a significance test, removes post-clustering p-values as cluster-validity evidence, and treats non-significance as inconclusive rather than equivalence.

Alternative-method results are explicitly limited to fixed K=4 on the synthetic PCA representation. The real-data analysis has one seeded year/sample and low stability across three chronological windows; the paper does not claim behavioral or demand-response validation from it.

## Measured-data record

- Source: UCI ElectricityLoadDiagrams20112014; citation key `trindade2015electricityloaddiagrams`.
- Sample: 120 client columns selected uniformly with seed 42 for 2012; 16 all-zero columns excluded; 104 analyzed clients and 913,536 hourly records.
- PCA: 11 components, 95.54% cumulative variance.
- Selected K: 2, the only candidate from 2--8 meeting the five-percent minimum-cluster-size rule.
- Internal metrics: silhouette 0.4662; Calinski-Harabasz 37.5607; Davies-Bouldin 0.9081.
- Eight-restart mean pairwise ARI: 1.0000.
- Three-window mean pairwise ARI: 0.2884 (SD 0.4661).
- Full source hash, selected/excluded IDs, processing assumptions, software versions, and profiles are in `outputs/reports/real_world_uci_load_diagrams_2012.json`.

The timestamp-ending interpretation is an explicit assumption in the ingest script. It assigns each 15-minute mean-power value to the preceding quarter-hour, converts kW to kWh by dividing by four, and aggregates four quarters to a local-clock hour. The run does not apply a timezone conversion or a fixed household-scale upper bound.

## Compilation and remaining checks

The built-in LaTeX compiler produced a first-pass XDV document but returned `compile-failed` because `biber` is unavailable in its environment. The bibliography remained empty and citations/references unresolved in that run. Local `pdflatex`, `biber`, and `latexmk` are not installed. Therefore `paper/MAIN.pdf` is not verified against the current source and should be treated as stale. The log also reported some overfull boxes; inspect those after building with a complete TeX toolchain.

A source-level citation key check found no undefined keys. `git diff --check` should be clean after this revision. No journal submission or venue choice is part of this audit.
