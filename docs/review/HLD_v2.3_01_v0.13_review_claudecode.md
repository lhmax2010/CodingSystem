# HLD v2.3（第三轮）+ 01_Contract_Spec v0.13（第十三轮）评审意见 —— Claude Code

- 被审：`docs/00_Framework_HLD_v2.3.md`、`docs/01_Contract_Spec_v0.13.md`
- 背景：`docs/review/HLD_v2.2_review_disposition.md`、`docs/review/01_v0.12_review_disposition.md`、上一轮三家原始意见、`docs/research/quickbuild_business_logic.md`（只读，未访问或探测 Quickbuild）、冻结基线
- 范围：按本轮要求收窄——A 处置落实核对；B A20 所列改动；C 组合场景走查；D 01 v0.13 五条时间线 × 崩溃点
- 方法：HLD v2.2→v2.3 与 01 v0.12→v0.13 全部 diff 块逐一核对；四份示例按 §4.2.6 三条规则手工加载；§7.6.1 逐句对照调查记录 Q1–Q8 的"已证实 / 推断 / 未知"标注
- 只评审、不修改被审文档

## 结论

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| 第一部分：HLD v2.3 | **NO-GO** | 0 | 3 | 4 | 1 |
| 第二部分：01 v0.13 | **NO-GO** | 0 | 1 | 2 | 1 |
| 同步项（单列，不计入第二部分结论） | — | 0 | 0 | 1 | 0 |

## 负责人七项裁决的判断

| # | 裁决 | 判断 | 理由（详见对应条目） |
|---|------|------|--------------------|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | **成立** | 规则③已改用汇合必经，四份示例都能加载（附录走查）；§4.3.5 有了结构保证与两个放行点。剩下的是措辞矛盾（H23-05、H23-08），不影响成立 |
| ② | Quickbuild 默认取最新，在 Run 启动时解析固定 | **有条件成立** | 方向正确，但 v2.3 把"用 Build Package List 锁定全部包"写成已具备，调查只证实了单包覆盖；按调查结果，唯一证实能让全部包落在确定版本的组合是"Profile 快照 + 少量覆盖"。建议把"最新"解析为最新的 Profile 快照 manifest（H23-01） |
| ③ | Profile 严格匹配 + 小改动复用预案 | **成立** | v2.3 已补伪探针前提与非劣开启条件 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | 确定时点、只增不减、最低套件集合都已落地；未采用"拒绝范围外候选"的理由成立 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | 验证资产保护、采纳率与准确率区分已落地；撤销后条目的处理有小缺口（H23-07） |
| ⑥ | Quickbuild 可加 Base CL，否则默认最新；由 Codex 实测 | **有条件成立** | 实测表明 Tizen 侧未确认存在 Base CL 机制（只有 VD 有），构建根 base、build.conf、脚本分支都不可写。"可加 Base CL"这一前提对 Tizen 不成立；v2.3 改为"包 commit + Profile 快照锁定、其余读回"，处理是对的，但部分能力仍写过了头（H23-01） |
| ⑦ | 超时后重试成功可以发布，但每条重试记录须审批人逐条确认 | **有条件成立** | 重试成功是真实的测试结果，由人做最终判断，这一点合理。但现文要求确认 Run 内**每一条** retried，包括早已被取代的 series 上的记录，与放行无关的确认会稀释注意力，最后变成一路点"确认"；确认也没有绑定到记录内容。代价：审批人工作量与 Run 内重试次数成正比；拒绝即整个 Run 作废、须新建 Run。改法见 H23-04 |

---

## A. 上一轮处置落实核对

| 处置 | 正文落点 | 核对结果 |
|------|---------|---------|
| M1 规则③汇合必经 + 运行时兜底 | §4.2.6③ | 已落实。但规则①的定义句仍写"**汇合必经（仅用于本规则）**"，与③的"适用于规则①与规则③"冲突 → H23-08 |
| M2 规则②净变更数据流 | §4.2.6② | 已落实；"汇合处"的取交范围有歧义 → H23-06 |
| M3 超时放行点 + 负责人裁定 | §4.3.5、§8.2 | 已落实；登录等待超时的处理三处说法不一 → H23-05；retried 确认范围 → H23-04 |
| M4 会话等待分阶段 | §4.3.4 | 已落实；submit_uncertain 依赖的标记 probe 不成立 → H23-01 |
| M5 cancel_pending | §4.3.4 | 已落实 |
| M6 Quickbuild 改写 | §7.6.1、§7.6.2 | 大体忠实于调查；三处写过了头 → H23-01 |
| M7 BenchPolicy 非劣 | §7A.3 | 已落实（上界、两类区间、方向统一、空集合不完整、BCa 退化） |
| M8 OptimizationPlan | §7A.4 | 已落实；组合场景下有无出口的情形 → H23-02；容量规则在示例一上被反例击穿 → H23-03 |
| M9 目标范围 | §7A.7 | 已落实；未采用 Codex 方案的理由成立 |
| M10 Profile v2 | §7.8 | 已落实 |
| M11 验证资产保护 | §7A.0 原则 6 | 已落实；撤销后的条目处理 → H23-07 |
| M12 D22 不可变基底 | D22 | 已落实（五条共同契约） |
| M13 CLI cgroup | §7.1 | 已落实；E0 已列 cgroup v2 预检 |
| N1–N10 | 各节 | 均已落实（含 exclude_boards、§13 P2/P4/P7、R 编号顺序）；附录 B 第 7 组仍残留 v2.2 的 `unpinned_inputs` → H23-08 |
| 01 Y1–Y7 | §2.2d、§2.5、§5.1、A0 | Y1、Y4–Y7 已落实并验证闭合；Y2、Y3 的新机制在 indeterminate × 实例未更替组合下不闭合 → C13-01 |

处置表中"未按评审方方案修改"之处，取舍理由均成立：
- M1：合并采用两家方案；
- M2：数据流采用 Codex 的方法，范围采用 Kimi/CC 的限定；
- M3：负责人折中两家；
- M9：未采用"拒绝范围外候选"；
- M10：采用非劣而非等价检验；
- Y3：通道采用 CC 的方案。

---

## B/C. 第一部分：HLD v2.3 问题清单

### H23-01 [MAJOR] §7.6.1 把调查未证实的三项能力写成已具备

**位置**：§7.6.1"可锁定的输入""读回""A/B 可比性""提交标记与跟踪"；§5.2 远程构建效应类别；§4.3.4 会话等待 `submit_uncertain`

**依据（调查记录原文）**：
- Q1："`BUILD_PKG_LIST_MODIFY`……作用是给目标包指定提交。历史样本覆盖一条 libtirpc"；"**没有验证**完全空白的 Live/Partial 提交、缺省 commit、重复 repo、ADD/MODIFY/RM 冲突的服务器处理"；"MODIFY 留空时，未新增的包保留所选 Profile manifest 的 revision"（已证实）。
- Q6："Recent Builds 只显示最近 10 个……也**没有证据表明列表支持服务端按备注全文搜索**"；"取消……未点击……停止是否联动子任务、何时释放资源未知"。
- Q4："父日志……多次克隆 `master`"；Q3："最终 worker 实际消费的 build.conf 字节摘要仍未知"；"manifest 与变量相符……**不能**单凭它证明每个包重新编译且没有使用缓存"。
- Q5："本次 Base 样本 `TARGET_IMAGE` 为空，目录没有 images"。

**问题**：
1. **全量锁定没有证实**。v2.3 写"每个包的 Git 版本——Build Package List……逐行，一律取自本 Run snapshot manifest"。snapshot 按 gerrit 的"最新"解析，与任何一个 Profile 快照都不同，这意味着要经 MODIFY 覆盖大量包。调查只证实了覆盖单个包，大批量覆盖、重复 repo 的处理都属"未验证"。真正证实过的组合是"Profile 快照决定全部包版本 + MODIFY 覆盖少数包"。
2. **按标记 probe 是有窗口的**。§5.2 写远程构建"可 probe——……Gateway 转发与远端查询均以该标记精确归因"，§4.3.4 的 `submit_uncertain` 规定"必须先按效应标记 probe"。但调查表明，标记只能在 Recent Builds 的 10 条窗口内逐个读取父构建变量来匹配，没有服务端搜索。观察到同一配置有 3 个并发运行；会话失效常常持续数小时，窗口必然滚过，此时既无法证明"已提交"，也无法证明"未提交"。结果只能是 indeterminate → 远程构建不可安全重放 → unknown → sys.error。"确认未发生后方可新版本提交"在窗口外永远不可达。
3. **脚本版本的处理自相矛盾**。读回项写"**可得时**的脚本版本"，可比性又要求"任一不同或**读不回** → unverifiable"。调查只读到 `QB_SCRIPTS_BRANCH=master`，没有读到 commit。若读不到即判 unverifiable，Quickbuild 下的 A/B 永远不可比，示例一换成 Quickbuild 后端后 bench_gate 恒为 fail；若读不到就忽略，则在可变分支上默认等价，等于静默放行。
4. **镜像能力未调查**。被调查的配置 1917 不产镜像；可产镜像的工程（Unified）的锁定字段与读回没有调查过，而 `build_image` 正是 Quickbuild 后端在流水线中的用途。
5. **两处没有如实写明**：取消是否联动子构建，§4.3.4 的 cancel_pending 只跟踪单一作业；源码缓存使"包版本一致"不等于"重新编译"，可比性判据没有提到这一点。

**候选改动方案**：
```diff
-  - **可锁定的输入（提交时显式携带）**：① 每个包的 Git 版本——表单 Build Package List（回显 `BUILD_PKG_LIST_MODIFY`）逐行 `仓库路径@完整 commit`，**一律取自本 Run snapshot manifest 中该仓的 commit**……
+  - **可锁定的输入（调查已证实的组合）**：使用 Quickbuild 后端时，snapshot pin 把"最新"解析为**最新可用的 Profile 快照**：其 manifest 即本 Run snapshot manifest 的全部包版本（本地 RPM 阶段使用同一份）；`SNAPSHOT_NUM` 锁定该快照；开发者显式指定的少数包版本经 Build Package List 覆盖（调查证实单包覆盖；批量上限与冲突处理属 P6 验证项，超出验证范围的提交形态不得使用）。
-  - 读回……可得时的脚本版本
+  - 读回……脚本版本：读得到 commit 时参与可比性比较；读不到时判为 config_tradeoff（后端能力声明：脚本分支不可锁定），并在 ImageReport 中标 `scripts_unpinned`，A/B 两侧须在同一提交窗口内（两侧父构建开始时刻之差 ≤ 配置值）——可比性结论注明"脚本分支未锁定"，不冒充完全可比
+  - **probe 窗口（如实声明）**：标记只能在 Recent Builds（10 条）或按构建号逐个读取变量来匹配。提交 intent 持久化"提交前该配置的最大构建号"；probe 按构建号自该值向上逐个读取 `BUILD_NOTES`（推断方案，P6 验证），上限为构建记录保留期 30 天。提交不确定且超出可扫描范围 → indeterminate。远程构建登记为"可 probe（有界）"，§5.2 同步改写
+  - **镜像工程**：调查只覆盖不产镜像的配置 1917；产镜像工程的锁定字段与读回在 P6 前另行只读调查，结论出来前 QuickbuildBackend 的 `build_image` 标为 provisional
+  - 取消：cancel_pending 跟踪父 trigger 及其全部子构建，全部到达终态才归还配额；包版本一致不代表重新编译，ImageReport 记录可得的缓存使用迹象
```
**副作用**：首期 Quickbuild 下的"最新"会比 gerrit HEAD 旧，落后量等于 Profile 快照的发布间隔，需在审批首屏注明。probe 能力降为有界，长时间会话失效会更多地以 unknown 结束，代价是需要人工核对。脚本未锁定改为可确认的取舍，避免 bench_gate 恒为 fail。

**配套测试/夹具**：FakeQuickbuild 增加四项能力：
- Recent Builds 10 条窗口与按构建号读取；
- 窗口滚过后 probe 得 indeterminate、按构建号扫描后命中；
- 脚本 commit 读不到时报 scripts_unpinned，可比性不判失败；
- 父 trigger 取消后子构建仍在运行时，配额不归还。

此外，P6 gate 增加"批量覆盖 N 包"的真实提交验证项（需经负责人确认）。

### H23-02 [MAJOR] 组合场景下 OptimizationPlan 有无出口的状态：unverifiable 的判定映射、reverted 的迁移时点都未定义

**位置**：§7A.4"收益判定""撤销"；§7.6.1"A/B 可比性"；§4.2.6① BenchReport 谓词

**依据**：§7.6.1："任一不同或读不回 → `comparison = unverifiable`：比较类判定字段缺失……**不得用于优化收益判定**"；§7A.4："gain → `accepted`；其余 → `rejected_reverting`"；"撤销完成**且重验证通过后**计划迁 `reverted`"；"存在 `pending_validation` 或 `rejected_reverting` 计划时，Optimization 返回 `no_further_gain` / `no_gain_found` → `sys.invalid_result`"；①："BenchReport = `gate_eligible` ∧ `comparison ≠ none` ∧ ……"。

**问题**（组合场景走查见附录 C，下列为其中的无出口点）：
1. **优化前后 A/B 为 unverifiable 时没有 opt_verdict**。"不得用于优化收益判定"没有说映射到哪一值。如果实现成"不产出 opt_verdict"，计划停在 pending_validation：Optimization 不能返回 no_further_gain（invalid），不能撤销（撤销只在 rejected_reverting 下发生），已达 max_opt_rounds 也不能建新计划。唯一出口是 sys.invalid_result → fail_safe，已通过验证的业务 patch 因环境原因被判为 Agent 违规。
2. **"重验证通过后迁 reverted"没有执行者，也没有判据**。计划状态只在 series 推进事务内迁移，而重验证通过并不推进 series。撤销后的常规 A/B 若为 unverifiable，"通过"与否不确定，计划就停在 rejected_reverting，Optimization 的下一次返回同样落入 invalid。
3. **BenchReport 谓词放进了 unverifiable**。① 只排除 `comparison = none`，unverifiable 满足谓词。在没有阈值 gate 的发布流水线中，这条报告会被当作"通过"的 Bench 证据；按 §7.6.1 它应作为 environment_gap 由人确认。目前两处表述不一致。

**候选改动方案**：
```diff
 （§7A.4 收益判定）
-并由框架写回计划记录：gain → `accepted`；其余 → `rejected_reverting`
+并由框架写回计划记录：gain → `accepted`；neutral / loss / inconclusive → `rejected_reverting`；**优化前后 A/B 为 unverifiable 时 opt_verdict = inconclusive**（原因 `comparison_unverifiable`），同样迁 `rejected_reverting`——收益不可证明即撤销
 （§7A.4 撤销）
-撤销完成且重验证通过后计划迁 `reverted`。
+撤销段提交的 series 推进事务内计划迁 `reverted`（撤销是确定性的树回退，判据是 tree_digest == plan.parent_tree，与后续重验证结果无关）；撤销后 series 的重验证结论按常规报告处理，不再影响计划状态。
 （§4.2.6 ①）
-BenchReport = `gate_eligible`（§7A.3）∧ `comparison ≠ none` ∧ 未 `baseline_revoked` ∧ 不存在未决优化计划
+BenchReport = `gate_eligible`（§7A.3）∧ `comparison = verified` ∧ 未 `baseline_revoked` ∧ 不存在未决优化计划；`comparison = unverifiable` 时谓词为假，**除非**该条目已作为 environment_gap 在 acknowledged_gaps 中确认（此时以"已确认的不可比"满足谓词，release_evidence 明确标注）
```
**副作用**：环境原因导致收益不可证明时，候选一律撤销，这是保守取向，代价是在 Quickbuild 环境漂移时少拿一次可能的收益。BenchReport 增加 `comparison` 三值：verified / unverifiable / none。

**配套测试/夹具**：
- 优化前后 A/B 为 unverifiable → opt_verdict=inconclusive → 撤销 → 撤销提交即 reverted → Optimization 返回 no_further_gain 合法；
- 撤销后常规 A/B 为 unverifiable 时计划不卡在 rejected_reverting；
- 无阈值 gate 的发布流水线中，unverifiable 未确认则审批被拒、确认后通过且 release_evidence 带标注。

### H23-03 [MAJOR] 修复环容量 ≥ 1 + max_opt_rounds 不足以兑现"不让已验证业务 patch 落入 fail_safe"，示例一即可构造反例

**位置**：§4.2.6③"预算容量"；§7A.4"轮次自限"；示例一 `image_fix_loop: max_rounds: 2`、`max_opt_rounds: 1`

**依据**：③："可能承载确定性撤销的修复环……`max_rounds ≥ 1 + max_opt_rounds`（至少保留一次普通修复，外加每个候选至多一次确定性撤销）"；§7A.4："环预算只作防御兜底，正常路径不触顶，不会因'还想再优化'而让已通过验证的业务 patch 落入 fail_safe"。

**问题**：环计数在整个 Run 内累计，而 ≥ 1 + max_opt_rounds 只在"业务修复至多用 1 轮"时才能留出撤销的位置。反例（示例一原文）：
1. 业务 patch 在镜像阶段先后两次失败、两次 AI 修复，image_fix_loop 计数 2/2，这是合法用法；
2. 之后 UT、Benchmark 通过，Optimization 创建计划 P1；
3. P1 的候选在镜像阶段失败，需要确定性撤销，经 image_fix_patch_ready 回流，这是第 3 次通过环边，被拦截 → fail_safe。

已通过全部验证的业务 patch 因一次优化尝试而丢失，正是该句承诺不会发生的事。同理适用于 rpm_fix_loop 与 ut_fix_loop。

**候选改动方案**：
```diff
 （§4.2.6 ③ 预算容量之后追加）
+**创建计划的准入（运行时，确定性）**：Optimization 提交 purpose=candidate 的 series candidate 时，编排在同一事务内核对：优化环剩余次数 ≥ 2，且优化重验证路径上每个修复环的剩余次数 ≥ 1；不满足 → 拒绝创建计划（`E-PLAN-NO-CAPACITY`），Optimization 必须返回 no_further_gain / no_gain_found（此时不计为违规）。静态容量规则保留，作为"至少能尝试一个候选"的配置下限。
 （§7A.4 轮次自限）
-环预算只作防御兜底，正常路径不触顶，不会因"还想再优化"而让已通过验证的业务 patch 落入 fail_safe。
+由准入检查保证：任何已创建的计划都必然有撤销所需的环容量，因此不会因"还想再优化"而让已通过验证的业务 patch 落入 fail_safe。
```
**副作用**：业务修复用满环预算后，本 Run 不再尝试优化，少一次优化机会，换来保证成立。Optimization 需要从 candidate 提交被拒的响应中得知原因。

**配套测试/夹具**：示例一中 image_fix_loop 用满 2/2 后，Optimization 提交 candidate → E-PLAN-NO-CAPACITY → no_further_gain，Run 继续走到审批；剩余 1 时允许创建计划，候选镜像失败后撤销成功、不触顶；rpm_fix_loop、ut_fix_loop 各一例。

### H23-04 [MINOR] retried 的确认范围与绑定（裁决⑦的落地条件）；核销复核失败的出口未定义

**位置**：§4.3.5"清单分类""放行点"；§8.2；§8.3 核销

**依据**：§4.3.5："发布路径上**每条** retried 记录都须审批人逐条确认后才可发布"；"**核销事务（§8.3）再次复核同一条件**，防止审批与核销之间新增条目"。

**问题**：
1. retried 覆盖整个 Run，包括已被后续 series 取代的轮次。例如 S1 上的编译超时重试，与 S4 上的发布证据毫无关系，却同样要求逐条确认，审批人的注意力被稀释。
2. 确认没有绑定到记录内容（超时位置、时长、最终通过报告的 digest），重放旧确认可以覆盖内容已变的条目。
3. 核销复核失败时走哪条路径没有写：是授权失效 → release_failed，还是撤回审批 → 重新等待？reason 也没有登记。

**候选改动方案**：
```diff
-发布路径上每条 retried 记录都须审批人逐条确认后才可发布
+发布路径上，**属于 release_evidence 中各报告所在 task**（即当前 series 的证据链）的 retried 记录须逐条确认；其余 retried（被取代 series 的轮次）在首屏汇总呈现、不要求逐条确认
+acknowledged_gaps 每项 = (条目 id, 条目内容 digest)；审批与核销两次复核均按 digest 比对，内容变化即视为未确认
+核销复核发现新增或变化条目 → 不核销，按 C-09② 关闭为 release_failed（reason = `gaps_changed`），FeedbackReport 列出差异
```
**副作用**：审批负担只与证据链上的重试相关。核销复核失败的 Run 关闭后须新建 Run，因为冻结映射不允许回到等待。

**配套测试/夹具**：S1 上的 retried 不要求逐条确认、只出现在汇总中；证据链上的 retried 未确认 → 审批被拒；确认后条目内容 digest 变化 → 核销以 `gaps_changed` 拒绝。

### H23-05 [MINOR] Gateway 登录等待超时：三处说法不一

**位置**：§4.3.5"超时一律不放行"；§4.3.4"会话等待"；§8.6"会话失效期间"

**依据**：§4.3.5："外部等待超时（`external_timeout_min` 与 Gateway 登录等待超时）……由编排固定路由 fail_safe（DSL 不提供其出边字段）"；§4.3.4："超过配置的登录等待上限 → 编排为对应 task 合成 `sys.timeout`（进入超时报告）"；§8.6："……合成 `sys.timeout`，**按节点重试策略处理**"。

**问题**：按 §8.6，可以重试。可是重试的新 attempt 面对的是同一个失效的会话，又会登记新的会话等待；登录等待时钟是重新计时还是继续累计，文中没说。按 §4.3.5，则固定 fail_safe、不可重试。两种读法给出两个不同的出口。

**候选改动方案**：
```diff
-（§8.6）超过配置的登录等待时长 → 编排为对应 task 合成 `sys.timeout`，按节点重试策略处理。
+（§8.6）超过配置的登录等待时长 → 编排为对应 task 合成 `sys.timeout` 并固定路由 fail_safe（不经节点 retry，§4.3.5）。
```
§4.3.4 同步改写。**副作用**：会话长期失效的 Run 不再靠重试拖延。

**配套测试/夹具**：登录等待超时且节点配置了 `retry: [sys.timeout]` → 仍直接 fail_safe，超时报告类别为 gateway_session。

### H23-06 [MINOR] 规则②数据流的"汇合处"取交范围不明

**位置**：§4.2.6②

**依据**："经过 `none` 的边保持不变；**汇合处**取各来源的共同结论"。

**问题**：DSL 中"汇合"通常特指 join，而数据流分析必须在**每个多前驱节点**（含环回边的目标，如 compile_rpm）取交，并以"已证明"为初值做最大不动点迭代。如果只在 join 处取交，示例二中 compile_rpm 来自 opt_patch_ready（重置为未证明）与 build_fix_patch_ready 两条入边的结论就无定义。

**候选改动方案**：
```diff
-汇合处取各来源的共同结论
+在每个有多条入边的节点（含 join 与环回边目标）对全部入边结论取交（"已证明" ⊓ "未证明" = "未证明"）；以 entry 为"未证明"、其余节点为"已证明"作初值，迭代至不动点
```
**副作用**：无。**配套测试/夹具**：validator property：随机含环图上，数据流结论与"每条路径上最后一条 advances 之后必有 asserts_nonempty"的枚举判定一致。

### H23-07 [MINOR] 被撤销的候选留下的 verification_asset_change 条目仍要求确认

**位置**：§7A.0 原则 6"验证资产保护"；§7A.4 撤销

**依据**："series candidate 受理时对 AI 产出的段计算是否触及验证资产；命中时……作为 `verification_asset_change` 条目要求审批人逐条确认"。

**问题**：检查按段、在受理时做，没有随撤销复核。候选改了 `%check`、之后被确定性撤销，当前树已不含该改动，条目却仍在 incomplete 中要求确认，徒增噪声。反过来，后续 AI 修复段若把被撤销的改动又带回来，会在新段上再次命中，这一点没有问题。

**候选改动方案**：
```diff
-series candidate 受理时对 AI 产出的段计算是否触及验证资产
+series candidate 受理时对 AI 产出的段计算是否触及验证资产；审批前按"当前树相对 snapshot 的净 diff 中归属 AI 段的部分"重算——已被撤销、不在净 diff 中的触及项降为多版本对比报告中的历史记录，不再要求确认
```
**副作用**：需要按 hunk 归属计算，用的仍是确定性 diff 规则。

**配套测试/夹具**：候选改 `%check` 后被撤销 → 审批时无该确认项、对比报告中仍可见；AI 修复段把它重新引入 → 要求确认。

### H23-08 [NIT] 残留措辞

**位置**：§4.2.6①；附录 B 第 7 组"报告与消息"；示例一

**问题**：
1. 规则①定义句仍写"**汇合必经（仅用于本规则）**"。
2. 附录 B 第 7 组仍列"Quickbuild 锁定 base 的 snapshot manifest 扩展与 `unpinned_inputs`"，这是 v2.2 的概念，v2.3 已改为读回与 `comparison = unverifiable`。
3. 四份示例都没有配置 `retry`，§4.3.5 的 retried 路径没有任何示例覆盖（§11.3 的测试可以补上，不影响结论）。

**候选改动方案**：
```diff
-**汇合必经（仅用于本规则）**
+**汇合必经（适用于规则①与规则③）**
-Quickbuild 锁定 base 的 snapshot manifest 扩展与 `unpinned_inputs`
+Quickbuild 的 snapshot manifest 扩展（Profile 快照编号、逐包 commit）与读回字段
```
**副作用**：无。**配套测试/夹具**：无。

---

## 附录 C：组合场景走查（第一部分）

前提：示例一，`compile_image.config.backend = quickbuild`，`compile_rpm` 配置 `retry: { on: [sys.timeout], max: 1 }`，`max_opt_rounds: 1`。

| 步 | 事件 | 状态 / series / 计划 | 清单（retried / incomplete） | 备注 |
|----|------|------|------|------|
| 1 | submit_patch（改模块 Ma） | queued；S1；范围 {Ma} | — | 首次 submit 时确定范围 |
| 2 | compile_rpm(S1) attempt1 超时，attempt2 成功 | running | retried: R1（S1 编译） | 未覆盖的超时为空 |
| 3 | compile_image(S1)（Quickbuild）→ 读回 R(S1) → fan-out [ut, review_static]，activation A1 | — | — | — |
| 4 | ut(S1) 失败；无未决计划 → AI 修复改到模块 Mb | S2（repair）；范围 {Ma, Mb}；ut_fix_loop 1/2；A1 被退役 | R1；若触及 protected_paths → verification_asset_change V1 | review_static(S1) 晚到 → stale |
| 5 | S2 重新编译、出镜像；fan-out A2；ut(S2) 含 Mb 用例 → 通过 | — | — | 范围增长生效 |
| 6 | benchmark(S2)：常规 A/B | — | — | 分三种变体，见下 |
| 7 | optimize 建计划 P1 → S3（candidate） | P1 pending_validation；opt_loop 1/2 | — | 准入见 H23-03 |
| 8 | S3 编译、UT 通过；benchmark(S3) 做优化前后 A/B | — | — | 变体 V2 中此 A/B 为 unverifiable |
| 9 | P1 被判 loss / inconclusive → Optimization 撤销 → S4（revert，树 = S2） | P1 rejected_reverting；opt_loop 2/2 | V1 是否仍要求确认 → H23-07 | — |
| 10 | S4 重验证；optimize → no_further_gain → bench_gate → join → review_final → ci_plan → human_review | P1 何时 reverted → H23-02 | — | — |

三种变体的结局：

- **V1：常规 A/B 不可比**。步 6/10 中 regression_pct 缺失 → bench_gate fail → fail_safe。只有一个出口，没有静默放行。FeedbackReport 首节为 environment_gap（不可比的原因：base 快照编号不同），多版本对比报告附带 S1–S4。
- **V2：常规 A/B 可比，优化前后 A/B 不可比**。现文中 opt_verdict 无定义，计划卡在 pending_validation，只能经 sys.invalid_result → fail_safe，这是无出口的状态（H23-02）。按 H23-02 修正后：inconclusive → 撤销 → 撤销提交即 reverted → no_further_gain → 进入审批。
- **V3：全部可比，进入审批**。审批首屏应呈现：
  - 验证范围 {Ma, Mb}，以及"范围增长：Mb 由 S2 的 AI 修复引入"；
  - 受影响但不在范围内的反向依赖模块；
  - 多版本对比报告：基线 / S1 / S2 / S3（P1 被拒，附 opt_verdict）/ S4；
  - 需逐条确认的项：V1（若仍在净 diff 中）；R1 按现文须逐条确认，按 H23-04 只做汇总；
  - Quickbuild 读回的 base 快照编号与 config_tradeoff 声明。

  审批人逐条确认后才可批准；核销时再复核一次；发布后只登记 pending。
- **附加反例**：若步 4 之前业务已在镜像阶段修复两次，步 8 中候选镜像失败时，撤销会超出 image_fix_loop → fail_safe（H23-03）。

**双出口检查**：同一时刻能产生 patch 的只有 bench 分支，review_static 不产 patch。UT 触发的撤销与 Optimization 触发的撤销按计划状态互斥：UT 失败时，计划处于 pending_validation，由 UT 撤销；Bench 判定后才由 Optimization 撤销。未发现双出口。

---

## D. 第二部分：01 v0.13 问题清单

### 五条时间线 × 崩溃点

| 时间线 | 崩溃点 | 出口 | 结论 |
|--------|--------|------|------|
| T1 正常 | consume / outcome 的 ACK 丢失；hello 响应丢失后新 socket 重放 | receipt 首响应；hello 每次先绑定连接 | 恰一出口 ✓（CF-AUTH-11、21） |
| T2 发布前崩溃 | receipt=intent（受理前 / 受理后 ACK 前 / ACK 后落账前）× 已核销与未核销；替代事务前后 kill；替代后发送前又换实例 | 规则 (a)/(b) 互斥；替代协议；已核销先等静默 | 恰一出口 ✓（Y1 闭合） |
| T3 发布后崩溃 | 同 T2 | resumed → reconcile happened → released | 恰一出口 ✓ |
| T4 indeterminate | 持有者实例**崩溃**后上线新实例 | 新 hello 扫描 → probe_only → C-11a | 恰一出口 ✓ |
| 〃 | 持有者实例**存活** | 无人发出 probe_only；并在发布时限到期后被判为 task 级失联 | **无自动出口，且可能循环** → C13-01 |
| T5 实例存活、task 失联 | 未核销 / 已核销 / 执行中 | retiring → supervisor 清理 → 新实例 → 替代协议 / 恢复臂 | 恰一出口 ✓，但 supervisor 无定义（C13-02）；indeterminate 时见 C13-01 |
| 〃 | 实例无法清理 | 不重派、告警、R13 人工 | 恰一出口 ✓ |

**probe_only 能否被用来执行发布**：在 Ledger 侧不能。consume 有 ④ 的 `recovery_state ≠ indeterminate` 守卫，release_outcome 有 `recovery_state ∈ {none, execution_permitted}` 守卫，reconcile 只在 reconcile_required 下受理，三条执行权路径全部关闭。但 broker 侧没有结构保证：probe_only 的 dispatch 携带 token_id 与 release_plan_ref，broker 进程本身持有凭据。一个执行了发布的 broker 只要上报 `confirmed_happened`，就会被映射为 released → C13-03。

### C13-01 [MAJOR] probe_only 通道在实例未更替时无人驱动；task 级失联判据把 indeterminate 当作失联，会循环重启 broker

**位置**：§2.2d"实例租约""indeterminate 锁存""持有者更替重派"；C-11a；CF-AUTH-17、20

**依据**："重派扫描对 indeterminate 者……改发 `mode = probe_only`……indeterminate → 记录、**按周期继续**"；"编排在**受理新 broker 实例的 broker_hello 后**，扫描……"；"单个 release task 超过配置的发布时限仍无 outcome / reconcile 结果（task 级失联）→ 编排将该实例标记 `retiring`"。

**问题**：
1. **通道无人驱动**。probe_only 的唯一发送点是"新实例 hello 后的扫描"。最常见的 indeterminate 来自存活的 E2 自己上报（多目标部分出现），之后不再有实例更替，也就不会发出任何 probe_only。"按周期继续"没有驱动者，C-11a 不可达，T4 又只剩人工裁决。
2. **会误判为失联并循环**。indeterminate 的 task 天然"无 outcome / reconcile 结果"（这两条命令都已被锁存禁止），发布时限到期就会触发 retiring：清理 E2、启动 E3，E3 收到 probe_only，若远端仍为部分出现，再报 indeterminate，时限再次到期，再次 retiring……broker 被循环重启，每一轮都会中断同实例上其他 Run 正在进行的发布。
3. **计时起点不明**。"发布时限"从何时起算（dispatch、核销还是许可），没有定义。

**候选改动方案**：
```diff
-- **indeterminate 锁存（R12）**：……重派扫描对 indeterminate 者**不发可执行的 release_dispatch**，改发 `mode = probe_only`……indeterminate → 记录、按周期继续。
+- **indeterminate 锁存（R12，R13 补驱动）**：……probe_only 的发送点有两个：① 新实例 hello 后的扫描；② **编排的周期任务**——对 recovery_state = indeterminate 的每个授权，按 `probe_interval`（配置）向当前 live 实例写 DispatchReceipt（mode = probe_only）并送达。两者都受"同 token 至多一个 intent"约束。C-11a 的 indeterminate 结果只记录，由下一周期继续。
-单个 release task 超过配置的发布时限仍无 outcome / reconcile 结果（task 级失联）→ 编排将该实例标记 `retiring`
+单个 release task 自最近一次 execute 型 dispatch 送达（DispatchReceipt.completed_at）起，超过配置的发布时限，仍无该阶段应有的结果（running：consume；publishing ∧ recovery_state ∈ {none, execution_permitted}：release_outcome；reconcile_required：reconcile_report）→ task 级失联 → retiring。**recovery_state = indeterminate 的 task 不适用**（其期待的是 probe 结果，由 probe 周期驱动，probe 超时只重发 probe_only，不触发 retiring）
```
**副作用**：编排增加一个周期任务。indeterminate 状态下 broker 不再被反复重启；远端长期部分出现时仍由人工（C-11）收尾，并计入 R13。

**配套测试/夹具**：CF-AUTH-17e：E2 存活并报 indeterminate 后无实例更替 → 周期任务发出 probe_only → 报 happened 时映射 released；报 not_happened 时因 E2 存活不静默而返回 ILLEGAL-STATE、继续周期。CF-AUTH-20b：indeterminate 的 task 超过发布时限 → 不 retiring。CF-AUTH-20c：发布时限从 completed_at 起算的边界值。

### C13-02 [MINOR] supervisor 的身份、权限与 kill 机制未定义；retiring 的拒绝范围两处不一

**位置**：§2.2d"实例租约"；§5.1 处理序③

**依据**："由框架 supervisor 终止并清理该实例进程组后启动新实例"；§2.2d："立即拒绝其后续**执行类命令**"；§5.1 ③："其余 broker 入向命令要求已握手、连接 epoch 为当前 epoch 且实例非 retiring"。

**问题**：编排以自己的 UID 无权向 broker UID 的进程组发信号（HLD §7.1 v2.3 已就 CLI 承认这一点）。supervisor 是谁、以什么权限 kill、如何避免与 systemd 的自动重启竞争，都没有说。另外，retiring 下拒绝"执行类命令"还是"除 hello 外全部命令"，两处不一致；heartbeat 与 release_probe_report 是否被拒，答案也不同。

**候选改动方案**：
```diff
-由框架 supervisor 终止并清理该实例进程组后启动新实例
+由 deploy 特权 launcher（HLD §8.5，与 CLI / 构建边界同一 cgroup v2 契约）对该实例的 cgroup 写 `cgroup.kill`，确认 cgroup 为空后启动新实例（systemd 单元配置为由 launcher 拉起，不自行重启）
-立即拒绝其后续执行类命令
+立即拒绝其除 heartbeat 外的全部命令（与 §5.1 ③ 一致；heartbeat 仍受理，仅用于判定进程是否仍存活）
```
**副作用**：broker 的部署形态由 launcher 管理。静默判据可以增加"cgroup 为空"，比 pgid 扫描更强。

**配套测试/夹具**：retiring 实例的 release_probe_report / outcome → FORBIDDEN，heartbeat 受理；broker 子进程 setsid 逃逸进程组后，cgroup.kill 仍将其清除。

### C13-03 [MINOR] probe_only 不能执行发布，只在 Ledger 侧有保证，broker 侧没有结构约束

**位置**：§5.1 ReleaseDispatch、ReleaseProbeReport；§2.2d

**依据**：`ReleaseDispatch{…, token_id, mode: "execute"|"probe_only"}`；`ReleaseProbeReport` 注释"只查远端、从不执行"。

**问题**：probe_only 的 dispatch 带有执行所需的全部输入（token_id、release_plan_ref），broker 持有凭据。broker 若有缺陷，在 probe_only 下补完了一次部分发布并报 confirmed_happened，Ledger 会把它映射为 released，indeterminate 就被"执行"而非"观测"消解了，而审计上无法区分。

**候选改动方案**：
```diff
-class ReleaseDispatch(BaseModel): run_id: str; task_id: str; release_plan_ref: ArtifactRef; token_id: str; mode: Literal["execute","probe_only"] = "execute"
+class ReleaseDispatch(BaseModel): run_id: str; task_id: str; release_plan_ref: ArtifactRef; token_id: str; mode: Literal["execute"] = "execute"
+class ReleaseProbeDispatch(BaseModel): run_id: str; task_id: str; probe_targets: tuple[ReleaseTarget, ...]; fencing: FencingInfo; probe_seq: int   # 不含 token_id 与 plan 引用
+# 部署契约：broker 处理 ReleaseProbeDispatch 时只构造只读 adapter 客户端（不加载写凭据原语）；conformance 断言 probe 路径上 FakePublisher 写调用计数 = 0
```
命令注册表与 A0 同步（出向分为两条命令或判别联合）。**副作用**：出向模型拆分，CF-IPC-10 的出向用例同步。

**配套测试/夹具**：probe 路径上调用写原语 → conformance 失败；probe_only dispatch 中不存在 token_id。

### C13-04 [NIT] 残留表述

**位置**：§2.2(c)；§5.1"出向"

**问题**：
1. (c) 仍写"自动周期 probe 得出确定结论 → 等同对应 broker outcome"，但 C-11 已改为仅人工裁决，自动定论已移到 C-11a。
2. §5.1"**出向**：编排→broker `release_dispatch{run_id, task_id, release_plan_ref, token_id}`"缺少 mode 字段。

**候选改动方案**：
```diff
-；自动周期 probe 得出确定结论 → 等同对应 broker outcome（……）
+；自动定论见 C-11a（probe_only 通道）
-release_dispatch{run_id, task_id, release_plan_ref, token_id}
+release_dispatch{run_id, task_id, release_plan_ref, token_id, mode}（或按 C13-03 拆分）
```
**副作用**：无。**配套测试/夹具**：无。

---

## 同步项（核对 HLD 附录 B 第 7 组后未登记者；不计入第二部分结论）

已逐条核对第 7 组，v2.3 新增项大多已登记，只有下列一项未登记：

| # | 严重程度 | HLD v2.3 | 01 v0.13 现文 | 建议落点 |
|---|---------|---------|--------------|---------|
| S-01 | MINOR | §4.2.6②：submit_patch 以 `E-SKILL-EMPTY-SERIES` 拒绝无净变更 series；分派需要 patch 的节点前做净变更复核，无净变更 → fail_safe 并记 environment_gap；§4.3.5：非发布路径结论 `succeeded_with_gaps`；核销复核失败的 reason（若采纳 H23-04 则为 `gaps_changed`） | §2.7 错误码表无 E-SKILL-EMPTY-SERIES；ResultEnvelope 无结论字段；ConsumeRejected.reason 无对应值 | 补入第 7 组"入口"与"状态机与等待"条目，随 01 同步 |

---

## 附录：已核对、未发现问题的项

- **四份示例加载**：
  - 示例一：规则③在 G'（从 compile_rpm 出发、删去指向 fail_safe 的边）上，must'(human_review) 经汇合必经包含 compile_rpm、compile_image、ut、benchmark，且依次出现，通过；规则①通过；规则②不适用（input: patch）；容量 rpm 3 / image 2 / ut 2 ≥ 1+1，opt 2 ≥ 2×1，静态通过（运行时问题见 H23-03）。
  - 示例二：规则③通过；规则②数据流中 ci_plan 入口为"已证明"（经 no_further_gain，之后无 advances）；容量 rpm 3 / image 3 / ut 3 ≥ 1+2，opt 4 ≥ 2×2。
  - 示例三、四：无 release、无优化，V-15 中镜像节点支配 benchmark，通过。
- **规则②的撤销 / 修复 / 优化交替**：示例二中，"候选 C1 被接受 → 候选 C2 被撤销 → 树回到 C1"时，asserts_nonempty 的运行时检查仍成立；"全部撤销 → 无净变更"只能返回 no_gain_found，进入 terminal；静态证明在每条 advances 之后正确重置。
- **BenchPolicy**：上界非劣、两类区间、方向统一、空集合判为不完整、BCa 退化判 inconclusive、opt_verdict 用区间，均自洽。我方上一轮认领的低功效放行问题已消除。
- **D22 / CLI cgroup / cancel_pending**：契约完整（cancel_pending 跟踪子构建一点见 H23-01）。
- **01 Y1**：替代协议、superseded 状态、发送前复核 epoch、晚到 ACK 只记审计，CF-IPC-10 覆盖充分。
- **01 Y2**：身份由 SO_PEERCRED + /proc 取得；静默判据写明"编排不是父进程"的含义。
- **01 Y4 / Y5 / Y6 / Y7**：hello 例外与每连接绑定、按 socket 角色处理协议错误、A0 补项、排序，均已落实。
- **CommandName = 20**：与注册表一致。
