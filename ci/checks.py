"""Run content and dependency inspections using explicit policy inputs."""

from __future__ import annotations

import importlib.metadata as metadata
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

from ci.d23 import POLICY_VERSION, SIGNALS, check_file, digest, php_package
from ci.installed import unlisted_files


def git(*args: str) -> bytes:
    """Read Git output without a shell."""
    return subprocess.check_output(["git", *args])


def repository_files() -> list[Path]:
    """Include tracked and nonignored new files, excluding removed paths."""
    names = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted(
        {
            Path(name.decode())
            for name in names.split(b"\0")
            if name and (Path(name.decode()).exists() or Path(name.decode()).is_symlink())
        }
    )


def json_file(path: str) -> dict[str, Any]:
    """Load a checked-in policy object."""
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise ValueError("Policy must be an object")
    return cast(dict[str, Any], value)


def content_hits(data: bytes, rules: dict[str, str]) -> list[tuple[str, int]]:
    """Return rule identifiers and line numbers without exposing matched content."""
    text = data.decode("utf-8", errors="replace")
    return [
        (name, text.count("\n", 0, match.start()) + 1)
        for name, pattern in rules.items()
        for match in re.finditer(pattern, text)
    ]


def check_content() -> int:
    """Reject current content violations unless an exact reviewed exception matches."""
    policy = json_file("ci/content_policy.json")
    exceptions = json_file("ci/content_exemptions.json")
    if policy["version"] != exceptions["version"]:
        raise ValueError("Content policy version mismatch")
    failures = 0
    for path in repository_files():
        for rule, line in content_hits(path.read_bytes(), policy["rules"]):
            matching = [
                entry
                for entry in exceptions["entries"]
                if entry["path"] == str(path)
                and entry["rule"] == rule
                and entry["line"] == line
                and entry.get("reason")
                and entry.get("digest") == digest(path.read_bytes())
            ]
            if not matching:
                print(f"CONTENT_FAIL {path}:{line} {rule}")
                failures += 1
    print(f"Current content findings: {failures}")
    return int(failures != 0)


def check_content_stdin() -> int:
    """Scan input without file-based exemptions or disclosing matched text."""
    hits = content_hits(sys.stdin.buffer.read(), json_file("ci/content_policy.json")["rules"])
    for rule, line in hits:
        print(f"CONTENT_STDIN_FAIL line={line} rule={rule}")
    return int(bool(hits))


def historical_content() -> int:
    """Scan each reachable historical blob once, retaining commit/path provenance."""
    rules = json_file("ci/content_policy.json")["rules"]
    seen: set[str] = set()
    findings: list[str] = []
    commits = git("rev-list", "--all").decode().splitlines()
    for commit in commits:
        for row in git("ls-tree", "-r", "-z", commit).split(b"\0"):
            if not row:
                continue
            header, name = row.split(b"\t", 1)
            _, kind, oid = header.decode().split()
            if kind != "blob" or oid in seen:
                continue
            seen.add(oid)
            data = git("cat-file", "blob", oid)
            for rule, line in content_hits(data, rules):
                findings.append(f"{commit} {oid} {name.decode()}:{line} {rule}")
    print(
        f"Historical commits: {len(commits)}; unique blobs: {len(seen)}; findings: {len(findings)}"
    )
    print("Matched values omitted; each blob is attributed to its first visited commit/path.")
    for finding in findings:
        print(finding)
    return 0  # Historical findings are report-only by task-001 authorization.


def check_d23() -> int:
    """Inspect repository content, all lock names and installed distribution files."""
    policy = json_file("ci/d23_policy.json")
    if policy["version"] != POLICY_VERSION or policy["parsers"] != {".py": "python-ast-tokenize"}:
        raise ValueError("D23 policy version or parser mismatch")
    if policy["signatures"] != list(SIGNALS):
        raise ValueError("D23 signature mismatch")
    scanner = json_file("ci/d23_scanner_digests.json")
    if scanner["version"] != POLICY_VERSION:
        raise ValueError("D23 digest policy version mismatch")
    failures: list[str] = []
    for path in repository_files():
        for reason in check_file(
            path,
            pure_data_digest=policy["pure_data"].get(str(path)),
            scanner_digest=scanner["files"].get(str(path)),
            executable_input=str(path) in policy["executable_inputs"],
        ):
            failures.append(f"{path}: {reason}")
    lock = tomllib.loads(Path("uv.lock").read_text())
    for package in lock["package"]:
        if php_package(package["name"]):
            failures.append(f"lock: {package['name']}: php_metadata")
    installed = 0
    owned: set[Path] = set()
    for distribution in metadata.distributions():
        installed += 1
        name = distribution.metadata["Name"]
        names = [name, *(re.split(r"[\s(;[<>=!~]", req)[0] for req in distribution.requires or [])]
        if any(php_package(item) for item in names):
            failures.append(f"distribution: {name}: php_metadata")
        if distribution.files is None:
            failures.append(f"distribution: {name}: missing_file_inventory")
            continue
        for relative in distribution.files:
            path = Path(str(distribution.locate_file(relative)))
            owned.add(path.resolve())
            if not path.exists():
                failures.append(f"distribution: {name}: missing_file {relative}")
                continue
            for reason in check_file(path):
                failures.append(f"distribution: {name}/{relative}: {reason}")
    failures.extend(unlisted_files(Path(sys.prefix), owned))
    for failure in failures:
        print(f"D23_FAIL {failure}")
    print(f"D23 installed distributions: {installed}; failures: {len(failures)}")
    return int(bool(failures))


def main() -> int:
    """Dispatch only explicit inspection commands."""
    from ci.registrations import check_bypass, check_provisional

    actions = {
        "content": check_content,
        "content-stdin": check_content_stdin,
        "history": historical_content,
        "d23": check_d23,
        "bypass": check_bypass,
        "provisional": check_provisional,
    }
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        print("Usage: python -m ci.checks " + "|".join(actions))
        return 2
    return actions[sys.argv[1]]()


if __name__ == "__main__":
    raise SystemExit(main())
