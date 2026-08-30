from pathlib import Path

import cge_core

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9-3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_source_version_matches_project_metadata():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert cge_core.__version__ == project["project"]["version"]


def test_v080_source_version():
    assert cge_core.__version__ == "0.8.0"
