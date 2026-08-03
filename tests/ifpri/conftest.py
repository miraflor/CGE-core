# -*- coding: utf-8 -*-
"""Shared fixtures for optional local IFPRI integration tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def ifpri_source_dir() -> Path:
    raw = os.environ.get("IFPRI_SOURCE_DIR")
    if not raw:
        pytest.skip("IFPRI_SOURCE_DIR is not set; external IFPRI test skipped.")
    path = Path(raw)
    if not (path / "test.dat").is_file():
        pytest.fail(f"IFPRI_SOURCE_DIR does not contain test.dat: {path}")
    return path
