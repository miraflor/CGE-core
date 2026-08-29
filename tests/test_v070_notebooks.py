import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NBDIR = ROOT / "notebooks"
EXPECTED = [
    "01_first_cge.ipynb", "02_policy_experiments.ipynb", "03_your_own_sam.ipynb",
    "04_camcge.ipynb", "05_ifpri.ipynb", "06_build_a_model.ipynb",
    "90_internals.ipynb",
]
FORBIDDEN = [
    "git clone", "git fetch", "git reset --hard", "CGE_CORE_REF",
    "sys.path", "amplpy.modules", "os.environ[\"PATH\"]", "os.chdir(",
    "subprocess.run", "subprocess.check_call",
]


def _text(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join("".join(cell.get("source", [])) for cell in nb["cells"])


def test_public_notebook_sequence_exists():
    for name in EXPECTED:
        assert (NBDIR / name).is_file()


def test_ordinary_notebooks_have_no_infrastructure_bootstrap():
    for name in EXPECTED:
        text = _text(NBDIR / name)
        for token in FORBIDDEN:
            assert token not in text, (name, token)


def test_first_notebook_uses_practitioner_api():
    text = _text(NBDIR / "01_first_cge.ipynb")
    assert "from cge_core import StandardCGE" in text
    assert "StandardCGE.example().solve()" in text
    assert "PyCGE" not in text


def test_documentation_notebook_copies_match_canonical_notebooks():
    for name in EXPECTED:
        assert (ROOT / "docs" / "notebooks" / name).read_bytes() == (NBDIR / name).read_bytes()
