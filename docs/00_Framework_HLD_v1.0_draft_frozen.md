# 00 — Multi-Agent Framework 高层设计（HLD）

**版本**: v1.0-draft-frozen（= v0.11 + 第十一轮三方 freeze 勘误）
**状态**: **DRAFT FREEZE**——第十一轮复审三方一致 GO（Kimi / Claude Code / Codex），十一轮累计 66+ 实质 issue 全部闭环处置。本冻结为 draft freeze：架构与关键路径语义不再变更；contract **v1.0 正式定稿**仍须按 D10/G6 三条件（reference Compiler Agent 真实消费 + 五类 fixture + 兼容矩阵）达成后宣布。冻结后的任何修改须重走三方评审
**读者**: 框架开发（Codex）、cross-reviewer（Kimi / Codex / Claude Code）、后续业务 Agent 开发者
**关联文档**: 01_Contract_Spec、02–06_Agent_Design_Guide、07_Conformance_and_Onboarding、08_Codex_Dev_Guide、09_Phased_Dev_Plan、docs/review/ 下 v0.1–v0.11 全部十一轮处置表（v0.11 处置表为 freeze 勘误依据）

> **文档定位**：本文档按"Codex 可直接开发"标准编写——关键路径上的技术决策均已定案，不提供备选方案。凡标注 `[待补充]` 的内容为环境类事实材料（由项目负责人核对后填充），不阻塞架构评审；凡标注 `[01]` 的内容为已定案、精确 schema 在 01_Contract_Spec 给出的项。

---

## 1. 背景与目标

### 1.1 背景

本框架服务于 Tizen 平台工程的自动化软件工程流水线（CodingSystem 重启版）。完整目标态为六角色协作：外部 Coding Agent（ClineSR / 过渡期 Codex）产出业务 patch，框架内的 Compiler / UT / Benchmark / Review / CI 五类 Agent 完成编译修复、单测验证、性能基准、AI+人工审查、发布。

与旧版 CodingSystem 的关键差异：

1. **Coding Agent 移出框架**——仅通过 Skill 协议调用流水线，框架对其零依赖；
2. **框架平台化**——本团队交付：框架 + 公共模块 + **approval 服务、release broker 及官方发布 adapter（gerrit/github，见 §8.3）** + reference Compiler Agent；业务 Agent（UT / Benchmark / Review / CI）由业务开发者依据 02–06 设计指引二次开发；
3. **流水线可配置**——支持子集编排（如仅 Compiler + Benchmark），不改代码只改配置。

### 1.2 目标（Goals）

- G1 声明式可配置 pipeline 编排：全量或任意**合法**子集（合法性定义见 §4.2.6），配置驱动；
- G2 Agent SDK：业务开发者面向 SDK 编程，不接触编排引擎内部；
- G3 公共模块：LLM 接入层、知识源接入、Context 管理、EvidencePacket 工具链、Ledger/Artifact store、资源管理接口；
- G4 全流程可追溯、可断点恢复；副作用语义为 **at-least-once + 效应侧幂等**（§5.2），不承诺 exactly-once；
- G5 发布安全物理强制：凭据仅存在于框架 release broker 进程，approval token 原子单次核销（§8）；
- G6 contract v1.0 定稿 gate：reference Compiler Agent 真实消费 + 五类 Agent 的 producer/consumer fixture 全部通过 + 兼容矩阵建立（§13 P5）。基于 FakeLLMProvider 达成；内网真实 LLM 的 provider 一致性验证为独立的上线 gate（§14 R5）。

### 1.3 非目标（Non-goals）

- N1 分布式多机部署（MVP 单机；单机自我保护不豁免，见 §7.6.3 资源额度）；
- N2 多租户与配额系统；
- N3 学习型 LLM 路由（沿用 static → rule → cascade，见 §7.1）；
- N4 通用工作流引擎（只覆盖本领域 pipeline 形态：显式声明的有界循环 DAG + gate）；
- N5 多语言 SDK（仅 Python）；
- N6 Coding Agent 本体实现（框架只定义 Skill 协议）；
- N7 完整容器级安全沙箱（信任模型与残余风险见 §8.1、§14 R7；凭据隔离不在此豁免范围，由 broker 进程隔离保证）。

---

## 2. 总体架构

### 2.1 分层视图

```
┌──────────────────────────────────────────────────────────────┐
│  外部世界（框架边界之外）                                       │
│  Coding Agent (ClineSR/Codex) ── Skill 协议(HTTP) ──┐         │
│  人工 Reviewer ── Review CLI → Approval 服务 ────────┤         │
└─────────────────────────────────────────────────────┼─────────┘
                                                      ▼
┌──────────────────────────────────────────────────────────────┐
│  业务 Agent 插件（业务侧二次开发；reference Compiler 本团队交付） │
│  Compiler / UT / Benchmark / Review / CI                      │
│  依赖方向：仅依赖 L3 SDK 与 L2 Contract                        │
├──────────────────────────────────────────────────────────────┤
│  L4 编排层：DSL 解析/校验 → 引擎执行；Run 生命周期/gate/循环预算 │
│     （LangGraph 硬封装于 framework/engine/，经 EnginePort 接入）│
│  L4' 特权服务（独立进程）：Approval 服务 │ Release Broker       │
├──────────────────────────────────────────────────────────────┤
│  L3 Agent SDK：AgentBase / worker 模型 / side_effect / trace   │
├──────────────────────────────────────────────────────────────┤
│  L2 Contract（独立文档 01，独立版本演进）                       │
├──────────────────────────────────────────────────────────────┤
│  L1 公共模块：LLM 接入 │ Knowledge │ Context │ Evidence │       │
│              Ledger+Artifact │ 资源管理接口                    │
├──────────────────────────────────────────────────────────────┤
│  L0 基础设施：SQLite(WAL) │ 文件存储 │ 日志 │ 配置              │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 架构决策一览

| # | 决策 | 结论 | 理由摘要 |
|---|------|------|---------|
| D1 | 编排引擎 | LangGraph，**锁定完整依赖闭包**（langgraph 及 langgraph-checkpoint / prebuilt 等全部 langgraph-* 卫星包，lockfile 固化；开工日生成），经框架自有 EnginePort 接入 | 1.0 稳定承诺属实，但卫星包有过破坏性变更先例（prebuilt 1.0.2 事件），故闭包锁定；EnginePort 保证可撤换 |
| D2 | 路由权归属 | Agent 只声明结果（HandoffResult），路由由编排层按 pipeline 配置决定；框架保留系统级 outcome（§4.3.2） | 子集流水线前提；Agent 间互不感知 |
| D3 | 语言/版本 | Python ≥ 3.12 | 实机环境统一 3.12+ |
| D4 | 仓库与分发 | 单 monorepo；框架以 wheel 发布（`codingsystem-framework`），业务 Agent 经 entry-point namespace `codingsystem.agents` 注册；fork 为特殊模式（同步责任在业务侧） | 业务侧可消费而非仅可见 |
| D5 | 基线管理 | Run 启动时 pin **多仓 snapshot manifest**（§7.6.2）；同时 pin **execution manifest**（D12）；Run 全程锁定 | patch 基线一致性 |
| D6 | 权威事实源 | 单一 SQLite **Ledger**（WAL）为 system of record：Run/Task 状态、artifact 索引、幂等记录、循环计数、token 核销同库事务提交；trace 为 Ledger 派生的 JSONL；LangGraph checkpoint 仅作执行恢复机制 | 消除多存储一致性分裂；审计不依赖引擎格式 |
| D7 | 数据边界 | 数据密级**由来源出生即标注**（snapshot 读取器/BuildExecutor/KnowledgeProvider 产出即带密级），聚合取最高、禁止调用方降级；provider 白名单由中心安全配置授权 | 不依赖调用方诚实；残余风险 §14 R8 |
| D8 | 发布安全 | 发布凭据仅存在于框架 **release broker** 独立进程；CI Agent 只产 ReleasePlan；审批授权以 Ledger 授权记录形态存在（无 bearer 流转），broker 经特权 RPC 原子核销；授权绑定 release manifest digest；官方发布 adapter 随框架交付 | 业务 Agent 拿不到凭据，绕过面收敛到 broker 单点 |
| D9 | 循环上限 | 循环为 DSL 显式声明的 `loop` 对象（环级预算），编排层强制；另有 Run 级总预算 | 计数归属清晰、静态可校验 |
| D10 | Contract 冻结 | draft freeze（三方评审）→ v1.0（G6 三条件） | 未被真实消费的 contract 不定稿 |
| D11 | 并发模型 | MVP：**单执行 Run**（执行槽 = 持有 worker/资源执行中；paused 不占执行槽、可多 Run 并存，resume 与新 Run 同入 FIFO 队列）；Run 内节点级并行；task 以子进程 worker 执行；资源经信号量额度管理（§7.6.3）；Ledger 直写者唯一（编排进程，其余经 control-plane RPC） | 单机资源与 SQLite 约束下最小正确模型 |
| D12 | 执行环境固化 | Run 创建时固化 execution manifest：pipeline digest、contract 版本、框架版本、agent 制品 digest、provider 配置 digest、引擎版本；task dispatch / 审批 / 发布前复核相关 digest；恢复时不匹配走 ledger 级 administrative finalize（§4.3.3），不做在途迁移；provider 配置 digest 含策略语义与 **端点身份/信任策略**（仅凭据值除外——密钥轮换不影响恢复，端点改向则触发不匹配） | 官方明示 interrupted thread 不支持拓扑变更（节点改名/删除）、state 不兼容变更有风险；逐类推理迁移安全性的成本与出错面大于一律拒绝 |
| D13 | 信任模型 | 内网单机单操作员；patch 来源限于经认证的 Skill 调用方；构建脚本视为半可信（见 §8.1） | 沙箱深度与威胁模型匹配（N7） |

### 2.3 与外部系统的关系

| 外部系统 | 关系 | Codex 开发期处理方式 |
|---------|------|---------------------|
| Coding Agent | 框架外，经 Skill 协议（HTTP，§6.5） | 框架实现 server 端 + 模拟客户端 |
| 人工 Reviewer | 经 Review CLI 操作 Approval 服务（§8.2） | 框架交付 CLI 与服务，Codex 可本地全流程测试 |
| CodeGraph / LLM Wiki | KnowledgeProvider 实现 | 开源仓库本地部署真实联调 |
| 内网 LLM | LLM provider 之一 | FakeLLMProvider（fixture 驱动、接口一致） |
| build server (GBS) | BuildExecutor 默认实现 | 本机真实 gbs（gbs.conf 已定可用）`[E0 预检]` |
| Tizen 源码 (gerrit) | snapshot 拉取来源 | 可达性 `[E0 预检]`；不可达则 fixture snapshot 模式 |
| UT 测试板 | BoardPool 接口 | FakeBoardPool；真实实现属 UT Agent 业务侧 |
| gerrit/github 发布 | **release broker 执行**（CI Agent 只产计划） | broker + 官方 gerrit/github adapter + FakePublisher 均框架交付；其他 CI 工具扩展走无凭据子进程受限模式（§8.3） |

---

## 3. 核心概念与术语

| 术语 | 定义 |
|------|------|
| **Run** | 一次 pipeline 执行实例；`run_id` 唯一；reject 后重提为新 Run，`parent_run_id` 成链。新 Run 默认重新 pin 最新 snapshot（可显式指定沿用父 snapshot） |
| **Snapshot** | 多仓 snapshot manifest（§7.6.2）的不可变引用，`snapshot_id` 标识 |
| **Execution manifest** | Run 创建时固化的执行环境描述（D12），`exec_manifest_digest` 标识 |
| **Pipeline** | 声明式 YAML（§4.2）；`pipeline_digest` 为其规范化摘要，进 execution manifest |
| **Agent** | 继承 SDK `AgentBase` 的执行单元；以子进程 worker 运行（§5.1.2） |
| **HandoffResult** | Agent 业务产出：`status`（业务枚举，须在 Agent 注册时全量声明）、artifact_refs、reason、series_id。不含 target 字段 |
| **Outcome** | 编排层路由的实际依据 = 业务 status ∪ 框架系统级 outcome（`sys.error` / `sys.timeout` / `sys.invalid_result` / `sys.crash`，§4.3.2） |
| **Patch series / series_id** | 有序 patch 序列及其版本标识；任何一段变更产生新 series_id 与新 `tree_digest`（snapshot+series 应用后的规范摘要，算法 `[01]`）。所有 Report 绑定产出时的 series_id |
| **Gate** | `hitl`（暂停等待 Approval 服务决定）、`threshold`（纯代码阈值判定；指标缺失一律 fail-closed 转 fail_safe） |
| **Task** | Agent 一次执行；`task_id` 形如 `CMP-000123`；`parent_task_id` 串联因果链 |
| **dispatch_id** | 创建 task 的边送达/分派事件的 Ledger 标识；跨 attempt 与重启稳定，效应键的 slot 锚（§5.2） |
| **activation** | 一次 entry 分派/fan-out/环激活的持久化标识（含环计数向量与 parent_activation_id），join 成组与效应隔离的作用域（§4.2.4） |
| **effect_call_id** | 业务代码内稳定的逻辑效应调用命名（如 "build_main"），由调用方提供、conformance 强制 task 内唯一（§5.2）——业务开发者 contract 面向概念 |
| **Artifact** | 内容寻址不可变对象（写入即定 content digest），Ledger 索引，消息只传 `artifact_ref` |
| **Ledger** | 单一 SQLite 权威事实源（D6） |
| **EvidencePacket** | 提交给 LLM 的结构化证据包（§7.4） |
| **Skill 协议** | 外部 Coding Agent 与框架交互的 HTTP+JSON 协议（§6.5） |
| **Approval 服务** | 框架交付的独立进程：接受 reviewer 决定（approve/reject）、签发授权记录、触发 gate resume（§8.2）；核销唯一归属 broker（§8.3） |
| **Release broker** | 框架交付的独立进程：唯一持有发布凭据；核销 token、按 release manifest 执行发布（§8.3） |
| **approval token / 授权记录** | approve 时在 Ledger 生成的一次性授权记录，绑定 **run_id、gate_instance_id、decision_id、ci_plan_task_id、series_id/tree_digest、release_manifest_digest**（manifest 含 snapshot、发布目标、动作、pipeline_digest、exec_manifest_digest）与过期时间；token_id 高熵随机；不以 bearer 形态进入图状态/checkpoint；仅由 broker 经特权 RPC 原子核销一次；series 推进/Run 关闭/过期即失效 |
| **保留节点** | DSL 内置节点，无需在 nodes 声明即可作为路由目标：`fail_safe`（终局处理：聚合证据产 FeedbackReport 并关闭 Run）。保留命名空间 `sys.*` 与裸名 `fail_safe`，用户节点禁用 |
| **fail_safe** | 仅指上述保留节点；Run 终态统一为 `closed(reason)`（§4.3.1），不再用 fail_safe 指代状态 |
| **Run 终局摘要** | 每个 Run 关闭时由 ledger 层生成的终局 artifact（含终态、pending 事件审计、产物索引；成功路径的异常信息载体——非 FeedbackReport），经 get_result 返回；关闭后的事实修正以 append-only 的 post-close correction 记录附联（§8.3，终态不可变），get_result 一并返回，schema `[01]` |

---

## 4. 编排层设计（L4）

### 4.1 引擎接入：EnginePort

- 框架定义自有执行抽象 `EnginePort`（编译后的图规范 → 执行/暂停/恢复/取消；状态与事件模型为框架自有类型），`framework/engine/` 为其 LangGraph 实现且是仓库内唯一允许 `import langgraph` 的模块（import-linter 强制）。
- 职责矩阵：`orchestration/` 拥有 DSL 解析、静态校验、Run 生命周期、循环预算、outcome 归一化、Ledger 写入；`engine/` 只做图执行与 checkpoint 存取。依赖方向 orchestration → engine（经 EnginePort），禁止反向。
- 引擎替换 = 重写 engine/ 一个模块 + 通过 engine conformance 套件（07 定义）。在途 Run 不迁移：D12 规则下直接拒绝恢复转 fail_safe。
- **hitl gate 实现约束**：官方语义为 interrupt 恢复时节点从头重执行、interrupt 前副作用重跑；因此 gate 前副作用必须走 side_effect 幂等包装（§5.2），这是设计硬前提而非待验证假设。

### 4.2 Pipeline DSL v1

#### 4.2.1 结构与示例（本示例即校验器验收用例，必须可通过校验）

```yaml
pipeline: full_migration
dsl_version: 1            # DSL schema 版本，纳入 Contract 版本体系
nodes:
  compiler:       { agent_type: compiler }
  ut:             { agent_type: ut }
  benchmark:      { agent_type: benchmark }
  bench_gate:     { gate: threshold, metric: benchmark.regression_pct,
                    op: "<=", value: 5.0 }        # 缺指标 = fail-closed
  review_static:  { agent_type: review, mode: static }
  review_final:   { agent_type: review, mode: final }
  ci_plan:        { agent_type: ci }               # 产 ReleasePlan（位于人工审批之前）
  human_review:   { gate: hitl }                   # 审批对象 = ReleasePlan 规范化的 ReleaseManifest
  release:        { broker: release }              # 特权终局节点，outcome 集固定（4.2.5）
entry: compiler
loops:
  - id: ut_fix_loop
    edges: [ { from: ut, to: compiler } ]          # 环由 edges 唯一定义，routes 不重复标注
    budget: { max_rounds: 2, max_wall_clock_min: 180 }   # 环边允许通过 2 次，第 3 次拦截（§4.5）
run_budget: { max_wall_clock_min: 1440 }
joins:
  - id: pre_final_review
    wait_for: [bench_gate, review_static]          # 必须 ≡ 指向本 join 的路由源集合（校验强制）
    timeout_min: 360                                # 可选；缺省以 run_budget 为界
    to: review_final                                # 触发后下游 TaskInput.join_inputs 携带各上游结果引用
routes:
  - { from: compiler,      on: build_passed,            to: [ut, review_static] }
  - { from: compiler,      on: build_failed_exhausted,  to: fail_safe }
  - { from: ut,            on: ut_passed,               to: benchmark }
  - { from: ut,            on: ut_fix_patch_ready,      to: compiler }
  - { from: benchmark,     on: bench_done,              to: bench_gate }
  - { from: bench_gate,    on: pass,                    to: join:pre_final_review }
  - { from: review_static, on: review_report_ready,     to: join:pre_final_review }
  - { from: review_final,  on: review_report_ready,     to: ci_plan }
  - { from: ci_plan,       on: release_plan_ready,      to: human_review }
  - { from: human_review,  on: approved,                to: release }   # approved 必须直达 release（4.2.6）
  - { from: human_review,  on: rejected,                to: fail_safe }
default_route: fail_safe    # 任何未匹配 outcome（含全部 sys.*）的兜底
```

#### 4.2.2 节点与寻址
- 同一 agent_type 的多次使用 = 多个显式节点（各带自有配置），**不存在 `node.qualifier` 点号寻址**；路由 from/to 只引用已声明节点名、保留节点、或 `join:<id>`。
- 保留节点见 §3；`entry` 必填且唯一；终局节点为 `release`、`fail_safe`、或显式 `terminal: true` 节点（子集流水线用）。terminal 节点必须声明 `success_on: [status...]`：outcome ∈ success_on → closed(succeeded)，其余（含 sys.*）→ fail_safe；`compiler_bench_only.yaml` 示例按此交付。release **特权节点**的 outcome 集与终态映射固定（§4.2.5）。

#### 4.2.3 路由穷尽性
- 每个 agent_type 注册时声明业务 status 全集 `[01]`；校验器强制：`on` 值 ∈ (该节点 status 全集 ∪ gate outcome 集（§4.4 封闭枚举） ∪ sys.* )，且每个节点的业务 status 要么逐条有路由、要么被 `default_route` 覆盖（`default_route` 必填）。拼写错 status 在加载期即被拒绝。

#### 4.2.4 并行与汇合
- fan-out：`to: [a, b]` 并行分派。
- **join 触发机制（定案）**：join 的"到达" = 指向该 join 的路由边送达事件；校验器强制 `wait_for` 集合 ≡ 指向该 join 的路由源集合（不一致拒绝加载）。**activation 语义**：每次 entry 分派、fan-out、环激活生成持久化 `activation_id`（含环计数向量；生命周期见下条），到达键 = (run_id, join_id, activation_id, source)；每源每 activation 计一次，同键重复到达丢弃并记审计；全部源到达且 **series_id 一致** → 整组原子消费、恰好触发一次下游（跨 activation 的到达不得混组）。触发后下游 TaskInput 以固定形态 `join_inputs: list[上游结果引用]` 携带全部输入（schema `[01]`）。普通（非 join 目标）节点：每次边送达独立触发一次 task，需要汇合必须显式 join。
- 陈旧性：与当前最新 series 不一致的到达结果标记 stale 丢弃、继续等待同 series 新结果；被取代 series 的在飞任务跑完即弃（MVP 不主动取消）；join 等待受 `timeout_min`（可选）约束、缺省以 run_budget 为界，计时自该 activation 首个到达起算，计时口径同 §4.5（排除 paused 与 publishing 等待时段）。
- **activation 生命周期（退役规则）**：activation_id 由编排层在 **Run 启动的 entry 分派事务（根 activation）**、fan-out、环激活的分派事务内生成并落 Ledger（恢复自 Ledger 重建）；线性边与分支中间节点任务继承派发边的 activation 上下文；activation 记录含 **parent_activation_id**（嵌套 fan-out 的父作用域），join 原子消费后下游以父 activation scope 分派（传播定义含根 activation 与父子关系，`[01]`）。**supersede 三个触发条件**：① series 推进事务同一事务内将旧 series 的全部 open activation 标记 superseded 并作废其计时器；② 某 activation 的已有到达因 series 推进全部转 stale（①的防御性兜底，非独立语义——实现以①为准）；③ **不可补全退役**——声明环边被采用时，在该环边分派事务内，将**采用该环边的 task 所属 activation 上下文**标记 superseded，并沿 parent_activation_id **级联其全部子孙 activation**、连带作废各自计时器（同源单送达规则下，该来源在被退役 activation 内已可证明不可能到达，cohort 及其内层子组必然无法完成整链；退役依据是不可补全性而非"更新者存在"，不恢复 latest-wins）。**替代 cohort**：环边回流路径重经共同 fan-out 时（§4.2.6 条件(iii)对此静态强制）的新分派事务产生新 activation，该 activation **继承被退役 activation 的 parent_activation_id**——环不插入额外嵌套层级，嵌套场景下替代 cohort 照常参与外层 join。**防御性双保险**：join 消费、下游分派与 timeout handler 的 CAS 除校验自身 open 外，一并**校验祖先链无 superseded**；向 superseded scope 的分派被拒并审计。**同 series 的多个 activation 各自保持 open、独立成组消费、独立超时——不存在"更新者淘汰旧者"规则**（环计数向量无全序，latest-wins 不成立）。到达处理与 timeout handler 均以 CAS 校验该 activation 仍 open 且属 current series——superseded activation 的迟到事件与 timer 一律为审计化 no-op；仅 open 且属 current series 的 activation 超时可路由 fail_safe。model-based 测试覆盖同 series 并发多 activation（§11.3）。
- 并行分支任一进入 fail_safe：编排层取消同 Run 其余在飞分支（worker 终止，§5.1.2），Run 走终局处理。
- 通则：任何 Report 携带 series_id。**series 推进为编排进程单事务**：worker 经数据面 RPC 提交 series candidate + `expected_parent_series_id`，编排进程在 task 完成事务内一次完成——父版本 CAS（不匹配即拒绝，防并发丢 patch）+ artifact/结果提交 + series lineage + latest 指针推进 + 待审批项与未核销授权失效；tree_digest 由编排层按规范纯算法计算（无需 worktree，算法 `[01]`）并记录于 Ledger。HandoffResult 中的 series_id 经框架校验、不可自造；candidate 预分配不改变 current series。

#### 4.2.5 特权节点
- `broker: release` 节点由框架内置实现（转发 ReleasePlan 至 release broker），不可被业务 agent_type 顶替。release 的 outcome 集固定为 {released, release_failed}（授权无效/过期/series 陈旧归入 release_failed 附 reason；**D12 版本漂移不属于 release_failed**——在核销前检测并走 administrative finalize，§8.3）。**release 节点无出边、其 outcome 不走 DSL 路由**：终态由 §8.3 固定映射在 ledger 级直接关闭（release_failed 的 FeedbackReport 由 ledger 层生成，同 administrative finalize 例）；校验器拒绝任何 from: release 的路由。校验器强制：所有到 release 的路径必经 hitl；**位于 release 可达路径上的 hitl**，其 approved 出边必须直达 release（与发布无关的其他 hitl gate 不受此约束）——审批与执行之间不得存在任何可改变 release manifest 的节点；凭据只在 broker 进程，业务 CI Agent 永远无凭据。

#### 4.2.6 子集合法性（"合法子集"的定义）
静态校验器全部规则：节点/路由/join 引用有效；entry 存在；每个可达环均被某 `loops` 声明覆盖且带 budget；路由穷尽（4.2.3）；含 release 节点则必经 hitl 且（release 可达路径上的 hitl）approved 出边直达 release、release 无出边（4.2.5）；join 的 wait_for ≡ 指向该 join 的路由源集合，join 的 to 不得指向另一 join（MVP 禁止链式 join）；**join 作用域与共同到达检查**——每个多源 join 的来源必须由同一次显式 fan-out 的不同分支派生（每个来源恰由一个分支到达——来源集在分支间构成划分；共同支配关系不得替代共同 fan-out），全部来源共享该 activation scope；**共同到达性**：从该 fan-out 到每个来源 s 的路径上，任一节点的每个 outcome 分支必须满足三者之一——仍在可达 s 的路径上、到达 Run 终局（fail_safe/terminal/release）、或经声明的环边回流。环边作为本条件例外须同时满足两条静态约束：**其一，回流路径必然重经该 join 的共同 fan-out、从而重派全部来源分区**（机制：环边采用触发 supersede 条件③级联退役旧 cohort，替代 cohort 由重经 fan-out 的新分派产生并继承父 scope——不依赖 timeout 或预算兜底）；**其二，在重经当前 task 所属 activation 的共同 fan-out 之前，不得先重经任何祖先 activation 的共同 fan-out**——跨 activation 边界的回环会使真正被替代的祖先 activation 逃过③的退役根（③锚定在采用环边的 task 所属 activation），其计时器存活即误杀，祖先链 CAS 因该祖先未被标记而不设防；本约束静态保证退役根 = 被替代的作用域。违反任一环约束的回环拒绝加载；outcome 分支三者皆不满足（且不构成合法环边例外）的图亦拒绝加载（互斥 outcome 分支导致来源必然缺席的图在此被拒）；拒绝同一 source 每 activation 多次送达的图（到达键歧义）。**嵌套汇合采用父 activation 关系（定案）**：activation 记录持久化 parent_activation_id，内层 join 原子消费后以**父 activation scope** 分派下游——内层先汇合再参与外层 join 因此合法且可成组；validator property 与 model-based 反例（含互斥 outcome、嵌套汇合重入外层）入 §11.3（4.2.4，传播细则 [01]）；hard-required 上游与 **threshold gate 的指标来源节点**均做**支配性检查**——到消费节点的每条路径都必须先经过生产节点，仅存在不满足，且消费同 series 结果；terminal 节点必有 success_on；threshold gate 引用的指标来源节点在图中存在（不存在即拒绝加载——hard-required 依赖同理：Agent contract 可声明少数 hard-required 上游产物 `[01]`，其余一律 optional 降级，§6.3）；无不可达节点。通过全部规则 = 合法子集；示例 `pipelines/compiler_bench_only.yaml` 随仓交付。

### 4.3 Run 生命周期

#### 4.3.1 状态机（穷尽）

```
created ─▶ awaiting_patch ─▶ queued ──▶ running ──核销事务──▶ publishing
   │            │(TTL 24h)    ▲  ▲        │   │                   │
   │(snapshot   ▼             │  └(槽空闲)┘   │(gate 等待)          │(broker 完成/
   │ 失败)  closed(cancelled) │              ▼                    │ probe 对账)
   ▼                          └──resume── paused(gate)            ▼
 closed(snapshot_error)                     │(reject/TTL)      closed(succeeded)
                                            ▼                  closed(fail_safe)
                                  closed(fail_safe 经保留节点)   closed(cancelled)
```
- resume 路径为 **paused → queued → running**（重新排队取执行槽，非直连）；running → closed(succeeded) 直达边存在于 terminal success_on 路径（非发布子集）；running → publishing 仅经授权核销事务迁入；publishing 出边仅 broker 完成或 probe 对账后按 §8.3 终态映射（ledger 级）关闭。
- 状态穷尽：created / awaiting_patch（snapshot 已 pin、等待 submit_patch，**不占执行队列**）/ queued（patch 受理**或 gate resume 后**待执行槽，FIFO 排队）/ running / paused(gate) / **publishing**（授权已核销、发布 point-of-no-return，§8.3）/ closed(reason)，reason ∈ {succeeded, fail_safe, cancelled, snapshot_error}。全部转换的命令/guard 表 `[01]`；非法转换由 Ledger 状态机守卫拒绝并记审计。
- FeedbackReport 在 reason=fail_safe 时由保留节点生成；**两条 ledger 级生成例外**：administrative finalize 路径（§4.3.3）与 release 固定映射路径（§4.2.5/§8.3）。
- awaiting_patch TTL 默认 24h，超时 closed(cancelled)；run_budget 自 submit_patch 受理（进入 queued）起算。
- 执行槽语义（D11）：paused 不占执行槽；resume 与新 Run 同入 FIFO 执行队列（§6.5）；awaiting_patch 不进队列、不阻塞 ready Run。
- cancel 入口：Skill `cancel_run`（限创建者）与运维 CLI；取消时在飞 worker 终止，进行中的 side_effect 按 §5.2 恢复协议处置。

#### 4.3.2 框架级 outcome 与错误策略
- worker 异常退出/execute 抛未捕获异常 → `sys.crash`；硬超时 → `sys.timeout`；HandoffResult 非法或 status 未注册 → `sys.invalid_result`；setup 失败 → `sys.error`。
- `sys.*` 默认走 `default_route`（即 fail_safe）；节点可配置 `retry: { on: [sys.crash, sys.error, sys.timeout], max: N }`（timeout 重试的重复副作用由幂等层覆盖）由编排层以同 task 新 attempt 重试——**幂等键不含 attempt**，重试以相同 effect_call_id 再调用，命中同一记录（干净终态/在途）或经对账后按 §5.2 记录版本化重新执行。
- 编排层对 wall clock 的强制以 worker 进程 hard-kill 实现（§5.1.2），不依赖 Agent 代码配合。

#### 4.3.3 恢复
- 进程重启后：校验 execution manifest（D12），匹配则经 EnginePort 从 checkpoint 恢复；不匹配 → **administrative finalize**：不经引擎与保留节点，由 ledger 层直接收尾——probe 对账全部 claimed/running 副作用（不可判定项如实记 unknown）→ 生成注明版本漂移的 FeedbackReport → closed(fail_safe)。
- 运行期完整性：task dispatch / 审批 / broker 发布前复核相关制品与配置 digest（D12），不匹配同走 administrative finalize；活跃引擎场景下先停止引擎执行并按 §5.1.2 终止在飞 worker，再执行 ledger 级收尾。
- 恢复即节点重执行（§4.1 前提），正确性由 side_effect 层保证；**恢复重执行复用 Ledger 既有 task/dispatch 记录（dispatch_id 不变），不产生新分派事件**——effect 键跨重启稳定的前提，故障注入含对应断言（§11.3）。

### 4.4 Gate
- gate outcome 全集（封闭枚举，§4.2.3 校验依据）：`hitl` → {approved, rejected, gate_expired}；`threshold` → {pass, fail}。
- **hitl 分两型（校验器按 release 可达性静态判定）**：release-approval 型（位于 release 可达路径）——审批对象为 ReleaseManifest、approve 生成授权记录、approved 直达 release（§8.2/§4.2.5）；plain-decision 型（与发布无关）——approve/reject 仅提交决定 + gate outcome CAS + resume outbox，**不生成 ReleaseManifest 与授权记录**。
- `hitl`：gate 等待为**节点级**——同 Run 其他在飞分支继续执行；Run 级 paused 当且仅当仅剩 gate 等待、无可运行工作（此时释放执行槽，D11）。Approval 服务的决定经 control-plane RPC 单命令原子提交（决定 + 授权记录【仅 release-approval 型；plain-decision 型无此项】+ gate outcome CAS（waiting→resolved，重复决定被守卫拒绝）+ resume outbox，§8.5）。**outbox 消费端去重**：每条以唯一 decision_id/outbox_id 标识，编排层持久化 inbox 去重——重复投递返回同一结果、不得重复创建 task，durable dispatch 完成后才确认 delivered；**resume 不消费授权**，唯一消费点在 broker（§8.3）。gate 可配置 TTL（默认无），超时 outcome=gate_expired；等待期间 series 变化按 §4.2.4 陈旧性规则处理。
- `threshold`：纯代码判定；指标缺失/非法一律 fail-closed（outcome=fail），不允许 fail-open。

### 4.5 循环预算
- 预算属于 `loops` 声明的环对象（环由 `edges` 唯一定义，routes 不重复标注环归属）；环边每通过一次计数 +1，**max_rounds: N = 环边允许通过 N 次，第 N+1 次通过请求即拦截并强制路由 fail_safe**（示例 max_rounds: 2 即最多 2 轮修复回流）；计数持久化于 Ledger 随恢复延续；wall_clock 排除 paused 时段；多环共享节点各环独立计数。`run_budget` 为 Run 级总预算，最先触发者生效；**run_budget 与 join timeout_min 的计时口径同 loop wall_clock——排除 paused 与 publishing 等待时段**（多日人工审批不消耗预算）。

---

## 5. Agent SDK（L3）

### 5.1 生命周期与 worker 模型

#### 5.1.1 AgentBase

```python
class AgentBase(ABC):
    agent_type: ClassVar[str]
    status_set: ClassVar[frozenset[str]]                 # 业务 status 全集（注册强制）
    contract_requires: ClassVar[str]                      # PEP 440 specifier，如 ">=1.0,<2"
    def setup(self, ctx: RunContext) -> None: ...
    @abstractmethod
    def execute(self, task: TaskInput) -> HandoffResult: ...
    def teardown(self) -> None: ...
```
- Agent 经 `ctx` 获得框架注入句柄：artifact store、KnowledgeProvider、LLM client、EvidencePacket builder、trace、以及**能力句柄**（BuildExecutor / BoardPool 等，按 agent_type 在配置中授权注入；清单**显式排除发布通道**——发布只存在于 broker（§8.3）；未授权句柄不存在于 ctx，与 D8 联动）。
- 注册：entry-point namespace `codingsystem.agents`；加载时校验 status_set 非空、contract 兼容、conformance attestation（§11.3）。

#### 5.1.2 Worker 模型（进程边界）
- 每个 task 由编排进程 spawn 独立子进程 worker 执行：注入 ctx → 调 execute → 结果经 IPC 回传。
- worker 以独立进程组（setsid）启动；hard timeout / 取消 = 对**进程组** SIGTERM 宽限后 SIGKILL（killpg，覆盖 gbs 等孙进程），BuildExecutor 额外登记外部长进程供递归清理；进程退出映射 `sys.crash` / `sys.timeout`。
- 编排层持有 worker 租约（heartbeat）；**心跳丢失时 worker（进程组长）先 killpg 终止本组全部进程（含 gbs 孙进程）与 BuildExecutor 登记的外部长进程，再自行退出**——kill 语义不因编排进程失联而缺席；编排进程恢复时先按 Ledger 登记的 pgid 验证归属并 reap 孤儿进程组、再重放。故障注入含"编排进程崩溃且 GBS 子进程仍活跃"用例（§11.3）。
- Agent 实例作用域 = 单 task（无跨 task 内存态，setup/teardown 每 task 执行）。凭据类 secret 不注入业务 worker（D8）。

### 5.2 副作用：at-least-once + 效应侧幂等
- **保证等级声明**：框架保证 at-least-once，不承诺 exactly-once。外部效应成功与完成记录落盘之间存在崩溃窗口，关闭窗口的责任在效应侧幂等。
- SDK 入口为 `side_effect(effect_call_id, params, fn, repeat_seq=None)`——**idem_key 只能由框架计算**（worker 不得自供完整键，conformance 强制）；**effect_class 由 fn 所属注册效应类型推导**：side_effect 仅可包装类型化能力句柄上注册的效应（probe/replay_safe 能力声明挂在该类型上），自由函数不可包装，effect_class 参与 conformance 校验（细则 `[01]`）；其为两阶段持久化状态机（Ledger 同库事务）：`claimed(intent) → running → succeeded/failed`；恢复时遇 `running/claimed` 记录 = 状态不确定（待对账），执行 **恢复协议**：按 §5.2 三支对账（probe / replay_safe 重放 / 皆无 → 持久化 unknown 态并转 sys.error）。
- `idem_key = hash(run_id, dispatch_id, effect_class, effect_call_id, effect_params_digest[, repeat_seq])`——**效应身份 = slot + 稳定逻辑调用标识**：slot = (run_id, **dispatch_id**)，dispatch_id 为创建该 task 的边送达/分派事件的 Ledger 标识——跨 attempt 稳定（重试复用同一 task 即同一 dispatch）、跨 task 天然隔离（含 entry 分派与兄弟送达；node/activation/环轮次由 dispatch 记录蕴含，不入键）。**`effect_call_id` 由调用方提供、在 Agent 代码内稳定**（如 "build_main"、"flash_pre"），不依赖调用次序——控制流变化的重试不会把新逻辑调用错配到旧记录；框架强制同 task 内 effect_call_id 唯一在册（conformance 检查项），显式声明的重复执行由调用方给定 `repeat_seq`（迭代序）。`effect_params_digest` = 调用实参规范化摘要（含 series_id/tree_digest、构建目标、板卡标识等，artifact 引用按 content digest 参与）。**不含 attempt**：同 (call_id, params) 的重试/重放命中同一记录；非决定论重执行实参不同 → 新键，且**跨 attempt 遗留**的同 call_id 旧在途异参记录经 attempt 启动对账**定态**——逐支终态：probe 确认成功 → succeeded（复用）、确认未发生或 replay_safe 退役 → abandoned、不可判定 → unknown + sys.error；**succeeded 与 unknown 不得改写为 abandoned**；**异参新键允许集合（枚举定案）**：定态 succeeded 或 abandoned → 异参新 claim 放行、新键独立执行，且旧 succeeded 仅供同参精确键命中复用、**不得跨参数复用**；定态 unknown → task 已随 sys.error 中止，无新键可立。**本枚举仅辖跨 attempt 定态记录**；干净终态 failed（正常执行产物、非定态产物）之上的同 call_id 异参新 claim 依既有效应类别策略放行，不在此列（效应侧"退役"不与 activation 的 supersede 术语混用）。**唯一性约束的两个层面**：conformance 静态检查（每逻辑调用点唯一命名）；运行时拒绝路径——**仅同一 attempt 内**（跨 attempt 遗留已经启动对账定态）同 call_id 存在未决（claimed/running）记录时的异参新 claim 被拒（作者误用形态），task 报 `sys.invalid_result`（细则 `[01]`）。
- **记录状态与查找矩阵**（全集 claimed / running / succeeded / failed / abandoned / unknown，迁移与查找表 `[01]`）：查找只命中非 abandoned 记录——claimed/running → 按效应能力对账（见下）；**succeeded → 直接复用（含上一 attempt 经 probe 确认成功的记录——可 probe 而不可安全重放的效应必须复用，不做保守重做）**；failed → 按效应类别策略重试或上报。对账按效应能力分三支（conformance 分别覆盖）：**可 probe** → probe 确认成功迁 succeeded（复用）、未发生迁 abandoned；**无 probe 但声明 replay_safe** → 旧在途记录退役 abandoned、重放；**两者皆无** → unknown（持久化）并报 sys.error。attempt 启动前，编排层将上一 attempt 遗留的本 task 非终态记录逐条按上述三支对账。abandoned 记录不参与命中；**记录版本化为通则**——凡同键在 abandoned 记录之上的重执行，一律以版本化新记录承载（迁移/查找表 `[01]`）。
- 状态迁移经 control-plane RPC 由编排进程事务写入：worker 收到 claimed ack 后方可启动效应，RPC 失败 = 效应不得启动（fail-closed）；intent/running 即时提交，task 完成事务仅覆盖最终结果 + artifact 索引 + 幂等终态。
- 效应类别要求（contract + conformance 强制）：构建 = 可 probe（worktree/产物存在性）；刷板/板上执行 = 可 probe 或声明可安全重放；**发布 = 仅经 broker，broker 端远端幂等（push 前查远端状态）+ token 单次核销双保险**。

### 5.3 trace 与 token 记账
- SDK 自动埋点（task 起止、LLM 调用、工具调用、artifact 读写）写 Ledger；`trace.jsonl` 为 Ledger 派生的追加安全格式（每行一事件），供人读与外部工具消费。
- token budget：按节点在 pipeline YAML 配置（`llm_budget:`），超限策略由 Context 管理执行（§7.3）。
- 落盘前统一脱敏：secret/token 只记指纹（§8.4）。

---

## 6. Contract 体系概览（精确 schema 见 01_Contract_Spec）

### 6.1 消息类型
`TaskInput` / `HandoffResult` / 各 Report（Build/UT/Bench/Review/Feedback，均携带 series_id 与产出 task_id）/ `RunContext` / `ReleasePlan` / `ReleaseManifest` / Approval 决定与授权记录 / Run 终局摘要 / Skill 协议消息。agent_type 注册信息含 status 全集与 hard-required 上游声明。

### 6.2 版本规则
Contract 独立版本号；Agent 以 PEP 440 specifier 声明兼容区间（§5.1.1）；框架装配时校验。pipeline `dsl_version` 属 Contract 版本体系。draft 期允许破坏性修改但记 decision_log。

### 6.3 上游缺失语义
默认全部 optional + 降级运行 + 报告显式标注"本次 Run 未执行 X"；Agent contract 可声明**少数 hard-required** 上游产物（如 benchmark hard-require 构建产物引用），由 DSL 校验器静态拦截（§4.2.6）。approval_token 属"外部供给依赖"类别，不参与上游产物校验。conformance 含上游缺失用例。

### 6.4 Patch 归属与陈旧性
产物为 patch series（非 squash），逐段标注产出者与动因；series 任何变更 → 新 series_id + 新 tree_digest → 旧 Report 对 gate/join 失效（§4.2.4）、未核销 token 失效（§8.2）。是否 squash 是 broker 发布期可配置行为。

### 6.5 Skill 协议（决策定案）
- 传输：**HTTP + JSON 单一协议**（MCP 若需要，未来以 adapter 包装同一操作 contract，MVP 不做）。
- 操作：`create_run(pipeline_id, target_spec)`（target_spec 指定 snapshot 拉取范围：仓/包/manifest，语义 `[01]`）、`submit_patch(run_id, series)`（unified diff series + 逐 patch 的 repo 归属；服务端校验对 pinned snapshot 可应用，不可应用即拒绝；一个 Run 仅接受一次初始 series，重复提交返回明确错误——修订走新 Run）、`get_status`、`get_result`、`cancel_run`。忙时语义：submit_patch 受理后 Run 进入 queued（FIFO，响应返回队列位置），resume 同队列；awaiting_patch 不占队列，TTL 见 §4.3.1。
- 认证与信任边界：静态 bearer token（配置下发调用方）；请求含 request_id 支持幂等重试；patch 大小/路径白名单校验。信任边界声明：Skill 端点仅暴露于内网单机/受控网段（D13），持 token 者视为受信 Coding Agent。

---

## 7. 公共模块（L1）

### 7.1 LLM 接入层
- Provider 抽象 `complete(messages, policy_ctx) -> LLMResponse`；实现：内网 LLM provider、FakeLLMProvider、可选外部 API provider。
- 数据边界（D7）：密级**全序**：secret > internal_code > build_log > public（聚合取最高 = 取全序最大）；密级由数据产出组件出生标注并随对象传播，聚合（EvidencePacket/消息/派生摘要/LLM 输出）取成员最高密级，API 不提供降级操作；provider 可接收密级集合由**中心安全配置**授权（非 provider 自报）；每次调用（含 cascade fallback 的每一跳）重新校验，fail-closed。业务侧绕过 SDK 自拼 payload 属残余风险（§14 R8），以 conformance 误标检测 + 约定管理。
- 路由：static binding → rule-based → cascade；cascade 升级判据 = 传输错误/超时/结构化输出校验失败（质量性判据不做，N3）。统一重试/超时/限流/token 记账。

### 7.2 KnowledgeProvider
接口同 v0.1；缓存键策略由 provider capabilities 声明：代码事实类（CodeGraph）键含 snapshot_id + tree_digest，知识库类（Wiki）键不含基线。查询结果出生即带密级（D7）。

### 7.3 Context 管理（四层）
Run 级共享状态（框架，只读注入）；Agent 工作上下文与 token budget（SDK 工具：预算执行、截断/压缩策略）；EvidencePacket 组装（§7.4）;知识注入（带来源与密级）。

### 7.4 EvidencePacket 工具链
结构 facts / negative_facts / log_excerpts / target_source_excerpt / confidence；negative_facts 仅限工具产出的否定性代码事实；日志摘录组件负有**按内容升级密级**的责任——摘录中内联源码行即标 internal_code，不因来源是 build_log 而低标；**产 patch 请求必含 target_source_excerpt**（有界行数）；校验器含 RawDataDetector 与体积上限；packet 密级 = 成员最高密级。

### 7.5 Ledger、Artifact、trace
- **Ledger（D6）**：单 SQLite（WAL）承载 Run/Task 状态机、artifact 索引、side_effect 状态、循环计数、gate 等待项、授权/核销记录、resume outbox、事件流。**直写者唯一为编排进程**；worker / Approval 服务 / broker 一律经 control-plane RPC（§8.5）请求编排进程事务写入。task 完成事务 = 最终结果 + artifact 索引 + 幂等终态（intent/running 随执行即时提交，§5.2）。
- **Blob 提交协议**：artifact 落盘顺序强制 = 临时文件写入 → fsync → rename 至 digest 路径 → Ledger 索引事务提交；上传中 blob 持有 active-upload lease（临时命名空间），GC 仅回收超安全年龄且无 lease 的对象——与合法上传并发安全；索引事务提交前复验 blob 存在与 digest；索引存在而 blob 缺失 = 损坏，消费方报 sys.error。
- **Artifact**：内容寻址（content digest 即引用组成部分）、写入后不可变；目录 `artifacts/<digest前缀>/...`；保留策略：终态 Run 的大体积构建日志类保留 N 天（配置，默认 14）后清理，patch/report/trace 永久保留。
- **trace.jsonl**：由 Ledger 事件流派生，追加安全；崩溃不影响权威源。

### 7.6 资源管理
#### 7.6.1 BuildExecutor
`build(snapshot, series, targets) -> BuildResult`；默认 `GbsLocalExecutor`：per-task git worktree 隔离、`git apply --index` + staged/worktree 一致性校验、构建可 probe（§5.2）；依赖范围默认 reverse-dependency 闭包增量，全量为显式开关。
#### 7.6.2 多仓 snapshot manifest
snapshot = `[ {repo_id, remote, commit, path} ]` 规范化清单；patch 逐条声明 repo_id；跨仓 series 按 manifest 序应用，任一仓失败即整体回滚该 worktree 组；tree_digest = 各仓应用后 tree hash 的规范组合（逻辑定义；计算为纯算法、无需 worktree，见 §4.2.4，算法 `[01]`）。
#### 7.6.3 资源额度（单机自我保护）
BuildExecutor / BoardPool / worker 数各配信号量上限；排队 FIFO；磁盘水位检查（低于阈值拒绝新 Run 并告警）；worktree 于 task 终结时清理，泄漏由定期对账回收。

---

## 8. 安全

### 8.1 信任模型（D13）
内网单机、单操作员运维；Skill 调用方经 bearer token 认证、视为受信；**patch 与其触发的构建脚本视为半可信**——不做完整容器沙箱（N7），控制面为：凭据物理隔离于 broker（8.3）、能力句柄按授权注入（5.1.1）、worker 子进程可强杀、发布必经 token。残余风险（恶意构建脚本网络外传源码等）登记 §14 R7，由内网环境与来源受信假设覆盖；该假设失效（如接入不受信来源）时必须先补沙箱。假设边界显式包含：**调用方认证 ≠ 内容可信**——patch 为 LLM 生成物、上游提示与语料不受控，间接提示注入可使受信来源产出恶意构建脚本，此路径属 R7 覆盖范围。

### 8.2 Approval 服务（框架交付）
- 独立进程 + **Review CLI**（MVP 形态；§9 Web 视图保持只读，不承担审批）。服务仅监听本机 Unix socket，远程 reviewer 场景显式不支持（D13）；CLI 认证 = socket peer credential（本机用户）+ 服务端 reviewer 名单。
- **审批对象 = ci_plan 产出的 ReleasePlan 规范化而成的 ReleaseManifest**（snapshot、tree_digest、发布目标、动作、pipeline_digest、exec_manifest_digest）——reviewer 在 CLI 看到并批准的即 broker 将执行的内容（示例流水线中 ci_plan 前置于 human_review 即为此）。
- （本节全部条款仅适用 **release-approval 型** hitl；plain-decision 型的 approve/reject 单命令只含决定 + gate outcome CAS + resume outbox，无 manifest 与授权记录项，§4.4）approve 经 control-plane RPC 单命令原子提交：审批决定 + **Ledger 授权记录（绑定字段见 §3）** + gate outcome CAS + resume outbox；事务内 **CAS 校验新鲜度**——gate 仍 waiting、被批 ReleasePlan 仍为该 Run 当前版本、series/tree_digest 仍为最新，任一不满足即拒绝并提示 reviewer 重审（series 推进事务同时撤销待审批项与未核销授权，§4.2.4）。CLI 呈现 manifest 及其关联证据链（ReviewReport、逐段出处的 patch series、各阶段 Report 引用；plain-decision 型呈现该 gate 上游 Report 与决策上下文——两型清单均细化入 01/07）；manifest 规范化算法 `[01]`。授权不以 bearer 形态存在、不进图状态/checkpoint；**权威判据唯一 = Ledger 记录**，无签名/HMAC 第二通道。
- series 变化 / Run 关闭 / 过期 → 未核销授权自动失效；过期授权被消费时 broker 返回 release_failed(reason=authorization_expired)。

### 8.3 Release broker（框架交付）
- 独立进程，唯一持有发布凭据；输入 = release 节点转发的 ReleasePlan + 授权引用（token_id，非 bearer）。
- **核销前置检查**：D12 制品/配置 digest 复核在核销之前执行——版本漂移以专用控制面错误码上报编排层并触发 administrative finalize，**不烧授权、不伪装成 release_failed**（R3-11 定案）。
- 原子 compare-and-consume = 发布 **point-of-no-return**：经 control-plane RPC 在 Ledger 事务内校验授权（未核销、未过期、全部绑定字段——run/gate/decision/ci_plan_task/series/manifest——与当前状态一致）、标记核销并**原子迁移 Run → publishing**；publishing 期间 cancel / 并行 fail_safe / series 更新 / **administrative finalize** 一律仅登记 pending、不得先关闭 Run；**publishing 是 administrative finalize 的状态级例外**——即使 D12 漂移或进程重启，也必须先与 broker 对账或 probe 远端结果，不可判定时保持 publishing 待人工处置。**终态映射（固定表，ledger 级执行、不经 DSL 路由，细则 `[01]`）**：broker outcome 优先——released → closed(succeeded)（pending 事件记入审计与 **Run 终局摘要**——非 FeedbackReport，不改变已发布事实）；release_failed → 按序应用 pending：**administrative finalize（最优先：ledger 级 closed(fail_safe) + 版本漂移 FeedbackReport）** > cancel → closed(cancelled) > fail_safe → closed(fail_safe) > 均无 → closed(fail_safe) + ledger 级生成 release_failed FeedbackReport；series 更新仅记录。故障注入含 pending 组合断言（§11.3）。核销绑定 task_id——broker task 中断恢复时"已核销给本 task"视为有效。
- 发布执行远端幂等（push 前查远端）；远端冲突 → release_failed，禁止自动 rebase（R9）。
- **人工裁决协议（publishing 滞留出口，R13）**：仅对处于 publishing 且强制 probe 后仍不可判定的 Run 开放；命令三选一——`confirm_released` / `confirm_not_released` / `keep_unknown`（继续等待），前两者**必须附远端证据引用**。`confirm_not_released` 附加三重防迟到机制：① 状态 guard 前置 **broker 侧静默**——broker task 进程组已终止（lease 回收 + pgid reap 确认），本地不存在在途发布执行；② **fencing 标识**——发布操作向远端写入的对象一律携带唯一标识（commit message/Change-Id 含 run_id+token_id），迟到发布可归因；③ **裁决后复查窗口**——关闭后按配置窗口（默认 24h）**周期性**重 probe 远端（频次配置），窗口结束后并入常规审计对账（监视不终止）；检出迟到发布 → 告警 + **post-close correction 记录**：append-only 特权命令（同裁决通道权限），绑定原裁决、远端对象与证据引用、操作者、处理状态，单 Ledger 事务提交；**原终态不可变**，`get_result` 在终局摘要之外一并返回有效 correction 引用（调用方可见真实远端状态）。已离开本机的在途网络请求无法绝对 fence（git/gerrit 端点无两阶段提交），此为显式残余（R14）。经特权 OS 用户 + peer credential 执行；裁决记录（操作者、证据引用、按 §8.3 映射的终态迁移）单 Ledger 事务提交；E2E 故障用例（含证据缺失拒绝、broker 未静默拒绝、迟到发布检出）入 §11.3。
- **发布 adapter 归属（定案）**：gerrit 与 github 官方 adapter **由框架交付**、运行于 broker 进程内、纳入安全审计与版本 pin——broker 进程内代码全部属可信计算基，不接受业务侧同进程插件。其他 CI 工具扩展走受限模式：业务 adapter 运行于**无凭据子进程**、产出受限操作描述，由 broker 以框架凭据原语执行。§5.1.1 能力句柄清单显式排除发布通道。FakePublisher 随框架交付供测试。

### 8.4 脱敏与审计访问
持久化统一脱敏：凭据/secret 只记指纹（授权本身即 Ledger 记录，无 bearer 需脱敏）；LLM prompt/响应 artifact 带密级标签；Web 视图只读 + 本机访问；审计记录保留策略随 §7.5。

### 8.5 Control-plane IPC（特权内部接口，双向）
- **入向（→编排进程）**：Unix socket + peer credential 认证；Approval 服务、broker、worker 使用**不同 socket、不同 OS 用户与文件权限**。worker socket 仅开放**数据面命令**（显式枚举：side_effect 状态迁移、trace、artifact 索引提交、series candidate 提交）；审批与核销命令所在 socket 对 worker 进程不可访问（文件权限隔离）。
- **task 级绑定**：worker 数据面通道为 **per-task socketpair**，FD 由编排进程 spawn 时注入——无文件系统监听端点，伪造连接构造上不可能；仅接受注入的预绑定连接，其余一律拒绝并记审计。服务端从连接上下文推导 run_id/task_id 并以 Ledger task 租约校验——客户端不得自报归属，越域请求拒绝并记审计；conformance 含跨 task 篡改拒绝用例（§11.3）。
- **出向（编排进程→broker）**：broker 发布调度端点仅接受编排进程 UID（peer credential），请求绑定 run/task/manifest。
- 命令幂等（request_id）；复合状态变更（审批提交、授权核销+publishing 迁移）为单命令单事务；resume outbox 语义见 §4.4（decision_id 去重）。
- **部署 provisioning 属交付物**（§10 deploy/）：系统账户创建、socket mode/ownership、Ledger 与凭据文件权限、多用户 spawn 的专用特权 launcher（属可信计算基）、服务启动顺序；P4 gate 含真实 UID/文件权限下的 E2E 隔离测试。

---

## 9. 可观测性
基于 Ledger/trace.jsonl 的只读本地 Web 视图（Run 状态、节点进度、循环计数、token 消耗、artifact 浏览）；指标离线聚合。不引入外部观测平台。

---

## 10. 部署形态与仓库结构

单机部署。monorepo：

```
coding-system/
├── framework/
│   ├── engine/            # EnginePort 的 LangGraph 实现（唯一 import langgraph 处）
│   ├── orchestration/     # DSL 解析/校验、Run 生命周期、循环预算、outcome、worker 调度、control-plane RPC
│   ├── sdk/               # AgentBase、worker 入口、side_effect、trace、ctx
│   ├── contracts/         # pydantic schema + 版本校验
│   ├── llm/               # provider、fake、数据边界、路由
│   ├── knowledge/         # KnowledgeProvider + CodeGraph/Wiki 实现 + 缓存
│   ├── context/
│   ├── evidence/
│   ├── ledger/            # SQLite 权威源 + artifact store + trace 派生
│   ├── resources/         # BuildExecutor(GbsLocal)、BoardPool 接口/Fake、额度管理
│   ├── approval/          # Approval 服务 + Review CLI
│   ├── release/           # Release broker + 官方 gerrit/github adapter + FakePublisher + 受限扩展接口
│   └── skill/             # Skill HTTP server
├── agents/
│   ├── skeletons/         # 五类 agent 可运行空壳 + producer/consumer fixtures
│   └── compiler/          # reference agent（P5 起）
├── conformance/           # 合规套件 + engine conformance + 本地 harness
├── pipelines/             # full_migration.yaml、compiler_bench_only.yaml 等
├── deploy/                # 安装脚本、systemd 单元、账户/权限 provisioning、特权 launcher
├── docs/                  # 00–09、review/、dev_memory 说明
└── ci/
```

分发（D4）：框架构建为 wheel `codingsystem-framework`（含 extras），业务 Agent 依赖该包并经 entry-point 注册；发布 gate 进 ci/。

---

## 11. 技术栈与质量门禁

### 11.1 技术栈
Python ≥ 3.12；LangGraph 依赖闭包 lockfile 锁定（D1）；pydantic v2；SQLite(WAL)；PyYAML。

### 11.2 门禁
pytest + coverage 全局 ≥ 80%；**关键模块（orchestration、ledger、approval、release、sdk.side_effect）分支覆盖 ≥ 95%**；mypy --strict；ruff；import-linter（引擎封装）。

### 11.3 强制测试类别（P1–P4 gate 组成部分）
DSL property/fuzz（随机图 → 校验器判定性质：可达环必有 budget、release 必经 hitl 等）；状态机 model-based 测试；**逐持久化边界故障注入**（每个 Ledger 提交点前后 kill，验证恢复与对账）；token 并发双消费测试；陈旧 series 进 gate/join 拒绝测试；checkpoint/execution manifest 不匹配拒绝恢复测试；artifact 损坏检测（digest 校验）与 blob 提交顺序逐点崩溃注入（孤儿 GC / dangling 索引对账）；control-plane IPC 权限隔离测试（worker socket 不可达审批/核销命令；跨 task 篡改拒绝；真实 UID/文件权限 E2E）；同 series 多轮循环下 join activation 分组与崩溃重放，含四组 model-based 断言——旧 activation 已首达后推进 series → stale 超时不误杀；同 series 并发多 activation 独立成组；不推进 series 的环（旧源已到达、环边采用、新 activation 成功、旧计时器后到 → 条件③已退役、无误杀）；父退役级联（嵌套子 activation 计时器同事务作废、不误杀，替代 cohort 继承父 scope 后参与外层 join）——及"分支内回环（不重经共同 fan-out）与跨祖先回环（先重经祖先 activation 的 fan-out）均拒绝加载"validator property；跨 attempt 三支定态 × 异参 claim 动作矩阵（succeeded/abandoned 放行新键、succeeded 不跨参复用、unknown 无新键、干净终态 failed 依类别策略放行）测试；publishing 终态映射 pending 组合（含 pending administrative finalize）故障注入与人工裁决 E2E（证据缺失拒绝、broker 未静默拒绝、迟到发布检出）；post-close correction（迟到检出、重复/并发修正、get_result 呈现）；effect_call_id 唯一性 conformance 与"双同参调用首成后崩溃、重试控制流变化"注入；probe-only / replay_safe / 皆无三类效应对账覆盖；join 作用域与共同到达 validator property（嵌套 fan-out、互斥 outcome、嵌套汇合重入外层三类反例）；恢复复用既有 dispatch 记录断言；publishing 期间进程重启/D12 漂移的对账优先注入；blob 上传与 GC 并发注入；编排进程崩溃且 GBS 子进程存活注入；五类 agent_type 的 contract producer/consumer fixture 兼容测试。conformance attestation：结果绑定 agent 制品 digest + contract/套件版本，digest 变更即失效，加载时校验。

---

## 12. 环境前提与 E0 预检
同 v0.1 表（gbs 工具链 / image URL / gerrit 探测 / CodeGraph / LLM Wiki / FakeLLM），追加：Approval 服务与 broker 的本机进程部分无外部环境依赖、不进 E0 预检；**官方发布 adapter 的真实端点联调（gerrit/github 端点、凭据、目标仓权限）为独立上线 gate 材料**——开发与 P4 验收基于本地 API 模拟器/fixture，真实端点验证由负责人在受控环境执行（用例 07 提供），未通过前不得对生产目标发布。

---

## 13. 分期计划概览（细化见 09）

| Phase | 交付 | 完成 gate |
|-------|------|----------|
| P0 | 00/01 复审通过 draft freeze；08/09 就绪 | 三方 unanimous GO |
| P1 | EnginePort + engine/ + DSL v1 校验器/编译器 + Run 状态机 + Ledger 核心 + worker 调度 | mock agents：全量/子集配置加载；逐边界故障注入恢复通过 |
| P2 | SDK（worker/side_effect）+ contracts + Skill server + **control-plane RPC + Approval 服务 + Review CLI + Release broker（FakePublisher + 官方 adapter 骨架）** | conformance 骨架 + 授权并发/双消费 + RPC 权限隔离测试通过 |
| P3 | 公共模块（LLM 层+数据边界、Knowledge 双实现联调、context、evidence、GbsLocalExecutor、FakeBoardPool、资源额度）+ **官方 gerrit/github adapter 功能完成与打包（对本地 API 模拟器集成）** | 真实 gbs 最小构建 + 数据边界 fail-closed + adapter 模拟联调用例通过 |
| P4 | 端到端：全量与子集 pipeline（mock 业务 + 真实构建 + CLI 审批 + Fake/模拟器发布）+ deploy/ 资产 | §11.3 全部测试类别 + 真实 UID/权限 E2E 隔离测试通过 = 框架完成；真实发布端点联调为独立上线 gate（§12） |
| P5+ | reference Compiler Agent + 五类 fixture + 兼容矩阵 | contract v1.0（G6） |

---

## 14. 风险登记

| # | 风险 | 检测信号 | 预防/恢复 | Owner |
|---|------|---------|-----------|-------|
| R1 | gerrit 不可达 | E0 探测 | fixture snapshot 降级 | 负责人 |
| R2 | 引擎恢复语义与实现偏差 | P1 故障注入 gate | side_effect 为硬前提（§4.1）；引擎替换经 EnginePort | 框架 |
| R3 | contract 脱离真实业务 | P5 消费失败 | D10 三条件 gate | 框架 |
| R4 | 真实构建拖慢迭代 | CI 时长 | fake 分层测试；真实构建仅 gate/nightly | 框架 |
| R5 | 内网 LLM 与 Fake 不一致 | provider 一致性测试（07 用例，内网执行） | 上线独立 gate | 负责人 |
| R6 | 业务侧绕过 SDK/引擎约束 | conformance attestation 失效告警 | 能力句柄授权注入 + 准入 attestation（§5.1/§11.3）；承认运行时非全量强制 | 框架+业务 |
| R7 | 恶意/缺陷构建脚本外传或破坏（无全沙箱） | 内网出口监控（环境侧） | D13 来源受信假设；假设失效前置补沙箱 | 负责人 |
| R8 | 数据边界被自拼 payload 绕过 | conformance 误标检测 | D7 来源标注收窄面；残余承认 | 框架+业务 |
| R9 | 基线漂移致发布冲突（review 挂数日） | broker push 前远端检查 | 禁止自动 rebase；冲突 → fail_safe → 新 Run | 框架 |
| R10 | 磁盘耗尽/artifact 膨胀 | 水位检查 | 保留策略 + 拒新 Run 阈值（§7.5/§7.6.3） | 框架 |
| R11 | approval 服务不可用 | gate 等待超时告警 | Run 保持 paused；服务无状态重启（状态在 Ledger） | 框架 |
| R12 | 旧 checkpoint 配新版本 | D12 校验 | 拒绝恢复 → fail_safe，不在途迁移 | 框架 |
| R13 | publishing 滞留（broker 挂起/对账不可判定） | publishing 时长超阈值告警（计时豁免不含告警） | 运维 CLI 对账/裁决命令（交付项，入 09）人工处置 | 框架+负责人 |
| R14 | confirm_not_released 后迟到发布（在途请求无法绝对 fence） | 复查窗口周期 probe（窗口后并入常规审计对账）+ fencing 标识归因 | 告警 + post-close correction 记录（append-only，终态不可变，get_result 可见）；不静默 | 框架+负责人 |

---

## 15. 附录
- A1 术语表：§3。
- A2 `[待补充]`：gbs.conf、gerrit 探测方式、内网 LLM 接口规格、CodeGraph/LLM Wiki 仓库地址。
- A3 引用：01/07/08/09（待产出）；docs/review/ 下 v0.1–v0.11 十一轮处置表。
- A4 v0.1→v0.2 变更摘要：DSL v1 完整语义（显式节点/join/loops/穷尽路由/保留节点/合法子集定义）；Approval 服务与 Release broker 纳入框架交付并修复 token 时序矛盾；at-least-once 语义显式化 + 两阶段 side_effect + 恢复协议；Ledger 单一权威源；execution manifest（D12）；多仓 snapshot manifest；worker 进程模型；数据边界来源标注；信任模型显式化（D13/N7）；并发模型（D11）;测试类别强制（§11.3）;风险表扩充；全部交叉引用修正。
- A5 v0.2→v0.3 变更摘要：join 触发机制定案（到达=入边路由送达，wait_for ≡ 入边源集合）+ 旗舰示例修正（死锁修复）；审批时序重排（review_final → ci_plan → human_review → release，approved 直达 release，审批对象=规范化 ReleaseManifest）；授权改为 Ledger 记录形态（无 bearer、无 HMAC，crash-safe）；control-plane RPC（§8.5）+ Ledger 直写者收敛 + Blob 提交协议；官方 gerrit/github adapter 纳入框架交付（broker 进程 = 可信计算基）；idem_key 去 attempt + probe 结果恢复 + claimed ack 前置；worker 进程组 kill + 心跳自杀 + 孤儿 reaping；terminal success_on 与 release outcome 集；hard-required 支配性检查；执行槽/paused 节点级语义 + create_run FIFO + awaiting-patch TTL；administrative finalize（不经引擎收尾）+ dispatch 期 digest 复核；密级全序；loop 计数边界定案（N 次通过、第 N+1 次拦截）；gate outcome 封闭枚举；series_id 框架签发；R7 假设边界补充（认证≠内容可信）；引用路径修正 docs/review/。
- A6 v0.3→v0.4 变更摘要：idem_key 效应级锚定（effect_class + effect_params_digest + effect_seq，修复非决定论重执行键碰撞）+ §4.3.2 残留"含 attempt"矛盾清除 + 上一 attempt 遗留记录对账；授权记录绑定扩展（run/gate/decision/ci_plan_task/series）+ approve 事务新鲜度 CAS + series 推进撤销待审批项；发布 point-of-no-return（核销原子迁移 publishing，期间 cancel/fail_safe 仅登记 pending）；D12 漂移核销前检测→administrative finalize（不烧授权）；series 推进收敛为编排单事务（candidate + expected_parent CAS）；resume outbox 消费端去重（decision_id + inbox + durable dispatch）；join activation 语义（activation_id/到达键/原子整组消费/重复丢弃/超时起算）+ 非 join 汇聚语义 + 禁链式 join；threshold 指标来源支配性与同 series 检查；状态机补 awaiting_patch/queued/publishing；心跳丢失 worker 先 killpg 后退；blob GC lease/安全年龄 + 索引前复验；IPC 双向化（broker 入站仅编排 UID）+ worker 数据面命令枚举 + task 级 socket FD 绑定 + deploy/ provisioning 交付；provider digest 含端点身份；官方 adapter P3 完成/P4 模拟联调/真实端点为上线 gate；hitl 直达约束限定 release 可达路径 + release 出边禁入环；日志摘录按内容升级密级；术语与路径修正（Approval 不核销、release 特权节点、docs/review/）。
- A7 v0.4→v0.5 变更摘要：activation 生命周期退役规则（series 推进同事务作废旧 open activation 及计时器、superseded 触发条件、CAS 守卫、仅最新 activation 超时可 fail_safe、生成/持久化/传播时点）；idem_key 改锚 logical effect slot（run/node/activation_id，去 loop_round）+ effect_seq 计数语义（去"连续"）+ 记录状态全集与查找矩阵（abandoned 不参与命中、同参新调用递增新键、unknown→sys.error）；publishing 为 administrative finalize 状态级例外 + broker outcome 优先的固定终态映射表（pending cancel/fail_safe 次序）；resume 路径定案 paused→queued→running + 状态图重绘（publishing 入出边显式）；hitl 分两型（release-approval / plain-decision，后者不生成 manifest 与授权）；run_budget 与 join timeout 计时排除 paused/publishing；worker 数据面通道定为 per-task socketpair（无监听端点）；术语与措辞对齐（授权记录、tree_digest 逻辑定义句）；§11.3 补 stale-activation 不误杀与 publishing 对账优先用例。
- A8 v0.5→v0.6 变更摘要：effect slot 改锚 dispatch_id（边送达/分派事件 Ledger 标识——跨 attempt 稳定、跨 task 含兄弟送达与 entry 天然隔离，node/activation 退出键组成）+ effect_seq 由编排层 claim 事务分配 + 对账策略反转（probe 确认成功 → succeeded 可复用，废除 succeeded-abandoned 保守重做——可 probe 不可安全重放的效应必须复用）+ 状态全集补 unknown；activation supersede 收敛为两条件（series 推进 / 到达全 stale），废除"更新者淘汰旧者"，同 series 多 activation 独立 open/消费/超时 + 根 activation（entry 分派事务生成）；release 节点无出边——outcome 由 §8.3 固定映射 ledger 级关闭（pending 序：administrative finalize > cancel > fail_safe > 默认），成功路径改记 Run 终局摘要（非 FeedbackReport）；§8.2 条款限定 release-approval 型（plain 型无授权项）+ plain 型 CLI 证据链；R13 publishing 滞留告警 + 运维对账/裁决 CLI；状态图补 running→closed(succeeded) 直达说明；§11.3 补并发 activation model-based 与 pending 组合注入。
- A9 v0.6→v0.7 变更摘要：效应键引入调用方稳定 effect_call_id（框架强制 task 内唯一、显式重复经 repeat_seq），废除服务端按序分配 effect_seq——顺序匹配在控制流变化重试下不成立；查找矩阵补 replay_safe 三支对账（probe / replay_safe 版本化重放 / 皆无→unknown+sys.error），消除与效应能力契约的冲突；join 作用域静态检查（唯一共同支配 fan-out、拒绝未汇合嵌套 fan-out 与同源多送达）；publishing 人工裁决协议（confirm_released/confirm_not_released 须附远端证据、keep_unknown、特权凭证、单事务）；§4.4 授权记录项限定 release-approval 型（消除内部矛盾）；恢复复用既有 dispatch 记录声明（键跨重启稳定前提）；FeedbackReport 两条 ledger 级例外列全 + Run 终局摘要入术语表与 §6.1；§4.2.4 activation 生成事件枚举同步、supersede 条件②标注防御性兜底；§4.2.5 重复句清除；§11.3 对应用例补齐。
- A10 v0.7→v0.8 变更摘要：join 静态检查升级为共同 fan-out 派生 + 共同到达性（互斥 outcome 分支图拒绝：每 outcome 分支须可达来源/到终局/经环边回流）；嵌套汇合定案父 activation 关系（parent_activation_id 持久化，内层 join 消费后以父 scope 分派——内层先汇合再入外层合法）；effect_seq 悬空引用清除 + SDK 签名定案 side_effect(effect_call_id, params, fn, repeat_seq)（idem_key 仅框架计算）+ 记录版本化提升为通则 + call_id 唯一性两层面定义（conformance 静态 + 运行时异参未决拒绝 sys.invalid_result）+ 术语纠正（对账退役不用 supersede）；confirm_not_released 三重防迟到（broker 静默 guard、fencing 标识、裁决后复查窗口）+ R14 残余登记（在途请求无绝对 fence，git/gerrit 无两阶段提交）；§3 补 dispatch_id/activation/effect_call_id 三条术语；§11.3 用例同步。
- A11 v0.8→v0.9 变更摘要：supersede 新增条件③不可补全退役（环边采用同事务退役旧 cohort 并作废计时器——退役依据为可证明不可补全性，非 latest-wins；series-非推进环误杀反例消除）+ §4.2.6 条件(iii)括注与 §11.3 断言同步修正；effect_class 来源定案（fn 所属注册效应类型推导，自由函数不可包装）；同 call_id 异参两规则的 attempt 范围词补齐（跨 attempt 对账清零 / 同 attempt 运行时拒绝）；post-close correction 记录定案（append-only 特权命令、终态不可变、get_result 返回 correction 引用）+ 复查窗口语义（窗口内周期 probe、窗口后并入常规审计对账）+ R14/终局摘要条目同步；共同 fan-out 派生量词修正（来源集在分支间构成划分）；§11.3 补三组用例（条件③模型断言、裁决 E2E 两例、correction 三例）。
- A12 v0.9→v0.10 变更摘要：supersede 条件③补全——退役沿 parent_activation_id 级联全部子孙（连带作废计时器）+ join 消费/分派/timeout CAS 增加祖先链无 superseded 校验（向死 scope 分派拒绝并审计）+ 替代 cohort 语义定案（继承被退役者 parent_activation_id，环不插入额外嵌套层级）+ 措辞修正（"采用该环边的 task 所属 activation 上下文"）+ 重复 no-op 句合并；§4.2.6 条件(iii)静态收敛——环边回流必须重经该 join 的共同 fan-out（重派全部来源分区），分支内回环拒绝加载；§5.2 跨 attempt 对账由"清零/统一 abandoned"改为逐支定态（probe 成功→succeeded、未发生/replay_safe→abandoned、不可判定→unknown+sys.error；succeeded/unknown 不得改写），异参新键仅立于允许继续的终态之上；§11.3 补级联退役断言、分支内回环拒绝 property、跨 attempt 定态矩阵。
- A13 v0.10→v0.11 变更摘要：§4.2.6 条件(iii)补第二条静态约束——环边在重经自身 activation 的共同 fan-out 之前不得先重经任何祖先 activation 的共同 fan-out（跨 activation 边界回环拒绝加载：退役根静态保证等于被替代作用域，消除外层 activation 逃过退役的组合缺口）+ 括注按"合法条件—机制—拒绝情形"重排；§5.2 异参新键允许集合枚举定案（succeeded/abandoned 放行且 succeeded 不跨参复用、unknown 无新键）；§11.3 用例格式修正并补跨祖先回环 property 与定态×异参动作矩阵。
- A14 v0.11→v1.0-draft-frozen 变更摘要（第十一轮 freeze 勘误）：§4.2.6 条件(iii)双"拒绝加载"指代分离（违反环约束的回环 / 三分支皆不满足的图，各自明示）；§5.2 异参新键枚举补范围短语（仅辖跨 attempt 定态记录；干净终态 failed 依既有类别策略放行）；§11.3 动作矩阵补 failed 行。裁决：第十一轮 Kimi GO(1 MINOR+1 NIT) / Claude Code GO(1 NIT) / Codex GO(1 NIT)，三方一致通过，勘误全部落入本版。

## 16. 附录 B：[01] 待落清单汇总（01_Contract_Spec 编写骨架）

正文 18 处 `[01]` 标注的已定案项，按 01 章节归组：
1. **DSL 与静态校验**：pipeline YAML 完整 schema（nodes/routes/loops/joins/gates/terminal success_on）；校验规则形式化（§4.2.6 全部规则，含共同到达性三条件、环边双约束、join 作用域/划分、支配性检查）；target_spec 语义。
2. **状态机与消息**：Run 状态机命令/guard 表（含 publishing、administrative finalize、post-close correction）；TaskInput/HandoffResult/各 Report/RunContext/ReleasePlan/ReleaseManifest（规范化算法）/授权记录/Run 终局摘要与 correction 记录 schema；join_inputs 形态；Skill 协议消息与错误语义。
3. **activation 与 series**：activation 传播定义（根/父子关系/替代 cohort 继承）；series lineage 与 tree_digest 算法；陈旧性判定细则。
4. **效应幂等**：effect 记录六态迁移/查找矩阵与版本化；effect_call_id 唯一性细则与 sys.invalid_result 归类；effect_class 注册与能力声明（probe/replay_safe）契约；恢复协议逐支细则。
5. **安全接口**：control-plane 命令集（数据面枚举、审批/核销、裁决、correction）；受限扩展 adapter 的操作描述与凭据原语契约；数据密级标注与传播规则。
6. **conformance**：§11.3 全部测试类别的用例级定义与判定标准（07 引用）。
