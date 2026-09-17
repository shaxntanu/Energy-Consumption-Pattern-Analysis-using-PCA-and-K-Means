"""Regression tests for export isolation and descriptive ML correctness."""
import builtins
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.metrics import get_scorer

import energy_analysis
from energy_analysis import AnalysisConfig, EnergyAnalysis
from explainability import _load_shap, _permutation_importance
from preprocessing import handle_missing_values


@pytest.mark.parametrize('custom_outputs, custom_models', [(True, True), (True, False), (False, True)])
def test_isolated_run_does_not_publish_web_artifacts(tmp_path, monkeypatch, custom_outputs, custom_models):
    root = Path(energy_analysis.__file__).resolve().parents[1]
    config = AnalysisConfig(
        output_dir=str(tmp_path / 'outputs' if custom_outputs else root / 'outputs'),
        model_dir=str(tmp_path / 'models' if custom_models else root / 'models'),
    )
    exporter = Mock()
    monkeypatch.setattr(energy_analysis, 'export_artifacts', exporter)

    EnergyAnalysis(config)._export_web_artifacts()

    exporter.assert_not_called()
    assert not (tmp_path / 'outputs').exists()
    assert not (tmp_path / 'models').exists()


@pytest.mark.parametrize('absolute', [False, True])
def test_canonical_run_still_publishes_web_artifacts(monkeypatch, absolute):
    root = Path(energy_analysis.__file__).resolve().parents[1]
    monkeypatch.chdir(root)
    config = AnalysisConfig(
        output_dir=str(root / 'outputs') if absolute else 'outputs',
        model_dir=str(root / 'models') if absolute else 'models',
    )
    exporter = Mock(return_value={'manifest': {}, 'csv_mirrors': []})
    monkeypatch.setattr(energy_analysis, 'export_artifacts', exporter)

    EnergyAnalysis(config)._export_web_artifacts()

    exporter.assert_called_once_with()


def test_relative_paths_outside_project_are_isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exporter = Mock()
    monkeypatch.setattr(energy_analysis, 'export_artifacts', exporter)
    EnergyAnalysis(AnalysisConfig())._export_web_artifacts()
    exporter.assert_not_called()


def test_group_mean_never_borrows_another_consumers_readings():
    frame = pd.DataFrame({
        'consumer_id': [1.0, 1.0, 2.0, 2.0, np.nan],
        'energy_consumption_kwh': [2.0, np.nan, np.nan, np.nan, np.nan],
    })
    original = frame.copy(deep=True)
    result = handle_missing_values(frame, strategy='mean')
    np.testing.assert_allclose(result.loc[:1, 'energy_consumption_kwh'], [2.0, 2.0])
    assert result.loc[2:, 'energy_consumption_kwh'].isna().all()
    assert pd.isna(result.loc[4, 'consumer_id'])
    pd.testing.assert_frame_equal(frame, original)


def test_mean_without_group_column_preserves_global_fallback():
    frame = pd.DataFrame({'value': [2.0, np.nan, 4.0]})
    result = handle_missing_values(frame, strategy='mean')
    np.testing.assert_allclose(result['value'], [2.0, 3.0, 4.0])


def test_permutation_importance_uses_balanced_accuracy(monkeypatch):
    # A majority-only classifier scores 75% accuracy but 50% balanced accuracy.
    # Exercise the scoring argument at the real sklearn scoring boundary.
    X = np.arange(16, dtype=float).reshape(8, 2)
    labels = np.array([0] * 6 + [1] * 2)
    calls = []
    monkeypatch.setattr(
        'sklearn.ensemble.RandomForestClassifier',
        lambda **kwargs: DummyClassifier(strategy='most_frequent'),
    )

    def inspect_importance(clf, values, binary, **kwargs):
        assert kwargs['scoring'] == 'balanced_accuracy'
        assert clf.score(values, binary) == pytest.approx(0.75)
        assert get_scorer(kwargs['scoring'])(clf, values, binary) == pytest.approx(0.5)
        calls.append(binary.copy())
        return SimpleNamespace(importances_mean=np.array([0.2, 0.1]))

    monkeypatch.setattr('sklearn.inspection.permutation_importance', inspect_importance)
    per_cluster, global_importance = _permutation_importance(X, labels, ['a', 'b'])
    assert len(calls) == len(per_cluster) == 2
    assert all(item['top_features'][0]['feature'] == 'a' for item in per_cluster)
    assert all(item['top_features'][0]['direction'] is None for item in per_cluster)
    assert global_importance['top_features'][0]['importance'] == pytest.approx(0.2)


def test_shap_import_failure_is_logged_with_its_actual_exception(monkeypatch, caplog):
    real_import = builtins.__import__

    def broken_shap_import(name, *args, **kwargs):
        if name == 'shap':
            raise ImportError('simulated incompatible SHAP binary')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', broken_shap_import)
    with caplog.at_level(logging.WARNING, logger='explainability'):
        assert _load_shap() is None

    assert 'ImportError: simulated incompatible SHAP binary' in caplog.text
