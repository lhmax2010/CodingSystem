# Coding System 文档索引

本目录包含 Coding System（Tizen toolchain 迁移自动化系统）的全部设计文档与开发指引。

## 目录结构

```
docs/
├── README.md                    # 本文件（文档索引 + 阅读顺序）
├── DEVELOPMENT_RULES.md         # R1–R14 开发规约（不走 PR，直接 push）
├── checkpoints.md               # checkpoint 登记表
├── baseline/                    # 设计基线文档（Frozen，开发期间不得修改）
├── prompts/                     # Codex 工作指引
├── adr/                         # 架构决策记录 + 规模化 spike
├── dev_memory/                  # 开发记忆（Codex 开发时填）
├── review/                      # Review 相关
├── design_changes/              # 设计变更提案（R1 触发）
└── spinoffs/                    # subagent 隔离话题
```

## 文档清单与版本（已含 Codex Sprint 0 design review 6 个 Issue 修复）

### baseline/ — 设计基线（Frozen）

| 文档 | 版本 | 用途 | 状态 |
|---|---|---|---|
| `00_Agent_Team_Contract_v0.7.3.md` | v0.7.3 | Agent 协作协议（最底层契约） | Locked |
| `02_Compiler_Agent_v5.2-RC2.3.md` | v5.2-RC2.3 | Phase 1A 主体：编译错误修复 Agent | Sprint 0 Ready |
| `03_Benchmark_Agent_v5.2-RC2.4.md` | v5.2-RC2.4 | Phase 1B 主体：性能基准 Agent | Sprint 0 Ready |
| `06_Code_Navigation_Evidence_Infrastructure_v0.3.5.md` | v0.3.5 | CNEI（Live 模式，代码导航证据基础设施） | Draft / Spike Required |
| `05_Phased_Development_Plan_v2.1.5.md` | v2.1.5 | Sprint 拆分 + DoD + dev_memory + merge gate | Implementation Plan |
| `07_Benchmark_Skill_Framework_v0.2.1.md` | v0.2.1 | Phase 1B Skill 扩展框架 | Implementation Candidate |
| `08_Phase_1_5_Overview_v0.3.md` | v0.3 | Phase 1.5 路线（含 OS 级扩展点预留） | Forward Roadmap |
| `09_Demo_Acceptance_Playbook_v0.3.md` | v0.3 | M1/M2 Demo 验收剧本 | Demo Template |

### prompts/ — Codex 工作指引

| 文档 | 版本 | 用途 |
|---|---|---|
| `MAIN_PROMPT_for_Codex_v2.5.md` | v2.5 | Codex 工作总指南（贯穿 Sprint 0 → M2） |
| `SPRINT_0_PROMPT_for_Codex_v1.2.1.md` | v1.2 | Sprint 0 Spike Gate 启动专用 |
| `SPRINT_1_PLUS_PROMPT_for_Codex_v1.3.md` | v1.3 | Sprint 1+ 常规开发流程 |

### adr/ — 架构决策记录

| 文档 | 用途 | 状态 |
|---|---|---|
| `ADR_001_CNEI_Scale_Direction.md` | OS 级规模化方向（三层架构：Live + Migration Intelligence + RPM Semantic） | Accepted |
| `S0-10_Scale_Feasibility_Spike.md` | OS 级规模可行性验证任务定义（独立 spike） | Pending Execution |

## 阅读顺序（Codex 每次会话开始时执行）

### Sprint 0 阶段

1. `README.md`（本文件）
2. `DEVELOPMENT_RULES.md`（R1–R14 规约，含 PR 调整）
3. `prompts/MAIN_PROMPT_for_Codex_v2.5.md`（工作总指南，必读）
4. `prompts/SPRINT_0_PROMPT_for_Codex_v1.2.1.md`（Sprint 0 启动）
5. `baseline/00_Agent_Team_Contract_v0.7.3.md`（协议层）
6. `baseline/02_Compiler_Agent_v5.2-RC2.3.md`（Phase 1A 主体）
7. `baseline/06_Code_Navigation_Evidence_Infrastructure_v0.3.5.md`（CNEI）
8. `baseline/05_Phased_Development_Plan_v2.1.5.md`（Sprint 拆分）
9. `adr/ADR_001_CNEI_Scale_Direction.md`（规模化方向，了解 Phase 1A 要预留什么）
10. `design_changes/`（已批准的设计变更，了解 baseline 演进）

### Sprint 1+ 阶段

切换到 `prompts/SPRINT_1_PLUS_PROMPT_for_Codex_v1.3.md`，按 v2.1.5 的 Sprint 任务清单推进。

## 重要边界（务必理解）

### 开工范围

- ✅ **Phase 1A 主线**：Compiler Agent + Live CNEI（baseline 文档已 finalize）
- ✅ **Sprint 0 Spike Gate**：S0-01 ~ S0-09（验证关键技术假设）
- ✅ **S0-10 Scale Spike**：OS 级规模可行性验证（独立 spike，由 PM 决定启动时机，不要自动开始）

### 不在开工范围

- ❌ **CNEI v0.4（Layer 0/1 Migration Intelligence）**：只有 ADR-001 锁定方向，正式设计**必须等 S0-10 spike 真实数据出来后再定稿**。Phase 1A **只做 Live CNEI + 接口预留**。

### 关键技术约束

1. **Cognitive Boundary**：CNEI 只收集证据，判断留给 LLM；rerun/retry/计数由 Tool 层决定
2. **Raw Log 硬约束**：raw log 永不进 LLM prompt；RawDataDetector 阈值 6000 字符（Contract v0.7.3 §5.6.3）
3. **不修改用户主代码**：用 git worktree 隔离，patch 作为产出由人决定 apply
4. **Bounded Repair**：最多 2 次 patch + 1 次 rebuild，失败 fail-safe
5. **Evidence 失败行为**：degraded 优先，完全无证据才 fail-fast（CNEI v0.3.5 §2.2.4）
6. **设计文档 Frozen**：开发期间不得擅自修改 baseline，发现问题走设计变更提案流程

## 版本演进历史

本文档体系经过 5+ 轮 Claude + ChatGPT + Kimi 联合 review + 1 轮 Codex Sprint 0 design review：
- Compiler：RC1 → RC2 → RC2.1 → RC2.2 → **RC2.3**（补 verify_timeout_sec）
- Benchmark：RC1 → RC2 → RC2.1 → RC2.2 → RC2.3 → **RC2.4**（token_usage 对齐 Contract）
- CNEI：v0.1 → v0.2 → v0.3.1 → v0.3.2 → v0.3.3 → v0.3.4 → **v0.3.5**（LogErrorParser taxonomy 扩到 10 类 + primary/cascade 识别 + LLD/GNU ld 双格式，S0-04 实证 26x token 缩减）
- Contract：v0.7 → v0.7.1 → v0.7.2 → **v0.7.3**（RawDataDetector 阈值统一）
- 开发计划：v2.0 → v2.1 → v2.1.1 → v2.1.2 → v2.1.3 → **v2.1.4**（S0-04 标准明确化 + S2b-03 LogErrorParser 实现增强）
- Prompts：MAIN **v2.4** / SPRINT_0 v1.2.1 / SPRINT_1+ v1.3

**最近一次变更**：Codex Sprint 0 S0-04 LogErrorParser spike 沉淀（26x token 缩减实证），见 `design_changes/change_2_S0-04_LogErrorParser_spike.md`。

**之前变更**：Codex Sprint 0 design review 6 个 `[DESIGN_ISSUE]`，见 `design_changes/change_1.md`。
