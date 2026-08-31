# HLD v0.2 三方复审处置表（→ v0.3）

裁决输入：Kimi NO-GO(1 BLOCKER)、Claude Code NO-GO(1 BLOCKER)、Codex NO-GO(重开 9 条 + 新增 4 BLOCKER)。
仲裁点 B1（N7/D13 沙箱裁剪）与 B2（D12 拒绝迁移）：**三方一致接受，就此定案关闭**（Claude Code/Kimi 各附一条措辞级补充，已采纳：R7 假设边界句、D12 理由句改引具体不支持场景）。B3（DSL 闭合性）三方一致反对闭合，成因即下述共识簇 J。

## 共识簇

| 簇 | 覆盖 | 处置 | 落点 |
|----|------|------|------|
| J join 死锁与触发机制（三家唯一共同 BLOCKER） | Kimi N-01; CC N-01; Codex 重开 I-01 | 采纳（按 CC/Kimi 一致建议） | §4.2.4 定案"到达=入边路由送达"+ wait_for ≡ 入边源集合（校验强制）；示例 wait_for 改 [bench_gate, review_static]；join_inputs 聚合结构（Kimi N-02/CC 同）；timeout_min（Kimi N-11/CC N-07） |
| K worker/approval/broker 的 Ledger 写路径矛盾 | Kimi N-04/N-06; CC N-02; Codex R2-04 | 采纳 | §7.5 直写者收敛 + §8.5 control-plane RPC（分 socket/分 OS 用户/peer credential/worker 不可达特权命令/幂等命令/单命令事务/resume outbox）；claimed ack 前置（§5.2）；HMAC 移除（权威判据唯一=Ledger，Kimi N-04 后半与 CC CL-1 同答） |
| L 审批时序与授权保管 | CC N-04; Codex R2-01/R2-02; Kimi N-09/N-13 | 采纳（按 Codex R2-01 方案） | 流水线重排 ci_plan → human_review → release；审批对象=ReleasePlan 规范化 ReleaseManifest；approved 出边直达 release（静态强制）；授权=Ledger 记录（token_id），无 bearer 进图状态/checkpoint，crash-safe；过期消费→release_failed(authorization_expired)（§4.2.5/§8.2/§8.3） |
| M 单执行 Run 语义 | Kimi N-08(部分); CC N-03/N-08; Codex R2-07 | 采纳 | D11 改"单执行 Run"：paused 不占执行槽、多 paused 并存、resume/新 Run FIFO（§6.5）；gate 等待为节点级、Run 级 paused=仅剩 gate 等待（§4.4）；awaiting-patch TTL 默认 24h（§4.3.1） |

## Kimi（N-01–N-13 + CLARIFY 1–4）

| # | 处置 | 落点/说明 |
|---|------|----------|
| N-01 BLOCKER | 采纳 | 簇 J（选其方案①） |
| N-02 | 采纳 | §4.2.4 join_inputs 固定形态，schema [01] |
| N-03 | 采纳 | §4.2.2 terminal success_on + compiler_bench_only.yaml 按此交付（与 Codex R2-08 合并） |
| N-04 | 采纳 | 簇 K：统一"经编排进程 RPC"；HMAC 按其质疑移除 |
| N-05 | 采纳 | §5.1.2 心跳丢失自杀 + pgid 孤儿 reaping |
| N-06 | 采纳 | 簇 K：claimed ack 前置、IPC 失败 fail-closed、intent/running 即时提交与完成事务边界（与 CC N-02 合并） |
| N-07 | 采纳（方案调整） | 发布 adapter 定案为**框架交付官方 gerrit/github adapter**（见 Codex R2-03 处置），能力句柄显式排除发布——两套集成点分裂消除，02–06 分工明确 |
| N-08 | 采纳 | §4.4 gate 节点级等待定案（在飞分支继续，series 漂移由陈旧性规则 fail-closed 兜底并显式引用） |
| N-09 | 采纳 | §8.3 输入=ReleasePlan+token_id（授权引用经编排层转发），§6.1 已含授权消息 |
| N-10 | 采纳 | §4.4 gate outcome 封闭枚举表 |
| N-11 | 采纳 | joins.timeout_min，缺省 run_budget |
| N-12 | 采纳 | routes 移除 loop 标注，环由 loops.edges 唯一定义（消除冗余优于双源校验） |
| N-13 | 采纳 | §8.2/§8.3 过期语义（release_failed 附 reason） |
| CL-1 | 采纳 | D12 理由句改写为引用具体不支持场景（与 CC N-10 一致），"官方明示"限定到拓扑变更/state 不兼容 |
| CL-2 | 已定 | §8.2：仅 Unix socket 本机监听，远程 reviewer 显式不支持，入 D13 |
| CL-3 | 已定 | §4.5：N 次通过、第 N+1 次拦截（与 Codex 重开 I-11 合并定案） |
| CL-4 | 已定 | D12：provider 配置 digest 仅含策略语义，端点/凭据轮换不影响恢复 |

## Claude Code（N-01–N-12 + CL-1–CL-4）

| # | 处置 | 落点/说明 |
|---|------|----------|
| N-01 BLOCKER | 采纳 | 簇 J（其"到达=入边路由送达+集合一致性校验"即定案文本） |
| N-02 | 采纳 | 簇 K |
| N-03 | 采纳 | 簇 M（按其建议：paused 释放执行槽 + FIFO） |
| N-04 | 采纳 | 簇 L（按 Codex R2-01 重排方案，与其建议方向一致） |
| N-05 | 采纳 | §4.2.4 series_id 由 SDK 原子 API 框架签发、不可自造 |
| N-06 | 采纳 | §7.1 密级全序 secret>internal_code>build_log>public（与 Codex 重开 I-09 合并） |
| N-07 | 采纳 | joins.timeout_min |
| N-08 | 采纳 | §4.3.1 awaiting-patch TTL + run_budget 起算点 |
| N-09 | 采纳 | 引用路径全文改 docs/review/（与 Codex 重开 I-25 合并；v0.1 处置表所称"grep 核验"当时只覆盖章节引用未覆盖文件路径，属实，致歉并已补） |
| N-10 | 采纳 | D12 理由句改写 |
| N-11 | 采纳 | §4.2.4 被取代 series 在飞任务跑完即弃（其 MVP 建议） |
| N-12 | 采纳 | §8.1 假设边界句（认证≠内容可信/间接提示注入） |
| CL-1 | 已定 | 权威判据=Ledger 记录，HMAC 移除，保管问题消失 |
| CL-2 | 已定 | §8.2 peer credential；细则 01 |
| CL-3 | 已定 | §4.3.3 dispatch/审批/发布前复核 digest（与 Codex R2-06 合并） |
| CL-4 | 已定 | §4.3.2 retry.on 允许 sys.timeout（注明幂等层覆盖） |

## Codex（任务 A 重开 9 条 + R2-01–R2-08）

| # | 处置 | 落点/说明 |
|---|------|----------|
| 重开 I-01 | 采纳 | 簇 J |
| 重开 I-02 | 采纳 | §4.2.6 hard-required 支配性检查（每条路径必先经生产节点） |
| 重开 I-04 | 采纳 | 簇 L + R2-03 处置，重开成立 |
| 重开 I-05 | 采纳 | §5.2 idem_key 去 attempt（逻辑效应身份）+ probe 结果描述符补全完成记录 |
| 重开 I-06 | 采纳 | §7.5 Blob 提交协议（temp→fsync→rename→索引事务）+ 孤儿 GC + dangling=sys.error；§11.3 逐点崩溃注入 |
| 重开 I-09 | 采纳 | §7.1 全序 |
| 重开 I-10 | 采纳 | §5.1.2 setsid 进程组 + killpg + BuildExecutor 长进程登记 |
| 重开 I-11 | 采纳 | §4.5 边界定案 |
| 重开 I-25 | 采纳 | docs/review/ 全文修正 |
| R2-01 BLOCKER | 采纳 | 簇 L（其方案全收，含静态禁止 hitl 后 manifest 可变节点——落为 approved 直达 release） |
| R2-02 BLOCKER | 采纳 | 簇 L（其推荐方案：Ledger authorization record + 特权 RPC 原子消费，bearer 不进 graph/checkpoint） |
| R2-03 BLOCKER | 采纳（取其第二方案） | §8.3：官方 gerrit/github adapter 由框架交付并纳入审计/版本 pin（broker 进程=可信计算基）；第三方扩展走其第一方案（无凭据子进程+broker 凭据原语）。框架范围+2 个 adapter，为保 D8 物理性的必要代价 |
| R2-04 BLOCKER | 采纳 | §8.5（其方案全收：分 socket/OS 用户/peer credential/worker 不可达/单命令原子/outbox） |
| R2-05 | 采纳 | §4.3.3 administrative finalize（ledger 级收尾，不经引擎与保留节点，先对账后关闭） |
| R2-06 | 采纳 | D12/§4.3.3 dispatch/审批/发布前复核 digest |
| R2-07 | 采纳 | 簇 M（其"active=执行中、paused 释放槽、FIFO"即定案） |
| R2-08 | 采纳 | §4.2.2 success_on + §4.2.5 release outcome 集 {released, release_failed} 及终态映射 |

## 汇总
- 三家全部新 issue、重开项、CLARIFY：**无一不采纳**（两处为等效/择案：Kimi N-07 与 Codex R2-03 在"官方 adapter 框架交付"上合并定案；Kimi N-12 取消除冗余而非双源校验）。
- 本轮无仲裁裁剪残留；B1/B2 两个上轮裁剪点三方一致接受，正式关闭。
- v0.3 复审关注点：(1) 簇 L 重排后的审批链时序是否闭合；(2) §8.5 RPC 权限模型是否够格承载 D8；(3) DSL v1 经簇 J 修复后是否可宣布闭合。
