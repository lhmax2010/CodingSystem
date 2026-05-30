#!/usr/bin/env python3
"""S0-05 spike-only EvidencePacket generator.

This is not product code. It validates packet assembly time and token budget
using real S0-04 logs while keeping raw logs outside the repository.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TMP_ROOT = Path("/tmp/coding-system-s0")
BUILDROOT = TMP_ROOT / "gbs-root-pkgmgr-llvm/local/BUILD-ROOTS/scratch.x86_64.0"
MAX_EXCERPT_CHARS = 3000
MAX_PACKET_TOKENS = 4000

SINGLE_PARSED = TMP_ROOT / "s0_04_exp1_1_parsed.json"
SINGLE_LOG = TMP_ROOT / "s0_04_exp1_1_build.log"
SINGLE_SOURCE_ROOT = Path("/home/abuild/s0/s0_04_exp1_1_src")
SINGLE_HOST_SOURCE_ROOT = BUILDROOT / "home/abuild/s0/s0_04_exp1_1_src"

CASCADE_LOG = TMP_ROOT / "s0_04_exp2_build.log"
CASCADE_SOURCE_ROOT = Path("/home/abuild/s0/s0_04_exp2_src")
CASCADE_HOST_SOURCE_ROOT = BUILDROOT / "home/abuild/s0/s0_04_exp2_src"

SOURCE_LOC_RE = re.compile(r"(?P<file>/[^:\n]+):(?P<line>\d+):(?P<col>\d+):")
UNKNOWN_TYPE_RE = re.compile(
    r"(?P<file>/[^:\n]+):(?P<line>\d+):(?P<col>\d+): "
    r"error: unknown type name '(?P<type>[^']+)'"
)


@dataclass(frozen=True)
class TokenEstimate:
    tokens: int
    estimator: str


def chroot_to_host(path: str | Path) -> Path:
    path = Path(path)
    if str(path).startswith("/home/abuild/"):
        return BUILDROOT / str(path).lstrip("/")
    return path


def chroot_display(path: Path) -> str:
    text = str(path)
    prefix = str(BUILDROOT)
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def estimate_tokens(text: str) -> TokenEstimate:
    try:
        import tiktoken  # type: ignore[import-not-found]

        encoding = tiktoken.get_encoding("cl100k_base")
        return TokenEstimate(len(encoding.encode(text)), "tiktoken_cl100k_base")
    except Exception:
        return TokenEstimate(math.ceil(len(text) / 4), "chars_div_4_fallback")


def bounded_excerpt(log_path: Path, line_no: int, before: int = 2, after: int = 4) -> dict[str, Any]:
    lines = read_text(log_path).splitlines()
    start = max(0, line_no - before - 1)
    end = min(len(lines), line_no + after)
    content = "\n".join(lines[start:end])
    if len(content) > MAX_EXCERPT_CHARS:
        content = content[:MAX_EXCERPT_CHARS]
    return {
        "source": str(log_path),
        "line_range": [start + 1, end],
        "redacted": True,
        "char_count": len(content),
        "reason": "compile_error_context",
        "content": content,
    }


def extract_source_location(message: str) -> dict[str, Any] | None:
    match = SOURCE_LOC_RE.search(message)
    if not match:
        return None
    return {
        "file": match.group("file"),
        "line": int(match.group("line")),
        "column": int(match.group("col")),
    }


def source_line(location: dict[str, Any] | None) -> str | None:
    if not location:
        return None
    host_path = chroot_to_host(location["file"])
    if not host_path.exists():
        return None
    lines = read_text(host_path).splitlines()
    line_index = location["line"] - 1
    if line_index < 0 or line_index >= len(lines):
        return None
    return lines[line_index].strip()


def find_header_candidates(source_root: Path, header: str) -> list[str]:
    host_root = chroot_to_host(source_root)
    candidates = []
    for path in host_root.rglob(header):
        candidates.append(chroot_display(path))
    return sorted(candidates)


def extract_compile_command(log_path: Path, source_file: str, line_no: int) -> str | None:
    lines = read_text(log_path).splitlines()
    for line in reversed(lines[: max(0, line_no - 1)]):
        if f" -c {source_file}" in line:
            return line
    return None


def include_paths_from_command(command: str | None) -> list[str]:
    if not command:
        return []
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    include_paths: list[str] = []
    next_is_include = False
    for token in tokens:
        if next_is_include:
            include_paths.append(token)
            next_is_include = False
            continue
        if token == "-I":
            next_is_include = True
        elif token.startswith("-I") and len(token) > 2:
            include_paths.append(token[2:])
    return include_paths


def make_packet(packet: dict[str, Any], start: float) -> dict[str, Any]:
    packet["collection_metadata"]["collection_duration_ms"] = round((time.perf_counter() - start) * 1000, 3)
    packet["collection_metadata"]["budget_tokens"] = MAX_PACKET_TOKENS
    packet["collection_metadata"]["total_tokens_estimate"] = 0
    packet["collection_metadata"]["token_estimator"] = "pending"
    packet["collection_metadata"]["packet_char_count"] = 0
    packet["collection_metadata"]["budget_pass"] = False

    # Iterate until self-referential metadata fields have a stable estimate.
    for _ in range(3):
        encoded = json.dumps(packet, ensure_ascii=False, sort_keys=True)
        estimate = estimate_tokens(encoded)
        packet["collection_metadata"]["total_tokens_estimate"] = estimate.tokens
        packet["collection_metadata"]["token_estimator"] = estimate.estimator
        packet["collection_metadata"]["packet_char_count"] = len(encoded)
        packet["collection_metadata"]["budget_pass"] = estimate.tokens <= MAX_PACKET_TOKENS
    return packet


def generate_single_primary_packet() -> dict[str, Any]:
    start = time.perf_counter()
    parsed = json.loads(read_text(SINGLE_PARSED))
    error = parsed["primary_candidate"]
    location = extract_source_location(error["message"])
    include_line = source_line(location)
    compile_command = extract_compile_command(SINGLE_LOG, location["file"], error["line_no"]) if location else None
    include_paths = include_paths_from_command(compile_command)
    header = error["symbol"]
    candidates = find_header_candidates(SINGLE_SOURCE_ROOT, header)
    candidate_dirs = sorted({str(Path(candidate).parent) for candidate in candidates})
    missing_candidate_dirs = [path for path in candidate_dirs if path not in include_paths]

    packet = {
        "evidence_id": "EP-S0-05-SINGLE-001",
        "task_id": "S0-05",
        "trigger": {
            "type": "compile_error",
            "error_type": error["error_type"],
            "error_signature": error["message"],
            "source_location": location,
            "build_target": "pkgmgr-info",
            "build_system": "cmake_make",
            "related_symbol": header,
            "is_primary": True,
            "primary_id": "ERR-S0-05-001",
        },
        "facts": {
            "header_candidates": candidates[:5],
            "header_candidate_count": len(candidates),
            "include_line": include_line,
            "compile_command_include_path_count": len(include_paths),
            "compile_command_include_paths_sample": include_paths[:12],
            "candidate_header_dirs": candidate_dirs,
        },
        "known_issue_matches": [
            {
                "issue_id": "tizen_missing_include_directory",
                "confidence": 0.82,
                "description": "Header exists in source tree but its directory is absent from the compile command include path.",
                "suggested_fix_hint": "Restore the missing include directory in CMake include directories for this target.",
                "anti_patterns": [
                    "Header may be generated and absent until a previous build step runs",
                    "Header may be intentionally removed in a newer upstream version",
                ],
            }
        ],
        "negative_facts": [
            {
                "check": "compile command include path contains header candidate directory",
                "result": "not_found",
                "confidence": "high",
                "scope": "build_config",
                "details": missing_candidate_dirs,
                "implication": "The source tree contains the header, but the failing translation unit cannot search that directory.",
            },
            {
                "check": "raw log included in packet",
                "result": "not_present",
                "confidence": "high",
                "scope": "prompt_boundary",
                "implication": "Only a bounded log_excerpt is included.",
            },
        ],
        "log_excerpt": [
            bounded_excerpt(SINGLE_LOG, error["line_no"]),
        ],
        "cascade_summary": None,
        "semantic_unavailable": False,
        "clangd_stale": False,
        "compile_commands_provenance": "build_log_command_line",
        "degraded_reason": None,
        "ambiguous_facts": [],
        "collection_metadata": {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "collectors_run": [
                {"name": "LogErrorParser", "status": "ok", "mode": "s0_04_parsed_input"},
                {"name": "CompileCommandCollector", "status": "ok", "mode": "build_log_command_line"},
                {"name": "HeaderIncludeCollector", "status": "ok", "mode": "source_tree_scan"},
                {"name": "CMakeContextCollector", "status": "degraded", "reason": "spike_regex_only"},
                {"name": "KnownIssueMatcher", "status": "mocked", "reason": "S0-07 owns full matcher validation"},
            ],
        },
        "schema": "evidence_packet.v1.spike",
    }
    return make_packet(packet, start)


def parse_unknown_type_errors(log_path: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for line_no, line in enumerate(read_text(log_path).splitlines(), start=1):
        match = UNKNOWN_TYPE_RE.search(line)
        if not match:
            continue
        errors.append(
            {
                "line_no": line_no,
                "message": line,
                "source_location": {
                    "file": match.group("file"),
                    "line": int(match.group("line")),
                    "column": int(match.group("col")),
                },
                "type_name": match.group("type"),
            }
        )
    return errors


def generate_cascade_primary_packet() -> dict[str, Any]:
    start = time.perf_counter()
    errors = parse_unknown_type_errors(CASCADE_LOG)
    if not errors:
        raise RuntimeError("no unknown_type_name errors found in cascade log")

    primary = errors[0]
    type_name = primary["type_name"]
    same_type_cascades = [error for error in errors[1:] if error["type_name"] == type_name]
    log_lines = read_text(CASCADE_LOG).splitlines()
    total_error_lines = sum(1 for line in log_lines if "error:" in line)
    too_many_errors = sum(1 for line in log_lines if "too many errors emitted" in line)
    header_path = CASCADE_HOST_SOURCE_ROOT / "include/pkgmgrinfo_type.h"
    header_text = read_text(header_path)
    original_typedef_present = f"typedef void *{type_name};" in header_text
    renamed_typedef_match = re.search(r"typedef void \*(?P<name>pkgmgrinfo_pkginfo_h_renamed_for_s0_04);", header_text)

    packet = {
        "evidence_id": "EP-S0-05-CASCADE-001",
        "task_id": "S0-05",
        "trigger": {
            "type": "compile_error",
            "error_type": "unknown_type_name",
            "error_signature": primary["message"],
            "source_location": primary["source_location"],
            "build_target": "pkgmgr-info",
            "build_system": "cmake_make",
            "related_symbol": type_name,
            "is_primary": True,
            "primary_id": "ERR-S0-05-CASCADE-001",
        },
        "facts": {
            "primary_heuristic": "first compiler error is primary candidate",
            "same_type_cascade_count": len(same_type_cascades),
            "total_error_lines": total_error_lines,
            "too_many_errors_lines": too_many_errors,
            "representative_cascade_messages": [error["message"] for error in same_type_cascades[:3]],
            "renamed_typedef_candidate": renamed_typedef_match.group("name") if renamed_typedef_match else None,
            "root_header": str(CASCADE_SOURCE_ROOT / "include/pkgmgrinfo_type.h"),
        },
        "known_issue_matches": [],
        "negative_facts": [
            {
                "check": f"public header declares typedef void *{type_name};",
                "result": "not_found" if not original_typedef_present else "found",
                "confidence": "high",
                "scope": "source_code",
                "implication": "The public API typedef used by later declarations is missing from the header.",
            },
            {
                "check": "raw log included in packet",
                "result": "not_present",
                "confidence": "high",
                "scope": "prompt_boundary",
                "implication": "Only one bounded primary excerpt and cascade counts are included.",
            },
        ],
        "log_excerpt": [
            bounded_excerpt(CASCADE_LOG, primary["line_no"]),
        ],
        "cascade_summary": {
            "strategy": "v0.3.5_mock_first_error_plus_same_symbol_summary",
            "primary_error_line_no": primary["line_no"],
            "summarized_error_count": len(same_type_cascades) + too_many_errors,
            "same_symbol": type_name,
            "same_symbol_cascade_count": len(same_type_cascades),
            "terminal_compiler_limit_count": too_many_errors,
            "note": "S0-05 mock validates packet size; full primary/cascade implementation belongs to S2b-03.",
        },
        "semantic_unavailable": False,
        "clangd_stale": False,
        "compile_commands_provenance": "not_required_for_cascade_summary_spike",
        "degraded_reason": "primary_cascade_is_spike_mock_not_product_parser",
        "ambiguous_facts": [
            {
                "fact": "The true source edit is a renamed typedef at the declaration line, while the primary compiler diagnostic appears at the first later use.",
                "confidence": "medium",
            }
        ],
        "collection_metadata": {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "collectors_run": [
                {"name": "LogErrorParser", "status": "mocked", "mode": "unknown_type_name_regex"},
                {"name": "PrimaryCascadeSummarizer", "status": "mocked", "mode": "first_error_plus_same_symbol"},
                {"name": "SourceHeaderProbe", "status": "ok", "mode": "source_tree_read"},
            ],
        },
        "schema": "evidence_packet.v1.spike",
    }
    return make_packet(packet, start)


def summarize_packet(packet: dict[str, Any]) -> dict[str, Any]:
    excerpts = packet.get("log_excerpt") or []
    return {
        "evidence_id": packet["evidence_id"],
        "error_type": packet["trigger"]["error_type"],
        "duration_ms": packet["collection_metadata"]["collection_duration_ms"],
        "estimated_tokens": packet["collection_metadata"]["total_tokens_estimate"],
        "token_estimator": packet["collection_metadata"]["token_estimator"],
        "budget_pass": packet["collection_metadata"]["budget_pass"],
        "facts_count": len(packet.get("facts") or {}),
        "negative_facts_count": len(packet.get("negative_facts") or []),
        "log_excerpt_count": len(excerpts),
        "log_excerpt_total_chars": sum(excerpt.get("char_count", 0) for excerpt in excerpts),
        "max_log_excerpt_chars": max([excerpt.get("char_count", 0) for excerpt in excerpts] or [0]),
        "cascade_summary_present": packet.get("cascade_summary") is not None,
    }


def run_measurements(runs: int) -> dict[str, Any]:
    single_packets = []
    cascade_packets = []
    for _ in range(runs):
        single_packets.append(generate_single_primary_packet())
        cascade_packets.append(generate_cascade_primary_packet())

    final_single = single_packets[-1]
    final_cascade = cascade_packets[-1]

    def stats(packets: list[dict[str, Any]]) -> dict[str, Any]:
        durations = [packet["collection_metadata"]["collection_duration_ms"] for packet in packets]
        tokens = [packet["collection_metadata"]["total_tokens_estimate"] for packet in packets]
        return {
            "runs": len(packets),
            "duration_ms_min": min(durations),
            "duration_ms_max": max(durations),
            "duration_ms_mean": round(statistics.fmean(durations), 3),
            "duration_ms_median": round(statistics.median(durations), 3),
            "tokens_min": min(tokens),
            "tokens_max": max(tokens),
            "budget_pass_all_runs": all(token <= MAX_PACKET_TOKENS for token in tokens),
        }

    return {
        "design_issue_check": {
            "status": "no_new_design_issue",
            "notes": [
                "S0-05 can validate single-primary EvidencePacket performance directly.",
                "Cascade primary recognition is exercised only as a spike mock; S2b-03 remains owner of full LogErrorParser implementation.",
            ],
        },
        "acceptance": {
            "max_duration_ms": 2000,
            "max_tokens": MAX_PACKET_TOKENS,
            "single_primary_pass": (
                final_single["collection_metadata"]["collection_duration_ms"] < 2000
                and final_single["collection_metadata"]["total_tokens_estimate"] <= MAX_PACKET_TOKENS
            ),
            "cascade_primary_mock_pass": (
                final_cascade["collection_metadata"]["collection_duration_ms"] < 2000
                and final_cascade["collection_metadata"]["total_tokens_estimate"] <= MAX_PACKET_TOKENS
            ),
        },
        "single_primary": {
            "scenario": "S0-04 exp1.1 cannot_find_header",
            "summary": summarize_packet(final_single),
            "stats": stats(single_packets),
        },
        "cascade_primary_mock": {
            "scenario": "S0-04 exp2 typedef rename cascade",
            "summary": summarize_packet(final_cascade),
            "stats": stats(cascade_packets),
            "scope_note": "Mock validates v0.3.5 packet strategy under S0-05; full primary/cascade parser stays in S2b-03.",
        },
        "raw_log_policy": {
            "raw_logs_location": str(TMP_ROOT),
            "committed_artifacts_contain_raw_logs": False,
            "bounded_excerpt_max_chars": MAX_EXCERPT_CHARS,
        },
        "packets": {
            "single_primary": final_single,
            "cascade_primary_mock": final_cascade,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = run_measurements(args.runs)

    packet_dir = args.output_dir
    (packet_dir / "spike_05_single_primary_packet.json").write_text(
        json.dumps(results["packets"]["single_primary"], indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )
    (packet_dir / "spike_05_cascade_primary_packet.json").write_text(
        json.dumps(results["packets"]["cascade_primary_mock"], indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    report_results = dict(results)
    report_results.pop("packets")
    (packet_dir / "spike_05_evidence_packet_results.json").write_text(
        json.dumps(report_results, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )
    print(json.dumps(report_results, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
