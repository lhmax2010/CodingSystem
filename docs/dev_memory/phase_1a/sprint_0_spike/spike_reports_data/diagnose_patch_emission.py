#!/usr/bin/env python3
"""Diagnose why S0-A Part 2 patches did not apply.

This diagnostic is intentionally independent from spike_A_repair_loop.py's
main flow. It imports the existing helpers and exercises them at unit level.
Default behavior stops after T1 if the gold diff cannot pass the real apply
pipeline, because that indicates a pipeline/index-state problem.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import spike_A_repair_loop as s0a


DIAG_ROOT = s0a.TMP_ROOT / "patch_emission_diagnosis"
RESULT_JSON = DIAG_ROOT / "diagnose_patch_emission_results.json"
REPORT_MD = DIAG_ROOT / "diagnose_patch_emission_report.md"
E1 = s0a.ERROR_SCENARIOS["E1_cannot_find_header"]
INSERT_LINE = "  ${CMAKE_SOURCE_DIR}/src/parser/include"
ANCHOR_LINE = "  ${CMAKE_SOURCE_DIR}/include"
LLM_RETRIES = 1
SAMPLES = 3


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    return value


def run_git(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def new_e1_worktree(label: str, gate: s0a.SideEffectGate) -> Path:
    run_id = f"diag_{int(time.time())}_{label}"
    worktree = s0a.create_isolated_worktree(E1, run_id, gate)
    s0a.apply_error_mutation(worktree, E1, gate)
    return worktree


def restore_e1_include_line(cmake_path: Path) -> None:
    lines = cmake_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if INSERT_LINE in lines:
        return
    for index, line in enumerate(lines):
        if line == ANCHOR_LINE:
            lines.insert(index + 1, INSERT_LINE)
            cmake_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise RuntimeError(f"anchor line not found: {ANCHOR_LINE}")


def make_gold_diff(worktree: Path) -> str:
    """Generate a real git diff that repairs E1 from the mutated file state."""

    target = worktree / "CMakeLists.txt"
    # Put the mutation into the index so git diff compares fixed working tree
    # against the mutated baseline. This produces a true patch from mutated ->
    # fixed without hand-writing hunk headers.
    run_git(["add", "CMakeLists.txt"], worktree)
    restore_e1_include_line(target)
    diff = run_git(["diff", "--", "CMakeLists.txt"], worktree).stdout
    if not diff.strip():
        raise RuntimeError("gold diff generation produced an empty diff")
    # Return to the actual Part 2 state: dirty mutation in worktree, original
    # index. This is the state dual_apply_patch saw during the 36-call run.
    run_git(["reset", "--hard", "HEAD"], worktree)
    s0a.apply_error_mutation(worktree, E1, s0a.SideEffectGate(True, "reset E1 mutation"))
    return diff


def make_gold_diff_control_state(worktree: Path) -> None:
    """Make index and worktree both represent the E1 mutation."""

    run_git(["reset", "--hard", "HEAD"], worktree)
    s0a.apply_error_mutation(worktree, E1, s0a.SideEffectGate(True, "control E1 mutation"))
    run_git(["add", "CMakeLists.txt"], worktree)


def apply_with_existing_pipeline(patch_text: str, worktree: Path, sample_id: str) -> dict[str, Any]:
    extracted = s0a.extract_unified_diff(patch_text)
    result = s0a.dual_apply_patch(
        extracted,
        worktree,
        s0a.SideEffectGate(True, f"diagnostic apply {sample_id}"),
        sample_id=sample_id,
    )
    result["extracted_patch"] = extracted
    return result


def test_gold_diff_apply() -> dict[str, Any]:
    gate = s0a.SideEffectGate(True, "T1 gold diff apply")
    worktree = new_e1_worktree("T1", gate)
    try:
        gold_diff = make_gold_diff(worktree)
        actual = apply_with_existing_pipeline(gold_diff, worktree, "diag_T1_actual_dirty")
        strict_status = (actual.get("strict") or {}).get("status")

        # Control: prove the same gold patch itself is valid when index and
        # worktree both represent the mutated baseline.
        make_gold_diff_control_state(worktree)
        control = apply_with_existing_pipeline(gold_diff, worktree, "diag_T1_control_staged")
        control_strict_status = (control.get("strict") or {}).get("status")

        return {
            "test": "T1 Gold Diff Apply",
            "status": "PASS" if strict_status == "PASS" else "FAIL",
            "assertion": "strict apply should PASS in the actual Part 2 pipeline state",
            "actual_dirty_pipeline": actual,
            "control_staged_mutation": control,
            "gold_diff": gold_diff,
            "diagnosis_hint": (
                "If actual_dirty_pipeline fails but control_staged_mutation passes, "
                "the patch content is valid and the failure is caused by pipeline "
                "index/worktree state around git apply --index."
            ),
        }
    finally:
        s0a.cleanup_worktree(worktree, gate)


def extract_exact_snippet(worktree: Path) -> dict[str, Any]:
    lines = (worktree / "CMakeLists.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    anchor_idx = next(i for i, line in enumerate(lines) if line == ANCHOR_LINE)
    start = max(0, anchor_idx - 8)
    end = min(len(lines), anchor_idx + 22)
    numbered = [f"{idx + 1}: {lines[idx]}" for idx in range(start, end)]
    return {
        "start_line": start + 1,
        "end_line": end,
        "numbered_text": "\n".join(numbered),
        "raw_text": "\n".join(lines[start:end]),
    }


def call_llm(prompt: str, system: str, scenario_id: str) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    for attempt in range(1, LLM_RETRIES + 2):
        try:
            response = s0a._call_adapter_with_part2_total_timeout(
                None,
                prompt,
                system=system,
                scenario_id=f"{scenario_id}_call{attempt}",
            )
            return {
                "status": "ok",
                "attempt": attempt,
                "response": {
                    "provider": response.provider,
                    "model": response.model,
                    "request_id": response.request_id,
                    "content": response.content,
                    "token_usage": response.token_usage,
                    "duration_ms": response.duration_ms,
                    "finish_reason": response.finish_reason,
                },
            }
        except Exception as exc:  # noqa: BLE001 - diagnostic records full class.
            errors.append({"type": type(exc).__name__, "message": str(exc)})
            if attempt <= LLM_RETRIES and s0a._is_timeout_error(exc):
                continue
            break
    return {"status": "llm_failed", "errors": errors}


def prepare_apply_worktree(label: str) -> tuple[Path, s0a.SideEffectGate]:
    gate = s0a.SideEffectGate(True, label)
    worktree = new_e1_worktree(label, gate)
    # These tests isolate model emission, not the dirty-index bug found by T1.
    run_git(["add", "CMakeLists.txt"], worktree)
    return worktree, gate


def test_exact_snippet_unified_diff(sample: int) -> dict[str, Any]:
    worktree, gate = prepare_apply_worktree(f"T2_sample{sample}")
    try:
        snippet = extract_exact_snippet(worktree)
        system = "Return only a unified diff. No prose, no markdown fences."
        prompt = (
            f"Here is the exact content of CMakeLists.txt lines {snippet['start_line']}-{snippet['end_line']}:\n"
            f"{snippet['numbered_text']}\n\n"
            "Add the line '  ${CMAKE_SOURCE_DIR}/src/parser/include' after the "
            "'  ${CMAKE_SOURCE_DIR}/include' line.\n"
            "Output ONLY a unified diff that git apply can apply.\n"
            "Context lines must match the source byte-for-byte.\n"
        )
        llm = call_llm(prompt, system, f"diag_T2_sample{sample}")
        result: dict[str, Any] = {
            "test": "T2 Exact Snippet Unified Diff",
            "sample": sample,
            "llm_call": llm,
            "snippet": snippet,
        }
        if llm.get("status") != "ok":
            result["status"] = "llm_failed"
            return result
        patch = s0a.extract_unified_diff(llm["response"]["content"])
        apply_result = s0a.dual_apply_patch(patch, worktree, gate, sample_id=f"diag_T2_sample{sample}")
        result.update(
            {
                "patch_text": patch,
                "apply": apply_result,
                "status": "PASS" if apply_result.get("final_applied") in {"strict", "fuzzy"} else "FAIL",
            }
        )
        return result
    finally:
        s0a.cleanup_worktree(worktree, gate)


def parse_search_replace(text: str) -> dict[str, str]:
    fenced = re.search(r"```(?:text)?\n(?P<body>.*?)```", text, re.DOTALL)
    body = fenced.group("body") if fenced else text
    match = re.search(
        r"<<<<<<< SEARCH\s*\n(?P<search>.*?)\n=======\s*\n(?P<replace>.*?)\n>>>>>>> REPLACE",
        body,
        re.DOTALL,
    )
    if not match:
        raise ValueError("search_replace_block_not_found")
    return {"search": match.group("search"), "replace": match.group("replace")}


def apply_search_replace(worktree: Path, block: dict[str, str]) -> dict[str, Any]:
    target = worktree / "CMakeLists.txt"
    text = target.read_text(encoding="utf-8", errors="replace")
    search = block["search"]
    replace = block["replace"]
    count = text.count(search)
    if count != 1:
        return {"status": "FAIL", "reason": f"search_exact_match_count={count}"}
    target.write_text(text.replace(search, replace, 1), encoding="utf-8")
    diff = run_git(["diff", "--", "CMakeLists.txt"], worktree).stdout
    correct = INSERT_LINE in target.read_text(encoding="utf-8", errors="replace")
    return {"status": "PASS" if correct else "FAIL", "exact_match_count": count, "diff": diff}


def test_search_replace(sample: int) -> dict[str, Any]:
    worktree, gate = prepare_apply_worktree(f"T3_sample{sample}")
    try:
        snippet = extract_exact_snippet(worktree)
        system = "Return only a search-replace block. No prose."
        prompt = (
            f"Here is the exact content of CMakeLists.txt lines {snippet['start_line']}-{snippet['end_line']}:\n"
            f"{snippet['numbered_text']}\n\n"
            "Add the line '  ${CMAKE_SOURCE_DIR}/src/parser/include' after the "
            "'  ${CMAKE_SOURCE_DIR}/include' line.\n"
            "Output your fix as a search-replace block:\n"
            "<<<<<<< SEARCH\n"
            "(exact existing lines to find)\n"
            "=======\n"
            "(replacement lines)\n"
            ">>>>>>> REPLACE\n"
            "The SEARCH block must match the source byte-for-byte.\n"
        )
        llm = call_llm(prompt, system, f"diag_T3_sample{sample}")
        result: dict[str, Any] = {
            "test": "T3 Search-Replace",
            "sample": sample,
            "llm_call": llm,
            "snippet": snippet,
        }
        if llm.get("status") != "ok":
            result["status"] = "llm_failed"
            return result
        content = llm["response"]["content"]
        result["raw_output"] = content
        try:
            block = parse_search_replace(content)
            result["block"] = block
            apply_result = apply_search_replace(worktree, block)
            result["apply"] = apply_result
            result["status"] = "PASS" if apply_result.get("status") == "PASS" else "FAIL"
        except Exception as exc:  # noqa: BLE001
            result["status"] = "FAIL"
            result["error"] = {"type": type(exc).__name__, "message": str(exc)}
        return result
    finally:
        s0a.cleanup_worktree(worktree, gate)


def extract_json_object(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\n(?P<body>.*?)```", text, re.DOTALL)
    body = fenced.group("body").strip() if fenced else text.strip()
    if not body.startswith("{"):
        start = body.find("{")
        end = body.rfind("}")
        if start < 0 or end < start:
            raise ValueError("json_object_not_found")
        body = body[start : end + 1]
    return json.loads(body)


def load_e1_evidence_packet_from_part2_prompt() -> dict[str, Any]:
    input_dir = s0a.S0A_TMP_ROOT / "part2_llm_inputs"
    candidates = sorted(input_dir.glob("part2_E1_A_sample*_call1.prompt.json"))
    if not candidates:
        raise RuntimeError(f"no E1 Part 2 prompt files found under {input_dir}")
    payload = json.loads(candidates[0].read_text(encoding="utf-8"))
    packet = payload.get("evidence_packet")
    if not isinstance(packet, dict):
        raise RuntimeError(f"evidence_packet missing in {candidates[0]}")
    return packet


def generate_patch_from_intent(worktree: Path, intent: dict[str, Any]) -> dict[str, Any]:
    target_file = intent.get("target_file")
    anchor = intent.get("anchor")
    value = intent.get("value")
    if target_file != "CMakeLists.txt":
        return {"status": "FAIL", "reason": f"unexpected_target_file={target_file!r}"}
    if not isinstance(anchor, str) or not isinstance(value, str):
        return {"status": "FAIL", "reason": "anchor_or_value_not_string"}

    target = worktree / target_file
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    match_mode = "none"
    insert_at: int | None = None
    for idx, line in enumerate(lines):
        if line == anchor:
            match_mode = "exact"
            insert_at = idx + 1
            break
    if insert_at is None:
        for idx, line in enumerate(lines):
            if line.strip() == anchor.strip():
                match_mode = "stripped"
                insert_at = idx + 1
                break
    if insert_at is None:
        return {"status": "FAIL", "reason": "anchor_not_found", "anchor": anchor}
    if value not in lines:
        lines.insert(insert_at, value)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    diff = run_git(["diff", "--", "CMakeLists.txt"], worktree).stdout
    return {
        "status": "PASS" if INSERT_LINE in lines else "FAIL",
        "anchor_match": match_mode,
        "diff": diff,
    }


def test_intent_json(sample: int, evidence_packet: dict[str, Any]) -> dict[str, Any]:
    worktree, gate = prepare_apply_worktree(f"T4_sample{sample}")
    try:
        system = "Return only a JSON object. No prose, no markdown fences."
        prompt = json.dumps(
            {
                "instruction": (
                    "Output ONLY a JSON repair intent with keys repair_type, "
                    "target_file, anchor, value."
                ),
                "required_schema": {
                    "repair_type": "add_cmake_include_directory",
                    "target_file": "CMakeLists.txt",
                    "anchor": "<existing line to insert after>",
                    "value": "<the include path to add>",
                },
                "scenario": "E1 cannot_find_header",
                "evidence_packet": evidence_packet,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        llm = call_llm(prompt, system, f"diag_T4_sample{sample}")
        result: dict[str, Any] = {"test": "T4 Intent JSON", "sample": sample, "llm_call": llm}
        if llm.get("status") != "ok":
            result["status"] = "llm_failed"
            return result
        content = llm["response"]["content"]
        result["raw_output"] = content
        try:
            intent = extract_json_object(content)
            result["intent"] = intent
            json_valid = True
        except Exception as exc:  # noqa: BLE001
            result["status"] = "FAIL"
            result["json_valid"] = False
            result["error"] = {"type": type(exc).__name__, "message": str(exc)}
            return result
        apply_result = generate_patch_from_intent(worktree, intent)
        result["json_valid"] = json_valid
        result["apply"] = apply_result
        result["status"] = "PASS" if apply_result.get("status") == "PASS" else "FAIL"
        return result
    finally:
        s0a.cleanup_worktree(worktree, gate)


def summarize(results: dict[str, Any]) -> dict[str, Any]:
    def count_pass(items: list[dict[str, Any]]) -> int:
        return sum(1 for item in items if item.get("status") == "PASS")

    summary = {
        "T1": results.get("T1", {}).get("status"),
        "only": results.get("only"),
        "stopped_after_T1": bool(results.get("stopped_after_T1")),
    }
    for key in ("T2", "T3", "T4"):
        items = results.get(key) or []
        summary[key] = {
            "samples": len(items),
            "pass": count_pass(items),
            "llm_failed": sum(1 for item in items if item.get("status") == "llm_failed"),
        }
    if results.get("T4"):
        summary["T4"]["json_valid"] = sum(1 for item in results["T4"] if item.get("json_valid"))
    return summary


def render_report(results: dict[str, Any]) -> str:
    t1 = results.get("T1") or {}
    actual = t1.get("actual_dirty_pipeline") or {}
    control = t1.get("control_staged_mutation") or {}
    lines = [
        "# Patch Emission Diagnosis",
        "",
        "## T1 Gold Diff Apply",
        f"- pipeline status: {t1.get('status', 'NOT_RUN')}",
        f"- actual dirty strict: {(actual.get('strict') or {}).get('status', 'N/A')}",
        f"- actual dirty fuzzy: {(actual.get('fuzzy') or {}).get('status', 'N/A')}",
        f"- actual dirty final_applied: {actual.get('final_applied', 'N/A')}",
        f"- control staged strict: {(control.get('strict') or {}).get('status', 'N/A')}",
        f"- control staged final_applied: {control.get('final_applied', 'N/A')}",
    ]
    if t1.get("status") == "FAIL":
        lines.extend(
            [
                f"- actual strict error: {((actual.get('strict') or {}).get('result') or {}).get('tail_excerpt', (actual.get('strict') or {}).get('reason', ''))}",
                f"- actual fuzzy error: {((actual.get('fuzzy') or {}).get('result') or {}).get('tail_excerpt', (actual.get('fuzzy') or {}).get('reason', ''))}",
                "",
                "T1 failed, so T2/T3/T4 were not run by default.",
            ]
        )
    for key, title in (
        ("T2", "T2 Exact Snippet Unified Diff"),
        ("T3", "T3 Search-Replace"),
        ("T4", "T4 Intent JSON"),
    ):
        items = results.get(key) or []
        if not items:
            continue
        lines.extend(["", f"## {title}", f"- apply PASS: {sum(1 for item in items if item.get('status') == 'PASS')}/{len(items)}"])
        if key == "T4":
            lines.append(f"- JSON valid: {sum(1 for item in items if item.get('json_valid'))}/{len(items)}")
        first_patch = next((item.get("patch_text") or item.get("raw_output") for item in items if item.get("patch_text") or item.get("raw_output")), "")
        if first_patch:
            lines.extend(["", "Sample output:", "```", first_patch[:4000].rstrip(), "```"])
    lines.extend(
        [
            "",
            "## Diagnostic conclusion (objective)",
            f"- T1 pipeline check: {t1.get('status', 'NOT_RUN')}",
            "- T2/T3/T4 compare exact context, search-replace, and intent JSON only if T1 passes or --force-all is used.",
            "",
            f"JSON results: {RESULT_JSON}",
        ]
    )
    return "\n".join(lines) + "\n"


def run(force_all: bool, only: str | None = None) -> dict[str, Any]:
    DIAG_ROOT.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {
        "schema": "patch_emission_diagnosis.v1",
        "created_at": s0a.utc_now(),
        "t1_policy": "stop_after_T1_failure_unless_force_all",
        "only": only,
    }
    results["T1"] = test_gold_diff_apply()
    if only == "T1":
        results["stopped_after_T1"] = False
        results["summary"] = summarize(results)
        RESULT_JSON.write_text(json.dumps(to_jsonable(results), ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        REPORT_MD.write_text(render_report(results), encoding="utf-8")
        return results
    if results["T1"].get("status") != "PASS" and not force_all:
        results["stopped_after_T1"] = True
        results["summary"] = summarize(results)
        RESULT_JSON.write_text(json.dumps(to_jsonable(results), ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        REPORT_MD.write_text(render_report(results), encoding="utf-8")
        return results

    results["stopped_after_T1"] = False
    results["T2"] = [test_exact_snippet_unified_diff(i) for i in range(1, SAMPLES + 1)]
    results["T3"] = [test_search_replace(i) for i in range(1, SAMPLES + 1)]
    evidence_packet = load_e1_evidence_packet_from_part2_prompt()
    results["T4"] = [test_intent_json(i, evidence_packet) for i in range(1, SAMPLES + 1)]
    results["summary"] = summarize(results)
    RESULT_JSON.write_text(json.dumps(to_jsonable(results), ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    REPORT_MD.write_text(render_report(results), encoding="utf-8")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-all", action="store_true", help="Run T2/T3/T4 even if T1 fails.")
    parser.add_argument("--only", choices=["T1"], help="Run only the selected diagnostic test.")
    args = parser.parse_args()
    results = run(force_all=args.force_all, only=args.only)
    print(json.dumps(to_jsonable(results["summary"]), ensure_ascii=False, indent=2, sort_keys=True))
    print(f"RESULT_JSON={RESULT_JSON}")
    print(f"REPORT_MD={REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
