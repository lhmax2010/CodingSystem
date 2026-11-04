# 评审意见：HLD v2.6（第六轮顺带核对）+ 01_Contract_Spec v0.16（第十六轮定向复审）

**评审方**：Kimi　**日期**：2026-11-04
**对象**：docs/00_Framework_HLD_v2.6.md（仅附录 A23 所列改动）；docs/01_Contract_Spec_v0.16.md（仅 A3 中 v0.16 一条所列改动）
**材料**：两份上轮处置表、三家上轮原始意见、docs/research/quickbuild_business_logic.md（只读）、冻结基线 v1.0+E-01。

## 结论表

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| HLD v2.6 | **GO** | 0 | 0 | 0 | 1（K-01） |
| 01 v0.16 | **GO** | 0 | 0 | 0 | 0 |

## 负责人七项裁决判断表

| # | 裁决 | 判断 | 理由 |
|---|------|------|------|
| ① | UT∥静态审查并行；超时出报告、不得当通过 | **成立** | 无改动、无回归。 |
| ② | Quickbuild 取最新并固定（最新 Profile 快照） | **成立** | 本版按证据重写代价说明后更如实：推广状态按证据显示（不无条件标"未推广"）、"失败更常见"改标设计推断、补写 Profile 与构建根两条输入链的版本差距（实测 Q4：Profile Oct-28 vs 构建根 Oct-13）并在失败报告附双编号。代价披露完整。 |
| ③ | Profile 严格匹配 + 放宽预案 | **成立** | 无改动、无回归。 |
| ④ | 目标模块范围验证 | **成立** | 无改动、无回归。 |
| ⑤ | 以测试结果与多版本报告检验 AI | **成立** | 上轮指出的 purpose 优先级缺口已由互斥四步判定修复（AI 无法借自报绕过收益验证）。 |
| ⑥ | Quickbuild 显式 base + 读回核对 | **成立** | 能力检查按实际所需（absolute-only 非发布 gate 不要求可比性能力、无法确定时保守按需要 A/B），消除了误拒。 |
| ⑦ | 超时重试成功可发布、审批人确认 | **成立** | 无改动、无回归。 |

---

## 第一部分：HLD v2.6（GO）

### A. 处置落实核验

- R1–R4 逐条落文：§7A.4 互斥四步判定 ✓；§4.2.6 后端能力检查按实际所需 ✓；§7.6.1 代价说明按证据重写 ✓；pending_plan_at_terminal 兜底（规则③ + §7A.4 撤销节）✓。
- **部分采纳评估（未采用"判为环境性失败即自动停止 AI 修复"）**：**成立**。判据目前无可确定形式（连提出方也只写"待 P6 以真实数据确定"）；在判据缺失时引入自动停修规则等于设置一个无定义的判断点，首期"提供双快照编号证据、不设自动规则"是唯一有判据支撑的做法。
- 三家同指一处的定级（purpose 规则取 MAJOR）复核：Codex 的反例（Optimization 亲自撤销被当成新候选再建计划）确实击穿确定性撤销与轮数上界，定 MAJOR 适当；我上轮将其判为 NIT 偏轻，认可合并后的定级。

### B. 改动面逐项核验

1. **purpose 四步互斥判定**：逐路径走查——①撤销优先且只匹配当前未决计划的 parent_tree（碰巧等于历史计划树的段不认作撤销）；②未决计划期间非撤销提交一律拒绝（Compiler/UT 代撤销因①的"不论提交者"而畅通，普通修复被拒——与"待验证期间只允许确定性撤销"一致）；③无未决计划时优化提交走准入（不足时撤销仍成功——撤销不经准入）；④其余 repair、初始段 initial。无误判、无无出口、无双出口。"删去后续修复段归属"后无引用残留，但撤销段描述留有一处残留短语（见 K-01）。
2. **pending_plan_at_terminal**：与 release 路径不冲突（审批本就拒未决计划）；与 campaign 的 no_gain_found 终局不冲突（no_gain_found 只在无未决计划时可返回，否则兜底截获）；补上"base_mismatch 路由到 terminal 时无出口"的最后一格。
3. **后端能力按实际所需**：absolute-only 可确定性解析（SuiteVersion/BenchPolicy 元数据固定）、无法确定时保守按需要 A/B——不误放（保守方向）不误拒（四份示例全部 local 后端 verified，加载通过）。
4. **代价说明按证据**：与实测记录一致（缺省 Ref. Snapshot、Profile/构建根双链、失败率为推断）。

### 问题清单（第一部分）

**K-01（NIT，§7A.4 撤销段）**
- 问题：撤销段描述仍含"包含该候选之后叠加的修复段"——互斥判定②下未决计划期间修复段一律被拒，"候选之后叠加的修复段"已不可能存在，短语无指代（R1 删去归属句时的残留）。
- 依据：§7A.4"series 以新段（purpose = revert）回到 plan.parent_tree，包含该候选之后叠加的修复段" vs 同节判定②"未决计划期间不满足①的提交一律拒绝"。
- 候选改动：
  ```diff
  - series 以新段（purpose = revert）回到 `plan.parent_tree`，包含该候选之后叠加的修复段
  + series 以新段（purpose = revert）回到 `plan.parent_tree`（未决计划期间不存在修复段，判定②）
  ```
- 副作用：无；配套测试：无需改动（§11.3 现有"撤销后 tree_digest 等价于父版本"断言已覆盖语义）。

---

## 第二部分：01_Contract_Spec v0.16（GO）

### 上一轮处置核验

本方第十五轮零 issue GO，无待核条目；处置表 V1–V5 落文核验通过：manual_only + 受强制 probe 约束的人工裁决分支 ✓；定时器代次（phase_generation, owner_epoch, timer_armed）+ 到期 CAS 消费一次 + 同事务解除同实例全部定时器 + waiting_holder 不计时 ✓；interrupt_count/max_task_interrupts（缺省 3）覆盖 lapsed 路径毒丸任务 + launcher 指数退避 ✓；broker cgroup 委派写权限限制 + CF-IPC-03 EACCES 断言 ✓；CF-AUTH-20/CF-IPC-10 预期与"新实例不等回收"统一 ✓。

### 五条时间线 × 崩溃点 × 期限 × 计数上限 × 毒丸走查（每格恰一出口）

1. **正常**：不变。✓
2. **核销后发生前崩溃**：已核销者等 reclaimed 后重派；等待期 waiting_holder 不跑执行期限（不错计失联）。✓
3. **发生后崩溃**：对账 happened → released 映射；proceed 后失联由 awaiting_outcome 期限覆盖。✓
4. **indeterminate**：锁存 + 周期只探测；到达计数上限相关路径不受影响（probe 不计 loss/interrupt）。✓
5. **实例存活但 task 失联**：代次 CAS 一次（重启重放/重复扫描不再计）→ 同事务解除同实例全部定时器（无辜 task 不被旧期限误伤）→ retiring → 回收 → 新 epoch → 重派重新武装；触发者计 loss_count、连带者计 interrupt_count，分工不重复。✓
6. **毒丸任务**（每次执行令 broker 崩溃，走 lapsed 路径）：interrupt_count 逐次 +1 → 达 max_task_interrupts → manual_only；launcher 指数退避 + 连续崩溃停止自动拉起——发布不再被无限重试，同实例无辜 task 有上限保护。✓

**重复计数/连累检查**：同一到期事件 CAS 只消费一次；同实例无辜 task 不计 loss、只计 interrupt；ABA 同名阶段事件被代次拒绝。**manual_only 后无自动执行路径**：C-09 与 execute 派发显式排除 manual_only，C-11a 不越过人工。**人工裁决不与远端事实相反**：裁决前强制只读 probe，全部发生只允许 confirm_released、全部未发生须原 holder 静默后 confirm_not_released、部分/未知沿既有证据规则。闭合。

### 一致性核验

C-11 guard 与 §5.1 特权运维 manual_only 分支一致；§2.2d 字段与 ReleaseTaskState 模型一致且 A0 无需新增（字段非新类型）；出向分述与 CF-IPC-10 预期统一（execute 恢复须静默、probe 发送不须静默、耗尽分支不断言自动恢复）；contract_version 升 dev5 与破坏性声明一致。

### 问题清单（第二部分）

无（BLOCKER / MAJOR / MINOR / NIT 均无新发现）。

### 同步项复核

HLD v2.6 新增项（E-CANDIDATE-NOT-REVERT、pending_plan_at_terminal、purpose 四值与推导序、后端能力检查语义）已逐条核对均在 HLD 附录 B 第 7 组登记（B-7 报告与消息条已含），不重复报告、不计入本部分结论。

---

## 交付备注

本文件为唯一提交内容；被审文档未改动。
