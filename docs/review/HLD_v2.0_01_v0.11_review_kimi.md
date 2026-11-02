# 评审意见：HLD v2.0（首轮）+ 01_Contract_Spec v0.11（第十一轮复审）

**评审方**：Kimi　**日期**：2026-11-02
**对象**：docs/00_Framework_HLD_v2.0.md（对比基线 docs/00_Framework_HLD_v1.0_draft_frozen.md）；docs/01_Contract_Spec_v0.11.md（对照 docs/review/01_v0.10_review_disposition.md）

---

## 第一部分：HLD v2.0（首轮）

### 结论：**GO**（0 BLOCKER / 0 MAJOR / 4 MINOR / 2 NIT）

#### 冻结核心核验（逐项，无放宽）

- diff 全量比对：D1–D13 原文保留；§4.2.4/§4.2.5/§4.3/§5/§8.2–8.5 逐字与冻结版一致；勘误 E-01（§17 附录 A15）原文在位且效力不受新增条款影响（V-13b 与新增 release_requires 互不冲突，见下）。
- D11 补充（长等待不占执行槽）为纯增量：§4.3.1 新增外部等待条目与 §4.5 计时口径拆分（gate 等待与 publishing 排除、远程构建/板子排队计入、Gateway 会话失效等待运维登录不计入）彼此一致；与"worker 中断恢复由 side_effect 幂等承载"的既有模型兼容——远程构建/镜像构建/刷板在 §5.2 均登记为可 probe 效应并带 run/task 归因标识，外部等待 = interrupt/resume 重执行 + probe 命中既有记录，链路闭合。
- §8.5 新增 Build Gateway 通道（业务 worker 不直连、编排进程以连接上下文校验归属后代为提交、Gateway 只受编排 UID）与 D8/D21 凭据集中原则一致，不削弱既有权限模型。

#### 新增面核验（按任务书九点）

1. **构建两阶段与 Build Gateway**：失败/超时/崩溃重入闭合——本地构建与镜像构建可 probe（worktree/镜像存储存在性），远程构建提交即写 run/task 标识（迟到可归因），会话失效走外部等待 + 告警 + 超时 sys.timeout；Gateway 取消职责在列。
2. **Benchmark**：三种套件来源、生成脚本有效性检查 + 人工确认入库、SPEC 与统计判定分离可执行（BenchReport 顶层 regression_pct/spec_out_count 均可 gateable）；一处缓存语义问题见 H-03。
3. **Optimization**：强制回流重编译/重 UT/重测量、环有上限、Profile 新鲜度拒用、发布同走人工审批 + broker，均落实。
4. **即插即用**：四条机制 + 校验器兑现"删 Agent 不影响其余"；release_requires 的静态（生产者存在且支配）+ 运行时（审批 CAS 核对当前 series）双层设计正确，删 Benchmark/UT 必须显式改清单并留痕于 pipeline_digest——绕过面闭合。两处文字级问题见 H-01/H-02/H-04。
5. **两份示例 YAML 走查**：full_pipeline 与 optimize_campaign 逐条过 V-00–V-17 语义（环覆盖、join 共同 fan-out 与划分、共同到达性、环边双约束、release 必经 hitl、approved 直达、E-01 支配 ReleasePlan 生产者、穷尽性）均通过；input:none 的 created→queued 直排与 §4.3.1 一致。
6. **板子池/镜像存储/Profile 库/SourceProvider**：租约独占 + task 绑定 + 心跳回收、刷机三次失败下线、保留策略与配额齐备。
7. **LLM 接入**：ClineSR CLI 只作补全（关工具、空工作目录、JSON 校验、进程组管理、token 估算标注）足以支撑 §7A 用法；"判定靠 SPEC/统计、AI 只分析"在 §7A.0 表与 §7A.3/§7A.4 流程中落实。
8. **MCP 入口**：同一操作契约双传输、bearer + request_id 沿用、Skill 版本协商明确。
9. **附录 B-7 与分期**：B-7 覆盖全部新增 [01] 项（含空发布计划、外部等待计时、Gateway 命令集）；P0–P8 依赖顺序可执行。

#### 问题清单

**H-01（MINOR，§8.2 vs §4.2.6）**——release_requires 的运行时检查在 §8.2 落空
- 问题：§4.2.6 规则①称"运行时检查：Approval 服务提交决定时的新鲜度 CAS（§8.2）一并核对清单内每类报告均存在且针对当前 series"，但 §8.2 的 CAS 枚举只有"gate 仍 waiting、被批 ReleasePlan 仍为该 Run 当前版本、series/tree_digest 仍为最新"三项，不含 release_requires 核对。实现者按 §8.2 写代码会漏掉该检查。
- 候选改动：
  ```diff
  - 事务内 **CAS 校验新鲜度**——gate 仍 waiting、被批 ReleasePlan 仍为该 Run 当前版本、series/tree_digest 仍为最新，任一不满足即拒绝并提示 reviewer 重审
  + 事务内 **CAS 校验新鲜度**——gate 仍 waiting、被批 ReleasePlan 仍为该 Run 当前版本、series/tree_digest 仍为最新、**release_requires 清单内每类报告均存在且针对当前 series**（§4.2.6），任一不满足即拒绝并提示 reviewer 重审
  ```
- 副作用：无（与 §4.2.6 一致化）；配套测试：§11.3 已有"release_requires 新鲜度测试"类别，无需新增，仅需在其判定依据中引用 §8.2。

**H-02（MINOR，§4.2.6 规则②）**——input:none 的静态检查仅约束 entry 节点
- 问题：规则只查"entry 节点不得是需要 patch 才能工作的节点"。反例：`input: none` + entry=compile_image + 无产 patch 环 + 下游直挂声明"需要 patch"的节点（如 review_final）——静态放行，运行时该节点面对空 series 只能降级或报错，与规则意图（input:none 流水线自成体系）不符。
- 候选改动：
  ```diff
  - `input: none` 的流水线以空 series 起步、创建后直接排队，其 entry 节点不得是需要 patch 才能工作的节点（以 Agent 注册的输入声明判定）
  + `input: none` 的流水线以空 series 起步、创建后直接排队；声明"需要 patch 才能工作"的节点要么被可产 patch 的节点/环支配，要么显式声明空 series 可降级运行——否则拒绝加载（以 Agent 注册的输入声明判定）
  ```
- 副作用：校验器复用既有支配性分析，无新机制；配套测试：§11.3"`input: none` 流水线生命周期"用例补一条中间节点反例。

**H-03（MINOR，§7.8）**——基线测量结果缓存的消费语义自相矛盾
- 问题：原文"基线测量结果按（基线镜像, 套件版本, 板型）同样缓存，但**每次 A/B 仍按交叉方式重测**以控制板子状态漂移"——条目被缓存却每次重测，缓存的用途、消费方与失效条件无定义（若缓存值从不被消费则不应存在；若被消费则与"每次重测"矛盾）。
- 候选改动（二选一写明）：
  ```diff
  - 基线测量结果按（基线镜像, 套件版本, 板型）同样缓存，但每次 A/B 仍按交叉方式重测以控制板子状态漂移（§7A.3）
  + 基线测量每次 A/B 都按交叉方式重测、不复用历史值（控制板子状态漂移）；历史基线测量按（基线镜像, 套件版本, 板型）归档保留，仅作趋势参照与审计，不参与当次判定
  ```
  （或若意图是允许复用：写明复用条件与失效条件，如板型/套件版本/镜像任一变化即失效。）
- 副作用：无架构变化；配套测试：§11.3"基线缓存命中/失效"用例按所选语义细化期望。

**H-04（MINOR，§4.2.6 规则①）**——release_requires 支配检查硬编码示例节点名
- 问题：原文"每一类报告的生产节点存在且支配 **human_review**"——human_review 是示例流水线的节点名而非保留字；采用其他 gate 名的合法流水线使该规则无法解释。
- 候选改动：
  ```diff
  - 每一类报告的生产节点存在且支配 human_review
  + 每一类报告的生产节点存在且支配 release-approval 型 hitl 节点（§4.4 分型）
  ```
- 副作用：无；配套测试：§11.3 即插即用组合测试补一个非"human_review"命名的正例。

**H-05（NIT，§4.2.4 vs §4.5）**——计时口径括注漂移：§4.2.4 称 join timeout"排除 paused 与 publishing 等待时段"，§4.5 已把 paused 按成因拆分（外部等待计入预算）。候选改动：§4.2.4 括注改为"排除 gate 等待与 publishing 时段；外部等待时段计入（口径同 §4.5）"。无测试影响。

**H-06（NIT，§1.2/§14）**——编号乱序：Goals 列表 G9 后出现 G11 再 G10；§14 风险表 R22 排在 R21 前。候选改动：各自按序重排或重编号。无测试影响。

#### 与 01 v0.11 的关系（同步项，见第二部分 S-01/S-02）

---

## 第二部分：01_Contract_Spec v0.11（第十一轮复审）

### 结论：**NO-GO**（0 BLOCKER / 1 MAJOR / 1 NIT / 2 同步项）

（注：上一轮本方窗口结论为 NO-GO——发现下述 C-01；任务书所录"上一轮 Kimi GO"与仓库/记录不符，以本条为准。）

#### 五个重点项复核（均通过）

1. **恢复路径全链**：resumed → release_reconcile_report 三结果（happened→ledger 级 released 映射关闭；not_happened→原子许可 proceed/deny；indeterminate→记录保持 publishing 走 C-11）→ release_outcome 回归两值后四条 broker 时间线（核销前/核销后发布前/发布中崩溃/旧 broker 未静默 stale_epoch）逐格闭合，C-10 目标仍仅 closed，C-10a 与 HLD §4.3"publishing 仅经 broker 完成或 probe 对账后关闭"逐字一致。
2. **DispatchReceipt 两事务出向协议**：四崩溃点（intent 前/后、broker 受理后 ACK 前、ACK 后落账前）恢复语义唯一；同 id 异 digest 在事务①即拒，broker 侧双执行由进程内去重 + 授权状态机 + intent 校验三层消除。
3. **broker_hello**：epoch 分配（每次启动单调、1..2^53、连接绑定）、等值校验（不等/未握手 → E-CP-FORBIDDEN）闭合；CF-AUTH-09/12 期望可判定。
4. **FramingError 边界**：envelope 前置解析失败（未知 command/缺 request_id/非法 envelope）与已知命令载荷非法（ResponseError E-CP-VALIDATION）互斥完备。一处 receipt 界定见 C-02。
5. **新命令/模型三面一致性**：CommandName 19 枚举、注册表注释、§5.1 文字面一致；**A0 面失守——见 C-01**。

#### 问题清单

**C-01（MAJOR，§7 附录 A0 vs §5.1/§4.2/§4.3；遗留自上轮本方报告）**——A0 类型索引滞留四轮
- 问题：A0 自称"本文全部具名类型……contracts 包按此逐一交付"，且 §5.1 声明"contracts 包 CI 以自动检查断言 A0 名 ↔ 正文模型一一解析"。grep 实证 v0.11 的 A0 与 v0.6 相同，缺 v0.7 起各轮新增的约 25 个模型（CommandEnvelope/CommandName/CommandAck/CommandError/ResponseOk/ResponseError/FramingError、EffectClaimRequest/EffectClaimResponse 三型、EffectTransitionRequest、Blob 三命令载荷、SeriesCandidateSubmit*、TaskCompleteRequest、AuthorizationConsumeRequest、ConsumeGranted/Rejected/Resumed、BrokerHelloRequest/Result、ReleaseReconcileReport/ReleaseReconcileResponse 三型、ProbeReceipt、DispatchReceipt、RecordView、ProbeReport、PendingRegisterRequest、PostCloseCorrectionRequest 等）。后果：CI 断言自启用起必然红灯；按 A0 逐一交付 contracts 包将漏掉整个命令面与恢复链模型。
- 依据：§7 A0 原文（与 v0.6 逐字相同）vs §5.1 命令载荷模型块与 §4.2/§4.3 新增模型。
- 候选改动：
  ```diff
  - **A0 类型索引**：……（现行滞留清单）
  + **A0 类型索引**：（按 CI 断言输出重新生成的全量清单，逐节列出 §0–§5 全部具名模型）
  ```
  并在 §5.1 的 CI 约定句中明确检查为**双向**（A0→正文可解析 ∧ 正文模型→A0 有条目），否则滞留类错误无自证：
  ```diff
  - contracts 包 CI 以自动检查断言 A0 名 ↔ 正文模型一一解析
  + contracts 包 CI 以自动检查双向断言：A0 每个名字解析到正文唯一定义，且正文每个具名模型在 A0 有条目
  ```
- 副作用：纯索引修复，无语义变化；配套测试：CI 检查本身即测试，无需新增用例。

**C-02（NIT，§5.1 通用段 / FramingError；遗留自上轮）**——framing 失败是否入 receipt 未界定："受理即持久化 receipt"的"受理"是否涵盖 envelope 前置解析失败未写明（缺 request_id 者无法入 receipt；带 request_id 的未知 command 未界定）。候选改动：
```diff
+ FramingError 不产生 receipt（未受理即无幂等义务；重放确定性得同错）。
```
副作用：无；配套测试：CF-IPC-09 期望补一句"无 receipt 落账"断言。

#### 同步项（v2.0 核心修订 × 01 现有条文；不算 01 缺陷）

**S-01（MAJOR，01 §3.4/§2.1 C-07 ↔ HLD v2.0 §4.3.1/§4.5）**——计时口径分歧：01 §3.4"run_budget……排除 paused 与 publishing 时段"与 C-07"仅剩 gate 等待"均不区分 paused 成因；v2.0 把外部等待（远程构建/板子排队）的 paused 计入预算、仅 gate 等待与 publishing 排除。01 同步 v2.0 范围时须将 paused 按成因拆分（gate 等待 / 外部等待），否则 run_budget 语义两文档相悖。
- 候选改动方向（01 侧，待 v2.0 范围同步时执行）：C-07 guard 改"仅剩 gate 等待或外部等待、无可运行工作"；§3.4 增加"外部等待 paused 计入 run_budget 与环时长；gate 等待与 publishing 排除"并拆分 Ledger 暂停区间的成因记录。
- 副作用：触发 CF-SM/CF-LED 相关用例期望更新（计时断言按成因区分）；HLD 附录 B-7 已列"外部等待的状态与计时细则"为 01 同步项，覆盖一致。

**S-02（MINOR，01 §6 注册表 ↔ HLD v2.0 §11.3 追加类别）**——01 §6 尚未含 v2.0 追加测试类别（即插即用组合、release_requires 新鲜度、input:none 生命周期、远程构建等待/迟到归因、板子池、基线缓存、生成型套件、Profile 陈旧、优化环回流）的用例族；属附录 B-7 已登记的同步范围，不单独计缺陷，但同步时应逐类落 CF 族。

---

## 汇总

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT | 其他 |
|------|------|---------|-------|-------|-----|------|
| HLD v2.0 | **GO** | 0 | 0 | 4（H-01～H-04） | 2（H-05/H-06） | — |
| 01 v0.11 | **NO-GO** | 0 | 1（C-01） | 0 | 1（C-02） | 同步项 2（S-01 MAJOR / S-02 MINOR） |
