"""Generate CycloneDX SBOMs for the Python and web dependency sets."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "sbom"


def run(command: list[str], *, cwd: Path, output: Path | None = None) -> None:
    """Run a generator, validate its JSON output, and save it atomically."""
    if os.name == "nt" and command[0] == "npm":
        command = ["cmd.exe", "/d", "/c", *command]
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{detail}")

    if output is not None:
        payload = result.stdout
        if not payload:
            raise RuntimeError(f"Command produced no JSON: {' '.join(command)}")
        json.loads(payload)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(payload + "\n", encoding="utf-8")
        temporary.replace(output)


def generate_pip_sbom(requirements: Path, destination: Path) -> None:
    temporary = destination.with_suffix(".pending.cdx.json")
    command = [
        sys.executable,
        "-m",
        "pip_audit",
        "--requirement",
        str(requirements),
        "--format",
        "cyclonedx-json",
        "--vulnerability-service",
        "osv",
        "--output",
        str(temporary),
        "--timeout",
        "60",
    ]
    transient_markers = (
        "RemoteDisconnected",
        "Connection aborted",
        "Read timed out",
        "timed out",
        "HTTP 429",
        "HTTP 502",
        "HTTP 503",
        "HTTP 504",
    )
    try:
        for attempt in range(3):
            temporary.unlink(missing_ok=True)
            result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            detail = result.stderr.strip() or result.stdout.strip()
            if result.returncode == 0 and temporary.is_file():
                json.loads(temporary.read_text(encoding="utf-8"))
                temporary.replace(destination)
                return
            if result.returncode and attempt < 2 and any(
                marker.lower() in detail.lower() for marker in transient_markers
            ):
                time.sleep(2**attempt)
                continue
            raise RuntimeError(
                f"SBOM generation or dependency audit failed ({result.returncode}): {detail}"
            )
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    try:
        run(
            [
                "npm",
                "sbom",
                "--package-lock-only",
                "--sbom-format",
                "cyclonedx",
                "--sbom-type",
                "application",
            ],
            cwd=ROOT / "web",
            output=OUTPUT / "web.cdx.json",
        )
        generate_pip_sbom(ROOT / "requirements.txt", OUTPUT / "python-runtime.cdx.json")
        generate_pip_sbom(ROOT / "requirements-dev.txt", OUTPUT / "python-dev.cdx.json")
        generate_pip_sbom(
            ROOT / "visualizations" / "manimgx" / "requirements.txt",
            OUTPUT / "manimgx-rendering.cdx.json",
        )
    except (OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Generated 4 CycloneDX SBOMs in {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
