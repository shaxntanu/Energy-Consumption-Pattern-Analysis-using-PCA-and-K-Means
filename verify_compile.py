r"""Compile every Python file in the project without path separators on the CLI.

The `!` command handler in this project's workflow strips "/" and the Windows
backslash from pasted commands, so a normal
`py -m py_compile src\data_loader.py ...` arrives with `src` and
`data_loader.py` glued together (`srcdata_loader.py`). This script instead
walks the project from its own location and compiles each file, so the command
line needs no path separator at all:

    py verify_compile.py

Exit code is 0 only if every .py file in the project (root + src/) compiles.
"""
from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parent
targets = sorted(ROOT.glob("*.py")) + sorted((ROOT / "src").glob("*.py"))

failed = []
for path in targets:
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:  # noqa: PERF203 - one file per loop
        failed.append((path.name, str(exc)))

print(f"Compiled {len(targets) - len(failed)}/{len(targets)} files.")
for name, exc in failed:
    print(f"FAIL  {name}: {exc}")

if failed:
    print(f"\n{len(failed)} file(s) failed to compile.")
    sys.exit(1)
print("All project Python files compile.")