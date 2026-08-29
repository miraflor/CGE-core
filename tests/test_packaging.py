from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9-3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
WHEEL_URL = "https://github.com/miraflor/CGE-core/releases/download/v0.7.0/cge_core-0.7.0-py3-none-any.whl"
SOURCE_ARCHIVE = "archive/refs/tags/v0.7.0.zip"


def test_pyproject_packages_only_runtime_namespaces_and_default_solver_support():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["version"] == "0.7.0"
    assert data["project"]["scripts"]["cge"] == "cge_core.cli:main"

    include = set(data["tool"]["setuptools"]["packages"]["find"]["include"])
    assert include == {"cge_core*", "cam*"}

    package_data = data["tool"]["setuptools"]["package-data"]
    assert "cge_core" in package_data
    assert "models/camcge/data/*.csv" in package_data["cge_core"]
    assert "cam" not in package_data

    assert any(dep.startswith("amplpy") for dep in data["project"]["dependencies"])
    assert data["project"]["optional-dependencies"]["solver"] == []


def test_practitioner_readme_uses_release_wheel_not_repository_archive():
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "StandardCGE.example().solve()" in text
    assert "reform.tariff" in text
    assert text.index("StandardCGE.example().solve()") < text.index("PyCGE")
    assert WHEEL_URL in text
    assert SOURCE_ARCHIVE not in text

    assert "install_solver()" not in text
    assert "cge install-solver" not in text
    assert "cge-core[solver]" not in text


def test_release_workflow_builds_checks_and_publishes_wheel():
    text = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "python -m build --wheel" in text
    assert "forbidden_roots" in text
    assert "repository-only content leaked into wheel" in text
    assert 'gh release upload "${TAG}" dist/*.whl --clobber' in text
    assert "gh release edit" in text


def test_notebook_ci_executes_from_built_wheel_not_checkout_source():
    text = (ROOT / ".github" / "workflows" / "notebooks.yml").read_text(encoding="utf-8")

    assert "python -m build --wheel" in text
    assert "python -m pip install dist/*.whl" in text
    assert "TemporaryDirectory" in text
    assert "allow_errors=False" in text
    assert "pip install -e" not in text
