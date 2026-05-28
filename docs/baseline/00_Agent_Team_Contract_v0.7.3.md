# Agent Team Contract（Phase 0）

**版本**：v0.7.3
**状态**：Locked（Phase 1A/1B 实施基线协议层）
**适用范围**：Coding System 所有 Agent（Coding / Compiler / UT / Review / Benchmark / CI 等)
**文档目的**：定义 Agent 之间协作的协议，使各 Agent 在独立实现时保持互操作性。

**版本历程**：
- v0.1：初版 7 块协议
- v0.2：新增 Contract-level Failure Class、HandoffRequest 必填性表格、artifact_refs 结构化、trace_ref 指向约束、AgentDescriptor 兼容性字段、Replay-safe 约束
- v0.3：Reason taxonomy 重构
- v0.4：verify_requested 拆分
- v0.5：新增 benchmark_passed reason
- v0.6：新增 Tool/Skill/Agent 术语章节
- v0.7：新增 5.5 节扩展位置预留、5.6 节 Raw Log 硬约束、新增 8 节安全约束（Secret/Env Redaction + Skill 概念）、ExecutionAdapter 多 backend 说明
- v0.7.1：Skill 代码限制精确化（user-authored but runtime-restricted）、Secret redaction 分级处理（L1/L2/L3）、handoff_id 加可选 disambiguator 字段
- v0.7.2：5.6 Raw Log 补 excerpt 例外条款、8.5.2 L1 redaction 路径局部替换、8.3.1 Skill Phase 1.5 hard-block 计划、2.6.2 Benchmark Phase 1B 启用 disambiguator
- **v0.7.3（本版）**：5.6.3 RawDataDetector 阈值统一为 6000 字符（消除 Compiler A5.2 代码骨架 20480 bytes 与 Contract 5000 字符的冲突）；统一单位为字符；新增场景 C 防绕过（Codex Sprint 0 design review Issue 2）

**v0.7.2 修订摘要**（针对 ChatGPT + Kimi 联合 review 反馈）：

- ChatGPT 指出"Contract 5.6 与 Compiler A5.2 log_excerpt 语义不一致" → 5.6 加 excerpt 例外
- Kimi 指出"L1 redaction 路径整段替换会破坏路径结构" → 改局部替换
- ChatGPT 指出"Skill Phase 1.5 hard-block 计划缺失" → 8.3.1 加 Phase 1.5 升级路径
- ChatGPT 指出"Benchmark Phase 1B 应启用 disambiguator" → 2.6.2 增加 Phase 1B 启用

---

## 0. 基本原则

1. **Contract-first**：任何 Agent 的对外接口必须先符合本文档，再谈内部实现
2. **最小协议**：本文档只定义 Agent 之间的必要协议，不涉及 Agent 内部状态机、Tool、Prompt 设计
3. **LangGraph-friendly**：所有协议保证未来可被 LangGraph StateGraph 自然包装
4. **ClineSR 边界清晰**：明确哪些决策归 LLM、哪些归 code
5. **Security-by-default**（v0.7 新增）：所有跨 Agent 数据传递、artifact 落盘、trace 记录默认进行 secret/env redaction

---

## 1. Task ID 命名空间

### 1.1 格式

```
{AGENT_CODE}-{SEQUENCE}[.{SUB_SEQUENCE}]
```

- `AGENT_CODE`：Agent 类型代码，固定 3 个大写字母
- `SEQUENCE`：6 位数字，按任务创建顺序单调递增
- `SUB_SEQUENCE`：可选，表示由该任务派生出的子任务序号

### 1.2 Agent Code 枚举

| Agent | Code |
|---|---|
| Coding | CDN |
| Compiler | CMP |
| UT Test | UTT |
| Review | REV |
| Benchmark | BMK |
| CI | CIX |

示例：`CMP-000123`、`CDN-000045.1`

### 1.3 关联关系

任务之间的因果关系通过 `parent_task_id` 字段显式表达：

```json
{
  "task_id": "CDN-000045.1",
  "parent_task_id": "CMP-000123",
  "trigger_reason": "compiler_suggested_fix"
}
```

### 1.4 Orchestrator 职责

Task ID 的分配由 **Team Orchestrator** 集中管理。MVP 阶段（无 Orchestrator）可由调用方手动指定。

---

## 2. Handoff Schema

### 2.1 定义

**Handoff** 指一个 Agent 完成任务后，通过 Orchestrator 触发下一个 Agent 的过程。每次 handoff 必须产出一个结构化的 `HandoffRequest`。

### 2.2 HandoffRequest Schema

```json
{
  "handoff_id": "HO-a1b2c3d4",
  "source_task_id": "CMP-000123",
  "target_agent": "CDN",
  "reason": "compile_failed",
  "priority": "normal",
  "payload": {
    "artifact_refs": [
      {
        "type": "artifact_ref",
        "task_id": "CMP-000123",
        "relative_path": "reports/build_report.json",
        "schema": "build_report.v1",
        "content_hash": "sha256:abc..."
      }
    ],
    "context_summary": "InlineCostModel not found, suggested patch available",
    "suggested_actions": ["apply_patch", "manual_review"]
  },
  "constraints": {
    "budget": { "total_agent_timeout_sec": 1800 },
    "deadline_iso": "2026-04-22T12:00:00Z"
  }
}
```

### 2.3 字段必填性

| Field | Required | Note |
|---|---|---|
| `handoff_id` | yes | 确定性 hash 规则（见 2.6） |
| `source_task_id` | yes | 必须是合法 Task ID |
| `target_agent` | yes | 必须在 1.2 枚举或 `HUMAN` |
| `reason` | yes | 必须在 2.5 枚举内 |
| `disambiguator` | no | v0.7.1 新增，区分同 source+reason+target 的多个 handoff（如 multi-Skill）|
| `priority` | no | 默认 `normal`，枚举：`high | normal | low` |
| `payload.artifact_refs` | conditional | 见 2.5 表 |
| `payload.context_summary` | yes | ≤ 300 字，不内嵌大日志 |
| `payload.suggested_actions` | no | 仅供参考 |
| `constraints.budget` | no | 默认由 Orchestrator 分配 |
| `constraints.deadline_iso` | no | 优先级高于 budget |

### 2.4 Handoff 规则

- Agent **不直接调用**其他 Agent，只能产出 `HandoffRequest`
- `target_agent: HUMAN` 表示升级到人工介入
- Orchestrator 负责消费 `HandoffRequest` 并决定是否真的触发下一个 Agent

### 2.5 Reason 枚举

**A. 失败/异常类**

| Reason | 来源 Agent | 典型目标 | 需要 artifact_refs |
|---|---|---|---|
| `compile_failed` | Compiler | Coding / Human | ✅ |
| `ut_failed` | UT | Coding / Human | ✅ |
| `regression_detected` | Benchmark | Coding / Review / Human | ✅ |
| `review_rejected` | Review | Coding / Human | ✅ |
| `ci_failed` | CI | Coding / Human | ✅ |

**B. 流转/请求类**

| Reason | 来源 Agent | 典型目标 | 需要 artifact_refs |
|---|---|---|---|
| `compile_requested` | Coding | Compiler | ✅ |
| `rebuild_verify_requested` | Compiler / Orchestrator | Compiler | ✅ |
| `functional_verify_requested` | Compiler | UT | ✅ |
| `performance_verify_requested` | Compiler | Benchmark | ✅ |
| `benchmark_requested` | Coding / UT | Benchmark | ✅ |
| `benchmark_passed` | Benchmark | Review / Coding | ✅ |
| `review_requested` | Coding | Review | ✅ |
| `ci_requested` | Review | CI | ✅ |

### 2.6 handoff_id 生成规则

#### 2.6.1 默认规则（Phase 1A/1B）

```
HO-{hex(sha256(source_task_id + "|" + reason + "|" + target_agent))[:8]}
```

适用于绝大多数场景。同 source_task + reason + target 组合产生确定性 ID，确保 replay-safe。

#### 2.6.2 Disambiguator 字段（v0.7.1 新增，可选）

为了应对未来同一 source_task + reason + target 组合可能产生多个 handoff 的场景（例如 multi-Skill benchmark 中每个 Skill 独立 handoff、多次 retry 后产生不同的 patch artifact），HandoffRequest 加一个**可选**字段 `disambiguator`：

```json
{
  "handoff_id": "HO-a1b2c3d4e5f6",
  "source_task_id": "BMK-000077",
  "target_agent": "CDN",
  "reason": "regression_detected",
  "disambiguator": "skill:video_player_startup",
  ...
}
```

**当 `disambiguator` 存在时**，handoff_id 生成规则改为：

```
HO-{hex(sha256(source_task_id + "|" + reason + "|" + target_agent + "|" + disambiguator))[:12]}
```

（注意：长度从 8 位 hex 增加到 12 位 hex，降低碰撞概率）

**Phase 1A 阶段（Compiler Agent）**：

- `disambiguator` 字段在 HandoffRequest schema 中已声明可选，但**Compiler Agent 不使用**（保持 8 位 hex 规则）
- Agent 实现 `HandoffBuilder` 时要支持解析 `disambiguator` 字段，但默认不生成
- 理由：Compiler Agent 每个 task 产出至多 1 个 handoff（compile_failed / functional_verify_requested / performance_verify_requested 三选一），不存在同 source+reason+target 的多 handoff 场景

**Phase 1B 阶段（Benchmark Agent，v0.7.2 修订）**：

- **Benchmark Agent 启用 disambiguator**（ChatGPT review 反馈）
- 当 Benchmark task 含**多个 Skill** 时，**每个 Skill 的 regression 独立 handoff**，使用 `disambiguator = "skill:{skill_id}"`
- handoff_id 使用 12 位 hex 规则
- 理由：multi-Skill task 在 Phase 1B 就会出现；现在启用避免 Phase 2 再改协议行为

**示例（Benchmark Phase 1B）**：

```json
// Benchmark task BMK-000077 含 video_player_startup + browser_load_time 两个 Skill
// video_player_startup 检测到 regression
{
  "handoff_id": "HO-{12 位 hex}",
  "source_task_id": "BMK-000077",
  "target_agent": "CDN",
  "reason": "regression_detected",
  "disambiguator": "skill:video_player_startup"
}

// browser_load_time 也检测到 regression
{
  "handoff_id": "HO-{不同的 12 位 hex}",
  "source_task_id": "BMK-000077",
  "target_agent": "CDN",
  "reason": "regression_detected",
  "disambiguator": "skill:browser_load_time"
}
```

两个 handoff 不会被去重，能独立路由。

**Phase 2+ 阶段**：

- 接收方 Agent / Orchestrator 必须支持两种长度的 handoff_id（向后兼容 8 位）
- 其他场景按需启用 disambiguator

#### 2.6.3 Replay-safe 保证

无论是否使用 `disambiguator`，handoff_id 必须是**纯函数性产生**（无随机、无时间戳）。同样输入永远得到同样的 handoff_id。

---

## 2a. Contract-level Failure Class

### 2a.1 目的

各 Agent 内部 failure_class 之外，**Team 层协作产生的失败**必须用统一枚举。

### 2a.2 Team-level Failure Class

| failure_class | 含义 | 典型 stage |
|---|---|---|
| `artifact_invalid` | Artifact reference 校验失败 | `input_resolve` |
| `handoff_invalid` | HandoffRequest 字段缺失或非法 | `handoff` |
| `contract_violation` | Agent 输出违反 Contract | `output_validate` |
| `budget_exceeded` | 预算耗尽 | `budget` |
| `deadline_exceeded` | deadline_iso 已过 | `scheduler` |
| `unknown_agent_type` | 路由到未注册 agent_type | `routing` |
| `incompatible_contract_version` | contract_version 不兼容 | `routing` |
| `raw_data_leakage` | **v0.7 新增**：raw log/data 直接进入 LLM prompt | `cognitive_input_validate` |
| `permission_denied` | **v0.7 新增**：Skill 申请的权限未在 Manifest 声明 | `skill_runtime` |
| `secret_leakage_detected` | **v0.7 新增**：trace/artifact 检测到 secret 未脱敏 | `output_validate` |

### 2a.3 stage 字段扩展

```
input_resolve | handoff | output_validate | scheduler | routing
| cognitive_input_validate (v0.7) | skill_runtime (v0.7)
```

---

## 3. Artifact Reference Protocol

### 3.1 目录布局

```
artifacts/
  {task_id}/
    workspace/
    logs/
    reports/
    patches/
    raw/
    evidence/                # v0.7 新增：Evidence Packet 落盘位置
    trace.json
    events.jsonl              # v0.7 新增：结构化事件流
    handoffs/
```

### 3.2 Artifact Reference 格式

跨 Agent 引用 artifact **必须**使用结构化 reference：

```json
{
  "type": "artifact_ref",
  "task_id": "CMP-000123",
  "relative_path": "reports/build_report.json",
  "schema": "build_report.v1",
  "content_hash": "sha256:abc..."
}
```

### 3.3 规则

- `task_id` / `schema` / `content_hash` 必填
- 生产方落盘时计算并记录 hash
- 消费方读取前校验 hash；不匹配抛 `ArtifactInvalid`

### 3.4 Artifact 生命周期

- 默认保留期：30 天
- 超期可被 GC
- 被下游显式引用的 hash 在下游 trace 中记录

### 3.5 Secret/Env Redaction（v0.7 新增）

**所有写入 artifact 的内容必须经过 redaction filter**，过滤以下模式：

- 环境变量值（除非显式 allowlist）
- 私钥 / token / API key 类正则模式
- 内网 IP / hostname（可配置）
- 用户名 / 邮箱（可配置）

Redaction 在 ArtifactManager 落盘前统一处理。**绕过 ArtifactManager 直接写文件视为 contract violation**。

---

## 4. Cross-Agent Trace 格式

### 4.1 目的

让一个 Task 在整个 Agent Team 中的流转可被端到端重建。

### 4.2 trace.json 结构与位置约束

**位置约束**：每个 Task 的 trace **必须**落在 `artifacts/{task_id}/trace.json`，路径固定、不可配置。

```json
{
  "task_id": "CMP-000123",
  "parent_task_id": null,
  "agent_type": "compiler",
  "agent_version": "5.2.0",
  "contract_version": "0.7",
  "started_at": "2026-04-22T10:00:00Z",
  "ended_at": "2026-04-22T10:05:23Z",
  "final_status": "failed",
  "token_usage": {
    "total_in": 12450,
    "total_out": 2380,
    "by_stage": {
      "analyze": {"in": 8500, "out": 1800},
      "generate_patch": {"in": 3950, "out": 580}
    }
  },
  "events": [
    {
      "seq": 1,
      "ts": "2026-04-22T10:00:01Z",
      "stage": "probe_env",
      "event_type": "tool_call",
      "name": "probe_build_env",
      "duration_ms": 450,
      "result_summary": "env_valid=true"
    },
    {
      "seq": 5,
      "ts": "2026-04-22T10:02:15Z",
      "stage": "analyze",
      "event_type": "llm_call",
      "name": "analyze_compile_failure",
      "prompt_version": "compiler_system@v3",
      "tokens_in": 2850,
      "tokens_out": 420,
      "duration_ms": 3200,
      "evidence_packet_ref": "evidence/ep_001.json",
      "result_summary": "decision=generate_patch, confidence=0.84"
    }
  ],
  "outgoing_handoffs": ["HO-a1b2c3d4"],
  "incoming_handoff": null
}
```

**v0.7 新增字段**：
- `token_usage`：task 级 token 统计（必填）
- `events[].evidence_packet_ref`：LLM call 必须关联其使用的 Evidence Packet

### 4.3 events.jsonl（v0.7 新增）

除 trace.json 外，每个 Task **必须**额外落盘 `events.jsonl`：

- 每行一个 event JSON
- 用于实时 stream（stdout / tail 监听）
- 内容与 trace.json 的 events[] 一致
- 失败时即使 trace.json 写入未完成，events.jsonl 也保留过程信息

### 4.4 Event Type 枚举

| event_type | 说明 |
|---|---|
| `tool_call` | 调用 Tool Layer |
| `llm_call` | 调用 ClineSR |
| `state_transition` | 状态机转移 |
| `failure` | 失败事件 |
| `budget_check` | BudgetTracker 检查点 |
| `handoff_emitted` | 发出 HandoffRequest |
| `evidence_collected` | **v0.7 新增**：Evidence Collector 完成 |
| `known_issue_matched` | **v0.7 新增**：Known Issue DB 命中 |
| `skill_invoked` | **v0.7 新增**：Skill Runtime 调用 Skill |

### 4.5 跨 Agent Trace 重建

通过 `parent_task_id` + `outgoing_handoffs` + `incoming_handoff` 三个字段串成 Team-level trace。

### 4.6 与外部 Observability 系统的关系

trace.json 是 source of truth。未来接入 Langfuse / Phoenix 等系统时由它们异步导入，**不反向依赖**。

---

## 5. Cognitive Layer Boundary（ClineSR 边界）

### 5.1 核心原则

**ClineSR 提建议，Code 做决定。**

任何可以用确定性规则表达的判断，**不得**交给 ClineSR。

### 5.2 归属明确的职责

**ClineSR 负责：**
- 根因分析（自由文本推理）
- Patch 生成（代码生成）
- 叙述性总结
- 模糊边界决策

**Code / Tool 负责：**
- 所有 schema validation
- 所有阈值判断（如 regression bool）
- 所有枚举值映射
- 所有跨字段一致性校验
- 所有 budget / timeout 判断
- 所有白名单/黑名单路径检查
- 所有影响路由决策的关键标签

### 5.3 违反边界的后果

不符合 Contract，Review 阶段被打回。

### 5.4 ClineSR 输出的信任级别

| 字段 | 信任级别 |
|---|---|
| `decision` 枚举值 | 低（必须校验 allowed_actions）|
| `suspected_root_cause` 文本 | 中（可展示，不可作为分支依据）|
| `confidence` 数值 | 低（参考用）|
| `patch_hint` / `patch` | 低（必须 Tool 校验后才能 apply）|

### 5.5 Cognitive Layer Extension Points（v0.7 新增）

为后续接入认知增强基础设施预留接口。Phase 1A/1B 阶段所有字段为空对象 `{}`。

**ClineSR 输入 schema 必须包含 `prior_context` 字段**：

```json
{
  "agent_type": "compiler",
  "role_profile": {...},
  "workspace_metadata": {...},
  "compressed_observation": {...},
  "stage_context": {...},
  "budget": {...},
  "prior_context": {
    "known_issue_matches": [],
    "evidence_packet_summary": null,
    "similar_failures": [],
    "recent_patches": [],
    "team_conventions": [],
    "callers_of_affected_symbols": [],
    "type_dependencies": [],
    "change_impact_scope": null
  }
}
```

**字段说明**：

| 字段 | 来源 | 引入时机 |
|---|---|---|
| `known_issue_matches` | Known Issues DB | **Phase 1A** |
| `evidence_packet_summary` | Code Navigation & Evidence Infrastructure | **Phase 1A** |
| `similar_failures` | Memory Infrastructure | Phase 1.5 |
| `recent_patches` | Memory Infrastructure | Phase 1.5 |
| `team_conventions` | Memory Infrastructure | Phase 1.5 |
| `callers_of_affected_symbols` | Code Navigation 增强查询 | Phase 1A best-effort |
| `type_dependencies` | Code Navigation 增强查询 | Phase 1.5 |
| `change_impact_scope` | Code Navigation + Memory 联合分析 | Phase 1.5 |

**版本演进规则**：未来引入新 prior_context 字段时，Contract 升级次版本号；已有字段含义不可变。

### 5.6 Raw Log / Raw Data 硬约束（v0.7 新增，v0.7.2 加 excerpt 例外，v0.7.3 统一阈值）

**这是架构级硬约束**：

> **任何 FULL 原始日志、原始数据、原始文件内容禁止直接进入 LLM prompt。**
> **但 bounded + redacted + source-linked 的 log_excerpt（受控片段）可以作为 Evidence Packet 的一部分进入 LLM prompt。**

#### 5.6.1 禁止行为

- ❌ 把完整 `compile.log` 内容拼到 Cline prompt 里
- ❌ 把完整 source file 内容拼到 prompt 里（除非是 < 100 行的 focused snippet）
- ❌ 把完整 benchmark raw output / logcat / strace 拼到 prompt 里
- ❌ 把 device 完整 dmesg 拼到 prompt 里
- ❌ 多个 small excerpt 实际上拼成一个大 log（绕过 excerpt size 约束）

#### 5.6.2 允许行为（v0.7.2 明确）

- ✅ 经过 `summarize_compile_log` 处理后的 structured error events
- ✅ Evidence Packet（精选的相关代码片段 + 上下文 + negative_facts）
- ✅ 经过 token budget 控制的 compressed observation
- ✅ **Evidence Packet 中的 `log_excerpt` 字段**——必须满足以下约束（v0.7.2 例外条款）：

##### log_excerpt 字段约束（v0.7.2 新增）

1. **必须在 Evidence Packet 内**（由 EvidenceCollector 产出），不能在 prompt 其他位置
2. **必须 redacted**（经过 secret/env redaction filter）
3. **必须 bounded**：
   - 单 excerpt ≤ 3000 字符
   - 整个 Evidence Packet 中 excerpt 总和 ≤ 6000 字符
   - 单 Evidence Packet 最多 3 个 log_excerpt
4. **必须 source-linked**：含 `source_file`、`line_range`、`reason` 元数据
5. **必须有明确 reason 枚举**：`template_error_context` / `macro_expansion` / `linker_context` / `nested_include` / `generated_code_origin` / `benchmark_outlier_context`

详细 schema 见 CNEI 文档 2.1 + Compiler A5.2 + Benchmark B5.5。

#### 5.6.3 实施层面（v0.7.3 修订：统一阈值，消除 5000/3000/6000/20480 混乱）

**统一阈值体系**（v0.7.3 — 解决 Compiler A5.2 代码骨架 `20480 bytes` 与 Contract `5000 字符` 的冲突）：

| 层级 | 限制 | 单位 | 说明 |
|---|---|---|---|
| L1 单 log_excerpt 上限 | **3000 字符** | 字符（character） | EvidencePacket 内单段 excerpt（见 5.6.2） |
| L2 整 packet excerpt 总和 | **6000 字符** | 字符 | 单 EvidencePacket 所有 excerpt 累加（见 5.6.2） |
| L3 RawDataDetector 触发阈值 | **6000 字符** | 字符 | 与 L2 对齐：不在 excerpt 结构内的连续 raw 内容超此值即判泄漏 |

**统一单位为「字符（character）」**，不再用 byte。原 Compiler A5.2 代码骨架的 `DEFAULT_SIZE_THRESHOLD_BYTES = 20480` 废弃，改为 `DEFAULT_RAW_DATA_THRESHOLD_CHARS = 6000`。

`ClineAdapter.call_cline()` 入口必须有 **Raw Data Detector**：

- **场景 A**（绝对禁止）：检测 prompt 中是否有**超过 6000 字符**（或 200 行，取先到者）的连续 raw 风格内容（含 `file:line:` 模式、stack trace、error 关键词密集等特征），且**不在** EvidencePacket.log_excerpt 字段内 → 抛 `RawDataLeakageError`
- **场景 B**（允许）：内容在 EvidencePacket.log_excerpt 字段内**且**符合 5.6.2 约束（单段 ≤ 3000、总和 ≤ 6000、最多 3 段）→ 允许通过
- **场景 C**（防绕过）：多个 small excerpt 累加超过 6000 字符（即使每段 < 3000）→ 抛 `RawDataLeakageError`（对应 5.6.1 "多个 small excerpt 拼成大 log"）
- 命中场景 A/C 则落 `raw_data_leakage` FailureEnvelope

**阈值对齐逻辑**：RawDataDetector 触发阈值（L3=6000）= 合法 excerpt 总和上限（L2=6000）。这样合法的满额 EvidencePacket 不会误判，而任何超过合法上限的 raw 内容必然触发，无灰色地带。

- 违反此约束的 Agent 设计在 Review 阶段被打回

#### 5.6.4 各 Agent 的实施

- **Compiler Agent**（A5.2）：允许 EvidencePacket 含 log_excerpt（template error / macro expansion 等）
- **Benchmark Agent**（B5.5）：同样允许 EvidencePacket 含 log_excerpt（benchmark outlier context 等）
- **未来 UT/Review/CI Agent**：相同规则

**这条约束影响：token 经济性、安全性、信号噪声比、整个系统的可解释性**。例外条款（5.6.2）是工程上必要的妥协，但每条 excerpt 都被严格约束。

---

## 6. Agent Interface Contract

### 6.1 每个 Agent 必须暴露

```python
class Agent(Protocol):
    agent_type: str
    agent_version: str

    def run(self, task: TaskInput) -> AgentResult: ...
    def describe(self) -> AgentDescriptor: ...
```

### 6.2 TaskInput 最小必要字段

```json
{
  "task_id": "CMP-000123",
  "parent_task_id": null,
  "agent_type": "compiler",
  "incoming_handoff_id": null,
  "payload": { },
  "constraints": {
    "budget": { },
    "deadline_iso": null
  }
}
```

### 6.3 AgentResult 最小必要字段

```json
{
  "task_id": "CMP-000123",
  "status": "success",
  "agent_type": "compiler",
  "primary_artifact": { "type": "artifact_ref", "...": "..." },
  "all_artifacts": [ ],
  "failure_envelope": null,
  "outgoing_handoffs": [ ],
  "trace_ref": {
    "type": "artifact_ref",
    "task_id": "CMP-000123",
    "relative_path": "trace.json",
    "schema": "trace.v1",
    "content_hash": "sha256:..."
  },
  "token_usage": {
    "total_in": 12450,
    "total_out": 2380
  }
}
```

**强约束**：
- `trace_ref.relative_path` 必须为 `"trace.json"`
- `trace_ref.task_id` 必须等于顶层 `task_id`
- `token_usage` 必填（v0.7 新增）

### 6.4 AgentDescriptor

```yaml
agent_type: compiler
agent_version: 5.2.0

team_contract_compatibility: ">=0.7,<0.8"
payload_input_schema: "compiler_task_input.v1"
payload_output_schemas:
  - "build_report.v1"
  - "issue_fix_report.v1"

accepts_reasons:
  - compile_requested
  - rebuild_verify_requested
produces_reasons:
  - compile_failed
  - functional_verify_requested
  - performance_verify_requested
required_inputs:
  - workspace_snapshot
  - build_target
  - env_profile

replay_safe: true

# v0.7 新增：执行环境声明
execution_backends:
  - host_shell
device_backends: []  # Compiler 不接触 device

# v0.7 新增：token 约束声明
token_constraints:
  max_tokens_per_call: 8000
  max_tokens_per_task: 50000
  evidence_packet_max_tokens: 4000
```

---

## 7. LangGraph-Compatibility 要求

### 7.1 Agent 必须是 pure function 式

- 不依赖全局可变状态
- 相同 TaskInput 多次调用得到等价结果
- 不自己发起对其他 Agent 的调用

### 7.2 State 必须可序列化

- TaskInput / AgentResult / HandoffRequest 必须纯 JSON 可序列化
- 禁止传递 Python 对象引用、文件句柄、数据库连接
- 所有 workspace 状态通过 artifact_ref 引用

### 7.3 失败必须显式

- 任何失败通过 FailureEnvelope 表达
- `BudgetExceeded` 是唯一允许在 Agent 内部抛出的特殊异常

### 7.4 Checkpoint 友好

- 状态机每个转移点，内存状态必须可被完整序列化
- MVP 阶段不强制实现，但设计必须为此预留

### 7.5 Replay-safe（幂等重放）

- 同一 TaskInput 重复触发不得产生重复副作用
- Artifact 写入以 `task_id + relative_path` 为幂等键
- Handoff 发送以 `source_task_id + reason + target_agent` 为去重键
- 外部副作用以 `task_id` 为幂等键

---

## 8. 安全与执行约束（v0.7 新增整节）

### 8.1 ExecutionAdapter 多 Backend 支持

`ExecutionAdapter` 是 Protocol，不同 backend 共存：

| Adapter | 用途 | Phase |
|---|---|---|
| `HostShellAdapter` | x86 工作站本地 shell | Phase 1A |
| `DeviceAdapter` | Tizen 开发板远程操作 | Phase 1B |
| `DockerSandboxAdapter` | 容器隔离 | Phase 2+ |

**`DeviceAdapter` 子类型**：

- `SdbDeviceAdapter`（Tizen 标准）
- `SshDeviceAdapter`（备选）
- 两者**接口完全一致**，由用户配置选择

**Agent 在 AgentDescriptor 中声明依赖**：

```yaml
execution_backends: [host_shell]      # Compiler 只用 host
device_backends: []                    # Compiler 不用 device

# Benchmark Agent:
execution_backends: [host_shell]
device_backends: [sdb, ssh]            # Benchmark 两种都支持
```

### 8.2 Skill 概念定义

**Skill** 是 Coding System 引入的**用户扩展机制**，特定于 Benchmark Agent。

**Skill vs Tool 区分**：

| 维度 | Tool | Skill |
|---|---|---|
| 谁写 | Agent 开发者（Codex / 内部）| Agent 用户（Tizen 开发人员）|
| 何时调用 | Agent 内部固定流程 | Tool 按用户配置加载执行 |
| 审计 | 走 Cognitive Boundary review | 必须有 Manifest，且代码 user-authored but runtime-restricted（见 8.4）|
| 加载 | Agent 启动时 import | 运行时从配置目录扫描注册 |
| 例子 | `run_benchmark_skill_set` | "video_player_startup" |

**Skill 等价于业界其他体系的 Plugin**。具体设计见《Benchmark Skill 框架》（文档 07）。

### 8.3 Skill Runtime 强制约束

**Skill 必须有 Manifest（运行时强制 enforce，不只是文档）**：

- `skill.yaml`：声明权限、超时、metrics schema、artifacts schema
- `skill.py`：实际执行代码

**运行时 enforcement**：

- 未在 Manifest 声明的权限不可使用 → 抛 `permission_denied`
- 超时必须 kill → 抛 `skill_timeout`
- 输出必须符合 metric schema → 抛 `metric_schema_mismatch`
- artifact 写入必须在 workspace 内 → 抛 `permission_denied`
- destructive operation 必须显式声明 `side_effects` → 否则拒绝执行

**Skill Card 概念**：

LLM 不读完整 `.skill.py` 源码。LLM 看到的是从 Manifest 提取的 **Skill Card**：

```
Skill: video_player_startup
Purpose: measure cold/warm startup time of video player on Tizen device
Inputs: app_id, video_file, repeat_count
Outputs: startup_time_ms, failure_rate, logs
Risk: launches app and clears app cache (declared side_effect)
Platforms: tizen_device
```

这避免 token 爆炸 + 安全风险。

### 8.3.1 Skill 代码限制精确化（v0.7.1 新增）

**核心原则**：

> Skill code is **user-authored but runtime-restricted**.

具体含义：

**用户可以做的**：

- 在 `skill.py` 中实现 `setup() / run() / teardown()` 的业务逻辑
- 使用 Python 语法、第三方库（在 Manifest `dependencies` 中声明）
- 实现复杂的指标采集、状态管理、错误处理

**用户必须通过受控 SDK 做的**（不允许直接调用底层 API）：

| 操作类型 | 必须用受控 API | 不允许 |
|---|---|---|
| 在 device 上执行命令 | `ctx.device.shell(cmd)` | `subprocess.run(["sdb", "shell", ...])` |
| 在 host 上执行命令 | `ctx.host.shell(cmd)` | `subprocess.run([...])` / `os.system(...)` |
| 文件读写 | `ctx.workspace.read(path)` / `ctx.workspace.write(path)` | `open(path)` 直接读写绝对路径 |
| Artifact 落盘 | `ctx.artifacts.save(name, data)` | 直接写文件系统 |
| 网络访问 | `ctx.network.fetch(url)`（仅当 manifest 声明 `network: true`）| `requests.get(...)` / `urllib.request.urlopen(...)` |
| 环境变量访问 | `ctx.env.get(name)` | `os.environ[...]`（绕过 redaction）|
| Push/pull 文件 | `ctx.device.push() / pull()` | 直接 sdb 命令 |

**Runtime Enforcement**（runtime 层强制 + best-effort 静态扫描）：

1. **Runtime 层强制**（必须 enforce）：
   - `ctx.*` 方法内部检查 Manifest 权限声明
   - 命令通过 `ctx.device.shell()` / `ctx.host.shell()` 走 allowlist / denylist 检查
   - workspace 访问限于 `ctx.workspace.root` 子目录
   - 网络访问受 `network: false` 控制

2. **静态扫描 best-effort**（加载时尝试检测）：
   - 加载 `skill.py` 前，扫描代码中是否含 `subprocess.` / `os.system` / `open(` 绝对路径 / `requests.` / `urllib.` 等
   - 命中则 emit warning event 到 trace，**不强制阻止加载**（用户可能用 import-but-not-call 的情况）
   - 加载后实际调用这些底层 API 时，进程会失败（因为 ctx 上下文是 sandboxed namespace）

3. **文档要求**：
   - Skill 模板和文档**必须明确指引开发人员只用 ctx API**
   - 提供违规检测工具：`benchmark-agent lint-skill <skill_dir>`

**为什么 Phase 1B 是"best-effort"而不是完全沙箱**：

- Phase 1B 不引入完整的 Python 沙箱（如 RestrictedPython）—— 那是 Phase 1.5+ 的事
- 100 人内部使用场景，信任度比公开平台高
- 通过"受控 API 引导 + best-effort 检测 + 文档约定"达成实用的安全边界

#### 8.3.1.1 Phase 1.5 升级路径（v0.7.2 新增）

ChatGPT review 指出："Phase 1B 软，但要写明 Phase 1.5 必须升级"。

**Phase 1B 阶段（warning 模式）**：

- 静态扫描检测到 `subprocess.` / `os.system` / `open(<absolute_path>)` / `requests.` / `urllib.request.urlopen` → **emit warning event**，不阻止加载
- 真正调用时通过 sandbox namespace 自动失败

**Phase 1.5 升级（block 模式，硬约束）**：

| 检测项 | Phase 1B 行为 | Phase 1.5 行为 |
|---|---|---|
| `subprocess.run / Popen / call` | emit warning | **加载时 block，拒绝注册 Skill** |
| `os.system` | emit warning | **block** |
| `open(<absolute_path>)` 直接读写 | emit warning | **block**（必须通过 `ctx.workspace.*`）|
| `requests.* / urllib.request.urlopen` 等网络访问（未声明 network: true）| emit warning | **block** |
| `reboot` / `rm -rf` / `killall` / `systemctl` 等 destructive command | 需 Manifest `side_effects` 声明 | **必须显式声明，否则 hard fail（含 Phase 1B）** |

**真正的 sandbox 隔离**：

- Phase 1.5 引入 **容器化 Skill 执行**（每个 Skill 在独立容器内运行）
- 文件系统通过 bind mount 限制访问范围
- 网络通过 network namespace 控制
- 这是 100 人推广前的必备硬化

**为什么 Phase 1B 不直接做容器化**：

- Phase 1B 验证用户的 Skill 编写体验，不验证安全边界
- 内部 5-10 人验证场景，信任度高
- 容器化增加 Skill 调度复杂度（开发板上跑 Skill 时容器化困难）

**关键承诺**：Phase 1.5 实施阶段，Skill Runtime 升级必须在推广 100 人**之前**完成，不可延后。

### 8.4 Build System Awareness

**Compiler Agent 必须支持的 Build System Backend**：

| Backend | Phase |
|---|---|
| `cmake` + `ninja` | Phase 1A |
| `make` | Phase 1.5 |
| `gbs`（Tizen Git Build System）| Phase 1.5 |

接口在 Phase 1A 必须预留，即使实现推到 Phase 1.5。

### 8.5 Secret / Env Redaction（v0.7.1 修订：分级处理）

所有跨层数据传递（artifact 落盘、trace 记录、LLM prompt 构造、stdout 输出）必须经过统一 redaction filter。

**统一 redaction filter 实现**：

- 在 `agents/base/redaction.py` 提供 `redact(text, context) -> RedactionResult`
- 所有 `ArtifactManager.save_*`、`TraceWriter.emit`、`ClineAdapter.call_cline`、stdout writer 入口调用

#### 8.5.1 检测模式（按严重程度分级）

| Level | 模式 | 例子 |
|---|---|---|
| **L1** | Env vars / username / hostname / 本机 IP | `USER=alice`、`HOSTNAME=dev-tm1` |
| **L2** | Token / API key / private key 等 | `Bearer eyJ...`、AWS keys、`-----BEGIN PRIVATE KEY-----`、GitHub PAT |
| **L3** | 高危：源代码授权 token / 商业敏感凭据 | License key、enterprise SSO token、SSH key with passphrase |

#### 8.5.2 分级处理策略（v0.7.1 核心新增）

| 检测时机 | 检测内容 | 处理 |
|---|---|---|
| **artifact 写入 / trace 记录** | L1 命中 | redact 后继续写入，emit `info` event（不阻塞） |
| **artifact 写入 / trace 记录** | L2 命中 | redact 后继续写入，emit `warning` event |
| **artifact 写入 / trace 记录** | L3 命中 | redact 后继续写入，emit `error` event，task 标记 sensitive |
| **LLM prompt 构造前** | L1 命中 | redact 后继续 |
| **LLM prompt 构造前** | L2 / L3 命中 | redact 后继续，但 emit `warning` event；如果 redact 后仍含可疑模式，则 **hard fail**（`secret_leakage_detected`）|
| **redaction 后二次扫描** | 任意 secret 残留 | **hard fail**（`secret_leakage_detected`），停止后续处理 |

**说明**：

- 大多数场景是 redact 后继续（不阻塞工作流）
- "redact 后继续"是因为 L1/L2 在编译/benchmark 日志中频繁出现（如环境变量、build path 中的 user 名），如果每次都 fail 系统会一直挂
- 但**进入 LLM prompt 时**，redact 后必须再扫一次—— 如果还检测到 secret 模式，说明 redactor 漏掉了，**这种情况必须 hard fail** 避免泄漏给 LLM provider
- L3 的命中在 trace 中记 error event，便于事后审计

#### 8.5.3 替换格式（v0.7.2 修订：路径局部替换）

**普通 secret（token / key / password 等）**：

```
原文: GITHUB_TOKEN=ghp_abc123def456
脱敏: GITHUB_TOKEN=[REDACTED:L2:github_pat]
```

保留**类型 hint**让 LLM 知道这里是什么（不影响理解），不保留具体值。

**路径类内容（v0.7.2 新增局部替换规则）**：

Kimi review 指出，把整个路径段替换掉会破坏路径结构，干扰 LLM 理解。例如：

```
原文: BUILD_DIR=/home/john/tizen/build
旧脱敏（v0.7.1）: BUILD_DIR=[REDACTED:L1:USER]    ← LLM 看不到路径结构
新脱敏（v0.7.2）: BUILD_DIR=/home/[REDACTED:L1:USER]/tizen/build    ← 保留路径结构
```

**路径局部替换规则**：

| 路径模式 | 替换策略 |
|---|---|
| `/home/<user>/...` | 替换 `<user>` → `[REDACTED:L1:USER]`，保留 `/home/.../...` |
| `/Users/<user>/...` | 同上 |
| `C:\Users\<user>\...` | 同上 |
| `~<user>/` | 替换 `<user>` |
| 含 hostname 的路径 | 只替换 hostname 段 |

**实现要求**：

- 在 redaction filter 中，对路径类内容**只替换敏感段**（user / hostname），**保留目录结构**
- 多次出现同一 user / hostname 时使用**一致的 placeholder**（如 `[REDACTED:L1:USER]` 总是指代同一个 user），让 LLM 能识别路径间关系
- 非路径类的 user / hostname 仍然整段替换（如 `LOGGED_IN_USER=john`）

#### 8.5.4 Allowlist（v0.7.2 增强 regex 支持）

#### 8.5.5 Allowlist

某些"看起来像 secret 但实际不是"的内容（如固定常量、公开标识符）可在 `redaction_allowlist.yaml` 中声明跳过：

```yaml
allowlist:
  - pattern: "TIZEN_PUBLIC_KEY_ID=.*"  # 公开 ID，不脱敏
  - regex: "^GIT_COMMIT=[0-9a-f]{40}$"  # commit hash 不脱敏
```

---

## 9. 版本管理

- 本文档变更必须递增版本号
- 任何 breaking change 必须升级次版本号
- 各 Agent 在 `team_contract_compatibility` 中声明兼容范围

---

## 10. 未在本文档覆盖的内容

故意不在本文档定义，留给后续：

- Team Orchestrator 具体实现（LangGraph 代码）
- 各 Agent 的内部状态机
- 具体的 Tool 设计
- 具体的 Prompt / Role Profile
- 冲突仲裁策略
- 具体的 HITL 流程
- 具体的重试 / 回退策略

---

## Appendix A：Agent 设计文档的对齐要求

任何 Agent 的设计文档必须明确列出与本 Contract 的对齐情况：

- Task ID 格式遵守 1.1
- TaskInput / AgentResult / HandoffRequest 遵守本文档 schema
- 所有 artifact 使用结构化 artifact_ref
- trace.json + events.jsonl 落盘到 `artifacts/{task_id}/`
- AgentResult 包含 `outgoing_handoffs` / `trace_ref` / `token_usage` 字段
- FailureEnvelope 支持 Team-level failure_class（含 v0.7 新增）
- 实现 `describe()` 返回 AgentDescriptor（含 v0.7 新增字段）
- 声明 `team_contract_compatibility` 版本范围
- 满足 replay-safe 约束
- ClineSR 输入包含 `prior_context` 字段（v0.7 新增，可为空对象）
- **遵守 Raw Log/Data 硬约束**（v0.7 新增，5.6 节）
- 通过 secret/env redaction filter 写入所有 artifact / trace（v0.7 新增）

---

## Appendix B：术语表（v0.6 引入，v0.7 扩充）

| 术语 | 定义 |
|---|---|
| **Agent** | 长期存在、可被调度的工程能力组件（Compiler Agent 等） |
| **Tool** | Agent 内部能力函数，开发者编写 |
| **Skill** | Benchmark Agent 的用户扩展机制，用户编写 |
| **Skill Card** | Skill 的 LLM 友好摘要（来自 Manifest） |
| **Evidence Packet** | 针对某编译错误精选的结构化证据（v0.7 引入） |
| **Known Issues DB** | 历史错误模式 + 修复模式的简单数据库（v0.7 引入） |
| **HostShellAdapter** | x86 本地 shell 执行 backend |
| **DeviceAdapter** | Tizen 开发板远程执行 backend（sdb/ssh） |
| **Raw Log/Data 硬约束** | 原始数据禁止直接进 LLM prompt 的硬约束（v0.7 引入） |

---

**文档结束**
