import pytest

pytestmark = pytest.mark.public_ifpri


def test_synthetic_ifpri_is_installed_and_valid():
    from cge_core.models.ifpri.synthetic import build_synthetic_ifpri_dataset
    dataset = build_synthetic_ifpri_dataset()
    assert dataset.sam.table_name == "SYNTHETIC_SAM"
    assert "ROW" in dataset.sets.accounts
    assert dataset.source_path.name == "synthetic.py"


def test_public_ifpri_constructor_is_explicitly_synthetic():
    from cge_core import IFPRICGE
    economy = IFPRICGE.synthetic()
    assert economy.source_kind == "synthetic"
