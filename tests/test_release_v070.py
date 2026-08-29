"""Release-consistency guards for CGE-Core v0.7.0."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_metadata_is_v070():
    pyproject = read("pyproject.toml")
    citation = read("CITATION.cff")
    init = read("cge_core/__init__.py")
    assert 'version = "0.7.0"' in pyproject
    assert re.search(r"(?m)^version:\s*[\"']?0\.7\.0[\"']?\s*$", citation)
    assert '__version__ = "0.7.0"' in init


def test_changelog_leads_with_v070():
    changelog = read("CHANGELOG.md")
    releases = [line for line in changelog.splitlines() if line.startswith("## v")]
    assert releases and releases[0].startswith("## v0.7.0 ")


def test_readme_leads_with_practitioner_api():
    readme = read("README.md")
    assert "from cge_core import StandardCGE" in readme
    assert "StandardCGE.example().solve()" in readme
    assert "reform.tariff" in readme
    assert readme.index("StandardCGE.example().solve()") < readme.index("PyCGE")

