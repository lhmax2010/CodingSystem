"""Exercise shell guards in isolated repositories before resource checks."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
@pytest.mark.parametrize("args", [[], ["task-2"], ["../../bad"], ["task-004", "--in-scope"]])
def test_invalid_entry(args: list[str], tmp_path: Path) -> None:
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci/gate.sh").write_bytes((ROOT / "ci/gate.sh").read_bytes())
    result = subprocess.run(["bash", "ci/gate.sh", *args], cwd=tmp_path, capture_output=True)
    assert result.returncode == 2
    assert b"GATE" not in result.stdout
    assert not (tmp_path / "docs").exists()


@pytest.mark.unit
def test_dirty_before_scope_and_records_allowed(tmp_path: Path) -> None:
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci/gate.sh").write_bytes((ROOT / "ci/gate.sh").read_bytes())
    (tmp_path / "code.txt").write_text("original")
    (tmp_path / ".gitignore").write_text("bin/\n")
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="Fixture",
        GIT_AUTHOR_EMAIL="fixture@example.com",
        GIT_COMMITTER_NAME="Fixture",
        GIT_COMMITTER_EMAIL="fixture@example.com",
    )
    for args in (["init", "-q"], ["add", "."], ["commit", "-qm", "fixture"]):
        subprocess.run(["git", *args], cwd=tmp_path, env=env, check=True, capture_output=True)
    (tmp_path / "bin").mkdir()
    sentinel = tmp_path / "bin/systemd-run"
    sentinel.write_text("#!/bin/sh\nprintf scope-reached\nexit 5\n")
    sentinel.chmod(0o755)
    env["PATH"] = str(tmp_path / "bin") + os.pathsep + env["PATH"]
    (tmp_path / "code.txt").write_text("dirty")
    command = ["bash", "ci/gate.sh", "task-004"]
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True)
    assert result.returncode == 1
    assert b"Working tree differs" in result.stderr and b"scope-reached" not in result.stdout
    (tmp_path / "code.txt").write_text("original")
    (tmp_path / "docs/dev/deliver/task-004").mkdir(parents=True)
    (tmp_path / "docs/dev/STATUS.md").write_text("pending")
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True)
    assert result.returncode == 5 and b"scope-reached" in result.stdout
