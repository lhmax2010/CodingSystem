# S0-09 Stale Detection And Confidence Downgrade

## Scope

S0-09 validates the Compiler Agent path for stale `compile_commands.json`
detection and confidence downgrade behavior.

Design context reread:

- `docs/baseline/06_Code_Navigation_Evidence_Infrastructure_v0.3.5.md` Section 4.3.2.1
- `docs/prompts/SPRINT_0_PROMPT_for_Codex_v1.2.1.md` S0-09
- `docs/baseline/05_Phased_Development_Plan_v2.1.4.md` S0-09

Benchmark path is intentionally out of scope for this spike. CNEI v0.3.5 says
Benchmark calls CNEI with `build_system=None`, which degrades before clangd is
enabled, so stale detection does not trigger there.

## Artifacts

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_09_stale_detection.py`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_09_stale_detection_results.json`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_09_fresh_packet.json`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_09_stale_packet.json`

Temporary workspaces only:

- `/tmp/coding-system-s0/s0_09/fresh`
- `/tmp/coding-system-s0/s0_09/stale`

No user source tree was modified.

## Method

Input data:

- Source repo: `/tmp/coding-system-s0/repos/pkgmgr-info`
- Real compile database from S0-02:
  `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/s0/build-s0-02/compile_commands.json`

Two isolated workspaces were created:

| Scenario | Setup | Expected stale flag |
|---|---|---|
| fresh | all `CMakeLists.txt` mtimes older than `compile_commands.json` | `false` |
| stale | append a marker comment to temp `CMakeLists.txt` after copying `compile_commands.json`, without rerunning cmake | `true` |

The fact set intentionally mixes sources:

- 2 clangd semantic facts
- 1 tree-sitter syntax fact
- 1 ctags candidate fact
- 1 ripgrep text fact

This directly tests that stale downgrade applies only to clangd facts.

## Mtime Detection

| Scenario | compile_commands relation | `clangd_stale` | Provenance |
|---|---|---|---|
| fresh | `compile_commands.json` newer than newest `CMakeLists.txt` | `false` | `auto_cmake_ninja` |
| stale | `compile_commands.json` older than modified `CMakeLists.txt` | `true` | `auto_cmake_ninja` |

Stale reason:

`compile_commands.json older than newest CMakeLists.txt`

## Confidence Comparison

| Fact | Source | Fresh confidence | Fresh modifier | Stale confidence | Stale modifier | Changed |
|---|---|---|---|---|---|---|
| `F-CLANGD-DEF` | clangd | high | none | medium | `stale_compile_commands` | yes |
| `F-CLANGD-REF` | clangd | high | none | medium | `stale_compile_commands` | yes |
| `F-TREESITTER-CONTEXT` | tree-sitter | medium | none | medium | none | no |
| `F-CTAGS-CANDIDATE` | ctags | medium | none | medium | none | no |
| `F-RIPGREP-TEXT` | ripgrep | low | none | low | none | no |

Summary checks:

- all clangd facts are `high` when `stale=false`
- all clangd facts become `medium` when `stale=true`
- all stale clangd facts have `confidence_modifier: stale_compile_commands`
- non-clangd facts are unchanged
- EvidencePacket top-level `clangd_stale` flips from `false` to `true`

## Benchmark Path Note

For documentation only, the same selector with `build_system=None` returns:

| Field | Value |
|---|---|
| backend | `DegradedBackend` |
| provenance | `auto_degraded` |
| clangd_stale | `false` |
| reason | `build_system_unknown_not_cmake_ninja` |

This matches CNEI v0.3.5: Benchmark path does not enable clangd, so stale
downgrade is not applicable.

## Pending Decision

S0-09 decision is pending user review.

Observed result: stale detection and downgrade behavior matched the requested
shape. The downgrade was precise: only clangd-sourced semantic facts changed,
and tree-sitter / ctags / ripgrep facts were left untouched.
