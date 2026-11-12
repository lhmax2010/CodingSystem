# 开发状态

## 1. 当前里程碑与周

2026-11-11，09 §4.4 W1（11-09～11-13），M0a 开发输入就绪准备期。M0a 不代表 P0 完成；P0/M0b 目标 2026-12-31。

## 2. 任务进度表

| 编号 | 标题 | 状态 | 提交号 | 交付目录 |
|---|---|---|---|---|
| task-001 | 08 初稿、仓库骨架、门禁与开发记录 | 实现完成；本地门禁通过，待外部评审 | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a；交付提交 38ed660cd7a4df8c3021d1d0ccde0ab580f91287 | docs/dev/deliver/task-001/ |
| task-002 | task-001 审读修正与批次审定 | 本地门禁通过，待审读 | 1b6775e8c7a85e7215250d1ef7942c88c3fa802d；交付提交 7ab70a28e5d57c3c427870f8f2176688616b1547 | docs/dev/deliver/task-002/ |
| task-003 | M0a 处置、08 v1.1 / 09 v0.5、映射与 gate 对照表 | 文档修订完成；L1 1–7 通过、8/9 跳过，待外部审读；第 6 项不作 D23 证据 | bad2eab247a4e1d6ed939c0b3a7ad73099867367；交付 25a5c2b6990df587868b3a9af9e8647ea8531ec9 | docs/dev/deliver/task-003/ |
| task-004 | M0a C1–C10 / E1–E5 门禁加固 | L1 第 1–9 项通过，10/11 跳过；待定向核对 | 8151478b42062be343e058238e8048a6f83d2b62；交付 25e3997db6864b808ceef55426b7544b7a3cb798；推送诊断补记为本文件所在提交 | docs/dev/deliver/task-004/ |

## 3. 已闭合结论

| 结论 | 证据路径 | 提交号 |
|---|---|---|
| 08 指南按给定摘要移动后，仅按负责人授权修改资源开跑门槛；Downloads 源文件已不存在 | deliver/task-001/evidence.txt | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a |
| 两个独立分发空壳可安装；依赖与实际导入边界有测试 | agents/skeletons/tests/test_installation.py；tests/ci/test_imports.py；最终结果见 deliver/task-001/gate_report.txt | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a |
| 当前框架没有业务代码；无 LangGraph；无 provisional 契约 | framework/；provisional.md | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a |
| 选定工具版本闭包不含 Pygments/rich，26 个已安装分发 D23 门禁零命中 | deliver/task-001/REPORT.md | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a |

task-002 已闭合：系统 3.12.3 虚拟环境、带任务号门禁、历史报告保护、四文件停用首行及批次消费三项自查。证据见 deliver/task-002/REPORT.md 与 gate_report.txt；实现提交 1b6775e8c7a85e7215250d1ef7942c88c3fa802d。

task-003 已完成文档自查：75 条 HLD 原文保持；102 个叶键各属一批；P1/P2 及 Demo 全属第一批，P1–P4 不晚于第二批。G1 日期、G2 契约入口与 D23-PENDING-09～12、P6 远程 version 待办已补齐。证据见 deliver/task-003/REPORT.md、evidence.txt；实现提交 bad2eab247a4e1d6ed939c0b3a7ad73099867367。本结论是文档核对，不代表对应契约或阶段 gate 已验收。

## 4. 负责人裁决前提

- 2026-11-11，负责人本会话裁决：08 §4.2 第 2 条旧的 2 倍 MemoryMax 开跑门槛作废；改为 available ≥ MemoryMax + 1 GB，L1 ≥4096 MiB。负载门槛及最长等待 30 分钟不变；CPUQuota=200%、MemoryMax=3G、MemorySwapMax=0 均不变。授权仅修改指南该句，并登记本条。

- 2026-11-11，task-001 与 09：HLD v2.14 定稿、01 v0.24 为核心契约开发基线、09 v0.4 为排期基线。
- 2026-11-11，09 §2 原则 7：负责人负责需求、决策与内网操作；设计与评审主持 1 人；Codex 开发会话重任务串行；三家外部评审；内网 AI 执行内网验证。产能变化或月度偏差超过一周，按 09 §10 重排。
- 2026-11-11，09 §3：总部方案确认随 12-29 Demo 进行。
- 2026-11-11，HLD D23、task-001：不得引入 PHP；未批准任何例外。
- 2026-11-11，08 §1、task-001：设计文档 00–09 只由设计方修改；本任务先原样移动 08，后按负责人专项授权仅修改 §4.2 第 2 条。


- 2026-11-11，task-002 常规规则：新放入的设计文档、评审文件或处置表含 D23 文本信号时，放入文件的任务必须同时在 ci/d23_policy.json 纯数据分类登记路径、sha256、理由，并在该任务 REPORT.md 列出，由设计审读确认。未登记导致门禁失败，任务视为未完成。
- 2026-11-11，task-002 常规规则：依赖闭包出现 PHP 相关文本信号时可选择不含它的版本，但不得长期以降级规避；确需该依赖时必须停止报告，走 HLD D23 例外与分类流程，由负责人裁决。

- 2026-11-11，task-003：08 v1.1 与 09 v0.5 已按给定摘要原样放入，旧 08 v1 与 09 v0.4 保留。本任务仍按 08 v1 执行；从 task-004 起按 08 v1.1 执行，排期按 09 v0.5。
- 2026-11-11，M0a 处置表与负责人决定：Kimi 本轮未参与，按 Codex / Claude Code 两家结论处置；不将此表述为三方 unanimous GO。
- 2026-11-11，M0a 处置 M1 设计裁决：P1 示例加载的静态字段 / 类型 / 规则前移第一批，BenchReport 谓词和 gate_eligible 判定语义仍在第二批；第二批通过前，含 BenchReport 的 release_requires 在运行期审批 fail-closed，静态加载不拒绝。Demo 的 release_requires 不含 BenchReport。

- 2026-11-11，task-004 常规规则：ci/gate.sh task-NNN 必须先提交实现；除 STATUS 与本任务交付外不得有脏树。历史报告不可覆盖，所有尝试单独保留；最终报告须注明采用的 attempt。
- 2026-11-11，task-004 常规规则：L1/L2 共用跨 worktree flock；预检与检查串行，首行预检须在 60 秒内有效，核对实际 nice / ionice。L0.5 用于单文件测试和小脚本。
- 2026-11-11，task-004 常规规则：新增放宽项须与 ci/bypass_register.json 逐条精确对应；非 intranet skip / xfail 一律失败；provisional 标注、清单、映射叶键须一一对应，Demo 不能以 provisional 代替评审。
- 2026-11-11，task-004 常规规则：所有推送方使用标准库 pre-push 模板或手动等效运行，检查工作树与待推送提交信息；本任务不修改 Git hooks 配置。内容豁免必须精确绑定文件摘要、规则、行号与理由。
- 2026-11-11，task-004 常规规则：开发门禁要求 CODINGSYSTEM_INTRANET 未设置；仅内网显式设为 1 才执行 intranet。uv 固定为 0.11.13；D23 包含实际 venv 前缀，不在门禁内删除遗留字节码。

## 5. 挂账

| 问题 | 临时处理 | 解除条件 | 负责方 |
|---|---|---|---|
| pytest 8.3.5 / import-linter 2.0 固定版本 | 新版默认闭包引入 Pygments PHP 词法器，按 D23 拒绝后暂固定无该依赖的版本；不得长期以降级规避 | 升级前重新核对闭包；确需含信号依赖则停止并提交 D23 分类/例外裁决，不自行扩大豁免 | 开发跟踪、负责人裁决 |
| contracts/CF 尚未实现 | task-004 按 08 v1.1 重编号为门禁 10、11；仍为跳过，非通过；未来比较 01 §0.3 的契约包版本 | 后续任务实现契约与 CF 后启用 | 设计下达任务、开发实现 |
| 关键模块无业务分支 | 保持 95% 阈值；报告 N/A，不作为业务验证证据 | 后续实现后逐模块验收 | 开发 |
| 部署类 D23 尚未实现 | gate_matrix 明列待实现，仓库扫描不替代部署验收 | 首次部署/使用前完成真实验收 | 开发 / 负责人 / 内网 AI |
| M0a 映射与 gate 对照表审定 | task-003 已执行 M1–M4、G1–G2；三项自查无批次违规 | 待本轮审读；01 落点列在第一批起草时回填，具体契约仍须对应批次三方通过 | 设计审读、开发维护 |
| 08 v1.1 门禁加固定向核对 | 仓库与依赖范围的无 PHP 门禁已按 C1–C8 加固，待定向核对确认；采用 task-004 attempt-002，旧报告不追溯升级证据等级 | 定向核对 C1–C10 / E1–E5、新增 91 条内容豁免与 3 条放宽项登记 | 设计 / 负责人审读 |
| 旧资源门槛导致等待超时 | 负责人授权修改为 L1 available ≥4096 MiB，已按新门槛运行 | 已解除；限额不变；后续仍执行资源预检 | 负责人裁决已登记 |

## 6. 环境事实

- 核实日期：2026-11-11；task-002 开场 main HEAD 38ed660cd7a4df8c3021d1d0ccde0ab580f91287，干净且已同步。
- 系统 `/usr/bin/python3.12` 与 `.venv/bin/python` 均为 Python 3.12.3；task-002 已重建虚拟环境，`.python-version` 固定 3.12；gate 在安装前后核对实际主次版本，不符失败。未安装系统 Python，不下载托管解释器。
- `uv --version`：0.11.13，可用；锁定工具 uv。`uv.lock` 同时记录两个工作区包和完整传递闭包与制品 hash。
- 打包：setuptools 显式 `package-dir={codingsystem="framework"}`；skeletons 用 src 布局、独立项目依赖框架 workspace 包；构建后端作为已锁定开发依赖，`--no-build-isolation` 避免额外浮动下载。
- `systemd-run --user --scope -p CPUQuota=200% -p MemoryMax=3G -p MemorySwapMax=0 nice -n 19 ionice -c3 true` 成功；gate.sh 还校验实际 cgroup 文件。
- `nproc`：20；`free -m` 总内存 31540 MiB；可用内存与负载每次 L1 前记录于证据/门禁报告。无并行门禁或 xdist。
- task-002 核对命令与输出见 deliver/task-002/evidence.txt；历史 task-001 证据保持原样。门禁必须用 ci/gate.sh task-NNN，已提交的报告不覆盖。

- task-004 重建仍为系统 Python 3.12.3、原锁文件与 26 个分发；旧虚拟环境保留在仓库同级 .CodingSystem-task004-venv-before-rebuild。实际 L1 限额、优先级已核实；本机 network-namespace: off，socket 禁网夹具生效。详见 deliver/task-004/evidence.txt 与 gate_report.txt。

- 2026-11-12 推送诊断：正常 HOME 的 HTTPS credential helper 原为空，gh keyring 登录有效；未发现 task-004 隔离影响 push。按负责人授权完成网页登录及 gh auth setup-git，helper 已衔接 gh，pull --rebase 成功。证据见 deliver/task-004/evidence.txt 的“2026-11-12 推送失败诊断与凭据恢复”节；既有门禁结果保持。

## 7. 设计问题清单

| 位置 | 问题 | 处置状态 |
|---|---|---|
| HLD 附录 B7、09 §3.1 | Demo 最小字段 / 第二批 mock / 第三批真实能力的字段子键需确认 | task-003 已按 M1–M4 进一步审定，102 个叶键各属一批；字段细化及 01 落点随对应批次起草 / 评审 |
| HLD §11.3、09 §3.1 | P4 全部类别消费的 mock schema 与真实业务字段分界 | task-003 按 M1–M3 修订：静态加载前移、套件最小 schema 为第二批 P4、远程 version 断言登记 P6；本轮自查无批次违规 |
| 09 §3/§5.2/§10 | 每个 gate 条目的个人负责人与细化日期未指定 | 保留角色与原文目标，待负责人确认 |

开发状态唯一来源为本文件；.dev_memory 四文件已加停用首行，原历史内容保留。
