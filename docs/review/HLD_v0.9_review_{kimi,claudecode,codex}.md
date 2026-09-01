## 1. 总裁决：NO-GO

存在 1 项 BLOCKER：条件③能退役旧 cohort，但没有保证替代 cohort 能重新获得全部 join 来源，DSL 语义仍未闭合。

## 2. 任务 A 结果表

| 本方第八轮编号 | 接受关闭/不接受 | 不接受的理由与定位 |
|---|---|---|
| R8-01 BLOCKER | 接受关闭 | §4.2.4 已按原建议增加条件③，在环边采用事务内退役旧 activation、作废 timer，并由 CAS 将迟到事件化为 no-op；原“新轮成功后旧 timer 误杀”的反例已消除。条件③对更一般图形的新增缺口另列 R9-01，不重复旧问题。 |
| R8-02 MAJOR | 接受关闭 | §5.2 已明确 `effect_class` 从 `fn` 所属注册效应类型推导，效应能力声明挂在类型上，自由函数不可包装，并纳入 conformance；键计算和三支对账选择已有唯一来源。 |
| R8-03 MAJOR | 接受关闭 | §3、§8.3、§14 R14 已定义 append-only post-close correction、权限与绑定字段、单 Ledger 事务、终态不可变以及 `get_result` 返回 correction 引用；§11.3 也覆盖迟到、重复/并发和查询呈现。 |

## 3. 任务 B 结果

1. **supersede 条件③：反对宣布闭合。**  
   条件③与①/②没有事务竞态：series 推进时①覆盖全部旧 series activation，②仍只是防御性兜底；它也只退役采用环边所属的 activation，没有恢复 same-series latest-wins。原旧 timer 反例确已修复。  
   但 §4.2.6 允许任意“经声明环边回流”作为共同到达性例外，没有要求环目标重新经过产生该 cohort 的共同 fan-out。反例：`F → [X,Y] → J`，X 已在 A0 到达，Y 在自身分支内回环而不返回 F；条件③退役 A0并创建 A1，但 X 不会在 A1 重派，A1 永远缺 X。嵌套场景下，新环 activation 应继承哪个 `parent_activation_id`、如何回到外层 join scope 也未定义。因此目前只是从“旧 timer 误杀”变成了“替代 cohort 无法补全”。

2. **effect_class 与 post-close correction：接受。**  
   `effect_class` 已限定为注册类型化能力句柄的固有属性，并禁止自由函数绕过；correction 已具备 append-only 权威记录、特权写入、证据绑定、终态不可变、查询可见和窗口后持续对账。配合 §7.5 的 Ledger 单写者及 §8.5 RPC，两个接口在 HLD 层已闭合，精确 schema 可进入 01。

## 4. 新 issue 清单表

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| R9-01 | BLOCKER | §4.2.4、§4.2.6、§11.3 | 条件③只证明旧 cohort 不可补全，却未证明新 cohort 可以补全。§4.2.6 的环边例外没有限制回流位置：分支内回环时，旧 activation 已有的兄弟来源被退役，新 activation 又不会重派这些兄弟来源，最终只能超时或耗尽 run budget。嵌套 fan-out 中，环 activation 与被替代 activation 的父 scope 关系也未规定，可能无法重新参与外层 join。 | 对 DSL v1 采用静态收敛方案：环边只有在其后续执行必先重新经过该 join 的共同 fan-out、从而重派全部来源分区时，才可作为条件(iii)例外；其余分支内回环拒绝加载。同步规定替代 cohort 继承被退役 cohort 的 `parent_activation_id`，环 activation 不得插入无法弹出的额外 scope。§11.3 增加“分支内回环被拒”和“嵌套 fan-out 回环后仍能进入外层 join”用例。 |
| R9-02 | MAJOR | §5.2 | 新增 attempt 范围词后仍有直接状态矛盾：前句称跨 attempt 旧在途异参记录“三支对账后退役 abandoned”，后句却规定 probe 成功迁 `succeeded`，无 probe 且不可重放迁 `unknown` 并报 `sys.error`。若按前句实现，已确认成功或不可判定的效应都会被错误改成 abandoned，可能导致重复外部效应或绕过 fail-closed。 | 将“对账清零/统一 abandoned”改成逐支终态：probe 成功→`succeeded`，确认未发生或 replay-safe 退役→`abandoned`，不可判断→`unknown + sys.error`；明确只有允许继续的终态才能建立异参新键，`succeeded` 与 `unknown` 不得改写为 abandoned。补跨 attempt 三种结果与异参新 claim 的矩阵测试。 |

## 5. CLARIFY 清单

无。

## 6. 一句话总结

距离 draft freeze 还差：约束环边必须能够重建完整替代 cohort并定案其父 scope，同时消除跨 attempt 三支对账的状态矛盾。

上面是Codex的review意见

CodingSystem Framework HLD v0.9 第九轮复审报告（评审员：Claude Code）
1. 总裁决：GO（无 BLOCKER/MAJOR/MINOR；2 NIT 随 GO 列为 freeze 勘误，1 CLARIFY）
条件③经本方反例时间线复演通过且优于本方原方案（表态见任务 A）；两处接口定案闭合；diff 级回归扫描未发现前八轮已关闭问题被重新打开。本方历轮 issue 全部清零。

2. 任务 A：本方第八轮 issue 处置核验（含簇 AC 仲裁表态）
第八轮编号	结论	说明
Z-01 (MAJOR)	接受关闭，并接受仲裁选择	对"未取本方超时降级方案"的表态：接受仲裁，且认为仲裁理由成立。复演本方反例：F→[X,Y]→J，Y 走环边（series 不推进）——条件③在生成新环 activation 的同一事务内退役 A1 并作废计时器，误杀在根因处消除；而本方的超时降级只令计时器不误杀，死 cohort（X 的到达 + 永不可能补全的组）每轮迭代累积一个、永久滞留 open，确属治症状不治病。条件③的退役依据（同源单送达下该来源在旧 activation 内可证明不可能到达 → cohort 不可补全）是良定义的单调事实判断，不引入次序比较，R5-01 的跨环不可比依据未被触碰——本方对"任何 latest-wins 变体都危险"的担忧不适用于此。附带确认：本方独有的"§11.3 断言固化误杀"发现已修正（"独立超时"表述从用例行移除，补条件③模型断言）；§4.2.6 条件(iii)括注改为引用条件③、不再依赖 timeout/预算兜底，v0.8 的虚假退役断言消除
Z-02 (NIT)	接受关闭	§5.2 effect_class 由 fn 所属注册效应类型推导、自由函数不可包装、参与 conformance 校验
Z-03 (NIT)	接受关闭	§5.2 两规则补 attempt 范围词：跨 attempt 遗留经启动对账清零；运行时拒绝仅同一 attempt 内（标注"作者误用形态"）——即本方给出的融贯读法落为定案文本
Z-04 (NIT)	接受关闭	§4.2.6 量词修正为"每个来源恰由一个分支到达（来源集在分支间构成划分）"
3. 任务 B：两个仲裁关注点
B1（supersede 条件③）：接受。 逐项相容性核查：(a) 与条件①②互补——③覆盖 series-非推进环，①②覆盖 series 推进，flagship 的 ut_fix 环中③与①同刻触发、无害重叠；(b) 与同 series 并发 activation 独立性相容——③只退役采用环边的 task 所属的那一个 activation，退役依据是不可补全性而非新旧次序，R5-01 的合法并发 A/B 不受触碰；(c) 与 parent activation 关系相容——③只退役环边所属层级的 activation、不及祖先：内层环退役内层 cohort，新环 activation 承接后内层 join 仍以父 scope 分派、外层 join 照常可成组；(d) 边界场景——已消费 activation 上的③触发被 CAS open 校验挡为 no-op；三分支 fan-out 中单支走环边时另两支的已到达随死 cohort 一并废弃，正确（组需全员）。§11.3 的条件③ model-based 断言（旧源已到达、环边采用、新 activation 成功、旧计时器后到 → 无误杀）恰是本方反例的测试化。闭合。

B2（两处接口定案）：接受。 effect_class 推导：锚定在类型化能力句柄的注册效应上（probe/replay_safe 能力声明挂在类型上），自由函数不可包装并入 conformance——与 §5.2 末条效应类别契约形成闭环，业务自有效应经注册类型进入同一纪律。post-close correction：append-only + 原终态不可变 + 与裁决同通道特权 + 单 Ledger 事务（经 control-plane RPC，与 Ledger 单写者一致）+ get_result 在终局摘要外返回有效 correction 引用（调用方可见真实远端状态）+ 窗口内周期 probe、窗口后并入常规对账（监视不终止）——把 R14 残余的"检出后如何留痕与呈现"补成完整闭环，且不引入终态改写这一危险能力。§3/R14/§11.3 三处同步一致。闭合。

4. 新 issue 清单（随 GO 的 freeze 勘误）
编号	等级	定位	问题描述	修改建议
AA-01	NIT	§4.2.4	条件③句后新增的"迟到事件与计时器一律审计化 no-op"与同段既有句"superseded activation 的迟到事件与 timer 一律为审计化 no-op"重复（修订合并残留）	删除条件③后的短句，保留段末统一表述
AA-02	NIT	§4.2.4 条件③	"该边所属的旧 activation"中"所属"措辞不精确——边不属于 activation，采用该边的 task 才携带 activation 上下文	改为"采用该边的 task 所继承的 activation"（与传播定义用语一致）
5. CLARIFY 清单
CL-β：条件③"生成新环 activation 的同一事务"中，新环 activation 的 parent_activation_id 指派未明示——按嵌套语义应与被退役 activation 同父（否则内层环重试后外层 join 无法成组）；该规则已隐含在 [01] 传播细则的职责范围内，建议在 01 编写时显式落一句。
6. 一句话总结
可以 freeze——本轮唯一实质缺口（簇 AC）以优于本方原方案的条件③根治并经反例复演确认，两处接口定案闭合，仅余 2 条编辑级 NIT 与 1 条 [01] 落点提醒，随 freeze 编辑落入即可；本方同意在此版本上进入 P0 draft freeze。

（本轮无新增外部事实断言需核实；历轮 LangGraph 依据不变——Interrupts、1.0 稳定承诺、部署版本兼容性。）

上面是Claude Code的review意见

两份文档已读完。本方第八轮为 GO（2 MINOR + 2 NIT），逐条核验落点；本轮仲裁关注点复演中发现条件③的一个级联缺口，详述如下。

---

# 复审报告：00_Framework_HLD_v0.9（Kimi 方）

## 1. 总裁决：**NO-GO**

本方第八轮 4 条全部妥善关闭，簇 AC 的仲裁选择我接受（见任务 A）。但在复演 B-1 时发现：条件③的退役范围不含子孙 activation——v0.8 刚合法化的嵌套汇合形态下，被退役 activation 的子 activation 的计时器仍可误杀健康 Run，且孤儿子 join完成后会向已死 scope 分派。这恰是本轮声称闭合的机制的同级缺口（与簇 AC 同类、深一层），按"Codex 直接开发"标准必须在 freeze 前补上这一句。

## 2. 任务 A：本方第八轮 issue 处置核验

| 编号 | 结论 说明 |
|------|------|------|
| M-01 | 接受关闭 | 簇 AC 落文（条件③即时退役），§4.2.6 条件（iii）括注与 §11.3 断言同步修正 |
| M-02 | 接受关闭 | §5.2 两处规则补齐 attempt 范围词："跨 attempt 遗留经启动对账清零"、"运行时拒绝仅同一 attempt 内"——我上轮指出的融贯读法即定案文本，字面冲突消除 |
| M-03 | 接受关闭 | §11.3 裁决 E2E 已列全三例（证据缺失拒绝、broker 未静默拒绝、迟到发布检出） |
| M-04 接受关闭 | §8.3/R14：窗口内周期 probe（频次配置）、窗口后并入常规审计对账（监视不终止），M-04 所问的窗口后情形覆盖 |

**对簇 AC 仲裁选择的表态：接受仲裁。** 我第八轮的方案是"显式声明假设"（披露），Codex 的即时退役是修复；披露不消除误杀，即时退役在句级成本下精确消除且退役依据（可证明不可补全性）不触碰废除 latest-wins 的既有依据——仲裁理由成立，方案优于我的。本轮任务 B-1 发现的级联缺口是该方案内部的补全问题，不构成对仲裁选择的否定。

## 3. 任务 B：仲裁关注点独立判断

**B-1（supersede 条件③反对（当前形态未闭合，一处级联缺口）。** 先确认成立部分：我第八轮的反例时间线复演通过——A1 已首达、patchless 环边采用 → 同事务退役 A1 并作废计时器 → 迟到 timer 审计化 no-op，误杀消除；与条件①（series 推进，全量退役含子孙——"旧 series 的全部 open activation"）不重叠不冲突；②为①的兜底标注不变；退役范围精确到"该边所属 activation"，不波及其他分支的并发同 series activation，latest-wins 依据不受触碰。**但**：③的退役不带子孙级。反例场景（v0.8 合法化嵌套汇合后可构造的合法图）：外层 fan-out A1 → 分支 P 内嵌套 fan-out 子 activation A1'（parent_activation_id=A1，内层 join J1 等待中、计时器已武装）→ 另一分支 Q 的节点采用声明环边 → ③退役 A1，**A1' 保持 open** → J1 的某来源任务耗时长于 timeout_min（共同到达性检查保证来源"最终"到达或自退役，但不保证在 timeout 内）→ A1' 超时 handler CAS 校验自身 open ∧ current series 通过 → fail_safe 误杀正在 A2 下健康推进的 Run。同一根因还有第二形态：A1' 成组完成后"以父 activation scope 分派下游"（§4.2.4）——父 scope A1 已 superseded，向 scope 的分派是否被拒/丢弃未规定。①无此问题（全量退役天然含子孙），③独有。修复为句级：③退役沿 parent_activation_id 级联子孙（或 timeout/分派 CAS 校验祖先链未被 supersede），二选一写明。

**B-2（两处接口定案）：接受。** effect_class 推导：注册效应类型承载 probe/replay_safe 能力声明、自由函数不可包装、参与 conformance——与三支对账的能力契约闭环，且与"idem_key 仅框架计算"叠加后 worker 侧的伪造面自供键/自供类）双向封死，无歧义。post-close correction：append-only + 终态不可变 + 绑定原裁决与证据 + 单 Ledger 事务（Ledger 单写者经编排进程事务，与裁决通道同权限，一致）+ get_result 一并返回 correction 引用（§3 终局摘要条目同步）——"终态不改写而事实可见"的语义自洽；窗口语义（内周期、后并入常规对账、监视不终止）回答了我第八轮 M-04。闭合。

## 4. 新 issue 清单

| # | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|------|------|---------|-------------|
| M-01 | MAJOR §4.2.4（supersede 条件③） | 条件③的退役范围不含子孙 activation，两个后果：①反例如上述 B-1——嵌套 fan-out 的子 activation（parent 被③退役）保持 open 且属 current series，其 join timeout CAS 通过，误杀同 Run 在 A2 下的健康执行；②子 join 成组完成后按"以父 activation scope 分派下游"向已 superseded 的父 scope 分派，该分派的处置（拒绝/丢弃/执行后弃）未规定。①无此缺口（"全部 open activation"天然含子孙），③按边归属单个退役、未级联。注：嵌套汇合 + 环的组合是 v0.8 明确合法化的图形态，非边缘滥用 | 二选一并写明：退役沿 parent_activation_id 传递级联子孙 activation（连带作废其计时器）；或 timeout handler 与 join 消费/分派的 CAS 增加"祖先链无 superseded"校验。§11.3 补对应 model-based 断言（父退役、子计时器不误杀） |
| M-02 | NIT | §4.2.4 | 条件③"该边所属的旧 activation"的归属关系未定义——边属于哪个 activation 须经"采用该边的 task 的 activation 上下文"推得，建议写明（与 M-01 修复同处落笔即可） | 措辞改为"采用该环边的 task 所属 activation 上下文（及其子孙，若取级联方案）" |

## 5. CLARIFY清单

空。

## 6. 一句话总结

距 freeze 差一句：条件③补子孙级联（或祖先链 CAS）+ 死 scope 分派处置（M-01），修复后我对 v0.9 其余全部内容（含两处接口定案与簇 AC 仲裁）无异议、可即 GO。

上面是Kimi Code的review意见
