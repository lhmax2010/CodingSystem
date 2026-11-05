# HLD v2.7 / 01 v0.17 定向复审 — Codex

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.7（仅 A24） | **GO** | 0 | 0 | 0 | 1 |
| 第二部分：01 v0.17（仅 A3 的 v0.17） | **NO-GO** | 0 | 3 | 0 | 1 |
| 新增同步项（不计入第二部分） | 无；B 第 7 组已有项不重复报告 | 0 | 0 | 0 | 0 |

## 负责人七项裁决的独立评估

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时必须显式报告 | **成立** | 两条验证支路仍按同一 series 汇合；本版没有放宽超时、缺失报告或审批谓词。并行可以减少时延，代价是保留两路及被替代轮次的完整证据，不必改回串行。 |
| ② | Quickbuild 取最新 Profile 快照并在 Run 启动时固定 | **成立** | §7.6.1 已区分本系统策略与 Quickbuild 的 Ref. Snapshot 缺省；本版进一步把构建根结论限定于已调查样本，独立固定能力仍为 unverified。采用较新快照的环境不匹配风险、推广证据与双编号均可见，不承诺 HEAD 落后上界。代价是真实的构建失败与取证成本，而非额外的已验证能力。 |
| ③ | Profile v1 严格匹配，v2 为经评估开启的放宽预案 | **成立** | 本版没有绕过缺省关闭、兼容条件及非劣评估。放宽应由实际工具链数据支持；仍需承担重采和验证成本。 |
| ④ | 目标范围与模块登记表，验证范围只增不减 | **成立** | 确定性撤销恢复代码树，不撤回已经识别的验证义务；本版没有增加缩减目标范围的入口。额外验证成本可接受。 |
| ⑤ | 用测试结果与多版本对比报告检验 AI | **成立** | 计划与 series 现在同事务生效，AI 不能通过暂存候选或自报 purpose 提前改变判定对象。收益不确定即撤销的保守性仍在；不能修复未决候选是换取可判定性的明确代价。 |
| ⑥ | 显式 base 预检、读回核对 | **成立** | `auto` 套件无法在加载期证明 absolute-only，保守要求 comparison 合理；显式锁定的 absolute-only 非发布用法仍有豁免。代价是部分实际只用绝对指标的 auto 配置也需比较能力或改配本地后端。 |
| ⑦ | 超时重试成功可发布，审批人确认 | **成立** | 当前 series 全部 task 与所用基线 task 的 retried 逐条确认、历史轮次首屏汇总、确认摘要和核销复核均未被本版缩减。开发者和审批人都能知道发生过超时；无需把已由成功重试覆盖的超时永久当作失败。代价是审批信息量与证据保留。 |

## 范围、输入与方法

日期：2026-11-05。首先执行 `git pull --rebase`，返回 Already up to date。输入 HEAD：`34a096e1a531ed2aa90b621f408f951aef5d86c1`。阅读两份上一轮处置表及 Kimi、Claude Code、Codex 三份上一轮原始意见；核对 v2.6→v2.7、v0.16→v0.17 的全部差异及其直接关联条款。未读取本轮其他评审方意见，未访问或探测 Quickbuild，未修改被审文档。

| 输入 | SHA-256 |
|---|---|
| `docs/00_Framework_HLD_v2.7.md` | `4ca18baeac6dbc059ae0c2332119813e02d65f5bc5959f4828b0cbeb09cfd6bf` |
| `docs/01_Contract_Spec_v0.17.md` | `a33a7b0a43fa8bea597b326d4feb9c0d15757cf3c99d8cfbdc825ac28c5de06d` |
| `docs/review/HLD_v2.6_review_disposition.md` | `27aa029fe4bed56e3fdee593efff808f3f2127ef0aad5bcb7c247cbd8c8ac355` |
| `docs/review/01_v0.16_review_disposition.md` | `ee003863542a5e88848d79046298bbfc24947bcf3b65e840abb83c8a66e7f265` |

验证为文档状态机走查、YAML 解析及小脚本反例演算，不是运行尚待实现的 conformance。四份示例均解析成功、镜像节点均选择 local；01 的 123 个 class 均能在 A0 找到。未用“最后一轮”作为降低 GO 标准的理由。

## A. 处置逐项核对

### HLD：S1–S6

| 条目 | 落实与判断 |
|---|---|
| S1 | §7A.4 已分离受理预校验与完成事务权威复核；计划创建、撤销迁移、父 CAS、lineage/current 一起提交。崩溃、作废及完成重放语义明确；本方 H26-01 关闭。 |
| S2 | 撤销条不再包含未决期间的后续修复段；§11.3 两个旧修复前置替换为失败后确定性撤销；旧 gate 用例限定 A/B 依赖。Kimi NIT、CC H26-01、本方 H26-02 对应正文已修。 |
| S3 | §7A.4 未决计划下非 opt_patch_ready 业务返回归 sys.invalid_result；campaign 的 no_gain_found 增净变更检查。§4.2.6③与撤销条修正 terminal 理由。§11.3 的 v2.6 旧断言尚有一处残留，见 H27-01。 |
| S4 | 拒绝响应包含 plan_id/parent_tree，同 task 的 make_revert 及错误结束处理已写入；§11.3 有先拒绝再撤销只通过一次环边的用例。 |
| S5 | §4.2.6 明确 auto/未锁版本按 A/B，豁免限于显式锁定且全部 absolute 的套件；新增两种相反预期的夹具。 |
| S6 | §7.6.1 构建根措辞限于样本，独立固定为 unverified；审批呈现删除重复的构建根编号。落实。 |

**“记录更正”核验**：HLD 处置表将 v2.5 的“5 个独立问题”更正为 R1–R4 四个，准确。CC 原始意见明确撤回了“base_mismatch 绕过 UT/Benchmark 直达 terminal 是合法可达场景”的判断；规则③确实在加载期拒绝该图，更正准确。本方上一轮路径表对该场景的条件化描述也应限于构造性防御测试，不能当作合法流水线路径。更正应同时清理当前规范的旧测试文字（H27-01），历史版本无需回写。

### 01：T1–T5

| 条目 | 落实与判断 |
|---|---|
| T1 | 嫌疑集、单个计数、多个不计数、持久化隔离顺序已写入 §2.2d、ReleaseTaskState、CF-AUTH-20g/20h/20k。但“只有一个 S 成员执行”不等于“实例上只有一个任务执行”，且队列只按业务终结推进，两个新缺口见 C17-01/02。 |
| T2 | 嫌疑集覆盖 awaiting_consume，不依赖 ACK；耗尽按授权实际核销状态分流。原核销前毒丸完全漏计问题已修。其与 launcher 的交界仍需互斥归责，见 C17-03。 |
| T3 | spawn_attempt_id/cgroup 先持久化，hello 前失败可计数，连续上界不依赖时间窗，稳定期才清零；CF-AUTH-20i 落实。首个“送达”与 T2 的持久化绑定使用不同边界，仍可能双计，见 C17-03。 |
| T4 | §2.2d、§5.1、C-11a 与 CF-AUTH-20j/IPC-10 已放开 manual_only 下四种 recovery_state 的只探测；结果仅作证据，人工裁决仍受远端事实约束。落实。 |
| T5 | recovery_mode 迁移及 isolating 字段落文；C-09、④显式拒 manual_only，C-11a 显式禁止其自动终局。隔离调度退出条件尚不完整，归 C17-02，不另重复计问题。 |

**两处合并方案的独立判断**：

1. **按派发绑定识别核销前嫌疑、按授权实际状态分流：成立。** 没有 ACK 不等于 broker 没收到，awaiting_consume 也不等于从未核销。采用持久化绑定与实际授权是正确选择。这里的“嫌疑”不能被解释为已经证明该任务导致崩溃；归责仍须完整隔离。
2. **持久化连续启动失败上界 + 执行故障不冲击启动熔断：有条件成立。** 两种故障分开处理的原意合理；必须用同一个持久化事件边界把每次故障唯一分到一个域。当前“已绑定”和“已送达”不是同一条件，合并文本没有实现互斥（C17-03）。不采用依赖时间窗密度的旧方案是正确的。

01 处置表没有单列“记录更正”节；其“合计 7 条”与原始意见数量不一致，见 C17-04。五个合并主题均有来源，不存在未找到来源的第六个主题。

## B. 第一部分问题与定向走查

### H27-01 — NIT：已纠正的 terminal 路由反例仍保留相反的旧夹具预期

**位置**：`docs/00_Framework_HLD_v2.7.md` §11.3，“v2.6 追加 / terminal 兜底”；直接冲突于本版 §4.2.6③及“v2.7 追加”。

**依据**：旧句仍为“**未决计划下 image_failed_exhausted 路由到 terminal → closed(fail_safe, pending_plan_at_terminal)**”；本版同一清单又要求“**image_failed_exhausted → terminal 的优化流水线被规则③拒绝**”，并另有“**直接构造‘未决计划 + terminal success_on’**”的防御测试。

**问题**：若把旧句当加载合法流水线的集成用例，前置即不可达。新规范和纵深防御本身正确，故不影响 GO；但自动生成夹具时仍会出现两个相反期望，S3 的清理未完全落实。

**候选 diff**：

```diff
--- docs/00_Framework_HLD_v2.7.md §11.3 / v2.6 追加
- terminal 兜底（未决计划下 image_failed_exhausted 路由到 terminal
- → closed(fail_safe, pending_plan_at_terminal)）
+ terminal 兜底（绕过加载器直接构造“未决计划 + terminal success_on”状态
+ → closed(fail_safe, pending_plan_at_terminal)；合法图的可达性由 v2.7 组单独检验）
```

**副作用**：仅明确单元测试与加载集成测试的边界，不改运行时兜底。**测试/夹具**：合并重复的 terminal 防御断言；保留非法路由加载拒绝与 Optimization 返回 no_gain_found 的 invalid_result/retry 两组测试。

### purpose、重放与正常终局

| 路径/竞争点 | 本版唯一结果 |
|---|---|
| 受理前或受理后 worker 崩溃 | 预校验不改变 current/plan；由既有 task attempt 恢复，不能凭已受理候选创建计划。 |
| 预校验 candidate/revert，完成时父版本不再匹配 | §4.2.4 父 CAS 拒绝；预校验不授予提交权，不采用候选、不迁移计划。旧 series 在飞结果按冻结陈旧性规则丢弃。 |
| 父仍匹配，但当前计划/purpose/容量不再满足 | 完成事务权威复核不通过，不提交推进与计划副作用；不把预校验快照当豁免。若需改交/重试，仍须通过相同规则。 |
| 两个并行候选引用同一父版本 | 完成事务串行化，一方 CAS 成功，另一方拒绝；只有胜者创建/迁移计划。预校验均成功不是双采用。 |
| 完成事务提交前/后崩溃、同完成 id 重放 | 前者全部未发生，后者 receipt 返回原结果；计划、lineage/current、候选轮数不重复变化。 |
| 初始段/普通修复 | initial 与 repair 保持原分类；无未决计划时的合法修复不被新规则拦截。 |
| E-CANDIDATE-NOT-REVERT 后 make_revert | 同 task 内拒绝的候选没有推进、没有路由环边；合法撤销被采用后才随对应 status 通过一次环边。Compiler/UT 与 Optimization 的撤销 status 各自沿原路由。 |
| 拒绝后直接用成功业务 status 结束 | sys.invalid_result；配置 retry 时复用该 task、增 attempt，重试本身不走环边。仍须满足 attempt/父版本有效性与原预算。 |
| 新候选容量不足/撤销时容量不足 | 新候选预校验 E-PLAN-NO-CAPACITY，按 mode/净变更返回无收益；撤销命中规则①，不再走候选准入。 |
| 未决计划下 campaign 返回 no_gain_found/no_further_gain | Optimization task 上 sys.invalid_result，可按 retry 修正，不能借 terminal 宣称成功。 |
| 全部候选已撤销且无净变更 | 所有计划已 reverted，无未决计划；常规重验证完成后 no_gain_found 合法，进入 report_no_gain，不建空发布计划。 |
| 已有净变更但 no_gain_found | 即使没有未决计划也 sys.invalid_result；应返回 no_further_gain。 |
| 未决计划到审批/直接构造 terminal 成功 | 审批拒绝；terminal 防御分支 fail_safe(pending_plan_at_terminal)，无发布授权。 |

新规则与 §4.2.4 的冻结推进模型一致。完成校验失败是拒绝事务，不是“把原 candidate 自动改类再提交”；没有发现必须另开权威计划状态的路径。四份原文示例的 local 后端三项能力均 verified：示例一/二/四使用 auto，不享受 absolute-only 豁免但不被误拒；示例三无 Benchmark，不新增比较要求。显式锁定 absolute-only 非发布 gate 的豁免与 auto 保守规则不冲突。

## C. 第二部分问题

### C17-01 — MAJOR：嫌疑集内串行不等于实例隔离，仍可无限不计数或误计无辜任务

**位置**：`docs/01_Contract_Spec_v0.17.md` §2.2d“嫌疑集 / 隔离重派”、CF-AUTH-20g/20h/20k。

**依据**：原文限制“**任一时刻全部实例上至多一个 S 内 task 处于执行可能阶段**”，同时规定“**不在 S 内的新派发不受影响**”；随后据此断言“**隔离中的单个 task 所在实例被回收时只对它 +1（嫌疑集大小为 1）**”。此外 S 明确排除“**本次失联触发者**”，但 `|S| = 1` 就给剩下的 task 加 interrupt。

**反例一（未完成隔离）**：P、B 首次同实例崩溃形成 S={P,B}。轮到 P，新的 N 正常派到当前唯一 broker；P 崩溃时，持久化绑定的未完成 execute 集实际是 {P,N}。按一般规则大小为 2，不计数、再形成嫌疑集。每轮加入一个新任务，P 可以一直不增 interrupt；简单演算 6 次仍为 0，推翻“至多 1+上限次”。若优先执行“隔离中只对它 +1”，当 N 才是毒丸时会把无辜 P 计到 manual_only。两种解释都不满足声明的性质。

**反例二（排除已知触发者不等于独占）**：A 的阶段到期退役，B 只是同实例无辜任务；排除 A 后 S={B}，B 仍被 +1。A 连续两次到期后耗尽，随后另一个 A2 到期，即可让一直较慢但正常的 B 累计三次 interrupt 进入 manual_only。现文“无辜任务不被连带计数”与此矛盾。单一当前实例意味着无法默认为新任务另有不受影响的 broker。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.17.md §2.2d 嫌疑集与隔离重派
- 至多一个 S 内 task 处于执行可能阶段；不在 S 内的新派发不受影响。
+ 隔离轮次持久化选中的 task、目标 epoch 和独占派发许可。
+ 该实例承担隔离任务时，不得接入其他任务的 execute 或 probe 派发，
+ 包括新任务、其他嫌疑集、hello 扫描及 intent 续送；未获许可的派发排队。
+ “单任务隔离失败”必须核对该实例确实独占，不能只统计原 S 的成员。
+ 隔离成员身份在 recovery_mode 回到 active 后仍由 suspect_set_id/顺序记录保留；
+ 所有出向生成/续送事务统一校验独占许可，重启不得绕过。
- 排除本次失联触发者后的 |S| = 1 → interrupt_count +1。
+ 已由阶段 CAS 确定触发 task 的退役事件只增加该 task 的 loss_count；
+ 其他 task 只解除定时器并重排，不因同实例退役增加 interrupt_count。
+ 无确定触发者的 lapsed：按该实例全部未完成执行绑定识别嫌疑；
+ 单一承担者或已证明独占的隔离任务才增加 interrupt_count；多人则不计数并隔离。
+ 既有隔离成员不得因新的嫌疑集覆盖而丢失顺序、计数与调度权。
```

**副作用**：事故恢复期间新发布和只探测会排队；这是同一进程故障域内实现归责的必要代价。若要保持新任务并发，须另设计进程级任务隔离，不能只在 S 内排序。本方案保留单一当前 broker、epoch 和授权规则；计数只识别任务执行导致的可复现故障，不宣称能从任意硬件故障推断真实责任。与 C17-02 的可运行队列结合，长期等待证据的任务不占独占槽。

**测试/夹具**：CF-AUTH-20k 的“新 task 照常派发”改为“排队且在隔离槽释放后可派发”。新增 P 与新 N 的两种毒丸位置、连续新任务流、两个重叠嫌疑集、hello 扫描和未完成 intent 恢复；断言实例独占、计数有界及健康任务不被别人计数。CF-AUTH-20h 加 A 两次到期+A2 一次到期，B interrupt 恒为 0。不能只测试静态的 P/B 两任务集合。

### C17-02 — MAJOR：隔离队列只在终结/耗尽时前进，等待静默或 indeterminate 会无限堵住后续任务

**位置**：01 v0.17 §2.2d 隔离顺序、recovery_mode 迁移、awaiting_probe 及持有者更替；CF-AUTH-20k。

**依据**：“**它终结或达到上限后，下一个进入执行；S 内全部终结后恢复常规并发**”；“**waiting_holder 与 isolating 下执行类阶段定时器不武装**”；“**awaiting_probe 不触发 retiring**”，只探测 indeterminate 可以一直保持 publishing。

**反例一**：S={A,B}，A 排首。A 已核销，旧 holder 子树长期无法证明为空；B 尚未核销，按既有替代协议本可在新实例立即执行。A 不可重派，不会到期计数，也未终结；B 因顺序一直不轮到。若坚持“B 立即重派”，则又绕过新隔离队列。新规则与保留的 CF-AUTH-20e 出现两种出口。

**反例二**：旧 holder 已静默，A 在隔离恢复中对账为部分出现/unknown，进入 indeterminate。它不再有执行权，只需要周期 probe；但既未终结也未耗尽，B 仍永远排在其后。B 的健康发布不应依赖 A 的远端证据或人工裁决何时获得。达到上限的 A 可以推进下一项，但“S 内全部终结”又未说明 manual_only 未关闭时如何结束隔离阶段。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.17.md §2.2d 隔离调度与 recovery_mode
- 它终结或达到上限后，下一个进入执行；S 内全部终结后恢复常规并发。
+ 隔离诊断完成/让出执行槽与 Run 关闭分开记录。
+ 成员以持久化状态区分 ready、waiting_holder、probe_only、diagnostic_done；
+ 只从 ready 集按既有确定序选取一个任务，等待静默者不占执行槽。
+ 已核销成员仍须自己的 granted_epoch holder 静默后才能成为 ready；
+ 不因跳过队首而放宽任何任务的静默条件。静默事件使其重新可运行，
+ 保留原顺序，防止持续新任务流使其饥饿。
+ 转 indeterminate 时同事务退出 execute 调度、进入 probe_only，释放隔离槽；
+ 达到上限或业务关闭时标 diagnostic_done；manual_only 仍只经 C-11 收尾。
+ 所有成员不再可执行诊断时可以放行普通队列，不等待人工终局；
+ 将来 waiting_holder 成员恢复 ready 时重新进入独占诊断，先前计数不清零。
+ hello、周期扫描与出向恢复共用此调度入口；等待模式的变更不能直接发 execute。
```

**副作用**：需要独立于 recovery_mode 的持久化隔离成员调度状态；不能把“active”同时当成“已经退出嫌疑集”。顺序变为可运行成员的确定序，保证安全前提下的进展；真正无法确认旧持有者静默的那个 task 仍可长期等待并告警，这是合法安全等待，不应传播成其他 Run 的无界阻塞。

**测试/夹具**：隔离队首已核销/尾项未核销且旧子树永久非空；队首恢复后进入 indeterminate，probe 永远 unknown；队首 manual_only 但人工不裁决；队首恢复 ready 与其他项完成并发；每个成员状态及选中许可提交前后 kill 编排。断言尾项可完成、无越过自身静默的执行、队首恢复后不饥饿、没有两个隔离 execute 同时进入当前实例。模型新增字段/记录须补 A0 索引及持久化恢复夹具。

### C17-03 — MAJOR：任务“已绑定”与 launcher“已送达”的分界不同，同一故障仍可双计或错误触发全局熔断

**位置**：01 v0.17 §2.2d 嫌疑集与 launcher 启动失败上界；§2.5 DispatchReceipt 两事务协议；CF-AUTH-20g/20i。

**依据**：任务按“**最近一条 execute 型 receipt 的 target_epoch == 该实例 epoch，不论是否收到 ACK**”识别；launcher 把“**首个 execute 派发送达本实例之前 lapsed**”算启动失败。§2.5 明确“**事务①（发送前）写 intent……发送；broker 响应；事务②写 completed + 首响应**”，completed 才表示 ACK 已落账的送达完成。

**反例**：E hello 成功，T 的 intent 已提交，尚未发送，E 因初始化尾部错误退出。回收时 T 已绑定、S={T}，interrupt +1；同时首个派发尚未送达，spawn 的启动失败也 +1。即使物理送达可知，该格仍确定重叠。再把崩溃点挪到“已接收毒丸、ACK 前”，编排没有 completed，无法仅凭现有持久化状态区分两者。按 ACK 当送达会让执行毒丸提前触发全局启动熔断；凭物理接收猜测则不具崩溃恢复依据。连续启动失败上界解决了旧漏计，但没有解决两种归责的互斥。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.17.md §2.2d launcher / 故障归责
- hello 后首个 execute 派发送达前 lapsed 计启动失败；送达后只计任务。
+ 启动/基础设施与任务故障共用持久化 retirement_event_id 的归责事务。
+ hello 及实例就绪完成前不得绑定 execute；intent 提交事务同时写入
+ 该实例已承担的执行绑定，作为启动域向任务域交接的唯一边界，不以 ACK 判定。
+ 回收事件按其故障快照互斥结算：存在未完成 execute 绑定则只进入任务
+ 嫌疑/隔离流程；没有绑定则由 launcher 的启动/健康失败计数承担。
+ intent、lapsed 判定与绑定关闭按同一实例状态串行化：lapsed 先提交时
+ 禁止新绑定；intent 先提交时故障只归任务域。每个事件只能选择一个域。
+ launcher 读取该归责结果按 spawn_attempt_id 恰一次记账，不另用 ACK 推断。
+ 既有任务全部完成后发生的无任务实例故障归基础设施域，不能因历史上
+ 曾经送达过一次任务就永久免计；正常稳定健康期仍按既定规则清零。
```

**副作用**：把“送达后不算启动失败”收紧为可恢复的逻辑交接，而非无法原子观察的物理送达。intent 后、实际发送前的故障会保守进入嫌疑流程，不能称为已证明任务有错；隔离复测承担辨别职责。新增实例就绪/归责记录与 launcher-Ledger 交接成本，但不增加发布执行许可，也不以 ACK 丢失推断未发布。

**测试/夹具**：同一 spawn 的 hello 前后、intent 前后、发送前、受理后 ACK 前、ACK 后 completed 前后逐点故障；断言每次事件只归一个域且重启不改归责。核销前毒丸即使从不返回 ACK 也不能耗尽 launcher 启动上限；无任务启动失败必须耗尽上限。补“任务已正常完成后实例失效”和“lapsed 与 intent 并发”两例，不能只做已 completed 的毒丸测试。

### C17-04 — NIT：上一轮原始意见合计是 6 条，处置表和 A3 写成 7 条

**位置**：`docs/review/01_v0.16_review_disposition.md` 开头；01 v0.17 文首关联计数与 A3 的 v0.17 项。

**依据**：处置表列 Kimi 0，Claude Code“**1 MAJOR + 2 MINOR + 1 NIT**”，Codex“**2 MAJOR**”，随后写“**合计 7 条意见**”。原始编号分别是 CC C16-01–04、本方 C16-01–02，合计 6 条；CC C16-03 内含两个子点，不是两个独立编号。

**问题**：五个合并问题有完整来源，但输入条数与按编号统计不一致。若有意按子点计数，应声明该口径，不能与各方结论表的条数混用。

**候选 diff**：

```diff
--- docs/review/01_v0.16_review_disposition.md
- 合计 7 条意见，归并为 5 个独立问题
+ 合计 6 条编号意见（CC C16-03 含两个子点），归并为 5 个独立问题
--- docs/01_Contract_Spec_v0.17.md 文首关联及 A3
- .../5/7 条逐条处置
+ .../5/6 条逐条处置
- v0.17 = 第十六轮 7 条意见（5 个独立问题）全部采纳
+ v0.17 = 第十六轮 6 条编号意见（5 个独立问题）全部采纳
```

**副作用**：不改处置方案、协议版本或状态机。**测试/夹具**：无需产品测试；来源索引应按“评审方+问题编号”去重得到 6，并保留 C16-03 两个子点到 T2/T3 的多对多映射。

## D. 五条时间线的组合走查

以下用分层互斥表覆盖时间线 × 崩溃点 × 阶段到期 × 计数上限 × 毒丸位置 × 同实例任务。先选业务行，再选传输/事务边界，再选故障归责与上限行；不可能组合明确排除，例如未核销授权不可能合法处于 awaiting_outcome。表中标出缺口，不把尚未闭合的格写成“唯一出口”。

### 记号与安全前提

- Q：原 granted_epoch 持有者的可信 cgroup 子树静默证明。lapsed、leader 退出、kill 请求、读取失败或同名目录重建均不等于 Q。
- R：已核销、非 indeterminate、非 manual_only 者，经 Q 后 resumed，对账全部发生→H；全部未发生且许可复核通过→P；许可不通过→F；部分/未知→U。
- H/F：分别按 released/release_failed 固定映射；P：一次原子执行许可；U：锁存 indeterminate，仅只探测。
- L/M：计数耗尽时，实际未核销→撤销授权并失败关闭 L；实际已核销→manual_only M，仅 C-11 人工出口。
- B：只读 probe；M 下结果仅证据；非 M 的 U 下，发生→H，未发生且 Q→F，未发生未 Q→退役原 holder 并在 Q 后以新 probe_seq 重探，未知→继续 U。

### 业务时间线

| 时间线 | 正常/恢复唯一业务出口 | 本版新增机制的影响 |
|---|---|---|
| 正常 | 未核销→一次 consume→执行→H/F；consume 与撤销授权 CAS 单胜 | 低于上限可恢复，上限先选 L/M；同实例混合的故障归责仍有 C17-01/03。 |
| 核销后发生前崩溃 | 不再初次核销；Q 后 R，未发生时 P 或 F | waiting_holder 安全等待正确；作为隔离队首时不能阻塞其他可运行成员，C17-02。 |
| 发生后崩溃 | Q 后 R→H；若部分出现则 U，不能再按全量未发生执行 | H 的终局事务前可再取事实，后只重放；耗尽 M 时 probe 全部发生只准 confirm_released。 |
| indeterminate | B/U；负向结案须 Q，不能发 execute、不能 P | M 任一 recovery_state 可 B；隔离任务转 U 却不释放顺序的缺口是 C17-02。 |
| 实例仍 live、单个 task 失联 | 当前 phase/generation 到期 CAS→退役→按 Q/授权恢复或 L/M | 只触发 task 增 loss 正确；剩余单个无辜 task 增 interrupt 的规则仍与隔离目标冲突，C17-01。 |

### 出向、完成和持久化崩溃点

| 崩溃点 | 正常未核销 | 两条已核销执行时间线 | U 或 M 的只探测 |
|---|---|---|---|
| intent 前 | 无派发；重新校验调度准入 | Q/模式/隔离准入后才创建 intent | 创建 probe intent，不 consume |
| intent 后、发送前 | 同 epoch 同 id 续送；换 epoch 替代 | 同左，但换实例恢复须 Q | 替代后仍 probe，无执行内容 |
| 受理后 ACK 前 | 同 id 进程内去重，授权只核销一次 | 不重复许可；新 epoch 必须重新 R | 不因丢 ACK 变 execute |
| ACK 后 completed 前 | 仍按 intent 恢复，不伪造 completed | 同左 | 同左 |
| completed 后 broker 崩溃 | completed 仅送达；按实际授权选择初次或恢复 | Q 后 R，不把 ACK 当 task 终结 | 周期 B；M 不自动结案 |
| 替代事务前/后再崩溃 | 旧 intent 或唯一新 intent，CAS 单胜 | 同左；新 epoch 再变化则重走替代 | 同左；旧 ACK 只审计 |
| consume/proceed/最终映射事务前后 | 前使用旧状态，后 receipt/状态恢复 | 已提交许可不跨 epoch 复用；终局已提交不重开 | 已记录观测不伪造新事实或终局 |

传输幂等与静默安全没有因本版改变而失效；但这张表中 intent 已提交至 completed 前的实例故障，在新增计数层存在 C17-03，不能因为传输唯一就宣称全链计数唯一。

### 阶段期限、计数与同实例任务

| 故障/阶段 | 低于上限 | 达任一上限 | 同实例其他任务/缺口 |
|---|---|---|---|
| live + 当前 armed 的 consume/outcome/reconcile 到期 | 本 task loss+1，退役、解除全部旧 timer；按授权恢复 | 实际未核销 L；实际已核销 M | 其他任务 loss 不加；S 单元素仍加 interrupt，C17-01。 |
| 实例 lapsed + awaiting_consume（初次或恢复派发） | 纳入嫌疑，单个加 interrupt，多人隔离 | 初次未核销 L；恢复虽同阶段仍是 M | 原漏计已修；与 launcher 送达分界冲突 C17-03。 |
| 实例 lapsed + awaiting_outcome/reconcile | 单个 interrupt+1，多人隔离 | M | 隔离允许新共驻任务，可能再成多人而永不计数，C17-01。 |
| waiting_holder / 尚未轮到的 isolating | 不武装，不计执行失联 | 既有耗尽状态不能被调度重新激活 | 等待本 task 合法；阻塞其他可运行任务不合法，C17-02。 |
| awaiting_probe 到期 | 重试 probe，不退役、不计执行计数 | M 仍仅裁决证据；U 不因 probe 超时变 L/M | 无限未知是事实不足，不应占隔离 execute 槽，C17-02。 |
| 旧代 timer、retiring/lapsed owner、重复回收事件 | no-op/审计，同 task 同事件至多一次 | 不恢复 L/M | 不应退役新实例；现有 generation/owner/CAS 规则成立。 |
| 完成事件与到期竞争 | 完成先提交→旧期限失效；到期先提交→旧结果被连接守卫拒绝 | 同一事务按实际授权选 L/M | 不允许先按未核销关闭、又收到合法 consume。 |
| launcher 在 spawn/hello 前后崩溃 | 持久化 spawn 续跑/清理，失败恰一次 | 连续上限停止并告警 | 无 execute 绑定时闭合；有 intent 但无送达时 C17-03。 |

isolating→active 不能清掉嫌疑组身份；现模型有 suspect_set_id/isolation_seq 可承载来源，但没有补齐可运行/只探测/已诊断的调度状态与退出条件。C-09 只排 manual_only 并不代替编排的隔离准入；C17-01/02 的修订应同步作用于 hello 扫描、普通 dispatch、旧 intent 续送和周期恢复。

### 毒丸位置与有界性

| 场景 | 本版可证明的结论 |
|---|---|
| 单任务核销前毒丸，已明确送达 | interrupt 有界；实际未核销 L，恢复派发已核销 M。 |
| 单任务执行中毒丸 | interrupt 有界后 M；不得再 execute。 |
| 固定 P/B 集合，其他工作完全不存在，Q 最终可得 | 首次多人不计数，真正单独复测时有界；这是 CF-AUTH-20g 已覆盖的受限情形。 |
| 隔离 P 同时加入新 N，或另一个嫌疑集也选中任务 | 原文不能证明单实例只承担 P；多人不计数或错归 P，C17-01。 |
| 无辜 B 被不同期限触发者轮流连带 | 排除触发者后的单元素计数会把 B 推入 M，C17-01。 |
| 隔离首项长期等 Q、变 U 或等待人工 | 尾项可永久等待，C17-02；不是毒丸达到计数上限可解决的格。 |
| 载入毒丸崩溃在 ACK 前，或 intent 后尚未发送就崩溃 | 任务计数与启动计数未互斥，C17-03。 |

小脚本按现文规则演算：6 次“P+新无辜成员”的 lapsed，P.interrupt_count 始终为 0；队首 U 且计数未耗尽时“终结或耗尽”条件恒假；intent 已绑定但尚未发送即 lapsed 时任务计数和启动计数同时为 1。这些是状态机反例，不是模拟真实 broker 的性能或错误概率。

### manual_only 与事实约束

本版 T4 的补丁成立：manual_only × {none, reconcile_required, execution_permitted, indeterminate} 的强制 probe 都有合法载体；它不包含发布计划/内容、不加载写原语、不 consume，写调用必须恒为 0。C-09、恢复臂和编排 execute 均排除 manual_only；C-11a 即使探测到全部发生也只记录证据，不能替审批人自动收尾。旧 epoch 的 granted/proceed receipt 在连接守卫之前不能复活权限。

人工裁决仍须实际执行强制 probe：全部发生只准 confirm_released；全部未发生只准 Q 后 confirm_not_released；相反请求拒绝并保持 publishing。部分/未知沿既有证据规则，不是自动发布许可。未发现本版新增能以只探测路径实际发布或违背明确远端事实的合法出口。上述三个 MAJOR 主要影响归责、有界恢复和跨 Run 可用性，并非已经发现重复发布漏洞。

## E. 同步项与交付边界

HLD B 第 7 组已登记 purpose 四值及编排推导、candidate 预校验与完成复核、E-CANDIDATE-NOT-REVERT 响应字段、pending_plan_at_terminal、后端能力/套件规则及相关报告扩展。01 仍以上游冻结 v1.0+E-01 为准，不将这些已登记但未同步的 v2.x 内容计为契约缺陷。本轮无新增未登记同步项。

所有候选 diff 仅存在于本报告；未修改 HLD、01、历史处置表或其他评审方文件。交付只暂存并提交本方报告。
