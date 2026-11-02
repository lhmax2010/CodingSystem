# HLD v2.2 / 01 v0.12 独立评审 — Codex

评审日期：2026-11-02。以仓库文件为准；全文评审，不因上一轮处置或负责人裁决而缩小范围。本文只提出文档候选修改，未修改被审文档。

## 结论与统计

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.2 | **NO-GO** | 0 | 12 | 3 | 0 |
| 第二部分：01 v0.12 | **NO-GO** | 0 | 3 | 2 | 0 |
| 单列同步项，不计入上述缺陷数 | 待 HLD 定案后同步 | 0 | 3 | 1 | 0 |

GO 标准为没有 BLOCKER、MAJOR。严重程度按实际影响判定；没有把所有恢复缺口都提升为 BLOCKER。E-01 仍有效；本轮 **不批准 E-02/E-03 随该版整体生效**，原因是第一部分仍有 MAJOR，而非否定其勘误程序。

审阅对象 SHA-256（避免并行评审提交改变 HEAD 造成歧义）：

| 文件 | SHA-256 |
|---|---|
| `docs/00_Framework_HLD_v2.2.md` | `1573f9c45fc91bb2633c786cdc55644d168163f4b4d7bd9e36bc6d0d04778b34` |
| `docs/00_Framework_HLD_v1.0_draft_frozen.md` | `0094d2f4ce52a11e9a89962e34355d942475a19a585d48c9194f2d47dbb08a12` |
| `docs/01_Contract_Spec_v0.12.md` | `cb87e8d2964bbcf9c746afa6865043f8fd6925384d90b7b628728e4e69b08856` |

已读两份上一轮处置表、三家上一轮原始意见，并对冻结 HLD 与新版做文本对比。验证为规范走查及临时只读脚本：抽取 YAML 图反例、核对预算、扫描 A0 类型差集和示例文件存在性。仓库尚无本轮规则的可运行校验器，因此没有声称通过产品 conformance。`[待补充]` 的环境参数未被当作缺陷。

## 负责人六项裁决的独立评估

| # | 裁决 | 判断 | 理由、条件与对应问题 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时显式化 | **有条件成立** | AND-join 的完整同 cohort 到达可以证明发布报告的汇合必经；只对 release_requires 使用，不改变 E-01/V-15，这个取舍成立。但规则③仍按每条普通路径检查，旗舰被拒（H-01）；超时禁成功与冻结发布事实优先冲突（H-03）。保留并行，修正两处规则，不建议退回串行。 |
| ② | Quickbuild 的“最新”在 Run 启动时解析固定 | **有条件成立** | 固定实际 base、包版本与配置，并读回核对，比每次提交取最新正确。不能进一步推导“未锁定输入只要同批就等价”：远端两次作业仍可能解析出不同依赖（H-06）。保留负责人希望的默认最新与显式 base；不接受未经证明的 A/B 可比性。 |
| ③ | Profile v1 严格匹配，预留小改动复用 v2 | **有条件成立** | 版本化、默认关闭、编译器适配与每候选重测是合理边界；95%/前 20 属可验证的策略参数，不要求现在换另一套算法。但“收益差异不显著即可开启”不能证明可接受损失（H-12）；优化撤销闭环还须修 H-08/H-09。保留小改动复用的原意，将开启证据改为预定界限内的非劣/等效证据。 |
| ④ | 目标范围与模块登记表 | **有条件成立** | 减少无关测试和明确关注模块合理；不主张全系统测试作为默认。现文却在 patch 尚未提交时要求定格 patch 派生范围（H-10），且后续 AI 修复和显式 suites 可以突破该验证范围（H-11）。需把范围落在可计算的事务点，并把最低覆盖集变成强制约束。 |
| ⑤ | 以测试与多版本对比检验 AI，取代能力试点登记 | **有条件成立** | 对产 patch 的能力，重建、重测、保留失败版本并由框架汇总，足以成为一个合理的首期准入方案，不必强加 pilot/adopted 登记。测试证明只限声明覆盖与实际观测，不能推导测试永不可造假或不存在范围外缺陷。分析意见的采纳率也不是准确率/误报率（H-13）；范围与统计缺口见 H-07/H-11。 |
| ⑥ | 预检 Quickbuild 显式指定 base 及读回实际版本 | **成立** | §12 把可行性落成两个可验证动作，§11.3 有读回不一致使构建无效的夹具；无需把具体表单字段现在写死。实测尚未完成不算设计缺陷。此结论不替 H-06 的兜底作背书，也不声称本轮已执行真实 Quickbuild 探测。 |

## 上一轮处置逐项复核

### HLD 处置 K1–K22

“落实”仅表示对应原问题有实质解决，不表示关联新增文本全部 GO。

| 处置 | 核验结果及对取舍的判断 |
|---|---|
| K1 | D22、§7.6.1、部署与 E0 已落实独立内核/独立构建机，宿主不执行半可信 root 脚本；无 KVM 的同等边界替代成立。 |
| K2 | 已登记 E-02；同 dispatch 续接、全集计时、paused 到期有规则。资源先授予再取槽可作为实现基础；提交前登录/恢复等待和取消后额度仍不闭合，见 H-04/H-05。 |
| K3 | 按 mode 注册落实；负责人恢复并行后，release_requires 专用 AND 必经取舍成立，但第三条优化规则仍拒绝示例，见 H-01。 |
| K4 | D15、rpm_fix_loop 与旧 series 报告归属落实；私有试构建不冒充正式报告的取舍成立。 |
| K5 | required/independent 及专项示例落实，允许独立全量构建成立。 |
| K6 | 效应标记含 idem_key 指纹与 version；镜像按效应索引 probe，Blob 提交/复验落实。 |
| K7 | 参数、模式、测量记录、确定性判定已增加；只认 full 的取舍成立，但 SPEC 量纲和回归值定义有新矛盾，H-07。 |
| K8 | 静止判定不调用 AI、特权确认、判定字段复算落实；负责人替换登记表的判断见上表⑤及 H-13。 |
| K9 | 路径强制、父版本 A/B、撤销和轮次上限均有正文；组合尚不闭合，H-01/H-08/H-09。 |
| K10 | v1 完全匹配、排除 profile 文件、自 Run 待验区、首期 clang/BOLT 边界落实；新增 v2 的开启证据见 H-12。 |
| K11 | generation、静默与复位、quarantine、持板上限、sequence 租约已落实；租约超时不等于静默这一核心原则正确。 |
| K12 | 闭包键、single-flight、GC、基线测量不复用已落实；同批构建可以替代输入锁定的理由不成立，H-06。 |
| K13 | 空 series 生命周期、无空发布计划落实；用 advances 证明有净变更不成立，H-02。 |
| K14 | E-03 六命令、编排单写者和共享正式区只读落实；不增加 worker renew/query 的取舍成立，但等待场景须按 H-04 扩全。 |
| K15 | 会话注入独立通道、身份检查、deferred、脱敏落实；提交前失效与取消未完成仍见 H-04/H-05。 |
| K16 | CLI 专用用户、FD、文件/出口约束、配置 pin、LogAnalyzer 注入与估算上界落实；E0 不满足不上线的边界成立。 |
| K17 | approval CAS、通过谓词、证据引用、删除说明落实；BenchReport 谓词应以 §7A.3 的 gate_eligible 为准（候选修订 H-07 明确统一），不能只实现 §4.2.6 的简写。 |
| K18 | MCP 参数 request_id、跨传输幂等域、Origin 与 principal 已落实；01 的同步见 S-04。 |
| K19 | 第 7 组覆盖了新增主题；仍有普通支配与汇合必经互相冲突的迁移指令，H-15。 |
| K20 | SourceProvider、构建隔离、Gateway 已归期；核心先定稿、Benchmark 等 provisional 后经真实消费定稿的取舍可接受。P4 用 mock/fixture 验规范，P6/P7 才作真实后端/统计优化验收，不能用 P4 的替身成功代替后两者。 |
| K21 | 半可信脚本、只在板上执行、宿主声明式解析与 digest pin 已落实。 |
| K22 | G 编号/A17 合并已改；保留 A15 地址避免历史引用破坏合理。新增 R25 插入 R23 前属排版，不另立问题。 |

### 01 处置 X1–X11

| 处置 | 核验结果 |
|---|---|
| X1 | C-08a/b 消费 inbox 而不再次 CAS gate；C-08c 与 decision_submit 单胜；真实串联测试落实。 |
| X2 | 按实例持久化 epoch、当前实例、入向域与 C-10/C-10a guard 落实；握手重放与同实例 task lease 丢失见 C-02/C-03。取实例 epoch 而非连接 epoch 的方向成立。 |
| X3 | 静默唯一定义为 lease 回收 ∧ pgid reap，所有相关文字已引用；未把单独超时当静默。 |
| X4 | publishing 下 D12 不错误返回，not_happened 不许可时同事务映射关闭，ReconcileDeny 删除；这比继续要求 broker 发未执行 outcome 更完整，取舍成立。 |
| X5 | DispatchReceipt 已统一，载荷持久化、两事务、唯一 intent 落实；新旧 epoch 的未完成 intent 交接仍冲突，C-01。 |
| X6 | completed 后新实例重派已有触发及夹具；未覆盖同实例 task lease 丢失，C-03。 |
| X7 | recovery_state 与执行权 guard 已落；indeterminate 能被下一 epoch 的恢复臂重置，C-04。 |
| X8 | FramingError/ResponseError 边界、ULID、前置失败不留 receipt 已统一；hello 的连接副作用需专门处理，C-02。 |
| X9 | A0 大幅补齐且声明双向；仍遗漏 SnapshotManifest，C-05。 |
| X10 | ReconcileProceed 的原子许可条件一致，无“阻断性”歧义。 |
| X11 | epoch 界统一为 1 ≤ e < 2^53，边界测试已有。 |

## 第一部分：HLD v2.2 问题

### H-01 — MAJOR — 专用于 release_requires 的 AND 必经未解决优化规则对旗舰的拒绝

**位置**：HLD §4.2.1 示例一、§4.2.6 规则①/③、D18。

**依据**：规则①明确“汇合必经（仅用于本规则）”；规则③要求 opt_patch_ready 出发的“每条非失败路径”在审批/terminal 前“依次经过镜像节点、UT 节点、Benchmark 节点”。

**问题**：普通图中存在 `optimize → compile_rpm → compile_image → review_static → join:pre_final_review → review_final → ci_plan → human_review`，没有 UT/Benchmark。临时脚本直接从规范 YAML 抽取得到该路径。执行时 join 确实会等测试支路，但①明确不能拿来改变③的逐路径含义。因此严格实现必须拒绝本版旗舰。不能一边保留“仅本规则”，一边让实现者自行把③也理解成 AND 数据流证明。

**候选 diff**：

```diff
@@ §4.2.6 规则③
- 其 opt_patch_ready 路由边出发的每条非失败路径……必须依次经过镜像节点、UT 节点、Benchmark 节点
+ 对 opt_patch_ready 创建的新 series 建立验证义务；所有可成功关闭或进入发布审批的执行必须解除该义务。
+ 校验器以 AND-join 的完整到达语义证明：当前 series 的镜像完成先于 UT，UT 完成先于 Benchmark，
+ Benchmark 的通过路径先于成功终局/审批；允许无产 patch 的静态审查旁支并行。
+ 这是规则③自己的执行依赖证明，不把规则①的“汇合必经”改成 E-01/V-13b/V-15 的支配定义。
+ 任一后续 series 推进重置验证义务；运行时成功终局/审批 CAS 必须核对义务已解除。
```

**副作用/取舍**：保留负责人要求的并行，校验器需实现执行依赖而非单一普通路径枚举；E-01 与 threshold 来源仍普通支配。避免只为让示例通过而放松重验证。

**测试/夹具**：旗舰原文通过；删 UT、Benchmark、镜像任一者拒绝；将 bench_gate 与其测试依赖整体移出 join 必达分支的合法语法变体拒绝；旧 cohort 报告不得解除新 series 义务；join 超时只到 fail_safe；E-01/V-15 原反例仍拒绝。

### H-02 — MAJOR — advances 不证明净变更，较早的非空证明也会被撤销失效

**位置**：HLD §3 series_effect、§4.2.6②、§7A.4 撤销。

**依据**：“advances（本 task 已提交 candidate）”；运行时只拒“未提交 candidate”；随后断言“因此……needs-patch 节点不会面对无净变更的 series”。撤销要求“tree_digest 等价于父版本”。

**问题**：提交 candidate 与相对 snapshot 非空是不同命题。空专项提交候选后再撤销，会产生合法新 series，但最终 tree 回到 snapshot；之前经过的 advances/非空断言仍满足当前静态路径规则。任意无净效果 candidate 也可构造反例。CI 自身的兜底不能兑现对所有注册为 patch 的插件的保证。反过来，把所有撤销一概拒绝，又会破坏专项的正常退出。

**候选 diff**：

```diff
@@ §4.2.6②
- 每条路径都必须经过至少一条 series_effect ∈ {advances, asserts_nonempty} 的路由边
+ 对 input:none 做非空事实的数据流分析：初始为 unknown/empty；advances 使此前的非空证明失效，
+ 因为推进可能是撤销；asserts_nonempty 建立 nonempty；none 保留事实，汇聚取所有分支共同事实。
+ input_requirement:patch 的分派必须有当前 series 的 nonempty 证明，且运行时再次比较 tree_digest。
+ advances 的“必须提交 candidate”检查保留，但不再把它等同于有净变更。
@@ §5.1.1 注册及专项夹具
+ Compiler RPM 重验证若支持撤销到 snapshot，注册为 optional，并从候选/撤销记录取得明确重建目标；
+ CI 等真正需要净变更的消费者仍为 patch，须经过当前 series 的 asserts_nonempty。
```

**副作用/取舍**：可合法重验证撤销后的空净变更，但不能发布空内容；按 mode 夹具须给出真实输入要求，而非靠 advances 代替证明。比当前二值路径规则多一个数据流状态。

**测试/夹具**：`advances(no-op) → needs-patch`、`asserts_nonempty → advances(revert-to-base) → needs-patch` 均拒绝或运行时阻断；campaign 候选→撤销→完整重验→no_gain_found 合法；CI 对空净变更无计划；有净修复后重新断言非空可发布。

### H-03 — MAJOR — 超时绝对禁止 succeeded 与冻结的发布终态映射冲突

**位置**：HLD §4.3.2、§4.3.5、§8.2、§8.3。

**依据**：§4.3.5“任何超时项存在时 Run 不得以 succeeded 关闭”；§4.3.2 允许 sys.timeout 重试；§8.3“released → closed(succeeded)……不改变已发布事实”。§8.2 的审批 CAS 未增加超时/incomplete 禁入条件。

**问题**：节点超时→重试成功→当前报告全通过→批准→远端 released，是正文允许的时间线。此时两条规范要求互相矛盾。另一路为发布已核销后，并行非必需分支超时；冻结语义只允许 pending，不能把真实已发布改记失败。这不是“显式展示”就能解决的字段缺失。

**候选 diff**：

```diff
@@ §4.3.5 / §8.2 核销前
+ 存在任一超时记录（包括已重试成功者），或存在未经配置显式接受的 incomplete 项，
+ 禁止签发发布授权、禁止正常 terminal_success；生成含 retried 的 fail_safe 结果。
+ 核销事务复核该禁止条件，防止审批与核销之间新增超时。
- 任何超时项存在时 Run 不得以 succeeded 关闭。
+ 上述禁成功适用于发布 point-of-no-return 之前。publishing 下新超时仅登记 pending(fail_safe)，
+ 仍严格按 §8.3 远端事实映射；released 的 succeeded 结果必须首屏显示“已发布，但存在超时/未完成”，
+ 并保留 incomplete/retried，不可显示为全项通过。
```

**副作用/与负责人原意的取舍**：保留“超时不能靠重试掩盖并继续正常成功”的严格策略，代价是超时恢复后仍需新 Run 才能发布；只为已经不可撤销的发布事实保留冻结例外。若负责人希望“恢复成功即可成功”，必须另行明示该不同产品语义，不能由实现者默选。

**测试/夹具**：超时后重试成功不签授权；审批后/核销前新增超时阻断；核销后超时×released/release_failed 按冻结映射；所有分支 get_result 清单完整，已发布异常不伪装成未发布。

### H-04 — MAJOR — 会话失效等待只覆盖已拿到 build_ref 的阶段

**位置**：HLD §4.3.4、§5.2、§8.5 task_suspend、§8.6。

**依据**：等待 kind 只有 resource/remote_build；远程等待是“提交……随后调用 ctx.await_external(build_ref)”；task_suspend 限“远程构建在途时”；会话失效只切换“全部 remote_build 等待项”；§8.6 对“查询类请求”返回 dependency_unavailable。

**问题**：新 Run 开始时尚未登录、提交前会话过期、提交 ACK 丢失后恢复 probe 发现会话失效，均可能没有 build_ref/已登记 remote_build 等待项。此时不能合法调用当前 task_suspend，又要求 worker 不跨等待存活；直接抛 sys.error 会消耗 retry/关闭，违背等待运维登录的既定行为。尤其恢复 probe 的 deferred 还需要持久化调度责任，不能只增加一个返回值。

**候选 diff**：

```diff
@@ §4.3.4 / §8.5 / §8.6
+ ExternalWait 增 gateway_session；绑定 dispatch 与（若已有）effect idem_key/version，
+ phase ∈ {before_submit, submit_uncertain, polling, reconciliation}，不要求已有 build_ref。
+ 分派前检测会话就绪；提交 RPC 发现会话不可用，或恢复 probe 返回 deferred 时，
+ 编排原子登记该等待并结束/不启动 worker（包括 reconciliation worker），不消费 retry/probe 次数。
+ 登录超时按不可暂停的登录等待时钟累计；恢复后同 dispatch 续接。
+ submit_uncertain 必须先按效应标记 probe，不能因登录恢复直接再次提交。
+ E-03 task_suspend 的合法 guard 包含上述会话等待，并由编排核验 Gateway 状态。
```

**副作用**：增加一种等待和阶段字段，session 不进入 worker；原远端幂等协议不变。会话不可用期间的占额按 H-05，不把未知提交当未发生。

**测试/夹具**：无会话首次提交、发送前过期、发送成功 ACK 丢失且会话过期、恢复 probe deferred 四例；全程无等登录的 worker，重启计时不重置，登录恢复不重复提交，登录到期产生明确 timeout。

### H-05 — MAJOR — 取消失败即释放远程额度，实际在途构建可无界超额

**位置**：HLD §4.3.4 预算到期/取消传导、§7.6.3、§8.6。

**依据**：“远端在途构建继续占远程构建配额”；“取消远端构建、释放租约，取消失败告警但不阻断”；“迟到结果……审计化丢弃”。

**问题**：额度为 1，A 已提交，取消 RPC 失败而释放额度；B 随即可提交，重复后真实作业数无界。逻辑 Run 可以及时关闭，但配额不应假装远端已停。若关闭后只丢弃迟到事件，也没有持久化清理责任来最终归还额度。板子章节已经正确区分 lease 到期与静默，远程作业需要相同的事实分离。

**候选 diff**：

```diff
@@ §4.3.4 取消传导 / §8.6
- 发起 Gateway 取消（幂等）并释放资源租约；迟到结果……审计化丢弃。
+ Run 可先终局；远程作业进入持久化 cancel_pending/reconciling，仍占远程额度，
+ 直到 Gateway 确认终态或确证从未提交才释放。取消失败重试与 probe 由框架清理任务承担，跨 Run 关闭/重启存续。
+ 迟到结果不得推进旧业务任务，但必须用于更新作业清理状态与恰一次归还额度；不可判定者隔离占额并告警。
```

**副作用**：远端长期不可达时可阻塞后续远程构建，这是配额真实性的代价；保留负责人“不因取消 RPC 失败卡住 Run 终局”的原意，不强行无限等终局。

**测试/夹具**：quota=1、取消失败时 B 不提交；Run 已关闭后远端完成恰一次归还；清理事务前后 kill；重复/旧 version 回报不能多归还；未确证提交的作业也保留占额。

### H-06 — MAJOR — 同批构建不能证明 unpinned_inputs 两侧相同

**位置**：HLD §7.6.1 Quickbuild 兜底、§7.8 闭包一致性、§4.3.5；处置 K12、负责人②。

**依据**：兜底要求“同批构建、不跨 Run 复用……不阻断发布”；§7.8 要求“相同的构建输入闭包、只有 series/tree 不同，否则不得比较”。处置理由直接声称“同批构建保证 A/B 仍然只差 patch”。

**问题**：A/B 作业同时入队不等于同一时刻解析依赖。一个无法 pin 的仓库在两作业解析之间更新，就会产生并非 patch 导致的差异。仅标注 unpinned_inputs 不让性能结论变得有效；而自动把它加入 incomplete 却“不阻断发布”，也缺少 §4.3.5 所要求的配置显式取舍。

**候选 diff**：

```diff
@@ §7.6.1 兜底
- ……同批构建……不阻断发布。
+ 同批只减少漂移概率，不证明可比。必须读回全部未锁定输入的实际内容标识，
+ A/B 两侧经确定性核对相同后才能生成比较字段；读不回或不一致时 comparison=unverifiable，
+ gateable 比较字段缺失、不得用于优化收益接受，基线不可跨 Run 缓存。
+ 仍可保留两侧绝对测试结果。若业务确需发布这种未经可比性验证的 patch，须在非优化流水线
+ 显式配置 accept_unverified_build_inputs 并相应声明缺失的发布验证；审批证据明示。
+ 这项显式取舍不得把无效 BenchReport 改成 gate_eligible，也不得绕过既有 threshold。
```

**副作用/取舍**：保留默认最新解析固定和诊断用途；放弃“同批天然可比”的无依据保证。默认全流程会在不具备可比较证据时停止，只有另行明确声明的验证子集可以继续发布。

**测试/夹具**：FakeQuickbuild 同批作业在解析间改变依赖→不可比较；读回相同实际 digest→可比较但不跨 Run 缓存；读不回→字段缺失；未声明取舍的 incomplete 阻止正常成功；优化不得接受 unverifiable 收益。

### H-07 — MAJOR — BenchPolicy 的 SPEC 量纲、回归符号及不可计算分支未闭合

**位置**：HLD §7A.3 统计判定/逐指标结论/判定字段，§4.2.6①。

**依据**：“效应 = 方向归一后的相对中位数变化（越小越好的指标取反）”；“SPEC 三值……效应区间整体在 SPEC 内”；“regression_pct = 显著回归指标的效应点估计最大值”；“无显著回归 = 0.00”；“无法计算 → 不得生成‘通过’的聚合值”。

**问题**：启动耗时的 SPEC 为毫秒上限，相对变化区间为百分比，二者不能比较；没有基线的专项首轮也没有效应区间，却需要绝对 SPEC。另取原始相对变化 `(candidate-base)/base`：耗时 100→120，取反后为 -20%，直接作 regression_pct 就能通过 `<=5`。如果实现选择反向原始公式，则需写明而非留两个相反实现。零基线/BCa 退化等 inconclusive 也不是“没有显著回归因此 0.00”。BCa 的退化区间可能为 NaN，这并非纯假设，见 [SciPy bootstrap 官方说明](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)；本评审不要求使用 SciPy，只要求策略有确定的异常分支。

**候选 diff**：

```diff
@@ §7A.3
+ 同时计算 candidate_median_ci（指标原单位）和 effect_ci_pct（A/B 相对效应，百分比）。
- SPEC 三值判定：效应区间整体在 SPEC 内……
+ absolute 类型 SPEC 使用 candidate_median_ci，与 SPEC 单位及比较算子一致；
+ relative 类型 SPEC 才使用 effect_ci_pct。SuiteVersion 必须声明类型，禁止跨量纲比较。
+ regression_pct 的方向统一为“正值表示劣化”：lower_is_better 时 r=100*(C-B)/B，
+ higher_is_better 时 r=100*(B-C)/B；只对允许相对比较且 B>0 的指标使用，其他另行定义或 inconclusive。
+ 显著回归以 r>0 判定；聚合取显著回归 r 的最大值。
+ 任一必测比较不可计算/区间非有限/缺必要 SPEC 时，不生成可通过的聚合值；
+ 只有全部必测比较均有效且无显著回归才输出 0.00。舍入时点、并列值、重采样器与退化处理须版本化。
@@ §4.2.6①
- BenchReport = validation_complete
+ BenchReport = gate_eligible（mode==full 且该验证目的的必需覆盖、样本与判定均完整有效）；
+ comparison:none 的绝对报告只能满足声明为绝对验证的目的，不能充当 A/B 收益或回归证据。
```

**副作用**：不把不显著改成回归，也不改变负责人选择的统计方法；增加绝对与相对的两个区间及验证目的。部分过去可能得到 0.00 的不可判定输入将 fail-closed。

**测试/夹具**：耗时 100→120 与吞吐 100→80 均为正回归；耗时绝对值超 SPEC 但相对改善仍 SPEC-OUT；绝对达标但相对劣化分别显示；首轮 comparison:none 可判绝对 SPEC；零基线、全等样本 BCa 退化、缺 SPEC、样本不足不得汇总为通过；固定种子黄金向量逐字节复算。

### H-08 — MAJOR — 仅检查 series 顶段，优化计划经修复/撤销后失去完整生命周期

**位置**：HLD §7A.3 优化轮、§7A.4 计划/收益/UT 归因、§7A.1 修复回流。

**依据**：“当前 series 顶端为 Optimization 产出的段时”才做父版本第二组 A/B；UT 同样只看“顶端为优化段”；撤销也以新段推进 series。

**问题**：S0→优化 S1→Compiler 修复 S2→UT/Benchmark，通过条件不再识别 S2 为待验优化，却仍包含 S1 的优化；没有 opt_verdict 可供接受/拒绝。另一面，Optimization 自己产出的撤销 S3 顶段仍来自 Optimization，字面规则又把撤销当候选再次判收益，可能对同一 rejected plan 重复撤销，或比较错误父版本。不能只以 producer 身份判断未决优化。

**候选 diff**：

```diff
@@ §7A.4
+ OptimizationPlan 在 Ledger 中有 plan_id、parent_series/tree/image、candidate_series、
+ state ∈ {pending_validation, accepted, rejected, reverting, reverted}；series 段声明 purpose=candidate|repair|revert。
+ 一个待验证 plan 的修复后代继续属于该 plan，父版本比较锚点不随修复改变；
+ Benchmark/UT 根据未决 plan 归属判断，不依赖当前顶段 producer。
+ pending_validation 的 UT 失败执行确定性撤销至 plan.parent_tree，包含该候选后的修复；
+ 撤销段仅执行构建/UT/常规 Benchmark 重验证，不作为新的收益候选，不再对 rejected plan 产出二次撤销。
+ 只有 accepted，或 reverted 且重验证完成，才可继续提案/结束；缺 opt_verdict 不可当 no_further_gain 放行。
```

**副作用**：增加计划状态与段用途，仍通过新 patch 撤销，不回拨 current。保留 Compiler 修复的能力，但不得让其抹掉优化验证责任；一个 plan 未处置完不叠加下一候选。

**测试/夹具**：优化→RPM 修复→父版本退化仍撤销；优化→修复→UT 失败撤销整个候选链；neutral→撤销→重验只撤销一次；缺 opt_verdict 拒绝结束；计划状态提交前后 kill 后同一处置。

### H-09 — MAJOR — max_opt_rounds 与实际撤销路由预算不相容

**位置**：HLD §7A.4 轮次自限/UT 归因、§4.2.6③、campaign YAML 的 ut_fix_loop/opt_loop。

**依据**：按“自身产出段的计数”限制候选；“每个候选至多一次提交 + 一次撤销”；UT 撤销走 ut_fix_patch_ready；campaign 为 max_opt_rounds=2、ut_fix_loop.max_rounds=1、opt_loop.max_rounds=4。

**问题**：两个候选先后导致 UT 失败，第二次正常撤销走 ut_fix_loop 第 2 次就被 fail_safe 拦截，opt_loop 的 4 次预算没有帮助。若是 Benchmark 拒绝，第一个 candidate + optimizer 自产 revert 已累计两段，按当前计数就耗尽两个候选名额。两条路径分别造成正常撤销失败和候选计数错误。

**候选 diff**：

```diff
@@ §7A.4 轮次自限
- 以 series lineage 中自身产出段的计数
+ 按本 Run 已创建的不同 OptimizationPlan 候选计数，repair/revert 段不计新候选；
+ 上限只禁止创建新计划，不得跳过当前计划的判定或撤销。
@@ §4.2.6③ 与示例
+ 对所有承载优化撤销的回流环分别验证容量：opt_loop 覆盖候选提交及 Benchmark 撤销；
+ ut_fix_loop 至少额外预留 max_opt_rounds 次优化 UT 撤销，普通 UT 修复额度另计并写入 fixture。
+ campaign 将 ut_fix_loop.max_rounds 从 1 调为 3（原普通修复 1 + 优化撤销 2）；
+ full_pipeline 将该值从 2 调为 3（原普通修复 2 + 优化撤销 1）。
```

**副作用**：允许更多有明确定额的 UT 回流，run/loop 时间预算仍兜底；不修改冻结“第 N+1 次拦截”的语义。若不愿共享额度，可另设优化撤销 status/环，但需同时更新两份 YAML 和 mode 注册集。

**测试/夹具**：campaign 两候选均 UT 失败→两次撤销均能执行→正常无收益终局；普通修复额度与撤销额度组合边界；一次 neutral 撤销后仍能尝试第二候选；到上限的在验候选仍须完成处置。

### H-10 — MAJOR — Run 创建时无法确定尚未提交 patch 的模块与套件集合

**位置**：HLD §3 目标范围、D12、§6.5、§7A.7。

**依据**：“目标范围的确定（Run 创建时定格，Run 内不可变）”；patch 范围由“patch 逐段的 repo / 包归属”推导；§4.3.1 为 created→awaiting_patch→submit_patch，§7A.7 还规定范围推导失败拒绝 submit_patch。

**问题**：create_run 时没有 patch，无法计算该并集；suites:auto 所选版本又依赖范围，D12 却要求创建时固化本 Run 引用的套件集合。实现只能把未知数据当已定格，或在后续合法提交时把自己判为配置漂移。这是生命周期决策缺口，不是待补环境信息。

**候选 diff**：

```diff
@@ D12 / §3 / §7A.7
- Run 创建时定格的模块集合
+ input:none 在 snapshot pin + 初始空 series 事务中确定范围；input:patch 在首次 submit_patch
+ 受理事务中，基于创建时 pin 的 ModuleRegistry/套件注册表版本确定范围与实际套件集合，随后不可变。
+ 创建先 pin 环境与注册表版本；首次 series 事务一次性补齐 range/suite selection 的执行绑定，
+ 在进入 queued 之前生成最终 execution manifest。此初始化完成前不得 dispatch/审批。
+ 相同 request_id 重放返回同范围与同最终 manifest；事务失败不留下部分范围或半签发 series。
```

**副作用/取舍**：把“创建时”细化为执行前的两步初始化；不允许执行中随意改 scope。负责人想固定本次关注范围的意图保持，实际可计算时点后移到收到 patch。

**测试/夹具**：创建不含 patch 不伪造范围；提交涉及 focus 外模块时并集正确；创建后外部 registry 更新仍按已 pin 版解释；初始化提交点前后 kill；重复提交不重新取“最新”套件。

### H-11 — MAJOR — 后续修复和显式 suites 可以绕过“改动模块不可缩小”的验证底线

**位置**：HLD §7A.7、§7A.1/7A.2、§4.2.6 release_requires、R25。

**依据**：“改动涉及的包所属模块……不可缩小”；“Run 内不可变”；“显式列出套件时以列出为准”；“gate_eligible 以所选集合的覆盖完整为准”；范围推导失败的拒绝只规定在 submit_patch。

**问题**：初始 patch 属 A，Compiler/UT 修复随后改 B，现文没有 candidate 范围校验，B 没进固定范围却可随最终 series 发布。即使没有后续修复，用户显式列一个容易通过的小套件，也能覆盖完整所选集合而删掉模块必测与 always_run，和负责人“改了的代码必须被验证”不一致。只在 CLI 展示范围不能抵消证据集缩水。

**候选 diff**：

```diff
@@ §7A.7 / series_candidate_submit
+ 每次 candidate 受理都依据已 pin ModuleRegistry 检查改动包归属；超出本 Run 固定范围或无法归属则拒绝，
+ 返回需要新 Run/扩展 focus 的诊断。优化、Compiler、UT 修复与撤销均适用，不仅初始 submit_patch。
- 显式列出套件时以列出为准
+ 显式列出套件可增加验证或选择登记的等效替代；发布用 full 模式不得少于范围内必测套件与 always_run。
+ gate_eligible 依据该最低集合而非调用者任意子集计算；诊断子集可测，但不得作完整发布证据。
```

**副作用/取舍**：保持负责人“不跑所有无关模块”及范围不可变；涉及新模块的自动修复需要新 Run，而不是悄悄扩大任务。显式小套件仍可用于诊断，无法暗中删除最低验证。

**测试/夹具**：A 范围内的修复可提交，A→B 跨模块 candidate 拒绝并说明；显式 suites 缺 always_run 或模块必测不具 gate_eligible；等效替代须由版本化 registry 声明；篡改报告 coverage 不满足审批 CAS。

### H-12 — MAJOR — Profile v2 用“不显著”作为开启依据，无法证明复用损失可接受

**位置**：HLD §7.8 Profile 新鲜度策略 v2 第 5 项；负责人裁决③。

**依据**：“两组的优化收益差异，差异在 BenchPolicy 判定下不显著，即可……设为该流水线的新鲜度策略”。

**问题**：样本噪声大/样本少也容易不显著。一个覆盖 -15% 到 +15% 的差异区间可能不显著，却不能证明复用与重采接近。每候选 A/B 能拒绝负收益，但仍可能长期接受 1% 改善并错过重采可得的 10%，与放宽策略的效果验证目的不同。95% 函数权重覆盖是输入匹配条件，也不替代收益非劣证据。[ASA 原始声明](https://doi.org/10.1080/00031305.2016.1154108)明确区分“大 p 值”与支持零假设的证据。

**候选 diff**：

```diff
@@ §7.8 策略 v2 开启条件
- 差异在 BenchPolicy 判定下不显著，即可……开启
+ 在采样前固定模块/改动类型集合、最小有意义收益差异 epsilon、采样计划与统计方法版本。
+ 对“复用收益 - 重采收益”做非劣评估，置信下界必须高于 -epsilon；
+ 如声明等效，整个差异区间必须落入 [-epsilon,+epsilon]。证据不足为 inconclusive，保持 v1。
+ 启用只覆盖已验证的优化方法/编译器版本/模块类别；支持函数匹配的适配器单独提供兼容与失败向量。
```

**副作用/取舍**：可能需要更多实测，不能凭一次“不显著”快速启用；不否定小改动复用，也不改首期默认 v1。阈值是需由项目明确的效果容忍决策，不能藏在环境待补资料里。

**测试/夹具**：宽区间且 p≥0.05 不开启；窄区间满足非劣界开启；恰跨界 inconclusive；方法/编译器适配不支持时拒用；策略版本变化进入 D12；继续覆盖候选劣化撤销。

### H-13 — MINOR — AI 采纳记录不能直接计算准确率与误报率

**位置**：HLD §7A.0 原则6、G11、R22。

**依据**：“采纳 / 不采纳……按能力累计统计准确率与误报率”。

**问题**：审核人可能因为成本不采纳正确建议，或采纳错误解释。该二值记录只能得到采纳率，没有真假标签及误报分母；不能用它评价分析类 AI 的正确性。负责人⑤的测试报告替代试点登记仍可保留。

**候选 diff**：

```diff
- 按能力累计统计准确率与误报率
+ 按能力统计采纳率；准确率/误报率仅在独立复核获得事实标签及明确分母的子集计算，
+ 同时展示标注覆盖率、样本数与 unknown。采纳/不采纳不自动充当真假标签。
```

**副作用**：指标名称更诚实；若确需准确率，需要额外的事实复核工作。**测试/夹具**：正确但未采纳、错误但采纳、未知三种记录；仅有采纳记录时不生成准确率字段；G11/R22 与报告 schema 同步。

### H-14 — MINOR — 四份示例的原文字节验收缺两个规范源及注册夹具

**位置**：HLD §2.4、§4.2.1/4.2.6、§11.3、P1。

**依据**：“四份示例流水线原文字节加载通过”；“示例 pipelines/ 下四份流水线随仓交付”。

**问题**：本版只有 full_pipeline、optimize_campaign 两个 YAML 块，仓库没有所列四个 pipelines/*.yaml。01 A4 的 compiler_bench_only 属冻结 v1.0 上游，直接 Compiler→Benchmark，并不是本版镜像依赖下的规范示例。因而不能核验用户要求的四份“都通过”，也不能把未来实现者自行补出的版本称为原文字节验收。按 mode 的完整输入/状态夹具也须与示例一起交付。

**候选 diff**：

```diff
@@ §4.2.1 之后追加（同版落四份 pipelines 文件，完整注册夹具按本轮规则一起更新）
+ **示例三：compiler_only.yaml**
+ ```yaml
+ pipeline: compiler_only
+ dsl_version: 1
+ input: patch
+ nodes:
+   compile_rpm: {agent_type: compiler, mode: rpm}
+   summary: {agent_type: review, mode: final, terminal: true, success_on: [review_report_ready]}
+ entry: compile_rpm
+ loops:
+   - id: rpm_fix_loop
+     edges: [{from: compile_rpm, to: compile_rpm}]
+     budget: {max_rounds: 3, max_wall_clock_min: 480}
+ routes:
+   - {from: compile_rpm, on: build_passed, to: summary}
+   - {from: compile_rpm, on: build_fix_patch_ready, to: compile_rpm}
+   - {from: compile_rpm, on: build_failed_exhausted, to: fail_safe}
+ default_route: fail_safe
+ run_budget: {max_wall_clock_min: 720}
+ ```
+ **示例四：compiler_bench_only.yaml**
+ ```yaml
+ pipeline: compiler_bench_only
+ dsl_version: 1
+ input: patch
+ nodes:
+   compile_rpm: {agent_type: compiler, mode: rpm}
+   compile_image: {agent_type: compiler, mode: image, config: {backend: local, rpm_precheck: required}}
+   benchmark: {agent_type: benchmark, config: {suites: auto, mode: full, collect_profile: false}}
+   bench_gate: {gate: threshold, metric: benchmark.regression_pct, op: "<=", value: 5.0}
+   summary: {agent_type: review, mode: final, terminal: true, success_on: [review_report_ready]}
+ entry: compile_rpm
+ loops:
+   - id: rpm_fix_loop
+     edges: [{from: compile_rpm, to: compile_rpm}]
+     budget: {max_rounds: 3, max_wall_clock_min: 480}
+   - id: image_fix_loop
+     edges: [{from: compile_image, to: compile_rpm}]
+     budget: {max_rounds: 2, max_wall_clock_min: 480}
+ routes:
+   - {from: compile_rpm, on: build_passed, to: compile_image}
+   - {from: compile_rpm, on: build_fix_patch_ready, to: compile_rpm}
+   - {from: compile_rpm, on: build_failed_exhausted, to: fail_safe}
+   - {from: compile_image, on: image_ready, to: benchmark}
+   - {from: compile_image, on: image_fix_patch_ready, to: compile_rpm}
+   - {from: compile_image, on: image_failed_exhausted, to: fail_safe}
+   - {from: benchmark, on: bench_done, to: bench_gate}
+   - {from: bench_gate, on: pass, to: summary}
+ default_route: fail_safe
+ run_budget: {max_wall_clock_min: 2880}
+ ```
+ 两个子集均无 release，不声明 release_requires；Review final 接受 optional 上游并明确呈现缺失。
+ compiler.rpm 仅 produces build_report；compiler.image 仅 produces image_report，required 时硬需前者；
+ Benchmark 硬需 image_report，review.final 的 status 含 review_report_ready。
+ 修复 status 为 advances，成功/失败 status 为 none；新原文覆盖替换旧 CF-FIX 相应模式集合。
+ 01 旧 A4 继续只作为旧上游规范，切换上游时显式替换。
```

**副作用**：新增验收资料，不要求本轮评审者替作者实现流水线。**测试/夹具**：四份原文逐一载入同一注册集；按原词素处理 on/value；两个新子集删除对应插件后验证预期拒绝/通过，不能拿 v1.0 原文冒充 v2.2。

### H-15 — MINOR — 附录 B 同时要求普通支配与汇合必经

**位置**：HLD 附录 B 第7组“注册与 DSL”及“报告与消息”。

**依据**：前者要求“V-13b/V-15 与 release_requires 共用同一普通支配定义”，后者又要求“release_requires 的‘汇合必经’形式化”。

**问题**：两条同步指令不能同时实现；这是 v2.1→v2.2 的残留，不应让后续 01 据此把 E-01 支配规则误改或重新拒绝旗舰。

**候选 diff**：

```diff
- 含 V-13b/V-15 与 release_requires 共用同一普通支配定义的说明
+ V-13b/V-15 维持普通支配；release_requires 单独形式化规则①的汇合必经；
+ 优化重验证按规则③的执行依赖证明单独实现，不改 E-01。
```

**副作用**：无新增权限或运行时语义，只消除迁移歧义。**测试/夹具**：01 同步追溯检查同时含 E-01 原反例、parallel release_requires 正例和优化并行正/反例。

## 第二部分：01 v0.12 问题

### 四条时间线 × 崩溃点走查

下表区分 RPC 送达事实与远端发布事实。D0=dispatch intent 提交前；D1=intent 已提交、发送前；D2=broker 受理后 ACK 前；D3=ACK 后 completed 提交前；D4=completed 后；D5=consume/resumed/Proceed 提交后至远端 outcome 落账前。`—` 表示首次派发时与该行的远端前提不相容，不拿不可达组合充覆盖数。

| 时间线 | D0 | D1 | D2 | D3 | D4 | D5 / 远端事实映射 |
|---|---|---|---|---|---|---|
| T1 正常发布；仅编排重启/连接 ACK 丢失，broker 实例仍活 | 未发，正常建 intent | 同 id 重送 | broker 内存去重同 id | 同 id 回 ACK 后补 completed | 不因 completed 重建逻辑 task | 同 epoch consume receipt 返回首 granted；执行后 released/failed 两值闭合。hello 重连动作见 C-02。 |
| T2 broker/task 中断，远端确证未发生 | 尚无授权核销，可正常派发 | 新 epoch 的旧 intent 交接有冲突 C-01 | 同左；即使已核销也不能越过静默 | 同左 | 新实例可触发重派；只有 task lease 失且实例不变会漏扫 C-03 | consumed 时新 epoch resumed→not_happened；许可通过才执行，不通过同事务 release_failed 映射。未 consumed 者正常 granted。 |
| T3 broker 中断，全部已发布或部分已发布 | — | — | 若受理后已并发执行，交接仍受 C-01 影响 | 同左 | 新实例重派路径已新增；同实例 task 丢失见 C-03 | 全部 happened→ledger released；部分只能 indeterminate→T4。pending admin 不覆盖真实 released。 |
| T4 resumed 对账 indeterminate | — | — | 如已到达该事实，未完成 intent 仍须按 C-01 交接 | 同左 | completed 不代表发布完成；待 C-11，不得因新 broker 把事实清空 | 同 epoch 再 reconcile 被拒已落实；再次换 epoch 却能重置 recovery_state，再获发布许可，C-04。 |

其他原子边界逐项检查：

- **决定/TTL 与 outbox**：decision_submit 或 C-08c 只一方 gate CAS 胜出；提交前 kill 未决定，提交后 kill 靠 outbox；C-08a/b 同事务 inbox+durable dispatch，消费前/后重复均不再改 gate。paused 与 running 两臂一致。
- **核销响应丢失**：同当前实例重连保持 epoch，③连接校验后命中该 epoch receipt，返回原 granted；新实例不能命中旧 epoch receipt。不同 request_id 的同 epoch consume 被拒，未见旧版的双许可问题。
- **resumed 提交前/后 kill**：前者仍为旧 holder；后者新实例须静默并再恢复。reconcile 的结果与 recovery_state、映射/许可必须同事务，不能先发送 Proceed 再落状态。
- **not_happened + D12 漂移**：同事务 pending(admin_finalize)+失败映射；响应丢失重放 Recorded，不依赖“未执行但发送 release_outcome”。happened 与 indeterminate 两臂也不再被 D12 错误阻断。
- **Proceed 已提交、执行前/执行中 broker 崩溃**：下一实例重新对账，不能使用前 epoch 的 Proceed。其 DispatchReceipt 交接仍需 C-01；未知已进入 C-11 的例外需 C-04。
- **outcome/Recorded 终局事务提交后 ACK 丢失**：同 epoch 同 request_id 从 receipt 返回首响应；Run 不再迁移。旧实例晚到消息在当前 epoch 校验拒绝，不进入 C-10/C-10a。
- **多目标发布**：部分发布不压成两值 outcome 的成功；恢复报告只能 indeterminate，保留人工证据与 correction 的冻结路径。不能凭“剩余目标未发生”取得整个计划的新许可。

### C-01 — MAJOR — 旧 epoch 未完成 intent 与新 epoch 重派的新 intent 互相阻塞

**位置**：01 §2.2d 持有者更替重派、§2.5 DispatchReceipt、§5.1 出向、CF-IPC-10。

**依据**：§2.5“同一 token 任一时刻至多一个 state=intent”；状态只有 intent/completed；“intent 无 completed → 以同 request_id 重派”。§2.2d 新实例必须“以新 DispatchReceipt（intent，新 request_id，recovery=true）重新送达”。

**问题**：E1 收到 release_dispatch 甚至已 consume，但 ACK 前崩溃，Ledger 仍是 intent(E1)。E2 hello 后，按 §2.2d 写新 intent 被唯一约束拒绝；按 §2.5 重送旧 intent 又没有 target_epoch 跨实例处理规则。若直接改 target_epoch，破坏原送达事实；若标 completed，伪造未收到的 ACK。当前“最终续跑”的 CF-IPC-10 期望没有可执行迁移支撑。completed 后崩溃的新增路径修好了原问题，但没有覆盖更早的三个窗口。

**候选 diff**：

```diff
@@ §2.5 DispatchReceipt
- state: Literal["intent","completed"]
+ state: Literal["intent","completed","superseded"]
+ superseded_by: str | None = None
+ superseded_at: datetime | None = None
@@ §2.2d / §2.5 出向协议
+ 当前 epoch 与 intent.target_epoch 相同：按原 request_id 重送。
+ 当前 epoch 已更替：先检查授权核销态；已核销须等旧 holder 静默，未核销无需等静默。
+ 满足重派条件后，在一个 Ledger 事务内将旧 intent CAS 为 superseded，并写新 epoch 的唯一 intent，
+ 保存替代链，不伪造旧 ACK、不改旧 target_epoch；已 completed 的旧 receipt 保持不变。
+ 发送前复核当前 epoch 与新 intent 目标一致；再次更替则重新走同一替代协议。
+ 旧 ACK 晚到只写历史审计，不能完成新 receipt、恢复旧执行权或创建第三个 intent。
```

**副作用**：模型增加一种历史终态及替代引用，仍保证同 token 至多一个活跃 intent；两个 Ledger 提交协议不变。A0 不增加重复模型；§5.1 统一引用该状态机。

**测试/夹具**：CF-IPC-10 的 D1/D2/D3 分别让 broker 换实例；覆盖未核销/已核销两种前提、静默未确认、替代事务前后 kill、E1 ACK 晚到、E2 尚未发送又换 E3；断言无永久 intent 阻塞、无双活跃 intent、无虚假 completed。

### C-02 — MINOR — hello 的前置例外与重放时连接绑定动作未落到统一处理序

**位置**：01 §2.2a 处理序、§2.2d hello、§5.1 全命令统一序/FramingError 客户端行为。

**依据**：§2.2a③写“已握手 ∧ 连接 epoch == 当前 broker epoch ∧ 载荷 broker_epoch == 连接 epoch”；§5.1 所有命令先连接校验后 receipt；§2.2d 要求同实例重连“返回同一 epoch、绑定新连接并关闭该实例旧连接”。broker_hello 的显式例外当前只落在幂等域。

**问题**：握手本来就是给尚未绑定的连接建立 epoch，且 HelloRequest 不含 broker_epoch。现文应明确上面的连接谓词适用于哪些命令，并把“同 id hello 重放仍重新绑定连接”安排在返回 receipt 之前。否则一个按通用模板实现的服务器可能在 hello 时先拒未握手，或直接返回旧 HelloResult 却没有绑定新 socket。这里按 MINOR 计：特例意图可从 §2.2d 推知，缺的是唯一处理位置，而非否定实例 epoch 设计。

**候选 diff**：

```diff
@@ §5.1 统一处理序③ / §2.2d
+ broker_hello 是尚未握手连接的唯一允许命令：③只校验 broker socket peer 与实际进程身份，
+ 不要求已有 epoch；payload 的 pid/pgid/start_time 与服务端核实身份一致。
+ 当前/退役实例检查先于 receipt。首次 hello 的 epoch 分配与实例记录同事务；
+ 同实例 hello（含同 request_id receipt 重放）每次都先完成连接绑定、关闭旧连接，再返回同 epoch。
+ 连接绑定是每连接动作，不被命令 receipt 的“只返回首响应”省略。
+ 其余 broker 入向命令要求已握手且当前 epoch；仅含 broker_epoch 字段的请求再做载荷等值校验。
```

**副作用**：无需新增命令；首次 hello 的 FramingError/载荷错误仍不写 receipt。**测试/夹具**：首次未握手 hello 成功但 consume 拒绝；hello 响应丢失后新 socket 同 id 重放，接着 consume 成功且旧连接不可用；旧实例重放 hello 不能靠历史 receipt 回来；伪造 pid/start_time 拒绝。

### C-03 — MAJOR — 同一 broker 实例丢失 task lease 时，重派扫描条件永远不选中它

**位置**：01 §2.2d 持有者更替重派、§2.2a④、C-09；冻结 HLD §8.3 broker task 静默。

**依据**：触发之一是“当前 holder 的 broker task lease 丢失”；扫描却只选“最近一次送达的 target_epoch ≠ 当前 epoch”；恢复臂要求“连接 epoch > 授权 granted_epoch”。

**问题**：broker 服务实例仍在，但某个 release task 子进程挂起/被回收或 lease 丢失。当前 epoch 没变，target_epoch 仍相等，扫描为空；即使人工补发，同 epoch consume 不走恢复臂而是 already_consumed。冻结 HLD 将 broker task 进程组与 lease 作为静默对象，并没有规定 task 失联必然导致整个 broker 实例重启。新触发条件因此没有覆盖声称覆盖的情形。

**候选 diff**（选择不引入第二套 task epoch 的最小方案）：

```diff
@@ §2.2d
+ holder 的 broker task lease 丢失时，将该 broker 实例标记 retiring，立即拒绝其新增执行命令；
+ 框架 supervisor 终止并 reap 该实例及其登记任务进程组，然后启动新 broker 实例。
+ retiring/retired 实例即使仍是数值最大 epoch，也不得重新 hello 复活。
+ 新实例 hello 分配更高 epoch；再按未核销/已核销及静默 guard 扫描重派。
+ 若无法 reap，则保持 publishing 并告警/走允许的 C-11 处置，不把 lease 丢失冒充静默。
```

**副作用**：单个 task 失联会重启当前 broker，其他待办也须按 Ledger 恢复；这是保持“执行权只按进程实例 epoch”这一简洁模型的代价。若需保留进程而只重启 task，必须另外正式设计 task generation，不能继续混用当前 epoch。

**测试/夹具**：CF-AUTH-05 新增 broker daemon 活着但 task lease 失/子进程已退出；恰一次 retiring→新实例→resumed；旧实例晚到 outcome 拒绝；无法 reap 不重派；未核销 task 新实例正常 granted。单独断连但 lease 正常不得触发此重启，保留 CF-AUTH-11。

### C-04 — MAJOR — 新 epoch 可把 indeterminate 重置成可再次发布

**位置**：01 §2.2a④、§2.2d 重派、C-09/C-10a/C-11、CF-AUTH-17。

**依据**：indeterminate 后“终局只经 C-11”；但④ guard 仅检查 publishing、本 task、绑定、更高 epoch、静默，随后无条件令 `recovery_state := reconcile_required`。

**问题**：E1 resumed→indeterminate→broker 崩溃；E2 满足④，状态被重置。E2 再得到 not_happened 时可获 Proceed 并发布；若同一 not_happened 由 C-11 自动 probe 得到，则映射 release_failed 关闭。旧版“同一观测两种终局”的问题只在同 epoch 修掉了；换进程即可重现，并绕过“indeterminate 之后只走 C-11”的锁存语义。

**候选 diff**：

```diff
@@ §2.2a④ / C-09
+ 恢复臂额外要求 recovery_state != indeterminate；unknown 锁存不因 holder/epoch 变化而清除。
+ recovery_state==indeterminate 时，不重派可执行 release_dispatch、不返回 resumed/Proceed；
+ 由编排重建持久化 C-11 对账工作，新 broker 如参与，只提供无发布许可的只读 probe 结果。
+ happened/not_happened 按 C-11 固定映射，仍 unknown 保持 publishing；负向关闭须满足冻结静默条件。
@@ §2.2d
+ hello 重派扫描先按 recovery_state 分流：indeterminate → C-11 恢复；其他 publishing → 恢复臂。
```

**副作用**：未知一旦锁存，即使后续确证未发生，也按原设计关闭失败而非自动重新发布；这是本版已经选择的 C-11 语义，修订只是使其跨重启有效。若项目希望允许再执行，需重新统一两条路径和人工权限，不能靠重启隐式取得许可。

**测试/夹具**：CF-AUTH-17 扩成同 epoch/新 epoch 两行；indeterminate 后新实例 not_happened 不获 Proceed、按 C-11 关闭；部分发布→重启仍保留 unknown；C-11 pending 组合及静默 guard 不变；锁存提交前后 kill。

### C-05 — MINOR — A0 双向索引仍漏 SnapshotManifest

**位置**：01 §3.6、§7 A0。

**依据**：§3.6 定义 `SnapshotManifest = list[{repo_id, remote, commit, path}]`；A0 声明包含“全部具名类型（class、类型别名……）”，且“差集为空”。

**问题**：A0 无 SnapshotManifest。临时扫描 class/别名并补查正文内联别名，得到该差项。旧意见要求的 exhaustive 索引因而尚未完全成立；不能靠只扫描 Python fenced block 的 CI 漏掉它。

**候选 diff**：

```diff
@@ §7 A0
- §3.1：ActivationRecord。§3.3：CandidateRecord。
+ §3.1：ActivationRecord。§3.3：CandidateRecord。§3.6：SnapshotManifest。
@@ §5.1 / A0 双向 CI 说明
+ 抽取范围包括行内代码中的具名别名与正文定义，不能只扫描代码块内 class。
```

**副作用**：无运行时变化；此处不要求提前引入 v2.x 的 snapshot 扩展。**测试/夹具**：删除该索引条目时双向检查失败；§3.6 名称能唯一解析，既有全部命令/模型索引继续通过。

## 同步项：HLD v2.2 核心修订与 01 v0.12

本节不计入第二部分 NO-GO；01 明确仍以上游 v1.0+E-01 为准，不能因尚未引入新范围处罚它。下列 diff 是 HLD 修复并按程序生效后的迁移候选，不表示本轮可以跳过评审直接启用。新增 ImageReport、OptimizationPlan 等纯扩展由附录 B 跟踪，不重复登记为核心冲突。

### S-01 — MAJOR — E-02 的 paused/计时/唤醒与 01 的 gate-only 模型相冲突

**位置/依据**：HLD §4.3.4 的“全部未决等待……non_billable”与 paused 预算到期；01 C-07“仅剩 gate 等待”、C-13“queued ∨ running”、§3.4“排除 paused 与 publishing 时段”。

**问题**：不改契约则外部等待期间可能无限豁免预算，paused 下超时不能触发；sys.await_external 也不属于现有任务完成/重试路径。

**候选 diff**：

```diff
@@ 01 §2.1 / §3.4
- C-07：仅剩 gate 等待
+ C-07：仅剩 gate ∪ external 等待，且无可运行/在飞本地工作
- C-13 guard：queued ∨ running
+ C-13 guard：queued ∨ running ∨ paused（存在计费区间）
- 排除 paused 与 publishing
+ publishing 豁免；其余严格按 HLD §4.3.4 全集条件逐区间扣除，持久化后恢复不重置。
+ 新增 task_suspend、wake outbox/inbox 事务；同 task/dispatch 新 attempt，不消费 retry。
+ wake 消费在 paused 时转 queued；在 running 时仅调度新就绪工作，不把仍在飞的 Run 降回 queued。
```

**副作用**：状态名可保持，但暂停原因、计费区间和恢复责任需扩表；H-04/H-05 修订纳入后再固定 schema。**测试/夹具**：CF-SM/CF-REC 增混合 gate+resource+session、paused 到期、运行中旁支 wake、重复 outbox、重启不重置时钟；保留 publishing 豁免。

### S-02 — MAJOR — E-03 命令与 deferred 扩充不在 01 封闭枚举内

**位置/依据**：HLD §8.5 六条新命令、§5.2 deferred；01 §5.1 worker 命令封闭九条、CommandName 十九条，§4.3 ProbeOutcome 只有四值。

**问题**：如果只按 HLD 注入新句柄、继续用当前 contracts，合法请求会 framing/schema 拒绝；若实现绕过枚举直写共享存储则破坏 D6。

**候选 diff**：

```diff
@@ 01 §5.1 / A0 / §4.3
+ CommandName、命令注册表与唯一请求/响应模型共同追加：task_suspend、resource_lease_release、
+ image_commit、profile_put、remote_build_submit、remote_build_fetch_logs。
+ 新命令沿用 per-task/attempt 归属和 request_id 幂等；新增模型逐名进入 A0。
+ ProbeOutcome 增 deferred；按 HLD 会话等待协议保存调度责任，不消费 probe_attempts，
+ deferred 不解释为 confirmed_not_happened/unknown。业务 sys outcome 路由集仍不接收 sys.await_external。
```

**副作用**：属于 draft 破坏性扩展，需要契约版本/追溯/夹具一起升级；新增接口不能开放共享正式区写权限。**测试/夹具**：CF-IPC 逐条跨 task/跨 Run 攻击；registry↔CommandName↔A0 双向；deferred 重启/计时；旧纯本地效应矩阵保持。

### S-03 — MAJOR — 超时/incomplete 的成功守卫必须在核心迁移表统一

**位置/依据**：HLD §4.3.5 的禁成功要求；01 C-16 只检查 terminal outcome∈success_on，C-09/C-10 按冻结表映射；ResultEnvelope 无清单。

**问题**：若仅给 01 增两份结果清单而不改变核销前 guard，仍可能“发布成功但规则要求不得 succeeded”。先按 H-03 保留 publishing 的事实优先例外，再迁移，不能反向拿 01 当前冻结行为当缺陷。

**候选 diff**：

```diff
@@ 01 C-16 / decision_submit / C-09 / ResultEnvelope
+ terminal_success、发布审批及未核销授权消费均检查 HLD 定案的 timeout/incomplete 阻断谓词。
+ publishing 后新 timeout 仅 pending_register，C-10/C-11 released 映射不改。
+ ResultEnvelope 增 incomplete、retried 及超时记录具名模型，并逐名纳入 A0；
+ 已发布异常与全项通过在结果呈现上明确区分，首响应与重放一致。
```

**副作用**：核销前增加拒绝/收尾分支，不改 release_outcome 两值。**测试/夹具**：CF-SM-01 全状态矩阵、超时重试后提交审批、审批后核销前超时、publishing 超时与两 outcome 全组合；更新 Skill 结果快照。

### S-04 — MINOR — MCP/HTTP 的 request_id 域由 endpoint 改为共享操作

**位置/依据**：HLD §6.5“幂等域 = (principal, 操作名)，跨 MCP/HTTP 传输共享”；01 §0.2 request_id 为“(bearer principal, endpoint)”。

**问题**：只新增 MCP 传输而不改域，会让同一次操作的跨传输重试重复执行。该变化属于入口幂等契约同步，非 01 在旧 HTTP 范围内的独立缺陷。

**候选 diff**：

```diff
@@ 01 §0.2 / §2.7
- (bearer principal, endpoint)
+ (bearer principal, canonical operation)，MCP 与 HTTP 映射同一操作；request_id 是工具参数，非 JSON-RPC id。
+ 请求摘要含操作所寻址的 run_id 等资源标识及业务载荷，避免路径参数在跨传输投影时遗漏。
```

**副作用**：映射表及存储域需迁移，保留期不变。**测试/夹具**：CF-SKILL-01 跨传输同 id 同资源同载荷复用；不同 run_id/载荷同 id 拒绝；不同 principal 不串用；MCP 会话重连不改变操作幂等域。

## 覆盖范围与接受边界

| 检查面 | 本轮结论 |
|---|---|
| 冻结核心逐节对照 | 原编排、Ledger 单写者、效应键/版本、审批 point-of-no-return、特权 IPC 原隔离规则仍在；E-01 普通支配保留。E-02/E-03 已走显式勘误入口，但 H-03 是额外的冻结语义冲突，不能用“无放宽”概括所有新增规则。 |
| 三条新 DSL 规则 | ① AND-join 证明在同 cohort 完整到达及审批 CAS 下可成立；② 反例见 H-02；③ 旗舰普通路径反例见 H-01。声明删除 Benchmark 却保留 release_requires 会拒绝；仅改配置显式删除验证的边界已明示；保留优化时不得删 UT/Bench。 |
| 四份示例 | full_pipeline：①及 E-01/V-15 的生产者关系可满足，但③拒绝；campaign：required/independent、CI 的非空出口静态意图可满足，运行时撤销/预算见 H-02/H-08/H-09；另外两份无本版规范源，H-14。没有声称“四份已跑过”。 |
| 外部等待与并发 | 资源先授予、全量资源满足才取槽与无 worker 等待的方向可实现；全集计时和 paused 预算触发已明确；不可把逻辑终局当外部作业终止，H-04/H-05。实现还须保持 wake 在 running 不迁移、reap 后才复用资源的既有不变量。 |
| 构建/效应/安全 | D22 收紧成立；RPM 修复回流和 rpm_precheck 明确；镜像 Blob、效应标记+version、Gateway 会话隔离、CLI OS 约束有可测边界。未把具体 mic/Quickbuild/ClineSR 参数待补算缺陷。 |
| Benchmark/Optimization/Profile | 统一 MeasurementRecord、full-only、确定性计算的方向成立；可执行判定、计划生命周期与复用验收仍须 H-07/H-08/H-09/H-12。 |
| 板子/存储/SourceProvider | 板子回收不只依赖过期，缓存 single-flight、引用保护与 Profile 两区已有明确责任；Quickbuild 兜底见 H-06。D20 已把 VCS 中立化推迟到 P8 勘误，首期 git 形态不是缺陷；§7.6.4“核心不改”应按该明确后续边界理解，不代表 Perforce 已获无修改证明。 |
| 附录 B/分期 | 新增 [01] 主题已基本收录，普通支配迁移残句须 H-15。P0 先两文评审，P1/P2 核心及协议，P3 隔离/存储，P4 mock 全链，P5 核心契约，P6 Quickbuild、P7 真实统计与优化，P8 VD 的依赖方向可接受；缺失示例不能推迟到 P1 之后。 |
| 01 全文与恢复 | 原模型、series/activation、效应/Blob、数据密级、控制面与 conformance 全文复核；本轮主要差异的单 CAS、两值 outcome、D12 映射、持久化 epoch、静默合取已实质修正。NO-GO 来自 C-01/C-03/C-04，不能因上一轮“全部采纳”而略过组合故障。 |

修订后的复审仍应覆盖组合矩阵，尤其“优化→修复→撤销→空净变更”、并行超时与 publishing、broker 更替与未完成 intent/unknown 锁存。候选 diff 不授权直接修改被审文档，也不替代后续 01/07 的字段级与夹具交付。
