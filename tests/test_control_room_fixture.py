# -*- coding: utf-8 -*-
"""Guard the v0.6 Control Room code-generation surface."""
from pathlib import Path
import runpy

from ._util import requires_solver

ROOT = Path(__file__).parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "control_room_stdcge_tariff.py.txt"
APP = ROOT / "docs" / "microsites" / "control-room" / "assets" / "app.js"


def test_control_room_fixture_is_v06_public_python():
    source = FIXTURE.read_text(encoding="utf-8")
    compile(source, str(FIXTURE), "exec")

    expected = (
        "from cge_core import CGE, example_data",
        "from cge_core.models import StdCGE",
        "model = CGE(",
        "benchmark = model.solve_benchmark(",
        'scenario = benchmark.scenario("control-room tariff abolition")',
        'scenario.set("taum", "BRD", 0.0)',
        "result = scenario.solve(",
        "comparison = result.compare(benchmark)",
    )
    for needle in expected:
        assert needle in source

    forbidden = (
        "PyCGE",
        "model_calibrate",
        "model_sim(",
        "model_modify_sim",
        "model_solve(",
        "model_compare(",
    )
    for needle in forbidden:
        assert needle not in source


def test_control_room_generator_targets_v06_public_api():
    source = APP.read_text(encoding="utf-8")

    expected = (
        "const CGE_CORE_TARGET_VERSION = '0.6.0';",
        "'from cge_core import CGE, example_data'",
        "`from cge_core.models import ${modelClass}`",
        "model = CGE(model=${ctor}, data=DATA_DIR)",
        "benchmark = model.solve_benchmark(",
        'scenario = benchmark.scenario("control-room scenario")',
        "scenario.set(${py(ctrl.component)}, ${idx},",
        "result = scenario.solve(solver=solver)",
        "results = result.compare(benchmark)",
        "equivalent_variation(benchmark, result)",
    )
    for needle in expected:
        assert needle in source

    forbidden = (
        "'from cge_core import PyCGE, example_data'",
        "cge.model_calibrate(",
        "cge.model_sim()",
        "cge.model_modify_sim(",
        "cge.model_solve(",
        "cge.model_compare()",
    )
    for needle in forbidden:
        assert needle not in source

    # The two specialized model families deliberately keep their validated,
    # dedicated execution paths.
    assert "build_and_solve_ifpri_scenarios" in source
    assert "from cam.replicate_experiments import (" in source


@requires_solver
def test_control_room_fixture_executes_public_workflow(tmp_path):
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
