# 01 — Contract Specification（契约规格）

**版本**: v0.5 Draft（v0.4 三方复审 2 GO / 1 NO-GO 后修订版，待第五轮复审）
**状态**: 复审中
**上游依据**: docs/00_Framework_HLD_v1.0_draft_frozen.md（下称 HLD）。本文档只精确化 HLD 冻结语义，不引入新架构决策；与 HLD 冲突以 HLD 为准并作为本文档缺陷处理。**例外一处**：V-13b 为 HLD 勘误 HLD-Q1 的形式化（首轮 Claude Code 登记、三方处置表确认走勘误通道），**已于第二轮三方一致批准生效**（规则与程序双表态全 GO），并回写 HLD 附录 A15 勘误注记。
**关联**: docs/review/ 下 01 系三轮处置表（57/47/34/21 条逐条处置）。本版为**自足文本**：不再以"同 v0.1/v0.2"外引承载任何规范性内容。

---

## 0. 约定、标识符与版本

### 0.1 canonical_json（唯一算法）
1. 输入为 pydantic v2 模型经 `model_dump(mode="json")` 的产物；仅允许类型：object / array / string / **integer** / bool / null。
2. **禁止浮点参与 digest**：digest 序列化器对输入**递归校验**（含 config/ext/effect params 等自由字典的嵌套层），遇 float 即拒绝（`CanonicalizationError`）；比率类以**定点字符串**承载，格式由字段声明 scale 并以 pydantic pattern 强制（缺省 2 位小数：`^-?\d+\.\d{2}$`）；datetime 唯一字面 = UTC、毫秒恒 3 位、`Z` 后缀（`2026-08-31T12:00:00.000Z`）；Enum 取字符串值；模型内 frozenset/set 由序列化器输出为**排序列表**；整数声明界 |n|<2^53（越界拒绝）。非 digest 运行时消息（如 HandoffResult.metrics）允许 float，此类字段永不参与 digest。
3. 编码：UTF-8；字符串先 NFC 后使用，**NFC 后键碰撞即拒绝**；非 ASCII 直出；**逐字符唯一转义表**：`"`→`\"`、`\`→`\\`、U+0008→`\b`、U+0009→`\t`、U+000A→`\n`、U+000C→`\f`、U+000D→`\r`，其余 <U+0020 控制字符→`\u00xx`（hex 小写）；此外一律不转义（golden vectors 覆盖换行/退格/NUL/引号/反斜杠）；键按 UTF-8 字节序升序、无空白、整数十进制无前导零（`-0` 非法）。
4. `digest(obj) = "sha256:" + hex_lower(sha256(canonical_json_bytes(obj)))`；凡本文"digest"均指此形式（含前缀的完整字符串）。
5. contracts 包交付 golden vectors（嵌套/Unicode/边界整数/定点字符串各≥1）作为跨实现一致性测试。

### 0.2 标识符总表（格式 | 生成方 | 唯一性域）

| 标识符 | 格式 | 生成方 | 唯一性域 |
|--------|------|--------|---------|
| run_id | `RUN-`+ulid | 编排（create_run 事务） | 全局 |
| task_id | `<PREFIX>-`+≥6位十进制（HLD 示例 6 位为下限，耗尽扩位） | 编排（dispatch 事务；序号全局单调） | 全局 |
| dispatch_id / activation_id / outbox_id / lease_id | ulid | 编排（对应事务内） | 全局 |
| decision_id / adjudication_id / correction_id | ulid | **编排进程**（对应命令事务内生成，请求载荷不含、响应返回——与 token_id 同一单写者理由） | 全局 |
| gate_instance_id | ulid | 编排（gate 等待项登记事务） | 全局 |
| series_id | `SER-`+ulid | 编排（§3.3 完成事务内签发；candidate 阶段为预留值） | run 内 |
| token_id | ulid + `-` + 32 hex（128bit CSPRNG） | **编排进程**（decision_submit 事务内随授权记录生成，响应返回供 CLI 展示——Approval 服务不产 ID，与单写者模型一致） | 全局（高熵，HLD §3） |
| snapshot_id | `SNAP-` + digest(manifest) 的 hex 前 32 字符（接口引用一律以 snapshot_id 为键；生成事务对 snapshot_id 施唯一约束，冲突时前缀逐次 +8 hex 直至唯一——确定性扩位规则；manifest 记录含全量 digest 供审计） | 编排 | 全局 |
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
RetryOutcome = Literal["sys.crash","sys.error","sys.timeout"]
class RetrySpec(BaseModel): on: list[RetryOutcome]; max: int = Field(ge=1)
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
    # 模型内部唯一形态为列表。**加载器定案（显式 resolution 表，不以"YAML 1.2 core"名义指代）**：
    # ①parse+compose 到节点树（**不构造**，标量原词素在节点层可得）；②按显式表做 tag 解析：
    #   bool 仅 `true|false`；int 仅 `^-?(0|[1-9][0-9]*)$`（前导零如 `010` 作字符串）；null 仅 `null|~|空`；
    #   其余标量（含 on/off/yes/no/y/n、1e3、八进制形）一律字符串；禁 anchor/merge 键与自定义 tag；
    # ③value 等定点位置在**节点层截取原词素**校验并 scale 补零转定点字符串（非十进制词素拒绝）；
    # ④构造 + 标量 to 列表化；⑤pydantic strict 校验。CF-DSL-FLAG 以旗舰与 compiler_bench_only
    # **原文字节**（后者规范文本见附录 A4）加载断言（`on:` 必得字符串键、`5.0` 必得 "5.00"）。
class PipelineSpec(BaseModel):
    pipeline: str; dsl_version: Literal[1]
    nodes: dict[str, NodeSpec]; entry: str
    loops: list[LoopSpec] = []; joins: list[JoinSpec] = []
    routes: list[RouteSpec]; default_route: Literal["fail_safe"]
    run_budget: RunBudget; snapshot_policy: Literal["pin_at_start"] = "pin_at_start"
```
`pipeline_digest = digest(PipelineSpec)`。`to` 成员语法：节点名 | `fail_safe` | `join:<id>`；fan-out = 单条 route 的多元素 to（V-04）。

### 1.2 保留名与固定语义（自足文本）
- 保留节点：`fail_safe`；保留命名空间：`sys.*`、裸名 `fail_safe`、前缀 `join:`。
- `SysOutcome = Literal["sys.crash","sys.timeout","sys.invalid_result","sys.error"]`（封闭）；`JsonValue = None|bool|int|str|list[JsonValue]|dict[str,JsonValue]`（digest 域禁 float，运行时非 digest 字段另允许 float，§0.1）。
- gate outcome 封闭枚举：hitl → {approved, rejected, gate_expired}；threshold → {pass, fail}。
- `broker: release` 节点 outcome 集固定 {released, release_failed}，无出边，终态经 §2.2b ledger 级固定映射。

### 1.3 静态校验规则（违规 → `PipelineValidationError(rule_id, locus)`）

| ID | 规则（依据） |
|----|--------------|
| V-00 | **引用有效性**：route.from_ ∈ nodes；route.to 各成员 ∈ nodes ∪ {fail_safe} ∪ {join:<已声明 id>}；join.to ∈ nodes；LoopEdge 两端 ∈ nodes 且该边对应至少一条已声明 route；threshold metric 的 producer_node ∈ nodes；join/loop id 各自唯一；wait_for/edges/to 元素无重复（HLD §4.2.6 首条） |
| V-01 | 节点三型互斥 + **字段适用矩阵**（§1.1 注）；threshold 必填 metric/op/value（§4.2.2） |
| V-02 | **注册与准入**：agent_type 已注册、status_set 非空、task_prefix 格式合法且全局唯一、contract_requires 与 contracts 包版本兼容、conformance attestation 有效且**三重绑定**（制品 digest ∈ execution manifest + contract_version + 套件版本，HLD §11.3——R2-02）——未注册 agent_type 在 V-05 之前即拒（重写恢复项，CF-DSL-02 覆盖） |
| V-03 | 节点名不占保留名/命名空间/`join:`前缀；entry 存在唯一；无不可达节点 |
| V-04 | **路由唯一性**：同 (from_, on) 至多一条 route（fan-out 经单条多元素 to 表达，多条即拒绝） |
| V-05 | route.on ∈（from 节点 status 全集 ∪ 其 gate outcome 集 ∪ sys.*） |
| V-06 | 穷尽性：每节点业务 status 逐条有路由或被 default_route 覆盖 |
| V-07 | 每个可达环至少含一条某 LoopSpec 声明边（等价判定：移除全部声明环边后图无环）；每条声明边隶属唯一 LoopSpec |
| V-08 | join.wait_for ≡ { r.from_ : "join:"+id ∈ r.to }（集合相等，按 to 成员判定） |
| V-09 | **每 activation 单送达（语义性质 + 保守判定）**：性质 = join 来源节点 s 每 activation 最大 dispatch 数 ≤1。判定：s 的多条入边合法当且仅当静态可证两两互斥（源自同一节点不同 outcome 的分支且中途未再汇合，可传递）；互斥性不可静态判定即拒绝。同节点互斥 outcome 多路指向同一 join 合法；互斥入边汇聚于中间节点 s 再入 join 亦合法（CS-05 反例形态） |
| V-10 | join.to 非 join（禁链式）；多源 join 来源由同一显式 fan-out 的分支派生、来源集在分支间构成划分；共同支配不得替代共同 fan-out |
| V-11 | **共同到达性**：对每个 join 来源 s，从其 scope fan-out 到 s 的路径上，每个节点的每个 outcome 分支须满足三者之一——仍在可达 s 的路径上、到达 Run 终局（fail_safe/terminal/release）、或经声明环边回流（受 V-12 双约束）；违者拒绝（HLD §4.2.6） |
| V-12 | **环边双约束**：①回流路径必然重经该 join 的共同 fan-out（重派全部来源分区）；②重经自身 activation 的共同 fan-out 之前不得先重经任何祖先 activation 的共同 fan-out；违任一即拒（HLD §4.2.6 条件(iii)） |
| V-13 | release 路径规则（照 HLD §4.2.5）：必经 hitl；release 可达路径上的 hitl approved 出边直达 release；release 无出边 |
| V-13b | **[HLD 勘误 HLD-Q1]** release-approval 型 hitl 须存在支配它的 **ReleasePlan 生产节点**（按 §2.3 produces 声明判定：produces 含 "release_plan"）；多候选生产者 → 取支配链上最近者，歧义（同深多者）拒绝 |
| V-14 | terminal 节点必有非空 success_on ⊆ status 全集，且**无出边**（非 success outcome 固定映射 fail_safe，编译期落表） |
| V-15 | hard-required（ProducerSelector 解析）与 threshold metric 生产节点：存在、可解析唯一、支配消费节点、消费同 series 结果；metric 的 field 须在该生产节点 produces 全部类型体的 gateable 字段中**唯一匹配**，歧义拒绝 |
| V-16 | retry.on ⊆ **RetryOutcome = {sys.crash, sys.error, sys.timeout}**（封闭枚举；`sys.invalid_result` 不可重试——HLD §4.3.2 字面；CF-DSL-16 反例固定为 invalid_result） |
| V-17 | hitl 分型静态判定：release 可达路径上的 hitl 为 release-approval 型、其余 plain-decision 型；分型进编译产物供运行时选择审批协议（HLD §4.4） |

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
| C-04 | submit_patch（Skill） | awaiting_patch | 可应用；单 Run 一次；**初始 series 单事务**（§3.3a：按 §0.2 格式签发初始 series_id、lineage(parent=None,base=snapshot)、tree_digest、current 推进）；request_id 重放返回同 series_id | queued（run_budget 起算） |
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
    series_candidate_id: str | None = None      # 引用本 task 预登记的 candidate；无 patch 任务为 None（R4-01）
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
- **PatchAttribution**：`patch_digest: str; repo_id: str; producer: Producer; motivation: str`；`Producer` 为判别联合：`AgentProducer{kind:"agent", agent_type, task_id, round}` | `ExternalProducer{kind:"external", principal}`（初始 series 的外部 Coding Agent 取后者，principal = Skill bearer 主体标识——R3-06）；`patch_digest = "sha256:" + hex(sha256(unified_diff 原文字节，统一 \n 行尾、保证结尾单换行；不含 description))`

### 2.5 ReleasePlan / ReleaseManifest / 授权

```python
class ReleaseAction(StrEnum): push_branch="push_branch"; gerrit_review="gerrit_review"
class ReleaseTarget(BaseModel): adapter: str; repo: str; branch: str; action: ReleaseAction
class ReleasePlan(ReportBase):       # Report 型：公共头承载 run/series/task/created/data_class/inputs
    tree_digest: str
    targets: tuple[ReleaseTarget, ...]              # 有序；执行按序；(adapter,repo,branch) 重复拒绝
    squash: bool = False
class ReleaseManifest(BaseModel):    # = Plan 无损规范化 + 环境绑定；含全部影响远端效果的字段
    snapshot_id: str; series_id: str; tree_digest: str
    targets: tuple[ReleaseTarget, ...]; squash: bool
    pipeline_digest: str; exec_manifest_digest: str
class ApprovalDecisionRequest(BaseModel):   # decision_submit 载荷（无 id，服务端签发）
    gate_instance_id: str; run_id: str
    verdict: Literal["approved","rejected"]     # reviewer 不在请求中——由 Approval 服务按 peer credential 映射生成（R3-09），不符映射拒绝并审计
    manifest: ReleaseManifest | None                # release-approval 型必填；plain 型 None
    evidence_refs: tuple[ArtifactRef, ...] = ()
class ApprovalDecision(ApprovalDecisionRequest): decision_id: str; reviewer: str; created_at: datetime  # 服务端补齐落 Ledger
class AuthorizationRecord(BaseModel):               # Ledger 行，非 bearer；revoke/consume 语义见下（HLD §8.2）
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
# 各 endpoint 请求/响应为具名模型（字段级定义如下，A0 收录）：
class PatchItem(BaseModel): repo_id: str; unified_diff: str; description: str
class CreateRunRequest(BaseModel): pipeline_id: str; target_spec: TargetSpec; request_id: str
class CreateRunResponse(BaseModel): run_id: str; state: str
class SubmitPatchRequest(BaseModel): series: list[PatchItem] = Field(min_length=1); request_id: str
class SubmitPatchResponse(BaseModel): accepted: bool; series_id: str; queue_position: int
class SnapshotInfo(BaseModel): snapshot_id: str; snapshot_manifest_ref: ArtifactRef
class RunStatusResponse(BaseModel):
    state: str; node_progress: dict[str, str]; loop_counters: dict[str, int]
    queue_position: int | None = None; snapshot: SnapshotInfo | None = None
class CancelRequest(BaseModel): request_id: str
class CancelResponse(BaseModel): state: str
class TraceEvent(BaseModel): seq: int; ts: datetime; run_id: str; task_id: str | None; type: str; payload: dict[str, JsonValue]
class SkillError(BaseModel): code: str; message: str; detail: dict[str, JsonValue] = {}
class ResultEnvelope(BaseModel):
    run_summary: RunSummary; feedback_report: ArtifactRef | None
    corrections: tuple[CorrectionRecord, ...]       # append-only，摘要之外返回（HLD §8.3）
```

| 操作 | 请求/响应 | 错误码（HTTP） |
|------|-----------|---------------|
| POST /runs（异步） | CreateRunRequest{pipeline_id, target_spec, request_id} → CreateRunResponse{run_id, state} | E-SKILL-VALIDATION(400)、E-SKILL-CAPACITY(503) |
| POST /runs/{id}/patches | SubmitPatchRequest{series: [PatchItem], request_id} → SubmitPatchResponse{accepted, series_id, **queue_position**}（重放返回同 series_id + **当前**队列位置，注明非首次快照——HLD §6.5） | E-SKILL-DUP-SUBMIT(409)、E-SKILL-UNAPPLICABLE(422，附首个失败 hunk 定位；**二进制 patch 段 v1 显式拒绝**，CC C-i)、E-SKILL-TOO-LARGE(413) |
| GET /runs/{id} | → RunStatusResponse{state, node_progress, loop_counters, queue_position?, snapshot?: {snapshot_id, snapshot_manifest_ref}（C-02 后非空；state=closed(snapshot_error) 即拉取失败形态）}——单一响应模型 | E-SKILL-NOT-FOUND(404) |
| GET /runs/{id}/result | → ResultEnvelope | E-SKILL-NOT-READY(425) |
| POST /runs/{id}/cancel | CancelRequest{request_id} → CancelResponse{state} | E-SKILL-FORBIDDEN(403) |
| （通用） | — | E-SKILL-IDEM-MISMATCH(422)、E-SKILL-AUTH(401) |
`PatchItem = {repo_id, unified_diff, description}`；应用序 = snapshot manifest 序。request_id 语义见 §0.2。

---

## 3. Activation 与 Series（HLD §4.2.4/§7.6.2/§4.5）

### 3.1 ActivationRecord 与传播（含 loop_vector 复制规则）

```python
class ActivationRecord(BaseModel):
    activation_id: str; run_id: str
    origin: Literal["root","fanout","loop"]; origin_node: str | None   # root=None；fanout=分派节点名；loop=loop_id（R3-10）
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
supersede 三条件（内联复述，权威 HLD §4.2.4）：①series 推进事务全量退役旧 series open activation 并作废计时器；②到达全 stale（①的防御兜底）；③环边采用同事务级联退役（§3.1 规则 4a）。CAS 守卫：到达/消费/分派/timeout 均校验自身 open ∧ 祖先链无 superseded ∧ series 为 current。恢复自 Ledger 重建全部 activation。

### 3.2 join 到达与消费（自足文本）
到达键 `(run_id, join_id, activation_id, source_node)` 唯一，重复到达丢弃并审计；到达 series ≠ current → 标 stale 丢弃并审计（CF-ACT-08）。全部 wait_for 源到达且 series 一致 → 单事务：各到达置 consumed + 下游 dispatch（父 scope，§3.1 规则 5）+ 作废该 activation 的 join 计时器；消费与分派 CAS 校验自身 open ∧ 祖先链无 superseded。timeout 自该 activation 首达起算，口径 §3.4。

### 3.3a 初始 series（C-04 单事务；R2-03）
校验完整 series 可应用 → 按 §0.2 格式签发初始 series_id（`SER-`+ulid；本文不使用特例字面量）→ 写 lineage（parent=None、base=snapshot、patches 全量 PatchAttribution，producer 为外部型，见 §2.4）→ 计算 tree_digest（§3.5）→ 推进 current → Run→queued。request_id 重放返回同 series_id；事务前崩溃 = 未受理（客户端重试），事务后崩溃 = 幂等返回。首个 task_complete 以该初始 series_id 为 expected_parent 接续 CAS 链。

### 3.3 series 推进（task_complete 复合事务，**两条封闭分支**——R4-01）
**分支 A（series_candidate_id=None，UT/Bench/Review 等无 patch 任务的常态）**：仅提交结果 + artifact 索引 + 幂等终态，**不签发 series、不推进 current、不触发任何失效**。
**分支 B（引用恰一个本 task 的 candidate）**：执行下列全步；引用他 task 的 candidate 或多 candidate → 拒绝，sys.invalid_result。
1. guard：Run ≠ publishing（是则 series 相关步骤降级 pending 记录，其余照常）；
2. CAS `current_series_id == expected_parent_series_id`——失败归 **sys.error**（合法并发竞争，可按节点 retry 策略重试；HLD"防并发丢 patch"）；
3. 结果 + artifact 索引转正 + 幂等终态；
4. 签发 series_id、写 lineage `{new, parent, contributed_by_task, patches}`、推进 current；
5. tree_digest 计算记录（§3.5）；
6. 失效链：未核销授权 revoke、待审批项作废、旧 series open activation 条件①全量退役。

### 3.4 计时口径
run_budget：自 C-04 起算，排除 paused 与 publishing 时段，queued 计入；触顶经 C-13。loop：计数器键 `(run_id, loop_id)`，环边通过 +1，**max_rounds: N = 环边允许通过 N 次、第 N+1 次通过请求在预算检查处拦截强制路由 fail_safe**（内联复述，权威 HLD §4.5）；wall_clock 自该 loop 首条环边首次通过起算，排除 paused/publishing。join timeout：`(run_id, join_id, activation_id)` 级，自首达起算，同口径。全部计时以 Ledger 暂停区间扣除实现。

### 3.5 tree_digest（应用后 tree OID 的规范组合；HLD §7.6.2）
1. 对每个 repo：以 bare object DB / 临时 index（无需 worktree）自 snapshot commit 依 series lineage 应用序 apply 全部该 repo patch，得 **git tree OID**；apply 失败：submit_patch 阶段即拒绝（E-SKILL-UNAPPLICABLE）；完成事务阶段失败（业务 fix-patch candidate 首次在此应用，可达）→ sys.error（T-b1）。
2. 确定性步骤：临时 index ← `git read-tree <snapshot commit tree>` → 逐 patch `git apply --cached --whitespace=nowarn` → `git write-tree` 得 OID；OID 表示 = `<object-format>:<hex>`（如 `sha1:...`，取仓库 object-format）。`line_i = repo_id + ":" + oid_repr`（repo_id 字符集 `[a-z0-9._-]+`，V-00 校验）；`tree_digest = "sha256:" + hex(sha256(UTF-8("\n".join(lines sorted by repo_id))))`，**无末尾换行**；golden vectors 覆盖多仓/空 patch 仓/等价 tree（R2-06）。
3. 性质：等价最终 tree ⇒ 等 digest（增删相消、异 patch 同果均一致）；BuildExecutor worktree 应用后复核 tree OID 一致，不一致 → sys.error（兜底为**校验**而非替代定义）。conformance 含等价 tree 用例 CF-SER-04。

### 3.6 snapshot manifest（自足文本）
`SnapshotManifest = list[{repo_id, remote, commit, path}]`，按 repo_id 升序规范化；snapshot_id 形式与引用语义见 §0.2；跨仓 patch 应用按 manifest 序，任一仓失败整组回滚。

---

## 4. 效应幂等（HLD §5.2）

### 4.1 键与调用面
```python
class EffectResult(BaseModel): return_value: JsonValue; artifact_refs: dict[str, ArtifactRef] = {}
def side_effect(effect_call_id: str, params: BaseModel, fn: EffectType, repeat_seq: int | None = None) -> EffectResult
# idem_key = digest({run_id, dispatch_id, effect_class, effect_call_id, effect_params_digest, repeat_seq})
```
succeeded 复用即返回存储的 EffectResult。**同键与调用约束（自足文本）**：
- `effect_call_id` 调用方提供、代码内稳定命名（`[a-z0-9_]+`），conformance 静态检查每逻辑调用点唯一命名，同 task 内唯一在册；显式重复执行由调用方给定 `repeat_seq` 迭代序。
- `effect_class` 由 fn 所属注册效应类型推导，自由函数不可包装（SDK 拒绝）；服务端交叉校验见 §5.1。
- `effect_params_digest = digest(params)`，params 内 ArtifactRef 以 digest 参与；canonical 全文存 params_ref。
- **不含 attempt**：同 (call_id, params) 重试/重放命中同一记录；非决定论重执行实参不同 → 新键；跨 attempt 遗留的同 call_id 旧在途异参记录经 attempt 启动对账定态（§4.3 三支），succeeded/unknown 不得改写为 abandoned。
- **异参新键允许集合（仅辖跨 attempt 定态记录）**：succeeded/abandoned → 放行（succeeded 仅同参精确键复用、不得跨参复用）；unknown → task 已随 sys.error 中止，无新键。干净终态 failed：**异参新 claim 一律放行新键**（异参 = 新逻辑效应，准入不受 disposition 辖；HLD "依类别策略放行"的字面）；**同键**再调用才按 failed_disposition 处置（§4.3）。
- 运行时拒绝：仅同一 attempt 内，同 call_id 存在未决（claimed/running）记录时的异参新 claim → 拒绝，task 报 sys.invalid_result。

### 4.2 EffectRecord 与迁移表
```python
class EffectRecord(BaseModel):
    idem_key: str; version: int; run_id: str; task_id: str; dispatch_id: str
    effect_class: str; effect_call_id: str; effect_params_digest: str; repeat_seq: int | None
    params_ref: ArtifactRef                       # canonical params 全文（内容寻址）——对账 probe 的参数来源（R2-05）
    state: Literal["claimed","running","succeeded","failed","abandoned","unknown"]
    result: EffectResult | None; error: EffectError | None; updated_at: datetime
    probe_attempts: int = 0; next_probe_at: datetime | None = None   # indeterminate 有限重试进度持久化（CS-19）
# EffectError = {category: Literal["validation","execution","transport","probe"], message: str, detail: dict}（封闭归类）
```
**迁移表（完整边集，自足）**：

| 从\到 | running | succeeded | failed | abandoned | unknown |
|-------|---------|-----------|--------|-----------|---------|
| claimed | worker ack 后启动 | 仅对账：probe 确认成功（补写 result） | 仅框架启动前判定失败（参数校验拒绝等；传输失败停留 claimed 待对账） | 对账：未发生 / replay_safe 退役 | 对账：不可判定（重试耗尽） |
| running | — | 效应完成 | 效应失败 | 对账：未发生 / replay_safe 退役 | 对账：不可判定（重试耗尽） |
| succeeded/failed/abandoned/unknown | 终态不迁移；abandoned 之上重执行 = 同键 version+1 新记录 | | | | |

### 4.3 Probe 与 failed 处置
```python
class ProbeOutcome(StrEnum): confirmed_happened="confirmed_happened"; confirmed_not_happened="confirmed_not_happened"; indeterminate="indeterminate"; not_supported="not_supported"
class ProbeResult(BaseModel): outcome: ProbeOutcome; result: EffectResult | None  # confirmed_happened 时必填。**Reconciliation 协议（R4-04 定案）**：probe 在专用 reconciliation worker 子进程执行（无 Ledger 写权限、进程组/心跳语义同 §5.1.2；通道为专用 socketpair，命令面仅 `probe_report{idem_key, version, probe_attempt, ProbeResult}` 一条——数据面封闭枚举不被突破，effect_claim/task_complete 等对其不可达）。派发消息 `ProbeDispatch{idem_key, version, probe_attempt, params_ref}`；**事务点定案**：probe_attempts 递增与 next_probe_at 写入在**派发事务**（spawn 前）——worker 执行后/回写前崩溃时该次已计数（保守、上限不被突破）；probe_report 以 (idem_key, version, probe_attempt) CAS 提交状态迁移，陈旧组拒绝并审计。派发前/执行后/回写前三点崩溃注入 = CF-EF-10。probe 必须只读、无副作用（conformance 断言）
class EffectType(Protocol):
    effect_class: ClassVar[str]; replay_safe: ClassVar[bool]
    supports_probe: ClassVar[bool]                # 静态能力位（对账路径选择依据）
    probe_retry_max: ClassVar[int]; probe_retry_interval_sec: ClassVar[int]   # indeterminate 有限重试参数（P-04）
    failed_disposition: ClassVar[Literal["raise","retry_new_version"]]; failed_max_retries: ClassVar[int]
    def probe(self, params, record) -> ProbeResult: ...
```
对账映射（**probe 优先**）：supports_probe → 先 probe：confirmed_happened → succeeded（复用）；confirmed_not_happened → abandoned；indeterminate → 有限重试（§4.2 进度字段）耗尽后——**若 replay_safe → 退役 abandoned 版本化重放（fallback）**，否则 unknown + sys.error（不得当作 not_happened）。not_supported ∧ replay_safe → 退役重放；两能力皆无 → unknown + sys.error。四组合（supports_probe × replay_safe）全覆盖 = CF-EF-02 轴定案。failed 同键再调用：按 failed_disposition——raise（返回存储 error）或 retry_new_version（版本化重试至 failed_max_retries，超限 raise）。
注册面：entry-point namespace `codingsystem.effects`；装配时校验 effect_class 唯一、能力声明齐备、类别硬性要求（build.* 可 probe；board.* 可 probe 或 replay_safe；publish.* 仅 broker，业务注册即拒绝）。

---

## 5. 安全接口（HLD §7.1/§8）

### 5.1 Control-plane 命令集

**worker 数据面 socket**（per-task socketpair；命令封闭枚举）：

| 命令 | 载荷 | 语义 |
|------|------|------|
| heartbeat | seq | 租约信号（间隔配置）；编排侧超时 = 租约失；worker 侧 socket EOF = 通道失 → killpg 自杀（HLD §5.1.2 双向覆盖） |
| effect_claim | effect_call_id, effect_class, params_ref, repeat_seq | 响应为封闭联合 `{action: execute(附 idem_key,version) | reuse(附存储 EffectResult) | error(附 EffectError)}`；服务端以注册表交叉校验载荷 effect_class 与 fn 注册类型，不符 → sys.invalid_result 并审计（Kimi M-03）；写 claimed（execute ack 前禁执行） |
| effect_transition | idem_key, **version**, expected_state, to∈{running,succeeded,failed}, result?/error? | (idem_key, version, expected_state) 三元 CAS；陈旧 version/状态不符 → 拒绝并审计（R4-02，CF-EF-09） |
| trace_append | 事件批（≤64 条/批，≥1s 批间隔——背压约定） | 追加 |
| blob_begin | size_hint, **data_class** → lease_id + 临时路径 | **lease 先于写入**（HLD §7.5）；续租经 heartbeat 隐含 |
| blob_commit | lease_id, digest | fsync→rename→digest 复验→索引暂存转正，原子；失败保持 lease 待 abort/GC |
| blob_abort | lease_id | 释放 lease + 清理临时文件 |
| series_candidate_submit | candidate_patches, expected_parent_series_id → candidate_id（ulid，绑定本 task；**每 task 至多一个**，重复提交拒绝） | 预登记（不改 current） |
| task_complete | HandoffResult | §3.3 复合事务 |
崩溃恢复：lease 未 commit → 超年龄 GC；已 rename 未入索引 → 孤儿 GC；索引在 blob 失 → 消费方 sys.error（HLD §7.5 各点覆盖，用例 CF-BLOB-*）。

**approval socket**：内部命令 `DecisionSubmitCommand{request: ApprovalDecisionRequest, reviewer: str}`——reviewer 由 **Approval 服务**按 Review CLI 的 peer credential 映射得出后填入（外部 CLI 请求不含该字段）；编排进程信任 approval socket（Approval 服务属框架交付 TCB，socket peer 即认证）。响应 `DecisionSubmitResult{decision_id, token_id | None}`（二者编排事务内生成；plain 型 token_id=None）——release-approval 型事务 = 决定 + 新鲜度 CAS（§2.5）+ 授权记录 + gate CAS + resume outbox（outbox 项含 token_id 供 release dispatch）；plain 型 = 决定 + gate CAS + outbox。
**broker socket**：`authorization_consume{token_id, task_id, release_manifest_digest}`（§2.2a 三支）、`release_outcome{task_id, outcome, reason, remote_refs}`。
**特权运维**：`adjudicate{run_id, adjudication_id, verdict, evidence_refs}`——guard：Run=publishing ∧ 强制 probe 后 unknown ∧（verdict∈confirm_* ⇒ evidence_refs 非空）∧（confirm_not_released ⇒ broker task 静默已确认）；`post_close_correction{run_id, CorrectionRequest}`。
**pending**：`pending_register{run_id, event: PendingEvent}`——判别联合整体提交（各型载荷见 §2.4），dedup_key 为联合公共字段（CS-10 闭合）。
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
class ProviderExecutionConfig(BaseModel):        # provider_policy_digest 的 digest 域（HLD D12——R4-03）
    provider_id: str; provider_type: str
    endpoint_identity: str                        # 规范化端点身份（scheme://host[:port]/path，凭据值除外）
    trust_policy: dict[str, JsonValue]            # TLS/信任锚策略
    routing: dict[str, JsonValue]                 # 模型绑定 / cascade 策略
    allowed_max: DataClass
# provider_policy_digest = digest(排序的 ProviderExecutionConfig 列表)；仅 secret 值排除——
# 端点改向必失配、密钥轮换不失配（CF-SM-12 两用例）
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
class ToolFact(BaseModel): tool: str; query: str; result: str; data_class: DataClass   # 工具按查询对象密级出生标注
class LogExcerpt(BaseModel): ref: ArtifactRef; lines: str; data_class: DataClass
class SourceExcerpt(BaseModel): path: str; start: int; end: int; content: str   # 有界：end-start ≤ 400；密级恒 internal_code
class EvidencePacket(BaseModel):
    facts: list[str]                     # 派生文本，密级=生成时所引成员最大（builder 计算）
    negative_facts: list[ToolFact]
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
| CF-DSL-01a/b | V-01 字段适用矩阵越界（hitl 带 metric）/ 合法三型 | 加载 | 拒 V-01 / 过 |
| CF-DSL-03a/b | 节点名占用 `fail_safe` / 三节点线性合法图 | 加载 | 拒 V-03 / 过 |
| CF-DSL-04a/b | 同 (from,on) 双 route / fan-out 单条多元素 to | 加载 | 拒 V-04 / 过 |
| CF-DSL-05a/b | on 拼错 status / 全 status 正确 | 加载 | 拒 V-05 / 过 |
| CF-DSL-06a/b | 某 status 无路由且 default_route 缺失（YAML 删行）/ default_route 兜底 | 加载 | 拒 V-06（缺失即 schema 拒）/ 过 |
| CF-DSL-07a/b | 未声明环边的可达环 / 声明齐备 | 加载 | 拒 V-07 / 过 |
| CF-DSL-08a/b | wait_for 多列一源 / 与路由源集相等 | 加载 | 拒 V-08 / 过 |
| CF-DSL-10a/b | 链式 join / 共同支配替代共同 fan-out | 加载 | 均拒 V-10 |
| CF-DSL-13c | 非 release 路径 hitl 的 approved 出边不直达 release | 加载 | 通过（V-13 限定域断言） |
| CF-DSL-09a | 同节点互斥 outcome 双路由入同 join | 加载 | 通过 |
| CF-DSL-09b | 非互斥多入边汇聚于来源节点 | 加载 | 拒，V-09 |
| CF-DSL-09c | 互斥入边汇聚于中间节点再入 join | 加载 | 通过（CS-05 形态） |
| CF-DSL-11a | 互斥 outcome 致来源必然缺席 | 加载 | 拒，V-11 |
| CF-DSL-12a/b | 分支内回环 / 跨祖先回环 | 加载 | 拒，V-12 |
| CF-DSL-13a | V-13b 反例：release-approval hitl 无支配 ReleasePlan 生产者 | 加载 | 拒，V-13b |
| CF-DSL-13b | 同深双 ReleasePlan 生产者 | 加载 | 拒（歧义 fail-closed） |
| CF-DSL-14a/b | terminal 无 success_on 或带出边 / 合法 terminal | 加载 | 拒 V-14 / 过 |
| CF-DSL-15a/b | metric 生产者不支配 gate；field 在 produces 多类型体歧义 / 唯一支配 | 加载 | 拒 V-15 / 过 |
| CF-DSL-16a/b | retry.on 含 sys.invalid_result / 三值合法 | 加载 | 拒 V-16 / 过 |
| CF-DSL-17a/b | 分型判定：release 路径 hitl 编译产物标 release-approval / 旁路 hitl 标 plain | 加载 | 分型正确落编译产物 |
| CF-DSL-FLAG | HLD §4.2.1 旗舰 YAML **原文**与 compiler_bench_only 原文 | 加载 | 全部通过且编译产物字段齐全（R2-01 断言） |
| CF-DSL-PROP | 随机图生成器（含环/嵌套 fan-out/join，参数化规模） | 批量加载 | 性质断言（model checking）：通过图必满足 V-09 基数、V-11 可达、**V-07 环全覆盖预算、V-13 release 必经 hitl**；拒绝图给出 rule_id；无 panic |

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
| CF-SM-12 | provider 配置两变体 | 端点改向 / 仅密钥轮换 | 前者 D12 失配 → C-14；后者不失配（R4-03） |
| CF-LED | 凡 §2.1/§3.3/§3.3a/§5.1 标注"单事务"的命令 | **参数化通则**：每命令提交点前、后各注入一次 kill | 前注入=命令未发生（幂等重放同果）；后注入=效果完整恰一次（M-02 规则；07 按命令清单枚举点位） |

### 6.3 CF-EF（效应）
| ID | 前置 | 动作 | 期望 |
|----|------|------|------|
| CF-EF-01 | 各态记录 | 迁移表全边尝试 | 合法边成功；非法边拒绝（含 claimed→succeeded 仅对账路径可达） |
| CF-EF-02 | claimed/running 遗留 × {可 probe, replay_safe, 皆无} × probe 四值 | attempt 启动对账 | 单元格规则：§4.3 映射（confirmed_happened→succeeded 复用原 EffectResult；not_happened→abandoned；indeterminate→重试 probe_retry_max 次后 unknown+sys.error；not_supported+replay_safe→abandoned+版本化重放；皆无→unknown+sys.error） |
| CF-EF-03 | 不可重放效应，probe indeterminate | 对账 | **零重放断言**（不得当 not_happened） |
| CF-EF-04 | failed 记录同参再调用 × 两 disposition | side_effect | raise 返回存储 error / retry_new_version 版本化至上限后 raise |
| CF-EF-05 | 跨 attempt 定态 {succeeded,abandoned,unknown} + 干净终态 failed × 异参新 claim | claim | succeeded/abandoned 放行新键（succeeded 不跨参复用）；unknown 无新键（task 已终止）；failed × **异参** → 放行新键（准入不受 disposition 辖）；failed × **同参** → 按 disposition 展开（raise → 返回存储 error；retry_new_version → 同键版本链至上限后 raise）——与 §4.1 idem_key 定义一致（R3-03 终修） |
| CF-EF-06a | 代码级重复 call_id 命名 | conformance 静态检查 | 拒绝（唯一命名断言） |
| CF-EF-06b | 同 attempt 同 call_id 未决 | 异参 claim | 拒绝，sys.invalid_result |
| CF-EF-09 | v1 abandoned、v2 running | v1 迟到 succeeded transition | (key,version,state) CAS 拒绝并审计，v2 不受污染（R4-02） |
| CF-EF-10 | ProbeDispatch 已计数 | 派发前/执行后/回写前三点 kill | attempt 上限不被突破；重放同组 CAS 幂等（R4-04） |
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
| CF-ACT-08 | 到达 series ≠ current | join 到达 | stale 丢弃并审计、组不受污染、同 series 新到达照常成组（R-04） |
| CF-SER-01 | 双 task 并发完成 | series CAS | 单胜；败者 sys.error 可 retry |
| CF-SER-02 | 待审批+未核销授权+旧 activation | series 推进 | 三失效同事务 |
| CF-SER-03 | publishing | task_complete | series 步骤降级 pending；结果/artifact 照常 |
| CF-SER-04 | 增删相消 / 异 patch 同果两组 | tree_digest | 等价 tree 同 digest（golden vectors） |
| CF-SER-05 | worktree 应用后 | BuildExecutor 复核 | OID 不一致 → sys.error |
| CF-SER-06 | submit_patch | §3.3a 单事务 + request_id 重放 + CF-LED 点位 | 初始 series/lineage/tree_digest/current 齐备；重放同 series_id |

### 6.5 CF-AUTH / CF-IPC / CF-BLOB / CF-SKILL / CF-DC / CF-COR / CF-REC / CF-UP / CF-FIX
| ID | 前置 | 动作 | 期望 |
|----|------|------|------|
| CF-AUTH-01 | 三分量各自过期 | decision_submit | 新鲜度 CAS 逐分量拒绝并提示重审 |
| CF-AUTH-02 | 单授权 | 并发双 consume | 恰一成功 |
| CF-AUTH-03 | 授权已过期 | consume | 不核销；closed(release_failed, reason=authorization_expired) |
| CF-AUTH-04 | D12 digest 漂移 | consume | E-CP-D12-MISMATCH；授权不动；C-14 触发 |
| CF-AUTH-05 | broker task 中断恢复，授权 consumed_by=本 task | 恢复续跑 | 视为有效、继续发布 |
| CF-AUTH-06 | RestrictedOp 序列 | 一一对应校验 | 多/少/异 ref/异 content_commit/自供 change_id 五拒 |
| CF-IPC-01 | worker socket | 发送特权命令 | 不可达/拒绝并审计 |
| CF-IPC-02 | worker A 连接 | 为 task B 提交 side_effect | 拒绝并审计 |
| CF-IPC-03 | deploy 资产真实 UID/权限 | E2E 全链 | 隔离断言全过 |
| CF-IPC-04 | outbox 项 | 重复投递 | 同结果、不重复建 task |
| CF-IPC-05 | 编排失联 + GBS 孙进程存活 | 心跳超时 | worker killpg 自杀含孙进程；probe 对账续 |
| CF-BLOB-01 | 无 lease 临时文件 | GC | 回收；有 lease 不回收（lease 先行断言 + data_class 出生标注断言） |
| CF-BLOB-02 | blob 提交链 | rename 前/后、索引前逐点 kill | 恢复语义逐点断言（CF-LED 点位） |
| CF-BLOB-03 | 上传中 | GC 并发 | 互不干扰 |
| CF-BLOB-04 | 索引在 blob 失 | 消费 | sys.error |
| CF-BLOB-05 | blob 内容被篡改（digest 不符） | 读取消费 | 读侧校验失败 → sys.error + 审计（Q-03） |
| CF-SKILL-01 | 同 request_id | 同/异载荷重放 | 同载荷复用结果；异载荷 E-SKILL-IDEM-MISMATCH |
| CF-SKILL-02 | 已提交 series | 再 submit | 409 |
| CF-SKILL-03 | 不可应用 series | submit | 422 + 首个失败 hunk 定位；二进制 patch 段拒 |
| CF-SKILL-04 | Run 未关闭 | GET result | 425 |
| CF-SKILL-05 | TargetSpec 三型 + 未知项/空集 | create | 解析正确/逐项拒绝 |
| CF-SKILL-06 | create 异步 | snapshot 失败 | GET 呈现 closed(snapshot_error)；GET 响应单一模型断言 |
| CF-DC-01 | 多密级成员 | 聚合 | 取最大 |
| CF-DC-02 | 缺失标签 | 消费 | 按 secret（fail-closed） |
| CF-DC-03 | cascade 多跳 | 每跳校验 | 越权跳拒绝 |
| CF-DC-04 | build_log 摘录含源码行 | 标注 | 升 internal_code |
| CF-DC-05 | worker 自报 ref 密级 ≠ 索引 | 校验 | 拒绝 sys.invalid_result |
| CF-COR-01 | 复查窗口检出迟到发布 | 自动流程 | 告警 + CorrectionRecord 生成（服务端字段）+ 终态不变 |
| CF-COR-02 | 同修正重复/并发提交 | post_close_correction | 幂等键去重、单条落账 |
| CF-COR-03 | 有修正的 Run | GET result | ResultEnvelope.corrections 呈现、RunSummary 不含 |
| CF-REC-01 | 崩溃恢复 | 重执行 | 复用既有 task/dispatch 记录（dispatch_id 不变）、不产生新分派事件 |
| CF-REC-02 | 恢复后同参效应 | claim | 命中崩溃前记录（键跨重启稳定断言） |
| CF-UP-01 | optional 上游缺失 | dispatch | UpstreamItem.ref=None 显式呈现；hard-required 缺失按 V-15 静态不可达（运行时防御拒绝） |
| CF-FIX-01 | compiler fixture：consume 无 / produce BuildReport(含 output_refs、fix_patches 各 1) | 装配+往返 | 注册过、schema 往返过、attestation 三重绑定过 |
| CF-FIX-02 | ut fixture：consume BuildReport / produce UTReport(双 board、fix_patch 1) | 同上 | 同上 + candidate 引用分支 B 走通 |
| CF-FIX-03 | benchmark fixture：consume BuildReport / produce BenchReport(regression_pct 定点) | 同上 | 同上 + gateable 字段解析 |
| CF-FIX-04 | review fixture：consume 三 Report(一缺失) / produce ReviewReport | 同上 | 同上 + inputs 缺失显式化（CF-UP 交叉） |
| CF-FIX-05 | ci fixture：consume ReviewReport / produce ReleasePlan(ReportBase 头) | 同上 | 同上 + V-13b produces 判定 + ci_plan_task_id 绑定 |

## 7. 附录
- **A0 类型索引**：本文全部具名类型及定义位置清单（contracts 包按此逐一交付）：§0 SysOutcome/DataClass…；§1 PipelineSpec 族/RetrySpec/预算族；§2 注册与消息族/Report 族/Release 族/ApprovalDecision/AuthorizationRecord/ExecutionManifest/RunContext/TargetSpec 族/SkillError/PatchItem/CreateRunRequest·Response/SubmitPatchRequest·Response/RunStatusResponse·SnapshotInfo/CancelRequest·Response/ResultEnvelope/PendingEvent 联合/RoundDigest/PatchAttribution/Producer 联合/EffectError/TraceEvent/ApprovalDecisionRequest/DecisionSubmitCommand·Result/ProbeDispatch·probe_report/ProviderExecutionConfig；§3 ActivationRecord；§4 EffectRecord/EffectResult/ProbeResult/EffectType；§5 命令载荷族/RestrictedOp 族/ProviderPolicy/CorrectionRequest/Record/EvidencePacket 族/TraceEvent（下条）。
- **A1 开放项（纯实现，均已收窄）**：task 序号分配器持久化布局；CompiledPipeline 内部 schema。`TraceEvent = {seq: int, ts, run_id, task_id: str|None, type: str, payload: dict}`——消费方对未知 type 前向兼容忽略，envelope 纳入版本规则（不再列开放项）。
- **A2 追溯矩阵**：§0↔HLD D6/D12；§1↔HLD §4.2（V-13b↔勘误 E-01/HLD-Q1）；§2↔HLD §4.3/§4.4/§6/§8.2-8.3（§2.2↔§8.3 三支）；§3↔HLD §4.2.4/§4.5/§7.6.2（§3.5↔应用后 tree 组合）；§4↔HLD §5.2；§5↔HLD §7.1/§7.5/§8.5；§6↔HLD §11.3/附录 B-6。
- **A3 变更记录**：v0.1 初稿；v0.2 = 57 条修订；v0.3 = 47 条修订；v0.4 = 34 条修订；v0.5 = 第四轮 21 条修订（loader 显式 resolution 表与节点层词素定案、task_complete 双分支 + candidate_id、effect 三元 CAS、ProviderExecutionConfig digest 域、reconciliation 派发/回报协议与事务点、DecisionSubmitCommand 两跳身份、迁移表内联、failed 异参终修、§6 逐 case 补全、A4 子集流水线规范文本）；contract_version 1.0.0.dev1。

## 8. 附录 A4：compiler_bench_only.yaml（规范原文——CF-DSL-FLAG 断言以此字节加载）

```yaml
pipeline: compiler_bench_only
dsl_version: 1
nodes:
  compiler: {agent_type: compiler}
  benchmark: {agent_type: benchmark}
  bench_gate: {gate: threshold, metric: benchmark.regression_pct, op: "<=", value: 5.0}
  summary: {agent_type: review, mode: bench_summary, terminal: true, success_on: [pass]}
entry: compiler
routes:
  - {from: compiler, on: build_passed, to: benchmark}
  - {from: benchmark, on: bench_done, to: bench_gate}
  - {from: bench_gate, on: pass, to: summary}
default_route: fail_safe
run_budget: {max_wall_clock_min: 240}
```
（status 名依 CF-FIX fixture 注册集；`value: 5.0` 词素路径与 `on:` 字符串键在本文件上同时得证；无环故无 loops 节，V-07 空覆盖合法。）
