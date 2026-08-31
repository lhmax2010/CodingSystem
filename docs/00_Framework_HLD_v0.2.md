# 00 — Multi-Agent Framework 高层设计（HLD）

**版本**: v0.2 Draft（v0.1 三方评审 NO-GO 后修订版，待复审）
**状态**: 复审中
**读者**: 框架开发（Codex）、cross-reviewer（Kimi / Codex / Claude Code）、后续业务 Agent 开发者
**关联文档**: 01_Contract_Spec、02–06_Agent_Design_Guide、07_Conformance_and_Onboarding、08_Codex_Dev_Guide、09_Phased_Dev_Plan、docs/reviews/HLD_v0.1_review_disposition.md（本版逐条处置表）

> **文档定位**：本文档按"Codex 可直接开发"标准编写——关键路径上的技术决策均已定案，不提供备选方案。凡标注 `[待补充]` 的内容为环境类事实材料（由项目负责人核对后填充），不阻塞架构评审；凡标注 `[01]` 的内容为已定案、精确 schema 在 01_Contract_Spec 给出的项。

---

## 1. 背景与目标

### 1.1 背景

本框架服务于 Tizen 平台工程的自动化软件工程流水线（CodingSystem 重启版）。完整目标态为六角色协作：外部 Coding Agent（ClineSR / 过渡期 Codex）产出业务 patch，框架内的 Compiler / UT / Benchmark / Review / CI 五类 Agent 完成编译修复、单测验证、性能基准、AI+人工审查、发布。

与旧版 CodingSystem 的关键差异：

1. **Coding Agent 移出框架**——仅通过 Skill 协议调用流水线，框架对其零依赖；
2. **框架平台化**——本团队交付：框架 + 公共模块 + **approval 服务与 release broker（发布安全组件，见 §8）** + reference Compiler Agent；业务 Agent（UT / Benchmark / Review / CI）由业务开发者依据 02–06 设计指引二次开发；
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
| D8 | 发布安全 | 发布凭据仅存在于框架 **release broker** 独立进程；CI Agent 只产 ReleasePlan；broker 对 approval token 原子 compare-and-consume，token 绑定 release manifest digest | 业务 Agent 拿不到凭据，绕过面收敛到 broker 单点 |
| D9 | 循环上限 | 循环为 DSL 显式声明的 `loop` 对象（环级预算），编排层强制；另有 Run 级总预算 | 计数归属清晰、静态可校验 |
| D10 | Contract 冻结 | draft freeze（三方评审）→ v1.0（G6 三条件） | 未被真实消费的 contract 不定稿 |
| D11 | 并发模型 | MVP：**单活跃 Run**；Run 内节点级并行；task 以子进程 worker 执行；资源经信号量额度管理（§7.6.3）；Ledger 单写者（编排进程） | 单机资源与 SQLite 约束下最小正确模型 |
| D12 | 执行环境固化 | Run 创建时固化 execution manifest：pipeline digest、contract 版本、框架版本、agent 制品 digest、provider 配置 digest、引擎版本；恢复时不匹配即拒绝恢复（fail_safe），不做在途迁移 | 旧 checkpoint 在新图上恢复是官方明示的兼容性风险 |
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
| gerrit/github 发布 | **release broker 执行**（CI Agent 只产计划） | broker 交付含 FakePublisher；真实 gerrit adapter 属 CI 业务侧按 broker 插件接口实现 |

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
| **Artifact** | 内容寻址不可变对象（写入即定 content digest），Ledger 索引，消息只传 `artifact_ref` |
| **Ledger** | 单一 SQLite 权威事实源（D6） |
| **EvidencePacket** | 提交给 LLM 的结构化证据包（§7.4） |
| **Skill 协议** | 外部 Coding Agent 与框架交互的 HTTP+JSON 协议（§6.5） |
| **Approval 服务** | 框架交付的独立进程：接受 reviewer 决定（approve/reject）、签发/核销 approval token、触发 gate resume（§8.2） |
| **Release broker** | 框架交付的独立进程：唯一持有发布凭据；核销 token、按 release manifest 执行发布（§8.3） |
| **approval token** | approve 时签发的一次性令牌，绑定 `run_id + release_manifest_digest`（含 snapshot、tree_digest、发布目标、pipeline_digest、exec_manifest_digest、过期时间）；仅在 broker 处原子核销一次 |
| **保留节点** | DSL 内置节点，无需在 nodes 声明即可作为路由目标：`fail_safe`（终局处理：聚合证据产 FeedbackReport 并关闭 Run）。保留命名空间 `sys.*` 与裸名 `fail_safe`，用户节点禁用 |
| **fail_safe** | 仅指上述保留节点；Run 终态统一为 `closed(reason)`（§4.3.1），不再用 fail_safe 指代状态 |

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
  review_static:  { agent_type: review, mode: static }    # 同 agent_type 两实例=两个显式节点
  review_final:   { agent_type: review, mode: final }
  human_review:   { gate: hitl }
  ci_plan:        { agent_type: ci }               # 只产 ReleasePlan
  release:        { broker: release }              # 特权节点，见 4.2.5
entry: compiler
loops:
  - id: ut_fix_loop
    edges: [ { from: ut, to: compiler } ]
    budget: { max_rounds: 2, max_wall_clock_min: 180 }   # 计时不含 gate 暂停
run_budget: { max_wall_clock_min: 1440 }
joins:
  - id: pre_final_review
    wait_for: [ut, bench_gate, review_static]      # all-of；同 series 才聚合(4.2.4)
    to: review_final
routes:
  - { from: compiler,      on: build_passed,            to: [ut, review_static] }
  - { from: compiler,      on: build_failed_exhausted,  to: fail_safe }
  - { from: ut,            on: ut_passed,               to: benchmark }
  - { from: ut,            on: ut_fix_patch_ready,      to: compiler, loop: ut_fix_loop }
  - { from: benchmark,     on: bench_done,              to: bench_gate }
  - { from: bench_gate,    on: pass,                    to: join:pre_final_review }
  - { from: review_static, on: review_report_ready,     to: join:pre_final_review }
  - { from: review_final,  on: review_report_ready,     to: human_review }
  - { from: human_review,  on: approved,                to: ci_plan }
  - { from: human_review,  on: rejected,                to: fail_safe }   # 终局处理统一走 fail_safe
  - { from: ci_plan,       on: release_plan_ready,      to: release }
default_route: fail_safe    # 任何未匹配 outcome（含全部 sys.*）的兜底
```

#### 4.2.2 节点与寻址
- 同一 agent_type 的多次使用 = 多个显式节点（各带自有配置），**不存在 `node.qualifier` 点号寻址**；路由 from/to 只引用已声明节点名、保留节点、或 `join:<id>`。
- 保留节点见 §3；`entry` 必填且唯一；终局节点为 `release` 成功、`fail_safe`、或显式 `terminal: true` 节点（子集流水线用，如 benchmark-only 在 bench 报告后终止）。

#### 4.2.3 路由穷尽性
- 每个 agent_type 注册时声明业务 status 全集 `[01]`；校验器强制：`on` 值 ∈ (该节点 status 全集 ∪ gate 结果集 ∪ sys.* )，且每个节点的业务 status 要么逐条有路由、要么被 `default_route` 覆盖（`default_route` 必填）。拼写错 status 在加载期即被拒绝。

#### 4.2.4 并行与汇合
- fan-out：`to: [a, b]` 并行分派。
- join：显式 `joins` 声明，语义为 all-of——全部 `wait_for` 上游到达且 **series_id 一致**才触发；收到不一致 series 的旧结果标记 `stale` 并丢弃、等待同 series 新结果（上游若不会再产出则按超时→fail_safe）。
- 并行分支任一进入 fail_safe：编排层取消同 Run 其余在飞分支（worker 终止，§5.1.2），Run 走终局处理。
- 陈旧性通则：任何 Report 携带 series_id；gate 与 join 只接受与当前最新 series 一致的输入；series 变化自动使已签发未核销的 approval token 失效（§8.2）。

#### 4.2.5 特权节点
- `broker: release` 节点由框架内置实现（转发 ReleasePlan 至 release broker），不可被业务 agent_type 顶替。校验器强制：release 节点入边有且仅有来自 `hitl` gate 下游路径（静态可达性检查：所有到 release 的路径必经 hitl）；凭据授权配置只接受 broker，"CI 类节点判定"问题因此消失——业务 CI Agent 永远无凭据。

#### 4.2.6 子集合法性（"合法子集"的定义）
静态校验器全部规则：节点/路由/join 引用有效；entry 存在；每个可达环均被某 `loops` 声明覆盖且带 budget；路由穷尽（4.2.3）；含 release 节点则必经 hitl（4.2.5）；threshold gate 引用的指标来源节点在图中存在（不存在即拒绝加载——hard-required 依赖同理：Agent contract 可声明少数 hard-required 上游产物 `[01]`，其余一律 optional 降级，§6.3）；无不可达节点。通过全部规则 = 合法子集；示例 `pipelines/compiler_bench_only.yaml` 随仓交付。

### 4.3 Run 生命周期

#### 4.3.1 状态机（穷尽）

```
created ──snapshot_pinned──▶ running ◀──resume── paused(gate)
   │                          │  │ ▲                │
   │ (snapshot失败)           │  └─┘(节点流转)       │(reject/超时TTL)
   ▼                          ▼                     ▼
 closed(snapshot_error)   closed(succeeded)      （经 fail_safe 节点）
                          closed(fail_safe)  closed(cancelled)
```
- 终态统一 `closed(reason)`，reason ∈ {succeeded, fail_safe, cancelled, snapshot_error}；FeedbackReport 在 reason=fail_safe 时由保留节点生成。
- 非法转换由 Ledger 状态机守卫拒绝并记审计；全部转换的命令/guard 表 `[01]`。
- cancel 入口：Skill `cancel_run`（限创建者）与运维 CLI；取消时在飞 worker 终止，进行中的 side_effect 按 §5.2 恢复协议处置。

#### 4.3.2 框架级 outcome 与错误策略
- worker 异常退出/execute 抛未捕获异常 → `sys.crash`；硬超时 → `sys.timeout`；HandoffResult 非法或 status 未注册 → `sys.invalid_result`；setup 失败 → `sys.error`。
- `sys.*` 默认走 `default_route`（即 fail_safe）；节点可配置 `retry: { on: [sys.crash, sys.error], max: N }` 由编排层重试（同 task 新 attempt，幂等键含 attempt 序号的意图记录见 §5.2）。
- 编排层对 wall clock 的强制以 worker 进程 hard-kill 实现（§5.1.2），不依赖 Agent 代码配合。

#### 4.3.3 恢复
- 进程重启后：校验 execution manifest（D12），匹配则经 EnginePort 从 checkpoint 恢复；不匹配 → closed(fail_safe) 并在 FeedbackReport 注明版本漂移。
- 恢复即节点重执行（§4.1 前提），正确性由 side_effect 层保证。

### 4.4 Gate
- `hitl`：Run 转 paused，Ledger 登记等待项；Approval 服务收到 reviewer 决定后写 Ledger 并触发 resume（approve → outcome=approved 并签发 token；reject → outcome=rejected）。**resume 不消费 token**；token 唯一消费点在 broker（§8.3）。gate 可配置 TTL（默认无），超时 outcome=`gate_expired` 走路由（默认 fail_safe）。
- `threshold`：纯代码判定；指标缺失/非法一律 fail-closed（outcome=fail，默认路由 fail_safe），不允许 fail-open。

### 4.5 循环预算
- 预算属于 `loops` 声明的环对象；编排层在环入边流转时 +1（进入即计数），计数持久化于 Ledger 并随恢复延续；wall_clock 累计计时排除 paused 时段；多环共享节点时各环独立计数。任一预算触顶 → 强制路由 fail_safe。`run_budget` 为 Run 级总预算，最先触发者生效。

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
- Agent 经 `ctx` 获得框架注入句柄：artifact store、KnowledgeProvider、LLM client、EvidencePacket builder、trace、以及**能力句柄**（BuildExecutor / BoardPool 等，按 agent_type 在配置中授权注入；未授权的能力句柄不存在于 ctx——业务代码想发布也拿不到通道，与 D8 联动）。
- 注册：entry-point namespace `codingsystem.agents`；加载时校验 status_set 非空、contract 兼容、conformance attestation（§11.3）。

#### 5.1.2 Worker 模型（进程边界）
- 每个 task 由编排进程 spawn 独立子进程 worker 执行：注入 ctx → 调 execute → 结果经 IPC 回传。
- 编排层持有 worker 租约（heartbeat）；hard timeout / 取消 = SIGTERM 宽限后 SIGKILL，进程退出映射 `sys.crash` / `sys.timeout`。
- Agent 实例作用域 = 单 task（无跨 task 内存态，setup/teardown 每 task 执行）。凭据类 secret 不注入业务 worker（D8）。

### 5.2 副作用：at-least-once + 效应侧幂等
- **保证等级声明**：框架保证 at-least-once，不承诺 exactly-once。外部效应成功与完成记录落盘之间存在崩溃窗口，关闭窗口的责任在效应侧幂等。
- `side_effect(idem_key, fn)` 为两阶段持久化状态机（Ledger 同库事务）：`claimed(intent) → running → succeeded/failed`；恢复时遇 `running/claimed` 记录 = 状态 unknown，执行 **恢复协议**：优先调用效应类型注册的 `probe()`（查询外部真实状态对账），无 probe 能力的效应标记 unknown 并转 sys.error。
- `idem_key = hash(run_id, node, loop_round, attempt, input_digest)`；`input_digest` = TaskInput 规范化序列化摘要，其中 artifact 引用按 **content digest**（非路径）参与——artifact 不可变性（§7.5）保证重放正确。
- 效应类别要求（contract + conformance 强制）：构建 = 可 probe（worktree/产物存在性）；刷板/板上执行 = 可 probe 或声明可安全重放；**发布 = 仅经 broker，broker 端远端幂等（push 前查远端状态）+ token 单次核销双保险**。

### 5.3 trace 与 token 记账
- SDK 自动埋点（task 起止、LLM 调用、工具调用、artifact 读写）写 Ledger；`trace.jsonl` 为 Ledger 派生的追加安全格式（每行一事件），供人读与外部工具消费。
- token budget：按节点在 pipeline YAML 配置（`llm_budget:`），超限策略由 Context 管理执行（§7.3）。
- 落盘前统一脱敏：secret/token 只记指纹（§8.4）。

---

## 6. Contract 体系概览（精确 schema 见 01_Contract_Spec）

### 6.1 消息类型
`TaskInput` / `HandoffResult` / 各 Report（Build/UT/Bench/Review/Feedback，均携带 series_id 与产出 task_id）/ `RunContext` / `ReleasePlan` / `ReleaseManifest` / Approval 决定与 token / Skill 协议消息。agent_type 注册信息含 status 全集与 hard-required 上游声明。

### 6.2 版本规则
Contract 独立版本号；Agent 以 PEP 440 specifier 声明兼容区间（§5.1.1）；框架装配时校验。pipeline `dsl_version` 属 Contract 版本体系。draft 期允许破坏性修改但记 decision_log。

### 6.3 上游缺失语义
默认全部 optional + 降级运行 + 报告显式标注"本次 Run 未执行 X"；Agent contract 可声明**少数 hard-required** 上游产物（如 benchmark hard-require 构建产物引用），由 DSL 校验器静态拦截（§4.2.6）。approval_token 属"外部供给依赖"类别，不参与上游产物校验。conformance 含上游缺失用例。

### 6.4 Patch 归属与陈旧性
产物为 patch series（非 squash），逐段标注产出者与动因；series 任何变更 → 新 series_id + 新 tree_digest → 旧 Report 对 gate/join 失效（§4.2.4）、未核销 token 失效（§8.2）。是否 squash 是 broker 发布期可配置行为。

### 6.5 Skill 协议（决策定案）
- 传输：**HTTP + JSON 单一协议**（MCP 若需要，未来以 adapter 包装同一操作 contract，MVP 不做）。
- 操作：`create_run(pipeline_id, target_spec)`（target_spec 指定 snapshot 拉取范围：仓/包/manifest，语义 `[01]`）、`submit_patch(run_id, series)`（unified diff series + 逐 patch 的 repo 归属；服务端校验对 pinned snapshot 可应用，不可应用即拒绝；一个 Run 仅接受一次初始 series，重复提交返回明确错误——修订走新 Run）、`get_status`、`get_result`、`cancel_run`。
- 认证与信任边界：静态 bearer token（配置下发调用方）；请求含 request_id 支持幂等重试；patch 大小/路径白名单校验。信任边界声明：Skill 端点仅暴露于内网单机/受控网段（D13），持 token 者视为受信 Coding Agent。

---

## 7. 公共模块（L1）

### 7.1 LLM 接入层
- Provider 抽象 `complete(messages, policy_ctx) -> LLMResponse`；实现：内网 LLM provider、FakeLLMProvider、可选外部 API provider。
- 数据边界（D7）：密级 ∈ {public, internal_code, build_log, secret} 构成格（lattice）；密级由数据产出组件出生标注并随对象传播，聚合（EvidencePacket/消息/派生摘要/LLM 输出）取成员最高密级，API 不提供降级操作；provider 可接收密级集合由**中心安全配置**授权（非 provider 自报）；每次调用（含 cascade fallback 的每一跳）重新校验，fail-closed。业务侧绕过 SDK 自拼 payload 属残余风险（§14 R8），以 conformance 误标检测 + 约定管理。
- 路由：static binding → rule-based → cascade；cascade 升级判据 = 传输错误/超时/结构化输出校验失败（质量性判据不做，N3）。统一重试/超时/限流/token 记账。

### 7.2 KnowledgeProvider
接口同 v0.1；缓存键策略由 provider capabilities 声明：代码事实类（CodeGraph）键含 snapshot_id + tree_digest，知识库类（Wiki）键不含基线。查询结果出生即带密级（D7）。

### 7.3 Context 管理（四层）
Run 级共享状态（框架，只读注入）；Agent 工作上下文与 token budget（SDK 工具：预算执行、截断/压缩策略）；EvidencePacket 组装（§7.4）;知识注入（带来源与密级）。

### 7.4 EvidencePacket 工具链
结构 facts / negative_facts / log_excerpts / target_source_excerpt / confidence；negative_facts 仅限工具产出的否定性代码事实；**产 patch 请求必含 target_source_excerpt**（有界行数）；校验器含 RawDataDetector 与体积上限；packet 密级 = 成员最高密级。

### 7.5 Ledger、Artifact、trace
- **Ledger（D6）**：单 SQLite（WAL）承载 Run/Task 状态机、artifact 索引、side_effect 状态、循环计数、gate 等待项、approval/token 核销记录、事件流。写者唯一（编排进程；approval/broker 经编排进程 API 写入）。task 完成 = 结果、artifact 索引、幂等记录同一事务提交，消除索引/状态分裂。
- **Artifact**：内容寻址（content digest 即引用组成部分）、写入后不可变；目录 `artifacts/<digest前缀>/...`；保留策略：终态 Run 的大体积构建日志类保留 N 天（配置，默认 14）后清理，patch/report/trace 永久保留。
- **trace.jsonl**：由 Ledger 事件流派生，追加安全；崩溃不影响权威源。

### 7.6 资源管理
#### 7.6.1 BuildExecutor
`build(snapshot, series, targets) -> BuildResult`；默认 `GbsLocalExecutor`：per-task git worktree 隔离、`git apply --index` + staged/worktree 一致性校验、构建可 probe（§5.2）；依赖范围默认 reverse-dependency 闭包增量，全量为显式开关。
#### 7.6.2 多仓 snapshot manifest
snapshot = `[ {repo_id, remote, commit, path} ]` 规范化清单；patch 逐条声明 repo_id；跨仓 series 按 manifest 序应用，任一仓失败即整体回滚该 worktree 组；tree_digest = 各仓应用后 tree hash 的规范组合（算法 `[01]`）。
#### 7.6.3 资源额度（单机自我保护）
BuildExecutor / BoardPool / worker 数各配信号量上限；排队 FIFO；磁盘水位检查（低于阈值拒绝新 Run 并告警）；worktree 于 task 终结时清理，泄漏由定期对账回收。

---

## 8. 安全

### 8.1 信任模型（D13）
内网单机、单操作员运维；Skill 调用方经 bearer token 认证、视为受信；**patch 与其触发的构建脚本视为半可信**——不做完整容器沙箱（N7），控制面为：凭据物理隔离于 broker（8.3）、能力句柄按授权注入（5.1.1）、worker 子进程可强杀、发布必经 token。残余风险（恶意构建脚本网络外传源码等）登记 §14 R7，由内网环境与来源受信假设覆盖；该假设失效（如接入不受信来源）时必须先补沙箱。

### 8.2 Approval 服务（框架交付）
- 独立进程 + **Review CLI**（MVP 形态；§9 Web 视图保持只读，不承担审批）。
- reviewer 经 CLI 认证（本机用户 + 服务端配置的 reviewer 名单）提交 approve/reject；approve 时服务生成 release manifest（snapshot、tree_digest、发布目标、pipeline_digest、exec_manifest_digest）、签发绑定其 digest 的一次性 token（含过期时间）、写 Ledger 并触发 gate resume。
- series 变化 / Run 关闭 → 未核销 token 自动失效。签发密钥仅存于 approval 服务；broker 以共享密钥（MVP，HMAC）验证签发真实性。

### 8.3 Release broker（框架交付）
- 独立进程，唯一持有发布凭据；输入 ReleasePlan + token。
- 原子 compare-and-consume：Ledger 事务内校验 token（有效、未核销、digest 与当前 Run 的 release manifest 完全一致）并标记核销；核销记录绑定 task_id——**broker task 中断恢复时，"已核销给本 task"视为有效**，消除恢复死锁。
- 执行发布前重核 manifest（防核销后内容漂移），远端幂等（push 前查远端状态）；发布 adapter 插件化（FakePublisher 随框架交付，gerrit/github adapter 属 CI 业务侧按 broker 插件接口实现，运行于 broker 进程内、经 broker 插件准入）。

### 8.4 脱敏与审计访问
持久化统一脱敏：token/凭据/secret 只记指纹；LLM prompt/响应 artifact 带密级标签；Web 视图只读 + 本机访问；审计记录保留策略随 §7.5。

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
│   ├── orchestration/     # DSL 解析/校验、Run 生命周期、循环预算、outcome、worker 调度
│   ├── sdk/               # AgentBase、worker 入口、side_effect、trace、ctx
│   ├── contracts/         # pydantic schema + 版本校验
│   ├── llm/               # provider、fake、数据边界、路由
│   ├── knowledge/         # KnowledgeProvider + CodeGraph/Wiki 实现 + 缓存
│   ├── context/
│   ├── evidence/
│   ├── ledger/            # SQLite 权威源 + artifact store + trace 派生
│   ├── resources/         # BuildExecutor(GbsLocal)、BoardPool 接口/Fake、额度管理
│   ├── approval/          # Approval 服务 + Review CLI
│   ├── release/           # Release broker + FakePublisher + 插件接口
│   └── skill/             # Skill HTTP server
├── agents/
│   ├── skeletons/         # 五类 agent 可运行空壳 + producer/consumer fixtures
│   └── compiler/          # reference agent（P5 起）
├── conformance/           # 合规套件 + engine conformance + 本地 harness
├── pipelines/             # full_migration.yaml、compiler_bench_only.yaml 等
├── docs/                  # 00–09、reviews/、dev_memory 说明
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
DSL property/fuzz（随机图 → 校验器判定性质：可达环必有 budget、release 必经 hitl 等）；状态机 model-based 测试；**逐持久化边界故障注入**（每个 Ledger 提交点前后 kill，验证恢复与对账）；token 并发双消费测试；陈旧 series 进 gate/join 拒绝测试；checkpoint/execution manifest 不匹配拒绝恢复测试；artifact 损坏检测（digest 校验）；五类 agent_type 的 contract producer/consumer fixture 兼容测试。conformance attestation：结果绑定 agent 制品 digest + contract/套件版本，digest 变更即失效，加载时校验。

---

## 12. 环境前提与 E0 预检
同 v0.1 表（gbs 工具链 / image URL / gerrit 探测 / CodeGraph / LLM Wiki / FakeLLM），追加：Approval 服务与 broker 无外部环境依赖（本机进程），不进预检。

---

## 13. 分期计划概览（细化见 09）

| Phase | 交付 | 完成 gate |
|-------|------|----------|
| P0 | 00/01 复审通过 draft freeze；08/09 就绪 | 三方 unanimous GO |
| P1 | EnginePort + engine/ + DSL v1 校验器/编译器 + Run 状态机 + Ledger 核心 + worker 调度 | mock agents：全量/子集配置加载；逐边界故障注入恢复通过 |
| P2 | SDK（worker/side_effect）+ contracts + Skill server + **Approval 服务 + Review CLI + Release broker(FakePublisher)** | conformance 骨架 + token 并发/双消费测试通过 |
| P3 | 公共模块（LLM 层+数据边界、Knowledge 双实现联调、context、evidence、GbsLocalExecutor、FakeBoardPool、资源额度） | 真实 gbs 最小构建 + 数据边界 fail-closed 用例通过 |
| P4 | 端到端：全量与子集 pipeline（mock 业务 + 真实构建 + CLI 审批 + Fake 发布） | §11.3 全部测试类别通过 = 框架完成 |
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

---

## 15. 附录
- A1 术语表：§3。
- A2 `[待补充]`：gbs.conf、gerrit 探测方式、内网 LLM 接口规格、CodeGraph/LLM Wiki 仓库地址。
- A3 引用：01/07/08/09（待产出）；docs/reviews/HLD_v0.1_review_disposition.md。
- A4 v0.1→v0.2 变更摘要：DSL v1 完整语义（显式节点/join/loops/穷尽路由/保留节点/合法子集定义）；Approval 服务与 Release broker 纳入框架交付并修复 token 时序矛盾；at-least-once 语义显式化 + 两阶段 side_effect + 恢复协议；Ledger 单一权威源；execution manifest（D12）；多仓 snapshot manifest；worker 进程模型；数据边界来源标注；信任模型显式化（D13/N7）；并发模型（D11）;测试类别强制（§11.3）;风险表扩充；全部交叉引用修正。
