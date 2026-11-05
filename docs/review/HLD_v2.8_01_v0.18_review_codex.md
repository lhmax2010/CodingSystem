# HLD v2.8 / 01 v0.18 收尾定向复审 — Codex

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.8（A25 与 D23） | **NO-GO** | 0 | 1 | 0 | 0 |
| 第二部分：01 v0.18（A3 的 v0.18） | **NO-GO** | 0 | 4 | 1 | 0 |
| 新增同步项（不计入第二部分） | 无；B 第 7 组已有项不重复报 | 0 | 0 | 0 | 0 |

## 负责人七项裁决的独立评估

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时必须显式报告 | **成立** | 本版不削弱同 series 汇合、报告义务及超时放行条件。并行减少时延，代价仍是保存两路证据及被替代历史，不必恢复串行。 |
| ② | Quickbuild 取最新 Profile 快照，在 Run 启动时固定 | **成立** | 保留了“本系统策略而非服务缺省”、按证据显示推广状态、Profile/构建根双编号及失败风险为推断的说明。本版未扩大 Quickbuild 能力声明；更新快照可能增加环境不匹配与修复成本，已如实呈现。 |
| ③ | Profile v1 严格匹配，v2 经评估后放宽 | **成立** | 缺省关闭、兼容条件和非劣验证仍在。放宽需工具链实测，不能以文档评审代替；重采和验证成本不可省。 |
| ④ | 目标模块登记与相关范围验证 | **成立** | 完成复核失败不推进 series，不会借 purpose 改记缩减范围；撤销后范围只增不减仍有效。额外验证成本是这一选择的代价。 |
| ⑤ | 用测试结果与多版本报告检验 AI | **成立** | 本版明确复核不一致时作废候选，不允许把撤销偷偷改为 repair；计划、代码和证据仍在同一权威事务链上。未决期间只能确定性撤销的保守代价保留。 |
| ⑥ | 显式 base 预检、读回核对 | **成立** | 镜像输入不可信时优先失败的例外现已与改交撤销规则一致。不能把不可比用人工确认补成比较结果；能力不足需本地后端，成本仍明确。 |
| ⑦ | 超时重试成功可发布，须审批人确认 | **成立** | 当前 series 全部任务及所用基线的重试逐条确认，历史重试首屏汇总，摘要绑定与核销复核未被本版缩减。开发者与审批人仍能知道超时；代价是审批信息量和证据保留。 |

D23 是新增的负责人前提，本报告接受“不引入 PHP”这一约束，只检查其实施完整性；H28-01 不评价语言选择本身。

## 输入、范围与方法

日期：2026-11-05。开始执行 `git pull --rebase`，返回 Already up to date。输入 HEAD：`729573de97dc3843494a24f351ae688fbe4d3d96`。阅读两份上一轮处置表及三家上一轮原始意见，核对 v2.7→v2.8、v0.17→v0.18 的改动及直接冲突条款。未读取本轮其他评审方意见，未访问或探测 Quickbuild，未修改被审文档。

| 输入 | SHA-256 |
|---|---|
| `docs/00_Framework_HLD_v2.8.md` | `0feaf5ca3d3d1e8453f55a453ed1a736ea188d8ebbe251e84b3316d83c8e2180` |
| `docs/01_Contract_Spec_v0.18.md` | `871d68e8073f60b5b7cad8a349da85f1f034e63e86c24d20e300ec08766f676c` |
| `docs/review/HLD_v2.7_review_disposition.md` | `5e400e208d592fab60e29b0f9344266cb0810a0332d0e165f91e0067457ea0f9` |
| `docs/review/01_v0.17_review_disposition.md` | `727453aaebbbd4fee77519165bdfa85f02aee961862d5c25af7e824c1114c7aa` |

验证方式是文档状态机走查、YAML 解析及显式谓词的小脚本演算。四份 HLD 示例均能解析；01 的 124 个 class 均在 A0 中有索引，新增 RetirementEvent 已收录。没有把这些检查描述为产品 conformance、真实 launcher 或部署镜像已通过验收。

## A. 处置落实与合并方案

### HLD

| 处置 | 正文与判断 |
|---|---|
| P1 完成复核不一致 | §7A.4 明确 purpose/plan_id 不同或容量不足时作废候选、计划与 series 不变、sys.error(candidate_recheck_failed)，可按节点 retry 重新预校验，不改记 purpose；§11.3 补竞争与 kill 点。落实。 |
| P2 改交撤销例外 | §7A.4 明确 base_mismatch/backend_source_input_unsupported 的镜像失败仍走原合法出口；被拒提交不登记 candidate，新 request_id 改交、旧 id 重放拒绝。落实。 |
| P3 terminal 旧夹具 | §11.3 v2.6 组已限定为绕过加载器直接构造状态；加载可达性另测。本方 H27-01 关闭。 |
| P4 无 PHP 前提 | D23、§9、§11.1、§11.2、B-7 已覆盖产品范围和两类例外。禁止范围完整；检查机制对后装制品及实际镜像闭包仍有缺口，H28-01。 |

HLD 上轮三条编号意见全部有落点，P4 是额外前提，不应算成漏报的第四条上轮意见。处置表无独立“记录更正”节。

### 01

| 处置 | 正文与判断 |
|---|---|
| X1 全局排他与不连带计数 | §2.2d 改为唯一通道，execute/probe 均经统一入口，hello 排除 isolating/manual_only，期限触发者之外不加 interrupt；CF-AUTH-20g/h/k 更新。原“只在 S 内串行”已移除。通道由普通工作切入独占的获取/放行协议仍不完整，C18-02。 |
| X2 判定时计数与队列进展 | 计数提前到判定事务，isolation_state 四值、跳过 waiting_holder/probe_only、耗尽后 diagnostic_done 与过期原因均已写入。核销前隔离头的再次准入被错误套用 holder 静默，C18-03；过期规则边界见 C18-05。 |
| X3 执行绑定划界 | 不看 ACK、就绪前不绑定、退役与 intent 串行化、RetirementEvent 与启动/健康上界已写入。绑定的终止谓词丢失，C18-01；事件的全部 cause 尚未闭合，C18-04。 |
| X4 进入时点与历史计数 | waiting_holder 改为标记 retiring/lapsed 的事务；文首与 A3 把 v0.17 输入更正为 6 条编号意见，落实。 |

**三处合并方案均为有条件成立**，条件是补齐本轮具体缺口，而不是退回上一版：

1. 全局隔离加统一入口是正确方向，且把 probe 纳入排他性比只禁止 execute 更完整；还需独占获取前排空既有工作，以及暂缓项重新放行的原子步骤（C18-02）。
2. 判定时计数和成员调度状态可避免等待物理回收把整个队列卡住；但未核销者没有 granted_epoch，不能套用已核销成员的等待条件（C18-03）。
3. 以逻辑绑定而非 ACK 划界解决了原来的双计；必须定义当前仍有效的绑定及所有事件的归责，不能让历史 completed receipt 永久形成绑定（C18-01/04）。

**“记录更正”准确**：上一轮 CC C16-01–04 共四条、本方 C16-01–02 共两条、Kimi 零条，合计六条；CC C16-03 有两个子点，按七点处置的说明成立。当前第十七轮输入为 CC 四条+Codex 四条=八条，归并 X1–X4 四题亦正确。

## B. 第一部分问题及边界核验

### H28-01 — MAJOR：D23 禁止范围完整，但注册自报运行时和镜像清单扫描不能覆盖实际依赖闭包

**位置**：`docs/00_Framework_HLD_v2.8.md` D23、§11.2；直接关联 §2.4 独立安装插件、§11.3 conformance 制品绑定及 B-7 部署契约。

**依据**：D23 禁止“**全部内容……以及它们的运行时依赖闭包**”；§11.2 检查对象是“**lockfile 依赖闭包、deploy 资产与镜像清单、仓库全部文件**”，注册检查是“**声明的运行时为 PHP 即拒绝注册**”。§2.4 同时允许业务 Agent 作为“**独立安装包**”接入。

**问题**：禁止的集合大于检查的集合。框架仓库 CI 无法覆盖之后安装的业务 wheel、adapter 的依赖；runtime=python 的合法包装入口也可以依赖 PHP 工具或捆绑 PHP 组件，按现有唯一注册谓词仍通过。部署镜像仅在清单中列出一个基础镜像 digest，也不能证明该基础层及安装后的 rootfs 不带 PHP。这个反例不需要恶意谎报：入口确实是 Python，只是其传递依赖不同。当前 conformance 只明确断言“声明 PHP 拒绝”，没有把闭包扫描结果绑定到被加载制品。

**候选 diff**：

```diff
--- docs/00_Framework_HLD_v2.8.md §11.2 / D23 检查
- CI 扫描 lockfile 依赖闭包、deploy 资产与镜像清单、仓库全部文件……
- 插件与受限 adapter 注册时声明的运行时为 PHP 即拒绝注册。
+ CI 的输入为最终交付清单及展开后的实际内容：应用依赖、OS 包、基础镜像
+ 与安装后 rootfs、随交付的前端资源/运维工具/测试夹具及其传递运行时依赖。
+ 镜像按 digest 解析依赖与实际文件，不能以镜像名称或顶层清单代替闭包检查。
+ 插件、受限 adapter、宿主侧解析器/适配器的注册准入，同时要求：
+ 运行时声明合规；实际制品及其运行环境闭包通过同一无 PHP 检查。
+ 检查结果绑定制品 digest、闭包 digest 与策略版本，并纳入加载期 attestation；
+ 声明非 PHP 不豁免传递依赖，缺闭包证据或 digest 变化时拒绝加载/重新检查。
+ 部署后新增工具或依赖必须先通过该检查，不能在注册后补装未验证运行时。
+ 外部系统与板端专用业务脚本按来源/执行位置登记为输入数据，不能把产品
+ 自带的 Web、运维服务或宿主适配组件改称“外部”来豁免。
--- docs/00_Framework_HLD_v2.8.md 附录 B 第 7 组 / 部署契约
+ D23 准入记录包含实际制品/运行环境闭包 digest、策略版本和扫描结论；
+ 与现有制品 attestation 和加载期复核一致。
```

**副作用**：增加依赖清单、镜像内容扫描和后装制品验收成本；某些未提供闭包材料的插件暂不能接入。这是兑现既定 D23 的成本，不改变禁用前提。不是要求以文件后缀识别所有语言，更不是要求审计外部服务的内部实现。

**测试/夹具**：使用合成清单/FakeScanner，覆盖 Python 入口但传递依赖为 PHP、基础镜像含 PHP 而应用 lockfile 不含、Web/运维辅助组件带 PHP、后装 adapter 和制品更换；均拒绝。纯静态前端、纯 Python 闭包通过。板端专用脚本作为外部输入可接收，但把同一脚本改成宿主侧执行即拒绝。负向夹具不必把真实 PHP 运行时作为产品测试依赖引入。

### D23 的范围结论

| 边界 | 本版范围是否明确 | 检查结论 |
|---|---|---|
| 框架、Agent、Approval、broker/官方 adapter、Gateway/登录助手 | 是，逐项列出 | 都属于 H28-01 的实际交付/闭包检查范围。 |
| Web 视图及前端、管理工具、deploy 镜像基础层、测试夹具 | 是；§9/11.1 还限定 Python 与静态前端 | “静态前端”不构成依赖豁免；仅清单扫描不足，H28-01。 |
| 业务插件、受限 adapter、宿主解析与适配代码 | 是 | 注册自报 PHP 可拒绝，但非 PHP 入口的闭包仍须验收，H28-01。 |
| Quickbuild/gerrit/github/Cosmos 等外部系统 | 明确不在范围 | 不要求探测其实现语言；实际由本产品交付部署的辅助服务不能用此例外。 |
| 业务提供、只在测试板执行的脚本 | 明确作为非产品交付输入排除 | 宿主侧适配/解析仍在范围。产品自带测试夹具没有被此例外整体排除。 |

### A25 小修订的结果

受理成功不承诺完成时一定采用。父 CAS 失败、purpose/plan_id 改变、容量不足现在均有候选作废与 sys.error 出口；完成重放复用 receipt，计划与 series 不会半提交。并行候选仍只有一个父 CAS 胜者。重试重新预校验，容量不足可转无进一步收益；未配 retry 则沿原失败路由，不引入新成功出口。

E-CANDIDATE-NOT-REVERT 不登记 candidate，旧 request_id 仍重放拒绝，新 id 可在同 task 改交；只有最终成功采用撤销后的路由通过才消耗一次环边，重试不等于新增环轮。镜像输入不可信的两个失败原因优先，不再误归 invalid_result。campaign 全部撤销且无净变更后 no_gain_found 合法，未决或有净变更时仍拒绝。本轮未发现这些小修订新增 MAJOR/MINOR；HLD 的 NO-GO 仅来自 D23 的准入覆盖问题。

## C. 第二部分问题

### C18-01 — MAJOR：执行绑定没有终止条件，历史 completed receipt 会继续污染归责与隔离成员集

**位置**：01 v0.18 §2.2d“执行绑定”“故障归责”“launcher 启动/健康上界”；§2.5 DispatchReceipt。

**依据**：绑定被定义为“**一条已放行发送的 execute 型 DispatchReceipt（state = intent 或 completed，held_for_isolation = false），其 target_epoch == 该实例 epoch**”。§2.5 规定“**已 completed 的旧 receipt 保持不变**”；launcher 又要求“**含任务已全部完成之后的无任务失效**”进入启动/健康域。本版定义不再包含上一版“未完成”和执行阶段的过滤。

**反例**：A 在 E 上正常发布并终结，其 execute receipt 仍 completed、held=false、target_epoch=E。E 随后无任务失效，按新绑定谓词仍有 A，只能走任务域，达不到 CF-AUTH-20i 的“任务全部完成后无绑定”预期。若 E 又处理毒丸 P，A+P 会被算成多人而都不计数。即使实现者自行为 closed 加过滤，已转 indeterminate/awaiting_probe 的非终态 A 仍满足同一历史 receipt 谓词，不应再被当成在飞 execute 嫌疑。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.18.md §2.2d 执行绑定
- 执行绑定 = 一条已放行发送的 execute 型 DispatchReceipt……
+ 执行绑定是当前尚未解除的逻辑执行承担关系，不能仅从历史 receipt 推断。
+ 它引用已放行的 execute receipt，并同时满足：task 未终结、未 manual_only、
+ 当前 owner_epoch 与该绑定一致，且处于 awaiting_consume/outcome/reconcile。
+ 正常 intent 提交或 held intent 放行事务建立绑定；终局、转 indeterminate、
+ 耗尽转 manual_only、实例退役判定事务解除绑定，退役事件先保存绑定快照。
+ 恢复派发建立新实例的新绑定；历史 receipt 保留，不作为当前绑定再计数。
+ 绑定更新、阶段迁移与归责事务同库串行化；同 task/实例退役事件只计一次。
```

**副作用**：需要显式绑定状态或等价的精确派生谓词；不能通过把 completed 改为 superseded 来伪造传输历史。绑定解除不等于远端执行静默，已核销恢复和负向映射仍等待 Q。

**测试/夹具**：CF-AUTH-20i 加“已完成 A 的 completed receipt 仍保留时 E 失效”；CF-AUTH-20g 加“历史 A + 在飞毒丸 P”；加入 A 转 indeterminate、manual_only 与退役并发，断言绑定快照只含当时真正承担 execute 的任务；未完成且已 ACK 的任务仍须计入，不能把 completed 全部排除。

### C18-02 — MAJOR：全局通道只规定独占后的拦截，缺少普通在飞工作到独占的有界交接及暂缓项的原子放行

**位置**：01 v0.18 §2.2d 全局隔离通道、阶段期限、awaiting_probe；§2.5 held_for_isolation 与出向续送；CF-AUTH-20k。

**依据**：规定“**没有 ready 成员时通道不阻塞普通派发**”，随后可“**从 ready 成员中按序选一个隔离头并授予独占派发许可**”；只描述隔离头执行期间其他派发“**写 intent 后暂缓……隔离头离开执行可能阶段后按序放行**”。原阶段期限仍由“**execute 型 dispatch 的 intent 事务**”建立；awaiting_probe“**不触发 retiring**”。

**反例**：P 等待旧 holder Q 时无 ready 成员，当前 E2 已接入普通任务 N（execute 或 probe）。Q 到达使 P ready。若立即授予 P 独占许可，N 的已发送工作不会被 held 标记撤回，仍与 P 共驻；若为维护“当前实例不承担其他派发”而等待 N，N 是永久无响应的只读 probe 时又没有执行类退役期限，P 可永久饿死。统一检查“是否已有隔离头”只能阻止新发送，不能解决这个获取独占前的状态。

另外，暂缓 intent 原先并不建立绑定/期限；清除 held 的动作必须原子建立新阶段，且重检 epoch、授权、模式与隔离许可。现文“按序放行”未给出这一事务点。按原 intent 时刻起算会立即误判超时；不重武装则新的核销前失联没有期限。扫描者只筛 target_epoch 变化也不能承担同 epoch 暂缓项的唤醒责任。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.18.md §2.2d 隔离调度
+ 通道持久化 open / draining / exclusive 状态与选中 task/epoch。
+ ready 成员出现后先进入 draining，停止接入新的普通派发；确认当前实例
+ 已无其他在飞 execute/probe 工作后，才在事务内授予 exclusive 许可。
+ 已在飞 execute 按原阶段完成/到期规则处理；在飞只读 probe 的排空须有
+ 有界取消/停止确认，无法确认时经计划性回收更换实例，不将等待无限传给 P。
+ 此回收不冒充 task 失联或启动失败（见 C18-04 的非故障回收分类）。
+ 释放/让出许可同事务写持久化调度唤醒；重启周期扫描同 epoch 的 held intent，
+ 不只依赖新 hello 或 target_epoch 变化。ready 成员按保留顺序优先，
+ 无 ready 成员时暂缓普通项按持久化顺序恢复，不得丢掉曾被暂缓的请求。
--- §2.5 出向与 §2.2d 阶段期限
+ held intent 创建不建立执行绑定、不启动执行期限。
+ 放行是单事务 CAS：校验当前 live epoch、Run/授权/恢复模式、Q（适用时）、
+ 独占许可及 token 唯一 intent；清 held、建立绑定、写 owner_epoch 与新
+ phase_generation/awaiting_consume/deadline，再发送。期限从放行提交起算。
+ epoch 已变化则先按替代协议创建当前 epoch 的 intent，不改旧记录目标；
+ 同一已放行 intent 重送不刷新期限。closed/manual_only/indeterminate
+ 不得放行旧 execute；按现模式退役待发项并选择合法终局或只探测。
```

**副作用**：事故恢复多一个有界排空阶段，普通流量会短暂排队；probe 取消失败可能需要更换实例。该成本是进程级排他归责的必要条件，不新增发布许可。暂缓放行事务可使用已有 receipt，不另造第二份出向协议。

**测试/夹具**：CF-AUTH-20k 加“无 ready→普通 execute 在飞→Q 到达”“普通 probe 永久无响应→Q 到达”；断言先排空再独占，持续新流量不能延长排空。held 创建/清除/绑定/发送各点 kill，跨原 deadline 后才放行应获得完整新期限；同 id 重送不能重置。隔离正常结束但 epoch 不变时，所有仍合法的 held 项最终发送，过期/关闭/模式变化者有明确取消处理，不留永久 intent 阻塞 probe。

### C18-03 — MAJOR：未核销隔离头崩溃也转 waiting_holder，等待不存在的授权持有者

**位置**：01 v0.18 §2.2d 全局隔离通道、上限分流、静默与实例替代；CF-AUTH-20g/k。

**依据**：隔离头失效后一律“**它转 waiting_holder……待其旧持有者静默后重新为 ready**”；本节执行权持有者的唯一定义是“**授权 granted_epoch**”。而新实例重派规则仍规定“**未核销者立即……不等静默**”。

**反例**：未核销 P 与 B 首次崩溃后进入通道。P 单独重派，在 consume 前再次崩溃；interrupt=1，尚未到上限，授权 consumed_by_task_id/granted_epoch 均空。按新规则进入 waiting_holder，但没有可供 Q 检验的授权 holder。若改用 dispatch 的旧实例等待，又把未核销恢复改成必须等回收；旧子树长期非空时 P 永远不能再试，与原未核销路径及核销前毒丸有界识别断言冲突。其他成员可前进并没有补上 P 的出口。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.18.md §2.2d 隔离头失效后的成员状态
- 它转 waiting_holder，待其旧持有者静默后重新为 ready。
+ 在计数及上限分流之后，按授权实际核销状态决定成员状态：
+ 未核销且仍有效、未耗尽 → ready，保留顺序；等待新的就绪实例和调度许可，
+ 不等待不存在的 granted_epoch，也不以旧 dispatch 实例 Q 作为新增前置。
+ 已核销且非 indeterminate、未耗尽 → waiting_holder；仅自己的
+ granted_epoch 持有者 Q 成立后恢复 ready。
+ indeterminate → probe_only；耗尽或业务终结 → diagnostic_done，
+ 已核销耗尽的 recovery_mode 保持 manual_only。
+ 上述状态在判定事务内持久化，与 consume 的 CAS 单胜，不由 phase 名推断。
```

**副作用**：未核销毒丸可以在旧实例清理完成前继续诊断，但这正是已有授权/epoch 隔离规则允许的行为，不放宽已核销恢复。旧实例仍按 cgroup 回收与告警处理；未核销授权到期则按有效期关闭，而不是伪造 Q。

**测试/夹具**：隔离 P 在 intent 后发送前、ACK 前、consume 前分别崩溃，旧 cgroup 永久非空；每次 P 保持 ready，在新实例按上限有限关闭或先授权过期，B 不受计数影响。consume 与退役并发：consume 先胜必须 waiting_holder，退役先胜旧 consume 被拒、P 可 ready。恢复派发处于 awaiting_consume 但已经核销的反例必须走 waiting_holder/manual_only。

### C18-04 — MAJOR：RetirementEvent 的归责与模型没有覆盖已存在的计划性回收及首次 hello 前失败

**位置**：01 v0.18 §2.2d 故障归责、launcher；§2.5 RetirementEvent；C-11a/§2.2d retire_requested。

**依据**：要求“**每次实例退役事件……恰归一个域**”，三分支仅列 phase_deadline、lapsed、start_failure；新模型 cause 又包含“**retire_requested**”，并要求“**broker_epoch: int**”。同时 epoch 仍在首次 hello 时分配，launcher 必须处理“**exec 失败、hello 前退出、hello 超时**”。

**反例一**：U 的 probe 确认未发生，但当前 holder 尚未静默，C-11a 返回 retire_requested 并回收。这不是阶段期限到期、lapsed 或启动失败，三个归责分支均不命中。若强塞启动失败，会把正常为取得负向证据的回收当成基础设施故障；若按在飞绑定计 interrupt，又会误计同实例任务。没有定义 zero-delta 的计划性回收域。

**反例二**：exec/hello 前失败需要落 spawn 对应的归责结果，但尚无 broker_epoch。RetirementEvent 的必填 epoch 无合法实例值；伪造 0 或提前分配又不符合现有身份/epoch 来源规则。新模型不能表达自己要求记录的事件。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.18.md §2.5
- broker_epoch: int
+ broker_epoch: int | None    # 仅 hello 前 start_failure 为 None；其余须真实实例 epoch
- cause: Literal["phase_deadline","lapsed","retire_requested","start_failure"]
- domain: Literal["task","start_health"]
+ cause: Literal["phase_deadline","lapsed","retire_requested","start_failure","isolation_drain"]
+ domain: Literal["task","start_health","controlled_reclaim"]
--- §2.2d 故障归责
+ 先按 cause 互斥分类：retire_requested（及隔离排空的计划性换实例）
+ → controlled_reclaim，只记回收与替换，不增加 loss/interrupt/start_health；
+ 关联任务解除绑定/定时器后依实际授权状态重排，旧 holder 的 Q 条件不变。
+ phase_deadline → task/loss；lapsed → 按当前有效执行绑定选择 task 或 start_health；
+ hello 前 start_failure → start_health，epoch=None，以 spawn_attempt_id 结算。
+ 每个实例/启动尝试的首次退役判定 CAS 确定一个事件；重复 retire_requested、
+ 后续 lapsed 通知及 launcher 重启均复用同事件，不另换域或重复计数。
```

**副作用**：增加一个明确不扣故障预算的运维回收域和可空的 pre-hello epoch；“恰归一个域”仍成立，只是不再强迫所有正常回收冒充两种故障之一。`isolation_drain` 配套 C18-02；若实现采用可确认的局部 probe 取消而不换实例，可不增加该 cause，但 retire_requested 分支和 pre-hello 表达仍必需。

**测试/夹具**：C-11a 负向结果→retire_requested 的当前/旧 holder 两例，回收前后重复 probe、租约随后 lapsed、launcher 重启，均只一个事件、计数零增量，Q 后新 probe_seq 唯一负向出口。exec/hello 前退出/超时实例必须可序列化真实事件，epoch=None，spawn 上界仍恰一次；hello 与失败判定竞争不能产生两个事件。

### C18-05 — MINOR：隔离授权过期条款未把暂缓请求限定为未核销，表文边界不一致

**位置**：01 v0.18 §2.2d 全局隔离通道的 authorization_expired_in_isolation；C-09②、§2.2a 与 CF-AUTH-20k。

**依据**：“**等待中的未核销成员或暂缓 intent 的授权过期 → 按 C-09② 关闭**”；暂缓对象明确包括 execute 与 release_probe_dispatch，而后者只对已经核销的 U/M 合法。C-09② 的既有语义是“**不核销，从 running 直接……关闭**”。

**问题**：第二个并列项“暂缓 intent”没有未核销限定。已经 publishing 的 probe 或恢复 execute 也会暂缓，授权原 expires_at 可以已经过去；它们不能因排队超过该时刻而当作未发布失败关闭。冻结 C-09② 与 publishing 事实优先仍能阻止这种映射，因此定为 MINOR 的明确化问题，不声称现文已授予伪造远端事实的合法权限。

**候选 diff**：

```diff
--- docs/01_Contract_Spec_v0.18.md §2.2d / CF-AUTH-20k
- 等待中的未核销成员或暂缓 intent 的授权过期 → 按 C-09② 关闭
+ 等待成员或暂缓 intent 对应的授权，只有实际仍未核销且 Run=running 时，
+ expires_at 到期才按 C-09② 关闭（authorization_expired_in_isolation）。
+ 该事务与 consume 互斥；已核销的恢复 execute/probe 不因 expires_at 关闭，
+ 继续按 Q、recovery_state 与 manual_only 的事实恢复/裁决规则处理。
```

**副作用**：不延长未核销审批时效，也不改变 point-of-no-return。**测试/夹具**：未核销 held execute 到期关闭且计数不变；已核销 held recovery execute、U probe、M probe 的 expires_at 已过仍不得关闭，放行后分别对账/只记证据；消费与到期事务仅一方成功。

## D. 五条时间线 × 故障与隔离的组合走查

为避免用大量重复的勾号掩盖缺口，以下按“授权/事实→传输点→故障归责→上限→通道状态”分层穷尽。每格组合按此顺序选唯一分支；不可能组合不人为制造，例如尚未核销任务不可能合法获得 awaiting_outcome 的执行权。标有问题编号的格尚不能由现文保证唯一/有界出口。

### 记号

- Q：原 granted_epoch 的可信 cgroup 子树静默证明；kill 请求、leader 死亡、读取失败、同名目录重建均不等于 Q。
- H/F：按 released/release_failed 固定映射；P：恢复对账后一次原子执行许可；U：锁存 indeterminate；M：manual_only，仅人工裁决。
- R：已核销、非 U/M，在 Q 后 resumed 并重新对账。全部发生→H；全部未发生→许可有效 P、无效 F；部分/未知→U。
- L：耗尽且实际未核销，撤销授权并 release_failed(dispatch_loss_exhausted) 关闭。
- B：只探测；U 下发生→H，未发生且 Q→F，未发生未 Q→计划性回收再用新序号探测，未知继续 U。M 下四种 recovery_state 均只能记录裁决证据。

### 五条业务时间线

| 时间线 | 正常/恢复出口 | 本版交界检查 |
|---|---|---|
| 正常 | 未核销一次 consume→执行→H/F | 结束后历史 completed receipt 不应再绑定；现谓词缺终止条件，C18-01。 |
| 核销后发生前崩溃 | Q 后 R，不重复初次核销；未发生后 P/F | 计数在判定时完成，等待 Q 不占通道是正确方向；只有已核销者应等待 holder，C18-03。 |
| 发生后崩溃 | Q 后 R→H；部分目标出现则 U | 耗尽 M 时全部发生只准人工 confirm_released；不能按授权过期作负向结案，C18-05。 |
| indeterminate | B/U，不再 execute；M 时只记证据 | 新 probe_only 使其退出通道，但历史 execute 绑定需解除，C18-01；retire_requested 事件域缺失，C18-04。 |
| 实例 live、单 task 失联 | 当前 phase/generation 到期 CAS→该 task loss+1→退役→恢复或 L/M | 其他 task 的 loss/interrupt 均不增加，修复了上轮连带计数；held 放行后的期限建立需补 C18-02。 |

### 崩溃点与事务竞争

| 点位 | 正常/未核销 execute | 已核销执行恢复 | U/M probe |
|---|---|---|---|
| spawn 持久化前/后，exec/hello 前 | 无执行绑定；启动/健康上界 | 已有发布保留事实状态 | 同左；新事件 epoch 尚不存在，C18-04 |
| hello 成功、尚无放行 intent | 无绑定→启动/健康域 | 未取得 Q 不得发 execute | 可发只读；不产生执行绑定 |
| held intent 已提交 | 不发送、不计执行期限，不算绑定 | 同左；消费状态不回退 | 同左；不能因 expires_at 伪造 F |
| 放行事务前/后 | 前仍 held；后应绑定并武装，新期限 | 后还须满足 Q/非 U/M | 后仍只读，不 consume；原文缺放行原子点，C18-02 |
| 普通 intent 提交后、发送前 | 已绑定，失效只归任务域 | 已绑定，不由 awaiting_consume 推断未核销 | 不构成 execute 绑定 |
| broker 受理后 ACK 前 | 同 id 去重，核销最多一次 | 不重复许可；新 epoch 重新 R | 不变成 execute |
| ACK 后 completed 前 | intent 重放，不伪造 ACK | 同左 | 同左 |
| completed 后实例失效 | 按当前 task 是否仍承担 execute 归责 | R 或 U/M 的 B | 不应被历史 execute 污染，C18-01 |
| epoch 更替、替代事务前/后 | 旧 intent 或唯一新 intent，迟到 ACK 只审计 | Q 后替代，不能复用旧 P | 始终 probe；held 仍须统一入口 |
| consume/proceed/终局前后 | 前旧状态、后 receipt/授权恢复；到期 CAS 单胜 | 许可不跨 epoch，终局不重开 | 观测记录不等于人工终局 |
| 退役判定前/后、reclaimed 前/后 | 判定事件一次计数，物理回收不再计 | 计数不等 Q，但执行恢复必须等 Q | 计划回收只记零预算事件，C18-04 |

表中“正常 intent”指已获发送许可的 intent；held=true 是本版显式例外，不能仍用其最初落账时间充当执行期限起点。派发绑定、授权核销和实际发生是三个不同事实。

### 故障归责、上限与毒丸

| 故障快照 | 低于上限 | 达上限 | 是否误计无辜/是否有界 |
|---|---|---|---|
| 有阶段期限触发者 | 只加其 loss；其他成员重排 | 未核销 L，已核销 M | 上轮 A 两次+A2 一次的 B 连带计数已修。 |
| 无触发者、一个当前有效执行绑定 | interrupt+1 | 未核销 L，已核销 M | 核销前/执行中毒丸均应有界；历史绑定过滤缺口 C18-01。 |
| 无触发者、多个当前有效执行绑定 | 不计数，合并通道 | 原已耗尽者不得再入 execute | 真正独占复测才能归责；获取/排空缺口 C18-02。 |
| 核销前隔离头崩溃 | 应保持 ready，旧 epoch 不能核销 | L 或先自然过期 | 现文错误等 holder，C18-03。 |
| 已核销隔离头崩溃 | waiting_holder，其他 ready 可继续 | M、diagnostic_done | Q 不可得只阻塞自身；不能声称在 Q 永远不可得时仍保证有限墙钟完成。 |
| 无有效执行绑定的 lapsed | 启动/健康计数 | 停止自动拉起并告警 | 当前绑定定义未使历史 receipt 失效，C18-01。 |
| retire_requested / 计划排空换实例 | 不应消耗任务/启动故障预算 | 无耗尽分支 | 现文未给归责域，C18-04。 |
| awaiting_probe 超时 | B 重试，非执行失联 | U/M 均不能自动获 P | 若阻挡独占获取须有界排空，C18-02。 |
| 重复 timer、旧 owner、同一退役事件重放 | no-op/审计 | 不复活 L/M | generation/owner/CAS 与事件幂等应联合校验；不能重复 +1。 |

在有限既有队列、可获得所需 Q、launcher 可用且独占获取/释放闭合的前提下，隔离毒丸可按计数界限退出；这不是对无限基础设施故障、不可取得 Q 或授权自然过期的无条件成功保证。需要区分“正常任务不因别人增加故障计数”和“正常任务永远不会因等待而过期”，后者原设计没有承诺，新增可见过期原因是合理代价。

### 新流量、通道调度和暂缓项

| 通道状态/事件 | 必须成立的唯一调度结果 | 本版判断 |
|---|---|---|
| 隔离头已独占，新 execute/probe 到来 | held，不放行、不计时、不绑定 | 已明确，统一入口覆盖 hello 与续送。 |
| 头失效，另有 ready 成员 | 判定计数/让出，按序选下一项；旧 holder 的 Q 不转嫁给下一项 | 已核销分支方向正确；未核销头 C18-03。 |
| 成员转 U 或 M，人工一直不裁决 | probe_only/diagnostic_done，不占 execute 通道 | 新退出状态修复上轮业务终局阻塞；绑定需同步解除。 |
| 无 ready，仅有 waiting_holder | 普通工作可运行 | 已明确。 |
| 普通工作在飞期间旧成员恢复 ready | 预留隔离获取、停止新普通接入、有界排空，再独占 | C18-02 未闭合，不能直接选头就假定实例为空。 |
| 正常头终结，epoch 未变化 | 唤醒同 epoch held 队列，合法项按序放行；不等下一次 hello | C18-02 需明确放行事务与持久化唤醒。 |
| held 等待中模式变化/关闭/授权到期 | 旧 execute 不再释放；未核销到期可见关闭，已核销继续事实恢复 | C18-02/05；不能保留一个永远占 token intent 名额的废弃待发项。 |
| 重启、持续新流量、多个嫌疑集 | 顺序和成员身份不丢失，新流量不能绕开预留或重置原成员顺序 | 字段已落文；排空/放行测试须覆盖，不仅验证列表排序。 |

小脚本按本版显式绑定谓词演算：一个 execute/completed/held=false/target_epoch 匹配的 receipt，在 task=closed、awaiting_probe、manual_only 三种情形仍得到 true；按三条归责条件，retire_requested 在有/无绑定时均无命中分支。这验证的是原文谓词缺口，不是声称真实服务已经发生这些故障。

### manual_only 与安全结论

C-09、恢复臂、execute 派发仍明确排除 M；C-11a 对 M 任一 recovery_state 的 probe 只作裁决证据。只读 adapter、不含发布内容、写调用恒为 0 的约束未被本版放宽。旧 epoch 的 granted/proceed receipt 仍先受连接守卫限制。没有发现本版新增一条合法的 manual_only 自动发布路径。

人工裁决前必须真正执行 probe：全部发生只准 confirm_released；全部未发生须 Q 后 confirm_not_released；部分/未知沿既有证据规则。C18-05 的候选改动用于消除与这些冻结规则不一致的表述，不能以“隔离授权到期”替代事实。上述 MAJOR 集中于检查覆盖、恢复归责及调度活性，不将尚未闭合的恢复路径误报为已证明重复发布。

## E. 同步项与交付边界

HLD B-7 已登记 candidate_recheck_failed、预校验拒绝不登记、purpose 与完成事务扩展；D23 的运行时声明/PHP 拒绝也已在部署契约登记。不把这些尚未扩入 01 的 v2.x 项重复计为契约缺陷。H28-01 建议补充的闭包证据属于该已登记 D23 主题的完善，不另计一个同步问题。

所有候选 diff 仅写在本报告；不修改 HLD、01、处置表、其他评审意见或研究记录。本次只暂存并提交本方文件。
