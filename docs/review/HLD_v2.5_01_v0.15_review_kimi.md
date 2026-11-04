# 评审意见：HLD v2.5（第五轮顺带核对）+ 01_Contract_Spec v0.15（第十五轮定向复审）

**评审方**：Kimi　**日期**：2026-11-04
**对象**：docs/00_Framework_HLD_v2.5.md（仅附录 A22 所列改动）；docs/01_Contract_Spec_v0.15.md（仅 A3 中 v0.15 一条所列改动）
**材料**：两份上轮处置表、三家上轮原始意见、docs/research/quickbuild_business_logic.md（只读）、冻结基线 v1.0+E-01。

## 结论表

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| HLD v2.5 | **GO** | 0 | 0 | 0 | 1（K-01） |
| 01 v0.15 | **GO** | 0 | 0 | 0 | 0 |

## 负责人七项裁决判断表

| # | 裁决 | 判断 | 理由 |
|---|------|------|------|
| ① | UT∥静态审查并行；超时出报告、不得当通过 | **成立** | 机制自上轮闭合，本版无改动、无回归。 |
| ② | Quickbuild 默认取最新、Run 启动时解析固定（本系统取最新 Profile 快照） | **成立** | 任务指定的代价专项评价：v2.5 已如实写明全部代价——缺省与本系统选择分离（"这是 CodingSystem 的策略、不是 Quickbuild 的缺省"）、快照未经 reference 推广且自身构建失败更常见（首屏注明）、落后量不给无依据上界（无证据标 unknown）。未写明的残余代价只有一个：运维若用 Quickbuild 表单缺省手动构建，其基线（reference）与本系统（最新 Profile）不同——属操作习惯差异，已由"首屏显示实际快照编号"覆盖可见性。代价披露充分。 |
| ③ | Profile 严格匹配 + 放宽预案 | **成立** | 无改动、无回归。 |
| ④ | 目标范围只跑相关模块 | **成立** | 无改动、无回归。 |
| ⑤ | 以测试结果检验 AI | **成立** | 无改动、无回归。 |
| ⑥ | Quickbuild Base CL/默认最新 + 实测 | **成立** | "按构建号读取"的证据等级已校正为"已知构建号读取已证实、顺序扫描与按配置过滤 unverified"——与实测（Q3 读回 1213815/1213816 变量页、Q6 Recent Builds 仅 10 条且无备注搜索证据）一致。 |
| ⑦ | 超时重试成功可发布、须审批人确认（收窄后） | **成立** | 收窄未缩小知情面：被取代轮次仍首屏汇总列出；逐条确认限于当前 series 证据链（含 ci_plan/Review/基线构建 task）且绑定 (id, 内容 digest)；核销复核兜底。负责人"都要知道发生过超时"的本意完整保留。 |

---

## 第一部分：HLD v2.5（GO）

### A. 处置落实核验

- Q1–Q5 逐条落文：证据措辞校正（§7.6.1"最新"的含义重写）✓；后端能力加载期检查（§4.2.6 新增段）✓；retried 证据链扩大 + gaps_changed 协议修正（§4.3.5/§8.3 改为 ConsumeRejected + ledger 级映射、broker 不发 outcome——与 01"outcome 恒为执行后"一致）✓；purpose 编排推导 + base_mismatch 优先（§7A.4）✓；准入拒绝后 status 写明（规则③）✓。
- **两处取舍评估**：①未核销 task 达失联上限后按发布失败关闭（不停在发布节点）——**成立**：授权从未核销即确定无远端发布，可安全关闭并留 dispatch_loss_exhausted 证据；停在发布节点反而无出口。②新实例不等旧实例回收完成——**成立**：安全只要求"已核销者恢复执行"与"负向终局"等待静默（二者仍等 reclaimed）；未核销 token 无远端效应风险，epoch 隔离使旧实例无法 consume，专属 cgroup 使旧实例判定不受新实例影响。
- **记录更正一节**：两处更正与实测记录核对准确（缺省确为 Ref. Snapshot；已知构建号读取确有样本）。

### B. 改动面逐项核验

1. **Quickbuild 证据措辞**：与实测逐条一致（见裁决②⑥）；无过头亦无过度保守。
2. **后端能力加载期检查**：不误拒四份示例（全部 backend: local，检查空虚通过）；示例二改配 quickbuild 且暂存输入 unverified 时"位于 opt 回流之后 → 拒绝"的判定与 §11.3 用例一致；运行时防御（image_failed_exhausted + 不进修复环）为加载期规则的兜底，双层一致。
3. **retried 证据链扩大**：边界明确（当前 series 全部 task ∪ 供基线的 sys.baseline_build task），跨 Run 共享基线的并入规则写明。
4. **purpose 编排推导**：candidate/revert/repair 三分支确定；见 K-01（NIT）。
5. **base_mismatch 优先**：未决计划在 Run 关闭时记 abandoned（审计可见、不进状态机），无新无出口（fail_safe 为唯一出口，语义正确：输入不可信时撤销也无法验证）。

### 问题清单（第一部分）

**K-01（NIT，§7A.4 优化计划段）**
- 问题：purpose 推导规则"注册为产出 optimization_candidate 的节点提交 = candidate；使 tree_digest 回到计划 parent_tree 的撤销段 = revert；其余 = repair"——Coding Agent 的初始 patch 段（经 submit_patch、不经任何节点提交）落入"其余"，被标为 `repair`。原始业务改动被叫"修复"语义略歪；虽无功能影响（计划归属与"顶段判定"均不看它），但 §6.4 的逐段标注是多版本对比报告与审计的输入。
- 依据：§7A.4"series 的每一段带 purpose ∈ {candidate, repair, revert}，由编排推导" vs §6.4 patch series 含 Coding Agent 原始 patch 段。
- 候选改动：
  ```diff
  - 其余 = repair
  + 其余 = repair；初始 patch（Coding Agent 经 submit_patch 提交）与撤销段之外的框架段不带 purpose（ purpose 仅服务于优化计划生命周期，§6.4 的产出者标注不受影响）
  ```
  （或显式将初始段标为 `repair` 并注明该值在此仅表示"非优化计划相关段"。）
- 副作用：无（枚举语义不变，仅澄清）；配套测试：无需改动（可在 §11.3"撤销后 tree_digest 等价于父版本"用例的段标注断言中顺带固定初始段的处置）。

---

## 第二部分：01_Contract_Spec v0.15（GO）

### 上一轮处置核验

本方第十四轮零 issue GO，无待核条目；处置表 W1–W5 落文核验通过：专属 domain cgroup + `cgroup.events` populated=0 递归判定 + launcher 写入的 cgroup_path/cgroup_generation 可信绑定 ✓；失联次数上界 loss_count/max_task_losses（缺省 2）与两种终局出口 ✓；新实例拉起不等 reclaimed、未核销者立即重派 ✓；出向续跑 execute/probe 分述 ✓；ReleaseTaskState 入模型并入 A0 ✓。记录更正（Y2 pid 复用判据）与正文一致。

### 五条时间线 × 崩溃点 × 期限到期 × 失联上限走查（每格恰一出口）

1. **正常**：dispatch→granted→执行→outcome；各崩溃点由 receipt/CF-LED 覆盖。✓
2. **核销后发生前崩溃**：新实例立即上线（不等回收）；已核销须等旧实例 reclaimed 后替代协议重派 → resumed → 对账 → proceed → 执行（CF-AUTH-20e：子树迟迟不空时已核销 task 等待+告警，无执行权授予）。✓
3. **发生后崩溃**：proceed 后 ACK 前/后失联均属 awaiting_outcome 到期 → retiring → 回收 → 新 epoch 恰一次恢复；期限与完成事件以 phase CAS 互斥（CF-AUTH-20f：完成先交则期限失效、失联先判则后到结果被连接守卫拒）。✓
4. **indeterminate**：锁存；周期任务 probe_interval 发只探测；awaiting_probe 到期不 retiring（不误判失联）；not_happened + 持有者未静默 → retire_requested → 回收 → 静默后新 probe_seq 重探 → 负向映射恰一次。✓
5. **实例存活但单 task 失联**：期限到期 → retiring → 除 heartbeat 全拒 → launcher cgroup.kill → populated=0 才 reclaimed → 新实例 → 恢复；loss_count +1；达 max_task_losses：未核销 → 撤销授权 + release_failed(dispatch_loss_exhausted) 关闭（确定无发布）；已核销 → 保持 publishing、只经人工裁决。同实例其他 task 重派不计数。✓

**并存期双重执行检查**：无——旧实例命令一律被拒（epoch 不现行/retiring）；未核销 token 旧实例无法 consume（epoch 隔离）；已核销者恢复执行与负向终局都等 reclaimed；两实例各有专属 cgroup 子树，populated 判定互不干扰。**新循环检查**：无——回收失败只告警不重派（人工）；静默确认重试为周期任务且以 reclaimed 终止；重执行次数受 loss_count 上界封死。

### 出向分述一致性

§5.1 的 execute/probe 分述与 §2.2d（未核销直派/已核销先静默/indeterminate 发 probe）、C-11a（probe 三出口）逐句一致；probe 非法组合（未核销或非 indeterminate 的 probe）编排拒绝生成；"同 token 至多一个 intent"不分型共享约束一致；CF-IPC-10 按载荷类型 × recovery_state 分组、probe 不以"最终执行完成"为期望——表述无诱导性。

### 问题清单（第二部分）

无（BLOCKER / MAJOR / MINOR / NIT 均无新发现；前轮已关闭条目 diff 复核无重开）。

### 同步项复核

本版 HLD 改动对应的 01 同步需求（gaps_changed 已在 HLD B-7 登记 ConsumeRejected 枚举落位、后端能力加载期检查、purpose 推导、证据链扩大、base_mismatch 优先级等）逐条核对均在 HLD v2.5 附录 B 第 7 组登记，不重复报告、不计入本部分结论。

---

## 交付备注

本文件为唯一提交内容；被审文档未改动。
