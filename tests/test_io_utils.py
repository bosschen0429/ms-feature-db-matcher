import pandas as pd

from ms_feature_db_matcher.io_utils import read_dataset_sheets


def test_read_dataset_sheets_returns_all_feature_sheets_from_excel(tmp_path) -> None:
    path = tmp_path / "dataset.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"Feature": ["268.1052/17.59"]}).to_excel(writer, sheet_name="Summary", index=False)
        pd.DataFrame({"Mz": [268.1052]}).to_excel(writer, sheet_name="VIP", index=False)
        pd.DataFrame({"Note": ["skip"]}).to_excel(writer, sheet_name="Metadata", index=False)

    tables = read_dataset_sheets(path)

    assert list(tables) == ["Summary", "VIP"]


def test_read_dataset_sheets_wraps_csv_as_single_dataset_sheet(tmp_path) -> None:
    path = tmp_path / "dataset.csv"
    pd.DataFrame({"Feature": ["268.1052/17.59"]}).to_csv(path, index=False)

    tables = read_dataset_sheets(path)

    assert list(tables) == ["Dataset"]
