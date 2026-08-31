# HLD v0.1 三方评审处置表（→ v0.2）

裁决输入：Claude Code NO-GO(2 BLOCKER)、Kimi NO-GO(3 BLOCKER)、Codex NO-GO(8 BLOCKER)。
处置类别：**采纳**（按建议或等效方案修入 v0.2）/ **部分采纳**（方向采纳、方案有裁剪，说明理由）/ **不采纳**（说明理由）。
落点列指 v0.2 章节。仲裁原则：以证据与反例场景为准，不以提出方为准；三方重叠 issue 合并处置。

## 共识簇（三方重叠，一并处置）

| 簇 | 覆盖 issue | 处置 | 落点 |
|----|-----------|------|------|
| A DSL 执行语义不完整（寻址/join/保留节点/穷尽路由/环预算/示例自违规） | CC I-02/03/04/05/12/21; Kimi I-01/02/04/05/14/15/19; Codex I-01/02/11/12 | 采纳 | §4.2 全重写：显式节点实例（废除点号寻址）、joins all-of + series 一致、保留节点清单、status 全集注册 + default_route 强制、loops 环级预算 + 计数口径、threshold 示例、合法子集定义（4.2.6）、示例即校验验收用例 |
| B approval 组件归属 + token 时序矛盾 | CC I-01/07/09; Kimi I-03/07; Codex I-03/04 | 采纳 | §8.2/8.3、§1.1、§10、§13 P2：Approval 服务+Review CLI+Release broker 纳入框架交付；resume 不消费 token、broker 原子单次核销；token 绑定 release manifest digest；release 保留节点必经 hitl（4.2.5），"CI 类判定"问题消解 |
| C 幂等/恢复/存储一致性 | CC I-07/18/20 C4; Kimi I-10; Codex I-05/06/07 | 采纳 | §5.2 at-least-once 显式化 + 两阶段 side_effect + probe 恢复协议 + input_digest 定义；D6 Ledger 单一权威源同库事务；trace 改 JSONL 派生；D12 execution manifest 拒绝跨版本恢复 |
| D 数据边界自我标注 | CC I-08; Kimi I-06; Codex I-09 | 采纳 | D7/§7.1：来源出生标注、密级格、聚合取最高、禁降级、中心配置授权、cascade 每跳重校验 fail-closed；残余风险 R8 |

## Claude Code（I-01–I-22, C1–C6）

| # | 等级 | 处置 | 落点/说明 |
|---|------|------|----------|
| I-01 | BLOCKER | 采纳 | 簇 B |
| I-02 | BLOCKER | 采纳 | 簇 A |
| I-03 | MAJOR | 采纳 | §6.3/§4.2.6：默认 optional + 少数 hard-required 可声明，校验恒真问题消除 |
| I-04 | MAJOR | 采纳 | 簇 A（§4.5） |
| I-05 | MAJOR | 采纳 | §4.2.3 |
| I-06 | MAJOR | 采纳 | §4.3.2 sys.* outcome + retry 策略 + default_route |
| I-07 | MAJOR | 采纳 | §8.3 核销绑定 task_id、恢复视为有效；§5.2 at-least-once + broker 远端幂等 |
| I-08 | MAJOR | 采纳 | 簇 D |
| I-09 | MAJOR | 采纳（等效方案） | §4.2.5：不做"凭据授权推断 CI 类"，改为 release 保留节点 + 凭据只在 broker——判定问题整体消失，强于原建议 |
| I-10 | MAJOR | 采纳 | §6.5 create_run(pipeline_id, target_spec) |
| I-11 | MAJOR | 采纳 | D11 单活跃 Run + Run 内并行 + WAL 单写者；§7.6.3 额度 |
| I-12 | MINOR | 采纳 | §3 保留节点；rejected 统一走 fail_safe |
| I-13 | MINOR | 采纳 | §6.5 cancel_run + §4.3.1 取消处置 |
| I-14 | MINOR | 采纳 | R9：禁自动 rebase，冲突 fail_safe → 新 Run |
| I-15 | MINOR | 采纳 | v0.2 全文重排引用并 grep 核验 |
| I-16 | MINOR | 采纳 | §6.5 HTTP+JSON 定案 + bearer 认证 + 信任边界声明 |
| I-17 | MINOR | 采纳 | §5.1.1 contract_requires PEP 440 specifier |
| I-18 | MINOR | 采纳 | §7.5 JSONL + 保留策略 |
| I-19 | MINOR | 采纳 | D1 依赖闭包 lockfile |
| I-20 | MINOR | 采纳 | §4.1 改写为已知引擎行为硬前提；R2 改写 |
| I-21 | NIT | 采纳 | §4.2.1 bench_gate |
| I-22 | NIT | 采纳 | §7.2 缓存键按 capabilities |
| C1 | — | 已回答 | G6/R5：v1.0 基于 FakeLLM 定稿，内网 provider 一致性为独立上线 gate，效力边界已明示 |
| C2 | — | 是 | threshold 参数模型入 01 DSL 章节；HLD 给出 fail-closed 决策（§4.4） |
| C3 | — | 已定 | §4.4 gate TTL 可配置，默认无，超时 outcome=gate_expired |
| C4 | — | 已定 | §7.5 Ledger 同库事务 |
| C5 | — | 已定 | §5.2 idem_key 含 attempt；task 内子操作派生键由 SDK 规定（node+loop_round+attempt+子操作序），细则入 01 |
| C6 | — | 采纳 | D1 理由注明依据；lockfile 固化 |

## Kimi（I-01–I-19 + CLARIFY 1–5）

| # | 等级 | 处置 | 落点/说明 |
|---|------|------|----------|
| I-01 | BLOCKER | 采纳 | 簇 A |
| I-02 | BLOCKER | 采纳 | 簇 A（§4.2.4 含分支 fail_safe 传播=取消其余在飞） |
| I-03 | BLOCKER | 采纳 | 簇 B：按其建议方向拆分——resume 用引擎机制由 approval 决定触发，token 单一消费点在 broker |
| I-04 | MAJOR | 采纳 | §4.5 环级预算、计数时点（入环+1）、持久化、wall_clock 排除 paused |
| I-05 | MAJOR | 采纳 | §4.2.3 status 全集注册 + on 值校验 + sys.* 命名空间 |
| I-06 | MAJOR | 采纳 | 簇 D；conformance 误标检测用例 §11.3 |
| I-07 | MAJOR | 采纳 | 簇 B；签发密钥归 approval 服务、broker HMAC 验签（§8.2） |
| I-08 | MAJOR | 采纳 | §5.1.2 worker 子进程 + D8 凭据仅 broker 进程 + 能力句柄授权注入 |
| I-09 | MAJOR | 采纳 | §4.3.2 |
| I-10 | MAJOR | 采纳 | 簇 C；input_digest 按 content digest 定义 |
| I-11 | MAJOR | 采纳（等效方案） | 承认业务侧仅准入级强制（R6）；运行时约束以能力句柄注入实现（其建议原文），发布/构建通道物理上只经框架句柄 |
| I-12 | MINOR | 采纳 | §5.1.1 |
| I-13 | MINOR | 采纳 | 引用修正 |
| I-14 | MINOR | 采纳 | §6.3 approval_token 外部供给类别 |
| I-15 | MINOR | 采纳 | §3：fail_safe 仅指保留节点，Run 终态统一 closed(reason) |
| I-16 | MINOR | 采纳 | §6.5：单协议、series 格式与基线校验、单次 submit 语义 |
| I-17 | NIT | 采纳 | D1 |
| I-18 | NIT | 采纳 | §2.1 分层图修正（业务 Agent 置于 SDK 之上） |
| I-19 | NIT | 采纳 | §4.2.1 dsl_version 注释 + §6.2 |
| CL-1 | — | 已定 | §7.1 cascade 判据=传输/超时/结构化校验失败；质量性判据不做（N3） |
| CL-2 | — | 已定 | §4.4 TTL 可配置默认无 |
| CL-3 | — | 已定 | D11 + §7.6.3 信号量 FIFO |
| CL-4 | — | 部分采纳 | pipeline 以文件+digest 管理，Run 绑定 pipeline_digest（D12），更新不影响在途 Run；完整生命周期管理（安装/废止流程）留 09/运维文档，MVP 不建管理系统 |
| CL-5 | — | 已定 | §5.3 llm_budget 在 pipeline 节点级 |

## Codex（I-01–I-25）

| # | 等级 | 处置 | 落点/说明 |
|---|------|------|----------|
| I-01 | BLOCKER | 采纳 | 簇 A（端口概念不引入，多实例=显式节点，语义等效更简） |
| I-02 | BLOCKER | 采纳 | §4.2.6 合法子集定义 + policy invariant（release 必经 hitl、threshold fail-closed、hard-required 静态拦截、可达性/穷尽性） |
| I-03 | BLOCKER | 采纳 | 簇 B；Skill API 不加 approve（审批走 Review CLI→Approval 服务，与 Coding Agent 通道隔离是刻意设计） |
| I-04 | BLOCKER | 采纳 | D8/§8.3 release broker + ReleasePlan + manifest 绑定（snapshot/tree_digest/目标/pipeline_digest/exec_manifest_digest/过期），发布前重核 |
| I-05 | BLOCKER | 采纳 | 簇 C：两阶段状态机 + claimed/running/unknown + probe 对账；exactly-once 表述全文移除；broker compare-and-consume 原子化 |
| I-06 | BLOCKER | 采纳 | D6 Ledger；trace 派生 JSONL；artifact 内容寻址不可变 |
| I-07 | BLOCKER | 采纳 | D12 execution manifest；不做在途迁移（拒绝恢复→fail_safe），比"迁移/drain 策略"更简且安全，属方案裁剪 |
| I-08 | BLOCKER | 部分采纳 | 凭据隔离部分全采纳（broker 独立进程、worker 无 secret、能力句柄授权）；**完整容器沙箱/egress allowlist 不采纳**：D13 信任模型下 patch 来源为内网认证 Coding Agent，威胁模型不含不受信公网输入；全沙箱为范围膨胀。以 §8.1 显式假设 + R7 残余风险 + "假设失效前置补沙箱"约束替代。此为本轮唯一实质性裁剪，复审可重点攻击 |
| I-09 | MAJOR | 采纳 | 簇 D（含派生数据继承最高密级、cascade 每跳重校验） |
| I-10 | MAJOR | 采纳 | §5.1.2 worker 生命周期/租约/hard-kill；§4.3.2 异常映射表 |
| I-11 | MAJOR | 采纳 | §4.5 + run_budget |
| I-12 | MAJOR | 采纳 | §4.3.2 outcome taxonomy + default_route 必填 |
| I-13 | MAJOR | 采纳 | §4.2.4/§6.4 series_id + tree_digest 绑定、stale 丢弃、token 随 series 失效 |
| I-14 | MAJOR | 采纳 | §4.3.1 穷尽状态机 + closed(reason) 统一；新 Run 默认重 pin（可显式沿用） |
| I-15 | MAJOR | 采纳 | §6.5：单协议、认证、request_id 幂等、大小/路径校验、错误语义入 01 |
| I-16 | MAJOR | 采纳 | §7.6.2 多仓 manifest + repo 归属 + 回滚 + tree_digest |
| I-17 | MAJOR | 采纳 | §4.1 EnginePort + 职责矩阵 + engine conformance；lockfile 于开工日生成 |
| I-18 | MAJOR | 采纳 | G6 三条件 + §13 P5 五类 fixture + 兼容矩阵 |
| I-19 | MAJOR | 采纳 | D4 wheel/entry-point/fork 定位；发布 gate 进 ci/ |
| I-20 | MAJOR | 采纳 | §8.4 脱敏（指纹化）、密级标签、只读+本机访问、保留策略 |
| I-21 | MAJOR | 采纳 | D11 + §7.6.3（信号量/FIFO/水位/worktree 对账回收）；调度优先级不做（单活跃 Run 下无意义） |
| I-22 | MAJOR | 采纳 | §11.2 关键模块 95% 分支 + §11.3 强制测试类别（其清单全收） |
| I-23 | MAJOR | 采纳 | §11.3 conformance attestation 绑定制品 digest |
| I-24 | MAJOR | 采纳 | §14 R6–R12 扩充，含 owner/信号/对策 |
| I-25 | NIT | 采纳 | 引用全文修正 + freeze 前 grep 核验（本轮已执行） |

## 汇总
- 全部 BLOCKER：13/13 采纳（其中 Codex I-07/I-08 为部分采纳/方案裁剪，理由如上）。
- MAJOR/MINOR/NIT：除 Kimi CL-4 部分采纳外全部采纳。
- 复审关注点提示：(1) N7/D13 信任模型裁剪是否可接受；(2) D12 "拒绝恢复不迁移" 是否可接受；(3) DSL v1 语义是否闭合。
