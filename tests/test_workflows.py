from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_workflow(name: str) -> str:
    return (REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def test_ci_workflow_delegates_to_shared_python_ci() -> None:
    workflow = read_workflow("ci.yml")

    assert "Chao-hu-Lab/shared-workflows/.github/workflows/python-ci.yml@main" in workflow
    assert 'python-versions: \'["3.11", "3.12"]\'' in workflow


def test_build_workflow_delegates_to_shared_python_build() -> None:
    workflow = read_workflow("build.yml")

    assert "Chao-hu-Lab/shared-workflows/.github/workflows/python-build.yml@main" in workflow
    assert 'spec-file: "ms_feature_db_matcher.spec"' in workflow
    assert 'executable-name: "MS Feature DB Matcher"' in workflow
