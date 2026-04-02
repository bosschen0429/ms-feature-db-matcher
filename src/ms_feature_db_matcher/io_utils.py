from pathlib import Path

import pandas as pd

from .column_rules import DATASET_FEATURE_COLUMNS, has_any_column

DEFAULT_DATASET_SHEET_NAME = "Dataset"


def read_table(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_excel(path, **kwargs)


def _validate_dataset_tables(
    tables: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    matching_tables = {
        sheet_name: table
        for sheet_name, table in tables.items()
        if has_any_column(table.columns, DATASET_FEATURE_COLUMNS)
    }
    if not matching_tables:
        # 保留原始欄位順序，讓有問題的欄位（通常在前幾欄）能直接顯示
        seen: set[str] = set()
        all_columns: list[str] = []
        for table in tables.values():
            for col in table.columns:
                if col not in seen:
                    seen.add(col)
                    all_columns.append(col)
        found_str = ", ".join(repr(c) for c in all_columns[:10])
        if len(all_columns) > 10:
            found_str += f" ... (共 {len(all_columns)} 欄)"
        raise ValueError(
            "Dataset 缺少可辨識的 m/z 欄位。\n"
            "  支援的欄位名稱：Feature, Mz, Mz/RT, m/z, Precursor Ion m/z, Charged monoisotopic mass 等\n"
            f"  Dataset 中實際找到的欄位：{found_str}\n"
            "  常見原因：欄位名稱使用逗號（如 'm/z,RT'）而非斜線（'Mz/RT'）、"
            "或第一列為說明列而非標題列。"
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
