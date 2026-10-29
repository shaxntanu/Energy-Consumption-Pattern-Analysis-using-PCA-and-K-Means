# Manuscript research status

**Updated:** 2026-10-29
**Canonical source:** [`MAIN.tex`](MAIN.tex)
**Status:** Active revision; not submission-ready.

## Evidence now included

The manuscript keeps the synthetic and measured-data evidence separate:

- Synthetic flagship: 200 consumers over 365 days; K=4; ARI=0.813 against labels withheld during modeling; multi-seed ARI=0.995; quarterly temporal ARI=0.882.
- Synthetic 20-run feature robustness: behavioral features mean ARI=0.641; scale-only mean ARI=0.013. The paired tests are described as exploratory; a non-significant p-value is not treated as evidence of equivalence.
- UCI ElectricityLoadDiagrams20112014: seeded 120-column sample from 2012; 16 all-zero columns excluded, leaving 104 clients and 913,536 meter-hours. The heuristic selects K=2, the only candidate meeting its minimum cluster-size constraint. Restart ARI=1.000; temporal-window mean pairwise ARI=0.288. No real-data ARI/NMI against fabricated labels is reported.

UCI identifies anonymized points/clients, not necessarily households. The real-data results are descriptive and show weak persistence across three chronological windows. They do not establish behavioral meaning, household routines, demand-response effects, or generalization.

## Reproduction and provenance

Run `research/run_uci_load_diagrams_validation.py` with the UCI ZIP archive; the full command and output locations are documented in [`README.md`](README.md). The JSON sidecar records the source SHA-256, selected and excluded client IDs, date range, conversion assumption, and software versions. Raw UCI data is not included in the repository.

## Remaining work before submission

- Rebuild `MAIN.pdf` from the current source and visually inspect all pages.
- Resolve any LaTeX warnings and verify references, figure paths, and table layout.
- Review the timestamp-ending assumption and temporal-window protocol against the dataset documentation.
- Repeat the measured-data analysis on additional multi-client datasets and years, and quantify uncertainty in cluster profiles.
- Revisit the target venue after checking current scope, fees, and author requirements.

The older modular sections, standalone drafts, and historical audit files in `paper/` are not synchronized with `MAIN.tex`; use only the canonical source unless those files are explicitly updated.
