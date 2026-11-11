# task-001 交付报告

状态：task-001 本地门禁 1–7 全部通过，8/9 按任务授权跳过；等待外部评审，不宣称阶段 gate 已获外部验收。

## 完成项

- 【真实】开场 main 的 HEAD 为 f5fcc6329c04da3d7bd324a06da724267df1c564，pull 已同步、工作区干净。08 指南源文件与移动后 SHA256 均为 22b49316f132339c9676b36a5658aed1549b08be8edff394bd525119c8a4b1e3；使用 mv，Downloads 不留副本，随后按负责人专项授权仅修改 08 §4.2 第 2 条；其余设计文档内容未改。
- 【真实】按 HLD §10 建立目录；删除 artifacts/skill 的空占位；framework 以 setuptools package-dir 映射到 codingsystem，全部子包只含职责 docstring；Agent skeletons 是独立分发包并显式依赖框架。没有业务实现，没有引入 LangGraph。
- 【真实】uv.lock 锁定完整解析闭包与制品哈希，两个工作区包按同一锁文件安装；开发依赖仅门禁工具、构建后端及其传递依赖。默认网络由 socket 夹具禁止，intranet 开发机自动跳过并保留计数。
- 【真实】import-linter 实际 CLI 的五条边界及框架根模块补充规则均有正/负夹具；Agent 公开导入面另有正向夹具。D23 有判定信号、纯数据逐文件摘要、Python AST/tokenizer 片段判定、策略版本与扫描器摘要表；无 docs/tests/py 整体免扫。
- 【真实】临时验证：44 passed、1 intranet skipped，coverage 合并汇总 97.47%。最终门禁以 gate_report.txt 为准，临时数值不是最终验收。
- 【人工】gate_matrix 抽取 HLD P0–P2、Demo 安全切片与 09 §10；P3–P7 只建表头。映射表保留附录 B 第 7 组十组、75 个顶层分号条款与候选子键；批次和测试类别关联是待设计审定的草稿。

## 未完成项及范围

- 【真实】完整门禁 1–7 通过；44 passed、1 intranet skipped；全局行覆盖率 97.87%，关键空模块 N/A，95% 门槛不变；provisional=0。
- 【未验证】contracts 仅目录空壳，无模型与 CF；门禁 8、9 按任务明示跳过，不标通过。
- 【未验证】关键框架模块只有 docstring，无分支，95% 阈值已固定，当前分支覆盖为 N/A，不冒充关键业务已测试。
- 【未验证】主机安装集、镜像、部署前缀、pyc 制品清单、E0 观测、执行准入、exec 记账及加载 attestation 不在任务范围，已列 gate_matrix 待实现。
- 【未验证】部署安全切片与真实内网场景未执行；没有访问内网、构建或提交 Quickbuild。

## 设计问题

本任务按提示词授权只出映射草稿，以下不影响空壳/CI 实现，也不据此实现契约：

1. 09 §3.1 未逐字段枚举 ImageReport/ImageRecord 的 Demo 最小面、Diagnosis/ai_draft 最小面、Quickbuild 锁定 base 的 P4 mock 输入，请设计确认映射子键互斥且穷尽。
2. HLD §11.3 的全部类别包含 P6/P7 真实能力；需设计逐类界定 P1–P4 mock 核心消费面，不晚于第二批。当前映射只作候选关联，未宣称闭合。
3. 09 给出角色、月份与里程碑，未逐条指派姓名/日期；gate_matrix 保留原文目标，待负责人落实。

## 新增依赖（完整锁定第三方闭包）

许可证来自已安装分发 METADATA；条件包 colorama 的许可证核对了锁定 wheel 内 LICENSE.txt，wheel SHA256 与 uv.lock 一致。制品完整 SHA256 见 uv.lock。无联网测试插件：采用仓库内 autouse socket 夹具。两个自有空壳包版本均 0.0.1，不作为第三方依赖重复计数。

| 名称 | 版本 | 许可证 | 用途 |
|---|---|---|---|
| annotated-types | 0.8.0 | MIT | pydantic 约束类型 |
| ast-serialize | 0.13.1 | MIT | mypy AST 支持 |
| click | 8.5.1 | BSD-3-Clause | import-linter 命令行解析 |
| colorama | 0.4.6 | BSD-3-Clause（锁定 wheel 内 LICENSE.txt） | Windows 条件终端依赖；Linux 未安装 |
| coverage | 7.17.2 | Apache-2.0 | 行与分支覆盖率收集 |
| grimp | 3.19 | BSD 2-Clause License | import-linter 的实际导入图 |
| hypothesis | 6.170.15 | MPL-2.0 | 固定种子、有界 property 测试 |
| import-linter | 2.0 | BSD 2-Clause License | 真实导入边界检查；2.0 默认闭包不引入 rich/Pygments |
| iniconfig | 2.3.1 | MIT | pytest 配置解析 |
| librt | 0.16.0 | MIT | mypy 运行支持 |
| mypy | 2.4.1 | MIT | 严格类型检查 |
| mypy-extensions | 1.2.0 | MIT | mypy 类型扩展 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | pytest/mypy 包版本处理 |
| pathspec | 1.1.1 | MPL-2.0（METADATA Classifier） | mypy 路径匹配 |
| pluggy | 1.7.0 | MIT | pytest 插件机制 |
| pydantic | 2.14.3 | MIT | 契约模型基础（本任务不实现契约） |
| pydantic-core | 2.50.4 | MIT | pydantic 核心验证 |
| pytest | 8.3.5 | MIT | 测试执行；8.3.5 默认闭包不引入 Pygments |
| pytest-cov | 7.1.0 | MIT | 覆盖率插件 |
| pyyaml | 6.0.3 | MIT | DSL YAML 解析基础（本任务不实现解析器） |
| ruff | 0.17.4 | MIT | 静态检查与格式检查 |
| setuptools | 84.2.1 | MIT | 两个独立空壳包的构建后端；与运行/开发闭包一同锁定以禁用隔离构建的浮动依赖 |
| sortedcontainers | 2.4.0 | Apache 2.0 | Hypothesis 数据结构 |
| typing-extensions | 4.16.0 | PSF-2.0 | 类型兼容支持 |
| typing-inspection | 0.4.5 | MIT | pydantic 类型分析 |

【真实】最初解析的 import-linter 2.16 → rich 15.0.0 → Pygments 2.21.0，以及 pytest 8.4.2 默认引入 Pygments。D23 拒绝其 PHP lexer 的长 docstring（不是精确签名常量）。改为仍通过实际边界夹具的 import-linter 2.0、pytest 8.3.5 后，闭包不再包含 Pygments/rich；未修改依赖源码、未豁免命中、未放宽签名规则。26 个 Linux 已安装分发（含两个本地包）的 D23 检查零命中；Windows 条件包仅在锁中，未作为已安装文件扫描结果宣称通过。

## 内容边界历史扫描

【真实】扫描全部 refs 的 108 个可达提交、318 个不同 blob，29 处模式命中。当前版本 19 处为 fake_llm golden vector 固定伪端点，逐条按文件摘要、规则和行号登记理由；其余历史命中只报告，不改历史。模式命中不等于已经确认的真实凭据泄露；历史条目需负责人复核，报告不复制命中值。

```text
Historical commits: 108; unique blobs: 318; findings: 29
Matched values omitted; each blob is attributed to its first visited commit/path.
f5fcc6329c04da3d7bd324a06da724267df1c564 3020627d398bfaf57074498dbb9984b40edc6530 docs/01_Contract_Spec_v0.10.md:568 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 c628dfa97e45950d9151f3d76ace2838b4aa7caa docs/01_Contract_Spec_v0.11.md:587 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 cc1679d5d05e96e70a99625773b8d3a12e88081b docs/01_Contract_Spec_v0.12.md:607 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 7036846674121aff2fb23f2e24b6647f36277a18 docs/01_Contract_Spec_v0.13.md:626 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 b49df3abf0575b8d07b48ecde73725fc48d82788 docs/01_Contract_Spec_v0.14.md:630 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 c28f5a89d70102c686194754a1eeb76c6d823441 docs/01_Contract_Spec_v0.15.md:635 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 20afac32d24696e38cf431f8f8e270c6ad08539f docs/01_Contract_Spec_v0.16.md:640 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 7335c9c42b2255214c6dd9a493f9f01d93d02d94 docs/01_Contract_Spec_v0.17.md:643 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 66565b9d45f286f5048f4ee4b6d4074d8898d6cd docs/01_Contract_Spec_v0.18.md:654 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 27068854b26e044fd7777e2689528e3aa92c551f docs/01_Contract_Spec_v0.19.md:667 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 08be9dd4f80461d64f55e8cb46f5036f7832b5b4 docs/01_Contract_Spec_v0.20.md:686 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 ec5e322c59352748505b280c74c799769a71f872 docs/01_Contract_Spec_v0.21.md:690 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 a91177770927ea7f54e6349228c1d43e620a74bf docs/01_Contract_Spec_v0.22.md:693 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 de36d89c5e9c4e67176148cadd70c7b213edbf03 docs/01_Contract_Spec_v0.23.md:693 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 ad4eb00c0b8c6b7c626d3303ccfa95316f302aa1 docs/01_Contract_Spec_v0.24.md:694 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 87b473995e826b3c8aa1aa9a5ec20f7362b2b3b2 docs/01_Contract_Spec_v0.7.md:520 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 895886d94041f333247867a5775b369a7548a7e4 docs/01_Contract_Spec_v0.8.md:535 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 0381feac66e2e8cedb54cd63c84f2a2305f4018a docs/01_Contract_Spec_v0.9.md:566 internal-host
f5fcc6329c04da3d7bd324a06da724267df1c564 326c4a33bd528108005d8b957b0dc09fec524696 docs/review/01_v0.7_review_{kimi,claudecode,codex}.md:65 internal-host
aa25375b8710ad72e8e0a614774d285430dc53ea 26e286579bfeb6ef3f79c1fec8b883b6033a0344 docs/baseline/00_Agent_Team_Contract_v0.7.3.md:891 private-key
aa25375b8710ad72e8e0a614774d285430dc53ea d06a10d0cfa144dd73f0870c0d754cac15895cca docs/baseline/08_Phase_1_5_Overview_v0.3.md:308 internal-host
aa25375b8710ad72e8e0a614774d285430dc53ea 60d500118361ba926d2160d477fc423c20f08204 docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/llm_adapter/README.md:223 internal-host
aa25375b8710ad72e8e0a614774d285430dc53ea 60d500118361ba926d2160d477fc423c20f08204 docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/llm_adapter/README.md:316 internal-host
fbfd625dcfa0b009b160b3891b3c68e23c28529a 51f777bfa400acd1d0d1fe201b883532e2b06e30 docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/llm_adapter/README.md:173 internal-host
fbfd625dcfa0b009b160b3891b3c68e23c28529a 51f777bfa400acd1d0d1fe201b883532e2b06e30 docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/llm_adapter/README.md:266 internal-host
8d0f082c5840470b5502ca249145808e509bc6b1 db20b2e92f4b17085d82f9fc271eed06a0327428 docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/llm_adapter/README.md:145 internal-host
8d0f082c5840470b5502ca249145808e509bc6b1 db20b2e92f4b17085d82f9fc271eed06a0327428 docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/llm_adapter/README.md:238 internal-host
cd883c5919e03d1d1e2b87bb25bb29f97d5295d7 226cecccc9ef81dc0a8c5ca2078e2f73661c9309 docs/baseline/00_Agent_Team_Contract_v0.7.2.md:875 private-key
e8ef16dd299e10cdb7c813b123b1de9487261095 1749015c7be7d53bdd73f1785a3395af6f858c6a docs/baseline/08_Phase_1_5_Overview_v0.3.md:308 internal-host
```

## 挂账与负责人事项

- 08 §9 分支：按提示词在 main 串行开发，不开任务分支；待指南评审确认。
- 08 §9 锁定工具：uv 0.11.13 可用，采用 uv；不需 pip-tools 降级。setuptools 构建映射与锁定方式已记录。
- 08 §9 托管 CI：未启用 GitHub Actions，以本地 gate.sh 证据为准；是否增加托管镜像由负责人决定。
- 08 §9 资源：systemd 用户 scope 已以 L1 true 验证，运行门禁还会核对实际 CPU/内存/swap cgroup 限额。后续可用内存不足时严格等待，最长 30 分钟。
- 请设计审定映射草稿与策略表（含逐文件纯数据分类）；没有自行批准 D23 例外。
- 未加入任何 provisional 契约实现，清单为空。

## 2026-11-11 负责人资源门槛裁决

旧门槛等待最终以退出码 75 超时，未启动该轮 L1。负责人授权按新门槛重新检查并继续 task-001：available ≥ MemoryMax + 1 GB（L1 为 4096 MiB），负载不超过核数一半，等待上限 30 分钟；三项 cgroup 上限不变。仅替换 08 §4.2 第 2 条指定句子；逆向替换后摘要严格等于原始给定摘要，证明未改其他内容。

修改后 08 SHA256：`181b81c236ab173c90a087219af4f55989e034c0906c896080a50ddb75886ba1`。

## 门禁实现校正

ruff 0.17.4 默认也检查 Markdown 中的代码块，首次全仓 format --check 因 51 份设计/评审文档的代码示例失败；未修改这些文档。配置明确代码格式门禁的文件类型为 Python/存根/notebook/pyproject，覆盖全部代码文件；设计文档仍全部进入 D23 与内容边界扫描。这是落实 08 的代码规范与设计文档修改边界，不改变 Python 格式规则和覆盖率阈值。

## 最终证据说明

实际 cgroup 上限由 gate.sh 读取并强制核对，报告记录实际值。19 项固定伪端点与 1 项 pytest 标记表达式按完整文件摘要、行号、规则和理由登记内容扫描豁免，未使用目录级豁免。纯数据分类、扫描器摘要与内容豁免表均作为本任务交付供评审。

未完成项仅限本任务明示的 contracts/CF 跳过项、部署侧 D23 后续工作及设计审定事项；不把空壳测试等同于业务契约/真实环境验收。

实现提交：`4f6ce82ef55cf11c17aa5466735a2f89bcea782a`。最终 gate_report 的 HEAD 绑定此实现提交，测试时还包含即将交付的 docs/dev 记录（同样接受内容扫描）；最后一笔提交仅保存开发记录与证据，并同步 STATUS，未变更被测实现。
