# HLD v0.4 三方复审处置表（→ v0.5）

裁决输入：Kimi **GO**（连续第二轮，6 MINOR/NIT + 2 CLARIFY 作勘误）、Claude Code NO-GO（1 BLOCKER + 1 MAJOR + 2 MINOR）、Codex NO-GO（重开 2 + 3 BLOCKER + 1 MAJOR）。
四个仲裁关注点：B4（IPC/deploy 兑现 D8）**三方一致接受，正式关闭**；B1/B2/B3 的反对方意见全部落为具体 issue，无悬空反对。

## 共识/交叉簇（本轮问题高度聚焦，三家互相印证）

| 簇 | 覆盖 | 处置 | 落点 |
|----|------|------|------|
| U activation 退役缺失（CC 与 Codex 独立构造出同一反例：旧 activation 计时器误杀健康 Run） | CC V-01(BLOCKER); Codex R4-02(BLOCKER) | 采纳（两家方案合并） | §4.2.4 activation 生命周期：series 推进同事务作废旧 open activation 及计时器；superseded 触发条件（更新 activation 首达 / 到达全 stale）；到达与 timeout handler CAS 校验 open+current；obsolete 事件与 timer = 审计化 no-op；仅最新 open activation 超时可 fail_safe；生成/持久化/传播时点补齐（并答 CC CL-i、Kimi CL-2）；§11.3 加"stale activation 超时不误杀"断言 |
| V 效应键残留缝隙 | Codex R4-01(BLOCKER); CC V-02(MAJOR); Kimi M-03(MINOR)+CL-1; CC CL-ii | 采纳 | §5.2 改锚 logical effect slot（run/node/**activation_id**，去 loop_round——Codex 的跨 task 碰撞反例由 activation 隔离消除）；effect_seq 改按计数（去"连续"）；记录状态全集（+abandoned）与查找矩阵：abandoned 不参与命中、同参新调用递增新键（CC 方案，与 Codex "同 slot 同参 probe 后复用或续跑"在非 abandoned 记录上相容）、unknown→sys.error；§4.3.2 措辞同步 |
| W publishing × administrative finalize | Codex R4-03(BLOCKER) + R3-02 未接受项; Kimi M-01(MINOR，同洞低评级) | 采纳 | §8.3：publishing 为 administrative finalize 的状态级例外（先 broker 对账/probe 远端，不可判定保持 publishing 待人工）；pending 枚举补 administrative finalize；**固定终态映射表**：broker outcome 优先——released→closed(succeeded)（pending 记审计），release_failed→依次 cancel/fail_safe/正常路由；[01] guard 表覆盖 publishing 源态 |
| X resume 路径与状态图 | Codex R3-08 未接受项; CC V-03; Kimi M-06 | 采纳 | §4.3.1 定案 paused→queued→running（重新排队）；queued 定义覆盖 resume；状态图重绘（publishing 入出边显式） |

## Kimi（M-01–M-06 + CLARIFY 1–2）——GO，全采纳

| # | 处置 | 落点 |
|---|------|------|
| M-01 | 采纳 | 簇 W |
| M-02 | 采纳 | §8.5 per-task socketpair 定案（无监听端点，伪造连接构造上不可能） |
| M-03 | 采纳 | 簇 V effect_seq 计数语义 |
| M-04 | 采纳 | §7.6.2 补"逻辑定义；计算为纯算法"衔接句 |
| M-05 | 采纳 | §6.1 "Approval 决定与授权记录" |
| M-06 | 采纳 | 簇 X 状态图重绘 |
| CL-1 | 采纳 | 簇 V 查找矩阵（abandoned 不参与命中）；schema 细则 [01] |
| CL-2 | 采纳 | §4.2.4 activation 生成于分派事务、恢复自 Ledger 重建 |

## Claude Code（V-01–V-04 + CL-i/ii）

| # | 处置 | 落点 |
|---|------|------|
| V-01 BLOCKER | 采纳 | 簇 U（其时间线反例为定案依据；退役规则按其建议句式落文） |
| V-02 | 采纳 | 簇 V（取其定案句：abandoned 不命中、递增新键、un-probe-able→sys.error） |
| V-03 | 采纳 | 簇 X |
| V-04 | 采纳 | §4.5 run_budget 与 join timeout 排除 paused/publishing（其反例成立：含 paused 则多日审批必杀挂审 Run） |
| CL-i | 采纳 | §4.2.4 传播定义句 + 细则 [01] |
| CL-ii | 采纳 | 簇 V |

## Codex（重开 2 + R4-01–R4-04）

| # | 处置 | 落点 |
|---|------|------|
| 重开 R3-02 | 采纳，重开成立 | 簇 W 固定终态映射表（v0.4 确未定 pending 优先级） |
| 重开 R3-08 | 采纳，重开成立 | 簇 X（其反例成立：gate resolved 而槽被占时状态无处安放） |
| R4-01 BLOCKER | 采纳 | 簇 V（其"键须绑定 task/activation"要求以 activation_id 入键实现；查找/迁移矩阵入 [01]） |
| R4-02 BLOCKER | 采纳 | 簇 U（其"series 推进同事务失效 open activation + CAS 校验 + no-op 化"方案全收） |
| R4-03 BLOCKER | 采纳 | 簇 W（其"publishing 状态级例外 + 不可判定保持待人工"方案全收） |
| R4-04 | 采纳 | §4.4 hitl 分两型（release-approval / plain-decision），plain 型不生成 manifest 与授权——保留普通人工 gate 能力而非删除 |

## 汇总
- 全部条目采纳，无裁剪；本轮无新机制，v0.5 全部为 v0.4 新定义的生命周期/边界补全。
- B4（IPC + deploy 兑现 D8）三方一致接受，四大架构主题（DSL 语义、审批-发布时序、幂等恢复、特权 IPC）中已有两项（DSL 框架性语义、IPC/D8）三方关闭。
- v0.5 复审重点：(1) 簇 U activation 退役规则是否闭合（CC 反例时间线复演）；(2) 簇 V effect slot + 查找矩阵；(3) 簇 W publishing 终态映射表。三者均为上轮方案的直接落文，若无新缺口即可 freeze。
