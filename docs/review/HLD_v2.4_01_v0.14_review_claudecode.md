# HLD v2.4（第四轮）+ 01_Contract_Spec v0.14（第十四轮）定向核对意见 —— Claude Code

- 被审：`docs/00_Framework_HLD_v2.4.md`、`docs/01_Contract_Spec_v0.14.md`
- 背景：`docs/review/HLD_v2.3_review_disposition.md`、`docs/review/01_v0.13_review_disposition.md`、上一轮三家原始意见、`docs/research/quickbuild_business_logic.md`（只读，未访问或探测 Quickbuild）、冻结基线
- 范围：只做定向核对——A 处置落实；B A21 所列改动；D 01 v0.14 改动与五条时间线走查。未改动部分不报
- 方法：v2.3→v2.4 与 v0.13→v0.14 全部 diff 块逐一核对；§7.6.1 逐句对照调查记录的证据等级；五条时间线 × 崩溃点 × 阶段期限到期逐格推演
- 只评审、不修改被审文档

## 结论

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| 第一部分：HLD v2.4 | **GO** | 0 | 0 | 4 | 1 |
| 第二部分：01 v0.14 | **NO-GO** | 0 | 1 | 1 | 1 |
| 同步项（单列，不计入第二部分结论） | — | 0 | 0 | 0 | 0 |

同步项：v2.4 新增的 ExpectedSourceManifest、`actual_build_conf_digest`、`backend_source_input_unsupported`、`E-PLAN-NO-CAPACITY`、`gaps_changed`、`succeeded_with_gaps`、`E-SKILL-EMPTY-SERIES`、comparison 三值、段 `purpose` 已全部登记在附录 B 第 7 组，没有未登记项。

## 负责人七项裁决的判断

| # | 裁决 | 判断 | 理由 |
|---|------|------|------|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | **成立** | 本轮未改动，上一轮的残留措辞已清理 |
| ② | Quickbuild 默认取最新，在 Run 启动时解析固定 | **有条件成立** | "最新"解析为最新 Profile 快照，是可以证实、可以复现的做法。但处置表说"这正是 Quickbuild 自身不指定版本时的行为（实测已证实）"不准确：调查记录中表单缺省是 `BUILD_REFERENCE=Ref. Snapshot`（滚动的 reference），样本里 reference 为 Oct-13，Profile 为 Oct-28。这是本系统的选择，不是 Quickbuild 的缺省，需要如实写明并说明代价（H24-01） |
| ③ | Profile 严格匹配 + 小改动复用预案 | **成立** | 本轮未改动 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | 撤销后范围不缩减，其出口已由"撤销即 reverted + 常规义务"补齐 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | 被测源码身份证明（ExpectedSourceManifest）补上了"测试结果确实来自所声称代码"这一前提；不可比不能经人工补出结论，与原则一致 |
| ⑥ | Quickbuild 可加 Base CL，否则默认最新 | **有条件成立** | Tizen 侧落为"Profile 快照编号 + 个别包覆盖"，按证据等级登记，处理正确。"按构建号读取"一项反而写得过于保守（H24-01） |
| ⑦ | 超时后重试成功可发布，须审批人确认（本版收窄） | **成立（附一处精度缺口）** | 负责人的本意是"开发人员和审批人都要知道发生过超时"，收窄后仍然满足：开发者经 `get_result` 看到全部 retried；审批人对当前证据链上的重试逐条确认，被取代轮次的重试在首屏汇总列出，仍可见；确认绑定内容 digest，防止重放旧确认。代价已在正文写明：核销复核失败须新建 Run。缺口是"证据链"只按 release_evidence 中的报告划定，漏掉了 ci_plan、Review 与内部基线构建上的重试（H24-03），补上后完全满足本意 |

---

## A. 处置落实核对

| 处置 | 正文落点 | 核对 |
|------|---------|------|
| M1 证据等级 / 最新 Profile 快照 / 有界 probe / 镜像与取消 unverified | §7.6.1、§5.2、§12、§13 P6 | 已落实；两处证据表述不准 → H24-01 |
| M2 ExpectedSourceManifest + 暂存输入通道 | §7.6.1 | 已落实；不支持时的失败点与状态未定，且首期 Quickbuild 实际无可用角色未在风险与分期中写明 → H24-02 |
| M3 实际 build.conf 与发布摘要分列、unknown 即不可比 | §7.6.1、§7.8 | 已落实 |
| M4 不可比 → inconclusive → 撤销；撤销即 reverted；谓词 `comparison = verified` | §7A.4、§4.2.6① | 已落实；段 `purpose` 由谁声明、base_mismatch 与确定性撤销的优先级未定 → H24-04 |
| M5 创建计划的运行时准入 | §4.2.6③、§7A.4 | 已落实；campaign 下"无进一步收益的 status"二选一未定 → H24-05 |
| N1 retried 收窄、digest 绑定、gaps_changed | §4.3.5、§8.2、§8.3 | 已落实；证据链边界与"broker 返回"措辞 → H24-03 |
| N2–N9 | 各节 | 均已落实（登录超时统一为 fail_safe、多入边取交、净 diff 重算、Review final 时序、残留措辞、base_mismatch 归属、external_timeout 缺省、附录 B 补登） |
| 01 Z1–Z6 | §2.1、§2.2d、§2.5、§5.1、CF | 均已落实；阶段期限与重派之间缺少次数上界 → C14-01 |

**未采用评审方方案之处的理由**：
- **M3 不按时间窗口视为可比（未采用我方方案）**：成立。我方上一轮自己也写过"读不到就忽略等于静默放行"，时间窗口只是降低漂移概率，不是证据。代价是首期 Quickbuild 不承担 A/B，正文已写明改用本地后端。
- **M4 不可比不能经人工确认满足 Bench 谓词（未采用我方方案）**：成立。人可以接受"没有比较结论"这一事实，但不能替测量补出结论；需要 A/B 的流水线因此只能用本地后端，这与原则 5、原则 6 一致。
- **M4 不新增 reverted_validating / failed 状态**：成立。撤销后的重验证由规则①③与审批 CAS 强制，再加计划状态属重复约束。我逐一推演了撤销后的三种失败：构建失败 → 普通修复环（树等于父版本，失败只可能来自环境或抖动，AI 修复的结果仍须重验证）；UT 失败 → 同上；Benchmark 不可比 → 谓词为假，在阈值 gate 处 fail 或审批被拒。三条都有唯一出口。
- **撤销后重验证失败按普通修复流程**：成立。依据同上，且比固定 fail_safe 少丢一个仍可修复的业务 patch。

**"记录更正"核对**：
- HLD 侧三条（M5 的"或保留期过期"、M6 的"10 天"、M1 的 G' 描述）均与 v2.3 正文、调查记录一致，**准确**。
- 01 侧 Y2 更正准确。"pid 被复用即判静默"这条测试原是我方 v0.12 C12-02 提出的，当时写得过强，在此认领。
- 另发现一处新的不准确：处置表裁决②的"这正是 Quickbuild 自身不指定版本时的行为（实测已证实）"，见 H24-01。

---

## B. 第一部分：HLD v2.4 问题清单

### H24-01 [MINOR] 证据等级两处与调查不符：一处写过头，一处写得过于保守

**位置**：§7.6.1"'最新'的含义""提交标记与跟踪"；处置表裁决②

**依据**：
- 调查记录 Q1："历史 RBS 表单默认 `BUILD_TYPE=Full`、`REPO_TYPE=ALL`、**`BUILD_REFERENCE=Ref. Snapshot`**……参考快照下拉只提供当时 reference"；"本次父 Profile Oct-28，子构建根 Oct-13"；Q4："reference 是滚动入口"。
- 调查记录 Q3：已通过 `https://quickbuild.tizen.org/build/1213815/overview`、`/build/1213815/variables` 与 `/build/1213816/variables` **按构建号读取**父 / 子变量。
- §7.6.1："Quickbuild 不显式指定版本时，未覆盖的包取所选 Profile 快照 manifest 中的版本（已证实）。**因此**……'最新'解析为当时最新可用的 Profile 快照"；"按构建号读取为推断方案，`unverified`"。

**问题**：
1. **写过头**。已证实的是"在 Snapshot Number 模式下，未覆盖的包取所选快照的版本"。Quickbuild 表单的缺省是 Ref. Snapshot，取的是滚动 reference，它比最新 Profile 快照旧，并且是经推广的版本。"最新 Profile 快照"是本系统的选择，不是 Quickbuild 的缺省；正文的"因此"与处置表的"正是 Quickbuild 自身……行为"把两者混为一谈。这一点有实际影响：最新 Profile 快照未经推广，快照自身的构建失败会更常见，而这会被记在当前 Run 头上。
2. **写得过于保守**。按构建号读取单个构建的变量，调查已经实际做过。真正未证实的是"按构建号顺序扫描、并识别出属于配置 1917 的构建"——构建号跨配置分配，样本中父 1213815 与子 1213816 相邻。

**候选改动方案**：
```diff
-  - **"最新"的含义（v2.4）**：Quickbuild 不显式指定版本时，未覆盖的包取所选 Profile 快照 manifest 中的版本（已证实）。因此选用 Quickbuild 后端时，snapshot pin 把"最新"解析为**当时最新可用的 Profile 快照**
+  - **"最新"的含义（v2.4）**：Quickbuild 表单缺省为 `Ref. Snapshot`（滚动 reference，已证实）；选择 `Snapshot Number` 时未覆盖的包取所选 Profile 快照 manifest 中的版本（已证实）。本系统**选择**把"最新"解析为当时最新可用的 Profile 快照（区别于 Quickbuild 缺省的 reference：更新但未经推广，快照自身构建失败的概率更高，审批首屏注明"快照未经 reference 推广"）
-（§7.6.1 提交标记）按构建号读取为推断方案，`unverified`
+（§7.6.1 提交标记）按构建号读取单个构建的变量已证实；按构建号顺序扫描并识别属于本配置的构建（构建号跨配置分配）为推断方案，`unverified`
```
**副作用**：无设计改动，只校正证据等级。快照未推广的风险进入审批首屏。

**配套测试/夹具**：FakeQuickbuild 的构建号跨配置交错分配；扫描时须按配置过滤，跳过其他配置的构建。

### H24-02 [MINOR] 首期 Quickbuild 在流水线中实际没有可用角色：拒绝点在运行时、status 未定，风险表与分期也未写明

**位置**：§7.6.1"被测源码身份""A/B 可比性"；§4.2.6；R15；§13 P6

**依据**："该通道的形态与可用性为 `unverified`……未验证或后端不支持时，该后端**拒绝非空 series 的构建**（`backend_source_input_unsupported`）"；"Quickbuild 构建在 P6 补出实际输入证据前只能作**绝对测量**"；R15："可切换本地后端（节点配置）"。

**问题**：两条约束叠加后的结果如下：
- `input: patch` 流水线的 series 必然非空，镜像节点一律被拒；
- `input: none` 的优化专项只有首轮空 series 可以构建，第一个候选之后同样被拒；
- 即使能构建，A/B 也恒为 unverifiable。

也就是说，首期 Quickbuild 只能为空 series 出镜像、做绝对测量。正文给了替代路径（改用本地后端），这一点闭合。但：
1. 拒绝发生在运行时——RPM 阶段跑完、镜像节点分派后才被拒，节点返回哪个 status（image_failed_exhausted？sys.error？）没有写；
2. R15 与 §13 P6 没有写明"P6 验证不通过时，Quickbuild 在流水线中无可用角色"，负责人裁决②的收益完全取决于 P6。

**候选改动方案**：
```diff
+（§4.2.6 追加静态规则）镜像节点选用的后端，其能力声明中 `source_input` ≠ verified，且该节点在图中可能面对非空 series（input: patch，或位于任一 advances 边之后）→ 拒绝加载，提示改配 LocalGbsBackend；后端 `comparison` 能力 ≠ verified，且其镜像被阈值 gate、优化判定或 release_requires 中的 bench_report 消费 → 同样拒绝加载
+（运行时防御）仍发生时返回 image_failed_exhausted(reason = backend_source_input_unsupported)，不进修复环
-| R15 | Quickbuild 不可用或会话频繁失效 | …… | 节点外部等待 + 运维登录；可切换本地后端（节点配置） |
+| R15 | Quickbuild 不可用或会话频繁失效；P6 未能验证暂存输入通道与实际输入证据 | …… | 节点外部等待 + 运维登录；能力未验证时校验器强制改配本地后端——此时 Quickbuild 在流水线中只承担空 series 的绝对测量（P6 gate 记录此结论） |
```
**副作用**：配置错误在加载期暴露，不再在 RPM 阶段之后才失败。负责人对裁决②的预期需要随之调整。

**配套测试/夹具**：CF-DSL：示例一 `backend: quickbuild` 且 source_input = unverified → 拒绝加载；示例二首轮可加载，但 opt_loop 之后的镜像节点会面对非空 series → 拒绝加载；运行时防御返回 image_failed_exhausted 的原因断言。

### H24-03 [MINOR] retried 的"证据链"边界漏掉 ci_plan、Review 与内部基线构建；"broker 返回 release_failed"与核销拒绝的协议不符

**位置**：§4.3.5"清单分类""放行点"

**依据**："**属于当前 series 证据链**（`release_evidence` 中各报告所在 task）的 retried 记录须审批人逐条确认"；"复核不通过则不核销，**broker 返回 release_failed**(reason = `gaps_changed`)"。

**问题**：
1. release_evidence 只收 release_requires 的报告。当前 series 上的 ci_plan（产出被审批的 ReleasePlan）、review_static / review_final，以及为本 Run 提供基线镜像的 `sys.baseline_build`（属于框架内部 Run，其重试甚至不在本 Run 的 retried 清单里），超时重试后都只会被汇总列出或完全不出现。审批人因此看不到"被批准的发布计划本身来自一次超时重试"或"基线镜像构建超时后重试"。
2. 核销复核在编排的 consume 事务内完成，按冻结协议，不核销时由 ledger 级映射关闭，broker 不发送 release_outcome（01 中 release_outcome 恒为"实际执行后"）。"broker 返回 release_failed"这一写法会诱导实现方让 broker 补发 outcome。

**候选改动方案**：
```diff
-**属于当前 series 证据链**（`release_evidence` 中各报告所在 task）的 retried 记录
+**属于当前 series 证据链**的 retried 记录——证据链 = 以当前 series_id 分派的全部 task（含 ci_plan 与 Review）∪ 为 release_evidence 中报告提供基线镜像的 `sys.baseline_build` task（其 retried 记录随基线引用并入本 Run 清单）
-复核不通过则不核销，broker 返回 release_failed(reason = `gaps_changed`)，按 §8.3 固定映射关闭 Run
+复核不通过则不核销：consume 返回 ConsumeRejected(reason = `gaps_changed`)，由编排按 §8.3 的 release_failed 固定映射在 ledger 级关闭 Run（broker 不发 release_outcome）
```
**副作用**：逐条确认的条目略增，但都与本次发布直接相关。

**配套测试/夹具**：ci_plan 超时重试后成功 → 要求逐条确认；基线构建超时重试 → 出现在本 Run 的 retried 中并要求确认；核销复核失败时 broker 未发送 outcome、Run 关闭为 release_failed(gaps_changed)。

### H24-04 [MINOR] 优化计划两处歧义：段 `purpose` 由谁声明（可借此绕过计划）；base_mismatch 与确定性撤销谁优先

**位置**：§7A.4"优化计划""撤销"；§7.6.1"读回校验"

**依据**：§7A.4："series 的每一段**声明** `purpose ∈ {candidate, repair, revert}`"；"计划待验证期间出现……**镜像失败**……只产出确定性撤销 patch"；§7.6.1："不符 → ……镜像节点返回 `image_failed_exhausted`（reason = `base_mismatch`），不经 LogAnalyzer 修复回流……按路由走 fail_safe"。

**问题**：
1. **绕过**。如果 purpose 由提交方自报，Optimization 把候选报成 repair，就不会创建计划，没有优化前后 A/B，D18"收益须实测证明，否则撤销"被绕过：只剩相对基线的回归检查，无收益的优化也能发布。
2. **双出口**。存在未决计划时出现 base_mismatch：按 §7A.4 走撤销（image_fix_patch_ready），按 §7.6.1 走 image_failed_exhausted → fail_safe，两条规则各给出一个出口。

**候选改动方案**：
```diff
-series 的每一段声明 `purpose ∈ {candidate, repair, revert}`
+series 的每一段的 `purpose` 由编排推导、不信载荷：注册为产出 optimization_candidate 的节点提交的段 = candidate（并在同一事务内创建计划）；任一节点提交的、使 tree_digest == 某 rejected_reverting 计划 parent_tree 的段 = revert；其余 = repair
+（§7A.4 撤销追加）base_mismatch 优先于确定性撤销：构建输入不可信时撤销同样无法验证，镜像节点直接返回 image_failed_exhausted(base_mismatch)，计划随 Run 关闭记为 abandoned（审计用，不进入状态机）
```
**副作用**：Optimization 失去"自报 repair"的自由，其所有提交都是候选，这正是 D18 的意图。

**配套测试/夹具**：Optimization 提交段时自报 purpose=repair → 仍按 candidate 处理、创建计划；存在未决计划时 base_mismatch → 唯一出口 fail_safe、不产生撤销段。

### H24-05 [NIT] 准入拒绝后 campaign 模式应返回哪个 status

**位置**：§4.2.6③"创建计划的运行时准入"

**依据**："Optimization 改为返回本 mode 表示无进一步收益的 status（不计为违规）"。

**问题**：campaign 模式下有两个候选值：no_further_gain（asserts_nonempty）与 no_gain_found（none）。选错时，前者在无净变更时会触发 sys.invalid_result。

**候选改动方案**：
```diff
-Optimization 改为返回本 mode 表示无进一步收益的 status（不计为违规）
+Optimization 改为返回本 mode 表示无进一步收益的 status：per_patch → no_further_gain；campaign → 当前 series 相对 snapshot 有净变更时 no_further_gain，否则 no_gain_found（不计为违规）
```
**副作用**：无。**配套测试/夹具**：campaign 下准入被拒，有净变更与无净变更各一例。

---

## D. 第二部分：01 v0.14

### 五条时间线 × 崩溃点 × 阶段期限

| 时间线 | 崩溃点 / 期限 | 出口 | 结论 |
|--------|--------------|------|------|
| T1 正常 | consume / outcome 的 ACK 丢失 | 同 epoch receipt 首响应 | ✓ |
| 〃 | awaiting_consume 到期 | retiring → launcher 回收 → 新实例 → 替代协议 → consume | ✓ |
| 〃 | awaiting_outcome 到期（发布确实耗时） | retiring → 回收（中断在途 push）→ resumed → reconcile → not_happened → Proceed → 再次执行 → **再次到期** | **循环** → C14-01 |
| T2 核销后、发生前崩溃 | lapsed → 回收 → 新实例 | resumed → reconcile not_happened → Proceed → outcome | ✓ |
| T3 发生后崩溃 | 同上 | reconcile happened → released | ✓ |
| T4 indeterminate | 持有者存活，无实例更替 | 周期 release_probe_dispatch → happened / 不发生且持有者已静默 / indeterminate 继续 | ✓ |
| 〃 | probe 报 not_happened 而持有者存活 | retire_requested → 回收 → 新 probe_seq 重探 → 持有者已静默 → release_failed | ✓，只回收一次（granted_epoch 不变，回收后即静默），**不形成循环重启** |
| 〃 | awaiting_probe 到期 | 只重发探测，不触发 retiring | ✓ |
| T5 实例存活、单 task 失联 | awaiting_consume / outcome / reconcile 到期 | retiring → 回收 → 换 epoch → 按阶段恢复 | ✓（但 awaiting_outcome / awaiting_reconcile 同样存在 C14-01 的循环） |
| 〃 | launcher 无法清理 | 不重派、告警、R13 | ✓（全局停摆的代价见 C14-02） |

**只探测命令能否被用于执行发布**：不能。
- Ledger 侧：consume 在 indeterminate 下被拒；outcome 与 reconcile 的 recovery_state 守卫都不放行；C-11a 要求对应 receipt 为 probe 型。
- 载荷侧：ReleaseProbeDispatch 不含 release_plan_ref 与发布内容。
- broker 侧：只构造只读 adapter，FakePublisher 写调用计数恒为 0，并有 CF-AUTH-17f 覆盖篡改 kind 与重放。

token_id 只出现在 fencing 中，它不是 bearer，远端提交信息本来就带有它，不构成执行能力。

### C14-01 [MAJOR] 阶段期限到期 → 回收 → 再执行没有次数上界，正常但耗时的发布会无限循环重启 broker

**位置**：§2.2d"release task 阶段期限""持有者更替重派"；CF-AUTH-20

**依据**："awaiting_consume / awaiting_outcome / awaiting_reconcile 到期仍无该阶段的完成事件 → **task 级失联**：即使实例心跳正常，也将该实例标记 `retiring` 并按上条回收，静默确认后换 epoch 按持有者更替重派恢复；**期限须足以容纳正常发布**"。

**问题**：期限是固定配置，而发布耗时没有上界（大仓 push、gerrit 繁忙、网络慢）。只要某次发布或对账超过期限，就会进入下面的循环：

retiring → cgroup.kill（中断在途 push）→ 新实例 → resumed → reconcile。单目标未完成时报 not_happened → Proceed → 重新执行（awaiting_outcome，期限重新起算）→ 再次超时 → retiring……

awaiting_reconcile 在远端查询慢时同理。全文没有任何次数上界，每一轮都会杀掉 broker 实例，连带中断同实例上其他 Run 的发布。"期限须足以容纳正常发布"只是配置要求，不是协议保证。

**候选改动方案**：
```diff
 - **release task 阶段期限（R13）**：……
+  每个 release task 持久化 `loss_count`（task 级失联次数，随失联判定事务 +1，重启不重置）。`loss_count` 达到 `max_task_losses`（配置，缺省 2）时，该 task **不再参与持有者更替重派与自动执行**：Run 保持 publishing（未核销者保持 running 并停在 release 节点），告警并计入 R13，只经人工裁决（C-11）或运维显式重置后继续。
+  task 级失联只回收**该 task 所在实例**一次；同一实例上其他 task 的阶段期限在新实例接管后重新起算（不累计到它们的 loss_count）。
```
**副作用**：反复超时的发布改由人工处置，不再无限重启。缺省 2 次可容纳一次偶发的慢发布。

**配套测试/夹具**：CF-AUTH-20b：FakePublisher 每次 push 耗时都大于 awaiting_outcome 期限 → 第 2 次失联后不再重派、保持 publishing、告警，且 broker 只被回收 2 次。CF-AUTH-20c：awaiting_reconcile 同理。CF-AUTH-20d：其他 Run 的期限在新实例上重新起算，loss_count 不受影响。

### C14-02 [MINOR] "回收完成才拉起新实例"把一个实例的清理变成全局发布停摆，且对未核销的 task 不必要

**位置**：§2.2d"实例租约"

**依据**："确认 cgroup 为空后才标 `reclaimed`，**再由 launcher 拉起新实例**……无法清理 → 不重派、告警并计入 R13"。

**问题**：静默前置只对**已核销**的 token 有必要（防止新旧实例同时发布）。对**未核销**的 token，epoch fencing 已经保证旧实例无法 consume（v0.12 CF-AUTH-05d 正是"无需静默等待即重派"）。现文把"拉起新实例"放在回收之后：只要 cgroup.kill 卡住（如进程处于 D 状态），全部 Run 的发布都停摆，包括与旧实例毫无关系、尚未核销的 Run；此外，retire_requested 与 task 级失联都会让同实例上的其他 Run 等待整个回收过程。

**候选改动方案**：
```diff
-确认 cgroup 为空后才标 `reclaimed`，再由 launcher 拉起新实例
+launcher 对旧实例写 cgroup.kill 后即可拉起新实例（新 hello → 新 epoch；旧实例的命令已因 retiring / 非当前 epoch 被拒）；旧实例 cgroup 确认为空时才标 `reclaimed`。持有者更替重派仍按授权状态分流：未核销者立即以替代协议重派（不等静默，同 CF-AUTH-05d），已核销者等旧实例 reclaimed 后再重派
```
**副作用**：短时间内两个实例进程并存（旧实例被拒且正被清理），epoch 与静默规则已覆盖这种情形。

**配套测试/夹具**：旧实例 cgroup.kill 卡住时，新实例仍上线，未核销的 Run 正常 consume，已核销的 Run 保持等待并告警。

### C14-03 [NIT] `phase` / `phase_deadline` / `loss_count` 没有所属模型

**位置**：§2.2d；附录 A0

**依据**："每个非终态 release task 持久化 `phase ∈ {…}` 与 `phase_deadline`"。

**问题**：这些字段不属于任何具名模型（01 中没有 release task 的 Ledger 记录模型）；A0 的双向 CI 抽取不到它们，实现方各自建表。

**候选改动方案**：
```diff
+class ReleaseTaskState(BaseModel):                  # Ledger 表（R13，§2.2d）；主键 task_id
+    task_id: str; token_id: str
+    phase: Literal["awaiting_consume","awaiting_outcome","awaiting_reconcile","awaiting_probe"]
+    phase_entered_at: datetime; phase_deadline: datetime; loss_count: int = 0
```
A0 §2.5 增加 ReleaseTaskState。**副作用**：无。**配套测试/夹具**：A0 双向断言覆盖该模型。

---

## 附录：已核对、未发现问题的项

- **证据等级与调查记录一致的部分**：
  - 已证实：单包覆盖、`SNAPSHOT_NUM` 锁定、Add 的样本依据；
  - unverified：Remove、批量覆盖、暂存通道、取消联动子构建、镜像工程；
  - 实际 build.conf 不可得，脚本只读到分支名，因此为 unknown；
  - 保留期按站点公布政策，并注明未核验后台；
  - 已观察到至少 3 个父请求同时运行；
  - "未证实不等于不支持"的措辞。
- **被测源码身份闭合**：读回须证明 series 应用后的实际 tree；只有 base 回显、没有应用证据时，不产成功报告；不得把 patch 提前发布到业务仓；base_mismatch 不进修复环。
- **优化计划**：不可比 → inconclusive → 撤销；撤销提交即 reverted；判定写回在 BenchReport 落账事务内；准入保证撤销容量。撤销后三种失败各有唯一出口（见 A 节）。
- **01 Z2–Z6**：
  - launcher 用 cgroup.kill 回收；静默判据为"租约 reclaimed ∧ cgroup 为空"，覆盖 setsid 逃逸；
  - retiring 实例除 heartbeat 外全部拒绝，§2.2d 与 §5.1 一致；
  - probe 拆为独立出向命令；DispatchReceipt 载荷为判别联合；"至多一个 intent"不分类型；
  - reconciliation worker 合成 `synthetic_worker_loss`；
  - CF-AUTH-09d/09e 已补前置条件；
  - CommandName = 21，与注册表一致；ReleaseProbeDispatch、ReleaseDispatchPayload 已收入 A0。
