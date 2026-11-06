# 00 — Multi-Agent Framework 高层设计（HLD）

**版本**: v2.10（最终版 HLD 候选）——在 v1.0-draft-frozen（含勘误 E-01）基础上的范围扩展版；v2.0 首轮三方评审后修订为 v2.1，按项目负责人六项裁决修订为 v2.2，第二轮三方评审（Kimi GO / Claude Code NO-GO / Codex NO-GO）后修订为 v2.3，第三轮三方评审（Kimi GO / Claude Code NO-GO / Codex NO-GO）后修订为 v2.4，第四轮三方评审（三家均 GO，余 MINOR / NIT）后修订为 v2.5，第五轮定向复审（Kimi / Claude Code GO，Codex NO-GO 1 MAJOR）后修订为 v2.6，第六轮定向复审（Kimi / Claude Code GO，Codex NO-GO 1 MAJOR）后修订为 v2.7，第七轮定向复审（三家均 GO，余 MINOR / NIT）后修订为 v2.8，第八轮收尾核对（Kimi / Claude Code GO，Codex 对 D23 落地 NO-GO）后修订为 v2.9，第九轮收尾核对（三家 HLD 部分均 GO，余 D23 的 MINOR / NIT）后修订为 v2.10
**状态**: HLD 主体已连续两轮三家 GO；v2.9 补 D23（不得引入 PHP）的范围定义与检查方法，v2.10 只补 D23 的误报分类、主机扫描口径与例外规则，其余未改；GO 后作为与总部对齐及开发的基线。**v1.0 已冻结的核心语义（编排、Ledger、效应幂等、审批与发布、特权 IPC、安全模型）未作任何放宽**；v2.0 范围扩展**对冻结核心的两处扩展**——外部等待（D11）与 worker 数据面命令扩充——**以勘误 E-02 / E-03 登记于附录 A15（§17），随本 HLD 三方评审 GO 生效**，规则文本以本文 §4.3.4、§8.5 为准；另新增**特权构建隔离（D22）**，属安全收紧。本版新增内容集中在：构建两阶段（RPM → 镜像）与可插拔构建后端、Compiler Agent 以 LogAnalyzer 为分析引擎、可配置 Benchmark（含版本化判定策略）、优化 Agent（AutoFDO / BOLT / CompilerGym 类 / MLGO）、板子池、基线镜像缓存、即插即用的显式保证、源码接入抽象（Tizen 先行、VD 后接）、部署与网络边界。变更清单见附录 A16（v1.0→v2.0）、A18（v2.0→v2.1）、A19（v2.1→v2.2）与 A20（v2.2→v2.3）
**读者**: 总部方案评审方、框架开发（Codex）、cross-reviewer（Kimi / Codex / Claude Code）、提供测试用例与知识库内容的业务部门
**关联文档**: 01_Contract_Spec（v0.20，上游仍为 v1.0 冻结版 + E-01；按本版范围同步扩展见附录 B 第 7 组）、02–06_Agent_Design_Guide、07_Conformance_and_Onboarding、08_Codex_Dev_Guide、09_Phased_Dev_Plan、docs/review/ 下 v0.1–v0.11 十一轮处置表、HLD_v2.0、HLD_v2.2、HLD_v2.3、HLD_v2.4、HLD_v2.5、HLD_v2.6、HLD_v2.7、HLD_v2.8 与 HLD_v2.9 处置表；Quickbuild 业务逻辑调查 docs/research/quickbuild_business_logic.md

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
- G10 **测量—优化闭环**：优化手段以插件注册（AutoFDO、BOLT、CompilerGym 类搜索、MLGO 策略），优化产物强制回流重新验证，收益须经"优化前 vs 优化后"A/B 按确定性策略证明，否则撤销（§7A.4）；
- G11 **AI 接入职责明确、判定与 AI 分离**：每个 Agent 的 AI 能力有明确分工（§7A.0）；是否达标、是否回归由 SPEC 与版本化统计策略判定，判定字段由框架统计库确定性计算，AI 负责分析、生成与建议；AI 方案以每轮测试结果检验（验证资产受保护）并在审批前以多版本对比报告呈现，分析类输出恒为 AI 初稿，准确率只在有事实标签的样本上统计。

### 1.3 非目标（Non-goals）

- N1 分布式多机部署（MVP 单机；单机自我保护不豁免，见 §7.6.3 资源额度）；
- N2 多租户与配额系统；
- N3 学习型 LLM 路由（沿用 static → rule → cascade，见 §7.1）；
- N4 通用工作流引擎（只覆盖本领域 pipeline 形态：显式声明的有界循环 DAG + gate）；
- N5 多语言 SDK（仅 Python）；
- N6 Coding Agent 本体实现（框架只提供 MCP 服务与配套 Skill）；
- N7 完整容器级安全沙箱（信任模型与残余风险见 §8.1、§14 R7；凭据隔离不在此豁免范围，由 broker / Gateway 进程隔离保证；**以 root 执行半可信内容的构建步骤不在此豁免范围**——OS 用户隔离对 root 无效，此类步骤一律在独立内核边界内执行，D22）；
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
| D11 | 并发模型 | MVP：**单执行 Run**（执行槽 = 持有 worker/资源执行中；paused 不占执行槽、可多 Run 并存，resume 与新 Run 同入 FIFO 队列）；Run 内节点级并行；task 以子进程 worker 执行；资源经信号量额度管理（§7.6.3）；Ledger 直写者唯一（编排进程，其余经 control-plane RPC）。**勘误 E-02（外部等待，§4.3.4）**：外部等待（远程构建、资源排队）期间**不存在任何 worker**——资源租约在分派前由编排授予（未获授予的 dispatch 不 spawn worker），远程构建提交后 task 以框架保留结果挂起本 attempt、编排登记外部等待项、结果到达后经 wake outbox 对**同一 dispatch** 续接；Run 仅剩等待项（gate ∪ 外部）且无可运行/在飞本地工作时迁 paused 并释放执行槽；锁序 = 先资源租约、后执行槽 | 单机资源与 SQLite 约束下最小正确模型；镜像与远程构建耗时长，不能独占执行槽；任何 worker 不跨越等待存活，冻结的 worker/task 模型（hard-kill、心跳、孤儿回收）不变 |
| D12 | 执行环境固化 | Run 创建时固化 execution manifest：pipeline digest、contract 版本、框架版本、agent 制品 digest、provider 配置 digest、引擎版本；task dispatch / 审批 / 发布前复核相关 digest；恢复时不匹配走 ledger 级 administrative finalize（§4.3.3），不做在途迁移；provider 配置 digest 含策略语义与 **端点身份/信任策略**（仅凭据值除外——密钥轮换不影响恢复，端点改向则触发不匹配）。**v2.0 扩展字段**（同一复核规则）：`llm_cli_version`（ClineSR CLI 版本）、`bench_suites_digest`（套件注册表在 Run 创建时的完整快照摘要；本 Run 实际所选套件是该快照与目标范围的确定性函数，范围按 §7A.7 增长不构成失配）、`spec_digest`、`bench_policy_digest`、`module_registry_digest`（Run 创建时 pin 的登记表快照，§7A.7）、`build_input_closure_digest`（§7.8）——均直接影响判定或产物，Run 中途变化按 D12 失配处理 | 官方明示 interrupted thread 不支持拓扑变更（节点改名/删除）、state 不兼容变更有风险；逐类推理迁移安全性的成本与出错面大于一律拒绝 |
| D13 | 信任模型 | 内网单机单操作员；patch 来源限于经认证的 Skill 调用方；构建脚本、**Benchmark 开发者脚本与生成脚本**视为半可信（见 §8.1）；Benchmark 脚本只在测试板上执行，宿主侧的**结果解析规则限声明式**（正则 / JSON path，不执行代码）；套件以内容 digest pin 入注册表 | 沙箱深度与威胁模型匹配（N7）；新增的可执行内容来源逐一列明准入方式 |
| D14 | 即插即用 | 业务 Agent = entry-point 插件；流水线组成 = YAML；Agent 间无直接依赖（只经 Contract 交换 Report）；删除/替换任一业务 Agent 由静态校验器判定合法性，上游缺失按 optional 降级并在报告中显式标注（§2.4）——**`release_requires` 清单不降级**：清单内报告缺生产者即拒绝加载，校验器不自动删减清单 | 各业务团队独立演进；试用子集流水线零代码；发布前验证的取舍必须显式 |
| D15 | 两阶段构建与构建后端 | Compiler Agent 两种模式：`rpm`（本地 GBS 增量，受影响包 + 反向依赖闭包）与 `image`（后端可选：`local` = GBS 全量 + mic 出镜像；`quickbuild` = 经 Build Gateway 提交远程构建）；两模式作为两个节点出现在流水线中，均可单独删除。**修复回流定案**：任何产出修复 patch 的 task（Compiler 两模式、UT、Optimization）提交唯一 series candidate 后即以 `*_fix_patch_ready` / `opt_patch_ready` 结束，由声明环重派——成功报告只由"未提交 candidate 的 task"产出，因而必然绑定其实际验证过的当前 series。镜像节点以 `rpm_precheck: required\|independent`（缺省 required）声明是否要求当前 series 的成功 BuildReport（§7.6.1） | 快速修复与完整镜像分离；报告与 series 的冻结绑定不放宽 |
| D16 | 编译问题分析引擎 | Compiler Agent 的分析与修复引擎 = LogAnalyzer（含团队编译问题经验知识库）；框架经适配接口调用；修复规则沿用 LogAnalyzer 既有约定：最优方案进 patch，另附两个备选方案入报告；真实缺陷直接修复，不以屏蔽告警选项绕过 | 复用已验证能力与经验库，不重复建设 |
| D17 | Benchmark 可配置 | 套件注册表，来源三种：内置套件（含 TPMS 适配）/ 开发者脚本 / 开发者描述用例 → Agent 生成脚本 → 有效性检查 + 人工确认一次（本机特权通道，不经 MCP）后入库；统一结果格式；A/B 对比基线镜像；**判定策略 BenchPolicy 随套件版本固化、缺省值定案**（§7A.3），判定字段由框架统计库从测量记录确定性计算；测量科学性复用 TPMS 做法（重复、交叉、板子静止判定） | 套件持续增长不改 Agent 代码；杜绝"测错东西"；同一数据不同实现必须得出同一判定 |
| D18 | 测量—优化闭环 | Optimization Agent 以优化方法插件组织（AutoFDO、BOLT、CompilerGym 类、MLGO）；两种触发：随 patch 的轻量模式与独立优化专项流水线的重量模式；优化产物以 patch 形式提交，**必须**回流 Compiler → UT → Benchmark 重新验证——**由校验器按路径强制**（§4.2.6 规则③），含优化节点的流水线不得从 `release_requires` 移除镜像/UT/Benchmark 报告；收益以"优化前 vs 优化后"A/B 按 BenchPolicy 判定，非收益候选必须以撤销 patch 退出（§7A.4）；发布仍经人工审批与 broker | 优化不得引入功能回归；收益须实测证明；"删 Agent"不得成为绕过优化重验证的途径 |
| D19 | 板子与镜像资源 | 板子池（BoardPool）由框架交付：独占租约（带单调 generation，回收须经静默/复位）、刷机、健康检查、能力探测（PMU/SPE/BRBE 等）、确定性静止判定；基线镜像按**构建输入闭包**缓存复用（§7.8）；Profile 库首期以兼容字段完全匹配判定新鲜度；**跨 Run 共享存储对业务 worker 只读**，权威状态在 Ledger（D6） | UT/Benchmark/profile 采集共享板子，不能各管各；基线不重复构建；共享内容不可被半可信进程投毒 |
| D20 | 源码接入 | SourceProvider 抽象：首期 Git/Gerrit（Tizen）；VD 的 Perforce + shelve CL 与 Cosmos 后端作为适配层后接；patch series 模型对两者统一。**范围说明**：现行 tree_digest（git tree 组合）与发布 fencing（Change-Id/commit 标识）为 git 形态，P8 接入 Perforce 时须对二者做 VCS 中立化，届时以勘误通道修订，首期不预先抽象 | Tizen 先行、VD 后接；不为未接入的 VCS 过度设计 |
| D21 | 外部构建凭据 | Quickbuild 的 SSO 会话只存在于框架 Build Gateway 独立进程；会话失效时由运维在弹出的浏览器窗口中登录，经运维会话通道注入 Gateway 并校验会话主体为配置的服务账号（§8.6），框架不保存账号密码；业务 Agent 经能力句柄（编排转发）提交，拿不到会话 | 与 D8 同一原则：凭据集中于可信小进程 |
| D22 | 特权构建隔离 | 凡以 root 执行来自 snapshot/series 内容的构建步骤（mic create 中的 RPM scriptlet 与 ks %post、GBS buildroot 的 sudo 段，增量与全量同等）一律在**独立内核边界**内执行：首选同机**一次性构建 VM**（KVM），E0 不具备虚拟化能力时改用**独立构建主机**（不提供宿主 root 直跑降级）。**两种形态的共同契约（v2.3）**：① 每次构建自框架构建的**不可变基底**（内容 digest 登记）启动，可写层一次性、构建后丢弃——独立构建主机须在每次构建前复位（不可变根 + overlay 重置，或重新部署），无法复位的主机不得承担构建；② 跨构建复用的状态（buildroot 包缓存等）只能由框架自有 task 以锁定输入生成，按构建输入闭包键**只读**挂载；③ 边界内无凭据、无 Ledger、无任何 control-plane socket；④ 基线构建（`sys.baseline_build`）与 series 构建不共用同一边界实例；⑤ 产物经只读导出通道交回，附基底 digest，由 launcher 导入镜像存储并复验入库（§7.6.1、§7.8）——root 执行的恶意 scriptlet 既拿不到凭据，也无法驻留下来污染之后的构建与跨 Run 共享的基线 | 凭据隔离依赖 OS 用户/文件权限，对 root 无效；LLM 生成的 patch 可经间接提示注入产出恶意 scriptlet（§8.1） |
| D23 | 不得引入 PHP（项目负责人前提，v2.8；v2.9 补范围定义与检查方法；v2.10 补误报分类、主机扫描口径与例外规则） | 本产品**不得引入 PHP**。**范围按引用定义**：§2.5 中"本团队开发"的全部部件（含板子池、基线镜像缓存与 Profile 库的实现、BenchPolicy 统计库、构建隔离边界的 launcher 与构建 VM 镜像）、§10 部署拓扑中本产品部署的全部内容（含 Review CLI、运维 CLI、MCP 服务、开发者侧 Skill、Approval 服务、Release broker 与官方发布 adapter、Build Gateway 与运维登录助手、只读 Web 视图及其前端、板型适配器及本产品下发到测试板上运行的能力探测与采集脚本）、测试夹具，以及它们的运行时依赖闭包；**由 deploy 安装在本产品主机、构建隔离边界与运维机上、并由本产品进程调用的第三方工具及其依赖**（ClineSR CLI、gbs / mic、LLVM / BOLT 工具链、CompilerGym 类工具、LogAnalyzer、sdb 等）属于运行时依赖闭包——若某内网工具自身依赖 PHP，E0 预检报告，由负责人决定换型；**该报告与任何"例外需求"记录都不是部署或注册许可**——在负责人正式修订本条前提之前，命中仍按 §11.2 拒绝、不签发合规 attestation。负责人若修订前提批准某项例外，例外以登记条目（工具名、安装件 digest、所依赖的 PHP 组件、理由、批准人、到期日）进入门禁的例外清单，只豁免该 digest，digest 变化、到期或依赖消失即失效，并随 E0 预检报告与 attestation 呈现。业务接入的扩展同样受约束：Agent 插件、受限模式的业务发布 adapter（§8.3）在注册时声明运行时**并经制品内容与运行环境闭包扫描**（§11.2），任一命中 PHP 即拒绝注册；Benchmark 外接套件的宿主侧解析规则只接受声明式格式（§7A.3），不得引用可执行脚本。**不在范围内**：本产品经网络接口对接的外部系统（Quickbuild、gerrit、github、Cosmos 等）的实现语言；业务部门提供、只在测试板上执行的测试用例脚本（同一脚本若改为宿主侧执行即在范围内）；**本产品处理的业务内容**——被测业务源码、按业务 spec 装入 buildroot 的构建依赖、产出的 RPM 与镜像、基线镜像缓存条目、Profile 数据（它们是数据而非交付物，门禁不扫描其内容）。产品自带的 Web、运维或宿主侧适配组件不得以"外部"名义豁免。 |

### 2.3 与外部系统的关系

| 外部系统 | 关系 | Codex 开发期处理方式 |
|---------|------|---------------------|
| Coding Agent | 框架外，经 Skill 调用框架 MCP 服务（§6.5） | 框架实现 MCP 服务 + 配套 Skill + 模拟客户端；ClineSR 与 Codex 均可作客户端联调 |
| 人工 Reviewer | 经 Review CLI 操作 Approval 服务（§8.2） | 框架交付 CLI 与服务，Codex 可本地全流程测试 |
| CodeGraph / LLM Wiki | KnowledgeProvider 实现 | 开源仓库本地部署真实联调 |
| 内网大模型（经 ClineSR CLI） | 第一阶段唯一的生产 LLM provider：框架经 ClineSR CLI 调用内网大模型（§7.1） | FakeLLMProvider（fixture 驱动、接口一致）；内网联调用真实 ClineSR CLI |
| build server (GBS) | 本地构建后端（RPM 增量、全量）；sudo 段在构建隔离边界内执行（D22） | 本机真实 gbs（gbs.conf 已定可用）`[E0 预检]`；开发期允许在开发机直接运行（开发机无生产凭据），生产部署强制隔离 |
| mic | 本地镜像构建（全量构建产物 → 镜像）；在构建隔离边界内执行（D22） | 本机真实 mic + 镜像 ks 配置 `[待补充]`；生产部署经构建 VM / 独立构建主机 |
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
| Benchmark | 不做性能评估 | 同时去掉阈值 gate 与 Optimization（二者以 Benchmark 结果为必需输入，校验器会提示）；含发布时须在 `release_requires` 中移除 `bench_report` |
| UT | 不做板上UT 测试 | 去掉 UT 修复环；同时去掉 Optimization（含优化节点时 UT 不可删，§4.2.6 规则③）；含发布时须在 `release_requires` 中移除 `ut_report` |
| Compiler（镜像模式） | 只出 RPM、不出镜像 | 同时去掉依赖镜像的 UT/Benchmark/Optimization；含发布时须在 `release_requires` 中移除 `image_report`、`ut_report`、`bench_report` |
| Review | 不做 AI 汇总审查 | 人工审批仍可凭各 Report 证据链进行 |
| CI / 发布段 | 只验证、不发布 | 末端改为 terminal 节点（成功条件显式声明）；`release_requires` 随 release 节点一并删除 |

**通则**：删除任何报告生产者时，`release_requires` 必须由配置者**显式**修改——清单内保留某类报告而图中无其生产者一律拒绝加载，校验器不自动删减；删减后的清单写入 ReleaseManifest 并在审批 CLI 首屏呈现"本次未执行的验证类别"（§4.2.6 规则①）。保留 Optimization 时，其强制重验证路径上的节点与报告不得删除（规则③）。

随仓流水线示例：`full_pipeline.yaml`（全流程，§4.2.1）、`optimize_campaign.yaml`（优化专项，§4.2.1）、`compiler_only.yaml`（只编译+出镜像，§4.2.1 示例三）、`compiler_bench_only.yaml`（编译+Benchmark，§4.2.1 示例四）。

### 2.5 交付边界

| 部件 | 提供方 |
|------|-------|
| 框架（编排、SDK、Contract、公共模块）、Approval 服务、Release broker、官方 gerrit/github adapter、Build Gateway（含运维登录助手）、板子池、基线镜像缓存、Profile 库、BenchPolicy 统计库、构建隔离边界（launcher 与构建 VM 镜像）、部署资产 | 本团队开发 |
| 全部六类 Agent：Compiler（LogAnalyzer 为分析引擎）、UT、Benchmark（套件机制 + TPMS 适配）、Optimization（AutoFDO/BOLT 先行，CompilerGym 类与 MLGO 随后）、Review、CI | 本团队开发 |
| UT 测试用例；模块登记表内容（模块 ↔ 包、用例集、套件、`always_run` 冒烟集，§7A.7） | 业务部门提供 |
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
| **基线镜像** | 同一 snapshot、同一构建输入闭包、不含本次 patch 的镜像；Benchmark A/B 对比的参照；按缓存键复用（§7.8） |
| **外部等待项（ExternalWait）** | 编排侧 Ledger 记录，与 gate 等待项同构：资源排队（板子、本地镜像构建额度、远程构建配额、基线镜像就绪）或远程构建在途；等待期间无 worker 存活，结果经 wake outbox 续接同一 dispatch（§4.3.4，勘误 E-02） |
| **构建隔离边界** | 以 root 执行半可信构建内容的独立内核环境：一次性构建 VM 或独立构建主机（D22） |
| **BenchPolicy** | 随 Benchmark 套件版本固化的判定策略：样本量、估计量、区间与检验方法、多指标校正、方向归一、SPEC 三值判定规则（§7A.3） |
| **测量记录（MeasurementRecord）** | 一次测量的完整原始记录（指标样本、区间耗时、资源时间序列、日志、板子与静止判定记录），内容寻址 artifact；判定字段由框架统计库从中确定性复算 |
| **目标范围（focus scope）** | 本 Run 验证与优化所围绕的模块集合：首次 submit_patch 时按改动涉及的模块 ∪ 开发者声明的关注模块确定（`input: none` 时为必填的目标模块），之后随 series 实际改到的已登记模块只增不减。UT、Benchmark、Optimization 只围绕该范围工作（§7A.7） |
| **series_effect** | Agent 按 mode 为每个业务 status 注册的 series 语义：`advances`（本 task 已提交 candidate）/ `asserts_nonempty`（断言当前 series 相对 snapshot 有净变更，即 tree_digest ≠ 初始空 series 的 tree_digest）/ `none`；运行时强制（§4.2.6 规则②、§5.1.1） |
| **板子池（BoardPool）** | 框架交付的测试板管理：登记、能力探测、独占租约、刷机、健康检查、静止判定（§7.7） |
| **Benchmark 套件** | 一组可重复执行的测量用例 + 结果解析规则 + 版本号；来源为内置 / 开发者脚本 / 开发者描述用例自动生成（§7A.3） |
| **Profile** | 板上运行采集的性能剖析数据（如 perf 采样），供 AutoFDO/BOLT 使用；存于 Profile 库，按方法插件声明的兼容字段完全匹配判定新鲜度（§7.8） |
| **优化方法插件** | Optimization Agent 内可注册的优化手段（AutoFDO、BOLT、CompilerGym 类搜索、MLGO 策略）（§7A.4） |
| **无输入流水线** | 声明 `input: none` 的流水线（如优化专项），snapshot pin 与初始空 series 同事务签发后进入排队、不等待 Coding Agent 的 patch（§4.2.6） |
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

#### 4.2.1 结构与示例（四份示例即校验器验收用例，必须可通过校验）

**示例一：全流程（`full_pipeline.yaml`）**

```yaml
pipeline: full_pipeline
dsl_version: 1            # DSL schema 版本，纳入 Contract 版本体系
input: patch              # 需要 Coding Agent 提交 patch（缺省值）
nodes:
  compile_rpm:    { agent_type: compiler, mode: rpm }          # 本地 GBS 增量：受影响包 + 反向依赖
  compile_image:  { agent_type: compiler, mode: image,
                    config: { backend: local, rpm_precheck: required } }   # local = GBS 全量 + mic；可改 quickbuild
  ut:             { agent_type: ut }
  benchmark:      { agent_type: benchmark,
                    config: { suites: auto, mode: full, collect_profile: true } }   # auto = 按本 Run 目标范围从模块登记表选套件（§7A.7）
  optimize:       { agent_type: optimizer, mode: per_patch,
                    config: { max_opt_rounds: 1 } }            # 轻量模式：只针对本次改动涉及的包
  bench_gate:     { gate: threshold, metric: benchmark.regression_pct,
                    op: "<=", value: 5.0 }                     # 只认 gate_eligible 报告；缺指标 = fail-closed
  review_static:  { agent_type: review, mode: static }
  review_final:   { agent_type: review, mode: final }
  ci_plan:        { agent_type: ci }                           # 产 ReleasePlan（位于人工审批之前）
  human_review:   { gate: hitl }                               # 审批对象 = ReleasePlan 规范化的 ReleaseManifest
  release:        { broker: release }                          # 特权终局节点，outcome 集固定（4.2.5）
entry: compile_rpm
release_requires: [build_report, image_report, ut_report, bench_report]   # 发布前必须针对当前 series 存在且结论为通过（4.2.6）
loops:
  - id: rpm_fix_loop
    edges: [ { from: compile_rpm, to: compile_rpm } ]         # RPM 阶段修复：提交修复 patch 后重派、在新 series 上重新构建
    budget: { max_rounds: 3, max_wall_clock_min: 480 }
  - id: image_fix_loop
    edges: [ { from: compile_image, to: compile_rpm } ]       # 镜像阶段发现的编译问题回流修复
    budget: { max_rounds: 2, max_wall_clock_min: 480 }
  - id: ut_fix_loop
    edges: [ { from: ut, to: compile_rpm } ]
    budget: { max_rounds: 2, max_wall_clock_min: 480 }
  - id: opt_loop
    edges: [ { from: optimize, to: compile_rpm } ]            # 优化产物必须回流重新编译、重新验证
    budget: { max_rounds: 2, max_wall_clock_min: 720 }        # 校验器强制 ≥ 2 × max_opt_rounds（每个候选至多一次提交 + 一次撤销）
run_budget: { max_wall_clock_min: 2880 }
joins:
  - id: pre_final_review
    wait_for: [bench_gate, review_static]
    timeout_min: 1440                                         # 自首个到达起算；超时 → fail_safe + 超时报告，绝不触发下游（§4.3.5）
    to: review_final
routes:
  - { from: compile_rpm,   on: build_passed,             to: compile_image }
  - { from: compile_rpm,   on: build_fix_patch_ready,    to: compile_rpm }
  - { from: compile_rpm,   on: build_failed_exhausted,   to: fail_safe }
  - { from: compile_image, on: image_ready,              to: [ut, review_static] }   # 镜像就绪后 UT 与静态审查并行
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

流程说明：本地 RPM 构建（需要修复时提交修复 patch 并结束本 task，由 rpm_fix_loop 在新 series 上重新构建，直至构建通过）→ 出镜像（镜像阶段的编译问题回流 RPM 阶段修复）→ 镜像就绪后**并行**开始板上UT 测试与静态审查 → UT 测试通过后跑 Benchmark（按本 Run 目标范围选套件，与基线镜像 A/B，顺带采集 profile）→ Optimization 判断是否有优化机会：有则产出优化 patch 回流重新编译、重新UT 测试、重新测量，并对"优化前 vs 优化后"做 A/B，无收益即撤销（§7A.4）；没有更多收益则进入阈值判定 → 与静态审查汇合后做汇总审查 → 生成发布计划 → 人工审批 → 发布。四个环均有轮数与时长上限。汇合点只在两路都到齐（同一 activation、同一 series）时触发下游；**汇合超时一律路由 fail_safe 并产出超时报告，绝不当作通过继续**（§4.3.5）——因此 ut、benchmark 按"汇合必经"定义（§4.2.6 规则①）必经 human_review。

**示例二：优化专项（`optimize_campaign.yaml`，开发者手动或按周期触发，不需要 Coding Agent 的 patch）**

```yaml
pipeline: optimize_campaign
dsl_version: 1
input: none               # 创建即排队，不进入 awaiting_patch
nodes:
  compile_rpm:    { agent_type: compiler, mode: rpm }
  compile_image:  { agent_type: compiler, mode: image,
                    config: { backend: local, rpm_precheck: independent } }   # 首轮无 RPM 结果，直接全量构建当前 snapshot+series
  ut:             { agent_type: ut }
  benchmark:      { agent_type: benchmark, config: { suites: auto, mode: full, collect_profile: true } }   # 按 create_run 给出的目标模块选套件
  optimize:       { agent_type: optimizer, mode: campaign,
                    config: { methods: [autofdo, bolt], max_opt_rounds: 2 } }   # 重量模式：可启用 compilergym / mlgo
  report_no_gain: { agent_type: review, mode: final, terminal: true,
                    success_on: [review_report_ready] }      # 无可发布内容：出测量与分析汇总后 succeeded 关闭，不进审批
  review_final:   { agent_type: review, mode: final }
  ci_plan:        { agent_type: ci }
  human_review:   { gate: hitl }
  release:        { broker: release }
entry: compile_image      # 首轮直接以当前 snapshot 出镜像并测量
release_requires: [image_report, ut_report, bench_report]   # 含优化节点：三者不可省略（规则③）
loops:
  - id: rpm_fix_loop
    edges: [ { from: compile_rpm, to: compile_rpm } ]
    budget: { max_rounds: 3, max_wall_clock_min: 480 }    # ≥ 1 + max_opt_rounds（规则③）
  - id: image_fix_loop
    edges: [ { from: compile_image, to: compile_rpm } ]
    budget: { max_rounds: 3, max_wall_clock_min: 480 }
  - id: ut_fix_loop
    edges: [ { from: ut, to: compile_rpm } ]
    budget: { max_rounds: 3, max_wall_clock_min: 480 }
  - id: opt_loop
    edges: [ { from: optimize, to: compile_rpm } ]
    budget: { max_rounds: 4, max_wall_clock_min: 1440 }    # ≥ 2 × max_opt_rounds
run_budget: { max_wall_clock_min: 4320 }
routes:
  - { from: compile_rpm,   on: build_passed,           to: compile_image }
  - { from: compile_rpm,   on: build_fix_patch_ready,  to: compile_rpm }
  - { from: compile_rpm,   on: build_failed_exhausted, to: fail_safe }
  - { from: compile_image, on: image_ready,            to: ut }
  - { from: compile_image, on: image_fix_patch_ready,  to: compile_rpm }
  - { from: compile_image, on: image_failed_exhausted, to: fail_safe }
  - { from: ut,            on: ut_passed,              to: benchmark }
  - { from: ut,            on: ut_fix_patch_ready,     to: compile_rpm }
  - { from: benchmark,     on: bench_done,             to: optimize }
  - { from: optimize,      on: opt_patch_ready,        to: compile_rpm }
  - { from: optimize,      on: no_further_gain,        to: review_final }     # series_effect = asserts_nonempty
  - { from: optimize,      on: no_gain_found,          to: report_no_gain }   # 未产生任何被接受的优化
  - { from: review_final,  on: review_report_ready,    to: ci_plan }
  - { from: ci_plan,       on: release_plan_ready,     to: human_review }
  - { from: human_review,  on: approved,               to: release }
  - { from: human_review,  on: rejected,               to: fail_safe }
default_route: fail_safe
```

说明：优化专项的产物（profile 文件、构建选项变更）以 patch 形式进入 series，发布到各包自身仓库——与普通 patch 走同一条人工审批 + broker 发布路径。campaign 模式的 status 集为 {opt_patch_ready, no_further_gain, no_gain_found}：`no_further_gain` 仅在 series 相对 snapshot 存在净变更（被接受的优化或修复）时可返回（注册为 `asserts_nonempty`，运行时无净变更而返回即 `sys.invalid_result`），`no_gain_found` 表示无净变更（未产生被接受的优化，或候选均已撤销）——此时经 report_no_gain 汇总测量结果后 Run 以 succeeded 关闭，**不产生空发布计划、不进入审批与 broker**（ci_plan 对无净变更的 series 不得产出计划，校验器与运行时均拒绝）。首轮 Benchmark 在空 series 上只做绝对测量与 profile 采集（无 A/B 对象，报告 `comparison: none`，不作为阈值 gate 输入）；本专项不含阈值 gate，候选收益由 §7A.4 的"优化前 vs 优化后"判定承担。

**示例三：只编译并出镜像（`compiler_only.yaml`，无发布）**

```yaml
pipeline: compiler_only
dsl_version: 1
input: patch
nodes:
  compile_rpm:   { agent_type: compiler, mode: rpm }
  compile_image: { agent_type: compiler, mode: image, config: { backend: local, rpm_precheck: required } }
  summary:       { agent_type: review, mode: final, terminal: true, success_on: [review_report_ready] }
entry: compile_rpm
loops:
  - id: rpm_fix_loop
    edges: [ { from: compile_rpm, to: compile_rpm } ]
    budget: { max_rounds: 3, max_wall_clock_min: 480 }
  - id: image_fix_loop
    edges: [ { from: compile_image, to: compile_rpm } ]
    budget: { max_rounds: 2, max_wall_clock_min: 480 }
run_budget: { max_wall_clock_min: 1440 }
routes:
  - { from: compile_rpm,   on: build_passed,           to: compile_image }
  - { from: compile_rpm,   on: build_fix_patch_ready,  to: compile_rpm }
  - { from: compile_rpm,   on: build_failed_exhausted, to: fail_safe }
  - { from: compile_image, on: image_ready,            to: summary }
  - { from: compile_image, on: image_fix_patch_ready,  to: compile_rpm }
  - { from: compile_image, on: image_failed_exhausted, to: fail_safe }
default_route: fail_safe
```

**示例四：编译 + Benchmark（`compiler_bench_only.yaml`，无 UT、无发布）**

```yaml
pipeline: compiler_bench_only
dsl_version: 1
input: patch
nodes:
  compile_rpm:   { agent_type: compiler, mode: rpm }
  compile_image: { agent_type: compiler, mode: image, config: { backend: local, rpm_precheck: required } }
  benchmark:     { agent_type: benchmark, config: { suites: auto, mode: full, collect_profile: false } }
  bench_gate:    { gate: threshold, metric: benchmark.regression_pct, op: "<=", value: 5.0 }
  summary:       { agent_type: review, mode: final, terminal: true, success_on: [review_report_ready] }
entry: compile_rpm
loops:
  - id: rpm_fix_loop
    edges: [ { from: compile_rpm, to: compile_rpm } ]
    budget: { max_rounds: 3, max_wall_clock_min: 480 }
  - id: image_fix_loop
    edges: [ { from: compile_image, to: compile_rpm } ]
    budget: { max_rounds: 2, max_wall_clock_min: 480 }
run_budget: { max_wall_clock_min: 2880 }
routes:
  - { from: compile_rpm,   on: build_passed,           to: compile_image }
  - { from: compile_rpm,   on: build_fix_patch_ready,  to: compile_rpm }
  - { from: compile_rpm,   on: build_failed_exhausted, to: fail_safe }
  - { from: compile_image, on: image_ready,            to: benchmark }
  - { from: compile_image, on: image_fix_patch_ready,  to: compile_rpm }
  - { from: compile_image, on: image_failed_exhausted, to: fail_safe }
  - { from: benchmark,     on: bench_done,             to: bench_gate }
  - { from: bench_gate,    on: pass,                   to: summary }
default_route: fail_safe
```

说明：两个子集均无 release 节点，不声明 `release_requires`；summary 为 Review final 的 terminal 用法，接受 optional 上游并在报告与 `incomplete` 清单中写明未执行的环节（UT、发布等，属 `config_tradeoff`）。按 mode 的注册集：compiler.rpm 只 produces build_report、compiler.image 只 produces image_report（`rpm_precheck: required` 时 hard-require 前者）、benchmark hard-require image_report；修复类 status 的 series_effect 为 advances，其余为 none。四份示例的原文即校验器验收用例（随仓交付 `pipelines/`）；01 现行附录 A4 的 compiler_bench_only 属 v1.0 上游原文，01 切换上游时以本示例替换（附录 B 第 7 组）。

#### 4.2.2 节点与寻址
- 同一 agent_type 的多次使用 = 多个显式节点（各带自有配置），**不存在 `node.qualifier` 点号寻址**；路由 from/to 只引用已声明节点名、保留节点、或 `join:<id>`。
- 保留节点见 §3；`entry` 必填且唯一；终局节点为 `release`、`fail_safe`、或显式 `terminal: true` 节点（子集流水线用）。terminal 节点必须声明 `success_on: [status...]`：outcome ∈ success_on → closed(succeeded)，其余（含 sys.*）→ fail_safe；`compiler_bench_only.yaml`、`compiler_only.yaml` 示例按此交付。release **特权节点**的 outcome 集与终态映射固定（§4.2.5）。

#### 4.2.3 路由穷尽性
- 每个 agent_type 注册时声明业务 status 全集 `[01]`；校验器强制：`on` 值 ∈ (该节点 status 全集 ∪ gate outcome 集（§4.4 封闭枚举） ∪ sys.* )，且每个节点的业务 status 要么逐条有路由、要么被 `default_route` 覆盖（`default_route` 必填）。拼写错 status 在加载期即被拒绝。

#### 4.2.4 并行与汇合
- fan-out：`to: [a, b]` 并行分派。
- **join 触发机制（定案）**：join 的"到达" = 指向该 join 的路由边送达事件；校验器强制 `wait_for` 集合 ≡ 指向该 join 的路由源集合（不一致拒绝加载）。**activation 语义**：每次 entry 分派、fan-out、环激活生成持久化 `activation_id`（含环计数向量；生命周期见下条），到达键 = (run_id, join_id, activation_id, source)；每源每 activation 计一次，同键重复到达丢弃并记审计；全部源到达且 **series_id 一致** → 整组原子消费、恰好触发一次下游（跨 activation 的到达不得混组）。触发后下游 TaskInput 以固定形态 `join_inputs: list[上游结果引用]` 携带全部输入（schema `[01]`）。普通（非 join 目标）节点：每次边送达独立触发一次 task，需要汇合必须显式 join。
- 陈旧性：与当前最新 series 不一致的到达结果标记 stale 丢弃、继续等待同 series 新结果；被取代 series 的在飞本地任务跑完即弃（MVP 不主动取消；挂起中的 task 按 §4.3.4 取消外部等待并以 sys.superseded 终结）；join 等待受 `timeout_min`（可选）约束、缺省以 run_budget 为界，计时自该 activation 首个到达起算，计时口径同 §4.5（扣除区间按 §4.3.4 全集条件）。
- **activation 生命周期（退役规则）**：activation_id 由编排层在 **Run 启动的 entry 分派事务（根 activation）**、fan-out、环激活的分派事务内生成并落 Ledger（恢复自 Ledger 重建）；线性边与分支中间节点任务继承派发边的 activation 上下文；activation 记录含 **parent_activation_id**（嵌套 fan-out 的父作用域），join 原子消费后下游以父 activation scope 分派（传播定义含根 activation 与父子关系，`[01]`）。**supersede 三个触发条件**：① series 推进事务同一事务内将旧 series 的全部 open activation 标记 superseded 并作废其计时器；② 某 activation 的已有到达因 series 推进全部转 stale（①的防御性兜底，非独立语义——实现以①为准）；③ **不可补全退役**——声明环边被采用时，在该环边分派事务内，将**采用该环边的 task 所属 activation 上下文**标记 superseded，并沿 parent_activation_id **级联其全部子孙 activation**、连带作废各自计时器（同源单送达规则下，该来源在被退役 activation 内已可证明不可能到达，cohort 及其内层子组必然无法完成整链；退役依据是不可补全性而非"更新者存在"，不恢复 latest-wins）。**替代 cohort**：环边回流路径重经共同 fan-out 时（§4.2.6 条件(iii)对此静态强制）的新分派事务产生新 activation，该 activation **继承被退役 activation 的 parent_activation_id**——环不插入额外嵌套层级，嵌套场景下替代 cohort 照常参与外层 join。**防御性双保险**：join 消费、下游分派与 timeout handler 的 CAS 除校验自身 open 外，一并**校验祖先链无 superseded**；向 superseded scope 的分派被拒并审计。**同 series 的多个 activation 各自保持 open、独立成组消费、独立超时——不存在"更新者淘汰旧者"规则**（环计数向量无全序，latest-wins 不成立）。到达处理与 timeout handler 均以 CAS 校验该 activation 仍 open 且属 current series——superseded activation 的迟到事件与 timer 一律为审计化 no-op；仅 open 且属 current series 的 activation 超时可路由 fail_safe。model-based 测试覆盖同 series 并发多 activation（§11.3）。
- 并行分支任一进入 fail_safe：编排层取消同 Run 其余在飞分支（worker 终止，§5.1.2），Run 走终局处理。
- 通则：任何 Report 携带 series_id。**series 推进为编排进程单事务**：worker 经数据面 RPC 提交 series candidate + `expected_parent_series_id`，编排进程在 task 完成事务内一次完成——父版本 CAS（不匹配即拒绝，防并发丢 patch）+ artifact/结果提交 + series lineage + latest 指针推进 + 待审批项与未核销授权失效；tree_digest 由编排层按规范纯算法计算（无需 worktree，算法 `[01]`）并记录于 Ledger。HandoffResult 中的 series_id 经框架校验、不可自造；candidate 预分配不改变 current series。

#### 4.2.5 特权节点
- `broker: release` 节点由框架内置实现（转发 ReleasePlan 至 release broker），不可被业务 agent_type 顶替。release 的 outcome 集固定为 {released, release_failed}（授权无效/过期/series 陈旧归入 release_failed 附 reason；**D12 版本漂移不属于 release_failed**——在核销前检测并走 administrative finalize，§8.3）。**release 节点无出边、其 outcome 不走 DSL 路由**：终态由 §8.3 固定映射在 ledger 级直接关闭（release_failed 的 FeedbackReport 由 ledger 层生成，同 administrative finalize 例）；校验器拒绝任何 from: release 的路由。校验器强制：所有到 release 的路径必经 hitl；**位于 release 可达路径上的 hitl**，其 approved 出边必须直达 release（与发布无关的其他 hitl gate 不受此约束）——审批与执行之间不得存在任何可改变 release manifest 的节点；凭据只在 broker 进程，业务 CI Agent 永远无凭据。

#### 4.2.6 子集合法性（"合法子集"的定义）
静态校验器全部规则：节点/路由/join 引用有效；entry 存在；每个可达环均被某 `loops` 声明覆盖且带 budget；路由穷尽（4.2.3）；含 release 节点则必经 hitl 且（release 可达路径上的 hitl）approved 出边直达 release、release 无出边（4.2.5）；join 的 wait_for ≡ 指向该 join 的路由源集合，join 的 to 不得指向另一 join（MVP 禁止链式 join）；**join 作用域与共同到达检查**——每个多源 join 的来源必须由同一次显式 fan-out 的不同分支派生（每个来源恰由一个分支到达——来源集在分支间构成划分；共同支配关系不得替代共同 fan-out），全部来源共享该 activation scope；**共同到达性**：从该 fan-out 到每个来源 s 的路径上，任一节点的每个 outcome 分支必须满足三者之一——仍在可达 s 的路径上、到达 Run 终局（fail_safe/terminal/release）、或经声明的环边回流。环边作为本条件例外须同时满足两条静态约束：**其一，回流路径必然重经该 join 的共同 fan-out、从而重派全部来源分区**（机制：环边采用触发 supersede 条件③级联退役旧 cohort，替代 cohort 由重经 fan-out 的新分派产生并继承父 scope——不依赖 timeout 或预算兜底）；**其二，在重经当前 task 所属 activation 的共同 fan-out 之前，不得先重经任何祖先 activation 的共同 fan-out**——跨 activation 边界的回环会使真正被替代的祖先 activation 逃过③的退役根（③锚定在采用环边的 task 所属 activation），其计时器存活即误杀，祖先链 CAS 因该祖先未被标记而不设防；本约束静态保证退役根 = 被替代的作用域。违反任一环约束的回环拒绝加载；outcome 分支三者皆不满足（且不构成合法环边例外）的图亦拒绝加载（互斥 outcome 分支导致来源必然缺席的图在此被拒）；拒绝同一 source 每 activation 多次送达的图（到达键歧义）。**嵌套汇合采用父 activation 关系（定案）**：activation 记录持久化 parent_activation_id，内层 join 原子消费后以**父 activation scope** 分派下游——内层先汇合再参与外层 join 因此合法且可成组；validator property 与 model-based 反例（含互斥 outcome、嵌套汇合重入外层）入 §11.3（4.2.4，传播细则 [01]）；hard-required 上游与 **threshold gate 的指标来源节点**均做**支配性检查**——到消费节点的每条路径都必须先经过生产节点，仅存在不满足，且消费同 series 结果；terminal 节点必有 success_on；threshold gate 引用的指标来源节点在图中存在（不存在即拒绝加载——hard-required 依赖同理：Agent contract 可声明少数 hard-required 上游产物 `[01]`，其余一律 optional 降级，§6.3）；无不可达节点。**按 mode 取注册集（v2.0）**：status 全集、produces、series_effect、input_requirement、hard-required 上游与所需能力均以节点的 (agent_type, mode) 取集合（无 mode 的 Agent 用缺省键），例如 compile_rpm 只产 build_report、不得写 `on: image_ready`，compile_image 只产 image_report（§5.1.1）。**v2.0 追加三条规则**：

① **发布前验证（release_requires）**——含 release 节点的流水线必须声明 `release_requires`（发布前必须存在的报告类型清单）。**静态检查**：清单内每类报告的生产节点（按 mode 的 produces 判定）存在且是每个 release-approval 型 hitl 节点（§4.4 分型）的**汇合必经节点**。**汇合必经（适用于规则①与规则③）**：在普通必经（支配）计算的基础上，join 节点 j 的必经集合 = {j} ∪ ⋃_{s∈wait_for(j)} 必经(s)，j 的下游照常继承。成立依据均为冻结语义或本版强制项：(i) join 只在全部来源以同一 activation、同一 series 到达时原子触发下游（§4.2.4）；(ii) join 超时只能路由 fail_safe 并产出超时报告，绝不触发下游（§4.3.5）；(iii) 环回流时旧 cohort 经 supersede 条件③整体退役，新 cohort 须重新集齐全部来源（§4.2.6 条件(iii)）；(iv) 运行时审批 CAS 再次核对各报告存在、属当前 series 且结论为通过——静态判定即使有遗漏，运行时也 fail-closed。**E-01/V-13b 与阈值 gate 指标来源检查仍使用普通支配定义，不受本定义影响**；清单内报告缺生产者一律拒绝加载，校验器不自动删减（D14）；清单为空须同时显式声明 `accept_unverified_release: true`。**运行时检查**：Approval 服务提交决定事务内的新鲜度 CAS（§8.2）核对清单内每类报告均存在、针对当前 series、且**结论为通过**（各报告类型的"通过"谓词，01 形式化：BuildReport = succeeded；ImageReport = succeeded ∧ 未被标记坏镜像 ∧ 读回构建输入与锁定一致（§7.6.1）；UTReport = 所选用例集（§7A.7）全部通过；BenchReport = `gate_eligible`（§7A.3）∧ `comparison = verified`（三值 verified / unverifiable / none；unverifiable 不能经人工确认满足本谓词，§7.6.1）∧ 未 `baseline_revoked` ∧ 不存在未决优化计划（§7A.4）；回归幅度由阈值 gate 与人工审批判断，不在此谓词内）。任何产生 patch 的节点推进 series 后，旧报告全部失效，必须重新验证才能再进审批。release_requires 及满足它的报告引用（report_type、task_id、digest）写入 ReleaseManifest 的 `release_evidence`，审批 CLI 首屏呈现"本次未执行的验证类别"；配置同时留痕于 pipeline_digest。另：注册 attestation 绑定 Agent 所 produces 的 report_type 对应的 conformance 套件（防替身插件凭声明满足清单，R6）。

② **输入类型与净变更（input）**——`input: patch`（缺省）的流水线须由 MCP `submit_patch` 提供初始 series，`submit_patch` 拒绝应用后无净变更的 series（tree_digest 等于 snapshot 的 tree_digest，错误 E-SKILL-EMPTY-SERIES）；`input: none` 的流水线以空 series 起步。**需要净变更的节点**：注册 `input_requirement: patch` 的节点（如 CI 的 ci_plan）必须面对相对 snapshot 有净变更的 series；能处理净变更为空的 series 的节点注册为 `optional`（如 Compiler RPM 模式——撤销回 snapshot 后仍需按 series 涉及的包重新构建验证）。**静态检查（仅 `input: none` 流水线）**：对"当前 series 有净变更"做数据流分析——初始为"未证明"；经过 series_effect = `asserts_nonempty` 的路由边后为"已证明"；经过 `advances` 的边后**重置为"未证明"**（推进可能是撤销，提交 candidate 不等于有净变更）；经过 `none` 的边保持不变；**在每个有多条入边的节点（含 join 与环回边目标）对全部入边结论取交**（"已证明" ⊓ "未证明" = "未证明"），以 entry 为"未证明"、其余节点为"已证明"作初值迭代至不动点。任一 `input_requirement: patch` 节点在其入口处必须为"已证明"，否则拒绝加载；entry 节点不得注册为 `patch`。**运行时强制（全部流水线）**：返回 `advances` 类 status 而本 task 未提交 candidate、或返回 `asserts_nonempty` 类 status 而当前 series 无净变更 → `sys.invalid_result`；另外，编排分派任何 `input_requirement: patch` 节点前再次比对 tree_digest，无净变更则不分派、该 Run 以 fail_safe 关闭并在 `incomplete` 清单写明"series 已无净变更"（`input: patch` 下只会在 AI 修复把业务改动整体撤掉时出现，属必须让开发者知道的异常）。`input: none` 的 Run 在 snapshot pin 成功的同一事务内签发初始空 series（base lineage、tree_digest、current 指针）后进入 queued；pin 失败 → closed(snapshot_error)，不得先排队；此类 Run 的 `submit_patch` 一律拒绝（MCP 与 HTTP 同错误语义，重复 create_run 按 request_id 幂等、不重复签发初始 series）。ci_plan 对无净变更的 series 不产出发布计划——无可发布内容的流水线以 terminal 节点 succeeded 关闭（示例二）。

③ **优化重验证（D18）**——对注册为产出 `optimization_candidate` 的节点（Optimization 的 per_patch / campaign 模式）：令 G' 为从其 `opt_patch_ready` 路由边的目标节点出发、删去全部以 fail_safe 为目标的边后的子图；对 G' 中每个可达的 release-approval 型 hitl 或 terminal 节点 t，在 G' 上按规则①的**汇合必经**定义计算必经集合，要求镜像节点、UT 节点、Benchmark 节点都在其中，且在 G' 的必经序上依次出现（镜像节点为 `rpm_precheck: required` 时 RPM 节点亦在其中且先于镜像节点）。不产 patch 的并行旁支（如静态审查）因此合法。**汇合必经定义适用于规则①与规则③**；E-01/V-13b 与阈值 gate 指标来源检查仍使用普通支配。含此类节点的流水线，`release_requires` 不得省略 `image_report`、`ut_report`、`bench_report`。**预算容量**：优化环 `max_rounds ≥ 2 × max_opt_rounds`（每个候选至多一次提交 + 一次由 Optimization 产出的撤销）；位于优化重验证路径上、可能承载确定性撤销的修复环（RPM、镜像、UT 修复环）`max_rounds ≥ 1 + max_opt_rounds`（至少保留一次普通修复，外加每个候选至多一次确定性撤销，§7A.4）——静态容量只保证"至少能尝试一个候选"。**创建计划的运行时准入（v2.4）**：Optimization 提交 purpose = candidate 的 series candidate 时，编排在同一事务内核对：优化环剩余次数 ≥ 2，且优化重验证路径上每个修复环剩余次数 ≥ 1；不满足 → 拒绝创建计划（`E-PLAN-NO-CAPACITY`），Optimization 改为返回本 mode 表示无进一步收益的 status——per_patch → `no_further_gain`；campaign → 当前 series 相对 snapshot 有净变更时 `no_further_gain`，否则 `no_gain_found`（不计为违规）——业务修复用尽环预算后本 Run 不再尝试优化，换来任何已创建的计划都必有撤销所需的环容量。**运行时兜底**：未决优化计划（§7A.4）存在时，审批决定被拒绝；terminal 的 success_on 命中时不关闭为 succeeded，而由编排按 fail_safe 保留节点关闭（reason = `pending_plan_at_terminal`，v2.6），未决计划在审计中记为 abandoned——作为纵深防御（v2.7 改写理由）：合法流水线中优化之后的 terminal 只能在 Benchmark 之后到达（规则③在加载期拒绝绕过 UT / Benchmark 的终点路由，如 `image_failed_exhausted → terminal`），Agent 违规返回已由 §7A.4 运行时强制以 `sys.invalid_result` 承载；兜底覆盖其余遗漏。违反任一条拒绝加载。

另：hitl 节点的 `gate_expired` 路由目标不得与 `approved` 相同；`on: sys.timeout` 的目标只能是 fail_safe（重试照常经节点 `retry` 字段，§4.3.5）。

另（v2.5，后端能力的加载期检查；v2.6 按实际所需能力判定）：镜像节点所选后端的能力声明中构建暂存输入（source_input）≠ `verified`，而该节点可能面对非空 series（`input: patch`，或存在一条从 entry 经过某条 `advances` 边到达该节点的路径）→ 拒绝加载并提示改配 LocalGbsBackend；后端的可比性能力（comparison）≠ `verified`，而其镜像用于需要 A/B 的判定——relative SPEC、`regression_pct` 等比较类指标、优化收益判定、或 `release_requires` 中的 bench_report——→ 同样拒绝加载；只消费完整 absolute SPEC 聚合字段的非发布阈值 gate 不要求可比性能力（仍检查 gate_eligible、有效样本、必测指标覆盖与字段存在），指标依赖类型由固定的 SuiteVersion / BenchPolicy 与字段注册元数据解析，无法确定为 absolute-only 时按需要 A/B 处理——套件为 `auto` 或未锁定版本时加载期无法确定，一律按需要 A/B 处理，豁免只适用于显式列出且版本锁定、全部 SPEC 为 absolute 的套件（v2.7）；`input: none` 首轮 `comparison: none` 不作 gate 输入不变。镜像生成本身另须 `build_image` 能力为 `verified`。LocalGbsBackend 的 source_input、comparison、build_image 能力声明为 `verified`（全部输入由本系统控制），四份示例流水线因此可加载。

另：镜像节点 `rpm_precheck: required` 时，RPM 节点（produces build_report）须支配该镜像节点（hard-required 上游，按本节支配检查）；`independent` 时不要求。通过全部规则 = 合法子集；示例 `pipelines/` 下四份流水线随仓交付（§2.4）。

### 4.3 Run 生命周期

#### 4.3.1 状态机（穷尽）

```
created ─▶ awaiting_patch ─▶ queued ──▶ running ──核销事务──▶ publishing
   │            │(TTL 24h)    ▲  ▲        │   │                   │
   │(snapshot   ▼             │  └(槽空闲)┘   │(仅剩等待项)         │(broker 完成/
   │ 失败)  closed(cancelled) │              ▼                    │ probe 对账)
   ▼                          └──resume── paused(wait)            ▼
 closed(snapshot_error)                     │(reject/TTL)      closed(succeeded)
                                            ▼                  closed(fail_safe)
                                  closed(fail_safe 经保留节点)   closed(cancelled)
```
- resume 路径为 **paused → queued → running**（重新排队取执行槽，非直连）；paused 期预算到期同样经 paused → queued（优先出队）→ running 执行 fail_safe（§4.3.4）；running → closed(succeeded) 直达边存在于 terminal success_on 路径（非发布子集）；running → publishing 仅经授权核销事务迁入；publishing 出边仅 broker 完成或 probe 对账后按 §8.3 终态映射（ledger 级）关闭。
- 状态穷尽：created / awaiting_patch（snapshot 已 pin、等待 submit_patch，**不占执行队列**）/ queued（patch 受理**或 gate resume / 外部等待唤醒后**待执行槽，FIFO 排队）/ running / paused(wait)（等待成因 ∈ {gate, external}，可同时存在，成因集合持久化，§4.3.4）/ **publishing**（授权已核销、发布 point-of-no-return，§8.3）/ closed(reason)，reason ∈ {succeeded, fail_safe, cancelled, snapshot_error}。全部转换的命令/guard 表 `[01]`；非法转换由 Ledger 状态机守卫拒绝并记审计。
- FeedbackReport 在 reason=fail_safe 时由保留节点生成；**两条 ledger 级生成例外**：administrative finalize 路径（§4.3.3）与 release 固定映射路径（§4.2.5/§8.3）。
- awaiting_patch TTL 默认 24h，超时 closed(cancelled)；run_budget 自 submit_patch 受理（进入 queued）起算。`input: none` 的流水线跳过 awaiting_patch：created → queued（snapshot pin 与初始空 series 签发同一事务，§4.2.6 规则②），run_budget 自进入 queued 起算。
- **外部等待（勘误 E-02）**：远程构建在途、资源排队（板子、本地镜像构建额度、远程构建配额、基线镜像就绪）属节点级外部等待，机制、唤醒、计时与预算到期见 §4.3.4；Run 级规则与 gate 等待统一：仅剩等待项（gate ∪ external）、无可运行/在飞本地工作 → paused(wait) 并释放执行槽，任一等待解决 → queued 重新取槽。
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

#### 4.3.4 外部等待（勘误 E-02，随本 HLD 三方评审 GO 生效）
定案原则：**外部等待是编排侧的等待项，任何 worker 都不跨越等待存活**——冻结的 worker/task 模型（注入 ctx → execute → 结果回传、hard-kill、心跳、孤儿回收）不变。
- **等待项（ExternalWait，Ledger 记录，与 gate 等待项同构）**：`wait_id`、run/task/dispatch 绑定、`kind ∈ {resource, remote_build, gateway_session}`、外部引用（资源类别、远端构建标记，或会话等待时的阶段与（若已有）效应 idem_key/version）、超时上限（`external_timeout_min`，节点可配，缺省 = 所在环 wall_clock 上限，节点不属于任何环时 = `run_budget.max_wall_clock_min`；会话等待另用登录等待上限）、计费类别（`billable` / `non_billable`）、登记与解决时间；解决以 CAS（pending → resolved）恰一次，重复通知审计化丢弃。
- **资源等待（分派前授予）**：节点按注册与配置声明所需资源（板子按"板型 + 能力"、本地镜像构建额度、远程构建配额、基线镜像就绪）。编排在分派事务内检查：全部可授予 → 授予租约后照常入队取执行槽；任一不可授予 → 该 dispatch 登记 `kind=resource` 等待项、**不 spawn worker**，按资源类别 FIFO 排队；授予后经 wake outbox 进入 queued。**锁序 = 先资源租约、后执行槽**——取槽从不等待租约，故无"持槽等租约 × 持租约等槽"环路；持有已授予租约的 Run 在 queued 中优先出队，减少板子空占。资源等待计费（billable）。
- **远程构建等待（提交后挂起）**：Agent 经 side_effect 提交远程构建（效应标记 = idem_key 指纹 + version，§5.2），随后调用 `ctx.await_external(build_ref)`：若该等待已解决 → 立即返回远端结果；否则 SDK 经数据面命令 `task_suspend` 结束本 attempt（**guard：本 attempt 除该远程构建效应外无 claimed/running 效应记录**，否则拒绝——Agent 须先完成或失败其他在途效应，避免续接 attempt 的启动对账把它们误判为 abandoned/unknown），task 以框架保留结果 `sys.await_external` 收尾——**不走 DSL 路由、不计入 retry.max、不映射 sys.crash**；编排在同一事务登记 `kind=remote_build` 等待项，释放 worker 与本地额度（远端在途构建继续占远程构建配额）。编排侧 poller 经 Build Gateway 查询远端状态；到达终态 → CAS 解决等待项 + 写 wake outbox（outbox_id 去重，与 resume outbox 同构）→ 消费端对**同一 task / 同一 dispatch** 分派续接 attempt（dispatch_id 不变 ⇒ 效应键稳定：提交效应命中 succeeded 记录复用，**不重复提交**；`await_external` 返回已记录结果）。远端失败同样以结果形式交回 Agent 处理（如交 LogAnalyzer 分析）。
- **会话等待（v2.3：覆盖提交前与对账阶段）**：Gateway 会话不可用时，等待不以"已有 build_ref"为前提——`kind=gateway_session`，`phase ∈ {before_submit, submit_uncertain, polling, reconciliation}`：分派前检测到会话未就绪（before_submit）、提交 RPC 发现会话不可用、提交 ACK 丢失后恢复 probe 返回 `deferred`（submit_uncertain / reconciliation）时，编排原子登记该等待并结束或不启动 worker（含对账 worker），**不消耗 retry 与 probe 次数**；已在途的 `remote_build` 等待项在会话失效期间计费类别切换为 non_billable，phase 记为 polling。会话恢复后对**同一 dispatch** 续接；`submit_uncertain` 必须先按效应标记 probe，**不得因登录恢复而直接再次提交**。登录等待按自己的时钟累计（重启不重置），超过配置的登录等待上限 → 编排为对应 task 合成 `sys.timeout`（进入超时报告，类别 gateway_session），**固定路由 fail_safe、不经节点 retry**（重试面对的是同一个失效会话，§4.3.5）。会话期间对账 probe 结果为 `deferred`——不进入 unknown（§8.6）。
- **Run 级**：Run 无可运行或在飞的本地工作且存在 ≥1 未决等待项（gate 或 external）→ paused(wait)、释放执行槽；任一等待解决 → queued。wake 消费时 Run 若处于 running（其他分支在跑）则只调度新就绪工作，不把 Run 降回 queued。**外部等待超时**：任一 external 等待超过其 `external_timeout_min` → 编排取消该等待（远程构建按下述取消协议）并为对应 task 合成 `sys.timeout`。
- **计时口径（全集条件）**：某区间从 run_budget / 环 wall_clock / join timeout 中扣除，**当且仅当**该区间内 Run 无可运行或在飞的本地工作、且全部未决等待项均为 non_billable（gate 等待、会话失效期的远程构建等待）；只要存在任一 billable 等待（远程构建在途、资源排队），该区间计入预算。publishing 时段按冻结规则豁免。等待成因与区间边界持久化，重启不重置。
- **paused 期间预算到期**：预算计时器在 paused(wait) 下照常可到期（计费区间）；到期 → 编排取消该 Run 全部未决外部等待（按下述取消协议）→ Run 迁 queued 并优先出队 → 执行 fail_safe 保留节点（状态图补 paused ─(预算到期)→ queued 边）。
- **取消传导与远程配额（v2.3）**：cancel、fail_safe 取消分支、预算到期、series supersede 时，编排对相关远程构建发起 Gateway 取消（幂等）。**Run 可先终局，但远端作业的配额不随之释放**：作业进入持久化的 `cancel_pending` 状态，继续占用远程构建配额，直到 Gateway 确认远端终态（Quickbuild 为父 trigger 及其全部子构建，§7.6.1）、或确证从未提交，才恰一次归还配额（远端证据过期不视为终态）；取消失败的重试与 probe 由框架清理任务承担，跨 Run 关闭与重启存续；迟到结果不得推进旧业务任务，但用于更新清理状态与归还配额；长期不可判定者隔离占额并告警。本地资源租约（板子等）按 §7.7 的静默与复位规则回收。**挂起中的 task**（无 worker）在其 series 被 supersede 时，于 supersede 事务内取消其外部等待并以保留结果 `sys.superseded` 审计化终结，不参与路由。
- **对冻结语义的偏离清单（随 E-02 一并生效）**：① paused 成因扩为 gate ∪ external；② 计时改为全集条件；③ paused 期预算可到期；④ 持有已授予租约的 Run 在 queued 中优先出队（偏离纯 FIFO）；⑤ series supersede 时主动取消挂起 task 的外部等待（冻结的"被取代 series 的在飞本地任务跑完即弃"对本地任务不变）；⑥ 新增保留结果 `sys.await_external`、`sys.superseded`（均不参与 DSL 路由，V-05/V-06 路由穷尽排除）。
- **规则文本单一事实源**：命令、guard 与计时的契约形式化在 01 同步扩展时落定（附录 B 第 7 组），与本节冲突以本节为准。

#### 4.3.5 超时与未完成必须显式呈现（v2.2 定案，v2.3 补放行点）
定案原则：**超时、未执行、被跳过的环节永远不能被当作"通过"，并且必须出现在开发者第一眼看到的结果里**——使用者通常只看结果、不看日志，结果里没写的就会被当成"已跑完且通过"。
- **超时一律不放行（结构保证）**：节点硬超时（`sys.timeout`）、join `timeout_min` 到期、环 / run 预算到期、外部等待超时（`external_timeout_min` 与 Gateway 登录等待超时，§4.3.4）一律走 fail_safe——join 超时、预算到期、外部等待超时由编排固定路由 fail_safe（DSL 不提供其出边字段）；校验器要求 `on: sys.timeout` 的目标只能是 fail_safe（重试经节点 `retry` 字段进行，不经路由）；hitl 的 `gate_expired` 目标不得与 `approved` 相同；threshold 指标缺失 = fail（既有规则）。因此**未被重试成功覆盖的超时必然使 Run 经 fail_safe 关闭**，不依赖关闭时再检查。
- **超时报告**：每次超时由编排在同一事务内生成一条超时记录——位置（节点 / join / 环 / 等待项）、超时类别、已用时长与上限、超时时刻仍在进行或仍在等待的内容（哪一路未到达、哪个远程构建仍在途、哪块板子仍在排队）、最后已知状态与相关日志引用、该位置此前的重试次数。超时导致 Run 关闭时，FeedbackReport 的**第一节**即为超时清单。
- **清单分类（定案）**：`get_result`（MCP 与 HTTP 同一契约）在最终结论之外固定返回两份清单，配套 Skill 与审批 CLI 首屏必须原样呈现，不得只呈现"成功 / 失败"：
  - `retried`：超时或崩溃后经同一 task 的后续 attempt 成功覆盖的记录（重试次数、每次超时时长、最终成功的 attempt）——**是真实通过**，但必须让开发者和审批人看到：发布路径上，**属于当前 series 证据链**的 retried 记录须审批人逐条确认后才可发布——证据链 = 以当前 series 分派的全部 task（含 ci_plan 与 Review）∪ 为 `release_evidence` 中报告提供基线镜像的 `sys.baseline_build` task（其 retried 记录随基线引用并入本 Run 清单，v2.5）；被后续 series 取代的轮次上的 retried 记录在首屏**汇总列出**（位置、超时时长、重试次数），不要求逐条勾选（负责人 v2.3 定案，v2.4 按评审收窄确认范围）；
  - `incomplete`：每条带 `class`——`timeout`（未被覆盖的超时，必然导致 fail_safe）/ `config_tradeoff`（可由 pipeline 原文静态推导的取舍：显式删除的 Agent、从 `release_requires` 移除的验证类别、optional 上游降级、构建后端声明的能力限制，§7.6.1）/ `environment_gap`（运行期环境事实：范围内模块无用例、构建输入读回不可比、`baseline_revoked`、series 已无净变更等）/ `verification_asset_change`（AI 段改动了验证资产，§7A.0 原则 6）。
- **放行点（v2.3）**：发布路径——release-approval 型 hitl 的决定事务（§8.2 新鲜度 CAS）核对：不存在 `timeout` 类条目；每条 `environment_gap`、`verification_asset_change` 与**当前 series 证据链上的每条 `retried` 记录**都出现在本次决定的 `acknowledged_gaps` 中（审批 CLI 首屏逐条呈现超时位置、超时时长、重试次数与最终通过的报告，审批人逐条确认），否则拒绝提交；**`acknowledged_gaps` 每项 = (条目 id, 条目内容 digest)**，复核按 digest 比对，内容变化即视为未确认；审批人不认可 → 按 reject 处理，不发布；**核销事务（§8.3）再次复核同一条件**，防止审批与核销之间新增或变化条目——复核不通过则不核销：consume 返回 ConsumeRejected(reason = `gaps_changed`)，由编排按 §8.3 的 release_failed 固定映射在 ledger 级关闭 Run（broker 不发 release_outcome——outcome 恒为实际执行后，v2.5），FeedbackReport 列出新增 / 变化的条目（冻结映射不允许回到等待，须新建 Run）。非发布路径——terminal success_on 照常 closed(succeeded)，`incomplete` 或 `retried` 非空时 `get_result` 的结论字段为 `succeeded_with_gaps` 并列出各条（终态 reason 集不变）。
- **publishing 之后**：核销即 point-of-no-return，之后出现的超时或未完成按冻结规则只登记 pending，终态严格按 §8.3 远端事实映射；released 的结果首屏显示"已发布，但发布后出现超时 / 未完成：…"，清单完整保留，不得显示为全项通过。

### 4.4 Gate
- gate outcome 全集（封闭枚举，§4.2.3 校验依据）：`hitl` → {approved, rejected, gate_expired}；`threshold` → {pass, fail}。
- **hitl 分两型（校验器按 release 可达性静态判定）**：release-approval 型（位于 release 可达路径）——审批对象为 ReleaseManifest、approve 生成授权记录、approved 直达 release（§8.2/§4.2.5）；plain-decision 型（与发布无关）——approve/reject 仅提交决定 + gate outcome CAS + resume outbox，**不生成 ReleaseManifest 与授权记录**。
- `hitl`：gate 等待为**节点级**——同 Run 其他在飞分支继续执行；Run 级 paused 当且仅当仅剩等待项（gate ∪ 外部等待，§4.3.4）、无可运行或在飞的本地工作（此时释放执行槽，D11）。Approval 服务的决定经 control-plane RPC 单命令原子提交（决定 + 授权记录【仅 release-approval 型；plain-decision 型无此项】+ gate outcome CAS（waiting→resolved，重复决定被守卫拒绝）+ resume outbox，§8.5）。**outbox 消费端去重**：每条以唯一 decision_id/outbox_id 标识，编排层持久化 inbox 去重——重复投递返回同一结果、不得重复创建 task，durable dispatch 完成后才确认 delivered；**resume 不消费授权**，唯一消费点在 broker（§8.3）。gate 可配置 TTL（默认无），超时 outcome=gate_expired；等待期间 series 变化按 §4.2.4 陈旧性规则处理。
- `threshold`：纯代码判定；指标缺失/非法一律 fail-closed（outcome=fail），不允许 fail-open。

### 4.5 循环预算
- 预算属于 `loops` 声明的环对象（环由 `edges` 唯一定义，routes 不重复标注环归属）；环边每通过一次计数 +1，**max_rounds: N = 环边允许通过 N 次，第 N+1 次通过请求即拦截并强制路由 fail_safe**（示例 max_rounds: 2 即最多 2 轮修复回流）；计数持久化于 Ledger 随恢复延续；多环共享节点各环独立计数。`run_budget` 为 Run 级总预算，最先触发者生效；**run_budget、loop wall_clock 与 join timeout_min 采用同一计时口径**——publishing 时段豁免（冻结规则），paused 区间按 §4.3.4 全集条件扣除：仅当全部未决等待均为不计费等待（gate 等待、Gateway 会话失效期的远程构建等待）时扣除，存在任一计费等待（远程构建在途、资源排队）时计入（多日人工审批不消耗预算；构建与排队属流水线自身成本）；paused 期间预算可到期（§4.3.4）。

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
- Agent 经 `ctx` 获得框架注入句柄：artifact store、KnowledgeProvider、LLM client、EvidencePacket builder、trace、`await_external`（§4.3.4）、以及**能力句柄**（BuildBackend（本地 / Quickbuild）、ImageBuilder、BoardPool、BaselineCache（只读）、ProfileStore（读正式区 + 写本 task 待验区）、LogAnalyzer 引擎等，按 agent_type 在配置中授权注入；清单**显式排除发布通道**——发布只存在于 broker（§8.3）；未授权句柄不存在于 ctx，与 D8 联动）。**句柄只是数据面命令的客户端**：凡改变共享或权威状态的操作（镜像入库、Profile 写入、远程构建提交、租约释放）一律经 §8.5 数据面命令由编排进程事务提交（勘误 E-03），句柄不在 worker 内直写任何数据库或共享目录（D6）；资源租约由编排在分派前授予（§4.3.4），句柄只能使用与释放本 task 已获授予的租约。
- 注册：entry-point namespace `codingsystem.agents`；加载时校验 status_set 非空、contract 兼容、conformance attestation（§11.3，绑定所 produces 的 report_type 的 conformance 套件）。**注册信息按 mode 声明**（无 mode 的 Agent 用缺省键）：`status_set`、`produces`（产出的报告类型）、每个 status 的 `series_effect`（advances / asserts_nonempty / none）、hard-required 上游、`input_requirement`（patch / optional——用于 `input: none` 校验）、所需资源（分派前授予，§4.3.4）、所需能力句柄；校验器以节点的 (agent_type, mode) 取集合（§4.2.6）。

#### 5.1.2 Worker 模型（进程边界）
- 每个 task 由编排进程 spawn 独立子进程 worker 执行：注入 ctx → 调 execute → 结果经 IPC 回传。外部等待不改变此模型：等待期间该 task 无 worker（资源未授予时不 spawn；远程构建在途时以 `sys.await_external` 结束本 attempt），续接为同一 dispatch 的新 attempt（§4.3.4）。
- worker 以独立进程组（setsid）启动；hard timeout / 取消 = 对**进程组** SIGTERM 宽限后 SIGKILL（killpg，覆盖 gbs 等孙进程），构建后端额外登记外部长进程（含 mic）供递归清理；进程退出映射 `sys.crash` / `sys.timeout`。
- 编排层持有 worker 租约（heartbeat）；**心跳丢失时 worker（进程组长）先 killpg 终止本组全部进程（含 gbs 孙进程）与构建后端登记的外部长进程，再自行退出**——kill 语义不因编排进程失联而缺席；编排进程恢复时先按 Ledger 登记的 pgid 验证归属并 reap 孤儿进程组、再重放。故障注入含"编排进程崩溃且 GBS 子进程仍活跃"用例（§11.3）。
- Agent 实例作用域 = 单 task（无跨 task 内存态，setup/teardown 每 task 执行）。凭据类 secret 不注入业务 worker（D8）。

### 5.2 副作用：at-least-once + 效应侧幂等
- **保证等级声明**：框架保证 at-least-once，不承诺 exactly-once。外部效应成功与完成记录落盘之间存在崩溃窗口，关闭窗口的责任在效应侧幂等。
- SDK 入口为 `side_effect(effect_call_id, params, fn, repeat_seq=None)`——**idem_key 只能由框架计算**（worker 不得自供完整键，conformance 强制）；**effect_class 由 fn 所属注册效应类型推导**：side_effect 仅可包装类型化能力句柄上注册的效应（probe/replay_safe 能力声明挂在该类型上），自由函数不可包装，effect_class 参与 conformance 校验（细则 `[01]`）；其为两阶段持久化状态机（Ledger 同库事务）：`claimed(intent) → running → succeeded/failed`；恢复时遇 `running/claimed` 记录 = 状态不确定（待对账），执行 **恢复协议**：按 §5.2 三支对账（probe / replay_safe 重放 / 皆无 → 持久化 unknown 态并转 sys.error）。
- `idem_key = hash(run_id, dispatch_id, effect_class, effect_call_id, effect_params_digest[, repeat_seq])`——**效应身份 = slot + 稳定逻辑调用标识**：slot = (run_id, **dispatch_id**)，dispatch_id 为创建该 task 的边送达/分派事件的 Ledger 标识——跨 attempt 稳定（重试复用同一 task 即同一 dispatch）、跨 task 天然隔离（含 entry 分派与兄弟送达；node/activation/环轮次由 dispatch 记录蕴含，不入键）。**`effect_call_id` 由调用方提供、在 Agent 代码内稳定**（如 "build_main"、"flash_pre"），不依赖调用次序——控制流变化的重试不会把新逻辑调用错配到旧记录；框架强制同 task 内 effect_call_id 唯一在册（conformance 检查项），显式声明的重复执行由调用方给定 `repeat_seq`（迭代序）。`effect_params_digest` = 调用实参规范化摘要（含 series_id/tree_digest、构建目标、板卡标识等，artifact 引用按 content digest 参与）。**不含 attempt**：同 (call_id, params) 的重试/重放命中同一记录；非决定论重执行实参不同 → 新键，且**跨 attempt 遗留**的同 call_id 旧在途异参记录经 attempt 启动对账**定态**——逐支终态：probe 确认成功 → succeeded（复用）、确认未发生或 replay_safe 退役 → abandoned、不可判定 → unknown + sys.error；**succeeded 与 unknown 不得改写为 abandoned**；**异参新键允许集合（枚举定案）**：定态 succeeded 或 abandoned → 异参新 claim 放行、新键独立执行，且旧 succeeded 仅供同参精确键命中复用、**不得跨参数复用**；定态 unknown → task 已随 sys.error 中止，无新键可立。**本枚举仅辖跨 attempt 定态记录**；干净终态 failed（正常执行产物、非定态产物）之上的同 call_id 异参新 claim 依既有效应类别策略放行，不在此列（效应侧"退役"不与 activation 的 supersede 术语混用）。**唯一性约束的两个层面**：conformance 静态检查（每逻辑调用点唯一命名）；运行时拒绝路径——**仅同一 attempt 内**（跨 attempt 遗留已经启动对账定态）同 call_id 存在未决（claimed/running）记录时的异参新 claim 被拒（作者误用形态），task 报 `sys.invalid_result`（细则 `[01]`）。
- **记录状态与查找矩阵**（全集 claimed / running / succeeded / failed / abandoned / unknown，迁移与查找表 `[01]`）：查找只命中非 abandoned 记录——claimed/running → 按效应能力对账（见下）；**succeeded → 直接复用（含上一 attempt 经 probe 确认成功的记录——可 probe 而不可安全重放的效应必须复用，不做保守重做）**；failed → 按效应类别策略重试或上报。对账按效应能力分三支（conformance 分别覆盖）：**可 probe** → probe 确认成功迁 succeeded（复用）、未发生迁 abandoned；**无 probe 但声明 replay_safe** → 旧在途记录退役 abandoned、重放；**两者皆无** → unknown（持久化）并报 sys.error。attempt 启动前，编排层将上一 attempt 遗留的本 task 非终态记录逐条按上述三支对账。abandoned 记录不参与命中；**记录版本化为通则**——凡同键在 abandoned 记录之上的重执行，一律以版本化新记录承载（迁移/查找表 `[01]`）。
- 状态迁移经 control-plane RPC 由编排进程事务写入：worker 收到 claimed ack 后方可启动效应，RPC 失败 = 效应不得启动（fail-closed）；intent/running 即时提交，task 完成事务仅覆盖最终结果 + artifact 索引 + 幂等终态。
- 效应类别要求（contract + conformance 强制）：本地构建 = 可 probe（worktree/产物存在性）；**镜像构建 = 可 probe——按本效应 idem_key（含 version）查 Ledger 镜像索引，仅已完成镜像存储提交协议（§7.8）的镜像可被命中，命中后复验内容 digest、snapshot、tree_digest 与构建输入闭包摘要；BaselineCache 键不作效应身份**；**远程构建（Quickbuild）= 可 probe（有界，v2.4）——提交即向远端写入效应标记（idem_key 指纹 + version），Gateway 转发与远端查询以该标记归因，run/task 标识仅作人工辅助标签；发送前持久化提交 intent（含提交前该配置的最大构建号），响应丢失先 probe——按构建号自该值起逐个匹配标记，扫描范围与读取方式受 §7.6.1 限制，超出即 indeterminate；查询不可见但不能证明未提交时返回 indeterminate（不得当作未发生），确认未发生且旧提交执行已静默后方可新版本提交，迟到结果不得替换现行版本；会话失效期间 probe 返回 deferred（§4.3.4）**；刷板/板上执行 = 可 probe（读板上镜像标识）或声明可安全重放，二者均绑定板子租约 generation（§7.7）；**profile 采集 = 声明可安全重放**；**发布 = 仅经 broker，broker 端远端幂等（push 前查远端状态）+ token 单次核销双保险**。

### 5.3 trace 与 token 记账
- SDK 自动埋点（task 起止、LLM 调用、工具调用、artifact 读写）写 Ledger；`trace.jsonl` 为 Ledger 派生的追加安全格式（每行一事件），供人读与外部工具消费。
- token budget：按节点在 pipeline YAML 配置（`llm_budget:`），超限策略由 Context 管理执行（§7.3）。
- 落盘前统一脱敏：secret/token 只记指纹（§8.4）。

---

## 6. Contract 体系概览（精确 schema 见 01_Contract_Spec）

### 6.1 消息类型
`TaskInput` / `HandoffResult` / 各 Report（Build/Image/UT/Bench/Optimization/Review/Feedback，均携带 series_id 与产出 task_id，各有确定性的"通过"谓词）/ Benchmark 套件版本（含 BenchPolicy 与 SPEC）/ 测量记录 / Profile 记录 / 优化计划 / `RunContext` / `ReleasePlan` / `ReleaseManifest`（含 release_evidence）/ Approval 决定与授权记录 / 外部等待项 / Run 终局摘要 / MCP 工具与 HTTP 端点的请求/响应消息。agent_type 注册信息按 mode 含 status 全集（及各 status 的 series_effect）、produces、input_requirement 与 hard-required 上游声明。

### 6.2 版本规则
Contract 独立版本号；Agent 以 PEP 440 specifier 声明兼容区间（§5.1.1）；框架装配时校验。pipeline `dsl_version` 属 Contract 版本体系。draft 期允许破坏性修改但记 decision_log。

### 6.3 上游缺失语义
默认全部 optional + 降级运行 + 报告显式标注"本次 Run 未执行 X"（同时进入 `get_result` 的 `incomplete` 清单，§4.3.5）；Agent contract 可声明**少数 hard-required** 上游产物（如 benchmark、UT hard-require 镜像引用；optimization hard-require Benchmark 报告），由 DSL 校验器静态拦截（§4.2.6）。approval_token 属"外部供给依赖"类别，不参与上游产物校验。conformance 含上游缺失用例。

### 6.4 Patch 归属与陈旧性
产物为 patch series（非 squash），逐段标注产出者与动因；series 任何变更 → 新 series_id + 新 tree_digest → 旧 Report 对 gate/join 失效（§4.2.4）、未核销 token 失效（§8.2）。是否 squash 是 broker 发布期可配置行为。

### 6.5 Coding Agent 接入：Skill + MCP（决策定案）
- **接入方式**：框架提供 **MCP 服务**，把流水线操作暴露为 MCP 工具；同时提供配套 **Skill**，安装在 Coding Agent（ClineSR / Codex）中——Skill 描述何时调用、调用顺序（创建 Run → 提交 patch → 轮询状态 → 获取结果与反馈报告）、失败如何处理。Coding Agent 经 Skill 调用 MCP 工具启动流水线。
- **传输**：MCP 服务使用 Streamable HTTP 传输，部署在框架主机上（内网）；同一操作契约另保留 HTTP + JSON 端点，供脚本、运维工具与测试使用——两者共用同一实现与同一套校验，不存在语义差异。
- **MCP 工具与操作一一对应**：
  - 操作：`create_run(pipeline_id, target_spec, focus_modules?, request_id)`（`focus_modules` 为本次目标模块：`input: none` 流水线必填，`input: patch` 流水线可选、在首次 submit_patch 时与改动推导出的模块取并集，§7A.7）（target_spec 指定 snapshot 拉取范围：仓/包/manifest，语义 `[01]`）、`submit_patch(run_id, series)`（unified diff series + 逐 patch 的 repo 归属；服务端校验对 pinned snapshot 可应用，不可应用即拒绝；一个 Run 仅接受一次初始 series，重复提交返回明确错误——修订走新 Run）、`get_status`、`get_result`、`cancel_run`。忙时语义：submit_patch 受理后 Run 进入 queued（FIFO，响应返回队列位置），resume 同队列；awaiting_patch 不占队列，TTL 见 §4.3.1。
- 认证与信任边界：MCP 连接与 HTTP 端点使用同一种静态 bearer token，**每个调用方一枚**（principal 由 token 映射；`cancel_run` 限创建者即按 principal 判定）；**request_id 为工具/端点参数**（不是 JSON-RPC 消息 id——后者会话内复用），幂等域 = **(principal, 操作名)**，跨 MCP 与 HTTP 两种传输共享：同一操作以同一 request_id 经任一传输重试得到同一结果；patch 大小/路径白名单校验。MCP 服务校验 `Origin` 头并仅监听内网受控网段（防 DNS rebinding），`Mcp-Session-Id` 不参与认证。信任边界声明：MCP 服务与 HTTP 端点仅暴露于内网受控网段（D13），持 token 者视为受信调用方。
- **开发者操作**（同一认证与幂等规则）：`submit_bench_suite`（提交开发者脚本或用例描述；**只提交、不确认**——确认走本机特权通道，§7A.3）；`create_run` 用于 `input: none` 流水线（如优化专项）。**周期触发**由框架内置调度器执行，principal = `sys.scheduler`，仅可创建 `input: none` 的流水线。
- **Skill 随框架交付并带版本**：Skill 中声明其适配的契约版本，与 MCP 服务版本不兼容时 MCP 返回明确错误，提示更新 Skill。

---

## 7. 公共模块（L1）

### 7.1 LLM 接入层
- Provider 抽象 `complete(messages, policy_ctx) -> LLMResponse`；实现：**ClineSRCliProvider（第一阶段生产实现）**、FakeLLMProvider（开发与测试）、将来的内网 LLM API provider（若提供）与可选外部 API provider。Agent 只面向该抽象编程，provider 更换不改任何 Agent 代码。
- **ClineSRCliProvider（定案：第一阶段不依赖 LLM API）**：内网目前只有 ClineSR CLI 可调用内网大模型，框架据此实现 provider，约束如下：
  - **只作补全引擎使用**：以单次非交互方式调用，框架把组装好的提示（含 EvidencePacket）写入临时目录作为输入，CLI 只返回文本结果；关闭 CLI 自身的文件修改与命令执行能力（CLI 参数层）——所有对代码与环境的改动都由 Agent 经框架的 side_effect 执行，不允许绕过框架由 CLI 直接改文件（保持可追溯与幂等）。
  - **OS 层强制（定案，不依赖 CLI 行为）**：EvidencePacket 含攻击者可控的日志与源码，间接提示注入可诱导 agentic CLI 执行命令，故参数层关闭之外另设兜底——CLI 以**专用 OS 用户**运行；spawn 时 `close_fds`（不继承 per-task socketpair 及任何 FD）；提示目录只读、唯一可写为空临时目录；无 worktree / Ledger / artifact / 镜像目录访问权；网络出口仅允许已登记的 LLM 端点（按 UID 的出口规则）；调用结束校验临时目录外无文件变更，有则该次调用作废并告警。E0 预检若确认 CLI 无法在上述约束下以补全模式工作，第一阶段 LLM 能力不上线（不提供放宽降级）。
  - **配置固化**：CLI 的端点、模型、输出格式由框架按每次调用生成临时配置（不读取用户目录下的 CLI 配置），端点身份进 provider 配置 digest；CLI 版本进 execution manifest（`llm_cli_version`，D12）。
  - **结构化输出**：提示中要求固定的 JSON 结构，provider 校验结构，校验失败按 cascade 规则重试（§7.1 路由），仍失败报错交由 Agent 处理。
  - **进程管理（v2.3）**：CLI 以专用 OS 用户运行，worker 以自身 UID 对它发信号会因权限被拒（进程组信号对不同 UID 的成员静默跳过），因此 CLI 一律由 deploy 特权 launcher（§8.5，属可信计算基）spawn 并置入该 task 的 **cgroup v2 子树**；硬超时、取消与回收经 launcher 写 `cgroup.kill` 终止整个子树（覆盖跨 UID 进程及其子进程）；launcher 以 pidfd 监视 worker，worker 退出即终止其 task 子树；编排恢复时按 Ledger 登记的 cgroup 路径对账回收。同 UID 进程仍按 §5.1.2 的进程组语义处理。部署需要 cgroup v2 委派（E0 预检项）。并发数由资源额度单独限流（§7.6.3），避免同时拉起过多 CLI 进程。
  - **记账**：CLI 不返回 token 数时按输入输出字节估算，**取上界系数**并标注为估算值（llm_budget 的 fail-closed 不得被低估突破）。
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
- **LocalGbsBackend**（首期）：RPM 阶段 = per-task git worktree 隔离、`git apply --index` + staged/worktree 一致性校验、GBS 增量构建（`--incremental`），范围默认"受影响包 + 反向依赖闭包"；镜像阶段 = GBS 全量构建至本地仓库 → `mic create`（镜像 ks 配置来源 `[待补充]`）。镜像产物入镜像存储（§7.8）。**特权构建隔离（D22）**：GBS buildroot 的 sudo 段（增量与全量）与 mic create 一律在构建隔离边界内执行——一次性构建 VM（首选）或独立构建主机；宿主不向边界内挂载 Ledger、凭据库、Gateway 会话存储，不暴露任何 control-plane socket；源码与 series 以只读方式送入，产物经只读导出通道交回并按镜像存储提交协议复验入库；deploy 特权 launcher 只负责边界的启动、销毁与产物回收，宿主 root 上下文中不执行任何 snapshot/series 内容。
- **QuickbuildBackend**（首期第二步，P6）：经 Build Gateway（§8.6）提交远程构建、由编排侧 poller 查询状态（§4.3.4）、拉取失败日志。以下按只读调查（docs/research/quickbuild_business_logic.md，公开 Tizen QuickBuild 的 RBS/TRIGGER 配置 1917）定案；**每项能力按配置登记证据等级 `verified` / `unverified` / `unsupported`（后端能力声明，v2.4）**——`unverified` 的能力不得启用，P6 前以经负责人确认的真实提交逐项验证后升级；"调查未证实可锁定"不等于"服务不支持"，只表示本系统当前不依赖它。
  - **"最新"的含义（v2.4，v2.5 校正依据）**：Quickbuild 表单缺省为 `BUILD_REFERENCE=Ref. Snapshot`（滚动的 reference，已证实；只代表所调查配置取证时的缺省）；选择 `Snapshot Number` 时，未覆盖的包取所选 Profile 快照 manifest 中的版本（已证实）。**本系统选择**把"最新"解析为与项目 / 分支匹配的**当时最新可用的 Profile 快照**——这是 CodingSystem 的策略、不是 Quickbuild 的缺省：它可能晚于当前 reference，也可能与之相同；选择更晚且缺乏推广证据的快照，可能增加基线自身失败的风险（设计推断，当前调查未量化失败率）。另一代价：在已调查配置（Tizen Base RBS 样本）中构建根取自 reference，能否在提交时独立固定为 `unverified`（调查 Q4：Profile 与构建根是两条输入链，样本中 Profile 为 Oct-28、构建根为 Oct-13），所选快照越新，源码与构建根的版本差距越大，可能出现与 patch 无关的构建失败——BuildReport / ImageReport 失败时附 Profile 与构建根两者的快照编号，供 LogAnalyzer 与审批人区分环境性失败（是否据此自动停止 AI 修复，待 P6 取得真实数据后再定判据，首期不设）。系统保存选取策略、所选快照及可取得的 reference 解析 / 推广证据，审批首屏按证据显示"与当前 reference 相同""已取得推广证据"或"推广状态未验证"（显式指定的快照同样按证据显示），不固定标注"未推广"。具体做法：该快照的 manifest 即本 Run snapshot manifest 的全部包版本（本地 RPM 阶段使用同一份），`BUILD_REFERENCE=Snapshot Number` + `SNAPSHOT_NUM` 锁定该快照（已证实）；开发者显式指定的个别包版本（即 Tizen 侧的"显式 base"）经 Build Package List（回显 `BUILD_PKG_LIST_MODIFY`）`仓库路径@完整 commit` 覆盖——**单包覆盖已证实，批量覆盖的数量上限、重复仓库与 Add/Modify/Remove 冲突处理为 `unverified`**，超出已验证形态的提交不得使用。快照发布时刻不构成逐包源码相对 gerrit HEAD 的落后上界（快照内单包版本可能远旧于发布日期）——审批首屏显示实际快照编号、发布时刻与逐包固定版本，落后量没有证据时标 `unknown`，不给保证。Remove Package List 的语义、优先级与权限为 `unverified`；Add 有样本依据。Tizen 侧未确认存在与 VD 相同的 Base CL 机制。
  - **被测源码身份（v2.4）**：每次构建生成 ExpectedSourceManifest——绑定 snapshot_id、series_id、逐包 base commit 与应用完整 series 后的 expected tree。基线构建使用空 series；被测构建使用当前 series：未改动的包取 base commit，**改动的包必须经已验证的构建暂存输入通道（不可变、与正式发布目标隔离，凭据仍只在 Gateway，按构建效应协议提交、探测与回收）送达远端，不得只提交 base commit**。该通道的形态与可用性为 `unverified`，P6 须验证非空修复、优化与撤销三种 series；未验证或后端不支持时，该后端**拒绝非空 series 的构建**（`backend_source_input_unsupported`），流水线配置选用 LocalGbsBackend——**校验器在加载期即拒绝**（§4.2.6，v2.5），运行时防御：仍发生则镜像节点返回 `image_failed_exhausted`(reason = `backend_source_input_unsupported`)、不进修复环；不得为满足构建输入而提前把 patch 发布到业务仓。
  - **只能读回的输入**：构建根所用的 base 仓库快照（`reference` 为滚动入口）、worker 实际消费的 build.conf、构建脚本版本——本次调查未证实可由提交锁定，按 `unverified` 处理。每次构建完成后读回并分别记录：子构建变量 / 日志解析出的 base 快照编号；`actual_build_conf_digest`（实际消费的配置）与 `published_build_conf_digest`（base 仓库发布的配置，repodata 中的 build 配置条目）——**后者只作取证附件，不代替前者**；实际配置不可得且没有经验证的确定性生成链（生成器版本与全部输入固定、可复核）时，实际配置身份为 `unknown`；脚本版本读到 commit 则记录，只读到分支名（如 `QB_SCRIPTS_BRANCH=master`）时为 `unknown`；全量 `BUILD_PKG_LIST`；以及可得的源码缓存使用迹象（包版本一致不等于已重新编译）。
  - **读回校验（规范条款）**：读回须同时证明基线包身份与 series 应用后的实际源码 tree 与 ExpectedSourceManifest 一致（新增包须与 Add 清单一致）；只有 base commit 回显、没有 series 应用证据时，不得产生当前 series 的成功 ImageReport。任一不符 → 该构建判为无效（ImageReport.succeeded = false，原因 `base_mismatch`），不进入缓存；镜像节点返回 `image_failed_exhausted`（reason = `base_mismatch`），**不经 LogAnalyzer 修复回流**（环境输入不可信，不是 patch 能修的缺陷），按路由走 fail_safe。
  - **A/B 可比性（v2.4：未知即不可比）**：基线与被测镜像的实际构建输入——base 快照编号、`actual_build_conf_digest`、脚本 commit、全量包版本中除本次 series 涉及的包以外的部分——**逐项有证据且相同**时，才生成 A/B 比较字段（`comparison = verified`）；任一不同或为 `unknown` → `comparison = unverifiable`：比较类判定字段缺失（阈值 gate fail-closed）、优化前后对比判为 `inconclusive`（§7A.4）、BenchReport 的"通过"谓词为假（§4.2.6①，**人工确认不能补出比较结论**）、该基线不进入跨 Run 缓存（§7.8），两侧绝对测量照常保留并作为 `environment_gap` 进入 `incomplete` 清单。按目前只读证据（实际 build.conf 摘要与脚本 commit 均不可得），Quickbuild 构建在 P6 补出实际输入证据前只能作**绝对测量**；需要 A/B 结论的流水线配置 LocalGbsBackend（全部输入由本系统控制）。被测与基线同批提交只用于降低漂移概率，不作为可比依据。
  - **提交标记与跟踪（v2.4：probe 有界）**：提交表单 BUILD NOTES（回显 `BUILD_NOTES`）写入效应标记（idem_key 指纹 + version）；提交 intent 同时持久化"提交前该配置的最大构建号"。提交成功后立即记录父 / 子构建号，之后按构建号跟踪父 trigger、子 build 与包级结果三个层次。Recent Builds 只显示最近 10 条，且无证据表明支持按备注搜索——提交结果不确定时，probe 自记录的构建号起**逐个**读取父构建变量匹配标记，扫描上限为构建记录保留期。证据等级：按已知构建号读取单个构建的变量与日志**已证实**；按构建号顺序扫描并识别属于本配置的构建（构建号跨配置交错分配，须按配置过滤）、缺号与权限缺失的处理为 `unverified`，P6 验证完整找回能力。超出可扫描范围、扫描不可用或无法判定归属 → `indeterminate`。远程构建效应因此登记为"可 probe（有界）"（§5.2）。
  - **取消**：Gateway 取消父 trigger 后，`cancel_pending` 跟踪父 trigger **及其全部子构建**，全部到达终态才归还远程构建配额（§4.3.4）；取消是否联动子构建为 `unverified`。
  - **镜像能力（v2.4）**：所调查的配置 1917 样本未产镜像（`TARGET_IMAGE` 为空、无 images 目录），未证实该配置其他参数组合能否产镜像；可产镜像的工程（如 Unified）的锁定字段与读回尚未调查——P6 前另行只读调查，结论出来前 QuickbuildBackend 的 `build_image` 为 `unverified`、不得启用。
  - **证据及时归档**：Quickbuild 构建记录保留 30 天、Artifact 10 天、下载站 RBS 7 天（站点公布政策，未核验后台实际清理时点）——构建完成后，ImageReport 需要的镜像、逐包日志、完整执行日志、manifest 与读回证据由后端立即拷入镜像存储 / artifact 存储（§7.8），不把远端链接当永久归档。
  - **并发**：Quickbuild 平台并发上限与配额未知（已观察到同一配置至少 3 个父请求同时运行），后端以本系统可配置的远程构建配额限流（§7.6.3），平台实际容量待管理员资料。
  - **开发者 patch 的基线早于锁定 base**：`submit_patch` 校验 patch 可在锁定 base 上**干净应用**（零 fuzz、不做三方合并，`git apply --index` 严格模式）——可应用则接受，并在结果中注明"patch 基于较旧版本，已在锁定 base 上应用"；不可应用则拒绝并给出冲突位置。
  - **审批呈现**：审批人只审本次改动及其带来的性能与稳定性变化；ReleaseManifest 与审批 CLI 显示 base 标识（锁定的 Profile 快照编号、发布时刻与基于证据的推广状态、读回的构建根快照编号、显式覆盖的包版本、解析时刻）、可比性结论与改动内容；未改动部分以该 base 为准。
  - 提交表单的控件定位属取证信息而非稳定 API（Wicket 动态字段），提交实现沿用既有工具"驱动浏览器在运行表单上填表"的方式，具体字段映射 `[待补充]`；P6 gate 的真实提交验收项（经负责人确认）：批量覆盖 N 个包、构建暂存输入通道（修复 / 优化 / 撤销三种 series）、按构建号读取标记、实际 build.conf 与脚本版本的取得方式、取消联动子构建、产镜像工程的锁定与读回。
- **CosmosBackend**（VD，后接 P8）：同 Quickbuild 形态，输入为 Perforce Base CL 清单、shelve CL 与 P4 版本的 BUILD_CONF（读回变量 `PACKAGE_LIST`、`SHELVE_LIST`、`BASE_REPOS`、`BUILD_CONF`、`PRODUCT_REPOS`）；同一 shelve CL 可被原号更新，因此必须记录 shelve 内容摘要而非仅 CL 号。P8 前另行调查提交映射。
- **廉价前置检查先行**：镜像构建前强制执行可快速完成的检查（patch 可应用性、ks 配置可解析、磁盘水位），避免长耗时构建末尾才暴露低级问题。**RPM 前置要求按节点配置 `rpm_precheck`**：`required`（缺省）——当前 series 的成功 BuildReport 为 hard-required 上游，RPM 节点须支配镜像节点（§4.2.6），仅存在旧 series 的报告即拒绝构建；`independent`——允许直接对 pinned snapshot + 当前 series 全量构建，不要求既有 RPM 结果（如优化专项首轮），ImageReport 如实标注"未经增量 RPM 前置"。
#### 7.6.2 多仓 snapshot manifest
snapshot = `[ {repo_id, remote, commit, path} ]` 规范化清单（使用 Quickbuild 后端时另含锁定的 Profile 快照编号与该快照 manifest 的全部包 commit、显式覆盖的包版本，"最新"在 pin 事务内解析为当时最新可用的 Profile 快照；构建根 base、实际 build.conf 与脚本版本以读回值记录，§7.6.1）；patch 逐条声明 repo_id；跨仓 series 按 manifest 序应用，任一仓失败即整体回滚该 worktree 组；tree_digest = 各仓应用后 tree hash 的规范组合（逻辑定义；计算为纯算法、无需 worktree，见 §4.2.4，算法 `[01]`）。
#### 7.6.3 资源额度（单机自我保护）
按资源类别计额：本地 RPM 构建、本地镜像构建（全量 + mic，默认并发 1）、板子（由板子池按可用板数管理；**单 Run 同时持有板数上限**，配置，缺省 1）、远程构建配额、ClineSR CLI 并发、worker 数；资源在分派前授予（§4.3.4），排队 FIFO；磁盘水位检查（低于阈值拒绝新 Run 并告警；镜像构建另设更高水位）；worktree 与临时镜像目录于 task 终结时清理，泄漏由定期对账回收。
#### 7.6.4 源码接入（SourceProvider）
接口：`pin_snapshot(target_spec) -> SnapshotManifest`、`materialize(snapshot, series) -> Worktree`、`to_backend_input(series)`（转换为构建后端所需形态：git patch / Quickbuild 输入 / shelve CL）。首期实现 **GitGerritSource**（Tizen）；**PerforceSource**（VD，后接 P8）以 shelve CL 集合映射 patch series——series 模型、tree_digest 与审批发布语义对两者统一，框架核心不改。

### 7.7 板子池（BoardPool，框架交付）
- **登记与能力探测**：每块板登记板型、架构、连接方式（如 sdb）与当前镜像；首次接入与每次刷机后运行能力探测脚本，记录 PMU / SPE / BRBE / ETM 等采样能力（Benchmark 采集 profile 与 Optimization 选择方法的依据）。
- **独占租约（Ledger 为权威，D6）**：UT、Benchmark、profile 采集按"板型 + 能力"申请，**在分派前由编排授予**（§4.3.4），FIFO 排队；能力匹配取"满足需求的最低能力板"以防强板被弱需求占满；单 Run 同时持板数受额度限制（§7.6.3）。租约带单调 **generation**，与 task 绑定；板上操作（刷机、执行、采样）及其结果一律携带 lease_id + generation，旧 generation 的命令与回报一律拒绝并审计（板型适配器无法在板侧强制时，以下述"静默确认 + 复位"作为唯一 fencing）。
- **序列租约**：Benchmark 交叉测量申请 `sequence` 租约，在同一租约内按 ABAB 序列交替刷写基线与被测镜像并测量，中途不释放、不被抢占。
- **回收 = reclaiming → 复位 → available**：task 终结、失联或超时后租约进入 reclaiming——先确认旧执行静默（旧 worker 进程组已 reap，且板型适配器的静默协议确认旧刷机/测试/采样不再在途），再复位（重启 + 健康检查；Benchmark 用途另需重刷已知镜像），通过后才转 available；无法确认静默 → quarantine 并告警，不重新分配。租约与回收状态持久化，编排重启先对账再开放分配。"租约超时"本身不构成外部效应已结束的证据。
- **刷机**：经板型适配器执行（刷机工具与流程 `[待补充]`，属适配器实现），刷机为可 probe 效应（读板上镜像标识，绑定 generation）。**失败按归因计数（Ledger 持久化）**：同一镜像在 ≥2 块板上刷机失败 → 归因镜像（ImageReport 标记坏镜像，板子不计数）；同一块板对 ≥2 个不同镜像连续失败 3 次 → 标记"维护中"并告警，不再分配。刷机失败时 task 以 `sys.error` 结束、按节点 retry 处理；重试 attempt 的分派授予**排除该 task 已失败的板**（`exclude_boards` 持久化于 dispatch），无其他满足能力的板时以资源等待排队（受 `external_timeout_min` 约束）——这样"多板失败才归因镜像"的规则在单 Run 持板上限为 1 时仍可达。
- **健康检查与静止判定（确定性规则）**：分配前检查在线、存储、温度等；Benchmark 测量前与每个用例结束后做静止判定——关键指标（CPU、内存等）在版本化的窗口、阈值与超时规则下平稳方可放行（规则随套件 BenchPolicy 固化，复用 TPMS 的判定思路），超时未静止则该次测量标记无效重测（重测受总预算约束）。**静止判定不调用 AI**；AI 只对异常给出解释（§7A.0）。
- **开发期**：FakeBoardPool（fixture 驱动，支持 generation、归因计数、延迟与重复回报）；真实板子联调在内网执行。

### 7.8 镜像存储、基线镜像缓存与 Profile 库
- **共同约束**：三者的权威状态（索引、引用、租约、pin、陈旧标记）均在 Ledger（D6），存储目录只存内容寻址对象；**对业务 worker 只读**（Profile 待验区例外，见下）——写入经 §8.5 数据面命令由编排事务提交，或由框架自有 task（保留 agent_type `sys.baseline_build`）完成。
- **镜像存储**：镜像体积大，独立于普通 artifact 目录存放，但**适用 §7.5 Blob 提交协议全部条款**（临时命名空间写入 + active-upload lease → fsync → rename 至 digest 路径 → Ledger 索引事务；索引前复验 digest；GC 仅回收超安全年龄且无 lease 的对象），大文件以分块 digest 清单承载；以 `image_ref = (内容摘要, snapshot_id, series_id, tree_digest, 构建输入闭包摘要, 后端)` 引用。**保留**：按引用计数保护——被任一活跃 Run、板子使用、上传中或缓存 pin 引用的对象不得删除；无引用后按保留期清理（默认 7 天，配置）；优化轮的"优化前"镜像在 Run 存续期内保留（§7A.4）。
- **基线镜像缓存（BaselineCache）**：缓存键 = (snapshot_id, **构建输入闭包摘要**, 后端, 镜像配置)；构建输入闭包覆盖工具链制品版本（gbs / mic / 编译器）、buildroot 依赖包仓的 pin 摘要、ks 内容及其依赖的 digest、后端实现与远端构建环境版本——任一分量变化即不命中；无法固定的输入使缓存不可复用。基线与被测镜像必须使用**相同**的构建输入闭包、只有 series/tree 不同，否则不得比较（BenchReport 拒绝产出 A/B 结论）。**写入**：仅框架自有 task `sys.baseline_build` 可写——Benchmark 节点的分派前置条件包含"基线可用"，未命中时以资源等待挂起 Benchmark dispatch（§4.3.4）；同键请求 **single-flight**（只构建一次，其余等待）。**归属（v2.3）**：`sys.baseline_build` 属于缓存而非某个 Run——以框架内部 Run（principal = `sys`，独立预算与执行队列条目）执行；各等待者只登记自己的资源等待，任一等待者取消只移除自身等待，全部等待者都取消时才取消该构建；基线构建失败 → 全部等待者收到 `baseline_unavailable`。Quickbuild 后端的基线以**读回的实际构建输入身份**作为缓存键的构建环境分量（§7.6.1）；实际输入闭包未被证明（任一分量 `unknown`）的镜像不得进入可复用基线缓存，发布目录的配置摘要只作证据附件。**失效**：TTL（默认 14 天）、运维手动失效、坏基线撤销（引用它的在途 BenchReport 标记 `baseline_revoked`）；对象缺失、损坏或未完成提交一律视为未命中。基线构建失败 → Benchmark 返回 `baseline_unavailable`（指标缺失，阈值 gate fail-closed，报告显式标注）。Quickbuild 的基线锁定与兜底见 §7.6.1。
- **基线测量**：每次 A/B 都按交叉方式在同一序列租约内重测，**不复用历史基线测量值参与当次判定**；历史基线测量按 (基线镜像, 套件版本, 板型) 归档，只作趋势参照与审计。
- **Profile 库（ProfileStore）**：每条 profile 记录 package 源码 tree（计算时排除该包登记的 profile 数据文件路径——否则提交 profile 的 patch 会使 profile 自身立即失配）、镜像/构建输入闭包摘要、被采样二进制标识（build-id）、采样格式与工具版本、板型与采样能力、套件版本、采集条件摘要；密级 internal_code（含符号与行号）。**新鲜度（首期定案）**：以优化方法插件声明的兼容字段**完全匹配**判定——缺字段或不匹配即拒用并请求重采；AutoFDO / BOLT 分别登记可消费格式与字段集合，插件版本纳入执行环境；**首期缺省不启用"代码有改动仍复用"**，放宽按下述预案以策略版本方式引入。**两区**：本 Run 采集的 profile 先写入待验区（键由编排按 task 连接上下文推导，不信载荷），只供同 Run、同 tree 使用；所属 Run 以 succeeded 关闭后晋升正式区，供其他 Run 读取。优化候选记录其源 profile 与被采样的父版本。最终交付给开发者的 profile 文件随优化 patch 进入各包自身仓库（§7A.4）。
- **Profile 复用放宽预案（新鲜度策略 v2，预先定义、缺省关闭，P7 以真实数据验证后按流水线开启）**：目标是小改动（加一行日志、改一处符号、改非热点函数）不必重新采集。判定全部为确定性规则，不交给 AI：
  0. **适用前提（v2.3）**：策略 v2 只适用于以伪探针一类选项（如 `-fpseudo-probe-for-profiling`）构建的包——该选项作为优化 patch 的一部分进入包仓（与 `--emit-relocs` 同理）并进入构建输入闭包摘要，A/B 两侧必须一致；采集版本或当前版本任一缺此选项 → 按策略 v1 处理。
  1. **前提**：除源码 tree 外，其余兼容字段（构建输入闭包中的工具链与构建选项、板型与采样能力、采样格式与工具版本、套件版本、采集条件）必须完全一致；任一不同仍按策略 v1 拒用。
  2. **函数级有效性**：以编译器为每个函数计算的校验和（伪探针 CFG 校验和一类）对比 profile 采集时的版本与当前版本——校验和未变的函数，其 profile 数据原样有效；校验和变化的函数，交给所用编译器自带的陈旧 profile 匹配能力（按调用点锚点重新对齐，含函数改名的调用图匹配；具体选项以所用 LLVM 版本实际提供的能力为准，P7 验证）尝试恢复，恢复不了的部分丢弃。
  3. **复用条件**：按采样权重计算的有效覆盖率（未变函数 + 匹配恢复成功函数的样本数 / 总样本数）≥ 阈值（缺省 95%，按包可配），且采样权重最高的前 K 个函数（缺省 K = 20）中没有"变化且未能恢复"的函数。满足即复用，否则重新采集。
  4. **记录与兜底**：复用时 OptimizationReport 记明"部分匹配复用"、有效覆盖率与被丢弃的函数；候选收益照常由"优化前 vs 优化后"A/B 判定、无收益即撤销（§7A.4）——放宽最坏只浪费一轮验证，不会让无效优化进入发布。
  5. **开启条件（v2.3：非劣证明，不以"不显著"代替）**：P7 前先固定评估的模块与改动类型集合、可接受的收益差异界 ε（缺省 1 个百分点，由负责人确认）、采样计划与统计方法版本；对"复用收益 − 重采收益"做非劣评估，其 95% 区间下界须高于 −ε，才可把策略 v2 设为对应模块类别、优化方法与编译器版本的新鲜度策略；区间跨越 −ε 或证据不足 → `inconclusive`，保持策略 v1。策略版本与参数进 execution manifest（D12）。
- **容量与 GC**：镜像、基线、Profile 分别配置容量与保留策略；GC 与分配由编排协调，磁盘不足时拒绝新构建，且不破坏在用对象。

---

## 7A. 各 Agent 设计要点（02–06 设计指引的输入）

### 7A.0 各 Agent 的 AI 能力与使用原则

| Agent | AI 主要做什么 | 不交给 AI 的部分 |
|-------|-------------|-----------------|
| Compiler | 分析编译错误日志，结合 LogAnalyzer 经验库、CodeGraph、LLM Wiki 生成修复 patch（最优方案 + 2 个备选） | 是否编译通过（由构建结果判定） |
| UT | 分析失败日志与崩溃信息（含 coredump 摘要），定位原因并生成修复 patch | 测试是否通过（由用例结果判定） |
| Benchmark | 按用例描述生成测试脚本；分析性能异常，给出原因初稿与可疑模块类别；解释静止判定失败等异常；生成测量报告初稿 | SPEC 达标与否、是否回归（由 SPEC 与 BenchPolicy 判定）；**板子静止判定与样本有效性（§7.7 确定性规则）** |
| Optimization | 依据性能数据与 profile 推荐优化候选并排序，解释收益来源 | 优化是否有效（由"优化前 vs 优化后"A/B 按 BenchPolicy 判定，§7A.4）；是否继续提案以外的任何放行 |
| Review | 审查代码改动；结合 CodeGraph 与业务部门的外接知识库给出审查意见；汇总全部报告形成结论 | 是否发布（由人工审批决定） |
| CI | 生成发布说明与变更摘要 | 发布执行（由 Release broker 按已批准计划执行） |

**使用原则**：
1. **判定与 AI 分离**——是否达标、是否回归、是否通过一律由 SPEC、统计规则或确定性结果判定；AI 的输出是分析、生成与建议，标注为"AI 初稿"，经人确认后才作为结论。
2. **先验证再推广**——AI 的修复与优化方案以每轮测试结果检验（原则 6）；分析类输出（尤其性能异常原因分析、优化候选排序）恒为 AI 初稿（`ai_draft`），不进入判定字段与路由（原则 5）。"扩大使用范围"指允许某项 AI 能力进入确定性检查之外的自动动作（例如不经人确认直接采纳其排序结果），任何此类扩大都须以策略版本登记并进入 execution manifest（D12），依据为原则 6 的统计数据。
3. **数据边界**——所有 AI 调用经 LLM 接入层，按数据密级校验可用的模型（D7），内网数据不出内网。
4. **可追溯**——AI 的每次输入证据、输出与采纳情况记入 Ledger，可按轮次回看。
5. **结构性保证**——报告中的判定字段（gateable 字段与各报告的"通过"谓词所用字段）一律由**框架统计库**从原始记录（测量记录、构建与测试结果）确定性计算；conformance 以复算比对强制，不一致 → `sys.invalid_result`。AI 输出只能进入报告的 `ai_draft` 子结构，不得进入判定字段，也不得作为路由依据。
6. **以测试结果检验 AI（v2.2 定案，v2.3 补验证资产保护）**——AI 给出的修复与优化方案每一轮都要重新经过构建、UT 与 Benchmark：方案可以错，但只要验证资产本身没被改动，测试结果就不会因 AI 而失真。据此：
   - **验证资产保护（确定性，v2.3）**：测试结果可信的前提是 AI 的 patch 没有改动"用来验证它的东西"。ModuleRegistry 为每个模块登记 `protected_paths`（测试源码、spec 的 `%check` 段、仓内基准脚本与解析规则、告警 / sanitizer 选项所在文件），框架另带确定性的 diff 检查规则（新增 `-Wno-*` / `-w` / 忽略诊断的 pragma、删除或短路 `%check`、新增测试跳过标记等）。series candidate 受理时对 AI 产出的段计算是否触及验证资产；命中时该段照常接受，但写入多版本对比报告与 `release_evidence`，并作为 `verification_asset_change` 条目要求审批人逐条确认（§4.3.5），未确认即不能审批通过。**审批前按"当前 tree 相对 snapshot 的净 diff 中归属 AI 段的部分"重算（v2.4）**——已被撤销、不在净 diff 中的触及项降为多版本对比报告中的历史记录，不再要求确认；后续 AI 段把它重新带回则在新段上再次命中。合理的测试修正（用例本身有错）因此仍可进行，只是必须经人确认。
   - **每轮结果全部保留**：每个 series 版本的 BuildReport、UTReport、BenchReport 及其测量记录在 Run 保留期内全部保存——被后续版本取代的报告不再作为放行依据，但**不删除**，用于对比。
   - **多版本对比报告（审批前必出）**：由编排在 ci_plan 的 task 完成事务内（terminal 型在 terminal 映射前、fail_safe 在生成 FeedbackReport 时）以框架统计库确定性生成（不由 AI 生成），作为内容寻址 artifact，其 digest 写入 ReleaseManifest 的 `release_evidence`，从而进入授权绑定（审批人看到的报告必然对应被批准的 series）；作为审批 CLI 首屏。列为**基线**（锁定 base、不含任何 patch）、**开发者原始改动**（若原始改动构建失败，如实写"构建失败"及失败摘要）、**之后每一轮 AI 修复 / 优化 / 撤销后的版本**（标明产出者与动因、是否触及验证资产）；行为构建结果、UT 逐用例集通过情况、每个 Benchmark 指标（中位数、区间、相对基线与相对上一版本的变化、SPEC 判定）；AI 对优化收益的预估与实测并列，修复 patch 标明其后构建与 UT 是否通过。
   - **分析类 AI 输出**（异常原因分析、候选排序、审查意见、报告初稿、发布说明）不产生 patch、无测试可直接检验，一律标注为 AI 初稿；审批人"采纳 / 不采纳"记入 Ledger，按能力统计**采纳率**。采纳与否不等于对错（正确建议可能因成本未被采纳，错误解释也可能被采纳），因此**准确率与误报率只在经独立复核取得事实标签的样本子集上计算**，并同时展示样本数、标注覆盖率与 unknown 数——回应总部"先验证再推广"的要求。
   - Run 被拒绝或 fail_safe 关闭时，FeedbackReport 同样附带截至当时的多版本对比，供开发者定位。

### 7A.1 Compiler Agent（本团队交付，LogAnalyzer 为分析引擎）
- **两种模式、两个节点**：`mode: rpm` 与 `mode: image`（D15），可分别出现在流水线中，也可单独删除镜像节点只出 RPM。
- **RPM 模式**：经 SourceProvider 物化 worktree、应用当前 series → 本地 GBS 增量构建受影响包与反向依赖。成功 → `build_passed`（BuildReport 绑定本 task 的 TaskInput.series，即实际验证过的当前 series）。失败 → 把日志交给 LogAnalyzer 引擎：日志解析 → 结合 LogAnalyzer 知识库、CodeGraph、LLM Wiki 组装 EvidencePacket → LLM 给出修复（task 内可在私有 worktree 中试构建以筛选方案，不计轮次、不提交）→ 最优方案作为修复 patch 提交**唯一** series candidate、另两个备选方案写入 BuildReport（该报告标注针对旧 series）→ 返回 `build_fix_patch_ready` 结束本 task；series 在完成事务内推进后由 `rpm_fix_loop` 重派 RPM 节点，在新 series 上正式重新构建（D15）。修复轮数由环预算限制；无可行修复 → `build_failed_exhausted`。**存在未决优化计划时**的构建失败不交 LogAnalyzer，只产出确定性撤销 patch（§7A.4）。注册为 `input_requirement: optional`——series 无净变更（如撤销回 snapshot）时按 series 涉及的包重新构建验证（§4.2.6 规则②）。
- **镜像模式**：按节点配置选择后端（local：GBS 全量 + mic，在构建隔离边界内执行，D22；quickbuild：经 Build Gateway，提交后以外部等待挂起，§4.3.4）。镜像阶段出现的构建失败（全量构建暴露、或远程构建环境差异）同样交 LogAnalyzer 分析：可修复 → 提交唯一 candidate、`image_fix_patch_ready` 回流 RPM 阶段；不可修复或超限 → `image_failed_exhausted`；存在未决优化计划时只产出确定性撤销 patch（§7A.4）。产出 ImageReport（image_ref、构建输入闭包、base 标识、读回的实际构建输入（Quickbuild）、耗时、失败与修复记录、`rpm_precheck` 方式）。
- **修复规则**（沿用 LogAnalyzer 约定）：真实代码缺陷直接修复并加注释说明原写法与修改原因，**不以关闭告警或屏蔽类编译选项绕过**；修复对开发者代码保持其原有命名与用法。
- **LogAnalyzer 接入形态**：框架定义 `LogAnalyzerEngine` 接口（`analyze(build_logs, context) -> Diagnosis{root_cause, fix_candidates[best + 2 alternatives], kb_refs}`，schema `[01]`）；实现为 LogAnalyzer 核心的 Python 封装，**LLM 调用一律经注入的框架 LLM client**（不得持有自有端点或凭据——数据边界、记账与 Fake 替身由此统一），开发期为 FakeLLMProvider；具体调用形态（库调用或 CLI）`[待补充]`。

### 7A.2 UT Agent（本团队开发；测试用例由业务部门提供）
- 定位：在板上对新镜像做稳定性测试（UT 测试）——验证改动后的系统在真实板子上能稳定运行，而不只是单个函数的单元测试。
- 输入：ImageReport（hard-required）与业务部门提供的 UT 测试用例集（按模块登记、带版本；只执行本 Run 目标范围内模块的用例集 + `always_run` 冒烟集，§7A.7；范围内无用例的模块在报告中标注"无用例"并进入 `incomplete` 清单）；所需板子租约在分派前由编排授予（§4.3.4）→ 刷入镜像 → 执行UT 测试 → 失败时分析并可产出修复 patch：提交唯一 candidate 后以 `ut_fix_patch_ready` 结束本 task、回流 Compiler RPM 阶段（D15）；存在未决优化计划时只产出确定性撤销 patch（§7A.4）。
- 产出 UTReport（板子、用例套件、通过/失败/跳过、失败分析）。刷机与板上执行均走 side_effect 幂等（§5.2）。

### 7A.3 Benchmark Agent（本团队开发；外接测试用例由业务部门提供）
- **套件来源三种**（D17）：
  1. **内置套件**：框架随附的适配器（首个为 TPMS 适配器），开箱即用；
  2. **开发者脚本**：开发者提供可执行脚本 + **声明式**结果解析规则（正则 / JSON path，声明输出指标、单位、方向：越大越好或越小越好；不执行代码，D13）；
  3. **开发者描述用例**：开发者用结构化描述写明"测什么、怎么触发、看哪些指标"，Agent 生成脚本 → **有效性检查**（在基线镜像上干跑两次：脚本能完成、指标确实来自被测对象、两次结果离散度在阈值内、无明显异常值）→ **人工确认一次** → 以版本号入套件注册表，此后与脚本型等同。生成脚本未通过检查或未经确认，一律不得作为基准使用（防止"测错了东西"）。
- **套件提交与确认通道**：开发者经 MCP `submit_bench_suite` 只能**提交**；**确认**经与 Review CLI 同类的本机特权通道执行（socket peer credential + 套件审核人名单），MCP/HTTP bearer 通道不提供确认操作——AI 不能确认自己生成的基准。确认人与所确认脚本、解析规则的内容 digest 记入 Ledger；套件内容 digest 变化必须递增版本并重新确认。
- **套件版本内容（SuiteVersion）**：脚本与解析规则的 digest、指标方向与单位、业务部门提供的 SPEC 边界与比较算子、**必测指标集合**、每种测量模式的用例集与样本数、**BenchPolicy**（下述）及其 golden 向量。BenchPolicy 不完整的套件不得激活；**运行期禁止由 AI 选择判定算法或样本有效性**。本 Run 引用的套件版本集合、SPEC 与 BenchPolicy 的 digest 进 execution manifest（D12），Run 中途变化按 D12 失配处理。
- **统计判定策略 BenchPolicy（随套件版本固化；以下缺省值定案，套件可以同构参数集覆盖、不允许自由代码，与 TPMS 科学性改造对齐时以参数覆盖）**：每臂**有效样本 n ≥ 10**（剔除静止判定失败与 CPU 争抢作废样本之后计）；ABAB 交叉；估计量 = 中位数；区间 = 95% bootstrap（BCa，10⁴ 次重采样，随机种子固定并写入报告；重采样器、舍入时点、并列值与退化处理随策略版本固化）；检验 = Mann–Whitney U 双侧，α = 0.05，多指标 Holm 校正。**两类区间（v2.3）**：`candidate_median_ci`（被测臂中位数区间，指标原单位）与 `effect_ci_pct`（A/B 相对效应区间，百分比）。**劣化方向统一为正**：越小越好的指标 r = 100 ×（被测 − 基线）/ 基线，越大越好的指标 r = 100 ×（基线 − 被测）/ 基线；只对允许相对比较且基线 > 0 的指标计算 r。基线为零、区间非有限（BCa 退化）、样本不足或无法合法计算 → 该指标 `inconclusive`。
- **逐指标结论**：`pass` / `fail` / `inconclusive` / `not_measured`。**SPEC 按类型判定（v2.3）**：套件为每条 SPEC 声明 `kind ∈ {absolute, relative}`——absolute（如"启动 ≤ 5 s"）用 `candidate_median_ci` 与 SPEC 边界比较，relative（如"相对基线劣化 ≤ 3%"）用 `effect_ci_pct` 比较，禁止跨量纲比较；三值规则：区间整体在 SPEC 内 → SPEC-IN，整体在外 → SPEC-OUT，跨越 SPEC 线 → SPEC-INCONCLUSIVE。`comparison: none`（无 A/B 对象）时只能做 absolute 判定。缺 SPEC、缺指标、样本不足或无法计算 → 不得生成"通过"的聚合值。
- **测量模式与判定效力**：模式由节点配置 `config.mode ∈ {full, single, quick}` 声明，Agent 运行时不得改变。**全量**（所选套件全部必测指标）、**单项**（只跑指定用例，用于针对性验证假设）、**快速**（精简用例与样本，用于开发期快速确认）。BenchReport 携带 `mode`、要求与实测的覆盖集、各指标有效样本数与 `validation_complete`（v2.3：所选必测指标集合**为空时为 false**，报告注明 `no_metrics_selected`）；**`gate_eligible = (mode == full) ∧ validation_complete`**——阈值 gate 的指标解析与 release_requires 的"通过"谓词只认 gate_eligible 报告，否则视为缺失（fail-closed）。单项与快速模式用于开发与诊断，不能作为发布证据；需要小范围发布验证时，以范围更小的套件版本（同样走 full 模式，且不得少于目标范围的最低必测集合，§7A.7）实现。
- **一次完整记录、无需重测**：每次测量同时记录测试指标、关键区间耗时（如启动各阶段）、资源使用（CPU、内存、IO 等时间序列）、相关日志与静止判定记录，统一存入**测量记录（MeasurementRecord）**——内容寻址 artifact，密级 ≥ internal_code（日志可能含源码路径与符号）；BenchReport 以引用携带。事后分析回归原因时直接使用这些附加信息，不需要为补数据再测一次（"无需重测"指不为补采分析信息而重测，不排斥无效样本重测与 A/B 交叉重复）。遥测采集配置在 A/B 两侧一致固定，避免测量扰动不对称。
- **判定字段确定性计算**：`regression_pct`、`spec_out_count` 等 gateable 字段与 `validation_complete` 由框架统计库从 MeasurementRecord 按 BenchPolicy 确定性计算（§7A.0 原则 5）。**`regression_pct`（v2.3 改为非劣形式）** = 全部必测指标劣化值 r 的 95% 区间**上界**的最大值，下限截为 "0.00"——阈值 gate `<= 5.0` 的含义因此是"以 95% 置信，回归不超过 5%"；样本少、噪声大时区间变宽、上界变大，gate 随之更难通过，不会因"检验不显著"而放行（原"显著回归点估计"的定义在低功效时 fail-open，已废止，保留为信息字段 `significant_regression_pct`，非 gateable）；任一必测指标 `inconclusive` 或样本不足 → 字段缺失 → gate fail-closed。`spec_out_count` 计入 SPEC-OUT 与 SPEC-INCONCLUSIVE（fail-closed），另列 `spec_inconclusive_count`。`opt_verdict` 同样用区间：改善方向区间下界 > 0 → gain。同一 MeasurementRecord 不论 LLM 给出何种建议，判定结论恒同。
- **测量方法**：与基线镜像做 A/B 对比（基线来自 §7.8 缓存，构建输入闭包必须与被测镜像一致）；在同一序列租约内基线与被测交叉执行；测量前与用例之间做确定性静止判定（§7.7）；同时监测测量期间是否有异常 CPU 争抢，有则该次结果作废重测。**空 series（`input: none` 首轮）**：只做绝对测量与 profile 采集，报告 `comparison: none`，不作为阈值 gate 输入。**优化轮**：存在未决优化计划时，另以计划的父镜像做"优化前 vs 优化后"第二组交叉 A/B（§7A.4）。
- **测量报告**：自动生成——包含 SPEC 判定结果、与基线的对比、统计区间与检验结果、BenchPolicy 版本、AI 给出的异常原因初稿与可疑模块类别（位于 `ai_draft`，标注为 AI 初稿）、每轮对应的镜像与改动；报告格式统一，便于与业务部门对接。
- **用例共享**：测试用例定义、测量方法、BenchPolicy 与测量环境（板型、镜像配置、负载条件）作为套件版本的一部分存放，可在不同部门（如 VD 与 SR）之间共享，保证双方测的是同一件事。
- **profile 采集**（`collect_profile: true`）：按板子能力探测结果选择采样方式（有分支栈记录能力则用之，否则用无分支栈的采样方案），采集结果经数据面命令写入 Profile 库待验区（§7.8）。
- 产出 BenchReport：`mode`、`gate_eligible`、`validation_complete`、顶层 `regression_pct` 与 `spec_out_count`、`spec_inconclusive_count`、逐指标结论与区间、BenchPolicy 版本、MeasurementRecord 引用、可疑与改动相关性分析（`ai_draft`）、本次采集的 profile 引用、优化轮的 `opt_gain_pct` 与 `opt_verdict`（§7A.4）。**所有回归都在报告中如实列出**，是否接受由阈值与人工审批决定，Agent 不做主观取舍。

### 7A.4 Optimization Agent（本团队开发，AutoFDO/BOLT 先行）
- **优化方法插件**（D18）：
  - **AutoFDO**：用 Profile 库中的新鲜 profile 生成编译用 profile（基于团队增强版 llvm-profgen），以 profile 引导重编受影响包；
  - **BOLT**：对热点二进制做链接后布局优化；
  - **CompilerGym 类搜索**：在编译选项 / pass 顺序空间中搜索更优配置——需要大量"编译 + 测量"，只在重量模式启用；
  - **MLGO 策略**：在可用的 MLGO 模型（如内联/寄存器分配策略）之间选择并验证。
- **两种触发模式**：
  - **轻量模式（`per_patch`，随普通流水线）**：针对本 Run 目标范围内的模块（含改动涉及的包，§7A.7），不只看改动的代码；用本次 Benchmark 采集的 profile 刷新其 AutoFDO/BOLT 数据；无明显收益机会则 `no_further_gain` 直接放行；
  - **重量模式（`campaign`，优化专项流水线，§4.2.1 示例二）**：由开发者手动或按周期触发，**创建时必须给出目标模块**（`focus_modules`），可启用全部方法，只对目标模块做系统性优化。
- **优化候选的推荐与排序**：复用 Benchmark 的测量记录与异常分析体系，按预期收益、风险与影响范围对优化候选（包括平台轻量化候选）排序，优先尝试排名靠前者；每个候选的实际效果以 A/B 测量评估后回填，用于改进后续排序。
- **产物与回流**：优化结果（profile 文件、构建选项或 spec 变更）以 patch 形式提交 series candidate → `opt_patch_ready` 回流 Compiler RPM 阶段 → 重新出镜像 → **UT 重跑**（BOLT/AutoFDO 等可能引入功能问题）→ **Benchmark 重测**；该路径由校验器强制（§4.2.6 规则③），不可经配置绕过。
- **优化计划（OptimizationPlan，Ledger 权威记录，v2.3）**：每个候选一条记录——`plan_id`、产出 task、`parent_series` / 父 tree_digest / 父镜像（"优化前"，在 Run 存续期内保留，§7.8）、候选段、目标指标与收益策略（BenchPolicy 的同构参数）、`state ∈ {pending_validation, accepted, rejected_reverting, reverted}`；在 series 推进事务内创建与迁移（收益判定写回除外，见下）。series 的每一段带 `purpose ∈ {initial, candidate, repair, revert}`，**由编排推导、不信提交方自报（v2.5；v2.6 定互斥顺序）**，按以下顺序判定、先命中者为准。**判定的事务位置（v2.7）**：series candidate 受理时只做预校验——按下列规则推导 purpose、校验准入、保存推导结果与 expected_parent / 关联 plan_id，**此时不创建或迁移 OptimizationPlan、不推进 series**（预校验不通过即时拒绝，如 `E-PLAN-NO-CAPACITY`、`E-CANDIDATE-NOT-REVERT`）；**权威复核在 §4.2.4 的 task 完成 / series 推进事务内**：校验父版本 CAS、当前计划、purpose 与准入，成功时与 lineage / current 推进一起原子创建或迁移计划；**复核推导的 purpose / plan_id 与预校验保存值不同，或准入不再满足（如收益判定写回在不推进 series 的情况下改变了计划状态、不推进 series 的环消耗了剩余次数）→ 与父版本 CAS 失败同一出口**：候选作废、计划与 series 均不变、task 以 `sys.error`（reason = `candidate_recheck_failed`，合法并发竞争）结束，按节点 retry 策略重试、重试时重新预校验，**不得按复核结论改记 purpose**（v2.8）。父版本 CAS 失败、候选作废、task 失败或候选受理后崩溃，都不改变计划状态；同一完成事务的重放复用既有 receipt，不重复创建计划、不重复累计候选轮数。判定规则：① **revert**——当前 Run 存在未决计划（`rejected_reverting`，或 `pending_validation` 且本次提交来自该计划重验证路径上失败的构建 / 镜像 / UT 节点），且本段使 tree_digest == **该计划**的 `parent_tree`（只匹配当前未决计划，不匹配历史已结束计划的树），不论提交者是否 Optimization：在上述完成事务内计划迁 `reverted`，不创建计划、不做候选准入、不计候选轮数；② **拒绝**——存在未决计划而提交不满足 ①（含 Compiler / UT 的非撤销段与 Optimization 的新候选）→ `E-CANDIDATE-NOT-REVERT`（未决计划期间只允许确定性撤销）——拒绝响应携带 plan_id 与 parent_tree，Agent 须在同一 task 内改交回到 parent_tree 的撤销段（撤销是确定性的，SDK 提供 `make_revert(plan_id)` 生成）；task 以其他 status 结束 → `sys.invalid_result`（v2.7）；例外：镜像节点的 `image_failed_exhausted`(reason ∈ {base_mismatch, backend_source_input_unsupported}) 仍按 base_mismatch 优先规则处理（v2.8）。预校验拒绝的提交不登记 candidate、不占"每 task 至多一个"名额，改交须使用新的 request_id（复用旧 request_id 返回首次的拒绝响应）；③ **candidate**——无未决计划，且提交节点注册产出 `optimization_candidate`：做创建计划的运行时准入（§4.2.6 规则③；预校验不足即返回 `E-PLAN-NO-CAPACITY`），完成事务复核通过才创建计划；④ **repair**——其余合法的业务修复段；`submit_patch` 受理的开发者初始段为 **initial**（来源仍按 producer 单独标识，repair 不等于 AI 来源）。因此待验证计划期间不存在修复段，判定锚点（父版本）恒为计划创建时的父版本；Benchmark、UT、Compiler 按"是否存在未决计划"判断，不看当前顶段由谁产出。
- **收益判定**：存在 `pending_validation` 计划时，Benchmark 除常规"被测 vs 基线"A/B 外，另以该计划的父镜像为"优化前"做第二组交叉 A/B，结果写入 BenchReport：`opt_gain_pct`（定点，gateable）与 `opt_verdict ∈ {gain, neutral, loss, inconclusive}`（区间判定，§7A.3），并由框架在 BenchReport 落账事务内写回计划记录：gain → `accepted`；neutral / loss / inconclusive → `rejected_reverting`；**优化前后 A/B 为 `comparison = unverifiable` 时 `opt_verdict = inconclusive`（原因 `comparison_unverifiable`）**——收益不可证明即撤销。同时报告相对 snapshot 的回归与相对父版本的收益——"相对基线仍快"不等于"优化本身有效"。
- **撤销（确定性，不做 AI 修复）**：计划处于 `rejected_reverting`，或计划待验证期间出现构建失败（Compiler 两模式）、镜像失败或 UT 失败时，相应 Agent 只产出**确定性撤销 patch**——series 以新段（purpose = revert）回到 `plan.parent_tree`（未决计划期间不接受修复段，撤销段即候选段的逆变更；v2.7）；**禁止回拨 current 指针**；动因 `revert_optimization`；分别经 `opt_patch_ready`（Optimization 撤销）、`build_fix_patch_ready` / `image_fix_patch_ready`（Compiler）、`ut_fix_patch_ready`（UT）回流。撤销段**不作为新的收益候选**，同一计划不会被二次撤销。**撤销段提交的 series 推进事务内计划即迁 `reverted`（v2.4）**——撤销是确定性的树回退，判据是 tree_digest == `plan.parent_tree`，与后续重验证结果无关；撤销后 series 的构建 / UT / Benchmark 重验证是当前 series 的常规义务（发布前由规则①③与审批 CAS 强制），结果按常规报告处理：重验证失败时已无未决计划，按普通修复环或 fail_safe 处理；Benchmark 不可比时 BenchReport 谓词为假、阈值 gate fail-closed。BOLT/AutoFDO 引起的编译问题因此不经 AI 修复，候选直接撤销、记为 rejected，换来可判定性。**`base_mismatch` 优先于确定性撤销（v2.5）**：构建输入不可信时撤销同样无法验证，镜像节点直接返回 `image_failed_exhausted`(reason = base_mismatch)，不产生撤销段；该 status 按路由走 fail_safe（绕过 UT / Benchmark 直达 terminal 的路由在加载期即被规则③拒绝）；未决计划随 Run 关闭在审计中记为 abandoned（不进入计划状态机）。
- **运行时强制**：存在 `pending_validation` 或 `rejected_reverting` 计划时，Optimization 返回 `opt_patch_ready` 以外的任何 status（`no_further_gain`、`no_gain_found`）→ `sys.invalid_result`（按节点 retry 策略可重试，违规归在 Optimization task）；campaign 的 `no_gain_found` 运行时核对"series 相对 snapshot 无净变更"，不成立 → `sys.invalid_result`（v2.7）；审批决定与 terminal 成功均核对"无未决计划"（§4.2.6 规则③、§8.2）。
- **轮次自限**：节点配置 `max_opt_rounds`，按本 Run **已创建的不同计划数**计数（修复段与撤销段不计）；上限只禁止创建新计划，**不得跳过当前计划的判定或撤销**。Agent 据此在达到上限且无未决计划时返回 `no_further_gain` / `no_gain_found`（确定性，无需感知环计数，D2）；**由创建计划的运行时准入（§4.2.6 规则③）保证任何已创建的计划都有撤销所需的环容量**，因此不会因"还想再优化"而让已通过验证的业务 patch 落入 fail_safe；候选提交被 `E-PLAN-NO-CAPACITY` 拒绝时 Agent 从响应得知原因并返回无进一步收益。
- **UT 归因**：存在未决优化计划时 UT 失败，UT Agent **不做 AI 修复**，只产出确定性撤销 patch（见上）；该计划标记 rejected。
- **status 集（按 mode 注册）**：`per_patch` = {opt_patch_ready (advances), no_further_gain (none)}；`campaign` = {opt_patch_ready (advances), no_further_gain (asserts_nonempty), no_gain_found (none)}。产出 OptimizationReport：采用的方法、源 profile 与被采样父版本、前后对比与 `opt_verdict`、被放弃或撤销的尝试及原因。
- **首期范围（定案）**：AutoFDO 首期只覆盖 **clang 构建的包**（团队增强版 llvm-profgen 产出 LLVM sample profile；GCC 构建的包首期不纳入，后续以 profile 格式转换链另行评估）；BOLT 首期只覆盖能加 `--emit-relocs` 链接选项的可执行文件，该链接选项变更作为优化 patch 的一部分提交；CompilerGym 类与 MLGO 在 P7 之后按同一验证规则接入。
- **发布**：profile 等文件最终进入各包自身仓库，属于发布行为——与普通 patch 同经人工审批 + broker，Optimization Agent 不持有任何提交凭据。

### 7A.5 Review Agent（本团队开发；外接知识库内容由业务部门提供）
- `mode: static`：镜像就绪后与 UT 并行，对 patch series 做静态审查（审查意见为 AI 初稿，进 `ai_draft`，采纳情况记入 Ledger，§7A.0）；
- `mode: final`：汇合全部报告（Build / Image / UT / Bench / Optimization / 静态审查），产出最终 ReviewReport——逐段出处的 patch 说明、各阶段结论、缺失与超时环节的显式标注（§4.3.5）；Review final 读取截至本 task 的各版本原始报告，**不引用尚未生成的正式多版本对比报告**（v2.4）——正式报告在下游 ci_plan 完成事务内生成，作为审批证据包中与 ReviewReport 同级的附件呈现（§7A.0 原则 6），不事后修改 ReviewReport；terminal / fail_safe 路径沿用各自终局生成点。
- **外接知识库**：业务部门提供的审查规范、领域知识、历史问题等内容，以 KnowledgeProvider 实现接入（出生即带密级，D7），审查时与 CodeGraph、LLM Wiki、LogAnalyzer 经验库一并检索；知识库内容的维护与更新由业务部门负责。

### 7A.6 CI Agent（本团队开发）
- 只产出 ReleasePlan（发往何处、发布哪些对象、基于哪个版本、是否 squash），位于人工审批之前；审批对象即其规范化后的 ReleaseManifest（含 `release_evidence`，§4.2.6 规则①）；执行由 Release broker 完成（§8.3）。注册为 `input_requirement: patch`：对无净变更的 series 不产出发布计划（空计划不存在）。

---

### 7A.7 目标范围与模块登记表（v2.2 定案，v2.3 补确定时点与增长规则）
定案原则：**每个 Run 都有明确的目标范围，UT、Benchmark、Optimization 只围绕目标范围工作**——只改了 multimedia，就不应顺带跑 Linux Kernel、APP 的 UT 与 Benchmark；优化也不能只看改动的那几行代码，而要看本次要求关注的模块。同时，**改了的代码必须被验证**。
- **模块登记表（ModuleRegistry，带版本）**：每个模块登记其包集合、UT 测试用例集、Benchmark 套件（含必测指标）、优化可作用的二进制、验证资产路径 `protected_paths`（§7A.0 原则 6），以及可选的 `always_run` 冒烟集（如开机与基本稳定性用例、整机关键性能指标——任何改动都应覆盖的全局底线）。内容由业务部门随测试用例一并提供、本团队维护格式与校验（§2.5）。**Run 创建时 pin 登记表与套件注册表的版本**（快照 digest 进 execution manifest，D12），之后一律按该快照解释。
- **目标范围的确定时点（v2.3）**：
  - `input: none`（优化专项等）：`focus_modules` **必填且非空**，即本次优化目标模块；未登记的模块名拒绝创建；范围在 snapshot pin + 初始空 series 的同一事务内确定。
  - `input: patch`：`create_run` 时尚无 patch，只记录开发者声明的 `focus_modules`；**首次 `submit_patch` 受理事务内**按 pin 的登记表计算初始范围 = patch 改动涉及的包所属模块 ∪ `focus_modules`，并一次性确定实际选用的用例集与套件——此初始化完成前不得分派、不得审批；同一 request_id 重放返回同一范围；事务失败不留下部分范围或半签发的 series。
- **范围只增不减（v2.3）**：之后每次 series 推进事务内，按当前 series 全部段所涉的包重算模块集合，与旧范围取并集——AI 修复或优化改到了范围外的已登记模块，范围随之增长，下一轮 UT / Benchmark 自动包含这些模块的用例集与套件（"改了的必须验证"，同时"只因真实改动而增长"，不会无故扩大）；范围增长写入报告头与多版本对比报告。实际选用的套件是"pin 的注册表快照 × 当前范围"的确定性函数，范围增长不构成 D12 失配（注册表本身中途变更仍失配）。任何 series candidate（含 AI 修复与优化）涉及**未登记模块**的包 → `series_candidate_submit` 拒绝，该 task 不得以 `advances` 类 status 结束；`submit_patch` 同理拒绝并提示补登记。
- **范围写入与呈现**：有效范围写入 Run 记录、ReleaseManifest 与全部报告头；审批 CLI 与 `get_result` 首屏呈现"本次验证范围"，另列"受影响但不在范围内的模块"（RPM 阶段构建的反向依赖闭包所属模块 − 有效范围），作为提示信息、不阻断。
- **各 Agent 如何使用**：UT 只执行范围内模块的用例集 + `always_run` 冒烟集；Benchmark 节点 `suites: auto`（缺省）时按范围选套件 + `always_run` 性能冒烟集；**显式列出套件只能增加验证或选择登记表中声明为等效替代的套件**——发布用的 full 模式不得少于"范围内模块的必测套件 + `always_run`"这一最低集合，`gate_eligible` 以该最低集合（而非调用方任意子集）的覆盖完整为准，诊断用的子集可以测，但不能作为完整发布证据；Optimization（per_patch 与 campaign）的候选只针对范围内模块的包与二进制，profile 只为这些二进制采集；Review 的外接知识库检索按范围过滤。
- **范围外回归**：由 `always_run` 冒烟集兜底（R25）。

## 8. 安全

### 8.1 信任模型（D13）
内网单机、单操作员运维；Skill 调用方经 bearer token 认证、视为受信；**patch 与其触发的构建脚本视为半可信**——不做完整容器沙箱（N7），控制面为：凭据物理隔离于 broker（8.3）与 Build Gateway（8.6）、能力句柄按授权注入（5.1.1）、worker 子进程可强杀、发布必经 token、**以 root 执行半可信内容的构建步骤在独立内核边界内进行（D22）**——OS 用户隔离对 root 无效，故此项不属 N7 豁免；Benchmark 脚本只在测试板执行、宿主侧解析规则限声明式（D13）。残余风险（恶意构建脚本网络外传源码等）登记 §14 R7，由内网环境与来源受信假设覆盖；该假设失效（如接入不受信来源）时必须先补沙箱。假设边界显式包含：**调用方认证 ≠ 内容可信**——patch 为 LLM 生成物、上游提示与语料不受控，间接提示注入可使受信来源产出恶意构建脚本，此路径属 R7 覆盖范围。

### 8.2 Approval 服务（框架交付）
- 独立进程 + **Review CLI**（MVP 形态；§9 Web 视图保持只读，不承担审批）。服务仅监听本机 Unix socket，远程 reviewer 场景显式不支持（D13）；CLI 认证 = socket peer credential（本机用户）+ 服务端 reviewer 名单。
- **审批对象 = ci_plan 产出的 ReleasePlan 规范化而成的 ReleaseManifest**（snapshot、tree_digest、发布目标、动作、pipeline_digest、exec_manifest_digest）——reviewer 在 CLI 看到并批准的即 broker 将执行的内容（示例流水线中 ci_plan 前置于 human_review 即为此）。
- （本节全部条款仅适用 **release-approval 型** hitl；plain-decision 型的 approve/reject 单命令只含决定 + gate outcome CAS + resume outbox，无 manifest 与授权记录项，§4.4）approve 经 control-plane RPC 单命令原子提交：审批决定 + **Ledger 授权记录（绑定字段见 §3）** + gate outcome CAS + resume outbox；事务内 **CAS 校验新鲜度**——gate 仍 waiting、被批 ReleasePlan 仍为该 Run 当前版本、series/tree_digest 仍为最新、**`release_requires` 清单内每类报告均存在、针对当前 series 且结论为通过（§4.2.6 规则①）**、**不存在 `timeout` 类未完成条目与未决优化计划、全部 `environment_gap` / `verification_asset_change` 条目与当前 series 证据链上的 `retried` 记录均在本次决定的 `acknowledged_gaps` 中按 (条目 id, 内容 digest) 逐条确认（§4.3.5）**，任一不满足即拒绝并提示 reviewer 重审（series 推进事务同时撤销待审批项与未核销授权，§4.2.4）。CLI 首屏呈现 manifest、base 标识、`release_evidence`、多版本对比报告（§7A.0）、`incomplete` 清单（§4.3.5）与"本次未执行的验证类别"，并呈现关联证据链（ReviewReport、逐段出处的 patch series、各阶段 Report 引用；plain-decision 型呈现该 gate 上游 Report 与决策上下文——两型清单均细化入 01/07）；manifest 规范化算法 `[01]`。授权不以 bearer 形态存在、不进图状态/checkpoint；**权威判据唯一 = Ledger 记录**，无签名/HMAC 第二通道。
- series 变化 / Run 关闭 / 过期 → 未核销授权自动失效；过期授权被消费时 broker 返回 release_failed(reason=authorization_expired)。

### 8.3 Release broker（框架交付）
- 独立进程，唯一持有发布凭据；输入 = release 节点转发的 ReleasePlan + 授权引用（token_id，非 bearer）。
- **核销前置检查**：D12 制品/配置 digest 复核在核销之前执行——版本漂移以专用控制面错误码上报编排层并触发 administrative finalize，**不烧授权、不伪装成 release_failed**（R3-11 定案）。
- 原子 compare-and-consume = 发布 **point-of-no-return**：经 control-plane RPC 在 Ledger 事务内校验授权（未核销、未过期、全部绑定字段——run/gate/decision/ci_plan_task/series/manifest——与当前状态一致；**v2.3：并复核 §4.3.5 放行条件——审批之后新增 `timeout` 条目、新增或内容 digest 变化的未确认条目 → 不核销，consume 返回 ConsumeRejected(reason = `gaps_changed`)，编排在 ledger 级按 release_failed 映射关闭，broker 不发 outcome（v2.4 定案，v2.5 校正协议表述）**）、标记核销并**原子迁移 Run → publishing**；publishing 期间 cancel / 并行 fail_safe / series 更新 / **administrative finalize** 一律仅登记 pending、不得先关闭 Run；**publishing 是 administrative finalize 的状态级例外**——即使 D12 漂移或进程重启，也必须先与 broker 对账或 probe 远端结果，不可判定时保持 publishing 待人工处置。**终态映射（固定表，ledger 级执行、不经 DSL 路由，细则 `[01]`）**：broker outcome 优先——released → closed(succeeded)（pending 事件记入审计与 **Run 终局摘要**——非 FeedbackReport，不改变已发布事实）；release_failed → 按序应用 pending：**administrative finalize（最优先：ledger 级 closed(fail_safe) + 版本漂移 FeedbackReport）** > cancel → closed(cancelled) > fail_safe → closed(fail_safe) > 均无 → closed(fail_safe) + ledger 级生成 release_failed FeedbackReport；series 更新仅记录。故障注入含 pending 组合断言（§11.3）。核销绑定 task_id——broker task 中断恢复时"已核销给本 task"视为有效。
- 发布执行远端幂等（push 前查远端）；远端冲突 → release_failed，禁止自动 rebase（R9）。
- **人工裁决协议（publishing 滞留出口，R13）**：仅对处于 publishing 且强制 probe 后仍不可判定的 Run 开放；命令三选一——`confirm_released` / `confirm_not_released` / `keep_unknown`（继续等待），前两者**必须附远端证据引用**。`confirm_not_released` 附加三重防迟到机制：① 状态 guard 前置 **broker 侧静默**——broker task 进程组已终止（lease 回收 + pgid reap 确认），本地不存在在途发布执行；② **fencing 标识**——发布操作向远端写入的对象一律携带唯一标识（commit message/Change-Id 含 run_id+token_id），迟到发布可归因；③ **裁决后复查窗口**——关闭后按配置窗口（默认 24h）**周期性**重 probe 远端（频次配置），窗口结束后并入常规审计对账（监视不终止）；检出迟到发布 → 告警 + **post-close correction 记录**：append-only 特权命令（同裁决通道权限），绑定原裁决、远端对象与证据引用、操作者、处理状态，单 Ledger 事务提交；**原终态不可变**，`get_result` 在终局摘要之外一并返回有效 correction 引用（调用方可见真实远端状态）。已离开本机的在途网络请求无法绝对 fence（git/gerrit 端点无两阶段提交），此为显式残余（R14）。经特权 OS 用户 + peer credential 执行；裁决记录（操作者、证据引用、按 §8.3 映射的终态迁移）单 Ledger 事务提交；E2E 故障用例（含证据缺失拒绝、broker 未静默拒绝、迟到发布检出）入 §11.3。
- **发布 adapter 归属（定案）**：gerrit 与 github 官方 adapter **由框架交付**、运行于 broker 进程内、纳入安全审计与版本 pin——broker 进程内代码全部属可信计算基，不接受业务侧同进程插件。其他 CI 工具扩展走受限模式：业务 adapter 运行于**无凭据子进程**、产出受限操作描述，由 broker 以框架凭据原语执行。§5.1.1 能力句柄清单显式排除发布通道。FakePublisher 随框架交付供测试。

### 8.4 脱敏与审计访问
持久化统一脱敏：凭据/secret 只记指纹（授权本身即 Ledger 记录，无 bearer 需脱敏）；LLM prompt/响应 artifact 带密级标签；Web 视图只读 + 本机访问；审计记录保留策略随 §7.5。

### 8.5 Control-plane IPC（特权内部接口，双向）
- **入向（→编排进程）**：Unix socket + peer credential 认证；Approval 服务、broker、worker 使用**不同 socket、不同 OS 用户与文件权限**。worker socket 仅开放**数据面命令**（显式枚举：side_effect 状态迁移、trace、artifact 索引提交、series candidate 提交；**勘误 E-03 追加**：`task_suspend`（远程构建在途时结束本 attempt，§4.3.4）、`resource_lease_release`（仅本 task 已获授予的租约，授予由编排在分派前完成）、`image_commit`（镜像存储提交协议的索引事务，§7.8）、`profile_put`（写 Profile 库**待验区**，键由编排按连接上下文推导，不信载荷）、`remote_build_submit` / `remote_build_fetch_logs`（编排以连接上下文校验 run/task 归属后转发 Gateway；远端状态查询由编排侧 poller 执行，取消仅由编排在 cancel / fail_safe / supersede / 预算到期时发起））；每条新命令沿用 task 级绑定、request_id 幂等与越域拒绝审计；**v2.3 细则**：镜像文件由 launcher 自构建边界的只读导出通道写入镜像存储临时命名空间（持 active-upload lease），worker 对存储目录无写权限、只调用 `image_commit` 提交索引；`remote_build_submit` 载荷只引用本 task 已 claimed 的效应记录（idem_key + version），效应标记由编排据该记录推导、不信载荷；`resource_lease_release` 在板型适配器能在板侧强制 generation 时立即进入回收，否则仅标记 release_requested、于 task 结束后按 §7.7 完成回收；跨 Run 共享存储的正式区与基线缓存无任何 worker 写命令（§7.8）。审批与核销命令所在 socket 对 worker 进程不可访问（文件权限隔离）。
- **task 级绑定**：worker 数据面通道为 **per-task socketpair**，FD 由编排进程 spawn 时注入——无文件系统监听端点，伪造连接构造上不可能；仅接受注入的预绑定连接，其余一律拒绝并记审计。服务端从连接上下文推导 run_id/task_id 并以 Ledger task 租约校验——客户端不得自报归属，越域请求拒绝并记审计；conformance 含跨 task 篡改拒绝用例（§11.3）。
- **出向（编排进程→broker）**：broker 发布调度端点仅接受编排进程 UID（peer credential），请求绑定 run/task/manifest。
- 命令幂等（request_id）；复合状态变更（审批提交、授权核销+publishing 迁移）为单命令单事务；resume outbox 语义见 §4.4（decision_id 去重）。
- **Build Gateway 通道（v2.0）**：Build Gateway 为独立 OS 用户与独立 socket；业务 worker 不直连 Gateway——远程构建请求经 worker 数据面命令到达编排进程（编排以连接上下文校验 run/task 归属后代为提交），**构建 socket** 只接受编排进程 UID；另设**运维会话 socket**（独立 OS 用户 + peer credential，仅运维特权用户可连），只承载会话注入命令（§8.6）。
- **部署 provisioning 属交付物**（§10 deploy/）：系统账户创建、socket mode/ownership、Ledger 与凭据文件权限、多用户 spawn 的专用特权 launcher（属可信计算基）、服务启动顺序；P4 gate 含真实 UID/文件权限下的 E2E 隔离测试。

### 8.6 Build Gateway（框架交付，v2.0）
- 独立进程，**唯一持有 Quickbuild 会话**（VD 后接时同样承载 Perforce 会话）；不保存账号密码，属可信计算基，与 Release broker 同等审计要求，不接受业务侧插件。
- **职责**：提交远程构建（写入效应标记 = idem_key 指纹 + version）、查询状态（供编排侧 poller 与 probe）、拉取日志与产物元数据、取消构建；全部操作记审计。**幂等**：以效应标记为 Gateway 请求去重键与远端归因标记；Gateway 崩溃重启后由 probe 按标记查询远端归因，不依赖 Gateway 内存状态。
- **会话注入通道（定案）**：会话失效时 Gateway 向运维发出告警；运维机器上的登录助手弹出浏览器窗口，由运维本人完成 SSO 登录；登录助手经 SSH 端口转发调用 Gateway **运维会话 socket** 的 `session_install{session_blob}`（§8.5）；Gateway 安装前调用 Quickbuild 身份接口校验**会话主体 == 配置的服务账号**，不符即拒绝并审计（防错账号构建与会话固定）；会话只保存在 Gateway 进程受限存储中（不落盘，或仅落 Gateway 专属加密存储）。
- **会话失效期间**：依赖远程构建的等待项（含尚未提交、提交结果不确定与对账阶段的会话等待，§4.3.4）计费类别切为 non_billable 并告警；对查询类请求返回 `dependency_unavailable`，probe 结果映射为 **deferred**——不消耗 probe 重试次数、不进入 unknown，对账推迟到会话恢复；其余节点不受影响。超过配置的登录等待时长 → 编排为对应 task 合成 `sys.timeout` 并固定路由 fail_safe（不经节点 retry，§4.3.4、§4.3.5）。
- **取消传导**：编排在 cancel、fail_safe 取消分支、series supersede 退役在飞任务、预算到期时，对相关远程构建发起取消（幂等；失败告警不阻断终局）。
- **脱敏**：日志与产物元数据进入编排与 worker 之前，按 §8.4 规则剥离会话凭据形态的字段（会话 URL、token、cookie）。

---

## 9. 可观测性
基于 Ledger/trace.jsonl 的只读本地 Web 视图（Python 实现，不引入 PHP，D23；Run 状态、节点进度、循环计数、token 消耗、artifact 浏览、**板子池占用、镜像与远程构建队列、Benchmark 对比图表、优化前后对比**）；指标离线聚合。不引入外部观测平台。

---

## 10. 部署形态与仓库结构

**部署拓扑与网络边界（v2.0）**：

| 位置 | 部署内容 |
|------|---------|
| 内网主机（单机） | 编排进程、Approval 服务、Release broker、Build Gateway、MCP 服务（含 HTTP 端点）、Ledger 与存储、各 Agent worker、ClineSR CLI（专用 OS 用户 + 出口规则，§7.1） |
| 构建隔离边界（同机一次性构建 VM；无 KVM 时为独立构建主机，D22） | GBS buildroot 的 sudo 段与 mic；无凭据、无 Ledger、无 control-plane socket，产物经只读导出通道交回 |
| 运维机器 | Quickbuild 登录助手（弹出浏览器，经 SSH 端口转发向 Gateway 运维会话 socket 注入会话，§8.6） |
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
│   ├── gateway/           # Build Gateway（Quickbuild 会话、提交/查询/日志、运维会话 socket）+ 运维登录助手
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
├── deploy/                # 安装脚本、systemd 单元、账户/权限 provisioning、特权 launcher、构建 VM 镜像与启停、CLI 专用用户与出口规则
├── docs/                  # 00–09、review/、dev_memory 说明
└── ci/
```

分发（D4）：框架构建为 wheel `codingsystem-framework`（含 extras），业务 Agent 依赖该包并经 entry-point 注册；发布 gate 进 ci/。

---

## 11. 技术栈与质量门禁

### 11.1 技术栈
Python ≥ 3.12；LangGraph 依赖闭包 lockfile 锁定（D1）；pydantic v2；SQLite(WAL)；PyYAML。只读 Web 视图（§9）同样在 Python 技术栈内实现（前端为静态资源）。**不得引入 PHP（D23）**。

### 11.2 门禁
pytest + coverage 全局 ≥ 80%；**关键模块（orchestration、ledger、approval、release、sdk.side_effect）分支覆盖 ≥ 95%**；mypy --strict；ruff；import-linter（引擎封装）；**无 PHP 检查（D23，v2.9）**——**判定信号**（任一命中即失败）：包元数据中的 php 包或对其的依赖（rpm / deb 包名与 Requires 等）；`php` / `php-cgi` / `php-fpm` 可执行文件、`libphp*` / `mod_php` 共享库；`.php` / `.phar` / `.phtml` / `.php3`–`.php8` / `.phps` 文件、shebang 为 php 的文件、含 `<?php` 标记的文件；`composer.json` / `composer.lock`。**仅命中文本标记时的分类（v2.10）**：规范文档、扫描器自身的规则表与单元测试、负向测试的合成清单只在文字中提到 PHP，不是 PHP 实现或运行时依赖；仓内受审阅、绑定策略版本的固定规则可把它们归为**非执行数据**，只免除"`<?php` 标记"这一文本信号——这些文件不得有可执行位或 php shebang，不得被任何交付物用作入口、模板或解释器输入，文件后缀、shebang、包、可执行文件与 composer 清单等其余信号照常判定；不接受插件自报豁免，不对 `docs/` 或 `tests/` 作整目录免扫，无法确认分类时仍拒绝。**扫描对象**：仓库全部文件；全部 lockfile（Python 与前端构建链）；deploy 镜像、构建 VM 镜像与镜像基础层按 digest 展开后的**实际安装集与文件**（不以镜像名称或顶层清单代替）；随交付的前端资源、运维工具、测试夹具及其传递依赖；本产品主机上 **deploy 清单解析出的安装集与本产品安装前缀**，以及本产品进程实际调用的工具闭包（含主机预装而被调用者）；运维机只扫描 deploy 安装的登录助手及其运行闭包——二者在 deploy 验收与 E0 预检中扫描（CI 看不到的部分不得省略）。主机上既非 deploy 安装、又不被本产品调用的预装包命中判定信号时只在预检报告中列出，不判门禁失败；工作区、Ledger / artifact 存储、基线镜像缓存、Profile 库等业务数据目录不扫描其内容（D23 排除项）。**注册准入**：插件、受限 adapter、宿主侧适配器注册时，运行时声明合规且制品内容（含入口的 shebang 与 ELF 类型）与运行环境闭包通过同一扫描；扫描结论绑定制品 digest、闭包 digest 与策略版本，纳入加载期 attestation，digest 变化即重新检查，缺闭包证据拒绝加载；部署后新增的工具或依赖须先通过扫描。**例外与复核（v2.10）**：只有 D23 所述经负责人修订前提批准的例外条目可使对应 digest 通过，E0 记录本身不放行；扫描策略版本升级后，全部注册记录与主机安装集重新扫描，未通过者拒绝加载；deploy 安装集的 digest 在验收时记录并写入 execution manifest（附录 B 第 7 组同步），Run 创建时与最近一次通过扫描的 digest 比对，不一致即拒绝创建并要求重新验收——运维绕过 deploy 直接安装的依赖因此会被发现。不扫描 D23 排除的业务内容（conformance 断言：buildroot 装入含 php 的业务包不报，deploy 清单中第三方工具传递依赖 php 即报）。

### 11.3 强制测试类别（P1–P4 gate 组成部分）
DSL property/fuzz（随机图 → 校验器判定性质：可达环必有 budget、release 必经 hitl 等）；状态机 model-based 测试；**逐持久化边界故障注入**（每个 Ledger 提交点前后 kill，验证恢复与对账）；token 并发双消费测试；陈旧 series 进 gate/join 拒绝测试；checkpoint/execution manifest 不匹配拒绝恢复测试；artifact 损坏检测（digest 校验）与 blob 提交顺序逐点崩溃注入（孤儿 GC / dangling 索引对账）；control-plane IPC 权限隔离测试（worker socket 不可达审批/核销命令；跨 task 篡改拒绝；真实 UID/文件权限 E2E）；同 series 多轮循环下 join activation 分组与崩溃重放，含四组 model-based 断言——旧 activation 已首达后推进 series → stale 超时不误杀；同 series 并发多 activation 独立成组；不推进 series 的环（旧源已到达、环边采用、新 activation 成功、旧计时器后到 → 条件③已退役、无误杀）；父退役级联（嵌套子 activation 计时器同事务作废、不误杀，替代 cohort 继承父 scope 后参与外层 join）——及"分支内回环（不重经共同 fan-out）与跨祖先回环（先重经祖先 activation 的 fan-out）均拒绝加载"validator property；跨 attempt 三支定态 × 异参 claim 动作矩阵（succeeded/abandoned 放行新键、succeeded 不跨参复用、unknown 无新键、干净终态 failed 依类别策略放行）测试；publishing 终态映射 pending 组合（含 pending administrative finalize）故障注入与人工裁决 E2E（证据缺失拒绝、broker 未静默拒绝、迟到发布检出）；post-close correction（迟到检出、重复/并发修正、get_result 呈现）；effect_call_id 唯一性 conformance 与"双同参调用首成后崩溃、重试控制流变化"注入；probe-only / replay_safe / 皆无三类效应对账覆盖；join 作用域与共同到达 validator property（嵌套 fan-out、互斥 outcome、嵌套汇合重入外层三类反例）；恢复复用既有 dispatch 记录断言；publishing 期间进程重启/D12 漂移的对账优先注入；blob 上传与 GC 并发注入；编排进程崩溃且 GBS 子进程存活注入；六类 agent_type 的 contract producer/consumer fixture 兼容测试；**v2.0 追加**：即插即用组合测试（§2.4 表中每种删除组合加载校验通过/拒绝符合预期，降级报告标注正确；删除生产者但保留 release_requires 条目 → 拒绝；空清单无 `accept_unverified_release` → 拒绝）；**四份示例流水线原文字节加载通过**，并对 full_pipeline 做反例变体（把 bench_gate 移出 join 来源 → 汇合必经检查拒绝；join 超时后断言不触发其 `to` 下游、只路由 fail_safe；删除 compile_image 而保留 image_report → 拒绝、不得由 compile_rpm 满足）；**超时显式化**（join 超时、节点硬超时、预算到期、外部等待超时、gate_expired 各一例：发布前未被重试覆盖的超时 → Run 经 fail_safe 关闭、不得以 succeeded 关闭（publishing 之后的超时按 §8.3 远端事实映射，首屏保留全部异常）、FeedbackReport 第一节为超时清单、get_result 的 incomplete 清单含该项且 Skill 原样呈现；超时后重试通过的进入 retried 清单；gate_expired 与 approved 同目标的路由 → 拒绝加载）；release_requires 运行时测试（任一产 patch 节点推进 series 后缺任一必需报告、或报告结论非通过时审批提交被拒；ReleaseManifest digest 含 release_evidence；CLI 首屏呈现快照）；**修复回流**（RPM 修复 S0→S1 后在 S1 上重新构建、成功报告不得重标 series；完成事务前后 kill；环预算耗尽）；`rpm_precheck` required 缺 RPM 报告拒绝、independent 可执行；`input: none` 生命周期（无 advances/asserts_nonempty 边即到达 needs-patch 节点 → 拒绝；`asserts_nonempty` 无净变更返回 → sys.invalid_result；初始空 series 签发逐提交点 kill；pin 失败不排队；submit_patch 拒绝且 MCP/HTTP 一致；空计划不可产出）；**外部等待（E-02）**：等待期间无 worker 存活断言、paused(wait) 时他 Run 取得执行槽、wake outbox 重复投递不重复分派、续接 attempt 复用提交效应不重复提交、"两 Run × 一板 × 一槽"租约/执行槽锁序 model-based 无死锁、外部等待 × gate × 会话失效的组合计时、paused 中预算到期取消远端、等待登记/唤醒前后 kill；远程构建效应（同 task 双 call_id / 异参 / 新 version 各自归因、提交后 ACK 前 kill、查询延迟可见返回 indeterminate、取消后迟到完成丢弃、会话失效 probe deferred 不计次）；镜像效应（半成品不被 probe 命中、被测与基线镜像互不命中、镜像提交逐点崩溃注入）；**特权构建隔离 E2E**（被测包 `%post` 尝试读 broker 凭据、读 Gateway 会话、连接 approval/broker/worker socket、写 Ledger → 全部失败并告警）；**worker 数据面扩展命令**（跨 task 释放租约、写他 Run 待验区、提交他 Run 远程构建 → 拒绝；worker 写基线缓存/Profile 正式区 → 无此命令）；**板子池**（旧持有者未静默前不再分配、旧 generation 命令与回报拒绝、坏镜像多板失败归因镜像而板不下线、单 Run 持板上限、序列租约不被抢占、回收中重启先对账、无法静默转 quarantine）；**基线缓存**（构建输入闭包各分量逐一变化的命中/失效矩阵、A/B 闭包不一致拒绝比较、single-flight 并发、多 Run 引用时 GC 不删、下载中 kill + GC、损坏重建、Quickbuild 读回构建输入不同或读不回 → comparison=unverifiable 且基线不进跨 Run 缓存；同一 Run 内 Quickbuild 各次提交携带同一锁定包版本与 Profile 快照）；**BenchPolicy golden 数据集**（不显著、跨 SPEC 线、样本不足、方向相反、零基线、多指标 Holm 各一例；quick/single 报告进入 gate → fail-closed；Run 中修改 SPEC → D12 失配；同一测量记录配相反的 LLM 建议判定不变；篡改 gateable 字段 → 复算不一致 sys.invalid_result）；生成型 Benchmark 套件未通过有效性检查或未确认时拒绝使用、MCP 调用确认操作 → 不存在该工具；**Profile**（同源不同构建选项 / 同名不同套件版本 / 采样能力不同 / 字段缺失 / 格式不支持 → 拒用；完全匹配 → 接受；待验区不被他 Run 消费；GCC 构建包被 AutoFDO 拒绝）；**优化环**（保留 optimizer 删 UT → 拒绝加载；优化回流绕过镜像/UT/Benchmark 各一反例 → 拒绝；对 snapshot 改善但对父版本退化 → 撤销；inconclusive → 撤销；撤销后 tree_digest 等价于父版本且全部报告重新新鲜；优化致 UT 失败 → 确定性撤销而非 AI 修复；max_opt_rounds 自限后环预算不触顶）；**ClineSR CLI 提示注入**（EvidencePacket 内嵌"执行命令 / 写文件 / 连接 socket"指令 → 无文件变更、无数据面命令、无外连；FD 不继承；端点改向 → D12 失配；LogAnalyzer 调用经 Fake provider 记账）；**MCP**（跨传输同 request_id → 同结果；非法 Origin 拒绝；他 principal 调用 cancel → 拒绝；sys.scheduler 只能创建 input: none 流水线）；**Gateway**（错账号会话注入被拒、会话恢复后对账、取消传导、日志脱敏）；**v2.2 追加**：**目标范围**（patch 涉及模块不可从范围剔除；input: none 无 focus_modules → 拒绝创建；未登记模块名拒绝；范围推导失败 → submit_patch 拒绝；UT/Benchmark 只选范围内用例集与套件 + always_run；范围只增不减、撤销后也不缩减；注册表快照不变，范围增长不构成 D12 失配；ModuleRegistry 变更 → D12 失配）；**多版本对比报告**（基线 / 开发者原始改动 / 每轮 AI 版本逐列齐全；原始改动构建失败如实呈现；被取代报告保留可读；同一测量记录重复生成结果逐字节一致；ReviewReport 不得改写其中数字；审批 CLI 首屏快照）；**Quickbuild 锁定 base**（"最新"在 pin 事务内解析为当时最新可用的 Profile 快照；同一 Run 内被测、基线与各轮提交携带同一 Profile 快照与显式覆盖版本，被测源码按当前 series，构建根环境按读回的实际输入证明比较；开发者旧基线 patch 可应用时注明、不可应用时拒绝并给冲突位置；FakeQuickbuild 读回实际使用版本与锁定不符 → 构建结果判为无效）；**Profile 新鲜度策略 v2**（缺省关闭；开启时覆盖率阈值与前 K 热点函数规则的 golden 用例；部分匹配复用在 OptimizationReport 中记明）；**v2.3 追加**：**示例**（示例一并行原文通过规则①③；变体 opt_patch_ready 绕开 ut 或把 bench_gate 移出 join → 拒绝；示例三、四原文通过）；**净变更**（input: none 下 advances(no-op) → needs-patch、asserts_nonempty → advances(撤销回 base) → needs-patch 均拒绝；campaign 候选→撤销→重验→no_gain_found 合法；submit_patch 无净变更拒绝；分派前无净变更 → fail_safe 且 incomplete 写明）；**超时放行点**（`on: sys.timeout` 指向非 fail_safe → 拒绝；超时后重试成功 → 只进 retried、非发布路径结论为 succeeded_with_gaps；发布路径 retried 记录未逐条确认 → 审批拒绝，确认后通过且写入决定，审批人 reject → 不发布；存在 timeout 条目 → 审批拒绝；environment_gap 未逐条确认 → 审批拒绝、确认后通过且写入决定；审批后核销前新增 timeout → 核销按授权失效处理；发布后超时 × released / release_failed 按冻结映射、结果首屏标明"已发布但存在超时"；terminal 有 gap → succeeded_with_gaps）；**外部等待补充**（无会话首次提交、发送前会话过期、ACK 丢失且会话过期、恢复 probe deferred 四例全程无等待中的 worker、登录恢复不重复提交；有其他在途效应时 task_suspend 被拒；external_timeout_min 到期 → sys.timeout；挂起 task 的 series 被 supersede → 远端取消、sys.superseded；paused 期预算到期经 queued 执行 fail_safe）；**远程配额**（配额 1、取消失败 → 下一提交不发出；Run 关闭后远端完成恰一次归还；清理事务前后 kill；重复或旧 version 回报不多归还）；**Quickbuild**（读回包版本与锁定不符 → base_mismatch；两侧读回 base 快照或 build.conf 摘要不同 → comparison=unverifiable、gate 缺字段、优化不得接受；需 fuzz 才能应用的 patch 被拒；BUILD_NOTES 标记写入与按构建号跟踪）；**BenchPolicy v2.3**（耗时 100→120 与吞吐 100→80 均为正回归；高噪声大回归点估计 12%、区间上界 30% → gate fail；absolute SPEC 超限但相对改善 → SPEC-OUT；comparison none 只做 absolute 判定；所选集合为空 → validation_complete=false；零基线、BCa 退化 → inconclusive、字段缺失）；**优化计划**（优化→RPM 失败→只允许确定性撤销、AI 修复段被拒；优化→UT 失败→撤销段仅逆转候选段（v2.7 替换 v2.3 的"优化→修复→…"两例，其前置条件在 v2.6 规则②下不可构造）；neutral→撤销→重验只撤销一次；未决计划时 no_further_gain → sys.invalid_result；max_opt_rounds=1 时 loss 候选仍先撤销再停；优化致链接失败 → 确定性撤销且修复环不触顶；campaign 两候选均 UT 失败 → 两次撤销均可执行）；**目标范围**（创建时不伪造范围、首次 submit_patch 定范围；修复改到范围外已登记模块 → 范围增长、下一轮测试包含其用例集与套件且不触发 D12 失配；改到未登记模块 → candidate 拒绝；显式套件少于最低集合 → 不具 gate_eligible；审批快照含"受影响未验证模块"）；**验证资产**（UT 修复删失败用例 / 编译修复加 -Wno-error → verification_asset_change、无确认审批被拒；正常修复不命中）；**对比报告**（篡改 → manifest digest 失配、核销拒绝；terminal 与 fail_safe 路径均生成）；**构建边界**（`%post` 写入持久化后门 → 下一次构建与 sys.baseline_build 的边界中不存在；基底 digest 不符 → 产物拒收）；**CLI 进程**（worker 被 SIGKILL / 硬超时 / 编排崩溃 → CLI 及其子进程经 cgroup 被终止）；**E-03 细则**（worker 直接写镜像存储 → 权限拒绝；remote_build_submit 引用他 task 的效应 → 拒绝；无板侧 fencing 时主动释放后板子在 task 结束前不被再分配）；**基线归属**（发起 Run 取消、另一等待 Run 仍拿到基线；全部取消 → 构建取消；失败广播 baseline_unavailable）；**换板重试**（板 A 刷机失败 → 重试分到板 B；B 也失败 → 镜像判坏、两板不计数）。**v2.4 追加**：**Quickbuild 证据等级**（`unverified` 能力（Remove、批量覆盖、构建暂存输入、产镜像工程）启用 → 加载或提交拒绝；非空 series 而构建暂存输入未验证 → `backend_source_input_unsupported`；FakeQuickbuild 分别只回显 base commit、实际应用当前 series、实际应用错误 series → 不可冒充成功 / 通过 / base_mismatch；base_mismatch → image_failed_exhausted、不进入修复环）；**实际构建输入**（发布摘要相等但实际配置不同、发布摘要相等但实际未知、实际闭包全等 → 不可比 / 不可比 / 可比；前两例无比较字段、不可接受优化、不进入跨 Run 缓存，人工确认 gap 也不能生成这些字段）；**有界 probe**（Recent Builds 10 条窗口滚过后按构建号扫描命中；扫描范围外或按构建号读取不可用 → indeterminate；父 trigger 已取消而子构建仍在运行 → 配额不归还）；**优化计划出口**（优化前后 A/B 不可比 → inconclusive → 撤销；撤销段提交即 reverted，Optimization 随后返回无进一步收益合法；撤销后重验证 UT 失败 → 按普通修复环处理；撤销后常规 A/B 不可比 → BenchReport 谓词为假、阈值 gate fail；示例一 image_fix_loop 用满后提交候选 → E-PLAN-NO-CAPACITY → 无进一步收益、Run 继续到审批；剩余 1 次时允许创建计划，候选镜像失败后撤销不触顶；rpm / ut 修复环各一例）；**retried 确认范围**（被取代 series 上的 retried 只汇总、不要求勾选；证据链上的 retried 未确认 → 审批被拒；确认后条目内容 digest 变化 → 核销以 gaps_changed 拒绝并按 release_failed 映射关闭）；**登录等待超时**（节点配置 `retry: [sys.timeout]` 时仍直接 fail_safe，超时类别 gateway_session）；**净变更数据流**（validator property：随机含环图上数据流结论与"每条路径上最后一条 advances 之后必有 asserts_nonempty"的枚举判定一致）；**撤销后的验证资产**（候选改 `%check` 后被撤销 → 审批时无该确认项、对比报告仍可见；AI 修复段重新引入 → 要求确认）；**报告时序**（review_final 完成时正式对比报告尚不存在仍可完成；ci_plan 完成事务前后崩溃不留下可审批的半份证据；ReviewReport digest 不变）；**无环节点外部等待**（缺省超时 = run_budget 上限）。**v2.5 追加**：**后端能力加载期检查**（示例一改配 `backend: quickbuild` 且构建暂存输入 unverified → 拒绝加载；示例二首轮镜像节点可面对空 series 但位于 opt 回流之后 → 拒绝加载；可比性 unverified 且 gate 消费 A/B 依赖字段 → 拒绝加载（absolute-only 按 v2.6 用例组）；运行时防御返回 image_failed_exhausted(backend_source_input_unsupported) 且不进修复环）；**Quickbuild 证据**（FakeQuickbuild 同时提供较旧 reference 与较新 Profile → 固定的是策略所指快照、首屏不宣称等于服务缺省；快照刚发布而包 commit 很旧时不计算落后量；构建号跨配置交错时扫描按配置过滤，缺号 / 权限缺失 → indeterminate；一个不产镜像的样本不使整个配置登记为 unsupported）；**证据链边界**（ci_plan 超时重试后成功 → 要求逐条确认；基线构建超时重试 → 出现在本 Run 的 retried 中并要求确认；核销复核失败时 broker 未发送 outcome、Run 以 release_failed(gaps_changed) 关闭）；**purpose 推导**（Optimization 自报 purpose = repair → 仍按 candidate 处理并创建计划；存在未决计划时 base_mismatch → 唯一出口 fail_safe、不产生撤销段）；**准入拒绝后的 status**（campaign 下有净变更 / 无净变更各一例）。**v2.6 追加**：**purpose 互斥判定**（Optimization 在 neutral / loss / inconclusive 后亲自撤销 → revert、计划迁 reverted、计划数不增加；max_opt_rounds 已到顶或优化环只剩撤销容量时撤销仍成功；Compiler / UT 失败代撤销同规则；未决计划期间 Compiler 提交非撤销段、Optimization 提交新候选 → E-CANDIDATE-NOT-REVERT；树碰巧等于历史已结束计划父版本的段不认作撤销；自报 repair 的优化提交仍创建计划；初始段为 initial）；**terminal 兜底**（绕过加载器直接构造"未决计划 + terminal success_on"状态 → closed(fail_safe, pending_plan_at_terminal)；合法图的可达性由 v2.7 用例组单独检验，v2.8 改写）；**绝对指标 gate**（构建暂存输入与镜像能力已验证而可比性未验证时，只用 absolute SPEC 的非发布 gate 可加载；改为 relative SPEC / regression_pct、加入 Optimization 或必需 Bench 发布 → 拒绝；指标依赖无法解析 → 拒绝）；**推广状态显示**（latest 等于 reference、latest 较新、reference 读回不可得、显式指定已有推广证据的快照四例；不凭时间先后宣称已 / 未推广；Profile 与构建根编号不同时两编号均可见）。**v2.7 追加**：**计划迁移的事务位置**（candidate 受理前后、task_complete 前后逐点 kill：撤销受理后 worker 崩溃仍为原候选 series + rejected_reverting，完成提交后才为撤销 series + reverted；新候选受理后崩溃不产生计划；父版本 CAS 失败、并行候选、旧 attempt 候选作废；同 id 完成重放计划数与轮数各只增加一次）；**拒绝后改交撤销**（FakeCompiler 先交 AI 修复段被拒、再交撤销段 → revert 且只消耗一次环计数；不改交直接结束 → sys.invalid_result）；**违规返回归因**（示例二变体：计划 rejected_reverting 时返回 no_gain_found → sys.invalid_result、配 retry 时重试后正常撤销；有净变更时返回 no_gain_found → sys.invalid_result；`image_failed_exhausted → terminal` 的优化流水线被规则③拒绝；直接构造"未决计划 + terminal success_on"仍为 pending_plan_at_terminal）；**auto 套件**（Quickbuild 能力 source_input / build_image verified、comparison unverified × `suites: auto` + absolute 指标 gate → 拒绝加载；改为显式锁定的 absolute 套件 → 通过）；**manifest schema**（构建根快照编号只出现一次）。**v2.8 追加**：**完成复核不一致**（并行产 patch 分支：失败节点预校验为 revert、完成前注入收益判定写回为 accepted → sys.error(candidate_recheck_failed)，计划仍为 accepted、series 不变；Optimization 预校验通过后不推进 series 的环耗尽剩余次数 → sys.error，重试得 E-PLAN-NO-CAPACITY 并返回无进一步收益；两例完成事务前后 kill 结局唯一）；**无 PHP 门禁**（`.phar` 文件、无后缀而 shebang 为 php 的脚本、`composer.lock`、deploy 镜像基础层含 php-cli、Python 插件 wheel 内含 `.php`、受限 adapter 声明 python 而入口为 php、解析规则引用外部脚本 → 均失败或拒绝注册；buildroot 装入含 php 的业务包 → 不报；纯 Python 闭包与纯静态前端 → 通过；制品 digest 变化后未重新扫描 → 拒绝加载；负向夹具使用合成清单，需要真实文件的负向例（`.phar`、php shebang 脚本、`composer.lock`、含 `.php` 的 wheel）在测试运行时生成到临时目录、不提交进仓库，不把真实 PHP 运行时引入测试依赖；**v2.10 追加**：仓库根目录自扫描（含本规范原文、扫描器规则表与合成清单）→ 通过；`docs/` 中放有可执行位的 php shebang 文件 → 失败；含 `<?php` 的文件改名为 `.txt` 并被注册为入口或模板 → 拒绝；主机预装与本产品无关的 php-cli → 预检列出、门禁通过；deploy 安装的工具传递依赖 php → 失败；工作区含业务 `.php` 源文件 → 不报；只有 E0 例外需求记录、无经批准的例外条目 → 仍拒绝；例外条目 digest 匹配 → 通过、不匹配或过期 → 失败；策略版本 +1 → 已注册插件重扫；deploy 安装集 digest 变化 → Run 创建被拒）；**改交撤销的例外与登记**（FakeImage 先交 AI 修复段被拒、随后读回 base_mismatch → image_failed_exhausted(base_mismatch) → fail_safe 而非 sys.invalid_result；被拒后新 request_id 改交撤销 → 受理，复用旧 request_id → 返回首次拒绝）。conformance attestation：结果绑定 agent 制品 digest + contract/套件版本，digest 变更即失效，加载时校验。

---

## 12. 环境前提与 E0 预检
同 v0.1 表（gbs 工具链 / image URL / gerrit 探测 / CodeGraph / LLM Wiki / FakeLLM），**v2.9 追加**：对 deploy 将安装或调用的第三方工具（ClineSR CLI、gbs / mic、LLVM / BOLT 工具链、LogAnalyzer、sdb 等）的安装件与本产品主机安装集（按 §11.2 v2.10 口径）执行无 PHP 扫描，结果写入预检报告（D23）；命中项只作为待负责人决定的报告，不构成许可；**v2.0 追加**：mic 与镜像 ks 配置、Quickbuild 提交方式与会话登录流程、各板型刷机工具与连接方式、LogAnalyzer 调用形态——均为 `[待补充]` 环境事实，由负责人提供后进入 E0 预检；**v2.1 追加三项可行性预检（结果决定上线形态，不提供放宽降级）**：① 宿主虚拟化能力（KVM）与构建 VM 镜像可用性——不满足则改用独立构建主机（D22），不得宿主 root 直跑；② ClineSR CLI 能否在 §7.1 的 OS 层约束下（专用用户、close_fds、只读提示目录、出口仅 LLM 端点）以补全模式工作——不能则第一阶段 LLM 能力不上线；③ Quickbuild：只读调查已完成——已证实 Profile 快照锁定与单包 commit 覆盖；构建根 base、实际 build.conf 与脚本版本本次未证实可锁定、按读回处理；其余能力按配置登记证据等级（§7.6.1），`unverified` 者不得启用。P6 前以经负责人确认的真实提交逐项验证（批量覆盖、构建暂存输入、按构建号读取标记、实际 build.conf 与脚本版本取得方式、取消联动子构建），并另行只读调查一个产镜像工程的锁定与读回；另：宿主是否支持按 UID 的出口规则（netfilter owner 匹配）与 cgroup v2 委派（launcher 终止跨 UID 进程，§7.1）；追加：Approval 服务与 broker 的本机进程部分无外部环境依赖、不进 E0 预检；**官方发布 adapter 的真实端点联调（gerrit/github 端点、凭据、目标仓权限）为独立上线 gate 材料**——开发与 P4 验收基于本地 API 模拟器/fixture，真实端点验证由负责人在受控环境执行（用例 07 提供），未通过前不得对生产目标发布。

---

## 13. 分期计划概览（细化见 09）

| Phase | 交付 | 完成 gate |
|-------|------|----------|
| P0 | 本 HLD 三方评审 GO（E-02/E-03 随之生效）并与总部对齐；01 按 v2.x 范围扩展并经三方评审 draft freeze；08/09 就绪 | 总部方案确认 + 三方 unanimous GO |
| P1 | EnginePort + engine/ + DSL v1 校验器/编译器（含 release_requires、input、优化重验证三条规则与按 mode 注册集）+ Run 状态机（含外部等待项与 wake outbox）+ Ledger 核心 + worker 调度（含分派前资源授予与锁序） | mock agents：四份示例流水线原文与 §2.4 删除组合加载；逐边界故障注入恢复通过；外部等待 model-based 无死锁 |
| P2 | SDK（worker/side_effect）+ contracts + MCP 服务（含 HTTP 端点；get_result 含 incomplete / retried 清单）与配套 Skill + control-plane RPC + Approval 服务 + Review CLI + Release broker + **Build Gateway 骨架** | conformance 骨架 + 授权并发/双消费 + RPC 权限隔离测试通过 |
| P3 | 公共模块（LLM 层+数据边界+ClineSR CLI OS 层约束、Knowledge 三实现、context、evidence）+ **GitGerritSource** + **LocalGbsBackend（RPM + 全量 + mic，经构建隔离边界）+ 板子池（Fake + 首个真实板型适配器）+ 镜像存储/基线缓存/Profile 库** + 官方 gerrit/github adapter | 真实 gbs 最小构建与镜像构建 + **特权构建隔离 E2E** + 数据边界 fail-closed + adapter 模拟联调通过 |
| P4 | 端到端：全量与子集流水线（mock 业务 Agent + 真实构建与镜像 + CLI 审批 + Fake/模拟器发布）+ ModuleRegistry 与目标范围 + 多版本对比报告（构建 / UT 列；Benchmark 列在 P7 补齐）+ 验证资产触及检查 + deploy/ 资产（含 launcher cgroup 契约） | §11.3 全部测试类别 + 真实 UID/权限 E2E = 框架完成 |
| P5 | **Compiler Agent**（LogAnalyzer 引擎，rpm + image(local)）+ 六类 fixture + 兼容矩阵 | contract v1.0（G6）——**核心 + Compiler/UT/Review/CI 面定稿；Benchmark/Optimization/Profile/套件/BenchPolicy schema 标注 provisional**（D10：未被真实消费者不定稿） |
| P6 | **QuickbuildBackend**（经 Build Gateway，Tizen） | 内网真实 Quickbuild 联调用例通过 + **Gateway 会话注入与错账号拒绝** + 会话失效期 probe deferred + **§7.6.1 证据等级表逐项验收**（未通过项保持 `unverified`、不得启用；构建暂存输入未通过 → 该后端只承担空 series 构建与绝对测量，校验器按 §4.2.6 后端能力检查拒绝其他用法） |
| P7 | **Benchmark Agent**（套件注册表、TPMS 适配器、BenchPolicy 统计库、脚本生成与有效性检查、profile 采集）+ **Optimization Agent**（AutoFDO/BOLT 先行，复用增强版 llvm-profgen；CompilerGym 类与 MLGO 随后） | **contract v1.1**（provisional 面经真实消费后定稿）；真实板子上 A/B 测量可复现；BenchPolicy golden 通过；多版本对比报告 Benchmark 列；Profile 新鲜度策略 v2 的非劣评估（满足则开启）；优化环回流重验证与撤销闭合；至少一个模块实测收益 |
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
| R15 | Quickbuild 不可用或会话频繁失效；P6 未能验证构建暂存输入与实际构建输入证据 | Gateway 会话状态与提交失败率告警；P6 证据等级表 | 节点外部等待 + 运维登录；能力未验证时校验器强制改配本地后端——此时 Quickbuild 在流水线中只承担空 series 的构建与绝对测量（P6 gate 记录此结论，负责人裁决②的收益以 P6 结果为前提） | 框架+负责人 |
| R16 | 生成型 Benchmark 脚本"测错了东西" | 有效性检查（干跑两次、指标来源核对、离散度） | 未通过检查或未经人工确认不得入库使用 | 框架+开发者 |
| R17 | 优化引入功能问题（BOLT/AutoFDO 误编译） | UT 重跑失败、Benchmark 异常 | 优化重验证路径由校验器强制（§4.2.6 规则③）；UT 失败于优化段时确定性撤销；release_requires 强制新鲜且通过的 UT 报告 | 框架 |
| R18 | Profile 与代码版本漂移导致优化失效或劣化 | Profile 兼容字段完全匹配检查 | 不匹配即拒用、请求重新采集；收益须"优化前 vs 优化后"A/B 实证，否则撤销 | 框架 |
| R19 | 板子争用、刷机失败、板子状态波动 | 租约排队时长、刷机失败计数、静止判定失败率 | 独占租约 + 失败下线 + 静止判定 + 交叉测量 | 框架+负责人 |
| R20 | 镜像构建耗时与磁盘占用 | 镜像队列时长、磁盘水位 | 基线缓存复用、廉价前置检查先行、镜像保留策略、镜像构建并发 1 | 框架 |
| R21 | VD 接入时源码模型差异超出适配层预期 | P8 前置评估 | SourceProvider/构建后端抽象首期即按 shelve CL 形态验证可容纳；tree_digest 与 fencing 的 VCS 中立化在 P8 以勘误通道修订（D20） | 框架 |
| R22 | AI 分析误报（异常原因、优化候选判断错误）；AI patch 改动验证资产 | 有事实标签样本上的准确率与误报率；验证资产触及检查 | 判定与 AI 分离（判定字段由框架统计库确定性计算，§7A.0 原则 5）；AI 方案以每轮测试结果检验、审批前多版本对比报告呈现（原则 6）；分析类输出为 AI 初稿 | 框架+负责人 |
| R23 | 构建隔离边界不可用或开销过大（无 KVM、VM 启停慢、loop 设备限制） | E0 预检、镜像构建时长 | 改用独立构建主机（同一契约）；不允许宿主 root 直跑（D22） | 框架+负责人 |
| R24 | 每臂 ≥10 个有效样本、回归按区间上界判定，使板子占用与镜像构建排队显著增加，噪声大的指标更难通过 gate | 租约排队时长、Benchmark 时长 | 基线缓存复用、单项/快速模式用于开发期、发布验证用范围更小的套件版本；必要时扩充板子池 | 框架+负责人 |
| R25 | 只按目标范围验证，范围外的回归漏检 | always_run 冒烟集失败率、发布后问题回溯 | 改动涉及的模块不可从范围中剔除；always_run 冒烟集兜底；范围推导失败拒绝提交（§7A.7） | 框架+业务 |

---

## 15. 附录
- A1 术语表：§3。
- A2 `[待补充]`：gbs.conf、gerrit 探测方式、ClineSR CLI 调用参数（非交互模式、关闭工具、输出格式）、CodeGraph/LLM Wiki 仓库地址；v2.0 追加：mic 镜像 ks 配置、Quickbuild 提交方式与登录流程（含显式指定 base 与读回实际使用版本的方式）、各板型刷机工具与连接方式（含板侧静默/复位能力）、LogAnalyzer 调用形态、TPMS 适配接口（含其现行统计方法参数，供 BenchPolicy 对齐）。
- A3 引用：01/07/08/09（待产出）；docs/review/ 下 v0.1–v0.11 十一轮处置表；docs/review/HLD_v2.0_review_disposition.md（v2.0 首轮）。
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

- A16 v1.0-draft-frozen → v2.0 变更摘要（范围扩展；对冻结核心的两处扩展于 v2.1 改登记为勘误 E-02/E-03）：七角色协作（新增 Optimization Agent）；Compiler Agent 两模式两节点（rpm / image）与可插拔构建后端（LocalGbs：增量 RPM、全量 + mic；Quickbuild 经 Build Gateway；VD Cosmos 后接）；LogAnalyzer 作为 Compiler 分析引擎与第三个知识源；可配置 Benchmark（三种套件来源、生成脚本有效性检查 + 人工确认、A/B 对基线、静止判定、profile 采集）；Optimization Agent（AutoFDO / BOLT / CompilerGym 类 / MLGO 方法插件，轻量与专项两种触发，强制回流重验证）；即插即用显式保证（§2.4）与交付边界（§2.5）；新增决策 D14–D21，D11 补充长等待不占执行槽（v2.1 改为勘误 E-02）；新 DSL 规则 release_requires 与 input；新示例流水线（全流程、优化专项）；板子池、镜像存储、基线镜像缓存、Profile 库、SourceProvider；Build Gateway（§8.6）与对应 IPC 通道；部署拓扑与网络边界；§11.3 追加测试类别；分期重排为 P0–P8；风险 R15–R21。
  - A16.1 v2.0 补充（总部方案沟通输入，原 A17 并入）：Coding Agent 接入改为"Skill 调用框架 MCP 服务"（HTTP 端点保留给脚本与测试，同一契约）；LLM 接入第一阶段经 ClineSR CLI（不依赖 LLM API）；新增 §7A.0 各 Agent 的 AI 能力与使用原则（判定与 AI 分离、试点先行、数据边界、可追溯）；Benchmark 增加全量/单项/快速三种测量模式、一次完整记录（指标、区间、资源、日志）无需重测、业务部门 SPEC 的 SPEC-IN/OUT 判定、统计判定标准、自动测量报告（含 AI 初稿）、跨部门用例共享；Optimization 增加优化候选的推荐与排序；目标 G11；风险 R22；全文"单测"统一为"UT 测试"，UT Agent 定位为板上稳定性测试；交付分工调整为六类 Agent 均由本团队开发，业务部门提供 UT 测试用例、外接性能测试用例与 SPEC、Review 外接知识库内容。
- A18 v2.0 → v2.1 变更摘要（v2.0 首轮三方评审：Kimi GO / Claude Code NO-GO（2 BLOCKER）/ Codex NO-GO，全部确属问题均已修入，逐条处置见 HLD_v2.0_review_disposition.md）：**特权构建隔离 D22**（mic/GBS sudo 段在独立内核边界内执行，N7/§8.1/§10/§12 同步）；**外部等待改为勘误 E-02**（§4.3.4：任何 worker 不跨越等待存活、分派前资源授予、远程构建提交后 `sys.await_external` 挂起与 wake outbox 续接同一 dispatch、锁序、全集计时条件、paused 期预算到期、取消传导；D11/§4.3.1/§4.4/§4.5/§4.2.4 同步，头部"原样保留"表述更正）；**worker 数据面扩充改为勘误 E-03**（§8.5 六条新命令，跨 Run 共享存储对业务 worker 只读）；**示例一改为单链**（静态审查移至阈值判定后，release_requires 生产节点按既有普通支配定义支配审批节点，不扩展 join 语义）；**修复回流定案**（D15：产修复 patch 的 task 提交唯一 candidate 即结束、由声明环重派，新增 rpm_fix_loop）；**镜像节点 rpm_precheck**（required / independent，专项首轮合法化）；**注册集按 mode 声明** + series_effect（advances / asserts_nonempty / none，运行时强制）；**§4.2.6 规则重写**（① release_requires：通用 release-approval 节点、结论为通过、不自动降级、空清单须显式确认、release_evidence 入 ReleaseManifest；② input: none：路径级 series_effect 检查、初始空 series 同事务签发、空计划取消；③ 新增优化重验证路径强制）；**示例二**（rpm_precheck: independent、campaign 三值 status、report_no_gain terminal 节点）；**效应身份**（远程构建效应标记 = idem_key 指纹 + version、indeterminate 不当未发生；镜像 probe 按 idem_key 查索引并复验，镜像存储纳入 Blob 提交协议）；**Benchmark**（BenchPolicy 缺省值定案、SPEC 三值、逐指标四值、gate_eligible 只认 full 且覆盖完整、判定字段框架统计库确定性计算、MeasurementRecord、manifest 固化、确认走本机特权通道、解析规则声明式）；**Optimization**（优化前 vs 优化后 A/B、opt_verdict、撤销 patch、max_opt_rounds 自限、UT 失败于优化段时确定性撤销、首期范围 clang 包与 --emit-relocs）；**板子池**（generation fencing、reclaiming→复位→available、quarantine、失败归因、单 Run 持板上限、序列租约、静止判定不调用 AI）；**基线缓存**（构建输入闭包键、A/B 闭包一致、single-flight、TTL/手动/撤销失效、引用计数 GC、仅 sys.baseline_build 可写、基线测量不复用于判定、unpinned_remote 约束）；**Profile**（兼容字段完全匹配、待验区/正式区、internal_code）；**Build Gateway**（运维会话 socket 注入与账号校验、probe deferred、取消传导、幂等、脱敏）；**ClineSR CLI OS 层强制**与配置固化、上界记账、LogAnalyzer 经框架 LLM client；**MCP**（每调用方 token、request_id 为工具参数、幂等域 (principal, 操作名) 跨传输共享、Origin 校验、开发者工具与 sys.scheduler）；**AI 原则 5/6**（结构性保证、pilot/adopted 登记）；D12 扩展字段；D13 新可执行内容来源；D14 release_requires 不降级；D20 VCS 中立化范围说明；§8.2 CAS 纳入 release_requires；§2.4 删除表补 release_requires 调整；§13 P3/P5/P6/P7 gate 调整（contract v1.0 核心 + provisional，v1.1 于 P7）；风险 R23/R24，R21/R22 排序；§11.3 用例补齐；附录 B 第 7 组补全；G10/G11 排序。
- A19 v2.1 → v2.2 变更摘要（项目负责人六项裁决）：① **恢复 UT 与静态审查并行**（示例一恢复 join），`release_requires` 改用仅本规则适用的"汇合必经"定义（E-01/V-13b 与阈值 gate 来源检查仍为普通支配），新增 §4.3.5 **超时与未完成必须显式呈现**（join 超时只能 fail_safe、gate_expired 不得与 approved 同目标、超时记录与 FeedbackReport 首节、`get_result` 的 incomplete / retried 清单、存在超时项不得以 succeeded 关闭）；② **Quickbuild 基线锁定**（"最新"在 snapshot pin 时解析为具体 CL / commit 并记录，本 Run 全部提交携带同一 base，基线跨 Run 复用；审批人只审改动；个别输入无法指定时 `unpinned_inputs` 兜底，取代 v2.1 的 unpinned_remote 方案）；③ **Profile 复用放宽预案**（新鲜度策略 v2：函数级校验和 + 编译器陈旧 profile 匹配 + 加权覆盖率与热点函数条件，缺省关闭，P7 验证后开启）；④ **目标范围与模块登记表**（新 §7A.7：改动涉及模块不可缩小 ∪ 开发者关注模块，input: none 必填目标模块；UT / Benchmark / Optimization 只围绕范围工作，always_run 冒烟集兜底；R25）；⑤ **以测试结果检验 AI**（取代按能力登记试点：每轮报告全部保留、审批前框架生成多版本对比报告——基线 / 开发者原始改动 / 每轮 AI 版本，分析类输出按采纳记录统计准确率）；⑥ E0 预检第 ③ 项改为核对 Quickbuild 显式指定 base 与读回实际版本的方式。
- A20 v2.2 → v2.3 变更摘要（第二轮三方评审：Kimi GO / Claude Code NO-GO（8 MAJOR）/ Codex NO-GO（12 MAJOR）；负责人六项裁决经三家独立评估均为"成立"或"有条件成立"，本版保留全部裁决、补齐使其成立的机制；Quickbuild 只读调查结论并入；逐条处置见 HLD_v2.2_review_disposition.md）：规则③改用"汇合必经"（与规则①共用，E-01/V-15 仍普通支配），示例一并行原文可通过；规则②改为 input: none 的净变更数据流分析（advances 重置证明）+ 全部流水线的分派前净变更复核 + submit_patch 拒绝无净变更，Compiler RPM 注册为 optional；§4.3.5 补放行点（`on: sys.timeout` 只能指向 fail_safe、retried 与 incomplete 分类、审批与核销复核、acknowledged_gaps、publishing 后按冻结映射并首屏标明、succeeded_with_gaps；负责人定案：超时后重试成功可以发布，但每条 retried 记录须审批人逐条确认，不认可即不发布）；E-02 补会话等待（提交前 / 提交不确定 / 对账阶段）、`task_suspend` guard、`external_timeout_min`、`sys.superseded`、远程配额 `cancel_pending` 恰一次归还、paused 期预算到期路径与偏离清单；Quickbuild 按调查结论改写（包 commit 与 Profile 快照锁定、构建根 base 与 build.conf 读回、读回校验、读回不可比 → comparison=unverifiable、BUILD_NOTES 标记、证据及时归档、单一解析、干净应用定义）；BenchPolicy（劣化方向统一为正、regression_pct 改为区间上界非劣形式、absolute / relative SPEC、空集合非完整、BCa 退化 inconclusive）；OptimizationPlan 生命周期（修复段归属计划、按计划状态触发判定与撤销、Compiler/镜像/UT 失败于未决计划时确定性撤销、按计划数计轮、修复环容量 ≥ 1 + max_opt_rounds，示例预算同步）；Profile v2 伪探针前提与非劣开启条件；目标范围（首次 submit_patch 时确定、只增不减、未登记模块拒绝、显式套件不得少于最低集合、注册表快照入 D12）；验证资产保护（protected_paths + 确定性 diff 规则 → verification_asset_change 需确认）、采纳率与准确率区分、原则 2 的策略版本开关；对比报告生成时点与 digest 入授权绑定；D22 不可变基底与一次性可写层（两种形态共同契约）；ClineSR CLI 经 launcher 与 cgroup v2 终止；E-03 细则（镜像由 launcher 导入、远程提交只引用已 claimed 效应、租约主动释放语义）；sys.baseline_build 归属框架内部 Run；换板重试；报告"通过"谓词统一；示例三、四原文；附录 B 第 7 组矛盾消除与补项；分期补项；R24 加重、R 编号排序。

- A21 v2.3 → v2.4 变更摘要（第三轮三方评审：Kimi GO / Claude Code NO-GO（3 MAJOR）/ Codex NO-GO（3 MAJOR）；负责人七项裁决三家均判成立或有条件成立，全部保留，条件以机制满足；逐条处置见 HLD_v2.3_review_disposition.md）：§7.6.1 Quickbuild 按证据等级重写——"最新"解析为当时最新可用的 Profile 快照、显式覆盖个别包版本（批量覆盖、Remove、构建暂存输入、按构建号读取、取消联动子构建、产镜像工程均为 unverified，不得启用），被测源码身份经 ExpectedSourceManifest 与构建暂存输入证明（不支持则拒绝非空 series、改用本地后端），实际 build.conf 与发布摘要分列、`unknown` 即不可比、不可比不能经人工确认补出比较结论、未证明输入不进入基线缓存，probe 有界，base_mismatch → image_failed_exhausted 且不进入修复环；§5.2 远程构建效应改为"可 probe（有界）"；§7A.4 优化前后不可比 → inconclusive → 撤销，撤销段提交即 reverted、其后重验证按常规义务处理；§4.2.6 规则③增创建计划的运行时准入（`E-PLAN-NO-CAPACITY`），规则② 多入边节点取交与不动点初值，规则① BenchReport 谓词改为 `comparison = verified`、汇合必经措辞统一；§4.3.5 / §8.2 / §8.3 retried 逐条确认限于当前 series 证据链（被取代轮次汇总列出），确认绑定内容 digest，核销复核不通过 → release_failed(gaps_changed)；登录等待超时固定 fail_safe（§4.3.4、§8.6 措辞统一）；`external_timeout_min` 无环节点缺省 = run_budget；验证资产触及项在审批前按净 diff 重算；Review final 不引用尚未生成的正式对比报告；§7.8 基线缓存、§11.3 旧断言（范围不可变、同一 base、超时不得 succeeded）同步修正并追加 v2.4 用例组；§12 E0 ③、§13 P6 gate 改为按证据等级表验收；附录 B 第 7 组补登对应同步项。
- A22 v2.4 → v2.5 变更摘要（第四轮三方评审：HLD 部分 Kimi / Codex / Claude Code 均 GO，余 Codex 1 MINOR、Claude Code 4 MINOR + 1 NIT，全部采纳；逐条处置见 HLD_v2.4_review_disposition.md）：§7.6.1 证据依据校正——Quickbuild 缺省为 Ref. Snapshot，"最新 Profile 快照"是本系统的选择（未经 reference 推广，首屏注明），删去"落后量等于快照发布间隔"、落后量无证据时标 unknown，已知构建号读取已证实、按构建号扫描与按配置过滤为 unverified，1917 样本未产镜像不外推为不支持；§4.2.6 增后端能力的加载期检查（构建暂存输入或可比性未验证时拒绝相应用法），运行时防御 image_failed_exhausted(backend_source_input_unsupported)，R15 与 P6 写明 Quickbuild 在能力未验证时的角色；§4.3.5 retried 证据链扩至当前 series 的全部 task（含 ci_plan、Review）与提供基线的 sys.baseline_build，核销复核失败改为 ConsumeRejected(gaps_changed) + ledger 级 release_failed 映射；§7A.4 段 purpose 由编排推导、base_mismatch 优先于确定性撤销；准入拒绝后 campaign 的 status 选择写明；§11.3 追加 v2.5 用例组。
- A23 v2.5 → v2.6 变更摘要（第五轮定向复审：Kimi GO（1 NIT）/ Claude Code GO（3 MINOR + 1 NIT）/ Codex NO-GO（1 MAJOR + 2 MINOR），全部采纳；逐条处置见 HLD_v2.5_review_disposition.md）：§7A.4 段 purpose 改为互斥的四步判定（撤销优先且只匹配当前未决计划、未决计划期间非撤销提交一律拒绝 `E-CANDIDATE-NOT-REVERT`、无未决计划时优化提交为 candidate 并做准入、其余为 repair，开发者初始段为 initial），删去"待验证计划的后续修复段归属该计划"；§4.2.6③ 运行时兜底改为 terminal 命中时以 `pending_plan_at_terminal` 关闭为 fail_safe；§4.2.6 后端能力加载期检查按实际所需能力判定（只用 absolute SPEC 的非发布 gate 不要求可比性能力），路径语义写明，LocalGbsBackend 能力声明为 verified；§7.6.1 "最新"的代价改为基于证据显示推广状态、补写 Profile 与构建根的版本差距（失败时附两者编号），失败率更高改标为设计推断；§11.3 追加 v2.6 用例组。
- A24 v2.6 → v2.7 变更摘要（第六轮定向复审：Kimi GO（1 NIT）/ Claude Code GO（2 MINOR + 3 NIT）/ Codex NO-GO（1 MAJOR + 1 NIT），全部采纳；逐条处置见 HLD_v2.6_review_disposition.md）：§7A.4 purpose 判定分为受理时预校验与 §4.2.4 完成事务内的权威复核，计划创建与迁移只在后者发生；`E-CANDIDATE-NOT-REVERT` 后 Agent 须在同一 task 内改交撤销段（SDK `make_revert`），否则 sys.invalid_result；未决计划时 Optimization 返回非 opt_patch_ready 的任何 status 均 sys.invalid_result，campaign 的 no_gain_found 运行时核对无净变更；§4.2.6③ terminal 兜底改述为纵深防御；`suites: auto` 一律按需要 A/B 处理；撤销条与 §11.3 旧用例残留清理；§7.6.1 审批呈现去除重复字段、构建根结论限定为已调查样本；§11.3 追加 v2.7 用例组。
- A25 v2.7 → v2.8 变更摘要（第七轮定向复审：HLD 部分 Kimi / Codex / Claude Code 均 GO，余 Claude Code 1 MINOR + 1 NIT、Codex 1 NIT，全部采纳；逐条处置见 HLD_v2.7_review_disposition.md）：§7A.4 完成事务复核结论与预校验不一致时与父版本 CAS 失败同一出口（sys.error(candidate_recheck_failed)，不改记 purpose）；改交撤销规则对镜像节点 base_mismatch / backend_source_input_unsupported 出口的例外，预校验拒绝的提交不登记 candidate、改交用新 request_id；§11.3 terminal 兜底用例改为直接构造状态的单元测试，追加 v2.8 用例组。另按项目负责人前提新增 D23"不得引入 PHP"：覆盖全部交付与部署内容及其依赖闭包、业务接入的插件与受限 adapter，明确外部系统与测试板上的业务用例脚本不在范围内；§11.1 技术栈、§11.2 门禁（依赖闭包与交付物扫描、注册时运行时检查）、§9 Web 视图与附录 B 部署契约同步。
- A26 v2.8 → v2.9 变更摘要（第八轮收尾核对：Kimi GO / Claude Code GO（D23 落地 2 MINOR + 1 NIT）/ Codex NO-GO（D23 落地 1 MAJOR），全部采纳；逐条处置见 HLD_v2.8_review_disposition.md）：D23 范围改为按 §2.5 与 §10 引用定义，写明本产品下发到测试板的脚本、由 deploy 安装并由本产品调用的第三方工具属于范围，业务内容（被测源码、buildroot 业务依赖、产出 RPM 与镜像、基线缓存、Profile 数据）不在范围；§11.2 门禁给出可机械执行的判定信号与扫描对象（实际安装集、全部 lockfile、镜像按 digest 展开），注册准入改为制品内容与运行环境闭包扫描并绑定 attestation；Benchmark 解析规则限声明式；§12 E0 增第三方工具与主机安装集扫描；附录 B 部署契约补注册记录字段与 broker 计划性回收须经 launcher 登记；§11.3 追加无 PHP 门禁用例。
- A27 v2.9 → v2.10 变更摘要（第九轮收尾核对：HLD 部分 Kimi / Codex / Claude Code 均 GO，余 D23 落地 MINOR / NIT 共 6 条，归并为 3 个问题，全部采纳；逐条处置见 HLD_v2.9_review_disposition.md）：§11.2 增"仅命中文本标记"的非执行数据分类（规范文档、扫描器规则、合成清单只免文本标记信号，不作整目录免扫），需要真实文件的负向夹具改为测试时生成；主机扫描口径收窄为 deploy 安装集、本产品安装前缀与本产品实际调用的工具闭包，运维机只扫登录助手闭包，无关预装包只列出不判失败；D23 写明 E0 报告与例外需求记录不是许可，只有负责人修订前提后批准、按 digest 限定且有到期日的例外条目才放行；策略版本升级触发重扫，deploy 安装集 digest 写入 execution manifest 并在 Run 创建时比对；§11.3、§12 E0、附录 B 第 7 组同步。
## 16. 附录 B：[01] 待落清单汇总（01_Contract_Spec 编写骨架）

正文 `[01]` 标注的已定案项，按 01 章节归组：
1. **DSL 与静态校验**：pipeline YAML 完整 schema（nodes/routes/loops/joins/gates/terminal success_on）；校验规则形式化（§4.2.6 全部规则，含共同到达性三条件、环边双约束、join 作用域/划分、支配性检查）；target_spec 语义。
2. **状态机与消息**：Run 状态机命令/guard 表（含 publishing、administrative finalize、post-close correction）；TaskInput/HandoffResult/各 Report/RunContext/ReleasePlan/ReleaseManifest（规范化算法）/授权记录/Run 终局摘要与 correction 记录 schema；join_inputs 形态；MCP 工具与 HTTP 端点的请求/响应消息与错误语义。
3. **activation 与 series**：activation 传播定义（根/父子关系/替代 cohort 继承）；series lineage 与 tree_digest 算法；陈旧性判定细则。
4. **效应幂等**：effect 记录六态迁移/查找矩阵与版本化；effect_call_id 唯一性细则与 sys.invalid_result 归类；effect_class 注册与能力声明（probe/replay_safe）契约；恢复协议逐支细则。
5. **安全接口**：control-plane 命令集（数据面枚举、审批/核销、裁决、correction）；受限扩展 adapter 的操作描述与凭据原语契约；数据密级标注与传播规则。
6. **conformance**：§11.3 全部测试类别的用例级定义与判定标准（07 引用）。
7. **v2.x 扩展项（01 需同步扩展；上游切换至本 HLD 并更新 A2 追溯矩阵）**：
   - **注册与 DSL**：注册信息按 mode 声明（status_set、produces、series_effect、input_requirement、所需资源、capabilities）及 CF-FIX 注册集按 mode 拆分；DSL 新字段 `input`、`release_requires`、`accept_unverified_release`、镜像节点 `rpm_precheck`、Benchmark `config.mode`、Optimization `max_opt_rounds` 及 §4.2.6 三条规则的形式化——V-13b/V-15 维持普通支配；规则①（release_requires）与规则③（优化重验证）共用单独形式化的"汇合必经"定义；规则②为 input: none 的净变更数据流分析；另加 V 规则：`gate_expired` 目标 ≠ `approved` 目标、`on: sys.timeout` 只能指向 fail_safe、保留命名空间 `sys.*`（含 `sys.baseline_build`）；四份示例流水线（§4.2.1 示例一至四原文）作为校验器验收用例，并替换 01 附录 A4。
   - **状态机与等待（E-02）**：ExternalWait 的 `gateway_session` 类与 phase、`external_timeout_min`、`task_suspend` guard（无其他在途效应）、`sys.superseded`、远程作业 `cancel_pending` 与配额恰一次归还、wake 在 running 下不迁移；paused(wait) 成因集合；ExternalWait 记录、wake outbox 与消费协议；`sys.await_external` 保留结果（V-05/V-06 排除于路由穷尽）；分派前资源授予与 awaiting_resource；C-07/C-13/§3.4 同步（全集计时条件、paused 期预算到期）；`input: none` 初始空 series 同事务签发（created → queued 新边）与 submit_patch 拒绝语义；§4.3.5 放行谓词进入核心迁移表——C-16 terminal_success、§2.5 审批 CAS（含 `acknowledged_gaps` 与各报告"通过"谓词）、核销前 consume 复核均检查；进入 publishing 后的超时只登记、不改 C-10/C-11 的 released 映射与 release_outcome 两值；核销复核不通过 → ConsumeRejected(reason = `gaps_changed`) + ledger 级 release_failed 映射（ConsumeRejected 原因枚举同步）；证据链含 ci_plan、Review 与提供基线的 sys.baseline_build task；登录等待超时固定 fail_safe；`external_timeout_min` 无环节点缺省；创建优化计划的准入核对与 `E-PLAN-NO-CAPACITY`；`E-SKILL-EMPTY-SERIES` 入 §2.7 错误码表。
   - **worker 数据面（E-03）**：`task_suspend`、`resource_lease_release`、`image_commit`、`profile_put`、`remote_build_submit`、`remote_build_fetch_logs` 的载荷、幂等域、归属校验与注册表；Gateway 构建 socket 与运维会话 socket 命令（`session_install`）。
   - **效应**：新增效应类别 image.* / remote_build.* / profile.* 的 probe 契约（远程构建效应标记 = idem_key 指纹 + version；ProbeOutcome 增 `deferred`；远程构建 probe 有界（提交 intent 含提交前最大构建号，扫描范围外 → indeterminate）；`backend_source_input_unsupported`；`base_mismatch` → `image_failed_exhausted`；镜像 probe 按 idem_key 查索引）；ImageRecord。
   - **报告与消息**：ImageReport（构建输入闭包、base 标识、读回的实际构建输入、rpm_precheck、base_mismatch）；Quickbuild 后端能力声明与 `comparison = unverifiable` 语义；BenchReport 扩展字段（mode、gate_eligible、validation_complete、逐指标四值与区间、spec_inconclusive_count、opt_gain_pct、opt_verdict、comparison、baseline_revoked/baseline_unavailable）；SuiteVersion / BenchPolicy / SPEC / MeasurementRecord schema；OptimizationPlan 与 OptimizationReport；Profile 记录与兼容字段；各报告"通过"谓词；ReleaseManifest `release_evidence`；LogAnalyzer Diagnosis schema；`ai_draft` 子结构与 AI 证据/采纳记录；多版本对比报告 schema；`get_result` 的 `incomplete` / `retried` 清单与超时记录；目标范围与 ModuleRegistry schema（含 `always_run`）、`create_run.focus_modules`；Profile 新鲜度策略 v2 参数；Quickbuild 的 snapshot manifest 扩展（Profile 快照编号、逐包 commit、显式覆盖版本）、ExpectedSourceManifest、读回字段（`actual_build_conf_digest` / `published_build_conf_digest` 分列、脚本版本、`unknown` 取值）与后端能力证据等级表；BenchReport `comparison` 三值（verified / unverifiable / none）与 `opt_verdict` 的 `comparison_unverifiable` 原因；release_requires 与优化重验证的"汇合必经"形式化（见"注册与 DSL"条）；`incomplete` 条目 `class` 与 `ApprovalDecision.acknowledged_gaps`（每项 = (条目 id, 内容 digest)；覆盖 environment_gap、verification_asset_change 与当前 series 证据链上的 retried 记录）；`get_result` 结论字段（含 `succeeded_with_gaps`）；OptimizationPlan 记录与 series 段 `purpose`（initial / candidate / repair / revert，编排按互斥顺序推导）；`E-CANDIDATE-NOT-REVERT`（响应含 plan_id 与 parent_tree）、`pending_plan_at_terminal`；candidate 受理的预校验结果与完成事务复核（含 `candidate_recheck_failed` 与"预校验拒绝不登记 candidate"）；ModuleRegistry 的 `protected_paths` 与验证资产触及检查；多版本对比报告 digest 入 `release_evidence`。
   - **资源**：板子池租约（generation、sequence 租约、reclaiming/quarantine、失败归因计数）、刷机与探测接口；基线缓存键（构建输入闭包）与 single-flight；镜像存储引用计数。
   - **入口**：MCP 工具 ↔ 操作映射表、request_id 为工具参数、幂等域 (principal, 操作名) 跨传输共享、`submit_bench_suite`、`sys.scheduler`；套件确认命令与权限（本机特权通道）。
   - **部署契约**：无 PHP 约束（D23）——插件、受限 adapter 与宿主侧适配器的注册记录含运行时声明、制品 digest、运行环境闭包 digest、策略版本与扫描结论，加载期复核；**v2.10 追加**：ExecutionManifest 增 deploy 安装集 digest 字段（Run 创建时与最近一次通过扫描的 digest 比对，D23 / §11.2）；无 PHP 例外清单条目（工具名、安装件 digest、PHP 组件、理由、批准人、到期日）只在负责人修订 D23 后存在；运维对 broker 的计划性 drain / restart 须经 launcher 登记（01 §2.2d 计划性回收域），未登记者按故障归责；特权 launcher 的 cgroup v2 spawn / kill 接口（ClineSR CLI、构建边界与 Release broker 实例——broker 的回收与静默判定按实例 cgroup，01 §2.2d）；构建隔离边界的不可变基底 digest 与复位要求。
   - **执行环境**：ExecutionManifest 扩展字段（llm_cli_version、bench_suites_digest、spec_digest、bench_policy_digest、module_registry_digest、build_input_closure_digest、Profile 新鲜度策略版本）。
   - **conformance**：§11.3 v2.0 追加类别逐类落 CF 族；构建隔离与 CLI OS 层约束的部署契约检查项；SourceProvider 接口。

## 17. 附录 A15：勘误记录（冻结后经三方评审通道生效）
- **E-01（HLD-Q1 → 01 V-13b）**：§4.2.6 校验规则集追加——release-approval 型 hitl 须存在支配它的 ReleasePlan 生产节点（按 Agent 注册 produces 声明判定，支配链最近者，同深歧义拒绝加载）。缺陷由 01 首轮评审（Claude Code）登记为 HLD-Q1；形式化定义在 01_Contract_Spec §1.3 V-13b；**01 第二轮复审中三方对规则与生效程序双表态一致 GO，勘误生效**。本条为规则集的静态加严，不触碰任何运行时语义。单一事实源：规则精确文本以 01 V-13b 为准。
- **E-02（D11 外部等待，v2.0 范围扩展引入）**：在冻结的"paused 不占执行槽"之上，把远程构建在途与资源排队纳入等待项——任何 worker 不跨越等待存活（分派前资源授予；远程构建提交后以 `sys.await_external` 挂起本 attempt、wake outbox 续接同一 dispatch）；Run 级 paused 条件扩为"仅剩等待项（gate ∪ external）"；计时改为全集条件（存在任一计费等待即计入预算），paused 期预算可到期；v2.3 补会话等待（提交前 / 提交不确定 / 对账阶段）、远程作业取消后的配额保留、`sys.superseded` 与对冻结语义的完整偏离清单（§4.3.4）。缺陷由 v2.0 首轮评审（Claude Code 登记为 BLOCKER、Codex 登记为 MAJOR）指出原补充未给机制且未走勘误通道。**生效程序**：随本 HLD（v2.x）三方评审一致 GO 生效。单一事实源：规则文本以本文 §4.3.4 为准，01 同步扩展时形式化（附录 B 第 7 组）。
- **E-03（§8.5 worker 数据面命令扩充，v2.0 范围扩展引入）**：在冻结的数据面封闭枚举上追加 `task_suspend`、`resource_lease_release`、`image_commit`、`profile_put`、`remote_build_submit`、`remote_build_fetch_logs` 六条命令，每条沿用 task 级绑定、request_id 幂等与越域拒绝审计；跨 Run 共享存储（基线缓存、Profile 正式区、套件注册表）对业务 worker 无写命令；v2.3 补细则（镜像文件由 launcher 导入、远程提交只引用本 task 已 claimed 的效应、`task_suspend` guard、租约主动释放语义）。缺陷由 v2.0 首轮评审（Claude Code）指出新能力句柄未落到冻结枚举与 D6。**生效程序**：随本 HLD（v2.x）三方评审一致 GO 生效。单一事实源：本文 §8.5。
