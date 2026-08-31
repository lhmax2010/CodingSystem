# HLD v0.3 三方复审处置表（→ v0.4）

裁决输入：Kimi **GO**（10 MINOR/NIT + 2 CLARIFY 作勘误）、Claude Code NO-GO（1 BLOCKER）、Codex NO-GO（重开 2 + 新增 6 BLOCKER + 6 MAJOR）。
三个仲裁关注点：B1/B2/B3 Kimi 与 Claude Code 接受，Codex 三项反对——其反对全部落为具体 issue（R3-01/02/04 → B1；R3-04/06/07 → B2；I-02 重开/R3-05 → B3），逐条处置于下，无悬空反对。

## 共识/交叉簇

| 簇 | 覆盖 | 处置 | 落点 |
|----|------|------|------|
| P idem_key 效应身份（v0.3 引入的回归） | CC T-01(BLOCKER); Codex 重开 I-05 | 采纳 | §5.2 效应级锚定（effect_class + effect_params_digest + effect_seq，含 series/tree_digest 等实参）；§4.3.2 残留"含 attempt 序号"矛盾清除；上一 attempt 非终态记录对账 abandoned。CC 的反例（LLM 非决定论产 S3' 复用 S3 构建产物）是定案依据 |
| Q 授权新鲜度与绑定 | Codex R3-01(BLOCKER); 与 CC B1(d)(e) 纵深分析相容 | 采纳 | §3 授权绑定扩展（run/gate_instance/decision/ci_plan_task/series/manifest）；§8.2 approve 事务 CAS（gate waiting + ReleasePlan 当前 + series 最新）；§4.2.4 series 推进事务撤销待审批项与未核销授权；§8.3 broker 复核全部绑定 |
| S 特权 IPC 完备性 | Codex R3-06(BLOCKER)/R3-07(MAJOR); Kimi M-05/M-06/M-07; CC T-02/CL-C | 采纳 | §8.5 双向化（broker 入站仅编排 UID）；worker 数据面命令显式枚举（side_effect/trace/artifact 索引/series candidate）；task 级 socket FD 绑定 + 连接上下文推导归属 + 越域拒绝审计；deploy/ provisioning 交付（账户/权限/特权 launcher/启动顺序）+ 真实 UID E2E 隔离测试入 P4 gate |

## Kimi（M-01–M-10 + CLARIFY 1–2）——GO，条目作勘误全采纳

| # | 处置 | 落点 |
|---|------|------|
| M-01 | 采纳 | §3 Approval 服务行删"核销"，核销唯一归属 broker |
| M-02 | 采纳 | §4.3.1 administrative finalize 显式例外句 |
| M-03 | 采纳 | §4.2.5 限定"release 可达路径上的 hitl" |
| M-04 | 采纳 | §4.2.4 普通节点每次送达独立触发、汇合必须显式 join |
| M-05 | 采纳 | 簇 S（task 级绑定强于其建议的 run/task 作用域声明） |
| M-06 | 采纳 | 簇 S（特权 launcher 属可信计算基，随 deploy/ 交付） |
| M-07 | 采纳 | 簇 S（broker 入站通道 + token_id 高熵已入 §3） |
| M-08 | 采纳 | §4.2.4 tree_digest 编排层纯算法计算、"Ledger 计算"措辞修正 |
| M-09 | 采纳 | §8.2 manifest 规范化算法补 [01] |
| M-10 | 采纳 | §4.3.1 状态机补 awaiting_patch（与 Codex R3-08 合并） |
| CL-1 | 采纳 | §7.4 日志摘录按内容升级密级（内联源码 → internal_code）；与 CC CL-A 同答 |
| CL-2 | 采纳 | §4.2.5 release 出边禁入环（校验器禁止） |

## Claude Code（T-01–T-06 + CL-A–D）

| # | 处置 | 落点 |
|---|------|------|
| T-01 BLOCKER | 采纳 | 簇 P（取其首选方案：效应级参数摘要；LLM 重放决定论化方案改动面大，不取） |
| T-02 | 采纳 | 簇 S 数据面命令枚举 |
| T-03 | 采纳 | §4.3.3 活跃引擎场景先停引擎/杀 worker 再收尾 |
| T-04 | 采纳 | §8.2 CLI 呈现 manifest + 证据链，清单入 01/07 |
| T-05 | 采纳 | §10 注释改 review/（与 Codex 重开 I-25 合并关闭） |
| T-06 | 采纳 | release 统一称"特权节点" |
| CL-A | 采纳 | 同 Kimi CL-1 |
| CL-B | 已定 | 受限操作描述与凭据原语 contract 归 01（07 引用），v0.4 未加标注句——01 编写时落 |
| CL-C | 采纳 | 簇 S deploy/ 交付 |
| CL-D | 已定 | §4.2.6 MVP 禁止链式 join |

## Codex（重开 2 + R3-01–R3-12）

| # | 处置 | 落点 |
|---|------|------|
| 重开 I-02 | 采纳，重开成立 | §4.2.6 threshold 指标来源支配性 + 同 series 检查（其反例有效：来源存在不支配 gate 必然运行时 fail） |
| 重开 I-05 | 采纳，重开成立 | 簇 P（§4.3.2 残留矛盾属实，v0.3 处置表所称关闭有误，本表更正） |
| 重开 I-25 | 采纳，重开成立 | §10 注释残留属实，已改 |
| R2-06 复议 | 采纳 | D12 provider digest 含端点身份/信任策略，仅凭据值除外（其反例：端点改向外部服务而策略名不变，成立） |
| R3-01 BLOCKER | 采纳 | 簇 Q（方案全收） |
| R3-02 BLOCKER | 采纳 | §8.3/§4.3.1 publishing point-of-no-return：核销事务原子迁移 publishing，期间 cancel/fail_safe/series 更新仅登记 pending，完成或 probe 对账后定终态 |
| R3-03 BLOCKER | 采纳 | §4.2.4 series 推进收敛为编排单事务（candidate + expected_parent CAS + lineage + latest + 失效），worker 崩溃不再留下无生产者的 current series |
| R3-04 BLOCKER | 采纳 | §4.4 outbox 消费端去重（decision_id、gate CAS、durable dispatch 后 delivered、重复投递同结果） |
| R3-05 BLOCKER | 采纳 | §4.2.4 activation 语义（activation_id 含环计数向量、到达键、每源一次、原子整组、重复丢弃审计、超时自首到达起算）+ §11.3 同 series 多轮循环用例 |
| R3-06 BLOCKER | 采纳 | 簇 S + deploy/ + P4 真实 UID gate（其"可实现同用户进程通过测试"的批评成立——部署资产此前确实缺位） |
| R3-07 | 采纳 | 簇 S task 级绑定（socket FD 注入方案） |
| R3-08 | 采纳 | §4.3.1 状态机补 awaiting_patch/queued/publishing；awaiting_patch 不占队列不阻塞 ready Run |
| R3-09 | 采纳 | §7.5 active-upload lease + 安全年龄 GC + 索引前复验 |
| R3-10 | 采纳（方案调整） | 不引入独立 watchdog 进程：worker 为进程组长，心跳丢失时**先 killpg 本组 + 终止登记外部进程、后退出**——达成同一语义、少一个常驻组件；故障注入用例照收 |
| R3-11 | 采纳 | §8.3 D12 漂移核销前检测、专用错误码、administrative finalize，不烧授权不伪装 release_failed；§4.2.5 同步 |
| R3-12 | 采纳 | §13 P3 adapter 功能完成+打包+模拟器集成、P4 模拟联调；§12 真实端点联调为独立上线 gate；"无外部环境依赖"表述修正 |

## 汇总
- 全部条目采纳或等效采纳；两处方案裁剪：R3-10 以 worker 自杀前 killpg 替代独立 watchdog（语义等价、组件更少），CC T-01 取效应级摘要方案（弃 LLM 重放决定论化）。
- v0.3 处置表两处更正：I-05 与 I-25 当时宣称关闭有误（残留文本未清），本轮重开成立并已修复。
- Kimi 已 GO；v0.4 复审重点：(1) 簇 P 的效应级 idem_key 是否闭合（含 abandoned 对账）；(2) 簇 Q+R3-02 的授权新鲜度与 publishing 状态机；(3) R3-05 activation 语义；(4) 簇 S 部署资产是否足以兑现 D8。
