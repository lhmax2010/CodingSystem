"""Exercise gate invocation failures before any expensive command can run."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
@pytest.mark.parametrize(
    "args",
    [
        [],
        ["task-2"],
        ["../../bad"],
        ["task-002", "bad"],
        ["task-002", "--in-scope", "extra"],
        ["task-001"],
    ],
)
def test_invalid_or_committed_report_is_rejected(args: list[str]) -> None:
    previous = (ROOT / "docs/dev/deliver/task-001/gate_report.txt").read_bytes()
    result = subprocess.run(["bash", "ci/gate.sh", *args], cwd=ROOT, capture_output=True)
    assert result.returncode == 2
    assert (ROOT / "docs/dev/deliver/task-001/gate_report.txt").read_bytes() == previous
    assert b"GATE 1-lock START" not in result.stdout


@pytest.mark.unit
def test_wrong_interpreter_fails_before_install(tmp_path: Path) -> None:
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci/gate.sh").write_bytes((ROOT / "ci/gate.sh").read_bytes())
    (tmp_path / ".venv/bin").mkdir(parents=True)
    interpreter = tmp_path / ".venv/bin/python"
    interpreter.write_text("#!/bin/sh\nprintf '3.13\\n'\n")
    interpreter.chmod(0o755)
    result = subprocess.run(["bash", "ci/gate.sh", "task-002"], cwd=tmp_path, capture_output=True)
    assert result.returncode == 1
    assert b"Interpreter mismatch: expected 3.12, got 3.13" in result.stderr
    assert not (tmp_path / "docs").exists()
