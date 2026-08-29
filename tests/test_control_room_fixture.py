# -*- coding: utf-8 -*-
"""Guard the Control Room generator across the v0.7 practitioner transition."""
from pathlib import Path
import runpy

from ._util import requires_solver

ROOT = Path(__file__).parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "control_room_stdcge_tariff.py.txt"
APP = ROOT / "docs" / "microsites" / "control-room" / "assets" / "app.js"


def test_control_room_fixture_keeps_supported_v06_compatibility_surface():
    source = FIXTURE.read_text(encoding="utf-8")
    compile(source, str(FIXTURE), "exec")
    for needle in (
        "from cge_core import CGE, example_data",
        "from cge_core.models import StdCGE",
        "benchmark = model.solve_benchmark(",
        'scenario = benchmark.scenario("control-room tariff abolition")',
        'scenario.set("taum", "BRD", 0.0)',
        "comparison = result.compare(benchmark)",
    ):
        assert needle in source


def test_control_room_targets_v070_without_reintroducing_low_level_workflow():
    source = APP.read_text(encoding="utf-8")
    assert "const CGE_CORE_TARGET_VERSION = '0.7.0';" in source
    for forbidden in (
        "'from cge_core import PyCGE, example_data'",
        "cge.model_calibrate(",
        "cge.model_sim()",
        "cge.model_modify_sim(",
        "cge.model_solve(",
        "cge.model_compare()",
    ):
        assert forbidden not in source
    assert "build_and_solve_ifpri_scenarios" in source
    assert "from cam.replicate_experiments import (" in source


@requires_solver
def test_control_room_fixture_still_executes_after_v070_transition(tmp_path):
    script = tmp_path / "control_room_generated.py"
    script.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    namespace = runpy.run_path(str(script))
    benchmark = namespace["benchmark"]
    result = namespace["result"]
    comparison = namespace["comparison"]
    assert result.name == "control-room tariff abolition"
    assert result.value("taum", "BRD") == 0.0
    assert not comparison.empty
    assert comparison.attrs["objective"]["reference"] == benchmark.objective
