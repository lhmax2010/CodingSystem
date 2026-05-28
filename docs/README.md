# Coding System 文档索引

本目录包含 Coding System（Tizen toolchain 迁移自动化系统）的全部设计文档与开发指引。

## 目录结构

```
docs/
├── README.md                    # 本文件（文档索引 + 阅读顺序）
├── baseline/                    # 设计基线文档（Frozen，开发期间不得修改）
├── prompts/                     # Codex 工作指引
└── adr/                         # 架构决策记录 + 规模化 spike
```

## 文档清单与版本

### baseline/ — 设计基线（Frozen）

| 文档 | 版本 | 用途 | 状态 |
|---|---|---|---|
| `00_Agent_Team_Contract_v0.7.2.md` | v0.7.2 | Agent 协作协议（最底层契约） | Locked |
| `02_Compiler_Agent_v5.2-RC2.2.md` | v5.2-RC2.2 | Phase 1A 主体：编译错误修复 Agent | Sprint 0 Ready |
| `03_Benchmark_Agent_v5.2-RC2.3.md` | v5.2-RC2.3 | Phase 1B 主体：性能基准 Agent | Sprint 0 Ready |
| `06_Code_Navigation_Evidence_Infrastructure_v0.3.3.md` | v0.3.3 | CNEI（Live 模式，代码导航证据基础设施） | Draft / Spike Required |
| `05_Phased_Development_Plan_v2.1.2.md` | v2.1.2 | Sprint 拆分 + DoD + dev_memory + merge gate | Implementation Plan |
| `07_Benchmark_Skill_Framework_v0.2.1.md` | v0.2.1 | Phase 1B Skill 扩展框架 | Implementation Candidate |
| `08_Phase_1_5_Overview_v0.3.md` | v0.3 | Phase 1.5 路线（含 OS 级扩展点预留） | Forward Roadmap |
| `09_Demo_Acceptance_Playbook_v0.3.md` | v0.3 | M1/M2 Demo 验收剧本 | Demo Template |

### prompts/ — Codex 工作指引

| 文档 | 版本 | 用途 |
|---|---|---|
| `MAIN_PROMPT_for_Codex_v2.2.md` | v2.2 | Codex 工作总指南（贯穿 Sprint 0 → M2） |
| `SPRINT_0_PROMPT_for_Codex_v1.1.md` | v1.1 | Sprint 0 Spike Gate 启动专用 |
| `SPRINT_1_PLUS_PROMPT_for_Codex_v1.2.md` | v1.2 | Sprint 1+ 常规开发流程 |

### adr/ — 架构决策记录

| 文档 | 用途 | 状态 |
|---|---|---|
| `ADR_001_CNEI_Scale_Direction.md` | OS 级规模化方向（三层架构：Live + Migration Intelligence + RPM Semantic） | Accepted |
| `S0-10_Scale_Feasibility_Spike.md` | OS 级规模可行性验证任务定义（独立 spike） | Pending Execution |

## 阅读顺序（Codex 每次会话开始时执行）

### Sprint 0 阶段

1. `prompts/MAIN_PROMPT_for_Codex_v2.2.md`（工作总指南，必读）
2. `prompts/SPRINT_0_PROMPT_for_Codex_v1.1.md`（Sprint 0 启动）
3. `baseline/00_Agent_Team_Contract_v0.7.2.md`（协议层）
4. `baseline/02_Compiler_Agent_v5.2-RC2.2.md`（Phase 1A 主体）
5. `baseline/06_Code_Navigation_Evidence_Infrastructure_v0.3.3.md`（CNEI）
6. `baseline/05_Phased_Development_Plan_v2.1.2.md`（Sprint 拆分）
7. `adr/ADR_001_CNEI_Scale_Direction.md`（规模化方向，了解 Phase 1A 要预留什么）
8. `adr/S0-10_Scale_Feasibility_Spike.md`（如启动规模 spike）

### Sprint 1+ 阶段

切换到 `prompts/SPRINT_1_PLUS_PROMPT_for_Codex_v1.2.md`，按 v2.1.2 的 Sprint 任务清单推进。

## 重要边界（务必理解）

### 开工范围

- ✅ **Phase 1A 主线**：Compiler Agent + Live CNEI（baseline 文档已 finalize）
- ✅ **Sprint 0 Spike Gate**：S0-01 ~ S0-09（验证关键技术假设）
- ✅ **S0-10 Scale Spike**：OS 级规模可行性验证（独立 spike，验证 gbs/chroot/scip-clang 可行性）

### 不在开工范围

- ❌ **CNEI v0.4（Layer 0/1 Migration Intelligence）**：只有 ADR-001 锁定方向，正式设计**必须等 S0-10 spike 真实数据出来后再定稿**。Phase 1A **只做 Live CNEI + 接口预留**，不实现 OS 级索引。

### 关键技术约束（来自 baseline + ADR）

1. **Cognitive Boundary**：CNEI 只收集证据，判断留给 LLM；rerun/retry/计数由 Tool 层决定
2. **Raw Log 硬约束**：raw log 永不进 LLM prompt，只有 bounded + redacted 的 log_excerpt 可进
3. **不修改用户主代码**：用 git worktree 隔离，patch 作为产出由人决定 apply
4. **Bounded Repair**：最多 2 次 patch + 1 次 rebuild，失败 fail-safe
5. **设计文档 Frozen**：开发期间不得擅自修改 baseline，发现问题走设计变更提案流程

## 版本演进历史（供追溯）

本文档体系经过 5+ 轮 Claude + ChatGPT + Kimi 联合 review：
- Compiler/Benchmark：RC1 → RC2 → RC2.1 → RC2.2 → RC2.3
- CNEI：v0.1 → v0.2 → v0.3.1 → v0.3.2 → v0.3.3
- 开发计划：v2.0 → v2.1 → v2.1.1 → v2.1.2
- Prompts：v2 → v2.1 → v2.2 / v1 → v1.1 → v1.2
- ADR-001 + S0-10：2 轮规模化方案 review 后产出

如需查阅历史版本，见原始输出目录。
