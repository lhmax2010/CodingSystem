# 00 — Multi-Agent Framework 高层设计（HLD）

**版本**: v0.1 Draft（待三方 cross-review 后 draft freeze）
**状态**: 评审中
**读者**: 框架开发（Codex）、cross-reviewer（Claude / ChatGPT / Kimi）、后续业务 Agent 开发者
**关联文档**: 01_Contract_Spec、02–06_Agent_Design_Guide、07_Conformance_and_Onboarding、08_Codex_Dev_Guide、09_Phased_Dev_Plan

> **文档定位**：本文档按"Codex 可直接开发"标准编写——关键路径上的技术决策均已定案，不提供备选方案。凡标注 `[待补充]` 的内容为环境类事实材料（由项目负责人核对后填充），不阻塞架构评审；凡标注 `[E0 预检]` 的内容需在开工前通过环境探测确认。

---

## 1. 背景与目标

### 1.1 背景

本框架服务于 Tizen 平台工程的自动化软件工程流水线（CodingSystem 重启版）。完整目标态为六角色协作：外部 Coding Agent（ClineSR / 过渡期 Codex）产出业务 patch，框架内的 Compiler / UT / Benchmark / Review / CI 五类 Agent 完成编译修复、单测验证、性能基准、AI+人工审查、发布。

与旧版 CodingSystem 的关键差异：

1. **Coding Agent 移出框架**——仅通过 Skill 协议调用流水线，框架对其零依赖；
2. **框架平台化**——本团队只交付框架 + 公共模块 + reference agent；业务 Agent（UT / Benchmark / Review / CI）由业务开发者依据 02–06 设计指引二次开发；
3. **流水线可配置**——支持子集编排（如仅 Compiler + Benchmark），不改代码只改配置。

### 1.2 目标（Goals）

- G1 提供声明式可配置的 pipeline 编排：全量六步或任意合法子集，配置文件驱动；
- G2 提供 Agent SDK：业务开发者面向 SDK 编程，不接触编排引擎内部；
- G3 提供公共模块：LLM 接入层、知识源接入（CodeGraph / LLM Wiki）、Context 管理、EvidencePacket 工具链、Artifact store、资源管理接口；
- G4 全流程可追溯、可断点恢复、可幂等重放；
- G5 HITL 与发布安全物理强制（approval token）；
- G6 以 Compiler Agent 作为 reference agent 验证全部 contract 后，contract 定稿 v1.0。

### 1.3 非目标（Non-goals）

以下明确不做，评审时不接受向此方向扩展的建议：

- N1 分布式多机部署（MVP 单机；build server / 板子池通过接口远程化是实现细节，不是框架的分布式化）；
- N2 多租户与配额系统；
- N3 学习型 / 强化学习型 LLM 路由（沿用 static binding → rule-based → cascade 三级，见 §8.1）；
- N4 通用工作流引擎（只覆盖本领域 pipeline 形态：有界循环的 DAG + 人工 gate）；
- N5 多语言 SDK（仅 Python）；
- N6 Coding Agent 本体的任何实现（框架只定义 Skill 协议）。

---

## 2. 总体架构

### 2.1 分层视图

```
┌─────────────────────────────────────────────────────────────┐
│  外部世界（框架边界之外）                                      │
│  Coding Agent (ClineSR / Codex)  ── Skill 协议 ──┐           │
│  人工 Reviewer ── Review UI / approval token ────┤           │
└──────────────────────────────────────────────────┼───────────┘
                                                   ▼
┌─────────────────────────────────────────────────────────────┐
│  L4 编排层 Orchestration                                     │
│    Pipeline DSL 解析/校验 → StateGraph 编译 → 执行            │
│    checkpoint / 恢复 / HITL gate / 路由 / 有界循环             │
│    （LangGraph 为内部引擎，硬封装于 framework/engine/）        │
├─────────────────────────────────────────────────────────────┤
│  L3 Agent SDK                                                │
│    AgentBase 生命周期 / 幂等键 / trace 埋点 / token budget     │
│    conformance hooks                                         │
├─────────────────────────────────────────────────────────────┤
│  L2 Contract（独立文档 01，独立版本演进）                      │
│    HandoffResult / 各类 Report schema / RunContext /          │
│    Pipeline DSL 格式 / Skill 协议 / 版本兼容规则               │
├─────────────────────────────────────────────────────────────┤
│  L1 公共模块 Common Modules                                   │
│    LLM 接入层 │ KnowledgeProvider │ Context 管理 │             │
│    EvidencePacket 工具链 │ Artifact store │ 资源管理接口        │
├─────────────────────────────────────────────────────────────┤
│  L0 基础设施 Infra                                            │
│    存储（SQLite/文件）│ 日志 │ 配置 │ 进程管理                  │
└─────────────────────────────────────────────────────────────┘
        ▲ 以插件形式接入（业务侧二次开发，不在框架仓库交付范围）
┌───────┴─────────────────────────────────────────────────────┐
│  业务 Agent：Compiler(reference，本团队交付) / UT / Benchmark  │
│  / Review / CI —— 均继承 SDK AgentBase，通过 conformance 准入  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心架构决策一览

| # | 决策 | 结论 | 理由摘要 |
|---|------|------|---------|
| D1 | 编排引擎 | LangGraph 1.2.x（钉精确版本），硬封装 | checkpoint/HITL/条件路由为其 1.0 核心能力且 API 已稳定（semver、2.0 前无破坏性变更）；封装保证可撤换 |
| D2 | 路由权归属 | Agent 只声明结果（HandoffResult），路由由编排层按 pipeline 配置决定 | 子集流水线的前提；Agent 间互不感知 |
| D3 | 语言/版本 | Python ≥ 3.12 | 实机环境统一 3.12+ |
| D4 | 仓库形态 | 单 monorepo | framework / agents / conformance / docs 同仓，业务团队以包依赖或 fork 使用 |
| D5 | 基线管理 | Run 启动时 pin snapshot，全程锁定 | patch 基线一致性；"拉最新"仅发生在 run 创建时刻 |
| D6 | 审计记录 | trace.json + artifact store 为 system of record；LangGraph checkpoint 仅作执行恢复机制 | 审计不依赖引擎内部格式，引擎可换 |
| D7 | 数据边界 | LLM Provider 声明允许接收的数据类别，框架调用时强制校验 | Tizen 源码/构建日志不得流向未授权 provider |
| D8 | 发布安全 | CI 类节点仅接受携带一次性人工 approval token 的输入 | 物理强制而非流程约定 |
| D9 | 循环上限 | 一切修复循环有次数与总时长上限，超限 fail_safe | spike 已验证模式（max attempts + rebuild 上限） |
| D10 | Contract 冻结 | 两段式：多方评审后 draft freeze；reference Compiler Agent 跑通后 v1.0 | 未被真实 Agent 消费过的 contract 不定稿 |

### 2.3 与外部系统的关系

| 外部系统 | 关系 | Codex 开发期处理方式 |
|---------|------|---------------------|
| Coding Agent (ClineSR/Codex) | 框架外，经 Skill 协议调用 | 框架侧实现 Skill server 端 + 模拟客户端用于测试 |
| CodeGraph | 公共模块以 provider 形式接入 | 开源仓库本地 clone 部署，真实联调 |
| LLM Wiki | 同上 | 同上 |
| 内网 LLM | LLM 接入层的一个 provider | 不可达；以 FakeLLMProvider（fixture 驱动）替代，接口与真实 provider 一致 |
| build server (GBS) | BuildExecutor 接口的默认实现 | 本机真实 gbs 编译（gbs.conf 由负责人提供，image URL 与依赖包可达）`[E0 预检]` |
| Tizen 源码 (gerrit) | Run 创建时 snapshot 拉取 | gerrit 可达性待探测 `[E0 预检]`；不可达则退化为负责人提供源码包的 fixture 模式 |
| UT 测试板 | BoardPool 接口（框架只定义接口） | FakeBoardPool 供测试；真实实现属 UT Agent 业务侧 |
| gerrit/github 发布 | CI Agent 业务实现 | 框架不实现，仅在 contract 中定义发布输入（含 approval token） |

---

## 3. 核心概念与术语

| 术语 | 定义 |
|------|------|
| **Run** | 一次完整的 pipeline 执行实例。`run_id` 全局唯一；因人工 reject 后重新提交产生的新 Run 通过 `parent_run_id` 成链 |
| **Snapshot** | Run 创建时刻锁定的代码基线：manifest / commit set 的不可变引用，`snapshot_id` 标识。Run 全程不更新基线 |
| **Pipeline** | 一份声明式 YAML 配置：节点（Agent 类型）、路由（结果 → 下一节点）、gate（HITL / 阈值）、循环上限。合法性由 DSL 校验器静态检查 |
| **Agent** | 继承 SDK `AgentBase` 的执行单元，输入 `TaskInput`，输出 `HandoffResult`。不感知其他 Agent 的存在 |
| **HandoffResult** | Agent 完成后的结构化产出：`status`（如 build_passed / build_failed_exhausted / ut_failed）、产物引用、reason。**取代旧设计的 HandoffRequest**——不含 target 字段，路由权在编排层 |
| **Gate** | 流水线上的暂停点。类型：`hitl`（等待人工，经 approval token 恢复）、`threshold`（数值阈值自动判定，如性能回归超限） |
| **Task** | 一个 Agent 的一次执行，`task_id` 形如 `CMP-000123`，`parent_task_id` 串联因果链 |
| **Artifact** | Task 产物（patch / report / log 摘要），统一由 Artifact store 管理，以 `artifact_ref` 在消息中引用，消息体不内嵌大对象 |
| **EvidencePacket** | 提交给 LLM 的结构化证据包：facts / negative_facts / 日志摘录 / 目标源码摘录 / 置信度。构建与校验由框架工具链完成（§8.4） |
| **Skill 协议** | 外部 Coding Agent 与框架的唯一交互协议：创建 Run（获取 snapshot）、提交 patch、查询状态、获取最终产物与报告。传输为纯 MCP / HTTP + 文件，禁止依赖任何特定 Coding Agent 的私有能力 |
| **approval token** | 人工 review 通过后由 Review UI 签发的一次性令牌，绑定具体 patch series hash 与 run_id；CI 类节点的输入 contract 强制要求 |
| **fail_safe** | 循环超限或不可恢复错误时的终态：停止流水线、汇总全部证据生成 FeedbackReport、等待人工处置 |

---

## 4. 编排层设计（L4）

### 4.1 引擎选型与封装边界

- 引擎：**LangGraph**，requirements 钉精确版本（开工日取最新 1.2.x，如 `langgraph==1.2.11`）。升级为框架团队专属事件，须过完整回归。
- **硬封装规则（物理强制）**：仓库内仅 `framework/engine/` 允许 `import langgraph`，以 import-linter contract + ruff 规则在 CI 中强制。LangGraph 的任何类型（StateGraph、Command、Checkpointer 等）不得出现在 SDK 公开 API、Contract schema、业务 Agent 代码中。
- 可撤换性：因硬封装，替换引擎只需重写 `framework/engine/`，不触及 Agent 与 Contract。

### 4.2 Pipeline DSL

声明式 YAML，示例（全量流水线，节选）：

```yaml
pipeline: full_migration
version: 1
snapshot_policy: pin_at_start
nodes:
  compiler:
    agent_type: compiler
    loop_limits: { max_patch_attempts: 2, max_rebuilds: 1, max_wall_clock_min: 240 }
  ut:
    agent_type: ut
    loop_limits: { max_fix_rounds: 2, max_wall_clock_min: 180 }
  benchmark:
    agent_type: benchmark
  review_ai:
    agent_type: review
  human_review:
    gate: hitl
  ci:
    agent_type: ci
    requires: [approval_token]
routes:
  - { from: compiler, on: build_passed, to: [ut, review_ai.static] }   # 静态审查与 UT 并行
  - { from: compiler, on: build_failed_exhausted, to: fail_safe }
  - { from: ut, on: ut_passed, to: benchmark }
  - { from: ut, on: ut_fix_patch_ready, to: compiler }                 # 有界回流
  - { from: benchmark, on: bench_done, to: review_ai.final }
  - { from: review_ai, on: review_report_ready, to: human_review }
  - { from: human_review, on: approved, to: ci }
  - { from: human_review, on: rejected, to: feedback_report }
```

子集流水线（如 Compiler + Benchmark）为另一份 YAML，不改任何代码。

**DSL 静态校验器**在 Run 创建前检查：节点的 agent_type 已注册且过 conformance；路由无悬空；每个循环边所在环有 loop_limits；CI 类节点必有 `requires: [approval_token]`（缺失即拒绝加载——D8 的第一道物理强制）；下游节点声明的输入依赖若在本 pipeline 中不存在，则必须被该 Agent 的 contract 标记为 optional（§6.3）。

### 4.3 Run 生命周期与状态

```
created → snapshot_pinned → running ⇄ paused(gate) → succeeded
                                   ↘ fail_safe → closed(feedback_report)
                                   ↘ cancelled
```

- **创建**：Skill 调用 `create_run(pipeline_id)` → 框架拉取最新代码、生成 snapshot、返回 `run_id + snapshot_id + snapshot 引用`；Coding Agent 基于该 snapshot 产 patch 后 `submit_patch(run_id, patch)` 触发执行。
- **恢复**：进程中断后由 checkpoint 恢复到最近一致状态。副作用防重不依赖引擎：SDK 层幂等键（§5.2）保证"同一 task 的编译不会重复触发"。
- **重入**：人工 reject → Run 终态 closed + FeedbackReport；开发者修复后创建新 Run，`parent_run_id` 指向旧 Run，报告链可追溯。

### 4.4 HITL 与 gate

- `hitl` gate 映射到引擎的 interrupt/resume 机制，但恢复凭据是框架自己的 approval token（一次性、绑定 run_id + patch series hash、由 Review UI 签发、服务端校验后作废）。
- `threshold` gate 由纯代码判定（如 benchmark 回归超阈值 → 转 fail_safe 或降级路由），LLM 不在判定路径上。

### 4.5 循环与终止保证

每条回流边（如 ut → compiler）必须隶属于一个带 `loop_limits` 的环。编排层维护环计数器，超限强制路由至 fail_safe。fail_safe 节点为框架内置：聚合本 Run 全部 artifact（各轮 patch、报错、分析、测试结果、AI review 意见）生成 FeedbackReport。

---

## 5. Agent SDK（L3）

### 5.1 AgentBase 生命周期

```python
class AgentBase(ABC):
    agent_type: ClassVar[str]
    contract_version: ClassVar[str]

    def setup(self, ctx: RunContext) -> None: ...          # 资源/依赖检查，失败即 task 不启动
    @abstractmethod
    def execute(self, task: TaskInput) -> HandoffResult: ...
    def teardown(self) -> None: ...
    def health(self) -> HealthStatus: ...
```

- Agent 通过 `ctx` 获得：artifact store 句柄、KnowledgeProvider、LLM client（已套数据边界策略）、EvidencePacket builder、trace 记录器。**Agent 不直接持有引擎、其他 Agent、或全局配置的引用。**
- 注册机制：entry-point 插件注册 `agent_type → class`，框架启动时加载并校验 contract_version 兼容。

### 5.2 幂等与副作用

- 每个 Task 分配幂等键 `idem_key = hash(run_id, node, loop_round, input_digest)`；SDK 提供 `side_effect(idem_key, fn)` 包装器，重放/恢复时命中已完成记录则跳过执行直接返回既有结果。编译、刷板、发布等昂贵或不可逆操作**必须**经此包装（conformance 检查项）。
- Task 输出仅经 HandoffResult + artifact store 落盘，不允许带内存态跨 task。

### 5.3 trace 与 token 记账

- SDK 自动埋点：task 起止、LLM 调用（provider/模型/输入输出 token/耗时）、工具调用、artifact 读写，写入 `trace.json`（schema 见 01）。
- token budget：每 task 可配置预算，超限告警/截断策略由 Context 管理提供（§8.3）。

---

## 6. Contract 体系概览（详细 schema 见 01_Contract_Spec）

### 6.1 消息类型

- `TaskInput` / `HandoffResult`（含 status 枚举、artifact_refs、reason、metrics 摘要）
- 各类 Report：`BuildReport` / `UTReport` / `BenchReport` / `ReviewReport` / `FeedbackReport`
- `RunContext`（run_id、snapshot、pipeline 摘要、artifact 索引）
- Skill 协议消息（create_run / submit_patch / get_status / get_result）

### 6.2 版本规则

- Contract 独立版本号；Agent 声明兼容区间；框架装配时校验，不兼容拒绝启动。
- draft freeze（多方评审通过）→ v1.0（reference Compiler Agent 完整消费后）。draft 期允许破坏性修改但须记 decision_log。

### 6.3 上游缺失语义（子集流水线的关键约定）

所有 Report 的下游消费字段一律 optional；Agent 对缺失上游必须降级运行而非报错（如 Review Agent 在无 UTReport 时照常审查并在报告显式标注"本次 Run 未执行 UT"）。conformance 套件包含"上游缺失"用例。

### 6.4 Patch 归属与形态

流水线产物为 **patch series**（非 squash）：Coding Agent 原始 patch + 各 Agent 各轮修复 patch，逐段标注产出者（agent_type + task_id + 轮次）与动因。人工 review 面对的是带完整出处的 series；是否 squash 是 CI Agent 发布期的可配置行为。

---

## 7. 公共模块（L1）

### 7.1 LLM 接入层

- Provider 抽象：`complete(messages, policy_ctx) -> LLMResponse`；实现包括内网 LLM provider（生产）、FakeLLMProvider（fixture 驱动，Codex 开发与 CI 测试用）、可选外部 API provider。
- **数据边界策略（D7）**：每个 provider 声明 `accepted_data_classes`（如 `public` / `internal_code` / `build_log`）；每次调用由 SDK 标注 payload 数据类别，框架校验不通过即拒绝调用并记审计。策略为配置文件，默认拒绝。
- 路由：static binding（按 agent/用途配置模型）→ rule-based（按任务特征）→ cascade（低成本先行，失败升级）。不做学习型路由（N3）。
- 统一重试/超时/限流/token 记账。

### 7.2 KnowledgeProvider（知识源抽象）

```python
class KnowledgeProvider(ABC):
    def query(self, q: KnowledgeQuery) -> KnowledgeResult: ...
    def capabilities(self) -> set[str]: ...   # e.g. {"call_graph", "symbol_def", "kb_search"}
```

- 两个官方实现：`CodeGraphProvider`（调用链/符号/引用查询）、`LLMWikiProvider`（知识库检索）。二者均有开源仓库，开发期本地部署真实联调；接口冻结进 01。
- 业务侧可注册自有 provider（扩展点）。查询结果统一走缓存层（run 级缓存，键含 snapshot_id 保证一致性）。

### 7.3 Context 管理（四层拆分）

1. **Run 级共享状态**：snapshot、artifact 索引、pipeline 元信息——框架持有，只读注入 Agent；
2. **Agent 工作上下文**：LLM 会话组装、token budget、截断/压缩策略——SDK 工具，防止上下文膨胀导致注意力稀释；
3. **EvidencePacket 组装**：见 §7.4；
4. **知识注入**：KnowledgeProvider 查询结果的选取与格式化注入，带来源标注。

### 7.4 EvidencePacket 工具链（spike 成果固化）

框架提供 builder + 校验器，将既有经验固化为平台能力：

- 结构：`facts` / `negative_facts` / `log_excerpts` / `target_source_excerpt` / `confidence`；
- **negative_facts 纪律**：仅允许工具产出的否定性代码事实（grep/clangd 查询结果），不得含行为性指导；行为约束进共享 system prompt（三方评审共识，直接沿用）；
- **target_source_excerpt 强制**：凡请求 LLM 产 patch，packet 必含目标文件在当前 worktree 的精确源码摘录（有界行数）——spike 教训：缺失此项导致 LLM 幻觉 patch 上下文；
- 校验器含 RawDataDetector（拦截原始日志直通 LLM）与 packet 体积上限。

### 7.5 Artifact store 与 trace

- 目录约定 `artifacts/<task_id>/{patches,reports,logs}/`，索引入库（SQLite）；消息中只传 `artifact_ref`。
- `trace.json` 每 Run 一份，task 级追加写，含 parent_task_id 因果链。trace + artifact 为审计与回放的唯一事实源（D6）。

### 7.6 资源管理接口

- `BuildExecutor`：`build(snapshot, patches, targets) -> BuildResult`。默认实现 `GbsLocalExecutor`（gbs.conf 注入、**git worktree 隔离**、patch 以 `git apply --index` 应用并校验 staged 与 worktree 一致——spike dirty-worktree 教训的固化、构建产物与日志入 artifact store）。依赖范围：默认按 GBS 依赖图计算 reverse-dependency 闭包增量构建，全量构建为显式开关。
- `BoardPool`：`acquire/release/flash/run_cmd/recover` 接口 + `FakeBoardPool`。真实板池实现属 UT Agent 业务侧（02–06 指引给出实现要求：板卡识别纪律、失败恢复、池化隔离）。

---

## 8. 安全与 HITL

- 发布路径物理强制链：pipeline 校验器拒绝无 `requires: [approval_token]` 的 CI 节点（静态）→ CI 类 Agent 的 TaskInput schema 强制 token 字段（contract）→ 框架在 dispatch 前向 token 服务校验并作废（运行时）。三层缺一不可。
- 权限边界：Agent 进程以最小权限运行；发布凭据仅注入 CI 类 Agent 且经配置显式授权；FakeProvider/测试环境物理上无发布凭据。
- 全部 LLM 决策留证：prompt、EvidencePacket、响应均入 artifact（受数据类别标注管理）。

## 9. 可观测性

- Run 可视化：基于 trace.json 的只读 Web 视图（run 状态、节点进度、循环计数、token 消耗、artifact 浏览）。MVP 为简单本地页面，不引入外部观测平台。
- 指标：run 成功率、各节点耗时分布、循环触发率、fail_safe 率、token 成本——从 trace 离线聚合即可，不建实时指标系统。

## 10. 部署形态与仓库结构

单机部署（N1）。monorepo（D4）：

```
coding-system/
├── framework/
│   ├── engine/            # 唯一允许 import langgraph 的模块
│   ├── orchestration/     # DSL 解析/校验、Run 生命周期、gate、fail_safe
│   ├── sdk/               # AgentBase、幂等、trace、ctx
│   ├── contracts/         # schema（pydantic）+ 版本校验
│   ├── llm/               # provider 抽象、fake、数据边界策略、路由
│   ├── knowledge/         # KnowledgeProvider、CodeGraph/Wiki 实现、缓存
│   ├── context/           # 四层 context 工具
│   ├── evidence/          # EvidencePacket builder/validator
│   ├── artifacts/         # store + trace
│   ├── resources/         # BuildExecutor、BoardPool 接口与默认/Fake 实现
│   └── skill/             # Skill 协议 server 端
├── agents/
│   ├── skeletons/         # 各 agent_type 可运行空壳
│   └── compiler/          # reference agent（Phase 5 起）
├── conformance/           # 合规测试套件 + 本地 harness（mock orchestrator/replay/golden）
├── pipelines/             # 示例与内置 pipeline YAML
├── docs/                  # 00–09 + dev_memory/
└── ci/
```

## 11. 技术栈与质量门禁

- Python **≥ 3.12**；LangGraph 1.2.x 钉精确版本；pydantic v2；SQLite；PyYAML。
- 门禁（CI 强制）：pytest + coverage ≥ 80%、mypy `--strict`、ruff、import-linter（引擎封装规则）。
- 开发纪律沿用 08_Codex_Dev_Guide：dev_memory 机制、每 Phase 行数上限、PR 必附单测 + self-review + 外部 AI review、开工前 reverse-review 文档。

## 12. 环境前提与 E0 预检

开工前 Codex 须执行并记录 E0 预检（清单进 09）：

| 项 | 验证方式 | 失败降级 |
|----|---------|---------|
| gbs 工具链可用 | `gbs --version`、以 gbs.conf 构建一个最小样例包 | 阻塞项，须解决 |
| image URL / 依赖包可达 | gbs 拉取依赖成功 | 阻塞项 |
| gerrit 源码可达 | 负责人提供探测方式，clone 指定测试仓验证 | 降级为负责人提供源码包（fixture snapshot 模式） |
| CodeGraph 本地部署 | clone 开源仓库、启动、跑通冒烟查询 | 阻塞项 |
| LLM Wiki 本地部署 | 同上 | 阻塞项 |
| 内网 LLM | 不可达（既定） | FakeLLMProvider（既定方案，非降级） |

## 13. 分期计划概览（细化见 09_Phased_Dev_Plan）

| Phase | 交付 | 完成 gate |
|-------|------|----------|
| P0 | 00/01 评审通过 draft freeze；08/09 就绪 | 三方 unanimous-pass |
| P1 | engine 封装 + DSL 校验器/编译器 + Run 生命周期 + checkpoint 恢复 | mock agents 下：中断恢复无重复副作用（kill 实测） |
| P2 | SDK + contracts + artifact/trace + Skill server | conformance 骨架可跑 |
| P3 | 公共模块（LLM 层含 fake 与数据边界、Knowledge 双实现真实联调、context、evidence、GbsLocalExecutor、FakeBoardPool） | 真实 gbs 最小构建通过 |
| P4 | 全量与子集两种 pipeline 配置端到端（mock 业务逻辑 + 真实构建） | 框架完成 gate |
| P5+ | reference Compiler Agent 设计/开发/校验（02 文档驱动） | contract v1.0 定稿 |

## 14. 风险与开放问题

| # | 风险/问题 | 应对 |
|---|----------|------|
| R1 | gerrit 可达性未知 | E0 探测；fixture snapshot 降级路径已定义 |
| R2 | LangGraph 恢复语义与幂等假设不符 | P1 gate 实测（kill/恢复）；不符则在 SDK 幂等层加严，极端情况触发引擎替换（封装保底） |
| R3 | 框架先行、contract 脱离真实业务 | reference Compiler Agent 强制消费全部 contract 后才 v1.0（D10） |
| R4 | 真实 gbs 构建耗时拖慢 Codex 迭代 | 分层测试：单测/conformance 全走 fake；真实构建仅 P3/P4 gate 与 nightly |
| R5 | 内网 LLM 接口与 Fake 假设不一致 | 内网 provider 上线时由负责人在内网跑 provider 一致性测试（07 提供用例） |
| R6 | 二次开发者绕过 conformance 直连引擎 | import-linter + 插件注册强制 conformance 通过记录 |

## 15. 附录

- A1 术语表：见 §3。
- A2 `[待补充]` 清单：gbs.conf 内容、gerrit 探测方式、内网 LLM 接口规格（provider 一致性测试用）、CodeGraph / LLM Wiki 仓库地址与部署说明链接。
- A3 引用：01_Contract_Spec（待产出）、07_Conformance_and_Onboarding（待产出）、08_Codex_Dev_Guide（沿用现有 SOP 改造）、09_Phased_Dev_Plan（待产出）、旧版设计文档（02_Compiler_Agent_v5.1 等，仅作历史参考，冲突处以本文档为准）。
