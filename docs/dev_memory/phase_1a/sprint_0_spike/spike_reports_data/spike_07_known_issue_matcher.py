#!/usr/bin/env python3
"""S0-07 spike-only KnownIssueMatcher.

The sample Known Issues are derived from S0-04 real pkgmgr-info error samples.
This validates matcher mechanics only; the 20-30 item production dataset is
owned by S2b-06.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


TMP_ROOT = Path("/tmp/coding-system-s0")

REAL_SAMPLE_PATHS = {
    "cannot_find_header": TMP_ROOT / "s0_04_exp1_1_parsed.json",
    "undefined_reference": TMP_ROOT / "s0_04_exp1_2_parsed.json",
    "undefined_symbol": TMP_ROOT / "s0_04_A_parsed.json",
    "type_mismatch": TMP_ROOT / "s0_04_exp1_3_parsed.json",
    "template_error": TMP_ROOT / "s0_04_exp1_4_parsed.json",
}

REQUIRED_FIELDS = {
    "id",
    "description",
    "category",
    "match",
    "applicable_build_systems",
    "supported_error_types",
    "applicable_toolchains",
    "applicable_languages",
    "evidence_requirements",
    "likely_causes",
    "suggested_fix_hints",
    "suggested_fix_type",
    "anti_patterns",
    "confidence_default",
    "owner",
    "created_at",
    "updated_at",
    "validated_count",
    "false_positive_count",
    "status",
    "auto_downgrade",
}


def load_primary_error(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    return data["errors"][0]


def real_events() -> dict[str, dict[str, Any]]:
    samples = {kind: load_primary_error(path) for kind, path in REAL_SAMPLE_PATHS.items()}
    return {
        "cannot_find_header": {
            "event_id": "ERR-S0-07-HEADER",
            "error_type": samples["cannot_find_header"]["error_type"],
            "raw_message": samples["cannot_find_header"]["message"],
            "build_system": "cmake_make",
            "toolchain": "clang",
            "language": "cpp",
            "source": "S0-04 exp1.1",
        },
        "undefined_reference": {
            "event_id": "ERR-S0-07-GNU-LD",
            "error_type": samples["undefined_reference"]["error_type"],
            "raw_message": samples["undefined_reference"]["message"],
            "build_system": "cmake_make",
            "toolchain": "clang",
            "language": "cpp",
            "source": "S0-04 exp1.2",
        },
        "undefined_symbol": {
            "event_id": "ERR-S0-07-LLD",
            "error_type": samples["undefined_symbol"]["error_type"],
            "raw_message": samples["undefined_symbol"]["message"],
            "build_system": "cmake_ninja",
            "toolchain": "clang",
            "language": "c",
            "source": "S0-04 experiment A",
        },
        "type_mismatch": {
            "event_id": "ERR-S0-07-TYPE",
            "error_type": samples["type_mismatch"]["error_type"],
            "raw_message": samples["type_mismatch"]["message"],
            "build_system": "cmake_make",
            "toolchain": "clang",
            "language": "cpp",
            "source": "S0-04 exp1.3",
        },
        "template_error": {
            "event_id": "ERR-S0-07-TEMPLATE",
            "error_type": samples["template_error"]["error_type"],
            "raw_message": samples["template_error"]["message"],
            "build_system": "cmake_make",
            "toolchain": "clang",
            "language": "cpp",
            "source": "S0-04 exp1.4",
        },
    }


def known_issues() -> list[dict[str, Any]]:
    common_meta = {
        "owner": "phase1a-spike-owner@example.invalid",
        "created_at": "2026-05-29",
        "updated_at": "2026-05-29",
        "validated_count": 0,
        "false_positive_count": 0,
        "status": "active",
        "auto_downgrade": {
            "threshold_false_positive_rate": 0.3,
            "threshold_min_validations": 10,
        },
    }
    common_scope = {
        "applicable_build_systems": ["cmake_ninja", "cmake_make", "gbs"],
        "applicable_toolchains": ["gcc", "clang"],
        "applicable_languages": ["c", "cpp"],
    }
    return [
        {
            **common_meta,
            **common_scope,
            "id": "s0_04_missing_include_directory",
            "description": "Header exists in source tree but the target include path is missing",
            "category": "include_path",
            "match": {
                "error_regex": r"fatal error: ['<](?P<header>[^'>]+)[>'] file not found",
                "captures": ["header"],
            },
            "supported_error_types": ["cannot_find_header"],
            "unsupported_error_types": ["undefined_reference", "template_error", "runtime_crash"],
            "evidence_requirements": {
                "must_have": ["log_excerpt", "compile_command_include_paths"],
                "optional": ["header_candidates", "cmake_include_directories"],
            },
            "likely_causes": [
                "CMake include_directories or target_include_directories entry was removed",
                "Generated header directory was not added to the target",
            ],
            "suggested_fix_hints": [
                "Restore the missing include directory for the failing target",
                "Check whether the header should come from BuildRequires/pkg-config",
            ],
            "suggested_fix_type": ["cmake_modification", "build_config_modification"],
            "anti_patterns": [
                "The header may be intentionally deleted in a newer upstream version",
                "The header may be generated by a failed earlier build step",
                "The include may be guarded by target-specific conditional compilation",
            ],
            "confidence_default": 0.78,
            "validation_source": "S0-04 exp1.1 cannot_find_header real pkgmgr-info log",
        },
        {
            **common_meta,
            **common_scope,
            "id": "s0_04_gnu_ld_missing_target_link_library",
            "description": "GNU ld undefined reference likely caused by missing target link library",
            "category": "linker_error",
            "match": {
                "error_regex": r"undefined reference to [`'](?P<missing_symbol>[^`']+)[`']",
                "captures": ["missing_symbol"],
            },
            "supported_error_types": ["undefined_reference"],
            "unsupported_error_types": ["undefined_symbol", "runtime_crash", "test_failure"],
            "evidence_requirements": {
                "must_have": ["link_command", "cmake_target_link_libraries"],
                "optional": ["symbol_definitions", "candidate_libraries"],
            },
            "likely_causes": [
                "target_link_libraries is missing the library that defines the symbol",
                "Library order changed and the resolver cannot see the definition",
            ],
            "suggested_fix_hints": [
                "Inspect the link command and restore the missing target_link_libraries entry",
                "Scan built libraries with nm -C to locate the missing symbol",
            ],
            "suggested_fix_type": ["cmake_modification", "link_command_modification"],
            "anti_patterns": [
                "Undefined reference may be caused by C++ ABI mismatch",
                "Undefined reference may be caused by symbol visibility hidden",
                "Undefined reference may be caused by missing template instantiation",
                "Undefined reference may be caused by C/C++ linkage mismatch",
            ],
            "confidence_default": 0.75,
            "validation_source": "S0-04 exp1.2 undefined_reference real pkgmgr-info log",
        },
        {
            **common_meta,
            **common_scope,
            "id": "s0_04_lld_undefined_symbol_format",
            "description": "LLD undefined symbol diagnostic from strict link flags",
            "category": "linker_error",
            "match": {
                "error_regex": r"ld\.lld: error: undefined symbol: (?P<missing_symbol>\S+)",
                "captures": ["missing_symbol"],
            },
            "supported_error_types": ["undefined_symbol"],
            "unsupported_error_types": ["undefined_reference", "runtime_crash", "test_failure"],
            "evidence_requirements": {
                "must_have": ["link_command", "related_symbols"],
                "optional": ["referenced_by_objects", "candidate_libraries"],
            },
            "likely_causes": [
                "LLD strict linking exposed a missing dependency",
                "The link command omits an object or library that GNU ld previously tolerated",
            ],
            "suggested_fix_hints": [
                "Parse the LLD referenced-by block and inspect the target's link libraries",
                "Compare the failing LLD link command against the GNU ld link command",
            ],
            "suggested_fix_type": ["cmake_modification", "link_command_modification"],
            "anti_patterns": [
                "Runtime dlopen undefined symbols should not use this build-time LLD hint",
                "A version script hiding a symbol needs a different fix",
                "A symbol removed by source refactor should not be fixed by adding libraries",
            ],
            "confidence_default": 0.72,
            "validation_source": "S0-04 experiment A LLD undefined symbol real pkgmgr-info log",
        },
        {
            **common_meta,
            **common_scope,
            "id": "s0_04_public_header_signature_drift",
            "description": "Header declaration changed without synchronized implementation/callers",
            "category": "type_error",
            "match": {
                "error_regex": (
                    r"cannot initialize a parameter of type '(?P<expected>[^']+)' "
                    r"with an lvalue of type '(?P<actual>[^']+)'"
                ),
                "captures": ["expected", "actual"],
            },
            "supported_error_types": ["type_mismatch"],
            "unsupported_error_types": ["template_error", "cannot_find_header", "runtime_crash"],
            "evidence_requirements": {
                "must_have": ["source_symbol_context", "declaration_location"],
                "optional": ["callers_of_affected_symbols"],
            },
            "likely_causes": [
                "A public header declaration was changed but implementation/callers were not updated",
                "A typedef or enum type drifted across translation units",
            ],
            "suggested_fix_hints": [
                "Compare the declaration, definition, and failing call site",
                "Update either the public header or all affected callers consistently",
            ],
            "suggested_fix_type": ["source_modification", "header_modification"],
            "anti_patterns": [
                "The mismatch may be caused by macro-expanded platform types",
                "Overload resolution may require inspecting all overload candidates",
                "C-style casts can hide the true source of the mismatch",
            ],
            "confidence_default": 0.74,
            "validation_source": "S0-04 exp1.3 type_mismatch real pkgmgr-info log",
        },
        {
            **common_meta,
            **common_scope,
            "id": "s0_04_stl_vector_allocator_value_type_mismatch",
            "description": "std::vector allocator value_type does not match the vector element type",
            "category": "template_error",
            "match": {
                "error_regex": r"std::vector must have the same value_type as its allocator",
                "captures": [],
            },
            "supported_error_types": ["template_error"],
            "unsupported_error_types": ["type_mismatch", "undefined_reference", "runtime_crash"],
            "evidence_requirements": {
                "must_have": ["template_instantiation_context", "source_symbol_context"],
                "optional": ["type_dependencies"],
            },
            "likely_causes": [
                "The STL container allocator template argument is not an allocator for the value type",
                "A template parameter was edited without updating the allocator argument",
            ],
            "suggested_fix_hints": [
                "Check the container template arguments at the instantiation site",
                "Use std::allocator<T> or omit the allocator parameter unless a real allocator is intended",
            ],
            "suggested_fix_type": ["source_modification"],
            "anti_patterns": [
                "Some template errors are only downstream symptoms of an earlier primary error",
                "libc++ and libstdc++ may report equivalent template failures with different wording",
                "A custom allocator may be valid if its value_type matches exactly",
            ],
            "confidence_default": 0.70,
            "validation_source": "S0-04 exp1.4 template_error real pkgmgr-info log",
        },
    ]


@dataclass(frozen=True)
class KnownIssueMatch:
    issue_id: str
    confidence: float
    captures: dict[str, str]
    suggested_fix_hints: list[str]


class KnownIssueMatcher:
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues

    def match(self, error_event: dict[str, Any]) -> list[KnownIssueMatch]:
        matches: list[KnownIssueMatch] = []
        for issue in self.issues:
            if issue.get("status") != "active":
                continue
            if error_event["error_type"] not in issue["supported_error_types"]:
                continue
            if error_event["build_system"] not in issue["applicable_build_systems"]:
                continue
            if error_event.get("toolchain") not in issue["applicable_toolchains"]:
                continue
            if error_event.get("language") not in issue["applicable_languages"]:
                continue

            regex = re.compile(issue["match"]["error_regex"])
            match = regex.search(error_event["raw_message"])
            if not match:
                continue
            captures = {name: match.group(name) for name in issue["match"].get("captures", []) if name in match.groupdict()}
            matches.append(
                KnownIssueMatch(
                    issue_id=issue["id"],
                    confidence=float(issue["confidence_default"]),
                    captures=captures,
                    suggested_fix_hints=list(issue["suggested_fix_hints"]),
                )
            )
        return sorted(matches, key=lambda item: item.confidence, reverse=True)


def lint_known_issues(issues: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for issue in issues:
        missing = sorted(REQUIRED_FIELDS - set(issue))
        if missing:
            failures.append({"issue_id": issue.get("id"), "failure": "missing_fields", "fields": missing})
        if len(issue.get("anti_patterns") or []) < 3:
            failures.append({"issue_id": issue.get("id"), "failure": "anti_patterns_lt_3"})
        if not issue.get("owner"):
            failures.append({"issue_id": issue.get("id"), "failure": "missing_owner"})
        if issue.get("confidence_default", 1) > 0.8:
            failures.append({"issue_id": issue.get("id"), "failure": "confidence_gt_0_8"})
        if not issue.get("supported_error_types"):
            failures.append({"issue_id": issue.get("id"), "failure": "supported_error_types_empty"})
        if not issue.get("applicable_build_systems"):
            failures.append({"issue_id": issue.get("id"), "failure": "applicable_build_systems_empty"})
        try:
            re.compile(issue["match"]["error_regex"])
        except re.error as exc:
            failures.append({"issue_id": issue.get("id"), "failure": "invalid_regex", "reason": str(exc)})
    return {
        "issue_count": len(issues),
        "failure_count": len(failures),
        "passed": not failures,
        "failures": failures,
    }


def serialize_matches(matches: list[KnownIssueMatch]) -> list[dict[str, Any]]:
    return [
        {
            "issue_id": match.issue_id,
            "confidence": match.confidence,
            "captures": match.captures,
            "suggested_fix_hints": match.suggested_fix_hints,
        }
        for match in matches
    ]


def test_cases(events: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    expected_ids = {
        "cannot_find_header": "s0_04_missing_include_directory",
        "undefined_reference": "s0_04_gnu_ld_missing_target_link_library",
        "undefined_symbol": "s0_04_lld_undefined_symbol_format",
        "type_mismatch": "s0_04_public_header_signature_drift",
        "template_error": "s0_04_stl_vector_allocator_value_type_mismatch",
    }

    hits = [
        {
            "case_id": f"hit_{name}",
            "event": event,
            "expected_issue_ids": [expected_ids[name]],
        }
        for name, event in events.items()
    ]

    no_matches = [
        {
            "case_id": "no_match_plain_warning",
            "event": {
                "event_id": "ERR-S0-07-NO-1",
                "error_type": "warning",
                "raw_message": "warning: unused variable 'tmp'",
                "build_system": "cmake_make",
                "toolchain": "clang",
                "language": "cpp",
            },
            "expected_issue_ids": [],
        },
        {
            "case_id": "no_match_permission_denied",
            "event": {
                "event_id": "ERR-S0-07-NO-2",
                "error_type": "permission_denied",
                "raw_message": "install: cannot create regular file '/usr/bin/foo': Permission denied",
                "build_system": "cmake_make",
                "toolchain": "clang",
                "language": "c",
            },
            "expected_issue_ids": [],
        },
        {
            "case_id": "no_match_cmake_message",
            "event": {
                "event_id": "ERR-S0-07-NO-3",
                "error_type": "cmake_configure_error",
                "raw_message": "Could not find package configuration file \"FooConfig.cmake\"",
                "build_system": "cmake_ninja",
                "toolchain": "clang",
                "language": "cpp",
            },
            "expected_issue_ids": [],
        },
        {
            "case_id": "no_match_unknown_type_name",
            "event": {
                "event_id": "ERR-S0-07-NO-4",
                "error_type": "unknown_type_name",
                "raw_message": "include/foo.h:10:3: error: unknown type name 'foo_handle_h'",
                "build_system": "cmake_make",
                "toolchain": "clang",
                "language": "c",
            },
            "expected_issue_ids": [],
        },
        {
            "case_id": "no_match_runtime_symbol",
            "event": {
                "event_id": "ERR-S0-07-NO-5",
                "error_type": "runtime_crash",
                "raw_message": "symbol lookup error: undefined symbol: pkgmgrinfo_basic_free_package",
                "build_system": "cmake_ninja",
                "toolchain": "clang",
                "language": "c",
            },
            "expected_issue_ids": [],
        },
    ]

    scope_guards: list[dict[str, Any]] = []
    for name, event in events.items():
        wrong_build_system = dict(event)
        wrong_build_system["event_id"] = f"{event['event_id']}-BAD-BUILD"
        wrong_build_system["build_system"] = "make"
        scope_guards.append(
            {
                "case_id": f"scope_guard_{name}_wrong_build_system",
                "event": wrong_build_system,
                "expected_issue_ids": [],
                "guard": "applicable_build_systems",
            }
        )

        wrong_error_type = dict(event)
        wrong_error_type["event_id"] = f"{event['event_id']}-BAD-TYPE"
        wrong_error_type["error_type"] = "runtime_crash"
        scope_guards.append(
            {
                "case_id": f"scope_guard_{name}_wrong_error_type",
                "event": wrong_error_type,
                "expected_issue_ids": [],
                "guard": "supported_error_types",
            }
        )

    return {"hits": hits, "no_matches": no_matches, "scope_guards": scope_guards}


def run_tests(issues: list[dict[str, Any]]) -> dict[str, Any]:
    matcher = KnownIssueMatcher(issues)
    events = real_events()
    grouped_cases = test_cases(events)

    groups: dict[str, Any] = {}
    for group_name, cases in grouped_cases.items():
        results = []
        for case in cases:
            matches = matcher.match(case["event"])
            actual_ids = [match.issue_id for match in matches]
            results.append(
                {
                    "case_id": case["case_id"],
                    "event_id": case["event"]["event_id"],
                    "source": case["event"].get("source"),
                    "error_type": case["event"]["error_type"],
                    "build_system": case["event"]["build_system"],
                    "expected_issue_ids": case["expected_issue_ids"],
                    "actual_issue_ids": actual_ids,
                    "matched_expectation": actual_ids == case["expected_issue_ids"],
                    "guard": case.get("guard"),
                    "matches": serialize_matches(matches),
                }
            )
        groups[group_name] = {
            "case_count": len(results),
            "matched_expectations": sum(1 for result in results if result["matched_expectation"]),
            "all_matched_expectation": all(result["matched_expectation"] for result in results),
            "results": results,
        }

    return {
        "matcher": "s0_07_mock_known_issue_matcher",
        "scope": {
            "sprint": "Sprint 0 spike mock",
            "known_issue_dataset_size": 5,
            "production_dataset_20_30_items": "deferred_to_S2b_06",
            "samples_source": "S0-04 real pkgmgr-info error samples",
        },
        "governance_lint": lint_known_issues(issues),
        "groups": groups,
        "summary": {
            "all_groups_matched_expectation": all(group["all_matched_expectation"] for group in groups.values()),
            "hit_accuracy": f"{groups['hits']['matched_expectations']}/{groups['hits']['case_count']}",
            "no_match_false_positive_count": (
                groups["no_matches"]["case_count"] - groups["no_matches"]["matched_expectations"]
            ),
            "scope_guard_false_positive_count": (
                groups["scope_guards"]["case_count"] - groups["scope_guards"]["matched_expectations"]
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    sample_path = args.output_dir / "spike_07_known_issues_sample.yaml"
    results_path = args.output_dir / "spike_07_known_issue_matcher_results.json"

    issues = known_issues()
    sample_path.write_text(yaml.safe_dump(issues, sort_keys=False, allow_unicode=True), encoding="utf-8")
    loaded_issues = yaml.safe_load(sample_path.read_text(encoding="utf-8"))
    results = run_tests(loaded_issues)
    results_path.write_text(json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
