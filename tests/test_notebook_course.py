import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NBDIR = ROOT / "notebooks"
CANONICAL = [
    "01_first_cge.ipynb", "02_policy_experiments.ipynb", "03_your_own_sam.ipynb",
    "04_camcge.ipynb", "05_ifpri.ipynb", "06_build_a_model.ipynb", "90_internals.ipynb",
]
WHEEL_URL = "https://github.com/miraflor/CGE-core/releases/download/v0.8.0/cge_core-0.8.0-py3-none-any.whl"
SOURCE_ARCHIVE = "archive/refs/tags/v0.8.0.zip"
FORBIDDEN = [
    "git clone", "git fetch", "git reset --hard", "CGE_CORE_REF", "sys.path.insert",
    "os.chdir(", 'os.environ["PATH"]', "amplpy.modules", "subprocess.run",
    "install_solver", "cge-core[solver]", SOURCE_ARCHIVE,
]


def text(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join("".join(cell.get("source", [])) for cell in nb["cells"])


def test_notebook_directory_is_one_unambiguous_course():
    actual = sorted(p.name for p in NBDIR.glob("*.ipynb"))
    assert actual == CANONICAL
    prefixes = [name.split("_", 1)[0] for name in CANONICAL]
    assert len(prefixes) == len(set(prefixes))


def test_canonical_sequence_exists_and_docs_copies_match():
    for name in CANONICAL:
        assert (ROOT / "docs" / "notebooks" / name).read_bytes() == (NBDIR / name).read_bytes()


def test_every_notebook_is_free_of_bootstrap_plumbing_and_source_archive_installs():
    for path in NBDIR.glob("*.ipynb"):
        body = text(path)
        for token in FORBIDDEN:
            assert token not in body, (path.name, token)


def test_every_canonical_notebook_installs_exact_release_wheel_once():
    for name in CANONICAL:
        assert text(NBDIR / name).count(WHEEL_URL) == 1, name


def test_first_notebook_is_one_install_line_then_practitioner_api():
    body = text(NBDIR / "01_first_cge.ipynb")
    assert "from cge_core import StandardCGE" in body
    assert "StandardCGE.example().solve()" in body
    assert WHEEL_URL in body
    assert "PyCGE" not in body


def test_tutorial_page_exposes_every_notebook_and_colab_link():
    page = (ROOT / "docs" / "tutorials" / "colab-notebooks.md").read_text(encoding="utf-8")
    for name in CANONICAL:
        stem = name[:-6]
        assert f"../notebooks/{stem}" in page
        assert f"notebooks/{name}" in page
    assert page.count("colab.research.google.com") >= 7
