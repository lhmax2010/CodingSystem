# M0a 前评审 — Codex

| 被审部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 08 开发指南 v1 | **GO** | 0 | 0 | 0 | 1 |
| 01 扩展逐条映射表 | **NO-GO** | 0 | 1 | 1 | 0 |
| gate 对照表 P0–P2 | **GO** | 0 | 0 | 1 | 0 |
| task-001 / task-002 门禁代码 | **NO-GO** | 0 | 3 | 3 | 0 |

## 输入与验证边界

评审日期：2026-11-11。先执行 `git pull --rebase`，结果 Already up to date。输入 HEAD 为 **`7ab70a28e5d57c3c427870f8f2176688616b1547`**，即任务指定提交。起始主工作区干净。

| 文件 | SHA-256 |
|---|---|
| `docs/08_Codex_Dev_Guide_v1.md` | `181b81c236ab173c90a087219af4f55989e034c0906c896080a50ddb75886ba1` |
| `docs/dev/01_extension_mapping.md` | `f9c5f8c8e440f77501879f4234daf9379f3fec0ed9af67cee686cc908a0965f0` |
| `docs/dev/gate_matrix.md` | `ef5c9f8c6d850011e8746ece057aa8df53cd7acbc03d7b3d7504fde33d7708bf` |

读取了三份被审文档、STATUS、两个任务的 REPORT 与门禁证据，以及 ci、tests、包配置、锁文件和导入边界。HLD v2.14、01 v0.24、09 v0.4 仅用于核对上游要求，不重新评审；没有读取其他评审方本轮意见。

所有 shell 命令均由 `nice -n 19 ionice -c3` 包装。验证前创建 detached 临时 worktree：`/tmp/codingsystem-m0a-codex-review-7ab70a2`。测试和脚本只在该副本内，串行经 `systemd-run --user --scope -p CPUQuota=100% -p MemoryMax=2G` 运行；用户 scope 可用。使用现有虚拟环境解释器和工具，不安装软件，不访问 Quickbuild、不运行 PHP，不启动构建或全量门禁。**未执行 ci/gate.sh，也未运行会调用它的 test_gate_entry.py。**

命令范围：`git pull/rev-parse/status/worktree`、`sha256sum`、`rg`、`sed`、`cat`、`nl`；受限 Python 的文本抽取、扫描器反例和 shell 日志构造验证；指定 pytest 文件。报告写入与交付另用 `tee`、`git diff/add/commit/push`。临时副本和其中生成物在交付前删除，不提交验证脚本或生成文件。

验证结果：

- 指定 `test_d23.py`、`test_checks.py`、`test_imports.py`、`test_coverage.py`、`test_offline.py`：**43 passed、1 intranet skipped**，不是完整门禁或阶段 gate 通过证明。
- 抽取核对：HLD B7 **75** 个顶层条款与映射原文逐条相同；映射 **111** 行 = **17** 个父键 + **94** 个叶键。这个数字正确，但不能证明消费阶段和子键语义正确。
- 反例实测：PHP 起始标记的两种大小写变体漏报；凭据前缀/常见 Header/短密码及非固定 depot 名的合成输入漏报；历史报告目录别名未被保护 guard 识别；日志写盘失败时生产进程仍返回 0。
- 在 Agent 测试目录加入仅检查 fixture 可见性的临时断言：**1 failed**，可见 fixture 只有 request，没有 offline。没有发出任何网络请求。
- 除所列谓词和工具验证外，资源内部参数旁路、映射依赖、文档日期按静态控制流核对。没有在开发机制造低内存、并发重门禁或真实网络故障。

## 已知事项与整体核对

不重复报告 STATUS/REPORT 已挂账的旧 pytest/import-linter 版本、contracts/CF 暂未实现与 8/9 授权跳过、关键空模块覆盖率 N/A、部署类 D23 尚待实现、个人负责人尚未逐项指派。也不把尚未发生的三方通过/实现/验收日期空白当作缺陷。下文 M-01/M-02 针对 task-002 **声称已闭合**的消费映射与互斥性，区别于“具体契约字段随后按批次评审”的正常待办。

**08**：角色、设计修改边界、公开仓库要求、锁定、provisional 登记、证据等级和阶段证据包总体可执行。provisional 不能满足阶段验收，Fake 不能替代要求真实的安全切片。L0 仅能用于确实轻量的操作，单文件若执行 property/fuzz 或重任务仍应按 L1；本次任务的更严限额优先。计时敏感用例重跑应保留首次失败，不能用一次单独通过替换完整 gate 结果。四项选择均合理：main 适用于明确的单会话串行；uv 已有锁定和 hash；暂不用托管 CI 可行但本地证据必须可靠；2 核 3G 是可验证上限，开跑门槛接受负责人确定的 MemoryMax 加 1G。问题在实现与版本比较精度，不需推翻这些选择。

**映射**：十组原文完整保留，父键不重复归批，绝大多数状态、数据面、部署及入口条目有落点；Demo 通过谓词按 09 v0.4 将 BenchReport 排除出第一批 release_requires，避免提前依赖真实 Benchmark。多版本报告的构建/UT 列与 P7 Benchmark 列拆分合理。问题是用“P4 不消费 SPEC”直接把加载校验反例移后，以及把 ImageRecord 同时写进两个父项的叶键。

**gate 对照表**：P0 的 3 项交付/2 项 gate、P1 的 6 项交付/3 项 gate、P2 的 8 项交付/3 项 gate 均有落点；Build Gateway 骨架、HTTP/Skill、Demo D23 逐产品单元 exec 记账、构建隔离、LLM 安全切片均已列。09 §10 点名的 P4 对比报告/验证资产及 M1.5 运维 CLI/correction 也登记了，没有因本表只展开 P0–P2 而消失。应修正已有明确日期的行，见 G-01。

**代码**：普通检查失败通过 run/显式 return 传递，实时 cgroup 三项上限并非只打印声明；解释器前后检查与锁定安装成立。import-linter 的五条边界及 root-engine 补充规则均通过真实 CLI 正反夹具，当前注册的包边界有效；新增 Agent 包仍须同步根包/边界配置。D23 的普通后缀、包名、shebang、composer、纯数据摘要、AST 隐式拼接、bytes latin-1、f-string、注释和未登记语言多数路径有真实负向测试。两份 D23 策略表没有目录级免扫，摘要不匹配会失败；修改扫描器后必须重审并更新摘要，不能只改实现不更新受审策略。现有覆盖率高不代表以下未测组合已被保护。

## 问题与候选修改

### D-01 — NIT：契约包版本与文档展示版本的比较对象不明确

**位置**：08 §5.1 第8项，第134行。

**依据**：“`contract_version` 与 01 文档版本头一致”。01 顶部是 v0.24，而 §0.3 的包版本为 `1.0.0.dev13`，两者不能直接相等。

**反例**：实现按“版本头”取 v0.24，会拒绝正确的 contracts 包；取 §0.3 则通过。本条不是重报 8/9 尚未实现，而是将来实现门禁时比较对象不同。

```diff
--- docs/08_Codex_Dev_Guide_v1.md §5.1 第8项
- contract_version 与 01 文档版本头一致
+ contracts 包的 contract_version 与受审 01 §0.3 的契约包版本精确一致；
+ 文档草案展示号仅按 A3 记录映射，不与包版本直接比较。
```

**副作用**：不改包版本或 01，只明确读取源。**测试**：v0.24 文档 + dev13 包通过；同文档 + 其他 dev 包失败；§0.3 缺失或存在歧义时失败。

### M-01 — MAJOR：把 P4 必须执行的能力加载校验移到 P7，消费自查因此产生假阴性

**位置**：映射表 B7-5-4、T11.3-073-b、T11.3-079、T11.3-083；相交的 B7-1-2-mock-bench-opt 与 T11.3-025/041-a。

**依据**：映射写“P4 mock 不消费 SuiteVersion / BenchPolicy / SPEC / MeasurementRecord”，把“absolute/relative SPEC 指标 gate”“auto 套件与 absolute 指标”均列在 **P7、不计入 P1–P4**。但 09 §3.1 第二批明确包含“§4.2.6 后端能力加载期检查规则”；HLD §11.3 的“后端能力加载期检查”又明确引用“absolute-only 按 v2.6 用例组”，该组要求 absolute-only 通过、relative/无法解析拒绝，v2.7 还要求 suites:auto 拒绝、显式锁定 absolute 套件通过。

**具体反例**：一个校验器对 comparison 未验证的后端全部拒绝，就能通过只保留拒绝例的 T073-b，却错误拒绝 HLD 明定可加载的 absolute-only 流水线；若相反地只看 gate 名称放行，则会漏拒 relative SPEC 或 auto 套件。以上都是 Fake 声明与静态解析，不需要真实板子、统计计算或 Quickbuild 实测。把用例改标 P7 并不能证明 P4 已实现完整加载规则。

此外，四份原文示例在 P1 gate 就消费 config.mode/max_opt_rounds 和预算容量约束；把相应子键的最早使用方只写 P4、T025/041-a 又不引用它，也使“最早使用方”失真。第二批日期可能早于 P1 gate，不等于这项依赖不存在。

```diff
--- docs/dev/01_extension_mapping.md
- B7-5-4 | SuiteVersion / BenchPolicy / SPEC / MeasurementRecord schema | ... | 第三批
+ B7-5-4 | 原文保留 | 父键，不归批
+ B7-5-4-load | 套件锁定身份、auto/显式选择、指标 absolute/relative 依赖的加载期最小 schema | 第二批 | P4
+ B7-5-4-business | 统计策略、测量记录及未在 load 子键定义的业务字段 | 第三批 | P7
- T11.3-079 / T11.3-083 | P7 | ...
+ T11.3-079 / T11.3-083 | P4 | Fake 套件/SPEC 依赖声明的真实加载规则 | B7-5-4-load, B7-5-2-schema
+ T11.3-073-b 明确包含上述通过与拒绝子矩阵，不仅测试“缺能力即拒绝”。
- B7-1-2-mock-bench-opt ... 最早使用方 P4 mock
+ B7-1-2-mock-bench-opt ... 最早使用方 P1 原文示例加载；P4 继续消费
+ T11.3-025/041-a 引用该子键；P1 开发/验收前已通过相应 schema，按最早消费规则审定其通过日期。
```

**副作用**：第二批需提前最小的加载期输入 schema，仍不提前实现统计库、真实性能或套件生成；不能把整个 BenchPolicy 生搬到早期。若想推迟加载规则本身，必须由设计方变更上游 gate，不能靠改映射实现。

**测试/检查点**：M0a 核对原文每个通过/拒绝断言的承载行；P4 fixture 交叉 comparison 未验证 × absolute/relative/无法解析 × auto/显式锁定，结果符合 HLD；P1 四份示例按原字节加载并覆盖 max_opt_rounds 容量反例。机械检查引用合法后，还须检查是否删除或推迟了断言。

### M-02 — MINOR：ImageRecord 字段重复归入效应子键和记录子键

**位置**：映射 B7-4-1-image-demo、B7-4-1-image-profile-probe 与 B7-4-2 两个子键。

**依据**：前两行分别含“ImageRecord 最小字段”“ImageRecord 其余核心字段”；B7-4-2-demo-record/rest 又分别定义“ImageRecord 最小入库字段”“ImageRecord 其余字段”。B7-4-1 原文是效应/probe 契约，ImageRecord 本身在独立 B7-4-2。

**反例**：实现一个 ImageRecord 入库字段，可在两个叶键同时登记已完成；以后更改批次或评审状态会产生两个权威落点。94 个键互不重名不能证明内容互斥。

```diff
--- docs/dev/01_extension_mapping.md
- B7-4-1-image-demo ... 可选 mic 最小入库与引用契约、ImageRecord 最小字段
+ B7-4-1-image-demo ... 可选 mic 的效应/入库/引用操作契约；消费 B7-4-2-demo-record，不重复定义其字段
- B7-4-1-image-profile-probe ... image.* / profile.* probe 与 ImageRecord 其余核心字段
+ B7-4-1-image-profile-probe ... image.* / profile.* probe 行为；记录字段引用 B7-4-2-record-rest
```

**副作用**：不改批次，只把字段所有者与消费依赖分开。**检查点**：映射增加“定义/消费”区分；逐字段只有一个定义叶键，多个消费者可以引用；保留 ImageRecord 两批各自通过与实现日期。

### G-01 — MINOR：P0 组成件的既定就绪日期被统一替换为 M0b 日期

**位置**：gate_matrix.md P0-D03、P0-G01、P0-G02（第11–13行）。

**依据**：三行日期都写 2026-12-31；09 §3 M0a 要求 **11-20** 的“08 开发指南 v1……本计划经评审”，第一批通过日为 **12-11**，总部确认随 **12-29 Demo** 进行。表头称“计划日期（09）”。

**反例**：按本表跟踪，08 在 12-30 才就绪仍未逾期，但实际已错过 M0a 和 Demo 开发输入；总部确认行也看不出 12-29 的承诺。这不是已挂账的“缺个人姓名/细化日期”，上游已给出了这些日期。

```diff
--- docs/dev/gate_matrix.md
- P0-D03 ... 2026-12-31（§3 M0b；第一批通过 12-11）
+ P0-D03 ... 2026-11-20 就绪并经评审（M0a）；12-31 汇入 P0 总体验收
- P0-G01 ... 2026-12-31（§3 M0b；第一批通过 12-11）
+ P0-G01 ... 2026-12-29 随 Demo 确认（备选 12-30）；12-31 为 P0 汇总目标
- P0-G02 ... 2026-12-31（§3 M0b；第一批通过 12-11）
+ P0-G02 ... 2026-12-11 第一批三方通过；12-31 汇入 P0 总体验收
```

**副作用**：区分组成件就绪与整体验收，不改变负责人里程碑。**检查点**：M0a 对照 09 原日期，后续周跟踪按组成件日期判延期，而非统一等到 M0b。

### C-01 — MAJOR：PHP 起始标记的大小写变体绕过文本判定

**位置**：ci/d23.py:52、65、74、112、144；tests/ci/test_d23.py。

**依据**：物理字节、AST 解码值和注释均用大小写敏感的 MARKER 匹配。HLD D23 禁止交付 PHP，§11.2 的文本信号用于发现改后缀或无后缀内容；大小写变化不使 PHP 程序变成非执行数据。

**反例及实测**：在临时副本内运行时生成同一短程序并存为未登记的 `.dat` 文件，只改变起始标记中三个字母的大小写。全小写返回 `unclassified_text_signal`，混合大小写和全大写均返回空列表。没有依赖 PHP 运行时，也没有修改策略或申请豁免。真实 PHP 的这类起始标签不区分字母大小写；本轮只实测扫描结果，没有执行 PHP。

```diff
--- ci/d23.py
+ OPEN_TEXT = re.compile(re.escape(MARKER), re.IGNORECASE)
+ OPEN_BYTES = re.compile(re.escape(MARKER.encode()), re.IGNORECASE)
- if MARKER not in value:
+ if not OPEN_TEXT.search(value):
- if token.type != tokenize.COMMENT or MARKER not in token.string:
+ if token.type != tokenize.COMMENT or not OPEN_TEXT.search(token.string):
- for match in re.finditer(re.escape(MARKER.encode()), raw)
+ for match in OPEN_BYTES.finditer(raw)
- marker_present = MARKER.encode() in data
+ marker_present = OPEN_BYTES.search(data) is not None
- if isinstance(value, str) and MARKER in value:
+ if isinstance(value, str) and OPEN_TEXT.search(value):
```

**副作用**：检测面扩大，**豁免仍按签名表完全相等**，不把大小写归一化后任意放行；可能新增文档命中，须按既有逐文件摘要流程审读。更新策略版本及扫描器摘要须随修复评审。

**测试**：运行时生成全部字母大小写组合，覆盖普通文件、改名文件、Python 常量/bytes/隐式拼接/f-string/注释；完整程序均拒绝，原精确签名常量仍通过；摘要豁免不得免除后缀/shebang 等其他信号。

### C-02 — MAJOR：内容规则存在无需逐条审批的凭据全局豁免与常见载荷漏报

**位置**：ci/content_policy.json 的 credential-assignment/token/perforce-path；ci/checks.py:41–74。

**依据**：08 §2.4 禁止“任何凭据、令牌、cookie、私钥”，豁免须逐条登记；当前赋值规则却以负向前瞻全局跳过 example/placeholder/redacted 等前缀，并只匹配至少20字符的受限字符集与引号形式。

**反例及实测**：普通长合成 api_key 赋值能报错；同样赋值仅在值开头加 example 即零命中，无对应 exemption。另有未加引号的 Bearer Header、12字符合成密码均零命中。非固定 depot 名的 Perforce 形式也未命中。没有使用或输出任何真实凭据、地址或业务路径。攻击者不必改变豁免表；误粘贴的真实值恰好有该前缀也同样放行。

```diff
--- ci/content_policy.json
- credential-assignment: 值排除若干文本前缀，长度至少20，限定字符集
+ credential-assignment: 对列出的凭据键检测非空的引号赋值及常见环境赋值；
+ 不因值前缀、长度小于20或包含标点而自动豁免。
+ authorization-bearer: 检测 Header/配置中的非空 Bearer 凭据。
+ perforce-path: 对具有 depot/file 结构的业务路径检测，不仅识别固定两个 depot 名；
+ URL、代码运算符的语法区分与必要的合成例外按明确规则/逐条记录处理。
--- ci/checks.py / ci/content_exemptions.json
+ 只有现有 path + digest + rule + line + reason 的受审条目才能免除上述命中。
+ 不在扫描器中另设“看起来像示例”的免扫路径。
```

**副作用**：会增加示例配置和扫描规则测试的误报；以占位符格式或精确受审条目处理，不换成新的全局前缀免扫。模式检查仍不能识别所有内部业务信息，报告不得把零命中当作完整的公开性审查。

**测试**：运行时拼接前缀变体、短值、带标点值、未加引号 Header 与多种 depot 名；仅有精确 exemption 时通过，改变摘要或行号后拒绝。测试输出只含规则/id，不打印载荷。

### C-03 — MINOR：日志接收者失败不影响门禁退出码

**位置**：ci/gate.sh:46–53。

**依据**：`exec > >(tee -a "$report") 2>&1` 的 tee 是异步进程替换；EXIT trap 只取检查进程的 `$?`。08 §4.2/§5.2 要求可靠的结束标记和门禁证据。

**反例及实测**：仅复刻该 shell 日志结构，把输出端换成拒绝写入的系统设备；tee 报写入失败，生产进程仍 exit 0，控制台仍出现 status=ok。未执行 gate.sh、未写交付目录。磁盘满或证据路径写失败时可能声称成功却没有完整证据。

```diff
--- ci/gate.sh 日志生命周期
- exec > >(tee -a "$report") 2>&1
- EXIT trap 仅以检查进程 $? 决定最终状态
+ 在独立驱动层通过显式 pipe/FIFO 管理检查进程与日志进程，保存两者 PID/退出码；
+ 等待日志进程完成，任何一方失败则整体非零；避免在进程替换中丢失 tee 状态。
+ 仅在检查成功且报告完成关闭/校验后，驱动层对外宣布成功；
+ 日志无法写入时在 stderr 报告证据失败，不输出可被当作有效通过证明的结束记录。
```

**副作用**：增加日志进程回收与状态合并；不改变各检查命令。**测试**：写盘失败、权限拒绝、日志子进程提前退出、检查失败四类夹具均整体失败；正常结果须完整结束标记且返回0。夹具用临时路径，不能覆盖历史交付。

### C-04 — MAJOR：历史报告保护只检查拼写路径，目录别名可截断已提交报告

**位置**：ci/gate.sh:10–13、41–46；tests/ci/test_gate_entry.py。

**依据**：先 `git ls-files --error-unmatch "$report"`，随后 `: > "$report"`；没有拒绝父目录符号链接，也没有用实际目标检查已提交历史。

**反例及实测**：临时副本中让新任务目录 task-999 成为 task-001 的目录符号链接。保护查询返回1（认为不是已跟踪报告），但两个 gate_report 路径的 samefile 为 true。因此外层初始化的截断会作用在 task-001 已提交证据上，发生在 D23 扫描 symlink 之前。验证只做 guard 和 samefile 查询，没有真正截断任何历史文件。直接报告文件别名也有同类问题。

```diff
--- ci/gate.sh 报告创建
- 仅用当前索引的拼写路径判断历史文件，然后 : > report
+ 检查 deliver 根到目标文件的所有组件，拒绝 symlink/非普通目录或文件；
+ 实际路径必须位于本任务的可信目录，不能解析到另一任务或仓库之外。
+ 同时核对 HEAD 与索引中的历史记录，不能因暂存删除而解除历史保护。
+ 用不跟随链接、排他创建的文件描述符创建本次输出；
+ 若需允许未提交报告重跑，用独立 attempt 文件保留前次输出，受控收尾选定最终报告。
```

**副作用**：不再支持把交付目录链接到其他位置；未提交失败报告重跑需要保留 attempt 或明确清理流程。可信目录内原正常路径不受影响。

**测试**：父目录链接、最终文件链接、HEAD 中有报告但索引暂存删除、普通新目录、重复 attempt；所有拒绝例断言历史摘要不变且未启动第1项门禁。真实脚本测试须在隔离副本中运行，本轮未运行它。

### C-05 — MINOR：offline 与 intranet 策略只覆盖 tests 子树，Agent 测试不受保护

**位置**：tests/conftest.py:16–37；pyproject.toml 的 testpaths；agents/skeletons/tests。

**依据**：08 §6.2 要求测试不访问网络、intranet 在开发机跳过；pytest 收集目录同时包含 tests 与 agents/skeletons/tests，而 fixture/collection hook 放在前者的 conftest.py。

**反例及实测**：在 Agent 测试目录放一个只检查 fixture 列表的临时测试，列表仅有 request，没有 offline，断言失败。因而同一测试放入 tests 会受禁网夹具约束，放入业务 Agent 包却不受约束。没有真的建立网络连接。子进程也不会继承 Python monkeypatch，不能据此宣称对子进程统一禁网。

```diff
--- tests/conftest.py
- 全局 offline fixture 与 intranet collection hook 只定义在 tests 子目录
+++ conftest.py 或显式全局 pytest 插件
+ 将 offline 与 intranet 收集策略移到全仓共同加载的 pytest 层，
+ 保证所有 Agent 测试树和后续新增测试目录均加载。
+ 将子进程测试列入禁网策略：通过受控离线执行环境或经验证的子进程入口阻断网络，
+ 不把父进程 monkeypatch 当作子进程隔离证明。
```

**副作用**：业务 Agent 测试需要适配同样的离线约束；Fake 不应依赖真实网络。**测试**：在根 tests 和独立 Agent 树分别断言 fixture 已加载、intranet 被跳过；用无外部请求的哨兵验证子进程也处于离线执行约束，不能仅测父进程 socket。

### C-06 — MINOR：内部参数可跳过开跑门槛，串行与优先级也没有实际守卫

**位置**：ci/gate.sh:5、24–44、54–65。

**依据**：`--in-scope` 是可直接传入的第二参数；它跳过 available/负载等待，只验证 cgroup 上限。nice/ionice 仅输出固定声明。08 §4.2 要求开跑检查及 L1 串行。

**反例（静态）**：在一个已具有所要求 cgroup 限额的 scope 中直接带该参数运行，不经过开跑门槛，也不必具有 nice=19/idle 优先级。两个不同新 task 的外层入口还可各自通过预检、各建一个 scope 并行执行，脚本没有共用锁。硬上限本身仍有效，本问题不是声称能无 cgroup 运行，而是另外几项被写成“已验证”却可跳过。本轮未制造低内存或并发重任务。

```diff
--- ci/gate.sh
+ 在预检前取得仓库共享的门禁排他锁（跨 worktree 使用共同 Git 目录的锁身份），
+ 锁覆盖等待、scope 内检查及报告收尾；另一门禁直接拒绝或有界等待。
- 只有非 --in-scope 分支执行资源预检
+ 执行检查命令前统一复核开跑门槛；内部分支不能仅靠调用参数跳过。
+ scope 内核对实际 nice/ionice；不足则拒绝或在受控启动路径先设置再复核。
+ “Resources”记录实际读取值，不以固定字符串宣称已满足。
```

**副作用**：并发入口更早排队/失败，较严格的最终预检可能再次等待；负责人开跑阈值不变。**测试**：以注入资源读取器测试不足/恢复/超时，内部参数也适用；两个轻量哨兵竞争同一锁只一个进入；优先级不符不允许产生通过证据。不要靠真正占满开发机复现。

## 交付与 M0a 判断

08 v1 可作为开发指南输入，D-01 随契约一致性门禁实现前澄清；gate 对照表内容基本齐全，G-01 应在 M0a 跟踪前更正。**映射表当前不能作为已闭合的 M0a 批次输入**：先修正 M-01 的真实消费依赖，再消除 M-02 的字段双重归属；不需要重审已定稿上游。门禁代码亦不能以现状承接公开仓库内容和历史证据的可靠门禁，须优先修复 C-01/C-02/C-04，再补齐其余保护与反例测试。现有43项测试通过和任务报告中的覆盖率，均不能替代这些未覆盖路径的验收。
