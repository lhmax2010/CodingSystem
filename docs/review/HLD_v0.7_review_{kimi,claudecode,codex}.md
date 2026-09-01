## 1. 总裁决：NO-GO

存在 **1 项新 BLOCKER、2 项新 MAJOR**，且上一轮 **R6-04 MAJOR 未真正闭合**。主要阻塞点是 join 静态校验仍会放行必然缺源的图。

## 2. 任务 A 结果表

| 本方第六轮编号 | 接受关闭/不接受 | 不接受的理由与定位 |
|---|---|---|
| 重开 R4-04 MAJOR | 接受关闭 | §4.4 已明确授权记录仅适用于 release-approval 型；plain-decision 型只提交决定、gate outcome CAS 与 resume outbox，原内部矛盾消除。 |
| R6-01 BLOCKER | 接受关闭 | §5.2 以调用方稳定 `effect_call_id` 取代调用顺序，`dispatch_id` 跨 attempt/重启稳定，`repeat_seq` 显式区分重复调用；原“控制流变化导致 A/B 错配”反例已解决。残留旧术语另列 R7-03。 |
| R6-02 MAJOR | 接受关闭 | §5.2 已给出 probe、replay_safe、两者皆无三支恢复路径；其中 replay_safe 使用同键版本化重放，能力契约与恢复矩阵一致。 |
| R6-03 BLOCKER | 接受关闭 | §4.2.6 已明确拒绝未汇合嵌套 fan-out 以及同 source 每 activation 多次送达，原两个反例均会被静态拒绝。新发现的共同 scope 仍不足以证明共同到达，另列 R7-01/R7-02。 |
| R6-04 MAJOR | **不接受** | §8.3 仅要求 `confirm_not_released` 附“远端查询输出/commit 引用”，但没有停止、隔离或证明原发布操作已不可能继续完成。反例仍成立：push 请求状态未知，查询时远端尚不可见，操作员据此关闭 Run；延迟请求随后成功，Ledger 与远端事实永久矛盾。单 Ledger 事务无法与在途远端操作形成原子序。 |
| R6-05 MINOR | 接受关闭 | §3 已将 Run 终局摘要定义为每个关闭 Run 的 artifact，并规定由 `get_result` 返回；§6.1 纳入消息类型，§4.3.1 也列全两条 Ledger 级 FeedbackReport 例外。 |

## 3. 任务 B 结果

1. **effect_call_id 方案：接受。**  
   稳定调用标识解决了按调用顺序匹配的问题；`dispatch_id` 隔离 task 且由 §4.3.3 保证恢复复用；异参旧在途记录先对账，三支恢复矩阵在不可判定时 fail-closed。§4.3.2 和公开 API 仍有旧术语，但属于文档一致性缺陷，不推翻核心模型，见 R7-03。

2. **join 作用域静态检查：反对。**  
   “共享 activation scope”只是正确分组的必要条件，不证明所有 `wait_for` 来源会在同一次 activation 中共同到达。根作用域例外会放行互斥 outcome 分支；此外，“内层先汇合”后的父 activation 恢复语义未定义，见 R7-01/R7-02。

3. **人工裁决协议：反对。**  
   状态 guard、权限、命令枚举和审计事务均已补齐，但 `confirm_not_released` 缺少发布操作 fencing/quiescence 和可验证的终态否定证据。普通查询结果只能证明查询时未观察到发布，不能证明延迟请求以后不会成功；R6-04 因而未关闭。

## 4. 新 issue 清单表

R6-04 是未关闭旧 issue，不在本表重复编号。

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| R7-01 | BLOCKER | §4.2.4、§4.2.6、§11.3 | join 校验没有证明来源能够共同到达。反例：同一节点的 outcome X 路由到 A、outcome Y 路由到 B，A/B 均指向 join J。一次 task 只能产生一个 outcome，因此每个 activation 只会到达 A 或 B；但该图具有共同根作用域、无嵌套 fan-out、每个 source 只送达一次，满足当前全部新增规则，运行时必然等待至 timeout/run_budget。 | 增加“共同激活/共同到达”静态性质：多源 join 原则上必须由同一次明确 fan-out 事件派生；校验每个分支要么恰好送达其 join source，要么通过 fail_safe 等路径关闭 Run。禁止以共同根支配关系替代共同 fan-out，除非校验器能证明所有来源在同一 activation 必然共同产生。§11.3 增加互斥 outcome 反例。 |
| R7-02 | MAJOR | §4.2.4、§4.2.6 | “拒绝未先汇合的嵌套 fan-out”暗示内层已汇合后可以继续参与外层 join，但运行时只有单一 `activation_id`，未定义内层 join 消费后输出是保留子 activation，还是恢复父 activation。若保留子 ID，外层兄弟携带父 ID，仍永不成组；若恢复父 ID，则缺少 parent 关系及恢复规则。 | 二选一定案：DSL v1 保守拒绝所有会继续进入外层 join 的嵌套 fan-out；或定义持久化父 activation 关系，并规定内层 join 原子消费后以父 scope 分派下游。相应用例需覆盖内层汇合后再参与外层 join。 |
| R7-03 | MAJOR | §4.3.2、§5.2 | v0.7 已废除 `effect_seq` 服务端分配，但 §4.3.2 仍称 abandoned 后“按新 effect_seq 重新执行”；§5.2 又将公开入口写成 `side_effect(idem_key, fn)`，与“调用方只提供稳定 effect_call_id、框架计算 idem_key”冲突。实现者可能重新引入顺序分配，或允许 worker 自行提供完整幂等键，直接破坏 R6-01 的修复。 | 删除当前语义中的 `effect_seq`；将 abandoned 后行为统一表述为按三支矩阵创建同 idem_key 的新记录版本。明确 SDK 输入是 `effect_call_id`、规范化实参及可选 `repeat_seq`，最终 idem_key 只能由框架计算。 |

## 5. CLARIFY 清单

无。

## 6. 一句话总结

距离 draft freeze 还差 join 共同到达与嵌套 activation 语义定案、`confirm_not_released` 的远端操作 fencing，以及效应接口旧术语清理。

上面是Codex的review信息

两份文档已读完。本方第六轮为 GO（1 MINOR + 3 NIT，无 CLARIFY），逐条核验落点如下；三个仲裁关注点已按反例复演。

---

# 复审报告：00_Framework_HLD_v0.7（Kimi 方）

## 1. 总裁决：**GO**

本方第六轮 4 条全部妥善关闭；本轮对 v0.6 方案的推翻（effect_seq 服务端按序分配 → 调用方稳定 effect_call_id）经复演认定理由成立、新方案正确；三个仲裁关注点全部接受。增量审查未发现 BLOCKER，残留 1 条 MINOR + 1 条 NIT 作 freeze 勘误。

## 2. 任务 A：本方第六轮 issue 处置核验

| 编号 | 结论 | 说明 |
|------|------|------|
| M-01 (MINOR) | 接受关闭 | §4.3.3 显式声明"恢复重执行复用 Ledger 既有 task/dispatch 记录（dispatch_id 不变），不产生新分派事件"，§11.3 补对应故障注入断言——隐含前提已落为明文 |
| M-02 (NIT) | 接受关闭 | §4.3.1 FeedbackReport 例外列全两条 ledger 级路径；"摘要"入 §3 术语表与 §6.1 消息类型（get_result 载体，schema [01]） |
| M-03 (NIT) | 接受关闭 | §4.2.5 重复句已删，全节仅一处"release 节点无出边"表述 |
| M-04 (NIT) | 接受关闭 | supersede 条件②已标注"①的防御性兜底，非独立语义——实现以①为准"，取标注方案合理（保留兜底语义意图的说明） |

另核验 Codex 重开 R4-04 的更正（v0.5 处置表对 Kimi M-04 的关闭结论当时不彻底——只改 §8.2 未改 §4.4）：v0.7 §4.4 原子提交句已内联"授权记录【仅 release-approval 型；plain-decision 型无此项】"，内部矛盾消除，更正属实。

## 3. 任务 B：仲裁关注点独立判断

**B-1（effect_call_id 方案）：接受。** 推翻理由成立：v0.6 的服务端按序分配解决的是"序号从哪来"，但匹配仍依赖"第 k 次调用"的次序同一性——控制流变化的重试（重试路径多/少一次 LLM 调用、分支不同）会把新逻辑调用错配到旧记录，反例有效。新方案是此类问题的标准解（逻辑调用身份由代码内稳定标识承担，等价于 Temporal 的 activity id 思路）：①控制流变化重试——同 call_id 异参先对账 supersede 旧在途记录，错配消除；②跨重启——dispatch_id 跨重启稳定（本轮 M-01 落文）+ call_id 代码内稳定 + D12 锁定 agent 制品 digest（同 Run 内代码不变，call_id 语义不漂移），键全链稳定；③显式重复经 repeat_seq， task 唯一性强制分工清晰；④三支对账（probe / replay_safe 版本化重放 / 皆无→unknown+sys.error）与效应能力契约逐类对应，v0.6 的契约冲突消除。闭合。一处语义细节需作者澄清（CL-1），不构成缺陷。

**B-2（join 作用域静态检查）：接受。** 充分性：Codex 的两个反例形态（跨层级 activation 永不成组、同源每 activation 多次送达的到达键歧义）均由静态拒绝覆盖；旗舰示例复演通过——pre_final_review 的两源共享 compiler fan-out 这一唯一共同支配作用域，环激活经"环激活生成新 activation"供轮次隔离，不与到达键冲突。误伤检查：被禁形态（未先汇合的嵌套 fan-out 汇聚）可用"join → 中间节点 → join"等价表达（链式 join 禁令只禁 to 直连 join，中间隔节点即合法），表达力损失有逃逸口，MVP 约束可接受。子集示例（线性图）不受影响。充分且伤。

**B-3（人工裁决协议）：接受。** 逐项：适用面收窄正确（仅 publishing 且强制 probe 后仍不可判定——可判定情形已被自动对账覆盖）；confirm_released/confirm_not_released 强制附远端证据引用，堵住"裁决与远端事实相反"的操作员风险，证据入裁决记录可审计；keep_unknown 保留不裁决的合法选择；执行通道（特权 OS 用户 + peer credential）与 §8.5/deploy  provisioning 一致；单 Ledger 事务 + 终态按既有固定映射迁移，不引入第二套映射；§11.3 有"证据缺失拒绝"E2E。闭合。证据引用为自由文本、不做机器核验——这是人工裁决的固有性质，审计留痕已是 MVP 正确水位，不列为 issue。

## 4. 新 issue 清单

| # | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|------|------|---------|-------------|
| M-01 | MINOR | §4.3.2 vs §5.2 | 残留悬空引用：§4.3.2 仍称重试"经 abandoned 对账后按新 **effect_seq** 重新执行"，而 v0.7 已废除 effect_seq 概念（§5.2 改为 effect_call_id + repeat_seq）——effect_seq 全文已无定义。且新方案下该句语义本身已不准确：重试是同 call_id 再调用、abandoned 不参与命中即重建记录，不存在"新序号"动作 | §4.3.2 该句改写为"重试以相同 effect_call_id 再调用，命中同一记录；上一 attempt 遗留记录经三支对账后处置（§5.2）" |
| M-02 | NIT | §3 | dispatch_id / effect_call_id / activation 未入术语表——effect_call_id 是业务开发者必须自己提供的 contract 面向概念（conformance 强制），activation 自 v0.4 起承载 join 语义，均无 §3 条目补三条术语（可一行式，指向 §4.2.4/§5.2） |

## 5. CLARIFY 清单

1. §5.2："框架强制同 task 内 effect_call_id 唯一在册（conformance 检查项）"的确切违例形态是什么？按现文推演：同 call_id 同参 → 命中复用；同 call_id 异参 → 在途旧记录对账 supersede——两条路径都收容了重复，"唯一"约束似乎无运行时违例形态。请明确：唯一性是 conformance 测试期的代码规约检查（每逻辑调用点唯一命名），还是运行时存在拒绝路径？若是后者，违例时的 outcome 归类（sys.invalid_result?）需写明。

## 6. 一句话总结

可以 freeze——七轮评审后关键路径全部闭合，本轮推翻（effect_call_id）经反例验证正确，建议将 M-01/M-02 与 CL-1 的答案作为 freeze 勘误随 v0.7 定稿，01_Con_Spec 编写时一并落精确条款。

上面是Kimi Code的review信息

CodingSystem Framework HLD v0.7 第七轮复审报告（评审员：Claude Code）
1. 总裁决：GO（无 BLOCKER/MAJOR；1 MINOR + 1 NIT 随 GO 列为 freeze 勘误）
本方连续第三轮 GO。对 v0.6 effect_seq 方案的推翻我已独立复演并确认成立（含对我上轮接受该方案时论证缺陷的自我更正，见任务 A）；三个仲裁关注点均闭合。全文回归扫描仅发现一处修订遗漏的陈旧引用。

2. 任务 A：本方第六轮 issue 处置核验（含被推翻方案的重新评判）
第六轮编号	结论	说明
X-01 (NIT)	接受关闭	§4.2.4 activation 语义句枚举补"entry 分派"并引生命周期条，两处同步
X-02 (NIT)	接受关闭	§4.2.5 重复句已删，"release 无出边"条款现仅出现一次
X-03 (NIT)	接受关闭	§4.3.1 例外句列全两条 ledger 级生成路径（administrative finalize + release 固定映射）
X-04 (NIT)	接受关闭	"Run 终局摘要"入 §3 术语表（含内容构成与 get_result 载体定位，schema [01]）与 §6.1 消息类型
X-05 (NIT)	接受关闭	§5.2 恢复句改"状态不确定（待对账）"并引三支对账矩阵，unknown 专指持久化态
CL-α	接受	supersede 条件②标注"①的防御性兜底，非独立语义——实现以①为准"
推翻（v0.6 effect_seq 服务端按序分配，本方上轮 B1 曾接受）	接受新方案，并更正本方上轮论证	Codex 反例成立：顺序匹配把"attempt 内第 i 次同参调用"当作逻辑身份，但控制流变化的重试下第 i 次同参调用可对应不同逻辑调用位。我上轮以"同参调用不可区分，按序映射语义正确"接受——该论证对无状态效应（构建）成立，对有状态顺序效应不成立（反例：flash→测试A→flash→测试B，attempt 1 首刷成功后崩溃，attempt 2 控制流变化只需一次刷板，按序匹配复用首刷记录 → 板上残留测试 A 污染状态却被视为已刷）。effect_call_id 以代码内稳定命名锚定逻辑身份，与调用次序解耦，是正确修法；task 内唯一强制 + repeat_seq 显式重复 + 同 call_id 异参在途先对账，方案完整
3. 任务 B：三个仲裁关注点
B1（effect_call_id 方案）：接受。 逻辑身份由调用方在代码内命名（"build_main"/"flash_pre"），控制流变化的重试不再产生错配；参数相同命中同一记录、非决定论异参取新键并先对账 supersede 旧在途记录（重试仅发生在 worker 已被 killpg 终止之后，无并发外部执行残留）；attempt 启动前对上一 attempt 非终态记录逐条三支对账，未被新控制流触达的调用位记录成为无害审计残留；dispatch_id 跨重启稳定的前提已由 §4.3.3"恢复复用既有 task/dispatch 记录、不产生新分派事件"显式化并入 §11.3 断言（Kimi M-01 补上了这块隐含地基）。task 内唯一在册由 conformance 与运行时共同强制。闭合。

B2（join 作用域静态检查）：接受。 四条规则将 v0.6 运行时必然死锁的两类图（跨层级 activation 永不成组、同源多送达键歧义）前移为加载期拒绝——静态拒绝严格优于运行时死锁。误伤面核查：旗舰示例通过（bench_gate 与 review_static 的唯一共同支配 fan-out 即 compiler 的 build_passed 分派，两来源共享该 activation scope，路径无未汇合嵌套 fan-out）；compiler_bench_only 无 join 平凡通过；层级化汇合仍可经"先内层 join 再外层 fan-out"合法表达，与 N4 的领域裁剪一致。§11.3 有 validator property 与 model-based 反例用例。

B3（人工裁决协议）：接受。 作用域收窄正确（仅 publishing 且强制 probe 后仍不可判定，可判定态不可被人工覆写）；confirm 双向均须附远端证据引用并对证据缺失显式拒绝（§11.3 E2E），封住"裁决与远端事实相反"的低级路径；keep_unknown 提供无害缺省；特权 OS 用户 + peer credential 与 §8.5 权限模型一致；裁决记录与终态迁移单 Ledger 事务、终态走 §8.3 既有固定映射，无新增状态语义。证据引用本身不可被框架验真，属单操作员内网模型下可接受的留痕强制而非密码学证明——与 D13 一致。

4. 新 issue 清单（随 GO 的 freeze 勘误）
编号	等级	定位	问题描述	修改建议
Y-01	MINOR	§4.3.2 vs §5.2	§4.3.2 仍写"或经 abandoned 对账后按新 effect_seq 重新执行（§5.2）"——effect_seq 已被本轮推翻废除，引用悬空；且同键（同 call_id + 同参）遇 abandoned 记录后的重执行机制，§5.2 仅在 replay_safe 分支明示"记录版本化"，probe→abandoned 分支的同键新记录依何机制未一般化声明	§4.3.2 改为"或经对账后按 §5.2 记录版本化重新执行"；§5.2 将"同键新版本记录（记录版本化）"从 replay_safe 分支提升为通则——凡 abandoned 记录同键重执行均以版本化新记录承载，细则随迁移/查找表入 [01]
Y-02	NIT	§5.2	"同 call_id 的旧在途异参记录在命中前先对账 supersede"——effect 记录状态全集为 {claimed, running, succeeded, failed, abandoned, unknown}，无 superseded 态；"supersede"在本文档已是 activation 生命周期的专用词，此处指"对账后退役"	改为"先按三支对账后退役（abandoned）"，避免与 activation supersede 术语碰撞
5. CLARIFY 清单
（空）

6. 一句话总结
可以 freeze——effect_call_id、join 作用域检查、人工裁决协议三项均闭合，本方历轮 issue 清零，仅余 1 条修订遗漏的陈旧引用（Y-01）与 1 条术语 NIT（Y-02），随 freeze 编辑落入即可，无需再走完整复审轮。

（本轮无新增外部事实断言需核实；历轮 LangGraph 依据不变——Interrupts、1.0 稳定承诺、部署版本兼容性。）

上面是Claude Code的review意见
