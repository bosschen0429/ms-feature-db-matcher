import sys
import shutil
import uuid
from pathlib import Path

import pytest

TMP_ROOT = Path(__file__).resolve().parents[1] / ".tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)
sys.pycache_prefix = str(TMP_ROOT / "pycache")


@pytest.fixture
def tmp_path() -> Path:
    root = TMP_ROOT / "test_artifacts"
    path = root / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
