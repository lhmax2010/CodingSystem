# Sprint 0 启动前设计 Review

**日期**：2026-05-28
**Reviewer**：Codex
**范围**：Phase 1A Sprint 0 编码/实施前置设计审查。

## 1. 已读文档

按本次启动要求顺序已读：

- `docs/README.md`
- `docs/DEVELOPMENT_RULES.md`
- `docs/prompts/MAIN_PROMPT_for_Codex_v2.2.md`
- `docs/prompts/SPRINT_0_PROMPT_for_Codex_v1.1.md`
- `docs/baseline/00_Agent_Team_Contract_v0.7.2.md`
- `docs/baseline/02_Compiler_Agent_v5.2-RC2.2.md`
- `docs/baseline/06_Code_Navigation_Evidence_Infrastructure_v0.3.3.md`
- `docs/baseline/05_Phased_Development_Plan_v2.1.2.md`
- `docs/adr/ADR_001_CNEI_Scale_Direction.md`

按 R1/R6 补读：

- `docs/prompts/SPRINT_1_PLUS_PROMPT_for_Codex_v1.2.md`
- `docs/baseline/03_Benchmark_Agent_v5.2-RC2.3.md`
- `docs/baseline/07_Benchmark_Skill_Framework_v0.2.1.md`
- `docs/baseline/08_Phase_1_5_Overview_v0.3.md`
- `docs/baseline/09_Demo_Acceptance_Playbook_v0.3.md`
- `docs/adr/S0-10_Scale_Feasibility_Spike.md`
- `docs/checkpoints.md`
- `docs/design_changes/`、`docs/dev_memory/`、`docs/review/`、`docs/spinoffs/`

## 2. 总体结论

Phase 1A 的总体方向成立：Sprint 0 先验证高风险技术假设，之后 Sprint 1+ 再依次实现 Base 层、CNEI、Compiler 主流程、bounded repair loop 和 M1 集成验收。核心架构与业务目标匹配：先收集结构化证据，再让 LLM 做根因分析；确定性判断留在 Tool/Controller 层；用户主代码通过 git worktree 隔离；所有过程可 trace；raw log/token/secret 均有硬约束。

但本次 review 发现若干设计口径不一致，需要 user 确认处理方式后再进入 Sprint 0。主要问题不是架构不可行，而是 gate 定义、阈值、失败策略、初始数据归属存在歧义。

## 3. 需求覆盖度审查

设计能够覆盖 Phase 1A 的主需求：

- Compiler Agent 范围控制合理：cmake/ninja、x86 host、单个小于 100 万行的 Tizen repo、12 类 C/C++ 编译失败场景。
- CNEI 定位正确：不是全局 code graph，而是 Live Evidence Collector，包含 build-system facts、semantic facts、negative_facts、confidence、stale 检测和 Known Issues hints。
- 安全约束完整：full raw log 不进 LLM，artifact/trace 经 redaction，用户源代码只在 isolated workspace 中修改。
- Sprint 0 gate 覆盖关键假设：compile database、clangd、log parser、EvidencePacket、RawDataDetector、KnownIssueMatcher、e2e dry run、stale confidence downgrade。
- ADR-001 正确地把 OS 级 Layer 0/1 实现推迟到 S0-10 数据之后。

## 4. 模块划分 / 数据流 / 接口契约审查

主数据流合理：

`run_compile -> structured_errors -> collect_evidence -> known_issue_match -> Cline analyze -> patch generation -> deterministic validation/apply/rebuild -> artifacts/trace/handoff`

该流程遵守 Cognitive Boundary：schema 校验、路由、retry 次数、budget、raw data 检测、threshold 判断都在代码层，不交给 LLM。

主要风险来自跨文档常量、schema 字段和失败行为的不一致，详见第 7 节。

## 5. Sprint 拆分与依赖审查

Phase 1A 拆分基本成立：

- Sprint 0 先 de-risk。
- Sprint 1 Base 层先做是正确的，因为 Compiler 和 Benchmark 都依赖 Base。
- Sprint 2a/2b 拆分合理，CNEI 单 sprint 风险过高。
- Sprint 3/4/5 顺序合理：先分析主流程，再 patch loop，最后 12 场景和 M1。

Sprint 0 有两个隐藏依赖需要 user/team 提供：

- S0-01 需要确认至少 3 个开发者熟悉候选 repo。
- S0-04 需要 50 份历史 Tizen build failure log。

这不是设计缺陷，但会影响 Sprint 0 启动速度。

## 6. 非功能性约束审查

非功能性约束在设计层可落地：

- Raw data 保护在 Contract、Compiler、CNEI、Demo 中都有约束。
- Compiler / Benchmark 都定义了 token budget。
- trace.json + events.jsonl 适合作为后续 Memory Infrastructure 输入。
- Redaction 和 artifact_ref 是协议级概念。
- check_gate.sh 作为 merge gate 已定义。

当前仓库只有 docs，没有 `scripts/check_gate.sh`、测试配置、lint 配置、schema 或 CI。该状态不与现有项目冲突，但 Sprint 1 开始写产品代码前必须补齐 gate 基础设施。

## 7. 需要 user 决策的问题

### [DESIGN_ISSUE-001] Sprint 0 gate 数量、stale 归属和报告路径不一致

证据：

- `SPRINT_0_PROMPT` / `MAIN_PROMPT` 定义 9 个任务：S0-01 前置任务 + S0-02..S0-09 共 8 个 core gates。
- `05_Phased_Development_Plan` 同意该口径，并规定报告路径为 `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/`。
- `02_Compiler_Agent` A18 仍写“7 个关键假设 / 七项验证”，后文又写“所有 8 项必须 PASS”，并使用旧路径 `docs/spike_reports/spike_0X_<name>.md`。
- `SPRINT_0_PROMPT` 把 stale 检测同时放在 S0-03 acceptance 和 S0-09 独立 gate。
- `CNEI` 仍写 stale 验证扩展 Compiler A18.1 第 6 项，和当前 S0 编号不一致。

影响：

- Sprint 0 执行时可能重复验证 stale，或把报告放到错误目录。

建议：

- 以 `MAIN_PROMPT v2.2`、`SPRINT_0_PROMPT v1.1`、`05_Phased_Development_Plan v2.1.2` 为执行权威。
- 报告统一放 `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/`。
- S0-03 聚焦 clangd 启动、索引、definition/reference 准确率。
- S0-09 作为 stale 检测 + confidence downgrade 的唯一 gate。

### [DESIGN_ISSUE-002] RawDataDetector 阈值冲突

证据：

- Team Contract 5.6.3 规定默认 raw prompt 阈值为 5000 字符 / 200 行。
- Compiler A5.2 重复了 5000 字符规则。
- Sprint 0 S0-06 明确要求构造 5000 字符 raw compile.log prompt 并拦截。
- Compiler A8.2 骨架却写 `DEFAULT_SIZE_THRESHOLD_BYTES = 20480`。
- Demo 场景使用 8000+ 字符 raw log fixture。

影响：

- 如果实现按 20 KB 骨架走，S0-06 的 5000 字符测试可能不会失败，违反 Contract gate。

建议：

- Phase 1A blocking 规则采用 Team Contract 的 5000 字符 / 200 行。
- 如果保留 20 KB，定义为额外 detector，不替代 5000 字符规则。

### [DESIGN_ISSUE-003] CompilerController 引用 `verify_timeout_sec`，但 budget schema/default 没定义

证据：

- Compiler TaskInput budget 列出 `compile_timeout_sec`、`cline_timeout_sec`、token 和 evidence budget。
- DEFAULT_BUDGET_PROFILE 也没有 `verify_timeout_sec`。
- CompilerController 骨架在 rebuild verification 阶段调用 `budget["verify_timeout_sec"]`。

影响：

- Sprint 4 若照骨架实现，会在 rebuild verification 处触发 `KeyError`。

建议：

- Sprint 4 前明确一个设计决策：
  - 推荐：在 budget schema/default 中显式增加 `verify_timeout_sec`。
  - 备选：verification 复用 `compile_timeout_sec`，并修正骨架引用。

### [DESIGN_ISSUE-004] Evidence collection 失败行为冲突

证据：

- Compiler 状态图写 `CollectEvidence -> EmitFailure : evidence collection failed`。
- Compiler failure_class 包含 `evidence_collection_failed`。
- CompilerController 骨架捕获 evidence collection 的 `ToolInvocationError` 后，只写 trace failure，然后继续无 evidence 分析。

影响：

- 这会让 Phase 1A 在没有 EvidencePacket 的情况下进入 Cline analyze，和 CNEI 作为 Phase 1A 必需依赖、Exit Criteria 中 CNEI 使用率要求存在冲突。

建议：

- Phase 1A 默认 fail fast，返回 `evidence_collection_failed`。
- 如果希望允许 degraded no-evidence 分析，需要 user 明确批准，并在 review_packet 中记录 deviation。

### [DESIGN_ISSUE-005] Known Issues 初始数据时机不清

证据：

- CNEI 7.4.0 要求 Phase 1A Sprint 0 提交首版 `known_issues.yaml`，20-30 条。
- Demo 准备也要求 Sprint 0 已有 20-30 条 Known Issues。
- Sprint 0 S0-07 只要求准备 5 份样例 Known Issue 做 matcher 验证。
- 开发计划把 “KnownIssueMatcher + Known Issues YAML 初始数据” 放在 Sprint 2b，同时又说 Sprint 0 期间应启动团队协调。

影响：

- S0-07 可能被理解成 matcher-only spike，也可能被理解成 full data gate。

建议：

- S0-07 作为 matcher spike，只要求 5 条符合 governance schema 的样例。
- Sprint 0 同步启动 20-30 条生产 Known Issues 的团队协调，但除非 user 明确要求，否则不把完整数据集作为 S0 PASS gate。

### [DESIGN_ISSUE-006] Benchmark AgentResult 字段与 Team Contract 不一致

证据：

- Team Contract 6.3 要求 AgentResult 必含 `token_usage`。
- Benchmark Agent B6.2 使用 `token_usage_summary`。

影响：

- Phase 1B 照文档实现会违反共享 AgentResult contract。

建议：

- Phase 1B 前统一为 Contract 要求：AgentResult 必含 `token_usage`。
- `token_usage_summary` 可以作为报告内部扩展字段，但不能替代 `token_usage`。

## 8. 非阻塞建议

### [DESIGN_SUGGESTION-001] 旧版本引用可作为文档债记录

Benchmark、Phase 1.5、Demo 文档中仍有少量关联文档版本引用旧口径，例如 Benchmark 头部引用 Compiler RC2.1 / CNEI v0.3.1 / Skill v0.1，而当前基线是 Compiler RC2.2 / CNEI v0.3.3 / Skill v0.2.1。

该问题不阻塞 Sprint 0，但后续 review 时可能造成困惑。

### [DESIGN_SUGGESTION-002] S0-01/S0-04 的 user-owned 数据需提前准备

Sprint 0 需要本地仓库无法推断的输入：

- 候选 Tizen cmake/ninja repo。
- 至少 3 个熟悉 repo 的开发者确认。
- 50 份历史 build failure log 的来源。
- 可在 x86 构建的 Tizen 环境。

建议 user 在 S0-01 启动前给出候选 repo 和日志来源。

### [DESIGN_SUGGESTION-003] 明确 `scripts/check_gate.sh` 引入时机

当前仓库是 docs-only，没有 gate 脚本。设计要求 merge 前必须跑 `scripts/check_gate.sh`。

建议在 Sprint 1 Base Layer 引入正式 gate 脚本，不在 Sprint 0 加产品代码，因为 Sprint 0 明确是 spike-only。

## 9. R12 现有项目扫描结果

当前仓库内容：

- 只有 `docs/`。
- 没有 `agents/`、`infrastructure/`、`tools/`、`scripts/`、`tests/`、`schemas/`、CI 目录。
- 没有 package/build/lint/test 配置。

结论：

- 没有现有代码风格、测试框架、构建系统、lint 配置或 CI 约定与 baseline 冲突。
- 后续可以按 baseline 目录规划新增实现，不会覆盖已有代码。

## 10. 我对 Sprint 0 的理解

Sprint 0 是 Spike Gate，不写产品代码。它要完成：

- 选定真实 Tizen cmake/ninja repo。
- 验证 compile database 生成。
- 验证 clangd 启动、索引、definition/reference 准确率。
- 用真实历史日志验证 LogErrorParser。
- 验证 EvidencePacket 生成时间和 token budget。
- 验证 RawDataDetector 只放行 bounded + redacted + source-linked excerpt。
- 验证 KnownIssueMatcher 的命中/不命中准确性。
- 跑通 compile fail -> parse -> evidence -> analyze 的 e2e dry run，不 apply patch。
- 验证 stale compile database 检测和 confidence downgrade。

S0-10 是独立 scale spike，未经 user 指令不启动。

## 11. user 确认后 S0-01 开始方式

待 user 确认上述 `[DESIGN_ISSUE]` 处理口径后，S0-01 应这样开始：

1. 创建/切换到 `codex/sprint-0-main`。
2. 创建 `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/`。
3. 根据 user 提供的候选 Tizen repo，或 user 允许访问的 repo 列表，做候选评估。
4. 按 S0-01 acceptance 逐项验证：
   - cmake + ninja
   - 小于 100 万行
   - x86 workstation 可 clone + build
   - 有历史 build 失败 commit/log
   - 至少 3 个熟悉该 repo 的开发者经 user/team 确认
5. 输出 `spike_01_repo_selection.md`，记录数据和推荐 repo。

## 12. 当前决策状态

按 R1/R2，因为发现了 `[DESIGN_ISSUE]`，Sprint 0 实施应暂停，等待 user 确认处理口径。
