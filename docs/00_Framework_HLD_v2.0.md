# 00 — Multi-Agent Framework 高层设计（HLD）

**版本**: v2.0（最终版 HLD）——在 v1.0-draft-frozen（含勘误 E-01）基础上的范围扩展版
**状态**: 最终版，用于与总部的方案对齐；对齐后即作为开发基线。**v1.0 已冻结的核心语义（编排、Ledger、效应幂等、审批与发布、特权 IPC、安全模型）原样保留，未作任何放宽**；本版新增内容集中在：构建两阶段（RPM → 镜像）与可插拔构建后端、Compiler Agent 以 LogAnalyzer 为分析引擎、可配置 Benchmark、优化 Agent（AutoFDO / BOLT / CompilerGym 类 / MLGO）、板子池、基线镜像缓存、即插即用的显式保证、源码接入抽象（Tizen 先行、VD 后接）、部署与网络边界。新增部分的变更清单见附录 A16
**读者**: 总部方案评审方、框架开发（Codex）、cross-reviewer（Kimi / Codex / Claude Code）、提供测试用例与知识库内容的业务部门
**关联文档**: 01_Contract_Spec（v0.11，需按本版范围同步扩展，见附录 B 第 7 组）、02–06_Agent_Design_Guide、07_Conformance_and_Onboarding、08_Codex_Dev_Guide、09_Phased_Dev_Plan、docs/review/ 下 v0.1–v0.11 全部十一轮处置表

> **文档定位**：本文档按"Codex 可直接开发"标准编写——关键路径上的技术决策均已定案，不提供备选方案。凡标注 `[待补充]` 的内容为环境类事实材料（由项目负责人核对后填充），不阻塞架构评审；凡标注 `[01]` 的内容为已定案、精确 schema 在 01_Contract_Spec 给出的项。

---

## 1. 背景与目标

### 1.1 背景

本框架服务于 Tizen 平台工程的自动化软件工程流水线（CodingSystem 重启版）。完整目标态为七角色协作：外部 Coding Agent（ClineSR / 过渡期 Codex）产出业务 patch，框架内的六类 Agent 依次完成：

| Agent | 一句话职责 |
|-------|-----------|
| **Compiler** | 以 LogAnalyzer 为分析引擎，先本地编译受影响的 RPM 并自动修复编译问题，通过后经本地全量构建 + mic 或 Quickbuild 出镜像 |
| **UT** | 在板子池分配的测试板上刷入镜像、执行UT 测试，失败时产出修复 patch 回流编译 |
| **Benchmark** | 可配置的性能/内存基准：内置套件、开发者脚本、或由开发者描述用例后自动生成脚本；与基线镜像做 A/B 对比，并可顺带采集 profile 数据 |
| **Optimization** | 依据 Benchmark 结果与 profile 数据做编译优化（AutoFDO、BOLT、CompilerGym 类选项/pass 搜索、MLGO 策略），优化产物必须回流重新编译、重新验证 |
| **Review** | AI 汇总审查（静态审查 + 汇总全部报告），为人工审批提供证据链 |
| **CI** | 生成发布计划；人工批准后由框架的发布组件执行（业务 Agent 不持有发布凭据） |

与旧版 CodingSystem 的关键差异：

1. **Coding Agent 移出框架**——Coding Agent 中安装框架提供的 Skill，由 Skill 调用框架的 MCP 服务来启动流水线、提交 patch、获取结果；框架对 Coding Agent 零依赖；
2. **框架平台化**——本团队开发：框架 + 公共模块 + **approval 服务、release broker 及官方发布 adapter（gerrit/github，见 §8.3）** + **外部构建网关（Build Gateway，§8.6）、板子池（§7.7）、基线镜像缓存与 Profile 库（§7.8）** + **全部六类 Agent**（Compiler 以 LogAnalyzer 为分析引擎；Benchmark 套件可配置；Optimization；UT；Review；CI）；业务部门提供的是业务内容而非 Agent 代码：UT 测试用例、外接性能测试用例、Review 外接知识库内容（分工见 §2.5）；
3. **流水线可配置、Agent 即插即用**——流水线组成完全由 YAML 声明；任一业务 Agent 可增删替换而不改框架代码，删掉后由静态校验器保证剩余流水线仍合法（§2.4）；
4. **两阶段构建**——先在本地增量编译受影响的 RPM（快、可反复修复），通过后再出完整镜像（本地全量构建 + mic，或 Quickbuild），UT 与 Benchmark 均在镜像上执行；
5. **测量—优化闭环**——Benchmark 不止于报告，结果驱动 Optimization Agent 产生优化，优化必须回流经编译、UT、Benchmark 重新证明收益后才进入人工审批；
6. **源码接入可扩展**——首期接入 Tizen（git / gerrit），VD（Perforce + Cosmos）以适配层后接，框架核心不改。

### 1.2 目标（Goals）

- G1 声明式可配置 pipeline 编排：全量或任意**合法**子集（合法性定义见 §4.2.6），配置驱动；
- G2 Agent SDK：Agent 开发者（本团队及将来的其他团队）面向 SDK 编程，不接触编排引擎内部；
- G3 公共模块：LLM 接入层、知识源接入、Context 管理、EvidencePacket 工具链、Ledger/Artifact store、资源管理接口；
- G4 全流程可追溯、可断点恢复；副作用语义为 **at-least-once + 效应侧幂等**（§5.2），不承诺 exactly-once；
- G5 发布安全物理强制：凭据仅存在于框架 release broker 进程，approval token 原子单次核销（§8）；
- G6 contract v1.0 定稿 gate：Compiler Agent 真实消费 + 六类 Agent 的 producer/consumer fixture 全部通过 + 兼容矩阵建立（§13 P5）。基于 FakeLLMProvider 达成；内网真实 LLM 的 provider 一致性验证为独立的上线 gate（§14 R5）；
- G7 **即插即用**：业务 Agent 以插件形式安装/卸载，流水线以 YAML 组合；删除任一业务 Agent 不影响框架与其余 Agent 的运行，合法性由静态校验器保证（§2.4）；
- G8 **构建后端可插拔**：同一 Compiler Agent 支持本地构建（GBS 增量 RPM、GBS 全量 + mic 镜像）与 Quickbuild 远程构建，由节点配置选择（§7.6）；
- G9 **Benchmark 可配置**：基准套件来源三种（内置套件 / 开发者脚本 / 开发者描述用例自动生成脚本），结果统一格式、测量科学可复现（§7A.3）；
- G11 **AI 接入职责明确、判定与 AI 分离**：每个 Agent 的 AI 能力有明确分工（§7A.0）；是否达标、是否回归由 SPEC 与统计规则判定，AI 负责分析、生成与建议，AI 分析先经试点验证再推广；
- G10 **测量—优化闭环**：优化手段以插件注册（AutoFDO、BOLT、CompilerGym 类搜索、MLGO 策略），优化产物强制回流重新验证，收益须经 A/B 证明（§7A.4）。

### 1.3 非目标（Non-goals）

- N1 分布式多机部署（MVP 单机；单机自我保护不豁免，见 §7.6.3 资源额度）；
- N2 多租户与配额系统；
- N3 学习型 LLM 路由（沿用 static → rule → cascade，见 §7.1）；
- N4 通用工作流引擎（只覆盖本领域 pipeline 形态：显式声明的有界循环 DAG + gate）；
- N5 多语言 SDK（仅 Python）；
- N6 Coding Agent 本体实现（框架只提供 MCP 服务与配套 Skill）；
- N7 完整容器级安全沙箱（信任模型与残余风险见 §8.1、§14 R7；凭据隔离不在此豁免范围，由 broker 进程隔离保证）；
- N8 VD 产品线（Perforce 源码 + Cosmos 构建）不在第一阶段范围：第一阶段基于 Tizen Public 代码（git/gerrit + 本地构建/Quickbuild）开发与验证，第二阶段再基于 VD 代码适配修正（SourceProvider 与构建后端适配层，§7.6.4、§13 P8）；
- N9 Quickbuild 远程构建视为外部服务，框架只作为其客户端，不构成 N1 意义上的分布式部署。

---

## 2. 总体架构

### 2.1 分层视图

```
┌────────────────────────────────────────────────────────────────────┐
│  外部世界（框架边界之外）                                             │
│  Coding Agent (ClineSR/Codex) ── Skill → MCP 服务 ────────┐          │
│  开发者 ── Benchmark 用例/脚本、优化专项触发（Skill / CLI）┤          │
│  人工 Reviewer ── Review CLI → Approval 服务 ─────────────┤          │
│  运维 ── Quickbuild SSO 登录（浏览器弹窗，Build Gateway 持有会话）     │
└──────────────────────────────────────────────────────────┼──────────┘
                                                           ▼
┌────────────────────────────────────────────────────────────────────┐
│  业务 Agent 插件（即插即用；entry-point 注册）                        │
│  Compiler(RPM│镜像) / UT / Benchmark / Optimization / Review / CI   │
│  依赖方向：仅依赖 L3 SDK 与 L2 Contract                              │
├────────────────────────────────────────────────────────────────────┤
│  L4 编排层：DSL 解析/校验 → 引擎执行；Run 生命周期/gate/循环预算       │
│     （LangGraph 硬封装于 framework/engine/，经 EnginePort 接入）      │
│  L4' 特权服务（独立进程）：Approval 服务 │ Release Broker │ Build Gateway│
├────────────────────────────────────────────────────────────────────┤
│  L3 Agent SDK：AgentBase / worker 模型 / side_effect / trace         │
├────────────────────────────────────────────────────────────────────┤
│  L2 Contract（独立文档 01，独立版本演进）                             │
├────────────────────────────────────────────────────────────────────┤
│  L1 公共模块：LLM 接入 │ Knowledge(CodeGraph/Wiki/LogAnalyzer KB) │   │
│   Context │ Evidence │ Ledger+Artifact │ 资源管理                     │
│   构建后端(本地 GBS+mic │ Quickbuild) │ 板子池 │ 基线镜像缓存 │ Profile 库│
├────────────────────────────────────────────────────────────────────┤
│  L0 基础设施：SQLite(WAL) │ 文件/镜像存储 │ 日志 │ 配置               │
└────────────────────────────────────────────────────────────────────┘
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
| D7 | 数据边界 | 数据密级**由来源出生即标注**（snapshot 读取器/构建后端/板子池/KnowledgeProvider 产出即带密级），聚合取最高、禁止调用方降级；provider 白名单由中心安全配置授权 | 不依赖调用方诚实；残余风险 §14 R8 |
| D8 | 发布安全 | 发布凭据仅存在于框架 **release broker** 独立进程；CI Agent 只产 ReleasePlan；审批授权以 Ledger 授权记录形态存在（无 bearer 流转），broker 经特权 RPC 原子核销；授权绑定 release manifest digest；官方发布 adapter 随框架交付 | 业务 Agent 拿不到凭据，绕过面收敛到 broker 单点 |
| D9 | 循环上限 | 循环为 DSL 显式声明的 `loop` 对象（环级预算），编排层强制；另有 Run 级总预算 | 计数归属清晰、静态可校验 |
| D10 | Contract 冻结 | draft freeze（三方评审）→ v1.0（G6 三条件） | 未被真实消费的 contract 不定稿 |
| D11 | 并发模型 | MVP：**单执行 Run**（执行槽 = 持有 worker/资源执行中；paused 不占执行槽、可多 Run 并存，resume 与新 Run 同入 FIFO 队列）；Run 内节点级并行；task 以子进程 worker 执行；资源经信号量额度管理（§7.6.3）；Ledger 直写者唯一（编排进程，其余经 control-plane RPC）。**v2.0 补充**：等待 Quickbuild 远程构建或排队等板子期间，Run 同 gate 等待一样不占执行槽（资源按类别计额：本地构建 / 镜像构建 / 板子 / 远程构建配额） | 单机资源与 SQLite 约束下最小正确模型；镜像与远程构建耗时长，不能独占执行槽 |
| D12 | 执行环境固化 | Run 创建时固化 execution manifest：pipeline digest、contract 版本、框架版本、agent 制品 digest、provider 配置 digest、引擎版本；task dispatch / 审批 / 发布前复核相关 digest；恢复时不匹配走 ledger 级 administrative finalize（§4.3.3），不做在途迁移；provider 配置 digest 含策略语义与 **端点身份/信任策略**（仅凭据值除外——密钥轮换不影响恢复，端点改向则触发不匹配） | 官方明示 interrupted thread 不支持拓扑变更（节点改名/删除）、state 不兼容变更有风险；逐类推理迁移安全性的成本与出错面大于一律拒绝 |
| D13 | 信任模型 | 内网单机单操作员；patch 来源限于经认证的 Skill 调用方；构建脚本视为半可信（见 §8.1） | 沙箱深度与威胁模型匹配（N7） |
| D14 | 即插即用 | 业务 Agent = entry-point 插件；流水线组成 = YAML；Agent 间无直接依赖（只经 Contract 交换 Report）；删除/替换任一业务 Agent 由静态校验器判定合法性，上游缺失按 optional 降级并在报告中显式标注（§2.4） | 各业务团队独立演进；试用子集流水线零代码 |
| D15 | 两阶段构建与构建后端 | Compiler Agent 两种模式：`rpm`（本地 GBS 增量，受影响包 + 反向依赖闭包，修复循环在此阶段完成）与 `image`（后端可选：`local` = GBS 全量 + mic 出镜像；`quickbuild` = 经 Build Gateway 提交远程构建）；两模式作为两个节点出现在流水线中，均可单独删除 | 快速修复与完整镜像分离；镜像阶段失败同样回流修复 |
| D16 | 编译问题分析引擎 | Compiler Agent 的分析与修复引擎 = LogAnalyzer（含团队编译问题经验知识库）；框架经适配接口调用；修复规则沿用 LogAnalyzer 既有约定：最优方案进 patch，另附两个备选方案入报告；真实缺陷直接修复，不以屏蔽告警选项绕过 | 复用已验证能力与经验库，不重复建设 |
| D17 | Benchmark 可配置 | 套件注册表，来源三种：内置套件（含 TPMS 适配）/ 开发者脚本 / 开发者描述用例 → Agent 生成脚本 → 有效性检查 + 人工确认一次后入库；统一结果格式；A/B 对比基线镜像；测量科学性复用 TPMS 做法（重复、交叉、板子静止判定） | 套件持续增长不改 Agent 代码；杜绝"测错东西" |
| D18 | 测量—优化闭环 | Optimization Agent 以优化方法插件组织（AutoFDO、BOLT、CompilerGym 类、MLGO）；两种触发：随 patch 的轻量模式与独立优化专项流水线的重量模式；优化产物以 patch 形式提交，**必须**回流 Compiler → UT → Benchmark 重新验证，发布仍经人工审批与 broker | 优化不得引入功能回归；收益须实测证明 |
| D19 | 板子与镜像资源 | 板子池（BoardPool）由框架交付：独占租约、刷机、健康检查、能力探测（PMU/SPE/BRBE 等）、静止判定；基线镜像按（snapshot、构建配置、后端）缓存复用；Profile 库按（包、代码版本、板型、套件）存储并带新鲜度 | UT/Benchmark/profile 采集共享板子，不能各管各；基线不重复构建 |
| D20 | 源码接入 | SourceProvider 抽象：首期 Git/Gerrit（Tizen）；VD 的 Perforce + shelve CL 与 Cosmos 后端作为适配层后接；patch series 模型对两者统一 | Tizen 先行、VD 后接，核心不改 |
| D21 | 外部构建凭据 | Quickbuild 的 SSO 会话只存在于框架 Build Gateway 独立进程；会话失效时由运维在弹出的浏览器窗口中登录，框架不保存账号密码；业务 Agent 经能力句柄提交与查询，拿不到会话 | 与 D8 同一原则：凭据集中于可信小进程 |

### 2.3 与外部系统的关系

| 外部系统 | 关系 | Codex 开发期处理方式 |
|---------|------|---------------------|
| Coding Agent | 框架外，经 Skill 调用框架 MCP 服务（§6.5） | 框架实现 MCP 服务 + 配套 Skill + 模拟客户端；ClineSR 与 Codex 均可作客户端联调 |
| 人工 Reviewer | 经 Review CLI 操作 Approval 服务（§8.2） | 框架交付 CLI 与服务，Codex 可本地全流程测试 |
| CodeGraph / LLM Wiki | KnowledgeProvider 实现 | 开源仓库本地部署真实联调 |
| 内网大模型（经 ClineSR CLI） | 第一阶段唯一的生产 LLM provider：框架经 ClineSR CLI 调用内网大模型（§7.1） | FakeLLMProvider（fixture 驱动、接口一致）；内网联调用真实 ClineSR CLI |
| build server (GBS) | 本地构建后端（RPM 增量、全量） | 本机真实 gbs（gbs.conf 已定可用）`[E0 预检]` |
| mic | 本地镜像构建（全量构建产物 → 镜像） | 本机真实 mic + 镜像 ks 配置 `[待补充]`；需特权执行，经 deploy 的特权 launcher |
| Quickbuild | 远程构建后端（经 Build Gateway） | 开发期不可达（外网）→ FakeQuickbuild（fixture 驱动、接口一致）；真实联调在内网执行 |
| LogAnalyzer | Compiler Agent 的分析与修复引擎 + 编译问题知识库 | 开源仓库本地部署；内网 LLM 不可达时用 FakeLLMProvider |
| Tizen 源码 (gerrit) | snapshot 拉取来源（SourceProvider：Git/Gerrit） | 可达性 `[E0 预检]`；不可达则 fixture snapshot 模式 |
| VD 源码 (Perforce) / Cosmos | 后接适配层（N8） | 首期不开发，仅保证接口可容纳 |
| 测试板（RPi4 / RPi5 / 电视板） | 板子池（框架交付）+ 板型适配器 | FakeBoardPool；真实板子联调在内网执行 |
| TPMS | Benchmark 内置套件之一（适配器） | 适配器 + fixture 数据 |
| llvm-profgen（增强版）/ BOLT / CompilerGym 类工具 / MLGO 模型 | Optimization Agent 的优化方法插件后端 | 本机工具链真实调用；板上 profile 采集在内网执行 |
| gerrit/github 发布 | **release broker 执行**（CI Agent 只产计划） | broker + 官方 gerrit/github adapter + FakePublisher 均框架交付；其他 CI 工具扩展走无凭据子进程受限模式（§8.3） |

### 2.4 即插即用（Agent 增删不影响整体）

**机制**（四条共同保证，缺一不可）：
1. **插件化注册**：每个业务 Agent 是独立安装包，经 entry-point `codingsystem.agents` 注册；安装/卸载不改框架代码。
2. **只经 Contract 交互**：Agent 之间互不调用、互不感知；上游产出以 Report 形式经框架传递（D2），下游只认 Report 类型，不认产出者。
3. **流水线 = 配置**：哪些 Agent 参与、顺序、并行、循环、审批位置全部写在 pipeline YAML；删掉一个节点只改 YAML。
4. **加载期静态校验**：删改后的流水线在加载时由校验器判定是否合法（路由穷尽、必需上游存在且先行、环有预算、发布必经人工审批等，§4.2.6）；不合法的配置根本无法启动，而不是跑到一半出错。合法时，缺失的可选上游按降级运行，并在最终报告中显式写明"本次 Run 未执行 X"（§6.3）。

**删除各 Agent 的影响**（随仓交付的流水线示例覆盖以下组合）：

| 删除的 Agent | 结果 | 需要同时调整的配置 |
|-------------|------|------------------|
| Optimization | 测量后直接进阈值判定与审查，不做优化 | 去掉 optimize 节点与优化环 |
| Benchmark | 不做性能评估 | 同时去掉阈值 gate 与 Optimization（二者以 Benchmark 结果为必需输入，校验器会提示） |
| UT | 不做板上UT 测试 | 去掉 UT 修复环；含发布时须在 `release_requires` 中移除UT 测试报告（见 §4.2.6），即显式接受"未测发布"并留痕 |
| Compiler（镜像模式） | 只出 RPM、不出镜像 | 同时去掉依赖镜像的 UT/Benchmark/Optimization |
| Review | 不做 AI 汇总审查 | 人工审批仍可凭各 Report 证据链进行 |
| CI / 发布段 | 只验证、不发布 | 末端改为 terminal 节点（成功条件显式声明） |

随仓流水线示例：`full_pipeline.yaml`（全流程，§4.2.1）、`optimize_campaign.yaml`（优化专项，§4.2.1）、`compiler_only.yaml`（只编译+出镜像）、`compiler_bench_only.yaml`（编译+Benchmark）。

### 2.5 交付边界

| 部件 | 提供方 |
|------|-------|
| 框架（编排、SDK、Contract、公共模块）、Approval 服务、Release broker、官方 gerrit/github adapter、Build Gateway、板子池、基线镜像缓存、Profile 库、部署资产 | 本团队开发 |
| 全部六类 Agent：Compiler（LogAnalyzer 为分析引擎）、UT、Benchmark（套件机制 + TPMS 适配）、Optimization（AutoFDO/BOLT 先行，CompilerGym 类与 MLGO 随后）、Review、CI | 本团队开发 |
| UT 测试用例 | 业务部门提供 |
| 外接性能测试用例（脚本或用例描述，经 Benchmark 套件机制接入）与性能 SPEC（启动、内存、场景性能等） | 业务部门提供 |
| Review 外接知识库内容（经 KnowledgeProvider 接入，与 CodeGraph / LLM Wiki / LogAnalyzer 经验库并列） | 业务部门提供 |
| 板型刷机适配中与具体产品相关的参数（刷机工具、连接方式） | 板子所属部门提供 |

各 Agent 仍按插件形态开发与注册（D14）：本团队统一开发不改变"即插即用"的结构——任何 Agent 可被替换、删除或由其他团队按 02–06 设计指引另行实现。

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
| **构建后端（Build backend）** | 执行构建的可插拔实现：`local`（GBS 增量 RPM / GBS 全量 + mic 镜像）、`quickbuild`（远程，经 Build Gateway）；VD 的 Cosmos 为后接实现 |
| **Build Gateway** | 框架交付的独立进程，唯一持有 Quickbuild 会话；代理提交、状态查询、日志拉取（§8.6） |
| **镜像（Image）** | Compiler Agent 镜像模式的产物；以 `image_ref`（内容摘要 + 构建元数据）引用，存放于镜像存储，不进普通 artifact 目录 |
| **基线镜像** | 同一 snapshot、同一构建配置、不含本次 patch 的镜像；Benchmark A/B 对比的参照；按缓存键复用（§7.8） |
| **板子池（BoardPool）** | 框架交付的测试板管理：登记、能力探测、独占租约、刷机、健康检查、静止判定（§7.7） |
| **Benchmark 套件** | 一组可重复执行的测量用例 + 结果解析规则 + 版本号；来源为内置 / 开发者脚本 / 开发者描述用例自动生成（§7A.3） |
| **Profile** | 板上运行采集的性能剖析数据（如 perf 采样），供 AutoFDO/BOLT 使用；存于 Profile 库并带新鲜度（§7.8） |
| **优化方法插件** | Optimization Agent 内可注册的优化手段（AutoFDO、BOLT、CompilerGym 类搜索、MLGO 策略）（§7A.4） |
| **无输入流水线** | 声明 `input: none` 的流水线（如优化专项），创建即进入排队、不等待 Coding Agent 的 patch（§4.2.6） |
| **Ledger** | 单一 SQLite 权威事实源（D6） |
| **EvidencePacket** | 提交给 LLM 的结构化证据包（§7.4） |
| **Skill / MCP 接入** | 外部 Coding Agent 与框架的交互方式：框架提供 MCP 服务（暴露流水线操作为 MCP 工具）与配套 Skill（告诉 Coding Agent 何时、如何调用这些工具）（§6.5） |
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

#### 4.2.1 结构与示例（两份示例即校验器验收用例，必须可通过校验）

**示例一：全流程（`full_pipeline.yaml`）**

```yaml
pipeline: full_pipeline
dsl_version: 1            # DSL schema 版本，纳入 Contract 版本体系
input: patch              # 需要 Coding Agent 提交 patch（缺省值）
nodes:
  compile_rpm:    { agent_type: compiler, mode: rpm }          # 本地 GBS 增量：受影响包 + 反向依赖
  compile_image:  { agent_type: compiler, mode: image,
                    config: { backend: local } }               # local = GBS 全量 + mic；可改 quickbuild
  ut:             { agent_type: ut }
  benchmark:      { agent_type: benchmark,
                    config: { suites: [core_startup, media_playback], collect_profile: true } }
  optimize:       { agent_type: optimizer, mode: per_patch }   # 轻量模式：只针对本次改动涉及的包
  bench_gate:     { gate: threshold, metric: benchmark.regression_pct,
                    op: "<=", value: 5.0 }                     # 缺指标 = fail-closed
  review_static:  { agent_type: review, mode: static }
  review_final:   { agent_type: review, mode: final }
  ci_plan:        { agent_type: ci }                           # 产 ReleasePlan（位于人工审批之前）
  human_review:   { gate: hitl }                               # 审批对象 = ReleasePlan 规范化的 ReleaseManifest
  release:        { broker: release }                          # 特权终局节点，outcome 集固定（4.2.5）
entry: compile_rpm
release_requires: [build_report, image_report, ut_report, bench_report]   # 发布前必须针对当前 series 新鲜（4.2.6）
loops:
  - id: image_fix_loop
    edges: [ { from: compile_image, to: compile_rpm } ]       # 镜像阶段发现的编译问题回流修复
    budget: { max_rounds: 2, max_wall_clock_min: 480 }
  - id: ut_fix_loop
    edges: [ { from: ut, to: compile_rpm } ]
    budget: { max_rounds: 2, max_wall_clock_min: 480 }
  - id: opt_loop
    edges: [ { from: optimize, to: compile_rpm } ]            # 优化产物必须回流重新编译、重新验证
    budget: { max_rounds: 2, max_wall_clock_min: 720 }
run_budget: { max_wall_clock_min: 2880 }
joins:
  - id: pre_final_review
    wait_for: [bench_gate, review_static]
    timeout_min: 720
    to: review_final
routes:
  - { from: compile_rpm,   on: build_passed,             to: compile_image }
  - { from: compile_rpm,   on: build_failed_exhausted,   to: fail_safe }
  - { from: compile_image, on: image_ready,              to: [ut, review_static] }
  - { from: compile_image, on: image_fix_patch_ready,    to: compile_rpm }
  - { from: compile_image, on: image_failed_exhausted,   to: fail_safe }
  - { from: ut,            on: ut_passed,                to: benchmark }
  - { from: ut,            on: ut_fix_patch_ready,       to: compile_rpm }
  - { from: benchmark,     on: bench_done,               to: optimize }
  - { from: optimize,      on: opt_patch_ready,          to: compile_rpm }
  - { from: optimize,      on: no_further_gain,          to: bench_gate }
  - { from: bench_gate,    on: pass,                     to: join:pre_final_review }
  - { from: review_static, on: review_report_ready,      to: join:pre_final_review }
  - { from: review_final,  on: review_report_ready,      to: ci_plan }
  - { from: ci_plan,       on: release_plan_ready,       to: human_review }
  - { from: human_review,  on: approved,                 to: release }   # approved 必须直达 release（4.2.6）
  - { from: human_review,  on: rejected,                 to: fail_safe }
default_route: fail_safe    # 任何未匹配 outcome（含全部 sys.*）的兜底
```

流程说明：本地 RPM 构建（修复在此完成）→ 出镜像（镜像阶段的编译问题回流 RPM 阶段修复）→ 镜像就绪后并行开始板上UT 测试与静态审查 → UT 测试通过后跑 Benchmark（与基线镜像 A/B，顺带采集 profile）→ Optimization 判断是否有优化机会：有则产出优化 patch 回流重新编译、重新UT 测试、重新测量；没有更多收益则进入阈值判定 → 与静态审查汇合后做汇总审查 → 生成发布计划 → 人工审批 → 发布。三个环均有轮数与时长上限。

**示例二：优化专项（`optimize_campaign.yaml`，开发者手动或按周期触发，不需要 Coding Agent 的 patch）**

```yaml
pipeline: optimize_campaign
dsl_version: 1
input: none               # 创建即排队，不进入 awaiting_patch
nodes:
  compile_rpm:    { agent_type: compiler, mode: rpm }
  compile_image:  { agent_type: compiler, mode: image, config: { backend: local } }
  ut:             { agent_type: ut }
  benchmark:      { agent_type: benchmark, config: { suites: [core_startup], collect_profile: true } }
  optimize:       { agent_type: optimizer, mode: campaign,
                    config: { methods: [autofdo, bolt] } }          # 重量模式：可启用 compilergym / mlgo
  review_final:   { agent_type: review, mode: final }
  ci_plan:        { agent_type: ci }
  human_review:   { gate: hitl }
  release:        { broker: release }
entry: compile_image      # 首轮直接以当前 snapshot 出镜像并测量
release_requires: [image_report, ut_report, bench_report]
loops:
  - id: ut_fix_loop
    edges: [ { from: ut, to: compile_rpm } ]
    budget: { max_rounds: 1, max_wall_clock_min: 480 }
  - id: opt_loop
    edges: [ { from: optimize, to: compile_rpm } ]
    budget: { max_rounds: 3, max_wall_clock_min: 1440 }
run_budget: { max_wall_clock_min: 4320 }
routes:
  - { from: compile_rpm,   on: build_passed,           to: compile_image }
  - { from: compile_image, on: image_ready,            to: ut }
  - { from: ut,            on: ut_passed,              to: benchmark }
  - { from: ut,            on: ut_fix_patch_ready,     to: compile_rpm }
  - { from: benchmark,     on: bench_done,             to: optimize }
  - { from: optimize,      on: opt_patch_ready,        to: compile_rpm }
  - { from: optimize,      on: no_further_gain,        to: review_final }
  - { from: review_final,  on: review_report_ready,    to: ci_plan }
  - { from: ci_plan,       on: release_plan_ready,     to: human_review }
  - { from: human_review,  on: approved,               to: release }
  - { from: human_review,  on: rejected,               to: fail_safe }
default_route: fail_safe
```

说明：优化专项的产物（profile 文件、构建选项变更）以 patch 形式进入 series，发布到各包自身仓库——与普通 patch 走同一条人工审批 + broker 发布路径。若首轮测量后即无优化机会（no_further_gain），review_final 汇总"无可发布内容"，ci_plan 产出空发布计划，审批后 Run 以 succeeded 关闭且不发布任何对象（空计划的处理细则 `[01]`）。

#### 4.2.2 节点与寻址
- 同一 agent_type 的多次使用 = 多个显式节点（各带自有配置），**不存在 `node.qualifier` 点号寻址**；路由 from/to 只引用已声明节点名、保留节点、或 `join:<id>`。
- 保留节点见 §3；`entry` 必填且唯一；终局节点为 `release`、`fail_safe`、或显式 `terminal: true` 节点（子集流水线用）。terminal 节点必须声明 `success_on: [status...]`：outcome ∈ success_on → closed(succeeded)，其余（含 sys.*）→ fail_safe；`compiler_bench_only.yaml`、`compiler_only.yaml` 示例按此交付。release **特权节点**的 outcome 集与终态映射固定（§4.2.5）。

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
静态校验器全部规则：节点/路由/join 引用有效；entry 存在；每个可达环均被某 `loops` 声明覆盖且带 budget；路由穷尽（4.2.3）；含 release 节点则必经 hitl 且（release 可达路径上的 hitl）approved 出边直达 release、release 无出边（4.2.5）；join 的 wait_for ≡ 指向该 join 的路由源集合，join 的 to 不得指向另一 join（MVP 禁止链式 join）；**join 作用域与共同到达检查**——每个多源 join 的来源必须由同一次显式 fan-out 的不同分支派生（每个来源恰由一个分支到达——来源集在分支间构成划分；共同支配关系不得替代共同 fan-out），全部来源共享该 activation scope；**共同到达性**：从该 fan-out 到每个来源 s 的路径上，任一节点的每个 outcome 分支必须满足三者之一——仍在可达 s 的路径上、到达 Run 终局（fail_safe/terminal/release）、或经声明的环边回流。环边作为本条件例外须同时满足两条静态约束：**其一，回流路径必然重经该 join 的共同 fan-out、从而重派全部来源分区**（机制：环边采用触发 supersede 条件③级联退役旧 cohort，替代 cohort 由重经 fan-out 的新分派产生并继承父 scope——不依赖 timeout 或预算兜底）；**其二，在重经当前 task 所属 activation 的共同 fan-out 之前，不得先重经任何祖先 activation 的共同 fan-out**——跨 activation 边界的回环会使真正被替代的祖先 activation 逃过③的退役根（③锚定在采用环边的 task 所属 activation），其计时器存活即误杀，祖先链 CAS 因该祖先未被标记而不设防；本约束静态保证退役根 = 被替代的作用域。违反任一环约束的回环拒绝加载；outcome 分支三者皆不满足（且不构成合法环边例外）的图亦拒绝加载（互斥 outcome 分支导致来源必然缺席的图在此被拒）；拒绝同一 source 每 activation 多次送达的图（到达键歧义）。**嵌套汇合采用父 activation 关系（定案）**：activation 记录持久化 parent_activation_id，内层 join 原子消费后以**父 activation scope** 分派下游——内层先汇合再参与外层 join 因此合法且可成组；validator property 与 model-based 反例（含互斥 outcome、嵌套汇合重入外层）入 §11.3（4.2.4，传播细则 [01]）；hard-required 上游与 **threshold gate 的指标来源节点**均做**支配性检查**——到消费节点的每条路径都必须先经过生产节点，仅存在不满足，且消费同 series 结果；terminal 节点必有 success_on；threshold gate 引用的指标来源节点在图中存在（不存在即拒绝加载——hard-required 依赖同理：Agent contract 可声明少数 hard-required 上游产物 `[01]`，其余一律 optional 降级，§6.3）；无不可达节点。**v2.0 追加两条规则**：① **发布前新鲜度（release_requires）**——含 release 节点的流水线必须声明 `release_requires`（发布前必须存在的报告类型清单）；静态检查：每一类报告的生产节点存在且支配 human_review；运行时检查：Approval 服务提交决定时的新鲜度 CAS（§8.2）一并核对清单内每类报告均存在且针对当前 series——任何产生 patch 的节点（Compiler 修复、UT 修复、Optimization）推进 series 后，旧报告全部失效，必须重新验证才能再进审批；清单中删去某类报告即显式接受不含该验证的发布，配置留痕于 pipeline_digest。② **输入类型（input）**——`input: patch`（缺省）的流水线须由 Skill `submit_patch` 提供初始 series；`input: none` 的流水线以空 series 起步、创建后直接排队，其 entry 节点不得是需要 patch 才能工作的节点（以 Agent 注册的输入声明判定）。通过全部规则 = 合法子集；示例 `pipelines/` 下四份流水线随仓交付（§2.4）。

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
- awaiting_patch TTL 默认 24h，超时 closed(cancelled)；run_budget 自 submit_patch 受理（进入 queued）起算。`input: none` 的流水线跳过 awaiting_patch：created → queued，run_budget 自进入 queued 起算。
- **长等待不占执行槽（v2.0）**：节点在等待 Quickbuild 远程构建结果、等待板子租约、或等待运维登录 Quickbuild 时，处于节点级外部等待——与 gate 等待同规则：仅剩此类等待、无可运行工作时 Run 迁 paused 并释放执行槽，等待结束经 queued 重新取槽；**计时口径**：外部等待计入 run_budget 与环时长（与人工审批不同——构建与排队属于流水线自身成本），但 Build Gateway 因会话失效等待运维登录的时段不计入（告警提示运维）。
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
- 预算属于 `loops` 声明的环对象（环由 `edges` 唯一定义，routes 不重复标注环归属）；环边每通过一次计数 +1，**max_rounds: N = 环边允许通过 N 次，第 N+1 次通过请求即拦截并强制路由 fail_safe**（示例 max_rounds: 2 即最多 2 轮修复回流）；计数持久化于 Ledger 随恢复延续；wall_clock 排除 paused 时段；多环共享节点各环独立计数。`run_budget` 为 Run 级总预算，最先触发者生效；**run_budget 与 join timeout_min 的计时口径同 loop wall_clock——排除因 gate 等待而 paused 的时段与 publishing 等待时段**（多日人工审批不消耗预算）；因远程构建/板子排队而 paused 的时段**计入**预算（属流水线自身成本），因 Build Gateway 会话失效等待运维登录的时段不计入（§4.3.1）。

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
- Agent 经 `ctx` 获得框架注入句柄：artifact store、KnowledgeProvider、LLM client、EvidencePacket builder、trace、以及**能力句柄**（BuildBackend（本地 / Quickbuild）、ImageBuilder、BoardPool、BaselineCache、ProfileStore、LogAnalyzer 引擎等，按 agent_type 在配置中授权注入；清单**显式排除发布通道**——发布只存在于 broker（§8.3）；未授权句柄不存在于 ctx，与 D8 联动）。
- 注册：entry-point namespace `codingsystem.agents`；加载时校验 status_set 非空、contract 兼容、conformance attestation（§11.3）。注册信息另声明：`produces`（产出的报告类型）、hard-required 上游、`input_requirement`（是否需要 patch 才能工作——用于 `input: none` 校验）、所需能力句柄。

#### 5.1.2 Worker 模型（进程边界）
- 每个 task 由编排进程 spawn 独立子进程 worker 执行：注入 ctx → 调 execute → 结果经 IPC 回传。
- worker 以独立进程组（setsid）启动；hard timeout / 取消 = 对**进程组** SIGTERM 宽限后 SIGKILL（killpg，覆盖 gbs 等孙进程），构建后端额外登记外部长进程（含 mic）供递归清理；进程退出映射 `sys.crash` / `sys.timeout`。
- 编排层持有 worker 租约（heartbeat）；**心跳丢失时 worker（进程组长）先 killpg 终止本组全部进程（含 gbs 孙进程）与构建后端登记的外部长进程，再自行退出**——kill 语义不因编排进程失联而缺席；编排进程恢复时先按 Ledger 登记的 pgid 验证归属并 reap 孤儿进程组、再重放。故障注入含"编排进程崩溃且 GBS 子进程仍活跃"用例（§11.3）。
- Agent 实例作用域 = 单 task（无跨 task 内存态，setup/teardown 每 task 执行）。凭据类 secret 不注入业务 worker（D8）。

### 5.2 副作用：at-least-once + 效应侧幂等
- **保证等级声明**：框架保证 at-least-once，不承诺 exactly-once。外部效应成功与完成记录落盘之间存在崩溃窗口，关闭窗口的责任在效应侧幂等。
- SDK 入口为 `side_effect(effect_call_id, params, fn, repeat_seq=None)`——**idem_key 只能由框架计算**（worker 不得自供完整键，conformance 强制）；**effect_class 由 fn 所属注册效应类型推导**：side_effect 仅可包装类型化能力句柄上注册的效应（probe/replay_safe 能力声明挂在该类型上），自由函数不可包装，effect_class 参与 conformance 校验（细则 `[01]`）；其为两阶段持久化状态机（Ledger 同库事务）：`claimed(intent) → running → succeeded/failed`；恢复时遇 `running/claimed` 记录 = 状态不确定（待对账），执行 **恢复协议**：按 §5.2 三支对账（probe / replay_safe 重放 / 皆无 → 持久化 unknown 态并转 sys.error）。
- `idem_key = hash(run_id, dispatch_id, effect_class, effect_call_id, effect_params_digest[, repeat_seq])`——**效应身份 = slot + 稳定逻辑调用标识**：slot = (run_id, **dispatch_id**)，dispatch_id 为创建该 task 的边送达/分派事件的 Ledger 标识——跨 attempt 稳定（重试复用同一 task 即同一 dispatch）、跨 task 天然隔离（含 entry 分派与兄弟送达；node/activation/环轮次由 dispatch 记录蕴含，不入键）。**`effect_call_id` 由调用方提供、在 Agent 代码内稳定**（如 "build_main"、"flash_pre"），不依赖调用次序——控制流变化的重试不会把新逻辑调用错配到旧记录；框架强制同 task 内 effect_call_id 唯一在册（conformance 检查项），显式声明的重复执行由调用方给定 `repeat_seq`（迭代序）。`effect_params_digest` = 调用实参规范化摘要（含 series_id/tree_digest、构建目标、板卡标识等，artifact 引用按 content digest 参与）。**不含 attempt**：同 (call_id, params) 的重试/重放命中同一记录；非决定论重执行实参不同 → 新键，且**跨 attempt 遗留**的同 call_id 旧在途异参记录经 attempt 启动对账**定态**——逐支终态：probe 确认成功 → succeeded（复用）、确认未发生或 replay_safe 退役 → abandoned、不可判定 → unknown + sys.error；**succeeded 与 unknown 不得改写为 abandoned**；**异参新键允许集合（枚举定案）**：定态 succeeded 或 abandoned → 异参新 claim 放行、新键独立执行，且旧 succeeded 仅供同参精确键命中复用、**不得跨参数复用**；定态 unknown → task 已随 sys.error 中止，无新键可立。**本枚举仅辖跨 attempt 定态记录**；干净终态 failed（正常执行产物、非定态产物）之上的同 call_id 异参新 claim 依既有效应类别策略放行，不在此列（效应侧"退役"不与 activation 的 supersede 术语混用）。**唯一性约束的两个层面**：conformance 静态检查（每逻辑调用点唯一命名）；运行时拒绝路径——**仅同一 attempt 内**（跨 attempt 遗留已经启动对账定态）同 call_id 存在未决（claimed/running）记录时的异参新 claim 被拒（作者误用形态），task 报 `sys.invalid_result`（细则 `[01]`）。
- **记录状态与查找矩阵**（全集 claimed / running / succeeded / failed / abandoned / unknown，迁移与查找表 `[01]`）：查找只命中非 abandoned 记录——claimed/running → 按效应能力对账（见下）；**succeeded → 直接复用（含上一 attempt 经 probe 确认成功的记录——可 probe 而不可安全重放的效应必须复用，不做保守重做）**；failed → 按效应类别策略重试或上报。对账按效应能力分三支（conformance 分别覆盖）：**可 probe** → probe 确认成功迁 succeeded（复用）、未发生迁 abandoned；**无 probe 但声明 replay_safe** → 旧在途记录退役 abandoned、重放；**两者皆无** → unknown（持久化）并报 sys.error。attempt 启动前，编排层将上一 attempt 遗留的本 task 非终态记录逐条按上述三支对账。abandoned 记录不参与命中；**记录版本化为通则**——凡同键在 abandoned 记录之上的重执行，一律以版本化新记录承载（迁移/查找表 `[01]`）。
- 状态迁移经 control-plane RPC 由编排进程事务写入：worker 收到 claimed ack 后方可启动效应，RPC 失败 = 效应不得启动（fail-closed）；intent/running 即时提交，task 完成事务仅覆盖最终结果 + artifact 索引 + 幂等终态。
- 效应类别要求（contract + conformance 强制）：本地构建 = 可 probe（worktree/产物存在性）；**镜像构建 = 可 probe（镜像存储中按缓存键查存在性）**；**远程构建（Quickbuild）= 可 probe（按提交时写入的 run/task 标识查询远端构建记录与状态，提交即带该标识以便归因）**；刷板/板上执行 = 可 probe（读板上镜像标识）或声明可安全重放；**profile 采集 = 声明可安全重放**；**发布 = 仅经 broker，broker 端远端幂等（push 前查远端状态）+ token 单次核销双保险**。

### 5.3 trace 与 token 记账
- SDK 自动埋点（task 起止、LLM 调用、工具调用、artifact 读写）写 Ledger；`trace.jsonl` 为 Ledger 派生的追加安全格式（每行一事件），供人读与外部工具消费。
- token budget：按节点在 pipeline YAML 配置（`llm_budget:`），超限策略由 Context 管理执行（§7.3）。
- 落盘前统一脱敏：secret/token 只记指纹（§8.4）。

---

## 6. Contract 体系概览（精确 schema 见 01_Contract_Spec）

### 6.1 消息类型
`TaskInput` / `HandoffResult` / 各 Report（Build/Image/UT/Bench/Optimization/Review/Feedback，均携带 series_id 与产出 task_id）/ Benchmark 套件描述 / Profile 引用 / 优化计划/ `RunContext` / `ReleasePlan` / `ReleaseManifest` / Approval 决定与授权记录 / Run 终局摘要 / MCP 工具与 HTTP 端点的请求/响应消息。agent_type 注册信息含 status 全集与 hard-required 上游声明。

### 6.2 版本规则
Contract 独立版本号；Agent 以 PEP 440 specifier 声明兼容区间（§5.1.1）；框架装配时校验。pipeline `dsl_version` 属 Contract 版本体系。draft 期允许破坏性修改但记 decision_log。

### 6.3 上游缺失语义
默认全部 optional + 降级运行 + 报告显式标注"本次 Run 未执行 X"；Agent contract 可声明**少数 hard-required** 上游产物（如 benchmark、UT hard-require 镜像引用；optimization hard-require Benchmark 报告），由 DSL 校验器静态拦截（§4.2.6）。approval_token 属"外部供给依赖"类别，不参与上游产物校验。conformance 含上游缺失用例。

### 6.4 Patch 归属与陈旧性
产物为 patch series（非 squash），逐段标注产出者与动因；series 任何变更 → 新 series_id + 新 tree_digest → 旧 Report 对 gate/join 失效（§4.2.4）、未核销 token 失效（§8.2）。是否 squash 是 broker 发布期可配置行为。

### 6.5 Coding Agent 接入：Skill + MCP（决策定案）
- **接入方式**：框架提供 **MCP 服务**，把流水线操作暴露为 MCP 工具；同时提供配套 **Skill**，安装在 Coding Agent（ClineSR / Codex）中——Skill 描述何时调用、调用顺序（创建 Run → 提交 patch → 轮询状态 → 获取结果与反馈报告）、失败如何处理。Coding Agent 经 Skill 调用 MCP 工具启动流水线。
- **传输**：MCP 服务使用 Streamable HTTP 传输，部署在框架主机上（内网）；同一操作契约另保留 HTTP + JSON 端点，供脚本、运维工具与测试使用——两者共用同一实现与同一套校验，不存在语义差异。
- **MCP 工具与操作一一对应**：
  - 操作：`create_run(pipeline_id, target_spec)`（target_spec 指定 snapshot 拉取范围：仓/包/manifest，语义 `[01]`）、`submit_patch(run_id, series)`（unified diff series + 逐 patch 的 repo 归属；服务端校验对 pinned snapshot 可应用，不可应用即拒绝；一个 Run 仅接受一次初始 series，重复提交返回明确错误——修订走新 Run）、`get_status`、`get_result`、`cancel_run`。忙时语义：submit_patch 受理后 Run 进入 queued（FIFO，响应返回队列位置），resume 同队列；awaiting_patch 不占队列，TTL 见 §4.3.1。
- 认证与信任边界：MCP 连接与 HTTP 端点使用同一种静态 bearer token（配置下发调用方）；每次工具调用含 request_id 支持幂等重试；patch 大小/路径白名单校验。信任边界声明：MCP 服务与 HTTP 端点仅暴露于内网受控网段（D13），持 token 者视为受信 Coding Agent。
- **Skill 随框架交付并带版本**：Skill 中声明其适配的契约版本，与 MCP 服务版本不兼容时 MCP 返回明确错误，提示更新 Skill。

---

## 7. 公共模块（L1）

### 7.1 LLM 接入层
- Provider 抽象 `complete(messages, policy_ctx) -> LLMResponse`；实现：**ClineSRCliProvider（第一阶段生产实现）**、FakeLLMProvider（开发与测试）、将来的内网 LLM API provider（若提供）与可选外部 API provider。Agent 只面向该抽象编程，provider 更换不改任何 Agent 代码。
- **ClineSRCliProvider（定案：第一阶段不依赖 LLM API）**：内网目前只有 ClineSR CLI 可调用内网大模型，框架据此实现 provider，约束如下：
  - **只作补全引擎使用**：以单次非交互方式调用，框架把组装好的提示（含 EvidencePacket）写入临时目录作为输入，CLI 只返回文本结果；**关闭 CLI 自身的文件修改与命令执行能力**，工作目录指向空的临时目录——所有对代码与环境的改动都由 Agent 经框架的 side_effect 执行，不允许绕过框架由 CLI 直接改文件（保持可追溯与幂等）。
  - **结构化输出**：提示中要求固定的 JSON 结构，provider 校验结构，校验失败按 cascade 规则重试（§7.1 路由），仍失败报错交由 Agent 处理。
  - **进程管理**：每次调用为独立子进程，纳入 worker 进程组（超时 killpg）；并发数由资源额度单独限流（§7.6.3），避免同时拉起过多 CLI 进程。
  - **记账**：CLI 不返回 token 数时按输入输出字节估算并标注为估算值。
  - **数据边界**：ClineSR 调用的是内网大模型，密级上限在中心安全配置中登记（D7），框架照常逐次校验。
  - CLI 的调用参数（非交互模式、关闭工具的方式、输出格式选项）`[待补充]`，由 E0 预检确认。
- 数据边界（D7）：密级**全序**：secret > internal_code > build_log > public（聚合取最高 = 取全序最大）；密级由数据产出组件出生标注并随对象传播，聚合（EvidencePacket/消息/派生摘要/LLM 输出）取成员最高密级，API 不提供降级操作；provider 可接收密级集合由**中心安全配置**授权（非 provider 自报）；每次调用（含 cascade fallback 的每一跳）重新校验，fail-closed。业务侧绕过 SDK 自拼 payload 属残余风险（§14 R8），以 conformance 误标检测 + 约定管理。
- 路由：static binding → rule-based → cascade；cascade 升级判据 = 传输错误/超时/结构化输出校验失败（质量性判据不做，N3）。统一重试/超时/限流/token 记账。

### 7.2 KnowledgeProvider
接口同 v0.1；三个实现：CodeGraph（代码事实）、LLM Wiki（团队知识库）、**LogAnalyzer 知识库（编译问题解决经验，v2.0 新增）**。缓存键策略由 provider capabilities 声明：代码事实类（CodeGraph）键含 snapshot_id + tree_digest，知识库类（Wiki / LogAnalyzer KB）键不含基线。查询结果出生即带密级（D7）。

### 7.3 Context 管理（四层）
Run 级共享状态（框架，只读注入）；Agent 工作上下文与 token budget（SDK 工具：预算执行、截断/压缩策略）；EvidencePacket 组装（§7.4）;知识注入（带来源与密级）。

### 7.4 EvidencePacket 工具链
结构 facts / negative_facts / log_excerpts / target_source_excerpt / confidence；negative_facts 仅限工具产出的否定性代码事实；日志摘录组件负有**按内容升级密级**的责任——摘录中内联源码行即标 internal_code，不因来源是 build_log 而低标；**产 patch 请求必含 target_source_excerpt**（有界行数）；校验器含 RawDataDetector 与体积上限；packet 密级 = 成员最高密级。

### 7.5 Ledger、Artifact、trace
- **Ledger（D6）**：单 SQLite（WAL）承载 Run/Task 状态机、artifact 索引、side_effect 状态、循环计数、gate 等待项、授权/核销记录、resume outbox、事件流。**直写者唯一为编排进程**；worker / Approval 服务 / broker 一律经 control-plane RPC（§8.5）请求编排进程事务写入。task 完成事务 = 最终结果 + artifact 索引 + 幂等终态（intent/running 随执行即时提交，§5.2）。
- **Blob 提交协议**：artifact 落盘顺序强制 = 临时文件写入 → fsync → rename 至 digest 路径 → Ledger 索引事务提交；上传中 blob 持有 active-upload lease（临时命名空间），GC 仅回收超安全年龄且无 lease 的对象——与合法上传并发安全；索引事务提交前复验 blob 存在与 digest；索引存在而 blob 缺失 = 损坏，消费方报 sys.error。
- **Artifact**：内容寻址（content digest 即引用组成部分）、写入后不可变；目录 `artifacts/<digest前缀>/...`；保留策略：终态 Run 的大体积构建日志类保留 N 天（配置，默认 14）后清理，patch/report/trace 永久保留。
- **trace.jsonl**：由 Ledger 事件流派生，追加安全；崩溃不影响权威源。

### 7.6 构建与资源管理
#### 7.6.1 构建后端（BuildBackend）
统一接口：`build_rpm(snapshot, series, targets, scope) -> BuildResult`、`build_image(snapshot, series, image_profile) -> ImageResult`、`query(build_ref)`、`fetch_logs(build_ref)`。实现：
- **LocalGbsBackend**（首期）：RPM 阶段 = per-task git worktree 隔离、`git apply --index` + staged/worktree 一致性校验、GBS 增量构建（`--incremental`），范围默认"受影响包 + 反向依赖闭包"；镜像阶段 = GBS 全量构建至本地仓库 → `mic create`（镜像 ks 配置来源 `[待补充]`，mic 需特权执行，经 deploy 特权 launcher）。镜像产物入镜像存储（§7.8）。
- **QuickbuildBackend**（首期第二步，P6）：经 Build Gateway（§8.6）提交远程构建、轮询状态、拉取失败日志；提交时写入 run/task 标识以便 probe 归因与迟到结果识别。Quickbuild 的提交方式（表单字段、目标工程）`[待补充]`。
- **CosmosBackend**（VD，后接 P8）：同 Quickbuild 形态，输入为 Perforce shelve CL。
- **廉价前置检查先行**：镜像构建前强制执行可快速完成的检查（patch 可应用性、RPM 阶段结果、ks 配置可解析、磁盘水位），避免长耗时构建末尾才暴露低级问题。
#### 7.6.2 多仓 snapshot manifest
snapshot = `[ {repo_id, remote, commit, path} ]` 规范化清单；patch 逐条声明 repo_id；跨仓 series 按 manifest 序应用，任一仓失败即整体回滚该 worktree 组；tree_digest = 各仓应用后 tree hash 的规范组合（逻辑定义；计算为纯算法、无需 worktree，见 §4.2.4，算法 `[01]`）。
#### 7.6.3 资源额度（单机自我保护）
按资源类别计额：本地 RPM 构建、本地镜像构建（全量 + mic，默认并发 1）、板子（由板子池按可用板数管理）、远程构建配额、worker 数；排队 FIFO；磁盘水位检查（低于阈值拒绝新 Run 并告警；镜像构建另设更高水位）；worktree 与临时镜像目录于 task 终结时清理，泄漏由定期对账回收。
#### 7.6.4 源码接入（SourceProvider）
接口：`pin_snapshot(target_spec) -> SnapshotManifest`、`materialize(snapshot, series) -> Worktree`、`to_backend_input(series)`（转换为构建后端所需形态：git patch / Quickbuild 输入 / shelve CL）。首期实现 **GitGerritSource**（Tizen）；**PerforceSource**（VD，后接 P8）以 shelve CL 集合映射 patch series——series 模型、tree_digest 与审批发布语义对两者统一，框架核心不改。

### 7.7 板子池（BoardPool，框架交付）
- **登记与能力探测**：每块板登记板型、架构、连接方式（如 sdb）与当前镜像；首次接入与每次刷机后运行能力探测脚本，记录 PMU / SPE / BRBE / ETM 等采样能力（Benchmark 采集 profile 与 Optimization 选择方法的依据）。
- **独占租约**：UT、Benchmark、profile 采集按"板型 + 能力"申请租约，FIFO 排队；租约与 task 绑定，task 终结或心跳丢失时回收；板子 IP 等连接信息由板子池配置提供，Agent 不自行发现。
- **刷机**：经板型适配器执行（刷机工具与流程 `[待补充]`，属适配器实现），刷机为可 probe 效应（读板上镜像标识）；刷机失败三次标记板子"维护中"并告警，不再分配。
- **健康检查与静止判定**：分配前检查在线、存储、温度等；Benchmark 测量前与每个用例结束后做静止判定——关键指标（CPU、内存等）在小范围内平稳浮动方可放行（复用 TPMS 的判定思路），超时未静止则该次测量标记无效重测。
- **开发期**：FakeBoardPool（fixture 驱动）；真实板子联调在内网执行。

### 7.8 镜像存储、基线镜像缓存与 Profile 库
- **镜像存储**：镜像体积大，独立于普通 artifact 目录存放；以 `image_ref = (内容摘要, snapshot_id, series_id, 构建配置摘要, 后端)` 引用；保留策略：被 Run 引用期间保留，终态后默认 7 天清理（配置），基线镜像按缓存策略保留。
- **基线镜像缓存（BaselineCache）**：缓存键 = (snapshot_id, 构建配置摘要, 后端, 镜像配置)；Benchmark 需要基线而缓存未命中时，由框架以同一后端构建"不含本次 patch"的镜像并入缓存；同一 snapshot 的后续 Run 直接复用，避免每个 Run 的镜像构建量翻倍。基线测量结果按 (基线镜像, 套件版本, 板型) 同样缓存，但每次 A/B 仍按交叉方式重测以控制板子状态漂移（§7A.3）。
- **Profile 库（ProfileStore）**：存放 Benchmark 采集的 profile；键 = (包, 代码版本, 板型, 套件)；附采集条件（采样方式、时长、负载）与新鲜度；代码版本变化超过阈值即标记陈旧（AutoFDO 对代码漂移敏感），Optimization 只使用新鲜 profile，陈旧时请求重新采集。最终交付给开发者的 profile 文件随优化 patch 进入各包自身仓库（§7A.4）。

---

## 7A. 各 Agent 设计要点（02–06 设计指引的输入）

### 7A.0 各 Agent 的 AI 能力与使用原则

| Agent | AI 主要做什么 | 不交给 AI 的部分 |
|-------|-------------|-----------------|
| Compiler | 分析编译错误日志，结合 LogAnalyzer 经验库、CodeGraph、LLM Wiki 生成修复 patch（最优方案 + 2 个备选） | 是否编译通过（由构建结果判定） |
| UT | 分析失败日志与崩溃信息（含 coredump 摘要），定位原因并生成修复 patch | 测试是否通过（由用例结果判定） |
| Benchmark | 按用例描述生成测试脚本；测试前与用例间判断板子是否稳定；分析性能异常，给出原因初稿与可疑模块类别；生成测量报告初稿 | SPEC 达标与否、是否回归（由 SPEC 与统计规则判定） |
| Optimization | 依据性能数据与 profile 推荐优化候选并排序，评估优化效果、解释收益来源 | 优化是否有效（由 A/B 统计判定） |
| Review | 审查代码改动；结合 CodeGraph 与业务部门的外接知识库给出审查意见；汇总全部报告形成结论 | 是否发布（由人工审批决定） |
| CI | 生成发布说明与变更摘要 | 发布执行（由 Release broker 按已批准计划执行） |

**使用原则**：
1. **判定与 AI 分离**——是否达标、是否回归、是否通过一律由 SPEC、统计规则或确定性结果判定；AI 的输出是分析、生成与建议，标注为"AI 初稿"，经人确认后才作为结论。
2. **试点先行**——AI 分析能力（尤其性能异常原因分析、优化候选排序）先在试点范围内运行，统计其准确率与误报率，达标后再扩大使用范围；未达标的能力只作参考信息呈现。
3. **数据边界**——所有 AI 调用经 LLM 接入层，按数据密级校验可用的模型（D7），内网数据不出内网。
4. **可追溯**——AI 的每次输入证据、输出与采纳情况记入 Ledger，可按轮次回看。

### 7A.1 Compiler Agent（本团队交付，LogAnalyzer 为分析引擎）
- **两种模式、两个节点**：`mode: rpm` 与 `mode: image`（D15），可分别出现在流水线中，也可单独删除镜像节点只出 RPM。
- **RPM 模式**：经 SourceProvider 物化 worktree、应用 series → 本地 GBS 增量构建受影响包与反向依赖 → 失败时把日志交给 LogAnalyzer 引擎：日志解析 → 结合 LogAnalyzer 知识库、CodeGraph、LLM Wiki 组装 EvidencePacket → LLM 给出修复 → 最优方案作为修复 patch 提交 series candidate、另两个备选方案写入 BuildReport 供人工审批时参考 → 再构建；修复轮数有上限，超限 `build_failed_exhausted`。
- **镜像模式**：按节点配置选择后端（local：GBS 全量 + mic；quickbuild：经 Build Gateway）。镜像阶段出现的构建失败（全量构建暴露、或远程构建环境差异）同样交 LogAnalyzer 分析：可修复 → `image_fix_patch_ready` 回流 RPM 阶段；不可修复或超限 → `image_failed_exhausted`。产出 ImageReport（image_ref、构建配置、耗时、失败与修复记录）。
- **修复规则**（沿用 LogAnalyzer 约定）：真实代码缺陷直接修复并加注释说明原写法与修改原因，**不以关闭告警或屏蔽类编译选项绕过**；修复对开发者代码保持其原有命名与用法。
- **LogAnalyzer 接入形态**：框架定义 `LogAnalyzerEngine` 接口（`analyze(build_logs, context) -> Diagnosis{root_cause, fix_candidates[best + 2 alternatives], kb_refs}`）；实现为 LogAnalyzer 核心的 Python 封装，运行于内网 LLM（开发期 FakeLLMProvider）；具体调用形态（库调用或 CLI）`[待补充]`。

### 7A.2 UT Agent（本团队开发；测试用例由业务部门提供）
- 定位：在板上对新镜像做稳定性测试（UT 测试）——验证改动后的系统在真实板子上能稳定运行，而不只是单个函数的单元测试。
- 输入：ImageReport（hard-required）与业务部门提供的 UT 测试用例集（按包登记、带版本，未登记用例的包在报告中标注"无用例"）；经板子池申请租约 → 刷入镜像 → 执行UT 测试 → 失败时分析并可产出修复 patch（`ut_fix_patch_ready` 回流 Compiler RPM 阶段）。
- 产出 UTReport（板子、用例套件、通过/失败/跳过、失败分析）。刷机与板上执行均走 side_effect 幂等（§5.2）。

### 7A.3 Benchmark Agent（本团队开发；外接测试用例由业务部门提供）
- **套件来源三种**（D17）：
  1. **内置套件**：框架随附的适配器（首个为 TPMS 适配器），开箱即用；
  2. **开发者脚本**：开发者提供可执行脚本 + 结果解析规则（声明输出指标、单位、方向：越大越好或越小越好）；
  3. **开发者描述用例**：开发者用结构化描述写明"测什么、怎么触发、看哪些指标"，Agent 生成脚本 → **有效性检查**（在基线镜像上干跑两次：脚本能完成、指标确实来自被测对象、两次结果离散度在阈值内、无明显异常值）→ **人工确认一次** → 以版本号入套件注册表，此后与脚本型等同。生成脚本未通过检查或未经确认，一律不得作为基准使用（防止"测错了东西"）。
- **测量模式**（三种）：**全量**（套件全部用例）、**单项**（只跑指定用例，用于针对性验证假设，代替整套重复测试）、**快速**（精简用例与重复次数，用于开发期快速确认）。
- **一次完整记录、无需重测**：每次测量同时记录测试指标、关键区间耗时（如启动各阶段）、资源使用（CPU、内存、IO 等时间序列）与相关日志，统一存入测量记录；事后分析回归原因时直接使用这些附加信息，不需要为补数据再测一次。
- **SPEC 判定**：业务部门提供性能 SPEC（启动时间、内存、场景性能等），Benchmark 对每个指标给出 SPEC-IN / SPEC-OUT 判定；阈值 gate 可配置为按 SPEC 判定（如"SPEC-OUT 项数为 0"）或按相对基线的回归幅度判定，二者可同时使用。
- **统计判定标准**：测量波动按统计方法判定（重复次数、置信区间、显著性检验），判定标准随套件版本固定并写入报告，避免"测一次凭感觉"；与 TPMS 科学性改造采用同一套方法。
- **测量报告**：自动生成——包含 SPEC 判定结果、与基线的对比、统计置信度、AI 给出的异常原因初稿与可疑模块类别（标注为 AI 初稿）、每轮对应的镜像与改动；报告格式统一，便于与业务部门对接。
- **用例共享**：测试用例定义、测量方法与测量环境（板型、镜像配置、负载条件）作为套件描述的一部分带版本存放，可在不同部门（如 VD 与 SR）之间共享，保证双方测的是同一件事。
- **测量方法**：与基线镜像做 A/B 对比（基线来自 §7.8 缓存）；每个用例重复 N 次、基线与被测交叉执行；测量前与用例之间做板子静止判定（§7.7）；同时监测测量期间是否有异常 CPU 争抢，有则该次结果作废重测。统计判定方法与 TPMS 改造保持一致。
- **profile 采集**（`collect_profile: true`）：按板子能力探测结果选择采样方式（有分支栈记录能力则用之，否则用无分支栈的采样方案），采集结果入 Profile 库。
- 产出 BenchReport：顶层 `regression_pct`（全部指标中的最大回归，供阈值 gate 使用）与 `spec_out_count`（SPEC-OUT 项数，供 SPEC 判定 gate 使用）、逐指标对比与置信度、可疑与改动相关性分析、本次采集的 profile 引用。**所有回归都在报告中如实列出**，是否接受由阈值与人工审批决定，Agent 不做主观取舍。

### 7A.4 Optimization Agent（本团队开发，AutoFDO/BOLT 先行）
- **优化方法插件**（D18）：
  - **AutoFDO**：用 Profile 库中的新鲜 profile 生成编译用 profile（基于团队增强版 llvm-profgen），以 profile 引导重编受影响包；
  - **BOLT**：对热点二进制做链接后布局优化；
  - **CompilerGym 类搜索**：在编译选项 / pass 顺序空间中搜索更优配置——需要大量"编译 + 测量"，只在重量模式启用；
  - **MLGO 策略**：在可用的 MLGO 模型（如内联/寄存器分配策略）之间选择并验证。
- **两种触发模式**：
  - **轻量模式（`per_patch`，随普通流水线）**：只针对本次改动涉及的包，用本次 Benchmark 采集的 profile 刷新其 AutoFDO/BOLT 数据；无明显收益机会则 `no_further_gain` 直接放行；
  - **重量模式（`campaign`，优化专项流水线，§4.2.1 示例二）**：由开发者手动或按周期触发，可启用全部方法，面向一组模块做系统性优化。
- **优化候选的推荐与排序**：复用 Benchmark 的测量记录与异常分析体系，按预期收益、风险与影响范围对优化候选（包括平台轻量化候选）排序，优先尝试排名靠前者；每个候选的实际效果以 A/B 测量评估后回填，用于改进后续排序。
- **产物与回流**：优化结果（profile 文件、构建选项或 spec 变更）以 patch 形式提交 series candidate → `opt_patch_ready` 回流 Compiler RPM 阶段 → 重新出镜像 → **UT 重跑**（BOLT/AutoFDO 等可能引入功能问题）→ **Benchmark 重测并证明收益**；优化环有轮数上限。产出 OptimizationReport：采用的方法、前后对比、收益置信度、被放弃的尝试及原因。
- **发布**：profile 等文件最终进入各包自身仓库，属于发布行为——与普通 patch 同经人工审批 + broker，Optimization Agent 不持有任何提交凭据。

### 7A.5 Review Agent（本团队开发；外接知识库内容由业务部门提供）
- `mode: static`：镜像就绪后与 UT 并行，对 patch series 做静态审查；
- `mode: final`：汇合全部报告（Build / Image / UT / Bench / Optimization / 静态审查），产出最终 ReviewReport——逐段出处的 patch 说明、各阶段结论、缺失环节的显式标注。
- **外接知识库**：业务部门提供的审查规范、领域知识、历史问题等内容，以 KnowledgeProvider 实现接入（出生即带密级，D7），审查时与 CodeGraph、LLM Wiki、LogAnalyzer 经验库一并检索；知识库内容的维护与更新由业务部门负责。

### 7A.6 CI Agent（本团队开发）
- 只产出 ReleasePlan（发往何处、发布哪些对象、基于哪个版本、是否 squash），位于人工审批之前；审批对象即其规范化后的 ReleaseManifest；执行由 Release broker 完成（§8.3）。

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
- **Build Gateway 通道（v2.0）**：Build Gateway 为独立 OS 用户与独立 socket；业务 worker 不直连 Gateway——远程构建请求经编排进程的能力句柄转发（编排进程以连接上下文校验 run/task 归属后代为提交），Gateway 只接受编排进程 UID。
- **部署 provisioning 属交付物**（§10 deploy/）：系统账户创建、socket mode/ownership、Ledger 与凭据文件权限、多用户 spawn 的专用特权 launcher（属可信计算基）、服务启动顺序；P4 gate 含真实 UID/文件权限下的 E2E 隔离测试。

### 8.6 Build Gateway（框架交付，v2.0）
- 独立进程，**唯一持有 Quickbuild 会话**（VD 后接时同样承载 Perforce 会话）；不保存账号密码：会话失效时向运维发出告警，并在运维机器上弹出浏览器窗口，由运维本人登录；登录得到的会话仅保存在 Gateway 进程的受限存储中。
- 职责：提交远程构建（写入 run/task 标识）、查询状态、拉取日志与产物元数据、取消构建；全部操作记审计。
- 会话失效期间，依赖远程构建的节点进入外部等待（§4.3.1，不计预算、告警），其余节点不受影响；超过配置时长仍未登录 → 该节点 `sys.timeout`，按节点重试策略处理。
- 属可信计算基，与 Release broker 同等审计要求；不接受业务侧插件。

---

## 9. 可观测性
基于 Ledger/trace.jsonl 的只读本地 Web 视图（Run 状态、节点进度、循环计数、token 消耗、artifact 浏览、**板子池占用、镜像与远程构建队列、Benchmark 对比图表、优化前后对比**）；指标离线聚合。不引入外部观测平台。

---

## 10. 部署形态与仓库结构

**部署拓扑与网络边界（v2.0）**：

| 位置 | 部署内容 |
|------|---------|
| 内网主机（单机） | 编排进程、Approval 服务、Release broker、Build Gateway、MCP 服务（含 HTTP 端点）、Ledger 与存储、GBS 与 mic、各 Agent worker |
| 内网实验室网络 | 板子池中的测试板（RPi4 / RPi5 / 电视板），经 sdb 等连接 |
| 内网服务 | 内网 LLM、Quickbuild、gerrit、（后接）Perforce 与 Cosmos |
| 外网开发机 | Codex 开发与测试：全部外部依赖以 Fake 实现替代（FakeLLM、FakeBoardPool、FakeQuickbuild、FakePublisher），真实联调在内网执行；内网产物不外传 |

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
│   ├── resources/         # 构建后端(LocalGbs/Quickbuild 客户端/Fake)、ImageBuilder(mic)、SourceProvider、额度管理
│   ├── boards/            # 板子池：登记、能力探测、租约、刷机适配器接口、健康与静止判定、Fake
│   ├── stores/            # 镜像存储、基线镜像缓存、Profile 库
│   ├── gateway/           # Build Gateway（Quickbuild 会话、提交/查询/日志）
│   ├── approval/          # Approval 服务 + Review CLI
│   ├── release/           # Release broker + 官方 gerrit/github adapter + FakePublisher + 受限扩展接口
│   └── entry/             # MCP 服务 + HTTP 端点（同一操作契约）+ 配套 Skill 包
├── agents/
│   ├── skeletons/         # 六类 agent 可运行空壳 + producer/consumer fixtures
│   ├── compiler/          # Compiler Agent（LogAnalyzer 引擎；rpm/image 两模式）
│   ├── benchmark/         # Benchmark Agent（套件注册表、TPMS 适配器、脚本生成与有效性检查）
│   └── optimizer/         # Optimization Agent（AutoFDO/BOLT/CompilerGym 类/MLGO 方法插件）
├── conformance/           # 合规套件 + engine conformance + 本地 harness
├── pipelines/             # full_pipeline.yaml、optimize_campaign.yaml、compiler_only.yaml、compiler_bench_only.yaml
├── suites/                # Benchmark 套件注册表（内置 + 开发者提交，带版本）
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
DSL property/fuzz（随机图 → 校验器判定性质：可达环必有 budget、release 必经 hitl 等）；状态机 model-based 测试；**逐持久化边界故障注入**（每个 Ledger 提交点前后 kill，验证恢复与对账）；token 并发双消费测试；陈旧 series 进 gate/join 拒绝测试；checkpoint/execution manifest 不匹配拒绝恢复测试；artifact 损坏检测（digest 校验）与 blob 提交顺序逐点崩溃注入（孤儿 GC / dangling 索引对账）；control-plane IPC 权限隔离测试（worker socket 不可达审批/核销命令；跨 task 篡改拒绝；真实 UID/文件权限 E2E）；同 series 多轮循环下 join activation 分组与崩溃重放，含四组 model-based 断言——旧 activation 已首达后推进 series → stale 超时不误杀；同 series 并发多 activation 独立成组；不推进 series 的环（旧源已到达、环边采用、新 activation 成功、旧计时器后到 → 条件③已退役、无误杀）；父退役级联（嵌套子 activation 计时器同事务作废、不误杀，替代 cohort 继承父 scope 后参与外层 join）——及"分支内回环（不重经共同 fan-out）与跨祖先回环（先重经祖先 activation 的 fan-out）均拒绝加载"validator property；跨 attempt 三支定态 × 异参 claim 动作矩阵（succeeded/abandoned 放行新键、succeeded 不跨参复用、unknown 无新键、干净终态 failed 依类别策略放行）测试；publishing 终态映射 pending 组合（含 pending administrative finalize）故障注入与人工裁决 E2E（证据缺失拒绝、broker 未静默拒绝、迟到发布检出）；post-close correction（迟到检出、重复/并发修正、get_result 呈现）；effect_call_id 唯一性 conformance 与"双同参调用首成后崩溃、重试控制流变化"注入；probe-only / replay_safe / 皆无三类效应对账覆盖；join 作用域与共同到达 validator property（嵌套 fan-out、互斥 outcome、嵌套汇合重入外层三类反例）；恢复复用既有 dispatch 记录断言；publishing 期间进程重启/D12 漂移的对账优先注入；blob 上传与 GC 并发注入；编排进程崩溃且 GBS 子进程存活注入；六类 agent_type 的 contract producer/consumer fixture 兼容测试；**v2.0 追加**：即插即用组合测试（§2.4 表中每种删除组合加载校验通过/拒绝符合预期，降级报告标注正确）；release_requires 新鲜度测试（任一产 patch 节点推进 series 后，缺任一必需报告的审批提交被拒）；`input: none` 流水线生命周期；远程构建等待/会话失效/迟到结果归因（FakeQuickbuild）；板子池租约竞争、刷机失败下线、静止判定不通过重测；基线缓存命中/失效；生成型 Benchmark 套件未通过有效性检查或未确认时拒绝使用；Profile 陈旧拒用；优化环回流后 UT/Benchmark 重验证强制。conformance attestation：结果绑定 agent 制品 digest + contract/套件版本，digest 变更即失效，加载时校验。

---

## 12. 环境前提与 E0 预检
同 v0.1 表（gbs 工具链 / image URL / gerrit 探测 / CodeGraph / LLM Wiki / FakeLLM），**v2.0 追加**：mic 与镜像 ks 配置、Quickbuild 提交方式与会话登录流程、各板型刷机工具与连接方式、LogAnalyzer 调用形态——均为 `[待补充]` 环境事实，由负责人提供后进入 E0 预检；追加：Approval 服务与 broker 的本机进程部分无外部环境依赖、不进 E0 预检；**官方发布 adapter 的真实端点联调（gerrit/github 端点、凭据、目标仓权限）为独立上线 gate 材料**——开发与 P4 验收基于本地 API 模拟器/fixture，真实端点验证由负责人在受控环境执行（用例 07 提供），未通过前不得对生产目标发布。

---

## 13. 分期计划概览（细化见 09）

| Phase | 交付 | 完成 gate |
|-------|------|----------|
| P0 | 本 HLD v2.0 与总部对齐；01 按 v2.0 范围扩展并经三方评审 draft freeze；08/09 就绪 | 总部方案确认 + 三方 unanimous GO |
| P1 | EnginePort + engine/ + DSL v1 校验器/编译器（含 release_requires、input 规则）+ Run 状态机（含外部等待）+ Ledger 核心 + worker 调度 | mock agents：四份示例流水线与 §2.4 删除组合加载；逐边界故障注入恢复通过 |
| P2 | SDK（worker/side_effect）+ contracts + MCP 服务（含 HTTP 端点）与配套 Skill + control-plane RPC + Approval 服务 + Review CLI + Release broker + **Build Gateway 骨架** | conformance 骨架 + 授权并发/双消费 + RPC 权限隔离测试通过 |
| P3 | 公共模块（LLM 层+数据边界、Knowledge 三实现、context、evidence）+ **LocalGbsBackend（RPM + 全量 + mic）+ 板子池（Fake + 首个真实板型适配器）+ 镜像存储/基线缓存/Profile 库** + 官方 gerrit/github adapter | 真实 gbs 最小构建与镜像构建 + 数据边界 fail-closed + adapter 模拟联调通过 |
| P4 | 端到端：全量与子集流水线（mock 业务 Agent + 真实构建与镜像 + CLI 审批 + Fake/模拟器发布）+ deploy/ 资产 | §11.3 全部测试类别 + 真实 UID/权限 E2E = 框架完成 |
| P5 | **Compiler Agent**（LogAnalyzer 引擎，rpm + image(local)）+ 六类 fixture + 兼容矩阵 | contract v1.0（G6） |
| P6 | **QuickbuildBackend**（经 Build Gateway，Tizen） | 内网真实 Quickbuild 联调用例通过 |
| P7 | **Benchmark Agent**（套件注册表、TPMS 适配器、脚本生成与有效性检查、profile 采集）+ **Optimization Agent**（AutoFDO/BOLT 先行，复用增强版 llvm-profgen；CompilerGym 类与 MLGO 随后） | 真实板子上 A/B 测量可复现；优化环回流重验证闭合；至少一个模块实测收益 |
| P8 | **VD 适配**（PerforceSource + CosmosBackend） | VD 流水线端到端 |
| 并行 | UT / Review / CI Agent（本团队，自 P4 空壳与合规套件起步）；业务部门准备 UT 测试用例、外接性能测试用例与 Review 外接知识库内容 | 各自通过合规测试接入；首批业务内容接入 |

---

## 14. 风险登记

| # | 风险 | 检测信号 | 预防/恢复 | Owner |
|---|------|---------|-----------|-------|
| R1 | gerrit 不可达 | E0 探测 | fixture snapshot 降级 | 负责人 |
| R2 | 引擎恢复语义与实现偏差 | P1 故障注入 gate | side_effect 为硬前提（§4.1）；引擎替换经 EnginePort | 框架 |
| R3 | contract 脱离真实业务 | P5 消费失败 | D10 三条件 gate | 框架 |
| R4 | 真实构建拖慢迭代 | CI 时长 | fake 分层测试；真实构建仅 gate/nightly | 框架 |
| R5 | 内网大模型（经 ClineSR CLI）与 Fake 行为不一致；CLI 版本升级改变参数或输出格式 | provider 一致性测试（07 用例，内网执行）；CLI 版本纳入 execution manifest（D12） | 上线独立 gate；CLI 版本锁定，升级先过一致性测试 | 负责人 |
| R6 | 业务侧绕过 SDK/引擎约束 | conformance attestation 失效告警 | 能力句柄授权注入 + 准入 attestation（§5.1/§11.3）；承认运行时非全量强制 | 框架+业务 |
| R7 | 恶意/缺陷构建脚本外传或破坏（无全沙箱） | 内网出口监控（环境侧） | D13 来源受信假设；假设失效前置补沙箱 | 负责人 |
| R8 | 数据边界被自拼 payload 绕过 | conformance 误标检测 | D7 来源标注收窄面；残余承认 | 框架+业务 |
| R9 | 基线漂移致发布冲突（review 挂数日） | broker push 前远端检查 | 禁止自动 rebase；冲突 → fail_safe → 新 Run | 框架 |
| R10 | 磁盘耗尽/artifact 膨胀 | 水位检查 | 保留策略 + 拒新 Run 阈值（§7.5/§7.6.3） | 框架 |
| R11 | approval 服务不可用 | gate 等待超时告警 | Run 保持 paused；服务无状态重启（状态在 Ledger） | 框架 |
| R12 | 旧 checkpoint 配新版本 | D12 校验 | 拒绝恢复 → fail_safe，不在途迁移 | 框架 |
| R13 | publishing 滞留（broker 挂起/对账不可判定） | publishing 时长超阈值告警（计时豁免不含告警） | 运维 CLI 对账/裁决命令（交付项，入 09）人工处置 | 框架+负责人 |
| R14 | confirm_not_released 后迟到发布（在途请求无法绝对 fence） | 复查窗口周期 probe（窗口后并入常规审计对账）+ fencing 标识归因 | 告警 + post-close correction 记录（append-only，终态不可变，get_result 可见）；不静默 | 框架+负责人 |
| R15 | Quickbuild 不可用或会话频繁失效 | Gateway 会话状态与提交失败率告警 | 节点外部等待 + 运维登录；可切换本地后端（节点配置） | 框架+负责人 |
| R16 | 生成型 Benchmark 脚本"测错了东西" | 有效性检查（干跑两次、指标来源核对、离散度） | 未通过检查或未经人工确认不得入库使用 | 框架+开发者 |
| R17 | 优化引入功能问题（BOLT/AutoFDO 误编译） | UT 重跑失败、Benchmark 异常 | 优化环强制回流 UT；release_requires 强制新鲜 UT 报告 | 框架 |
| R18 | Profile 与代码版本漂移导致优化失效或劣化 | Profile 新鲜度检查 | 陈旧拒用、请求重新采集；收益须 A/B 实证 | 框架 |
| R19 | 板子争用、刷机失败、板子状态波动 | 租约排队时长、刷机失败计数、静止判定失败率 | 独占租约 + 失败下线 + 静止判定 + 交叉测量 | 框架+负责人 |
| R20 | 镜像构建耗时与磁盘占用 | 镜像队列时长、磁盘水位 | 基线缓存复用、廉价前置检查先行、镜像保留策略、镜像构建并发 1 | 框架 |
| R22 | AI 分析误报（异常原因、优化候选判断错误） | 试点期准确率与误报率统计 | 判定与 AI 分离（判定只用 SPEC 与统计规则）；AI 输出标注为初稿并经人确认；试点达标后再扩大 | 框架+负责人 |
| R21 | VD 接入时源码模型差异超出适配层预期 | P8 前置评估 | SourceProvider/构建后端抽象首期即按 shelve CL 形态验证可容纳 | 框架 |

---

## 15. 附录
- A1 术语表：§3。
- A2 `[待补充]`：gbs.conf、gerrit 探测方式、ClineSR CLI 调用参数（非交互模式、关闭工具、输出格式）、CodeGraph/LLM Wiki 仓库地址；v2.0 追加：mic 镜像 ks 配置、Quickbuild 提交方式与登录流程、各板型刷机工具与连接方式、LogAnalyzer 调用形态、TPMS 适配接口。
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

- A17 v2.0 补充（总部方案沟通输入）：Coding Agent 接入改为"Skill 调用框架 MCP 服务"（HTTP 端点保留给脚本与测试，同一契约）；LLM 接入第一阶段经 ClineSR CLI（不依赖 LLM API）；新增 §7A.0 各 Agent 的 AI 能力与使用原则（判定与 AI 分离、试点先行、数据边界、可追溯）；Benchmark 增加全量/单项/快速三种测量模式、一次完整记录（指标、区间、资源、日志）无需重测、业务部门 SPEC 的 SPEC-IN/OUT 判定、统计判定标准、自动测量报告（含 AI 初稿）、跨部门用例共享；Optimization 增加优化候选的推荐与排序；目标 G11；风险 R22；全文"单测"统一为"UT 测试"，UT Agent 定位为板上稳定性测试；交付分工调整为六类 Agent 均由本团队开发，业务部门提供 UT 测试用例、外接性能测试用例与 SPEC、Review 外接知识库内容。
- A16 v1.0-draft-frozen → v2.0 变更摘要（范围扩展，冻结核心语义原样保留）：七角色协作（新增 Optimization Agent）；Compiler Agent 两模式两节点（rpm / image）与可插拔构建后端（LocalGbs：增量 RPM、全量 + mic；Quickbuild 经 Build Gateway；VD Cosmos 后接）；LogAnalyzer 作为 Compiler 分析引擎与第三个知识源；可配置 Benchmark（三种套件来源、生成脚本有效性检查 + 人工确认、A/B 对基线、静止判定、profile 采集）；Optimization Agent（AutoFDO / BOLT / CompilerGym 类 / MLGO 方法插件，轻量与专项两种触发，强制回流重验证）；即插即用显式保证（§2.4）与交付边界（§2.5）；新增决策 D14–D21，D11 补充长等待不占执行槽；新 DSL 规则 release_requires 与 input；新示例流水线（全流程、优化专项）；板子池、镜像存储、基线镜像缓存、Profile 库、SourceProvider；Build Gateway（§8.6）与对应 IPC 通道；部署拓扑与网络边界；§11.3 追加测试类别；分期重排为 P0–P8；风险 R15–R21。

## 16. 附录 B：[01] 待落清单汇总（01_Contract_Spec 编写骨架）

正文 18 处 `[01]` 标注的已定案项，按 01 章节归组：
1. **DSL 与静态校验**：pipeline YAML 完整 schema（nodes/routes/loops/joins/gates/terminal success_on）；校验规则形式化（§4.2.6 全部规则，含共同到达性三条件、环边双约束、join 作用域/划分、支配性检查）；target_spec 语义。
2. **状态机与消息**：Run 状态机命令/guard 表（含 publishing、administrative finalize、post-close correction）；TaskInput/HandoffResult/各 Report/RunContext/ReleasePlan/ReleaseManifest（规范化算法）/授权记录/Run 终局摘要与 correction 记录 schema；join_inputs 形态；MCP 工具与 HTTP 端点的请求/响应消息与错误语义。
3. **activation 与 series**：activation 传播定义（根/父子关系/替代 cohort 继承）；series lineage 与 tree_digest 算法；陈旧性判定细则。
4. **效应幂等**：effect 记录六态迁移/查找矩阵与版本化；effect_call_id 唯一性细则与 sys.invalid_result 归类；effect_class 注册与能力声明（probe/replay_safe）契约；恢复协议逐支细则。
5. **安全接口**：control-plane 命令集（数据面枚举、审批/核销、裁决、correction）；受限扩展 adapter 的操作描述与凭据原语契约；数据密级标注与传播规则。
6. **conformance**：§11.3 全部测试类别的用例级定义与判定标准（07 引用）。
7. **v2.0 扩展项（01 v0.11 需同步扩展）**：Compiler 两模式的 status 全集与 ImageReport；BenchReport 扩展字段与 Benchmark 套件描述 schema（含生成型套件的有效性检查记录与确认记录）；OptimizationReport 与优化计划；Profile 引用与新鲜度；image_ref 与基线缓存键；DSL 新字段 `input`、`release_requires` 及其静态/运行时规则；外部等待的状态与计时细则；Build Gateway 命令集与 IPC 通道；板子池租约/刷机/探测接口；新增效应类别（镜像构建、远程构建、profile 采集）的 probe 契约；空发布计划的处理；SourceProvider 接口；四份示例流水线作为校验器验收用例。

## 17. 附录 A15：勘误记录（冻结后经三方评审通道生效）
- **E-01（HLD-Q1 → 01 V-13b）**：§4.2.6 校验规则集追加——release-approval 型 hitl 须存在支配它的 ReleasePlan 生产节点（按 Agent 注册 produces 声明判定，支配链最近者，同深歧义拒绝加载）。缺陷由 01 首轮评审（Claude Code）登记为 HLD-Q1；形式化定义在 01_Contract_Spec §1.3 V-13b；**01 第二轮复审中三方对规则与生效程序双表态一致 GO，勘误生效**。本条为规则集的静态加严，不触碰任何运行时语义。单一事实源：规则精确文本以 01 V-13b 为准。
