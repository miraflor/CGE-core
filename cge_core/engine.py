r"""Core workflow for calibrating and simulating Pyomo CGE models.

This module is the CGE analogue of OG-Core's ``SS.py``/``execute.py``: it
holds no economics of its own. The model algebra lives in the model
definition classes (see ``cge_core/examples/*_model_def.py`` and
``docs/OG_CORE_CROSSWALK.md``); this engine loads data, imposes the closure
(numeraire + Walras'-law equation drop), solves the baseline, applies
reforms, solves counterfactuals, and compares.

Error and reporting contract (v0.3.0):
    * Misuse raises exceptions -- :class:`WorkflowError` for out-of-order
      calls, :class:`ComponentError` for unknown/ineligible components,
      :class:`DataValidationError` for bad input data, and
      :class:`SolveError` for solver failures -- rather than printing and
      returning ``None``.
    * Progress is reported through the standard :mod:`logging` module on
      the ``cge_core.engine`` logger. Scripts that want the classic
      chatter should call ``logging.basicConfig(level=logging.INFO)``
      (the bundled examples do). Only explicitly requested displays
      (``model_compare('print')``, ``model_postprocess(..., 'print')``)
      write to stdout.
    * :meth:`PyCGE.model_compare` returns a pandas DataFrame.

Provenance: fork of PyCGE (Fung & Burtwistle, NIST 2017, public domain);
fork revisions by James Matthew Miraflor (2026) via an AI-assisted
workflow directed and reviewed by him. The original engine
design is not his work. See README.md and CITATION.cff.
"""
from __future__ import annotations

import copy
import csv
import importlib.util
import logging
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import dill
import pandas as pd
from pyomo.environ import (
    Constraint,
    DataPortal,
    Param,
    SolverFactory,
    SolverManagerFactory,
    Set,
    Var,
    value,
)
from pyomo.opt import check_optimal_termination

logger = logging.getLogger(__name__)


class CGEError(RuntimeError):
    """Base exception for CGE-Core workflow errors."""


class WorkflowError(CGEError):
    """Raised when workflow methods are called out of order.

    The message always names the method to call first (e.g. "Call
    ``model_calibrate`` first"), preserving the guidance that earlier
    versions printed.
    """


class ComponentError(CGEError):
    """Raised when a named model component cannot be used as requested.

    Covers unknown component names, invalid indexes, immutable
    parameters, protected calibration inputs, and undo requests with no
    stored original value.
    """


class DataValidationError(CGEError, ValueError):
    """Raised when model input data fail structural validation."""


class SolveError(CGEError):
    """Raised when a solver does not return an acceptable optimum."""

    def __init__(self, message: str, results=None):
        super().__init__(message)
        self.results = results


def _component_key(name: str, index: Any) -> Tuple[str, Any]:
    """Return an unambiguous key for modification history."""
    try:
        hash(index)
        safe_index = index
    except TypeError:
        safe_index = repr(index)
    return name, safe_index


def _normalise_index(index: Any) -> Tuple[Any, ...]:
    if index is None:
        return ()
    if isinstance(index, tuple):
        return index
    return (index,)


class PyCGE:
    r"""Pyomo-based CGE calibration and counterfactual workflow.

    Orchestrates the sequence (cf. OG-Core's ``run_SS`` pipeline)::

        model_data -> model_instance -> model_drop_redundant
            -> model_calibrate -> model_sim -> model_modify_sim
            -> model_solve -> model_compare / model_postprocess

    Args:
        model_def (object): model-definition object exposing ``model()``
            that returns a Pyomo AbstractModel (e.g. ``StdModelDef``).

    Attributes:
        base (ConcreteModel or None): the baseline instance; after
            ``model_calibrate`` it reproduces the SAM benchmark.
        sim (ConcreteModel or None): the counterfactual instance, cloned
            from the calibrated baseline by ``model_sim``.
        dict_base, dict_sim (dict): reversible-modification history for
            ``model_modify_base`` / ``model_modify_sim`` undo support.
    """

    def __init__(self, model_def):
        self.m = model_def.model()
        candidates = getattr(model_def, "redundant_constraints", None)
        self.redundant_constraints = (
            frozenset(candidates) if candidates is not None else None
        )
        required_files = getattr(model_def, "required_data_files", None)
        self.required_data_files = (
            frozenset(required_files) if required_files is not None else None
        )
        numeraires = getattr(model_def, "numeraire_variables", None)
        self.numeraire_variables = (
            frozenset(numeraires) if numeraires is not None else None
        )
        accounts = getattr(model_def, "accounts", None)
        self.institutional_accounts = (
            frozenset(accounts.values()) if accounts is not None else None
        )
        self.data = None
        self.data_dir: Optional[Path] = None
        self.base = None
        self.sim = None
        self.base_results = None
        self.sim_results = None
        self.base_calibrated = False
        self.sim_solved = False
        self.dict_base: Dict[Tuple[str, Any], Dict[str, Any]] = {}
        self.dict_sim: Dict[Tuple[str, Any], Dict[str, Any]] = {}
        self.numeraire: Optional[Tuple[str, Any]] = None

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def _invalidate_sim(self) -> None:
        self.sim = None
        self.sim_results = None
        self.sim_solved = False
        self.dict_sim = {}

    def _invalidate_base_solution(self) -> None:
        self.base_results = None
        self.base_calibrated = False
        self._invalidate_sim()

    @staticmethod
    def degrees_of_freedom(instance) -> int:
        """Return free variables minus active equality constraints."""
        free_vars = sum(
            1
            for item in instance.component_data_objects(Var, active=True)
            if not item.fixed
        )
        equalities = sum(
            1
            for item in instance.component_data_objects(Constraint, active=True)
            if item.equality
        )
        return free_vars - equalities

    # ------------------------------------------------------------------
    # Data loading and validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_sam_csv(path: Path, tolerance: float = 1e-8):
        """Validate a square, finite, balanced SAM and return its labels."""
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                rows = [row for row in csv.reader(handle)
                        if any(cell.strip() for cell in row)]
        except OSError as exc:
            raise DataValidationError(f"Could not read SAM file: {path}") from exc

        if len(rows) < 2 or len(rows[0]) < 2:
            raise DataValidationError(f"SAM file is empty or malformed: {path}")

        columns = [cell.strip() for cell in rows[0][1:]]
        row_names = [row[0].strip() for row in rows[1:]]
        if not all(columns) or not all(row_names):
            raise DataValidationError("SAM account labels cannot be empty.")
        if len(set(columns)) != len(columns) or len(set(row_names)) != len(row_names):
            raise DataValidationError("SAM row and column labels must be unique.")
        if set(row_names) != set(columns):
            raise DataValidationError(
                "SAM must be square with the same account labels on rows and columns."
            )
        if any(len(row) != len(columns) + 1 for row in rows[1:]):
            raise DataValidationError("Every SAM row must have the same number of cells.")

        matrix = []
        for row_name, row in zip(row_names, rows[1:]):
            numeric_row = []
            for column_name, cell in zip(columns, row[1:]):
                try:
                    number = float(cell)
                except ValueError as exc:
                    raise DataValidationError(
                        f"SAM[{row_name},{column_name}] is not numeric: {cell!r}"
                    ) from exc
                if not math.isfinite(number):
                    raise DataValidationError(
                        f"SAM[{row_name},{column_name}] is not finite."
                    )
                numeric_row.append(number)
            matrix.append(numeric_row)

        row_totals = {name: sum(row) for name, row in zip(row_names, matrix)}
        column_totals = {
            name: sum(matrix[r][c] for r in range(len(matrix)))
            for c, name in enumerate(columns)
        }
        imbalances = {
            name: row_totals[name] - column_totals[name] for name in row_names
        }
        relative_imbalances = {
            name: abs(imbalances[name])
            / max(1.0, abs(row_totals[name]), abs(column_totals[name]))
            for name in row_names
        }
        worst = max(relative_imbalances, key=relative_imbalances.get)
        if relative_imbalances[worst] > tolerance:
            raise DataValidationError(
                "SAM is not balanced: account "
                f"{worst!r} has row minus column total "
                f"{imbalances[worst]:.12g} (relative imbalance "
                f"{relative_imbalances[worst]:.12g})."
            )
        return frozenset(row_names)

    @staticmethod
    def _read_set_csv(path: Path, expected_name: str):
        """Read a one-column Pyomo set CSV with precise validation errors."""
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                rows = [row for row in csv.reader(handle)
                        if any(cell.strip() for cell in row)]
        except OSError as exc:
            raise DataValidationError(f"Could not read set file: {path}") from exc
        if not rows:
            raise DataValidationError(f"Set file is empty: {path}")
        header = rows[0][0].strip() if rows[0] else ""
        if header.lower() != expected_name.lower() or any(
                cell.strip() for cell in rows[0][1:]):
            raise DataValidationError(
                f"Set file {path.name!r} must have a one-cell header "
                f"named {expected_name!r}."
            )
        members = []
        for row_number, row in enumerate(rows[1:], start=2):
            if not row or not row[0].strip() or any(
                    cell.strip() for cell in row[1:]):
                raise DataValidationError(
                    f"Set file {path.name!r}, row {row_number}, must contain "
                    "exactly one non-empty label."
                )
            members.append(row[0].strip())
        if not members:
            raise DataValidationError(f"Set {expected_name!r} cannot be empty.")
        if len(set(members)) != len(members):
            raise DataValidationError(
                f"Set {expected_name!r} contains duplicate labels."
            )
        return members

    def _validate_standard_dataset_structure(self, directory: Path,
                                             sam_labels) -> None:
        """Validate the bundled models' goods/factor/account partition."""
        if self.required_data_files is None and self.institutional_accounts is None:
            return
        paths = {
            name: directory / f"set-{name}-.csv" for name in ("i", "h", "u")
        }
        if not all(path.is_file() for path in paths.values()):
            return
        goods = set(self._read_set_csv(paths["i"], "i"))
        factors = set(self._read_set_csv(paths["h"], "h"))
        accounts = set(self._read_set_csv(paths["u"], "u"))
        if sam_labels is not None and accounts != set(sam_labels):
            missing = sorted(set(sam_labels) - accounts)
            extra = sorted(accounts - set(sam_labels))
            raise DataValidationError(
                "set-u-.csv must contain exactly the SAM account labels; "
                f"missing={missing}, extra={extra}."
            )
        overlap = goods & factors
        if overlap:
            raise DataValidationError(
                f"Goods and factor sets overlap: {sorted(overlap)}."
            )
        if not goods <= accounts or not factors <= accounts:
            outside = sorted((goods | factors) - accounts)
            raise DataValidationError(
                f"Goods/factor labels missing from set u: {outside}."
            )
        if self.institutional_accounts is not None:
            institutions = set(self.institutional_accounts)
            missing = sorted(institutions - accounts)
            if missing:
                raise DataValidationError(
                    "Configured institutional accounts are missing from the "
                    f"SAM/set u: {missing}."
                )
            overlap = (goods | factors) & institutions
            if overlap:
                raise DataValidationError(
                    "Institutional accounts cannot also be goods or factors: "
                    f"{sorted(overlap)}."
                )
            classified = goods | factors | institutions
            if classified != accounts:
                unclassified = sorted(accounts - classified)
                missing_from_u = sorted(classified - accounts)
                raise DataValidationError(
                    "Goods, factors, and configured institutions must "
                    "partition set u; "
                    f"unclassified={unclassified}, missing={missing_from_u}."
                )

    def model_data(self, data_dir: Union[os.PathLike, str] = ""):
        r"""Load ``set-*.csv`` and ``param-*.csv`` files into a DataPortal.

        A file named ``param-sam-.csv`` (the social accounting matrix) is
        structurally validated first: square, unique labels, finite numeric
        cells, and row/column totals balanced to tolerance. An unbalanced
        SAM cannot be reproduced by any equilibrium, so it is rejected
        before Pyomo ever sees it.

        Args:
            data_dir (str or PathLike): directory containing the CSVs,
                e.g. from :func:`cge_core.example_data` or built by
                :func:`cge_core.samtools.build_dataset`.

        Returns:
            data (pyomo DataPortal): the loaded data.

        Raises:
            DataValidationError: if ``data_dir`` is missing/invalid or
                the SAM fails validation.
        """
        if not data_dir:
            raise DataValidationError(
                "A data directory must be specified, e.g. "
                "model_data(example_data('stdcge'))."
            )

        directory = Path(data_dir).expanduser().resolve()
        if not directory.is_dir():
            raise DataValidationError(
                f"'{data_dir}' is not a valid data directory."
            )

        if self.required_data_files is not None:
            missing = sorted(
                name for name in self.required_data_files
                if not (directory / name).is_file()
            )
            if missing:
                raise DataValidationError(
                    "Data directory is missing required files: "
                    + ", ".join(missing)
                )

        sam_path = directory / "param-sam-.csv"
        sam_labels = None
        if sam_path.exists():
            sam_labels = self._validate_sam_csv(sam_path)
        self._validate_standard_dataset_structure(directory, sam_labels)

        data = DataPortal()
        loaded_components = set()
        for path in sorted(directory.iterdir()):
            if not path.is_file():
                continue
            parts = path.name.split("-")
            if len(parts) != 3 or path.suffix.lower() != ".csv":
                logger.warning(
                    "%s is not in the right format and was not loaded "
                    "into DataPortal", path.name)
                continue
            dat_type, name, _ = parts
            component = self.m.component(name)
            expected_ctype = Set if dat_type == "set" else Param
            if dat_type not in {"set", "param"}:
                logger.warning(
                    "%s is not in the right format and was not loaded "
                    "into DataPortal", path.name)
                continue
            if component is None or component.ctype is not expected_ctype:
                raise DataValidationError(
                    f"Data file {path.name!r} targets unknown or wrong-type "
                    f"model component {name!r}."
                )
            key = (dat_type, name)
            if key in loaded_components:
                raise DataValidationError(
                    f"Multiple data files target {dat_type} {name!r}."
                )
            loaded_components.add(key)
            if dat_type == "set":
                data.load(filename=str(path), format="set", set=name)
                logger.info("File '%s' was loaded into set: %s",
                            path.name, name)
            elif dat_type == "param":
                data.load(filename=str(path), param=name, format="array")
                logger.info("File '%s' was loaded into param: %s",
                            path.name, name)

        self.data = data
        self.data_dir = directory
        self.base = None
        self.numeraire = None
        self.dict_base = {}
        self._invalidate_base_solution()
        return data

    # ------------------------------------------------------------------
    # Instance construction and closure
    # ------------------------------------------------------------------
    def model_instance(self, NAME, INDEX):
        r"""Create the BASE concrete instance and fix the numeraire.

        A CGE determines only relative prices, so exactly one price must
        be fixed as numeraire (Hosoe: ``pf.fx("LAB") = 1``). This method
        builds the concrete instance from the loaded data and fixes
        variable ``NAME[INDEX]`` at its initialized value (1 for prices).

        Args:
            NAME (str): name of the variable to fix, e.g. ``'pf'``.
            INDEX: index of that variable, e.g. ``'LAB'``.

        Returns:
            instance (ConcreteModel): the new BASE instance.

        Raises:
            WorkflowError: if the model or data are not loaded.
            ComponentError: if ``NAME`` is not a variable or ``INDEX``
                is not one of its indexes. The half-created instance is
                discarded, so ``self.base`` stays unchanged.
            DataValidationError: if model-specific calibration cannot be
                constructed from the supplied benchmark flows.
        """
        if self.m is None:
            raise WorkflowError("Model not loaded.")
        if self.data is None:
            raise WorkflowError("Data not loaded. Call `model_data` first.")

        try:
            candidate = self.m.create_instance(self.data)
        except ZeroDivisionError as exc:
            raise DataValidationError(
                "Model instance construction failed with division by zero. "
                "This commonly indicates a zero benchmark flow that violates "
                "the model's calibration assumptions, but it can also indicate "
                "a defect in a custom model definition; inspect both the input "
                "data and the model-specific initializer."
            ) from exc
        component = candidate.component(NAME)
        if component is None or component.ctype is not Var:
            raise ComponentError(
                f"Variable '{NAME}' does not exist in the model.")
        if (self.numeraire_variables is not None
                and NAME not in self.numeraire_variables):
            allowed = ", ".join(sorted(self.numeraire_variables))
            raise ComponentError(
                f"Variable '{NAME}' is not a supported price numeraire for "
                f"this model. Use one of: {allowed}.")
        try:
            var_data = component[INDEX]
        except (KeyError, TypeError):
            raise ComponentError(
                f"Index '{INDEX}' does not exist for variable '{NAME}'.")

        var_data.fix()
        self.base = candidate
        self.numeraire = _component_key(NAME, INDEX)
        self.base_results = None
        self.base_calibrated = False
        self.dict_base = {}
        self._invalidate_sim()
        logger.info("Note, %s[%s] is now fixed as numeraire.", NAME, INDEX)
        logger.info(
            "BASE instance created. (This can be modified by calling "
            "`model_modify_base`.) Call `model_postprocess` to output or "
            "`model_calibrate` to solve.")
        return candidate

    def model_drop_redundant(self, name, index=None, base=True):
        r"""Deactivate exactly one redundant equality constraint.

        By Walras' law, once the numeraire is fixed the system carries one
        redundant market-clearing equation; IPOPT rejects the resulting
        over-determined system ("too few degrees of freedom"). Dropping any
        single market-clearing equation restores a square system, and the
        dropped market still clears at the solution (asserted in the test
        suite). See docs/MODEL.md, "Closure and degrees of freedom".

        The operation is transactional: the selected equation is
        reactivated unless deactivation leaves the model with exactly
        zero degrees of freedom.

        Args:
            name (str): constraint name, e.g. ``'eqpf'``.
            index: index of the constraint instance to drop (required for
                indexed constraints), e.g. ``'LAB'``.
            base (bool): operate on the BASE (True) or SIM (False) instance.

        Returns:
            success (bool): True; the system is now square.

        Raises:
            WorkflowError: if the target instance does not exist, the
                equation is already inactive, or deactivation would not
                leave exactly zero degrees of freedom (rolled back).
            ComponentError: if ``name`` is unknown, is not an equality
                Constraint, or ``index`` is missing/invalid.
        """
        instance = self.base if base else self.sim
        target = "BASE" if base else "SIM"
        if instance is None:
            raise WorkflowError(
                f"You must create the {target} instance first.")

        component = instance.component(name)
        if component is None:
            raise ComponentError(
                f"Constraint '{name}' does not exist on the {target} "
                "instance.")
        if component.ctype is not Constraint:
            raise ComponentError(f"Component '{name}' is not a Constraint.")
        if component.is_indexed() and index is None:
            raise ComponentError(
                f"Constraint '{name}' is indexed; specify exactly one index "
                "instead of deactivating the whole block.")

        try:
            item = component if not component.is_indexed() else component[index]
        except (KeyError, TypeError):
            raise ComponentError(
                f"Index '{index}' does not exist for constraint '{name}'.")
        if not item.equality:
            raise ComponentError(
                f"Constraint '{name}' is not an equality and cannot be the "
                "Walras equation.")
        if (self.redundant_constraints is not None
                and name not in self.redundant_constraints):
            allowed = ", ".join(sorted(self.redundant_constraints))
            raise ComponentError(
                f"Constraint '{name}' is not a supported Walras-law "
                f"candidate for this model. Use one of: {allowed}.")
        if not item.active:
            raise WorkflowError(f"Constraint '{name}' is already inactive.")

        item.deactivate()
        try:
            dof = self.degrees_of_freedom(instance)
        except Exception:
            item.activate()
            raise
        if dof != 0:
            item.activate()
            raise WorkflowError(
                f"Deactivating '{name}' would leave degrees of freedom = "
                f"{dof}; the change was rolled back.")

        label = name if not component.is_indexed() else f"{name}[{index}]"
        logger.info("Deactivated constraint '%s' on %s (Walras' law "
                    "redundancy).", label, target)
        logger.info("System is square (degrees of freedom = 0).")
        if base:
            self._invalidate_base_solution()
        else:
            self.sim_results = None
            self.sim_solved = False
        return True

    # ------------------------------------------------------------------
    # Scenario state and reversible modifications
    # ------------------------------------------------------------------
    def model_sim(self):
        r"""Clone the calibrated BASE into a SIM (counterfactual) instance.

        The clone is a deep copy, so shocks applied to SIM can never leak
        into the calibrated baseline. The OG-Core analogue is constructing
        the reform ``Specifications`` from the baseline before ``run_SS``.

        Returns:
            sim (ConcreteModel): the new SIM instance.

        Raises:
            WorkflowError: if the BASE instance is missing or not yet
                calibrated.
        """
        if self.base is None:
            raise WorkflowError("You must create the BASE instance first.")
        if not self.base_calibrated:
            raise WorkflowError(
                "You must calibrate first. Call `model_calibrate`.")
        self.sim = copy.deepcopy(self.base)
        self.sim_results = None
        self.sim_solved = False
        self.dict_sim = {}
        logger.info(
            "SIM instance created. Note, this is currently the same as "
            "BASE. Call `model_modify_sim` to modify.")
        return self.sim

    @staticmethod
    def _data_item(component, index):
        if component.is_indexed():
            return component[index]
        if index not in (None, ""):
            raise KeyError(index)
        return component

    def _modify(self, *, base: bool, name, index, new_value, fix=True, undo=False):
        instance = self.base if base else self.sim
        history = self.dict_base if base else self.dict_sim
        label = "BASE" if base else "SIM"
        if instance is None:
            first = ("base instance. Call `model_instance` first." if base
                     else "sim instance. Call `model_sim` first.")
            raise WorkflowError("Must first create " + first)

        component = instance.component(name)
        if component is None:
            raise ComponentError(
                f"'{name}' does not exist in the current instance.")
        if component.ctype not in (Var, Param):
            raise ComponentError(
                f"'{name}' is not a variable or mutable parameter.")
        if component.ctype is Param and not component.mutable:
            raise ComponentError(
                f"'{name}' is immutable and cannot be modified.")

        try:
            item = self._data_item(component, index)
        except (KeyError, TypeError):
            raise ComponentError(f"'{index}' is not an index of '{name}'.")

        # The SAM and *0 magnitudes are benchmark-only inputs: changing them
        # after construction either leaves derived calibration parameters
        # stale (BASE) or silently has no effect on the behavioural equations
        # (SIM). Factor endowments are protected only on BASE; they are a
        # legitimate counterfactual shock on SIM.
        if name == "sam" or name.endswith("0") or (base and name == "FF"):
            scope = "BASE" if base else "SIM"
            raise ComponentError(
                f"{scope} component '{name}' is benchmark calibration data "
                "and cannot be modified in-place. Change the input CSV and "
                "rebuild the instance instead.")

        key = _component_key(name, index)
        if undo:
            original = history.get(key)
            if original is None:
                raise ComponentError(
                    f"No stored original value for {name}[{index}].")
            prior_value = value(item, exception=False)
            prior_fixed = (
                bool(item.fixed) if component.ctype is Var else None
            )
            try:
                item.set_value(original["value"])
                if component.ctype is Var:
                    if original["fixed"]:
                        item.fix()
                    else:
                        item.unfix()
            except Exception:
                try:
                    item.set_value(prior_value)
                    if component.ctype is Var:
                        item.fix() if prior_fixed else item.unfix()
                except Exception:
                    logger.exception(
                        "Failed to roll back undo for %s[%s].", name, index
                    )
                raise
            del history[key]
            logger.info("%s is restored to %s", item, item.value)
        else:
            if component.ctype is Var and not fix and key == self.numeraire:
                raise ComponentError(
                    f"{name}[{index}] is the numeraire and cannot be unfixed. "
                    "Create a new instance to choose a different numeraire.")
            try:
                numeric = float(new_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"VALUE for {name}[{index}] must be a finite numeric "
                    "scalar.") from exc
            if not math.isfinite(numeric):
                raise ValueError(
                    f"VALUE for {name}[{index}] must be a finite numeric "
                    "scalar.")

            prior_value = value(item, exception=False)
            prior_fixed = (
                bool(item.fixed) if component.ctype is Var else None
            )
            added_history = key not in history
            try:
                if component.ctype is Var:
                    lb = value(item.lb, exception=False)
                    ub = value(item.ub, exception=False)
                    if lb is not None and numeric < lb:
                        raise ValueError(
                            f"value {numeric} is below lower bound {lb}")
                    if ub is not None and numeric > ub:
                        raise ValueError(
                            f"value {numeric} is above upper bound {ub}")
                if added_history:
                    history[key] = {
                        "value": prior_value,
                        "fixed": prior_fixed,
                    }
                item.set_value(numeric)
                if component.ctype is Var:
                    item.fix() if fix else item.unfix()
            except Exception:
                try:
                    item.set_value(prior_value)
                    if component.ctype is Var:
                        item.fix() if prior_fixed else item.unfix()
                except Exception:
                    logger.exception(
                        "Failed to roll back %s[%s] after a rejected "
                        "modification.", name, index
                    )
                if added_history:
                    history.pop(key, None)
                raise
            logger.info("%s is now set to %s", item, item.value)
            if component.ctype is Var:
                logger.info("Note, %s is now %s", item,
                            "fixed" if item.fixed else "NOT fixed")

        if base:
            self._invalidate_base_solution()
        else:
            self.sim_results = None
            self.sim_solved = False
        logger.info("%s updated.", label)
        return True

    def model_modify_sim(self, NAME, INDEX, VALUE, fix=True, undo=False):
        r"""Apply (or undo) a reform shock on the SIM instance.

        This is CGE-Core's reform interface (cf. OG-Core reform dicts):
        e.g. ``model_modify_sim('taum', 'BRD', 0)`` abolishes the tariff
        on BRD. Original values and fixed-status are recorded so the shock
        can be reversed with ``undo=True``. Benchmark-only ``sam``/``*0``
        components are rejected because changing them after calibration is a
        silent no-op; factor endowments (``FF``) remain valid SIM shocks.

        Args:
            NAME (str): variable or mutable parameter to change.
            INDEX: index of the component (None/'' for scalars).
            VALUE: finite numeric scalar; for variables, checked against
                bounds.
            fix (bool): if a variable, fix it at VALUE (an exogenous
                shock) rather than leaving it free.
            undo (bool): restore the stored original value instead.

        Returns:
            success (bool): True if the modification was applied.

        Raises:
            WorkflowError: if the SIM instance does not exist yet.
            ComponentError: for unknown components/indexes, immutable
                parameters, or undo with no stored original.
            ValueError: if VALUE is nonnumeric/nonfinite or violates a
                variable's bounds.
        """
        result = self._modify(
            base=False, name=NAME, index=INDEX, new_value=VALUE,
            fix=fix, undo=undo,
        )
        if result:
            logger.info("Call `model_postprocess` to output or "
                        "`model_solve` to solve.")
        return result

    def model_modify_base(self, NAME, INDEX, VALUE, fix=True, undo=False):
        r"""Apply (or undo) a modification on the BASE instance.

        Benchmark calibration inputs (``sam``, ``FF``, and ``*0``
        parameters) are refused here, because the calibrated share/scale
        parameters derived from them would silently go stale; change the
        input CSVs and rebuild instead. Signature as in
        :meth:`model_modify_sim`.

        Returns:
            success (bool): True if the modification was applied.

        Raises:
            WorkflowError, ComponentError, ValueError: as in
                :meth:`model_modify_sim`; additionally ComponentError
                when targeting protected calibration data.
        """
        result = self._modify(
            base=True, name=NAME, index=INDEX, new_value=VALUE,
            fix=fix, undo=undo,
        )
        if result:
            logger.info("Call `model_postprocess` to output or "
                        "`model_calibrate` to solve.")
        return result

    # ------------------------------------------------------------------
    # Solving
    # ------------------------------------------------------------------
    @staticmethod
    def _available_solver(preferred: Optional[str] = None) -> str:
        candidates = [preferred] if preferred else ["ipopt", "cyipopt"]
        for name in candidates:
            if not name:
                continue
            try:
                if not SolverFactory(name).available(exception_flag=False):
                    continue
                if name == "cyipopt":
                    # Pyomo's cyipopt route imports SciPy at runtime and
                    # requires the PyNumero ASL bridge. SolverFactory can
                    # report cyipopt as available even when either piece is
                    # missing, so probe both before selecting it.
                    if importlib.util.find_spec("scipy") is None:
                        continue
                    from pyomo.contrib.pynumero.asl import AmplInterface

                    if not AmplInterface.available():
                        continue
                return name
            except Exception:
                continue
        requested = preferred or "ipopt/cyipopt"
        raise SolveError(f"No available local solver found ({requested}).")

    def _solve(self, instance, solver=None, mgr=""):
        try:
            if mgr:
                if not solver:
                    raise SolveError(
                        "A solver name is required with a remote solver manager.")
                logger.info("solver %s used through %s", solver, mgr)
                with SolverManagerFactory(mgr) as solver_mgr:
                    results = solver_mgr.solve(instance, opt=solver)
            else:
                solver_name = self._available_solver(solver)
                logger.info("local solver %s used", solver_name)
                results = SolverFactory(solver_name).solve(instance)

            if not check_optimal_termination(results):
                status = getattr(results.solver, "status", "unknown")
                termination = getattr(
                    results.solver, "termination_condition", "unknown"
                )
                raise SolveError(
                    "Solver did not reach an acceptable optimum: "
                    f"status={status}, termination={termination}.",
                    results=results,
                )
            instance.solutions.store_to(results)
            return results
        except SolveError:
            raise
        except Exception as exc:
            raise SolveError(f"Solver execution failed: {exc}") from exc

    def model_calibrate(self, solver=None, mgr=""):
        r"""Solve the BASE instance (the calibration check).

        Because every behavioural parameter is recovered from the SAM,
        the solved baseline must reproduce the SAM benchmark exactly at
        unit prices; this solve verifies it (cf. OG-Core solving the
        baseline steady state before a reform).

        Args:
            solver (str, optional): local solver name; auto-detects
                ipopt/cyipopt if omitted.
            mgr (str, optional): Pyomo solver-manager name for remote
                solving (e.g. ``'neos'``); requires ``solver``.

        Returns:
            results (SolverResults): solver results. If the model is
                already calibrated, the cached results are returned.

        Raises:
            WorkflowError: if the BASE instance does not exist.
            SolveError: if the solver does not reach an acceptable
                optimum. The failed results are attached to the
                exception; solved-state flags are left unset.
        """
        if self.base is None:
            raise WorkflowError(
                "You must create the BASE instance before you can solve "
                "it. Call `model_instance` first.")
        if self.base_calibrated:
            logger.info("Model already calibrated. If a SIM has been "
                        "created, call `model_solve` to solve it.")
            return self.base_results

        self.base_calibrated = False
        try:
            results = self._solve(self.base, solver=solver, mgr=mgr)
        except SolveError as exc:
            self.base_results = exc.results
            logger.error(str(exc))
            raise
        self.base_results = results
        self.base_calibrated = True
        logger.info("Base model solved. Call `model_postprocess` to output.")
        logger.info("Solution is optimal and feasible")
        return results

    def model_solve(self, solver=None, mgr=""):
        r"""Solve the SIM (counterfactual) instance.

        Signature and error behaviour as in :meth:`model_calibrate`.

        Returns:
            results (SolverResults): solver results. If the sim is
                already solved, the cached results are returned.

        Raises:
            WorkflowError: if the model is not calibrated or the SIM
                instance does not exist.
            SolveError: if the solver does not reach an acceptable
                optimum.
        """
        if not self.base_calibrated:
            raise WorkflowError(
                "You must first calibrate the model. Call "
                "`model_calibrate`.")
        if self.sim is None:
            raise WorkflowError(
                "You must create the SIM instance before you can solve "
                "it. Call `model_sim` first.")
        if self.sim_solved:
            logger.info("This sim has already been solved.")
            return self.sim_results

        self.sim_solved = False
        try:
            results = self._solve(self.sim, solver=solver, mgr=mgr)
        except SolveError as exc:
            self.sim_results = exc.results
            logger.error(str(exc))
            raise
        self.sim_results = results
        self.sim_solved = True
        logger.info("Sim model solved. Call `model_postprocess` to output.")
        logger.info("Solution is optimal and feasible")
        return results

    # ------------------------------------------------------------------
    # Comparison and exports
    # ------------------------------------------------------------------
    def _comparison_records(self):
        records = []
        for sim_var in self.sim.component_objects(Var, active=True):
            base_var = self.base.component(str(sim_var))
            if base_var is None:
                continue
            for index in sim_var:
                sim_value = value(sim_var[index], exception=False)
                base_value = value(base_var[index], exception=False)
                if sim_value is None or base_value is None:
                    difference = None
                    pct_change = None
                else:
                    difference = sim_value - base_value
                    pct_change = None if base_value == 0 else difference / base_value * 100
                records.append({
                    "component": str(sim_var),
                    "index": index,
                    "base_value": base_value,
                    "sim_value": sim_value,
                    "difference": difference,
                    "pct_change": pct_change,
                })
        return records

    @staticmethod
    def _comparison_frame(records) -> pd.DataFrame:
        """Return the comparison records as a tidy pandas DataFrame.

        The variable index is expanded into ``index_1..index_N`` columns
        (N = the largest dimensionality present), so the frame is valid
        rectangular data with one row per variable element.
        """
        max_dims = max((len(_normalise_index(r["index"])) for r in records),
                       default=0)
        rows = []
        for r in records:
            indexes = list(_normalise_index(r["index"]))
            indexes.extend([""] * (max_dims - len(indexes)))
            row = {"component": r["component"]}
            for n, part in enumerate(indexes):
                row[f"index_{n + 1}"] = part
            row["base_value"] = r["base_value"]
            row["sim_value"] = r["sim_value"]
            row["difference"] = r["difference"]
            row["pct_change"] = r["pct_change"]
            rows.append(row)
        columns = (["component"]
                   + [f"index_{n + 1}" for n in range(max_dims)]
                   + ["base_value", "sim_value", "difference", "pct_change"])
        return pd.DataFrame(rows, columns=columns)

    def model_compare(self, verbose=None):
        r"""Compare SIM against BASE variable by variable.

        Differences are reported as ``sim - base`` and percentage change
        as ``(sim - base)/base * 100`` throughout, including the
        objective (utility), so a welfare gain is positive.

        Args:
            verbose (str, optional): ``None`` to just return the
                DataFrame; ``'print'`` to also print it; any other
                string is treated as a directory path in which
                ``compared.csv`` is written.

        Returns:
            frame (pandas.DataFrame): one row per variable element with
                columns ``component``, ``index_1..index_N``,
                ``base_value``, ``sim_value``, ``difference``,
                ``pct_change``. The objective comparison is attached as
                ``frame.attrs['objective']`` with keys ``base``,
                ``sim``, and ``difference``.

        Raises:
            WorkflowError: if the BASE or SIM instance does not exist.
        """
        if self.base is None:
            raise WorkflowError("You have not created a BASE instance.")
        if self.sim is None:
            raise WorkflowError("You have not created a SIM instance.")

        records = self._comparison_records()
        frame = self._comparison_frame(records)
        base_obj = value(self.base.obj)
        sim_obj = value(self.sim.obj)
        frame.attrs["objective"] = {
            "base": base_obj,
            "sim": sim_obj,
            "difference": sim_obj - base_obj,
        }
        if self.base_calibrated and self.sim_solved:
            solved_note = "both models solved"
        elif self.base_calibrated:
            solved_note = "base model solved; sim model unsolved"
        elif self.sim_solved:
            solved_note = "base model unsolved; sim model solved"
        else:
            solved_note = "both models unsolved"
        frame.attrs["solved"] = solved_note

        if verbose == "print":
            print("#===========HERE ARE THE DIFFERENCES==========#")
            print(f"#=========== note: {solved_note} ==========#")
            print(frame.to_string(index=False))
            print(f"\nCalibrated Value of obj = {base_obj}")
            print(f"Simulated Value of obj = {sim_obj}")
            print(f"Difference of obj = {sim_obj - base_obj}")
        elif verbose:
            directory = Path(verbose)
            directory.mkdir(parents=True, exist_ok=True)
            destination = directory / "compared.csv"
            with destination.open("w", newline="", encoding="utf-8") as handle:
                handle.write(f"# {solved_note}\n")
                frame.to_csv(handle, index=False)
                writer = csv.writer(handle)
                writer.writerow([])
                writer.writerow(["Calibrated Value of obj", base_obj])
                writer.writerow(["Simulated Value of obj", sim_obj])
                writer.writerow(["Difference of obj", sim_obj - base_obj])
            logger.info("Comparison saved to: %s", destination)
        return frame

    def _write_variables(self, instance, directory: Path, moment: str) -> None:
        prefix = directory / "vars"
        for component in instance.component_objects(Var, active=True):
            destination = Path(f"{prefix}{component}_{moment}.csv")
            indexes = list(component)
            dimensions = max((len(_normalise_index(i)) for i in indexes), default=0)
            with destination.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                if dimensions <= 1:
                    writer.writerow(["Names", str(component)])
                    for index in indexes:
                        writer.writerow([index, value(component[index], exception=False)])
                else:
                    writer.writerow([*(f"index_{i + 1}" for i in range(dimensions)), "value"])
                    for index in indexes:
                        parts = list(_normalise_index(index))
                        parts.extend([""] * (dimensions - len(parts)))
                        writer.writerow([*parts, value(component[index], exception=False)])
            logger.info("Vars saved to: %s", destination)

    @staticmethod
    def _save_payload(path: Path, *, kind: str, instance, results, solved: bool,
                      numeraire=None) -> None:
        payload = {
            "format": "cge-core-instance-v1",
            "kind": kind,
            "instance": instance,
            "results": results,
            "solved": solved,
            "numeraire": numeraire,
        }
        with path.open("wb") as handle:
            dill.dump(payload, handle)

    def model_postprocess(self, object_name="", verbose="", base=True):
        r"""Display or export an instance, results, params, or variables.

        Args:
            object_name (str): one of ``'compare'`` (dispatches to
                :meth:`model_compare` with ``verbose``), ``'instance'``,
                ``'results'``, ``'params'`` (returns a dict of
                parameter values), ``'vars'`` (CSV export), ``'obj'``
                (CSV export), or ``'dill_instance'`` (persistence).
            verbose (str): ``'print'`` or a destination directory,
                depending on ``object_name``.
            base (bool): operate on the BASE (True) or SIM (False)
                instance.

        Returns:
            Varies by ``object_name``: the comparison DataFrame, a
            params dict, a written path, or None for display modes.

        Raises:
            WorkflowError: if the required instance/results are missing.
            ValueError: for an unknown ``object_name`` or a missing
                required destination.
        """
        if object_name == "compare":
            return self.model_compare(verbose=verbose)

        instance = self.base if base else self.sim
        results = self.base_results if base else self.sim_results
        kind = "base" if base else "sim"
        if instance is None:
            raise WorkflowError(
                f"Please make sure the {kind} instance has been created.")
        if not object_name:
            raise ValueError("Please specify what you would like to output.")

        if object_name == "instance":
            return print_function(verbose, output=instance.display,
                                  typename="instance")
        if object_name == "results":
            if results is None:
                raise WorkflowError(
                    f"You must solve the {kind} instance first.")
            return print_function(verbose, output=results.write,
                                  typename="results")
        if object_name == "params":
            params = {}
            for component in instance.component_objects(Param, active=True):
                for index in component:
                    params[(str(component), index)] = value(component[index])
            logger.info("Collected %d parameter values from the %s "
                        "instance.", len(params), kind)
            return params
        if object_name not in {"vars", "obj", "dill_instance"}:
            raise ValueError(f"'{object_name}' is not a valid object_name.")
        if not verbose:
            raise ValueError("Please specify a directory to export to.")

        directory = Path(verbose)
        directory.mkdir(parents=True, exist_ok=True)
        moment = time.strftime("%Y-%b-%d__%H_%M_%S", time.localtime())
        if object_name == "vars":
            self._write_variables(instance, directory, moment)
        elif object_name == "obj":
            destination = directory / f"obj_{moment}.csv"
            with destination.open("w", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerow(["objective", value(instance.obj)])
            logger.info("Objective saved to: %s", destination)
        else:
            if results is None:
                raise WorkflowError(
                    f"You must solve the {kind} instance first.")
            destination = directory / f"dill_instance_{kind}_{moment}"
            self._save_payload(
                destination, kind=kind, instance=instance, results=results,
                solved=self.base_calibrated if base else self.sim_solved,
                numeraire=self.numeraire,
            )
            logger.info("%s instance saved to: %s", kind.capitalize(),
                        destination)
        return None

    def model_load_instance(self, pathname, base=True):
        r"""Load a trusted dill file created by :meth:`model_postprocess`.

        Dill can execute code while loading. Never open an untrusted file.
        Legacy v0.2.1 files containing only a raw Pyomo instance are
        accepted.

        Args:
            pathname (str or PathLike): path to the dill file.
            base (bool): restore into the BASE (True) or SIM (False)
                slot.

        Returns:
            instance (ConcreteModel): the loaded instance.

        Raises:
            FileNotFoundError: if ``pathname`` does not exist.
        """
        path = Path(pathname)
        if not path.exists():
            raise FileNotFoundError(
                f"'{pathname}' does not exist. Please enter a valid path "
                "to the file you would like to load.")
        with path.open("rb") as handle:
            payload = dill.load(handle)

        if isinstance(payload, dict) and payload.get("format") == "cge-core-instance-v1":
            instance = payload["instance"]
            results = payload.get("results")
            solved = bool(payload.get("solved"))
            numeraire = payload.get("numeraire")
        else:
            instance = payload
            results = None
            solved = False
            numeraire = None

        if base:
            self.base = instance
            self.base_results = results
            self.base_calibrated = solved
            self.numeraire = numeraire
            self.dict_base = {}
            self._invalidate_sim()
            logger.info("base instance loaded")
        else:
            self.sim = instance
            self.sim_results = results
            self.sim_solved = solved
            if numeraire is not None:
                self.numeraire = numeraire
            self.dict_sim = {}
            logger.info("sim instance loaded")
        return instance


def print_function(verbose="", output=None, typename=""):
    """Print a display callback or write it to ``<verbose>/<typename>``.

    Args:
        verbose (str): ``'print'`` to print to stdout, or a directory
            path to write into.
        output (callable): display callback (e.g. ``instance.display``
            or ``results.write``) accepting an optional ``ostream``.
        typename (str): label used in messages and as the filename.

    Returns:
        destination (Path or None): the written path, or None when
        printing.

    Raises:
        ValueError: if ``verbose`` is empty.
    """
    if not verbose:
        raise ValueError("Please specify how you would like to output.")
    if verbose == "print":
        print("\nThis is the " + typename + "\n")
        output()
        print("Output printed")
        return None

    directory = Path(verbose)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / typename
    with destination.open("w", encoding="utf-8") as handle:
        output(ostream=handle)
    return destination
