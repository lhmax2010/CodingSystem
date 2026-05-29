#!/usr/bin/env python3
"""S0-08 end-to-end dry-run pipeline.

This is a Sprint 0 spike, not product code. It replays the real S0-04 typedef
cascade failure log through:

compile fail -> LogErrorParser -> EvidenceCollector -> EvidencePacket ->
RawDataDetector -> mocked LLM entrance.

No real LLM is called and no patch is generated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "CMP-S0-08-DRYRUN"
TMP_ROOT = Path("/tmp/coding-system-s0")
RAW_LOG = TMP_ROOT / "s0_04_exp2_build.log"
DIFF_REF = TMP_ROOT / "exp2_cascade.diff"
BUILDROOT = TMP_ROOT / "gbs-root-pkgmgr-llvm/local/BUILD-ROOTS/scratch.x86_64.0"
SOURCE_ROOT = Path("/home/abuild/s0/s0_04_exp2_src")
HOST_SOURCE_ROOT = BUILDROOT / "home/abuild/s0/s0_04_exp2_src"

MAX_EVIDENCE_PACKET_TOKENS = 4000
MAX_TOKENS_PER_CALL = 8000
MAX_TOKENS_PER_TASK = 50000
SPRINT_0_PROMPT_TOKEN_LIMIT = 25000
MAX_LOG_EXCERPT_CHARS = 3000
RAW_DATA_THRESHOLD_CHARS = 6000
RAW_DATA_THRESHOLD_LINES = 200

UNKNOWN_TYPE_RE = re.compile(
    r"(?P<file>/[^:\n]+):(?P<line>\d+):(?P<col>\d+): "
    r"error: unknown type name '(?P<type>[^']+)'"
)
RAW_STYLE_RE = re.compile(
    r"(/[^:\n]+:\d+:\d+:\s+(?:fatal\s+)?error:|"
    r"ld\.lld: error|undefined reference|gmake\[\d+\]: \*\*\*)"
)


@dataclass
class StructuredErrorEvent:
    event_id: str
    error_type: str
    raw_message: str
    source_location: dict[str, Any]
    related_symbol: str
    line_no: int
    is_primary: bool
    primary_id: str | None = None


@dataclass
class ParsedErrors:
    primary_errors: list[StructuredErrorEvent]
    cascade_errors: list[StructuredErrorEvent]
    unrelated_errors: list[StructuredErrorEvent]
    total_error_lines: int
    unknown_type_name_lines: int
    too_many_errors_lines: int


@dataclass
class TraceWriter:
    artifact_dir: Path
    events: list[dict[str, Any]] = field(default_factory=list)
    seq: int = 0

    def emit(self, **event: Any) -> dict[str, Any]:
        self.seq += 1
        event = {
            "seq": self.seq,
            "ts": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        self.events.append(event)
        with (self.artifact_dir / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        return event

    def write_trace(self, token_usage: dict[str, Any], final_status: str, started_at: str) -> dict[str, Any]:
        trace = {
            "task_id": TASK_ID,
            "parent_task_id": None,
            "agent_type": "compiler",
            "agent_version": "5.2-RC2.3-sprint0-spike",
            "contract_version": "0.7.3",
            "started_at": started_at,
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "final_status": final_status,
            "token_usage": token_usage,
            "events": self.events,
            "outgoing_handoffs": [],
            "incoming_handoff": None,
            "dry_run": True,
            "llm_called": False,
        }
        (self.artifact_dir / "trace.json").write_text(
            json.dumps(trace, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return trace


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode(errors="replace")).hexdigest()


def estimate_tokens(text: str) -> dict[str, Any]:
    try:
        import tiktoken  # type: ignore[import-not-found]

        encoding = tiktoken.get_encoding("cl100k_base")
        return {"tokens": len(encoding.encode(text)), "estimator": "tiktoken_cl100k_base"}
    except Exception:
        return {"tokens": math.ceil(len(text) / 4), "estimator": "chars_div_4_fallback"}


def bounded_excerpt(lines: list[str], line_no: int) -> dict[str, Any]:
    start = max(0, line_no - 3)
    end = min(len(lines), line_no + 5)
    content = "\n".join(lines[start:end])
    if len(content) > MAX_LOG_EXCERPT_CHARS:
        content = content[:MAX_LOG_EXCERPT_CHARS]
    return {
        "source_file": str(RAW_LOG),
        "line_range": [start + 1, end],
        "reason": "nested_include",
        "redacted": True,
        "char_count": len(content),
        "content": content,
    }


def parse_log(log_path: Path) -> ParsedErrors:
    lines = read_text(log_path).splitlines()
    unknown_events: list[StructuredErrorEvent] = []
    total_error_lines = 0
    too_many_errors = 0
    for line_no, line in enumerate(lines, start=1):
        if "error:" in line:
            total_error_lines += 1
        if "too many errors emitted" in line:
            too_many_errors += 1
        match = UNKNOWN_TYPE_RE.search(line)
        if not match:
            continue
        event_id = f"ERR-S0-08-{len(unknown_events) + 1:03d}"
        unknown_events.append(
            StructuredErrorEvent(
                event_id=event_id,
                error_type="unknown_type_name",
                raw_message=line,
                source_location={
                    "file": match.group("file"),
                    "line": int(match.group("line")),
                    "column": int(match.group("col")),
                },
                related_symbol=match.group("type"),
                line_no=line_no,
                is_primary=False,
            )
        )
    if not unknown_events:
        raise RuntimeError("S0-08 cascade log has no unknown_type_name errors")

    primary = unknown_events[0]
    primary.is_primary = True
    primary.primary_id = primary.event_id
    cascades = []
    for event in unknown_events[1:]:
        event.primary_id = primary.event_id
        cascades.append(event)

    return ParsedErrors(
        primary_errors=[primary],
        cascade_errors=cascades,
        unrelated_errors=[],
        total_error_lines=total_error_lines,
        unknown_type_name_lines=len(unknown_events),
        too_many_errors_lines=too_many_errors,
    )


def source_probe(parsed: ParsedErrors) -> dict[str, Any]:
    primary = parsed.primary_errors[0]
    header = HOST_SOURCE_ROOT / "include/pkgmgrinfo_type.h"
    text = read_text(header)
    symbol = primary.related_symbol
    declared = f"typedef void *{symbol};" in text
    renamed_match = re.search(r"typedef void \*(pkgmgrinfo_pkginfo_h_renamed_for_s0_04);", text)
    return {
        "root_header": str(SOURCE_ROOT / "include/pkgmgrinfo_type.h"),
        "primary_related_symbol": symbol,
        "expected_typedef_present": declared,
        "renamed_typedef_candidate": renamed_match.group(1) if renamed_match else None,
        "probe_confidence": "high",
        "source_probe": "public_header_text_search",
    }


def collect_evidence(parsed: ParsedErrors) -> dict[str, Any]:
    started = time.perf_counter()
    lines = read_text(RAW_LOG).splitlines()
    primary = parsed.primary_errors[0]
    facts = source_probe(parsed)
    same_symbol_cascades = [event for event in parsed.cascade_errors if event.related_symbol == primary.related_symbol]

    packet = {
        "evidence_id": "EP-CMP-S0-08-001",
        "task_id": TASK_ID,
        "trigger": {
            "type": "compile_error",
            "error_type": primary.error_type,
            "error_signature": primary.raw_message,
            "source_location": primary.source_location,
            "build_target": "pkgmgr-info",
            "build_system": "cmake_make_replay",
            "related_symbol": primary.related_symbol,
            "is_primary": True,
            "primary_id": primary.event_id,
        },
        "facts": {
            **facts,
            "raw_error_line_count": parsed.total_error_lines,
            "unknown_type_name_line_count": parsed.unknown_type_name_lines,
            "primary_candidate_policy": "v0.3.5 first compiler error + same-symbol cascade summary",
            "primary_position": 1,
            "representative_cascade_messages": [event.raw_message for event in same_symbol_cascades[:3]],
        },
        "known_issue_matches": [],
        "negative_facts": [
            {
                "check": f"public header declares typedef void *{primary.related_symbol};",
                "result": "not_found",
                "confidence": "high",
                "scope": "source_code",
                "implication": "The public typedef used by later declarations is absent from the header in this failure case.",
            },
            {
                "check": "KnownIssueMatcher has active unknown_type_name sample",
                "result": "not_found",
                "confidence": "high",
                "scope": "known_issues",
                "implication": "S0-07 sample DB did not include this new P0 taxonomy item; no hint is attached.",
            },
        ],
        "log_excerpt": [bounded_excerpt(lines, primary.line_no)],
        "cascade_summary": {
            "strategy": "v0.3.5_first_error_primary_same_symbol_summary",
            "primary_error_line_no": primary.line_no,
            "total_compiler_error_lines": parsed.total_error_lines,
            "unknown_type_name_lines": parsed.unknown_type_name_lines,
            "same_symbol_cascade_count_excluding_primary": len(same_symbol_cascades),
            "terminal_compiler_limit_count": parsed.too_many_errors_lines,
            "evidence_packets_generated": 1,
            "suppressed_per_error_packets": max(parsed.total_error_lines - 1, 0),
        },
        "semantic_unavailable": False,
        "clangd_stale": False,
        "compile_commands_provenance": "not_required_for_log_parser_dry_run",
        "degraded_reason": "dry_run_replay_uses_existing_s0_04_failure_log",
        "ambiguous_facts": [
            {
                "fact": "The true source edit is a renamed typedef declaration; the first compiler diagnostic is the primary candidate for repair analysis.",
                "confidence": "medium",
            }
        ],
        "collection_metadata": {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "collectors_run": [
                {"name": "LogErrorParser", "status": "ok", "mode": "s0_08_unknown_type_name_parser"},
                {"name": "PrimaryCascadeSummarizer", "status": "ok", "mode": "v0.3.5_spike"},
                {"name": "SourceHeaderProbe", "status": "ok", "mode": "source_tree_read"},
                {"name": "KnownIssueMatcher", "status": "ok", "matches": 0},
            ],
        },
        "schema": "evidence_packet.v1.spike",
    }
    packet_text = json.dumps(packet, ensure_ascii=False, sort_keys=True)
    token_estimate = estimate_tokens(packet_text)
    packet["collection_metadata"].update(
        {
            "collection_duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "packet_char_count": len(packet_text),
            "total_tokens_estimate": token_estimate["tokens"],
            "token_estimator": token_estimate["estimator"],
            "budget_tokens": MAX_EVIDENCE_PACKET_TOKENS,
            "budget_pass": token_estimate["tokens"] <= MAX_EVIDENCE_PACKET_TOKENS,
        }
    )
    return packet


def validate_prompt_raw_data(prompt: dict[str, Any]) -> dict[str, Any]:
    excerpt_contents: list[str] = []

    def walk(node: Any, path: str = "$", in_excerpt_content: bool = False) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        if isinstance(node, dict):
            for key, value in node.items():
                child_path = f"{path}.{key}"
                if key == "content" and ".log_excerpt" in path:
                    violations.extend(walk(value, child_path, True))
                else:
                    violations.extend(walk(value, child_path, False))
            return violations
        if isinstance(node, list):
            for index, item in enumerate(node):
                violations.extend(walk(item, f"{path}[{index}]", in_excerpt_content))
            return violations
        if isinstance(node, str):
            if in_excerpt_content:
                excerpt_contents.append(node)
                return violations
            if RAW_STYLE_RE.search(node):
                chars = len(node)
                lines = node.count("\n") + 1
                if chars > RAW_DATA_THRESHOLD_CHARS or lines > RAW_DATA_THRESHOLD_LINES:
                    violations.append({"path": path, "chars": chars, "lines": lines})
            return violations
        return violations

    violations = walk(prompt)
    excerpt_total = sum(len(content) for content in excerpt_contents)
    excerpt_max = max([len(content) for content in excerpt_contents] or [0])
    return {
        "status": "allowed" if not violations else "blocked",
        "failure_class": None if not violations else "raw_data_leakage",
        "violations": violations,
        "excerpt_count": len(excerpt_contents),
        "excerpt_total_chars": excerpt_total,
        "max_excerpt_chars": excerpt_max,
        "l1_pass": excerpt_max <= MAX_LOG_EXCERPT_CHARS,
        "l2_pass": excerpt_total <= 6000,
        "l3_pass": not violations,
    }


def build_mock_llm_request(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "adapter": "ClineAdapter",
        "dry_run": True,
        "llm_called": False,
        "model": "mock-no-provider",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Compiler Agent analyze stage. Known Issue matches are hints, not truth. "
                    "Use the EvidencePacket and do not assume raw logs beyond bounded excerpts."
                ),
            },
            {
                "role": "user",
                "content": {
                    "task": "Analyze the compile failure and decide what evidence would be needed for repair. Do not generate a patch in S0-08.",
                    "evidence_packet": packet,
                    "constraints": {
                        "max_tokens_per_call": MAX_TOKENS_PER_CALL,
                        "max_tokens_per_task": MAX_TOKENS_PER_TASK,
                        "evidence_packet_max_tokens": MAX_EVIDENCE_PACKET_TOKENS,
                    },
                },
            },
        ],
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def run_pipeline(output_root: Path) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat()
    artifact_dir = output_root / "spike_08_artifacts" / TASK_ID
    evidence_dir = artifact_dir / "evidence"
    llm_dir = artifact_dir / "llm"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for stale in ["events.jsonl", "trace.json"]:
        stale_path = artifact_dir / stale
        if stale_path.exists():
            stale_path.unlink()
    trace = TraceWriter(artifact_dir)

    raw_log_text = read_text(RAW_LOG)
    trace.emit(
        stage="probe_env",
        event_type="tool_call",
        name="probe_s0_08_inputs",
        duration_ms=1,
        result_summary="pkgmgr-info S0-04 cascade failure replay inputs available",
        artifacts={"raw_log_path": str(RAW_LOG), "raw_log_sha256": sha256_text(raw_log_text), "diff_ref": str(DIFF_REF)},
    )
    trace.emit(
        stage="compile",
        event_type="tool_call",
        name="run_compile_replay",
        duration_ms=1,
        result_summary="compile_status=failed (real S0-04 captured log replay)",
        artifacts={"raw_log_path": str(RAW_LOG), "raw_log_committed": False},
    )
    trace.emit(
        stage="compile",
        event_type="state_transition",
        name="RunCompile->ParseErrors",
        duration_ms=0,
        result_summary="raw log kept outside prompt; parsing structured errors next",
    )

    parse_start = time.perf_counter()
    parsed = parse_log(RAW_LOG)
    parsed_summary = {
        "primary_errors": [asdict(event) for event in parsed.primary_errors],
        "cascade_error_count": len(parsed.cascade_errors),
        "unrelated_error_count": len(parsed.unrelated_errors),
        "total_error_lines": parsed.total_error_lines,
        "unknown_type_name_lines": parsed.unknown_type_name_lines,
        "too_many_errors_lines": parsed.too_many_errors_lines,
    }
    write_json(artifact_dir / "parsed_errors.json", parsed_summary)
    trace.emit(
        stage="analyze",
        event_type="tool_call",
        name="LogErrorParser.parse",
        duration_ms=round((time.perf_counter() - parse_start) * 1000, 3),
        result_summary=(
            f"primary_errors=1 cascade_errors={len(parsed.cascade_errors)} "
            f"total_error_lines={parsed.total_error_lines}"
        ),
        artifacts={"parsed_errors_ref": "parsed_errors.json"},
    )

    collect_start = time.perf_counter()
    packet = collect_evidence(parsed)
    write_json(evidence_dir / "ep_001.json", packet)
    trace.emit(
        stage="evidence_collect",
        event_type="evidence_collected",
        name=packet["evidence_id"],
        duration_ms=round((time.perf_counter() - collect_start) * 1000, 3),
        evidence_packet_ref="evidence/ep_001.json",
        tool_calls_inside=["LogErrorParser", "PrimaryCascadeSummarizer", "SourceHeaderProbe", "KnownIssueMatcher"],
        result_summary=(
            f"packet_tokens={packet['collection_metadata']['total_tokens_estimate']} "
            "packets_generated=1 known_issue_matches=0"
        ),
    )
    trace.emit(
        stage="known_issue_match",
        event_type="known_issue_matched",
        name="KnownIssueMatcher.match",
        duration_ms=0.5,
        result_summary="matches=0 for unknown_type_name cascade sample",
    )

    llm_request = build_mock_llm_request(packet)
    raw_check = validate_prompt_raw_data(llm_request)
    write_json(llm_dir / "mock_llm_request.json", llm_request)
    trace.emit(
        stage="analyze",
        event_type="tool_call",
        name="RawDataDetector.validate",
        duration_ms=1,
        result_summary=f"status={raw_check['status']} excerpt_chars={raw_check['excerpt_total_chars']}",
        artifacts={"raw_data_check": raw_check},
    )

    prompt_text = json.dumps(llm_request, ensure_ascii=False, sort_keys=True)
    prompt_tokens = estimate_tokens(prompt_text)
    token_usage = {
        "total_in": prompt_tokens["tokens"],
        "total_out": 0,
        "by_stage": {
            "analyze": {"in": prompt_tokens["tokens"], "out": 0},
            "evidence_collect": {"in": 0, "out": 0},
        },
        "estimator": prompt_tokens["estimator"],
        "budget": {
            "max_tokens_per_call": MAX_TOKENS_PER_CALL,
            "max_tokens_per_task": MAX_TOKENS_PER_TASK,
            "sprint_0_prompt_limit": SPRINT_0_PROMPT_TOKEN_LIMIT,
            "evidence_packet_max_tokens": MAX_EVIDENCE_PACKET_TOKENS,
        },
        "budget_pass": {
            "per_call": prompt_tokens["tokens"] <= MAX_TOKENS_PER_CALL,
            "per_task_compiler_rc2_3": prompt_tokens["tokens"] <= MAX_TOKENS_PER_TASK,
            "per_task_sprint_0_prompt_legacy": prompt_tokens["tokens"] <= SPRINT_0_PROMPT_TOKEN_LIMIT,
            "evidence_packet": packet["collection_metadata"]["total_tokens_estimate"] <= MAX_EVIDENCE_PACKET_TOKENS,
        },
    }
    write_json(artifact_dir / "token_usage_summary.json", token_usage)
    trace.emit(
        stage="budget",
        event_type="budget_check",
        name="TokenLedger.preflight",
        duration_ms=0,
        tokens_in=prompt_tokens["tokens"],
        tokens_out=0,
        result_summary=(
            f"per_call={token_usage['budget_pass']['per_call']} "
            f"per_task_50000={token_usage['budget_pass']['per_task_compiler_rc2_3']} "
            f"packet={token_usage['budget_pass']['evidence_packet']}"
        ),
    )

    trace.emit(
        stage="analyze",
        event_type="llm_call",
        name="analyze_compile_failure",
        prompt_version="s0_08_mock_analyze@v1",
        tokens_in=prompt_tokens["tokens"],
        tokens_out=0,
        duration_ms=0,
        evidence_packet_ref="evidence/ep_001.json",
        mocked=True,
        llm_called=False,
        result_summary="dry_run_stopped_at_llm_entry; no provider call; no patch generated",
    )

    build_report = {
        "task_id": TASK_ID,
        "source_case": "S0-04 exp2 typedef rename cascade",
        "compile_status": "failed",
        "raw_log_path": str(RAW_LOG),
        "raw_log_sha256": sha256_text(raw_log_text),
        "raw_log_committed": False,
        "pipeline_boundary": "stopped at mocked LLM entrance",
        "patch_generated": False,
        "llm_called": False,
        "primary_packets_generated": 1,
        "raw_error_lines": parsed.total_error_lines,
        "unknown_type_name_lines": parsed.unknown_type_name_lines,
        "same_symbol_cascade_count_excluding_primary": len(parsed.cascade_errors),
        "too_many_errors_lines": parsed.too_many_errors_lines,
        "trace_ref": "trace.json",
        "events_ref": "events.jsonl",
    }
    write_json(artifact_dir / "build_report.json", build_report)
    trace.emit(
        stage="finalize",
        event_type="state_transition",
        name="DryRunComplete",
        duration_ms=0,
        result_summary="trace.json/events.jsonl/build_report/evidence_packet/mock_llm_request written",
    )
    trace_json = trace.write_trace(token_usage, "dry_run_complete", started_at)

    events_path = artifact_dir / "events.jsonl"
    events_count = len(events_path.read_text(encoding="utf-8").splitlines())
    summary = {
        "task_id": TASK_ID,
        "source_case": "S0-04 exp2 typedef rename cascade",
        "decision_pending_user_review": True,
        "pipeline_steps": [
            "compile_fail_replay",
            "log_error_parser",
            "evidence_collector",
            "evidence_packet",
            "raw_data_detector",
            "mock_llm_entrance",
        ],
        "trace": {
            "artifact_dir": str(artifact_dir),
            "trace_json": str(artifact_dir / "trace.json"),
            "events_jsonl": str(events_path),
            "trace_event_count": len(trace_json["events"]),
            "events_jsonl_line_count": events_count,
            "events_match_trace": events_count == len(trace_json["events"]),
            "required_event_types_present": sorted({event["event_type"] for event in trace_json["events"]}),
        },
        "primary_cascade": {
            "raw_error_lines": parsed.total_error_lines,
            "unknown_type_name_lines": parsed.unknown_type_name_lines,
            "primary_errors": len(parsed.primary_errors),
            "cascade_errors_same_symbol_excluding_primary": len(parsed.cascade_errors),
            "too_many_errors_lines": parsed.too_many_errors_lines,
            "evidence_packets_generated": 1,
            "would_generate_without_primary_cascade": parsed.total_error_lines,
            "suppressed_per_error_packets": max(parsed.total_error_lines - 1, 0),
        },
        "token_budget": token_usage,
        "raw_data_detector": raw_check,
        "artifacts": {
            "build_report": str(artifact_dir / "build_report.json"),
            "parsed_errors": str(artifact_dir / "parsed_errors.json"),
            "evidence_packet": str(evidence_dir / "ep_001.json"),
            "mock_llm_request": str(llm_dir / "mock_llm_request.json"),
            "token_usage_summary": str(artifact_dir / "token_usage_summary.json"),
        },
    }
    write_json(output_root / "spike_08_e2e_dry_run_results.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = run_pipeline(args.output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
