# Repository audit and maturity assessment

**Review date:** 2026-11-02

**Scope:** architecture, source claims, user interfaces, research methods, tests, dependencies, security controls, reproducibility, documentation, and repository hygiene.

## Summary

This repository is a research prototype with a Python and Streamlit analysis pipeline, a static React and Vite results site, measured-data study scripts, a LaTeX manuscript, and an optional C++ extension. The principal reference result is synthetic. The UCI and London studies are limited exploratory analyses. The load-shift study is a retrospective counterfactual. None of these results demonstrates energy savings or a production-ready utility service.

The audit found that the Vercel page contradicted the evidence and its own research documentation in the SDG section. It claimed an unsupported quarterly stability value, utility-scale readiness, a possible 50x speedup, and relevance to several SDGs that the project documentation explicitly disclaims. Its technology strip also named frameworks not used by the project. Those statements have been corrected in source. Existing Python analysis results and the dark visual system were preserved.

## Repository overview

| Area | Role |
|---|---|
| `src/` | Reusable validation, preprocessing, feature, PCA, clustering, export, and optional C++ bridge modules. |
| `streamlit_app.py` and `src/dashboard_*.py` | Interactive local analysis interface that runs the Python pipeline. The configured theme is dark. |
| `research/` | Study-specific adapters and scripts for UCI and London data. |
| `web/` | Static React and Vite site that reads committed artifacts. It does not fit models. |
| `cpp_engine/` | Optional native kernels. Python and scikit-learn remain the reference implementation. |
| `outputs/`, `models/`, `web/public/data/` | Saved plots, reports, metrics, models, and versioned web artifacts. |
| `visualizations/`, `docs/visualizations/` | ManimGX source and Anatomy figure sources. Existing outputs include source files and rendered media. |
| `paper/` | LaTeX manuscript source and a previously compiled PDF. |
| `tests/`, `.github/workflows/`, `Dockerfile`, `sbom/` | Automated checks, CI, container packaging, and software inventories. |

See [architecture](architecture.md), [methodology](METHODOLOGY.md), [limitations](limitations.md), and [visualizations](visualizations.md) for the detailed contracts and evidence boundaries.

## Initial condition

At the start of this review, the repository already had broad project documentation, test suites, pinned Python requirements, an npm lockfile, four CycloneDX SBOM files, read-only CI permissions, Docker hardening, and a dark Streamlit palette. Existing tests and builds were available to validate the changes. The Streamlit configuration disabled CORS while XSRF protection was enabled.

The main problems found were:

- The SDG section on the Vercel page contradicted [`docs/sdg-alignment.md`](sdg-alignment.md). It declared SDGs 9, 11, 12, and 13 as supported or indirect goals even though the assessment says no such contributions are claimed.
- The page reported quarterly ARI mean 0.92. The saved longitudinal metrics report mean ARI 0.8817.
- The page described production-grade utility-scale readiness, a 50x speedup potential, and 150M+ meter scalability without supporting evidence. The committed C++ benchmark reports a 1.32x end-to-end speedup for its stated workload, and the software is not an operational service.
- The footer listed Next.js, TypeScript, Tailwind CSS, and Three.js as stack technologies although they are not the project's implemented web stack.
- The roadmap proposed adding an SBOM even though four SBOMs were already checked in.
- There was no central registry distinguishing installed or used skills from references in the supplied prompt.
- The Streamlit configuration disabled CORS while XSRF was enabled, leaving cross-origin WebSocket connections unrestricted according to the startup warning.

The audit began from `main` at `dd381ba` with the configured Git identity `shaxntanu <i.shantanu2807@gmail.com>`. No repository history was rewritten.

## Major problems found

The research methods and limits were already documented well, but the public-facing SDG card and footer did not follow those documents. The public page therefore overstated impact and implementation scale. The roadmap and missing skill registry were documentation maintenance gaps. No defect was found that required changing the saved analysis results.

## Architecture findings

- Synthetic generation, measured-data ingestion, analysis, export, and presentation are separated across modules and scripts.
- The static Vercel app reads versioned JSON and CSV outputs. It does not execute Python or train a model.
- Streamlit runs the analysis pipeline for selected controls and stores session output separately from committed results.
- C++ kernels are optional and have a Python fallback.
- No utility feed connector, demand-response controller, or deployed inference service is present.
- Existing Mermaid architecture and research figures explain distinct aspects of the system. The audit did not add a duplicate diagram or animation.

## Improvements implemented

- Replaced the Vercel SDG hierarchy with one evidence-limited card for potential relevance to SDG 7, Target 7.3. Removed unsupported claims about other goals, efficiency impact, deployment scale, speedup, and incorrect longitudinal stability.
- Replaced inaccurate technology logos with the actual project tools: Python, Streamlit, scikit-learn, NumPy, Plotly, React, Vite, Chart.js, and C++.
- Constrained the single SDG card to a readable width while preserving the existing dark palette.
- Enabled Streamlit CORS protection, retained XSRF protection, and allowlisted the deployed Streamlit app origin.
- Corrected the roadmap to maintain and refresh the four existing SBOMs after dependency changes.
- Added a skills and tools reference that records prompt references, local availability, actual use, artifacts, validation, and not-applicable tooling.
- Linked the new reference from the root README.

No analysis algorithm, input dataset, saved result, or license was changed.

## Files added

- `docs/AI_SKILLS_REFERENCE.md`

## Files modified

- `README.md`
- `docs/REPOSITORY_AUDIT.md`
- `docs/roadmap.md`
- `.streamlit/config.toml`
- `web/src/main.jsx`
- `web/src/components/LogoLoop.jsx`
- `web/src/styles.css`

## Testing performed

| Check | Result | Notes |
|---|---|---|
| Python test suite | 168 passed, 5 skipped | Two scikit-learn warnings report rare classes with fewer than five members in cross-validation folds. |
| Web tests | 14 passed | Includes application logic and the load-shift figure model. |
| Streamlit application | Passed | Restarted with CORS enabled and the deployed app origin allowlisted. The local browser loaded the dark simulator, controls, metrics, and charts. The origin check accepted the deployed origin and rejected an unrelated origin. |
| Vite production build | Passed | Builds the React app and the versioned Anatomy figure. Main JavaScript bundle is 576.02 kB before gzip and 190.40 kB after gzip, above Vite's 500 kB warning threshold. |
| npm audit | 0 known vulnerabilities | Ran with `--omit=optional` against the web lockfile. |
| ManimGX dependency audit | No known vulnerabilities found | OSV service responded for the renderer requirement set. |
| Python runtime and development dependency audit | Inconclusive | The OSV request timed out. This is not a clean audit result. |
| Docker image build | Not completed | Docker Hub TLS handshake timed out while retrieving `python:3.14-slim`. |
| Paper compilation | Not run | No `pdflatex`, `latexmk`, `tectonic`, or Biber executable is available in this environment. |
| Git whitespace check | Passed | `git diff --check` reported no whitespace errors. |
| Personal path scan | Passed for tracked text files | No machine-specific user paths were found in tracked text. The `/home/app` path in the Dockerfile is a generic container path. |

The Python tests ran in a task-specific virtual environment with repository development requirements installed. It used system site packages to reuse existing scientific dependencies, so this was not a clean-machine installation test. The global Python installation was not modified.

## Security findings

- CI requests read-only `contents` permission and does not publish artifacts or push commits.
- The Dockerfile runs as a non-root numeric user. `.dockerignore` excludes raw data, secrets, and Git metadata.
- Streamlit now has CORS and XSRF protection enabled, with the deployed app origin allowlisted. Local access was verified after restart. Hosted deployment behavior was not verified.
- No secret pattern or personal absolute path was found in the tracked text scan.
- The web dependency scan found no known vulnerabilities.
- The Python dependency scan could not complete because the OSV service timed out. Retry it when connectivity is available.
- LFS pointers for the UCI and Kaggle datasets are present. Remote LFS object availability was not checked or changed during this audit.
- The optional C++ extension remains a native-code risk and should be built from reviewed source.

## Dependency findings

Python runtime and development requirements are pinned, the web app has a committed npm lockfile, and CycloneDX files exist for web, Python runtime, Python development, and ManimGX renderer dependencies. The roadmap now calls for refreshing those inventories when the declarations change. The failed Docker Hub request prevented checking the container build against the currently published base image.

## Documentation improvements

The root README links to the new [AI skills and tool reference](AI_SKILLS_REFERENCE.md). The audit now records the repository boundary, evidence-backed UI corrections, validation results, limits, and maturity scores. The historical verification matrix remains labelled historical and points to the current audit. The roadmap no longer asks for an SBOM that already exists.

## Research improvements

No research result was recomputed or relabelled. The Vercel page now reports the synthetic-label ARI accurately and describes SDG 7.3 as potential research relevance. It states that no efficiency outcome, bill saving, emissions reduction, or participant response was measured. The UCI and London analyses remain exploratory and do not gain fabricated behavioral labels.

## Reproducibility improvements

The repository already records configuration hashes, seeds, study protocols, sidecars, dependency versions, and a versioned web artifact contract. This audit preserved those outputs and corrected their public-facing interpretation. It also clarified the SBOM refresh task. A clean-clone installation, Docker image build, LFS remote check, and fresh paper compile remain unverified.

## Traceability status

The existing [traceability matrix](traceability.md) links requirements to implementation and tests. It correctly marks most research and application behavior as partially verified because measured-data studies are not covered by a full-data automated regression suite and several behaviors depend on optional data or native compilation. This audit did not upgrade those statuses without new evidence.

## Remaining limitations

- Synthetic ARI and NMI measure recovery of labels created by the synthetic generator, not classification accuracy for real consumers.
- The UCI client panel has no behavioral ground truth. The London analysis covers a filtered subset and is not population-representative.
- The counterfactual load-shift study does not observe participant response or demonstrate causal, cost, emissions, or system-level savings.
- An independent labeled or expert-reviewed consumer dataset is still needed for external validation.
- The Docker build, full Python advisory scan, fresh paper compilation, clean-clone smoke check, and LFS remote verification remain outstanding.
- The Vite bundle is above the configured warning threshold and can be split if the web app grows.
- `web/src/main.jsx` remains a large module and could be decomposed in a separate behavior-preserving refactor.

## Initial maturity score

Scores use a 0 to 5 scale and the supplied category weights. The initial score refers to the repository at the beginning of this audit, not to an empty project. No category was excluded or reweighted.

| Dimension | Weight | Score | Weighted points | Evidence and gap |
|---|---:|---:|---:|---|
| Architecture and modularity | 15% | 4.0 / 5 | 12.0 / 15 | Distinct pipeline, measured-data scripts, UI, exports, and optional C++ path; no separate data-contract package or full clean-clone check. |
| Documentation | 15% | 3.0 / 5 | 9.0 / 15 | Broad methods and limitations documentation existed, but the UI contradicted its SDG assessment and roadmap, and no skills registry existed. |
| Code quality | 15% | 3.0 / 5 | 9.0 / 15 | Python modules and tests were present; the web page had stale claims, a false stack list, and a large monolithic entry file. |
| Testing | 15% | 4.0 / 5 | 12.0 / 15 | Substantial Python and web suites existed; measured-data full runs and optional native builds are not always regression-tested. |
| Security | 10% | 3.5 / 5 | 7.0 / 10 | Read-only CI, pinned dependencies, SBOMs, non-root Docker; Python advisory status and container build were not yet verified. |
| Reproducibility | 10% | 3.0 / 5 | 6.0 / 10 | Seeds, config hashes, sidecars, and versioned exports existed; clean clone, Docker, LFS remote, and paper rebuild were unverified. |
| Open-source governance | 10% | 4.0 / 5 | 8.0 / 10 | License, citation metadata, contributing guidance, security policy, and CI existed; community process remains small. |
| Research rigor and traceability | 10% | 3.5 / 5 | 7.0 / 10 | Research limits and result sidecars existed, but public SDG claims overstated what they support and external labeled validation is absent. |
| **Initial total** | **100%** |  | **70.0 / 100** |  |

## Final maturity score

| Dimension | Weight | Score | Weighted points | Evidence and remaining gap |
|---|---:|---:|---:|---|
| Architecture and modularity | 15% | 4.0 / 5 | 12.0 / 15 | Same evidence-backed separation as the initial review; a clean-clone check remains. |
| Documentation | 15% | 4.5 / 5 | 13.5 / 15 | Audit, skills registry, README navigation, SBOM roadmap, and page claims now agree; the historical verification snapshot still contains old instructions by design. |
| Code quality | 15% | 3.5 / 5 | 10.5 / 15 | False stack entries and unsupported SDG content are removed; the large web entry module remains. |
| Testing | 15% | 4.0 / 5 | 12.0 / 15 | 168 Python tests passed, 5 skipped, and 14 web tests passed; full measured-data and native build coverage remains limited. |
| Security | 10% | 4.0 / 5 | 8.0 / 10 | CORS and XSRF protections are enabled and the web audit is clean; the Python scan timed out at OSV and the Docker build could not reach Docker Hub. |
| Reproducibility | 10% | 3.0 / 5 | 6.0 / 10 | Existing metadata and reproducibility instructions are intact; clean clone, container, LFS remote, and PDF rebuild are still open. |
| Open-source governance | 10% | 4.0 / 5 | 8.0 / 10 | Existing governance files and CI remain in place; community participation has not been evaluated. |
| Research rigor and traceability | 10% | 4.0 / 5 | 8.0 / 10 | Public SDG and technology claims now match the source and methods documents; external validation remains an open research need. |
| **Final total** | **100%** |  | **78.0 / 100** |  |

The weighted increase is 8 points. This reflects corrections to public claims, documentation, and the Streamlit cross-origin security setting. It does not mean that the research has gained new empirical validation or is ready for utility deployment.

## Recommended next actions

1. Run the Python runtime and development dependency audits when the OSV service is reachable.
2. Build the Docker image in an environment that can reach Docker Hub.
3. Verify both LFS objects from a fresh clone without uploading them as part of this work.
4. Compile the LaTeX manuscript with its required toolchain and review the generated PDF.
5. Evaluate the method on an independent labeled or expert-reviewed dataset before claiming real-world behavioral accuracy.
6. Split the Vite bundle and the large web entry module only if that work can be done without changing the saved analysis contract.
