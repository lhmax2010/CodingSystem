CodingSystem Framework HLD v0.8 第八轮复审报告（评审员：Claude Code）
1. 总裁决：NO-GO（无 BLOCKER；1 项 MAJOR——共同到达性条件(iii)的退役断言在 series-非推进环下不成立，存在虚假 fail_safe 反例，属仲裁关注点 B1 明示要我裁定的边界，我的裁定是"现状不可接受、需一句话级修复"；另 3 NIT。修复即本方 GO）
说明裁决口径:本方七轮以来 GO 的前提始终是"无 MINOR 级以上实质残留"。本轮唯一实质问题恰好落在 B1 明示征询的边界上，且 §11.3 的新增断言（"独立超时"）会把该错误行为固化为预期行为，freeze 前应定案而非登记为勘误。

2. 任务 A：本方第七轮 issue 处置核验
第七轮编号	结论	说明
Y-01 (MINOR)	接受关闭	§4.3.2 悬空 effect_seq 引用改写为"重试以相同 effect_call_id 再调用……按 §5.2 记录版本化重新执行"；§5.2 "记录版本化为通则——凡同键在 abandoned 记录之上的重执行一律版本化承载"，从 replay_safe 分支提升为通则，正是本方建议句
Y-02 (NIT)	接受关闭	效应侧改"按三支对账后退役（abandoned；不与 activation 的 supersede 术语混用）"，术语碰撞消除
（簇 AB 顺带落定的 SDK 签名 side_effect(effect_call_id, params, fn, repeat_seq=None) + "idem_key 只能由框架计算"是强于本方原建议的加固，堵住 worker 自供键的回退路径，认可。）

3. 任务 B：三个仲裁关注点
B1（共同到达性三条件）：部分反对。 接受的部分：多源 join 须由同一显式 fan-out 的不同分支派生（共同支配不得替代）正确封死了 Codex 的互斥 outcome 反例（X→A、Y→B 同 join 静态拒绝）；旗舰示例逐条复核通过（ut_fix 分支走条件三，bench_gate fail 走 default fail_safe 即条件二，无嵌套 fan-out）。反对的部分：条件(iii)括注"该 activation 由 series 推进或环预算耗尽退役"在 series-非推进环下是不成立的断言——反例见 Z-01：环成功收敛（预算未耗尽）且不产新 series 时，旧 activation 两个 supersede 条件均不触发，其计时器最终对健康 Run 触发虚假 fail_safe。这不是"timeout 兜底"（兜底应只延迟），而是误杀。缓解面（缺省 timeout 以 run_budget 为界时误杀与预算同刻）不改变显式设置 timeout_min 时的错误性。修复为一句话级，见 Z-01 建议。

B2（parent activation 分派语义）：接受。 parent_activation_id 持久化 + 内层 join 原子消费后以父 scope 分派，使"先内层汇合再入外层"合法且可成组，保住了 B2 上轮论证依赖的表达力逃逸口；恢复自 Ledger 重建覆盖父子关系；到达键取父 activation 无歧义；series 推进 supersede 对父子 activation 一并生效；effect slot 以 dispatch_id 锚定不受影响；根 activation 充当无上层 fan-out 时的父。方案 b 相对保守拒绝的选择正确。闭合。

B3（三重防迟到 + R14）：接受，且在二选一中明确表态——接受 R14 残余方案，不改禁用 confirm_not_released。 理由：(a) "已离开本机的在途请求无法绝对 fence、git/gerrit 无两阶段提交"是客观事实而非设计取舍，与 D13/N7 的残余登记风格一致；(b) 三重机制把残余窗口收窄到"broker 死亡前已发出且远端尚未可见"这一狭窄场景，且 fencing 标识 + 24h 复查把静默不一致转化为可检出、可归因、不改写终态的告警——工程上正确的失败模式；(c) 替代方案（仅留 keep_unknown）并不换来真正的绝对一致：HTTP 语义下远端无法自证"永不到达"，等待无既定终点，Run 无限滞留 publishing 成为运维债，而操作员做 confirm_not_released 时依据的远端证据与 keep_unknown 最终依赖的是同一份事实。单操作员内网模型下，检出+归因优于无出口。

4. 新 issue 清单
编号	等级	定位	问题描述	修改建议
Z-01	MAJOR	§4.2.6 条件(iii)括注 / §4.2.4 supersede / §11.3	series-非推进环下旧 activation 无退役路径，虚假 fail_safe 反例：fan-out F→[X,Y]→join J，Y 侧经声明环边回流（如 flaky benchmark 重跑环，迭代不产新 series）。轮 1：X 到达 J（activation A1 计时起算），Y 失败走环边 → F 重激活 → A2（同 series）。轮 2 全部到达 A2 成组触发 ✓；但 A1 两个 supersede 条件（series 推进/到达全 stale）均不触发、环预算未耗尽（Y 已成功），保持 open 且属 current series——显式 timeout_min 到期即按"仅 open 且属 current series 的超时可路由 fail_safe"误杀健康 Run。条件(iii)括注的退役断言对此类环不成立；§11.3 新增"同 series 并发多 activation 独立超时"断言会把误杀固化为预期行为	二选一定案（均为句级修改）：a)（推荐）timeout 降级规则——同一 fan-out 节点产生、activation 向量除该环计数分量外完全相同的多个 open activation 中，仅计数最大者的超时可路由 fail_safe，其余超时降级为审计告警（该分量在同环内全序，不触碰 R5-01 的跨环不可比反例）；b) 静态限制：环边回流路径覆盖的 fan-out 所属环，须其每次迭代必然推进 series（无法静态判定则拒绝加载并要求改写），并将 series-非推进环列为不支持形态。同步修正条件(iii)括注与 §11.3 断言措辞
Z-02	NIT	§5.2	SDK 签名定案后 effect_class 的来源未声明：键含 effect_class，但 side_effect(effect_call_id, params, fn, repeat_seq) 不含该参数——应为由 fn 所属注册效应类型推导（probe/replay_safe 能力声明即挂在该类型上），自由函数不可传入	补一句"effect_class 由 fn 所属注册效应类型推导；仅注册效应可包装"，细则入 [01]
Z-03	NIT	§5.2	相邻两句的适用范围未标注，字面互斥："同 call_id 旧在途异参记录在命中前先对账退役"（允许）与"同 call_id 存在未决记录时的异参新 claim 被拒 → sys.invalid_result"（拒绝）。实际由 attempt 启动对账保证一致（跨 attempt 遗留在新 claim 前已清零，运行时拒绝只会命中同 attempt 内的真实误用），但需读者自行推导	两句各加范围词："跨 attempt 遗留（经 attempt 启动对账清零）"与"同一 attempt 内"
Z-04	NIT	§4.2.6	"每分支恰好覆盖一个来源子集"量词错位——任何分支都平凡地覆盖"一个子集"（含空集）；意图应为来源在分支间构成划分	改为"每个来源恰由一个分支到达（来源集在分支间构成划分）"
5. CLARIFY 清单
（空）

6. 一句话总结
距 draft freeze 差 Z-01 一处定案——series-非推进环下旧 activation 的超时误杀（推荐同环序数 timeout 降级规则，句级修改）——外加 3 条 NIT 随编辑落入；Z-01 修入后本方即转 GO，且鉴于其余全部闭合，建议下轮可仅做该点的定点复核而非全文复审。

（本轮无新增外部事实断言需核实；历轮 LangGraph 依据不变——Interrupts、1.0 稳定承诺、部署版本兼容性。）

上面是Claude Code的review意见

## 1. 总裁决：NO-GO

存在 **1 项 BLOCKER、2 项 MAJOR**。共同到达性对“不推进 series 的环回流”仍未闭合，会留下可误杀 Run 的旧 activation。

## 2. 任务 A 结果表

| 本方第七轮编号 | 接受关闭/不接受 | 不接受的理由与定位 |
|---|---|---|
| R6-04 续 MAJOR | 接受关闭 | §8.3 已补 broker 静默 guard、远端 fencing 标识、裁决后复查，并在 §14 R14 明确登记无法绝对 fence 的残余风险。该风险取舍本身接受；迟到检出后的记录修正接口缺口另列 R8-03。 |
| R7-01 BLOCKER | 接受关闭 | §4.2.6 已要求共同显式 fan-out，并逐 outcome 检查可达来源、Run 终局或声明环边；原“互斥 outcome 分别到 A/B”反例会被拒绝。环边例外自身的新生命周期问题另列 R8-01。 |
| R7-02 MAJOR | 接受关闭 | §4.2.4/§4.2.6 已持久化 `parent_activation_id`，并规定内层 join 原子消费后以父 scope 分派；原嵌套汇合后无法参与外层 join 的问题已解决。 |
| R7-03 MAJOR | 接受关闭 | §4.3.2 已清除当前语义中的 `effect_seq`；§5.2 改为调用方提供 `effect_call_id` 和结构化参数、框架独占 idem_key 计算，并将 abandoned 后同键重执行统一版本化。新签名缺少 `effect_class` 来源是新增接口缺陷，见 R8-02。 |

## 3. 任务 B 结果

1. **共同到达性三条件：反对。**  
   共同 fan-out 和 outcome 检查修复了互斥分支，但环边例外不充分。若分支经声明环边回流且不推进 series，旧 activation 不满足 §4.2.4 的两个 supersede 条件，仍保持 open；新 activation 即使成功汇合，旧 timer 之后仍可路由 fail_safe。把 timeout 当作旧 cohort 的正常退役会使成功与否依赖执行时长，而不是图语义，见 R8-01。

2. **parent activation 分派语义：接受。**  
   父关系持久化于 Ledger，恢复不依赖内存栈；内层 join 的整组消费和下游触发本就原子，新增“以父 scope 分派”明确了单层 pop。多层嵌套可沿持久化父链逐层恢复，series 推进时父子 open activation 又会在同一事务统一 supersede。

3. **confirm_not_released：接受 R14 残余方案，不主张禁用。**  
   broker 静默先排除本地在途执行，fencing 标识支持迟到归因，复查窗口负责检测和告警；该命令又仅由特权操作员在强制 probe 仍 unknown 时使用。更重要的是，迟到对象仍受原授权和 manifest 绑定，不构成审批绕过。因此在本文单机、单操作员信任模型下，显式登记 R14 比永久禁用运维出口更合适。迟到检出后的权威记录呈现仍需补全，见 R8-03。

## 4. 新 issue 清单表

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| R8-01 | BLOCKER | §4.2.4、§4.2.6、§4.5、§11.3 | 环边回流条件会留下无法完成的旧 activation。反例：fan-out 生成 A0，左分支已到达 join，右分支不改 series 而经声明环边重试；A0 不会被 supersede。新一轮 A1 后续成功汇合并继续运行时，A0 仍为 current+open，其 timeout 可按 §4.2.4 将整个 Run 路由 fail_safe。环预算只有在耗尽时关闭 Run，不能处理“重试成功但旧 timer 后到”的路径。 | 定案旧 cohort 的即时退役：声明环边被采用时，在生成新环 activation 的同一事务中，将该边所属旧 activation 标为专用 retired/abandoned 状态并作废 join timer，迟到事件审计化 no-op；这只退役已确定无法完成的 cohort，不恢复 latest-wins。或者静态禁止不保证 series 推进的环边作为共同到达例外。§11.3 增加“不推进 series、旧源已到达、新 activation 成功、旧 timer 后到”的模型测试。 |
| R8-02 | MAJOR | §5.2 | 已定案 SDK 签名为 `side_effect(effect_call_id, params, fn, repeat_seq=None)`，但 idem_key 还包含 `effect_class`，三支对账能力也按效应类别选择；正文没有说明 `effect_class` 从哪个参数、注册表或能力句柄推导。Codex 无法唯一实现键计算、probe 选择和 replay_safe 校验。 | 明确定案一种来源：将 effect_class 纳入 SDK contract，或规定 `side_effect` 只能由已注册的类型化能力句柄调用并从该句柄推导固定 effect_class；同时明确该值参与 manifest/conformance 校验。 |
| R8-03 | MAJOR | §3 Run 终局摘要、§6.5、§8.3、§14 R14 | 迟到发布检出后规定“不改写已关闭终态，人工按 R14 修正”，但未定义修正什么记录、使用什么命令和 guard，以及 `get_result` 如何呈现新的远端事实。原 Run 终局摘要是关闭时生成的不可变 artifact；若只补审计事件，调用方仍可能长期看到 `closed(fail_safe/cancelled)` 而不知道实际已发布。 | 定义 append-only 的 post-close reconciliation/correction 记录及特权命令：绑定原裁决、远端对象、证据、操作者和处理状态；保持原终态不可变，但要求 `get_result` 同时返回有效远端发布状态或 correction 引用。§11.3 覆盖迟到检出、重复修正、并发修正及查询呈现。 |

## 5. CLARIFY 清单

无。

## 6. 一句话总结

距离 draft freeze 还差旧 activation 在无 series 环回流时的确定性退役，以及 `effect_class` 来源和迟到发布修正记录两项接口定案。

上面是Codex的review意见

两份文档已读完。本方第七轮为 GO（1 MINOR + 1 NIT + 1 CLARIFY），先核验处置落点，再对三个仲裁关注点逐一复演。

---

# 复审报告：00_Framework_HLD_v0.8（Kimi 方）

## 1. 总裁决：**GO**

本方第七轮 3 条全部妥善关闭；三个仲裁关注点逐一攻击后均接受（B-3 按要求给出二选一立场）。增量审查未发现 BLOCKER，残留 2 条 MINOR + 2 条 NIT 作 freeze 勘误。

## 2. 任务 A：本方第七轮 issue 处置核验

| 编号 | 结论 | 说明 |
|------||------|
| M-01 | 接受关闭 | 簇 AB 落文超出原建议：§4.3.2 悬空引用改写（"重试以相同 effect_call_id 再调用……按 §5.2 记录版本化重新执行"，effect_seq 全文肃清）；SDK 签名定案 `side_effect(effect_call_id, params, fn, repeat_seq=None)` 且 idem_key 仅框架计算（堵住 worker 自供键的回退路径）；记录版本化提升为通则；"退役（abandoned）"与 activation 的 supersede 术语分离 |
| M-02 | 接受关闭 | §3 已补 dispatch_id / activation / effect_call_id 三条术语，effect_call 标注"业务开发者 contract 面向概念" |
| CL-1 | 接受关闭 | §5.2 唯一性两层面定案：conformance 静态检查（每逻辑调用点唯一命名）+ 运行时拒绝路径（同 call_id 未决记录上的异参新 claim → sys.invalid_result）——正面回答了我问的"违例形态与 outcome 归类"。但运行时拒绝与同段的命中前对账退役存在字面张力，见新 M-02（MINOR） |

## 3. 任务 B：仲裁关注点独立判断

**B-1（共同到达性三条件）：接受，附一条边界勘误（新 M-01，MINOR）。** 充分性：互斥 outcome 反例（X→A、Y→B 汇入同一 join，任一分支触发必致另一来源缺席）被三条件静态拒绝，正确。不误伤验证——旗舰示例逐条复：ut 的三分支分别命中条件 a（ut_passed→benchmark 在 bench_gate 路径上）、c（ut_fix_patch_ready 经声明环边回流）、b（其余走 default fail_safe）；compiler 与 benchmark 同理；通过。条件 c 的边界问题（任务点名处）：环迭代不推进 series 时，旧 activation 不触发 supersede 条件①，存活至 timeout——若 timeout_min < 剩余运行时长，超时将误杀健康 Run（false fail_safe）。文档已以括注"（该 activation 由 series 推进或环预算耗尽退役）"诚实披露该边界；内置环路由（ut_fix/build fix）均携带 patch → 推进 series → 实际不触发；仅无 patch 重试环"（DSL 未禁止、 flaky-test 重跑类场景可构造）落入此角。失败模式为保守终止且有完整证据，可接受为 MVP 水位，但该假设应显式化（M-01）。

**B-2（parent activation 分派语义）：接受。** 嵌套场景复演：外层 fan-out → 分支 A 内嵌套 fan-out（子 activation，parent_activation_id 指向外层）→ 内层 join 在子 scope 成组原子消费 → 下游以父 scope 分派 → 与分支 B 层 join 成组——到达键（join, activation, source）在两层各自无歧义，跨层不混组。恢复路径闭合：parent_activation_id 随 activation 记录持久化落 Ledger，恢复自 Ledger 重建（与 v0.7 的 dispatch 记录复用声明一致）。与既有规则无冲突：链式 join 禁令只禁 to 直连 join，内层 join→中间节点→外层 join 仍合法；同源多次送达拒绝规则兜住分支汇合后再分裂的歧义形态。闭合。

**B-3（confirm_not_released 三重防迟到 + R14）：接受 R14 残余，明确反对禁用 confirm_not_released。** 二选一理由：①替代方案买不到绝对一致——git/gerrit 无两阶段提交，已离机的在途请求物理上不可撤，这是客观边界；禁用 confirm_not_released 只是把风险换成"Run 永远滞留 publishing"，且远端不存在"超时自明"机制（在途请求要么落地要么不落地，无限等待同样到不了零概率），结果是牺牲唯一运维出口换取概率上的边际改善，与 R13 的设立目的自相矛盾。②三重机制把残余压到可运维水位：本地在途归零（broker 静默 guard）→ 迟到事件可归因（fencing 标识定位到 run_id+token_id）→ 可检出（复查窗口重 probe）→ 检出后告警+审计补记、不静默不改写终态。检测+归因+显式残余登记，与 D13/N7 的残余处理风格一致。③残余的实际危害面窄：迟到发布落地而 Run 标记失败——可发现、可归因、可修正，且无凭据扩散（凭据仍在 broker）。一处窗口语义细节见 M-04（NIT）。

## 4. 新 issue 清单

| # | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|------|------|---------|-------------|
| M-01 | MINOR | §4.2.6 / §4.5 | 条件 c（环边回流）隐含"环迭代推进 series"的假设未声明：patchless 环迭代（DSL 未禁止，如 flaky 重跑环）不触发 supersede ①，旧 activation 带活计时器存活；若 timeout_min 小于剩余运行时长，超时 handler CAS 通过（仍 open 且属 current series）→ 误杀健康 Run。反例A1 已首达（review_static 到达）→ ut 走无 patch 环边回流 → A2 完成 join、流水线推进至 release → A1 计时器到期 → fail_safe | §4.2.6 条件 c 处显式声明：经环边回流的分支须推进 series，否则旧 activation 依赖 timeout 退役、存在保守误杀（或规定环激活对同环旧 activation 的退役规则——环内计数有全序，不违背废除 latest-wins 的依据） |
| M-02 | MINOR | §5.2 | 同段两处规则字面冲突： 二称"同 call_id 的旧在途异参记录在命中前先按三支对账后退役"（对账退役→放行新 claim），bullet 末又称"同 call_id 存在未决（claimed/running）记录时的异参新 claim 被拒，task 报 sys.invalid_result"。二者覆盖同一事件（存在未决同 call_id 记录时的异参 claim）给出相反结果；融贯读法需以 attempt 边界区分（跨 attempt=attempt 启动前已对账退役；同 attempt 内=拒绝），但该区分未写明，ex 实现 claim 路径时两可 | 写明区分：attempt 启动前的逐条对账使跨 attempt 不存在未决遗留；运行时拒绝仅适用同 attempt 内的未决异参 claim（作者 bug 形态）；据此改写互引两句 |
| M-03 | NIT | §11.3 vs §8.3 | §8.3 承诺三个人工裁决 E2E 用例（证据缺失拒绝、**broker 未静默拒绝**、**迟到发布检出**），§11.3 只落了"证据缺失拒绝"一个，后两个在测试清单中缺席 | §11.3 补齐两条用例名 |
| M-04 | NIT | §8.3 / R14 | 复查窗口语义未明："按配置窗口（默认 24h）自动重 probe"——窗口内单次周期性 probe？窗口关闭后是否完全停止监视（迟到发布晚于窗口则永不检出）？R14 的检测信号句同样未覆盖窗口后情形 | 写明窗口内 probe 频次与窗口后策略（建议：窗口内周期，窗口后并入常规审计对账或显式声明监视终止） |

## 5. CLARIFY 清单

空。

## 6. 一句话总结

可以 freeze——八轮评审后 DSL 静态检查体系（作用域/到达性/嵌套三层）、效应幂等、发布 PONR 与人工裁决全部闭合，建议将 M-01～M-04 作为 freeze 勘误随 v0.8 定稿（M-01/M-02 优先落入 01 编写）。

上面是Kimi Code的review意见
