# 评审意见：HLD v2.2（第二轮）+ 01_Contract_Spec v0.12（第十二轮复审）

**评审方**：Kimi　**日期**：2026-11-02
**对象**：docs/00_Framework_HLD_v2.2.md（基线 docs/00_Framework_HLD_v1.0_draft_frozen.md）；docs/01_Contract_Spec_v0.12.md
**方法**：v2.0→v2.2 与 v0.11→v0.12 全量 diff + 处置表逐条核验 + 四份示例流水线与新规则走查 + 四条 broker 时间线 × 崩溃点复演。

---

## 第一部分：HLD v2.2

### 结论：**GO**（0 BLOCKER / 0 MAJOR / 2 MINOR / 1 NIT）

#### 上一轮处置核验

- 本方首轮 6 条（H-01～H-06）全部落实：§8.2 CAS 已含 release_requires（H-01）；§4.2.6 规则①改面向 release-approval 型 hitl（H-04）；基线测量改为"只归档不参与判定"（H-3，取我建议的第一种写法）；§4.2.4 计时括注按 §4.3.4 全集条件改写（H-05）；G 编号已排序（H-06 部分——R 编号残留见 N-02）。input:none 仅查 entry 的问题（H-02）被 Codex H-11/CC H2-14 的更强方案（series_effect 路径级规则）覆盖。
- 未按评审方方案的取舍抽查：K2 计时取 Codex 全集条件（成立——混合等待区间有唯一答案）；K3 不引入 AND-join 支配（后被负责人裁决①以"仅本规则适用的汇合必经"替代，见下）；K7 模式效力取 CC（gate_eligible = full ∧ validation_complete，合理）；K10 不采用 CFG checksum 匹配率（合理，v2 预案已预登记）；K12 Quickbuild 部分采纳（后被裁决②改写）。上述取舍的论证均成立。

#### 十二个重点项核验（逐项）

1. **E-02（§4.3.4）**：与冻结 worker/task 模型兼容——任何 worker 不跨越等待存活、资源分派前授予、sys.await_external 保留结果不路由不计 retry（V-05/V-06 排除已登记 B-7）、wake outbox 续接同一 dispatch（效应键稳定、不重复提交）；锁序先租约后槽，取槽从不等租约，无死锁环；计时全集条件对混合等待有唯一答案；paused 期预算到期带取消传导；Gateway 会话失效切 non_billable + probe deferred 不耗重试。闭合。
2. **D22 特权构建隔离**：边界内无凭据/无 Ledger/无 socket、产物只读导出复验、E0 无 KVM 时改独立构建主机且禁止宿主 root 直跑降级——成立。
3. **§4.2.6 三规则**：①汇合必经的成立依据（全到达才触发/超时仅 fail_safe/环退役整体重置/运行时 CAS 兜底）逐条有文本支撑，且明确不触碰 E-01/V-13b 与阈值来源的普通支配；②③见下述 N-01 与走查——四份示例（全文两份 + 两份子集）按规则通过，文中反例被拒。
4. **§4.3.5**：超时绝不放行、incomplete/retried 清单、存在超时项不得 succeeded——与 terminal/fail_safe 语义一致。一处规则清单缺位见 N-01b。
5. **修复回流（D15 + rpm_fix_loop）**：成功报告只由未提交 candidate 的 task 产出，与 01 的 task_complete 双分支咬合；自环边（compile_rpm→compile_rpm）按环定义合法。rpm_precheck required/independent 与支配检查接合正确。
6. **效应身份**：远程构建效应标记（idem_key 指纹 + version）+ intent 先持久化 + 不确定窗口 indeterminate 不误判；镜像 probe 按 idem_key 查索引复验；镜像存储纳入 Blob 协议。闭合。
7. **Benchmark**：BenchPolicy 缺省参数可直接实现；gate_eligible 只认 full ∧ validation_complete；判定字段框架统计库确定性计算 + conformance 复算；原则 6 多版本对比报告由统计库生成、ReviewReport 不改写。闭合。
8. **Optimization**：opt_verdict 四值、非收益必须撤销且禁回拨 current、max_opt_rounds 自限 + 环预算 ≥2× 防御兜底、UT 失败于优化段确定性撤销、Profile 策略 v1 完全匹配 / v2 预登记缺省关闭。闭合。
9. **板子池/基线缓存/Quickbuild 锁定**：generation fencing、reclaiming→复位→available、归因计数、序列租约、构建输入闭包键、single-flight、仅 sys.baseline_build 可写。闭合。
10. **§7A.7**：范围不可缩小 + focus_modules + always_run 兜底 + 推导失败拒绝提交，fail-closed。
11. **Gateway/ClineSR/MCP**：会话注入通道含账号校验；CLI OS 层兜底不依赖 CLI 行为；MCP 每 principal 令牌 + (principal, 操作名) 跨传输幂等域 + Origin 校验。闭合。
12. **附录 B-7 / §13**：B-7 按主题重写覆盖全部新增 [01] 项（含 E-02/E-03）；P5 核心定稿 + provisional、P7 v1.1 修复了 D10 时序问题。

#### 问题清单

**N-01（MINOR，§4.2.6 规则②）**——静态检查适用范围未限定
- 问题：规则②行文为"input: patch……；input: none……。**静态检查**：任一声明 input_requirement: patch 的节点，从 entry 到它的每条路径都必须经过 advances/asserts_nonempty 边"，未限定该检查仅适用 `input: none`。按字面适用于 input:patch 流水线时，旗舰示例即被误拒：entry compile_rpm 声明 needs-patch，而 entry 到自身的路径为空、不含任何 advances 边。
- 依据：§4.2.6 规则②原文 vs §4.2.1 示例一（input: patch 缺省 + entry compile_rpm）。
- 候选改动：
  ```diff
  - **静态检查**：任一声明 `input_requirement: patch` 的节点，从 entry 到它的**每条路径**……
  + **静态检查（仅 `input: none` 流水线；`input: patch` 的初始 series 恒非空，无需检查）**：任一声明 `input_requirement: patch` 的非 entry 节点……（input: none 下 entry 节点声明 needs-patch 即拒绝——其必面对空 series）
  ```
- 副作用：无语义变化；配套测试：§11.3 input 用例组补"input: patch + needs-patch entry 通过"正例。

**N-01b（MINOR，§4.2.6 vs §4.3.5/§11.3）**——"gate_expired 不得与 approved 同目标"未入合法子集规则清单
- 问题：§4.3.5 规定该路由拒绝加载、§11.3 有对应用例，但 §4.2.6 的"静态校验器全部规则"清单未含此条——该清单自称完备（"通过全部规则 = 合法子集"），遗漏使校验器实现可漏检"超时即发布"形态。
- 候选改动：
  ```diff
  - 通过全部规则 = 合法子集；示例 `pipelines/` 下四份流水线随仓交付（§2.4）。
  + 另：hitl 节点的 `gate_expired` 路由目标不得与 `approved` 相同（§4.3.5）。通过全部规则 = 合法子集；示例 `pipelines/` 下四份流水线随仓交付（§2.4）。
  ```
- 副作用：无；配套测试：§11.3 已有对应用例，仅需在 §4.2.6 与用例间补引用。

**N-02（NIT，§14）**——风险编号乱序：R25 插在 R22 与 R23 之间（实际顺序 R20, R21, R22, R25, R23, R24）。候选改动：按 R23→R24→R25 重排行序（编号不动以免引用失效）。无测试影响。

---

## 负责人裁决的独立评估（六项逐项）

| # | 裁决 | 判断 | 理由 |
|---|------|------|------|
| ① | 恢复 UT∥静态审查并行 + 超时显式化 | **成立** | 汇合必经定义限定域使用（仅 release_requires，不动 E-01/V-13b 的普通支配），成立四依据（全到达触发/超时仅 fail_safe/环退役重置/审批 CAS 兜底）逐条有冻结文本或本版定案支撑；§4.3.5"超时绝不当通过"消除了并行形态下"超时=缺一路照过"的唯一实质风险。落地缺口见 N-01b（规则未入清单），不改变裁决本身的成立。 |
| ② | Quickbuild 基线锁定（pin 时解析"最新"） | **成立** | 与 D5"基线一致性"同一原则的合理延伸；同 Run 全部提交同 base 使 A/B 只差 patch；unpinned_inputs 兜底（同批构建 + 不跨 Run 复用 + 首屏呈现 + 不阻断发布）与"发布对象是 patch、镜像是证据"的论证自洽；E0 ③探测项保证不可行时早暴露。 |
| ③ | Profile 复用放宽预案（策略 v2） | **成立** | 缺省关闭 + P7 真实数据验证后开启 + 全确定性判定 + 无收益即撤销兜底——"最坏浪费一轮验证"的代价声明属实；这恰是对 v2.0 评审中"CFG checksum 无数据支撑"批评（未采纳项）的合规回应：先定义、后验证、再开启。 |
| ④ | 目标范围与模块登记表（§7A.7） | **成立** | "改动涉及模块不可缩小 ∪ 开发者关注模块"防止范围被静默缩小；input:none 必填目标模块；范围推导失败即拒绝 submit_patch（fail-closed）；范围外回归以 always_run 冒烟集兜底并登记 R25。未发现绕过形态。 |
| ⑤ | 以测试结果检验 AI（多版本对比报告取代能力登记试点） | **成立** | 产 patch 类 AI 输出本就被构建/UT/Benchmark/审批的确定性链兜底，"方案可以造假、测试结果不能"的论证成立；分析类输出改按采纳记录统计准确率，比预先分级更少假设。原则 5 的"判定字段框架统计库计算 + conformance 复算"提供了结构性保证。 |
| ⑥ | Quickbuild 显式指定 base 的 E0 预检 | **成立** | 纯探测项调整，与裁决②配套，无风险面。 |

六项无"不成立"。落地文本缺口均已按问题条目报告（N-01b 对应①）。

---

## 第二部分：01_Contract_Spec v0.12

### 结论：**GO**（0 BLOCKER / 0 MAJOR / 0 MINOR / 0 NIT）

#### 上一轮处置核验（本方条目）

- C-01（A0 滞留，MAJOR）：A0 已按节逐名全量重建（无"族"概括、含异常类型与类型别名），CI 改双向断言——抽查 v0.7–v0.11 各轮新增模型（Consume* 三型、ProbeReceipt、DispatchReceipt、BrokerHello*、ReleaseReconcile* 三型、FramingError、CommandName 等）全部在列，被删除的 ReconcileDeny/ConsumeD12Mismatch 不在列，一致。关闭。
- C-02（FramingError 落 receipt 界定，NIT）：全命令统一处理序定案——envelope/schema/连接级三步失败均不落 receipt、不占幂等域，null request_id 的客户端处置（断连重投在途）写明。关闭。
- 处置表"记录更正"一节关于本方上轮结论的记载与事实一致性：本方对 v0.11 的窗口结论确为 NO-GO（1 MAJOR），处置表头部的裁决输入记录（Kimi NO-GO 1 MAJOR + 1 NIT）与此相符；该节所称"存档为 GO"指的是第**十**轮（v0.10，零 issue GO）——两个轮次各自的记录均无误，无遗留争议。

#### 重点项走查（四条时间线 × 崩溃点）

1. **gate CAS 唯一化（X1）**：CAS 只在决定事务/C-08c 发生一次；C-08a/b 消费端改 inbox CAS + 一致性核对、不再改 gate；决定与 TTL 仅一方胜出。CF-SM-02/10 改真实串联。闭合。
2. **epoch 实例化（X2）**：epoch 按 (pid, pgid, start_time) 实例分配、计数器持久化、单一当前实例、同实例断连重连保持 epoch——ACK 丢失重投在 v0.11 下三种形态全部无出口的问题被根除（CF-AUTH-11：同 id 重投仍 granted）；新实例复用旧 request_id 落新域进恢复臂（CF-AUTH-11b）；每 epoch 至多一次执行许可（CF-AUTH-13）。
3. **静默合取 + 执行权 guard + 更替重派（X3/X6）**：静默 = lease 回收 ∧ pgid reap（合取，HLD §8.3① 字面）作为 §2.2a④/§2.2c/C-11/重派的唯一定义；granted_epoch 即执行权持有者，C-10/C-10a 校验连接 epoch，旧实例晚到命令被拒（CF-AUTH-14）；completed 仅表送达、崩溃后经持有者更替重派（未核销直派/已核销先静默），恢复臂不再不可达（CF-AUTH-05/05c/05d）。
4. **publishing 下 D12（X4）**：不以错误返回、不阻断对账、pending(admin_finalize) 恰一次登记；not_happened 且许可不通过 → 同事务 ledger 级 release_failed 映射、broker 不发布不发 outcome；ReconcileDeny 删除、release_outcome 恒为执行后——"仅实际执行后发送"与 deny 路径的矛盾消除。与 HLD §8.3 状态级例外一致。
5. **DispatchReceipt 唯一模型 + 处理序（X5/X8）**：§2.5 唯一模型、§5.1 旧表述删除、出向域 (token_id, command)、同 token 至多一个 intent、payload 完整持久化（重派不由 digest 反推）。
6. **recovery_state 四值与终局唯一（X7）**：C-10 仅 none/execution_permitted、C-10a 仅 reconcile_required、indeterminate 后终局只经 C-11（CF-AUTH-16/17），同一观测无两种终局。

四条 broker 时间线（核销前/核销后发布前/发布中崩溃/旧实例未静默）× 各崩溃点复演：每格恰一 wire 出口、无双许可、无滞留。

#### 同步项（HLD v2.2 核心修订 ↔ 01 现文；不算 01 缺陷）

- **S-01（MAJOR 级同步）**：HLD v2.2 E-02（外部等待、paused(wait) 成因、计时全集条件、sys.await_external、wake outbox）与 E-03（数据面六命令）落在 01 §2.1 状态机、§3.4 计时口径、§5.1 命令枚举之外——01 §2.1 C-07"仅剩 gate 等待"与 §3.4"排除 paused"均为 v1.0 语义。须随 B-7 同步扩展一次性落定（HLD B-7 已逐项登记，覆盖无缺口）。
- **S-02（MINOR 级同步）**：HLD v2.2 §6.5 的 MCP 幂等域 (principal, 操作名) 跨传输共享 vs 01 §0.2 Skill 层 (bearer principal, endpoint)；§4.3.5 的 incomplete/retried 清单 vs 01 ResultEnvelope。均在 B-7 登记范围内。

---

## 汇总

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| HLD v2.2 | **GO** | 0 | 0 | 2（N-01、N-01b） | 1（N-02） |
| 01 v0.12 | **GO** | 0 | 0 | 0 | 0 |

负责人裁决六项：①成立 ②成立 ③成立 ④成立 ⑤成立 ⑥成立（①的落地缺口已列 N-01b，不撼动裁决本身）。
