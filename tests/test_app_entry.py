import sys
import importlib.util
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
SPEC = importlib.util.spec_from_file_location("app_module", APP_PATH)
assert SPEC is not None and SPEC.loader is not None
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


def test_bootstrap_src_path_adds_project_src_when_missing(monkeypatch) -> None:
    src_dir = APP_PATH.parent / "src"
    other_paths = [entry for entry in sys.path if Path(entry).resolve() != src_dir.resolve()]
    monkeypatch.setattr(sys, "path", other_paths)

    app.bootstrap_src_path()

    assert sys.path[0] == str(src_dir)
