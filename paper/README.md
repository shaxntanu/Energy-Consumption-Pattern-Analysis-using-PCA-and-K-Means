# Paper status and reproduction guide

**Updated:** 2026-10-30 | **Canonical source:** MAIN.tex | **Status:** Active revision; not submission-ready.

MAIN.tex now includes the full-year synthetic baseline replication, UCI client results, the exploratory London household subset, and retrospective peak-shift scenarios. The London analysis is explicitly limited to 292 eligible households from 11 complete CSV members recovered from a truncated local archive. Its selected K=3 partition includes a singleton. Neither measured dataset has behavioral ground truth.

## Evidence and outputs

- 20 independent synthetic runs, 200 consumers x 365 days: behavioral features with PCA, fixed K=4, mean ARI 0.854 (95% seed-bootstrap CI [0.825, 0.880]); normalized 24-bin shape baseline without PCA, 0.693 [0.655, 0.732].
- UCI ElectricityLoadDiagrams20112014: 104 active clients; restart ARI 1.000; chronological-window mean pairwise ARI 0.288.
- London SmartMeter: 292 coverage-eligible households; monthly agreement with annual labels mean ARI 0.609, range approximately 0.000-0.957; conditional household bootstrap intervals.
- Peak shifting: UCI targeting and equal-energy comparator give similar evening-peak reductions (5.64% and 5.62%) and both create a larger afternoon peak. London scenarios assume flexibility and use different shifted-energy volumes.
- Reports and data sidecars: outputs/reports/ and outputs/research_additions/.
- Figures: outputs/figures/research_additions/.

## Reproduction

Run from the repository root.

Full-year synthetic seed study:

```powershell
python research/run_synthetic_365_replication.py --runs 20 --data-seed-start 100 --model-seed-offset 10000 --stability-runs 8
```

UCI client analysis using the Git LFS source in dataset/real world/:

```powershell
python research/run_uci_load_diagrams_validation.py --source "dataset/real world/LD2011_2014.txt" --start 2012-01-01 --end 2012-12-31 --n-meters 120 --sample-seed 42 --seed 42 --stability-runs 8
```

UCI retrospective peak-shift scenario:

```powershell
python research/simulate_demand_response_uci.py --source "dataset/real world/LD2011_2014.txt"
```

London analysis requires the official partitioned archive. The script records selected archive members, hashes, household IDs, coverage checks, and transformations; raw London readings are not included in the repository. Example:

```powershell
python research/run_london_household_validation.py --source "$env:TEMP/Partitioned_LCL_Data.zip" --n-households 292 --sample-seed 42 --seed 42 --stability-runs 8
```

The UCI source is included under CC BY 4.0 in dataset/real world/README.md and stored with Git LFS. Install Git LFS and run git lfs pull if the source file is not materialized after cloning.

## Compile status

The built-in LaTeX compiler produced a partial XDV but could not complete bibliography processing because Biber is unavailable in its environment. MAIN.pdf must therefore be treated as stale until rebuilt with a complete LaTeX/Biber toolchain. A venue-specific template has not been selected.
