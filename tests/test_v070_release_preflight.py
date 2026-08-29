"""Release-migration guard added after the v0.7 independent review."""
from pathlib import Path
import subprocess
import sys


def test_prepare_release_check_is_no_write_and_idempotent_after_application():
    root = Path(__file__).parents[1]
    tracked = [
        root / "CITATION.cff",
        root / "CHANGELOG.md",
        root / "cge_core" / "engine.py",
        root / "cge_core" / "examples" / "stdcge_model_def.py",
        root / "cge_core" / "examples" / "splcge_model_def.py",
        root / "cam" / "cam_model_def.py",
    ]
    before = {path: path.read_bytes() for path in tracked}
    completed = subprocess.run(
        [sys.executable, str(root / "release" / "prepare_release.py"), "--check"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    after = {path: path.read_bytes() for path in tracked}
    assert before == after
    assert "release preflight OK" in completed.stdout
