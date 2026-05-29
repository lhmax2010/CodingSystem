# S0-06 RawDataDetector Spike

## Scope

S0-06 validates the Contract v0.7.3 Section 5.6.3 RawDataDetector threshold
behavior with a Sprint 0 mock. It does not integrate with `ClineAdapter`; that
belongs to Sprint 1+.

Design context reread:

- `docs/baseline/00_Agent_Team_Contract_v0.7.3.md` Section 5.6.3
- `docs/design_changes/change_1.md` Issue 2
- `docs/baseline/06_Code_Navigation_Evidence_Infrastructure_v0.3.5.md` CNEIConfig threshold fields
- `docs/prompts/SPRINT_0_PROMPT_for_Codex_v1.2.1.md` S0-06

Doc consistency note: `SPRINT_0_PROMPT_for_Codex_v1.2.1.md` still contains the
older "5000 字符" wording, but Contract v0.7.3, `docs/README.md`, and
`docs/design_changes/change_1.md` all define the current 3000 / 6000 / 6000
character thresholds. This spike follows Contract v0.7.3 and the user's S0-06
instruction.

## Mock Detector

Artifact:

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_06_raw_data_detector.py`

Result artifact:

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_06_raw_data_detector_results.json`

Implemented thresholds:

| Layer | Threshold | Unit | Behavior |
|---|---:|---|---|
| L1 single `log_excerpt` | 3000 | characters | block if one excerpt exceeds this |
| L2 packet excerpt total | 6000 | characters | block if all excerpts in one packet exceed this |
| L3 raw content outside excerpt | 6000 | characters | block raw-like content outside `EvidencePacket.log_excerpt` |
| L3 line guard | 200 | lines | block raw-like content outside excerpt if line count exceeds this |

The mock explicitly records `DEFAULT_SIZE_THRESHOLD_BYTES=20480` as deprecated
and unused. Length checks use Python `len(str)`, i.e. Unicode character count,
not UTF-8 byte count.

Interface shape kept Sprint-1-friendly:

- `RawDataDetector.validate(prompt) -> DetectorResult`
- `RawDataLeakageError.failure_class = raw_data_leakage`
- structured reasons such as `l1_single_log_excerpt_exceeds_3000_chars`

## Case Results

Payloads are generated in memory. No raw payload/log content is committed.

| Case | Expected | Actual | Key measured chars | Reason |
|---|---|---|---:|---|
| Case 1 legal excerpt | allowed | allowed | 2 excerpts: 2800 + 2800 = 5600 | within L1 and L2 |
| Case 2 single excerpt > L1 | blocked | blocked | 3001 | `l1_single_log_excerpt_exceeds_3000_chars` |
| Case 3 multiple small excerpts > L2 | blocked | blocked | 2100 + 2100 + 2100 = 6300 | `l2_log_excerpt_total_exceeds_6000_chars` |
| Case 4 raw log outside excerpt > L3 | blocked | blocked | 6001 | `l3_raw_content_outside_excerpt_exceeds_6000_chars` |
| Case 5 character-not-byte control | allowed | allowed | 2500 chars / 7500 UTF-8 bytes | confirms character-based threshold |

All blocked cases returned `failure_class = raw_data_leakage`.

## Raw Boundary

The raw-like test content is derived/generated at runtime and is not written to
repo artifacts. The committed result JSON contains only case IDs, counts,
reasons, and detector outcomes.

`EvidencePacket.log_excerpt` content is skipped by raw-content scanning only
after the excerpt structure passes the L1/L2 checks. Raw-like content outside
the excerpt structure is scanned and blocked when it exceeds L3.

## Pending Decision

S0-06 decision is pending user review.

Observed result: all required cases matched the expected detector behavior, and
the extra non-ASCII control case confirms thresholds are measured in characters
rather than bytes.
