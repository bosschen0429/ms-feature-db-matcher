# MS Feature DB Matcher

Standalone Tkinter desktop app for matching dataset `Feature` values against DNA and RNA databases, then exporting a new Excel workbook into the project's `Output/` folder.

## What It Does

- Imports one dataset file and up to two database files
- Supports `DNA`, `RNA`, and `Both` matching modes
- Extracts the `mz` value from the `Feature` column by taking the text before the first `/`
- Matches with a `20 ppm` tolerance
- Writes a new Excel file with:
  - `No match` when nothing matches
  - `Invalid Feature` when the source value cannot be parsed
  - blue DNA short names
  - red RNA short names
  - DNA-before-RNA ordering in `Both` mode

## Supported Dataset Formats

- `.csv`
- `.tsv`
- `.xlsx`
- `.xls`

The dataset must contain a `Feature` column.

## Default Databases

- DNA:
  `C:/Users/user/Desktop/NTU cancer/Database/datatables.xlsx`
- RNA:
  `C:/Users/user/Desktop/NTU cancer/Database/RNA modification for Lab.xlsx`

You can replace either database file from the GUI.

## Matching Rules

- Dataset `Feature` example:
  `268.1052/17.59(Mz/RT)`
- Parsed feature `mz`:
  `268.1052`
- DNA compares against `Charged monoisotopic mass`
- RNA compares against `[M+H]+`
- Formula:
  `abs(feature_mz - db_mz) / db_mz * 1e6 <= 20`

## Output Behavior

- The app auto-creates `Output/` under the project root
- Results are written as `<input_stem>_matched.xlsx`
- If the filename already exists, a timestamp suffix is appended
- The GUI includes an `Open Output Folder` button

## Run the App

Install dependencies in your Python environment:

```bash
pip install -e .
```

Launch the desktop app:

```bash
python app.py
```

Run the test suite:

```bash
pytest -v
```
