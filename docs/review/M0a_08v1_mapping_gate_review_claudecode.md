# M0a 前评审：08 开发指南 v1、01 扩展逐条映射表、gate 对照表（P0–P2）与门禁代码（claudecode）

评审方：claudecode　日期：2026-11-11

## 0. 结论

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|---|---|---:|---:|---:|---:|
| 08 开发指南 v1 | **GO** | 0 | 0 | 4 | 1 |
| 01 扩展逐条映射表 | **NO-GO** | 0 | 1 | 3 | 0 |
| gate 对照表（P0–P2） | **GO** | 0 | 0 | 2 | 0 |
| 门禁代码（ci/、tests/、配置） | **NO-GO** | 0 | 1 | 6 | 1 |

两条 MAJOR：

- **MAP-01**：四份示例流水线（B7-1-6）被分在第一批，是 P1 gate 的加载用例，Demo 也引用它们。但示例原文实际要用到四个第二批子键：B7-1-2-mock-bench-opt、B7-5-7-bench、B7-5-2-schema、B7-5-3-decision-core。消费映射与 Demo 自查都没有列出这些子键。按 09 v0.4，第二批通过前校验器拒绝含 BenchReport 的 release_requires，所以只靠第一批无法通过 P1-G01。
- **CI-01**：无 PHP 扫描只做"小写 PHP 起始标记"的字节匹配，且 Python 片段判定比较的是解码后再编码的文本。以下两种情况已实测全部通过门禁：
  - 大小写变体（PHP 认可的起始标记）；
  - 声明为 hz / iso2022_jp 编码、原始字节含起始标记的 .py 文件。

  其中大小写变体直接推翻了 HLD §11.3 的断言"伪装为 .py 的 PHP 源 → 拒绝"。

## 1. 输入与验证边界

**仓库状态**：已执行 `git pull --rebase`（Already up to date），HEAD 为 `7ab70a2`。

**受评文件 sha256**：

| 文件 | sha256 |
|---|---|
| docs/08_Codex_Dev_Guide_v1.md | 181b81c236ab173c90a087219af4f55989e034c0906c896080a50ddb75886ba1 |
| docs/dev/01_extension_mapping.md | f9c5f8c8e440f77501879f4234daf9379f3fec0ed9af67cee686cc908a0965f0 |
| docs/dev/gate_matrix.md | ef5c9f8c6d850011e8746ece057aa8df53cd7acbc03d7b3d7504fde33d7708bf |

**看了**：

- 受评三份文件全文；
- docs/dev/STATUS.md、provisional.md；
- deliver/task-001、task-002 的 REPORT.md；
- ci/ 全部文件：gate.sh、d23.py、checks.py、coverage_check.py、两份 D23 策略文件、content_policy.json；content_exemptions.json 看了结构与前若干条；
- tests/ 全部、agents/skeletons 的包与测试；
- pyproject.toml、.importlinter、.python-version、.gitignore；
- 上游原文对照：
  - HLD v2.14 §10、§11.2、§11.3（逐分句检索）、§13、附录 B 第 7 组，以及 §4.2.1 四份示例、§4.2.6 规则；
  - 09 v0.4 §2、§3、§3.1、§4.1–§4.6、§5.2、§5.3、§10。

**没看**：

- 本轮其他评审方的意见：工作区有其他评审方未提交的文件，未打开；
- uv.lock 逐包内容：只核对了门禁读取它的方式；
- evidence.txt、gate_report.txt 的全文；
- 01 v0.24 正文：本轮只作依据，映射核对以 HLD 附录 B 原文为准。

**运行过的命令**，按顺序串行，均以 `nice -n 19 ionice -c3` 包装：

1. git pull / log / ls-files / sha256sum；
2. `systemd-run --user --scope -p CPUQuota=100% -p MemoryMax=2G true`，结果可用；
3. 用 `git worktree add --detach` 建立临时副本；以下各步都在副本中、以 `systemd-run --user --scope -q -p CPUQuota=100% -p MemoryMax=2G` 运行：
   - (a) 用运行时拼接的输入调用 `ci.d23.check_file` 与 `ci.checks.content_hits` 做反例探测；
   - (b) 统计仓库与 `.venv` 中大小写不同的起始标记变体（用于评估修复副作用）；
   - (c) 统计 `.venv` 中不在任何 RECORD 里的文件；
   - (d) `pytest -q -p no:cacheprovider -ra`（不带 coverage），结果为 51 passed、1 skipped（intranet），与 task-002 报告一致；
   - (e) 把拟议的内容规则跑在全部已跟踪文件上，统计命中变化，并用正例样本核对；
4. `git worktree remove --force` 与 `git worktree prune`，临时副本已删除。

**未运行的**：`ci/gate.sh`、构建、全量带 coverage 的门禁。没有安装任何软件，也没有访问内网或 Quickbuild。

**负责人前提按原样接受，不作评价**：

- HLD v2.14 定稿；
- 01 v0.24 是核心契约开发基线；
- 09 v0.4 是排期基线；
- 不得引入 PHP；
- 设计文档 00–09 只由设计方修改；
- 门禁开跑门槛为可用内存不少于 MemoryMax 加 1G。

**已挂账、本报告不重复的事项**：

- 门禁 8、9 跳过；
- 关键模块分支覆盖为 N/A；
- 部署类 D23 待实现：只就本报告 GM-02 指出的漏列项补充；
- pytest / import-linter 固定版本；
- gate 条目的个人负责人与日期；
- 历史内容扫描的 29 处命中。

---

## 2. 08 开发指南 v1

总体判断：

- 规则与 HLD §10 / §11 / §13、09 §2 / §3.1 / §4 / §10 一致。
- 目录、包名、五条依赖边界、门禁九项、阶段 gate 证据都能对上原文。
- 下列问题都是"写了规则但无法机械执行"或"漏了一类绕过途径"，不影响按 08 开工。

### G08-01 MINOR　§1 规则 5 的禁止清单不全，门禁也不检查

**位置**：08 §1 规则 5（L28）、§5.1。

**问题**：

1. 规则 5 只列了 `# type: ignore`、`# noqa`、`pytest.skip`、`xfail`。以下同样能让门禁"通过"却不在清单里：
   - `# pragma: no cover`：直接把未覆盖分支移出覆盖率分母，对 95% 关键分支门槛尤其有效；
   - 配置层面的放宽：coverage `omit` / `exclude_lines`、mypy 的 per-module `ignore_errors`、ruff `per-file-ignores` / `extend-exclude`、pytest `addopts` 中的 `--deselect` / `-k`、import-linter `ignore_imports`。
2. 门禁对上述任一项都不做检查，`-ra` 只是把 skip 打印出来。

**反例**：在 `framework/ledger` 的一个分支上加 `# pragma: no cover`，门禁 5 的分支覆盖照样 ≥ 95%，gate_report 中看不出任何异常。

**候选修改**：

08 §1 规则 5：

```diff
-5. **不放宽门禁。** 不得降低覆盖率阈值、不得添加 `# type: ignore` / `# noqa` / `pytest.skip` / `xfail` 绕过失败，除非提示词明确授权并在开发状态文件登记理由与解除条件。
+5. **不放宽门禁。** 不得降低覆盖率阈值；不得以 `# type: ignore` / `# noqa` / `# pragma: no cover` / `pytest.skip` / `skipif` / `xfail` 绕过失败；不得改动 coverage `omit` / `exclude_lines`、mypy 模块级覆盖、ruff `per-file-ignores` / `extend-exclude`、pytest `addopts` 选择项、import-linter `ignore_imports`、D23 / 内容豁免表来放宽判定——除非提示词明确授权，并在 `ci/bypass_register.json` 逐条登记（路径、行内容摘要、理由、任务号、解除条件）。门禁核对登记表，未登记即失败。
```

`ci/checks.py` 增加 `bypass` 动作：

```python
BYPASS = re.compile(
    r"#\s*(?:type:\s*ignore|noqa|pragma:\s*no\s*cover)"
    r"|pytest\.(?:skip|xfail)\b|@pytest\.mark\.(?:skip|skipif|xfail)\b"
)

def check_bypass() -> int:
    """Every in-code gate bypass must match a reviewed register entry."""
    register = json_file("ci/bypass_register.json")["entries"]
    allowed = {(e["path"], digest(e["line"].encode())) for e in register}
    failures = 0
    for path in repository_files():
        if path.suffix not in {".py", ".pyi"} or str(path) == "ci/checks.py":
            continue
        for line in path.read_text().splitlines():
            if BYPASS.search(line) and (str(path), digest(line.strip().encode())) not in allowed:
                print(f"BYPASS_FAIL {path}: unregistered")
                failures += 1
    return int(failures != 0)
```

另外：

- gate.sh 在 `7-content` 之后增加 `run 8-bypass .venv/bin/python -m ci.checks bypass`，原 8、9 顺延；
- 打印 `pyproject.toml` 中 `[tool.coverage]`、`[tool.mypy]`、`[tool.ruff]`、`[tool.pytest.ini_options]` 各段与 `.importlinter` 的 sha256，供阶段评审对比上一阶段。

conftest 增加钩子：skip / xfail 只要不来自 intranet 标记就判失败。

```python
def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.skipped and "intranet" not in report.keywords:
        raise pytest.UsageError(f"unregistered skip: {report.nodeid}")
```

**副作用**：

- 当前仓库没有上述标记，开工即零登记；
- `ci/checks.py` 自身含正则文本，已在扫描中排除；
- 以后真需要 `# type: ignore`（例如第三方无类型库）时，要先登记。

**测试**：

- 运行时生成含 `# pragma: no cover` 的临时 .py，未登记时 `check_bypass()==1`，登记后为 0；
- 改动该行内容后再次失败；
- 一个非 intranet 的 skip 用例应使 pytest 失败。

### G08-02 MINOR　§2.4 内容边界只在开发任务的门禁中检查，设计、评审提交与提交信息不受约束

**位置**：08 §2.4（L51–62）、§9"托管 CI"一行。

**问题**：

1. 内容扫描只由 `ci/gate.sh` 触发，而门禁只在 Codex 任务中运行。设计方提交 00–09 与处置表、三家评审方提交评审文件时，都直接推送到公开仓库 main，没有任何扫描。
2. 只扫描文件内容，不扫描提交信息、标签注释。
3. "一旦发现敏感内容已推送……不自行重写历史"只讲了历史怎么处理。凭据类泄露真正的补救是立即吊销或轮换，这一步没写。

**反例**：

- 评审方在评审文件里引用一个私网地址或内部主机名后推送：内容已经公开，要等下一个开发任务跑门禁时才被发现。本轮评审要求中特意提醒"否则会触发仓库门禁"，说明检查是事后的。
- 一条提交信息里写了内部服务名，没有任何扫描覆盖。

**候选修改**：

08 §2.4 末尾追加：

```diff
+所有向本仓库推送的一方（开发、设计、评审）推送前执行 L0.5 级的 `python3.12 -B -m ci.checks content`（只依赖标准库，无需虚拟环境）与 `git log @{u}.. --format=%B | python3.12 -B -m ci.checks content-stdin`；仓库提供 `ci/hooks/pre-push` 模板，`git config core.hooksPath ci/hooks` 后自动执行（只改本仓库配置）。凭据类命中一经推送，负责人立即吊销 / 轮换该凭据，与是否改写历史无关。
```

`ci/checks.py` 增加 `content-stdin` 动作：对标准输入按同一规则判定，豁免表不适用。

08 §9"托管 CI"一行改为：

```diff
-| 托管 CI | 暂不启用，以本地 `ci/gate.sh` 为准 | 门禁结果须绑定资源限制与提交号；是否另开 GitHub Actions 镜像由负责人决定 |
+| 托管 CI | 暂不启用 Actions，以本地 `ci/gate.sh` 为准；建议负责人开启 GitHub secret scanning 与 push protection（服务端执行，不占开发机资源） | 门禁结果须绑定资源限制与提交号；服务端推送保护覆盖不经门禁的设计 / 评审提交 |
```

**副作用**：

- 每次推送前多一次约 1 秒的纯标准库扫描；
- push protection 只覆盖平台已知的令牌格式，与本仓库规则互补，不能替代。

**测试**：

- 在临时仓库中安装 hook，提交一个运行时拼接出的命中文件后推送到本地裸仓库，推送应被拒；
- `content-stdin` 对运行时拼接的命中文本返回 1。

### G08-03 MINOR　§4.1 L0 允许不带内存上限运行"单个测试文件、小脚本"，§4.2 规则 1 的"串行"没有机制保证

**位置**：08 §4.1 表 L0 行（L106）、§4.2 规则 1（L112）。

**问题**：

1. 开发机曾因内存耗尽崩溃，但 L0 只有 `nice` / `ionice`。一个"单个测试文件"照样可能拉起大量子进程或吃满内存。例如 `tests/ci/test_imports.py` 会依次启动 12 次 `lint-imports`；以后的 property 测试也可能无界。
2. 规则 1 要求 L1 / L2 串行，但同时开两个会话、或评审方在副本中跑测试时，没有任何互斥。资源预检只能挡住一部分（可用内存在两次检查之间可能同时满足）。

**候选修改**：

08 §4.1：

```diff
-| L0 轻量 | git、文件移动、单个测试文件、小脚本 | `nice -n 19 ionice -c3` |
+| L0 轻量 | git、文件移动、文本查看（不启动 Python 解释器或编译器） | `nice -n 19 ionice -c3` |
+| L0.5 受限脚本 | 单个测试文件、小脚本、`ci.checks` 单项 | `systemd-run --user --scope -p CPUQuota=100% -p MemoryMax=2G -p MemorySwapMax=0 nice -n 19 ionice -c3 <命令>` |
```

08 §4.2 规则 1 追加："L1 / L2 由 `ci/gate.sh` 以 `flock` 独占 `${XDG_RUNTIME_DIR}/codingsystem-heavy.lock`；L2 命令同样先取该锁。"实现见 CI-07。

**副作用**：单文件调试多一层包装；systemd-run 不可用时按 §4.2 规则 3 停止，这一点不变。

**测试**：见 CI-07，即并发启动第二个门禁时立即以退出码 2 失败。

### G08-04 MINOR　§6.4 provisional：缺 Demo 的约束，标注与清单之间没有机械核对，计数在缺少 `rg` 时被静默置 0

**位置**：08 §6.4（L169–172）；`ci/gate.sh` L97–99。

**问题**：

1. 09 §3.1 写明"W3 / W4 若早于所需条目的通过日期，则顺延该能力或按 §4.6 显式缩减 Demo，不以'代码标 provisional'代替三方评审"。08 §6.4 只约束阶段 gate，没有覆盖 Demo（M1）的验收。
2. 代码里的 `PROVISIONAL(子键)`、`provisional.md` 清单、映射表子键三者之间没有核对：子键可以写错，也可以不登记。
3. gate.sh 用 `(rg … || true) | wc -l` 计数，有两个问题：
   - 本机的 `rg` 来自 Codex 安装包（`~/.codex/packages/.../codex-path/rg`），其他会话、内网主机或系统 PATH 下可能没有；
   - `|| true` 同时吞掉了"命令不存在"和"读取出错"（退出码 2）。

   两种情况下，报告都写成 `Provisional annotations: 0`。

**反例**：在没有 `rg` 的环境运行门禁，即使代码中有 5 处 provisional，gate_report 也显示 0，阶段验收会被误导。

**候选修改**：

08 §6.4：

```diff
-- 门禁统计 provisional 数量并写入 `gate_report.txt`；阶段 gate 验收时，该阶段生产或消费的条目不得仍为 provisional（HLD §13、09 §3.1）。
+- 门禁核对 provisional：代码标注的子键必须存在于映射表，且与 `provisional.md` 一一对应，不一致即失败；数量与子键清单写入 `gate_report.txt`。阶段 gate 与 Demo（M1）验收时，该阶段或 Demo 路径生产、消费的条目不得仍为 provisional；Demo 所需条目晚于 W3 / W4 通过时，按 09 §3.1 顺延或按 §4.6 缩减，不以 provisional 代替三方评审。
```

gate.sh 改为：

```diff
-  printf 'Provisional annotations: '
-  # Count code annotations only; the empty register is not itself an implementation.
-  (rg -o 'PROVISIONAL\([^)]*\)' framework agents conformance ci --glob '*.py' || true) | wc -l
+  .venv/bin/python -m ci.checks provisional
```

`ci/checks.py` 增加：

```python
def check_provisional() -> int:
    """Annotations, the register and mapping leaf keys must agree exactly."""
    mapping = Path("docs/dev/01_extension_mapping.md").read_text()
    keys = set(re.findall(r"^\| (B7-[0-9A-Za-z-]+) \|", mapping, re.M))
    register = Path("docs/dev/provisional.md").read_text()
    registered = set(re.findall(r"^\|[^|\n]+\| (B7-[0-9A-Za-z-]+) \|", register, re.M))
    found: dict[str, list[str]] = {}
    for path in repository_files():
        if path.suffix == ".py" and path.parts[0] in {"framework", "agents", "conformance"}:
            for match in re.finditer(r"PROVISIONAL\(([^)]*)\)", path.read_text()):
                found.setdefault(match.group(1), []).append(str(path))
    bad = (set(found) - keys) | (set(found) ^ registered)
    print(f"Provisional annotations: {sum(map(len, found.values()))}; keys: {sorted(found)}")
    for key in sorted(bad):
        print(f"PROVISIONAL_FAIL {key}")
    return int(bool(bad))
```

**副作用**：

- 去掉对 `rg` 的依赖；
- 映射表的父键也会出现在 `keys` 中，但 §6.4 要求标注叶键。可以在 `keys` 中排除批次列为"父键"的行，实现时一并处理。

**测试**：

- 用 monkeypatch 构造三种不一致，各自返回 1：标注子键不在映射表、标注未登记、登记了但没有标注；
- 一致时返回 0；
- 在 PATH 中去掉 `rg` 后，门禁计数仍然正确。

### G08-05 NIT　§7.4 证据等级缺来源字段，§8 缺两项可核对条件

**位置**：08 §7.4（L209）、§8（L215–223）。

**问题**：

1. "真实"一级不区分执行环境（开发机、内网主机、Demo 主机）和执行者（Codex、内网 AI、负责人），也不要求原始记录的位置或摘要。09 §4.5 / §4.6 要求可回放的记录绑定安全切片验收记录的 id，但 §7.4 的字段承接不了这个要求。
2. §8 没有要求两件事：
   - gate_report 取自干净工作树（见 CI-04）；
   - 映射表中该阶段消费的子键都已填写"三方通过日期"。

   HLD §13 P0 要求"任一阶段 gate 验收时其生产或消费的契约条目……必须已经三方评审通过"，而 §8 第 3 项只写了"无 provisional"。

**候选修改**：

```diff
-报告中的每个验收结论标明证据等级：**真实**（真实依赖、真实环境）、**Fake**（Fake 依赖）、**人工**（人工操作得出）、**未验证**。
+报告中的每个验收结论标明证据等级：**真实**（真实依赖、真实环境）、**Fake**（Fake 依赖）、**人工**（人工操作得出）、**未验证**；真实与人工两级另注执行环境、执行者、原始记录位置或摘要，回放记录注明来源验收记录 id（09 §4.5）。
```

§8 第 2 项改为"对应提交上、干净工作树中运行的 `gate_report.txt`（门禁全部通过）"；第 3 项追加"映射表中该阶段生产或消费的子键均已填写三方通过日期"。

**副作用**：报告的字段增加。

**测试**：无代码。阶段评审清单增加这两项核对。

### 08 §9 四项选择的评价

| 项 | 评价 |
|---|---|
| 在 main 上开发 | 合理：单会话串行，评审对象就是已推送的提交。前提是门禁绑定到所测的树（CI-04）；REPORT 写明本任务的提交区间 |
| uv | 合理：锁文件含完整闭包与哈希，task-002 已核对 `uv lock --check`。建议在 gate_report 中打印 `uv --version`，并在 pyproject 中用 `[tool.uv] required-version` 固定，避免 uv 升级改变解析行为（见 CI-08） |
| 暂不用托管 CI | 合理：门禁证据必须绑定资源限制。但应当开启服务端的 secret scanning / push protection，弥补不经门禁的提交（G08-02） |
| 门禁 2 核 3G | 合理：实测当前套件约 2 秒，限额已由 gate.sh 读取 cgroup 文件核对。故障注入与 property 套件落地后按 §4.2 规则 6 分档再评估 |

---

## 3. 01 扩展逐条映射表

**抽取忠实性**：

- 逐条对照 HLD v2.14 附录 B 第 7 组（L981–990）：十组条目数为 6 / 15 / 2 / 2 / 24 / 3 / 2 / 17 / 1 / 3，共 75 条，与原文分号条款一致；
- 原文字词保留，没有发现漏条、合并或改写；
- B7-8 组的"v2.1x 追加"标签照抄在首条上，与原文一致。

**问题集中在两处**：一是子键是否互斥、穷尽，二是"消费映射"与 Demo 自查和 HLD 示例原文对不上。

### MAP-01 MAJOR　四份示例流水线（第一批，P1 gate / Demo 引用）实际消费第二批子键，映射与自查都没有列出

**位置**：

- 映射表 B7-1-6（L20）、B7-1-2 的两个子键（L15–16）、B7-5-2 的子键（L72）、B7-5-7 的子键（L85–86）；
- 消费映射 T11.3-024（L213）、T11.3-025（L214）、T11.3-041-a（L230）、T11.3-049（L239）；
- Demo 六步自查第 4 步（L315）。

**事实**：

- HLD §4.2.1 示例一（`full_pipeline`）中：
  - `benchmark` 节点为 `config: { suites: auto, mode: full, collect_profile: true }`；
  - `optimize` 节点为 `config: { max_opt_rounds: 1 }`；
  - `opt_loop` 注释写明"校验器强制 ≥ 2 × max_opt_rounds"；
  - `bench_gate` 只认 `gate_eligible` 报告；
  - `release_requires: [build_report, image_report, ut_report, bench_report]`。
- 示例二（`optimize_campaign`）：`release_requires` 含 `bench_report`，`max_opt_rounds: 2`，budget 规则为"≥ 1 + max_opt_rounds"。
- 示例四：含 `mode: full` 与 `bench_gate`。
- 示例一、二、四的镜像节点都配置 `backend: local`。HLD §4.2.6 的"后端能力加载期检查"对每个镜像节点读取所选后端的能力声明（source_input、comparison）。对 `release_requires` 中的 bench_report 还要求 comparison 能力。
- HLD §13：
  - P1 的 gate 是"四份示例流水线原文与 §2.4 删除组合加载"；
  - P0 把第一批定义为"Demo 与 P1 / P2 所用条目"。
- 09 v0.4 §3.1：
  - 第一批："BenchReport 谓词随第二批定稿；此前校验器拒绝 release_requires 含 BenchReport 的流水线（fail-closed）"；
  - 第二批：后端能力声明的 schema 与加载期检查规则。

**结论**：在映射表现有的批次下，以下第二批子键是 P1 加载示例一、二、四原文的前提：

| 子键 | 用途 |
|---|---|
| B7-1-2-mock-bench-opt | config.mode、max_opt_rounds 及相应 budget 规则 |
| B7-5-7-bench | BenchReport 通过谓词 |
| B7-5-2-schema | 后端能力声明与加载期检查 |
| B7-5-3-decision-core | gate_eligible |

而映射表的处理是：

- T11.3-025、T11.3-049、T11.3-041-a、T11.3-024 都只列第一批叶键；
- task-002 自查声称"第三批消费违规：0""非第一批消费：0"；
- Demo 第 4 步引用 B7-1-6，却写着"不消费扩展 BenchReport 或第二批其余通过谓词"，自相矛盾。

另外，Demo 第 2 步（可选 mic）的镜像节点同样要经过后端能力加载期检查（需要读取 LocalGbs 的 source_input 声明），但自查只列了第一批键。

**反例**：12-11 第一批按映射表通过后，P1 开发按"只实现已评审的契约"推进：

- 校验器按 09 v0.4 拒绝含 bench_report 的 release_requires，示例一、二加载失败；
- 不认识 `config.mode` / `max_opt_rounds`，示例四因未知字段或 budget 规则未定义而失败；
- P1-G01"四份示例原文加载"无法通过。

开发若为通过 P1 而先实现这些字段，又违反 08 §1 规则 2（只实现已评审契约）。gate 对照表把 P1-G01 的日期写成"2027-01 月末"，没有写出第二批（1-22）这个入口依赖，排期风险因此被隐藏。

**候选修改**：批次改动须由设计审定，此处给出建议方案。

1. 拆出两个第一批的最小子键，其余保持第二批，以符合"Demo 路径一律第一批"：

```diff
-| B7-1-2-mock-bench-opt | 父键原文的字段组：Benchmark config.mode、Optimization max_opt_rounds 的 P4 mock 核心面 | 字段子键 | 第二批；… | P4 mock | …
+| B7-1-2-bench-opt-syntax | 父键原文的字段组：Benchmark config.mode 取值集合与缺省、Optimization max_opt_rounds 字段及"loop budget ≥ 2 × / ≥ 1 + max_opt_rounds"静态规则（只含校验器语法与静态规则，不含判定语义） | 字段子键 | 第一批；待设计审定 | P1 示例加载；Demo 空壳 Benchmark 节点 | …
+| B7-1-2-mock-bench-opt | 父键原文的字段组：config.mode 的判定效力与 max_opt_rounds 的运行时语义（P4 mock 核心面） | 字段子键 | 第二批；… | P4 mock | …
-| B7-5-2-schema | 父键原文的字段组：后端能力声明 schema、加载期检查与锁定 base mock 所需核心字段 | 字段子键 | 第二批；… | P4 mock | …
+| B7-5-2-local-min | 父键原文的字段组：能力声明的最小 schema（source_input / comparison 两项、取值枚举）与 LocalGbsBackend 的声明，以及加载期检查对 local 后端的判定 | 字段子键 | 第一批；待设计审定 | P1 示例加载；Demo mic | …
+| B7-5-2-schema | 父键原文的字段组：其余能力项、Quickbuild 声明与锁定 base mock 所需核心字段 | 字段子键 | 第二批；… | P4 mock | …
```

2. B7-5-7-bench 按 09 v0.4 留在第二批，B7-5-3-decision-core 的 gate_eligible 也一样。因此必须显式写出 P1-G01 对第二批的依赖。拆分如下：

```diff
-| T11.3-025 四份示例原文及加载反例 | P1 | 示例字节、image_report 生产者、汇合必经与 fail_safe | B7-1-6, B7-1-3, B7-1-2-demo-dsl |
+| T11.3-025-a 示例三原文、不含 bench_report 的删除组合与加载反例 | P1 | 示例字节、image_report 生产者、汇合必经、fail_safe、local 后端能力检查 | B7-1-6, B7-1-3, B7-1-2-demo-dsl, B7-5-2-local-min |
+| T11.3-025-b 示例一 / 二 / 四原文加载 | P1（入口：第二批 1-22） | release_requires 含 bench_report、config.mode、max_opt_rounds 与 budget 规则、gate_eligible 阈值 gate、comparison 能力 | B7-1-6, B7-1-2-bench-opt-syntax, B7-5-7-bench, B7-5-3-decision-core, B7-5-2-local-min |
```

T11.3-024、T11.3-041-a、T11.3-049 按同一方式补列消费键。Demo 自查第 2 步补 B7-5-2-local-min，第 4 步补 B7-1-2-bench-opt-syntax，并删去"不消费第二批"的断言，改为如实列出。

3. gate 对照表 P1-G01 的计划日期改为"2027-01 月末（§5.2）；入口条件：第一批 12-11 + 第二批中 B7-5-7-bench、B7-5-3-decision-core（1-22）"。同时在 STATUS §7 登记一条设计问题："HLD §13 P0'第一批——Demo 与 P1 / P2 所用条目'与 09 v0.4'BenchReport 谓词随第二批'对 P1-G01 的含义需设计裁定（勘误 HLD 措辞，或把这两项提前到第一批）"。

**副作用**：

- 第一批增加两个很小的子键，均为校验器语法与静态规则；
- P1 gate 的入口改为依赖第二批：第二批延误会直接推迟 P1 gate；
- 09 §5.2 已把 P1 gate 放在 1 月末，晚于 1-22，排期可行，但余量只有约一周。

**测试**：

- 映射一致性脚本（建议随 CI-07 一并加入 `ci.checks mapping`）：解析四份示例原文的 DSL 字段，按"字段 → 子键"表反查批次，断言 P1 类别的消费列包含全部反查结果；
- P1 测试：第二批通过前，示例一加载应以"release_requires 含 BenchReport（fail-closed）"的类型化错误被拒；第二批通过后加载成功。

### MAP-02 MINOR　部分父键的子键不穷尽或不互斥

**位置**：B7-1-2（L14–16）、B7-4-1 / B7-4-2（L56–62）、B7-5-3（L74–76）、B7-5-16（L106）。

**问题与反例**：

1. **B7-1-2**：父键原文里有三项没有落到任何子键：
   - "§4.2.6 三条规则的形式化"的非 Demo 部分，即规则③的优化重验证；而 HLD §13 P1 明确包含"优化重验证三条规则"；
   - "V-13b/V-15 维持普通支配"；
   - config.mode / max_opt_rounds 的非 mock 面。

   demo-dsl 子键只写"三条规则的 Demo 面"，规则③在 Demo 中根本不出现。
2. **B7-4-1**：父键原文中有三项没有分配：
   - "ProbeOutcome 增 `deferred`"；
   - `backend_source_input_unsupported`；
   - "`base_mismatch` → `image_failed_exhausted`"。

   另有两处与 B7-4-2 重叠：
   - B7-4-1-image-demo 含"ImageRecord 最小字段"，与 B7-4-2-demo-record 重叠；
   - B7-4-1-image-profile-probe 含"ImageRecord 其余核心字段"，与 B7-4-2-record-rest 重叠。

   同一字段属于两个叶键，不符合"每个子键恰属一批"所隐含的互斥要求。
3. **B7-5-3**：decision-core 写"…comparison 等 mock 判定骨架；精确字段集合待设计确认"，measurement 写"与核心字段分界待确认"。用"等"和"待确认"划分，在定义上就做不到穷尽与互斥，却被标为"设计审定 2026-11-11"。comparison 与 B7-5-16 也重叠。

**候选修改**：

```diff
+| B7-1-2-rules-rest | 父键原文：§4.2.6 规则③（优化重验证）形式化、规则①对 bench_report 的适用、V-13b/V-15 维持普通支配 | 字段子键 | 第一批 | P1（HLD §13 P1 三条规则） | …
-| B7-4-1-image-demo | 父键原文的字段组：image.* 中可选 mic 最小入库与引用契约、ImageRecord 最小字段 | …
+| B7-4-1-image-demo | 父键原文的字段组：image.* 中可选 mic 最小入库与引用契约（ImageRecord 字段见 B7-4-2） | …
-| B7-4-1-image-profile-probe | 父键原文的字段组：image.* / profile.* probe 与 ImageRecord 其余核心字段 | …
+| B7-4-1-image-profile-probe | 父键原文的字段组：image.* / profile.* probe、镜像 probe 按 idem_key 查索引 | …
+| B7-4-1-deferred | 父键原文：ProbeOutcome 增 deferred（枚举值与"作为挂起输入"的通用语义） | 字段子键 | 第一批 | P1（T11.3-052） | …
+| B7-4-1-image-failure | 父键原文：backend_source_input_unsupported、base_mismatch → image_failed_exhausted | 字段子键 | 第二批 | P4 | …
-| B7-5-3-decision-core | 父键原文字段组：mode、gate_eligible、validation_complete、opt_verdict、comparison 等 mock 判定骨架；精确字段集合待设计确认 | …
+| B7-5-3-decision-core | 父键原文字段组：mode、gate_eligible、validation_complete、opt_verdict（comparison 三值与 comparison_unverifiable 原因见 B7-5-16） | …
-| B7-5-3-measurement | 父键原文字段组：逐指标四值与区间、spec_inconclusive_count、opt_gain_pct、baseline_revoked/baseline_unavailable 的业务面；与核心字段分界待确认 | …
+| B7-5-3-measurement | 父键原文字段组：逐指标四值与区间、spec_inconclusive_count、opt_gain_pct、baseline_revoked、baseline_unavailable | …
```

B7-1-2-bench-opt-syntax 见 MAP-01。

**副作用**：

- 叶键增加 4 个；
- `deferred` 进入第一批：它与外部等待（E-02，第一批）的挂起语义本来就在一起；
- 远程构建的具体 probe 仍在第三批。

**测试**：映射一致性脚本增加断言：

- 每个父键原文按分号或顿号切出的每个字段名，恰好出现在一个子键中；
- 子键之间的字段名交集为空。

### MAP-03 MINOR　消费映射中还有三处漏列或依赖批次存疑

**位置**：T11.3-052（L243）、T11.3-053（L244）、T11.3-029（L219）、Demo 自查第 2 步（L313）。

**问题**：

1. **T11.3-052**（P1）的判定字段写着"deferred 作为挂起输入"，但消费列没有任何含 `deferred` 的键。`deferred` 目前只在 B7-4-1 父键原文中出现（见 MAP-02）。
2. **T11.3-053**（P2，远程配额恰一次归还）的判定字段含"版本回报"。远程构建效应标记"idem_key 指纹 + version"在 B7-4-1-remote-build（第三批）中，而 P2 消费第三批违反 09 §3.1。如果 P2 只断言配额账而不断言效应版本，应在判定字段中写明。
3. **T11.3-029**（P1，rpm_precheck 加载）加载镜像节点时同样触发后端能力检查，应补 B7-5-2-local-min（MAP-01）。

另外，Demo 第 2 步自查漏列 B7-3-1（mic 的 `image_commit` 命令）与 B7-2-5（分派前资源授予）。两者都在第一批，不违反规则，但自查声称"全部扩展叶键"。

**候选修改**：

```diff
-| T11.3-052 外部等待会话/ACK/挂起补充 | P1 | … | B7-2-1, B7-2-3, B7-2-6 |
+| T11.3-052 外部等待会话/ACK/挂起补充 | P1 | … | B7-2-1, B7-2-3, B7-2-6, B7-4-1-deferred |
-| T11.3-053 远程配额恰一次归还（Fake 远端） | P2 | cancel_pending、版本回报与配额账；远端真实提交留 P6 | B7-2-1, B7-3-1 |
+| T11.3-053 远程配额恰一次归还（Fake 远端） | P2 | cancel_pending 与配额账；Fake 远端只回报终态，不断言远程效应标记 version（version 语义随 B7-4-1-remote-build 于 P6 断言） | B7-2-1, B7-3-1 |
-| T11.3-029 rpm_precheck 加载与运行 | P1 | … | B7-1-2-demo-dsl, B7-5-1-image-schema |
+| T11.3-029 rpm_precheck 加载与运行 | P1 | … | B7-1-2-demo-dsl, B7-5-1-image-schema, B7-5-2-local-min |
```

Demo 第 2 步补 B7-3-1、B7-2-5。T11.3-053 也可以不缩小断言，改为把"效应标记 = idem_key 指纹 + version"单拆为第一批子键，由设计二选一。

**副作用**：T11.3-053 若缩小断言，P2 不再验证远程版本回报，这部分推迟到 P6，应在 gate 对照表的 P6 行补一条。

**测试**：映射一致性脚本把每行"判定读写的字段 / 命令"中出现的已知字段名（从附录 B 原文抽取的词表）反查到子键，断言消费列包含这些子键。

### MAP-04 MINOR　表头缺 09 要求的"负责人"与"schema / 命令 / 迁移 / CF 用例"列

**位置**：映射表各组表头（如 L11）；09 §3 M0a 行与 §3.1"逐条映射"段。

**问题**：

- 09 §3 M0a 的完成条件包含"01 扩展三批的条目清单与**负责人**确定"；
- 09 §3.1 要求映射表"列出 schema / 命令 / 迁移 / CF 用例"。

现在的表只有"类型"一列（schema/字段、命令/接口等分类），没有负责人列，也没有指向 01 落点或 CF 编号的列。M0a 时这一项因此无法核对。STATUS §7 挂账的是"gate 条目的个人负责人"，不包含映射条目。

**候选修改**：各组表头改为：

```diff
-| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 三方通过日期 | 实现日期 | 阶段验收日期 |
+| 编号 | 原文（逐条保留） | 类型 | 批次 | 最早使用方 | 负责人（起草 / 实现） | 01 落点（章节 / 模型 / 命令 / 迁移 / CF 编号；起草时填） | 三方通过日期 | 实现日期 | 阶段验收日期 |
```

负责人按 09 §2 原则 7 的角色填写：起草为设计与评审主持，实现为开发。如需落实到个人，并入 STATUS §7 已有的挂账，不另立。

**副作用**：表格加宽；第一批起草时逐行回填 01 落点。

**测试**：映射一致性脚本断言第一批的每个叶键在 12-11 前都已填写"01 落点"。

---

## 4. gate 对照表（P0–P2）

**完整性**：

- P0–P2 行与 HLD §13 原文逐项对应，交付件与 gate 分行，没有遗漏；
- Demo 安全切片 DEMO-S01..S06 与 09 §4.2 原文一致；
- 09 §10 点名的三项（TRACK-04..06）都已列出。

问题在日期精度，以及部署类 D23 待办与阶段入口条件这两处漏列。

### GM-01 MINOR　P0 两行与 Demo 安全切片的日期与 09 不一致或过粗

**位置**：P0-D03（L11）、P0-G01（L12）、DEMO-S01..S06（L34–39）。

**问题与反例**：

1. **P0-D03"08/09 就绪"**：表中写 12-31。09 §3 M0a（11-20）要求"08 开发指南 v1……本计划经评审"，08 自身的状态行也写"计划 2026-11-20 M0a 前通过"。按现在的表，08 晚到 12 月也不算超期。
2. **P0-G01"总部方案确认"**：表中写"12-31（第一批通过 12-11）"。09 §3 写明"总部方案确认随 12 月 Demo 进行"，09 §4.4 W8 的日期为 12-29，备选 12-30。
3. **DEMO-S01..S06**：统一写成"W3–W4，Demo 12-29"。09 §4.4 的实际顺序是：
   - 构建隔离在 W3 验收（11-27 检查点）；
   - LLM 安全切片在 W4 首次内网联调之前完成；
   - W3 已在内网主机落地 ClineSR CLI 专用用户与 launcher 拉起方式，这意味着产品进程首次部署到该主机。

   D23 deploy 验收（S01）必须早于这次部署。按 09 §4.6，11-27 检查点的第四行就是 D23 deploy 验收。写成"W3–W4"会让 S01 显得可以晚于 W3 的部署。

**候选修改**：

```diff
-| P0-D03 | HLD §13:893 | 08/09 就绪 | … | 2026-12-31（§3 M0b；第一批通过 12-11） | | 待交付/验收 |
+| P0-D03 | HLD §13:893 | 08/09 就绪 | … | 2026-11-20（09 §3 M0a：08 v1、09 经评审） | | 待交付/验收 |
-| P0-G01 | HLD §13:893 | 总部方案确认 | … | 2026-12-31（§3 M0b；第一批通过 12-11） | | 待交付/验收 |
+| P0-G01 | HLD §13:893 | 总部方案确认 | … | 2026-12-29，备选 12-30（09 §3、§4.4 W8，随 Demo） | | 待交付/验收 |
-| DEMO-S01 | … | 首次使用前；§4.4 W3–W4，Demo 12-29 | …
+| DEMO-S01 | … | 产品进程首次部署到内网主机之前（W3 内 launcher / CLI 专用用户落地前，≤ 2026-11-27；09 §4.6 11-27 检查点第四行） | …
-| DEMO-S02 | … | 首次使用前；§4.4 W3–W4，Demo 12-29 | …
+| DEMO-S02 | … | 首次真实构建前，≤ 2026-11-27（09 §4.4 W3"构建隔离方案落地并验收"） | …
```

DEMO-S03..S06 改为"W4 首次内网 LLM 联调前（≤ 2026-12-04；09 §4.4 W4）"。

**副作用**：无。只是把 09 已有的日期落到条目上，便于周跟踪按 09 §10 计算偏差。

**测试**：无代码。周跟踪时逐行比对。

### GM-02 MINOR　"task-001 明确不实现的 D23 项"漏列 v2.12–v2.14 的部署检查，P1 / P2 行缺契约入口条件

**位置**：gate 对照表 L49–60；P1、P2 各行（L14–33）。

**问题**：

1. D23-PENDING-01..08 漏了 HLD §11.2 与附录 B 第 7 组中以下部署侧检查：
   - **v2.14**：最低有效策略版本与例外撤销清单在 Run 创建时的读取与校验，含 revocation_max_age（B7-8-4）；对应 §11.3 断言"部署停在策略版本 N、发布源把例外 E 列入撤销清单 → 下一次 Run 创建被拒"；
   - Run 创建时的例外复核与"现行版本"绑定（B7-8-10）；
   - 扫描策略版本升级后全部注册记录与主机安装集的重扫；
   - 独立构建主机按同一口径扫描，运维机登录助手及其闭包的扫描；
   - 构建 VM 内由本产品下发的辅助程序按同一口径约束。

   这些检查同样在"首次部署 / 使用前"生效，漏列后周跟踪无从反查。
2. HLD §13 P0 写明"任一阶段 gate 验收时，其生产或消费的契约条目……必须已经三方评审通过"，但 P1 / P2 行没有任何一列指向映射表的子键或批次。MAP-01 所述 P1-G01 依赖第二批的情况，在本表中看不出来。

**候选修改**：

```diff
+| D23-PENDING-09 | HLD §11.2 v2.14；附录 B7（B7-8-4） | 最低有效策略版本与例外撤销清单：发布格式、读取、缓存时限 revocation_max_age，Run 创建前校验 | 开发 / 部署负责人 | 首次部署 / 使用前（09 §4.2） | | 待实现；本任务不验收 |
+| D23-PENDING-10 | HLD §11.2；B7-8-10、B7-8-12 | Run 创建时例外复核与"现行版本"绑定 | 同上 | 同上 | | 待实现 |
+| D23-PENDING-11 | HLD §11.2"例外与复核" | 策略版本升级后注册记录与主机安装集全量重扫 | 同上 | 同上 | | 待实现 |
+| D23-PENDING-12 | HLD §11.2"扫描对象" | 独立构建主机（D22）与运维机登录助手闭包扫描；构建 VM 内本产品辅助程序同口径约束 | 同上 | 首次使用独立构建主机 / 登录助手前 | | 待实现 |
```

P0–P2 表增加一列"契约入口（映射子键 / 批次）"，每行填写所消费的子键或"第一批"。P1-G01 按 MAP-01 填写"第一批 + B7-5-7-bench、B7-5-3-decision-core（第二批 1-22）"。

**副作用**：表格增加一列与 4 行；后续 P3–P7 部分沿用同一列。

**测试**：映射一致性脚本断言 gate 对照表每个 P1–P4 行的"契约入口"子键都存在于映射表中，且批次不晚于该阶段的入口批次。

---

## 5. 门禁代码

**正面确认**：

- **资源限额**：gate.sh 的内层读取 `/proc/self/cgroup` 定位到的 `memory.max`、`memory.swap.max`、`cpu.max`，并强制核对，不信任 `--in-scope` 参数。直接以 `--in-scope` 在无限制会话中运行时，`memory.max` 为 `max`，门禁会失败。
- **失败传递**：`set -Eeuo pipefail`，各检查函数内部显式 `|| return $?`，任一项失败都能导致整体失败，并写出 `ALL-END … status=fail`。
- **历史报告保护**：通过 `git ls-files --error-unmatch` 拒绝覆盖已跟踪的报告；`test_gate_entry` 用真实脚本验证了这一点。
- **import-linter 的六条合约**：每条都由真实 CLI、正负夹具验证；负向夹具在运行时写入临时目录。
- **D23 负向夹具**：都在运行时拼接，源码中没有起始标记字面量。
- **测试运行**：51 passed、1 skipped，与 task-002 报告一致。

### CI-01 MAJOR　文本信号判定可被大小写变体与有状态编码绕过

**位置**：`ci/d23.py` L12（`MARKER`）、L30–40（`python_fragments` 按声明编码解码后，以 `source.encode("utf-8")` 代替原始字节作最终覆盖检查）、L74、L112（`marker_present` 为区分大小写的字节匹配）、L118、L133。

**实测**（临时副本、受限 scope 内，输入均在运行时拼接）：

| 输入 | 原始字节含小写起始标记 | `check_file` 结果 |
|---|---|---|
| `.txt`：起始标记全大写，后接 `echo 1; ?>` | 否（大写） | `[]`，通过 |
| `.html` 模板：起始标记大小写混合，后接 `system('id'); ?>` | 否 | `[]`，通过 |
| `.py`：字符串常量内为大小写混合的起始标记加 `echo 1;` | 否 | `[]`，通过 |
| `.py`：首行声明 `coding: hz`，字符串内 `~{` + 起始标记 + `A~}` | **是** | `[]`，通过（且 `compile()` 成功） |
| `.py`：首行声明 `coding: iso2022_jp`，字符串内 ESC `$B` + 起始标记 + `A` + ESC `(B` | **是** | `[]`，通过（且 `compile()` 成功） |

**原因**：

- PHP 的起始标记不区分大小写。HLD §11.2 的判定信号是"含 PHP 起始标记的文件"，§11.3 要求"伪装为 `.py` 的 PHP 源 → 拒绝"。把起始标记写成大写的 PHP 源改名为 `.py` 后，`ast.parse` 失败，`python_fragments` 返回 False；但 `marker_present` 与 `decoded_marker` 都按小写匹配，结果是不报任何原因。
- 有状态编码（HZ、ISO-2022）把 ASCII 区间的字节对解码成汉字。原始字节里有起始标记，解码后的源码里却没有。`python_fragments` 最后比对的是 `source.encode("utf-8")`，不是原始 `data`，因此判定"全部命中都已批准"。HLD 的判据针对的是文件本身。

**候选修改**（`ci/d23.py`）：

```diff
 MARKER = …  # unchanged
+MARKER_RE = re.compile(re.escape(MARKER.encode()), re.IGNORECASE)
+UTF8_CODECS = {"utf-8", "utf-8-sig"}
+
+
+def raw_marker(data: bytes) -> bool:
+    """PHP open tags are case-insensitive; always judge the file's own bytes."""
+    return MARKER_RE.search(data) is not None
@@ def python_fragments(data: bytes) -> bool:
         encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
+        if codecs.lookup(encoding).name not in UTF8_CODECS:
+            return False  # Byte offsets below are defined only for UTF-8 sources.
         source = data.decode(encoding)
@@
-    raw = source.encode("utf-8")
+    raw = data.removeprefix(codecs.BOM_UTF8)
@@
-        if MARKER not in value:
+        if MARKER.lower() not in value.lower():
             continue
@@
-        if token.type != tokenize.COMMENT or MARKER not in token.string:
+        if token.type != tokenize.COMMENT or MARKER.lower() not in token.string.lower():
             continue
@@
-        for match in re.finditer(re.escape(MARKER.encode()), raw)
+        for match in MARKER_RE.finditer(raw)
@@ def check_file(…):
-    marker_present = MARKER.encode() in data
+    marker_present = raw_marker(data)
@@ def decoded_marker(data: bytes) -> bool:
-            if isinstance(value, str) and MARKER in value:
+            if isinstance(value, str) and MARKER.lower() in value.lower():
```

还有两点要同步：

- 在 import 处加入 `codecs`；
- 精确相等的豁免判定 `value not in SIGNALS` 保持区分大小写。大小写变体的常量因此一律不豁免，比原来更严。

**副作用**：

- **误报面**：在临时副本中实测，全部已跟踪文件与 `.venv` 的 2599 个文件中，大小写不同的起始标记变体为 0 处，因此不会新增误报；
- **非 UTF-8 编码**：声明非 UTF-8 编码、且含起始标记的 Python 源将一律失败，当前仓库没有这种文件；
- **重新登记**：`ci/d23.py` 的摘要变化，需要同步 `d23_scanner_digests.json`，并升级策略版本号。

**测试**（追加到 `tests/ci/test_d23.py`，全部在运行时拼接）：

```python
@pytest.mark.unit
@pytest.mark.parametrize("variant", [str.upper, str.title, lambda s: s[:2] + s[2:].upper()])
@pytest.mark.parametrize("name", ["x.txt", "x.html", "x.py"])
def test_case_variants_are_signals(variant, name, tmp_path: Path) -> None:
    path = tmp_path / name
    path.write_text(variant(marker()) + " echo 1; ?>")
    assert check_file(path)


@pytest.mark.unit
@pytest.mark.parametrize(
    "data",
    [
        b"# -*- coding: hz -*-\nx = '~{" + marker().encode() + b"A~}'\n",
        b"# -*- coding: iso2022_jp -*-\nx = '\x1b$B" + marker().encode() + b"A\x1b(B'\n",
    ],
)
def test_stateful_encodings_cannot_hide_raw_marker(data: bytes, tmp_path: Path) -> None:
    path = tmp_path / "enc.py"
    path.write_bytes(data)
    assert "unapproved_python_fragment" in check_file(path)


@pytest.mark.unit
def test_utf8_sig_signature_constant_still_approved() -> None:
    assert python_fragments(b"\xef\xbb\xbfx = " + repr(marker()).encode())
```

### CI-02 MINOR　扫描器摘要在仓库扫描中整体豁免 `.py`，与 HLD"仓库扫描按片段分类"不符，测试断言了错误行为

**位置**：`ci/d23.py` L128–129；`tests/ci/test_d23.py` L119（`test_unregistered_language_and_no_whole_python_exemption`）。

**问题**：

- HLD §11.2："**适用范围**：仓库扫描按上述规则分类；镜像与主机扫描只对扫描器自身的规则表与源码按其**文件 digest**……免除。"也就是说，仓库中的扫描器 Python 源应按片段判据判定。HLD §11.3 v2.12 的断言为"扫描器源码中与签名表完全相等的常量 → 通过"。
- 现实现中，只要文件摘要登记在 `d23_scanner_digests.json` 中，就删去 `unapproved_python_fragment`。登记文件里即使有一个以单个字符串常量承载的完整 PHP 程序也会通过。
- 测试 L117–119 恰恰断言了这一点（`assert not check_file(path, scanner_digest=...)`），与测试名"no whole python exemption"相反。

**反例**：在 `ci/d23.py` 中加入 `HELP = MARKER + " system($_GET[1]);"` 的字面量拼合版本，即单个常量，再更新摘要表。仓库扫描通过，而 HLD 要求失败。

**候选修改**：

```diff
-    # A reviewed scanner source can exempt text, but never names, shebang or metadata.
-    if scanner_digest == digest(data):
-        reasons = [reason for reason in reasons if reason != "unapproved_python_fragment"]
+    # Repository scans classify scanner Python by fragments (HLD §11.2); the reviewed
+    # file digest exempts only non-Python rule tables here, and images/hosts elsewhere.
     return reasons
```

`tests/ci/test_d23.py` L119 改为：

```diff
-    assert not check_file(path, scanner_digest=digest(path.read_bytes()))
+    assert "unapproved_python_fragment" in check_file(path, scanner_digest=digest(path.read_bytes()))
```

**副作用**：

- 现有 `ci/d23.py` 中只有与签名完全相等的常量，按片段判据本来就通过，门禁结果不变；
- 非 Python 的 `ci/d23_policy.json` 仍按摘要豁免。

**测试**：

- 上述修改后的断言；
- 新增正例：内容为 `MARKER` 单常量的 `.py`，在不登记摘要的情况下也通过。

### CI-03 MINOR　已安装依赖的扫描只遍历 RECORD 清单，门禁自身会生成不受扫描的运行时 pyc

**位置**：`ci/checks.py` L128–143；`ci/gate.sh` L15–23、L62。

**问题**：

1. `check_d23` 只扫描 `distribution.files`，即 RECORD 列出的文件。HLD §11.2 要求扫描"实际安装集与文件（不以……顶层清单代替）"，§11.3 的断言是"存在运行时生成的 pyc → 失败"。
2. `verify_python`（L17）在 `export PYTHONDONTWRITEBYTECODE=1`（L62）**之前**运行 `.venv/bin/python`。解释器启动时处理 `.pth`，会导入 `_virtualenv`、`_distutils_hack` 和可编辑安装的 finder，并写出 pyc。

**实测**：在临时副本中统计主仓 `.venv`，不属于任何 RECORD 的文件有 18 个，其中 3 个是 `site-packages/__pycache__/` 和 `_distutils_hack/__pycache__/` 下的 `.pyc`。它们的修改时间为 2026-11-11 21:51，与 task-002 门禁运行时段吻合。这些 pyc 从未被扫描，门禁照样通过。往 site-packages 放一个不在 RECORD 中的文件，同样不受扫描。

**候选修改**：

gate.sh 把环境变量提到最前：

```diff
 cd "$(dirname "${BASH_SOURCE[0]}")/.."
+export PYTHONDONTWRITEBYTECODE=1
```

`ci/checks.py`：

```diff
+    owned: set[Path] = set()
     for distribution in metadata.distributions():
@@
         for relative in distribution.files:
             path = Path(str(distribution.locate_file(relative)))
+            owned.add(path.resolve())
@@
+    prefix = Path(sys.prefix)
+    for path in sorted(prefix.rglob("*")):
+        if path.is_symlink():
+            target = path.resolve()
+            if target.is_relative_to(prefix.resolve()) or (
+                path.parent == prefix / "bin" and path.name.startswith("python")
+            ):
+                continue  # lib64 -> lib, and interpreter links checked against pyvenv.cfg home
+        elif path.is_dir():
+            continue
+        if path.resolve() in owned:
+            continue
+        if path.suffix == ".pyc":
+            failures.append(f"installed: {path.relative_to(prefix)}: runtime_pyc_unlisted")
+            continue
+        for reason in check_file(path):
+            failures.append(f"installed: {path.relative_to(prefix)}: {reason}")
```

**副作用**：

- 修复后第一次运行门禁，会因为现存的 3 个 pyc 而失败。这是期望的结果：开发应重建 `.venv`（`uv sync --reinstall`），不应在门禁中自动删除 pyc 来掩盖问题；
- venv 的激活脚本等非 RECORD 文本文件也会进入文本信号扫描，目前这类文件中没有命中。

**测试**：

- 在临时目录伪造 `sys.prefix`（含 `lib64 -> lib` 链接），放入一个不属于 RECORD 的 `.pyc`，断言 `runtime_pyc_unlisted`，且 `lib64` 链接本身不报；
- 放入一个含运行时拼接起始标记的非 RECORD 文本文件，断言 `unclassified_text_signal`；
- 解释器链接被跳过。

### CI-04 MINOR　门禁结果不绑定所测的工作树

**位置**：`ci/gate.sh` L64（只打印 HEAD）；task-001、task-002 REPORT 的末段。

**问题**：

- 门禁允许在有未提交修改的工作树上运行，报告只记录 `git rev-parse HEAD`，不记录 `git status`、diff 摘要或任务号；
- 两份 REPORT 都写明"最终门禁在该 HEAD 上运行，并扫描待提交的 STATUS 与交付文本"，可见这已是常规做法。

这样，任何未提交的代码改动都可能出现在测试中，却不在所引用的提交里，反过来也一样。08 §5.2 说"阶段 gate 证据引用该文件及其所在提交"，但该提交并不能证明被测内容。

**反例**：工作区中暂时把某个关键函数改成恒真，运行门禁得到 PASS，再 `git checkout` 恢复后提交。gate_report 记录的 HEAD 与 PASS 都"真实"，但被测代码从未进入历史。

**候选修改**：

```diff
+require_clean_tree() {
+  local dirty
+  dirty=$(git status --porcelain=v1 --untracked-files=all -- . \
+    ':(exclude)docs/dev/STATUS.md' ":(exclude)docs/dev/deliver/${task_id}") || return $?
+  if [[ -n "$dirty" ]]; then
+    printf 'Working tree differs from HEAD outside task records:\n%s\n' "$dirty" >&2
+    return 1
+  fi
+}
+require_clean_tree
 if [[ "${2:-}" != "--in-scope" ]]; then
@@
-printf 'HEAD: %s\nTime: %s\n' "$(git rev-parse HEAD)" "$(date -u +%FT%TZ)"
+require_clean_tree
+printf 'Task: %s\nHEAD: %s\nTree: %s\nTime: %s\n' "$task_id" "$(git rev-parse HEAD)" \
+  "$(git rev-parse 'HEAD^{tree}')" "$(date -u +%FT%TZ)"
```

**副作用**：

- 开发必须先提交实现，再跑门禁；STATUS 与本任务交付目录可以保持未提交，这符合 08 §7.1 中"收尾提交只保存记录"的流程；
- 其他评审方或设计方留在工作区的未提交文件（例如本轮另一家评审的草稿）也会让门禁失败。这是正确的，但要求在干净的克隆或 worktree 中运行门禁。

**测试**：在临时 git 仓库中复制 gate.sh，并放一个伪造的 `.venv/bin/python`（输出 3.12）：

- 修改一个已跟踪文件后运行，期望退出码 1、输出 "Working tree differs"，且尚未进入资源预检；
- 只修改 `docs/dev/STATUS.md` 时，不因工作树失败。

### CI-05 MINOR　内容边界规则的漏报

**位置**：`ci/content_policy.json`。

**实测**：以下 11 个样本在运行时拼接后，现有规则全部 0 命中。

| 规则 | 漏报的样本 |
|---|---|
| token | OpenAI 项目密钥（`sk-` + `proj-` 前缀）、Anthropic 密钥（`sk-` + `ant-` 前缀；因为前缀后紧跟连字符，`sk-[a-z0-9]{32,}` 不匹配）、Slack `xox?-` 令牌、GitLab `glpat-` 令牌 |
| credential-assignment | YAML 中不带引号的口令赋值；`client_secret` 等关键字（不在关键字表中） |
| private-ipv4 | 私网地址后紧跟英文句点，例如句末。原因是否定前瞻 `(?![\w.])` 排除了 `.` |
| perforce-path | 除 `SHARED` / `depot` 之外的任何 depot 名；大小写不同的 `Depot` |
| private-key | `ENCRYPTED PRIVATE KEY`、`PGP PRIVATE KEY BLOCK` |

本项目会调用 LLM 服务，前两类令牌恰好最容易误入仓库。

**候选修改**：

```diff
-    "private-key": "-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
+    "private-key": "-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----",
-    "token": "(?i)(?:gh[pousr]_[a-z0-9]{30,}|github_pat_[a-z0-9_]{40,}|AKIA[A-Z0-9]{16}|sk-[a-z0-9]{32,})",
+    "token": "(?i)(?:gh[pousr]_[a-z0-9]{30,}|github_pat_[a-z0-9_]{40,}|AKIA[A-Z0-9]{16}|sk-(?:proj-|ant-[a-z0-9]+-)?[a-z0-9_-]{32,}|xox[abprs]-[a-z0-9-]{10,}|glpat-[a-z0-9_-]{20,}|AIza[0-9a-z_-]{35})",
-    "credential-assignment": "(?i)(?:password|passwd|api_key|access_token|authorization|cookie)\\s*[:=]\\s*[\"'](?!<|\\$\\{|example|placeholder|redacted)[a-z0-9/+=_.-]{20,}[\"']",
+    "credential-assignment": "(?i)\\b(?:password|passwd|pwd|secret|client_secret|api[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?token|authorization|cookie)\\s*[:=]\\s*[\"']?(?!<|\\$\\{|example|placeholder|redacted)[A-Za-z0-9/+=_.\\-@!#%^&*]{16,}",
-    "private-ipv4": "…(?![\\w.])",
+    "private-ipv4": "…(?!\\w|\\.\\d)",
-    "perforce-path": "(?<![:/])//(?:SHARED|depot|[A-Za-z0-9_-]+/\\[[^\\]\\n]+\\])/"
+    "perforce-path": "(?<![:/\\w])//[A-Za-z][A-Za-z0-9_-]*/[^\\s/]+/"
```

`version` 升为 `task-00N-content-v2`，`content_exemptions.json` 的 `version` 同步升级。

**副作用**：

- 在临时副本中把新规则跑在全部已跟踪文件上，5 条规则的命中数相对旧规则**均无变化**，因此不需要新增豁免；
- 正例核对：
  - 上述样本全部命中；
  - `10.1.2.3.4` 形式的版本号串仍然不命中；
  - 以 `https:` 开头的 URL 不命中（负向前瞻排除冒号后的双斜线）。
- 新的 perforce 规则对协议相对 URL（以 `//` 开头）会命中，如果以后需要，按豁免表逐条登记。

**测试**：在 `test_real_content_signals` 中加入上述样本（运行时拼接），并加入两条负例：版本号串和 https URL。

### CI-06 MINOR　import-linter 合约逐个列举模块，新子包或新 Agent 包会静默逃出边界

**位置**：`.importlinter` 的 `engine`、`framework`、`agent`、`worker`、`contracts` 五条合约；`tests/ci/test_imports.py`。

**问题**：

1. `engine` 合约的 `source_modules` 逐个列出 15 个子包，`contracts` 的 `forbidden_modules` 也逐个列出。新增 `codingsystem.web` 之类的子包时，如果忘记同步，新子包就可以直接 import `langgraph`。
2. `framework`、`agent`、`worker` 三条合约只写了 `codingsystem_agent_skeletons`，`root_packages` 也只有它。08 §3.2 规定"每个业务 Agent 是独立分发包"，P5 新增 `codingsystem_agent_compiler` 时，"Agent 只 import sdk / contracts""worker 不得触达 approval / release"对它完全不生效。
3. `test_imports.py` 只证明现有列表有效，不检查列表是否完整。

**候选修改**：

`engine` 合约改为默认封闭：

```diff
 [importlinter:contract:engine]
 name = Only engine imports LangGraph
 type = forbidden
 source_modules =
-    codingsystem.orchestration
-    …（15 行）
+    codingsystem
     codingsystem_agent_skeletons
 forbidden_modules = langgraph
+ignore_imports =
+    codingsystem.engine -> langgraph
+    codingsystem.engine.** -> langgraph
 allow_indirect_imports = True
```

`root-engine` 合约随之可以删除。另在 `tests/ci/test_imports.py` 增加完整性断言：

```python
@pytest.mark.unit
def test_contract_lists_are_complete() -> None:
    config = configparser.ConfigParser()
    config.read(ROOT / ".importlinter")
    subpackages = {p.name for p in (ROOT / "framework").iterdir() if (p / "__init__.py").is_file()}
    agents = {p.name for d in (ROOT / "agents").glob("*/src") for p in d.iterdir() if (p / "__init__.py").is_file()}
    roots = set(config["importlinter"]["root_packages"].split())
    assert agents <= roots
    for name in ("framework", "agent", "worker"):
        section = config[f"importlinter:contract:{name}"]
        listed = set((section.get("source_modules", "") + " " + section.get("forbidden_modules", "")).split())
        assert agents <= listed, name
    forbidden = set(config["importlinter:contract:contracts"]["forbidden_modules"].split())
    assert forbidden == {f"codingsystem.{n}" for n in subpackages - {"contracts"}}
```

**副作用**：

- 新增 Agent 包时必须同时更新三条合约；
- 测试会提醒，不会静默漏检。

**测试**：

- 上面的完整性测试；
- 已有的负向夹具改为对新的 `engine` 合约验证 `codingsystem.orchestration` 与 `codingsystem` 根模块各自 import `langgraph` 时被拒。

### CI-07 MINOR　门禁可在没有资源预检的情况下运行，也没有串行互斥

**位置**：`ci/gate.sh` L24–45。

**问题**：

1. `--in-scope` 只核对 cgroup 限额，不核对预检是否真的执行过。在任何与门禁限额相同的 scope 中直接调用 `ci/gate.sh task-NNN --in-scope`，就会跳过"可用内存 ≥ 4096 MiB、负载 ≤ 核数一半"的预检。
2. 外层预检的 `free -m` 与 `/proc/loadavg` 只打印到终端，不写入报告，所以报告无法证明开跑时满足了 08 §4.2 规则 2。
3. 没有任何互斥（08 §4.2 规则 1）。

**候选修改**：

```diff
 if [[ "${2:-}" != "--in-scope" ]]; then
+  exec 9>"${XDG_RUNTIME_DIR:-/tmp}/codingsystem-heavy.lock"
+  flock -n 9 || { printf 'Another L1/L2 job holds the lock\n' >&2; exit 2; }
   start=$SECONDS
@@
   mkdir -p "$(dirname "$report")"
-  : > "$report"
+  printf 'PREFLIGHT ok available=%s load=%s cores=%s waited=%ss at=%s\n' \
+    "$available" "$load" "$cores" "$((SECONDS - start))" "$(date -u +%s)" > "$report"
   exec systemd-run …
 fi
+# The in-scope run must follow a fresh preflight written by the outer invocation.
+read -r tag ok _ _ _ _ at < "$report" || exit 2
+[[ "$tag $ok" == "PREFLIGHT ok" ]] || { printf 'Missing preflight record\n' >&2; exit 2; }
+(( $(date -u +%s) - ${at#at=} <= 60 )) || { printf 'Stale preflight record\n' >&2; exit 2; }
```

**副作用**：

- 锁文件描述符 9 经 `exec systemd-run` 继承到内层，门禁运行期间锁一直被持有；
- 评审方在副本中跑测试时如果也使用 L1 / L2，同样会受到这把锁的约束，这正是 08 §4.2 规则 1 的意图。

**测试**：

- 持有锁时运行 `ci/gate.sh task-999`，期望退出码 2、不写报告；
- 直接以 `--in-scope` 运行且报告不存在或首行不是 PREFLIGHT 时，期望退出码 2。这两个测试都用伪造的 `.venv/bin/python`，在资源预检之前就退出，不会真正进入门禁。

### CI-08 NIT　intranet 跳过无条件生效；断网只覆盖进程内 socket；uv 版本未入报告

**位置**：`tests/conftest.py` L13–17、L24–33；`ci/gate.sh` L64–68。

**问题**：

1. conftest 在任何环境中都跳过 `intranet` 标记，内网主机上也无法运行这类测试，与 08 §6.2"开发机自动跳过"的表述不一致。
2. 断网夹具只覆盖本进程的 `socket` 函数。测试启动的子进程（例如 `git`、`lint-imports`，以及以后可能的 `curl`、`gbs`）不受约束，"测试不访问网络（以夹具强制）"并不完整。
3. gate_report 没有记录 `uv --version`。

**候选修改**：

- conftest 改为仅在 `os.environ.get("CODINGSYSTEM_INTRANET") != "1"` 时跳过 intranet 用例；gate.sh 在开发机上断言该变量未设置。
- gate.sh 中，pytest 步骤在可用时以 `unshare --user --net --map-current-user` 运行，并在报告中写明 `network-namespace: on`；不可用时写 `off`，不阻断。
- 在 `sha256sum uv.lock` 之后加一行 `uv --version`。

**副作用**：`unshare` 依赖内核是否允许非特权用户命名空间；不可用时只是记录下来，不阻断门禁。

**测试**：

- 设置该环境变量时，intranet 哨兵用例被收集并执行（在测试中用 monkeypatch 设置变量，并断言 `pytest_collection_modifyitems` 不添加 skip）；
- `unshare` 可用时，在 pytest 中用子进程访问回环以外的地址应失败。

---

## 6. 能否作为 M0a 的开发输入

**08 开发指南 v1（GO）**：可以作为 M0a 的开发输入。四条 MINOR 都是补充可执行性与绕过清单，可随 08 v1.1 一并修订，不影响按现稿开工。其中 G08-01（禁止清单与登记）与 G08-04（provisional 核对）建议在 contracts 包落地前完成。

**01 扩展逐条映射表（NO-GO）**：在 MAP-01 处理之前，不宜作为 M0a 的"三批条目清单"定稿输入。四份示例流水线与 Demo 镜像节点对第二批子键的依赖，需要设计做出批次裁定：

- 一是拆出两个第一批最小子键；
- 二是把 P1-G01 的第二批入口条件写进 gate 对照表，并登记 HLD §13 措辞问题。

不受影响的部分可以先用作第一批起草的索引，包括 B7-2、B7-3、B7-7、B7-8、B7-10 各组，以及 P2 的大部分类别。MAP-02..04 可在第一批起草时一并修正。

**gate 对照表 P0–P2（GO）**：可以作为 M0a 的开发输入。GM-01 的日期与 GM-02 的漏列 D23 部署项、契约入口列，应在下一次维护中补齐；其中 DEMO-S01、S02 的日期在 11-27 检查点之前就会被使用，建议优先修改。

**门禁代码（NO-GO）**：只限 D23 证据。CI-01 修复之前，门禁的"无 PHP 检查"结论不应作为 D23 证据引用。其余检查（锁文件、ruff、mypy、import-linter、pytest 与 coverage、内容扫描）可以照常使用。CI-02..CI-07 建议在 contracts 包落地、阶段 gate 证据开始积累之前完成。
