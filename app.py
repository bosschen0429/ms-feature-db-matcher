import sys
from pathlib import Path

sys.pycache_prefix = str(Path(__file__).resolve().parent / ".tmp" / "pycache")


def bootstrap_src_path() -> None:
    src_dir = Path(__file__).resolve().parent / "src"
    src_text = str(src_dir)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)


def main() -> None:
    bootstrap_src_path()
    from ms_feature_db_matcher.gui import launch_app

    launch_app()


if __name__ == "__main__":
    main()
