# -*- coding: utf-8 -*-
"""
Tests for cge_core.samtools and the configurable account labels.

The point of the pair is loading a real-country SAM without editing model
code: samtools derives the set files from the SAM itself, and the
``accounts=`` mapping on the model definitions relabels the institutional
accounts the equations read. Both are verified against the bundled
stdcge SAM -- once as-is, and once with every institutional account
renamed -- and the relabelled economy must calibrate to the *identical*
equilibrium, which is the strongest available check that the mapping is
wired into every equation that needs it.
"""
import csv

import pytest

from pyomo.environ import value

from ._util import SOLVER, STD_DATA_DIR, requires_solver

RENAMES = {
    'HOH': 'HH',
    'GOV': 'GOVT',
    'INV': 'SAV-INV',
    'EXT': 'ROW',
    'IDT': 'ITAX',
    'TRF': 'TARIFF',
}
ACCOUNTS = {
    'hoh': 'HH',
    'gov': 'GOVT',
    'inv': 'SAV-INV',
    'ext': 'ROW',
    'idt': 'ITAX',
    'trf': 'TARIFF',
}
STD_INSTITUTIONS = ['HOH', 'GOV', 'INV', 'EXT', 'IDT', 'TRF']


def _renamed_sam(tmp_path):
    """Copy the bundled stdcge SAM with every institution relabelled."""
    source = STD_DATA_DIR + '/param-sam-.csv'
    destination = tmp_path / 'renamed_sam.csv'
    with open(source, newline='') as handle:
        rows = list(csv.reader(handle))
    for row in rows:
        for k, cell in enumerate(row):
            row[k] = RENAMES.get(cell.strip(), cell)
    with destination.open('w', newline='') as handle:
        csv.writer(handle).writerows(rows)
    return destination


# ----------------------------------------------------------------------
# samtools: deriving sets from a SAM
# ----------------------------------------------------------------------
def test_derive_sets_partitions_accounts():
    from cge_core import samtools

    goods, factors = samtools.derive_sets(
        STD_DATA_DIR + '/param-sam-.csv',
        factors=['CAP', 'LAB'],
        institutions=STD_INSTITUTIONS)
    assert goods == ['BRD', 'MLK']
    assert factors == ['CAP', 'LAB']


def test_derive_sets_rejects_unknown_account():
    from cge_core import samtools
    from cge_core.compat.pycge import DataValidationError

    with pytest.raises(DataValidationError, match='not present'):
        samtools.derive_sets(
            STD_DATA_DIR + '/param-sam-.csv',
            factors=['CAP', 'LAB'],
            institutions=STD_INSTITUTIONS + ['NOT_AN_ACCOUNT'])


def test_derive_sets_rejects_factor_institution_overlap():
    from cge_core import samtools
    from cge_core.compat.pycge import DataValidationError

    with pytest.raises(DataValidationError, match='both factor and'):
        samtools.derive_sets(
            STD_DATA_DIR + '/param-sam-.csv',
            factors=['CAP', 'LAB'],
            institutions=STD_INSTITUTIONS + ['CAP'])


def test_build_dataset_writes_loadable_directory(tmp_path):
    from cge_core import PyCGE, samtools
    from cge_core.models.standard.model import StdModelDef

    out = samtools.build_dataset(
        STD_DATA_DIR + '/param-sam-.csv', tmp_path / 'data',
        factors=['CAP', 'LAB'], institutions=STD_INSTITUTIONS)
    for name in ('set-i-.csv', 'set-h-.csv', 'set-u-.csv',
                 'param-sam-.csv'):
        assert (out / name).is_file()

    cge = PyCGE(StdModelDef())
    cge.model_data(str(out))
    cge.model_instance('pf', 'LAB')
    assert sorted(cge.base.i) == ['BRD', 'MLK']
    assert sorted(cge.base.h) == ['CAP', 'LAB']
    # Calibrated parameters must match the bundled dataset exactly.
    assert value(cge.base.taud) == pytest.approx(23.0 / 90.0)


def test_build_dataset_rejects_unbalanced_sam(tmp_path):
    from cge_core import samtools
    from cge_core.compat.pycge import DataValidationError

    bad = tmp_path / 'bad.csv'
    bad.write_text('U,A,B\nA,0,1\nB,0,0\n')
    with pytest.raises(DataValidationError, match='not balanced'):
        samtools.build_dataset(bad, tmp_path / 'data',
                               factors=['A'], institutions=['B'])


# ----------------------------------------------------------------------
# Configurable account labels on the model definitions
# ----------------------------------------------------------------------
def test_unknown_account_key_is_rejected():
    from cge_core.models.standard.model import StdModelDef

    with pytest.raises(ValueError, match='Unknown account keys'):
        StdModelDef(accounts={'household': 'HH'})


def test_relabelled_accounts_build_and_calibrate_structurally(tmp_path):
    """A fully relabelled SAM must produce identical calibrated params."""
    from cge_core import PyCGE, samtools
    from cge_core.models.standard.model import StdModelDef

    sam = _renamed_sam(tmp_path)
    out = samtools.build_dataset(sam, tmp_path / 'data',
                                 factors=['CAP', 'LAB'],
                                 institutions=ACCOUNTS.values())
    cge = PyCGE(StdModelDef(accounts=ACCOUNTS))
    cge.model_data(str(out))
    cge.model_instance('pf', 'LAB')

    reference = PyCGE(StdModelDef())
    reference.model_data(STD_DATA_DIR)
    reference.model_instance('pf', 'LAB')

    for name in ('taud', 'ssp', 'ssg'):
        assert value(getattr(cge.base, name)) == pytest.approx(
            value(getattr(reference.base, name)), abs=1e-12)
    for i in cge.base.i:
        for name in ('alpha', 'tauz', 'taum', 'deltam', 'gamma', 'theta',
                     'lambd', 'mu'):
            assert value(getattr(cge.base, name)[i]) == pytest.approx(
                value(getattr(reference.base, name)[i]), abs=1e-12)


@requires_solver
def test_relabelled_accounts_reproduce_identical_equilibrium(tmp_path):
    """End to end: renamed institutions, same economy, same solution."""
    from cge_core import PyCGE, samtools
    from cge_core.models.standard.model import StdModelDef

    sam = _renamed_sam(tmp_path)
    out = samtools.build_dataset(sam, tmp_path / 'data',
                                 factors=['CAP', 'LAB'],
                                 institutions=ACCOUNTS.values())
    cge = PyCGE(StdModelDef(accounts=ACCOUNTS))
    cge.model_data(str(out))
    cge.model_instance('pf', 'LAB')
    cge.model_drop_redundant('eqpf', 'LAB')
    cge.model_calibrate(SOLVER)

    expected = {'BRD': {'Z': 73.0, 'Xp': 20.0, 'M': 13.0, 'E': 8.0},
                'MLK': {'Z': 72.0, 'Xp': 30.0, 'M': 11.0, 'E': 4.0}}
    for i in cge.base.i:
        for name, target in expected[str(i)].items():
            assert value(getattr(cge.base, name)[i]) == pytest.approx(
                target, abs=1e-6)


def test_derive_sets_rejects_duplicate_role_labels():
    from cge_core import samtools
    from cge_core.compat.pycge import DataValidationError

    with pytest.raises(DataValidationError, match='Factor account labels'):
        samtools.derive_sets(
            STD_DATA_DIR + '/param-sam-.csv',
            factors=['CAP', 'CAP'],
            institutions=STD_INSTITUTIONS,
        )
    with pytest.raises(DataValidationError, match='Institutional account labels'):
        samtools.derive_sets(
            STD_DATA_DIR + '/param-sam-.csv',
            factors=['CAP', 'LAB'],
            institutions=[*STD_INSTITUTIONS, 'HOH'],
        )


def test_account_roles_must_have_distinct_nonempty_labels():
    from cge_core.models.simple.model import SplModelDef
    from cge_core.models.standard.model import StdModelDef

    with pytest.raises(ValueError, match='distinct'):
        StdModelDef(accounts={'hoh': 'GOV'})
    with pytest.raises(ValueError, match='non-empty'):
        SplModelDef(accounts={'hoh': '   '})
