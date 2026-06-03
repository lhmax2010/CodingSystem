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
import atexit
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field, is_dataclass
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
PART2_RESULTS_PATH = S0A_TMP_ROOT / "part2_results.json"
PART2_REVIEW_FORM_PATH = S0A_TMP_ROOT / "part2_review_form.md"
PART2_PATCH_ROOT = S0A_TMP_ROOT / "part2_patches"

GBS_CONF = Path("/home/linhao/Toolchain/gbs_llvm_coding.conf")
GBS_ROOT = Path("/home/linhao/GBS-ROOT-TIZEN-LLVM/local/BUILD-ROOTS/scratch.x86_64.0")
CHROOT_BUILD_PREFIX = "/home/abuild/rpmbuild/BUILD/pkgmgr-info-0.37.0"
CHROOT_BUILD_HOST = GBS_ROOT / "home/abuild/rpmbuild/BUILD/pkgmgr-info-0.37.0"
CLANGD_WORKSPACE_DIR = TMP_ROOT / "clangd_workspace" / "pkgmgr-info"
COMPILE_COMMANDS_RAW = CLANGD_WORKSPACE_DIR / "compile_commands.json.chroot_raw"
COMPILE_COMMANDS_HOST = CLANGD_WORKSPACE_DIR / "compile_commands.json"
GBS_ARCH = "x86_64"
MAX_PATCH_ATTEMPTS = 2
VERIFY_TIMEOUT_SEC = 300
MAX_PATCH_LINES = 200  # +/- 变更行数总和(Compiler Agent v5.2-RC2.4 §5.2)
MAX_CHROOT_CONFIGURE_SEC = 60
MAX_CLANGD_INITIALIZE_SEC = 30
MAX_CLANGD_QUERY_SEC = 10
MAX_CLANGD_SELF_TEST_SEC = 30
CLANGD_INDEX_DRAIN_SEC = 8
DEFAULT_CLANGD = Path("/usr/bin/clangd")
PART2_SAMPLE_COUNT = 3
PART2_LLM_TIMEOUT_RETRIES = 1
PART2_RAW_LOG_CHAR_LIMIT = 12000
CNEI_EVIDENCE_PACKET_MAX_TOKENS = 4000
PART2_SHARED_SYSTEM_PROMPT = (
    "You are repairing a Tizen C/C++ package. Return only a unified diff.\n"
    "The diff context must match the existing source exactly.\n"
    "Do not restructure or refactor unrelated code.\n"
    "Do not rename all call sites unless evidence explicitly supports it.\n"
    "Prefer the minimal package-local fix.\n"
    "Repair scope is limited to the current package worktree only."
)
NEGATIVE_FACT_REQUIRED_FIELDS = {
    "check",
    "result",
    "scope",
    "confidence",
    "source",
    "implication",
}
NEGATIVE_FACT_ALLOWED_RESULTS = {"not_found", "unavailable", "present"}
NEGATIVE_FACT_FORBIDDEN_PHRASES = (
    "must",
    "do not",
    "prefer",
    "return only",
    "diff context",
    "repair scope",
    "rename all call sites",
    "minimal fix",
)
_CLANGD_CACHE: dict[str, Any] = {}

SPIKE_03_PATH = SPIKE_REPORTS_DATA / "spike_03_clangd_lsp_eval.py"
SPIKE_04_PATH = SPIKE_REPORTS_DATA / "spike_04_log_parser.py"
SPIKE_05_PATH = SPIKE_REPORTS_DATA / "spike_05_evidence_packet.py"
SPIKE_06_PATH = SPIKE_REPORTS_DATA / "spike_06_raw_data_detector.py"
REWRITE_COMPILE_COMMANDS_PATH = SPIKE_REPORTS_DATA / "rewrite_compile_commands.py"
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
    llm_error: dict[str, str] | None = None
    patch_text: str = ""
    patch_validation: PatchValidationResult | None = None
    apply_result: CommandResult | None = None
    rebuild_result: CommandResult | None = None
    status: str = "not_started"
    failure_class: str | None = None
    error: dict[str, str] | None = None


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


PART_2_VARIANTS: dict[str, dict[str, Any]] = {
    "A": {
        "variant_id": "A",
        "name": "with_negative_facts",
        "description": "Full EvidencePacket, including negative_facts.",
        "input_strategy": "evidence_packet",
        "include_negative_facts": True,
        "include_raw_log": False,
    },
    "B": {
        "variant_id": "B",
        "name": "without_negative_facts",
        "description": "EvidencePacket with negative_facts removed.",
        "input_strategy": "evidence_packet",
        "include_negative_facts": False,
        "include_raw_log": False,
    },
    "C": {
        "variant_id": "C",
        "name": "evidence_packet_baseline",
        "description": "EvidencePacket baseline for comparison with raw-log workflow.",
        "input_strategy": "evidence_packet",
        "include_negative_facts": True,
        "include_raw_log": False,
    },
    "D": {
        "variant_id": "D",
        "name": "raw_log_baseline",
        "description": "Raw build log baseline, local-only, truncated for token budget comparison.",
        "input_strategy": "raw_log",
        "include_negative_facts": False,
        "include_raw_log": True,
        "raw_log_char_limit": PART2_RAW_LOG_CHAR_LIMIT,
    },
}


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp for trace/event records."""

    return datetime.now(timezone.utc).isoformat()


def safe_asdict(obj: Any) -> Any:
    """Convert dataclass values to JSON-friendly structures without crashing.

    dataclasses.asdict() only accepts dataclass instances. The repair loop also
    stores lists, dicts, pathlib paths, and partially populated objects in
    exception paths, so trace writing must be more forgiving.
    """

    if is_dataclass(obj) and not isinstance(obj, type):
        return safe_asdict(asdict(obj))
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(key): safe_asdict(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_asdict(value) for value in obj]
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return safe_asdict(vars(obj))
    return obj


def estimate_text_tokens(text: str) -> int:
    """Estimate tokens for Part 2 metadata without depending on a running spike module."""

    try:
        import tiktoken  # type: ignore[import-not-found]

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, (len(text) + 3) // 4)


def estimate_json_tokens(value: Any) -> int:
    """Estimate tokens for a JSON-serializable value."""

    return estimate_text_tokens(
        json.dumps(safe_asdict(value), ensure_ascii=False, sort_keys=True, default=str)
    )


def refresh_packet_token_metadata(packet: dict[str, Any]) -> None:
    """Refresh packet token metadata after Part 2 injects negative_facts."""

    collection_metadata = packet.setdefault("collection_metadata", {})
    encoded = json.dumps(packet, ensure_ascii=False, sort_keys=True, default=str)
    token_estimate = estimate_text_tokens(encoded)
    collection_metadata["total_tokens_estimate"] = token_estimate
    collection_metadata["packet_char_count"] = len(encoded)
    collection_metadata["budget_tokens"] = CNEI_EVIDENCE_PACKET_MAX_TOKENS
    collection_metadata["budget_pass"] = token_estimate <= CNEI_EVIDENCE_PACKET_MAX_TOKENS
    collection_metadata["token_estimator"] = "tiktoken_or_chars_div_4"


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
        "rewrite_compile_commands": load_spike_module("s0a_rewrite_compile_commands", REWRITE_COMPILE_COMMANDS_PATH),
        "llm_adapter": load_spike_module("s0a_llm_adapter", LLM_ADAPTER_PATH),
    }
    required: dict[str, list[str]] = {
        "spike_03": ["JsonRpcClient", "LogCollector", "uri", "normalize_locs"],
        "spike_04": ["parse_log"],
        "spike_05": ["bounded_excerpt", "estimate_tokens", "make_packet"],
        "spike_06": ["RawDataDetector"],
        "rewrite_compile_commands": ["rewrite_commands"],
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
    """Create an isolated clone for the scenario.

    GBS does not recognize linked git-worktree checkouts whose .git is a file,
    so S0-A uses git clone --shared. This keeps object storage cheap while
    presenting GBS with a normal .git directory.
    """

    gate.require("git clone --shared")
    source_repo = package_repo_path(scenario)
    ensure_git_repo(source_repo)
    ensure_clean_worktree(source_repo)
    worktree_path = WORKTREE_ROOT / f"{run_id}_{scenario.scenario_id}"
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    if worktree_path.exists():
        raise RuntimeError(f"isolated clone already exists: {worktree_path}")

    clone = subprocess.run(
        ["git", "clone", "--shared", "--quiet", str(source_repo.resolve()), str(worktree_path)],
        cwd=CODING_SYSTEM_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    if clone.returncode != 0:
        raise RuntimeError(f"git clone failed: {clone.stderr.strip()}")

    git_dot = worktree_path / ".git"
    if not git_dot.is_dir():
        kind = "file" if git_dot.is_file() else "missing"
        raise RuntimeError(f"expected .git directory in isolated clone, got: {kind}")

    source_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    subprocess.run(["git", "checkout", "--quiet", source_head], cwd=worktree_path, check=True)
    ensure_clean_worktree(worktree_path)
    return worktree_path


def cleanup_worktree(worktree_path: Path, gate: SideEffectGate) -> None:
    """Remove an isolated --shared clone."""

    gate.require("cleanup isolated clone")
    if worktree_path.exists():
        shutil.rmtree(worktree_path)


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
    log_path.parent.mkdir(parents=True, exist_ok=True)
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


def parse_build_log_extended(log_path: Path, modules: dict[str, ModuleType]) -> ParsedBuildFailure:
    """Wrap S0-04 parser with local S0-A unknown_type_name fallback.

    S0-04 is a frozen Sprint 0 artifact. Its own report records the known gap
    that unknown type name diagnostics and primary/cascade classification are
    not covered. S0-A keeps that artifact intact and adds only a local wrapper
    so the repair-loop spike can exercise E3.
    """

    primary_result = parse_build_log(log_path, modules)
    if primary_result.parsed_error_count != 0:
        return primary_result

    extended = _parse_unknown_type_name_cascade(log_path)
    if extended.parsed_error_count > 0:
        return extended
    return primary_result


def _parse_unknown_type_name_cascade(log_path: Path) -> ParsedBuildFailure:
    """Identify Clang unknown type name diagnostics and same-type cascades."""

    pattern = re.compile(
        r"(?:^|\s)(?P<path>/[^:\s]+|[^:\s]+):(?P<line>\d+):(?P<col>\d+):\s+"
        r"error:\s+unknown type name\s+[`'\"](?P<type>[A-Za-z_][A-Za-z0-9_]*)[`'\"]"
    )
    errors: list[dict[str, Any]] = []
    primary: dict[str, Any] | None = None
    cascade_count = 0

    try:
        with log_path.open(errors="replace") as stream:
            for log_line_no, line in enumerate(stream, start=1):
                match = pattern.search(line)
                if not match:
                    continue
                type_name = match.group("type")
                error = {
                    "error_type": "unknown_type_name",
                    "path": match.group("path"),
                    "line": int(match.group("line")),
                    "col": int(match.group("col")),
                    "line_no": log_line_no,
                    "type_name": type_name,
                    "symbol": type_name,
                    "symbol_for_clangd": type_name,
                    "message": line.strip(),
                    "source_location": {
                        "file": match.group("path"),
                        "line": int(match.group("line")),
                        "column": int(match.group("col")),
                    },
                }
                errors.append(error)
                if primary is None:
                    primary = dict(error)
                    primary["same_type_cascade_count"] = 0
                    primary["cascade_count"] = 0
                elif type_name == primary["type_name"]:
                    cascade_count += 1
    except OSError:
        pass

    if primary:
        primary["same_type_cascade_count"] = cascade_count
        primary["cascade_count"] = max(0, len(errors) - 1)
        primary["total_unknown_type_name_errors"] = len(errors)

    raw_result = {
        "parser": "spike_A_unknown_type_name_v1",
        "log_path": str(log_path),
        "parsed_error_count": len(errors),
        "primary_candidate": primary,
        "primary_candidate_policy": "first_unknown_type_name_with_same_type_cascade_count",
        "counts_by_type": {"unknown_type_name": len(errors)} if errors else {},
        "errors": errors[:80],
    }
    return ParsedBuildFailure(
        parser_name="spike_A_unknown_type_name_v1",
        log_path=log_path,
        parsed_error_count=len(errors),
        primary_candidate=primary,
        raw_result=raw_result,
    )


SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp"}


def find_clangd_binary() -> Path | None:
    """Find clangd on host or in the GBS LLVM build root."""

    configured = os.environ.get("CLANGD")
    candidates = [
        Path(configured) if configured else None,
        Path(shutil.which("clangd")) if shutil.which("clangd") else None,
        DEFAULT_CLANGD,
    ]
    for candidate in candidates:
        if candidate and candidate.exists() and os.access(candidate, os.X_OK):
            return candidate
    return None


def iter_source_files(source_roots: list[Path]) -> list[Path]:
    """Return C/C++ source files under source_roots, excluding git/build noise."""

    files: list[Path] = []
    skip_parts = {".git", "build", "cmake-build-debug", "cmake-build-release"}
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                continue
            if skip_parts.intersection(path.parts):
                continue
            files.append(path.resolve())
    source_suffixes = {".c", ".cc", ".cpp", ".cxx"}
    return sorted(set(files), key=lambda path: (0 if path.suffix in source_suffixes else 1, str(path)))


def find_symbol_occurrences(source_roots: list[Path], symbol: str, *, limit: int = 80) -> list[dict[str, Any]]:
    """Find query positions for a symbol without replacing clangd semantics."""

    occurrences: list[dict[str, Any]] = []
    pattern = re.compile(r"\b" + re.escape(symbol) + r"\b")
    for path in iter_source_files(source_roots):
        try:
            lines = path.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for line_index, line in enumerate(lines):
            match = pattern.search(line)
            if not match:
                continue
            is_definition = line.strip().startswith("typedef") or re.search(
                rf"\b(?:struct|enum|class)\b.*\b{re.escape(symbol)}\b",
                line,
            ) is not None
            occurrences.append(
                {
                    "path": path,
                    "line": line_index,
                    "character": match.start(),
                    "line1": line_index + 1,
                    "character1": match.start() + 1,
                    "snippet": line.strip(),
                    "is_definition_candidate": is_definition,
                }
            )
            if len(occurrences) >= limit:
                return occurrences
    return occurrences


def include_dirs_for_roots(source_roots: list[Path]) -> list[Path]:
    """Build common include directories for generated clangd compile commands."""

    suffixes = [
        "include",
        "src",
        "src/common",
        "src/common/socket",
        "src/common/parcel",
        "src/common/shared_memory",
        "src/common/filter_checker",
        "src/parser/include",
        "src/server",
        "src/server/cynara_checker",
        "src/server/database",
        "src/server/request_handler",
        "tests",
        "test",
    ]
    dirs: list[Path] = []
    for root in source_roots:
        dirs.append(root)
        for suffix in suffixes:
            candidate = root / suffix
            if candidate.exists():
                dirs.append(candidate)
    return sorted(set(path.resolve() for path in dirs if path.exists()))


def generated_compile_commands_dir(
    workspace_root: Path,
    source_roots: list[Path],
    symbol: str,
) -> Path:
    """Create a minimal compile_commands.json for clangd self/spike queries."""

    out_dir = S0A_TMP_ROOT / "clangd_compile_commands" / re.sub(r"[^A-Za-z0-9_.-]+", "_", symbol)
    out_dir.mkdir(parents=True, exist_ok=True)
    include_args = " ".join(f"-I{path}" for path in include_dirs_for_roots(source_roots))
    commands = []
    for path in iter_source_files(source_roots):
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        if symbol not in text:
            continue
        is_c = path.suffix == ".c"
        language = "-x c" if is_c else "-x c++"
        standard = "-std=c11" if is_c else "-std=c++17"
        compiler = "clang" if is_c else "clang++"
        commands.append(
            {
                "directory": str(workspace_root),
                "file": str(path),
                "command": (
                    f"{compiler} {language} {standard} {include_args} "
                    "-Wno-unknown-warning-option -c "
                    f"{path}"
                ),
            }
        )
    (out_dir / "compile_commands.json").write_text(
        json.dumps(commands, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_dir


def select_query_occurrence(occurrences: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Prefer a normal source-code use, then a definition-like occurrence."""

    for occurrence in occurrences:
        path = Path(occurrence["path"])
        if path.suffix in {".c", ".cc", ".cpp", ".cxx"} and not occurrence.get("is_definition_candidate"):
            return occurrence
    for occurrence in occurrences:
        if not occurrence.get("is_definition_candidate"):
            return occurrence
    for occurrence in occurrences:
        if occurrence.get("is_definition_candidate"):
            return occurrence
    return occurrences[0] if occurrences else None


def did_open_file(client: Any, modules: dict[str, ModuleType], opened: set[Path], path: Path) -> None:
    """Open a file in clangd via LSP textDocument/didOpen."""

    path = path.resolve()
    if path in opened:
        return
    language_id = "c" if path.suffix == ".c" else "cpp"
    client.notify(
        "textDocument/didOpen",
        {
            "textDocument": {
                "uri": modules["spike_03"].uri(path),
                "languageId": language_id,
                "version": 1,
                "text": path.read_text(errors="replace"),
            }
        },
    )
    opened.add(path)


def symbol_from_parsed_failure(parsed_failure: ParsedBuildFailure) -> str | None:
    """Extract a clangd-queryable symbol from S0-04 parsed output."""

    primary = parsed_failure.primary_candidate or {}
    symbol = primary.get("symbol")
    if isinstance(symbol, str) and symbol and not symbol.endswith((".h", ".hh", ".hpp")):
        return symbol
    message = str(primary.get("message", ""))
    quoted = re.search(r"'(?P<symbol>[A-Za-z_][A-Za-z0-9_]*)'", message)
    if quoted:
        return quoted.group("symbol")
    return None


def cleanup_clangd_client() -> None:
    """Best-effort shutdown for the cached clangd subprocess."""

    client = _CLANGD_CACHE.get("client")
    proc = _CLANGD_CACHE.get("proc")
    if client is not None:
        try:
            client.request("shutdown", {}, timeout=3.0)
            client.notify("exit")
        except Exception:
            pass
    if proc is not None:
        try:
            proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
    _CLANGD_CACHE.clear()


def _ensure_compile_commands_for_host_clangd(
    modules: dict[str, ModuleType],
    *,
    force_regenerate: bool = False,
) -> dict[str, Any]:
    """Generate/copy/rewrite compile_commands.json for host clangd lazily."""

    started = time.perf_counter()
    if COMPILE_COMMANDS_HOST.exists() and not force_regenerate:
        return {
            "status": "ok",
            "cache_hit": True,
            "output_path": str(COMPILE_COMMANDS_HOST),
            "elapsed_sec": round(time.perf_counter() - started, 3),
        }

    CLANGD_WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    raw_source = CHROOT_BUILD_HOST / "compile_commands.json"
    configure_tail = "reuse_existing_chroot_compile_commands"
    if not raw_source.exists():
        configure_script = "\n".join(
            [
                "set -e",
                f"cd {CHROOT_BUILD_PREFIX}",
                'cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release -G "Unix Makefiles" .',
                "test -s compile_commands.json",
                "exit",
            ]
        )
        try:
            result = subprocess.run(
                ["gbs", "chroot", str(GBS_ROOT)],
                input=configure_script,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=MAX_CHROOT_CONFIGURE_SEC,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"chroot configure timed out after {MAX_CHROOT_CONFIGURE_SEC}s") from exc
        configure_tail = "\n".join(result.stdout.splitlines()[-20:])
        if result.returncode != 0 and not raw_source.exists():
            raise RuntimeError(f"chroot configure failed rc={result.returncode}: {configure_tail}")

    if not raw_source.exists():
        raise RuntimeError(f"compile_commands.json missing after configure: {raw_source}")

    shutil.copy2(raw_source, COMPILE_COMMANDS_RAW)
    rewrite_result = modules["rewrite_compile_commands"].rewrite_commands(
        str(COMPILE_COMMANDS_RAW),
        str(COMPILE_COMMANDS_HOST),
        str((CODING_SYSTEM_ROOT / "codes" / "pkgmgr-info").resolve()),
        str(GBS_ROOT),
        CHROOT_BUILD_PREFIX,
    )
    elapsed = time.perf_counter() - started
    metadata = {
        "status": "ok",
        "cache_hit": False,
        "configure_tail": configure_tail,
        "raw_path": str(COMPILE_COMMANDS_RAW),
        "output_path": str(COMPILE_COMMANDS_HOST),
        "rewrite": rewrite_result,
        "elapsed_sec": round(elapsed, 3),
    }
    _CLANGD_CACHE["compile_commands_metadata"] = metadata
    return metadata


def _get_or_start_host_clangd_client(modules: dict[str, ModuleType]) -> dict[str, Any]:
    """Start host clangd once per spike run and reuse the LSP client."""

    proc = _CLANGD_CACHE.get("proc")
    if _CLANGD_CACHE.get("client") is not None and proc is not None and proc.poll() is None:
        return _CLANGD_CACHE

    clangd = find_clangd_binary()
    if clangd is None:
        raise RuntimeError("host clangd not found")

    cmd = [
        str(clangd),
        f"--compile-commands-dir={CLANGD_WORKSPACE_DIR}",
        "--background-index",
        "--log=error",
        "--limit-results=1000",
    ]
    started = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    log = modules["spike_03"].LogCollector(proc)
    client = modules["spike_03"].JsonRpcClient(proc)
    init = client.request(
        "initialize",
        {
            "processId": os.getpid(),
            "rootUri": modules["spike_03"].uri((CODING_SYSTEM_ROOT / "codes" / "pkgmgr-info").resolve()),
            "capabilities": {
                "window": {"workDoneProgress": True},
                "textDocument": {"definition": {"linkSupport": True}, "references": {}},
            },
            "initializationOptions": {"clangdFileStatus": True},
        },
        timeout=MAX_CLANGD_INITIALIZE_SEC,
    )
    client.notify("initialized", {})
    _CLANGD_CACHE.update(
        {
            "client": client,
            "proc": proc,
            "log": log,
            "cmd": cmd,
            "opened": set(),
            "init_result": init,
            "init_sec": round(time.perf_counter() - started, 3),
            "indexed_once": False,
        }
    )
    if not _CLANGD_CACHE.get("atexit_registered"):
        atexit.register(cleanup_clangd_client)
        _CLANGD_CACHE["atexit_registered"] = True
    return _CLANGD_CACHE


def _extract_symbol_for_scenario(
    scenario: ErrorScenario,
    parsed_failure: ParsedBuildFailure,
) -> tuple[str | None, str]:
    """Extract the scenario-specific semantic query target."""

    primary = parsed_failure.primary_candidate or {}
    message = str(primary.get("message", ""))
    if scenario.error_type == "cannot_find_header":
        header = primary.get("missing_header") or primary.get("header")
        if not header:
            match = re.search(r"(?:fatal error:|file not found:?)\s*[<\"']?([^>\"'\s]+\.h)", message)
            if match:
                header = match.group(1)
        return (str(header), "header_include") if header else (None, "header_include")

    if scenario.error_type == "undefined_reference":
        symbol = primary.get("undefined_symbol") or primary.get("symbol")
        if not symbol:
            match = re.search(r"undefined reference to [`'\"“]?([^`'\"”]+)", message)
            if match:
                symbol = match.group(1).strip()
        return (str(symbol), "symbol") if symbol else (None, "symbol")

    if scenario.error_type == "unknown_type_name":
        symbol = primary.get("type_name") or primary.get("symbol_for_clangd") or primary.get("symbol")
        if not symbol:
            match = re.search(r"unknown type name [`'\"“]?([A-Za-z_][A-Za-z0-9_]*)", message)
            if match:
                symbol = match.group(1)
        if not symbol:
            symbol = symbol_from_parsed_failure(parsed_failure)
        return (str(symbol), "symbol") if symbol else (None, "symbol")

    symbol = symbol_from_parsed_failure(parsed_failure)
    return (symbol, "symbol") if symbol else (None, "symbol")


def _collect_header_include_facts(header: str, source_root: Path) -> dict[str, Any]:
    """Collect include references for cannot_find_header scenarios."""

    references: list[dict[str, Any]] = []
    include_pattern = re.compile(r"#\s*include\s*[<\"]" + re.escape(header) + r"[>\"]")
    for path in iter_source_files([source_root]):
        try:
            lines = path.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for line_index, line in enumerate(lines):
            if include_pattern.search(line):
                references.append(
                    {
                        "path": str(path),
                        "line": line_index,
                        "character": line.find(header),
                        "line1": line_index + 1,
                        "character1": line.find(header) + 1,
                        "snippet": line.strip(),
                    }
                )

    definition = None
    search_roots = [
        source_root,
        GBS_ROOT / "usr" / "include",
    ]
    for root in search_roots:
        matches = list(root.rglob(header)) if root.exists() else []
        if matches:
            definition = {"path": str(matches[0]), "line1": 1, "snippet": f"header file {header}"}
            break

    return {
        "status": "ok" if references or definition else "degraded",
        "reason": None if references or definition else "header_not_found",
        "query_kind": "header_include",
        "symbol": header,
        "references": references[:50],
        "reference_count": len(references),
        "definition": definition,
        "definition_count": 1 if definition else 0,
    }


def _query_host_clangd_symbol(symbol: str, modules: dict[str, ModuleType]) -> dict[str, Any]:
    """Query host clangd for definition/references of a normal symbol."""

    started = time.perf_counter()
    source_root = (CODING_SYSTEM_ROOT / "codes" / "pkgmgr-info").resolve()
    occurrences = find_symbol_occurrences([source_root], symbol, limit=200)
    query = select_query_occurrence(occurrences)
    if query is None:
        return {
            "status": "degraded",
            "reason": "symbol_not_found_in_sources",
            "query_kind": "symbol",
            "symbol": symbol,
            "references": [],
            "reference_count": 0,
            "definition": None,
            "definition_count": 0,
            "elapsed_sec": round(time.perf_counter() - started, 3),
        }

    state = _get_or_start_host_clangd_client(modules)
    client = state["client"]
    opened: set[Path] = state["opened"]
    did_open_file(client, modules, opened, query["path"])
    drain_sec = CLANGD_INDEX_DRAIN_SEC if not state.get("indexed_once") else 0.5
    client.drain(drain_sec)
    state["indexed_once"] = True

    params = {
        "textDocument": {"uri": modules["spike_03"].uri(query["path"])},
        "position": {"line": query["line"], "character": query["character"]},
    }
    ref_started = time.perf_counter()
    references_response = client.request(
        "textDocument/references",
        {**params, "context": {"includeDeclaration": True}},
        timeout=MAX_CLANGD_QUERY_SEC,
    )
    references_sec = time.perf_counter() - ref_started

    def_started = time.perf_counter()
    definition_response = client.request("textDocument/definition", params, timeout=MAX_CLANGD_QUERY_SEC)
    definition_sec = time.perf_counter() - def_started

    references = modules["spike_03"].normalize_locs(references_response.get("result"))
    definitions = modules["spike_03"].normalize_locs(definition_response.get("result"))
    status = "ok" if references or definitions else "degraded"
    return {
        "status": status,
        "reason": None if status == "ok" else "missing_definition_and_references",
        "query_kind": "symbol",
        "symbol": symbol,
        "query": {**query, "path": str(query["path"])},
        "references": references[:50],
        "reference_count": len(references),
        "definition": definitions[0] if definitions else None,
        "definition_count": len(definitions),
        "timings": {
            "references_sec": round(references_sec, 3),
            "definition_sec": round(definition_sec, 3),
            "total_query_sec": round(time.perf_counter() - started, 3),
            "index_drain_sec": drain_sec,
        },
        "clangd": {
            "binary": str(find_clangd_binary()),
            "command": state.get("cmd"),
            "init_sec": state.get("init_sec"),
            "stderr_tail": getattr(state.get("log"), "lines", [])[-80:],
        },
    }


def query_clangd_symbol(
    *,
    workspace_root: Path,
    source_roots: list[Path],
    symbol: str,
    modules: dict[str, ModuleType],
    max_total_sec: int = MAX_CLANGD_SELF_TEST_SEC,
) -> dict[str, Any]:
    """Compatibility wrapper: query host clangd with rewritten compile commands."""

    del workspace_root, source_roots, max_total_sec
    _ensure_compile_commands_for_host_clangd(modules)
    return _query_host_clangd_symbol(symbol, modules)


def collect_clangd_facts(
    scenario: ErrorScenario,
    worktree_path: Path,
    parsed_failure: ParsedBuildFailure,
    modules: dict[str, ModuleType],
    gate: SideEffectGate,
) -> dict[str, Any]:
    """Collect semantic facts via host clangd and explicit compile_commands.

    Spike path: GBS chroot generates compile_commands.json once, the helper
    rewrites chroot paths to host paths, and host clangd indexes
    codes/pkgmgr-info. Failures degrade evidence instead of aborting repair.
    """

    del worktree_path
    gate.require("clangd semantic collection")
    started = time.perf_counter()
    degraded_reasons: list[str] = []
    facts: dict[str, Any] = {
        "status": "ok",
        "references": [],
        "reference_count": 0,
        "definition": None,
        "definition_count": 0,
        "confidence": "high",
        "semantic_unavailable": False,
        "compile_commands_provenance": "explicit_path",
        "degraded_reasons": degraded_reasons,
        "backend": "clangd_18.1.3_host",
        "semantic_source_root": str((CODING_SYSTEM_ROOT / "codes" / "pkgmgr-info").resolve()),
    }

    try:
        facts["compile_commands"] = _ensure_compile_commands_for_host_clangd(modules)
    except Exception as exc:
        degraded_reasons.append(f"chroot_configure_failed: {exc}")
        facts.update(
            {
                "status": "degraded",
                "confidence": "low",
                "semantic_unavailable": True,
                "elapsed_sec": round(time.perf_counter() - started, 3),
            }
        )
        return facts

    symbol, query_kind = _extract_symbol_for_scenario(scenario, parsed_failure)
    facts["query_kind"] = query_kind
    facts["symbol"] = symbol
    if not symbol:
        degraded_reasons.append("no_symbol_to_query")
        facts.update(
            {
                "status": "degraded",
                "confidence": "low",
                "semantic_unavailable": True,
                "elapsed_sec": round(time.perf_counter() - started, 3),
            }
        )
        return facts

    try:
        if query_kind == "header_include":
            query_result = _collect_header_include_facts(symbol, CODING_SYSTEM_ROOT / "codes" / "pkgmgr-info")
        else:
            query_result = _query_host_clangd_symbol(symbol, modules)
        facts.update(query_result)
        if query_result.get("status") != "ok":
            degraded_reasons.append(str(query_result.get("reason", "clangd_query_degraded")))
            facts["status"] = "degraded"
            facts["confidence"] = "medium"
    except Exception as exc:
        degraded_reasons.append(f"clangd_query_failed: {exc}")
        facts.update(
            {
                "status": "degraded",
                "confidence": "low",
                "semantic_unavailable": True,
            }
        )

    facts["degraded_reasons"] = degraded_reasons
    facts["elapsed_sec"] = round(time.perf_counter() - started, 3)
    return facts


def collect_clangd_facts_integration_self_test(modules: dict[str, ModuleType]) -> dict[str, Any]:
    """Self-test collect_clangd_facts end-to-end on pkgmgrinfo_appinfo_h."""

    cleanup_clangd_client()
    if COMPILE_COMMANDS_HOST.exists():
        COMPILE_COMMANDS_HOST.unlink()
    if COMPILE_COMMANDS_RAW.exists():
        COMPILE_COMMANDS_RAW.unlink()

    scenario = ERROR_SCENARIOS["E3_unknown_type_name_cascade"]
    parsed = ParsedBuildFailure(
        parser_name="self-test",
        log_path=Path("/tmp/coding-system-s0/self-test-clangd-integration.log"),
        parsed_error_count=1,
        primary_candidate={
            "message": "unknown type name 'pkgmgrinfo_appinfo_h'",
            "type_name": "pkgmgrinfo_appinfo_h",
            "source_location": {
                "file": str(CODING_SYSTEM_ROOT / "codes/pkgmgr-info/src/common/pkgmgrinfo_appinfo.cc"),
                "line": 91,
                "column": 33,
            },
        },
        raw_result={"parser": "self-test"},
    )
    gate = SideEffectGate(enabled=True, reason="self-test-clangd-integration")
    started = time.perf_counter()
    facts = collect_clangd_facts(
        scenario,
        CODING_SYSTEM_ROOT / "codes" / "pkgmgr-info",
        parsed,
        modules,
        gate,
    )
    definition = facts.get("definition") or {}
    pass_status = (
        facts.get("status") == "ok"
        and int(facts.get("reference_count", 0)) >= 100
        and str(definition.get("path", "")).endswith("include/pkgmgrinfo_type.h")
    )
    return {
        "test": "self-test-clangd-integration",
        "status": "PASS" if pass_status else "FAIL",
        "elapsed_sec": round(time.perf_counter() - started, 3),
        "expected": {
            "references_count_min": 100,
            "definition_suffix": "include/pkgmgrinfo_type.h",
        },
        "facts": facts,
    }


def collect_clangd_facts_self_test(modules: dict[str, ModuleType]) -> dict[str, Any]:
    """Backward-compatible alias for the integrated clangd self-test."""

    result = collect_clangd_facts_integration_self_test(modules)
    result["test"] = "self-test-clangd"
    return result


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
    clangd_facts = collect_clangd_facts(scenario, worktree_path, parsed_failure, modules, gate)
    if clangd_facts.get("status") != "ok":
        degraded.append(f"clangd:{clangd_facts.get('reason', 'unknown_degraded_reason')}")

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
            "scenario_mutation": safe_asdict(scenario),
            "parser_primary_candidate": primary,
            "clangd": clangd_facts,
        },
        "negative_facts": [],
        "known_issue_matches": [],
        "log_excerpt": [excerpt],
        "cascade_summary": {
            "strategy": "framework_placeholder",
            "note": "S2b-03 owns full primary/cascade parser. S0-A uses the S0-04 primary candidate plus bounded summary.",
        } if scenario.error_type == "unknown_type_name" else None,
        "semantic_unavailable": bool(clangd_facts.get("semantic_unavailable")),
        "clangd_stale": False,
        "compile_commands_provenance": clangd_facts.get("compile_commands_provenance", "explicit_path"),
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
    packet = modules["spike_05"].make_packet(safe_asdict(packet), start)
    detector = modules["spike_06"].RawDataDetector()
    raw_status = safe_asdict(detector.validate(packet))
    return EvidenceCollectionResult(packet=packet, raw_data_status=raw_status, clangd_facts=clangd_facts, degraded_reasons=degraded)


def collect_negative_facts(
    scenario: ErrorScenario,
    parsed_failure: ParsedBuildFailure,
    worktree_path: Path,
) -> list[dict[str, Any]]:
    """Collect CNEI-style tool-derived negative code facts on mutated worktree.

    Negative facts are not behavioral prompt guidance. They are bounded facts
    from concrete checks against the error-time source/build configuration.
    """

    if scenario.error_type == "undefined_reference":
        return [_negative_fact_e2_missing_parser_library(worktree_path)]
    if scenario.error_type == "cannot_find_header":
        return [_negative_fact_e1_missing_parser_include(worktree_path)]
    if scenario.error_type == "unknown_type_name":
        return [_negative_fact_e3_missing_typedef(worktree_path, parsed_failure)]
    return []


def _grep_fixed(pattern: str, paths: list[Path], *, cwd: Path) -> tuple[str, str]:
    """Run grep -F for a bounded fact check."""

    command = ["grep", "-nF", pattern, *[str(path) for path in paths]]
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable", " ".join(command)
    if result.returncode == 0:
        return "present", " ".join(command)
    if result.returncode == 1:
        return "not_found", " ".join(command)
    return "unavailable", " ".join(command)


def _rg_fixed(pattern: str, paths: list[Path], *, cwd: Path) -> tuple[str, str]:
    """Run ripgrep for a bounded fact check, reporting unavailable if rg cannot run."""

    rg = shutil.which("rg")
    if rg is None:
        return "unavailable", f"rg -nF {pattern!r} " + " ".join(str(path) for path in paths)
    command = [rg, "-nF", pattern, *[str(path) for path in paths]]
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable", " ".join(command)
    if result.returncode == 0:
        return "present", " ".join(command)
    if result.returncode == 1:
        return "not_found", " ".join(command)
    return "unavailable", " ".join(command)


def _fact_confidence(result: str, default: str = "high") -> str:
    return default if result != "unavailable" else "medium"


def _negative_fact_e1_missing_parser_include(worktree_path: Path) -> dict[str, Any]:
    result, command = _grep_fixed(
        "src/parser/include",
        [Path("CMakeLists.txt")],
        cwd=worktree_path,
    )
    return {
        "check": "active include dirs / CMake INCLUDE_DIRECTORIES contains src/parser/include",
        "result": result,
        "scope": "build_config",
        "confidence": _fact_confidence(result),
        "source": "CMake grep",
        "implication": "the header include directory is not available to this target",
        "command": command,
    }


def _negative_fact_e2_missing_parser_library(worktree_path: Path) -> dict[str, Any]:
    result, command = _grep_fixed(
        "${TARGET_LIB_PKGMGR_PARSER}",
        [Path("tool/CMakeLists.txt")],
        cwd=worktree_path,
    )
    return {
        "check": "tool/CMakeLists.txt target_link_libraries contains ${TARGET_LIB_PKGMGR_PARSER}",
        "result": result,
        "scope": "build_config",
        "confidence": _fact_confidence(result),
        "source": "CMake grep",
        "implication": "the tool target is missing the parser library dependency",
        "command": command,
    }


def _negative_fact_e3_missing_typedef(
    worktree_path: Path,
    parsed_failure: ParsedBuildFailure,
) -> dict[str, Any]:
    result, command = _rg_fixed(
        "typedef void *pkgmgrinfo_appinfo_h;",
        [Path("include"), Path("src")],
        cwd=worktree_path,
    )
    type_name = (parsed_failure.primary_candidate or {}).get("type_name") or "pkgmgrinfo_appinfo_h"
    return {
        "check": "grep -R 'typedef void *pkgmgrinfo_appinfo_h;' include/ src/",
        "result": result,
        "scope": "source_code",
        "confidence": _fact_confidence(result),
        "source": "ripgrep",
        "implication": f"the typedef definition is absent from the mutated source tree for {type_name}",
        "command": command,
    }


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


def build_variant_prompt(
    scenario: ErrorScenario,
    parsed_failure: ParsedBuildFailure,
    variant_config: dict[str, Any],
    *,
    evidence: EvidenceCollectionResult | None = None,
    raw_log_path: Path | None = None,
    sample_index: int = 1,
) -> tuple[str, str, dict[str, Any]]:
    """Render a Part 2 A/B prompt variant without mutating source evidence."""

    variant_id = variant_config["variant_id"]
    system = PART2_SHARED_SYSTEM_PROMPT
    metadata = {
        "scenario_id": scenario.scenario_id,
        "variant_id": variant_id,
        "variant_name": variant_config["name"],
        "sample_index": sample_index,
        "input_strategy": variant_config["input_strategy"],
    }

    if variant_config.get("input_strategy") == "raw_log":
        if raw_log_path is None:
            raise ValueError("raw_log_path is required for raw_log variant")
        limit = int(variant_config.get("raw_log_char_limit", PART2_RAW_LOG_CHAR_LIMIT))
        raw_log_excerpt = raw_log_path.read_text(errors="replace")[:limit]
        metadata.update(
            {
                "raw_log_path": str(raw_log_path),
                "raw_log_char_limit": limit,
                "raw_log_excerpt_chars": len(raw_log_excerpt),
                "raw_log_chars": len(raw_log_excerpt),
                "evidence_packet_tokens": 0,
                "spike_budget_overflow_observed": False,
                "raw_log_policy": "LOCAL_ONLY_EXPERIMENTAL_TRACE; do not commit raw log",
            }
        )
        user_payload = {
            "instruction": "Generate a unified diff that fixes the compile failure.",
            "experiment": "S0-A Part 2 raw log baseline",
            "scenario": safe_asdict(scenario),
            "primary_candidate": parsed_failure.primary_candidate,
            "max_patch_lines": MAX_PATCH_LINES,
            "raw_log_excerpt": raw_log_excerpt,
            "raw_log_warning": (
                "This raw-log prompt intentionally violates the normal EvidencePacket boundary "
                "only as a local S0-A Part 2 baseline. Do not persist raw log in repo artifacts."
            ),
        }
        return system, json.dumps(user_payload, ensure_ascii=False, indent=2, sort_keys=True), metadata

    if evidence is None:
        raise ValueError("evidence is required for EvidencePacket variants")
    packet = json.loads(json.dumps(safe_asdict(evidence.packet), ensure_ascii=False))
    if variant_config.get("include_negative_facts"):
        packet["negative_facts"] = list(packet.get("negative_facts") or [])
    else:
        packet.pop("negative_facts", None)

    evidence_packet_tokens = estimate_json_tokens(packet)
    metadata.update(
        {
            "include_negative_facts": bool(variant_config.get("include_negative_facts")),
            "evidence_id": packet.get("evidence_id"),
            "evidence_packet_tokens": evidence_packet_tokens,
            "raw_log_chars": 0,
            "spike_budget_overflow_observed": evidence_packet_tokens > CNEI_EVIDENCE_PACKET_MAX_TOKENS,
        }
    )
    user_payload = {
        "instruction": "Generate a unified diff that fixes the compile failure.",
        "experiment": "S0-A Part 2 EvidencePacket A/B",
        "scenario": safe_asdict(scenario),
        "max_patch_lines": MAX_PATCH_LINES,
        "evidence_packet": packet,
    }
    return system, json.dumps(user_payload, ensure_ascii=False, indent=2, sort_keys=True), metadata


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
    if not any(line.startswith("--- ") for line in lines) or not any(line.startswith("+++ ") for line in lines):
        return PatchValidationResult(False, "not_unified_diff", len(lines), [])

    # +/- change-line count per Compiler Agent v5.2-RC2.4 §5.2.
    # Excludes diff headers (---/+++), hunk headers (@@), and context lines.
    change_line_count = sum(
        1
        for line in lines
        if (line.startswith("+") and not line.startswith("+++"))
        or (line.startswith("-") and not line.startswith("---"))
    )
    if change_line_count > MAX_PATCH_LINES:
        return PatchValidationResult(False, "patch_too_large", change_line_count, [])

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
            return PatchValidationResult(False, "patch_path_escapes_worktree", change_line_count, touched)
        touched.append(path_text)
    return PatchValidationResult(True, None, change_line_count, sorted(set(touched)))


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


def _run_git_apply(
    patch_text: str,
    worktree_path: Path,
    gate: SideEffectGate,
    *,
    mode: str,
    extra_args: list[str],
    patch_file: Path,
) -> CommandResult:
    """Run one git apply command for Part 2 strict/fuzzy comparison."""

    gate.require(f"git apply patch ({mode})")
    patch_file.parent.mkdir(parents=True, exist_ok=True)
    patch_file.write_text(patch_text, encoding="utf-8")
    command = ["git", "apply", *extra_args, str(patch_file)]
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        cwd=worktree_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return CommandResult(
        command=command,
        cwd=worktree_path,
        exit_code=proc.returncode,
        duration_sec=time.perf_counter() - started,
        tail_excerpt="\n".join(proc.stdout.splitlines()[-50:]),
    )


def dual_apply_patch(
    patch_text: str,
    worktree_path: Path,
    gate: SideEffectGate,
    *,
    sample_id: str,
) -> dict[str, Any]:
    """Try strict apply first, then fuzzy three-way apply if strict fails."""

    validation = validate_patch(patch_text, worktree_path)
    if not validation.accepted:
        return {
            "validation": safe_asdict(validation),
            "strict": {"status": "SKIPPED", "reason": validation.reason},
            "fuzzy": {"status": "SKIPPED", "reason": "patch_validation_failed"},
            "final_applied": "none",
        }

    strict_result = _run_git_apply(
        patch_text,
        worktree_path,
        gate,
        mode="strict",
        extra_args=["--index"],
        patch_file=PART2_PATCH_ROOT / f"{sample_id}.strict.patch",
    )
    strict_status = "PASS" if strict_result.exit_code == 0 else "FAIL"
    if strict_result.exit_code == 0:
        return {
            "validation": safe_asdict(validation),
            "strict": {"status": strict_status, "result": safe_asdict(strict_result)},
            "fuzzy": {"status": "SKIPPED", "reason": "strict_apply_passed"},
            "final_applied": "strict",
        }

    fuzzy_result = _run_git_apply(
        patch_text,
        worktree_path,
        gate,
        mode="fuzzy",
        extra_args=["--3way", "--index"],
        patch_file=PART2_PATCH_ROOT / f"{sample_id}.fuzzy.patch",
    )
    fuzzy_status = "PASS" if fuzzy_result.exit_code == 0 else "FAIL"
    return {
        "validation": safe_asdict(validation),
        "strict": {"status": strict_status, "result": safe_asdict(strict_result)},
        "fuzzy": {"status": fuzzy_status, "result": safe_asdict(fuzzy_result)},
        "final_applied": "fuzzy" if fuzzy_result.exit_code == 0 else "none",
    }


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
        "attempts": safe_asdict(result.attempts),
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
            payload=safe_asdict(result.build_failure),
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

        result.parsed_failure = parse_build_log_extended(fail_log, modules)
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
        if result.parsed_failure.parsed_error_count == 0 or not result.parsed_failure.primary_candidate:
            result.final_status = "fail_safe"
            result.failure_envelope = make_failure_envelope(
                scenario,
                "initial_build_unexpected_failure",
                "initial build failed, but parser found no C/C++ primary error",
                stage="parse_errors",
                reason_code="initial_build_unexpected_failure",
                details={
                    "parser": result.parsed_failure.parser_name,
                    "parsed_error_count": result.parsed_failure.parsed_error_count,
                    "primary_candidate": result.parsed_failure.primary_candidate,
                },
                last_attempt_log_excerpt=result.build_failure.tail_excerpt if result.build_failure else None,
            )
            emit_event(
                events_path,
                stage="repair_loop",
                event_type="state_transition",
                name="initial_build_unexpected_failure",
                result_summary="parsed_error_count=0; LLM call skipped",
                payload=result.failure_envelope,
            )
            return result

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

        llm_adapter_error = getattr(modules.get("llm_adapter"), "LLMAdapterError", Exception)
        for attempt_index in range(1, MAX_PATCH_ATTEMPTS + 1):
            attempt = RepairAttemptResult(attempt_index=attempt_index)
            result.attempts.append(attempt)

            try:
                attempt.llm_result = call_llm_for_patch(result.evidence, attempt_index, modules, gate)
            except llm_adapter_error as exc:
                attempt.status = "llm_call_failed"
                attempt.failure_class = "llm_call_failed"
                attempt.llm_error = {"type": type(exc).__name__, "message": str(exc)}
                emit_event(
                    events_path,
                    stage="generate_patch",
                    event_type="llm_call",
                    name="llm_call_failed",
                    result_summary=f"attempt={attempt_index}, error={type(exc).__name__}",
                    payload=attempt.llm_error,
                    attempt_index=attempt_index,
                )
                continue
            except Exception as exc:
                attempt.status = "llm_call_unexpected_error"
                attempt.failure_class = "llm_call_unexpected_error"
                attempt.llm_error = {"type": type(exc).__name__, "message": str(exc)}
                emit_event(
                    events_path,
                    stage="generate_patch",
                    event_type="llm_call",
                    name="llm_call_unexpected_error",
                    result_summary=f"attempt={attempt_index}, error={type(exc).__name__}",
                    payload=attempt.llm_error,
                    attempt_index=attempt_index,
                )
                continue

            try:
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
                    payload=safe_asdict(attempt.patch_validation),
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
                    payload=safe_asdict(attempt.apply_result),
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
            except Exception as exc:
                attempt.status = "attempt_unexpected_error"
                attempt.failure_class = "attempt_unexpected_error"
                attempt.error = {"type": type(exc).__name__, "message": str(exc)}
                emit_event(
                    events_path,
                    stage="repair_attempt",
                    event_type="tool_call",
                    name="attempt_unexpected_error",
                    result_summary=f"attempt={attempt_index}, error={type(exc).__name__}",
                    payload=attempt.error,
                    attempt_index=attempt_index,
                )
                continue

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


def _is_timeout_error(exc: Exception) -> bool:
    """Return true for adapter/network timeout messages."""

    lowered = str(exc).lower()
    return "timeout" in lowered or "timed out" in lowered or "read timed out" in lowered


def call_llm_for_part2_variant(
    scenario: ErrorScenario,
    parsed_failure: ParsedBuildFailure,
    variant_config: dict[str, Any],
    sample_index: int,
    modules: dict[str, ModuleType],
    gate: SideEffectGate,
    *,
    evidence: EvidenceCollectionResult | None,
    raw_log_path: Path,
) -> dict[str, Any]:
    """Call the real LLM once for a Part 2 variant, retrying timeout once."""

    gate.require("Part 2 LLM call")
    adapter = modules["llm_adapter"].get_adapter(str(LLM_CONFIG_PATH))
    system, prompt, prompt_metadata = build_variant_prompt(
        scenario,
        parsed_failure,
        variant_config,
        evidence=evidence,
        raw_log_path=raw_log_path,
        sample_index=sample_index,
    )
    prompt_metadata.update(
        {
            "prompt_chars": len(system) + len(prompt),
            "estimated_prompt_tokens": estimate_text_tokens(system + "\n" + prompt),
        }
    )
    llm_adapter_error = getattr(modules.get("llm_adapter"), "LLMAdapterError", Exception)
    scenario_label = scenario.scenario_id.split("_", 1)[0]
    sample_id = f"part2_{scenario_label}_{variant_config['variant_id']}_sample{sample_index}"
    errors: list[dict[str, str]] = []
    max_calls = 1 + PART2_LLM_TIMEOUT_RETRIES
    for call_index in range(1, max_calls + 1):
        try:
            response = adapter.call(
                prompt,
                system=system,
                scenario_id=f"{sample_id}_call{call_index}",
            )
            return {
                "status": "ok",
                "sample_id": sample_id,
                "call_index": call_index,
                "auto_retry_count": call_index - 1,
                "prompt_metadata": prompt_metadata,
                "llm_result": safe_asdict(
                    LLMCallResult(
                        scenario_id=sample_id,
                        attempt_index=call_index,
                        provider=response.provider,
                        model=response.model,
                        request_id=response.request_id,
                        content=response.content,
                        token_usage=response.token_usage,
                        duration_ms=response.duration_ms,
                        finish_reason=response.finish_reason,
                    )
                ),
            }
        except llm_adapter_error as exc:
            errors.append({"type": type(exc).__name__, "message": str(exc)})
            if call_index < max_calls and _is_timeout_error(exc):
                continue
            break
        except Exception as exc:
            errors.append({"type": type(exc).__name__, "message": str(exc)})
            break
    return {
        "status": "llm_failed",
        "sample_id": sample_id,
        "auto_retry_count": len(errors) - 1 if errors else 0,
        "prompt_metadata": prompt_metadata,
        "errors": errors,
    }


def prepare_part2_scenario_context(
    scenario: ErrorScenario,
    modules: dict[str, ModuleType],
    gate: SideEffectGate,
    *,
    run_id: str,
) -> dict[str, Any]:
    """Create one failing build + EvidencePacket context for all Part 2 samples."""

    worktree_path = create_isolated_worktree(scenario, f"{run_id}_context", gate)
    fail_log = TRACE_ROOT / run_id / scenario.scenario_id / "part2_initial_build_fail.log"
    context: dict[str, Any] = {
        "scenario": safe_asdict(scenario),
        "worktree_path": str(worktree_path),
        "fail_log": str(fail_log),
        "status": "not_started",
    }
    try:
        apply_error_mutation(worktree_path, scenario, gate)
        build_result = run_gbs_build(worktree_path, scenario, fail_log, gate)
        parsed_failure = parse_build_log_extended(fail_log, modules)
        context.update(
            {
                "build_result": safe_asdict(build_result),
                "parsed_failure": safe_asdict(parsed_failure),
            }
        )
        if build_result.exit_code == 0:
            context.update({"status": "scenario_did_not_fail", "error": "mutation unexpectedly built successfully"})
            return context
        if parsed_failure.parsed_error_count == 0 or not parsed_failure.primary_candidate:
            context.update({"status": "parse_failed", "error": "no primary error parsed"})
            return context
        evidence = collect_evidence_packet(scenario, worktree_path, parsed_failure, modules, gate)
        negative_facts = collect_negative_facts(scenario, parsed_failure, worktree_path)
        evidence.packet["negative_facts"] = negative_facts
        refresh_packet_token_metadata(evidence.packet)
        context.update(
            {
                "status": "ok",
                "evidence": evidence,
                "negative_facts": negative_facts,
                "evidence_summary": {
                    "evidence_id": evidence.packet.get("evidence_id"),
                    "raw_data_status": evidence.raw_data_status,
                    "reference_count": evidence.clangd_facts.get("reference_count"),
                    "definition": evidence.clangd_facts.get("definition"),
                    "estimated_tokens": evidence.packet.get("collection_metadata", {}).get("total_tokens_estimate"),
                    "spike_budget_overflow_observed": (
                        int(evidence.packet.get("collection_metadata", {}).get("total_tokens_estimate") or 0)
                        > CNEI_EVIDENCE_PACKET_MAX_TOKENS
                    ),
                    "negative_facts_count": len(negative_facts),
                },
                "_parsed_failure_obj": parsed_failure,
            }
        )
        return context
    finally:
        try:
            cleanup_worktree(worktree_path, gate)
        except Exception:
            pass


def warning_count_from_log(log_path: Path | None) -> int | None:
    """Count warning lines in a build log if it exists."""

    if log_path is None or not log_path.exists():
        return None
    count = 0
    with log_path.open(errors="replace") as stream:
        for line in stream:
            if "warning:" in line.lower():
                count += 1
    return count


def run_part2_sample(
    scenario: ErrorScenario,
    parsed_failure: ParsedBuildFailure,
    evidence: EvidenceCollectionResult,
    variant_config: dict[str, Any],
    sample_index: int,
    modules: dict[str, ModuleType],
    gate: SideEffectGate,
    *,
    run_id: str,
    raw_log_path: Path,
) -> dict[str, Any]:
    """Run one Part 2 sample: LLM call, strict/fuzzy apply, optional rebuild."""

    variant_id = variant_config["variant_id"]
    scenario_label = scenario.scenario_id.split("_", 1)[0]
    sample_id = f"part2_{scenario_label}_{variant_id}_sample{sample_index}"
    sample: dict[str, Any] = {
        "sample_id": sample_id,
        "scenario_id": scenario.scenario_id,
        "variant_id": variant_id,
        "variant_name": variant_config["name"],
        "sample_index": sample_index,
        "status": "not_started",
    }
    llm_call = call_llm_for_part2_variant(
        scenario,
        parsed_failure,
        variant_config,
        sample_index,
        modules,
        gate,
        evidence=evidence,
        raw_log_path=raw_log_path,
    )
    sample["llm_call"] = llm_call
    sample["prompt_metadata"] = llm_call.get("prompt_metadata")
    sample["spike_budget_overflow_observed"] = bool(
        (sample.get("prompt_metadata") or {}).get("spike_budget_overflow_observed")
    )
    if llm_call.get("status") != "ok":
        sample.update(
            {
                "status": "llm_failed",
                "patch_text": "",
                "apply": {
                    "strict": {"status": "SKIPPED", "reason": "llm_failed"},
                    "fuzzy": {"status": "SKIPPED", "reason": "llm_failed"},
                    "final_applied": "none",
                },
                "rebuild": {"status": "N/A", "reason": "llm_failed"},
            }
        )
        return sample

    llm_result = llm_call["llm_result"]
    patch_text = extract_unified_diff(llm_result.get("content", ""))
    sample["patch_text"] = patch_text
    patch_file = PART2_PATCH_ROOT / f"{sample_id}.llm.patch"
    patch_file.parent.mkdir(parents=True, exist_ok=True)
    patch_file.write_text(patch_text, encoding="utf-8")
    sample["patch_file"] = str(patch_file)

    worktree_path = create_isolated_worktree(scenario, f"{run_id}_{variant_id}_sample{sample_index}", gate)
    try:
        apply_error_mutation(worktree_path, scenario, gate)
        apply_result = dual_apply_patch(patch_text, worktree_path, gate, sample_id=sample_id)
        sample["apply"] = apply_result
        final_applied = apply_result.get("final_applied")
        if final_applied in {"strict", "fuzzy"}:
            rebuild_log = TRACE_ROOT / run_id / scenario.scenario_id / f"{sample_id}_rebuild.log"
            rebuild_result = run_gbs_build(worktree_path, scenario, rebuild_log, gate, timeout_sec=VERIFY_TIMEOUT_SEC)
            sample["rebuild"] = {
                "status": "PASS" if rebuild_result.exit_code == 0 else "FAIL",
                "result": safe_asdict(rebuild_result),
                "warning_count": warning_count_from_log(rebuild_log),
            }
            sample["status"] = "repair_succeeded" if rebuild_result.exit_code == 0 else "rebuild_failed"
        else:
            sample["rebuild"] = {"status": "N/A", "reason": "patch_not_applied"}
            sample["status"] = "patch_not_applied"
        return sample
    finally:
        try:
            cleanup_worktree(worktree_path, gate)
        except Exception:
            pass


def part2_sample_failure(
    scenario: ErrorScenario,
    variant_config: dict[str, Any],
    sample_index: int,
    exc: Exception,
    *,
    status: str = "sample_exception",
) -> dict[str, Any]:
    """Create a persisted sample record when one sample fails before normal completion."""

    scenario_label = scenario.scenario_id.split("_", 1)[0]
    sample_id = f"part2_{scenario_label}_{variant_config['variant_id']}_sample{sample_index}"
    return {
        "sample_id": sample_id,
        "scenario_id": scenario.scenario_id,
        "variant_id": variant_config["variant_id"],
        "variant_name": variant_config["name"],
        "sample_index": sample_index,
        "status": status,
        "error": {"type": type(exc).__name__, "message": str(exc)},
        "patch_text": "",
        "apply": {
            "strict": {"status": "SKIPPED", "reason": status},
            "fuzzy": {"status": "SKIPPED", "reason": status},
            "final_applied": "none",
        },
        "rebuild": {"status": "N/A", "reason": status},
    }


def part2_sample_from_context_failure(
    scenario: ErrorScenario,
    variant_config: dict[str, Any],
    sample_index: int,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Create a skipped sample record when scenario context preparation fails."""

    scenario_label = scenario.scenario_id.split("_", 1)[0]
    sample_id = f"part2_{scenario_label}_{variant_config['variant_id']}_sample{sample_index}"
    return {
        "sample_id": sample_id,
        "scenario_id": scenario.scenario_id,
        "variant_id": variant_config["variant_id"],
        "variant_name": variant_config["name"],
        "sample_index": sample_index,
        "status": "scenario_context_failed",
        "context_status": context.get("status"),
        "error": context.get("error"),
        "patch_text": "",
        "apply": {
            "strict": {"status": "SKIPPED", "reason": "scenario_context_failed"},
            "fuzzy": {"status": "SKIPPED", "reason": "scenario_context_failed"},
            "final_applied": "none",
        },
        "rebuild": {"status": "N/A", "reason": "scenario_context_failed"},
    }


def persist_part2_outputs(results: dict[str, Any]) -> None:
    """Persist Part 2 JSON and review form after each sample."""

    PART2_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PART2_RESULTS_PATH.write_text(
        json.dumps(safe_asdict(results), ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    PART2_REVIEW_FORM_PATH.write_text(render_part2_review_form(results), encoding="utf-8")


def part2_progress_line(index: int, total: int, sample: dict[str, Any]) -> str:
    """Return one PM-visible progress line for a completed sample."""

    scenario_label = str(sample.get("scenario_id", "unknown")).split("_", 1)[0]
    variant = sample.get("variant_id", "unknown")
    sample_index = sample.get("sample_index", "?")
    apply_result = sample.get("apply") or {}
    rebuild = sample.get("rebuild") or {}
    strict = (apply_result.get("strict") or {}).get("status", "N/A")
    fuzzy = (apply_result.get("fuzzy") or {}).get("status", "N/A")
    rebuild_status = rebuild.get("status", "N/A")
    return (
        f"[{index}/{total}] {scenario_label} variant-{variant} sample-{sample_index}: "
        f"strict={strict} fuzzy={fuzzy} rebuild={rebuild_status} status={sample.get('status')}"
    )


def _sample_timed_out(sample: dict[str, Any]) -> bool:
    errors = ((sample.get("llm_call") or {}).get("errors")) or []
    return any(_is_timeout_error(Exception(error.get("message", ""))) for error in errors)


def _sample_auth_failed(sample: dict[str, Any]) -> bool:
    errors = ((sample.get("llm_call") or {}).get("errors")) or []
    text = "\n".join(error.get("message", "") for error in errors).lower()
    return any(marker in text for marker in ("401", "403", "unauthorized", "forbidden"))


def _sample_disk_full(sample: dict[str, Any]) -> bool:
    text = json.dumps(sample.get("error") or {}, ensure_ascii=False).lower()
    return "no space left" in text or "disk full" in text


def summarize_part2_results(results: dict[str, Any]) -> dict[str, Any]:
    """Compute automatic apply/rebuild statistics. Semantic accuracy is PM-reviewed later."""

    by_variant: dict[str, dict[str, Any]] = {}
    for variant_id in PART_2_VARIANTS:
        by_variant[variant_id] = {
            "samples": 0,
            "strict_pass": 0,
            "fuzzy_pass": 0,
            "rebuild_pass": 0,
            "timeout": 0,
            "llm_failed": 0,
            "sample_exception": 0,
        }

    for sample in results.get("samples", []):
        variant_id = str(sample.get("variant_id"))
        stats = by_variant.setdefault(
            variant_id,
            {
                "samples": 0,
                "strict_pass": 0,
                "fuzzy_pass": 0,
                "rebuild_pass": 0,
                "timeout": 0,
                "llm_failed": 0,
                "sample_exception": 0,
            },
        )
        stats["samples"] += 1
        apply_result = sample.get("apply") or {}
        if (apply_result.get("strict") or {}).get("status") == "PASS":
            stats["strict_pass"] += 1
        if (apply_result.get("fuzzy") or {}).get("status") == "PASS":
            stats["fuzzy_pass"] += 1
        if (sample.get("rebuild") or {}).get("status") == "PASS":
            stats["rebuild_pass"] += 1
        if sample.get("status") == "llm_failed":
            stats["llm_failed"] += 1
        if sample.get("status") == "sample_exception":
            stats["sample_exception"] += 1
        if _sample_timed_out(sample):
            stats["timeout"] += 1

    for stats in by_variant.values():
        total = max(1, int(stats["samples"]))
        stats["strict_pass_rate"] = round(stats["strict_pass"] / total, 4)
        stats["fuzzy_pass_rate"] = round(stats["fuzzy_pass"] / total, 4)
        stats["rebuild_pass_rate"] = round(stats["rebuild_pass"] / total, 4)

    return {
        "by_variant": by_variant,
        "comparisons": {
            "A_vs_B": {
                "strict_pass": [by_variant.get("A", {}).get("strict_pass"), by_variant.get("B", {}).get("strict_pass")],
                "fuzzy_pass": [by_variant.get("A", {}).get("fuzzy_pass"), by_variant.get("B", {}).get("fuzzy_pass")],
                "rebuild_pass": [by_variant.get("A", {}).get("rebuild_pass"), by_variant.get("B", {}).get("rebuild_pass")],
            },
            "C_vs_D": {
                "strict_pass": [by_variant.get("C", {}).get("strict_pass"), by_variant.get("D", {}).get("strict_pass")],
                "fuzzy_pass": [by_variant.get("C", {}).get("fuzzy_pass"), by_variant.get("D", {}).get("fuzzy_pass")],
                "rebuild_pass": [by_variant.get("C", {}).get("rebuild_pass"), by_variant.get("D", {}).get("rebuild_pass")],
            },
        },
    }


def render_part2_review_form(results: dict[str, Any]) -> str:
    """Render PM-facing review form with fixed per-sample fields."""

    lines = [
        "# S0-A Part 2 Review Form",
        "",
        "PM semantic eval options: correct / acceptable / wrong",
        "",
    ]
    for sample in results.get("samples", []):
        scenario_label = sample["scenario_id"].split("_", 1)[0]
        variant_id = sample["variant_id"]
        sample_index = sample["sample_index"]
        request_id = ((sample.get("llm_call") or {}).get("llm_result") or {}).get("request_id", "N/A")
        variant_name = sample.get("variant_name", "")
        patch_text = sample.get("patch_text") or ""
        apply_result = sample.get("apply") or {}
        strict = apply_result.get("strict") or {}
        fuzzy = apply_result.get("fuzzy") or {}
        rebuild = sample.get("rebuild") or {}
        llm_result = ((sample.get("llm_call") or {}).get("llm_result") or {})
        token_usage = llm_result.get("token_usage") or {}
        prompt_metadata = sample.get("prompt_metadata") or {}
        strict_msg = ((strict.get("result") or {}).get("tail_excerpt")) or strict.get("reason") or ""
        fuzzy_msg = ((fuzzy.get("result") or {}).get("tail_excerpt")) or fuzzy.get("reason") or ""
        lines.extend(
            [
                f"## {scenario_label}, variant {variant_id} ({variant_name}), sample {sample_index}",
                f"(scenario_id: {sample['sample_id']}, request_id: {request_id})",
                "",
                "**Patch text**:",
                "```diff",
                patch_text.rstrip() if patch_text else "[no unified diff returned]",
                "```",
                "",
                "**Build pipeline**:",
                f"- strict apply (`git apply --index`): {strict.get('status', 'N/A')} ({strict_msg})",
                f"- fuzzy apply (`git apply --3way --index`): {fuzzy.get('status', 'N/A')} ({fuzzy_msg})",
                f"- final_applied: {apply_result.get('final_applied', 'none')}",
                f"- rebuild: {rebuild.get('status', 'N/A')}",
                "",
                "**LLM metadata**:",
                f"- duration_ms: {llm_result.get('duration_ms', 'N/A')}",
                f"- tokens (in/out/total): {token_usage.get('in', 'N/A')}/{token_usage.get('out', 'N/A')}/{token_usage.get('total', 'N/A')}",
                f"- finish_reason: {llm_result.get('finish_reason', 'N/A')}",
                "",
                "**Prompt metadata**:",
                f"- prompt_chars: {prompt_metadata.get('prompt_chars', 'N/A')}",
                f"- estimated_prompt_tokens: {prompt_metadata.get('estimated_prompt_tokens', 'N/A')}",
                f"- evidence_packet_tokens: {prompt_metadata.get('evidence_packet_tokens', 'N/A')}",
                f"- raw_log_chars: {prompt_metadata.get('raw_log_chars', 'N/A')}",
                f"- spike_budget_overflow_observed: {prompt_metadata.get('spike_budget_overflow_observed', 'N/A')}",
                "",
                "**PM semantic eval**: ___ (correct / acceptable / wrong)",
                "**PM 备注**: ___",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def run_part2_ab_test(
    modules: dict[str, ModuleType],
    gate: SideEffectGate,
    *,
    scenarios: dict[str, ErrorScenario] | None = None,
) -> dict[str, Any]:
    """Run S0-A Part 2 A/B experiment. This is side-effect gated."""

    gate.require("S0-A Part 2 A/B test")
    started_at = time.perf_counter()
    run_id = datetime.now().strftime("part2_%Y%m%d_%H%M%S_%f")
    selected = scenarios or ERROR_SCENARIOS
    total_samples = len(selected) * len(PART_2_VARIANTS) * PART2_SAMPLE_COUNT
    completed_samples = 0
    consecutive_system_failures = 0
    results: dict[str, Any] = {
        "schema": "s0_a_part2_results.v1",
        "run_id": run_id,
        "created_at": utc_now(),
        "sample_count_per_variant": PART2_SAMPLE_COUNT,
        "variants": PART_2_VARIANTS,
        "comparison_note": (
            "A and C intentionally share EvidencePacket construction but serve different "
            "comparison axes: A/B isolates negative_facts; C/D compares EvidencePacket vs raw-log baseline."
        ),
        "real_llm_calls_expected": len(selected) * len(PART_2_VARIANTS) * PART2_SAMPLE_COUNT,
        "samples": [],
        "scenario_contexts": {},
        "output_paths": {
            "results_json": str(PART2_RESULTS_PATH),
            "review_form_md": str(PART2_REVIEW_FORM_PATH),
        },
    }

    try:
        for scenario in selected.values():
            try:
                context = prepare_part2_scenario_context(scenario, modules, gate, run_id=run_id)
            except Exception as exc:
                context = {
                    "scenario": safe_asdict(scenario),
                    "status": "context_exception",
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            results["scenario_contexts"][scenario.scenario_id] = {
                key: value for key, value in context.items()
                if key not in {"evidence", "_parsed_failure_obj"}
            }
            if context.get("status") != "ok":
                for variant_config in PART_2_VARIANTS.values():
                    for sample_index in range(1, PART2_SAMPLE_COUNT + 1):
                        sample = part2_sample_from_context_failure(
                            scenario,
                            variant_config,
                            sample_index,
                            context,
                        )
                        results["samples"].append(sample)
                        completed_samples += 1
                        results["summary"] = summarize_part2_results(results)
                        persist_part2_outputs(results)
                        print(part2_progress_line(completed_samples, total_samples, sample), flush=True)
                continue
            evidence = context["evidence"]
            parsed_failure = context["_parsed_failure_obj"]
            raw_log_path = Path(context["fail_log"])
            for variant_config in PART_2_VARIANTS.values():
                for sample_index in range(1, PART2_SAMPLE_COUNT + 1):
                    try:
                        sample = run_part2_sample(
                            scenario,
                            parsed_failure,
                            evidence,
                            variant_config,
                            sample_index,
                            modules,
                            gate,
                            run_id=run_id,
                            raw_log_path=raw_log_path,
                        )
                    except Exception as exc:
                        sample = part2_sample_failure(scenario, variant_config, sample_index, exc)
                    results["samples"].append(sample)
                    completed_samples += 1
                    results["summary"] = summarize_part2_results(results)
                    persist_part2_outputs(results)
                    print(part2_progress_line(completed_samples, total_samples, sample), flush=True)

                    if _sample_disk_full(sample):
                        raise RuntimeError("systemic_failure: disk full observed in sample")
                    if _sample_auth_failed(sample) or sample.get("status") == "sample_exception":
                        consecutive_system_failures += 1
                    else:
                        consecutive_system_failures = 0
                    if consecutive_system_failures >= 5:
                        raise RuntimeError("systemic_failure: 5 consecutive auth/sample exceptions")
    finally:
        cleanup_clangd_client()

    results["status"] = "complete"
    results["elapsed_sec"] = round(time.perf_counter() - started_at, 3)
    results["real_llm_calls_observed"] = sum(
        1 for sample in results["samples"]
        if (sample.get("llm_call") or {}).get("status") == "ok"
    )
    results["summary"] = summarize_part2_results(results)
    persist_part2_outputs(results)
    return results


def _init_tmp_git_repo(repo_path: Path, files: dict[str, str]) -> None:
    """Create a tiny committed git repo for pure-local failure tests."""

    subprocess.run(["git", "init", "--quiet"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo_path, check=True)
    for relative_path, content in files.items():
        path = repo_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "init"], cwd=repo_path, check=True)


def _local_failure_scenario(scenario_id: str) -> ErrorScenario:
    """Return a package-agnostic scenario for local failure tests."""

    return ErrorScenario(
        scenario_id=scenario_id,
        package="pkgmgr-info",
        error_type="mock_error",
        source_file=Path("CMakeLists.txt"),
        mutation_kind="mock",
        mutation_target="mock",
        expected_primary_hint="mock",
        notes=f"{scenario_id} pure-local failure-path test",
    )


def _mock_parsed_failure(log_path: Path) -> ParsedBuildFailure:
    """Return a minimal parsed failure used by mocked repair-loop tests."""

    return ParsedBuildFailure(
        parser_name="mock",
        log_path=log_path,
        parsed_error_count=1,
        primary_candidate={
            "message": "mock compile error",
            "line_no": 1,
            "source_location": {"file": str(log_path), "line": 1, "column": 1},
            "symbol": "mock_symbol",
        },
        raw_result={"parser": "mock"},
    )


def _mock_evidence_packet() -> EvidenceCollectionResult:
    """Return a minimal RawDataDetector-allowed EvidencePacket."""

    return EvidenceCollectionResult(
        packet={"evidence_id": "EP-test", "schema": "evidence_packet.v1.spike_A"},
        raw_data_status={"status": "allowed"},
        clangd_facts={},
        degraded_reasons=[],
    )


def test_patch_format_invalid() -> dict[str, Any]:
    """Pure-local failure test: invalid non-unified patch is rejected."""

    import tempfile

    with tempfile.TemporaryDirectory(prefix="s0a_test_patch_format_") as tmp:
        tmp_path = Path(tmp)
        _init_tmp_git_repo(tmp_path, {"file.txt": "original\n"})
        mock_llm = LLMCallResult(
            scenario_id="TEST_PATCH_FORMAT_INVALID",
            attempt_index=1,
            provider="mock",
            model="mock",
            request_id="mock-invalid-format",
            content="I would fix this by editing file.txt, but this is not a diff.",
            token_usage={"in": 1, "out": 1, "total": 2},
            duration_ms=1,
            finish_reason="stop",
        )
        patch_text = extract_unified_diff(mock_llm.content)
        validation = validate_patch(patch_text, tmp_path)

    assert validation.accepted is False
    assert validation.reason == "not_unified_diff"
    return {
        "test": "test_patch_format_invalid",
        "status": "PASS",
        "setup": "tmp git repo + mock LLM content with no unified diff markers",
        "real_llm_calls": 0,
        "mock_llm_calls": 1,
        "assertions": {
            "validation.accepted": validation.accepted,
            "validation.reason": validation.reason,
        },
    }


def test_apply_conflict() -> dict[str, Any]:
    """Pure-local failure test: git apply conflict returns non-zero."""

    import tempfile

    patch_text = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-original\n"
        "+patched\n"
    )
    with tempfile.TemporaryDirectory(prefix="s0a_test_apply_conflict_") as tmp:
        tmp_path = Path(tmp)
        _init_tmp_git_repo(tmp_path, {"file.txt": "original\n"})
        (tmp_path / "file.txt").write_text("local uncommitted edit\n", encoding="utf-8")
        validation = validate_patch(patch_text, tmp_path)
        assert validation.accepted is True
        apply_result = apply_patch_to_worktree(
            patch_text,
            tmp_path,
            SideEffectGate(enabled=True, reason="test_apply_conflict"),
        )

    assert apply_result.exit_code != 0
    return {
        "test": "test_apply_conflict",
        "status": "PASS",
        "setup": "tmp git repo with uncommitted file change; real validate_patch + real git apply --index",
        "real_llm_calls": 0,
        "assertions": {
            "validation.accepted": validation.accepted,
            "apply_result.exit_code": apply_result.exit_code,
            "apply_result.tail_excerpt": apply_result.tail_excerpt,
        },
    }


def test_rebuild_fails() -> dict[str, Any]:
    """Pure-local failure test: applicable patches cannot loop forever."""

    import tempfile
    from unittest.mock import patch as mock_patch

    with tempfile.TemporaryDirectory(prefix="s0a_test_rebuild_fails_") as tmp:
        tmp_path = Path(tmp)
        _init_tmp_git_repo(tmp_path, {"CMakeLists.txt": "PROJECT(test)\n"})
        llm_call_count = 0
        build_call_count = 0

        def mock_llm(*_args: Any, **_kwargs: Any) -> LLMCallResult:
            nonlocal llm_call_count
            llm_call_count += 1
            old_project = "test" if llm_call_count == 1 else f"test_rebuild_{llm_call_count - 1}"
            new_project = f"test_rebuild_{llm_call_count}"
            return LLMCallResult(
                scenario_id="TEST_REBUILD_FAILS",
                attempt_index=llm_call_count,
                provider="mock",
                model="mock",
                request_id=f"mock-rebuild-{llm_call_count}",
                content=(
                    "--- a/CMakeLists.txt\n"
                    "+++ b/CMakeLists.txt\n"
                    "@@ -1 +1 @@\n"
                    f"-PROJECT({old_project})\n"
                    f"+PROJECT({new_project})\n"
                ),
                token_usage={"in": 2, "out": 2, "total": 4},
                duration_ms=1,
                finish_reason="stop",
            )

        def mock_build_fail(
            worktree_path: Path,
            _scenario: ErrorScenario,
            log_path: Path,
            _gate: SideEffectGate,
            **_kwargs: Any,
        ) -> CommandResult:
            nonlocal build_call_count
            build_call_count += 1
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(f"mock build failed call={build_call_count}\n", encoding="utf-8")
            return CommandResult(
                command=["gbs", "build"],
                cwd=worktree_path,
                exit_code=1,
                duration_sec=0.01,
                combined_log_path=log_path,
                tail_excerpt=f"mock build failed call={build_call_count}",
            )

        scenario = _local_failure_scenario("TEST_REBUILD_FAILS")
        gate = SideEffectGate(enabled=True, reason="test_rebuild_fails")
        with mock_patch(f"{__name__}.create_isolated_worktree", return_value=tmp_path), \
             mock_patch(f"{__name__}.apply_error_mutation", return_value=None), \
             mock_patch(f"{__name__}.run_gbs_build", side_effect=mock_build_fail), \
             mock_patch(f"{__name__}.parse_build_log", side_effect=lambda log_path, _modules: _mock_parsed_failure(log_path)), \
             mock_patch(f"{__name__}.collect_evidence_packet", return_value=_mock_evidence_packet()), \
             mock_patch(f"{__name__}.call_llm_for_patch", side_effect=mock_llm), \
             mock_patch(f"{__name__}.write_trace", return_value=None), \
             mock_patch(f"{__name__}.emit_event", return_value=None):
            result = run_repair_loop_for_scenario(scenario, {}, gate)

    assert llm_call_count <= MAX_PATCH_ATTEMPTS
    assert llm_call_count == MAX_PATCH_ATTEMPTS
    assert build_call_count == 1 + MAX_PATCH_ATTEMPTS
    assert result.final_status == "fail_safe"
    assert result.failure_envelope is not None
    assert result.failure_envelope.get("reason_code") == "max_patch_attempts_exhausted"
    assert all(attempt.status == "rebuild_failed" for attempt in result.attempts)
    return {
        "test": "test_rebuild_fails",
        "status": "PASS",
        "setup": "tmp git repo; mock LLM returns valid/applicable patches; mock initial build and rebuilds fail",
        "real_llm_calls": 0,
        "mock_llm_calls": llm_call_count,
        "build_calls": build_call_count,
        "assertions": {
            "llm_call_count <= MAX_PATCH_ATTEMPTS": llm_call_count <= MAX_PATCH_ATTEMPTS,
            "attempt_statuses": [attempt.status for attempt in result.attempts],
            "final_status": result.final_status,
            "failure_envelope.reason_code": result.failure_envelope.get("reason_code"),
        },
    }


def test_bounded_repair_limit() -> dict[str, Any]:
    """Half-real test: real tmp git worktree + validate/apply, mock LLM/build.

    Assertions:
      - llm_call_count == MAX_PATCH_ATTEMPTS (exactly 2)
      - llm_call_count != 3
      - final_status == fail_safe
      - failure_envelope.reason_code == max_patch_attempts_exhausted
      - failure_envelope.attempt_index == 2
    """

    import tempfile
    from unittest.mock import patch as mock_patch

    with tempfile.TemporaryDirectory(prefix="s0a_test_bounded_") as tmp:
        tmp_path = Path(tmp)
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
        (tmp_path / "CMakeLists.txt").write_text("PROJECT(test)\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)

        llm_call_count = 0

        def mock_llm(*_args: Any, **_kwargs: Any) -> LLMCallResult:
            nonlocal llm_call_count
            llm_call_count += 1
            old_project = "test" if llm_call_count == 1 else f"test_mock_{llm_call_count - 1}"
            new_project = f"test_mock_{llm_call_count}"
            return LLMCallResult(
                scenario_id="TEST_BOUNDED",
                attempt_index=llm_call_count,
                provider="mock",
                model="mock",
                request_id=f"mock-{llm_call_count}",
                content=(
                    "--- a/CMakeLists.txt\n"
                    "+++ b/CMakeLists.txt\n"
                    "@@ -1 +1 @@\n"
                    f"-PROJECT({old_project})\n"
                    f"+PROJECT({new_project})\n"
                ),
                token_usage={"in": 10, "out": 5, "total": 15},
                duration_ms=1,
                finish_reason="stop",
            )

        def mock_build_fail(*_args: Any, **_kwargs: Any) -> CommandResult:
            return CommandResult(
                command=["gbs", "build"],
                cwd=tmp_path,
                exit_code=1,
                duration_sec=0.1,
                tail_excerpt="build failed (mock)",
            )

        mock_evidence = EvidenceCollectionResult(
            packet={"evidence_id": "EP-test", "schema": "evidence_packet.v1.spike_A"},
            raw_data_status={"status": "allowed"},
            clangd_facts={},
            degraded_reasons=[],
        )
        mock_parsed = ParsedBuildFailure(
            parser_name="mock",
            log_path=Path("/tmp/mock.log"),
            parsed_error_count=1,
            primary_candidate={
                "message": "mock error",
                "line_no": 1,
                "source_location": {"file": str(tmp_path / "CMakeLists.txt"), "line": 1, "column": 1},
            },
            raw_result={"parser": "mock"},
        )
        fake_scenario = ErrorScenario(
            scenario_id="TEST_BOUNDED",
            package="pkgmgr-info",
            error_type="mock_error",
            source_file=Path("CMakeLists.txt"),
            mutation_kind="mock",
            mutation_target="mock",
            expected_primary_hint="mock",
            notes="test_bounded_repair_limit half-real test",
        )
        gate = SideEffectGate(enabled=True, reason="test_bounded_repair_limit half-real")

        with mock_patch(f"{__name__}.create_isolated_worktree", return_value=tmp_path), \
             mock_patch(f"{__name__}.apply_error_mutation", return_value=None), \
             mock_patch(f"{__name__}.run_gbs_build", side_effect=mock_build_fail), \
             mock_patch(f"{__name__}.parse_build_log", return_value=mock_parsed), \
             mock_patch(f"{__name__}.collect_evidence_packet", return_value=mock_evidence), \
             mock_patch(f"{__name__}.call_llm_for_patch", side_effect=mock_llm), \
             mock_patch(f"{__name__}.write_trace", return_value=None), \
             mock_patch(f"{__name__}.emit_event", return_value=None):
            result = run_repair_loop_for_scenario(fake_scenario, {}, gate)

        assert llm_call_count == MAX_PATCH_ATTEMPTS, (
            f"LLM must be called exactly 2 times, got {llm_call_count}"
        )
        assert llm_call_count != 3, "LLM must never be called 3rd time"
        assert result.final_status == "fail_safe", f"expected fail_safe, got {result.final_status}"
        assert result.failure_envelope is not None
        assert result.failure_envelope.get("reason_code") == "max_patch_attempts_exhausted"
        assert result.failure_envelope.get("attempt_index") == MAX_PATCH_ATTEMPTS

        return {
            "test": "test_bounded_repair_limit",
            "status": "PASS",
            "mode": "half-real (mock LLM/build, real git worktree + validate_patch + git apply)",
            "llm_calls": llm_call_count,
            "final_status": result.final_status,
            "failure_envelope": result.failure_envelope,
        }


def test_uncommitted_changes() -> dict[str, Any]:
    """Pure-local failure test: dirty source repo is rejected before clone."""

    import tempfile
    from unittest.mock import patch as mock_patch

    with tempfile.TemporaryDirectory(prefix="s0a_test_uncommitted_") as tmp:
        tmp_path = Path(tmp)
        _init_tmp_git_repo(tmp_path, {"CMakeLists.txt": "PROJECT(test)\n"})
        (tmp_path / "CMakeLists.txt").write_text("PROJECT(dirty)\n", encoding="utf-8")
        scenario = _local_failure_scenario("TEST_UNCOMMITTED_CHANGES")
        gate = SideEffectGate(enabled=True, reason="test_uncommitted_changes")
        try:
            with mock_patch(f"{__name__}.package_repo_path", return_value=tmp_path):
                create_isolated_worktree(scenario, "test_uncommitted", gate)
        except RuntimeError as exc:
            message = str(exc)
        else:
            raise AssertionError("create_isolated_worktree must reject dirty source repos")

    assert "uncommitted changes" in message
    return {
        "test": "test_uncommitted_changes",
        "status": "PASS",
        "setup": "tmp git repo with uncommitted source change; real create_isolated_worktree preflight",
        "real_llm_calls": 0,
        "assertions": {
            "raised": "RuntimeError",
            "message": message,
            "contains_uncommitted_changes": "uncommitted changes" in message,
        },
    }


def test_non_git_repo() -> dict[str, Any]:
    """Pure-local failure test: non-git source path emits contract violation."""

    import tempfile
    from unittest.mock import patch as mock_patch

    with tempfile.TemporaryDirectory(prefix="s0a_test_non_git_") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "CMakeLists.txt").write_text("PROJECT(test)\n", encoding="utf-8")
        scenario = _local_failure_scenario("TEST_NON_GIT_REPO")
        gate = SideEffectGate(enabled=True, reason="test_non_git_repo")
        try:
            with mock_patch(f"{__name__}.package_repo_path", return_value=tmp_path):
                create_isolated_worktree(scenario, "test_non_git", gate)
        except RuntimeError as exc:
            message = str(exc)
        else:
            raise AssertionError("create_isolated_worktree must reject non-git source paths")

    assert "contract_violation" in message
    assert "not a git repo" in message
    return {
        "test": "test_non_git_repo",
        "status": "PASS",
        "setup": "tmp directory without git init; real create_isolated_worktree preflight",
        "real_llm_calls": 0,
        "assertions": {
            "raised": "RuntimeError",
            "message": message,
            "contains_contract_violation": "contract_violation" in message,
            "contains_not_a_git_repo": "not a git repo" in message,
        },
    }


def run_failure_path_tests() -> dict[str, Any]:
    """Run all pure-local S0-A Step 2 failure-path tests."""

    tests = [
        test_patch_format_invalid,
        test_apply_conflict,
        test_rebuild_fails,
        test_bounded_repair_limit,
        test_uncommitted_changes,
        test_non_git_repo,
    ]
    results: list[dict[str, Any]] = []
    for test in tests:
        try:
            results.append(test())
        except Exception as exc:
            results.append(
                {
                    "test": test.__name__,
                    "status": "FAIL",
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            )
    return {
        "suite": "S0-A Step 2 failure-path tests",
        "status": "PASS" if all(result.get("status") == "PASS" for result in results) else "FAIL",
        "real_llm_calls": 0,
        "gbs_builds": 0,
        "results": results,
    }


def _write_negative_fact_fixture(worktree_path: Path, scenario: ErrorScenario) -> None:
    """Create a tiny source tree that contains the scenario mutation target."""

    if scenario.error_type == "cannot_find_header":
        (worktree_path / "CMakeLists.txt").write_text(
            "INCLUDE_DIRECTORIES(\n"
            "  ${CMAKE_SOURCE_DIR}/include\n"
            "  ${CMAKE_SOURCE_DIR}/src/parser/include\n"
            ")\n",
            encoding="utf-8",
        )
        return
    if scenario.error_type == "undefined_reference":
        tool_dir = worktree_path / "tool"
        tool_dir.mkdir(parents=True, exist_ok=True)
        (tool_dir / "CMakeLists.txt").write_text(
            "target_link_libraries(${PKG_DB_CREATOR}\n"
            "  ${TARGET_LIB_PKGMGR_PARSER}\n"
            ")\n",
            encoding="utf-8",
        )
        return
    if scenario.error_type == "unknown_type_name":
        include_dir = worktree_path / "include"
        src_dir = worktree_path / "src"
        include_dir.mkdir(parents=True, exist_ok=True)
        src_dir.mkdir(parents=True, exist_ok=True)
        (include_dir / "pkgmgrinfo_type.h").write_text(
            "typedef void *pkgmgrinfo_appinfo_h;\n",
            encoding="utf-8",
        )
        return
    raise ValueError(f"unsupported negative-fact fixture scenario: {scenario.scenario_id}")


def _parsed_failure_for_negative_fact_test(scenario: ErrorScenario, log_path: Path) -> ParsedBuildFailure:
    """Return a parsed failure carrying the scenario symbol for local purity tests."""

    primary = {
        "message": scenario.expected_primary_hint,
        "line_no": 1,
        "source_location": {"file": str(log_path), "line": 1, "column": 1},
        "symbol": scenario.mutation_target,
    }
    if scenario.error_type == "unknown_type_name":
        primary["type_name"] = "pkgmgrinfo_appinfo_h"
    if scenario.error_type == "undefined_reference":
        primary["undefined_symbol"] = "pkgmgr_parser_create_and_initialize_db"
    if scenario.error_type == "cannot_find_header":
        primary["missing_header"] = "pkgmgr_parser_db.h"
    return ParsedBuildFailure(
        parser_name="negative_fact_purity_mock",
        log_path=log_path,
        parsed_error_count=1,
        primary_candidate=primary,
        raw_result={"parser": "negative_fact_purity_mock"},
    )


def _all_string_values(value: Any) -> list[str]:
    """Collect nested string values for negative_facts purity scanning."""

    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for nested in value.values():
            strings.extend(_all_string_values(nested))
        return strings
    if isinstance(value, list):
        strings = []
        for nested in value:
            strings.extend(_all_string_values(nested))
        return strings
    return []


def validate_negative_facts_purity(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return purity violations for negative_facts."""

    violations: list[dict[str, Any]] = []
    for index, fact in enumerate(facts):
        missing = sorted(NEGATIVE_FACT_REQUIRED_FIELDS - set(fact))
        if missing:
            violations.append({"index": index, "type": "missing_required_fields", "fields": missing})
        result = fact.get("result")
        if result not in NEGATIVE_FACT_ALLOWED_RESULTS:
            violations.append({"index": index, "type": "invalid_result", "result": result})
        joined = "\n".join(_all_string_values(fact)).lower()
        for phrase in NEGATIVE_FACT_FORBIDDEN_PHRASES:
            if phrase in joined:
                violations.append({"index": index, "type": "forbidden_phrase", "phrase": phrase})
    return violations


def _test_evidence_with_negative_facts(facts: list[dict[str, Any]]) -> EvidenceCollectionResult:
    """Create a small EvidencePacket object for prompt-purity checks."""

    packet = {
        "schema": "evidence_packet.v1.spike_A",
        "evidence_id": "EP-S0-A-negative-facts-purity",
        "task_id": "S0-A-Part2-purity",
        "trigger": {"type": "compile_error"},
        "facts": {"mock": True},
        "negative_facts": facts,
        "log_excerpt": [],
        "collection_metadata": {},
    }
    refresh_packet_token_metadata(packet)
    return EvidenceCollectionResult(
        packet=packet,
        raw_data_status={"status": "allowed"},
        clangd_facts={},
        degraded_reasons=[],
    )


def _prompt_payload_without_negative_facts(prompt: str) -> dict[str, Any]:
    """Decode a Part 2 JSON prompt and remove only evidence_packet.negative_facts."""

    payload = json.loads(prompt)
    packet = payload.get("evidence_packet")
    if isinstance(packet, dict):
        packet.pop("negative_facts", None)
    return payload


def test_negative_facts_purity() -> dict[str, Any]:
    """Validate negative_facts semantics and Part 2 prompt purity."""

    import tempfile

    gate = SideEffectGate(enabled=True, reason="test_negative_facts_purity local fixtures")
    scenario_facts: dict[str, list[dict[str, Any]]] = {}
    violations: list[dict[str, Any]] = []
    parsed_by_scenario: dict[str, ParsedBuildFailure] = {}

    for scenario in ERROR_SCENARIOS.values():
        with tempfile.TemporaryDirectory(prefix=f"s0a_negative_facts_{scenario.scenario_id}_") as tmp:
            worktree_path = Path(tmp)
            _write_negative_fact_fixture(worktree_path, scenario)
            apply_error_mutation(worktree_path, scenario, gate)
            parsed_failure = _parsed_failure_for_negative_fact_test(
                scenario,
                worktree_path / "negative_fact_purity.log",
            )
            parsed_by_scenario[scenario.scenario_id] = parsed_failure
            facts = collect_negative_facts(scenario, parsed_failure, worktree_path)
            scenario_facts[scenario.scenario_id] = facts
            for violation in validate_negative_facts_purity(facts):
                violations.append({"scenario_id": scenario.scenario_id, **violation})

    first_scenario = next(iter(ERROR_SCENARIOS.values()))
    first_parsed = parsed_by_scenario[first_scenario.scenario_id]
    evidence = _test_evidence_with_negative_facts(scenario_facts[first_scenario.scenario_id])
    raw_log = TMP_ROOT / "negative_facts_purity_raw.log"
    raw_log.parent.mkdir(parents=True, exist_ok=True)
    raw_log.write_text("mock raw build log for prompt purity test\n", encoding="utf-8")

    prompts: dict[str, str] = {}
    system_prompts: dict[str, str] = {}
    prompt_metadata: dict[str, dict[str, Any]] = {}
    for variant_id, config in PART_2_VARIANTS.items():
        system, prompt, metadata = build_variant_prompt(
            first_scenario,
            first_parsed,
            config,
            evidence=evidence,
            raw_log_path=raw_log,
            sample_index=1,
        )
        system_prompts[variant_id] = system
        prompts[variant_id] = prompt
        prompt_metadata[variant_id] = metadata

    system_prompt_byte_identical = len(set(system_prompts.values())) == 1
    if not system_prompt_byte_identical:
        violations.append({"type": "system_prompt_not_byte_identical"})

    a_without_negative = _prompt_payload_without_negative_facts(prompts["A"])
    b_without_negative = _prompt_payload_without_negative_facts(prompts["B"])
    ab_diff_only_negative_facts = a_without_negative == b_without_negative
    if not ab_diff_only_negative_facts:
        violations.append({"type": "ab_prompt_diff_not_limited_to_negative_facts"})

    return {
        "test": "test_negative_facts_purity",
        "status": "PASS" if not violations else "FAIL",
        "scenario_facts": scenario_facts,
        "system_prompt_byte_identical": system_prompt_byte_identical,
        "ab_prompt_diff_only_negative_facts": ab_diff_only_negative_facts,
        "system_prompts": system_prompts,
        "prompt_metadata": prompt_metadata,
        "violations": violations,
    }


def describe_framework() -> dict[str, Any]:
    """Return a side-effect-free framework summary for PM review."""

    return {
        "phase": "S0-A Part 1 complete + Step 2 tests + Part 2 framework",
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
            "compile_commands_rewrite": str(REWRITE_COMPILE_COMMANDS_PATH),
            "RawDataDetector": str(SPIKE_06_PATH),
            "LLMAdapter": str(LLM_ADAPTER_PATH),
        },
        "scenarios": {key: safe_asdict(value) for key, value in ERROR_SCENARIOS.items()},
        "bounded_repair": {
            "max_patch_attempts": MAX_PATCH_ATTEMPTS,
            "verify_timeout_sec": VERIFY_TIMEOUT_SEC,
            "max_patch_lines": MAX_PATCH_LINES,
            "third_attempt_allowed": False,
        },
        "part2_ab_test": {
            "variants": PART_2_VARIANTS,
            "sample_count_per_variant": PART2_SAMPLE_COUNT,
            "expected_llm_calls": len(ERROR_SCENARIOS) * len(PART_2_VARIANTS) * PART2_SAMPLE_COUNT,
            "outputs": {
                "results_json": str(PART2_RESULTS_PATH),
                "review_form_md": str(PART2_REVIEW_FORM_PATH),
            },
            "mode": "run-part2-ab-test",
            "side_effect_gate_required": True,
        },
        "failure_path_tests": [
            {
                "test": "test_patch_format_invalid",
                "status": "implemented_run_with_--mode run-failure-path-tests",
                "expected": "validate_patch rejects non-unified diff before apply",
            },
            {
                "test": "test_apply_conflict",
                "status": "implemented_run_with_--mode run-failure-path-tests",
                "expected": "real git apply --index conflict returns non-zero",
            },
            {
                "test": "test_rebuild_fails",
                "status": "implemented_run_with_--mode run-failure-path-tests",
                "expected": "valid/applicable patches still stop at bounded repair limit when rebuild fails",
            },
            {
                "test": "test_bounded_repair_limit",
                "status": "implemented_half_real_run_with_--mode test-bounded",
                "llm_calls": "asserted at runtime",
                "expected": "real tmp git repo + real validate/apply; mock LLM/build; exactly 2 LLM calls",
            },
            {
                "test": "test_uncommitted_changes",
                "status": "implemented_run_with_--mode run-failure-path-tests",
                "expected": "dirty source repo is rejected before clone/mutation",
            },
            {
                "test": "test_non_git_repo",
                "status": "implemented_run_with_--mode run-failure-path-tests",
                "expected": "non-git source path raises contract_violation",
            },
            {
                "test": "test_negative_facts_purity",
                "status": "implemented_run_with_--mode test-negative-facts-purity",
                "expected": "negative_facts contain tool-derived facts only; A/B differ only by negative_facts; system prompt is byte-identical",
            },
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Defaults to side-effect-free framework description."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=[
            "describe",
            "check-imports",
            "test-patch-format-invalid",
            "test-apply-conflict",
            "test-rebuild-fails",
            "test-bounded",
            "test-uncommitted-changes",
            "test-non-git-repo",
            "test-negative-facts-purity",
            "run-failure-path-tests",
            "run-part2-ab-test",
            "self-test-clangd",
            "self-test-clangd-integration",
            "run-part1",
        ],
        default="describe",
        help="run-part1/run-part2-ab-test are blocked unless --enable-side-effects is set by PM instruction",
    )
    parser.add_argument("--scenario", choices=sorted(ERROR_SCENARIOS), help="scenario for run-part1")
    parser.add_argument("--enable-side-effects", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "describe":
        print(json.dumps(describe_framework(), indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0

    if args.mode == "test-bounded":
        result = test_bounded_repair_limit()
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "test-patch-format-invalid":
        result = test_patch_format_invalid()
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "test-apply-conflict":
        result = test_apply_conflict()
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "test-rebuild-fails":
        result = test_rebuild_fails()
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "test-uncommitted-changes":
        result = test_uncommitted_changes()
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "test-non-git-repo":
        result = test_non_git_repo()
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "test-negative-facts-purity":
        result = test_negative_facts_purity()
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "run-failure-path-tests":
        result = run_failure_path_tests()
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    modules = load_reused_spikes()
    if args.mode == "check-imports":
        print(json.dumps({"status": "ok", "modules": sorted(modules)}, indent=2, sort_keys=True))
        return 0

    if args.mode == "self-test-clangd":
        result = collect_clangd_facts_self_test(modules)
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "self-test-clangd-integration":
        result = collect_clangd_facts_integration_self_test(modules)
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0 if result.get("status") == "PASS" else 1

    if args.mode == "run-part1":
        if not args.scenario:
            parser.error("--scenario is required for run-part1")
        gate = SideEffectGate(
            enabled=args.enable_side_effects,
            reason="PM-confirmed S0-A Part 1 execution" if args.enable_side_effects else "Step 0 framework review only",
        )
        result = run_repair_loop_for_scenario(ERROR_SCENARIOS[args.scenario], modules, gate)
        print(json.dumps(safe_asdict(result), indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0

    if args.mode == "run-part2-ab-test":
        gate = SideEffectGate(
            enabled=args.enable_side_effects,
            reason="PM-confirmed S0-A Part 2 execution" if args.enable_side_effects else "Part 2 code review only",
        )
        result = run_part2_ab_test(modules, gate)
        print(json.dumps(safe_asdict(result), indent=2, ensure_ascii=False, sort_keys=True, default=str))
        return 0

    raise AssertionError(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
