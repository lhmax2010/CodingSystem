# HLD v2.13 / 01 v0.23 / 09 v0.3 第二十三轮定向核对 — Claude Code

## 结论

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| HLD v2.13（A30、Q1–Q4、§13 P0 同步项） | **GO** | 0 | 0 | 1 | 2 |
| 01 v0.23（A3 v0.23 条及直接相交路径） | **GO** | 0 | 0 | 3 | 1 |
| 09 v0.3（W1–W6） | **GO** | 0 | 0 | 2 | 0 |
| 同步项（不计入结论） | — | — | — | — | 4 条 |

- **01**：上一轮唯一的 MAJOR（Z1）已关闭：C-10a 与 C-11a 两条自动负向路径都检查锁存，人工规则的优先级也已写明。剩下三条 MINOR 都在"锁存为真之后怎样收尾"这条人工路径上，没有自动路径会把部分已发布的授权判为未发布。
- **09**：§3.1 的批次表与本版新写的划分规则（"每条恰属一批""gate 所用条目先通过"）有三处冲突。其中 P4 gate 要跑的 §11.3 类别会用到第三批（3-19）才通过的条目，而 M1.5 是 2-26。

---

## 输入与验证边界

**输入**
- `git pull --rebase origin main`：Already up to date。HEAD = `7652a57924d870eabc190643d7870ec3b5a759e5`。
- sha256：
  - `docs/00_Framework_HLD_v2.13.md` = `db4507dade13c2d095dc61853d06ecb4dcda6a43d69193d46f78e5f8fe88d03d`
  - `docs/01_Contract_Spec_v0.23.md` = `9764feb15416b4752785d334e46de39bbe37502dd2a2199310f16e47597e0b78`
  - `docs/09_Phased_Dev_Plan_v0.3.md` = `d9aaa33bd3574ba5d083f180fc638eab36416f98f2aab0b2ba95b66d522a63dc`

**看了什么**
- **三份处置表**：`HLD_v2.12_review_disposition.md`、`01_v0.22_review_disposition.md`、`09_v0.2_review_disposition.md`。
- **上一轮三家原始意见**（`HLD_v2.12_01_v0.22_09_v0.2_review_{kimi,codex,claudecode}.md`）：只用来核对来源、计数与采用方案。
- **正文**：按句级 diff（v2.12→v2.13、v0.22→v0.23、v0.2→v0.3）定位全部改动，再读这些改动直接相交的段落：
  - **01**：C-10a / C-11a、§2.2d 的 K3–K5 与 S2、indeterminate 锁存段与 hello 扫描、§2.4 RunSummary、§2.5 的 AuthorizationRecord / ReleaseTaskState、§5.1 的报告与裁决模型、处理序、CF-AUTH-17d / 20i / 20j / 20k / 20o；
  - **HLD**：D23、§11.2、§11.3、§13 P0–P8、附录 B 第 7 组；
  - **09**：§1、§3、§3.1、§4.1–§4.6、§5、§8、§10。

**没看什么**
- 本轮其他评审方的意见。
- HLD、01、09 中与本轮改动不相交的章节（不做全文重审）。

**执行过的命令**（均带 `nice -n 19 ionice -c3`，串行）：
- `git pull --rebase origin main`、`git rev-parse HEAD`、`sha256sum`、`wc -l`、`diff`、`sed -n`、`grep`。
- 句级 diff 用三次小型 Python 脚本完成，均套在 `systemd-run --user --scope -p CPUQuota=100% -p MemoryMax=2G` 下，只读文件、不写仓库。
- 本轮没有复现脚本：H213-02 涉及的 Python AST 行为在上一轮已验证。
- 未构建、未跑测试、未建索引、未访问 Quickbuild、未安装任何软件。

---

## A. 处置表核对

### A1. 计数与来源

| 处置表 | 声称 | 核对 | 结论 |
|---|---|---|---|
| HLD_v2.12 | 6 条 → 4 个问题，2 处合并 | Kimi H22-01（1）、Codex H212-01（1）、CC H212-01 至 H212-04（4），共 6 条。Q1 = Codex H212-01 + CC H212-02；Q2 = CC H212-01；Q3 = CC H212-03 + Kimi H22-01；Q4 = CC H212-04 | **正确** |
| 01_v0.22 | 8 条 → 5 个问题，2 处合并 | Kimi K22-01（1）、Codex C22-01 与 C22-02（2）、CC C22-01 至 C22-05（5），共 8 条。Z1 合并三家，Z3 合并 Codex C22-02 与 CC C22-03 | **正确** |
| 09_v0.2 | 10 条 → 6 个问题，2 处合并 | Kimi P22-01（1）、Codex P22-01 至 P22-03（3）、CC P092-01 至 P092-06（6），共 10 条。W1 含 4 条，W2 含 2 条，W3–W6 各 1 条 | **正确** |

三家各自的结论与分级计数，在三张表的"裁决输入"中都与原文一致。

### A2. "采用谁的方案"

逐条与原意见对照，表述都准确：
- **Q1**：完整 digest 加制品清单取 Codex，只读前缀与 PYTHONDONTWRITEBYTECODE 取 CC。
- **Q3**：契约句取 Kimi，覆盖清单取 CC。
- **Z1**：自动路径加锁存取 CC / Kimi，"先并入再判定"与 §5.1 优先级取 Codex。C-10a 的防御性检查是处置方新增的，表中写明"另加"。
- **Z3**：canonical 摘要取 Codex，②/⑤ 拆分、probe_targets 与 RunSummary 取 CC。
- **W1**：口径统一取 Codex 与 CC P092-01，补条目取 CC P092-02，逐条映射取 Kimi。
- **W2**：只检测只告警与宽限期取 CC，按核销分流与"人工处理"的含义取 Codex。

本方上一轮的两条同步项都有落点：
- S1 落到 HLD §13 P0；
- S2 落到 09 第一批的"ReleaseOutcomeRequest 可选的逐目标观测"。

### A3. 正文落实

| 处置 | 正文位置 | 结论 |
|---|---|---|
| Q1 | HLD L877："pyc 与源文件一样按自身完整文件 digest 免除……制品清单……不从待扫描 pyc 自报生成清单……安装前缀对运行用户只读，并以 PYTHONDONTWRITEBYTECODE=1（或 -B）运行"；L880 用例 | 已落实 |
| Q2 | HLD L877 (a)/(b) 两项判据；L880 用例中的隐式拼接、f-string 与两种注释 | 已落实。非 Python 语言的口径见 H213-02 |
| Q3 | HLD L877："本产品在宿主上的全部进程——编排、worker、Approval 服务、Build Gateway、MCP 服务、broker，以及 launcher 拉起的 CLI 与构建边界——及其子孙进程"；"exec 记账覆盖同一范围"；L880 哨兵用例 | 已落实。枚举不全，见 H213-03；09 未跟进 exec 记账，见 P093-02 |
| Q4 | HLD L124："'现行版本'取部署所用策略版本绑定的 HLD 版本……每次 Run 创建时……复核" | 已落实。撤销的生效依赖部署是否升级策略，见 H213-01 |
| §13 P0 | HLD L893 分批口径；09 M0b、§3.1 | 两份文档的措辞一致。批次内容与规则的冲突见 P093-01 |
| Z1 | 01 L161（C-11a 加锁存条件与锁存为真的出口）；L175（C-10a 防御）；L218（"合法报告先同事务把其 targets 中的 appeared 并入……再判定出口"）；L316 注释；L651 优先级 | 已落实。自动路径已闭合；人工收尾路径的残余问题见 C23-01 至 C23-03 |
| Z2 | 01 L640 target_refs 与生成方；L651 并集恰等于 manifest | 已落实。证据时点见 C23-02 |
| Z3 | 01 L294 target_ref 的定义与 manifest 内去重；L629–634 ②/⑤ 拆分；L637 probe_targets；L287 RunSummary.release_targets | 已落实。release_targets 的取值口径见 C23-01 |
| Z4 | 01 L195 K4③；L199 判定顺序 ③→②→①；L210 S2 | 已落实。措辞残留见同步项 S2 与 S3 |
| Z5 | 01 L352 置位、清除规则与不变式；L219 hello 扫描过滤 | 已落实。策略主动退出的路径见 C23-04 |
| W1–W6 | 09 M0b、§3.1、§4.1–§4.6、§10 | 均有落点。残余问题见 P093-01、P093-02 |

---

## 负责人七项裁决（独立判断）

| # | 裁决 | 判断 | 理由 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时必须出报告、不得当通过 | **成立** | 两支在同一 series 上汇合，超时作为 incomplete 条目留存，审批与核销都复核放行谓词。09 v0.3 第一批把 incomplete / retried / acknowledged_gaps 放进 Demo 路径，执行面没有放松 |
| ② | Quickbuild 默认取最新 Profile 快照，在 Run 启动时固定 | **成立** | 固定在 Run 启动时，Run 内的"最新"不会漂移，并以读回核对实际输入。09 的 Quickbuild 证据等级验收与 4-30 检查点保持"前提不足即不启用"。P093-01 只涉及能力声明 schema 的批次，不影响本裁决 |
| ③ | Profile 严格匹配，并预留小改动复用的预案 | **成立** | 缺省严格匹配；放宽要等非劣评估，09 排在 2027-07，先有真实数据再放宽 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | 范围只增不减；09 v0.3 已把 focus_modules 放入第一批，ModuleRegistry 与 always_run 放入第二批，Demo 第 1 步与 P4 gate 都有契约落点 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | AI 的建议与客观验证分开；09 要求有 AI / 无 AI 两条路径都给出结果，回放记录绑定验收 id，修复以重新构建为准 |
| ⑥ | Quickbuild 可指定 Base CL，否则默认最新，并读回核对 | **成立** | 请求值与实际输入经读回比对，不一致走 base_mismatch 出口；改用其他后端须显式改配并以新 Run 执行 |
| ⑦ | 超时后重试成功可以发布，但须审批人逐条确认 | **成立** | acknowledged_gaps 按（条目 id，内容 digest）绑定，核销前复核；Demo 审批画面要求逐条确认 |

D23"不得引入 PHP"、人力基线、总部方案确认随 12-29 Demo 进行，都是负责人前提，本报告只接受，不评价。

---

## B. HLD v2.13

### H213-01 [MINOR] "现行版本"由部署自选的策略版本决定，部署不升级策略，例外就撤销不了

- **位置**：D23（L124）"'现行版本'取部署所用策略版本绑定的 HLD 版本，该绑定随签名表一起发布；每次 Run 创建时……复核所依赖的例外仍在现行清单中且未到期"。

**问题**
- v2.12 的承诺是"现行版本删除该条目即撤销，不等到期"。
- v2.13 把"现行版本"定义为"部署所用策略版本"绑定的版本，而部署用哪个策略版本由部署自己决定。
- 全文没有"部署必须使用最新策略版本"或"最低有效版本"的约束。§11.3 中"策略版本 +1 → 已注册插件重扫"只在部署确实升级之后才触发。
- 结果是撤销能否生效，取决于运维何时升级策略。

**反例**
1. 负责人修订 D23 批准例外 E：工具 T、digest d、到期日 2027-06-30。E 进入 HLD v2.14，策略版本 P5 绑定 v2.14。
2. 2027-03 负责人撤销 E：HLD v2.15 删除该条目，策略版本 P6 绑定 v2.15 并发布。
3. 内网部署仍运行 P5（没有任何规则强制升级）。
4. 此后每次创建 Run，门禁按 P5 所绑定的 v2.14 复核：E 在清单中、未到期，于是通过。T 一直可用到 6-30，"删除即撤销"没有生效。

**候选修改**（D23 L124）：

```diff
-"现行版本"取部署所用策略版本绑定的 HLD 版本，该绑定随签名表一起发布；
-每次 Run 创建时，在 digest 比对的同一检查中复核所依赖的例外仍在现行清单中且未到期，否则拒绝创建 Run（v2.13）；
+"现行版本"取部署所用策略版本绑定的 HLD 版本，该绑定随签名表一起发布；
+策略发布源同时发布单调递增的**最低有效策略版本**与**例外撤销清单**（条目：工具名 + 安装件 digest + 撤销所在 HLD 版本），
+二者不随部署所选策略版本冻结，门禁每次从发布源读取（本地缓存超过 `revocation_max_age` 即视为不可用）；
+撤销例外的 HLD 修订同时提升最低有效策略版本；
+每次 Run 创建时，在 digest 比对的同一检查中复核：部署所用策略版本 ≥ 最低有效策略版本，
+且所依赖的例外仍在现行清单中、不在撤销清单中、未到期——任一不满足或发布源不可用即拒绝创建 Run（v2.13，R23）；
```

附录 B 第 7 组 v2.13 追加项同步加入"最低有效策略版本与例外撤销清单的发布格式、缓存时限"。

**副作用**
- 部署在创建 Run 时依赖策略发布源可达。发布源不可达超过缓存时限会 fail-closed，拒绝创建 Run。这是有意的代价，需要在内网部署时提供本地发布源镜像。
- 例外以外的扫描规则不受影响。

**测试**（§11.3 无 PHP 用例组追加）：
- 部署停在策略 N，发布源把 E 列入撤销清单 → 下一次 Run 创建被拒；
- 最低有效策略版本提升到 N+1 → 停在 N 的部署 Run 创建被拒；
- 发布源不可达且缓存超时 → 拒绝；缓存未超时 → 按缓存判定。

### H213-02 [NIT] 片段判据只给了 Python 的 AST 口径；其他语言与 bytes 常量怎样判定没写

- **位置**：§11.2（L877）"字符串按 AST 常量判定，相邻字面量的隐式拼接视为一个常量……f-string（JoinedStr）中的任何命中一律不免除；注释由 tokenizer 定位"；签名表"给出各语言的注释符与规范化规则"。

**问题**
- 判据的适用对象是"非 PHP 语言写的扫描器与测试源码（如 Python）"，但 JoinedStr 是 Python AST 的节点名。
- 签名表只按语言给出注释规则，没有给出字符串的解析器与求值规则。
- D23 的范围还包括 shell 部署脚本、只读 Web 视图前端（JS）等，这些语言没有对应的口径：
  - JS：模板字面量 `` `<?php ${x}` `` 算不算可豁免的常量？
  - shell：`'<?''php'` 这种相邻引号拼接按什么规则合并？
- Python 自身也有一个缺口：`b"<?php"` 求值后是 bytes，和签名表中的 str 是否"完全相等"未定义。扫描器按字节读文件，很可能写成 bytes 常量。
- 两种实现都能声称合规：一种把未知语言当常量豁免，一种按文本信号拒绝。

**候选修改**（L877 (a) 项与签名表说明）：

```diff
-(a) 位于字符串字面量或注释内：字符串按 AST 常量判定，相邻字面量的隐式拼接视为一个常量、以求值后的值比较，f-string（JoinedStr）中的任何命中一律不免除；注释由 tokenizer 定位；
+(a) 位于字符串字面量或注释内：字符串按签名表为该语言登记的解析器取常量（Python：ast；相邻字面量的隐式拼接视为一个常量、以求值后的值比较；
+bytes 常量按 latin-1 解码后比较），带插值的字符串（Python f-string / JoinedStr、JS 模板字面量含 `${}`、shell 含变量展开的双引号串）中的任何命中一律不免除；
+注释由该语言的 tokenizer 定位；签名表未登记解析器的语言不适用片段豁免，命中即按文本信号判定；
```

**副作用**：未登记语言的测试源码如果含签名字面量会被拒，需要把这类夹具改成运行时拼接（与现行"负向夹具在测试运行时拼字节生成"一致）。

**测试**（§11.3 v2.13 追加组）：
- Python `b"<?php"` → 通过；
- 未登记解析器的语言文件中含 `"<?php"` → 失败；
- 登记 JS 后，`` `<?php` `` 通过、`` `<?php ${x}` `` 失败。

### H213-03 [NIT] "全部产品进程"的枚举漏了只读 Web 视图后端，也没有可机械核对的来源

- **位置**：§11.2（L877）"本产品在宿主上的全部进程——编排、worker、Approval 服务、Build Gateway、MCP 服务、broker，以及 launcher 拉起的 CLI 与构建边界——及其子孙进程"；附录 B 第 7 组"执行准入与 exec 记账覆盖全部产品进程的部署检查项"；§11.3 只有"worker、编排进程直接 spawn 未声明的哨兵程序"一例。

**问题**
- D23 的范围（L124）包括"只读 Web 视图及其前端"，§10 部署拓扑中它是宿主上的独立服务，但不在上面的破折号枚举里。
- 枚举读起来是穷尽的，部署检查项又没有说明"全部"以什么清单为准。
- 实现者可能只给枚举中的 systemd 单元配置 ExecPaths=。

**反例**：
1. Web 视图后端以独立单元部署，没有配置执行准入。
2. 某次升级引入一个渲染 diff 的辅助工具；该工具调用了只被列出、未被声明的预装包。
3. 这一路径既不被拦截，也不进 exec 记账。
4. §11.3 只测 worker 与编排，部署检查也没有可比对的单元清单，于是验收通过。

**候选修改**（L877 与附录 B 第 7 组）：

```diff
-**本产品在宿主上的全部进程**——编排、worker、Approval 服务、Build Gateway、MCP 服务、broker，以及 launcher 拉起的 CLI 与构建边界——及其子孙进程，
+**本产品在宿主上的全部进程**——以 DeploymentInventory 登记的产品单元为准，至少含编排、worker、Approval 服务、Build Gateway、MCP 服务、broker、只读 Web 视图后端，以及 launcher 拉起的 CLI 与构建边界——及其子孙进程，
```

部署检查项改为："逐个核对 DeploymentInventory 中的产品单元都配置了执行准入与 exec 记账；产品 cgroup 子树内出现不属于任何登记单元的进程，即判验收失败"。

**副作用**：DeploymentInventory 需要登记单元清单。v2.11 已有 DeploymentInventory 的规范化输入，这里只是加一个字段。

**测试**（§11.3）：
- 新增一个未配置执行准入的产品单元 → deploy 验收失败；
- Web 视图后端 spawn 未声明的哨兵程序 → 执行前被拒并记 `deployment_dependency_violation`。

---

## C. 01 v0.23

### C1. 锁存是否约束全部负向结案（按 brief 第 1 点逐条构造）

| 路径 | v0.23 文本 | 结论 |
|---|---|---|
| C-11a 自动负向映射 | L161 / L218："confirmed_not_happened ∧ 持有者静默 ∧ `observed_any_appeared = false` → release_failed"；锁存为真 → 不映射、记冲突、计入 R13、同事务置 manual_only | 闭合 |
| C-10a 未发生分支 | L175：锁存为真 → 不授予执行许可、不映射，转 indeterminate | 闭合（防御性。正常情况下锁存为真时任务已在只探测，见同步项 S4） |
| C-11 人工裁决 | L651：锁存为真时"全部未发生只允许 confirm_not_released"不适用；已记录观测的约束覆盖全部分支 | 闭合 |
| K3 耗尽 | L194：已核销者转 manual_only，未核销者 release_failed(dispatch_loss_exhausted)；锁存只会在已核销后置真 | 不受影响 |
| 授权过期 | 只对未核销授权生效 | 不受影响 |
| admin_finalize | 只在 C-10a 锁存为假的未发生分支与 (b) 序中被消费 | 不受影响 |

反例逐项检查：
- **部分发布后远端撤回**：对账 [appeared, absent] → 只探测 [absent, absent]。走 C-11a 锁存为真的分支，不会自动结案。
- **乱序报告**：只探测按 token 串行，每次探测有自己的 probe_seq；同 request_id 的重放返回首响应，不会重新判定。
- **重启**：锁存与报告在同一事务落账。
- **强制探测**：manual_only 下全部未发生，被锁存覆盖。

自动路径在 v0.23 中已无反例。残余问题都在锁存为真之后的人工收尾上，见 C23-01 至 C23-03。

### C2. 其余各点

- **target_ref 与校验步骤**：canonical 摘要在 manifest 规范化时去重，载荷校验（②，不落回执）与双射校验（⑤，落回执、不改锁存）分开，与处理序 L654 的 ②/⑤ 定义一致。
- **probe_targets**：恒等于 manifest 全部目标。
- **K4 与 K5**：K4③ 只拦尚未放行的派发；K5 判定顺序 ③→②→①，CF-AUTH-20o 的 R22 格覆盖"manual_only 与 dispatch_paused 同时成立"。
- **strategy_managed 与 hello 扫描**：hello 扫描过滤统一为 `strategy_managed = false`，manual_only 任务只在 `auto_probe_suspended = false` 时发只探测，与括注一致。
- **contract_version**：1.0.0.dev12。
- **A3 v0.23 条**："8 条编号意见（5 个独立问题）"正确。

### C23-01 [MINOR] RunSummary.release_targets 取"最后一次观测"：锁存冲突后以 confirm_released 结案，曾出现的目标显示为 absent，开发者按 §5.1 会把它重新发布

- **位置**：
  - L287：RunSummary.release_targets"发布类 Run 结案时各目标最后一次观测"；
  - L651："后者在 RunSummary 中逐目标列出最后观测到的状态，未出现的目标由开发者经新 Run 补发"；
  - CF-AUTH-20j R22 格："部分发布以 confirm_released 结案 → RunSummary.release_targets 逐项等于最后一次观测"。

**问题**
- 锁存的语义是"以已发生为准"，但它只在授权级别记一个布尔值。
- RunSummary 逐目标呈现的是最后一次观测，而锁存冲突恰好发生在最后一次观测与历史观测相反的时候。
- 开发者在 RunSummary 中看不到冲突，§5.1 的指引又让开发者补发"未出现的目标"。

**反例**（双目标 T1、T2）：
1. 对账报告 [T1 appeared, T2 absent] → 锁存为真，任务进入 indeterminate。
2. 只探测 [T1 absent, T2 absent]（读到滞后副本，或 T1 被他人 abandon）→ C-11a 锁存为真的分支 → manual_only、告警。
3. 运维按 §5.1 只能选 keep_unknown 或 confirm_released，选了 confirm_released → Run 以 released 结案。
4. RunSummary.release_targets = [T1 absent, T2 absent]。
5. 开发者按 §5.1"未出现的目标由开发者经新 Run 补发"新开 Run，发布 T1 与 T2。
6. 如果 T1 实际存在（读滞后），T1 被发布两次。

这正是锁存要防止的结果，只是从契约内的自动结案换成了按契约指引的人工操作。

**候选修改**：

```diff
 # §2.5 AuthorizationRecord
     observed_any_appeared: bool = False  # ……
+    appeared_target_refs: frozenset[str] = frozenset()   # 逐目标正向事实锁存（R23）：受理合法 reconcile / probe 报告时与其中 appeared 的 target_ref 同事务取并；
+                                                         # 不清零；不变式 observed_any_appeared ⇔ appeared_target_refs 非空
```

```diff
 # §2.4 RunSummary
-release_targets: tuple[TargetObservation, ...] | None = None`（发布类 Run 结案时各目标最后一次观测，无观测为 unknown；R22）
+release_targets: tuple[ReleaseTargetSummary, ...] | None = None`（发布类 Run 结案时逐目标列出，R22，R23）
+class ReleaseTargetSummary(BaseModel): target_ref: str; last_state: Literal["appeared","absent","unknown"]; ever_appeared: bool
+   # last_state = 最后一次观测，无观测为 unknown；ever_appeared = target_ref ∈ appeared_target_refs；
+   # ever_appeared ∧ last_state ≠ appeared → 该项标"远端观测矛盾"
```

```diff
 # §5.1 已记录观测的约束
-后者在 RunSummary 中逐目标列出最后观测到的状态，未出现的目标由开发者经新 Run 补发。
+后者在 RunSummary 中逐目标列出最后观测状态与是否曾出现：只有 ever_appeared = false 的目标由开发者经新 Run 补发；
+ever_appeared = true 而最后观测非 appeared 的目标标为"远端观测矛盾"，须先核实远端再决定是否补发（R23）。
```

**副作用**
- release_targets 是 v0.23 新增字段，尚无消费者，改类型的成本低。
- contract_version 需升到 1.0.0.dev13。
- `observed_any_appeared` 保留为派生布尔量，现有守卫不变。

**测试**（CF-AUTH-20j 追加 R23 格）：
- 序列"对账 [appeared, absent] → 只探测 [absent, absent] → confirm_released"：release_targets = [{T1, absent, ever_appeared = true, 标矛盾}, {T2, absent, false}]；
- 在两份报告事务前后各 kill 一次，appeared_target_refs 不丢、不缩小；
- 锁存为假、全部 appeared 的正常 released：ever_appeared 全为 true、无矛盾标记。

### C23-02 [MINOR] confirm_not_released 的逐目标覆盖可以由"原 holder 静默之前"的 absent 观测凑齐

- **位置**：
  - L651："unknown 下 `confirm_not_released` 须有远端证据、其 `target_refs` 并集**恰等于**授权 manifest 的目标集合（逐目标覆盖，R22），且原 holder 已静默"；
  - "明确全部未发生 → 只允许 `confirm_not_released` 且原 holder 已静默"；
  - L640：probe_report 型的 target_refs 由编排从被引报告的 absent 项生成。

**问题**
- 自动路径明确要求负向结论来自静默**之后**的观测：L161 / L218"静默确认后由周期任务以新 probe_seq / 新 request_id 重新探测，再作负向映射"。
- 人工路径只要求"裁决时 holder 已静默"，不限制证据观测的时点。
- 静默之前的 absent 只说明"当时还没出现"，holder 之后仍可能发布。
- Z2 新增的逐目标覆盖可以由不同时刻、静默之前的报告拼成，锁存也不会触发：那些报告里没有 appeared。

**反例**（双目标 T1、T2，granted_epoch 持有者 H 发布缓慢）：
1. t1：只探测 #1 = [T1 absent, T2 unknown]，H 尚未推 T1。
2. t2：H 推送 T1 成功。
3. t3：只探测 #2 = [T1 unknown（该目标查询超时）, T2 absent]。锁存仍为假。
4. t4：H 被回收，静默确认。
5. t5：裁决前的强制探测因实例退役失败 → 按 unknown 处理。
6. 运维以 #1 与 #2 为证据提交 confirm_not_released：编排生成的 target_refs 并集 = {T1, T2}，holder 已静默，锁存为假 → release_failed。
7. T1 实际已发布，开发者重提后 T1 再次发布。

同一组事实走自动路径时，必须在 t4 之后重新探测，会看到 T1 appeared。

**候选修改**：

```diff
 # §5.1 C-11 guard
-unknown 下 `confirm_not_released` 须有远端证据、其 `target_refs` 并集**恰等于**授权 manifest 的目标集合（逐目标覆盖，R22），且原 holder 已静默；
+unknown 下 `confirm_not_released` 须有远端证据、其 `target_refs` 并集**恰等于**授权 manifest 的目标集合（逐目标覆盖，R22），且原 holder 已静默；
+**计入覆盖的证据须观测于原 holder 静默确认之后（R23）**：probe_report 型按 Ledger 提交序判定，早于静默确认的报告只作附加引用、不计入覆盖；
+external_record 型须声明 `observed_at`，晚于静默确认时间才计入覆盖；
+manual_only 分支"明确全部未发生 → 只允许 confirm_not_released"同样要求该次强制探测在静默确认之后落账，否则按 unknown 处理；
```

```diff
-class AdjudicationEvidence(BaseModel): kind: Literal["probe_report","external_record"]; ref: ArtifactRef; target_refs: tuple[str, ...] = ()
+class AdjudicationEvidence(BaseModel): kind: Literal["probe_report","external_record"]; ref: ArtifactRef; target_refs: tuple[str, ...] = (); observed_at: datetime | None = None
+   # external_record 型 observed_at 必填（R23）
```

**副作用**
- 运维在 holder 静默之后可能要多等一次探测。auto_probe_suspended 时经强制探测获得。
- 强制探测失败时只能用 external_record，而外部记录的 observed_at 是运维的声明，契约只能要求其存在并审计。
- 自动路径不变。

**测试**（CF-AUTH-20j 追加 R23 格）：
- 上述序列：两份静默前报告合计覆盖全部目标 → confirm_not_released 被拒；静默后一次全部 absent 的探测 → 允许；
- external_record 的 observed_at 早于静默 → 不计入覆盖；
- manual_only 下强制探测早于静默落账、结果全部 absent → 不适用"只允许 confirm_not_released"，按 unknown 处理。

### C23-03 [MINOR] 锁存冲突后 confirm_released 的"合格远端证据"没有定义；记录了出现事实的对账报告不能作为证据引用

- **位置**：
  - L651："锁存为真时本条不适用……只允许 `keep_unknown` 或有合格远端证据的 `confirm_released`"；
  - guard："evidence_refs 只收远端证据：本授权已落账的只探测报告或外部系统记录"；
  - L640：`AdjudicationEvidence.kind: Literal["probe_report","external_record"]`；
  - CF-AUTH-20j R22 格："对账部分出现 → 只探测全部 absent……keep_unknown / confirm_released 允许"。

**问题**
- 在 CF 的第一条序列里，唯一记录了 T1 appeared 的是 ReleaseReconcileReport，可它不属于 AdjudicationEvidence 的任何一种 kind。
- 已落账的只探测报告全都是 absent。
- "合格"没有定义，两种实现都能声称合规：
  - **实现 A**：只检查"证据非空"，于是引用一份全部 absent 的探测报告就能 confirm_released。证据与结论相反，"合格"形同虚设。
  - **实现 B**：要求证据中有 appeared，于是只能另找外部记录，记录了事实的对账报告反而用不上。
- 在这条 CF 格上，两种实现给出不同结果。
- 另外，L640 规定 probe_report 型的 target_refs 取"absent 项"。这条规则是为 confirm_not_released 写的，用在 confirm_released 上方向是反的。

**候选修改**：

```diff
-class AdjudicationEvidence(BaseModel): kind: Literal["probe_report","external_record"]; ref: ArtifactRef; target_refs: tuple[str, ...] = ()
-   # probe_report 型由编排从被引报告的 targets 取 absent 项生成，运维填写无效；
+class AdjudicationEvidence(BaseModel): kind: Literal["probe_report","reconcile_report","external_record"]; ref: ArtifactRef; target_refs: tuple[str, ...] = ()
+   # probe_report / reconcile_report 型（本授权已落账的报告）的 target_refs 由编排生成，运维填写无效：
+   # 用于 confirm_not_released 时取该报告的 absent 项，用于 confirm_released 时取其 appeared 项；external_record 型由运维逐目标声明（R23）
```

```diff
-只允许 `keep_unknown` 或有合格远端证据的 `confirm_released`，R22）；
+只允许 `keep_unknown` 或 `confirm_released`；后者的合格远端证据 = 至少一条证据的 target_refs（按上式生成或声明为 appeared）非空，
+锁存为真时编排可直接引用使锁存置真的那份报告（R22，R23）；
```

**副作用**
- AdjudicationEvidence 的枚举新增一值，contract_version 升到 dev13（与 C23-01 合并）。
- 一般情况下，确认"已发布"的人工结案更容易给出证据，方向是安全的。

**测试**（CF-AUTH-20j 追加 R23 格）：
- 序列一中，引用对账报告作 confirm_released → 通过，target_refs = {T1}；
- 只引用全部 absent 的探测报告作 confirm_released → 被拒；
- 用对账报告作 confirm_not_released 的证据 → 因锁存为真被拒（回归）。

### C23-04 [NIT] strategy_managed 只能随终结或 manual_only 清除，归因策略主动结束对某个 task 的管理时没有出口

- **位置**：L352"由归因策略在其纳入事务中置 true；task 终结或置 manual_only 的同一事务置 false……不变式：recovery_mode = isolating ⇒ strategy_managed = true"；CF-AUTH-20k R21 格"替换策略……只置 strategy_managed = true"。

**问题**
- 契约允许替换策略。
- 替换策略可能判定某个成员无辜、让它回到普通流程，但契约只给了两个清除点。该 task 会一直被 hello 扫描排除，后续能否派发完全取决于一个已经不管理它的策略入口。
- 参考策略 v1 中 isolating 保持到终结，所以不受影响。

**候选修改**（L352）：

```diff
-由归因策略在其纳入事务中置 true；task 终结或置 manual_only 的同一事务置 false，之后只探测与强制探测都走契约通道；
+由归因策略在其纳入事务中置 true；task 终结或置 manual_only 的同一事务置 false，之后只探测与强制探测都走契约通道；
+归因策略也可在其释放事务中置 false，须同事务把 recovery_mode 由 isolating 按授权实际状态改回 active / waiting_holder、按 K5 释放其预约并写唤醒，此后由 hello 扫描与周期任务照常处理（R23）；
```

**副作用**：无。参考策略 v1 不使用这一出口。

**测试**（CF-AUTH-20k 追加 R23 格）：
- 替换策略释放成员 X → 同事务清零、预约释放；
- 下一次 broker_hello 按 target_epoch 规则重派 X；
- 释放事务前后 kill，不出现 strategy_managed = false 而 recovery_mode = isolating 的状态。

---

## D. 09 v0.3

### D1. 逐项核对

- **M0b 分批口径**：与 HLD L893 一致。HLD 的 P0 gate 是"总部方案确认 + 三方 unanimous GO（第一批）"，09 M0b 是 12-31，第一批 12-11，两份文档的日期链一致。
- **第一批对 Demo 六步的覆盖**：

  | 步骤 | 第一批条目 |
  |---|---|
  | 1 | focus_modules、MCP 与 DSL |
  | 2 | 构建隔离、image.* 最小契约、SourceProvider 最小 Git |
  | 3 | Diagnosis 与 ai_draft、AI 证据 |
  | 4 | 空壳 Agent 输出 v1.0 核心已有的 UTReport / BenchReport / ReviewReport / ReleasePlan |
  | 5 | incomplete / retried / acknowledged_gaps、release_evidence |
  | 6 | DispatchReceipt 恢复规则 (a) |

  例外是 §4.2.6 规则①的 BenchReport 谓词，见 P093-01 (c)。
- **Demo 故障分支**：
  - broker 只检测、只告警；
  - 编排重启后有宽限期；
  - 按授权是否核销分流；
  - "人工处理"限于保留证据、受控排查与回收，不得直接改 Ledger；
  - kill 时点覆盖构建中、审批中、intent 前后、核销前后、outcome 前后；
  - Approval 与 broker 分开降级。

  逐条检查没有发现会把未核销授权迁入 publishing、或把已核销授权自动结案的路径。
- **回放记录**：绑定验收 id，出内网前逐条核对密级，没有这类记录时标为 FakeLLM；降级表两行同步。已落实。
- **D23 部署验收切片**：§4.2 与 11-27 降级行都已加入。exec 记账遗漏见 P093-02。
- **gate 对照表**（§10）：位置与三段完成日期已写明。
- **VD 措辞**：已改为"除 VD 外"。
- **日期与口径**：三份文档一致。09 §1 引用 HLD v2.13 与 01 v0.23；W1 周的核对对象已同步。

### P093-01 [MINOR] §3.1 的批次表与本版新写的划分规则冲突：P4 gate 会用到第三批条目，另有条目跨批、第一批有前向引用

- **位置**：
  - 09 §3.1：第二批、第三批的内容；"逐条映射"段"每条恰属一批……阶段 gate 所用 mock 的核心 schema 在该阶段开发与预验收之前通过"；
  - HLD L893："任一阶段 gate 验收时，其生产或消费的契约条目，含 mock 所用的核心 schema，必须已经三方评审通过"；
  - HLD L897（P4）："§11.3 全部测试类别……= 框架完成"；
  - 09 M1.5 = 2027-02-26。

**问题与反例**

(a) **P4 gate 会用到第三批条目。**
- §11.3 含 v2.5 追加的"后端能力加载期检查"（示例一改配 `backend: quickbuild` 且构建暂存输入 unverified → 加载拒绝），以及"Quickbuild 锁定 base"等类别。
- 这些用例消费"Quickbuild 后端能力声明、证据等级与 `comparison = unverifiable`"，而 09 把这些条目放在第三批（2027-03-19）。
- 2-26 做 M1.5 验收时，要么这些用例跑在未通过评审的契约上，违反 HLD L893；要么 M1.5 推到 3-19 之后，连带 M2 前的余量。
- 这条依赖不经过 Quickbuild 的真实联调（真实联调在 P6），只用到能力声明的 schema 与加载期规则。

(b) **条目跨批。**
- BenchReport 同时出现在第二批（"判定字段骨架"）与第三批（"BenchReport / BenchPolicy / MeasurementRecord"）；OptimizationPlan 同时出现在第二批（"与 purpose / 候选复核"）与第三批（"与 Profile 新鲜度"）。
- 逐条映射以"附录 B 第 7 组原文逐条编号为键……每条恰属一批"，而附录 B 中的"BenchReport 扩展字段（mode、gate_eligible……）"是一条，按现行规则无法拆进两批。

(c) **第一批有前向引用。**
- 第一批含"§4.2.6 三条规则"。规则①的"通过"谓词由 01 形式化，其中 BenchReport = `gate_eligible ∧ comparison = verified ∧ 未 baseline_revoked ∧ 无未决优化计划`，这些字段在第二批或第三批。
- 第一批要么定稿一个引用未定字段的谓词，要么把它留空，规则①就不完整。

**候选修改**（09 §3.1）：

```diff
 | 第一批 | ……注册按 mode 声明与 DSL 新字段（input、release_requires、rpm_precheck 等）及 §4.2.6 三条规则；……
+  （规则①的"通过"谓词在本批对 BuildReport / ImageReport / UTReport 定稿；BenchReport 谓词随第二批定稿，
+  此前校验器拒绝 release_requires 含 BenchReport 的流水线（fail-closed），Demo 流水线的 release_requires 不含 BenchReport）……
 | 第二批 | ……**P4 全量流水线 mock 所需的核心 schema**——……BenchReport / OptimizationReport 的判定字段骨架
+  （含 comparison 三值语义与规则①的 BenchReport 谓词）；
+  **后端能力声明的 schema 与 §4.2.6 后端能力加载期检查规则**（P4 §11.3"后端能力加载期检查""锁定 base"类别所需，以 mock 能力声明验证）……
 | 第三批 | Quickbuild 后端能力声明、证据等级与 `comparison = unverifiable`；……
+| 第三批 | Quickbuild 后端的**具体能力取值**与证据等级逐项结论；……
```

```diff
-**逐条映射（v0.3）**：11-20（M0a）前以 HLD 附录 B 第 7 组原文**逐条编号**为键，……每条恰属一批，……
+**逐条映射（v0.3）**：11-20（M0a）前以 HLD 附录 B 第 7 组原文**逐条编号**为键（一条须跨批时拆为"编号 + 字段组"子键，每个子键恰属一批），……
+映射表同时列出 P1–P4 gate 所跑 §11.3 各类别消费的条目，核对其批次不晚于第二批……
```

**副作用**
- 第二批略增：一个 schema 与一条加载期规则。Quickbuild 实测结论仍按第三批与 4-30 检查点推进，不受影响。
- Demo 不能把 BenchReport 放进 release_requires，这与"空壳 Benchmark 只证明结构"的定位一致。

**检查点**
- M0a 映射表验收时逐类核对"P4 gate 所跑 §11.3 类别 → 条目 → 批次 ≤ 2"。
- 校验器用例：第二批通过前，release_requires 含 BenchReport → 加载拒绝。

### P093-02 [MINOR] D23 部署验收切片与内网预检只覆盖执行准入，漏了 HLD v2.13 同时要求的 exec 记账

- **位置**：
  - 09 §4.2"D23 deploy 验收——主机安装集与本产品安装前缀扫描、E0 子进程观测、全部产品进程的执行准入（受控执行视图或 systemd ExecPaths=）生效"；
  - W1 内网预检第④项"mount namespace 与 systemd ExecPaths= 是否可用（D23 执行准入）"；
  - 11-27 降级行"D23 deploy 验收（主机安装集扫描、子进程观测、执行准入）未通过"。

**问题**
- HLD v2.13 L877 要求"exec 记账覆盖同一范围（全部产品进程及其子孙），deploy 验收时与声明清单比对"，并且"无法提供上述约束的工具环境不得以一次观测无命中通过验收"。
- ExecPaths= / NoExecPaths= 与只读 mount namespace 只提供准入，不产生 exec 记录。
- 非 launcher 进程的 exec 记账需要 auditd 的 execve 规则、fanotify，或基于 cgroup 的进程记账等机制。这些机制在受管的内网主机上通常需要 root 或 IT 审批。

**反例**：
1. W1 预检确认内网主机可以配置 systemd 单元与 ExecPaths=，第④项通过。
2. 产品用户无权配置 auditd，也不能加载 eBPF。
3. 12 月部署时，验收需要把 exec 记录与声明清单比对，才发现没有记录来源。
4. 11-27 检查点按现行措辞不会触发，问题会拖到 W6 部署之后才暴露。

**候选修改**：

```diff
 W1 内网预检④：……，mount namespace 与 systemd ExecPaths= 是否可用（D23 执行准入）
+，以及覆盖全部产品进程的 exec 记账机制（auditd execve 规则、fanotify 或 cgroup 进程记账之一）能否以批准的方式配置
```

```diff
 §4.2：- 首次在 Demo 主机部署前：D23 deploy 验收——……全部产品进程的执行准入（受控执行视图或 systemd ExecPaths=）生效，
+exec 记账覆盖全部产品进程及其子孙并与声明清单比对，
 DeploymentInventory 记录 approved_digest（HLD v2.13 §11.2）。
```

```diff
 11-27 检查点：| D23 deploy 验收（主机安装集扫描、子进程观测、执行准入）未通过 |
+| D23 deploy 验收（主机安装集扫描、子进程观测、执行准入、exec 记账）未通过 |
```

**副作用**
- 预检多一项，可能需要 IT 审批 audit 规则。拿不到时，按 §4.5 备选处理并登记补齐日期，与现行降级规则一致。

**检查点**
- 部署验收脚本在每个产品单元内 spawn 一个已声明的工具，确认 exec 记录中出现该工具且路径与声明清单一致；
- 关闭记账机制后，部署验收必须失败。

---

## 同步项（不计入结论）

| # | 位置 | 内容 | 建议 |
|---|---|---|---|
| S1 | 01 L218 | 只探测结果映射中"confirmed_not_happened 而持有者未静默 → retire_requested"没有"（且锁存为假）"限定，而 L161 有。锁存为真且持有者未静默时，两个分句同时匹配 | 照 L161 补上"（且锁存为假）" |
| S2 | 01 L210（S2 draining） | "hello 扫描与 尚未放行的暂缓项与 release_probe_dispatch"：修订时删掉了"产生的 execute"，留下一个多余空格，句子不通 | 改为"hello 扫描与尚未放行的暂缓项产生的 execute 与 release_probe_dispatch" |
| S3 | 01 L195（K4③） | 句尾"放行复核时保持暂缓而不作废（K5）"现在接在"已放行的 intent……照常重送"之后，读起来像在说已放行的 intent | 移回"写 intent 后暂缓"之后 |
| S4 | 01 L175（C-10a 防御分支） | "记录冲突并告警"没有像 C-11a 那样"计入 R13" | 补"计入 R13"，使两条锁存冲突出口的告警口径一致 |

---

## 总体判断

**HLD v2.13 可以定稿。**
- 本轮只剩一条 MINOR（H213-01：例外撤销依赖部署是否升级策略）和两条 NIT，都是 D23 落地的精度问题，可以作为勘误或在附录 B 第 7 组的 01 扩展中落实，不影响主体。

**01 v0.23 可以作为核心契约的开发基线。**
- 锁存已约束全部自动负向结案，自动路径上没有反例。
- C23-01 至 C23-03 都在锁存为真或 holder 静默之后的人工收尾路径上，影响的是运维与开发者能看到什么、能引用什么证据。建议在第一批扩展（12-11）之前以一次 dev13 修订合并处理。
- 这些模型没有被 Demo 契约子集实现（Demo 不实现人工裁决），不阻塞开发起步。

**09 v0.3 可以作为排期基线，前提是在 M0a（11-20）的逐条映射表中处理 P093-01。**
- 后端能力声明的 schema 与规则①的 BenchReport 谓词应移到第二批。否则 2-26 的 M1.5 与 HLD v2.13 的"gate 所用条目须已三方通过"冲突。
- P093-02 需要在 W1 内网预检中补一项 exec 记账，否则问题会拖到 Demo 部署时才暴露。
