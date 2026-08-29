from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9-3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_packages_cam_and_cli():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == "0.7.0"
    assert data["project"]["scripts"]["cge"] == "cge_core.cli:main"
    assert "cam*" in data["tool"]["setuptools"]["packages"]["find"]["include"]
    assert "cam" in data["tool"]["setuptools"]["package-data"]


def test_practitioner_readme_leads_with_short_workflow():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "StandardCGE.example().solve()" in text
    assert "reform.tariff" in text
    assert text.index("StandardCGE.example().solve()") < text.index("PyCGE")
