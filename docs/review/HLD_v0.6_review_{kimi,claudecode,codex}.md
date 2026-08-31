## 1. 总裁决

**NO-GO。**v0.6 已修复上轮大部分问题，但仍有 **2 项 BLOCKER、3 项 MAJOR、1 项 MINOR**；effect 重放身份和嵌套 fan-out 的 join 关联尚未闭合。

## 2. 任务 A 结果表

| 本方第五轮编号 | 接受关闭/不接受 | 不接受的理由与定位 |
|---|---|---|
| 重开 R4-01 BLOCKER | 接受关闭 | §5.2 的 `dispatch_id` 已解决兄弟 task/entry 碰撞；probe 成功改为 succeeded 复用，unknown 也进入状态全集。新发现的 effect occurrence 问题属于 v0.6 新方案缺陷，另列 R6-01/R6-02。 |
| 重开 R4-04 MAJOR | **不接受** | 原问题定位在 §4.4：第242条规定 plain-decision 不生成授权，第243条仍无条件声明原子提交“决定 + 授权记录 + gate outcome CAS + resume outbox”。§8.2 新增适用范围不能消除 §4.4 内部的直接矛盾。 |
| R5-01 BLOCKER | 接受关闭 | §4.2.4 已删除“更新 activation 首达淘汰旧者”，明确同 series 多 activation 独立 open、消费、超时，原反例与环向量全序问题均已解决。新的嵌套 fan-out 关联问题另列 R6-03。 |
| R5-02 BLOCKER | 接受关闭 | §4.2.5 已规定 release 无出边、校验器拒绝 `from: release`，outcome 由 Ledger 固定映射关闭，不再需要不存在的 `publishing → queued/running` 转换。 |
| R5-03 BLOCKER | 接受关闭 | §8.3 已明确 `administrative finalize > cancel > fail_safe > 默认`，PONR 后 D12 漂移且发布失败的反例会优先走 administrative finalize。 |
| R5-04 MINOR | 接受关闭 | released → closed(succeeded) 已改记审计与 Run 终局摘要，不再生成 FeedbackReport。新引入的报告契约勘误另列 R6-05。 |

## 3. 任务 B 结果

1. **effect slot：反对。**  
   `dispatch_id` 对跨 task、兄弟送达及 entry 的隔离成立，成功对账后复用的策略反转也正确；但服务端分配 `effect_seq` 并不能识别跨 attempt 的逻辑调用。两个同参调用在重试时究竟匹配旧 seq、还是分配新 seq，没有确定规则；非决定论改变调用顺序时，即使增加 attempt cursor 也可能误复用。另有“无 probe → unknown/sys.error”与“允许仅声明安全重放”的能力契约冲突，见 R6-01/R6-02。

2. **activation 并发语义：反对。**  
   上轮同 series A/B 并发及陈旧 timer 反例已经通过，但 activation 上下文仍是单值。合法的嵌套 fan-out 可以让同一 join 的两个来源携带不同层级的 activation_id，从而永远不能成组；现有静态校验规则不会拒绝该图，见 R6-03。

3. **release 固定映射：接受。**  
   release 无 DSL 出边、核销原子进入 publishing、期间只登记 pending、broker outcome 优先及固定 pending 序共同消除了原状态机缺口。Ledger 单写者使 pending 与 outcome 事务形成明确全序。R13 人工裁决入口的接口缺失属于自动映射之外的新运维问题，另列 R6-04。

## 4. 新 issue 清单表

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| R6-01 | BLOCKER | §5.2、§4.3.2 | 服务端分配 `effect_seq` 没有解决逻辑调用匹配。反例：attempt 1 中同参调用 A 得到 seq=1 并成功，调用 B 得到 seq=2 后崩溃；attempt 2 若控制流跳过 A、以 B 作为首个同参调用，则按“第 k 次调用”会错误复用 A。若每次 claim 总是递增，又会导致正常重放无法命中旧记录。当前 `side_effect(idem_key, fn)` 似乎允许调用方提供身份，但计算公式没有纳入该身份。 | 冻结稳定的逻辑调用标识：将调用方提供、跨 attempt 稳定的 `effect_call_id` 纳入 key，并要求同一 task 内逻辑效应唯一；`effect_seq` 仅用于同一调用标识下明确声明的重复执行。补充“双同参调用、首个成功后崩溃、重试顺序改变”的故障注入测试。 |
| R6-02 | MAJOR | §5.2 第278、280、282条 | 第278条规定无 probe 能力一律持久化 unknown 并转 sys.error；第282条却允许刷板/板上执行“可 probe **或**声明可安全重放”。因此一个合法的、无 probe 但可安全重放的效应在 running 后崩溃时没有恢复分支，只能失败。 | 在查找矩阵中增加明确的 `replay_safe` 分支：无 probe 且声明安全重放时，将旧在途记录按既定状态退役并以新 effect 身份重放；未声明安全重放才进入 unknown/sys.error。conformance 分别覆盖 probe-only、replay-safe、不可判定三类。 |
| R6-03 | BLOCKER | §4.2.4、§4.2.6、§11.3 | 单一 activation_id 无法组合嵌套 fan-out。反例：根 fan-out 产生 A0，右分支 R 直接去 join J；左分支再 fan-out 产生 A1，其子节点 X 去 J。R 携带 A0、X 携带 A1，`(run,J,activation,source)` 永不成组，但该图满足现有 wait_for、可达性及禁链式 join 校验。类似地，同一 source 在同 activation 下被独立触发两次时，第二个到达会被当作重复丢弃。 | DSL v1 建议采用静态限制：对每个 join 确定唯一的共同支配 fan-out/root，要求全部来源共享该 activation scope，并拒绝在仅部分来源路径上引入未先汇合的嵌套 fan-out，以及同 source 每 activation 多次送达的图；加入相应 validator property 与 model-based 反例。 |
| R6-04 | MAJOR | §14 R13、§8.3、§8.5 | “运维 CLI 对账/裁决命令”没有定义可执行语义：允许的裁决结果、必需远端证据、调用权限、状态 guard、审计字段及如何原子应用 §8.3 映射均未定。反例：远端 push 超时但实际成功，操作员先裁决 release_failed 并关闭 Run，稍后远端发布可见，Ledger 与发布事实永久矛盾。 | 在 HLD 固定裁决协议：仅允许处于 publishing 且强制 probe 后仍 unknown 的 Run；定义 `confirm_released`、`confirm_not_released`、`keep_unknown` 及各自证据要求；复用特权 OS 用户/peer credential；裁决记录、操作者、远端引用和终态迁移在单一 Ledger 事务提交，并补 E2E 故障用例。 |
| R6-05 | MINOR | §4.3.1、§6.1、§8.3 | §4.3.1 仍称 FeedbackReport 由保留节点生成、仅 administrative finalize 是 Ledger 级例外，但 v0.6 又规定 release_failed 由 Ledger 生成 FeedbackReport。新术语“Run 终局摘要”也未在 §3 或 §6.1 定义其是 artifact、Ledger 事件还是 API 字段。 | 在 §4.3.1 补 release_failed Ledger 例外；在 §3/§6.1 定义 Run 终局摘要的类型、生成条件、持久化位置及 `get_result` 暴露方式，精确 schema 可归入 `[01]`。 |

## 5. CLARIFY 清单

无。

## 6. 一句话总结

距离 draft freeze 还差 2 个 BLOCKER 与 3 个 MAJOR 的闭合，核心是稳定的逻辑 effect 调用身份、可组合的 join activation 作用域，以及 publishing 人工裁决协议。

上面是Codex的review意见

CodingSystem Framework HLD v0.6 第六轮复审报告（评审员：Claude Code）
1. 总裁决：GO（无 BLOCKER/MAJOR/MINOR；5 条 NIT 随 GO 列为 freeze 勘误，1 条 CLARIFY）
两处对既往取舍的推翻我均独立核验成立（理由见任务 A/B）；v0.6 的三个收敛方案闭合，未发现对前五轮已关闭问题的回归。本方连续第二轮 GO，且本轮已无 MINOR 级以上残留。

2. 任务 A：本方第五轮 issue 处置核验（含被推翻取舍的重新评判）
第五轮编号	结论	说明
W-01 (MINOR)	接受关闭	§4.2.4 补根 activation（entry 分派事务生成）；且 dispatch_id 入键后 entry task 的 effect slot 天然成立，双重闭合
W-02 (NIT)	接受关闭	§8.3 成功路径改"审计与 Run 终局摘要"，FeedbackReport 严格限于 fail_safe/administrative finalize 语境
W-03 (NIT)	接受关闭	§4.3.1 补 running→closed(succeeded) 直达边说明（terminal success_on 路径）
CL-a	接受	§8.2 补 plain-decision 型 CLI 呈现（该 gate 上游 Report 与决策上下文），两型清单入 01/07
CL-b	接受	R13 新增：publishing 滞留告警 + 运维对账/裁决 CLI 交付项（入 09）
推翻① 对账策略反转（涉本方第四轮 V-02 定案句）	接受新方案	Codex 反例成立：效应能力契约允许"可 probe 但不可安全重放"（§5.2 刷板类），"成功保守重做"会强制重放此类效应，违反其自身契约——我方原"不复用"取舍仅对构建类幂等效应安全。新方案（probe 确认成功 → 迁移 succeeded 可复用）同时消除了我第四轮已指出但未追到底的"attempt 边界与恢复协议两路径政策不一致"——反转后两路径统一为 probe-确认-复用，比原方案更自洽
推翻② 废除 latest-wins supersede（涉本方第四轮 V-01 落文的一部分）	接受新方案	Codex 反例成立：环计数向量无全序，"更新者"不良定义；且同 series 合法并发 activation 会被误淘汰致下游丢触发。关键核验：我方 v0.4 原始反例（A1 首达后 series 推进、多日审批）在两条件方案下仍然消除——条件①在 series 推进事务内 supersede 旧 series 全部 open activation 并作废计时器，CAS 守卫使迟到 timer 为 no-op；§11.3 保留"stale activation 超时不误杀"断言并新增并发 activation model-based 用例。退役保证未因废除 latest-wins 而削弱
3. 任务 B：三个仲裁关注点
B1（dispatch_id effect slot）：接受。 dispatch_id 以分派事件为锚，一举闭合三个残留：entry 分派天然有 dispatch 事件（v0.5 根 activation 补丁不再是键构成的必要条件）；同一 fan-out 经两条边送达同一非 join 节点产生两个并发 task（v0.5 下同 (run, node, activation) 必碰撞）各有 dispatch_id，天然隔离；retry 复用同一 task 即同一 dispatch，跨 attempt 稳定。effect_seq 由编排层在 claim 事务内分配、worker 不本地计数，"attempt 内第 i 次同参调用 ↔ seq i"的映射与查找矩阵（succeeded 复用 / claimed·running probe 续跑 / abandoned 不命中递增新键 / unknown 持久化报 sys.error）组合后无歧义分支；六态全集补齐 unknown 使对账结果全部可持久表达。

B2（activation 两条件 supersede + 并发独立性）：接受。 条件①（series 推进同事务 supersede 旧 series 全部 open activation）覆盖零到达与部分到达的旧 activation；条件②覆盖残余；同 series 多 activation 独立 open/消费/超时避免了 latest-wins 的误杀且无需全序假设；"仅 open 且属 current series 的超时可 fail_safe"与 CAS 守卫保持了 v0.4 反例的修复。一处冗余观察（②似为①的子集）入 CLARIFY，不构成缺陷。

B3（release 无出边 + ledger 级固定映射）：接受。 release outcome 脱离 DSL 路由消除了"publishing 终态与图路由竞争"这最后一处状态机双主：released → closed(succeeded)（pending 仅记审计与终局摘要）；release_failed 按 administrative finalize > cancel > fail_safe > 默认的固定序关闭，R5-03 的"PONR 后 D12 漂移 + 远端确认失败"反例在 admin finalize 最优先下正确落位；校验器拒绝 from: release 使穷尽性检查与新语义一致；R13 补上 publishing 滞留的检测与人工出口。残余竞态未发现。

4. 新 issue 清单（随 GO 的 freeze 勘误）
编号	等级	定位	问题描述	修改建议
X-01	NIT	§4.2.4	第 197 行 activation 语义句仍写"每次 fan-out / 环激活生成 activation_id"，未与 199 行生命周期句（含"Run 启动的 entry 分派事务（根 activation）"三事件）同步	197 行枚举补"entry 分派"或改引 199 行
X-02	NIT	§4.2.5	"release 节点无出边（outcome 由 §8.3 固定映射关闭，校验器拒绝 from: release 路由）"在同一条目中完整出现两次（修订合并残留）	删除重复句
X-03	NIT	§4.3.1	FeedbackReport 例外句仅列 administrative finalize 一个 ledger 级生成例外，未纳入 §4.2.5/§8.3 新定的第二例外（release_failed 终态映射的 ledger 级 FeedbackReport）	例外句改为"administrative finalize 与 release 终态映射两路径"
X-04	NIT	§8.3/§6.1/§3	"Run 终局摘要"为新引入的报告载体名，未入 §3 术语表与 §6.1 消息类型清单（get_result 的返回载体归属不明）	§6.1 消息类型补列（schema [01]），§3 酌情加一行
X-05	NIT	§5.2	恢复协议句"遇 running/claimed 记录 = 状态 unknown"中的"unknown"系口语（状态不确定），与六态全集中持久化 unknown 态构成术语碰撞	改为"状态不确定（待对账）"，unknown 仅指持久化态
5. CLARIFY 清单
CL-α：supersede 条件②（"已有到达因 series 推进全部转 stale"）在条件①（series 推进事务 supersede 旧 series 全部 open activation）下似为其子集——若②意在覆盖①实现遗漏之外的场景（如 activation 系列标签与到达系列标签可能不一致的实现方式），建议在 01 的 activation 迁移表中注明②的独立触发场景，或标注其为防御性冗余。
6. 一句话总结
可以 freeze——两处推翻均以有效反例为据且经独立复演成立，三个收敛方案闭合，本方历轮 issue 清零，仅余 5 条编辑级 NIT 与 1 条 CLARIFY，建议随 freeze 编辑一并落入，无需再走完整复审轮。

（本轮无新增外部事实断言需核实；历轮 LangGraph 依据不变——Interrupts、1.0 稳定承诺、部署版本兼容性。）

上面是Claude Code的review意见

两份文档已读完。本方第五轮为 GO（2 MINOR + 3 NIT + 1 CLARIFY 作勘误），本轮逐条核验落点，并按任务要求重点复演两处被推翻的既定取舍。

---

# 复审报告：00_Framework_HLD_v0.6（Kimi 方）

## 1. 总裁决：**GO**

本方第五轮 6 条全部妥善关闭；两处推翻既往取舍的反转，经独立复演反例后认定成立且新方案更优；三个仲裁关注点全部接受。增量审查未发现 BLOCKER/MAJOR，残留 1 条 MINOR + 3 条 NIT 作 freeze 勘误。本轮"无新机制、仅定义修正"的声明经逐节比对属实。

## 2. 任务 A：本方第五轮 issue 处置核验

| 编号 | 结论 | 说明 |
|------|------|------|
| M-01 | 接受关闭 | 簇 Y 取方案 b：§4.2.5 release 节点无出边、outcome 不走 DSL 路由、终态 ledger 级固定映射关闭、校验器拒绝 from: release——状态机矛盾根除，比我原建议的两选一更彻底 |
| M-02 | 接受关闭 | §14 R13：publishing 滞留超阈值告警（注明计时豁免不含告警）+ 运维对账/裁决 CLI 列为交付项入 09 |
| M-03 | 接受关闭 | succeeded-abandoned 标签随对账策略反转整体废除，状态全集改六态含 unknown——该反转本身的评判见任务 B-1 |
| M-04 | 接受关闭 | §8.2 开头括注限定"本节全部条款仅适用 release-approval 型"，plain 型单命令构成另行列明 |
| M-05 | 接受关闭 | §8.3 成功路径改记"Run 终局摘要（非 FeedbackReport）"，FeedbackReport 回归 fail_safe/admin finalize 专属 |
| CL-1 | 接受关闭 | §5.2 effect_seq 由编排层在 claim 命令的 Ledger 事务内分配、worker 不本地计数——正是我追问的分配点，且服务端分配顺带消除了并发 task 同 slot 的序号态 |

两处推翻的合规性确认：处置表对两处的反转均给出反例依据（兄弟送达共享 activation_id 碰撞；latest-wins 淘汰同 series 合法并发 activation），我独立复演后确认反例成立、反转正确，不构成"随意翻烧饼"（详见任务 B）。

## 3. 任务 B：仲裁关注点独立判断

**B-1（dispatch_id 锚定的 effect slot）：接受。** 逐项验证：①跨 task 碰撞——兄弟送达各有分派事件 Ledger 记录 → dispatch_id 天然互异，v0.5 的同 activation 碰撞面消除；entry 由根 activation 的分派事务覆盖（W-01 合并关闭）；②跨 attempt 稳定——重试复用同一 task 即同一 dispatch，配合 effect_seq 服务端分配，键全链稳定；③对账策略反转成立——"可 probe 但不可安全重放的效应必须复用"是能力契约的逻辑必然：v0.5 的保守重做对此类效应是强制重复执行不可重放操作，Codex 反例有效；反转后 probe 确认成功 → 迁移 succeeded → 可复用，且与 at-least-once 声明不矛盾（复用是更强结果，承诺未变）；④unknown 入状态全集并与恢复协议（sys.error）闭环。唯一残留：dispatch_id 跨**进程重启**的稳定性依赖一个未显式声明的前提（恢复重执行沿用既有 dispatch 记录），记 M-01（MINOR）。

**B-2（两条件 supersede + 同 series 并发 activation）：接受。** 废除 latest-wins 的理由成立：环计数向量是偏序（多环共享节点时各环独立计数，§4.5），不存在全序，"更新者"本身不可定义；且同 series 合法并发 activation（上游非 join 汇聚的两次独立送达各触发 fan-out）会被误淘汰、永不触发。收敛后的两条件中，条件①（series 推进同事务作废）覆盖一切真实退役需求；同 series 多 activation 各自 open、独立成组（到达键含 activation_id，跨 activation 不混组）、独立超时、CAS 守卫迟到事件——并发语义闭合。根 activation 补齐 entry 来源。条件②在①之下不可达，属冗余而非错误，记 M-04（NIT）。

**B-3（release 无出边 + ledger 级固定映射）：接受。** 复演第五轮反例：publishing（PONR 已核销）→ broker 执行中 D12 漂移检出 → administrative finalize 登记 pending 且被状态级例外拦住先对账 → broker 回报 release_failed → 按 pending 序 administrative finalize 最优先 → ledger 级 closed(fail_safe) + 版本漂移 FeedbackReport，不落入普通路由、不烧错路径。released × pending cancel → closed(succeeded) + 终局摘要，已发布事实不被改写。校验器静态拒绝 from: release 使 DSL 层无从绕过固定映射。无残余竞态：映射执行与 pending 登记均为编排进程单写者事务。两处文字级瑕疵记 M-02/M-03（NIT）。

## 4. 新 issue 清单

| # | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|------|------|---------|-------------|
| M-01 | MINOR | §5.2 / §4.3.3 | dispatch重启的稳定性是幂等链的隐含前提但未显式声明：§4.3.3"恢复即节点重执行" + §5.2 键含 dispatch_id，只有当恢复重执行**沿用 Ledger 既有 task/dispatch 记录**（而非产生新分派事件）时键才命中；若实现按新分派处理，全部效应键漂移，probe-able 不可重放效应将被重复执行——恰是本轮反转要避免的事故。文本只声明了"跨 attempt 稳定"，未声明跨 restart | §4.3.3 或 §5.2 补一句：恢复重执行复用既有 task/dispatch 记录（dispatch_id 不变），不产生新分派事件；§11.3 故障注入用例补对应断言 |
| M-02 | NIT | §4.3.1 vs §4.2.5/§8.3 | FeedbackReport 例外句列举不全：§4.3.1 称"由保留节点生成，administrative finalize 为显式例外"，但 v0.6 新增第二条 ledger 级生成路径（release 固定映射下 release_failed 的 FeedbackReport，§4.2.5/§8.3）未列入 | §4.3.1 例外句补"release 固定映射路径（§4.2.5）" |
| M-03 | NIT | §4.2.5 | "release 节点无出边（outcome 由 §8.3 固定映射关闭，校验器拒绝 from: release 路由）"在该 bullet 内出现两次（首句与倒数第二句），纯编辑残留 | 删其一 |
| M-04 | NIT | §4.2.4 | supersede 条件②（"某 activation 的到达因 series 推进全部转 stale"）在条件①下不可达：stale 仅相对 series 推进定义，而推进事务已按①将全部旧 series open activation 作废——②无独立触发场景，"仅两个触发条件"的陈述因此不精确 | 删条件②，或注明其为①的兜底表述 |

## 5. CLARIFY 清单

空（第五轮 CL-1 已落为分配；无新疑问）。

## 6. 一句话总结

可以 freeze——六轮评审的关键路径（DSL、审批-发布、幂等恢复、并发汇合、特权 IPC）全部闭合并经反例复演验证，建议将 M-01～M-04 作为 freeze 勘误随 v0.6 定稿（M-01 一句声明优先落入 §4.3.3 与 01）。

上面是Kimi Code的review意见
