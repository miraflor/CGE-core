"""Regression guards for the v0.6 Phase 6 cleanup."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_first_time_user_surfaces_use_public_facade():
    installation = read("docs/getting-started/installation.md")
    loading = read("docs/tutorials/loading-sam.md")
    tariff = read("docs/tutorials/tariff-reform.md")

    for text in (installation, loading, tariff):
        assert "from cge_core import CGE" in text
        assert "from cge_core.models import StdCGE" in text
        assert "from cge_core import PyCGE" not in text
        assert "StdModelDef" not in text

    assert "solve_benchmark(" in tariff
    assert ".scenario(" in tariff
    assert ".set(" in tariff
    assert ".compare(benchmark)" in tariff
    for inherited_method in (
        "model_calibrate",
        "model_sim",
        "model_modify_sim",
        "model_solve",
        "model_compare",
    ):
        assert inherited_method not in tariff


def test_og_crosswalk_maps_to_public_workflow_first():
    text = read("docs/OG_CORE_CROSSWALK.md")
    assert "## Public workflow mapping" in text
    assert "CGE.solve_benchmark" in text
    assert "Scenario.set" in text
    assert "Scenario.solve" in text
    assert "Result.compare" in text
    assert "## Lower-level implementation" in text


def test_samtools_teaches_facade_but_keeps_internal_validator():
    text = read("cge_core/samtools.py")
    header = text.split('"""', 2)[1]
    assert "from cge_core import CGE, samtools" in header
    assert "from cge_core.models import StdCGE" in header
    assert "model = CGE(" in header
    assert "PyCGE._validate_sam_csv(path)" in text


def test_facade_calls_engine_lower_level_not_legacy():
    text = read("cge_core/api.py")
    assert "legacy" not in text.lower()
    assert "lower-level" in text
    assert "PyCGE" in text


def test_control_room_uses_model_language_not_implementation_class_name():
    text = read("docs/microsites/control-room/assets/app.js")
    assert "StdModelDef" not in text
    assert "Standard CGE model" in text


def test_project_role_metadata_is_explicit():
    config = read("docs/_config.yml")
    readme = read("README.md")
    citation = read("CITATION.cff")
    pyproject = read("pyproject.toml")

    assert "James Matthew Miraflor — Project Lead and Maintainer" in config
    assert "### Project leadership and maintenance" in readme
    assert "project lead and maintainer" in readme.lower()
    assert "cited as project lead and maintainer" in citation.lower()
    assert "authors = [" not in pyproject
    assert "maintainers = [" in pyproject
