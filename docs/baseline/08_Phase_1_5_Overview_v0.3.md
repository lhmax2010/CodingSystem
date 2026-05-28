# Phase 1.5 总览 v0.3（100 人推广 + 产品化 + 跨构建系统）

**版本**：v0.3（针对 Kimi v0.2 review 小修）

**v0.3 修订摘要**：

- Kimi 抓到：§5.4 trust_level 描述不准 — 实际 Skill v0.2.1 §2.6 已声明 trust_level 字段（local / registered），Phase 1B 已实施；Phase 1.5 新增 untrusted_external 支持
- 同步 Skill 框架版本号引用到 v0.2.1（之前是 v0.2，但 v0.2.1 才是当前基线）
**状态**：Forward-looking Roadmap（前瞻性规划，Phase 1A/1B 完成后再做精细化）

**v0.2 修订摘要**：

- ChatGPT 抓到：Phase 1.5 范围偏大（5-7 个月串行 vs 目标 3-4 个月） — 拆为 Must-have / Should-have / Stretch 三层
- ChatGPT 抓到：Memory Infrastructure 缺 governance 规则 — 新增 §2.2.1 Memory Governance
**适用对象**：管理层 / Codex（了解 Phase 1A/1B 写代码时需要预留什么扩展点） / 团队
**关联文档**：
- 《Agent Team Contract v0.7.2》（文档 00）
- 《Compiler Agent v5.2-RC2.2》（文档 02）
- 《Benchmark Agent v5.2-RC2.3》（文档 03）
- 《CNEI v0.3.3》（文档 06）
- 《开发计划 v2.1.1》（文档 05）
- 《Skill 框架 v0.2.1》（文档 07）

**文档目的**：把 Phase 1A/1B 之后要做的事说清楚，让管理层看到路线，让 Codex 在 Phase 1A/1B 写代码时知道该预留什么扩展点，避免日后大改。

**重要说明**：本文档是**前瞻性 roadmap**，**不是精细 Sprint 计划**。详细 Sprint 拆分留到 Phase 1B 完成后基于真实数据再做。

---

## 1. Phase 1.5 目标

### 1.1 核心目标

把 Phase 1A/1B 验证过的 MVP 从 **5-10 人内部 dogfooding** 推广到 **100 人内部使用**，同时补齐产品化基础设施和扩展能力。

### 1.2 量化目标

| 维度 | Phase 1A/1B 末期 | Phase 1.5 末期 |
|---|---|---|
| **覆盖用户** | 5-10 人 | 100 人 |
| **支持 build system** | cmake/ninja | cmake/ninja + **gbs** + **make** |
| **支持 repo 规模** | < 100 万行 | < 2500 万行（**Chromium-scale**） |
| **Compiler Agent 自动修复率** | ≥ 60%（12 场景）| ≥ 70%（更多场景）|
| **Skill 沙箱** | best-effort policy | **容器化真隔离** |
| **Known Issues 增长方式** | 人工维护 20-30 条 | **Memory Infrastructure 自动学习** |
| **运维** | 无 | **监控 + 告警 + SLA** |

### 1.3 时间估算

**3-4 个月**（实际工期估算 5-7 个月，详见 §6 风险）。

---

## 2. Phase 1.5 新能力清单（v0.2 分层）

### 2.0 能力分层（v0.2 新增，ChatGPT 反馈）

Phase 1.5 范围按交付优先级分三层。**Must-have 是 M3 验收的硬门槛**，Should-have 视进度，Stretch 是有时间才做：

#### M3 Must-have（必须达成才能算 Phase 1.5 完成）

- **gbs basic support**（§2.1 gbs 解析与构建集成）
- **make / autotools basic support**（§2.1 make 解析）
- **Memory Infrastructure v1**（§2.2 + §2.2.1 governance）
- **监控 + Grafana dashboard + 基础告警**（§2.7 部分）
- **100 人滚动推广流程**（§4 三 wave 完整实施）

#### M3 Should-have（推荐达成，不达成不阻塞 M3）

- **Skill 容器化 host-side**（§2.4 host-side Skill 容器化，device-side Skill 推 Phase 2）
- **Benchmark history trend**（§2.6 报告升级中"历史趋势图"）
- **distributed Known Issues registry**（§2.2 跨 repo 共享）

#### M3 Stretch（如有富余时间）

- **Chromium-scale CNEI**（§2.3 全部）
- **Cross-host device pool**（§2.5 全部）
- **untrusted_external skill execution**（§2.4 容器化全部覆盖到 untrusted）

**理由说明**：

- Chromium-scale 和 Cross-host pool 是规模化能力，**不是 100 人推广的必要条件**（100 人内部场景仍可单主机 + 中等 repo 满足）
- 这些放 Stretch 让 Phase 1.5 实际可控（避免范围爆炸）
- 真正需要时再启动 Phase 2 专门规划

### 2.1 跨 Build System 支持

**目标**：从 cmake/ninja 扩展到 Tizen 主流构建系统。

**新增能力**：

- **gbs 解析与构建集成**
  - gbs-buildroot 解析（包含 spec 文件 + chroot 环境）
  - sysroot 处理（cross-compile 头文件路径）
  - rpm 包构建上下文
- **make 解析**
  - Makefile 解析（include / variable / pattern rules）
  - autotools 配置上下文（configure.ac）
- **autotools 集成**
  - configure 脚本环境探测
  - Makefile.am 处理

**CNEI 影响**：

- `select_backend_for_cpp()` Gate 4 增加 gbs/make 支持（不再降级）
- 新增 `SpecFileCollector`（Phase 1A 接口预留，1.5 完整实现）
- 新增 `AutotoolsContextCollector`

### 2.2 Memory Infrastructure

**目标**：Known Issues 从"人工维护 20-30 条"升级到"自动学习 + 向量检索 + 跨 repo 共享"。

**新增能力**：

- **trace 自动学习**
  - 从 Phase 1A/1B 累积的 trace 中提取候选 Known Issues
  - 用户标注成功/失败修复案例
  - 自动转换为 governance schema 格式
- **向量化检索**
  - error message → embedding
  - 相似度搜索：找到历史类似错误的修复
  - 替代/补充当前的 regex-based KnownIssueMatcher
- **跨 repo 共享**
  - team-level Known Issues registry
  - 不同 Tizen repo 间复用经验

**CNEI 影响**：

- `KnownIssueMatcher` 升级为 `HybridMatcher`（regex + vector）
- 新增 `MemoryService`（独立 service，跨 task 共享）
- Phase 1A/1B 的 `trace.json` 格式必须保持稳定（兼容性）

### 2.2.1 Memory Governance（v0.2 新增，ChatGPT 反馈）

**问题**：Memory Infrastructure 如果只做"自动学习"不做治理，200 条 auto-learned Known Issues 会很快变成"噪声库"，反而降低修复准确率。

**Memory Governance 规则**（M3 Must-have 一部分）：

#### 2.2.1.1 候选 Known Issue 晋升机制

```
candidate_known_issue (从 trace 自动提取，初始 confidence_default=0.3)
  ↓
[satisfies promotion criteria?]
  - 至少 N 次成功 verified fix（默认 N=3）
  - 或人工 review 标注 verified
  ↓ Yes
promoted to active Known Issue (confidence_default 升至 0.6)
  ↓
[continued usage tracked]
  ↓
[periodic revalidation]
```

#### 2.2.1.2 必备字段

每条 auto-learned Known Issue 必须有（同 v0.3.3 §7.4.1 governance schema）：

- `version`（每次更新 + 1）
- `owner`（推广组成员邮箱，不能是 auto）
- `confidence_default`（初始 0.3）
- `validated_count` + `false_positive_count`
- `expiry_date` 或 `revalidation_due_date`（默认 6 个月）
- `applicable_build_systems`（必填，禁止 catch-all）
- `supported_error_types` + `unsupported_error_types`

#### 2.2.1.3 置信度衰减规则

- false_positive_rate > 0.3 + validated_count ≥ 10 → confidence × 0.7
- false_positive_rate > 0.5 → status: under_review（停用 hint）
- 连续 3 个月无命中 → status: deprecated
- 超过 expiry_date 未 revalidate → status: deprecated

#### 2.2.1.4 跨 repo 共享时的 redaction

cross-repo 共享前必须 redact：

- repo-private file paths（如 `/home/john/internal/...`）
- usernames / hostnames
- internal URLs / tokens
- internal-only library names（如 allowlist 外的）

#### 2.2.1.5 trace 可追溯性

每次 KnownIssue match（regex 或 vector）必须在 `trace.json` 中记录：

```json
{
  "event_type": "known_issue_match",
  "match_method": "regex" | "vector",
  "matched_id": "...",
  "matched_confidence": 0.X,
  "match_evidence": {
    "regex_pattern_id": "...",
    "vector_similarity": 0.X,
    "embedding_model": "..."
  }
}
```

这保证 Memory Infrastructure 不是"黑箱"——每个匹配都可 audit。

#### 2.2.1.6 治理责任

- Memory Governance 由 Phase 1.5 期间专人负责（推广组指派）
- 每月 review：candidate → promoted / deprecated / under_review 数量
- 季度 revalidation：随机抽样 10% 跑 verification

### 2.3 Chromium-scale CNEI

**目标**：支持 Chromium 级（~2500 万行）的代码库。

**新增能力**：

- **scip-clang 预索引**
  - 离线生成 SCIP 索引文件（与 clangd LSP 并行使用）
  - CI 期间预生成，task 启动时 mmap 加载
- **Index sharding**
  - 大 repo 索引按 module 切片
  - 按需加载（只加载受影响 module）
- **Distributed cache**
  - 索引缓存放共享 storage（NFS / S3）
  - 多用户共享同一 repo 索引

**CNEI 影响**：

- `ClangdBackend` 增加 `scip-clang` 模式（与 LSP 并行）
- 新增 `IndexShardManager`
- Phase 1A 的 CNEIConfig 增加 `index_strategy: live | precomputed | hybrid`（Phase 1A 默认 live，Phase 1.5 推荐 hybrid）

### 2.4 Skill 容器化（真沙箱）

**目标**：从 Phase 1B 的 best-effort policy enforcement 升级到**真 sandbox**。

**新增能力**：

- **每个 Skill 在独立容器内运行**
  - Docker / Podman 或类似容器机制
  - 文件系统通过 bind mount 限制访问范围
  - 网络通过 network namespace 控制
  - CPU / 内存通过 cgroup 限制
- **Static scan: warning → block**
  - subprocess / os.system / open(abs) / requests 等直接调用 → **加载时拒绝**
- **`untrusted_external` Trust Level 开放**（v0.2.1 §2.6 中已预留枚举值，Phase 1B 不支持运行；Phase 1.5 容器化后才支持运行外部 Skill）

**Skill 框架影响**：

- v0.2.1 的 `trust_level` 字段在 Phase 1.5 真正发挥作用
- v0.2.1 的 ctx API 设计**不需要改**（Skill 代码不变，只是底层执行方式变了）
- Phase 1B static scan warning 在 Phase 1.5 升级为 hard fail

### 2.5 Cross-host Device Pool

**目标**：从单主机 device lock 扩展到跨主机 device 调度。

**新增能力**：

- **跨主机 device pool**
  - 基于 Redis / etcd 的分布式锁
  - 多主机 Benchmark Agent 抢同一开发板
- **自动 device 分配**
  - 调度器选择空闲开发板
  - 负载均衡 + 故障转移
- **Device 监控**
  - 健康检查（thermal / battery / connectivity）
  - 自动隔离故障 device

**Benchmark Agent 影响**：

- `DeviceLockManager` 升级为分布式版本（v0.2.1 的 PID file 机制保留作为 fallback）
- TaskInput 增加 `device_pool` 字段（指定 pool 而非具体 device_id）

### 2.6 报告升级

**目标**：从静态 HTML 升级到交互式 + 历史趋势。

**新增能力**：

- **plotly 交互式图表**
  - hover 显示详细数据点
  - zoom / pan / filter
- **历史趋势图**
  - 同一 benchmark 历史 N 次结果对比
  - 检测长期 regression / improvement
- **跨 benchmark 关联**
  - 不同 Skill 间 metric 相关性分析

**Benchmark Agent 影响**：

- `render_benchmark_report` 加 plotly backend（保留 matplotlib 作为 PDF backend）
- 新增 `BenchmarkHistoryService`（独立 service，访问历史结果）

### 2.7 产品化基础设施

**目标**：从 5-10 人 dogfooding 上升到 100 人推广所需的运营能力。

**新增能力**：

- **监控**
  - Prometheus metrics：task 数量 / 成功率 / token usage / device 利用率
  - Grafana dashboard
- **告警**
  - PagerDuty / Slack：自动修复成功率下降 / device pool 异常
- **SLA**
  - 99% task 在 budget 内完成
  - device 可用率 ≥ 95%
- **用户支持**
  - 内部文档站（docs.coding-system.internal）
  - Slack support channel
  - 培训材料

---

## 3. Phase 1.5 Sprint 主题（粗略）

**重要**：以下是**主题概览**，不是精确 sprint 拆分。详细 sprint 拆分在 Phase 1B 完成后基于真实进度再做。

| Sprint 主题 | 预估时长 | 依赖 |
|---|---|---|
| **gbs / make 解析与构建集成** | 3-4 周 | Phase 1A M1 / CNEI v0.3.3 |
| **Memory Infrastructure（向量库 + 检索）** | 4-5 周 | Phase 1A trace 数据 |
| **Chromium-scale CNEI（scip-clang + sharding）** | 3-4 周 | Phase 1A CNEI 主体 |
| **Skill 容器化（block 模式 + 真隔离）** | 3-4 周 | Phase 1B Skill 框架 v0.2.1 |
| **Cross-host device pool** | 2-3 周 | Phase 1B DeviceLockManager |
| **报告升级（plotly + 历史趋势）** | 2 周 | Phase 1B benchmark report |
| **监控 / 告警 / SLA** | 3-4 周 | Phase 1A/1B 集成 |
| **文档站 + 培训** | 2 周 | 其他能力就绪 |
| **100 人滚动推广** | 4-6 周 | 全部能力就绪 |

**总计**：22-30 周 ≈ **5-7 个月**（如果全部串行）

**实际目标**：3-4 个月 → **多个工作流并行**，详见 §4。

---

## 4. Phase 1.5 推广策略

### 4.1 滚动推广（关键）

**不要一次性放 100 人**。分 3 个 wave 滚动验证：

```
Wave 1（month 1）: 5-10 → 30 人
   - Phase 1A/1B 的 dogfooding 用户继续
   - 增加 20 人左右，覆盖 3-4 个团队
   - 重点收集"非 dogfooding"用户的反馈
   - 期望：发现"原作者觉得 OK 但其他人觉得难用"的问题

Wave 2（month 2-3）: 30 → 60 人
   - 加入 gbs / make 用户（Phase 1A/1B 不支持的群体）
   - 覆盖 8-10 个团队
   - 验证 Memory Infrastructure（积累足够 trace 后效果如何）
   - 期望：验证产品化设施（监控 / 告警）

Wave 3（month 3-4）: 60 → 100 人
   - 全 Tizen build team 推广
   - 覆盖 15+ 团队
   - 期望：稳态运行，无重大问题
```

### 4.2 推广前置条件

每个 Wave 启动前必须达成：

- [ ] 监控 + 告警 ready（不能盲飞）
- [ ] SLA 在前一 Wave 达标
- [ ] 文档站 + 培训材料更新到位
- [ ] 上一 Wave 用户反馈 80% 满意度

### 4.3 用户支持

- **L1 support**：Slack channel，2 小时内响应
- **L2 support**：Codex 自动诊断（基于 trace）
- **L3 support**：人工 root cause（用户 + Codex + 我们 PM）
- **Bug 处理流程**：标准化 ticket + SLA

---

## 5. Phase 1A/1B 需要为 Phase 1.5 预留的扩展点

**这部分对 Codex 最重要**：Phase 1A/1B 实施时不要写死，要为 1.5 留接口。

### 5.1 Compiler Agent 预留

| 扩展点 | Phase 1A 实施约束 |
|---|---|
| `build_system` 字段 | 枚举类型，Phase 1.5 增加 `gbs` / `make` 时不破坏 schema |
| `CompileCommandParser` | 实现是 plugin 式，Phase 1.5 可加 gbs / make parser |
| `WorkspaceManager` | 只支持 `git_repo_path`，Phase 1.5 可加 `gbs_buildroot` / `non_git_workspace` |
| `KnownIssueMatcher` | 基于 plugin / strategy 模式，方便 Phase 1.5 加 vector matcher |

### 5.2 Benchmark Agent 预留

| 扩展点 | Phase 1B 实施约束 |
|---|---|
| `DeviceLockManager` | API 设计为 single-host 实现，但接口签名兼容 distributed lock（acquire/release/heartbeat） |
| `SkillRuntime` | Skill 执行通过 `ExecutionBackend` 抽象，Phase 1B 是 LocalProcessBackend，Phase 1.5 加 ContainerBackend |
| `BenchmarkReportRenderer` | 5 种 backend 用 plugin 模式（md/html/png/csv/json），Phase 1.5 可加 plotly_interactive backend |
| `TaskInput.device_config` | 支持 `device_id`（具体） + `device_pool`（Phase 1.5 用） |

### 5.3 CNEI 预留

| 扩展点 | Phase 1A 实施约束 |
|---|---|
| `select_backend_for_cpp()` Gate 4 | 当前 cmake_ninja 通过；Phase 1.5 加 `gbs` / `make` 通过路径 |
| `IndexBackend` | 抽象接口，Phase 1A 是 `ClangdBackend`（live），Phase 1.5 加 `ScipClangBackend`（precomputed） + `HybridBackend` |
| `KnownIssueMatcher` | 接口暴露 `match(error_event) -> list[KnownIssue]`，实现可换 |
| `MemoryService` | Phase 1A 无此 service，但 CNEIConfig 可预留 `memory: enabled/disabled` 字段 |

### 5.4 Skill 框架预留

| 扩展点 | Phase 1B 实施约束 |
|---|---|
| `trust_level` | Phase 1B 已在 Skill v0.2.1 §2.6 声明 + 实施 `local` / `registered`；Phase 1.5 启用 `untrusted_external` 支持（依赖容器化）|
| `ExecutionBackend` | Skill 通过 backend 抽象执行，Phase 1B 是 LocalProcess，Phase 1.5 加 Container |
| Static scan | warning 模式，Phase 1.5 升级 block 模式 |
| `Manifest.dependencies` | Phase 1B 仅记录信息，Phase 1.5 容器化后实际安装到容器 |

### 5.5 跨 Agent 预留

| 扩展点 | Phase 1A/1B 实施约束 |
|---|---|
| `trace.json` schema | **必须保持向后兼容**，因为 Memory Infrastructure 依赖历史 trace |
| `EvidencePacket` schema | 同上 |
| `AgentDescriptor.team_contract_compatibility` | 用 `>=0.7,<0.8` 区间，Phase 1.5 可升 v0.8 但 Phase 1A/1B Agent 仍兼容 |

---

## 6. 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|---|---|---|---|
| Phase 1A/1B 工期超支拖累 1.5 | 中 | 高 | Phase 1A 预留缓冲（已在 v2.1.1 +2 周） |
| gbs / make 比 cmake 复杂得多，工期超支 | 高 | 高 | 提前 Phase 1A 期间做 gbs spike；选 1-2 个具代表性 gbs project 而非全部 |
| Memory Infrastructure 准确率不够 | 中 | 中 | 用 hybrid（regex + vector）保留 fallback；用户标注门槛降低 |
| Skill 容器化在 Tizen 开发板上跑不动 | 中 | 高 | host 侧 Skill 优先容器化；device 侧 Skill 在 Phase 2 再容器化 |
| 100 人推广反馈过度负面 | 低 | 高 | 滚动推广 + 每 Wave 验证；不达标不进下一 Wave |
| 跨主机 device pool 复杂度高于预期 | 中 | 中 | 推迟到 1.5 后期，先用 single-host pool |
| 监控 / 告警基础设施不到位 | 中 | 中 | 提前 Phase 1B 期间 PoC 监控方案 |

---

## 7. Phase 1.5 → Phase 2+ 演化方向

Phase 1.5 完成后，剩余 5 个 Agent（Coding / UT / Review / CI / Orchestrator）的实施进入 Phase 2+。届时 1.5 的产品化设施成为基线：

- **Coding Agent**：基于 Compiler/Benchmark 的反馈，自动生成 PR
- **UT Agent**：单元测试自动生成 + 维护
- **Review Agent**：代码 review 自动化
- **CI Agent**：CI 流程编排
- **LangGraph Orchestrator**：跨 Agent 流程编排（替代 Phase 1A/1B 的简单 handoff）

这些都不在 Phase 1.5 范围，但 Phase 1.5 的 Team Contract 兼容性区间（v0.7-v0.8）为它们留出了协议演化空间。

---

## 8. Phase 1.5 Exit Criteria（M3 验收，v0.2 分层）

Phase 1.5 完成的标志（M3 验收）：

### M3 Must-have（硬门槛，全部达成才算 M3 通过）

- [ ] 100 人内部用户实际使用 ≥ 1 个月
- [ ] gbs + make + cmake/ninja 三种 build system 都有用户成功修复案例
- [ ] Memory Infrastructure 至少积累 200 条 auto-learned Known Issues（governance 合规：confidence 衰减 + 治理责任）
- [ ] 监控 dashboard ready
- [ ] 基础 SLA：99% task 在 budget 内 / device 可用率 ≥ 95%
- [ ] 重大 incident（P0/P1）≤ 2 起
- [ ] 用户满意度 ≥ 80%
- [ ] 文档站 + 培训材料完整

### M3 Should-have（推荐达成，不阻塞 M3 通过）

- [ ] Skill 容器化覆盖至少 3 个 host-side 示例 Skill
- [ ] Benchmark 报告含历史趋势功能
- [ ] distributed Known Issues registry 跨 repo 共享试点

### M3 Stretch（如达成是 bonus）

- [ ] Chromium-scale repo（或类似规模）能产出有效 EvidencePacket
- [ ] Cross-host device pool 至少 3 台开发板稳定运行
- [ ] Skill 容器化覆盖 untrusted_external 试点

达成 Must-have 后进入 Phase 2+ 规划。Should/Stretch 未完成项纳入 Phase 2 待办。

---

**文档结束**
