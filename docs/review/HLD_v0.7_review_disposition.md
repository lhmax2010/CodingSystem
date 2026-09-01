# HLD v0.7 三方复审处置表（→ v0.8）

裁决输入：Kimi **GO**（连续第五轮，1 MINOR + 1 NIT + 1 CLARIFY）、Claude Code **GO**（连续第三轮，1 MINOR + 1 NIT）、Codex NO-GO（R6-04 未接受 + 1 BLOCKER + 2 MAJOR）。
任务 B：B1（effect_call_id）**三方一致接受，正式关闭**（CC 并对其上轮接受 v0.6 方案的论证作了自我更正——有状态顺序效应反例）；B2/B3 的 Codex 反对落为 R7-01/R7-02 与 R6-04 续项，逐条处置于下。

## 交叉簇

| 簇 | 覆盖 | 处置 | 落点 |
|----|------|------|------|
| AB effect_seq 残留与 SDK 签名 | Codex R7-03(MAJOR); Kimi M-01(MINOR); CC Y-01(MINOR)/Y-02(NIT)（三家同发现，评级不同） | 采纳 | §4.3.2 悬空引用改写（重试=同 call_id 再调用，对账后按记录版本化重执行）；SDK 签名定案 `side_effect(effect_call_id, params, fn, repeat_seq=None)`——idem_key 只能由框架计算（conformance 强制，堵住"worker 自供完整键"回退路径）；记录版本化从 replay_safe 分支提升为通则（凡 abandoned 之上同键重执行均版本化）；"supersede"术语让位 activation 专用，效应侧改"对账后退役（abandoned）" |

## Codex（R6-04 续 + R7-01–R7-03）——唯一 NO-GO 方，全采纳（一处附诚实残余）

| # | 处置 | 落点/说明 |
|---|------|----------|
| R6-04 续（不接受成立） | 采纳（部分 fencing + 检测，残余显式登记） | 其批评正确：远端查询只证"查询时不可见"，证不了在途请求不迟到。v0.8 三重机制：① broker 侧静默为 confirm_not_released 的状态 guard（进程组终止 + lease 回收确认——本地在途归零）；② fencing 标识（远端对象携带 run_id+token_id，迟到发布可归因）；③ 裁决后复查窗口（默认 24h 重 probe，检出即告警+审计补记，不静默不改写终态）。**绝对 fence 不采纳**：git/gerrit 端点无两阶段提交协议，已离开本机的在途请求物理上不可撤——此为客观边界而非设计取舍，登记 R14 残余风险（与 D13/N7 的残余处理风格一致）。若复审认为 24h 窗口方案不足，替代只有"禁用 confirm_not_released、仅留 keep_unknown 待远端超时自明"——牺牲运维出口换绝对一致，可作为攻击点 |
| R7-01 BLOCKER | 采纳 | §4.2.6 共同到达性检查：多源 join 必须由同一显式 fan-out 的不同分支派生（共同支配不得替代）；从 fan-out 到每来源的路径上，每个 outcome 分支须满足三者之一——可达来源 / 到 Run 终局 / 经声明环边回流（activation 由 series 推进或环预算耗尽退役）——其互斥 outcome 反例（X→A、Y→B 同 join）在此被静态拒绝；§11.3 补反例。旗舰示例复核通过：ut_fix 分支走环边（条件三），bench_gate fail 走 default fail_safe（条件二） |
| R7-02 | 采纳（取其方案 b） | activation 持久化 parent_activation_id，内层 join 原子消费后以**父 scope** 分派下游——内层先汇合再入外层 join 合法且可成组。不取保守拒绝（方案 a）：它会封死 Kimi/CC 在 B2 论证中依赖的"先内层 join 再外层"表达力逃逸口，与两家 GO 依据冲突；方案 b 增量小（一个持久化字段 + 分派规则一句） |
| R7-03 | 采纳 | 簇 AB |

## Kimi（M-01–M-02 + CL-1）——GO，全采纳

| # | 处置 | 落点 |
|---|------|------|
| M-01 | 采纳 | 簇 AB |
| M-02 | 采纳 | §3 补 dispatch_id / activation / effect_call_id 三条术语（effect_call_id 标注"业务开发者 contract 面向概念"） |
| CL-1 | 已答 | §5.2 定案两层面：conformance 静态检查（每逻辑调用点唯一命名）+ 运行时拒绝路径（同 call_id 未决记录上的异参新 claim → 拒绝，task 报 sys.invalid_result） |

## Claude Code（Y-01–Y-02）——GO，全采纳

| # | 处置 | 落点 |
|---|------|------|
| Y-01 | 采纳 | 簇 AB（其"版本化提升为通则"即定案文本） |
| Y-02 | 采纳 | 簇 AB 术语纠正 |

## 汇总
- 全部条目采纳；R6-04 为**带显式残余的采纳**（绝对远端 fence 客观不可达，方案与替代项已陈明供复审攻击）。
- 七轮 BLOCKER 轨迹：13→3→7→5→4→2→1；本轮唯一 BLOCKER（共同到达性）是对 v0.7 新增检查的必要条件/充分条件之辨——静态检查体系至此覆盖作用域、到达性、嵌套三层。
- v0.8 复审重点：(1) 共同到达性三条件是否充分且不误伤（含环边回流条件的边界）；(2) parent activation 分派语义；(3) R6-04 的三重机制 + R14 残余是否可接受（或改禁用 confirm_not_released）。
