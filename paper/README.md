# Research Paper: Shape-First Behavioral Segmentation of Household Energy Consumption

This directory contains the publication-quality LaTeX manuscript for the Energy Consumption Pattern Analysis research project.

## Structure

```
paper/
├── main.tex                 # Main document
├── references.bib           # Bibliography (40+ citations)
├── sections/                # Individual sections
│   ├── introduction.tex
│   ├── related_work.tex
│   ├── methodology.tex
│   ├── experiments.tex      # To be created
│   ├── results.tex          # To be created
│   ├── discussion.tex       # To be created
│   ├── limitations.tex      # To be created
│   └── conclusion.tex       # To be created
├── figures/                 # Publication figures (to be generated)
├── tables/                  # LaTeX tables (to be generated)
└── README.md               # This file
```

## Compilation

### Prerequisites

- LaTeX distribution (TeX Live, MiKTeX, or MacTeX)
- BibLaTeX with Biber backend
- Required packages: amsmath, graphicx, booktabs, siunitx, algorithm, biblatex, hyperref

### Commands

```bash
# Standard compilation
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex

# Or use latexmk (recommended)
latexmk -pdf -bibtex main.tex

# Clean auxiliary files
latexmk -c
```

### Quick Start (Windows)

```cmd
cd paper
pdflatex main.tex
biber main
pdflatex main.tex
```

## Status

**Current State:** Partially complete

- [x] Main structure (main.tex)
- [x] Abstract
- [x] Introduction
- [x] Related Work
- [x] Methodology
- [ ] Experiments section (in progress)
- [ ] Results section (in progress)
- [ ] Discussion section (in progress)
- [ ] Limitations section (in progress)
- [ ] Conclusion section (in progress)
- [ ] Figures (to be generated from actual data)
- [ ] Tables (to be generated)

## Key Features

### Scientific Integrity

- All numerical results traced to `outputs/reports/analysis_summary.md`
- No fabricated experiments or citations
- Synthetic data clearly labeled throughout
- Limitations explicitly documented
- Real-world pathway marked as "implemented but not executed"

### Research Positioning

This is a **methodology paper** emphasizing:
- Reproducible experimental design
- Evidence-based decision criteria
- Rigorous feature engineering
- Comprehensive stability analysis
- Complete reproducibility infrastructure

**NOT** an application paper claiming real-world impact or algorithmic novelty.

### Target Journals

Primary targets:
- Energy Informatics (Springer)
- Applied Energy (Elsevier)
- Energy and AI (Elsevier)

Secondary targets:
- IEEE Transactions on Smart Grid (methodology track)
- Sustainable Energy, Grids and Networks

## Citation

When citing this work (after publication):

```bibtex
@article{energyclustering2026,
  title={Shape-First Behavioral Segmentation of Household Energy Consumption: A Reproducible Framework with Evidence-Based K-Selection and Controlled Validation},
  author={[Authors]},
  journal={[Journal]},
  year={2026},
  note={Configuration hash: 99c7a6631340d301}
}
```

## Data and Code Availability

- Repository: https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means
- Interactive Explorer: https://energy-consumption-pattern.vercel.app
- Configuration Hash: `99c7a6631340d301` (flagship 365-day run)

## Remaining Work

Before submission:
1. Complete remaining sections (Experiments, Results, Discussion, Limitations, Conclusion)
2. Generate all figures from actual experimental data
3. Create LaTeX tables from results
4. Execute real-world UCI pathway (or explicitly note as future work)
5. Add statistical uncertainty quantification (bootstrap CIs)
6. Consider benchmark comparison with GMM/DBSCAN/hierarchical
7. Finalize author information and affiliations
8. Proofread and copyedit
9. Verify all citations resolve
10. Check for LaTeX compilation warnings

## Contact

For questions about the manuscript or research:
- See author information in main.tex (to be finalized)
- Repository issues: https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means/issues
