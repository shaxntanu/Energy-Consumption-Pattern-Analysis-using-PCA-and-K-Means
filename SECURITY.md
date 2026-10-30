# Security policy

## Scope

The public Vercel app is a static artifact viewer. The Streamlit app runs a configurable research pipeline. The repository also contains local-file research scripts and an optional native extension. This is not a production energy-management service.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting or security advisory feature for this repository if it is enabled. If that channel is unavailable, contact the maintainer through the contact method listed on the GitHub profile. Do not publish exploitable details in a public issue before a fix is available.

## Current controls and residual risk

- CI workflows request read-only repository permissions and do not publish or push artifacts.
- The Docker image runs as an unprivileged numeric UID and excludes environment files, secrets, raw datasets, and Git metadata from its build context.
- The Streamlit interface exposes analysis parameters; research scripts accept local paths. Treat local input data as trusted and keep sensitive meter data out of public artifacts.
- No credentials should be stored in source, notebooks, workflow files, or committed environment files.
- The optional C++ extension adds native-code risk and should only be built from reviewed source.
- Python requirements are pinned and the web app has a committed npm lockfile. CycloneDX inventories are stored in [`sbom/`](sbom/README.md).

## Dependency review

Install development tools and run the Python audit from the repository root:

```powershell
py -3.14 -m pip install -r requirements-dev.txt
py -3.14 -m pip_audit -r requirements.txt -s osv
py -3.14 -m pip_audit -r requirements-dev.txt -s osv
py -3.14 -m pip_audit -r visualizations/manimgx/requirements.txt -s osv
```

Audit the web lockfile and regenerate all SBOMs with:

```powershell
cd web
npm audit --omit=optional
cd ..
python scripts/generate_sbom.py
```

The Python audit requires access to its vulnerability service. A network timeout is not a clean audit result; record it as inconclusive and retry when connectivity is available.

