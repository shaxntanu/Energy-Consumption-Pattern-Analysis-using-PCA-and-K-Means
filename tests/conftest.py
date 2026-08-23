"""
Shared pytest fixtures. Tests import from src/ via sys.path.
"""
import os
import sys
from pathlib import Path

# Headless-safe plotting before any matplotlib import in src modules
os.environ.setdefault('MPLBACKEND', 'Agg')

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data_loader import generate_synthetic_data
from preprocessing import preprocess_pipeline
from feature_engineering import engineer_all_features, select_features


@pytest.fixture(scope='session')
def small_raw():
    """A small panel that still contains weekends.

    The generator starts on 2024-01-01, a Monday. Anything shorter than 7 days
    holds no Saturday or Sunday, which silently drops weekend_ratio and
    weekend_shape_distance from the feature set and hides bugs in them. 14 days
    gives two full weekends while staying fast.
    """
    return generate_synthetic_data(n_consumers=20, n_days=14, hourly_records=True, random_seed=42)


@pytest.fixture(scope='session')
def small_preprocessed(small_raw):
    return preprocess_pipeline(small_raw.drop(columns=['archetype']), remove_outliers_flag=False)


@pytest.fixture(scope='session')
def small_features(small_preprocessed):
    return engineer_all_features(small_preprocessed, feature_set='behavioral')
