# 01 扩展逐条映射（设计审定 2026-11-11，M0a 处置）

来源：HLD v2.14 附录 B 第 7 组。原文条目保持不变；task-003 按设计审定 2026-11-11（M0a 处置）更新批次和字段子键。父键只作索引，不重复归批；无子键的原始条目自身为叶键。日期空白表示尚未发生，不代表契约已三方通过。

总前提原文：7. **v2.x 扩展项（01 需同步扩展；上游切换至本 HLD 并更新 A2 追溯矩阵）**：

## B7-1 **注册与 DSL**

来源 HLD 附录 B:981。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-1-1 | 注册信息按 mode 声明（status_set、produces、series_effect、input_requirement、所需资源、capabilities）及 CF-FIX 注册集按 mode 拆分 | CF/验收 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-1-2 | DSL 新字段 `input`、`release_requires`、`accept_unverified_release`、镜像节点 `rpm_precheck`、Benchmark `config.mode`、Optimization `max_opt_rounds` 及 §4.2.6 三条规则的形式化——V-13b/V-15 维持普通支配 | schema/字段、规则/约束 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-1-2-bench-opt-syntax | Benchmark config.mode 的取值集合与缺省、Optimization max_opt_rounds 字段；loop budget ≥ 2×max_opt_rounds / ≥ 1+max_opt_rounds 的静态规则；仅语法与静态规则 | 静态 schema/校验规则 | 第一批；设计审定 2026-11-11（M0a 处置） | P1 原文示例加载；Demo 第 4 步 | 设计 / 开发 |  |  |  |  |
| B7-1-2-rules-rest | §4.2.6 规则③优化重验证的形式化、规则①对 bench_report 的适用、V-13b / V-15 维持普通支配；共同汇合定义引用 B7-1-3 | 静态形式化/规则消费 | 第一批；设计审定 2026-11-11（M0a 处置） | P1 | 设计 / 开发 |  |  |  |  |
| B7-1-2-demo-dsl | input、release_requires、accept_unverified_release、rpm_precheck 的语法字段；净变更规则定义见 B7-1-4，共同汇合定义见 B7-1-3，其余静态规则定义见 B7-1-2-rules-rest | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 | 设计 / 开发 |  |  |  |  |
| B7-1-2-mock-bench-opt | Benchmark config.mode 与 Optimization max_opt_rounds 的运行时语义；字段语法、取值/缺省及 budget 静态规则只引用 B7-1-2-bench-opt-syntax | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock | 设计 / 开发 |  |  |  |  |
| B7-1-3 | 规则①（release_requires）与规则③（优化重验证）共用单独形式化的"汇合必经"定义 | 规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-1-4 | 规则②为 input: none 的净变更数据流分析 | 规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-1-5 | 另加 V 规则：`gate_expired` 目标 ≠ `approved` 目标、`on: sys.timeout` 只能指向 fail_safe、保留命名空间 `sys.*`（含 `sys.baseline_build`） | 规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-1-6 | 四份示例流水线（§4.2.1 示例一至四原文）作为校验器验收用例，并替换 01 附录 A4。 | CF/验收 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
## B7-2 **状态机与等待（E-02）**

来源 HLD 附录 B:982。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-2-1 | ExternalWait 的 `gateway_session` 类与 phase、`external_timeout_min`、`task_suspend` guard（无其他在途效应）、`sys.superseded`、远程作业 `cancel_pending` 与配额恰一次归还、wake 在 running 下不迁移 | 命令/接口、迁移/守卫 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-2 | paused(wait) 成因集合 | 迁移/守卫 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-3 | ExternalWait 记录、wake outbox 与消费协议 | schema/字段 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-4 | `sys.await_external` 保留结果（V-05/V-06 排除于路由穷尽） | 结果状态枚举/DSL 穷尽校验（01 §1.3/§2.3） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-5 | 分派前资源授予与 awaiting_resource | 调度状态/资源授予迁移守卫（01 §2.1/§2.3 扩展） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-6 | C-07/C-13/§3.4 同步（全集计时条件、paused 期预算到期） | 迁移/守卫 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-7 | `input: none` 初始空 series 同事务签发（created → queued 新边）与 submit_patch 拒绝语义 | 命令/接口、迁移/守卫 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-8 | §4.3.5 放行谓词进入核心迁移表——C-16 terminal_success、§2.5 审批 CAS（含 `acknowledged_gaps` 与各报告"通过"谓词）、核销前 consume 复核均检查 | 迁移/守卫、规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-9 | 进入 publishing 后的超时只登记、不改 C-10/C-11 的 released 映射与 release_outcome 两值 | 迁移/守卫 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-10 | 核销复核不通过 → ConsumeRejected(reason = `gaps_changed`) + ledger 级 release_failed 映射（ConsumeRejected 原因枚举同步） | 迁移/守卫 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-11 | 证据链含 ci_plan、Review 与提供基线的 sys.baseline_build task | 证据链选择规则（01 §2.5 ReleaseManifest/授权守卫扩展） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-12 | 登录等待超时固定 fail_safe | 超时路由规则（01 §2.1、§3.4 扩展） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-13 | `external_timeout_min` 无环节点缺省 | DSL 配置默认值/计时规则（01 §1.1、§3.4 扩展） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-2-14 | 创建优化计划的准入核对与 `E-PLAN-NO-CAPACITY` | 计划创建准入守卫/错误码（01 §3.3 扩展） | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock | 设计 / 开发 |  |  |  |  |
| B7-2-15 | `E-SKILL-EMPTY-SERIES` 入 §2.7 错误码表。 | Skill 错误码（01 §2.7） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
## B7-3 **worker 数据面（E-03）**

来源 HLD 附录 B:983。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-3-1 | `task_suspend`、`resource_lease_release`、`image_commit`、`profile_put`、`remote_build_submit`、`remote_build_fetch_logs` 的载荷、幂等域、归属校验与注册表 | 命令/接口 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-3-2 | Gateway 构建 socket 与运维会话 socket 命令（`session_install`）。 | 命令/接口 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
## B7-4 **效应**

来源 HLD 附录 B:984。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-4-1 | 新增效应类别 image.* / remote_build.* / profile.* 的 probe 契约（远程构建效应标记 = idem_key 指纹 + version；ProbeOutcome 增 `deferred`；远程构建 probe 有界（提交 intent 含提交前最大构建号，扫描范围外 → indeterminate）；`backend_source_input_unsupported`；`base_mismatch` → `image_failed_exhausted`；镜像 probe 按 idem_key 查索引） | 规则/约束 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-4-1-deferred | ProbeOutcome 增 deferred 的枚举值与挂起语义；远程具体 probe 行为不在此定义 | 共享枚举/挂起协议 | 第一批；设计审定 2026-11-11（M0a 处置） | P1 | 设计 / 开发 |  |  |  |  |
| B7-4-1-image-failure | backend_source_input_unsupported、base_mismatch → image_failed_exhausted 的失败分类与映射 | 错误分类/结果映射 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 | 设计 / 开发 |  |  |  |  |
| B7-4-1-image-demo | 可选 mic 的效应、入库与引用操作契约（字段见 B7-4-2-demo-record） | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo mic | 设计 / 开发 |  |  |  |  |
| B7-4-1-image-profile-probe | image.* / profile.* probe 行为、镜像 probe 按 idem_key 查索引（字段见 B7-4-2-record-rest） | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P3 / P4 | 设计 / 开发 |  |  |  |  |
| B7-4-1-remote-build | remote_build.* 效应标记指纹/version、扫描界与远端 probe 行为；共享 deferred 枚举与挂起语义引用 B7-4-1-deferred，镜像失败映射引用 B7-4-1-image-failure | 字段子键 | 第三批；设计审定 2026-11-11（M0a 处置） | P6 | 设计 / 开发 |  |  |  |  |
| B7-4-2 | ImageRecord。 | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-4-2-demo-record | 父键原文的字段组：ImageRecord 最小入库字段 | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo mic | 设计 / 开发 |  |  |  |  |
| B7-4-2-record-rest | 父键原文的字段组：ImageRecord 其余字段 | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P3 / P4 | 设计 / 开发 |  |  |  |  |
## B7-5 **报告与消息**

来源 HLD 附录 B:985。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-5-1 | ImageReport（构建输入闭包、base 标识、读回的实际构建输入、rpm_precheck、base_mismatch） | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-1-image-schema | ImageReport 构建输入闭包、base 标识、读回的实际构建输入（本地 gbs）、rpm_precheck、base_mismatch schema；Quickbuild 读回语义见 B7-5-15 | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo 本地构建 | 设计 / 开发 |  |  |  |  |
| B7-5-2 | Quickbuild 后端能力声明与 `comparison = unverifiable` 语义 | 能力声明 schema/可比性枚举与判定语义（HLD §7.6.1；01 §2.4 扩展） | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-2-local-min | 能力声明最小 schema：source_input、comparison 两项及取值枚举；LocalGbsBackend 声明与加载期检查对 local 后端的判定 | 最小能力 schema/本地静态规则 | 第一批；设计审定 2026-11-11（M0a 处置） | P1；Demo 第 2 步 | 设计 / 开发 |  |  |  |  |
| B7-5-2-schema | 其余能力项与 Quickbuild 能力声明、加载期检查；source_input/comparison 的最小 schema 与枚举只引用 B7-5-2-local-min，不重复定义 | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock | 设计 / 开发 |  |  |  |  |
| B7-5-2-actual | 父键原文的字段组：具体能力取值、读回与证据等级结论 | 字段子键 | 第三批；设计审定 2026-11-11（M0a 处置） | P6 | 设计 / 开发 |  |  |  |  |
| B7-5-3 | BenchReport 扩展字段（mode、gate_eligible、validation_complete、逐指标四值与区间、spec_inconclusive_count、opt_gain_pct、opt_verdict、comparison、baseline_revoked/baseline_unavailable） | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-3-gate-fields | DSL gate 条件可引用的 BenchReport 字段名与类型，如 gate_eligible；不含判定语义 | 静态字段名/类型 | 第一批；设计审定 2026-11-11（M0a 处置） | P1 | 设计 / 开发 |  |  |  |  |
| B7-5-3-decision-core | mode、gate_eligible、validation_complete、opt_verdict 的判定语义；字段名/类型由 B7-5-3-gate-fields 供静态加载引用；comparison 三值与 comparison_unverifiable 的定义见 B7-5-16 | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-5-3-measurement | 逐指标四值与区间、spec_inconclusive_count、opt_gain_pct、baseline_revoked、baseline_unavailable 的业务字段与语义 | 字段子键 | 第三批；设计审定 2026-11-11（M0a 处置） | P7；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-5-4 | SuiteVersion / BenchPolicy / SPEC / MeasurementRecord schema | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见 load / business 子键 | 设计 / 开发 |  |  |  |  |
| B7-5-4-load | 套件锁定身份、suites: auto 与显式选择、指标 absolute / relative 依赖的加载期最小 schema；不含统计策略或测量记录 | 加载期最小 schema | 第二批；设计审定 2026-11-11（M0a 处置） | P4 | 设计 / 开发 |  |  |  |  |
| B7-5-4-business | 统计策略、测量记录及 SuiteVersion / BenchPolicy / SPEC / MeasurementRecord 其余业务字段；加载期字段引用 B7-5-4-load | 业务 schema/统计与测量 | 第三批；设计审定 2026-11-11（M0a 处置） | P7 | 设计 / 开发 |  |  |  |  |
| B7-5-5 | OptimizationPlan 与 OptimizationReport | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-5-core | 父键原文字段组：OptimizationPlan 核心与 OptimizationReport 判定字段骨架 | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-5-5-business | 父键原文字段组：OptimizationPlan 的 Profile 新鲜度及 OptimizationReport 真实业务字段 | 字段子键 | 第三批；设计审定 2026-11-11（M0a 处置） | P7；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-5-6 | Profile 记录与兼容字段 | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见 core / compat 子键 | 设计 / 开发 |  |  |  |  |
| B7-5-6-core | Profile 记录的存取、引用、待验区与入库 | schema/存储命令 | 第二批；设计审定 2026-11-11（M0a 处置） | P3 | 设计 / 开发 |  |  |  |  |
| B7-5-6-compat | Profile 兼容判定字段 | schema/兼容性谓词 | 第三批；设计审定 2026-11-11（M0a 处置） | P7 | 设计 / 开发 |  |  |  |  |
| B7-5-7 | 各报告"通过"谓词 | 规则/约束 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-7-bench-static | bench_report 作为 release_requires 成员的类型标识与生产者规则；不定义报告通过谓词 | 静态类型/生产者规则 | 第一批；设计审定 2026-11-11（M0a 处置） | P1 | 设计 / 开发 |  |  |  |  |
| B7-5-7-build-image-ut | 父键原文字段组：BuildReport / ImageReport / UTReport 的通过谓词 | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo release_requires；09 §3.1 v0.4 | 设计 / 开发 |  |  |  |  |
| B7-5-7-bench | BenchReport 通过谓词的运行时判定语义；bench_report 类型标识与生产者静态规则只引用 B7-5-7-bench-static | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock；09 §3.1 v0.4 | 设计 / 开发 |  |  |  |  |
| B7-5-7-other-reports | 其余报告的通过谓词（Review / CI 等；UTReport 谓词仍由 B7-5-7-build-image-ut 在第一批负责） | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 Agent 空壳 | 设计 / 开发 |  |  |  |  |
| B7-5-8 | ReleaseManifest `release_evidence` | schema/字段 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P2 | 设计 / 开发 |  |  |  |  |
| B7-5-9 | LogAnalyzer Diagnosis schema | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-9-demo-min | 父键原文字段组：Diagnosis 的 Demo 最小字段 | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo AI 分析；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-5-9-rest | Diagnosis 其余字段 | 字段子键 | 第三批；设计审定 2026-11-11（M0a 处置） | P5 Compiler Agent，contract v1.0 | 设计 / 开发 |  |  |  |  |
| B7-5-10 | `ai_draft` 子结构与 AI 证据/采纳记录 | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-10-demo-min | 父键原文字段组：ai_draft 的 Demo 最小字段与 AI 证据/采纳记录 | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo AI 修复；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-5-10-rest | ai_draft 其余字段 | 字段子键 | 第三批；设计审定 2026-11-11（M0a 处置） | P5 Compiler Agent，contract v1.0 | 设计 / 开发 |  |  |  |  |
| B7-5-11 | 多版本对比报告 schema | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-11-build-ut | 父键原文字段组：多版本对比报告构建与 UT 列 | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo 结果；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-5-11-bench-business | Benchmark 对比报告列的 schema 与业务字段（合并原 bench-core） | 字段子键 | 第三批；设计审定 2026-11-11（M0a 处置） | P7；HLD §13：P4 只含构建/UT 列 | 设计 / 开发 |  |  |  |  |
| B7-5-12 | `get_result` 的 `incomplete` / `retried` 清单与超时记录 | schema/字段 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P2 | 设计 / 开发 |  |  |  |  |
| B7-5-13 | 目标范围与 ModuleRegistry schema（含 `always_run`）、`create_run.focus_modules` | schema/字段、命令/接口 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-13-focus | 父键原文字段组：create_run.focus_modules | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo create_run；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-5-13-registry | 父键原文字段组：目标范围其余部分、ModuleRegistry schema 与 always_run | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P4；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-5-14 | Profile 新鲜度策略 v2 参数 | 配置 schema/策略参数（HLD Profile 新鲜度策略 v2） | 第三批；设计审定 2026-11-11（M0a 处置） | P7 Profile 新鲜度策略 | 设计 / 开发 |  |  |  |  |
| B7-5-15 | Quickbuild 的 snapshot manifest 扩展（Profile 快照编号、逐包 commit、显式覆盖版本）、ExpectedSourceManifest、读回字段（`actual_build_conf_digest` / `published_build_conf_digest` 分列、脚本版本、`unknown` 取值）与后端能力证据等级表 | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-5-15-schema | snapshot manifest 扩展（Profile 快照编号、逐包 commit、显式覆盖版本）、ExpectedSourceManifest、读回字段的 schema（actual / published build_conf digest 分列、脚本版本、unknown 取值） | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 FakeQuickbuild 锁定 base 测试 | 设计 / 开发 |  |  |  |  |
| B7-5-15-evidence | 后端能力证据等级表的逐项结论与 Quickbuild 实测取值 | 实测证据/能力取值 | 第三批；设计审定 2026-11-11（M0a 处置） | P6 | 设计 / 开发 |  |  |  |  |
| B7-5-16 | BenchReport `comparison` 三值（verified / unverifiable / none）与 `opt_verdict` 的 `comparison_unverifiable` 原因 | schema/字段 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock | 设计 / 开发 |  |  |  |  |
| B7-5-17 | release_requires 与优化重验证的"汇合必经"形式化（见"注册与 DSL"条） | 规则消费/转引（定义见 B7-1-3；具体适用见 B7-1-2-rules-rest） | 第一批；设计审定 2026-11-11（M0a 处置） | P1 | 设计 / 开发 |  |  |  |  |
| B7-5-18 | `incomplete` 条目 `class` 与 `ApprovalDecision.acknowledged_gaps`（每项 = (条目 id, 内容 digest)；覆盖 environment_gap、verification_asset_change 与当前 series 证据链上的 retried 记录） | schema/字段 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P2 | 设计 / 开发 |  |  |  |  |
| B7-5-19 | `get_result` 结论字段（含 `succeeded_with_gaps`） | schema/字段 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P2 | 设计 / 开发 |  |  |  |  |
| B7-5-20 | OptimizationPlan 记录与 series 段 `purpose`（initial / candidate / repair / revert，编排按互斥顺序推导） | schema/字段 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock | 设计 / 开发 |  |  |  |  |
| B7-5-21 | `E-CANDIDATE-NOT-REVERT`（响应含 plan_id 与 parent_tree）、`pending_plan_at_terminal` | 类型化错误响应/终态兜底原因（01 §3.3、§2.1 扩展） | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock | 设计 / 开发 |  |  |  |  |
| B7-5-22 | candidate 受理的预校验结果与完成事务复核（含 `candidate_recheck_failed` 与"预校验拒绝不登记 candidate"） | 候选预校验及完成事务守卫/错误码（01 §3.3 扩展） | 第二批；设计审定 2026-11-11（M0a 处置） | P4 mock | 设计 / 开发 |  |  |  |  |
| B7-5-23 | ModuleRegistry 的 `protected_paths` 与验证资产触及检查 | 规则/约束 | 第二批；设计审定 2026-11-11（M0a 处置） | P4 | 设计 / 开发 |  |  |  |  |
| B7-5-24 | 多版本对比报告 digest 入 `release_evidence`。 | ReleaseManifest 摘要域字段（01 §2.5 扩展） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P2 | 设计 / 开发 |  |  |  |  |
## B7-6 **资源**

来源 HLD 附录 B:986。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-6-1 | 板子池租约（generation、sequence 租约、reclaiming/quarantine、失败归因计数）、刷机与探测接口 | 命令/接口 | 第二批；设计审定 2026-11-11（M0a 处置） | P3 / P4 | 设计 / 开发 |  |  |  |  |
| B7-6-2 | 基线缓存键（构建输入闭包）与 single-flight | 缓存键 schema/并发协调协议（HLD 基线缓存） | 第二批；设计审定 2026-11-11（M0a 处置） | P3 / P4 | 设计 / 开发 |  |  |  |  |
| B7-6-3 | 镜像存储引用计数。 | 存储记录字段/引用计数迁移（HLD 镜像存储） | 第二批；设计审定 2026-11-11（M0a 处置） | P3 / P4 | 设计 / 开发 |  |  |  |  |
## B7-7 **入口**

来源 HLD 附录 B:987。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-7-1 | MCP 工具 ↔ 操作映射表、request_id 为工具参数、幂等域 (principal, 操作名) 跨传输共享、`submit_bench_suite`、`sys.scheduler` | 命令/接口 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-7-1-mcp | 父键原文的字段组：MCP 映射/request_id/幂等域/sys.scheduler | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P2 | 设计 / 开发 |  |  |  |  |
| B7-7-1-suite-submit | 父键原文的字段组：submit_bench_suite | 字段子键 | 第三批；设计审定 2026-11-11（M0a 处置） | P7 | 设计 / 开发 |  |  |  |  |
| B7-7-2 | 套件确认命令与权限（本机特权通道）。 | 命令/接口 | 第三批；设计审定 2026-11-11（M0a 处置） | P7 | 设计 / 开发 |  |  |  |  |
## B7-8 **部署契约**

来源 HLD 附录 B:988。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-8-1 | 无 PHP 约束（D23）——插件、受限 adapter 与宿主侧适配器的注册记录含运行时声明、制品 digest、运行环境闭包 digest、策略版本与扫描结论，加载期复核 | schema/字段 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-2 | **v2.10 追加**：ExecutionManifest 增 deploy 安装集 digest 字段（Run 创建时与最近一次通过扫描的 digest 比对，D23 / §11.2） | schema/字段 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-3 | **v2.11 追加**：DeploymentInventory 的规范化输入、当前状态的采集来源与 approved / current 比对契约，独立构建主机的同类字段 | schema/字段、迁移/守卫、规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-4 | **v2.14 追加**：最低有效策略版本与例外撤销清单的发布格式、读取方式与缓存时限 revocation_max_age | 策略发布 schema/读取接口/缓存时限配置（HLD §11.2） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-5 | 签名表按语言登记的字符串解析器与插值判定规则（含 bytes 常量的解码口径） | 规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-6 | DeploymentInventory 的产品单元清单字段与逐单元部署检查 | schema/字段、规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-7 | **v2.13 追加**：签名表的注释符与规范化规则 | 规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-8 | pyc 制品清单（源 digest、source_hash、解释器 / cache tag、编译参数、完整 pyc digest） | 制品清单 schema（HLD §11.2） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-9 | 执行准入与 exec 记账覆盖全部产品进程的部署检查项 | 规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-10 | "现行版本"绑定与 Run 创建时的例外复核 | Run 创建准入守卫（HLD §11.2；01 §2.1 扩展） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-11 | **v2.12 追加**：签名表与扫描器 digest 表随策略版本发布的格式 | 策略签名表/摘要表 schema（HLD §11.2） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-12 | 例外比对现行 HLD 版本的已批准例外清单 | 例外批准清单一致性校验规则（HLD §11.2） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-13 | launcher 的受控执行视图 / 执行准入与子孙 exec 记账、`deployment_dependency_violation` 诊断 | 命令/接口 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-14 | 无 PHP 例外清单条目（工具名、安装件 digest、PHP 组件、理由、批准人、到期日）只在负责人修订 D23 后存在 | 负责人批准的例外清单 schema（HLD D23、§11.2） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-15 | 运维对 broker 的计划性 drain / restart 须经 launcher 登记（01 §2.2d 计划性回收域），未登记者按故障归责 | 命令/接口 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-16 | 特权 launcher 的 cgroup v2 spawn / kill 接口（ClineSR CLI、构建边界与 Release broker 实例——broker 的回收与静默判定按实例 cgroup，01 §2.2d） | 命令/接口、规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
| B7-8-17 | 构建隔离边界的不可变基底 digest 与复位要求。 | 部署配置 digest 字段/构建边界复位协议（HLD §11.2） | 第一批；设计审定 2026-11-11（M0a 处置） | Demo / P1 / P2 | 设计 / 开发 |  |  |  |  |
## B7-9 **执行环境**

来源 HLD 附录 B:989。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-9-1 | ExecutionManifest 扩展字段（llm_cli_version、bench_suites_digest、spec_digest、bench_policy_digest、module_registry_digest、build_input_closure_digest、Profile 新鲜度策略版本）。 | schema/字段 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-9-1-llm | 父键原文字段组：llm_cli_version | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo LLM；09 §3.1 | 设计 / 开发 |  |  |  |  |
| B7-9-1-core | 父键原文字段组：bench_suites_digest、spec_digest、bench_policy_digest、module_registry_digest、build_input_closure_digest 的核心 schema | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P3/P4 mock；09 §3.1 其余摘要字段 | 设计 / 开发 |  |  |  |  |
| B7-9-1-freshness | 父键原文字段组：Profile 新鲜度策略版本 | 字段子键 | 第三批；设计审定 2026-11-11（M0a 处置） | P7；09 §3.1 | 设计 / 开发 |  |  |  |  |
## B7-10 **conformance**

来源 HLD 附录 B:990。

| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号） | 三方通过日期 | 实现日期 | 阶段验收日期 |
|---|---|---|---|---|---|---|---|---|---|
| B7-10-1 | §11.3 v2.0 追加类别逐类落 CF 族 | CF/验收 | 第二批；设计审定 2026-11-11（M0a 处置） | P3 / P4 | 设计 / 开发 |  |  |  |  |
| B7-10-2 | 构建隔离与 CLI OS 层约束的部署契约检查项 | 规则/约束 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo 首次使用前 | 设计 / 开发 |  |  |  |  |
| B7-10-3 | SourceProvider 接口。 | 命令/接口 | 父键（不归批，见子键）；设计审定 2026-11-11（M0a 处置） | 见子键 | 设计 / 开发 |  |  |  |  |
| B7-10-3-git-min | 父键原文的字段组：最小 Git 接口 | 字段子键 | 第一批；设计审定 2026-11-11（M0a 处置） | Demo 源码接入 | 设计 / 开发 |  |  |  |  |
| B7-10-3-rest | 父键原文的字段组：其余 SourceProvider 接口 | 字段子键 | 第二批；设计审定 2026-11-11（M0a 处置） | P3 / P4 | 设计 / 开发 |  |  |  |  |



## §11.3 测试类别消费映射（M0a 处置 M1–M3）

每行列断言实际读写的字段/命令对应的叶键；既有 01 核心不强挂 B7。T11.3 编号及拆分后缀保持可反查 HLD §11.3。P1 / P2 只能消费第一批扩展；P1–P4 不消费晚于第二批的扩展。Demo 安全切片仍须首次使用前验收。

M1：P1 静态加载所需字段、类型与规则前移第一批；BenchReport 谓词、gate_eligible 判定语义仍在第二批。第二批谓词通过前，运行期审批对 release_requires 含 BenchReport 一律 fail-closed；不再由静态校验器拒绝这类示例。P4 的套件/指标加载期最小 schema 由 B7-5-4-load 提供，统计、测量与其余业务字段仍属第三批。

### P1–P4

| 类别（HLD §11.3） | 最早阶段 gate | 判定读写的字段/命令 | 消费叶键（或既有核心） |
|---|---|---|---|
| T11.3-001 DSL property/fuzz | P1 | input、release_requires、汇合必经、净变更；budget/hitl 为 01 §1.3 核心 | B7-1-2-demo-dsl, B7-1-3, B7-1-4 |
| T11.3-002 状态机 model-based | P1 | paused 原因、wake outbox、计时守卫、created→queued；01 §2.1 核心迁移 | B7-2-2, B7-2-3, B7-2-6, B7-2-7 |
| T11.3-003 Ledger 逐持久化边界故障注入 | P1 | 初始 series 与等待/outbox 的原子提交；其余提交点为 01 CF-LED | B7-2-3, B7-2-7 |
| T11.3-004 token 并发双消费 | P2 | 01 §2.5 token_id、授权 CAS、consume；无新增 B7 字段 | 无新增 B7；见本行 01 核心字段 |
| T11.3-005 陈旧 series 进 gate/join 拒绝 | P1 | 01 §3.1–§3.3 series_id、activation、join 到达记录 | 无新增 B7；见本行 01 核心字段 |
| T11.3-006 checkpoint / manifest 不匹配拒绝恢复 | P1 | 01 §2.6 核心 execution manifest digest 与 checkpoint 绑定 | 无新增 B7；见本行 01 核心字段 |
| T11.3-007 artifact 损坏与 blob 提交崩溃 | P1 | 01 CF-BLOB：blob digest、索引、提交顺序及 GC 可达性 | 无新增 B7；见本行 01 核心字段 |
| T11.3-008-a control-plane 命令隔离 | P2 | task/run 归属与数据面命令载荷；审批/核销权限为 01 §5.1 核心 | B7-3-1 |
| T11.3-008-b 真实 UID/文件权限 E2E | P4 | launcher spawn/kill、进程身份与 socket 可达性；01 §5.1 | B7-8-16 |
| T11.3-009 旧 activation 首达后推进 series | P1 | 01 §3.1–§3.4 activation/series 与超时退役条件 | 无新增 B7；见本行 01 核心字段 |
| T11.3-010 同 series 并发 activation 成组 | P1 | 01 §3.1–§3.2 activation 身份、join 分组 | 无新增 B7；见本行 01 核心字段 |
| T11.3-011 不推进 series 的环不误杀 | P1 | 01 §3.1–§3.4 cohort、activation、计时器退役 | 无新增 B7；见本行 01 核心字段 |
| T11.3-012 父退役级联与跨 fan-out 回环拒绝 | P1 | 01 §3.1–§3.4 scope、共同到达与 validator | 无新增 B7；见本行 01 核心字段 |
| T11.3-013 跨 attempt claim 三支矩阵 | P2 | 01 §4 idem_key/version/参数摘要、EffectRecord 状态 | 无新增 B7；见本行 01 核心字段 |
| T11.3-014 publishing / pending finalize 裁决 | P2 | 01 §2.2、§5.1 终态映射、裁决证据与 broker 静默状态 | 无新增 B7；见本行 01 核心字段 |
| T11.3-015 post-close correction | P2 | 01 §5.4 CorrectionRequest/Record、get_result 修正视图 | 无新增 B7；见本行 01 核心字段 |
| T11.3-016 effect_call_id 唯一性与重试 | P2 | 01 §4.1 调用键、参数摘要、repeat_seq | 无新增 B7；见本行 01 核心字段 |
| T11.3-017 probe-only / replay_safe 效应对账 | P2 | 01 §4.3 核心 ProbeOutcome、能力标志、对账迁移 | 无新增 B7；见本行 01 核心字段 |
| T11.3-018 join 共同到达 validator | P1 | 01 §1.3、§3.2 scope、activation 与互斥 outcome | 无新增 B7；见本行 01 核心字段 |
| T11.3-019 恢复复用 dispatch | P2 | 01 §2.2 DispatchReceipt、epoch、出向协议 | 无新增 B7；见本行 01 核心字段 |
| T11.3-020 publishing 重启/D12 漂移优先对账 | P2 | 01 §2.2/§2.6 manifest digest、publishing、恢复臂 | 无新增 B7；见本行 01 核心字段 |
| T11.3-021 blob 上传与 GC 并发 | P1 | 01 CF-BLOB 的 blob 引用、索引与提交顺序 | 无新增 B7；见本行 01 核心字段 |
| T11.3-022 编排崩溃而 GBS 存活 | P3 | 构建边界 cgroup、kill、复位；本地构建 probe 核心为 01 §4 | B7-8-16, B7-8-17 |
| T11.3-024 即插即用与删除组合 | P1 | mode 注册 produces 与 release_requires、accept_unverified_release；config.mode/max_opt_rounds 与 budget 静态规则、bench_report 类型/生产者、gate 字段类型、本地最小能力；不消费运行时 BenchReport 判定语义 | B7-1-1, B7-1-2-demo-dsl, B7-1-2-bench-opt-syntax, B7-5-7-bench-static, B7-5-3-gate-fields, B7-5-2-local-min, B7-1-2-rules-rest |
| T11.3-025 四份示例原文及加载反例 | P1 | 示例字节、image_report 生产者、汇合必经与 fail_safe；config.mode/max_opt_rounds 与 budget 静态规则、bench_report 类型/生产者、gate 字段类型、本地最小能力；不消费运行时 BenchReport 判定语义 | B7-1-6, B7-1-3, B7-1-2-demo-dsl, B7-1-2-bench-opt-syntax, B7-5-7-bench-static, B7-5-3-gate-fields, B7-5-2-local-min, B7-1-2-rules-rest |
| T11.3-026-a 超时路由与状态记录 | P1 | 超时原因、预算、fail_safe 与 publishing 映射 | B7-1-5, B7-2-6, B7-2-9 |
| T11.3-026-b 超时首屏/Skill 呈现 | P2 | incomplete/retried、结论字段；FeedbackReport 核心为 01 §2.4 | B7-5-12, B7-5-19 |
| T11.3-027 release_requires 审批运行时 | P2 | 构建/镜像/UT 通过谓词、release_evidence、审批 CAS/consume | B7-5-7-build-image-ut, B7-5-8, B7-2-8 |
| T11.3-028 修复回流与 series 新鲜度 | P1 | series_effect；series 事务与循环 budget 为 01 §3.3/§1 | B7-1-1 |
| T11.3-029 rpm_precheck 加载与运行 | P1 | rpm_precheck、ImageReport；RPM 报告为核心 BuildReport；LocalGbsBackend 的 source_input/comparison 最小能力及加载期判定 | B7-1-2-demo-dsl, B7-5-1-image-schema, B7-5-2-local-min |
| T11.3-030 input:none 生命周期 | P1 | 净变更、初始空 series、submit_patch 拒绝、Skill 空 series 错误 | B7-1-4, B7-2-7, B7-2-15 |
| T11.3-031-a 外部等待/outbox/执行槽锁序 | P1 | task_suspend guard、wake、资源授予、计时与 supersede | B7-2-1, B7-2-2, B7-2-3, B7-2-5, B7-2-6 |
| T11.3-031-b 两 Run 一板一槽真实租约锁序 | P3 | 授予顺序与板租约 generation；P1 可用调度资源 Fake 验证锁序 | B7-2-5, B7-6-1 |
| T11.3-033 镜像效应半成品与提交崩溃 | P3 | 镜像 probe 索引、ImageRecord 原子入库与被测/基线身份 | B7-4-1-image-profile-probe, B7-4-2-record-rest |
| T11.3-034 特权构建隔离 E2E | P3 | 不可变基底、复位、无凭据导出、UID/socket/Ledger 隔离 | B7-8-17, B7-10-2 |
| T11.3-035 worker 数据面扩展命令归属 | P2 | resource_lease_release/image_commit/profile_put/remote_build_submit 的归属与命令注册表 | B7-3-1 |
| T11.3-036 板子池 fencing/quarantine | P3 | generation、sequence、静默、reclaiming/quarantine、归因计数 | B7-6-1 |
| T11.3-037-a 基线缓存键/引用/GC | P3 | 闭包 digest、single-flight、引用数与损坏重建 | B7-6-2, B7-6-3, B7-9-1-core |
| T11.3-037-b FakeQuickbuild 输入不符/不可读 | P4 | 锁定包版本、Profile 快照、actual 输入/unknown、comparison 与缓存准入 | B7-5-15-schema, B7-5-2-schema, B7-6-2 |
| T11.3-040-a Profile 待验区跨 Run 隔离 | P3 | Profile 归属、存取、引用与入库命令 | B7-5-6-core |
| T11.3-041-a 优化回路加载校验 | P1 | 优化回流汇合必经、UT 注册存在性；无真实性能输入；config.mode/max_opt_rounds 与 budget 静态规则、bench_report 类型/生产者、gate 字段类型、本地最小能力；不消费运行时 BenchReport 判定语义 | B7-1-3, B7-1-1, B7-1-2-bench-opt-syntax, B7-5-7-bench-static, B7-5-3-gate-fields, B7-5-2-local-min, B7-1-2-rules-rest |
| T11.3-041-b 优化环 mock 判定与撤销 | P4 | mock opt_verdict、plan 状态、purpose、父版本与候选复核；不消费 BenchPolicy 统计 schema | B7-5-5-core, B7-5-20, B7-5-22, B7-5-16, B7-1-2-mock-bench-opt |
| T11.3-042 ClineSR 提示注入与 FD/端点 | P3 | OS 边界、spawn/kill、llm_cli_version；EvidencePacket/provider 摘要用 01 §5.3/§5.5 | B7-10-2, B7-8-16, B7-9-1-llm |
| T11.3-043 MCP 幂等、Origin、principal、scheduler | P2 | request_id、(principal,操作名)、sys.scheduler 与 input:none | B7-7-1-mcp, B7-2-7 |
| T11.3-044-a Gateway 两 socket 命令与错账号桩 | P2 | session_install 命令、会话归属；P2 骨架 Fake | B7-3-2 |
| T11.3-045-a create_run focus_modules | P2 | 创建时显式目标模块参数；Demo 启动使用 | B7-5-13-focus |
| T11.3-045-b 目标范围注册/只增/always_run | P4 | ModuleRegistry、always_run、范围推导与 module_registry_digest | B7-5-13-registry, B7-9-1-core |
| T11.3-046 多版本对比构建/UT 列 | P4 | 固定测量输入的构建/UT 列、不可改写数字、release_evidence 摘要 | B7-5-11-build-ut, B7-5-24 |
| T11.3-047 FakeQuickbuild 锁定 base | P4 | Profile 快照、逐包 commit/覆盖版本、ExpectedSourceManifest 与 actual 输入比对；SourceProvider patch 应用/冲突检查 | B7-5-15-schema, B7-5-2-schema, B7-10-3-rest |
| T11.3-049 v2.3 示例规则①③反例 | P1 | 示例一/三/四、汇合必经、ut/bench_gate 路径；config.mode/max_opt_rounds 与 budget 静态规则、bench_report 类型/生产者、gate 字段类型、本地最小能力；不消费运行时 BenchReport 判定语义 | B7-1-6, B7-1-3, B7-1-2-bench-opt-syntax, B7-5-7-bench-static, B7-5-3-gate-fields, B7-5-2-local-min, B7-1-2-rules-rest |
| T11.3-050-a 净变更数据流与 submit_patch | P1 | advances/asserts_nonempty、空 series 拒绝与 fail_safe | B7-1-4, B7-2-7 |
| T11.3-050-b campaign 候选撤销与 no_gain_found | P4 | purpose、候选事务、未决计划终态守卫 | B7-5-20, B7-5-21, B7-5-22 |
| T11.3-051 超时放行、gap 确认与核销 | P2 | timeout/retried、acknowledged_gaps、gaps_changed、结论映射 | B7-1-5, B7-2-8, B7-2-9, B7-2-10, B7-5-18, B7-5-19 |
| T11.3-052 外部等待会话/ACK/挂起补充 | P1 | gateway_session phase、task_suspend guard、deferred 作为挂起输入、计时；不验证远端 probe 实现 | B7-2-1, B7-2-3, B7-2-6, B7-4-1-deferred |
| T11.3-053 远程配额恰一次归还（Fake 远端） | P2 | cancel_pending 与配额账；Fake 远端只回报终态，不断言远程效应标记 version（随 B7-4-1-remote-build 于 P6 断言） | B7-2-1, B7-3-1 |
| T11.3-054-a Quickbuild 锁定输入 mock 比较 | P4 | base_mismatch、actual 配置摘要/unknown、comparison 缺字段 | B7-5-15-schema, B7-5-2-schema, B7-4-1-image-failure |
| T11.3-056 优化计划状态与容量 | P4 | purpose、撤销、候选复核、pending_plan 与容量错误码 | B7-5-20, B7-5-21, B7-5-22, B7-2-14 |
| T11.3-057-a 目标范围增长与审批快照 | P4 | 模块登记/范围、always_run、未验证模块 gap | B7-5-13-registry, B7-5-18 |
| T11.3-058 验证资产触及确认 | P4 | protected_paths、verification_asset_change、确认 digest | B7-5-23, B7-5-18 |
| T11.3-059 对比报告摘要/terminal/fail_safe | P2 | 构建/UT 报告 digest、release_evidence、核销校验 | B7-5-11-build-ut, B7-5-24 |
| T11.3-060 构建边界持久后门与基底变更 | P3 | 不可变基底 digest、复位、产物拒收 | B7-8-17 |
| T11.3-061 CLI 及后代终止 | P3 | cgroup spawn/kill 与孤儿回收 | B7-8-16 |
| T11.3-062-a E-03 命令与镜像存储权限 | P2 | image_commit/remote_build_submit 归属与无直接写权限 | B7-3-1 |
| T11.3-062-b 无板侧 fencing 的释放 | P3 | generation、主动释放与静默后再分配 | B7-6-1 |
| T11.3-063 基线构建归属与取消广播 | P3 | single-flight 引用/等待者、取消与失败广播；不消费 BenchReport 业务 schema | B7-6-2 |
| T11.3-064-a 换板重试与镜像归因 | P3 | 板 generation、失败归因计数、换板结果 | B7-6-1 |
| T11.3-064-b Quickbuild 证据等级的 Fake 准入 | P4 | verified/unverified、ExpectedSourceManifest、实际 series、base_mismatch | B7-5-2-schema, B7-5-15-schema, B7-4-1-image-failure |
| T11.3-065 实际/发布配置不同或 unknown | P4 | actual/published build_conf digest 分列、unknown、缓存准入；使用 Fake 输入 | B7-5-15-schema, B7-5-2-schema, B7-6-2 |
| T11.3-067 优化计划出口与撤销后重验证 | P4 | comparison/opt_verdict mock 值、计划状态、BenchReport 通过谓词 | B7-5-16, B7-5-5-core, B7-5-20, B7-5-7-bench |
| T11.3-068 retried 确认范围 | P2 | 当前证据链、(条目 id,digest)、gaps_changed | B7-2-11, B7-5-18, B7-2-10 |
| T11.3-069 登录等待超时固定 fail_safe | P1 | gateway_session 超时类别与禁止重试路由 | B7-2-12, B7-2-1 |
| T11.3-070 净变更数据流 property | P1 | advances/asserts_nonempty 路径判定 | B7-1-4 |
| T11.3-071 撤销后的验证资产 | P4 | protected_paths、撤销后差异、审批确认项 | B7-5-23, B7-5-18, B7-5-20 |
| T11.3-072 报告时序与证据链原子提交 | P2 | ci_plan/Review 证据引用、完成事务、报告 digest | B7-2-11, B7-5-24 |
| T11.3-073-a 无环节点等待缺省 | P1 | external_timeout_min/run_budget 与计时条件 | B7-2-13, B7-2-6 |
| T11.3-073-b 后端能力加载期检查 | P4 | source_input/build_image 已验证、comparison 未验证：显式锁定 absolute-only 非发布 gate 通过；relative、无法解析指标依赖或 suites:auto 拒绝；加入 Optimization / 必需 Bench 发布亦拒绝。消费套件身份、选择方式与指标依赖的加载期最小 schema，不消费统计策略/测量记录 | B7-5-2-schema, B7-5-4-load |
| T11.3-074-a FakeQuickbuild 快照策略 | P4 | reference/Profile 快照编号、显式锁定包版本；读回未知不虚构落后量 | B7-5-15-schema |
| T11.3-075 证据链边界与 consume 拒绝 | P2 | ci_plan/sys.baseline_build retried、consume gaps_changed | B7-2-11, B7-2-10, B7-5-18 |
| T11.3-076 purpose 推导与 base_mismatch | P4 | 互斥 purpose、未决计划、base_mismatch；mock 业务结论 | B7-5-20, B7-5-22, B7-5-1-image-schema, B7-4-1-image-failure |
| T11.3-077-a 计划准入拒绝后的 status | P4 | E-PLAN-NO-CAPACITY、净变更与 status | B7-2-14, B7-5-21 |
| T11.3-077-b purpose 互斥判定 | P4 | 候选/撤销优先级、parent_tree、E-CANDIDATE-NOT-REVERT | B7-5-20, B7-5-21, B7-5-22 |
| T11.3-078 terminal 未决计划兜底 | P4 | pending_plan_at_terminal 与终态 guard | B7-5-21 |
| T11.3-080-b 计划迁移事务位置 | P4 | candidate 受理/task_complete 原子位置、CAS、重放计数 | B7-5-20, B7-5-22 |
| T11.3-081 拒绝后改交撤销 | P4 | 候选拒绝、revert 受理、环计数与 sys.invalid_result | B7-5-21, B7-5-22, B7-5-20 |
| T11.3-082 违规返回归因 | P4 | rejected_reverting、status/净变更、未决计划 | B7-5-21, B7-5-22, B7-5-20 |
| T11.3-084-a snapshot manifest schema | P4 | 构建根快照编号唯一位置 | B7-5-15-schema |
| T11.3-084-b 完成复核不一致 | P4 | candidate_recheck_failed、收益判定写回、容量与事务不推进 | B7-5-22, B7-2-14, B7-5-20 |
| T11.3-086 改交撤销的例外与登记 | P4 | 候选拒绝后 base_mismatch、request_id 幂等与新请求受理 | B7-5-22, B7-5-21, B7-5-1-image-schema, B7-4-1-image-failure |
| T11.3-085-signals 仓库判定信号、改名/入口/模板、合成负向夹具 | P1 | 制品类型、文本信号、非执行分类、扫描器 digest 与策略版本 | B7-8-1, B7-8-11 |
| T11.3-085-fragments Python 常量/隐式拼接/bytes/f-string/注释及未登记语言 | P1 | 解析器登记、常量值、插值拒绝、tokenizer/规范化、精确签名（v2.12–v2.14） | B7-8-5, B7-8-7, B7-8-11 |
| T11.3-085-pyc PEP552/pyc 篡改与运行时生成 | P3 | 源 digest/source_hash、解释器/cache tag、编译参数、完整 pyc digest | B7-8-8 |
| T11.3-085-image 镜像/主机依赖、业务目录排除与扫描器摘要 | P3 | 安装闭包、受检前缀、scanner digest、业务/无关预装排除边界 | B7-8-1, B7-8-11 |
| T11.3-085-inventory 安装件替换/升级/独立构建主机与 Run 准入 | P3 | ExecutionManifest deploy digest、DeploymentInventory approved/current 与实际采集来源 | B7-8-2, B7-8-3 |
| T11.3-085-exceptions 例外无批准/摘要不符/过期/现行版本删除 | P3 | 例外工具/digest/批准人/到期、现行 HLD 批准清单与 Run 复核 | B7-8-10, B7-8-12, B7-8-14 |
| T11.3-085-revocation 最低策略版本/撤销清单/缓存过期 | P3 | 最低有效版本、撤销条目、revocation_max_age | B7-8-4 |
| T11.3-085-exec 错误分支、子孙、绝对路径/符号链接执行准入 | P3 | 受控执行视图、exec 记账与 deployment_dependency_violation；观测不代替准入 | B7-8-13, B7-8-9 |
| T11.3-085-units 未登记/未配置产品单元、Web 后端与 cgroup 子树 | P3 | 产品单元清单、逐单元准入/exec 核对、未登记进程 | B7-8-6, B7-8-9 |
| T11.3-079 absolute/relative SPEC 指标 gate | P4 | source_input/build_image 已验证、comparison 未验证：显式锁定 absolute-only 非发布 gate 通过；relative、无法解析指标依赖或 suites:auto 拒绝；加入 Optimization / 必需 Bench 发布亦拒绝。消费套件身份、选择方式与指标依赖的加载期最小 schema，不消费统计策略/测量记录 | B7-5-2-schema, B7-5-4-load |
| T11.3-083 auto 套件与 absolute 指标 | P4 | source_input/build_image 已验证、comparison 未验证：显式锁定 absolute-only 非发布 gate 通过；relative、无法解析指标依赖或 suites:auto 拒绝；加入 Optimization / 必需 Bench 发布亦拒绝。消费套件身份、选择方式与指标依赖的加载期最小 schema，不消费统计策略/测量记录 | B7-5-2-schema, B7-5-4-load |

### P5 及以后：不计入 P1–P4

| 类别（HLD §11.3） | 最早阶段 gate | 判定读写的字段/命令 | 消费叶键（或既有核心） |
|---|---|---|---|
| T11.3-023 六类 agent_type producer/consumer 兼容矩阵 | P5 | 按 mode 的注册 CF-FIX 集；真实六类 fixture 为 HLD §13 P5 交付 | B7-1-1 |
| T11.3-032 远程构建效应与 ACK/probe | P6 | idem 指纹/version、deferred/indeterminate、取消后迟到结果 | B7-4-1-remote-build |
| T11.3-038 BenchPolicy golden 数据集 | P7 | SPEC、MeasurementRecord、统计区间、Holm、gateable 复算 | B7-5-4-business, B7-5-3-measurement, B7-5-3-decision-core, B7-5-7-bench |
| T11.3-039 生成套件有效性与确认 | P7 | SuiteVersion、submit_bench_suite、特权确认与工具清单 | B7-5-4-business, B7-7-1-suite-submit, B7-7-2 |
| T11.3-040-b Profile 兼容与 AutoFDO 拒用 | P7 | 源/构建选项/套件版本/采样能力/格式/编译器兼容字段 | B7-5-6-compat |
| T11.3-044-b Gateway 真实会话恢复/取消/日志脱敏 | P6 | 真实会话注入、远程 probe deferred、取消与远端日志 | B7-3-2, B7-4-1-remote-build |
| T11.3-048 Profile 新鲜度策略 v2 | P7 | 覆盖率阈值、前 K 热点、部分匹配与 OptimizationReport 业务面 | B7-5-14, B7-5-6-compat |
| T11.3-054-b Quickbuild patch 应用与 BUILD_NOTES | P6 | 实测输入应用能力、远端标记与构建号归因 | B7-5-15-evidence, B7-4-1-remote-build |
| T11.3-055 BenchPolicy v2.3 判定 | P7 | SPEC/MeasurementRecord、方向、区间、空集、统计业务规则 | B7-5-4-business, B7-5-3-measurement, B7-5-3-decision-core |
| T11.3-057-b 显式套件少于最低集合 | P7 | SuiteVersion 集合与 gate_eligible | B7-5-4-business, B7-5-3-decision-core |
| T11.3-066 有界 probe 与父子 trigger | P6 | 最大构建号、扫描界、indeterminate、父子远程作业取消 | B7-4-1-remote-build |
| T11.3-074-b Quickbuild 构建号扫描与配置证据 | P6 | 配置过滤、缺号/权限、样本能力证据结论 | B7-4-1-remote-build, B7-5-15-evidence |
| T11.3-080-a 推广状态显示 | P6 | latest/reference 推广实证、Profile/构建根实测编号 | B7-5-15-evidence |

## Demo 六步消费自查（09 §4.1）

| Demo 步骤 | 消费扩展叶键 | 使用边界 |
|---|---|---|
| 1 启动与范围 | B7-7-1-mcp, B7-5-13-focus, B7-10-3-git-min, B7-1-1, B7-1-2-demo-dsl | MCP/request_id、focus_modules、Git 输入、mode 注册与流水线子集 |
| 2 本地构建/可选 mic | B7-4-1-image-demo, B7-4-2-demo-record, B7-5-1-image-schema, B7-8-16, B7-8-17, B7-10-2, B7-5-2-local-min, B7-3-1, B7-2-5 | 本地 gbs 实际输入、mic 最小入库、隔离与 launcher；无 Quickbuild；本地最小能力、入库数据面命令与分派前资源授予 |
| 3 Compiler AI 修复 | B7-5-9-demo-min, B7-5-10-demo-min, B7-9-1-llm, B7-1-1, B7-10-2 | Diagnosis/ai_draft 最小字段、llm_cli_version、series_effect 与 CLI 数据边界 |
| 4 后续空壳 Agent | B7-1-1, B7-1-6, B7-1-2-bench-opt-syntax | mode 注册、示例加载与 01 §2.3/§2.4 既有合规报告；新增消费 config.mode 取值/缺省与 max_opt_rounds/budget 的静态规则。Demo release_requires 不含 BenchReport（09 v0.5 §3.1） |
| 5 审批/模拟发布/反馈 | B7-5-7-build-image-ut, B7-5-8, B7-5-11-build-ut, B7-5-12, B7-5-18, B7-5-19, B7-5-24, B7-2-8, B7-2-10, B7-2-11 | 构建/UT 对比、证据链、gap/retried 确认、release_evidence 与 consume；核心 token/模拟发布用 01 §2.2/§2.5 |
| 6 编排重启可靠性 | B7-2-3, B7-2-7, B7-8-16 | outbox/初始事务与子进程回收；持久化、dispatch、consume 幂等用 01 §2/§4 核心 |

共同部署前提（09 §4.2）：B7-8-1, B7-8-2, B7-8-3, B7-8-4, B7-8-5, B7-8-6, B7-8-7, B7-8-8, B7-8-9, B7-8-10, B7-8-11, B7-8-12, B7-8-13, B7-8-14, B7-8-15；均第一批。例外清单 schema 不表示已批准 PHP 例外。Demo 不包含真实板子、性能、优化、Quickbuild 或 VD；本次逐键自查实际消费批次，结果见 REPORT.md。

## 定义与消费边界（M2 自查依据）

- ImageRecord 字段仅由 B7-4-2-demo-record / record-rest 定义；B7-4-1-image-demo / image-profile-probe 只定义操作和 probe 行为，引用字段，不重复定义。
- config.mode / max_opt_rounds 的语法、取值、缺省与 budget 静态规则由 bench-opt-syntax 定义；mock-bench-opt 只定义运行时语义。demo-dsl 不再兜底“三条规则的 Demo 面”：净变更定义在 B7-1-4，共同汇合定义在 B7-1-3，规则③与规则①对 bench_report 的适用及 V-13b/V-15 在 rules-rest。B7-5-17 仅转引这些定义。
- bench-static 定义类型标识与生产者规则，bench 定义报告通过谓词。gate-fields 定义静态字段名/类型；decision-core 定义 mode、gate_eligible、validation_complete、opt_verdict 的判定语义；measurement 定义逐指标四值与区间、spec_inconclusive_count、opt_gain_pct、baseline_revoked、baseline_unavailable；BenchReport.comparison 三值及 opt_verdict 的 comparison_unverifiable 原因仅由 B7-5-16 定义；后端能力声明中同名 comparison 是另一个模型的能力等级项，不是重复定义报告字段。
- local-min 定义 source_input/comparison 的最小 schema、枚举及 local 后端加载期判定；schema 子键只扩展其余能力项与 Quickbuild 声明并引用最小 schema。套件/指标加载身份与依赖只由 load 定义，business 只定义统计、测量及其余业务字段。
- deferred 的共享枚举/挂起语义仅由 B7-4-1-deferred 定义，远程 probe 只消费；镜像两项失败分类仅由 image-failure 定义，ImageReport/状态机消费该分类。父键保留 HLD 原文作索引，不承担第二份字段定义。

负责人按角色填写；01 落点列全部暂空，第一批起草时回填，不以当前类型分类代替契约落地。
