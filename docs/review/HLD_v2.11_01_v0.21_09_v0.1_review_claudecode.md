# HLD v2.11 + 01_Contract_Spec v0.21 + 09_Phased_Dev_Plan v0.1（第二十一轮定向复审）— Claude Code

**评审方**：Claude Code　**日期**：2026-11-11
**对象**：
- docs/00_Framework_HLD_v2.11.md：仅附录 A28 所列改动（D23、§11.2、§11.3、附录 B 第 7 组新增项）
- docs/01_Contract_Spec_v0.21.md：仅 A3 中 v0.21 一条所列改动（§2.2d K2 / K3 / K4 / K5 与计划性回收、§5.1 人工裁决与 AdjudicationEvidence、§2.5 DispatchReceipt / CrossTaskBreaker 新字段、§6.5 CF-AUTH-20g/i/j/k/n/o/q 与 CF-STR-03）
- docs/09_Phased_Dev_Plan_v0.1.md：新文档，全文

**输入**：
- HEAD `b69d747a645ef798045b260ecdc8b9d1e9cca1e0`（与 origin/main 一致）
- 另读：HLD_v2.10_review_disposition.md、01_v0.20_review_disposition.md、上一轮三家原始意见（只核对处置是否忠实与计数）；HLD §13 / §14 用于核对 09

**方法**：
- 逐句 diff（v2.10→v2.11、v0.20→v0.21），沿直接关联条款走查。
- 09 对照 HLD §13 gate、§14 风险登记与 01 的交付要求逐行核对。
- 时间线为手工推演，未运行脚本，未启动构建、测试或索引；命令均以 `nice -n 19 ionice -c3` 运行。

**约束遵守**：未访问 Quickbuild，未读本轮其他评审方意见，未修改被审文档、处置表或他方文件。

## 结论表

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.11（A28） | **GO** | 0 | 0 | 1 | 1 |
| 第二部分：01 v0.21（A3 v0.21） | **NO-GO** | 0 | 1 | 1 | 1 |
| 第三部分：09 v0.1（全文） | **GO** | 0 | 0 | 5 | 1 |
| 同步项（不计入结论） | — | 0 | 0 | 0 | 0 |

**第二部分唯一的 MAJOR（C21-01）：线上模型无法表达"部分目标已出现"，新加的约束因此没有输入。**
- 01 规定"多目标发布中部分目标已在远端出现 → 只能上报 indeterminate"，而 ReleaseProbeReport / ReleaseReconcileReport 只有三值 `probe` 加不透明的 `remote_refs`。
- 编排因此分不清"部分已出现"和"完全不确定"。v0.21 新增的"已记录或本次结果表明部分目标已出现 → 不允许 confirm_not_released"无法机械判定。
- 结果是：运维附一条外部记录、确认原 holder 静默，就能对一次部分已发布的任务判 confirm_not_released。开发者重提后，已发布的那些目标会被再次发布。
- 另外，约束只引用 ReleaseProbeReport，没有覆盖恢复臂对账上报的 ReleaseReconcileReport。
- 修正是局部的：报告增加逐目标观测字段，约束改为读取它，并覆盖两种报告。

**第三部分**的五个 MINOR 集中在两处：
- Demo 的安全前提没有写全：ClineSR CLI 的 OS 层约束没有列入、也没有排在内网首次联调之前；
- 契约 v1.0 的定稿时间与 CI Agent 的落地顺序违反 D10。

计划结构本身可行。

## 负责人七项裁决判断表

本轮改动不触及七项裁决的语义；D23 是负责人前提，只核对落地。09 把裁决落到日历上，判断时一并考虑。

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时必须出报告、不得当通过 | **成立** | 两路共用同一 series、汇合点唯一；超时显式化，堵住"超时 = 通过"这一最难察觉的漏检。09 §4.1 第 5 条与 §4.2 把"超时、重试、未完成项全部显式呈现"列为 Demo 验收，落地一致。代价：报告与审批首屏信息更多。 |
| ② | Quickbuild 默认取最新 Profile 快照，在 Run 启动时固定 | **成立** | 启动时固定，同一 Run 可复现，"最新"如实呈现。代价：快照越新，与构建根的差距越大，可能出现与 patch 无关的构建失败；09 把 Quickbuild 放在 4 月按证据等级验收，在此之前不承担这一风险。 |
| ③ | Profile 严格匹配，加小改动复用预案 | **成立** | 严格匹配保证优化输入可解释；复用预案缺省关闭，09 §6 7 月"非劣评估，满足条件才开启"与之一致。代价：Profile 失效时多一次采集，依赖板子自动化。 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | 范围写进 Run 与报告，"受影响但不在范围内"单列。代价：漏测风险取决于模块登记表质量；09 把登记表内容列为业务部门 2027-02-28 的交付，时间合理。 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | 09 原则 2"有 AI / 无 AI 两条路径、以测试结果说明"把这条裁决落成了验收方式，Demo 与 M2 都有对应条目。代价：需要维护真实失败样本集并报告误修率，效果不足时也要如实呈现。 |
| ⑥ | Quickbuild 可指定 Base CL，否则默认最新，并读回核对 | **成立** | 读回核对先于撤销，base_mismatch 不可冒充成功。代价：后端能力未验证时只能用本地后端（09 §9 已登记）。 |
| ⑦ | 超时后重试成功可以发布，但须审批人逐条确认 | **成立** | 09 §4.1 第 5 条把"重试成功的条目须审批人逐条确认"列入 Demo 审批证据。代价：审批负担随重试次数增加。 |

---

## A. 处置落实

### HLD v2.10 处置表（V1–V4）

| # | 处置要求 | 正文落点 | 判断 |
|---|---|---|---|
| V1 | 纯数据按文件、Python 扫描器与测试按命中片段；镜像与主机只对扫描器按文件 digest 免除；文档与合成清单不得入镜像 | §11.2 L877"粒度（v2.11）""适用范围"；§11.3 L880 v2.11 追加 | 已落实。"命中片段是检测签名"缺机械谓词，扫描器的 `.pyc` 不在 digest 表内（H211-01） |
| V2 | "调用"按声明 + 依赖闭包 + E0 子进程观测；独立构建主机同口径；current_digest 从当前实际状态重算，不得复制旧记录 | §11.2 主机扫描口径、"安装清单与比对（v2.11）"；B-7 L985 | 已落实。子进程观测只在 E0 做一次，重新验收时是否重做未写（H211-02） |
| V3 | 例外条目含批准它的 HLD 版本，且须同时列在该版本 D23 的"已批准例外"表中；当前为无 | D23 L124 | 已落实。"该版本"指批准版本而非现行版本，撤销路径不清（H211-02） |
| V4 | 主机安装集未通过 → deploy 验收失败，其间不能创建 Run | §11.2"例外与复核" | 已落实 |

计数核对：Kimi 1 NIT、Codex 2 MINOR、Claude Code 2 MINOR + 1 NIT，合计 6 条，归并为 4 个问题，其中 2 处合并。**准确。**

"采用谁的方案"核对：
- V1 取本方"镜像与主机只按扫描器文件 digest 免除、文档不得入镜像"；
- V2 取本方"调用按声明 + E0 观测 + 独立构建主机"；
- V3 取本方"双处比对"。

均与本方原意见一致。

### 01 v0.20 处置表（W1–W7）

| # | 处置要求 | 正文落点 | 判断 |
|---|---|---|---|
| W1 | ①已发生 → 只允许 confirm_released；部分出现 → 不允许 confirm_not_released ②暂停只禁止自动派发 ③强制探测照常执行，失败才按 unknown ④origin = operator_force 与运维请求绑定，重放只探测一次 ⑤证据类型化，内部记录不计入 | §5.1 L648；AdjudicationEvidence / AdjudicateRequest L637–638；DispatchReceipt.origin L324；K3 L194；C-11 guard L180；CF-AUTH-20j | ②③④⑤已落实。①的"部分出现"在报告模型中不可表达，约束也未覆盖对账报告（**C21-01**） |
| W2 | 编排自动发起的两类计划回收计 K2；isolation_drain 只允许执行快照为空；删去"计数上限先触发"；替换策略的其他自动循环须纳入上界；等待旧 holder 不属于自动恢复 | L185；① L189；K2 L193；CF-AUTH-20n | 已落实。在任意归因策略下有界，见 C2 |
| W3 | 期限停滞暂停新 execute 派发，唤醒 = 人工恢复或一次正常结案，授权到期可见关闭，已核销不受影响 | K4 ③ L195；CrossTaskBreaker.dispatch_paused L337；CF-AUTH-20i | 已落实。与 K5"放行复核不通过即作废"的交互未闭合（C21-02） |
| W4 | 放行复核不通过即作废；暂停自动探测同事务作废暂缓自动 probe | K5 L199；K3 L194；CF-AUTH-20o | 已落实。暂停派发是否算"复核不通过"未写（C21-02） |
| W5 | 熔断用例 5→6 登记、4→5 不登记；影响上限用例拆为预算单元测试与 NullAttribution 端到端 | CF-AUTH-20g、20i | 已落实 |
| W6 | DispatchReceipt.reservation_seq；三处正文改为通用表述 | L200；L325；L213；L219；① L189 | 已落实。recovery_mode 枚举与 hello 扫描过滤条件仍直接写 `isolating`（C21-03） |
| W7 | K2 限定为自动路径，运维强制探测可超限但不产生自动动作 | K2 L193；CF-AUTH-20q | 已落实，与 K3 一致 |

计数核对：Kimi 1 MINOR + 1 NIT、Codex 2 MAJOR + 1 MINOR、Claude Code 1 MAJOR + 3 MINOR + 1 NIT，合计 10 条，归并为 W1–W7 共 7 个问题。**准确。**"4 处合并"：W1、W2、W5 明写合并，W4 取本方方案并吸收 Codex 的配套要求，按 4 处计可以接受。

"采用谁的方案"核对：
- W1 取本方的③与⑤；
- W2 取本方"isolation_drain 只允许空快照、等待不属于自动恢复"；
- W3、W4、W6 分别对应本方 C20-03、C20-04、C20-05 的候选改动。

均一致。

---

## B. 第一部分：HLD v2.11 D23 核对

| 检查项 | 判断 |
|---|---|
| 按命中片段分类会不会放过真实 PHP | 不会放过可执行 PHP：解释器、包、后缀、shebang、composer 清单都不在豁免内，伪装为 `.py` 的 PHP 源无法被 Python tokenizer 解析，按"无法确认分类即拒绝"处理。但"命中的字符串常量是检测签名或期望值"是语义判断，没有给出机械谓词：一个装着完整 PHP 程序的字符串常量也可以自称"期望值"（H211-01） |
| 镜像与主机扫描只按扫描器文件 digest 免除，可否执行 | 源文件与规则表可以。但 Python 安装后生成的 `__pycache__/*.pyc` 含同样的字符串常量，其 digest 随解释器版本变化，不在随策略版本发布的 digest 表内，主机扫描会在 `.pyc` 上自触发（H211-01） |
| "调用"按声明 + E0 子进程观测有无漏洞 | 口径成立。观测只在 E0 做一次；合规升级被调用工具后重新验收时，是否重做观测未写，新增的间接调用会漏过（H211-02） |
| current_digest 从当前实际状态重算能否机械执行 | 能。规范化输入（包、版本、架构、文件内容摘要、符号链接目标、闭包成员）与采集来源（包数据库重新解析、文件树重算）都已写明，且禁止复制旧值 |
| 例外双处比对有无歧义 | 有一处："须列在**该版本**本条的'已批准例外'表中"。按字面比对的是批准它的 HLD 版本，而不是现行版本：后续 HLD 版本撤销该例外后，门禁仍按旧版本比对、继续放行到到期日。另外表格需要机器可读的格式（H211-02） |

### 第一部分问题

#### H211-01 [MINOR] "命中片段是检测签名"缺机械谓词；扫描器的 `.pyc` 不在 digest 免除范围内

- **位置**：HLD v2.11 §11.2 L877（"粒度（v2.11）""适用范围"）。
- **依据**：
  - "非 PHP 语言写的扫描器与测试源码（如 Python）按**命中片段**分类——只确认命中的字符串常量或注释是检测签名或期望值、不作为 PHP 程序或可执行模板的输入"。
  - "镜像与主机扫描只对扫描器自身的规则表与源码按其**文件 digest**（随策略版本发布）免除文本信号"。
- **问题**：
  1. "是检测签名或期望值"需要人判断。tokenize 能机械确认"命中处位于字符串常量或注释内"，但确认不了"它是签名"。一个内容为完整 PHP 程序的字符串常量（例如测试夹具在运行时写到临时目录的 PHP 文件内容）同样位于字符串常量内。测试夹具运行时生成负向例是 v2.9 起的要求，所以这类常量必然存在，且长短不一，分类规则须能机械区分。
  2. 扫描器装进安装前缀后，Python 会生成 `__pycache__/*.pyc`，里面含同样的字符串常量。pyc 的 digest 随解释器小版本与优化级别变化，不在随策略版本发布的 digest 表内，主机扫描会在 pyc 上命中"`<?php` 标记"。
- **候选改动**：

```diff
--- HLD §11.2 粒度（v2.11）
- 非 PHP 语言写的扫描器与测试源码（如 Python）按**命中片段**分类——只确认命中的字符串常量或注释是检测签名或期望值、不作为 PHP 程序或可执行模板的输入，
+ 非 PHP 语言写的扫描器与测试源码（如 Python）按**命中片段**分类——机械谓词：命中处经该语言 tokenizer 确认位于字符串常量或注释内，且该常量 / 注释与随策略版本发布的签名表中某一项**完全相等**（签名表只含判定信号本身，如 `<?php`、`composer.lock`、`.phar`），或位于扫描器测试目录、且所在文件不含 PHP 解释器调用；负向夹具在运行时拼接生成 PHP 内容，不以单个完整 PHP 程序的字符串常量出现在源码中；不满足即按文本信号判定；
--- HLD §11.2 适用范围
- 镜像与主机扫描只对扫描器自身的规则表与源码按其**文件 digest**（随策略版本发布）免除文本信号，
+ 镜像与主机扫描只对扫描器自身的规则表与源码按其**文件 digest**（随策略版本发布）免除文本信号；扫描器以预编译字节码随包发布（hash-based pyc，PEP 552，内嵌源文件哈希），pyc 按"内嵌源哈希属于已发布 digest 表中的源文件"免除，运行时不另行生成 pyc，
```

- **副作用**：
  - 签名表须与扫描规则一起维护；负向夹具写法受约束（运行时拼接），只是测试代码的风格要求。
  - 改用 hash-based pyc 发布扫描器，是一次性的打包约定。
- **配套测试 / 夹具**：§11.3 增加以下用例：
  - 扫描器源码中的 `"<?php"` 常量 → 通过；
  - 测试源码中含完整 PHP 程序的字符串常量 → 失败；
  - 安装前缀含扫描器 hash-based pyc → 通过，pyc 内嵌源哈希不匹配 → 失败。

#### H211-02 [NIT] 例外比对的是批准版本而非现行版本；重新验收时是否重做子进程观测未写

- **位置**：HLD v2.11 D23 L124；§11.2 L877。
- **依据**：
  - D23："同一条目……须列在**该版本**本条的'已批准例外'表中"；"例外以登记条目（……批准该例外的 HLD 版本）"。
  - §11.2："E0 预检对这些工具执行一次子进程观测……观测结果写入预检报告并进入声明清单"；"合规的依赖更新也须先重扫、更新批准记录"。
- **问题**：
  1. 比对批准版本时，负责人在后续 HLD 版本中撤销某例外，门禁仍会在旧版本表中找到该条目并放行到到期日。应比对现行 HLD 版本。门禁还需要从 D23 中解析表格，格式应机器可读。
  2. 子进程观测只在 E0 做一次。合规升级被调用的工具后重新验收时若不重做，新版本工具新增的间接调用不会进入声明清单。
- **候选改动**：

```diff
--- HLD D23
- **且同一条目（工具名 + 安装件 digest）须列在该版本本条的"已批准例外"表中**
+ **且同一条目（工具名 + 安装件 digest）须同时列在批准版本与现行 HLD 版本本条的"已批准例外"表中**（表格按固定列序书写，门禁解析；现行版本中删除即撤销）
--- HLD §11.2
- 以及 E0 预检对这些工具执行一次子进程观测
+ 以及对这些工具执行子进程观测（E0 预检时，以及任何被调用工具的安装件 digest 变化导致重新验收时）
```

- **副作用**：撤销例外即时生效；重新验收多一次观测，只在工具变化时发生。
- **配套测试 / 夹具**：
  - 例外在批准版本表中、现行版本已删除 → 拒绝；
  - 升级 gbs 后重新验收 → 重做观测，新增的间接调用工具进入声明清单并参与扫描。

---

## C. 第二部分：01 v0.21 核对

### C1. 人工裁决：还有没有路径能把已发布的任务判成未发布

| 路径 | 结论 |
|---|---|
| 已落账 confirmed_happened 的探测报告 → 只允许 confirm_released | 已封住（ReleaseProbeReport 是三值中的确定值，可机械判定） |
| 暂停自动探测后跳过强制探测 | 已封住（强制探测照常执行，origin = operator_force、绑定运维请求、重放只一次） |
| 只用内部记录满足"证据非空" | 已封住（evidence_refs 只收 probe_report / external_record，内部记录放 internal_refs） |
| 强制探测失败 → unknown → 附外部记录 + 静默 → confirm_not_released | 人工判断，契约允许，合理 |
| **多目标部分已出现** | **未封住**：报告模型把部分出现折叠为 indeterminate，约束无输入；对账报告不在约束范围内（C21-01） |
| 非 manual_only 分支（强制 probe 后 unknown）的已记录观测约束 | 约束写在 manual_only 段落内，适用范围不明（并入 C21-01） |

### C2. K2 能否在任意归因策略下保证每个任务有界

能。
- 任务域事件与编排自动发起的两类计划回收都对快照并集计 K2；isolation_drain 只允许在执行快照为空时发起，因此不能用来回收执行任务。
- Codex 上一轮的反例（只探测 ACK 后永不报告、反复排空换实例）由只探测快照中的 K2 计数终止，CF-AUTH-20n 已覆盖。
- retire_requested 对每个实例至多一次：被回收后，其余 indeterminate 授权的持有者都是已退役实例。
- planned_restart 由人发起，不计入是合理的。
- "替换策略若引入其他自动回收或重派循环，须同样纳入本上界或给出持久化的停止状态"把替换策略也约束住了。
- "自动路径上界"与"运维强制探测可超限但不产生自动动作"在 K2、K3、§5.1 三处表述一致。

### C3. K4 期限停滞暂停

- **唤醒**：人工恢复或一次正常结案。broker 卡死时没有正常结案，暂停保持到人工处理；远端间歇变慢时，暂停与恢复交替，每轮至多耗费 `max_distinct_task_deadlines` 个任务各一次 loss。可接受。
- **授权过期**：按 K5 可见关闭。闭合。
- **已核销任务不受影响**：闭合。
- **饿死**：没有。暂停是可见状态，唤醒来源持久化。
- **绕过**：
  - K5 放行事务的复核清单里没有 `dispatch_paused`，渠道唤醒放行暂缓 execute 时会绕过暂停；
  - 若实现者把它加进复核清单，按"复核不通过即作废"，暂缓项会被作废，而暂停解除后新任务没有定义的"发送点"来重新生成。

  两种读法都不闭合（C21-02）。"新的 execute 派发"是否包括未核销任务的 hello 扫描重派，也未写明（并入 C21-02）。

### C4. K5：作废、暂停时作废自动 probe、reservation_seq

- 放行复核不通过即作废，条件恢复后由发送点重建。对 execute 而言：已核销等静默者由周期任务重试，任务终结者无需重建，转 indeterminate / manual_only 者走 probe 路径。每格一个出口，**唯一例外是 K4 暂停（C21-02）**。
- 暂停自动探测时同事务作废暂缓的自动 probe，运维强制探测可写入：闭合。
- reservation_seq 记录在 DispatchReceipt 上，释放与回调按它 CAS，同一 task 在同一 epoch 上两次当选也能区分：闭合。

### C5. 契约正文是否还依赖参考策略字段、或把策略目标写成保证

- 未见把策略目标写成保证的句子；K2 已删去"计数上限先触发"。
- 仍直接依赖策略字段的有两处：
  - §2.5 ReleaseTaskState.recovery_mode 的枚举含 `isolating`；
  - 持有者更替重派扫描的过滤条件写 `recovery_mode ∉ {isolating, manual_only}`。

  括注已改为通用表述，但过滤条件本身仍是策略值（C21-03）。

---

## D. 第二部分：时间线走查

符号说明：
- P：毒丸。B：无辜 task。U：处于 indeterminate、在飞只探测的 task。
- "✓"表示出口唯一；C21-xx 表示该格出口不唯一或违反底线，详见对应问题。

| 时间线 | 交叉点 | 出口 | 判定 |
|---|---|---|---|
| 正常 | 无故障；K4 未暂停 | 放行写 awaiting_consume → 终局 | ✓ |
| 正常 | K4 暂停期间新任务派发 | 写 intent 后暂缓；渠道唤醒时放行复核是否包含暂停未写 | **C21-02** |
| 正常 | 暂停期间未核销授权到期 | K5 授权过期，可见关闭 | ✓ |
| 正常 | 编排重启 | 重启扫描全部暂缓项；旧 epoch 的经替代协议放行 | ✓ |
| 核销前 | intent 后崩溃，快照 {P} | 任务域；K1 由策略决定；K2 +1 | ✓ |
| 核销前 | intent 前崩溃，两份快照均空 | start_health | ✓ |
| 核销前 | K4 暂停期间未核销任务的 hello 扫描重派 | "新 execute"是否包括重派未写 | **C21-02** |
| 核销后发生前 | 快照 {P, B}，NullAttribution | 各 affected +1，至多 6 次后按 K3 分流 | ✓ |
| 核销后发生前 | K3 耗尽 | 已核销 → manual_only；未核销 → dispatch_loss_exhausted | ✓ |
| 核销后发生前 | K4 暂停 | 已核销任务的恢复与对账不受影响 | ✓ |
| 发生后崩溃 | 恢复臂对账得全部已发生 | released 映射 | ✓ |
| 发生后崩溃 | 多目标部分已出现，对账报 indeterminate，随后 manual_only，强制探测失败 | 运维附外部记录 + 静默 → confirm_not_released 被允许 | **C21-01** |
| indeterminate | U 达到上限 | manual_only + suspended，同事务作废暂缓自动 probe | ✓ |
| indeterminate | 裁决：已有 confirmed_happened 报告 | 只允许 confirm_released | ✓ |
| indeterminate | 裁决：强制探测（operator_force）重放 | 复用同一次探测与结果 | ✓ |
| indeterminate | 裁决：强制探测令实例崩溃 | K2 +1（可超限），按 unknown；只有 internal_refs → confirm_not_released 被拒 | ✓ |
| indeterminate | 只探测 ACK 后永不报告、反复排空 | isolation_drain（执行快照空）计 K2，U 达上限后暂停 | ✓ |
| 实例存活、单任务失联 | 期限到期，快照 {B} | 任务域，K2 +1 | ✓ |
| 实例存活、单任务失联 | 不同 task 期限到期达阈值 | K4 ③ 暂停新 execute，告警 | ✓（与 K5 的交互见 C21-02） |
| 实例存活、单任务失联 | 执行快照非空时发起 isolation_drain | 拒绝提交并告警 | ✓ |
| 熔断 | 两个 task 零计数、affected 5→6 | 两者登记，缺省阈值下熔断 | ✓ |
| K5 预约 | 同一 task 同 epoch 两次当选，旧回调晚到 | reservation_seq 不匹配，不释放 | ✓ |
| 任意 | manual_only 之后 | 无自动执行路径；只探测只作证据 | ✓ |

### 第二部分问题

#### C21-01 [MAJOR] 报告模型无法表达"部分目标已出现"，新约束没有输入；约束未覆盖对账报告与非 manual_only 分支

- **位置**：01 v0.21 §5.1 L648（已记录观测的约束）；§5.1 ReleaseReconcileReport L627、ReleaseProbeReport L631；§2.2a"多目标部分出现只能报 indeterminate"；C-11 guard L180；CF-AUTH-20j。
- **依据**：
  - §5.1 L648："**已记录观测的约束（R20）**：本授权任一已落账的 ReleaseProbeReport 为 confirmed_happened → 只允许 `confirm_released`……**已记录或本次结果表明部分目标已出现 → 不允许 `confirm_not_released`**"。
  - 模型：`class ReleaseProbeReport(BaseModel): task_id: str; probe: Literal["confirmed_happened","confirmed_not_happened","indeterminate"]; remote_refs: list[str] = []; probe_seq: int`；ReleaseReconcileReport 同构（无 probe_seq）。
  - §2.2a："**多目标发布中部分目标已在远端出现 → 只能上报 indeterminate**（不得报 confirmed_happened 或 confirmed_not_happened）"。
- **问题**：
  1. **无输入**：部分出现在线上被折叠为 indeterminate，与"完全不确定"不可区分，remote_refs 是不透明字符串。新约束"表明部分目标已出现"因此无法机械判定，CF-AUTH-20j 的"部分目标已出现 → 不允许 confirm_not_released"也构造不出符合模型的夹具。
  2. **反例**：多目标发布，目标 1 已发布、目标 2 未发布时 broker 崩溃。
     1. 恢复臂对账报 indeterminate（按 §2.2a 只能这么报）。
     2. 随后 manual_only，裁决前强制探测因实例退役失败 → unknown。
     3. 运维附一条外部记录（例如目标 2 未合入的截图），原 holder 已静默 → confirm_not_released 被允许。
     4. Run 以 release_failed 关闭；开发者重提后，目标 1 会被再次发布。

     这正是"把已发布的任务判成未发布"，且属于范围调整时三家要求留在契约里的底线。
  3. **范围**：
     - 约束只引用 ReleaseProbeReport。部分出现最常见的来源是恢复臂对账（ReleaseReconcileReport），它不在约束内。
     - 约束写在 manual_only 段落中。非 manual_only 的"强制 probe 后 unknown"分支是否适用，没有写明；W1 处置称"用于所有裁决分支"的只是证据类型化。
- **候选改动**：

```diff
--- 01 §5.1 模型
+ class TargetObservation(BaseModel): target_ref: str; state: Literal["appeared","absent","unknown"]   # 逐目标观测（R21）
- class ReleaseReconcileReport(BaseModel): task_id: str; probe: Literal["confirmed_happened","confirmed_not_happened","indeterminate"]; remote_refs: list[str] = []
+ class ReleaseReconcileReport(BaseModel): task_id: str; probe: Literal["confirmed_happened","confirmed_not_happened","indeterminate"]; remote_refs: list[str] = []; targets: tuple[TargetObservation, ...] = ()   # 多目标时必填；probe 与 targets 须一致：全部 appeared ⇔ confirmed_happened，全部 absent ⇔ confirmed_not_happened，其余 indeterminate（编排校验，不一致即 E-CP-VALIDATION）
- class ReleaseProbeReport(BaseModel): task_id: str; probe: Literal[...]; remote_refs: list[str] = []; probe_seq: int
+ class ReleaseProbeReport(BaseModel): task_id: str; probe: Literal[...]; remote_refs: list[str] = []; probe_seq: int; targets: tuple[TargetObservation, ...] = ()   # 同上
--- 01 §5.1 已记录观测的约束
- **已记录观测的约束（R20）**：本授权任一已落账的 ReleaseProbeReport 为 confirmed_happened → 只允许 `confirm_released`（与本次结果冲突时以已发生为准并记审计）；已记录或本次结果表明部分目标已出现 → 不允许 `confirm_not_released`。
+ **已记录观测的约束（R20，R21 补逐目标与适用范围；适用于全部裁决分支）**：本授权任一已落账的 ReleaseProbeReport 或 ReleaseReconcileReport 为 confirmed_happened → 只允许 `confirm_released`（与本次结果冲突时以已发生为准并记审计）；任一已落账报告或本次结果中有目标 `state = appeared` → 不允许 `confirm_not_released`（部分已发布的发布只能经 keep_unknown 或 confirm_released 收尾，后者在 RunSummary 中逐目标列出实际状态）。
```

- **副作用**：
  - 两个报告模型各增一个可空字段（dev10 → dev11），broker 的 adapter 须逐目标返回观测。只读查询本来就是逐目标做的，实现成本低。
  - 部分发布的 Run 不能以"未发布"关闭。须人工以 confirm_released 收尾，并在 RunSummary 中呈现逐目标状态；后续补发未发布的目标走新的 Run。这是安全方向的代价。
- **配套测试 / 夹具**：
  - CF-AUTH-20j 改为可构造的夹具：对账报告 indeterminate + targets = [appeared, absent]，随后 manual_only、强制探测失败 → confirm_not_released 被拒，keep_unknown / confirm_released 允许；
  - 非 manual_only 分支同例 → 同样被拒；
  - probe 与 targets 不一致（如 confirmed_not_happened + appeared）→ E-CP-VALIDATION；
  - 契约序列化往返含 targets。

#### C21-02 [MINOR] K4 期限停滞暂停与 K5"放行复核不通过即作废"的交互未闭合

- **位置**：01 v0.21 §2.2d K4 ③ L195；K5 放行事务 L198、作废 L199。
- **依据**：
  - K4 ③："置 CrossTaskBreaker.`dispatch_paused = true`：**暂停新的 execute 派发**——未核销 task 的新 execute 写 intent 后暂缓（按 K5 有持久化唤醒，唤醒 = 显式人工恢复或一次正常结案……）"。
  - K5 放行："共同复核：当前 live epoch、task 非终态、独占许可、同 token 至多一个 intent……**execute**：复核 C-09 / ④ 的执行派发条件……及适用的静默条件"。
  - K5 作废："**放行复核不通过**（守卫、模式、暂停条件或通道许可以外的任一条件不满足）时，该暂缓项在放行事务内作废……条件恢复后由相应发送点重新生成"。
- **问题**：
  1. K5 放行的复核清单没有 `dispatch_paused`。暂停期间若渠道唤醒（例如参考策略的隔离头离开，按 K5 先放行全部暂缓项），暂缓的未核销 execute 会被放行，暂停被绕过。
  2. 若实现者把 `dispatch_paused` 加进复核：作废规则中的"暂停条件"指的是哪种暂停没有写（auto_probe_suspended，还是 dispatch_paused）。按"任一条件不满足即作废"，暂缓的新任务会被作废；而暂停解除后，新任务的"发送点"（审批通过后的 release 节点派发）没有定义重新生成的触发点，任务就悬空了。
  3. "新的 execute 派发"是否包括未核销任务的 hello 扫描重派、持有者更替重派，没有写明。按 K4 的意图应包括：它们同样会核销后卡在停滞的 broker 上。
- **候选改动**：

```diff
--- 01 §2.2d K5 放行事务
- **execute**：复核 C-09 / ④ 的执行派发条件（排除 indeterminate 与 manual_only）及适用的静默条件；
+ **execute**：复核 C-09 / ④ 的执行派发条件（排除 indeterminate 与 manual_only）及适用的静默条件；授权未核销且 CrossTaskBreaker.dispatch_paused = true → **保持暂缓**（不视为复核不通过、不作废），其唤醒来源为暂停解除；
--- 01 §2.2d K5 作废
- **放行复核不通过**（守卫、模式、暂停条件或通道许可以外的任一条件不满足）时，
+ **放行复核不通过**（守卫、模式或 auto_probe_suspended 不满足；独占许可与 K4 dispatch_paused 除外——这两种情形保持暂缓）时，
--- 01 §2.2d K4 ③
- **暂停新的 execute 派发**——未核销 task 的新 execute 写 intent 后暂缓
+ **暂停未核销授权的全部 execute 派发**（新派发、hello 扫描与持有者更替重派）——写 intent 后暂缓
```

- **副作用**：无新状态。暂停解除时须对暂缓项写一次唤醒（"一次正常结案"的事务内，或人工恢复的事务内）。
- **配套测试 / 夹具**：CF-AUTH-20i / 20o 增加以下用例：
  - 暂停期间渠道唤醒 → 未核销 execute 保持暂缓、不作废；
  - 暂停期间 hello 扫描重派未核销任务 → 暂缓；
  - 人工恢复 → 暂缓项按序放行；
  - 暂停期间 task 转 manual_only → 暂缓 execute 按模式作废。

#### C21-03 [NIT] 契约正文仍以参考策略的 `isolating` 作为过滤条件与枚举值

- **位置**：01 v0.21 §2.5 ReleaseTaskState L350；持有者更替重派 L219。
- **依据**：
  - L350：`recovery_mode: Literal["active","waiting_holder","isolating","manual_only"]`。
  - L219："扫描全部非终态、且 `recovery_mode ∉ {isolating, manual_only}` 的 release task……（由归因策略独占预约管理的 task 只经该策略的放行入口派发——参考策略 v1 中即 isolating 成员……）"。
- **问题**：
  - 括注已改为通用表述，但过滤条件本身仍是参考策略的取值。替换策略若不用 `isolating`，而用别的方式管理自己的独占成员，hello 扫描会把这些成员当作普通任务重派，绕过其放行入口。
  - 枚举中的 `isolating` 也是策略值。
- **候选改动**：

```diff
--- 01 §2.2d 持有者更替重派
- 扫描全部非终态、且 `recovery_mode ∉ {isolating, manual_only}` 的 release task
+ 扫描全部非终态、`recovery_mode ≠ manual_only`、且不由归因策略独占预约管理（ReleaseTaskState.strategy_managed = false；参考策略 v1 中 isolating 成员为 true）的 release task
--- 01 §2.5 ReleaseTaskState
+     strategy_managed: bool = False                    # 由归因策略的独占预约管理、只经其放行入口派发（R21；契约字段，取代以 recovery_mode = isolating 判断）
```

- **副作用**：多一个布尔字段；参考策略置位规则不变。
- **配套测试 / 夹具**：CF-AUTH-20k 增加一例：替换策略不使用 isolating、只置 strategy_managed → hello 扫描不重派其成员。

---

## E. 第三部分：09 开发计划核对

### E1. 里程碑与 HLD §13 gate 的对应

| HLD 阶段 | §13 gate / 交付 | 09 落点 | 判断 |
|---|---|---|---|
| P0 | 三方 unanimous GO + **总部方案确认**；01 draft freeze；08/09 就绪 | M0（11-20）：HLD 定稿、01 基线、08 / 02 / 09 评审、预检 | 缺"总部方案确认"的日期与形式（P09-03） |
| P1 | 示例流水线加载、逐边界故障注入恢复、外部等待无死锁 | 1 月"P1、P2 gate 通过" | 一致 |
| P2 | conformance 骨架、授权并发 / 双消费、RPC 权限隔离；**Build Gateway 骨架** | 1 月 | Build Gateway 骨架没有排期，4 月才出现（P09-05） |
| P3 | 真实 gbs + mic + 特权构建隔离 E2E + 数据边界 fail-closed + adapter 模拟联调；**ClineSR CLI OS 层约束** | 1–2 月 | 排期一致；但 Demo（12 月）已在内网用真实 ClineSR CLI，OS 层约束未提前（P09-01） |
| P4 | §11.3 全部测试类别 + 真实 UID / 权限 E2E；deploy 资产与 launcher cgroup 契约 | 2 月（M1.5） | 一致；Demo 在内网部署已需要 launcher 与 cgroup 的一部分（P09-02） |
| P5 | contract v1.0：核心 + Compiler / UT / Review / CI 面定稿（D10：未被真实消费者不定稿） | 3 月契约 v1.0；CI Agent v1 在 4 月 | **CI 面在 CI Agent 消费前定稿，违反 D10**（P09-04） |
| P6 | Quickbuild + Gateway 会话注入 + 证据等级表 | 4 月 | 一致 |
| P7 | Benchmark + Optimization，contract v1.1 | 4–5 月、7–8 月 | 一致 |
| P8 | VD 端到端 | 9–10 月 | 一致 |
| §14 R13 | "运维 CLI 对账 / 裁决命令（**交付项，入 09**）" | 无 | **遗漏**（P09-05） |
| §14 R14 | post-close correction、复查窗口周期 probe | 无 | 遗漏（P09-05） |

### E2. 12 月 Demo 的可行性

- **范围**：竖切片的取舍合理：真实构建 + Compiler AI 修复为核心，其余 Agent 用空壳，发布到模拟 gerrit。但"Demo 用到的每个部件都按正式设计实现"加上 01 §2.2d 的完整恢复机制，7 周内不可能全部完成。计划没有界定 Demo 实现的契约子集，也没有要求未实现的恢复路径 fail-closed（P09-02）。
- **范围检查点（12-11）**：
  - 构建隔离方案若到 12-11 才降级，W3（11-23 起）的 LocalGbsBackend 已经依赖它；
  - 降级表没有"两种隔离方案都不可用"一行；
  - Approval / broker（W5 开发）与 Compiler AI 修复本身没有降级行（P09-02）。
- **降级是否放宽安全约束**：表中四项降级本身不放宽。但原则 5 列举的安全底线漏了 ClineSR CLI 的 OS 层约束与数据边界，而 W4 的内网首次联调就要把真实构建日志交给 agentic CLI（P09-01）。
- **回放降级**："用事先录制的真实分析结果回放"时，修复是否成立仍须以真实重新构建验证，计划未写明（并入 P09-02）。

### E3. 依赖、截止时间与风险

关键路径上未写的事项：
- 总部方案确认（P0 gate）；
- 内网主机的特权部署：launcher 的 cgroup v2 委派、systemd 单元、专用 OS 用户、ClineSR 出口规则、构建 VM 所需 KVM，都需要内网主机管理员权限；
- 内网对 Tizen 公开仓库的访问：gbs 构建需要 download.tizen.org 或镜像源，Demo 在内网运行时这是"真实构建"的前提；W1 预检只在开发机上检查 gbs 与 gerrit；
- 模拟 gerrit 的部署位置；
- 内网 LLM 的配额 / 并发；
- 团队人力假设：计划全文没有人力或 AI 开发产能的假设，工作量是否均衡无从判断。

以上见 P09-03。

### E4. 2027 年各月工作量

上半年明显偏重，下半年偏轻：
- 1 月：P1 / P2 补齐到 gate、P3 三项公共模块、三份设计文档（03、06、07）；
- 2 月：P3 余项、P4 全部（E2E、ModuleRegistry、deploy 资产、真实 UID E2E），外加春节一周；
- 3 月：Compiler 完整版、UT v1、Review v1、契约 v1.0；
- 4 月：Quickbuild、Gateway、CI v1、Benchmark v1；
- 5 月：Optimization v1 与 A/B 可复现性验收，而它依赖的增强版 llvm-profgen 同月才完成；
- 下半年：7 月只有 BOLT 评估与非劣评估，11–12 月有余量。

建议把部分 2 月内容前移到 Demo 阶段（Demo 在内网部署本来就需要 launcher 与 cgroup），把 M1.5 后延两周，并给 5 月的 AutoFDO 实测收益留出 6 月缓冲（P09-04）。

### 第三部分问题

#### P09-01 [MINOR] Demo 的安全底线漏列 ClineSR CLI 的 OS 层约束与数据边界，而 W4 就在内网用真实 CLI 分析真实日志

- **位置**：09 §2 原则 5（L32）；§4.3 W1、W4（L77、L80）；HLD §7.1 ClineSRCliProvider "OS 层强制（定案）"、P3 gate"数据边界 fail-closed"。
- **依据**：
  - 09 L32："**安全底线不为进度让步。** 构建隔离（不在宿主以 root 直跑）、发布凭据只在 broker、人工审批、超时不得当通过、不得引入 PHP——Demo 阶段同样遵守"。
  - L80（W4）："内网首次联调：ClineSR CLI 实际分析 2–3 个真实失败"。
  - L77（W1）只做预检："ClineSR CLI 能否在受限用户下以补全模式工作"。
  - HLD §7.1："EvidencePacket 含攻击者可控的日志与源码，间接提示注入可诱导 agentic CLI 执行命令，故参数层关闭之外另设兜底——CLI 以……专用 OS 用户……由 deploy 特权 launcher"。
- **问题**：
  - HLD 把 ClineSR CLI 的 OS 层约束（专用 OS 用户、出口规则、由 launcher 管理、关闭工具）定为安全定案；P3 gate 也有"数据边界 fail-closed"。09 把这两项的实现放在 1 月（P3），但 W4（12 月初）就在内网主机上让真实 CLI 读真实构建日志。这台主机同时运行编排进程与 Ledger。
  - 原则 5 的列举漏掉了这两项，读者会以为 Demo 阶段可以不做。Demo 输入是公开代码与挑选过的失败样本，风险较低，但这正是"安全约束为进度让步"。
- **候选改动**：

```diff
--- 09 §2 原则 5
- 5. **安全底线不为进度让步。** 构建隔离（不在宿主以 root 直跑）、发布凭据只在 broker、人工审批、超时不得当通过、不得引入 PHP——Demo 阶段同样遵守。
+ 5. **安全底线不为进度让步。** 构建隔离（不在宿主以 root 直跑）、发布凭据只在 broker、人工审批、超时不得当通过、不得引入 PHP、**ClineSR CLI 的 OS 层约束（专用 OS 用户、出口规则、由 launcher 管理、关闭工具）与发往 LLM 的数据边界 fail-closed**——Demo 阶段同样遵守，不在降级范围内。
--- 09 §4.3 W3 内网 / 环境列
- | 构建隔离方案落地（同机 VM 或独立构建主机） |
+ | 构建隔离方案落地（同机 VM 或独立构建主机）；内网主机上 ClineSR CLI 专用用户、出口规则与 launcher 拉起方式落地（W4 联调的前提） |
--- 09 §4.3 W4 开发列
- LLM 接入层（外网用 FakeLLM，内网走 ClineSR CLI）
+ LLM 接入层（外网用 FakeLLM，内网走 ClineSR CLI，含 OS 层约束与数据边界 fail-closed，按 P3 设计提前实现）
```

- **副作用**：W3 / W4 多两项工作，大部分是部署配置；与 P09-02 的"Demo 契约子集"一起，可以从 1 月 P3 中提前拿出。
- **配套检查点**：
  - W4 内网联调前检查：CLI 以专用用户运行，工具已关闭，出口仅限内网 LLM 端点；
  - 注入一条诱导执行命令的日志，确认无文件写入或进程派生；
  - 数据边界对未标注来源的载荷拒绝发送。

#### P09-02 [MINOR] Demo 实现的契约子集未界定；未实现的恢复路径未要求 fail-closed；范围检查点偏晚且缺行

- **位置**：09 §2 原则 1（L28）；§4.1 第 6 条（L61）；§4.2（L71）；§4.5（L94–103）。
- **依据**：
  - L28："Demo 用到的每个部件都按正式设计实现，不写一次性演示代码"。
  - L61："演示中途强制结束编排进程后重启……已核销的授权不重复发布"。
  - L96："以下任一项到 12-11 仍未就绪，就按右列降级"。
  - L101："同机构建 VM → 使用独立构建主机"。
- **问题**：
  1. 01 §2.2d（broker epoch、租约、cgroup 回收、DispatchReceipt 协议、K1–K6、恢复臂对账）全部实现不可能在 7 周内完成，但计划没有说 Demo 实现哪个子集。只实现"正常路径 + 编排重启"是合理的，但须写明：未实现的路径（broker 崩溃恢复、对账、只探测）在 Demo 中 **fail-closed**，即 Run 保持 publishing、告警、人工处理，不能自动重派。否则"按正式设计实现"就会变成实现一半的恢复逻辑。
  2. 构建隔离在 W3（11-23）就是 LocalGbsBackend 的前提，到 12-11 才降级太晚；降级表也没有"同机 VM 与独立构建主机都不可用"一行。此时只能放弃真实构建，不能退回宿主 root。
  3. Approval / broker（W5）与 Compiler AI 修复本身没有降级行。
  4. 回放降级须写明"修复 patch 仍以真实重新构建验证"，否则 AI 作用的证据链断了。
- **候选改动**：

```diff
--- 09 §4.1 末尾
+ **Demo 实现的契约子集**：01 的数据模型与 Ledger 落账完整实现；Release broker 实现正常发布路径、epoch 与连接守卫、DispatchReceipt 出向协议；§2.2d 的 broker 崩溃恢复、恢复臂对账、只探测与 K1–K6 在 M1.5 前完成——Demo 期间这些路径 **fail-closed**：broker 失联时 Run 保持 publishing 并告警，不自动重派、不自动结案，由人工处理。Demo 只演示编排进程重启。
--- 09 §4.5 表
+ | 构建隔离（11-27 前须确定可用方案） | 同机 VM 不可用改独立构建主机；两者都不可用 → Demo 不演示真实构建，改为以事先在合规环境中得到的构建日志驱动 Compiler Agent，并如实说明；**不得退回宿主 root 构建** |
+ | Approval 服务 / Release broker | 发布环节改为审批通过即结束、不调用 broker，并如实说明；broker 的正常路径放到 M1.5 |
+ | Compiler Agent 的 AI 修复 | 减为 1 个真实失败；仍须给出有 AI / 无 AI 对比 |
--- 09 §4.5 内网 ClineSR CLI 联调行
- | Demo 在内网主机上用事先录制的真实分析结果回放，并如实说明（同 §4.4 备选） |
+ | Demo 在内网主机上用事先录制的真实分析结果回放，并如实说明（同 §4.4 备选）；回放得到的修复 patch 仍以真实重新构建验证 |
```

- **副作用**：Demo 不演示 broker 崩溃恢复（原计划本来也只演示编排重启）；明确的子集反而减轻 7 周的压力。
- **配套检查点**：
  - 11-27 增加构建隔离检查点；
  - Demo 验收增加一条：kill broker → Run 保持 publishing 并告警，无自动重派。

#### P09-03 [MINOR] 关键路径依赖缺项：总部方案确认、内网主机特权部署、内网对 Tizen 仓库的访问、人力假设

- **位置**：09 §3 M0（L40）；§4.3 W1（L77）；§8（L165–181）；§9（L185–197）；HLD §13 P0 gate。
- **依据**：
  - HLD §13 P0 gate："总部方案确认 + 三方 unanimous GO"。
  - 09 L40：M0 内容不含总部确认。
  - L77：W1 开发机预检 gbs / mic、KVM、gerrit 可达性，内网预检只列 ClineSR CLI、LogAnalyzer 与代码拉取。
  - §8 没有内网主机权限、Tizen 仓库访问。
- **问题**：
  1. **总部方案确认**是 P0 gate 的一半，计划没有日期，也没写由谁、以什么形式确认。若总部只在 12-29 Demo 时才看方案，P0 实际上没有关闭。
  2. **内网主机特权部署**：Demo 在内网主机运行（§4.4 建议），需要 launcher 的 cgroup v2 委派、systemd 单元、专用 OS 用户、出口规则、KVM，这些都要主机管理员权限，计划没有列为依赖。
  3. **内网对 Tizen 仓库的访问**：gbs 构建要从 download.tizen.org 或镜像源拉 buildroot 包。Demo 在内网运行时，这是"真实构建"的前提，W1 只在开发机上检查。
  4. **人力假设**：全文没有团队人数或开发产能（人 / AI 会话）假设。7 周 Demo 与 1–2 月的工作量是否可行，无法评估。
- **候选改动**：

```diff
--- 09 §3 M0 行
- | **M0 设计基线** | 2026-11-20 | HLD 定稿；01 作为开发基线；08 开发指南 v1、02 Compiler Agent 设计指引 v1、本计划经评审；内外网环境预检完成，Demo 环境确定 | P0 |
+ | **M0 设计基线** | 2026-11-20 | HLD 定稿；01 作为开发基线；08 开发指南 v1、02 Compiler Agent 设计指引 v1、本计划经评审；内外网环境预检完成，Demo 环境确定；**总部方案确认（形式与日期由负责人定，P0 gate 的另一半）** | P0 |
--- 09 §4.3 W1 内网 / 环境列（追加）
+ 内网预检追加：内网主机能否访问 Tizen 公开仓库或内网镜像源（gbs buildroot）；KVM；能否创建专用 OS 用户、配置 cgroup v2 委派与 systemd 单元
--- 09 §8 表（追加）
+ | 内网 Demo 主机的管理员权限（launcher、cgroup 委派、专用用户、出口规则、KVM） | 负责人 / 内网 IT | 2026-11-20 | Demo 部署与构建隔离 |
+ | 内网可用的 Tizen 仓库镜像（gbs buildroot 与源码） | 负责人 / 内网 IT | 2026-11-20 | Demo 真实构建 |
+ | 总部方案确认的形式与日期 | 负责人 | 2026-11-20 | P0 gate |
--- 09 §2 末尾
+ 6. **人力假设**：本计划按 ⟨N⟩ 名开发者 + AI 编码会话估算（由负责人填写）；人力变化时按 §10 月度更新重排。
```

- **副作用**：§8 多三行依赖，都是 Demo 能否在内网运行的前提，越早暴露越好。
- **配套检查点**：W1 结束时内网预检报告须包含上述三项结论；任一不可用，即在 11-20 前触发 §4.4 的备选方案。

#### P09-04 [MINOR] 契约 v1.0 在 CI Agent 消费之前定稿，违反 D10；1–2 月过载

- **位置**：09 §5.2 3 月、4 月（L129–130）；2 月（L128）；5 月（L131）；HLD §13 P5 gate、D10。
- **依据**：
  - HLD §13 P5："contract v1.0（G6）——**核心 + Compiler/UT/Review/CI 面定稿**……（D10：未被真实消费者不定稿）"。
  - 09 L129（3 月）："契约 v1.0 定稿；UT / Review 合规接入"；L130（4 月）："CI Agent v1……CI 合规接入"。
  - L128（2 月）："P3 余项……P4：全量与子集流水线、模块登记表与目标范围、部署资产与 launcher cgroup 契约、真实 UID / 权限 E2E……春节前后约一周产能下降"。
  - L131（5 月）："Optimization Agent v1（AutoFDO，接入增强版 llvm-profgen）……AutoFDO/BOLT 线 5 月开发完成，作为输入……至少一个模块的 AutoFDO 实测收益"。
- **问题**：
  1. **D10**：3 月定稿的 v1.0 包含 CI 面，而 CI Agent 4 月才实现并合规接入，等于 CI 面在没有真实消费者时定稿，违反 D10 的三条件 gate。
  2. **过载**：2 月要完成 P3 余项和整个 P4，外加春节一周，M1.5（2-26）几乎没有余量；而下半年 7 月与 11–12 月相对轻。
  3. **5 月依赖同月到位**：增强版 llvm-profgen 5 月才完成，同月就要求实测收益，且需要板子上的 profile 采集，没有缓冲。
- **候选改动**：

```diff
--- 09 §5.2 3 月
- | 3 月 | 05 Optimization Agent 设计指引 | P5 Compiler Agent 完整版（六类 fixture、兼容矩阵、修复成功率评估）；UT Agent v1；Review Agent v1 | 第一批 UT 用例与 Review 知识库内容接入 | 契约 v1.0 定稿；UT / Review 合规接入 |
+ | 3 月 | 05 Optimization Agent 设计指引 | P5 Compiler Agent 完整版（六类 fixture、兼容矩阵、修复成功率评估）；UT Agent v1；Review Agent v1；**CI Agent v1（官方 adapter 模拟联调）** | 第一批 UT 用例与 Review 知识库内容接入 | 契约 v1.0 定稿（核心 + Compiler / UT / Review / CI 面，四类消费者均已合规接入）；UT / Review / CI 合规接入 |
--- 09 §5.2 4 月
- P6 QuickbuildBackend 与 Build Gateway（……）；CI Agent v1；Benchmark Agent v1（……）
+ P6 QuickbuildBackend 与 Build Gateway（……）；Benchmark Agent v1（……）
--- 09 §5.2 2 月 / §4.3
+ 部署资产与 launcher cgroup 契约中 Demo 已需要的部分（ClineSR 专用用户、构建边界与 broker 的 cgroup 拉起）在 W3–W5 先行实现，2 月只补齐其余部分与真实 UID / 权限 E2E；M1.5 如仍不足，后延至 3-12，3 月工作相应顺延一周（以 7 月余量吸收）
--- 09 §5.2 5 月月末交付
- | 至少一个模块的 AutoFDO 实测收益 |
+ | AutoFDO 闭环在真实板子上跑通（重验证与撤销）；至少一个模块的实测收益最迟 6 月中旬给出 |
```

- **副作用**：
  - CI v1 提前到 3 月，3 月更紧，但 CI 依赖的官方 adapter 已在 2 月完成模拟联调，增量主要是 Agent 本身。
  - M1.5 可能后延一周，由 7 月余量吸收。
- **配套检查点**：
  - 3 月末契约 v1.0 评审时，核对四类消费者各自的合规接入证据；缺任一类则该面保持 provisional。
  - 2 月中旬检查 P4 进度：落后一周以上即启用 M1.5 后延方案。

#### P09-05 [MINOR] 遗漏的交付件：运维对账 / 裁决 CLI（HLD 明确"入 09"）、post-close correction、Build Gateway 骨架

- **位置**：09 §3、§5.2；HLD §14 R13、R14；§13 P2。
- **依据**：
  - HLD R13："运维 CLI 对账/裁决命令（**交付项，入 09**）人工处置"。
  - HLD R14："告警 + post-close correction 记录……复查窗口周期 probe"。
  - HLD §13 P2："……Release broker + **Build Gateway 骨架**"。
- **问题**：
  - 运维对账 / 裁决 CLI 是 manual_only、indeterminate 等情形的唯一人工出口，01 §5.1 的 AdjudicateRequest / AdjudicationEvidence 就是它的接口。M2 要对真实端点发布（6 月），没有它，就无法处理 publishing 滞留。HLD 明确要求写进 09，但 09 没有。
  - post-close correction 与复查窗口 probe 也没有排期。
  - Build Gateway 骨架是 P2 交付件，09 到 4 月（P6）才提及。
- **候选改动**：

```diff
--- 09 §5.2 2 月开发列（追加）
+ 运维 CLI：对账查询、人工裁决（AdjudicateRequest，类型化证据）、运维强制只探测、post-close correction、复查窗口周期 probe——随 M1.5 的授权与恢复 gate 一并验收；Build Gateway 骨架（P2 交付件，会话注入接口与错账号拒绝的桩）
--- 09 §5.1 验收（追加）
+ - **运维出口**：publishing 滞留、manual_only、部分发布等情形可经运维 CLI 按 01 §5.1 收尾，裁决受已记录观测约束；真实端点联调前完成。
```

- **副作用**：2 月更满，与 P09-04 的前移、后延方案一起考虑。运维 CLI 的大部分逻辑在编排侧，CLI 本身较薄。
- **配套检查点**：M1.5 gate 增加用例：manual_only 任务经运维 CLI 裁决（含被已记录观测拒绝的一例）；M2 前在受控测试仓上演练一次 publishing 滞留的人工处置。

#### P09-06 [NIT] 文档日期与状态描述不一致

- **位置**：09 头部 L3；§1 L18–19；§3 M0 L40；§7 L153–157。
- **依据**：
  - §7："00 HLD 2026-11-13 定稿""08 开发指南 2026-11-13（v1）"。
  - M0："2026-11-20……08 开发指南 v1、02 Compiler Agent 设计指引 v1、本计划经评审"。
  - §1："01 契约规格 v0.21……建议再做一轮定向核对后作为开发基线"。本轮即为该轮，计划日期写的是 11-06。
- **问题**：§7 的 HLD / 08 日期（11-13）与 M0（11-20）不是同一口径。§1 的状态在本轮之后会过期。
- **候选改动**：

```diff
--- 09 §7
- | 00 HLD | 总体设计 | 2026-11-13 定稿 |
+ | 00 HLD | 总体设计 | 2026-11-13 定稿（M0 前置） |
- | 08 开发指南 | …… | 2026-11-13（v1），之后随阶段补充 |
+ | 08 开发指南 | …… | 2026-11-13 初稿，2026-11-20（M0）评审通过，之后随阶段补充 |
--- 09 §1
+ （本表随第二十一轮评审结论更新：HLD 定稿版本、01 基线版本与遗留挂账项）
```

- **副作用**：无。
- **配套检查点**：本轮处置后的第一次月度更新同步 §1 与 §7。

---

## 同步项

已核对 HLD v2.11 附录 B 第 7 组（L985）：DeploymentInventory 的规范化输入、当前状态采集与 approved / current 比对、独立构建主机字段，以及例外清单条目均已登记。**无新增同步项。**

若采纳 H211-02，B-7 宜注明例外比对按现行 HLD 版本进行。C21-01 的逐目标观测字段属于 01 本身，不是同步项。

## 交付备注

- 只新增本文件，未修改被审文档、处置表或他方文件。
- 第二部分唯一的 MAJOR（C21-01）是 v0.21 新增约束缺少数据载体：补一个逐目标观测字段，约束覆盖对账报告与全部裁决分支即可，不改动 K 层结构。
- 第一部分两条、第三部分六条都是落地细节，不影响 HLD 定稿与开发启动；P09-01 与 P09-03 建议在 W1–W2 内处理，因为它们决定 Demo 能否在内网按安全底线运行。
