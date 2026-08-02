"""Access to the example datasets bundled with CGE-Core."""
from __future__ import annotations

from pathlib import Path

_DATASETS = {
    "splcge": "splcge_data_dir",
    "stdcge": "stdcge_data_dir",
}


def example_data(name: str) -> Path:
    """Return the path to a bundled example dataset.

    ``name`` is case-insensitive and must be ``"splcge"`` or ``"stdcge"``.
    Standard Python wheel installations unpack package data beside this module,
    so this path works independently of the caller's working directory.
    """
    key = name.lower().strip()
    try:
        directory = _DATASETS[key]
    except KeyError as exc:
        allowed = ", ".join(sorted(_DATASETS))
        raise ValueError(f"Unknown example dataset {name!r}; choose {allowed}.") from exc
    path = Path(__file__).resolve().parent / "data" / directory
    if not path.is_dir():
        raise FileNotFoundError(f"Bundled dataset is missing: {path}")
    return path
