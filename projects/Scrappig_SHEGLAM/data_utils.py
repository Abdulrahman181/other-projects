"""Data loading and validation helpers for the SHEGLAM dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "Category",
    "Name",
    "Price",
    "Stars",
    "Subcategory",
    "Best Seller",
)


class DataValidationError(ValueError):
    """Raised when a SHEGLAM CSV cannot support the dashboard."""


def _normalise_best_seller(series: pd.Series) -> pd.Series:
    """Convert common boolean/flag representations to nullable integers."""
    if pd.api.types.is_bool_dtype(series):
        return series.astype("Int64")

    values = series.astype("string").str.strip().str.lower()
    mapped = values.map(
        {
            "1": 1,
            "true": 1,
            "yes": 1,
            "y": 1,
            "0": 0,
            "false": 0,
            "no": 0,
            "n": 0,
        }
    )
    # Accept numeric spellings such as ``1.0`` only when they are exactly
    # integral flags.  Rounding arbitrary values (for example, 0.4 -> 0)
    # would silently change source data.
    numeric = pd.to_numeric(values, errors="coerce")
    exact_numeric = numeric.where(numeric.isin([0, 1]))
    mapped = mapped.fillna(exact_numeric)
    return mapped.astype("Int64")


def validate_products(frame: pd.DataFrame) -> None:
    """Validate the minimum schema and usable content without creating values."""
    duplicate_columns = frame.columns[frame.columns.duplicated()].tolist()
    if duplicate_columns:
        raise DataValidationError(
            "CSV contains duplicate column label(s): "
            + ", ".join(map(str, duplicate_columns))
        )
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise DataValidationError(
            "CSV schema is missing required column(s): " + ", ".join(missing)
        )
    if frame.empty:
        raise DataValidationError(
            "CSV contains no product rows; collect data before opening the dashboard."
        )

    usable_names = frame["Name"].astype("string").str.strip().ne("").fillna(False)
    usable_categories = frame["Category"].astype("string").str.strip().ne("").fillna(False)
    if not (usable_names & usable_categories).any():
        raise DataValidationError("CSV has no rows with both a product Name and Category.")


def clean_products(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a typed copy; invalid source values become missing, never fabricated."""
    validate_products(frame)
    cleaned = frame.copy()
    for column in ("Category", "Name", "Subcategory"):
        cleaned[column] = (
            cleaned[column].astype("string").str.strip().replace("", pd.NA)
        )

    cleaned["Price"] = pd.to_numeric(
        cleaned["Price"].astype("string").str.replace(r"[$,]", "", regex=True),
        errors="coerce",
    )
    # Negative or non-finite prices are not meaningful product prices and are
    # kept missing rather than being clipped or otherwise guessed.
    invalid_prices = cleaned["Price"].notna() & (
        cleaned["Price"].lt(0)
        | cleaned["Price"].isin([float("inf"), float("-inf")])
    )
    cleaned.loc[invalid_prices, "Price"] = pd.NA
    cleaned["Stars"] = pd.to_numeric(cleaned["Stars"], errors="coerce")
    cleaned.loc[
        cleaned["Stars"].notna()
        & cleaned["Stars"].isin([float("inf"), float("-inf")]),
        "Stars",
    ] = pd.NA
    cleaned["Best Seller"] = _normalise_best_seller(cleaned["Best Seller"])

    invalid_stars = cleaned["Stars"].notna() & ~cleaned["Stars"].between(0, 5)
    cleaned.loc[invalid_stars, "Stars"] = pd.NA
    invalid_flags = cleaned["Best Seller"].notna() & ~cleaned["Best Seller"].isin([0, 1])
    cleaned.loc[invalid_flags, "Best Seller"] = pd.NA
    return cleaned


def load_products(path: str | Path) -> pd.DataFrame:
    """Load and validate a product CSV with actionable artifact errors."""
    csv_path = Path(path).expanduser()
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Product data not found at '{csv_path}'. Run the scraper first and save sheglam_products.csv."
        )
    try:
        frame = pd.read_csv(csv_path)
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ) as exc:
        raise DataValidationError(f"Could not read product CSV '{csv_path}': {exc}") from exc
    return clean_products(frame)
