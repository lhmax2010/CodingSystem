D12 的外部事实断言核实通过：[LangGraph 官方 backward-compatibility 文档](https://docs.langchain.com/oss/python/langgraph/backward-compatibility)明确"the only topology change that can break an interrupted thread is renaming or removing a node"，与 D12 改写后的理由句一致，CL-1 处置属实。以下为第三轮评审结论。

---

# 复审报告：00_Framework_HLD_v0.3（Kimi 方）

## 1. 总裁决：**GO**

第二轮本方 13 条 issue + 4 条 CLARIFY 全部妥善关闭；三个仲裁关注点独立攻击后均接受；增量审查未发现 BLOCKER/MAJOR，仅存 8 条 MINOR/NIT 级接缝瑕疵，均不位于关键路径决策上，适合作为 freeze 勘误或在 01_Contract_Spec 编写时并入。这是三轮来文档首次达到"Codex 可直接开发"标准。

## 2. 任务 A：本方第二轮 issue 处置核验

| 编号 | 结论 | 说明 |
|------|------|------|
| N-01 (BLOCKER) | 接受关闭 | §4.2.4"到达=入边路由送达"+ wait_for ≡ 入边源集合（校验强制_for 已改 [bench_gate, review_static]，逐边复核示例路由/join/loop 引用现均自洽 |
| N-02 | 接受关闭 | §4.2.4 join_inputs 固定形态，schema 归 [01] |
| N-03 | 接受关闭 | §4.2.2 terminal 节点 success_on 映射 + §4.2.5 release outcome 集固定，子集成功语义闭合 |
| N-04 | 接受关闭 | §7.5 直写者收敛编排进程 + §8.5 RPC；§8.2"权威判据唯一 = Ledger 记录，无签名/HMAC 第二通道"——HMAC 已按质疑移除 |
| N-05 | 接受关闭 | §5.1.2 心跳丢失自杀 + 恢复时按 Ledger 登记 pgid reap 孤儿进程组后再重放 |
| N-06 | 接受关闭 | §5.2 claimed ack 前置、RPC 失败 fail-closed、intent/running 即时提交与完成事务边界均写明 |
| N-07 | 接受关闭 | §8.3 官方 gerrit/github adapter 框架交付、broker 进程=可信计算基；§5.1.1 能力句柄显式排除发布通道——两套集成点分裂消除，方案强于原建议 |
| N-08 | 接受关闭 | § 等待节点级 + D11 执行槽语义，paused 行为有明确定义 |
| N-09 | 接受关闭 | §8.3 输入 = ReleasePlan + token_id（授权引用经编排层转发） |
| N-10 | 接受关闭 | §4.4 gate outcome 封闭枚举表 |
| N-11 | 接受关闭 | joins.timeout_min，缺省以 run_budget 为界 |
| N-12 | 接受关闭 | routes 移除 loop 标注，环由 loops.edges 唯一定义——消除冗余优于双源校验，同意 |
| N-13 | 接受关闭 | §8.2/§8.3 过期授权消费 → release_failed(authorization_expired) |
| CL-1 | 接受关闭 | D12 理由句已限定到官方明示的具体场景，经核实与[官方文档](https://docs.langchain.com/oss/python/langgraph/backward-compatibility)一致 |
| CL-2 | 接受关闭 | §8.2 仅本机 Unix socket，远程 reviewer 显式不支持 |
| CL-3 | 接受关闭 | §4.5"N 次通过、第 N+1 次拦截"边界定案 |
| CL-4 | 接受关闭 | D12 provider 配置 digest 仅含策略语义，端点/凭据轮换不影响恢复 |

第一轮已关闭条目抽查无回归（一处术语残留见 M-01，不构成重开）。

## 3. 任务 B：仲裁关注点

**B-1（审批链重排后的授权-执行时序）：接受。** 我针对四条攻击路径逐一推演，均收敛到安全侧：①审批与 gate_expired 竞态——单命令原子事务（§8.5）消除中间态，Run 已关闭则授权随"Run 关闭自动失效"（§8.2）作废；②approve 后并行在飞分支造成 series 漂移——授权 digest 绑定 tree_digest，series 变化即失效，broker 消费时-closed 为 release_failed；③授权不落地崩溃——授权即 Ledger 记录、无 bearer 进图状态/checkpoint，恢复后权威状态完整；④worker/业务代码伪造消费——token_id 仅引用、核销命令所在 socket 对 worker 文件权限隔离（§8.5）。"approved 直达 release"的静态强制（§4.2.5）消除了审批与执行之间的 manifest 可变窗口，这是本轮最关键的一处结构性收敛。时序闭合，无绕过。

**B-2（§8.5 RPC 权限模型承载 D8）：接受。** 分 socket + 分 OS 用户 + peer credential + worker 不可达特权命令 + 单命令原子事务 + resume outbox，与 D8"凭据仅 broker 进程、授权原子单次核销"的物理强制声明匹配；§11.3 已配 RPC 权限隔离与双消费测试类别。两处加固级观察记为 M-05/M-06（命令作用域、setuid 前提），不撼动模型本身。

**B-3（DSL v1 语义闭合）：接受。** 逐条复核：示例即验收用例现已自洽（wait_for ≡ 入边源、环边与路由定义、approved 直达、default_route 兜底）；触发、聚合、超时、终态映射、穷尽性、支配性、计数边界全部有唯一解释；合法子集定义（§4.2.6）规则清单完备且可静态判定。残留仅一处未声明语义（非 join 汇聚的多路到达，M-04），为 MINOR 级，可宣布闭合。

## 4. 新 issue 清单

| # | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---||-------------|
| M-01 | MINOR | §3 vs §8.2/§8.3 | 术语表"Approval 服务：接受 reviewer 决定（approve/reject）、**签发/核销** approval token"残留 v0.2 措辞——核销已唯一归属 broker（§8.2"无第二通道"、§8.3 原子核销） | §3 该行改为"签发授权记录、触发 gate resume"，核销字样删去 |
| M-02 | MINOR | §4.3.1 vs §4.3.3 | FeedbackReport 生成者两说：§4.3.1"reason=fail_safe 时由保留节点生成"，§4.3.3 administrative finalize"不经引擎与保留节点……生成注明版本漂移的 FeedbackReport" | §4.3.1 补例外句：administrative finalize 路径由 ledger 层直接生成（或§4.3.3 注明这是对§4.3.1 的显式例外） |
| M-03 | MINOR | §4.2.5 / §4.2.6 | "hitl 的 approved 出边必须直达 release"的量化范围未定义：含多个 hitl gate 的 pipeline（如早期另有一个与发布无关的人工 gate），按字面全部 hitl 的 approved 都被强制直达 release，属过度约束；按意图应只约束"在 release 可达路径上的 hitl" | 改为存在到 release 路径的 hitl gate，其 approved 出边必须直达 release" |
| M-04 | MINOR | §4.2.4 | 非 join 汇聚语义未声明：多条路由边指向同一普通节点 X（非 join: 目标）时，X 是每次到达各触发一个 task 还是有其他合并语义？可从 join 的存在反推"每到达一触发"，但全文未写，校验器对此形态是否告警也未定 | §4.2.4 增一句：普通节点的每次边送达独立触发一次 task 执行；如需汇合必须显式 join |
| M-05 | MINOR | §8.5 | worker socket 命令未声明按调用方身份限定作用域：worker 内运行的半可信构建脚本（R7 已承认）可为任意 idem_key 提交 claimed/succeeded，污染其他节点的幂等记录（危害被 Blob 协议 dangling=sys.error 兜底大半，故不定 MAJOR） | §8.5 增"worker 命令的作用域限定为该 worker 所属 run_id/task_id，越域请求拒绝并记审计" |
| M-06 | MINOR | §8.5 / §5.1.2 | worker 以不同 OS 用户运行的前提未写明实现支点：编排进程 spawn 他用户子进程需 root 或 setuid launcher，这本身扩大 TCB，与"编排进程最小权限"的关系未交代 | 写明权限机制要求（如专用 setuid launcher 属可信计算基） |
| M-07 | MINOR | §8.3 / §8.5 | 编排→broker 方向的发布请求通道未定义：§8.5 只覆盖 broker→编排（核销 RPC），broker 接收 release 转发请求的监听形态、访问控制、token_id 不可猜测性均无规定 | §8.5 补 broker 入向通道条款（本机 socket + peer credential + token_id 高熵随机） |
| M-08 | MINOR | §4.2.4 / §7.6.2 | "series_id 由 SDK 原子 API 向框架登记签发（Ledger 计算 tree_digest）"：tree_digest 按 §7.6.2 定义依赖"应用后 tree hash"，计算主体与场所（登记时由编排层在专用 worktree 实际 apply，还是纯内容算法）未指明；"Ledger 计算"与 Ledger=SQLite 事实措辞不符 | 明确 tree_digest 在 series 登记时的计算主体与方式（建议：规范算法纯计算，无需 worktree），修正"Ledger 计算"措辞 |
| M-09 | NIT | §8.2 | ReleaseManifest"规范化"算法未标 `[01]`，而 approval 与 broker 两个进程对同一 ReleasePlan 的 digest 一致性完全依赖它 | 给规范化算法补 `[01]` 标注 |
| M-10 | NIT | §4.3.1 | 状态图中 `snapshot_pinned` 是迁移标注，正文 TTL 句却将其作为等待 submit_patch 的状态使用；awaiting-patch 未作为图中 | 状态图补 awaiting-patch 状态或统一措辞 |

## 5. CLARIFY 清单

1. §7.1 密级全序中 `build_log < internal_code` 的依据：gbs 编译错误输出常内联源码行，将日志整标 build_log 是否低估密级？EvidencePacket 聚合取最高能兜住组装场景，但请确认"日志摘录出生标注"时是否要求摘录器按内容升级密级。
2. §4.2.5：release_failed 出边是否允许配置重试（授权已核销，重试必然 release_failed）？若属无意义配置，校验器是否应禁止 release 出边入环？

## 6. 一句话总结

可以 freeze——三个仲裁点全部闭合、本方前两轮 43 条问题无一遗留，建议将 M-01～M-10 作为 freeze 勘误清单随 v0.3 定稿，并在 01_Contract_Spec 编写时一并落掉。

上面是Kimi Code的review意见

CodingSystem Framework HLD v0.3 第三轮复审报告（评审员：Claude Code）
1. 总裁决：NO-GO（1 项 BLOCKER——v0.3 新修改自身引入，修复为单点定义级；其余均为小对齐项，修复后本方即 GO）
先说结论性评价：三个仲裁关注点本方全部接受，上两轮遗留问题全部确认关闭，v0.3 的修订质量延续了前两轮水准。唯一的实质缺陷出在本轮 idem_key 去 attempt 的修改上——该修改正确解决了"重试须命中前一 attempt 记录"的问题，但把效应身份锚定在 task 级 input_digest 上，在非决定论重执行（LLM 在环）下产生键碰撞与错误复用，直接动摇 §5.2/G4 的恢复正确性承诺。

2. 任务 A：本方第二轮 issue 处置核验
第二轮编号	结论	说明
N-01 (BLOCKER)	接受关闭	§4.2.4 "到达=入边路由送达" + wait_for ≡ 入边源集合（校验强制）；示例 wait_for 改 [bench_gate, review_static]，与路由源一致；outcome 计入问题因"仅路由送达算到达"而结构性消解
N-02 (MAJOR)	接受关闭	§7.5 直写者收敛 + §8.5 RPC；§5.2 claimed ack 前置、RPC 失败 fail-closed、intent/running 即时提交与完成事务边界划清——v0.2 的两处矛盾均消除
N-03 (MAJOR)	接受关闭	D11 单执行 Run 语义完整（paused 释放槽、多 paused 并存、FIFO）；§6.5 忙时受理入队返回位置；§4.4 节点级等待与 Run 级 paused 定义
N-04 (MAJOR)	接受关闭	簇 L 重排后审批对象 = ci_plan 产出 ReleasePlan 规范化的 ReleaseManifest，"发布目标来源"数据流闭合；新时序的攻击见任务 B1
N-05 (MINOR)	接受关闭	§4.2.4 series_id SDK 原子 API 框架签发、不可自造
N-06 (MINOR)	接受关闭	§7.1 密级全序定案（一条配置指引层面的观察移入 CLARIFY，不构成重开）
N-07 (MINOR)	接受关闭	joins.timeout_min，缺省 run_budget
N-08 (MINOR)	接受关闭	§4.3.1 awaiting-patch TTL 24h + run_budget 起算点
N-09 (NIT)	接受关闭	文档头/A3 已改 docs/review/；§10 仓库树注释残留一处 "reviews/"（新 NIT，见 T-05）
N-10 (NIT)	接受关闭	D12 理由句已改为引用具体不支持场景，与既核实的官方文档一致
N-11 (NIT)	接受关闭	§4.2.4 跑完即弃（MVP）
N-12 (NIT)	接受关闭	§8.1 假设边界句（认证≠内容可信/间接提示注入）
CL-1–CL-4	接受	HMAC 移除（权威判据唯一=Ledger）；peer credential 定案；dispatch/审批/发布前 digest 复核；retry.on 含 sys.timeout——均已定案落文
3. 任务 B：三个仲裁关注点
B1（审批链重排后授权-执行时序）：接受。 逐项攻击未找到绕过或竞态：(a) 审批对象与 broker 执行对象同源——reviewer 批准的是 ci_plan 产出 ReleasePlan 的规范化 manifest，broker 核销时以"manifest digest 与 ReleasePlan 规范化结果完全一致"复核（§8.3），ReleasePlan 为内容寻址不可变 artifact，无替换窗口；(b) approved 出边静态直达 release（§4.2.5），审批与执行之间无可变更 manifest 的节点；(c) 审批期间 series 漂移 → 授权自动失效 → 核销 fail-closed 为 release_failed（§8.2/§4.2.5）；(d) approve 为单命令原子事务（决定+授权+outcome+outbox），崩溃后 outbox 重扫补发，重复 resume 被 Ledger 状态机守卫拒绝（§4.3.1 非法转换）；(e) 即使静态校验被绕过，broker CAS 仍需 Approval 服务写入的授权记录，纵深成立。

B2（§8.5 RPC 权限模型承载 D8）：接受。 分 socket/分 OS 用户/peer credential/文件权限使 worker 物理不可达审批与核销命令；单命令单事务消除多步竞态窗口；凭据仅在 broker 进程且官方 adapter 进程内属可信计算基、第三方扩展走无凭据子进程——D8 的"物理强制"表述在单机威胁模型下成立。两条不影响接受的配套项：worker socket 命令枚举与 §7.5 不一致（T-02）、多 OS 用户 provisioning 需落运维文档（CL-C）。

B3（DSL v1 语义闭合）：接受，可宣布闭合。 join 触发机制、wait_for 一致性校验、join_inputs、timeout_min、terminal success_on、release outcome 固定集、hard-required 支配性检查、loop 计数边界（N 次通过、N+1 拦截）均已定案；本方以旗舰示例逐规则复演（环覆盖、路由穷尽、必经 hitl、支配性、无不可达节点）全部通过，含二轮循环后 series 更迭下的 join 陈旧性时序。残余仅 [01] schema 粒度（如链式 join 是否允许，CL-D）。

4. 新 issue 清单
编号	等级	定位	问题描述	修改建议
T-01	BLOCKER	§5.2（v0.3 新改动引入）	idem_key 去 attempt 后效应身份锚定错误：idem_key = hash(run_id, node, loop_round, effect_seq, input_digest) 中 input_digest 明文定义为 TaskInput 级摘要。反例：compiler task attempt 1 中 LLM 产出修复 patch S3 并启动 build（claimed），worker 崩溃；attempt 2 重执行，LLM（非决定论）产出不同 patch S3'，其 build 的 idem_key 与 attempt 1 完全同键（TaskInput 未变、effect_seq 同为首个 build）→ probe 命中 S3 的 worktree/产物 → 复用旧结果，HandoffResult 报 series S3' 而产物实为 S3，下游 UT/发布链拿到错配二进制。同一机制也覆盖 §4.1 声明的"恢复即节点重执行"路径——这不是重试边角，而是 P1 崩溃恢复主路径的正确性缺陷；§4.3.2"timeout 重试的重复副作用由幂等层覆盖"的承诺同被架空。另 effect_seq 全文仅出现一次、无定义	将 idem_key 的输入分量改为效应级参数规范化摘要（side_effect 调用实参 digest，含所操作 series_id/tree_digest 等），effect_seq 定义为同键源冲突时的单调序并入 [01]；或替代方案：声明 LLM 调用结果经记录重放使 task 重执行决定论化——改动面大，建议取前者
T-02	MINOR	§8.5 vs §7.5/§4.2.4	worker socket 命令枚举为"仅 side_effect/trace"，但 §7.5 要求 artifact 索引经 RPC 事务提交、§4.2.4 要求 series_id 经 SDK 原子 API 框架签发——二者均是 worker 发起的写入，字面读下 worker 无通道，系统不可工作	§8.5 将 worker socket 命令集定义为"数据面命令"并显式枚举（side_effect、trace、artifact 索引、series 登记），与 §7.5 对齐；特权命令（审批/核销/resume）不可达的表述保留
T-03	MINOR	§4.3.3	运行期 digest 复核不匹配"同走 administrative finalize"，但 administrative finalize 定义为"不经引擎"的恢复态收尾；活跃引擎场景（dispatch 期发现不匹配、其他分支在飞）缺少前置步骤声明	补一句：运行期触发时先停止引擎执行并按 §5.1.2 终止在飞 worker，再执行 ledger 级收尾
T-04	MINOR	§8.2	Review CLI 的审批呈现内容未声明：reviewer 批准的是 manifest，但据以判断的证据（ReviewReport、带出处的 patch series、各 Report 链）CLI 是否及如何呈现无一句定案——这是 P2 Review CLI 的直接实现输入，也关系 HITL 审查的实质性	§8.2 增加一句：CLI 呈现 manifest 及其关联证据链（ReviewReport、patch series 逐段出处、各阶段 Report 引用），清单细化入 01/07
T-05	NIT	§10	仓库树 docs/ 注释仍写 "reviews/"，与已定案的 docs/review/ 不一致（N-09 残留）	改为 review/
T-06	NIT	§4.2.2 vs §3	release 被称"保留节点"，但 §3 保留节点定义为"无需在 nodes 声明即可作为路由目标"且仅含 fail_safe；release 须在 nodes 声明（§4.2.1）	统一称"特权节点"（§4.2.5 标题用语）
5. CLARIFY 清单
CL-A：密级全序中 build_log < internal_code，但构建日志常内嵌源码片段；建议 07/中心安全配置指引提示两者通常应同组授权（机制不变，属配置指引）。
CL-B：第三方发布扩展的"受限操作描述"与"凭据原语"的 contract 归属（01 还是 07）未标注。
CL-C：§8.5 依赖部署侧为编排/approval/broker/worker 配置不同 OS 用户与文件权限——该 provisioning 要求应在 09 运维章节登记为部署前提。
CL-D：join 的 to 是否允许指向另一 join（链式 join）——[01] schema 请显式允许或禁止。
6. 一句话总结
距 draft freeze 仅差 T-01 一处修复——把 idem_key 的效应身份从 task 级摘要改为效应级参数摘要（v0.3 去 attempt 改动引入的回归，单点定义级修改）——外加三处 MINOR 对齐；T-01 修入后本方即转 GO。

（本轮无新增外部事实断言需核实：D12 理由句与 §4.1 引擎语义均与前两轮已核实的官方文档一致——Interrupts 文档、部署版本兼容性说明。）

上面是Claude Code的review意见

## 1. 总裁决：NO-GO

第二轮遗留的 `I-02`、`I-05` 两项 BLOCKER 仍未完全关闭；本轮另发现 6 项 BLOCKER。v0.3 尚不满足 draft freeze 标准。

## 2. 任务 A：本方第二轮处置核验

| 本方第二轮编号 | 结论 | 不接受的理由与定位 |
|---|---|---|
| 重开 I-01 | 接受关闭 | — |
| 重开 I-02 | 不接受 | §4.2.6（L206）仅对 hard-required 增加支配性检查，threshold 仍只要求指标来源节点“存在”。反例：entry 同时 fan-out 到 benchmark 与 bench_gate；来源存在但不支配 gate，配置仍能通过校验并在运行时必然因缺指标 fail-safe。需对 threshold 指标来源执行同样的支配性及同 series 检查。 |
| 重开 I-04 | 接受关闭 | — |
| 重开 I-05 | 不接受 | §5.2（L274）明确 `idem_key`“不含 attempt”，但 §4.3.2（L228）仍明确写“幂等键含 attempt 序号”，关键恢复语义直接矛盾；若实现遵循后者，重试仍会换键并重新打开重复副作用窗口。 |
| 重开 I-06 | 接受关闭 | — |
| 重开 I-09 | 接受关闭 | — |
| 重开 I-10 | 接受关闭 | — |
| 重开 I-11 | 接受关闭 | — |
| 重开 I-25 | 不接受 | §10（L394）仓库结构仍写 `docs/... reviews/`，实际目录及其余引用均为 `docs/review/`；“全文修正”尚未完成。 |
| R2-01 | 接受关闭 | — |
| R2-02 | 接受关闭 | — |
| R2-03 | 接受关闭 | — |
| R2-04 | 接受关闭 | —；RPC 基础方向已落实，但新增接口自身的问题见 R3-04、R3-06、R3-07。 |
| R2-05 | 接受关闭 | — |
| R2-06 | 不接受 | D12（L91）虽增加 dispatch/审批/发布前复核，却明确把 provider **端点**排除在 digest 外。反例：逻辑 provider 名称和策略不变，但端点由内网服务改为外部服务，复核仍通过，可能将 internal_code 发往新的信任域。凭据值可以排除，端点身份及 TLS/信任策略不能排除。 |
| R2-07 | 接受关闭 | — |
| R2-08 | 接受关闭 | — |

## 3. 任务 B：三个关注点判断

1. **审批链重排：反对宣布闭合。** `ci_plan → human_review → release` 的顺序和审批对象已经正确，但授权记录未明确绑定 Run、gate 实例、ci_plan task 与 series；审批创建时也没有原子校验“待审批 manifest 仍对应当前最新 series”。此外，授权核销后的取消/关闭竞态没有 point-of-no-return 规则。见 R3-01、R3-02。

2. **Control-plane RPC：反对认定足以承载 D8。** 分 socket、OS 用户、peer credential、单事务和 outbox 都是必要基础，但 broker 的入站执行接口及实际多用户部署方式未定义，worker RPC 也只有角色级而非 task 级授权；outbox 只有重扫，没有消费端去重语义。见 R3-04、R3-06、R3-07。

3. **DSL v1：反对宣布语义闭合。** 单次、无循环的 join 示例已经可实现，terminal/release outcome 也已补齐；但 threshold 支配性仍缺失，循环中同 series 的多次到达没有 activation/消费语义，可能跨轮错误汇合或重复触发。见任务 A 的 I-02 与 R3-05。

## 4. 新 issue 清单

| 编号 | 等级 | 定位 | 问题描述 | 具体修改建议 |
|---|---|---|---|---|
| R3-01 | BLOCKER | §3 授权记录；§4.2.4；§4.4；§8.2–§8.3 | （置信度 10/10）授权记录列出的字段只有 `token_id + manifest_digest + 过期时间`，未明确绑定 `run_id`、gate 实例、ci_plan task 或 series。审批事务也未声明校验当前 series。反例：human_review 等待 S1 时，并行分支先产生 S2；之后 reviewer 仍批准 S1。由于授权是在 series 变化后才创建，既有“series 变化使未核销授权失效”无法命中；broker 又只比较授权 digest 与旧 ReleasePlan，两者一致即可发布已被取代的 S1。 | 授权记录至少绑定 `run_id、gate_instance_id、decision_id、ci_plan_task_id、series_id/tree_digest、manifest_digest`。approve 事务必须 CAS 校验 gate 仍 waiting、ReleasePlan 仍为当前版本、series/tree 仍最新；series 推进事务同时撤销待审批项及未核销授权。broker consume 再独立复核全部绑定关系。 |
| R3-02 | BLOCKER | §4.2.4；§4.3.1；§8.2–§8.3 | （置信度 9/10）授权核销与远端发布之间仍有不可原子的窗口。§8.3 规定已核销给同一 task 的授权恢复时继续有效；与此同时 cancel、并行 fail_safe、Run 关闭或 series 更新仍可能发生。反例：broker 核销后、push 前 Run 被取消，broker 仍可能发布；或者远端已发布后分支取消导致 Run 被记为 fail_safe。 | 把 consume 事务定义为明确的发布 point-of-no-return：原子迁移 release task/Run 到 `publishing`；该状态下 cancel、fail_safe、series 更新只能登记 pending，不能先关闭 Run。broker 完成或 probe 对账后再决定最终状态，并规定崩溃恢复及运维可见语义。 |
| R3-03 | BLOCKER | §4.2.4（L200）；§5.2；§7.5；§8.5 | （置信度 10/10）`series_id` 由 worker 通过 SDK API 先向框架登记，但 task 完成事务没有包含 series 更新，worker socket 又只开放 side_effect/trace。反例：worker 登记 S2、Ledger 将其设为最新并使旧报告/授权失效，随后在 HandoffResult 提交前崩溃；系统留下没有成功生产 task 的当前 series。并行生产者从同一父 series 登记时也没有 expected-parent CAS，可能丢 patch。 | worker 只提交 `series candidate + expected_parent_series_id`；由编排进程在一个事务内完成父版本 CAS、artifact/result 提交、series lineage、latest 指针推进以及 gate/授权失效。若需要预分配 ID，预分配不得改变 current series。 |
| R3-04 | BLOCKER | §4.4；§7.5；§8.5 | （置信度 9/10）resume outbox 只定义“信号丢失后重扫补发”，没有消费端幂等。反例：EnginePort 已恢复并调度 release，编排进程在标记 outbox delivered 前崩溃；重启后再次 resume，可能生成第二个 release task。token 会阻止第二次发布，却可能令第二个 task `release_failed`，形成“实际已发布、Run 却 fail-safe”的审计错误。 | 每条 outbox 使用唯一 `decision_id/outbox_id`；gate 状态以 CAS 从 waiting→resolved，EnginePort/调度层持久化 inbox 去重，同一事件重复投递必须返回同一结果且不得重复创建 task。只有 durable dispatch 完成后才能确认 outbox delivered。 |
| R3-05 | BLOCKER | §4.2.4；§4.5 | （置信度 9/10）join 仅以 source 和 series_id 关联到达，没有 activation epoch、到达消费或重复触发规则。DSL 又允许不产生新 series 的有界循环。反例：A fan-out 到 B/C，B 经循环回到 A；`C(round 0)` 与 `B(round 1)` 使用同一 series，可被错误组合；同一 source 重复到达时也未规定 first/last/error，timeout 起算点同样未定义。 | 为每次 fork/循环激活生成持久化 `activation_id`（必要时含 loop-counter vector），到达键为 `(run, join, activation, source)`，每源一次、整组原子消费并最多触发一次；明确重复到达策略和 timeout 起算点。conformance 增加同 series 多轮循环及崩溃重放用例。 |
| R3-06 | BLOCKER | §8.3；§8.5；§10；§13 P2 | （置信度 9/10）§8.5 只定义 Approval/broker/worker → 编排进程的状态写 RPC，没有定义编排进程 → broker 的发布调度接口、调用方身份或 ACL。与此同时 §10 只交付 wheel，没有定义如何创建不同 OS 用户、设置 socket/数据库/凭据权限并启动服务。Codex 可实现多个同用户进程并通过测试，却无法兑现 D8 的“物理强制”。 | 定义完整双向 IPC 与角色权限矩阵：broker dispatch 端点仅接受编排 UID，并绑定 run/task/manifest；规定服务管理器、系统账户、socket mode/ownership、Ledger 权限、broker secret 文件权限及启动顺序。交付安装/部署资产，并用真实 UID 和文件权限做 E2E 隔离测试。 |
| R3-07 | MAJOR | §5.1.2；§8.5 | （置信度 8/10）peer credential 只识别公共 worker OS 用户，没有把请求绑定到具体 run/task。业务 worker 可在自身允许的 socket 上伪造其他 task 的 side_effect 或 trace 请求，破坏 Ledger 因果链；不同 socket 只能做角色隔离，不能做对象级授权。 | 为每个 worker 注入 task-scoped 不可转移能力或已绑定身份的 socket FD；服务端从连接上下文推导 run/task，禁止客户端自由指定归属，并以 Ledger task 租约/状态验证每条命令。增加跨 task 篡改拒绝测试。 |
| R3-08 | MAJOR | §4.3.1；§6.5 | （置信度 10/10）声称状态机“穷尽”，但图中 `snapshot_pinned` 是事件，L222 又把它当成等待 patch 的状态；FIFO `queued` 状态也完全缺失。另一个反例是未提交 patch 的 Run 先进入 FIFO 队首，后续 ready Run 是否被阻塞 24 小时没有定义。 | 显式加入 `awaiting_patch`、`queued` 等状态及全部 guard；只有 submit_patch 成功或 gate resume 后的 ready Run 才进入执行 FIFO，awaiting-patch 不占队列位置、不阻塞 ready Run。 |
| R3-09 | MAJOR | §7.5 Blob 提交协议 | （置信度 8/10）rename 与索引事务之间，合法上传中的 blob 与崩溃孤儿 blob 形态相同。后台 GC 若在该窗口删除“孤儿”，随后索引事务可以提交出 dangling index。现有“定期对账 GC”没有年龄、租约或并发排除规则。 | 为 blob commit 建立 active-upload lease/临时命名空间，GC 只处理超过安全年龄且无 lease 的对象；索引事务提交前再次校验 blob 存在及 digest。增加上传与 GC 并发、各步骤 kill 的测试。 |
| R3-10 | MAJOR | §5.1.2 | （置信度 9/10）hard timeout/cancel 明确 kill 整个进程组，但 heartbeat 丢失只规定 worker“自行退出”。编排进程失联时，worker 退出不会执行文档所要求的进程组 kill 语义，GBS 孙进程可继续运行；“恢复时再 reap”只在编排进程重启后补救。 | 让独立 watchdog/supervisor 在 heartbeat 丢失时终止整个 pgid及登记的外部长进程，而非仅退出 worker；恢复 reaping 前验证进程组归属。增加“编排进程崩溃且 GBS 子进程仍活跃”的故障注入。 |
| R3-11 | MAJOR | §4.3.3；§8.3 | （置信度 10/10）同一种发布前 execution-manifest mismatch 有两个互斥处理：§4.3.3 要求走 administrative finalize，§8.3 却要求返回普通 `release_failed`。并且 §8.3 的文本顺序是先核销授权、再复核 digest，会在未发布时烧掉授权。 | 统一为一个控制面结果：所有 D12 mismatch 均在授权核销前检测，并触发 administrative finalize；broker 使用独立错误码通知编排层，不得把版本漂移伪装成普通发布失败或继续图路由。 |
| R3-12 | MAJOR | §1.1；§2.3；§12；§13 | （置信度 10/10）框架承诺交付可用的 gerrit/github 官方 adapter，但 P2 只交付“adapter 骨架”，P4 完成 gate 仍只使用 FakePublisher，后续没有任何阶段负责完成或验证真实 adapter；§12 还称 broker 无外部环境依赖，与新增发布职责矛盾。框架可在真实 adapter 尚不可用时被宣布完成。 | 在 P3/P4 增加官方 adapter 的功能完成、打包、安全审计、API fixture/本地模拟集成与受控真实环境验证 gate；§12 增加发布端点、凭据和权限预检，无法真实联调的材料登记为明确上线 gate。 |

## 5. CLARIFY 清单

无。剩余不确定点均直接影响授权、恢复、数据边界或可实现性，已提升为 issue。

## 6. 一句话总结

距离 draft freeze 还差：关闭 `I-02/I-05` 两个遗留 BLOCKER，并补齐授权新鲜度与发布 point-of-no-return、series 原子提交、resume 去重、join activation 及特权 IPC 的六个关键闭环。

上面是Codex的review意见
