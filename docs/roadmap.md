# Roadmap

Items are proposals, not commitments. Priorities depend on obtaining complete data and defining a validation question.

## Immediate

- [ ] Re-run the London study against the complete source archive and publish the exact source checksum and selection protocol.
- [ ] Complete a reproducible C++ versus Python timing report with hardware, compiler, library versions, thread settings, raw trials, and parity checks.
- [ ] Extend automated coverage for the UCI/London ingestion and experiment-sidecar schemas.
- [ ] Refresh the four checked-in SBOMs whenever dependency pins or the npm lockfile change, and review the inventory diff with the dependency audit.

## Short term

- [ ] Test the segmentation on an independent, labeled or expert-reviewed household dataset.
- [ ] Investigate temporal drift and K-selection sensitivity before making deployment recommendations.
- [ ] Validate the versioned Python-to-web artifact contract in CI against a fresh export.

## Medium term

- [ ] Evaluate cluster stability under missingness, coverage variation, outlier policies, and population shifts.
- [ ] Design a preregistered, controlled evaluation if a demand-response intervention is proposed.
- [ ] Document a supported C++ build matrix across Windows, Linux, and macOS.

## Long term

- [ ] Consider a utility-facing inference service only after privacy, security, validation, monitoring, and operational requirements are specified.
- [ ] Measure actual energy outcomes before making efficiency, cost, or emissions claims.

