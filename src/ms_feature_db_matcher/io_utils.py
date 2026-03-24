from pathlib import Path

import pandas as pd

from .column_rules import DATASET_FEATURE_COLUMNS, has_any_column

DEFAULT_DATASET_SHEET_NAME = "Dataset"


def read_table(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_excel(path, **kwargs)


def _validate_dataset_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    matching_tables = {
        sheet_name: table for sheet_name, table in tables.items() if has_any_column(table.columns, DATASET_FEATURE_COLUMNS)
    }
    if not matching_tables:
        raise ValueError(
            "Dataset must contain a supported m/z column "
            "(Feature, Mz, Mz/RT, m/z, Precursor Ion m/z, Charged monoisotopic mass, etc.)."
        )
    return matching_tables


def read_dataset_sheets(path: Path) -> dict[str, pd.DataFrame]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        tables = {DEFAULT_DATASET_SHEET_NAME: pd.read_csv(path)}
    elif suffix == ".tsv":
        tables = {DEFAULT_DATASET_SHEET_NAME: pd.read_csv(path, sep="\t")}
    elif suffix in {".xlsx", ".xls"}:
        tables = pd.read_excel(path, sheet_name=None)
    else:
        raise ValueError(f"Unsupported dataset file type: {path.suffix}")

    return _validate_dataset_tables(tables)


def read_dataset(path: Path) -> pd.DataFrame:
    return next(iter(read_dataset_sheets(path).values()))
