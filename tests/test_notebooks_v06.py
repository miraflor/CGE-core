"""Source-level safeguards for the v0.6 notebook migration."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
NOTEBOOKS = [
    "00_start_here.ipynb",
    "01_your_first_cge.ipynb",
    "02_open_economy_cge.ipynb",
    "03_policy_experiments.ipynb",
    "04_bring_your_own_sam.ipynb",
    "05_ifpri_standard_cge.ipynb",
    "06_camcge_replication.ipynb",
    "07_under_the_hood.ipynb",
]
MIGRATED_HOSOE = NOTEBOOKS[1:5]


def _load(name: str) -> dict:
    return json.loads((NOTEBOOK_DIR / name).read_text(encoding="utf-8"))


def _all_text(nb: dict) -> str:
    return "\n".join("".join(cell.get("source", [])) for cell in nb["cells"])


def _code_text(nb: dict) -> str:
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in nb["cells"]
        if cell.get("cell_type") == "code"
    )


def test_notebooks_are_valid_json_and_python_source():
    for name in NOTEBOOKS:
        nb = _load(name)
        assert nb["nbformat"] == 4
        for cell in nb["cells"]:
            if cell.get("cell_type") == "code":
                ast.parse("".join(cell.get("source", [])), filename=f"{name}:{cell.get('id')}")


def test_every_notebook_setup_is_branch_safe():
    for name in NOTEBOOKS:
        code = _code_text(_load(name))
        assert 'CGE_CORE_REF = os.environ.get("CGE_CORE_REF", "main")' in code
        assert '"reset", "--hard", "origin/main"' not in code
        assert '"reset", "--hard", "FETCH_HEAD"' in code
        assert "current checkout" in code


def test_hosoe_teaching_notebooks_use_v06_public_api():
    for name in MIGRATED_HOSOE:
        text = _all_text(_load(name))
        assert "from cge_core import CGE" in text
        assert "from cge_core.models import" in text
        assert "solve_benchmark(" in text
        assert ".scenario(" in text
        assert "PyCGE" not in text
        assert "model_sim(" not in text
        assert "model_modify_sim(" not in text
        assert "model_compare(" not in text
        assert "base_value" not in text
        assert "sim_value" not in text


def test_policy_notebook_demonstrates_multiple_live_scenarios():
    text = _all_text(_load("03_policy_experiments.ipynb"))
    assert text.count("benchmark.scenario(") >= 4
    assert "tariff_scenario" in text
    assert "production_tax_scenario" in text
    assert "capital_scenario" in text


def test_specialized_notebooks_keep_their_validated_paths():
    ifpri = _all_text(_load("05_ifpri_standard_cge.ipynb"))
    cam = _all_text(_load("06_camcge_replication.ipynb"))
    hood = _all_text(_load("07_under_the_hood.ipynb"))

    assert "from cge_core.ifpri import" in ifpri
    assert "from cge_core import CGE" not in ifpri
    assert "from cam.replicate_base import" in cam
    assert "from cge_core import PyCGE" in hood
    assert "Why `PyCGE` appears here" in hood


def test_notebook_readme_documents_branch_validation():
    text = (NOTEBOOK_DIR / "README.md").read_text(encoding="utf-8")
    assert "CGE_CORE_REF" in text
    assert "current checkout" in text
    assert "Equilibrium" in text
    assert "Scenario" in text
    assert "Result" in text
