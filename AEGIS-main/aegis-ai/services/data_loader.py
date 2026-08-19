from pathlib import Path
from typing import Any

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXCEL_FILE = DATA_DIR / "AEGIS_Dummy_Datasets.xlsx"

EXPECTED_SHEETS = [
    "hospitals",
    "ambulances",
    "emergency_scenarios",
    "government_statistics_demo",
    "incidents",
    "cctv_metadata",
    "accident_clips_metadata",
    "ai_decisions",
]

_cache: dict[str, pd.DataFrame] | None = None


class DataLoadError(Exception):
    """Raised when the Excel workbook cannot be loaded."""


def _to_json_compatible(value: Any) -> Any:
    """Convert Pandas/NumPy values into JSON-compatible Python types."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, dict):
        return {key: _to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_json_compatible(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame into a list of JSON-safe dictionaries."""
    if df.empty:
        return []

    records = df.to_dict(orient="records")
    return [_to_json_compatible(record) for record in records]


def _load_sheet(all_sheets: dict[str, pd.DataFrame], sheet_name: str) -> pd.DataFrame:
    """Return a sheet DataFrame, or an empty DataFrame if the sheet is missing."""
    if sheet_name not in all_sheets:
        return pd.DataFrame()

    sheet_df = all_sheets[sheet_name]
    if sheet_df is None or sheet_df.empty:
        return pd.DataFrame()

    return sheet_df


def load_all_data(force_reload: bool = False) -> dict[str, pd.DataFrame]:
    """Load every expected sheet from the Excel workbook."""
    global _cache

    if _cache is not None and not force_reload:
        return _cache

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")

    try:
        all_sheets = pd.read_excel(EXCEL_FILE, sheet_name=None, engine="openpyxl")
    except Exception as exc:
        raise DataLoadError(f"Failed to read Excel file: {exc}") from exc

    loaded_data = {
        sheet_name: _load_sheet(all_sheets, sheet_name)
        for sheet_name in EXPECTED_SHEETS
    }

    _cache = loaded_data
    return loaded_data


def get_data_summary() -> dict[str, int]:
    """Return the number of rows in every dataset."""
    data = load_all_data()
    return {sheet_name: len(data.get(sheet_name, pd.DataFrame())) for sheet_name in EXPECTED_SHEETS}


def get_hospitals() -> list[dict[str, Any]]:
    """Return hospital records as JSON-compatible dictionaries."""
    data = load_all_data()
    return dataframe_to_records(data.get("hospitals", pd.DataFrame()))


def get_ambulances() -> list[dict[str, Any]]:
    """Return ambulance records as JSON-compatible dictionaries."""
    data = load_all_data()
    return dataframe_to_records(data.get("ambulances", pd.DataFrame()))


def get_incidents() -> list[dict[str, Any]]:
    """Return incident records as JSON-compatible dictionaries."""
    data = load_all_data()
    return dataframe_to_records(data.get("incidents", pd.DataFrame()))


def get_emergency_scenarios() -> list[dict[str, Any]]:
    """Return emergency scenario records as JSON-compatible dictionaries."""
    data = load_all_data()
    return dataframe_to_records(data.get("emergency_scenarios", pd.DataFrame()))
