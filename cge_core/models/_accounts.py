# -*- coding: utf-8 -*-
"""Checking the account labels a model reads out of a social accounting matrix.

Background for non-programmers
------------------------------
A social accounting matrix (SAM) is a square table of an economy's transactions.
Its rows and columns are named accounts: households, government, investment,
the rest of the world, and so on.  A model's equations have to look those
accounts up by name, but different countries' SAMs spell them differently — one
may call the household account ``HOH`` and another ``HH``.

So each model ships with default labels and lets the user override any of them.
This file holds the checking that has to happen when they do.  It used to be
written out separately inside two model files, word for word the same, which
meant a fix to one would not reach the other.
"""
from __future__ import annotations


def merge_accounts(defaults, overrides, *, require_distinct=False):
    """Combine the model's default account labels with the user's overrides.

    Parameters
    ----------
    defaults : dict
        The labels the model uses if the user says nothing.
    overrides : dict or None
        Only the labels the user wants to change.  Anything left out keeps its
        default, so a user renaming one account does not have to restate them
        all.
    require_distinct : bool
        Whether two accounts are forbidden from sharing a label.

    Three things are checked, each because getting them wrong produces a
    failure that is hard to trace back to its cause:

    1. Unknown keys are rejected.  Silently ignoring a misspelt key would leave
       the user believing they had relabelled an account when they had not, and
       the model would then read the wrong row of their SAM.

    2. Labels must be non-empty text.  An empty or blank label cannot match any
       row of a SAM, so the failure would otherwise appear much later as a
       missing-data error naming nothing useful.

    3. Where ``require_distinct`` is set, no two accounts may share a label.
       One row of a SAM cannot simultaneously be the household and the
       government: the resulting model would balance and would describe an
       economy that does not exist.
    """
    merged = dict(defaults)
    if overrides:
        unknown = sorted(set(overrides) - set(merged))
        if unknown:
            raise ValueError(
                "Unknown account keys %s; valid keys are %s."
                % (unknown, sorted(merged)))
        merged.update(overrides)

    if any(not isinstance(label, str) or not label.strip()
           for label in merged.values()):
        raise ValueError("Account labels must be non-empty strings.")

    # Surrounding spaces in a label are almost always a typing accident, and
    # would stop the label matching the SAM row it was meant to name.
    merged = {key: label.strip() for key, label in merged.items()}

    if require_distinct and len(set(merged.values())) != len(merged):
        raise ValueError(
            "Institutional account labels must be distinct; one SAM "
            "account cannot fill multiple economic roles.")
    return merged
