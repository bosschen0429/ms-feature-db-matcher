import sys
from pathlib import Path


def _base_path() -> Path:
    """Return the project root in dev, or the temp extraction dir under PyInstaller."""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def database_dir() -> Path:
    return _base_path() / "database"


DEFAULT_DNA_PATH = database_dir() / "datatables.xlsx"
DEFAULT_RNA_PATH = database_dir() / "natural_modifications.xlsx"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_output_dir() -> Path:
    output = project_root() / "Output"
    output.mkdir(parents=True, exist_ok=True)
    return output
