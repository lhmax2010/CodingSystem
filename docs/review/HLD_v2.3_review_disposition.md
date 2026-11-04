# HLD v2.3 第三轮三方评审处置表（→ v2.4）

裁决输入：Kimi **GO**（0 BLOCKER / 0 MAJOR / 1 MINOR / 1 NIT）；Claude Code **NO-GO**（0 BLOCKER / 3 MAJOR / 4 MINOR / 1 NIT，另单列同步项 1 MINOR）；Codex **NO-GO**（0 BLOCKER / 3 MAJOR / 3 MINOR）。第一部分合计 17 条意见（含 1 条同步项），归并为 14 个独立问题（5 个 MAJOR 级、9 个 MINOR/NIT 级），**全部采纳**。其中 4 处在两家方案之间作了取舍，理由逐条写明。

三家在两处独立指向同一问题：Quickbuild 一节有能力写过了头（Codex、Claude Code），以及组合场景下优化计划没有出口（Codex、Claude Code）。Kimi 在组合场景里假定撤销后"重验证通过 → reverted"可以发生，没有覆盖不可比的分支，因此未发现后者。

---

## 负责人七项裁决：评审方意见与本版处理

| # | 裁决 | Kimi | Claude Code | Codex | 本版处理 |
|---|------|------|-------------|-------|----------|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | 成立 | 成立 | 成立 | 保留；清理残留措辞（N6） |
| ② | Quickbuild 默认取最新，在 Run 启动时解析固定 | 成立 | 有条件成立：实测只证实单包覆盖，建议把"最新"解析为最新 Profile 快照 | 有条件成立：须区分源码基线、应用 series 后的源码与构建环境 | **保留**。"最新"解析为当时最新可用的 Profile 快照——这正是 Quickbuild 自身不指定版本时的行为（实测已证实）；被测源码身份另行证明（M1、M2） |
| ③ | Profile 严格匹配 + 小改动复用预案 | 成立 | 成立 | 成立 | 保留，无改动 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | 成立 | 成立 | 成立（指出撤销后范围不缩减须有出口） | 保留；撤销后的出口由 M4 补齐 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | 成立 | 成立 | 有条件成立：测试证据须确实来自所声称的源码及可比输入 | 保留；源码身份与可比性证明见 M2、M3，报告时序见 N5 |
| ⑥ | Quickbuild 可加 Base CL，否则默认最新 | 成立 | 有条件成立：Tizen 侧未确认 Base CL 机制 | 有条件成立："未证实能指定"不能写成"实测证明不能指定" | **保留**。Tizen 侧的"显式 base"落为"指定 Profile 快照编号 + 个别包 commit 覆盖"；能力按证据等级登记（M1） |
| ⑦ | 超时后重试成功可以发布，但每条重试记录须审批人逐条确认 | 成立 | 有条件成立：只应逐条确认当前 series 证据链上的重试，确认须绑定记录内容 | 成立 | **保留，按 Claude Code 收窄确认范围**：当前证据链上的重试逐条确认；被取代版本上的重试在首屏汇总列出、不要求逐条勾选；确认绑定内容摘要（N1） |

---

## MAJOR

| # | 问题 | 来源 | 处置与采用方案 | 理由 |
|---|------|------|---------------|------|
| M1 | §7.6.1 把调查未证实的能力写成已具备：全量包锁定（实测只证实单包覆盖）；按标记 probe（Recent Builds 只有 10 条、无服务端搜索）；脚本版本"可得时"与"读不回即不可比"自相矛盾；被调查配置不产镜像；取消是否联动子构建未知；"不可锁定"把"未证实"写成"不支持" | CC H23-01（MAJOR）、Codex H23-04（MINOR） | **合并**。取 CC："最新"解析为当时最新可用的 Profile 快照（全部包版本由快照 manifest 决定，`SNAPSHOT_NUM` 锁定），显式指定的个别包经 Build Package List 覆盖；probe 改为有界——提交 intent 记录提交前最大构建号，按构建号逐个匹配标记，扫描范围外即 indeterminate，§5.2 远程构建效应改为"可 probe（有界）"；产镜像工程另行只读调查，之前 `build_image` 不得启用；`cancel_pending` 跟踪父 trigger 及全部子构建。取 Codex：每项能力按配置登记 `verified` / `unverified` / `unsupported`，`unverified` 不得启用；"不可锁定"改为"本次调查未证实可锁定"；Remove 列为 unverified。§12 E0 与 §13 P6 gate 改为按证据等级表逐项验收 | 两家各补一面：CC 给出实测已证实的可用组合，Codex 给出不把推断写成事实的登记方式 |
| M2 | 锁定规则只指向 snapshot，未闭合当前 series 的远端源码身份：逐包填 base commit 并读回一致即可通过，被测的修复 / 优化 patch 是否真的被远端应用无从证明 | Codex H23-01 | **采用 Codex**：每次构建生成 ExpectedSourceManifest（snapshot、series、逐包 base commit、应用后的 expected tree）；改动的包必须经已验证的构建暂存输入通道送达远端（不可变、与正式发布目标隔离、凭据仍只在 Gateway），读回须证明 series 应用后的实际 tree；该通道为 `unverified`，未验证时 Quickbuild 拒绝非空 series 的构建（`backend_source_input_unsupported`），流水线改配本地后端；不得为满足构建输入提前把 patch 发布到业务仓 | 只证明 base 一致、不证明被测代码确实被构建，测试结果就可能来自旧代码——直接违背负责人"测试结果不能造假"的前提 |
| M3 | 发布目录的 build.conf 摘要被当成实际构建输入等价证明；脚本版本只读到分支名 | Codex H23-02；关联 CC H23-01 第 3 点 | **采用 Codex**：`actual_build_conf_digest` 与 `published_build_conf_digest` 分列，后者只作证据附件；实际配置或脚本 commit 为 `unknown` 时 `comparison = unverifiable`；未证明实际输入的镜像不进入基线缓存。按目前证据，Quickbuild 在 P6 补出实际输入证据前只做绝对测量，需要 A/B 结论的流水线使用本地后端 | **未采用 CC 的"脚本读不到时记为 config_tradeoff、两侧在同一提交窗口内即视为可比"**：时间窗口只是降低概率，不是证据；CC 自己也指出"读不到就忽略等于静默放行"，窗口方案是它的弱化形式。代价是首期 Quickbuild 不承担 A/B 判定，CC 担心的"bench_gate 恒为 fail"由流水线改配本地后端避免，而不是放宽可比性 |
| M4 | 组合场景下优化计划无出口：优化前后 A/B 不可比时 opt_verdict 无定义，计划卡在 pending_validation；"重验证通过后迁 reverted"无执行者与判据，撤销后若 UT 失败或不可比则既不能二次撤销也不能结束；BenchReport 谓词放进了 unverifiable | CC H23-02、Codex H23-03 | **主体采用 CC**：优化前后不可比 → `opt_verdict = inconclusive`（原因 `comparison_unverifiable`）→ 撤销；**撤销段提交的事务内计划即迁 reverted**（判据 tree_digest == parent_tree）；撤销后的重验证按当前 series 的常规义务处理——UT 失败走普通修复环或 fail_safe，Benchmark 不可比则谓词为假、阈值 gate fail。BenchReport 谓词改为 `comparison = verified`。**谓词例外取 Codex**：不可比不能经人工确认满足谓词 | **未采用 Codex 新增 `reverted_validating` / `failed` 两个状态**：撤销后的重验证本来就由规则①③与审批 CAS 强制，单独再建计划状态是重复约束；而 Codex 方案把"撤销后 UT 失败"固定为 fail_safe，会让一个仍可修复的业务 patch 直接失败。**未采用 CC 的"不可比经人工确认后满足 Bench 谓词"**：负责人原则是以测试结果为准，没有可比结果就没有结论，人不能替测量补出结论（Codex H23-02 同此意见） |
| M5 | 修复环容量 ≥ 1 + max_opt_rounds 在示例一上可被击穿：业务修复先用满镜像修复环后，优化候选失败需要撤销，超出环预算，已验证的业务 patch 落入 fail_safe | CC H23-03 | **采用 CC**：Optimization 提交候选时编排在同一事务内做准入核对——优化环剩余 ≥ 2 且优化重验证路径上每个修复环剩余 ≥ 1，否则以 `E-PLAN-NO-CAPACITY` 拒绝创建计划，Optimization 返回"无进一步收益"（不计违规）；静态容量规则保留为下限 | 静态规则无法知道业务修复会用掉几轮，只有运行时准入能兑现"不因还想再优化而丢掉已验证 patch"的承诺 |

## MINOR / NIT

| # | 问题 | 来源 | 处置 |
|---|------|------|------|
| N1 | retried 逐条确认覆盖整个 Run，包括已被取代的版本；确认未绑定记录内容；核销复核失败的出口未定义 | CC H23-04 | 采用。当前 series 证据链上的 retried 逐条确认，其余汇总列出；`acknowledged_gaps` 每项 = (条目 id, 内容 digest)；核销复核不通过 → broker 返回 release_failed(reason = `gaps_changed`)，按固定映射关闭，须新建 Run |
| N2 | Gateway 登录等待超时三处说法不一（固定 fail_safe / 合成超时 / 按节点重试） | CC H23-05 | 采用。统一为固定 fail_safe、不经节点 retry，超时类别 gateway_session |
| N3 | 规则②"汇合处取交"范围不明 | CC H23-06 | 采用。每个多入边节点（含 join 与环回边目标）取交，entry 初值"未证明"、其余"已证明"，迭代至不动点 |
| N4 | 被撤销的候选留下的验证资产触及项仍要求确认 | CC H23-07 | 采用。审批前按当前 tree 相对 snapshot 的净 diff 重算，已撤销者降为对比报告中的历史记录 |
| N5 | Review final 要"随附"的对比报告，直到下游 ci_plan 完成才生成 | Codex H23-06 | 采用。Review final 读取原始报告、不引用正式对比报告；正式报告在 ci_plan 完成事务生成，作为同级附件呈现，不回改 ReviewReport |
| N6 | 残留措辞与相反断言：规则①"仅用于本规则"；附录 B 的 `unpinned_inputs`；§11.3 旧断言"范围不可变""同一 base""超时不得 succeeded"；示例未覆盖 retry | Codex H23-05、CC H23-08 | 采用。逐处修正；§11.3 追加 v2.4 用例组覆盖重试、不可比与撤销分支 |
| N7 | `base_mismatch` 的节点 status 归属未定 | Kimi K-01 | 采用。返回 `image_failed_exhausted`(reason = base_mismatch)，不经 LogAnalyzer 修复回流 |
| N8 | 不在任何环内的节点，`external_timeout_min` 缺省未定义 | Kimi K-02 | 采用。缺省 = `run_budget.max_wall_clock_min` |
| N9 | 同步项：`E-SKILL-EMPTY-SERIES`、`succeeded_with_gaps` 结论字段、核销复核失败原因未登记附录 B | CC 同步项 S-01 | 采用，补登附录 B 第 7 组；另补 `E-PLAN-NO-CAPACITY`、`backend_source_input_unsupported`、`comparison` 三值等本版新增项 |

---

## 记录更正（上一轮处置表 HLD_v2.2_review_disposition.md）

- **M5**："配额在远端确认终态（或保留期过期）后恰好归还一次"——括号内的"或保留期过期"不正确，以正文为准：只有远端确认终态或确证从未提交才归还，证据过期不视为终态（Codex 指出）。
- **M6**："产物保留 10 个"应为"Artifact 公布保留 10 天"，且为站点公布政策、未核验后台实际清理时点（Codex 指出）。
- **M1**：对 G' 的描述"去掉从 Optimization 出发不经 compile 的边"与正文不符；正文为"从 `opt_patch_ready` 目标出发、删去全部以 fail_safe 为目标的边"，以正文为准（Codex 指出）。

## 下一轮建议

本轮无 BLOCKER；三家 MAJOR 集中在 Quickbuild 一节与优化计划的出口，均已按机制补齐，其余为措辞与边界。Kimi GO，Codex 与 Claude Code 两家的 MAJOR 落点高度重合。建议**再审一轮，范围继续收窄**：只核对本版改动（A21 所列）与两处新机制——Quickbuild 证据等级与被测源码身份证明、优化计划撤销后的出口与运行时准入。
