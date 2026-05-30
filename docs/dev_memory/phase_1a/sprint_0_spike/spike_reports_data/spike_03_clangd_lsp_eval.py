#!/usr/bin/env python3
"""Sprint 0 S0-03 clangd LSP spike driver.

This is a dev-memory spike tool, not product code. It is intended to run inside
the Tizen GBS chroot where /home/abuild/s0/pkgmgr-info and build-s0-02 exist.
"""

from __future__ import annotations

import json
import os
import re
import resource
import select
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/home/abuild/s0/pkgmgr-info")
BUILD_DIR = Path("/home/abuild/s0/build-s0-02")
WORK_DIR = Path("/home/abuild/s0/s0_03")
OUT_JSON = WORK_DIR / "clangd_lsp_results.json"
OUT_LOG = WORK_DIR / "clangd_stderr_bounded.log"


def uri(path: Path) -> str:
    return "file://" + str(path)


def uri_to_path(value: str) -> Path:
    assert value.startswith("file://"), value
    return Path(value[7:])


def read_sample(name: str) -> list[dict[str, Any]]:
    return json.loads((WORK_DIR / name).read_text(encoding="utf-8"))


class JsonRpcClient:
    def __init__(self, proc: subprocess.Popen[bytes]):
        self.proc = proc
        self.next_id = 1
        self.responses: dict[int, Any] = {}
        self.notifications: list[dict[str, Any]] = []
        self.progress_events: list[dict[str, Any]] = []
        self.file_status_events: list[dict[str, Any]] = []
        self.index_begin_ts: float | None = None
        self.index_end_ts: float | None = None

    def send(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        assert self.proc.stdin is not None
        self.proc.stdin.write(header + data)
        self.proc.stdin.flush()

    def request(self, method: str, params: dict[str, Any], timeout: float = 30.0) -> Any:
        msg_id = self.next_id
        self.next_id += 1
        self.send({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = self.read_message(timeout=deadline - time.monotonic())
            if msg is None:
                continue
            self.handle(msg)
            if msg_id in self.responses:
                return self.responses.pop(msg_id)
        raise TimeoutError(f"request timed out: {method}")

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self.send(msg)

    def read_message(self, timeout: float = 0.2) -> dict[str, Any] | None:
        assert self.proc.stdout is not None
        ready, _, _ = select.select([self.proc.stdout], [], [], max(0.01, min(timeout, 0.2)))
        if not ready:
            return None
        line = self.proc.stdout.readline()
        if not line:
            return None

        headers: dict[str, str] = {}
        while line and line.strip():
            key, _, value = line.decode("ascii", errors="replace").partition(":")
            headers[key.lower()] = value.strip()
            line = self.proc.stdout.readline()
        length = int(headers["content-length"])
        body = self.proc.stdout.read(length)
        return json.loads(body.decode("utf-8"))

    def handle(self, msg: dict[str, Any]) -> None:
        if "id" in msg and "method" not in msg:
            self.responses[int(msg["id"])] = msg
            return
        if "method" not in msg:
            return

        method = msg["method"]
        params = msg.get("params")
        if "id" in msg:
            # Minimal server-request support. clangd may ask for progress token
            # creation or workspace configuration.
            result: Any = None
            if method == "workspace/configuration":
                result = []
            self.send({"jsonrpc": "2.0", "id": msg["id"], "result": result})
            return

        self.notifications.append(msg)
        if method == "$/progress":
            event = params or {}
            self.progress_events.append(event)
            value = event.get("value", {}) if isinstance(event, dict) else {}
            title = str(value.get("title", ""))
            message = str(value.get("message", ""))
            text = f"{title} {message}".lower()
            if value.get("kind") == "begin" and "index" in text and self.index_begin_ts is None:
                self.index_begin_ts = time.monotonic()
            if value.get("kind") == "end" and "index" in text:
                self.index_end_ts = time.monotonic()
        elif method == "textDocument/clangd.fileStatus":
            self.file_status_events.append(params or {})

    def drain(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            msg = self.read_message(timeout=0.2)
            if msg is not None:
                self.handle(msg)


class LogCollector:
    def __init__(self, proc: subprocess.Popen[bytes]):
        self.lines: list[str] = []
        self.index_begin_ts: float | None = None
        self.index_end_ts: float | None = None
        self._thread = threading.Thread(target=self._run, args=(proc,), daemon=True)
        self._thread.start()

    def _run(self, proc: subprocess.Popen[bytes]) -> None:
        assert proc.stderr is not None
        for raw in proc.stderr:
            line = raw.decode("utf-8", errors="replace").rstrip()
            self.lines.append(line)
            lower = line.lower()
            if "backgroundindex" in lower and self.index_begin_ts is None:
                self.index_begin_ts = time.monotonic()
            if "backgroundindex" in lower and (
                "serving version" in lower
                or "indexed" in lower
                or "finished" in lower
                or "queue is empty" in lower
            ):
                self.index_end_ts = time.monotonic()


def location_to_dict(loc: dict[str, Any]) -> dict[str, Any]:
    if "targetUri" in loc:
        path = uri_to_path(loc["targetUri"])
        rng = loc.get("targetSelectionRange") or loc.get("targetRange") or {}
    else:
        path = uri_to_path(loc["uri"])
        rng = loc.get("range") or {}
    start = rng.get("start", {})
    return {
        "path": str(path),
        "repo_path": str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path),
        "line": int(start.get("line", 0)),
        "character": int(start.get("character", 0)),
        "line1": int(start.get("line", 0)) + 1,
        "character1": int(start.get("character", 0)) + 1,
        "snippet": line_snippet(path, int(start.get("line", 0))),
    }


def normalize_locs(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, dict):
        return [location_to_dict(result)]
    if isinstance(result, list):
        return [location_to_dict(item) for item in result if isinstance(item, dict)]
    return []


def line_snippet(path: Path, line: int) -> str:
    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception:
        return ""
    if 0 <= line < len(lines):
        return lines[line].strip()
    return ""


def code_mask(text: str) -> list[bool]:
    mask = [True] * len(text)
    i = 0
    state = "code"
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if ch == "/" and nxt == "/":
                mask[i] = mask[i + 1] = False
                i += 2
                state = "line"
                continue
            if ch == "/" and nxt == "*":
                mask[i] = mask[i + 1] = False
                i += 2
                state = "block"
                continue
            if ch == '"':
                mask[i] = False
                i += 1
                state = "string"
                continue
            if ch == "'":
                mask[i] = False
                i += 1
                state = "char"
                continue
            i += 1
            continue
        if state == "line":
            mask[i] = False
            if ch == "\n":
                state = "code"
            i += 1
            continue
        if state == "block":
            mask[i] = False
            if ch == "*" and nxt == "/":
                mask[i + 1] = False
                i += 2
                state = "code"
                continue
            i += 1
            continue
        if state == "string":
            mask[i] = False
            if ch == "\\" and i + 1 < len(text):
                mask[i + 1] = False
                i += 2
                continue
            if ch == '"':
                state = "code"
            i += 1
            continue
        if state == "char":
            mask[i] = False
            if ch == "\\" and i + 1 < len(text):
                mask[i + 1] = False
                i += 2
                continue
            if ch == "'":
                state = "code"
            i += 1
    return mask


def line_col(text: str, idx: int) -> tuple[int, int]:
    line = text.count("\n", 0, idx)
    last = text.rfind("\n", 0, idx)
    return line, idx if last < 0 else idx - last - 1


def grep_occurrences(symbol: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if path.suffix not in {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp"}:
            continue
        try:
            text = path.read_text(errors="replace")
        except Exception:
            continue
        mask = code_mask(text)
        for match in re.finditer(r"\b" + re.escape(symbol) + r"\b", text):
            if all(mask[i] for i in range(match.start(), match.end())):
                line, col = line_col(text, match.start())
                results.append({
                    "repo_path": str(path.relative_to(REPO_ROOT)),
                    "line1": line + 1,
                    "character1": col + 1,
                    "snippet": line_snippet(path, line),
                })
    return results


def did_open(client: JsonRpcClient, opened: set[Path], path: Path) -> None:
    if path in opened:
        return
    client.notify(
        "textDocument/didOpen",
        {
            "textDocument": {
                "uri": uri(path),
                "languageId": "cpp" if path.suffix in {".cc", ".cpp", ".cxx", ".hh", ".hpp"} else "c",
                "version": 1,
                "text": path.read_text(errors="replace"),
            }
        },
    )
    opened.add(path)


def query_definition(client: JsonRpcClient, sample: dict[str, Any]) -> list[dict[str, Any]]:
    path = REPO_ROOT / sample["file"]
    params = {
        "textDocument": {"uri": uri(path)},
        "position": {"line": sample["line"], "character": sample["character"]},
    }
    return normalize_locs(client.request("textDocument/definition", params, timeout=30.0).get("result"))


def query_references(client: JsonRpcClient, sample: dict[str, Any]) -> list[dict[str, Any]]:
    path = REPO_ROOT / sample["file"]
    params = {
        "textDocument": {"uri": uri(path)},
        "position": {"line": sample["line"], "character": sample["character"]},
        "context": {"includeDeclaration": True},
    }
    return normalize_locs(client.request("textDocument/references", params, timeout=60.0).get("result"))


def main() -> int:
    start = time.monotonic()
    definition_samples = read_sample("definition_sample_semantic.json")
    reference_samples = read_sample("references_sample_semantic.json")

    cmd = [
        "/usr/bin/clangd",
        f"--compile-commands-dir={BUILD_DIR}",
        "--background-index",
        "--log=verbose",
        "--limit-results=1000",
    ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    log = LogCollector(proc)
    client = JsonRpcClient(proc)

    init_started = time.monotonic()
    init_result = client.request(
        "initialize",
        {
            "processId": os.getpid(),
            "rootUri": uri(REPO_ROOT),
            "capabilities": {
                "window": {"workDoneProgress": True},
                "textDocument": {
                    "definition": {"linkSupport": True},
                    "references": {},
                },
            },
            "initializationOptions": {"clangdFileStatus": True},
        },
        timeout=60.0,
    )
    init_finished = time.monotonic()
    client.notify("initialized", {})

    # Give background indexing a chance to start. If clangd sends explicit
    # index progress, wait for its end. Otherwise fall back to a bounded idle
    # window and the query run itself as proof that semantic service is usable.
    index_wait_started = time.monotonic()
    saw_index = False
    while time.monotonic() - index_wait_started < 300:
        client.drain(0.5)
        if client.index_begin_ts or log.index_begin_ts:
            saw_index = True
        if (client.index_end_ts or log.index_end_ts) and time.monotonic() - index_wait_started > 1:
            break
        if not saw_index and time.monotonic() - index_wait_started > 5:
            break

    opened: set[Path] = set()
    for sample in definition_samples + reference_samples:
        did_open(client, opened, REPO_ROOT / sample["file"])
    client.drain(2.0)

    def_results = []
    for sample in definition_samples:
        locs = query_definition(client, sample)
        def_results.append({
            "sample": sample,
            "clangd_locations": locs,
            "grep_occurrences_count": len(grep_occurrences(sample["symbol"])),
        })
        client.drain(0.05)

    ref_results = []
    for sample in reference_samples:
        locs = query_references(client, sample)
        grep = grep_occurrences(sample["symbol"])
        ref_results.append({
            "sample": sample,
            "clangd_locations": locs,
            "clangd_count": len(locs),
            "grep_occurrences_count": len(grep),
            "grep_first_20": grep[:20],
        })
        client.drain(0.05)

    shutdown_result = client.request("shutdown", {}, timeout=10.0)
    client.notify("exit")
    proc.wait(timeout=10)
    max_rss_kb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss

    elapsed = time.monotonic() - start
    index_begin = client.index_begin_ts or log.index_begin_ts
    index_end = client.index_end_ts or log.index_end_ts
    result = {
        "tool": "clangd",
        "command": cmd,
        "repo_root": str(REPO_ROOT),
        "build_dir": str(BUILD_DIR),
        "elapsed_sec": round(elapsed, 3),
        "initialize_sec": round(init_finished - init_started, 3),
        "index_progress_seen": bool(index_begin),
        "index_completed_seen": bool(index_end),
        "index_elapsed_sec": round(index_end - index_begin, 3) if index_begin and index_end else None,
        "max_rss_kb": max_rss_kb,
        "max_rss_mb": round(max_rss_kb / 1024, 1),
        "init_result": init_result.get("result", {}),
        "shutdown_result": shutdown_result.get("result"),
        "progress_events_count": len(client.progress_events),
        "file_status_events_count": len(client.file_status_events),
        "definition_results": def_results,
        "reference_results": ref_results,
    }

    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    bounded_log = "\n".join(log.lines[:120] + (["... bounded log truncated ..."] if len(log.lines) > 160 else []) + log.lines[-40:])
    OUT_LOG.write_text(bounded_log + "\n", encoding="utf-8")
    print(json.dumps({
        "elapsed_sec": result["elapsed_sec"],
        "initialize_sec": result["initialize_sec"],
        "index_progress_seen": result["index_progress_seen"],
        "index_completed_seen": result["index_completed_seen"],
        "index_elapsed_sec": result["index_elapsed_sec"],
        "max_rss_mb": result["max_rss_mb"],
        "definition_queries": len(def_results),
        "reference_queries": len(ref_results),
        "out_json": str(OUT_JSON),
        "out_log": str(OUT_LOG),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
