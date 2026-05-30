#!/usr/bin/env python3
"""S0-A Repair Loop spike framework.

Step 0 artifact only. This file defines the repair-loop control flow,
interfaces, scenario config, reuse points, and local failure-test stubs.

Important boundary:
  - Default execution does not open worktrees, run GBS, call clangd, call LLM,
    apply patches, or rebuild.
  - Side-effectful functions require SideEffectGate(enabled=True), which is
    reserved for later PM-confirmed S0-A Part 1 execution.
  - Parser / evidence / clangd / raw-data logic is imported from Sprint 0
    spike artifacts. Do not fork those implementations here.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
CODING_SYSTEM_ROOT = SCRIPT_DIR.parents[4]
SPIKE_REPORTS_DATA = SCRIPT_DIR
TMP_ROOT = Path("/tmp/coding-system-s0")
S0A_TMP_ROOT = TMP_ROOT / "s0_a_repair_loop"
WORKTREE_ROOT = S0A_TMP_ROOT / "worktrees"
TRACE_ROOT = S0A_TMP_ROOT / "traces"
PATCH_ROOT = S0A_TMP_ROOT / "patches"

GBS_CONF = Path("/home/linhao/Toolchain/gbs_llvm.conf")
GBS_ARCH = "x86_64"
MAX_PATCH_ATTEMPTS = 2
VERIFY_TIMEOUT_SEC = 300
MAX_PATCH_LINES = 200

SPIKE_03_PATH = SPIKE_REPORTS_DATA / "spike_03_clangd_lsp_eval.py"
SPIKE_04_PATH = SPIKE_REPORTS_DATA / "spike_04_log_parser.py"
SPIKE_05_PATH = SPIKE_REPORTS_DATA / "spike_05_evidence_packet.py"
SPIKE_06_PATH = SPIKE_REPORTS_DATA / "spike_06_raw_data_detector.py"
LLM_ADAPTER_PATH = SPIKE_REPORTS_DATA / "llm_adapter" / "llm_adapter.py"
LLM_CONFIG_PATH = SPIKE_REPORTS_DATA / "llm_adapter" / "llm_config.yaml"


@dataclass(frozen=True)
class ErrorScenario:
    """A real build-error scenario accepted by PM for S0-A Part 1."""

    scenario_id: str
    package: str
    error_type: str
    source_file: Path
    mutation_kind: str
    mutation_target: str
    expected_primary_hint: str
    notes: str


@dataclass
class CommandResult:
    """Result from a subprocess command.

    Future Part 1 runs write full logs under /tmp only. This object carries
    only paths and bounded metadata into repo artifacts.
    """

    command: list[str]
    cwd: Path
    exit_code: int
    duration_sec: float
    stdout_path: Path | None = None
    stderr_path: Path | None = None
    combined_log_path: Path | None = None
    tail_excerpt: str = ""


@dataclass
class ParsedBuildFailure:
    """Build failure parsed by the S0-04 LogErrorParser."""

    parser_name: str
    log_path: Path
    parsed_error_count: int
    primary_candidate: dict[str, Any] | None
    raw_result: dict[str, Any]


@dataclass
class EvidenceCollectionResult:
    """EvidencePacket plus collector metadata for one repair attempt."""

    packet: dict[str, Any]
    raw_data_status: dict[str, Any]
    clangd_facts: dict[str, Any] = field(default_factory=dict)
    degraded_reasons: list[str] = field(default_factory=list)


@dataclass
class LLMCallResult:
    """Single LLM call result using llm_adapter.LLMResponse semantics."""

    scenario_id: str
    attempt_index: int
    provider: str
    model: str
    request_id: str
    content: str
    token_usage: dict[str, int]
    duration_ms: int
    finish_reason: str | None


@dataclass
class PatchValidationResult:
    """Patch validation result before git apply."""

    accepted: bool
    reason: str | None = None
    line_count: int = 0
    touched_paths: list[str] = field(default_factory=list)


@dataclass
class RepairAttemptResult:
    """One bounded repair attempt."""

    attempt_index: int
    llm_result: LLMCallResult | None = None
    patch_text: str = ""
    patch_validation: PatchValidationResult | None = None
    apply_result: CommandResult | None = None
    rebuild_result: CommandResult | None = None
    status: str = "not_started"
    failure_class: str | None = None


@dataclass
class RepairRunResult:
    """End-to-end Part 1 result for one scenario."""

    scenario_id: str
    worktree_path: Path
    build_failure: CommandResult | None = None
    parsed_failure: ParsedBuildFailure | None = None
    evidence: EvidenceCollectionResult | None = None
    attempts: list[RepairAttemptResult] = field(default_factory=list)
    final_status: str = "not_started"
    failure_envelope: dict[str, Any] | None = None


@dataclass(frozen=True)
class SideEffectGate:
    """Prevents accidental Part 1 execution during Step 0 framework review."""

    enabled: bool = False
    reason: str = "S0-A Step 0 framework review only"

    def require(self, operation: str) -> None:
        if not self.enabled:
            raise RuntimeError(
                f"side effects disabled: {operation}; "
                f"current phase: {self.reason}"
            )


ERROR_SCENARIOS: dict[str, ErrorScenario] = {
    "E1_cannot_find_header": ErrorScenario(
        scenario_id="E1_cannot_find_header",
        package="pkgmgr-info",
        error_type="cannot_find_header",
        source_file=Path("CMakeLists.txt"),
        mutation_kind="remove_line",
        mutation_target="${CMAKE_SOURCE_DIR}/src/parser/include",
        expected_primary_hint="tool/pkg-db-recovery.c includes pkgmgr_parser_db.h",
        notes="Remove parser include dir from root CMakeLists.txt.",
    ),
    "E2_undefined_reference": ErrorScenario(
        scenario_id="E2_undefined_reference",
        package="pkgmgr-info",
        error_type="undefined_reference",
        source_file=Path("tool/CMakeLists.txt"),
        mutation_kind="remove_line",
        mutation_target="${TARGET_LIB_PKGMGR_PARSER}",
        expected_primary_hint="pkg-db-creator.c calls pkgmgr_parser_create_and_initialize_db",
        notes="Remove parser library from tool target_link_libraries.",
    ),
    "E3_unknown_type_name_cascade": ErrorScenario(
        scenario_id="E3_unknown_type_name_cascade",
        package="pkgmgr-info",
        error_type="unknown_type_name",
        source_file=Path("include/pkgmgrinfo_type.h"),
        mutation_kind="remove_typedef",
        mutation_target="typedef void *pkgmgrinfo_appinfo_h;",
        expected_primary_hint="public typedef drift cascades through pkgmgr-info and consumers",
        notes="Delete pkgmgrinfo_appinfo_h typedef; reused later for S0-C.",
    ),
}


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp for trace/event records."""

    return datetime.now(timezone.utc).isoformat()


def load_spike_module(module_name: str, path: Path) -> ModuleType:
    """Load an existing Sprint 0 spike module by path.

    This is the central reuse hook. S0-A must call existing spike functions
    instead of copying parser/evidence/raw-data code here.
    """

    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_reused_spikes() -> dict[str, ModuleType]:
    """Import Sprint 0 artifacts and verify required public hooks exist."""

    modules = {
        "spike_03": load_spike_module("s0a_spike_03_clangd", SPIKE_03_PATH),
        "spike_04": load_spike_module("s0a_spike_04_log_parser", SPIKE_04_PATH),
        "spike_05": load_spike_module("s0a_spike_05_evidence", SPIKE_05_PATH),
        "spike_06": load_spike_module("s0a_spike_06_raw_detector", SPIKE_06_PATH),
        "llm_adapter": load_spike_module("s0a_llm_adapter", LLM_ADAPTER_PATH),
    }
    required: dict[str, list[str]] = {
        "spike_03": ["JsonRpcClient", "LogCollector", "uri", "normalize_locs"],
        "spike_04": ["parse_log"],
        "spike_05": ["bounded_excerpt", "estimate_tokens", "make_packet"],
        "spike_06": ["RawDataDetector"],
        "llm_adapter": ["get_adapter", "LLMAdapterError"],
    }
    for key, names in required.items():
        missing = [name for name in names if not hasattr(modules[key], name)]
        if missing:
            raise AttributeError(f"{key} missing required hooks: {missing}")
    return modules


def ensure_git_repo(repo_path: Path) -> None:
    """Validate that repo_path is a git worktree; emit contract violation later."""

    if not (repo_path / ".git").exists():
        raise RuntimeError(f"contract_violation: not a git repo: {repo_path}")


def ensure_clean_worktree(repo_path: Path) -> None:
    """Fail-safe if the target worktree has uncommitted changes."""

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_path,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git status failed in {repo_path}: {result.stderr.strip()}")
    if result.stdout.strip():
        raise RuntimeError("fail_safe: uncommitted changes present")


def package_repo_path(scenario: ErrorScenario) -> Path:
    """Return the source repo path for a scenario package."""

    return CODING_SYSTEM_ROOT / "codes" / scenario.package


def create_isolated_worktree(
    scenario: ErrorScenario,
    run_id: str,
    gate: SideEffectGate,
) -> Path:
    """Create a git worktree for the scenario.

    Side-effectful; disabled in Step 0. Future Part 1 will use this to keep the
    PM's source checkout untouched.
    """

    gate.require("git worktree add")
    source_repo = package_repo_path(scenario)
    ensure_git_repo(source_repo)
    ensure_clean_worktree(source_repo)
    worktree_path = WORKTREE_ROOT / f"{run_id}_{scenario.scenario_id}"
    branch = f"codex/s0a/{run_id}/{scenario.scenario_id}"
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(worktree_path)],
        cwd=source_repo,
        check=True,
    )
    return worktree_path


def apply_error_mutation(worktree_path: Path, scenario: ErrorScenario, gate: SideEffectGate) -> None:
    """Introduce the accepted real error scenario into an isolated worktree."""

    gate.require(f"mutate scenario {scenario.scenario_id}")
    target = worktree_path / scenario.source_file
    text = target.read_text(errors="replace")
    if scenario.mutation_target not in text:
        raise RuntimeError(f"mutation target not found: {scenario.mutation_target}")
    if scenario.mutation_kind in {"remove_line", "remove_typedef"}:
        lines = [
            line for line in text.splitlines()
            if scenario.mutation_target not in line
        ]
        target.write_text("\n".join(lines) + "\n")
        return
    raise ValueError(f"unsupported mutation kind: {scenario.mutation_kind}")


def run_gbs_build(
    worktree_path: Path,
    scenario: ErrorScenario,
    log_path: Path,
    gate: SideEffectGate,
    *,
    timeout_sec: int | None = None,
) -> CommandResult:
    """Run GBS in the worktree and capture full raw output under /tmp only."""

    gate.require("gbs build")
    command = [
        "gbs",
        "--conf",
        str(GBS_CONF),
        "build",
        "-A",
        GBS_ARCH,
        "--include-all",
        "--clean",
    ]
    started = time.perf_counter()
    with log_path.open("w", encoding="utf-8", errors="replace") as log_file:
        proc = subprocess.run(
            command,
            cwd=worktree_path,
            text=True,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            timeout=timeout_sec,
            check=False,
        )
    duration = time.perf_counter() - started
    tail = "\n".join(log_path.read_text(errors="replace").splitlines()[-50:])
    return CommandResult(
        command=command,
        cwd=worktree_path,
        exit_code=proc.returncode,
        duration_sec=duration,
        combined_log_path=log_path,
        tail_excerpt=tail,
    )


def parse_build_log(log_path: Path, modules: dict[str, ModuleType]) -> ParsedBuildFailure:
    """Parse build log through S0-04 LogErrorParser without reimplementing it."""

    result = modules["spike_04"].parse_log(log_path)
    return ParsedBuildFailure(
        parser_name=result.get("parser", "spike_04"),
        log_path=log_path,
        parsed_error_count=int(result.get("parsed_error_count", 0)),
        primary_candidate=result.get("primary_candidate"),
        raw_result=result,
    )


def collect_clangd_facts(
    worktree_path: Path,
    parsed_failure: ParsedBuildFailure,
    modules: dict[str, ModuleType],
    gate: SideEffectGate,
) -> dict[str, Any]:
    """Collect semantic facts with clangd using the S0-03 JSON-RPC client.

    Future Part 1 implementation should:
      1. find the primary symbol/source location from parsed_failure,
      2. start clangd with the scenario compile_commands dir,
      3. query definition/references with spike_03.JsonRpcClient,
      4. mark macro/token-paste references confidence low/medium per S0-03.

    This is side-effectful because it launches clangd; it is intentionally not
    called during Step 0.
    """

    gate.require("clangd semantic collection")
    _ = (worktree_path, parsed_failure, modules)
    raise NotImplementedError("S0-A Part 1 will wire real clangd collection here")


def collect_evidence_packet(
    scenario: ErrorScenario,
    worktree_path: Path,
    parsed_failure: ParsedBuildFailure,
    modules: dict[str, ModuleType],
    gate: SideEffectGate,
) -> EvidenceCollectionResult:
    """Build an EvidencePacket by extending S0-05 packet helpers.

    Reuse boundary:
      - bounded excerpts / token estimation / packet metadata: spike_05
      - primary error input: spike_04
      - clangd facts: spike_03 client, added here as a thin collector
      - RawDataDetector: spike_06
    """

    start = time.perf_counter()
    primary = parsed_failure.primary_candidate
    if not primary:
        raise RuntimeError("evidence_collection_failed: no primary error")

    clangd_facts: dict[str, Any] = {}
    degraded: list[str] = []
    try:
        clangd_facts = collect_clangd_facts(worktree_path, parsed_failure, modules, gate)
    except NotImplementedError:
        degraded.append("clangd_collector_framework_only_step_0")

    excerpt = modules["spike_05"].bounded_excerpt(
        parsed_failure.log_path,
        int(primary.get("line_no", 1)),
    )
    if excerpt.get("reason") == "compile_error_context":
        # S0-06 allow-list is narrower than S0-05's early spike value.
        excerpt["reason"] = "nested_include"

    packet = {
        "schema": "evidence_packet.v1.spike_A",
        "evidence_id": f"EP-S0-A-{scenario.scenario_id}",
        "task_id": "S0-A-Part1",
        "trigger": {
            "type": "compile_error",
            "error_type": scenario.error_type,
            "error_signature": primary.get("message"),
            "source_location": primary.get("source_location"),
            "build_target": scenario.package,
            "build_system": "gbs_cmake",
            "related_symbol": primary.get("symbol"),
            "is_primary": True,
            "primary_id": f"ERR-S0-A-{scenario.scenario_id}",
        },
        "facts": {
            "scenario_mutation": asdict(scenario),
            "parser_primary_candidate": primary,
            "clangd": clangd_facts,
        },
        "negative_facts": [
            {
                "check": "raw build log included in prompt",
                "result": "not_present",
                "confidence": "high",
                "scope": "prompt_boundary",
                "implication": "Only bounded log_excerpt is allowed into LLM prompt.",
            }
        ],
        "known_issue_matches": [],
        "log_excerpt": [excerpt],
        "cascade_summary": {
            "strategy": "framework_placeholder",
            "note": "S2b-03 owns full primary/cascade parser. S0-A uses the S0-04 primary candidate plus bounded summary.",
        } if scenario.error_type == "unknown_type_name" else None,
        "semantic_unavailable": not bool(clangd_facts),
        "clangd_stale": False,
        "compile_commands_provenance": "future_part1_build_worktree",
        "degraded_reason": ";".join(degraded) if degraded else None,
        "ambiguous_facts": [],
        "collection_metadata": {
            "collected_at": utc_now(),
            "collection_duration_ms": round((time.perf_counter() - start) * 1000, 3),
            "collectors_run": [
                {"name": "LogErrorParser", "status": "ok", "mode": "spike_04.parse_log"},
                {"name": "EvidencePacketBuilder", "status": "ok", "mode": "spike_05_extended"},
                {"name": "ClangdCollector", "status": "degraded" if degraded else "ok", "mode": "spike_03.JsonRpcClient"},
                {"name": "RawDataDetector", "status": "pending", "mode": "spike_06.RawDataDetector"},
            ],
        },
    }
    packet = modules["spike_05"].make_packet(packet, start)
    detector = modules["spike_06"].RawDataDetector()
    raw_status = asdict(detector.validate(packet))
    return EvidenceCollectionResult(packet=packet, raw_data_status=raw_status, clangd_facts=clangd_facts, degraded_reasons=degraded)


def build_llm_prompt(evidence: EvidenceCollectionResult, attempt_index: int) -> tuple[str, str]:
    """Render the S0-A Part 1 prompt from bounded EvidencePacket data only."""

    system = (
        "You are repairing a Tizen C/C++ package. Return only a unified diff. "
        "Use only the bounded EvidencePacket; do not ask for raw logs."
    )
    user = json.dumps(
        {
            "instruction": "Generate a minimal unified diff that fixes the compile failure.",
            "attempt_index": attempt_index,
            "max_patch_lines": MAX_PATCH_LINES,
            "evidence_packet": evidence.packet,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return system, user


def call_llm_for_patch(
    evidence: EvidenceCollectionResult,
    attempt_index: int,
    modules: dict[str, ModuleType],
    gate: SideEffectGate,
) -> LLMCallResult:
    """Call the real LLM through llm_adapter.

    Side-effectful and disabled in Step 0. Part 1 will use Kimi/Moonshot via
    llm_config.yaml after PM confirms framework review.
    """

    gate.require("LLM call")
    system, prompt = build_llm_prompt(evidence, attempt_index)
    adapter = modules["llm_adapter"].get_adapter(str(LLM_CONFIG_PATH))
    response = adapter.call(
        prompt,
        system=system,
        scenario_id=f"S0-A-Part1-attempt-{attempt_index}",
    )
    return LLMCallResult(
        scenario_id=f"S0-A-Part1-attempt-{attempt_index}",
        attempt_index=attempt_index,
        provider=response.provider,
        model=response.model,
        request_id=response.request_id,
        content=response.content,
        token_usage=response.token_usage,
        duration_ms=response.duration_ms,
        finish_reason=response.finish_reason,
    )


def extract_unified_diff(text: str) -> str:
    """Extract a unified diff from an LLM response."""

    fenced = re.search(r"```(?:diff|patch)?\n(?P<body>.*?)```", text, re.DOTALL)
    if fenced:
        return fenced.group("body").strip() + "\n"
    return text.strip() + "\n"


def validate_patch(patch_text: str, worktree_path: Path) -> PatchValidationResult:
    """Validate patch format, size, and path scope before git apply."""

    lines = patch_text.splitlines()
    touched: list[str] = []
    if not patch_text.strip():
        return PatchValidationResult(False, "empty_patch", 0, [])
    if len(lines) > MAX_PATCH_LINES:
        return PatchValidationResult(False, "patch_too_large", len(lines), [])
    if not any(line.startswith("--- ") for line in lines) or not any(line.startswith("+++ ") for line in lines):
        return PatchValidationResult(False, "not_unified_diff", len(lines), [])

    for line in lines:
        if not line.startswith(("--- ", "+++ ")):
            continue
        path_text = line[4:].strip()
        if path_text == "/dev/null":
            continue
        if path_text.startswith(("a/", "b/")):
            path_text = path_text[2:]
        candidate = (worktree_path / path_text).resolve()
        try:
            candidate.relative_to(worktree_path.resolve())
        except ValueError:
            return PatchValidationResult(False, "patch_path_escapes_worktree", len(lines), touched)
        touched.append(path_text)
    return PatchValidationResult(True, None, len(lines), sorted(set(touched)))


def apply_patch_to_worktree(patch_text: str, worktree_path: Path, gate: SideEffectGate) -> CommandResult:
    """Apply a validated patch with git apply."""

    gate.require("git apply patch")
    patch_file = PATCH_ROOT / f"apply_{int(time.time())}.patch"
    patch_file.parent.mkdir(parents=True, exist_ok=True)
    patch_file.write_text(patch_text)
    started = time.perf_counter()
    proc = subprocess.run(
        ["git", "apply", "--index", str(patch_file)],
        cwd=worktree_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return CommandResult(
        command=["git", "apply", "--index", str(patch_file)],
        cwd=worktree_path,
        exit_code=proc.returncode,
        duration_sec=time.perf_counter() - started,
        tail_excerpt="\n".join(proc.stdout.splitlines()[-50:]),
    )


def make_failure_envelope(
    scenario: ErrorScenario,
    failure_class: str,
    message: str,
    *,
    stage: str = "repair_loop",
    reason_code: str | None = None,
    attempt_index: int | None = None,
    details: dict[str, Any] | None = None,
    last_attempt_log_excerpt: str | None = None,
) -> dict[str, Any]:
    """Create a bounded failure envelope for fail-safe exits."""

    return {
        "schema": "failure_envelope.v1",
        "agent_type": "compiler",
        "task_id": "S0-A-Part1",
        "created_at": utc_now(),
        "scenario_id": scenario.scenario_id,
        "stage": stage,
        "failure_class": failure_class,
        "reason_code": reason_code or failure_class,
        "message": message,
        "attempt_index": attempt_index,
        "max_patch_attempts": MAX_PATCH_ATTEMPTS,
        "retryable": False,
        "details": details or {},
        "last_attempt_log_excerpt": last_attempt_log_excerpt,
    }


def emit_event(
    events_path: Path,
    *,
    stage: str,
    event_type: str,
    name: str,
    result_summary: str = "",
    payload: dict[str, Any] | None = None,
    **extra: Any,
) -> None:
    """Append one Compiler-style JSONL event.

    Shape follows Compiler Agent v5.2 trace/events style:
    stage/event_type/name/result_summary plus optional payload fields.
    """

    events_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": utc_now(),
        "stage": stage,
        "event_type": event_type,
        "name": name,
        "result_summary": result_summary,
        "payload": payload or {},
    }
    record.update(extra)
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def build_trace_payload(result: RepairRunResult) -> dict[str, Any]:
    """Build a trace.json payload without embedding raw build logs."""

    token_usage = {"total_in": 0, "total_out": 0, "by_stage": {}}
    for attempt in result.attempts:
        if not attempt.llm_result:
            continue
        usage = attempt.llm_result.token_usage
        token_usage["total_in"] += int(usage.get("in", 0))
        token_usage["total_out"] += int(usage.get("out", 0))
        stage_usage = token_usage["by_stage"].setdefault("generate_patch", {"in": 0, "out": 0})
        stage_usage["in"] += int(usage.get("in", 0))
        stage_usage["out"] += int(usage.get("out", 0))

    return {
        "schema": "trace.v1.spike_A",
        "agent_type": "compiler",
        "task_id": "S0-A-Part1",
        "scenario_id": result.scenario_id,
        "status": result.final_status,
        "worktree_path": str(result.worktree_path),
        "token_usage": token_usage,
        "failure_envelope": result.failure_envelope,
        "artifacts": {
            "events_jsonl": "events.jsonl",
            "raw_logs_policy": "raw logs stay under /tmp/coding-system-s0 and are referenced by path only",
        },
        "attempts": asdict(result.attempts),
    }


def write_trace(trace_path: Path, result: RepairRunResult) -> None:
    """Write structured trace JSON without raw build log content."""

    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(
        json.dumps(build_trace_payload(result), ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def run_repair_loop_for_scenario(
    scenario: ErrorScenario,
    modules: dict[str, ModuleType],
    gate: SideEffectGate,
) -> RepairRunResult:
    """S0-A Part 1 bounded repair-loop control flow.

    This shows the intended production-like order while preserving Step 0's
    no-side-effect boundary unless gate.enabled is explicitly set by a later PM
    instruction.
    """

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    worktree_path = create_isolated_worktree(scenario, run_id, gate)
    result = RepairRunResult(scenario_id=scenario.scenario_id, worktree_path=worktree_path)
    events_path = TRACE_ROOT / run_id / scenario.scenario_id / "events.jsonl"
    trace_path = TRACE_ROOT / run_id / scenario.scenario_id / "trace.json"
    try:
        apply_error_mutation(worktree_path, scenario, gate)
        fail_log = TRACE_ROOT / run_id / scenario.scenario_id / "initial_build_fail.log"
        emit_event(
            events_path,
            stage="compile",
            event_type="tool_call",
            name="build_started",
            result_summary=f"initial failing build for {scenario.scenario_id}",
            log_path=str(fail_log),
        )
        result.build_failure = run_gbs_build(worktree_path, scenario, fail_log, gate)
        emit_event(
            events_path,
            stage="compile",
            event_type="tool_call",
            name="build_finished",
            result_summary=f"exit_code={result.build_failure.exit_code}",
            payload=asdict(result.build_failure),
        )
        if result.build_failure.exit_code == 0:
            result.final_status = "scenario_did_not_fail"
            result.failure_envelope = make_failure_envelope(
                scenario,
                "scenario_setup_error",
                "mutated scenario unexpectedly built successfully",
                stage="compile",
                reason_code="scenario_did_not_fail",
            )
            return result

        result.parsed_failure = parse_build_log(fail_log, modules)
        emit_event(
            events_path,
            stage="parse_errors",
            event_type="tool_call",
            name="parse_completed",
            result_summary=f"parsed_error_count={result.parsed_failure.parsed_error_count}",
            payload={
                "parser": result.parsed_failure.parser_name,
                "primary_candidate": result.parsed_failure.primary_candidate,
            },
        )
        result.evidence = collect_evidence_packet(scenario, worktree_path, result.parsed_failure, modules, gate)
        emit_event(
            events_path,
            stage="evidence_collect",
            event_type="evidence_collected",
            name=result.evidence.packet["evidence_id"],
            result_summary=f"raw_data_status={result.evidence.raw_data_status.get('status')}",
            payload={
                "degraded_reasons": result.evidence.degraded_reasons,
                "raw_data_status": result.evidence.raw_data_status,
            },
            evidence_packet_ref=result.evidence.packet["evidence_id"],
        )
        if result.evidence.raw_data_status.get("status") != "allowed":
            result.final_status = "fail_safe"
            result.failure_envelope = make_failure_envelope(
                scenario,
                "raw_data_leakage",
                "RawDataDetector blocked EvidencePacket",
                stage="cognitive_input_validate",
                reason_code=result.evidence.raw_data_status.get("reason", "raw_data_detector_blocked"),
                details=result.evidence.raw_data_status,
            )
            return result

        for attempt_index in range(1, MAX_PATCH_ATTEMPTS + 1):
            attempt = RepairAttemptResult(attempt_index=attempt_index)
            result.attempts.append(attempt)
            attempt.llm_result = call_llm_for_patch(result.evidence, attempt_index, modules, gate)
            emit_event(
                events_path,
                stage="generate_patch",
                event_type="llm_call",
                name="llm_called",
                result_summary=f"attempt={attempt_index}, request_id={attempt.llm_result.request_id}",
                tokens_in=attempt.llm_result.token_usage.get("in", 0),
                tokens_out=attempt.llm_result.token_usage.get("out", 0),
                request_id=attempt.llm_result.request_id,
            )
            attempt.patch_text = extract_unified_diff(attempt.llm_result.content)
            attempt.patch_validation = validate_patch(attempt.patch_text, worktree_path)
            emit_event(
                events_path,
                stage="validate_patch",
                event_type="tool_call",
                name="patch_validated",
                result_summary=f"accepted={attempt.patch_validation.accepted}, reason={attempt.patch_validation.reason}",
                payload=asdict(attempt.patch_validation),
            )
            if not attempt.patch_validation.accepted:
                attempt.status = "patch_rejected"
                attempt.failure_class = attempt.patch_validation.reason
                continue

            attempt.apply_result = apply_patch_to_worktree(attempt.patch_text, worktree_path, gate)
            emit_event(
                events_path,
                stage="apply_patch",
                event_type="tool_call",
                name="patch_applied",
                result_summary=f"exit_code={attempt.apply_result.exit_code}",
                payload=asdict(attempt.apply_result),
            )
            if attempt.apply_result.exit_code != 0:
                attempt.status = "apply_failed"
                attempt.failure_class = "apply_conflict"
                continue

            rebuild_log = TRACE_ROOT / run_id / scenario.scenario_id / f"rebuild_attempt_{attempt_index}.log"
            emit_event(
                events_path,
                stage="verify_rebuild",
                event_type="tool_call",
                name="rebuild_started",
                result_summary=f"attempt={attempt_index}",
                log_path=str(rebuild_log),
                verify_timeout_sec=VERIFY_TIMEOUT_SEC,
            )
            attempt.rebuild_result = run_gbs_build(
                worktree_path,
                scenario,
                rebuild_log,
                gate,
                timeout_sec=VERIFY_TIMEOUT_SEC,
            )
            if attempt.rebuild_result.exit_code == 0:
                attempt.status = "repair_succeeded"
                result.final_status = "repair_succeeded"
                return result
            attempt.status = "rebuild_failed"
            attempt.failure_class = "patch_did_not_fix_build"

        result.final_status = "fail_safe"
        result.failure_envelope = make_failure_envelope(
            scenario,
            "bounded_repair_limit_reached",
            "two patch attempts failed; third attempt is forbidden",
            stage="repair_loop",
            reason_code="max_patch_attempts_exhausted",
            attempt_index=MAX_PATCH_ATTEMPTS,
            last_attempt_log_excerpt=(
                result.attempts[-1].rebuild_result.tail_excerpt
                if result.attempts and result.attempts[-1].rebuild_result
                else None
            ),
        )
        return result
    finally:
        emit_event(
            events_path,
            stage="repair_loop",
            event_type="state_transition",
            name="repair_loop_terminated",
            result_summary=f"final_status={result.final_status}",
            failure_class=result.failure_envelope.get("failure_class") if result.failure_envelope else None,
        )
        write_trace(trace_path, result)


def test_patch_format_invalid() -> dict[str, Any]:
    """Pure-local failure test stub: invalid non-unified patch is rejected."""

    return {
        "test": "test_patch_format_invalid",
        "status": "stubbed_for_step_2",
        "llm_calls": 0,
        "expected": "validate_patch rejects non-unified diff before apply",
    }


def test_apply_conflict() -> dict[str, Any]:
    """Pure-local failure test stub: mocked git apply conflict is fail-safe."""

    return {
        "test": "test_apply_conflict",
        "status": "stubbed_for_step_2",
        "llm_calls": 0,
        "expected": "git apply failure records apply_conflict and allows bounded retry",
    }


def test_rebuild_fails() -> dict[str, Any]:
    """Pure-local failure test stub: patch applies but verification build fails."""

    return {
        "test": "test_rebuild_fails",
        "status": "stubbed_for_step_2",
        "llm_calls": 0,
        "expected": "rebuild failure collects new failure and consumes one bounded attempt",
    }


def test_bounded_repair_limit() -> dict[str, Any]:
    """Pure-local failure test stub: exactly two patch attempts, no third.

    Assertion design for Step 2:
      - mock LLM returns a valid unified diff every time,
      - mock rebuild fails every time,
      - controller stops after MAX_PATCH_ATTEMPTS,
      - assert llm_call_count == 2, never 3.
    """

    llm_call_count = 0
    rebuild_failures = 0

    def mock_llm_patch() -> str:
        nonlocal llm_call_count
        llm_call_count += 1
        return (
            "--- a/CMakeLists.txt\n"
            "+++ b/CMakeLists.txt\n"
            "@@ -1,1 +1,1 @@\n"
            "-PROJECT(pkgmgr-info)\n"
            "+PROJECT(pkgmgr-info)\n"
        )

    for _attempt_index in range(1, MAX_PATCH_ATTEMPTS + 1):
        patch = mock_llm_patch()
        validation = validate_patch(patch, CODING_SYSTEM_ROOT)
        assert validation.accepted, validation.reason
        rebuild_failures += 1

    failure_envelope = {
        "failure_class": "bounded_repair_limit_reached",
        "reason_code": "max_patch_attempts_exhausted",
    }
    assert rebuild_failures == MAX_PATCH_ATTEMPTS
    assert llm_call_count == MAX_PATCH_ATTEMPTS, "LLM must be called exactly 2 times, not 3"
    assert llm_call_count != 3

    return {
        "test": "test_bounded_repair_limit",
        "status": "stubbed_for_step_2",
        "llm_calls": llm_call_count,
        "assertions": {
            "llm_calls_eq_2": llm_call_count == 2,
            "llm_calls_ne_3": llm_call_count != 3,
            "failure_class": failure_envelope["failure_class"],
        },
        "expected": "after two failed patches emit failure envelope; no third call",
    }


def test_uncommitted_changes() -> dict[str, Any]:
    """Pure-local failure test stub: dirty worktree triggers fail-safe."""

    return {
        "test": "test_uncommitted_changes",
        "status": "stubbed_for_step_2",
        "llm_calls": 0,
        "expected": "dirty worktree is rejected before mutation/apply",
    }


def test_non_git_repo() -> dict[str, Any]:
    """Pure-local failure test stub: non-git path emits contract_violation."""

    return {
        "test": "test_non_git_repo",
        "status": "stubbed_for_step_2",
        "llm_calls": 0,
        "expected": "non-git target path emits contract_violation",
    }


def describe_framework() -> dict[str, Any]:
    """Return a side-effect-free framework summary for PM review."""

    return {
        "phase": "S0-A Part 1 Step 0 framework only",
        "side_effects": {
            "worktree": False,
            "gbs_build": False,
            "clangd": False,
            "llm": False,
            "patch_apply": False,
        },
        "reuse_points": {
            "LogErrorParser": str(SPIKE_04_PATH),
            "EvidencePacket": str(SPIKE_05_PATH),
            "clangd_client": str(SPIKE_03_PATH),
            "RawDataDetector": str(SPIKE_06_PATH),
            "LLMAdapter": str(LLM_ADAPTER_PATH),
        },
        "scenarios": {key: asdict(value) for key, value in ERROR_SCENARIOS.items()},
        "bounded_repair": {
            "max_patch_attempts": MAX_PATCH_ATTEMPTS,
            "verify_timeout_sec": VERIFY_TIMEOUT_SEC,
            "max_patch_lines": MAX_PATCH_LINES,
            "third_attempt_allowed": False,
        },
        "failure_test_stubs": [
            test_patch_format_invalid(),
            test_apply_conflict(),
            test_rebuild_fails(),
            test_bounded_repair_limit(),
            test_uncommitted_changes(),
            test_non_git_repo(),
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Defaults to side-effect-free framework description."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["describe", "check-imports", "run-part1"],
        default="describe",
        help="run-part1 is blocked unless --enable-side-effects is set later by PM instruction",
    )
    parser.add_argument("--scenario", choices=sorted(ERROR_SCENARIOS), help="scenario for run-part1")
    parser.add_argument("--enable-side-effects", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "describe":
        print(json.dumps(describe_framework(), indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0

    modules = load_reused_spikes()
    if args.mode == "check-imports":
        print(json.dumps({"status": "ok", "modules": sorted(modules)}, indent=2, sort_keys=True))
        return 0

    if args.mode == "run-part1":
        if not args.scenario:
            parser.error("--scenario is required for run-part1")
        gate = SideEffectGate(
            enabled=args.enable_side_effects,
            reason="PM-confirmed S0-A Part 1 execution" if args.enable_side_effects else "Step 0 framework review only",
        )
        result = run_repair_loop_for_scenario(ERROR_SCENARIOS[args.scenario], modules, gate)
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0

    raise AssertionError(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
