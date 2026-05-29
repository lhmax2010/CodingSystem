# S0-05 EvidencePacket Performance Spike

## Scope

S0-05 validates EvidencePacket assembly performance and packet size on the real
`pkgmgr-info` baseline selected in S0-01. This is a spike-only validation and
does not implement product CNEI code.

Updated docs reread before this spike:

- `docs/baseline/06_Code_Navigation_Evidence_Infrastructure_v0.3.5.md`
- `docs/baseline/05_Phased_Development_Plan_v2.1.4.md`
- `docs/prompts/MAIN_PROMPT_for_Codex_v2.4.md`
- `docs/design_changes/change_2_S0-04_LogErrorParser_spike.md`

Design check result: no new `[DESIGN_ISSUE]`.

## Acceptance

| Requirement | Result |
|---|---|
| Single EvidencePacket generation time < 2s, excluding clangd cold start | PASS |
| Estimated tokens <= 4000 | PASS |
| facts / negative_facts / log_excerpt counts reasonable | PASS |
| Raw log not committed | PASS |

## Method

Artifact:

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_05_evidence_packet.py`

Generated bounded artifacts:

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_05_evidence_packet_results.json`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_05_single_primary_packet.json`
- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_05_cascade_primary_packet.json`

Raw logs remain only under `/tmp/coding-system-s0/`.

The script generated EvidencePacket-shaped JSON from real S0-04 logs:

1. Single-primary case: S0-04 experiment 1.1 `cannot_find_header`.
2. Cascade case: S0-04 experiment 2 typedef rename cascade, using a spike mock for the v0.3.5 primary/cascade strategy.

The S0-04 diagnostic logs used here came from CMake/Make spike builds. S0-05 is
only validating EvidencePacket assembly cost and size; it is not expanding the
Phase 1A build-system backend scope. CMake/Ninja compile command feasibility was
covered by S0-02, and end-to-end CNEI flow remains S0-08.

The cascade case is intentionally a mock validation. Full LogErrorParser
taxonomy + primary/cascade implementation remains owned by S2b-03.

Token estimator: `tiktoken` is not installed in this environment, so the script
used `ceil(chars / 4)` fallback.

## Result

30 runs per scenario:

| Scenario | Max duration | Median duration | Tokens | facts | negative_facts | log_excerpt | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Single primary: `cannot_find_header` | 1.610 ms | 1.305 ms | 1057 | 6 | 2 | 1 x 558 chars | PASS |
| Cascade primary mock: `unknown_type_name` | 4.421 ms | 4.080 ms | 1006 | 7 | 2 | 1 x 655 chars | PASS |

Both are far below the S0-05 thresholds:

- Time budget: 2000 ms
- Token budget: 4000 tokens
- Single log excerpt budget: 3000 chars

## Cascade Strategy Check

S0-04 showed that generating one packet per error can exceed token budget:

- Raw log: 8960 estimated tokens
- All error packets: 8679 estimated tokens
- One primary packet with cascade summary: 340 estimated tokens in the S0-04 comparison

S0-05 rechecked this direction with an EvidencePacket-shaped object. The mock
primary/cascade packet includes:

- `error_type: unknown_type_name`
- first compiler error as primary candidate
- `cascade_summary` with same-symbol cascade count
- one bounded primary excerpt
- source-code negative fact that the public typedef declaration is absent

The resulting packet is 1006 estimated tokens, which confirms the v0.3.5
strategy is compatible with the S0-05 budget. This does not reduce the S2b-03
requirement: the real LogErrorParser must still implement taxonomy 10 classes,
LLD/GNU ld support, and primary/cascade identification.

## Raw Log Boundary

No raw build log is committed. Committed JSON artifacts contain only bounded
EvidencePacket `log_excerpt` values:

| Packet | Excerpt chars |
|---|---:|
| `spike_05_single_primary_packet.json` | 558 |
| `spike_05_cascade_primary_packet.json` | 655 |

Both excerpts are below Contract v0.7.3 L1 limit of 3000 chars.

## Conclusion

Codex judgment: S0-05 PASS.

EvidencePacket generation is comfortably below both hard limits on the selected
real Tizen repo and real S0-04 failure logs. The only boundary to carry forward
is implementation ownership: S0-05 validates the packet strategy, while S2b-03
must still deliver the formal LogErrorParser primary/cascade implementation.
