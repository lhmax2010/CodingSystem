# 复审报告：00_Framework_HLD_v0.2（Kimi 方）

## 1. 总裁决：**NO-GO**

v0.2 对第一轮的处置质量很高——三个 BLOCKER 簇（DSL 语义、token 时序、幂等/存储）的修复方向均正确且比我原建议更简。但 §4.2.1 的"验收级"示例自身存在 join 死锁（N-01），恰好复发我第一轮 I-01 的同类问题（示例违反本文档自身语义），按"Codex 直接开发"标准构成 BLOCKER。另有 8 个 MAJOR，多为新组件（Ledger 单写者 vs worker/approval/broker 写入路径、编排进程崩溃时孤儿 worker、发布 adapter 归属）之间的接缝缺陷。

## 2. 任务 A：本方第一轮 issue 处置核验

| 编号 | 结论 | 不接受的理由与定位 |
|------|------|------|
| I-01 (BLOCKER) | 接受关闭 | 点号寻址废除（§4.2.2）、保留节点定义（§3）、示例重写，方向正确。**但注意**：新示例仍有一处自身不一致（join wait_for 含无入边的 `ut`），作为新 issue N-01 提出，不构成对本条处置的否定 |
| I-02 (BLOCKER) | 接受关闭 | §4.2.4 all-of join + series 一致 + 分支 fail_safe 传播（取消在飞分支）已定义；残留的 join 聚合语义与超时来源问题另立 N-02/N-11 |
| I-03 (BLOCKER) | 接受关闭 | §4.4"resume 不消费 token，唯一消费点在 broker"彻底消除双重作废矛盾，时序闭合 |
| I-04 | 接受关闭 | §4.5 环级 budget 对象、入环计数、Ledger 持久化、wall_clock 排除 paused、多环独立计数，全部命中 |
| I-05 | 接受关闭 | §4.2.3 status 全集注册 + on 值校验 + 穷尽性 + default_route 必填，加载期拦截拼写错误 |
| I-06 | 接受关闭 | D7 出生标注 + 密级格 + 聚合取最高 + 禁降级 + 中心授权 + 每跳重校验；残余风险 R8 如实登记 |
| I-07 | 接受关闭 | §1.1 交付范围已含 Approval 服务 + Review CLI + Release broker；§8.2 签发密钥归属明确 |
| I-08 | 接受关闭 | §5.1.2 worker 子进程模型 + 凭据仅 broker 进程 + 能力句柄授权注入，进程边界清晰 |
| I-09 | 接受关闭 | §4.3.2 sys.* outcome 分类 + retry 策略 + default_route 兜底 |
| I-10 | 接受关闭 | §5.2 at-least-once 显式声明 + 两阶段状态机 + probe 对账；input_digest 按 content digest、artifact 不可变（§7.5） |
| I-11 | 接受关闭 | R6 改写如实承认"运行时非全量强制"，运行时约束以能力句柄注入实现——正是原建议 |
| I-12 | 接受关闭 | §5.1.1 `contract_requires` PEP 440 specifier，与 §6.2 兼容区间一致 |
| I-13 | 接受关闭 | 交叉引用已修正（§5.3 → §7.3） |
| I-14 | 接受关闭 | §6.3 明确 approval_token 为"外部供给依赖"类别 |
| I-15 | 接受关闭 | §3：fail_safe 仅指保留节点，Run 终态统一 closed(reason) |
| I-16 | 接受关闭 | §6.5：HTTP+JSON 单协议、series 格式与基线可应用性校验、单次 submit 语义 |
| I-17 | 接受关闭 | D1 升级为完整依赖闭包 lockfile，并引用了 prebuilt 1.0.2 先例作为依据 |
| I-18 | 接受关闭 | §2.1 分层图业务 Agent 已置于 SDK 之上 |
| I-19 | 接受关闭 | `dsl_version` 纳入 Contract 版本体系（§4.2.1/§6.2） |
| CL-1~CL-5 | 接受关闭 | cascade 判据、gate TTL、D11 并发、pipeline 文件+digest 管理（CL-4 部分采纳合理，MVP 裁剪可接受）、llm_budget 节点级，均有落点 |

**结论：本方 19 条 issue + 5 条 CLARIFY 全部接受关闭。** 他方处置抽查：Codex I-07（D12 拒绝迁移）与 I-08（N7 裁剪）见任务 B；CC I-09 的等效方案（release 保留节点取代"CI 类判定"）核验成立，确实强于原建议。

## 3. 任务 B：仲裁点独立判断

**B-1（N7/D13 信任模型裁剪）：接受。** 威胁模型显式且内部自洽：内网单机 + bearer 认证来源 + 半可信构建脚本。关键论据：不可逆损害路径（发布凭据外传/冒用）已由 broker 进程隔离 + token 单次核销物理覆盖（D8），沙箱缺失的残余面（构建脚本网络外传源码）登记 R7 且附"假设失效前置补沙箱"的触发条件——这是诚实的风险登记而非掩盖。MVP 单机范围（N1）下再要求容器沙箱属范围膨胀。附带观察（不构成 issue）：R7 的检测信号"内网出口监控"是环境侧能力、不在 E0 预检清单内，建议在 09 中其责任归属。

**B-2（D12 拒绝恢复、不做在途迁移）：接受。** D11 单活跃 Run 前提下，在途迁移的收益仅为省一次重跑（run_budget 上限 1440min 封顶了损失），而跨版本 checkpoint 恢复的正确性风险高且几乎无法充分测试；拒绝恢复 → fail_safe → FeedbackReport 注明版本漂移 → 新 Run，是 fail-closed 且可追溯的闭环。"更简且安全"的裁剪理由成立。一个运维面观察见 CLARIFY-4（provider 配置 digest 粒度）。

**B-3（DSL v1 语义闭合性）：反对闭合）。** 框架性语义（显式节点、join/loops/default_route/保留节点/合法子集定义）已接近闭合，但三处实质缺口使其尚不可实现：① §4.2.1 示例自身死锁（N-01）——且该示例被声明为"校验器验收用例"，意味着校验器实现与示例至少错一个；② join 下游 TaskInput 聚合语义未定义（N-02）；③ `terminal: true` 节点的 Run 成功判定未定义（N-03）。修复这三条后我可转为接受。

## 4. 新 issue 清单

| # | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|------|------|---------|-------------|
| N-01 | BLOCKER | §4.2.1 / §4.2.4 | 验收示例自身死锁：join `pre_final_reviewwait_for: [ut, bench_gate, review_static]` 含 `ut`，但 routes 中没有任何 `from: ut, to: join:pre_final_review` 的边——按"wait_for 上游到达才触发"语义，ut 的结果永远不会到达 join，human_review 永不触发；若 wait_for 语义实为"产出过结果即算到达"，则 `to: join:<id>` 路由边冗余且两套语义并存。该示例被声明为"校验器验收用例，必须可通过校验"（§4.2.1），矛盾显式化。此为我第一轮 I-01 的同类复发：文档自身样例违反自身语义 | 二选一并写死：① wait_for 成员必须有入 join 的路由边（校验器强制），修正示例（ut 的结果经 bench_gate 传递即可，wait_for 改为 [bench_gate, review_static]）；② 或定义 wait_for 为"Run 内已产出同 series 结果的节点"并说明路由边仅作触发提示 |
| N-02 | MAJOR | §4.2.4 / §6.1 | join 触发后下游节点的 TaskInput 聚合语义未定义：`pre_final_review` 等到 bench_gate/review_static 等多份结果后，`review_final` 的 TaskInput 里装什么——全部上游 HandoffResult 引用列表？各 Report 的 artifact_ref 合并？字段名与顺序？Codex 无法实现 join 编译 | 在 §4.2.4 或 01 中定义 join 输出结构（建议：TaskInput 增加 `join_inputs: list[上游结果引用]` 固定形态） |
| N-03 | MAJOR | §4.2.2 / §4.3.1 | `terminal: true` 节点的 Run 成功判定未定义：终局节点列举含"显式 terminal: true 节点（子集流水线用）"，但到达 terminal 节点后 closed(reason) 的 reason 如何由该节点 outcome 决定？benchmark-only 子集中 bench 回归超限也 closed(s 吗？G1 的主用例之一缺成功语义 | 定义 terminal 节点的 outcome→reason 映射规则（如 outcome∈声明的 success 集 → succeeded，否则 fail_safe），并在 compiler_bench_only.yaml 示例体现 |
| N-04 | MAJOR | §7.5 vs §8.2 / §8.3 | Ledger 单写者规则与 approval/broker 写入路径表述矛盾：§7.5 称"写者唯一（编排进程；approval/broker 经编排进程 API 写入）"，但 §8.2 写 approval 服务"写 Ledger 并触发 gate resume"、§8.3 写 broker"Ledger 事务内校验 token……并标记核销"——读起来是直写。若确实经编排进程 API 中转，则 §8.2 的"broker 以共享密钥（HMAC）验证签发真实性"成为多余的第二验证通道（编排进程本就信 approval 服务），且 HMAC 密钥分发全文未定义 | 统一表述：approval/broker 的一切状态变更经编排进程 API 以 Ledger 事务提交（§8.2/8.3 改写为"经编排进程 API"）；据此重审 HMAC 验签的必要性，保留则补密钥分发，去除则删 §8.2 末句 |
| N-05 | MAJOR | §5.1.2 / §4.3.3 | 编排进程崩溃时在飞 worker 的处置未定义：租约 heartbeat 由编排层持有（§5.1.2），编排进程死亡后 worker 失去心跳对端——自杀？继续跑？后者会在恢复重放后与重执行的 worker 并发产生重复副作用（同 worktree 构建、同板卡刷写）。P1 完成 gate 恰是"kill 实测"，此场景必现 | 定义 worker 失联自杀纪律（heartbeat 超时 → 自行退出，副作用由 §5.2 probe 对账）及编排进程恢复时的孤儿 worker reaping |
| N-06 | MAJOR | §5.2 / §7.5 / §5.1.2 | side_effect 两阶段状态机声称"Ledger 同库事务"（§5.2），但执行体在 worker 子进程内（SDK 包装器随 execute 运行于 worker），而 Ledger 写者唯一为编排进程（§7.5）——claimed/running/succeeded 状态迁移须经 worker→编排进程 IPC 同步提交，该协议（同步性、IPC 失败时的状态、与 task 完成事务的关系）全文未定义。幂等是 G4 核心机制，此处是实现级歧义 | 在 §5.2 明确迁移的提交通道（worker 经 IPC 请求编排进程代为事务写入）及 IPC 失败语义 |
| N-07 | MAJOR | §2.3 / §8.3 vs §5.1.1 | 发布 adapter 归属两说：§2.3 与 §8.3 称"gerrit adapter 属 CI 业务侧按 broker 插件接口实现，运行于 broker 进程内"；§5.1.1 的能力句柄模型则是业务 Agent 在自有 worker 内使用框架注入的通道。两套集成点并存，Codex 需二，业务开发者拿到的指引也分裂（broker 插件 vs 能力句柄） | 定案其一：broker 插件接口（与 D8"凭据仅 broker 进程"最自洽，能力句柄不含发布通道），§5.1.1 能力句柄清单显式排除发布，02–06 指引据此分工 |
| N-08 | MAJOR | §4.3.1 / §4.4 | paused(gate) 状态下非 gate 在飞分支的行为未定义：状态机是 Run 级 running⇄paused，DSL 允许 hitl gate 与其他分支并行（如 gate 等待时另一长分支仍在构建）。paused 期间在飞 worker 冻结还是继续？继续则可能产生 series 变化使审批基点漂移（虽有 §4.2.4 stale 机制 fail-closed 兜底，但语义应显式） | 定义 paused 的语义粒度：仅 gate 等待（在飞分支继续）或全 Run 冻结（在飞分支 checkpoint 挂起），并说明与 token 失效链的交互 |
| N-09 | MINOR | §8.3 / §4.2.5 | token 注入 release 节点执行的通道未定义：§8.3 称 broker"输入 ReleasePlan + token"，但 token 由 Approval 服务签发后如何到达 broker——编排层读 Ledger 注入 release 节点的转发载荷？broker 按？§6.1 消息类型未列 token 载体。v0.1 的 `requires: [approval_token]` 机制删除后未补位 | 在 §8.2/§8.3 写明 token 流转路径（建议：Approval 服务写 Ledger，编排层在 release 节点 dispatch 时随 ReleasePlan 一并转发 broker） |
| N-10 | MINOR | §4.2.3 / §4.4 | "gate 结果集"未显式枚举：§4.2.3 校验规则引用"on 值 ∈（status 全集 ∪ gate 结果集 ∪ sys.*）"，但 threshold 的 {pass, fail}、hitl 的 {approved, rejected, gate_expired} 只能从 §4.4 行文推断，未作为封闭集合定义 | §4.4 以表格枚举两类 gate 的 outcome 全集 |
| N-11 | MINOR | §4.2.4 | join"等待同 series 新结果（上游若不会再产出则按超时→fail_safe）"的超时来源未定义——实际由 run_budget 兜底，但未写明，读者会寻找不存在的 join timeout 参数 | 注明 join 等待无独立超时、以 run_budget 为界（或增加 join_timeout 配置项） |
| N-12 | MINOR | §4.2.1 / §4.2.6 | route 的 `loop: ut_fix_loop` 标注与 loops 声明的 `edges: [{from: ut, to: compiler}]` 是冗余双源，二者不一致时（改了一处忘改另一处）的校验规则未列入 §4.2.6 规则清单 | §4.2.6 增加"route 的 loop 标注与 loops.edges 必须一致"校验，或消除冗余（仅从 loops.edges 推导） |
| N-13 | N | §3 | approval token 定义含"过期时间"，但过期与"series 变化失效/单次核销"的优先关系及过期后的 outcome（走 sys.*? gate_expired?）未写明，需读者自行推断 | §8.3 补一句过期 token 核销失败的 outcome 归类 |

## 5. CLARIFY 清单

1. D12 理由"旧 checkpoint 在新图上恢复是官方明示的兼容性风险"——请给出 LangGraph 官方出处（release policy / checkpoint 兼容性文档）。我核实到官方 semver 承诺（[1.0 公告](https://www.langchain.com/blog/langchain-langgraph-1dot0)）仅覆盖 API，未覆盖 checkpoint 格式跨图/跨版本兼容性，故"官方明示"一语需引证；不影响 D12 决策本身（拒绝恢复是安全默认）。
2. §8.2 Review CLI 认证为"本机用户 + 服务端配置的 reviewer 名单"——是否意味着 Approval 服务仅监听 loopback、远程 reviewer 场景被显式排除？若是，请在 D13 信任模型中写明。
3. §4.5"进入即计数"+"任一预算触顶 → 强制路由 fail_safe"：max_rounds: 2 是允许 2 次回流（第 3 次进入前拦截）还是第 2 次进入即触顶？边界判定（< vs ≤）请写明——示例中 ut_fix_loop 只允许 1 次还是 2 次修复轮直接影响验收。
4. D12 execution manifest 含"provider 配置 digest"——粒度是什么？内网 LLM 端点变更或密钥轮换会导致全部 paused Run 不可恢复转_safe，若属有意为之请说明运维预期。

## 6. 一句话总结

v0.2 的处置质量与新增设计（Ledger 单一权威源、broker 隔离、两阶段 side_effect、环级预算）已达到可 freeze 的架构成熟度，距 draft freeze 只差：修复 N-01 示例死锁（BLOCKER）并补齐 join 聚合/terminal 成功语义（N-02/N-03），其余 MAJOR 均为可在 01 编写前以增补条款方式闭环的接缝问题。

上面是Kimi Code的review意见

CodingSystem Framework HLD v0.2 复审报告（评审员：Claude Code）
1. 总裁决：NO-GO（1 项 BLOCKER + 3 项 MAJOR；均为局部修订量级，无架构性返工，修复后可 freeze）
v0.2 的修订质量高：第一轮的系统性缺口（安全组件归属、token 时序、幂等语义、权威事实源、DSL 语义）已被正面解决，且多处采用了强于原建议的方案（release 保留节点消解"CI 类判定"、Ledger 单库事务）。NO-GO 仅因新写的 join 语义存在一处两种解读结果相反（死锁 vs 通过）的矛盾，且矛盾体现在被声明为"校验器验收用例"的规范性示例中。

2. 任务 A：本方第一轮 issue 处置核验
第一轮编号	结论	说明
I-01 (BLOCKER)	接受关闭	Approval 服务+Review CLI+Broker 纳入交付：§1.1、§2.1 L4'、§8.2/8.3、§10、§13 P2 齐备
I-02 (BLOCKER)	接受关闭	§4.2.2 显式节点实例废除点号寻址；§4.2.4 join/取消语义已立。新写语义自身的缺陷另立新 issue（N-01），不属重开
I-03 (MAJOR)	接受关闭	§6.3 + §4.2.6 hard-required 静态拦截，检查恒真问题消除
I-04 (MAJOR)	接受关闭	§4.2 loops 环级预算 + §4.5 计数口径；agent 内部限制与编排预算已分离
I-05 (MAJOR)	接受关闭	§4.2.3 status 全集注册 + default_route 必填
I-06 (MAJOR)	接受关闭	§4.3.2 sys.* taxonomy + retry + default_route
I-07 (MAJOR)	接受关闭	§8.3 核销绑定 task_id、恢复视为有效；恢复死锁消除
I-08 (MAJOR)	接受关闭	D7 来源出生标注 + 禁降级 + 中心授权 + R8 残余登记
I-09 (MAJOR)	接受关闭	§4.2.5 等效方案强于原建议：凭据只在 broker，判定问题整体消失
I-10 (MAJOR)	接受关闭	§6.5 target_spec
I-11 (MAJOR)	接受关闭	D11 + §7.6.3。"单活跃 Run"自身的语义留白另立 N-03
I-12–I-22 (MINOR/NIT)	全部接受关闭	逐条核对落点属实（保留节点/§4.3.1 cancel/R9/引用修正/§6.5 定案/PEP 440/JSONL+保留策略/D1 闭包锁定/§4.1 硬前提改写/bench_gate/§7.2 缓存键）。唯 I-15 相关新增一处路径笔误（N-09）
C1–C6	接受	均已定案回答；C1 的效力边界（FakeLLM 定稿 + R5 独立上线 gate）已在 G6 明示
他方处置抽查未发现明显错误；Codex I-07/I-08 的两处裁剪即任务 B 仲裁点，见下。

3. 任务 B：仲裁点判断
B1（N7/D13 不做完整沙箱）：接受。 威胁模型与部署形态（内网单机、单操作员、认证调用方）匹配，凭据隔离未被豁免（broker 进程 + 能力句柄注入），残余风险 R7 有检测信号、owner 与失效前置条件（"接入不受信来源必须先补沙箱"）。全沙箱在此威胁模型下确属范围膨胀。一点边界措辞建议（不影响接受）：受信假设应显式覆盖"调用方认证 ≠ 内容可信"——patch 是 LLM 生成物，间接提示注入可使受信来源产出恶意构建脚本，此路径宜写进 R7 的假设边界（N-12）。

B2（D12 拒绝恢复不迁移）：接受。 依据两点：(a) 单活跃 Run 下"升级前等 Run 关闭"即天然 drain，拒绝恢复仅是保底路径，实际触发面很小；(b) 官方文档明示 interrupted thread 不支持节点改名/删除的拓扑变更、state 类型不兼容变更有风险（见文末 Sources），逐类推理"哪些变更可安全迁移"的成本与出错面远大于一律拒绝。注意：D12 理由句的措辞比官方文档略强（官方实际支持相当多迁移场景），建议改为引用具体不支持场景，决策不变（N-10）。

B3（DSL v1 语义闭合）：原则接受，一处未闭合。 寻址、路由穷尽性、环预算与计数口径、保留节点、合法子集定义、fail-closed threshold 均已闭合到可实现、可校验。唯 join 的触发机制存在定义矛盾（N-01，BLOCKER）：这是本轮 NO-GO 的唯一原因，修复为局部性（一条语义定案 + 一条校验规则 + 示例修正）。

4. 新 issue 清单
编号	等级	定位	问题描述	修改建议
N-01	BLOCKER	§4.2.1/§4.2.4/§4.2.6	join 触发机制两种解读结果相反且示例不自洽：pre_final_review 的 wait_for: [ut, bench_gate, review_static] 中 ut 没有任何路由指向该 join（ut_passed 路由至 benchmark）。若"到达"= 路由送达 join，则 ut 永不到达 → 旗舰示例死锁至 run_budget 超时；若"到达"= 观察节点完成，则 bench_gate/review_static 指向 join 的两条路由沦为冗余装饰，且"ut 以哪些 outcome 完成才算到达"（ut_fix_patch_ready 算吗？）未定义。§4.2.6 校验规则清单也无 wait_for 与入边一致性检查，故该示例可能通过校验后在运行时死锁——与 §4.2.1"本示例即校验器验收用例"直接冲突	定案：join 触发 = join 入边路由到达事件；校验器强制 wait_for 集合 ≡ 指向该 join 的路由源集合；示例 wait_for 修正为 [bench_gate, review_static]（ut 通过由 bench_gate 传递闭包蕴含）；同时定义计入 join 的 outcome 集合规则
N-02	MAJOR	§5.1.2/§5.2/§5.3 vs §7.5	worker 侧持久化路径与单写者矛盾：§7.5 声明 Ledger 写者唯一为编排进程（括号仅列 approval/broker 经 API 写入），但 side_effect 两阶段状态机（§5.2，claimed 须在效应执行前持久化）与 SDK trace 埋点（§5.3）均运行在 worker 子进程内。另 §7.5 "task 完成 = 结果、artifact 索引、幂等记录同一事务提交"与 §5.2 claimed(intent) 先行落盘矛盾——若幂等记录延迟到 task 完成才提交，崩溃时无 intent 记录，probe 恢复协议失效，P1 故障注入 gate 无从通过	定案 worker 经编排进程同步 IPC API 写 Ledger（claimed 收到 ack 后方可启动效应），§7.5 括号补入 worker；明确"task 完成事务"仅涵盖最终结果+索引+幂等终态，intent/running 记录随执行即时提交
N-03	MAJOR	D11/§6.5/§4.4	"单活跃 Run"语义未闭合：paused(gate) 是否占据活跃槽未定——R9 承认 review 可挂数日，若占槽则人工 review 期间全系统吞吐为零，若不占槽则"多 paused + 一 running"的并存规则需要定义；且 create_run 在已有活跃 Run 时的行为（拒绝/排队）在 Skill 协议中未定义，Codex 无从实现	定案：建议 paused 不占活跃槽（多 Run 可同时 paused，running 仅一个，resume 时若有 running 则排队）；create_run busy 语义（建议 FIFO 排队 + 返回队列位置）写入 §6.5
N-04	MAJOR	§8.2 vs §4.2.1	approve 时序与"发布目标"数据来源矛盾：§8.2 规定 approve 时由 Approval 服务生成含发布目标的 release manifest 并签发绑定其 digest 的 token，但示例中确定发布内容的 ci_plan 在 human_review 之后执行——approve 时刻发布目标从何而来未定义；ReleasePlan 与 manifest 不一致仅有"重核失败"一条运行时兜底	定案发布目标来源：由 release 节点/pipeline 配置静态声明（进 pipeline_digest），approve 时从配置读取；broker 校验 ReleasePlan 的目标 ⊆ manifest 声明的目标。或调整规范示例为 ci_plan 前置于 human_review 并说明取舍
N-05	MINOR	§3/§6.4	series_id 签发权未定：若允许 Agent 自行声明/复用 series_id，join/gate 的陈旧性保护可被业务 bug 静默失效（token 侧有 tree_digest 重核兜底，但正确性机制裸奔）	定案：series 变更须经 SDK 原子 API 向框架登记（Ledger 签发新 series_id 并计算 tree_digest），HandoffResult 中的 series_id 由框架校验非自造
N-06	MINOR	§7.1	密级"格"的偏序/join 未定义：{public, internal_code, build_log, secret} 中 internal_code 与 build_log 是否可比？"聚合取最高"依赖明确的 join 运算	在 01 给出全序（如 secret > internal_code > build_log > public）或偏序 + join 表；HLD 一句话声明选择
N-07	MINOR	§4.2.4	join 等待同 series 新结果的"按超时→fail_safe"未定义计时器：joins 声明无 timeout 字段，目前仅 run_budget（1440min）兜底，粒度过粗	joins 增加可选 timeout_min（缺省继承 run_budget），计时口径与 §4.5 对齐（排除 paused）
N-08	MINOR	§4.3.1/§6.5	snapshot_pinned 后等待 submit_patch 阶段无 TTL：Coding Agent 永不提交则 Run 悬挂占据活跃槽；run_budget 是否在该阶段计时未说明	增加 awaiting-patch TTL（超时 closed(cancelled)）并明确 run_budget 起算点
N-09	NIT	文档头/§15 A3	引用路径 docs/reviews/HLD_v0.1_review_disposition.md 与实际 docs/review/ 不符	修正路径
N-10	NIT	D12 理由句	"旧 checkpoint 在新图上恢复是官方明示的兼容性风险"措辞强于官方文档——官方明示的不兼容仅限 interrupted thread 的节点改名/删除与 state 类型不兼容变更，其余迁移场景官方声明支持（依据见 Sources）	理由句改为引用具体不支持场景 + "拒绝逐类推理"的工程决策；结论不变
N-11	NIT	§4.2.4	被新 series 取代的在飞任务（如 S1 的 review_static 仍在跑）策略未声明：跑完丢弃 vs 主动取消	显式声明（建议 MVP 跑完丢弃，stale 标记既有；避免取消路径复杂化）
N-12	NIT	§8.1/R7	受信假设边界建议补一句：调用方认证 ≠ 内容可信，Coding Agent 上游提示/语料不受控（间接提示注入产出恶意构建脚本）属 R7 覆盖路径	R7 假设边界补充该句
5. CLARIFY 清单
CL-1：broker 对 token 既查 Ledger 核销记录又验 HMAC 签名（§8.2/8.3），权威判据是哪个（建议明示：Ledger 记录为准，签名防伪为辅）？共享密钥的存放与轮换需一句定案（MVP 可从简）。
CL-2：reviewer"本机用户"认证的具体机制（unix socket peer credential / 登录会话）落在 01 还是 09？
CL-3：agent 制品 digest 与 exec manifest 的校验时点仅有加载时（§11.3）与恢复时（D12），task dispatch 时是否复核（防运行中原地升级插件）？
CL-4：retry.on 是否允许包含 sys.timeout（§4.3.2 示例仅 crash/error）？
6. 一句话总结
距 draft freeze 差四个局部定案——join 触发机制（N-01，唯一 BLOCKER）、worker 侧 Ledger 写路径（N-02）、单活跃 Run 忙时语义（N-03）、发布目标数据来源（N-04）——均无架构性返工，修复后本方可转 GO。

Sources（本轮外部断言核实）：

Managing State Schema Changes Across Deployment Versions（官方支持文档：interrupted thread 拓扑变更限制与 state schema 兼容性）
第一轮已核实并沿用：LangGraph Interrupts 官方文档（恢复时节点重执行）、1.0 稳定承诺、langgraph-prebuilt 破坏性变更 issue #6363

上面是Claude Code的review意见

## 1. 总裁决：NO-GO

v0.2 修复幅度很大，但仍有未关闭的第一轮 BLOCKER，并新增 4 条 BLOCKER，尚不满足 draft freeze 标准。

## 2. 任务 A：本方第一轮处置核验

| 本方第一轮编号 | 结论 | 不接受的理由与定位 |
|---|---|---|
| I-01 | 不接受 | [§4.2.1、§4.2.4](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:146)：join 声明等待 `ut`，但 `ut_passed` 只路由到 `benchmark`，从未“到达” join；若 join 自动观察节点完成，则另外两条显式 `to: join` 又显得冗余。join 超时也没有配置或默认值。旗舰示例仍无法唯一编译。 |
| I-02 | 不接受 | [§4.2.6、§6.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:203)：hard-required 和 threshold 只检查来源节点“存在”，没有检查来源在控制流上先于并支配消费者。反例：entry 同时 fan-out 到 compiler 与 hard-require BuildReport 的 benchmark，节点存在但 benchmark 会提前执行。 |
| I-03 | 接受关闭 | — |
| I-04 | 不接受 | [§4.2.1、§8.2–8.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:148)：当前顺序为 `human_review → ci_plan → release`，approval 在最终 ReleasePlan 产生前签发；此外业务侧 publisher adapter 又进入持凭据的 broker 进程。见新 issue R2-01、R2-03。 |
| I-05 | 不接受 | [§5.2](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:264)：`idem_key` 包含 `attempt`，同一逻辑副作用在 retry 时换键，无法命中前一 attempt 的 running/unknown 记录，重新打开重复执行窗口；`probe()` 成功后如何恢复原调用结果/artifact 也未规定。LangGraph 重新执行节点的事实由[官方 interrupts 文档](https://docs.langchain.com/oss/python/langgraph/interrupts)确认。 |
| I-06 | 不接受 | [D6、§7.5](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:314)：SQLite 事务只能覆盖 artifact 索引，不能覆盖文件系统 blob；文档未规定 blob 的 temp-write/fsync/rename/index 顺序、孤儿回收和 dangling-index 恢复，原崩溃窗口仍未闭合。 |
| I-07 | 接受关闭 | — |
| I-08 | 接受关闭 | — |
| I-09 | 不接受 | [§7.1](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:300)：声明 `{public, internal_code, build_log, secret}`“构成格”但未给偏序/join 表；`internal_code` 与 `build_log` 谁更高、两者聚合结果是什么无法实现。 |
| I-10 | 不接受 | [§5.1.2](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:259)：SIGKILL worker 不会自动杀死 GBS 等孙进程；构建仍可能继续占资源或修改 worktree，因此 hard timeout/cancel 尚未物理闭合。需规定独立 process group/session 与递归清理。 |
| I-11 | 不接受 | [§4.5](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:235)：`max_rounds: 2` 在入环 `+1` 后，是计数达到 2 时拒绝第二轮，还是下一次将超过 2 时拒绝第三轮，仍不明确。 |
| I-12 | 接受关闭 | — |
| I-13 | 接受关闭 | — |
| I-14 | 接受关闭 | — |
| I-15 | 接受关闭 | — |
| I-16 | 接受关闭 | — |
| I-17 | 接受关闭 | — |
| I-18 | 接受关闭 | — |
| I-19 | 接受关闭 | — |
| I-20 | 接受关闭 | — |
| I-21 | 接受关闭 | — |
| I-22 | 接受关闭 | — |
| I-23 | 接受关闭 | — |
| I-24 | 接受关闭 | — |
| I-25 | 不接受 | [文档头、A3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:6)：仍引用不存在的 `docs/reviews/...`；仓库实际路径为 `docs/review/...`，与“全文修正并 grep 核验”的处置结论不符。 |

## 3. 任务 B：仲裁点攻击

1. **N7/D13：接受。** 在“内网单机、单操作员、Coding Agent 身份受控”前提下，把完整容器沙箱列为 Non-goal，并明确接受源码被恶意构建脚本外传的残余风险，是可以成立的范围裁剪。认证不等于内容无害，但只要风险 Owner 明确接受，该裁剪不阻塞 freeze。此接受不豁免 broker/control-plane 的 OS 与 IPC 权限隔离，见 R2-03/R2-04。

2. **D12：接受。** LangGraph 会将最新部署的 graph 应用于已有 checkpoint，[官方文档](https://docs.langchain.com/oss/python/langgraph/backward-compatibility)明确说明了这一点。MVP 在 execution manifest 不匹配时拒绝恢复，比尝试自动迁移更安全、更容易验证；但必须补齐无需旧 graph 的收尾与副作用对账，见 R2-05。

3. **DSL v1：反对“已经闭合”。** 显式节点、保留节点、环预算和路由全集已经成形，但 join 到达语义、hard-required 的因果先后、`terminal: true` 结果语义仍未闭合；当前全量示例自身存在 `ut` 不到达 join 的问题。

## 4. 新 issue 清单

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| R2-01 | BLOCKER | [§4.2.1、§8.2–8.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:148) | （置信度 10/10）human_review 在 `ci_plan` 之前；Approval 服务却在 approve 时生成并签署含发布目标的 ReleaseManifest。最终 ReleasePlan 尚不存在，reviewer 无法确认自己批准的正是 broker 将执行的计划。CI Agent 之后改变 target/action 时，文档没有定义 broker 是拒绝、忽略还是采用。 | 调整为 `ci_plan → human_review → release`；CLI 向 reviewer 展示由 ReleasePlan 规范化得到的最终 ReleaseManifest，并签署其 digest。静态校验禁止 hitl 后再出现任何可改变 release manifest 的节点。 |
| R2-02 | BLOCKER | [§4.4、§8.2、§8.4](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:231) | （置信度 10/10）approval token 在 approve 后、broker 执行前必须跨越 ci_plan 和可能的进程重启，但 §8.4 又规定 token 只持久化指纹。若不持久化，崩溃后 token 丢失；若放入 graph state/checkpoint，则违反脱敏规则。 | 定案 crash-safe custody：推荐 Ledger 保存 `token_id + authorization record`，broker 通过特权 RPC 原子消费授权，bearer 不进入 graph/checkpoint；如坚持签名 token，则规定可确定性重签/安全存储、key_id、重启恢复和失效流程。 |
| R2-03 | BLOCKER | [§2.3、§8.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:94) | （置信度 10/10）真实 gerrit/github adapter 由业务侧开发，却“运行于 broker 进程内”；Python 插件与 broker 同进程即可读取凭据或绕过 manifest 校验，重新破坏 D8 的物理边界。“插件准入”未定义为可信计算基的一部分。 | 明确 publisher adapter 的信任级别。推荐 adapter 在无凭据子进程中生成受限操作，由框架 broker 执行最终 credential-bearing primitive；否则真实 adapter 必须由框架交付并纳入安全审计、制品 attestation 和版本 pin。 |
| R2-04 | BLOCKER | [§7.5、§8.2–8.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:314) | （置信度 9/10）Ledger 声明仅编排进程可写，但 Approval/Broker 是独立进程，正文又分别说它们“写 Ledger”“Ledger 事务内核销”。内部 API 没有传输、服务身份、授权、幂等或事务边界；无沙箱 worker 在同机上可能调用该特权 API。approval commit 成功但 resume 触发丢失时也没有 outbox 恢复。 | 定义私有 control-plane RPC：独立 OS 用户、Unix socket 权限/peer credential 或等效强认证；worker 不可访问。由编排进程以单个幂等命令原子提交 decision、token record、gate outcome 与 resume outbox；broker consume 同样使用有 task_id 的原子命令。 |
| R2-05 | MAJOR | [D12、§3 fail_safe、§4.3.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:91) | （置信度 9/10）execution manifest 不匹配时拒绝启动旧 graph，却又要求生成只能由 `fail_safe` 保留节点产生的 FeedbackReport；同时直接关闭会跳过对 `claimed/running` 副作用的 probe，对外部真实状态形成错误审计。 | 定义不依赖 EnginePort 的 ledger-native administrative finalize 路径：先对账全部 unknown side effects、记录无法判定项，再生成版本漂移 FeedbackReport 并关闭 Run；不要声称执行了无法恢复的旧 `fail_safe` 节点。 |
| R2-06 | MAJOR | [D5、D12、§4.3.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:84) | （置信度 8/10）execution manifest 只明确在“进程重启后”校验。Run 运行期间若 provider 配置、Agent wheel 或安全策略文件被替换，后续 task 可使用新内容，而 token 仍绑定旧 digest。 | 将相关配置/制品复制到 Run 级不可变位置，或在每次 task dispatch、approval 与 broker publish 前重新核验实际 digest；不匹配立即进入 administrative fail-safe。 |
| R2-07 | MAJOR | [D11、§4.4、§7.6.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:90) | （置信度 9/10）“单活跃 Run”没有说明 paused Run 是否占用唯一槽位，而 gate TTL 默认无。若占用，reviewer 长期不操作即可阻塞所有后续 Run；若不占用，resume 时的排队与资源获取未定义。 | 将 active 精确定义为“正在执行/持有 worker 资源”；paused Run 释放执行槽，resume 进入 FIFO 队列重新获取。若坚持 paused 也占槽，则 gate 必须有有限默认 TTL 或显式运维解锁规则。 |
| R2-08 | MAJOR | [§4.2.2–4.2.3](/home/linhao/Toolchain/development/CodingSystem/docs/00_Framework_HLD_v0.2.md:187) | （置信度 9/10）`terminal: true` 未定义哪些业务 status 关闭为 succeeded，也未说明 sys.*、未匹配 status 与全局 default_route 的优先级；broker release 成功/失败的 outcome 集同样未列出。不同实现会产生不同终态。 | 在 DSL v1 定义 terminal 节点的 `terminal_on` 或等价明确规则：成功 status 集、系统错误处理、default_route 优先级；为 release 保留节点定义固定 outcome 集和终态映射。 |

## 5. CLARIFY 清单

无。需要澄清的关键点均已达到 issue 门槛。

## 6. 一句话总结

距离 draft freeze 还差：修正 DSL join/依赖语义，重新闭合 approval→ReleasePlan→broker 的授权与 token 恢复链，稳定 side-effect 身份及 Artifact/Ledger 提交协议，并封死 broker 特权 IPC 与 publisher adapter 的绕过路径。

上面是Codex的review意见
