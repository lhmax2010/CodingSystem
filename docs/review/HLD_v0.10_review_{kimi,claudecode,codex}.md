## 1. 总裁决：NO-GO

存在 1 项 BLOCKER、1 项 MAJOR、1 项 NIT。条件③仍未覆盖跨嵌套 activation 边界的回环，合法图可能保留永远无法补全的外层 activation。

## 2. 任务 A 结果表

| 本方第九轮编号 | 接受关闭/不接受 | 不接受的理由与定位 |
|---|---|---|
| R9-01 BLOCKER | 接受关闭 | §4.2.4 已规定子孙级联、祖先链 CAS 和替代 cohort 父继承；§4.2.6 已拒绝不重经共同 fan-out 的分支内回环，原反例及单层嵌套场景均已修复。跨越祖先 fan-out 的新反例来自 v0.10 规则组合，另列 R10-01。 |
| R9-02 MAJOR | 接受关闭 | §5.2 已取消“统一改为 abandoned”，明确三支分别进入 `succeeded`、`abandoned`、`unknown + sys.error`，且禁止改写 `succeeded/unknown`；原状态矛盾已消除。“允许继续的终态”集合未定是修订引入的后续接口缺口，另列 R10-02。 |

## 3. 任务 B 结果

1. **条件③三件套：反对宣布闭合。**

   旗舰示例可以闭合：compiler fan-out 产生 activation A，UT 回环退役 A 及子孙，回到 compiler 后重新 fan-out，替代 activation 继承 A 的父 scope，UT/review 两个来源都会重派。

   环被限制在内层作用域时也成立：外层 activation O 下的内层 activation I 回到自己的共同 fan-out，退役 I、生成父为 O 的 I′，内层 join 完成后仍能以 O 参与外层 join。

   但 §4.2.6 没有禁止内层环越过祖先 fan-out。反例：

   `F0 → [L, F1 → (X,Y) → J1] → J0`，其中 J1 的输出是 J0 的右侧来源，Y 的环边回到 F0 之前。该环对 J1 会重新经过 F1，对 J0 会重新经过 F0，因此满足现有“重经该 join 的共同 fan-out”检查并可通过加载。

   运行时，采用环边的 task 属于内层 activation I（`parent=O`），§4.2.4 只退役 I 及其子孙，外层 O 仍保持 open；重新经过 F0 产生的 activation 按字面继承 `I.parent=O`，而不是被实际替代的外层 O 的父 scope。若 O 的 L 来源已经到达，其另一来源永远不会以 O 到达，旧计时器可在替代 cohort 完成前触发 fail_safe。series 未推进，因此条件①/②不生效；O 及祖先均未 superseded，祖先链 CAS 也无法拦截该计时器。

2. **跨 attempt 逐支定态：反对宣布接口闭合。**

   三支状态迁移本身已经与 §5.2 查找矩阵一致：probe 成功保持 `succeeded`，确认未发生或 replay-safe 进入 `abandoned`，不可判定进入 `unknown + sys.error`。

   残余缺口是“仅在允许继续的终态之上方可建立异参新键”没有枚举允许集合。反例：上一 attempt 的 P1 经 probe 确认为 `succeeded`，新 attempt 以同一 `effect_call_id` 调用 P2。由于参数摘要不同，P1/P2 的 idem_key 不同；精确键查找中的“succeeded 直接复用”不能决定 P2 应被执行、拒绝，还是错误复用 P1。若执行 P2，会产生不受同键幂等保护的第二个外部效应；若不执行，也没有规定返回值或 outcome。该行为不是 `[01]` 的 schema 细节，而是副作用恢复策略的关键决策。

## 4. 新 issue 清单表

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| R10-01 | BLOCKER | §4.2.4、§4.2.6、§11.3 | 条件③以“采用环边的 task 所属 activation”为退役根，只级联子孙；但静态规则允许内层环先越过外层共同 fan-out，再依次重经多个嵌套 fan-out。此时真正不可补全的是外层 activation，当前规则却只退役内层 activation，导致外层旧 cohort 和计时器继续存活；替代 cohort 的父继承也会多嵌套一层。祖先链 CAS 无法处理未被标记 superseded 的外层 activation。 | DSL v1 静态拒绝跨 activation 边界的回环：环边回流在重经当前 task 所属 activation 的共同 fan-out 之前，不得先重经任何祖先 activation 的共同 fan-out。§11.3 增加“内层来源回跳到外层 fan-out 之前必须拒绝加载”的嵌套 property；现有旗舰图和留在内层作用域的环继续合法。 |
| R10-02 | MAJOR | §5.2、§11.3 | “允许继续的终态”未定义，导致跨 attempt 旧异参记录定态为 `succeeded` 后，新异参 key 的处理不唯一；不同实现可能重复执行新效应、跨参数复用旧结果或拒绝调用。 | 明确本矩阵中允许建立异参新键的集合及动作。与现有“非决定论异参→新键”决策一致的定案可为：`succeeded`、`abandoned` 允许新键，且旧 `succeeded` 只供旧参数精确键复用、不得跨参数复用；`unknown` 固定 `sys.error` 并禁止新键。将三种状态与异参 claim 的预期动作逐项写入 §11.3。 |
| R10-03 | NIT | §11.3 | 新增测试描述出现 `...无误杀**""**父退役级联...**"model-based`，两个用例之间缺少分隔且 Markdown 强调/引号粘连，影响测试项边界可读性。 | 将两个用例拆成明确的并列项，并补齐引号、空格或分号。 |

## 5. CLARIFY 清单

无。

## 6. 一句话总结

距离 draft freeze 还差：禁止或正确定义跨祖先 fan-out 的环退役根，并枚举跨 attempt `succeeded` 异参新键的唯一处理语义。

上面是Codex的review意见

两份文档已读完。本方第九轮为 NO-GO（1 MAJOR + 1 NIT），本轮逐条核验簇 AD 的合并落文，并以旗舰示例与嵌套+环组合图复演条件③三件套。

---

# 复审报告：00_Framework_HLD_v0.10（Kimi 方）

## 1. 总裁决：**GO**

本方第九轮 2 条全部妥善关闭，且簇 AD 的落文完整覆盖我提出那一面（级联面）；两个仲裁关注点复演后均接受。增量审查未发现新问题——issue 清单自首轮以来首次为空。

## 2. 任务 A：本方第九轮 issue 处置核验

| 编号 | 结论 | 说明 |
|------|------|------|
| M-01 (MAJOR) | 接受关闭 | 簇 AD 将我的两个形态全部落文：①级联面——③改为"沿 parent_activation_id 级联其全部子孙 activation、连带作废各自计时器"（主修法）；②防御面——join 消费/分派/timeout CAS 增加祖先链无 superseded 校验、向 superseded scope 的分派拒绝并审计（我给的"或"项作为双保险一并落入）。两案并落，成本句级，处置超出预期 |
| M-02 (NIT) | 接受关闭 | ③措辞已改"采用该环边的 task 所属 activation 上下文"，归属关系明确 |

簇 AD 合并性质确认：我方级联面（③正文 + 双保险段）、Codex 静态收敛面（§4.2.6 条件（iii)）、CC 父继承提醒（替代 cohort 段）三面各自完整落入 §4.2.4/§4.2.6，无一面被稀释。

## 3. 任务 B：仲裁关注点独立判断

**B-1（条件③三件套）：接受。** 两个场景复演：

- 旗舰示例：ut 在 A1 下采用 ut_fix 环边 → ③同事务退役 A1（无子孙）→ compiler 重跑 build_passed 重新 fan-out 产生替代 cohort A2，继承 A1 的 parent（根）→ join 在 A2 下成组；§4.2.6 条件（iii）静态验证通过（ut_fix→compiler→build_passed 重经共同 fan-out）。无误杀路径。
- 嵌套 fan-out + 环组合图（我第九轮反例）：外层 A1 → 分支 P 内嵌套子 A1'（J1 计时器已武装）→ Q 分支节点采用环边 → ③退役 A1 并级联 A1'、双计时器同事务作废 → J1 迟到 timer 经祖先链 CAS 为 no-op；替代 cohort A2 继承 A1 的 parent_activation_id，嵌套层级不随环轮次增长，A2 下的内层汇合照常以父 scope 参与外层 join。误杀与死 scope 分派两形态均死。

相容性核验：级联只沿子孙方向、不波及兄弟分支的并发同 series activation（独立性保留，latest-wins 依据不受触碰）；①全量退役天然含子孙、无需级联，与③分工清晰；静态收敛只约束 join 来源路径上的环边，非来源路径的环不受限（不误伤）；分支内回环拒绝加载消除了"兄弟来源永不重派"的重建面缺口。闭合。

**B-2（跨 attempt 逐支定态）：接受。** 逐支映射（probe 成功→succeeded 复用 / 未发生或 replay_safe→abandoned / →unknown+sys.error）与本段查找矩阵逐字一致，v0.9"对账清零（退役 abandoned）"的措辞 bug（会把 probe 确认成功的记录改写为 abandoned 导致不可重放效应被重复执行、把 unknown 改写为 abandoned 绕过 fail-closed）已根除；"succeeded/unknown 不得改写为 abandoned"与"异参新键仅立于允许继续的终态之上"给出不变式；与运行时拒绝路径（仅同 attempt 内未决异参拒绝）的 attempt 边界分工保持融贯——跨 attempt 经启动对账后无未决遗留，同 attempt 内未决即作者误用。§11.3 矩阵测试对应。闭合。

## 4. 新 issue 清单

无（首轮以来首次）。回归抽查：§3 术语、§8.3 裁决/防迟到/correction、状态机、publishing 固定映射、§4.5 计时口径等既关闭条目逐处比对，v0.10 新文本未重新打开任何一项。

## 5. CLARIFY 清单

空。

## 6. 一句话总结

可以 freeze——十轮评审的全部关键路径（DSL 静态三层检查、activation 生命周期、效应幂等、审批-发布-裁决全链、特权 IPC）闭合并经反例复演，v0.10 issue，建议以此为 draft freeze 基线进入 01_Contract_Spec 编写。

上面是Kimi的review意见

CodingSystem Framework HLD v0.10 第十轮复审报告（评审员：Claude Code）
1. 总裁决：GO（无 BLOCKER/MAJOR/MINOR；1 条编辑级 NIT 随 GO 列为 freeze 勘误）
条件③三件套经旗舰示例与嵌套组合图复演闭合；跨 attempt 逐支定态修正了 v0.9 的措辞矛盾且与同段规则无冲突；diff 级回归扫描未发现前九轮已关闭问题被重新打开。本方连续第二轮全清。

2. 任务 A：本方第九轮 issue 处置核验
第九轮编号	结论	说明
AA-01 (NIT)	接受关闭	条件③重写时独立的"迟到事件与计时器一律审计化 no-op"短句已并入段末统一表述，重复消除
AA-02 (NIT)	接受关闭	措辞改"采用该环边的 task 所属 activation 上下文"，与传播定义用语一致（与 Kimi M-02 合并落文）
CL-β	接受	替代 cohort 继承被退役者 parent_activation_id 已写入条件③正文（"环不插入额外嵌套层级"一句同时把语义讲透），不再仅留 [01]——本方那一面（父继承落点）完整落入簇 AD 合并文本
（簇 AD 合并落文中本方核验面已确认；Kimi 的级联面与 Codex 的静态收敛面在任务 B1 中一并复演核验。）

3. 任务 B：两个仲裁关注点
B1（条件③三件套）：接受。 两图复演：

旗舰示例——ut_fix 环边回流至 compiler，恰为 pre_final_review 的共同 fan-out，静态收敛条件天然满足；环边采用退役 A1（无子孙，级联平凡），替代 cohort 由 compiler 重新 fan-out 产生、继承根作用域，双分支全部来源分区重派。通过。

嵌套 fan-out + 环组合图——外层 F1(P)→[含内层 F2(C, parent=P) 的分支, 其他分支]→外层 J1；三个关键情形均闭合：(a) 内层环回流至 F2：静态合法（重经 J2 的共同 fan-out F2）；运行时退役 C 并级联其子孙、作废各计时器，替代 cohort C' 继承 C 的父 P，J2 在 C' 下成组后仍以 P scope 分派、外层 J1 照常可组——级联只向下不向上，P 的其他到达不受损，正确；(b) 分支内回环（不返回共同 fan-out）：静态拒绝，封死了 v0.9 条件③的真正残洞——退役正确但替代 cohort 因兄弟来源分区永不重派而自身不可补全；(c) 外层环边退役 P 时内层 C 尚 open：级联同事务退役 C 并作废其计时器（主保险），join 消费/分派/timeout 的祖先链 CAS 与死 scope 分派拒绝作双保险覆盖并发窗口。与同 series 并发 activation 独立性相容（级联仅及被退役者子树，不比较新旧，latest-wins 未复活）；与 join 原子消费相容（单写者事务串行化，祖先链检查内嵌于消费事务）。闭合。

B2（跨 attempt 逐支定态）：接受。 v0.9 "对账清零（退役 abandoned）"括注确与三支对账矛盾——probe 确认成功的记录被改写为 abandoned 会触发保守重做（恰是第六轮反转所禁止的，对可 probe 不可安全重放效应构成重复外部效应），unknown 被改写则绕过 fail-closed。v0.10 逐支定态（成功→succeeded 复用、未发生/replay_safe→abandoned、不可判定→unknown+sys.error）与查找矩阵、记录版本化通则、"succeeded 直接复用"承诺、同 attempt 运行时拒绝规则逐条比对无矛盾；"succeeded/unknown 不得改写"与"异参新键仅立于允许继续的终态之上"两条不变式把边缘排列组合收拢（unknown 路径本身即中止 task，无新键可立，自洽）。§11.3 的定态×异参矩阵测试将其固化。闭合。

4. 新 issue 清单（随 GO 的 freeze 勘误）
编号	等级	定位	问题描述	修改建议
AB-01	NIT	§4.2.6 条件(iii)	括注错位：说明合法情形运行时机制的括注（"环边采用即触发 supersede 条件③级联退役旧 cohort，替代 cohort 由重经 fan-out 的新分派产生并继承父 scope——不依赖 timeout 或预算兜底"）被接在"拒绝加载"之后，且同句出现两次"拒绝加载"，首读易误解为对拒绝情形的解释	将该括注移至"从而重派全部来源分区"之后；句子按"合法条件——机制说明——两类拒绝情形"重新断句
5. CLARIFY 清单
（空）

6. 一句话总结
可以 freeze——条件③三件套与逐支定态均经复演闭合，本方历轮 issue 连续两轮全清，仅余 1 条括注位置的编辑级 NIT 随 freeze 编辑落入；本方维持并重申上轮立场：同意在此版本上进入 P0 draft freeze。

（本轮无新增外部事实断言需核实；历轮 LangGraph 依据不变——Interrupts、1.0 稳定承诺、部署版本兼容性。）

上面是Claude Code的review意见
