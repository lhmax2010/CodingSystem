# Design Change 1：Codex Sprint 0 Design Review 6 个 Issue 修复

**触发**：Codex Sprint 0 启动前设计 Review（R1）
**日期**：2026-05-28
**决策者**：PM（user）+ Claude
**状态**：Approved & Applied
**影响范围**：Contract / Compiler / Benchmark / CNEI / 开发计划 / SPRINT_0_PROMPT

---

## 背景与触发原因

Codex 在 Sprint 0 启动前执行 R1 强制设计 Review，输出 `design_review_sprint_0.md`，发现 6 个 `[DESIGN_ISSUE]`。这些是真实的文档不一致或缺口，需要在启动 Sprint 0 前确认处理口径。

按 R1 规约，baseline 文档由 PM 更新（Codex 不得修改设计文档）。本次由 Claude 直接修订 baseline，PM 覆盖，Codex 重新读取。

---

## 6 个 Issue 与处理结果

### Issue 1：Sprint 0 gate 数量 / stale 归属 / spike report 路径不一致

**问题**：stale 检测在 SPRINT_0_PROMPT 的 S0-03（clangd）和 S0-09（独立 gate）重复出现，归属不清。

**处理**：
- gate 数量锁定：9 任务 = 1 prerequisite（S0-01）+ 8 core gates（S0-02~S0-09）
- stale 归属：S0-09 是独立 core gate（完整 stale 检测 + confidence 降级）；S0-03 只做 mtime 基础探测
- spike report 路径统一：`docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/`

**改动**：开发计划 v2.1.2 → v2.1.3（S0-03 行注明）；SPRINT_0_PROMPT v1.1 → v1.2（S0-03 stale 改为基础探测，指向 S0-09）

### Issue 2：RawDataDetector 阈值 5000 字符 vs 20480 bytes 冲突

**问题**：Contract §5.6.3 写 RawDataDetector 阈值 5000 字符，但 Compiler A5.2 代码骨架写 `DEFAULT_SIZE_THRESHOLD_BYTES = 20480`（20KB），单位和数值都冲突。

**处理**：统一三级阈值体系，单位统一为字符：
- L1 单 log_excerpt 上限：3000 字符
- L2 整 packet excerpt 总和：6000 字符
- L3 RawDataDetector 触发阈值：6000 字符（与 L2 对齐）
- 新增场景 C 防绕过（多个 small excerpt 累加超 6000）
- 废弃 `DEFAULT_SIZE_THRESHOLD_BYTES=20480`，改为 `DEFAULT_RAW_DATA_THRESHOLD_CHARS=6000`

**改动**：Contract v0.7.2 → v0.7.3（§5.6.3 重写）；CNEI v0.3.3 → v0.3.4（CNEIConfig 补 `max_log_excerpts_total_chars` + `raw_data_detector_threshold_chars`）

### Issue 3：verify_timeout_sec 被代码骨架引用但 budget schema 未定义

**问题**：A8.3 代码骨架引用 `budget["verify_timeout_sec"]`，但 budget schema 没定义默认值。

**处理**：budget schema 补 `verify_timeout_sec: 300`（5 分钟）。理由：isolated workspace 是增量 rebuild，300 秒足够；超时判定 verify 失败，走 bounded repair fail-safe。

**改动**：Compiler v5.2-RC2.2 → RC2.3

### Issue 4：Evidence collection 失败是 fail-fast 还是 degraded

**问题**：文档未明确 evidence collection 整体失败时的行为。

**处理**：degraded 优先，fail-fast 仅在完全无证据时。
- 单 collector 失败 → degraded 继续
- 单 backend 失败 → 降级到下一 backend（clangd→tree-sitter→ctags→ripgrep）
- 所有 backend 失败 + 无任何 fact → fail-fast（`evidence_collection_failed`）
- mandatory_negative_checks 无法执行 → 标 `check_status: unavailable`，不阻断

**改动**：CNEI v0.3.4 新增 §2.2.4

### Issue 5：Known Issues 初始数据 5 条 vs 20-30 条，时机不清

**问题**：Sprint 0 提到 5 条样例，其他地方提到 20-30 条完整数据，时机不清。

**处理**：用途和时机不同，不冲突：
- S0-07 用 5 份样例（仅验证 matcher 机制）
- 20-30 条完整数据是 Sprint 2b 前置（S2b-06，build team 协调）

**改动**：开发计划 v2.1.3（S0-07 行注明）

### Issue 6：Benchmark token_usage_summary 与 Contract token_usage 不一致

**问题**：Benchmark AgentResult 用 `token_usage_summary`（子字段 `total_tokens_in/total_tokens_out/cost_estimate_usd`），与 Contract 必填 `token_usage`（子字段 `total_in/total_out/by_stage`）字段名和结构都不一致。

**处理**：以 Contract 为准（Contract 是 Locked 最底层）。统一为 `token_usage` + `total_in/total_out/by_stage`。`cost_estimate_usd` 移至 trace metadata。

**改动**：Benchmark v5.2-RC2.3 → RC2.4

---

## 影响的 Phase / 模块 / 接口

| Issue | 影响 Phase | 影响模块 | 影响接口 |
|---|---|---|---|
| 1 | Sprint 0 | spike 流程 | 无（流程文字） |
| 2 | Phase 1A | RawDataDetector / CNEIConfig | RawDataDetector 阈值常量 |
| 3 | Phase 1A | budget schema | budget 字段 |
| 4 | Phase 1A | EvidenceCollector | collect_evidence 行为 |
| 5 | Sprint 0 / 2b | Known Issues | 无 |
| 6 | Phase 1B | Benchmark AgentResult | token_usage 字段 |

## 是否影响已完成的 checkpoint

否。本次变更在 Sprint 0 启动**前**，尚无任何代码或 checkpoint。

## 是否需要回滚或返工

否。纯设计文档修订，Codex 尚未编码。

## 关联版本号同步

因 baseline 版本号变化，以下文档的关联引用同步更新：
- MAIN_PROMPT v2.2 → v2.3
- SPRINT_1_PLUS v1.2 → v1.3
- 07/08/09 baseline 文档头部关联引用
- ADR-001 的 CNEI 引用 → v0.3.4

## 待 Codex 确认

无待确认项。口径已由 PM 确认，baseline 已修订。Codex 重新读取 `docs/` 后可启动 Sprint 0 S0-01。
