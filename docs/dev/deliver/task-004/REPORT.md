# task-004 门禁加固交付

适用 08 v1.1，开发机 / Codex 本地执行。开场 main HEAD 25a5c2b6990df587868b3a9af9e8647ea8531ec9，与 STATUS task-003 交付一致；工作树干净，pull --rebase 已同步。未修改设计文档 00–09、历史交付或 Git 配置。

## C1–C10、E1–E5 改动与对应测试

证据等级：下表正反例为 Fake（临时文件、临时仓库及注入失败）；真实门禁结论单列于下节。内容豁免分类为人工（开发机 / Codex 逐行核对，位置与理由见清单）；设计确认尚未完成。

| 处置 | 改动 | 复测证据 |
|---|---|---|
| C1 | 原始字节忽略大小写检测；Python 片段只接受 UTF-8 / BOM；常量、bytes、隐式拼接、f-string、注释按原始偏移逐处核对；批准签名仍大小写精确相等 | test_d23 的全部 8 种大小写 × 7 种载体 × 签名/完整程序，以及 HZ / ISO-2022-JP、BOM、非 ASCII 偏移；143 项专项通过 |
| C7 | 删除 Python 扫描器摘要整文件豁免；非 Python 规则表仍摘要绑定；D23 策略升级 task-004-d23-v2、重登记源码与规则表摘要 | test_unregistered_language_and_no_whole_python_exemption；精确签名未登记也通过 |
| C8 | shell 入口及步骤脚本首部设置禁写 bytecode；在 RECORD 之外检查实际 venv 文件；未列入清单的运行时 bytecode 拒绝；内部链接不重复遍历，解释器链接必须落在 pyvenv.cfg home 且为 Python 版本化文件 | test_installed；首轮正式门禁及重建结果见下节 |
| C2 | 内容策略与豁免表升为 task-004-content-v2；扩充令牌 / 私钥 / 任意 depot / 私网尾句点；赋值长度 8、无需引号、无示例值前缀放行；加入 Header 凭据规则 | test_checks 的前缀、长度、标点、引号、令牌族及版本串 / HTTPS 反例；原有精确摘要豁免测试 |
| E3 | 标准库 content-stdin 无豁免；pre-push 模板检查当前文件及待推送各提交信息，包括新分支与标签对象；未修改本仓/全局 hooks 配置 | test_pre_push：临时仓库向本地裸仓库推送文件或提交信息命中均拒绝，安全提交通过；最终手动检查见 evidence |
| C3 | 目录描述符逐级 O_NOFOLLOW；拒绝符号链接、非普通报告、硬链接别名；同时检查 HEAD / index；O_EXCL 新建递增 attempt，不截断任何旧报告 | test_gate_runtime：每级目录链接、最终链接、报告目录、普通新目录、重复 attempt、暂存删除仍受 HEAD 保护 |
| C4 | 显式检查进程与日志进程，分别等待退出码；日志失败终止检查；写入、fsync、关闭、尾记录复核后才宣布成功 | test_logger_and_check_exit_codes、test_final_log_write_failure_no_success、test_execute_records_and_failures |
| C6 | Python 驱动以 flock 锁住运行目录共用锁（无运行目录时为共同 Git 目录），覆盖预检至证据关闭；没有可跳过预检的内部参数；预检写第一行并读回验证 60 秒有效期；记录实际 cgroup / nice / ionice | test_preflight_recovery_timeout_and_freshness、test_cross_worktree_shared_lock、test_effective_limits_validator；最终门禁真实资源记录 |
| C9 | shell 在任何解释器及资源检查前拒绝任务记录之外的脏树；驱动复核；报告 Task / HEAD / Tree；实现先提交后验收 | test_gate_entry：修改代码在 scope 前拒绝，仅 STATUS / 本任务交付允许；最终报告 HEAD / Tree |
| C5 | 全仓 conftest，两个测试树均有禁网/intranet 哨兵；只在显式内网环境时执行 intranet；开发门禁要求变量未设置；可用时 pytest 与子进程运行于独立网络命名空间 | test_pytest_policy 双树收集 / 执行与无外部请求的子进程路由哨兵；Agent 实际测试树哨兵 |
| C10 | engine 合约对框架和所有 Agent 根默认封闭；两条 engine 导入例外登记；删除 root-engine；所有根包、Agent 三条边界和 contracts 子包列表做完整性验证 | test_imports：五类边界、框架根违规、engine 正例及新增子包 / Agent 检测 |
| E2 | bypass 检查真实注释与 AST 调用 / 装饰器（含导入别名），不对扫描器源码整文件免扫；配置值包含多行内容，覆盖 pyproject 及常用独立配置；精确逐条登记、内容变化失效；非 intranet skip / xfail / XPASS / 收集跳过显式失败 | test_registrations 的未登记 / 登记 / 变更及配置；test_pytest_policy 五类拒绝 |
| E4 | 单文件测试与小脚本使用 L0.5（1 核 / 2G / 无 swap）；L1 检查及环境重建共用 flock，未并行执行 | evidence 中命令前缀；test_cross_worktree_shared_lock；真实 L1 报告 |
| E5 | 标注位置与叶键、provisional 清单精确一一匹配；排除父键，读取或表头失败即失败；无外部搜索工具依赖；输出计数与键列表 | test_provisional_exact_locations：未知键、父键、漏登记、孤立登记、错行与读取失败 |
| E1 | 10 / 11 两项仍授权跳过，文本明确未来比较 01 §0.3 的契约包版本，非文档草案号 | gate_steps.sh；本任务未实现契约模型或 CF |

uv 固定 `required-version ==0.11.13`，报告记录实际版本。新增依赖：无。锁文件与 26 个安装分发的版本不变；仅按锁重新安装的情况在 evidence 记录。

## 实现方式与未直接照抄的细节

- C6 将预检与驱动整体放在 L1 scope 内，锁由驱动持有到日志结束；不采用可公开传入的内部跳转参数。L0 shell 仍在 scope 之前核对工作树，scope 内无任何参数可绕过预检。使用 fcntl.flock 与命令行 flock 的同一内核锁。
- C3 始终先写带序号的 attempt；交付时以排他创建的 gate_report.txt 保存最终成功 attempt 的相同字节。所有失败 attempt 留存，不用覆盖实现重跑。
- C4 用显式管道和两个 Popen，避免异步进程替换丢退出码。日志错误不能产生对外成功记录。
- E2 不采用评审候选中整文件排除检查器的做法；用 tokenizer / AST 区分规则文本与真实放宽代码。配置登记摘要覆盖完整规范化配置值（含续行），源代码登记覆盖完整调用的行内容。既有 Agent 公开面导入白名单及授权 intranet 跳过一并登记，共 3 项，engine 为第一项；不是新增业务豁免。
- E5 以 path:line + 叶键核对，补足候选补丁仅比键集合不能识别错位置 / 重复登记的问题。
- E3 对 Git hook 输入的实际 ref 更新枚举提交；新分支没有旧对象时检查完整可达历史，避免只依赖可能缺失的 upstream。标准库实现，不需要虚拟环境。
- pytest 禁止非 intranet 跳过按候选方案显式报错退出；实现调试中仅修改报告状态不能可靠改变 pytest 退出码的方案未采用，失败与复测计数保留于 evidence。

## 门禁与证据等级

以下门禁执行结果为真实：开发机 / Codex 执行，原始记录在两个 attempt 文件与 evidence.txt。10/11 的契约与 CF 行为未验证；network-namespace 的隔离效果未验证，不将 off 视为通过。

实现提交：8151478b42062be343e058238e8048a6f83d2b62；被测 tree：3bc0a8e622c9c03d391936196bc6cccd1bb3066f。最终采用 gate_report.attempt-002.txt；gate_report.txt 是该文件的逐字节副本，排他创建。attempt-001 保留，不覆盖。

| 项 | 结果 |
|---|---|
| 1 锁文件 / 安装 | PASS；系统 Python 3.12.3，uv 0.11.13 |
| 2 Ruff | PASS |
| 3 mypy strict | PASS；41 个源文件 |
| 4 导入边界 | PASS；5 条合约 |
| 5 pytest / coverage | PASS；214 passed、2 个授权 intranet skipped；全局行覆盖 87.18%，综合覆盖 86.27%；关键空模块 N/A，95% 阈值未改 |
| 6 D23 | PASS；26 个分发，零失败；包含 RECORD 外前缀 |
| 7 内容边界 | PASS；零未豁免命中 |
| 8 放宽项登记 | PASS；发现 3 条、登记 3 条 |
| 9 provisional | PASS；0 个标注，子键清单为空 |
| 10 契约一致性 | SKIP；尚无契约模型，将来比较 01 §0.3 契约包版本 |
| 11 CF 追溯 | SKIP；尚无 CF 实现，契约基线采用 01 §0.3 契约包版本 |

首轮正式门禁第 6 项拒绝 43 个遗留 runtime_pyc_unlisted；1–5 通过、7–11 未执行。按指示 uv sync --reinstall 后仍剩 4 个未归属字节码，故将原 .venv 整体 mv 到仓库同级 .CodingSystem-task004-venv-before-rebuild 保留，使用系统 3.12.3 与未改动的锁文件重建，再执行 uv sync --reinstall。重建后字节码计数 0，第二轮通过。没有在门禁中删除字节码，也没有扩大 D23 豁免。命令及原始输出见 evidence.txt。

第二轮开跑 available=11078 MiB、load=8.95、cores=20；实际 CPU 配额 200%、MemoryMax=3G、MemorySwapMax=0、nice=19、ionice=idle。network-namespace: off：本机 unshare 探测不可用，按处置记录、不阻断；全仓 socket 夹具仍生效，子进程网络隔离不作已实现环境保证。

本地门禁为真实开发机执行；反例验证使用临时仓库/文件和 Fake 数据，不发真实构建或内网请求。部署安装集、镜像、运行期执行准入与 D23 阶段验收仍不在本任务范围。内容零命中不替代所有内部业务信息的公开性人工审查。

## 新增内容豁免（逐条人工核对，待设计审读确认）

共 91 条：90 条规范/评审术语，1 条 pytest 标记表达式。未发现疑似真实凭据或内网地址；未对词前缀做全局放行。以下仅列位置、规则、理由；不记录命中值。既有 20 条保持，旧设计及评审文档内容未修改。

| 路径 | 行号 | 规则 | 理由 |
|---|---|---|---|
| agents/skeletons/tests/test_agent_offline.py | 15 | internal-host | task-004 人工逐行核对：pytest 的 intranet 标记属性表达式，非主机名；C5 要求两个测试树的哨兵。 |
| docs/00_Framework_HLD_v0.10.md | 312 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.10.md | 351 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.11.md | 312 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.11.md | 351 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.2.md | 294 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.2.md | 332 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.3.md | 302 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.3.md | 341 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.4.md | 303 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.4.md | 342 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.5.md | 308 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.5.md | 347 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.6.md | 308 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.6.md | 347 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.7.md | 309 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.7.md | 348 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.8.md | 312 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.8.md | 351 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.9.md | 312 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v0.9.md | 351 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v1.0_draft_frozen.md | 312 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v1.0_draft_frozen.md | 351 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.0.md | 459 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.0.md | 593 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.10.md | 587 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.10.md | 778 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.11.md | 587 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.11.md | 778 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.12.md | 587 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.12.md | 778 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.13.md | 587 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.13.md | 778 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.14.md | 587 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.14.md | 778 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.2.md | 514 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.2.md | 690 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.3.md | 584 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.3.md | 772 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.4.md | 584 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.4.md | 775 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.5.md | 586 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.5.md | 777 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.6.md | 586 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.6.md | 777 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.7.md | 586 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.7.md | 777 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.8.md | 587 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.8.md | 778 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.9.md | 587 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/00_Framework_HLD_v2.9.md | 778 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.10.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.11.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.12.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.13.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.14.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.15.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.16.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.17.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.18.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.19.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.2.md | 30 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.20.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.21.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.22.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.23.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.24.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.3.md | 31 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.4.md | 31 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.5.md | 31 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.6.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.7.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.8.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/01_Contract_Spec_v0.9.md | 32 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/01_v0.4_review_{kimi,claudecode,codex}.md | 67 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/01_v0.6_review_{kimi,claudecode,codex}.md | 73 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/01_v0.7_review_{kimi,claudecode,codex}.md | 11 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/01_v0.7_review_{kimi,claudecode,codex}.md | 114 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v0.1_review_{claudecode,kimi,codex}.md | 141 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.0_01_v0.11_review_claudecode.md | 312 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.0_01_v0.11_review_claudecode.md | 440 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.0_01_v0.11_review_claudecode.md | 448 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.0_01_v0.11_review_claudecode.md | 449 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.0_01_v0.11_review_claudecode.md | 764 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.0_01_v0.11_review_kimi.md | 27 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.2_01_v0.12_review_claudecode.md | 704 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.2_01_v0.12_review_codex.md | 698 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.2_01_v0.12_review_codex.md | 706 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.2_01_v0.12_review_codex.md | 707 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/HLD_v2.2_01_v0.12_review_kimi.md | 97 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |
| docs/review/M0a_08v1_mapping_gate_review_codex.md | 165 | authorization-bearer | task-004 人工逐行核对：设计或评审文本中的认证机制、主体或头部术语及说明性运算符，非凭据载荷；不改变冻结文档，仅批准该文件摘要与该行。 |

## 待定向核对与负责人事项

- 设计定向核对 C1–C3、全部新增内容豁免、3 条放宽项登记及 08 v1.1 门禁落实。
- 负责人按指南确认 GitHub secret scanning / push protection；本任务未改 GitHub 设置，也未替各方安装 hook。
- 既有工具版本固定与部署 D23 待办继续，不宣称阶段 gate、Demo 或契约评审已完成。


## 2026-11-12 推送失败诊断与凭据恢复

真实证据（本机 / Codex，浏览器授权由负责人完成）见 evidence.txt 同名节。原推送因正常 HOME 下 HTTPS credential helper 未配置而退出 128；gh keyring 登录当时有效，协议记录为 ssh，不能被原 HTTPS Git 推送自动使用。未发现本任务隔离设置影响 push，无法确定此前凭据衔接何时变化。按负责人授权完成网页登录与 gh auth setup-git，HTTPS helper 已指向 gh；只使用这一条命令改变全局 Git 配置。恢复后的 pull --rebase 成功。诊断补记与 pre-push 检查不改变已提交实现或既有门禁证据。
