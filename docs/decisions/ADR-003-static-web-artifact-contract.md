# ADR-003: Keep the Vercel explorer static and artifact-driven

## Status

Accepted (retrospective interpretation)

## Context

The repository contains a Python analysis pipeline and a separate Vite/React frontend deployed to Vercel.

## Decision

Export a versioned JSON/CSV contract from Python to `web/public/data/`; have the frontend render those artifacts without running the model.

## Alternatives

- Reimplement PCA and clustering in browser JavaScript.
- Add a server API between the site and the Python pipeline.
- Make the frontend read arbitrary local files.

## Rationale and evidence

Retrospective interpretation based on current repository evidence: `src/export_artifacts.py` defines the contract and manifest; `web/src/` reads static data; `web/vercel.json` configures a static Vite deployment.

## Consequences and tradeoffs

Deployment is simple and reproducible, but the displayed content updates only when artifacts are regenerated and the site is redeployed. The export contract must remain compatible across Python and frontend changes.

