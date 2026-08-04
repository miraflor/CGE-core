# -*- coding: utf-8 -*-
"""Shared fixtures and marker separation for IFPRI tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest


def pytest_collection_modifyitems(items) -> None:
    """Mark tests that transitively depend on the official external source."""
    external = pytest.mark.external_ifpri
    for item in items:
        if "ifpri_source_dir" in getattr(item, "fixturenames", ()):
            item.add_marker(external)


@pytest.fixture(scope="session")
def ifpri_source_dir() -> Path:
    """Return the optional official IFPRI source used for local replication."""
    raw = os.environ.get("IFPRI_SOURCE_DIR")
    if not raw:
        pytest.skip("IFPRI_SOURCE_DIR is not set; external IFPRI test skipped.")
    path = Path(raw)
    if not (path / "test.dat").is_file():
        pytest.fail(f"IFPRI_SOURCE_DIR does not contain test.dat: {path}")
    return path
