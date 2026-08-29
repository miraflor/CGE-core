import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    "os.chdir(", "os.environ[\"PATH\"]", "amplpy.modules", "subprocess.run",
]


def notebook_text(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join("".join(cell.get("source", [])) for cell in nb["cells"])


def main():
    nbdir = ROOT / "notebooks"
    docs_nb = ROOT / "docs" / "notebooks"
    for name in CANONICAL:
        a = nbdir / name
        b = docs_nb / name
        assert a.is_file(), f"missing canonical notebook: {name}"
        assert b.is_file(), f"missing docs notebook copy: {name}"
        assert a.read_bytes() == b.read_bytes(), f"docs copy differs: {name}"
    for name in LEGACY:
        assert (nbdir / name).is_file(), f"missing legacy redirect: {name}"
    for path in sorted(nbdir.glob("*.ipynb")):
        text = notebook_text(path)
        for token in FORBIDDEN:
            assert token not in text, (path.name, token)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for required in (
        "StandardCGE.example().solve()", "CGE-Core Control Room", "01_first_cge.ipynb",
        "ifpri_cleanroom.md",
    ):
        assert required in readme, required
    app = (ROOT / "docs/microsites/control-room/assets/app.js").read_text(encoding="utf-8")
    assert "CGE_CORE_TARGET_VERSION = '0.7.0'" in app
    assert "from cge_core import StandardCGE" in app
    assert "from cge_core import CGE, example_data" not in app
    print("documentation/notebook/control-room checks passed")


if __name__ == "__main__":
    main()
