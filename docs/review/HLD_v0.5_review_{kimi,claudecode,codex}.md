两份文档已读完。本方第四轮已 GO，所列 6 条 MINOR/NIT + 2 条 CLARIFY 均作为勘误采纳；本轮核验落点并复演三个仲裁关注点的反例时间线。

---

# 复审报告：00_Framework_HLD_v0.5（Kimi 方）

## 1. 总裁决：**GO**

本方第四轮 8 条全部妥善关闭；三个仲裁关注点逐一复演反例后均接受。增量审查未发现 BLOCKER/MAJOR——activation 退役、effect slot、publishing 终态映射三组补全与既有机制咬合，无回归。残留 2 条 MINOR + 3 条 NIT，适合作 freeze 勘误随 01 编写落掉。

## 2. 任务 A：本方第四轮 issue 处置核验

| 编号 | 结论 | 说明 |
|------|------|------|
| M-01 | 接受关闭 | 簇 W 落文质量高于原建议：§8.3 pending 枚举补 administrative finalize、publishing 为状态级例外（先对账/probe、不可判定保持待人工）、固定终态映射表——我方 MINOR 与他方 BLOCKER 同洞，处置彻底 |
| M-02 | 接受关闭 | §8.5 per-task socketpair 定案："无文件系统监听端点，伪造连接构造上不可能"——正是建议的最强形态 |
| M-03 | 接受关闭 | §5.2 effect_seq 改按计数，"非相邻性——同参调用被异参调用间隔时序号照常延续"，"连续"缝隙消除 |
| M-04 | 接受关闭 | §7.6.2 补"（逻辑定义；计算为纯算法、无需 worktree，见 §4.2.4）"衔接句 |
| M-05 | 接受关闭 | §6.1 改 决定与授权记录" |
| M-06 | 接受关闭 | 簇 X：状态图重绘（publishing 入出边显式）+ paused→queued→running 定案 |
| CL-1 | 接受关闭 | §5.2 查找矩阵：abandoned 不参与命中、同参新调用递增新键；矩阵细则 [01] |
| CL-2 | 接受关闭 | §4.2.4 activation 于分派事务内生成落 Ledger、恢复自 Ledger 重建、传播定义 [01] |

前四轮已关闭条目抽查无回归：审批链 CAS、能力句柄排除发布、join 触发机制、数据边界来源标注等关键文本逐处比对均未松动。

## 3. 任务 B：仲裁关注点独立判断

**B-1（activation 退役规则）：接受。** 按第四轮反例时间线复演：round 1 的 join activation A1 首达、计时器 T1 启动 → ut_fix 环推进 series（单事务）→ 同事务内 A1 标 superseded、T1 作废 → 多日人工审批期间 T1 即便在内存中残留 CAS 校验 A1 非 open → 审计化 no-op，不误杀健康 Run。关键点验证：①作废与 series 推进同事务（§4.2.4），不存在"推进已提交而作废未提交"的窗口；②崩溃恢复自 Ledger 重建 activation（不重新生成），排除"恢复制造幽灵新 activation 顶替健康旧 activation"的路径；③"仅当前最新 open activation 超时可 fail_safe"+ CAS 双保险，迟到 timer 与迟到到达均为 no-op；④计时口径排除 paused/publishing（§4.5），多日审批不烧 join 预算——CC V-04 反例同时闭合。规则集闭合。

**B-2（effect slot + 查找矩阵）：接受。** 跨 task 碰撞复演：同 activation 下非 join 汇聚产生的同节点双 task 共享 slot，但当且仅当实参完全一致时键才相同——此时两者本就是同一逻辑效应，复用/去重语义正确；实参不同则键不同，天然隔离。跨 attempt 路径：attempt 启动前对账上一 attempt 非终态记录（未发生→abandoned、已成功→succeeded-abandoned 保守重做、不可判定→unknown→sys.error），abandoned 不参与命中、同参新调用递增新键——状态机每条边都有归属，无"记录悬空"形态。loop_round 去列并由 activation 环计数，消除双源。闭合。一处措辞级瑕疵见 M-03（NIT）。

**B-3（publishing 终态映射）：接受。** 残余竞态扫描：①publishing 中进程重启 + manifest 匹配 → 恢复后按"已核销给本 task 有效"+ broker probe 收口；②重启 + manifest 漂移 → administrative finalize 被状态级例外拦住，先对账、不可判定保持 publishing 待人工——发布事实不被行政收尾篡改；③released × pending cancel → closed(succeeded)，pending审计——"不可撤消的已发布"处理正确；④release_failed × pending 的优先序（cancel > fail_safe > 正常路由）固定无歧义；⑤run_budget/join 计时排除 publishing 等待，挂审不烧预算。映射表闭合。一处运维面缺口（publishing 滞留无检测信号）记 M-02（MINOR）；一处状态机文字矛盾记 M-01（MINOR）。

## 4. 新 issue 清单

| # | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|------|------|---------|-------------|
| M-01 | MINOR | §4.3.1 vs §8.3 | publishing 出边表述矛盾：§4.3.1 称"publishing 出边仅 broker 完成或 probe 对账后按 §8.3 终态映射**关闭**"，但 §8.3 映射表中 release_failed（无 pending 时）"按 release_failed 正常路由"——走路由即需执行 fail_safe 保留节点生成 FeedbackReport，这要求 publishing→running→fail_safe→closed 的转换，而状态图与文字均未给 publishing→running 出边。实现者无法判断 FeedbackReport 是经保留节点生成还是并入 publishing 收尾事务 | 一并写明：补 publishing→running（仅终局处理）转换；或规定 release_failed 路由的 fail_safe 处理在 publishing 收尾事务内由 ledger 层生成 FeedbackReport（与 administrative finalize 同例） |
| M-02 | MINOR | §8.3 / §14 | publishing 滞留无检测约定：broker 挂起或对账不可判定时 Run 保持 publishing"待人工处置"，但无超时、无告警、§14 无对应风险条目——人工发现依赖巧合，且 §4.5 已豁免 publishing 计时，run_budget 不会兜底 | §14 R13：publishing 滞留超阈值告警（检测信号：publishing 时长）；或 §8.3 补滞留告警约定 |
| M-03 | NIT | §5.2 | 状态全集枚举为五态（claimed/running/succeeded/failed/abandoned），同段内文却使用第六标签"succeeded-abandoned"——"全集"声明被自身打破 | 明确 succeeded-abandoned 为 succeeded ∧ abandoned 的标志组合而非第六态，或将全集改为六态 |
| M-04 | NIT | §8.2 vs §4.4 | §4.4 已将 hitl 分两型（plain-decision 不生成 manifest 与授权），§8.2 的 approve 原子提交描述（"审批决定 + Ledger 授权记录 + gate outcome CAS + resume outbox"）未限定仅适用 release-approval 型，字面覆盖 plain 型则矛盾 | §8.2 该句补"（release-approval 型；plain-decision 型无授权记录项，见 §4.4）" |
| M-05 | NIT | §8.3 vs §4.3.1 | released→closed(succeeded) 的括注"pending cancel/fail_safe 记入审计与 FeedbackReport"与 §4.3.1"FeedbackReport 在 reason=fail_safe 时生成"冲突——succeeded 路径不应产 FeedbackReport | 改"记入审计与终局摘要"，或明确成功路径的该文档不叫 FeedbackReport |

## 5. CLARIFY 清单

1. §5.2："同参新调用按 effect_seq 递增取新键"——递增由谁分配？若为层（Ledger 侧）分配则并发 task 同 slot 的键稳定性有保证；若为 worker 本地计数，跨 attempt 与同 slot 并发场景的推导规则需写明。建议入 01 时明确分配点。

## 6. 一句话总结

可以 freeze——三个仲裁关注点全部闭合、本方四轮累计条目无一遗留，建议将 M-01～M-05 作为 freeze 勘误随 v0.5 定稿（M-01 优先，涉及 publishing 状态机文字与 [01] guard 表的对）。

上面是Kimi Code的review意见

CodingSystem Framework HLD v0.5 第五轮复审报告（评审员：Claude Code）
1. 总裁决：GO（无 BLOCKER/MAJOR；1 MINOR + 2 NIT 随 GO 列为 freeze 勘误，不阻塞）
本方第四轮全部 issue 已按建议或更强方案落文；三个仲裁关注点经独立复演（含本方 v0.4 反例时间线重放）均确认闭合。v0.5 的修改是上轮已裁定方案的忠实落文，未发现新机制性缺口，也未发现对前四轮已关闭问题的回归。

2. 任务 A：本方第四轮 issue 处置核验
第四轮编号	结论	说明
V-01 (BLOCKER)	接受关闭	§4.2.4 activation 生命周期完整落文：series 推进同事务作废旧 open activation 及计时器、superseded 三触发条件、到达/timeout handler CAS 校验 open+current、obsolete 事件与 timer 审计化 no-op、仅最新 open activation 超时可 fail_safe、生成/持久化/恢复重建时点；§11.3 补"stale activation 超时不误杀"断言。反例复演见任务 B1——通过
V-02 (MAJOR)	接受关闭	§5.2 记录状态全集（含 abandoned）+ 查找矩阵：abandoned 不参与命中、同参新调用按 effect_seq 递增取新键、un-probe-able → unknown → sys.error；§4.3.2 措辞同步为"命中同一记录（干净终态/在途）或经 abandoned 对账后按新 effect_seq 重新执行"——两处冲突消除
V-03 (MINOR)	接受关闭	§4.3.1 状态图重绘：resume 定案 paused→queued→running，queued 定义覆盖 resume 场景，publishing 入出边显式
V-04 (MINOR)	接受关闭	§4.5 定案 run_budget 与 join timeout_min 计时口径同 loop wall_clock，排除 paused 与 publishing 时段，§4.2.4 同步引用
CL-i	接受	§4.2.4 补传播定义句（中间节点继承派发边的 activation 上下文），细则 [01]
CL-ii	接受	§5.2 effect_seq 改为"同 (effect_class, effect_params_digest) 的第 k 次调用（按计数，非相邻性）"，歧义消除
3. 任务 B：三个仲裁关注点
B1（activation 退役规则）：接受。 以本方第四轮反例时间线复演：round 1 中 A1 因 review_static(S1) 首达开始计时；ut 修复导致 series 推进 S2 时，同一事务将 A1 标记 superseded 并作废计时器；round 2 的 A2 正常成组触发 review_final；此后无论 round 2 重建耗时多长、审批挂起多少天（计时口径已排除 paused），A1 的迟到 timer 均被 CAS 校验（open+current）拦截为审计化 no-op——虚假 fail_safe 消除。边界再攻击：同 series 重复激活由"更新 activation 首达"触发退役覆盖；supersede 与 join 原子消费的并发经 Ledger 事务串行化，两序均安全（消费先行则下游按既有陈旧性链兜底）；崩溃后 activation 与计时器自 Ledger 重建，handler 幂等。闭合。

B2（logical effect slot）：接受，附 1 项 MINOR（W-01）。 slot =（run, node, activation_id）使同节点多次边送达的 task 天然隔离（跨 task 碰撞消除），loop_round 由环计数向量蕴含；effect_seq 计数语义与 abandoned 查找矩阵将上轮全部边缘态收拢为确定规则，且与 probe 恢复协议相容（非 abandoned 记录 probe 续跑/复用，abandoned 换新键保守重做）。唯一残留：activation 的生成事件仅列 fan-out/环激活两种，entry 初始分派未列——在 compiler_bench_only 子集（全程无 fan-out）下按字面无任何 activation 存在，effect slot 无从构成；而 §5.2 又断言"独立 task 各有 activation 上下文"。属枚举遗漏而非设计缺口（自然补全唯一：run 启动/entry 分派事务生成根 activation，线性边继承），定为 MINOR。

B3（publishing 终态映射）：接受。 publishing 作为 administrative finalize 的状态级例外（先 broker 对账/probe 远端、不可判定保持 publishing 待人工）消除了"版本漂移收尾丢弃已完成发布"的竞态；固定映射表（broker outcome 优先：released→closed(succeeded) 且 pending 仅记审计；release_failed→依次 cancel/fail_safe/正常路由）使 pending 次序确定；核销绑定 task_id 保恢复。残余仅两处措辞/工具级事项（W-02、CL-ii'），不构成竞态。

4. 新 issue 清单（随 GO 的 freeze 勘误，不阻塞）
编号	等级	定位	问题描述	修改建议
W-01	MINOR	§4.2.4 vs §5.2	activation 生成事件仅枚举"fan-out / 环激活"，entry 初始分派缺失：compiler_bench_only 子集全程无 fan-out，按字面无任何 activation，而 §5.2 的 effect slot 以 activation_id 为必要分量且断言"各 task 均有 activation 上下文"——枚举遗漏使子集示例的 idem_key 字面上不可构成	§4.2.4 生命周期句补"Run 启动的 entry 分派事务生成根 activation"，线性边继承规则已有（传播定义 [01] 同步覆盖根 activation）
W-02	NIT	§8.3	released → closed(succeeded) 分支称 pending cancel/fail_safe "记入审计与 FeedbackReport"，但 §4.3.1 定义 FeedbackReport 仅在 reason=fail_safe 时生成——succeeded 终态引用 FeedbackReport 属术语误用	改为"记入审计与 Run 最终报告"（或在 01 中为 succeeded-with-pending 定义报告载体）
W-03	NIT	§4.3.1	状态图缺 running → closed(succeeded) 直达边（terminal: true 节点成功的非发布子集路径，如 compiler_bench_only），文字枚举正确、图不完整	图中补该边，标注"terminal success_on"
5. CLARIFY 清单
CL-a：plain-decision 型 hitl（§4.4）的 Review CLI 呈现内容未如 release-approval 型那样声明（§8.2 仅覆盖后者）——建议 01/07 的证据链清单显式覆盖 plain 型（该 gate 上游 Report 与决策上下文）。
CL-b：publishing "不可判定保持待人工处置"的人工操作入口（运维 CLI 的对账/裁决命令）建议在 09 运维章节登记为交付项，与 cancel 的运维入口并列。
6. 一句话总结
可以 freeze——三个仲裁关注点全部闭合、本方历轮 issue 清零，仅剩 1 MINOR + 2 NIT 措辞级勘误与 2 条 CLARIFY，建议随 freeze 编辑一并落入，不需要再走一轮完整复审。

（本轮无新增外部事实断言需核实；历轮 LangGraph 依据不变——Interrupts、1.0 稳定承诺、部署版本兼容性。）

上面是Claude Code的review意见

## 1. 总裁决

**NO-GO。**仍有 **4 项 BLOCKER**、**1 项 MAJOR**、**1 项 MINOR**；effect 身份、同 series activation 并发语义及 publishing 终态仍未闭合。

## 2. 任务 A 结果表

| 本方第四轮编号 | 接受关闭/不接受 | 不接受的理由与定位 |
|---|---|---|
| 重开 R3-02 | 接受关闭 | §8.3 已明确 broker outcome 优先，以及 pending cancel → fail_safe 的处理次序，原“pending 优先级未定”问题已解决。 |
| 重开 R3-08 | 接受关闭 | §4.3.1 已定案 `paused → queued → running`，并明确 queued 同时覆盖首次调度与 gate resume，执行槽等待状态闭合。 |
| R4-01 BLOCKER | **不接受** | §5.2 所称“跨 task 隔离”不成立：§4.2.4 的 `activation_id` 是一次 fan-out/环的共享关联标识，兄弟分支继承同一值；若两条边送达同一普通节点，会产生两个独立 task，却落入相同 `(run,node,activation_id)` slot。entry 至首次 fan-out 前的 task 也没有定义 activation_id。此外，probe 已确认成功的记录被标为 `succeeded-abandoned` 后“不复用、重做”，会对“可 probe 但不可安全重放”的效应造成重复执行。 |
| R4-02 BLOCKER | 接受关闭 | §4.2.4 已把旧 series open activation 的 supersede、timer 作废及 handler 的 `open + current` CAS 放入明确事务边界，原“陈旧 timer 误杀健康 Run”反例已消除。 |
| R4-03 BLOCKER | 接受关闭 | §8.3 已明确 publishing 是 administrative finalize 的状态级例外：必须先 broker/probe 对账，不可判定则保持 publishing，原“发布仍在进行但 Run 被提前关闭”的竞态已消除。终态映射的新缺口另列 R5-02/R5-03。 |
| R4-04 MAJOR | **不接受** | §4.4 第242条规定 plain-decision hitl“不生成授权”，但第243条仍无条件写成原子提交“决定 + 授权记录 + gate outcome CAS + resume outbox”。实现者无法判断 plain-decision 命令是否包含授权写入，原歧义仍在。 |

## 3. 任务 B 结果

1. **activation 生命周期：反对宣布整体闭合。**  
   第四轮指定反例可以通过：round 1 activation 首达并启动 timer；series 推进事务将其 superseded 并作废 timer；迟到 timeout handler 的 CAS 失败并审计化 no-op；后续多日审批处于 paused，亦不计入预算。但 §4.2.4 新增的“同一 join 更新 activation 首达即 supersede 旧 activation”会淘汰同 series 下仍合法在途的 activation，且多环计数向量没有定义“更新”的全序关系，见 R5-01。

2. **logical effect slot：反对。**  
   `(run,node,activation_id)` 不能隔离共享同一 fan-out activation 的不同 task，首次 fan-out 前也无 activation_id 来源。`effect_seq` 依赖同参调用次序，非决定论重执行若改变相同参数调用的数量或顺序，会把新逻辑调用误配到旧记录。更严重的是，已由 probe 确认成功的效应被“不复用、重做”，与 §5.2“可 probe **或**可安全重放”的能力要求冲突。另有状态全集不含 `unknown`，正文却要求持久化 unknown 的内部不一致。

3. **publishing 终态映射：反对。**  
   核销、进入 publishing、pending 登记以及不可判定时保持人工处置的主时序成立；但 `release_failed` 的“正常路由”无法从当前 Run 状态合法执行，且 pending administrative finalize 没有进入固定优先级表，见 R5-02、R5-03。

## 4. 新 issue 清单表

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| R5-01 | BLOCKER | §4.2.4、§4.5 | “更新 activation 首达即 supersede 旧 activation”与“每个 activation 全源到达后恰好触发一次”冲突。反例：同 series 合法产生 A、B 两次 fan-out；A 的源 X 先到，B 的源 X 随后到并淘汰 A；A 的源 Y 最后到达时被丢弃，导致 A 即使最终全源到达也永不触发。多环向量如 `(1,0)` 与 `(0,1)` 也无法据现有规则判断谁“更新”。 | 同 series 的 activation 应分别保持 open、独立原子消费及独立超时；仅 series 推进或该 activation 全部输入已确定 stale 时 supersede。若确需 latest-wins，则必须增加单调 `activation_seq`、静态禁止并发 activation，并明确丢弃语义。补充同 series 并发两组 activation 的 model-based 测试。 |
| R5-02 | BLOCKER | §4.2.5、§4.3.1、§8.3 | §4.2.5 允许 `release_failed` 走配置路由，但 §4.3.1 明确 publishing 出边只能关闭。反例：release_failed 路由至保留 `fail_safe` 或其他诊断节点时，需要创建 task，却不存在 `publishing → queued/running` 转换；直接路由违反状态机，直接关闭又绕过 DSL。 | 若保留可配置路由，定义 broker 完成事务中的 `publishing → queued` 转换、持久化 release outcome 并调度目标节点，同时规定已核销授权不可复用；同步状态图、guard 表与恢复测试。MVP 的另一闭合方案是静态限制 release_failed 只能直接映射固定终态。 |
| R5-03 | BLOCKER | §4.3.3、§8.3 | publishing 期间 administrative finalize 被登记为独立 pending 类型，但固定表在 release_failed 分支只处理 cancel、fail_safe，随后进入“正常路由”。反例：PONR 后发现 D12 漂移，远端最终确认发布失败；此时只有 pending administrative finalize，系统会错误进入普通 release_failed 路由，甚至可能使用已确认漂移的 execution manifest。 | 将 administrative finalize 明确加入 release_failed 的有序 pending 表；建议优先于普通路由，直接执行 ledger 级 `closed(fail_safe)` 并生成版本漂移 FeedbackReport。明确其与 cancel/fail_safe 的优先次序并加入故障注入断言。 |
| R5-04 | MINOR | §4.3.1、§8.3 | §4.3.1 声明 FeedbackReport 仅在 `closed(fail_safe)` 或 administrative finalize 生成；§8.3 却要求 released → `closed(succeeded)` 时把 pending cancel/fail_safe 写入 FeedbackReport。产物存在条件前后矛盾。 | 将成功发布后的异常信息改为独立审计产物，或在 §4.3.1 明确 FeedbackReport 还可用于 publishing pending 异常，并同步其 schema/消费者契约。 |

## 5. CLARIFY 清单

无。

## 6. 一句话总结

距离 draft freeze 还差 4 个 BLOCKER 与 1 个 MAJOR 的闭合，核心是稳定的 logical effect 身份、同 series activation 并发规则及 publishing 失败后的完整状态迁移。

上面是Codex的review意见
