# HLD v2.2 第二轮三方评审处置表（→ v2.3）

裁决输入：Kimi **GO**（0 BLOCKER / 0 MAJOR / 2 MINOR / 1 NIT）；Claude Code **NO-GO**（0 BLOCKER / 8 MAJOR / 12 MINOR / 1 NIT，另单列同步项 3 MAJOR / 6 MINOR / 1 NIT）；Codex **NO-GO**（0 BLOCKER / 12 MAJOR / 3 MINOR，另单列同步项 3 MAJOR / 1 MINOR）。第一部分合计 39 条意见，归并为 23 个独立问题（13 个 MAJOR 级、10 个 MINOR/NIT 级），**全部采纳**。其中 9 处对评审方候选方案作了合并或取舍，理由逐条写明；1 处（M3 的"重试成功是否算通过"）两家给出不同产品语义，已由负责人裁定（见文末"负责人裁定"）。

另有 Quickbuild 业务逻辑实测（执行 Codex，`docs/research/quickbuild_business_logic.md`，commit 1907da3）一并纳入 §7.6.1，见 M6。

同步项（HLD v2.x 核心修订 ↔ 01 v0.12 现文）两家共 14 条，与第一轮一致，不计入 01 结论，全部确认已在 HLD 附录 B 第 7 组登记；本版补登一处遗漏（S-03：§4.3.5 放行谓词进入核心迁移表），见文末"同步项"。

---

## 负责人六项裁决：评审方意见与本版处理

三家都按要求独立评估，没有简单附和。结论：**六项全部保留**，评审方提出的条件全部以补机制的方式满足，没有一项被改回原方案。

| # | 裁决 | Kimi | Claude Code | Codex | 本版处理 |
|---|------|------|-------------|-------|----------|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | 成立 | 有条件成立：规则③仍按字面路径检查，示例一被拒；"不得 succeeded"无执行点 | 有条件成立：同左；且与冻结的"已发布即 released"映射冲突 | **保留并行**。规则③改用同一套"汇合必经"（M1）；超时分类 + 结构保证 + 审批与核销两次复核 + 发布后显式呈现（M3） |
| ② | Quickbuild 不指定 CL 默认取最新，在 Run 启动时解析固定 | 成立 | 有条件成立：须与 git snapshot 同一次解析；"读回不符即无效"须写进正文 | 有条件成立：同批提交不等于输入相同 | **保留默认最新 + 可选显式 base**。按实测：包提交与 Profile 快照可锁定；build root base、build.conf、脚本分支锁不住，改为逐项读回比对，不一致即 `comparison = unverifiable`、不作为 gate 输入（M6） |
| ③ | Profile 严格匹配，预留小改动复用的放宽预案 | 成立 | 有条件成立：伪探针编译选项未列入构建输入；"差异不显著"不能当"等价" | 有条件成立：同后者 | **保留策略 v2（缺省关闭）**。前置条件增加伪探针选项入构建输入闭包；开启条件改为非劣证明（M10） |
| ④ | 每个 Run 必须有目标模块，只跑相关模块的 UT/Benchmark | 成立 | 有条件成立：范围在创建时定格，AI 修复改到的范围外模块不被验证 | 有条件成立：创建时还没有 patch，无法定格；显式 suites 可绕过底线 | **保留按模块限定**。范围在首次提交 patch 时确定，之后随真实改动只增不减；规定最低套件集合（M9） |
| ⑤ | 用每轮 UT/Benchmark 结果和多版本对比报告检验 AI | 成立 | 有条件成立："测试结果不能造假"的前提是 AI 不能改验证资产 | 有条件成立：采纳率不等于准确率 | **保留**。新增验证资产保护（M11）；分析类 AI 改为分别统计采纳率与准确率（N9）；报告生成时点与 digest 绑定（N2） |
| ⑥ | Quickbuild 可加 Base CL，否则默认最新；由 Codex 实测 | 成立 | 成立 | 成立 | 已由执行 Codex 实测，结论写入 §7.6.1 与 §12（M6） |

---

## MAJOR

| # | 问题 | 来源 | 处置与采用方案 | 理由 |
|---|------|------|---------------|------|
| M1 | 规则③（优化后必须重验证）仍按"每条路径"检查，示例一经 review_static 分支被拒；附录 B 对规则③同时写了普通支配与汇合必经 | Codex H-01、CC H22-01；关联 Codex H-15、CC H22-18 | **采用 CC 的 G' 子图 + 汇合必经**：在去掉"从 Optimization 出发不经 compile 的边"后的子图上，要求 UT、Benchmark 对每个 release 为汇合必经；**补 Codex 的运行时义务检查**——series 推进后，release 前须有该 series 的 UT/Benchmark 通过报告，否则审批 CAS 拒绝。环容量：优化环 ≥ 2 × max_opt_rounds（候选 + 撤销），修复环 ≥ 1 + max_opt_rounds。附录 B 改为"规则①③共用汇合必经，E-01/V-13b/V-15 维持普通支配" | 规则①③共用一个定义，示例一可加载；静态规则只证明"图上必经"，运行时检查再挡住"图上必经但本轮没跑"的情况，两者不可互替 |
| M2 | 规则②：`advances` 只说明推进过 series，不证明有净变更；后续撤销可让早先的非空证明失效；静态检查未限定 `input: none`，按字面会误拒示例一；`input: patch` 下净变更为空的 series 未被拒 | Codex H-02（MAJOR）、Kimi N-01、CC H22-10 | **合并**：静态检查只对 `input: none` 做（Kimi/CC 范围），检查方法取 **Codex 的净变更数据流**——`advances` 重置证明，撤销段可使证明失效；`submit_patch` 对净变更为空的 patch 拒绝（`E-SKILL-EMPTY-SERIES`，取 CC）；所有流水线在分派需要 patch 的节点前做运行时净变更检查。Compiler 的 RPM 模式登记为 optional 输入（取 Codex），优化专项首轮可空跑基线 | 数据流分析是唯一对撤销正确的静态方法；运行时检查兜住静态分析无法覆盖的情况 |
| M3 | 超时"不得 succeeded"没有执行点；`on: sys.timeout` 可路由到任意节点；与 §7.6.1、§7A.2 的"不阻断发布"冲突；重试后成功是否算超时项未定义；审批与核销之间新增超时无人复核；发布后超时与冻结映射冲突；`gate_expired ≠ approved` 未进规则清单；两处"通过"谓词定义不一致 | Codex H-03、CC H22-02、CC H22-11、Kimi N-01b | **主体采用 CC**：incomplete 分四类（timeout / config_tradeoff / environment_gap / verification_asset_change）；`on: sys.timeout` 只能指向 fail_safe，未被覆盖的超时必然 fail_safe；审批事务核对无 timeout 类条目、environment_gap 与 verification_asset_change 逐条出现在 `acknowledged_gaps`；非发布路径结论为 `succeeded_with_gaps`。**补 Codex**：核销事务再次复核同一条件；publishing 后的超时只登记，终态按冻结映射，首屏显示"已发布，但发布后出现超时/未完成"。**补 Kimi**：两条路由规则入 §4.2.6 清单。**补 CC H22-11**：各报告"通过"谓词统一定义一处，覆盖撤销与读回失败 | **负责人裁定（折中两家）**：重试成功是真实通过的测试结果，可以发布（取 CC，未采用 Codex 的"出现过超时即禁止发布"）；但每条 `retried` 记录须在审批时逐条呈现并由审批人确认（纳入 `acknowledged_gaps`），审批人不认可即 reject、不发布——保留 Codex"超时不能被重试悄悄掩盖"的要求，由人而非规则作最终判断 |
| M4 | Gateway 会话失效等待只覆盖已拿到 build_ref 之后；提交前、提交中失效无处挂起 | Codex H-04 | **采用 Codex**：新增 `gateway_session` 等待类，带 phase（提交前 / 提交中 / 已提交）；`task_suspend` 只在本 attempt 无其他在途效应时可用；提交中失效先 probe 再挂起 | — |
| M5 | 取消远程构建失败即归还配额，实际在途构建可无限超额 | Codex H-05 | **采用 Codex**：新增 `cancel_pending`，配额在远端确认终态（或保留期过期）后恰好归还一次 | — |
| M6 | "同批构建"不能证明 unpinned_inputs 两侧相同；与 git snapshot 不是同一次解析；读回不符即无效只写在测试里；"干净应用"无定义 | Codex H-06、CC H22-12；执行 Codex 实测 | **以实测为准重写 §7.6.1**：同一次 snapshot 解析得出包提交列表，经 Build Package List 锁定；Profile 经 `SNAPSHOT_NUM` 锁定；build root base、build.conf、脚本分支实测**无法设定**，改为提交后逐项读回（base 标识、build.conf digest、脚本版本），A/B 两侧任一不等 → `base_mismatch`、`comparison = unverifiable`、不作为阈值 gate 输入、进 incomplete（environment_gap）；`BUILD_NOTES` 写入 Run 标记用于归属；Recent Builds 只显示 10 条、记录保留 30 天、产物保留 10 个、RBS 保留 7 天，故证据完成即归档；并发上限未知，客户端自设配额；"干净应用"定义为零 fuzz、零偏移 | Codex 指出的"同批 ≠ 可比"成立；实测证明部分输入锁不住，读回比对是唯一可验证的做法 |
| M7 | BenchPolicy 在样本功效不足时放行回归；SPEC 混用相对与绝对量；回归符号未统一；BCa 退化分支未定义 | CC H22-06（认领本方上一轮缺省值）、Codex H-07 | **合并**：取 CC 的非劣形式——`regression_pct` = 各指标退化方向 95% 区间上界的最大值、下限 0，样本少则区间宽、自然判不过；SPEC 每条标明绝对或相对。取 Codex 的符号约定（退化为正，按指标方向换算）与 BCa 退化处理（全同值或样本不足 → 不可计算 → `validation_complete = false`、不得作 gate 输入） | 原"显著才算回归"在样本少时放行，方向错误；改为上界判定后功效不足只会多拦、不会漏放 |
| M8 | 优化候选的判定状态靠 Agent 自律；修复段叠在优化段之上后判据失效；`max_opt_rounds` 与实际撤销所需路由次数不相容 | Codex H-08、H-09，CC H22-03 | **合并**：OptimizationPlan 由框架持有生命周期 pending_validation → accepted / rejected_reverting → reverted；series 段带 `purpose ∈ {candidate, repair, revert}`，判定按 plan 追溯整条段链而非只看顶段；撤销由框架确定性生成；轮次按 plan 计数；环容量见 M1；UT 失败按段归因到 plan | 两家各覆盖了一半时间线（Codex：撤销预算；CC：修复叠加），合并后覆盖完整 |
| M9 | 目标范围在 Run 创建时定格，但此时还没有 patch；AI 修复改到的范围外模块不被验证；显式 suites 可绕过"改动模块不可缩小" | Codex H-10、H-11，CC H22-04 | **范围增长取 CC**：首次 `submit_patch` 受理事务内确定初始范围；之后每次 series 推进按全部段所涉包重算并取并集（只增不减）；未登记模块拒绝。**取 Codex**：确定时点写明（input: none 在 pin 事务内）；规定最低套件集合（范围内必测套件 + `always_run`），显式 suites 只能增加或选登记的等效替代；反向依赖模块首屏提示 | **未采用 Codex 的"拒绝范围外候选"**：会让 AI 修复在跨模块问题上直接失败、需人工重建 Run；范围增长同样保证"改了的必须验证"，且保留自动化 |
| M10 | Profile 策略 v2 的函数校验和依赖伪探针类编译选项，未列入构建输入闭包；开启条件"差异不显著"不能证明损失可接受 | Codex H-12、CC H22-16 | **合并**：策略 v2 增前置条件 0——伪探针选项列入构建输入闭包，缺失则不得启用；开启条件改为非劣证明：预先固定评估集合与 ε（缺省 1 个百分点，负责人确认），"复用收益 − 重采收益"95% 区间下界高于 −ε 才可开启，否则 `inconclusive`、保持 v1 | 保留负责人"小改动不必重采"的原意，只把开启证据换成能证明损失可控的形式 |
| M11 | AI patch 可以改测试用例、`%check`、告警选项、仓内基准脚本，"测试结果不能造假"的前提不成立 | CC H22-05 | **采用 CC**：ModuleRegistry 登记 `protected_paths`；AI 段触及即生成 `verification_asset_change` 条目，审批时逐条确认；对比报告单列 | 负责人原则"测试结果不能造假"由此变成可检查的机制 |
| M12 | D22 的"独立构建主机"形态不是一次性的，root scriptlet 可跨构建持久化 | CC H22-07 | **采用 CC**：两种形态统一为"不可变基底 + 每次构建一次性可写层"，基底 digest 进 manifest，构建后复位并校验 | — |
| M13 | ClineSR CLI 改为专用 UID 后，worker 无法 killpg；超时、心跳自杀、孤儿回收全部失效 | CC H22-08 | **采用 CC**：CLI 经特权 launcher 启动，置于独立 cgroup v2，worker 经 launcher 接口 kill；E0 增 cgroup v2 预检 | — |

## MINOR / NIT

| # | 问题 | 来源 | 处置 |
|---|------|------|------|
| N1 | 勘误 E-02 未列全偏离冻结语义之处；§4.2.4 与 §4.3.4 措辞矛盾 | CC H22-09 | 采用。E-02 增偏离清单（paused 成因、计时、到期、wake 在 running 下不迁移、`sys.superseded`），§4.2.4 措辞对齐 |
| N2 | 多版本对比报告缺生成时点与 digest 绑定 | CC H22-13 | 采用。框架在 ci_plan 完成事务内生成，digest 写入 `ReleaseManifest.release_evidence`，审批 CAS 核对 |
| N3 | E-03 细节：镜像 blob 写入方、远程构建标记来源、租约主动释放语义 | CC H22-14 | 采用，§8.5 逐条写明 |
| N4 | `sys.baseline_build` 的归属、预算、取消语义未定义 | CC H22-15 | 采用。由框架内部 Run 持有，独立预算，single-flight 共享，请求方取消只解除订阅 |
| N5 | 四份示例中两份无原文；01 附录 A4 与 v2.2 规则冲突 | Codex H-14、CC H22-17 | 采用。§4.2.1 增示例三、四原文（按 mode、含镜像节点）；01 A4 在 01 切换上游时以示例四替换（附录 B 第 7 组） |
| N6 | 附录 B 第 7 组漏收 v2.2 新增项，且规则③定义自相矛盾 | Codex H-15、CC H22-18 | 采用，补齐并修正 |
| N7 | v2.2 新增项没有落到 §13 分期 | CC H22-19 | 采用。P2/P4/P7 补入 |
| N8 | 板子失败归因在"单 Run 持板上限 1 + 分派前授予"下不可达 | CC H22-20 | 采用。刷机失败重试时带 `exclude_boards`，使"同镜像 ≥2 块板失败"可达 |
| N9 | AI 采纳记录不能直接得出准确率与误报率 | Codex H-13 | 采用。分开定义采纳率与准确率，后者须有事后确认的真值 |
| N10 | 编号与措辞（R25 插序等） | Kimi N-02、CC H22-21 | 采用，R25 移至 R24 之后 |

---

## 同步项（不计入 01 结论；HLD 三方 GO 后随 01 一次性同步）

两家共列 14 条（Codex S-01～S-04，CC S-01～S-10），与 HLD 附录 B 第 7 组逐条核对：13 条已在册；**补登 1 条**：§4.3.5 放行谓词进入核心迁移表（C-16 terminal_success、§2.5 审批 CAS 含 `acknowledged_gaps` 与"通过"谓词、核销前复核；publishing 后不改 C-10/C-11 映射与 release_outcome 两值）。CC S-05 指出的 01 A4 与 CF-FIX-00 注册集问题，按 N5 处理。

---

## 负责人裁定

**超时后重试成功，能否发布？** Codex 主张出现过超时（包括重试成功）就不得发布；Claude Code 主张重试成功即真实通过、首屏显示即可。负责人裁定：**可以发布，但必须在人工审批时告知审批人**——每条 retried 记录（超时位置、超时时长、重试次数、最终通过的报告）在审批 CLI 首屏逐条呈现，审批人确认后才可提交批准；审批人不认可即拒绝、不发布。非发布路径的结论为 `succeeded_with_gaps`，同样列出 retried。v2.3 已按此修改 §4.3.5、§8.2、§11.3、A20 与附录 B 第 7 组。

## 下一轮建议

本轮无 BLOCKER，Kimi GO，两家 NO-GO 的 MAJOR 均为机制补齐，已全部落地。建议**再审一轮**，范围收窄为：v2.3 改动部分（A20 所列）+ 组合场景走查（并行 + 超时 + 范围增长 + 优化撤销同时发生）+ Quickbuild 实测结论的落地是否准确。
