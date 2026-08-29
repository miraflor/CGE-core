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
FORBIDDEN_NOTEBOOK = [
    "git clone", "git fetch", "git reset --hard", "CGE_CORE_REF", "sys.path.insert",
    "os.chdir(", 'os.environ["PATH"]', "amplpy.modules", "subprocess.run",
    "install_solver", "cge-core[solver]",
]
PUBLIC_SOLVER_BOOTSTRAP = [
    "install_solver()",
    "cge install-solver",
    "cge-core[solver]",
]

def notebook_text(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join("".join(cell.get("source", [])) for cell in nb["cells"])

def main():
    nbdir = ROOT / "notebooks"
    docs_nb = ROOT / "docs" / "notebooks"

    for name in CANONICAL:
        a, b = nbdir / name, docs_nb / name
        assert a.is_file(), f"missing canonical notebook: {name}"
        assert b.is_file(), f"missing docs notebook copy: {name}"
        assert a.read_bytes() == b.read_bytes(), f"docs copy differs: {name}"

    for name in LEGACY:
        assert (nbdir / name).is_file(), f"missing legacy redirect: {name}"

    for path in sorted(nbdir.glob("*.ipynb")):
        body = notebook_text(path)
        for token in FORBIDDEN_NOTEBOOK:
            assert token not in body, (path.name, token)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for required in (
        "StandardCGE.example().solve()", "CGE-Core Control Room",
        "01_first_cge.ipynb", "ifpri_cleanroom.md",
    ):
        assert required in readme, required

    public_docs = [
        ROOT / "README.md",
        ROOT / "docs/install.md",
        ROOT / "docs/getting-started/installation.md",
        ROOT / "docs/tutorials/colab-notebooks.md",
    ]
    for path in public_docs:
        text = path.read_text(encoding="utf-8")
        for token in PUBLIC_SOLVER_BOOTSTRAP:
            assert token not in text, (path, token)

    notebook_page = (ROOT / "docs/tutorials/colab-notebooks.md").read_text(encoding="utf-8")
    for name in CANONICAL:
        stem = name[:-6]
        assert f"../notebooks/{stem}" in notebook_page, name
        assert f"notebooks/{name}" in notebook_page, name
    assert notebook_page.count("colab.research.google.com") >= 7

    config = (ROOT / "docs/_config.yml").read_text(encoding="utf-8")
    for required in (
        "sphinxcontrib.mermaid", 'mermaid_version: "11.12.1"',
        "mermaid_d3_zoom: true", "mermaid_fullscreen: true",
    ):
        assert required in config, required

    toc = (ROOT / "docs/_toc.yml").read_text(encoding="utf-8")
    for required in (
        "Getting Started", "Practitioner Guides", "Models", "Theory", "Tutorials",
        "Executable Notebooks", "Validation", "API Reference", "Developer Reference",
        "Detailed Reference", "theory/overview", "api/public", "architecture",
    ):
        assert required in toc, required

    for diagram in (
        ROOT / "docs/diagrams/pycge-architecture.mmd",
        ROOT / "docs/diagrams/standard-cge-theory.mmd",
        ROOT / "docs/diagrams/cge-core-v070-public.mmd",
    ):
        assert diagram.is_file(), f"missing Mermaid source: {diagram.name}"
        assert diagram.stat().st_size > 200, f"Mermaid source unexpectedly tiny: {diagram.name}"

    html = (ROOT / "docs/microsites/control-room/index.html").read_text(encoding="utf-8")
    app_path = ROOT / "docs/microsites/control-room/assets/app.js"
    css_path = ROOT / "docs/microsites/control-room/assets/styles.css"
    app = app_path.read_text(encoding="utf-8")

    for required_id in (
        'id="modelStep"', 'id="walkthroughStep"', 'id="economyStep"',
        'id="closureStep"', 'id="scenarioStep"', 'id="scriptStep"',
        'id="notationPrimer"', 'id="variableGlossary"', 'id="flowStory"',
        'id="scenarioStack"', 'id="downloadPyBtn"', 'id="downloadJsonBtn"',
    ):
        assert required_id in html, required_id

    assert app_path.stat().st_size > 30000, "Control Room app was unexpectedly simplified"
    assert css_path.stat().st_size > 10000, "Control Room styling was unexpectedly simplified"
    assert "CGE_CORE_TARGET_VERSION = '0.7.0'" in app
    assert "from cge_core import StandardCGE" in app
    assert "from cge_core import CGE, example_data" not in app
    assert "cge install-solver" not in app
    assert "cge-core[solver]" not in app
    for required in ("TARCUT1", "EXP1", "scenario.tariff", "scenario.endowment", "StandardCGE.from_sam"):
        assert required in app, required

    architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
    assert "cge-core-v070-public.mmd" in architecture
    assert "pycge-architecture.mmd" in architecture
    theory = (ROOT / "docs/theory/overview.md").read_text(encoding="utf-8")
    assert "standard-cge-theory.mmd" in theory

    print("documentation/notebook/control-room/Mermaid checks passed")

if __name__ == "__main__":
    main()
