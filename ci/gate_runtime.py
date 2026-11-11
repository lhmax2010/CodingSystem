"""Own the constrained gate lifecycle, exclusive evidence files and log processes."""

from __future__ import annotations

import fcntl
import io
import json
import os
import re
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast


def git(*args: str) -> str:
    """Read repository identity without shell interpretation."""
    return subprocess.check_output(["git", *args], text=True).strip()


def clean_tree(task: str) -> None:
    """Allow only the current task's records to differ from the tested commit."""
    dirty = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        ".",
        ":(exclude)docs/dev/STATUS.md",
        f":(exclude)docs/dev/deliver/{task}",
    )
    if dirty:
        raise ValueError("Working tree differs from HEAD outside task records:\n" + dirty)


@contextmanager
def heavy_lock(path: Path) -> Iterator[None]:
    """Hold flock through preflight, checks and evidence finalization, across worktrees."""
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def resources() -> tuple[int, float, int]:
    """Read the requested free available column, one-minute load and CPU count."""
    output = subprocess.check_output(["free", "-m"], text=True)
    print(output, end="", flush=True)
    mem = next(line for line in output.splitlines() if line.startswith("Mem:"))
    load = Path("/proc/loadavg").read_text().strip()
    print(load, flush=True)
    return (
        int(mem.split()[-1]),
        float(load.split()[0]),
        int(subprocess.check_output(["nproc"], text=True)),
    )


def preflight(
    reader: Callable[[], tuple[int, float, int]] = resources,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Wait at most thirty minutes without changing any resource limit."""
    start = clock()
    while True:
        available, load, cores = reader()
        waited = clock() - start
        if available >= 4096 and load <= cores / 2:
            return {
                "available": available,
                "load": load,
                "cores": cores,
                "waited": waited,
                "at": time.time(),
            }
        if waited >= 1800:
            raise TimeoutError("Resource preflight timed out")
        sleep(min(15, 1800 - waited))


def fresh_preflight(record: dict[str, Any], now: float) -> None:
    """Validate actual recorded values, rejecting missing, future and stale records."""
    if (
        not 0 <= now - record["at"] <= 60
        or record["available"] < 4096
        or record["cores"] < 1
        or record["load"] > record["cores"] / 2
        or not 0 <= record["waited"] <= 1800
    ):
        raise ValueError("Invalid or stale preflight record")


def effective_limits() -> None:
    """Verify actual cgroup limits and process scheduling priorities."""
    group = next(
        line.split(":", 2)[2]
        for line in Path("/proc/self/cgroup").read_text().splitlines()
        if line.startswith("0:")
    )
    root = Path("/sys/fs/cgroup") / group.lstrip("/")
    cpu = (root / "cpu.max").read_text().strip()
    quota, period = cpu.split()
    memory = int((root / "memory.max").read_text())
    swap = int((root / "memory.swap.max").read_text())
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    io = subprocess.check_output(["ionice", "-p", str(os.getpid())], text=True).strip()
    validate_limits(quota, period, memory, swap, nice, io)
    print(
        f"Resources actual: cpu.max={cpu}; memory.max={memory}; memory.swap.max={swap}; "
        f"nice={nice}; ionice={io}",
        flush=True,
    )


def validate_limits(quota: str, period: str, memory: int, swap: int, nice: int, io: str) -> None:
    """Keep validation pure for low-impact negative tests."""
    if (
        quota == "max"
        or int(quota) / int(period) > 2
        or memory != 3221225472
        or swap != 0
        or nice != 19
        or io != "idle"
    ):
        raise ValueError("Resource or priority limits are not effective")


@contextmanager
def task_directory(task: str) -> Iterator[int]:
    """Walk with directory descriptors; no component may redirect a report write."""
    if not re.fullmatch(r"task-\d{3}", task):
        raise ValueError("Invalid task identifier")
    fd = os.open(".", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in ("docs", "dev", "deliver", task):
            try:
                os.mkdir(component, dir_fd=fd)
            except FileExistsError:
                pass
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        for name in os.listdir(fd):
            if name.startswith("gate_report"):
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise ValueError("Unsafe report file: " + name)
        yield fd
    finally:
        os.close(fd)


def protect_history(task: str) -> None:
    """Check HEAD as well as the index, including staged deletions and attempts."""
    folder = f"docs/dev/deliver/{task}/"
    names = set(git("ls-tree", "-r", "--name-only", "HEAD", "--", folder).splitlines())
    names.update(git("ls-files", "--", folder).splitlines())
    if any(Path(name).name.startswith("gate_report") for name in names):
        raise ValueError("Refusing committed gate evidence in HEAD or index")


def new_report(directory: int) -> tuple[str, int]:
    """Never truncate an old report; retain every invocation under a new attempt."""
    for attempt in range(1, 10000):
        name = f"gate_report.attempt-{attempt:03d}.txt"
        try:
            fd = os.open(
                name, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o644, dir_fd=directory
            )
            return name, fd
        except FileExistsError:
            continue
    raise ValueError("Too many gate attempts")


def write_all(fd: int, data: bytes) -> None:
    """Detect short/failed writes instead of treating partial evidence as complete."""
    while data:
        count = os.write(fd, data)
        if count <= 0:
            raise OSError("Evidence write made no progress")
        data = data[count:]


def log_stream(source: io.BufferedReader, fd: int) -> None:
    """Own logging errors in a separately waited process, including flush failures."""
    while data := source.read1(8192):
        write_all(fd, data)
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    os.fsync(fd)


def supervise(command: list[str], fd: int, logger: list[str] | None = None) -> tuple[int, int]:
    """Explicitly wait for both checks and logger; neither return code is discarded."""
    producer = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        consumer = subprocess.Popen(
            logger or [sys.executable, "-B", "-m", "ci.gate_runtime", "--logger", str(fd)],
            stdin=producer.stdout,
            pass_fds=(fd,),
        )
    except OSError:
        producer.terminate()
        producer.wait()
        raise
    assert producer.stdout is not None
    producer.stdout.close()
    # A dead logger must not leave a silent, long-running check behind.
    while producer.poll() is None:
        if consumer.poll() is not None and consumer.returncode != 0:
            producer.terminate()
            break
        time.sleep(0.02)
    return producer.wait(), consumer.wait()


def execute(task: str) -> int:
    """Run only after acquiring the shared lock and creating safe fresh evidence."""
    clean_tree(task)
    protect_history(task)
    if "CODINGSYSTEM_INTRANET" in os.environ:
        raise ValueError("Development gate requires CODINGSYSTEM_INTRANET unset")
    # This module has no parameter that skips resource checks.
    effective_limits()
    with task_directory(task) as directory:
        record = preflight()
        name, fd = new_report(directory)
        path = Path("docs/dev/deliver") / task / name
        try:
            header = "PREFLIGHT " + json.dumps(record, sort_keys=True) + "\n"
            write_all(fd, header.encode())
            os.fsync(fd)
            with path.open() as evidence:
                saved = json.loads(evidence.readline().removeprefix("PREFLIGHT "))
            fresh_preflight(saved, time.time())
            clean_tree(task)
            details = f"Task: {task}\nHEAD: {git('rev-parse', 'HEAD')}\n"
            details += f"Tree: {git('rev-parse', 'HEAD^{tree}')}\n"
            details += f"Time: {datetime.now(UTC).isoformat()}\nAttempt: {path}\n"
            write_all(fd, details.encode())
            check_rc, log_rc = supervise(["bash", "ci/gate_steps.sh"], fd)
            status = "ok" if check_rc == log_rc == 0 else "fail"
            rc = 0 if status == "ok" else 1
            end = f"ALL-END {datetime.now(UTC).isoformat()} status={status} rc={rc}\n"
            if log_rc:
                print(f"Evidence logger failed: rc={log_rc}", file=sys.stderr)
            write_all(fd, end.encode())
            os.fsync(fd)
        finally:
            os.close(fd)
        # No success announcement until all writes, fsync and close succeeded.
        if not path.read_bytes().endswith(end.encode()):
            raise OSError("Incomplete gate evidence")
        print(end, end="", flush=True)
        print(f"Gate attempt retained: {path}; select final evidence only after success.")
        return rc


def main() -> int:
    """Launch the driver or its log-only child; internal check bypass flags do not exist."""
    if len(sys.argv) == 3 and sys.argv[1] == "--logger":
        log_stream(cast(io.BufferedReader, sys.stdin.buffer), int(sys.argv[2]))
        return 0
    if len(sys.argv) != 2 or not re.fullmatch(r"task-\d{3}", sys.argv[1]):
        print("Usage: ci/gate.sh task-NNN", file=sys.stderr)
        return 2
    common = Path(git("rev-parse", "--git-common-dir")).resolve()
    base = Path(os.environ.get("XDG_RUNTIME_DIR", str(common)))
    try:
        with heavy_lock(base / "codingsystem-heavy.lock"):
            return execute(sys.argv[1])
    except BlockingIOError:
        print("Another L1/L2 job holds the lock", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"Gate refused or evidence failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
