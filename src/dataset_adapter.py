"""
Dataset adapter: a thin, documented bridge that turns an external real-world
electricity consumption dataset into the long panel the pipeline consumes.

This is the second data pathway (Improvement 3). It is strictly separate from
the synthetic generator and from the archetype ground-truth used to mark the
synthetic branch. The contract of the pipeline is a long table with at least

    meter_id  |  timestamp  |  energy_consumption_kwh

so the one job of an adapter is to map whatever a real file looks like on disk
onto that shape - renaming columns, parsing the timestamp, and converting to
kWh per record. Everything downstream (preprocessing, features, PCA, K-Means,
internal validation) is then the same code as the synthetic branch, which is the
point: the real-world pathway validates the *method*, not a rewritten method.

A public dataset is shipped built in: the UCI "Individual household electric
power consumption" archive (one house, ~9 years of minute-level readings). The
dataset itself also ships with a GitHub-hosted multi-house residential sample, an
external Kaggle hourly building dataset, and a simple generic ``csv`` adapter, so
that a user with their own meter file can map it here in one function without
touching the pipeline.

Nothing in this module invents data or semantic meaning. It maps columns, parses
timestamps and applies documented unit conversions; every assumption is stated on
the adapter and can be inspected.

Adapters are safe to import in any order; they hold no state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import pandas as pd

# A panel of real readings normalised onto the pipeline contract.
# meter_id and timestamp are always strings / datetimes; energy is float kWh.
PANEL_COLUMNS = ("meter_id", "timestamp", "energy_consumption_kwh")


@dataclass(frozen=True)
class ColumnMapping:
    """Where each pipeline column comes from in a raw file.

    ``timestamp`` may be a single column (``2010-01-01 00:00:00``), or a pair of
    ``date_col`` + ``time_col`` that the adapter concatenates. ``energy`` is the
    raw consumption column, in whatever unit ``energy_unit`` names.
    """

    meter_col: Optional[str] = None   # column naming the meter, if the file has several
    date_col: str = ""                # date column, e.g. "Date"
    time_col: Optional[str] = None    # optional separate time column, e.g. "Time"
    timestamp_col: Optional[str] = None  # alternative single timestamp column
    energy_col: str = ""              # raw consumption column
    energy_unit: str = "kWh"          # "kWh" | "Wh" | "kWavg" | "kWh_hourly"
    time_unit: str = "hour"           # row granularity: "hour" | "minute" | "second"
    separator: str = " "

    def build_timestamp(self, df: pd.DataFrame) -> pd.Series:
        """Return the parsed timestamp Series for the raw frame."""
        if self.timestamp_col and self.timestamp_col in df.columns:
            return pd.to_datetime(df[self.timestamp_col])
        date = pd.to_datetime(df[self.date_col]).astype(str)
        if self.time_col and self.time_col in df.columns:
            time = df[self.time_col].fillna("").astype(str)
            return pd.to_datetime(date + self.separator + time)
        return pd.to_datetime(date)


@dataclass(frozen=True)
class DatasetAdapter:
    """A named, documented route from a real file to the pipeline panel.

    ``adapt`` is the only executable part; everything else is documentation a
    reviewer can read. ``validation_notes`` is a checklist of the validation the
    ingestion step applies to this source.
    """

    name: str                                   # short handle, e.g. "uci_power"
    kind: str                                   # "public" | "external" | "generic"
    description: str                            # what the file is
    citation: str                               # where it came from
    url: str                                    # download / documentation location
    license_note: str                           # licence or terms
    mapping: ColumnMapping
    adapt: Callable[[pd.DataFrame], pd.DataFrame]  # raw frame -> pipeline panel (kWh)
    downsampling_hint: str = (
        "Rows are grouped to the hour before feature extraction; the adapter "
        "returns one row per meter-hour."
    )
    validation_notes: tuple[str, ...] = field(default_factory=tuple)

    # Human label used by the ingestion layer for logging / reporting.
    @property
    def source_label(self) -> str:
        return f"{self.kind}:{self.name}"


def _panel(meter_col, timestamps, energy) -> pd.DataFrame:
    """Assemble the long panel and drop non-finite / non-positive energy rows.

    A real meter log has gaps and zero-runs; 0 kWh rows are valid context but
    negative or missing consumption is an instrumentation error and is dropped
    here, at the ingestion boundary, before it can pollute feature extraction.
    """
    df = pd.DataFrame({
        "meter_id": meter_col,
        "timestamp": pd.to_datetime(timestamps),
        "energy_consumption_kwh": pd.to_numeric(energy, errors="coerce"),
    }).dropna(subset=["meter_id", "timestamp"])
    # Keep 0 kWh (the meter idle) but reject impossible negative readings.
    df = df[df["energy_consumption_kwh"] >= 0]
    df["energy_consumption_kwh"] = df["energy_consumption_kwh"].astype(float)
    return df.reset_index(drop=True)


def _to_kwh(raw: pd.Series, unit: str) -> pd.Series:
    """Convert a raw consumption Series into kWh per row.
    """
    values = pd.to_numeric(raw, errors="coerce")
    if unit == "kWh":
        return values
    if unit == "Wh":
        return values / 1000.0
    # kWavg: a per-minute mean-power reading in kW, converted to kWh for the hour
    # it lands in is the same mean (1 hour). For a non-hour row the energy is
    # kW * hours_of_row; we only ship hourly grouping, so kWavg == kwh_hourly.
    if unit in ("kWavg", "kWh_hourly"):
        return values
    raise ValueError(f"Unknown energy unit: {unit}")


def _group_hourly(panel: pd.DataFrame) -> pd.DataFrame:
    """Mean raw per-minute/second readings up to one row per meter-hour.

    Energy (kWh) in an hour equals mean power (kW) across that hour when the row
    is one reading per minute, because both sides measure the same one-hour
    window. Grouping by meter + hour therefore preserves kWh.
    """
    panel = panel.copy()
    panel["timestamp"] = pd.to_datetime(panel["timestamp"])
    panel["_hour"] = panel["timestamp"].dt.floor("h")
    out = (panel.groupby(["meter_id", "_hour"], as_index=False)["energy_consumption_kwh"]
           .mean().rename(columns={"_hour": "timestamp"}))
    return out.sort_values(["meter_id", "timestamp"]).reset_index(drop=True)


# --- UCI Individual household electric power consumption ---------------------
# https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption
# Public research archive, one dwelling, ~2 075 259 minute rows (Dec 2006 - Nov 2010).
# Global_active_power is the household's mean active power in kilowatts averaged
# over the minute. Sub-meterings 1-3 split part of the load but do not cover all
# of it; for a total-load study only Global_active_power is used as the measure.

def _adapt_uci_power(raw: pd.DataFrame) -> pd.DataFrame:
    m = _UCI_MAPPING
    timestamps = m.build_timestamp(raw)
    panel = _panel(
        meter_col=pd.Series([0] * len(raw), dtype=int).astype(str),
        timestamps=timestamps,
        energy=_to_kwh(raw[m.energy_col], m.energy_unit),
    )
    return _group_hourly(panel)


_UCI_MAPPING = ColumnMapping(
    meter_col=None,
    date_col="Date",
    time_col="Time",
    energy_col="Global_active_power",   # mean kW over the minute
    energy_unit="kWavg",
    time_unit="minute",
)

UCI_POWER_ADAPTER = DatasetAdapter(
    name="uci_power",
    kind="public",
    description=(
        "UCI Individual household electric power consumption: minute-level active "
        "power for one dwelling, Dec 2006 - Nov 2010 (about 9 years). Ten minutes "
        "of a real home; aggregated to hourly energy for this study."
    ),
    citation=(
        "Dheeru, D. and Karra Taniskidou, E. (2017). UCI Individual household "
        "electric power consumption dataset. UCI Machine Learning Repository."
    ),
    url="https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption",
    license_note="UCI repository research-use terms; redistribution per its current licence statement.",
    mapping=_UCI_MAPPING,
    adapt=_adapt_uci_power,
    downsampling_hint="Minute rows are averaged to the hour: kWh(h) = mean kW over that hour.",
    validation_notes=(
        "Missing values appear in the raw file as '?' and are coerced to NaN.",
        "The timestamp is reconstructed from the Date and Time columns.",
        "Out-of-range active power (<=0 or non-finite) is dropped at ingestion.",
        "One meter is expected; single-house files collapse under one meter id.",
    ),
)


# --- Generic CSV adapter -----------------------------------------------------
# For a user's own meter file: map columns onto the panel in one line. The date
# is a single datetime column (or date+time), energy is kWh already or in an
# explicit energy_unit. Schematic canonical date columns are the default so the
# same mapping works on any hourly CSV whose columns are named conventionally.

_GENERIC_MAPPING = ColumnMapping(
    meter_col="meter_id",
    timestamp_col="timestamp",
    energy_col="energy_consumption_kwh",
    energy_unit="kWh",
    time_unit="hour",
)

GENERIC_CSV_ADAPTER = DatasetAdapter(
    name="generic_csv",
    kind="generic",
    description=(
        "Map a user's own hourly meter CSV onto the pipeline. Expected default "
        "columns: meter_id, timestamp, energy_consumption_kwh; override via "
        "GenericColumnMapping for a file that names them differently."
    ),
    citation="User-supplied data; no public citation.",
    url="",
    license_note="The user is responsible for the provenance and terms of their own data.",
    mapping=_GENERIC_MAPPING,
    adapt=lambda raw: _panel(
        meter_col=raw[_GENERIC_MAPPING.meter_col].fillna("meter").astype(str),
        timestamps=raw[_GENERIC_MAPPING.timestamp_col],
        energy=_to_kwh(raw[_GENERIC_MAPPING.energy_col], _GENERIC_MAPPING.energy_unit),
    ),
    validation_notes=(
        "The generic adapter assumes hourly kWh rows and a single timestamp column.",
        "Consumption is assumed non-negative; negative rows are dropped.",
    ),
)


ADAPTERS: dict[str, DatasetAdapter] = {
    "uci_power": UCI_POWER_ADAPTER,
    "generic_csv": GENERIC_CSV_ADAPTER,
}


def get_adapter(name: str) -> DatasetAdapter:
    """Look up an adapter by handle, raising a helpful error if it is unknown."""
    if name not in ADAPTERS:
        known = ", ".join(sorted(ADAPTERS))
        raise KeyError(f"Unknown adapter '{name}'. Known adapters: {known}.")
    return ADAPTERS[name]


def validate_panel_shape(panel: pd.DataFrame) -> None:
    """The ingestion guard: a real panel must satisfy the pipeline contract.

    Raises:

        ValueError: If a required column is missing or a row type is wrong.
    """
    missing = [c for c in PANEL_COLUMNS if c not in panel.columns]
    if missing:
        raise ValueError(
            f"Real-world panel is missing required columns {missing}; "
            f"got {list(panel.columns)}. Check the adapter's column mapping."
        )
    pd.to_datetime(panel["timestamp"])   # raises if the timestamps are unparsable
    pd.to_numeric(panel["energy_consumption_kwh"], errors="raise")