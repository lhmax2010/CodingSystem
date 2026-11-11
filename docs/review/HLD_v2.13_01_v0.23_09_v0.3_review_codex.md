# 第二十三轮定向核对 — Codex

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| HLD v2.13（A30、Q1–Q4 与 P0 同步） | **GO** | 0 | 0 | 0 | 0 |
| 01 v0.23（A3 本版条目及直接相交路径） | **GO** | 0 | 0 | 1 | 1 |
| 09 v0.3（W1–W6 的落实） | **GO** | 0 | 0 | 1 | 0 |

上一轮的两个阻断点已经解除：部分发布的正向观测不再被自动负向映射覆盖；HLD 与 09 已共同修订 P0 的分批定义。余下问题是终态字段不变式、变更摘要及 Demo 故障验收预期的局部一致性，不需要重新选择架构。

## 输入与验证边界

- 日期：2026-11-11。
- 仓库：`/home/linhao/Toolchain/development/CodingSystem`。
- 首先执行 `git pull --rebase`，返回 Already up to date；起始工作区干净。
- 输入 HEAD：`7652a57924d870eabc190643d7870ec3b5a759e5`。

| 输入文件 | SHA-256 |
|---|---|
| `docs/00_Framework_HLD_v2.13.md` | `db4507dade13c2d095dc61853d06ecb4dcda6a43d69193d46f78e5f8fe88d03d` |
| `docs/01_Contract_Spec_v0.23.md` | `9764feb15416b4752785d334e46de39bbe37502dd2a2199310f16e47597e0b78` |
| `docs/09_Phased_Dev_Plan_v0.3.md` | `d9aaa33bd3574ba5d083f180fc638eab36416f98f2aab0b2ba95b66d522a63dc` |

**读取范围**：三份当前处置表全文；上一轮三家原始报告，仅核对意见来源、方案、计数与非编号同步项；本轮三份文档的指定改动、直接相交的模型/迁移/测试，以及七项裁决所需的 HLD 段落。用上一版本与本版的文本差异定位改动，没有展开全文重审。没有读取其他评审方本轮意见。

**执行与资源边界**：所有 shell 命令均加 `nice -n 19 ionice -c3`；脚本均再经 `systemd-run --user --scope -p CPUQuota=100% -p MemoryMax=2G` 串行运行，用户 scope 可用。使用的命令为 `git pull --rebase`、`git rev-parse HEAD`、`git status --short`、`sha256sum`、`rg`（含查找 AGENTS.md）、`sed`、`cat`，以及受限 Python 文本差异/AST/小型谓词检查；报告写入与交付使用同样优先级限制的 `tee`、`git diff`、`git add`、`git commit`、`git pull --rebase`、`git push` 和提交信息核验。未运行构建、全量测试、索引、产品进程或 Quickbuild；未安装软件，未运行 PHP。

小型检查只验证文档谓词：AST 检查确认单个签名常量可豁免、隐式拼接完整程序及 f-string 不可豁免；72 格 C-11a 抽象组合覆盖历史锁存、双目标三态、manual_only 与静默条件；K5 的永久失资格/临时阻碍四组合恰有一个结果；另构造终态清除 strategy_managed 后的不变式反例。没有执行生成的源码或字节码。这些检查不是产品 conformance 通过证明，也没有验证真实主机的执行准入或部署工具能力。

## 负责人七项裁决：独立判断

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | **成立** | 并行不改变同 series 证据汇合与放行检查；超时必须留下 incomplete/retried 记录。节省并行耗时，但需维护两支证据的新鲜度，较慢分支仍决定等待时间。 |
| ② | Quickbuild 默认取最新 Profile 快照，在 Run 启动时固定 | **成立** | 固定一次解析结果可避免 Run 内基线漂移。§7.6.1 已明确这是本系统策略，不是 Quickbuild 的 Ref. Snapshot 缺省；推广状态与构建根差距按证据呈现。代价是更新的源码可能不匹配较旧构建根，并增加环境性失败；不承诺源码相对 HEAD 的落后上界。 |
| ③ | Profile 严格匹配，加小改动复用预案 | **成立** | 严格匹配是可检验的缺省；v2 是关闭的放宽预案，需实际非劣验证后启用。代价是初期重采较多，不能仅凭“小改动”口头判断复用安全。 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | “相关”须按模块登记、影响扩展与 always_run 解释，不能由 AI 任意删减；修复扩大范围时只增不减。代价是登记表维护与扩大后重验。Demo 的最小登记内容也受“使用到的条目进入第一批”约束。 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | 建议、修复和优化必须由可追溯的构建/测试证据评价，保护验证资产可以避免用改测试制造收益。代价是额外构建和存储；分析输出的采纳率不能冒充有事实标签的准确率。 |
| ⑥ | Quickbuild 可指定 Base CL，否则默认最新，并读回核对 | **成立** | 固定请求值、证明实际输入、发现 mismatch 后显式失败，能把“想构建什么”与“实际构建什么”区分。仅在已验证能力内启用；输入未获证明时改配本地后端须新 Run。代价是首期远程能力可能受限，不能靠人工确认把不可比变为可比。 |
| ⑦ | 超时后重试成功可以发布，但须审批人逐条确认 | **成立** | 重试成功可以补足当前证据，但原超时不能消失。当前 series 证据链逐条确认并绑定内容 digest，被取代轮次汇总可见，核销再复核；这样开发者和审批人都知道发生过超时。代价是审批操作增加，证据变化须 gaps_changed 关闭后新建 Run。 |

D23 不引入 PHP、人力基线以及总部方案确认随 12-29 Demo 进行均作为前提接受，不评价选择本身。

## A. 处置来源、计数与逐项落实

### A1. 计数与采用方案

| 处置表 | 原始编号意见数 | 归并核对 | 结论 |
|---|---|---|---|
| HLD_v2.12 | Kimi 1 + Codex 1 + CC 4 = **6** | Q1 合并 Codex H212-01 / CC H212-02；Q3 合并 Kimi H22-01 / CC H212-03；Q2、Q4 单项，合计 **4**；CC S1 为非编号同步，不混入计数 | 正确 |
| 01_v0.22 | Kimi 1 + Codex 2 + CC 5 = **8** | Z1 三条归一、Z3 两条归一，其余单项，合计 **5**；“2 处合并”指两个合并组，并非只减少两条 | 正确 |
| 09_v0.2 | Kimi 1 + Codex 3 + CC 6 = **10** | W1 四条归一，W2 两条归一，W3–W6 单项，合计 **6** | 正确 |

各家级别数量与原报告结论表相符。Q1 的完整 pyc 摘要及可信清单来自 Codex，安装前缀只读与不写 pyc 来自 CC；Q2 的 AST/注释判据来自 CC；Q3 的完整调用承诺与进程枚举分别对应 Kimi/CC。Z1 三家的负向守卫、顺序和人工优先级均可在原文找到，Z2/Z4/Z5 来自 CC，Z3 的算法与校验拆分分别对应 Codex/CC。W1 采用 CC 的正式修订 HLD 方案，同时回应 Codex 的“两文必须同口径”要求；**这确实改变 P0 的条件，不是原 P0 全量扩展条件已经满足**。本轮两文已共同修改，取舍成立。W1 的逐条键、留存与检查点对应 Kimi；W2–W6 来源也吻合。

最新三份处置表没有独立的“记录更正”小节；不把上一轮报告引用的更早更正当作本次新增事项。01 处置表开头“人工裁决分支……已经闭合”是过宽的概括：原 Codex C22-01 仍要求历史正向事实优先级，CC C22-02 仍要求证据覆盖；其后 Z1/Z2 已明确记载并实际处理这两点。本核对按具体处置与原始意见判断，不把概括句当作三家对所有人工分支无保留确认的证据。

### A2. HLD：Q1–Q4 与非编号同步

| 项 | 正文落点 | 核对 |
|---|---|---|
| Q1 | §11.2、§11.3 v2.13、B-7 部署契约 | 以完整 pyc digest 约束实际字节，可信清单含源 digest/source_hash/解释器/cache tag/编译参数；同时检查 checked 标志与对应关系。只读前缀及 PYTHONDONTWRITEBYTECODE 已写。未登记 pyc 不享受文本豁免；“按普通文件扫描”不应解读为所有无命中信号的第三方 pyc 也必须无条件拒绝。原反例中含违规信号的替换正文会被拒，免除旁路已关闭。 |
| Q2 | §11.2、§11.3 | 隐式拼接按 AST 合并值比较、JoinedStr 不豁免、注释去符号/首尾空白后比对签名；四个正反例已列。 |
| Q3 | §11.2、§11.3、B-7 | 全部宿主产品进程及子孙纳入执行准入和记账，列出编排/worker/Approval/Gateway/MCP/broker/launcher 子进程；直接 spawn 哨兵反例已加入。业务构建步骤仍只在 D22 隔离边界内排除，不能把产品辅助程序标签改成业务内容逃避。 |
| Q4 | D23、§11.2、§11.3 | 现行 HLD 从部署策略版本绑定取得，Run 创建时复核例外在现行清单中且未到期；不是读取任意最新仓库文件或信任插件自报。 |
| P0 同步 | §13 P0、09 §3 M0b/§3.1 | 第一批是 P0 条件；第二、三批分别服务后续阶段。mock 使用的核心 schema 也须先评审，不能以 provisional 完成 gate。两文一致。 |

HLD 本轮没有新增问题。完整 digest 豁免不替代其他 PHP 判定信号；运行时不生成 pyc 与不可写前缀共同约束部署。执行准入的具体 OS 机制仍须在 Demo 主机验收，不把本轮文档 GO 当作已实测生效。

### A3. 01：Z1–Z5

| 项 | 正文落点 | 核对 |
|---|---|---|
| Z1 | C-10a/C-11a、§2.2a/§2.2d、AuthorizationRecord、§5.1、CF-AUTH-20j | 自动负向映射与再次许可均受锁存约束；合法报告同事务 OR 后决定出口；C-11a 冲突转 manual_only；人工全 absent 不再压过历史 appeared。安全问题已修复；A3 对 C-10a 的描述见 C23-02。 |
| Z2 | AdjudicationEvidence、§5.1、CF-AUTH-20j | unknown 的负向裁决需 target_refs 并集恰等于全部目标；probe_report 引用由编排从已落账报告的 absent 项生成，不能由运维伪填。外部证据由运维逐目标声明，其真实性仍属人工证据责任。 |
| Z3 | ReleaseTarget、两类报告、ReleaseProbeDispatch、RunSummary、CF-AUTH-17d/20j | target_ref 按 §0.1 canonical_json 的 SHA-256 派生；manifest 去重；②查内部一致性/非空/重复，⑤查与授权 manifest 双射；⑤失败落首响应但不落观测、不改锁存。probe_targets 全量，summary 有逐目标字段。 |
| Z4 | K4③/K5、S2、CF-AUTH-20i/20o | 暂停只拦未放行项；同 request_id 重送不重开期限。K5 明文③→②→①，失资格不会被暂停掩盖。 |
| Z5 | ReleaseTaskState、hello 扫描、CF-AUTH-20k | 置位/清除与 manual_only 回契约通道已写；hello 只筛 strategy_managed=false，仍经统一入口。终态与无条件不变式的交叉缺口见 C23-01。 |

版本为 `1.0.0.dev12`，与新增字段及破坏性报告校验变化一致。R22 格覆盖报告校验、锁存、证据覆盖、暂停重送及策略字段主要变化；需要补的终态组合见 C23-01。

### A4. 09：W1–W6

| 项 | 正文落点 | 核对 |
|---|---|---|
| W1 | §3 M0b、§3.1、§4.4 | 与 HLD 的正式分批修订一致。第一批补 Demo 字段及最小服务契约，第二批补 P4 mock 骨架；11-20 前逐条编号入仓，每条恰属一批并列使用方/通过/实现/验收日期。此表是有截止日的待交付物，不冒充已存在。 |
| W2 | §4.2/§4.3/§4.4/§4.6 | 心跳/阶段期限仅检测告警，编排重启给宽限期；孤儿回收、构建 probe、同实例 intent 重送与授权过期已列；按是否核销分流，人工处理不允许直接改 Ledger；Approval/broker 分别降级。kill 用例的通用预期需按提交边界拆开，见 P23-01。 |
| W3 | §4.5、§4.6 两处回放 | 来源须绑定安全切片验收 id，出内网逐条核密级；无合格记录用 FakeLLM，并不计真实 AI 自动修复。 |
| W4 | §4.2 安全切片、W1、§4.6 | 首次部署前验证安装集/子进程观测/全部进程执行准入并留 approved_digest；不通过不部署，不用一次观测代替准入。 |
| W5 | §10 | 对照表与开发状态文件同目录；P0–P2 在 M0a 前、P3–P4 在 1-22 前、P5–P7 在第三批通过前完成。固定路径的具体文件名属于这项待交付工作，不在本轮重复索要新设计。 |
| W6 | §4.1 | 已改为“除 VD 外”，VD 仅 M3；M2 的 AutoFDO 范围、Quickbuild 显式延期与受控仓发布边界已写。 |

日期链成立：11-20 是映射/输入检查点而不是完整 P0；第一批 12-11、Demo 12-29、M0b 12-31；第二批 1-22 在 P3/P4 gate 前；第三批两日期服务 P5–P7。W3/W4 早于第一批通过的问题已明文处理为顺延能力或缩减 Demo，不能用 provisional 顶替评审。总部确认与人力不重评。

## B. 01 本轮相交路径走查

以 **L** 表示授权的 observed_any_appeared。下表的“受理”均指通过连接、幂等、状态与目标双射校验并提交的报告，不包括被拒载荷。

| 反例/交叉条件 | 现文唯一处理 |
|---|---|
| 对账部分出现，之后远端撤回，全 absent 只探测；原 holder 已静默 | 首报告 L=true；第二报告不能负向映射，C-11a 同事务 manual_only、告警；只能 C-11，不能再发 execute。 |
| 只探测部分出现，随后旧的全 absent 报告迟到；holder 未静默 | L 仍为 true，冲突分支先处理，不能以 retire_requested 后重新探测的方式绕过 L。 |
| 上述两个序列在首报告事务提交前/后重启 | 提交前回滚并按幂等重投；提交后 L 持久化，不由 epoch 更替、后续 absent 或重启清除。负向判定使用同事务并入后的值。 |
| manual_only 或非 manual_only，已记录部分出现；强制 probe 全 absent/unknown/失败 | 负向人工裁决均被历史正向事实禁止；允许 keep_unknown 或按证据规则 confirm_released。auto_probe_suspended 不取消运维强制探测，也不清锁存。 |
| L=true 的 C-10a confirmed_not_happened 防御夹具 | §2.2a④ 转 indeterminate，既不 ReconcileProceed 也不 release_failed；不是正文定义的直接 manual_only，摘要误述见 C23-02。 |
| L=false、全 absent、holder 已静默，非 manual_only | C-11a 保留正常 release_failed 映射。manual_only 下仍只留证据，不自动映射。 |
| 两目标、无正向历史、强制 probe unknown，证据仅覆盖一目标 | confirm_not_released 拒绝；补齐全部目标且静默才可受理。伪填 probe_report.target_refs 不能扩大覆盖。 |
| targets 空/重复/与 probe 矛盾；或集合缺项/额外项 | 前组②拒绝且不占 receipt；后组⑤拒绝并落 receipt；均不修改 L。集合重排不改变身份，单目标仍是一元素双射。 |
| 已放行 intent 未 ACK，之后暂停、重启 | 同 request_id 重送，期限不刷新；尚未放行者才受 K4③ 暂停。 |
| 暂缓 execute 同时 manual_only 与暂停；合法项只是临时无独占许可 | 前者③作废；后者②保留并由持久化唤醒推进。epoch 变化走替代协议后再复核，不直接跳过 K5。 |

“乱序”保证是已受理正向事实不能被后到负向报告抹除，不能理解为预测尚未收到的远端事实。终态之后的新远端证据沿已有 correction 机制处理，不用本轮锁存承诺取代远端探测一致性或 post-close correction。正常 release_outcome 的逐目标呈现扩展已经登记在 09 第一批，见同步项，不重复报告。

## C. 本轮问题及候选修改

### C23-01 — MINOR：终态清除 strategy_managed 与无条件 isolating 不变式冲突

**位置**：01 §2.5 ReleaseTaskState.strategy_managed（第352行）；§2.2d recovery_mode 迁移；CF-AUTH-20k R22。

**原文依据**：字段注释“**task 终结或置 manual_only 的同一事务置 false**”；紧接着“不变式：**recovery_mode = isolating ⇒ strategy_managed = true**”。迁移规则对 isolating 写“**保持至 task 终结**”，没有给 Ledger 终态记录定义新的 recovery_mode。

**具体反例**：隔离成员以 `recovery_mode=isolating, strategy_managed=true` 正常发布结案。终局事务按新规则清 managed=false，保留持久化任务行的最后 recovery_mode=isolating。该正常终态随即违反无条件不变式，CF-AUTH-20k 又要求此组合一致性检查失败。一个实现可能错误回滚合法关闭，另一个可能偷偷把历史 mode 改成 active。问题在终态不变式的定义域，既不需要新恢复状态，也不影响已修复的发布安全守卫，定为 MINOR。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.23.md §2.5 ReleaseTaskState
- 不变式：recovery_mode = isolating ⇒ strategy_managed = true
+ 活跃任务不变式：task 非终态 ∧ recovery_mode = isolating ⇒ strategy_managed = true。
+ task 终结时 strategy_managed=false；终态行可保留最后 recovery_mode 作审计，
+ 不再参与上述活跃不变式或任何派发扫描。manual_only 为非终态时仍按既有规则清零。
--- CF-AUTH-20k R22
- recovery_mode = isolating 而 strategy_managed = false → 一致性检查失败
+ 非终态 task 的 recovery_mode = isolating 且 strategy_managed = false → 一致性检查失败；
+ isolating task 正常 H/F 终局或授权过期关闭 → managed 同事务清零，
+ 终态记录保留历史 mode 仍通过一致性检查，hello/周期扫描不再派发它。
```

**副作用**：收窄不变式至它实际管理的活跃调度域；不增加枚举、不丢失历史，也不放宽活跃任务独占许可。

**测试/夹具**：CF-AUTH-20k 增正常 H/F、draining 授权过期、结案事务前后重启；提交前仍是有效隔离成员，提交后 managed=false 且不可派发。保留非终态 false 组合拒绝与转 manual_only 后只探测测试。

### C23-02 — NIT：A3 把 C-10a 的冲突出口也概括成直接 manual_only

**位置**：01 A3 v0.23 条（第935行），对照 §2.2a④ confirmed_not_happened、C-11a 与处置 Z1。

**原文依据**：A3 写“**C-11a 自动负向映射与 C-10a 未发生分支在锁存为真时不作负向映射、不授予执行许可，记录冲突、告警并转 manual_only**”；§2.2a④ 实际为“**recovery_state := indeterminate、响应 ReconcileRecorded(indeterminate_recorded)**”，没有置 manual_only。处置 Z1 的 C-10a 防御条也只规定 indeterminate。

**具体反例**：直接构造 CF 的 L=true、reconcile_required 防御夹具，提交合法全 absent 对账。按正文仍可在 indeterminate 通道等待后续全正向结果；按 A3 应已进入只经人工收尾的 manual_only。安全禁令一致，但“唯一出口”及是否允许以后自动正向结案的测试预期不同。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.23.md A3 v0.23
- C-11a 自动负向映射与 C-10a 未发生分支在锁存为真时不作负向映射、不授予执行许可，记录冲突、告警并转 manual_only
+ 锁存为真时，两条路径均不作负向映射、不授予执行许可并记录冲突、告警：
+ C-11a 同事务置 manual_only、只经 C-11 收尾；
+ C-10a 防御分支置 recovery_state=indeterminate，响应 indeterminate_recorded，沿既有只探测/裁决通道处理
```

**副作用**：仅让摘要忠实于规范正文和采用方案，不额外增加一次人工化迁移。若要两处都 manual_only，必须另行同步迁移及 CF，不能只以摘要暗改。

**测试/夹具**：CF-AUTH-20j 的 C-10a 防御格明确同时断言 recovery_state、recovery_mode 保持值、响应与写调用零次；C-11a 格继续断言 manual_only。防御状态可以直接构造，不声称正常状态机一定可达。

### P23-01 — MINOR：新增 kill 验收把 outcome 已提交与尚未提交统一要求为 publishing

**位置**：09 §4.3 原版验收（第138行），直接相交的 §4.2“失败即停”和“不自动结案”。

**原文依据**：“**分别在构建中、审批中、intent 前后、核销前后、outcome 前后 kill broker 或编排**”，随后统一要求“**未核销者不进入 publishing、授权到期……关闭；已核销者保持 publishing 并告警；无自动重派、无自动结案**”。§4.2 又完整实现 broker 正常路径与 DispatchReceipt 恢复 (a)。01 C-10 正常 outcome 提交即关闭。

**具体反例**：正常 `release_outcome=released` 的 Ledger 事务已提交，ACK 发送前 kill 编排。授权已核销，但 Run 已 closed(succeeded)，重启只能保留终态/重放 receipt，不能回到 publishing。另一个分支是仅 kill 编排、broker 仍健康，同 epoch 重连并补交合法 outcome；这是计划保留的正常续跑，不能一概按 broker 已失联处理。构建/审批早期尚无授权的 kill，也不能套“授权到期关闭”。新增测试时点正确，单一预期却不能覆盖这些提交边界；这是验收矩阵问题，不要求提前实现整套 broker 恢复。

**候选 diff**：

```diff
--- docs/09_Phased_Dev_Plan_v0.3.md §4.2 失败即停
- 不自动结案。
+ 不以 broker 失联本身伪造远端结果或走未实现的恢复/裁决出口；
+ 已实现的未核销授权过期关闭、同实例正常 outcome 的终局映射照常有效，已提交终态不得回退。
--- §4.3 kill 验收条
- 已核销者保持 publishing 并告警；无自动重派、无自动结案
+ 以被 kill 的进程及最后成功提交点分别验收：
+ (a) 构建/审批中尚无授权：验收既有构建效应 probe、gate/outbox 恢复，不套授权过期分支；
+ (b) 授权存在且未核销，broker 失联：停止派发，不进入 publishing，到期按可见原因关闭；
+ (c) 已核销、无终局提交且 broker 已失联：保持 publishing、告警，不自动恢复发布、不伪造结果；
+ (d) outcome 终局已提交：重启保留同一 closed 结果，重放不重复执行；
+ (e) 仅编排重启、同一 broker 健康且未进入故障分支：宽限期 hello 与 (a) 出向恢复照常，
+     后到的合法正常 outcome 只映射一次，不把正常续跑误判为 broker 故障恢复。
```

**副作用**：验收记录多列“故障进程、提交边界、是否有授权、是否已有终局”；不增加 broker 替代实例、只探测或人工裁决的 Demo 范围，不放宽安全切片。

**检查点/验收**：W6 把上述五类写入场景断言；核销、outcome 各做提交前/提交后 ACK 前 kill，分别核验 Ledger 与模拟发布写计数。12-22 预演仍可只展示构建/审批/publishing 三个画面，完整边界测试另留证据。outcome 已提交分支必须保持 closed 且写计数不增加。

## D. 同步项与已登记事项

无新增未登记的 HLD→01 同步缺口。HLD B-7 已登记本轮 AST 签名口径、pyc 制品清单、全部进程执行准入/exec 记账以及现行版本绑定/Run 创建复核。分批不是从 01 v0.23 的核心基线中偷偷要求全部 v2.x 功能，第一批及后续阶段按 09 的明确 gate 推进。

正常 release_outcome 的可选逐目标观测及 RunSummary 呈现已由上一轮 CC 非编号 S2 登记，09 §3.1 第一批已接受；不再作为新缺陷重复报告。映射表、gate 对照表和实际部署验收证据都是已有截止日/首次使用门槛的交付项，本轮不把尚未到期等同于漏设计。

## E. 基线判断

HLD v2.13 可以定稿：本轮四项 D23 修订及 P0 同步已落实，没有新增阻断。01 v0.23 可以作为核心契约开发基线，C23-01 的活跃/终态不变式限定应随 contracts 与 conformance 实现补齐，C23-02 校准摘要即可；不需要再把已降为策略的归因问题拉回核心。09 v0.3 可以作为排期基线，P23-01 应在 W6 验收脚本定稿前修正；使用到的契约须先通过、部署安全切片须先验收，以及超期按既定检查点顺延或缩减范围，均继续作为该基线的有效约束。
