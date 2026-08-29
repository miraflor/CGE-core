from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "docs" / "microsites" / "control-room"
APP = CONTROL / "assets" / "app.js"
CSS = CONTROL / "assets" / "styles.css"
HTML = CONTROL / "index.html"
FIXTURE = ROOT / "tests" / "fixtures" / "control_room_stdcge_tariff.py.txt"


def test_control_room_retains_mature_six_step_surface():
    html = HTML.read_text(encoding="utf-8")
    for item in (
        'id="modelStep"', 'id="walkthroughStep"', 'id="economyStep"',
        'id="closureStep"', 'id="scenarioStep"', 'id="scriptStep"',
        'id="notationPrimer"', 'id="variableGlossary"', 'id="flowStory"',
        'id="scenarioStack"', 'id="codePreview"', 'id="outputsGrid"',
        'id="themeSelect"', 'id="downloadPyBtn"', 'id="downloadJsonBtn"',
    ):
        assert item in html
    assert APP.stat().st_size > 50000
    assert CSS.stat().st_size > 10000


def test_control_room_inherits_jupyter_book_theme():
    html = HTML.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    assert "document.referrer" in html
    assert "localStorage.getItem('mode')" in html
    assert "inheritedDocsTheme" in app
    assert "mode==='auto'" in app
    assert "mode==='light'||mode==='dark'" in app


def test_control_room_uses_restored_diagram_geometry():
    app = APP.read_text(encoding="utf-8")
    assert 'viewBox="0 0 720 270"' in app
    assert "node(275,94,170,76,'Firms & sectors'" in app
    assert "node(55,95,150,70,'Household'" in app
    assert 'viewBox="0 0 440 300"' not in app


def test_control_room_restores_persistent_state_and_rich_model_reading():
    app = APP.read_text(encoding="utf-8")
    assert "cge-control-room-state-v070" in app
    assert "Armington elasticity" in app
    assert "CET elasticity" in app
    assert "Direct-tax adjustment" in app
    assert "Published sector production quantity" in app


def test_control_room_generates_practitioner_api_without_solver_bootstrap():
    app = APP.read_text(encoding="utf-8")
    assert "CGE_CORE_TARGET_VERSION = '0.7.0'" in app
    for item in (
        "SimpleCGE", "StandardCGE", "IFPRICGE", "CamCGE",
        "scenario.tariff", "scenario.endowment", "StandardCGE.from_sam",
        "TARCUT1", "EXP1", "EXP2", "EXP3",
    ):
        assert item in app
    assert "from cge_core import CGE, example_data" not in app
    assert "solve_benchmark(" not in app
    assert "numeraire=" not in app
    assert "redundant=" not in app
    assert "cge install-solver" not in app
    assert "cge-core[solver]" not in app


def test_canonical_tariff_fixture_is_embedded_as_regression_target():
    fixture = FIXTURE.read_text(encoding="utf-8").strip()
    app = APP.read_text(encoding="utf-8")
    assert fixture in app
