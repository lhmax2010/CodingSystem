"""Reject synthetic content and messages before a local bare repository receives them."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
@pytest.mark.parametrize("location", ["file", "message", "safe"])
def test_local_push_hook(location: str, tmp_path: Path) -> None:
    repo = tmp_path / "source"
    repo.mkdir()
    remote = tmp_path / "remote.git"
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="Fixture",
        GIT_AUTHOR_EMAIL="fixture@example.com",
        GIT_COMMITTER_NAME="Fixture",
        GIT_COMMITTER_EMAIL="fixture@example.com",
        PYTHONDONTWRITEBYTECODE="1",
    )

    def git(*args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(["git", *args], cwd=repo, env=env, capture_output=True)

    assert git("init", "-q").returncode == 0
    assert git("init", "--bare", "-q", str(remote)).returncode == 0
    shutil.copytree(ROOT / "ci", repo / "ci", ignore=shutil.ignore_patterns("__pycache__"))
    (repo / "ci/content_exemptions.json").write_text(
        '{"version":"task-004-content-v2","entries":[]}'
    )
    assert git("config", "core.hooksPath", "ci/hooks").returncode == 0
    assert git("remote", "add", "origin", str(remote)).returncode == 0
    payload = "gh" + "p_" + "a" * 36
    (repo / "input.txt").write_text(payload if location == "file" else "safe")
    assert git("add", ".").returncode == 0
    assert git("commit", "-qm", payload if location == "message" else "safe").returncode == 0
    pushed = git("push", "origin", "HEAD:main")
    assert (pushed.returncode == 0) == (location == "safe")
    output = pushed.stdout + pushed.stderr
    assert payload.encode() not in output
    if location != "safe":
        assert b"FAIL" in output
        refs = (
            subprocess.check_output(
                ["git", "--git-dir", str(remote), "show-ref"], stderr=subprocess.DEVNULL
            )
            if location == "safe"
            else git("ls-remote", "origin").stdout
        )
        assert not refs


@pytest.mark.unit
def test_content_stdin_has_no_exemptions() -> None:
    payload = ("gh" + "p_" + "a" * 36).encode()
    result = subprocess.run(
        [sys.executable, "-B", "-m", "ci.checks", "content-stdin"],
        input=payload,
        capture_output=True,
    )
    assert result.returncode == 1
    assert b"rule=token" in result.stdout
    assert payload not in result.stdout + result.stderr
