"""Lightweight offline checks for source files and the notebook."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTEBOOK_NAME = "SHEGLAM_WEB_SCRAPING.ipynb"
FORBIDDEN_NOTEBOOK_REFERENCES = (
    "chromedriver",
    "/content/",
    "mongodb://localhost",
    "mongodb://127.0.0.1",
)


def _validate_python_files(failures: list[str]) -> None:
    """Parse every tracked-looking Python source file, including tests."""
    for path in sorted(ROOT.rglob("*.py")):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f"{path}: {exc}")


def _validate_notebook(path: Path, failures: list[str]) -> None:
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"{path}: {exc}")
        return

    if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
        failures.append(f"{path}: expected nbformat 4 notebook with a cells list")
        return

    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") not in {"code", "markdown", "raw"}:
            failures.append(f"{path}: cell {index} has an invalid cell_type")
        source = cell.get("source", [])
        source_text = "".join(source) if isinstance(source, list) else str(source)
        lowered = source_text.lower()
        for forbidden in FORBIDDEN_NOTEBOOK_REFERENCES:
            if forbidden in lowered:
                failures.append(f"{path}: cell {index} contains {forbidden!r}")
        if cell.get("cell_type") == "code":
            if cell.get("execution_count") is not None:
                failures.append(f"{path}: code cell {index} has an execution count")
            if cell.get("outputs"):
                failures.append(f"{path}: code cell {index} contains stored outputs")


def main() -> int:
    failures: list[str] = []
    _validate_python_files(failures)
    _validate_notebook(ROOT / NOTEBOOK_NAME, failures)

    if failures:
        print("Validation failed:")
        print("\n".join(failures))
        return 1
    print("AST and notebook JSON validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
