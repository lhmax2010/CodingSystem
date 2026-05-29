# S0-07 Known Issue Matcher Spike

## Scope

S0-07 validates the KnownIssueMatcher mechanism with 5 sample Known Issues.
This follows the clarified change_1 Issue 5 scope: Sprint 0 uses 5 examples
only; the 20-30 item production Known Issues dataset is deferred to S2b-06.

Design context reread:

- `docs/design_changes/change_1.md` Issue 5
- `docs/baseline/05_Phased_Development_Plan_v2.1.4.md` S0-07 / S2b-06
- `docs/baseline/06_Code_Navigation_Evidence_Infrastructure_v0.3.5.md` Section 7
- `docs/prompts/SPRINT_0_PROMPT_for_Codex_v1.2.1.md` S0-07

## Artifacts

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_07_known_issue_matcher.py`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_07_known_issues_sample.yaml`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_07_known_issue_matcher_results.json`

The sample YAML is governance-schema shaped and includes required scope fields:
`applicable_build_systems`, `supported_error_types`, anti-patterns, owner,
confidence, counters, and auto-downgrade metadata.

## Sample Known Issues

All 5 samples are derived from S0-04 real `pkgmgr-info` error samples.

| Sample ID | S0-04 source | Error type | Main hint |
|---|---|---|---|
| `s0_04_missing_include_directory` | exp1.1 `cannot_find_header` | `cannot_find_header` | restore missing include directory / check BuildRequires |
| `s0_04_gnu_ld_missing_target_link_library` | exp1.2 GNU ld undefined reference | `undefined_reference` | inspect link command and restore missing `target_link_libraries` |
| `s0_04_lld_undefined_symbol_format` | experiment A LLD undefined symbol | `undefined_symbol` | parse LLD referenced-by block and inspect link libraries |
| `s0_04_public_header_signature_drift` | exp1.3 type mismatch | `type_mismatch` | compare declaration, definition, and call site |
| `s0_04_stl_vector_allocator_value_type_mismatch` | exp1.4 STL template error | `template_error` | check container template arguments / allocator |

Governance lint result:

- sample count: 5
- missing required fields: 0
- invalid regex: 0
- anti-pattern count check: all >= 3
- `confidence_default`: all <= 0.8

## Matcher Behavior

The mock matcher enforces this order:

1. `status == active`
2. `error_type in supported_error_types`
3. `build_system in applicable_build_systems`
4. `toolchain/language` scope
5. regex match on `raw_message`

This is intentionally scope-first so text similarity alone cannot produce a
match when `supported_error_types` or build-system scope is wrong.

## Results

| Behavior | Cases | Expected | Actual |
|---|---:|---|---|
| Hit: error matches corresponding Known Issue | 5 | 5 matches | 5 matches |
| No hit: unrelated error does not match any Known Issue | 5 | 0 false positives | 0 false positives |
| Scope guard: same/known-looking text but wrong build_system or error_type | 10 | 0 false positives | 0 false positives |

Hit details:

| Case | Returned issue | Captured value |
|---|---|---|
| `hit_cannot_find_header` | `s0_04_missing_include_directory` | `header=pkgmgr_parser.h` |
| `hit_undefined_reference` | `s0_04_gnu_ld_missing_target_link_library` | `missing_symbol=pkgmgr_server::Daemonizer::Daemonizer()` |
| `hit_undefined_symbol` | `s0_04_lld_undefined_symbol_format` | `missing_symbol=pkgmgrinfo_basic_free_package` |
| `hit_type_mismatch` | `s0_04_public_header_signature_drift` | `expected=const char *`, `actual=const ParcelableType` |
| `hit_template_error` | `s0_04_stl_vector_allocator_value_type_mismatch` | no capture needed |

Scope guard details:

- 5 cases reused the exact real error text but changed `build_system` to `make`.
- 5 cases reused the exact real error text but changed `error_type` to `runtime_crash`.
- All 10 returned no match, validating the CNEI v0.3.5 `supported_error_types`
  and build-system scope constraints.

## Boundary

This spike does not create the production `data/known_issues.yaml`, and it does
not claim the 5 samples are sufficient for Phase 1A production use. They only
validate matcher mechanics. S2b-06 remains responsible for the initial 20-30
item governed Known Issues dataset.

Known Issue matches remain hints, not truth; downstream prompts must still ask
the LLM to verify hints against current facts and negative_facts.

## Pending Decision

S0-07 decision is pending user review.

Observed result: all three required matcher behaviors matched expectations:
correct hit/hint return, no-match silence, and no over-matching when
`build_system` or `error_type` scope is incompatible.
