# Software bills of materials

This directory contains CycloneDX JSON inventories for the dependency sets used by the web app, Python runtime, Python development tools, and optional ManimGX renderer. The SBOMs describe software packages only; they do not inventory project datasets or research outputs.

Regenerate them from the repository root after installing the development dependencies and Node.js:

```powershell
py -3.14 -m pip install -r requirements-dev.txt
python scripts/generate_sbom.py
```

The generator uses the npm lockfile for the web app and `pip-audit` for the pinned Python requirement files. Python generation also checks the dependency vulnerability feed; resolve reported advisories before treating the inventory as a clean audit. Review dependency upgrades, rerun tests, and regenerate the files together.
