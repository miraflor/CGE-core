from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_metadata_is_v070():
    assert 'version = "0.7.0"' in read("pyproject.toml")
    assert re.search(r"(?m)^version:\s*[\"']?0\.7\.0[\"']?\s*$", read("CITATION.cff"))
    assert '__version__ = "0.7.0"' in read("cge_core/__init__.py")


def test_readme_is_practitioner_first_and_exposes_colab_control_room():
    readme = read("README.md")
    assert "StandardCGE.example().solve()" in readme
    assert "CGE-Core Control Room" in readme
    assert "01_first_cge.ipynb" in readme
    assert "IFPRI clean-room boundary" in readme
    assert readme.index("StandardCGE.example().solve()") < readme.index("PyCGE")


def test_control_room_is_v070_not_v06_generator():
    app = read("docs/microsites/control-room/assets/app.js")
    assert "CGE_CORE_TARGET_VERSION = '0.7.0'" in app
    assert "from cge_core import StandardCGE" in app
    assert "from cge_core import CGE, example_data" not in app
