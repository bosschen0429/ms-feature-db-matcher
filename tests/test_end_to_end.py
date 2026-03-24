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
        formula_column_name="Matched Formula",
        name_column_name="Matched Short name",
    )

    result = pd.read_excel(output_path)

    assert list(result["Matched Short name"]) == ["dX/m1A", "Invalid Feature"]


def test_end_to_end_with_formula_output(tmp_path) -> None:
    dataset = pd.DataFrame({"Feature": ["268.1052/17.59(Mz/RT)"]})
    dna = pd.DataFrame({
        "Short name": ["dX"],
        "Charged monoisotopic mass": [268.1052],
        "Formula": ["C10H13N4O4"],
    })
    rna = pd.DataFrame({
        "Short name": ["m1A"],
        "[M+H]+": [268.1052],
        "Formula": ["C11H16N5O3"],
    })

    cells = build_match_column(dataset, dna, rna, MatchMode.BOTH)
    output_path = export_results(
        dataset=dataset,
        match_cells=cells,
        source_path=tmp_path / "sample.xlsx",
        output_dir=tmp_path / "Output",
        formula_column_name="Matched Formula",
        name_column_name="Matched Short name",
    )

    result = pd.read_excel(output_path)

    assert list(result.columns) == ["Feature", "Matched Formula", "Matched Short name"]
    assert list(result["Matched Short name"]) == ["dX/m1A"]
    assert list(result["Matched Formula"]) == ["C10H13N4O4/C11H16N5O3"]
