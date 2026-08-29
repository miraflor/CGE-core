from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "docs" / "microsites" / "control-room" / "assets" / "app.js"
FIXTURE = ROOT / "tests" / "fixtures" / "control_room_stdcge_tariff.py.txt"


def test_control_room_targets_v070_practitioner_api():
    text = APP.read_text(encoding="utf-8")
    assert "CGE_CORE_TARGET_VERSION = '0.7.0'" in text
    assert "from cge_core import StandardCGE" in text
    assert "StandardCGE.example().solve()" in text
    assert "const method=shock==='tariff'?'tariff':'production_tax';" in text
    assert "from cge_core import CGE, example_data" not in text
    assert "detect_solver" not in text
    assert "CGE_CORE_REF" not in text


def test_frozen_standard_tariff_fixture_is_v070_surface():
    text = FIXTURE.read_text(encoding="utf-8")
    assert "from cge_core import StandardCGE" in text
    assert 'base = StandardCGE.example().solve()' in text
    assert 'scenario = base.scenario("Tariff reform")' in text
    assert 'scenario.tariff("BRD", 0)' in text
    assert 'result = scenario.solve()' in text
    assert 'comparison = result.compare(base)' in text
    assert "PyCGE" not in text
