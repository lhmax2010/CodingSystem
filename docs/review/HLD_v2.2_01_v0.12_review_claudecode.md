# HLD v2.2（第二轮）+ 01_Contract_Spec v0.12（第十二轮）评审意见 —— Claude Code

- 评审对象：`docs/00_Framework_HLD_v2.2.md`（对照冻结基线 `docs/00_Framework_HLD_v1.0_draft_frozen.md`）；`docs/01_Contract_Spec_v0.12.md`
- 参考：`docs/review/HLD_v2.0_review_disposition.md`（含"项目负责人裁决"一节）、`docs/review/01_v0.11_review_disposition.md`、上一轮三家原始意见 `HLD_v2.0_01_v0.11_review_{kimi,claudecode,codex}.md`
- 方法：HLD v2.2 全文通读，对照处置表 K1–K22 与六项裁决逐条核对落地文本；两份示例 YAML 按 §4.2.6 三条规则与 01 V-00..V-17 逐条手工走查（另两份示例在 HLD 中无原文，见 H22-17）；01 v0.11→v0.12 全部 26 个 diff 块逐一核对，恢复臂按"四条时间线 × 崩溃点"重新推演；A0 类型索引用脚本做双向差集检查
- 约定：只评审、不修改被审文档；`[待补充]` 环境事实不计缺陷；对已定案的设计不提替代方案，除非原方案矛盾、不可实现、不安全或不可测

## 结论

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| 第一部分：HLD v2.2 | **NO-GO** | 0 | 8 | 12 | 1 |
| 第二部分：01 v0.12 | **NO-GO** | 0 | 3 | 1 | 1 |
| 同步项（单列，不计入第二部分结论） | — | 0 | 3 | 6 | 1 |

**负责人六项裁决的判断**（详见下一节）：① 有条件成立；② 有条件成立；③ 有条件成立；④ 有条件成立；⑤ 有条件成立；⑥ 成立。

**第一部分要点**：上一轮两个 BLOCKER 均已落实为 D22 与勘误 E-02，主体成立。但负责人恢复并行后，只把"汇合必经"用于规则①，规则③仍按字面路径检查，示例一因此经 review_static 分支被规则③拒绝（H22-01）。另有七条 MAJOR：§4.3.5"有超时项不得 succeeded"没有可执行的放行点，且与 §7.6.1、§7A.2 互相矛盾（H22-02）；优化候选的判定状态只靠 Agent 自律，修复段叠在优化段之上时判据失效（H22-03）；目标范围在 Run 创建时定格，AI 后续改到的模块不被验证（H22-04）；AI patch 可以改动验证资产本身，⑤的前提随之落空（H22-05）；BenchPolicy 在样本功效不足时放行，这条缺省值是我方上一轮提出的，在此认领（H22-06）；D22 的独立构建主机形态不是一次性的（H22-07）；ClineSR CLI 以另一 UID 运行后，worker 无法对它 killpg（H22-08）。

**第二部分要点**：X1–X11 的修法本身闭合，gate CAS 唯一化（C-08a/b/c）与 epoch 按实例分配均已验证通过。仍有三处缺口落在恢复臂上：DispatchReceipt 的 intent 跨 broker 实例更替时，两条重派规则与"同 token 至多一个 intent"互相卡死（C12-01）；"静默"谓词的两个分量（broker task lease、登记 pgid）在 01 中没有来源（C12-02）；第四条时间线 indeterminate 之后，自动 probe 没有命令载体，新 epoch 的恢复臂还会重开对账（C12-03）。

---

## 负责人裁决的独立评估

| # | 裁决 | 判断 | 理由 | 对应问题 |
|---|------|------|------|---------|
| ① | UT 与静态审查并行 + 超时显式化 | **有条件成立** | "汇合必经"的四条成立依据我逐条验证过：(i) 原子成组触发、(ii) 超时只能 fail_safe、(iii) 条件③退役旧 cohort、(iv) 审批 CAS 复核。在示例一上，`must(join) = {join} ∪ must(bench_gate) ∪ must(review_static)` 确实包含 ut、benchmark，规则①成立，而且没有改动 V-13b/V-15 共用的普通支配。缺口有两处：同一张图上的规则③仍按字面"每条路径"检查，示例一被拒；§4.3.5 的"不得 succeeded"缺少放行点，还与另外两节冲突 | H22-01、H22-02 |
| ② | Quickbuild 基线锁定（"最新"在 pin 时解析） | **有条件成立** | 在 pin 事务内把"最新"解析为具体版本，是唯一能让 A/B 只差 patch、基线能跨 Run 复用的做法，比 v2.1 的 unpinned_remote 更好。缺口：Quickbuild 侧的解析与 git snapshot 的解析没有规定为同一次解析；"读回版本与锁定不符即无效"只写在 §11.3 测试里，正文没有；unpinned_inputs "不阻断发布"与 §4.3.5 冲突 | H22-12、H22-02 |
| ③ | Profile 小改动复用放宽预案（策略 v2） | **有条件成立** | 全部是确定性规则、缺省关闭、最坏只浪费一轮验证（由 opt_verdict 撤销兜底），方向正确。缺口：函数级校验和依赖伪探针一类编译选项，它属于构建输入，正文没有列入闭包；开启条件写成"差异不显著"，以"不显著"当"等价"，样本少时必然开启 | H22-16、H22-06 |
| ④ | 目标范围与模块登记表 | **有条件成立** | 按模块限定验证范围、改动模块不可剔除、always_run 兜底，这套设计合理。缺口：范围"Run 创建时定格、Run 内不可变"，而 Compiler/UT 的 AI 修复 patch 可以改到范围外的包，这些改动不会被 UT/Benchmark 覆盖，正违背裁决自己的原则"改了的代码必须被验证"；反向依赖模块也没有在审批首屏呈现 | H22-04 |
| ⑤ | 以测试结果检验 AI（取代按能力登记试点） | **有条件成立** | 对产 patch 的 AI，用每轮构建/UT/Benchmark 结果检验，比预先分级更直接，多版本对比报告也给了审批人真正需要的信息。但"测试结果不能造假"有两个前提，文中都没有保证：一是 AI patch 不能改动验证资产（用例、`%check`、告警选项、仓内基准脚本）；二是测试覆盖了 AI 改动所及的范围（见④）。另外，取消登记表之后，原则 2 所说的"数据达标后再扩大使用范围"已经没有可调的开关 | H22-05、H22-04、H22-13 |
| ⑥ | E0 预检改为核对显式指定 base 与读回方式 | **成立** | 与②配套，属于把可行性前置的正确做法。正文缺"读回不符即判无效"的规范条款，已并入 H22-12 | H22-12 |

与负责人原意的取舍：以上候选方案都**保留**负责人的决定（保留并行、保留锁定、保留策略 v2、保留按范围验证、保留以测试结果检验 AI），只补齐使决定能成立的机制。只有两处在原意上加了约束：一是 H22-02 要求 environment_gap 类未完成项（unpinned_inputs、范围内模块无用例）在审批时逐条确认，"不阻断发布"改为"确认后不阻断"；二是 H22-05 要求触及验证资产的 AI 段须经审批人确认。

---

## 上一轮处置落实核对（HLD 侧）

| 处置 | 落实情况 | 备注 |
|------|---------|------|
| K1 特权构建隔离 D22 | 已落实（D22、N7、§2.3、§7.6.1、§8.1、§10、§12、§13 P3 gate、R23） | 独立构建主机形态缺"一次性"约束 → H22-07 |
| K2 外部等待 E-02 | 已落实（§4.3.4、D11、§4.3.1、§4.4、§4.5、§17） | 勘误记录未列出全部偏离冻结语义之处，且 §4.2.4 自相矛盾 → H22-09 |
| K3 示例一单链 / 按 mode 注册 | 单链被裁决①推翻、恢复 join；按 mode 注册已落实 | 规则③未随之调整 → H22-01 |
| K4 修复回流 D15 | 已落实（D15、rpm_fix_loop、§7A.1/7A.2） | 与优化段叠加时的预算与 AI 修复问题 → H22-03 |
| K5 rpm_precheck | 已落实 | — |
| K6 效应身份 | 已落实（§5.2、§7.6.1、§7.8） | remote_build_submit 的标记来源 → H22-14 |
| K7 BenchPolicy | 已落实 | 我方提出的缺省判定在功效不足时放行（认领）→ H22-06 |
| K8 判定与 AI 分离 | 原则 5 已落实；登记表被裁决⑤取代 | → H22-05、H22-13 |
| K9 优化重验证 | 路径强制、opt_verdict、撤销、max_opt_rounds 已落实 | 判定状态未进入运行时强制 → H22-03 |
| K10 Profile | 已落实；裁决③另加策略 v2 | → H22-16 |
| K11 板子池 | 已落实 | 失败归因在单 Run 持板上限 1 下不可达 → H22-20 |
| K12 基线缓存 | 已落实；Quickbuild 部分被裁决②取代 | sys.baseline_build 的归属 → H22-15 |
| K13 input: none | 已落实 | 规则②的适用范围有歧义 → H22-10 |
| K14 E-03 数据面 | 已落实（六条命令） | 镜像 blob 写入路径、租约主动释放语义 → H22-14 |
| K15 Gateway | 已落实 | — |
| K16 ClineSR CLI | 已落实 | 跨 UID 无法 killpg → H22-08 |
| K17 release_requires | 已落实 | "通过"谓词两处定义不一致 → H22-11 |
| K18 MCP | 已落实 | — |
| K19 附录 B 第 7 组 | 已重写 | v2.2 新增项有遗漏 → H22-18 |
| K20 分期 | 已落实 | v2.2 新增项未分期 → H22-19 |
| K21 D13 | 已落实 | — |
| K22 编号 | 已落实；A15 留在 §17 的理由成立 | R25 排在 R23 之前 → H22-21 |

**处置表"未按评审方方案修改"之处的取舍判断**：
- K2 不采 Kimi 的 interrupt/resume：成立，冻结 task 模型里没有 worker 中途退出的映射。
- K3 当时不采 AND-join：当时的理由成立；现已被裁决①以"仅本规则适用"的方式重新引入，见上一节。
- K7 不采 Codex"快速/单项可作发布证据"：成立。
- K10 首期不采 CFG checksum 匹配：成立，裁决③把它改为缺省关闭的策略 v2，与此一致。
- K13 自拟 asserts_nonempty：成立，见 H22-10 的范围补正。
- K14 不加 renew 与 worker 侧查询：成立，租约随 task 存续，命令越少攻击面越小。
- K17 改为运行时谓词：成立。

---

## 第一部分：HLD v2.2 问题清单

### H22-01 [MAJOR] 规则③仍按字面"每条路径"检查，示例一经 review_static 分支被拒

**位置**：§4.2.6 规则③（第 389 行）；§4.2.1 示例一 routes（第 287、296 行）；§11.3"四份示例流水线原文字节加载通过"

**问题**：裁决①恢复了 `compile_image → [ut, review_static]` 并行，并且只为规则①引入了"汇合必经"（明文"仅用于本规则"）。规则③仍写作"每条非失败路径……必须依次经过镜像节点、UT 节点、Benchmark 节点"。示例一中存在这样一条非失败路径：

`optimize --opt_patch_ready--> compile_rpm --build_passed--> compile_image --image_ready--> review_static --review_report_ready--> join:pre_final_review --> review_final --> ci_plan --> human_review`

它经过镜像节点，却不经过 ut、benchmark，因此按字面示例一会被规则③拒绝加载。这与"示例即校验器验收用例、必须可通过"直接矛盾。实现者如果为了让示例通过而放宽规则③，§11.3 的反例"优化回流绕过镜像/UT/Benchmark → 拒绝"也会随之失守。这是上一轮 H2-03 / Codex H-01 同一类问题，在规则③上又出现了一次。

**依据**：规则③："其 `opt_patch_ready` 路由边出发的**每条非失败路径**（不以 fail_safe 终止的路径）在到达 release-approval 型 hitl 或 terminal 节点之前，必须依次经过镜像节点、UT 节点、Benchmark 节点"；规则①："**汇合必经（仅用于本规则）**"；示例一：`{ from: compile_image, on: image_ready, to: [ut, review_static] }`、`{ from: review_static, on: review_report_ready, to: join:pre_final_review }`。

**候选改动方案**：
```diff
-③ **优化重验证（D18）**——……其 `opt_patch_ready` 路由边出发的**每条非失败路径**（不以 fail_safe 终止的路径）在到达 release-approval 型 hitl 或 terminal 节点之前，必须依次经过镜像节点、UT 节点、Benchmark 节点（镜像节点为 `rpm_precheck: required` 时还须先经 RPM 节点）；
+③ **优化重验证（D18）**——……令 G' 为以 `opt_patch_ready` 边的目标节点为起点、删去全部以 fail_safe 终止的边后的子图；对 G' 中每个可达的 release-approval 型 hitl 或 terminal 节点 t，按规则①的**汇合必经**定义在 G' 上计算 must'(t)，要求镜像节点、UT 节点、Benchmark 节点 ∈ must'(t)，且三者在 G' 的支配序上依次出现（镜像节点为 `rpm_precheck: required` 时 RPM 节点亦 ∈ must'(t) 且先于镜像节点）。**汇合必经定义适用于规则①与规则③**，E-01/V-13b 与 V-15 仍用普通支配；
```
**副作用**：汇合必经的适用面从一条规则扩到两条。四条成立依据 (i)–(iv) 与规则①完全相同，不引入新的运行时语义；规则③的运行时兜底同样由审批 CAS 承担（ut_report、bench_report 必须针对当前 series）。V-13b/V-15 不受影响。

**配套测试/夹具**：CF-DSL：示例一原文字节通过规则③；变体"把 bench_gate 改为直接 → review_final、join 只剩 review_static"拒绝（join 最少两源，加上规则③）；变体"opt_patch_ready → review_static（绕开 ut）"拒绝；optimize_campaign 原文仍通过；01 附录 B 第 7 组的"汇合必经形式化"条目改为覆盖规则①③。

### H22-02 [MAJOR] §4.3.5"不得以 succeeded 关闭"缺少放行点，并与 §7.6.1、§7A.2 冲突

**位置**：§4.3.5（第 439–442 行）；§4.2.2 terminal 映射；§4.2.3 路由允许 `on: sys.*`；§8.3 released 固定映射；§7.6.1 兜底（第 559 行）；§7A.2（第 628 行）

**问题**：
1. **执行点缺失**：Run 关闭为 succeeded 只有两条路径。一是 terminal 的 success_on，§4.2.2 规定"outcome ∈ success_on → closed(succeeded)"；二是 release 的 released，§8.3 规定 released → closed(succeeded)，发生在 publishing（point-of-no-return）之后。§4.3.5 要求"存在超时项不得 succeeded"，但没有说在哪里检查。如果在关闭时检查，发布已经发生，再判不成功就违反 §8.3 固定映射；而且 closed 的 reason 集是封闭的，也没有"成功但有缺口"这一项。
2. **超时项可以到达成功路径**：§4.2.3 允许 `on: sys.timeout` 路由到任意节点，于是节点超时后可以经用户路由继续走到 terminal 或审批。
3. **与其他章节冲突**：§7.6.1 说 unpinned_inputs "在 incomplete 清单与审批首屏呈现，不阻断发布"；§7A.2 说"范围内无用例的模块……进入 incomplete 清单"。这两类都不是"流水线配置显式声明的取舍"，按 §4.3.5 有它们就不能 succeeded，与"不阻断发布"相反。
4. **"超时项"与 retried 的边界不清**：节点超时后重试成功的，是否仍算"超时项"，文中没有定义。

**依据**：§4.3.5："Run 只有在 `incomplete` 清单为空、或清单中的每一项都属于流水线配置显式声明的取舍（如显式删除的 Agent、显式移除的验证类别）时，才能以 succeeded 关闭；任何超时项存在时 Run 不得以 succeeded 关闭"；§7.6.1："该输入记入 ImageReport 的 `unpinned_inputs`……在 `incomplete` 清单与审批首屏呈现（§4.3.5），不阻断发布"；§4.2.3："`on` 值 ∈ (该节点 status 全集 ∪ gate outcome 集 ∪ sys.* )"。

**候选改动方案**：
```diff
 - **不以"正常结束"掩盖**：
-  Run 只有在 `incomplete` 清单为空、或清单中的每一项都属于流水线配置显式声明的取舍……时，才能以 succeeded 关闭；任何超时项存在时 Run 不得以 succeeded 关闭。
+  - **条目分类（定案）**：incomplete 每条带 `class`：`timeout`（未被同 task 后续 attempt 成功覆盖的超时；被覆盖者只进 retried）/ `config_tradeoff`（可由 pipeline 原文静态推导：删除的 Agent、移除的 release_requires 类别、optional 降级）/ `environment_gap`（运行期环境事实：unpinned_inputs、范围内模块无用例、baseline_revoked 等）。
+  - **结构保证（校验器）**：`on: sys.timeout` 的目标只能是 fail_safe（重试照常经 `retry` 字段）；join 超时、预算到期、外部等待超时本就固定 fail_safe。因此 timeout 类条目存在 ⇒ Run 必经 fail_safe 关闭，"超时不得 succeeded"不依赖关闭时检查。
+  - **放行点**：release-approval 型 hitl 的决定事务（§8.2 新鲜度 CAS）核对：无 timeout 类条目；每条 environment_gap 都出现在本次决定的 `acknowledged_gaps`（审批 CLI 首屏逐条确认）中，否则拒绝提交。terminal success_on 照常 closed(succeeded)，get_result 的结论字段为 `succeeded_with_gaps`（列出 environment_gap 与 config_tradeoff），终态 reason 集不变。
-  （§7.6.1）……在 `incomplete` 清单与审批首屏呈现（§4.3.5），不阻断发布。
+  （§7.6.1）……作为 environment_gap 进入 `incomplete` 清单，经审批人逐条确认后不阻断发布（§4.3.5）。
```
**副作用**：校验器收紧，把 sys.timeout 路由到诊断节点的流水线会被拒，诊断改由 fail_safe 的 FeedbackReport 承担。审批多一步逐条确认。负责人"未锁定输入不阻断发布"的原意保留为"确认后不阻断"。终态集与 §8.3 映射都不变。

**配套测试/夹具**：CF-DSL：`on: sys.timeout → review_final` 拒绝；CF-AUTH：unpinned_inputs 非空且无 ack 时审批被拒，有 ack 时通过且 ack 写入 ApprovalDecision；超时后重试通过的只进 retried、Run 可 succeeded；terminal 路径存在 environment_gap 时 get_result 为 `succeeded_with_gaps`；§11.3"超时显式化"五例保持。

### H22-03 [MAJOR] 优化候选的判定状态只靠 Agent 自律；修复段叠在优化段之上时判据失效

**位置**：§7A.4（第 660–663 行）；§7A.3 优化轮（第 643 行）；§7A.1 RPM/镜像修复；§4.2.6 规则①的 BenchReport 谓词

**问题**：
1. **"顶端为优化段"会失效**。反例（per_patch，max_opt_rounds=1）：
   - optimize 提交 BOLT 候选 C1（加 `--emit-relocs`），series S1→S2；
   - S2 链接失败，Compiler 交给 LogAnalyzer 做 AI 修复，S2→S3，顶端变为编译修复段；
   - 之后 UT 通过；Benchmark 看到顶端不是优化段，不做第二组 A/B，没有 opt_verdict；
   - optimize 的自身段计数已经等于 1（达到上限），返回 no_further_gain；
   - 结果：C1 从未被判定收益，就进入 bench_gate 与审批。运行时没有任何检查能拦住它。规则①的 Bench 谓词只看 validation_complete，不看候选判定。
2. **max_opt_rounds 与强制撤销冲突**。"自身产出段的计数"是否包含撤销段没有定义。如果包含，达到上限时"返回 no_further_gain"与"neutral/loss → **必须**产出撤销 patch"冲突；实现先判上限的话，就会带着一个已判 loss 的候选放行。
3. **优化引起的编译/镜像失败**会被 AI 修复，并消耗业务修复环（rpm_fix_loop / image_fix_loop）的预算。预算耗尽时，已经通过验证的业务 patch 落入 fail_safe——上一轮 H2-10 要防的正是这种情况。§7A.4 只为 UT 规定了确定性撤销。

**依据**：§7A.4："当前 series 顶端为 Optimization 产出的段时，Benchmark……另对'优化前 vs 优化后'做第二组交叉 A/B"；"Agent 以 series lineage 中自身产出段的计数……在达到上限时返回 `no_further_gain` / `no_gain_found`"；"`neutral` / `loss` / `inconclusive` → **必须**产出撤销 patch"；"UT 失败且失败 series 的顶端为优化段时，UT Agent **不做 AI 修复**"；§4.2.6①："BenchReport = `validation_complete`"。

**候选改动方案**：
```diff
+- **优化候选记录（Ledger，权威）**：OptimizationCandidate{candidate_id, producer_task_id, parent_series_id, parent_tree_digest, parent_image_ref, state ∈ {pending_verdict, accepted, rejected_pending_revert, reverted}}，在 series 推进事务内创建并迁移。**"未决优化段"** = 自某 pending_verdict 候选的段起至当前 head 的全部段（含其后叠加的修复段）。
-当前 series 顶端为 Optimization 产出的段时，Benchmark 除常规"被测 vs 基线"A/B 外，另对"优化前 vs 优化后"做第二组交叉 A/B
+存在 pending_verdict 候选时，Benchmark 另以该候选的 parent_image_ref 为"优化前"做第二组交叉 A/B；opt_verdict 由框架统计库写回候选记录（gain → accepted；其余 → rejected_pending_revert）
+- **运行时强制**：optimize 返回 no_further_gain / no_gain_found 时，若存在 pending_verdict 或 rejected_pending_revert 候选 → `sys.invalid_result`；release-approval 决定事务另核对"无此二态候选"。
+- **计数**：max_opt_rounds 只计候选段，撤销段不计；撤销**优先于**上限判断。
+- **编译/镜像归因**：存在未决优化段时，Compiler 两模式的构建失败一律产出确定性撤销 patch（motivation=`revert_optimization`），不做 AI 修复（与 UT 归因同规则）。校验器另要求：位于优化重验证路径上的修复环 max_rounds ≥ 1 + max_opt_rounds（每个候选至多引发一次确定性撤销）。
```
**副作用**：Ledger 增加一种记录；Benchmark 的二次 A/B 触发条件从"看顶端"改为"看候选状态"，更稳定。修复环最小预算提高，业务 patch 因此多出可用的修复轮次，属于预算放宽，可接受。BOLT/AutoFDO 引起的编译问题不再经 AI 修复，候选直接撤销、记为 rejected，少一次修复机会，换来可判定性。

**配套测试/夹具**：注入"优化段 + 编译修复段叠加"后，二次 A/B 照常执行、opt_verdict 写回候选；候选未判即返回 no_further_gain → sys.invalid_result；max_opt_rounds=1 时 loss 候选仍先撤销再停；优化致链接失败 → 确定性撤销、rpm_fix_loop 计数 +1 且不触顶；审批 CAS 在存在 rejected_pending_revert 时拒绝。

### H22-04 [MAJOR] 目标范围在 Run 创建时定格，AI 修复改到的范围外模块不被验证

**位置**：§7A.7"目标范围的确定（Run 创建时定格，Run 内不可变）"；§7A.1、§7A.2 修复 patch；D12 `bench_suites_digest`

**问题**：范围在创建时由"patch 改动涉及的包"推导，之后不变。可是 Compiler（LogAnalyzer）和 UT 的修复 patch 完全可以改到别的包——修一个头文件、改一个依赖库，都很常见。这些改动进入 series、最终发布，UT 只跑创建时范围内的用例集，Benchmark 只选创建时范围内的套件，结果就是"改了的代码没有被验证"，正是裁决④自己要防止的事。此外，修复 patch 改到未登记的包时会发生什么，文中没有规定（§7A.7 只拒绝 submit_patch）。

还有一层冲突：范围一旦变大，所选套件集合跟着变，而 D12 固化的是"本 Run 引用的套件版本集合"，中途变化就按失配处理，Run 会被 administrative finalize。

反向依赖方面：RPM 阶段构建"受影响包 + 反向依赖闭包"，但验证范围只含被改包所属模块，审批人看不到哪些受影响模块没有验证。

**依据**：§7A.7："有效范围 = patch 改动涉及的包所属模块（……**不可缩小**——改了的代码必须被验证）∪ 开发者在 `create_run` 中显式声明的 `focus_modules`"；"目标范围的确定（Run 创建时定格，Run 内不可变）"；D12："`bench_suites_digest`（本 Run 引用的套件版本集合）……Run 中途变化按 D12 失配处理"。

**候选改动方案**：
```diff
-- **目标范围的确定（Run 创建时定格，Run 内不可变）**：
+- **目标范围的确定（只增不减）**：有效范围 = 当前 series 全部段所涉包的模块 ∪ focus_modules，在每次 series 推进事务内重算并与旧范围取并集（不可缩小）；范围增长写入报告头与多版本对比报告。
+  - 任何 series candidate（含 AI 修复与优化）涉及未登记模块的包 → series_candidate_submit 拒绝（E-CANDIDATE-UNREGISTERED），该 task 不得以 advances 类 status 结束。
+  - 审批首屏与 release_evidence 列出"受影响但不在范围内的模块"（被改包反向依赖闭包所属模块 − 有效范围），作为提示信息，不阻断。
-（D12）`bench_suites_digest`（本 Run 引用的套件版本集合）
+（D12）`bench_suites_digest`（套件注册表在 Run 创建时的完整快照摘要；所选子集 = f(注册表快照, 有效范围) 的确定性函数，范围增长不构成 D12 失配）
```
**副作用**：AI 修复跨模块时 UT/Benchmark 工作量增加，这正符合"改了的必须验证"。D12 改为固化注册表全集快照，Run 中途的注册表变化仍然失配，判定的确定性不变。负责人"不跑无关模块"的原意保留：范围只因真实改动而增长。

**配套测试/夹具**：修复 patch 改到范围外的已登记模块 → 范围增长，下一轮 UT/Benchmark 包含该模块用例集与套件；改到未登记模块 → candidate 拒绝；范围增长不触发 D12 失配，注册表本身变更仍触发；审批快照含"受影响未验证模块"。

### H22-05 [MAJOR] AI patch 可以改动验证资产，"测试结果不能造假"的前提没有保证

**位置**：§7A.0 原则 6；附录 A19 ⑤；§7A.1 修复规则；§7A.2 UT 修复

**问题**：⑤的论证是"方案可以错，测试结果不能造假"。这个结论只在 AI 无法改动验证资产时成立，而 series 里的 patch 恰恰可以改到它们：
- 包内测试源码与 spec 的 `%check` 段（RPM 构建成功谓词的一部分）；
- 告警与 sanitizer 选项（加 `-Wno-*`、`-w`、`#pragma GCC diagnostic ignored`）；
- 仓内的基准脚本或被测入口（对 Benchmark 路径特殊处理）。

UT Agent 的"修复"可能就是改测试本身。§7A.1"不以关闭告警或屏蔽类编译选项绕过"只是 LogAnalyzer 的提示约定，没有确定性检查。这样一来，测试结果虽然没有被篡改，测的东西却已经被改了。

**依据**：§7A.0 原则 6："方案可以错，测试结果不能造假"；§7A.1："真实代码缺陷直接修复……**不以关闭告警或屏蔽类编译选项绕过**"；§7A.2："失败时分析并可产出修复 patch"。

**候选改动方案**：
```diff
+- **验证资产保护（确定性）**：ModuleRegistry 为每个模块登记 `protected_paths`（测试源码、spec `%check` 段、仓内基准脚本与解析规则、告警/sanitizer 选项文件）；框架另带确定性 diff 检查规则（新增 `-Wno-*` / `-w` / diagnostic ignored pragma、删除或短路 `%check`、新增测试跳过标记）。
+- series_candidate_submit 对 AgentProducer 段计算 `verification_touch`；命中 → 段照常接受，但写入多版本对比报告与 release_evidence，并作为 `verification_asset_change` 条目要求审批人在决定中逐条确认（同 H22-02 的 acknowledged_gaps 机制），未确认即拒绝审批。
+- 原则 2 改为：分析类 AI 输出恒为 `ai_draft`，不进入判定字段与路由（原则 5 已保证）；"扩大使用范围"指的是允许其进入确定性检查之外的自动动作，任何此类扩大都须以策略版本形式登记，并进入 execution manifest。
```
**副作用**：合理的测试修正（用例本身有错）仍然允许，只是须经审批人确认；diff 检查规则可能误报，误报的成本是一次人工确认。原则 2 有了真实的开关，回应"先验证再推广"。

**配套测试/夹具**：UT 修复 patch 删除失败用例 → verification_touch 命中，审批无确认时被拒；编译修复加 `-Wno-error` → 命中；正常修复不命中；多版本对比报告标注命中段。

### H22-06 [MAJOR] BenchPolicy 在功效不足时放行；SPEC 判定混用相对与绝对量（认领我方上一轮缺省值）

**位置**：§7A.3（第 638–642 行）；§7A.7 `gate_eligible` 覆盖；§7.8 策略 v2 开启条件

**问题**：
1. **低功效放行**。`regression_pct` 只取"显著回归"指标的点估计，不显著时为 0.00。每臂 n=10、Mann–Whitney U、Holm 校正下，功效有限：例如真实回归 12%、变异系数 15%、8 个必测指标时，最小 p 值的门槛是 α/8≈0.006，这个回归很可能不显著，于是 regression_pct=0.00，`<= 5.0` 的阈值 gate 通过。"缺指标 fail-closed"的原则，在"数据不足以判定"这种最常见的情形下反而成了 fail-open。**这一定义出自我方上一轮 H2-09 的 diff，在此如实认领。**
2. **空覆盖**。§7A.7 规定"`gate_eligible` 以所选集合的覆盖完整为准"；如果范围内模块没有登记套件、always_run 也为空，所选集合为空，validation_complete 空真成立。
3. **inconclusive 指标**（零基线等）不计入 regression_pct，也不会导致字段缺失。
4. **SPEC 混用量纲**。SPEC 多为绝对量（如启动 ≤ 5 s），文中却用效应区间（相对变化）与 SPEC 比较。
5. **策略 v2 的开启条件**写成"差异在 BenchPolicy 判定下不显著"，同样以不显著当等价。

**依据**：§7A.3："指标'显著回归' ⇔ 校正后 p < α ∧ 区间不含 0 ∧ 效应为劣化方向"；"`regression_pct` = 显著回归指标的效应点估计最大值（无显著回归 = "0.00"……）"；"效应区间整体在 SPEC 内 → SPEC-IN"；§7.8："差异在 BenchPolicy 判定下不显著，即可把策略 v2 设为该流水线的新鲜度策略"。

**候选改动方案**：
```diff
-`regression_pct` = 显著回归指标的效应点估计最大值（无显著回归 = "0.00"；任一必测指标样本不足 → 字段缺失 → gate fail-closed）
+`regression_pct` = 全部必测指标"劣化方向效应 95% BCa 区间上界"的最大值，下限截为 0.00（非劣性形式：阈值 gate `<= 5.0` 即"以 95% 置信回归不超过 5%"）；任一必测指标样本不足或为 inconclusive → 字段缺失 → fail-closed。原定义改名 `significant_regression_pct`，只作信息字段（非 gateable）。
+`validation_complete` 另要求所选必测指标集合非空；为空 → `validation_complete=false`，报告注明 `no_metrics_selected`。
-SPEC 三值判定：效应区间整体在 SPEC 内 → SPEC-IN
+SPEC 按 `kind ∈ {absolute, relative}` 登记：absolute 以被测臂中位数的 95% 区间比较 SPEC 边界，relative 以效应区间比较；三值规则不变。
-（§7.8 策略 v2）差异在 BenchPolicy 判定下不显著
+（§7.8 策略 v2）以等价检验（TOST，等价界 δ 随策略参数登记，缺省 1%）证明两组收益差异落在 ±δ 内
```
**副作用**：gate 更严，A/B 更容易判 fail 或缺失，需要更多样本或更低噪声的测量（R24 加重）；阈值的含义从"点估计"变为"置信上界"，套件作者需重新校准阈值。opt_verdict 可以沿用区间写法（gain ⇔ 改善方向区间下界 > 0），保持一致。

**配套测试/夹具**：BenchPolicy golden 增加三例：高噪声大回归（点估计 12%、上界 30%）→ gate fail；所选集合为空 → validation_complete=false；零基线 inconclusive → 字段缺失。absolute/relative SPEC 各一例；策略 v2 开启的 TOST golden 一例。

### H22-07 [MAJOR] D22 的"独立构建主机"形态不是一次性的，root scriptlet 可以跨构建持久化

**位置**：D22（第 123 行）；§7.6.1 LocalGbsBackend；§7.8 基线缓存；R23

**问题**：D22 首选"一次性构建 VM"，E0 不具备 KVM 时改用"独立构建主机（同一契约）"。但契约本身只写了"边界内无凭据、无 Ledger、无 socket"，"每次构建从干净基底开始"并不在契约里。在一台常驻的独立主机上，root 执行的恶意 `%post` 可以驻留下来，篡改之后的每一次构建——包括 `sys.baseline_build` 产出的、跨 Run 共享的基线镜像——从而污染所有 Run 的 A/B 证据与刷到板上的镜像。VM 形态也有同样的隐患：为保住 GBS `--incremental` 的速度而复用 buildroot，就把上一次构建的 root 写入状态带进了下一次。凭据没有泄露，但验证证据的完整性被打穿了。

**依据**：D22："首选同机**一次性构建 VM**（KVM），E0 不具备虚拟化能力时改用**独立构建主机**（同一契约……）；边界内无凭据、无 Ledger、无任何 control-plane socket"；§7.6.1："GBS 增量构建（`--incremental`）"。

**候选改动方案**：
```diff
-| D22 | 特权构建隔离 | ……首选同机**一次性构建 VM**（KVM），E0 不具备虚拟化能力时改用**独立构建主机**（同一契约……）；边界内无凭据、无 Ledger、无任何 control-plane socket……
+| D22 | 特权构建隔离 | ……**契约（两种形态共同）**：① 每次构建自框架构建的**不可变基底**（digest 登记）启动，可写层一次性、构建后丢弃；② 跨构建复用的状态（buildroot 包缓存等）只能由框架自有 task 以锁定输入生成，按构建输入闭包键只读挂载；③ 边界内无凭据、无 Ledger、无任何 control-plane socket；④ 基线构建与 series 构建不共用同一边界实例。独立构建主机须在每次构建前复位（不可变根 + overlay 重置，或重新部署），并在交回产物时附基底 digest 复核；无法复位的主机不得承担构建……
```
**副作用**：独立主机形态的复位有时间开销；增量构建改为"只读缓存 buildroot + 一次性 overlay"，速度依赖缓存命中。

**配套测试/夹具**：特权构建隔离 E2E 增加一例：被测包 `%post` 在边界内写入持久化后门 → 下一次构建（含 sys.baseline_build）的边界中检测不到该文件；基底 digest 不符 → 产物拒收。

### H22-08 [MAJOR] ClineSR CLI 以专用 UID 运行后，worker 无法对它 killpg；超时、心跳自杀与孤儿回收全部失效

**位置**：§7.1"OS 层强制"与"进程管理"（第 526、529 行）；§5.1.2；§8.5 特权 launcher

**问题**：§7.1 要求 CLI 以专用 OS 用户运行，同时"纳入 worker 进程组（超时 killpg）"。按 kill(2)，没有 CAP_KILL 时，发送方的实际或有效 UID 必须与目标的实际 UID 或 saved set-user-ID 相同，否则对该进程返回 EPERM。对进程组发信号时，Linux 只要有一个进程被成功送达就返回成功，其余进程被静默跳过。结果是 worker 以自身 UID 执行 killpg 时，CLI 进程一个也杀不掉。冻结的三条 kill 语义因此对 CLI 全部失效：
- 硬超时 = killpg；
- 心跳丢失时 worker 先 killpg 再退出；
- 编排恢复时按 pgid reap 孤儿。

这些正是"kill 语义不因编排进程失联而缺席"的保证。在 CLI 受提示注入时，这一点尤其关键。

**依据**：§7.1："CLI 以**专用 OS 用户**运行"；"每次调用为独立子进程，纳入 worker 进程组（超时 killpg）"；§5.1.2："心跳丢失时 worker（进程组长）先 killpg 终止本组全部进程……再自行退出"。

**候选改动方案**：
```diff
-  - **进程管理**：每次调用为独立子进程，纳入 worker 进程组（超时 killpg）
+  - **进程管理**：CLI 由 deploy 特权 launcher（§8.5，属可信计算基）以专用用户 spawn，置入该 task 的 cgroup v2 子树；终止一律经 launcher 写 `cgroup.kill`（覆盖跨 UID 进程）。launcher 以 pidfd 监视 worker，worker 退出即 kill 其 task 子树；编排恢复时按 Ledger 登记的 cgroup 路径（而非 pgid）对账回收。同 UID 进程仍按 §5.1.2 的进程组语义处理。
```
**副作用**：launcher 职责扩大（TCB 面略增）；部署需要 cgroup v2 委派，列入 E0 预检。构建隔离边界的启停可以复用同一机制。

**配套测试/夹具**：注入：worker 在 CLI 调用中被 SIGKILL → CLI 在 T 秒内被终止；硬超时 → CLI 被终止；编排崩溃 → launcher 终止 task 子树；CLI fork 的子进程同样被回收。

### H22-09 [MINOR] 勘误 E-02 未列全偏离冻结语义之处；§4.2.4 与 §4.3.4 自相矛盾

**位置**：§17 E-02；§4.2.4（第 374 行）；§4.3.4；§4.3.1 状态图；§4.3.5"外部等待超时"

**问题**：
1. §4.2.4 保留了冻结原文"被取代 series 的在飞任务跑完即弃（MVP 不主动取消）"，而 §4.3.4/§8.6 规定 supersede 时取消远端构建。被取消的挂起 task 以什么形态终结，也没有定义。
2. "持有已授予租约的 Run 在 queued 中优先出队"偏离了冻结的 FIFO。
3. paused 期预算到期 → fail_safe，是一条新的状态迁移；状态图上 paused 只画了 (reject/TTL) 出边。在 paused 下执行 fail_safe 保留节点，是否需要先取执行槽，没有说明。
4. `task_suspend` 没有前置条件"本 attempt 无 claimed/running 效应记录"；有在途效应时挂起，续接 attempt 的启动对账可能把它们判为 abandoned 或 unknown。
5. §4.3.5 列出"外部等待超时"，但 §4.3.4 只定义了 Gateway 登录等待超时；远程构建在途过久、资源排队过久都没有超时字段。

以上都属于冻结语义的改动或补充，应写进勘误记录，否则 01 同步时没有依据。

**依据**：§4.2.4："被取代 series 的在飞任务跑完即弃（MVP 不主动取消）"；§4.3.4："cancel、fail_safe 取消分支、series supersede 退役在飞任务时，编排对相关远程构建发起 Gateway 取消"；"持有已授予租约的 Run 在 queued 中优先出队"。

**候选改动方案**：
```diff
-- 陈旧性：……被取代 series 的在飞任务跑完即弃（MVP 不主动取消）；
+- 陈旧性：……被取代 series 的在飞本地任务跑完即弃（MVP 不主动取消）；挂起中的 task（无 worker）在 supersede 事务内取消其外部等待（远端构建经 Gateway 取消）并以 `sys.superseded` 审计化终结，不参与路由（勘误 E-02）；
 （§4.3.4 新增）
+- `task_suspend` guard：本 attempt 无 claimed/running 效应记录（否则拒绝，Agent 须先完成或失败该效应）。
+- 节点可配置 `external_timeout_min`（缺省 = 所在环 wall_clock）；到期 → 取消外部等待 + 合成 sys.timeout。
+- paused 期预算到期：Run → queued（优先出队）后执行 fail_safe；状态图补 paused ─(budget)→ queued 边。
 （§17 E-02 记录追加）
+  偏离清单：supersede 时主动取消挂起 task 的外部等待；持租约 Run 优先出队；paused 期预算可到期；挂起 task 的 sys.superseded 终结。
```
**副作用**：E-02 的范围文本变长，但 01 同步时有了依据。增加一个保留结果 sys.superseded（不路由）。

**配套测试/夹具**：挂起 task 所属 series 被 supersede → 远端取消、task 以 sys.superseded 终结、无路由；有在途效应时 task_suspend 被拒；external_timeout 到期 → sys.timeout 并进入超时报告；paused 期预算到期 → queued → fail_safe。

### H22-10 [MINOR] 规则②的静态检查适用范围有歧义；input: patch 下净变更为空的 series 未被拒绝

**位置**：§4.2.6 规则②（第 387 行）；§6.5 submit_patch

**问题**：规则②的静态检查没有限定 `input: none`。如果对 input: patch 流水线也适用，示例一中 ci_plan 的路径（build_passed → image_ready → … → release_plan_ready）不经过任何 advances/asserts_nonempty 边，会被拒绝。另外，input: patch 时，submit_patch 如果收到净变更为空的 series（例如 patch 加上它的 revert），"needs-patch 节点不会面对无净变更 series"这条保证就不成立了。

**依据**：规则②："**静态检查**：任一声明 `input_requirement: patch` 的节点，从 entry 到它的**每条路径**都必须经过至少一条 series_effect ∈ {advances, asserts_nonempty} 的路由边"。

**候选改动方案**：
```diff
-**静态检查**：任一声明 `input_requirement: patch` 的节点，
+**静态检查（仅 `input: none`）**：任一声明 `input_requirement: patch` 的节点，
+`input: patch` 时 submit_patch 另拒绝净变更为空的 series（应用后 tree_digest = snapshot 的 tree_digest，E-SKILL-EMPTY-SERIES），由此保证同一性质。
```
**副作用**：无。

**配套测试/夹具**：示例一原文通过规则②；patch + revert 组成的 series 被 submit_patch 拒绝（MCP 与 HTTP 一致）。

### H22-11 [MINOR] 报告"通过"谓词两处定义不一致，且漏掉撤销与读回失败等情形

**位置**：§4.2.6 规则①；§7A.3"gate_eligible"；§7.8 baseline_revoked；§7.7 坏镜像标记；§11.3 Quickbuild 读回

**问题**：
1. 规则①写的是"BenchReport = `validation_complete`"，§7A.3 写的是"release_requires 的'通过'谓词只认 gate_eligible 报告"（= mode==full ∧ validation_complete），两处不同。
2. 被标记 `baseline_revoked` 的 BenchReport、`comparison: none` 的报告是否算"通过"，没有说。
3. ImageReport 被 §7.7 标记为坏镜像后，"构建成功"谓词仍然为真。
4. "Quickbuild 读回版本与锁定不符 → 构建结果判为无效"只出现在 §11.3 测试中，谓词里没有。

**依据**：规则①："BenchReport = `validation_complete`——覆盖完整且满足 BenchPolicy 样本要求"；§7A.3："阈值 gate 的指标解析与 release_requires 的'通过'谓词只认 gate_eligible 报告"。

**候选改动方案**：
```diff
-（各报告类型的"通过"谓词由 01 定义：BuildReport/ImageReport = 构建成功、UTReport = 全部用例通过、BenchReport = `validation_complete`……）
+（"通过"谓词，01 形式化：BuildReport = succeeded；ImageReport = succeeded ∧ ¬bad_image ∧ 读回版本 = 锁定版本（Quickbuild 后端）；UTReport = 所选用例集全部通过；BenchReport = gate_eligible ∧ comparison ≠ none ∧ ¬baseline_revoked ∧ 无未决优化候选（H22-03））
```
**副作用**：撤销或读回失败后需要重新验证，审批可能因此推迟。

**配套测试/夹具**：每个谓词分量各给一例反例，审批 CAS 均拒绝。

### H22-12 [MINOR] Quickbuild 锁定：解析来源要唯一，读回校验要写进正文，"干净应用"要有定义

**位置**：§7.6.1"基线锁定""开发者 patch 的基线早于锁定 base"；§7.6.2

**问题**：
1. 同一 Run 若 RPM 阶段走本地 GBS（git snapshot 的 commit）、镜像阶段走 Quickbuild（"最新"另行解析），两者可能落到不同版本：RPM 验证的是 X，镜像构建的是 Y。正文没有规定 Quickbuild 侧逐包版本必须取自同一份 snapshot manifest。
2. 读回校验只在测试里出现（见 H22-11）。
3. "可在锁定 base 上干净应用"没有排除 fuzz 或三方合并。

**依据**：§7.6.1："未给出的包把'最新'**解析为具体 CL / commit 并记录**"；"`submit_patch` 校验 patch 可在锁定 base 上干净应用"。

**候选改动方案**：
```diff
+- **单一解析**：Quickbuild 侧逐包版本一律取自本 Run snapshot manifest 中该包所属仓的 commit（与本地后端同一次解析）；manifest 未覆盖的包由同一 pin 事务解析并写入 manifest。
+- **读回校验（规范条款）**：每次 Quickbuild 构建完成后，Gateway 读回实际使用的 base 快照、逐包版本与 build.conf，与锁定值逐项比对；任一不符 → 该构建判为无效（ImageReport.succeeded=false，原因 `base_mismatch`），不进入缓存。
+- "干净应用" = 零 fuzz、不做三方合并（`git apply --index` 严格模式）。
```
**副作用**：无。

**配套测试/夹具**：FakeQuickbuild 读回不符 → base_mismatch；RPM/镜像跨后端时版本一致性断言；需要 fuzz 才能应用的 patch 被拒。

### H22-13 [MINOR] 多版本对比报告缺少生成触发点与 digest 绑定

**位置**：§7A.0 原则 6；§7A.6；§8.2

**问题**：报告"在 ci_plan 产出发布计划前，由框架统计库确定性生成"，写入 release_evidence。但没有规定由哪个事务生成、它的 digest 是否进入 ReleaseManifest（从而进入授权绑定）；terminal 型流水线（示例二的 report_no_gain）是否也生成，同样没说。如果报告与审批对象不绑定，审批人看到的对比报告可能不对应被批准的 series。

**依据**：原则 6："在 ci_plan 产出发布计划前，由框架统计库确定性生成（不由 AI 生成），写入 `release_evidence` 并作为审批 CLI 首屏"。

**候选改动方案**：
```diff
-在 ci_plan 产出发布计划前，由框架统计库确定性生成（不由 AI 生成），写入 `release_evidence`
+由编排在 ci_plan 的 task 完成事务内（terminal 型在 terminal 映射前、fail_safe 在 FeedbackReport 生成时）以框架统计库确定性生成，作为内容寻址 artifact；其 digest 写入 ReleaseManifest.release_evidence，从而进入 release_manifest_digest 与授权绑定
```
**副作用**：无。

**配套测试/夹具**：篡改对比报告 → manifest digest 失配、核销拒绝；terminal 与 fail_safe 两条路径都有报告。

### H22-14 [MINOR] E-03 细节：镜像 blob 的写入方、远程构建标记的来源、租约主动释放的语义

**位置**：§8.5 E-03；§7.8"对业务 worker 只读"；§7.7 回收

**问题**：
1. 镜像存储"对业务 worker 只读"，但 Blob 提交协议要求上传方写临时命名空间并 fsync/rename，`image_commit` 又只是索引事务。那么从构建边界导出的镜像由谁写入存储，没有说。
2. `remote_build_submit` 的效应标记若取自载荷，worker 可以借用其他记录的 idem_key 指纹，造成归因串用。
3. `resource_lease_release` 之后 worker 仍然存活，而回收要求"旧 worker 进程组已 reap"，主动释放实际上要等到 task 结束才能完成，与"释放"的本意不符。

**依据**：§7.8："三者的权威状态……**对业务 worker 只读**"；§8.5："`image_commit`（镜像存储提交协议的索引事务）"；"`remote_build_submit` / `remote_build_fetch_logs`（编排以连接上下文校验 run/task 归属后转发 Gateway）"。

**候选改动方案**：
```diff
+- 镜像 blob 由 launcher 自构建边界的只读导出通道写入镜像存储临时命名空间（持 active-upload lease），worker 只调用 image_commit 提交索引；worker 对存储目录无写权限。
+- remote_build_submit 载荷只引用本 task 已 claimed 的效应记录（idem_key + version），效应标记由编排据该记录推导，不信载荷。
+- resource_lease_release：板型适配器能在板侧强制 generation 时立即进入 reclaiming；不能时标记 release_requested，在 task 结束后按 §7.7 完成回收。
```
**副作用**：launcher 增加一项导入职责。

**配套测试/夹具**：worker 直接写镜像存储 → 权限拒绝；remote_build_submit 引用他 task 的 idem_key → 拒绝；无板侧 fencing 时主动释放后，板子在 task 结束前不被再分配。

### H22-15 [MINOR] sys.baseline_build 的归属、预算与取消语义未定义

**位置**：§7.8 基线缓存"写入""single-flight"

**问题**：sys.baseline_build 由某个 Run 的 Benchmark 分派前置条件触发，同键请求 single-flight，其他 Run 共享等待。但它属于哪个 Run、消耗谁的预算、占谁的执行槽、发起 Run 被取消后其他等待者怎么办，都没有说。按"取消传导"，发起 Run 被 cancel 会连带取消基线构建，其他 Run 就只能等到预算耗尽。

**依据**：§7.8："未命中时由编排分派 `sys.baseline_build` 并以资源等待挂起 Benchmark dispatch（§4.3.4）；同键请求 **single-flight**（只构建一次，其余等待）"。

**候选改动方案**：
```diff
+- sys.baseline_build 归属**缓存**而非某个 Run：以框架内部 Run（`sys` principal，独立预算与执行队列条目）执行；等待者以 kind=resource 等待其完成；任一等待者取消只移除自身等待；全部等待者都取消时才取消构建。基线构建失败 → 全部等待者收到 baseline_unavailable。
```
**副作用**：多一个框架内部 Run 类型。

**配套测试/夹具**：两个 Run 等待同一基线，发起者取消，另一个 Run 仍拿到基线；全部取消 → 构建取消；失败时广播 baseline_unavailable。

### H22-16 [MINOR] 策略 v2 的函数级校验和依赖构建选项，未列入构建输入闭包

**位置**：§7.8 策略 v2 第 2 条

**问题**：伪探针 CFG 校验和要求被采样的二进制与当前构建都带伪探针选项（如 `-fpseudo-probe-for-profiling`）。这是会改变产物的构建选项，必须出现在构建输入闭包或 series 里，A/B 两侧也必须一致。正文没有说明它从哪来、是否随优化 patch 进入包仓。

**依据**：策略 v2："以编译器为每个函数计算的校验和（伪探针 CFG 校验和一类）对比 profile 采集时的版本与当前版本"。

**候选改动方案**：
```diff
+  0. **前置**：策略 v2 只适用于以伪探针选项构建的包；该选项作为优化 patch 的一部分进入包仓（与 `--emit-relocs` 同理），进入构建输入闭包摘要；采集版本与当前版本任一缺伪探针 → 按策略 v1 处理。
```
**副作用**：首次启用策略 v2 时需要先发布一次带伪探针的构建配置。

**配套测试/夹具**：缺伪探针 → 回退 v1；伪探针选项差异 → 闭包不一致、A/B 拒绝比较。

### H22-17 [MINOR] 四份示例中两份没有原文；01 A4 的 compiler_bench_only 与 v2.2 规则冲突

**位置**：§2.4"随仓流水线示例"；§11.3"四份示例流水线原文字节加载通过"；01 附录 A4

**问题**：`compiler_only.yaml` 与 `compiler_bench_only.yaml` 在 HLD 中没有原文，仓库 `pipelines/` 目录也只有 .gitkeep，"原文字节加载通过"无从验收。唯一的规范原文是 01 附录 A4 的 compiler_bench_only，它在 v2.2 规则下不成立：
- `compiler: {agent_type: compiler}` 没有 mode，按 mode 注册时无法取集合；
- benchmark 硬依赖镜像引用（§6.3），图中没有镜像节点，V-15 不过；
- 状态名 bench_done/build_passed 与 v2.2 注册集未对齐。

**依据**：§2.4："随仓流水线示例：`full_pipeline.yaml`……`compiler_only.yaml`（只编译+出镜像）、`compiler_bench_only.yaml`（编译+Benchmark）"；§6.3："benchmark、UT hard-require 镜像引用"。

**候选改动方案**：
```diff
+#### 4.2.1 示例三、示例四（原文）
+```yaml
+pipeline: compiler_bench_only
+dsl_version: 1
+nodes:
+  compile_rpm:   { agent_type: compiler, mode: rpm }
+  compile_image: { agent_type: compiler, mode: image, config: { backend: local, rpm_precheck: required } }
+  benchmark:     { agent_type: benchmark, config: { suites: auto, mode: full } }
+  bench_gate:    { gate: threshold, metric: benchmark.regression_pct, op: "<=", value: 5.0 }
+  summary:       { agent_type: review, mode: final, terminal: true, success_on: [review_report_ready] }
+entry: compile_rpm
+loops:
+  - { id: rpm_fix_loop, edges: [ { from: compile_rpm, to: compile_rpm } ], budget: { max_rounds: 3, max_wall_clock_min: 480 } }
+  - { id: image_fix_loop, edges: [ { from: compile_image, to: compile_rpm } ], budget: { max_rounds: 2, max_wall_clock_min: 480 } }
+routes:
+  - { from: compile_rpm,   on: build_passed,          to: compile_image }
+  - { from: compile_rpm,   on: build_fix_patch_ready, to: compile_rpm }
+  - { from: compile_image, on: image_ready,           to: benchmark }
+  - { from: compile_image, on: image_fix_patch_ready, to: compile_rpm }
+  - { from: benchmark,     on: bench_done,            to: bench_gate }
+  - { from: bench_gate,    on: pass,                  to: summary }
+default_route: fail_safe
+run_budget: { max_wall_clock_min: 1440 }
+```
+（compiler_only.yaml 同形，去掉 benchmark/bench_gate，`compile_image` 的 image_ready → terminal。）
```
**副作用**：01 A4 需要同步替换（见同步项 S-05）。

**配套测试/夹具**：四份原文字节加载通过；01 CF-FIX-00 注册集按 mode 对齐。

### H22-18 [MINOR] 附录 B 第 7 组未收入 v2.2 新增的若干 [01] 项

**位置**：§16 第 7 组

**问题**：以下已定案、须由 01 形式化的项，第 7 组没有收入：
- 校验规则"gate_expired 的目标不得与 approved 相同"，以及 join 超时固定 fail_safe 的说明；
- 保留 agent_type `sys.baseline_build`（保留命名空间与注册）；
- `ctx.await_external` / `task_suspend` 的 guard（H22-09）；
- incomplete 条目分类与 `acknowledged_gaps`（若采纳 H22-02）；
- OptimizationCandidate 记录（若采纳 H22-03）；
- ModuleRegistry 的 `protected_paths`（若采纳 H22-05）；
- launcher 的 cgroup 契约（若采纳 H22-08）。

**依据**：§4.3.5："`gate_expired` 的路由目标不得与 `approved` 相同"；§7.8："保留 agent_type `sys.baseline_build`"。

**候选改动方案**：
```diff
    - **注册与 DSL**：……
+     V 规则：gate_expired 目标 ≠ approved 目标；`on: sys.timeout` 只能指向 fail_safe（H22-02）；保留 agent_type 命名空间 `sys.*`（含 sys.baseline_build）。
    - **状态机与等待（E-02）**：……
+     task_suspend guard（无在途效应）；sys.superseded；external_timeout_min。
    - **报告与消息**：……
+     incomplete 条目 class 与 ApprovalDecision.acknowledged_gaps；OptimizationCandidate；ModuleRegistry.protected_paths 与 verification_touch。
+   - **部署契约**：launcher 的 cgroup v2 spawn/kill 接口。
```
**副作用**：无。

**配套测试/夹具**：01 同步时逐条落 CF 用例。

### H22-19 [MINOR] v2.2 新增项没有落到 §13 分期

**位置**：§13

**问题**：§13 没有交代以下几项在哪个阶段交付：
- ModuleRegistry 与目标范围：UT Agent 并行线就需要它，P4 端到端也离不开；
- 多版本对比报告：P4 端到端的 CLI 审批首屏就要用；
- §4.3.5 的 incomplete/retried 清单：P2 MCP 服务的 get_result 契约；
- 策略 v2：P7。

其中，多版本对比报告依赖"框架统计库"，而这个库在 P7 才随 Benchmark 交付。

**依据**：§13 P4："端到端：全量与子集流水线（mock 业务 Agent + 真实构建与镜像 + CLI 审批……）"。

**候选改动方案**：
```diff
-| P2 | SDK…… + MCP 服务（含 HTTP 端点）与配套 Skill ……
+| P2 | SDK…… + MCP 服务（含 HTTP 端点，get_result 含 incomplete/retried 清单）与配套 Skill ……
-| P4 | 端到端：全量与子集流水线……
+| P4 | 端到端：全量与子集流水线……+ ModuleRegistry 与目标范围 + 多版本对比报告（构建/UT 列；Benchmark 列在 P7 补齐）
-| P7 | **Benchmark Agent**……
+| P7 | **Benchmark Agent**……+ 多版本对比报告 Benchmark 列 + Profile 新鲜度策略 v2 验证
```
**副作用**：无。

**配套测试/夹具**：各 gate 增加对应验收项。

### H22-20 [MINOR] 板子失败归因在"单 Run 持板上限 1 + 分派前授予"下不可达

**位置**：§7.7 刷机失败归因；§7.6.3 单 Run 持板上限（缺省 1）

**问题**："同一镜像在 ≥2 块板上刷机失败 → 归因镜像"需要在第二块板上重试。但租约是分派前授予、随 task 存续的，单 Run 同时只能持一块板，重试时可能又分到同一块板。由谁触发换板重试、如何排除已失败的板，没有定义，归因规则实际上走不到。

**依据**：§7.7："同一镜像在 ≥2 块板上刷机失败 → 归因镜像"；§7.6.3："**单 Run 同时持有板数上限**，配置，缺省 1"。

**候选改动方案**：
```diff
+- 刷机失败时 task 以 sys.error 结束（节点 retry 处理）；重试 attempt 的分派授予排除该 task 已失败的板（exclude_boards 持久化于 dispatch）；无其他满足能力的板 → 以资源等待排队，等待超时按 external_timeout_min 处理。
```
**副作用**：无。

**配套测试/夹具**：板 A 刷机失败 → 重试分到板 B；B 也失败 → 镜像被标坏，两块板都不计数。

### H22-21 [NIT] 编号与措辞

**位置**：§14；§4.2.4

**问题**：
1. 风险表顺序为 R22、R25、R23、R24。
2. §4.2.4 写"仅不计费等待的 paused 区间与 publishing 时段扣除"，与 §4.3.4 的"全集条件"等价，但措辞不同，建议直接引用后者。
3. 示例一 `pre_final_review.timeout_min: 720` 从首个到达起算：静态审查分支先到，Benchmark 分支在排队计费时可能超过 12 小时，作为示例偏紧。

**候选改动方案**：
```diff
-| R25 | 只按目标范围验证……
-| R23 | 构建隔离边界……
+| R23 | 构建隔离边界……
+| R24 | ……
+| R25 | 只按目标范围验证……
-……计时口径同 §4.5（扣除区间按 §4.3.4 等待类别规则：仅不计费等待的 paused 区间与 publishing 时段扣除，计费外部等待计入）
+……计时口径同 §4.5（扣除区间按 §4.3.4 全集条件）
```
**副作用**：无。**配套测试/夹具**：无。

---

## 第二部分：01_Contract_Spec v0.12 问题清单

### 恢复臂四条时间线 × 崩溃点走查

| 时间线 | 路径 | 崩溃点 | 结论 |
|--------|------|--------|------|
| T1 正常 | consume granted → 执行 → release_outcome | consume 的 ACK 丢失（同实例断连重连，epoch 不变，receipt 命中）；outcome 的 ACK 丢失；编排在 C-10 事务前后崩溃 | **闭合**（X2 已验证：按实例分配 epoch 后，CF-AUTH-11 可达） |
| T2 broker 发布前崩溃 | 新实例 hello → §2.2d 扫描 → 等旧 holder 静默 → 重派 → ④ resumed → reconcile not_happened → 原子许可 → Proceed → 执行 → outcome | ① DispatchReceipt 已 completed 时崩溃 | 主干闭合（X6 已验证）；但"静默"不可计算 → **C12-02** |
| 〃 | 〃 | ② receipt 仍为 intent 时崩溃（已受理、未 ACK，或发送失败）| 两条重派规则与"至多一个 intent"互卡 → **C12-01** |
| 〃 | 〃 | ③ publishing 下 D12 漂移叠加 | 闭合（X4 已验证：resumed 不阻断，not_happened 同事务映射） |
| T3 broker 发布后崩溃 | 同 T2 → reconcile happened → ledger 级 released | 同 T2 ①② | 映射闭合；可达性同 T2（C12-01、C12-02） |
| T4 不可判定 | resumed → reconcile indeterminate → C-11 | holder 在 indeterminate 后崩溃、新实例上线 | 自动 probe 没有命令载体；新 epoch 的 ④ 会重置 recovery_state → **C12-03** |
| gate 支线 | decision_submit / C-08c → outbox → C-08a/b | paused/running × 决定/TTL；重复投递 | **闭合**（X1 已验证；Run=queued 时消费推迟到 running 后经 C-08b 完成，不丢失） |

### C12-01 [MAJOR] DispatchReceipt 的 intent 跨 broker 实例更替时，两条重派规则与"同 token 至多一个 intent"互相卡死

**位置**：§2.5 DispatchReceipt 注释（第 288–293 行）；§2.2d 持有者更替重派（第 184 行）；CF-IPC-10

**问题**：01 有两条重派规则：
- §2.5："intent 无 completed → 以**同 request_id** 重派"；
- §2.2d：target_epoch ≠ 当前 epoch → 写一条**新** intent（新 request_id，recovery=true）。

另有约束"同一 token 至多一个 intent"。设 receipt R1 处于 intent（target_epoch=E1）：broker E1 已受理 dispatch 但在 ACK 前崩溃，或者编排发送时 E1 已经不在。之后 E2 上线 hello，§2.2d 的扫描命中 R1（E1 ≠ E2），要写 R2 intent，被"至多一个 intent"拒绝。§2.5 的规则则用 R1 的 request_id 向 E2 重派，但 R1.target_epoch 仍是 E1、recovery 仍为 false，于是每次扫描都会再次命中 R1。两条规则谁先执行、R1 最终处于什么状态，都没有定义：结果要么滞留，要么两条规则各重派一次。

另外，§2.2d 的"最近一次**送达**的 target_epoch"是否包括 intent，也不明确。CF-IPC-10 虽然列了"broker 受理后 ACK 前"与"同时注入"，期望写的却是"按 DispatchReceipt 状态重派或复用"，没有给出唯一结果。

**依据**：§2.5："约束：同一 token 任一时刻至多一个 state=intent 的 receipt（第二个 intent 拒绝——防并发重派）。恢复：intent 无 completed → 以同 request_id 重派"；§2.2d："扫描全部非终态 release task 中'最近一次送达的 target_epoch ≠ 当前 epoch'者：……以新 DispatchReceipt（intent，新 request_id，recovery=true）重新送达"。

**候选改动方案**：
```diff
-    state: Literal["intent","completed"]
+    state: Literal["intent","completed","superseded"]
-# 恢复：intent 无 completed → 以同 request_id 重派（broker 进程内去重 + 授权状态机承接）；
+# 恢复（两条规则按 target_epoch 互斥）：
+#  (a) intent 无 completed ∧ target_epoch == 当前 epoch → 以同 request_id 重派（同一 broker 实例进程内去重）；
+#  (b) 最近一条 receipt（任一 state）的 target_epoch ≠ 当前 epoch → 只经 §2.2d 持有者更替重派：同一事务内把该 token 的全部 intent 迁为 superseded，
+#      再写新 intent（新 request_id、target_epoch = 当前 epoch、recovery=true）；"至多一个 intent"约束不变。
+# superseded receipt 的迟到响应只记审计，不改变授权与 Run 状态。
-扫描全部非终态 release task 中"最近一次送达的 target_epoch ≠ 当前 epoch"者
+扫描全部非终态 release task 中"最近一条 DispatchReceipt（任一 state）的 target_epoch ≠ 当前 epoch"者
```
**副作用**：receipt 增加一个终态。重派规则从两条可能重叠变为互斥，CF-IPC-10 有了唯一期望。

**配套测试/夹具**：CF-IPC-10 增加第六点"intent 已写、broker 受理前或受理后 ACK 前崩溃、新实例 hello"，分别在编排不重启、编排同时重启两种情形下断言：R1 → superseded；R2 intent → completed；broker 侧无双执行；R1 的迟到 ACK 只写审计。CF-IPC-06 增加"superseded receipt 的迟到响应"一例。

### C12-02 [MAJOR] "静默"谓词的两个分量在 01 中没有来源：broker task lease 无机制，pgid 由 broker 自报

**位置**：§2.2d 静默定义（第 182 行）与重派触发（第 184 行）；§5.1 broker socket 命令面；BrokerHelloRequest（第 541 行）

**问题**：静默 = "旧 holder 的 broker task lease 已回收 ∧ 其登记 pgid 已 reap 确认"。它是防止双重发布的关键 guard，同时用于 ④、confirm_not_released、C-11 与重派。但：
1. **broker task lease 没有任何机制**。broker socket 只有 broker_hello、authorization_consume、release_reconcile_report、release_outcome 四条命令，没有心跳；heartbeat 只存在于 worker 数据面。lease 何时授予、如何续期、何时算"丢失"、何时算"回收"，都没有定义，"当前 holder 的 broker task lease 丢失"这个重派触发条件也就无从实现。
2. **"登记 pgid"来自 BrokerHelloRequest 的自报字段**（broker_pid、broker_pgid、broker_start_time），编排没有用 SO_PEERCRED 与 /proc 复核。自报的 pgid 如果有误（例如实现缓存了旧值），静默检查会对一个不存在的 pgid 得出"已 reap"，从而错误放行重派或 confirm_not_released。
3. **编排不是 broker 的父进程，无法 reap**（waitpid 只适用于子进程）。"reap 确认"在这里只能表示"该 pgid 下已无存活进程"，需要写明判据。另外，broker 若在子进程中执行发布且这些子进程 setsid，pgid 检查也覆盖不到它们。

**依据**：§2.2d："旧 holder 的 broker task lease **已回收** ∧ 其登记 pgid **已 reap 确认**"；"编排在受理新 broker 实例的 broker_hello 或当前 holder 的 broker task lease 丢失后，扫描"；`class BrokerHelloRequest(BaseModel): broker_pid: int; broker_pgid: int; broker_start_time: datetime`；§5.1 broker socket 命令面。

**候选改动方案**：
```diff
+- **BrokerInstanceLease（Ledger）**：{broker_epoch, pid, pgid, start_time, lease_expires_at, state ∈ {live, lapsed, reclaimed}}。hello 时编排以 SO_PEERCRED 取 pid，读 /proc/<pid>/stat 取 pgid 与 starttime，与载荷逐项比对，不符 → E-CP-FORBIDDEN（载荷仅作回显）。
+- 续期：broker socket 增加 `heartbeat`（复用 HeartbeatRequest，幂等域 (broker_epoch, command)，与 worker 一样不存响应）；连接关闭且超过 lease 时长未续期 → lapsed（这就是重派触发里的"lease 丢失"）；编排在回收事务内迁 reclaimed。
-- **静默（唯一定义……）**：旧 holder 的 broker task lease **已回收** ∧ 其登记 pgid **已 reap 确认**
+- **静默（唯一定义……）**：旧实例 lease = reclaimed ∧ 不存在属于其 pgid、且 starttime ≥ 实例 start_time 的存活进程（kill(-pgid, 0) = ESRCH，或扫描 /proc）。部署契约：broker 的发布执行子进程不得脱离实例进程组（禁止 setsid），由 deploy 资产与 conformance 检查保证。
```
**副作用**：broker socket 增加一条命令，CommandName 由 19 变为 20（若与 C12-03 一并落地则为 21），A0 与注册表同步更新。broker 实现须维持心跳。

**配套测试/夹具**：CF-AUTH-18：hello 载荷与 SO_PEERCRED / /proc 不符 → FORBIDDEN。CF-AUTH-19：断连后超时 → lapsed → 触发扫描；未超时重连 → 保持 live。CF-AUTH-09c：pgid 内仍有子进程存活 → 不静默。CF-AUTH-09d：pid 被复用但 starttime 不同 → 判为静默。

### C12-03 [MAJOR] 第四条时间线未闭合：自动 probe 没有命令载体；新 epoch 的 ④ 会重开已转 indeterminate 的对账

**位置**：§2.2a④ indeterminate 分支（第 175 行）；④ guard（第 172 行）；§2.2c（第 179 行）；C-11；CF-AUTH-17；§4.3 注册面"publish.* 仅 broker"

**问题**：
1. **自动 probe 无载体**。§2.2c 规定"自动周期 probe 得出确定结论 → 等同对应 broker outcome"，CF-AUTH-17 也以"C-11 自动 probe 得 not_happened → release_failed 映射"为期望。可命令注册表里没有任何一条命令能把发布的 probe 结论送回 Ledger：probe_report 只服务于 EffectRecord（按 idem_key/version，由 reconciliation worker 执行，而 publish.* 效应只能由 broker 注册）；indeterminate 之后 release_reconcile_report 又被 C-10a guard 拒绝。因此 T4 实际上只能靠人工裁决关闭，CF-AUTH-17 后半无法照文实现。
2. **新 epoch 重开对账**。④ 的 guard 不检查 recovery_state，命中时无条件置 `recovery_state := reconcile_required`。§2.2d 的重派扫描也不排除 indeterminate 的 task。于是当 E2 报 indeterminate 后崩溃、E3 上线时，重派 → ④ resumed → recovery_state 被重置，E3 可以再次 reconcile。这与"此后同授权的 reconcile_report **一律** E-CP-ILLEGAL-STATE，终局只经 C-11"相矛盾——C11-06 处置要消除的"同一观测两种终局"，在跨 epoch 时又回来了。

**依据**：§2.2a④："indeterminate → recovery_state := indeterminate……此后同授权的 reconcile_report 一律 E-CP-ILLEGAL-STATE（C-10a guard），终局只经 C-11（裁决或自动 probe 定论）"；④ guard："Run=publishing ∧ 授权 consumed_by_task_id == 本 task ∧ 全绑定匹配 ∧ 连接 epoch > 授权 granted_epoch ∧ 旧执行已静默 → 响应 resumed(reconcile_required)，同事务 granted_epoch := 连接 epoch、recovery_state := reconcile_required"；§2.2c："自动周期 probe 得出确定结论 → 等同对应 broker outcome"。

**候选改动方案**：
```diff
-guard = Run=publishing ∧ 授权 consumed_by_task_id == 本 task ∧ 全绑定匹配 ∧ **连接 epoch > 授权 granted_epoch ∧ 旧执行已静默**
+guard = Run=publishing ∧ 授权 consumed_by_task_id == 本 task ∧ 全绑定匹配 ∧ recovery_state ≠ indeterminate ∧ **连接 epoch > 授权 granted_epoch ∧ 旧执行已静默**
+（recovery_state = indeterminate 时 consume → ConsumeRejected(reason="recovery_indeterminate")，Run 不变）
-扫描全部非终态 release task 中……
+扫描全部 recovery_state ≠ indeterminate 的非终态 release task 中……；indeterminate 者改由下述 probe 通道驱动
+- **发布 probe 通道（C-11 自动定论的唯一载体）**：编排按周期向当前 broker 发 `release_dispatch{…, mode: "probe_only"}`（mode 缺省 "execute"）；broker 只查远端、不执行，并以 `release_probe_report{task_id, probe: confirmed_happened|confirmed_not_happened|indeterminate, remote_refs, probe_seq}` 上报。
+  guard：Run=publishing ∧ recovery_state = indeterminate ∧ 连接 epoch == 当前 epoch；幂等域 (broker_epoch, command)。
+  映射：confirmed_happened → released 映射；confirmed_not_happened → 另需 granted_epoch 持有者静默（§2.2d），满足 → release_failed 映射（同 (b) pending 序），不满足 → E-CP-ILLEGAL-STATE；indeterminate → 记录、继续周期。
```
**副作用**：CommandName 增加 release_probe_report，ReleaseDispatch 增加 mode 字段，ConsumeRejected.reason 增加一个值，A0 同步。如果负责人不希望新增命令，最小改法是删除 §2.2c 的"自动周期 probe"表述与 CF-AUTH-17 后半，T4 只经人工裁决（R13）关闭，同时仍须给 ④ 加上 recovery_state ≠ indeterminate。

**配套测试/夹具**：CF-AUTH-17 按新通道改写。CF-AUTH-17b：E2 报 indeterminate 后崩溃，E3 hello → 不做 execute 重派，consume 被 rejected(recovery_indeterminate)，probe_only → not_happened 且 E2 已静默 → release_failed。CF-AUTH-17c：probe 报 not_happened 但持有者未静默 → ILLEGAL-STATE。CF-AUTH-17d：probe 报 happened → released。

### C12-04 [MINOR] "null request_id 的 FramingError → 断开重连"对 worker 的 per-task socketpair 不可行

**位置**：§5.1 统一处理序末句（第 568 行）；CF-IPC-09

**问题**：worker 与 reconciliation worker 的通道是 spawn 时注入的 socketpair，没有监听端点，断开后无法重连；而且 worker 侧 socket EOF 会触发 killpg 自杀。"关闭连接、重连后重投"只适用于 broker、approval 与运维 socket。

**依据**：§5.1："客户端收到 request_id=None 的 FramingError → 视为连接级协议错误，关闭连接、重连后对全部在途请求按 ACK 丢失重投"；"heartbeat……worker 侧 socket EOF = 通道失 → killpg 自杀"。

**候选改动方案**：
```diff
-客户端收到 request_id=None 的 FramingError → 视为连接级协议错误，关闭连接、重连后对全部在途请求按 ACK 丢失重投。
+客户端收到 request_id=None 的 FramingError → 视为连接级协议错误：broker / approval / 特权运维 socket 关闭连接、重连（broker 须重新 hello）后对全部在途请求按 ACK 丢失重投；worker 与 reconciliation worker 的 socketpair 不重连，SDK 将全部在途请求置为失败，本 attempt 以 sys.error 结束（effect 记录按 §4.2 在下一 attempt 启动时对账）。
```
**副作用**：无。

**配套测试/夹具**：CF-IPC-09 按 socket 角色拆为两例：broker 重连 hello 后重投得到首响应；worker 收到 null-id FramingError → attempt sys.error，下一 attempt 对账在途效应。

### C12-05 [NIT] 表格与用例编号顺序

**位置**：§2.1 表格；§6.5 CF-AUTH 表

**问题**：§2.1 中 C-10a 排在 C-10 之前；CF-AUTH-11..17 排在 08..10 之前。

**候选改动方案**：
```diff
-| C-10a | release_reconcile_report …
-| C-10 | release_outcome …
+| C-10 | release_outcome …
+| C-10a | release_reconcile_report …
```
CF-AUTH 表按编号重排。**副作用**：无。**配套测试/夹具**：无。

---

## 同步项（HLD v2.2 对核心的修订 ↔ 01 v0.12 现文；不计入第二部分结论）

| # | 严重程度 | HLD v2.2 | 01 v0.12 现文 | 冲突 | 建议落点 |
|---|---------|---------|--------------|------|---------|
| S-01 | MAJOR | E-02（§4.3.4）：paused(wait) 成因 {gate, external}；全集计时条件；paused 期预算可到期；sys.await_external；wake outbox | C-07 只有"仅剩 gate 等待"；C-13 guard 为 queued ∨ running（不含 paused）；§3.4"排除 paused 与 publishing 时段"；V-05/V-06 不认 sys.await_external；task 没有挂起态 | 直接矛盾：01 的 paused 一律不计时、不可到期 | §2.1 增 C-07b（external）与 C-08d（wake 消费），C-13 guard 加 paused；§3.4 改为全集条件；§1.2 增保留结果 sys.await_external、sys.superseded（H22-09） |
| S-02 | MAJOR | E-03（§8.5）：worker 数据面追加六条命令 | §5.1 worker 数据面封闭为 9 条；CommandName 19 | 封闭枚举与新命令冲突 | §5.1 表、CommandName、注册表、A0；数据面幂等域沿用 (task_id, attempt, command) |
| S-03 | MAJOR | 规则① 审批 CAS 核对 release_requires 各报告"通过"谓词；ReleaseManifest 含 release_evidence；§4.3.5 incomplete/retried 与成功关闭约束 | §2.5 decision_submit 新鲜度 CAS 只检查 gate、plan、series；ReleaseManifest 没有 release_evidence；C-16 terminal_success 无附加 guard；ResultEnvelope 没有 incomplete/retried | 冻结的审批 CAS 被扩展，01 没有对应条款 | §2.5 CAS 增加谓词核对与 acknowledged_gaps（H22-02）；ReleaseManifest 增 release_evidence；§2.7 ResultEnvelope 增两份清单 |
| S-04 | MINOR | §4.2.6 规则①②③、汇合必经、gate_expired ≠ approved、`on: sys.timeout` 限定（H22-02） | §1.3 只有 V-00..V-17 | 缺 V 规则 | 增 V-18（release_requires + 汇合必经，与 V-13b/V-15 的普通支配分开定义）、V-19（input）、V-20（优化重验证）、V-21（gate_expired / sys.timeout 路由） |
| S-05 | MINOR | 注册按 (agent_type, mode) 声明 status_set / produces / series_effect / input_requirement / 资源 | §2.3 AgentRegistration 为扁平结构；CF-FIX-00 注册集（compiler{build_passed, build_failed_exhausted}、benchmark{bench_done, bench_failed}）与 v2.2 示例不符；附录 A4 无镜像节点、compiler 无 mode | 注册模型与验收夹具都要改 | AgentRegistration 改为 `modes: dict[str, ModeRegistration]`；CF-FIX-00 按 v2.2 四份示例重抽；A4 换为 H22-17 原文 |
| S-06 | MINOR | D12 扩展字段（llm_cli_version、bench_suites_digest、spec_digest、bench_policy_digest、module_registry_digest、build_input_closure_digest、Profile 策略版本） | §2.6 ExecutionManifest 七字段 | 缺字段 | §2.6 增字段；bench_suites_digest 按 H22-04 改为注册表快照 |
| S-07 | MINOR | BenchReport：gate_eligible、validation_complete、逐指标四值与区间、opt_gain_pct、opt_verdict；regression_pct 新定义（H22-06） | §2.4 BenchReport.regression_pct 注释为"全指标最大回归"；MetricEntry 只有 value/baseline/regression_pct | gateable 字段的语义不一致 | §2.4 重写 BenchReport，并新增 ImageReport、OptimizationReport |
| S-08 | MINOR | MCP：幂等域 (principal, 操作名) 跨 MCP/HTTP 共享；create_run.focus_modules；submit_bench_suite；sys.scheduler | §0.2 request_id 的幂等域为 (bearer principal, endpoint)；CreateRunRequest 没有 focus_modules | 幂等域定义不同 | §0.2、§2.7 |
| S-09 | MINOR | input: none：created → queued，pin 与初始空 series 同一事务 | C-02 只有 created → awaiting_patch；§3.3a 初始 series 只经 C-04 | 缺状态边 | §2.1 增 C-02b；§3.3a 增空 series 分支 |
| S-10 | NIT | E-02/E-03 生效后上游切换 | 头部"上游依据：v1.0 冻结版"；A2 追溯矩阵 | — | HLD 三方 GO 后改头部与 A2 |

---

## 附录：已核对、未发现问题的项

- **E-01 仍然有效**：V-13b 仍用普通支配，v2.2 明文"E-01/V-13b 与阈值 gate 指标来源检查仍使用普通支配定义"。两份示例中 ci_plan 都支配 human_review。
- **示例一（full_pipeline）逐规则走查**：
  - V-00..V-12：fan-out 在 compile_image 的 image_ready；bench_gate 与 review_static 两源构成划分；共同到达性中，ut_fix_loop / opt_loop 两条环边都必然重经 compile_image 的 fan-out，且之前不经过祖先 fan-out。均通过。
  - V-13 / V-13b / V-14 / V-15 / V-17：通过。
  - 规则①（汇合必经）：must(human_review) ⊇ {compile_rpm, compile_image, ut, benchmark}，通过。
  - 规则②：按 H22-10 限定范围后不适用。
  - rpm_precheck required：compile_rpm 支配 compile_image，通过。
  - **规则③：不通过（H22-01）。**
- **示例二（optimize_campaign）**：V-*、规则①②③全部通过。ci_plan 的每条路径都经过 `no_further_gain`（asserts_nonempty）；opt_loop max_rounds 4 ≥ 2×2。
- **E-02 锁序**："两 Run × 一板 × 一槽"推演：取槽从不等待租约，只剩等待项的 Run 必然释放槽，不形成环路。
- **§11.3 反例**：
  - "删除 compile_image 而保留 image_report → 拒绝"：按 mode 的 produces 可以成立；
  - "保留 optimizer 删 UT → 拒绝"：规则③可以成立；
  - "gate_expired 与 approved 同目标 → 拒绝"：可以成立。
- **01 X1（gate CAS 唯一化）**：paused/running × 人工决定/TTL 四种组合、决定与 TTL 竞争、outbox 重复投递均闭合；CF-SM-02/10、CF-IPC-04 与正文一致。
- **01 X2/X11（epoch）**：按实例分配、计数器持久化、同实例重连同 epoch、低 epoch 实例被拒、上界 < 2^53、§0.2 两行，与 CF-AUTH-11/11b/15 一致。
- **01 X4（publishing 下的 D12）**：E-CP-D12-MISMATCH 只在 Run ≠ publishing 时出现（CommandError 注释与 §2.2a③ 一致）；pending(admin_finalize) 恰一次；not_happened 同事务映射；与 CF-AUTH-04b/04c/05b 一致。
- **01 X5/X6**：§5.1 旧的"授权记录 dispatch receipt 子记录"表述已删除；completed 只表示送达；持有者更替重派区分未核销与已核销两支（剩余缺口见 C12-01、C12-02）。
- **01 X7/X10**：C-10 / C-10a 的 recovery_state guard 与 CF-AUTH-16 一致；原子许可的措辞在 §2.2a 与 ReconcileProceed 注释中一致。
- **01 X8**：§2.2a 处理序与 §5.1 全命令统一处理序一致（剩余缺口见 C12-04）。
- **01 X9（A0）**：用脚本对正文全部 `class`、Annotated 别名与 `- **名**：` 形式的 Report 类型体做双向差集，两个方向均为空。JsonValue / WireJson / SysOutcome 以行内代码定义、两个异常类型、内部 schema CompiledPipeline 均已按 A0 说明收录。
- **CommandName = 19**：与注册表 19 项、§5.1 各 socket 角色的命令划分一致。
