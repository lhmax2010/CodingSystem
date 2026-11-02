# HLD v2.0 首轮三方评审处置表（→ v2.1；负责人裁决后 → v2.2）

裁决输入：Kimi **GO**（0 BLOCKER / 0 MAJOR / 4 MINOR / 2 NIT）；Claude Code **NO-GO**（2 BLOCKER / 10 MAJOR / 7 MINOR / 1 NIT）；Codex **NO-GO**（0 BLOCKER / 11 MAJOR / 1 MINOR）。合计 38 条意见，归并为 22 个独立问题，**全部采纳**（其中 5 处对评审方候选方案作了取舍或改写，理由逐条写明）。另有同步项（v2.0 核心修订 ↔ 01 现有条文）13 条，归入 HLD 附录 B 第 7 组，随 01 同步扩展处理；其中 D20 一项在 HLD 侧直接定案。

**程序性更正**：v2.0 头部"冻结核心原样保留、未作任何放宽"的表述不准确——外部等待（D11）与 worker 数据面扩充实质改动了冻结语义且未走勘误通道。v2.1 将二者改登记为**勘误 E-02 / E-03**（§17），随本 HLD 三方评审一致 GO 生效。

## BLOCKER

| # | 问题 | 来源 | 处置与采用方案 | 理由 |
|---|------|------|---------------|------|
| K1 | mic / GBS sudo 以 root 执行来自 patch 的 scriptlet 与 ks %post，与 broker 凭据、Gateway 会话同机，OS 用户隔离对 root 无效 | CC H2-01 | **采用 CC 方案并补一项**：新增 D22 特权构建隔离——root 步骤一律在独立内核边界内执行（同机一次性构建 VM，边界内无凭据、无 Ledger、无 control-plane socket，产物只读导出并复验入库）；**补充**：E0 无 KVM 时改用独立构建主机（同一契约），仍不允许宿主 root 直跑。N7、§2.3、§7.6.1、§8.1、§10、§12、§13 P3 gate、R23 同步 | CC 的 VM 方案正确；但内网主机是否具备 KVM 尚未确认，给出同等安全性质的替代形态，避免 E0 不满足时无路可走 |
| K2 | D11"长等待不占执行槽"无机制、改冻结状态机与计时、未走勘误；§4.5 自相矛盾；锁序未定 | CC H2-02（BLOCKER）、Codex H-04（MAJOR）、Kimi H-05（NIT，§4.2.4 括注）；Kimi 正文核验认为闭合 | **合并采用**：机制取 CC——任何 worker 不跨越等待存活；资源在分派前授予（未授予不 spawn）；远程构建提交后以 `sys.await_external` 挂起本 attempt（不路由、不计 retry），wake outbox 续接**同一 dispatch**（效应键稳定、不重复提交）；锁序先租约后执行槽；改登记勘误 E-02（新 §4.3.4）。**计时取 Codex 的全集条件**：仅当全部未决等待均为不计费等待（gate、会话失效期）时扣除，存在任一计费等待即计入。另取 Codex：paused 期预算可到期（取消远端、释放租约后 fail_safe）。取消传导取 CC H2-06。状态图改为 paused(wait)，§4.2.4/§4.4/§4.5/§5.1.2 同步 | CC 的"按等待类别扣除"无法处理同一 Run 同时存在多种等待的区间（Codex 反例），Codex 的全集条件对任意组合都有唯一答案；Kimi 的"interrupt/resume + probe"读法依赖 worker 中途退出的映射，冻结 task 模型中不存在，故不采 |

## MAJOR

| # | 问题 | 来源 | 处置与采用方案 | 理由 |
|---|------|------|---------------|------|
| K3 | 示例一 `full_pipeline` 的 review_static → join 路径绕开 ut/benchmark，按文中支配定义过不了 release_requires 检查；produces 按 agent_type 注册无法区分 rpm/image 两模式 | Codex H-01、CC H2-03 | **路径问题采用 Codex**：示例一改为单链（静态审查移至阈值判定后），删除 join；**不采用 CC 的 AND-join 支配定义**。**按 mode 注册采用 CC**：status_set / produces / series_effect / input_requirement 等均按 (agent_type, mode) 声明 | AND-join 支配会改变 E-01/V-13b 共用的判定图，需另行证明 join 超时、环回流与 series 转移下的 AND 必经性；串行化只放弃静态审查与 UT 并行的时间收益，不改任何既有语义。CC 指出的"compile_rpm 被当作 image_report 生产者"是独立缺陷，按 mode 注册直接消除 |
| K4 | RPM 内部修复后成功 BuildReport 只能标旧 series，release_requires 无法满足；多轮修复与"每 task 至多一个 candidate"冲突 | Codex H-02 | **采用 Codex 并推广为通则**（D15）：任何产修复 patch 的 task 提交唯一 candidate 即以 `*_fix_patch_ready` 结束，由声明环重派；新增 rpm_fix_loop；task 内允许私有 worktree 试构建（不提交、不计轮）以保留 LogAnalyzer 筛选方案的能力 | Codex 只覆盖 RPM 模式，同一问题在镜像、UT、Optimization 上同样存在，统一为一条规则更不易遗漏 |
| K5 | 优化专项 `entry: compile_image` 无 RPM 结果，与"镜像构建前强制检查 RPM 阶段结果"矛盾 | Codex H-03 | **采用 Codex**：镜像节点 `rpm_precheck: required\|independent`（缺省 required；required 时 RPM 节点须支配镜像节点）；示例二设 independent | — |
| K6 | 远程构建 probe 按 run/task 归因粒度不足；镜像 probe 按基线缓存键会串用；镜像半成品可被命中 | Codex H-05、CC H2-07 | **合并采用**：远程构建写入效应标记（idem_key 指纹 + version），发送前持久化 intent、查询不可见返回 indeterminate、确认未发生且旧执行静默后才允许新版本提交（Codex）；镜像存储纳入 §7.5 Blob 提交协议，镜像 probe 按 idem_key 查 Ledger 索引并复验 digest/snapshot/tree/构建输入闭包（CC + Codex） | 两家方案互补：Codex 补的是远端提交的不确定窗口，CC 补的是本地镜像的落盘协议 |
| K7 | Benchmark 统计规则只有名词，不可执行；快速/单项报告可冒充全量；判定依据未固化；测量记录未定义 | Codex H-06、CC H2-09 | **合并采用**：BenchPolicy 随套件版本固化，**缺省值取 CC 的具体参数**（每臂有效样本 ≥10、中位数、95% BCa bootstrap、Mann–Whitney U、α=0.05、Holm 校正），套件可用同构参数覆盖以对齐 TPMS；逐指标四值 pass/fail/inconclusive/not_measured 与覆盖记录取 Codex；SPEC 三值、`gate_eligible`、manifest 固化、MeasurementRecord 取 CC。**模式效力取 CC**（只有 full 且覆盖完整才 gate_eligible），不采用 Codex"快速/单项覆盖声明范围时可作发布证据" | Codex 只要求有 schema，没有给出数值，实现者仍无法照做；CC 的缺省值可直接实现、也可覆盖。快速/单项作为发布证据需要再定义"声明的发布范围"，等价于另建一个更小的套件版本——直接用小套件走 full 模式更简单 |
| K8 | "判定与 AI 分离"未结构性落实：板子稳定性列为 AI 职责；生成套件的人工确认通道未定义；判定字段无可复算约束；试点无落点 | CC H2-11（板子稳定性一点 Codex H-06 亦提出） | **采用 CC 并补首期登记**：静止判定改为确定性规则（不调用 AI）；判定字段由框架统计库确定性计算、conformance 复算比对，AI 输出只进 `ai_draft`；套件确认走本机特权通道（MCP 不提供）；新增原则 6 试点登记。**补充**：首期把产 patch 的能力（编译修复、UT 修复、优化候选）登记为 adopted，纯分析类登记为 pilot | CC 指出若修复能力登记为 pilot 首期就不能自动修复，需要定案；产 patch 的能力其产物还要过构建、UT、Benchmark 与人工审批，风险由后续确定性检查兜住，可直接 adopted。此项写明待与总部对齐时确认 |
| K9 | 优化重验证可经配置绕过（删 UT 等）；收益无确定性判定者（只比较 vs snapshot）；无撤销路径；环预算触顶会杀掉已通过的业务 patch | Codex H-07、CC H2-10 | **合并采用**：校验器路径强制与 release_requires 不可省略、禁止回拨 current 指针取 Codex（新 §4.2.6 规则③）；"优化前 vs 优化后"第二组 A/B、`opt_verdict`、非收益必须撤销 patch、`max_opt_rounds` 自限且环预算 ≥ 2×、UT 失败于优化段时确定性撤销取 CC | 两家各补一半：Codex 堵配置绕过，CC 补收益判定与退出路径 |
| K10 | Profile"代码版本变化超过阈值"无度量与阈值；同版本不同构建选项会误命中；自引用陈旧；未批准 patch 的 profile 进共享库；首期范围未定 | Codex H-08、CC H2-15 | **新鲜度取 Codex**：首期以方法插件声明的兼容字段完全匹配判定，不启用漂移阈值。**不采用 CC 的函数级 CFG checksum 匹配率**。其余取 CC：profile 数据文件路径排除于源码 tree 摘要；待验区 / 正式区；密级 internal_code；首期 AutoFDO 只覆盖 clang 构建的包、BOLT 只覆盖可加 `--emit-relocs` 的可执行文件 | CFG checksum 匹配率需要新的确定性算法、阈值与验收向量，首期没有真实数据支撑阈值；完全匹配保守但可测，以后再按 Codex 写明的条件引入距离算法 |
| K11 | 板子租约回收无 fencing，残留任务与下一任务并发；板上状态不复位；失败归因、配额、序列租约缺失 | Codex H-09、CC H2-05 | **合并采用**：租约 generation、旧 generation 命令拒绝、reclaiming（静默确认 + 复位 + 健康检查）→ available、无法静默 quarantine、Ledger 持久化与重启对账（两家共同）；失败按镜像/板子归因计数、单 Run 持板上限、最低能力匹配防饥饿、序列租约（CC） | — |
| K12 | 基线缓存键缺工具链与依赖仓等构建环境，A/B 不再只比较 patch；共享内容 GC 与写入权未定；基线测量"缓存但每次重测"自相矛盾；Quickbuild 能否 pin snapshot 被藏在待补充里 | Codex H-10、CC H2-08、Kimi H-03 | **合并采用**：缓存键改为构建输入闭包、A/B 两侧闭包必须一致、引用计数 GC、镜像入库协议（Codex）；single-flight、TTL/手动/撤销失效、`baseline_unavailable`、仅 `sys.baseline_build` 可写（CC）；基线测量只归档不参与判定（Kimi 的第一种写法）。**CC 的 Quickbuild 约束部分采用**：无法完整 pin 时基线不得跨 Run 复用、必须同批构建并标注 `unpinned_remote`，**但不据此判定 image_report 不满足发布** | 发布对象是 patch（推到 gerrit），镜像只是验证证据；同批构建保证 A/B 仍然只差 patch，审批人可见标注即可。若据此阻断发布，Quickbuild 在发布路径上就失去作用，这应由总部对齐决定而不是在 HLD 里默认关闭——已在 E0 预检中列为可行性项 |
| K13 | input: none 只检查 entry，后续 needs-patch 节点仍可拿到空 series；初始空 series 签发与 submit_patch 拒绝未定义；空发布计划走审批与 broker | Codex H-11、CC H2-14、Kimi H-02 | **采用路径级规则 + 自拟语义**：每条 status 按 mode 注册 `series_effect ∈ {advances, asserts_nonempty, none}`，needs-patch 节点从 entry 起的每条路径都须经过 advances 或 asserts_nonempty 边，运行时强制（advances 未提交 candidate、或 asserts_nonempty 而无净变更 → `sys.invalid_result`）。初始空 series 同事务签发、pin 失败不排队、submit_patch 拒绝取 Codex；取消空发布计划、sys.scheduler 取 CC；示例二新增 `no_gain_found` 与 report_no_gain 终局节点 | Codex 的"全部可达节点都必须可处理空 series"会拒绝优化专项示例本身（compile_rpm、ci_plan 必然可达）；CC 的 `advances_series` 单值也无法让"有净变更"之后的 ci_plan 合法。增加 asserts_nonempty 并由运行时强制，静态检查即可成立 |
| K14 | 新能力句柄的写操作不在冻结的 worker 数据面枚举内，权威状态位置未定（违反 D6）；跨 Run 共享存储对 worker 可写可投毒 | CC H2-04 | **采用 CC 并精简**：改登记勘误 E-03，追加 6 条数据面命令（`task_suspend`、`resource_lease_release`、`image_commit`、`profile_put`、`remote_build_submit`、`remote_build_fetch_logs`）；跨 Run 共享存储对业务 worker 只读，权威状态在 Ledger。**不采用** CC 的 `resource_lease_renew` 与 worker 侧 `remote_build_query` | 租约已改为分派前授予并随 task 存续，不需要 worker 续租；远端状态由编排侧 poller 查询（E-02），worker 不需要查询命令——命令越少，半可信进程的攻击面越小 |
| K15 | Build Gateway：会话注入入口缺失且与"只接受编排 UID"冲突；会话失效时 probe 会把 Run 判死；远端取消未传导；Gateway 崩溃恢复与日志脱敏未定 | CC H2-06 | **采用 CC**：运维会话 socket + 登录助手经 SSH 端口转发注入 + 会话主体校验；会话失效期 probe 返回 deferred（不耗重试、不进 unknown）；取消传导；以效应标记做 Gateway 幂等；日志脱敏 | — |
| K16 | ClineSR CLI 的"关闭工具执行"只靠 CLI 参数，缺 OS 级兜底；端点由 CLI 自身配置决定；CLI 版本未进 manifest；LogAnalyzer 可能自带 LLM 路径；token 估算未取上界 | CC H2-12 | **采用 CC**：专用 OS 用户、close_fds、只读提示目录、出口仅 LLM 端点、调用后文件变更校验；框架生成临时配置；`llm_cli_version` 进 D12；LogAnalyzer 经框架 LLM client；记账取上界。E0 预检新增可行性项，不满足则首期 LLM 能力不上线 | — |
| K17 | release_requires 语义不完整：§8.2 CAS 未列入；规则硬编码 human_review；只看存在不看结论；允许空清单；审批人看不到未执行的验证；§2.4 删除表漏调整 | Kimi H-01、Kimi H-04、Codex H-12、CC H2-13 | **采用**：§8.2 CAS 纳入（Kimi）；规则面向 release-approval 型 hitl（Kimi）；§2.4 各行补 release_requires 调整与"不自动删减"通则（Codex/CC）；空清单须 `accept_unverified_release`、`release_evidence` 入 ReleaseManifest 并在 CLI 首屏呈现、attestation 绑定 report_type（CC）。**CC 的"结论由路由保证、校验器检查非通过 status 不可达审批"改为运行时检查**：审批 CAS 核对每份必需报告的"通过"谓词 | 路由法需要给所有 status 再标注通过/不通过并做可达性分析，且仍要信任路由覆盖完整；在审批事务里直接检查报告结论更简单、不可绕过 |
| K18 | MCP：request_id 位置与幂等域、Origin 校验、开发者工具、调用方主体 | CC H2-16 | **采用 CC** | — |
| K19 | 附录 B 第 7 组未覆盖全部新增 [01] 项 | CC H2-17 | **采用 CC**，并按主题分组重写第 7 组（含 E-02/E-03、按 mode 注册、各报告"通过"谓词等本轮新增项） | — |
| K20 | 分期：contract v1.0 在 Benchmark/Optimization 被真实消费前定稿，违反 D10；GitGerritSource 未分期；隔离与会话注入无 gate | CC H2-18 | **采用 CC**：P5 定稿核心 + Compiler/UT/Review/CI 面，Benchmark/Optimization/Profile/套件 schema 标 provisional，P7 发 v1.1；GitGerritSource 入 P3；特权构建隔离 E2E 入 P3 gate；会话注入入 P6 gate | — |
| K21 | D13 未列 Benchmark 开发者脚本、生成脚本、解析规则等新的可执行内容来源 | CC H2-19 | **采用 CC**：脚本只在板上执行，宿主侧解析规则限声明式，套件以 digest pin | — |

## MINOR / NIT

| # | 问题 | 来源 | 处置 |
|---|------|------|------|
| K22 | 编号与排序（G10/G11、R21/R22、A16/A17、附录 A15 位置） | CC H2-20、Kimi H-06 | G、R 重排；A17 并入 A16 为 A16.1；新增 A18。**附录 A15 保持在 §17**——01 与历轮处置表均以"HLD 附录 A15（§17）"引用勘误记录，移动会使外部引用失效 |

## 同步项（不计入 HLD 缺陷，归入附录 B 第 7 组）

Codex S-01；CC S-01 至 S-08；Kimi S-01、S-02。其中：
- **S-07（D20 的 VCS 中立性）**：按 CC 建议在 HLD 侧定案——D20 写明 tree_digest 与发布 fencing 当前为 git 形态，P8 接入 Perforce 时以勘误通道做 VCS 中立化，首期不预先抽象（R21 同步）。
- 其余（paused 成因与计时、worker 数据面命令、AND-join 不引入后的 V-13b/V-15 说明、ExecutionManifest 扩展字段、新效应类别、MCP 映射、上游切换与 A2）全部写入附录 B 第 7 组对应条目，待本 HLD 三方 GO 后随 01 同步扩展一次性落定。

## 项目负责人裁决（v2.1 → v2.2）

v2.1 中有四处未按评审方方案修改、两处需与总部对齐，经负责人裁决后在 v2.2 中调整如下：

| 事项 | v2.1 做法 | 负责人裁决 | v2.2 落地 |
|------|----------|-----------|----------|
| 全流程示例的并行 | 改为单链（取 Codex），放弃静态审查与 UT 并行 | 超时必须产出报告、绝不当作通过继续；在此前提下保留并行 | 恢复 join 并行；release_requires 改用**仅本规则适用**的"汇合必经"定义（实质采纳 CC H2-03 的 AND-join 思路，但不改动 E-01/V-13b 与阈值来源检查所用的普通支配定义，回应 Codex 对"默默改支配含义"的担心）；成立依据为 join 只在完整到达时触发、超时只能 fail_safe、环回流整体退役旧 cohort、运行时审批 CAS 复核；新增 §4.3.5 超时与未完成显式化 |
| Quickbuild 无法锁定快照 | 同批构建 + unpinned_remote 标注、不阻断发布 | Quickbuild 可指定 Base CL，不指定则默认拉最新；审批人只关注改动，未改部分默认为指定基线或最新基线 | 在 snapshot pin 时把"最新"解析为具体 CL/commit 并记录，本 Run 全部提交携带同一 base，基线可跨 Run 复用；个别输入无法指定时以 unpinned_inputs 兜底；提交细节交 Codex 探测（复用已有 Quickbuild 分析成果） |
| Profile 新鲜度 | 首期兼容字段完全匹配（取 Codex） | 同意；小改动（加日志、改一处符号）不应重新采集，需预先给出放宽方案 | 新增新鲜度策略 v2：函数级校验和 + 编译器陈旧 profile 匹配 + 加权覆盖率 ≥95% 且前 20 热点函数无未恢复变化；缺省关闭，P7 验证后开启；最坏只浪费一轮验证 |
| 无 patch 流水线的校验 | 自拟 series_effect 路径规则 | 无 patch 时也要给出本次优化的目标模块；有 patch 也要确定关注模块，不能把无关模块的 UT/Benchmark 都跑一遍，优化也要看关注模块而非只看改动代码 | series_effect 规则保留；新增 §7A.7 目标范围与模块登记表：改动涉及模块（不可缩小）∪ 开发者关注模块，input: none 必填；UT/Benchmark/Optimization 只围绕范围，always_run 冒烟集兜底；R25 |
| AI 能力首期分级（总部对齐项） | pilot / adopted 登记表 | AI 的方案每轮都要过 UT 与 Benchmark，保留每轮详细结果，审批前出"基线 / 开发者改动后 / AI 优化后"的对比报告——方案可以造假，测试结果不能，审批人立即可判断 | 取消登记表与其 manifest 字段；原则 6 改为"以测试结果检验 AI"：每轮报告全部保留，框架统计库在审批前生成多版本对比报告（审批 CLI 首屏、release_evidence）；分析类输出为 AI 初稿，按采纳记录统计准确率 |
| Quickbuild 能否锁定（总部对齐项） | E0 可行性预检 | 可加 Base CL，也可不加默认最新；由 Codex 探测细节，参考其他 Session 已有的 Quickbuild / Cosmos 分析 | E0 第 ③ 项改为核对显式指定 base 与读回实际使用版本的方式 |

## 是否再起一轮

建议**再起一轮，范围不收窄**（v2.2 一并评审）：本轮有 2 个 BLOCKER、19 个 MAJOR 级问题，新增大段规范文本（E-02 §4.3.4、E-03、§4.2.6 三条规则、BenchPolicy、优化判定、板子池、基线缓存、Gateway），这些都是首次接受评审，且 E-02/E-03 的生效以三方一致 GO 为前提。
