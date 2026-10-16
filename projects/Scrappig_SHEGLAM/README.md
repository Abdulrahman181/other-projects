# Scrapping SHEGLAM

A small, reproducible Python project for collecting and exploring SHEGLAM product
metadata (name, price, category, rating, subcategory, and best-seller flag).
The Streamlit dashboard reads a reviewed CSV export; it does **not** manufacture
rows or metrics when the export is absent.

## Repository layout

- `app.py` — Streamlit dashboard with guarded loading and empty-data handling.
- `data_utils.py` — CSV path resolution, schema validation, and type cleaning.
- `SHEGLAM_WEB_SCRAPING.ipynb` — clean, output-free analysis notebook.
- `tests/test_data_utils.py` — offline tests for the data boundary.
- `requirements.txt` — runtime dependencies.

## Data contract

Place a scraper export at `sheglam_products.csv` in the repository directory, or
set `SHEGLAM_DATA_PATH` to an absolute or repository-relative CSV path. The CSV
must contain these columns:

`Category`, `Name`, `Price`, `Stars`, `Subcategory`, `Best Seller`

Prices may include `$` and commas. Ratings outside `0..5` and unrecognised
best-seller flags are treated as missing, not replaced with guessed values. If the
file is missing, empty, or lacks the required schema, the dashboard stops with an
actionable message.

## Local usage

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

A browser driver and a working internet connection are required for live Selenium
collection. The collection selectors are site-dependent and should be checked
against the current SHEGLAM site before a fresh scrape. No scraped dataset is
committed to this repository.

## Reproducibility and scope

The project is descriptive exploration, not a supervised ML model. There is no
train/test split or predictive metric to report, and no leakage-safe model
pipeline is claimed. Dashboard statistics are calculated only from the supplied
CSV and are not evidence of causal effects.

## Dashboard

An historical hosted dashboard link may be available in the project history, but
local execution is the supported path. Do not rely on a hosted app for data
freshness or reproducibility.
