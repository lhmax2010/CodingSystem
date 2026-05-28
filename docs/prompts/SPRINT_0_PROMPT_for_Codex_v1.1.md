# Sprint 0 Spike Gate 启动 Prompt v1.1（Phase 1A）

**版本**：v1.1
**对应阶段**：Phase 1A Sprint 0（Spike Gate，2 周内完成）
**前置条件**：已读 `MAIN_PROMPT_for_Codex_v2.1.md` § 1-2

**v1.1 修订摘要**（针对 ChatGPT + Kimi v1 review）：

- ChatGPT 抓到：「8 项 / 9 项 / 10 个子任务」口径混乱 — 统一为 "9 个任务 = 1 prerequisite (S0-01) + 8 core gates (S0-02 ~ S0-09)"
- Kimi 抓到：S0-03 合并后工时 3 天，但 v2.1 中是 1.5+2=3.5 天 — 统一为 3.5 天
- Kimi 抓到：S0-09 stale 在 Sprint 0 prompt 但不在 v2.1.1 Sprint 0 — v2.1.1 已把 S0-09 加入（确认）
- Kimi 抓到：Sprint 0 总工时 10/10.5/11 不一致 — 统一为 11 天，明确接受超 10 天 1 天的小延期
**后续阶段**：Sprint 0 PASS 后启动 Sprint 1（Base 层）

---

## 0. 这个 prompt 的目的

Codex，你**现在正式开始 Phase 1A Sprint 0 Spike Gate**。

Sprint 0 是整个 Coding System 实施的**第一个 gate**，目的是验证关键技术假设是否成立。

**Sprint 0 任务结构**（v1.1 统一口径）：

```
Sprint 0 包含 9 个任务: S0-01 ~ S0-09

其中:
- S0-01 是"前置选择任务"（选定 Tizen repo，不是技术 gate）
- S0-02 ~ S0-09 是 8 个核心技术 gate

进入 Sprint 1 的条件:
- S0-01 完成 + S0-02 ~ S0-09 共 8 个核心 gate 全部 PASS
- 任何核心 gate PARTIAL/FAIL → 必须 ADR 决策（A 重做 / B 降目标 / C 推 1.5）
- 3+ 个 gate FAIL → Stop the line
```

**关键判断**：Sprint 0 不写产品代码，只做 spike。如果某项假设 PARTIAL/FAIL，比起在 Sprint 3/4 才发现要好得多。

---

## 1. Sprint 0 时间盒（v1.1 统一工时口径）

- **目标工期**：2 周（10 工作日）软上限
- **总工时**：约 **11 天**（v1.1 修订：v2.1.1 中明确为 0.5+0.5+3.5+2+1+1+1+1.5+1 = 11 天）
- **超时处理**：
  - **超出 1 天**（2 周 + 1 天）：可接受，不阻塞 Sprint 1 启动
  - **超出 2 天**（11.5+ 天）：必须做拆分决策（非核心 spike 推 Sprint 1 启动 Day 1，详见 §2.3 Sprint 0 超时处理规则）
  - **超出 3 天+**：Stop the line，必须 ADR

---

## 2. Sprint 0 任务清单（必读）

详见《开发计划 v2.1.1》§Sprint 0。这里给出执行版：

**任务结构**：S0-01 是前置选择 + S0-02 ~ S0-09 是 8 个核心 gate。

### S0-01: 选定 Tizen 真实 repo（0.5 天，**前置选择，非 gate**）

**目标**：选定 1 个 cmake/ninja 的 Tizen project 作为 Phase 1A 验证基线。

**Acceptance**：

- [ ] 是 cmake + ninja
- [ ] < 100 万行（用 `tokei` / `cloc` 估算）
- [ ] 能在 x86 工作站正常 clone + build
- [ ] 有历史 build 失败的 commit（用于 S0-04 提供错误样本）
- [ ] 至少 3 个开发者熟悉这个 repo（便于后续 dogfooding）

**Deliverable**：`spike_reports/spike_01_repo_selection.md`

---

### S0-02: compile_commands.json 生成验证（0.5 天，**核心 gate**）

**目标**：验证 `CMAKE_EXPORT_COMPILE_COMMANDS=ON` 能稳定生成 compile_commands.json。

**Acceptance**：

- [ ] 生成的 json 覆盖 100% source files
- [ ] include paths / defines 完整
- [ ] cross-compile（如有 sysroot）的 wrapper 正确处理

**Deliverable**：`spike_reports/spike_02_compile_commands.md` + 一份 sample compile_commands.json 摘录（脱敏）

---

### S0-03: clangd 启动 + 索引 + 准确率（**3.5 天，核心 gate**，v1.1 工时修正）

**目标**：验证 clangd 作为 CNEI preferred backend 可用。

**Acceptance**（任一 FAIL 即 PARTIAL）：

- [ ] clangd 启动成功（5 min 内）
- [ ] 索引完成（不超过 5 min for 100 万行）
- [ ] 内存峰值 < 4GB
- [ ] `textDocument/definition` 抽样 50 个 symbol，准确率 ≥ 90%
- [ ] `textDocument/references` 抽样 30 个 symbol，准确率 ≥ 85%
- [ ] **stale 检测**：人工修改 CMakeLists.txt 后不跑 cmake，CNEI 应 detect mtime stale

**人工抽样方法**：

```bash
# 1. 随机选 50 个 symbol（用 ripgrep 找）
rg --type=cpp -o '\b[A-Z][a-zA-Z]+\b' --no-line-number src/ | sort -u | shuf -n 50

# 2. 对每个 symbol，记录 clangd 的 definition 返回值
# 3. 人工 grep 确认 ground truth
# 4. 算准确率
```

**Deliverable**：`spike_reports/spike_03_clangd.md` 含：

- 实际索引时间 / 内存峰值
- definition 50 sample 的 ground truth vs clangd 结果对比表
- references 30 sample 的同上
- stale 检测验证

---

### S0-04: LogErrorParser 覆盖度（2 天，**核心 gate**）

**目标**：验证 LogErrorParser 能解析 Tizen 常见的 5 类 error_type。

**Acceptance**：

- [ ] 收集 Tizen 历史 build 失败日志样本 50 份（CI fail / 本地 fail 都行）
- [ ] 5 类 error_type 解析准确率：
  - `undefined_reference`: ≥ 80%
  - `undefined_symbol`: ≥ 80%
  - `cannot_find_header`: ≥ 80%
  - `type_mismatch`: ≥ 70%
  - `template_error`: ≥ 70%（template 错误最难）
- [ ] 不在 5 类内的错误不会被错误归类（false positive ≤ 10%）

**Deliverable**：`spike_reports/spike_04_log_parser.md` 含覆盖率统计表

---

### S0-05: EvidencePacket 生成性能（1 天，**核心 gate**）

**目标**：验证 EvidencePacket 生成时间 + token 估算合理。

**Acceptance**：

- [ ] 单次 EvidencePacket 生成时间 < 2s（不含 clangd cold start）
- [ ] token 估算 ≤ 4000（CNEIConfig 默认值）
- [ ] facts / negative_facts / log_excerpt 数量合理

**Deliverable**：`spike_reports/spike_05_evidence_packet.md`

---

### S0-06: RawDataDetector 验证（1 天，**核心 gate**）

**目标**：验证 RawDataDetector 能正确放行 EvidencePacket excerpt + 拦截 raw log。

**Acceptance**：

- [ ] 构造含 5000 字符 raw compile.log 的 prompt → 检测 raw_log，抛 RawDataLeakageError
- [ ] 构造含 < 5000 字符 + 符合 5.6.2 约束的 EvidencePacket.log_excerpt 的 prompt → 放行
- [ ] 构造多个 small excerpt 试图绕过 size 约束 → 拦截（global size check）

**Deliverable**：`spike_reports/spike_06_raw_data_detector.md`

---

### S0-07: Known Issue matcher（1 天，**核心 gate**）

**目标**：验证 KnownIssueMatcher regex 设计。

**Acceptance**：

- [ ] 准备 5 份样例 Known Issue（governance schema）
- [ ] 构造 5 个命中场景 → 准确率 100%
- [ ] 构造 5 个不命中场景 → false positive 0%

**Deliverable**：`spike_reports/spike_07_known_issue_matcher.md`

---

### S0-08: End-to-end dry run（1.5 天，**核心 gate**）

**目标**：完整跑通 compile fail → log parse → evidence collect → cline analyze（不 apply patch）。

**Acceptance**：

- [ ] 故意构造编译失败
- [ ] CNEI 产出有效 EvidencePacket
- [ ] ClineAdapter 调用通过 RawDataDetector
- [ ] trace.json + events.jsonl 完整
- [ ] Token budget 不超 25000

**Deliverable**：`spike_reports/spike_08_e2e_dry_run.md` + 完整 trace.json sample

---

### S0-09: stale 检测 + confidence 降级（1 天，**核心 gate**）

**目标**：验证 v0.3.3 stale 检测和 confidence 降级。

**Acceptance**：

- [ ] 构造 stale 场景（CMakeLists.txt mtime > compile_commands.json mtime）
- [ ] CNEI 设 `clangd_stale=true`
- [ ] 所有 clangd 来源的 facts confidence=medium + confidence_modifier="stale_compile_commands"
- [ ] Evidence Packet 顶层 `clangd_stale=true`

**Deliverable**：`spike_reports/spike_09_stale_detection.md`

---

## 3. 每个 spike report 模板

```markdown
# Spike 0X: <验证项名称>

## 假设
（这次要验证的假设是什么？）

## 执行
- 命令: `...`
- 配置: ...
- 数据集: ... （文件数 / 大小）

## 数据
（实际观察到的数字、表格、错误日志、抽样结果）

## 结论
- ✅ PASS / ⚠️ PARTIAL / ❌ FAIL
- 通过/失败原因

## 影响
（对 Phase 1A 主流程实施的影响）

## 后续动作
（如果失败，下一步是什么）

## Artifact 路径
- 完整数据 / 日志 / sample：`spike_reports/spike_0X_data/`
```

---

## 4. Sprint 0 Gate 决策（核心，v1.1 口径统一）

**进入 Sprint 1 的条件**：

- S0-01 完成（前置选择，无 PASS/FAIL 概念）
- **S0-02 ~ S0-09 共 8 个核心 gate 全部 PASS**

**单个核心 gate PARTIAL 处理**：

- 选项 A（重做）：调整方案后重做 spike（如改 clangd 配置 / extended timeout）
- 选项 B（降目标）：调整 RC2.2 文档的 Exit Criteria（如 12 场景 60% → 50%）
- 选项 C（推迟）：推迟该能力到 Phase 1.5（如 clangd 完全不行，Phase 1A 用 tree-sitter + ctags）

每个 PARTIAL 必须产出 ADR：`docs/dev_memory/phase_1a/sprint_0_spike/adrs/adr_00X_xxx.md`

**3+ 个核心 gate FAIL → Stop the line**：

- 整体方案重评估
- 可能需要 RC3 或推迟 Phase 1A
- 不要硬冲

**S0-01 处理方式不同**：

- S0-01 是前置选择，没有 PASS/FAIL
- 但如果**找不到合适的 Tizen repo**（不满足"cmake/ninja + < 100 万行 + 可 build + 有历史 build 失败 commit"），整个 Sprint 0 无法启动
- 这种情况下也是 Stop the line

---

## 5. Sprint 0 关键禁令

### 5.1 不要做的事

- ❌ **不要写产品代码**（不碰 `agents/compiler_agent/`）
- ❌ **不要跳过 spike**（即使觉得"显然能 PASS"）
- ❌ **不要静默降低门槛**（如 60% → 不报告就改 50%）
- ❌ **不要开始 Phase 1B 工作**

### 5.2 PARTIAL/FAIL 处理

- ❌ **不要自己决定 A/B/C 选项**
- ✅ **emit comment 给 user，说明数据 + 推荐选项 + 理由**
- ✅ **等 user 决策后产出 ADR**

---

## 6. Sprint 0 日常报告

**每天给 user 一次 progress message**，格式参考 MAIN_PROMPT §5.3：

```
Sprint 0 Day N progress：

[已完成]
- S0-01 ✅ ...
- S0-02 ✅ ...

[进行中]
- S0-03 🔄 ...

[阻塞 / 决策]
- [描述]

预计今日完成: ...
预计明日做: ...
```

---

## 7. Sprint 0 结束 deliverable

最后一天必须产出：

```
docs/dev_memory/phase_1a/sprint_0_spike/
├── spike_summary.md             # 汇总 9 项验证（必读：v2.1.1 §1.2.1）
├── spike_reports/
│   ├── spike_01_repo_selection.md
│   ├── spike_02_compile_commands.md
│   ├── spike_03_clangd.md
│   ├── spike_04_log_parser.md
│   ├── spike_05_evidence_packet.md
│   ├── spike_06_raw_data_detector.md
│   ├── spike_07_known_issue_matcher.md
│   ├── spike_08_e2e_dry_run.md
│   └── spike_09_stale_detection.md
├── spike_reports_data/           # 完整原始数据 + sample
│   └── ...
├── adrs/                         # 如有 PARTIAL/FAIL
│   └── adr_001_xxx.md
└── review_packets/
    └── sprint_0_review_packet.md
```

### spike_summary.md 模板

```markdown
# Phase 1A Sprint 0 Spike Summary

**Sprint 工期**: YYYY-MM-DD ~ YYYY-MM-DD (X working days)
**总结**: [PASS / PARTIAL / FAIL]

## 9 项 spike 结果（v1.1：1 prerequisite + 8 core gates）

| ID | 名称 | 类型 | 结果 | 备注 |
|---|---|---|---|---|
| S0-01 | repo selection | Prerequisite | ✅ 完成 | tizen-repo-foo, 847k LOC |
| S0-02 | compile_commands.json | Core Gate | ✅/⚠️/❌ | 100% coverage |
| S0-03 | clangd 启动+索引+准确率 | Core Gate | ✅/⚠️/❌ | [详见 report] |
| S0-04 | log parser | Core Gate | ✅/⚠️/❌ | ... |
| S0-05 | evidence packet | Core Gate | ✅/⚠️/❌ | ... |
| S0-06 | raw data detector | Core Gate | ✅/⚠️/❌ | ... |
| S0-07 | known issue matcher | Core Gate | ✅/⚠️/❌ | ... |
| S0-08 | e2e dry run | Core Gate | ✅/⚠️/❌ | ... |
| S0-09 | stale detection | Core Gate | ✅/⚠️/❌ | ... |

**Gate 总结**: 8 core gates 中 X PASS / Y PARTIAL / Z FAIL

## 关键发现

[Sprint 0 期间发现的、对 Phase 1A 主流程有影响的事]

## ADR 记录

[如有 PARTIAL/FAIL]

## 推荐下一步

- [ ] 进入 Sprint 1 (Base 层)
- [ ] 等待 user 决策 [如 PARTIAL 情况]
- [ ] Stop the line [如 FAIL 严重]
```

---

## 8. 进入 Sprint 1 的标志（v1.1 口径统一）

- S0-01 完成
- **S0-02 ~ S0-09 共 8 个核心 gate 全部 PASS**（或 PARTIAL 已 ADR 决策完成）
- spike_summary.md + review_packet 提交
- user + 至少 1 个外部 AI（Claude / ChatGPT / Kimi）review 通过
- **user 明确说"进入 Sprint 1"**

**不要自己决定**。等明确指令再继续。

---

**Sprint 0 启动，开始 S0-01。**
