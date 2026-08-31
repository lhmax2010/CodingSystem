# HLD v0.5 三方复审处置表（→ v0.6）

裁决输入：Kimi **GO**（连续第三轮，2 MINOR + 3 NIT + 1 CLARIFY）、Claude Code **GO**（首轮转 GO，1 MINOR + 2 NIT + 2 CLARIFY）、Codex NO-GO（重开 2 + 3 BLOCKER + 1 MINOR）。
关键事实：Codex 的 NO-GO 项中有三条与两家 GO 方自列勘误为同一洞的不同评级（R5-02≈Kimi M-01、R5-04≈Kimi M-05/CC W-02、R4-04≈Kimi M-04）——分歧只在严重度，不在事实；逐条核对后 **Codex 全部意见成立并采纳**，其中两条推翻了此前轮次的既定取舍（见下）。

## 交叉簇

| 簇 | 覆盖 | 处置 | 落点 |
|----|------|------|------|
| Y release outcome 与 publishing 状态机矛盾 | Codex R5-02(BLOCKER)/R5-03(BLOCKER); Kimi M-01(同洞 MINOR) | 采纳（取双方共同给出的 MVP 方案 b） | §4.2.5/§8.3/§4.2.6：release 节点**无出边**、outcome 不走 DSL 路由，终态由固定映射 ledger 级关闭（release_failed 的 FeedbackReport 由 ledger 层生成，同 administrative finalize 例）；pending 序定为 **administrative finalize > cancel > fail_safe > 默认**（R5-03 反例：PONR 后 D12 漂移 + 远端确认失败，现走 admin finalize 优先，不再落入普通路由）；校验器拒绝 from: release |
| Z hitl 两型的 §8.2 适用范围 | Codex R4-04 重开(MAJOR); Kimi M-04(同洞 NIT) | 采纳，重开成立 | §8.2 开头限定"本节仅适用 release-approval 型；plain 型单命令无授权记录项" |
| AA FeedbackReport 语义越界 | Codex R5-04; Kimi M-05; CC W-02（三家同发现） | 采纳 | §8.3 成功路径改"审计与 Run 终局摘要"，FeedbackReport 仅 fail_safe/admin finalize |

## Codex（重开 2 + R5-01–R5-04）——本轮唯一 NO-GO 方，全采纳

| # | 处置 | 落点/说明 |
|---|------|----------|
| 重开 R4-01 BLOCKER | 采纳，重开成立，**推翻 v0.5 方案** | 三点全部有效：①兄弟送达共享 activation_id → 同 slot 碰撞（v0.5 的 activation 锚定不足）；②entry 前无 activation 来源（CC W-01 独立同发现）；③succeeded-abandoned"保守重做"违反效应能力契约——可 probe 不可安全重放的效应被强制重复执行（此点推翻第四轮 Kimi 背书的保守取舍，按能力契约仲裁 Codex 正确）。§5.2 重定：slot 改锚 **dispatch_id**（分派事件 Ledger 标识，跨 attempt 稳定、跨 task 含兄弟/entry 天然隔离，比其"绑定 task/activation+调用位"建议更简且等效）；对账策略反转（probe 确认成功 → succeeded 可复用）；状态全集补 unknown；effect_seq 由编排层 claim 事务分配（顺带答 Kimi CL-1，消除其"重执行改变同参调用数量/次序"的错配担忧——序号服务端分配、查找按矩阵） |
| 重开 R4-04 | 采纳，重开成立 | 簇 Z |
| R5-01 BLOCKER | 采纳，**推翻 v0.5 新增规则** | "更新 activation 首达即淘汰旧者"确不成立（其反例：同 series 合法并发 A/B，A 被淘汰后永不触发；环计数向量无全序）。§4.2.4 收敛为两触发条件（series 推进 / 到达全 stale），同 series 多 activation 独立 open/消费/超时；§11.3 补 model-based 并发用例 |
| R5-02 BLOCKER | 采纳 | 簇 Y（取其"MVP 静态限制 release_failed 直接映射固定终态"方案——较 publishing→queued 转换更简，不需扩状态机） |
| R5-03 BLOCKER | 采纳 | 簇 Y pending 序 |
| R5-04 | 采纳 | 簇 AA |

## Kimi（M-01–M-05 + CL-1）——GO，勘误全采纳

| # | 处置 | 落点 |
|---|------|------|
| M-01 | 采纳 | 簇 Y（其两选一与 Codex R5-02 方案 b 相同） |
| M-02 | 采纳 | §14 R13 publishing 滞留告警 + 运维对账/裁决 CLI 交付项（与 CC CL-b 合并） |
| M-03 | 采纳（经簇 Y/G3 消解） | succeeded-abandoned 标签整体废除（对账策略反转后不复存在），全集改六态含 unknown |
| M-04 | 采纳 | 簇 Z |
| M-05 | 采纳 | 簇 AA |
| CL-1 | 采纳 | §5.2 effect_seq 编排层 claim 事务分配 |

## Claude Code（W-01–W-03 + CL-a/b）——GO，勘误全采纳

| # | 处置 | 落点 |
|---|------|------|
| W-01 | 采纳 | §4.2.4 根 activation（entry 分派事务生成）；与 R4-01② 合并——dispatch_id 入键后 entry task 的 effect slot 亦天然成立 |
| W-02 | 采纳 | 簇 AA |
| W-03 | 采纳 | §4.3.1 补 running→closed(succeeded) 直达说明（terminal success_on 路径） |
| CL-a | 采纳 | §8.2 plain 型 CLI 呈现该 gate 上游 Report 与决策上下文，清单入 01/07 |
| CL-b | 采纳 | R13 运维对账/裁决 CLI 交付项，入 09 |

## 汇总
- 全部条目采纳；本轮两处**推翻既定取舍**（succeeded 复用替代保守重做、废除 latest-wins supersede），均以 Codex 的反例为定案依据并在上表注明——此前轮次对这两处的关闭结论作废。
- 五轮 BLOCKER 轨迹：13→3→7→5→4，且本轮 4 条中 3 条与 GO 方勘误同洞；v0.6 无新机制，全部为 v0.5 定义的修正与收敛。
- v0.6 复审重点：(1) dispatch_id 锚定的 effect slot 是否闭合（含 entry/兄弟送达/effect_seq 服务端分配）；(2) activation 两条件 supersede 下同 series 并发语义；(3) release 无出边 + ledger 级固定映射（含 pending administrative finalize 优先序）。
