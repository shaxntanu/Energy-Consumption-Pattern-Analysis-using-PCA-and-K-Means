# Research Paper Documentation

This directory contains all LaTeX manuscripts and documentation for the research paper on energy consumption pattern analysis using PCA and K-means clustering.

## 📄 Available Manuscripts

### 1. **paper_scientific_reports.tex** ⭐ (Recommended for Submission)
- **Purpose**: Complete Scientific Reports-style manuscript
- **Status**: ✅ Ready for submission
- **Features**:
  - Full mathematical formulations (PCA eigendecomposition, K-means optimization, validation metrics)
  - Complete methodology with numbered equations
  - Real experimental results from `baseline/metrics/`
  - Professional tables with actual cluster profiles
  - Single author (Shantanu) with ORCID: 0009-0008-4403-0670
  - ~25 pages, 474 lines, 40+ citations
  - Honest scientific tone with limitations acknowledged
  
**Compile**:
```bash
pdflatex paper_scientific_reports.tex
pdflatex paper_scientific_reports.tex  # Second pass for references
```

### 2. **paper_standalone.tex**
- **Purpose**: Self-contained version for Overleaf upload
- **Status**: ✅ Standalone compilation
- **Use case**: Direct upload to Overleaf with figures

**Compile**:
```bash
pdflatex paper_standalone.tex
```

### 3. **main.tex** (Modular Development Version)
- **Purpose**: Multi-file structured manuscript
- **Status**: 🔄 Development version with sections/
- **Use case**: Collaborative editing and iterative development

**Compile**:
```bash
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

## 📊 Supporting Files

### Bibliography
- **references.bib**: 40+ citations covering PCA, clustering, energy analytics, validation methods

### Modular Sections (for main.tex)
Located in `sections/` directory:
- `01_introduction.tex` - Background and motivation
- `02_related_work.tex` - Literature review
- `03_methodology.tex` - Data generation, PCA, K-means
- `04_experiments.tex` - Experimental setup
- `05_results.tex` - Quantitative findings
- `06_discussion.tex` - Interpretation and implications
- `07_conclusion.tex` - Summary and future work
- `08_appendix.tex` - Supplementary material

### Diagrams and Visualizations
Located in `diagrams/` directory:
- `experimental_architecture.mmd` - Mermaid flowchart of pipeline
- Additional methodology diagrams

### Generation Scripts
Located in `scripts/` directory:
- `generate_tables.py` - Auto-generate LaTeX tables from CSV metrics
- `generate_figures.py` - Create publication-ready figures
- `validate_results.py` - Cross-check paper claims with actual data

## 🎯 Quick Start Guide

### Option A: For Journal Submission (Recommended)
```bash
cd paper/
pdflatex paper_scientific_reports.tex
pdflatex paper_scientific_reports.tex  # Build bibliography
# Output: paper_scientific_reports.pdf
```

### Option B: For Overleaf Editing
1. Open Overleaf
2. Upload `paper_standalone.tex`
3. Upload figures from `../outputs/figures/` (when generated)
4. Compile in Overleaf (pdfLaTeX)

### Option C: For Modular Development
```bash
cd paper/
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
# Output: main.pdf
```

## 📈 Figures Integration

The manuscripts reference figures that should be in `../outputs/figures/`:

**Required Figures:**
1. `pca_scree_plot.png` - Explained variance by component
2. `cluster_scatter_pc1_pc2.png` - 2D projection of clusters
3. `silhouette_analysis.png` - Silhouette scores per cluster
4. `time_of_use_profiles.png` - Temporal consumption patterns
5. `validation_metrics_k.png` - Metric curves vs. K
6. `cluster_heatmap.png` - Feature comparison heatmap

**Generate figures:**
```bash
python scripts/generate_figures.py
```

## 📋 Results Data Sources

The paper uses **real experimental results** from:

### Metrics Files
- `../baseline/metrics/evaluation_metrics.csv` - Silhouette, CH, DB scores
- `../baseline/metrics/pca_results.csv` - Explained variance ratios
- `../baseline/metrics/clustering_metrics.csv` - Performance per K

### Cluster Profiles
- `../baseline/reports/cluster_profiles.csv` - Mean/std per cluster
- `../baseline/reports/cluster_insights.csv` - Interpretations
- `../baseline/reports/statistical_summary.csv` - Dataset stats

### Models
- `../baseline/models/kmeans_model.pkl` - Trained K-means (K=3)
- `../baseline/models/pca_model.pkl` - Trained PCA (6 components)
- `../baseline/models/scaler.pkl` - StandardScaler
- `../baseline/models/cluster_labels.npy` - Final assignments

## ✅ Manuscript Completion Status

### paper_scientific_reports.tex
- [x] Title, author, affiliation with ORCID
- [x] Complete abstract (200 words)
- [x] Introduction with motivation
- [x] Methods section with equations
  - [x] Data generation model
  - [x] Feature engineering (15 features)
  - [x] PCA formulation (SVD-based)
  - [x] K-means algorithm
  - [x] Validation metrics (silhouette, CH, DB)
  - [x] Software implementation details
- [x] Results section with tables
  - [x] PCA explained variance table
  - [x] Clustering metrics comparison
  - [x] Cluster profiles table
- [x] Discussion with implications
- [x] Limitations acknowledged
- [x] Conclusion and future work
- [x] Data/Code availability statements
- [x] Bibliography (40+ references)
- [ ] **Add figures** (placeholder references exist)
- [ ] Final proofreading pass

### Status Summary
| Component | Status | Notes |
|-----------|--------|-------|
| Structure | ✅ Complete | 8 sections, proper flow |
| Equations | ✅ Complete | 16 numbered equations |
| Tables | ✅ Complete | 3 tables with real data |
| Figures | ⏳ Pending | 0/6 integrated |
| Bibliography | ✅ Complete | 40+ citations |
| Metadata | ✅ Complete | Author, ORCID, GitHub |

## 📝 Author Information

**Author**: Shantanu  
**Email**: shxntanu@gmail.com  
**ORCID**: [0009-0008-4403-0670](https://orcid.org/0009-0008-4403-0670)  
**Affiliation**: Independent Researcher  
**GitHub**: [shaxntanu](https://github.com/shaxntanu)  
**Repository**: [Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means](https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means)

## 🎓 Target Journal

**Primary Target**: Scientific Reports (Nature Portfolio)
- **Scope**: Interdisciplinary, transparent methodology
- **Format**: Matches reference paper style (s41598-026-69967-5)
- **Requirements**: 
  - Open access: ✅
  - Data availability: ✅ (GitHub)
  - Code availability: ✅ (MIT License)
  - Ethics: N/A (synthetic data)

**Secondary Targets**:
- PLOS ONE (methodology papers)
- IEEE Access (engineering applications)
- Applied Energy (energy domain)

## 🔗 Related Documentation

### Main Repository Documentation
- `../README.md` - Project overview
- `../RESULTS.md` - Experimental results summary
- `../PROJECT_FEATURES_AND_PIPELINE.md` - Technical pipeline

### Research Documentation
- `../RESEARCH_AUDIT.md` - Research integrity audit
- `../RESEARCH_INFRASTRUCTURE_AUDIT.md` - Infrastructure details
- `../audit_report.md` - Comprehensive audit

### Code Documentation
- `../src/` - Python implementation
- `../cpp_engine/` - C++ acceleration
- `../tests/` - Unit tests

## 🛠️ Troubleshooting

### LaTeX Compilation Issues

**Missing packages:**
```bash
# Install required packages (TeX Live)
tlmgr install amsmath graphicx booktabs natbib geometry hyperref
```

**Bibliography not showing:**
```bash
# Run twice to resolve references
pdflatex paper_scientific_reports.tex
pdflatex paper_scientific_reports.tex
```

**Figure not found:**
- Check `../outputs/figures/` directory exists
- Run `python scripts/generate_figures.py`
- Update figure paths in .tex if needed

## 📦 Submission Checklist

Before journal submission:
- [ ] Add all 6 figures to manuscript
- [ ] Verify all tables render correctly
- [ ] Check equations compile properly
- [ ] Proofread entire manuscript
- [ ] Verify bibliography entries
- [ ] Generate final PDF
- [ ] Check PDF metadata (author, title)
- [ ] Prepare supplementary materials
- [ ] Write cover letter
- [ ] Confirm author guidelines compliance

## 📮 Questions?

For manuscript questions or collaboration:
- Email: shxntanu@gmail.com
- GitHub Issues: [Repository Issues](https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means/issues)
- ORCID: [0009-0008-4403-0670](https://orcid.org/0009-0008-4403-0670)

---

**Last Updated**: 2026-09-23  
**Paper Status**: Ready for figure integration and submission  
**Repository**: [![GitHub](https://img.shields.io/badge/GitHub-shaxntanu-blue)](https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means)
