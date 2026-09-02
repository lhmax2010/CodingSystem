# 01 — Contract Specification（契约规格）

**版本**: v0.3 Draft（v0.2 三方复审 NO-GO 后修订版，待第三轮复审）
**状态**: 复审中
**上游依据**: docs/00_Framework_HLD_v1.0_draft_frozen.md（下称 HLD）。本文档只精确化 HLD 冻结语义，不引入新架构决策；与 HLD 冲突以 HLD 为准并作为本文档缺陷处理。**例外一处**：V-13b 为 HLD 勘误 HLD-Q1 的形式化（首轮 Claude Code 登记、三方处置表确认走勘误通道），**已于第二轮三方一致批准生效**（规则与程序双表态全 GO），并回写 HLD 附录 A15 勘误注记。
**关联**: docs/review/ 下 01 系两轮处置表（首轮 57 条、次轮 47 条逐条处置）。

---

## 0. 约定、标识符与版本

### 0.1 canonical_json（唯一算法）
1. 输入为 pydantic v2 模型经 `model_dump(mode="json")` 的产物；仅允许类型：object / array / string / **integer** / bool / null。
2. **禁止浮点参与 digest**：digest 序列化器对输入**递归校验**（含 config/ext/effect params 等自由字典的嵌套层），遇 float 即拒绝（`CanonicalizationError`）；比率类以**定点字符串**承载，格式由字段声明 scale 并以 pydantic pattern 强制（缺省 2 位小数：`^-?\d+\.\d{2}$`）；datetime 唯一字面 = UTC、毫秒恒 3 位、`Z` 后缀（`2026-08-31T12:00:00.000Z`）；Enum 取字符串值；模型内 frozenset/set 由序列化器输出为**排序列表**；整数声明界 |n|<2^53（越界拒绝）。非 digest 运行时消息（如 HandoffResult.metrics）允许 float，此类字段永不参与 digest。
3. 编码：UTF-8；字符串先 NFC 后使用，**NFC 后键碰撞即拒绝**；非 ASCII 直出，仅转义 JSON 必需字符（`"`、`\`、控制字符，`\u` 小写）；键按 UTF-8 字节序升序、无空白、整数十进制无前导零（`-0` 非法）。
4. `digest(obj) = "sha256:" + hex_lower(sha256(canonical_json_bytes(obj)))`；凡本文"digest"均指此形式（含前缀的完整字符串）。
5. contracts 包交付 golden vectors（嵌套/Unicode/边界整数/定点字符串各≥1）作为跨实现一致性测试。

### 0.2 标识符总表（格式 | 生成方 | 唯一性域）

| 标识符 | 格式 | 生成方 | 唯一性域 |
|--------|------|--------|---------|
| run_id | `RUN-`+ulid | 编排（create_run 事务） | 全局 |
| task_id | `<PREFIX>-`+≥6位十进制（HLD 示例 6 位为下限，耗尽扩位） | 编排（dispatch 事务；序号全局单调） | 全局 |
| dispatch_id / activation_id / outbox_id / lease_id | ulid | 编排（对应事务内） | 全局 |
| decision_id / adjudication_id / correction_id | ulid | **对应服务端**（Approval / 编排特权面）事务内生成，请求载荷不含、响应返回 | 全局 |
| gate_instance_id | ulid | 编排（gate 等待项登记事务） | 全局 |
| series_id | `SER-`+ulid | 编排（§3.3 完成事务内签发；candidate 阶段为预留值） | run 内 |
| token_id | ulid + `-` + 32 hex（128bit CSPRNG） | Approval 服务 | 全局（高熵，HLD §3） |
| snapshot_id | `SNAP-` + digest(manifest) 的 hex 前 32 字符（**全量 digest 入 Ledger，判定按全量；前缀仅显示名**） | 编排 | 全局 |
| request_id | 调用方任意 ≤64 字符 | Skill 调用方 | (bearer principal, endpoint) 内幂等，保留 7 天；同 id 异载荷 → E-SKILL-IDEM-MISMATCH(422) |
| pipeline_id | 文件名 stem `[a-z0-9_]+` | 部署配置 | 部署内 |

ulid = 26 字符 Crockford Base32。碰撞策略：ulid 类由生成方保证单调；序号类溢出扩位不回绕。task_prefix：2–4 大写字母、注册期全局唯一（V-02 校验）。

### 0.3 Contract 版本
`contract_version = "1.0.0.dev1"`（PEP 440 合法；文档展示号 v0.2 与其映射关系记于 A3 变更表）。draft 期破坏性修改递增 devN；v1.0.0 按 HLD D10/G6 宣布。`contract_requires` 按 PEP 440 specifier 匹配 contracts 包版本；draft 期业务侧锁精确版本（`==1.0.0.devN`，逐版显式升级）。`dsl_version` 当前 1。

### 0.4 模型总纲
全部模型 `ConfigDict(extra="forbid", frozen=True)`；**唯一豁免**：各 Report 类型体允许扩展键，必须置于 `ext: dict[str, JsonValue]` 单一容器内且键带 `<org>__` 前缀——除 ext 外仍 forbid。本文出现的每个类型名在正文或 §7 附录 A0 有完整定义，无匿名 schema。

---

## 1. Pipeline DSL v1 与静态校验（HLD §4.2）

### 1.1 文件 schema

```python
class GateType(StrEnum): hitl="hitl"; threshold="threshold"
class RetrySpec(BaseModel): on: list[SysOutcome]; max: int = Field(ge=1)   # V-16 约束子集
class LoopBudget(BaseModel): max_rounds: int = Field(ge=1); max_wall_clock_min: int = Field(ge=1)
class RunBudget(BaseModel): max_wall_clock_min: int = Field(ge=1)
class LLMBudget(BaseModel): max_tokens: int = Field(ge=1); on_exceed: Literal["truncate","error"]="truncate"

class NodeSpec(BaseModel):
    agent_type: str | None = None; mode: str | None = None
    gate: GateType | None = None
    metric: str | None = None            # threshold: "<producer_node>.<field>"（§1.5）
    op: Literal["<=", ">=", "<", ">", "=="] | None = None
    value: str | None = None             # 定点字符串；加载器对 value 位置做 schema 感知预处理：
                                         # YAML 十进制字面量按**原文词素**无损转定点字符串（按声明 scale 补零，
                                         # 精度超 scale 或非十进制词素拒绝），字符串原样校验 pattern
    ttl_min: int | None = Field(default=None, ge=1)   # 仅 hitl；缺省无 TTL（HLD §4.4）
    broker: Literal["release"] | None = None
    terminal: bool = False
    success_on: list[str] | None = None
    retry: RetrySpec | None = None
    llm_budget: LLMBudget | None = None
    config: dict[str, JsonValue] = {}
# 字段适用矩阵（V-01 强制）：agent 型可用 mode/retry/llm_budget/config/terminal/success_on；
# threshold 型仅 gate/metric/op/value；hitl 型仅 gate/ttl_min；broker 型仅 broker。越界字段拒绝。

class LoopEdge(BaseModel): from_: str = Field(alias="from"); to: str      # wire 名 from/to
class LoopSpec(BaseModel): id: str; edges: list[LoopEdge] = Field(min_length=1); budget: LoopBudget
class JoinSpec(BaseModel): id: str; wait_for: list[str] = Field(min_length=2); timeout_min: int | None = None; to: str
class RouteSpec(BaseModel):
    from_: str = Field(alias="from"); on: str
    to: list[str] = Field(min_length=1)
    # wire 兼容（HLD §4.2.1 旗舰原文强制通过）：加载器接受标量 to 并规范化为单元素列表；
    # 模型内部唯一形态为列表。CF-DSL-FLAG 断言旗舰原文直接加载。
class PipelineSpec(BaseModel):
    pipeline: str; dsl_version: Literal[1]
    nodes: dict[str, NodeSpec]; entry: str
    loops: list[LoopSpec] = []; joins: list[JoinSpec] = []
    routes: list[RouteSpec]; default_route: Literal["fail_safe"]
    run_budget: RunBudget; snapshot_policy: Literal["pin_at_start"] = "pin_at_start"
```
`pipeline_digest = digest(PipelineSpec)`。`to` 成员语法：节点名 | `fail_safe` | `join:<id>`；fan-out = 单条 route 的多元素 to（V-04）。

### 1.2 保留名与固定语义
同 v0.1 §1.2（保留节点 fail_safe；sys.* = crash/timeout/invalid_result/error；gate outcome 封闭枚举；release outcome {released, release_failed} 且无出边）。`SysOutcome = Literal["sys.crash","sys.timeout","sys.invalid_result","sys.error"]`。

### 1.3 静态校验规则（违规 → `PipelineValidationError(rule_id, locus)`）

| ID | 规则（依据） |
|----|--------------|
| V-00 | **引用有效性**：route.from_ ∈ nodes；route.to 各成员 ∈ nodes ∪ {fail_safe} ∪ {join:<已声明 id>}；join.to ∈ nodes；LoopEdge 两端 ∈ nodes 且该边对应至少一条已声明 route；threshold metric 的 producer_node ∈ nodes；join/loop id 各自唯一；wait_for/edges/to 元素无重复（HLD §4.2.6 首条） |
| V-01 | 节点三型互斥 + **字段适用矩阵**（§1.1 注）；threshold 必填 metric/op/value（§4.2.2） |
| V-02 | **注册与准入**：agent_type 已注册、status_set 非空、task_prefix 格式合法且全局唯一、contract_requires 与 contracts 包版本兼容、conformance attestation 有效且绑定制品 digest ∈ execution manifest——未注册 agent_type 在 V-05 之前即拒（重写恢复项，CF-DSL-02 覆盖） |
| V-03 | 节点名不占保留名/命名空间/`join:`前缀；entry 存在唯一；无不可达节点 |
| V-04 | **路由唯一性**：同 (from_, on) 至多一条 route（fan-out 经单条多元素 to 表达，多条即拒绝） |
| V-05 | route.on ∈（from 节点 status 全集 ∪ 其 gate outcome 集 ∪ sys.*） |
| V-06 | 穷尽性：每节点业务 status 逐条有路由或被 default_route 覆盖 |
| V-07 | 每个可达环至少含一条某 LoopSpec 声明边（等价判定：移除全部声明环边后图无环）；每条声明边隶属唯一 LoopSpec |
| V-08 | join.wait_for ≡ { r.from_ : "join:"+id ∈ r.to }（集合相等，按 to 成员判定） |
| V-09 | **每 activation 单送达（语义性质 + 保守判定）**：性质 = join 来源节点 s 每 activation 最大 dispatch 数 ≤1。判定：s 的多条入边合法当且仅当静态可证两两互斥（源自同一节点不同 outcome 的分支且中途未再汇合，可传递）；互斥性不可静态判定即拒绝。同节点互斥 outcome 多路指向同一 join 合法；互斥入边汇聚于中间节点 s 再入 join 亦合法（CS-05 反例形态） |
| V-10 | join.to 非 join（禁链式）；多源 join 来源由同一显式 fan-out 的分支派生、来源集在分支间构成划分；共同支配不得替代共同 fan-out |
| V-11 | 共同到达性三条件（同 v0.1，措辞照 HLD §4.2.6） |
| V-12 | 环边双约束（同 v0.1，照 HLD 条件(iii)） |
| V-13 | release 路径规则（照 HLD §4.2.5）：必经 hitl；release 可达路径上的 hitl approved 出边直达 release；release 无出边 |
| V-13b | **[HLD 勘误 HLD-Q1]** release-approval 型 hitl 须存在支配它的 **ReleasePlan 生产节点**（按 §2.3 produces 声明判定：produces 含 "release_plan"）；多候选生产者 → 取支配链上最近者，歧义（同深多者）拒绝 |
| V-14 | terminal 节点必有非空 success_on ⊆ status 全集，且**无出边**（非 success outcome 固定映射 fail_safe，编译期落表） |
| V-15 | hard-required（ProducerSelector 解析）与 threshold metric 生产节点：存在、可解析唯一、支配消费节点、消费同 series 结果；metric 的 field 须在该生产节点 produces 全部类型体的 gateable 字段中**唯一匹配**，歧义拒绝 |
| V-16 | retry.on ⊆ SysOutcome 全集 |
| V-17 | hitl 分型静态判定（同 v0.1） |

### 1.4 编译产物
`CompiledPipeline`（内部 schema，进 execution manifest 的是其 digest 而非本体）：节点表（分型/hitl 型别/terminal 映射）、路由表、环表、join 表（scope fan-out、来源划分、超时配置）、支配缓存、threshold 解析表。

### 1.5 threshold 指标解析（唯一数据源）
`metric = "<producer_node>.<field>"`：field 解析到该生产节点注册 Report 类型体的**顶层定点字符串字段**（§2.4 各 Report 的可门禁字段以 `# gateable` 注明）；比较按 Decimal。缺失字段 / 非法值 / 生产节点本轮无产出 → outcome=fail（fail-closed）。旗舰示例 `benchmark.regression_pct` 解析到 BenchReport.regression_pct（顶层聚合字段，§2.4）。

---

## 2. 状态机与消息（HLD §4.3/§6/§8.2-8.3）

### 2.1 Run 状态机命令/guard 表

| # | 命令（发起者） | 前置 guard | 附加 guard / 事务内容 | 目标 |
|---|----------------|-----------|----------------------|------|
| C-01 | create_run（Skill，**异步**） | — | pipeline 校验通过；水位达标；响应仅 {run_id, state}，snapshot 经 GET 获取（R2-07 定案） | created |
| C-02 | snapshot_pin（编排） | created | 成功：写 snapshot/execution manifest | awaiting_patch |
| C-03 | snapshot_pin 失败 | created | — | closed(snapshot_error) |
| C-04 | submit_patch（Skill） | awaiting_patch | 可应用；单 Run 一次；**初始 series 单事务**（§3.3a：签发 SER-0、lineage(parent=None,base=snapshot)、tree_digest、current 推进）；request_id 重放返回同 series_id | queued（run_budget 起算） |
| C-05 | awaiting_patch TTL | awaiting_patch | 默认 24h | closed(cancelled) |
| C-06 | slot_acquire（编排） | queued | FIFO 队首且槽空闲 | running |
| C-07 | gate_wait_only（编排） | running | 仅剩 gate 等待、无可运行工作 | paused（释放槽） |
| C-08a | gate_resolve（outbox 消费） | paused | decision_id 未消费；gate CAS waiting→resolved | queued（resume 入 FIFO） |
| C-08b | gate_resolve（outbox 消费） | running | 同上；**Run 不迁移**，同事务 durable dispatch 下游 | running |
| C-08c | gate_ttl_expire（编排定时） | paused ∨ running | gate CAS waiting→resolved(**gate_expired**，编排合成 outcome，不经 ApprovalDecision，outbox 项标 origin=ttl）；paused→queued / running 不迁移同事务 dispatch | queued / running |
| C-09 | authorization_consume（broker RPC） | running | 三支见 §2.2a | ①publishing ②closed(按 §2.2b release_failed 映射) ③→C-14 |
| C-10 | release_outcome（broker） | publishing | §2.2b 固定映射 | closed(...) |
| C-11 | 裁决/自动 probe 定论 | publishing | §2.2c 裁决映射；adjudication_id 幂等、状态 CAS | closed(...) 或保持 publishing |
| C-12 | fail_safe_enter（编排） | running | 保留节点：聚合 + FeedbackReport | closed(fail_safe) |
| C-13 | budget_expire（编排定时） | queued ∨ running | run_budget/loop 预算触顶（口径 §3.4）→ 强制路由 fail_safe（等效 C-12） | closed(fail_safe) |
| C-14 | administrative_finalize（ledger 级） | 非 closed、非 publishing | HLD §4.3.3（活跃引擎先停）；probe 对账 + ledger 级 FeedbackReport | closed(fail_safe) |
| C-15a | cancel_close（Skill/运维） | created ∨ awaiting_patch ∨ queued ∨ running ∨ paused | 在飞 worker 终止（§5.1 语义） | closed(cancelled) |
| C-15b | cancel_pending（Skill/运维） | publishing | 仅 pending_register(kind=cancel)；幂等返回登记态 | publishing（不迁） |
| C-16 | terminal_success（编排） | running | terminal outcome ∈ success_on | closed(succeeded) |

publishing 期一切改向事件（cancel / 并行 fail_safe / series 更新 / administrative finalize）经 `pending_register{kind, dedup_key}` 仅登记（HLD §8.3）；§3.3 完成事务在 Run=publishing 时 series 相关步骤（推进/失效/退役）整体降级为 pending 记录，结果与 artifact 照常提交。

### 2.2 release 三支与终态映射（ledger 级；HLD §8.3/§4.2.5）
**(a) 核销三支（C-09）**：①授权有效（未核销未撤销未过期、全绑定字段与当前一致）→ 原子核销 + Run→publishing；②授权失效/过期/series 陈旧 → **不核销**，从 running 直接按 (b) 的 release_failed 映射 ledger 级关闭（reason 附 authorization_expired/stale/revoked；即 C-09 目标②）；③D12 digest 不匹配（**核销前检测**）→ 专用错误码 `E-CP-D12-MISMATCH`，授权不动，触发 C-14。
**(b) broker outcome 映射（C-10）**：released → closed(succeeded)（pending 记入 RunSummary）；release_failed → 按序消费 pending：admin_finalize（closed(fail_safe)+版本漂移 FeedbackReport）＞ cancel（closed(cancelled)）＞ fail_safe（closed(fail_safe)）＞ 均无 → closed(fail_safe) + ledger 级 release_failed FeedbackReport。series 更新 pending 仅记录。
**(c) 裁决映射（C-11）**：confirm_released ≡ released 映射；confirm_not_released ≡ release_failed 映射（同 (b) pending 序；guard：broker 静默确认 + evidence_refs 非空）；keep_unknown → 保持 publishing；自动周期 probe 得出确定结论 → 等同对应 broker outcome。并发/重复裁决：publishing 状态 CAS + adjudication_id 幂等（重复返回首个结果）。

### 2.3 Agent 注册与任务消息

```python
class ProducerSelector(BaseModel): report_type: str; producer_node: str | None = None  # None=按支配链最近唯一者
class AgentRegistration(BaseModel):
    agent_type: str; task_prefix: str
    status_set: frozenset[str]; contract_requires: str
    produces: frozenset[str]                       # 产出 report_type 集（V-13b/V-15 判定依据）
    hard_required_inputs: tuple[ProducerSelector, ...] = ()
    capabilities_required: frozenset[str] = frozenset()

class UpstreamItem(BaseModel): producer_node: str; report_type: str; task_id: str | None; ref: ArtifactRef | None  # ref=None 即缺失
class TaskInput(BaseModel):
    run_id: str; task_id: str; dispatch_id: str; attempt: int
    node: str; node_config: dict[str, JsonValue]; mode: str | None
    series_id: str; snapshot_id: str
    upstream: tuple[UpstreamItem, ...]              # 按 (producer_node, report_type) 唯一；同类型多生产者各占一项
    join_inputs: tuple[JoinInputItem, ...] | None
class JoinInputItem(BaseModel): source_node: str; handoff_ref: ArtifactRef; series_id: str; task_id: str

class HandoffResult(BaseModel):
    task_id: str; status: str; series_id: str
    artifact_refs: dict[str, ArtifactRef]; reason: str = ""
    metrics: dict[str, float] = {}                  # 运行时观测，不参与 digest（§0.1）

class ArtifactRef(BaseModel): digest: str; kind: str; media_type: str = "application/json"; data_class: DataClass
class RunContext(BaseModel):                        # setup(ctx) 注入面（HLD §5.1.1/§6.1）
    run_id: str; snapshot_id: str; snapshot_manifest_ref: ArtifactRef
    pipeline_id: str; pipeline_digest: str; contract_version: str
    capabilities: frozenset[str]                    # 实际注入的能力句柄名集（发布通道永不出现）
```

### 2.4 Report schema
```python
class ReportBase(BaseModel):
    report_type: str; task_id: str; run_id: str; series_id: str
    created_at: datetime; data_class: DataClass
    inputs: tuple[UpstreamItem, ...]        # 消费与缺失显式记录（HLD §6.3）
```
每个具名 Report = ReportBase 子类 + 类型体；**ReleasePlan 亦然**（§2.5 类型体中与头重复的 run_id/series_id 移除，由头承载）。`HandoffResult.artifact_refs` 键约定：所产各 Report 以其 report_type 为键（框架据此 + produces 声明构造 UpstreamItem 并校验齐全），其余产物键自由但不得与任何 report_type 冲突。类型体（`# gateable` = 可作 threshold 指标的顶层定点字符串字段）：
- **BuildReport**：`succeeded: bool; targets_built: list[str]; revdep_scope: list[str]; failed_target: str|None; error_excerpt_ref: ArtifactRef|None; fix_patches: list[PatchAttribution]; rounds_used: int; output_refs: dict[str, ArtifactRef]`（RPM 等构建产物，供 hard-require）
- **UTReport**：`passed: bool; boards: list[str]; suites: list[SuiteResult]; failure_analysis_ref: ArtifactRef|None; fix_patches: list[PatchAttribution]`；`SuiteResult = {name, board_id, passed: int, failed: int, skipped: int}`
- **BenchReport**：`regression_pct: str  # gateable（定点，全指标最大回归）; metrics: dict[str, MetricEntry]; baseline_ref: ArtifactRef; patch_relatedness_ref: ArtifactRef`；`MetricEntry = {value: str, baseline: str, regression_pct: str}`（定点字符串）
- **ReviewReport**：`verdict: Literal["pass","concerns","block"]; findings: list[Finding]`；`Finding = {severity, locus, summary, evidence_ref: ArtifactRef|None}`
- **ReleasePlan**（report_type="release_plan"，ci 型 Agent 产物）：见 §2.5
- **FeedbackReport**：`origin: Literal["fail_safe","admin_finalize","release_failed"]; rounds: list[RoundDigest]; all_patches: list[PatchAttribution]; reports: list[ReportEntry]; parent_run_id: str|None`；`ReportEntry = {producer_node: str, report_type: str, task_id: str, ref: ArtifactRef}`（按 (producer_node, report_type, task_id) 唯一、按 created_at 排序——R2-09）；`RoundDigest = {round: int, node: str, task_id: str, status: str, summary: str}`
- **RunSummary**：`final_state: str; reason: str; pending_events: list[PendingEvent]; artifact_index_ref: ArtifactRef`（**不含 corrections**——修正只经结果 envelope 返回，§2.7/§5.4）；`PendingEvent` 为按 kind 判别联合，各型携带消费所需载荷（CS-10）：cancel{requestor}；fail_safe{origin_node, reason, evidence_refs}；series_update{candidate_ref, expected_parent_series_id}；admin_finalize{drift_detail}——固定映射消费时据此生成规定的 FeedbackReport；公共字段 registered_at, dedup_key
- **PatchAttribution**：`patch_digest: str; repo_id: str; producer: {agent_type: str, task_id: str, round: int}; motivation: str`；`patch_digest = "sha256:" + hex(sha256(unified_diff 原文字节，统一 \n 行尾、保证结尾单换行；不含 description))`

### 2.5 ReleasePlan / ReleaseManifest / 授权

```python
class ReleaseAction(StrEnum): push_branch="push_branch"; gerrit_review="gerrit_review"
class ReleaseTarget(BaseModel): adapter: str; repo: str; branch: str; action: ReleaseAction
class ReleasePlan(BaseModel):        # Report 型
    run_id: str; series_id: str; tree_digest: str
    targets: tuple[ReleaseTarget, ...]              # 有序；执行按序；(adapter,repo,branch) 重复拒绝
    squash: bool = False
class ReleaseManifest(BaseModel):    # = Plan 无损规范化 + 环境绑定；含全部影响远端效果的字段
    snapshot_id: str; series_id: str; tree_digest: str
    targets: tuple[ReleaseTarget, ...]; squash: bool
    pipeline_digest: str; exec_manifest_digest: str
class ApprovalDecisionRequest(BaseModel):   # decision_submit 载荷（无 id，服务端签发）
    gate_instance_id: str; run_id: str
    verdict: Literal["approved","rejected"]; reviewer: str
    manifest: ReleaseManifest | None                # release-approval 型必填；plain 型 None
    evidence_refs: tuple[ArtifactRef, ...] = ()
class ApprovalDecision(ApprovalDecisionRequest): decision_id: str; created_at: datetime  # 服务端补齐落 Ledger
class AuthorizationRecord(BaseModel):               # 同 v0.1 字段 + revoke/consume 语义（HLD §8.2）
    token_id: str; run_id: str; gate_instance_id: str; decision_id: str
    ci_plan_task_id: str; series_id: str; tree_digest: str
    release_manifest_digest: str; expires_at: datetime
    consumed_by_task_id: str | None = None; revoked: bool = False
```
decision_submit（release-approval 型）事务内 **新鲜度 CAS**：gate waiting ∧ manifest 所引 ReleasePlan 为该 Run 当前版本 ∧ series/tree 为最新（HLD §8.2）。`ci_plan_task_id` 来源闭合：授权记录取 gate 实例绑定的 ReleasePlan Report 的 task_id（decision_submit 新鲜度 CAS 校验该 Report 为当前版本）。release 节点 dispatch 载荷含 `token_id`；broker 以 token_id 读授权记录取 manifest digest，依 release_plan_ref 重建 canonical ReleaseManifest 并比对 digest 后执行——审批-核销-执行链以 digest 闭合（CS-16）。

### 2.6 ExecutionManifest
```python
class ExecutionManifest(BaseModel):
    pipeline_digest: str; compiled_pipeline_digest: str
    contract_version: str; framework_version: str; engine_version: str
    agent_artifacts: dict[str, str]                 # agent_type → 制品 digest
    provider_policy_digest: str; dsl_version: int
```
复核时点：恢复 / dispatch / decision_submit / C-09 核销前（三支 ③）。

### 2.7 Skill 协议

```python
TargetSpec = Annotated[ReposSpec | ManifestSpec | PackagesSpec, Field(discriminator="kind")]
class ReposSpec(BaseModel): kind: Literal["repos"]; repo_ids: list[str] = Field(min_length=1)
class ManifestSpec(BaseModel): kind: Literal["manifest"]; name: str
class PackagesSpec(BaseModel): kind: Literal["packages"]; packages: list[str] = Field(min_length=1)
# 解析语义（CS-24）：repos → 须为部署 repo 注册表子集，未知项 E-SKILL-VALIDATION；manifest → 注册表命名清单；
# packages → 经部署 package→repo 映射解析为 repo 集，未知项拒绝；三型解析结果去重、非空，空集拒绝。
# 各 endpoint 请求/响应均为具名模型（SkillCreateRunRequest 等，A0 收录），无匿名载荷。
class SkillError(BaseModel): code: str; message: str; detail: dict[str, JsonValue] = {}
class ResultEnvelope(BaseModel):
    run_summary: RunSummary; feedback_report: ArtifactRef | None
    corrections: tuple[CorrectionRecord, ...]       # append-only，摘要之外返回（HLD §8.3）
```

| 操作 | 请求/响应 | 错误码（HTTP） |
|------|-----------|---------------|
| POST /runs（异步） | {pipeline_id, target_spec, request_id} → {run_id, state} | E-SKILL-VALIDATION(400)、E-SKILL-CAPACITY(503) |
| GET /runs/{id}（snapshot 就绪后） | → 含 snapshot_id, snapshot_manifest_ref；state=closed(snapshot_error) 即失败形态 | — |
| POST /runs/{id}/patches | {series: [PatchItem], request_id} → {accepted, series_id} | E-SKILL-DUP-SUBMIT(409)、E-SKILL-UNAPPLICABLE(422，附首个失败 hunk 定位)、E-SKILL-TOO-LARGE(413) |
| GET /runs/{id} | → {state, node_progress, loop_counters, queue_position?} | E-SKILL-NOT-FOUND(404) |
| GET /runs/{id}/result | → ResultEnvelope | E-SKILL-NOT-READY(425) |
| POST /runs/{id}/cancel | {request_id} → {state} | E-SKILL-FORBIDDEN(403) |
| （通用） | — | E-SKILL-IDEM-MISMATCH(422)、E-SKILL-AUTH(401) |
`PatchItem = {repo_id, unified_diff, description}`；应用序 = snapshot manifest 序。request_id 语义见 §0.2。

---

## 3. Activation 与 Series（HLD §4.2.4/§7.6.2/§4.5）

### 3.1 ActivationRecord 与传播（含 loop_vector 复制规则）

```python
class ActivationRecord(BaseModel):
    activation_id: str; run_id: str
    origin: Literal["root","fanout","loop"]; origin_node: str | None
    parent_activation_id: str | None
    loop_vector: dict[str, int]          # loop_id → 通过次数
    series_id: str; state: Literal["open","superseded"]
```
1. **root**：entry 分派事务生成；parent=None；loop_vector={}。
2. **线性/分支中间边**：继承派发边的 activation 上下文（含 loop_vector），不新建。
3. **fan-out（一般情形）**：分派事务生成子 activation；parent=分派 task 的 activation；loop_vector=父副本。
4. **loop**：环边分派事务内：(a) 条件③级联退役（被采用者及子孙闭包、计时器作废）；(b) 生成 loop activation L：parent=被退役者的 parent，loop_vector=被退役者副本且该 loop_id 分量 +1；(c) 环计数/预算检查同事务（触顶改路 fail_safe，L 不生成）。
5. **join 消费**：下游 dispatch 的 activation 上下文 = 被消费 activation 的 parent（loop_vector 取 parent 记录值）。
6. **替代 cohort（规则 3 的显式覆盖）**：当 fan-out 分派 task 的 activation 为 loop 型（origin="loop"）且该 fan-out 为其所回流的共同 fan-out 时，生成的 activation **parent 直接置为该 loop activation 的 parent**（即被退役 cohort 的 parent），loop_vector=该 loop activation 副本——祖先链深度不随环轮次增长（HLD"环不插入额外嵌套层级"）；conformance 断言 CF-ACT-06。
supersede 三条件与 CAS 守卫照 HLD §4.2.4；恢复自 Ledger 重建全部 activation。

### 3.2 join 到达与消费
同 v0.1 §3.2（到达键唯一、stale 丢弃、原子整组消费 + 父 scope 分派 + 计时器作废、超时自首达起算按 §3.4 口径）。

### 3.3a 初始 series（C-04 单事务；R2-03）
校验完整 series 可应用 → 签发 `SER-0`（初始 series_id）→ 写 lineage（parent=None、base=snapshot、patches 全量 PatchAttribution，producer=coding_agent）→ 计算 tree_digest（§3.5）→ 推进 current → Run→queued。request_id 重放返回同 series_id；事务前崩溃 = 未受理（客户端重试），事务后崩溃 = 幂等返回。

### 3.3 series 推进（task_complete 复合事务）
1. guard：Run ≠ publishing（是则 series 相关步骤降级 pending 记录，其余照常）；
2. CAS `current_series_id == expected_parent_series_id`——失败归 **sys.error**（合法并发竞争，可按节点 retry 策略重试；HLD"防并发丢 patch"）；
3. 结果 + artifact 索引转正 + 幂等终态；
4. 签发 series_id、写 lineage `{new, parent, contributed_by_task, patches}`、推进 current；
5. tree_digest 计算记录（§3.5）；
6. 失效链：未核销授权 revoke、待审批项作废、旧 series open activation 条件①全量退役。

### 3.4 计时口径
run_budget：自 C-04 起算，排除 paused 与 publishing 时段，queued 计入；触顶经 C-13。loop：计数器键 `(run_id, loop_id)`，环边通过 +1（max_rounds 语义照 HLD §4.5）；wall_clock 自该 loop 首条环边首次通过起算，排除 paused/publishing。join timeout：`(run_id, join_id, activation_id)` 级，自首达起算，同口径。全部计时以 Ledger 暂停区间扣除实现。

### 3.5 tree_digest（应用后 tree OID 的规范组合；HLD §7.6.2）
1. 对每个 repo：以 bare object DB / 临时 index（无需 worktree）自 snapshot commit 依 series lineage 应用序 apply 全部该 repo patch，得 **git tree OID**；apply 失败：submit_patch 阶段即拒绝（E-SKILL-UNAPPLICABLE）；完成事务阶段失败（业务 fix-patch candidate 首次在此应用，可达）→ sys.error（T-b1）。
2. 确定性步骤：临时 index ← `git read-tree <snapshot commit tree>` → 逐 patch `git apply --cached --whitespace=nowarn` → `git write-tree` 得 OID；OID 表示 = `<object-format>:<hex>`（如 `sha1:...`，取仓库 object-format）。`line_i = repo_id + ":" + oid_repr`（repo_id 字符集 `[a-z0-9._-]+`，V-00 校验）；`tree_digest = "sha256:" + hex(sha256(UTF-8("\n".join(lines sorted by repo_id))))`，**无末尾换行**；golden vectors 覆盖多仓/空 patch 仓/等价 tree（R2-06）。
3. 性质：等价最终 tree ⇒ 等 digest（增删相消、异 patch 同果均一致）；BuildExecutor worktree 应用后复核 tree OID 一致，不一致 → sys.error（兜底为**校验**而非替代定义）。conformance 含等价 tree 用例 CF-SER-04。

### 3.6 snapshot manifest（同 v0.1；snapshot_id 形式见 §0.2）

---

## 4. 效应幂等（HLD §5.2）

### 4.1 键与调用面
```python
class EffectResult(BaseModel): return_value: JsonValue; artifact_refs: dict[str, ArtifactRef] = {}
def side_effect(effect_call_id: str, params: BaseModel, fn: EffectType, repeat_seq: int | None = None) -> EffectResult
# idem_key = digest({run_id, dispatch_id, effect_class, effect_call_id, effect_params_digest, repeat_seq})
```
succeeded 复用即返回存储的 EffectResult；同键规则、effect_call_id 约束、异参枚举（含 failed 条款）照 v0.1 §4.1/§4.3 全文保留。

### 4.2 EffectRecord 与迁移表
```python
class EffectRecord(BaseModel):
    idem_key: str; version: int; run_id: str; task_id: str; dispatch_id: str
    effect_class: str; effect_call_id: str; effect_params_digest: str; repeat_seq: int | None
    params_ref: ArtifactRef                       # canonical params 全文（内容寻址）——对账 probe 的参数来源（R2-05）
    state: Literal["claimed","running","succeeded","failed","abandoned","unknown"]
    result: EffectResult | None; error: JsonValue | None; updated_at: datetime
```
迁移表（v0.1 基础上两处修正）：**claimed→succeeded 合法**——限定"对账 probe 确认成功，补写 result_descriptor"（B-03）；**claimed→failed 限定**为框架启动前判定失败（参数校验拒绝等），传输失败一律停留 claimed 待对账（N-06）。abandoned 之上重执行 = 同键 version+1 新记录。

### 4.3 Probe 与 failed 处置
```python
class ProbeOutcome(StrEnum): confirmed_happened="confirmed_happened"; confirmed_not_happened="confirmed_not_happened"; indeterminate="indeterminate"; not_supported="not_supported"
class ProbeResult(BaseModel): outcome: ProbeOutcome; result: EffectResult | None  # confirmed_happened 时必填；probe 由**编排进程**加载注册 EffectType 执行（对账场景），probe 必须只读、无副作用（conformance 断言）；重试计数持久化于记录
class EffectType(Protocol):
    effect_class: ClassVar[str]; replay_safe: ClassVar[bool]
    supports_probe: ClassVar[bool]                # 静态能力位（对账路径选择依据）
    probe_retry_max: ClassVar[int]; probe_retry_interval_sec: ClassVar[int]   # indeterminate 有限重试参数（P-04）
    failed_disposition: ClassVar[Literal["raise","retry_new_version"]]; failed_max_retries: ClassVar[int]
    def probe(self, params, record) -> ProbeResult: ...
```
对账映射：confirmed_happened → succeeded（复用）；confirmed_not_happened → abandoned；indeterminate（含 probe 自身异常）→ **保持待对账重试有限次后 unknown + sys.error**（不得当作 not_happened，防不可安全重放效应被重放——CS-19）；not_supported + replay_safe → 退役 abandoned 后同键版本化重放；皆无 → unknown + sys.error。failed 同键再调用：按 failed_disposition——raise（返回存储 error）或 retry_new_version（版本化重试至 failed_max_retries，超限 raise）。
注册面：entry-point namespace `codingsystem.effects`；装配时校验 effect_class 唯一、能力声明齐备、类别硬性要求（build.* 可 probe；board.* 可 probe 或 replay_safe；publish.* 仅 broker，业务注册即拒绝）。

---

## 5. 安全接口（HLD §7.1/§8）

### 5.1 Control-plane 命令集

**worker 数据面 socket**（per-task socketpair；命令封闭枚举）：

| 命令 | 载荷 | 语义 |
|------|------|------|
| heartbeat | seq | 租约信号（间隔配置）；编排侧超时 = 租约失；worker 侧 socket EOF = 通道失 → killpg 自杀（HLD §5.1.2 双向覆盖） |
| effect_claim | effect_call_id, effect_class, params_ref, repeat_seq | 响应为封闭联合 `{action: execute(附 idem_key,version) | reuse(附存储 EffectResult) | error(附归类)}`；写 claimed（execute ack 前禁执行） |
| effect_transition | idem_key, to∈{running,succeeded,failed}, result?/error? | 单行 CAS（受 §4.2 迁移表约束） |
| trace_append | 事件批（≤64 条/批，≥1s 批间隔——背压约定） | 追加 |
| blob_begin | size_hint, **data_class** → lease_id + 临时路径 | **lease 先于写入**（HLD §7.5）；续租经 heartbeat 隐含 |
| blob_commit | lease_id, digest | fsync→rename→digest 复验→索引暂存转正，原子；失败保持 lease 待 abort/GC |
| blob_abort | lease_id | 释放 lease + 清理临时文件 |
| series_candidate_submit | candidate_patches, expected_parent_series_id | 预登记 |
| task_complete | HandoffResult | §3.3 复合事务 |
崩溃恢复：lease 未 commit → 超年龄 GC；已 rename 未入索引 → 孤儿 GC；索引在 blob 失 → 消费方 sys.error（HLD §7.5 各点覆盖，用例 CF-BLOB-*）。

**approval socket**：`decision_submit{ApprovalDecision}`——release-approval 型事务 = 决定 + 新鲜度 CAS（§2.5）+ 授权记录 + gate CAS + resume outbox（outbox 项含 token_id 供 release dispatch）；plain 型 = 决定 + gate CAS + outbox。
**broker socket**：`authorization_consume{token_id, task_id, release_manifest_digest}`（§2.2a 三支）、`release_outcome{task_id, outcome, reason, remote_refs}`。
**特权运维**：`adjudicate{run_id, adjudication_id, verdict, evidence_refs}`——guard：Run=publishing ∧ 强制 probe 后 unknown ∧（verdict∈confirm_* ⇒ evidence_refs 非空）∧（confirm_not_released ⇒ broker task 静默已确认）；`post_close_correction{run_id, CorrectionRequest}`。
**pending**：`pending_register{run_id, kind, dedup_key}`（§2.1）。
**出向**：编排→broker `release_dispatch{run_id, task_id, release_plan_ref, token_id}`，端点仅受编排 UID。
通用：request_id 幂等；复合变更单命令单事务；outbox/inbox 去重同 HLD §4.4。

### 5.2 受限扩展发布原语（封闭判别联合；HLD §8.3）
```python
class FencingInfo(BaseModel): run_id: str; token_id: str
class GitPushOp(BaseModel):
    op: Literal["git_push"]; repo: str; target_ref: str
    content_commit: str                 # 由框架自已核销 manifest 的 series 构建的 commit digest
    force: Literal[False] = False; fencing: FencingInfo
class GerritReviewOp(BaseModel):
    op: Literal["gerrit_review_push"]; repo: str; branch: str
    content_commit: str; fencing: FencingInfo
    # change_id 由 broker 构建 commit 时生成并回填（Change-Id trailer 与 fencing 同级固定），
    # 业务 adapter 不得供给（P-05/CS-22）
RestrictedOp = Annotated[GitPushOp | GerritReviewOp, Field(discriminator="op")]
```
校验（broker 执行前，逐条）：op 序列与已核销 manifest.targets **一一对应**（adapter/repo/branch/action 匹配：push_branch↔git_push、gerrit_review↔gerrit_review_push，多退少补皆拒）；content_commit 必须等于 broker 侧按 manifest（series+squash）自行构建的 commit digest（业务 adapter 无自由内容）；fencing 键固定。透传式原语（任意 REST）禁止；官方 adapter 需要的其余 API 操作在 broker 进程内的原语层实现、不经 RestrictedOp 暴露。

### 5.3 数据密级
```python
class DataClass(IntEnum): public=0; build_log=1; internal_code=2; secret=3   # 全序即 IntEnum 序
class ProviderPolicy(BaseModel): provider_id: str; allowed_max: DataClass    # 授权集 = ≤allowed_max
```
携带：密级权威 = Ledger 索引（blob_begin 出生标注、commit 落索引）；ArtifactRef.data_class 必填且框架以索引值校验，自报不符拒绝（sys.invalid_result）——worker 无降级路径（CS-23）；Report 头必填；EvidencePacket/消息聚合 = max(成员)；**缺失标签或索引损坏 → 按 secret 处理（fail-closed）**；LLM 调用（含 cascade 每跳）校验 payload_class ≤ provider.allowed_max。摘录组件内容升级责任照 HLD。

### 5.4 修正
```python
class CorrectionRequest(BaseModel): original_adjudication_id: str | None; remote_refs: list[str]; evidence_refs: list[ArtifactRef]; disposition: str
class CorrectionRecord(CorrectionRequest): correction_id: str; run_id: str; operator: str; created_at: datetime  # 服务端按 peer credential/服务器时钟生成
```
append-only；终局 artifact 不可变；仅经 ResultEnvelope.corrections 返回（单一事实源，§2.7）。幂等键 = (run_id, original_adjudication_id, digest(request))。

### 5.5 EvidencePacket
```python
class ToolFact(BaseModel): tool: str; query: str; result: str
class LogExcerpt(BaseModel): ref: ArtifactRef; lines: str; data_class: DataClass
class SourceExcerpt(BaseModel): path: str; start: int; end: int; content: str   # 有界：end-start ≤ 400
class EvidencePacket(BaseModel):
    facts: list[str]; negative_facts: list[ToolFact]
    log_excerpts: list[LogExcerpt]; target_source_excerpt: SourceExcerpt | None
    confidence: str                     # 定点字符串
    data_class: DataClass               # = max(成员)，builder 计算
```
builder 校验：产 patch 请求 target_source_excerpt 非空；RawDataDetector；体积上限 256KB。

---

## 6. Conformance 用例注册表（判定权威在本文档；07 只实现 harness 并引用 case ID，不得改写期望）

格式：每 case 一行 `ID | 前置/输入 | 动作（或崩溃/注入点） | 期望`。矩阵型 case 给出轴与**单元格期望规则**，07 枚举单元格执行。攻击面来自 HLD §11.3 全类别（B-4/M-01/P-03 对账补全）。

### 6.1 CF-DSL（校验器）
| ID | 前置/输入 | 动作 | 期望 |
|----|----------|------|------|
| CF-DSL-00a/b | 悬空 route.to / join.to 引用未声明名 | 加载 | 拒绝，rule_id=V-00 |
| CF-DSL-02a/b | 未注册 agent_type / attestation 失效 | 加载 | 拒绝，rule_id=V-02（先于 V-05） |
| CF-DSL-03..08 | V-03..V-08 逐规则最小反例 + 对应最小正例 | 加载 | 反例拒（定位 rule_id）；正例过 |
| CF-DSL-09a | 同节点互斥 outcome 双路由入同 join | 加载 | 通过 |
| CF-DSL-09b | 非互斥多入边汇聚于来源节点 | 加载 | 拒，V-09 |
| CF-DSL-09c | 互斥入边汇聚于中间节点再入 join | 加载 | 通过（CS-05 形态） |
| CF-DSL-11a | 互斥 outcome 致来源必然缺席 | 加载 | 拒，V-11 |
| CF-DSL-12a/b | 分支内回环 / 跨祖先回环 | 加载 | 拒，V-12 |
| CF-DSL-13a | V-13b 反例：release-approval hitl 无支配 ReleasePlan 生产者 | 加载 | 拒，V-13b |
| CF-DSL-13b | 同深双 ReleasePlan 生产者 | 加载 | 拒（歧义 fail-closed） |
| CF-DSL-14..17 | V-14..V-17 逐规则一正一反 | 加载 | 同上模式 |
| CF-DSL-FLAG | HLD §4.2.1 旗舰 YAML **原文**与 compiler_bench_only 原文 | 加载 | 全部通过且编译产物字段齐全（R2-01 断言） |
| CF-DSL-PROP | 随机图生成器（含环/嵌套 fan-out/join，参数化规模） | 批量加载 | 性质断言：校验通过图必满足 V-09 基数性质与 V-11 可达性质（model checking）；拒绝图给出 rule_id；无 panic |

### 6.2 CF-SM（状态机）+ CF-LED（提交点注入）
| ID | 前置 | 动作 | 期望 |
|----|------|------|------|
| CF-SM-01 | 全状态 | 全命令×全状态矩阵 | 单元格规则：§2.1 guard 列合法者迁移、其余 IllegalTransition 拒绝并审计、状态不变 |
| CF-SM-02 | running，他分支在飞 | gate_resolve | Run 保持 running；在飞 task 不受扰；下游 durable dispatch 恰一次 |
| CF-SM-03 | awaiting_patch | TTL 到期 | closed(cancelled) |
| CF-SM-04 | queued | run_budget 触顶 | C-13 → closed(fail_safe) |
| CF-SM-05 | publishing | 四类 pending 逐一登记 + released/release_failed × pending 全组合 | §2.2b 序逐组合断言（含 admin_finalize 最优先、FeedbackReport 载荷来自 PendingEvent payload） |
| CF-SM-06 | running + 三类授权态 | authorization_consume | ①核销+publishing ②不核销+closed(release_failed 映射) ③E-CP-D12-MISMATCH+授权不动+C-14 |
| CF-SM-07 | publishing/unknown | 裁决四形态 | 证据缺失拒；broker 未静默拒 confirm_not_released；重复 adjudication_id 同结果；并发 CAS 单胜 |
| CF-SM-08 | 重启，execution manifest 不匹配 | 恢复 | 不恢复引擎，C-14 administrative finalize（版本漂移 FeedbackReport） |
| CF-SM-09 | publishing 中进程重启 | 恢复 | 对账优先：先 broker/远端 probe，禁 C-14；不可判定保持 publishing |
| CF-SM-10 | paused | resume | paused→queued→running 全链（含槽竞争） |
| CF-SM-11 | gate waiting + ttl_min | C-08c 到期 | outcome=gate_expired 走路由；origin=ttl；verdict 枚举不受扰 |
| CF-LED | 凡 §2.1/§3.3/§3.3a/§5.1 标注"单事务"的命令 | **参数化通则**：每命令提交点前、后各注入一次 kill | 前注入=命令未发生（幂等重放同果）；后注入=效果完整恰一次（M-02 规则；07 按命令清单枚举点位） |

### 6.3 CF-EF（效应）
| ID | 前置 | 动作 | 期望 |
|----|------|------|------|
| CF-EF-01 | 各态记录 | 迁移表全边尝试 | 合法边成功；非法边拒绝（含 claimed→succeeded 仅对账路径可达） |
| CF-EF-02 | claimed/running 遗留 × {可 probe, replay_safe, 皆无} × probe 四值 | attempt 启动对账 | 单元格规则：§4.3 映射（confirmed_happened→succeeded 复用原 EffectResult；not_happened→abandoned；indeterminate→重试 probe_retry_max 次后 unknown+sys.error；not_supported+replay_safe→abandoned+版本化重放；皆无→unknown+sys.error） |
| CF-EF-03 | 不可重放效应，probe indeterminate | 对账 | **零重放断言**（不得当 not_happened） |
| CF-EF-04 | failed 记录同参再调用 × 两 disposition | side_effect | raise 返回存储 error / retry_new_version 版本化至上限后 raise |
| CF-EF-05 | 跨 attempt 定态 {succeeded,abandoned,unknown,failed} × 异参新 claim | claim | succeeded/abandoned/failed 放行新键（succeeded 不跨参复用）；unknown 无新键（task 已终止） |
| CF-EF-06 | 同 attempt 同 call_id 未决 | 异参 claim | 拒绝，sys.invalid_result |
| CF-EF-07 | 双同参调用首成后崩溃 | 重试且控制流变化 | effect_call_id 锚定：不错配（原 R6-01 注入） |
| CF-EF-08 | claim | 响应联合三形态 | execute/reuse/error 各自载荷齐全；reuse 返回存储 EffectResult 逐字节一致 |

### 6.4 CF-ACT / CF-SER
| ID | 前置 | 动作 | 期望 |
|----|------|------|------|
| CF-ACT-01 | 六规则逐条构造 | 传播 | ActivationRecord 字段逐项断言（含 root、继承、loop_vector 复制/递增） |
| CF-ACT-02 | 嵌套子 activation 带计时器 | 环边采用 | 条件③级联退役 + 全部计时器同事务作废 |
| CF-ACT-03 | 旧 activation 首达后 series 推进 | 旧计时器到期 | 审计化 no-op，无误杀 |
| CF-ACT-04 | 同 series 并发双 activation | 各自到达/超时 | 独立成组独立超时互不干扰 |
| CF-ACT-05 | superseded 祖先链 | join 消费/分派/timeout | CAS 拒绝 + 死 scope 分派拒绝并审计 |
| CF-ACT-06 | 环 N 轮迭代（含嵌套 fan-out） | 每轮取父链 | 深度恒定（规则 6 断言） |
| CF-ACT-07 | 内层 join 汇合 | 下游参与外层 join | 父 scope 分派成组成功 |
| CF-SER-01 | 双 task 并发完成 | series CAS | 单胜；败者 sys.error 可 retry |
| CF-SER-02 | 待审批+未核销授权+旧 activation | series 推进 | 三失效同事务 |
| CF-SER-03 | publishing | task_complete | series 步骤降级 pending；结果/artifact 照常 |
| CF-SER-04 | 增删相消 / 异 patch 同果两组 | tree_digest | 等价 tree 同 digest（golden vectors） |
| CF-SER-05 | worktree 应用后 | BuildExecutor 复核 | OID 不一致 → sys.error |
| CF-SER-06 | submit_patch | §3.3a 单事务 + request_id 重放 + CF-LED 点位 | SER-0/lineage/tree_digest/current 齐备；重放同 series_id |

### 6.5 CF-AUTH / CF-IPC / CF-BLOB / CF-SKILL / CF-DC / CF-COR / CF-REC / CF-UP / CF-FIX
| ID | 前置 | 动作 | 期望 |
|----|------|------|------|
| CF-AUTH-01 | 三分量各自过期 | decision_submit | 新鲜度 CAS 逐分量拒绝并提示重审 |
| CF-AUTH-02 | 单授权 | 并发双 consume | 恰一成功 |
| CF-AUTH-03..05 | 同 v0.2（过期不核销 / D12 不烧授权 / 恢复期已核销本 task 有效） | | |
| CF-AUTH-06 | RestrictedOp 序列 | 一一对应校验 | 多/少/异 ref/异 content_commit/自供 change_id 五拒 |
| CF-IPC-01..05 | 同 v0.2 | | 权限隔离/跨 task 拒/真实 UID E2E/outbox 去重/心跳双向（GBS 存活注入） |
| CF-BLOB-01..04 | 同 v0.2 + data_class 出生标注断言 | | lease 先行/逐点崩溃/GC 并发/dangling sys.error |
| CF-SKILL-01..05 | 同 v0.2 + 异步 create（snapshot_error 经 GET 呈现） | | 幂等/409/422 定位/425/TargetSpec 三型解析与未知项拒绝 |
| CF-DC-01..04 | 同 v0.2 + 自报密级不符 | | 聚合最大/缺失按 secret/cascade fail-closed/升级责任/自报不符拒 |
| CF-COR-01 | 复查窗口检出迟到发布 | 自动流程 | 告警 + CorrectionRecord 生成（服务端字段）+ 终态不变 |
| CF-COR-02 | 同修正重复/并发提交 | post_close_correction | 幂等键去重、单条落账 |
| CF-COR-03 | 有修正的 Run | GET result | ResultEnvelope.corrections 呈现、RunSummary 不含 |
| CF-REC-01 | 崩溃恢复 | 重执行 | 复用既有 task/dispatch 记录（dispatch_id 不变）、不产生新分派事件 |
| CF-REC-02 | 恢复后同参效应 | claim | 命中崩溃前记录（键跨重启稳定断言） |
| CF-UP-01 | optional 上游缺失 | dispatch | UpstreamItem.ref=None 显式呈现；hard-required 缺失按 V-15 静态不可达（运行时防御拒绝） |
| CF-FIX-01..05 | 五类 agent_type 各一 producer/consumer fixture 对 | 全链装配 | 逐类：注册通过、TaskInput/HandoffResult 往返 schema 校验、Report 头+类型体齐全、attestation 绑定校验（G6 判定依据） |

## 7. 附录
- **A0 类型索引**：本文全部具名类型及定义位置清单（contracts 包按此逐一交付）：§0 SysOutcome/DataClass…；§1 PipelineSpec 族/RetrySpec/预算族；§2 注册与消息族/Report 族/Release 族/ApprovalDecision/AuthorizationRecord/ExecutionManifest/RunContext/TargetSpec 族/SkillError/ResultEnvelope/PendingEvent/RoundDigest/PatchAttribution；§3 ActivationRecord；§4 EffectRecord/EffectResult/ProbeResult/EffectType；§5 命令载荷族/RestrictedOp 族/ProviderPolicy/CorrectionRequest/Record/EvidencePacket 族/TraceEvent（下条）。
- **A1 开放项（纯实现，均已收窄）**：task 序号分配器持久化布局；CompiledPipeline 内部 schema。`TraceEvent = {seq: int, ts, run_id, task_id: str|None, type: str, payload: dict}`——消费方对未知 type 前向兼容忽略，envelope 纳入版本规则（不再列开放项）。
- **A2 追溯矩阵**：同 v0.1，另增 §2.2↔HLD §8.3 三支、§3.5↔HLD §7.6.2、§6↔HLD §11.3/附录 B-6、V-13b↔HLD-Q1。
- **A3 变更记录**：v0.1 初稿；v0.2 = 首轮 **57 条原始 issue**（合并去重约 40 独立问题）全量修订；v0.3 = 次轮 47 条修订（含旗舰 wire 兼容、初始 series、审批链闭合、probe 参数持久化、§6 注册表扩全）；contract_version 1.0.0.dev1（文档版与包版映射记于此表）。
