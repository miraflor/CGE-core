# -*- coding: utf-8 -*-
"""Inspect the external IFPRI test dataset without solving a model."""
from __future__ import annotations

from cge_core.ifpri import IfpriDataError, load_ifpri_test_data


def main() -> int:
    try:
        dataset = load_ifpri_test_data()
    except IfpriDataError as exc:
        print(f"IFPRI data error: {exc}")
        return 1

    sets = dataset.sets
    sam = dataset.sam
    print(f"Source: {dataset.source_path}")
    print(f"Activities ({len(sets.activities)}): {', '.join(sets.activities)}")
    print(f"Commodities ({len(sets.commodities)}): {', '.join(sets.commodities)}")
    print(f"Factors ({len(sets.factors)}): {', '.join(sets.factors)}")
    print(f"Households ({len(sets.households)}): {', '.join(sets.households)}")
    print(f"Active SAM accounts: {len(sam.accounts)}")
    print(f"SAM scale: {sam.scale:g}")
    print(f"Maximum absolute SAM imbalance: {sam.max_abs_imbalance():.12g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
