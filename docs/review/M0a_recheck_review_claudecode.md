# M0a 定向核对：上轮处置的落实情况（claudecode）

评审方：claudecode　日期：2026-11-12

## 0. 结论

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 映射表（M1、M2） | **GO** | 0 | 0 | 1 | 1 |
| 09 v0.5 §3.1 | **GO** | 0 | 0 | 1 | 0 |
| 门禁代码（C1–C3、内容豁免） | **NO-GO** | 0 | 1 | 1 | 1 |
| 08 v1.1 落实 | **GO** | 0 | 0 | 4 | 1 |

**上轮本方反例复测**：全部"已拒绝"，逐条结果见 §3.1。

**唯一的 MAJOR 是 G-01**：凭据赋值规则的 `\b` 前缀与"键名后紧跟冒号或等号"两点，使最常见的两种泄露形式不被检出：

- 环境变量里带前缀的键名（如 `DB_` 前缀的口令变量、`aws_` 前缀的密钥变量）；
- JSON / YAML 中带引号的键名。

`\b` 出自本方上轮 CI-05 的候选方案，属于本方方案引入的回归。修复是一行正则，已实测在全部已跟踪文件上新增命中为 0。

---

## 1. 输入与验证边界

**仓库状态**：

- 第一次 `git pull --rebase` 报 "Cannot rebase onto multiple branches"。检查后 `branch.main.merge` 只有一项，`git fetch` 正常，HEAD 与 `origin/main` 相同。立即重试得到 "Already up to date"，判断为与其他会话并发 fetch 引起的瞬时错误。
- HEAD 为 `be05cc7`。

**sha256**：

| 文件 | sha256 |
|---|---|
| docs/08_Codex_Dev_Guide_v1.1.md | 1581c53a679a6b141bda67adc06c5c5d2a7fddfc6796e2d0070afd5c9debe620 |
| docs/09_Phased_Dev_Plan_v0.5.md | 81da755af67a260b83cd4257b5ab9ae8cd2b29995b9dc53f473945f0871d4e86 |
| docs/dev/01_extension_mapping.md | 80917f78a110be122bfc7fdd8142bd80aa899bdbca28c9924f469e9293665e5b |
| docs/dev/gate_matrix.md | e783ddcd3bd233d401b05daf8edbfa9736b4e76c154eccbf4f8fa7345d720392 |

**看了**：

- 处置表全文；
- 映射表全文，并用脚本把每个消费行的子键反查批次；
- 09 v0.4 → v0.5 的逐句 diff，以及 HLD v2.14 §4.2.1 示例、§4.2.6、§13；
- 01 v0.24 中 `config`、BenchReport、`metric` 的核心定义；
- 08 v1 → v1.1 的 diff；
- ci/ 全部源码与策略文件：gate.sh、gate_steps.sh、gate_runtime.py、d23.py、checks.py、installed.py、registrations.py、pre_push.py、hooks/pre-push、bypass_register.json、content_policy.json、content_exemptions.json 全部 21 条；
- 根目录 conftest.py、pyproject.toml；
- STATUS.md 的裁决与挂账；
- task-004 / task-005 交付目录中报告的选取方式：gate_report.txt 与最后一次成功的 attempt 逐字节一致，失败的 attempt 也已保留。

**没看**：

- 本轮其他评审方的意见；
- tests/ci 各测试的全部断言：只看了测试名与关键段；
- uv.lock 内容；
- evidence.txt 全文；
- gate 对照表：只抽查了 P0-G01 / G02、P1-G01 与 D23-PENDING 各行。

**运行过的命令**，全部以 `nice -n 19 ionice -c3` 包装，脚本均在 `git worktree add --detach` 建立的临时副本中、以 `systemd-run --user --scope -q -p CPUQuota=100% -p MemoryMax=2G` 串行运行：

1. 复测上轮反例与新反例。所有输入都在运行时拼接，调用 `ci.d23.check_file` 与 `ci.checks.content_hits`。
2. 用候选内容规则测正负样本，并统计它们在全部已跟踪文件上的命中。
3. 在副本中写一个临时测试文件，验证 pytest 跳过策略；随后运行 `ci.checks bypass`。
4. 在临时克隆与本地裸仓库之间演示 pre-push。
5. 在临时目录演示 pyc 遮蔽源文件。

结束时已执行 `git worktree remove --force` 与 `prune`，临时克隆和目录也已删除。

**没有运行** `ci/gate.sh`、构建或全量测试，没有安装任何软件，没有修改 hooks 配置。

**负责人前提**按原样接受：

- HLD v2.14 定稿；
- 01 v0.24 为核心契约开发基线；
- 不得引入 PHP；
- M1 批次裁决（静态部分前移第一批）；
- 网络命名空间不可用时只记录、不阻断。

另外，task-005 已裁决 Bearer 规则的接受范围（15 位含数字、16 位全字母不检出），本报告只按评审要求评估其合理性。

---

## 2. 映射表与 09 v0.5 §3.1

### 2.1 定向核对结论

| 核对项 | 结论 |
|---|---|
| M1 四个第一批静态子键是否只含语法、字段名、类型与加载规则 | bench-opt-syntax、rules-rest、bench-static、local-min **成立**。gate-fields 的定义有问题，见 MAP-R1 |
| 原第二批子键收窄后，与新子键之间有无重复或空隙 | mock-bench-opt / bench-opt-syntax、bench / bench-static、schema / local-min 三对都写成"语义 / 静态，后者只引用前者"，**无重复**。B7-5-3 有一处空隙，见 MAP-R1 |
| P1 能否只凭第一批加载 §4.2.1 四份示例 | **能**，前提是 01 核心中节点的 `config: dict[str, JsonValue]` 保持不透明，`suites`、`collect_profile`、`methods` 都不做类型检查（见 MAP-R2）。local 后端的 comparison 为 verified，加载期不需要解析指标依赖。脚本反查结果：T11.3-024 / 025 / 041-a / 049 只消费第一批键 |
| B7-5-4 拆分后，P4 类别是否只消费第二批 | **是**。T11.3-073-b / 079 / 083 只消费 B7-5-2-schema 与 B7-5-4-load。全表 P1 / P2 行只有第一批键，P3 / P4 行没有第三批键 |
| ImageRecord 是否只有一处定义 | **是**。只由 B7-4-2 的两个子键定义；B7-4-1 的子键只写行为，并引用 B7-4-2 |
| 新增的规则③、deferred、镜像失败分类子键是否完整 | **完整**。B7-1-2-rules-rest 含规则③、规则①对 bench_report 的适用以及 V-13b / V-15；B7-4-1-deferred 在第一批，由 T11.3-052 消费；B7-4-1-image-failure 在第二批，由 T11.3-054-a / 064-b / 076 / 086 消费 |
| B7-5-3 字段清单是否确定 | decision-core 与 measurement **已确定**；gate-fields 仍是开放清单，见 MAP-R1 |
| 09 v0.5 §3.1 是否自洽、与 HLD §13 P0 是否冲突 | 与 §13 P0 **不冲突**：P1 只消费第一批，"第一批 = Demo 与 P1 / P2 所用条目"成立。fail-closed 的覆盖面不完整，过渡规则也没有落到映射表，见 N09-R1 |

### MAP-R1 MINOR　B7-5-3-gate-fields 的清单不确定，唯一的示例与 01 的 metric 规则矛盾，并留下一处空隙

**位置**：映射表 B7-5-3-gate-fields、B7-5-3-decision-core 两行；01 v0.24 L137、L271。

**问题**：

1. gate-fields 写作"DSL gate 条件可引用的 BenchReport 字段名与类型，**如** gate_eligible"。上轮 M2 指出的"等 / 待确认"在这里换成了"如"，清单仍不确定。
2. 01 v0.24 L137 规定，`metric = "<producer_node>.<field>"` 只能解析到报告体中**顶层定点字符串**、标注为 `# gateable` 的字段。gate_eligible 是布尔值，不可能被 DSL gate 条件引用。它在 HLD 示例中的作用是阈值 gate"只认 gate_eligible 报告"，属于运行期过滤，也就是 decision-core 的语义。示例一、四实际引用的 `benchmark.regression_pct` 已经是 01 §2.4 的核心 gateable 字段（L271），P1 静态加载并不需要 gate-fields 提供任何新字段。
3. decision-core 写"mode、gate_eligible、validation_complete、opt_verdict 的判定语义；**字段名 / 类型由 B7-5-3-gate-fields 供静态加载引用**"。但 gate-fields 只覆盖"gate 条件可引用的"字段，所以 mode、validation_complete、opt_verdict 这三个字段的名称与类型没有任何子键负责。

**反例**：第一批起草时按 gate-fields 的字面意思，把 gate_eligible 标为 gateable。校验器于是接受 `metric: benchmark.gate_eligible`。这与 01 §1 的"定点字符串"规则冲突，比较按 Decimal 进行时会失败或被迫特殊处理。

**候选修改**：

```diff
-| B7-5-3-gate-fields | DSL gate 条件可引用的 BenchReport 字段名与类型，如 gate_eligible；不含判定语义 | 静态字段名/类型 | 第一批 … | P1 | …
+| B7-5-3-names | BenchReport 扩展字段 mode、gate_eligible、validation_complete、opt_verdict 的字段名与类型（不含判定语义）；本批不新增 `# gateable` 字段，DSL 阈值 gate 仍只引用 01 §2.4 已标注的核心 gateable 字段（如 regression_pct）；gate_eligible 对阈值 gate 的过滤作用属 decision-core | 静态字段名/类型 | 第一批 … | P1 | …
-| B7-5-3-decision-core | mode、gate_eligible、validation_complete、opt_verdict 的判定语义；字段名/类型由 B7-5-3-gate-fields 供静态加载引用；… | …
+| B7-5-3-decision-core | mode、gate_eligible、validation_complete、opt_verdict 的判定语义（含阈值 gate 只认 gate_eligible 报告）；字段名/类型见 B7-5-3-names；… | …
```

T11.3-024 / 025 / 041-a / 049 中的 `B7-5-3-gate-fields` 同步改为 `B7-5-3-names`，"gate 字段类型"改为"BenchReport 扩展字段名 / 类型"。

**副作用**：子键改名后，`ci.checks provisional` 依据的叶键集合随之变化；目前没有 provisional 标注，不受影响。

**测试**：在映射一致性检查中加一条断言：第一批中任何"字段名 / 类型"类子键都不得出现"如""等""待确认"这类开放措辞。

### MAP-R2 NIT　"P1 只凭第一批加载四份示例"依赖 `config` 不透明，映射表没有写明

**位置**：映射表 M1 说明段；B7-5-4-load 行。

**问题**：

- 示例一、二、四的 `config` 中还有 `suites: auto`、`collect_profile` 和 `methods`。
- 其中 "`suites: auto` 与显式选择"的加载期 schema 在 B7-5-4-load，属于第二批；`collect_profile` 与 `methods` 不在附录 B 的任何条目中。
- P1 能加载这些示例，只是因为 01 v0.24 L73 的 `config: dict[str, JsonValue]` 不做类型检查。第一批起草时如果把 Benchmark / Optimization 的 `config` 改成封闭模型（`extra="forbid"`），P1 加载会再次依赖第二批。

**候选修改**：M1 说明段追加一句："第一批只为 `config.mode`、`max_opt_rounds` 定义类型；`suites`、`collect_profile`、`methods` 等其余 config 键在第二批（B7-5-4-load）之前保持 01 §1 的不透明 `dict[str, JsonValue]`，第一批不得把这些节点的 config 改为封闭模型。"

**副作用**：无。

**测试**：P1 的 T11.3-025 加一条断言：示例原文中 `config` 的全部键都能在只有第一批模型的条件下加载。

### N09-R1 MINOR　"fail-closed 移到运行期审批"只覆盖审批，其他消费 BenchReport 判定语义的运行期位置没有覆盖；过渡规则本身也没有映射键

**位置**：09 v0.5 §3.1 第一批一格（"BenchReport 谓词通过之前，运行期审批遇到 release_requires 含 BenchReport 一律 fail-closed"）；映射表 M1 说明段。

**问题**：

1. 校验器现在接受含 `bench_gate` 的流水线：示例一、四都有阈值 gate，并且注释写明"只认 gate_eligible 报告"。示例四（compiler_bench_only）**没有 release 节点**，也不经过审批。第二批通过之前，它在 P1 / P2 的 mock 运行中，或在由它派生的 Demo"构建 + 后续 Agent"子集中运行到 `bench_gate` 时，需要 gate_eligible 的过滤语义（decision-core，第二批），这一点没有定义。审批环节的 fail-closed 管不到这里。结果是要么通过（fail-open），要么各自实现一套临时语义，而后者违反 08 §1 规则 2。HLD §4.3.5 的 C-16 terminal_success 也同样会检查放行谓词。
2. "运行期审批拒绝含 BenchReport 的 release_requires"本身是一条契约行为。P2 的 Approval 服务要实现它，需要类型化的拒绝原因，并且要在第二批通过后撤销。HLD §13 P0 要求"任一阶段 gate 验收时，其生产或消费的契约条目……必须已经三方评审通过"，而这条规则在映射表里没有子键，第一批评审也就不会覆盖它。

与 HLD §13 P0 的措辞没有冲突（P1 只消费第一批）；问题在于覆盖面与可追溯性。

**候选修改**：

09 v0.5 §3.1 第一批一格：

```diff
-BenchReport 谓词通过之前，**运行期审批**遇到 release_requires 含 BenchReport 一律 fail-closed（拒绝审批），校验器的静态加载不受影响。
+BenchReport 谓词通过之前，**运行期凡需 BenchReport 判定语义之处一律 fail-closed**：审批 CAS 与核销前复核拒绝含 BenchReport 的 release_requires；读取 BenchReport 的阈值 gate 与 C-16 terminal_success 判为不通过，并以可见原因记录（不路由到通过分支）。校验器的静态加载不受影响。
```

映射表增加一个第一批子键：

```diff
+| B7-5-7-bench-pending | 第二批前的过渡规则：审批 / 核销复核 / 阈值 gate / C-16 遇 BenchReport 判定语义时 fail-closed 的类型化原因（如 bench_semantics_pending），第二批通过后由 B7-5-7-bench 与 decision-core 取代 | 过渡守卫/原因码 | 第一批 | P1 / P2 / Demo | …
```

T11.3-027（P2，审批运行时）与 T11.3-024 / 025 补消费这一子键。

**副作用**：第二批通过后，01 要删除这条过渡规则，属于一次契约版本变更，需在第二批评审中一并处理。Demo 子集如果含 `bench_gate`，在第二批之前该节点固定不通过，因此 Demo 流水线不应含读取 BenchReport 的阈值 gate；这与 09 中"空壳 Benchmark 只证明结构"一致。

**测试**：

- P1 / P2 mock：示例四在第二批之前运行到 `bench_gate` 时，结果为不通过并记录原因码；
- 示例一走到审批时被拒，拒绝原因码与阈值 gate 的原因码一致；
- 第二批模型就位后，两条用例都改为按谓词判定。

---

## 3. 门禁代码（C1–C3 与内容豁免）

### 3.1 上轮本方反例复测

| 上轮编号 | 反例（输入均在运行时拼接） | 结果 |
|---|---|---|
| CI-01 | `.txt`：全大写 PHP 起始标记 + 语句 | **已拒绝**（unclassified_text_signal） |
| CI-01 | `.html` 模板：大小写混合的起始标记 | **已拒绝** |
| CI-01 | `.py` 字符串常量：大小写混合的起始标记 + 语句 | **已拒绝**（unapproved_python_fragment） |
| CI-01 | 改名为 `.py` 的非 Python 文件：全大写起始标记 | **已拒绝** |
| CI-01 | `.py`，`coding: hz`，原始字节含起始标记 | **已拒绝** |
| CI-01 | `.py`，`coding: iso2022_jp`，原始字节含起始标记 | **已拒绝** |
| CI-02 | 登记了扫描器摘要、以单个常量承载完整程序的 `.py` | **已拒绝** |
| CI-03 | venv 中不属于 RECORD 的 pyc | **已拒绝**：`installed.py` 判 runtime_pyc_unlisted；当前 `.venv` 与仓库内均无 pyc |
| CI-04 | 未提交修改的工作树上运行门禁 | **已拒绝**：gate.sh 第 10 行，以及 gate_runtime 的两次 `clean_tree`。本项为静态核对 |
| CI-05 | OpenAI 项目密钥、Anthropic 密钥、Slack 令牌、GitLab 令牌 | **已拒绝**（token） |
| CI-05 | YAML 不带引号的口令、`client_secret` 赋值 | **已拒绝**（credential-assignment） |
| CI-05 | 私网地址后接句点 | **已拒绝** |
| CI-05 | 其他 depot 名、大小写不同的 depot 名 | **已拒绝** |
| CI-05 | `ENCRYPTED PRIVATE KEY`、`PGP PRIVATE KEY BLOCK` | **已拒绝** |
| CI-06 | 新子包 / 新 Agent 包逃出 import-linter 边界 | **已拒绝**：engine 合约默认封闭，`test_contract_lists_complete_and_detect_new_packages` 检查列表完整性。本项为静态核对 |
| CI-07 | 跳过开跑检查、并发两个门禁 | **已拒绝**：不再有内部参数；flock。残余问题见 E-05 |
| CI-08 | intranet 无条件跳过、子进程不禁网、未记录 uv 版本 | **已拒绝** |

**BOM 专项**：

| 输入 | 结果 |
|---|---|
| UTF-8 BOM 加完全相等的签名常量 | 通过（正确） |
| UTF-8 BOM 加大写变体常量 | 拒绝 |
| UTF-8 BOM 加注释内的程序 | 拒绝 |

**C3（Codex 上轮反例，静态核对）**：

- `task_directory` 对 `docs`、`dev`、`deliver`、`task-NNN` 逐级以 `O_NOFOLLOW` 打开；
- 已有的 `gate_report*` 必须是普通文件，且 `st_nlink == 1`，可防硬链接别名；
- 新报告以 `O_CREAT|O_EXCL|O_NOFOLLOW` 在目录描述符下创建；
- `protect_history` 同时检查 HEAD 与索引。

因此"把任务目录做成指向 task-001 的符号链接"**已拒绝**。残余的路径重读问题见 E-05。

### G-01 MAJOR　凭据赋值规则漏检带前缀的键名、带引号的键名与含空格的口令；Bearer 规则只在独立出现时有效，Basic 认证完全漏检

**位置**：`ci/content_policy.json` 第 6 行（credential-assignment）、第 11 行（authorization-bearer）。

**实测**：以下样本均在运行时拼接，当前规则 0 命中。

| 样本 | 原因 |
|---|---|
| 环境变量形式：键名带 `DB_` 前缀的口令变量 | `\b` 要求关键字前是词边界，而下划线属于词字符 |
| `aws_` 前缀、后接 `secret_access_key` 的赋值 | 同上 |
| JSON 中带双引号的口令键 | 关键字与冒号之间夹着引号 |
| YAML 中带单引号的 `api_key` 键 | 同上 |
| 带引号、含空格的口令短语 | 值的字符类排除了空格，第一个词不足 8 个字符 |
| `Authorization:` 头中的 Basic 凭据（base64） | 没有任何规则覆盖 |
| `Authorization:` 头中的 Bearer 值，16 位全字母或 15 位 | 按 task-005 的接受范围不检出 |

`\b` 来自本方上轮 CI-05 的候选方案，task-004 照此采纳，属于本方方案引入的回归。在上轮之前的规则下，`DB_` 前缀的形式本来能检出（虽然当时要求值带引号）。

**关于"16 位以上且含数字"的评价**：

- 对**独立出现**的 `Bearer` 可以接受：全字母令牌出现的概率很低，换来的是较低的误报。
- 但实测发现了一个**误报**：`Bearer` 后接一个由 refresh、token、v2、rotation 四个词用连字符连成的英文短语时会命中，因为短语含数字且超过 16 位。
- 对 `Authorization:` **请求头**里的值，不应再套用"含数字"和"16 位"这两个限制。请求头语境本身已足以说明这是凭据，限制只会造成漏检。

**候选修改**：

```diff
-    "credential-assignment": "(?i)\\b(?:password|passwd|pwd|secret|client_secret|api[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?token|authorization|cookie)\\s*[:=]\\s*[\"']?[^\\s\"'`<>]{8,}",
+    "credential-assignment": "(?i)(?<![A-Za-z0-9])(?:[A-Za-z0-9]+[_-])*(?:password|passwd|pwd|secret(?:[_-]access)?[_-]?key|secret|api[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?token|authorization|cookie)[\"']?\\s*[:=]\\s*(?:[\"'][^\"'\\n<>`$]*[^\\s\"'<>`$][^\"'\\n<>`$]{6,}[\"']|[^\\s\"'`<>$]{8,})",
-    "authorization-bearer": "(?i:\\bBearer)[ \\t]+(?=[A-Za-z0-9._~+/=-]*[0-9])[A-Za-z0-9._~+/=-]{16,}"
+    "authorization-header": "(?i:\\bauthorization)[\"']?\\s*[:=]\\s*[\"']?(?i:Bearer|Basic|Token)[ \\t]+[A-Za-z0-9._~+/=-]{8,}",
+    "authorization-bearer": "(?i:\\bBearer)[ \\t]+(?![a-z][a-z0-9]*(?:-[a-z0-9]+)+(?![A-Za-z0-9._~+/=-]))(?=[A-Za-z0-9._~+/=-]*(?:[0-9]|[A-Z][A-Za-z0-9._~+/=-]*[a-z]|[a-z][A-Za-z0-9._~+/=-]*[A-Z]))[A-Za-z0-9._~+/=-]{16,}"
```

`version` 升为 `task-00N-content-v4`，豁免表的版本同步升级。

**改动要点**：

- 键名前允许带 `xxx_` 前缀，键名后允许一个引号；
- 引号内的值允许含空格，但至少要有 8 个字符；
- 值中出现 `$` 时不算命中，即排除 `${VAR}` 与 `$TOKEN` 这类变量引用；
- 新增"请求头语境"规则，覆盖 Bearer / Basic / Token，只要求值至少 8 位；
- 独立出现的 Bearer 规则把"含数字"改为"含数字，或大小写混合"，并排除全小写的连字符短语。

**副作用**：

- **实测样本**：
  - 上述 7 类漏检样本全部命中；
  - 以下负例都不命中：连字符短语、`${…}` 变量引用、尖括号占位符、`$TOKEN`、以 Basic 开头的英文句子。
- **仓库实测**：三条规则在全部已跟踪文件上的命中均为 **0**，不需要新增豁免。
- **关键字取舍**：试过把通用的 `token` 也加入关键字。结果在 01 各版本中命中 20 处 `token_id=None`、16 处枚举赋值、2 处 `[REDACTED]`，误报过多，因此不加入；`authorization` 也不允许带后缀。

**测试**：

- 在 `test_real_content_signals` 的正例中加入上表 7 类样本，负例中加入上述 5 种；全部在运行时拼接，只输出规则名；
- 在 `tests/ci/test_checks.py` 中断言：新规则在仓库现有文件上命中为 0。

### G-02 MINOR　UTF-16 / UTF-32 编码的文件同时绕过 D23 文本信号与内容扫描

**位置**：`ci/d23.py` 第 116 行（只在原始字节上匹配）；`ci/checks.py` 第 45 行（只按 UTF-8 解码）。

**实测**：

- 带 BOM 的 UTF-16 `.txt` 与 `.py`、UTF-32 `.html`，内容都是 PHP 起始标记加语句，`check_file` 的结果都是 `[]`；
- 一段同时含私网地址与私钥头的文本，按 UTF-8 编码时命中 2 条规则，改成 UTF-16 编码后命中 0 条。

HLD §11.2 的判定信号是"含 PHP 起始标记的**文件**"，不限定编码。内容边界要防的是凭据或地址进入公开仓库，与文件编码同样无关。

**候选修改**：新增一个共用函数，D23 与内容扫描都对它返回的每一份文本视图做判定。

```python
WIDE_BOMS = ((codecs.BOM_UTF32_LE, "utf-32"), (codecs.BOM_UTF32_BE, "utf-32"),
             (codecs.BOM_UTF16_LE, "utf-16"), (codecs.BOM_UTF16_BE, "utf-16"))

def text_views(data: bytes) -> list[bytes]:
    """Raw bytes plus a UTF-8 re-encoding of wide-encoded text (BOM or NUL-interleaved)."""
    views = [data]
    for bom, codec in WIDE_BOMS:
        if data.startswith(bom):
            views.append(data.decode(codec, "replace").encode("utf-8"))
            return views
    if len(data) >= 8 and data[1::2].count(0) >= len(data) // 4:
        views.append(data.decode("utf-16-le", "replace").encode("utf-8"))
    return views
```

- `ci/d23.py`：`marker_present = any(MARKER_RE.search(v) for v in text_views(data))`。`.py` 文件若是宽编码，`python_fragments` 返回 False，于是得到 unapproved_python_fragment。
- `ci/checks.py`：`content_hits` 对每个视图分别匹配，结果按 (规则, 行号) 去重。

**副作用**：

- 两次 UTF-32 BOM 的检测要排在 UTF-16 之前，因为 UTF-32-LE 的 BOM 以 UTF-16-LE 的 BOM 开头；
- 二进制文件可能偶然满足"隔字节为 NUL"的条件，从而多解码一次，只会增加检出、不会漏检；
- 仓库与 `.venv` 中目前没有这类文件，修改后结果应不变，需按 G-01 的方式实测确认。

**测试**：

- 用 UTF-16 / UTF-32 编码、运行时拼接的 PHP 起始标记文本，后缀分别为 `.txt`、`.py`、`.html`，断言判定失败；
- 用 UTF-16 编码的私网地址文本，断言 `content_hits` 命中。

### G-03 NIT　21 条内容豁免：19 条成立；2 条 intranet 标记豁免应改为修正规则

**位置**：`ci/content_exemptions.json`；`ci/content_policy.json` 第 7 行（internal-host）。

**逐条核对**：

- 21 条的摘要都与当前文件一致，所在行确实命中所登记的规则。
- **19 条**是 01 v0.7–v0.24 与一份 01 评审中 fake_llm golden vector 的固定伪端点，同一字符串，用于规范哈希判定，**成立**。STATUS 已挂账"01 下一版改用 .invalid 域名"，不再重复。
- **2 条**（`tests/ci/test_offline.py` 第 16 行、`agents/skeletons/tests/test_agent_offline.py` 第 15 行）命中的是 pytest 的 intranet 标记表达式。internal-host 规则把"标记属性点号后接 intranet"当成了主机名。

  这两条豁免本身没有问题，但会带来维护负担：豁免绑定整个文件的摘要，这两个测试文件每改一次都要重新登记；以后每新增一个 intranet 用例文件，还要再加一条豁免。豁免数量因此会持续增长，评审也会因次数多而流于形式。

**候选修改**：

```diff
-    "internal-host": "(?i)\\b[a-z0-9][a-z0-9.-]*\\.(?:internal|intranet|corp|local|sec\\.samsung\\.net)\\b",
+    "internal-host": "(?i)\\b(?!pytest\\.mark\\.)[a-z0-9][a-z0-9.-]*\\.(?:internal|intranet|corp|local|sec\\.samsung\\.net)\\b(?!\\s*[(:])",
```

同时删除这两条豁免。

**副作用**：

- `(?!\s*[(:])` 只排除"后面紧跟括号或冒号"的属性 / 调用写法；
- 主机名后跟端口号的写法（冒号后接数字）也会被这一条排除。因此建议用 `(?!\s*\(|:\D)` 代替，只排除"冒号后跟非数字"。

**测试**：

- 运行时拼接 pytest 的 intranet 标记表达式，断言不命中；
- 运行时拼接"主机名 + 冒号 + 端口"，断言仍命中。

---

## 4. 08 v1.1 在 gate.sh / gate_runtime.py 中的落实

### 4.1 逐项落实情况

| 08 v1.1 规则 | 落实位置 | 结论 |
|---|---|---|
| 放宽项登记 | `ci/registrations.py`、`ci/bypass_register.json` | 已落实；覆盖面有缺口，见 E-04。现有 3 条登记的理由都成立，见下 |
| provisional 三方核对 | `check_provisional` | 已落实：只认叶键；位置与键在标注和清单之间一一对应，并检查重复；清单表头缺失即失败 |
| 干净工作树 | gate.sh 第 10 行、`clean_tree` 两次 | 已落实；但被忽略的文件不在范围内，见 E-02 |
| 开跑记录不可跳过与 flock 互斥 | `execute` 没有任何跳过参数；`heavy_lock` | 已落实；残余问题见 E-05 |
| 实际优先级核对 | `effective_limits` 读取 `getpriority` 与 `ionice -p` | 已落实，驱动进程与 gate_steps 中各核对一次 |
| 报告写入失败即失败 | `write_all`、`fsync`、日志进程退出码、读回校验 | 已落实；报告选取方式见下 |
| 禁网与 intranet 规则覆盖全部测试树 | 根目录 `conftest.py`；`unshare` | 已落实；跳过策略可被关键字冒用，见 E-03 |
| pre-push 模板 | `ci/hooks/pre-push`、`ci/pre_push.py` | 只扫描工作树与提交信息，不扫描待推送提交的内容，见 E-01 |

**现有 3 条放宽项登记**：

1. engine 合约的 `ignore_imports`：唯一 engine 可导入 LangGraph，属于设计本身，**成立**；
2. agent 合约的 `ignore_imports`：08 §3.2 规定的公开面，**成立**；
3. `conftest.py` 第 21 行：仅在未开启内网时为 intranet 用例加 skip，**成立**。

三条都按"值的完整摘要"绑定，追加一条 ignore 即会失效，设计正确。

**报告选取**：task-004 / 005 的 `gate_report.txt` 与最后一次成功的 attempt 逐字节一致，失败的 attempt 也已一并提交，符合"首次失败保留在证据中"。

### E-01 MINOR　pre-push 只扫描工作树与提交信息，不扫描待推送提交中的内容

**位置**：`ci/pre_push.py` 第 13 行（`check_content()` 扫描的是工作树）、第 35–39 行（只扫描提交信息）；08 v1.1 §2.4"执行仓库提供的内容扫描……并扫描待推送提交的提交信息"。

**实测**：在临时克隆中设 `core.hooksPath ci/hooks`，然后依次：

1. 提交一个运行时写入私网地址的文件；
2. 删除该文件并再次提交；
3. 推送到本地裸仓库。

hook 输出 `Pre-push commits checked: 2; result=pass`，推送成功。含私网地址的 blob 进入了远端历史。

同类情形还有：先提交凭据、在工作树中改掉但没有提交就推送，此时被推送的是含凭据的提交，而 hook 扫描的是改过的工作树。

**候选修改**（`ci/pre_push.py`）：对每个待推送提交新增或修改的 blob 做内容扫描。豁免仍按"路径 + 摘要 + 规则 + 行号"匹配：

```python
def pushed_blob_failures(commits: set[str], rules: dict[str, str], entries: list[dict[str, Any]]) -> int:
    failures = 0
    seen: set[str] = set()
    for commit in sorted(commits):
        rows = git("diff-tree", "-r", "--no-commit-id", "--root", "-z", "--diff-filter=AMRC", commit)
        fields = rows.split(b"\0")
        for meta, path in zip(fields[0::2], fields[1::2]):
            if not meta:
                continue
            oid = meta.split()[3].decode()
            if oid in seen:
                continue
            seen.add(oid)
            data = git("cat-file", "blob", oid)
            for rule, line in content_hits(data, rules):
                if not any(e["path"] == path.decode() and e["rule"] == rule and e["line"] == line
                           and e.get("digest") == digest(data) for e in entries):
                    print(f"PUSH_BLOB_FAIL {commit}:{path.decode()}:{line} rule={rule}")
                    failures += 1
    return failures
```

`-z` 输出中重命名会占三个字段，实现时用 `--no-renames`，或按状态字母解析字段。08 v1.1 §2.4 相应把"并扫描待推送提交的提交信息"改为"并扫描待推送提交的提交信息与其新增 / 修改的文件内容"。

**副作用**：

- 新分支第一次推送时（远端对象为全零），会扫描整个历史中的 blob。历史中存在只报告、不阻断的命中（task-001 报告时为 29 处，按现行规则需重新统计），这会导致首次推送新分支失败。
- 建议对远端为全零的情况，以 `git merge-base local origin/main` 为界，只扫描新增提交。

**测试**：在 `tests/ci/test_pre_push.py` 中用临时仓库复现上面的"提交后删除"序列，断言 `check_updates` 返回 1，并输出 `PUSH_BLOB_FAIL`。

### E-02 MINOR　"门禁结果绑定被测内容"不覆盖被忽略的文件：仓库中的 pyc 可以遮蔽已提交的源码，venv 中的文件也不与 RECORD 哈希核对

**位置**：gate.sh 第 10 行与 `clean_tree`（`git status` 默认不列出被忽略的文件）；`.gitignore` 第 2–3 行（`__pycache__/`、`*.pyc`）；`ci/checks.py` 第 147–154 行。

**实测**：在临时目录中，源文件内容为 `X = 1`；另写一个 timestamp 型 pyc，内容编译自 `X = 2`，头部填入源文件的 mtime 与 size。在设置 `PYTHONDONTWRITEBYTECODE=1` 的情况下导入，得到 `X = 2`。

`PYTHONDONTWRITEBYTECODE` 只禁止写 pyc，不禁止读。在仓库中，`framework/ledger/__pycache__/…pyc` 被 `.gitignore` 第 2 行忽略。因此可以在"干净"的工作树上，让 pytest 执行一份与提交内容不同的代码，而 gate_report 记录的 HEAD 与 tree 摘要都是真实的。

同理，`.venv` 中被改动的已安装文件（例如修改过的 pytest 插件）不会被 `uv sync --locked` 重新安装，D23 扫描也只检查文本信号，不核对 RECORD 中记录的 sha256。

**候选修改**：

```diff
 # ci/gate_steps.sh
 export PYTHONDONTWRITEBYTECODE=1
+export PYTHONPYCACHEPREFIX="$(mktemp -d "${TMPDIR:-/tmp}/cs-pycache.XXXXXX")"
+ignored=$(git ls-files --others --ignored --exclude-standard -- . ':(exclude).venv' \
+  | grep -E '(__pycache__/|\.py[co]$|\.pth$|(^|/)(site|user)customize\.py$)' || true)
+[[ -z "$ignored" ]] || { printf 'Ignored executable artifacts present:\n%s\n' "$ignored" >&2; exit 1; }
```

在 `ci/checks.py` 遍历 RECORD 时核对哈希：

```diff
         for relative in distribution.files:
             path = Path(str(distribution.locate_file(relative)))
             owned.add(path.resolve())
@@
+            if relative.hash is not None and relative.hash.mode == "sha256":
+                actual = base64.urlsafe_b64encode(hashlib.sha256(path.read_bytes()).digest()).rstrip(b"=").decode()
+                if actual != relative.hash.value:
+                    failures.append(f"distribution: {name}/{relative}: record_hash_mismatch")
```

**副作用**：

- 设置 `PYTHONPYCACHEPREFIX` 后，Python 只在这个临时前缀下读写 pyc，仓库内的 `__pycache__` 一律不再被读取；
- 被忽略的可执行产物在门禁中直接判失败，开发需要先清理，门禁本身不自动删除；
- RECORD 哈希核对会多读一遍已安装的文件（约 2600 个），在 L1 限额下增加的耗时很小。

**测试**：

- 临时仓库中放入一个遮蔽源码的 pyc，`gate_steps` 的预检应失败；
- 篡改一个伪造分发包中的文件内容，使其与 RECORD 哈希不一致，断言 `record_hash_mismatch`。

### E-03 MINOR　skip / xfail 策略按关键字判断 intranet，可被同名节点冒用；`pytest.importorskip` 不在放宽项清单中

**位置**：根目录 `conftest.py` 第 77 行（`"intranet" not in report.keywords`）；`ci/registrations.py` 第 52–58 行。

**实测**：在副本中写一个临时测试，以 `pytest.param(1, id="intranet")` 参数化，函数体内调用 `pytest.importorskip` 导入一个不存在的模块。pytest 退出码为 0，结果 "1 skipped"，跳过被放行。同一函数不带该 id 时会被正确拒绝（退出码 4）。随后 `ci.checks bypass` 只检出现有的 3 条登记，没有发现 `importorskip`。

原因：pytest 把参数化 id 和各级节点名都写进 `report.keywords`。因此名为 intranet 的参数 id、目录（例如 `tests/intranet/`）或类，都能让任意 skip 通过。

**候选修改**：

```diff
+_INTRANET_IDS: set[str] = set()
+
 def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
     for item in items:
-        if (
-            os.environ.get("CODINGSYSTEM_INTRANET") != "1"
-            and item.get_closest_marker("intranet") is not None
-        ):
+        if item.get_closest_marker("intranet") is not None:
+            _INTRANET_IDS.add(item.nodeid)
+            if os.environ.get("CODINGSYSTEM_INTRANET") != "1":
                 item.add_marker(pytest.mark.skip(reason="intranet: disabled on development machine"))
@@
 def pytest_runtest_logreport(report: pytest.TestReport) -> None:
-    if "intranet" not in report.keywords and (report.skipped or hasattr(report, "wasxfail")):
+    allowed = (
+        report.nodeid in _INTRANET_IDS
+        and os.environ.get("CODINGSYSTEM_INTRANET") != "1"
+        and report.skipped
+        and "intranet: disabled on development machine" in str(report.longrepr)
+    )
+    if (report.skipped or hasattr(report, "wasxfail")) and not allowed:
```

`ci/registrations.py` 的名单中加入 `"pytest.importorskip"`。

**副作用**：

- 内网运行（`CODINGSYSTEM_INTRANET=1`）时，intranet 用例自身的 skip 也会失败，比现在更严；
- 改动后 `conftest.py` 的行号与摘要都会变，`bypass_register.json` 中第 3 条需要按新的行与摘要重新登记。

**测试**：在 `test_pytest_policy.py` 中补以下情形，全部在运行时生成：

- 参数 id 为 intranet；
- 测试位于名为 intranet 的目录下；
- 用例调用 `importorskip`；

断言门禁失败，且 `check_bypass` 能检出 `importorskip`。

### E-04 MINOR　放宽项登记不覆盖阈值与范围类配置

**位置**：`ci/registrations.py` 的 `config_bypasses`；08 v1.1 §1 规则 5"不得降低覆盖率阈值"；pyproject.toml 中 `[tool.codingsystem.coverage]`、`[tool.coverage.run] source`、`[tool.coverage.report] fail_under`、`[tool.mypy] strict / files`、`[tool.pytest.ini_options] testpaths`、`[tool.ruff.lint] select`；`.importlinter` 中合约的类型、`source_modules`、`forbidden_modules`、`allow_indirect_imports`。

**问题**：放宽项检查只识别 `omit`、`exclude_lines`、`per-file-ignores`、`extend-exclude`、`ignore_imports`、mypy overrides 和 addopts 中的选择项。以下改动都能放宽门禁，但不会被检出：

- 把 `line_minimum` 从 80 改成 50，或把 `critical_branch_minimum` 改成 0；
- 把 `[tool.coverage.run] source` 缩小到 `["ci"]`，这与 `omit` 等效；
- 从 `testpaths` 中去掉 `agents/skeletons/tests`；
- 把 mypy 的 `strict` 改为 false；
- 删掉一条 import-linter 合约。

现有测试都使用自带的阈值配置，没有测试把仓库中的实际值固定下来。

**候选修改**：新增 `ci/gate_config_baseline.json`，按配置段记录规范化 JSON 的摘要：

```json
{"version": "task-00N-gate-config-v1",
 "sections": {"pyproject:tool.codingsystem": "…", "pyproject:tool.coverage": "…",
              "pyproject:tool.mypy": "…", "pyproject:tool.pytest": "…",
              "pyproject:tool.ruff": "…", ".importlinter": "…"}}
```

`check_bypass` 按同一方法重新计算各段摘要。任何一段与基线不同，都必须在 `bypass_register.json` 中有对应条目（`rule = "gate-config:<段名>"`，`line_digest` 填新的摘要），否则失败。

**副作用**：

- 此后任何门禁配置变更（包括收紧）都需要登记一次，代价不大，而且所有改动都可追溯；
- 基线文件本身属于受审文件。

**测试**：

- 在临时目录复制 pyproject，把 `line_minimum` 改为 50，断言 `check_bypass` 返回 1；
- 补登记后返回 0；
- 删除一条 import-linter 合约后返回 1。

### E-05 NIT　互斥与证据收尾的三处残余问题

**位置**：`ci/gate_runtime.py` 第 276–277 行、第 218–222 行、第 242 行与第 261 行。

**问题**：

1. 锁文件的位置取决于环境：设置了 `XDG_RUNTIME_DIR` 时在该目录下，没设置时退回到 Git 公共目录。一个会话有这个变量、另一个会话没有（例如经 ssh 或 cron 启动）时，两者用的是不同的锁文件，互斥失效。08 v1.1 §4.2 规则 1 写的是固定的 `${XDG_RUNTIME_DIR}`。
2. 日志进程异常时，`producer.terminate()` 只向 `gate_steps.sh` 发送 SIGTERM，其子进程（pytest、uv）留在 scope 中继续运行。驱动进程随后退出、释放锁，下一次门禁就可能与这些残留进程并行。
3. 报告通过目录描述符安全地新建，但新鲜度校验（第 242 行）和结尾校验（第 261 行）又按路径重新打开文件。如果交付目录在这期间被替换成链接，读回的就是另一个文件。

**候选修改**：

- 锁文件固定为 `Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}") / "codingsystem-heavy.lock"`；目录不存在就拒绝运行，不再退回到其他位置。
- `Popen(command, …, start_new_session=True)`；终止时用 `os.killpg(producer.pid, SIGTERM)`，等待 10 秒后改用 `SIGKILL`。释放锁之前，确认 `/sys/fs/cgroup/<scope>/cgroup.procs` 中只剩当前进程。
- 读回改为通过已有的描述符：`os.pread(fd, n, 0)` 与 `os.fstat(fd).st_size`，不再按路径打开。

**副作用**：无功能变化。

**测试**：

- 用伪造的日志进程以退出码 1 结束，断言 producer 的整个进程组都已结束；
- 在没有 `XDG_RUNTIME_DIR` 的环境中运行门禁时被拒绝。

---

## 5. 能否作为 M0a（11-20）的开发输入

**映射表（GO）**：M1、M2 的核心目标都已达成：

- P1 只凭第一批即可加载四份示例；
- P4 不消费第三批；
- ImageRecord 只有一处定义；
- 规则③、deferred、镜像失败分类都有子键。

可以作为 M0a 的开发输入，也可以作为第一批起草的索引。MAP-R1（gate-fields 改为确定的字段名清单）与 N09-R1（过渡期 fail-closed 扩展到阈值 gate 与 C-16，并补映射键）应在 12-11 第一批定稿之前，随第一批起草一并处理，否则会把一个不能用作 metric 的字段写进契约，并让示例四的运行期行为无定义。

**门禁（代码部分 NO-GO）**：上轮本方的全部反例都已被拒绝，C1–C3 的落实质量很好；08 v1.1 的各项规则也都有真实实现。阻断项只有 G-01：凭据规则漏检环境变量形式和 JSON 形式。这两种是最常见的泄露形式，而且是本方上轮方案引入的回归。修复只需改一行正则，实测不新增豁免，建议在下一次门禁运行前完成。其余 MINOR 可在 M0a 之后、contracts 包落地之前处理。

完成 G-01 后，门禁可以作为 M0a 的开发输入。在此之前，门禁的其他各项（锁文件、静态检查、测试与覆盖率、D23、放宽项、provisional）照常可用，只是内容扫描的"通过"结论不能用来证明没有凭据进入仓库。
