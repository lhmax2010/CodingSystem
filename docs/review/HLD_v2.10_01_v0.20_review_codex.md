# HLD v2.10 / 01 v0.20 第二十次定向复审 — Codex

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| HLD v2.10（仅 A27） | **GO** | 0 | 0 | 2 | 0 |
| 01 v0.20（仅 A3 的 v0.20） | **NO-GO** | 0 | 2 | 1 | 0 |
| 新增同步项（不计入结论） | 无；已登记内容不重复报 | 0 | 0 | 0 | 0 |

**范围调整判断：成立，但本版尚未完整满足调整的前提。** 将根因归属降为可替换策略是合理选择；K2 尚漏掉自动计划性回收循环，暂停探测后的裁决还需消除“unknown”与实际确定结果的优先级歧义。这两点属于必须保留的恢复上界与事实约束，不要求把准确识别毒丸重新升为契约保证。

## 负责人七项裁决：独立判断

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时显式报告、不得当通过 | **成立** | 两路的同 series 汇合与报告义务可以保证并行不降低验证要求；未覆盖的超时仍阻断发布。代价是保存两路及替代轮次证据，不能仅凭较早完成的一路批准。 |
| ② | 默认最新 Profile 快照，在 Run 启动时固定 | **成立** | 固定选择可使同 Run 内基线与候选使用一致输入；“最新”是本系统策略，不等于 Quickbuild 服务缺省的 reference，也不意味着最稳定。代价是可能增大快照与构建根差距，需保留实际读回和双编号，不能承诺落后量上界。 |
| ③ | Profile 严格匹配，加小改动复用预案 | **成立** | 严格策略作为缺省，放宽策略以兼容检查、热点覆盖与非劣证据为前提，能把重采成本与结果可信度分开决策。代价是先收集工具链数据，缺证据仍重采；不能让 AI 自行决定陈旧数据是否可用。 |
| ④ | 每 Run 有目标模块，只跑相关模块 | **成立** | 按真实改动与显式关注模块确定范围，未登记拒绝、真实改动使范围只增不减，并保留 always_run 冒烟集。这比任意选择少量用例更可执行；代价是维护模块登记及跨模块依赖，撤销也不能用来缩减已增长的验证义务。 |
| ⑤ | 用每轮测试和多版本报告检验 AI | **成立** | 客观验证决定通过，分析与建议可单独衡量，保留失败和被撤销版本能避免只展示最佳结果。代价是构建、测试和存储开销；测试覆盖不足仍须如实呈现，不能把报告等同于无限范围的正确性证明。 |
| ⑥ | 可指定 Base CL，否则默认最新，并读回核对 | **成立** | 明确输入选择，再以读回证明实际使用的输入，比仅相信请求回显更可靠。能力未证实、实际输入不匹配或不可比时必须拒绝相应用途；代价是额外预检及本地后端的替代成本。 |
| ⑦ | 超时后重试成功可发布，审批人逐条确认 | **成立** | 逐条确认当前 series 证据链及引用基线的重试，旧轮次首屏汇总，确认绑定内容 digest 并在核销重检，能同时保留实际成功与超时历史。代价是审批信息量和证据保留；不赞成要求逐条确认所有已被替代轮次，现有收窄没有隐去它们。 |

以上判断基于这些约束之间的关系与成本，不以“前轮已通过”为理由。D23 是另一个负责人前提，本报告不评价语言选择。

## 输入、边界与资源约束

日期：2026-11-06。首次 `git pull --rebase` 返回 `Cannot rebase onto multiple branches`；工作区干净，显式执行 `git pull --rebase origin main` 成功，返回 Already up to date。固定输入 HEAD：`d18d74e7f877baf1c78847c457af9a09c282fa03`。

| 输入 | SHA-256 |
|---|---|
| `docs/00_Framework_HLD_v2.10.md` | `162e66c18714e65c02c8a6349262b3cb0a614773683884f451537c955fd11217` |
| `docs/01_Contract_Spec_v0.20.md` | `ac272a796149041349de6462ac036d3d162bf49e90a5f390b535f912b9d80da0` |
| `docs/review/HLD_v2.9_review_disposition.md` | `319c7704e39291951c05ed1febf294b1ecefee4e8b574f27884fa66a7f7e2986` |
| `docs/review/01_v0.19_review_disposition.md` | `17f1f30f75be7e38244c7492d0bcce82fc9eeea080b5329983151aa9fa34360d` |

只核对 A27、A3 v0.20 及直接相交条款；读取上一轮三家意见用于处置、方案来源和计数核对，不读取本轮其他意见。不访问或探测 Quickbuild。命令均通过 `nice -n 19 ionice -c3`；差异提取、AST 与小型谓词推演还通过 user scope 限制 CPUQuota=100%、MemoryMax=2G，串行执行。没有启动构建、全量测试或索引。

验证为文档推演与小型字段/谓词检查，不是产品实现的 conformance 运行。AST 已确认 RetirementEvent 含三份 task_id 字段及 strategy_version，IsolationChannel 不再含快照；预算演算显示相同 U 在六次任务域事件后暂停，而十二次 isolation_drain 后 affected_count 仍为零；NullAttribution 的多绑定事件达到 affected 上限时，按 K4 应登记两个 task 并熔断。下文提供完整场景与修法。

## A. 处置落实、方案来源与数量

### HLD：R1–R3

| 项 | 来源核对 | 落文与判断 |
|---|---|---|
| R1 文本分类、负向夹具 | Codex H29-01 提出按用途分类；CC H29-01 第 1–3 点提出受控豁免及运行时生成负向文件。合并采用的归属准确。 | D23、§11.2/§11.3 已写仅免文本标记、其他信号仍判、不接受插件自报、真实负向文件不入仓。方向落实；文件级“不得作为解释器输入”仍会误伤 Python 扫描器/测试，H210-01。 |
| R2 主机范围 | CC H29-01 第 4 点提出安装前缀、运维助手闭包及业务目录排除；Kimi H29-01 提出无关预装包只列报告。 | §11.2/§12 已落实，并把实际调用的预装工具纳入闭包，比仅按 deploy 是否安装更完整。没有把业务 buildroot 整体当产品依赖，也没有把产品调用的预装工具排除。 |
| R3 例外、策略升级、漂移 | Codex H29-02 要求 E0 记录不是许可、先正式修订前提；CC/Kimi 提出例外登记形态；CC H29-02 提出策略重扫和环境 digest。 | D23、§11.2/§11.3、B-7 已落文。当前前提下例外清单不可自行生效，审批记录不替代扫描。digest 检查还须明确“当前实际值”的采集，H210-02。 |

### 01：Z1–Z7 与范围调整

| 项 | 来源核对 | 落文与判断 |
|---|---|---|
| Z1 只探测快照与停止出口 | CC C19-01 建议增加只探测快照、上限及探测不可用的人工出口；其根因归属部分允许转实现期。 | 新 probe_task_ids、K2/K3、auto_probe_suspended、CF-AUTH-20q 已落实。使用统一 affected_count 代替 CC 的专用 probe_fault_count 是明确的设计整合，不是假称逐字采纳。人工新分支需 C20-02。 |
| Z2 预约释放 | Codex C19-01 的所有释放事件、selection_seq CAS、持久化唤醒和固定批次。 | K5、S2、CF-AUTH-20k 已落实，正常完成不再依赖下一次故障才释放。原问题关闭。 |
| Z3 暂缓 probe 分型 | Codex C19-02 的 execute/probe 两支、probe 不要求 Q、不写执行阶段。 | K5、CF-AUTH-20o 已落实；关闭两类作废、U/M 只作废 execute 的主干一致。原问题关闭；新增暂停标记的例外路径仍须明确。 |
| Z4 熔断 | Codex C19-03 提出持久化窗口、正常结案清零及保守保护定位；CC C19-02 提出 deadline 仅告警。 | K4、CrossTaskBreaker、CF-AUTH-20i 已落文；consume/resumed 不再清零。额外把“本事件达到 K3 上限”者入窗口，是支持 NullAttribution 的必要整合；夹具仍残留相反断言，C20-03。 |
| Z5 模型字段 | Codex C19-04 要求 bound_task_ids 移回事件并做字段归属测试。 | §2.5、A0、CF-AUTH-20r 落实，AST 验证通过；新增 probe/charged/strategy 字段均属于事件。 |
| Z6 不依赖不存在的取消命令 | CC C19-03 提出等报告或 probe_drain_timeout 后计划回收。 | S2、CF-STR-03 落实；没有暗增取消 RPC。但与 K2 的零计数回收组合后仍可重复循环，C20-01。 |
| Z7 旧 epoch held 唤醒、非法 deadline | CC C19-04；Codex 走查也说明空执行快照的有效 deadline 不可达。 | K5 扫全部 held，再按 epoch 替代；任务域判定明确空执行快照 deadline 拒绝提交并告警；CF-AUTH-20h/o 覆盖。落实。 |

**范围调整的来源表述准确，但“照 Codex 条件执行”是验收目标，不能视为已自动成立。** 上轮三家均支持或有条件支持转实现期；本方明确要求恢复上界、持久化派发和安全底线留在契约。将 S1–S3、CF-STR-01–04 标为非规范是正确落点，本轮只报告其与 K 条款发生的直接冲突，不重审归因精度。

**数量核对准确**：HLD 为 Codex 2 MINOR、Kimi 1 MINOR+1 NIT、CC 1 MINOR+1 NIT，6 条编号意见归并 3 题；01 为 Codex 3 MAJOR+1 MINOR、CC 1 MAJOR+2 MINOR+1 NIT、Kimi 0，8 条归并 7 题，其中 Z4 合并两家各一条。Z1 分出多个契约动作不改变原编号数。dev8→dev9、A3 与模型扩展一致。

## B. HLD v2.10 问题

### H210-01 — MINOR：对“承载文件”禁止解释器输入，仍会拒绝含检测签名的 Python 扫描器与测试

**位置**：HLD §11.2“仅命中文本标记时的分类”（第 877 行）、§11.3 无 PHP 自扫描用例。

**原文依据**：豁免对象包含“扫描器自身的规则表与单元测试”，但“**这些文件不得有可执行位或 php shebang，不得被任何交付物用作入口、模板或解释器输入**”；无法确认分类仍拒绝。§11.3 又要求仓库根目录自扫描通过。

**问题/反例**：一个普通 `test_php_scan.py` 包含 `marker = "<?php"`，没有可执行位和 PHP shebang，pytest 仍会把这个 Python 文件交给 Python 解释器；扫描器源码内保存该签名也一样。文本片段是非执行的 PHP 签名，但承载它的 Python 文件是可执行程序。按文件级限制不能将其归类，仍回到文字误报。此合并忠实延续了上轮建议；本方旧候选也未充分区分片段与承载文件，不能因曾由本方提出就默认正确。

**候选 diff**：

```diff
--- docs/00_Framework_HLD_v2.10.md §11.2
- 这些文件不得有可执行位或 php shebang，不得被任何交付物用作入口、模板或解释器输入
+ 对文档、合成清单等纯数据文件，保留上述禁止作为程序入口/可执行模板的限制。
+ 对受审阅的非 PHP 扫描器/测试源码，豁免以命中的字符串常量或注释片段为单位：
+ 确认该片段仅为检测签名/期望值，不作为 PHP 程序或可执行模板输入；
+ 不因承载文件由 Python 执行而拒绝，也不豁免同文件中的其他信号。
+ PHP shebang、PHP 源文件/模板、真实 PHP 包与运行时依赖仍拒绝；
+ 无法确定命中片段用途时拒绝，不对路径或 .py 后缀整体放行。
--- §11.3
+ Python 扫描器及 pytest 源码含 PHP 标记字符串/注释时自扫描通过；
+ 将同样文本注册为 PHP 入口、解释器输入或可执行模板时拒绝。
```

**副作用分析**：分类器需要识别少量受控语言的文本上下文，不能仅凭后缀白名单。真实 PHP 不因夹具、docs 或“扫描器”名称获得豁免；不需要引入 PHP 来做负向测试。

**配套测试/夹具**：增加无 executable bit 的 Python 单元测试文件、实际 Python 扫描入口两个正例；PHP shebang、伪装为 `.py` 的 PHP 源、把签名转作 PHP 程序输入的负例；原有 phar、composer、传递依赖和基础层检查保留。

### H210-02 — MINOR：验收时保存的 digest 与通过扫描的 digest 比较，尚未规定如何取得当前安装状态

**位置**：HLD §11.2“例外与复核”、§11.3 的安装集漂移用例、B-7 部署契约（第 984 行）。

**原文依据**：“**deploy 安装集的 digest 在验收时记录并写入 execution manifest……Run 创建时与最近一次通过扫描的 digest 比对**”，并声称“**运维绕过 deploy 直接安装的依赖因此会被发现**”。扫描范围还包括产品安装前缀和实际调用的预装工具闭包。

**问题/反例**：如果两个被比较值都来自上次验收，它们会始终相等。运维在产品安装前缀内替换一个工具文件，或直接安装产品会调用的新依赖，deploy 清单及旧验收记录都不变；只计算声明包集合/记录 digest 也检测不到实际变化。这里不要求扫描整台工作站，更不应把无关预装 PHP 判成违规。所缺的是当前实际输入清单的来源、与通过扫描清单的同域比较。D12 的复核原则支持这一补充，但不能替代新字段的计算口径；定为局部落地明确化 MINOR。

**候选 diff**：

```diff
--- docs/00_Framework_HLD_v2.10.md §11.2
- deploy 安装集的 digest 在验收时记录并写入 execution manifest……比对
+ deploy 验收保存已通过扫描的 DeploymentInventory 及 approved_digest。
+ 清单覆盖本节规定的实际安装集、产品安装前缀文件与已解析的实际调用工具闭包，
+ 记录组件身份/版本、实际文件内容摘要、符号链接目标及闭包成员，按统一规范化
+ 规则计算 digest；不混入业务目录和未被产品使用的预装包。
+ 每次 Run 创建前由可信部署侧读取当前实际状态重新生成 current_digest，
+ 不得从 deploy 声明清单、旧 execution manifest 或 approved_digest 复制。
+ 当前值与同策略版本的 approved_digest 相等，且例外未过期，才创建 Run，
+ 并 pin current_digest；不一致或无法读取则拒绝并要求重新验收。
+ 合规依赖更新也先重扫、更新批准记录，再允许创建，不自动接受新摘要。
--- 附录 B 第 7 组部署契约
+ 登记 DeploymentInventory 的规范化输入、当前采集来源和 approved/current
+ 比较契约，与 ExecutionManifest 的安装集 digest 字段配套形式化。
```

**副作用分析**：Run 创建增加受控安装状态核验成本；可以采用可信且能检测外部变更的快照机制，但不能仅缓存旧声明。产品范围内合法运维更新会触发重验收，无关主机软件或业务数据变化不应触发。

**配套测试/夹具**：保持 deploy 清单与旧验收文件不变，替换安装前缀内工具内容、更新被实际调用的预装工具闭包，各自应拒绝新 Run；保持当前状态不变而重启仍通过；无关预装包和业务 buildroot 变化不失败；采集失败、例外过期、策略变更未重扫均拒绝。

## C. 范围调整与 K1–K6 覆盖评估

| 必须保留的内容 | 当前落点 | 判断 |
|---|---|---|
| 执行权栅栏、一次核销、恢复先静默后对账、U 锁存 | C-09/10/10a、§2.2a/d 仍为规范条款 | 保留；不能因 S1–S3 非规范而替换。 |
| M 后无自动 execute，只探测只读 | K3、K5、C-09/④/C-11a、broker 只读 adapter | 保留，未发现新增合法自动发布分支。 |
| 裁决不违背远端事实 | §5.1、C-11、K3 新暂停分支 | 原限制保留，但新“强制 probe 按 unknown”与显式成功探测的优先级不清，C20-02。 |
| 每 task 有界自动恢复及安全停止 | K2/K3 三上限、实际 consumed 分流 | 任务域事件内独立于策略成立；自动 controlled_reclaim 循环不受约束，C20-01。不能将 M 等同于 Run 已关闭。 |
| 全局停止出口 | K4、launcher、CrossTaskBreaker | 启动/健康失败和 lapsed 窗口保留；deadline 仅告警是明示取舍，接受更多任务个别耗尽的代价。窗口夹具需 C20-03。 |
| 持久化派发、作废、独占释放及唤醒 | K5、§2.5、CF-AUTH-20k/o | 上轮主干问题已修；不得有“仅依赖策略自觉唤醒”的实现。自动回收循环仍需单独预算或停止，C20-01。 |
| 可审计、可重放 | K1/K6、RetirementEvent、计数、CrossTaskBreaker | 已补快照、charged_task_ids、strategy_version；允许策略不计数，但不能省掉影响记录。 |

**K2 能保证什么**：对持续出现在任务域退役快照中的同一 task，每次 affected_count 单调 +1；即使 NullAttribution 永不增加 loss/interrupt，达到 max_task_affected 后也必须停止自动执行，按未核销 L / 已核销 M 分流。两份快照的并集去重，不能因同一 task 出现两次而双计。

**K2 不能保证什么**：它不保证外部事实不明的 publishing 在有限墙钟时间关闭，也不应以预算代替事实；等待 Q 或人工处理是安全的可见状态。更重要的是，本版明确豁免了自动 isolation_drain 的全部计数，故尚不能据 K2 宣称“每个自动恢复循环都有界”，见 C20-01。

**规范与策略的边界**：S1–S3 和 CF-STR-01–04 已标“目标、非规范、不计 conformance”，未再把准确找出毒丸及无辜零计数作为无条件保证。S2 的“不饿死”应视为受 K5 约束的调度责任，而非故障归因精度；不能用“参考策略”标签免除违反 K5 的循环。两个 conformance 夹具仍残留策略耦合/相反断言，C20-03。waiting_holder 的契约含义仍是等 Q；isolating、IsolationChannel 可不使用，不应迫使替换策略实现参考排序。

## D. 01 v0.20 问题

### C20-01 — MAJOR：自动 isolation_drain 不计影响次数，K2 仍允许只探测驱动的无限回收循环

**位置**：01 §2.2d 计划性回收域、K2/K3/K5、参考 S2（第 189、193–201、210 行）；CF-AUTH-20n/q、CF-STR-03。

**原文依据**：controlled_reclaim “**不增加任何计数（含 K2）**”；K2 只对“**任务域事件**”的快照增加 affected_count；S2 在只探测未报告时经 `probe_drain_timeout` 以 isolation_drain 换实例；K5/S2 要求回到 open 后“**先**放行……暂缓项，**再**……下一个……draining”。总则却保证“**每个 task 的自动恢复次数有界**”。

**问题/反例（固定两个 task，不依赖持续外部新任务）**：

1. U 已锁存 indeterminate。E 上的 probe q1 已 ACK，所以 receipt=completed，但始终不返回报告；broker 心跳正常。A 是已核销、原 holder 已 Q、ready 的隔离成员。
2. A 预约 draining。配置允许 `probe_interval < probe_drain_timeout <= probe_timeout`；下一周期为 U 创建 q2，因 draining 而 held。q1 已 completed，不违反同 token 至多一个 intent。
3. 排空期限到，E 经 isolation_drain 回收，事件快照包含 U 的在飞 q1，但所有计数仍为 0。A 尚未执行；它已核销，不因旧授权 expires_at 被关闭。旧 cgroup 可正常回收。
4. 新实例上线，K5 先放行已排队的 q2，再为 A 重新预约。q2 同样不报告；下一周期 q3 进入 held。回到步骤 3。

每一步都有唤醒，但 U 永不到 affected 上限，launcher 失败上界和 lapsed 熔断也均不适用；A 可无限重复排空。它不是“归因不准确”问题，而是自动恢复预算漏掉一种会重复的自动操作。把 S2 降为非规范不解决它：当前参考实现仍须满足 K2/K5。人工反复下达 planned_restart 不在此反例中。

**候选 diff（保持域分类，把影响预算与故障归因分开）**：

```diff
--- docs/01_Contract_Spec_v0.20.md §2.2d 计划性回收 / K1–K3
- controlled_reclaim：不增加任何计数（含 K2）
+ controlled_reclaim 不增加 loss_count、interrupt_count 或 launcher 故障计数；
+ 运维主动登记的 planned_restart 不扣自动恢复预算。
+ 自动发起的 isolation_drain / retire_requested 仍按两份快照的并集恰一次
+ 增加 affected_count，表示恢复影响，不是认定该任务有错；事件域保持不变。
- K2：任务域事件……affected_count +1
+ K2：任务域事件及上述自动回收事件……affected_count +1。
+ 自动回收的影响计数与首次 RetirementEvent 同事务提交，重启不清零；
+ K3 的上限分流同样适用，不能由参考策略改为免费重派。
+ 删除“归因正确时计数上限先触发”的无条件说明：自动回收的影响预算
+ 可以先耗尽；max_task_affected 的配置下限不等于承诺哪种上限先触发。
+ 达只探测影响上限时暂停 U 的自动 probe，并作废其尚未放行的自动 probe
+ intent，释放 token 的唯一 intent 名额；仅保留经特权来源明确授权的单次探测。
--- K5 / S2
+ 排空回收后重新派发前先应用 K3；已暂停的 U 不重新入自动 held 批次。
+ 替换策略若不用 isolation_drain，仍须给它引入的自动回收循环规定持久化预算
+ 或明确的停止状态，不能仅以持续唤醒代替有界恢复。
```

**副作用分析**：计划性回收仍不是肇事归因；被正常自动回收影响的任务可能更早转人工，这正是“独立于归因的预算”的代价。也可另设自动回收预算，但不得继续声称三个现有预算已覆盖。人工主动重启不被当作自动故障；Q、U 锁存和 M 的执行禁令不放宽。

**配套测试/夹具**：以固定 U/A 和短周期 probe 构造上述循环，每次 ACK 成功、报告永不返回、心跳正常、回收正常；在预算边界前后 kill 编排/launcher，断言有限回收后 U 暂停、待发自动 probe 作废，A 可前进或进入明确的安全停止状态。CF-AUTH-20n 区分人工 planned_restart 与自动回收的 affected 增量；CF-STR-03 不再笼统断言所有计数零增量；仍断言 loss/interrupt/start-health 不因计划回收增加。

### C20-02 — MAJOR：auto_probe_suspended 被直接解释为 unknown，可能遮蔽显式探测的确定结果；单次强制探测还缺协议选择

**位置**：01 §2.2d K3/K5、§5.1 特权运维（第 644 行）、AdjudicateRequest（第 634 行）、CF-AUTH-20j/q。

**原文依据**：K3 与 §5.1 都规定暂停时“**强制 probe 按 unknown 处理**”，同时允许“**运维可显式发起单次强制只探测**”。同段已有强制约束：“**probe 明确全部发生 → 只允许 confirm_released**”。AdjudicateRequest 目前仅含 run_id、verdict、evidence_refs，没有选择显式单次 probe 的字段；ReleaseProbeDispatch/DispatchReceipt 也没有特权发起来源绑定。

**问题/反例**：U 达到探测影响上限，M 且 auto_probe_suspended=true。运维显式单次探测成功，报告全部发生，C-11a 按 M 规则保存为裁决证据；没有条款说这个成功会清除暂停标记。随后裁决时，一条规则要求只准 confirm_released，另一条按仍为 true 的标记把强制 probe 当 unknown。后一种读法会使确定证据退回可人工选择的分支。必须明确“无法执行一次自动探测”不等于“将已取得的结果改为未知”。

此外，暂停后的特权入口如何区分“接受探测不可用、直接凭证据裁决”与“显式请求一次探测”，没有请求/持久化表达。若把每次 adjudicate 都当作强制请求，又失去了本版为避免坏 probe 阻断人工出口而新增的跳过行为；若一律跳过，则无法兑现单次强制例外。不能靠在 evidence_refs 内暗藏一个未定义的控制开关。

这不是断言现有实现已经违背事实，而是新分支没有唯一且可序列化的规则；事实优先的安全边界不能靠实现者猜测优先级。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.20.md §2.2d K3 / §5.1 特权运维
- auto_probe_suspended=true 时，强制 probe 按 unknown 处理
+ auto_probe_suspended 只禁止自动派发，不改写任何实际 probe 结果。
+ 暂停且本次未显式请求探测时，记录 probe_unavailable（引用 RetirementEvent）；
+ 该记录只解释本次不能自动取证，不是远端未发生/未知的观测。
+ 若已有与本次授权/目标绑定的有效确定证据，或本次显式 probe 得到确定结果，
+ 必须优先按确定结果约束 verdict；不得因暂停标记降为 unknown。
+ 没有可用确定结果时才走既有 unknown 的人工证据分支；RetirementEvent
+ 本身不能充当“已发布/未发布”的远端证据；负向裁决仍要求原 holder 的 Q。
--- §5.1 AdjudicateRequest
+    force_probe: bool = False   # 暂停后显式请求一次；非暂停时仍按原规则强制 probe
--- §2.5 DispatchReceipt
+    origin: Literal["automatic","operator_force"] = "automatic"
+    operator_request_ref: str | None = None  # 指向已认证的运维入向请求记录
--- §5.1 特权运维处理序
+ origin/operator_request_ref 由编排据已认证请求填写，不作为 broker 自报值。
+ 编排将单次探测与经认证的运维 principal、入向 request_id 及出向 request_id
+ 持久化绑定；K5 的“运维显式发起”据此判定，不信任 broker/插件自报。
+ 同一运维请求重放复用同一次探测和结果，不再次生成自动探测循环。
+ 单次探测仍只读、受 K2 结算，不清除 manual_only/auto_probe_suspended。
```

**副作用分析**：需要一个请求字段和少量来源/结果绑定记录，wire 版本与夹具应同步。允许坏 probe 被跳过以便人工处置，但不会把已知发生事实抹掉；显式探测失败可如实形成不可用证据，不能恢复自动执行权。

**配套测试/夹具**：暂停 × 本次不探测/显式探测 × 实际全部发生/未发生/部分/不可用；确定发生时 confirm_not_released 始终拒绝，即使暂停标记仍 true。已存在确定发生证据、本次不可用的组合也不得将其丢弃。相同运维 request_id 在生成 probe 前后、结果落账前后重放，只一次逻辑探测；强制来源不可由普通 worker/broker 伪造。CF-AUTH-20q 不能仅以引用 RetirementEvent 就断言任意 verdict 合法。

### C20-03 — MINOR：两处规范夹具仍与策略分层及 K4 的耗尽入窗规则不一致

**位置**：01 §6.5 CF-AUTH-20g/20i（第 849、851 行）、K4；参考 S1/S2、CF-STR-01。

**原文依据**：CF-AUTH-20i 要求“**controlled_reclaim 与多绑定未计数事件不进入窗口**”；K4 同时要求记录“**被计数、或因该事件达到 K3 上限**”的不同 task。CF-AUTH-20g 前置为“**P 与无辜 B 永久同处一个实例**”，要求 ref-v1 和 NullAttribution 下 P/B 都在 affected 上限后耗尽；ref-v1 的 S1/S2 又规定多绑定故障后隔离重派。

**问题/反例**：

- NullAttribution 下 A/B 的 affected_count 都为 5，第六次共同 lapsed，无 charged_task_ids，但二者均达到缺省 max_task_affected=6。K4 要将 A/B 入窗，缺省 distinct 上限 2 即熔断；CF-AUTH-20i 的排除句却要求不入窗。这不是策略可自由选择的行为。
- ref-v1 正常工作时，首次多绑定后就不应让 P/B 永久同处；无辜 B 可以独占成功并关闭，不应强制它达到影响上限。若夹具强制永久同处，则它不是完整 ref-v1 的合法端到端执行。不能为满足一个“策略无关”用例而禁用参考策略自己的排他性。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.20.md CF-AUTH-20i
- controlled_reclaim 与多绑定未计数事件不进入窗口
+ controlled_reclaim 不进入 lapsed 窗口；多绑定、未计数且无人因本事件达到
+ K3 上限时不入窗；达到上限者即使未被计数也入窗，同事件多人分别登记。
--- CF-AUTH-20g
- P 与 B 永久同处……ref-v1 / NullAttribution……P、B 都在……耗尽
+ NullAttribution 的端到端场景允许 P/B 持续同处，验证影响预算兜底；
+ ref-v1 端到端场景遵循隔离行为，任务可以正常完成或在其实际累计影响
+ 达上限时走 K3，不能预先要求无辜 B 必耗尽。
+ 另对固定的合法任务域事件序列分别运行计数策略，逐事件验证 K1/K2/K3
+ 结算；这只是预算单元测试，不宣称序列一定由完整 ref-v1 调度产生。
```

**副作用分析**：不改变生产规则，仅避免实现按错误的测试断言删除 K4 的兜底，或人为破坏参考策略调度。归因准确度仍放在 CF-STR，不重新变成 conformance 承诺。

**配套测试/夹具**：新增两 task、零 charged、affected 从 5→6 的 lapsed 窗口 golden；相同快照但 4→5 不入窗；phase_deadline 仍只进告警集合。ref-v1 使用真实调度允许 B 成功；固定事件序列预算测试单独命名，不用“永久同处 ref-v1”前置。

## E. 五条时间线 × 提交/故障/上限/调度的交叉走查

按可达状态分解交叉维度，避免将尚未核销却已发生发布等非法前置当作正常格。组合先取业务事实行，再取提交点、域与快照、预算和调度行；标注问题号的格当前不满足要求，其他格给出唯一规则出口。此为文档推演，不宣称完成产品模型检验。

记号：Q 为 granted_epoch 对应实例 reclaimed 且可信 cgroup 子树静默；U 为 indeterminate；M 为 manual_only；H/F 为固定 released/release_failed 终局映射；L 为未核销耗尽时撤销并 F。M 是终止自动执行的安全出口，不等于业务 Run 已关闭。

### 五条业务时间线

| 时间线 | 未耗尽的事实路径 | 耗尽/新条款交界 |
|---|---|---|
| 正常 | 一次 consume→执行→有效 outcome→H/F | 任何预算命中时按实际 consumed 分流；正常终局按 K5 释放预约、写唤醒，不依赖实例退役。 |
| 核销后发生前崩溃 | 等 Q；新 epoch resumed；not_happened 原子许可通过才执行，不通过则 F；未知→U | K3 任一上限→M；不得因 phase=awaiting_consume 误认成尚未核销。 |
| 发生后崩溃 | Q 后对账全部发生→H；部分出现/不确定→U | M 后仍只人工结案，明确发生不得负向裁决；暂停探测后确定结果优先级需 C20-02。 |
| 无法确定 | 只探测；发生→H，未发生且 Q→F，未 Q→回收原 holder 后新序号探测，未知保持 publishing | probe 导致 lapsed 纳入 affected；达到上限 M+暂停自动 probe。drain 回收漏预算见 C20-01；人工出口见 C20-02。 |
| broker live 而单 task 失联 | 当前 armed phase/generation CAS 到期→retiring；由当前双快照定域/结算 | 每 task 三上限仍生效；deadline 不进入 lapsed 熔断、达到 deadline 不同 task 门槛只告警，是明确可用性取舍。 |

### 提交点和编排重启

| 点位/竞争 | 唯一恢复规则 | 本轮核对 |
|---|---|---|
| spawn 记录前/后、exec/hello 前失败 | 无 task 在飞；start_health，epoch=None，spawn 恰一次结算 | 已覆盖；不能伪造 epoch 或将 hello 前失败写成 task 域。 |
| hello 成功、放行 intent 尚未提交 | 仍无绑定/只探测在飞；与退休按同实例事务顺序单胜 | 两类快照建立都不能在实例未就绪时绕过发送条件。 |
| held intent 提交、发送前重启 | 无执行阶段/两份快照项；扫描全部 held，由 K5 唤醒 | 旧 epoch 经替代，不走同 epoch 的普通重送；修复 Z7。 |
| 放行提交前/后 | 前仍 held；后 execute 建绑定/阶段/期限，probe 仅成为只探测在飞 | probe 不要求 Q，不恢复执行阶段；修复 Z3。 |
| 受理后 ACK 前、ACK 后 completed 前 | 同 epoch 同 id 传输去重；completed 仅送达 | 无第二次 consume；probe ACK 不等于报告，是 C20-01 可达性的关键。 |
| completed 后实例失效 | 仍未完成的 execute 进 B；尚无对应报告的 probe 进 P | 历史终局/U/M execute receipt 不再构成 B；已报告 probe 不进 P。 |
| 替代事务前/后、新 epoch 再次失效 | 旧 intent 或唯一新 intent；旧 ACK 只审计 | execute 已核销须 Q，probe 不要求 Q；模式检查不能因 epoch 更替跳过。 |
| consume/resumed/proceed 与 deadline | 同阶段/代次 CAS 单胜，后到旧结果拒绝 | completion 不清 K4 窗口；对耗尽分流使用实际 consumed 状态。 |
| 报告/业务终局与退役判定 | 报告先提交则更新在飞状态后取快照；退役先提交则后到旧实例结果拒绝 | 一份事件保存当时快照；影响计数、K3、窗口和唤醒同事务结算。 |
| K3 / 预约释放 / outbox 提交前后重启 | 前旧状态可重试，后复用持久化结果及唤醒 | 旧 selection_seq 通知不能释放新预约；同批次进度恢复不吸入无限新流量。 |
| 人工裁决与显式单次 probe 的提交点 | 运维请求幂等，实际探测结果约束唯一 verdict | 当前暂停分支与来源绑定不闭合，C20-02；不能用普通重试生成无界强制 probe。 |

### 三域与两份快照

令 B=bound_task_ids，P=probe_task_ids，影响集合取 B∪P 去重。

| cause 与快照 | 当前规定的域/结算 | 结论 |
|---|---|---|
| start_failure，尚未 hello | start_health，按 spawn 计一次，epoch=None | 完备。 |
| lapsed，B=P=∅ | start_health | 已结束的历史 receipt 不污染判断。 |
| lapsed，B 非空、P 空 | task；charged⊆B；B 的 affected+1 | NullAttribution 也受 K2。 |
| lapsed，B 空、P 非空 | task；无合法 charged execute；P 的 affected+1 | 不计 launcher 失败，修复上轮只探测混入启动域的问题。 |
| lapsed，B/P 均非空 | task；只可能对 B 归因计数，B∪P affected+1 | 参考策略可能误计 B 是已声明局限，不再报归因缺陷。 |
| 有效 phase_deadline | 触发者必须在 B；task，B∪P affected+1 | B 空先拒绝为不变量破坏，不应硬塞 start_health；旧代/解除 timer 也先拒绝。 |
| controlled_reclaim，任意快照 | 当前 loss/interrupt/affected/start-health 均零 | 分类互斥，但自动回收的 affected 豁免造成 C20-01；域归属与预算豁免是两个不同问题。 |
| 首次退役后重复通知、后续 lapsed | 复用首事件，不更换域或再结算 | 不能在重放时按已变化的快照再算；K6 模型已正确保存原快照。 |

### K3 三上限与 K4 窗口

| 条件 | 自动出口/窗口结果 |
|---|---|
| loss、interrupt、affected 均未到限 | 依执行权/Q/模式恢复；参考策略可以隔离，但不是必须正确归因才允许 K2 兜底。 |
| 任一达到上限，实际未核销 | 同事务撤销授权、L；旧 consume 拒绝，不重开授权。 |
| 任一达到上限，实际已核销 | M，停 execute；保留事实，对账证据仍可读取。 |
| probe 在飞导致 affected 达上限 | M+auto_probe_suspended；自动周期与 hello 均跳过；显式运维探测不清 M。需要 C20-02 明确其请求与结果。 |
| 同一事件重复、一个 task 同在两份集合 | 各计数至多一次，不双计；不同上限同时命中也只有一次 L/M 分流。 |
| lapsed：被计数或本次达到 K3 上限 | 以不同 task_id 入持久化窗口；无 charged 但受影响耗尽也必须登记，C20-03 修夹具。 |
| lapsed：多绑定、未计数、均未到限 | 不入熔断窗口，但 K2 影响不丢；后续到限不能继续豁免。 |
| ACK、consume/resumed、合成耗尽关闭、人工结案 | 不清窗口；原先每次 consume 成功就绕过的路径已关闭。 |
| 有效 outcome 或恢复对账正常终局 | 按 Ledger 提交序清窗口；重放该终局不再执行一次清零动作，沿统一 receipt/终局 CAS。 |
| phase_deadline | 只更新 deadline_task_ids、达到门槛告警，不熔断；不能把它混入 lapsed 集。 |
| 编排/launcher 重启 | 窗口及 tripped 保留；显式人工恢复可清零，但不是普通进程重启。 |

### K5 预约、放行、作废与迟到通知

- 所有入口和续送统一核对独占许可；held 不计执行期限、不进入两份快照。execute 与 probe 的放行条件互斥，不能用 C-09 规则拒绝 U/M 的合法读取，也不能让 probe 获得执行阶段。
- 业务终结作废两类 held；U/M 转换作废 execute，合法 probe 保留。新增 auto_probe_suspended 后不再合法的自动 probe 必须有作废或显式停止去向；C20-01 的修法同时要求释放其 token 名额，避免阻挡特权单次取证。
- 正常 H/F、转 U、转 M、实例退役、draining 中失去准入均释放预约并写唤醒；正常 consume→outcome/reconcile 不释放。释放动作使用触发事件所属的 selection_seq，而不是回调执行时重新读取新序号冒充旧序号。
- 旧 sequence 的回调在新预约前后都不能清掉新头；同一释放事务重放只复用结果。K5 明确了该要求，未发现新的 ABA 放行路径。
- 固定 held 批次先处理，再建下一预约可以防止新外部流量无限扩充本批，但不自动消除“批次中的同一个自动 probe→排空回收→下一批同一 probe”的循环；这正是 C20-01，而非要求改变参考策略排序偏好。
- 依赖 Q 永不可得时，可见 waiting/告警是合法出口，不可伪造静默；不能令该项占用全局预约而饿死其他 Run。此处是活性约束，不承诺该 Run 必然业务成功。

## F. 同步项与交付边界

HLD B 第 7 组已登记 ExecutionManifest 的 deploy 安装集 digest、Run 创建比较、例外清单，以及原有注册 attestation 和 launcher 部署契约。01 仍以上游冻结版为范围，尚未加入这些 HLD v2.x 字段，不计为第二部分缺陷。H210-02 是已登记主题的计算/采集规则补全，不再拆成独立同步项。

本报告只给文档候选 diff 与配套夹具要求，没有修改被审文档、处置表、他方报告或研究记录。报告所用小脚本只验证字段归属和明确的预算/窗口谓词，不代替真实 broker、launcher、扫描器或部署验收。只提交本方文件。
