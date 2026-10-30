# Contributing

Contributions should keep the analysis reproducible and the claims proportional to the evidence.

## Before opening a change

1. Read [the architecture](docs/architecture.md), [methodology](docs/METHODOLOGY.md), and [limitations](docs/limitations.md).
2. For research results, include the input source/checksum, configuration, seed, scripts, raw or machine-readable outputs, and interpretation limits.
3. Keep synthetic recovery, measured-data analysis, and counterfactual scenarios clearly separated.
4. Do not commit credentials, local environment files, personal absolute paths, generated caches, or downloaded datasets without an attribution/license review.

## Verification

For Python changes, run:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

For frontend changes, run from `web/`:

```bash
npm ci
npm test
npm run build
```

For the optional C++ engine, record the compiler, Python ABI, build flags, and parity evidence. A missing local compiler should be reported; it is not a reason to present unverified performance claims.

## Pull requests

Describe the behavior changed, evidence added, tests run, data/license impact, and remaining limitations. Do not include generated PDFs or large data unless needed and approved by the project’s existing policies.

