from pathlib import Path

import pandas as pd

from ms_feature_db_matcher.config import DEFAULT_DNA_PATH
from ms_feature_db_matcher.gui import (
    AppState,
    describe_mode,
    path_badge_text,
    run_matching,
    status_appearance,
)
from ms_feature_db_matcher.matcher import MatchMode


def test_app_state_preloads_default_paths_and_output_dir() -> None:
    state = AppState.create()

    assert state.output_dir.exists()
    assert "datatables.xlsx" in str(state.dna_db_path)
    assert "natural_modifications.xlsx" in str(state.rna_db_path)


def test_describe_mode_explains_both_ordering() -> None:
    summary = describe_mode(MatchMode.BOTH)

    assert "DNA" in summary
    assert "RNA" in summary
    assert "DNA first" in summary


def test_path_badge_text_distinguishes_default_and_custom() -> None:
    assert path_badge_text(DEFAULT_DNA_PATH, DEFAULT_DNA_PATH) == "Default"
    assert path_badge_text(Path("custom.xlsx"), DEFAULT_DNA_PATH) == "Custom"


def test_status_appearance_uses_semantic_states() -> None:
    ready = status_appearance("Output folder: C:/demo/Output")
    success = status_appearance("Saved result to: C:/demo/Output/file.xlsx")
    error = status_appearance("Failed: bad dataset")

    assert ready["tone"] == "ready"
    assert success["tone"] == "success"
    assert error["tone"] == "error"


def test_run_matching_in_dna_mode_does_not_require_rna_database(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.csv"
    dna_path = tmp_path / "dna.xlsx"

    pd.DataFrame({"Feature": ["268.1052/17.59(Mz/RT)"]}).to_csv(dataset_path, index=False)
    pd.DataFrame(
        {
            "Short name": ["dX"],
            "Charged monoisotopic mass": [268.1052],
        }
    ).to_excel(dna_path, index=False)

    state = AppState(
        dataset_path=dataset_path,
        dna_db_path=dna_path,
        rna_db_path=tmp_path / "missing-rna.xlsx",
        output_dir=tmp_path / "Output",
    )

    output_path = run_matching(state, MatchMode.DNA)
    result = pd.read_excel(output_path)

    assert list(result["Matched Short name"]) == ["dX"]


def test_run_matching_in_dna_mode_accepts_mz_database_column(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.xlsx"
    dna_path = tmp_path / "dna.xlsx"

    pd.DataFrame({"Feature": ["268.1052/17.59(Mz/RT)"]}).to_excel(dataset_path, index=False)
    pd.DataFrame({"Short name": ["dX"], "Mz": [268.1052]}).to_excel(dna_path, index=False)

    state = AppState(
        dataset_path=dataset_path,
        dna_db_path=dna_path,
        rna_db_path=tmp_path / "missing-rna.xlsx",
        output_dir=tmp_path / "Output",
    )

    output_path = run_matching(state, MatchMode.DNA)
    result = pd.read_excel(output_path)

    assert list(result["Matched Short name"]) == ["dX"]


def test_run_matching_accepts_charged_monoisotopic_mass_in_dataset(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.xlsx"
    dna_path = tmp_path / "dna.xlsx"

    pd.DataFrame({"Charged monoisotopic mass": ["268.1052"]}).to_excel(dataset_path, index=False)
    pd.DataFrame({"Short name": ["dX"], "Mz/RT": ["268.1052/9.41"]}).to_excel(dna_path, index=False)

    state = AppState(
        dataset_path=dataset_path,
        dna_db_path=dna_path,
        rna_db_path=tmp_path / "missing-rna.xlsx",
        output_dir=tmp_path / "Output",
    )

    output_path = run_matching(state, MatchMode.DNA)
    result = pd.read_excel(output_path)

    assert list(result["Matched Short name"]) == ["dX"]


def test_run_matching_exports_all_feature_sheets_from_excel_workbook(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.xlsx"
    dna_path = tmp_path / "dna.xlsx"

    with pd.ExcelWriter(dataset_path) as writer:
        pd.DataFrame({"Feature": ["268.1052/17.59"]}).to_excel(writer, sheet_name="Summary", index=False)
        pd.DataFrame({"Feature": ["300.0/4.2"]}).to_excel(writer, sheet_name="VIP", index=False)
        pd.DataFrame({"Note": ["skip"]}).to_excel(writer, sheet_name="Metadata", index=False)

    pd.DataFrame(
        {
            "Short name": ["dX", "dY"],
            "Mz": [268.1052, 300.0],
        }
    ).to_excel(dna_path, index=False)

    state = AppState(
        dataset_path=dataset_path,
        dna_db_path=dna_path,
        rna_db_path=tmp_path / "missing-rna.xlsx",
        output_dir=tmp_path / "Output",
    )

    output_path = run_matching(state, MatchMode.DNA)
    summary = pd.read_excel(output_path, sheet_name="Summary")
    vip = pd.read_excel(output_path, sheet_name="VIP")
    sheets = pd.ExcelFile(output_path).sheet_names

    assert sheets == ["Summary", "VIP"]
    assert list(summary["Matched Short name"]) == ["dX"]
    assert list(vip["Matched Short name"]) == ["dY"]


def test_run_matching_outputs_formula_column(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.csv"
    dna_path = tmp_path / "dna.xlsx"

    pd.DataFrame({"Feature": ["268.1052/17.59"]}).to_csv(dataset_path, index=False)
    pd.DataFrame({
        "Short name": ["dX"],
        "Charged monoisotopic mass": [268.1052],
        "Formula": ["C10H13N4O4"],
    }).to_excel(dna_path, index=False)

    state = AppState(
        dataset_path=dataset_path,
        dna_db_path=dna_path,
        rna_db_path=tmp_path / "missing-rna.xlsx",
        output_dir=tmp_path / "Output",
    )

    output_path = run_matching(state, MatchMode.DNA)
    result = pd.read_excel(output_path)

    assert "Matched Formula" in result.columns
    assert "Matched Short name" in result.columns
    assert list(result["Matched Formula"]) == ["C10H13N4O4"]
    assert list(result["Matched Short name"]) == ["dX"]
