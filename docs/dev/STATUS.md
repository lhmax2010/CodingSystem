# 开发状态

## 1. 当前里程碑与周

2026-11-11，09 §4.4 W1（11-09～11-13），M0a 开发输入就绪准备期。M0a 不代表 P0 完成；P0/M0b 目标 2026-12-31。

## 2. 任务进度表

| 编号 | 标题 | 状态 | 提交号 | 交付目录 |
|---|---|---|---|---|
| task-001 | 08 初稿、仓库骨架、门禁与开发记录 | 实现完成；本地门禁通过，待外部评审 | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a；交付为本文件所在提交 | docs/dev/deliver/task-001/ |

## 3. 已闭合结论

| 结论 | 证据路径 | 提交号 |
|---|---|---|
| 08 指南按给定摘要移动，原文未修改；Downloads 源文件已不存在 | deliver/task-001/evidence.txt | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a |
| 两个独立分发空壳可安装；依赖与实际导入边界有测试 | agents/skeletons/tests/test_installation.py；tests/ci/test_imports.py；最终结果见 deliver/task-001/gate_report.txt | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a |
| 当前框架没有业务代码；无 LangGraph；无 provisional 契约 | framework/；provisional.md | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a |
| 选定工具版本闭包不含 Pygments/rich，26 个已安装分发 D23 门禁零命中 | deliver/task-001/REPORT.md | 4f6ce82ef55cf11c17aa5466735a2f89bcea782a |

## 4. 负责人裁决前提

- 2026-11-11，负责人本会话裁决：08 §4.2 第 2 条旧的 2 倍 MemoryMax 开跑门槛作废；改为 available ≥ MemoryMax + 1 GB，L1 ≥4096 MiB。负载门槛及最长等待 30 分钟不变；CPUQuota=200%、MemoryMax=3G、MemorySwapMax=0 均不变。授权仅修改指南该句，并登记本条。

- 2026-11-11，task-001 与 09：HLD v2.14 定稿、01 v0.24 为核心契约开发基线、09 v0.4 为排期基线。
- 2026-11-11，09 §2 原则 7：负责人负责需求、决策与内网操作；设计与评审主持 1 人；Codex 开发会话重任务串行；三家外部评审；内网 AI 执行内网验证。产能变化或月度偏差超过一周，按 09 §10 重排。
- 2026-11-11，09 §3：总部方案确认随 12-29 Demo 进行。
- 2026-11-11，HLD D23、task-001：不得引入 PHP；未批准任何例外。
- 2026-11-11，08 §1、task-001：设计文档 00–09 只由设计方修改；本任务先原样移动 08，后按负责人专项授权仅修改 §4.2 第 2 条。

## 5. 挂账

| 问题 | 临时处理 | 解除条件 | 负责方 |
|---|---|---|---|
| contracts/CF 尚未实现 | 按 task-001 授权将门禁 8、9 标为跳过，非通过 | 后续任务实现契约与 CF 后启用 | 设计下达任务、开发实现 |
| 关键模块无业务分支 | 保持 95% 阈值；报告 N/A，不作为业务验证证据 | 后续实现后逐模块验收 | 开发 |
| 部署类 D23 尚未实现 | gate_matrix 明列待实现，仓库扫描不替代部署验收 | 首次部署/使用前完成真实验收 | 开发 / 负责人 / 内网 AI |
| 映射批次草稿尚未审定 | 保留原文与候选子键，不实现其契约 | 设计审定互斥、穷尽、最早消费者 | 设计与评审主持 |
| 旧资源门槛导致等待超时 | 负责人授权修改为 L1 available ≥4096 MiB，已按新门槛运行 | 已解除；限额不变；后续仍执行资源预检 | 负责人裁决已登记 |

## 6. 环境事实

- 核实日期：2026-11-11；开场 main HEAD f5fcc6329c04da3d7bd324a06da724267df1c564，干净且已同步。
- `python3 --version`：Python 3.12.3；uv 使用既有托管 CPython 3.13.13 创建 `.venv`，未安装系统 Python，后续安装禁止解释器下载；两者均满足 ≥3.12。
- `uv --version`：0.11.13，可用；锁定工具 uv。`uv.lock` 同时记录两个工作区包和完整传递闭包与制品 hash。
- 打包：setuptools 显式 `package-dir={codingsystem="framework"}`；skeletons 用 src 布局、独立项目依赖框架 workspace 包；构建后端作为已锁定开发依赖，`--no-build-isolation` 避免额外浮动下载。
- `systemd-run --user --scope -p CPUQuota=200% -p MemoryMax=3G -p MemorySwapMax=0 nice -n 19 ionice -c3 true` 成功；gate.sh 还校验实际 cgroup 文件。
- `nproc`：20；`free -m` 总内存 31540 MiB；可用内存与负载每次 L1 前记录于证据/门禁报告。无并行门禁或 xdist。
- 完整命令与原始输出见 deliver/task-001/evidence.txt。

## 7. 设计问题清单

| 位置 | 问题 | 处置状态 |
|---|---|---|
| HLD 附录 B7、09 §3.1 | Demo 最小字段 / 第二批 mock / 第三批真实能力的字段子键需确认 | task-001 授权只出草稿，待设计审定 |
| HLD §11.3、09 §3.1 | P4 全部类别消费的 mock schema 与真实业务字段分界 | 映射表候选关联已列，待设计审定 |
| 09 §3/§5.2/§10 | 每个 gate 条目的个人负责人与细化日期未指定 | 保留角色与原文目标，待负责人确认 |
