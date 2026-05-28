# Coding System 开发计划 v2.1.3（Phase 1A/1B/1.5 Sprint 拆分）

**版本**：v2.1.3
**状态**：Implementation Plan
**适用对象**：Codex 开发主体、用户（PM）、外部 AI Reviewer（Claude / ChatGPT / Kimi）
**关联文档**（v2.1.2 基线，与 MAIN_PROMPT v2.2 一致）：
- 《Agent Team Contract v0.7.3》（文档 00，Locked）
- 《Compiler Agent v5.2-RC2.3》（文档 02）
- 《Benchmark Agent v5.2-RC2.4》（文档 03）
- 《CNEI v0.3.4》（文档 06）
- 《Benchmark Skill 框架 v0.2.1》（文档 07）
- 《Phase 1.5 总览 v0.3》（文档 08）
- 《Demo & 验收剧本 v0.3》（文档 09）

**文档目的**：把设计文档落地成**可执行的 Sprint 计划**，定义每个 Sprint 的目标、任务、deliverable、Definition of Done（DoD）和 Exit Criteria。

**版本历程**：
- v1.1：Phase 1 整体节奏初版
- v2.0：Phase 1A/1B 拆分 + 工作日粒度
- v2.1：ChatGPT + Kimi 联合 review 反馈（Sprint 2 拆分 / merge gate / Phase 1B 启动前置 / 风险表）
- v2.1.1：ChatGPT + Kimi v0.2 review 反馈（Sprint 0 工时修正 / Sprint 2b 弹性触发 / review_packet 字段 / merge gate 第 9 项）
- **v2.1.2**：ChatGPT + Kimi 批次 3 修订 review，consistency cleanup（头部基线版本同步 / Sprint 0 残留 S0-10 清理 / 工时 10.5→11 天 / S0-03 工时 3→3.5 / check_gate.sh 实现细节修正）
- **v2.1.3（本版）**：Codex Sprint 0 design review 反馈 — 关联文档版本同步到 Contract v0.7.3 / Compiler RC2.3 / Benchmark RC2.4 / CNEI v0.3.4；S0-03 注明 stale 仅 mtime 基础探测（完整验证归 S0-09，解决 Issue 1 归属重叠）；S0-07 注明 5 份样例仅验证 matcher 机制、20-30 条是 Sprint 2b 前置（解决 Issue 5 时机不清）

---

## 0. 全局原则

### 0.1 时间盒与缓冲

- **每个 Sprint = 2 周**（10 个工作日，2 周自然日）
- **每个 Sprint 留 20% 缓冲**（即 8 天有效工作 + 2 天缓冲）
- **Spike Sprint 例外**：可短至 1 周或长至 3 周，按发现的问题决定

### 0.2 Sprint 末尾必做

每个 Sprint 最后一天，Codex 必须：

1. 更新 `docs/dev_memory/current_state.md`（项目当前状态快照）
2. 更新 `docs/dev_memory/decision_log.md`（本 Sprint 的关键决策）
3. 更新 `docs/dev_memory/blocker_log.md`（遇到的阻塞 + 解决方式）
4. 生成 `docs/dev_memory/phase_X/sprint_N/handoff_summary.md`（给 user/外部 AI review 用）
5. 提交 review_packet.md（见 0.4）

### 0.3 不走 PR，直接 git push

**根据 user 决策（前几轮已确认）**：

- Codex 在 branch（`codex/sprint-N-task-X`）上 commit + push
- **同时生成 review_packet.md**（给外部 AI review 用）
- user 拿 review_packet 给 Claude/ChatGPT/Kimi review
- review 通过后 Codex 自己 `git merge` 到 main + `git push origin main`
- branch 删除

这种方式**绕开 GitHub PR**，但保留 review gate（user 的批准就是 gate）。

### 0.3.1 Merge Gate Script（v2.1 新增，ChatGPT 反馈）

虽然不走 GitHub PR，但 **merge 到 main 之前必须跑机器 gate**，避免"user 口头批准但实际有问题就 merge"。

每个 repo 必须有 `scripts/check_gate.sh`，包含以下检查：

```bash
#!/bin/bash
# scripts/check_gate.sh
# Run before merging any branch to main. Exit non-zero blocks merge.
# v2.1.2 修正：去掉 set -e 与自定义错误信息冲突；review_packet 路径对齐；dev_memory 4 文件检查。

# 不用 set -e —— 我们要在每个步骤后自定义错误信息

run_blocking() {
  local name="$1"
  shift
  echo "=== ${name} ==="
  if ! "$@"; then
    echo "❌ FAIL: ${name}"
    exit 1
  fi
}

run_advisory() {
  local name="$1"
  shift
  echo "=== ${name} (ADVISORY) ==="
  if ! "$@"; then
    echo "⚠️  ADVISORY warning: ${name} (not blocking)"
    echo "   This warning must be listed in review_packet §6"
  fi
}

# ===== 8 个 blocking gates =====

# 1. 单元测试
run_blocking "1. Unit tests" pytest tests/ -v

# 2. Coverage ≥ 80%
echo "=== 2. Coverage ==="
COV_RAW=$(pytest tests/ --cov=. --cov-report=term-missing 2>&1 | grep -E '^TOTAL' | awk '{print $NF}' | tr -d '%')
if [ -z "$COV_RAW" ]; then
  echo "❌ FAIL: cannot parse coverage from pytest output"
  exit 1
fi
if [ "$COV_RAW" -lt 80 ]; then
  echo "❌ FAIL: coverage $COV_RAW < 80"
  exit 1
fi
echo "   Coverage: ${COV_RAW}%"

# 3. Schema validation
run_blocking "3. Schema validation" python -m scripts.validate_schemas

# 4. Lint
run_blocking "4a. Lint (ruff)" ruff check .
run_blocking "4b. Lint (mypy)" mypy --strict agents/ infrastructure/

# 5. No raw log fixtures committed
echo "=== 5. No raw log fixtures ==="
CHANGED_FILES=$(git diff main --name-only)
if [ -n "$CHANGED_FILES" ]; then
  echo "$CHANGED_FILES" | xargs python -m scripts.detect_raw_log_fixture --files-from-stdin
  if [ $? -ne 0 ]; then
    echo "❌ FAIL: raw log fixture detected"
    exit 1
  fi
fi

# 6. No secret patterns
echo "=== 6. No secret patterns ==="
git diff main | python -m scripts.detect_secret_patterns
if [ $? -ne 0 ]; then
  echo "❌ FAIL: secret pattern detected"
  exit 1
fi

# 7. review_packet exists for this branch (v2.1.2 修正：用正确路径)
echo "=== 7. review_packet exists ==="
# 检查有任何 review_packet 已生成（不依赖具体 branch name）
if ! find docs/dev_memory -path "*/review_packets/*.md" -newer docs/dev_memory/.last_gate 2>/dev/null | grep -q .; then
  # fallback：至少要存在一个 review_packet（首次 commit 用）
  if ! find docs/dev_memory -path "*/review_packets/*.md" | grep -q .; then
    echo "❌ FAIL: no review_packet found in docs/dev_memory/**/review_packets/"
    exit 1
  fi
fi
touch docs/dev_memory/.last_gate

# 8. dev_memory 4 files + handoff_summary updated (v2.1.2 修正：完整检查)
echo "=== 8. dev_memory updated ==="
REQUIRED_FILES=(
  "docs/dev_memory/current_state.md"
  "docs/dev_memory/decision_log.md"
  "docs/dev_memory/blocker_log.md"
)
for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "❌ FAIL: ${f} missing"
    exit 1
  fi
done
# Sprint 末尾 commit 还需要 handoff_summary（用 git log 检测当前 sprint）
if git log main..HEAD --name-only | grep -q "handoff_summary.md"; then
  echo "   Sprint-end commit: handoff_summary present"
fi

# ===== 1 个 advisory check =====

run_advisory "9. Design doc consistency check" python -m scripts.validate_doc_consistency --strict-fields version,team_contract_compatibility

echo ""
echo "✅ All 8 blocking gates PASSED + 1 advisory check completed."
echo "   Safe to merge."
```

**check_gate.sh 项数明确**（v2.1.2 表述精化，对应 prompt v2.2）：

- **8 个 blocking gates**（项 1-8）：任一 FAIL 不允许 merge
- **1 个 advisory check**（项 9）：emit warning，不 block，但必须在 review_packet §6 列出

**v2.1.2 实现细节修正**（ChatGPT review 反馈）：

- 不用 `set -e`：与自定义错误信息冲突
- 用 `run_blocking` / `run_advisory` 函数封装：每个步骤错误信息独立
- review_packet 路径用 `find docs/dev_memory -path "*/review_packets/*.md"`：与文档定义路径一致
- dev_memory 检查从 1 个文件扩到 4 个文件（current_state / decision_log / blocker_log + handoff_summary）
- COV 解析失败时显式报错而不是隐式继续

**第 9 项实施细节**：

- `scripts/validate_doc_consistency.py` 扫描代码中的关键硬编码值：
  - AgentDescriptor 中的 `team_contract_compatibility`
  - failure_class 枚举值
  - HandoffRequest reason 枚举值
  - 版本号字符串
  - schema 字段名（Pydantic models 的字段是否与设计文档列出的一致）
- 与对应设计文档 markdown 中提取的"权威值"比对
- 检测到不一致：emit warning（advisory），不 block merge
- 真正"代码偏离设计"的情况要靠**外部 AI review** 兜底

**强制规则**：

- Codex **必须**在 merge 前跑 `./scripts/check_gate.sh`
- 任何一项 FAIL 不允许 merge
- review_packet 必须含 `gate_check_result: PASS`（含 8 项各自结果）

这相当于把 GitHub PR 的 CI gate **在本地实现一遍**，既不走 PR，又有机器 gate 兜底。

### 0.4 review_packet.md 模板

每个 review 单元产出一份 review_packet.md，放在 `docs/dev_memory/phase_X/sprint_N/review_packets/`。模板：

```markdown
# Review Packet: {sprint}-{task_id}-{short_title}

## 1. 这次改动了什么

- [一句话总结]
- 涉及文件: [文件路径列表]
- 代码增量: +XX 行 / -YY 行

## 2. 设计决策

- 关键设计: [简述]
- **与设计文档对应章节**: [必填，格式：`Compiler v5.2-RC2.3 §A8.3` / `CNEI v0.3.4 §4.3.1` / `Skill v0.2.1 §5.4` 等]（v2.1.1 强化）
- 与原计划的 deviation: [如有，必须解释]
- **本变更涉及的 contract**: [Team Contract v0.7.3 哪些条款？]（v2.1.1 新增）

## 3. Diff（关键部分）

```diff
[关键代码 diff，可摘录]
```

## 4. 测试

- 测试命令: `pytest tests/...`（v2.1 新增）
- 单元测试: 通过 / 失败 / 跳过
- 覆盖率: XX%（要求 ≥ 80%）
- Coverage report 路径: docs/dev_memory/phase_X/sprint_N/coverage_report.html（v2.1 新增）
- 集成测试: [描述]
- Artifact sample 路径: docs/dev_memory/phase_X/sprint_N/sample_artifacts/（v2.1 新增）
- **scripts/check_gate.sh 结果**: PASS / FAIL（v2.1 新增）

## 5. 自查 checklist

- [ ] 遵守 Team Contract v0.7.3
- [ ] 遵守 Cognitive Boundary（确定性判断不交给 LLM）
- [ ] 遵守 Raw Log 硬约束
- [ ] Token Budget 强制
- [ ] Secret Redaction 自动
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试通过
- [ ] dev_memory 已更新

## 6. 已知风险 / Blocker

- [描述]

## 7. Commit 信息（v2.1 新增）

- Commit hash: {commit_hash}
- Branch: {branch}
- Author: codex
- Date: {timestamp}

## 8. 回滚命令

```bash
git reset --hard {previous_commit_hash}
git push origin main --force-with-lease  # 仅在必要时
```
```

### 0.5 dev_memory 体系

```
docs/dev_memory/
├── current_state.md          # 项目当前状态快照（每个 sprint 末尾更新）
├── decision_log.md           # 跨 sprint 关键决策
├── blocker_log.md            # 阻塞记录
├── phase_1a/
│   ├── sprint_0_spike/
│   │   ├── handoff_summary.md
│   │   ├── spike_reports/
│   │   │   ├── spike_01_compile_commands.md
│   │   │   ├── spike_02_clangd.md
│   │   │   └── ...
│   │   └── review_packets/
│   ├── sprint_1_base_layer/
│   ├── sprint_2_cnei/
│   ├── sprint_3_compiler_main/
│   ├── sprint_4_repair_loop/
│   └── sprint_5_integration_m1/
├── phase_1b/
│   ├── sprint_0b_spike/
│   ├── sprint_1b_skill_runtime/
│   └── ...
└── phase_1_5/
    └── ...
```

---

## 1. Phase 1A 总览

### 1.1 Phase 1A 目标（继承 Compiler v5.2-RC2.1 A1.1）

让 Compiler Agent 在选定 Tizen repo（cmake/ninja，< 100 万行）上做到：

- 12 种典型 C/C++ 编译失败场景中**自动修复率 ≥ 60%**
- 内部 5-10 人 dogfooding 验证
- 所有修订/PATCH 输出符合 Cognitive Boundary 原则
- 完整 trace + token budget + secret redaction

### 1.2 Phase 1A Sprint 拆分（v2.1 修订）

**v2.1 修订**：Sprint 2 拆分为 2a/2b（原 16 天工作量超支 100%），总工期延长 2 周。

| Sprint | 工期 | 主题 | Exit Criteria 关键项 |
|---|---|---|---|
| **Sprint 0** | 1-2 周 | **Spike Gate**（开工前验证） | CNEI 8 项 Spike PASS |
| **Sprint 1** | 2 周 | Base 层 | BaseAgentController + 9 个 helper 类完成 |
| **Sprint 2a** | 2 周 | **CNEI Backend Indexers**（v2.1 新增）| tree-sitter / ctags / ripgrep / SQLite / CompileCommandParser |
| **Sprint 2b** | 2 周 | **CNEI 核心层 + EvidenceCollector**（v2.1 新增） | clangd B++ + stale + LogErrorParser + Collectors + EvidenceCollector + Known Issues |
| **Sprint 3** | 2 周 | Compiler 主流程（probe → analyze） | 5/12 场景 happy path 跑通 |
| **Sprint 4** | 2 周 | Compiler bounded repair loop + verify | 8/12 场景闭环通过（**v2.1 不含 12 场景完整集成测试，移到 Sprint 5**）|
| **Sprint 5** | 2 周 | 集成 + 12 场景完整测试 + M1 验收 | 12 场景 ≥ 60% 自动修复 + Demo 通过 |

**总工期**：**12-14 周 ≈ 3-3.5 个月**（v2.1 调整，原 v2.0 的 10-12 周不现实）

**v2.1 工期变化的对外说明**：

- Phase 1A 总工期延长 2 周，符合实际开发节奏
- Compiler Agent v5.2-RC2.3 A1.3 节中的 Phase 1A 时长承诺**同步更新为 3-3.5 个月**
- 这是更现实的估算，避免开发到一半发现进度卡死

### 1.3 Phase 1A 团队配置

- **核心开发**：Codex（AI），全程
- **PM / 决策**：user，每 Sprint 末尾 review + 决策
- **外部 reviewer**：Claude / ChatGPT / Kimi，按需调用
- **试用用户**：内部 5-10 人，Sprint 4-5 加入 dogfooding

---

## 2. Phase 1A Sprint 详细规划

### Sprint 0 ：Phase 1A Spike Gate（1-2 周）

**目标**：验证 Compiler Agent v5.2-RC2.1 A18 节定义的 8 项关键假设，避免基于错误前提构建系统。

**子任务**：

| 任务 ID | 任务名 | 工时（天）| 验证标准 |
|---|---|---|---|
| S0-01 | 选定 Tizen 真实 repo（cmake/ninja）| 0.5 | 1 个 repo 确认可用 |
| S0-02 | 验证 `CMAKE_EXPORT_COMPILE_COMMANDS=ON` 能生成 compile_commands.json | 0.5 | 覆盖所有 source file |
| S0-03 | **clangd 启动 + 索引 + 准确率抽样**（v2.1.1 合并；stale 仅 mtime 基础探测，完整验证见 S0-09）| 3.5 | < 5 min / < 4GB / definition ≥ 90% / references ≥ 85% |
| S0-04 | LogErrorParser 在 50 份历史日志上覆盖度 | 2 | 5 类错误覆盖率 ≥ 80% |
| S0-05 | EvidencePacket 生成性能 | 1 | < 2s / < 4000 tokens |
| S0-06 | Bounded log_excerpt 通过 RawDataDetector | 1 | 含 excerpt 放行、不含拦截 |
| S0-07 | Known Issue matcher 命中/不命中验证（仅验证 matcher 机制，用 5 份样例；20-30 条完整数据是 Sprint 2b 前置，见 S2b-06）| 1 | 准确率 100%（5 份样例） |
| S0-08 | End-to-end dry run（compile fail → evidence → analyze） | 1.5 | trace 完整、token budget 不超 |
| S0-09 | **stale 检测 + confidence 降级**（v0.3.1 新增）| 1 | stale=true 时 facts 降为 medium |

**v2.1.2 工时合计**：11 天（含 1 天弹性；v2.1 是 12 天，超出 2 周上限；v2.1.1 合并 S0-03/04 + 重新编号；v2.1.2 修正 S0-03 工时为 3.5 天）

**v2.1.2 工时核算**：S0-01 (0.5) + S0-02 (0.5) + S0-03 (3.5) + S0-04 (2) + S0-05 (1) + S0-06 (1) + S0-07 (1) + S0-08 (1.5) + S0-09 (1) = **11 天**

**Sprint 0 超时处理规则**（v2.1.1 新增）：

- **2 周（10 工作日）是软上限**：可以延 0.5 天
- **超出 2 周** ：必须做拆分决策，将以下任务推到 Sprint 1 启动前完成（不阻塞主流程）：
  - S0-04（LogErrorParser 覆盖度，可挪到 Sprint 1 启动 Day 1）
  - S0-07（Known Issue matcher 命中验证，可挪到 Sprint 2b 启动 Day 1）
- **核心 spike 项不可推迟**：S0-01 / S0-02 / S0-03 / S0-05 / S0-08 必须 Sprint 0 完成

**Deliverable**：

- 9 份 spike report（`docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/`，对应 S0-01 ~ S0-09）
- 1 份汇总报告 `spike_summary.md`
- 1 份 ADR（如有任何 PARTIAL/FAIL，记录决策）

**Definition of Done**：

- [ ] S0-01 前置选择任务完成（Tizen repo 确认）
- [ ] **8 个核心 Spike Gate 全部 PASS**（S0-02 / S0-03 / S0-04 / S0-05 / S0-06 / S0-07 / S0-08 / S0-09）
- [ ] 任何 PARTIAL/FAIL 都有明确 ADR：A（重做）/ B（降目标）/ C（推 1.5）
- [ ] user + 至少 1 个外部 AI 通过 `spike_summary.md` review

**失败处理**：

- **PASS**：进入 Sprint 1
- **PARTIAL（1-2 项）**：按 ADR 处理；如选 B（降目标），更新 RC2.1 文档的 Exit Criteria
- **FAIL（≥ 3 项）**：**Stop the line**，整体方案重评估；可能需要 RC3 或推迟 Phase 1A

---

### Sprint 1：Base 层（2 周）

**目标**：实现所有 Agent 共享的 Base 层组件（详见 Compiler A8.2 / Benchmark B8.2 节）。

**子任务**：

| 任务 ID | 任务名 | 工时（天）| 关联文档 |
|---|---|---|---|
| S1-01 | `BaseAgentController` 骨架 | 1 | Compiler A8.2 |
| S1-02 | `BudgetTracker`（时间预算 + ensure_time_budget）| 1 | Contract 6.4 |
| S1-03 | `TokenLedger`（token 累计 + budget 强制）| 1.5 | Contract 5.5.2 |
| S1-04 | `ArtifactManager`（含 redaction filter 集成点）| 1.5 | Contract 3.4 |
| S1-05 | `TraceWriter`（trace.json + events.jsonl 同步写）| 1.5 | Contract 4.2 / 4.4 |
| S1-06 | `HandoffBuilder`（含 disambiguator 支持）| 1 | Contract 2.6 |
| S1-07 | `FailureEnvelopeWriter`（含 Team-level failure_class）| 1 | Contract 2a.2 |
| S1-08 | `Redactor`（L1/L2/L3 分级 + 路径局部替换）| 2 | Contract 8.5 |
| S1-09 | `RawDataDetector`（< 5000 字符放行 + EvidencePacket excerpt 区分）| 1.5 | Contract 5.6.3 |
| S1-10 | `ToolInvoker`（统一 Tool 调用入口，自动 trace）| 1 | Compiler A8.2 |
| S1-11 | 单元测试 | 2 | UT 覆盖率 ≥ 80% |

**Deliverable**：

```
agents/base/
├── base_agent_controller.py
├── budget_tracker.py
├── token_ledger.py
├── artifact_manager.py
├── trace_writer.py
├── handoff_builder.py
├── failure_envelope.py
├── redaction.py
├── raw_data_detector.py
└── tool_invoker.py

tests/agents/base/
└── （对应单元测试，覆盖率 ≥ 80%）
```

**Definition of Done**：

- [ ] 所有 10 个组件代码完成 + 单元测试覆盖率 ≥ 80%
- [ ] Redactor L1/L2/L3 三级分别有测试
- [ ] RawDataDetector 含 excerpt 放行测试 + raw log 拦截测试
- [ ] BudgetTracker / TokenLedger 边界测试（恰好到达 budget / 超过 budget）
- [ ] HandoffBuilder 测试 8 位 hex 默认 + 12 位 hex disambiguator
- [ ] review_packet 通过 user + 至少 1 个外部 AI
- [ ] dev_memory 更新

---

### Sprint 2a：CNEI Backend Indexers（2 周，v2.1 拆分 + v2.1.1 补全）

**目标**：实现 Backend Indexer 层和基础数据结构（CNEI 第一层）。

**子任务**：

| 任务 ID | 任务名 | 工时（天）| 关联文档 |
|---|---|---|---|
| S2a-01 | CNEIConfig 加载 + 默认值 | 0.5 | CNEI 11.1 |
| S2a-02 | EvidencePacket / NegativeFact / LogExcerpt Pydantic models | 1 | CNEI 2.1 |
| S2a-03 | tree-sitter 多语言 AST | 1 | CNEI 4.1 |
| S2a-04 | universal-ctags 集成 | 1 | CNEI 4.2 |
| S2a-05 | ripgrep 兜底搜索 | 0.5 | CNEI 4.4 |
| S2a-06 | SQLite 索引 cache | 1 | CNEI 4.5 |
| S2a-07 | CompileCommandParser | 1 | CNEI 3.2.1 |
| S2a-08 | 单元测试 | 2 | UT ≥ 80% |

**工时合计**：8 天（符合 Sprint 限制）

**Deliverable**：

```
infrastructure/code_navigation_evidence/
├── config.py
├── data_models.py
├── indexers/
│   ├── tree_sitter_backend.py
│   ├── ctags_backend.py
│   ├── ripgrep_backend.py
│   └── sqlite_cache.py
└── collectors/
    └── compile_command_parser.py
```

**Definition of Done**：

- [ ] 4 个 Backend Indexer 可独立使用
- [ ] EvidencePacket Pydantic schema 含所有 v0.3.4 字段
- [ ] CompileCommandParser 在 Sprint 0 选定的 Tizen repo 上能正确解析
- [ ] UT 覆盖率 ≥ 80%
- [ ] review_packet 通过

---

### Sprint 2b：CNEI 核心层 + EvidenceCollector（2 周，v2.1 拆分 + v2.1.1 补全）

**目标**：实现 CNEI 的核心 collector + clangd B++ + EvidenceCollector，产出可用的 EvidencePacket。

**子任务**：

| 任务 ID | 任务名 | 工时（天）| 关联文档 |
|---|---|---|---|
| S2b-01 | **clangd B++ 5-Gate 决策树**（核心）| 2 | CNEI 4.3.1 |
| S2b-02 | **clangd_stale 检测 + confidence 降级** | 1 | CNEI 4.3.2.1 |
| S2b-03 | LogErrorParser（5 类错误）| 1.5 | CNEI 3.2 |
| S2b-04 | LinkCommandCollector | 1 | CNEI 3.2.2 |
| S2b-05 | CMakeContextCollector | 1 | CNEI 3.2.3 |
| S2b-06 | KnownIssueMatcher + Known Issues YAML 初始数据 | 1 | CNEI 7.4 + 7.4.0 |
| S2b-07 | **EvidenceCollector**（含 mandatory_negative_checks）| 2 | CNEI 6.2 |
| S2b-08 | 集成测试 | 1.5 | 在 Tizen repo 跑通 |

**工时合计**：11 天（紧张但可控）

**实际工作量管理（v2.1.1 加强：Sprint 0 PARTIAL 自动触发扩容）**：

**v2.1.1 新增自动扩容触发条件**（ChatGPT + Kimi 都强调）：

```
IF Sprint 0 在以下任一项标记 PARTIAL：
   - S0-03 clangd 启动 + 索引 + 准确率
   - S0-04 LogErrorParser 覆盖度
   - S0-05 EvidencePacket 生成性能
   - S0-08 End-to-end dry run
THEN Sprint 2b 自动触发以下之一（user + 至少 1 个外部 AI review 决定）：
   - 选项 A：Sprint 2b 扩容到 2.5 周（保留任务范围，单 Sprint 跨周）
   - 选项 B：Sprint 2b 拆为 Sprint 2b1（核心 9 天）+ Sprint 2b2（EvidenceCollector + Known Issues + 集成测试 5-6 天）
   - 选项 C：Phase 1A 总目标降级（如 success rate 从 60% 改 50%）

ELSE Sprint 2b 按 11 天紧凑计划执行
```

**常规工作量管理**（不依赖 Sprint 0 结果）：

- 如果 S2b-01 / S2b-07 实际超时，可将 S2b-06 的"初始数据"准入审核**前置到 Sprint 0/1 期间团队协调**，让本 sprint 只做加载逻辑
- PkgConfigCollector 推迟到 Sprint 3（虽然 CNEI 6.2 列入 collector，但 Phase 1A 不是必需）

**Deliverable**：

```
infrastructure/code_navigation_evidence/
├── service.py                  # 顶层 API
├── indexers/
│   └── clangd_backend.py       # 含 5-Gate 决策树 + stale 检测
├── collectors/
│   ├── log_error_parser.py
│   ├── link_command_collector.py
│   ├── cmake_context_collector.py
│   └── known_issue_matcher.py
├── evidence_collector.py
└── known_issues/
    └── known_issues.yaml       # 20-30 条初始数据
```

**Definition of Done**：

- [ ] CNEI 主 API `get_evidence_packet(error_event) -> EvidencePacket` 可用
- [ ] clangd B++ 5 个 Gate 各有测试
- [ ] clangd_stale 检测 + confidence 降级有测试
- [ ] EvidencePacket 含 facts + negative_facts + log_excerpt + provenance + scope
- [ ] Known Issues 含至少 20 条初始数据（团队提供）
- [ ] 在 Sprint 0 选定的 Tizen repo 上能产出有效 EvidencePacket
- [ ] UT 覆盖率 ≥ 80%
- [ ] review_packet 通过

**Sprint 2a + 2b 风险点**：

- clangd 集成是 Sprint 2b 的高风险点（已在 Sprint 0 spike 缓解，但实际生产代码集成可能再发现问题）
- Known Issues 初始数据准入要早启动（建议 Sprint 0 期间就开始团队协调，**强制条件**）

---

### Sprint 3：Compiler Agent 主流程（probe → analyze）（2 周）

**目标**：实现 Compiler Agent 从 probe_env 到 analyze 的主流程，验证 happy path 编译失败分析。

**子任务**：

| 任务 ID | 任务名 | 工时（天）| 关联文档 |
|---|---|---|---|
| S3-01 | `CompilerController` 主框架 | 1 | Compiler A8.3 |
| S3-02 | Tool: `probe_build_env` | 1 | Compiler A7 |
| S3-03 | Tool: `run_compile` | 1 | Compiler A7 |
| S3-04 | Tool: `summarize_compile_log`（structured errors）| 1.5 | Compiler A5.2 |
| S3-05 | Tool: `collect_evidence`（调用 CNEI） | 0.5 | Compiler A5.3 |
| S3-06 | Tool: `match_known_issues`（调用 CNEI） | 0.5 | Compiler A5.4 |
| S3-07 | `ClineAdapter` + Cline 集成 | 2 | Compiler A8.2 |
| S3-08 | `analyze_compile_failure` Cline 调用 | 1.5 | Compiler A5.5 |
| S3-09 | `generate_suggestion_patch` Cline 调用 | 1.5 | Compiler A5.6 |
| S3-10 | Prompt: `compiler_system.md`（A12 模板） | 1 | Compiler A12 |
| S3-11 | TaskInput / AgentResult schema 校验 | 1 | Contract 6.2 / 6.3 |
| S3-12 | WorkspaceManager（git worktree）| 1 | Compiler A5.10.1 |
| S3-13 | 集成测试 | 2 | 5 类场景 |

**Deliverable**：

```
agents/compiler_agent/
├── compiler_controller.py
├── compiler_descriptor.py
├── role_profile.yaml
├── prompts/
│   └── compiler_system.md
└── workspace_manager.py

tools/compiler/
├── probe_build_env.py
├── run_compile.py
├── summarize_compile_log.py
├── collect_evidence.py
├── match_known_issues.py
└── ...
```

**Definition of Done**：

- [ ] CompilerController.run() 完整跑通 probe → compile → parse → evidence → analyze 流程
- [ ] 5/12 典型场景的 happy path 能产出有效 diagnosis（即便还没 patch）
- [ ] trace.json + events.jsonl 完整记录
- [ ] Token budget 在 ClineAdapter 强制
- [ ] Raw Data Detector 在 ClineAdapter 入口强制
- [ ] WorkspaceManager 用 git worktree（O(1)）
- [ ] UT ≥ 80% + 集成测试

---

### Sprint 4：Compiler bounded repair loop + verify（2 周）

**目标**：实现 bounded repair loop + patch validate + apply + verify_rebuild 闭环。

**子任务**：

| 任务 ID | 任务名 | 工时（天）| 关联文档 |
|---|---|---|---|
| S4-01 | Tool: `validate_suggestion_patch` | 1 | Compiler A7 |
| S4-02 | `RECOVERABLE_VALIDATION_ERRORS` 枚举 | 0.5 | Compiler A1.2 |
| S4-03 | Tool: `apply_patch`（含 allow_repair） | 1.5 | Compiler A7 |
| S4-04 | `RECOVERABLE_APPLY_ERRORS` 枚举 | 0.5 | Compiler A1.2 |
| S4-05 | Tool: `verify_rebuild` | 1 | Compiler A7 |
| S4-06 | **Bounded repair loop**（A8.3 while 循环）| 2 | Compiler A8.3 |
| S4-07 | `_hash_patch` helper | 0.5 | Compiler A8.4 |
| S4-08 | 第二次 patch 生成时 `previous_attempt_failure` 上下文 | 1 | Compiler A8.3 |
| S4-09 | `_build_success_with_patch_result` helper | 1 | Compiler A8.4 |
| S4-10 | failure_envelope 完整覆盖（含 Team-level 枚举） | 1 | Compiler A11 |
| S4-11 | suggestion_patch.diff 含 metadata（base_commit, verified）| 0.5 | Compiler A5.10 |
| S4-12 | 集成测试（**3 个核心场景**作为 happy path 验证）| 1.5 | 3 场景闭环通过（**v2.1 修订：完整 12 场景测试移到 Sprint 5**）|

**工时合计**：8 天（v2.1 修订后，移除了原来 3 天的完整集成测试）

**Deliverable**：

- bounded repair loop 完整实现
- **3 个核心 happy path 场景**修复闭环跑通（剩余 9 个场景的完整测试留给 Sprint 5）
- suggestion_patch.diff 含 metadata

**Definition of Done**：

- [ ] bounded repair loop while 循环 + hash 比较 + 第二次 patch 生成
- [ ] rebuild 失败绝不重试（在测试中验证）
- [ ] **3 个核心 happy path 场景**的修复闭环跑通
- [ ] UT ≥ 80% + 3 个核心场景集成测试

---

### Sprint 5：Phase 1A 集成 + 12 场景完整测试 + M1 验收（2 周，v2.1 调整）

**目标**：完整 12 场景集成测试 + Demo 演练 + Phase 1A Exit Criteria 验证 + M1 验收。

**子任务**：

| 任务 ID | 任务名 | 工时（天）| 关联文档 |
|---|---|---|---|
| S5-01 | **完整 12 场景集成测试自动化**（v2.1 从 Sprint 4 移入） | 2.5 | Compiler A13 |
| S5-02 | Demo 剧本演练（A15 节）| 1 | Compiler A15 |
| S5-03 | Phase 1A Exit Criteria 验证 | 1 | Compiler A1.3 |
| S5-04 | 内部 dogfooding（5-10 人）启动 | 1.5 | - |
| S5-05 | Bug 修复（从 dogfooding 收集） | 1 | - |
| S5-06 | M1 验收 Demo | 1 | Demo 文档 09 |

**工时合计**：8 天

**Definition of Done（M1 验收 = Phase 1A Exit Criteria）**：

- [ ] **12 种典型场景中自动修复成功率 ≥ 60%**（gate 指标）
- [ ] Detection Success Rate / Evidence Usefulness Rate / Patch Generation Success Rate 收集（观察指标）
- [ ] 真实 Tizen repo 端到端跑通
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] Demo 剧本通过
- [ ] 内部 5-10 人 dogfooding 启动
- [ ] user + 至少 1 个外部 AI 通过 M1 验收

---

## 3. Phase 1B 总览

### 3.0 Phase 1B 启动前置条件（v2.1 新增）

**严格约束**：

- **Phase 1B 主线（Sprint 1B+）不允许在 Phase 1A M1 通过前启动**
- 唯一允许提前的：**Sprint 0B Phase 1B Spike**（约 1 周，仅做概念验证，不写产品代码）
- 这保证 Base 层（Sprint 1）不会因 Benchmark Agent 需求反复变更

**理由**：Benchmark Agent 依赖 Base 层（BaseAgentController / TokenLedger / HandoffBuilder 等），Phase 1A 期间这些组件可能基于 Compiler 实际使用反馈做调整。如果 Phase 1B 提前并行，会导致 Base 层频繁返工。

### 3.1 Phase 1B 目标（继承 Benchmark v5.2-RC2.2 B1.5）

让 Benchmark Agent 在 x86 + Tizen 开发板上做到：

- 至少 3 个 Skill 示例（startup / runtime / memory 三类）
- Skill Manifest runtime-enforced
- 5 种格式报告完整产出（md + html + png + csv + json）
- 与 Compiler Agent 串联（`performance_verify_requested` handoff 闭环）

### 3.2 Phase 1B Sprint 拆分（v2.1 修订）

**v2.1 修订**：Kimi 指出 Phase 1B 多个 Sprint 工时超支 18-25%。接受 **Phase 1B 个别 Sprint 可达 2.5 周**（不增加 Sprint 数量，但单 Sprint 工期可弹性）：

| Sprint | 工期（v2.1 弹性） | 主题 |
|---|---|---|
| **Sprint 0B** | 1 周 | Phase 1B Spike（Skill 框架 / Device Lock） |
| **Sprint 1B** | **2-2.5 周** | Skill Runtime 基础 |
| **Sprint 2B** | **2-2.5 周** | Benchmark Tool 层 + Device Adapter |
| **Sprint 3B** | **2-2.5 周** | Validity Contract + Report Contract |
| **Sprint 4B** | 2 周 | 集成 + Cross-agent handoff |
| **Sprint 5B** | 1 周 | M2 验收 |

**总工期**：10-11.5 周 ≈ **2.5-3 个月**（v2.1 微调，原 v2.0 的 10 周不现实）

**v2.1 工期调整说明**：

- Sprint 1B/2B/3B 任一允许跨到 2.5 周（视实际进度）
- 如果某 Sprint 实际只用 2 周，剩下 0.5 周作为 buffer
- 不允许多个 Sprint 同时超 2 周（避免累积延迟）

---

## 4. Phase 1B Sprint 详细规划

### Sprint 0B：Phase 1B Spike（1 周）

**目标**：验证 Skill 框架 + Device Lock 关键假设。

**子任务**：

| 任务 | 工时（天）|
|---|---|
| Skill Manifest schema 验证（用样例 yaml）| 0.5 |
| Skill Runtime sandbox guardrails 验证（受控 API + 静态扫描）| 1.5 |
| DeviceAdapter sdb 连接验证（真实 Tizen 开发板）| 1 |
| DeviceLockManager PID file + 心跳验证（含进程 crash 抢占）| 1 |
| sdb 断开自动释放 lock 验证 | 0.5 |
| 三平台示例 Skill（cpu_microbench / video_player_startup）跑通 | 1.5 |

**DoD**：6/6 验证 PASS，否则同 Sprint 0 处理。

---

### Sprint 1B：Skill Runtime 基础（2 周）

**子任务**：

| 任务 | 工时（天）| 关联文档 |
|---|---|---|
| `SkillRegistry`（加载 + 注册）| 1 | 文档 07 §2 |
| `SkillManifestValidator`（runtime enforce）| 1.5 | 文档 07 §2.4 |
| `SkillRuntime`（setup/run/teardown 调度）| 2 | 文档 07 §3 |
| `SkillContext`（受控 API 实现）| 2 | 文档 07 §4 |
| `SkillCardGenerator`（自动生成 LLM 友好摘要）| 0.5 | 文档 07 §2.5 |
| Guardrails 实施（allowlist / denylist / static scan）| 2 | 文档 07 §5 |
| 3 个示例 Skill | 1 | 文档 07 §6 |

**DoD**：

- [ ] 3 个示例 Skill 在 x86 + Tizen device 上跑通
- [ ] Manifest violation 测试通过
- [ ] UT ≥ 80%

---

### Sprint 2B：Benchmark Tool 层 + Device Adapter（2 周）

**子任务**：

| 任务 | 工时（天）| 关联文档 |
|---|---|---|
| Tool: `check_benchmark_env`（含 device health）| 1 | Benchmark B7 |
| Tool: `collect_environment_snapshot` | 1 | Benchmark B7 |
| Tool: `run_benchmark_skill_set`（调度）| 2 | Benchmark B7 |
| `HostShellAdapter` | 0.5 | Contract 8 |
| `DeviceAdapter (sdb)` | 1.5 | Contract 8 |
| `DeviceAdapter (ssh)` | 1（**v2.1 标 Phase 1B 可选**，优先保证 sdb；如时间不足推到 Sprint 4B） | Contract 8 |
| **`DeviceLockManager`**（PID + 心跳 + sdb 监控）| 2 | Benchmark B8.4 |
| 单元测试 | 1 | UT ≥ 80% |

**DoD**：

- [ ] Skill 在 sdb + ssh 两个 backend 都能跑
- [ ] DeviceLock PID file + 30s 心跳 + 120s stale 抢占 + sdb 断开释放都有测试
- [ ] UT ≥ 80%

---

### Sprint 3B：Validity Contract + Report Contract（2 周）

**子任务**：

| 任务 | 工时（天）| 关联文档 |
|---|---|---|
| Tool: `validate_result`（含 requires_rerun）| 1.5 | Benchmark B5.6 |
| Tool: `compare_benchmark`（含 suggests_rerun 精确化）| 1.5 | Benchmark B5.3 |
| Tool: `summarize_benchmark_result` | 1 | Benchmark B7 |
| Tool: `render_benchmark_chart`（matplotlib）| 1 | Benchmark B7 |
| Tool: `render_benchmark_report`（**v2.1 拆分**：Sprint 3B 完成 md+html+csv 3 种格式 2 天；png/json 在 Sprint 4B 补完）| 2 | Benchmark B6.3 |
| `BenchmarkController` 主框架 | 2 | Benchmark B8.2 |
| **rerun 决策位置**（Tool 层，cline 调用之前）| 1 | Benchmark B5.2.1 / B8.2 |

**DoD**：

- [ ] 5 种报告完整产出
- [ ] HTML 验证 static-only 约束
- [ ] rerun 决策完全由 Tool 层做出
- [ ] suggests_rerun 同一 metric breached + variance_flag 逻辑正确
- [ ] UT ≥ 80%

---

### Sprint 4B：集成 + Cross-agent handoff（2 周）

**子任务**：

| 任务 | 工时（天）|
|---|---|
| ClineAdapter `analyze_benchmark`（narrative only）| 1.5 |
| Prompt: `benchmark_system.md`（B12 模板）| 1 |
| HandoffBuilder 支持 `disambiguator = skill:{id}` | 1 |
| 与 Compiler Agent 的 cross-agent handoff 联动测试 | 2 |
| 12+ 种集成测试场景（Benchmark B11） | 3 |
| Bug 修复 | 1 |

**DoD**：

- [ ] Benchmark 能接收 Compiler `performance_verify_requested` handoff
- [ ] multi-Skill regression 产出 disambiguated handoff
- [ ] 12 种典型场景中 8 种通过
- [ ] UT ≥ 80%

---

### Sprint 5B：M2 验收（1 周）

**子任务**：

| 任务 | 工时（天）|
|---|---|
| Demo 剧本演练（B13 节）| 1 |
| Phase 1B Exit Criteria 验证 | 1 |
| 内部 dogfooding（含 Phase 1A 的 5-10 人）| 2 |
| Bug 修复 | 1 |
| M2 验收 Demo | 1 |

**Definition of Done（M2 验收 = Phase 1B Exit Criteria）**：

- [ ] 至少 3 个 Skill 示例（startup / runtime / memory 三类）
- [ ] 5 种格式报告完整
- [ ] device lock 防止抢板子
- [ ] 配合 Compiler Agent 完成 cross-agent handoff
- [ ] Demo 剧本通过
- [ ] user + 至少 1 个外部 AI 通过 M2 验收

---

## 5. Phase 1.5 概要规划

### 5.1 Phase 1.5 目标

- 100 人内部推广（5-10 → 100）
- 产品化（监控 / 告警 / 运维 / SLA）
- Memory Infrastructure（Known Issues → 自动学习）
- gbs / make 构建支持
- Skill 容器化沙箱（warning → block）
- Chromium-scale CNEI（scip-clang 预索引）

### 5.2 Phase 1.5 工期估算

**3-4 个月**（详细 Sprint 拆分留到 Phase 1B 完成后再做，避免过早规划）

### 5.3 Phase 1.5 Sprint 主题（粗略）

| Sprint 主题 | 预估时长 |
|---|---|
| gbs / make 解析与构建集成 | 3-4 周 |
| Memory Infrastructure（向量库 + 检索）| 4-5 周 |
| Chromium-scale CNEI（scip-clang + sharding）| 3-4 周 |
| Skill 容器化（block 模式 + sandbox 升级）| 3-4 周 |
| Cross-host device pool | 2-3 周 |
| 监控 / 告警 / 文档站 | 3-4 周 |
| 100 人滚动推广 | 4-6 周 |

**总计**：22-30 周 ≈ 5-7 个月（含缓冲），目标 3-4 个月需要并行多个工作流。

---

## 6. 跨 Phase 关键里程碑

| 里程碑 | 含义 | 标准 |
|---|---|---|
| **M0** | Spike Gate 通过 | Phase 1A Sprint 0 PASS |
| **M1** | Phase 1A Demo + Exit Criteria | 12 场景 ≥ 60% / Tizen repo 跑通 |
| **M1B** | Phase 1B Spike 通过 | Phase 1B Sprint 0B PASS |
| **M2** | Phase 1B Demo + Exit Criteria | 3 Skill / 5 格式 / cross-agent |
| **M2.5** | Phase 1A + 1B 整合 | Compiler → Benchmark 联动稳定 |
| **M3** | Phase 1.5 100 人推广就绪 | 监控 + SLA + 文档 |

---

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|---|---|---|---|
| Sprint 0 spike 失败（clangd 不可用） | 中 | 高 | 提前选定 Tizen repo；准备 fallback（推迟 clangd 到 1.5）|
| Known Issues 初始数据准备延迟 | 高 | 中 | Sprint 0 期间就启动团队协调 |
| Tizen 开发板供给不足 | 中 | 中 | Phase 1B 前确认至少 2 块开发板可用 |
| ClineSR 准确率低于预期 | 中 | 高 | A1.3 分层观察指标可定位瓶颈 |
| 12 种场景 < 60% 自动修复 | 中 | 高 | Sprint 5 留 buffer；M1 验收可降级到 50% + 改进计划 |
| dev_memory 累积膨胀，影响 review | 低 | 低 | 每 Sprint 末尾 archive |
| **Codex 复杂逻辑实现质量波动**（v2.1 新增）| 中 | 高 | bounded repair loop 等复杂逻辑预留 1 轮 review + 重构时间；复杂任务拆分为更小单元；外部 AI review 必查 |
| **Codex 生成代码与设计文档偏差**（v2.1 新增）| 中 | 中 | review_packet 必含"与设计文档对应章节"字段；scripts/check_gate.sh 含 schema validation；外部 AI review 抽查"代码意图 vs 设计文档"一致性 |
| **CNEI Sprint 2b 工作量爆发**（v2.1 新增，从 Sprint 2 拆分引申）| 中 | 高 | Sprint 2b 留 PkgConfigCollector 推迟选项；Known Issues 数据准入前置到 Sprint 0 团队协调；clangd 启动失败时降级方案 ready |

---

## 8. 跟 v1.1 / v2.0 的主要差异

| 维度 | v1.1 | v2.0 | v2.1 |
|---|---|---|---|
| Phase 切分 | Phase 1 整体 | Phase 1A / 1B 拆分 | Phase 1A / 1B / 1.5 完整 |
| Sprint 粒度 | 月级 | 2 周粒度 | **Phase 1A 2 周固定；Phase 1B 弹性 2-2.5 周** |
| Spike Gate | 无 | Sprint 0 强制 | 保留 |
| Sprint 2 拆分 | 无 | 单 Sprint | **拆为 2a + 2b（v2.1 修订）** |
| Sprint 4 集成测试 | - | 含 12 场景 | **移到 Sprint 5（v2.1 修订）** |
| dev_memory 体系 | 简单 | 完整 | 同 v2.0 + commit hash + coverage 路径 |
| Merge gate | 无机器 gate | 同 v1.1 | **scripts/check_gate.sh 强制（v2.1 新增）** |
| Phase 1B 启动前置 | 无 | 隐含 | **M1 通过前不允许（v2.1 新增）** |
| 风险表条目 | 4 条 | 6 条 | **9 条（v2.1 新增 Codex 质量 / 偏差 / Sprint 2b 风险）** |
| 100 人推广 | Phase 1 末尾 | Phase 1.5 专门阶段 | 同 v2.0 |
| Phase 1A 总工期 | - | 10-12 周 | **12-14 周（更现实）** |
| Phase 1B 总工期 | - | 10 周 | **10-11.5 周（弹性）** |

---

## 9. 给 Codex 的最终注意事项

### 9.1 永远做的事

- 每个 Sprint 末尾更新 dev_memory（4 个文件 + handoff_summary）
- 每个可独立 review 的变更生成 review_packet.md
- 单元测试覆盖率 ≥ 80%（gate）
- 遵守 Team Contract v0.7.3 + Cognitive Boundary
- branch + git push 到 main（不走 PR）

### 9.2 绝对不做的事

- ❌ raw log 直接进 LLM（除 EvidencePacket excerpt）
- ❌ 让 ClineSR 控制 rerun（Benchmark）/ patch 数量（Compiler）
- ❌ 修改用户主代码（Phase 1A/1B verify_only）
- ❌ `cp -r` 复制大 workspace（用 git worktree）
- ❌ 跳过 Spike Gate 直接进 Sprint 1
- ❌ Sprint 末尾不更新 dev_memory
- ❌ 单元测试覆盖率 < 80% 就提交 review_packet

---

**文档结束**
