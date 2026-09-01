# 01 — Contract Specification（契约规格）

**版本**: v0.1 Draft（待三方 cross-review 后 draft freeze）
**状态**: 评审中
**上游依据**: docs/00_Framework_HLD_v1.0_draft_frozen.md（下称 HLD）。本文档只精确化 HLD 已冻结的语义（HLD 正文 18 处 `[01]` 标注 + 附录 B 六组清单），**不引入任何新架构决策**；凡与 HLD 冲突之处以 HLD 为准并作为本文档缺陷处理。
**读者**: 框架开发（Codex）、cross-reviewer、业务 Agent 开发者（§2/§4/§6 为二次开发者的主要接口面）。

---

## 0. 约定与版本规则

### 0.1 序列化与规范化
- 所有 schema 以 **pydantic v2** 模型交付于 `framework/contracts/`，本文中的类定义即实现蓝本；`model_config = ConfigDict(extra="forbid", frozen=True)` 为默认（可变工作对象显式豁免）。
- **规范化 JSON（canonical_json）**：UTF-8、键按 Unicode 码点升序、无多余空白、数值不带多余精度、禁止 NaN/Inf。凡"digest"均指 `sha256(canonical_json(obj))` 的小写十六进制，前缀 `sha256:`。
- 标识符格式：`run_id = "RUN-" + ulid`；`task_id = <AGENT前缀>-<6位序号>`（前缀注册见 §2.3）；`dispatch_id / activation_id / decision_id / token_id / correction_id = ulid`；ulid 一律 26 字符 Crockford Base32。
- 时间一律 UTC ISO-8601 毫秒精度；时长配置单位在字段名后缀标明（`_min` / `_sec`）。

### 0.2 Contract 版本
- 本文档定义 `contract_version`，语义化版本，当前 `1.0.0-draft.1`；draft 期破坏性修改允许但须递增 `draft.N` 并记 decision_log；v1.0.0 按 HLD D10/G6 三条件宣布。
- Agent 以 PEP 440 specifier 声明兼容区间（`contract_requires`，HLD §5.1.1）；框架装配时以本文档发布的 `contracts` 包版本校验。
- `dsl_version`（整数）独立演进，当前 **1**；pipeline 文件声明的 dsl_version 必须被当前框架支持。

### 0.3 术语
沿用 HLD §3，本文不重复定义；正文以 `（HLD §x.y）` 回标依据。

---

## 1. Pipeline DSL v1 与静态校验（HLD §4.2）

### 1.1 文件 schema

```python
class GateType(StrEnum): hitl = "hitl"; threshold = "threshold"

class NodeSpec(BaseModel):
    # 三选一：agent_type | gate | broker（互斥，校验 V-01）
    agent_type: str | None = None          # 已注册 agent_type
    mode: str | None = None                # 透传给 Agent 的节点级配置键（如 review 的 static/final）
    gate: GateType | None = None
    metric: str | None = None              # threshold 专用：`<node_name>.<metric_key>`
    op: Literal["<=", ">=", "<", ">", "=="] | None = None
    value: float | None = None
    broker: Literal["release"] | None = None
    terminal: bool = False
    success_on: list[str] | None = None    # terminal=True 时必填（V-14）
    retry: RetrySpec | None = None         # {on: list[SysOutcome], max: int>=1}
    loop_limits: None = None               # 保留字段：dsl_version=1 禁用（环预算只在 loops，V-02）
    llm_budget: LLMBudget | None = None    # {max_tokens: int, on_exceed: "truncate"|"error"}
    config: dict[str, JsonValue] = {}      # 节点级业务配置，原样进 TaskInput

class LoopEdge(BaseModel): from_: str; to: str        # YAML 键名 from/to
class LoopSpec(BaseModel):
    id: str
    edges: list[LoopEdge]                  # 环由 edges 唯一定义（HLD §4.5）
    budget: LoopBudget                     # {max_rounds: int>=1, max_wall_clock_min: int>=1}

class JoinSpec(BaseModel):
    id: str
    wait_for: list[str]                    # 必须 ≡ 指向本 join 的路由源集合（V-08）
    timeout_min: int | None = None         # 缺省以 run_budget 为界
    to: str                                # 普通/特权节点名；不得为 join（V-10）

class RouteSpec(BaseModel):
    from_: str
    on: str                                # ∈ status 全集 ∪ gate outcome ∪ sys.*（V-05）
    to: str | list[str]                    # 节点名 | "fail_safe" | "join:<id>"

class PipelineSpec(BaseModel):
    pipeline: str                          # 名称，[a-z0-9_]+
    dsl_version: Literal[1]
    nodes: dict[str, NodeSpec]             # 节点名 [a-z0-9_]+，禁用保留名（V-03）
    entry: str
    loops: list[LoopSpec] = []
    joins: list[JoinSpec] = []
    routes: list[RouteSpec]
    default_route: Literal["fail_safe"]    # dsl_version=1 固定值，必填
    run_budget: RunBudget                  # {max_wall_clock_min: int>=1}
    snapshot_policy: Literal["pin_at_start"] = "pin_at_start"
```

`pipeline_digest = sha256(canonical_json(PipelineSpec))`（YAML 解析为模型后取 digest，与源文件排版无关）。

### 1.2 保留名与固定语义
- 保留节点：`fail_safe`（HLD §3）；保留命名空间：`sys.*`、裸名 `fail_safe`、前缀 `join:`。
- `broker: release` 节点：outcome 集固定 `{released, release_failed}`，**无出边**（V-13）；终态由 §2.2 固定映射 ledger 级关闭（HLD §4.2.5）。
- gate outcome 封闭枚举：`hitl → {approved, rejected, gate_expired}`；`threshold → {pass, fail}`（HLD §4.4）。
- 系统 outcome：`sys.crash | sys.timeout | sys.invalid_result | sys.error`（HLD §4.3.2）。

### 1.3 静态校验规则（编号即实现与测试的规则 ID；全部违规 = 拒绝加载并报 `PipelineValidationError(rule_id, locus)`）

| ID | 规则（依据） |
|----|--------------|
| V-01 | 每个 NodeSpec 恰为 agent/gate/broker 三型之一；threshold 必填 metric/op/value；hitl 不得带 metric（§4.2.2） |
| V-02 | dsl_version=1 下 NodeSpec.loop_limits 必须缺省；环预算仅经 LoopSpec.budget（§4.5） |
| V-03 | 节点名不占用保留名/命名空间；entry 存在且唯一；无不可达节点（§4.2.2/§4.2.6） |
| V-04 | agent_type 已注册且通过 conformance attestation（§11.3）；contract_requires 兼容 |
| V-05 | 每条 route.on ∈（from 节点的 status 全集 ∪ 其 gate outcome 集 ∪ sys.*）；status 拼写错在此拒绝（§4.2.3） |
| V-06 | 穷尽性：每个节点的业务 status 逐条有路由或被 default_route 覆盖；default_route 必填（§4.2.3） |
| V-07 | 每个可达环均被某 LoopSpec.edges 精确覆盖且带 budget；routes 不得含环归属标注（§4.5） |
| V-08 | join.wait_for ≡ {r.from_ : r.to == "join:"+id}（集合相等；§4.2.4） |
| V-09 | 同一 source 每 activation 至多一次送达：不存在两条同 from 路由指向同一 join（§4.2.6） |
| V-10 | join.to 不得为 join（禁链式）；join 来源须由**同一次显式 fan-out** 的不同分支派生，来源集在分支间构成划分；共同支配不得替代共同 fan-out（§4.2.4/§4.2.6） |
| V-11 | **共同到达性**：对每个 join 来源 s，从其 scope fan-out 到 s 的路径上，每个节点的每个 outcome 分支须满足：可达 s ∨ 到 Run 终局（fail_safe/terminal/release）∨ 经声明环边回流；违者拒绝（§4.2.6） |
| V-12 | **环边双约束**：作为 V-11 第三分支例外的环边，①回流路径必然重经该 join 的共同 fan-out（重派全部来源分区）；②重经自身 activation 的共同 fan-out 之前不得先重经任何祖先 activation 的共同 fan-out（§4.2.6 条件(iii)） |
| V-13 | release：所有到 release 的路径必经 hitl；release 可达路径上的 hitl 的 approved 出边直达 release；release 无出边；含 release 的 pipeline 中 ci 类节点位于该 hitl 上游（§4.2.5） |
| V-14 | terminal=True 节点必有非空 success_on ⊆ 其 status 全集（§4.2.2） |
| V-15 | hard-required 依赖与 threshold metric 来源：生产节点存在且**支配**消费节点（每条到消费节点的路径先经生产节点），threshold 消费同 series 结果（§4.2.6） |
| V-16 | retry.on ⊆ {sys.crash, sys.error, sys.timeout}（§4.3.2） |
| V-17 | hitl 分型静态判定：release 可达路径上的 hitl 为 release-approval 型，其余 plain-decision 型；类型进编译产物供运行时选择审批协议（§4.4） |

### 1.4 编译产物
DSL 编译输出 `CompiledPipeline`（进 execution manifest）：节点表（含 hitl 分型、release 标记）、路由表、环表（edges→loop_id 反查）、join 表（scope fan-out、来源划分）、支配关系缓存。schema 内部件，不对业务暴露。

---

## 2. 状态机与消息（HLD §4.3/§6）

### 2.1 Run 状态机命令/guard 表

状态集：`created | awaiting_patch | queued | running | paused | publishing | closed(reason)`；reason ∈ `{succeeded, fail_safe, cancelled, snapshot_error}`。

| # | 命令（发起者） | 前置状态 guard | 附加 guard | 目标状态 |
|---|----------------|----------------|-----------|----------|
| C-01 | create_run（Skill） | — | pipeline 校验通过；单机资源水位达标（HLD §7.6.3） | created |
| C-02 | snapshot_pin（编排） | created | 拉取成功 → 写 snapshot manifest + execution manifest | awaiting_patch |
| C-03 | snapshot_pin 失败（编排） | created | — | closed(snapshot_error) |
| C-04 | submit_patch（Skill） | awaiting_patch | series 对 snapshot 可应用；单 Run 仅一次（重复 → E-SKILL-409） | queued（run_budget 起算） |
| C-05 | awaiting_patch TTL（编排定时） | awaiting_patch | 超时（默认 24h） | closed(cancelled) |
| C-06 | slot_acquire（编排） | queued | FIFO 队首且执行槽空闲 | running |
| C-07 | gate_wait_only（编排） | running | 仅剩 gate 等待、无可运行工作 | paused（释放执行槽） |
| C-08 | gate_resolve（Approval 经 outbox） | paused ∨ running | decision_id 未消费；gate CAS waiting→resolved | queued（resume 入 FIFO） |
| C-09 | authorization_consume（broker RPC） | running | §5.2 授权全绑定校验 + 未核销未过期；同事务核销 | **publishing** |
| C-10 | release_outcome（broker） | publishing | released ∨ release_failed；§2.2 固定映射 | closed(...) |
| C-11 | probe_reconcile / 人工裁决（编排/裁决） | publishing | HLD §8.3 裁决协议 guard（broker 静默等） | closed(...)（或保持） |
| C-12 | fail_safe_enter（编排） | running | 保留节点执行：聚合证据 + FeedbackReport | closed(fail_safe) |
| C-13 | cancel_run（Skill 创建者/运维） | created…paused | publishing 期仅登记 pending（§2.2） | closed(cancelled) |
| C-14 | administrative_finalize（编排 ledger 级） | 任意非 closed、**非 publishing** | D12 不匹配/活跃引擎先停（HLD §4.3.3）；probe 对账后 FeedbackReport（ledger 级生成） | closed(fail_safe) |
| C-15 | terminal_success（编排） | running | terminal 节点 outcome ∈ success_on | closed(succeeded) |

publishing 为 administrative finalize 的状态级例外（HLD §8.3）：C-14 在 publishing 上仅登记 pending。非法命令 → `IllegalTransition` 拒绝并审计，Run 状态不变。

### 2.2 release 固定终态映射（ledger 级，不经 DSL 路由；HLD §8.3）

broker outcome 优先：`released` → closed(succeeded)（pending 事件记入 Run 终局摘要）；`release_failed` → 按序应用 pending：administrative finalize（→ closed(fail_safe) + 版本漂移 FeedbackReport）＞ cancel（→ closed(cancelled)）＞ fail_safe（→ closed(fail_safe)）＞ 均无 → closed(fail_safe) + ledger 级 release_failed FeedbackReport。series 更新仅记录。

### 2.3 Agent 注册与核心消息

```python
class AgentRegistration(BaseModel):
    agent_type: str; task_prefix: str          # 如 "compiler"/"CMP"；prefix 全局唯一
    status_set: frozenset[str]                 # 业务 status 全集，非空，不得含 "." 
    contract_requires: str                     # PEP 440
    hard_required_inputs: frozenset[str] = frozenset()   # report 类型名集合（V-15）
    capabilities_required: frozenset[str] = frozenset()  # 能力句柄需求（装配校验）

class TaskInput(BaseModel):
    run_id: str; task_id: str; dispatch_id: str; attempt: int
    node: str; node_config: dict[str, JsonValue]
    series_id: str; snapshot_id: str
    upstream: dict[str, ArtifactRef | None]    # 各 Report 类型名 → 引用；缺失=None（HLD §6.3）
    join_inputs: list[JoinInputItem] | None    # 仅 join 下游任务非空
class JoinInputItem(BaseModel):
    source_node: str; handoff_ref: ArtifactRef; series_id: str; task_id: str

class HandoffResult(BaseModel):
    task_id: str; status: str                  # ∈ 注册 status_set（否则 sys.invalid_result）
    series_id: str                             # 须为框架签发的当前值（§3.3）
    artifact_refs: dict[str, ArtifactRef]      # 键含所产 Report 类型名
    reason: str = ""; metrics: dict[str, float] = {}

class ArtifactRef(BaseModel):
    digest: str                                # "sha256:..."（内容寻址，HLD §7.5）
    kind: str                                  # "patch_series"|"build_report"|... 注册表见 §2.4
    media_type: str = "application/json"
```

### 2.4 Report 与产物 schema（公共头 + 类型体）

所有 Report 公共头：`{report_type, task_id, run_id, series_id, created_at, data_class}`（data_class 见 §5.3）。类型体（字段为冻结语义的最小充分集，实现可扩 `extra` 命名空间但不得复用既有键）：

- **BuildReport**：`succeeded: bool; targets_built: list[str]; revdep_scope: list[str]; failed_target: str | None; error_excerpt_ref: ArtifactRef | None; fix_patches: list[PatchAttribution]; rounds_used: int`
- **UTReport**：`passed: bool; board_id: str; suites: list[{name, passed, failed, skipped}]; failure_analysis_ref: ArtifactRef | None; fix_patches: list[PatchAttribution]`
- **BenchReport**：`baseline_ref: ArtifactRef; metrics: dict[str, {value: float, baseline: float, regression_pct: float}]; patch_relatedness_ref: ArtifactRef`（threshold gate 读 `benchmark.<metric_key>` 即 metrics[key].regression_pct）
- **ReviewReport**：`verdict: Literal["pass","concerns","block"]; findings: list[{severity, locus, summary, evidence_ref}]; consumed: dict[str, ArtifactRef | None]`（显式记录消费到的上游，含缺失标注——HLD §6.3）
- **FeedbackReport**（fail_safe/administrative finalize/release_failed 三源，ledger 级或保留节点生成）：`origin: Literal["fail_safe","admin_finalize","release_failed"]; rounds: list[RoundDigest]; all_patches: list[PatchAttribution]; reports: dict[str, ArtifactRef]; parent_run_id: str | None`
- **RunSummary（Run 终局摘要）**：`final_state: str; reason: str; pending_events: list[PendingEvent]; artifact_index_ref: ArtifactRef; corrections: list[CorrectionRef]`（HLD §3；corrections 见 §5.4）
- **PatchAttribution**：`patch_digest: str; repo_id: str; producer: {agent_type, task_id, round}; motivation: str`（HLD §6.4 逐段出处）

### 2.5 ReleasePlan / ReleaseManifest / 授权记录

```python
class ReleasePlan(BaseModel):
    run_id: str; series_id: str; tree_digest: str
    targets: list[ReleaseTarget]               # {adapter: "gerrit"|"github"|受限扩展名, repo, branch, action}
    squash: bool = False                       # HLD §6.4 发布期可配置
class ReleaseManifest(BaseModel):              # = ReleasePlan 规范化 + 环境绑定（HLD §8.2）
    snapshot_id: str; tree_digest: str; series_id: str
    targets: list[ReleaseTarget]
    pipeline_digest: str; exec_manifest_digest: str
# release_manifest_digest = sha256(canonical_json(ReleaseManifest))

class AuthorizationRecord(BaseModel):          # Ledger 行，非 bearer（HLD §3/§8.2）
    token_id: str                              # 高熵随机（ulid + 128bit 随机后缀）
    run_id: str; gate_instance_id: str; decision_id: str
    ci_plan_task_id: str; series_id: str; tree_digest: str
    release_manifest_digest: str; expires_at: datetime
    consumed_by_task_id: str | None = None; revoked: bool = False
```

失效规则（HLD §8.2）：series 推进事务 / Run 关闭 → `revoked=True`；过期消费 → broker 返回 `release_failed(reason="authorization_expired")`；核销 CAS：`consumed_by_task_id IS NULL AND NOT revoked AND now()<expires_at AND 全绑定字段与当前状态一致`，同事务置 consumed + Run→publishing（C-09）。broker task 恢复时 `consumed_by_task_id == 本 task` 视为有效（HLD §8.3）。

### 2.6 Execution manifest（HLD D12）

`{pipeline_digest, contract_version, framework_version, engine_version, agent_artifacts: dict[agent_type, digest], provider_policy_digest, dsl_version}`；provider_policy_digest 覆盖策略语义与端点身份/信任策略、不含凭据值。恢复/dispatch/审批/发布前复核，不匹配 → C-14（publishing 除外）。

### 2.7 Skill 协议（HTTP+JSON；HLD §6.5）

| 操作 | 请求 | 成功响应 | 主要错误 |
|------|------|---------|---------|
| POST /runs | `{pipeline_id, target_spec, request_id}` | `{run_id, snapshot_id, snapshot_manifest, queue_position?}` | E-SKILL-400 校验失败；E-SKILL-503 水位拒绝 |
| POST /runs/{id}/patches | `{series: [PatchItem], request_id}` | `{accepted: true, series_id}` | E-SKILL-409 已提交过；E-SKILL-422 不可应用（附首个失败 hunk 定位）；E-SKILL-413 超限 |
| GET /runs/{id} | — | `{state, node_progress, loop_counters, queue_position?}` | E-SKILL-404 |
| GET /runs/{id}/result | — | `{run_summary: RunSummary, feedback_report?: ArtifactRef, corrections: [...]}` | E-SKILL-409 未关闭 |
| POST /runs/{id}/cancel | `{request_id}` | `{state}` | E-SKILL-403 非创建者 |

`PatchItem = {repo_id, unified_diff, description}`；应用序 = snapshot manifest 序（HLD §7.6.2）。认证：静态 bearer；request_id 幂等（重复请求返回首个结果）；路径白名单与大小上限为部署配置。target_spec：`{repos: [repo_id] | "manifest:<name>", packages?: [..]}`——语义为 snapshot 拉取范围选择器，解析表随部署配置交付。

---

## 3. Activation 与 Series（HLD §4.2.4/§7.6.2）

### 3.1 activation 记录与传播

```python
class ActivationRecord(BaseModel):
    activation_id: str; run_id: str
    origin: Literal["root", "fanout", "loop"]
    origin_node: str | None                     # fanout/loop 的产生节点/环 id
    parent_activation_id: str | None            # root 为 None
    loop_vector: dict[str, int]                 # loop_id → 已通过次数（环计数向量）
    series_id: str                              # 产生时的 current series
    state: Literal["open", "superseded"]
```

传播规则（编译期可静态导出 fan-out 归属，运行期按下列规则赋 activation 上下文）：
1. **root**：Run 首次 dispatch（entry）事务内生成，`parent=None, loop_vector={}`。
2. **线性/分支中间边**：task 继承其 dispatch 所来边的 activation 上下文，不新建。
3. **fan-out**：`to: [a,b,...]` 分派事务内生成一个新 activation（子），`parent = 分派 task 的 activation`；全部分支送达共享之。
4. **loop**：声明环边分派事务内：(a) 触发 supersede 条件③——将采用环边的 task 所属 activation 及其**全部子孙**（沿 parent 链下行闭包）置 superseded、作废计时器；(b) 生成 loop activation，`parent = 被退役 activation 的 parent`（不加层），`loop_vector = 被退役者 loop_vector 该 loop_id 分量 +1`；(c) 环计数 +1 与预算检查同事务（超限改路 fail_safe，不生成）。
5. **join 消费**：原子整组消费后，下游 dispatch 的 activation 上下文 = 被消费 activation 的 **parent**（HLD §4.2.4）。
6. **替代 cohort**：环回流重经共同 fan-out 时按规则 3 生成，其 parent 即等于被退役者的 parent（由规则 4b + 3 组合保证，V-12 静态前提）。

supersede 触发条件与守卫照 HLD §4.2.4：①series 推进全量退役；②到达全 stale（①兜底）；③上述 4(a)。join 消费、下游分派、timeout handler 的 CAS：自身 open ∧ 祖先链（parent 闭包）无 superseded ∧ series 为 current；违者审计化 no-op / 分派拒绝。

### 3.2 join 到达与消费

到达键 `(run_id, join_id, activation_id, source_node)`；唯一约束，重复到达丢弃并审计。同键 series 与 current 不一致 → 标 stale 丢弃。全部 wait_for 源到达且 series 一致 → 单事务：置各到达 consumed + 生成下游 dispatch（父 scope）+ 作废该 activation 的 join 计时器。timeout 自该 activation 首个到达起算，口径同 §3.4。

### 3.3 series 推进（单事务；HLD §4.2.4/R3-03）

worker 数据面命令 `series_candidate_submit{candidate_patches, expected_parent_series_id}` 预登记（不改 current）；task 完成事务内一次完成：
1. CAS：`current_series_id == expected_parent_series_id`（失败 → task 结果拒绝，sys.invalid_result 处置——并发丢 patch 防护）；
2. 提交结果 + artifact 索引 + 幂等终态；
3. 写 series lineage（`new_series_id, parent_series_id, contributed_by_task, patches: [PatchAttribution]`）、推进 current 指针；
4. 计算并记录 tree_digest（§3.5）；
5. 失效：未核销授权 `revoked=True`、待审批项作废、旧 series open activation 全量 superseded（条件①）。

### 3.4 计时口径（HLD §4.5）

loop wall_clock / run_budget / join timeout 一律排除 Run 处于 paused 与 publishing 的时段；实现为 Ledger 记录暂停区间、检查时扣除。环计数语义：`max_rounds: N` = 环边允许通过 N 次，第 N+1 次通过请求在预算检查处拦截强制路由 fail_safe。

### 3.5 tree_digest 算法（纯算法、无需 worktree；HLD §7.6.2）

```
输入: snapshot_manifest = [{repo_id, commit}...]（按 repo_id 升序）,
      series lineage 至当前 series 的全部 patches（应用序）
line_i = repo_id + ":" + commit + ":" + sha256(该 repo 按序全部 patch_digest 拼接)
       （该 repo 无 patch 时第三段 = "-"）
tree_digest = "sha256:" + sha256("\n".join(line_i for 全部 repo 升序))
```
性质：仅依赖 snapshot 与 patch 内容序列，跨机可复算；与 worktree 实际 tree hash 的一致性由 BuildExecutor 应用校验兜底（HLD §7.6.1）。

### 3.6 snapshot manifest

`[{repo_id, remote, commit, path}]`，repo_id 升序规范化；`snapshot_id = sha256(canonical_json(manifest))` 截断 16 字节前缀 + "SNAP-"。跨仓应用按 manifest 序，任一仓失败整组回滚（HLD §7.6.2）。

---

## 4. 效应幂等（HLD §5.2）

### 4.1 键与调用

```python
def side_effect(effect_call_id: str, params: BaseModel, fn, repeat_seq: int | None = None): ...
# idem_key = sha256(canonical_json({run_id, dispatch_id, effect_class,
#                                   effect_call_id, effect_params_digest, repeat_seq}))
```
- `effect_call_id`：调用方提供、代码内稳定命名（`[a-z0-9_]+`）；conformance 静态检查每逻辑调用点唯一命名；同 task 内唯一在册。
- `effect_class`：由 fn 所属**注册效应类型**推导（§4.4）；自由函数不可包装（SDK 拒绝）。
- `effect_params_digest = sha256(canonical_json(params))`；params 内 ArtifactRef 以 digest 参与。
- `repeat_seq`：显式声明重复执行时由调用方给定迭代序；缺省 None。

### 4.2 记录状态机（六态）

`claimed → running → succeeded | failed`；对账产 `abandoned | unknown`。迁移表：

| 从\到 | running | succeeded | failed | abandoned | unknown |
|-------|---------|-----------|--------|-----------|---------|
| claimed | worker ack 后启动 | —（禁跳） | RPC 层失败 | 对账：未发生 / replay_safe 退役 | 对账：不可判定 |
| running | — | 效应完成 | 效应失败 | 对账：未发生 / replay_safe 退役 | 对账：不可判定 |
| succeeded / failed / abandoned / unknown | 终态不迁移（abandoned 之上重执行走**版本化新记录**，版本号 +1 同键） | | | | |

约束：succeeded 与 unknown **不得改写为 abandoned**（HLD §5.2）；claim 经 control-plane RPC ack 前效应不得启动（fail-closed）。

### 4.3 查找与对账

同键查找只命中非 abandoned 的最高版本记录：`claimed/running` → 按能力三支对账（可 probe → 成功迁 succeeded 复用 / 未发生迁 abandoned；无 probe 但 replay_safe → 退役 abandoned 后同键版本化重放；皆无 → unknown + sys.error）；`succeeded` → 直接复用（仅同参精确键命中，禁跨参复用）；`failed` → 按效应类别策略重试或上报。

attempt 启动序：编排层将上一 attempt 本 task 全部非终态记录逐条三支对账**定态**后，才 dispatch 新 attempt。**异参新键允许集合（枚举，仅辖跨 attempt 定态记录）**：succeeded/abandoned → 放行；unknown → task 已 sys.error 中止，无新键。干净终态 failed 依效应类别策略放行，不在此列。运行时拒绝：仅同一 attempt 内，同 call_id 存在未决记录时的异参新 claim → 拒绝，task 报 sys.invalid_result。

### 4.4 效应类型注册（能力契约）

```python
class EffectType(Protocol):
    effect_class: ClassVar[str]                  # 如 "build.gbs", "board.flash", "publish.broker"
    replay_safe: ClassVar[bool]
    def probe(self, params, record) -> ProbeResult | NotSupported: ...
class ProbeResult(BaseModel):
    happened: bool; result_descriptor: dict[str, JsonValue] | None   # happened 时据此补写完成记录
```
类别硬性要求（HLD §5.2/conformance）：`build.*` 必须可 probe；`board.*` 可 probe 或 replay_safe；`publish.*` 仅存在于 broker 进程（能力句柄清单显式排除，业务侧注册即拒绝）。

---

## 5. 安全接口（HLD §7.1/§8）

### 5.1 Control-plane 命令集（Unix socket + peer credential；HLD §8.5）

**worker 数据面 socket**（per-task socketpair，FD 注入；服务端由连接上下文推导 run/task 并校验租约；仅下列命令）：

| 命令 | 载荷要点 | 事务语义 |
|------|---------|----------|
| effect_claim | effect_call_id, effect_class, params_digest, repeat_seq | 写 claimed + 分配记录版本；ack 前禁执行 |
| effect_transition | idem_key, to ∈ {running, succeeded, failed}, result_descriptor? | 单行 CAS |
| trace_append | 事件批 | 追加 |
| artifact_stage | digest, kind, size | blob 已按提交协议落盘后登记暂存（lease） |
| series_candidate_submit | candidate_patches, expected_parent_series_id | 预登记（§3.3） |
| task_complete | HandoffResult | §3.3 完成事务（含 series CAS、artifact 索引转正、幂等终态） |

**approval socket**（Approval 服务 OS 用户）：`decision_submit{gate_instance_id, decision, decision_id, evidence_refs}`——release-approval 型附 ReleaseManifest，单事务 = 决定 + 授权记录 + gate CAS + resume outbox；plain 型无授权项（HLD §4.4）。
**broker socket**（broker OS 用户）：`authorization_consume{token_id, task_id, release_manifest_digest}`（C-09 事务）、`release_outcome{task_id, outcome, reason, remote_refs}`。
**裁决/修正命令**（特权运维用户）：`adjudicate{run_id, verdict ∈ confirm_released|confirm_not_released|keep_unknown, evidence_refs}`（guard：publishing ∧ 强制 probe 后 unknown ∧ confirm_not_released 另需 broker 静默确认）、`post_close_correction{run_id, correction: CorrectionRecord}`。
**出向**：编排→broker 调度端点仅接受编排进程 UID，请求绑定 run/task/manifest。
通用：全部命令幂等（request_id）；复合变更单命令单事务；resume outbox 消费端 inbox 去重（decision_id/outbox_id，durable dispatch 后 delivered）。

### 5.2 受限扩展发布 adapter 契约（HLD §8.3）

业务扩展 adapter 运行于**无凭据子进程**，输入 ReleaseManifest 只读视图，输出受限操作描述序列：
```python
class RestrictedOp(BaseModel):
    op: Literal["git_push", "gerrit_rest"]      # 框架凭据原语枚举，v1 仅此二种
    repo: str; ref: str
    payload_digest: str                          # 引用已入 artifact store 的推送内容
    fencing: dict[str, str]                      # 必含 run_id, token_id（HLD §8.3 迟到归因）
```
broker 校验描述与已核销 manifest 一致后以框架凭据原语执行；描述之外的一切（新目标、改 ref）拒绝并审计。官方 gerrit/github adapter 在 broker 进程内直接实现同一原语层。

### 5.3 数据密级（HLD D7/§7.1）

`DataClass = public < build_log < internal_code < secret`（全序）。标注责任：snapshot 读取器/BuildExecutor/KnowledgeProvider 等产出组件出生标注；聚合（EvidencePacket/消息/派生摘要/LLM 输出）取成员最大；API 无降级操作；**摘录组件负内容升级责任**（build_log 摘录内联源码行 → internal_code）。LLM 调用（含 cascade 每跳）：`payload_class ⊑ provider 授权集`（中心安全配置），违者拒绝并审计。持久化脱敏：secret 只记指纹。

### 5.4 修正与终局

```python
class CorrectionRecord(BaseModel):               # append-only（HLD §8.3）
    correction_id: str; run_id: str
    original_adjudication_id: str | None
    remote_refs: list[str]; evidence_refs: list[ArtifactRef]
    operator: str; disposition: str; created_at: datetime
```
原终态不可变；RunSummary.corrections 与 get_result 一并返回有效修正引用。

### 5.5 EvidencePacket（HLD §7.4）

`{facts: [str], negative_facts: [ToolFact], log_excerpts: [{ref, lines, data_class}], target_source_excerpt: {path, start, end, content} | None, confidence: float}`；产 patch 请求 target_source_excerpt 必非空（builder 校验）；`ToolFact = {tool, query, result}`（仅工具产出的否定性代码事实）；packet data_class = 成员最大；RawDataDetector 与体积上限为 builder 内置校验。

---

## 6. Conformance 挂钩（细则归 07）

本文档为 07 的判定依据源。07 须至少覆盖（映射 HLD §11.3）：V-01…V-17 逐条正反例（含 V-11/V-12 的互斥 outcome、分支内回环、跨祖先回环三反例与旗舰/子集两正例）；C-01…C-15 状态机 model-based；§4.2 迁移表全边 + 三支对账 × 六态 × 异参矩阵（含 failed 行）；§3.1 传播六规则与条件③级联/替代 cohort 断言；§3.3 series CAS 并发；§5.1 各 socket 权限隔离与跨 task 篡改拒绝；授权双消费/过期/漂移不烧授权；publishing pending 组合与裁决 E2E（证据缺失拒绝、broker 未静默拒绝、迟到检出→correction）；blob 提交协议逐点崩溃注入与 lease GC 并发。attestation 绑定 agent 制品 digest + contract_version + 套件版本。

---

## 7. 附录

- A1 开放项（不阻塞评审，随实现落定并回填）：task 序号分配器的持久化布局；trace.jsonl 事件类型全集（实现期从 SDK 埋点枚举导出）；Skill 错误码全集的 HTTP 映射表；CompiledPipeline 内部 schema。以上均为实现细节，不含语义决策。
- A2 与 HLD 的追溯矩阵：§1↔HLD §4.2；§2↔§4.3/§6/§8.2-8.3；§3↔§4.2.4/§7.6.2/§4.5；§4↔§5.2；§5↔§7.1/§8；§6↔§11.3。
- A3 变更记录：v0.1 初稿（HLD v1.0-draft-frozen 附录 B 全量落定）。
