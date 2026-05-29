#!/usr/bin/env python3
"""S0-06 spike-only RawDataDetector mock.

This validates Contract v0.7.3 Section 5.6.3 threshold behavior in characters,
not bytes. It is intentionally outside product code and does not integrate with
ClineAdapter in Sprint 0.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


MAX_LOG_EXCERPT_CHARS = 3000
MAX_LOG_EXCERPTS_TOTAL_CHARS = 6000
MAX_LOG_EXCERPTS_PER_PACKET = 3
RAW_DATA_THRESHOLD_CHARS = 6000
RAW_DATA_THRESHOLD_LINES = 200

ALLOWED_REASONS = {
    "template_error_context",
    "macro_expansion",
    "linker_context",
    "nested_include",
    "generated_code_origin",
    "benchmark_outlier_context",
}

RAW_STYLE_PATTERNS = [
    re.compile(r"/[^:\n]+:\d+:\d+:\s+(?:fatal\s+)?(?:error|warning):"),
    re.compile(r"\b(?:fatal error|undefined reference|ld\.lld: error|error generated)\b"),
    re.compile(r"^\s*(?:gmake|make|ninja)(?:\[\d+\])?: \*\*\*", re.MULTILINE),
    re.compile(r"^\s*\[\s*\d+%\]\s+(?:Building|Linking|Generating)\b", re.MULTILINE),
    re.compile(r"^\s*cd\s+/.*\s+&&\s+/.+", re.MULTILINE),
]


class RawDataLeakageError(Exception):
    def __init__(
        self,
        reason: str,
        *,
        chars: int,
        lines: int = 0,
        field_path: str = "",
        failure_class: str = "raw_data_leakage",
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.chars = chars
        self.lines = lines
        self.field_path = field_path
        self.failure_class = failure_class


@dataclass
class DetectorResult:
    status: str
    failure_class: str | None = None
    reason: str | None = None
    field_path: str | None = None
    chars: int = 0
    bytes_utf8: int = 0
    lines: int = 0
    excerpt_count: int = 0
    excerpt_total_chars: int = 0
    max_excerpt_chars: int = 0
    details: dict[str, Any] = field(default_factory=dict)


class RawDataDetector:
    """Contract v0.7.3-compatible mock detector using character thresholds."""

    def validate(self, prompt: Any) -> DetectorResult:
        try:
            excerpt_stats = self._validate_log_excerpts(prompt)
            self._validate_raw_strings_outside_excerpts(prompt)
            return DetectorResult(status="allowed", **excerpt_stats)
        except RawDataLeakageError as exc:
            return DetectorResult(
                status="blocked",
                failure_class=exc.failure_class,
                reason=exc.reason,
                field_path=exc.field_path,
                chars=exc.chars,
                bytes_utf8=0,
                lines=exc.lines,
            )

    def _validate_log_excerpts(self, prompt: Any) -> dict[str, int]:
        excerpts = list(self._find_log_excerpts(prompt))
        total_chars = 0
        max_chars = 0

        if len(excerpts) > MAX_LOG_EXCERPTS_PER_PACKET:
            raise RawDataLeakageError(
                "too_many_log_excerpts",
                chars=0,
                field_path="log_excerpt",
            )

        for path, excerpt in excerpts:
            if not isinstance(excerpt, dict):
                raise RawDataLeakageError("log_excerpt_not_object", chars=0, field_path=path)
            content = excerpt.get("content", "")
            if not isinstance(content, str):
                raise RawDataLeakageError("log_excerpt_content_not_string", chars=0, field_path=f"{path}.content")
            char_count = len(content)
            total_chars += char_count
            max_chars = max(max_chars, char_count)

            if char_count > MAX_LOG_EXCERPT_CHARS:
                raise RawDataLeakageError(
                    "l1_single_log_excerpt_exceeds_3000_chars",
                    chars=char_count,
                    lines=content.count("\n") + 1,
                    field_path=f"{path}.content",
                )
            if excerpt.get("redacted") is not True:
                raise RawDataLeakageError("log_excerpt_not_redacted", chars=char_count, field_path=path)
            if "line_range" not in excerpt:
                raise RawDataLeakageError("log_excerpt_missing_line_range", chars=char_count, field_path=path)
            if "source_file" not in excerpt and "source" not in excerpt:
                raise RawDataLeakageError("log_excerpt_missing_source_link", chars=char_count, field_path=path)
            if excerpt.get("reason") not in ALLOWED_REASONS:
                raise RawDataLeakageError("log_excerpt_invalid_reason", chars=char_count, field_path=path)

        if total_chars > MAX_LOG_EXCERPTS_TOTAL_CHARS:
            raise RawDataLeakageError(
                "l2_log_excerpt_total_exceeds_6000_chars",
                chars=total_chars,
                field_path="log_excerpt[*].content",
            )

        return {
            "excerpt_count": len(excerpts),
            "excerpt_total_chars": total_chars,
            "max_excerpt_chars": max_chars,
        }

    def _validate_raw_strings_outside_excerpts(self, prompt: Any) -> None:
        for path, value in self._walk_non_excerpt_strings(prompt):
            if not self._is_raw_like(value):
                continue
            line_count = value.count("\n") + 1
            char_count = len(value)
            if char_count > RAW_DATA_THRESHOLD_CHARS:
                raise RawDataLeakageError(
                    "l3_raw_content_outside_excerpt_exceeds_6000_chars",
                    chars=char_count,
                    lines=line_count,
                    field_path=path,
                )
            if line_count > RAW_DATA_THRESHOLD_LINES:
                raise RawDataLeakageError(
                    "l3_raw_content_outside_excerpt_exceeds_200_lines",
                    chars=char_count,
                    lines=line_count,
                    field_path=path,
                )

    def _find_log_excerpts(self, node: Any, path: str = "$") -> list[tuple[str, Any]]:
        found: list[tuple[str, Any]] = []
        if isinstance(node, dict):
            for key, value in node.items():
                child_path = f"{path}.{key}"
                if key == "log_excerpt":
                    if isinstance(value, list):
                        found.extend((f"{child_path}[{index}]", item) for index, item in enumerate(value))
                    else:
                        found.append((child_path, value))
                    continue
                found.extend(self._find_log_excerpts(value, child_path))
        elif isinstance(node, list):
            for index, item in enumerate(node):
                found.extend(self._find_log_excerpts(item, f"{path}[{index}]"))
        return found

    def _walk_non_excerpt_strings(self, node: Any, path: str = "$") -> list[tuple[str, str]]:
        if isinstance(node, str):
            return [(path, node)]
        if isinstance(node, list):
            strings: list[tuple[str, str]] = []
            for index, item in enumerate(node):
                strings.extend(self._walk_non_excerpt_strings(item, f"{path}[{index}]"))
            return strings
        if isinstance(node, dict):
            strings = []
            for key, value in node.items():
                if key == "log_excerpt":
                    continue
                strings.extend(self._walk_non_excerpt_strings(value, f"{path}.{key}"))
            return strings
        return []

    def _is_raw_like(self, value: str) -> bool:
        if not value:
            return False
        matches = sum(1 for pattern in RAW_STYLE_PATTERNS if pattern.search(value))
        error_density = len(re.findall(r"\b(?:error|warning|fatal|undefined reference)\b", value)) >= 3
        return matches >= 1 and (error_density or len(value) > RAW_DATA_THRESHOLD_CHARS)


def repeated_raw_log(target_chars: int) -> str:
    raw_path = Path("/tmp/coding-system-s0/s0_04_exp1_1_build.log")
    if raw_path.exists():
        base = raw_path.read_text(errors="replace")
    else:
        base = (
            "/home/abuild/s0/pkg/foo.cc:35:10: fatal error: 'foo.h' file not found\n"
            "   35 | #include \"foo.h\"\n"
            "      |          ^~~~~~~\n"
            "1 error generated.\n"
            "gmake[2]: *** [src/CMakeFiles/foo.dir/build.make:166: foo.cc.o] Error 1\n"
        )
    repeats = (target_chars // len(base)) + 2
    return (base * repeats)[:target_chars]


def excerpt(content: str, *, source: str = "logs/compile.log") -> dict[str, Any]:
    return {
        "source_file": source,
        "line_range": [1, max(1, content.count("\n") + 1)],
        "reason": "nested_include",
        "redacted": True,
        "content": content,
    }


def prompt_with_excerpts(contents: list[str], extra_text: str = "Please analyze the EvidencePacket.") -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": "Use only bounded EvidencePacket evidence."},
            {"role": "user", "content": extra_text},
        ],
        "evidence_packet": {
            "schema": "evidence_packet.v1.spike",
            "log_excerpt": [excerpt(content, source=f"logs/compile_{index}.log") for index, content in enumerate(contents)],
        },
    }


def build_cases() -> list[dict[str, Any]]:
    legal_a = repeated_raw_log(2800)
    legal_b = repeated_raw_log(2800)
    over_l1 = repeated_raw_log(3001)
    small_a = repeated_raw_log(2100)
    small_b = repeated_raw_log(2100)
    small_c = repeated_raw_log(2100)
    raw_outside = repeated_raw_log(6001)
    unicode_content = "错" * 2500

    return [
        {
            "case_id": "case_1_legal_excerpt",
            "description": "合法 excerpt：单段 2800 字符，2 段总计 5600 字符，在 EvidencePacket.log_excerpt 内",
            "expected": "allowed",
            "payload": prompt_with_excerpts([legal_a, legal_b]),
            "char_metrics": {
                "excerpt_chars": [len(legal_a), len(legal_b)],
                "excerpt_total_chars": len(legal_a) + len(legal_b),
            },
        },
        {
            "case_id": "case_2_single_excerpt_over_l1",
            "description": "单个 log_excerpt 3001 字符，违反 L1 3000 字符",
            "expected": "blocked",
            "payload": prompt_with_excerpts([over_l1]),
            "char_metrics": {
                "excerpt_chars": [len(over_l1)],
                "excerpt_total_chars": len(over_l1),
            },
        },
        {
            "case_id": "case_3_multiple_small_excerpts_over_l2",
            "description": "3 个 small excerpt 各 2100 字符，总计 6300 字符，违反 L2/场景 C",
            "expected": "blocked",
            "payload": prompt_with_excerpts([small_a, small_b, small_c]),
            "char_metrics": {
                "excerpt_chars": [len(small_a), len(small_b), len(small_c)],
                "excerpt_total_chars": len(small_a) + len(small_b) + len(small_c),
            },
        },
        {
            "case_id": "case_4_raw_log_outside_excerpt_over_l3",
            "description": "不在 excerpt 结构内的 raw-like content 6001 字符，违反 L3/场景 A",
            "expected": "blocked",
            "payload": {
                "messages": [
                    {"role": "system", "content": "Analyze this build failure."},
                    {"role": "user", "content": raw_outside},
                ],
                "evidence_packet": {"schema": "evidence_packet.v1.spike", "facts": {}},
            },
            "char_metrics": {
                "raw_outside_chars": len(raw_outside),
                "raw_outside_lines": raw_outside.count("\n") + 1,
            },
        },
        {
            "case_id": "case_5_character_not_byte_control",
            "description": "字符单位控制：2500 个中文字符，UTF-8 bytes > 3000，但字符数 <= 3000，应按字符放行",
            "expected": "allowed",
            "payload": prompt_with_excerpts([unicode_content], extra_text="Character unit control."),
            "char_metrics": {
                "excerpt_chars": [len(unicode_content)],
                "excerpt_total_chars": len(unicode_content),
                "excerpt_utf8_bytes": [len(unicode_content.encode("utf-8"))],
            },
        },
    ]


def run_cases() -> dict[str, Any]:
    detector = RawDataDetector()
    case_results = []
    for case in build_cases():
        result = detector.validate(case["payload"])
        result_dict = {
            "case_id": case["case_id"],
            "description": case["description"],
            "expected": case["expected"],
            "actual": result.status,
            "matched_expectation": result.status == case["expected"],
            "failure_class": result.failure_class,
            "reason": result.reason,
            "field_path": result.field_path,
            "chars": result.chars,
            "lines": result.lines,
            "excerpt_count": result.excerpt_count,
            "excerpt_total_chars": result.excerpt_total_chars,
            "max_excerpt_chars": result.max_excerpt_chars,
            "char_metrics": case["char_metrics"],
        }
        case_results.append(result_dict)

    return {
        "detector": "s0_06_mock_raw_data_detector",
        "thresholds": {
            "l1_single_log_excerpt_max_chars": MAX_LOG_EXCERPT_CHARS,
            "l2_packet_log_excerpt_total_max_chars": MAX_LOG_EXCERPTS_TOTAL_CHARS,
            "l3_raw_data_detector_threshold_chars": RAW_DATA_THRESHOLD_CHARS,
            "raw_data_detector_line_threshold": RAW_DATA_THRESHOLD_LINES,
            "unit": "characters",
            "deprecated_threshold_not_used": "DEFAULT_SIZE_THRESHOLD_BYTES=20480",
        },
        "scope": {
            "sprint": "Sprint 0 spike mock",
            "cline_adapter_integration": "not_started_sprint_1_plus",
            "raw_payloads_committed": False,
        },
        "summary": {
            "case_count": len(case_results),
            "matched_expectations": sum(1 for result in case_results if result["matched_expectation"]),
            "all_matched_expectation": all(result["matched_expectation"] for result in case_results),
        },
        "cases": case_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run_cases()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
