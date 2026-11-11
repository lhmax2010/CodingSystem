# task-003 交付报告

日期：2026-11-11。执行者：Codex；开发机本地，L0 命令均低优先级串行。适用指南仍为 08 v1；08 v1.1 从下一任务生效。未修改业务代码、依赖、锁文件或门禁实现；两个 JSON 文件仅刷新受审文档及策略表的摘要。

## 开场与输入文件（真实：开发机文件 / Git 校验）

开场 main HEAD：76d3352e1c3df2d854cff132a90377e8d4ef8c14。工作树干净，pull --rebase 已同步。STATUS 的 task-002 实现 / 交付与历史一致；其后的 a55c241、76d3352 仅新增两份 M0a 评审文件，因此不存在状态冲突。STATUS §6 环境事实逐字保留。

三个源文件均先核对存在、给定摘要、目标不存在与 D23 文本信号，再用 mv 移动，移动后再次核对；Downloads 三个原路径均不存在。旧 08 v1、09 v0.4 与 task-001 / task-002 门禁报告原样保留。原始输出见 evidence.txt。

| 仓库路径 | SHA256（移动前后均一致） |
|---|---|
| docs/08_Codex_Dev_Guide_v1.1.md | 1581c53a679a6b141bda67adc06c5c5d2a7fddfc6796e2d0070afd5c9debe620 |
| docs/09_Phased_Dev_Plan_v0.5.md | 81da755af67a260b83cd4257b5ab9ae8cd2b29995b9dc53f473945f0871d4e86 |
| docs/review/M0a_review_disposition.md | e21861c777d66c7df48d2fe3717e6dd308693a0cc137693b858fbc4af441bc63 |

三个新文件无 D23 判定信号，未新增纯数据登记；另对起始标记按原始字节忽略大小写核对，亦无命中。这是对三个输入文件的专项核对，不是对旧扫描器合规性的证明。现有映射表的纯数据登记保持原理由，仅更新 sha256；ci/d23_scanner_digests.json 随之刷新策略表摘要，策略版本及扫描器源码不变。映射表新 SHA256 为 `80917f78a110be122bfc7fdd8142bd80aa899bdbca28c9924f469e9293665e5b`；分类理由仍为规范文本阅读、非入口 / 可执行模板，待设计审读确认。

## 改动对照处置表（人工：规范逐项核对）

| 处置项 | 落地修改 |
|---|---|
| M1-静态部分 | 新增第一批 B7-1-2-bench-opt-syntax、B7-5-7-bench-static、B7-5-3-gate-fields、B7-5-2-local-min；mock-bench-opt、bench、decision-core、schema 分别收窄为运行时语义、谓词、判定语义及其余能力 / Quickbuild 声明，仍属第二批。 |
| M1-套件分界 | B7-5-4 仅作父索引；-load 为第二批 P4，-business 为第三批 P7。明确加载身份、auto / 显式选择与 absolute / relative 依赖不包含统计与测量记录。 |
| M1-测试消费 | T024、025、041-a、049 补四个第一批静态子键及 rules-rest；T073-b、079、083 均为 P4，消费 -load 与 -schema，写明 absolute-only 通过、relative / 无法解析 / auto 拒绝及 Optimization / 必需 Bench 发布拒绝子矩阵。 |
| M1-Demo / 审批 | 第 2 步加入 local-min；第 4 步加入 bench-opt-syntax，删除笼统“不消费第二批”断言，按实际键检查。遵循 09 v0.5：Demo release_requires 不含 BenchReport；第二批通过前拒绝发生在运行期审批，非静态加载。 |
| M2-ImageRecord | 字段归 B7-4-2 的两个子键；B7-4-1-image-demo 只描述 mic 效应 / 入库 / 引用，image-profile-probe 只描述 probe 行为，均显式引用字段所有者。 |
| M2-遗漏落点 | 新增第一批 B7-1-2-rules-rest、B7-4-1-deferred 与第二批 B7-4-1-image-failure；缩窄旧 demo-dsl、remote-build 的定义范围，父键原文不删改。 |
| M2-判定字段 | decision-core 明列 mode、gate_eligible、validation_complete、opt_verdict 的判定语义；measurement 明列逐指标四值 / 区间、spec_inconclusive_count、opt_gain_pct、baseline_revoked、baseline_unavailable。BenchReport.comparison 三值及 comparison_unverifiable 原因归 B7-5-16。 |
| M2-定义 / 消费 | B7-5-17 标为引用规则而非再次定义；表末列出字段唯一落点与静态 / 运行时边界。能力声明模型的 comparison 与 BenchReport 同名字段按不同模型区分。镜像失败类别的实际消费测试补 image-failure；纯加载测试不挂运行时失败映射。 |
| M3 | T052 补 deferred；T053 缩为 cancel_pending / 配额账与 Fake 终态，不断言 version；T029 补 local-min；Demo 第 2 步补 B7-3-1、B7-2-5。version 独立登记 P6-TODO-01。 |
| M4 | 十个分组表在最早使用方之后加负责人和 01 落点列，120 行统一“设计 / 开发”；01 落点暂空，第一批起草回填。 |
| G1-P0 | P0-D03 为 11-20；P0-G01 为 12-29（备选 12-30）；P0-G02 为 12-11；三者均注明 12-31 汇入 P0。 |
| G1-Demo | S01 首次部署前且不晚于 11-27；S02 首次真实构建前且不晚于 11-27；S03–S06 W4 首次内网 LLM 联调前且不晚于 12-04。 |
| G2-待办 | 逐条采用 Claude Code GM-02 候选补 D23-PENDING-09～12：最低策略 / 撤销发布与缓存、Run 例外复核与现行版本、策略升级全量重扫、独立构建主机 / 运维助手闭包。均待实现，证据空。 |
| G2-契约入口 | P0–P2 共 25 行新增契约入口列并逐行填写；P1-G01 为“第一批（含 M1 新增静态子键）”。既有 01 核心不强挂 B7；P3–P5 / P7 仍空表，仅 P6 新增指定待办。 |
| STATUS | 登记新版本、Kimi 未参与按两家处置、M1 裁决与 C1 证据限制；更新 task-003 状态及历史 task-002 交付号，环境事实保持。 |

## 三项自查

1. **通过（人工 + 真实的本地结构校验）**：75 条 HLD 原文逐条与开场提交比对无变化。120 个映射行含 18 个不归批父键与 102 个叶键；第一批 63、第二批 25、第三批 14；每个叶键恰属一批，无重复编号、无悬空消费引用。字段定义 / 消费人工核对未发现两个叶键重复定义同一模型的同一字段；M2 指出的 ImageRecord、comparison、三条规则、deferred 与失败类别已各有唯一落点。静态字段与运行时语义为不同责任，交叉引用不作为第二份定义。此项不替代 01 起草时的模型字段审读。
2. **通过（真实：本地结构校验）**：112 个测试类别含 P1 28、P2 22、P3 20、P4 29，合计 P1–P4 99 类；引用叶键全部不晚于第二批。其中 P1/P2 共 50 类全部为第一批。P5/P6/P7 另列 13 类，不计入 P1–P4。违规清单：无；未为检查通过自行改批。
3. **通过（真实：本地结构校验；消费选择为人工核对）**：Demo 六步逐项引用数为 5 / 9 / 5 / 3 / 10 / 3；共同部署前提另含 15 项，全部第一批。违规清单：无。空壳 Benchmark 只证明结构，不宣称已实现第二批报告判定或真实 Benchmark。

结构校验脚本及原始输出收在 evidence.txt；脚本最初把 bench / bench-static 的字符串前缀误判为父子，已修正为原始数字条目键才可作父键，同级子键不嵌套。未因此改动设计批次；这不是项目门禁失败。

## 门禁与证据边界

实现提交：bad2eab247a4e1d6ed939c0b3a7ad73099867367。门禁 HEAD 将绑定该实现提交；最后的交付提交只含 STATUS 与本任务三个文本证据。task-003 按 08 v1 的现有门禁运行，C9 的新规则不在本任务实现。

真实（开发机受限 L1 执行；测试使用 Fake / 本地夹具）：2026-11-11T15:00:17Z～15:00:31Z，ALL-END status=ok rc=0，未重跑。实际 cgroup：cpu.max=200000 100000，memory.max=3221225472，memory.swap.max=0；开跑 available=9137 MiB，load1=0.65，20 核，满足 4096 MiB / 10 门槛。

| 项 | 结果 |
|---|---|
| 1 锁文件 / 安装 | PASS；Python 3.12.3，锁文件未变 |
| 2 ruff | PASS；31 文件格式检查 |
| 3 mypy --strict | PASS；31 源文件 |
| 4 import-linter | PASS；6 条合约 |
| 5 pytest / coverage | PASS；51 passed，1 intranet skipped；行覆盖 97.87% ≥80%；关键空模块 N/A，95% 阈值未改；provisional=0 |
| 6 无 PHP 扫描 | 现有实现执行 PASS；26 个已安装分发，0 命中。因 C1 不作为 D23 证据 |
| 7 内容边界 | PASS；当前内容 0 命中 |
| 8 契约一致性 | SKIP；仅 contracts 目录空壳，无契约模型 |
| 9 CF 追溯 | SKIP；尚无 CF 实现 |

原始门禁输出保持在 gate_report.txt。门禁完成后仅回填 STATUS / REPORT 的实际结果及 evidence 的命令输出，对最终四个交付 / 状态文件作同策略的定向文本检查；未改代码或门禁结果。

C1 已知缺陷未在本任务修复：**本次及此前门禁“无 PHP”输出不得作为 D23 证据引用**，不能以执行通过推导符合 HLD §11.2。08 v1.1 新规则与 C1–C10 留待 task-004。关键模块仍无业务分支，95% 阈值保持，空模块 N/A 不代表验证通过；契约与 CF 尚未实现，8 / 9 两项按授权跳过，非通过。

## 未完成项、设计问题与挂账

- 本任务要求的文档维护与自查已完成；本地门禁结论见上节。新增依赖：无；解释器、锁文件与依赖闭包版本不变。
- 设计问题：本轮未发现需新增裁决的批次矛盾；M1–M4、G1–G2 按给定裁决执行，尚待外部审读，不宣称 M0a 或 P0 验收通过。
- task-004：实现 C1–C10 和 08 v1.1 新门禁规则，并按处置表下一步组织定向核对。该后续任务未启动。
- 设计：第一批起草时回填 01 落点，分别记录三方通过日期；当前留空有明确授权。Kimi 缺席为负责人本轮决定，不扩展为以后免除三方评审。
- 负责人：gate 个人负责人仍待确认；已指定的日期已按 G1 细化。D23 部署待办共 12 项及 Demo 安全切片须在各自首次使用前真实验收，本任务未执行内网操作。
- 原挂账继续：pytest 8.3.5 / import-linter 2.0 暂时固定，不能长期靠降级规避；contracts / CF 与关键业务覆盖尚未实现。
