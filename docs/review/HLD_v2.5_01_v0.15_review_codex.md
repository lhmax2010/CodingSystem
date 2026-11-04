# HLD v2.5 / 01 v0.15 定向复审 — Codex

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.5（仅 A22） | **NO-GO** | 0 | 1 | 2 | 0 |
| 第二部分：01 v0.15（仅 A3 的 v0.15） | **NO-GO** | 0 | 2 | 0 | 1 |
| 新增同步项（不计入第二部分） | 无；已登记 B 第7组者不重复报 | 0 | 0 | 0 | 0 |

## 负责人七项裁决的独立评估

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时显式化 | **成立** | 本版未放宽汇合、当前 series 报告与未覆盖 timeout 的禁止发布条件；扩大重试知情范围不要求把并行改成串行。代价仍是两路报告、超时及替代历史都必须保留。 |
| ② | 取最新 Profile，在 Run 启动时固定 | **有条件成立** | 将其明确为 CodingSystem 的选择、与服务缺省 Ref. Snapshot 区分，已纠正主要事实错误。代价是可能采用尚无 reference 推广证据的快照，基线自身问题会进入本次验证，且不能承诺距 HEAD 的上界。不过本版把“更晚且未推广”写成所有所选快照的事实，连显式指定快照也一律如此展示，仍须 H25-03；应显示实际证据，而非固定警示标签。 |
| ③ | Profile v1 严格匹配，v2 小改动复用预案 | **成立** | 本版未改其缺省关闭、预定非劣评估与兼容条件。仍须真实工具链评估后才能开启；代价是重采、评估成本，不因 HLD GO 就视为工具已验证。 |
| ④ | 目标模块登记与相关范围验证 | **成立** | 本版未减小撤销后的验证范围。base_mismatch 直接终止是环境输入不可信的出口，不是允许缩小范围规避验证。代价是遇到输入证明失败需修复环境或新建 Run，而非继续 AI 试修。 |
| ⑤ | 用测试结果及多版本报告检验 AI | **成立** | source/config 证据与不可比不得人工补成通过的原则保留。purpose 由编排推导方向正确，但新推导规则相交会破坏确定性撤销，须修 H25-01；不能把 AI 自报类别作为修补办法。代价仍是无收益候选的重建、验证和撤销成本。 |
| ⑥ | 显式 base 预检与实际输入核对 | **成立** | 已知 ID 读取与完整找回区分，批量覆盖、暂存通道及镜像能力仍按证据准入。加载期暴露能力不足合理，但须按实际所需能力判定，不能连不需要 A/B 的 gate 一起拒绝，见 H25-02。 |
| ⑦ | 重试成功可发布，审批人确认 | **成立** | 当前 series 全部 task 补上 ci_plan、Review；被引用基线的内部构建重试并入消费 Run；旧 series 仍首屏汇总。知情面符合原意，且确认 id+digest、consume 再复核保留。代价是确认项增加、共享/缓存基线须携带可追溯重试记录；被放弃且未被使用的基线构建不应变成本次发布确认项。 |

## 范围与证据

评审前 `git pull --rebase` 返回 Already up to date；输入 HEAD：`f870c28ea2e9ee8097faf16878887b1ed0c854f1`。阅读两份上一轮处置表、上一轮三家原始意见及 Quickbuild 研究记录；核对 v2.4→v2.5、v0.14→v0.15 的全部 diff，再沿直接关联条款走查。没有读取本轮其他评审方意见，没有访问或探测 Quickbuild，没有修改被审文档。

| 输入 | SHA-256 |
|---|---|
| `docs/00_Framework_HLD_v2.5.md` | `51e636168c32ebe233048e3d80b1c8340e0967036efa5d02e34ff9c3c3e87836` |
| `docs/01_Contract_Spec_v0.15.md` | `46e1ae77f5dc64bd80da65127c26c89b9b7d9d48f5f385e6555ac354e9e00442` |
| `docs/review/HLD_v2.4_review_disposition.md` | `f1137b229e6fae7458fbffc8aa9f39493f6161b251679944a50b8874e6af8fe3` |
| `docs/review/01_v0.14_review_disposition.md` | `82662af3e158bf334c01ac2e8067d08a398eea497324cfa40c36215bb4179b3e` |
| `docs/research/quickbuild_business_logic.md` | `33104bb3c1f70d5f196b83c7f02b5b664db5c0da512a56cf49738164498763c3` |

方法：文本/事务边界审查与反例演算；临时只读 Python/PyYAML 检查四份原文 YAML 的后端、advances 后可达性；模型和注册表扫描得到 123 个 class 均出现在 A0，CommandName 与命令注册表均21项且集合相等。以下不是对实际校验器、launcher 或 conformance 的执行结果；没有用夹具假设证明线上能力。

## A. 处置落实与两项取舍

### HLD 处置

| 条目 | 落实与判断 |
|---|---|
| Q1 | §7.6.1、审批呈现、A22已纠正服务缺省/框架策略、删除落后量上界、区分已知 ID 读取/扫描/配置过滤、限定1917样本无镜像。主要意见落实；新加入的无条件“未经推广”仍需 H25-03。 |
| Q2 | §4.2.6新增加载期检查；§7.6.1定义 image_failed_exhausted(backend_source_input_unsupported)，不进修复环；R15/P6写出本地替代。落实；“所有阈值 gate 均要求 comparison verified”范围过宽，H25-02。 |
| Q3 | §4.3.5证据链扩大到当前 series 全部 task及所用基线内部构建；consume 拒绝、ledger直接失败映射在§4.3.5/8.3/B-7一致。协议表述落实，broker不再补发未执行的outcome。 |
| Q4 | §7A.4新增框架推导及base_mismatch优先。后者成立；前者candidate/revert条件重叠，H25-01，是本版新增规则的直接问题。 |
| Q5 | §4.2.6③明确per_patch返回no_further_gain；campaign按净变更选no_further_gain/no_gain_found。落实，拒绝创建计划不消耗新候选数，不需要Agent猜环预算。 |

“记录更正”两条准确：历史默认是 Ref. Snapshot，不是已证明的最新Profile策略；已知ID读取有实测，未证实的是完整扫描/归属过滤。处置表总述“上一轮全部条目三家均核验落实”应理解为已有落点，不等于各边界都无缺陷；上一轮本方和Claude Code仍对Q1所归并问题提出了异议。

### 01 处置

| 条目 | 落实与判断 |
|---|---|
| W1 | 专属domain cgroup、可信路径/代次、禁止迁出、递归populated=0、kill与空子树分开、launcher恢复、同名重建/读取失败不认静默、CF-AUTH-09f均落实。本方上轮C14-01关闭。 |
| W2 | loss_count/max_task_losses、未核销关闭、已核销人工出口、阶段CAS和CF-AUTH-20d/f已落文。但新人工出口与既有guard不闭合（C15-01），退役等待期间的旧阶段计时未定义失效（C15-02）。不能仅因字段出现就认定循环问题全部解决。 |
| W3 | 写kill后新实例在新cgroup上线、未核销立即重派、已核销/负向映射仍等旧holder静默已落文。取舍本身成立；与阶段期限组合须补C15-02，旧夹具须同步C15-03。 |
| W4 | §5.1按execute/probe分述，非法probe组合拒绝；CF-IPC-10输入列也分组。专门规则一致，输出列残留未限定的旧断言归C15-03。 |
| W5 | ReleaseTaskState及A0、dev4均落实。模型可被索引抽取，但尚不能表达退役等待/停止自动恢复时的定时器状态，配套完善见C15-02。 |

01_v0.14处置表没有单独的“记录更正”节，不能虚称核验了不存在的章节；其对前轮两家MAJOR的来源、计数及取舍描述与原始意见相符。

**取舍①：未核销失联耗尽后直接失败关闭——成立。** 以同一Ledger事务核对授权仍未核销、撤销授权并关闭，可以与consume竞争而单胜：consume先提交则进入publishing分支；耗尽判定先提交则旧实例/授权不能再consume。停在release节点既不属于publishing人工裁决域又无新事件，反而会悬挂。代价是已审批的工作仍需新Run重试，但没有伪造已执行的release_outcome。

**取舍②：新实例不等旧实例回收完成——成立。** 撤回本方上轮“新实例启动也必须等回收证明”的过强限制。未核销任务依赖Ledger一次消费和当前epoch隔离；旧实例已核销的任务仍可有本地在途执行，必须等其专属子树空后才授予新的执行权。只读探测可提前，负向终局不能提前。代价是会同时存在一个当前实例和若干正在回收的旧实例，故阶段定时器必须绑定原所属实例并在退役时停止，不能把等待清理算成新实例再次失联（C15-02）。

## B. 第一部分问题

### H25-01 — MAJOR：purpose 推导的 candidate 与 revert 条件重叠，正常优化撤销可能再创建计划

**位置**：HLD v2.5 §7A.4“优化计划”“撤销”，§4.2.6③；A22/Q4。

**依据**：新增规则先规定“**注册为产出 optimization_candidate 的节点提交的段 = candidate（同一事务内创建计划）**”，又规定“**任一节点提交……parent_tree 的确定性撤销段 = revert**”。下一段保留“**opt_patch_ready（Optimization 撤销）**”与“**撤销段不作为新的收益候选**”。

**问题**：Optimization自己执行撤销是正常路径，不只是Compiler/UT代它撤销。例：计划P在Benchmark中判neutral/inconclusive→rejected_reverting，Optimization提交恢复P.parent_tree的段。这次提交同时满足两个推导条件；按先写规则匹配会创建P2，按撤销规则匹配才结束P。前者可能被max_opt_rounds/剩余容量拒绝，或遗留P为未决而另建P2，破坏确定性撤销与轮数上界。仅禁止提交方自报不能解决规则不互斥。

**候选 diff**：

```diff
--- docs/00_Framework_HLD_v2.5.md §7A.4
+++ docs/00_Framework_HLD_v2.5.md §7A.4
- 注册为产出 optimization_candidate 的节点提交的段 = candidate；
- 任一节点提交……确定性撤销段 = revert；其余 = repair。
+ 编排按以下互斥顺序推导purpose：
+ 1. 当前Run有可撤销的未决计划，且按其记录确定性生成/复验的段
+    恢复该计划parent_tree：revert优先，不论提交者是否Optimization；
+    同事务迁原计划reverted，不创建计划、不执行新候选准入、不增加候选轮数。
+ 2. 非上述撤销，且提交节点注册optimization_candidate：candidate；
+    要求无未决计划，并执行候选轮数/容量准入，同事务创建新计划。
+ 3. 其余合法业务修复段：repair；初始开发者patch的purpose亦归此类，
+    producer/来源仍单独标识，不因purpose=repair改称AI修复。
+ 存在未决计划但冒充普通修复/新候选的非法提交，按该计划允许的动作拒绝；
+ 不依赖提交方的purpose或任意历史计划parent_tree判定。
```

**副作用**：保持三种purpose，不新增计划状态；明确它不是作者/来源分类。撤销要匹配当前可撤销计划及确定性内容，避免任意patch碰巧等于某个历史树就被认作撤销。负责人“收益须验证”的意图保留，取消的是含糊的分类优先级。

**测试/夹具**：Optimization在neutral/loss/inconclusive后亲自撤销；max_opt_rounds已到顶及优化环只剩撤销容量时仍成功撤销；Compiler/UT失败代撤销同规则；自报repair的新优化仍创建计划；匹配历史已结束计划的树不能冒充revert；每次撤销只结束原计划、计划数不增加。

### H25-02 — MINOR：comparison 能力检查覆盖所有阈值 gate，误拒只用绝对指标的合法验证

**位置**：HLD v2.5 §4.2.6新增后端能力规则、§11.3对应夹具；对照§7A.3/§7.6.1。

**依据**：新增规则说“**后端的可比性能力（comparison）≠ verified，而其镜像被阈值 gate、优化收益判定或 release_requires 中的 bench_report 消费 → 同样拒绝加载**”。§7A.3则区分absolute SPEC用candidate_median_ci和relative SPEC用effect_ci_pct；§7.6.1未知输入只使“**比较类判定字段缺失**”，保留两侧绝对测量。

**问题**：不发布、无Optimization的流水线可以只对非空series做完整绝对SPEC测量，用spec_out_count门禁；它需要有效镜像、源码证明、样本和完整覆盖，不需要A/B输入可比。设后端source_input/build_image已verified、comparison尚未verified，该新规则仍一律拒绝。这不是放宽release_requires的Bench谓词，也不是让input:none首轮comparison:none报告进入gate；是非发布的绝对判定被误要求具备相对比较能力。四份原文示例使用local，通常不会暴露此反例。

**候选 diff**：

```diff
--- docs/00_Framework_HLD_v2.5.md §4.2.6
+++ docs/00_Framework_HLD_v2.5.md §4.2.6
- comparison ≠ verified，而其镜像被阈值 gate……消费 → 拒绝加载。
+ comparison ≠ verified，且其镜像用于需要A/B的指标（relative SPEC、
+ regression_pct等）、优化收益判定或release_requires的bench_report → 拒绝加载。
+ 仅消费完整absolute SPEC聚合字段的非发布gate不要求A/B可比性能力；
+ 仍检查gate_eligible、有效样本、所选必测指标覆盖与字段存在。
+ 指标依赖类型由固定SuiteVersion/BenchPolicy与字段注册元数据解析，
+ 无法确定为absolute-only则保守按需要A/B处理。input:none首轮禁作gate输入不变。
--- docs/00_Framework_HLD_v2.5.md §11.3
+++ docs/00_Framework_HLD_v2.5.md §11.3
+ 对照夹具：source_input/build_image已验证而comparison未验证时，
+ absolute-only非发布gate可加载；relative gate、Optimization、必需Bench发布拒绝。
```

**副作用**：校验器须按指标依赖判定，而不是只看gate节点类型。保留未知即fail-closed、人工不能补A/B结论；避免为了运行一个绝对SPEC验证而被迫换本地后端。若产品决定禁用所有不可比镜像上的gate，也应显式收缩绝对验证功能，不能称其为“只检查所需能力”。

**测试/夹具**：非空series、full套件全部absolute、spec_out_count=0的非发布流程；同图切换relative SPEC或regression_pct必须拒绝；混合SPEC/无法解析依赖必须拒绝；single/quick或覆盖不全仍不可过gate。

### H25-03 — MINOR：最新快照策略的代价已披露，但“更晚且未推广”仍被无条件当成事实

**位置**：HLD v2.5 §7.6.1“最新”“审批呈现”、A22；HLD_v2.4处置Q1/负责人②。

**依据**：正文称所选最新Profile“**它比 reference 新，但未经 reference 推广，快照自身的构建失败更常见**”；审批呈现对“**锁定的 Profile 快照编号与发布时刻（注明未经 reference 推广）**”无条件加注。研究Q1只限定取证时配置的Ref. Snapshot默认；Q3的一组Profile/base日期不同，既不保证每次最新Profile与reference不同，也没有给出两类快照失败率的统计证据。

**问题**：当当前reference恰是最新可用Profile，或开发者显式指定已有推广证据的快照，首屏仍会写“未经推广”。latest不必严格大于reference；未验证的风险也不等于已测得“失败更常见”。本版纠正了旧缺省混淆，却不应引入新的固定事实标签。

**候选 diff**：

```diff
--- docs/00_Framework_HLD_v2.5.md §7.6.1
+++ docs/00_Framework_HLD_v2.5.md §7.6.1
- 它比reference新，但未经reference推广，快照自身的构建失败更常见，
- 审批首屏注明“快照未经reference推广”。
+ 它可能晚于当前reference，也可能与之相同；选择更晚且缺乏推广证据的
+ 快照可能增加基线自身失败的风险（设计推断，当前研究未量化失败率）。
+ 保存选取策略、所选快照及可取得的reference解析/推广证据；首屏据证据显示
+ “与当前reference相同”“已取得推广证据”或“推广状态未验证”，不得固定填未推广。
- 锁定的Profile快照编号与发布时刻（注明未经reference推广）
+ 锁定的Profile快照编号、发布时刻与上述基于证据的状态（含显式指定的快照）
```

**副作用**：不改变“选最新并固定”的决定，不要求在线补探，也不强求不可得的推广字段；unknown可以明确展示。代价说明从绝对断言改为风险与实际证据，审批人仍知道取舍。

**测试/夹具**：latest等于reference、latest较新、reference读回不可得、显式指定已有推广证据快照四例；不能凭时间先后宣称已/未推广；不能生成无证据的失败率或HEAD落后上界。

## C. HLD 边界核验结果

| 检查 | 结果 |
|---|---|
| 四份示例原文的能力加载 | full_pipeline、optimize_campaign、compiler_only、compiler_bench_only均为backend:local。在本地source_input与comparison已验证的部署声明下，新能力规则均不拒绝；这是能力规则核对，不重做全部DSL审计。 |
| 四份示例改为暂存输入未验证的Quickbuild | 四者镜像节点均可能面对非空series；示例二首轮虽空，opt回边和修复边仍可达镜像，故整图拒绝成立。不能把“首轮可运行”当成“整图可加载”。 |
| 真正仅空series的无修改、无A/B、无发布图 | source_input未验证本身不应拒绝，但build_image仍须verified。当前调查尚未给出Quickbuild镜像能力，因此不能凭此图宣称首期已能实际出镜像。 |
| retried扩大后的边界 | 当前series所有task含ci_plan/Review；提供实际所用基线的内部task，即使跨Run缓存命中，也须随引用带入可追溯重试记录。共享基线应按原task/attempt/条目id去重，不按等待者重复制造超时；被放弃且不再被引用的基线只作历史，不作当前确认项。 |
| retried的批准/核销 | id+digest确认及核销再检查不变；ConsumeRejected(gaps_changed)+ledger关闭与“outcome仅实际执行后”一致。publishing后的异常仍只能pending，不能反改发布事实。 |
| purpose类型全集 | candidate/repair/revert可覆盖优化、普通修复和撤销；开发者初始输入应沿既有producer归属保留，repair不等于AI来源。当前致命问题是条件相交，非必须增加第四枚举，H25-01。 |
| base_mismatch优先 | 输入不可信→image_failed_exhausted→fail_safe；不再生成撤销段。Run关闭时abandoned为审计标记，不要求不存在未决计划才能失败关闭，故不形成死锁。后续不能在同一closed Run继续该计划。 |
| backend_source_input_unsupported | 加载期先挡，运行期防御仍直接image_failed_exhausted不进修复环；不能在未决计划下借常规“镜像失败撤销”规则吞掉该防御。此处以§7.6.1具体错误分支为准。 |

本轮只因A22新增推导规则报H25-01，不重开上轮“撤销提交即reverted”的已接受设计。Quickbuild已知ID读取、顺序扫描/配置过滤未验证、1917仅样本无镜像、HEAD落后量unknown等其余修订与研究记录一致。

## D. 第二部分问题

### C15-01 — MAJOR：已核销任务失联耗尽后的唯一人工出口，被既有 unknown guard 堵住

**位置**：01 v0.15 §2.2d失联上限、§5.1特权运维、C-11/C-11a；ReleaseTaskState及CF-AUTH-20d。

**依据**：新增规则规定达到上限的已核销task“**不再参与持有者更替重派与自动执行**”“**只经人工裁决（C-11）收尾**”。§5.1的adjudicate guard仍为“**Run=publishing ∧ 强制 probe 后 unknown**”；§5.1/§2.2d的release_probe_dispatch“**仅用于已核销且 indeterminate**”。耗尽事务没有把none/execution_permitted/reconcile_required改为indeterminate，也没有另开人工入口。

**反例**：任务第二次awaiting_outcome到期，loss_count=2，recovery_state=execution_permitted；旧实例回收后，远端其实已全部发布。不能重新execute/resumed；非indeterminate不能发release_probe_dispatch；操作员强制probe却得到happened，不能满足adjudicate的unknown guard。未发生的确定结果也同样无出口。只有事实更不清楚时反而能裁决，无法满足“每格唯一出口”。

**候选 diff**（保留“耗尽后不再自动执行，只人工收尾”的取舍）：

```diff
--- docs/01_Contract_Spec_v0.15.md §2.2d / §5.1 / C-11
+++ docs/01_Contract_Spec_v0.15.md §2.2d / §5.1 / C-11
+ loss_count达到上限且publishing时持久化manual_only并停止自动派发；
+ 不伪造远端事实、不授予新执行许可。运维adjudicate仍先执行只读强制probe。
- guard：Run=publishing ∧ 强制probe后unknown ∧ ...
+ guard：Run=publishing ∧ (强制probe后unknown 或 task处于loss_exhausted/manual_only) ∧ ...
+ 耗尽分支：probe明确全部发生时仅允许confirm_released；明确全部未发生时
+ 仅允许confirm_not_released且原holder真正静默；部分/unknown沿既有裁决证据规则。
+ 只读probe结果与人工决定/证据引用绑定并落账；不借C-10发送伪outcome。
+ C-09及execute派发显式排除manual_only；C-11a自动通道不得越过本分支的人工要求。
```

**副作用**：扩大的是人工收尾入口，不是重开发布权限；强制probe依然必须，确定结果不能被相反裁决覆盖。也可以选择“耗尽后自动只探测、禁止执行”的另一产品方案，但会改变本版“只人工收尾”的选择，不能不写清就混用。

**测试/夹具**：loss_count达到上限×recovery_state三种非unknown状态×远端全部发生/全部未发生/部分/未知；发生允许人工确认成功，未发生须静默后人工确认失败，部分/未知保持证据约束；旧receipt不能恢复执行；决定事务前后崩溃仅一次终局。

### C15-02 — MAJOR：退役等待未使阶段计时失效，无法保证失联恰计一次或隔离连带任务

**位置**：01 v0.15 §2.2d阶段期限、异步回收与持有者更替；§2.5 ReleaseTaskState；CF-AUTH-20d/e/f。

**依据**：新增“**loss_count……在判定事务内+1**”，以及“**同一实例上其他task……其新阶段由重派事务重新写入，loss_count不增加**”。但已核销者要等旧holder静默才重派；ReleaseTaskState只有四个活动phase，失联判定也未规定phase/期限如何退出或解除武装。CAS仅写“phase CAS互斥”，没有给出失联事件胜出后的目标、阶段代次或等待回收状态。

**反例**：E1上的A先超时，A计一次，E1退役；写kill后E2上线，E1子树因D状态迟迟不空。E1上原本正常的B已核销，不能重派，故其旧phase/期限还在。B旧期限到期仍满足“无该阶段完成事件”，会被另算task失联；A本身也没有新的phase或已消费期限标记来阻止重复定时扫描再加一次。到上限后B可能被迫人工收尾，虽然它只是被A的整实例回收连带中断。若“该实例”误取当前实例还会退役E2；即便正确取E1，重复kill/替换通知也缺少一次性边界。W3使此等待窗口成为明确允许的正常部署状态，不能依赖清理恰好很快来避免。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.15.md §2.2d / §2.5
+++ docs/01_Contract_Spec_v0.15.md §2.2d / §2.5
+ 每段期限绑定(phase_generation, owner_epoch, phase, deadline)，
+ 只对timer_armed=true且owner_epoch对应实例仍live的当前阶段生效。
+ 到期事务CAS消费该代定时器，loss_count只增加一次；同事务退役该owner实例，
+ 将其全部未终结task的旧定时器解除武装。其他task不计loss。
+ 等待旧holder静默期间不运行执行阶段期限；继续R13等待告警。
+ 新派发/恢复阶段才增加phase_generation并重新武装；旧代事件一律忽略。
+ 耗尽manual_only和closed均不再武装执行期限；awaiting_probe仍仅驱动只探测。
+ launcher对每个实例的退役/替换请求幂等；重复定时器、retire_requested或
+ launcher恢复不得为同一退役事件反复拉起替换实例。
 class ReleaseTaskState(BaseModel):
     ...
+    owner_epoch: int
+    phase_generation: int
+    timer_armed: bool
+    recovery_mode: Literal["active","waiting_holder","manual_only"]
```

**副作用**：增加明确的调度元数据，仍只有实例epoch作为执行权，不引入task执行epoch。等待旧holder可以长期持续，但只告警，不消耗“真正运行后失联”的重试次数。批量冻结同实例任务可能增加一个Ledger事务的写集，换来精确一次计数与无连带退役。

**测试/夹具**：A超时、B尚正常且E1子树长时间不空；B旧deadline到达、A同一到期事件重复/重启重放，A只计1次、B计0次、E2不被旧事件退役；E1回收后B重派才启动新期限；新旧阶段同名的ABA事件；到期与完成两种事务顺序；同一退休请求跨launcher崩溃只产生一个替换实例。

### C15-03 — NIT：旧夹具预期仍无条件要求先回收、已核销先静默

**位置**：01 v0.15 CF-AUTH-20、CF-IPC-10输出列；对照新增CF-AUTH-20e和§5.1。

**依据**：CF-AUTH-20仍写“**cgroup为空后reclaimed→新epoch恰一次恢复**”“**无法清理→不重派**”，输入同时含awaiting_consume；CF-IPC-10左列虽已分execute/probe，右列仍笼统写“**已核销须先静默**”。

**问题**：专门条款与新增夹具已经明确未核销可以先重派、probe可先发送，旧输出列却可能生成相反断言。按左列限定可理解正确，故只计NIT，不重复上轮的协议级MINOR。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.15.md CF-AUTH-20 / CF-IPC-10
+++ docs/01_Contract_Spec_v0.15.md CF-AUTH-20 / CF-IPC-10
- cgroup为空后reclaimed→新epoch恰一次恢复；无法清理→不重派
+ 写kill后可上线新epoch；未耗尽且未核销者可立即重派，
+ 已核销execute恢复等原holder静默；无法清理只阻塞相应已核销执行与负向终局。
- 已核销须先静默
+ 已核销且非indeterminate的execute恢复须先静默；probe发送不要求静默，
+ 其负向映射才要求静默。耗尽分支按CF-AUTH-20d，不断言自动恢复。
```

**副作用**：仅统一测试预期，不改权限。**测试/夹具**：共用参数表覆盖未核销execute、已核销execute、indeterminate probe三类，分别断言发送条件与负向终局条件，避免用一条“已核销”布尔值代表所有语义。

## E. 五条时间线、崩溃、期限与上限的组合走查

### 出口函数与边界

以下以Ledger事务前/后状态为准，分解四个正交维度。送达表的每格再与阶段/次数表相乘，最后按远端事实表唯一分流；不是以ACK决定远端事实。不可达组合明确列出前提，而不是为它另造出口。

| 记号 | 唯一动作 |
|---|---|
| D/S/X | 无intent则创建D；有intent且target_epoch等于current则同id重送S；不等则满足业务guard后以替代事务X重派。三者按持久化状态互斥。 |
| A | completed只表送达，同实例等待业务结果/当前期限；新实例仍按X。 |
| Q | 原实例可信cgroup子树回收，未证实空则等待告警。新实例可先上线，不能据此宣称Q已完成。 |
| G | 未核销有效授权一次consume；过期/撤销或D12失败按既有running分支关闭/行政终结。 |
| R(f) | 已核销非unknown，在Q后新holder resumed并对账：全部发生H；未发生且许可有效P；未发生且许可无效F；部分/未知U。 |
| P/H/F | P为原子许可后执行；H为released固定映射；F为release_failed固定映射（admin_finalize优先于cancel、fail_safe）。 |
| U/B(f) | U锁存indeterminate，只探测B：发生H；未发生且holder静默F；未发生未静默J；部分/未知继续U。 |
| J | retire_requested记录观测并回收原granted_epoch持有者；Q后新seq/new id重新探测，不凭旧负向观测直接F。 |
| M | 已核销且loss耗尽，停止自动执行/重派，人工收尾。**当前明确事实的人工入口有C15-01缺口。** |
| L | 未核销且loss耗尽，同事务撤销授权并ledger级F(reason=dispatch_loss_exhausted)。 |
| I | 同幂等域同id重放首响应，旧epoch/退役实例先被连接守卫拒绝；closed不重开。 |

### 五条时间线 × 送达崩溃点

T1正常；T2核销后发生前崩溃；T3发生后终局未落账；T4indeterminate；T5实例存活但单任务失联。T2/T3行的D指恢复发送的intent，不是第二次初始核销。各格均受下一表的loss上限覆盖，不能先发送再检查上限。

| 崩溃点 | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| intent前 | D→G | Q后D→R(f) | Q后D→R(发生)→H | D(probe)→B(f) | D；保留期限 |
| intent后受理前 | S或X，epoch唯一选定 | S或X，恢复执行须Q | 同左，事实发生只H | S或X，只probe、不需先Q | S或X，ACK不替代失联检测 |
| 受理后ACK前 | 同上一行；不新建task | 不重复核销 | 不因无ACK判未发生 | 不consume、不授予P | 同上一行 |
| ACK后completed前 | 同上一行 | 同上一行 | 同上一行 | 同上一行 | 同上一行 |
| completed后 | A | A；换实例Q后R(f) | A；换实例Q后H | 周期B或X(probe) | A；当前阶段到期按下表 |

替代事务前崩溃保留旧intent，后崩溃只留新活动intent；E2尚未发送再换E3继续X，旧ACK仅审计。launcher写kill前/后、populated确认前/后、reclaimed提交前/后均按可信绑定恢复：未提交证明就不能负向终结；同名重建、目录缺失、读取失败一律不冒充Q。新实例自身拥有不同cgroup，不会使旧子树永远非空。

### 阶段期限 × 是否到上限（作用于上述每个可达格）

“达上限”按本次失联事务加1后的值判断。没有到期事件就不新增loss；编排重启/ACK重放不改计数。真实实例反复崩溃但未触发task期限，不属于本版定义的task失联计数，不能宣称该配置还限制了所有外部进程崩溃次数。

| 当前持久化状态/事件 | 加1后仍低于上限 | 本次达到上限/已耗尽 |
|---|---|---|
| awaiting_consume到期，未核销 | 退役原实例；新epoch可立即X→G，不等Q | L；不得留下等待release节点 |
| awaiting_consume到期，但这是已核销恢复dispatch | 退役对应实例，Q后X→R(f) | M；不能按未核销L关闭 |
| awaiting_outcome到期（包括proceed后） | 退役原实例，Q后R(f)，期限不是未发生证据 | M；已发生也不能自动再execute；当前人工明确结果缺口C15-01 |
| awaiting_reconcile到期 | 退役原实例，Q后重新对账，不复用旧P | M；同上 |
| awaiting_probe到期 | 只重发/周期只探测B，不增loss、不退役 | 仅正常锁存流程可在此活动；若另被标manual_only则停止自动派发，按M。状态必须显式区分，不能同时B与M |
| 已retiring/reclaimed的旧阶段deadline | 应解除武装、忽略；当前缺C15-02 | 不得重复加1或再次拉新实例；当前缺C15-02 |
| 已被换代的阶段/已closed的deadline | 忽略；不能以phase名称相同匹配新一代 | 同左 |
| 完成事件先提交 | 新phase或终局生效，旧期限失效 | 若已closed则I；不再加loss |
| 到期事务先提交 | 旧实例后到结果被拒，按低于上限分支 | 按L/M，不能仍无条件说“新实例对账” |

只有未核销分支能安全按“没有发布发生”关闭。其consume与耗尽判定必须共享授权/Run事务守卫：无论哪方先提交，另一方读到的状态只允许另一个分支，不能同时G与L。

### 五条时间线 × 业务崩溃边界 × 上限

| 时间线 | consume前后 | resumed/reconcile/proceed前后 | 远端动作/报告终局前后 | 到期低于上限 / 达上限 |
|---|---|---|---|---|
| T1正常 | 前G；后同实例I(granted)，换实例Q后R(f) | 正常初次无需resumed；若进入恢复按R(f)，事务后I | 动作前崩溃转T2，后转T3；终局后I | 未核销X→G或L；已核销R(f)或M |
| T2核销后发生前 | 已核销不可再G | 未发生+原子许可有效P，无效F；P事务ACK丢失同实例I，新实例重做Q/R(f) | 未执行不发outcome；实际执行后按事实；终局后I | 低于上限重对账；达上限且明确未发生应人工F，现文C15-01堵住 |
| T3发生后 | 已核销 | 全部发生H，不重发发布；D12仅pending | H提交前重新取事实，后I；部分发生转T4 | 低于上限对账H；达上限应人工H，现文C15-01堵住 |
| T4indeterminate | C-09排除，旧执行receipt不能复活 | 锁存提交前仍原阶段，提交后U；新id的C-10a拒绝 | 只B(f)，J后Q并新seq；终局CAS单胜 | probe期限不增loss；不应凭周期probe达到执行失联上限 |
| T5实例活任务失联 | 未核销依X/G或L；核销先提交则改走已核销分支 | resumed/尤其P之后的失联均有期限，不以曾收到reconcile为完成 | 失联不替代远端事实；完成先提交则旧期限失效 | 低于上限恢复、达上限M；回收中的连带task须等待而非再计loss，C15-02 |

上述表格穷尽所要求的事务前/后、五个送达崩溃点、四种phase与上限两侧。当前无法满足唯一有效出口的格明确标了C15-01/02，未用“保持publishing”掩盖无法使用的人工入口，也未把计数重复当成合理的第二次失联。

### 新旧实例并存、周期探测与双重执行

单一“当前”是Ledger epoch，不等于只允许一个OS进程存在。新实例hello和旧实例consume竞争：旧consume先成功，授权就是已核销，新实例必须等原holder真正Q；新hello先成功，旧连接非当前，不能consume，新实例可正常G。旧granted/proceed receipt不因重连或重放绕过连接检查。由此未发现并存本身授权双重执行。

周期probe不改granted_epoch。原holder E1不静默时E2得到未发生，只能请求回收E1；E1真正Q后负向F，unknown则继续U，不能把E2当执行holder再回收。因此业务探测本身仍无“每次probe都重启当前broker”的合法循环。实现必须把对已retiring E1的重复回收/替换请求做幂等，C15-02的补充同时覆盖此组合。

只探测payload不含计划与发布内容，broker只读adapter、C-09/C-10/C-10a/C-11a的recovery_state守卫仍一致；新§5.1正确分开送达协议与执行权限。probe不能拿到P，篡改kind、旧consume/proceed request_id、旧epoch也不能发布。人工耗尽出口的修订同样不得以恢复自动execute来“解决”无出口。

## F. 同步项与收尾

HLD附录B第7组已登记后端能力、ExpectedSourceManifest、comparison、OptimizationPlan及purpose、三规则、确认集合/扩大的证据链、ConsumeRejected(gaps_changed)、get_result清单等；不将这些尚未落入01的v2.x扩展重复计为第二部分缺陷。本轮无新增未登记同步项。

123个class/A0覆盖和21命令索引检查通过，只证明索引齐全，不证明ReleaseTaskState生命周期完整；C15-02正是新增模型与异步回收组合的语义缺口。被审文档之外只新增本报告；上述diff均为候选，未实际修改正文。
