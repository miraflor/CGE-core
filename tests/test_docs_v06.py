"""Source-level guards for the v0.6 documentation migration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read(path):
    return (DOCS / path).read_text(encoding="utf-8")


def test_public_api_page_documents_facade_objects():
    text = read("api/public.md")
    for name in ("CGE", "Equilibrium", "Scenario", "Result"):
        assert f"cge_core.api.{name}" in text
    assert "universal closure API" in text


def test_quickstart_uses_v06_public_api():
    text = read("getting-started/quickstart.md")
    assert "from cge_core import CGE, example_data" in text
    assert "from cge_core.models import StdCGE" in text
    assert "solve_benchmark(" in text
    assert ".scenario(" in text
    assert ".set(" in text
    assert ".compare(benchmark)" in text
    assert "PyCGE" not in text


def test_api_index_prioritizes_public_surface():
    text = read("api/index.md")
    assert text.index("{doc}`public`") < text.index("{doc}`engine`")
    assert "Advanced/lower-level `PyCGE`" in text


def test_engine_and_workflow_are_explicitly_advanced():
    engine = read("api/engine.md")
    workflow = read("workflow.md")
    assert engine.startswith("# Advanced Engine API")
    assert workflow.startswith("# Advanced PyCGE engine workflow")
    assert "ordinary Hosoe-model use" in workflow


def test_toc_includes_public_api_before_engine():
    toc = read("_toc.yml")
    assert "- file: api/public" in toc
    assert toc.index("- file: api/public") < toc.index("- file: api/engine")


def test_getting_started_uses_benchmark_scenario_result_language():
    overview = read("getting-started/overview.md")
    first = read("getting-started/first-simulation.md")
    assert "solve benchmark" in overview
    assert "protected solved benchmark" not in overview  # prose stays user-facing
    assert "CGE-Core calls the SAM-replicating static reference state the **benchmark**" in first
    assert "`Result` is an immutable numerical snapshot" in first
