# HLD v2.13 + 01_Contract_Spec v0.23 + 09_Phased_Dev_Plan v0.3 评审意见（Kimi，第二十三轮定向核对）

## 结论表

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| HLD v2.13（A30 + §13 P0 分批口径） | **GO** | 0 | 0 | 0 | 0 |
| 01_Contract_Spec v0.23（A3 v0.23 条） | **GO** | 0 | 0 | 0 | 1 |
| 09_Phased_Dev_Plan v0.3 | **GO** | 0 | 0 | 0 | 0 |

## 输入与验证边界

- HEAD：`7652a57`（git pull --rebase 后 "Already up to date"）。
- sha256：`00_Framework_HLD_v2.13.md` = `db4507da…8d03d`；`01_Contract_Spec_v0.23.md` = `9764feb1…0b78`；`09_Phased_Dev_Plan_v0.3.md` = `d9aaa33b…63dc`。
- 已读：三份被审文档的本版改动（diff 全文，长行按行号展开核对）；三份处置表全文；上一轮三家原始意见中与本方处置核对相关的部分（仅用于核对忠实性与计数）。未读：本轮其他评审方的意见。
- 执行的命令：git pull/log、sha256sum、diff、grep、sed（均加 `nice -n 19 ionice -c3`）。本轮无需脚本推演，未使用 systemd-run，未跑构建/测试/索引，未访问 Quickbuild，未安装任何软件。

## 任务 A：处置落实、忠实性与计数

### HLD（HLD_v2.12_review_disposition.md，Q1–Q4 + 非编号同步项）

条数：Kimi 1（H22-01）+ Codex 1（H212-01）+ CC 4（H212-01..04）= 6 条归并 4 个——**计数正确**；归属与原意见一致（Q1 = Codex 完整摘要 + CC 只读前缀；Q3 = Kimi 契约句 + CC 覆盖清单，经与两家原文核对一致）。

- **Q1（pyc）**：落实。§11.2 改为按完整文件 digest 免除（明示取代 v2.12 的"按内嵌源哈希"），可信打包清单逐项含源 digest、source_hash、解释器版本与 cache tag、编译参数、完整 pyc digest，门禁核对 checked 标志与源哈希对应关系、不自报生成清单、清单外照常判定；安装前缀只读 + PYTHONDONTWRITEBYTECODE；解释器/参数变化后重新打包发布。§11.3 v2.13 用例含"头部源哈希正确而字节码被替换 → 失败（拼字节生成，不执行）"。**落实**。
- **Q2（片段判据）**：落实。判据 = AST 常量（隐式拼接视为一个常量、按求值后的值比较；f-string/JoinedStr 一律不免除）+ 注释按签名表给出的各语言注释符与规范化规则比较；签名表只含信号本身且插件不能自报扩大。§11.3 用例含隐式拼接、f-string、注释正反对例。**落实**。
- **Q3（全覆盖）**：落实。§11.2 写明执行准入与 exec 记账"覆盖本产品在宿主上的全部进程及其子孙""不存在绕过受管通道的工具调用路径"（由"经 launcher 拉起"扩到全部产品进程），构建 VM 内本产品下发的辅助程序同口径、业务构建步骤仍排除；§11.3 含 worker、编排进程直 spawn 未登记哨兵程序被拒的用例；09 W1 预检④同步要求 mount namespace 与 ExecPaths= 可用性。**落实**。
- **Q4（现行版本）**：落实。"现行版本"= 部署所用策略版本绑定的 HLD 版本（随签名表发布）；Run 创建时在 digest 比对的同一检查中复核所依赖例外仍在现行清单且未到期，否则拒绝创建；在途 Run 不受影响（复核只在创建时）。**落实**。
- **非编号同步项（§13 P0 分批）**：落实。§13 P0 行改为分批口径（第一批为 P0 条件；第二批、第三批分别为 P3/P4 与 P5–P7 gate 入口条件；任一 gate 用到的契约条目含 mock 核心 schema 须已三方通过，provisional 不代替评审），与 09 §3.1、M0b（"按 HLD v2.13 §13 分批口径"）一致。A30 摘要与正文一致；附录 B 第 7 组 v2.13 追加（签名表注释符规则、pyc 制品清单、全覆盖部署检查项、现行版本绑定与 Run 创建复核）已登记。

### 01（01_v0.22_review_disposition.md，Z1–Z5）

条数：Kimi 1（K22-01）+ Codex 2（C22-01/02）+ CC 5（C22-01..05）= 8 条归并 5 个——**计数正确**；Z1 为三家独立发现的同一 MAJOR，归属准确。

- **Z1（锁存约束全部负向结案，三家合并）**：落实。① C-11a：confirmed_not_happened ∧ 锁存为真 → 不作负向映射、记录冲突、告警入 R13、同事务置 manual_only 只经 C-11 收尾（不要求先静默）；② 出口判定前先把合法报告的 appeared 并入锁存（§2.2d indeterminate 段写明"先同事务并入，再判定出口"）；③ §5.1 写明优先级——锁存为真时"全部未发生只允许 confirm_not_released"一条不适用，只允许 keep_unknown 或有合格远端证据的 confirm_released；④ C-10a 防御：not_happened 分支复核锁存，为真则不授予执行许可、记 indeterminate 并告警；⑤ 锁存注释改为"约束本授权的一切负向结案与再次执行许可——C-10a、C-11a、C-11"。**落实**。
- **Z2（证据逐目标覆盖）**：落实。AdjudicationEvidence 增 target_refs；unknown 下 confirm_not_released 要求证据 target_refs 并集**恰等于** manifest 目标集合；probe_report 型由编排从被引报告的 absent 项生成，运维填写无效（CF 断言"被忽略"）。**落实**。
- **Z3（target_ref 算法、②/⑤ 拆分、probe_targets、RunSummary）**：落实。target_ref := "sha256:" + hex(sha256(canonical_json(ReleaseTarget)))，manifest 内重复即拒绝；报告校验拆为处理序②（内部一致、非空、无重复，不落 receipt，同 request_id 修正后受理）与⑤（与 manifest 双射，不符落 receipt、不改锁存）；ReleaseProbeDispatch.probe_targets 由编排填写、恒等于授权全部目标；RunSummary 增 release_targets（结案时各目标最后观测，无观测为 unknown）。**落实**。
- **Z4（K4③ 已放行重送 + K5 判定顺序）**：落实。暂停只拦"尚未放行"的派发（新派发、hello 后重派、暂缓项放行），已放行 intent 按 §2.5 (a) 同 request_id 照常重送、不刷新期限、不产生仅由暂停导致的 phase_deadline；K5 判定顺序定为③→②→①；S2 draining 措辞同步（见 K23-01 的措辞 NIT）。**落实**。
- **Z5（strategy_managed 规则）**：落实。置位 = 归因策略纳入事务；清除 = task 终结或置 manual_only 同事务；不变式 isolating ⇒ strategy_managed；hello 扫描过滤统一为 `strategy_managed = false`，原括注矛盾已改正（"manual_only 者只在 auto_probe_suspended = false 时发只探测"）。**落实**。
- CF-AUTH-17d / 20i / 20j / 20k / 20o 的 R22 格逐条对应上述各点（含锁存为真两序列 × manual_only 两分支 × 静默两态 × kill 与乱序、证据覆盖不全被拒、已放行 intent 暂停期间重送、strategy_managed 清零与不变式检查失败）；contract_version = 1.0.0.dev12。**落实**。
- 处置表无"记录更正"一节（本轮无需更正者）。

### 09（09_v0.2_review_disposition.md，W1–W6）

条数：Kimi 1（P22-01 NIT）+ CC 6（P092-01..06）+ Codex 3（P22-01 MAJOR、P22-02/03）= 10 条归并 6 个——**计数正确**；我方 P22-01 的候选（以第 7 组原文编号为键、入仓、每条恰属一批）被并入 W1 采纳。

- **W1（分批口径 + 批次补齐 + 逐条映射）**：落实。M0b 标注"按 HLD v2.13 §13 分批口径"，写明第二、三批不属 P0；第一批补齐 Demo 路径条目（focus_modules、incomplete/retried/acknowledged_gaps/gaps_changed/succeeded_with_gaps、Diagnosis 与 ai_draft 最小字段、AI 证据/采纳记录、release_evidence、ReleaseOutcomeRequest 可选逐目标观测、DeploymentInventory 与 launcher 执行准入、最小 Git SourceProvider、mic 最小 image.*、sys.scheduler）；第二批补 ModuleRegistry/always_run/protected_paths、ExecutionManifest 其余摘要字段与 P4 mock 核心 schema（OptimizationPlan/purpose/候选复核、BenchReport/OptimizationReport 判定骨架）；§3.1 逐条映射以第 7 组原文编号为键、M0a 前入仓（与开发状态文件同目录）、每条恰属一批、列最早使用方与各日期、每批评审先核对无遗漏，W3/W4 早于所需条目通过日期则顺延或显式缩减 Demo。Demo 六步（启动/构建/AI 修复/空壳 Agent/审批发布/可靠性）所用契约逐条有落点。**落实**。
- **W2（Demo 故障分支）**：落实。§4.2 新增：broker 租约/心跳/阶段期限只检测只告警（不生成 RetirementEvent、不退役、不计数）；编排重启后 broker 租约宽限期；worker 孤儿回收、本地构建效应 probe 对账、恢复规则 (a)；授权过期关闭（C-09②）。失联分流：未核销者不迁入 publishing、到期按可见原因关闭，已核销者保持 publishing 并告警；"人工处理"限定为保留证据与受控排查、不得以直接改账本代替未实现的裁决；编排重启只在未进入故障分支时演示续跑。kill 验收扩为构建中/审批中/intent 前后/核销前后/outcome 前后，W6 脚本固定三个 kill 时点、12-22 预演逐个验证。降级表把 Approval 与 broker 拆为两行（broker 未就绪→无 release 节点的子集；Approval 未就绪→不宣称审批通过、不签发授权）。**落实**。
- **W3（回放记录约束）**：落实。§4.5 备选与降级表两行均要求：记录产自已通过 LLM 安全切片验收的环境并绑定验收 id；出内网前逐条核对密级、不合规不出内网；无记录如实标 FakeLLM。**落实**。
- **W4（D23 部署验收切片）**：落实。§4.2 增"首次在 Demo 主机部署前"切片（安装集扫描、子进程观测、全部产品进程执行准入、DeploymentInventory 记录 approved_digest）；W1 预检④加 mount namespace 与 ExecPaths=；降级表增"D23 deploy 验收未通过 → 不在该主机部署，不得以一次观测无命中代替执行准入"行。**落实**。
- **W5（gate 对照表）**：落实。§10 写明存放位置（与开发状态文件同目录）与三个完成日期（M0a 前 P0–P2；第二批通过前 P3–P4；第三批通过前 P5–P7）。
- **W6（VD 措辞）**：落实。§4.1 改为"除 VD 外，其余各项按 M2 的范围逐项验收（优化在 M2 只含 AutoFDO；Quickbuild 显式延期单独记录；真实发布先经受控测试仓）"。
- §1 状态与 W1 核对对象已更新到 v2.13 / v0.23，三份文档日期与口径互查一致（HLD 头部关联文档指向 01 v0.23；09 M0b 与 HLD §13 P0 行措辞一致）。

## 任务 B：HLD v2.13 逐项核对

1. **pyc**：完整文件摘要 + 可信清单 + checked 标志核对 + 只读前缀 + 禁生成，自封免扫旁路已封；清单字段齐备。可执行，无放行真实 PHP 的路径。
2. **片段判据**：判据对象改为解释器实际看到的值（AST 常量求值），拆分写法（隐式拼接、f-string）无法绕过；注释规范化由签名表给定规则。**闭合**。
3. **执行准入全覆盖**：明文"全部产品进程及其子孙""不存在绕过受管通道的路径"，并扩到构建 VM 内产品下发的辅助程序；业务构建划界保留；我方上轮 H22-01 的缺口闭合。**闭合**。
4. **现行版本与 Run 创建复核**：取值来源（策略版本绑定的 HLD 版本，随签名表发布）与复核时点（Run 创建时，与 digest 比对同一检查）均明确。**闭合**。
5. **§13 P0 分批口径**：与 09 §3.1、M0b 三处一致；mock 核心 schema 须先通过的规则写入 P0 行。**一致**。

本轮 HLD 无新 issue。

## 任务 C：01 v0.23 逐项核对

1. **锁存约束所有负向结案**——逐条反例走查：
   - *部分发布后远端撤回*：部分出现报告 → 锁存真；之后全 absent：走 C-11a → 不作负向映射、置 manual_only 转人工；走 C-10a（对账）→ 防御分支不授予许可、记 indeterminate；走 C-11 → "全 absent 只允许 confirm_not_released"被锁存压制，只允许 keep_unknown/confirm_released。三通道结论一致，无重复发布路径。
   - *乱序报告*：同 task 只探测受"同 token 至多一个 intent"与 probe_seq 约束，同一时刻至多一个在飞，正常不会并发；kill/重放格（CF-AUTH-20j R22）断言先并入后判定、锁存不被改写。即使出现旧报告晚到，Run 若已按全 absent + 静默负向关闭，迟到的 appeared 观测由冻结核心的 post-close correction（迟到检出）通道兜底——本轮改动未削弱该通道。
   - *重启*：锁存持久化于 AuthorizationRecord，重启不清零（CF 含 kill 点）。
   - *强制探测*：origin = operator_force 的报告同样先并入锁存再判定，无例外通道。
   - **先并入后判定**的顺序保证同一份报告里的 appeared 先生效（Codex 方案要点），消除"同一报告先判出口后落锁存"的竞态。
2. **证据覆盖**：confirm_not_released 要求 target_refs 并集恰等于全部目标；probe_report 型的 target_refs 由编排生成（提交方填写无效）；external_record 型由运维逐目标声明。无部分覆盖放行。
3. **target_ref 与校验拆分**：算法确定（canonical_json 摘要）、去重（manifest 内与报告内均拒）、②（载荷自身一致性，不落 receipt）与⑤（与 manifest 双射，落 receipt 不改锁存）的拆分使"修正后重试"与"正式拒绝"两态可区分；probe_targets 恒等于全部目标使探测无目标遗漏；RunSummary.release_targets 给出结案呈现。
4. **K4③/K5**：已放行 intent 的重送明确不受暂停影响（期限已在走，不制造新 deadline）；K5 判定顺序 ③→②→① 使"manual_only + dispatch_paused"类组合唯一落到"已失去资格"。
5. **strategy_managed**：置位/清除/不变式齐备，hello 扫描过滤与括注一致；替换策略不实现 isolating 时契约行为仍确定。
6. **dev12 与 CF R22 格**：版本递增与模型变更一致；五个用例的 R22 格覆盖上述全部要点。

发现 1 条 NIT（K23-01，措辞），不影响基线结论。

## 任务 D：09 v0.3 逐项核对

1. **分批口径与批次覆盖**：M0b 与 HLD §13 P0 一致；第一批新增条目覆盖 Demo 六步（启动=focus_modules/sys.scheduler、构建=BuildReport/ImageReport 与 mic 最小 image.*、AI 修复=Diagnosis/ai_draft/AI 证据、空壳 Agent=注册按 mode、审批发布=acknowledged_gaps/release_evidence/ReleaseOutcomeRequest 逐目标观测、可靠性=E-02/恢复 (a)）；第二批含 P4 mock 核心 schema。逐条映射的键（第 7 组原文编号）、留存位置（与开发状态文件同目录）、完成日期（M0a 前）齐备。
2. **Demo 故障分支**：只检测只告警（不退役不计数）、宽限期、按核销状态分流、"人工处理"的边界（不得直接改账本）、kill 时点矩阵、Approval 与 broker 分行降级——均明确且与 01 语义一致（C-09②、publishing 保持、不伪造远端结果）。
3. **回放记录**：来源验收 id + 出内网密级核对 + 无记录标 FakeLLM，写入 §4.5 与降级表两处。
4. **D23 部署切片**：首次部署前验收项与降级行齐备，且明确"不得以一次观测无命中代替执行准入"。
5. **gate 对照表**：位置与三个完成日期明确。
6. **VD 措辞**：已改为"除 VD 外"，与 VD 排在 M3（9–10 月）一致。

本轮 09 无新 issue。

## 新 issue 清单

| 编号 | 等级 | 定位 | 问题与依据 | 候选改动（diff） | 副作用分析 | 配套测试/夹具 |
|------|------|------|-----------|-----------------|-----------|--------------|
| K23-01 | NIT | 01 §2.2d S2"通道状态"段（R22 同步句） | 句子被改残："自此当前实例的一切新出向（新任务、其他成员、hello 扫描与 尚未放行的暂缓项与 release_probe_dispatch；已放行 intent 的同 request_id 重送不在此列，R22）写 intent 后暂缓"——"hello 扫描与 尚未放行的暂缓项与 release_probe_dispatch"语法不通（双"与"、多余空格），且"尚未放行的暂缓项写 intent 后暂缓"自我循环（暂缓项本就是已写 intent 的）。语义可从上下文推断（=新产生的 execute 与 probe 派发），不至于实现错误，但措辞须修。 | ```diff- 自此当前实例的一切新出向（新任务、其他成员、hello 扫描与 尚未放行的暂缓项与 release_probe_dispatch；已放行 intent 的同 request_id 重送不在此列，R22）写 intent 后暂缓；+ 自此当前实例的一切新出向（新任务、其他成员与 hello 扫描产生的 execute 与 release_probe_dispatch；已放行 intent 的同 request_id 重送不在此列，R22）写 intent 后暂缓，已在暂缓中的项维持暂缓；``` | 纯措辞修复，消除循环表述；不改变任何行为语义（暂缓项在 draining 期间本就走 K5 放行复核、结果为"仍须暂缓"）。 | 无需新增用例；CF-STR-03（通道排空）已覆盖语义。 |

## 总结

三份处置表忠实、计数正确、归属与原意见一致。HLD v2.13 的 Q1–Q4 与 §13 P0 分批口径全部落实且机械可执行，**HLD 可以定稿**。01 v0.23 的 Z1 把锁存约束扩展到全部负向结案通道（自动映射、对账防御、人工裁决三处结论一致，先并入后判定），我方上轮的 MAJOR 完整闭合，K4③/K5/strategy_managed/targets 校验均严密，仅余一句措辞 NIT——**01 v0.23 可以作为核心契约的开发基线**。09 v0.3 的 W1–W6 全部落实，分批口径与 HLD 对齐、Demo 故障分支与降级不破安全底线——**09 v0.3 可以作为排期基线**。
