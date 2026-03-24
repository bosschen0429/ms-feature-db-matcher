from pathlib import Path

from ms_feature_db_matcher.config import ensure_output_dir, project_root


def test_project_root_and_output_dir_are_created() -> None:
    root = project_root()
    output = ensure_output_dir()

    assert root.name == "ms-feature-db-matcher"
    assert output.exists()
    assert output.name == "Output"
