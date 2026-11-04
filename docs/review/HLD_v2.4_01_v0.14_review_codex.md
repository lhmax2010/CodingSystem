# HLD v2.4 / 01 v0.14 定向复审 — Codex

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.4 | **GO** | 0 | 0 | 1 | 0 |
| 第二部分：01 v0.14 | **NO-GO** | 0 | 1 | 1 | 0 |
| 新增同步项（不计入第二部分） | 无；已登记 B 第 7 组的项目不重复报 | 0 | 0 | 0 | 0 |

## 负责人七项裁决的独立评估

| # | 裁决 | 判断 | 理由及代价 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时显式化 | **成立** | 并行并不减免同 series 的汇合与报告义务。本版清理了“曾超时即永不成功”的旧断言，未覆盖的 timeout 仍不能发布。代价是汇合、旧 activation 退役及重试历史都必须持久化，不能仅看最终节点绿灯。 |
| ② | Quickbuild 默认取最新，在 Run 启动时解析固定 | **有条件成立** | 将“最新可用 Profile”作为 CodingSystem 的显式选择策略、随后固定 manifest 成立；但不能声称实测已经证明它就是 Quickbuild 的默认，也不能保证距 HEAD 只差一个快照发布间隔，见 H24-01。源码身份、环境身份分开证明的必要条件本版已经补齐。代价是可能比 reference 新、也可能仍落后于源码 HEAD，必须准确展示所选基线。 |
| ③ | Profile 严格匹配 v1，小改动复用 v2 | **成立** | 延续预定非劣界限、样本计划、方法版本及兼容条件，v2 缺省关闭，P7 实测后才按验证范围开启。本轮未放宽这些条件。代价是重采与准入评估成本；认可机制不等于保证任一工具版本已可复用。 |
| ④ | 每个 Run 有目标模块，只跑相关模块 | **成立** | 范围并集增长不因撤销缩小，防止通过修复或撤销逃避已触及模块的验证。撤销后的失败现按普通修复处理，有明确预算耗尽出口。代价是父版本回退后仍可能面对新增模块的测试，不能承诺所有撤销都会恢复成功。 |
| ⑤ | 以测试结果和多版本对比报告检验 AI | **成立** | ExpectedSourceManifest、实际配置身份、unknown 不可比、不可比不能人工补成通过，补齐了上轮条件；Review final 与正式对比报告的生成时序也分开。代价是 Quickbuild 当前证据不足时不能给 A/B 结论，需要本地后端；失败、撤销和未知仍须保留在历史报告中。 |
| ⑥ | Quickbuild 显式指定 base 的预检 | **成立** | Tizen 的显式输入限定为已证实的 Profile 编号与单包 commit 覆盖，不借用 VD Base CL 语义；未验证形态拒绝启用。实际 base/config/script 与 series 源码仍另行核对。H24-01 的证据标注修正不推翻此预检机制。代价是批量覆盖、暂存通道、镜像工程等不能提前作为可用能力。 |
| ⑦ | 重试成功可发布，须审批人确认；本版收窄确认范围 | **成立** | 当前 `release_evidence` 中各报告 task 的重试逐条确认，旧 series 的重试仍在首屏按位置、超时时长、次数汇总；`get_result` 和 Skill 保留完整清单。这仍满足“开发人员和审批人都要知道发生过超时”，只减少对已被替代证据的重复勾选。确认绑定条目 id 与内容摘要，核销再核对；拒绝确认不能发布。代价是历史记录需可追溯，而摘要不能被实现为隐藏历史或只显示一个总数。 |

## 范围、独立性与验证方式

日期：2026-11-04。评审开始已执行 `git pull --rebase`，返回 Already up to date。本轮被审文档来自提交 `8ccfdcd`；记录时工作区 HEAD 为 `ba94e9a7939ba2b7869c0b04d11d089f13fabab6`，后续提交仅增加其他评审文件，被审内容未变。未读取本轮其他两家的评审内容；上一轮三家意见、两份处置表、冻结基线和 Quickbuild 研究记录均作为本轮输入核对。

只检查处置落实、A21 变更及指定发布恢复机制。未将无直接冲突的旧条款扩大为全文重审；未修改被审文档；没有访问或探测 Quickbuild。为了核对新增 OS 接口条款，另查了 Linux 官方 cgroup v2 文档，来源列在 C14-01。

| 输入 | SHA-256 |
|---|---|
| `docs/00_Framework_HLD_v2.4.md` | `4a2f81e7fc5c4cf72cf03bc7efb3dded302e53844d9b9e3f198c0f197285700b` |
| `docs/01_Contract_Spec_v0.14.md` | `802875848f543ee3e3e3e90e9aa4ecf1f04cc13c53201c1d136ee9bdd73ce2c2` |
| `docs/00_Framework_HLD_v1.0_draft_frozen.md` | `0094d2f4ce52a11e9a89962e34355d942475a19a585d48c9194f2d47dbb08a12` |
| `docs/research/quickbuild_business_logic.md` | `33104bb3c1f70d5f196b83c7f02b5b664db5c0da512a56cf49738164498763c3` |
| `docs/review/HLD_v2.3_review_disposition.md` | `84d1bc4fbdfe64189f9b11629a7c23bbca7765af2994fa594e32ac29c4fcd1ae` |
| `docs/review/01_v0.13_review_disposition.md` | `909463337dba0baed82e1c9683d251725c547adc2402f7b994d67bbfa66c795b` |

验证是文档差异核对、反例与事务边界走查，并非执行尚未实现的 conformance。只读脚本核对 01 的 122 个 class 定义均在 A0 出现，CommandName 与三列注册表均为 21 项、集合相等，新增 ReleaseProbeDispatch / ReleaseDispatchPayload / ReleaseProbeResponse 均有索引。文中测试建议是后续需落地的夹具，不能视为已在真实部署通过。

## A. 上轮处置逐项核验

### HLD：14 个合并处置

| 处置 | 核对位置、结果与取舍 |
|---|---|
| M1 | §7.6.1、§5.2、§12 E0、§13 P6 已采用分配置证据等级、有界 probe、父子取消占额和镜像能力禁用。核心安全限制落实；默认行为、已知 ID 读取与样本镜像能力的证据措辞仍有 H24-01，故不认可“全部事实表述均已纠正”。 |
| M2 | §7.6.1/7.6.2 已绑定 snapshot、当前 series、逐包 base 与 expected tree，要求不可变暂存输入及实际应用证明，未验证则拒绝非空 series，明确 LocalGbsBackend 替代，不允许先发布业务代码喂构建。采纳成立。 |
| M3 | §7.6.1/7.8 已分 actual/published config digest、脚本 commit unknown、不可比与不缓存；未知时只有绝对测量。**不采纳同一时间窗口即视为可比，理由成立**：近时提交不能证明相同脚本或配置。 |
| M4 | §7A.4 已定义不可比→inconclusive→rejected_reverting，撤销提交时检查 parent_tree 并迁 reverted；§4.2.6①要求 comparison=verified。**不采纳人工确认补足 Bench 谓词，理由成立**。**不采纳本方两个新增计划状态也成立**：计划结束表示撤销动作完成，不表示新 series 通过验证；当前 series 的独立验证义务仍有效。撤销后普通修复比一律 fail_safe 更符合业务目标，预算耗尽仍有出口。 |
| M5 | §4.2.6③在创建候选同事务检查优化环余量≥2、各相关修复环余量≥1；拒绝不创建计划，返回 E-PLAN-NO-CAPACITY 后使用无进一步收益 status。§7A.4、§11.3 同步。运行时余量检查补足静态下限，成立。 |
| N1 | §4.3.5、§8.2/8.3 已收窄逐条确认、保留历史汇总、绑定 id+digest；核销复核失败不核销，release_failed(gaps_changed) 按固定映射关闭、须新 Run。符合冻结终态方向，不引入重回审批等待的旁路。 |
| N2 | §4.3.4、§8.6 已统一 gateway_session 超时固定 fail_safe、不经节点 retry；§11.3 加了配置 retry 仍失败的反例。落实。 |
| N3 | §4.2.6②明确每个多入边节点含 join/环回边目标取交，entry 未证明、其余已证明初值；§11.3 新增与路径枚举对照的 property。落实，见下方数据流走查。 |
| N4 | §7A.0 原则6改为审批前按当前 tree 相对 snapshot 的净 diff 重算；撤销触及项降历史，修复再引入须再确认。§11.3 有两分支。落实。 |
| N5 | §7A.5 Review final 读原始报告；ci_plan 完成事务生成正式对比报告作为同级附件，不回改 ReviewReport；§11.3 有事务前后崩溃夹具。落实，消除了倒置依赖。 |
| N6 | 规则①不再写“仅用于本规则”，B-7 不再沿用 unpinned_inputs；§11.3 对范围增长、基线差异、重试成功与不可比等使用新断言，追加 v2.4 用例组。落实。 |
| N7 | §7.6.1 base_mismatch 映射 image_failed_exhausted，不交 LogAnalyzer 试修；§11.3 有反例。输入证明失败不是源码诊断，取舍成立。 |
| N8 | §4.3.4 无环节点 external_timeout_min 缺省为 run_budget 上限；§11.3 有缺省夹具。落实。 |
| N9 | B 第7组补 E-SKILL-EMPTY-SERIES、E-PLAN-NO-CAPACITY、backend_source_input_unsupported、comparison 三值、确认摘要、结论字段及核销失败原因。落实，不向仍基于冻结 v1.0 的 01 重复报缺失。 |

### 01：6 个合并处置

| 处置 | 核对位置、结果与取舍 |
|---|---|
| Z1 | §2.2d 四阶段期限、持久化起算、重放不重置、awaiting_probe 排除退役、周期发送、retire_requested 与新序号重探测均落文；C-11a/模型/CF-AUTH-17c/e、20/b/c 对齐。合并两家方案成立，proceed 后失联不再漏检。静默实现依赖仍受 C14-01 影响。 |
| Z2 | §2.2d 明确特权 launcher、cgroup.kill、reclaimed 后再拉新实例、systemd 不自行重启、lapsed 同回收；retiring 除 heartbeat 外统一拒绝。方向成立，**指定根 cgroup.procs 判空不足以实现整个实例静默**，见 C14-01。 |
| Z3 | ReleaseProbeDispatch 不含计划和发布内容，出向命令独立、DispatchReceipt 判别联合、broker 只读 adapter、写调用计数为0、CF-AUTH-17f 均已落文；注册/索引无漏。§5.1 共用续跑描述和 CF-IPC-10 仍混用 execute 的前提，见 C14-02。 |
| Z4 | §5.1、CF-IPC-09 区分 reconciliation worker：终止 probe 组，无 receipt 恰一次 synthetic_worker_loss、有 receipt 复用，按 probe_attempt 能力矩阵处理。落实，没有再误终结业务 task。 |
| Z5 | CF-AUTH-09d 增 reclaimed 且 cgroup 空前置；09e 明确 pid 复用但子进程存活/未回收不能静默。原问题已修；需将本版新增 cgroup 判空问题补进夹具，而非再次归咎 pid 身份规则。 |
| Z6 | §2.2(c) 指向 C-11a；§5.1 两条出向字段与 dev3 版本更新落实。共用段尾的执行型旧语义残留并入 C14-02，不另计。 |

### “记录更正”的准确性

| 更正 | 判断 |
|---|---|
| HLD 旧 M5：保留期过期也可归还配额 | 更正准确。正文要求远端终态或确证从未提交；证据消失不是资源释放。 |
| HLD 旧 M6：“10 个”→Artifact 公布保留10天 | 更正准确，与研究 Q5 一致，并保留“未核验后台实际清理时点”。Recent Builds 的10条另属列表窗口。 |
| HLD 旧 M1：G' 删除边的描述 | 更正准确，删的是以 fail_safe 为目标的边，而不是先删除违反 compile 顺序的边再证明规则。 |
| 01 旧 Y2：pid 复用即静默 | 更正准确，pid 复用仅否定旧 leader，不能证明旧执行全部终止。新 cgroup 判空接口的缺陷不否定这次历史记录更正。 |

## B. 第一部分问题

### H24-01 — MINOR：Quickbuild 证据等级仍混淆框架策略、服务默认与样本能力

**位置**：HLD v2.4 §7.6.1“最新”“提交标记与跟踪”“镜像能力”、§12 E0/§13 P6及 A21相应措辞；HLD_v2.3_review_disposition.md 负责人②、M1。

**依据**：正文说“snapshot pin 把‘最新’解析为**当时最新可用的 Profile 快照**”，并称“落后量等于 Profile 快照的发布间隔”；处置表②称“**这正是 Quickbuild 自身不指定版本时的行为（实测已证实）**”。正文另称“**按构建号读取为推断方案，unverified**”及“**被调查的配置1917不产镜像（TARGET_IMAGE为空）**”。

研究 Q1 实测默认却是“**BUILD_REFERENCE=Ref. Snapshot**”，并限定“这只能证明取证时配置的默认，不代表所有工程永远相同”。Q3 已按已知构建号1213815/1213816读取变量、日志、manifest；Q6 未证明的是超过 Recent Builds 窗口后的完整找回能力。Q5 只证明“**本次 Base 样本 TARGET_IMAGE 为空，目录没有 images**”，不能外推配置的所有参数组合都不能产镜像。

**问题**：锁定策略安全性已改善，但“最新可用 Profile”是框架自己的可选政策，不能从 Ref. Snapshot 推导成服务默认；快照内单包 revision 也可能远旧于快照发布日期，不存在所述相对 HEAD 的固定落后界限。反向过保守的标签又把已经证明的已知 ID 读取，与尚未证明的枚举/完整找回混为一项。镜像禁用门槛合理，依据应为尚未验证，而非已证明永久不支持。属于事实溯源与验收边界问题；本版 fail-closed 和本地替代已阻断危险放行，故不升 MAJOR。

**候选文档 diff**（不要求本轮另探服务）：

```diff
--- docs/00_Framework_HLD_v2.4.md §7.6.1
+++ docs/00_Framework_HLD_v2.4.md §7.6.1
- 因此选用 Quickbuild 后端时，snapshot pin 把“最新”解析为当时最新可用的 Profile 快照。
+ CodingSystem 显式选择“项目/分支匹配的最新可用 Profile 快照”并在 pin 事务固定；
+ 这是本系统策略。研究已证实的服务默认是所调查配置当时的 Ref. Snapshot，
+ 尚未证明它始终等于最新可用 Profile；不得将二者标为同一项已证实能力。
- 落后量等于 Profile 快照的发布间隔。
+ 快照发布时间不构成逐包源码相对 HEAD 的落后上界；首屏显示实际快照编号、
+ 发布时刻和逐包固定版本。未取得证据的落后量标 unknown，不给出保证。
- 按构建号读取为推断方案，unverified，P6 验证。
+ 已知构建号的变量/日志读取已有样本证据；从提交前高水位枚举到目标标记的
+ 有界找回算法、权限与缺号/清理处理仍为 unverified，P6 验证完整找回能力。
- 被调查的配置1917不产镜像（TARGET_IMAGE为空）。
+ 所调查的1917样本未产镜像；未证实该配置的其他参数组合是否支持产镜像。
+ 可产镜像工程的提交、锁定和读回仍为 unverified，build_image 禁用门槛不变。
--- docs/review/HLD_v2.3_review_disposition.md 负责人②/M1
+++ docs/review/HLD_v2.3_review_disposition.md 负责人②/M1
- 这正是 Quickbuild 自身不指定版本时的行为（实测已证实）
+ 这是 CodingSystem 的显式选取策略；实测服务默认是 Ref. Snapshot，二者等价性未证实。
+ 同步 §12 E0、§13 P6、A21：验收的是有界找回算法，不把已知 ID 读取整体标成未证实。
```

**副作用及与负责人原意的取舍**：保留“取最新并固定”的产品选择，不擅自改回 reference；只纠正其依据，并暴露与服务默认可能不同。已知 ID 查询不必重复从零验证，但不能据此跳过崩溃找回验收。镜像能力仍需验证，不把这次文字修正当作启用授权。

**配套测试/夹具**：FakeQuickbuild 同时提供较旧 reference 与较新 Profile，断言选取并固定的是声明策略所指对象、首屏不宣称服务默认等价；快照刚发布而包 commit 很旧时不得计算固定 HEAD 落后量；已知 ID 可读但 Recent Builds 已滚动、扫描有缺号/权限缺失时按找回能力返回 indeterminate；一个不产镜像样本不得把整个配置登记为 unsupported。

## C. A21 变更与组合边界核对

### Quickbuild 的可用边界

| 项目 | 仓库证据与本版可用程度 |
|---|---|
| Profile 编号、单包完整 commit 覆盖、BUILD_NOTES | 有既有输入与回显证据，可作为受限输入形态；不推导批量/冲突/Remove 已验证。 |
| Profile 与构建根 base | 两条输入链；样本 Profile Oct-28、base Oct-13。snapshot pin 不是构建根锁定，正文已分开。 |
| 当前 series 实际源码 | ExpectedSourceManifest + 不可变暂存通道 + actual tree 才能证明。只回显 base commit 不能出成功 ImageReport；错误 tree→base_mismatch→image_failed_exhausted，不能 AI 试修掩盖。 |
| 实际 build.conf 与脚本 commit | 当前证据不足。发布摘要只作附件；unknown→unverifiable，不能给 A/B 判定、不能作为跨 Run 基线。人工确认环境缺口不使 Bench 谓词变真。 |
| 构建号找回、保留期、取消 | 标记已证实，完整找回仍需验证；公布30/10/7天不是后台清理保证；父终止而子仍跑不能归还配额。H24-01纠正读回与找回的分级。 |
| 镜像及首期替代 | build_image 仍 unverified，因此按现有证据，Quickbuild **尚不能承担本设计的完整修复/优化镜像流水线**；这不是隐藏的无出口。§7.6.1明确改配 LocalGbsBackend，P3/P5先提供本地构建，P6逐项启用。P6的“空 series/绝对测量”是其他所需能力已验证后的最大允许范围，不覆盖镜像禁用。 |

保守门槛本身不报缺陷：用户没有要求此轮保证 Quickbuild 已可用于非空 series，也未授权补做真实提交。源码暂存输入尚未验证是明确的能力验收项；规范已经给出所需不可变性、身份判据与失败/替代路径，不把未定输入适配冒充已具备服务能力。

### 净变更与优化计划

| 步骤 | 证明、计划与出口 |
|---|---|
| input:none 起点 | 证明 U（未证明）；普通 none 边保持 U，不能分派 needs-patch。 |
| asserts_nonempty 边 | 运行时先检查净 tree 不等于 snapshot，成功才使证明为 P。不能靠 status 声明造出净变更。 |
| 修复/优化/revert 的 advances | 都重置为 U，不能继承前一轮 P；revert 回非空业务父树也不在静态层自动恢复 P。 |
| 多入边与回环 | 全部入边取交；P与U汇合为U。重新经过有效 asserts_nonempty 才恢复P；运行时仍复核真实 tree。entry 的外部空输入条件保持U。 |
| 创建优化计划 | 静态容量是下限；事务内各环余量足够才提交候选并创建计划。容量不足返回 E-PLAN-NO-CAPACITY，不消耗候选轮、不留下 pending_validation。 |
| 优化 A/B 不可比 | BenchReport 落账同事务写 inconclusive/comparison_unverifiable，计划转 rejected_reverting；不可 no_further_gain 逃离。 |
| 撤销提交 | 新 series 段的 tree == parent_tree 后，同事务计划转 reverted；不回拨指针，不生成第二个候选计划，旧 series 报告不能支持新 series 审批。 |
| 撤销后失败 | 当前 series 普通构建/UT失败可进入普通修复环，或预算耗尽 fail_safe；没有未决计划，故不会第二次撤销同一候选。普通修复推进的新 series 仍要重验证。 |
| 撤销后 Benchmark 不可比 | 即使计划已 reverted，comparison=unverifiable 仍使必需 BenchReport 不通过，阈值 fail-closed；人工确认不能发布。 |

这解释了不新增 reverted_validating / failed 的取舍：撤销的事实状态与当前 series 验证状态分别有权威记录。四份示例原有回流结构未因本版修改而改变；本版对多入边和预算的加严不把它们改成绕过验证的路径。这里没有把“reverted”误读为“已经重新验证通过”。

### 当前证据链与历史超时的具体演算

1. 业务 series S1 的 UT 与静态审查并行；UT task U1 超时后同 task 后续 attempt 成功。U1 产生一条 retried，原超时不能删除；对应未完成 timeout 被成功覆盖，不再据它强制 fail_safe。
2. 后续 AI 修复产生 S2 并增加目标模块。S1 的 U1 成为历史重试，首屏仍按位置/时长/次数汇总；S2 必须重新获得当前范围的报告。若 S2 的报告 task U2 也重试成功，其记录属于当前 release_evidence，须逐条确认。
3. S2 上创建优化候选 S3，若优化前后输入不可比，计划 inconclusive→rejected_reverting；确定性撤销产生 S4，tree 回到 S2，计划立即 reverted。目标范围不缩减，S2 报告不能因 tree 相等直接充当 S4 报告；当前 series 常规验证继续。撤销的验证资产改动仅留历史；若普通修复再引入，则重新确认。
4. 若 S4 的 Quickbuild 读回仍不可比，当前必须的 BenchReport 谓词为假，**不能到可批准发布状态**；确认 environment_gap 不能补这个谓词。源码暂存未验证时更早拒绝非空 series，不能假定这条线上已经得到合法 Quickbuild 镜像。
5. 若改用已配置、输入可证明的本地路径并形成完整当前证据，审批首屏同时显示：当前 manifest/base/报告；当前证据 task 的逐条 retried；历史 series 重试摘要；全部 incomplete；多版本对比（含撤销与失败）。只确认当前要求的条目 id+digest，历史摘要不要求逐条勾选，但不能省略。
6. 决定后、核销前有相关记录新增或摘要变化，核销不消费授权，release_failed(gaps_changed) 按固定映射关闭，FeedbackReport 指出变化。没有“继续发布”和“回到同 gate 再审批”两个出口。核销以后新增超时只登记 pending，已发布事实不能被改写为未发布，首屏明确披露。

A21其余连带项已核对：Gateway登录等待超时固定fail_safe、无环外部等待缺省、远端效应有界probe登记、Review final附件时序、基线缓存排除未知输入、验证资产净diff重算、§11.3新增夹具、E0/P6能力gate与B-7索引。未发现本轮范围内其他独立问题。

## D. 第二部分问题

### C14-01 — MAJOR：根 cgroup.procs 判空不能证明整个 broker 实例子树已静默

**位置**：01 v0.14 §2.2(d)“实例租约”“静默”、§2.5 BrokerInstanceLease；CF-AUTH-09c/d/e、20/20c。属于本版将回收从进程组改为 cgroup 的直接新增问题，不是 HLD 范围扩展同步项。

**依据**：§2.2d要求“旧实例租约 = reclaimed ∧ 该实例 cgroup 内无存活进程”，但把确认方法指定为“**经 launcher 确认 cgroup.procs 为空**”；同节先写 cgroup.kill、“确认 cgroup 为空后才标 reclaimed”。BrokerInstanceLease 仅有 epoch/pid/pgid/start_time/lease/state，未给实例 cgroup 的持久化绑定。

**问题与反例**：普通 domain 层级中，实例根 E 的直接进程都退出，发布子进程仍位于 E/child 时，E/cgroup.procs 可以为空，整个实例却仍未静默。Linux为整个子树提供的是 `cgroup.events` 的递归 `populated` 状态。`cgroup.kill` 覆盖子树，但“已请求杀死”与随后证明子树无存活进程是不同步骤；现有确认方法不能正确判定后一步。该接口区别依据 [Linux 官方 cgroup v2 文档](https://docs.kernel.org/admin-guide/cgroup-v2.html) 的 Basic Operations、[Un]populated Notification 与 cgroup.kill 定义。

规范没有要求实例 cgroup 必须为禁止嵌套的叶子；相反把 cgroup 作为包含所有后代的回收边界。按现文实现可提前写 reclaimed，随后新 epoch 获恢复许可，或 C-11a 将“未发生”负向关闭，但旧子树尚有本地执行。即便最终SIGKILL会结束它，也已经违反冻结基线“本地不存在在途发布执行”的静默前置。这不同于明确接受的 R14 已离开本机的网络请求残余。应把杀进程、验证空子树、记录回收、允许新执行串成同一个可信回收协议。

**候选文档 diff**：

```diff
--- docs/01_Contract_Spec_v0.14.md §2.2d / §2.5
+++ docs/01_Contract_Spec_v0.14.md §2.2d / §2.5
- 经 launcher 确认 cgroup.procs 为空
+ 由 launcher 确认绑定于该 broker_epoch 的实例 cgroup 子树
+ 的 cgroup.events:populated=0；不得用根 cgroup.procs 为空替代递归确认。
+ 实例使用专属 domain cgroup；其路径和创建代次由 launcher 管理并持久化，
+ 在该 epoch 回收证明提交前不得删除/复用；所有 broker 后代不得迁出边界。
+ launcher 写 cgroup.kill 后等待上述空子树证据，再持久化 reclaimed；
+ 存在后代、接口读取失败、绑定无法核实或清理超时均不构成静默。
+ launcher 重启时按持久化绑定继续回收；目录不存在本身不是已回收证明。
+ 新实例启动与负向映射必须在该回收证明成立后执行；不改变远端 R14 残余。
 class BrokerInstanceLease(BaseModel):
     broker_epoch: int; pid: int; pgid: int; start_time: datetime
+    cgroup_path: str; cgroup_generation: str  # launcher 可信绑定，非 broker 自报
     lease_expires_at: datetime; state: Literal["live","retiring","lapsed","reclaimed"]
--- docs/01_Contract_Spec_v0.14.md CF-AUTH-09c/09e/20/20c
+++ docs/01_Contract_Spec_v0.14.md CF-AUTH-09c/09e/20/20c
+ 根 cgroup.procs 为空但子 cgroup 有发布进程：不 reclaimed、不静默，
+ 不授予恢复执行权、不作负向映射；子树 populated=0 且回收落账后方可继续。
+ 覆盖 launcher 在 kill 前后、空子树确认前后、reclaimed 提交前后崩溃；
+ 目录同名重建不能复用旧证明；清理失败保持等待并告警。
```

**副作用分析**：增加可信 launcher 的实例绑定与恢复记录，回收可能等待更久；这是兑现已经承诺的整实例静默，不是新增第二套 task epoch。也可选择显式强制“实例永远是不可嵌套且不可迁出的叶 cgroup”，但这会约束部署结构，递归判定更直接。不能通过单独扩大超时或再扫一次 leader PID 修复。

**配套测试/夹具**：在真实 cgroup v2 domain 子树下放置子组进程，验证根 procs 空而 populated=1 的情形；加入 fork/setsid、leader退出、pid复用、回收延迟/读取失败、launcher重启、路径复用组合。FakeLauncher 必须分别模拟 kill 已请求与子树已空，禁止一个布尔 kill_success 同时充当静默证据；断言新 epoch 的恢复许可和负向终局在证明前均为0次。

### C14-02 — MINOR：新 probe 出向协议仍继承了 execute 专属的续跑描述和夹具前提

**位置**：01 v0.14 §5.1末尾“出向命令（release_dispatch / release_probe_dispatch）”、CF-IPC-10；对照 §2.2d、C-11a。

**依据**：§5.1把两命令并列后仍称“**重放落到授权记录状态机（granted/resumed/rejected）**”；CF-IPC-10已经扩为两条命令，但预期仍统一写“**已核销须先静默**”。§2.2d则要求 indeterminate 时“**对 indeterminate 者不发可执行的 release_dispatch**”，周期向当前 live 实例发送 probe；C-11a 的负向结果才要求 holder 静默，未静默时还要能先得到 retire_requested。

**问题**：两事务送达模型可以共用，消费授权和取得执行许可不能共用。所有合法 release_probe_dispatch 的授权恰是已核销且 indeterminate；它不能以 granted/resumed 续跑。如果夹具按未核销/已核销的旧二维表机械扩到 probe，会生成非法组合，并可能要求先静默才允许本应在活实例上运行的只探测。主状态机及只读限制已明确，因此这是实现/测试指引冲突，按 MINOR，不否定锁存机制本身。

**候选文档 diff**：

```diff
--- docs/01_Contract_Spec_v0.14.md §5.1
+++ docs/01_Contract_Spec_v0.14.md §5.1
- 跨 broker 实例的续跑由 §2.2d 持有者更替重派承担，
- 重放落到授权记录状态机（granted/resumed/rejected）
+ 两种出向共用 DispatchReceipt 的送达/替代事务，业务续跑分别为：
+ execute：按 §2.2d 与 C-09 核销/恢复；已核销且非 indeterminate 时，
+ 必须旧 holder 静默后恢复并对账。
+ probe：仅用于已核销且 indeterminate，不 consume、不返回执行许可，
+ 换实例仍只探测；发送只探测不以 holder 静默为前提，负向映射才需要静默。
+ confirmed_not_happened 且 holder 未静默走 retire_requested 与新序号重探测。
--- docs/01_Contract_Spec_v0.14.md CF-IPC-10
+++ docs/01_Contract_Spec_v0.14.md CF-IPC-10
- 未核销与已核销两种前提；已核销须先静默
+ execute：未核销 / 已核销且非 indeterminate；后者恢复须先静默。
+ probe：仅已核销且 indeterminate；覆盖持有者仍活着的周期探测，
+ 以及换实例的 probe 替代，禁止转 execute、禁止授权消费和发布写调用。
+ 未核销 probe 等非法组合应拒绝，不以“最终执行完成”作为其期望。
```

**副作用分析**：不新增状态、命令或响应，仅把共用传输协议与不同业务权限分开。不会让负向映射绕过静默，也不让探测 ACK 充当完成发布。代价是 CF-IPC-10 需按载荷类型和 recovery_state 分组，不能复制同一执行型期望。

**配套测试/夹具**：当前活实例报 indeterminate 后，无换实例也能周期收到 probe；ACK 丢失同 id 重送只查远端；未发生且 holder 活着→retire_requested，随后新序号读回；换 epoch 的 probe intent 替代只有一个活动 intent；所有组合 consume调用及 FakePublisher 写调用为0，不能返回 granted/proceed。

## E. 五条时间线 × 崩溃点 × 阶段期限

### 唯一出口的判定规则

以下将送达事务、业务事务和阶段期限三轴分开列出，按持久化状态组合，避免把 ACK 等价于发布。每格的条件都是互斥选择，**等待也是合法出口，但须保留指定的驱动/告警，不能偷换为成功或未发生**。C14-01使所有依赖静默证明的格目前不能签字通过；C14-02是 probe 格共用文字冲突。表中的正确出口依 C-09/C-10a/C-11a 的专门规则列出，不将候选修订冒充现文已正确。

| 记号 | 唯一动作/出口 |
|---|---|
| D | 原 durable dispatch 创建一条 intent；逻辑 release task 不变。 |
| S | intent 的 target_epoch 等于当前 epoch：同 request_id 重送，实例内去重。 |
| X | target_epoch 不同：满足 §2.2d 条件后，旧 intent→superseded 与新 intent 同事务；completed 历史保留。载荷按授权状态选择 execute 或 probe，不能同时选二者。 |
| A | completed 仅表示送达；同实例等业务结果并保持阶段期限，不能再次启动执行；新实例走 X。 |
| G | 未核销有效授权只核销一次→publishing；无效/过期走既定失败映射，running 下 D12 漂移走 C-14。 |
| Q | 回收对应实例：retiring/lapsed→launcher清理→真正空子树→reclaimed。失败保持原 Run 状态并告警，不强行推进。**当前 C14-01 使该步骤的证明不可靠。** |
| R(f) | 已核销非 indeterminate：Q 后新 epoch resumed，再对账；全部发生→H；全部未发生且原子许可有效→P；全部未发生且许可无效→F；部分/未知→U。f为实际观测，四分支互斥。 |
| P | 同事务 execution_permitted 与 awaiting_outcome/期限；获得 proceed 的当前实例才可执行。 |
| H | 全部目标已发生：ledger级 released 映射，closed(succeeded)，pending记摘要。 |
| F | 按 release_failed 固定映射：admin_finalize > cancel > fail_safe > 缺省fail_safe；不伪造未执行的 release_outcome。 |
| U | indeterminate 锁存，publishing；周期只探测，不因阶段超时退役，不再获得执行许可。 |
| B(f) | 只探测：全部发生→H；全部未发生且 holder 已真正静默→F；全部未发生但 holder 未静默→J；部分/未知→U。 |
| J | 观测+retire_requested+holder retiring 同事务；Q 后新 probe_seq/new request_id，再用 B(f)；不复用旧负向观测直接关闭。 |
| I | 同实例、同幂等域、同id重放首响应；已退役/旧epoch先被连接守卫拒绝。终局已提交则不再迁移。 |

### 送达层：五条时间线、五个崩溃点

T1正常；T2核销后远端发生前崩溃；T3远端发生后终局未落账；T4已锁存indeterminate；T5实例活但单个发布task失联。K0–K3可发生在初次或恢复发送，授权状态始终取Ledger，不能由是否收到ACK猜测。

| 崩溃点 | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| K0 intent事务前 | D→G | D→R(f) | D→R(f=发生) | D(probe)→B(f) | D；随后由当前阶段期限驱动 |
| K1 intent已提交、受理前 | S或X，由epoch唯一选择 | S或X→R(f) | S或X→H | S或X，仅probe→B(f) | S或X；送达不撤销task期限 |
| K2 已受理、ACK前 | 同K1，不新增task | 同K1，不重复核销 | 同K1，不因无ACK假定未发生 | 同K1，不解锁执行 | 同K1；业务失联仍由期限处理 |
| K3 ACK后、completed事务前 | 同K1 | 同K1 | 同K1 | 同K1 | 同K1 |
| K4 completed事务后 | A | A；新epoch X→R(f) | A；新epoch X→H | A；下周期新探测或换epoch X(probe) | A；前三阶段到期Q，awaiting_probe则U |

S/X条件分别为epoch相等/不等。X事务前崩溃保留旧intent，事务后仅有新intent；E2尚未发送再换E3继续X；迟到旧ACK只审计，不能将superseded改回completed。T4若仍有旧execute intent，先依送达协议收敛该intent，不能额外并存probe intent；锁存守卫与broker只读分支不允许借重送恢复执行权。

### 业务层：事务前后与远端动作边界

| 时间线 | 核销提交前/后崩溃 | 对账/许可提交前/后崩溃 | 动作或探测前/后崩溃 | 终局提交前/后崩溃 |
|---|---|---|---|---|
| T1 正常 | 前按G；后同实例I(granted)，实例更替Q→R(f) | 首次正常路径无此事务；若已进入恢复则前重做对账、后I | 动作前转T2；动作后转T3 | 前重取事实；后I，closed不可重开 |
| T2 核销后、未发生 | 已核销，不能再G；Q后恢复 | resumed提交前仍旧holder；提交后awaiting_reconcile；not_happened许可提交前重新判断，提交后同实例I(proceed)，新实例重新Q→R(f) | 未发生+许可有效P；不允许因旧proceed跳过新epoch对账 | 未执行时不用outcome；许可拒绝事务直接F；已提交F则I |
| T3 已发生 | 已核销，不能再G | resumed后全部目标发生→H；D12只登记pending不阻断H | 不再执行发布；只有部分目标出现则转T4 | 前重新确认发生→H；后I；pending不推翻已发布事实 |
| T4 indeterminate | C-09拒绝recovery_indeterminate，不消费第二次 | 锁存提交前仍按原恢复阶段；提交后U，旧id只I，新id的C-10a拒绝 | 只能B(f)，不存在发布动作；J事务前未记录则重新探测，事务后Q并使用新序号再探测 | C-11a/C-11共用publishing状态CAS；前按事实分支，后I，负向后保留R14复查 |
| T5 实例活、task失联 | awaiting_consume到期Q；若consume已提交则实际阶段为awaiting_outcome，按该阶段处理 | awaiting_reconcile到期Q；proceed已提交即awaiting_outcome，ACK丢失不取消期限，仍到期Q | 失联不证明未发生；Q后R(f)或U，依锁存状态唯一选择 | 有终局则I；无终局且只见中间结果不能停watchdog |

对账中的not_happened只有一个原子许可判定：允许→P，不允许→F；不是先发许可再异步核对D12。confirmed_happened与F的映射都在报告事务内，因此ACK丢失不会形成第二个终局。Publishing仍保留冻结的远端事实优先规则。

### 阶段期限轴：与上面每个崩溃格组合

期限处理只读取恢复后的**当前持久化phase**，不是崩溃前内存phase。下表应用于上面K0–K4、consume/resumed/proceed/结果事务前后各格；事务前取旧phase，事务后取新phase，故不存在提交一半时同时触发两个阶段的合法状态。

| 到期的当前phase | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| awaiting_consume | 无完成事件→Q→X→G | 已核销旧阶段不可达；恢复execute intent若新设此阶段→Q→X→R(f) | 同左，但观测全部发生→H | 锁存后不得新发execute；旧阶段到期不适用，当前应为awaiting_probe | Q→X；未核销G，已核销R(f)，按授权状态唯一选定 |
| awaiting_outcome | 无outcome→Q→X→R(f)，不能直接F | Q→R(f)；未发生许可有效才P | Q→R(f=发生)→H | 当前应为awaiting_probe；旧deadline不得退役 | **包括proceed提交后ACK丢失**，Q→R(f) |
| awaiting_reconcile | 正常路径未进入；若恢复到此阶段则Q→R(f) | Q→R(f)，不得仅凭上次未发生观测发P | Q→R(f=发生)→H | indeterminate事务已切phase，旧deadline不得退役 | Q→R(f)，心跳正常也不豁免 |
| awaiting_probe | 仅锁存后可达，按T4 | 若对账转unknown，按T4 | 若仅部分可证转unknown，按T4 | **仅U：周期只探测B(f)，不因该期限Q** | 若实际状态为unknown则U，不能沿“task失联”另触发Q |
| 旧phase的到期事件或已closed | 非当前阶段无完成事件这一前提不成立；忽略 | 同左 | 同左 | 同左 | 同左 |

每格的Q都受C14-01影响：当前写法可能把“应等待”的格误推进到恢复/负向终局，故第二部分不能GO。实现夹具应将状态/phase/期限守卫置于同一Ledger事务：结果先提交时旧期限失效；到期先提交retiring时后到结果按连接守卫拒绝，然后新实例对账；不能在定时器预读phase后无条件退役。该项是现有“到期仍无该阶段完成事件”的必要测试展开，不另计新问题。

### 周期探测是否形成重启循环

逐步检查：E2作为holder报indeterminate→锁存且awaiting_probe；多次unknown或probe超时只继续probe，**不退役E2**。首次not_happened且E2未静默→J，退役的明确是granted_epoch所指E2；Q后E3只探测，**probe不会把granted_epoch改为E3**。E3读回not_happened时，E2已真正静默→F；若unknown则继续U，不退役E3；若happened则H。因此正常回收完成后没有“每次负向探测都杀掉新探测者”的循环。J的ACK丢失不撤销已落账retiring，也不复用旧观测直接F。

若E3本身断连且租约失效，lapsed依同一launcher流程回收，这是实际实例失效，不是awaiting_probe的业务超时误触发。清理失败只告警等待，不无限创建新实例。需修正C14-01才能保证此处Q的前提真实。

### 只探测能否被用于执行发布

专门规则下没有合法执行出口：ReleaseProbeDispatch不含发布计划/内容；只读adapter不加载写原语；C-09恢复臂排除indeterminate；C-10与C-10a的recovery_state守卫均排除它；C-11a响应没有proceed。旧epoch的granted/proceed receipt先被连接守卫挡住，新epoch又不能命中旧幂等域；篡改kind或借旧request_id不能取得许可。FakePublisher写调用=0已列为conformance强制项。

这不是对任意被攻陷的TCB进程的沙箱证明；本轮要求是在可信broker实现结构和契约中杜绝probe调用写路径，v0.14已经给出了结构约束。C14-02要求把共享协议与夹具也写成这个含义，不能让“所有出向重放都走granted/resumed”的旧文字引导出另一种实现。

## F. 同步项与交付边界

已核对HLD附录B第7组：三条静态规则与按mode登记、外部等待/计时与Gateway、ExpectedSourceManifest/实际输入闭包、Bench比较与OptimizationPlan、范围/验证资产/对比报告、release_evidence/acknowledged_gaps、get_result清单/结论字段、核销gaps_changed、新错误码、MCP入口与部署launcher等均已登记。本轮**无新增未登记同步项**，不把这些尚未扩入01的字段计为契约缺陷。

E-01继续有效；规则①③的汇合必经不替代E-01/V-13b的普通支配。C14-01是01本版主动规定的静默实现错误，C14-02是新增probe命令的自相冲突，两者都属于第二部分本身，不能以HLD同步未完成豁免。

候选diff仅存在于本报告，未改动被审文档或背景研究记录。本轮结论不声称真实Quickbuild、板子、launcher或参考实现已验收。
