from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

import pandas as pd

from app.config import get_settings
from app.models.schemas import ClimateContext


CITY_CANDIDATES = ["city", "location", "station", "name"]
DATE_CANDIDATES = ["date", "time", "datetime"]
TEMP_MAX_CANDIDATES = ["temperature_2m_max", "temp_max", "tmax", "max_temperature", "maximum_temperature"]


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _find_column(columns: list[str], candidates: list[str]) -> str | None:
    normalized = {_normalize(c): c for c in columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    for norm, original in normalized.items():
        if any(candidate in norm for candidate in candidates):
            return original
    return None


@lru_cache(maxsize=1)
def _load_csv(path_string: str) -> pd.DataFrame | None:
    path = Path(path_string)
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def climate_context(city: str, current_max_temp: float | None, target_month: int | None = None) -> ClimateContext:
    settings = get_settings()
    df = _load_csv(str(settings.historical_path))
    if df is None:
        return ClimateContext(
            available=False,
            status="dataset_not_configured",
            note="Place the Kaggle historical CSV in data/ and set HISTORICAL_DATASET_PATH.",
        )

    city_col = _find_column(list(df.columns), CITY_CANDIDATES)
    date_col = _find_column(list(df.columns), DATE_CANDIDATES)
    temp_col = _find_column(list(df.columns), TEMP_MAX_CANDIDATES)
    if not city_col or not date_col or not temp_col:
        return ClimateContext(
            available=False,
            status="column_mapping_required",
            note=f"Could not auto-detect city/date/max-temperature columns. Columns found: {', '.join(map(str, df.columns[:12]))}",
        )

    work = df[[city_col, date_col, temp_col]].copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    work[temp_col] = pd.to_numeric(work[temp_col], errors="coerce")
    work = work.dropna()
    city_mask = work[city_col].astype(str).str.lower().str.contains(city.lower(), regex=False)
    work = work[city_mask]
    if target_month:
        work = work[work[date_col].dt.month == target_month]
    if work.empty:
        return ClimateContext(available=False, status="no_matching_history", note=f"No historical rows found for {city}.")

    normal = float(work[temp_col].mean())
    anomaly = None if current_max_temp is None else float(current_max_temp - normal)
    return ClimateContext(
        available=True,
        status="ok",
        metric="daily_max_temperature_c",
        current_value=current_max_temp,
        historical_normal=round(normal, 1),
        anomaly=round(anomaly, 1) if anomaly is not None else None,
        sample_size=len(work),
        note="Historical context from the locally supplied dataset; not a live forecast source.",
    )
