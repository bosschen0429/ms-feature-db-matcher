from dataclasses import dataclass, field
from enum import Enum

import pandas as pd

from .column_rules import (
    DATASET_FEATURE_COLUMNS,
    FORMULA_COLUMNS,
    NAME_COLUMNS,
    RNA_EXTRA_MASS_COLUMNS,
    UNIVERSAL_MASS_COLUMNS,
    find_column,
)


class MatchMode(str, Enum):
    DNA = "DNA"
    RNA = "RNA"
    BOTH = "Both"


@dataclass(frozen=True)
class MatchCell:
    text: str
    formula_text: str
    dna_names: list[str] = field(default_factory=list)
    rna_names: list[str] = field(default_factory=list)
    dna_formulas: list[str] = field(default_factory=list)
    rna_formulas: list[str] = field(default_factory=list)

def parse_mz_value(value: object) -> float:
    text = str(value).strip()
    if not text:
        raise ValueError("Missing m/z value")
    value = text.split("/", 1)[0].strip()
    return float(value)


def parse_feature_mz(feature: object) -> float:
    return parse_mz_value(feature)


def ppm_difference(feature_mz: float, db_mz: float) -> float:
    return abs(feature_mz - db_mz) / db_mz * 1e6


def _collect_hits(
    table: pd.DataFrame, mass_candidates: set[str], feature_mz: float,
) -> tuple[list[str], list[str]]:
    name_col = find_column(table.columns, NAME_COLUMNS)
    mass_col = find_column(table.columns, mass_candidates)
    if name_col is None or mass_col is None:
        return [], []
    formula_col = find_column(table.columns, FORMULA_COLUMNS)
    names: list[str] = []
    formulas: list[str] = []
    for _, row in table.iterrows():
        try:
            if ppm_difference(feature_mz, parse_mz_value(row[mass_col])) <= 20:
                names.append(str(row[name_col]))
                if formula_col is not None:
                    f = str(row[formula_col]).strip()
                    formulas.append(f if f and f.lower() != "nan" else "")
                else:
                    formulas.append("")
        except (TypeError, ValueError, ZeroDivisionError):
            continue
    return names, formulas


def build_match_column(
    dataset: pd.DataFrame,
    dna: pd.DataFrame,
    rna: pd.DataFrame,
    mode: MatchMode,
) -> list[MatchCell]:
    feature_col = find_column(dataset.columns, DATASET_FEATURE_COLUMNS)
    if feature_col is None:
        raise ValueError(
            "Dataset must contain a supported m/z column "
            "(Feature, Mz, Mz/RT, m/z, Precursor Ion m/z, Charged monoisotopic mass, etc.)."
        )
    results: list[MatchCell] = []
    for feature in dataset[feature_col]:
        try:
            feature_mz = parse_feature_mz(feature)
        except (TypeError, ValueError):
            results.append(MatchCell(text="Invalid Feature", formula_text=""))
            continue

        dna_names: list[str] = []
        rna_names: list[str] = []
        dna_formulas: list[str] = []
        rna_formulas: list[str] = []
        if mode in (MatchMode.DNA, MatchMode.BOTH):
            dna_names, dna_formulas = _collect_hits(dna, UNIVERSAL_MASS_COLUMNS, feature_mz)
        if mode in (MatchMode.RNA, MatchMode.BOTH):
            rna_names, rna_formulas = _collect_hits(rna, UNIVERSAL_MASS_COLUMNS | RNA_EXTRA_MASS_COLUMNS, feature_mz)

        all_names = dna_names + rna_names
        all_formulas = dna_formulas + rna_formulas
        text = "/".join(all_names) if all_names else "No match"
        non_empty = [f for f in all_formulas if f]
        formula_text = "/".join(non_empty) if non_empty else ""
        results.append(MatchCell(
            text=text,
            formula_text=formula_text,
            dna_names=dna_names,
            rna_names=rna_names,
            dna_formulas=dna_formulas,
            rna_formulas=rna_formulas,
        ))

    return results
