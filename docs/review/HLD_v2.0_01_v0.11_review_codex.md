# HLD v2.0 / 01 v0.11 独立评审（Codex）

评审日期：2026-11-02。依据为本地仓库文件；未修改被审文档。候选 diff 均为建议，尚未实施。

## 结论与计数

| 被审部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.0 | **NO-GO** | 0 | 11 | 1 | 0 |
| 第二部分：01_Contract_Spec v0.11 | **NO-GO** | 2 | 2 | 1 | 1 |

另列 **1 项 MAJOR 同步项**，不计入 01 v0.11 的缺陷数，亦不重复计入 HLD 缺陷数。01 仍以上游冻结 v1.0 为准，不因尚未实现 v2.0 的新增范围而扣分。

方法：全文阅读两份 HLD、01 v0.11、v0.10 处置表；对照两个版本 diff，并查阅相关历史处置与上一轮原始意见。对 YAML 抽取节点/边并计算普通支配集合；对恢复、审批和 receipt 逐事务构造反例。本仓库当前为设计文档，以下不是对实际实现运行测试后的结论。

## 已核实的边界与通过项

| 检查范围 | 核实结果 |
|---|---|
| 冻结 HLD §4.1、§4.2.2–§4.2.5、§4.3.2–§4.4 | 引擎封装、路由权、activation、发布两值 outcome、恢复优先级的核心条款保留。§4.2.2 仅增加示例名称。 |
| 冻结 HLD §4.2.6 / E-01 | 原规则集保留后追加新规则；v2.0 §17 保留有效勘误与 01 V-13b 的单一事实源。没有发现 E-01 被撤销。新规则和示例的冲突见 H-01。 |
| D11 / §4.3.1 / §4.5 | 存在实质扩展：外部等待也进入 paused，且其中部分时间计入预算。因此不能把“原样保留”理解成状态/计时实现可原封不动使用；见 H-04、S-01。 |
| §5.1.1 / §5.2 | 发布句柄仍明确排除；自由函数不可包装、效应键、跨 attempt 定态规则保留。新构建效应的归因没有达到原有键的精度，见 H-05。 |
| §8.1–§8.5 | broker 凭据隔离、审批 CAS、publishing 例外、IPC UID/task 绑定保留。Gateway 通道亦规定独立 UID、worker 不直连；这部分未降低隔离要求。 |
| 两阶段 / 两后端 | 普通全流程确为 RPM→镜像；local 的全量+mic 与 Quickbuild 经 Gateway 均已定案。专项入口、修复报告与恢复归因仍有问题，见 H-02/03/05。 |
| Benchmark / Optimization | 三来源、三模式、完整测量记录、生成脚本确认、AutoFDO/BOLT 先行、环预算均已写明。“无需重测”指无需为补采分析信息重测，不与无效样本重测、A/B 交叉重复相矛盾。可执行判定与强制重验证缺口见 H-06/07/08。 |
| LLM / Coding Agent 入口 | completion-only + 禁工具 + JSON 校验足以承载文中分析/生成任务，实际工具动作留在 Agent 能力层。CLI 参数属于 E0 事实，不能据缺参数直接判缺陷。MCP/HTTP 共用契约、鉴权和 request_id 的方向明确。板子有效性的 AI 判定矛盾见 H-06。 |
| SourceProvider / 分期 | Tizen 的 git 物化和 tree_digest 与冻结模型一致。VD 明确后接 P8，本轮不要求给出 Perforce 实现；其无凭据调用最终仍须经 Gateway。P4 用 mock/Fake 做框架合规、P6/P7 做真实业务联调的顺序可以成立，不要求提前交付全部业务 Agent。 |
| 附录 B 第 7 组 | 正文新增的显式 `[01]` 项（如空计划）有落点；MCP 消息另在第 2 组，conformance 在第 6 组。未发现必须单列的新增 `[01]` 项漏列。该清单不能替代本报告指出的尚未定案语义。 |
| 01 新命令 / framing | CommandName 与三列注册表均为 **19 项，无漏项**。合法 envelope 的非法 payload 用 ResponseError；未知 command/缺 request_id 用 FramingError，三种既有夹具已可区分。 |

## 第一部分：HLD v2.0

### H-01 — MAJOR：全流程 YAML 不满足新增 release_requires 的支配性规则

**位置**：`docs/00_Framework_HLD_v2.0.md` §4.2.1 示例一（L253、L265–285），§4.2.6（L355）。

**依据**：§4.2.6 写“每一类报告的生产节点存在且支配 human_review”，并定义支配为“到消费节点的每条路径都必须先经过生产节点”；示例要求 `ut_report, bench_report`，同时存在 `compile_image → review_static → join:pre_final_review → review_final → ci_plan → human_review`。

**问题与反例**：上述图路径不经过 ut/benchmark；二者都不普通支配 human_review。实际 join 等待全部来源，运行时确有同步，但文中并未给 release_requires 定义区别于普通支配的 AND-join 必经证明，不能自行用它替换明确的“每条路径”。抽取原文得到 human_review 的普通支配集合为 `{compile_rpm, compile_image, join:pre_final_review, review_final, ci_plan, human_review}`。因此“原文必须通过”与新规则同时不可满足。专项示例的 ut/benchmark 则确实支配 human_review。

**候选改动**：最小且不改冻结校验语义的方案是把这份规范示例改为串行审查；保留并行可作为另一次明确的校验规则扩展。

```diff
@@ HLD §4.2.1 full_pipeline
-joins:
-  - id: pre_final_review
-    wait_for: [bench_gate, review_static]
-    timeout_min: 720
-    to: review_final
@@ routes
-  - { from: compile_image, on: image_ready, to: [ut, review_static] }
+  - { from: compile_image, on: image_ready, to: ut }
-  - { from: bench_gate, on: pass, to: join:pre_final_review }
-  - { from: review_static, on: review_report_ready, to: join:pre_final_review }
+  - { from: bench_gate, on: pass, to: review_static }
+  - { from: review_static, on: review_report_ready, to: review_final }
@@ §7A.5 / 示例流程说明
-镜像就绪后与 UT 并行
+阈值判定通过后执行静态审查，再执行汇总审查
```

**副作用**：失去静态审查和板上测试的并行收益；不放宽 E-01/V-15，也不改变已有 join 语义。如果要保留并行，应另行完整定义只用于新规则的必备报告数据流分析及循环/series 转移证明，不能默默改“支配”的含义。

**配套测试/夹具**：新 CF-DSL-RELREQ-01：原示例按现规则拒绝；修订示例原文字节通过；缺 ut/bench 生产者、旁路审批路径均拒绝；原有 AND-join/V-10–V-12 用例保持。

### H-02 — MAJOR：RPM 内部修复完成后，成功 BuildReport 属于旧 series，发布新鲜度无法满足

**位置**：HLD §7A.1（L542）、§4.2.4、§4.2.6；对照 01 §3.3（L354–378）。

**依据**：§7A.1 写“提交 series candidate … → 再构建”；HLD 又规定“在 task 完成事务内”推进 series，且“旧报告全部失效，必须重新验证”。01 冻结契约要求 `HandoffResult.series_id == TaskInput.series_id`，Report 头也须一致。

**问题与反例**：compile_rpm 接到 S0，内部修复并构建成功，完成时才把 candidate 推进为 S1。其成功 BuildReport 仍只能合法标 S0；下游 image/UT/bench 对 S1 产报告。全流程 release_requires 要求当前 S1 的 build_report，而图中没有再次运行 RPM 的边。把报告直接标成 S1 又违反冻结的上下文校验。连续多轮内部修复也与“每 task 至多一个活跃 candidate、不可异载荷重提”不吻合。

**候选改动**：修复成为有预算的显式 task 回流，不在同一次 task 内发布 candidate 后继续构建。

```diff
@@ HLD §7A.1 RPM 模式
-最优方案作为修复 patch 提交 series candidate ... → 再构建
+每 task 构建当前 TaskInput.series；需要修复时提交唯一 candidate，
+返回 build_fix_patch_ready 并结束 task。完成事务推进 series 后，
+由声明环重派 RPM task；仅无 candidate 的成功 task 返回 build_passed。
+成功 BuildReport 因而绑定实际验证过的当前 series。
@@ §4.2.1 两份 YAML 的 loops/routes
+  # loops
+  - id: rpm_fix_loop
+    edges: [{from: compile_rpm, to: compile_rpm}]
+    budget: {max_rounds: 2, max_wall_clock_min: 480}
+  # routes
+  - {from: compile_rpm, on: build_fix_patch_ready, to: compile_rpm}
@@ 附录 B 第 7 组
+Compiler 注册及 fixture 增加 build_fix_patch_ready；明确按 mode 解析产出与输入声明。
```

**副作用**：修复增加 task/dispatch，显式消耗环预算；保留 candidate、series、Report 的冻结绑定，避免为了新流程放宽核心校验。两份示例应共同应用该修改。

**配套测试/夹具**：RPM S0 修复→S1 成功→镜像/UT/bench→审批全链；成功报告不得重标 series；多轮修复、完成事务前后 kill、预算耗尽；release_requires 必须找到 S1 的成功构建报告。

### H-03 — MAJOR：优化专项直接出镜像，却被强制 RPM 前置检查挡住

**位置**：HLD §4.2.1 示例二 L309、§7.6.1 L499、D15。

**依据**：专项规定 `entry: compile_image # 首轮直接以当前 snapshot 出镜像并测量`；§7.6.1 又规定“镜像构建前强制执行…RPM 阶段结果”；D15 允许两模式“均可单独删除”。

**问题**：专项首轮没有 RPM task/报告；若 RPM 结果是 hard-required，则入口不满足校验；若不是，运行时仍无法执行写明的强制检查。这不是 ks 或环境参数缺失，而是“独立镜像模式是否允许”的规范矛盾。

**候选改动**：保留已经明确允许的独立镜像模式，显式声明前置要求。

```diff
@@ HLD §7.6.1
-镜像构建前强制执行...RPM 阶段结果...
+镜像节点配置 rpm_precheck: required|independent，默认 required。
+required：当前 series 的成功 BuildReport 为 hard-required，生产者须支配镜像节点。
+independent：允许直接对 pinned snapshot+series 全量构建，不要求既有 RPM 结果；
+仍强制检查 patch 可应用性、ks 可解析与磁盘水位。它不宣称增量 RPM 已先行通过。
@@ §4.2.1 optimize_campaign
-config: { backend: local }
+config: { backend: local, rpm_precheck: independent }
@@ 附录 B 第 7 组
+按节点 mode/config 实例化输入要求，覆盖独立镜像构建。
```

**副作用**：专项首轮可能在较晚的全量构建阶段暴露错误，但这是现有“首轮直接出镜像”的明确代价；普通全流程仍强制先 RPM。

**配套测试/夹具**：两份原文加载和首轮执行；required 缺 RPM 拒绝；independent 无 RPM 可执行；required 只存在旧 series 报告拒绝；空 series snapshot 失败不进入 queued。

### H-04 — MAJOR：外部等待没有与 worker 占用和混合等待计时闭合

**位置**：HLD D11、§4.3.1 L375、§4.4、§4.5、§5.1.2、§7.6.1、§8.6。

**依据**：D11 定义槽为“持有 worker/资源执行中”；新增条款说远程构建等待释放槽；SDK 仍为同步 `execute` / `build_image(...) -> ImageResult`，普通进程退出映射 sys.crash。§4.3.1 说外部等待计预算，§4.5 保留“wall_clock 排除 paused 时段”，后面又区分暂停原因。

**问题与反例**：A 的 build_image 同步阻塞时，到底保留 worker/额度还是杀掉并恢复，没有定案；若保留，足够多 paused Run 可占满 worker 额度，使已入槽的 B 无法执行；若普通退出，产生 sys.crash/retry 而非正常等待。另有同一 Run 同时等待一个远程构建、一个 hitl，或者远程构建仍运行但另一任务等待 SSO 登录时，哪些秒计费无法由单一 paused 区间确定。预算在计费的 paused 期间到期也必须有合法关闭入口。

**候选改动**：定案可持久化、可恢复的节点外部等待，并把时间规则写为全集条件。

```diff
@@ HLD §4.3.1 / §5.1.2
+外部等待登记为 Ledger WaitRecord，绑定 task/dispatch/effect 版本、原因和外部操作引用。
+SDK 在登记提交后以框架专用挂起结果退出 worker；不产生 sys.crash、不消耗 retry。
+释放 worker/本地执行额度；远端仍在运行的 job 继续占远程配额。
+等待完成以持久事件恰一次唤醒，经 queued 取槽；重执行复用原 task/dispatch，先对账效应。
+计费 paused 上仍可触发 budget_expire，终止/对账远端操作后 ledger 级收尾。
@@ §4.5
-wall_clock 排除 paused 时段
+仅在 Run 无可运行/在飞本地工作，且全部未决等待均为 hitl 或登录等待时扣除该区间；
+只要仍有远端构建/板子排队等计费等待，该区间计入 run/loop/join 预算。
+publishing 继续按冻结规则豁免。等待原因及区间边界持久化，重启不重置。
```

**副作用**：增加挂起事件和等待记录，不能仅改 enum 注释；混合等待的上述取法可能让并行 hitl 期间的构建成本照常计费，与“流水线自身成本计入”一致。远端完成只登记结果，不能不经 FIFO 唤醒 worker。

**配套测试/夹具**：外部等待×hitl×登录等待的组合时钟；paused 中预算到期；等待登记/worker 退出/唤醒前后 kill；大量 paused Run 不耗尽 worker；同结果重复通知不双 dispatch；远端在途 job 不因释放执行槽而释放配额。01 对应修订另列 S-01。

### H-05 — MAJOR：新增构建 probe 的身份比冻结效应键更粗，可能复用另一产物

**位置**：HLD §5.2 L428/L431、§7.6.1、§7.8、§8.6。

**依据**：冻结键包含 `dispatch_id, effect_class, effect_call_id, effect_params_digest[, repeat_seq]`；新远程 probe 却“按提交时写入的 run/task 标识查询”；镜像 probe“按缓存键查存在性”，正文唯一定义的镜像缓存键是 `(snapshot_id, 构建配置摘要, 后端, 镜像配置)`，不含 series/tree。

**问题与反例**：同 task 内两个合法调用，或跨 attempt 异参新键，具有相同 run/task。A 成功、B 提交后崩溃，恢复仅按 run/task 不能证明查到的是 B。基线镜像和带 patch 镜像也可拥有相同上述缓存键；“存在”既不能证明是当前效应的产物，也不能证明镜像完整可消费。远端提交响应丢失后的查询暂不可见，不等于确认未发生。

**候选改动**：保留现有幂等设计，将完整身份送到网关和产物索引。

```diff
@@ HLD §5.2 / §7.6.1 / §8.6
-远程构建...按提交时写入的 run/task 标识查询
+远程提交绑定 (idem_key, effect_version)，并保存完整输入摘要、run/task 与远端 job_id。
+Gateway 转发及远端查询均以该身份精确归因；run/task 仅为辅助标签。
+发送前持久化提交 intent；响应丢失先 probe；查询不可见但不能证明未提交时返回 indeterminate。
+确认未发生且旧提交执行已静默后才允许新版本提交；迟到结果不得替换现行版本。
-镜像构建...按缓存键查存在性
+镜像效应 probe 查当前 effect 的完整、已提交产物记录；校验 snapshot、tree_digest、
+构建输入摘要和内容摘要，返回可重建的 ImageResult。BaselineCache 键不作效应身份。
```

**副作用**：远端若无法可靠检索该身份，必须 fail-closed 保持不可判定，不能假定 Quickbuild 支持幂等提交。这是上线能力验证，不是要求更换后端。

**配套测试/夹具**：FakeQuickbuild 同 task 双 call_id/异参/新 version；提交前、远端受理后 ACK 前、产物下载中 kill；查询延迟可见；取消后迟到完成；基线与 patched 镜像同时存在不得串用；半写文件不能 probe 为成功。

### H-06 — MAJOR：Benchmark 判定缺少失败闭合规则，快速/单项报告可伪装成完整达标

**位置**：HLD §7A.0、§7A.3 L555–565、§7.7、§4.2.6。

**依据**：§7A.3 仅写“重复次数、置信区间、显著性检验”“随套件版本固定”，并输出最大 `regression_pct` 和 `spec_out_count`；三模式中单项只跑指定用例、快速减少重复次数。release_requires 只检查报告类型存在且同 series。§7A.0 同时把“判断板子是否稳定”列为 AI 职责，而原则要求“是否通过一律由…确定性结果判定”。

**问题与反例**：10 个必测指标只测 1 个合格指标，报告可以有 `spec_out_count=0` 和很小的最大回归，满足示例发布前置；未测 9 项没有必须 fail-closed 的规则。SPEC 缺失、样本不足、基线为零、置信区间跨阈值、方向不同等也无统一判定。仅列统计术语没有给出实现者可照做的政策 schema 或 oracle。AI 决定样本是否有效还会使统计输入选择不可重复。

**候选改动**：让套件携带可执行、版本化判定政策，并把覆盖完整性纳入发布要求。

```diff
@@ HLD §7A.3
+SuiteVersion 固化脚本/解析器摘要、指标方向/单位、SPEC 边界与比较算子、
+必测指标集合、每模式用例/样本数、最低有效样本数、统计算法版本/参数及黄金向量。
+算法与参数不全的套件不得激活；禁止运行期由 AI 选择判定算法或样本有效性。
+逐指标结果为 pass/fail/inconclusive/not_measured；缺 SPEC、缺指标、样本不足或
+无法合法计算相对回归时不得生成“通过”的聚合值。
+BenchReport 记录 mode、要求/实测覆盖集、有效样本数及 validation_complete。
+默认发布要求 validation_complete=true；快速/单项报告仅在覆盖所声明发布验证范围且
+满足其统计政策时可作为审批证据，否则不能仅凭 spec_out_count=0 放行。
@@ §7A.0 / §7.7
-Benchmark AI：测试前与用例间判断板子是否稳定
+板子稳定性由版本化窗口/阈值/超时规则决定；AI 只解释异常，不决定样本有效性。
@@ 附录 B 第 7 组
+同步上述判定政策、测量记录、覆盖性与审批校验字段及错误/不确定结果。
```

**副作用**：已有仅脚本+解析器的套件需补政策；快速模式仍可用，但不能默认等价于发布验证。完整遥测会增加存储与测量扰动，应把采集配置同时固定于 A/B 两侧。

**配套测试/夹具**：大小方向、等于 SPEC 边界、零基线、缺项、低样本、跨界置信区间、全量/单项/快速覆盖矩阵；LLM 对同一遥测返回相反建议仍得到相同有效性与 gate 结论；生成型脚本版本变更后重新检查/确认。

### H-07 — MAJOR：优化重验证和收益没有成为不可绕过的配置/运行时约束

**位置**：HLD D18、§2.4、§4.2.6、§7A.4、示例二。

**依据**：D18 要求产物“必须回流 Compiler → UT → Benchmark”；§2.4 又允许删 UT 并从 release_requires 移除报告；§4.2.6 只要求任意环有预算，没有针对优化回流路径的约束。§7A.4 要求“Benchmark 重测并证明收益”，但专项没有收益 gate，只在 `no_further_gain` 后进入审批。

**问题与反例**：保留 optimizer、删 UT、移除 ut_report，现静态规则仍可通过，直接违反 D18。另一条合法配置可让 opt_patch_ready 进入普通有预算环后直达审查。即便使用示例，优化前业务 patch 已较 snapshot 快 20%，优化使它退化至快 8%，与 snapshot 的 A/B 仍显示收益；没有优化父版本对照与确定性接受规则，不能证明优化本身有效。AI 的 no_further_gain 也不能承担收益认证。

**候选改动**：把保证落在注册能力、路径校验和验证记录上。

```diff
@@ HLD §4.2.6 / §7A.4
+注册声明产物为 optimization_candidate 的节点，opt_patch_ready 的所有非失败路径
+必须先经过当前 series 的 RPM、镜像、UT、Benchmark 再到审批；否则拒绝加载。
+含优化候选发布的配置不得从 release_requires 移除上述验证要求。
+OptimizationPlan 固定 parent_series/tree、父镜像、目标指标和确定性收益政策。
+优化验证同时报告 snapshot 回归与 candidate 对 parent 的收益；未达收益政策、
+功能回归或统计不确定时不得把候选作为已验证优化发布。
+失败候选以显式逆向 patch 生成新 series，或关闭该 Run；禁止回拨 current 指针。
+no_further_gain 仅决定不再提案，不能替代验证记录或直接使未验证候选通过。
```

**副作用**：缩小“删除任一 Agent”的合法组合，这是 D18 已声明强制性的必要结果；增加父镜像保留和一次比较成本。可保留只分析不产候选的优化模式，但须明确分型。

**配套测试/夹具**：保留 optimizer 删 UT 拒绝；优化回流绕过 build/UT/bench 各一反例；对 snapshot 改善但对 parent 退化拒绝；置信度不足不放行；失败候选撤回后全部报告重新新鲜；环上限仍独立生效。

### H-08 — MAJOR：Profile“新鲜”的核心判据未定义，无法拒绝不兼容输入

**位置**：HLD §7.8 L517、§7A.3 profile 采集、§7A.4 AutoFDO/BOLT。

**依据**：Profile 键为“包、代码版本、板型、套件”；“代码版本变化超过阈值即标记陈旧”，Optimization“只使用新鲜 profile”。

**问题**：代码版本是离散标识，文中没有“变化量”函数、阈值政策及默认行为。同代码版本但不同编译选项/工具链/被采样二进制的 profile 也会命中该键；附带采集条件不等于定义了消费者适配校验。于是“陈旧拒用”没有可测试的真值，AutoFDO/BOLT 两种方法也没有各自的兼容性契约。

**候选改动**：先用保守的完全匹配政策闭合首期，不凭未定义的距离复用。

```diff
@@ HLD §7.8
-代码版本变化超过阈值即标记陈旧
+Profile 记录 package source tree、image/build input digest、被采样 binary 标识、
+采样格式/工具版本、板型与能力、套件版本及采集条件摘要。
+首期以方法插件声明的兼容字段完全匹配作为新鲜度判据；缺字段或不匹配即拒用并请求重采。
+AutoFDO/BOLT 分别登记可消费格式和字段集合，插件版本纳入执行环境。
+不启用“代码漂移低于阈值”的复用；将来启用须给出确定性距离算法、政策版本和验收向量。
```

**副作用**：保守匹配降低跨构建复用率，但不会阻止使用本次 Benchmark 采集的数据生成下一轮候选。候选必须记录源 profile 与被采样父版本，不能伪称来自待优化后的二进制。

**配套测试/夹具**：同 source 不同构建选项、同套件名不同版本、板型相同采样能力不同、字段缺失、格式不支持均拒绝；完全匹配接受；重采前后引用与 Ledger 归因完整。

### H-09 — MAJOR：板子租约回收没有远端静默屏障，下一任务可能与残留任务并发

**位置**：HLD §7.7 L509–511、§5.1.2、§5.2。

**依据**：“租约与 task 绑定，task 终结或心跳丢失时回收”；worker killpg 只规定终止本机进程组及登记的长进程；刷机 probe 通过读镜像标识。

**问题与反例**：A 在板子上启动长时间测试/采样后本机 worker 崩溃，租约被回收并分给 B；远端命令可能仍运行，或刷机操作仍未结束。读到预期镜像标识不能证明 A 的测试已经停止。B 的测量可能受污染，B 的刷机也可能破坏 A 尚在运行的操作。健康/静止指标检查没有提供操作所有权或迟到命令隔离。

**候选改动**：回收先进入隔离态，经适配器确认静默再可租。

```diff
@@ HLD §7.7
-task 终结或心跳丢失时回收
+租约带单调 generation，远端操作与结果绑定 lease_id/generation。
+task 终结、失联或超时后进入 reclaiming，停止旧执行并执行板型适配器的静默/复位协议；
+确认旧刷机、测试、采样不再在途且健康检查通过后才转 available。
+无法确认静默则 quarantine 并告警，不直接重新分配；旧 generation 的命令与结果拒绝。
+租约/回收状态由 Ledger 持久化，重启先对账再开放分配。
```

**副作用**：失联可能暂时减少可用板数；需要板型适配器提供复位/静默能力。不能以“租约超时”代替外部效应已结束的证据。

**配套测试/夹具**：A 本机死亡但板上测试继续；刷机超时后迟到；回收中重启；并发申请只一胜；旧 generation 回报拒绝；不能静默时 B 不得获得该板。静止性重测继续受总预算限制。

### H-10 — MAJOR：基线缓存没有完整的构建环境失效条件，也没有共享内容的生命周期约束

**位置**：HLD D19、§7.6.3、§7.8 L515–517。

**依据**：基线键仅列 `(snapshot_id, 构建配置摘要, 后端, 镜像配置)`；同 snapshot 后续 Run“直接复用”；镜像“终态后默认 7 天清理”。D12 只明确 framework/agent/provider 等执行环境，并未说明构建配置摘要包含工具链及外部包仓快照。

**问题与反例**：相同源码/config/backend 名下工具链、系统包仓或远端工程构建环境更新，旧基线仍命中，candidate 则用新环境构建，A/B 不再只比较 patch。共享基线被多个 Run 引用时，按某个 Run 的终态时间清理也缺少跨引用约束；大镜像下载与 GC 的提交/租约机制不能仅靠“文件存在”判断。

**候选改动**：明确构建输入闭包和复用/回收条件，复用既有 blob 原则。

```diff
@@ HLD §7.8
+构建配置摘要必须覆盖工具链制品、依赖包仓快照、ks 及其依赖、后端实现/远端构建环境版本。
+基线和 candidate 使用相同的该输入闭包，只有 series/tree 不同；不能固定的输入使缓存不可复用。
+配置/环境摘要变更、对象缺失/损坏、未完成提交均视为未命中。
+镜像/Profile 的上传采用 §7.5 同等的 lease→fsync/rename→Ledger 索引协议；
+共享内容按全部活跃 Run/板子使用/上传/缓存 pin 的引用保护，7 天策略不得删除仍被 pin 的对象。
+同键构建请求合并为一个在途构建；镜像、基线、Profile 分别配置容量/保留策略，
+GC 与分配由编排协调，磁盘不足时拒绝新构建且不破坏在用对象。
```

**副作用**：工具链/仓库更新会降低缓存命中率；增加输入闭包摘要与跨 Run 引用索引。这属于单机资源保护，不引入 N2 排除的多租户配额系统。

**配套测试/夹具**：相同 source 但工具链/仓库快照变更失效；A/B 环境不等拒绝比较；多 Run 同键竞争只一次构建；一个 Run 关闭另一个 paused 使用时 GC 不删；下载中 kill+GC；损坏缓存重建；容量耗尽不伤已有引用。

### H-11 — MAJOR：input:none 只校验 entry，不能保证后续节点能处理空 series

**位置**：HLD §4.2.6 L355、§5.1.1 L417、§4.3.1。

**依据**：“其 entry 节点不得是需要 patch 才能工作的节点（以 Agent 注册的输入声明判定）”；同时即插即用承诺“不合法的配置根本无法启动，而不是跑到一半出错”。

**问题与反例**：entry 为允许无 patch 的分析节点，成功后线性进入 `input_requirement=needs_patch` 的节点；中间没有 candidate 提交。全部现规则通过，但第二节点拿到的仍为空 series。entry 的局部检查无法证明整个配置合法。`input:none` 的 submit_patch 拒绝语义与初始空 series 的原子签发也应明确，而非仅画 created→queued。

**候选改动**：首期采用保守全图限制；无需发明未定义的“该 outcome 必定生成 patch”推断。

```diff
@@ HLD §4.2.6 input 规则
-其 entry 节点不得是需要 patch 才能工作的节点
+input:none 的所有可达 agent 节点必须声明可处理空 series；任一 needs_patch 节点即拒绝加载。
+后续允许精细放行时，须先定义 outcome 级 candidate 生产声明和所有路径证明。
@@ §4.3.1
+snapshot pin 成功后，同事务签发空 series、base lineage、tree_digest/current，再进入 queued；
+snapshot 失败走 closed(snapshot_error)，不得提前排队。该 Run 的 submit_patch 始终拒绝，
+错误语义在 MCP/HTTP 一致，重复 create_run 不重复创建初始 series。
```

**副作用**：可能拒绝“先必然产 patch、再消费 patch”的可行专项图，但首期契约未提供可靠证明，保守拒绝符合当前 validator 风格；两份现有示例可通过合适注册声明适配。

**配套测试/夹具**：无 patch entry→needs_patch 下游拒绝；全图 empty-safe 通过；空 series 初始化逐提交点 kill；pin 失败；input:none submit_patch 拒绝；MCP/HTTP 同 request_id 重放一致。

### H-12 — MINOR：删除 Benchmark/镜像节点的配置说明漏掉 release_requires

**位置**：HLD §2.4 删除影响表，§4.2.6。

**依据**：删 Benchmark 的调整只列“阈值 gate 与 Optimization”；删镜像只列 UT/Benchmark/Optimization。只有删 UT 一行提醒移除 release_requires。

**问题**：照表删除后，原 full_pipeline 仍声明 bench_report/image_report，正确 validator 必须拒绝。不能把报告缺失当 optional 自动降级，否则会绕过发布显式要求。这是迁移说明不完整，不是已证明的发布绕过。

**候选改动**：

```diff
@@ HLD §2.4
+删除 Benchmark、镜像或其他报告生产者时，还须显式调整 release_requires 中对应条目；
+若保留必需报告却无生产者，一律拒绝加载。校验器不得自动删减清单。
+保留 Optimization 时的强制验证依赖不得删除（见 D18 与优化路径校验）。
```

**副作用**：只完善操作说明；显式接受未测发布仍记录于 pipeline_digest，不暗中改变发布政策。

**配套测试/夹具**：删 Benchmark 但保留 bench_report 拒绝；删除相关节点并显式修改清单后普通非优化子集通过，报告标记未测；不能自动修复配置。

## 第二部分：01_Contract_Spec v0.11

### 上轮处置与恢复链核验

| v0.10 问题 / 本轮重点 | 本轮核验 |
|---|---|
| R10-01：release_outcome 第三值 | **原问题已修复**：恢复对账改用独立命令，outcome 回归两值；happened/indeterminate 的主路径可表达。不是因为新增命令本身再否决。 |
| R10-02：对账后原子许可 | guard 已加入，但新许可的重放域没有 epoch，且 D12 wire 路径重新出现双表示，见 C-02/C-04。 |
| R10-03：出向模型与两事务 | DispatchReceipt 与 intent/completed 已增加，四个发送窗口有测试条目；不能再报“没有模型”。交付 ACK 与任务执行完成之间的恢复责任仍未闭合，见 C-03。 |
| R10-04 / Z10-01：broker_epoch 获取/校验 | broker_hello 与 consume 等值校验已增加；不再报“没有握手”。新命令还需 epoch 作用域，见 C-02；边界数值见 C-06。 |
| R10-05：FramingError | **原三种形态已闭合**，与 ResponseError 有明确前置解析边界。非字符串关联字段应按不可提取处理为 None，可在实现夹具中补全，不据此另报 MAJOR。 |
| R10-06：D12 状态分型 | running/publishing 两组已补，原缺陷关闭；新 reconcile 的 D12 冲突是 C-04。 |
| R10-07：receipt 先于 guard | consume ACK 丢失的同 id 重投已明确返回 granted；原问题关闭。不能把这条规则不加 epoch 区分地应用于恢复许可，见 C-02。 |
| R10-08：轮数 | 已修正。 |

四条时间线：

1. **核销前崩溃**：授权仍未消费，重新执行 C-09 可 granted；但 dispatch 已 ACK、broker 尚未 consume 即单独崩溃时，谁重新激活该任务没有完整协议，见 C-03。
2. **核销后、发布前崩溃**：更高 epoch、旧执行静默、resumed、probe 的主链成立；not_happened 许可还受 C-02/C-04 影响。
3. **发布中崩溃**：happened 可 ledger 级 released 映射；indeterminate 记录并保持 publishing，不再错误触发 C-10。not_happened 重启执行仍须防旧许可重放；部分目标无法确定是否全部完成时不能伪装为 confirmed_not_happened，须留在不确定路径。
4. **旧 broker 未静默**：CF-AUTH-09 的 stale_epoch 拒绝正确；但物理 reap 不等于清除了旧连接已进入控制面队列的命令，C-02 要求补齐命令 epoch 守卫。

### C-01 — BLOCKER：gate 的 resolved CAS 被审批提交和 outbox 消费各执行一次

**位置**：`docs/01_Contract_Spec_v0.11.md` §2.1 C-08a/C-08b（L152–153）、§5.1 approval socket（L543）、CF-SM-02/10、CF-IPC-04；冻结 HLD §4.4。

**依据**：§5.1 明确 decision_submit 事务包含“gate CAS + resume outbox”；冻结 HLD §4.4 更明确为“gate outcome CAS（waiting→resolved）”。C-08a/C-08b 却又把“gate CAS waiting→resolved”列为 outbox 消费 guard。

**问题与反例**：合法 approve 事务提交后 gate 已 resolved，outbox 消费再要求 waiting 必定失败。于是 paused 的 Run 无法 resume，running 中的 gate 也不能 durable dispatch 下游；plain-decision 型同样受影响。把两次 CAS 默认为不同对象无法成立，因为 C-08 点名的是 gate，而不是 inbox。这是全文走查发现的既有矛盾，不是 v2.0 同步项。

**候选改动**：只有 decision_submit 负责决定 CAS，消费负责 outbox/inbox CAS。

```diff
@@ 01 §2.1 C-08a / C-08b
-decision_id 未消费；gate CAS waiting→resolved
+outbox_id 未消费；gate 已 resolved 且其 decision_id/outcome 与 outbox 一致；
+同事务写 inbox receipt + 持久下游 dispatch，并按 Run 状态迁 queued 或保持 running。
+同 outbox 重放复用已登记结果，不再次改 gate、不重复建 task。
@@ C-08c / §5.1
+TTL 路径由编排以 waiting→resolved(gate_expired) CAS 生成同形 outbox；
+决定与 TTL 仅一方胜出。消费沿用上述同一协议，作废 gate 的事件仅审计化丢弃。
```

**副作用**：不改变冻结审批事务；把判决状态与送达状态分开。重启时从已 resolved 的 gate 与 pending outbox 恢复，不能重做审批。

**配套测试/夹具**：修订 CF-SM-02/10、CF-IPC-04，真实串联 decision_submit→消费，不能手工用 waiting gate 代替提交后的状态；审批提交前/后及消费提交前/后 kill；TTL/人工决定竞争；paused/running/plain/release-approval 四类都只 dispatch 一次。

### C-02 — BLOCKER：恢复许可的 receipt 未按 epoch 隔离，旧 proceed 可绕过本轮复核

**位置**：01 §2.2(a)、§5.1 `ReleaseReconcileReport` / `ReleaseOutcomeRequest`（L527–532）、通用幂等域（L548）、C-10/C-10a。

**依据**：`ReleaseReconcileReport` 只有 `task_id, probe, remote_refs`；broker 入向域是 `(broker, command)`；通则“同 id 同载荷重放返回首响应”；`proceed` 原子 guard 又要求“epoch 现行”。只有 authorization_consume 载荷和校验明确包含 epoch。

**问题与反例**：epoch E1 对账 not_happened、请求 R 获得 proceed 并落 receipt，随后 broker 在执行前崩溃。E2 经 hello/consume 获得 resumed，期间配置已漂移；它重新 probe 仍为 not_happened，重用合法的逻辑请求 ID R。新对账 payload 与旧值完全一样，通用 receipt 规则返回 E1 的 proceed，不再执行 E2 的 D12/epoch/pending 校验。规范没有要求该命令跨恢复更换 ID，也没有将 broker 幂等域定义为 epoch 域；不能依赖客户端恰好生成不同 ID 保证安全。

此外，release_outcome 的 C-10 guard 只有 publishing，没有校验连接 epoch 与当前授权 epoch。旧 broker 在死亡前发出、但尚未处理的 release_failed，可在新 broker 获准执行后到达，提前关闭当前 publishing；旧进程已 reap 不能消除已排队的 IPC。

**候选改动**：恢复许可和执行结果同属当前发布 epoch；receipt 的历史响应不跨 epoch 赋予新执行权。

```diff
@@ 01 §5.1
-class ReleaseReconcileReport(...): task_id: str; probe: ...; remote_refs: ...
+class ReleaseReconcileReport(...): task_id: str; broker_epoch: int; probe: ...; remote_refs: ...
-class ReleaseOutcomeRequest(...): task_id: str; outcome: ...
+class ReleaseOutcomeRequest(...): task_id: str; broker_epoch: int; outcome: ...
+上述两命令幂等域为 (broker_service, task_id, connection_epoch, command)。
+先验证连接已握手且 payload epoch 等于连接 epoch；再在该域查 receipt，随后执行状态 guard。
+新的对账/结果受理要求 connection_epoch == AuthorizationRecord.granted_epoch，
+且为该 task 的现行恢复/执行阶段；陈旧连接只返回拒绝并审计，不产生终态映射。
@@ §2.2(a) / C-10 / C-10a
+resumed 持久记录本 epoch 的 reconciliation_required；proceed 将其原子转为 execution_permitted。
+同 epoch 同 request_id 仅重放首响应；不同 request_id 不得再次发放执行许可。
+新 epoch 必须重新对账、重新获得许可，旧 epoch 的 receipt 只作历史记录。
+broker 客户端不得在连接/进程 epoch 变化后使用缓存许可执行发布。
```

**副作用**：两个新/旧命令载荷发生 draft 期变更，需同步客户端；receipt 仍零淘汰，只是明确生命周期域，不回退到窗口去重。authorization_consume 的同 epoch ACK 丢失用例继续返回 granted。

**配套测试/夹具**：新增 CF-AUTH-13：E1 proceed 落账后 kill、E2 resumed、D12 漂移、同逻辑 request_id 重用，断言不复用旧许可；跨 epoch 同 id 异载荷；同 epoch 不同 id 双报告不得双许可；旧结果排队→reap→新 epoch 获准→旧结果到达，不关闭新执行；CF-AUTH-11/12 保持。

### C-03 — MAJOR：DispatchReceipt 的 completed 只代表 ACK，尚未定义交付后的执行恢复责任

**位置**：01 §2.5 `DispatchReceipt`（L266–273）、§5.1 release_dispatch / 通用 RPC（L497/L548）、CF-IPC-10；冻结 HLD §4.3.3。

**依据**：出向协议“broker 响应；事务②写 completed + 首响应”；成功响应类型是 `CommandAck`。恢复仅规定“intent 无 completed → …重派”。broker 去重仅在进程内。§5.1 还保留旧措辞“在出向事务内将…首响应, granted_epoch…写入…子记录”，与新两事务模型和不含 granted_epoch 的模型不一致。

**问题与反例**：broker 收到任务并 ACK，编排已提交 completed；broker 随后在 authorization_consume 前崩溃，编排本身未重启。此时 Run=running、授权未核销、无 intent 待重派；broker 进程内受理状态已失。publishing 的恢复臂尚不适用，completed 的重放又只复用 ACK。没有约定 ACK 必须对应持久受理，也没有约定 broker 重连后恢复所有“已交付但未完成”的 task，因而无法保证继续执行。现有四点注入还未覆盖这个 ACK 落账后的窗口。

**候选改动**：区分 RPC 送达与 release task 生命周期，明确恢复扫描。

```diff
@@ 01 §2.5 / §5.1
+DispatchReceipt.completed 仅表示 RPC 送达完成，不表示 release task 已完成。
+Ledger 在首次发送前已持久化 release task、完整 ReleaseDispatch 载荷和稳定 request_id；
+receipt 关联该 dispatch_id。恢复发送不得仅靠不可逆的 payload_digest 重建请求。
+broker 启动/失联恢复时，编排扫描全部非终态 release task：
+未核销者重新交付并走正常 consume；已核销者在旧执行静默后走 resumed+对账。
+该恢复交付独立于向原调用方复用 completed receipt；不新建逻辑 task，不重复核销。
-在出向事务内将 (...首响应, granted_epoch) 写入授权记录的 dispatch receipt 子记录
+出向以 §2.5 两事务协议写 DispatchReceipt；执行 epoch 由 AuthorizationRecord 及
+发布执行阶段记录承载。统一使用声明的出向幂等域索引，不以可变请求字段另开域。
```

**副作用**：需要在 broker-only 重启时触发扫描，而非只在编排进程重启时依赖 checkpoint；不会要求 broker 成为第二个 Ledger 写者。历史 ACK 的幂等回复与真实执行续跑必须分别测试。

**配套测试/夹具**：CF-IPC-10 保留四点并追加“ACK completed 后、consume 前 broker-only kill”；consume 后但 outcome 前 kill；编排和 broker 同时 kill；原四点必须分别注入两个进程，不只杀发送方。断言 task 最终完成或合法进入 publishing 对账，不凭 completed 丢任务。

### C-04 — MAJOR：reconcile 的 D12 拒绝恢复了双 wire 表示，且无执行的失败回报违背新文字限制

**位置**：01 §2.2(a)、§5.1 L484/L526–531/L544、CF-AUTH-04b/05b。

**依据**：§5.1 写“D12 漂移一律 ResponseError(E-CP-D12-MISMATCH)”；CF-AUTH-04b 对 publishing“任一复核点”同样要求此错误。但 `ReconcileDeny.reason` 包含 `d12_drift`，CF-AUTH-05b 要求返回 deny。其后规定 broker 不发布，却“随即发 release_outcome(release_failed, proceed_denied)”；ReleaseOutcomeRequest 和 broker socket 文字又都限定“仅在实际执行后发送”。

**问题**：同一个 resumed→probe 期间发生漂移→not_happened 的请求，两个权威 fixture 分别要求 ResponseError 和 ResponseOk(deny)，无法同时满足。deny 后没有实际执行，是否可发送 release_outcome 又有两种相反规定。不能把这理解为已定案方案的另一种选择：规范自身没有唯一期望。

**候选改动**：保持 D12 专用错误的既有定案；既然已确认未发生，当前 epoch 的拒绝可直接 ledger 级收尾，免去一个无执行的 outcome 回调。陈旧 epoch 拒绝不能这样收尾（C-02）。

```diff
@@ 01 §2.2(a) / C-10a
-不通过则 deny(reason)，broker ... 随即发 release_outcome(release_failed, proceed_denied)
+连接/授权 epoch 不现行：拒绝、仅审计，不关闭当前执行。
+当前 epoch 的 confirmed_not_happened 经原子复核发现 D12 漂移：同事务登记
+pending(admin_finalize)、保存对账证据并按 §2.2b 的 release_failed 映射收尾；
+响应 ResponseError(E-CP-D12-MISMATCH)，不要求 broker 再发 outcome。
+仅已有 pending(admin_finalize) 阻断时，同事务按该映射收尾，响应
+ReconcileRecorded(reason=not_happened_mapped)。
+通过时仍返回 proceed；happened/indeterminate 保持现有两条路径。
@@ §5.1 / §6
-ReconcileDeny.reason 含 d12_drift / pending_admin_finalize
+移除上述成功响应臂中的 D12 表示；ReconcileRecorded 增 not_happened_mapped。
+C-10a 目标增加 closed(按 §2.2b)；CF-AUTH-05b 拆分为新检出漂移和已登记 pending 两例。
```

**副作用**：拒绝路径减少一次 RPC；依赖当前 epoch、确认未发生、同事务收尾三个条件，不能把任意拒绝都映射为未发布。此改动保留 release_outcome 两值且仅执行后发送，也不触发 publishing 禁止的 C-14。

**配套测试/夹具**：CF-AUTH-04b 与 05b 在同一事件轨迹上期望一致；D12 首次在最终复核检出时 pending 恰一次；收尾事务前后 kill、ACK 丢失重放同错误；已登记 pending 分支；epoch_stale 不关闭；远端 happened 仍优先映射成功，不因 pending 改写事实。

### C-05 — MINOR：新模型未同步到承诺可逐名核对的 A0 类型索引

**位置**：01 §5.1 L471、§7/A0 L763。

**依据**：§5.1 承诺“A0 名 ↔ 正文模型一一解析”；A0 自称“本文全部具名类型及定义位置清单”。本版新增 DispatchReceipt 未列，BrokerHello、ReleaseReconcile 和 FramingError 也只可能被笼统的“命令载荷族”涵盖；位置归组还把 ProbeDispatch / ProviderExecutionConfig 等实际 §5 类型列在 §2。

**问题**：注册表本身已闭合，但 A0 不能作为所承诺的逐名 CI 输入，新增的 Ledger 模型尤其可能漏交付。属于索引与一致性问题，不据此否认正文已有定义。

**候选改动**：

```diff
@@ 01 §7/A0
+§2.5：AuthorizationRecord、DispatchReceipt。
+§5.1：BrokerHelloRequest、BrokerHelloResult、ReleaseReconcileReport、ReconcileProceed、
+ReconcileDeny、ReconcileRecorded、ReleaseReconcileResponse、FramingError、CommandResponse。
+ProbeDispatch/ProbeReport 定位 §5.1；ProviderExecutionConfig 定位 §5.3。
+将“族”展开为可机器读取的类型索引，或明确索引由正文模型自动生成，CI 校验覆盖差集为空。
```

**副作用**：只完善索引与交付检查；C-02/03/04 增删模型后索引也须随之更新。

**配套测试/夹具**：模型定义名集合与索引名集合双向差集为空；19 命令仍各有唯一请求/成功响应映射；复合联合的各 arm 均可解析。

### C-06 — NIT：broker_epoch 上界与 canonical 整数界相差一

**位置**：01 §0.1 L14、§5.1 BrokerHelloResult L521。

**依据**：canonical 整数要求 `|n| < 2^53`；epoch 范围却写 `1..2^53`。

**问题**：按闭区间解释的最后一个合法 epoch 无法参与 consume 载荷摘要。实际极难耗尽，但规范边界应唯一。

**候选改动**：

```diff
@@ 01 §5.1
-范围 1..2^53
+范围 1 <= broker_epoch < 2^53；达到上界拒绝新分配并告警，禁止回绕。
```

**副作用**：不改变任何正常会话；与全局 canonical 约束统一。

**配套测试/夹具**：`2^53-1` 接受，`2^53` 拒绝；模拟分配器耗尽不回绕到旧 epoch。

## 单列同步项（不计为 01 v0.11 缺陷）

### S-01 — MAJOR：D11 扩展要求同步 01 的 paused guard、预算入口与等待恢复

**位置**：HLD v2.0 D11/§4.3.1/§4.5；01 v0.11 §2.1 C-07/C-08/C-13、§3.4。

**依据**：01 C-07 只允许“仅剩 gate 等待”进入 paused；C-13 只允许 queued/running 预算到期；§3.4 无条件“排除 paused”。v2.0 则要求远程构建/板子等待进入 paused，并把这段时间计入预算。

**问题**：继续原样使用 v0.11 会把所有外部等待预算扣掉，且即使计时器发现到期，paused 状态也没有合法 C-13 入口。这是 v2.0 核心修订的同步责任，不是 v0.11 偏离其上游 v1.0。H-04 定案后应一次同步，不能仅新增两个枚举值。

**候选改动**：

```diff
@@ 下一版 01 §2.1
+C-07 扩展为 no_runnable_work_wait，持久记录 gate/external/login 等等待原因。
+外部等待完成以专用持久事件触发 paused→queued；不得复用要求 gate decision 的 C-08 载荷。
-C-13 guard: queued ∨ running
+C-13 guard: queued ∨ running ∨ paused（存在按 HLD 新规则计费的预算）
@@ §3.4 / §5.1 / §6
-排除 paused 与 publishing 时段
+按 HLD H-04 定案后的等待集合计费；仅豁免区间扣除，publishing 原规则不变。
+补 WaitRecord、挂起/唤醒命令、资源占用与重启对账协议，加入命令注册表和 A0。
+新增混合等待、paused 到期、FIFO 唤醒、两次崩溃下不重置预算的 conformance。
```

**副作用**：属于核心状态/时钟行为扩展，contract 版本和相容矩阵必须显式更新；旧 paused-only fixtures 不可直接当作新版全部覆盖。

**配套测试/夹具**：扩展 CF-SM-01 全命令×全状态矩阵；CF-SM-04 增计费 paused 变体；CF-SM-10 增外部等待唤醒；run/loop/join 三时钟同轨迹验证；普通审批等待与 publishing 不消耗预算的冻结用例继续通过。

## 评审交付核对

- 两份 YAML 均已从文档原文抽取并检查可达性；没有把 01 v0.11 不认识 v2.0 字段当作 YAML 缺陷。H-01 的拒绝来自 v2.0 自身规则；H-03 来自其构建前置要求。
- 不将 CLI 参数、ks、Quickbuild 表单、板型刷机命令等 `[待补充]` 环境事实列为缺陷。H-04/06/08 指向的是状态、判定、兼容性政策，不能用环境待补充替代。
- 未要求改变已定案的 LangGraph、单 SQLite、Python、插件机制、Quickbuild、人工审批或 broker 边界；候选方案旨在兑现这些既有决策。
- 所有问题均给出文档位置、原文依据、反例、候选 diff、副作用和配套测试。测试 ID 中本轮新命名的项是建议加入的夹具，未声称仓库已实现或运行通过。
