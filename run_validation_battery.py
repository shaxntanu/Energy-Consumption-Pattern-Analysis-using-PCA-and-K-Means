r"""Run the full validation battery end to end, one command.

Each step runs as its own fresh interpreter through the exact launcher a
reviewer would use (run_module.py for src/ modules, verify_compile.py for the
compile gate), so the battery exercises the documented command line rather than
an internal shortcut.

Every step's stdout and stderr are captured to logs/validation_battery/<tag>.log
and, for the energy-analysis steps, the resulting analysis_summary.md is
archived alongside as <tag>_analysis_summary.md. The 365-day run is deliberately
the LAST energy-analysis step, so when the battery finishes, models/,
outputs/ and the web/public/data contract all describe the full-year flagship
run, and the archived per-horizon summaries keep the 30/90/180-day numbers
quotable even though the canonical summary only describes the last run.

Steps (in order):

    compile_gate      verify_compile.py                 (every .py compiles)
    30d / 90d / 180d  energy_analysis --n_days N --n_consumers 200
    realworld_demo    run_realworld --demo              (internal-only metrics)
    ablation          run_ablation_study                (5 feature-set arms)
    seed_robustness   run_seed_robustness               (5 arms x 20 datasets)
    365d              energy_analysis --n_days 365 --n_consumers 200
    export_artifacts  export_artifacts                  (web/public/data contract)

A failed step does not stop the battery (a transient failure in one horizon must
not prevent the flagship 365-day run and its export from completing), but the
exit code is 1 if ANY step failed, so the clean-clone check and any CI fail loud.

Run via:  py run_validation_battery.py
"""
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs" / "validation_battery"
RESULTS_PATH = LOG_DIR / "results.json"

# (tag, (module_or_script, [args...])). compile_gate runs the root script
# directly; everything else runs through run_module.py, which resolves the
# module inside src/ and executes it exactly as `py run_module.py <name>`.
STEPS = [
    ('compile_gate', ('verify_compile', [])),
    ('30d', ('energy_analysis', ['--n_days', '30', '--n_consumers', '200'])),
    ('90d', ('energy_analysis', ['--n_days', '90', '--n_consumers', '200'])),
    ('180d', ('energy_analysis', ['--n_days', '180', '--n_consumers', '200'])),
    ('realworld_demo', ('run_realworld', ['--demo'])),
    ('ablation', ('run_ablation_study', [])),
    ('seed_robustness', ('run_seed_robustness', [])),
    ('365d', ('energy_analysis', ['--n_days', '365', '--n_consumers', '200'])),
    ('export_artifacts', ('export_artifacts', [])),
]

# Tags whose step leaves a fresh outputs/reports/analysis_summary.md worth
# archiving (the energy_analysis runs). The real-world, ablation and seed
# studies write their own reports and are not summary producers.
SUMMARY_PRODUCERS = {'30d', '90d', '180d', '365d'}


def _command_for(module: str, args: list) -> list:
    """The documented command line for one step.

    Returns:
        argv list with the same interpreter that is running the battery.
    """
    if module == 'verify_compile':
        return [sys.executable, str(ROOT / 'verify_compile.py')] + args
    return [sys.executable, str(ROOT / 'run_module.py'), module] + args


def _run_step(tag: str, module: str, args: list) -> dict:
    """Run one step, capture its output, and record the outcome.

    Returns:
        A results row for results.json.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{tag}.log"
    command = _command_for(module, args)

    print(f"=== {tag}: running {module} {args}", flush=True)
    start = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
        output = proc.stdout
        returncode = proc.returncode
    except Exception as exc:  # pragma: no cover - process spawn failures
        output = f"Failed to launch {command}: {exc}\n"
        returncode = -1

    elapsed = time.monotonic() - start
    ok = returncode == 0
    log_path.write_text(output, encoding='utf-8')

    if ok and tag in SUMMARY_PRODUCERS:
        summary_src = ROOT / 'outputs' / 'reports' / 'analysis_summary.md'
        if summary_src.exists():
            archive = LOG_DIR / f"{tag}_analysis_summary.md"
            archive.write_text(summary_src.read_text(encoding='utf-8'),
                               encoding='utf-8')

    status = "OK" if ok else f"FAILED (exit {returncode})"
    print(f"=== {tag}: {status} in {elapsed:.1f}s -> {log_path.relative_to(ROOT)}",
          flush=True)
    if not ok:
        # Surface the tail of the failure in the battery's own output so a
        # background run is diagnosable without opening the log.
        tail = "\n".join(output.splitlines()[-30:])
        print(f"--- tail of {tag}.log ---\n{tail}\n---", flush=True)

    return {
        'tag': tag,
        'module': module,
        'args': args,
        'exit_code': returncode,
        'ok': ok,
        'elapsed_seconds': round(elapsed, 2),
        'log': str(log_path.relative_to(ROOT)),
    }


def _write_results(rows: list, shap_available: bool, started_utc: str) -> None:
    """Write the running results.json (also called after each step)."""
    n_ok = sum(1 for r in rows if r['ok'])
    payload = {
        'started_utc': started_utc,
        'finished_utc': datetime.now(timezone.utc).isoformat(),
        'shap_available': shap_available,
        'n_ok': n_ok,
        'n_failed': len(rows) - n_ok,
        'status': 'PASS' if n_ok == len(rows) else 'FAIL',
        'steps': rows,
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def main() -> int:
    os.chdir(ROOT)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    shap_available = importlib.util.find_spec('shap') is not None
    print(f"Shap probe: {'shap installed -> explainability method will be SHAP' if shap_available
          else 'shap NOT installed -> explainability falls back to permutation_importance'}")
    print(f"Battery root: {ROOT}")
    print(f"Steps: {len(STEPS)} -> {', '.join(tag for tag, _ in STEPS)}\n", flush=True)

    started_utc = datetime.now(timezone.utc).isoformat()
    rows = []
    for tag, (module, args) in STEPS:
        row = _run_step(tag, module, args)
        rows.append(row)
        _write_results(rows, shap_available, started_utc)

    n_ok = sum(1 for r in rows if r['ok'])
    n_failed = len(rows) - n_ok

    print("\n" + "=" * 72)
    print("VALIDATION BATTERY SUMMARY")
    print("=" * 72)
    for row in rows:
        mark = "OK " if row['ok'] else "FAIL"
        print(f"  [{mark}] {row['tag']:<18} {row['elapsed_seconds']:>8.1f}s"
              f"  {row['log']}")
    print("-" * 72)
    print(f"  Passed {n_ok}/{len(rows)} steps, failed {n_failed}.")
    print(f"  Results written to {RESULTS_PATH.relative_to(ROOT)}")
    if n_failed:
        print("  >>> EXIT 1: at least one step failed. See the per-step logs above.")
    return 1 if n_failed else 0


if __name__ == "__main__":
    sys.exit(main())