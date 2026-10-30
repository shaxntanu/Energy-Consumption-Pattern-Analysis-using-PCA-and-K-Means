# UCI ElectricityLoadDiagrams20112014

This folder contains the extracted source file used for the real-client analyses:

- `LD2011_2014.txt` — 15-minute mean-power observations in kW for 370 anonymized electricity points.

## Source and attribution

- Dataset: [UCI Machine Learning Repository: ElectricityLoadDiagrams20112014](https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014)
- Citation: Trindade, A. (2015). *ElectricityLoadDiagrams20112014* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C58C86.
- License: Creative Commons Attribution 4.0 International (CC BY 4.0). Please retain this attribution when sharing or adapting the data.
- File size: 710,998,915 bytes
- SHA-256: `d51565f2cb5a6b768d06ba1bbd3c084c6e2f3aab07f00c6f2dcb80e90175124b`
- Rows: 140,256 observations plus the header row

The measurements are anonymized electricity clients and are not necessarily residential households. The source is included for reproducibility; the analysis reports the original dataset attribution and does not infer household identity.

## Reproduce the UCI analysis

From the repository root, run:

```powershell
python research/run_uci_load_diagrams_validation.py `
  --source "dataset/real world/LD2011_2014.txt" `
  --start 2012-01-01 --end 2012-12-31 `
  --n-meters 120 --sample-seed 42 --seed 42 --stability-runs 8
```

The source file is tracked with Git LFS. Clone the repository with Git LFS installed and run `git lfs pull` if the file is not downloaded automatically.
