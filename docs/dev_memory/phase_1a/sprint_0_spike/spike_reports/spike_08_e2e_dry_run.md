# S0-08 End-to-End Dry Run

## Scope

S0-08 validates the dry-run pipeline boundary:

`compile fail -> LogErrorParser -> EvidenceCollector -> EvidencePacket -> RawDataDetector -> mocked LLM entrance`

No real LLM provider was called. No patch was generated. The dry run stops at
the LLM entrance and records the prompt-preflight artifact only.

Design context reread:

- `docs/prompts/SPRINT_0_PROMPT_for_Codex_v1.2.1.md` S0-08
- `docs/baseline/02_Compiler_Agent_v5.2-RC2.3.md` budget schema and trace shape
- `docs/baseline/00_Agent_Team_Contract_v0.7.3.md` trace/events/token usage
- `docs/baseline/06_Code_Navigation_Evidence_Infrastructure_v0.3.5.md` primary/cascade strategy

Doc consistency note: `SPRINT_0_PROMPT_for_Codex_v1.2.1.md` says token budget
must not exceed 25000, while the user instruction for this run asks to report
Compiler RC2.3 `max_tokens_per_task = 50000`. The measured dry run is below
both limits.

## Input

Real failure source: S0-04 experiment 2 typedef rename cascade.

- Raw log: `/tmp/coding-system-s0/s0_04_exp2_build.log`
- Diff reference: `/tmp/coding-system-s0/exp2_cascade.diff`
- Raw log committed: no

The compile stage is represented as a replay of the already captured S0-04 real
failure log. This avoids inventing a new error while still exercising the whole
post-failure pipeline.

## Artifacts

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_08_e2e_dry_run.py`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_08_e2e_dry_run_results.json`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_08_artifacts/CMP-S0-08-DRYRUN/trace.json`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_08_artifacts/CMP-S0-08-DRYRUN/events.jsonl`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_08_artifacts/CMP-S0-08-DRYRUN/evidence/ep_001.json`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_08_artifacts/CMP-S0-08-DRYRUN/llm/mock_llm_request.json`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_08_artifacts/CMP-S0-08-DRYRUN/build_report.json`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_08_artifacts/CMP-S0-08-DRYRUN/token_usage_summary.json`

## Pipeline Result

| Step | Result |
|---|---|
| compile fail | replayed real S0-04 captured failure log |
| LogErrorParser | parsed typedef cascade into structured events |
| primary/cascade | 1 primary, 38 same-symbol follow-on diagnostics, 2 terminal compiler-limit lines |
| EvidenceCollector | generated 1 primary EvidencePacket |
| KnownIssueMatcher | 0 matches for `unknown_type_name` sample |
| RawDataDetector | allowed bounded packet prompt |
| LLM entrance | mock request written; no provider call |

Primary/cascade accounting:

| Metric | Value |
|---|---:|
| raw compiler `error:` lines | 41 |
| `unknown_type_name` diagnostics | 39 |
| primary errors | 1 |
| same-symbol cascade diagnostics excluding primary | 38 |
| `too many errors emitted` lines | 2 |
| EvidencePackets generated | 1 |
| per-error packets avoided | 40 |

This validates the v0.3.5 strategy end to end: the cascade log did not produce
41 EvidencePackets.

## Trace Completeness

| Check | Result |
|---|---|
| `trace.json` exists | yes |
| `events.jsonl` exists | yes |
| trace event count | 10 |
| events.jsonl line count | 10 |
| events match trace | yes |
| event types present | `tool_call`, `state_transition`, `evidence_collected`, `known_issue_matched`, `budget_check`, `llm_call` |
| LLM call event has `evidence_packet_ref` | yes, `evidence/ep_001.json` |
| LLM actually called | no, `mocked=true`, `llm_called=false` |

Event flow:

1. `probe_s0_08_inputs`
2. `run_compile_replay`
3. `RunCompile->ParseErrors`
4. `LogErrorParser.parse`
5. `EP-CMP-S0-08-001`
6. `KnownIssueMatcher.match`
7. `RawDataDetector.validate`
8. `TokenLedger.preflight`
9. `analyze_compile_failure` mock LLM entrance
10. `DryRunComplete`

## Token Budget

Estimator: `chars_div_4_fallback` because `tiktoken` is not installed.

| Budget item | Limit | Measured | Result |
|---|---:|---:|---|
| EvidencePacket | 4000 | 1036 | within limit |
| LLM call input | 8000 | 1227 | within limit |
| Sprint 0 prompt budget note | 25000 | 1227 | within limit |
| Compiler RC2.3 task budget | 50000 | 1227 | within limit |

No output tokens were counted because the LLM call was mocked and no provider
call happened.

## Raw Boundary

RawDataDetector preflight result:

| Metric | Value |
|---|---:|
| status | allowed |
| excerpt count | 1 |
| excerpt chars | 699 |
| max excerpt chars | 699 |
| L1 / L2 / L3 | pass / pass / pass |

The committed mock LLM request contains one bounded `log_excerpt`; it does not
contain the full raw log. The raw build log remains under `/tmp/coding-system-s0/`.

## Pending Decision

S0-08 decision is pending user review.

Observed result: the real S0-04 cascade failure traversed the full dry-run
pipeline to the mocked LLM entrance, produced complete trace artifacts, stayed
well inside token budgets, and generated one primary EvidencePacket rather than
one packet per compiler error.
