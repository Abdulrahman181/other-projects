from pathlib import Path

import pandas as pd
import pytest

from data_utils import DataValidationError, clean_products, load_products

COLUMNS = ["Category", "Name", "Price", "Stars", "Subcategory", "Best Seller"]


def write_csv(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    path = tmp_path / "products.csv"
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, index=False)
    return path


def test_load_products_normalises_types_without_fabricating_values(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        [
            {
                "Category": " Face ",
                "Name": "Example blush",
                "Price": "$1,299.50",
                "Stars": "4.5",
                "Subcategory": "Blush",
                "Best Seller": "yes",
            },
            {
                "Category": "Eyes",
                "Name": "No price",
                "Price": "not available",
                "Stars": "6",
                "Subcategory": "Mascara",
                "Best Seller": "unknown",
            },
        ],
    )

    frame = load_products(path)

    assert frame.loc[0, "Category"] == "Face"
    assert frame.loc[0, "Price"] == 1299.50
    assert frame.loc[0, "Best Seller"] == 1
    assert pd.isna(frame.loc[1, "Price"])
    assert pd.isna(frame.loc[1, "Stars"])
    assert pd.isna(frame.loc[1, "Best Seller"])


def test_missing_data_fails_with_actionable_message(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Run the scraper first"):
        load_products(tmp_path / "missing.csv")


def test_missing_column_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "products.csv"
    pd.DataFrame({"Name": ["Only a name"]}).to_csv(path, index=False)

    with pytest.raises(DataValidationError, match="required column"):
        load_products(path)


def test_empty_csv_is_reported_as_invalid_data(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    with pytest.raises(DataValidationError, match="Could not read product CSV"):
        load_products(path)


def test_best_seller_does_not_round_fractional_values(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        [
            {
                "Category": "Face",
                "Name": "Fractional flag",
                "Price": "1",
                "Stars": "4",
                "Subcategory": "Blush",
                "Best Seller": value,
            }
            for value in (0.4, 1.5, "1.0", "0.0", "true")
        ],
    )

    flags = load_products(path)["Best Seller"].tolist()

    assert pd.isna(flags[0])
    assert pd.isna(flags[1])
    assert flags[2:5] == [1, 0, 1]


def test_invalid_and_nonfinite_prices_become_missing(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        [
            {
                "Category": "Face",
                "Name": f"Product {value}",
                "Price": value,
                "Stars": "4",
                "Subcategory": "Blush",
                "Best Seller": "no",
            }
            for value in ("-1", "inf", "2.50")
        ],
    )

    frame = load_products(path)

    assert pd.isna(frame.loc[0, "Price"])
    assert pd.isna(frame.loc[1, "Price"])
    assert frame.loc[2, "Price"] == 2.5


def test_blank_text_fields_are_missing_not_filter_values(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        [
            {
                "Category": "  ",
                "Name": "Valid name",
                "Price": "1",
                "Stars": "4",
                "Subcategory": "  ",
                "Best Seller": "no",
            },
            {
                "Category": "Face",
                "Name": "  ",
                "Price": "1",
                "Stars": "4",
                "Subcategory": "Blush",
                "Best Seller": "no",
            },
            {
                "Category": "Face",
                "Name": "Valid product",
                "Price": "1",
                "Stars": "4",
                "Subcategory": "Blush",
                "Best Seller": "no",
            },
        ],
    )

    frame = load_products(path)

    assert frame["Category"].isna().sum() == 1
    assert frame["Name"].isna().sum() == 1
    assert frame["Subcategory"].isna().sum() == 1


def test_duplicate_column_labels_are_rejected() -> None:
    frame = pd.DataFrame(
        [["Face", "duplicate", "name", 1, 4, "Blush", "no"]],
        columns=["Category", "Name", "Name", "Price", "Stars", "Subcategory", "Best Seller"],
    )

    with pytest.raises(DataValidationError, match="duplicate column"):
        clean_products(frame)
