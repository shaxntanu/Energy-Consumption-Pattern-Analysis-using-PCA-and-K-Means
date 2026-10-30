# Manuscript research status

**Updated:** 2026-10-30 | **Canonical source:** MAIN.tex | **Status:** Active revision; not submission-ready.

## Evidence now included

- **Synthetic 365-day replication:** 20 independent datasets, each with 200 consumers. At fixed K=4, 51 behavioral features plus PCA achieve ARI 0.854 (95% seed-bootstrap CI [0.825, 0.880]) versus 0.693 [0.655, 0.732] for normalized 24-bin shapes without PCA. Paired difference: 0.161 [0.125, 0.201]. The heuristic selects K=3 in 7/20 seeds and K=4 in 13/20; selected-K mean ARI is 0.778 [0.719, 0.836]. Intervals represent generator-seed variability only.
- **UCI ElectricityLoadDiagrams20112014:** seeded 120-column sample; 16 all-zero clients excluded, leaving 104 clients and 913,536 meter-hours in 2012. Restart ARI=1.000; mean pairwise agreement across three chronological windows=0.288. UCI clients are not assumed to be households.
- **London SmartMeter:** 292 households meeting coverage criteria in 11 complete CSV members recovered from a truncated archive. Selected K=3 yields cluster sizes 11, 280, and 1. Monthly ARI against the annual partition averages 0.609 and varies substantially; intervals are conditional on the selected archive members, annual labels, and K.
- **Retrospective peak shifting:** UCI targeted and equal-energy non-target shifts reduce the evening peak by 5.64% and 5.62%, respectively, but both create a larger afternoon whole-day peak. London simulations assume 10% flexibility and are not matched on shifted energy. Neither scenario estimates actual response or savings.

The paper treats post-clustering feature contrasts as descriptive, labels synthetic confidence intervals by their seed-resampling unit, and does not report ground-truth scores for measured clients or households.

## Reproduction and provenance

Scripts are in research/. The UCI source file is included at dataset/real world/LD2011_2014.txt under CC BY 4.0; the adjacent README records citation, checksum, and license. The London source archive is not redistributed. Derived reports, figures, and metadata are stored under outputs/reports/, outputs/figures/research_additions/, and outputs/research_additions/.

## Remaining work before submission

- Rebuild MAIN.pdf with a working Biber installation and inspect final page layout.
- Resolve bibliography, reference, and overfull-box warnings.
- Repeat London on the complete public archive and validate on an independent household dataset.
- Select and apply a venue template after venue choice.

Older modular sections and historical audit files remain unsynchronized; MAIN.tex is canonical.
