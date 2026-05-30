#!/usr/bin/env python3
"""S0-09 stale compile_commands confidence downgrade spike.

This is Sprint 0 spike code only. It validates CNEI v0.3.5 Section 4.3.2.1:
when compile_commands.json is older than any CMakeLists.txt, only clangd facts
are downgraded from high to medium and tagged with
confidence_modifier="stale_compile_commands".
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


TMP_ROOT = Path("/tmp/coding-system-s0")
SOURCE_REPO = TMP_ROOT / "repos/pkgmgr-info"
COMPILE_COMMANDS_SOURCE = (
    TMP_ROOT
    / "gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/s0/build-s0-02/compile_commands.json"
)
WORK_ROOT = TMP_ROOT / "s0_09"
SYMBOL = "pkgmgrinfo_pkginfo_h"


@dataclass(frozen=True)
class BackendSelection:
    backend: str
    provenance: str
    clangd_stale: bool
    stale_reason: str | None
    compile_commands_mtime: float | None
    newest_cmake_mtime: float | None
    newest_cmake_path: str | None


@dataclass
class Fact:
    fact_id: str
    source: str
    kind: str
    symbol: str
    location: str
    confidence: str
    confidence_modifier: str | None = None
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = {
            "fact_id": self.fact_id,
            "source": self.source,
            "kind": self.kind,
            "symbol": self.symbol,
            "location": self.location,
            "confidence": self.confidence,
        }
        if self.confidence_modifier is not None:
            data["confidence_modifier"] = self.confidence_modifier
        if self.note is not None:
            data["note"] = self.note
        return data


def copytree_clean(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git"))


def set_all_cmake_mtime(repo_root: Path, mtime: float) -> None:
    for cmake_file in repo_root.rglob("CMakeLists.txt"):
        os.utime(cmake_file, (mtime, mtime))


def prepare_workspace(name: str, *, stale: bool) -> dict[str, Any]:
    if not SOURCE_REPO.exists():
        raise FileNotFoundError(SOURCE_REPO)
    if not COMPILE_COMMANDS_SOURCE.exists():
        raise FileNotFoundError(COMPILE_COMMANDS_SOURCE)

    root = WORK_ROOT / name
    repo = root / "pkgmgr-info"
    build = root / "build"
    copytree_clean(SOURCE_REPO, repo)
    if build.exists():
        shutil.rmtree(build)
    build.mkdir(parents=True)
    compile_commands = build / "compile_commands.json"
    shutil.copy2(COMPILE_COMMANDS_SOURCE, compile_commands)

    now = time.time()
    old = now - 3600
    newer = now + 10

    set_all_cmake_mtime(repo, old)
    os.utime(compile_commands, (now, now))

    modified_file = None
    if stale:
        modified_file = repo / "CMakeLists.txt"
        with modified_file.open("a", encoding="utf-8") as stream:
            stream.write("\n# S0-09 stale detection marker: CMake changed after compile_commands.json\n")
        os.utime(modified_file, (newer, newer))

    return {
        "repo_root": repo,
        "compile_commands": compile_commands,
        "modified_file": modified_file,
        "scenario": "stale_true" if stale else "stale_false",
    }


def newest_cmake(repo_root: Path) -> tuple[Path | None, float | None]:
    newest_path = None
    newest_mtime = None
    for cmake_file in repo_root.rglob("CMakeLists.txt"):
        mtime = cmake_file.stat().st_mtime
        if newest_mtime is None or mtime > newest_mtime:
            newest_path = cmake_file
            newest_mtime = mtime
    return newest_path, newest_mtime


def path_is_stale(compile_commands: Path, repo_root: Path) -> tuple[bool, str | None, Path | None, float | None, float | None]:
    cc_mtime = compile_commands.stat().st_mtime
    newest_path, newest_mtime = newest_cmake(repo_root)
    if newest_mtime is None:
        return False, None, newest_path, cc_mtime, newest_mtime
    if cc_mtime < newest_mtime:
        return (
            True,
            "compile_commands.json older than newest CMakeLists.txt",
            newest_path,
            cc_mtime,
            newest_mtime,
        )
    return False, None, newest_path, cc_mtime, newest_mtime


def select_backend(repo_root: Path, compile_commands: Path, build_system: str | None) -> BackendSelection:
    if build_system != "cmake_ninja":
        return BackendSelection(
            backend="DegradedBackend",
            provenance="auto_degraded",
            clangd_stale=False,
            stale_reason=f"build_system_{build_system or 'unknown'}_not_cmake_ninja",
            compile_commands_mtime=None,
            newest_cmake_mtime=None,
            newest_cmake_path=None,
        )
    stale, reason, newest_path, cc_mtime, newest_mtime = path_is_stale(compile_commands, repo_root)
    return BackendSelection(
        backend="ClangdBackend",
        provenance="auto_cmake_ninja",
        clangd_stale=stale,
        stale_reason=reason,
        compile_commands_mtime=cc_mtime,
        newest_cmake_mtime=newest_mtime,
        newest_cmake_path=str(newest_path) if newest_path else None,
    )


def find_symbol_locations(repo_root: Path) -> dict[str, str]:
    definition = None
    reference = None
    for path in sorted(repo_root.rglob("*")):
        if path.is_dir() or path.suffix not in {".h", ".hh", ".c", ".cc", ".cpp"}:
            continue
        for index, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
            if f"typedef void *{SYMBOL};" in line and definition is None:
                definition = f"{path.relative_to(repo_root)}:{index}"
            elif SYMBOL in line and "typedef void *" not in line and reference is None:
                reference = f"{path.relative_to(repo_root)}:{index}"
        if definition and reference:
            break
    return {
        "definition": definition or "include/pkgmgrinfo_type.h:188",
        "reference": reference or "include/pkgmgr-info.h:297",
    }


def base_facts(repo_root: Path) -> list[Fact]:
    locations = find_symbol_locations(repo_root)
    return [
        Fact(
            fact_id="F-CLANGD-DEF",
            source="clangd",
            kind="symbol_definition",
            symbol=SYMBOL,
            location=locations["definition"],
            confidence="high",
            note="semantic definition from clangd",
        ),
        Fact(
            fact_id="F-CLANGD-REF",
            source="clangd",
            kind="symbol_reference",
            symbol=SYMBOL,
            location=locations["reference"],
            confidence="high",
            note="semantic reference from clangd",
        ),
        Fact(
            fact_id="F-TREESITTER-CONTEXT",
            source="tree-sitter",
            kind="syntax_context",
            symbol=SYMBOL,
            location=locations["reference"],
            confidence="medium",
            note="syntax-only fact; does not depend on compile_commands.json",
        ),
        Fact(
            fact_id="F-CTAGS-CANDIDATE",
            source="ctags",
            kind="symbol_candidate",
            symbol=SYMBOL,
            location=locations["definition"],
            confidence="medium",
            note="name-based index fact; does not depend on compile_commands.json",
        ),
        Fact(
            fact_id="F-RIPGREP-TEXT",
            source="ripgrep",
            kind="text_match",
            symbol=SYMBOL,
            location=locations["reference"],
            confidence="low",
            note="text search fact; does not depend on compile_commands.json",
        ),
    ]


def apply_stale_policy(facts: list[Fact], backend: BackendSelection) -> list[Fact]:
    adjusted: list[Fact] = []
    for fact in facts:
        copy = Fact(**fact.as_dict())
        if backend.clangd_stale and copy.source == "clangd":
            copy.confidence = "medium"
            copy.confidence_modifier = "stale_compile_commands"
        adjusted.append(copy)
    return adjusted


def evidence_packet_for_scenario(name: str, workspace: dict[str, Any]) -> dict[str, Any]:
    repo_root: Path = workspace["repo_root"]
    compile_commands: Path = workspace["compile_commands"]
    backend = select_backend(repo_root, compile_commands, "cmake_ninja")
    facts = apply_stale_policy(base_facts(repo_root), backend)
    return {
        "evidence_id": f"EP-S0-09-{name.upper()}",
        "task_id": "S0-09",
        "trigger": {
            "type": "stale_detection_spike",
            "symbol": SYMBOL,
            "build_system": "cmake_ninja",
        },
        "facts": [fact.as_dict() for fact in facts],
        "clangd_stale": backend.clangd_stale,
        "compile_commands_provenance": backend.provenance,
        "semantic_unavailable": backend.backend != "ClangdBackend",
        "degraded_reason": None if backend.backend == "ClangdBackend" else backend.stale_reason,
        "stale_detection": {
            "backend": backend.backend,
            "compile_commands_path": str(compile_commands),
            "compile_commands_mtime": backend.compile_commands_mtime,
            "newest_cmake_path": backend.newest_cmake_path,
            "newest_cmake_mtime": backend.newest_cmake_mtime,
            "stale_reason": backend.stale_reason,
            "modified_file": str(workspace["modified_file"]) if workspace.get("modified_file") else None,
        },
        "schema": "evidence_packet.v1.spike",
    }


def summarize_packet(packet: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for fact in packet["facts"]:
        rows.append(
            {
                "fact_id": fact["fact_id"],
                "source": fact["source"],
                "confidence": fact["confidence"],
                "confidence_modifier": fact.get("confidence_modifier"),
            }
        )
    clangd_facts = [fact for fact in packet["facts"] if fact["source"] == "clangd"]
    non_clangd_facts = [fact for fact in packet["facts"] if fact["source"] != "clangd"]
    return {
        "evidence_id": packet["evidence_id"],
        "clangd_stale": packet["clangd_stale"],
        "compile_commands_provenance": packet["compile_commands_provenance"],
        "clangd_fact_confidences": [fact["confidence"] for fact in clangd_facts],
        "clangd_fact_modifiers": [fact.get("confidence_modifier") for fact in clangd_facts],
        "non_clangd_fact_confidences": {
            fact["source"]: fact["confidence"] for fact in non_clangd_facts
        },
        "rows": rows,
    }


def compare_packets(fresh: dict[str, Any], stale: dict[str, Any]) -> dict[str, Any]:
    fresh_by_id = {fact["fact_id"]: fact for fact in fresh["facts"]}
    stale_by_id = {fact["fact_id"]: fact for fact in stale["facts"]}
    comparisons = []
    for fact_id, fresh_fact in fresh_by_id.items():
        stale_fact = stale_by_id[fact_id]
        comparisons.append(
            {
                "fact_id": fact_id,
                "source": fresh_fact["source"],
                "fresh_confidence": fresh_fact["confidence"],
                "fresh_modifier": fresh_fact.get("confidence_modifier"),
                "stale_confidence": stale_fact["confidence"],
                "stale_modifier": stale_fact.get("confidence_modifier"),
                "changed": (
                    fresh_fact["confidence"] != stale_fact["confidence"]
                    or fresh_fact.get("confidence_modifier") != stale_fact.get("confidence_modifier")
                ),
            }
        )
    return {
        "comparisons": comparisons,
        "clangd_only_downgraded": all(
            row["changed"] == (row["source"] == "clangd") for row in comparisons
        ),
        "all_clangd_medium_when_stale": all(
            row["stale_confidence"] == "medium" and row["stale_modifier"] == "stale_compile_commands"
            for row in comparisons
            if row["source"] == "clangd"
        ),
        "all_non_clangd_unchanged": all(
            not row["changed"] for row in comparisons if row["source"] != "clangd"
        ),
    }


def run(output_dir: Path) -> dict[str, Any]:
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    fresh_ws = prepare_workspace("fresh", stale=False)
    stale_ws = prepare_workspace("stale", stale=True)

    fresh_packet = evidence_packet_for_scenario("fresh", fresh_ws)
    stale_packet = evidence_packet_for_scenario("stale", stale_ws)
    comparison = compare_packets(fresh_packet, stale_packet)

    benchmark_backend = select_backend(stale_ws["repo_root"], stale_ws["compile_commands"], None)
    benchmark_note = {
        "backend": benchmark_backend.backend,
        "provenance": benchmark_backend.provenance,
        "clangd_stale": benchmark_backend.clangd_stale,
        "reason": benchmark_backend.stale_reason,
        "scope": "documented only; S0-09 validates Compiler Agent path",
    }

    result = {
        "scope": {
            "task": "S0-09",
            "agent_path": "Compiler Agent only",
            "benchmark_path": "not under test; build_system=None degrades before clangd",
            "source_repo": str(SOURCE_REPO),
            "compile_commands_source": str(COMPILE_COMMANDS_SOURCE),
            "work_root": str(WORK_ROOT),
        },
        "scenarios": {
            "fresh": summarize_packet(fresh_packet),
            "stale": summarize_packet(stale_packet),
        },
        "mtime_checks": {
            "fresh": fresh_packet["stale_detection"],
            "stale": stale_packet["stale_detection"],
        },
        "comparison": comparison,
        "benchmark_path_note": benchmark_note,
        "decision_pending_user_review": True,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "spike_09_fresh_packet.json").write_text(
        json.dumps(fresh_packet, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "spike_09_stale_packet.json").write_text(
        json.dumps(stale_packet, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "spike_09_stale_detection_results.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
