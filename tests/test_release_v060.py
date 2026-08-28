"""Release-consistency guards for CGE-Core v0.6.0."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_metadata_is_v060():
    pyproject = read("pyproject.toml")
    citation = read("CITATION.cff")
    init = read("cge_core/__init__.py")
    readme = read("README.md")

    assert 'version = "0.6.0"' in pyproject
    assert re.search(r"(?m)^version:\s*0\.6\.0\s*$", citation)
    assert '__version__ = "0.6.0"' in init
    assert "version = {0.6.0}," in readme

    for stale in ('version = "0.5.0"', "version: 0.5.0", "version = {0.5.0},"):
        assert stale not in pyproject
        assert stale not in citation
        assert stale not in readme


def test_changelog_leads_with_v060():
    changelog = read("CHANGELOG.md")
    releases = [
        line for line in changelog.splitlines()
        if line.startswith("## v")
    ]
    assert releases
    assert releases[0].startswith("## v0.6.0 ")
    assert "### Migration from the lower-level workflow" in changelog
    assert "`PyCGE` remains supported as the advanced/lower-level API" in changelog


def test_release_docs_do_not_point_to_old_development_branch():
    notebooks = read("notebooks/README.md")
    assert "CGE_CORE_REF=v0.6.0" in notebooks
    assert "CGE_CORE_REF=v0.6-phase4b-notebooks" not in notebooks
    assert "supported advanced/lower-level API" in notebooks
    assert "supported legacy/advanced API" not in notebooks


def test_readme_describes_released_lower_level_status():
    readme = read("README.md")
    assert "### Advanced / lower-level workflow API" in readme
    assert "### Legacy and advanced workflow API" not in readme
    assert "existing code in the v0.6 line" in readme
    assert "during the v0.6 migration" not in readme


def test_control_room_targets_v060():
    app = read("docs/microsites/control-room/assets/app.js")
    assert "const CGE_CORE_TARGET_VERSION = '0.6.0';" in app


def test_api_docstring_does_not_claim_public_domain_status():
    api = read("cge_core/api.py")
    first = api.splitlines()[1]
    assert "Public scientific API for CGE-Core v0.6." in first
    assert "Public domain API" not in api
