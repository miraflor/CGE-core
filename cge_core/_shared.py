# -*- coding: utf-8 -*-
"""Small helpers that more than one part of CGE-Core needs.

Why this file exists
--------------------
Several modules used to keep their own private copy of the same few helper
functions.  Copies drift: one copy gets a bug fix and the other does not, and
the two then behave differently for no reason a user could ever guess.  Putting
the shared pieces here means there is exactly one version of each, and a change
made once takes effect everywhere.

Nothing in this file knows anything about economics.  These are plumbing
helpers: how to name a stored value, how to tidy up an index, how to check that
a number is really a number, and how to lay out a before-and-after table.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Working with component indexes
# ---------------------------------------------------------------------------
# A "component" is one named thing inside a model: a price, a quantity, a tax
# rate.  Most components are indexed, meaning they hold one number per sector,
# per factor, or per pair of the two.  The index is how you pick out one of
# those numbers, for example ("CAP", "BRD") for capital used in bread.


def component_key(name: str, index: Any) -> Tuple[str, Any]:
    """Return a stable dictionary key that identifies one component element.

    The engine remembers the original value of anything the user changes, so a
    change can be undone later.  That memory is a dictionary, and dictionary
    keys must be hashable, which is Python's word for "usable as a lookup
    label".  Almost every index already is.  For the rare index that is not, we
    fall back to its printed form, which is always usable as a label.
    """
    try:
        hash(index)
        safe_index = index
    except TypeError:
        safe_index = repr(index)
    return name, safe_index


def index_tuple(index: Any) -> Tuple[Any, ...]:
    """Return any index in the same shape: a tuple, possibly an empty one.

    Pyomo hands indexes over in three different shapes.  A component with no
    index gives ``None``.  A component indexed by one set gives a bare value
    such as ``"BRD"``.  A component indexed by two or more sets gives a tuple
    such as ``("CAP", "BRD")``.  Code that wants to count index positions, or
    spread them across table columns, should not have to handle three shapes,
    so everything is converted to a tuple first.
    """
    if index is None:
        return ()
    if isinstance(index, tuple):
        return index
    return (index,)


# ---------------------------------------------------------------------------
# Checking values the user supplied
# ---------------------------------------------------------------------------


def finite_float(new_value: Any, name: str, index: Any) -> float:
    """Return ``new_value`` as an ordinary finite number, or raise ValueError.

    A CGE model is solved by a numerical routine that cannot cope with
    "infinity" or with "not a number" (the value Python produces from things
    like zero divided by zero).  Letting either into the model produces a
    failure much later, in the solver, with a message that gives no hint about
    which value caused it.  Rejecting the value at the moment it is supplied
    means the error names the exact component and index the user typed.
    """
    message = f"VALUE for {name}[{index}] must be a finite numeric scalar."
    try:
        numeric = float(new_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(message) from exc
    if not math.isfinite(numeric):
        raise ValueError(message)
    return numeric


# ---------------------------------------------------------------------------
# Undoing a change that failed halfway through
# ---------------------------------------------------------------------------


def set_fixed(item, fixed: bool) -> None:
    """Fix or release one variable.

    "Fixing" a variable means telling the solver to treat it as a known number
    rather than something to be solved for.  Fixing and releasing variables is
    how a modeller chooses a closure: which quantities the economy adjusts and
    which are held still.
    """
    if fixed:
        item.fix()
    else:
        item.unfix()


def restore_item(item, is_variable: bool, prior_value, prior_fixed,
                 logger, description: str, name: str, index: Any) -> None:
    """Put one component element back the way it was before a failed change.

    If applying a change raises partway through, the model must not be left in
    a half-changed state, because everything computed from it afterwards would
    be quietly wrong.  This puts back both pieces of the previous state: the
    number, and, for a variable, whether it was fixed.

    If even the restore fails, we record that in the log rather than raising.
    The original failure is the one worth reporting to the user; hiding it
    behind a second, more confusing error would help nobody.
    """
    try:
        item.set_value(prior_value)
        if is_variable:
            set_fixed(item, prior_fixed)
    except Exception:
        logger.exception("Failed to roll back %s for %s[%s].",
                         description, name, index)


# ---------------------------------------------------------------------------
# Before-and-after comparison tables
# ---------------------------------------------------------------------------
# Comparing a policy run against the benchmark is the central thing a CGE user
# does, so several parts of the package build such a table.  They used to build
# it with separate, slightly different code, which is why they disagreed about
# what to call the columns.  They now share the builder below and pass in the
# names they need, so the shape of the table is decided in one place.


def expand_index_columns(index: Any, width: int) -> Dict[str, Any]:
    """Spread one index across ``index_1``, ``index_2``, ... columns.

    A table must be rectangular: every row needs the same columns.  But
    components differ in how many index positions they have — a price of a good
    has one, a factor payment has two.  So the table is given as many index
    columns as the widest component needs, and narrower rows leave the spare
    columns empty.
    """
    parts = index_tuple(index)
    return {
        f"index_{position + 1}": parts[position] if position < len(parts) else ""
        for position in range(width)
    }


def index_column_names(width: int) -> List[str]:
    """Return the index column names, in order, for a table of this width."""
    return [f"index_{position + 1}" for position in range(width)]


def percentage_change(difference: Optional[float], reference: Optional[float],
                      *, zero_reference) -> Optional[float]:
    """Return the percentage change, or ``zero_reference`` when the base is zero.

    Percentage change has no meaning when the quantity you are comparing
    against is zero: any change from zero is infinitely large in percentage
    terms.  Callers say what they want reported in that case, because the two
    public interfaces of CGE-Core have always answered it differently and
    changing either answer would break code that people already have.
    """
    if difference is None or reference is None:
        return None
    if reference == 0:
        return zero_reference
    return difference / reference * 100.0


def comparison_frame(current: Mapping[Tuple[str, Tuple[Any, ...]], Optional[float]],
                     reference: Mapping[Tuple[str, Tuple[Any, ...]], Optional[float]],
                     *,
                     reference_column: str,
                     value_column: str,
                     zero_reference) -> pd.DataFrame:
    """Return one row per component element, comparing ``current`` to ``reference``.

    Both inputs map ``(component name, index)`` to a number.  The result has one
    column naming the component, as many index columns as the widest component
    needs, then the reference value, the current value, the plain difference,
    and the percentage change.

    Differences are always reported as current minus reference, so a positive
    number always means "larger than the thing being compared against".
    """
    keys = sorted(current, key=lambda item: (item[0], repr(item[1])))
    width = max((len(index) for _, index in keys), default=0)

    rows = []
    for component, index in keys:
        current_value = current[(component, index)]
        reference_value = reference[(component, index)]
        difference = None
        if current_value is not None and reference_value is not None:
            difference = current_value - reference_value
        row = {"component": component}
        row.update(expand_index_columns(index, width))
        row.update({
            reference_column: reference_value,
            value_column: current_value,
            "difference": difference,
            "pct_change": percentage_change(difference, reference_value,
                                            zero_reference=zero_reference),
        })
        rows.append(row)

    columns = (["component"] + index_column_names(width)
               + [reference_column, value_column, "difference", "pct_change"])
    return pd.DataFrame(rows, columns=columns)


def objective_comparison(current: Optional[float], reference: Optional[float],
                         *, zero_reference) -> Dict[str, Optional[float]]:
    """Return the same before-and-after summary for the model's objective value.

    The objective is a single number rather than a table, so it travels
    alongside the table rather than inside it.  The key ``reference`` is the
    older public name and ``reference_value`` the newer one; both are kept so
    that code written against either version keeps working.
    """
    difference = None
    if current is not None and reference is not None:
        difference = current - reference
    return {
        "reference": reference,
        "reference_value": reference,
        "value": current,
        "difference": difference,
        "pct_change": percentage_change(difference, reference,
                                        zero_reference=zero_reference),
    }


def rectangular_frame(records: Sequence[Mapping[str, Any]], *,
                      index_field: str,
                      leading_column: str,
                      trailing_columns: Sequence[str]) -> pd.DataFrame:
    """Build a rectangular table from records that each carry a raw index.

    This is the same idea as :func:`comparison_frame`, for callers that have
    already computed their own differences and only need the index spread into
    columns and the column order settled.
    """
    width = max((len(index_tuple(record[index_field])) for record in records),
                default=0)
    rows = []
    for record in records:
        row = {leading_column: record[leading_column]}
        row.update(expand_index_columns(record[index_field], width))
        for column in trailing_columns:
            row[column] = record[column]
        rows.append(row)
    columns = ([leading_column] + index_column_names(width)
               + list(trailing_columns))
    return pd.DataFrame(rows, columns=columns)
