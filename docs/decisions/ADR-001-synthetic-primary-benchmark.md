# ADR-001: Keep synthetic data as the controlled primary benchmark

## Status

Accepted (retrospective interpretation)

## Context

The main pipeline has a seeded archetype-based generator and evaluates recovery against the generated archetype labels. The measured UCI and London analyses do not provide equivalent behavioral labels and have different coverage and schemas.

## Decision

Use synthetic data for controlled method validation. Keep UCI and London studies separate and exploratory; do not combine their labels or report their results as ground-truth recovery.

## Alternatives

- Treat anonymized meter/client IDs as household behavior classes.
- Pool the UCI, London, and generated observations into one validation set.
- Remove measured-data studies until a labeled dataset is available.

## Rationale and evidence

Retrospective interpretation based on current repository evidence: the synthetic generator exposes valid ground truth for recovery metrics, while the measured inputs do not. See `src/energy_analysis.py`, `research/run_uci_load_diagrams_validation.py`, and `research/run_london_household_validation.py`.

## Consequences and tradeoffs

Controlled recovery is reproducible but generator-specific. Real-data studies add plausibility checks, not external validation. A representative labeled or expert-reviewed dataset remains necessary for stronger claims.

