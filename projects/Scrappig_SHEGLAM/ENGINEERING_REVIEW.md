# Engineering review — Scrappig_SHEGLAM

**Review date:** 2026-10-14  
**Repository:** `Abdulrahman181/Scrappig_SHEGLAM`  
**Scope:** all tracked Python, Notebook, README, and repository-level dependency/config files.

## Executive summary

The repository contained a Streamlit dashboard and one large exploratory notebook, but no
requirements file, ignore rules, tests, or product CSV. The dashboard attempted to read
`sheglam_products.csv` at import time and would crash before showing an actionable message.
The notebook contained stale outputs and environment-specific paths from Windows and Colab.

The project is an exploratory scraping/analytics project, not a supervised ML training
pipeline. Consequently, there is no train/test split, model, or predictive metric to
validate. I did not invent a dataset, scrape the live site, or report analytics results.

## Work completed

- Added `data_utils.py` as the single CSV boundary. It resolves paths, checks the required
  six-column schema, rejects empty/unusable files, normalises prices and best-seller flags,
  bounds ratings to `0..5`, and converts invalid source values to missing rather than
  silently guessing replacements.
- Refactored `app.py` to use a repository-relative default or `SHEGLAM_DATA_PATH`, fail
  closed with a clear Streamlit message when data is missing/invalid, and guard empty
  selections, all-missing numeric columns, empty groupings, missing collection matches,
  and missing optional WordCloud support. Plot figures are closed after rendering.
- Replaced the 46-cell historical notebook with a seven-cell, output-free, reproducible
  analysis notebook using the same loader. Removed stale results, the Windows
  `chromedriver` path, `/content/SHEGLAM.csv`, local MongoDB insertion, and references to
  unavailable image artifacts. No credentials or generated data were retained.
- Added `requirements.txt` with bounded runtime dependencies. `pymongo` is documented as
  optional/commented because database export is not part of the supported dashboard path.
- Added `.gitignore` rules for scraped CSVs, generated images, notebook checkpoints,
  environments, caches, and local configuration.
- Added three offline tests in `tests/test_data_utils.py` covering type normalisation,
  missing-data messaging, and schema rejection.
- Added `validate_project.py` for lightweight AST and notebook-JSON checks.
- Rewrote `README.md` with the data contract, setup commands, reproducibility limitations,
  and explicit no-fabrication behavior.

## Findings and risk assessment

### Fixed — high impact

1. **Missing artifact crash:** the original `app.py` used a bare `pd.read_csv("sheglam_products.csv")`.
   The CSV is not present in the repository. The new loader stops with an actionable error.
2. **Missing dependency declaration:** imports included Streamlit, Plotly, Seaborn, and
   WordCloud without `requirements.txt`. A bounded requirements file is now present.
3. **Hard-coded local paths:** the notebook referenced a Windows ChromeDriver path and a
   Colab `/content` CSV path. Both were removed.
4. **Stale notebook state:** the original notebook had 46 cells, 40 stored outputs, image
   references, a localhost MongoDB insert, and stateful cells that produced undefined-name
   reports when checked independently. The notebook is now output-free and self-contained
   around the validated data boundary.
5. **Fragile empty-data behavior:** the dashboard used positional indexing (`iloc[0]`),
   `idxmin`, and unconditional WordCloud/chart generation. These paths are now guarded.
6. **Schema/type assumptions:** prices, ratings, and flags were cast without error handling.
   The loader now validates columns and performs explicit, non-fabricating coercion.

### Reviewed — no model leakage claim

- No model training, target construction, train/test split, cross-validation, or predictive
  metric exists in the repository. Therefore a leakage audit for a predictive pipeline is
  not applicable; the report and README do not claim model performance.
- The dashboard is descriptive and computes statistics only from the supplied CSV. Best
  Seller is treated as a source field, not as a model target.

### Security/API review

- No API keys, passwords, or committed credentials were found in the inspected source.
- The original notebook's MongoDB insertion was removed from the supported workflow; no
  network/database side effect occurs during dashboard import.
- The Streamlit app accepts only a configured local path through `SHEGLAM_DATA_PATH`; it
  does not execute CSV contents or build shell commands from user input.
- Selenium collection remains site-dependent and is not executed by the dashboard. Its
  selectors should be revalidated against SHEGLAM before a fresh collection.

## Validation performed

- `python -m pytest -q` — **3 passed**.
- `ruff check app.py data_utils.py validate_project.py tests /tmp/sheglam_notebook_combined.py` — **passed**.
- `python validate_project.py` — **passed** (AST and Notebook JSON).
- `python -m compileall -q app.py data_utils.py validate_project.py tests` — **passed**.
- Notebook inspection — **0 stored outputs**, no Windows/Colab paths, no MongoDB localhost
  reference, no image artifact references.
- `git diff --check` — **passed**.

## Limitations and unexecuted paths

- No `sheglam_products.csv` or `SHEGLAM.csv` exists in the checkout, so no full dashboard
  run or data-dependent analysis was performed. This is intentional; no data was invented.
- The sandbox has pandas, matplotlib, Seaborn, Plotly, and pytest, but does not have the
  declared `streamlit`, `wordcloud`, `selenium`, or `nbformat` packages installed. The
  dependency declaration was added, but those heavy/runtime paths were not claimed as
  executed.
- The live website was not scraped. Selenium behavior and current CSS selectors therefore
  remain unverified against the live site.
- The PDF was treated as a reference artifact and was not modified.

## Commit policy

A local commit was created only in this checkout. No changes were pushed to GitHub and no
other repository was modified.

## Second Senior Review

**Review date:** 2026-10-16
**Reviewer scope:** all tracked source, tests, notebook JSON, README, requirements,
repository configuration, Git history/diff, and the tracked PDF reference.

### Findings and fixes

1. **Empty CSV crash at the data boundary — fixed.** `pandas.errors.EmptyDataError`
   was not handled, so a zero-byte export escaped as a traceback instead of the
   dashboard's actionable validation error. `load_products()` now converts it to
   `DataValidationError` alongside parser, filesystem, and encoding failures.
2. **Best-seller coercion could fabricate flags — fixed.** Numeric values were rounded
   before conversion, so values such as `0.4` could become `0`. Normalization now accepts
   only explicit boolean values or exact `0`/`1` spellings (including `0.0`/`1.0`), and
   leaves fractional/unknown values missing.
3. **Invalid numeric values could pollute analysis — fixed.** Negative and infinite
   prices, and infinite ratings, are now treated as missing. No clipping, imputation, or
   guessed replacement is performed. Blank category/name/subcategory strings become
   missing values, preventing an empty filter option or collection token.
4. **Required schema ambiguity — fixed.** Duplicate column labels are rejected before
   column access, avoiding pandas' ambiguous DataFrame-vs-Series behavior.
5. **Visualization all-missing edge cases — fixed.** Category and seller charts now
   omit all-missing metric series rather than handing NaN-only values to Seaborn or
   Plotly. Existing empty-data messages remain fail-closed.
6. **Notebook portability and state checks — fixed.** The notebook finds the repository
   by walking current-directory parents and adds it to `sys.path`, so launching Jupyter
   from a child directory does not silently import the wrong module. The project validator
   now parses Python files under tests, verifies notebook format/cell types, rejects stored
   outputs and execution counts, and checks for known stale local/database paths.
7. **Test setup contract — fixed.** `pytest` is now declared in `requirements.txt`, matching
   the documented validation command. Five additional offline tests cover empty files,
   strict flag coercion, invalid/non-finite prices, and blank text normalization.
8. **Plotting dependency compatibility — fixed.** A real Streamlit smoke test exposed that
   an unconstrained NumPy/SciPy/PyArrow combination could fail during Seaborn or
   `st.dataframe` import. Requirements now constrain NumPy/SciPy to a compatible modern
   wheel range for the declared Streamlit stack. `pytest` coverage also includes duplicate
   column labels (five new edge-case tests in total).

### Validation performed in the second review

- `python -m pytest -q` — **8 passed**.
- `python validate_project.py` — **passed**, including recursive AST and notebook-state checks.
- `python -m compileall -q app.py data_utils.py validate_project.py tests` — **passed**.
- `ruff check .` — **passed** after the intentional notebook bootstrap import annotation.
- `git diff --check` — **passed**.
- Streamlit `AppTest` with a temporary two/three-row CSV — **passed with no exceptions**,
  including missing-source and all-missing-price branches. A temporary `streamlit run`
  health check also returned `ok`; no temporary data was committed.
- Notebook inspection — **7 cells, 0 stored outputs, all code execution counts null**.
- Edge probes — empty artifact, fractional flags, decimal flags, invalid prices, and blank
  text all follow the documented missing-value behavior.
- No product CSV, credentials, generated images, or tracked cache artifacts were added.

### Remaining risks and explicit non-claims

- No product CSV is present, so data-dependent dashboard execution and analytics cannot be
  honestly claimed. No rows, metrics, or model performance were invented.
- The repository still has no scraper implementation in the tracked source; the historical
  PDF describes Selenium collection, but current selectors and live-site behavior remain
  unverified. `selenium` remains a declared dependency for that external workflow only.
- Streamlit and WordCloud were installed only in the disposable sandbox for the smoke test;
  Selenium/live scraping and a full notebook kernel execution remain unverified. The smoke
  test does not constitute a live-site or data-scale end-to-end claim.
- This remains descriptive exploration, not a predictive ML pipeline; train/test leakage and
  predictive metrics are therefore not applicable.
