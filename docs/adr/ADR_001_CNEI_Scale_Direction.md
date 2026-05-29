# ADR-001: CNEI Scale Direction（OS 级 Toolchain 迁移）

**状态**：Accepted
**日期**：2026-05-27
**决策者**：user（PM）+ Claude + ChatGPT + Kimi（2 轮联合 review）
**关联文档**：
- 《CNEI v0.3.5》（现有 Live 模式设计）
- 《Phase 1.5 总览 v0.3》（§2.3 Chromium-scale CNEI）
- 待产出：S0-10 Scale Feasibility Spike（任务定义）
- 待产出：CNEI v0.4 Scale Architecture（Spike 后定稿）

---

## 1. 背景与问题

CNEI v0.3.5 当前是 **Live 按需收集证据**模式（`get_evidence_packet(error_event) -> EvidencePacket`），针对**单个编译错误**做深度诊断，强项是 build-system 感知 + negative_facts + confidence + stale 检测。

这对 Phase 1A（项目级、cmake/ninja、单 repo）是正确的。

**但实际业务目标是 OS 级 toolchain 迁移**（不只 LLD，还有 libc++ 替换 libstdc++、glibc 替换 musl 等持续需求），涉及：

- 数千个 Tizen RPM、数千万行代码
- 一次 toolchain 替换 → 大量 RPM 同时出错 → 大量错误共享相同根因
- 需要批量聚类、复用证据、复用修复、按 build context 精确定位

**经 2 轮 ChatGPT + Kimi 联合 review，确认 Live-only 模式在 OS 级规模下有真实瓶颈**：

1. clangd cold start 成本（数千 RPM 每个独立 cold start 不可接受）
2. 缺乏跨 RPM 全局索引（无法回答"symbol 在整个 OS 被谁引用/提供"）
3. 无持久化复用（同类错误反复分析）

---

## 2. 决策

### 2.1 采用三层架构（不是"双模式 code graph"）

```
Migration Orchestrator（Phase 1.5）
  按任务类型选择调用路径（非固定瀑布流）
  ├─ 批量聚类 → 可能只碰 Layer 0
  ├─ 单复杂 C++ 错误 → 可能只碰 Layer 2 Live
  └─ cluster exemplar 深挖 → Layer 0 选样 → Layer 1 语义 → Layer 2 证据

Layer 0: OS-level Migration Intelligence（核心，Phase 1.5）
  ├─ diagnostic warehouse + fingerprint clustering   ← 主数据源
  ├─ artifact symbol index（nm/readelf/llvm-readobj） ← 主数据源（高置信）
  ├─ link command index                              ← 主数据源
  ├─ package dependency graph                        ← 跨 RPM 影响
  ├─ failure_causality_graph                         ← primary/secondary/cascade 区分
  ├─ global source identifier index（tree-sitter）   ← 仅 recall，confidence=low
  └─ fix pattern memory（含 anti-pattern + 状态机）   ← 谨慎，见 §3.5

Layer 1: Context-sharded RPM Semantic Index（增强，非首选）
  引擎：scip-clang
  shard key = package + arch + toolchain_profile + sysroot + cc_hash
  只持久化 package-owned semantic facts（允许解析依赖 header）
  仅在 cluster exemplar / 复杂 C++ 语义时启用

Layer 2: Live Evidence Collector（CNEI v0.3.5 现有，完全不动）
  clangd + build-system collectors + EvidencePacket + negative_facts
```

### 2.2 8 条核心原则（锁定方向，防止后续走偏）

1. **Live CNEI 不替换、不推翻**。v0.3.5 的 Layer 2 完整保留。
2. **OS scale 需要 Migration Intelligence，不是 global code graph**。问题不是"代码怎么查得快"，而是"错误/构建/符号/依赖如何组织"。
3. **Layer 0 的 source identifier index 只做 recall，不做 truth**。tree-sitter/ctags 受 macro/typedef/template/条件编译/generated headers/arch 差异影响，只能回答"哪里可能提到这个 identifier"，不能回答"真实定义/引用关系"。confidence 标 low。
4. **Layer 0 的主 truth source 是 diagnostics / link commands / artifact symbols / package deps**。这些来自真实构建产物，置信度高于源码 recall。
5. **Layer 1 scip-clang 是 context-sharded RPM semantic index，不做全 OS semantic graph**。
6. **Layer 1 允许解析 dependency headers（type-check 必需），但默认只持久化 package-owned facts**。跨 RPM 语义跳转不承诺，交给 Layer 0 recall。
7. **Phase 1A 只做 scale spike + interface reservation**，不做 OS 索引实现。
8. **CNEI v0.4 必须等 scale spike 数据出来后再定稿**。避免基于假设写大设计。

---

## 3. 关键技术边界（经 review 修正）

### 3.1 Layer 1 边界精确表述（ChatGPT 修正 1）

C/C++ 语义索引**不可能完全不碰依赖**——编译一个 TU 必须解析 headers / sysroot / 依赖包 header 才能 type-check。

正确边界：

```
- 输入：当前 RPM 的真实 compile command / sysroot / include path
- 解析：允许解析 dependency headers（type-check 必需）
- 持久化：默认只保存 package-owned files 的 semantic facts
- 跨 RPM：不承诺语义跳转，交给 Layer 0 artifact/source recall
```

**不是"不解析依赖"，而是"不把依赖包作为完整 semantic shard 输出"。**

### 3.2 scip-clang 二次方限制：高风险假设，非定论（ChatGPT 修正 2）

scip-clang 官方文档警告：索引多个 package shard 时，可能重复解析共享依赖 headers / 传递依赖上下文，造成重复工作。

**但这是高风险假设，不是已证明定论**。实际成本取决于运行方式 / cache / project root 限制 / 是否输出 external dependency facts / sysroot 是否复用。

**必须在 Scale Spike 验证**（见 S0-10 P1）。

### 3.3 gbs chroot 路径映射：生死线中的生死线（Kimi 致命发现）

gbs 在 chroot 内构建，compile_commands.json 里的路径是 chroot 内绝对路径（`/builddir/build/BUILD/...`）。scip-clang 在宿主机运行时这些路径**可能失效**。

**这比"能否提取 compile_commands"严重一个量级**。必须在 Spike 对比三种解法（见 S0-10 P0-2）。

### 3.4 存储：SQLite 为主 + 分区策略（双方折中 + ChatGPT 修正 4）

```
- SQLite 用于 Spike 和 Phase 1.5 MVP（嵌入式零运维）
- 数据必须可按 toolchain_profile / arch / package / build_id / sysroot_hash 分区
- artifact symbols 和 diagnostics 不塞进一个巨表
- 分析瓶颈时引入 DuckDB/Parquet 做 OLAP（不改 producer schema，可直接查 SQLite）
- 明确不上 Postgres（除非演化为公司级平台）
```

### 3.5 fix pattern memory：状态机 + 安全机制（双方合并 + ChatGPT 修正 5）

**不输出"修复方案"，输出"候选 pattern + 必需证据 + 反模式 + 验证规则"。**

状态机（加 exemplar 验证中间态）：

```
candidate
  ↓ exemplar verification pass
validated_on_exemplars
  ↓ batch sample verification pass + human approval
trusted
  ↓ regression / false positive
rejected or quarantined
```

每个 pattern 必须含：required_evidence + anti_patterns + verification rules + human gate。

### 3.6 failure_causality_graph：区分 primary/secondary/cascade（ChatGPT 盲点）

基础库 provider 包先失败 → 下游 consumer 大量 undefined reference / missing header。这些看起来像 consumer 错误，根因其实是 provider 没构建成功。

Layer 0 必须区分：

```
primary failure（provider 自己的错）
secondary failure（consumer 因 provider 失败而失败）
cascade failure（连锁）

示例：
  libfoo build failed
    ↓
  libbar link failed: -lfoo not found
    ↓
  appbaz undefined reference: foo_init
```

否则系统会对 200 个 consumer 包生成错误 patch，而真正要修的是 1 个 provider 包。

### 3.7 scip-clang 不支持 PCH（Kimi 盲点）

scip-clang 官方明确不支持 precompiled headers。Tizen 某些 RPM 可能用 PCH 加速编译。

Spike 故意测一个用 PCH 的 RPM。如失败，v0.4 明确"不支持 PCH 的 RPM 降级为纯 Layer 0 + Layer 2 Live 模式"。

---

## 4. 输出分级

```
EvidencePacket         单错误（Layer 2，现有）
ClusterEvidencePacket  同类错误（Layer 0，新增，带 3 类 exemplar）
MigrationRunReport     全局迁移（Orchestrator，新增）
```

ClusterEvidencePacket 必须含 exemplar（不能只是统计摘要）：

```
每个 cluster 选 3 类 exemplar：
1. smallest failing package（最小复现）
2. most common failure pattern package（最典型）
3. highest impact / most depended-on package（最高影响）
```

---

## 5. 时序

```
Phase 1A:
  - Live CNEI 主线不动（验证 Agent 修复能力）
  - Sprint 0 增加 S0-10 Scale Feasibility Spike（轻量，50-100 RPM）
  - 预留 Layer 0 接口（query_global_symbol / query_artifact_symbols / query_error_clusters）
  - Layer 0 可以是 mock（ripgrep 慢速实现）

Phase 1B:
  - 专注 Benchmark，不碰 OS 索引

Phase 1.5:
  - 正式实现 Layer 0（优先 diagnostic DB + artifact symbol DB + package dep graph）
  - Layer 1 scip-clang 作为增强，非第一优先级
```

---

## 6. 被拒绝的方案

| 方案 | 拒绝理由 |
|---|---|
| 用 colbymchenry/codegraph 替代 CNEI | tree-sitter 语法级、不懂 build system、无 negative facts、无 confidence；只能做 recall 辅助 |
| scip-clang 做全 OS 单体 semantic graph | 符号冲突 / 类型不一致 / 二次方索引 / TB 级存储 |
| Kythe / Glean | 重、部署复杂、学习曲线陡；当前阶段过度工程 |
| Postgres 做 Layer 0 存储 | 运维负担，Tizen 基础设施团队接受度低；SQLite + DuckDB 够用 |
| Phase 1A 直接做全局索引 | 应先验证 Agent 修复能力 + gbs/chroot 生死线，再规模化 |

---

## 7. 风险与待验证项

所有高风险假设集中在 S0-10 Scale Feasibility Spike 验证：

| 风险 | 验证项 | 优先级 |
|---|---|---|
| gbs 提取不出 compile/link command | S0-10 P0-1 | 生死线 |
| gbs chroot 路径在宿主机失效 | S0-10 P0-2 | 生死线 |
| artifact symbol 数据源拿不到 | S0-10 P0-3 | 生死线 |
| scip-clang 二次方索引成本 | S0-10 P1-2 | 架构边界 |
| diagnostic 聚类准确率不足 | S0-10 P1-1 | 架构边界 |
| scip-clang 不支持 PCH | S0-10 P1-2 | 工程约束 |

**如 P0 任一项 FAIL → 整个 Layer 1 scip-clang 方案重新评估。**

---

**ADR 结束。下一步：S0-10 Scale Feasibility Spike 任务定义。**
