# Requirements and objectives

## Problem statement

Electricity-use profiles can differ in timing and regularity even when daily energy totals are similar. A magnitude-only grouping can hide these differences. This project explores unsupervised segmentation of daily usage shapes and tests whether controlled synthetic archetypes can be recovered.

The project does not establish that a discovered segment corresponds to a real household type or that an intervention based on it saves energy. Existing measured-data studies are exploratory because behavioral labels are unavailable and data coverage is limited.

## Users and use cases

- **Researcher or student:** reproduce the synthetic pipeline and compare feature representations.
- **Reviewer or evaluator:** trace results to scripts, data, configuration, and saved evidence.
- **Developer:** run the Streamlit simulator or build the static Vercel explorer.
- **Future maintainer:** understand boundaries, limitations, and verification status without relying on undocumented assumptions.

## Objectives

| ID | Objective | Measurable evidence |
|---|---|---|
| O-1 | Generate a deterministic synthetic consumer panel with hidden archetypes available only for validation. | Seeded generator output; pipeline drops truth columns before modeling; synthetic recovery tests/reports. |
| O-2 | Represent behavioral timing separately from consumption magnitude. | 24 normalized hourly-shape features plus 27 summary features; feature tests and ablation outputs. |
| O-3 | Reduce the feature space and select a cluster count without using synthetic labels. | PCA variance threshold and recorded K-selection trace; clustering tests. |
| O-4 | Report both internal diagnostics and synthetic-only external recovery. | Silhouette/CH/DB/stability plus ARI/NMI sidecars. |
| O-5 | Export reproducible artifacts for review and static visualization. | Config hash, seed, package versions, manifest, JSON/CSV contract. |
| O-6 | Make the pipeline inspectable through interactive interfaces. | Streamlit smoke tests and Vite test/build. |
| O-7 | Keep native acceleration optional. | Python fallback and conditional C++ bridge tests. |

## Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | Generate synthetic observations from a configured number of consumers, days, and random seed. |
| FR-02 | Parse, order, validate, and preprocess records without filling across consumer boundaries. |
| FR-03 | Build behavioral, scale, or combined feature matrices and preserve consumer identity outside the numeric model matrix. |
| FR-04 | Standardize features, fit PCA, and record component selection and explained variance. |
| FR-05 | Sweep candidate K values, report metrics/stability, and persist the selection trace. |
| FR-06 | Use hidden archetypes only for post-fit validation when synthetic labels exist. |
| FR-07 | Save analysis artifacts and export a versioned static-web contract. |
| FR-08 | Run the same analysis interactively in Streamlit without overwriting committed reference outputs. |
| FR-09 | Provide separately documented UCI and London studies with input provenance and coverage caveats. |
| FR-10 | Allow an optional C++ backend without making it a runtime requirement. |

## Nonfunctional requirements

- **Reproducibility:** fixed seeds, pinned Python dependencies, npm lockfile, config hashes, input checksums where applicable.
- **Portability:** paths are resolved from the checkout or supplied as input; no machine-specific absolute paths in tracked files.
- **Scientific honesty:** distinguish synthetic, measured, and counterfactual evidence; do not infer causality from clustering.
- **Maintainability:** keep analysis stages in focused modules with tests around key contracts.
- **Usability:** provide exact install, run, and test instructions.
- **Security:** least-privilege CI, no embedded credentials, and clear reporting route for vulnerabilities.

## Scope boundaries

Implemented scope is synthetic clustering, exploratory measured-data analysis, result visualization, artifact export, and optional C++ kernels. Utility telemetry ingestion, customer-facing inference, dispatch/control, billing integration, causal demand-response evaluation, and production SLAs are out of scope.

