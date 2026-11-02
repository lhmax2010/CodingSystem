# HLD v2.0（首轮）+ 01_Contract_Spec v0.11（第十一轮）评审意见 —— Claude Code

- 评审方：Claude Code
- 日期：2026-11-02
- 被审对象：`docs/00_Framework_HLD_v2.0.md`（对比基线 `docs/00_Framework_HLD_v1.0_draft_frozen.md`）；`docs/01_Contract_Spec_v0.11.md`（对照 `docs/review/01_v0.10_review_disposition.md`）
- 方法：v1.0 → v2.0 逐节 diff（全部 47 个变更块逐一核对）；两份示例 YAML 按 §4.2.6 与 01 V-00..V-17 逐条手工走查；01 v0.11 全文通读，第十轮处置的五个重点按"恢复臂四条时间线 × 崩溃点"逐格推演
- 未修改任何被审文档

## 0. 结论

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| 第一部分：HLD v2.0 | **NO-GO** | 2 | 10 | 7 | 1 |
| 第二部分：01 v0.11 | **NO-GO** | 0 | 5 | 3 | 1 |
| 同步项（v2.0 核心修订 ↔ 01 现有条文） | 单列，不计入第二部分结论 | 0 | 2 | 5 | 1 |

一句话理由：
- **HLD v2.0**：两处冻结核心被实质改动，而文档声称"原样保留，未作任何放宽"。一是 mic/GBS 以 root 执行半可信内容，使 D8/D21 的凭据进程隔离在同一台主机上失效（H2-01）。二是 D11 的"长等待不占执行槽"改变了冻结的状态机、task 模型和计时口径，却没有给出机制，也没有走勘误通道（H2-02）。另外示例一 `full_pipeline.yaml` 按文中的支配定义无法通过 release_requires 静态检查（H2-03）。Benchmark 的统计/SPEC 判定规则不可执行（H2-09）；优化收益没有确定性的判定者，也没有撤销路径（H2-10）。
- **01 v0.11**：第十轮修入的恢复臂在四条时间线中有三条不闭合。一是静默条件弱于 HLD，且 release_outcome / reconcile_report 不校验执行权持有者（C11-01）。二是 epoch 写进载荷、又与连接绑定、再叠加"receipt 先于 guard"，三者组合后，现实中的 ACK 丢失（即断连）路径走不通（C11-02）。三是 publishing 期 D12 漂移会阻断恢复臂对账，与 HLD §8.3 冲突（C11-03）。此外 DispatchReceipt 在 §2.5 与 §5.1 各有一套互相矛盾的模型（C11-04）；broker 在 dispatch 已 ACK 之后崩溃时，没有任何规则触发重派（C11-05）。
- **勘误 E-01 仍有效**：v2.0 §17 保留原文；v2.0 新增的 release_requires 静态检查沿用同一"支配"概念，与 V-13b 一致（但支配定义本身需按 H2-03 补 join 语义，V-13b 同步受益）。

---

## 第一部分：HLD v2.0

### H2-01 ｜ BLOCKER ｜ mic/GBS 以 root 执行半可信内容，凭据物理隔离失效

**位置**：HLD v2.0 §2.3 mic 行；§7.6.1 LocalGbsBackend；§8.1；§8.5 末条；§10 部署拓扑；D8、D21、N7

**问题**：v2.0 把"mic 需特权执行，经 deploy 特权 launcher"定为常规路径。`mic create` 以 root 把被测 RPM 安装进镜像根，期间会执行各包 spec 中的 `%pre/%post` scriptlet 以及 ks 文件的 `%post` 段。这些内容来自 snapshot 与 series，其中包括 LLM 生成的修复/优化 patch，§8.1 也明确承认受信来源可能经间接提示注入产出恶意构建脚本。chroot 内的 root 进程可以逃逸。release broker 凭据、Build Gateway 会话与它们在同一台主机上（§10），彼此之间只靠 OS 用户和文件权限隔离（§8.5），而这层隔离对 root 无效。结果是 D8/D21 "凭据仅存在于 broker/Gateway 进程"这一物理强制不再成立，相当于放宽了冻结安全模型。N7 明文规定"凭据隔离不在此豁免范围"。GBS 全量构建经 sudo 建 buildroot，是同类暴露：v1.0 已有，v2.0 全量构建把它扩大了。

**依据**：
- §7.6.1："镜像阶段 = GBS 全量构建至本地仓库 → `mic create`（…mic 需特权执行，经 deploy 特权 launcher）"
- N7："完整容器级安全沙箱（…）；凭据隔离不在此豁免范围，由 broker 进程隔离保证"
- §8.1："patch 与其触发的构建脚本视为半可信——不做完整容器沙箱（N7），控制面为：凭据物理隔离于 broker（8.3）…间接提示注入可使受信来源产出恶意构建脚本"
- §10："内网主机（单机）| 编排进程、Approval 服务、Release broker、Build Gateway、…GBS 与 mic、各 Agent worker"

**候选改动**：
```diff
 §7.6.1 LocalGbsBackend
-…镜像阶段 = GBS 全量构建至本地仓库 → `mic create`（镜像 ks 配置来源 `[待补充]`，mic 需特权执行，经 deploy 特权 launcher）。镜像产物入镜像存储（§7.8）。
+…镜像阶段 = GBS 全量构建至本地仓库 → `mic create`（镜像 ks 配置来源 `[待补充]`）。镜像产物入镜像存储（§7.8）。
+**特权构建隔离（定案）**：凡以 root 执行来自 snapshot/series 内容的步骤（mic create 的 RPM scriptlet 与 ks %post、GBS buildroot 的 sudo 段）一律在**一次性构建 VM** 内执行——独立内核边界；宿主侧不向 VM 挂载 Ledger、凭据库、Gateway 会话存储，不暴露任何 control-plane socket；VM 仅经只读导出通道交回产物，产物按镜像存储提交协议（§7.8）入库并复验 digest。deploy 特权 launcher 只负责 VM 的启动/销毁/产物回收，宿主 root 上下文中不执行任何 snapshot/series 内容。
 §8.1
-…控制面为：凭据物理隔离于 broker（8.3）、能力句柄按授权注入（5.1.1）、worker 子进程可强杀、发布必经 token。
+…控制面为：凭据物理隔离于 broker（8.3）、能力句柄按授权注入（5.1.1）、worker 子进程可强杀、发布必经 token、**以 root 执行半可信内容的步骤在内核边界之外进行（§7.6.1 特权构建隔离）——OS 用户隔离对 root 无效，故此项不属 N7 豁免**。
 §10 部署拓扑表 新增一行
+| 内网主机内的一次性构建 VM | mic / GBS 特权步骤；无凭据、无控制面 socket、无 Ledger 访问 |
 §12 E0 预检 追加
+宿主虚拟化能力（KVM）与构建 VM 镜像可用性；不满足即阻断上线（不提供宿主 root 直跑降级）。
```
**副作用**：每次镜像构建多出 VM 启停开销（几十秒量级，相对小时级的全量构建可以忽略）；P3 交付增加构建 VM 镜像与 launcher；mic 依赖的 loop 设备挂载改在 VM 内进行，宿主反而更干净。GBS 增量构建若同样经 sudo，也须一并迁入 VM，否则等于留着同一缺口。
**配套测试/夹具**：§11.3 新增"特权构建隔离 E2E"：在被测包 `%post` 中尝试读取 broker 凭据文件、读取 Gateway 会话、连接 approval/broker/worker socket、写 Ledger，必须全部失败并告警。01 CF-IPC-03 扩展该断言。FakeImageBuilder 夹具需暴露"隔离边界"接口，便于在 Fake 下断言调用确实经由 launcher。

---

### H2-02 ｜ BLOCKER ｜ D11 "长等待不占执行槽"改动冻结核心，且未给出机制、未走勘误通道

**位置**：D11（v2.0 补充）；§4.3.1 状态机与"长等待不占执行槽"条；§4.5；§4.2.4 陈旧性条；§5.1.2；§8.6；01 C-07 / C-13 / §3.4（同步项 S-01）

**问题**：
1. **机制空缺，任何一种实现都会破坏冻结语义**。节点等待 Quickbuild 或板子时 worker 是否存活，文中没有交代。如果 worker 存活，该 Run 进入 paused、释放执行槽后，另一个 Run 会进入执行，于是两个 Run 同时持有 worker/资源，违反 D11"执行槽 = 持有 worker/资源执行中""单执行 Run"。如果 worker 不存活，就需要 task 级的挂起/续接：execute 中途退出且没有 HandoffResult，这次 attempt 映射成什么？续接用哪个 attempt、哪个 dispatch？hard timeout 与心跳租约如何计？这些在冻结的 task 模型（§5.1.2"注入 ctx → 调 execute → 结果经 IPC 回传"）里都不存在。
2. **唤醒通道空缺**。gate 的 resume 走 Approval outbox（§4.4），而外部等待结束后由谁写 Ledger、如何去重、如何重新分派，都没有定义。§8.5 规定 Gateway 只接受编排 UID，没有反向通知。
3. **状态机未更新**。状态图与"状态穷尽"列举中仍然只有 `paused(gate)`。
4. **计时自相矛盾**。§4.5 同一段先写"wall_clock 排除 paused 时段"，后写"因远程构建/板子排队而 paused 的时段**计入**预算"。§4.2.4 的 join timeout 仍写"排除 paused 与 publishing 等待时段"。
5. **锁序未定**。执行槽与板子租约是两类资源，获取顺序没有规定。"持租约排队等槽"与"持槽等租约"同时出现时，有没有死锁全靠实现者自己发挥。
6. **程序问题**。冻结核心的修订应走勘误通道（先例 E-01），本版却以"补充"方式写入，同时在头部声明"原样保留，未作任何放宽"。

**依据**：
- v1.0 D11："执行槽 = 持有 worker/资源执行中；paused 不占执行槽…"
- v2.0 D11："**v2.0 补充**：等待 Quickbuild 远程构建或排队等板子期间，Run 同 gate 等待一样不占执行槽"
- §4.3.1："状态穷尽：…/ paused(gate) / …"；"计时口径：外部等待计入 run_budget 与环时长"
- §4.5："wall_clock 排除 paused 时段；…因远程构建/板子排队而 paused 的时段**计入**预算"
- 01 C-07："gate_wait_only | running | 仅剩 gate 等待、无可运行工作 | paused（释放槽）"；01 §3.4："run_budget：…排除 paused 与 publishing 时段"

**候选改动**（定案方向：外部等待是编排侧的等待项，任何 worker 都不跨越等待存活）：
```diff
 D11 结论列
-**v2.0 补充**：等待 Quickbuild 远程构建或排队等板子期间，Run 同 gate 等待一样不占执行槽（资源按类别计额：本地构建 / 镜像构建 / 板子 / 远程构建配额）
+**勘误 E-02（经三方评审通道生效后方入基线）**：引入**外部等待项 ExternalWait**（编排侧 Ledger 记录，与 gate 等待项同构）。外部等待期间不存在任何 worker：
+① 资源排队（板子/本地镜像构建额度）——资源租约在**分派前**由编排层授予（dispatch precondition），未获租约的 dispatch 处于 awaiting_resource、不 spawn worker；
+② 远程构建——task 以 side_effect 提交后，以框架保留结果 `sys.await_external{wait_ref}` 结束本 attempt（不走 DSL 路由、不计入 retry.max），编排同事务登记 ExternalWait；编排侧 poller 经 Build Gateway 查询到终态后 CAS 解决等待项，经与 resume outbox 同构的 wake outbox（outbox_id 去重）对**同一 dispatch** 分派续接 attempt（dispatch_id 不变 ⇒ 效应键稳定，提交效应经 probe/succeeded 复用命中，不重复提交）；
+③ Run 级：仅剩 gate 等待项与外部等待项、无可运行工作 → paused(wait)，释放执行槽；锁序 = 先租约后执行槽，持有已授租约的 Run 在 queued 中优先出队。
 §4.3.1 状态穷尽
-… / running / paused(gate) / **publishing** …
+… / running / paused(wait: gate | external) / **publishing** …（状态图同步改标签）
 §4.5
-…计数持久化于 Ledger 随恢复延续；wall_clock 排除 paused 时段；…
+…计数持久化于 Ledger 随恢复延续；wall_clock 排除 **gate 等待致 paused** 与 publishing 时段，**计入**外部等待致 paused 的时段（Gateway 会话失效等待运维登录的区间除外）；…
 §4.2.4 陈旧性
-…计时口径同 §4.5（排除 paused 与 publishing 等待时段）。
+…计时口径同 §4.5（按等待类别扣除：gate 等待与 publishing 排除，外部等待计入）。
 §17 附录 A15 追加
+- E-02（D11 外部等待）：…（规则文本以 01 同步后的 C-07'/C-08d/§3.4' 为准）
```
**副作用**：01 §1.2 SysOutcome 新增保留结果 `sys.await_external`，V-05/V-06 必须把它排除在路由穷尽之外；SDK 需提供 `ctx.await_external(ref)`；§8.6 的"超过配置时长仍未登录 → sys.timeout"改为由编排在 ExternalWait 超时时合成；model-based 测试的状态空间扩大。不过这一方案让 worker 生命周期与冻结的 task 模型保持一致，hard-kill、心跳、孤儿回收逻辑都不需要改。
**配套测试/夹具**：§11.3 追加以下用例：外部等待期间"无 worker 存活"断言；paused(wait) 时另一 Run 取得执行槽；wake outbox 重复投递不重复分派；续接 attempt 的提交效应复用（不重复提交 Quickbuild）；"两 Run × 一板 × 一槽"的租约/执行槽锁序 model-based 无死锁；计时按等待类别扣除。01 CF-SM-01 矩阵加入新状态与新命令；CF-SM-10 增 external 变体。FakeQuickbuild/FakeBoardPool 夹具需支持"延迟完成"和"重复完成通知"。

---

### H2-03 ｜ MAJOR ｜ 示例一 `full_pipeline.yaml` 按文中支配定义无法通过 release_requires 静态检查；produces 无法按 mode 区分

**位置**：§4.2.1 示例一；§4.2.6 规则①与支配性条；§5.1.1 注册信息；01 V-13b / V-15（同步项 S-03）

**问题**：
1. §4.2.6 要求"release_requires 每一类报告的生产节点存在且**支配** human_review"，支配的定义是"到消费节点的**每条路径**都必须先经过生产节点"。示例一中存在路径 `compile_rpm → compile_image →(image_ready fan-out) review_static → join:pre_final_review → review_final → ci_plan → human_review`，这条路径不经过 `ut` 与 `benchmark`。按字面定义，ut_report 与 bench_report 的生产者不支配 human_review，示例一会被拒绝加载，与"两份示例即校验器验收用例，必须可通过校验"相矛盾。执行层面 join 要求全部来源到达（AND 语义），所以 ut 实际上必然先行；但 HLD 与 01 的支配定义都是图路径定义，没有给出 join 的 AND 语义。
2. produces 按 agent_type 注册，而 compiler 一个类型对应两个模式（rpm/image）。于是 `compile_rpm` 与 `compile_image` 都被视为 build_report 和 image_report 的生产者。删除镜像节点后，若 release_requires 里保留 image_report，校验器会认为由 compile_rpm 满足，§2.4"删除镜像节点"一行就失去了拦截力。status_set 同理：compile_rpm 上可以合法写出 `on: image_ready`。

（其余规则已逐条走查：V-07 三条声明环边移除后无环；join 的 V-09/V-10/V-11/V-12 双约束对 ut_fix_loop、opt_loop、image_fix_loop 均成立；bench_gate 的 V-15 支配成立；V-13b 中 ci_plan 支配 human_review 成立。示例二线性路径上 release_requires 支配成立，问题见 H2-14。）

**依据**：§4.2.6："hard-required 上游与 threshold gate 的指标来源节点均做支配性检查——到消费节点的每条路径都必须先经过生产节点"；"静态检查：每一类报告的生产节点存在且支配 human_review"；§5.1.1："注册信息另声明：`produces`（产出的报告类型）…"

**候选改动**：
```diff
 §4.2.6
-hard-required 上游与 **threshold gate 的指标来源节点**均做**支配性检查**——到消费节点的每条路径都必须先经过生产节点，仅存在不满足，且消费同 series 结果；
+hard-required 上游、**threshold gate 的指标来源节点**与 **release_requires 各报告的生产节点**均做**支配性检查**，判定图为 **AND-join 支配**：普通节点 n 的支配者 = 到 n 的每条路径必经的节点；join 节点 j 的支配者 = {j} ∪ ⋃_{s∈wait_for(j)} Dom(s)（全部来源到达才触发，任一来源的必经节点均为 j 的必经节点）；j 下游节点照常继承。仅存在不满足，且消费同 series 结果；V-13b（E-01）的"支配链最近者"在 AND-join 支配树上取深度。
 §5.1.1 注册
-注册信息另声明：`produces`（产出的报告类型）、hard-required 上游、`input_requirement`（…）、所需能力句柄。
+注册信息另声明（**均按 mode 声明**，无 mode 的 Agent 用缺省键 `_`）：`status_set_by_mode`、`produces_by_mode`、hard-required 上游、`input_requirement`、所需能力句柄；校验器以节点的 (agent_type, mode) 取集合。
```
**副作用**：01 V-13b、V-15 需改用同一支配定义（V-13b 属勘误 E-01 的形式化，这里只是加严判定图，不改变规则意图，建议在同步时登记为 E-01 的澄清而非新勘误）；CompiledPipeline 的支配缓存需要按 AND-join 计算。
**配套测试/夹具**：CF-DSL-FLAG 扩为四份示例原文字节加载；新增 CF-DSL-RR-a（full_pipeline 通过：ut/benchmark 经 AND-join 支配 human_review）、RR-b（把 bench_gate 移出 join 来源后 benchmark 不再支配 → 拒）、RR-c（删除 compile_image 但保留 image_report → 拒，不得由 compile_rpm 满足）；CF-FIX-00 注册集按 mode 拆分（compiler.rpm / compiler.image）。

---

### H2-04 ｜ MAJOR ｜ 新能力句柄没有落到冻结的 worker 数据面枚举与 D6 单一事实源上；跨 Run 共享存储对 worker 可写

**位置**：§5.1.1 能力句柄；§7.7、§7.8；§8.5 入向第一条、Build Gateway 通道条；D6；01 §5.1（同步项 S-02）

**问题**：BoardPool、BaselineCache、ProfileStore、ImageBuilder、Gateway 转发都需要写操作，包括租约申请/释放/续租、刷机失败计数、镜像入库、基线缓存登记、Profile 入库与陈旧标记、远程构建提交/查询/取消。这些操作都不在冻结的 worker 数据面封闭枚举里。权威状态放在哪里也没有定义：如果句柄在 worker 内直接写本地文件或数据库，就形成了第二事实源（违反 D6）；如果经 RPC，就必须扩充枚举，而这会扩大半可信 worker 的攻击面，每条命令都需要定义归属校验。更关键的是，BaselineCache 与 ProfileStore 是**跨 Run 共享**的。如果 worker（正是执行半可信构建内容的进程）可以写入，它就能投毒其他 Run 的 A/B 基线与优化输入。

**依据**：§8.5："worker socket 仅开放**数据面命令**（显式枚举：side_effect 状态迁移、trace、artifact 索引提交、series candidate 提交）"；§8.5（v2.0）："远程构建请求经编排进程的能力句柄转发"；D6："单一 SQLite Ledger…为 system of record…Ledger 直写者唯一"

**候选改动**：
```diff
 §8.5 入向
-worker socket 仅开放**数据面命令**（显式枚举：side_effect 状态迁移、trace、artifact 索引提交、series candidate 提交）；
+worker socket 仅开放**数据面命令**（显式枚举：side_effect 状态迁移、trace、artifact 索引提交、series candidate 提交；**勘误 E-03 追加**：`resource_lease_renew` / `resource_lease_release`（仅本 task 已获授租约；授予在分派前由编排完成，见 E-02）、`image_commit`（镜像存储提交协议，§7.8）、`profile_put`（写入 Profile 库**待验区**，键由编排按本 task 连接上下文推导，不信载荷）、`remote_build_submit` / `remote_build_query` / `remote_build_fetch_logs`（编排以连接上下文校验 run/task 归属后转发 Gateway；`cancel` 仅由编排在 cancel/fail_safe/supersede 时自行发起））；
+**跨 Run 共享存储（基线镜像缓存、Profile 库正式区、Benchmark 套件注册表）对业务 worker 只读**——写入仅由框架自有 task（保留 agent_type `sys.baseline_build` 等）经编排事务提交；上述全部状态以 Ledger 为权威源（D6），存储目录只存内容寻址 blob。
```
**副作用**：01 CommandName 再扩充（约 7 条），需要注册表、幂等域与 CF-IPC 攻击用例；Profile 需要定义"待验区 → 正式区"的晋升规则（建议：所属 Run 以 succeeded 关闭，或按 tree_digest 键隔离、只供同 tree 使用，见 H2-15）。
**配套测试/夹具**：CF-IPC-01/02 扩到新命令（跨 task 续租被拒；查询他 Run 的 build_ref 被拒）；新增"worker 写基线缓存被拒""Profile 待验区不被他 Run 消费"。

---

### H2-05 ｜ MAJOR ｜ 板子池租约：回收缺 fencing、板上状态不复位、失败归因与配额未定

**位置**：§7.7；D19；§7.6.3；§7A.3 测量方法

**问题**：
1. **回收即重分配，没有 fencing**。心跳丢失时，编排无法确认旧持有者（worker、它的 sdb 会话、板上进程）已经终止。如果马上把板子分给下一个 task，旧持有者的刷机或测量会与新持有者并发进行，导致刷机损坏、Benchmark 数据被污染，而交叉测量与静止判定都发现不了另一方的写入。broker 场景已经定了"静默确认"（§8.3①），板子没有沿用。
2. **板上残留**。回收后没有规定"恢复到已知状态"（重刷，或至少重启加健康检查），新 task 会继承前一个 task 遗留的进程和文件。
3. **失败归因**。"刷机失败三次标记维护中"没有区分镜像归因与板归因。同一个坏镜像在三块板上各失败一次，就会把整个池打成维护中。计数是连续还是累计、持久化在哪里，也没有规定。
4. **配额与饥饿**。单个 Run 可同时持有的板数上限、能力匹配下的饥饿（能力强的板被弱需求占用）都未规定。
5. **A/B 交叉需要"同板序列租约"**。基线与被测在同一块板上交替刷写、测量是交叉测量的前提，但租约模型只有单次独占。

**依据**：§7.7："租约与 task 绑定，task 终结或心跳丢失时回收"；"刷机失败三次标记板子'维护中'并告警"；§7A.3："基线与被测交叉执行"

**候选改动**：
```diff
 §7.7 独占租约
-- **独占租约**：UT、Benchmark、profile 采集按"板型 + 能力"申请租约，FIFO 排队；租约与 task 绑定，task 终结或心跳丢失时回收；…
+- **独占租约**：UT、Benchmark、profile 采集按"板型 + 能力"申请租约，FIFO 排队，租约记录在 Ledger（D6），带单调 `lease_epoch`；租约与 task 绑定。**回收 = draining → 复位 → 可分配**：心跳丢失或 task 终结后先进入 draining，须**旧持有者进程组 reap 确认**（同 §8.3① 静默定义）后执行复位（重启 + 健康检查；Benchmark 用途另需重刷基线镜像），才可分配；板子适配器对每条板上命令携带 lease_epoch，旧 epoch 命令一律拒绝并审计（适配器无法板侧强制时，以"reap 确认 + 重启"作为唯一 fencing）。
+- **序列租约**：Benchmark 交叉测量申请 `sequence` 租约，在单一租约内按 ABAB 序列刷写与测量，中途不释放。
+- **配额**：单 Run 同时持有板数上限（配置，默认 1）；能力匹配取"满足需求的最低能力板"以防饥饿。
 §7.7 刷机
-…刷机失败三次标记板子"维护中"并告警，不再分配。
+…刷机失败按归因计数（Ledger 持久化）：同一镜像在 ≥2 块板上失败 → 归因镜像（ImageReport 标记坏镜像，板子不计数）；同一板对 ≥2 个不同镜像连续失败 3 次 → 标记"维护中"并告警。
```
**副作用**：draining 与复位会延长板子周转时间，需要计入 R19 的检测信号；板型适配器接口新增 `lease_epoch` 参数。
**配套测试/夹具**：§11.3 追加：旧持有者未 reap 前新租约不授予；适配器拒绝旧 epoch 命令；坏镜像在三块板上失败 → 镜像归因、板子不下线；单 Run 持板上限；序列租约中途不被抢占。FakeBoardPool 需支持 epoch 与归因计数。

---

### H2-06 ｜ MAJOR ｜ Build Gateway：会话注入入口缺失、会话失效时 probe 会把 Run 判死、远端取消未传导

**位置**：§8.6；§8.5 Build Gateway 通道条；§5.2 远程构建效应类别；01 §4.3 probe 能力矩阵

**问题**：
1. **会话注入入口缺失，且与"只接受编排 UID"冲突**。浏览器在运维机器上完成 SSO 后，会话凭据必须经某个通道进入 Gateway。这是一个凭据入向的特权接口，但它的认证（谁可以注入）、绑定（注入的会话账号是否为配置的服务账号，用于防止会话固定或错账号构建）、传输方式（运维机器到内网主机）都没有定义。§8.5 又写着 Gateway 只接受编排 UID。
2. **会话失效时 probe 会把 Run 判死**。远程构建效应的对账依赖 Gateway 查询。会话失效时 probe 只能返回 indeterminate；按 01 §4.3，有限重试耗尽后，若该效应不是 replay_safe 就进入 unknown + sys.error。运维侧的会话事件因此会让 Run 失败，与 §8.6"外部等待、其余节点不受影响"矛盾。
3. **cancel / fail_safe / series supersede 没有传导到远端**。killpg 只覆盖本地进程，远程构建会继续占用配额并产生迟到结果；§8.6 列了"取消构建"，但没有触发规则。
4. **Gateway 自身的崩溃恢复未定义**。提交已发出但响应丢失时，Gateway 侧没有幂等 receipt；Gateway 重启后会话丢失，又落回第 2 条。
5. **日志与产物元数据可能内嵌会话 URL 或 token**，进入 worker 前没有脱敏要求（§8.4）。

**依据**：§8.6："会话失效时向运维发出告警，并在运维机器上弹出浏览器窗口，由运维本人登录；登录得到的会话仅保存在 Gateway 进程的受限存储中"；"会话失效期间，依赖远程构建的节点进入外部等待…其余节点不受影响"；§8.5："Gateway 只接受编排进程 UID"；01 §4.3："indeterminate → 有限重试…耗尽后——若 replay_safe → …否则 unknown + sys.error"

**候选改动**：
```diff
 §8.6
+- **会话注入通道（定案）**：Gateway 另开**运维会话 socket**（独立 OS 用户 + peer credential，仅运维特权用户）；运维机器上的登录助手完成 SSO 后，经 SSH 端口转发调用该 socket 的 `session_install{session_blob}`；Gateway 安装前调用 Quickbuild 身份接口校验会话主体 == 配置的服务账号，不符即拒并审计；会话不落盘或仅落 Gateway 专属加密存储。
+- **会话失效期间的对账**：Gateway 对查询类请求返回 `dependency_unavailable`，probe 结果映射为 **deferred**——不消耗 probe_retry_max、不进入 unknown，对账推迟到会话恢复（计入外部等待，不计预算）。
+- **取消传导**：编排在 cancel / fail_safe 取消分支 / series supersede 退役在飞任务时，对该任务已登记的远程构建发起 `remote_build_cancel`（幂等；失败告警不阻断终局）。
+- **Gateway 幂等**：提交以效应 idem_key 指纹为远端标记与 Gateway 请求去重键（见 H2-07），Gateway 崩溃后由 probe 按标记归因。
+- **脱敏**：日志与产物元数据进入 worker 前按 §8.4 规则剥离会话凭据形态的字段。
```
**副作用**：01 ProbeOutcome 增加 `deferred`，CF-EF-02 的矩阵需要加一个轴值；deploy/ 需交付登录助手与运维会话 socket 的 provisioning。
**配套测试/夹具**：FakeQuickbuild + FakeSSO：错账号会话被拒；会话失效期间 probe deferred 不计次，恢复后对账；cancel 触发远端取消；Gateway 提交后崩溃，按标记 probe 命中；日志脱敏断言。

---

### H2-07 ｜ MAJOR ｜ 镜像存储不在 Blob 提交协议内；镜像与远程构建的 probe 身份错误

**位置**：§5.2 效应类别要求；§7.8 镜像存储；§7.5 Blob 提交协议；01 §4.1 idem_key

**问题**：
1. **镜像存储没有提交协议**。mic 产物写到一半时崩溃，按"存在性"做的 probe 会命中半成品，然后以 succeeded 复用一个损坏的镜像，后续刷机与测量都建立在坏镜像上。GC 与写入并发时也有同样问题。
2. **镜像 probe 的键用错了**。§5.2 写的是"按缓存键查存在性"，而 §7.8 唯一定义的缓存键是**基线**键，不含 series/tree_digest。含 patch 的被测镜像按这个键去查，会命中基线镜像或其他 Run 的镜像，误判为"已发生"。
3. **远程构建按 run/task 标识归因，粒度不够**。同一 task 内的多次远程构建（不同 effect_call_id 或 repeat_seq），以及跨 attempt 的异参调用，靠 run/task 标识无法区分。01 的 probe 必须定位到"本效应记录"（idem_key + version）。

**依据**：§5.2："镜像构建 = 可 probe（镜像存储中按缓存键查存在性）；远程构建（Quickbuild）= 可 probe（按提交时写入的 run/task 标识查询远端构建记录与状态…）"；§7.8："镜像体积大，独立于普通 artifact 目录存放"；§7.5 Blob 提交协议原文

**候选改动**：
```diff
 §5.2 效应类别要求
-**镜像构建 = 可 probe（镜像存储中按缓存键查存在性）**；**远程构建（Quickbuild）= 可 probe（按提交时写入的 run/task 标识查询远端构建记录与状态，提交即带该标识以便归因）**；
+**镜像构建 = 可 probe（按效应 idem_key 查 Ledger 镜像索引并复验内容 digest；仅已完成提交协议的镜像可被命中）**；**远程构建（Quickbuild）= 可 probe（提交即写入效应标记 = idem_key 指纹 + version，按标记查询远端构建记录；run/task 标识另写入供人工归因）**；
 §7.8 镜像存储
-- **镜像存储**：镜像体积大，独立于普通 artifact 目录存放；以 `image_ref = (…)` 引用；…
+- **镜像存储**：镜像体积大，独立于普通 artifact 目录存放，但**适用 §7.5 Blob 提交协议全部条款**（临时命名空间写入 + active-upload lease → fsync → rename 至 digest 路径 → Ledger 索引事务；GC 仅回收超安全年龄且无 lease 的对象；索引前复验 digest）；大文件以分块 digest 清单承载；以 `image_ref = (…)` 引用；…
```
**副作用**：镜像入库多一次全量 digest 计算（GB 级，分钟量级，相对构建时长可以接受）；01 新增 ImageRecord 与 image_commit 命令（与 H2-04 合并）。
**配套测试/夹具**：镜像提交逐点崩溃注入（复用 CF-BLOB-02 点位）；半成品不被 probe 命中；同一 task 内两次远程构建的 probe 各自归因；被测镜像与基线镜像互不命中。

---

### H2-08 ｜ MAJOR ｜ 基线镜像缓存：失效条件缺失；Quickbuild 能否按 snapshot 构建藏在 [待补充] 里；写入权与并发未定

**位置**：§7.8 BaselineCache；D5；D19；§7.6.1 QuickbuildBackend；§7A.3 测量方法

**问题**：
1. **失效条件缺失**。缓存键不含工具链与构建环境身份：gbs/mic 版本、GBS 全量构建所依赖的、snapshot 之外的基础仓库源（若指向滚动仓库则每天都不一样）、ks 内容 digest、编译器及其相关构建选项。也没有定义 TTL、手动失效、"已知坏基线"撤销。
2. **Quickbuild 是否按 pinned snapshot 构建是架构决策，不是环境事实**。如果远程构建基于远端工程的当前状态（滚动依赖），被测镜像与几天前缓存的基线镜像之间的差异就不只来自 patch，A/B 结论失效，D5 对远程后端也不成立。这一点被放在"Quickbuild 提交方式 `[待补充]`"里，按评审说明属于"实际上藏着一个未定的架构决策"。
3. **"基线测量结果缓存，但每次 A/B 仍重测"自相矛盾**：缓存下来的结果到底用于什么，没有说明。
4. **并发**：两个 Run 同一 snapshot 同时未命中缓存，会重复做全量构建，需要 single-flight。
5. **基线构建失败时 Benchmark 的 status 与报告呈现未定义**。
6. **写入权**：缓存写入方是谁（见 H2-04）。

**依据**：§7.8："缓存键 = (snapshot_id, 构建配置摘要, 后端, 镜像配置)…基线测量结果按 (基线镜像, 套件版本, 板型) 同样缓存，但每次 A/B 仍按交叉方式重测"；D5："Run 启动时 pin 多仓 snapshot manifest…Run 全程锁定"；§7.6.1："Quickbuild 的提交方式（表单字段、目标工程）`[待补充]`"

**候选改动**：
```diff
 §7.8 基线镜像缓存
-- **基线镜像缓存（BaselineCache）**：缓存键 = (snapshot_id, 构建配置摘要, 后端, 镜像配置)；…基线测量结果按 (基线镜像, 套件版本, 板型) 同样缓存，但每次 A/B 仍按交叉方式重测以控制板子状态漂移（§7A.3）。
+- **基线镜像缓存（BaselineCache）**：缓存键 = (snapshot_id, 构建配置摘要, 后端, ks 内容 digest, **构建环境身份** = {gbs/mic 版本, buildroot 基础仓库源的 pin 摘要, 编译器版本})；任一分量变化即不命中。**失效**：TTL（默认 14 天）、运维手动失效、坏基线撤销（撤销后引用它的在途 BenchReport 标记 baseline_revoked）。**仅框架自有 task `sys.baseline_build` 可写**（H2-04），同键 single-flight（后到者以外部等待挂起，E-02）。基线构建失败 → Benchmark 返回 `baseline_unavailable`（缺指标，gate fail-closed，报告显式标注）。
+- **远程后端约束（定案）**：远程后端必须能以完整 snapshot pin（含依赖仓 commit）提交；若 E0 确认 Quickbuild 无法 pin，则 quickbuild 后端的基线**不得跨 Run 复用**，必须与被测镜像同批构建，且 ImageReport 标注 `unpinned_remote=true`，release_requires 视其为不满足 image_report（不得据此发布）。
+- **基线测量缓存**仅供 `quick` 模式展示参考，不进入任何 gateable 字段（§7A.3）。
```
**副作用**：缓存命中率下降（工具链更新即全量失效，符合预期）；Quickbuild 若无法 pin，远程后端在发布路径上的价值大幅降低，这一点应在总部对齐时显式确认。
**配套测试/夹具**：缓存键各分量逐一变化的命中/失效矩阵；single-flight 并发；unpinned_remote 时跨 Run 复用被拒，且 release_requires 不满足；baseline_unavailable 路由与报告标注。

---

### H2-09 ｜ MAJOR ｜ Benchmark 判定规则不可执行；测量模式对门禁/发布的效力未定；判定依据未固化进 execution manifest

**位置**：§7A.3 统计判定标准、SPEC 判定、测量模式、BenchReport；G9、G11；D12；01 §1.5、BenchReport

**问题**：
1. **统计规则只有名词**。估计量（均值还是中位数）、区间方法、检验方法与显著性水平、最小有效样本数（剔除无效样本之后）、多指标多重比较校正、方向归一（越大越好 / 越小越好），全都未定义。regression_pct 是点估计还是区间上界、不显著时取什么值，也未定义。同一组数据，不同实现会得出不同的 gate 结论，"判定靠统计规则"无法落地。
2. **SPEC 判定在噪声下缺第三值**。均值在 SPEC 内、但置信区间跨越 SPEC 线时，判 IN 还是 OUT 没有规定。
3. **模式效力未定**。快速模式与单项模式样本少，若产出与全量同型的 BenchReport，就能满足 bench_gate 与 release_requires，等于可以凭快速测量发布。模式在哪里选择（节点配置还是 Agent 运行时决定）也未定义。
4. **判定依据未固化**。套件版本、SPEC、统计配置都是外部可变内容，直接决定 gate 结论，却不在 execution manifest 里。Run 进行中有人修改 SPEC，判定就会改变，而且没有漂移检测。
5. **"一次完整记录"的测量记录** schema、密级（日志可能含源码路径/符号，应为 internal_code）以及它与 BenchReport 的关系均未定义。

**依据**：§7A.3："统计判定标准：测量波动按统计方法判定（重复次数、置信区间、显著性检验），判定标准随套件版本固定并写入报告"；"Benchmark 对每个指标给出 SPEC-IN / SPEC-OUT 判定"；"顶层 `regression_pct`（全部指标中的最大回归…）与 `spec_out_count`"；G11："是否达标、是否回归由 SPEC 与统计规则判定"

**候选改动**（给出缺省策略，并允许套件版本以同构参数覆盖，以对齐 TPMS 改造）：
```diff
 §7A.3 统计判定标准
-- **统计判定标准**：测量波动按统计方法判定（重复次数、置信区间、显著性检验），判定标准随套件版本固定并写入报告，…
+- **统计判定策略 BenchPolicy（随套件版本固定，缺省值定案）**：每臂有效样本 n ≥ 10（剔除静止判定失败与争抢作废样本后计）；ABAB 交叉；估计量 = 中位数；效应 = 方向归一后的相对中位数变化（越小越好的指标取反）；区间 = 95% bootstrap（BCa，10⁴ 次重采样，种子固定写入报告）；检验 = Mann–Whitney U 双侧，α=0.05，多指标 Holm 校正。指标"显著回归" ⇔ 校正后 p<α ∧ 区间不含 0 ∧ 效应为劣化方向。`regression_pct` = 显著回归指标的效应点估计最大值（无显著回归 = "0.00"；任一指标样本不足 → 字段缺失 → gate fail-closed）。
+- **SPEC 三值判定**：区间整体在 SPEC 内 → SPEC-IN；整体在外 → SPEC-OUT；跨线 → SPEC-INCONCLUSIVE。`spec_out_count` 计入 OUT 与 INCONCLUSIVE（fail-closed），另列 `spec_inconclusive_count`。
+- **模式效力**：模式由节点配置 `config.mode ∈ {full, single, quick}` 声明（Agent 运行时不得改变）；BenchReport 携带 `mode` 与 `gate_eligible`（仅 full 且满足 BenchPolicy 样本量时为 true）；threshold 解析与 release_requires 只认 gate_eligible=true 的 BenchReport，否则视为缺失（fail-closed）。
+- **固化**：execution manifest（D12）增加 `bench_suites_digest`（所用套件版本集合）、`spec_digest`、`bench_policy_digest`；Run 中途变化按 D12 失配处理。
+- **测量记录**：MeasurementRecord 为内容寻址 artifact（密级 ≥ internal_code），BenchReport 以引用携带；gateable 字段必须可由框架统计库从 MeasurementRecord 确定性复算（见 H2-11）。
```
**副作用**：每臂 10 次以上的有效样本会显著增加板子占用（R19/R20 需要重估）；快速模式无法单独通过 gate，开发期应使用 terminal 子集流水线；若 TPMS 现有方法与缺省策略不同，以套件版本覆盖参数，但必须是同构参数集，不允许自由代码。
**配套测试/夹具**：BenchPolicy golden 数据集（固定样本 → 期望判定：不显著、跨 SPEC 线、样本不足、方向相反、多指标 Holm 各一例）；quick 报告进入 gate → fail；Run 中修改 SPEC → D12 失配；01 BenchReport 增字段的 fixture。

---

### H2-10 ｜ MAJOR ｜ 优化环：预算触顶会杀掉业务 patch；收益没有确定性判定者；没有撤销路径

**位置**：§7A.4 产物与回流；D18；§7A.0 Optimization 行；§4.5；§4.2.1 示例一 opt_loop 与 ut 路由；R17

**问题**：
1. **预算触顶会杀掉业务 patch**。per_patch 模式下，若 Optimization 持续返回 opt_patch_ready，第 3 次环边通过会被拦截并强制 fail_safe。业务 patch 本身已经通过编译、UT、Benchmark，却因为"还想再优化"导致整个 Run 失败。按 D2，Agent 不感知环计数，无法在上限之前自行收手。
2. **收益没有确定性判定者**。流水线里唯一的 A/B 是"被测 vs 不含本次 patch 的基线"，而优化轮的收益应该是"优化后 vs 优化前（同一业务 patch）"。这个对比的参照镜像没有定义，执行判定的节点也不存在。bench_gate 只看相对基线的回归是否 ≤5%，于是一个让性能变差、但仍在 5% 以内的优化 patch 会被发布。§7A.0"优化是否有效（由 A/B 统计判定）"在流程里没有落点。
3. **没有撤销路径**。优化 patch 导致 UT 失败时，路由 `ut_fix_patch_ready → compile_rpm` 会让 UT Agent 去"修复"代码来迁就优化，而不是撤掉优化 patch，同时消耗 ut_fix_loop 预算。Benchmark 显示劣化时，同样没有"回退优化 patch"的出口。

**依据**：§7A.4："Benchmark 重测并证明收益；优化环有轮数上限"；§4.5："第 N+1 次通过请求即拦截并强制路由 fail_safe"；§7.8："基线镜像：同一 snapshot、同一构建配置、不含本次 patch 的镜像"；示例一 `opt_loop … max_rounds: 2` 与 `{ from: ut, on: ut_fix_patch_ready, to: compile_rpm }`

**候选改动**（不触碰冻结的 §4.5）：
```diff
 §7A.4 产物与回流 后追加
+- **优化判定（定案）**：优化轮的参照 = 优化 patch 父 series 对应的镜像与 MeasurementRecord（"优化前"，镜像保留期覆盖 Run 存续）。当前 series 顶端为 Optimization 产出的段时，Benchmark 对"优化前 vs 优化后"按 BenchPolicy（§7A.3）追加第二组交叉 A/B，结果写入 BenchReport：`opt_gain_pct`（gateable，定点）与 `opt_verdict ∈ {gain, neutral, loss, inconclusive}`。Optimization 只能依据 opt_verdict 处置：gain → 可继续或返回 no_further_gain；neutral / loss / inconclusive → 必须产出**撤销 patch**（series 树回到优化前，tree_digest 等价），并把该候选在 OptimizationReport 中标记为 rejected、不再重试。
+- **轮次自限**：节点配置 `max_opt_rounds`，校验器强制 `2 × max_opt_rounds ≤ 对应 loop.max_rounds`（每个候选至多一次提交 + 一次撤销）；Agent 以 series lineage 中自身产出段的计数（确定性，无需感知环计数）在达到上限时返回 no_further_gain——环预算只作防御兜底，正常路径不会触顶。
+- **UT 归因**：UT 失败且失败 series 顶端为优化段时，UT Agent 不做 AI 修复，只产出确定性撤销 patch（PatchAttribution.motivation = "revert_optimization"），沿既有 ut_fix_patch_ready 路由回流。
```
**副作用**：每个优化轮多一组 A/B（板子时长翻倍）；示例一 opt_loop 若保持 max_rounds 2，则 max_opt_rounds 只能是 1；撤销 patch 也会推进 series，旧报告失效，必须完整重验（这本身是正确的）。
**配套测试/夹具**：§11.3 追加：优化后劣化 → 撤销 patch → tree_digest 等价于优化前；max_opt_rounds 自限后预算不触顶；优化致 UT 失败 → 撤销而非修复；opt_verdict golden；01 BenchReport/OptimizationReport fixture 增加字段。

---

### H2-11 ｜ MAJOR ｜ "判定与 AI 分离"没有在各 Agent 流程里结构性落实

**位置**：§7A.0 表 Benchmark 行与原则 1、2；§7.7 静止判定；§7A.3 生成型套件"人工确认一次"；§2.1 开发者入口；§6.5

**问题**：
1. **板子稳定性被列为 AI 职责**。§7A.0 写"测试前与用例间判断板子是否稳定"由 AI 完成。这直接决定测量是否有效、进而决定 gate 的输入，与原则 1 以及 §7.7 的确定性静止判定都冲突。
2. **生成型套件的"人工确认"走什么通道没有定义**。如果走 Skill/MCP，而 bearer token 由 Coding Agent 持有，那么 AI 可以确认自己生成的基准，D17"杜绝测错东西"就失效了。
3. **gateable 字段没有"可复算"约束**。regression_pct 与 spec_out_count 由 Agent 代码产出，Agent 内部完全可以用 LLM 生成这些值，原则 1 没有任何结构性保证。
4. **"试点先行"没有落点**。哪些 AI 能力处于试点、哪些已达标，没有配置项与 Ledger 记录；"未达标只作参考"在流程中如何体现（例如不得进入 gateable 字段、不得生成进入 series 的 patch）也未定义。Compiler/UT 的修复 patch 生成是否属于试点能力，同样未说明。

**依据**：§7A.0 Benchmark 行："测试前与用例间判断板子是否稳定"；原则 1："是否达标、是否回归、是否通过一律由 SPEC、统计规则或确定性结果判定"；§7.7："关键指标（CPU、内存等）在小范围内平稳浮动方可放行"；§7A.3："Agent 生成脚本 → 有效性检查 → **人工确认一次**"

**候选改动**：
```diff
 §7A.0 表 Benchmark 行
-| Benchmark | 按用例描述生成测试脚本；测试前与用例间判断板子是否稳定；分析性能异常，… | SPEC 达标与否、是否回归（由 SPEC 与统计规则判定） |
+| Benchmark | 按用例描述生成测试脚本；分析性能异常，… | SPEC 达标与否、是否回归（由 SPEC 与统计规则判定）；**板子静止判定（§7.7 确定性规则）** |
 §7A.0 使用原则 追加
+5. **结构性保证**——gateable 字段一律由框架统计库从 MeasurementRecord 确定性计算（conformance 以复算比对强制，不一致 → sys.invalid_result）；AI 输出只能进入报告的 `ai_draft` 子结构，不得进入 gateable 字段，也不得进入路由依据。
+6. **试点登记**——每项 AI 能力在中心配置登记 `pilot | adopted`；pilot 能力的输出只进 ai_draft、不产生进入 series 的 patch；登记状态进入 execution manifest。
 §7A.3 开发者描述用例
-…→ **人工确认一次** → 以版本号入套件注册表，…
+…→ **人工确认一次**（经 Review CLI 同类本机通道：peer credential + 套件审核人名单；MCP/HTTP bearer 通道不提供确认操作；确认人与所确认脚本的 digest 记入 Ledger）→ 以版本号入套件注册表，…
```
**副作用**：如果 Compiler/UT 的修复能力被登记为 pilot，首期就不能自动修复，需要在总部对齐时决定首期哪些能力直接 adopted。
**配套测试/夹具**：conformance"gateable 复算一致"（篡改 regression_pct → sys.invalid_result）；"MCP 调用套件确认 → 不存在该工具 / 拒绝"；"静止判定 trace 中无 LLM 调用"；pilot 能力产 patch → 拒绝。

---

### H2-12 ｜ MAJOR ｜ ClineSR CLI：关闭工具执行这一安全前提被放在 [待补充]；缺 OS 级隔离与端点/版本固化

**位置**：§7.1 ClineSRCliProvider；§8.1；§5.2；R5；D12；§7A.1 LogAnalyzer 接入；01 ExecutionManifest（同步项 S-04）

**问题**：
1. **能否可靠关闭一个 agentic CLI 的工具执行，是架构可行性问题，不是环境事实**。EvidencePacket 中含有构建日志与源码，这些是攻击者可控的内容，间接提示注入可以诱导 CLI 执行命令或修改文件。CLI 子进程"纳入 worker 进程组"，即以 worker 同一 OS 用户运行，能访问 worktree，若 FD 被继承还能访问 per-task socketpair，从而绕过 side_effect/trace 直接改代码或伪造数据面命令。
2. **模型端点由 CLI 自己的配置文件决定**。如果这份配置不由框架下发并纳入 provider_policy_digest，D7/D12 的端点校验形同虚设。
3. **R5 声称"CLI 版本纳入 execution manifest"**，但 D12 的列举与 01 ExecutionManifest 都没有这个字段。
4. **LogAnalyzer 若自带 LLM 调用路径**，就绕过了 LLM 接入层（数据边界、记账、Fake 替身）。
5. **字节估算 token 需要保守取上界**，否则 llm_budget 的 fail-closed 会被低估突破。

**依据**：§7.1："关闭 CLI 自身的文件修改与命令执行能力…"；"CLI 的调用参数（非交互模式、关闭工具的方式、输出格式选项）`[待补充]`"；"每次调用为独立子进程，纳入 worker 进程组"；R5："CLI 版本纳入 execution manifest（D12）"；§7A.1："实现为 LogAnalyzer 核心的 Python 封装，运行于内网 LLM"

**候选改动**：
```diff
 §7.1 ClineSRCliProvider
-  - **只作补全引擎使用**：…**关闭 CLI 自身的文件修改与命令执行能力**，工作目录指向空的临时目录——…
+  - **只作补全引擎使用**：…关闭 CLI 自身的文件修改与命令执行能力（CLI 参数层），**并以 OS 层强制作为不依赖 CLI 行为的兜底（定案）**：CLI 以专用 OS 用户运行；spawn 时 close_fds（不继承 per-task socketpair 及任何 FD）；提示目录只读挂载、唯一可写为空临时目录；无 worktree/Ledger/artifact 目录访问权；网络出口仅允许已登记的 LLM 端点（按 UID 的出口规则）；调用结束校验临时目录外无文件变更。E0 预检若确认 CLI 无法在上述约束下以补全模式工作，第一阶段 LLM 能力不得上线（不提供放宽降级）。
+  - **配置固化**：CLI 的端点、模型、输出格式由框架按调用生成临时配置（不读用户目录配置），其 endpoint_identity 进 provider_policy_digest；CLI 版本进 execution manifest（`llm_cli_version`）。
+  - **记账**：CLI 不返回 token 数时按字节估算，取**上界**系数并标注为估算值。
 §7A.1 LogAnalyzer 接入形态
-…实现为 LogAnalyzer 核心的 Python 封装，运行于内网 LLM（开发期 FakeLLMProvider）；…
+…实现为 LogAnalyzer 核心的 Python 封装，**LLM 调用一律经注入的框架 LLM client**（不得持有自有端点/凭据），开发期为 FakeLLMProvider；…
```
**副作用**：deploy/ 需要新增 CLI 专用用户与出口规则；按 UID 的出口规则要求宿主具备 netfilter owner 匹配能力（属 E0 项）。
**配套测试/夹具**：提示注入用例（EvidencePacket 内嵌"执行命令 / 写文件 / 连接 socket"指令 → 无文件变更、无数据面命令、无外连）；FD 不继承断言；端点改向 → D12 失配；LogAnalyzer 调用经 Fake provider 记账断言。

---

### H2-13 ｜ MINOR ｜ release_requires 语义不完整：只看存在不看结论、允许空列表、审批人看不到、删除表遗漏

**位置**：§4.2.6 规则①；§2.4 删除影响表；§8.2 审批对象

**问题**：
1. 规则只检查报告"存在且针对当前 series"，不检查结论：一份 UTReport.passed=false 也能满足。在示例的路由下这种情况不可达，但规则本身没有声明"结论由路由保证"。
2. 允许 `release_requires: []`，于是"必须声明"实际上变成了可选。
3. "未测发布"只留痕于 pipeline_digest；ReleaseManifest 不包含 release_requires 及其所满足的报告引用，审批人在 CLI 中看不到"本次未经 UT"。
4. §2.4 "Compiler（镜像模式）"一行没有提示同步调整 release_requires（image/ut/bench）。
5. 任何声明 `produces bench_report` 的替身插件都能满足规则，属 R6 范畴，应当由 attestation 绑定 report_type 的 conformance 来防范。

**依据**：§4.2.6①："运行时检查：…核对清单内每类报告均存在且针对当前 series"；"清单中删去某类报告即显式接受不含该验证的发布，配置留痕于 pipeline_digest"

**候选改动**：
```diff
 §4.2.6 ①
-…清单中删去某类报告即显式接受不含该验证的发布，配置留痕于 pipeline_digest。
+…清单中删去某类报告即显式接受不含该验证的发布：空清单须同时声明 `accept_unverified_release: true`；release_requires 与满足它的报告引用（report_type, task_id, digest）写入 ReleaseManifest（`release_evidence`），审批 CLI 首屏呈现"本次未执行的验证类别"。报告结论由路由保证（非通过 status 不得有通往 human_review 的路由），校验器对 release_requires 中报告的生产节点，检查其非通过类 status 不可达 human_review。V-02 attestation 绑定 Agent 所 produces 的 report_type 的 conformance 套件。
 §2.4 表 Compiler（镜像模式）行
-| Compiler（镜像模式） | 只出 RPM、不出镜像 | 同时去掉依赖镜像的 UT/Benchmark/Optimization |
+| Compiler（镜像模式） | 只出 RPM、不出镜像 | 同时去掉依赖镜像的 UT/Benchmark/Optimization；含发布时从 release_requires 移除 image/ut/bench_report |
```
**副作用**：ReleaseManifest 的 schema 与规范化算法发生变化，需要在 01 同步时一并处理。
**配套测试/夹具**：空清单且无确认标志 → 拒；ReleaseManifest digest 包含 evidence；"ut_failed → human_review"路由 → 拒；CLI 呈现快照测试。

### H2-14 ｜ MINOR ｜ `input: none` 规则只约束 entry；触发主体未定；空计划经 broker 核销

**位置**：§4.2.6 规则②；§4.2.1 示例二说明；§2.1；§6.5

**问题**：
1. 规则只约束 entry 节点。entry 之后、首次 series 推进之前可达的"需要 patch"节点（例如 static review）不受检查。
2. "按周期触发"由谁执行没有定义，Run 的创建主体也没有定义；而 cancel 限创建者，PatchAttribution 的 ExternalProducer.principal 也取决于创建主体。
3. 空计划仍要走 hitl 加 broker 核销、迁入 publishing、再返回 released：既浪费人工审批，又把"released"的含义放宽到"什么也没发布"。

**依据**：§4.2.6②："其 entry 节点不得是需要 patch 才能工作的节点"；§4.2.1："ci_plan 产出空发布计划，审批后 Run 以 succeeded 关闭且不发布任何对象"

**候选改动**：
```diff
 §4.2.6 ②
-…`input: none` 的流水线以空 series 起步、创建后直接排队，其 entry 节点不得是需要 patch 才能工作的节点（以 Agent 注册的输入声明判定）。
+…`input: none` 的流水线以空 series 起步、创建后直接排队；自 entry 沿"不产 patch 的 outcome"（注册时为每个 status 声明 `advances_series: bool`）可达的全部节点，input_requirement 均不得为 patch。触发主体：MCP `create_run` 调用方，或框架内置调度器（principal = `sys.scheduler`，仅可创建 input: none 的流水线）。
 §4.2.1 示例二说明
-…review_final 汇总"无可发布内容"，ci_plan 产出空发布计划，审批后 Run 以 succeeded 关闭且不发布任何对象（空计划的处理细则 `[01]`）。
+…review_final 返回 `nothing_to_release`，路由至 terminal 汇总节点（success_on: [nothing_to_release]），Run 以 succeeded 关闭，不进入审批与 broker；ci_plan 不得产出空计划（校验器与运行时均拒绝）。
```
**副作用**：示例二的 YAML 需增加一个 terminal 节点及一条路由；空计划的 [01] 细则因此删除。
**配套测试/夹具**：input: none 图中 entry 之后紧接需 patch 节点 → 拒；空 series 走 terminal 成功关闭、不产生授权记录；调度器 principal 的创建权限测试。

### H2-15 ｜ MINOR ｜ Profile 库：陈旧度度量未定、自引用陈旧、来源隔离、工具链范围

**位置**：§7.8 Profile 库；§7A.4 AutoFDO/BOLT；§7A.3 profile 采集

**问题**：
1. "代码版本变化超过阈值"的度量方式与阈值都未定义。
2. 如果"代码版本"包含 profile 文件本身，那么提交 profile 的 patch 会立即让该 profile 变成陈旧。
3. per_patch 模式采集自含未批准 patch 的镜像，进入共享库后可能被其他 Run 使用（与 H2-04 相关）。
4. 密级未标注：profile 含符号与行号，应为 internal_code。
5. llvm-profgen 产出的是 LLVM sample profile，只有 clang 构建的包可以直接使用；Tizen 平台包的编译器分布决定了 AutoFDO 首期覆盖面。BOLT 需要 `--emit-relocs` 这类链接选项变更。两者都是范围决策，不是环境事实。

**依据**：§7.8："代码版本变化超过阈值即标记陈旧"；§7A.4："基于团队增强版 llvm-profgen"

**候选改动**：
```diff
 §7.8 Profile 库
-…代码版本变化超过阈值即标记陈旧（AutoFDO 对代码漂移敏感），…
+…陈旧度 = 采集时与当前代码间函数级 CFG checksum 匹配率（排除 profile 数据文件路径），低于阈值（缺省 90%，按包配置）即标记陈旧；键中的代码版本取 tree_digest 级、仅同 tree 或经批准 series 的 profile 可晋升正式区（H2-04）；profile 密级 internal_code。
 §7A.4 范围（新增）
+- **首期范围（定案）**：AutoFDO 仅覆盖 clang 构建的包（GCC 包首期不纳入，后续以 profile 格式转换链另行评估）；BOLT 仅覆盖可加 `--emit-relocs` 的可执行文件，链接选项变更作为优化 patch 的一部分提交。
```
**配套测试/夹具**：陈旧度 golden；profile 文件变更不触发陈旧；被 reject 的 Run 的 profile 不可见；GCC 包被优化方法拒绝。

### H2-16 ｜ MINOR ｜ MCP 入口：request_id 位置与幂等域、Origin 校验、工具清单与调用方主体

**位置**：§6.5；§4.3.1 cancel 入口；01 §0.2 request_id 行（同步项 S-06）

**问题**：
1. request_id 应当是工具参数，而不是 JSON-RPC id（后者是会话内消息 id，重连后会复用）。幂等域应按"操作"划分，而不是按"endpoint"：同一操作经 MCP 与 HTTP 以同一 request_id 重试，必须得到同一结果（"两者不存在语义差异"）。01 当前按 `(bearer principal, endpoint)` 分域，会导致重复执行。
2. Streamable HTTP 需要校验 Origin、只在受控网段监听，以防 DNS rebinding；Mcp-Session-Id 不得作为认证因子。
3. 开发者操作（套件提交、优化专项触发）没有列入工具清单。
4. "cancel 限创建者"需要按调用方区分主体，即每个调用方独立 token。

**候选改动**：
```diff
 §6.5 认证与信任边界
-- 认证与信任边界：MCP 连接与 HTTP 端点使用同一种静态 bearer token（配置下发调用方）；每次工具调用含 request_id 支持幂等重试；…
+- 认证与信任边界：MCP 连接与 HTTP 端点使用同一种静态 bearer token，**每调用方一枚**（principal 由 token 映射）；request_id 为**工具参数**（非 JSON-RPC id），幂等域 = (principal, 操作名)，跨 MCP/HTTP 传输共享；MCP 服务校验 Origin 头、仅监听受控网段；Mcp-Session-Id 不参与认证。开发者操作工具：`submit_bench_suite`（仅提交，确认见 §7A.3）、`create_run` 用于 input: none 流水线。
```
**配套测试/夹具**：CF-SKILL-01 扩为"跨传输同 request_id → 同结果"；非法 Origin 被拒；他 principal 调用 cancel → 403。

### H2-17 ｜ MINOR ｜ 附录 B 第 7 组未覆盖全部新增的 [01] 待落项

**位置**：§16 附录 B 第 7 组

**问题**：第 7 组缺以下各项：
- 注册信息扩展（status_set/produces 按 mode、input_requirement、capabilities_required、advances_series）；
- MCP 工具与 HTTP 的映射及跨传输幂等域（第 2 组提到"MCP 工具"，但 01 v0.11 只有 HTTP，属于新增，应放入第 7 组）；
- ExternalWait / 资源租约的 Ledger 记录与命令（D11 机制）；
- §7A.0 原则 4 的"AI 证据与采纳记录"schema；
- BenchPolicy、SPEC、MeasurementRecord schema；
- LogAnalyzer Diagnosis schema；
- 套件确认命令与权限；
- ExecutionManifest 扩展（CLI 版本，套件/SPEC/策略 digest，AI 能力登记）；
- worker 数据面命令扩展（H2-04）；
- 特权构建隔离的部署契约（H2-01）；
- "01 上游切换为 v2.0 并更新 A2 追溯矩阵"。

（正文"18 处 [01]"的计数经核对无误。）

**候选改动**：
```diff
 §16 第 7 组末尾追加
+；**注册信息扩展**（status_set/produces 按 mode、input_requirement、advances_series、capabilities_required）；**MCP 工具映射与跨传输幂等域**；**ExternalWait 与资源租约记录、wake outbox、相应状态机命令（E-02）**；**worker 数据面扩展命令（E-03）**；**AI 证据与采纳记录 schema、AI 能力登记**；**BenchPolicy / SPEC / MeasurementRecord schema**；**LogAnalyzer Diagnosis schema**；**生成型套件确认命令与权限**；**ExecutionManifest 扩展字段**；**特权构建隔离的部署契约**；01 上游切换至 v2.0 并更新 A2 追溯矩阵。
```
**配套测试/夹具**：01 同步完成时，contracts 包 CI 的"A0 名 ↔ 正文模型"检查覆盖以上新类型。

### H2-18 ｜ MINOR ｜ §13 分期：contract v1.0 在 Benchmark/Optimization 被真实消费之前定稿

**位置**：§13 P5、P7；G6；D10

**问题**：
1. contract v1.0 在 P5 宣布，但 BenchReport（gate 的输入）、OptimizationReport、套件描述、Profile 引用要到 P7 才首次被真实 Agent 消费，这与 D10"未被真实消费的 contract 不定稿"相悖；v1.0 之后再改这些 schema 就只能 major 升版。
2. GitGerritSource（SourceProvider）没有被分配到任何期。
3. 特权构建隔离（H2-01）与 Gateway 会话注入（H2-06）没有进入任何 gate。

**候选改动**：
```diff
 §13
-| P5 | **Compiler Agent**（…）+ 六类 fixture + 兼容矩阵 | contract v1.0（G6） |
+| P5 | **Compiler Agent**（…）+ 六类 fixture + 兼容矩阵 | contract v1.0（G6，**核心 + Compiler/UT/Review/CI 面**；Benchmark/Optimization/Profile/套件 schema 标注 provisional） |
-| P7 | **Benchmark Agent**（…）+ **Optimization Agent**（…） | 真实板子上 A/B 测量可复现；…
+| P7 | **Benchmark Agent**（…）+ **Optimization Agent**（…） | contract v1.1（provisional 面经真实消费后定稿）；真实板子上 A/B 测量可复现；…
 P3 交付追加：GitGerritSource；P3 gate 追加：特权构建隔离 E2E；P6 gate 追加：Gateway 会话注入与错账号拒绝
```
**配套测试/夹具**：兼容矩阵区分 core 与 provisional 面。

### H2-19 ｜ MINOR ｜ D13 未列举新增的可执行内容来源

**位置**：D13；§8.1；§7A.3 开发者脚本与结果解析规则、生成脚本

**问题**：开发者基准脚本、LLM 生成的脚本、结果解析规则是新的可执行内容来源。它们在宿主 worker 中执行（解析规则）或在板上执行，但信任等级、准入方式（谁可以提交、版本 digest 如何 pin）、执行位置都没有在 D13 中列举。

**候选改动**：
```diff
 D13 结论列
-内网单机单操作员；patch 来源限于经认证的 Skill 调用方；构建脚本视为半可信（见 §8.1）
+内网单机单操作员；patch 来源限于经认证的 Skill 调用方；构建脚本、**Benchmark 开发者脚本与生成脚本**视为半可信（见 §8.1）；脚本只在板上执行，宿主侧的**结果解析规则限声明式**（正则/JSON path，不执行代码）；套件以 digest pin 入注册表
```
**配套测试/夹具**：解析规则中出现代码形态 → 注册时拒绝；套件 digest 变化 → 版本必须递增。

### H2-20 ｜ NIT ｜ 编号与排序

**位置**：§1.2、§14、§15、§17

**问题**：G11 排在 G10 之前；R22 排在 R21 之前；A17 排在 A16 之前，且 A17（"v2.0 补充"）实际上是 A16 的子集；附录 A15 位于附录 B（§16）之后的 §17。

**候选改动**：按编号重排，并把 A17 并入 A16 作为子条。无副作用，无需测试。

---

## 第二部分：01_Contract_Spec v0.11

### 恢复臂四条时间线走查摘要

| 时间线 | 路径 | 结论 |
|--------|------|------|
| T1 正常 | consume granted → 执行 → release_outcome | 主干闭合；但"ACK 丢失"的现实形态（断连重连）不闭合 → C11-02 |
| T2 broker 在发布前崩溃 | 新实例 → consume ④ resumed → reconcile not_happened → 原子许可 → proceed → 执行 → outcome | 若 DispatchReceipt 已 completed，则无重派触发 → C11-05；静默定义弱于 HLD → C11-01；与 D12 漂移叠加时对账被阻断 → C11-03 |
| T3 broker 在发布后崩溃 | 新实例 → resumed → reconcile happened → ledger 级 released | 可达性同 T2（C11-05）；映射本身闭合 |
| T4 不可判定 | resumed → reconcile indeterminate → C-11 | C-11 自动 probe 与再次 reconcile 的处置相反 → C11-06 |

DispatchReceipt 的四个崩溃点（intent 前、intent 后、broker 受理后 ACK 前、ACK 后落账前）就其自身而言闭合，但与 §5.1 的另一套模型矛盾（C11-04），且缺"completed 之后 broker 崩溃"这第五点（C11-05）。

### C11-01 ｜ MAJOR ｜ 恢复臂"旧执行静默"弱于 HLD；release_outcome / reconcile_report 不绑定执行权持有者

**位置**：01 §2.2(a)④、§2.2(c)；§2.1 C-09 / C-10 / C-10a / C-11；§5.1 broker socket

**问题**：01 把静默定义为"reap/lease 过期"，是析取。只要 lease 过期而进程仍然存活（挂起、调度停顿、socket 半断），条件就满足。于是新 epoch 进入恢复臂，对账得到 not_happened，经 proceed 后由新 broker 发布。旧 broker 恢复后，可能继续它此前已获 granted 的发布：git push 同一 commit 有远端幂等兜底，gerrit review push 却会产生新的 patchset。并且旧 broker 在旧连接上发出的 release_outcome / release_reconcile_report 不受任何 epoch 约束，C-10/C-10a 都会接受，于是两个执行者都能关闭 Run。HLD 的合取定义（lease 回收 + pgid reap）正是为了排除这种情形。C-11 的"broker 静默确认"在 01 中没有独立定义，沿用的是同一个弱定义。

**依据**：
- HLD §8.3："① 状态 guard 前置 **broker 侧静默**——broker task 进程组已终止（lease 回收 + pgid reap 确认），本地不存在在途发布执行"
- 01 §2.2(a)④："∧ 旧执行已静默**（编排确认旧 broker 进程组已 reap/lease 过期）"
- 01 C-10："release_outcome（broker）| publishing | §2.2b 固定映射"（无 epoch/持有者条件）

**候选改动**：
```diff
 §2.2(a)④ guard
-…∧ **请求携带的 broker_epoch > 授权记录的 granted_epoch ∧ 旧执行已静默**（编排确认旧 broker 进程组已 reap/lease 过期）→ 响应 resumed(reconcile_required)，授权记录 epoch 更新（…）
+…∧ **请求携带的 broker_epoch > 授权记录的 granted_epoch ∧ 旧执行已静默**——**静默 = 旧 holder 的 broker task lease 已回收 ∧ 其登记 pgid 已 reap 确认（合取；单独 lease 过期不构成静默；HLD §8.3① 字面）**，本定义同时作为 §2.2(c) 与 C-11 "broker 静默确认"的唯一定义 → 响应 resumed(reconcile_required)，授权记录 granted_epoch 更新为本连接 epoch（**granted_epoch 即执行权持有者 epoch**）（…）
 §2.1
-| C-10a | release_reconcile_report（broker，仅恢复臂后） | publishing | …
+| C-10a | release_reconcile_report（broker，仅恢复臂后） | publishing **∧ 连接 epoch == 授权 granted_epoch** | …
-| C-10 | release_outcome（broker） | publishing | §2.2b 固定映射 | closed(...) |
+| C-10 | release_outcome（broker） | publishing **∧ 连接 epoch == 授权 granted_epoch** | §2.2b 固定映射；guard 不符 → E-CP-FORBIDDEN + 审计，Run 不变 | closed(...) |
```
**副作用**：broker 正常路径中若因断连重连而换 epoch，release_outcome 会被拒；因此必须与 C11-02 配套（epoch 按进程实例分配，同实例重连保持 epoch）。
**配套测试/夹具**：CF-AUTH-09b（旧 broker lease 过期但 pgid 未 reap → 新 epoch consume → rejected(stale_epoch)）；CF-AUTH-13（非持有者连接发送 release_outcome / reconcile_report → E-CP-FORBIDDEN，Run 不变）；CF-SM-07 增"lease 过期未 reap → confirm_not_released 拒"。

### C11-02 ｜ MAJOR ｜ epoch 写进载荷 × 连接绑定 × receipt 先于 guard：现实 ACK 丢失路径走不通；epoch 计数持久化与 hello 幂等未定

**位置**：01 §5.1 AuthorizationConsumeRequest / BrokerHelloRequest / BrokerHelloResult；§1.2 投影规则；§2.2(a) 处理序（R10-07）；§5.1 通用 RPC envelope 的幂等域与保留期；CF-AUTH-11

**问题**：
1. **现实中的 ACK 丢失走不通**。Unix socket 上的"ACK 丢失"实际上只会因为断连发生（编排重启、socket 重建）。重连必须重新 hello，按"建连后分配、绑定于连接上下文"得到新 epoch E'。此时 broker 有三种重投方式，都拿不到 granted：
   - 载荷仍带旧 E：E ≠ 连接 E'，返回 E-CP-FORBIDDEN；
   - 载荷改带 E'：投影 digest 变化（consume 的投影 = 全载荷，含 broker_epoch），返回 E-CP-IDEM-MISMATCH；
   - 换新 request_id：不同 request_id，且"旧执行"就是它自己、不可能静默，返回 rejected(stale_epoch) 或 already_consumed。

   结果是一个存活的 broker 无法得知自己是否已经获得核销，Run 滞留 publishing，只能走 R13 人工。CF-AUTH-11 的期望只在"同连接重投"这一不现实的形态下成立。反过来，如果实现者为了通过 CF-AUTH-11，把 receipt 查找放在 epoch 校验之前并忽略 epoch，那么一个**新进程**只要复用同一 request_id（例如确定性的 request_id = f(token_id)），就能经 receipt 取回 granted，跳过恢复臂与对账，打开双发布窗口。
2. **epoch 计数器的持久化未定义**。若计数器只在编排内存中，编排重启后从 1 开始分配，`broker_epoch > granted_epoch` 永远为假，恢复臂永久不可达。
3. **"每次启动"与"建连后分配"二义**：同一 broker 进程重连时是否换 epoch，没有规定。
4. **broker_hello 自身的幂等语义未定义**。它落在 (broker, command) 域，且"无语义豁免"，同一 request_id 重放返回首个 epoch，新进程若复用 request_id 会拿到旧 epoch。保留期"Run 存续 + 7 天"对一个与 Run 无关的命令也没有定义。

**依据**：
- 01 §5.1："`broker_epoch: int   # 必须等于本连接经 broker_hello 分配的 epoch（不等 → E-CP-FORBIDDEN）`"
- 01 §5.1："`BrokerHelloResult … 编排在 broker socket 建连（peer credential 认证）后按每次启动单调分配，范围 1..2^53，绑定于连接上下文`"
- 01 §1.2："每条命令的幂等摘要经投影…（缺省 = 全载荷…）"
- 01 §2.2(a)："先查同幂等域 receipt——同 request_id 同载荷（含首次 granted 的 ACK 丢失重投）→ 返回首响应（仍为 granted）"
- CF-AUTH-11："首次 granted 的 ACK 丢失 | 同 request_id 重投 | 仍返回 granted"

**候选改动**：
```diff
 §5.1
-class BrokerHelloRequest(BaseModel): broker_pid: int; broker_pgid: int
-class BrokerHelloResult(BaseModel): broker_epoch: int    # 编排在 broker socket 建连（peer credential 认证）后按每次启动单调分配，范围 1..2^53，绑定于连接上下文（R10-04/Z10-01）
+class BrokerHelloRequest(BaseModel): broker_pid: int; broker_pgid: int; broker_start_time: datetime   # (pid, pgid, start_time) = broker 进程实例身份（防 pid 复用）
+class BrokerHelloResult(BaseModel): broker_epoch: int
+# epoch 按 **broker 进程实例** 分配：计数器持久化于 Ledger（跨编排重启单调），范围 1..2^53；同一实例重连 hello → 返回同一 epoch、绑定新连接并关闭该实例旧连接；新实例 → 计数器 +1。
+# broker_hello 幂等域 = (broker 实例身份, command)，保留期 = 实例存续；新实例即新域。
 §1.2 投影规则
-…缺省 = 全载荷；task_complete 投影 = HandoffResult 去 metrics 字段…
+…缺省 = 全载荷；task_complete 投影 = HandoffResult 去 metrics 字段；**authorization_consume 投影 = 载荷去 broker_epoch**（epoch 由连接上下文权威给出、单独校验）…
 §2.2(a) 处理序
-**处理序（R10-07）**：先查同幂等域 receipt——…；再执行状态机 guard——…
+**处理序（R10-07 修订）**：① 连接 epoch == 载荷 broker_epoch（不符 E-CP-FORBIDDEN）；② 查 receipt，**broker 入向幂等域 = (broker 实例身份, command)**——同实例同 request_id 同投影载荷（含断连重连后的 ACK 丢失重投）→ 返回首响应；**不同实例不经他实例 receipt**；③ 状态机 guard——…
 §5.1 通用 RPC envelope 幂等域
-…broker 入向 = (broker, command)…
+…broker 入向 = (broker 实例身份, command)…
```
**副作用**：CF-AUTH-11 变得在现实中可达（同实例重连沿用同一 epoch，receipt 返回 granted）；新实例复用 request_id 会落入不同幂等域，走正常 guard 进入恢复臂。epoch 只在新实例时递增，恢复臂语义不变。
**配套测试/夹具**：CF-AUTH-11 改写为"编排重启/重连后，同一实例以同 request_id 重投 → 仍 granted"；CF-AUTH-11b（新实例复用同 request_id → 不命中 receipt → 恢复臂 resumed）；CF-AUTH-14（编排重启后 epoch 计数器大于重启前最大值）；CF-AUTH-15（同实例重连得同 epoch，新实例 +1）；CF-LED 点位增加计数器提交。

### C11-03 ｜ MAJOR ｜ publishing 期 D12 漂移阻断恢复臂对账，与 HLD §8.3 冲突；D12 存在两种 wire 表示

**位置**：01 §2.2(a)③④；§2.6 复核时点；§5.1 CommandError 注释、ReconcileDeny；CF-AUTH-04b、CF-AUTH-05b；C-10a

**问题**：最常见的恢复组合，是框架升级（framework_version 或 agent digest 变化）之后重启全部服务，这会同时触发"broker 重启"与"D12 漂移"。新 broker 的恢复臂 consume 在 publishing 下命中 D12 复核点，按 CF-AUTH-04b 返回 E-CP-D12-MISMATCH，而不是 resumed。broker 没有收到 resumed，就无权调用 release_reconcile_report（"仅恢复臂后"），对账通道因此关闭：远端是否已发布永远不会被查询，Run 滞留 publishing 直到人工裁决。HLD 要求的"必须先对账"被 01 阻断了。另外，publishing 下的 D12 漂移有两种 wire 表示（E-CP-D12-MISMATCH 与 ReconcileDeny(d12_drift)），与 §5.1 所说的"唯一 wire 表示"自相矛盾。

**依据**：
- HLD §8.3："**publishing 是 administrative finalize 的状态级例外**——即使 D12 漂移或进程重启，也必须先与 broker 对账或 probe 远端结果"
- 01 §2.2(a)③："publishing 期检出漂移 → 不适用 C-14，登记 pending(admin_finalize) 并走 HLD §8.3 对账流程"
- CF-AUTH-04b："D12 漂移检出，**Run=publishing** | 任一复核点 | E-CP-D12-MISMATCH；…"
- 01 §5.1："E-CP-D12-MISMATCH 为全部 D12 复核点（含 authorization_consume）的唯一 wire 表示"
- ReconcileDeny.reason 含 "d12_drift"

**候选改动**：
```diff
 §2.2(a)③
-…publishing 期检出漂移 → 不适用 C-14，登记 pending(admin_finalize) 并走 HLD §8.3 对账流程。
+…publishing 期检出漂移 → 不适用 C-14，登记 pending(admin_finalize)（恰一次）；**恢复臂 consume 照常按 ④ 返回 resumed(reconcile_required)——漂移不阻断对账（HLD §8.3"即使 D12 漂移…也必须先对账"）**；对账结果：happened → released 映射（broker outcome 优先，pending 记入 RunSummary）；not_happened → 原子许可必 deny(d12_drift) → release_failed → admin_finalize 最优先消费；indeterminate → C-11。
 §5.1 CommandError 注释
-    # E-CP-D12-MISMATCH 为全部 D12 复核点（含 authorization_consume）的唯一 wire 表示
+    # D12 漂移的 wire 表示按 Run 状态二分：running 下一律 E-CP-D12-MISMATCH（触发 C-14）；publishing 下不以错误返回——consume 恢复臂返回 resumed、原子许可返回 deny(d12_drift)，漂移事实由 pending(admin_finalize) 承载
 CF-AUTH-04b
-| CF-AUTH-04b | D12 漂移检出，**Run=publishing** | 任一复核点 | E-CP-D12-MISMATCH；授权与 Run 不关闭；pending(admin_finalize) 恰一次登记并进入 §8.3 对账（R10-06） |
+| CF-AUTH-04b | D12 漂移检出，**Run=publishing** | 恢复臂 consume / 原子许可 / 其余复核点 | consume → resumed（非错误）；许可 → deny(d12_drift)；其余复核点不关闭 Run；pending(admin_finalize) 恰一次；三对账结果分别闭合（happened → succeeded 且 RunSummary 含 pending；not_happened → release_failed → admin_finalize FeedbackReport；indeterminate → C-11） |
```
**副作用**：C-09 在 publishing 下不再有 D12 错误臂，CF-SM-01 矩阵相应单元格改变。
**配套测试/夹具**：CF-AUTH-04c（升级重启组合：broker 新实例 + framework_version 漂移，Run=publishing，三种对账结果逐一断言）；CF-SM-09 扩展同场景。

### C11-04 ｜ MAJOR ｜ DispatchReceipt 在 §2.5 与 §5.1 各有一套互相矛盾的模型

**位置**：01 §2.5 DispatchReceipt 与出向协议注释；§5.1 通用 RPC envelope"出向命令"句与幂等域列表；CF-IPC-06、CF-IPC-10

**问题**：§5.1 仍是 v0.10 的单事务子记录表述，与 §2.5 有三处矛盾：
- 单事务里写入"首响应"，而首响应在发送之前不可能得到；
- granted_epoch 是 consume 时才产生的，与 dispatch 无关；
- AuthorizationRecord 根本没有子记录字段。

此外两处的幂等域也不一致：§5.1 是 (run_id, task_id, command)，§2.5 的唯一键是 (token_id, request_id)。同一 task 能否并存两个 request_id、同一 request_id 能否跨 token，都无法判定。出向 request_id 的生成规则也没有定义。CF-IPC-06 引用的是 §5.1 模型，CF-IPC-10 引用的是 §2.5 模型，实现者无法确定哪一个是规范。

**依据**：
- 01 §2.5："`class DispatchReceipt … # Ledger 表，唯一键 (token_id, request_id)` … `# 出向协议：事务①（发送前）写 intent…；事务②写 completed + 首响应`"
- 01 §5.1："**出向命令（release_dispatch）**：编排…在出向事务内将 (request_id, payload 投影 digest, 首响应, granted_epoch) 绑定写入授权记录的 dispatch receipt 子记录"
- 01 §5.1："编排→broker 出向 = (run_id, task_id, command)"

**候选改动**：
```diff
 §5.1 通用 RPC envelope
-…、**编排→broker 出向 = (run_id, task_id, command)**（全方向覆盖）；…
+…、**编排→broker 出向 = (token_id, command)，持久化于 §2.5 DispatchReceipt**（全方向覆盖）；…
-…**出向命令（release_dispatch）**：编排（单写者、调用方）在出向事务内将 (request_id, payload 投影 digest, 首响应, granted_epoch) 绑定写入授权记录的 dispatch receipt 子记录；broker 进程内以 request_id 去重；跨 broker 重启的重放落到授权记录状态机（granted/resumed/rejected）且编排以 receipt 校验 payload digest（同 id 异 manifest → E-CP-IDEM-MISMATCH）。
+…**出向命令（release_dispatch）**：唯一模型为 §2.5 DispatchReceipt 两事务协议（request_id = ulid，于事务①生成）；同一 token 任一时刻至多一个 state=intent 的 receipt；broker 进程内以 request_id 去重；跨 broker 实例的重放落到授权记录状态机（granted/resumed/rejected）。
 CF-IPC-06 期望列
-…出向经授权记录 dispatch receipt + 状态机去重（同 id 异 manifest 拒）…
+…出向经 §2.5 DispatchReceipt + 状态机去重（同 id 异 digest 拒；同 token 第二个 intent 拒）…
```
**副作用**：仅为文字统一，无语义扩张；"同一 token 至多一个 intent"是新增约束，用于防止并发重派。
**配套测试/夹具**：CF-IPC-10 增"同 token 存在未完成 intent 时第二个 intent 被拒"；CF-IPC-06 出向行改为引用 DispatchReceipt。

### C11-05 ｜ MAJOR ｜ broker 在 dispatch 已 ACK（receipt=completed）之后崩溃：没有重派触发，恢复臂不可达

**位置**：01 §2.5 出向协议"恢复"注释；§2.2(a)④；CF-AUTH-05；HLD §8.3

**问题**：broker 最常见的崩溃时点是"已 ACK dispatch、已 granted、发布执行中"。此时 DispatchReceipt 为 completed，而恢复规则只处理"intent 无 completed"，所以不会重派。新 broker 实例不知道 token_id 和 task_id，无从发起恢复臂 consume。01 既没有"broker task lease 丢失或新实例握手后，由编排重派"的规则，也没有定义 broker 可以读 Ledger 自行发现待恢复的授权。CF-AUTH-05 的前置条件在这条时间线上不可达：恢复臂只在 receipt 恰好停在 intent 的少数组合下可达，其余情形一律滞留 publishing，走 R13 人工。

**依据**：
- 01 §2.5："恢复：intent 无 completed → 以同 request_id 重派"
- CF-AUTH-05 前置："broker 重启（broker_hello 取更高 epoch、旧进程组已 reap），Run=publishing、授权 consumed_by=本 task"
- HLD §8.3："即使…进程重启，也必须先与 broker 对账或 probe 远端结果"

**候选改动**：
```diff
 §2.5 出向协议注释 追加
+# **持有者更替重派（定案）**：编排在以下任一事件后——holder 的 broker task lease 丢失，或受理新 broker 实例的 broker_hello——对全部 Run=publishing ∧ 授权 consumed_by_task_id≠None ∧ holder 实例 ≠ 当前实例的授权，先确认旧 holder 静默（§2.2a④ 合取定义），再写新 DispatchReceipt(intent, 新 request_id, recovery=true) 并重派 release_dispatch；新实例据此 consume → 恢复臂 resumed → 对账。旧 holder 未静默 → 不重派、告警并计入 R13 时长，静默确认后由周期任务重试。
 class DispatchReceipt
+    recovery: bool = False
```
**副作用**：hello 事务需要扫描 publishing 授权（数量极小）；静默确认可能需要等待 reap，因此要配一个周期重试任务。
**配套测试/夹具**：CF-AUTH-05 前置改为"receipt=completed、broker 在发布中崩溃"；CF-AUTH-05c（旧 holder 未静默 → 不重派）；CF-IPC-10 增第五个崩溃点"completed 之后 broker 崩溃"。

### C11-06 ｜ MINOR ｜ release_outcome 的发送条件与恢复子状态未建模

**位置**：01 §5.1 ReleaseOutcomeRequest 注释与 broker socket 句；§2.2(a)④ deny 句；§2.1 C-10 / C-10a；§2.2(c)

**问题**：
1. "仅在实际执行后发送"与 deny 路径"随即发 release_outcome(release_failed, proceed_denied)"在文字上冲突。
2. reason 是自由字符串，而 CF-AUTH-05b 断言的是 proceed_denied，应当枚举。
3. resumed 之后、对账与 proceed 之前，C-10 只要求 Run=publishing，因此 broker 若跳过对账直接上报 outcome 也会被接受；"必须先远端对账"没有任何契约强制。
4. indeterminate 记录之后，broker 若再次 reconcile 得到 not_happened，会经 proceed 去发布；而 C-11 自动 probe 得到同一结论时，规则是"等同 release_failed"。同一个观测，两种终局。

**依据**：§5.1："`# 两值固定（HLD §4.2.5），仅在实际执行后发送`"；"`release_outcome`（两值，仅执行后）"；§2.2(a)："不通过则 `deny(reason)`，broker 不得发布、随即发 release_outcome(release_failed, reason=proceed_denied)"；§2.2(c)："自动周期 probe 得出确定结论 → 等同对应 broker outcome"

**候选改动**：
```diff
 §2.5 AuthorizationRecord
+    recovery_state: Literal["none","reconcile_required","proceed_granted","denied","indeterminate"] = "none"
 §2.1
-| C-10 | release_outcome（broker） | publishing | …
+| C-10 | release_outcome（broker） | publishing ∧ recovery_state ∈ {none, proceed_granted, denied} | …
-| C-10a | release_reconcile_report（broker，仅恢复臂后） | publishing | …
+| C-10a | release_reconcile_report（broker，仅恢复臂后） | publishing ∧ recovery_state == reconcile_required（indeterminate 之后不再受理，只走 C-11） | …
 §5.1
-class ReleaseOutcomeRequest(BaseModel): task_id: str; outcome: Literal["released","release_failed"]; reason: str = ""; remote_refs: list[str] = []   # 两值固定（HLD §4.2.5），仅在实际执行后发送
+class ReleaseOutcomeRequest(BaseModel): task_id: str; outcome: Literal["released","release_failed"]; reason: Literal["", "remote_conflict", "adapter_error", "authorization_expired", "proceed_denied"] = ""; remote_refs: list[str] = []   # 两值固定；在实际执行后发送，或在 deny 后以 reason=proceed_denied 发送（未执行）
```
**配套测试/夹具**：CF-AUTH-16（resumed 后直接发 release_outcome → 拒）；CF-AUTH-17（indeterminate 后再次 reconcile → 拒；C-11 自动 probe 得 not_happened → release_failed 映射）。

### C11-07 ｜ MINOR ｜ FramingError 与 ResponseError 的边界：处理序、receipt 持久化、空关联 id 的处置

**位置**：01 §5.1 FramingError 定义；通用 RPC envelope 段"未知命令 → E-CP-VALIDATION"；"受理即持久化 receipt"；CF-IPC-09

**问题**：
1. 通用段仍写"未知命令 → E-CP-VALIDATION"，没有指明走哪一臂；ResponseError.command 是封闭枚举，承载不了未知命令。
2. 处理序只定义了"先 receipt 后 guard"，没有覆盖 framing 与 schema 校验相对 receipt 的先后。若 ResponseError(E-CP-VALIDATION) 也落 receipt，那么修正载荷后以同一 request_id 重试会得到 IDEM-MISMATCH；FramingError 不落 receipt 也应当明示。
3. request_id=None 的 FramingError 在多请求并发在途时无法关联，客户端如何处置未定义。
4. control-plane 层的 request_id 没有格式约束（§0.2 只约束了 Skill 层）。

**候选改动**：
```diff
 §5.1 通用 RPC envelope
-…payload 按 command 解析，未知命令 → E-CP-VALIDATION）。
+…payload 按 command 解析）。**处理序（全命令统一）**：① envelope 解析——失败（未知 command / 缺或非法 request_id（control-plane 格式 = ulid）/ envelope 非法）→ FramingError，**不落 receipt、不占幂等域**；② payload schema——失败 → ResponseError(E-CP-VALIDATION)，**不落 receipt**；③ 连接级校验（task 归属、broker epoch）；④ receipt 查找；⑤ 状态机 guard 与执行——其结果（含业务拒绝与 ⑤ 阶段的 ResponseError）作为首响应落 receipt。客户端收到 request_id=None 的 FramingError → 视为连接级协议错误，关闭连接，对在途请求按 ACK 丢失重投。
```
**配套测试/夹具**：CF-IPC-09 增三条：载荷非法后以同 request_id 提交合法载荷 → 正常受理（不得 IDEM-MISMATCH）；FramingError 不产生 receipt；null request_id → 客户端断开重连后重投。

### C11-08 ｜ MINOR ｜ A0 类型索引未逐名收录 v0.11 新增类型

**位置**：01 §7 A0；§5.1"contracts 包 CI 以自动检查断言 A0 名 ↔ 正文模型一一解析"

**问题**：v0.11 新增的 DispatchReceipt、BrokerHelloRequest/Result、ReleaseReconcileReport、ReconcileProceed/Deny/Recorded、ReleaseReconcileResponse、FramingError、CommandResponse 都没有在 A0 中逐名出现，只能靠"§5 命令载荷族"笼统覆盖。既有的 CandidateRecord、ProbeReceipt、ProbeOutcome 也不在 A0 中。按 §5.1 自己声明的 CI 检查规则，这会红灯。

**候选改动**：
```diff
 A0
-…§3 ActivationRecord；§4 EffectRecord/EffectResult/ProbeResult/EffectType；§5 命令载荷族/…
+…§2 追加 DispatchReceipt；§3 ActivationRecord/CandidateRecord；§4 EffectRecord/EffectResult/ProbeResult/ProbeOutcome/ProbeReceipt/EffectType；§5 命令载荷族（逐名：…/BrokerHelloRequest/BrokerHelloResult/ReleaseReconcileReport/ReconcileProceed/ReconcileDeny/ReconcileRecorded/ReleaseReconcileResponse/FramingError/CommandResponse）/…
```
**配套测试/夹具**：contracts CI 的 A0 ↔ 正文一一解析检查。

### C11-09 ｜ NIT ｜ 原子许可条件在 §2.2(a) 与模型注释中措辞不一致

**位置**：§2.2(a)④ "execution manifest 匹配 ∧ broker epoch 现行 ∧ 无**阻断性** pending admin_finalize"；§5.1 ReconcileProceed 注释 "manifest 匹配 ∧ epoch 现行 ∧ 无 pending admin_finalize"

**问题**："阻断性"这个限定词没有定义，模型注释里也没有；"manifest"指 execution manifest 还是 release manifest，存在二义。按 C11-01 的修法，"epoch 现行"应写成"连接 epoch == granted_epoch"。

**候选改动**：两处统一为"execution manifest 匹配 ∧ 连接 epoch == 授权 granted_epoch ∧ 无 pending(admin_finalize) ∧ 授权仍 consumed_by 本 task"。无副作用，无需新增测试。

---

## 同步项（HLD v2.0 核心修订 ↔ 01 v0.11 现有条文）

> 按评审说明：v2.0 的新增范围尚未写入 01（附录 B 第 7 组），不算 01 的缺陷。下列各项是 v2.0 **对核心的修订**或**对核心的隐含依赖**与 01 现有条文直接冲突的情形，单列，不计入第二部分结论。

| 编号 | 严重程度 | HLD v2.0 | 01 v0.11 冲突条文 | 同步方案 |
|------|---------|----------|------------------|---------|
| S-01 | MAJOR | D11 补充、§4.3.1 长等待、§4.5 计入外部等待 | C-07 guard"仅剩 gate 等待"；C-13 guard"queued ∨ running"（paused 下预算不触顶）；§3.4"排除 paused 与 publishing 时段"；状态集只有 paused(gate) | 以 H2-02 的 E-02 为前提：C-07 改为"仅剩等待项（gate ∪ external）"；新增 C-08d wake_resolve（wake outbox 消费）；C-13 guard 加入 paused(external)；§3.4 按等待类别扣除；SysOutcome 增 sys.await_external 并排除于 V-05/V-06。测试：CF-SM-01/04/10 扩展 |
| S-02 | MAJOR | §8.5 Gateway 经编排转发；§5.1.1 新能力句柄 | §5.1"worker 数据面 socket（per-task socketpair；命令封闭枚举）"共 9 条 | 以 H2-04 的 E-03 为前提扩充 CommandName、注册表与幂等域；CF-IPC-01/02 扩到新命令 |
| S-03 | MINOR | §4.2.6 release_requires 支配检查；§5.1.1 注册的 produces / input_requirement | V-13b/V-15 的支配未定义 join 语义；AgentRegistration 无 input_requirement、无按 mode 声明；CF-FIX-00 只有单一 compiler 注册集 | 按 H2-03 定义 AND-join 支配（V-13b 作为 E-01 的澄清登记）；AgentRegistration 改为 by_mode；CF-DSL-FLAG 改为四份原文 |
| S-04 | MINOR | R5"CLI 版本纳入 execution manifest"；H2-09/H2-11 的套件、SPEC、策略、AI 登记 | §2.6 ExecutionManifest 无对应字段 | 增加 `llm_cli_version`、`bench_suites_digest`、`spec_digest`、`bench_policy_digest`、`ai_capability_registry_digest`；CF-SM-12 增变体 |
| S-05 | MINOR | §5.2 新效应类别（镜像构建、远程构建、profile 采集） | §4.3 注册面类别硬性要求只有 build.*/board.*/publish.* | 增加 image.*（可 probe，按 idem_key 查索引）、remote_build.*（可 probe，远端标记 = idem_key 指纹 + version；ProbeOutcome 增 deferred，见 H2-06）、profile.*（replay_safe）；CF-EF-02 扩轴 |
| S-06 | MINOR | §6.5 Skill → MCP 为主 | §2.7 仅 HTTP；§0.2 request_id 幂等域"(bearer principal, endpoint)" | 增加 MCP 工具 ↔ 操作映射表；幂等域改为 (principal, 操作名)，跨传输共享（H2-16）；CF-SKILL-01 扩为跨传输 |
| S-07 | MINOR | D20"series 模型、tree_digest 与审批发布语义对两者统一，框架核心不改" | §3.5 tree_digest 以 git tree OID 定义；§5.2 fencing 依赖 Change-Id/commit | 要么 HLD 把 D20 改为"P8 需对 tree_digest 与 fencing 作 VCS 中立化（届时走勘误）"，要么 01 现在就把 §3.5 抽象为 `vcs_tree_id`（git 实现保持不变）。建议前者，避免首期过度设计 |
| S-08 | NIT | v2.0 已成为对齐基线 | 01 头部"上游依据：…HLD_v1.0_draft_frozen.md"；A2 追溯矩阵 | 同步时切换上游并更新 A2 |

---

## 附：本轮核对过、未发现问题的事项

- **v1.0 → v2.0 冻结核心的逐节 diff**：编排（§4.1–§4.2.5）、Ledger（§7.5）、效应幂等（§5.2 主体）、审批与发布（§8.2–§8.3）、IPC（§8.5 原有各条）均逐字未变；变动集中在 D7 与 D11、§4.2.6 的追加规则、§4.3.1 与 §4.5 的外部等待、§5.1.1 与 §5.2 的新增句柄与效应类别、§8.5 末条。其中被实质改动的冻结语义只有 H2-01 与 H2-02 两处。
- **勘误 E-01**：§17 原文保留，§4.2.6 新规则与其不冲突，仍然有效。
- **01 v0.11 第十轮的其余修订**：CommandName 计数为 19，与注册表 19 行一致；ConsumeRejected 枚举与 CF-AUTH-09 一致；R10-06 的 running/publishing 分型（CF-AUTH-04/04b、CF-SM-12/12b）在 running 一侧闭合（publishing 一侧见 C11-03）；R10-08 头部轮数已改为十轮。
