# Phase 1A Sprint 0 Dev Memory

**Date**: 2026-05-30
**Branch**: `codex/sprint-0-main`
**Status**: Sprint 0 closed; S0-01 prerequisite and S0-02~S0-09 core gates all confirmed PASS by user.
**Checkpoint**: `checkpoint/phase_1a_sprint_0_spike_complete`
**Scope boundary**: Sprint 0 was spike validation only. No product code was implemented. S0-10 Scale Spike was not started.

This file is the recovery note for the next engineer. It summarizes what was proven, which design inputs were created, and what must be carried into Sprint 1 / Sprint 2b.

## Current Baseline

Relevant docs after Sprint 0:

- Contract: `docs/baseline/00_Agent_Team_Contract_v0.7.3.md`
- Compiler Agent: `docs/baseline/02_Compiler_Agent_v5.2-RC2.3.md`
- Benchmark Agent: `docs/baseline/03_Benchmark_Agent_v5.2-RC2.4.md`
- CNEI: `docs/baseline/06_Code_Navigation_Evidence_Infrastructure_v0.3.5.md`
- Development plan: `docs/baseline/05_Phased_Development_Plan_v2.1.4.md`
- Main prompt: `docs/prompts/MAIN_PROMPT_for_Codex_v2.4.md`
- Sprint 0 prompt: `docs/prompts/SPRINT_0_PROMPT_for_Codex_v1.2.1.md`
- Sprint 1+ prompt: `docs/prompts/SPRINT_1_PLUS_PROMPT_for_Codex_v1.3.md`
- Design changes: `docs/design_changes/change_1.md`, `docs/design_changes/change_2_S0-04_LogErrorParser_spike.md`

Frozen baseline docs were not edited during the individual spike runs except where the user explicitly stated that design changes had already been applied.

## Validation Target

S0-01 selected `platform/core/appfw/pkgmgr-info` as the Phase 1A validation baseline.

Key facts:

- Remote: `git://git.tizen.org/platform/core/appfw/pkgmgr-info`
- Branch: `tizen_10.0`
- Baseline commit: `469d442d9e1323d389d33f4689933c692c097429`
- Size: about 48.6 K C/C++/CMake LOC, 310 files, 8 `CMakeLists.txt`
- Existing tests: CTest 33/33 PASS in the validated GBS build
- Build route: x86_64 GBS + CMake/Ninja verified
- Historical toolchain migration sample: `c2bf5240083784312290b56bbf5a27ff6b7de1c0` "Fix build for Clang compiler"

The user confirmed `pkgmgr-info` satisfies the spike hard standard. The "3 developers familiar with repo" preference was split into a non-blocking dogfooding preference; for a 48 KLOC repo, 1-2 engineers able to read C/C++/CMake are enough for ground truth review.

## Gate Summary

| Gate | Result | Key Data |
|---|---|---|
| S0-01 repo selection | PASS | `pkgmgr-info` selected; CMake/Ninja/GBS route works; CTest 33/33; historical Clang build-fix commit identified. |
| S0-02 compile_commands | PASS | `compile_commands.json` valid; 203 entries; 153/153 translation units covered; missing 0; extra 0; 34 include paths; 9 defines; native x86_64 GBS build without hidden wrapper/sysroot interference. |
| S0-03 clangd accuracy | PASS | clangd 19.1.4; random sampling; definitions 50/50 = 100%; references 27/30 = 90%; peak RSS 3573.2 MB; index completion about 37.8s. Three reference misses were token-paste macro arguments from `LOG(ERROR/WARNING)`, accepted as non-critical. |
| S0-04 LogErrorParser coverage | PASS | 5 real C/C++ error classes covered with 30 real samples; deterministic parse 3/3 same SHA; GNU ld and LLD formats recorded; cascade typedef scenario measured 41 errors with primary 1 and cascade 39; raw log 8960 tokens vs primary packet 340 tokens in controlled comparison. |
| S0-05 EvidencePacket performance | PASS | Single primary packet max 1.610 ms, 1057 tokens; cascade-primary mock max 4.421 ms, 1006 tokens; both below 2s and 4000-token limits; raw logs not committed. |
| S0-06 RawDataDetector | PASS | Character-based thresholds validated: L1 3000 chars, L2 6000 chars, L3 6000 chars; legal 5600-char packet allowed; 3001-char single excerpt blocked; 6300-char combined excerpt blocked; 6001-char raw outside excerpt blocked; 2500 non-ASCII chars / 7500 bytes allowed, proving chars not bytes. |
| S0-07 KnownIssueMatcher | PASS | 5 sample Known Issues derived from S0-04 real errors; 5/5 correct hits; 5/5 no-match cases silent; 10/10 scope guards prevented false positives when `build_system` or `error_type` was wrong; governance lint passed. |
| S0-08 e2e dry run | PASS | Real S0-04 typedef cascade replayed through compile fail -> LogErrorParser -> EvidenceCollector -> EvidencePacket -> RawDataDetector -> mocked LLM entrance; `llm_called=false`; trace 10/10 aligned with events.jsonl; 41 error lines -> 1 primary packet; EvidencePacket 1036 tokens; mock LLM input 1227 tokens; total task 1227 tokens. |
| S0-09 stale confidence | PASS | Fresh `compile_commands.json` gives clangd facts `high`; stale CMake mtime downgrades only clangd facts `high -> medium` with `confidence_modifier: stale_compile_commands`; tree-sitter/ctags/ripgrep unchanged; Benchmark path uses `DegradedBackend` and does not trigger stale handling. |

## Artifact Map

Current retained spike reports:

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/spike_05_evidence_packet.md`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/spike_06_raw_data_detector.md`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/spike_07_known_issue_matcher.md`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/spike_08_e2e_dry_run.md`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/spike_09_stale_detection.md`

Earlier S0-01~S0-04 reports were superseded by the approved design-change flow, but the data is recoverable from history:

- S0-01 report commit: `6d20070`
- S0-02 report commit: `572aca6`
- S0-03 report commit: `66617b5`
- S0-04 report commit: `26b0be4`
- S0-04 design sediment: `docs/design_changes/change_2_S0-04_LogErrorParser_spike.md`

Temporary raw logs and temporary package workspaces live under `/tmp/coding-system-s0/` and were not committed. This preserves the Raw Log hard boundary.

## Design Inputs From Sprint 0

### 1. LogErrorParser Needs Production-Grade Primary/Cascade Handling

S0-04 and S0-08 proved that per-error packet generation is the wrong default for cascade builds.

Observed cascade:

- Trigger: typedef rename/delete in a public header
- Raw compiler `error:` lines: 41
- True primary: first compiler error
- Cascade shape: mostly repeated `unknown type name`
- S0-08 e2e result: 41 error lines collapsed into 1 primary EvidencePacket

Design consequence already captured in CNEI v0.3.5:

- LogErrorParser must output primary and cascade groups.
- EvidencePacket generation defaults to one packet per primary, with cascade summary.
- Sprint 2b implementation must not degrade primary/cascade identification into "parse all errors independently".

### 2. Taxonomy Expansion Is Mandatory

S0-04 exposed `unknown_type_name` as a common primary/cascade form not covered by the original 5-class taxonomy.

CNEI v0.3.5 expands the taxonomy to 10 classes:

- P0: `cannot_find_header`, `undefined_reference`, `undefined_symbol`, `type_mismatch`, `template_error`, `unknown_type_name`
- P1: `redefinition`, `incomplete_type`
- P2: `linker_script_error`, `version_script_error`

Sprint 2b must implement and validate this taxonomy against real logs.

### 3. LLD And GNU ld Formats Must Both Be Supported

S0-04 recorded both linker formats:

- GNU ld: `undefined reference to`
- LLD: `ld.lld: error: undefined symbol` with `>>> referenced by` blocks

LLD/libc++/musl-specific deep validation remains deferred, but dual-format support is no longer optional.

### 4. clangd Macro Blind Spot

S0-03 reference misses were all `LOG(ERROR/WARNING)` token-paste macro parameters, not normal semantic symbols.

Carry this rule into implementation:

> clangd references for token-paste macro parameters are unreliable. CNEI should mark macro-expansion-related symbol references `confidence: low` or `confidence: medium`, and add a `negative_fact` noting references may be incomplete.

This is not a blocker for Phase 1A because compile-fix evidence should rely on normal symbols, declarations, includes, and call sites rather than macro log-level tokens.

### 5. Token Data Correction And Reporting Guidance

There are two valid token measurements from Sprint 0, and they answer different questions:

- Controlled S0-04 comparison: raw cascade log 8960 tokens -> minimal primary packet 340 tokens, about 26x reduction.
- Realistic S0-08 dry run: raw cascade log 8960 tokens -> EvidencePacket 1036 tokens, about 8.65x reduction; raw log -> mocked LLM input 1227 tokens, about 7.3x reduction.

Use the realistic number as the safer implementation-facing claim: "about 9x token reduction at the packet boundary" for the tested cascade. Keep the 26x number only when explicitly describing the controlled minimal-primary comparison from `change_2`.

### 6. RawDataDetector Must Use Character Units

S0-06 closed change_1 Issue 2:

- L1 single excerpt: 3000 characters
- L2 packet excerpt total: 6000 characters
- L3 raw content outside excerpt: 6000 characters
- Deprecated byte threshold: `DEFAULT_SIZE_THRESHOLD_BYTES=20480` must not be used

The character-vs-byte control case is important for multilingual logs and must be preserved when implementing the Sprint 1 adapter boundary.

### 7. Known Issue Matching Must Be Scope-First

S0-07 showed that text similarity alone is unsafe. Matcher order should remain:

1. active status
2. `error_type in supported_error_types`
3. `build_system in applicable_build_systems`
4. toolchain/language scope
5. regex/text match

Known Issue hits are hints, not truth. Downstream prompts must still verify hints against current facts and negative facts.

### 8. Stale Detection Applies Only To clangd Facts

S0-09 confirmed the intended boundary:

- Compiler Agent path with CMake/Ninja can use clangd and stale detection.
- Stale compile database downgrades only clangd-derived facts.
- tree-sitter, ctags, and ripgrep facts do not depend on `compile_commands.json` and must not be downgraded.
- Benchmark path enters `DegradedBackend` when `build_system=None`; it does not trigger clangd stale handling.

## Carry Forward

Sprint 1 should start only after user confirmation and should use `docs/prompts/SPRINT_1_PLUS_PROMPT_for_Codex_v1.3.md`.

Immediate Sprint 1 first task:

- Create `check_gate.sh` with the development-plan v2.1.4 quality gate shape: 8 blocking checks + 1 advisory check.

Implementation work that must wait until Sprint 2b or later:

- Formal LogErrorParser implementation with 10-class taxonomy.
- Primary/cascade grouping as mandatory behavior, including same-symbol cascade detection and independent-primary splitting.
- LLD/GNU ld dual-format parser coverage with real build-farm style logs.
- Production Known Issues dataset of 20-30 governed entries.
- `failure_causality_graph` / ADR-001 Layer 0 scale direction beyond the Sprint 0 mock validation.
- LLD/libc++/musl migration-specific error collection once suitable current packages are available.

Environment and data caveats:

- For LLVM GBS builds, use `/home/linhao/Toolchain/gbs_llvm.conf`; public Tizen Base code may not match the latest LLVM build environment.
- If extra packages are needed for future LLD/libc++ logs, ask the user to download suitable Tizen package sources.
- In the current spike environment, direct libc++ validation was limited by missing `-lc++`; do not infer that libc++ migration is validated.

Things not done:

- S0-10 Scale Spike was not started.
- No Phase 1B work was started.
- No product code was added.
- No raw build logs were committed.
- `check_gate.sh` does not exist yet; this is intentional until Sprint 1.

## Recovery Steps For Next Engineer

1. Checkout `codex/sprint-0-main`.
2. Read `docs/README.md`, `docs/DEVELOPMENT_RULES.md`, `docs/prompts/MAIN_PROMPT_for_Codex_v2.4.md`, this memory file, and `docs/prompts/SPRINT_1_PLUS_PROMPT_for_Codex_v1.3.md`.
3. Confirm with the user before entering Sprint 1.
4. Do not start S0-10 unless the user explicitly asks.
5. Start Sprint 1 with `check_gate.sh`; do not jump ahead to LogErrorParser/CNEI production work.
