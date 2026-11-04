# HLD v2.6 第六轮定向复审处置表（→ v2.7）

裁决输入：Kimi **GO**（0 / 0 / 0 / 1 NIT）；Claude Code **GO**（0 BLOCKER / 0 MAJOR / 2 MINOR / 3 NIT）；Codex **NO-GO**（0 BLOCKER / 1 MAJOR / 0 MINOR / 1 NIT）。合计 8 条意见，归并为 6 个独立问题，**全部采纳**。负责人七项裁决三家均判成立（Claude Code 对 ② 只留一处措辞，已改）。

Claude Code 更正了本方上一轮的一条意见：上一轮所举"base_mismatch 路由到 terminal 时无出口"在加载期就会被规则③拒绝，实际不可达；terminal 兜底真正可达的触发是 campaign 在未决计划下违规返回 no_gain_found。本版据此改写兜底理由并把违规归到 Optimization task（S3）。

## MAJOR

| # | 问题 | 来源 | 处置与采用方案 | 理由 |
|---|------|------|---------------|------|
| S1 | purpose 判定写在 candidate **受理**事务内，计划随之创建 / 迁移；但冻结模型规定 series 在 task **完成**事务内才推进。撤销受理后 worker 崩溃，会出现"计划已撤销、代码未撤销"；新候选只是暂存就建了计划，反过来会拒绝后续合法提交 | Codex H26-01 | **采用 Codex**：受理时只做预校验（推导 purpose、校验准入、保存推导结果，可即时拒绝），计划的创建与迁移只在 §4.2.4 完成事务内与 series 推进一起原子发生；父版本 CAS 失败、候选作废、崩溃都不改变计划；重放不重复计数 | 计划状态与代码状态必须由同一事务决定，否则两者会不一致 |

## MINOR / NIT

| # | 问题 | 来源 | 处置 |
|---|------|------|------|
| S2 | 删去"修复段归属计划"后的残留：撤销条仍写"包含候选之后叠加的修复段"；§11.3 两条 v2.3 用例的前置条件"候选之后先修复"在新规则下不可构造；旧能力检查用例与 v2.6 的 absolute-only 豁免相反 | CC H26-01、Codex H26-02、Kimi NIT | 采用，逐处清理；旧用例替换为与新规则一致的写法 |
| S3 | terminal 兜底所举例子不可达；真正可达的是 campaign 在未决计划下返回 no_gain_found，此时违规被算在 terminal 而不是 Optimization，也绕过了节点 retry | CC H26-02 | 采用。未决计划时 Optimization 返回非 opt_patch_ready 的任何 status 均 sys.invalid_result；campaign 的 no_gain_found 运行时核对"无净变更"；兜底保留，理由改写为纵深防御 |
| S4 | `E-CANDIDATE-NOT-REVERT` 之后 Agent 该做什么未写明，可能把可恢复的 Agent 失误变成 fail_safe | CC H26-03 | 采用。拒绝响应携带 plan_id 与 parent_tree，Agent 须在同一 task 内改交撤销段（SDK 提供 `make_revert`），否则 sys.invalid_result |
| S5 | `suites: auto` 在加载期总是无法确定是否只用 absolute 指标，应写明一律按需要 A/B 处理 | CC H26-04 | 采用。豁免只适用于显式列出且版本锁定、全部 SPEC 为 absolute 的套件 |
| S6 | 审批呈现字段重复；"构建根由 reference 决定"把单个样本写成一般结论 | CC H26-05 | 采用。去重；改为"已调查样本中构建根取自 reference，能否独立固定为 unverified" |

## 记录更正（上一轮处置表 HLD_v2.5_review_disposition.md）

- 开头"归并为 5 个独立问题"应为 **4 个**（R1–R4）（Codex 指出）。
- R4 所举触发场景"base_mismatch 路由到 terminal"在加载期即被规则③拒绝、实际不可达；兜底仍保留，理由见本表 S3（Claude Code 指出并更正其上一轮意见）。

## 下一轮建议

HLD 两家 GO、一家只剩 S1 一个事务位置问题，已按 Codex 方案修正。建议与 01 v0.17 一起做最后一轮定向核对；若 HLD 部分无 MAJOR，即视为定稿。
