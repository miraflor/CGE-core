from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9-3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]

def test_pyproject_packages_cam_cli_and_default_solver_support():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == "0.7.0"
    assert data["project"]["scripts"]["cge"] == "cge_core.cli:main"
    assert "cam*" in data["tool"]["setuptools"]["packages"]["find"]["include"]
    assert "cam" in data["tool"]["setuptools"]["package-data"]
    assert any(dep.startswith("amplpy") for dep in data["project"]["dependencies"])
    assert data["project"]["optional-dependencies"]["solver"] == []

def test_practitioner_readme_leads_with_short_workflow_and_no_solver_bootstrap():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "StandardCGE.example().solve()" in text
    assert "reform.tariff" in text
    assert text.index("StandardCGE.example().solve()") < text.index("PyCGE")
    assert "install_solver()" not in text
    assert "cge install-solver" not in text
    assert "cge-core[solver]" not in text
