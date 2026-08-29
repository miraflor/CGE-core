# -*- coding: utf-8 -*-
"""
Regression tests for the PyCGE engine workflow.

The bugs fixed in this fork were all *silent* -- they produced plausible
numbers rather than errors, which is the failure mode that survives
casual use and corrupts published results. Each one gets a test here so
it cannot come back unnoticed:

  * sim variable export wrote base values (v0.2.0 fix)
  * model_compare reported a ratio, not a percentage change (v0.2.0 fix)
  * the objective difference used base - sim while every variable
    difference used sim - base (v0.2.1 fix)
  * guard clauses on the state machine were unreachable, so calling
    methods out of order raised AttributeError from deep inside the
    engine instead of explaining what to call first (v0.2.1 fix)

As of v0.3.0 the guards raise typed exceptions (WorkflowError /
ComponentError / DataValidationError) whose messages carry the guidance
that earlier versions printed, and model_compare returns a pandas
DataFrame.
"""
import os

import pytest

from pyomo.environ import value

from ._util import SOLVER, calibrated, quiet, requires_solver, std_instance


# ----------------------------------------------------------------------
# State machine: calling things out of order must explain, not explode
# ----------------------------------------------------------------------
def test_fresh_object_has_initialised_state():
    """__init__ must define every attribute the guards test against."""
    from cge_core.compat.pycge import PyCGE
    from cge_core.models.standard.model import StdModelDef

    cge = PyCGE(StdModelDef())
    for attr in ('data', 'base', 'sim', 'base_results', 'sim_results'):
        assert getattr(cge, attr) is None, "%s not initialised" % attr
    assert cge.base_calibrated is False
    assert cge.sim_solved is False


def test_drop_redundant_before_instance_raises_workflow_error():
    """Must raise guidance rather than AttributeError."""
    from cge_core.compat.pycge import PyCGE, WorkflowError
    from cge_core.models.standard.model import StdModelDef

    cge = PyCGE(StdModelDef())
    with pytest.raises(WorkflowError, match='BASE instance first'):
        cge.model_drop_redundant('eqpf', 'LAB')


def test_sim_before_calibrate_raises_workflow_error():
    from cge_core.compat.pycge import WorkflowError

    cge = std_instance()
    with pytest.raises(WorkflowError, match='calibrate'):
        cge.model_sim()
    assert cge.sim is None


def test_solve_before_calibrate_raises_workflow_error():
    from cge_core.compat.pycge import WorkflowError

    cge = std_instance()
    with pytest.raises(WorkflowError, match='calibrate'):
        cge.model_solve('ipopt')


def test_drop_redundant_unknown_constraint_raises_component_error():
    from cge_core.compat.pycge import ComponentError

    cge = std_instance(drop_redundant=False)
    with pytest.raises(ComponentError, match='does not exist'):
        cge.model_drop_redundant('not_a_constraint', 'LAB')


def test_drop_redundant_bad_index_raises_component_error():
    from cge_core.compat.pycge import ComponentError

    cge = std_instance(drop_redundant=False)
    with pytest.raises(ComponentError, match='does not exist'):
        cge.model_drop_redundant('eqpf', 'NOT_A_FACTOR')


def test_model_instance_unknown_variable_raises_component_error():
    from cge_core.compat.pycge import ComponentError, PyCGE
    from cge_core.models.standard.model import StdModelDef
    from ._util import STD_DATA_DIR

    cge = PyCGE(StdModelDef())
    cge.model_data(STD_DATA_DIR)
    with pytest.raises(ComponentError, match='does not exist'):
        cge.model_instance('not_a_var', 'LAB')


def test_compare_before_instances_raises_workflow_error():
    from cge_core.compat.pycge import PyCGE, WorkflowError
    from cge_core.models.standard.model import StdModelDef

    cge = PyCGE(StdModelDef())
    with pytest.raises(WorkflowError, match='BASE'):
        cge.model_compare('print')


# ----------------------------------------------------------------------
# model_compare: sign conventions, percentage semantics, DataFrame API
# ----------------------------------------------------------------------
@requires_solver
def test_compare_objective_difference_is_sim_minus_base():
    """The objective delta must use the same direction as the variables.

    Abolishing tariffs raises welfare, so the reported difference must be
    positive. The pre-0.2.1 code computed base - sim here while computing
    sim - base for every variable above it, so a welfare *gain* printed
    as a negative number.
    """
    cge = calibrated()
    with quiet():
        cge.model_sim()
        cge.model_modify_sim('taum', 'BRD', 0)
        cge.model_modify_sim('taum', 'MLK', 0)
        cge.model_solve(SOLVER)

    u_base = value(cge.base.obj)
    u_sim = value(cge.sim.obj)
    assert u_sim > u_base, "precondition: tariff abolition should raise welfare"

    frame = cge.model_compare()
    objective = frame.attrs['objective']
    assert objective['difference'] == pytest.approx(u_sim - u_base, abs=1e-9)
    assert objective['difference'] > 0
    assert objective['base'] == pytest.approx(u_base, abs=1e-9)
    assert objective['sim'] == pytest.approx(u_sim, abs=1e-9)


@requires_solver
def test_compare_reports_percentage_change_not_ratio():
    """Pct change must be (sim - base)/base * 100, not base/sim * 100."""
    cge = calibrated()
    with quiet():
        cge.model_sim()
        cge.model_modify_sim('taum', 'BRD', 0)
        cge.model_solve(SOLVER)

    frame = cge.model_compare()
    pcts = frame['pct_change'].dropna().abs().sort_values()
    assert len(pcts), "no percentage changes reported"

    # A ratio would put unchanged quantities near 100%; a percentage
    # change puts them near 0%. Most variables barely move under a
    # single-good tariff cut, so the median must sit near zero.
    assert pcts.median() < 50, "percentages look like a ratio, not a change"

    # Column-level check: difference must equal sim - base.
    row = frame[(frame['component'] == 'M') & (frame['index_1'] == 'BRD')]
    assert len(row) == 1
    assert row['difference'].iloc[0] == pytest.approx(
        row['sim_value'].iloc[0] - row['base_value'].iloc[0], abs=1e-9)


@requires_solver
def test_compare_returns_dataframe_with_expected_columns():
    cge = calibrated()
    with quiet():
        cge.model_sim()
        cge.model_modify_sim('taum', 'BRD', 0)
        cge.model_solve(SOLVER)

    frame = cge.model_compare()
    for column in ('component', 'index_1', 'index_2', 'base_value',
                   'sim_value', 'difference', 'pct_change'):
        assert column in frame.columns
    # Every active variable element appears exactly once: two-good
    # stdcge has 48 scalar variables.
    assert len(frame) == 48
    assert frame.attrs['solved'] == 'both models solved'


@requires_solver
def test_compare_writes_csv_file(tmp_path):
    cge = calibrated()
    with quiet():
        cge.model_sim()
        cge.model_modify_sim('taum', 'BRD', 0)
        cge.model_solve(SOLVER)
        cge.model_compare(str(tmp_path))

    written = tmp_path / 'compared.csv'
    assert written.exists()
    body = written.read_text()
    assert 'Difference of obj' in body
    assert 'both models solved' in body
    assert 'pct_change' in body


# ----------------------------------------------------------------------
# Export paths: sim export must write sim values
# ----------------------------------------------------------------------
@requires_solver
def test_sim_export_writes_sim_values_not_base(tmp_path):
    """The v0.2.0 critical bug: sim export used getattr(self.base, ...).

    Files labelled as simulation output silently contained base values.
    """
    cge = calibrated()
    with quiet():
        cge.model_sim()
        cge.model_modify_sim('taum', 'BRD', 0)
        cge.model_modify_sim('taum', 'MLK', 0)
        cge.model_solve(SOLVER)
        cge.model_postprocess('vars', str(tmp_path), base=False)

    exported = [
        path for path in tmp_path.iterdir()
        if path.name.startswith("varsM_") and path.suffix == ".csv"
    ]
    assert exported, "no export written for M"

    rows = {}
    for line in exported[0].read_text().splitlines()[1:]:
        if ',' in line:
            k, v = line.split(',', 1)
            rows[k.strip()] = float(v.strip())

    for i in cge.sim.i:
        assert rows[str(i)] == pytest.approx(value(cge.sim.M[i]), abs=1e-6)

    # And it must genuinely differ from base, or the test proves nothing.
    assert any(abs(value(cge.sim.M[i]) - value(cge.base.M[i])) > 1e-6
               for i in cge.sim.i)


@requires_solver
def test_base_export_writes_base_values(tmp_path):
    cge = calibrated()
    with quiet():
        cge.model_postprocess('vars', str(tmp_path), base=True)

    exported = [
        path for path in tmp_path.iterdir()
        if path.name.startswith("varsZ_") and path.suffix == ".csv"
    ]
    assert exported
    rows = {}
    for line in exported[0].read_text().splitlines()[1:]:
        if ',' in line:
            k, v = line.split(',', 1)
            rows[k.strip()] = float(v.strip())
    for i in cge.base.i:
        assert rows[str(i)] == pytest.approx(value(cge.base.Z[i]), abs=1e-6)


@requires_solver
def test_dill_roundtrip_restores_instance(tmp_path):
    cge = calibrated()
    with quiet():
        cge.model_postprocess('dill_instance', str(tmp_path))

    saved = [p for p in tmp_path.iterdir() if '_base_' in p.name]
    assert saved, "no dill instance written"

    fresh = std_instance()
    with quiet():
        fresh.model_load_instance(str(saved[0]))
    assert fresh.numeraire == ('pf', 'LAB')
    for i in fresh.base.i:
        assert value(fresh.base.Z[i]) == pytest.approx(value(cge.base.Z[i]),
                                                       abs=1e-9)


# ----------------------------------------------------------------------
# Shock application and undo
# ----------------------------------------------------------------------
@requires_solver
def test_modify_sim_undo_restores_original_value():
    cge = calibrated()
    with quiet():
        cge.model_sim()
    original = value(cge.sim.taum['BRD'])

    with quiet():
        cge.model_modify_sim('taum', 'BRD', 0)
    assert value(cge.sim.taum['BRD']) == pytest.approx(0.0)

    with quiet():
        cge.model_modify_sim('taum', 'BRD', 0, undo=True)
    assert value(cge.sim.taum['BRD']) == pytest.approx(original)


@requires_solver
def test_modify_sim_clears_solved_flag():
    """A shock after solving must mark the sim as needing a re-solve."""
    cge = calibrated()
    with quiet():
        cge.model_sim()
        cge.model_modify_sim('taum', 'BRD', 0)
        cge.model_solve(SOLVER)
    assert cge.sim_solved is True

    with quiet():
        cge.model_modify_sim('taum', 'MLK', 0)
    assert cge.sim_solved is False


def test_modify_sim_unknown_component_raises_component_error():
    from cge_core.compat.pycge import ComponentError

    cge = std_instance()
    cge.base_calibrated = True      # bypass solve; testing the guard only
    cge.model_sim()
    with pytest.raises(ComponentError, match='does not exist'):
        cge.model_modify_sim('not_a_param', 'BRD', 0)


def test_modify_sim_bad_index_raises_component_error():
    from cge_core.compat.pycge import ComponentError

    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    with pytest.raises(ComponentError, match='not an index'):
        cge.model_modify_sim('taum', 'NOT_A_GOOD', 0)


def test_modify_sim_out_of_bounds_value_raises_value_error():
    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    with pytest.raises(ValueError, match='lower bound'):
        cge.model_modify_sim('pz', 'BRD', -1.0)
    # The failed attempt must not leave a bogus undo entry.
    assert ('pz', 'BRD') not in cge.dict_sim


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
def test_model_data_rejects_missing_directory():
    from cge_core.compat.pycge import DataValidationError, PyCGE
    from cge_core.models.standard.model import StdModelDef

    cge = PyCGE(StdModelDef())
    with pytest.raises(DataValidationError, match='valid data directory'):
        cge.model_data(os.path.join('no', 'such', 'dir'))
    assert cge.data is None


def test_model_data_requires_a_directory_argument():
    from cge_core.compat.pycge import DataValidationError, PyCGE
    from cge_core.models.standard.model import StdModelDef

    cge = PyCGE(StdModelDef())
    with pytest.raises(DataValidationError, match='must be specified'):
        cge.model_data()


# ----------------------------------------------------------------------
# v0.2.2 correctness hardening (contract preserved under v0.3.0 API)
# ----------------------------------------------------------------------
def test_invalid_numeraire_does_not_leave_half_created_base():
    from cge_core.compat.pycge import ComponentError, PyCGE
    from cge_core.models.standard.model import StdModelDef
    from ._util import STD_DATA_DIR

    cge = PyCGE(StdModelDef())
    cge.model_data(STD_DATA_DIR)
    with pytest.raises(ComponentError, match='does not exist'):
        cge.model_instance('pf', 'NOT_A_FACTOR')
    assert cge.base is None


def test_drop_redundant_rejects_entire_indexed_block():
    from cge_core.compat.pycge import ComponentError

    cge = std_instance(drop_redundant=False)
    with pytest.raises(ComponentError, match='indexed'):
        cge.model_drop_redundant('eqpf')
    assert cge.degrees_of_freedom(cge.base) == -1


def test_drop_redundant_rejects_nonconstraint():
    from cge_core.compat.pycge import ComponentError

    cge = std_instance(drop_redundant=False)
    with pytest.raises(ComponentError, match='not a Constraint'):
        cge.model_drop_redundant('pf', 'LAB')


def test_second_redundant_drop_is_rolled_back():
    """Only one equation is redundant; a second drop must roll back.

    The raw system has DOF = -1, so dropping any single equality makes
    it square; dropping a second would leave DOF = +1, and the
    transactional guard must reactivate it.
    """
    from cge_core.compat.pycge import WorkflowError

    cge = std_instance(drop_redundant=False)
    assert cge.model_drop_redundant('eqpf', 'LAB') is True
    with pytest.raises(WorkflowError, match='rolled back'):
        cge.model_drop_redundant('eqpf', 'CAP')
    # The first drop stands; the second was reverted.
    assert cge.degrees_of_freedom(cge.base) == 0


def test_repeated_shock_undo_restores_first_value():
    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    original = value(cge.sim.taum['BRD'])
    cge.model_modify_sim('taum', 'BRD', 0.1)
    cge.model_modify_sim('taum', 'BRD', 0.2)
    cge.model_modify_sim('taum', 'BRD', 0, undo=True)
    assert value(cge.sim.taum['BRD']) == pytest.approx(original)


def test_variable_undo_restores_fixed_status():
    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    item = cge.sim.pz['BRD']
    assert item.fixed is False
    original = value(item)
    cge.model_modify_sim('pz', 'BRD', original * 1.1, fix=True)
    assert item.fixed is True
    cge.model_modify_sim('pz', 'BRD', 0, undo=True)
    assert value(item) == pytest.approx(original)
    assert item.fixed is False


def test_new_simulation_clears_old_shock_history():
    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    cge.model_modify_sim('taum', 'BRD', 0)
    assert cge.dict_sim
    cge.model_sim()
    assert cge.dict_sim == {}


def test_base_change_invalidates_existing_simulation():
    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    cge.model_modify_base('taum', 'BRD', 0)
    assert cge.base_calibrated is False
    assert cge.base_results is None
    assert cge.sim is None


def test_calibration_data_cannot_be_modified_in_place():
    from cge_core.compat.pycge import ComponentError

    cge = std_instance()
    original = value(cge.base.Z0['BRD'])
    with pytest.raises(ComponentError, match='calibration data'):
        cge.model_modify_base('Z0', 'BRD', original + 1)
    assert value(cge.base.Z0['BRD']) == pytest.approx(original)


def test_multidimensional_variable_export_is_valid_csv(tmp_path):
    import csv

    cge = std_instance()
    with quiet():
        cge.model_postprocess('vars', str(tmp_path), base=True)
    exported = list(tmp_path.glob('*F_*.csv'))
    assert exported
    with exported[0].open(newline='') as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ['index_1', 'index_2', 'value']
    assert all(len(row) == 3 for row in rows[1:])


def test_postprocess_params_returns_dict():
    cge = std_instance()
    params = cge.model_postprocess('params')
    assert isinstance(params, dict)
    assert params[('taud', None)] == pytest.approx(23.0 / 90.0)
    assert ('alpha', 'BRD') in params


def test_postprocess_invalid_object_name_raises():
    cge = std_instance()
    with pytest.raises(ValueError, match='not a valid object_name'):
        cge.model_postprocess('not_a_thing', 'print')


def test_unbalanced_sam_is_rejected(tmp_path):
    from cge_core.compat.pycge import DataValidationError, PyCGE

    path = tmp_path / 'param-sam-.csv'
    path.write_text('U,A,B\nA,0,1\nB,0,0\n')
    with pytest.raises(DataValidationError, match='not balanced'):
        PyCGE._validate_sam_csv(path)


def test_failed_calibration_does_not_set_success_flag(monkeypatch):
    from cge_core.compat.pycge import SolveError

    cge = std_instance()

    def fail(*args, **kwargs):
        raise SolveError('infeasible')

    monkeypatch.setattr(cge, '_solve', fail)
    with pytest.raises(SolveError, match='infeasible'):
        cge.model_calibrate('ipopt')
    assert cge.base_calibrated is False
    assert cge.base_results is None


# ----------------------------------------------------------------------
# v0.3.0: logging instead of print
# ----------------------------------------------------------------------
def test_engine_progress_goes_through_logging(caplog):
    """The workflow chatter must arrive on the cge_core logger, and the
    happy path must write nothing to stdout."""
    import contextlib
    import io
    import logging

    buf = io.StringIO()
    with caplog.at_level(logging.INFO, logger='cge_core'):
        with contextlib.redirect_stdout(buf):
            std_instance()
    assert buf.getvalue() == '', "engine wrote to stdout on the happy path"
    messages = ' '.join(record.message for record in caplog.records)
    assert 'numeraire' in messages
    assert 'BASE instance created' in messages


# ----------------------------------------------------------------------
# Final v0.3.0 audit hardening
# ----------------------------------------------------------------------
def test_sam_balance_tolerance_is_account_relative(tmp_path):
    """A huge account must not hide a 100% imbalance in a small account."""
    from cge_core.compat.pycge import DataValidationError, PyCGE

    path = tmp_path / 'param-sam-.csv'
    path.write_text('U,BIG,SMALL\nBIG,1000000000000,0\nSMALL,1,0\n')
    with pytest.raises(DataValidationError, match='SMALL'):
        PyCGE._validate_sam_csv(path)


def test_compare_solved_note_uses_success_flags_not_failed_results():
    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    # Failed solver result objects are intentionally retained for diagnosis.
    cge.base_results = object()
    cge.sim_results = object()
    cge.base_calibrated = False
    cge.sim_solved = False

    frame = cge.model_compare()
    assert frame.attrs['solved'] == 'both models unsolved'


def test_sim_benchmark_only_parameter_is_rejected():
    from cge_core.compat.pycge import ComponentError

    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    original = value(cge.sim.Z0['BRD'])
    with pytest.raises(ComponentError, match='benchmark calibration data'):
        cge.model_modify_sim('Z0', 'BRD', original + 1)
    assert value(cge.sim.Z0['BRD']) == pytest.approx(original)


def test_sim_factor_endowment_remains_a_valid_counterfactual_shock():
    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    original = value(cge.sim.FF['CAP'])
    cge.model_modify_sim('FF', 'CAP', original * 1.05)
    assert value(cge.sim.FF['CAP']) == pytest.approx(original * 1.05)


@pytest.mark.parametrize('bad', ['not-a-number', float('nan'), float('inf'),
                                 float('-inf')])
def test_modify_rejects_nonfinite_or_nonnumeric_values(bad):
    cge = std_instance()
    cge.base_calibrated = True
    cge.model_sim()
    original = value(cge.sim.taum['BRD'])

    with pytest.raises(ValueError, match='finite numeric'):
        cge.model_modify_sim('taum', 'BRD', bad)
    assert value(cge.sim.taum['BRD']) == pytest.approx(original)
    assert ('taum', 'BRD') not in cge.dict_sim


def test_failed_modification_rolls_back_value_fixed_state_and_history(monkeypatch):
    import cge_core.engine as engine
    from cge_core.compat.pycge import PyCGE
    from pyomo.environ import Var

    class FakeItem:
        def __init__(self):
            self.value = 1.0
            self.fixed = False
            self.lb = 0.0
            self.ub = 10.0

        def set_value(self, new):
            self.value = new

        def fix(self):
            if self.value == 2.0:
                raise RuntimeError('synthetic fix failure')
            self.fixed = True

        def unfix(self):
            self.fixed = False

    class FakeComponent:
        ctype = Var
        mutable = False

        def __init__(self, item):
            self.item = item

        def is_indexed(self):
            return True

        def __getitem__(self, index):
            if index != 'A':
                raise KeyError(index)
            return self.item

    class FakeInstance:
        def __init__(self, component):
            self._component = component

        def component(self, name):
            return self._component if name == 'x' else None

    item = FakeItem()
    cge = object.__new__(PyCGE)
    cge.base = FakeInstance(FakeComponent(item))
    cge.sim = None
    cge.base_results = None
    cge.sim_results = None
    cge.base_calibrated = False
    cge.sim_solved = False
    cge.dict_base = {}
    cge.dict_sim = {}
    cge.numeraire = None
    monkeypatch.setattr(
        engine, 'value',
        lambda obj, exception=False: obj.value if hasattr(obj, 'value') else obj,
    )

    with pytest.raises(RuntimeError, match='synthetic fix failure'):
        cge.model_modify_base('x', 'A', 2.0, fix=True)
    assert item.value == pytest.approx(1.0)
    assert item.fixed is False
    assert cge.dict_base == {}


def test_drop_redundant_rejects_nonmarket_equation_even_if_square():
    from cge_core.compat.pycge import ComponentError

    cge = std_instance(drop_redundant=False)
    with pytest.raises(ComponentError, match='Walras-law candidate'):
        cge.model_drop_redundant('eqpy', 'BRD')
    assert cge.base.eqpy['BRD'].active
    assert cge.degrees_of_freedom(cge.base) == -1


def test_successful_structural_drop_invalidates_stale_solution_state():
    cge = std_instance(drop_redundant=False)
    cge.base_results = object()
    cge.base_calibrated = True

    cge.model_drop_redundant('eqpf', 'LAB')
    assert cge.base_results is None
    assert cge.base_calibrated is False
    assert cge.sim is None


@pytest.mark.parametrize('target', ['base', 'sim'])
def test_numeraire_cannot_be_unfixed_through_modify_api(target):
    from cge_core.compat.pycge import ComponentError

    cge = std_instance()
    if target == 'sim':
        cge.base_calibrated = True
        cge.model_sim()
        modify = cge.model_modify_sim
    else:
        modify = cge.model_modify_base

    with pytest.raises(ComponentError, match='numeraire'):
        modify('pf', 'LAB', 1.0, fix=False)


def test_solver_execution_exception_is_wrapped_as_solve_error(monkeypatch):
    import cge_core.engine as engine
    from cge_core.compat.pycge import SolveError

    class BrokenSolver:
        def available(self, exception_flag=False):
            return True

        def solve(self, instance):
            raise RuntimeError('synthetic solver crash')

    monkeypatch.setattr(engine, 'SolverFactory', lambda name: BrokenSolver())
    cge = std_instance()
    with pytest.raises(SolveError, match='Solver execution failed'):
        cge.model_calibrate('broken')
    assert cge.base_results is None
    assert cge.base_calibrated is False


def test_bundled_models_require_complete_data_directory(tmp_path):
    from cge_core.compat.pycge import DataValidationError, PyCGE
    from cge_core.models.standard.model import StdModelDef

    (tmp_path / 'set-i-.csv').write_text('i\nBRD\n')
    with pytest.raises(DataValidationError, match='missing required files'):
        PyCGE(StdModelDef()).model_data(tmp_path)


def test_quantity_variable_cannot_be_chosen_as_numeraire():
    from cge_core.compat.pycge import ComponentError, PyCGE
    from cge_core.models.standard.model import StdModelDef
    from ._util import STD_DATA_DIR

    cge = PyCGE(StdModelDef())
    cge.model_data(STD_DATA_DIR)
    with pytest.raises(ComponentError, match='price numeraire'):
        cge.model_instance('Z', 'BRD')
    assert cge.base is None


def test_dataset_sets_must_match_and_partition_sam_accounts(tmp_path):
    import shutil

    from cge_core.compat.pycge import DataValidationError, PyCGE
    from cge_core.models.standard.model import StdModelDef
    from ._util import STD_DATA_DIR

    data_dir = tmp_path / 'data'
    shutil.copytree(STD_DATA_DIR, data_dir)
    # Misclassify CAP as both a good and a factor.
    with (data_dir / 'set-i-.csv').open('a', encoding='utf-8') as handle:
        handle.write('\nCAP\n')
    with pytest.raises(DataValidationError, match='overlap'):
        PyCGE(StdModelDef()).model_data(data_dir)


def test_configured_institution_must_exist_in_sam(tmp_path):
    import shutil

    from cge_core.compat.pycge import DataValidationError, PyCGE
    from cge_core.models.standard.model import StdModelDef
    from ._util import STD_DATA_DIR

    data_dir = tmp_path / 'data'
    shutil.copytree(STD_DATA_DIR, data_dir)
    with pytest.raises(DataValidationError, match='Configured institutional'):
        PyCGE(StdModelDef(accounts={'hoh': 'HH'})).model_data(data_dir)


def test_unknown_component_data_file_is_rejected(tmp_path):
    import shutil

    from cge_core.compat.pycge import DataValidationError, PyCGE
    from cge_core.models.standard.model import StdModelDef
    from ._util import STD_DATA_DIR

    data_dir = tmp_path / 'data'
    shutil.copytree(STD_DATA_DIR, data_dir)
    (data_dir / 'param-typo-.csv').write_text('U,BRD\nBRD,1\n')
    with pytest.raises(DataValidationError, match='unknown or wrong-type'):
        PyCGE(StdModelDef()).model_data(data_dir)
