import pandas as pd

from ms_feature_db_matcher.matcher import MatchMode, build_match_column, parse_feature_mz


def test_parse_feature_mz_extracts_value_before_slash() -> None:
    assert parse_feature_mz("268.1052/17.59(Mz/RT)") == 268.1052


def test_build_match_column_handles_invalid_and_no_match() -> None:
    dataset = pd.DataFrame({"Feature": ["bad-value", "100.0/1.0"]})
    dna = pd.DataFrame({"Short name": ["dI"], "Charged monoisotopic mass": [200.0]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [300.0]})

    result = build_match_column(dataset, dna, rna, MatchMode.BOTH)

    assert result[0].text == "Invalid Feature"
    assert result[0].formula_text == ""
    assert result[1].text == "No match"
    assert result[1].formula_text == ""


def test_build_match_column_uses_mz_rt_column_when_feature_absent() -> None:
    dataset = pd.DataFrame({"Mz/RT": ["268.1052/17.59"]})
    dna = pd.DataFrame({"Short name": ["dX"], "Charged monoisotopic mass": [268.1052]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [300.0]})

    result = build_match_column(dataset, dna, rna, MatchMode.DNA)

    assert result[0].text == "dX"


def test_build_match_column_accepts_mz_database_column_in_dna_mode() -> None:
    dataset = pd.DataFrame({"Feature": ["268.1052/17.59(Mz/RT)"]})
    dna = pd.DataFrame({"Short name": ["dX"], "Mz": [268.1052]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [300.0]})

    result = build_match_column(dataset, dna, rna, MatchMode.DNA)

    assert result[0].text == "dX"


def test_build_match_column_parses_mz_rt_values_in_database() -> None:
    dataset = pd.DataFrame({"Charged monoisotopic mass": ["268.1052"]})
    dna = pd.DataFrame({"Short name": ["dX"], "Mz/RT": ["268.1052/9.41"]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [300.0]})

    result = build_match_column(dataset, dna, rna, MatchMode.DNA)

    assert result[0].text == "dX"


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


def test_build_match_column_accepts_precursor_ion_mz_dataset_column() -> None:
    dataset = pd.DataFrame({"Precursor Ion m/z": ["268.1052"]})
    dna = pd.DataFrame({"Short name": ["dX"], "Charged monoisotopic mass": [268.1052]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [300.0]})

    result = build_match_column(dataset, dna, rna, MatchMode.DNA)

    assert result[0].text == "dX"


def test_build_match_column_accepts_mz_slash_dataset_column() -> None:
    dataset = pd.DataFrame({"m/z": [268.1052]})
    dna = pd.DataFrame({"Short name": ["dX"], "Charged monoisotopic mass": [268.1052]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [300.0]})

    result = build_match_column(dataset, dna, rna, MatchMode.DNA)

    assert result[0].text == "dX"


def test_build_match_column_accepts_protonated_mass_db_column() -> None:
    dataset = pd.DataFrame({"Feature": ["268.1052/17.59"]})
    dna = pd.DataFrame({"Short name": ["dX"], "[M+H]+ Protonated Mass": [268.1052]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [300.0]})

    result = build_match_column(dataset, dna, rna, MatchMode.DNA)

    assert result[0].text == "dX"


def test_build_match_column_collects_formula_separately() -> None:
    dataset = pd.DataFrame({"Feature": ["268.1052/17.59"]})
    dna = pd.DataFrame({
        "Short name": ["dX", "dI"],
        "Charged monoisotopic mass": [268.1052, 268.1052],
        "Formula": ["C10H13N4O4", "C10H13N4O4"],
    })
    rna = pd.DataFrame({
        "Short name": ["m1A"],
        "[M+H]+": [268.1052],
        "Formula": ["C11H16N5O3"],
    })

    result = build_match_column(dataset, dna, rna, MatchMode.BOTH)

    assert result[0].text == "dX/dI/m1A"
    assert result[0].formula_text == "C10H13N4O4/C10H13N4O4/C11H16N5O3"
    assert result[0].dna_formulas == ["C10H13N4O4", "C10H13N4O4"]
    assert result[0].rna_formulas == ["C11H16N5O3"]


def test_build_match_column_formula_empty_when_db_has_no_formula_col() -> None:
    dataset = pd.DataFrame({"Feature": ["268.1052/17.59"]})
    dna = pd.DataFrame({"Short name": ["dX"], "Charged monoisotopic mass": [268.1052]})
    rna = pd.DataFrame({"Short name": ["m1A"], "[M+H]+": [300.0]})

    result = build_match_column(dataset, dna, rna, MatchMode.DNA)

    assert result[0].text == "dX"
    assert result[0].formula_text == ""
