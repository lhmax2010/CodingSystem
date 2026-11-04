# HLD v2.6（第六轮定向核对）+ 01_Contract_Spec v0.16（第十六轮定向复审）— Claude Code

**评审方**：Claude Code　**日期**：2026-11-04
**对象**：docs/00_Framework_HLD_v2.6.md（仅附录 A23 所列改动）；docs/01_Contract_Spec_v0.16.md（仅 A3 中 v0.16 一条所列改动）
**输入**：HEAD `185d7fefa91e31609d41351d2f23f9466e7850f6`；HLD v2.6 sha256 `dd79de5258b76a2ee25f46d9874eeb740b88a0be37305547986cb80a87acffc5`；01 v0.16 sha256 `00747399a6df2e8ddf4d6ca846f3dfe9e6cb1f326a6d35982909d7479b75f78a`。另读两份上一轮处置表、上一轮三家原始意见、docs/research/quickbuild_business_logic.md（只读）。方法：v2.5→v2.6、v0.15→v0.16 全量 diff，再沿直接关联条款走查；四份示例按原文路由手工演算。未访问或探测 Quickbuild，未读本轮其他评审方意见，未修改被审文档。

## 结论表

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.6（A23） | **GO** | 0 | 0 | 2 | 3 |
| 第二部分：01 v0.16（A3 v0.16） | **NO-GO** | 0 | 1 | 2 | 1 |
| 同步项（不计入第二部分） | — | 0 | 0 | 0 | 0 |

第二部分唯一的 MAJOR（C16-01）：崩溃（lapsed）路径上没有"失联触发者"，毒丸任务与同实例上的无辜任务每轮各计一次中断，而且回收后两者被同一事件同时恢复、再次同处执行阶段——无辜任务与毒丸任务同步到达 `max_task_interrupts`，一起落入 manual_only。v0.16 自己给出的"缺省 3 高于 2 以容纳无辜任务"只在退役（retiring）路径上成立。安全性不受影响（无双重执行），受损的是跨 Run 隔离：别人的坏计划让本 Run 的已核销发布只能人工收尾。

## 负责人七项裁决判断表

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | **成立** | 本版未触及汇合、超时显式化与 retried 确认范围；示例一 `pre_final_review` 汇合与规则①③的汇合必经未变。代价不变：两路报告与超时 / 替代历史都须保留。 |
| ② | Quickbuild 默认取最新，Run 启动时解析固定（取最新 Profile 快照） | **成立**（上一轮"有条件成立"的条件已满足） | §7.6.1 已按证据重写：推广状态按证据显示三种取值、不固定标"未推广"；失败率改标"设计推断"；补写 Profile 与构建根两条输入链的版本差距（Q4：Oct-28 / Oct-13）及失败时附两者编号。与实测记录一致（`build-1213816.log:309–345`、研究记录"Profile 与 base 是两条输入链"）。残余只有措辞：把"构建根仍由 reference 决定"从样本配置推广成一般结论（H26-05，NIT）。代价如实可见：所选快照越新，与 reference 构建根的差距越大，环境性构建失败会落到 AI 修复环或（未决计划期间）直接导致候选被撤销。 |
| ③ | Profile v1 严格匹配 + v2 小改动复用预案 | **成立** | 本版未改。v2 仍缺省关闭，须真实工具链数据评估后才能开启。 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | 本版的 purpose 互斥判定不缩小验证范围；撤销后范围只增不减保留。代价不变。 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | purpose 改为编排按互斥顺序推导，AI 自报与"未决计划期间偷偷做 AI 修复"两条绕过均已堵上（核对见 B1）。新增代价应当写明：未决计划期间任何构建 / 镜像 / UT 失败——包括与候选无关的环境性失败（如裁决②带来的构建根差距）——都会让候选被确定性撤销，换来可判定性，而非尝试修复。属可接受的保守取舍。残留的旧测试用例与新规则矛盾（H26-01）。 |
| ⑥ | Quickbuild 可加 Base CL，否则默认最新；显式 base 读回核对 | **成立** | 能力检查按实际所需能力判定，误拒面收窄；无法确定按需要 A/B 处理（fail-closed），不产生误放。`suites: auto` 时实际上总是"无法确定"（H26-04，NIT）。当前 Quickbuild 的产镜像能力仍为 unverified，此放宽暂无受益配置，属面向未来。 |
| ⑦ | 超时后重试成功可发布，须审批人确认 | **成立** | 本版未改；当前 series 证据链范围、(id, digest) 确认与核销复核保留。 |

---

## A. 处置落实

### HLD v2.5 处置表（R1–R4）

| 条目 | 正文落点 | 结论 |
|---|---|---|
| R1 purpose 互斥四步 | §7A.4 L743：①revert（只匹配当前未决计划）②拒绝 `E-CANDIDATE-NOT-REVERT` ③candidate + 准入 ④repair / initial；"因此待验证计划期间不存在修复段" | 落实。但删掉"后续修复段归属该计划"后，§7A.4 撤销条与 §11.3 v2.3 用例仍以"候选之后叠加的修复段"为前提（H26-01） |
| R2 能力检查按实际所需 | §4.2.6 L457：A/B 类判定清单、absolute-only 非发布 gate 豁免、无法确定按 A/B、路径语义、LocalGbsBackend 三项 verified | 落实（H26-04 为措辞） |
| R3 "最新"代价按证据 | §7.6.1 L628 推广状态三值、设计推断、构建根差距、失败附两编号；L639 审批呈现 | 落实（H26-05 为措辞） |
| R4 terminal 兜底 | §4.2.6③ L453 `pending_plan_at_terminal`；§7A.4 L745 | 落实。但兜底所举触发例（base_mismatch 路由到 terminal）过不了规则③的加载检查，真正可达的触发是 campaign 在未决计划下返回 no_gain_found（H26-02；含对本方上一轮 H25-03 的更正） |

**部分采纳（未采用"判为环境性失败即自动停止 AI 修复"）——理由成立。** 本方上一轮提出 `env_skew_suspected` 时自己就写了判据"待 P6 以真实数据确定"。没有可确定的判据时，自动停止修复是一个无定义的判断，会引入新的不确定出口。首期只附 Profile 与构建根两个编号作为证据、交给 LogAnalyzer 与审批人，同时为 P6 积累数据，这是正确的先后次序。撤回该子建议。

### 01 v0.15 处置表（V1–V5）

| 条目 | 正文落点 | 结论 |
|---|---|---|
| V1 manual_only 人工出口 | L160 C-11 行、L185、L598 特权运维 guard；CF-AUTH-20j | 落实。manual_only 下的"只读强制 probe"在 recovery_state ≠ indeterminate 时没有合法载体（C16-02） |
| V2 定时器代次 | L184：(phase_generation, owner_epoch, phase, deadline)、CAS 一次、同事务解除同实例定时器、owner 非 live 即失效、launcher 幂等；L304 模型字段；CF-AUTH-20h | 落实。`waiting_holder` 无写入 / 清除点（C16-04） |
| V3 interrupt_count + 退避 | L185；CF-AUTH-20g / 20i | 落实了退役路径；崩溃路径上无辜任务不可区分（C16-01）；核销前崩溃不计数、退避阈值与中断上限无约束（C16-03） |
| V4 夹具预期统一 | CF-AUTH-20、CF-IPC-10 已按 execute（未核销 / 已核销）与 probe 分写 | 落实 |
| V5 cgroup 委派 | L183 部署契约；CF-IPC-03 断言迁出 EACCES | 落实。跨实例迁移（E1 后代迁入 E2 子树，否则会让 E1 假静默）在 cgroup v2 下同样需要对共同祖先 `cgroup.procs` 的写权限，与"迁出到父 cgroup"是同一判据，CF-IPC-03 已能覆盖；不另报 |

---

## B. 第一部分：HLD v2.6（A23）核对

### B1. purpose 四步互斥判定的路径演算

以示例一（per_patch）、示例二（campaign）原文路由为准；P 为当前计划。

| # | 路径 | 提交 / 计划状态 | 命中 | 结果 | 出口 |
|---|---|---|---|---|---|
| 1 | 开发者 submit_patch | 无计划 | initial | 正常 | 唯一 |
| 2 | 无计划时 compile_rpm 修复 | 无 | ④ repair | 正常 | 唯一 |
| 3 | optimize 提交候选，环容量足 | 无 | ③ candidate | 建 P(pending_validation) | 唯一 |
| 4 | optimize 提交候选，容量不足 | 无 | ③ 准入拒绝 | `E-PLAN-NO-CAPACITY` → no_further_gain / no_gain_found | 唯一 |
| 5 | P 待验证，compile_rpm / compile_image / ut 失败，提交回到 parent_tree 的段 | pending_validation ∧ 失败节点在重验证路径上 | ① revert | P→reverted，不准入、不计轮 | 唯一 |
| 6 | 同 5，但提交非撤销段（AI 修复） | 同上 | ② 拒绝 | `E-CANDIDATE-NOT-REVERT` | 唯一，但 Agent 的后续动作未写明（H26-03） |
| 7 | Bench 判 neutral / loss / inconclusive → optimize 亲自撤销 | rejected_reverting | ① revert（不论提交者） | P→reverted；max_opt_rounds 已到顶也成功 | 唯一（上一轮 Codex H25-01 的重叠已消除） |
| 8 | rejected_reverting 时 optimize 提交新候选 | rejected_reverting | ② 拒绝 | `E-CANDIDATE-NOT-REVERT` | 唯一 |
| 9 | rejected_reverting 时 optimize 返回 no_further_gain | — | 不经 purpose | sys.invalid_result（v2.3 用例） | 唯一 |
| 10 | rejected_reverting 时 campaign 返回 no_gain_found | — | 不经 purpose | 无 invalid_result 规则 → report_no_gain（terminal）→ `pending_plan_at_terminal` → fail_safe | 唯一，但归因错位（H26-02） |
| 11 | 树碰巧等于历史已结束计划的 parent_tree | 无未决 | ③ / ④ | 不认作撤销 | 唯一 |
| 12 | Bench 判 gain | accepted | — | 之后提交按 ③ / ④ | 唯一 |
| 13 | P 待验证，镜像 base_mismatch | pending_validation | 不产段 | image_failed_exhausted → fail_safe，P 记 abandoned | 唯一 |

结论：四步之间没有重叠，也没有路径遗漏（上一轮的两条双出口——撤销被当候选、待验证期间接受 AI 修复——均已消除）。剩下的是删除"修复段归属该计划"后留下的文字与测试残留（H26-01），以及第 6、10 两行的处理细节（H26-03、H26-02）。

### B2. pending_plan_at_terminal 与 release、no_gain_found 的关系

- **release 路径**：未决计划存在时审批决定被拒，release 节点不可达，兜底只作用于 terminal。两者不冲突。
- **campaign 正常 no_gain_found**：候选均已撤销（P 已 reverted）后返回，此时无未决计划，report_no_gain 以 succeeded 关闭。不冲突。
- **兜底的实际触发面**：见 H26-02。A23 与 §7A.4 所举的"base_mismatch 等失败经路由到达 terminal"在合法流水线中不可达——这种边在 G' 内绕过 UT / Benchmark，规则③拒绝加载。真正可达的是 B1 第 10 行。

### B3. 后端能力加载期检查

- **四份示例**：全部 `backend: local`，LocalGbsBackend 三项能力声明为 verified，不误拒。示例一、四的 `bench_gate` 用 `regression_pct`（A/B 类），即使改配 Quickbuild 也应拒绝——判定正确。
- **能否确定**：判定输入为"固定的 SuiteVersion / BenchPolicy 与字段注册元数据"。四份示例都用 `suites: auto`，套件按 Run 的目标范围选取，且范围在 Run 内只增不减。加载期这项判定永远"无法确定"，按规则当作需要 A/B。这是 fail-closed，不会误放，但应写明（H26-04）。
- **误放**：即使加载期按显式套件判为 absolute-only，运行时套件版本或范围变化引入 relative SPEC，`comparison = unverifiable` 时比较字段缺失、gate fail-closed，不会误判通过。
- 当前 Quickbuild 的 `build_image` 为 unverified，任何 Quickbuild 镜像节点仍会被拒；这项放宽暂无受益配置。

### B4. "最新 Profile 快照"代价说明与实测记录对照

| 正文（§7.6.1 L628） | 实测记录 | 一致性 |
|---|---|---|
| 缺省 `BUILD_REFERENCE=Ref. Snapshot` | 历史表单缺省、reference 为滚动入口（研究记录 L112） | 一致 |
| Profile 与构建根两条输入链，样本 Oct-28 / Oct-13 | 研究记录 L54、L91、L113（`build-1213816.log:311`） | 一致 |
| "构建根仍由 reference 决定" | 研究记录 L65 / L72："独立固定构建根 base 和 build.conf 的可写提交字段未知"；L46："Live/Partial 的所有默认规则……不能由此外推" | 样本层面一致；一般化表述过头（H26-05） |
| 推广状态按证据显示，不凭时间先后宣称 | 研究记录无"按快照号读取推广状态"的已证实接口 | 一致（无证据时显示"推广状态未验证"） |
| 失败率高为设计推断 | 研究记录无失败率数据 | 一致 |

### 第一部分问题

#### H26-01 [MINOR] 删去"修复段归属该计划"后的文字与测试残留

- **位置**：§7A.4 撤销条（L745）；§11.3 v2.3 追加的"优化计划"用例组（L879）。
- **依据**：
  - L743 新规则："② **拒绝**——存在未决计划而提交不满足 ①（含 Compiler / UT 的非撤销段……）→ `E-CANDIDATE-NOT-REVERT`……因此待验证计划期间不存在修复段"。
  - L745 仍写："series 以新段（purpose = revert）回到 `plan.parent_tree`，**包含该候选之后叠加的修复段**"。
  - L879（v2.3 用例）仍写："**优化→RPM 修复→父版本退化仍撤销；优化→修复→UT 失败撤销整条候选链**"。
- **问题**：
  - 按新规则，"优化→RPM 修复"这一步本身就会被 ② 拒绝，两个 v2.3 用例的前置条件不可构造。照原文实现夹具的人会写出与 ② 相反的期望（接受修复段），或得到不可达的测试。
  - 撤销条里"包含……叠加的修复段"会让实现者以为撤销需要回卷多段，误导撤销 patch 的构造与审计呈现。
  - v2.6 用例组已有正确的新用例（"未决计划期间 Compiler 提交非撤销段 → E-CANDIDATE-NOT-REVERT"），与旧用例并存时互相矛盾。
- **候选改动**：

```diff
--- §7A.4 撤销（L745）
- series 以新段（purpose = revert）回到 `plan.parent_tree`，包含该候选之后叠加的修复段；
+ series 以新段（purpose = revert）回到 `plan.parent_tree`（未决计划期间不接受修复段，撤销段即候选段的逆变更；v2.6）；
--- §11.3 v2.3 追加·优化计划（L879）
- **优化计划**（优化→RPM 修复→父版本退化仍撤销；优化→修复→UT 失败撤销整条候选链；neutral→撤销→重验只撤销一次；
+ **优化计划**（优化→RPM 失败→只允许确定性撤销、AI 修复段被拒（v2.6 替换原"优化→RPM 修复→父版本退化仍撤销"）；优化→UT 失败→撤销段仅逆转候选段（v2.6 替换原"撤销整条候选链"）；neutral→撤销→重验只撤销一次；
```

- **副作用**：无语义变化；只是让旧文与 R1 一致。A20 的历史摘要（"修复段归属计划"）属变更记录，保留不改。
- **配套测试 / 夹具**：删除两个旧用例；新增断言"撤销段 diff == 候选段 diff 的逆"；validator 侧检查 §11.3 用例清单不含"未决计划期间的修复段"前置条件。

#### H26-02 [MINOR] terminal 兜底的实际触发是 campaign 违规返回 no_gain_found，归因落在 terminal 而非 Optimization

- **位置**：§4.2.6③ 运行时兜底（L453）；§7A.4 base_mismatch 优先（L745）；示例二路由（`optimize --no_gain_found--> report_no_gain`）；A23。
- **依据**：
  - L453："terminal 的 success_on 命中时不关闭为 succeeded，而由编排按 fail_safe 保留节点关闭（reason = `pending_plan_at_terminal`，v2.6）……——**避免 base_mismatch 等失败经路由到达 terminal 时无出口**"。
  - 同条规则③："对 G' 中每个可达的 release-approval 型 hitl 或 terminal 节点 t……要求镜像节点、UT 节点、Benchmark 节点都在其中"。
  - v2.3 用例只规定"未决计划时 **no_further_gain** → sys.invalid_result"。
- **问题**：
  1. **所举触发例不可达（含本方更正）**：若存在 `compile_image --image_failed_exhausted--> terminal` 这样的边，它位于 G' 内，并让该 terminal 有一条绕过 UT 与 Benchmark 的路径，规则③在加载期就会拒绝。所以"base_mismatch 路由到 terminal"在合法流水线中不会出现。本方上一轮 H25-03 以此为场景，属判断失误，在此更正。兜底本身仍有价值，但理由要换成可达的路径。
  2. **真正可达的触发**：campaign 在 P 为 rejected_reverting 时返回 no_gain_found（应先撤销）。no_gain_found 的 series_effect 为 none，运行时不核对"无净变更"，也没有对应的 invalid_result 规则，于是 Run 经 report_no_gain 走到 terminal，靠兜底以 fail_safe 关闭。结果安全且唯一，但有三处错位：
     - 违规归到 terminal，而不是 Optimization task；
     - 绕过了节点的 retry 策略（本可重试一次后正常撤销）；
     - FeedbackReport 显示"终点有未决计划"，而不是"Optimization 违反撤销义务"。
- **候选改动**：

```diff
--- §7A.4 轮次自限 / status 集
+ 存在未决计划时，Optimization 返回 opt_patch_ready 以外的任何 status（no_further_gain、no_gain_found）→ sys.invalid_result（v2.6；原只列 no_further_gain）；
+ campaign 的 no_gain_found 运行时核对"series 相对 snapshot 无净变更"，不成立 → sys.invalid_result。
--- §4.2.6③ 运行时兜底
- ——避免 base_mismatch 等失败经路由到达 terminal 时无出口。
+ ——作为纵深防御：合法流水线中 terminal 只能在 Benchmark 之后到达（规则③），兜底覆盖 Agent 违规与未来新增 status 的遗漏；base_mismatch 一类绕过 UT / Benchmark 的终点路由由规则③在加载期拒绝。
```

- **副作用**：违规改由 sys.invalid_result 承载，按节点 retry 策略可重试，否则路由 fail_safe——终局相同，归因更准。兜底保留，不减少安全性。
- **配套测试 / 夹具**：
  - 示例二变体：P 为 rejected_reverting 时 FakeOptimizer 返回 no_gain_found → sys.invalid_result（非 pending_plan_at_terminal）；
  - 同上配 `retry: [sys.invalid_result]` → 重试后正常撤销；
  - validator 反例：`image_failed_exhausted → terminal` 的优化流水线被规则③拒绝；
  - 兜底单测保留：直接构造"未决计划 + terminal success_on"仍为 `closed(fail_safe, pending_plan_at_terminal)`。

#### H26-03 [NIT] `E-CANDIDATE-NOT-REVERT` 之后 Agent 的义务未写明

- **位置**：§7A.4 L743 ②；对照 L747 的 `E-PLAN-NO-CAPACITY`。
- **依据**：L747："候选提交被 `E-PLAN-NO-CAPACITY` 拒绝时 Agent 从响应得知原因并返回无进一步收益"；② 只写"→ `E-CANDIDATE-NOT-REVERT`"。
- **问题**：Compiler / UT 在未决计划期间提交了 AI 修复段被拒之后，没有写明是"在同一 task 内改交确定性撤销"还是"task 以 sys.invalid_result 结束"。两种实现都可能出现，后者会把一次可恢复的 Agent 失误变成 fail_safe。
- **候选改动**：

```diff
- ② **拒绝**——……→ `E-CANDIDATE-NOT-REVERT`（未决计划期间只允许确定性撤销）；
+ ② **拒绝**——……→ `E-CANDIDATE-NOT-REVERT`（未决计划期间只允许确定性撤销）；响应携带 plan_id 与 parent_tree，Agent 须在同一 task 内改交回到 parent_tree 的撤销段（撤销是确定性的，SDK 提供 `make_revert(plan_id)` 生成）；task 以其他 status 结束 → sys.invalid_result；
```

- **副作用**：SDK 多一个确定性辅助函数；不改变计划状态机。
- **配套测试 / 夹具**：FakeCompiler 先交 AI 修复段被拒、再交撤销段 → revert 且只消耗一次环计数；不改交直接结束 → sys.invalid_result。

#### H26-04 [NIT] absolute-only 判定在 `suites: auto` 下恒为"无法确定"，应明写

- **位置**：§4.2.6 L457。
- **依据**："指标依赖类型由固定的 SuiteVersion / BenchPolicy 与字段注册元数据解析，无法确定为 absolute-only 时按需要 A/B 处理"；示例一、二、四均为 `suites: auto`（按 Run 目标范围选套件，§7A.7）。
- **问题**：auto 套件取决于运行时的目标范围，且范围只增不减，加载期无从"固定"。按规则一律当作需要 A/B——结论正确（fail-closed），但读者容易以为 auto 套件也能享受豁免，误以为配错了后端。
- **候选改动**：

```diff
+ 套件为 `auto` 或未锁定版本时，加载期无法确定，按需要 A/B 处理；豁免只适用于显式列出且版本锁定、全部 SPEC 为 absolute 的套件。运行时范围增长引入的 relative SPEC 由 comparison 字段 fail-closed 兜底。
```

- **副作用**：无。
- **配套测试 / 夹具**：Quickbuild（source_input / build_image verified、comparison unverified）× `suites: auto` + absolute 指标 gate → 拒绝加载；同配置改为显式锁定的 absolute 套件 → 加载通过。

#### H26-05 [NIT] §7.6.1 审批呈现字段重复；构建根结论超出样本

- **位置**：§7.6.1 L628、L639。
- **依据**：
  - L639："读回的构建根快照编号、显式覆盖的包版本、读回的构建根 base 快照编号"——同一字段列了两次。
  - L628："构建根仍由 reference 决定（调查 Q4……）"。研究记录 L65："独立固定构建根 base 和 build.conf 的可写提交字段未知"；L46："Live/Partial 的所有默认规则及 CL 机制不能由此外推"。
- **问题**：重复字段会让 ReleaseManifest schema 出现两个同义字段。构建根的表述把一个配置的样本写成一般结论，与"按证据标等级"的写法不一致。
- **候选改动**：

```diff
- 读回的构建根快照编号、显式覆盖的包版本、读回的构建根 base 快照编号、解析时刻
+ 读回的构建根快照编号、显式覆盖的包版本、解析时刻
- 另一代价：构建根仍由 reference 决定（调查 Q4：……）
+ 另一代价：在已调查配置（Tizen Base RBS 样本）中构建根取自 reference，能否在提交时独立固定为 `unverified`（调查 Q4：……）
```

- **副作用**：无。
- **配套测试 / 夹具**：ReleaseManifest schema golden 去掉重复字段。

---

## D. 第二部分：01 v0.16 核对

### D1. 定时器代次与计数分工

- **到期 CAS 一次**：每代只消费一次，重启重放与重复扫描不计数。
- **同实例定时器解除**：同事务解除 → 同实例两个 task 同时到期时只有先提交者计 loss，另一个因 `timer_armed = false` 不再触发，回收时按执行阶段计 interrupt。同一故障对每个 task 恰计一次。
- **owner 非 live 即失效**：覆盖了 lapsed 路径——崩溃实例上没有解除事务，但定时器因 owner 不再 live 而失效。
- **新阶段 generation +1**：防 ABA。
- **退役路径**：触发者 A 计 loss、无辜者 B 计 interrupt，分工成立。毒丸挂起型（不崩溃、只是不回结果）→ 每轮 A 计 loss，2 轮耗尽；B 至多 2 次 interrupt < 3。"3 高于 2"的设计在这条路径上成立。
- **崩溃路径**：没有触发者，分工失效（C16-01）。

### D2. 五条时间线 × 崩溃点 × 期限 × 上限 × 毒丸

记号：E1 为原实例，E2 为新实例；"✓"表示恰一个出口。

| 时间线 | 崩溃 / 注入点 | 期限到期 | 计数到上限 | 出口 | 判定 |
|---|---|---|---|---|---|
| 1 正常 | intent 前 / 后、受理后 ACK 前、ACK 后落账前 | — | — | receipt 规则 (a)/(b) 唯一送达 → granted → outcome | ✓ |
| 1 | — | awaiting_consume 到期（E1 活但不核销） | loss<2 | E1 retiring → 未核销立即替代重派到 E2 | ✓ |
| 1 | — | 同上 | loss=2 | 撤销授权 + release_failed(dispatch_loss_exhausted) | ✓ |
| 1 | E1 在核销前崩溃（payload 令 broker 崩溃） | 定时器因 owner 非 live 失效 | **不计数** | 立即重派 E2 → 再崩溃 → ……仅由 launcher 退避止住 | **C16-03** |
| 2 核销后发生前 | E1 崩溃（lapsed） | 失效 | interrupt<3 | 等 E1 reclaimed → E2 resumed → 对账 not_happened → proceed → 执行 | ✓ |
| 2 | 同上，毒丸 P 与无辜 B 同处执行阶段 | 失效 | P、B 同步 +1 | 同时恢复、同时再处执行阶段，第 3 次两者都 manual_only | **C16-01** |
| 2 | — | awaiting_outcome 到期 | loss<2 | 计 loss（触发者），同实例执行阶段者计 interrupt | ✓ |
| 2 | 计数耗尽 | — | manual_only（recovery_state = none / execution_permitted） | 只经人工；强制 probe 无合法载体 | **C16-02** |
| 3 发生后 | ACK 前 / 后崩溃 | 失效 | <上限 | E2 resumed → 对账 happened → released 映射 | ✓ |
| 3 | 同上 | — | 达上限 | manual_only → 人工；远端已发生应只允许 confirm_released，但 probe 载体同 C16-02 | ✓ / C16-02 |
| 4 indeterminate | 任意 | awaiting_probe 不触发 retiring | 不计 interrupt（非执行阶段） | 周期 probe → happened / not_happened（持有者静默）/ retire_requested 后重探 | ✓ |
| 4 | manual_only ∧ indeterminate | — | — | probe 合法（indeterminate）；C-11a"不越过人工"只在正文、不在 C-11a 行 | ✓ / C16-04 |
| 5 实例活、单任务失联 | A 到期 | CAS 一次 | A loss+1，B interrupt+1，C（未核销）立即重派 | E1 回收后 B 重派才武装新期限；只拉起一个替换实例 | ✓ |
| 5 | A 同一到期事件重复 / 重启重放 / ABA | CAS 失败 | 不重复 | — | ✓ |
| 5 | E1 子树长期不空 | B 不计时（owner 非 live） | — | B 不重派、告警（R13）；未核销与其他实例不受影响 | ✓ |

**重点检查结论**：
- **重复计数**：没有。同一事件对同一 task 至多计一次（CAS + 解除 + 触发者排除）。
- **连累无辜**：退役路径不会；崩溃路径会（C16-01）。
- **manual_only 后的自动执行**：正文排除了 C-09 / execute 派发，持有者实例此时已 retiring / lapsed，C-10 / C-10a 被连接守卫拒绝；不存在自动执行发布的路径。C-09 行与 ④ guard 的表格未体现 manual_only（C16-04，属一致性）。
- **人工裁决与远端事实相反**：probe 明确全部发生 / 全部未发生时已受约束。部分出现按 §2.2a 只能报 indeterminate，系统本身不知道确定事实，交由人工按证据裁决，符合冻结语义。真正的缺口是 recovery_state ≠ indeterminate 时 probe 发不出去（C16-02）：此时退化为"unknown → 证据规则"，人工仍可在远端其实已发生时选 confirm_not_released。

### 第二部分问题

#### C16-01 [MAJOR] 崩溃路径上毒丸任务与无辜任务计数相同且被同步恢复，无辜任务随毒丸一起落入 manual_only

- **位置**：01 v0.16 §2.2d"失联与中断次数上界"（L185）；CF-AUTH-20g / 20h（L803–804）。
- **依据**：
  - L185："`interrupt_count`——实例因 lapsed 或 retiring 被回收时，该实例上处于执行可能阶段（awaiting_outcome 或 awaiting_reconcile）、**且不是本次失联触发者**的每个 task（覆盖'每次执行都令 broker 崩溃'的毒丸任务，它走 lapsed 路径……）"；"`max_task_interrupts`（缺省 3，**高于前者以容纳同实例无辜 task 的连带中断**）"。
  - 处置表 V3："触发者计 loss、连带者计 interrupt，两种计数互不重复"。
  - CF-AUTH-20h："无辜 task 被连带中断两次后仍能正常完成"。
- **问题**：
  1. lapsed 路径（broker 崩溃）没有"失联触发者"，毒丸 P 与同处执行阶段的无辜 B 每轮都各 +1，计数上不可区分。
  2. 更关键的是两者会被**同步**：E1 崩溃后，P、B 都是已核销任务，都等 E1 reclaimed，在同一回收事务后同时重派到 E2，同时 resumed → 对账 → proceed。P 一执行就让 E2 崩溃，而 B 此时多半还处在 awaiting_reconcile / awaiting_outcome，于是再 +1。第一次被连带后，后续每一轮 B 都高度可能被连带，这不是偶发。
  3. 结果：第 3 次崩溃时 P 与 B 同时到达 `max_task_interrupts = 3`，B 置 manual_only，只能人工收尾。若 probe 显示未发生，只能 confirm_not_released，B 的 Run 以 release_failed 关闭——一个 Run 的坏计划让另一个已审批 Run 的发布失败。
  4. "3 高于 2"只在退役路径（有触发者 A 计 loss）上成立；在 V3 本来要覆盖的崩溃路径上无效。CF-AUTH-20h 只测到"两次"，恰好没有覆盖这一点。
- **安全性**：不受影响。没有双重执行，也不会伪造远端事实；问题在于跨 Run 隔离与可用性，以及正文所声明的性质不成立。
- **候选改动（嫌疑隔离重派）**：

```diff
--- 01 §2.2d 失联与中断次数上界
- `interrupt_count`——实例因 lapsed 或 retiring 被回收时，该实例上处于执行可能阶段（awaiting_outcome 或 awaiting_reconcile）、且不是本次失联触发者的每个 task（……）。
+ `interrupt_count`——实例因 lapsed 或 retiring 被回收时，该实例上处于执行可能阶段（awaiting_outcome 或 awaiting_reconcile）、且不是本次失联触发者的 task 集合记为嫌疑集 S（同回收事务持久化 `suspect_set_id`）：
+   · |S| = 1 → 该 task interrupt_count +1；
+   · |S| ≥ 2 → 不计数，S 内已核销 task 进入**隔离重派**（`recovery_mode = isolating`）：按 (consumed_at, task_id) 确定序，任一时刻每个实例上至多一个 S 内 task 处于执行可能阶段，其余保持等待、定时器不武装；隔离中的单个 task 所在实例被回收时，只对它 +1（|S'| = 1）；它终结或达到上限后，下一个进入执行。S 内全部终结后恢复常规并发。
+ 隔离序与 isolating 状态持久化，编排重启后按序继续；不在 S 内的新派发不受影响。
- `max_task_interrupts`（缺省 3，高于前者以容纳同实例无辜 task 的连带中断）
+ `max_task_interrupts`（缺省 3）；无辜 task 至多因"首次未隔离的崩溃"不计数，随后在隔离中单独执行，不再被连带
```

- **副作用**：
  - 崩溃之后、同实例上同时恢复的多个发布改为串行，增加的只是事故后的恢复时延；正常路径不受影响。
  - 毒丸到达 manual_only 所需的崩溃次数至多为 1 + max_task_interrupts（第一次不计数）。
  - 新增一个 recovery_mode 取值（破坏性，随 dev 版本号递增），并入 ReleaseTaskState 与 A0。
  - 退役路径不变（触发者计 loss；|S| ≥ 2 时同样隔离，进一步降低无辜任务的 interrupt）。
- **配套测试 / 夹具**：
  - **CF-AUTH-20g 扩充**：P 与 B 同处 E1 执行阶段；FakePublisher 令 P 每次执行都崩溃，B 的对账 + 执行时长大于 P 的崩溃点 → 断言 B 的 interrupt_count ≤ 1 且 B 最终 released；P 在至多 1 + max_task_interrupts 次崩溃后置 manual_only。
  - **CF-AUTH-20k（新）**：隔离序在编排重启前后一致；隔离中 task 的阶段期限到期只计它的 loss；隔离期间新到的未核销 task 照常派发。
  - **CF-AUTH-20h 修订**：把"无辜 task 被连带中断两次后仍能正常完成"改为"无辜 task 与毒丸同实例连续三次崩溃后仍不进入 manual_only"。
  - model-based：随机若干 task、其中 0–2 个为毒丸，断言非毒丸 task 永不进入 manual_only，毒丸 task 均在有界次数内进入 manual_only。

#### C16-02 [MINOR] manual_only 分支的"只读强制 probe"在 recovery_state ≠ indeterminate 时没有合法载体

- **位置**：L598 特权运维 guard；L183–186 §2.2d indeterminate 锁存与重派；CF-IPC-10（L816）；CF-AUTH-20j（L806）。
- **依据**：
  - L598："**manual_only 分支**：裁决前仍先执行只读强制 probe，probe 明确全部发生 → 只允许 `confirm_released`；明确全部未发生 → 只允许 `confirm_not_released`……"。
  - CF-AUTH-20j："manual_only × recovery_state ∈ {none, execution_permitted, reconcile_required} × ……"。
  - §2.2d："对 indeterminate 者……改发出向命令 `release_probe_dispatch`"。
  - CF-IPC-10："probe——**仅已核销且 indeterminate**……未核销 probe 等非法组合被拒"。
- **问题**：
  - manual_only 最常见的来源（C16-01 场景、awaiting_outcome 多次失联）对应的 recovery_state 是 none / execution_permitted / reconcile_required，而唯一的只读探测命令只对 indeterminate 合法。按原文实现，强制 probe 要么被编排拒绝生成，要么实现者私下放宽 CF-IPC-10 的约束。
  - 前者会让 V1 的"裁决受 probe 结果约束"退化为"unknown → 证据规则"：远端其实已全部发生时，人工仍可在静默后选 confirm_not_released，与远端事实相反——这恰是 V1 要堵住的情形。
- **候选改动**：

```diff
--- §2.2d indeterminate 锁存 / §5.1 出向
- 对 indeterminate 者不发可执行的 release_dispatch，改发出向命令 `release_probe_dispatch`
+ 对 indeterminate 者、以及 `recovery_mode = manual_only` 的已核销者（任一 recovery_state），不发可执行的 release_dispatch，改发出向命令 `release_probe_dispatch`
--- C-11a 行 guard
- publishing ∧ recovery_state == indeterminate ∧ ……
+ publishing ∧（recovery_state == indeterminate ∨ recovery_mode == manual_only）∧ ……；manual_only 下 probe 结果只记录为裁决证据、不自动映射终局（"C-11a 自动通道不越过人工要求"写入本行）
--- CF-IPC-10
- probe——仅已核销且 indeterminate
+ probe——仅已核销且（indeterminate ∨ manual_only）
```

- **副作用**：
  - probe 合法域扩大一个已核销子集。broker 侧只读 adapter 与"写调用计数恒为 0"的约束不变，没有新的执行风险。
  - manual_only 的 probe 由持有者以外的当前实例执行。全部未发生时仍须原 holder 静默，规则不变。
- **配套测试 / 夹具**：
  - CF-AUTH-20j 前置改为"probe 确实送达"，并对四种 recovery_state 断言：FakePublisher 写计数为 0；全部发生 → confirm_not_released 被拒。
  - CF-IPC-10 增 "manual_only × recovery_state ∈ {none, execution_permitted, reconcile_required}" 的 probe 合法组。
  - 非 manual_only、非 indeterminate 的 probe 仍被拒。

#### C16-03 [MINOR] 核销前崩溃的毒丸不计数；launcher 退避阈值与中断上限没有约束关系

- **位置**：L185"失联与中断次数上界"及"launcher 拉起退避"；CF-AUTH-20i。
- **依据**：
  - interrupt 只计"awaiting_outcome 或 awaiting_reconcile"。
  - "连续 N 次（配置）在时间窗 T 内 lapsed → 停止自动拉起并告警……（防止与 task 无关的启动即崩溃耗尽资源）"。
- **问题**：
  1. **核销前崩溃不计数**：若 ReleaseDispatch 载荷或 plan 校验在 consume 之前就让 broker 崩溃，task 处于 awaiting_consume，lapsed 路径不计任何数；未核销者又是"立即重派、不等静默"，于是 E2 一收到派发即崩溃，循环只能由 launcher 退避止住。止住时整个 broker 停机，所有发布受阻；毒丸 task 未被识别、也未按 dispatch_loss_exhausted 关闭，人工重启后再次进入同一循环。
  2. **退避与上限的关系**：退避计数统计的是任意 lapsed，并不区分"启动即崩溃"与"执行中崩溃"。若配置 N ≤ max_task_interrupts（或配合 C16-01 的 1 + max_task_interrupts），执行期毒丸会先触发全局停机，而不是先进入 manual_only，与"与 task 无关"的设计意图相反。
- **候选改动**：

```diff
--- 失联与中断次数上界
+ 核销前崩溃：实例 lapsed 回收时，其上 awaiting_consume 且 DispatchReceipt 已 completed（已送达）的 task 同样纳入嫌疑集 S（C16-01 的隔离规则同样适用：|S| = 1 时 interrupt_count +1，|S| ≥ 2 时串行单独派发）；未核销者达到 max_task_interrupts → 按 dispatch_loss_exhausted 关闭（授权从未核销，无发布发生）。
--- launcher 拉起退避
- 连续 N 次（配置）在时间窗 T 内 lapsed → 停止自动拉起并告警
+ 退避计数只统计"启动即崩溃"——实例在 hello 后、首个 dispatch 送达前 lapsed（或 hello 前退出）；送达后的 lapsed 归 task 计数处理，不计入退避停机阈值（退避间隔仍按指数增长）。
```

- **副作用**：未核销的无辜 task 与核销前毒丸同实例时，在隔离中只延迟、不被关闭。launcher 需要读取"首个 dispatch 是否已送达"（Ledger 中 DispatchReceipt 的 target_epoch），属只读依赖。
- **配套测试 / 夹具**：
  - CF-AUTH-20g 增"核销前崩溃"变体：FakeBroker 解析某 ReleaseDispatch 即崩溃 → 有界次数后该 task 以 release_failed(dispatch_loss_exhausted) 关闭，其他 task 正常完成，broker 未被退避停机。
  - CF-AUTH-20i 区分两类：启动即崩溃 N 次 → 停机告警；执行期毒丸连续崩溃 → 不停机，先 manual_only。

#### C16-04 [NIT] `waiting_holder` 没有写入 / 清除点；manual_only 只写在正文，未进入 C-09、④、C-11a 的 guard

- **位置**：L184、L304 模型；L157 C-09 行；L173 ④ guard；L161 C-11a 行。
- **依据**：
  - L184："等待旧 holder 静默期间（`recovery_mode = waiting_holder`）不运行执行类阶段期限"——全文只出现在这里和模型里。
  - L185："C-09 与 execute 派发显式排除 manual_only，C-11a 自动通道不越过人工要求"。但 C-09 行的 guard 是"（running ∨ publishing）∧ 连接 epoch == 当前 broker epoch ∧ 实例非 retiring"，④ guard 与 C-11a 行均未提 manual_only。
- **问题**：
  - 定时器的失效实际已由"owner_epoch 对应实例仍 live"承担，`waiting_holder` 成了没有状态迁移的字段，实现者无从知道谁写、何时回到 active。
  - manual_only 的排除只在散文中，按状态表实现的 guard 会漏掉。目前持有者实例已 retiring / lapsed，C-10 / C-10a 会被连接守卫拒绝，所以不构成可利用路径，但表与文不一致。
- **候选改动**：

```diff
+ recovery_mode 迁移：active →（已核销 task 所在实例 retiring / lapsed 的事务）waiting_holder →（持有者更替重派事务）active；任一 →（计数耗尽）manual_only（终止于 C-11 裁决）。
--- C-09 行 guard
- （running ∨ publishing）∧ 连接 epoch == 当前 broker epoch ∧ 实例非 retiring
+ （running ∨ publishing）∧ 连接 epoch == 当前 broker epoch ∧ 实例非 retiring ∧ 对应 task recovery_mode ≠ manual_only
--- ④ guard 同加 recovery_mode ≠ manual_only；C-11a 行加"manual_only 下只记录、不映射"（与 C16-02 合并）
```

- **副作用**：无语义变化，只是表文一致。
- **配套测试 / 夹具**：CF-SM 增 recovery_mode 迁移表断言；manual_only task 的 consume（构造性注入）→ 被拒且 Run 不变。

---

## 同步项

逐条核对 HLD v2.6 附录 B 第 7 组（L976 一带）：v2.6 新增的 01 同步需求——series 段 `purpose`（initial / candidate / repair / revert）、`E-CANDIDATE-NOT-REVERT`、`pending_plan_at_terminal`——均已登记。未发现需新报的同步项。

## 交付备注

本文件为本方唯一提交内容；被审文档未改动。
