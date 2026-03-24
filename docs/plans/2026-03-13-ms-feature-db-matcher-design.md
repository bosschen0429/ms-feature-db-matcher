# MS Feature DB Matcher Design

> Date: 2026-03-13

## Overview

Build a fully independent desktop tool for matching LC/MS feature rows
against DNA and RNA modification databases. The tool will use a minimal
Tkinter GUI, accept user dataset files in `csv`, `tsv`, `xlsx`, or `xls`
format, and write a new Excel result file into an auto-created `Output`
folder.

The matching key is the `mz` portion of the user dataset `Feature`
column. A typical value looks like `268.1052/17.59(Mz/RT)`, where the
string before `/` is the feature `mz`. That value is compared against a
database mass column using an absolute `20 ppm` tolerance.

This project must not modify or import runtime code from
`Pairs/`. That project may be used only as a structural reference for
GUI organization and desktop-tool ergonomics.

## Scope

### In Scope

- A standalone Tkinter desktop app
- One user dataset input
- Two database inputs:
  - DNA database
  - RNA database
- Mode selector:
  - `DNA`
  - `RNA`
  - `Both`
- Automatic output folder creation
- Excel result export
- Colored result text in Excel:
  - DNA matches in blue
  - RNA matches in red

### Out of Scope

- Editing the `Pairs` project
- RT-based filtering
- User-editable ppm tolerance in v1
- In-GUI table preview
- Packaging into `.exe` in this planning phase

## Default Database Profiles

The GUI should preload two default database files while still allowing
users to replace them.

### DNA Default Profile

- File:
  `C:/Users/user/Desktop/NTU cancer/Database/datatables.xlsx`
- Sheet: `Sheet1`
- Header row: row 2 in Excel, which means `header=1` in pandas
- Match mass column: `Charged monoisotopic mass`
- Label column: `Short name`

### RNA Default Profile

- File:
  `C:/Users/user/Desktop/NTU cancer/Database/RNA modification for Lab.xlsx`
- Sheet: `總表`
- Header row: row 2 in Excel, which means `header=1` in pandas
- Match mass column: `[M+H]+`
- Label column: `Short name`

### Replacement Database Behavior

If the user replaces a database file, the app should not assume the
first worksheet is valid. Instead, it should scan worksheets and detect
the first sheet containing the required pair of columns for the selected
mode:

- DNA:
  - `Charged monoisotopic mass`
  - `Short name`
- RNA:
  - `[M+H]+`
  - `Short name`

If no valid sheet is found, the GUI should show a targeted validation
error and stop the run.

## Matching Rules

### Dataset Parsing

- Read the user dataset from:
  - `csv`
  - `tsv`
  - `xlsx`
  - `xls`
- For Excel input, use the first worksheet
- Require a `Feature` column
- Parse the feature mass from the substring before the first `/`

Examples:

- `268.1052/17.59(Mz/RT)` -> `268.1052`
- `300.1234/5.01` -> `300.1234`

If parsing fails for a row, the output cell for that row must be
`Invalid Feature`.

### PPM Formula

Use:

```text
ppm = abs(feature_mz - db_mz) / db_mz * 1e6
```

A row is considered matched when:

```text
ppm <= 20
```

### Mode Semantics

#### DNA Mode

- Compare feature `mz` to DNA `Charged monoisotopic mass`
- Collect matching DNA `Short name` values

#### RNA Mode

- Compare feature `mz` to RNA `[M+H]+`
- Collect matching RNA `Short name` values

#### Both Mode

- Run DNA matching first
- Run RNA matching second
- Combine the matched names into one output cell
- Preserve order:
  - DNA names first
  - RNA names second

## Result Construction

The result workbook uses the user dataset as the base table and appends
one new column at the end.

Recommended output column name:

```text
Matched Short name
```

Cell rules:

- Valid feature with no matches -> `No match`
- Invalid feature string -> `Invalid Feature`
- One match -> `Short name`
- Multiple matches in same mode -> join with `/`
- Both mode with DNA and RNA matches -> DNA segment first, RNA segment
  second, separated by `/`

## Excel Styling

The result workbook must use rich text for mixed-color matches in a
single cell.

### Color Rules

- DNA `Short name` text: blue
- RNA `Short name` text: red
- `No match`: default text color
- `Invalid Feature`: default text color

### Both Mode Rich Text

When both DNA and RNA matches exist, the cell should be written as rich
text with segmented coloring.

Example:

```text
dI/dX/m1A/m1G
```

Where:

- `dI/dX` is blue
- `m1A/m1G` is red

If only one side matches in `Both` mode, only that segment should be
present and colored accordingly.

## GUI Design

The GUI should stay intentionally small and task-focused.

### Required Controls

- Dataset file picker
- DNA database file picker
- RNA database file picker
- Mode selector:
  - radio buttons or segmented buttons for `DNA`, `RNA`, `Both`
- `Run Matching` button
- `Open Output Folder` button
- Status label or small log area

### Output Folder Behavior

The app should create an `Output` folder under the new project root on
startup if it does not already exist.

Recommended location:

```text
ms-feature-db-matcher/Output/
```

All generated workbooks should be written there automatically.

Recommended naming pattern:

```text
<input_stem>_matched.xlsx
```

If a filename collision occurs, append a timestamp suffix.

## Architecture

Recommended project structure:

```text
ms-feature-db-matcher/
  app.py
  pyproject.toml
  README.md
  Output/
  docs/
    plans/
      2026-03-13-ms-feature-db-matcher-design.md
      2026-03-13-ms-feature-db-matcher.md
  src/
    ms_feature_db_matcher/
      __init__.py
      config.py
      profiles.py
      io_utils.py
      matcher.py
      exporter.py
      gui.py
  tests/
    test_profiles.py
    test_matcher.py
    test_exporter.py
    test_gui_smoke.py
```

### Module Responsibilities

#### `config.py`

- Project root helpers
- Default database paths
- Output folder path
- Styling constants

#### `profiles.py`

- DNA and RNA database profile definitions
- Sheet and header rules for defaults
- Detection logic for replacement database files

#### `io_utils.py`

- Read `csv`, `tsv`, `xlsx`, `xls`
- Excel first-sheet loading for the user dataset
- General validation helpers

#### `matcher.py`

- `Feature` parsing
- ppm calculation
- DNA/RNA/both matching
- Match result normalization

#### `exporter.py`

- Create output workbook
- Append result column
- Apply rich text color formatting

#### `gui.py`

- Build Tkinter layout
- File picker actions
- Mode switching
- Run workflow
- Open output folder action
- User-facing error messages

## Data Flow

1. App starts
2. App creates `Output/` if needed
3. GUI preloads the DNA and RNA default database paths
4. User selects the dataset and mode
5. User optionally replaces one or both database files
6. App loads the dataset and validates `Feature`
7. App loads the active database files using the correct profile rules
8. App parses feature masses
9. App runs DNA, RNA, or both matching
10. App builds the appended result column
11. App writes a new workbook into `Output/`
12. GUI reports success and allows the user to open the output folder

## Error Handling

### Dataset Errors

- Missing dataset file path -> block run with a GUI warning
- Unsupported file type -> block run with a GUI warning
- Missing `Feature` column -> block run with a GUI warning

### Database Errors

- Default database file missing -> show a clear path-specific error
- Replacement file missing required sheet/columns -> show which columns
  were expected
- Non-numeric database mass values -> ignore invalid rows during
  matching, but do not crash the whole run

### Row-Level Errors

- Bad `Feature` value -> mark row as `Invalid Feature`
- Valid feature with no matches -> mark row as `No match`

### Export Errors

- Locked workbook or permission issue -> show the destination path and
  failure reason

## Testing

### Unit Tests

- `Feature` parsing success and failure cases
- ppm boundary behavior at exactly `20 ppm`
- DNA-only matching
- RNA-only matching
- Both mode ordering
- Multi-match joining with `/`
- Default profile loading
- Replacement database sheet detection

### Export Tests

- Result workbook is created in `Output/`
- Output column is appended at the end
- `No match` and `Invalid Feature` text are written correctly
- DNA-only rich text uses blue
- RNA-only rich text uses red
- Both-mode mixed rich text preserves segment order and colors

### GUI Smoke Test

- Window construction
- Default paths are populated
- Output folder is created on startup

## Recommendation

Implement the project as a small, modular desktop app rather than a
single large script. That keeps the business rules testable, makes the
Excel rich-text behavior easier to isolate, and preserves the boundary
that this tool is fully independent from `Pairs/`.
