"""
Real-world data ingestion (Improvement 3, ingestion layer).

This module sits *before* the pipeline and takes a real electricity dataset to a
long panel the rest of the code can consume. It is deliberately kept separate
from the synthetic generator: the synthetic branch knows which consumers exist
and can be marked against them; the real branch does not, and must not pretend
otherwise. Real-world results are therefore evaluated only with internal
indices and stability, never with ARI/NMI against fabricated archetypes.

A real dataset has no ground-truth label, has arbitrary identifiers, and can
have gaps, '*?'* placeholders and inconsistent units - so ingestion is the one
place where the raw file is first *validated*: schema checks, timestamp parsing,
energy-unit conversion, missing-value accounting, and a per-meter continuity
summary are all recorded here and carried into the report. None of that hides a
problem; it surfaces it.

This module performs no modelling. Its output is:

- a validated long panel (meter_id, timestamp, energy_consumption_kwh), and
- a dict of ingestion facts (source, rows read, meters, date span, missing
  counts, adapters run) for the report and for the validation layer.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from dataset_adapter import (
    ADAPTERS,
    DatasetAdapter,
    get_adapter,
    validate_panel_shape,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RealWorldConfig:
    """Everything needed to load and validate a real-world dataset.

    Args:
        source_path: Path to the raw file (CSV). Optional when ``adapter`` is
            "generic_csv" and ``inline_frame`` is supplied.
        adapter: Handle of a registered DatasetAdapter ("uci_power" or
            "generic_csv" today).
        meter_cap: Cap on the number of meters kept, so a huge archive can be
            studied on a student laptop. None keeps them all.
        date_start: Optional inclusive floor for the window (date string).
        date_end: Optional inclusive ceiling for the window (date string).
        run_table: If set, write the validated panel to this CSV path.
    """

    source_path: Optional[str] = None
    adapter: str = "generic_csv"
    meter_cap: Optional[int] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    run_table: Optional[str] = None
    # Hosting the frame directly avoids a file round-trip for smoke tests.
    inline_frame: Optional[pd.DataFrame] = None

    def effective_adapter(self) -> DatasetAdapter:
        return get_adapter(self.adapter)


def _read_raw(config: RealWorldConfig) -> pd.DataFrame:
    """Read the raw file (or inline frame) the adapter expects."""
    if config.inline_frame is not None:
        return config.inline_frame
    if not config.source_path:
        raise ValueError(
            "RealWorldConfig needs either source_path or inline_frame."
        )
    path = Path(config.source_path)
    if not path.exists():
        raise FileNotFoundError(f"Real-world source not found: {path}")
    return pd.read_csv(path, low_memory=False)


def _window(panel: pd.DataFrame, config: RealWorldConfig) -> pd.DataFrame:
    """Apply the requested date window and meter cap, if any."""
    panel = panel.copy()
    panel["timestamp"] = pd.to_datetime(panel["timestamp"])
    if config.date_start is not None:
        panel = panel[panel["timestamp"] >= pd.Timestamp(config.date_start)]
    if config.date_end is not None:
        panel = panel[panel["timestamp"] <= pd.Timestamp(config.date_end)]
    if config.meter_cap is not None and config.meter_cap > 0:
        meters = panel["meter_id"].drop_duplicates()
        panel = panel[panel["meter_id"].isin(meters.head(config.meter_cap))]
    return panel


def _ingestion_facts(panel: pd.DataFrame, adapter: DatasetAdapter,
                     config: RealWorldConfig, rows_read: int) -> dict:
    """A compact, reportable summary of what ingestion saw."""
    panel = panel.copy()
    panel["timestamp"] = pd.to_datetime(panel["timestamp"])
    n_meters = panel["meter_id"].nunique()
    per_meter = panel.groupby("meter_id")["timestamp"].agg(["min", "max", "count"])
    facts = {
        "source": adapter.source_label,
        "source_name": adapter.name,
        "description": adapter.description,
        "citation": adapter.citation,
        "url": adapter.url,
        "license": adapter.license_note,
        "rows_read": int(rows_read),
        "rows_after_cleaning": int(len(panel)),
        "meters": int(n_meters),
        "date_start": str(panel["timestamp"].min()),
        "date_end": str(panel["timestamp"].max()),
        "records_per_meter": {
            str(m): {
                "first": str(r["min"]),
                "last": str(r["max"]),
                "n": int(r["count"]),
            }
            for m, r in per_meter.iterrows()
        },
        "missing_per_field": {
            c: int(panel[c].isna().sum()) for c in ("meter_id", "timestamp", "energy_consumption_kwh")
        },
        "negative_dropped": int((panel["energy_consumption_kwh"] < 0).sum()),
        "validation_notes": list(adapter.validation_notes),
        "config": {
            "adapter": config.adapter,
            "source_path": config.source_path,
            "meter_cap": config.meter_cap,
            "date_start": config.date_start,
            "date_end": config.date_end,
        },
    }
    return facts


def ingest(config: RealWorldConfig) -> tuple[pd.DataFrame, dict]:
    """Load, validate and clean a real-world dataset into the pipeline panel.

    Args:
        config: The RealWorldConfig describing the source, adapter and window.

    Returns:
        Tuple of (validated panel, ingestion facts dict).
    """
    adapter = config.effective_adapter()
    raw = _read_raw(config)
    rows_read = len(raw)

    panel = adapter.adapt(raw)
    panel["timestamp"] = pd.to_datetime(panel["timestamp"])
    panel["meter_id"] = panel["meter_id"].astype(str)

    validate_panel_shape(panel)                      # contract guard
    panel = _window(panel, config)                   # date / meter selection

    facts = _ingestion_facts(panel, adapter, config, rows_read)

    if config.run_table:
        out = Path(config.run_table)
        out.parent.mkdir(parents=True, exist_ok=True)
        panel.to_csv(out, index=False)
        logger.info("Wrote validated real-world panel to %s", out)

    logger.info(
        "Ingested '%s' -> %d rows, %d meters, %s to %s",
        adapter.name, len(panel), panel["meter_id"].nunique(),
        panel["timestamp"].min(), panel["timestamp"].max(),
    )
    return panel, facts


# --- lightweight in-repo demo dataset ----------------------------------------
# A tiny, fully synthetic *provenance* for the real-world pathway's smoke test.
# This is NOT the study's evidence and is clearly labelled as such: it exists so
# the real-world pipeline (ingest -> features -> PCA -> KMeans -> internal
# validation) can be exercised from end to end on a student laptop without a
# multi-gigabyte download. It is not used for any reported finding.

_CANONICAL_HOURLY_COLS = ["meter_id", "timestamp", "energy_consumption_kwh"]


def make_demo_panel(n_meters: int = 24, n_days: int = 21, seed: int = 7,
                    start: str = "2025-01-06") -> pd.DataFrame:
    """A small multi-meter daily-load panel for the real pathway's smoke test.

    Two coarse behaviour groups (day-peaking and evening-peaking) plus noise and
    a weekend effect. Keep the same mixing as the study's *design* but clearly
    NOT the synthetic archetype used for graded results - this only exercises the
    ingestion + internal-validation plumbing end to end.

    Returns a frame already on the panel contract (generic_csv adapter).
    """
    rng = np.random.default_rng(seed)
    hours = np.arange(24)
    rows = []
    # n_days of *hours* (one row per meter-hour), so the window actually spans
    # the requested number of days and therefore includes both weekdays and
    # weekend days. With periods=n_days we would only make n_days hours.
    ts = pd.date_range(start=start, periods=n_days * 24, freq="h")
    for m in range(n_meters):
        peak = 8 if m % 2 == 0 else 19
        base = 0.35 + 0.4 * rng.random()
        for t in ts:
            hour = t.hour
            # a bump centred on `peak`, plus a flat baseline and weekend lift
            shape1 = np.exp(-0.5 * ((hour - peak) / 2.6) ** 2)
            shape2 = np.exp(-0.5 * ((hour - (peak + 4)) / 3.2) ** 2)
            weekend = 1.25 if t.weekday() >= 5 else 1.0
            value = base * weekend * (0.35 + 1.5 * shape1 + 0.45 * shape2)
            value *= 1 + 0.12 * rng.standard_normal()
            rows.append((str(m), t, float(max(0.0, value))))
    return pd.DataFrame(rows, columns=_CANONICAL_HOURLY_COLS)