# Sprint 1+ 常规开发 Prompt v1.2（Phase 1A/1B 主流程）

**版本**：v1.2
**对应阶段**：Phase 1A Sprint 1（Base 层）→ Phase 1B Sprint 5B（M2 验收）
**前置条件**：Sprint 0 PASS + 已读 `MAIN_PROMPT_for_Codex_v2.2.md` § 全部
**Phase 1B 适用**：Phase 1A M1 通过后，本 prompt 仍适用（替换 Sprint 编号即可）

**v1.2 修订摘要**（针对 ChatGPT v1.1 review）：

- ChatGPT 抓到：Sprint 整体 review_packet 模板"check_gate.sh 9 项全 PASS"措辞错（advisory 不应算 PASS） — 精化为 "8 blocking gates PASS + advisory check completed"
- 同步开发计划版本号到 v2.1.2

**v1.1 修订摘要**（针对 ChatGPT + Kimi v1 review）：

- ChatGPT 抓到：branch 策略 task-X vs main 不一致 — 统一为 sprint-N-main 默认
- ChatGPT 抓到：check_gate.sh 第 9 项 optional vs blocking 矛盾 — 明确 8 blocking + 1 advisory
- Kimi 抓到：扩展点表 IndexBackend 描述与 MAIN_PROMPT 不一致 — 统一为完整版
- ChatGPT 抓到：结尾硬编码 "Sprint 1 启动 S1-01" 不适合 Phase 1B 复用 — 改模板化
- Kimi 抓到：Sprint 2b "v2.1.2 §自动扩容触发" 表述需精确 — 引用 v2.1.2 实际章节

---

## 0. 这个 prompt 的目的

Codex，Sprint 0 已经 PASS，**现在开始 Phase 1A 主流程实施**。

跟 Sprint 0 不同：

| 维度 | Sprint 0 | Sprint 1+ |
|---|---|---|
| 输出 | spike_report | 产品代码 |
| 验收门槛 | 8 项 PASS | UT ≥ 80% + 集成测试 + check_gate.sh |
| 失败处理 | ADR 决策方向 | bug fix + 重新 review |
| 节奏 | 1-2 周 spike | 2 周 sprint × 6 个 |

---

## 1. Phase 1A Sprint 列表（参考 v2.1.2）

| Sprint | 工期 | 主题 |
|---|---|---|
| **Sprint 1** | 2 周 | Base 层（10 个共享组件）|
| **Sprint 2a** | 2 周 | CNEI Backend Indexers |
| **Sprint 2b** | 2 周 | CNEI 核心层 + EvidenceCollector |
| **Sprint 3** | 2 周 | Compiler 主流程（probe → analyze）|
| **Sprint 4** | 2 周 | Compiler bounded repair loop + verify |
| **Sprint 5** | 2 周 | 集成 + 12 场景测试 + M1 验收 |

每个 Sprint 详细任务清单 见 `05_Phased_Development_Plan_v2.1.2.md`。

---

## 2. Sprint 启动 checklist

每个 Sprint Day 1 必做：

```bash
# 1. 读 v2.1.2 对应 Sprint 章节
$ cat 05_Phased_Development_Plan_v2.1.2.md | grep -A 100 "### Sprint N"

# 2. 确认前置依赖就绪
#    Phase 1A:
#    - Sprint 2a 需要 Sprint 1 Base 层 ready
#    - Sprint 2b 需要 Sprint 2a Backend Indexers ready
#    - Sprint 3 需要 Sprint 2b CNEI ready
#    Phase 1B:
#    - Sprint 1B 需要 Phase 1A M1 通过 + Sprint 0B Spike PASS
#    - Sprint 2B 需要 Sprint 1B Skill Runtime ready
#    - ...

# 3. 创建 sprint 主 branch（v1.1：统一为 sprint-N-main，与 MAIN_PROMPT §3.1 一致）
$ git checkout main && git pull
$ git checkout -b codex/sprint-N-main

# 4. 创建 sprint 目录
$ mkdir -p docs/dev_memory/phase_1X/sprint_N_{xxx}/
$ mkdir -p docs/dev_memory/phase_1X/sprint_N_{xxx}/review_packets/

# 5. 在 sprint 目录创建 plan.md，列出本 Sprint 子任务 + 预估工时
```

**Branch 策略说明**（v1.1 与 MAIN_PROMPT 统一）：

- **默认**：一个 sprint-N-main branch，每个子任务独立 commit + review_packet
- **风险隔离任务**：用 sprint-N-task-X 独立 branch（如某子任务可能需要实验性大改），验证后再 merge 回 sprint-N-main
- 不要每个子任务都建 task-X branch（merge 成本太高）

---

## 3. Sprint 内开发节奏（推荐）

### 3.1 一日工作流

```
Morning（30 min）:
- 看 yesterday handoff（如有）
- 决定今天目标（1-2 个子任务）
- 看相关文档章节

Mid-day:
- 写代码 + 单元测试
- 每完成 1 个子任务 → 跑 check_gate.sh
- 不通过不要走下一个

Afternoon（30 min）:
- 给 user 写 daily progress（§3.4）
- 准备明天计划
```

### 3.2 子任务级 review_packet

**每个子任务（如 S1-03 TokenLedger）都产生一个独立 review_packet**：

```
docs/dev_memory/phase_1a/sprint_1_base_layer/review_packets/
├── S1-01_BaseAgentController.md
├── S1-02_BudgetTracker.md
├── S1-03_TokenLedger.md          # ← 本子任务
├── ...
└── sprint_1_review_packet.md     # Sprint 整体 review（末尾）
```

每个子任务 review_packet 用 MAIN_PROMPT §3.3 模板。

### 3.3 Sprint 末尾整体 review_packet

Sprint 最后一天产出 `sprint_N_review_packet.md`，汇总：

```markdown
# Sprint N Review Packet (整体)

**Sprint**: N (xxx)
**工期**: YYYY-MM-DD ~ YYYY-MM-DD (X working days)

## 1. Sprint 整体结果

- [ ] 所有子任务 PASS
- [ ] 集成测试通过
- [ ] UT 覆盖率 ≥ 80%
- [ ] check_gate.sh: **8 blocking gates PASS**
- [ ] check_gate.sh: advisory doc consistency check completed
- [ ] advisory warnings 在 §6 known risks 中列出（如有）

## 2. 子任务汇总

| ID | 名称 | 工时（计划）| 工时（实际）| 状态 |
|---|---|---|---|---|
| S1-01 | BaseAgentController | 1 | 1.2 | ✅ |
| S1-02 | BudgetTracker | 1 | 0.8 | ✅ |
| ... |

## 3. 关键决策

[本 Sprint 期间做的关键设计决策，如有]

## 4. 与原计划的 deviation

[如某子任务工时超时 / 范围调整 / 推迟，必须列出]

## 5. 集成测试结果

[end-to-end 集成测试 sample]

## 6. 已知 risk / blocker

## 7. 下 Sprint 准备

- 前置依赖：是否准备好？
- 风险点：可能阻塞下 Sprint 的事
```

### 3.4 Daily progress 格式

```
Sprint N Day M progress:

[已完成]
- S1-01 ✅ BaseAgentController (代码 + UT)
- S1-02 ✅ BudgetTracker (代码 + UT)

[进行中]
- S1-03 🔄 TokenLedger (代码完成，UT 进行中, ~80%)

[阻塞 / 决策]
- 发现 Contract 5.5.2 中 TokenLedger.record() 描述与 v0.7.2 Appendix A schema 不一致
  → emit_failure 应该 record token 还是不 record？
  请 user 确认（建议: 不 record，因为 failure 时 task abort，token 已计入 stage 内）

预计今日完成: S1-03 全部
预计明日做: S1-04 ArtifactManager
```

---

## 4. Sprint 关键约束（不可妥协）

### 4.1 进入 Sprint 1 前已强调的（重申）

1. **Cognitive Boundary**：rerun / retry / 计数 → Tool 层，不交 LLM
2. **Raw Log 硬约束**：full raw log 绝不进 LLM prompt
3. **不修改用户主代码**：git worktree 创建 isolated workspace
4. **Secret Redaction**：ArtifactManager 自动 redact
5. **Token Budget**：每个 stage 前 check
6. **check_gate.sh**：merge 前必跑（v1.1 修订：**8 blocking gates + 1 advisory check**，任一 blocking FAIL 不 merge；advisory warning 必须在 review_packet §6 列出但不 block merge；详见 MAIN_PROMPT §3.2）

### 4.2 Sprint 特定约束

| Sprint | 特定约束 |
|---|---|
| **Sprint 1** | Base 层接口必须稳定，因为后续所有 Agent 用；接口签名不能任意变（变更需要 review_packet 强调） |
| **Sprint 2a** | Backend Indexers 接口必须支持 plugin-style（Phase 1.5 加 scip-clang）|
| **Sprint 2b** | clangd B++ 5-Gate 必须完整实现；stale 检测不能省（Spike 0 已验证）；如 Sprint 0 PARTIAL 触发自动扩容（v2.1.2 §Sprint 2b 弹性触发条件）|
| **Sprint 3** | Compiler Controller `workspace_snapshot.type != "git_repo_path"` 必须 emit `contract_violation`（RC2.2 修订）|
| **Sprint 4** | bounded repair loop 严格 2 次 patch generation 上限 + 1 次 apply repair + rebuild 失败绝不重试 |
| **Sprint 5** | 完整 12 场景测试自动化；M1 验收前 Demo 演练至少 3 次 |

### 4.3 扩展点约束（来自 Phase 1.5 v0.1 §5）

实施时必须为 Phase 1.5 预留扩展点：

| Phase 1A 实施 | 必须预留 |
|---|---|
| `WorkspaceManager` | 支持 `local_path` 类型预留（Phase 1.5 加 gbs/non-git） |
| `select_backend_for_cpp()` Gate 4 | schema 可扩 gbs/make |
| `IndexBackend` | 抽象接口（Phase 1A 是 `ClangdBackend`（live），Phase 1.5 加 `ScipClangBackend`（precomputed） + `HybridBackend`） |
| **`BenchmarkController` rerun loop** | Tool 层产出 rerun 信号（validate_result / compare_benchmark），Controller 消费；绝不把 rerun 决策硬编码在 ClineAdapter |
| `trace.json` schema | 向后兼容（Memory Infrastructure 依赖） |
| `EvidencePacket` schema | 向后兼容 |

不要为 Phase 2+ 做过度设计，但**不要写死阻碍 Phase 1.5 演化**。

---

## 5. Sprint 间 handoff

Sprint N 末尾产出 `handoff_summary.md`，作为 Sprint N+1 的输入：

```markdown
# Sprint N → Sprint N+1 Handoff

**From Sprint**: N (xxx)
**To Sprint**: N+1 (yyy)
**Handoff Date**: YYYY-MM-DD

## 1. Sprint N 交付的能力

- [组件 1]: 接口 / 限制 / 已知问题
- [组件 2]: ...

## 2. Sprint N+1 需要用的内容

- [API 1]: 来自 Sprint N 的 [模块]
- [API 2]: ...

## 3. 已知 limitation（Sprint N+1 不要踩坑）

[如 Sprint 2b clangd 启动慢于预期，Sprint 3 调用时要预留更长 timeout]

## 4. 推荐 Sprint N+1 Day 1 任务

[基于 N 的实际进度调整]
```

---

## 6. Sprint 失败处理

**如果 Sprint 某子任务 FAIL**：

1. 不要硬冲（不要"明天再写就追上"）
2. 在 daily progress 明确说：「S2b-07 EvidenceCollector 实际比预估难 2x，可能阻塞 Sprint 2b」
3. 给 user 选项：
   - A：Sprint 2b 扩到 2.5 周（v2.1.2 §自动扩容触发已允许）
   - B：Sprint 2b 拆为 2b1 + 2b2
   - C：降低 EvidenceCollector Phase 1A 范围
4. 等 user 决策

**Sprint 整体 FAIL**：

- 进入 ADR 阶段
- 调整 v2.1.2 的工期估算
- 通报管理层（可能影响 M1 时间）

---

## 7. M1 验收专项（Sprint 5）

Sprint 5 末尾的 M1 验收特别准备：

### 7.1 Demo 准备（参考文档 09）

- 完成 6 个 Demo 场景脚本化
- 至少演练 3 次（不要现场试）
- 录制 backup 视频
- 准备 Q&A 预案 10 题

### 7.2 M1 验收 deliverable

```
docs/dev_memory/phase_1a/M1_acceptance/
├── m1_summary.md              # M1 总结报告
├── exit_criteria_check.md     # 12 场景成功率 + Detection/Evidence/Patch Rate
├── demo_scripts/              # 6 个场景脚本
├── demo_videos_backup/        # 预录视频
├── test_results_full.html     # 完整测试报告
└── known_issues_v1.yaml       # 收集的 20-30 条初始 Known Issues
```

### 7.3 Phase 1A → 1B 转换

M1 PASS 后才能启动 Phase 1B Sprint 0B（v2.1.2 §3.0 硬约束）。

不要在 Phase 1A 期间预先开始 Phase 1B 代码。

---

## 8. 与 Phase 1B 的关系

Phase 1B 本 prompt **同样适用**，只需替换：

- Sprint N → Sprint NB（如 Sprint 1B / 2B / ...）
- Phase 1A → Phase 1B
- M1 → M2
- Compiler Agent → Benchmark Agent
- 12 场景 → 5 种 Skill / 5 种报告 / cross-agent handoff

Phase 1B 特有补充见《Benchmark Agent v5.2-RC2.3》+《Skill 框架 v0.2.1》。

---

## 9. 总结

**Sprint 1+ 不是 spike，是真实施**。

- 每个子任务都要 UT + 集成测试
- 每个 commit 都要 check_gate.sh（8 blocking + 1 advisory）
- 每个 Sprint 末尾都要 review_packet
- 跟设计文档不符合的实施必须明确说明
- 失败时不要硬冲，给 user 选项

**节奏与质量比速度重要**。

---

**Sprint 启动指令**（v1.1 模板化）：

当 user 明确说 "**Sprint N 启动**" 时：

1. 读 v2.1.2 中对应 Sprint 的任务清单
2. 从该 Sprint 第一个子任务开始（如 Sprint 1 从 S1-01 / Sprint 2a 从 S2a-01 / Sprint 1B 从 S1B-01）
3. 按 §3.1 标准 checklist 开始

**不要假设是 Sprint 1**。Phase 1A Sprint 1-5 / Phase 1B Sprint 1B-5B 均适用本 prompt，每次启动等 user 明确指令。
