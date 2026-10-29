# Paper status and reproduction guide

## Current manuscript

[`MAIN.tex`](MAIN.tex) is the canonical manuscript. It covers the controlled synthetic experiments and a separate, unlabeled analysis of the UCI ElectricityLoadDiagrams20112014 client data. Older standalone, modular, and template files in this directory are not synchronized with `MAIN.tex` and should not be submitted as current versions.

The manuscript is still under review and should not be described as submission-ready. In particular, `MAIN.pdf` is a previously generated artifact and may not match the current TeX source until it is rebuilt.

## UCI measured-data run

The source archive is available from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014) and is not committed here. Download the archive, then run from the repository root:

```powershell
python research/run_uci_load_diagrams_validation.py `
  --source "$env:TEMP\LD2011_2014.zip" `
  --start 2012-01-01 --end 2012-12-31 `
  --n-meters 120 --sample-seed 42 --seed 42 --stability-runs 8
```

The run samples 120 client columns, excludes 16 with zero consumption across 2012, and analyzes 104 clients. Results, provenance, selected IDs, and the archive hash are saved to:

- [`outputs/reports/real_world_uci_load_diagrams_2012.md`](../outputs/reports/real_world_uci_load_diagrams_2012.md)
- [`outputs/reports/real_world_uci_load_diagrams_2012.json`](../outputs/reports/real_world_uci_load_diagrams_2012.json)
- [`outputs/figures/real_world/cluster_load_shapes.png`](../outputs/figures/real_world/cluster_load_shapes.png)

The full-year partition has eight-restart ARI 1.000, while the independently fitted partitions across three chronological windows have mean pairwise ARI 0.288. UCI identifies anonymized points/clients rather than necessarily households and supplies no behavioral labels, so this is descriptive unsupervised analysis, not behavioral ground-truth validation.

## Build and verify

Compile `MAIN.tex` with the repository's LaTeX project compiler or with a local LaTeX installation using `pdflatex`, `biber`, then `pdflatex` twice. Keep the generated figures under `../outputs/figures/` so the manuscript's relative image paths resolve.

Before submission, update the PDF from the current source, resolve compilation warnings, proofread all claims and references, and select a venue only after checking its current scope, fees, and author requirements.
