# HLD v2.7（第七轮定向核对）+ 01_Contract_Spec v0.17（第十七轮定向复审）— Claude Code

**评审方**：Claude Code　**日期**：2026-11-05
**对象**：docs/00_Framework_HLD_v2.7.md（仅附录 A24 所列改动）；docs/01_Contract_Spec_v0.17.md（仅 A3 中 v0.17 一条所列改动）
**输入**：
- HEAD `34a096e1a531ed2aa90b621f408f951aef5d86c1`
- HLD v2.7 sha256 `4ca18baeac6dbc059ae0c2332119813e02d65f5bc5959f4828b0cbeb09cfd6bf`
- 01 v0.17 sha256 `a33a7b0a43fa8bea597b326d4feb9c0d15757cf3c99d8cfbdc825ac28c5de06d`
- 另读：两份上一轮处置表、上一轮三家原始意见

**方法**：
- 对 v2.6→v2.7、v0.16→v0.17 做逐句 diff，再沿直接关联条款走查：HLD §4.2.4 冻结的 series 推进模型；01 §3.3 分支 B、§2.2d 持有者更替重派。
- 四份示例按原文路由手工演算。

**约束遵守**：未访问 Quickbuild，未读本轮其他评审方意见，未修改被审文档。

## 结论表

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.7（A24） | **GO** | 0 | 0 | 1 | 1 |
| 第二部分：01 v0.17（A3 v0.17） | **NO-GO** | 0 | 1 | 2 | 1 |
| 同步项（不计入第二部分） | — | 0 | 0 | 0 | 0 |

### 第二部分的 MAJOR（C17-01）：隔离重派不排他

隔离的前提是"隔离中的任务单独执行"，但正文同时写了：
- "不在 S 内的新派发不受影响"；
- 每个嫌疑集各自"至多一个"任务在执行；
- 新实例 hello 后的持有者更替重派扫描没有排除 isolating 任务。

所以隔离头执行时，同一实例上仍可能有别的任务在执行。崩溃时，两种读法各破坏一条 v0.17 自己声明的保证：

| 读法 | 结果 | 破坏的保证 |
|---|---|---|
| 按字面"只对它 +1" | 新来的毒丸让隔离中的无辜任务被计数，最终进入 manual_only；毒丸本身一直不被计数 | 无辜任务不进入只能人工处理 |
| 按一般嫌疑集规则 | 只要有持续的并发流量，毒丸每次崩溃都与他人同处，永远不计数；送达后的失效又不计入启动失败 | 毒丸一定在有限次数内被识别（等于回到 v0.15 的无界循环） |

安全性仍然成立：没有双重执行，也没有伪造远端事实。

## 负责人七项裁决判断表

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | **成立** | 本版未触及汇合、超时显式化与 retried 确认范围。代价不变：两路报告与超时 / 替代历史都要保留。 |
| ② | Quickbuild 默认取最新 Profile 快照，在 Run 启动时固定 | **成立** | 上一轮留下的唯一措辞已改为"已调查配置（Tizen Base RBS 样本）中构建根取自 reference，能否独立固定为 unverified"，与实测记录一致。代价如实可见：快照越新，与构建根的差距越大，可能出现与 patch 无关的构建失败；失败时附两个编号。 |
| ③ | Profile 严格匹配 + 小改动复用预案 | **成立** | 本版未改。v2 仍缺省关闭，开启前须用真实工具链数据评估。 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | 本版未改验证范围。make_revert 与预校验不缩小范围；撤销后范围只增不减仍保留。 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | 计划状态改由完成事务决定，"计划已撤销、代码未撤销"的不一致已消除。违规返回归到 Optimization task，可按节点 retry 恢复。代价：未决计划期间任何失败都只能撤销候选，包括与候选无关的环境性失败（上一轮已述，可接受）。完成复核与预校验不一致时缺统一出口（H27-01）。 |
| ⑥ | Quickbuild 可加 Base CL，否则默认最新；读回核对 | **成立** | `suites: auto` 一律按需要 A/B 处理，豁免限于显式锁定、全部为 absolute 的套件。判定可确定，且 fail-closed。四份示例（全部 local）不受影响。 |
| ⑦ | 超时后重试成功可发布，须审批人确认 | **成立** | 本版未改。 |

---

## A. 处置落实

### HLD v2.6 处置表（S1–S6）

| 条目 | 正文落点 | 结论 |
|---|---|---|
| S1 预校验 / 完成复核 | §7A.4 L743："受理时只做预校验……此时不创建或迁移 OptimizationPlan、不推进 series"；"权威复核在 §4.2.4 的 task 完成 / series 推进事务内"；崩溃、CAS 失败、重放的规则；§11.3 v2.7 用例 | 落实；与 §4.2.4"candidate 预分配不改变 current series"、01 §3.3 分支 B 一致。复核不一致（CAS 以外）的出口未写（H27-01） |
| S2 残留清理 | L745"撤销段即候选段的逆变更"；L879 两条旧用例替换；能力检查旧用例改为"gate 消费 A/B 依赖字段" | 落实 |
| S3 违规归因 | L746"返回 opt_patch_ready 以外的任何 status → sys.invalid_result"；no_gain_found 核对无净变更；L453 兜底改为纵深防御 | 落实 |
| S4 改交撤销 | L743 ②"拒绝响应携带 plan_id 与 parent_tree……make_revert……task 以其他 status 结束 → sys.invalid_result" | 落实；"其他 status"的范围需排除合法的 base_mismatch 出口（H27-02） |
| S5 auto 套件 | L457 | 落实 |
| S6 字段去重、构建根措辞 | L639、L628 | 落实 |

**记录更正**：两条都准确。
- HLD_v2.5 处置表正文确为 R1–R4 四个问题。
- R4 的触发例在规则③下不可达（本方上一轮已更正）。

### 01 v0.16 处置表（T1–T5）

| 条目 | 正文落点 | 结论 |
|---|---|---|
| T1 嫌疑集隔离 | L185：嫌疑集、|S|=1 计数、|S|≥2 不计数并隔离、确定序持久化；L187 recovery_mode 迁移；CF-AUTH-20g / 20k | 文字落实，但隔离不排他（C17-01） |
| T2 核销前毒丸 | L185"按持久化的 owner_epoch / DispatchReceipt 绑定识别……不论是否收到 ACK"；"按授权实际是否已核销分流" | 落实。与 launcher 的"送达"边界不一致（C17-03） |
| T3 launcher 上界 | L187 spawn_attempt_id、四类启动失败、连续上界、稳定期清零、送达后不计 | 落实。见 C17-03 |
| T4 manual_only 下的 probe | L161 C-11a 行、L191、L601、L604、CF-IPC-10、CF-AUTH-20j | 落实；自动映射已排除 |
| T5 迁移与守卫 | L157 C-09、L173 ④、L161 C-11a、L187 迁移、CF-AUTH-20l | 落实；L192 的 hello 重派扫描未同步（并入 C17-01） |

**两处合并方案**：
- **核销前毒丸**（派发绑定识别 + 按授权实际状态分流）：成立。以 receipt 的 target_epoch 识别、不看 ACK，覆盖了"解析计划即崩溃"。按 consumed 与否分流，避免了"已核销的恢复派发处于 awaiting_consume、被误按未核销关闭"。
- **launcher**（持久化拉起记录的连续上界 + 送达后不计）：方向成立。先写 spawn 记录、按 spawn 恰计一次，解决了"hello 前退出没有租约"；"送达后归 task 计数"解决了执行期毒丸先触发全局停机。但"送达"与嫌疑集用的"派发绑定"不是同一个边界：intent 已写、ACK 之前崩溃的那一段两边都计（C17-03）。

**处置表计数**（并入 C17-04）：01_v0.16 处置表写"合计 7 条意见"。上一轮原文是 Kimi 0、Claude Code 4、Codex 2，共 6 条；按 5 个独立问题归并正确，7 只有在把 CC C16-03 的两点分开计时才成立。A3 的 v0.17 条与"关联"行沿用了 7。

---

## B. 第一部分：HLD v2.7（A24）核对

### B1. 预校验与完成复核

**能使两者结论不同的来源**：

| 来源 | 机制 | 结果 |
|---|---|---|
| series 推进 | 一切会推进 series 的事件 | 父版本 CAS 失败，01 §3.3 步骤 2 → sys.error，候选作废、计划不变（有定义） |
| Benchmark 收益判定写回 | 在 BenchReport 落账事务内迁移计划（pending_validation → accepted / rejected_reverting），**不推进 series** | CAS 照样通过，而 purpose 可能改变（见下），出口未定义 |
| 不推进 series 的环边 | 消耗环计数、不改 series（§11.3 已有此类环） | 准入复核可能不再满足，出口未定义 |

**purpose 改变的例子**：某失败节点在 pending_validation 期间被预校验为 ①（撤销）；完成前判定写回为 accepted，此时已无未决计划，同一段在复核时应落入 ④（以"repair"名义回退已接受的优化）。

**可达性**：在四份示例中不可达。规则③要求镜像、UT、Benchmark 在 G' 上依次必经，因此同一 series 上 Benchmark 判定与 UT / 构建失败不会并发。但规则③不禁止其他产 patch 的并行分支，所以出口必须有定义（H27-01）。

| 场景 | 结果 | 唯一性 |
|---|---|---|
| 撤销受理后 worker 崩溃 | 原候选 series + rejected_reverting，attempt 重试后重新提交 | ✓ |
| 新候选受理后崩溃 | 不产生计划；新 attempt 启动事务把旧 registered candidate 退役 | ✓ |
| 完成事务重放 | 复用 receipt，计划数 / 轮数各一次 | ✓ |
| 父版本 CAS 失败 | sys.error，计划不变 | ✓ |
| 并行两个候选（同一 expected_parent） | 先完成者推进，后者 CAS 失败 → sys.error | ✓ |
| CAS 通过但 purpose / 计划 / 准入复核不一致 | 未定义 | ✗（H27-01） |
| 与 §4.2.4 冻结模型的关系 | 计划迁移并入"父版本 CAS + 结果提交 + lineage + current 推进"的单事务，预分配不改 current | 一致 |

### B2. E-CANDIDATE-NOT-REVERT → make_revert

- **环计数**：环边在 task 完成后的路由中采用，一个 task 只完成一次，改交撤销只消耗一次环计数。✓
- **重试**：改交之前 attempt 崩溃，走节点 retry，消耗的是 retry 预算而不是环计数；新 attempt 重新预校验。✓
- **候选唯一性**：01 §3.3 规定每 task 至多一个活跃 candidate、"重复提交拒绝"。被预校验拒绝的提交必须不登记为 candidate，否则改交会被"重复提交"挡住。HLD 只写"即时拒绝"，没写不登记；01 侧的落地属 B-7 已登记的同步项（"candidate 受理的预校验结果与完成事务复核"），HLD 侧措辞并入 H27-02。
- **"task 以其他 status 结束 → sys.invalid_result"的范围**：没有排除镜像节点合法的 `image_failed_exhausted(base_mismatch | backend_source_input_unsupported)`（v2.5 规定 base_mismatch 优先于撤销）（H27-02）。

### B3. 未决计划下的违规返回与 campaign 正常终局

| 场景 | 结果 | 冲突？ |
|---|---|---|
| 候选全部撤销（P 已 reverted）后返回 no_gain_found，series 相对 snapshot 无净变更 | 合法，report_no_gain 以 succeeded 关闭 | 无 |
| 有被接受的优化或修复段（如 input: none 下 Compiler 修好快照自身的构建问题）后返回 no_gain_found | sys.invalid_result；应返回 no_further_gain（asserts_nonempty）进审批 | 无，语义一致 |
| P 为 rejected_reverting 时 Optimization 返回 opt_patch_ready（撤销段） | ①revert | 无 |
| P 为 pending_validation 时 Optimization 被调用 | 示例中不可达：Benchmark 在落账事务内先写判定，再经 bench_done 路由到 optimize | 无 |

### B4. suites: auto 与四份示例、absolute-only 豁免

四份示例全部 `backend: local`，LocalGbsBackend 三项能力为 verified，加载不受影响。示例一、四的 `bench_gate` 用 `regression_pct`，本就需要 A/B。示例二无阈值 gate。没有示例依赖豁免，v2.7 测试组也只用"显式锁定 absolute 套件"作通过例。一致。

### 第一部分问题

#### H27-01 [MINOR] 完成事务复核与预校验不一致（CAS 通过时）的出口未定义

- **位置**：§7A.4 L743"判定的事务位置（v2.7）"。
- **依据**：
  - "权威复核在 §4.2.4 的 task 完成 / series 推进事务内：校验父版本 CAS、当前计划、purpose 与准入，**成功时**与 lineage / current 推进一起原子创建或迁移计划。父版本 CAS 失败、候选作废、task 失败或候选受理后崩溃，都不改变计划状态"。
  - §7A.4 收益判定："由框架在 BenchReport 落账事务内写回计划记录"（不推进 series）。
  - 01 §3.3 步骤 2："CAS……失败归 **sys.error**（合法并发竞争，可按节点 retry 策略重试）"。
- **问题**：
  - 正文只给了"成功时"与"CAS 失败"两种结局。计划状态（收益判定写回）和环计数（不推进 series 的环）都可以在不改变 current series 的情况下变化，因此存在"CAS 通过、但 purpose / 计划 / 准入复核结论与预校验不同"的第三种结局。
  - 这种情况下，task 完成事务是整体失败、只丢弃候选，还是按复核结论改记 purpose，实现者无从判断。按复核结论改记最危险：一个按撤销提交的段会以 repair 名义回退已接受的优化。
- **候选改动**：

```diff
- 校验父版本 CAS、当前计划、purpose 与准入，成功时与 lineage / current 推进一起原子创建或迁移计划。
+ 校验父版本 CAS、当前计划、purpose 与准入，成功时与 lineage / current 推进一起原子创建或迁移计划；
+ 复核推导的 purpose / plan_id 与预校验保存值不同，或准入不再满足 → 与父版本 CAS 失败同一出口：候选作废、计划与 series 均不变、task 以 sys.error（reason = candidate_recheck_failed，合法并发竞争）结束，按节点 retry 策略重试，重试时重新预校验（Optimization 届时得到 E-PLAN-NO-CAPACITY 并返回无进一步收益）；不得按复核结论改记 purpose。
```

- **副作用**：
  - 竞争失败统一为一个 sys.error 出口，与冻结的 CAS 语义一致，不新增 status。
  - 未配 retry 的节点在这种竞争下会进入 fail_safe。可以接受：它只在存在并行产 patch 分支的流水线中出现，且与 CAS 竞争的既有代价相同。
- **配套测试 / 夹具**：
  - 构造并行产 patch 分支的流水线：失败节点预校验为 revert，完成前注入 Benchmark 判定写回为 accepted → 完成事务以 sys.error(candidate_recheck_failed) 结束，计划仍为 accepted，series 不变。
  - Optimization 预校验通过准入后，注入不推进 series 的环消耗剩余次数 → sys.error；重试后得到 E-PLAN-NO-CAPACITY，返回 no_further_gain。
  - 以上两例的完成事务前后 kill → 结局唯一。

#### H27-02 [NIT] 改交撤销规则的范围：合法失败出口与"被拒提交不登记"

- **位置**：§7A.4 L743 ②；L745 base_mismatch 优先。
- **依据**：
  - ②："task 以其他 status 结束 → `sys.invalid_result`（v2.7）"。
  - L745："`base_mismatch` 优先于确定性撤销……镜像节点直接返回 `image_failed_exhausted`(reason = base_mismatch)，不产生撤销段"。
  - 01 §3.3：series_candidate_submit "每 task 至多一个，重复提交拒绝"。
- **问题**：
  1. 镜像节点若在被拒之后才读回发现 base_mismatch（或 backend_source_input_unsupported），按 ② 应判 sys.invalid_result；按 L745 应走 image_failed_exhausted。两条规则对同一事件给出不同出口，配了 `retry: [sys.invalid_result]` 时还会对一个确定性的输入问题重复重试。
  2. 被预校验拒绝的提交如果被登记为该 task 的 candidate，"至多一个"会挡住随后的改交。
- **候选改动**：

```diff
- task 以其他 status 结束 → `sys.invalid_result`（v2.7）；
+ task 以其他 status 结束 → `sys.invalid_result`（v2.7）；例外：镜像节点的 `image_failed_exhausted`(reason ∈ {base_mismatch, backend_source_input_unsupported}) 仍按 §7A.4 base_mismatch 优先规则处理。预校验拒绝的提交不登记 candidate、不占"每 task 至多一个"名额，改交须使用新的 request_id。
```

- **副作用**：无语义扩张，只是消除两条规则之间的冲突。
- **配套测试 / 夹具**：
  - FakeImage 先交 AI 修复段被拒，随后读回 base_mismatch → image_failed_exhausted(base_mismatch) → fail_safe，不是 sys.invalid_result。
  - 被拒后用新 request_id 改交撤销 → 受理；复用旧 request_id → 返回首次的拒绝响应。

---

## D. 第二部分：01 v0.17 核对

### D1. 嫌疑集与隔离重派

| 检查项 | 结论 |
|---|---|
| 单个计数 / 多个不计数 | 规则清楚；同一退役事件对同一 task 至多计一次；触发者只计 loss。✓ |
| 隔离序持久化 | suspect_set_id / isolation_seq 入模型，重启按序继续（CF-AUTH-20k）。✓ |
| 隔离排他性 | **不成立**："不在 S 内的新派发不受影响"、多个嫌疑集各自"至多一个"、L192 hello 扫描不排除 isolating，三者都允许隔离头与他人同处执行阶段（C17-01） |
| 饿死 / 死锁 | 隔离头崩溃后若其实例回收卡住（子树不空），隔离头不终结也不达上限，计数要到回收事务才结算，整条队列停住——包括旧持有者早已静默、本可执行的无辜任务。排队中的未核销任务授权 `expires_at` 可能过期，被按 release_failed 关闭（C17-02） |
| 核销前毒丸 | 以 receipt 绑定识别，覆盖 awaiting_consume；按授权实际状态分流。✓ 与 launcher 边界不一致（C17-03） |
| manual_only 后的自动执行 | C-09、④、execute 派发均排除；C-11a 只记录；迁移表中 manual_only 为终止态。没有自动路径能执行发布。✓ |
| 人工裁决与远端事实 | 只读 probe 对任一 recovery_state 合法并确实送达（CF-AUTH-20j）；全部发生时拒绝 confirm_not_released。✓ |

### D2. 五条时间线 × 崩溃点 × 期限 × 上限 × 毒丸 × 同实例无辜任务

记号：P 为毒丸，B 为无辜任务，N 为隔离期间新到的、不在 S 内的任务；"✓"为恰一个出口。

| 时间线 | 情形 | 计数 | 出口 | 判定 |
|---|---|---|---|---|
| 1 正常 | intent / ACK / 落账各点崩溃、无毒丸 | 实例独有一 task → +1（≤3） | receipt 规则唯一送达，最终 outcome | ✓ |
| 1 | awaiting_consume 到期（E1 活但不核销） | 触发者 loss | <2 立即重派；=2 → release_failed(dispatch_loss_exhausted) | ✓ |
| 1 | 核销前毒丸 P，单独 | P +1/次 | ≤3 次后 release_failed（未核销） | ✓ |
| 1 | 核销前毒丸 P，在 ACK 前崩溃 | P +1 **且** launcher 计启动失败 | 若 max_start_failures 先到 → 全局停机 | **C17-03** |
| 1 | 核销前毒丸 P + 同实例 B | 首次 |S|=2 不计、隔离 | 隔离排他时 ✓；N 并发时见 C17-01 | ✓ / **C17-01** |
| 2 核销后发生前 | E1 崩溃、单 task | +1 | 等回收 → resumed → 对账 → proceed | ✓ |
| 2 | 执行中毒丸 P + B | 首次不计，隔离；P 单独时逐次 +1 | P 至多 1+3 次后 manual_only；B 正常完成 | ✓（仅当排他） |
| 2 | 同上，隔离期间有 N 在 P 的实例上执行 | 字面：只给 P +1；一般规则：|S'|≥2 不计 | 字面读法下 N 若为毒丸则误计 P / B；一般规则下 P 永不计数 | **C17-01** |
| 2 | 隔离头 P 崩溃后实例回收卡住 | 不结算 | 队列停住，B 无限等待 | **C17-02** |
| 2 | 计数耗尽 | — | manual_only → probe（任一状态合法）→ 受约束的人工裁决 | ✓ |
| 3 发生后 | ACK 前 / 后崩溃 | 同时间线 2 | resumed → 对账 happened → released 映射 | ✓ |
| 3 | 达上限 | — | manual_only；probe 全部发生 → 只允许 confirm_released | ✓ |
| 4 indeterminate | 任意崩溃 | awaiting_probe 不入嫌疑集 | 周期 probe；manual_only 下 probe 只作证据 | ✓ |
| 5 实例活、单 task 失联 | A 到期 | A loss；其余执行绑定者入 S | |S|=1 → +1；|S|≥2 → 隔离；A 本身不入隔离、正常重派 | ✓；A 与隔离头并发同 C17-01 |
| 5 | 同一到期事件重放 / ABA / launcher 重启 | CAS 一次、spawn 记录恰一次 | 只一个替换实例 | ✓ |
| 5 | 隔离中 task 期限到期 | 只计它的 loss（CF-AUTH-20k） | — | ✓ |

**重复 / 遗漏汇总**：
- **重复**：ACK 前崩溃同时计 task 中断与启动失败（C17-03）。
- **遗漏**：隔离期间并发执行时，毒丸可能永不计数（C17-01）。
- 其余每格恰一个出口。

### 第二部分问题

#### C17-01 [MAJOR] 隔离重派不排他：隔离头与他人同处执行阶段时，"只对它 +1"误伤无辜；按一般规则则毒丸永不被识别

- **位置**：01 v0.17 §2.2d L185（嫌疑集）、L187（recovery_mode 迁移）、L192（持有者更替重派扫描）；CF-AUTH-20g / 20k。
- **依据**：
  - L185："任一时刻全部实例上至多一个 **S 内** task 处于执行可能阶段，其余保持等待……**隔离中的单个 task 所在实例被回收时只对它 +1（嫌疑集大小为 1）**……**不在 S 内的新派发不受影响**。因此毒丸 task 至多 1 + `max_task_interrupts` 次崩溃后被识别，无辜 task……不被连带计数"。
  - L192："编排在受理新 broker 实例的 broker_hello 后，扫描全部非终态 release task 中'最近一条 DispatchReceipt（任一 state）的 target_epoch ≠ 当前 epoch'者……授权未核销 → 直接以替代协议写新 intent 重新送达"（未排除 isolating）。
  - L187："`waiting_holder` 与 `isolating` 下执行类阶段定时器不武装"（只管定时器，不管派发）。
- **问题**：隔离之所以能分清肇事者，前提是隔离头**单独**执行。现文有三处破坏这个前提：
  - (a) 新派发照常进入同一实例；
  - (b) 若先后形成两个嫌疑集（S1 来自 E1 崩溃，S2 来自 E2 崩溃），"至多一个 S 内"按集计算，两个隔离头可同时执行；
  - (c) hello 扫描会把排队中的 isolating 未核销任务立即重派。

  隔离头所在实例崩溃时：
  1. **按字面"只对它 +1"**——反例：一次与任务无关的崩溃（OOM）形成 S = {B1, B2}，都是无辜任务；隔离期间新到的毒丸 N 不在 S 内、照常派发，与隔离头 B1 同实例执行；N 每次让实例崩溃，只计 B1 +1，N 不计。B1 三次后进入 manual_only，接着 B2 轮为隔离头、同样被耗尽，N 始终未被识别。
  2. **按一般嫌疑集规则**（S' = 当时全部执行绑定者，|S'|≥2 不计数）——只要每次崩溃时都有并发流量，毒丸 P 永远与他人同处，永不计数；送达后的失效按 T3 又不计入启动失败，launcher 不会停机。这就回到了 v0.15 的无界重派。

  两种读法分别违反"无辜不进入只能人工处理"和"毒丸有限次被识别"，都是 v0.17 明文声明的性质。CF-AUTH-20g / 20k 只在没有并发流量时成立，所以夹具能通过，但不覆盖反例。
- **候选改动（全局排他隔离通道）**：

```diff
--- §2.2d 嫌疑集
- ……任一时刻全部实例上至多一个 S 内 task 处于执行可能阶段，其余保持等待、定时器不武装；隔离中的单个 task 所在实例被回收时只对它 +1（嫌疑集大小为 1）；……不在 S 内的新派发不受影响。
+ ……全部嫌疑集合并为**唯一的全局隔离通道**（按 (suspect_set 创建序, consumed_at 或 dispatched_at, task_id) 排序，持久化）。通道非空时，**隔离头处于执行可能阶段期间，当前实例不承担其他任何 execute 派发**：不在通道内的新 execute 派发写 intent 后暂缓发送（不计时、不入嫌疑集），隔离头离开执行可能阶段后按序发送；只探测派发不受限，但 awaiting_probe 不入嫌疑集，因此不影响归因。因此隔离头所在实例被回收时，嫌疑集按定义恰为 {隔离头}，只对它 +1；通道清空后恢复常规并发。
--- §2.2d 持有者更替重派（L192）
- 扫描全部非终态 release task 中"最近一条 DispatchReceipt（任一 state）的 target_epoch ≠ 当前 epoch"者，按授权状态分流：
+ 扫描全部非终态、且 recovery_mode ∉ {isolating, manual_only} 的 release task 中"最近一条 DispatchReceipt（任一 state）的 target_epoch ≠ 当前 epoch"者（isolating 者只由隔离通道按序派发），按授权状态分流：
```

- **副作用**：
  - 隔离期间全局 execute 发布串行。每个隔离头占用通道的时间受其阶段期限约束；通道长度受嫌疑集大小约束；毒丸至多占用 1 + max_task_interrupts 轮。只在"多任务同实例崩溃"之后出现，正常路径无成本。
  - 暂缓的新派发在通道内不计时，不会因等待被误判失联。
  - 未核销的暂缓任务的授权可能在等待中过期，按 C17-02 的规则处理。
  - 不新增命令；recovery_mode 不变。只多一个"暂缓发送"的 intent 子状态（或复用 DispatchReceipt 的 intent 未发送态），随 dev 版本号递增。
- **配套测试 / 夹具**：
  - **CF-AUTH-20g 扩充两例**：
    - S = {B1, B2} 来自无关崩溃，隔离期间注入新毒丸 N → N 在隔离头执行期间不发送；通道清空后 N 单独执行并逐次计数，B1、B2 的 interrupt_count 均为 0 且最终完成。
    - S = {P, B} 且有持续并发流量 → P 在至多 1 + max_task_interrupts 次崩溃后被识别，期间流量任务不与 P 同处执行阶段。
  - **CF-AUTH-20k 扩充**：先后两次崩溃形成两个嫌疑集 → 合并为一个通道，任一时刻至多一个隔离头在执行；hello 扫描不重派 isolating 任务。
  - **model-based**：随机流量 + 0–2 个毒丸 + 随机无关崩溃。断言：非毒丸 task 永不进入 manual_only，也不被 dispatch_loss_exhausted 关闭（授权自然过期除外）；每个毒丸在有界次数内被识别；broker 不因 task 崩溃被启动退避停机。

#### C17-02 [MINOR] 隔离队列的活性：隔离头等待回收时整条队列停住；排队中的未核销授权可能过期

- **位置**：L185"它终结或达到上限后，下一个进入执行"；L187 迁移；§2.2a ①"授权有效（未核销未撤销**未过期**……）"、AuthorizationRecord.expires_at。
- **依据**：
  - L185："隔离中的单个 task 所在实例被回收时只对它 +1……它终结或达到上限后，下一个进入执行"。
  - L183："存在后代、接口读取失败、绑定无法核实或清理超时均不 reclaimed"；"旧实例无法清理 → 其已核销 task 不重派、告警并计入 R13"。
- **问题**：
  1. 计数在**回收事务**里结算。隔离头所在实例崩溃后，若子树迟迟不空，回收不完成，隔离头既不终结也不计数，队列无限停住。被挡住的 B 的旧持有者早已静默，本可以在新实例上执行。非隔离设计里，回收卡住只阻塞该实例上的已核销任务；隔离把阻塞扩大到整个嫌疑集。
  2. 排队中的未核销任务（Run = running）不计时，但授权的 `expires_at` 照常走。队列较长时，无辜任务会在轮到之前过期，被 C-09② 按 release_failed(authorization_expired) 关闭——结论上是"因为别人的毒丸而发布失败"，且原因不可见。
- **候选改动**：

```diff
--- §2.2d 嫌疑集
- 隔离中的单个 task 所在实例被回收时只对它 +1（嫌疑集大小为 1）；它终结或达到上限后，下一个进入执行
+ 隔离头所在实例被判定 lapsed / retiring 的事务内即对隔离头 +1（排他执行下嫌疑集恰为它本身，归因不依赖回收完成），并让出通道：隔离头转 waiting_holder 并移到通道末尾（待其实例 reclaimed 后再次轮到），下一个进入执行；隔离头终结或达到上限则出通道
+ 通道内未核销 task 的授权在等待中过期 → 按 C-09② 关闭，reason = `authorization_expired_in_isolation`（审计与 FeedbackReport 写明所在嫌疑集与等待时长），不计 loss / interrupt；通道排序对未核销者以 expires_at 优先
```

- **副作用**：
  - 计数时点从回收事务提前到失效判定事务。单个 task 的计数仍为同一退役事件至多一次，CAS 规则不变。
  - 回收卡住只阻塞该隔离头自身（与非隔离设计一致）。
  - 过期仍按冻结的授权有效期处理，不放宽审批时效，只让原因可见、并减少过期概率。
- **配套测试 / 夹具**：
  - CF-AUTH-20k 增：隔离头崩溃且实例子树长期不空 → 隔离头 +1、转 waiting_holder，下一个 B 在新实例上执行并完成；子树清空后隔离头重新轮到。
  - 通道中未核销 task 授权到期 → reason = authorization_expired_in_isolation，计数不变。
  - 失效判定事务前后 kill → 只计一次。

#### C17-03 [MINOR] 启动失败与任务计数的边界不一致：intent 已写、ACK 之前的崩溃被两边各计一次

- **位置**：L185 嫌疑集识别；L187 launcher 启动失败上界；L192"DispatchReceipt.completed 仅表示 RPC 送达"；CF-AUTH-20g / 20i。
- **依据**：
  - 嫌疑集："按持久化的 owner_epoch / DispatchReceipt 绑定识别（最近一条 execute 型 receipt 的 target_epoch == 该实例 epoch，**不论是否收到 ACK**）"。
  - launcher："启动失败 = ……或 hello 后**在首个 execute 派发送达本实例之前** lapsed"；"**派发送达之后**的 lapsed 归入上述 task 计数，不计入启动失败"。
  - 送达的定义（L192）：DispatchReceipt.completed 表示 RPC 送达。
  - CF-AUTH-20g 预期："broker 未被启动退避停机"。
- **问题**：
  - 一个让 broker 在**处理派发 RPC 时**（ACK 之前）崩溃的核销前毒丸：嫌疑集按 target_epoch 把它算作 interrupt；launcher 按"未送达"算作启动失败。同一次失效被计两次。
  - 每个新实例都是"hello → 收到派发 → 崩溃"，恰好构成**连续**的启动失败。只要 `max_start_failures` ≤ 1 + max_task_interrupts（正文未给缺省值或约束），全局停机会先于毒丸被识别发生，与 T3 的意图和 CF-AUTH-20g 的预期相反。
  - 人工重启后，连续失败计数未清零（需稳定期），下一次失败立即再停机。
- **候选改动**：

```diff
--- launcher 启动失败上界
- 或 hello 后在首个 execute 派发送达本实例之前 lapsed
+ 或 hello 后、在 Ledger 中出现首条 target_epoch == 本实例 epoch 的 execute 型 DispatchReceipt（intent 即算，不论 ACK）之前 lapsed
- **派发送达之后的 lapsed 归入上述 task 计数，不计入启动失败**
+ **出现上述 receipt 之后的 lapsed 归入 task 计数（嫌疑集），不计入启动失败**——两者以同一谓词划界，每次失效恰归一边
```

- **副作用**：
  - 两种计数互斥且完备，不再需要约束 max_start_failures 与 max_task_interrupts 的关系。
  - "hello 后、尚无任何派发即崩溃"仍计启动失败，覆盖与 task 无关的启动问题。
  - launcher 需要读取 receipt 的 target_epoch（只读依赖，上一轮已接受）。
- **配套测试 / 夹具**：
  - CF-AUTH-20g 增"ACK 前崩溃"变体：FakeBroker 在反序列化 ReleaseDispatch 时崩溃 → 只计 task interrupt，启动失败计数不变，broker 不停机，毒丸有界关闭。
  - CF-AUTH-20i 增边界点：intent 提交前 / 后各 kill broker → 分别只计启动失败 / 只计 task。

#### C17-04 [NIT] `waiting_holder` 的进入事务措辞；处置记录计数

- **位置**：L187 迁移；01_v0.16 处置表开头、A3 v0.17 条、"关联"行。
- **依据**：
  - L187："`active` →（已核销 task 所在实例 retiring / lapsed 的**回收事务**）`waiting_holder` →（持有者更替重派事务）`active`"。
  - 处置表："合计 7 条意见，归并为 5 个独立问题"；上一轮原文 Kimi 0、Claude Code 4（C16-01..04）、Codex 2（C16-01、C16-02）。
- **问题**：
  - 等待旧持有者的区间是"retiring / lapsed 判定 → reclaimed"。"回收事务"若指 reclaimed 事务，waiting_holder 就只在回收完成后的一瞬存在，失去意义。定时器失效目前实际由"owner 实例 live"承担，所以不致错。
  - 7 条与原文 6 条不符（若把 CC C16-03 的两点分开计则为 7，应注明）。
- **候选改动**：

```diff
- `active` →（已核销 task 所在实例 retiring / lapsed 的回收事务）`waiting_holder`
+ `active` →（已核销 task 所在实例被标记 retiring 或 lapsed 的事务）`waiting_holder` →（该实例 reclaimed 后的持有者更替重派事务）`active`
- 合计 7 条意见，归并为 5 个独立问题
+ 合计 6 条意见（Claude Code C16-03 含两点，按 7 点处置），归并为 5 个独立问题
```

- **副作用**：无。
- **配套测试 / 夹具**：CF-AUTH-20l 增：实例 retiring 后、reclaimed 前，已核销 task 的 recovery_mode 为 waiting_holder。

---

## 同步项

逐条核对 HLD v2.7 附录 B 第 7 组（L977）："candidate 受理的预校验结果与完成事务复核"、`E-CANDIDATE-NOT-REVERT`（含 plan_id 与 parent_tree）、`pending_plan_at_terminal`、series 段 purpose 均已登记。01 §3.3 的 series_candidate_submit 尚无预校验与复核结论字段，也尚未写明"被拒不登记"，均属已登记范围，不重复报。没有新增同步项。

## 交付备注

本文件为本方唯一提交内容；被审文档未改动。
