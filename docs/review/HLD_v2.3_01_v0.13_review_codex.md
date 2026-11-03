# HLD v2.3 / 01 v0.13 复审 — Codex

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.3 | **NO-GO** | 0 | 3 | 3 | 0 |
| 第二部分：01 v0.13 | **NO-GO** | 0 | 1 | 2 | 0 |
| 新增同步项（不计入第二部分） | 无；既有项已登记 B-7，不重复报 | 0 | 0 | 0 | 0 |

## 负责人七项裁决的独立评估

| # | 裁决 | 判断 | 理由及代价 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时显式化 | **成立** | 同 activation、同 series 的 AND 汇合，配合环退役、超时只去 fail_safe，可以支持规则①③的汇合必经；不必退回串行。审批/核销复核和发布后事实优先的分界也成立。旧测试文字须清理（H23-05），不推翻这项取舍。 |
| ② | “最新”在 Run 启动时解析固定，Quickbuild 锁定基线 | **有条件成立** | 将默认解析结果固定一次成立；必须区分源码基线、应用 series 后的源码与构建环境。当前锁定条款未闭合被测源码身份（H23-01），发布的配置摘要也不足以证明实际输入相同（H23-02）。代价是证据不足时不能提供 A/B 结论和跨 Run 缓存，必要时使用本地后端。 |
| ③ | Profile 严格匹配 v1，预留小改动复用 v2 | **成立** | 本版将“不显著”改为预定 ε、采样计划和方法版本下的非劣证明；缺省关闭，限通过验证的模块类别/方法/编译器版本，伪探针与其他兼容条件不足则回落 v1。这里认可准入机制，并非断言某个 LLVM 版本已经通过 P7。代价是额外评估、重采和较保守的开启范围。 |
| ④ | 目标范围与模块登记表 | **成立** | 首次 submit_patch 初始化、后续并集增长、最低套件集合和固定注册表快照，解决了原先的时间点与绕过问题。允许跨模块修复、随后扩大验证，比一律拒绝候选更符合自动修复目标。代价是撤销后也不缩减范围，可能触发父版本此前没跑过的验证；这个组合出口须补 H23-03。范围外回归仍是明确的 R25 残余。 |
| ⑤ | 用测试与多版本对比检验 AI，取代按能力登记试点 | **有条件成立** | 验证资产触及记录、人工逐条确认、框架计算判定、采纳率与准确率分离，方向成立；测试证据必须确实来自所声称的源码及可比输入（H23-01/02），报告生成顺序也须自洽（H23-06）。人工可以批准合理的测试修改，不能把不可比数据批准成已证明的优化收益。代价是保留失败/撤销版本及独立核验成本。 |
| ⑥ | 预检 Quickbuild 显式 base 与实际版本读回 | **有条件成立** | 预检本身必要，只读调查也有价值；但“未证实能指定”不能改写为“实测证明不能指定”，字段存在也不等于语义与权限已验证（H23-04）。保留 P6 真实提交验收，明确未验证能力不可启用，不要求本轮再访问服务。 |
| ⑦ | 超时后重试成功可发布，每条重试记录须审批人确认 | **成立** | 同一逻辑 task 的后续成功不等于原超时被抹掉。保留所有重试记录、首屏逐条呈现、决定绑定确认集合、核销再次复核，能够支持这个产品取舍；不需要坚持“曾经超时永久禁止发布”。确认只豁免重试历史，不替代当前 series 的必需报告、优化闭环与阈值。代价是更多审批信息及拒绝后重新处理的成本。 |

## 范围与证据

日期：2026-11-03。评审前已执行 `git pull --rebase`，返回 Already up to date；取证 HEAD 为 `0449ee57f64c892b3a0adf3d035c87d8ff6613db`。本轮按要求收窄：核对上一轮两份处置表及三家原始意见，审阅 A20 全部改动和所指定组合/恢复场景；没有将未变旧设计重新扩成全文审计。未查看本轮其他评审方意见，未访问或探测 Quickbuild，未修改被审文档。

| 文件 | SHA-256 |
|---|---|
| `docs/00_Framework_HLD_v2.3.md` | `d66d7cdf33d6f7b1328de78f4f391607b2127f71f1df36bb6d8d8309f6649bf2` |
| `docs/01_Contract_Spec_v0.13.md` | `f3ad51b4b49266e2c8964b8478b9d9ceabbae9f762e46272d9d3c066dd28c85a` |
| `docs/00_Framework_HLD_v1.0_draft_frozen.md` | `0094d2f4ce52a11e9a89962e34355d942475a19a585d48c9194f2d47dbb08a12` |
| `docs/research/quickbuild_business_logic.md` | `33104bb3c1f70d5f196b83c7f02b5b664db5c0da512a56cf49738164498763c3` |

验证方法：文本差异与协议走查；临时只读 Python 脚本解析四份 YAML，计算普通/AND 必经集合、核对优化环预算、演算净变更证明的失效与恢复；扫描 01 的 class 定义与 A0、核对新增命令/响应/模型。不是执行尚待实现的产品校验器或 conformance 套件；没有声称真实 Quickbuild、板子、CLI、supervisor 已验证通过。`[待补充]` 环境事实本身不计缺陷。

## A. 上一轮处置逐项核验

“落实”指原问题已有对应规则，不代表相关实现已经通过测试。下列 M/N/Y 编号均来自用户指定的本轮背景处置表，已按其“来源”列回查三家原始意见。

### HLD：13 个 MAJOR 合并处置

| 处置 | 正文落实与取舍判断 |
|---|---|
| M1 | §4.2.6③改为从 opt_patch_ready 目标出发的 G' 上计算汇合必经，环容量同步，四份示例结构可通过。正文是“删去以 fail_safe 为目标的边”，并非处置表描述的“去掉从 Optimization 出发不经 compile 的边”；采用正文，不能先删掉违规边再证明合规。运行时未决计划 guard 与同 series 报告约束有实质落实。 |
| M2 | 静态仅检查 input:none；advances 重置证明；运行时所有 needs-patch 分派复核净变更；空 submit_patch 拒绝；RPM optional。完整落实，采用更严格的数据流方案成立。 |
| M3 | §4.3.5、§8.2/8.3有分类、两次复核、逐条确认 retried、发布后事实优先、结果 succeeded_with_gaps。采纳负责人第⑦项成立。旧 §11.3 仍有冲突断言，H23-05。 |
| M4 | §4.3.4新增 gateway_session 四阶段、提交不确定先 probe、deferred 不耗次数、结束或不启动 worker、其他在途效应 guard。提交前没有 build_ref 也有等待出口，落实。 |
| M5 | 正文取消后保持 cancel_pending 占额，只有远端终态/确证未提交才归还；比处置表“或保留期过期”更严格，采用正文是正确取舍。过期/日志被删不证明任务停止，不能照处置表放宽。差异归 H23-05。 |
| M6 | 单次 pin、读回不符使镜像无效、BUILD_NOTES、及时归档、自有配额已落实；30/10/7 天在正文正确。但被测源码与 build.conf 证明仍有 H23-01/02；能力证据等级 H23-04；处置表的“10 个”不应沿用。 |
| M7 | 劣化统一正号、区间上界 gate、absolute/relative SPEC、空集合不完整、BCa 退化缺字段均落实。样本不足不再因“不显著”静默放行，取舍成立。 |
| M8 | Ledger OptimizationPlan、整链归属、确定性撤销、按计划计轮、修复环容量均落实；撤销后重验证未通过的分支仍不闭合，H23-03。 |
| M9 | submit_patch 初始化、范围只增不减、未登记包拒绝、最低套件、完整注册表快照入 D12均落实。采用增长而非拒绝跨模块修复的理由成立；须处理增长后撤销的组合。 |
| M10 | 伪探针前提入闭包，预先固定 ε/样本计划、95% 区间下界高于 −ε 的非劣准入已落实；策略 v2仍缺省关闭。不要求在环境材料里提前保证具体编译器能力。 |
| M11 | protected_paths 与确定性 diff 检查、verification_asset_change、审批逐条确认已落实。允许合理测试修复而非全面禁止合理；证明边界仍是测得事实及人为确认。 |
| M12 | D22 两种部署形态都要求不可变基底、一次性可写层、共享缓存只读、基线/被测边界隔离、产物复验，原持久化污染缺口已在规范层补齐。 |
| M13 | §7.1由特权 launcher 启动 CLI，cgroup.kill 跨 UID 清理，pidfd 监视 worker、恢复时对账；E0 与部署 gate 有对应项，原 UID 信号权限缺口落实。 |

### HLD：10 个 MINOR/NIT 合并处置

| 处置 | 核验 |
|---|---|
| N1 | E-02已列 paused、计时、到期、租约优先队列、superseded 等偏离；running 下 wake不降级状态；冻结本地 worker 模型未放宽。 |
| N2 | ci_plan 完成事务生成报告并绑定 digest已写入；与 Review final 的前置“随附”尚冲突，H23-06。 |
| N3 | launcher 写临时镜像、active-upload lease、claimed 效应引用与服务端标记推导、主动释放按板侧 fencing 分型均落实。 |
| N4 | sys.baseline_build 属框架内部 Run，独立预算/队列，取消订阅与全部订阅取消分开，失败广播已落实。 |
| N5 | 示例三/四已有原文；A4/CF-FIX 待上游切换的登记正确。 |
| N6 | B-7 规则①③共用汇合必经，E-01/V-15普通支配；新增状态/模型/部署项齐全，不再重报既有同步项。 |
| N7 | P2消息清单、P4范围/验证资产/对比报告/deploy、P7 Benchmark列及策略 v2评估已落实。P4用 fixture验证机制，P6/P7真实消费者验证，不能以 P4通过替代后续门槛。 |
| N8 | exclude_boards 持久化与资源等待，使单板配额下多板归因可达；没有空闲替代板时按等待预算失败合理。 |
| N9 | 采纳率和有真值样本的准确率/误报率分开，展示覆盖率和 unknown，落实。 |
| N10 | 风险编号已顺序排列；小范围旧措辞并入 H23-05，不另列纯排版项。 |

### 01：7 个合并处置

| 处置 | 正文落实与取舍判断 |
|---|---|
| Y1 | §2.5 superseded 与替代事务完整；同 epoch 重送/跨 epoch 替代互斥；已 completed 保留、迟到 ACK仅审计。解决了旧 intent永久阻塞，合并方案成立。 |
| Y2 | 内核核实实例身份、实例租约、进程组静默合取、task失联升级为整实例退役均落文。接受不另造 task epoch 的简化及整实例回收成本；但发布中间结果之后的失联未覆盖，C13-01；pid复用夹具前置不充分，C13-03。 |
| Y3 | indeterminate 跨 epoch锁存；C-09恢复臂拒绝；mode=probe_only、C-11a、负向结果静默 guard、部分目标只能 unknown 已落实。新增自动只探测通道比纯人工出口更可用，执行权限制成立。与 Y2组合的活性见 C13-01。 |
| Y4 | §5.1处理序③有 hello例外，历史 receipt前重新绑定连接并检查退役实例；CF-AUTH-21覆盖，落实。 |
| Y5 | broker/approval/admin可重连与普通 worker socketpair不可重连已区分；新增文字把 reconciliation也套进普通 task终止，仍需 C13-02。 |
| Y6 | SnapshotManifest及新增四个模型已入 A0；class扫描无缺项，新增命令名/载荷/响应/索引对应一致。 |
| Y7 | C-10/C-10a及 CF-AUTH排序已改；dev2反映本轮破坏性修改，落实。 |

## B. 第一部分问题

### H23-01 — MAJOR：Quickbuild 锁定规则只指向 snapshot，未闭合当前 series 的远端源码身份

**位置**：HLD v2.3 §7.6.1 Quickbuild“可锁定输入”“读回校验”，§7.6.2/7.6.4；对应 M6、裁决②⑤。

**依据**：§7.6.1要求逐包版本“**一律取自本 Run snapshot manifest 中该仓的 commit**”，并要求“读回的全量包版本必须与提交时锁定的逐包版本一致”。同节接口却为 `build_image(snapshot, series, image_profile)`；§7.6.2规定 tree_digest 是“各仓应用后 tree hash 的规范组合”；§7.6.4仅给出 `to_backend_input(series)` 抽象。

**问题**：设 snapshot 包版本为 C0，当前 S1是 C0上未发布的修复/优化。逐包填 C0并成功读回 C0，按新规则即可通过镜像输入校验，却没有规定远端在哪里应用 S1及如何证明应用后的 tree。若适配器改填派生提交 C1，又与“一律取自 snapshot”及读回基准冲突。A/B条款排除 patch涉及包的版本差异，说明两侧理应可能不同，但前一条没有这条合法路径。`to_backend_input` 的名称不能替代输入身份、暂存权限和读回证据契约；实测也没有验证未发布 patch 的传输能力。这不是表单控件坐标的待补充问题。

**候选改动**（片段，均为提议，不修改正文）：

```diff
@@ §7.6.1 / §7.6.4
- 每个包的 Git 版本……一律取自本 Run snapshot manifest 中该仓的 commit
+ snapshot manifest 固定源码基线；每次构建另外生成 ExpectedSourceManifest，
+ 绑定 snapshot_id、series_id、逐包 base_commit 与应用完整 series 后的 expected_tree。
+ 基线构建使用空 series；被测构建使用当前 series。未改包取 base_commit，
+ 改动包必须通过已验证的不可变补丁包/构建暂存输入供远端构建；不得只提交 base_commit。
+ 此输入通道与正式发布目标隔离，凭据仍只在 Gateway，按构建效应协议提交、探测与回收。
- 读回的全量包版本必须与提交时锁定的逐包版本一致
+ 读回须同时证明基线包身份和 series 应用后的实际源码 tree 与 ExpectedSourceManifest 一致。
+ 只有基线 commit 回显、没有 series 应用证据，不得产生 succeeded 的当前-series ImageReport。
+ P6须验证非空修复、优化和撤销三种输入；未验证/后端不支持时禁用该后端的非空 series 构建，
+ 明确报 backend_source_input_unsupported，可由配置选择 LocalGbsBackend；不得自行发布补丁来满足输入。
```

**副作用**：增加构建输入证明、临时产物生命周期与 P6验收；不会授权审批前向业务仓发布。若远端实际不支持这条能力，Quickbuild不能承担该种被测镜像构建，而不是用旧源码测量代替。

**测试/夹具**：FakeQuickbuild 分别只回显 C0、实际应用 S1、实际应用错误 S2；前者不可冒充 S1成功，后两者按 tree匹配分别通过/拒绝；基线空 series与撤销等价 tree仍保留不同 series身份；暂存 ACK丢失/恢复不得重复提交；非空 series能力未验证时加载或提交有明确拒绝。

### H23-02 — MAJOR：发布目录的 build.conf 摘要被当成实际构建输入等价证明

**位置**：HLD v2.3 §7.6.1“不可由提交锁定”“A/B 可比性”、§7.8基线缓存；对应 M6、裁决②⑤。

**依据**：§7.6.1明确说“‘实际消费的 build.conf 摘要’Quickbuild 未归档，**以发布摘要代替**”，随后规定 base编号、`build.conf 发布摘要`、脚本版本等“逐项相同”即可生成 A/B比较字段。研究记录 Q3区分日志片段、base发布配置、产物发布配置，并写明实际 worker 的 `./build.conf` 内容/完整摘要未知；Q4未证实完整可复现输入闭包。§7.8又要求“只有 series/tree 不同，否则不得比较”。

**问题**：两个实际生成配置 X/Y可以共享同一 base发布配置摘要 B。当前规则会将 X≠Y、B相同判为可比，并允许跨 Run缓存复用；在报告里标注“代替”并不能恢复推理有效性。配置能力限制可以是 config_tradeoff，**当次可比性缺证**仍必须是 environment_gap，不能变成默认接受的已证明收益。

```diff
@@ §7.6.1
- “实际消费的 build.conf 摘要”……以发布摘要代替并在报告中如实标注
+ actual_build_conf_digest 与 published_build_conf_digest 分开记录；后者只作取证，
+ 不代替前者。actual_build_conf_digest 不可得，且没有经验证的确定性生成链
+ （生成器版本及全部输入均固定并可复核）时，实际配置身份为 unknown。
- ……build.conf 发布摘要……逐项相同……才生成 A/B 比较字段
+ ……实际消费配置身份、实际脚本版本及其他必需闭包分量……逐项有证据且相同，
+ 才生成 A/B 比较字段；任一 unknown 与不等同样令 comparison=unverifiable。
@@ §7.8
+ 未证明实际输入闭包的镜像不得进入可复用基线缓存；发布目录配置仅作为证据附件。
```

**副作用**：按目前只读材料，部分乃至全部已观察的 Quickbuild作业可能只能作绝对测量，直到 P6补出实际输入证据；这比声称已验证收益更保守，但仍保留构建与日志能力。不要求本轮去探测服务。

**测试/夹具**：published digest相等但实际配置不同；published digest相等但 actual未知；实际配置/脚本闭包全等；三例分别不可比、不可比、可比。确认前两例无 gate字段、不可接受优化、不可跨 Run命中缓存，人工确认 gap也不能生成这些字段。

### H23-03 — MAJOR：撤销已应用但重验证失败时，OptimizationPlan 没有可执行的收尾分支

**位置**：HLD v2.3 §7A.4生命周期/撤销/UT归因、§4.2.6③；对应 M8，组合涉及 M9。

**依据**：计划处于 `rejected_reverting` 时“相应 Agent **只产出确定性撤销 patch**”；同时“**同一计划不会被二次撤销**”，“撤销完成且重验证通过后计划迁 `reverted`”；存在未决计划时 `no_further_gain / no_gain_found → sys.invalid_result`。

**问题**：撤销段已经把 tree恢复父版本，但计划仍是 rejected_reverting。若重验证 UT失败，既要求撤销又禁止二次撤销；若 Quickbuild读回不可比，Benchmark无合法比较结果，计划无法满足“重验证通过”，Optimization既不能再次撤销也不能结束。范围只增不减使这个场景更现实：候选或前序修复引入了新模块的测试义务，父版本的旧通过报告不能代替新范围重测。最终等待预算耗尽或让插件任选 sys.error，不是一个已定义的计划出口。

```diff
@@ §7A.4 OptimizationPlan
- state ∈ {pending_validation, accepted, rejected_reverting, reverted}
+ state ∈ {pending_validation, accepted, rejected_reverting,
+          reverted_validating, reverted, failed}
+ 确定性撤销段提交成功的同一事务：rejected_reverting → reverted_validating，
+ 绑定 revert_series_id；只允许这个事务生成一次撤销段。
- 计划处于 rejected_reverting……相应 Agent 只产出确定性撤销 patch
+ rejected_reverting 仅允许执行尚未完成的撤销；reverted_validating 只允许重验证，
+ 不再产候选、修复或第二个撤销。原始验证记录及框架规则判断全部义务满足后，
+ 同事务转 reverted，并据此计算面向审批的报告通过谓词（避免通过谓词与未决状态互相等待）。
+ 重验证确定失败、不可比或重试耗尽 → failed，记录具体缺口，固定进入 fail_safe。
+ 基础设施重试只能在已有 retry/等待/预算内进行；failed 不是允许发布的已结算计划。
@@ §4.2.6③ / §8.2
+ reverted_validating 同样是未决状态；failed 只能走失败终局，不能由人工确认跳过。
```

**副作用**：新增一个撤销已落账但仍在验证的状态及失败状态，细分原来的 rejected_reverting；不回拨 current、不缩减范围。选择安全失败而非撤销后再开放 AI修复，会减少自动挽救机会，但避免继续修改父版本、重新解释优化收益的额外循环。

**测试/夹具**：候选撤销后 UT失败；撤销后 Quickbuild不可比；范围增长后父版本新增套件失败；撤销提交前/后、重验证结果提交前/后 kill。断言恰一个撤销段、明确 failed→fail_safe、无第二个优化计划、不得靠环预算耗尽才停止；成功重验证恰一次进入 reverted。

### H23-04 — MINOR：Quickbuild 的“已证实”“未证实”“待验证”被混写

**位置**：HLD v2.3 §7.6.1可锁定/不可锁定输入、§12 E0；HLD v2.2处置表 M6。

**依据**：正文将增减包写为可锁定输入“③ 增减包——Add / Remove Package List”，将 root base、build.conf、脚本分支写为“不可由提交锁定、只能读回”；§12称只读调查已完成这些结论。研究 Q2/Q3对某些写入控件和脚本能力的结论是未知，Remove字段存在但删除语义/优先级未实测；Q5也只证明不同配置具有不同镜像能力。

**问题**：未证实可指定，不能证明无法指定；只见字段不等于修改有效。本文后置真实提交验收降低了当前风险，故不提升为 MAJOR，但能力声明会影响配置取舍与报告，不能把推断标成实测事实。本条只处理证据等级；源码身份/假可比性的实质后果分别计 H23-01/02。

```diff
@@ §7.6.1 / §12
- 不可由提交锁定、只能读回的输入
+ 本次调查未证实可由提交锁定的输入；当前适配器按 unverified 处理，
+ 不宣称服务永远不支持。读回能力也逐字段登记，不以字段存在推断完整值可得。
- ③ 增减包——Add / Remove Package List
+ ③ Add 已有样本依据；Remove 的语义、冲突优先级与权限尚待 P6验证。
+ 后端能力按具体 configuration/profile 记录 verified / unverified / unsupported。
+ 未验证的能力不得启用；目标配置是否实际产镜像同样是 P6上线条件。
```

**副作用**：需要一张按配置的能力证据表，不阻止验证后升级能力，也不预先发明服务限制。与负责人原意相比保留预检和默认 pin，撤回“全部相关能力已经测明”的措辞。

**测试/夹具**：Remove未验证则拒绝启用；Base无镜像能力与 Unified有镜像能力的 fixture分开；字段存在但无权限/无效的 fixture不能登记 verified。材料不足保持 unverified，不执行在线探测。

### H23-05 — MINOR：新增规范已替换旧规则，但强制测试与处置表仍保留相反要求

**位置**：HLD v2.3 §11.3、§4.2.6①；`HLD_v2.2_review_disposition.md` M5/M6。

**依据**：§11.3旧 v2.2段仍要求“**范围在 Run 内不可变**”，而 §7A.7及同一 §11.3新增段要求范围增长；旧 Quickbuild测试要求同一 Run各次提交携带“同一 base”，新条款仅锁包/Profile，root base读回可漂移；旧超时测试不分阶段要求“Run不得以 succeeded关闭”，新 publishing映射明确保留 succeeded。规则①还保留“汇合必经（仅用于本规则）”，③又明确①③共用。处置表 M5含“或保留期过期”归还配额，M6写“产物保留10个”，均与正文不同。

**问题**：这些是仍有效的强制断言/实施指令，不是仅存档的版本摘要。按字面实现测试会互相冲突，且实施者若照处置表释放配额会重新引入 M5。本轮不把正文已经正确的取消协议再报为架构缺陷。

```diff
@@ §11.3 既有用例段
- 范围在 Run 内不可变
+ 范围只增不减；注册表快照不变，范围增长不构成 D12失配
- 同一 Run 内被测、基线与各轮提交携带同一 base
+ snapshot/Profile基线固定；被测源码按当前series；root环境按实际输入证明比较
- 超时……Run 不得以 succeeded 关闭
+ 未覆盖的发布前超时→fail_safe；成功重试须逐条确认；
+ publishing后按冻结远端事实映射，结果首屏保留全部异常
@@ §4.2.6①
- 汇合必经（仅用于本规则）
+ 汇合必经（仅用于规则①与③）
@@ HLD_v2.2_review_disposition.md M5 / M6
- 远端确认终态（或保留期过期）
+ 远端确认终态或确证从未提交；证据过期不归还配额
- 产物保留10个
+ Artifact公布保留10天；不推定后台准时清理
```

**副作用**：不增加产品机制，只去掉冲突的旧预期；历史 A19摘要可以保留历史语义，不应与有效测试混同。

**测试/夹具**：维护一个当前有效期望版本，覆盖增长/撤销不缩减、发布前/后超时、证据过期仍 cancel_pending。旧 fixture更新而非同时保留两组相反断言。

### H23-06 — MINOR：Review final 要随附的对比报告，直到下游 ci_plan 完成才生成

**位置**：HLD v2.3 §7A.0原则6、§7A.5、§4.2.1示例一/二；对应 N2。

**依据**：新条款为“由编排在 **ci_plan 的 task 完成事务内**……生成”；§7A.5却要求 Review final产出 ReviewReport时，多版本对比报告“由框架统计库生成并**随附**”；示例明确 `review_final → ci_plan → human_review`。

**问题**：Review task完成时还没有下游事务产物；不能让 worker预测 artifact引用，亦不能事后改写已提交的不可变 Report。审批前的正式生成点合理，只需区分最终审查输入与审批附件。

```diff
@@ §7A.5
- 多版本对比报告由框架统计库生成并随附（§7A.0 原则6）
+ Review final读取截至本task的各版本原始报告，不要求引用尚未生成的正式对比报告。
+ 正式对比报告在ci_plan完成事务生成，作为审批证据包的同级附件呈现，
+ 不事后修改ReviewReport；terminal/fail_safe路径沿用各自终局生成点。
```

**副作用**：ReviewReport不直接持有正式对比报告引用；审批仍看到绑定 digest的正式版本。若未来需要 AI解读同一表格，可另定义预览版本，本轮不增加此依赖。

**测试/夹具**：review_final完成时正式报告尚不存在仍可完成；ci_plan完成后正式报告和 manifest证据一致；事务前后崩溃不留下可审批的半份证据；ReviewReport digest保持不变。

## C. 静态规则、净变更与组合场景

### 四份原文示例

| 示例 | 规则① | 规则② | 规则③与冻结检查 | 判定 |
|---|---|---|---|---|
| 一 full_pipeline | join的 AND必经包含 compile_rpm、compile_image、ut、benchmark；必经 human_review | input:patch不做 input:none静态分析，运行时净变更仍查 | G'从 compile_rpm起，终局前必经 image→UT→Benchmark；ci_plan仍普通支配 human_review，benchmark普通支配 bench_gate；修复预算3/2/2≥2，优化预算2≥2 | 可加载 |
| 二 optimize_campaign | image/UT/Benchmark必经审批 | 空入口 image可用；RPM optional；到ci_plan前必经 no_further_gain(asserts_nonempty)，no_gain_found不进入ci_plan | 从opt回流的G'含image→UT→Benchmark后才到审批或report_no_gain；independent首轮无需RPM；三修复环预算3≥3，优化4≥4 | 可加载；运行时撤销失败另见H23-03 |
| 三 compiler_only | 无release，不适用 | input:patch | required image前有普通支配RPM；无优化义务，summary terminal合法 | 可加载 |
| 四 compiler_bench_only | 无release，不适用 | input:patch | image支配benchmark，benchmark普通支配bench_gate；无优化义务，summary terminal合法 | 可加载 |

核对的反例：opt回流改到UT后或直接到审批，缺image/UT必经而拒绝；将Benchmark分支脱离join而保留release_requires，缺汇合必经而拒绝（若仍填wait_for，先因来源集合不等拒绝）；删除生产者不删清单拒绝；空清单未显式确认拒绝；优化存在却删三项报告拒绝；两个超时路由限制均在合法子集规则中。E-01/V-13b及V-15没有改成AND必经。

净变更证明用二值状态 U（未证明）/P（已证明）：初始U；`advances`不论候选、修复或撤销均置U；`asserts_nonempty`置P；none保留；汇合取共同结论。因此 `assert→修复→撤销→needs_patch` 为U而拒绝，`assert→撤销→优化→assert→needs_patch`恢复P。实际空tree却返回assert被运行时拒绝。input:patch也不能因早期非空绕过最终分派复核。Campaign撤销回空后可重新构建/UT/测量，再走no_gain终局；前提是撤销重验证有明确结果，不能跳过H23-03。

### 必做组合：并行 + 超时重试 + 范围增长 + 优化撤销 + Quickbuild不可比

采用示例一的结构，配置一次允许 `sys.timeout` 的节点重试及 Quickbuild后端。为单独走查编排，以下假定 H23-01所需当前series输入证明具备；否则应更早拒绝镜像。scope、报告和清单均为Ledger事实，不允许AI改写。

| 步骤 | 状态/series/计划 | 清单与证据变化 | 合法后继 |
|---|---|---|---|
| 1 | created→awaiting_patch；pin注册表与源码；submit S0，scope={A}；queued→running | incomplete按配置列取舍；retried=[]；无计划 | RPM、镜像 |
| 2 | 初次RPM失败，AI普通修复S0→Sr，触及登记模块B，scope={A,B} | 新范围、原因、构建失败与修复入报告；如触及protected_paths再记V1 verification_asset_change | rpm_fix_loop回流，Sr构建与镜像成功；范围增长不触发D12失配 |
| 3 | image_ready，activation ar派UT∥review_static，包含A/B及always_run；UT attempt1硬超时 | 编排写T1：位置、实际时长/上限、attempt、日志。retry执行期间不是成功证据；静态分支可先到join | 按节点retry attempt2；不是沿sys.timeout边绕过 |
| 4 | 同task attempt2通过，仍Sr/ar | T1归retried，记录最终成功attempt和UTReport；不再有未覆盖timeout项；历史T1保留 | 本轮Benchmark，然后Optimization |
| 5 | Optimization生成P1，Sr→S1(candidate)，scope仍{A,B} | P1=pending_validation；父版本Sr及父镜像pin；Sr报告仅历史；ar退役，待审批项失效 | 回流RPM、镜像、UT∥Review、Benchmark |
| 6 | P1候选S1已UT通过；父Sr与候选S1的收益对比为loss（此前QB证据可比） | P1→rejected_reverting；保留loss测量，不把相对snapshot快当gain | Optimization产一次确定性撤销，S1→S2，tree(S2)=tree(Sr) |
| 7 | S2回流构建和UT∥静态审查；scope仍{A,B}；报告不能复用Sr的旧series身份 | 撤销版本单独列，P1仍待重验证；T1、V1都不删除 | 重新Benchmark |
| 8 | S2镜像与本次基线的QB读回base/配置不等，comparison=unverifiable | 新G1=environment_gap；保留两侧绝对测量，比较字段缺失、不能接受优化/缓存。retried=[T1]，incomplete至少[G1]，另可能[V1及config_tradeoff] | 当前文本在Benchmark→Optimization处遇H23-03：不能通过重验证、不能二次撤销、不能返回结束。不是合法的发布分支 |
| 9（按H23-03补齐后） | P1=failed，固定进入fail_safe→closed(fail_safe) | FeedbackReport及get_result完整呈现T1/G1、范围增长、P1的loss和撤销、全部版本；不产生授权 | 唯一失败出口，无发布 |

在pending计划下Compiler/UT失败应确定性撤销，不能为了凑组合场景偷偷开放AI修复。因此AI跨模块修复在步骤2、优化计划创建前发生，仍完全满足“同一Run同时出现”要求。步骤2使用一次rpm_fix_loop，步骤5/6各使用一次opt_loop，均在示例预算内。若要测试“优化后叠加修复段”的兼容记录，可用明确允许的修复来源另建夹具，但不得违反本版对Compiler/UT的禁修复规则。

**审批首屏应是什么**：本组合实际不能到审批；不可伪造一张可批准的首屏。如果运维只读查看证据，应看到 snapshot/Profile/root base与读回差异，scope从A长到A+B、反向依赖未验证提示，S0/Sr/S1/S2各列结果，P1 loss/撤销但重验证失败，T1每次超时时长/重试次数/最终报告，G1不可比，以及有则V1。不能把Sr的“曾经通过”写成S2已经通过。

**可到达审批的对照分支**：步骤8若获得真实可比输入且重验证通过，P1→reverted，bench_gate通过、join同cohort集齐后才进入Review→CI→HITL。首屏必须逐条展示T1和所有gap/验证资产变化；未勾选任何一条或reviewer拒绝均不发布。全部确认且必需报告通过，审批事务生成授权；核销前新增T2/G2则再次拒绝。核销后新超时仅记pending，实际released仍closed(succeeded)，结果首屏明确已发布及异常。这是第⑦项允许的发布路径。

**结论**：不可比不是可由人工确认覆盖的优化/阈值证据。本组合当前没有已规范化的正常收尾分支（H23-03），修订后唯一出口是fail_safe；不存在“逐条确认G1就能发布”的合法出口。H23-02若错误把代理摘要判为可比，则会产生另一种静默放行风险，必须一并修正。

## D. 第二部分问题

### C13-01 — MAJOR：task失联判据以“是否收到过reconcile”为界，遗漏proceed之后失联及unknown持有者的回收

**位置**：01 v0.13 §2.2a④、§2.2d实例租约与indeterminate通道，CF-AUTH-19/20；对应Y2/Y3。

**依据**：触发retiring的条件是“**单个 release task 超过配置的发布时限仍无 outcome / reconcile 结果**”；confirmed_not_happened通过许可后“`recovery_state := execution_permitted`”，仍需实际发布并发送outcome。C-11a负向映射又要求“**granted_epoch持有者实例静默**”，静默必须租约reclaimed且进程组无人。

**问题**：E2已成功上报confirmed_not_happened并收到proceed，此后发布协程/子进程失联，broker主进程仍正常心跳：已经有reconcile结果，按字面不满足新失联判据；epoch不变，不触发换实例扫描；没有outcome，Run不能关闭。这正是第五条时间线在中间许可之后的变体。另一个相关变体是E2已报indeterminate且一直存活，周期只探测后来确定未发生：负向映射要求E2静默，但已有reconcile结果又排除了该超时触发；文本没有为这个已确定结果安排退役动作。安全拒绝是对的，但不能只靠操作者在协议之外杀服务才能走完已确定的自动出口。

```diff
@@ §2.2d 实例租约 / task失联
- 单个 release task 超过配置的发布时限仍无 outcome / reconcile 结果……retiring
+ 每个非终态release task持久化当前phase与phase_deadline；
+ 等待consume、等待reconcile、等待实际执行outcome分别有期限。
+ granted与ReconcileProceed事务进入等待outcome并持久化其期限；
+ resumed事务进入等待reconcile并持久化其期限。
+ 收到非终局reconcile结果仅切换phase，不能取消整个任务的失联检测。
+ phase到期且仍无该phase的完成事件，即使实例心跳正常也retiring，
+ supervisor清理整个实例，确认静默后换epoch恢复；重启/receipt重放不重置期限。
+ lapsed实例进入同一回收流程，回收完成才标reclaimed；hello不得复活已retiring/reclaimed实例。
@@ indeterminate 锁存 / C-11a
+ unknown保持锁存。若只探测取得confirmed_not_happened但原holder尚live，
+ 记录观测并请求原holder的retiring/回收（不授予执行权）；
+ 静默确认后以新probe_seq及新request_id重新探测，再作负向映射，
+ 不把旧ILLEGAL_STATE receipt改写为成功。无法清理则保持publishing并告警。
```

**副作用**：整实例回收可能影响同一broker的其他Run，它们也沿既有epoch恢复协议对账；这是本版选择实例epoch的既有代价。期限须足够容纳正常发布，不能把超时当未发生。未知远端仍可无限保持publishing并告警，本建议没有强迫unknown终局，也不解除indeterminate锁存。

**测试/夹具**：CF-AUTH-20扩为等待consume/reconcile/outcome三阶段；特别注入proceed提交后ACK前、ACK后执行前、执行中task失联且broker心跳正常；phase定时器提交前后编排重启。另加indeterminate后同实例仍活、只探测后来not_happened，确认先退役/静默/重新probe，再唯一关闭；清理失败只告警不重派执行。回收后历史granted/proceed receipt不可经旧实例重放恢复执行权。

### C13-02 — MINOR：reconciliation的协议错误被误归为普通task的sys.error

**位置**：01 v0.13 §5.1统一处理序末段、§4.3 Reconciliation协议、CF-IPC-09；对应Y5。

**依据**：新文字把“worker与reconciliation worker”的socketpair统一处理为“**本attempt以sys.error结束……下一attempt……对账**”。§4.3却明确probe通道只有heartbeat/probe_report、没有task_complete；启动后无receipt退出应合成 `synthetic_worker_loss`，消耗probe尝试，按能力矩阵继续/耗尽。

**问题**：probe_attempt与业务task attempt不是同一个域。新文字若按普通task执行，会在仍有probe次数时提前失败，或者试图从不可用通道报告sys.error；与原有合成receipt分支产生两个不同处理结果。普通worker不重连的修复成立，需给reconciliation第三种处理。

```diff
@@ §5.1 FramingError(null request_id)
- worker与reconciliation worker……本attempt以sys.error结束……下一attempt对账
+ 普通worker：在途请求失败，本task attempt以sys.error结束，后续按节点retry及启动对账处理。
+ reconciliation worker：终止当前probe进程组；若本组尚无receipt，编排按§4.3
+ 恰一次合成synthetic_worker_loss，消耗本probe_attempt，沿probe重试/耗尽能力矩阵处理；
+ 已提交receipt则复用，不另生成task_complete或提前终结业务task。
```

**副作用**：只细分角色，不改变probe总次数上限及现有能力矩阵。多一次合成回报路径测试。

**测试/夹具**：CF-IPC-09追加reconciliation角色，与CF-EF-10交叉：无receipt/已有receipt、还有次数/已耗尽、replay_safe两值；重复退出通知不得双计数；不重连socketpair、不越权发task_complete。

### C13-03 — MINOR：pid复用夹具把“不足以证明静默”写成了确定静默

**位置**：01 v0.13 §6.5 CF-AUTH-09d、§2.2d静默；01 v0.12处置表Y2。

**依据**：CF-AUTH-09d前置仅“旧实例pid已被无关进程复用、starttime不同”，期望“**判为静默**”。正文的唯一定义为“旧实例租约=reclaimed **∧** 不存在属于其pgid……的存活进程”。

**问题**：原broker leader退出且pid被复用，不排除旧pgid内仍有发布子进程；也没给出reclaimed前置。这个用例会鼓励实现以leader pid身份变化替代全进程组静默，抵消09c与正文合取。正文安全规则正确，所以以夹具缺陷计MINOR，而不将其重复计为执行协议BLOCKER。

```diff
@@ CF-AUTH-09d
- 旧实例pid已被无关进程复用、starttime不同 | 静默判定 | 判为静默
+ 旧实例pid被复用、starttime不同；租约已reclaimed且旧pgid无存活进程
+ | 静默判定 | 判为静默，不把无关复用pid当旧holder
+ CF-AUTH-09e：同样pid复用，但旧pgid仍有发布子进程，或租约尚未reclaimed
+ | 静默判定 / 新epoch恢复 / 负向probe映射 | 不静默、不得授予恢复执行权或负向终局
@@ 01_v0.12_review_disposition.md Y2
- pid被复用但starttime不同即判静默
+ pid复用不再视为旧leader存活；静默仍须满足正文的租约与整个进程组合取
```

**副作用**：可能发现实际回收器只查leader的实现缺陷；不放宽任何安全条件。

**测试/夹具**：leader退出后留子进程、无关pid复用、租约live/reclaimed四组合；只有reclaimed且整个旧组无人通过。

## E. 五条时间线 × 崩溃点

### 出口记号与判定顺序

矩阵分成“送达恢复”与“执行事实映射”两层，避免把ACK状态误当发布事实。每格是一个确定的恢复动作；后续远端观测再按下表唯一分流。**不能同时选择重送和替代，也不能把等待误记为release_failed。**

| 记号 | 唯一动作/出口 |
|---|---|
| D | 尚无intent：同原durable dispatch创建一条intent再发送；不新建逻辑release task。 |
| S | 当前实例未变：重送同request_id；broker实例内去重；③连接检查先于④receipt。 |
| X | 换实例：旧intent→superseded与新intent同事务；先复核当前epoch。未核销走正常consume；已核销且非unknown必须旧holder静默后恢复；unknown只发probe_only。 |
| A | completed仅是送达：同实例不重复派业务执行，依赖已运行task/其失联定时器；换实例仍为X。 |
| G | 未核销有效授权→granted，唯一核销并进入publishing；无效按既有关闭/D12规则处理。 |
| N | 已核销、静默后新epoch→resumed；探测未发生且原子许可通过→proceed，才执行；许可不通过同事务release_failed映射。 |
| H | 已证全部目标发布：ledger级released映射，closed(succeeded)；pending仅审计。 |
| U | indeterminate锁存：保持publishing，只探测/人工裁决；不再发execute、不再resumed许可。 |
| F | 已证未发布且满足静默：按pending固定序做release_failed映射，不要求broker伪造未执行的outcome。 |
| R | 已落账首响应重放；终态及执行许可不再迁移。连接已退役则先③拒绝，不能凭receipt复活。 |
| W | 旧holder未静默或事实仍未知：保持publishing、告警/继续对账；这是明确等待出口，不是成功或失败。 |
| GAP | 当前规范未给唯一有效后继；对应C13-01，须修订，不能声称已闭合。 |

### 5 × 5 送达崩溃矩阵

五条时间线定义：T1正常发布；T2核销后、远端发生前崩溃；T3远端已发生、outcome未落账；T4对账为indeterminate；T5实例存活但单个task失联。前四个发送崩溃点属于共同前缀，恢复后再进入相应事实时间线；T4行的恢复载荷始终强制probe_only。表格同时列同实例/换实例的互斥条件，不以猜测选其一。

| 崩溃点 | T1 正常 | T2 发生前 | T3 发生后 | T4 unknown | T5 task失联 |
|---|---|---|---|---|---|
| K0 intent事务前 | D | D，随后按N对账 | D，随后H | D(mode=probe_only)，随后U/H/F/W | D；失联按下表T5 |
| K1 intent已落账、broker受理前 | 同epoch S；换epoch X | S/X，由epoch唯一选定 | S/X，由epoch唯一选定 | S/X，载荷probe_only | S/X；同实例仍须task定时器 |
| K2 broker受理后、ACK前 | S/X | S/X，不因无ACK重复核销 | S/X，不因无ACK假定未发布 | S/X，不解除锁存 | S/X；ACK去重不能替代task回收 |
| K3 ACK收到、completed落账前 | S/X | S/X | S/X | S/X | S/X |
| K4 completed已落账 | A；换epoch X | A；换epoch X并N | A；换epoch X并H | A/周期probe；换epoch X且仅probe_only | 初始无结果失联→retiring→X；已proceed后失联为GAP |

对K1–K3，S与X的条件严格是 `target_epoch == current_epoch` 与不等，互斥且穷尽。替代事务前崩溃保留旧intent，恢复重做X；事务后崩溃只有新intent，恢复按其target_epoch选择S/X；E2未发送就换E3仍是X；superseded的迟到ACK只能审计。不存在旧intent和新intent同时有效的合法格。T4若旧execute intent尚有ACK待落账，必须先处理其送达状态，不能因重投执行载荷获得新许可；C-09锁存及C-10 guard仍拒绝。

### 核销、对账与实际发布的崩溃矩阵

| 时间线 | 核销事务前/后 | reconcile事务前/后（含ACK丢失） | 远端动作前/后 | outcome或probe终局事务前/后 |
|---|---|---|---|---|
| T1 正常 | 前→G；后同实例同id→R(granted)，新实例静默后→N/H/U按观测 | 如进入恢复，事务前重做探测；事务后同id→R，不能再发第二份许可 | 动作前中断转T2；动作后中断转T3 | 前按远端事实H/F/U；后R，closed不再执行 |
| T2 核销后远端未发生 | 核销已落账，不得再G；旧实例未静默→W | 新epoch resumed；未发生+许可通过→N；D12/pending不许可→F；许可事务ACK丢失同实例R(proceed)，换epoch重新静默/探测 | 执行前再崩溃仍走N；不得仅因有旧proceed跳过新epoch探测 | 未实际执行不得发outcome；执行后的失败按固定F映射；已提交则R |
| T3 远端已发生 | 已核销，无第二次核销 | resumed探测happened→H；事务前崩溃再探测，事务后R；D12不改远端成功事实 | 不重复执行；全部目标已出现才H，部分出现转T4 | 前重新确认H；后R；pending不将已发布改成未发布 |
| T4 indeterminate | C-09新id→recovery_indeterminate；旧epoch执行receipt被③拒绝 | indeterminate落账前按原恢复阶段；落账后C-10a新id非法，旧id只R(indeterminate_recorded)，换epoch仍U | probe_only没有动作出口；happened→H；not_happened且旧holder静默→F；未静默→W（活性缺口见C13-01）；仍unknown→U | C-11a/人工裁决都经publishing CAS；提交前重复只探测，提交后R；负向后仍保留R14复查与correction |
| T5 实例活、task失联 | 未核销或granted后无任何结果超时：retiring→回收→X→G或N/H/U | resumed后尚无reconcile超时同前；**proceed已提交后无outcome：GAP**，现文“已有reconcile结果”排除触发。按C13-01补phase期限后唯一retiring→X | 不可把子任务失联当not_happened；即使broker心跳正常也必须先整组静默再对账 | 已有终局事务则R；仅有中间reconcile不等于完成，不能停掉watchdog |

上述每个含远端观测的格，按下列穷尽函数选择一次：全部目标happened→H；全部not_happened且普通恢复许可合法→N；not_happened但许可不合法→F；unknown锁存后的not_happened只有静默后→F；部分/无法确认→U；静默前→W。同一事务的CAS与receipt决定并发单胜。**原文无法满足全部格唯一有效后继的部分已明确标GAP，未以表格记号掩盖缺陷。**

### 只探测通道是否能执行发布

未发现当前规范赋予它重新执行的合法路径：

1. 新epoch不能命中旧epoch的granted/proceed receipt；同实例hello重放先完成绑定，retiring实例先被拒绝。
2. indeterminate时C-09恢复臂明确排除；C-10仅允许none/execution_permitted，C-10a仅允许reconcile_required；C-11a响应没有proceed。
3. probe_only不能因“confirmed_not_happened”回到execute；其负向出口是静默后的F，且部分目标只能unknown。
4. 旧实例迟到outcome/reconcile经当前epoch校验拒绝；出向旧ACK也不能恢复旧执行权。

仍应补恶意/错误载荷夹具：unknown下强改mode=execute、复用旧consume/reconcile request_id、伪造旧epoch、probe_only后发release_outcome，全部不得执行发布原语。安全守卫已成立，C13-01关注的是安全等待如何有明确恢复动作，不建议为解决活性而放松锁存或静默。

## F. 同步项与范围收尾

已逐项核对 HLD B-7：mode注册/三规则/四YAML；E-02等待、暂停计时、两次放行复核；E-03六命令；deferred与新效应；Image/Bench/OptimizationPlan/范围/验证资产/确认集合/结果清单；MCP跨传输幂等；部署cgroup与基底；D12扩展均已登记。01仍以上游冻结v1.0+E-01为准，这些未落入0.13 **不重复报同步缺陷、不计入第二部分**。本报告候选增加的计划状态和phase期限随相应问题修订进入其契约/fixture，不另重复计数。

E-01继续有效；E-02/E-03的勘误通道与偏离清单本身成立，本方因上述HLD MAJOR仍不对该版整体给GO。D22、CLI cgroup、Gateway分阶段等待、cancel_pending实际正文、SourceProvider抽象、板子换板、Profile非劣准入、分期依赖未发现本轮范围内其他独立问题。P3的真实构建隔离依赖launcher可用，P4完成其部署资产/真实权限验收；实施计划应在P3提供所需最小launcher，不能先用宿主root直跑来冒充P3验收。P4的mock通过不替代P6远端输入证明和P7真实统计/优化验收。
