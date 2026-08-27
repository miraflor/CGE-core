# -*- coding: utf-8 -*-
"""Smoke the frozen Control Room code-generation reference fixture."""
from pathlib import Path
import runpy

from ._util import requires_solver

FIXTURE = Path(__file__).parent / "fixtures" / "control_room_stdcge_tariff.py.txt"


def test_control_room_fixture_is_valid_python():
    source = FIXTURE.read_text(encoding="utf-8")
    compile(source, str(FIXTURE), "exec")
    assert "PyCGE" in source
    assert "model_modify_sim" in source


@requires_solver
def test_control_room_fixture_executes_legacy_workflow(tmp_path):
    # runpy expects a .py path; write the frozen text verbatim to a temporary
    # script rather than importing it as a pytest module.
    script = tmp_path / "control_room_generated.py"
    script.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    namespace = runpy.run_path(str(script))
    assert namespace["cge"].sim_solved is True
