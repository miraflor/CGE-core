"""Structural checks for the practitioner-first v0.7 documentation."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
NBDIR = ROOT / "notebooks"
REQUIRED = [
    "index.md", "install.md", "first_cge.md", "policy_experiments.md",
    "own_sam.md", "bundled_models.md", "authoring_python.md", "cge_md.md",
    "validation.md", "advanced.md", "_toc.yml",
]
RETAINED_BASELINE_DOCS = [
    "MODEL.md", "IFPRI.md", "GAMS_STDCGE_VALIDATION.md", "GAMS_CROSSWALK.md",
    "OG_CORE_CROSSWALK.md", "architecture.md",
]
NOTEBOOKS = [
    "01_first_cge.ipynb", "02_policy_experiments.ipynb",
    "03_your_own_sam.ipynb", "04_camcge.ipynb", "05_ifpri.ipynb",
    "06_build_a_model.ipynb", "90_internals.ipynb",
]
FORBIDDEN_NOTEBOOK_PLUMBING = (
    "git clone", "git fetch", "git reset --hard", "CGE_CORE_REF",
    "sys.path", "amplpy.modules", 'os.environ["PATH"]', "os.chdir(",
    "subprocess.run", "subprocess.check_call",
)


def _notebook_text(path):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", [])) for cell in notebook.get("cells", [])
    )


def main():
    missing = [name for name in REQUIRED if not (DOCS / name).is_file()]
    if (ROOT / "cge_core" / "engine.py").exists():
        missing += [name for name in RETAINED_BASELINE_DOCS if not (DOCS / name).is_file()]
    if missing:
        raise SystemExit(f"Missing v0.7 docs: {missing}")
    for name in NOTEBOOKS:
        path = NBDIR / name
        if not path.is_file():
            raise SystemExit(f"Missing v0.7 notebook: {name}")
        text = _notebook_text(path)
        for token in FORBIDDEN_NOTEBOOK_PLUMBING:
            if token in text:
                raise SystemExit(f"Notebook {name} contains forbidden plumbing: {token}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for symbol in ("StandardCGE.example().solve()", "IFPRICGE.synthetic()", "cge doctor"):
        if symbol not in readme:
            raise SystemExit(f"README missing practitioner surface: {symbol}")
    print("v0.7 documentation structure OK")


if __name__ == "__main__":
    main()
