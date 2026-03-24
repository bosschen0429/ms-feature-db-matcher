# MS Feature DB Matcher

Standalone desktop app for matching mass spectrometry features against DNA / RNA databases with a 20 ppm tolerance rule. Outputs an Excel workbook with matched Formula and Short name columns.

## Download

Pre-built binaries for Windows (.exe) and macOS (.app) are available on the [Releases](https://github.com/bosschen0429/ms-feature-db-matcher/releases) page.

### macOS Note

The app is not code-signed. On first launch, right-click the app and choose **Open**, then confirm in the dialog. Alternatively, go to **System Settings > Privacy & Security** and allow the app.

## Accepted Dataset Columns

The dataset file must contain at least one of the following columns (case-insensitive):

| Column Name | Example Value |
|---|---|
| Feature | `268.1052/17.59(Mz/RT)` |
| Mz | `268.1052` |
| m/z | `268.1052` |
| Mz/RT | `268.1052/17.59` |
| Precursor Ion m/z | `268.1052` |
| Charged monoisotopic mass | `268.1052` |

**Parsing rule**: if a value contains `/`, only the text before the first `/` is used as m/z.

## Accepted Database Mass Columns

When matching, the app looks for mass values in these database columns:

| Column Name | Mode |
|---|---|
| Mz | DNA & RNA |
| m/z | DNA & RNA |
| Mz/RT | DNA & RNA |
| Precursor Ion m/z | DNA & RNA |
| Charged monoisotopic mass | DNA & RNA |
| [M+H]+ Protonated Mass | DNA & RNA |
| [M+H]+ | RNA only |

The database must also contain a **Short name** (or **Compound**) column. A **Formula** (or **Molecular Formula**) column is optional — if present, matched formulas are included in the output.

## Matching Modes

| Mode | Behavior |
|---|---|
| DNA | Compare dataset m/z against DNA database masses |
| RNA | Compare dataset m/z against RNA database masses (includes [M+H]+) |
| Both | Run DNA first, then RNA; results are merged with DNA before RNA |

## Matching Rule

```
abs(feature_mz - db_mz) / db_mz * 1e6 <= 20
```

## Output

- Two columns are appended to the original dataset: **Matched Formula** then **Matched Short name**
- DNA matches are colored **blue**, RNA matches are colored **red**
- Multiple matches are joined with `/`
- `No match` when nothing matches, `Invalid Feature` when the value cannot be parsed
- Results are saved to an `Output/` folder next to the application
- If the filename already exists, a timestamp suffix is appended

## Default Databases

Bundled in the `database/` folder:

| File | Mode |
|---|---|
| `datatables.xlsx` | DNA |
| `natural_modifications.xlsx` | RNA |

You can replace either database from the GUI.

## Supported Dataset Formats

`.csv`, `.tsv`, `.xlsx`, `.xls`

For Excel files with multiple sheets, every sheet containing a supported m/z column is matched and exported.

## Development

```bash
pip install -e .
python app.py
```

Run tests:

```bash
pip install pytest
pytest -v
```

## Build from Source

```bash
pip install .[build]
pyinstaller ms_feature_db_matcher.spec
```

Output binary appears in `dist/`.
