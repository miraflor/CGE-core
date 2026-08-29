import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NBDIR = ROOT / "notebooks"
CANONICAL = [
    "01_first_cge.ipynb", "02_policy_experiments.ipynb", "03_your_own_sam.ipynb",
    "04_camcge.ipynb", "05_ifpri.ipynb", "06_build_a_model.ipynb", "90_internals.ipynb",
]
LEGACY = [
    "00_start_here.ipynb", "01_your_first_cge.ipynb", "02_open_economy_cge.ipynb",
    "03_policy_experiments.ipynb", "04_bring_your_own_sam.ipynb",
    "05_ifpri_standard_cge.ipynb", "06_camcge_replication.ipynb", "07_under_the_hood.ipynb",
]
FORBIDDEN = [
    "git clone", "git fetch", "git reset --hard", "CGE_CORE_REF", "sys.path.insert",
    "os.chdir(", 'os.environ["PATH"]', "amplpy.modules", "subprocess.run",
    "install_solver", "cge-core[solver]",
]

def text(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join("".join(cell.get("source", [])) for cell in nb["cells"])

def test_canonical_sequence_exists_and_docs_copies_match():
    for name in CANONICAL:
        assert (NBDIR / name).is_file()
        assert (ROOT / "docs" / "notebooks" / name).read_bytes() == (NBDIR / name).read_bytes()

def test_every_notebook_is_free_of_bootstrap_plumbing():
    for path in NBDIR.glob("*.ipynb"):
        body = text(path)
        for token in FORBIDDEN:
            assert token not in body, (path.name, token)

def test_legacy_names_are_redirects_not_old_tutorials():
    for name in LEGACY:
        body = text(NBDIR / name)
        assert "legacy filename" in body.lower()
        assert "canonical v0.7.0 notebook" in body

def test_first_notebook_is_one_install_line_then_practitioner_api():
    body = text(NBDIR / "01_first_cge.ipynb")
    assert "from cge_core import StandardCGE" in body
    assert "StandardCGE.example().solve()" in body
    assert "refs/tags/v0.7.0.zip" in body
    assert "cge-core @ https://" in body
    assert "PyCGE" not in body

def test_tutorial_page_exposes_every_notebook_and_colab_link():
    page = (ROOT / "docs" / "tutorials" / "colab-notebooks.md").read_text(encoding="utf-8")
    for name in CANONICAL:
        stem = name[:-6]
        assert f"../notebooks/{stem}" in page
        assert f"notebooks/{name}" in page
    assert page.count("colab.research.google.com") >= 7
