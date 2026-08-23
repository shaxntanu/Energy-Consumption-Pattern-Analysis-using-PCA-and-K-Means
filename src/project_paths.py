"""
Project Paths Module

Every other module takes its output directory as an argument and defaults to a
path relative to the current working directory, which is the right behaviour for
a library. It is the wrong behaviour for a script: running
`py src/energy_analysis.py` from inside src/ would write a second copy of every
artifact to src/outputs/, and the repository would then hold two sets of numbers
that disagree.

The scripts therefore anchor themselves to the project root before writing
anything. The root is found from this file's location, so nothing here depends on
where the repository was cloned or on which directory the user is in.
"""

import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / 'src'
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = PROJECT_ROOT / 'models'
OUTPUTS_DIR = PROJECT_ROOT / 'outputs'
FIGURES_DIR = OUTPUTS_DIR / 'figures'
METRICS_DIR = OUTPUTS_DIR / 'metrics'
REPORTS_DIR = OUTPUTS_DIR / 'reports'


def anchor_to_project_root() -> Path:
    """Change the working directory to the project root.

    Call this at the start of a script's __main__ block, before any module with a
    relative output path default is used. Importing this module does not change
    the working directory; only calling this function does.

    Returns:
        The project root.
    """
    current = Path.cwd().resolve()
    if current != PROJECT_ROOT:
        os.chdir(PROJECT_ROOT)
        logger.info(f"Working directory set to the project root: {PROJECT_ROOT}")
    return PROJECT_ROOT
