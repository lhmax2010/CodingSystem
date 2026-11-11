"""Test refusal, logging failure and immutable attempts with lightweight sentinels."""

import io
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from ci import gate_runtime as gate


@pytest.mark.unit
def test_preflight_recovery_timeout_and_freshness() -> None:
    samples = iter([(1000, 0.0, 20), (9000, 11.0, 20), (5000, 1.0, 20)])
    elapsed = [0.0]

    def sleep(delay: float) -> None:
        elapsed[0] += delay

    record = gate.preflight(lambda: next(samples), lambda: elapsed[0], sleep)
    assert record["waited"] == 30
    gate.fresh_preflight(record, record["at"])
    for change in (
        {"at": record["at"] - 61},
        {"at": record["at"] + 1},
        {"available": 4095},
        {"load": 11},
        {"cores": 0},
        {"waited": 1801},
    ):
        with pytest.raises(ValueError):
            gate.fresh_preflight(record | change, record["at"])
    elapsed[0] = 0
    with pytest.raises(TimeoutError):
        gate.preflight(lambda: (0, 0.0, 20), lambda: elapsed[0], sleep)
    assert elapsed[0] == 1800


@pytest.mark.unit
def test_real_resource_reader() -> None:
    available, load, cores = gate.resources()
    assert available > 0 and load >= 0 and cores > 0


@pytest.mark.unit
@pytest.mark.parametrize("change", [0, 1, 2, 3, 4, 5, 6])
def test_effective_limits_validator(change: int) -> None:
    args = ("200000", "100000", 3221225472, 0, 19, "idle")
    gate.validate_limits(*args)
    bad = [
        ("max", "100000", 3221225472, 0, 19, "idle"),
        ("300000", "100000", 3221225472, 0, 19, "idle"),
        ("200000", "100000", 9999999999, 0, 19, "idle"),
        ("200000", "100000", 3221225472, 1, 19, "idle"),
        ("200000", "100000", 3221225472, 0, 0, "idle"),
        ("200000", "100000", 3221225472, 0, 19, "best-effort"),
        ("200000", "100000", 2147483648, 0, 19, "idle"),
    ]
    with pytest.raises(ValueError):
        gate.validate_limits(*bad[change])


@pytest.mark.unit
def test_cross_worktree_shared_lock(tmp_path: Path) -> None:
    path = tmp_path / "codingsystem-heavy.lock"
    with gate.heavy_lock(path):
        with pytest.raises(BlockingIOError), gate.heavy_lock(path):
            raise AssertionError("second holder entered")
    with gate.heavy_lock(path):
        pass


@pytest.mark.unit
@pytest.mark.parametrize(
    "component", ["docs", "docs/dev", "docs/dev/deliver", "docs/dev/deliver/task-999"]
)
def test_symlink_parent_never_touches_history(
    component: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    history = tmp_path / "history"
    history.mkdir()
    (history / "gate_report.txt").write_bytes(b"immutable")
    link = Path(component)
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(history, target_is_directory=True)
    with pytest.raises(OSError), gate.task_directory("task-999"):
        raise AssertionError("redirected write permitted")
    assert (history / "gate_report.txt").read_bytes() == b"immutable"


@pytest.mark.unit
def test_file_aliases_and_attempts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with gate.task_directory("task-999") as directory:
        first, fd = gate.new_report(directory)
        gate.write_all(fd, b"first")
        os.close(fd)
        second, fd = gate.new_report(directory)
        os.close(fd)
    base = Path("docs/dev/deliver/task-999")
    assert first != second and (base / first).read_bytes() == b"first"
    (base / "gate_report.txt").symlink_to(first)
    with pytest.raises(ValueError), gate.task_directory("task-999"):
        raise AssertionError("report alias permitted")
    (base / "gate_report.txt").unlink()
    (base / "gate_report.txt").mkdir()
    with pytest.raises(ValueError), gate.task_directory("task-999"):
        raise AssertionError("report directory permitted")
    with pytest.raises(ValueError), gate.task_directory("../../bad"):
        raise AssertionError("escape permitted")


@pytest.mark.unit
def test_history_head_and_index(monkeypatch: pytest.MonkeyPatch) -> None:
    for source in ("ls-tree", "ls-files"):
        monkeypatch.setattr(
            gate,
            "git",
            lambda *args, source=source: (
                "docs/dev/deliver/task-001/gate_report.txt" if args[0] == source else ""
            ),
        )
        with pytest.raises(ValueError, match="committed"):
            gate.protect_history("task-001")
    monkeypatch.setattr(gate, "git", lambda *args: "")
    gate.protect_history("task-999")
    gate.clean_tree("task-999")
    monkeypatch.setattr(gate, "git", lambda *args: " M framework/code.py")
    with pytest.raises(ValueError, match="Working tree"):
        gate.clean_tree("task-999")


@pytest.mark.unit
def test_logger_and_check_exit_codes(tmp_path: Path) -> None:
    path = tmp_path / "log.txt"
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        gate.log_stream(io.BufferedReader(io.BytesIO(b"line\n")), fd)
        assert path.read_bytes() == b"line\n"
        command = [sys.executable, "-B", "-c", "print('sentinel')"]
        assert gate.supervise(command, fd) == (0, 0)
        failed = [sys.executable, "-B", "-c", "raise SystemExit(3)"]
        assert gate.supervise(failed, fd)[0] == 3
        assert gate.supervise(command, fd, failed)[1] == 3
        with pytest.raises(OSError):
            gate.supervise(command, fd, ["/nonexistent-logger"])
    finally:
        os.close(fd)
    full = os.open("/dev/full", os.O_WRONLY)
    try:
        with pytest.raises(OSError):
            gate.log_stream(io.BufferedReader(io.BytesIO(b"line")), full)
    finally:
        os.close(full)
    readonly = os.open(path, os.O_RDONLY)
    try:
        with pytest.raises(OSError):
            gate.write_all(readonly, b"refused")
    finally:
        os.close(readonly)


@pytest.mark.unit
@pytest.mark.parametrize("codes", [(0, 0), (1, 0), (0, 2)])
def test_execute_records_and_failures(
    codes: tuple[int, int],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CODINGSYSTEM_INTRANET", raising=False)
    monkeypatch.setattr(gate, "clean_tree", lambda task: None)
    monkeypatch.setattr(gate, "protect_history", lambda task: None)
    monkeypatch.setattr(gate, "effective_limits", lambda: None)
    monkeypatch.setattr(gate, "git", lambda *args: "fixture-id")
    monkeypatch.setattr(
        gate, "preflight", lambda: dict(available=5000, load=1, cores=20, waited=0, at=time.time())
    )
    monkeypatch.setattr(gate, "supervise", lambda command, fd: codes)
    assert gate.execute("task-999") == int(codes != (0, 0))
    report = Path("docs/dev/deliver/task-999/gate_report.attempt-001.txt").read_text()
    assert report.startswith("PREFLIGHT ") and "Tree: fixture-id" in report
    assert ("status=ok" in report) == (codes == (0, 0))
    assert ("status=ok" in capsys.readouterr().out) == (codes == (0, 0))
    monkeypatch.setenv("CODINGSYSTEM_INTRANET", "0")
    with pytest.raises(ValueError, match="unset"):
        gate.execute("task-999")


@pytest.mark.unit
def test_final_log_write_failure_no_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CODINGSYSTEM_INTRANET", raising=False)
    monkeypatch.setattr(gate, "clean_tree", lambda task: None)
    monkeypatch.setattr(gate, "protect_history", lambda task: None)
    monkeypatch.setattr(gate, "effective_limits", lambda: None)
    monkeypatch.setattr(gate, "git", lambda *args: "fixture-id")
    monkeypatch.setattr(
        gate, "preflight", lambda: dict(available=5000, load=1, cores=20, waited=0, at=time.time())
    )
    monkeypatch.setattr(gate, "supervise", lambda command, fd: (0, 0))
    original = gate.write_all

    def fail_footer(fd: int, data: bytes) -> None:
        if data.startswith(b"ALL-END"):
            raise OSError("synthetic full disk")
        original(fd, data)

    monkeypatch.setattr(gate, "write_all", fail_footer)
    with pytest.raises(OSError):
        gate.execute("task-999")
    assert "status=ok" not in capsys.readouterr().out
    assert (
        "status=ok" not in Path("docs/dev/deliver/task-999/gate_report.attempt-001.txt").read_text()
    )


@pytest.mark.unit
def test_staged_delete_keeps_head_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    report = Path("docs/dev/deliver/task-999/gate_report.txt")
    report.parent.mkdir(parents=True)
    report.write_text("immutable history")
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="Fixture",
        GIT_AUTHOR_EMAIL="fixture@example.com",
        GIT_COMMITTER_NAME="Fixture",
        GIT_COMMITTER_EMAIL="fixture@example.com",
    )
    for args in (
        ["init", "-q"],
        ["add", "."],
        ["commit", "-qm", "fixture"],
        ["rm", "--cached", str(report)],
    ):
        subprocess.run(["git", *args], env=env, check=True, capture_output=True)
    with pytest.raises(ValueError, match="committed"):
        gate.protect_history("task-999")
    assert report.read_text() == "immutable history"
