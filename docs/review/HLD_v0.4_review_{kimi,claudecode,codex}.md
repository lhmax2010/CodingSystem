## 1. 总裁决：NO-GO

仍有 4 个 BLOCKER：R3-02 未完整关闭，以及新增 R4-01、R4-02、R4-03。它们分别影响崩溃重放、join 正确性和发布 point-of-no-return。

## 2. 任务 A：处置核验

| 本方第三轮编号 | 结论 | 不接受的理由与定位 |
|---|---|---|
| 重开 I-02 | 接受关闭 | §4.2.6 已对 hard-required 与 threshold 指标来源同时实施支配性及同 series 检查。 |
| 重开 I-05 | 接受关闭 | §4.3.2 已删除“幂等键含 attempt”的残留矛盾；v0.4 新效应模型自身的问题另见 R4-01。 |
| 重开 I-25 | 接受关闭 | §10 已统一为 `docs/review/`。 |
| R2-06 复议 | 接受关闭 | D12 已将 provider 端点身份和信任策略纳入 digest，仅排除凭据值。 |
| R3-01 | 接受关闭 | §3、§8.2、§8.3 已补全 run/gate/decision/ci-plan/series/manifest 绑定、approve CAS 和 broker 二次复核。 |
| R3-02 | **不接受** | §8.3 虽增加原子 `publishing` 迁移，但只称 pending 事件在 broker 完成后“再定终态”，没有规定 released/release_failed 与 pending cancel/fail_safe/series-update 的优先级和最终映射；§4.3.3 还存在可提前 administrative finalize 的冲突，见 R4-03。 |
| R3-03 | 接受关闭 | §4.2.4 已将 candidate、父版本 CAS、结果/artifact、lineage、latest 和授权失效收敛到 task 完成单事务。 |
| R3-04 | 接受关闭 | §4.4 已定义 decision/outbox ID、持久化 inbox、重复投递同结果及 durable dispatch 后确认。 |
| R3-05 | 接受关闭 | 针对原反例的 activation_id、环计数向量、每源一次、原子消费、重复丢弃和超时起算均已补齐；series 推进引出的新缺陷见 R4-02。 |
| R3-06 | 接受关闭 | §8.5、§10、§13 已覆盖双向 IPC、分用户部署资产、特权 launcher 和真实 UID E2E gate。 |
| R3-07 | 接受关闭 | §8.5 已采用 task 绑定 FD、服务端推导归属和 Ledger task 租约校验。 |
| R3-08 | **不接受** | §4.3.1 新增了 `queued`，但 resume 仍画成 `paused(gate) → running`，同时 §4.4 定义 paused 当且仅当尚有 gate 等待。反例：gate 已 resolved、执行槽被其他 Run 占用时，该 Run 既不能保持 paused，也不能进入 running；应明确 `paused → queued → running`。 |
| R3-09 | 接受关闭 | §7.5 已增加 active-upload lease、安全年龄及索引前存在性/digest 复验。 |
| R3-10 | 接受关闭 | §5.1.2 已明确心跳丢失时先清理进程组与登记外部进程，并加入对应故障注入。 |
| R3-11 | 接受关闭 | §8.3 已将 D12 复核移至核销前，并使用专用控制面错误触发 administrative finalize。 |
| R3-12 | 接受关闭 | §12、§13 已明确 P3 完成功能和模拟器集成、P4 模拟联调以及真实端点独立上线 gate。 |

## 3. 任务 B：四个关注点

1. **效应级 idem_key：反对宣布闭合。** 参数摘要解决了 S3/S3′ 误复用，但 §5.2 的 abandoned 协议与同键重放互相冲突，而且“effect_seq 按 task 计数”却不把 task/activation 纳入键，见 R4-01。

2. **授权新鲜度与 publishing：反对宣布闭合。** 核销前的绑定、CAS 和新鲜度复核已经闭合；核销后的普通 cancel/fail_safe 也被 publishing 状态挡住。但 pending 事件的终态优先级未定，D12 administrative finalize 还能绕过 publishing 守卫提前关闭 Run，故完整时序仍未闭合。

3. **join activation：反对宣布 DSL v1 全面闭合。** 同 series 多轮循环的跨轮混组问题已经解决；但 series 推进没有原子废弃旧 activation 及其 timeout，旗舰流水线本身仍可被旧 activation 超时误杀，见 R4-02。

4. **双向 IPC 与部署隔离：接受。** 分 socket、分 UID、peer credential、task 绑定 FD、broker 仅接受编排 UID、特权 launcher、凭据权限和真实 UID E2E gate 已形成可验证的 D8 物理强制链；其余半可信脚本风险仍处于已接受的 D13/N7 边界内。

## 4. 新 issue 清单

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| R4-01 | BLOCKER | §5.2；§4.2.4 | 效应身份和恢复状态机无法唯一实现。`effect_seq` 定义为“同 task”序号，但 idem_key 不含 task_id/activation_id；两个独立送达到同一节点的 task，在相同 loop_round 下调用相同参数效应会同键碰撞。另一方面，重试前把旧非终态记录标为 abandoned，而相同参数的重试仍生成同一键：复用则违反“成功者不复用”，新建则违反键唯一性；`abandoned` 也不在已列状态机中。 | 定义跨 attempt 稳定、跨 task/activation 隔离的 logical effect slot；键至少绑定 task/activation、效应调用位和参数摘要，但仍排除 attempt。补全 succeeded/failed/claimed/running/abandoned 的查找与迁移矩阵：同 slot 同参数 probe 后复用或续跑，不同参数先对账并 supersede 旧记录后创建新键。 |
| R4-02 | BLOCKER | §4.2.4；§6.4；§11.3 | series 推进只撤销审批和授权，没有废弃未完成 join activation 或取消其 timeout。反例：S0 的 `review_static` 先到 join；UT 产生修复并推进 S1，随后 S1 activation 成功完成；S0 activation 仍可能在 360 分钟后超时并把已经成功推进的 Run 路由到 fail_safe。仅在“到达时”丢弃 stale 结果不能阻止已持久化 timer。 | 将旧 series 的 open activation 失效纳入 series 推进同一事务；到达处理和 timeout handler 均以 CAS 校验 activation 仍 open 且属于 current series，obsolete activation 的迟到事件和 timer 必须成为审计化 no-op。增加“旧 activation 已首达后推进 series”的故障用例。 |
| R4-03 | BLOCKER | §4.3.3；§4.3.1；§8.3；D12 | publishing 与 administrative finalize 的优先级矛盾。授权核销后若编排进程以新 execution manifest 重启，§4.3.3 要求停止引擎/worker并直接 `closed(fail_safe)`；但 broker 是独立进程，可能仍在完成远端发布，违反 §8.3“broker 完成或 probe 后才能定终态”。结果可能是 Ledger 已关闭 fail_safe，远端稍后实际发布。 | 明确 `publishing` 是 administrative finalize 的状态级例外：禁止直接关闭，必须先与 broker 对账或 probe 远端结果；结果不可判定时保持 publishing/人工处置状态。随后再按固定表处理 broker outcome 与 pending cancel/fail_safe/series-update。 |
| R4-04 | MAJOR | §4.2.5；§4.4；§8.2 | §4.2.5 明确允许“不位于 release 可达路径”的普通 hitl，但 §4.4 对所有 hitl approve 都要求原子生成授权记录，§8.2 又把唯一审批对象定义为 ReleaseManifest。非发布人工决策没有 ReleasePlan/Manifest，无法按现有协议 approve。 | 在 DSL/Contract 中区分 release approval 与普通 human decision；仅前者要求 ReleaseManifest、签发授权并受 approved→release 约束，后者只提交 decision、gate CAS 和 resume outbox。若不支持普通 hitl，则删除允许它的规则并由校验器拒绝。 |

## 5. CLARIFY 清单

无。

## 6. 一句话总结

距离 draft freeze 还差关闭 4 个 BLOCKER（R3-02、R4-01～R4-03）和 2 个 MAJOR（R3-08、R4-04）。

上面是Codex的review意见

两份文档已读完。上一轮本方（Kimi）已 GO，所列 10 条 MINOR/NIT + 2 条 CLARIFY 作为勘误全采纳；本轮核验其实际落点，并对四个仲裁关注点做独立攻击。

---

# 复审报告：00_Framework_HLD_v0.4（Kimi 方）

## 1. 总裁决：**GO**

本方第三轮 12 条全部妥善关闭且实现质量高于建议原文（task 级 FD 绑定强于作用域声明）；四个仲裁关注点逐一攻击后均接受；增量审查未发现 BLOCKER/MAJOR——publishing 状态机、效应级幂等键、activation 语义、deploy 交付物四组新定义彼此咬合良好，仅余 6 条 MINOR/NIT 级接缝，适合作 freeze 勘误。注意：本轮无新机制、全部为定义补全的声明（§A6）经逐条核对属实。

## 2. 任务 A：本方第三轮 issue 处置核验

| 编号 | 结论 | 说明 |
|------|------|------|
| M-01 | 接受关闭 | §3 Approval 服务行已删"核销"，补"核销唯一归属 broker（§8.3）" |
| M-02 | 接受关闭 | §4.3.1 已补"administrative finalize 路径为显式例外——由 ledger 层直接生成" |
| M-03 | 接受关闭 | §4.2.5 已限定"位于 release 可达路径上的 hitl"，无关 hitl 不受约束 |
| M-04 | 接受关闭 | §4.2.4 末句"普通节点每次边送达独立触发一次 task，需要汇合必须显式 join" |
| M-05 | 接受关闭 | §8.5 task 级 socket FD 绑定 + 连接上下文推导归属 + Ledger 租约校验 + 越域拒绝审计 + §11.3 跨 task 篡改用例——强于原建议 |
| M-06 | 接受关闭 | §8.5 特权 launcher 明确属可信计算基 + deploy/ provisioning 交付 + P4 真实 UID E2E gate |
| M-07 | 接受关闭 | §8.5 出向：broker 发布调度端点仅接受编排进程 UID；§3 token_id 高熵随机 |
| M-08 | 接受关闭 | §4.2.4"tree_digest 由编排层按规范纯算法计算（无需 worktree，算法 [01]）"，"Ledger 计算"措辞已除（§7.6.2 残留一处措辞张力，见新 M-04，NIT） |
| M-09 | 接受关闭 | §8.2"manifest 规范化算法 [01]" |
| M-10 | 接受关闭 | §4.3.1 状态机补 awaiting_patch/queued/publishing，且 awaiting_patch 不占执行队列 |
| CL-1 | 接受关闭 | §7.4 日志摘录按内容升级密级（内联源码行即标 internal_code），与 §7.1 全序自洽 |
| CL-2 | 接受关闭 | §4.2.5"release 的出边不得进入任何环（校验器禁止）" |

前三轮已关闭条目抽查无回归：审批链时序（§8.2 CAS + §4.2.4 series 推进事务撤销待审批项）较 v0.3 进一步增强而非削弱；两处 v0.2 处置表的更正（I-05/I-25 误关重开）核验属实，v0.4 文本确已修复。

## 3. 任务 B：仲裁关注点独立判断

**B-1（效应级 idem_key 闭合性）：接受。** 键结构 hash(run_id, node, loop_round, effect_class, effect_params_digest, effect_seq) 把效应身份锚定在"做什么"而非"第几次做"：决定重放（同参数）命中同一记录实现跳过；LLM 非决定论重执行（patch 内容变 → series/tree_digest 实参变）自然产生新键，v0.3 的"错误复用旧构建产物"反例被结构性消除。崩溃恢复主路径闭合：claimed ack 前置（§5.2）+ 恢复遇 running/claimed 走 probe + 新 attempt 启动前对上一 attempt 非终账标 abandoned。"成功者保留但不复用"是保守取舍（宁可多构建一次，不误信崩溃现场的半成品结论），与 at-least-once 声明一致。唯一残留为 effect_seq"连续"二字的语义缝隙（新 M-03，MINOR）。

**B-2（授权新鲜度 × publishing PONR）：接受。** 攻击面逐一推演均收敛安全侧：①approve 与 series 推进竞态——两者均为编排进程单事务（单写者），CAS（gate waiting + ReleasePlan 当前 + series 最新）必然有一个输；②approve 与核销竞态——同上串行化；③核销后崩溃——publishing 已原子落库，恢复后"已核销给本 task 视为有效"+ broker 远端幂等 probe 收口；④核销后 cancel/fail_safe——仅登记 pending，PONR 不被行政操作击穿；⑤D12 漂移——核销前检测、专用错误码、不烧授权、不伪装 release_failed（），与 §4.2.5 outcome 集的划分一致。绑定六字段（run/gate_instance/decision/ci_plan_task/series/manifest）消灭了跨 gate 实例与跨 ci_plan 重执行的授权复用。唯一未写明的交互是 administrative finalize 与 publishing 的相遇顺序（新 M-01，MINOR）——现有文本组合解读可得安全结论，但应显式化。

**B-3（join activation 语义）：接受。** 针对同 series 多轮循环这一关键场景推演：ut_fix_loop 2 轮环边通过 → 环计数向量变 → compiler 再 fan-out 产生新 activation_id → bench_gate/review_static 在新 activation 下到达、整组原子消费；第 1 轮的迟到到达因键不同被丢弃记审计，跨 activation 混组被"整组消费"禁止；崩溃重放的重复到达命中同键丢弃。超时自首到达起算避免了"join 永远等不到第一个到达时计时器不在走"的悬挂。陈旧 series 到达 + 并行环推进的组合最坏结局是 timeout_min 到期 fail_safe，fail-closed 且有界。闭合。

**B-4（§8.5 双向 IPC + 部署交付兑现 D8）：接受。** FD 注入绑定身份（客户端不得自报）+ 服务端租约校验 + 越域拒绝，使半可信构建脚本（R7 承认在 worker 进程内）即使拿到 worker 通道也被锁在本 task 的数据面命令内；审批/核销 socket 的文件权限隔离 + broker 入站仅编排 UID，把 D8 的"物理强制"从进程隔离落到了 IPC 层； provisioning 与 P4 真实 UID E2E gate 回应了"同用户进程也能通过测试"的批评——部署资产从隐式假设变为交付物。一处构造级加固建议（新 M-02，MINOR）：worker 通道若采用 per-task socketpair 则无监听端点、伪造连接从构造上不可能，建议显式化。

## 4. 新 issue 清单

| # | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|------|------|---------|-------------|
| M-01 | MINOR | §4.3.3 / §8.3 / §4.3.1 | administrative finalize 与 publishing 的相遇顺序未规定：§8.3 的 pending 纪律只枚举"cancel / 并行 fail_safe / series 更新"，不含 administrative finalize；§4.3.3 称 digest 不匹配"同走 administrative finalize"而无 publishing 例外。反例场景：发布在飞 + 进程重启 + manifest 不匹配 → 恢复路径直接 ledger 级收尾，还是等 broker probe 对账后定终态？且 publishing→closed(fail_safe) 的转换必须存在于 [01] 命令/guard 表，否则被自身状态机守卫拒绝 | §8.3 pending 枚举补 administrative finalize（或§4.3.3 补"publishing 状态下先待 probe 对账再收尾"一句）；[01] guard 表覆盖 publishing 源态02 | MINOR | §8.5 | worker socket 对非注入连接的处置未规定：FD 注入绑定身份只覆盖 spawn 时建立的连接；同 OS 用户的恶意进程（半可信构建脚本）向 worker socket 发起新连接时，服务端无连接上下文可推导 task 身份。未写明"拒绝无绑定连接"，实现者可能放行后退回 uid 推导——而并行 task 共享 worker 用户时 uid 推导有歧义 | 定为 per-task socketpair（无文件系统监听端点，伪造连接构造上不可能），或显式规定"仅接受 spawn 注入的预绑定连接，其余拒绝并记审计" |
| M-03 | MINOR | §5.2 | effect_seq 定义为"同 task 内实参完全相同的**连续**调用的单调序"："连续"二字引入缝隙——同一 task 内非连续地用相同实参调用同一 effect_class（A、B、A），第二个 A 的 seq 如何推导未定义；若重放时调用交错序变化（重试路径代码分支不同），键将漂移 | 去掉"连续"依赖：定义 effect_seq 为"同 task 内同 (effect_class, effect_params_digest) 的第 N 次调用"（按调用计数而非相邻性），或显式规定非连续重复调用的 |
| M-04 | NIT | §7.6.2 vs §4.2.4 | 措辞张力：§7.6.2 仍称 tree_digest 为"各仓**应用后** tree hash 的规范组合"，§4.2.4 称"纯算法计算（无需 worktree）"。语义可调和（"应用后"为逻辑定义、纯算法为实现），但字面矛盾 | §7.6.2 补"（逻辑定义；计算为纯算法，见 §4.2.4）" |
| M-05 | NIT | §6.1 | 消息类型清单残留"Approval 决定与 **token**"，与授权记录术语（§3/D8）不一 | 改"Approval 决定与授权记录" |
| M-06 | NIT | §4.3.1 | 状态机 ASCII 图中 publishing 的布局（"closed(fail_safe) / publishing ─▶ closed(...)"）出边指向难读，publishing 的合法边集合（→closed(succeeded)／经 probe 后定终态）需从 §8.3 反推 | 重绘或补一行 publishing 出边说明 |

## 5. CLARIFY 清单

1. §5.2：abandoned 记录与同 idem_key 新记录并存后，查找规则（"忽略 abandoned"）建议明确——同键多记录在 Ledger schema 上如何区分当前有效记录？（可入 01）
2. §4.2.4：activation_id 的生成与持久化时点——fan-out 分派时由编排层生成并随分派事务落 Ledger？恢复重放时 activation_id 的重建来源是 Ledger 记录还是 checkpoint？建议写明一句。

## 6. 一句话总结

可以 freeze——四轮评审的关键（DSL 语义、审批-发布时序、幂等恢复、特权 IPC）现已全部闭合，建议将 M-01～M-06 作为 freeze 勘误随 v0.4 定稿，M-01/M-02/M-03 三条在 01_Contract_Spec 编写时优先落为精确条款。

上面是Kimi Code的review意见

CodingSystem Framework HLD v0.4 第四轮复审报告（评审员：Claude Code）
1. 总裁决：NO-GO（1 项 BLOCKER：join activation 缺"被取代 activation 退役"规则，旗舰示例在自身预算参数下会被误杀；单句级修复。另 1 MAJOR + 2 MINOR）
总体评价：v0.4 对第三轮三方 issue 的处置质量高，本方 T-01（idem_key 效应级锚定）的修复方向正确且反例已消除。NO-GO 的唯一原因是本轮新写的 activation 语义存在一个生命周期缺口——它在旗舰流水线的正常修复循环场景下（该场景正是 §11.3 新增测试类别声称覆盖的对象）会产生虚假 fail_safe。

2. 任务 A：本方第三轮 issue 处置核验
第三轮编号	结论	说明
T-01 (BLOCKER)	接受关闭	§5.2 效应级 idem_key（effect_class + effect_params_digest + effect_seq，实参含 series_id/tree_digest/构建目标/板卡）；本方反例（LLM 非决定论产 S3' 复用 S3 构建产物）在新键下消除；§4.3.2 残留矛盾已清。abandoned 对账机制的一处边缘态歧义为新文本引入的新问题，另立 V-02，不构成重开
T-02 (MINOR)	接受关闭	§8.5 worker 数据面命令显式枚举（side_effect/trace/artifact 索引/series candidate），与 §7.5、§4.2.4 对齐
T-03 (MINOR)	接受关闭	§4.3.3 活跃引擎场景先停引擎、终止在飞 worker、再 ledger 级收尾
T-04 (MINOR)	接受关闭	§8.2 CLI 呈现 manifest + 证据链（ReviewReport、逐段出处 series、各 Report 引用），清单入 01/07
T-05 (NIT)	接受关闭	§10 注释已改 review/
T-06 (NIT)	接受关闭	release 统一称"特权节点"（§4.2.2/§4.2.5）
CL-A	接受	§7.4 日志摘录按内容升级密级
CL-B	接受	归 01 的安排明确（07 引用），处置表已登记
CL-C	接受	deploy/ provisioning 纳入交付 + P4 真实 UID gate
CL-D	接受	§4.2.6 MVP 禁链式 join
3. 任务 B：四个仲裁关注点
B1（效应级 idem_key）：接受，附 1 项需定案的边缘态（V-02）。 核心机制闭合：非决定论重执行实参不同 → 新键，键碰撞反例消除；同参重试命中既有记录 + probe 对账正确。未闭合处：abandoned 记录的命中语义（见 V-02）——两种可选解读均是安全的（重执行 probe 可对账的效应无害），故属歧义而非错误，不推翻接受结论。

B2（授权新鲜度与 point-of-no-return）：接受。 逐项攻击未发现绕过：approve 事务 CAS（gate waiting + plan 当前 + series 最新）与 series 推进事务（撤销待审批项与未核销授权）同经编排进程串行化，两序皆安全；核销原子迁移 publishing 后 cancel/fail_safe/series 更新仅登记 pending，消除"发布中关 Run"竞态；D12 漂移核销前检测、不烧授权（R3-11）与 administrative finalize 的 probe 对账衔接自洽；核销绑定 task_id 保恢复；publishing 期间编排崩溃的两个分支（manifest 匹配→恢复续跑 / 不匹配→admin finalize 先 probe 发布效应再收尾）均有出路。

B3（join activation 语义）：反对。 activation 的组成机制（到达键、每源每 activation 一次、原子整组消费、重复丢弃、禁混组）本身闭合，但缺少被取代 activation 的退役规则，在旗舰示例自身参数下产生虚假 fail_safe——详见 V-01 的具体时间线反例。这是本轮唯一 BLOCKER。

B4（IPC 双向 + FD 绑定 + deploy provisioning）：接受。 task 级 socket FD 注入 + 连接上下文推导归属 + 租约校验消除自报身份伪造面；broker 入站仅编排 UID；deploy/ 将账户/权限/特权 launcher/启动顺序纳入交付物并以 P4 真实 UID E2E 验收，补上了"同用户跑测试即可通过"的空洞。同 UID worker 间经文件系统互扰的残余路径被 blob 索引前 digest 复验封住（内容寻址下篡改必致 digest 不符）。D8 的物理强制声明在单机威胁模型下成立。

4. 新 issue 清单
编号	等级	定位	问题描述	修改建议
V-01	BLOCKER	§4.2.4（v0.4 新增 activation 语义）	被取代 activation 无退役规则，正常循环场景下产生虚假 fail_safe。旗舰示例反例时间线：round 1 中 compiler build_passed(S1) fan-out 生成 A1，review_static(S1) 到达 join（A1 计时自此起算）；ut(S1) 产修复 patch，series 推进 S2 并回流；round 2 fan-out 生成 A2，bench_gate 与 review_static 的 S2 到达按"不得混组"全部计入 A2 并正确触发 review_final。此后 A1 永远无法完备（其 S1 到达已 stale，A2 到达不得混入），但其计时器仍在走——timeout_min: 360 到期即"超时 → fail_safe"，在 round 2 重建（loop 预算允许 180min）+ bench + 多日人工审批（R9 明示、gate TTL 默认无）的正常时序下必然触发，杀掉一个健康甚至已进入审批的 Run。文中无任何 activation 关闭/作废条款	§4.2.4 补 activation 生命周期规则：同一 join 出现更新 activation 的首个到达、或某 activation 组内到达因 series 推进全部转 stale 时，该 activation 标记 superseded 关闭、计时器作废（记审计）；仅当前最新 activation 的超时可路由 fail_safe。§11.3 的"同 series 多轮循环 activation 分组"用例显式加入"stale activation 超时不误杀"断言
V-02	MAJOR	§5.2 vs §4.3.2	abandoned 记录的命中语义未定且两处表述冲突：§4.3.2 称"重试命中同一效应记录"，§5.2 称上一 attempt 非终态记录 probe 对账后标 abandoned 且"成功者保留为已完成但不复用"——同参新调用遇 abandoned-completed 记录时，键已被占用而复用被禁，claim 行为（另取 effect_seq？覆盖？报错？）未定义；且与恢复协议路径"probe 成功→补写完成并复用结果"政策不一致。两种解读均安全（重执行可 probe 效应无害），故为歧义而非错误	定案一句：abandoned 记录不参与命中，同参新调用按 effect_seq 递增取新键；§4.3.2 措辞改为"命中同一记录（干净终态）或经 abandoned 对账后重新执行"；同时定案 un-probe-able 遗留记录在 attempt 启动对账时的处置（建议同恢复协议：unknown → sys.error）
V-03	MINOR	§4.3.1	状态图与文字枚举不一致：文字定案 resume 与新 Run 同入 FIFO（即 paused → 排队 → running），图中画 paused ◀─resume─ 直连 running；publishing 的入边（running 经核销事务迁入）未画；且 queued 的定义句仅锚定"patch 受理"，未覆盖 resume 排队场景	以文为准修图（补 paused→queued 边与 running→publishing 边），queued 定义改为"patch 受理或 resume 后待执行槽"
V-04	MINOR	§4.5/§4.2.4	"wall_clock 排除 paused 时段"语句仅锚定 loop 预算；run_budget 与 join timeout_min 是否排除 paused 未声明。若 run_budget（示例 1440min）含 paused，则 R9 承认的多日审批必然杀掉一切挂审 Run，与 gate TTL 默认无的设计意图矛盾	统一声明：run_budget 与 join timeout_min 的计时口径同 loop wall_clock，排除 paused（及 publishing 等待）时段
5. CLARIFY 清单
CL-i：activation 上下文沿分支的传播规则（中间节点任务继承派发边的 activation、嵌套 fan-out 的环计数向量组合）目前靠推断成立（bench_gate 与 review_static 需共享同一 A2），请在 01 的 activation schema 中显式给出传播定义。
CL-ii：effect_seq 定义中"实参完全相同的连续调用"的"连续"易误读（同参调用被异参调用间隔时序号是否延续），01 定义时建议改为"同参调用的第 k 次"计数语义。
6. 一句话总结
距 draft freeze 差一句 activation 退役规则（V-01，唯一 BLOCKER）+ abandoned 命中语义一句定案（V-02）+ 两处计时/状态图小对齐；V-01/V-02 修入后本方即转 GO，无需再触碰任何架构决策。

（本轮无新增外部事实断言需核实；沿用前三轮已核实的 LangGraph 依据——Interrupts、1.0 稳定承诺、部署版本兼容性。）

上面是Claude Code的review意见
