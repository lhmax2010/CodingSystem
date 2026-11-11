# HLD v2.12 / 01 v0.22 / 09 v0.2 第二十二轮定向核对 — Claude Code

评审基线：HEAD = `2745e28`（`git pull --rebase origin main` 后无更新）。日期 2026-11-11。

范围：
- HLD 只核附录 A29 所列改动：
  - D23 例外清单；
  - §11.2 的片段判据、pyc、子进程观测与受控执行视图；
  - §11.3 v2.12 用例、§14 R15 措辞、附录 B 第 7 组 v2.12 追加项。
- 01 只核 A3 v0.22 一条所列改动。
- 09 只核 brief 列出的各节。

方法：
- 三份处置表逐行对照三家第二十一轮原始意见，只用来核对来源、采用方案与计数。
- 正文按句级 diff（v2.11→v2.12、v0.21→v0.22）定位改动，逐条核对落实。
- 两处可机械验证的结论用小脚本确认，均在 `systemd-run --user --scope -p CPUQuota=100% -p MemoryMax=2G` 下以 `nice -n 19 ionice -c3` 串行运行：
  - Python 3.12 tokenizer 与 AST 对隐式拼接字符串的处理（H212-01）；
  - PEP 552 checked hash-based pyc 的头部是否约束字节码（H212-02）。
- 未访问 Quickbuild，未启动构建、全量测试或索引。

## 结论

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| HLD v2.12（A29） | **GO** | 0 | 0 | 3 | 1 |
| 01 v0.22（A3 v0.22 条） | **NO-GO** | 0 | 1 | 3 | 1 |
| 09 v0.2（指定各节） | **GO** | 0 | 0 | 5 | 1 |
| 同步项（不计入结论） | — | — | — | — | 2 条 |

- **01 的 MAJOR**：观测锁存只约束人工裁决，不约束只探测通道的自动负向映射。
  - 对账报告"目标 1 已出现、目标 2 未出现"之后，任务进入只探测。
  - 下一轮自动探测若读到两个目标都未出现（复制延迟、分支被他人改写、探测实现缺陷），C-11a 在持有者静默时自动作 release_failed 映射。
  - 结果是部分已发布的授权被判为未发布。这正是本版 A3 宣称已排除的情形。
- **HLD**：四条都不影响 D23 的主干。其中一条修正本方上一轮自己的提案：按内嵌源哈希免除 pyc 并不约束字节码，已用脚本复现。

## 负责人七项裁决（独立判断）

| # | 裁决 | 判断 | 理由 |
|---|---|---|---|
| ① | UT 与静态审查并行，超时必须出报告、不得当通过 | **成立** | 两支在同一 series 上汇合，超时作为 incomplete 条目显式留存，审批与核销都复核放行谓词。09 v0.2 §4.3 把"超时、重试、未完成项全部显式呈现"列为 Demo 原版验收项，执行面没有放松。代价是并行两支的证据留存与等待较慢的一支 |
| ② | Quickbuild 默认取最新 Profile 快照，在 Run 启动时固定 | **成立** | 固定在 Run 启动时，避免同一 Run 内"最新"漂移，并以读回核对实际输入。代价是可能与构建根版本拉开距离，HLD 已要求首屏显示。09 把 Quickbuild 证据等级验收放在 4 月，并设 4-30 检查点，前提不足时不启用而不是默认放行 |
| ③ | Profile 严格匹配，加小改动复用预案 | **成立** | 缺省严格匹配；复用要等非劣评估，09 排在 2027-07，顺序正确（先有真实数据再放宽）。代价是早期重采成本 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | **成立** | "相关"包括反向依赖与 always_run，范围只增不减。代价是维护模块登记表；09 §8 已列业务部门 2-28 提供。另见 P092-02：Demo 第 1 步就用到 focus_modules，但它没有排进扩展批次 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | **成立** | 把 AI 的建议与客观验证分开；09 原则 2 与 §4.3 要求有 AI / 无 AI 两条路径都给出结果，修复以重新构建为准。代价是额外的构建与存储 |
| ⑥ | Quickbuild 可指定 Base CL，否则默认最新，并读回核对 | **成立** | 请求值与实际输入经读回比对，不一致走 base_mismatch 出口。R15 v2.12 已澄清为"校验器拒绝、人显式改配并以新 Run 执行"，不会在运行期自动换后端 |
| ⑦ | 超时后重试成功可以发布，但须审批人逐条确认 | **成立** | acknowledged_gaps 按（条目 id、内容 digest）绑定，核销前复核，变化即 gaps_changed。09 §4.1 第 5 步把逐条确认放进 Demo 审批画面。代价是审批负担 |

"整个产品不得引入 PHP"是负责人前提。本报告只核对其落地，不评价这一选择。

---

## A. 三份处置表核对

### A1. 计数与来源

| 处置表 | 声称 | 核对 | 结果 |
|---|---|---|---|
| HLD_v2.11 | 4 条 → 3 个问题，1 处合并 | Codex H211-01（MINOR）、Kimi H211-01（MINOR）、CC H211-01（MINOR）与 H211-02（NIT）共 4 条；R1 合并 Codex 与 Kimi | **正确** |
| 01_v0.21 | 7 条 → 5 个问题，2 处合并 | Codex C21-01 至 C21-04 共 4 条，CC C21-01 至 C21-03 共 3 条，Kimi 0 条；X1、X2 合并 | **正确** |
| 09_v0.1 | 14 条 → 10 个问题，6 处合并 | Kimi P09-01 至 P09-03 共 3 条，CC P09-01 至 P09-06 共 6 条，Codex P01-01 至 P01-05 共 5 条；Y1 至 Y6 为合并项；14 条全部有落点 | **正确** |

裁决输入各家的级别计数与三份原始报告的结论表一致。

### A2. "采用谁的方案"

| 项 | 处置表写法 | 原文核对 | 结果 |
|---|---|---|---|
| R1 | 拦截取 Codex，记账取 Kimi，构建边界划分取 Codex | Codex H211-01 的 diff 是"受控执行视图或覆盖子孙进程的执行准入，执行前拒绝"，并写明"不将隔离边界内的业务构建输入归为产品工具"；Kimi H211-01 的 diff 是"launcher 子进程记账，deploy 验收时与声明清单比对" | 忠实 |
| R2 | 取 CC | 本方 H211-01 候选改动：tokenizer 定位加签名表完全相等；负向夹具运行时生成；hash-based pyc | 忠实。本方案中 pyc 一项自身有缺口，见 H212-02 |
| R3 | 取 CC | 本方 H211-02：现行版本比对，重新验收时重做观测 | 忠实 |
| X1 | 逐目标字段取 CC，锁存取 Codex | 本方 C21-01 提出 TargetObservation 与一致性校验；Codex C21-01 提出"远端正向事实锁存" | 忠实 |
| X2 | 三种结果取 Codex，暂停标志与范围取 CC | Codex C21-02 的 diff 原文就是"可放行、仍须暂缓、已失去派发资格"；本方 C21-02 提出 execute 放行检查加入 dispatch_paused 并扩到重派 | 忠实 |
| X3、X5 | 取 Codex | Codex C21-03、C21-04 | 忠实 |
| X4 | 取 CC | 本方 C21-03 | 忠实 |
| Y1–Y10 | 见表 | 逐项对照 Kimi、Codex 与本方原文，子点拆分与表头说明一致 | 忠实 |

### A3. 01 处置表的记录更正

更正说上一轮处置表把"三家支持分层"写成了"三家都确认 K2 当时已对任意策略有界"。核对三家第二十轮原文：

- 本方第 27 行原文："K2 在任意归因策略下……都给出了每个任务的终止上界，**只漏了计划性回收一处（C20-02）**"；
- Codex 第 9 行原文："成立，但本版尚未完整满足调整的前提。K2 尚漏掉自动计划性回收循环"；
- Kimi 判为成立，未提例外。

更正后的文字"Kimi 认为当时已经成立；Codex 与 Claude Code 指出自动计划性回收仍有例外"**准确**。

### A4. 正文落实

| 项 | 正文位置 | 结果 |
|---|---|---|
| R1 | HLD L877："声明是产品工具闭包的完整承诺……受控执行视图……执行准入……`deployment_dependency_violation`……launcher 同时对子孙进程的 exec 记账"；业务构建划分句；L880 v2.12 用例 | 已落实。覆盖范围见 H212-03 |
| R2 | L877"判据可机械执行（v2.12）"、负向夹具拼接、hash-based pyc 免除；L880 用例 | 已落实。判据粒度见 H212-01，pyc 免除依据见 H212-02 |
| R3 | L124"门禁比对三处……现行版本删除该条目即撤销"、固定列序清单；L877 重新验收时重做观测 | 已落实。生效点见 H212-04 |
| R15 同步 | L924 | 已落实，与 §13 P6 一致 |
| B-7 v2.12 追加 | L986 | 已落实 |
| X1 | 01 L629–634 TargetObservation 与两类报告的 targets；L316 observed_any_appeared；L651 约束扩到两类报告与全部裁决分支；CF-AUTH-17d、20j | 人工裁决侧已落实。自动映射侧未覆盖，见 C22-01；RunSummary 没有逐目标字段，见 C22-03 |
| X2 | L195 K4③；L196 K5 三种结果与 execute 复核含 dispatch_paused；CF-AUTH-20i、20o | 已落实。"intent 续送"的含义见 C22-04 |
| X3 | CF-AUTH-20n 删除旧断言；CrossTaskBreaker 注释（L336） | 已落实 |
| X4 | L352 strategy_managed；L219 hello 扫描过滤；L351 isolating 注释；CF-AUTH-20k | 已落实。字段生命周期见 C22-05 |
| Y1–Y10 | 09 §2 原则 5–7、§3 M0a/M0b、§3.1、§4.2、§4.3、§4.6、§5.2–§5.3、§8、§9、§10 | 均有落点。残余问题见 P092-01 至 P092-06 |

---

## B. HLD v2.12

### B1. 判据能否机械执行，会不会放过真实 PHP

"tokenizer 定位加与签名表完全相等"把人工判断变成了谓词，方向正确。但谓词作用在 token 上，而 Python 中"单个字符串常量"是 AST 层的概念，两者不一致，见 H212-01。

对"会不会放过真实 PHP"的判断：
- 运行时拼接（包括负向夹具本身）任何文本扫描都看不到；
- 这一残余由宿主侧执行准入兜底：产品闭包中没有 php 解释器，执行视图拒绝未声明的可执行文件；
- 因此不构成 MAJOR。

### B2. hash-based pyc 免除规则

规则可执行，但免除依据选错了对象：内嵌源哈希只把 pyc 头部与源文件绑定，字节码本身不受约束。见 H212-02。

### B3. 受控执行视图与业务构建的划分

- 业务构建划分清楚："构建隔离边界内按业务 spec 执行的构建步骤"不归为产品工具，产品自己的运维与适配程序不得以"业务内容"标注规避。
- 拦截对象只写了"经 launcher 拉起的产品宿主侧工具"。按 HLD §5.1.2，worker 由编排进程直接 spawn；编排、worker、Approval、Build Gateway、MCP 服务调用的工具都不经 launcher。上一轮反例中的"某工具的错误分支调用预装 php"在这些路径上仍然成立。见 H212-03。

### B4. 例外"三处比对、现行版本删除即撤销"

规则本身没有歧义：比对三处，现行版本删除即撤销。缺两点：
- "现行版本"从哪里取；
- 撤销或到期在已验收的部署上何时生效（Run 创建只比对 digest，不复核例外）。

见 H212-04。

### HLD 问题

#### H212-01 [MINOR] 片段判据按 token 比对，隐式拼接的字符串与 f-string 能把完整 PHP 程序拆成"都等于签名"的片段；注释的比较口径未定义

**位置**：HLD §11.2"粒度（v2.11）"中 v2.12 判据（L877）。

**原文依据**："命中处经该语言 tokenizer 确认位于字符串常量或注释内，且该常量 / 注释与随策略版本发布的**签名表**中某一项完全相等"；"源码中不得出现以单个字符串常量承载的完整 PHP 程序"。

**问题与反例**（Python 3.12.3 实测）：

```python
A = "<?php" "\nsystem($_GET[1]);"
B = f"<?php{payload}"
# <?php
```

- tokenizer 对 `A` 产出两个 STRING token：`"<?php"` 与 `"\nsystem($_GET[1]);"`。前者的值与签名完全相等，后者不含信号，按判据通过。但 AST 中 `A` 是**一个**常量 `'<?php\nsystem($_GET[1]);'`，也就是正文明令禁止的"以单个字符串常量承载的完整 PHP 程序"。判据层与禁止句层的粒度不一致。
- `B` 在 3.12 中被拆成 FSTRING_START / FSTRING_MIDDLE(`<?php`) / FSTRING_END，"字符串常量"是否包括 FSTRING_MIDDLE 未定义。
- 注释 token 的文本是 `# <?php`，按字面不等于签名 `<?php`。按字面比较，注释里提到签名必然误报；若去掉 `#` 与空白，又需要写明规范化规则。
- "完全相等"比较的是 token 原文（带引号和前缀 `r`、`b`）还是求值后的值，也没有写。

后果：判据仍要靠实现者补口径，同一文件在不同实现下结论不同。实际执行仍由宿主执行准入兜底，所以定为 MINOR。

**候选改动**：

```diff
--- HLD §11.2 粒度（v2.12 判据）
- 命中处经该语言 tokenizer 确认位于字符串常量或注释内，且该常量 / 注释与……签名表中某一项完全相等
+ 命中处须同时满足：
+ (a) 位于字符串字面量或注释内。字符串按 AST 常量判定：相邻字面量的隐式拼接视为一个常量，
+     以求值后的值比较；f-string（JoinedStr）中的任何命中一律不免除；
+ (b) 该常量的值、或注释去掉注释符与首尾空白后的文本，与签名表中某一项完全相等。
+ 签名表随策略版本发布，同时给出各语言的注释符与规范化规则。不满足即按文本信号判定。
```

**副作用**：扫描器要同时用 AST 与 tokenizer（注释只在 tokenizer 中可见），实现略增。现有"扫描器规则表里写 `"<?php"`"的用法不受影响。

**配套测试**：在 §11.3 v2.12 追加三例（均在测试运行时生成源码，不入仓库）：
- `"<?php" " echo 1;"` 隐式拼接 → 失败；
- `f"<?php{x}"` → 失败；
- 注释 `# <?php` → 通过，注释 `# <?php echo 1;` → 失败。

#### H212-02 [MINOR] 按"内嵌源哈希"免除 pyc 不约束字节码：头部正确、代码被替换的 pyc 会被免扫，并且 Python 照常加载（本方上一轮提案的缺口）

**位置**：HLD §11.2"适用范围"v2.12 句（L877）；§11.3 v2.12 用例"hash-based pyc 内嵌源哈希匹配 → 通过"（L880）。

**原文依据**："扫描器以预编译的 hash-based pyc（PEP 552，checked 模式，内嵌源文件哈希）随包发布，pyc 按'内嵌源哈希属于已发布 digest 表中的源文件'免除"。

**问题与复现**：
- PEP 552 的 pyc 头部是 16 字节：magic、flags、源文件的 SipHash（64 位，密钥公开）。哈希只覆盖源文件，不覆盖其后 marshal 的 code object。
- checked 模式下，导入时 Python 只校验源哈希与 `.py` 一致，校验通过就直接执行 pyc 里的字节码。
- 本方用 Python 3.12.3 复现：先编译 `SIG = "<?php"` 的 checked pyc（flags = 3），保留其 16 字节头部，把 code object 换成 `print("tampered: <?php system(1);")`。`import scan` 输出 `tampered: <?php system(1);`。
- 按现行免除规则，这个 pyc 的内嵌源哈希属于已发布表，**免扫**。
- 部署后的篡改会被 DeploymentInventory 的 current/approved 比对发现。但在验收扫描当时，内容错误的 pyc 会被免扫后写入 approved_digest，此后的 digest 比对只能证明"没变"，不能证明"没问题"。

这是本方上一轮 R2 提案自身的缺陷，特此更正。

**候选改动**：

```diff
--- HLD §11.2 适用范围
- pyc 按"内嵌源哈希属于已发布 digest 表中的源文件"免除，运行时不另行生成 pyc
+ pyc 与源文件一样按**自身文件 digest** 免除：hash-based pyc 不含时间戳、可复现，随策略版本发布
+ "源文件 digest + 各支持解释器版本的 pyc digest"表；不在表中的 pyc 照常按文本信号判定。
+ 运行时不生成 pyc：安装前缀对运行用户只读，且以 PYTHONDONTWRITEBYTECODE=1（或 -B）运行。
--- §11.3 v2.12
- 安装前缀中扫描器的 hash-based pyc 内嵌源哈希匹配 → 通过、不匹配或存在运行时生成的 pyc → 失败
+ pyc 文件 digest 在表中 → 通过；头部源哈希正确而字节码被替换 → 失败；存在运行时生成的 pyc → 失败
```

**副作用**：发布时要为每个支持的解释器版本生成并登记 pyc digest；解释器升级须随策略版本更新表。免除范围缩小，没有扩大。

**配套测试**：在测试运行时生成"头部正确、code object 被替换"的 pyc（只拼字节，不引入 PHP 运行时）→ 主机扫描失败；以 Python 次版本不同的解释器运行且前缀只读 → 不生成新 pyc。

#### H212-03 [MINOR] 执行准入只覆盖"经 launcher 拉起"的工具，编排、worker 与各服务直接 spawn 的工具不受约束

**位置**：HLD §11.2"扫描对象"v2.12 句（L877）；§5.1.2"每个 task 由编排进程 spawn 独立子进程 worker"（L548）。

**原文依据**：
- "**经 launcher 拉起的**产品宿主侧工具在**受控执行视图**内运行……或在覆盖子孙进程的执行准入下运行——视图外 / 未声明的可执行文件在执行前被拒绝"；
- "无法提供上述约束的工具环境不得以'一次观测无命中'通过验收"。

**问题与反例**：
- launcher 只拉起 ClineSR CLI、构建边界与 broker 实例（L602、L986）。
- 业务 worker 由编排 spawn；Compiler、Optimization 等 worker 会调用 git、readelf、llvm-profgen、perf 等宿主工具。编排、Approval、Build Gateway、MCP 服务进程也不经 launcher。
- 上一轮反例换到这些路径上照样成立：某 worker 调用的工具在错误分支 exec 了主机预装的 php，E0 观测没走到这个分支，执行视图不覆盖 worker，门禁全绿而 PHP 已执行。
- 第二句"无法提供上述约束的工具环境"可以理解为"这些进程也必须受约束"，也可以理解为"只说 launcher 拉起的工具"。两种读法的验收结论相反。

**候选改动**：

```diff
--- HLD §11.2
- 经 launcher 拉起的产品宿主侧工具在受控执行视图内运行……
+ 本产品在宿主上的全部进程（编排、worker、Approval、Build Gateway、MCP 服务、broker，
+ 以及 launcher 拉起的 CLI 与构建边界）及其子孙进程，都在执行准入下运行：
+ 只有已批准闭包内的可执行文件与库可被 exec 或以可执行方式映射。
+ 可用 systemd 单元的 ExecPaths= / NoExecPaths= 实现（mount namespace，子孙继承），
+ 或由 launcher 提供的受控执行视图实现。
+ exec 记账覆盖同一范围。构建 VM 内由本产品下发的辅助程序按同一口径约束；
+ VM 内业务构建步骤仍按 D23 排除。
```

**副作用**：编排与 worker 的 systemd 单元须列出完整的可执行路径集合，漏项会在开发期显式失败，开发期成本增加。这本来就是"声明是完整承诺"的直接推论。

**配套测试**：§11.3 v2.12 的哨兵用例从"launcher 拉起的工具"扩到"worker 直接 spawn 的工具"与"编排进程直接 spawn 的工具"两例，断言执行前被拒绝并记 `deployment_dependency_violation`。

#### H212-04 [NIT] "现行版本"的取值来源与撤销、到期的生效点未写

**位置**：HLD D23 例外条款（L124）。

**原文依据**："门禁比对三处（例外清单、批准版本、现行版本）……现行版本删除该条目即撤销，不等到期"。

**问题**：
- 门禁运行在已部署的产品上，"现行 HLD 版本"可以读作仓库 main 上最新的 HLD，也可以读作部署所对应策略版本绑定的 HLD。两种读法下撤销的生效时间不同。
- Run 创建时只比对 DeploymentInventory 的 current/approved digest，不复核例外是否仍有效。一个已带例外验收的部署，在例外撤销或到期后，到下一次重新验收前仍能创建 Run。

**候选改动**：

```diff
--- HLD D23 例外
+ "现行版本"取部署所用策略版本绑定的 HLD 版本，该绑定随签名表一起发布；
+ 每次 Run 创建时，在 digest 比对的同一检查中复核所依赖例外仍在现行清单中且未到期，否则拒绝创建 Run。
```

**副作用**：Run 创建多一次清单查找，开销可忽略。

**配套测试**：已带例外验收的部署，在现行版本删除该条目 → 下一次 Run 创建被拒；例外到期 → 同样被拒。

---

## C. 01 v0.22

### C1. 是否还有路径能把部分已发布的授权判为未发布

| 路径 | v0.22 的处理 | 结论 |
|---|---|---|
| 人工裁决 · manual_only 分支 | 锁存或本次 targets 有 appeared → 拒绝 confirm_not_released（L651） | 已闭合 |
| 人工裁决 · 非 manual_only 的"强制 probe 后 unknown" | 同上，"适用于全部裁决分支" | 已闭合 |
| 对账报告记录了部分出现 | 同事务置锁存 | 已闭合 |
| 只探测报告记录了部分出现 | 同上 | 已闭合 |
| 重启、K3 暂停、holder 更替 | 锁存持久化，不清零 | 已闭合 |
| 报告乱序：先部分出现，后全部未出现 | 锁存不清零；**但 C-11a 对后到的 confirmed_not_happened 作自动 release_failed 映射，不读锁存** | **未闭合，C22-01** |
| 从未记录过任何观测，运维以一条外部记录裁决 | 锁存为假，"至少一条远端证据"即可，证据不必覆盖每个目标 | 残余，C22-02 |
| 被拒的报告（一致性校验失败、旧 epoch）中的 appeared 事实 | 不落账 | 可接受：后续探测会重新观测；R14 复查窗口兜底结案后的迟到发布 |
| 正常执行路径中部分失败后发 release_outcome = release_failed | 不在 X1 范围；ReleaseOutcomeRequest 没有 targets | 列为同步项 S2 |

### C2. targets 校验与"目标集合须等于 manifest"

- probe 与 targets 一致（全部 appeared ⇔ happened，全部 absent ⇔ not_happened）只看载荷，能在处理序 ② 判定。
- "集合等于 manifest"要读授权记录，只能在 ③ 或 ⑤ 判定。两处都写成"E-CP-VALIDATION，不落账"，但 ② 不落 receipt、⑤ 的错误会作为首响应落 receipt，两者的重试语义不同。
- `target_ref` 的"规范标识"没有定义：ReleaseTarget 只有 `adapter / repo / branch / action`，没有 id。
- RunSummary 没有逐目标字段。

以上见 C22-03。

单目标发布：targets 恰一项，三值与单项状态一一对应，语义不变，只多一个必填字段。**不受影响**。

### C3. K5 三种结果与 K4③

- **完备性**：execute 与 probe 两型的每个复核条件都落入三类之一。
- **互斥性**：没有写判定顺序。例如"execute 遇 manual_only"与"dispatch_paused"可能同时为真；若先判 ②，该项会被保留而不是作废。实际上转 manual_only 的事务会同时作废暂缓的 execute（K5"作废"段），所以不会出错，但规则本身应写明 ③ 先于 ②。
- **暂停的清除与唤醒**：人工恢复或正常结案同事务清除并写持久化唤醒，闭合。全部在途任务都未核销时没有正常结案的来源，只能人工恢复。这是可见的暂停状态，不是饿死。
- **"intent 续送"**：其含义有一种读法会让暂停制造期限超时，见 C22-04。

### C4. strategy_managed

契约正文中由策略独占管理的判断已全部改用 `strategy_managed`：hello 扫描用它过滤，定时器武装与 K5 独占许可使用通用措辞。`isolating` 只出现在枚举注释与 S2 中。剩余问题是字段的置位与清除没有规则，见 C22-05。

### 01 问题

#### C22-01 [MAJOR] 观测锁存只约束人工裁决，C-11a 的自动负向映射仍可把部分已发布的授权关为 release_failed

**位置**：
- 01 C-11a 行（L161）："confirmed_not_happened ∧ granted_epoch 持有者实例静默 → release_failed 映射"；
- §2.2d"indeterminate 锁存"段的同一规则（L218）；
- AuthorizationRecord.observed_any_appeared 注释（L316）。

**原文依据**：
- L316："不是执行许可，**只约束人工裁决**（§5.1）"；
- A3 v0.22："部分已发布的授权不得判为未发布"；
- L651："部分已发布的授权只能经 `keep_unknown` 或 `confirm_released` 收尾"。

**反例**：
1. 双目标授权。broker（epoch 2）推送目标 1 成功后崩溃。新实例 hello → 恢复臂对账，`targets = [appeared, absent]`，`probe = indeterminate` → recovery_state := indeterminate，`observed_any_appeared := true`。
2. 任务未耗尽，留在非 manual_only 的只探测通道。周期任务按 probe_interval 发只探测。
3. 下一次探测读到两个目标都是 absent。可能的原因：探测读的是滞后的副本；目标 1 所在分支被他人强推；变更被人工删除；探测实现缺陷。broker 合法上报 `confirmed_not_happened`，与 targets 一致，通过校验并落账。
4. C-11a：持有者（epoch 2）已静默 → **自动 release_failed 映射**，Run 以"未发布"结案。人工裁决路径上的锁存检查完全没有被调用。
5. 开发者看到发布失败后重新提交，目标 1 被再次发布。

本版设锁存的理由正是"之后的 unknown / absent 报告……不清零"（X1 理由一栏："Codex 的锁存保证这一事实不会被后来的报告冲掉"），但这个事实只在人工出口生效，自动出口照样被冲掉。另外，C-11 写明 `confirm_not_released ≡ release_failed 映射`，自动映射与人工判"未发布"终局相同。

**候选改动**：

```diff
--- 01 C-11a 行与 §2.2d indeterminate 锁存段
- confirmed_not_happened ∧ granted_epoch 持有者实例静默 → release_failed 映射
+ confirmed_not_happened ∧ granted_epoch 持有者实例静默 ∧ 授权 observed_any_appeared = false → release_failed 映射；
+ observed_any_appeared = true 时记录该报告、告警"远端观测矛盾"并计入 R13，同事务置 recovery_mode = manual_only
+ （不改 recovery_state），只经 C-11 收尾——裁决受 §5.1 已记录观测约束
--- L316 注释
- 不是执行许可，只约束人工裁决（§5.1）
+ 不是执行许可；约束人工裁决（§5.1）与一切负向终局映射（C-10a not_happened、C-11a）
--- C-10a / ReconcileRecorded(not_happened_mapped) 与 ReconcileProceed
+ 防御性同条件：observed_any_appeared = true 时不作负向映射、不授予执行许可，转 indeterminate
```

**副作用**：
- 观测矛盾时，原来可自动结案的任务改为人工裁决，manual_only 数量可能略增，并会告警。
- 单目标授权不变：单目标的锁存为真，说明曾有报告 `confirmed_happened`，按现有规则已经映射为 released，走不到这里。
- 只增加守卫，不改计数。

**配套测试**（扩展 CF-AUTH-17d、20j）：
- 对账报告 `[appeared, absent]` 后，只探测报告 `[absent, absent]`，持有者已静默 → 不映射 release_failed，转 manual_only 并告警；随后 confirm_not_released 被拒，keep_unknown 与 confirm_released 允许。
- 同一序列，在报告事务前后 kill 编排 → 结局唯一。
- 锁存为假的 `[absent, absent]` → 照常 release_failed（回归）。

#### C22-02 [MINOR] 从未记录观测时，confirm_not_released 的证据不必逐目标覆盖：一条只涉及部分目标的外部记录就能放行

**位置**：§5.1 特权运维（L651）："unknown 下 `confirm_not_released` 须有至少一条远端证据且原 holder 已静默"；AdjudicationEvidence（L640）。

**问题与反例**：
- broker 推完目标 1 后崩溃，此后各实例在对账前反复崩溃。K3 耗尽 → manual_only。强制探测令实例崩溃 → unknown。锁存为假。
- 运维附一条外部记录，只查了目标 2，确认未出现。holder 已静默 → confirm_not_released 通过。目标 1 实际已发布，重新提交后会被再次发布。
- 契约无法验证外部记录的内容，但可以要求运维**逐目标声明并给出证据**，把"证据不完整"变成可机械拒绝的结构错误。

**候选改动**：

```diff
--- 01 §5.1
- class AdjudicationEvidence(BaseModel): kind: ...; ref: ArtifactRef
+ class AdjudicationEvidence(BaseModel): kind: ...; ref: ArtifactRef; target_refs: tuple[str, ...]   # 该证据所涉的目标
--- guard
+ confirm_not_released ⇒ 证据的 target_refs 并集恰等于授权 manifest 的目标集合；
+ probe_report 型证据的 target_refs 由编排从被引报告的 targets 中取 absent 项生成，不由运维填写
```

**副作用**：多目标裁决时运维要多填字段；单目标不变。

**配套测试**：双目标、锁存为假、只有一条覆盖目标 2 的外部记录 → confirm_not_released 被拒；补齐目标 1 的证据 → 通过。

#### C22-03 [MINOR] target_ref 的规范标识、集合校验所在的处理步骤与 RunSummary 的逐目标字段未定义

**位置**：TargetObservation（L629）；两类报告的校验注释（L630、L634）；处理序（L654）；RunSummary（L287）；ReleaseTarget（L294）。

**原文依据**：
- "target_ref 取本授权 ReleaseManifest 中目标的规范标识"；
- "不一致或目标集合不符 → E-CP-VALIDATION，不落账"；
- 处理序 ②："schema 校验——失败 → ResponseError(E-CP-VALIDATION)，**不落 receipt**（修正载荷后以同 request_id 重试正常受理）"；
- L651："后者在 RunSummary 中逐目标列出最后观测到的状态"。

**问题**：
1. ReleaseTarget 只有 `adapter / repo / branch / action`，没有标识字段，"规范标识"无从取值。同一 repo 与 branch 上两种 action 是否算两个目标，也不确定。targets 是 tuple，重复项是否违反"集合恰等于"未写。
2. 集合比对要读授权记录，不属于 ② 的 schema 校验。若在 ⑤ 判定，错误会落 receipt，broker 用同一 request_id 修正重试会拿到旧的拒绝，与 ② 的重试语义相反。
3. RunSummary 模型没有逐目标字段，L651 的"逐目标列出"没有载体。
4. ReleaseProbeDispatch 的 `probe_targets` 是否必须等于 manifest 的目标集合未写。若允许子集，按规则报告必然因"集合不符"被拒。

**候选改动**：

```diff
--- §2.5 ReleaseTarget
+ target_ref := "sha256:" + hex(sha256(canonical_json(ReleaseTarget)))；manifest.targets 内 target_ref 不得重复（加载期与审批 CAS 校验）
--- 两类报告注释
- 不一致或目标集合不符 → E-CP-VALIDATION，不落账
+ probe 与 targets 不一致、或 targets 内重复 → 处理序 ② E-CP-VALIDATION（不落 receipt）；
+ 目标集合与授权 manifest 不符 → 处理序 ⑤ E-CP-VALIDATION，作为首响应落 receipt，不落观测、不改锁存
--- ReleaseProbeDispatch
+ probe_targets 恒等于授权 manifest.targets（编排填写）
--- RunSummary
+ release_targets: tuple[TargetObservation, ...] | None = None   # 发布类 Run 结案时各目标最后一次观测；无观测为 unknown
```

**副作用**：manifest 规范化多一个派生字段，ReleaseManifest digest 的计算不变（target_ref 是派生值，不入 digest）。

**配套测试**：
- 同一 repo 与 branch 上两种 action → 两个 target_ref；
- 重复 target_ref 的报告 → ② 拒绝，以同 request_id 修正后受理；
- 集合不符 → ⑤ 拒绝并落 receipt；
- 部分发布以 confirm_released 结案 → RunSummary.release_targets 逐项与最后一次观测一致。

#### C22-04 [MINOR] K4③ 暂停范围中的"intent 续送"可以读成包括恢复规则 (a) 对已放行 intent 的重送：已放行的派发若被暂停，期限照走，会制造 phase_deadline；三种结果的判定顺序未写

**位置**：§2.2d K4③（L195）；K5"放行复核的三种结果"（L196）；§2.5 恢复规则 (a)（L361）。

**原文依据**：
- K4③："**暂停授权实际未核销的全部 execute 派发**（新派发、hello 后的持有者更替重派与 intent 续送，R21）——写 intent 后暂缓"；
- 规则 (a)："intent 无 completed ∧ held_for_isolation = false ∧ target_epoch == 当前 epoch → 以同 request_id 重送"；
- K5："同一已放行 intent 重送不刷新期限"。

**问题与反例**：
1. 未核销 task T 的 execute intent 已放行：建立了执行绑定，awaiting_consume 的期限在走，ACK 丢失。此时 K4③ 置 dispatch_paused。
2. 编排重启，规则 (a) 要以同 request_id 重送 T。
3. 若"intent 续送"包括这种重送，T 不能变回暂缓（K5 只定义"写 intent 后暂缓"，没有已放行 intent 退回暂缓的迁移），于是只能不发。broker 若根本没收到，期限到期 → phase_deadline 事件 → 当前实例退役，loss 计数 +1，并累加 deadline_task_ids。
4. 暂停本来是为了避免继续耗尽 task，这里却给一个只是被暂停的 task 记了故障，严重时会触发 K3 以 dispatch_loss_exhausted 关闭。
5. 若"续送"不包括这种重送，现行文字应写明。S2 draining（L210）的"intent 续送产生的 execute"有同样的歧义。

判定顺序方面：K5 没写三种结果按什么顺序判定。目前靠转 manual_only 的事务顺带作废来保证结果正确，规则本身应当自足。

**候选改动**：

```diff
--- K4③
- 暂停授权实际未核销的全部 execute 派发（新派发、hello 后的持有者更替重派与 intent 续送，R21）
+ 暂停授权实际未核销、且尚未放行的全部 execute 派发（新派发、hello 后的持有者更替重派，以及已暂缓项的放行，R21）；
+ 已放行（held = false、已建立执行绑定）的 intent 按 §2.5 (a) 以同 request_id 照常重送，不受暂停影响——
+ 它不是新的执行开始，期限已在走
--- S2 draining 同步澄清"intent 续送"
--- K5 三种结果
+ 判定顺序：先判 ③ 已失去派发资格，再判 ② 仍须暂缓，都不满足才是 ① 可放行
```

**副作用**：暂停期间仍有少量已放行派发的重送。这些派发在暂停前就已开始，属于暂停前的工作，不扩大暂停要拦的面。

**配套测试**（扩展 CF-AUTH-20i、20o）：
- 已放行未 ACK 的未核销 execute，暂停后编排重启 → 以同 request_id 重送，期限不刷新，不产生仅由暂停导致的 phase_deadline；
- 同时满足 manual_only 与 dispatch_paused 的暂缓 execute → 结果为 ③。

#### C22-05 [NIT] strategy_managed 的置位与清除没有规则；hello 扫描括注与过滤条件自相矛盾

**位置**：ReleaseTaskState.strategy_managed（L352）；持有者更替重派（L219）。

**原文依据**：
- "由归因策略的独占预约管理、只经其放行入口派发（参考策略 v1 中 isolating 成员为 true）"；
- L219：扫描条件为"`recovery_mode ≠ manual_only` 且 `strategy_managed = false`"，括注却写"manual_only 者只发只探测且 `auto_probe_suspended = false`"。

**问题**：
- 契约没写谁在什么事务中置位与清除 strategy_managed，也没写与 K3 manual_only 的关系。若某替换策略在 task 转 manual_only 后不清除该字段，按 K5 活性要求，它的强制探测是否仍须经策略的放行入口，不明确。
- 契约也没有不变式"recovery_mode = isolating ⇒ strategy_managed = true"。
- L219 的过滤条件已经排除 manual_only，括注又说扫描会给 manual_only 发只探测，两者矛盾。此句先于本版就存在，本版改的是同一句。

**候选改动**：

```diff
--- L352
+ 由归因策略在其纳入事务中置 true；task 终结或置 manual_only 的同一事务置 false（之后只探测与强制探测都走契约通道）；
+ 不变式：recovery_mode = isolating ⇒ strategy_managed = true
--- L219
- 扫描全部非终态、`recovery_mode ≠ manual_only` 且 `strategy_managed = false` 的 release task……（……manual_only 者只发只探测且 `auto_probe_suspended = false`……）
+ 扫描全部非终态、`strategy_managed = false` 的 release task……：manual_only 者只在 `auto_probe_suspended = false` 时发只探测，其余按授权状态分流
```

**副作用**：无语义扩张，只把现有意图写成规则。

**配套测试**：CF-AUTH-20k 追加两例：strategy_managed 的 task 转 manual_only → 字段清零、hello 后按契约通道发只探测；isolating 而 strategy_managed = false → 加载或一致性检查失败。

---

## D. 09 v0.2

### D1. M0a / M0b 与 P0，三批的覆盖与日期

- M0a 明确"不宣称 P0 完成"，正确。M0b 宣称"P0 完成"，但 HLD §13 P0 要求"01 按 v2.x 范围扩展并经三方评审 draft freeze"，即全部扩展；09 只要求第一批。见 P092-01。
- 三批覆盖了 B-7 的九个子组标题，但"报告与消息"与"执行环境"两组中有若干条没有分到任何一批，其中几条 Demo 和 P3、P4 都会用到。见 P092-02。
- 日期与所服务的阶段：
  - 第一批 12-11 早于 P1/P2 的 1 月底 gate，Demo 代码在此之前按 provisional 开发，符合原则 6；
  - 第二批 1-22 早于 2 月 P3 余项与 P4；
  - 第三批 3-19 与 3-31 早于 4 月的 P6 与 Benchmark。
  
  均匹配。第二批中"§11.3 v2.0 追加类别落 CF 族"到 P1/P2 gate 只有 9 天，偏紧，可接受。

### D2. Demo 契约子集与失败即停

子集与 fail-closed 的方向清楚。但 Demo 实际会走到的几条路径落在两类之间，没有归属。最典型的是"broker 失联告警"：失联靠什么检测，在子集里没有说明。见 P092-03。

### D3. 降级表是否放宽安全约束

各行本身都没有放宽。但"回放留存的真实分析记录"这条降级路径，对记录在什么约束下产生、如何出内网都没有要求；而它恰好是内网权限不到位时的备选路径。另外 §4.2 的安全切片漏列 D23 在 Demo 主机上的部署验收。见 P092-04、P092-05。

### D4. 依赖表与 gate 对照表

依赖表已补齐上一轮各项，没有发现新的、会卡关键路径的外部依赖。gate 对照表只有三个例子，没有表本身，也没有完成日期。见 P092-06。

### 09 问题

#### P092-01 [MINOR] M0b 宣称"P0 完成"，而 HLD §13 P0 要求 01 的 v2.x 扩展全部 draft freeze；09 只要求第一批

**位置**：09 §3 M0b 行；§3.1；HLD §13 P0 行（L893）。

**原文依据**：
- HLD："P0 | ……01 按 v2.x 范围扩展并经三方评审 draft freeze；08/09 就绪 | 总部方案确认 + 三方 unanimous GO"；
- 09 M0b："**M0b 设计 gate（P0 完成）** | 2026-12-31 | 01 扩展第一批经三方评审通过"；
- 原则 6："对应批次未定稿，相关阶段的 gate 不能宣称完成"。

**问题**：按 HLD 原文，12-31 时第二、三批尚未通过，P0 不能完成；按 09，P0 在 12-31 完成。两份文档对同一个 gate 结论相反，验收时必然有一方被违反。分批本身合理，因为第三批要等真实消费者；但需要 HLD 同步，或者 09 不宣称完整的 P0。

**候选改动**（二选一，推荐 a）：

```diff
--- (a) 09 §3 M0b，同时登记同步项 S1 修订 HLD §13 P0
- **M0b 设计 gate（P0 完成）**
+ **M0b 设计 gate（P0 完成，按 HLD v2.12+ §13 P0 分批口径）**
+ P0 要求第一批 draft freeze；第二批、第三批分别为 P3/P4、P5–P7 gate 的入口条件
--- (b) 09 §3 M0b
- P0 完成
+ P0 的第一批部分完成；P0 整体随第三批（3-31）完成
```

**副作用**：(a) 需要对 HLD 做一处一致性修订，符合 HLD 处置表"后续只随 01 扩展做一致性修订"。(b) 不动 HLD，但 P0 要到 3 月才完成，与"P1–P4 在 M1.5 完成"的叙述不顺。

**配套检查点**：M0b 验收时，以修订后的 HLD §13 P0 原文逐项对照。

#### P092-02 [MINOR] 附录 B 第 7 组中若干条没有分到任何一批，其中几条在 Demo 路径上

**位置**：09 §3.1 批次表；HLD 附录 B 第 7 组（L978–L988）。

**问题**：按 B-7 原文逐条对照三批的内容列，以下各条没有出现在任何一批中：

| B-7 条目 | 谁用到 | 应入 |
|---|---|---|
| 目标范围与 ModuleRegistry schema（含 `always_run`）、`create_run.focus_modules`、`protected_paths` 与验证资产触及检查 | Demo §4.1 第 1 步"指定目标模块"；P4（2 月） | 第一批（focus_modules 部分）；第二批（其余） |
| `get_result` 的 `incomplete` / `retried` 清单与超时记录、`incomplete` 条目 `class`、`ApprovalDecision.acknowledged_gaps`、`succeeded_with_gaps` | Demo §4.1 第 5 步审批画面与 §4.3"超时、重试、未完成项全部显式呈现" | 第一批 |
| LogAnalyzer Diagnosis schema、`ai_draft` 子结构与 AI 证据 / 采纳记录 | Demo 核心场景（Compiler Agent 的 AI 修复）；P3 证据包（1 月） | 第一批 |
| ReleaseManifest `release_evidence`、多版本对比报告 digest 入 `release_evidence` | Demo 审批与发布 | 第一批 |
| ExecutionManifest 的 `build_input_closure_digest`、`module_registry_digest` 等其余字段 | 第二批基线缓存键；P4 | 第二批 |
| DeploymentInventory 契约、launcher 的 cgroup v2 spawn / kill 接口、broker 计划性回收须经 launcher 登记 | W3 的 CLI launcher 与 W5 的 broker | 第一批 |
| `sys.scheduler` | 入口 | 第一批或第三批 |

09 写了"11-20 前完成三批的逐条清单"，这些条目可能在那时补上。但现行批次表的内容列会被当作范围的依据，Demo 用到的条目若默认落入后续批次，按原则 6，Demo 代码就会建立在未定稿的契约上。

**候选改动**：

```diff
--- 09 §3.1
+ 划分规则：Demo 路径（§4.1 六步）用到的条目一律入第一批。11-20 的逐条清单以 B-7 原文逐条编号，
+ 每条恰属一批，附"使用方（阶段 / Demo 步骤）"列；未分配的条目不得留空。
+ 第一批补：focus_modules、incomplete / retried / acknowledged_gaps / succeeded_with_gaps、
+ Diagnosis 与 ai_draft、release_evidence、DeploymentInventory 与 launcher cgroup 接口
```

**副作用**：第一批工作量增加，12-11 更紧。可用的缓解办法：Diagnosis 与 ai_draft 先以 Demo 所需的最小字段定稿，其余标为 provisional。

**配套检查点**：M0a（11-20）检查逐条清单覆盖 B-7 全部条目、无重复、每条有使用方；12-11 检查第一批包含 Demo 路径全部条目。

#### P092-03 [MINOR] Demo 契约子集没有归属 Demo 会走到的几条路径："broker 失联告警"缺少检测机制，编排重启穿过 publishing 时会撞上未实现的 §2.2d

**位置**：09 §4.2"完整实现"与"失败即停"两段；§4.1 第 6 步；§4.3"kill broker 时，Run 保持 publishing 并告警"。

**原文依据**：
- "失败即停：……broker 崩溃后的自动恢复、恢复臂对账、只探测；K1–K6 的计数、暂停与重派"；
- "broker 失联时 Run 保持 publishing 并告警"；
- "演示中途强制结束编排进程后重启……已核销的授权不重复发布"。

**问题**：
1. **失联靠什么检测**：01 中 broker 失联由 BrokerInstanceLease 与心跳、ReleaseTaskState 阶段期限判定，二者都在 §2.2d。子集没说 Demo 实现到哪一层。若实现了租约与期限，到期会产生 RetirementEvent，进而触发 K1–K6（未实现）；若都不实现，则没有"告警"的来源。
2. **编排重启穿过 publishing**：编排停机若超过 broker 租约时长，重启后租约已过期，按 01 走 lapsed，这又是未实现的 §2.2d 路径。演示脚本若恰在 publishing 期间 kill 编排，结局取决于停机时长。
3. **核销前 kill broker**：Run 仍为 running，§4.3 的"保持 publishing"不适用。授权会一直挂到过期，再按 C-09② 关闭。这条路径是否在子集内没有写。
4. **编排在构建中途被 kill**：worker 进程组与构建边界中孤儿的回收（HLD §5.1.2 的 pgid 与 cgroup reap）、本地构建效应的 probe 对账，都是"已执行的构建不重复执行"的前提，子集没有点名。

**候选改动**：

```diff
--- 09 §4.2 完整实现
+ - broker 实例租约与心跳、ReleaseTaskState 阶段期限：只检测、只告警。到期时不生成 RetirementEvent，
+   不退役实例，不计数；Run 保持当前状态（running 或 publishing）；
+ - 编排重启：worker 孤儿进程组与构建边界的回收，本地构建效应的 probe 对账，DispatchReceipt 规则 (a)；
+   编排重启后对 broker 租约给一个宽限期（≥ 停机时长），期间同一实例的 hello 照常绑定；
+ - 授权过期关闭（C-09②），用于核销前 broker 丢失的情形
--- 09 §4.3
+ - 在 publishing 期间 kill 编排并在租约时长以外重启 → 不产生 lapsed 结局，Run 续跑或保持 publishing 并告警；
+ - 核销前 kill broker → Run 保持 running 并告警，授权到期后按 C-09② 关闭
```

**副作用**：Demo 多实现一层"只检测"的租约与期限。正式实现时把"告警"换成 §2.2d 的完整处理即可，不是一次性代码。

**配套检查点**：W6 的 Demo 场景脚本固定 kill 的时点（构建中、审批中、publishing 中各一次），12-22 预演逐个验证结局。

#### P092-04 [MINOR] 降级路径"回放真实分析记录"没有约束记录的来源条件与出内网的数据边界

**位置**：09 §4.5"若做不到"；§4.6 的 11-27 检查点"内网主机权限……→ 触发 §4.5 的备选方案"；12-11 检查点"内网 ClineSR CLI 联调"行。

**原文依据**：
- "回放内网事先跑出并留存的真实分析记录"；
- "回放事先留存、绑定输入 / 工具版本 / 结果摘要的真实分析记录"；
- 原则 5："ClineSR CLI 的 OS 层约束……发往 LLM 的数据边界 fail-closed……不在任何降级范围内"。

**问题**：
- 11-27 触发备选的条件正是"内网主机权限（专用用户、cgroup、出口规则）不就绪"。在这种情况下，"事先跑出"的真实记录只能是在**没有 CLI OS 层约束**的环境里，用真实 CLI 分析真实日志得到的。这相当于在 §4.2 安全切片验收之前首次真实使用了 CLI，与原则 5 冲突。
- 降级表要求的是"绑定输入、工具版本、结果摘要"，没有要求绑定"产生时的约束验收记录"。
- 外网开发机上回放，意味着内网的分析记录（含真实构建日志片段与内网 LLM 输出）要出内网。原则 3 只写了"以文本回传"，没有要求按数据密级检查。

**候选改动**：

```diff
--- 09 §4.6 两处回放行与 §4.5
+ 可回放的记录须在已通过 §4.2 LLM 安全切片验收的环境中产生，记录绑定该验收记录的 id。
+ 没有这类记录时，如实标为 FakeLLM 演示。
+ 记录出内网前按数据边界规则逐条核对密级，不合规的条目不得出内网。
```

**副作用**：内网权限迟迟不到位时，"真实 AI"画面可能只能以 FakeLLM 呈现。这是安全底线不降级的直接代价。

**配套检查点**：11-27 检查点在触发备选时同时登记：可回放记录的来源验收 id；出内网清单的密级核对结论。

#### P092-05 [MINOR] §4.2 安全切片漏列 D23 在 Demo 主机上的部署验收（主机安装集扫描、子进程观测、v2.12 执行准入）

**位置**：09 §4.2"Demo 用到的安全切片在首次使用前验收"；原则 5"不得引入 PHP"。

**原文依据**：安全切片只列"首次真实构建前：构建隔离"与"首次真实 LLM 调用前：ClineSR CLI 的 OS 层约束与数据边界"。

**问题**：
- Demo 要把本产品部署到内网主机。按 HLD §11.2，这需要 deploy 验收与 E0 预检中的主机安装集扫描、子进程观测，以及 v2.12 新增的受控执行视图或执行准入，后者依赖主机能力。W1 预检 ④ 只问到 systemd 与出口规则，没有问 mount namespace 或 ExecPaths 的可用性。
- 原则 5 把"不得引入 PHP"列为不可降级，但没有安排它在 Demo 主机上的首次验收时点。
- §3.1 第一批包含"launcher 受控执行视图"的契约，却没有对应的实现与验收落点。

**候选改动**：

```diff
--- 09 §4.2 安全切片
+ - 首次在 Demo 主机部署前：D23 deploy 验收——主机安装集与本产品安装前缀扫描、E0 子进程观测、
+   执行准入（受控执行视图或 ExecPaths=）生效，DeploymentInventory 记录 approved_digest
--- 09 §4.4 W1 内网主机预检 ④
+ 以及 mount namespace / systemd ExecPaths= 是否可用
```

**副作用**：W3 的工作量略增。若主机不支持执行准入，按 HLD 不能以"一次观测无命中"通过验收，需要尽早暴露。

**配套检查点**：11-27 检查点增加"D23 deploy 验收通过"一项；未通过则按 §4.5 备选处理，并登记补齐日期。

#### P092-06 [NIT] gate 对照表只有三个例子，表本身没有落点和完成日期

**位置**：09 §10"gate 对照表"；原则 4"HLD 每一项交付件与 gate 都对应到负责人、日期和证据路径（§10）"。

**问题**：原则 4 把对照表当作已经存在的依据，§10 却只写了"维护……对应表"并举了三个例子，没有说明放在哪里、何时完成第一版。P1/P2 gate 在 1 月底，到那时表必须已经存在。

**候选改动**：

```diff
--- 09 §10
+ gate 对照表放在仓库固定路径（与开发状态文件同目录），M0a（11-20）前完成 P0–P2 部分，
+ 01 第二批通过（1-22）前完成 P3–P4 部分，第三批通过前完成 P5–P7 部分
```

**副作用**：无。

**配套检查点**：M0a 检查 P0–P2 部分逐项有负责人、日期与证据路径。

---

## 同步项（不计入结论）

| # | 内容 | 涉及 | 说明 |
|---|---|---|---|
| S1 | HLD §13 P0 的"01 按 v2.x 范围扩展并经三方评审 draft freeze"改为分批口径：第一批为 P0，第二、三批为对应阶段的入口条件 | HLD §13、09 §3 | 随 P092-01 (a)。属 HLD 处置表允许的"随 01 扩展的一致性修订" |
| S2 | 正常执行路径中多目标部分失败：broker 推完目标 1、目标 2 被远端拒绝后，发 `release_outcome = release_failed`。ReleaseOutcomeRequest 没有 targets，Run 以"发布失败"结案，RunSummary 看不出目标 1 已发布，开发者重新提交时可能再次发布 | 01 ReleaseOutcomeRequest（L628）、HLD §4.2.5 两值固定 | 这是 v1.0 冻结语义下的既有行为，不在本轮 X1 的范围内，不计入结论。建议在 01 扩展第一批中给 ReleaseOutcomeRequest 增加可选的 targets，并让 RunSummary.release_targets（C22-03）在该路径上同样填写；不改两值映射 |

已核对 HLD 附录 B 第 7 组：v2.12 追加项（签名表与扫描器 digest 表格式、现行版本例外比对、执行准入与 exec 记账、`deployment_dependency_violation`）已登记。本报告 H212-01 至 H212-03 若被采纳，只改变这些条目的内容，不新增条目。
