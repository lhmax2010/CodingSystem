# M0a 定向核对 — Codex

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 映射表 | NO-GO | 0 | 1 | 0 | 0 |
| 09 v0.5 §3.1 | GO | 0 | 0 | 0 | 0 |
| 门禁代码 | NO-GO | 0 | 1 | 0 | 0 |
| 08 v1.1 落实 | GO | 0 | 0 | 1 | 0 |

日期：2026-11-12。只核对 M0a 上轮处置及 task-003～005 的相关改动。共 3 条问题；相同问题不跨部分重复计数。08 落实的 GO 按“没有 BLOCKER / MAJOR”的标准给出，不表示其 MINOR 已修复。

## 输入与验证边界

同步后 HEAD：`be05cc7f52b1f88f1e2ae32d30fae012a60a6f3c`，符合指定基线。四份输入的 SHA256：

| 文件 | SHA256 |
|---|---|
| docs/08_Codex_Dev_Guide_v1.1.md | `1581c53a679a6b141bda67adc06c5c5d2a7fddfc6796e2d0070afd5c9debe620` |
| docs/09_Phased_Dev_Plan_v0.5.md | `81da755af67a260b83cd4257b5ab9ae8cd2b29995b9dc53f473945f0871d4e86` |
| docs/dev/01_extension_mapping.md | `80917f78a110be122bfc7fdd8142bd80aa899bdbca28c9924f469e9293665e5b` |
| docs/dev/gate_matrix.md | `e783ddcd3bd233d401b05daf8edbfa9736b4e76c154eccbf4f8fa7345d720392` |

首次 `git pull --rebase` 返回 `fatal: Cannot rebase onto multiple branches.`。按追加指令作如下只读诊断，输出为：

```text
git status -sb
## main...origin/main

git config --get-all branch.main.remote
origin

git config --get-all branch.main.merge
refs/heads/main

git config --get-all remote.origin.fetch
+refs/heads/*:refs/remotes/origin/*

git worktree list
/home/linhao/Toolchain/development/CodingSystem  be05cc7 [main]
```

随后 `git fetch origin main` 成功，`git merge --ff-only origin/main` 返回 `Already up to date.`。这些诊断没有证明失败由多值 branch 配置造成；不据此猜测原因，也没有修改主仓库或全局 Git 配置。

阅读范围：本轮四份输入；M0a_review_disposition；上一轮 Codex、Claude Code 两份意见；STATUS；task-003～005 的 REPORT 与对应交付记录；涉及的 ci 脚本、策略、登记表、根 conftest 与定向测试。只为交叉核对引用 HLD v2.14 §4.2.1、§4.2.6、§11、§13、附录 B，以及 01 v0.24 的既有报告字段。未阅读其他评审方本轮意见，未重审冻结设计，未访问 Quickbuild 或内网，未安装软件，未运行构建、全量测试、索引或 `ci/gate.sh`。

命令边界与实际验证：所有开发机 shell 命令均以 `nice -n 19 ionice -c3` 开头。下面用 P 表示该前缀，用 S 表示 `P systemd-run --user --scope -p CPUQuota=100% -p MemoryMax=2G -p MemorySwapMax=0 nice -n 19 ionice -c3`；这是命令记录的缩写，不是省略资源限制。使用的 Python 解释器是系统 python3.12，pytest 使用主仓库既有 `.venv/bin/python -B`，没有重装依赖。

1. P 下执行 Git 诊断、fetch / ff-only、rev-parse、sha256sum；文本核对使用 P 下的 rg、sed、cat、nl。
2. `P git worktree add --detach /tmp/codingsystem-m0a-recheck-codex-be05cc7 HEAD`；全部测试和 Python 脚本只在该副本中串行运行。systemd 用户 scope 可用，没有无约束回退。
3. S 下执行 `python -B -m pytest -q`，显式选择 `tests/ci/test_d23.py test_checks.py test_gate_runtime.py test_registrations.py test_pytest_policy.py test_offline.py test_pre_push.py`（除首项外均同目录）：**199 passed，1 skipped，4.30 秒**。跳过项为授权的 intranet 用例。刻意未选择会启动 gate.sh 的 test_gate_entry.py。
4. S 下单独选择 `tests/ci/test_installed.py tests/ci/test_imports.py`：**8 passed，1.69 秒**。合计 **207 passed、1 skipped**，不生成覆盖率，不把此结果冒称完整门禁。
5. S 下执行临时 `recheck_probe.py`：96 格大小写 / 载体 / BOM 矩阵、2 种有状态编码、上轮内容反例、日志失败的无负载子进程哨兵，以及 21 条豁免摘要与命中上下文核对。载荷在运行时拼接，脚本和夹具不提交。日志反例只启动短暂睡眠与写哨兵文件，不启动检查工具或实际门禁。
6. S 下执行 `python3.12 -B -m ci.checks bypass`：检测 3 / 登记 3；`python3.12 -B -m ci.checks provisional`：0 个标注、空子键清单。
7. 将本报告复制进副本后，以 S 执行用户指定的 `python3.12 -B -m ci.checks content`：`Current content findings: 0`；提交信息另经 content-stdin 核对，不登记新豁免。临时副本在验证结束后删除。提交、推送仅涉及本报告；按追加指令使用 fetch、rebase origin/main、push origin HEAD:main，不再 pull，不 force push。

测试证据是本机受限执行的合成夹具证据；现存 task-004 / task-005 完整门禁是开发方历史证据，本次未重跑。pre-push 测试仅在新建临时 fixture 仓库安装 hook，未改变主仓库的 hooksPath。

## 处置忠实性与逐项落实

原意见计数为 Codex 10、Claude Code 19，共 29 条。E1～E6 为 6 个，M1～M4 为 4 个，G1～G2 为 2 个，C1～C10 为 10 个，合计 22 个。两家合并项恰为 M1、M2、G1、C1、C2、C5、C6，29 − 7 = 22。来源与方案归属相符；E6 引用的 Codex 重跑保留意见是非编号意见，没有额外算成第 30 条。M1 明确标为合并后的设计裁决，没有冒称两家原方案完全相同。

| 处置 | 核对结果 |
|---|---|
| E1 | 08 §5.1(10) 与 gate_steps 的授权跳过说明均改为比较 01 §0.3 的契约包版本。已落实。 |
| E2 | 禁止清单、逐条登记、配置层检测与非 intranet skip / xfail / XPASS 失败均落实；定向测试通过。三条现存登记理由见后文。 |
| E3 | 08 约束所有推送者及提交信息；标准库 pre-push 模板验证当前文件、待推送提交信息和标签对象。临时本地推送正反例通过。平台 secret scanning / push protection 仍属负责人已登记待办，不重复报。 |
| E4 | L0.5 分级与共同 flock 已落实；失败后的检查子孙生命周期有新缺口，见 R-E1。 |
| E5 | 标注位置 / 叶键 / 清单一一核对，父键、缺记录、错行、读取失败均拒绝；Demo 约束已写入指南。 |
| E6 | 环境、执行者、回放来源、干净树与已通过叶键证据要求已补；首次失败输出保留规则已补。 |
| M1 | 静态前移、运行期审批兜底、套件 load / business 拆分均按裁决落实；local-min 沿用了原候选的两字段清单，遗漏 build_image，见 R-M1。 |
| M2 | ImageRecord 唯一字段定义归 B7-4-2；规则③ / V-13b / V-15、deferred、镜像失败分类各有新子键；判定语义清单及 comparison 唯一归属已补。 |
| M3 | T052、T029、Demo 第 2 步补引；T053 只测配额与终态，远程 version 已移 P6-TODO-01。 |
| M4 | 两列已补，角色已填写；01 落点暂空是明确允许的起草期回填，不重新报告。 |
| G1 | P0-D03 / G01 / G02 分别为 11-20、12-29（备选 12-30）、12-11；汇入 12-31，Demo 安全切片按首次使用与截止日双约束。 |
| G2 | P0–P2 契约入口列、D23-PENDING-09～12 均补齐。 |
| C1 | 原始字节忽略大小写检出、仅 UTF-8 片段豁免、精确签名与 BOM 处理均经复测；没有重现上轮绕过。 |
| C2 | 前缀全局放行、短赋值、路径及令牌族漏报已修；task-005 有意收窄后，明确认证头中的上轮反例仍放行，见 R-C1。 |
| C3 | 目录逐级 no-follow、最终文件链接 / 硬链接拒绝、HEAD + index、排他 attempt 均落实。 |
| C4 | 两个退出码和写入失败都导致失败；原来的假成功已关闭。新发现终止不覆盖子孙，计入 R-E1，不重复算 C4。 |
| C5 | 根 conftest 覆盖两棵测试树，内网开关与子进程 namespace 探测已落实。namespace 不可用记录而不阻断，接受负责人前提。 |
| C6 | 旧内部跳转参数已删除；正常入口强制预检、首行写入读回、新鲜度核对、实际优先级验证、共同 flock。低内存与陈旧记录用注入测试验证，没有真实压低主机内存。 |
| C7 | Python 扫描器不再按完整文件摘要跳过片段检查；非 Python 规则表仍摘要绑定，测试已纠正。 |
| C8 | bytecode 环境变量提前，RECORD 外扫描与未归属 pyc 拒绝落实；定向安装集夹具通过。部署侧完整 pyc 清单是既有挂账。 |
| C9 | shell / driver 均检查任务记录之外的脏树，记录 HEAD 与 tree；只静态核对 shell 入口，没有违反“不运行 gate.sh”的要求。 |
| C10 | 默认封闭及包列表完整性断言落实；导入正反例 5 类和新增包检测通过。 |

### 映射与 09 的具体边界

四个新增第一批键没有提前 BenchPolicy 统计或 BenchReport 通过判定：bench-opt-syntax 只含字段 / 取值 / budget 静态约束；bench-static 只含报告类型与生产者；gate-fields 只含名称 / 类型；local-min 只含声明与静态准入。四个原第二批键改为运行期或其余后端内容，定义 / 消费分工成立。唯一影响 P1 原文加载的剩余批次缺口是 R-M1。

B7-5-4-load 现在覆盖锁定身份、auto / 显式选择及 absolute / relative 依赖；T073-b、T079、T083 都在 P4，消费 load / schema 两个第二批键，既验证 absolute-only 正例，也验证 relative、auto、未知依赖、优化与必需 Bench 发布的反例，不消费第三批统计或测量记录。B7-5-3 decision-core 明列 mode、gate_eligible、validation_complete、opt_verdict 的语义，measurement 明列逐指标结论 / 区间、spec_inconclusive_count、opt_gain_pct、baseline_revoked、baseline_unavailable；comparison 及不可比原因归 B7-5-16。静态字段声明引用与业务字段语义不是两份权威定义。ImageRecord 的效应条目只引用字段，不再重复定义。

09 §3.1 的审批 fail-closed **成立**：加载验证的是图、注册类型与规则；发布审批必须有已评审的报告通过谓词，尚未定义则拒绝，不能把“能加载”当成“可批准”。Demo 不要求 BenchReport，四份原文的静态验收也无需提前执行 Benchmark 判定。它没有改变 HLD §13 P0 的第一批边界；修正 R-M1 即可补足具体字段归批，不需撤销负责人 M1 裁决或推迟 P1 到第二批。第二批前不能以固定真值模拟一个已经获准的 BenchReport 发布审批。

### 本方上轮反例逐条复测

| 原编号 / 反例 | 本次结论与证据 |
|---|---|
| C-01：普通 / 改名文件中的大小写变体 | **已拒绝**。补充矩阵覆盖 8 种大小写、普通文件、字符串、bytes、隐式拼接、f-string、注释，再交叉 BOM：96 格中 88 格拒绝，8 格仅是原签名的合法片段，符合预期。 |
| C-01：Python 常量中的混合 / 全大写变体 | **已拒绝**。原样小写完整签名才豁免，含正文或 f-string 不豁免。HZ / ISO-2022-JP 两个补充反例均拒绝。 |
| C-02：普通长值赋值（阳性对照） | **已拒绝**。 |
| C-02：以 example 开头的同等长赋值 | **已拒绝**；补测 placeholder / redacted 同样拒绝，不再全局豁免。 |
| C-02：认证头中的 40 个全字母 Bearer 值 | **仍可绕过**，content_hits 返回空；R-C1。补测 15 位含数字放行、16 位含数字拒绝，与 task-005 当前设计完全一致。 |
| C-02：12 字符密码赋值 | **已拒绝**。 |
| C-02：任意 depot 名的多段路径 | **已拒绝**。 |
| C-03：日志接收者写入失败仍成功 | **已拒绝**。/dev/full、只读 fd、末尾写入失败及 logger 非零退出均导致失败，不再生成成功证明。另有 R-E1。 |
| C-04：task 新目录链接到旧交付目录 | **已拒绝**。逐级目录链接测试保持旧文件字节不变；追加最终链接、非普通文件和 staged-delete 保护均通过。 |
| C-05：Agent 子树没有 offline / intranet 规则 | **已拒绝**。双树夹具断言 offline 存在且网络调用被拒；内网开关关闭时跳过、开启时执行，均经定向测试。没有发网络请求。 |
| C-06：旧内部参数跳过预检 | **已拒绝（静态核对入口）**。新入口只收一个任务号，无原跳转参数；驱动的预检拒绝 / 超时 / 新鲜度与 flock 争用、实际限额和优先级错误的拒绝由低负载单元测试验证。没有运行 gate.sh 或制造真实资源耗尽。 |

### 三条放宽登记与 21 条内容豁免

三条放宽登记均成立：engine 对 LangGraph 的唯一授权、Agent 只导入 SDK / contracts 的公开面、仅对未开启内网开关的 intranet 用例跳过。前两条是默认封闭规则内的设计允许边，不是任意导入白名单；第三条由根 hook 条件限制。路径、规则、行内容摘要、理由、任务与解除条件具备，实际检查输出 3 / 3；配置变更、未登记代码与普通 skip / xfail 的反例失败。

以下按现存豁免逐条核对，不把 task-004 已删除的 90 条算在内。21 条全部匹配现行文件摘要及对应规则 / 行号；本次没有新增或修改豁免。

| 文件（docs 下版本文件均指 01_Contract_Spec） | 行 | 上下文判断 |
|---|---:|---|
| v0.7 | 520 | fake_llm 固定 golden 输入，成立 |
| v0.8 | 535 | 同上，成立 |
| v0.9 | 566 | 同上，成立 |
| v0.10 | 568 | 同上，成立 |
| v0.11 | 587 | 同上，成立 |
| v0.12 | 607 | 同上，成立 |
| v0.13 | 626 | 同上，成立 |
| v0.14 | 630 | 同上，成立 |
| v0.15 | 635 | 同上，成立 |
| v0.16 | 640 | 同上，成立 |
| v0.17 | 643 | 同上，成立 |
| v0.18 | 654 | 同上，成立 |
| v0.19 | 667 | 同上，成立 |
| v0.20 | 686 | 同上，成立 |
| v0.21 | 690 | 同上，成立 |
| v0.22 | 693 | 同上，成立 |
| v0.23 | 693 | 同上，成立 |
| v0.24 | 694 | 同上，成立；下一版改用保留域名已有挂账 |
| docs/review/01_v0.7_review_{kimi,claudecode,codex}.md | 65 | 上述 golden 输入的历史引用，成立 |
| tests/ci/test_offline.py | 16 | pytest 标记表达式误命中主机规则，成立 |
| agents/skeletons/tests/test_agent_offline.py | 15 | 同上，成立 |

前 19 条的判断依据是规范中明确的 fake_llm 用途和完整摘要绑定，不能推广为“看起来像示例的地址一律安全”；不改历史哈希输入，亦不允许未来任意新增同类豁免。后两条不是实际主机地址。

## 问题与候选修改

### R-M1 — MAJOR：第一批 local-min 少了镜像加载必读的 build_image

**位置**：映射表 B7-5-2-local-min、B7-5-2-schema、末尾“定义与消费边界”；关联 T025 / T029 / T049、P1-G01 与 Demo 第 2 步。

**原文依据**：local-min 写“能力声明最小 schema：source_input、comparison 两项及取值枚举”；schema 将“其余能力项”分到第二批。HLD §4.2.6 明定“镜像生成本身另须 build_image 能力为 verified”，且“LocalGbsBackend 的 source_input、comparison、build_image 能力声明为 verified……四份示例流水线因此可加载”。

**问题 / 反例**：四份原文均有 local 镜像节点。按第一批只有上述两项的 schema 起草和实现，加载器无法读取已评审的 build_image 声明：缺失按未验证拒绝，则四份示例（包括无 Bench 的示例三）失败；跳过这项检查或在代码里硬编码未入第一批的字段，则破坏第一批契约先行与加载期能力守卫。不是要求提前运行时判定，只差一个明确的静态能力字段。遗漏来自采用的旧候选清单，开发忠实执行并不意味着清单完整。

**候选 diff**（设计审定后改映射，叶键数不变）：

```diff
--- docs/dev/01_extension_mapping.md
+++ docs/dev/01_extension_mapping.md
@@ B7-5-2-local-min
-能力声明最小 schema：source_input、comparison 两项及取值枚举
+能力声明最小 schema：source_input、comparison、build_image 三项及取值枚举；
+LocalGbsBackend 三项声明 verified，镜像节点加载须核对 build_image == verified
@@ B7-5-2-schema
-source_input/comparison 的最小 schema 与枚举只引用 B7-5-2-local-min
+source_input/comparison/build_image 的最小 schema 与枚举只引用 B7-5-2-local-min
@@ 定义与消费边界
-local-min 定义 source_input/comparison 的最小 schema、枚举及 local 后端加载期判定
+local-min 定义 source_input/comparison/build_image 的最小 schema、枚举及 local 后端加载期判定
@@ T11.3-025、T11.3-029、T11.3-049、Demo 第 2 步
+本地能力消费显式含 build_image；其声明与加载规则均由第一批 local-min 提供。
```

**副作用**：第一批增加一个静态字段及一个已有 HLD 守卫，不提前 Quickbuild 实证、Benchmark 统计或运行期能力语义；09 的泛称“本地最小能力”无需改变排期。字段 schema 由 local-min 唯一定义，第二批只能引用。

**测试 / 验收**：P1 对四份原文使用第一批注册夹具加载成功；只把 build_image 改为 unverified、unsupported 或删除字段时，含镜像的示例一律拒绝。映射自查从 HLD 加载守卫反查三个字段的定义键，不能仅验证消费列里的键都标第一批。

### R-C1 — MAJOR：Bearer 收窄把明确认证头中的合法形态一起放行

**位置**：ci/content_policy.json:6、11；tests/ci/test_checks.py；task-005 REPORT 的接受范围。对应处置 C2 的收窄后复核。

**原文依据**：task-005 将认证方案后的值限制为“长度至少 16 且含数字”；规则含数字前瞻及 `{16,}`。08 §2.4 禁止“任何凭据、令牌、cookie、私钥”，处置 C2 明确要补 Bearer 头漏报。

**问题 / 反例**：运行时构造一个明确的 Authorization 头，认证方案为 Bearer，其后为 40 个全字母字符；content_hits 仍返回空。15 位含数字的头值也放行。credential-assignment 不能兜底：它只看到长度为 6 的方案单词，遇空格即停止，达不到赋值规则下限。数字并不是这类凭据必有的性质，长度 16 也不是认证头内容可公开的界线。减少散文误报是合理目标，但把同一启发式用于明确认证头，会重新放过本方上一轮提供的反例。

此项**不是声称实现违背 task-005 裁决**；实现和测试忠实执行了它。用户本轮明确要求评估该接受范围，此处认为在有认证头上下文时不合理，应对裁决作局部收窄。普通散文仍可沿用较保守的启发式，不要求恢复被删除的 90 条术语豁免，也不声称正则能发现所有秘密。

**候选 diff**（以下为规则设计 diff；JSON 入仓时作正常反斜线转义，不含任何凭据样本）：

```diff
--- ci/content_policy.json
+++ ci/content_policy.json
@@ rules
  保留当前 authorization-bearer 作为无认证头上下文的启发式。
+增加 authorization-bearer-header：
+(?i)\b(?:proxy-)?authorization["']?\s*[:=]\s*["']?bearer[ \t]+[A-Za-z0-9._~+/=-]+
@@ version
-task-005-content-v3
+下一受审策略版本（与 content_exemptions 的 version 同步）
--- tests/ci/test_checks.py
+++ tests/ci/test_checks.py
@@ Bearer 接受范围
-对所有上下文都断言短值或全字母值放行
+散文上下文与明确 Header 上下文分开；明确 Header 中的全字母长值、
+短于 16 的值、引号包围的 JSON Header、Proxy-Authorization 都必须命中。
+认证机制说明、占位符尖括号与不带值的 Header 名称不作为凭据值命中。
```

**副作用**：明确 Header 中真实载荷形态的示例也会被拒，需改写为无值说明或运行时生成夹具；这是公开仓库可接受的成本。无需给本报告或散文术语加豁免。策略调整须由设计审定，开发不可自行放宽。

**测试**：复用本轮 C2 各载荷，断言所有值只在内存或临时夹具中生成；补 Header 大小写、空白、JSON / Python 字典键、Proxy 头的矩阵。重复 40 全字母与 15 位含数字反例，预期改为拒绝；散文对照仍通过。pre-push 的文件及提交信息各至少覆盖一格，输出只显示规则名。

### R-E1 — MINOR：logger 失败后只终止直接 shell，子孙可越过 flock 生命周期

**位置**：ci/gate_runtime.py:202–223、268–280；08 §4.2(1)、§5.2；处置 C4 / C6 新实现的交叉路径。

**原文依据**：08 要求锁覆盖“受限范围内的全部检查与报告收尾”；supervise 的注释是“ A dead logger must not leave a silent, long-running check behind.”，但两个失败分支都只执行 `producer.terminate()` 和 `producer.wait()`。实际 producer 是 `bash ci/gate_steps.sh`，真正检查在其子进程中。

**问题 / 反例**：本轮直接调用 supervise，producer 先启动一个只睡眠后写哨兵的子进程；logger 读到首行即退出 3。实测返回 `(-15, 3)`，返回时子进程未结束，之后哨兵仍被写出。没有执行 gate.sh。用于真实 gate 时，驱动会结束报告并释放 flock，而 pytest 或其他检查子孙仍可能运行；另一个任务随后可取得锁，与前一任务重叠。当前 scope 的资源上限没有消失，且结果仍为失败，所以不重报“假成功”，定为 MINOR；但失去了用户要求的重任务串行保证。若直接 producer 忽略终止信号，现有无期限 wait 还会一直占锁。

**候选 diff**（生命周期方案，回收 helper 须随测试实现，不只给 shell 增加一条 terminate）：

```diff
--- ci/gate_runtime.py
+++ ci/gate_runtime.py
@@ supervise
-producer = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
+producer = subprocess.Popen(command, stdout=subprocess.PIPE,
+                            stderr=subprocess.STDOUT, start_new_session=True)
@@ logger 创建失败以及 logger 非零退出两处分支
-producer.terminate()
-producer.wait()
+stop_check_group_and_wait(producer, term_grace_seconds=2, kill_grace_seconds=2)
@@ 回收 helper 的契约
+向检查专属进程组发 SIGTERM；到期限仍存活则 SIGKILL；
+等待并回收直接子进程，确认检查组内无仍可运行的后代后才允许退出 supervise。
+driver 异常 / 中断走同一 finally 回收路径；未确认回收不得宣布完整结束并交接锁。
+若检查工具允许脱离进程组，改用可回收的专属 workload cgroup，
+在 launcher/环境不支持时拒绝该种运行方式，不把父 shell 退出当作子树静默。
```

**副作用**：日志失败会终止当前检查及其普通子孙，不能期待测试继续产生有用结果；最多增加有界清理等待。不对整个用户 scope 或其他评审进程发信号。若采用子 cgroup，需要补部署能力探测，不能为此解除外层资源限制。

**测试**：新增“检查孙进程写哨兵 + logger 非零退出”与“logger 启动失败 + 检查已派生子进程”夹具；supervise 返回后不得再写哨兵，下一持锁者进入时前一个检查子树已静止。另测 producer / 子进程忽略 SIGTERM 后强杀、driver 异常的清理；仅使用轻量睡眠夹具、限定总时长，仍在 1 核 2G 临时副本中运行。

## M0a 输入判断

09 v0.5 §3.1 的批次裁决和审批兜底可以作为开发输入；08 v1.1 的规定可继续使用，但应补齐失败回收的生命周期落实。映射表须先补 R-M1，门禁须先修正 R-C1 的明确认证头漏报，才能把二者作为 11-20 M0a 已就绪输入；现有 207 项定向通过不能替代这两个反例的关闭，也不表示任何后续阶段 gate 已通过。
