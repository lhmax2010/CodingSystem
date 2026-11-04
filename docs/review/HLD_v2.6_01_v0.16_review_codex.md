# HLD v2.6 / 01 v0.16 定向复审 — Codex

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.6（仅 A23） | **NO-GO** | 0 | 1 | 0 | 1 |
| 第二部分：01 v0.16（仅 A3 的 v0.16） | **NO-GO** | 0 | 2 | 0 | 0 |
| 新增同步项（不计入第二部分） | 无；B 第7组已有项目不重复报 | 0 | 0 | 0 | 0 |

## 负责人七项裁决的独立评估

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时必须出报告 | **成立** | 本版不放宽同 series 汇合、超时记录及未覆盖 timeout 的禁止发布。并行不需要改回串行；代价仍是完整保存两路证据与被替代历史。 |
| ② | Quickbuild 取最新并固定 | **成立** | 现在明确是本系统策略，服务缺省仍是 Ref. Snapshot；推广状态按证据显示，失败率增加标为推断，并揭示Profile源码与构建根的两条输入链。取更新快照可能把环境不匹配问题带入Run，但没有伪造推广状态或HEAD落后上界。代价说明已足够支持此选择，不等于Quickbuild能力已验收。 |
| ③ | Profile v1 严格匹配，v2 小改动复用预案 | **成立** | 未改变v2缺省关闭、非劣评估及工具链兼容条件。真实评估和重采成本仍须承担，不以文档通过代替工具实测。 |
| ④ | 目标模块登记与相关范围验证 | **成立** | 本版没有通过撤销缩小范围。terminal遇未决计划失败关闭是生命周期兜底，不是免除验证；代价是失败Run不能借汇总节点显示成功。 |
| ⑤ | 用测试结果与多版本报告检验 AI | **成立** | 四步purpose的类别与优先级合理，禁止未决计划期间的普通修复堵住自报绕过。H26-01要求将计划变更重新放回series完成事务，才能兑现此设计；不改变以实测收益决定采纳的原则。 |
| ⑥ | 显式 base 预检与读回核对 | **成立** | absolute-only非发布gate不再被误要求A/B能力；混合/未知依赖仍保守拒绝，镜像和源码能力独立检查。代价是能力不足仍需改配本地后端，不能用人工确认替代实际输入证明。 |
| ⑦ | 重试成功可发布，须审批人确认 | **成立** | 本版未缩减当前series全部task、所用基线构建及历史重试的可见性，确认摘要与核销复核保留。代价仍是审批信息量与跨Run基线证据保留，不必恢复“曾超时永久不得发布”。 |

## 范围、输入与方法

评审开始执行 `git pull --rebase`，返回 Already up to date；输入HEAD为 `d221970606d4207b158e01eef8cf8d6a37301936`。阅读上一轮两份处置表、三家原始意见和Quickbuild研究记录，核对两个版本的全部diff及直接冲突条款。未读取本轮其他评审方结论，未访问或探测Quickbuild，未修改被审文档。

| 输入 | SHA-256 |
|---|---|
| `docs/00_Framework_HLD_v2.6.md` | `dd79de5258b76a2ee25f46d9874eeb740b88a0be37305547986cb80a87acffc5` |
| `docs/01_Contract_Spec_v0.16.md` | `00747399a6df2e8ddf4d6ca846f3dfe9e6cb1f326a6d35982909d7479b75f78a` |
| `docs/review/HLD_v2.5_review_disposition.md` | `9255a0157dd9a0b42daae832ec495aa7ab2dc44ffe4e9e38abeda0ef51021a17` |
| `docs/review/01_v0.15_review_disposition.md` | `602cf82fbbd012cc38441b1663142b5266d6c54b6598489aafa77f6623a56103` |
| `docs/research/quickbuild_business_logic.md` | `33104bb3c1f70d5f196b83c7f02b5b664db5c0da512a56cf49738164498763c3` |

验证方式为文档/状态机走查及只读小脚本反例演算。原文四份YAML均能解析、均使用local；123个class均被A0收录，21个CommandName与三列注册表集合相等。脚本演算四步purpose分支和lapsed各阶段的计数，不是运行尚待实现的产品校验器或conformance；未声称真实launcher、Quickbuild、板子已验收。

## A. 处置逐项核对

### HLD

| 条目 | 落实与结论 |
|---|---|
| R1 | §7A.4、B-7、§11.3已有revert优先、只认当前未决计划、未决计划非撤销提交拒绝、无未决时新candidate、initial独立标记。分类重叠已修；但新增“受理事务”使计划先于series迁移，H26-01。删去旧归属句后仍有残留措辞，H26-02。 |
| R2 | §4.2.6按指标依赖要求comparison，absolute-only例外可确定；无法解析保守按A/B；source_input按entry经advances到镜像的路径检查；local三项能力明确verified。主要修订完整，旧夹具文字清理见H26-02。 |
| R3 | §7.6.1推广状态三类证据显示、推断标注、Profile与实际构建根编号均落实。部分采纳理由成立，见下。 |
| R4 | §4.2.6③、§7A.4和§11.3定义pending_plan_at_terminal失败关闭，计划审计abandoned；不再依赖terminal成功被拒后自行寻找后继。落实。 |

处置表正文实际为R1–R4四个合并项，开头“归并为5个独立问题”应改为4，归H26-02；本轮没有凭这个计数差异虚构第五条处置。

**部分采纳的判断：成立。** 研究证明Profile源码与构建根base可以不同，不证明“某次失败一定由版本差距导致”。在没有确定性判据时，以 `env_skew_suspected` 自动停止AI修复会把推断变成控制规则。首期展示两套版本、保留日志、遵守修复预算且让所有修复重验证，属于完整的当前决策；P6以后另行制定判据是后续增强，不是把当前失败出口留空。这不放宽 `base_mismatch`、源码输入不支持等已有明确的禁止修复分支。

### 01

| 条目 | 落实与结论 |
|---|---|
| V1 | recovery_mode=manual_only、C-11/§5.1人工入口和全量probe结果约束、CF-AUTH-20j均落实。明确发生/未发生不再被unknown guard堵住；本方C15-01关闭。 |
| V2 | phase_generation、owner_epoch、timer_armed、当前live实例、到期CAS消费一次、同实例解除、waiting_holder不运行执行期限、替换幂等及CF-AUTH-20h均落实。本方C15-02的旧期限重复计loss问题关闭。 |
| V3 | interrupt_count/max_task_interrupts覆盖awaiting_outcome、awaiting_reconcile的lapsed与连带中断；launcher退避已落文。执行阶段毒丸有界，但awaiting_consume漏计及首次hello前启动失败仍未覆盖，C16-01/02。 |
| V4 | CF-AUTH-20和CF-IPC-10输出列按未核销execute、已核销execute、probe和耗尽分支区分。本方C15-03关闭。 |
| V5 | 实例子树委派、外部cgroup.procs无写权限、CF-IPC-03迁出EACCES均落文。与专属子树绑定及populated递归证明一致；部署须在新旧实例并存时也实际满足，不只检查某个父目录的权限。 |

两份本轮背景处置表均无单列“记录更正”节；本报告不声称核验了不存在的章节。01的三条MAJOR来源和两条NIT来源与上轮原始意见相符。

## B. 第一部分问题

### H26-01 — MAJOR：purpose 的新事务位置使计划早于 series 提交，崩溃后可出现“已撤销但代码未撤销”

**位置**：HLD v2.6 §7A.4“优化计划”四步判定；直接冲突于§4.2.4及同节“撤销”的series推进事务要求。

**依据**：新增文本是“**series candidate受理事务内按以下顺序判定**”，①随后写“**同事务计划迁reverted**”，③写“**通过则同事务创建计划**”。但§4.2.4规定“**编排进程在task完成事务内一次完成——父版本CAS……series lineage + latest指针推进**”且“**candidate预分配不改变current series**”。§7A.4开头和撤销条款也仍要求在series推进事务内创建/迁移计划。

**问题/反例**：P已rejected_reverting、current仍是优化候选S1。Optimization提交回到父树的candidate，受理事务按新增文字将P置reverted；随后worker在task_complete前崩溃。此时current仍S1，撤销段未被采用，P却已结束。反向情形是新候选仅暂存就创建pending_validation计划，但current尚未含候选；重试或父CAS失败后可能拒绝新的非撤销提交。两处事务不能同时成为权威迁移点；新规则不能通过把候选预提交视为series提交来覆盖冻结模型。

**候选 diff**：

```diff
--- docs/00_Framework_HLD_v2.6.md §7A.4
+++ docs/00_Framework_HLD_v2.6.md §7A.4
- series candidate受理事务内按以下顺序判定、先命中者为准：
+ 四步为编排的互斥分类规则。candidate受理时做预校验并保存推导结果、
+ expected_parent及关联plan_id；此时不创建/迁移OptimizationPlan、不推进series。
+ 权威复核在§4.2.4的task完成/series推进事务内：校验父CAS、当前计划、
+ purpose与候选容量，成功时与lineage/current推进一起原子创建或迁移计划。
- ①……同事务计划迁reverted
+ ①……在上述完成事务内计划迁reverted；撤销不执行新候选容量准入。
- ③……通过则同事务创建计划
+ ③……预校验不足时仍返回E-PLAN-NO-CAPACITY；完成事务复核成功才创建计划。
+ 父CAS失败、候选作废、task失败或仅候选受理后崩溃，不改变权威计划状态；
+ 重放以既有candidate/完成receipt恢复，不重复创建计划或累计候选轮数。
```

**副作用**：分类需预校验和提交复核两次，但不增加第二个权威状态源；保留可提前返回准入不足的接口。若需要预约容量，应作为可回收预约单独定义，不能用pending_validation充当未提交候选的预约。四步优先级及“不让提交方自报purpose”的决定不变。

**测试/夹具**：candidate受理前后、task_complete前后逐点kill；撤销受理后worker崩溃时仍为S1+rejected_reverting，完成提交后才为S2+reverted；新候选受理后崩溃不产生权威计划；父CAS失败、并行候选、旧attempt候选作废；同id完成重放计划数和轮数均只增加一次。

### H26-02 — NIT：已替换规则的修复段、gate夹具和处置计数仍有残留

**位置**：HLD v2.6 §7A.4“撤销”、§11.3“v2.5追加”；HLD_v2.5_review_disposition.md开头。

**依据**：§7A.4已写“**待验证计划期间不存在修复段**”，下一条仍说撤销“**包含该候选之后叠加的修复段**”。§11.3旧组仍要求“**可比性unverified而镜像被阈值gate消费→拒绝加载**”，新组已经允许absolute-only非发布gate。处置表说“归并为**5**个独立问题”，实际只有R1–R4。

**问题**：最新专门规则可以消除解释歧义，故不另升为机制缺陷，但按字面生成夹具会得到相反的absolute-only预期；修复段句也会让实现者误以为还有一条被允许的pending修复路径。

**候选 diff**：

```diff
--- docs/00_Framework_HLD_v2.6.md
+++ docs/00_Framework_HLD_v2.6.md
- 回到plan.parent_tree，包含该候选之后叠加的修复段
+ 回到plan.parent_tree；未决期间不接受普通修复段，不存在需一并撤销的后续repair段
- 可比性unverified而镜像被阈值gate消费→拒绝加载
+ 可比性unverified且gate消费A/B依赖字段→拒绝加载；absolute-only按v2.6组通过
--- docs/review/HLD_v2.5_review_disposition.md
+++ docs/review/HLD_v2.5_review_disposition.md
- 归并为5个独立问题
+ 归并为4个独立问题（R1–R4）
```

**副作用**：仅消除残留，不改四步规则或新增状态。**测试/夹具**：合并旧/新能力测试向量，保证同一absolute-only输入只有一个期望；pending下repair拒绝用例保留；历史A20变更记录描述旧版行为，无需把历史重写成新版。

## C. HLD 改动面走查

以下分类结果以H26-01修正后的**series完成事务**为权威点；分类本身已不重叠。

| 路径 | 唯一分类/出口 |
|---|---|
| 开发者submit_patch初始段 | initial，走原初始series受理事务；input:none初始空series没有patch段，不凭空生成repair。 |
| 无未决计划的普通Compiler/UT修复 | repair；producer仍保留真实来源，修复后新series重验证。 |
| 无未决计划的Optimization候选 | candidate，准入/轮数通过才采用并创建计划。 |
| 新候选准入不足 | 拒绝候选；per_patch返回no_further_gain，campaign有净变更则no_further_gain、否则no_gain_found；无计划遗留。 |
| rejected_reverting下Optimization亲自撤销 | ①优先revert，不能再建候选；max_opt_rounds已到顶或只剩撤销容量也不做新候选准入。 |
| pending_validation下Compiler RPM/镜像/UT失败代撤销 | 匹配当前计划、失败来源与父树时revert；普通修复或新优化均②拒绝。 |
| 碰巧等于历史计划父树 | 不满足当前未决计划条件，不能冒充revert；按当前上下文进入candidate/repair或拒绝。 |
| 未决计划下base_mismatch | 不产撤销段，失败路由；若终到terminal且success_on命中，pending_plan_at_terminal→fail_safe，审计abandoned。 |
| campaign已撤销且无净变更 | 无未决计划，可no_gain_found→report_no_gain→succeeded；与上行不同，不会被误当pending终局。 |
| release路径 | 有未决计划仍拒审批；terminal兜底不授予发布权限。没有“失败汇总节点成功即允许发布”的新边。 |

四份原文示例均选local，三项能力声明现在明确verified，新能力规则不误拒。换成source_input未验证的Quickbuild时，四份图都有面对非空series的镜像路径（优化专项包括回边），拒绝正确。真正只用空series的图仍必须先有verified build_image，不能以“源码为空”绕过镜像能力验证。

absolute-only判定有固定SuiteVersion/BenchPolicy与字段依赖作为输入；混合relative SPEC、regression_pct、Optimization及必需Bench发布证据均要求comparison。无法确定依赖则拒绝，不让LLM选择类型；full/覆盖/有效样本/字段存在仍是运行时条件。input:none首轮comparison:none禁止进入gate的例外没有被取消。

Quickbuild研究Q1/Q3/Q4证明缺省、Profile与构建根两条输入链及样本Oct-28/Oct-13差异；Q5/Q6的镜像与标记/找回证据没有被本版扩大。推广状态、失败风险推断、两个编号呈现已匹配研究边界。本轮不要求为制定env_skew判据再访问服务。

## D. 第二部分问题

### C16-01 — MAJOR：awaiting_consume 的毒丸崩溃落在两个计数之外，重派仍可无上界

**位置**：01 v0.16 §2.2d“阶段定时器代次”“失联与中断次数上界”、CF-AUTH-20g；与execute intent起始阶段直接相关。

**依据**：execute型intent事务置“**awaiting_consume**”；loss到期仅对“**owner_epoch对应实例仍live**”生效；interrupt只覆盖“**awaiting_outcome或awaiting_reconcile**”。实例lapsed后仍按授权状态重派。

**反例**：broker受理某ReleaseDispatch，解析/载入计划或执行核销前检查时崩溃，尚未发送consume。phase为awaiting_consume，租约随后lapsed：loss不计，interrupt也不计。新实例重派同一毒丸计划，再崩溃。此路径既可以是从未核销的task，也可以是**已核销任务的新epoch恢复派发，尚未成功resumed**，不能仅因phase叫awaiting_consume就认为无发布历史。

launcher的N次/T窗口不替代task上限：例如N=3、T=60s，每次计划处理70s才崩溃、阶段期限120s，周期和退避使每个窗口不到3次；loss/interrupt一直为0。当前CF-AUTH-20g只在FakePublisher实际执行时注入，漏掉这一发送后的合法崩溃点。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.16.md §2.2d
+++ docs/01_Contract_Spec_v0.16.md §2.2d
- interrupt_count只计awaiting_outcome或awaiting_reconcile
+ interrupt_count计本实例已经承担的未完成execute派发，包括awaiting_consume、
+ awaiting_outcome、awaiting_reconcile；awaiting_probe仍不计执行中断。
+ 按持久化的owner_epoch/DispatchReceipt绑定识别，不由是否收到ACK推断。
+ 同一个实例退役事件、同一个task只计一次；loss触发者排除，其他task计interrupt。
+ 达interrupt上限时按实际授权是否核销分流：未核销撤销并失败关闭；
+ 已核销manual_only。不得由phase名称决定授权是否已消费。
--- docs/01_Contract_Spec_v0.16.md CF-AUTH-20g
+++ docs/01_Contract_Spec_v0.16.md CF-AUTH-20g
+ 加入初次dispatch与已核销恢复dispatch在consume/resumed前反复崩溃；
+ 每次间隔大于launcher的T、仍必须由task中断上限终止重派。
```

**副作用**：与毒丸同实例且尚未consume的无辜任务也可能被计interrupt，极端情况下需新Run；这是停止无界重派的明确代价。阈值可比loss高，但不能用“确定没有发布”作为无限重试理由。若希望精确归责，需另定义可证明的task接管/退出证据，不能凭没有ACK排除计数。

**测试/夹具**：初始/恢复execute×intent后受理前/受理后ACK前/ACK后consume前；lapsed与期限同时到达只计一种原因；重复回收事件不重计；低于上限正常重派，上限时未核销失败、已核销manual_only；毒丸每次耗时超过T但低于phase期限仍有界。

### C16-02 — MAJOR：启动退避以 lapsed 为计数条件，首次 hello 前退出没有可计数的租约

**位置**：01 v0.16 §2.2d“launcher拉起退避”“epoch按进程实例分配”、§5.1首次hello事务、CF-AUTH-20i。

**依据**：新增停止条件是“**连续N次……在时间窗T内lapsed→停止自动拉起**”；§5.1仍规定“**首次hello的epoch分配与实例租约记录同一事务**”。CF-AUTH-20i要求覆盖“**启动即崩溃**”。

**问题**：broker在模块初始化/加载配置时退出，尚未hello，就没有已分配epoch和BrokerInstanceLease，不能进入lapsed。launcher可能有进程退出通知，但现文未把这类通知定义为停止条件的输入。若直接反复重拉，N次lapsed永远不发生；若不重拉，又没有文中承诺的重试/停止状态。此外，把有限窗口密度当成唯一停止条件时，指数退避本身会拉长间隔，也不能保证连续失败最终停止。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.16.md §2.2d
+++ docs/01_Contract_Spec_v0.16.md §2.2d
- 连续N次在时间窗T内lapsed后停止自动拉起
+ launcher先持久化spawn_attempt_id及cgroup绑定，再启动进程；
+ hello前退出、hello超时与hello后短期lapsed均计作启动/健康失败，
+ 按spawn_attempt_id恰一次结算，launcher重启不丢失计数和待处理spawn记录。
+ 连续失败达到max_start_failures即停止自动拉起；指数退避仅决定重试间隔。
+ 只有成功hello并连续健康运行达到配置的稳定期，才清零连续失败计数；
+ N/T可另作速率熔断，不能作为连续失败的唯一上限。
+ hello前的清理依据launcher spawn记录执行，不伪造broker_epoch或已回收租约。
--- docs/01_Contract_Spec_v0.16.md CF-AUTH-20i
+++ docs/01_Contract_Spec_v0.16.md CF-AUTH-20i
+ 覆盖exec失败、hello前退出、hello超时、hello后立即lapsed；
+ 退避间隔跨T与launcher重启仍在上限停止；稳定运行后才重置计数。
```

**副作用**：需要launcher自身的持久化启动记录，不是再造执行权epoch。瞬时部署错误可能触发停机需运维恢复，代价显式且优于无界启动；已在publishing的task保持事实优先和人工入口，不以启动失败判定未发布。

**测试/夹具**：上述四类启动失败×spawn记录提交前后/进程启动前后/hello前后/退出记账前后kill launcher；一个spawn失败只计一次；同一待处理spawn不可重复拉起两个替换实例；N/T密度未触发但连续失败仍须停止。

## E. 五条时间线 × 崩溃点 × 期限 × 双计数 × 毒丸

### 组合规则

以下按“送达状态→业务/phase→故障事件→上限→远端事实”分层列出笛卡尔积。每层条件互斥；事务前使用旧状态、事务后使用新状态。表中明确保留C16-01/02未闭合格，不能把无限重试标成合法等待。

| 符号 | 含义 |
|---|---|
| D/S/X/A | 无intent创建D；当前epoch intent同id重送S；不同epoch按替代事务X；completed只表示送达A，继续业务期限或换实例恢复。 |
| Q | 原holder专属cgroup子树回收证明成立；读取失败、同名重建、清理超时不构成Q。新实例可在Q前上线。 |
| G | 未核销授权有效则一次核销；无效按既有running失败/D12规则处理。 |
| R(f) | 已核销、非indeterminate、非manual_only，Q后resumed再取事实：全部发生H；全部未发生且原子许可有效P；许可无效F；部分/未知U。 |
| H/F/P | H按released固定映射；F按release_failed固定映射；P为原子许可后才执行。 |
| U/B(f)/J | U锁存，只探测B：发生H；未发生且Q则F；未发生未Q则J（retire_requested原holder）；部分/未知继续U。J后新seq重探，不能复用旧负向观测直接F。 |
| L/M/I | 耗尽且未核销L：撤销授权并ledger失败关闭；耗尽且已核销M：manual_only；I为同域首响应重放，旧epoch先被连接守卫拒绝、closed不重开。 |

### 五条时间线与送达崩溃

T1正常、T2核销后发生前崩溃、T3发生后终局未提交、T4indeterminate、T5实例活但单任务失联。恢复派发的D不是第二次初始核销。下表所有execute格均须先检查L/M，不能先发送后检查上限。

| 崩溃点 | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| intent前 | D→G | Q后D→R(f) | Q后D→R(发生)→H | D(probe)→B(f) | D；随后当前期限 |
| intent后、受理前 | S/X按epoch选择 | S/X，执行恢复须Q | 同左，事实发生只H | S/X，只probe | S/X，保留期限 |
| 受理后ACK前 | 同上，不建第二task | 不重复核销 | 不因无ACK判未发生 | 不consume、不P | 同上 |
| ACK后completed前 | 同上 | 同上 | 同上 | 同上 | 同上 |
| completed后 | A | A或换实例R(f) | A或换实例H | 周期B/X(probe) | 期限按下表 |

替代事务前保留旧intent、后仅新intent有效；新目标又更替继续X；旧ACK仅审计。这里的“broker崩溃”再按当前phase查计数表：awaiting_consume的每一类崩溃都可能落入C16-01，不能只因传输有幂等就宣称活性有界。

### 故障来源、阶段与计数上限

| 事件/持久化phase | 本次计数 | 未到两种上限 | 任一达到上限 |
|---|---|---|---|
| live实例的本task执行期限到期：consume/outcome/reconcile | 触发者loss+1，不再interrupt | 退役原owner；未核销可立即X/G，已核销Q后R(f) | 未核销L，已核销M |
| 同次退役中其他task在outcome/reconcile | loss不变，interrupt+1 | 解除旧timer，waiting_holder；Q后才重武装 | 已核销M；不误作未发布 |
| lapsed且task在outcome/reconcile | interrupt+1，loss不变 | Q后R(f) | M；正常执行/对账毒丸至多max_task_interrupts次 |
| lapsed且task在awaiting_consume | **现文两者均不加，C16-01** | 可反复X，须修为有界 | 计数不会因该故障到顶；不能宣称L/M可达 |
| awaiting_probe超时 | 两者不加，不退役 | B(f)下一周期 | 正常U流程不靠probe超时耗尽；manual_only时无自动终局/执行 |
| retiring/lapsed实例的旧timer、waiting_holder、ABA旧代 | 不加 | owner非live或timer解除，忽略/告警 | 同左，不能复活L/M |
| 已closed或manual_only | 不再计执行期限 | I或M | 同左 |
| 首次hello前进程退出/超时 | 无lease、无lapsed，**C16-02** | launcher停止条件缺计数入口 | N次lapsed可能永远不可达 |

计数必须以同一个实例退役事件为事务边界：A触发loss的一次事件中B只计interrupt一次；重复定时器、租约通知、launcher恢复和重复retire_requested不能另造“中断”。V2已明确timer CAS与退役/替换幂等；扩充V3夹具时须同时断言interrupt也按该事件单次结算。B遭两次连带中断仍可正常完成；达到3次转人工是V3明确接受的代价，不能说无辜任务完全不受影响。`owner_epoch`不是当前全局epoch，旧实例事件不能退役新实例。

### 业务事务前后与期限竞争

| 时间线 | consume / resumed / proceed前后 | 事实与终局提交前后 | 期限低于上限 / 达上限 |
|---|---|---|---|
| T1 | consume前G，后I(granted)；换实例先Q再R(f) | 动作前崩溃转T2，后转T3；终局后I | 执行期限按loss，未核销X或L、已核销R或M |
| T2 | 已核销不可G；resumed后对账，未发生许可有效P、否则F；旧P不能跨epoch复用 | 未执行不发outcome；新实例必须重新取事实 | outcome/reconcile到期按loss；崩溃按interrupt，恢复consume前漏洞C16-01 |
| T3 | 全部发生只能H，不因D12/pending重发发布 | H提交前重新取事实，后I；部分出现进入T4 | 低于上限自动R→H；耗尽M后probe发生只准confirm_released |
| T4 | 锁存提交后C-09/C-10/C-10a不给执行权 | B/J/Q/新seq按事实分流，终局CAS一次 | probe期限不计loss；J回收原holder，不能把探测者当新执行holder循环回收 |
| T5 | phase/generation CAS；完成先提交旧期限失效，到期先提交旧结果被拒 | 不把task失联当远端未发生 | 低于上限恢复；上限L/M；连带任务按上表interrupt，不另计loss |

consume与未核销耗尽判定同一Ledger守卫单胜：consume先提交就按已核销M/R处理；耗尽先撤销关闭则旧实例不能再消费。proceed已提交但ACK丢失仍为awaiting_outcome，新代期限明确存在；receipt重放不刷新期限。重启、期限扫描和旧代事件均不能双计loss。

### 毒丸与launcher崩溃专项

| 毒丸/崩溃位置 | 本版结果 |
|---|---|
| FakePublisher每次执行即崩溃 | awaiting_outcome，interrupt达到3后M；不再自动execute，已覆盖。 |
| 恢复对账客户端每次崩溃 | awaiting_reconcile，同上；不复用旧P。 |
| 初次或恢复dispatch载入计划、consume/resumed前每次崩溃 | awaiting_consume，不计两种计数；C16-01。 |
| broker初始化、首次hello前崩溃 | 没有BrokerInstanceLease；C16-02。 |
| launcher在kill、空子树确认、reclaimed提交前后崩溃 | 按可信绑定与幂等退役事件恢复，不认目录不存在为静默，不重复替换。 |
| launcher在首次spawn前后、hello前崩溃 | 当前缺独立spawn失败结算边界，随C16-02补齐；不能通过伪造broker_epoch补洞。 |

因此并非五条时间线每格都已经闭合：正常执行阶段的毒丸已被中断计数限制；新边界中的consume前与hello前失败仍有无界或未定义出口，明确对应两条MAJOR。

### manual_only、只探测与事实一致性

manual_only后文本明确排除C-09和execute派发，C-11a不得绕过人工收尾；旧epoch receipt先经连接守卫，不能重放granted/proceed复活。未发现本版赋予manual_only自动发布的合法路径。只探测仍不含发布计划/内容、只用只读adapter，不能拿到P。

强制probe全部发生时只允许confirm_released；全部未发生时只允许静默后的confirm_not_released；相反请求应拒绝并保持publishing。部分/unknown仍沿既有证据裁决规则，不把部分出现自动映射成全量成功或全量未发生；证据不足可keep_unknown。这保留人工处理不确定事实的职责，不把人工批准当作重新执行授权。probe结果、决定和证据引用同事务记录，重放不产生第二终局。

新旧实例并存本身没有双消费：旧consume先提交则授权已核销，新实例须Q；新hello先提交则旧epoch consume被拒，未核销可G。委派权限必须阻止迁出可信子树，不能仅因leader退出就Q；CF-IPC-03应在并存实例及子进程环境执行真实权限验证。

## F. 同步项与交付边界

B第7组已登记initial/candidate/repair/revert、编排推导、E-CANDIDATE-NOT-REVERT、pending_plan_at_terminal、能力声明及实际输入/报告扩展。01仍以上游冻结v1.0+E-01为基准，这些尚未扩入的v2.x字段不计为第二部分缺陷。

H26-01是HLD新增事务位置与其自身冻结核心冲突；C16-01/02是01本版新计数/退避机制的覆盖缺口，均不能以等待上游同步豁免。本轮无新增未登记同步项。所有候选diff只写在本报告，未改正文或研究记录。
