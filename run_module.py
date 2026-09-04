r"""Run a src/ module by bare name, avoiding path separators on the command line.

The `!` command handler in this project's workflow strips "/" and the Windows
backslash from pasted commands, so `py src/run_realworld.py --demo` can arrive
as `py srcrun_realworld.py --demo`. This launcher keeps the real path inside
Python (where separators are safe) and takes only a bare module name:

    py run_module.py run_realworld --demo
    py run_module.py energy_analysis
    py run_module.py run_seed_robustness

Run from the project root so relative output paths (outputs/, models/, ...)
resolve the same way `py src/<name>.py` would.
"""
from pathlib import Path
import runpy
import sys

SRC = Path(__file__).resolve().parent / "src"

if len(sys.argv) < 2:
    sys.exit("usage: py run_module.py <module_name> [args...]")

module_name = sys.argv[1]
script_path = SRC / f"{module_name}.py"
if not script_path.exists():
    sys.exit(f"no such module in src/: {module_name}.py")

# Tolerate the documented `module -- --flag` form. argparse treats a bare `--`
# as "everything after is positional", which would turn `-- --n_days 365` into
# the unrecognized positionals `--n_days 365`. Strip one leading `--` when
# present so `... module --n_days 365` and `... module -- --n_days 365` both
# reach the module as `--n_days 365`.
extra = sys.argv[2:]
if extra and extra[0] == '--':
    extra = extra[1:]

# Mimic `python src/<name>.py`: script path becomes argv[0], the script's
# directory is first on sys.path (so `from clustering import ...` resolves),
# and the script runs as __main__ (so its `if __name__ == "__main__"` block
# fires exactly as it would when launched directly).
sys.argv = [str(script_path)] + extra
sys.path.insert(0, str(SRC))
try:
    runpy.run_path(str(script_path), run_name="__main__")
except SystemExit as exc:  # argparse etc. exit with a code; preserve it
    raise SystemExit(exc.code if exc.code is not None else 0)