# ADR-002: Keep the C++ backend optional

## Status

Accepted (retrospective interpretation)

## Context

The repository contains pybind11 PCA and K-Means kernels and a Python/scikit-learn reference pipeline. Native builds depend on compiler and ABI availability.

## Decision

Keep C++ acceleration optional and preserve Python as the default reference/fallback implementation.

## Alternatives

- Require a native build for every user.
- Remove the C++ engine.
- Select native kernels automatically whenever they can be imported.

## Rationale and evidence

Retrospective interpretation based on current repository evidence: `src/cpp_bridge.py` handles unavailable modules and defines Python fallback behavior; `tests/test_cpp_bridge.py` exercises that contract.

## Consequences and tradeoffs

The base install remains portable. Native parity and speed claims require a built module and machine-specific tests. The optional build adds maintenance across Python ABI and compiler versions.

