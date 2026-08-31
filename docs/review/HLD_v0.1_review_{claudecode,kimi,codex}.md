评审完成。所有涉及 LangGraph 的断言已按评审纪律核实（依据见文末 Sources）。以下为独立评审结论。

CodingSystem Framework HLD v0.1 评审报告（评审员：Claude）
1. 总裁决：NO-GO（2 项 BLOCKER，均可低成本修复后复审）
文档整体质量高：分层清晰、决策留痕充分、spike 教训固化到位、Non-goals 裁剪合理。NO-GO 仅因两处按文档自身标准（"关键路径决策已定、无歧义"）不达标的缺口：一是 D8 安全链依赖的组件（Review UI / token 服务）无交付归属；二是旗舰示例 pipeline 依赖的并行/汇合语义在 DSL 中未定义。两者均在关键路径上且属架构层决策，不宜推给 01 隐式解决。

2. Issue 清单
编号	等级	定位	问题描述	修改建议
I-01	BLOCKER	§2.3/§8/§10/§13	approval token 的签发方 "Review UI" 与校验方 "token 服务" 被反复引用（§3、§4.4、§8），却不在 §10 仓库结构、§13 任何 Phase、§2.3 交付边界中。D8 三层强制链的第三层（运行时校验作废）与 P4 "全量 pipeline 端到端" gate 均依赖该组件，当前无人交付、无设计位置。Codex 做到 P1 的 hitl gate 时即会阻塞	在 §10 增加 framework/approval/（token 签发/校验/作废服务 + 最小 Review CLI/页面）并纳入 §13 相应 Phase；明确 Review UI 的 MVP 形态（可为 CLI）属框架交付
I-02	BLOCKER	§4.2/§4.4	并行分支语义未定义：① to: [ut, review_ai.static] 的 review_ai.static/review_ai.final 子节点寻址语法在 nodes 段与 DSL 说明中均无定义，from: review_ai 与两个子节点实例的匹配关系不明；② fan-out 后无 join/汇合语义。反例：review_ai.static 先发 review_report_ready → human_review 提前触发并签发 token，此时 ut 分支仍在回流 compiler 修改 patch series——虽然 series hash 变化会使 token 失效，但 Run 将进入"审过即作废、需重审"的未定义状态	在 §4.2 定案：并行节点实例的声明语法（如 nodes 中显式声明两个 review 节点）、join 节点/等待语义（human_review 须等待哪些上游）、分支一方进 fail_safe 时另一方的取消语义
I-03	MAJOR	§4.2 vs §6.3	内部矛盾：§4.2 校验器规则"输入依赖若不存在须被 contract 标记 optional"与 §6.3 "所有 Report 下游消费字段一律 optional"冲突——若一律 optional，该检查恒真、静态防护失效。例如 Benchmark-only 子集缺构建产物无法被静态拦截，只能运行时失败	§6.3 改为"默认 optional，允许 Agent contract 声明少数 hard-required 依赖（如 benchmark 依赖 BuildReport 的产物引用）"，使 §4.2 检查有效
I-04	MAJOR	§4.2/§4.5	循环上限归属不明：loop_limits 挂在节点上，§4.5 语义却挂在"环"上。ut→compiler 环由 compiler 的 max_patch_attempts 还是 ut 的 max_fix_rounds 管？max_patch_attempts/max_rebuilds 看似 Agent 内部限制，与编排层环计数混在同一配置块，执行者（编排层 vs SDK）不明；多环共享节点时计数归属未定义	语法上区分两类：Agent 内部限制留在节点，环级限制显式声明在环/回流边上（如 routes 条目携带 loop_limit），并写明由编排层强制
I-05	MAJOR	§4.2	路由完备性未校验："路由无悬空"只查目标存在，不查源侧覆盖。节点产出路由表未列出的 status（HandoffResult status 为 per-agent 枚举）时行为未定义	校验器增加规则：每个节点的 status 枚举须全覆盖，或强制 default 路由（建议默认导向 fail_safe）
I-06	MAJOR	§4.3/§5.1	框架级异常路由未定义：Agent execute 抛异常、进程崩溃、超 max_wall_clock_min 均不产生 HandoffResult，路由表无从匹配。重试几次？直接 fail_safe？这是 P1 编排层的关键路径决策	在 §4.3 定案框架级错误策略（如：可重试异常 N 次后转 fail_safe；wall clock 超限由编排层终止并转 fail_safe）
I-07	MAJOR	§8/§4.3/§5.2	token 作废与恢复的交互死角："dispatch 前校验并作废"后若 CI task 中断（发布中途崩溃），恢复重入 dispatch 时 token 已废→Run 死锁；且发布这类不可逆外部效应在"效应完成"与"side_effect 记录落盘"之间存在崩溃窗口→重复发布。P1 gate"中断恢复无重复副作用"对此类操作仅靠 SDK 记录不可达成	定义 token 生命周期：作废记录与 task_id 绑定，恢复时"已核销给本 task"视为有效；CI contract 明确要求发布操作实现远端幂等（push 前查远端状态），并在 §5.2 写明 side_effect 的保证等级是 at-least-once + 效应侧幂等，非 exactly-once
I-08	MAJOR	§7.1 (D7)	数据边界依赖调用方诚实标注：SDK "标注 payload 数据类别"若由 Agent 侧声明，业务 Agent 误标（bug 或绕过）internal_code 为 public 即泄漏至外部 API provider，"强制校验"只比对声明与 provider 白名单，不校验声明与内容一致。泄漏场景：二次开发者复制源码摘录进自拼 prompt 直接调 complete()	类别标签由数据来源自动携带（snapshot 读取器/BuildExecutor/KnowledgeProvider 产出的数据出生即带类别），EvidencePacket/消息聚合取最高密级，禁止调用方降级；此规则进 contract 与 conformance
I-09	MAJOR	§8/§4.2	"CI 类节点"判定机制未定义，凭据与 token 要求未闭环：校验器如何认定一个节点是 CI 类（按 agent_type 字面量？）。若配置将发布凭据授予一个 agent_type 为 publisher 的业务节点，三层链整体绕过——静态检查不认识它、contract 无 token 字段、运行时不校验	定案闭环规则："被配置注入发布凭据的节点自动视为 CI 类"，校验器据凭据授权配置（而非 agent_type 字面量）强制 requires: [approval_token]；同时建议静态要求每条到 CI 类节点的路径必经 hitl gate，且 token 服务仅对停在该 gate 的 Run 签发
I-10	MAJOR	§4.3/§6.1	create_run(pipeline_id) 无工作目标参数：snapshot 拉什么（哪些仓/包/manifest）无处指定，Codex 无法实现 snapshot 生成逻辑。§2.3 说"Run 创建时 snapshot 拉取"但范围来源未定义	在 Skill 协议签名中补目标参数（如 create_run(pipeline_id, target_spec)），target_spec 语义进 01
I-11	MAJOR	§10/§4.2/§7.5	并发模型未声明：单 Run 内已有并行分支（ut ∥ review_ai.static），是否允许多 Run 并发？Agent 以独立进程最小权限运行（§8）+ SQLite 索引 + 单台 build server 的组合下，锁策略与资源排队是 P1/P2 关键决策，全文无一处定案	明确 MVP 并发模型（建议：单活跃 Run、Run 内节点级并行、SQLite WAL + 单写者约定），写入 §4 或 §10
I-12	MINOR	§4.2/§4.5	fail_safe、feedback_report 作为路由目标未在 nodes 声明且未列为保留字；二者关系不明（human_review rejected → feedback_report 与 fail_safe 生成的 FeedbackReport 是同一内置节点吗？）。校验器查"无悬空"需要内置节点清单	枚举框架内置节点保留字及各自语义；建议 rejected 也走 fail_safe（终态语义一致：closed + FeedbackReport）
I-13	MINOR	§4.3/§6.1	状态机含 cancelled，但 Skill 协议四操作（create_run/submit_patch/get_status/get_result）无 cancel；取消入口与取消时在飞 task 的处置未定义	Skill 协议增加 cancel_run 或注明取消仅限运维侧 CLI，并定义在飞 task 处置
I-14	MINOR	§14 (D5)	遗漏风险：snapshot pin + 人工 review 可能数日 → 发布时基线已漂移，gerrit push 冲突。CI 冲突时的行为（fail_safe→新 Run？自动 rebase 禁止？）无 contract 约定	§14 增加该风险；01 中 CI 发布输入 contract 定义冲突处置（建议禁止自动 rebase，冲突即 fail_safe）
I-15	MINOR	§3/§1.3	交叉引用错位：§3 EvidencePacket 引"§8.4"（实为 §7.4）；§1.3 N3 引"§8.1"（实为 §7.1）。§8 无子节，提示曾整体重编号	全文核对交叉引用后再 freeze
I-16	MINOR	§3/§6.1	Skill 协议传输"纯 MCP / HTTP"二选一未定（对 Codex 是两套实现量级差异）；且 Skill 端点无认证设计——能访问端点者即可经 submit_patch 在构建机执行任意构建脚本。单机内网可接受，但信任边界应显式声明	定案传输协议（一个），§8 补一句 Skill 端点的信任边界假设
I-17	MINOR	§5.1 vs §6.2	contract_version: ClassVar[str] 单值与 §6.2 "Agent 声明兼容区间"表达力不一致	改为兼容区间表达式（如 PEP 440 specifier 风格）或补充说明
I-18	MINOR	§7.5/§9	构建日志类 artifact 体量大且无保留/清理策略；trace.json "task 级追加写"与 JSON 格式矛盾（JSON 不可追加，崩溃时文件损坏影响 D6 审计事实源）	改 JSONL（追加安全）；补 artifact 保留策略一句话决策
I-19	MINOR	§2.2 (D1)/§11	D1 只钉 langgraph 本体版本。已核实生态包发生过破坏性变更实例：langgraph-prebuilt==1.0.2 曾给 ToolNode.afunc 加必选参数（GitHub issue #6363），说明卫星包不在同等稳定承诺纪律下	"钉精确版本"扩展为钉全部 langgraph-* 依赖闭包（checkpoint、prebuilt 等），锁 lockfile
I-20	MINOR	§14 (R2)	R2 把"LangGraph 恢复语义与幂等假设不符"当作待 P1 实测的未知风险，但官方文档已明确：interrupt 恢复时节点从头重执行，interrupt 前副作用会重跑（见 Sources）。SDK 幂等层不是"不符时加严"的备选，而是设计上的硬前提	R2 改写为已知引擎行为 + P1 gate 验证实现正确性；§4.4 hitl gate 实现须注明"gate 前副作用必须幂等"约束
I-21	NIT	§4.2	全量示例未展示 threshold gate（benchmark 回归静默流向 review_ai.final），旗舰示例宜覆盖 §3/§4.4 声明的两种 gate 类型	示例中 benchmark 后补 threshold gate 节点
I-22	NIT	§7.2	缓存键统一含 snapshot_id，但 LLMWikiProvider 结果与代码基线无关，键语义不符（造成假失效）	缓存键策略由 provider capabilities 声明
3. CLARIFY 清单
C1：P5 期内网 LLM 不可达，reference Compiler Agent 只能以 FakeLLMProvider 跑通——D10 的 "真实 Agent 消费过 contract 才定稿 v1.0" 在认知路径上实为 fixture 驱动。v1.0 定稿是否需要至少一次内网真实 LLM 端到端？若否，请在 D10 明示效力边界。
C2：threshold gate 的参数模型（指标取自哪个 Report 字段、比较器、超限路由目标）是否明确划入 01 的 DSL 格式章节？
C3：停在 hitl gate 的 Run 是否有 TTL/超时策略（无限期挂起 vs 自动 close）？
C4：side_effect 完成记录存于何处、以何种事务保证与 task 状态一致（SQLite 同库事务？）？
C5：idem_key 粒度为 task 级输入，Compiler 单个 task 内多次 build（max_patch_attempts=2 × rebuild）的子操作幂等键派生规则由 SDK 规定还是 Agent 自定？
C6：D1 中 "如 langgraph==1.2.11" ——已核实 1.2.x 版本线真实存在（PyPI 最新为 1.2.x，2026 年活跃维护），1.0 的官方稳定承诺（semver、2.0 前无破坏性变更）属实；建议在 D1 脚注直接附官方 release policy 链接以固化依据。
4. 评审维度覆盖确认
架构合理性：分层与 Agent/编排边界（D2 路由权上收）成立且是子集流水线的正确前提；L2 Contract 作为"层"实为横切物，仅是视图表达问题，不构成 issue。结论：通过。
架构决策攻击：D1–D7、D9、D10 理由经攻击后站得住（D1 外部事实已核实属实）；D8 的三层链自身成立但存在 I-09 判定缺口；D1 需扩展到依赖闭包（I-19）。结论：基本通过，两处需补。
可配置子集流水线：DSL 存在实质漏洞——并行/汇合语义缺失（I-02）、optional 检查恒真（I-03）、环计数归属（I-04）、路由完备性（I-05）、内置节点未枚举（I-12）。结论：不通过，为 NO-GO 主因之一。
安全：token 链在"CI 类"判定（I-09）与恢复交互（I-07）上有洞；D7 数据边界在标注来源上有泄漏场景（I-08）；组件归属缺失（I-01）。结论：设计方向正确，四处需补。
Codex 可开发性：I-01/02/04/06/10/11/16 均为拿文档直接开发即会阻塞或产生分歧的点；[待补充]/[E0] 登记项之外仍有上述未定项。结论：不达"无歧义"标准。
恢复与幂等：SDK 层幂等的总体思路正确且与已核实的 LangGraph 恢复语义（节点重执行）匹配，但对不可逆外部效应的保证等级需如实降级声明（I-07/I-20）。结论：思路对，边界需澄清。
风险完整性：遗漏基线漂移发布冲突（I-14）、并发/锁（I-11）、artifact 膨胀（I-18）；R2 定性需修正（I-20）。结论：主干覆盖，三处补充。
内部一致性：§4.2↔§6.3 矛盾（I-03）、两处交叉引用错位（I-15）、cancelled 无入口（I-13）、contract_version 表达力（I-17）、feedback_report/fail_safe 术语（I-12）。结论：freeze 前需一轮一致性清理。
Sources（LangGraph 断言核实依据）：

LangChain & LangGraph 1.0 官方公告（稳定承诺、2.0 前无破坏性变更）
LangChain 官方 Release policy（semver）
LangGraph 官方 Interrupts 文档（恢复时节点从头重执行、interrupt 前副作用重跑）
langgraph PyPI（1.2.x 版本线存在性）
langgraph-prebuilt 1.0.2 破坏性变更实例 issue #6363

上面是Claude Code的review意见

核实完毕：LangGraph 1.2.x 确实存在（[GitHub Releases](https://github.com/langchain-ai/langgraph/releases) 显示 1.2.11 发布于 2026-08），"2.0 前无破坏性变更"出自 [LangChain 官方 1.0 公告](https://www.langchain.com/blog/langchain-langgraph-1dot0)，D1 事实基础成立（但见 I-17 的附带证据）。以下为独立评审结论。

---

# 评审报告：00_Framework_HLD_v0.1

## 1. 总裁决：**NO-GO**

存在 3 个 BLOCKER：DSL 示例自身违反文档的校验规则且并行汇合语义缺失（I-01/I-02）、approval token 生命周期自相矛盾（I-03）。这些都是 Codex 开工即踩的关键路径歧义，不符合文档自我声明的"无歧义、无 TBD"标准。

## 2. Issue 清单

| # | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|------|------|---------|-------------|
| I-01 | BLOCKER | §4.2 | DSL 示例违反本文档自己声明的校验规则：路由目标 `review_ai.static`、`review_ai.final` 的 `.限定符` 语法全文未定义；`fail_safe`、`feedback_report` 未定义为保留/内置节点（§3 术语表只定义了 FeedbackReport 报告和 fail_safe 状态，未定义节点）；按 §4.2"路由无悬空"规则，文档中唯一的全量示例自身即不合法，Codex 无法判断是示例错还是规则错 | 在 §4.2 定义节点实例寻址语法（`node.qualifier` 的语义：同 agent 多次调用如何寻址、各自的路由归属），列出内置保留节点清单（fail_safe、feedback_report 等）及其，并修正示例使其可通过本文档声明的校验器 |
| I-02 | BLOCKER | §4.2 / §4.4 | 并行扇出 `to: [ut, review_ai.static]` 的汇合（join）语义完全未定义：`from: review_ai, on: review_report_ready, to: human_review` 中的 review_ai 有两个实例（static/final），谁在何时触发 human_review？静态审查与 benchmark 链完成情况不一致时 gate 等谁？某并行分支进 fail_safe 时其余分支如何处置（继续/取消/等待）？这是子集编排（G1）的核心语义，LangGraph 的 fan-in 需要显式定义，文档无任何约定 | 在 §4.2 增加 join 语义定义（如显式 join 节点或 all-of/any-of 依赖声明）、并行分支中单个 fail_safe 的传播规则，并在示例中体现 |
| I-03 | BLOCKER | §4.4 vs §8 | approval token 生命周期自相矛盾：§4.4 称 hitl gate"恢复凭据是框架自己的 approval token（一次性……服务端校验后作废）"——即 token 在 gate resume 时作废；§8 第三层称"框架在 dispatch 前向 token 服务校验并作废"——即 token 在 CI dispatch 时才作废。一次性令牌不可能同时承担两个消费点。若 resume 时已作废，则 CI 层校验必然失败，发布路径永远走不通；若 dispatch 时才作废，则 gate resume 凭据是什么？这是发布安全机制核心时序，三层强制链（§8）断在中间 | 明确单一令牌时序（建议：token 仅在 CI dispatch 校验点作废，gate resume 使用引擎自身的 resume 机制而非 token），或拆分为 resume 凭据与 approval token 两种凭据，并同步修改 §3 术语、§4.4、§8 三处 |
| I-04 | MAJOR | §4.2 / §4.5 / D9 | 循环上限语义错位：`loop_limits` 配置在**节点**上，而 §4.5 的约束对象是**环**（"每条回流边必须隶属于一个带 loop_limits 的环"、"编排层维护环计数器"）。环计数器归属哪个节点？ut→compiler 环上 compiler 的 max_patch_attempts 与 ut 的 max_fix_rounds 如何合成？max_wall_clock_min 是单次 task 还是跨轮次累计、是否计入 gate 暂停时间（人工 review 可挂数天）？均未定义，"每个循环边所在环有 loop_limits"按现有 schema 无法校验 | 将循环上限显式建模为环级配置（或定义为"环上所有节点限额的最先触发者"），明确 wall_clock 的计时口径（建议排除 gate 暂停时间），并给出校验器对环的判定算法 |
| I-05 | MAJOR | §4.2 / §6.1 | 路由 `on:` 值与 Agent 可能输出的 status 之间无静态校验约定：Contract 未要求 agent_type 声明其 status 全集，校验器的"路由无悬空"只能查目标节点存在性，无法发现 `on: ut_paassed` 这类拼写错误——运行时该分支永久不触发，等价于路由悬空。业务 Agent 由第三方开发，此漏洞必然被踩 | 在 01_Contract_Spec 中要求每个 agent_type 注册时声明 status 枚举集，DSL 校验器增加"on 值 ∈ from 节点 agent_type 的 status 集"检查，并预留框架系统 status（见 I-09）的命名空间 |
| I-06 | MAJOR | §7.1 / D7 | 数据边界依赖调用方自我标注："每次调用由 SDK 标注 payload 数据类别"——若标注动作由业务 Agent 代码触发（SDK 只是通道），误标/漏标（internal_code 标成 public）即泄漏到外部 provider，"默认拒绝"只标注、不防错标。框架无法核验内容，此处的强制强度表述（"物理强制"级别的暗示）与实际能力不符 | 明确标注的权威来源：尽量由框架侧根据数据来源（artifact 类别、context 层来源）推导而非 Agent 声明；无法推导的在 §14 登记残余风险"数据边界依赖 Agent 诚实标注"，并在 conformance 增加误标检测用例 |
| I-07 | MAJOR | §8 / §2.1 / §9 / §1.1 | token 服务与 Review UI 的归属未定义：§8 要求"向 token 服务校验并作废"、§3 称 token"由 Review UI 签发"，但 §1.1 交付范围（框架+公共模块+reference Compiler）不含二者，02–06 业务指引列表也不含；签发密钥与信任链（框架如何验证 token 确由合法 Review UI 签发）完全未定义。§9 又称 Web 视图"只读"，与 Review UI 需要 approve/reject 写操作的关系不明。发布安全链的关键组件无人承建 | 在 §1.1 或 §10 明确 token 服务/Review UI 的交付归属（建议：框架交付最小 token 签发/校验服务 + 只读视图上的端点），并定义密钥管理与时序 |
| I-08 | MAJOR | §5.1 vs §8 | 进程模型矛盾：§5.1 采用 entry-point 插件注册（同进程加载业务 Agent 类），§8 却称"Agent 进程以最小权限运行；发布凭据仅注入 CI 类 Agent"。同进程内任何插件代码都能读到注入的发布凭据，凭据隔离不成立 | 二选一并写明：CI 类 Agent 独立进程部署（凭据注入该进程），或承认 MVP 同进程并将凭据隔离降级为进程隔离（在 §14 登记风险） |
| I-09 | MAJOR | §5.1 / §4.3 | Agent 异常路径无定义：setup 失败"task 不启动"之后 Run 走向何处？execute 抛未捕获异常映射到什么 status、走哪条路由？系统错误（infra 故障）与业务失败（build_failed_exhausted）的区分、是否一律进 fail_safe，均无规定。DSL 作者无法为异常写路由，Codex 实现时只能自创语义 | 在 §4.3/§5.1 定义框架保留的系统级 status（如 system_error）及其默认路由（建议默认 fail_safe），并说明 setup/teardown 失败的处理 |
| I-10 | MAJOR | §5.2 / §4.3 | 幂等记录与副作用非原子："命中已完成记录则跳过"要求完成记录落盘，但与记录落盘之间存在崩溃窗口——窗口内崩溃将重放副作用。发布有一次性 token 兜底（设计巧合地自洽），但刷板、构建提交等是 at-least-once。文档未声明该语义，也未要求副作用自身幂等或"先记意图、后确认"两阶段记录。另 `idem_key` 的 `input_digest` 定义缺失：对 artifact_ref（路径）还是内容取摘要？artifact 是否规定，直接影响重放正确性 | 在 §5.2 显式声明 at-least-once 语义及各类副作用的兜底机制；定义 input_digest 的精确组成；在 §7.5 明确 artifact 不可变性 |
| I-11 | MAJOR | §14 / R6 | R6 对策部分无效：import-linter 只能约束 monorepo 内代码（§4.1 的硬封装规则同理），业务 Agent 作为外部包可自由 `import langgraph` 或不经 SDK 直接执行副作用，conformance 是准入测试而非运行时强制，测试之后的行为无约束 | 修正 R6 表述：承认对业务侧代码仅能"准入检测+约定"，补充可执行的运行时约束（如构建/发布能力仅经框架注入的句柄暴露，句柄按 agent_type 授权——与 I-08 联动） |
| I-12 | MINOR | §5.12 | `contract_version: ClassVar[str]` 是单一值，§6.2 称"Agent 声明兼容区间"，二者不一致，装配校验规则无法实现 | 统一为兼容区间声明（或单一版本+框架侧兼容矩阵） |
| I-13 | MINOR | §5.3 | 引用"（§8.3）"不存在——§8 无子节，Context 管理实际在 §7.3 | 修正交叉引用 |
| I-14 | MINOR | §4.2 / §6.3 / §8 | 校验规则"下游输入依赖在本 pipeline 不存在则必须为 optional"与 CI 的 approval_token未说明：token 由人工供给而非任何上游节点，按字面规则含 CI 的 pipeline 要么无法通过校验、要么被错误放行 | 在校验器规则中显式定义 approval_token 为"外部供给依赖"例外类别 |
| I-15 | MINOR | §3 / §4.3 / §4.5 | `fail_safe` 一词三用：Run 终态（§3、§4.3 状态机）、路由目标/内置节点（§4.2、§4.5）；`feedback_report` 在路由中出现但术语表只有 FeedbackReport（报告而非节点）。状态与节点命名空间混用 | 区分保留节点名与 Run 状态名（如节点 `__fail_safe__`），统一术语表 |
| I-16 | MINOR | §3 | Skill 协议"纯 MCP / HTTP + 文件"有歧义：MCP 与 HTTP 是二选一还是并存？`submit_patch` 的 patch 格式（unified diff/series）及对 pin 住 snapshot 的可应用性校验（过期 patch 拒绝策略）未定义；同一 run 是否接受多次 submit_patch 未规定 | 明确传输形态；patch 格式与基线校验、重复提交语义写入的 Skill 协议章节（本文档至少给出决策句） |
| I-17 | NIT | §2.2 D1 | LangGraph 1.2.x 与"2.0 前无破坏性变更"承诺属实（[官方 1.0 公告](https://www.langchain.com/blog/langchain-langgraph-1dot0)、[Releases](https://github.com/langchain-ai/langgraph/releases) 1.2.11@2026-08），但存在 semver 承诺下仍发生破坏性变更的先例（[langgraph-prebuilt 1.0.2 事件，issue #6363](https://github.com/langchain-ai/langgraph/issues）——钉精确版本的决策因此是对的，建议在 D1 理由中补一句此依据并注明 prebuilt 等附属包需同样钉版 | D1 理由补充：附属包（langgraph-prebuilt/checkpoint）一并钉版 |
| I-18 | NIT | §2.1 | 分层图将业务 Agent 画在 L0 之下（"以插件形式接入"箭头自 L0 指出），与"继承 SDK AgentBase"（依赖方向应在 L3 之上）相悖，图示依赖方向误导 | 调整分层图，业务 Agent 置于 L3 之上 |
| I-19 | NIT | §4.2 | pipeline YAML 的 `version: 1` 与 Contract 独立版本号（§6.2）的关系未说明 | 说明 pipeline version 即 DSL schema 版本，纳入 Contract 版本体系 |

## 3. CLARIFY 清单

1. §7.1 cascade"失败升级"判据是什么（超时/异常/低置信度）？质量性失败如何判定？
2. §4.3 hitl gate 的人工响应无超时策略——Run 可无限期 paused，是否有提醒/升级/自动 fail_safe 机制？
3. 并发 Run 对 BuildExecutor（本机 gbs）与 BoardPool 的争用策略：串行队列还是并发上限？（N1 单机下单实例并发未定义）
4. pipeline 配置的生命周期管理：`create_run(pipeline_id)` 的 pipeline 由谁、如何安装/更新/废止？运行中的 Run 引用被更新的 pipeline 时行为？
5. §5.3 token budget 的配置位置（pipeline YAML 节点级？Agent 配置？）未指明。

## 4. 评审维度覆盖确认

1. **架构合理性**：L0–L4 分层与 Agent/编排边界（D2）成立且清晰，仅图示依赖方向有误（I-18）——成立。
2. **D1–D10 攻击**：D1 事实核实通过（附 I-17 钉版依据）；D2/D3/D4/D6/D10 站得住；D5 与 submit_patch 语义有缺口（I-16）；D7 自我标注削弱强制力（I-06）；D8 令牌时序矛盾（I-03）；D9 环/节点限额错位（I-04）。
3. **子集流水线**：上游缺失语义（§6.3）设计合理，但 join 语义缺失（I-02）、on 值无校验（I-05）、环限额语义未定义（I-04）、CI 依赖例外未说明（I-14）——当前不足以支撑无歧义实现。
4. **安全**：三层强制链因 token 消费点矛盾而断裂（I-03），token 服务归属与信任链缺失（I-07），同进程插件击穿凭据隔离（I-08），数据边界依赖自我标注（I-06）——存在实质。
5. **Codex 可开发性**：DSL 示例自相矛盾（I-01）、异常路径（I-09）、幂等细节（I-10）、契约版本（I-12）、悬空引用（I-13）等关键路径歧义多处——不满足"直接开发"标准。
6. **恢复与幂等**：checkpoint+SDK 幂等键的双层设计方向正确且正确声明"不依赖引擎"，但崩溃窗口的 at-least-once 语义与 input_digest 未定义（I-10），wall_clock 计时口径未定义（I-04）——基本自洽，需。
7. **风险完整性**：§14 缺三处重大风险——token/Review UI 组件无人承建（I-07）、业务 Agent 运行时约束缺失使 R6 对策虚设（I-11）、数据边界误标残余风险（I-06）。
8. **内部一致性**：发现 §4.4↔§8 令牌作废矛盾（I-03）、§5.1↔§6.2 版本声明矛盾（I-12）、§5.1↔§8 进程模型矛盾（I-08）、§5.3 悬空引用（I-13）、fail_safe 术语三用（I-15）——多处需修。

**总结**：架构方向与决策骨架（D2/D5/D6/D10、硬封装、EvidencePacket 固化）是扎实的，问题集中在三处关键路径的规格缺口：DSL 语义（I-01/02/04/05）、approval token 时序与组件归属（I-03/与幂等语义（I-09/10）。这些正是 P1–P2 首先落地的部分，按"Codex 直接开发"标准必须在 draft freeze 前闭环。建议修复 I-01～I-03 及全部 MAJOR 后重新提交一轮评审。

上面是Kimi Code的review意见

## 1. 总裁决：NO-GO

存在 8 条 BLOCKER。当前版本尚不能 draft freeze，主要阻断点是：DSL 执行语义不完整、发布授权链并未真正形成安全边界、幂等与恢复存在不可关闭的崩溃窗口、执行与数据隔离不足。

## 2. Issue 清单

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| I-01 | BLOCKER | [§4.2](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:142) | （置信度 10/10）示例只声明 `review_ai` 节点，却路由到 `review_ai.static`、`review_ai.final`；`fail_safe`、`feedback_report` 也未声明。DSL 没有入口、端口、多次调用、fork/join、并行状态归并语义。反例：静态审查先返回 `review_report_ready`，可能在 UT/Benchmark 完成前直接进入人工 gate。 | 定义完整 v1 图语义：显式入口/终态、保留内置节点、节点端口或独立节点、多次调用标识、fork/join/barrier、状态 reducer、事件关联和路由穷尽性；提供一份可由校验器实际通过的全量 YAML。 |
| I-02 | BLOCKER | [§4.2、§6.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:177) | （置信度 9/10）“任意合法子集”没有定义“合法”；同时规定所有 Report 消费字段一律 optional、缺失即降级。反例：Compiler→CI 或 CI-only 配置可能跳过 UT、Benchmark、Review；threshold gate 在指标缺失时也无 fail-open/fail-closed 规定。 | 引入节点 capability/requirement 与 pipeline policy invariant；区分“整个上游未执行”“存在但字段缺失/非法”；规定安全检查是否可裁剪、缺失指标的默认处理，并校验可达性、死路、路由穷尽以及所有 CI 路径的批准前置条件。 |
| I-03 | BLOCKER | [§2.1、§2.3、§4.4、§6.1、§10、§13](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:48) | （置信度 10/10）Review UI/token service 是 approval 链必需组件，但外部系统清单、仓库结构、协议消息和分期交付均未包含其实现或责任方；现有 Skill API 也没有 approve/reject/resume。Codex 无法实现完整 HITL 路径。 | 明确 UI、可信后端和 token service 的交付归属、部署边界及接口；补齐 reviewer 认证授权、decision 提交、签发、撤销、过期、原子消费、resume/reject API 和持久化模型。浏览器 UI 不应自行持有签发能力。 |
| I-04 | BLOCKER | [§3 approval token、§6.4、§8](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:129) | （置信度 10/10）§8 将发布凭据直接注入业务 CI Agent。即使 TaskInput 含合法 token，CI Agent 仍可忽略批准对象，发布另一提交、分支或目标；因此 contract 字段不是“物理强制”。token 也仅绑定 run 与 patch-series hash，未绑定 snapshot、最终 tree、发布目标和 pipeline 配置。 | 将凭据收回到框架控制的 release broker；CI Agent 只生成发布计划。broker 校验并发布不可变 release manifest，至少绑定 snapshot、ordered patch/tree digest、目标仓库/分支、动作、pipeline digest、reviewer、过期时间，并在发布前重新核验。 |
| I-05 | BLOCKER | [§4.4、§5.2](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:193) | （置信度 10/10）`side_effect(idem_key, fn)` 无法关闭“外部操作成功、完成记录尚未落盘即崩溃”的窗口；token“校验后作废”若非原子操作，也可被并发 dispatch 重复消费。LangGraph 官方说明 interrupt 恢复会从节点开头重跑，未完成任务也可能重新执行副作用。[官方依据](https://docs.langchain.com/oss/python/langgraph/interrupts) | 定义持久化操作状态机（claimed/running/succeeded/unknown/failed）、互斥租约与原子 compare-and-consume；要求外部系统接受幂等键或提供结果查询/对账。发布、刷板等不可逆动作必须定义专用恢复协议，不能依赖通用包装器宣称 exactly-once。 |
| I-06 | BLOCKER | [D6、§4.3、§7.5](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:94) | （置信度 9/10）`trace.json`、artifact 文件、SQLite 索引、幂等记录和 LangGraph checkpoint 分别落盘，却没有提交顺序、原子边界或冲突时的权威顺序。并行 task 追加同一 JSON 文件还可能丢写。反例：artifact 已写但索引未提交，checkpoint 又把 task 标为完成，恢复时既不能重跑也找不到结果。 | 指定一个框架拥有的持久化事件/状态账本为权威源；artifact 使用不可变、带摘要的 blob；定义 task-result、artifact refs、幂等状态的原子提交或 outbox/reconcile 协议。trace 应由账本派生或采用并发安全的 append-only 格式。 |
| I-07 | BLOCKER | [D1、D5、§4.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:89) | （置信度 9/10）Run 只 pin 源码 snapshot，没有 pin pipeline YAML/digest、contract、框架、Agent 包、provider 配置和引擎版本。暂停期间升级后，旧 checkpoint 可能按新路由恢复，甚至改变 gate。LangGraph 官方明确说明持久化 thread 会使用最新部署的 graph，因此图演进必须保持兼容。[官方依据](https://docs.langchain.com/oss/python/langgraph/backward-compatibility) | 为每个 Run 固化 execution manifest；恢复时只允许加载匹配版本。定义图/schema 迁移、旧 worker 保留、drain 或拒绝恢复策略，并将 approval token 绑定 execution-manifest digest。 |
| I-08 | BLOCKER | [§5.1、§7.1、§7.6、§8](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:206) | （置信度 9/10）外部 patch 会进入 GBS 构建，业务 Agent 通过 entry point 加载；但只有“最小权限”一句，没有进程、文件系统、网络或 secret 隔离。恶意构建脚本或 Agent 可直接开网络连接泄漏源码，绕过 LLM provider 数据校验；git worktree 只隔离 Git 状态，不是安全沙箱。 | 明确信任模型；在隔离 worker/容器中运行 Agent 和构建，规定只读/可写挂载、网络 egress allowlist、secret broker、CPU/内存/进程数限制与可强杀超时。所有外部副作用通过受控 broker，非 CI worker 不得接触发布凭据。 |
| I-09 | MAJOR | [D7、§7.1](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:95) | （置信度 9/10）Provider 自报 `accepted_data_classes`、SDK/Agent 自标 payload，不能构成可信策略；混合 payload、KnowledgeResult、派生摘要、cascade fallback 和 LLM 输出的分类传播也未定义。错误低标即可把源码送往外部 provider。 | 由中心安全配置授权 provider，而非信任 provider 声明；为输入 artifact 建立来源分类，定义分类格与合并规则，派生数据默认继承最高敏感级；每次 cascade/fallback 重新校验并 fail closed。 |
| I-10 | MAJOR | [§5.1、§4.5](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:198) | （置信度 9/10）`execute()` 是同步函数，但未定义 Agent 实例作用域、并发模型、worker 协议、重试、取消、硬超时以及 setup/execute/teardown 异常映射。进程内卡死的 Python 调用无法由 `max_wall_clock` 安全终止。 | 定义 task worker 生命周期与进程边界、租约/heartbeat、取消和 hard-kill 语义；列出 setup、execute、teardown、进程退出、超时、失联分别对应的框架结果及是否可重试。 |
| I-11 | MAJOR | [D9、§4.2、§4.5](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:97) | （置信度 9/10）DSL 将 `loop_limits` 放在节点上，正文却要求“每个环”有上限；共享节点、重叠环和多个回流边时无法判断使用哪个计数器。计数在开始还是完成时增加、wall-clock 是否含暂停、计数如何 checkpoint 均未定义。 | 为环显式定义 `loop_id`/budget，或以强连通分量建立统一预算；规定 attempt 计数时点、持久化、暂停计时和 hard timeout。静态校验应证明每个可达环有界，并再设 Run 级总预算。 |
| I-12 | MAJOR | [§3 HandoffResult、§4.2](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:123) | （置信度 9/10）只定义了业务 status 路由；Agent 抛异常、超时、返回非法 schema、返回未知 status 或没有匹配 route 时的行为未定义。“路由无悬空”不能防止执行时无路可走。 | 定义框架级 outcome taxonomy；校验每种 agent_type 的 status 路由穷尽且互斥；为 exception/timeout/invalid-result/unmatched-status 提供显式 error route，默认 fail_safe。 |
| I-13 | MAJOR | [§4.2、§6.4](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:166) | （置信度 9/10）并行静态审查可能针对 patch series A；UT 随后生成修复形成 series B，但文档没有陈旧结果失效、取消、合并或冲突规则。A 的 ReviewReport 可能被用于批准 B。 | 所有 TaskInput/Report 绑定 `series_id` 与 tree digest；join 只接收相同 digest 的结果，旧分支结果自动标 stale 且不可进入 gate；定义多 Agent patch 的确定顺序、冲突处理与重新验证规则。 |
| I-14 | MAJOR | [§3 fail_safe、§4.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:130) | （置信度 9/10）术语表称 `fail_safe` 是终态，状态图却为 `fail_safe → closed`；`succeeded`、`cancelled` 是否还需 closed 未说明，也缺少 snapshot 失败、非法/重复 submit、gate 过期、恢复失败及副作用进行中取消等状态。reject 后新 Run 使用旧 snapshot 还是重新 pin 最新也未定。 | 给出穷尽状态转移表，包含命令、guard、幂等响应、非法转换、终态；明确 parent Run 的 snapshot 继承/重基线规则及其对 patch/approval 的影响。 |
| I-15 | MAJOR | [§3 Skill 协议、§6.1](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:128) | （置信度 9/10）“MCP / HTTP + 文件”未说明是一套协议的两种 transport 还是多个协议；外部接口缺少认证授权、request id、重复 submit、并发调用、文件引用生命周期、patch 摘要/大小/path 校验和标准错误语义。 | 定义 transport-neutral 操作 contract 及明确 adapter；规定调用者认证、授权、idempotency key、状态前置条件、限额、内容摘要、文件句柄安全和稳定错误码。 |
| I-16 | MAJOR | [D5、§3 Snapshot、§7.6](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:93) | （置信度 8/10）Snapshot 被定义为 manifest/commit set，`GbsLocalExecutor` 却描述为单一 git worktree；多仓 Tizen 源码的 repo 标识、路径映射、跨仓 patch series 和最终 tree digest 均未定义。 | 固化规范化 snapshot manifest：repo ID、remote、commit、相对路径和依赖；patch 明确归属 repo，并定义应用顺序、跨仓失败回滚及整个 snapshot+series 的规范摘要算法。 |
| I-17 | MAJOR | [D1、§4.1、§10](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:136) | （置信度 9/10）import-linter 只能阻止类型泄漏，不能证明引擎可替换；并行、interrupt、checkpoint 与恢复语义仍会渗入 orchestration。`engine/` 与 `orchestration/` 对 StateGraph 编译、执行和 checkpoint 的所有权也未明确。 | 定义框架自有 EnginePort、状态/事件模型及 engine conformance suite；给出两目录的依赖方向和职责矩阵，并承认在途 checkpoint 需要迁移或 drain。当前官方版本确为 1.2.11，但应将“如”改为冻结时的实际精确锁文件，并锁定相关 checkpoint 包。[版本依据](https://reference.langchain.com/python/langgraph/langgraph) |
| I-18 | MAJOR | [D10、G6、§6.2、§13](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:31) | （置信度 9/10）单个 Compiler Agent 无法真实消费 BenchReport、ReviewReport、CI 发布 contract、BoardPool 行为等全部契约，因此“Compiler 跑通后 contract v1.0”不足以验证全部 contract。 | 不要求实现完整业务 Agent，但在 v1.0 gate 前为五类 Agent 都提供独立 producer/consumer fixture、可运行 skeleton 和代表性 E2E；建立 contract compatibility matrix。 |
| I-19 | MAJOR | [D4、§10、§13](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:92) | （置信度 9/10）业务团队要“以包依赖或 fork 使用”，但仓库结构和阶段计划没有 Python 包边界、构建发布流水线、安装方式、SDK/contract 独立版本或升级策略。代码存在并不等于业务开发者可消费。 | 规定发布包及依赖方向、entry-point namespace、版本兼容范围、制品仓库/安装命令和 CI 发布 gate；将 fork 限定为特殊模式并说明同步责任。 |
| I-20 | MAJOR | [§5.3、§7.5、§8、§9](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:228) | （置信度 9/10）prompt、EvidencePacket、响应、工具调用和 artifact 全部持久化并可由 Web 视图浏览，但没有 secret redaction、访问控制、保留期和删除规则。approval token、凭据、源码或日志秘密可能进入长期审计记录。 | 建立敏感字段 schema；token/凭据只记录指纹，不记录 bearer value；持久化前统一脱敏并保留分类标签；定义 Web 访问认证、最小授权、保留/销毁和必要的静态加密策略。 |
| I-21 | MAJOR | [§7.6、§9、§14 R4](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:300) | （置信度 8/10）全量流水线允许并行，而 GBS、板卡、worktree、artifact、cache 都没有并发上限、backpressure、磁盘水位或清理策略。多个 Run 可耗尽 CPU/磁盘，使 checkpoint/审计写入失败。N2 的多租户配额裁剪不等于可以省略单机自我保护。 | 定义 Run/task 调度器、每类资源 semaphore、排队/优先级/取消规则、worktree 清理、cache 上限、artifact retention、磁盘 admission watermark 及低磁盘 fail_safe。 |
| I-22 | MAJOR | [§11、§13 P1/P4](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:345) | （置信度 9/10）80% coverage、一次 kill 恢复和两条 E2E 不能验证本文最危险的并发与崩溃窗口。缺少 token 双消费、每个持久化边界 kill、DSL 环性质、陈旧 patch、损坏 checkpoint/artifact 和 worker 逃逸测试。 | 在 HLD 列出强制测试类别：DSL property/fuzz、状态机 model-based、并发 token、逐崩溃点 fault injection、存储损坏/对账、patch lineage、sandbox/egress、每类 Agent contract compatibility；安全与恢复模块要求完整分支覆盖，而非仅全局 80%。 |
| I-23 | MAJOR | [§4.2、§5.1、§14 R6](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:179) | （置信度 8/10）“过 conformance 的记录”没有定义如何产生、保存和绑定。Agent 包通过后若被替换，旧记录仍可能被接受；业务插件也可能伪造声明。 | 将 conformance 结果绑定 agent 制品 digest、contract/framework 版本和测试套件版本；加载时验证可信 attestation，或在安装/启动时实际运行套件；变更 digest 后自动失效。 |
| I-24 | MAJOR | [§14](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:375) | （置信度 10/10）风险表遗漏了已影响关键路径的风险：恶意 patch/插件逃逸、发布凭据滥用、token 双消费、磁盘耗尽、审计/索引分裂、旧 checkpoint 在新图上恢复、approval 服务不可用、并行结果陈旧。现有 R2“极端情况换引擎”也未覆盖在途 Run 迁移。 | 将上述风险逐项登记，并为每项补 owner、检测信号、预防控制、恢复动作及对应 Phase gate；不要只写笼统“加严/替换”。 |
| I-25 | NIT | [§1.3、§3、§5.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.1.md:39) | （置信度 10/10）存在三处失效引用：LLM 路由写“§8.1”实际是 §7.1；EvidencePacket 写“§8.4”实际是 §7.4；Context/token budget 写“§8.3”实际是 §7.3。 | 修正为 §7.1、§7.4、§7.3，并在 freeze gate 加内部链接检查。 |

## 3. CLARIFY 清单

无。关键歧义均直接影响可实现性、安全或恢复正确性，已提升为 issue，而非留作非阻塞提问。

## 4. 评审维度覆盖确认

1. **架构合理性**：分层方向合理，Agent 只产结果、编排层持有路由权的原则成立；但 engine/orchestration、插件执行及发布 broker 边界尚未闭合。
2. **架构决策攻击**：D1 选型与 semver 理由基本成立，但封装/恢复版本有缺口；D2 原则成立、状态语义不足；D3 可接受；D4 需补分发；D5 需补多仓 manifest；D6–D9 当前不成立；D10 的验证主体不足。
3. **可配置子集流水线**：不足；缺少 entry、fork/join、端口、穷尽路由、合法子集 policy、陈旧结果和可证明有界循环语义。
4. **安全**：不足；token 三层链可被 CI Agent 权限、非原子消费和未绑定发布目标绕过，D7 也可被 Agent/构建脚本直接 egress 绕过。
5. **Codex 可开发性**：不足；控制面 API、执行模型、图语义、存储提交协议、版本恢复和发布边界均存在关键未定项。
6. **恢复与幂等**：不自洽；通用包装器无法处理外部成功后崩溃，checkpoint、审计、artifact 与幂等记录之间没有一致性协议。
7. **风险完整性**：不足；§14 遗漏安全隔离、授权竞争、数据损坏、资源耗尽、旧图恢复等重大风险；N1–N6 本身可保留，无需扩展 Non-goals。
8. **内部一致性**：存在 DSL 节点/端口不一致、`fail_safe` 终态定义冲突及三处错误章节引用。

上面是Codex的review意见
