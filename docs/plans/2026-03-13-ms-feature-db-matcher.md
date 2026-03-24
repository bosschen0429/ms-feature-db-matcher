# MS Feature DB Matcher Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone Tkinter desktop app that matches feature `mz` values from a user dataset against DNA and RNA database files, then exports a color-formatted Excel workbook into an auto-created `Output` folder.

**Architecture:** Create a new isolated Python project under `ms-feature-db-matcher` with separate modules for configuration, file loading, database profiles, matching logic, Excel export, and GUI orchestration. Keep all matching logic pure and testable, then let the GUI call those modules without embedding business rules directly in widget handlers.

**Tech Stack:** Python 3.11+, tkinter, pandas, openpyxl 3.1+, pytest

---

**Repo Root**

- `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher`

### Task 1: Scaffold the Independent Project

**Files:**
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/app.py`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/pyproject.toml`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/README.md`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/src/ms_feature_db_matcher/__init__.py`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/src/ms_feature_db_matcher/config.py`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/tests/test_smoke_project.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from ms_feature_db_matcher.config import ensure_output_dir, project_root


def test_project_root_and_output_dir_are_created() -> None:
    root = project_root()
    output = ensure_output_dir()

    assert root.name == "ms-feature-db-matcher"
    assert output.exists()
    assert output.name == "Output"
```

**Step 2: Run test to verify it fails**

Run from `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher`:

```bash
pytest tests/test_smoke_project.py -v
```

Expected: FAIL with `ModuleNotFoundError` because the project scaffold does not exist yet.

**Step 3: Write minimal implementation**

```python
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_output_dir() -> Path:
    output = project_root() / "Output"
    output.mkdir(parents=True, exist_ok=True)
    return output
```

Create `app.py` so the app can be launched:

```python
from ms_feature_db_matcher.gui import launch_app


if __name__ == "__main__":
    launch_app()
```

**Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_smoke_project.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" add .
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" commit -m "feat: scaffold feature db matcher project"
```

### Task 2: Implement Database Profiles and Input Loading

**Files:**
- Modify: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/src/ms_feature_db_matcher/config.py`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/src/ms_feature_db_matcher/profiles.py`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/src/ms_feature_db_matcher/io_utils.py`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/tests/test_profiles.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

import pandas as pd

from ms_feature_db_matcher.profiles import (
    DatabaseMode,
    load_database_table,
)


def test_load_default_dna_profile_reads_sheet1_header_row_2() -> None:
    path = Path(r"C:/Users/user/Desktop/NTU cancer/Database/datatables.xlsx")
    table = load_database_table(path, DatabaseMode.DNA, use_default_profile=True)

    assert "Short name" in table.columns
    assert "Charged monoisotopic mass" in table.columns


def test_detects_replacement_rna_sheet_by_required_columns(tmp_path) -> None:
    path = tmp_path / "rna.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"note": ["ignore"]}).to_excel(writer, sheet_name="Intro", index=False)
        pd.DataFrame(
            {
                "Short name": ["m1A"],
                "[M+H]+": [282.1202],
            }
        ).to_excel(writer, sheet_name="Usable", index=False)

    table = load_database_table(path, DatabaseMode.RNA, use_default_profile=False)

    assert list(table["Short name"]) == ["m1A"]
```

**Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_profiles.py -v
```

Expected: FAIL because profile and loader modules do not exist.

**Step 3: Write minimal implementation**

```python
from enum import Enum
from pathlib import Path

import pandas as pd


class DatabaseMode(str, Enum):
    DNA = "DNA"
    RNA = "RNA"


DEFAULT_DNA_PATH = Path(r"C:/Users/user/Desktop/NTU cancer/Database/datatables.xlsx")
DEFAULT_RNA_PATH = Path(r"C:/Users/user/Desktop/NTU cancer/Database/RNA modification for Lab.xlsx")


def load_database_table(path: Path, mode: DatabaseMode, use_default_profile: bool) -> pd.DataFrame:
    if use_default_profile and mode == DatabaseMode.DNA:
        return pd.read_excel(path, sheet_name="Sheet1", header=1)
    if use_default_profile and mode == DatabaseMode.RNA:
        return pd.read_excel(path, sheet_name="總表", header=1)

    required = {
        DatabaseMode.DNA: {"Short name", "Charged monoisotopic mass"},
        DatabaseMode.RNA: {"Short name", "[M+H]+"},
    }[mode]

    workbook = pd.ExcelFile(path)
    for sheet in workbook.sheet_names:
        for header in (0, 1):
            table = pd.read_excel(path, sheet_name=sheet, header=header)
            if required.issubset(set(table.columns)):
                return table
    raise ValueError(f"No worksheet contains required columns: {sorted(required)}")
```

**Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_profiles.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" add src/ms_feature_db_matcher/config.py src/ms_feature_db_matcher/profiles.py src/ms_feature_db_matcher/io_utils.py tests/test_profiles.py
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" commit -m "feat: add database profiles and loaders"
```

### Task 3: Implement Feature Parsing and PPM Matching Logic

**Files:**
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/src/ms_feature_db_matcher/matcher.py`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/tests/test_matcher.py`

**Step 1: Write the failing test**

```python
import pandas as pd

from ms_feature_db_matcher.matcher import (
    MatchMode,
    build_match_column,
    parse_feature_mz,
)


def test_parse_feature_mz_extracts_value_before_slash() -> None:
    assert parse_feature_mz("268.1052/17.59(Mz/RT)") == 268.1052


def test_build_match_column_handles_invalid_and_no_match() -> None:
    dataset = pd.DataFrame({"Feature": ["bad-value", "100.0/1.0"]})
    dna = pd.DataFrame({"Short name": ["dI"], "Charged monoisotopic mass": [200.0]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [300.0]})

    result = build_match_column(dataset, dna, rna, MatchMode.BOTH)

    assert result[0].text == "Invalid Feature"
    assert result[1].text == "No match"


def test_build_match_column_joins_multiple_hits_and_orders_both_mode() -> None:
    dataset = pd.DataFrame({"Feature": ["268.1052/17.59(Mz/RT)"]})
    dna = pd.DataFrame(
        {
            "Short name": ["dX", "dI"],
            "Charged monoisotopic mass": [268.1052, 268.1052],
        }
    )
    rna = pd.DataFrame(
        {
            "Short name": ["m1A", "m6A"],
            "[M+H]+": [268.1052, 268.1052],
        }
    )

    result = build_match_column(dataset, dna, rna, MatchMode.BOTH)

    assert result[0].text == "dX/dI/m1A/m6A"
    assert result[0].dna_names == ["dX", "dI"]
    assert result[0].rna_names == ["m1A", "m6A"]
```

**Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_matcher.py -v
```

Expected: FAIL because matching code does not exist yet.

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from enum import Enum


class MatchMode(str, Enum):
    DNA = "DNA"
    RNA = "RNA"
    BOTH = "Both"


@dataclass(frozen=True)
class MatchCell:
    text: str
    dna_names: list[str]
    rna_names: list[str]


def parse_feature_mz(feature: object) -> float:
    text = str(feature).strip()
    value = text.split("/", 1)[0]
    return float(value)


def ppm_difference(feature_mz: float, db_mz: float) -> float:
    return abs(feature_mz - db_mz) / db_mz * 1e6
```

Then implement `build_match_column()` so it:

- catches parse failures and emits `Invalid Feature`
- collects DNA hits from `Charged monoisotopic mass`
- collects RNA hits from `[M+H]+`
- uses `ppm <= 20`
- joins names with `/`
- preserves DNA-before-RNA order in `Both`

**Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_matcher.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" add src/ms_feature_db_matcher/matcher.py tests/test_matcher.py
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" commit -m "feat: add feature mz matching logic"
```

### Task 4: Export a New Excel Workbook with Colored Match Text

**Files:**
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/src/ms_feature_db_matcher/exporter.py`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/tests/test_exporter.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from ms_feature_db_matcher.exporter import export_results
from ms_feature_db_matcher.matcher import MatchCell


def test_export_results_writes_output_file_and_appends_column(tmp_path) -> None:
    source = tmp_path / "input.xlsx"
    pd.DataFrame({"Feature": ["268.1052/17.59(Mz/RT)"]}).to_excel(source, index=False)

    output = tmp_path / "Output"
    result_path = export_results(
        dataset=pd.read_excel(source),
        match_cells=[MatchCell(text="dX/m1A", dna_names=["dX"], rna_names=["m1A"])],
        source_path=source,
        output_dir=output,
        output_column_name="Matched Short name",
    )

    workbook = load_workbook(result_path)
    sheet = workbook.active

    assert result_path.parent == output
    assert sheet.cell(row=1, column=2).value == "Matched Short name"
    assert sheet.cell(row=2, column=2).value == "dX/m1A"
```

**Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_exporter.py -v
```

Expected: FAIL because exporter code does not exist yet.

**Step 3: Write minimal implementation**

```python
from pathlib import Path

import pandas as pd


def export_results(dataset, match_cells, source_path: Path, output_dir: Path, output_column_name: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    result = dataset.copy()
    result[output_column_name] = [cell.text for cell in match_cells]
    output_path = output_dir / f"{source_path.stem}_matched.xlsx"
    result.to_excel(output_path, index=False)
    return output_path
```

Then upgrade the implementation so it:

- avoids collisions with a timestamp suffix when needed
- applies rich text formatting with blue DNA and red RNA segments
- leaves `No match` and `Invalid Feature` as normal text

**Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_exporter.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" add src/ms_feature_db_matcher/exporter.py tests/test_exporter.py
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" commit -m "feat: add excel result exporter"
```

### Task 5: Build the Tkinter GUI Workflow

**Files:**
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/src/ms_feature_db_matcher/gui.py`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/tests/test_gui_smoke.py`
- Modify: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/app.py`

**Step 1: Write the failing test**

```python
from ms_feature_db_matcher.gui import AppState


def test_app_state_preloads_default_paths_and_output_dir() -> None:
    state = AppState.create()

    assert state.output_dir.exists()
    assert "datatables.xlsx" in str(state.dna_db_path)
    assert "RNA modification for Lab.xlsx" in str(state.rna_db_path)
```

**Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_gui_smoke.py -v
```

Expected: FAIL because GUI state and launch code do not exist.

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path

from .config import DEFAULT_DNA_PATH, DEFAULT_RNA_PATH, ensure_output_dir


@dataclass
class AppState:
    dataset_path: Path | None
    dna_db_path: Path
    rna_db_path: Path
    output_dir: Path

    @classmethod
    def create(cls) -> "AppState":
        return cls(
            dataset_path=None,
            dna_db_path=DEFAULT_DNA_PATH,
            rna_db_path=DEFAULT_RNA_PATH,
            output_dir=ensure_output_dir(),
        )
```

Then finish `gui.py` so it:

- renders file pickers for dataset, DNA DB, RNA DB
- renders mode buttons for `DNA`, `RNA`, `Both`
- runs the loader, matcher, and exporter
- displays success or failure messages
- opens the output folder through the platform shell

**Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_gui_smoke.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" add src/ms_feature_db_matcher/gui.py tests/test_gui_smoke.py app.py
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" commit -m "feat: add desktop gui workflow"
```

### Task 6: Add End-to-End Verification and User Documentation

**Files:**
- Modify: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/README.md`
- Create: `C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher/tests/test_end_to_end.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

import pandas as pd

from ms_feature_db_matcher.exporter import export_results
from ms_feature_db_matcher.matcher import MatchMode, build_match_column


def test_end_to_end_both_mode_creates_expected_output(tmp_path) -> None:
    dataset = pd.DataFrame({"Feature": ["268.1052/17.59(Mz/RT)", "bad"]})
    dna = pd.DataFrame({"Short name": ["dX"], "Charged monoisotopic mass": [268.1052]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [268.1052]})

    cells = build_match_column(dataset, dna, rna, MatchMode.BOTH)
    output_path = export_results(
        dataset=dataset,
        match_cells=cells,
        source_path=tmp_path / "sample.xlsx",
        output_dir=tmp_path / "Output",
        output_column_name="Matched Short name",
    )

    result = pd.read_excel(output_path)

    assert list(result["Matched Short name"]) == ["dX/m1A", "Invalid Feature"]
```

**Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_end_to_end.py -v
```

Expected: FAIL until matching and export modules are wired together correctly.

**Step 3: Write minimal implementation**

Update README with:

- purpose of the tool
- supported input formats
- mode behavior
- default databases
- output folder behavior
- how to run the app

Ensure module imports and function signatures support the end-to-end test
without GUI interaction.

**Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_end_to_end.py -v
pytest -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" add README.md tests/test_end_to_end.py
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" commit -m "docs: add usage guide and end-to-end verification"
```

### Task 7: Manual Verification Before Hand-Off

**Files:**
- No code changes required

**Step 1: Run the GUI manually**

Run:

```bash
python app.py
```

Expected:

- the window opens
- `Output/` exists
- default DNA and RNA paths are prefilled

**Step 2: Verify a real sample run**

Run one manual flow with:

- one dataset containing a `Feature` column
- `DNA` mode
- `RNA` mode
- `Both` mode

Expected:

- output file lands in `Output/`
- `Open Output Folder` works
- `No match` and `Invalid Feature` appear correctly
- DNA text is blue
- RNA text is red
- `Both` mode preserves DNA-first ordering

**Step 3: Final commit**

```bash
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" status --short
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" add .
git -C "C:/Users/user/Desktop/MS Data process package/ms-feature-db-matcher" commit -m "feat: complete ms feature db matcher v1"
```
