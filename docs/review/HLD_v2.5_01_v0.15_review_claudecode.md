# HLD v2.5（A22 核对）+ 01_Contract_Spec v0.15（第十五轮）定向核对意见 —— Claude Code

- 被审：`docs/00_Framework_HLD_v2.5.md`（只核对附录 A22 所列改动）；`docs/01_Contract_Spec_v0.15.md`（只核对 A3 中 v0.15 一条）
- 背景：`docs/review/HLD_v2.4_review_disposition.md`、`docs/review/01_v0.14_review_disposition.md`、上一轮三家原始意见、`docs/research/quickbuild_business_logic.md`（只读，未访问或探测 Quickbuild）
- 方法：v2.4→v2.5 与 v0.14→v0.15 全部 diff 块逐一核对；五条时间线 × 崩溃点 × 阶段期限 × 失联上界逐格推演
- 只评审、不修改被审文档

## 结论

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| 第一部分：HLD v2.5（A22） | **GO** | 0 | 0 | 3 | 1 |
| 第二部分：01 v0.15 | **NO-GO** | 0 | 1 | 0 | 1 |
| 同步项（单列，不计入第二部分结论） | — | 0 | 0 | 0 | 0 |

同步项：v0.15 的改动都属于 01 自身的协议细化（cgroup 绑定、失联上界、ReleaseTaskState），没有新的 HLD 范围项；A22 新增的加载期能力检查、证据链与 `gaps_changed` 已登记在附录 B 第 7 组。

## 负责人七项裁决的判断

| # | 裁决 | 判断 | 理由 |
|---|------|------|------|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | **成立** | 本版未改动 |
| ② | Quickbuild 默认取最新，在 Run 启动时解析固定 | **有条件成立** | 证据措辞已校正：缺省是 Ref. Snapshot，"最新 Profile 快照"是本系统的选择，落后量标 unknown。**代价写了一半**：写明了"未经 reference 推广"，但漏了调查中直接可见的另一项代价——Profile 快照与构建根 base 是两条输入链（样本中 Profile 为 Oct-28，构建根仍为 reference Oct-13）。取最新 Profile 会把"新源码对旧构建根"的错位拉大，这类环境性构建失败会落在当前 Run 头上。另外，"快照自身的构建失败更常见"是推断，正文写成了事实（H25-01） |
| ③ | Profile 严格匹配 + 小改动复用预案 | **成立** | 本版未改动 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | 本版未改动 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | 段 purpose 改由编排推导，堵住了自报绕过；推导规则的优先级仍有缺口（H25-02） |
| ⑥ | Quickbuild 可加 Base CL，否则默认最新 | **成立** | 已知构建号读取标已证实，扫描与按配置过滤标 unverified，镜像能力不外推，均与调查一致 |
| ⑦ | 超时后重试成功可发布，须审批人确认 | **成立** | 证据链扩至当前 series 的全部 task 与提供基线的 sys.baseline_build；核销复核失败改为 ConsumeRejected + ledger 级映射，协议表述已与 01 一致 |

---

## A. 处置落实核对

| 处置 | 正文落点 | 核对 |
|------|---------|------|
| Q1 证据措辞 | §7.6.1 | 已落实，逐条对照调查记录 Q1/Q3/Q5/Q6 一致；代价说明不全 → H25-01 |
| Q2 加载期能力检查 | §4.2.6、§7.6.1、R15、P6 | 已落实；四份示例均选用本地后端，不会被误拒（附录）；措辞精度 → H25-04 |
| Q3 证据链与 gaps_changed | §4.3.5、§8.3 | 已落实 |
| Q4 purpose 推导、base_mismatch 优先 | §7A.4 | 已落实；推导规则的优先级与 pending 下的非撤销段 → H25-02；base_mismatch 后 terminal 出口 → H25-03 |
| Q5 campaign status | §4.2.6③ | 已落实 |
| W1 cgroup 子树 populated=0 | §2.2d、§2.5 | 已落实（launcher 崩溃、同名重建、读取失败均有处理，CF-AUTH-09c/09f） |
| W2 失联上界 | §2.2d、ConsumeRejected、CF-AUTH-20d/20f | 已落实；但上界只计"阶段期限到期"，实例崩溃路径不计 → C15-01 |
| W3 新实例不等回收 | §2.2d、CF-AUTH-20e | 已落实 |
| W4 出向按 execute / probe 分述 | §5.1、CF-IPC-10 | 已落实，与 §2.2d、C-11a 一致 |
| W5 ReleaseTaskState | §2.5、A0 | 已落实，A0 已收录 |

**两处取舍理由**：
- **① 未核销 task 达到上界后以 release_failed 关闭（未采用我方"停在发布节点"）**：成立。我方原方案写"只经人工裁决或运维重置"，但 C-11 只对 publishing 开放，running 下没有裁决入口，确实是无出口。授权从未核销，按协议不可能发生过发布，同事务撤销授权后关闭是安全的：之后任何实例的 consume 都会因 revoked 被拒。代价是审批成果作废、须新建 Run，可以接受。我方原方案在此撤回。
- **② 新实例拉起不等旧实例回收（未采用 Codex"须在回收证明后启动"）**：成立。我逐项核对了三条安全性质：
  - 单一当前实例：新 hello 使 epoch +1，旧实例因 retiring 且非当前 epoch，全部命令被拒；
  - 已核销者等待静默：重派扫描仍以 reclaimed ∧ populated=0 为前置；
  - 负向映射等待静默：C-11a 照旧。

  新旧实例各有专属 cgroup，旧子树的判定不受新实例影响。未核销 token 在旧实例上无法 consume，因此不会被执行，新旧实例并存期间不存在双重执行。

**"记录更正"**：
- HLD 侧两条（裁决②的缺省、M1 的构建号读取证据等级）与调查记录一致，**准确**。
- 01 v0.14 处置表无记录更正一节，无需核对。

---

## B. 第一部分：HLD v2.5（A22）问题清单

### H25-01 [MINOR] 裁决②的代价只写了"未经推广"，漏了 Profile 与构建根的错位；"失败更常见"把推断写成事实

**位置**：§7.6.1"'最新'的含义"

**依据**：
- 调查记录 Q1："base 快照 URL……决定构建根依赖仓库，不等于每个待构建包的 Git revision"；Q4："**Profile 与 base 是两条输入链**——本次父 Profile Oct-28，子构建根 Oct-13……只固定 Profile 不足以证明 base 固定"。
- §7.6.1："它比 reference 新，但未经 reference 推广，**快照自身的构建失败更常见**"。

**问题**：
1. 选 Snapshot Number 模式后，源码取最新 Profile，构建根仍是 reference，两者差距被拉大。新源码对旧构建根二进制依赖的错位，是这一选择的直接代价：构建失败可能来自错位而非 patch，并会进入 LogAnalyzer 修复流程，引出不必要的 AI 修复。正文没有写。
2. "失败更常见"没有调查证据，只能作为推断。

**候选改动方案**：
```diff
-它比 reference 新，但未经 reference 推广，快照自身的构建失败更常见，审批首屏注明"快照未经 reference 推广"。
+它比 reference 新，但未经 reference 推广（快照自身构建失败率是否更高为推断，未经统计）；且构建根仍由 reference 决定（调查 Q4：Profile 与构建根是两条输入链），源码与构建根的版本差距随之拉大——新源码对旧构建根的错位可能导致与 patch 无关的构建失败。审批首屏注明"快照未经 reference 推广"与 Profile / 构建根两者的快照编号；ImageReport 与 BuildReport 失败时附该差距，供 LogAnalyzer 区分环境性失败（不对其产出修复 patch，返回 *_failed_exhausted(reason = env_skew_suspected)，待 P6 以真实数据确定判据）。
```
**副作用**：对推断性失败多一个保守出口，代价是少一次自动修复机会。

**配套测试/夹具**：FakeQuickbuild 设 Profile 与构建根编号不同 → 审批快照中两编号均可见；判定为 env_skew_suspected 的失败不进修复环。

### H25-02 [MINOR] purpose 推导缺优先级：Optimization 的撤销段可能被判为 candidate；pending 计划下 Compiler / UT 的非撤销段没有被拒绝

**位置**：§7A.4"优化计划"中的 purpose 推导

**依据**："注册为产出 `optimization_candidate` 的节点提交的段 = candidate（同一事务内创建计划）；任一节点提交、使 tree_digest == 某 `rejected_reverting` 计划或待验证计划失败时的 `parent_tree` 的确定性撤销段 = revert；其余 = repair"；"计划待验证期间出现构建失败……只产出确定性撤销 patch"；"一个待验证计划的后续修复段继续归属该计划"。

**问题**：
1. **撤销被误判为候选**。Optimization 在 `rejected_reverting` 下提交的撤销段，同时满足第一条（优化节点提交）与第二条（回到 parent_tree）。若按书写顺序先判 candidate，就会为撤销段创建新计划；若此时准入已不足，撤销会被 `E-PLAN-NO-CAPACITY` 拒绝，计划卡在 rejected_reverting，Optimization 的下一次返回落入 sys.invalid_result。这是新的无出口路径。
2. **pending 下的修复段**。计划待验证时，Compiler / UT 提交的若不是撤销段，会被归为 repair 并"继续归属该计划"——这正是"只产出确定性撤销"要禁止的 AI 修复，推导规则把它接受了下来。
3. 初始 series（submit_patch 外部提交）的 purpose 未定义。

**候选改动方案**：
```diff
-注册为产出 `optimization_candidate` 的节点提交的段 = candidate（同一事务内创建计划）；任一节点提交、使 tree_digest == ……的确定性撤销段 = revert；其余 = repair。
+按以下顺序判定（先命中者为准）：① 存在 rejected_reverting 计划，或存在待验证计划且本次提交来自其失败的构建 / 镜像 / UT 节点，且 tree_digest == 该计划 parent_tree → revert（不创建计划、不受准入约束）；② 存在待验证计划时，Compiler / UT 节点提交的、不满足 ① 的段 → series_candidate_submit 拒绝（E-CANDIDATE-NOT-REVERT）；③ 注册为产出 optimization_candidate 的节点提交 → candidate（同事务创建计划并做准入核对）；④ 其余 → repair。初始 series 的段 purpose = initial。
-一个待验证计划的后续修复段继续归属该计划
+（删除：按 ② 待验证计划下不存在修复段）
```
**副作用**：Compiler / UT 在待验证计划下失去 AI 修复的可能，这本就是原意。

**配套测试/夹具**：
- 准入已不足时 Optimization 提交撤销 → 判为 revert、不被拒，计划迁 reverted；
- pending 下 Compiler 提交非撤销段 → E-CANDIDATE-NOT-REVERT；
- 初始 series 的段为 initial。

### H25-03 [MINOR] base_mismatch 优先后，若 image_failed_exhausted 被路由到 terminal，pending 计划会使 terminal 成功被拒且没有出口

**位置**：§7A.4"base_mismatch 优先于确定性撤销"；§4.2.6③"运行时兜底"

**依据**："镜像节点直接返回 `image_failed_exhausted`(reason = base_mismatch) 走 fail_safe……未决计划**随 Run 关闭**在审计中记为 abandoned"；"未决优化计划存在时，审批决定与 terminal 成功均被拒绝"。

**问题**："走 fail_safe"依赖路由配置；DSL 允许把 `image_failed_exhausted` 路由到 Review terminal（汇总失败原因的子集流水线很常见）。此时计划仍为 pending（只在 Run 关闭时才记 abandoned），terminal 成功被兜底规则拒绝，而"被拒绝之后怎样"没有定义，Run 停在 running。

**候选改动方案**：
```diff
-镜像节点直接返回 `image_failed_exhausted`(reason = base_mismatch) 走 fail_safe，不产生撤销段；未决计划随 Run 关闭在审计中记为 abandoned（不进入计划状态机）。
+镜像节点直接返回 `image_failed_exhausted`(reason = base_mismatch)，不产生撤销段。
+（§4.2.6③ 运行时兜底）未决优化计划存在时，审批决定被拒绝；terminal success_on 命中时不关闭为 succeeded，而由编排按 C-12 路由 fail_safe（reason = pending_plan_at_terminal），未决计划在审计中记为 abandoned
```
**副作用**：terminal 路径多一个确定性出口。

**配套测试/夹具**：image_failed_exhausted 路由到 terminal、pending 计划下 base_mismatch → closed(fail_safe, pending_plan_at_terminal)。

### H25-04 [NIT] 加载期能力检查的措辞

**位置**：§4.2.6"另（v2.5，后端能力的加载期检查）"

**依据**："该节点可能面对非空 series（`input: patch`，或**位于任一 `advances` 边之后**）"。

**问题**：
1. "位于……之后"应写成路径语义：存在一条从 entry 经过 advances 边到达该节点的路径。
2. 四份示例能通过，前提是 LocalGbsBackend 的 source_input 与 comparison 声明为 verified，正文没有明写。

**候选改动方案**：
```diff
-（`input: patch`，或位于任一 `advances` 边之后）
+（`input: patch`，或存在一条从 entry 经过某条 `advances` 边到达该节点的路径）；LocalGbsBackend 的 source_input 与 comparison 能力声明为 `verified`（全部输入由本系统控制）
```
**副作用**：无。**配套测试/夹具**：四份示例原文在 local 后端下通过；示例二把 compile_image 改为 quickbuild 时被拒（opt_loop 之后可面对非空 series）。

---

## D. 第二部分：01 v0.15

### 五条时间线 × 崩溃点 × 阶段期限 × 失联上界

| 时间线 | 情形 | 出口 | 结论 |
|--------|------|------|------|
| T1 正常 | ACK 丢失 / hello 重放 | receipt 首响应 | ✓ |
| 〃 | awaiting_consume 到期，loss < 上界 | retiring → kill → 新实例（不等回收）→ 立即替代重派 | ✓ |
| 〃 | awaiting_consume 到期，loss = 上界 | 同事务撤销授权 → release_failed(dispatch_loss_exhausted) | ✓ |
| 〃 | awaiting_outcome 到期，loss < / = 上界 | 等旧实例 reclaimed → resumed → 对账；达上界 → 保持 publishing，人工裁决 | ✓ |
| 〃 | 期限与完成事件竞争 | phase CAS 互斥；失联先提交时，后到的结果被连接守卫拒绝 | ✓ |
| T2 核销后、发生前崩溃 | lapsed → kill → 新实例 → 等 reclaimed → resumed → not_happened → Proceed → 执行 | 一次性崩溃时 ✓；**同一 task 每次执行都致 broker 崩溃时无上界** | **循环** → C15-01 |
| T3 发生后崩溃 | 同上 → happened → released | ✓ |
| T4 indeterminate | 周期探测；not_happened 且持有者存活 → retire_requested（至多一次）→ reclaimed 后重探 → release_failed | ✓，不循环 |
| 〃 | awaiting_probe 到期 | 只重发探测 | ✓ |
| T5 实例存活、单 task 失联 | 同 T1 各行；同实例其他 task 重派不计次 | ✓ |
| 〃 | 旧实例无法回收（D 状态） | 新实例照常服务；已核销 task 告警、R13；未核销 task 正常重派 | ✓ |

**新旧实例并存期间有无双重执行**：没有。
- 旧实例为 retiring 且非当前 epoch，consume、outcome、reconcile 都被③拒绝；
- 已核销的 token 只在旧实例 reclaimed ∧ populated=0 后才重派；
- 未核销的 token 在旧实例上无法核销，因此不会被执行。

**只探测通道**：v0.15 写明"未核销或非 indeterminate 的 probe 属非法组合，编排拒绝生成"，与 C-11a 一致。

### C15-01 [MAJOR] 失联上界只计"阶段期限到期"；broker 在某个 task 上反复崩溃（lapsed 路径）不计次，仍会无限循环

**位置**：§2.2d"失联次数上界""实例租约"

**依据**："`loss_count`（**以本 task 阶段期限到期判定的失联次数**……）"；"同一实例上其他 task 因该实例被回收而随之重派时，其新阶段由重派事务重新写入，`loss_count` 不增加"；"连接关闭且超过租约时长未续期 → `lapsed`……lapsed 与 retiring 实例进入同一回收流程"。

**问题**：W2 的上界只覆盖"实例活着、task 不回话"。另一种同样常见的形态是"毒丸 task"：某个发布计划触发 adapter 缺陷，broker 每次执行都会崩溃。

1. 实例崩溃后进入 lapsed，回收后拉起新实例；
2. 重派扫描把该 task 当作"因实例被回收而随之重派"，重写阶段、不计 loss；
3. resumed → reconcile not_happened → Proceed → 再次执行 → 再次崩溃。

这个循环在 01 中没有任何上界，launcher 也没有重启退避。每一轮都会中断同实例上其他 Run 的发布——正是 W2 要消除的那类循环，只是换了触发方式。

**候选改动方案**：
```diff
 - **失联次数上界（R14）**：……
+  另计 `interrupt_count`：实例因 lapsed 或 retiring 被回收时，该实例上处于**执行可能阶段**（awaiting_outcome，或 execution_permitted 下的 awaiting_outcome）的每个 task，在回收提交事务内 +1（不处于执行阶段的 task 不计）。达到 `max_task_interrupts`（配置，缺省 3，大于 max_task_losses，以容纳无辜同实例 task 的连带中断）→ 与失联上界同样处理：已核销者保持 publishing、只经人工裁决；未核销者不会处于执行阶段，不受此计数影响。
+  launcher 对 broker 的拉起施加指数退避（连续 N 次在 T 内 lapsed 即告警并停止自动拉起，计入 R13），防止与 task 无关的启动即崩溃耗尽资源。
```
ReleaseTaskState 增 `interrupt_count: int = 0`，A0 同步。

**副作用**：与毒丸 task 同实例的无辜 task 也会被计数，但阈值更高；最坏情况下，一个无辜 task 在三次连带中断后转人工，这是有界的代价。

**配套测试/夹具**：
- CF-AUTH-20g：FakePublisher 对某个计划每次执行都令 broker 进程崩溃 → 第 max_task_interrupts 次中断后不再重派、保持 publishing、告警；broker 被拉起次数有上界。
- CF-AUTH-20h：无辜 task 在同实例上被连带中断两次后，正常完成，计数不影响其结果。
- CF-AUTH-20i：launcher 退避——启动即崩溃时停止自动拉起并告警。

### C15-02 [NIT] "broker 的全部后代不得迁出该子树"缺少可检查的部署约束

**位置**：§2.2d"实例 cgroup 绑定"

**依据**："broker 的全部后代不得迁出该子树"。

**问题**：cgroup v2 中，进程能否迁出取决于对目标 cgroup 的 `cgroup.procs` 与共同祖先的写权限。正文只写了要求，没有写由什么保证。一旦部署给了 broker UID 对外部 cgroup 的写权限，populated=0 的判定就会被迁出的进程绕过。

**候选改动方案**：
```diff
-broker 的全部后代不得迁出该子树
+broker 的全部后代不得迁出该子树：部署契约要求 broker UID 只对本实例子树内的 cgroup 有委派写权限，对子树外任何 `cgroup.procs` 无写权限（deploy 检查项，conformance 断言迁出尝试失败）
```
**副作用**：无。**配套测试/夹具**：CF-IPC-03 增"broker 进程尝试迁出到父 cgroup → EACCES"。

---

## 附录：已核对、未发现问题的项

- **§7.6.1 证据措辞**：以下几点与调查记录逐条一致：
  - 缺省为 Ref. Snapshot，并注明"只代表所调查配置取证时的缺省"；
  - 落后量标 unknown，并写明"快照内单包版本可能远旧于发布日期"；
  - 已知构建号读取已证实；按构建号扫描、按配置过滤、缺号与权限缺失为 unverified；
  - 1917 样本未产镜像、其他组合未证实。
- **加载期检查不误拒示例**：四份示例均为 `backend: local`。示例二把 compile_image 改为 quickbuild 时被拒，属于预期，因为首轮之后会面对非空 series。只做空 series 绝对测量的 Quickbuild 流水线可以加载。
- **retried 证据链**：当前 series 的全部 task 加提供基线的内部构建，边界完整。修复 patch 的产出 task 属上一 series，其重试影响的是 patch 的产生而非验证，汇总列出即可。
- **01 W1**：专属 domain cgroup，绑定由 launcher 写入；populated=0 递归覆盖子树；"已请求 kill"与"子树已空"分开；同名重建不沿用旧证明（cgroup_generation）；读取失败或超时不判 reclaimed。
- **01 W3 / W4 / W5**：新实例上线与三条安全性质见 A 节；出向按 execute / probe 分述与 C-11a 一致；ReleaseTaskState 与 BrokerInstanceLease 已收入 A0。
