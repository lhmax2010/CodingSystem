# HLD v0.6 三方复审处置表（→ v0.7）

裁决输入：Kimi **GO**（连续第四轮，1 MINOR + 3 NIT）、Claude Code **GO**（连续第二轮，5 NIT + 1 CLARIFY）、Codex NO-GO（重开 1 + 2 BLOCKER + 2 MAJOR + 1 MINOR）。
两处既往取舍的推翻（对账策略反转、废除 latest-wins）：**三方一致确认成立**（两家 GO 方均独立复演反例后接受），正式关闭。任务 B：B3（release 固定映射）三方一致接受关闭；B1/B2 的 Codex 反对落为 R6-01/R6-02/R6-03，逐条处置于下。

## Codex（重开 1 + R6-01–R6-05）——唯一 NO-GO 方，全采纳

| # | 处置 | 落点/说明 |
|---|------|----------|
| 重开 R4-04 | 采纳，重开成立 | v0.6 只改了 §8.2 未改 §4.4 自身条款，内部矛盾属实（处置不彻底，本表更正 v0.5 表的关闭结论）。§4.4 原子提交句内联限定"授权记录项仅 release-approval 型" |
| R6-01 BLOCKER | 采纳，**推翻 v0.6 的 effect_seq 服务端分配方案** | 其反例成立：顺序匹配（"第 k 次调用"）在控制流变化的重试下把新逻辑调用错配到旧记录，服务端分配不解决匹配问题。按其建议改为**调用方提供、代码内稳定的 effect_call_id 入键**（框架强制 task 内唯一，conformance 检查；显式重复经 repeat_seq）；同 call_id 异参旧在途记录先对账 supersede；注入用例照收（§11.3）。Kimi 上轮 CL-1 对分配点的关闭结论随之作废——分配点问题被"取消按序分配"整体消解 |
| R6-02 | 采纳 | §5.2 对账改**三支**：probe / **无 probe 但声明 replay_safe →退役旧在途记录、同键版本化重放** / 皆无 → unknown + sys.error——与效应能力契约（§5.2 末条"可 probe 或声明可安全重放"）的冲突消除；conformance 三类分别覆盖 |
| R6-03 BLOCKER | 采纳 | §4.2.6 join 作用域静态检查：唯一共同支配 fan-out/根作用域、全部来源共享该 activation scope、拒绝未先汇合的嵌套 fan-out、拒绝同 source 每 activation 多次送达（其两个反例——跨层级 activation 永不成组、同源二次到达被误判重复——均由静态拒绝消除）；validator property + model-based 反例入 §11.3 |
| R6-04 | 采纳 | §8.3 人工裁决协议定案：仅 publishing 且强制 probe 后仍不可判定；confirm_released / confirm_not_released（**必须附远端证据引用**——其"操作员裁决与远端事实相反"反例的解）/ keep_unknown；特权 OS 用户 + peer credential；裁决记录单 Ledger 事务；E2E 用例入 §11.3 |
| R6-05 | 采纳 | §4.3.1 FeedbackReport 例外列全（administrative finalize + release 固定映射两路径）；"Run 终局摘要"入 §3 术语表与 §6.1 消息类型（get_result 载体，schema [01]）——与 CC X-03/X-04、Kimi M-02 合并 |

## Kimi（M-01–M-04）——GO，全采纳

| # | 处置 | 落点 |
|---|------|------|
| M-01 MINOR | 采纳 | §4.3.3：恢复重执行复用 Ledger 既有 task/dispatch 记录（dispatch_id 不变），不产生新分派事件——效应键跨重启稳定的前提显式化；§11.3 断言（GO 方本轮最有价值的一条：隐含前提落为声明） |
| M-02 NIT | 采纳 | 并入 R6-05 处置 |
| M-03 NIT | 采纳 | §4.2.5 重复句删除（与 CC X-02 合并） |
| M-04 NIT | 采纳 | supersede 条件②标注"①的防御性兜底，非独立语义"（与 CC CL-α 同答，取标注不取删除） |

## Claude Code（X-01–X-05 + CL-α）——GO，全采纳

| # | 处置 | 落点 |
|---|------|------|
| X-01 | 采纳 | §4.2.4 activation 语义句枚举补 entry 分派并引生命周期条 |
| X-02 | 采纳 | 同 Kimi M-03 |
| X-03 | 采纳 | 并入 R6-05 |
| X-04 | 采纳 | 并入 R6-05 |
| X-05 | 采纳 | §5.2 恢复句改"状态不确定（待对账）"，unknown 专指持久化态；对账句同步引三支矩阵 |
| CL-α | 采纳 | 同 Kimi M-04 |

## 汇总
- 全部条目采纳；本轮一处推翻 v0.6 自身方案（effect_seq 服务端按序分配 → effect_call_id 调用方稳定标识），处置表已注明 v0.5 表相应关闭结论作废。
- 六轮 BLOCKER 轨迹：13→3→7→5→4→2；本轮两条 BLOCKER 均为 Codex 独立新发现（effect 调用身份、join 作用域），两家 GO 方复演区未覆盖到——异构评审的价值所在。
- v0.7 复审重点：(1) effect_call_id 方案是否闭合（含 task 内唯一强制与 repeat_seq）；(2) join 作用域静态检查是否充分且不误伤合法图；(3) 人工裁决协议。三者均为 Codex 自给方案的直接落文。
