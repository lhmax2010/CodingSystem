# 评审意见：HLD v2.3（第三轮）+ 01_Contract_Spec v0.13（第十三轮）

**评审方**：Kimi　**日期**：2026-11-03
**对象**：docs/00_Framework_HLD_v2.3.md；docs/01_Contract_Spec_v0.13.md
**背景材料**：两份处置表、上一轮三家原始意见、docs/research/quickbuild_business_logic.md（只读实测）、冻结基线 v1.0+E-01。

## 结论表

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| HLD v2.3 | **GO** | 0 | 0 | 1（K-01） | 1（K-02） |
| 01 v0.13 | **GO** | 0 | 0 | 0 | 0 |

## 负责人七项裁决判断表

| # | 裁决 | 判断 | 理由 |
|---|------|------|------|
| ① | UT 与静态审查并行；超时出报告、不得当通过 | **成立** | v2.3 补齐了使其成立的机制：规则③改用与规则①共用的"汇合必经"（G' 子图上计算，示例一并行原文可走查通过），§4.3.5 给超时以结构保证（未被覆盖的超时必然 fail_safe）+ 审批/核销两次复核。 |
| ② | Quickbuild"最新"在 Run 启动时解析固定 | **成立** | 实测证明只能部分成立（包 commit 与 Profile 快照可锁；构建根 base、build.conf、脚本分支锁不住），v2.3 的落地比裁决原文更忠实于证据：能锁的提交时锁定、锁不住的逐项读回比对、读不回或不等即 comparison=unverifiable 不作判定输入。这是"裁决意图（A/B 只差 patch）+ 实测边界"的正确合成，非打折扣。 |
| ③ | Profile 严格匹配 + 小改动复用放宽预案 | **成立** | v2.3 补上了两个成立条件：伪探针选项列入构建输入闭包（缺则不得启用）；开启条件改为非劣证明（固定 ε、区间下界 > −ε 才开启，否则 inconclusive 保持 v1）。"差异不显著"当"等价"的误用已消除。 |
| ④ | 目标范围与模块登记表 | **成立** | 确定时点的缺陷（创建时无 patch）已修为"首次 submit_patch 受理事务内确定 + 之后只增不减"；显式 suites 不得少于最低集合堵住了绕过；未登记模块拒绝、D12 快照 pin、范围增长不失配均已写明。 |
| ⑤ | 以测试结果检验 AI（多版本对比报告） | **成立** | 前提"AI 不能改验证资产"已机制化（protected_paths + 确定性 diff 规则 + verification_asset_change 逐条确认）；采纳率与准确率分开统计（准确率只在有事实标签的样本上）修正了误用；报告在 ci_plan 完成事务内生成且 digest 入授权绑定。 |
| ⑥ | Quickbuild Base CL 探测 | **成立** | 探测已完成且结论（含"锁不住"的负面结论）如实落地，E0 ③改写与实际调查一致。 |
| ⑦ | 超时后重试成功可发布，但每条 retried 须审批人逐条确认，不认可即拒绝 | **成立** | 两家对立语义中，"出现过超时即禁止发布"会把暂态环境噪声变成永久不可发布，代价过大；"重试成功即真实通过"单独又会让超时被悄悄掩盖。本裁决取真实通过 + 强制知情：放行点要求无 timeout 类条目、retried 逐条入 acknowledged_gaps、核销事务再复核一次（审批与核销之间新增条目即授权失效），非发布路径以 succeeded_with_gaps 显式标注。代价是审批人多读一份逐条清单，量级可控。 |

---

## 第一部分：HLD v2.3（GO）

### A. 上一轮处置核验

23 个独立问题 + 负责人裁定逐条对到正文：M1（规则③汇合必经 + G' 子图 + 运行时义务检查 + 环容量公式）落 §4.2.6 ✓；M2（净变更数据流）落规则② ✓；M3 + 负责人裁定落 §4.3.5 放行点 ✓；M4/M5 落 §4.3.4（会话等待 phase、cancel_pending 恰一次归还）✓；M6 按实测重写 §7.6.1 ✓；M7 非劣判定落 §7A.3 ✓；M8 OptimizationPlan 生命周期落 §7A.4 ✓；M9/M10/M11/M12/M13 分别落 §7A.7/§7.8/§7A.0 原则 6/D22/§7.1 ✓；N1（E-02 偏离清单）✓；N10（R25 移至 R24 后）✓。未按评审方方案的取舍（如 M9 未采用"拒绝范围外候选"）理由成立：范围增长同样保证"改了的必须验证"且保留自动化。同步项 S-03 已确认补登于附录 B 第 7 组。

### B. 改动面逐项核验

1. **规则③与四份示例**：示例一（含 join）在 G' 上按汇合必经走查：镜像/UT/Benchmark 均位于 bench_gate 的必经集合（汇合必经 = {j} ∪ ⋃ 必经（来源）），在必经序上依次出现，rpm_precheck=required 时 compile_rpm 在前——加载通过；示例二（无 join）退化为普通支配，通过；示例三、四（无优化节点、无 release）规则③与 release_requires 空虚，通过。静态规则与运行时义务（审批 CAS 核对存在 + 当前 series + 通过谓词；未决计划拒批）互补且一致。我上一轮 N-01（规则②适用范围）与 N-01b（gate_expired 规则入清单）均已修复。
2. **规则②净变更数据流**：advances 重置证明（撤销段使证明失效）、asserts_nonempty 置位、汇合取共同结论；运行时双重强制（返回类校验 + 分派前 tree_digest 比对）。撤销→修复→优化交替场景：撤销回 base 后证明失效，后续 needs-patch 节点不会被分派（fail_safe + incomplete 写明）——正确失效；新一轮候选推进后证明恢复——正确恢复。闭合。
3. **超时放行点**：见裁决⑦。结构上无"超时被当作通过"的路径；审批与核销两次复核 + publishing 后只登记 + 首屏标明，与冻结映射无冲突。
4. **Quickbuild 与实测记录的忠实性**：逐项比对 docs/research/quickbuild_business_logic.md——可锁输入（Build Package List=`BUILD_PKG_LIST_MODIFY`、Profile `SNAPSHOT_NUM`、Add/Remove）与 Q1/Q2 的"已证实"一致；不可锁输入（reference 滚动 base、build.conf、脚本 master 分支）与 Q2/Q4 的"未知/未证实"一致，未把未证实能力写成已具备；读回三层（子变量/日志、repodata 发布摘要、明确标注"实际消费 build.conf 未归档"）与 Q3 逐字吻合；保留期（记录 30 天、Artifact 10、RBS 7）与 Q5 政策表一致；Recent Builds 10 条与 Q6 一致；并发未知 → 客户端自设配额与 Q8 一致；Q4 的设计推断（"无法固定或读回的项保留不保证等价"）正是 comparison=unverifiable 的出处。Cosmos 段落如实标注证据等级（shelve 原号更新风险取自 C:530/771）。忠实。
5. **BenchPolicy 非劣判定**（区间上界、下限 0、样本少自然判不过——修正了低功效放行的方向错误）、**OptimizationPlan 生命周期**（四态、修复段归属计划、确定性撤销、按计划数计轮、环容量 ≥1+max_opt_rounds 使撤销可达）、**范围只增不减**、**验证资产保护**、**Profile v2 开启条件**（前提 0 + 非劣）——均闭合。
6. **D22 不可变基底**（两形态共同契约、基底 digest 入 manifest、基线与 series 构建不共用边界实例）、**CLI cgroup v2**（launcher spawn + cgroup.kill 覆盖跨 UID）、**会话等待分阶段**（before_submit / submit_uncertain / polling / reconciliation，提交不确定必先 probe 不重复提交）、**cancel_pending 配额恰一次归还**——均闭合。

### C. 组合场景走查（任务书指定场景）

场景：full_pipeline（backend=quickbuild），同一 Run 内发生：UT∥静态审查并行 + 节点超时后重试成功 + AI 修复使范围增长 + 优化候选被撤销 + Quickbuild 读回不可比。

- compile_rpm 修复环：AI 修复触及范围外已登记模块 → series 推进事务内范围并集增长（不触发 D12 失配，套件 = pin 快照 × 范围的确定性函数）；若触及 protected_paths → verification_asset_change 条目。
- compile_image 提交后外部等待；等待超 external_timeout_min → sys.timeout → 节点 retry 重试 → 成功：记录进 retried（非 timeout 类 incomplete）。
- UT∥review_static → join 两路到达（同 activation 同 series）→ 触发 review_final。
- 优化候选 → pending_validation → Benchmark 第二组 A/B（对父镜像）→ opt_verdict=loss → 确定性撤销（新段 purpose=revert 回 plan.parent_tree，不回拨 current）→ 重验证 → 计划 reverted → optimize 返回 no_further_gain（asserts_nonempty，series 有净变更——开发者 patch 仍在）→ 合法。
- Quickbuild 读回比对：基线与被测的 build.conf 发布摘要不等 → comparison=unverifiable → 比较类判定字段缺失 → **bench_gate 指标缺失 fail-closed → fail → fail_safe**。终态 closed(fail_safe)，FeedbackReport 首节含超时清单与不可比说明。结果：不能发布——这是正确出口（fail-closed），无"静默放行"。
- 变体（读回可比）：bench_gate pass → join → ci_plan → human_review：审批 CAS 核对 release_requires 报告存在 + 当前 series + 通过谓词；无 timeout 类条目（已被重试覆盖）；retried 逐条、verification_asset_change 逐条须入 acknowledged_gaps；审批人确认 → 核销复核（此间新增条目则授权失效）→ 发布。**无无出口、无双出口**。
- 补充检查：超时发生在发布路径之外的非发布流水线时，terminal 成功但 get_result 结论为 succeeded_with_gaps 且清单完整——无掩盖。

### 问题清单（第一部分）

**K-01（MINOR，§7.6.1 读回校验 vs §7A.1 镜像模式 status 集）**
- 问题：读回逐包版本不符 → "该构建判为无效（ImageReport.succeeded=false，原因 base_mismatch），不进入缓存"，但镜像节点的 status 归属未定义：base_mismatch 不是 patch 可修复的缺陷，若归 image_fix_patch_ready 会让 LogAnalyzer 分析不可修问题并空耗环预算；归 image_failed_exhausted 则语义混淆（构建本身成功了，是环境不可信）。
- 依据：§7.6.1"读回校验（规范条款）"只给报告字段与缓存处置，未给节点 status 映射；§7A.1 镜像模式仅定义 image_ready / image_fix_patch_ready / image_failed_exhausted。
- 候选改动：
  ```diff
  - 任一不符 → 该构建判为无效（ImageReport.succeeded = false，原因 `base_mismatch`），不进入缓存。
  + 任一不符 → 该构建判为无效（ImageReport.succeeded = false，原因 `base_mismatch`），不进入缓存；节点返回 `image_failed_exhausted`（reason=base_mismatch，不经 LogAnalyzer 修复回流——环境不可信非 patch 可修），走默认 fail_safe。
  ```
- 副作用：无（归已有 status，不动 DSL）；配套测试：§11.3 Quickbuild 用例补"base_mismatch → image_failed_exhausted → fail_safe 且不进入修复环"断言。

**K-02（NIT，§4.3.4 等待项）**
- 问题：`external_timeout_min` "缺省 = 所在环 wall_clock 上限"——节点不在任何环内时缺省无定义（旗舰示例的 compile_image 在环内，但 DSL 不强制节点属于环）。
- 候选改动：补"节点不属于任何环时缺省 = run_budget"（或独立缺省值）。
- 副作用：无；配套测试：§11.3 外部等待用例补一例无环节点的缺省生效断言。

---

## 第二部分：01_Contract_Spec v0.13（GO）

### 上一轮处置核验

本方第十二轮为零 issue GO，无待核条目；处置表所载 7 个独立问题（Y1–Y7）的落文逐条核验通过：DispatchReceipt superseded 态与替代协议（Y1）✓；SO_PEERCRED+/proc 身份核实与 BrokerInstanceLease（Y2）✓；indeterminate 锁存 + C-11a probe_only 通道（Y3）✓；hello 处理序例外与重放绑定（Y4）✓；按 socket 角色的协议错误处理（Y5）✓；A0 补齐（Y6，含 SnapshotManifest 与本版新增类型）✓；C-10/C-10a 行序与 CF-AUTH 排序（Y7）✓。contract_version 升 dev2 与破坏性修改声明一致。

### 五条时间线 × 崩溃点走查（每格恰一出口）

1. **核销前崩溃**：无 receipt/intent 或未核销 → 重派（同 epoch 同 request_id；换实例走替代协议）→ 正常 consume → granted。✓
2. **核销后发布前崩溃**：completed 仅表送达 → 持有者更替重派（已核销须先静默）→ resumed → 对账 → proceed → 执行 → outcome。✓
3. **发布中崩溃**：对账 happened → ledger 级 released 关闭；not_happened → 原子许可 → proceed/deny。✓
4. **旧实例未静默**：consume → holder_not_quiesced；晚到命令因 epoch 不现行被拒（CF-AUTH-14）。✓
5. **实例存活但单 release task 失联**：实例 retiring → 拒绝执行类命令 → supervisor 清理 → 新实例新 epoch → 恰一次恢复（未核销 granted / 已核销 resumed）；无法清理则告警不重派。✓

崩溃点矩阵：intent 前/后、ACK 前、ACK 后落账前、completed 后崩溃、实例更替（受理前/后/落账前）× 核销前后、迟到 ACK、尚未发送又换实例——CF-IPC-10 逐格有唯一期望；superseded receipt 的迟到 ACK 只写审计、不完成新 receipt、不恢复旧执行权。

### probe_only 通道滥用检查（任务书指定重点）

probe_only 不能用于执行发布：① 仅当授权 recovery_state=indeterminate 时重派扫描才发 mode=probe_only（§2.2d）；② broker 侧 probe_only 只查远端不执行（职责分离，broker 虽在 TCB 内但通道上无"执行"动作可调用）；③ C-11a 上报只有三出口：happened→released 映射（远端已发生的事实确认，非执行）、not_happened→（持有者静默后）release_failed 映射、indeterminate→记录；④ C-11a guard 要求 recovery_state==indeterminate 且连接 epoch 为当前 epoch；⑤ 多目标部分出现只能报 indeterminate。无法经此通道产生一次新的远端写入。闭合。

### 新增项一致性

CommandName=20、注册表、A0、§5.1 broker socket 描述四面一致（抽查 broker_hello / release_reconcile_report / release_probe_report / heartbeat 均在四处同现）；ConsumeRejected 增 recovery_indeterminate 与 ④ guard 一致；CF-AUTH-17b/17c/17d 与锁存语义一致；CF-AUTH-21 与 hello 例外一致；CF-IPC-09 按角色拆分与 Y5 一致。

### 问题清单（第二部分）

无（BLOCKER / MAJOR / MINOR / NIT 均无新发现；前十二轮已关闭条目 diff 复核无重开）。

### 同步项复核

HLD v2.3 附录 B 第 7 组登记范围与 01 现文的差异（E-02/E-03 命令与状态机、§4.3.5 放行谓词与 C-16、报告"通过"谓词、新 DSL 字段、四份示例替换 A4 等）已逐项核对均在册（含本轮补登的 S-03）；无未登记的新同步项，不计入本部分结论。

---

## 交付备注

本文件为唯一提交内容；被审文档未改动。
