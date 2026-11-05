# HLD v2.8（收尾定向核对）+ 01_Contract_Spec v0.18（第十八轮定向复审）— Claude Code

**评审方**：Claude Code　**日期**：2026-11-05
**对象**：docs/00_Framework_HLD_v2.8.md（仅附录 A25 所列改动与新增 D23）；docs/01_Contract_Spec_v0.18.md（仅 A3 中 v0.18 一条所列改动）
**输入**：
- HEAD `bbe6a9775c8dcb11a893338fb368c33f93732b92`
- HLD v2.8 sha256 `0feaf5ca3d3d1e8453f55a453ed1a736ea188d8ebbe251e84b3316d83c8e2180`
- 01 v0.18 sha256 `871d68e8073f60b5b7cad8a349da85f1f034e63e86c24d20e300ec08766f676c`
- 另读：HLD_v2.7_review_disposition.md、01_v0.17_review_disposition.md、上一轮三家原始意见（只核对计数与原文）

**方法**：
- 对 v2.7→v2.8、v0.17→v0.18 做逐句 diff。
- HLD 沿 §7A.4、§2.5 交付边界、§10 部署拓扑、§11 走查。
- 01 沿 §2.2d 全段（阶段期限、执行绑定、故障归责、全局隔离通道、上限与分流、launcher）与 §2.5 出向协议走查。
- 按任务书的维度手工推演时间线。

**约束遵守**：未访问 Quickbuild，未读本轮其他评审方意见，未修改被审文档。

## 结论表

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 第一部分：HLD v2.8（A25 + D23） | **GO** | 0 | 0 | 2 | 1 |
| 第二部分：01 v0.18（A3 v0.18） | **NO-GO** | 0 | 2 | 4 | 1 |
| 同步项（不计入第二部分） | — | 0 | 0 | 0 | 0 |

**第一部分**：三条处置均已落入正文。D23 的范围和门禁已经写出，但有两处还不能照文执行：
- 边界没有覆盖"业务构建内容"和"宿主上的第三方工具"（H28-01）；
- 门禁只认 `.php` 后缀和自报的运行时（H28-02）。

两条都是 MINOR，不影响 GO。

**第二部分的两个 MAJOR 同出一源：计数的前提是"崩溃时实例上只有一个 task 在执行"，但这个前提有两处没有闭合。**
- **C18-01：隔离头的独占许可不要求先排空。** 许可授予时，实例上已经在执行的普通任务继续执行。通道没有 ready 成员时普通派发照常进行（这是为防阻塞设计的），所以已核销成员等到旧实例回收、变为 ready 时，当前实例上几乎一定有在飞的普通任务。正文"该实例当时为隔离通道独占"可以有两种读法：
  - 按"持有许可"读：无辜的隔离头替同实例的毒丸计数，最终进入 manual_only；
  - 按"只剩隔离头一个绑定"读：只要有持续流量，毒丸每次都与别人同处，永不计数。
- **C18-02：阶段期限到期只计触发者。** 毒丸让 broker 部分停滞、心跳仍在时，同实例所有任务都停住，谁的期限先到谁被计数。期限短的无辜任务两次即被耗尽，毒丸的定时器每次都被解除，永不计数。

两条都不会造成重复发布或伪造远端事实，安全性仍然成立。坏的是 v0.18 自己声明的两条保证："无辜 task 不被他人计数"和"毒丸有限次被识别"。修法是同一个原则：**只在判定事务快照的执行绑定集恰为一个 task 时计数（loss 与 interrupt 一样）；否则不计数，全部进入通道；隔离头先排空再放行。**

## 负责人七项裁决判断表

本轮 HLD 改动不触及七项裁决的语义。D23 是负责人新增前提，不在七项之内，只核对落地（第一部分）。

| # | 裁决 | 判断 | 理由与代价 |
|---|---|---|---|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | **成立** | 本版未触及。代价不变：两路报告与超时 / 替代历史都要保留。 |
| ② | Quickbuild 默认取最新 Profile 快照，在 Run 启动时固定 | **成立** | 本版未改；措辞与实测记录一致。代价不变：快照越新，与构建根的差距越大，可能出现与 patch 无关的构建失败，失败时附两个编号。 |
| ③ | Profile 严格匹配 + 小改动复用预案 | **成立** | 本版未改；v2 仍缺省关闭，开启前须用真实工具链数据评估。 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | 本版未改。`candidate_recheck_failed` 重试与改交撤销都不缩小验证范围。 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | 上一轮唯一的缺口（完成复核与预校验不一致的出口）已与父版本 CAS 失败合并为同一出口，且不改记 purpose，"按修复名义回退已接受的优化"不再可能。代价：并发竞争会多一次节点重试；节点 retry 为 0 时该竞争直接进入 fail_safe（与 CAS 失败一致，可接受）。 |
| ⑥ | Quickbuild 可加 Base CL，否则默认最新；读回核对 | **成立** | 本版未改；改交撤销对 base_mismatch / backend_source_input_unsupported 的例外与"base_mismatch 优先"一致，读回核对仍先于撤销。 |
| ⑦ | 超时后重试成功可发布，须审批人确认 | **成立** | 本版未改。 |

---

## A. 处置落实

### HLD v2.7 处置表（P1–P4）

| # | 处置要求 | 正文落点 | 判断 |
|---|---|---|---|
| P1 | 复核结论与预校验不同 / 准入不再满足 → 与 CAS 失败同一出口：候选作废、计划与 series 不变、sys.error(candidate_recheck_failed)、重试时重新预校验、不得改记 purpose | §7A.4 L744"复核推导的 purpose / plan_id 与预校验保存值不同，或准入不再满足……→ 与父版本 CAS 失败同一出口……不得按复核结论改记 purpose（v2.8）"；§11.3 L880 v2.8 用例组两例；B-7 L979 | 已落实。两个触发例子（收益判定写回、不推进 series 的环）正是上一轮 H27-01 的两种情形 |
| P2 | 改交撤销的例外；被拒提交不登记 candidate、改交用新 request_id | §7A.4 L744 规则② 末尾 | 已落实。"复用旧 request_id 返回首次的拒绝响应"与命令幂等一致 |
| P3 | §11.3 terminal 兜底用例改为直接构造状态的单元测试 | L880"绕过加载器直接构造'未决计划 + terminal success_on'状态" | 已落实 |
| P4 | D23 不得引入 PHP；§11.1、§11.2、§9、附录 B 同步 | D23 L124；§9 L816；§11.1 L874；§11.2 L877；B-7 L982 | 已落实到四处。范围与门禁的可执行性见 H28-01 / H28-02 / H28-03 |

计数核对：Kimi 0 + Codex 1 NIT + Claude Code 1 MINOR + 1 NIT = 3 条，与"合计 3 条意见"一致。

### 01 v0.17 处置表（X1–X4）与三处合并方案

| # | 处置要求 | 正文落点 | 判断 |
|---|---|---|---|
| X1 全局隔离通道 | 所有嫌疑集合并为一个通道 | L188 | 已落实 |
| | 隔离头执行期间当前实例不承担其他派发；暂缓 intent 不放行、不计时、不构成绑定 | L188；DispatchReceipt.held_for_isolation L301 | 已落实，但**只对隔离头进入执行阶段后新产生的派发生效**，许可授予前已在飞的绑定不受约束（C18-01）。暂缓 intent 与既有阶段 / 恢复规则未衔接（C18-03） |
| | hello 扫描排除 isolating / manual_only | L196 | 已落实 |
| | 统一出向调度入口校验独占许可（含只探测） | L188"所有出向生成与续送事务统一经此调度入口校验独占许可，重启不得绕过"；L196 | 已落实（§2.5 恢复规则 (a) 本身未改，见 C18-03） |
| | 成员身份回到常规后保留 | L188 | 已写，但按 L190 的迁移条件，成员不会以非终态回到 active（C18-07） |
| | 有确定触发者只计其 loss，其他不计 interrupt | L187 ① | 已落实；但触发者本身未必是肇事者（C18-02） |
| X2 判定事务内计数 | 计数在判定事务内结算，隔离头随即让出通道 | L187 末句；L188 | 已落实 |
| | authorization_expired_in_isolation | L188；ConsumeRejected L587 | 已落实（放进 ConsumeRejected 的位置不当，C18-07） |
| | 成员调度状态 ready / waiting_holder / probe_only / diagnostic_done；只从 ready 中选头；等待者保留原序；不放宽静默条件；无 ready 时不阻塞普通派发 | L188；ReleaseTaskState.isolation_state L318 | 已落实。"无 ready 时不阻塞普通派发"恰好是 C18-01 的成因：它保证有成员变 ready 时实例上必有在飞流量 |
| X3 执行绑定划界 | intent 提交即绑定、不看 ACK；就绪前不得绑定；退役判定与绑定串行化 | L186 | 已落实（绑定缺结束条件，C18-04；放行才是真正的绑定时点，C18-03） |
| | RetirementEvent 持久化并恰归一个域 | L187；模型 L302–306 | 已落实 ①②③ 三类；`cause = retire_requested` 没有归属（C18-05） |
| | 无绑定失效（含任务全部完成后）归启动 / 健康域 | L191 | 文字已写，但与 L186 的绑定谓词字面矛盾（C18-04） |
| X4 | waiting_holder 进入时点；计数更正 | L190"被标记 retiring 或 lapsed 的事务"；A3 v0.17 条已改为"6 条编号意见（Claude Code C16-03 含两点；5 个独立问题）" | 已落实 |

**三处合并方案是否成立**：
- **全局隔离通道 + 统一入口校验**：方向成立；缺"先排空再放行"一步（C18-01）。
- **判定事务内计数 + 成员调度状态**：成立。被卡住的成员只阻塞自身：waiting_holder 不占通道，probe_only 让出通道，manual_only 为 diagnostic_done。没有死锁。
- **intent 划界 + 无绑定归启动 / 健康域**：方向成立。须补三处：
  - 绑定的结束条件（C18-04）；
  - 计划内退役的归属（C18-05）；
  - 病态 broker 在有流量时只会被算到任务头上（C18-06）。这是本方上一轮 C17-03 所提谓词的代价，当时没有写出，本轮补上。

**"记录更正"**：01_v0.16 处置表开头"合计 7 条意见"更正为"6 条编号意见（Claude Code C16-03 含两个子点，按 7 点处置）"。核对：Claude Code 1 MAJOR + 2 MINOR + 1 NIT = 4，Codex 2 MAJOR = 2，Kimi 0，合计 6。**准确。**本轮 01_v0.17 处置表"8 条编号意见"：Codex 3 + 1 = 4，Claude Code 1 + 2 + 1 = 4，合计 8，归并为 X1–X4。**准确。**

---

## B. 第一部分：HLD v2.8 核对

### B1. 完成复核不一致 → candidate_recheck_failed

- **出口唯一**：
  - 复核不一致的唯一结局是 sys.error，计划与 series 都不变。
  - 预校验保存的 purpose / plan_id 只作比较，不作写入依据。
  - 同一完成事务的重放复用既有 receipt。因此"复核不一致 + 重放"不会出现第二种结局。
- **重试收敛**：重试会重新预校验，看到的是复核时已变化的状态，结论稳定，不会无限竞争。
  - 例一：计划已为 accepted。失败节点按无未决计划走常规修复环。
  - 例二：剩余环次数已耗尽。重试得到 `E-PLAN-NO-CAPACITY`，Agent 返回 `no_further_gain` / `no_gain_found`。
- **与 §4.2.4 冻结模型的一致性**：CAS 失败本来就是 sys.error 出口，这里只是并入同一出口，没有新增 series 状态。
- **与 sys.invalid_result 规则的关系**：sys.error 由框架设置，不是 Agent 返回的 status，不触发"未决计划期间返回 opt_patch_ready 以外 status → sys.invalid_result"。无冲突。

### B2. 改交撤销的例外与"被拒提交不登记 candidate"

- 例外只列 base_mismatch / backend_source_input_unsupported 两种 image_failed_exhausted 原因，与 L630、L744"base_mismatch 优先于确定性撤销"一致。
- 被拒提交不占"每 task 至多一个 candidate"名额，改交使用新 request_id，复用旧 id 回放首次拒绝。三者合起来，"拒绝 → make_revert → 改交"在同一 task 内可完成，不会被自己的被拒提交挡住。
- 01 §3.3 冻结 series 模型的对应改动已登记在 B-7 L979，不另列同步项。

### B3. D23 落地

| 检查项 | 正文 | 判断 |
|---|---|---|
| 范围：全部交付与部署内容 + 依赖闭包 | D23 列举框架、各 Agent、Approval、broker 与官方 adapter、Build Gateway 与登录助手、Web 视图、deploy 资产与镜像、测试夹具 | 列举与 §2.5 交付边界、§10 部署拓扑不完全对齐（H28-03） |
| 业务接入的插件与受限 adapter | 注册时声明运行时，PHP 拒绝 | 只看自报，不看制品内容（H28-02） |
| 边界：外部系统、测试板上的业务用例脚本 | 已写；"宿主侧的适配与解析代码属于本产品"也写了 | **业务构建内容**（buildroot 装入的业务依赖、产出的 RPM / 镜像、BaselineCache、Profile 库数据）与**宿主上的第三方工具**（ClineSR CLI、gbs / mic、LLVM 工具、LogAnalyzer、sdb）两类未归属（H28-01） |
| 门禁扫描 | §11.2 扫 lockfile 闭包、deploy 资产与镜像清单、仓库全部文件 | 判定规则只认 `.php` 后缀；"以 PHP 实现的第三方组件"无判定方法；主机实际安装集、镜像基础层、前端构建链不在扫描对象内（H28-02） |
| Web 视图前端 | §9、§11.1"Python 实现……前端为静态资源" | 运行时成立；静态资源的构建链（若用 npm）不在"lockfile 依赖闭包"内（并入 H28-02） |
| 运维工具 | 登录助手已列；Review CLI、运维 CLI、MCP 服务未列 | H28-03 |
| deploy 镜像基础层 | "deploy 资产与镜像" | 未写明按实际安装集而非声明清单扫描（H28-02） |
| 测试夹具 | 已列 | 成立 |

### 第一部分问题

#### H28-01 [MINOR] D23 边界没有覆盖"业务构建内容"与"宿主上的第三方工具"，门禁的扫描对象因此不确定

- **位置**：HLD v2.8 D23（L124）、§11.2（L877）；相关 §2.5（L172）、§7.8 BaselineCache（L663）、§10 部署拓扑（L822–826）。
- **依据**：
  - D23："本产品交付与部署的全部内容**不得引入 PHP**：……deploy 资产与镜像、测试夹具，以及它们的运行时依赖闭包……**边界**：本产品对接的外部系统（Quickbuild、gerrit、github、Cosmos 等）的实现语言不在本约束范围内；业务部门提供、只在测试板上执行的测试用例脚本不属于本产品交付物"。
  - §11.2："CI 扫描 lockfile 依赖闭包、deploy 资产与镜像清单、仓库全部文件"。
  - §10："内网主机（单机）| ……各 Agent worker、ClineSR CLI"；"构建隔离边界 | GBS buildroot 的 sudo 段与 mic"。
- **问题**：有两类内容既不在"范围内"的列举里，也不在"边界"的排除里：
  - **(a) 业务构建内容**：被编译的业务源码工作区；按业务 spec 的 BuildRequires 装进 buildroot 的包；产出的 RPM 与镜像；BaselineCache 条目；Profile 库数据。这些是产品处理的**数据**，不是交付物。但字面上"镜像"与"依赖闭包"会把构建 VM 里实际装入的 buildroot 包、缓存的基线镜像都算进去。业务平台若本身含 PHP 包，门禁要么阻断合法的业务构建，要么由各实现者自行放宽，两种都不是负责人前提的本意。
  - **(b) 宿主与运维机上的第三方工具**：ClineSR CLI、gbs / mic、llvm-profgen / BOLT / CompilerGym 类工具与 MLGO 模型、LogAnalyzer、sdb、登录助手调用的浏览器。它们由 deploy 安装、由产品调用，却没写清属于"运行时依赖闭包"（受约束）还是"外部系统"（不受约束）。ClineSR CLI 与 LogAnalyzer 是内网他方提供的工具，最容易两边都套得上。
- **候选改动**：

```diff
--- HLD D23 边界
- **边界**：本产品对接的外部系统（Quickbuild、gerrit、github、Cosmos 等）的实现语言不在本约束范围内；业务部门提供、只在测试板上执行的测试用例脚本不属于本产品交付物，但其在宿主侧的适配与解析代码属于本产品、受本约束。
+ **边界**：
+ - 不在范围内：本产品对接的外部系统（Quickbuild、gerrit、github、Cosmos 等，经网络接口访问）的实现语言；业务部门提供、只在测试板上执行的测试用例脚本；**本产品处理的业务内容**——被测业务源码、按业务 spec 装入 buildroot 的构建依赖、产出的 RPM 与镜像、基线镜像缓存条目、Profile 数据（它们是数据而非交付物，门禁不扫描其内容）。
+ - 在范围内：其在宿主侧的适配与解析代码；**由 deploy 安装在本产品主机、构建隔离边界与运维机上、并由本产品进程调用的第三方工具及其依赖**（ClineSR CLI、gbs / mic、LLVM / BOLT 工具链、CompilerGym 类工具、LogAnalyzer、sdb 等）——属于运行时依赖闭包；若某内网工具自身依赖 PHP，E0 预检即报告，由负责人决定换型或豁免并记录。
```

- **副作用**：
  - (a) 写明排除后，业务平台即使含 PHP 也不影响产品使用；代价是产品不对业务镜像内容作此项保证（本来也不该保证）。
  - (b) 归入依赖闭包后，这些工具的部署件也要过扫描。内网工具若依赖 PHP，在接入期就会暴露，不会等到上线后才发现。
- **配套测试 / 夹具**：
  - 门禁夹具：构建 VM 的 buildroot 装入含 php-cli 的业务包 → 产品门禁不报（业务内容）；deploy 清单中某第三方工具传递依赖 php → 报。
  - E0 预检清单增加：对 ClineSR CLI、LogAnalyzer 等内网工具的安装件执行与 §11.2 相同的扫描，结果写入预检报告。

#### H28-02 [MINOR] 门禁与注册检查的判定规则不能机械执行：只认 `.php` 后缀与自报运行时，扫描对象漏掉实际安装集

- **位置**：HLD v2.8 §11.2（L877）、D23（L124）。
- **依据**：
  - §11.2："出现 PHP 解释器 / 扩展 / 包、`.php` 文件或以 PHP 实现的第三方组件即门禁失败；插件与受限 adapter 注册时**声明的运行时**为 PHP 即拒绝注册"。
  - D23："Benchmark 外接套件的宿主侧解析规则（声明式，§7A.3）在注册时声明运行时"。
- **问题**：
  1. **文件判定只列 `.php`**。漏掉：
     - `.phar`、`.phtml`、`.php3`–`.php8`、`.phps`；
     - 无后缀但 shebang 为 php 的脚本；
     - 含 `<?php` 标记的其他后缀文件（如 `.inc` 或模板）；
     - `composer.json` / `composer.lock`。
  2. **"以 PHP 实现的第三方组件"没有可执行的判定方法**。扫描能落地的只有四类信号：
     - 包管理器元数据中的 php 包（rpm / deb 包名与 Requires、PyPI 不涉及）；
     - 可执行文件（`php`、`php-cgi`、`php-fpm`）；
     - 共享库（`libphp*`、`mod_php`）；
     - composer 清单。

     正文应以这些信号定义"以 PHP 实现"。
  3. **扫描对象不全**：
     - "lockfile 依赖闭包"只是 Python lockfile；Web 视图静态资源若由 npm 构建链生成，其 lockfile 不在内。
     - 内网主机上的进程不是以镜像交付的，deploy 会安装系统包。"镜像清单"若指声明清单，就漏掉传递依赖；镜像基础层与构建 VM 镜像同理。这三处都应按实际安装集扫描（`rpm -qa` / `dpkg -l` + 文件系统），不是只扫声明。
     - 内网主机的实际安装集 CI 看不到，须放进 deploy 验收或 E0 预检。
  4. **注册检查只看自报**：
     - Python 插件可以携带 `.php` 文件并以子进程调用；受限 adapter 的入口可以是任意可执行文件。注册时须对制品内容做与 CI 同一规则的扫描，并检查入口的 shebang 与 ELF 类型。
     - 声明式解析规则本身没有运行时，"声明运行时"无意义。应改为"只接受声明式格式，不得引用可执行脚本"。
- **候选改动**：

```diff
--- HLD §11.2
- **无 PHP 检查（D23）**——CI 扫描 lockfile 依赖闭包、deploy 资产与镜像清单、仓库全部文件：出现 PHP 解释器 / 扩展 / 包、`.php` 文件或以 PHP 实现的第三方组件即门禁失败；插件与受限 adapter 注册时声明的运行时为 PHP 即拒绝注册（conformance 断言）。
+ **无 PHP 检查（D23）**——判定信号（任一命中即失败）：包元数据中的 php 包或对其的依赖；`php` / `php-cgi` / `php-fpm` 可执行文件、`libphp*` / `mod_php` 共享库；`.php` / `.phar` / `.phtml` / `.php[3-8]` / `.phps` 文件、shebang 为 php 的文件、含 `<?php` 标记的文件；`composer.json` / `composer.lock`。扫描对象：仓库全部文件；全部 lockfile（Python 与前端构建链）；deploy 镜像与构建 VM 镜像的**实际安装集**（含基础层，按包数据库与文件系统）；内网主机的实际安装集在 deploy 验收与 E0 预检中以同一规则扫描。注册检查：插件与受限 adapter 的**制品内容**按同一规则扫描，入口文件的 shebang / ELF 类型须与声明的运行时一致，任一不符拒绝注册；Benchmark 宿主侧解析规则只接受声明式格式、不得引用可执行脚本（conformance 断言）。
--- HLD D23
- 与 Benchmark 外接套件的宿主侧解析规则（声明式，§7A.3）在注册时声明运行时，PHP 运行时一律拒绝注册。
+ 在注册时声明运行时并经制品内容扫描（§11.2），PHP 一律拒绝注册；Benchmark 外接套件的宿主侧解析规则只接受声明式格式（§7A.3），不得引用可执行脚本。
```

- **副作用**：
  - CI 与注册各增加一次内容扫描，规则表需要维护，但规则表很小。
  - 安装集扫描依赖目标环境的包数据库，在外网开发机上只能对镜像执行；内网主机部分放到 deploy 验收。
- **配套测试 / 夹具**：门禁夹具各一例，均须报：
  - `.phar` 文件；
  - 无后缀、shebang 为 `#!/usr/bin/env php` 的脚本；
  - `composer.lock`；
  - deploy 镜像基础层含 php-cli；
  - Python 插件 wheel 内含 `.php`，注册拒绝；
  - 受限 adapter 声明 python、入口 shebang 为 php，注册拒绝；
  - 解析规则引用外部脚本，注册拒绝。

#### H28-03 [NIT] D23 范围列举与 §2.5 交付边界、§10 部署拓扑不对齐

- **位置**：HLD v2.8 D23（L124）；§2.5（L172）；§10（L822–826）；§7.7（L652）。
- **依据**：
  - D23 列举："框架、各 Agent、Approval 服务、Release broker 与官方发布 adapter、Build Gateway 与运维登录助手、只读 Web 视图（§9）、deploy 资产与镜像、测试夹具"。
  - §2.5"本团队开发"另含："板子池、基线镜像缓存、Profile 库、BenchPolicy 统计库、构建隔离边界（launcher 与构建 VM 镜像）"。
  - §1 / §4："Review CLI""运维 CLI""MCP 服务（含 HTTP 端点）""Skill"。
  - §7.7："首次接入与每次刷机后运行能力探测脚本"。
- **问题**：
  - 未列出的部件多半能被"框架"或"deploy 资产"兜住，但兜不兜得住要靠解读。
  - 边界只排除"业务部门提供"的板上用例脚本。**产品自己在板上运行的脚本**（能力探测、profile 采集封装、刷机适配器）在范围内这一点没有正面写出。
- **候选改动**：

```diff
--- HLD D23
- 本产品交付与部署的全部内容**不得引入 PHP**：框架、各 Agent、……测试夹具，以及它们的运行时依赖闭包
+ 本产品交付与部署的全部内容**不得引入 PHP**——范围按引用定义：§2.5 中"本团队开发"的全部部件、§10 部署拓扑中本产品部署的全部内容（含 Review CLI、运维 CLI、MCP 服务、开发者侧 Skill、板型适配器及本产品下发到测试板上运行的能力探测与采集脚本）、测试夹具，以及它们的运行时依赖闭包
```

- **副作用**：无。§2.5 与 §10 以后增删部件时，D23 自动跟随。
- **配套测试 / 夹具**：§11.2 扫描对象随之包括板型适配器下发到板上的脚本目录。

---

## D. 第二部分：01 v0.18 核对

### D1. 逐项结论

| 检查项 | 结论 |
|---|---|
| intent 提交即绑定、不看 ACK | 成立；核销前（反序列化 ReleaseDispatch 时、ACK 前）崩溃的毒丸能被计数 |
| 就绪前不得绑定 | 成立 |
| 退役判定与绑定串行化 | 对 intent 提交成立；暂缓 intent 的**放行**才是真正的绑定时点，未纳入（C18-03） |
| 有触发者只计其 loss、同实例他人不计 interrupt | 成立，但触发者未必是肇事者（C18-02） |
| 无触发者、有绑定 → 任务域；无绑定 → 启动 / 健康域 | 规则成立；绑定谓词缺结束条件（C18-04）；`retire_requested` 无归属（C18-05）；病态 broker 被算到任务头上（C18-06） |
| 隔离头执行期间当前实例不承担其他派发 | 只约束新派发，不约束许可授予时已在飞的绑定（C18-01） |
| 暂缓 intent 不放行、不计时、不构成绑定 | 与 R13 阶段写入、§2.5 恢复规则 (a)、替代协议未衔接（C18-03） |
| hello 扫描排除 isolating / manual_only | 成立 |
| 所有出向经统一调度入口 | 成立（§2.5 规则 (a) 未加 held 条件，C18-03） |
| ready / waiting_holder / probe_only / diagnostic_done 与 recovery_mode 迁移 | 调度状态成立；"isolating → active"的条件自相矛盾（C18-07） |
| authorization_expired_in_isolation | 成立；放在 ConsumeRejected 的位置不当（C18-07） |
| launcher 启动 / 健康失败上界 | 划界成立；完成后失效与谓词矛盾（C18-04）；有流量时永不停机（C18-06） |

### D2. 时间线走查

符号说明：
- P：毒丸。B / A：无辜 task。N：隔离期间新到的 task。
- "排他"指判定事务快照里该实例的执行绑定集恰为一个 task。
- "✓"表示出口唯一且符合声明的性质；C18-xx 表示该格出口不唯一或违反声明，详见对应问题。

| 时间线 | 崩溃点 / 情形 | 出口 | 判定 |
|---|---|---|---|
| 正常 | 无崩溃；通道空 | intent → granted → outcome → 终局 | ✓ |
| 正常 | 隔离头执行中，本 task 新派发 | 暂缓，不计时；头离开后放行 | ✓（放行时阶段 / 目标实例 / 串行化见 C18-03） |
| 正常 | 暂缓中授权过期 | authorization_expired_in_isolation 关闭，计数不变 | ✓（暂缓 intent 须同事务作废，C18-03） |
| 核销前（intent 后、ACK 前） | P 单独 | 任务域，P +1 | ✓ |
| 核销前 | intent 提交前 broker 崩溃 | 启动 / 健康域 | ✓ |
| 核销前 | 判定与 intent 并发 | 先提交者决定归属 | ✓ |
| 核销后发生前 | P + B 同处，非隔离 | ≥2 → 均不计，进入通道 | ✓ |
| 核销后发生前 | 隔离头 P，实例上无其他绑定 | P +1 → waiting_holder → 回收后 ready，原序 | ✓ |
| 核销后发生前 | 隔离头 B（已核销、刚变 ready），实例上有在飞的 N（毒丸） | 读法甲 B +1（误伤）；读法乙均不计、P/N 在持续流量下永不计数 | **C18-01** |
| 发生后崩溃 | outcome 丢失，单绑定 | +1；回收后恢复臂 resumed → 对账 confirmed_happened → released | ✓ |
| 发生后崩溃 | 达到上限 | 已核销 → manual_only，只经 C-11；diagnostic_done 不占通道 | ✓ |
| indeterminate | 隔离头转 indeterminate | probe_only，让出通道；周期 probe（头执行期间暂缓） | ✓ |
| indeterminate | probe 永远 unknown | 只阻塞自身，C-11 出口 | ✓ |
| 实例存活、单 task 失联 | A 远端挂起，单绑定 | ① A loss +1 | ✓ |
| 实例存活、单 task 失联 | P 令 broker 部分停滞（心跳正常），A 期限先到 | ① A loss +1，P 不计；重复两次 A 耗尽 | **C18-02** |
| 实例存活、单 task 失联 | probe 得 not_happened 而持有者为当前实例 → retire_requested，同实例有在飞 task | 无归属域 | **C18-05** |
| 任意 | 实例完成全部 task 后无任务 lapsed | 字面"有绑定"→ 任务域，launcher 不计 | **C18-04** |
| 任意 | broker 自身健康故障、持续流量 | 每次都有绑定 → 任务域，逐个耗尽无辜 task，launcher 不停机 | **C18-06** |
| 任意 | manual_only 之后 | C-09、④、execute 派发、hello 扫描均排除；暂缓的旧 execute intent 即使放行也被 C-09 拒绝 | ✓（无自动执行路径；建议仍按 C18-03 同事务作废） |

**重点问题的结论**：
- **隔离通道死锁 / 饿死**：没有死锁。waiting_holder、probe_only、manual_only 都不占通道。饿死有一处：没有排空步骤时，隔离头会与在飞流量同处，读法乙下会无限推迟识别（C18-01）。
- **暂缓 intent 能否全部放行**：能（通道有限，每个隔离头受期限约束）。但放行的目标实例与时点要补（C18-03）。
- **毒丸有限次识别**：崩溃型毒丸在 C18-01 修正后成立。部分停滞型毒丸须 C18-02。
- **无辜 task 不被他人计数**：须 C18-01、C18-02、C18-05 三处同时修正。
- **退役事件恰归一个域**：除 retire_requested（C18-05）外成立。
- **manual_only 后无自动执行路径**：成立。

### 第二部分问题

#### C18-01 [MAJOR] 隔离头的独占许可不要求先排空：许可授予时实例上仍可有其他执行绑定，"独占"的两种读法各破坏一条声明的保证

- **位置**：01 v0.18 §2.2d L188（全局隔离通道）、L187 ②（故障归责）；CF-AUTH-20g / 20k。
- **依据**：
  - L188："**通道每次只从 ready 成员中按序选一个隔离头并授予独占派发许可**；隔离头处于执行可能阶段期间，**当前实例不承担任何其他派发**——新任务、其他成员、hello 扫描与 intent 续送产生的 execute 与 release_probe_dispatch 一律写 intent 后暂缓……没有 ready 成员时通道不阻塞普通派发"；"已核销成员须自己的 granted_epoch 持有者静默后才为 ready"。
  - L187 ②："绑定者恰一个、**或该实例当时为隔离通道独占**（下条）→ 该 task `interrupt_count` +1；绑定者 ≥ 2 → 都不计数，全部进入隔离通道"。
  - L188 末："由此毒丸至多 1 + `max_task_interrupts` 次崩溃后被识别，无辜 task 不被他人计数"。
- **问题**：暂缓只约束隔离头进入执行阶段**之后新产生**的派发，没有要求许可授予前实例上已有的执行绑定先结束。而"没有 ready 成员时普通派发照常"（X2 防阻塞的设计）保证了：成员一旦变为 ready（典型情形是已核销成员等到旧实例 reclaimed），当前实例上几乎一定有在飞的普通任务。反例：
  1. E1 无关崩溃（OOM），执行绑定 {B1, B2}，二者均已核销 → 都进入通道，都是 waiting_holder。
  2. E2 hello。通道没有 ready 成员，普通派发照常进行；毒丸 N 被派到 E2，进入 awaiting_outcome。
  3. E1 reclaimed → B1 变为 ready → 成为隔离头，许可授予，恢复派发发往 E2。此后新派发暂缓，但 N 已在执行。
  4. N 令 E2 崩溃，绑定集 {B1, N}。

  按 L187 ② 的两种读法：
  - **读法甲**（"独占" = 隔离头持有许可）：只对 B1 +1，N 不计。B1 转 waiting_holder；E2 回收后 B1 再次 ready，又与回收期间进来的流量同处……三次后 B1 进入 manual_only。B2 随后轮为隔离头，同样被耗尽。**破坏"无辜 task 不被他人计数"。**
  - **读法乙**（"独占" = 绑定集恰为 {隔离头}）：≥2 → 都不计，N 进入通道。若毒丸本身是已核销成员 P：P 每次都要等旧实例回收才 ready，等待期间普通流量照常进入新实例；P 成为隔离头时，总有在飞的普通任务与它同处。于是 P 每次崩溃都不计数，还把同处的无辜任务拉进通道。只要流量持续，P 永不被识别。**破坏"毒丸有限次被识别"，等于回到 v0.15 的无界重派。**

  CF-AUTH-20g 本版新增的"S = {P, B} 且有持续并发流量"一格期望 P 被识别，但正文没有能保证它的机制。
- **候选改动（先预约、后排空、再放行；"独占"按绑定集定义）**：

```diff
--- 01 §2.2d 全局隔离通道
- **通道每次只从 ready 成员中按序选一个隔离头并授予独占派发许可**；隔离头处于执行可能阶段期间，**当前实例不承担任何其他派发**——新任务、其他成员、hello 扫描与 intent 续送产生的 execute 与 release_probe_dispatch 一律写 intent 后暂缓（……），隔离头离开执行可能阶段后按序放行。
+ **通道每次只从 ready 成员中按序选一个隔离头，分两步授予独占**：① **预约**——选出隔离头的事务持久化 `isolation_reservation`（隔离头 task_id、当前实例 epoch），自此当前实例的一切新出向（新任务、其他成员、hello 扫描与 intent 续送产生的 execute 与 release_probe_dispatch）写 intent 后暂缓；② **排空后放行**——当前实例上隔离头以外的执行绑定全部离开执行可能阶段（终结、转 awaiting_probe、或随实例退役重排）后，才放行隔离头的派发。排空期间隔离头不武装定时器；在飞者仍受自身阶段期限约束，排空有界。实例在排空期间退役 → 预约随之作废、按常规归责，隔离头保持 ready 并在下一实例上重新预约。隔离头离开执行可能阶段后预约解除，暂缓 intent 按序放行（C18-03）。
--- 01 §2.2d 故障归责 ②
- ② **无确定触发者的 lapsed**，且存在执行绑定 → 任务域：绑定者恰一个、或该实例当时为隔离通道独占（下条）→ 该 task `interrupt_count` +1；绑定者 ≥ 2 → 都不计数，全部进入隔离通道；
+ ② **无确定触发者的 lapsed**，且存在执行绑定 → 任务域：判定事务快照的绑定集（RetirementEvent.bound_task_ids）恰为一个 task → 该 task `interrupt_count` +1；绑定者 ≥ 2 → 都不计数，全部进入隔离通道（隔离通道的排空保证隔离头执行时绑定集恰为 {隔离头}）；
```

- **副作用**：
  - 排空期间普通派发暂缓，最长等于在飞任务剩余的阶段期限。只在通道有 ready 成员时发生，正常路径无成本。
  - 不推荐的替代方案：给隔离头单独拉起一个专用实例。它需要两个当前实例，与"任一时刻只有一个当前 broker 实例"冲突。
  - 新增一个持久化字段（`isolation_reservation`，可放在通道记录上），随 dev7 一并发布。
- **配套测试 / 夹具**：
  - **CF-AUTH-20g 补反例**：B1 / B2 已核销、来自无关崩溃；E2 上在飞毒丸 N；E1 reclaimed 后 B1 变为 ready。断言：
    - B1 的派发在 N 离开执行阶段前不放行；
    - N 令 E2 崩溃时绑定集为 {N} → N +1；
    - B1 / B2 的 interrupt_count 为 0，且最终完成。
  - **CF-AUTH-20g 持续流量 × 已核销 P**：P 在至多 1 + max_task_interrupts 次崩溃后进入 manual_only。
  - **CF-AUTH-20k**：排空期间实例退役 → 预约作废，隔离头在新实例重新预约；预约与放行两个事务的前后各 kill 编排，结局唯一。
  - **model-based 断言**：每条 domain = task 且有计数的 RetirementEvent，其 bound_task_ids 恰一个元素。

#### C18-02 [MAJOR] 有确定触发者的退役只计触发者：实例级停滞时触发者未必是肇事者

- **位置**：01 v0.18 §2.2d L187 ①；L189（上限与分流）；CF-AUTH-20h（L818）。
- **依据**：
  - L187 ①："**有确定触发者**（阶段期限 CAS 到期）→ 只对触发 task `loss_count` +1；同实例其他 task 只解除定时器并重排，**不增加 interrupt_count**"。
  - L189："`loss_count` 达到 `max_task_losses`（缺省 2）……未核销者……release_failed……dispatch_loss_exhausted；已核销者……manual_only"。
  - L188 末："无辜 task 不被他人计数"。
  - v0.17 CF-AUTH-20h 的预期"无辜 task 与毒丸同实例连续崩溃后仍不进入 manual_only"在 v0.18 中被删去。
- **问题**：阶段期限到期只说明"该 task 的阶段没在期限内完成"，不说明原因在它自己。毒丸 P 可以让 broker **部分停滞而心跳仍在**，例如：
  - 官方 adapter 的同步调用占满执行线程池；
  - 在共享锁上死锁，而心跳在独立线程续期。

  这时实例不会 lapsed，同实例所有 task 都停住，**谁的期限先到谁被计数**。awaiting_consume 的期限通常短于 awaiting_outcome，所以 P 执行中时，刚派发的无辜 A 先到期：
  1. A loss +1，实例 retiring。A、P 按常规并发重派（① 不进入隔离），再次同实例。
  2. A 再先到期 → 达到 max_task_losses = 2 → 未核销则 dispatch_loss_exhausted，已核销则 manual_only。
  3. P 的定时器每次都被解除，从不计数。只要持续有期限更短的新任务进来，P 就永远不被识别。

  v0.17 已有同样的计数方式，但 v0.18 把它写成归责规则，并声明"无辜 task 不被他人计数"，这条声明在部分停滞下不成立。后果与 C17-01 同类：无重复发布，但无辜任务被耗尽，毒丸识别无界。
- **候选改动（与 C18-01 同一原则：只在绑定集恰为一个时计数）**：

```diff
--- 01 §2.2d 故障归责 ①
- ① **有确定触发者**（阶段期限 CAS 到期）→ 只对触发 task `loss_count` +1；同实例其他 task 只解除定时器并重排，**不增加 interrupt_count**；
+ ① **有确定触发者**（阶段期限 CAS 到期）→ 判定事务快照的绑定集恰为 {触发 task}（含隔离头排他执行）→ 只对它 `loss_count` +1；绑定集 ≥ 2 → **都不计数**，触发 task 与其余绑定者全部进入隔离通道，触发 task 排在本批首位；两种情形下同实例其他 task 都**不增加 interrupt_count**、只解除定时器并重排。由此单 task 的远端挂起在通道内单独执行再到期时被计数，识别上界为 1 + `max_task_losses` 次期限事件。
```

- **副作用**：
  - 真实的单任务远端挂起若与他人同处，识别推迟一轮隔离。
  - 通道使用增加，但只在多任务同实例时发生。
  - 不再需要区分"停滞是任务自身的还是实例级的"，判定仍只依赖持久化的绑定集快照。
- **配套测试 / 夹具**：
  - **CF-AUTH-20h 新增**：FakePublisher 令 P 占满 broker 执行线程、心跳正常；A 的 awaiting_consume 期限短于 P 的 awaiting_outcome；持续流量。断言：
    - A 与流量任务的 loss_count 均为 0；
    - P 在至多 1 + max_task_losses 次期限事件后被识别；
    - 恢复 v0.17 删掉的预期（无辜 task 不进入 manual_only）。
  - **单绑定远端挂起**：仍为第一次期限即计数（回归）。

#### C18-03 [MINOR] 暂缓 intent 的生命周期未与既有规则衔接：阶段写入、重启续送、目标实例、绑定时点、作废

- **位置**：01 v0.18 §2.2d L184（阶段期限 R13）、L186（执行绑定）、L188（暂缓）；§2.5 出向协议 L320–328；DispatchReceipt L301。
- **依据**：
  - L184："execute 型 dispatch 的 intent 事务 → awaiting_consume……期限自该事务提交时刻起算"。
  - L188："写 intent 后暂缓（`held_for_isolation = true`，不放行、不计时、不构成执行绑定），隔离头离开执行可能阶段后按序放行"。
  - L324："(a) intent 无 completed ∧ target_epoch == 当前 epoch → 以同 request_id 重送"。
  - L186："实例 hello 完成（就绪）之前不得写入 execute 绑定；实例的 lapsed / retiring 判定与 **intent 提交**按同一实例状态串行化"。
- **问题**：
  1. R13 规定 intent 事务写入 awaiting_consume 并起算期限；暂缓要求"不计时"。两条没有衔接，应改为在放行事务里写阶段与期限。
  2. §2.5 恢复规则 (a) 会在编排重启后重送全部"intent 无 completed 且 target_epoch == 当前"的 receipt，暂缓的也在内。L188 只泛称"重启不得绕过"，(a) 本身没有 held 条件。
  3. 暂缓期间隔离头所在实例退役、换了实例，暂缓 intent 的 target_epoch 已过时，"按序放行"不能直接发送，须走 (b) 的替代协议（新 request_id、新 target_epoch）。
  4. 执行绑定的实际时点是**放行**（held → false），不是 intent 提交。"就绪前不得绑定"和"与退役判定串行化"两条应同样适用于放行事务。
  5. 授权在暂缓中过期，或 task 被关闭 / 耗尽时，暂缓 intent 须同事务作废；否则"按序放行"会把已关闭 task 的派发发出去。C-09 守卫会拒绝核销，所以不会造成发布，但会产生无意义的出向与审计噪音。
  6. 隔离头离开后，暂缓 intent 和下一个 ready 成员谁先没有写。
- **候选改动**：

```diff
--- 01 §2.2d 全局隔离通道（暂缓）
- 一律写 intent 后暂缓（`held_for_isolation = true`，不放行、不计时、不构成执行绑定），隔离头离开执行可能阶段后按序放行。
+ 一律写 intent 后暂缓（`held_for_isolation = true`，不放行、不写阶段与期限、不构成执行绑定）。**放行事务**：held := false，复核 task 非终态且守卫（C-09 / ④ 与 recovery_mode）仍允许；target_epoch ≠ 当前 epoch 时改走 §2.5 (b) 替代协议；写入 R13 阶段并起算期限；放行即构成执行绑定，适用"就绪前不得绑定"与"与退役判定串行化"。隔离头离开执行可能阶段后，先按序放行全部暂缓 intent，再由通道为下一个 ready 成员预约（C18-01），防止普通流量在通道非空时长期暂缓。task 关闭、耗尽或授权过期的事务同事务将其暂缓 intent 置 superseded（superseded_by = 关闭事件）。
--- 01 §2.5 出向协议恢复规则
- #  (a) intent 无 completed ∧ target_epoch == 当前 epoch → 以同 request_id 重送（同一 broker 实例进程内去重）；
+ #  (a) intent 无 completed ∧ held_for_isolation = false ∧ target_epoch == 当前 epoch → 以同 request_id 重送（同一 broker 实例进程内去重）；held 的 intent 只由 §2.2d 放行事务处理；
--- 01 §2.2d R13 阶段期限
- execute 型 dispatch 的 intent 事务 → awaiting_consume；
+ execute 型 dispatch 的 intent 事务（暂缓者为放行事务）→ awaiting_consume；
```

- **副作用**：
  - 没有新状态值：作废复用 superseded，只是 superseded_by 指向关闭事件而非新 receipt（须在模型注释中说明）。
  - "先放行、后预约"让普通流量在两个隔离头之间有一个窗口。这个窗口与 C18-01 的排空一起决定隔离吞吐，两者都有界。
- **配套测试 / 夹具**：CF-IPC-10 增加以下用例：
  - 暂缓 intent × 编排重启 → 不重送；
  - 暂缓中换实例 → 放行走替代协议；
  - 放行与 lapsed 判定并发 → 判定先提交则不放行、不构成绑定；
  - 暂缓中授权过期 → intent superseded，不发送；
  - awaiting_consume 期限从放行起算。

#### C18-04 [MINOR] 执行绑定没有结束条件：已终结或已转只探测的 task 仍"绑定"在实例上

- **位置**：01 v0.18 §2.2d L186（执行绑定）、L187 ②③、L191（launcher）。
- **依据**：
  - L186："某 task 对某实例的执行绑定 = 一条已放行发送的 execute 型 DispatchReceipt（state = intent 或 completed，`held_for_isolation = false`），其 target_epoch == 该实例 epoch"。
  - L191："退役时**该实例上没有任何执行绑定**的 lapsed（含任务已全部完成之后的无任务失效——不因曾经承担过任务而永久免计）"。
- **问题**：谓词只看 receipt，不看 task 是否非终态、是否仍在执行可能阶段。completed 的 execute receipt 在 task 终结后一直存在，所以按字面，实例上曾完成过的 task 都算"绑定"：
  - (a) 任务全部完成后的失效仍"有绑定"，归任务域，launcher 不计。这与 L191 的括注直接矛盾，"不因曾承担过任务而永久免计"落空。
  - (b) 毒丸与若干已终结 task 同实例崩溃时，绑定者 ≥ 2，已终结 task "进入隔离通道"没有定义。
  - (c) 已转 indeterminate（awaiting_probe）的 task 也被算作绑定者，而 v0.17 明确 awaiting_probe 不计执行中断。

  v0.17 嫌疑集的阶段条件（awaiting_consume / outcome / reconcile）在本版重写时丢了。
- **候选改动**：

```diff
--- 01 §2.2d 执行绑定
- 某 task 对某实例的执行绑定 = 一条已放行发送的 execute 型 DispatchReceipt（state = intent 或 completed，`held_for_isolation = false`），其 target_epoch == 该实例 epoch——**以 intent 提交为准，不看 ACK**。
+ 某 task 对某实例的执行绑定 = 该 task **非终态、阶段 ∈ {awaiting_consume, awaiting_outcome, awaiting_reconcile}**，且其**最近一条** execute 型 DispatchReceipt 已放行（state = intent 或 completed，`held_for_isolation = false`）、target_epoch == 该实例 epoch——**以 intent 提交（暂缓者为放行）为准，不看 ACK**。task 终结、转 awaiting_probe 或其 receipt 被替代，绑定即结束。
```

- **副作用**：无。判定所需字段（phase、task 终态、最近 receipt）均已持久化，RetirementEvent.bound_task_ids 快照不变。
- **配套测试 / 夹具**：CF-AUTH-20i 增加以下用例：
  - 实例完成 2 个 task 后无任务 lapsed → 计启动 / 健康失败；
  - P 与已终结 task 同实例崩溃 → 绑定集 {P}，P +1；
  - indeterminate task 与 P 同实例 → 不入绑定集。

#### C18-05 [MINOR] `retire_requested` 等计划内退役没有归属域

- **位置**：01 v0.18 §2.2d L187（故障归责）；RetirementEvent L302–306；L195（C-11a 持有者未静默）。
- **依据**：
  - RetirementEvent：`cause: Literal["phase_deadline","lapsed","retire_requested","start_failure"]`；`domain: Literal["task","start_health"]`。
  - 归责只列 ① 阶段期限、② 无触发者 lapsed、③ 无绑定 lapsed / 启动失败。
  - L195："confirmed_not_happened 而持有者未静默（如持有者即当前实例）→ 记录观测、响应 `retire_requested` 并将持有者实例标记 retiring"。
- **问题**：
  - retire_requested 是编排为取得静默证明而**主动**退役实例，不是故障。但 ①②③ 都不覆盖它，domain 又只有两个值，实现只能把它塞进其中一个：
    - 按 ②（有绑定）处理：同实例在飞的无辜 task 被计 interrupt，或被拉进通道；
    - 按 ③ 处理：launcher 把计划内退役计为健康失败，连续几次就停止自动拉起。
  - 这种情形会发生：probe 在当前实例上发出，而通道无 ready 成员时该实例同时承载普通发布。
  - 运维显式重启（部署升级）也一样，现文下会表现为 lapsed 并被归入任务域。
- **候选改动**：

```diff
--- 01 §2.2d 故障归责
+ ④ **计划内退役**（cause = `retire_requested`，或运维经 launcher 接口登记的 drain / restart）→ domain = `planned`：不计任何计数、不进入隔离通道、不计启动 / 健康失败；同实例 task 解除定时器后按常规重排（已核销者等静默）。未经 launcher 登记的运维重启按 lapsed 处理。
--- 01 §2.5 RetirementEvent
-     cause: Literal["phase_deadline","lapsed","retire_requested","start_failure"]
-     domain: Literal["task","start_health"]; trigger_task_id: str | None = None
+     cause: Literal["phase_deadline","lapsed","retire_requested","planned_restart","start_failure"]
+     domain: Literal["task","start_health","planned"]; trigger_task_id: str | None = None
```

- **副作用**：
  - 新增一个枚举值（dev7 内）。
  - 运维重启须先经 launcher 登记，这是部署契约上的一条新要求，应同步写入 HLD B-7 部署契约，登记时一并记录。
- **配套测试 / 夹具**：CF-AUTH-20h / 20i 增加以下用例：
  - retire_requested 时同实例有 2 个在飞 task → 两者计数不变、不进入通道，launcher 连续失败计数不变；
  - 已登记的 drain / restart → 同上；
  - 未登记的重启 → 按 lapsed 归责。

#### C18-06 [MINOR] 与任务无关的 broker 健康故障在有绑定时全部计入任务域：病态 broker 会逐个耗尽无辜任务，且永不停机

- **位置**：01 v0.18 §2.2d L186、L187 ②、L191。
- **依据**：L191："**有执行绑定的失效只归任务域**——两种计数以同一谓词划界、互斥且完备，执行期与核销前毒丸都先被任务计数识别，不触发全局停机"。
- **问题**：以 intent 提交划界是本方上一轮 C17-03 提出的谓词，它的代价当时没有写出。broker 自身的健康问题（内存泄漏、依赖库崩溃、宿主资源耗尽）只要崩溃时有绑定，就算到任务头上。持续流量下：
  - 单绑定 → 该 task +1；多绑定 → 进入通道，隔离头单独执行时崩溃 → 隔离头 +1。
  - 每个任务至多被计 max_task_interrupts 次，但被波及的任务数没有上界。
  - launcher 只在"无绑定"时计数，有流量时永远不会停止自动拉起。

  结果是，一个坏掉的 broker 会把排队的发布逐个变成 dispatch_loss_exhausted 或 manual_only，而本该触发的是"停机 + 告警"。
- **候选改动（跨任务熔断）**：

```diff
--- 01 §2.2d launcher 启动 / 健康失败上界（末尾追加）
+ **跨任务熔断**：任务域内连续 `max_distinct_task_faults`（配置，缺省 2）次有计数的退役事件分别落在**不同 task** 的排他执行上（绑定集恰为一个 task，含隔离头），且其间没有任何 release task 正常完成一次执行可能阶段 → 判定为 broker 健康故障：launcher 停止自动拉起、告警并计入 R13；已计的任务计数不回滚，熔断期间不再计入任务计数；人工恢复后清零。毒丸只会让同一 task 反复计数，不触发熔断。
```

- **副作用**：
  - 毒丸与健康故障交替出现时可能提前熔断。这是转人工，属于安全方向。
  - 新增一个配置项和一种 R13 告警类型。
  - 熔断判定只读 RetirementEvent 序列，不新增 Ledger 表。
- **配套测试 / 夹具**：CF-AUTH-20i 增加以下用例：
  - FakeBroker 在处理任意 intent 后 N 秒崩溃（与载荷无关）+ 持续流量 → 至多 `max_distinct_task_faults` 个 task 被计数后，launcher 停止自动拉起；
  - 单个毒丸 P + 其余正常 → 熔断不触发，P 照常被识别。

#### C18-07 [NIT] recovery_mode 迁移条件自相矛盾；`authorization_expired_in_isolation` 的位置；排序键

- **位置**：01 v0.18 L190、L188、L587。
- **依据**：
  - L190："`isolating` →（`isolation_state = diagnostic_done` 且未耗尽）`active`"。
  - L188："达到上限或业务终结时为 diagnostic_done"；"成员身份……回到 active 后也不丢失顺序与计数"。
  - L587：ConsumeRejected.reason 增 `authorization_expired_in_isolation`。
- **问题**：
  1. diagnostic_done = 达到上限或业务终结，"且未耗尽"之后只剩业务终结，而已终结的 task 回到 active 没有意义。成员实际上不会以非终态回到 active（隔离头要么终结，要么崩溃转 waiting_holder，要么转 probe_only / manual_only），所以"回到 active 后不丢失顺序"无从发生。
  2. 等待中的成员与暂缓 intent 都没有送达 broker，过期关闭是编排侧事务，不经过 consume。broker 只有在派发已放行之后才会看到这个原因，而那时它已不在"等待中"。
  3. 排序键 (进入通道序, expires_at 或 consumed_at, task_id) 在同一位置混比两种时间：结果确定，但语义不一。
- **候选改动**：

```diff
--- 01 §2.2d recovery_mode 迁移
- `active` / `waiting_holder` →（归责结果为进入隔离通道）`isolating` →（`isolation_state = diagnostic_done` 且未耗尽）`active`；
+ `active` / `waiting_holder` →（归责结果为进入隔离通道）`isolating`（保持至 task 终结；耗尽时转 `manual_only` 或关闭）；
--- 01 §2.2d 全局隔离通道
- 成员身份由 `suspect_set_id` / `isolation_seq` 保留，回到 active 后也不丢失顺序与计数。
+ 成员身份由 `suspect_set_id` / `isolation_seq` 保留，直至 task 终结。
- 成员按 (进入通道序, 未核销者的授权 expires_at 或已核销者的 consumed_at, task_id) 排序
+ 成员按 (进入通道序, 未核销者在前、按授权 expires_at；已核销者在后、按 consumed_at, task_id) 排序
--- 01 §5 ConsumeRejected
- reason: Literal["authorization_expired","authorization_expired_in_isolation","stale",……]
+ reason: Literal["authorization_expired","stale",……]   # authorization_expired_in_isolation 为编排侧 C-09② 关闭与 FeedbackReport 的 reason，不经 consume 返回
```

- **副作用**：无行为变化，只是消除歧义。若保留在 ConsumeRejected 中，须写明何时由 consume 返回。
- **配套测试 / 夹具**：CF-AUTH-20k：等待中授权过期 → FeedbackReport.reason = authorization_expired_in_isolation，不产生 ConsumeRejected。

---

## 同步项

已核对 HLD v2.8 附录 B 第 7 组：
- L979 已登记"candidate 受理的预校验结果与完成事务复核（含 `candidate_recheck_failed` 与'预校验拒绝不登记 candidate'）"。
- L982 已登记"部署契约：无 PHP 约束（D23）——插件与受限 adapter 注册信息含运行时声明，PHP 拒绝注册"。

本版 HLD 改动在 01 中尚未同步的内容均已登记，**无新增同步项**。若采纳 H28-02，B-7 L982 的"注册信息含运行时声明"宜改为"注册时制品内容扫描与运行时一致性检查"；若采纳 C18-05，部署契约增加"运维重启须经 launcher 登记"。

## 交付备注

- 只新增本文件，未修改被审文档。
- 第二部分 NO-GO 的两个 MAJOR 共用一条修法："计数前提 = 绑定集恰为一个 task"，加上隔离头先排空再放行。改动集中在 §2.2d 故障归责 ①② 与全局隔离通道两段，不改命令、不改状态机。
- C18-03 至 C18-07 是同一段落的衔接与边界补全，可在同一版收入。
