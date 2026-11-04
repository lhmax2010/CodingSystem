# 评审意见：HLD v2.4（第四轮）+ 01_Contract_Spec v0.14（第十四轮）

**评审方**：Kimi　**日期**：2026-11-04
**对象**：docs/00_Framework_HLD_v2.4.md；docs/01_Contract_Spec_v0.14.md
**范围**：定向核对（处置落实 + 两版改动面 + 组合/时间线走查），未改动部分不重审。
**材料**：两份处置表、三家上轮原始意见、docs/research/quickbuild_business_logic.md（只读）、冻结基线 v1.0+E-01。

## 结论表

| 部分 | 结论 | BLOCKER | MAJOR | MINOR | NIT |
|------|------|---------|-------|-------|-----|
| HLD v2.4 | **GO** | 0 | 0 | 0 | 0 |
| 01 v0.14 | **GO** | 0 | 0 | 0 | 0 |

## 负责人七项裁决判断表

| # | 裁决 | 判断 | 理由 |
|---|------|------|------|
| ① | UT 与静态审查并行；超时出报告、不得当通过 | **成立** | 汇合必经（规则①③共用）+ §4.3.5 结构保证自上轮起闭合，本版清理了残留措辞（"汇合必经"适用范围表述统一、§11.3 旧断言修正）。 |
| ② | Quickbuild"最新"在 Run 启动时解析固定 | **成立** | v2.4 取"最新 = 当时最新可用 Profile 快照"——这正是实测（Q1）证实的 Quickbuild 默认行为（MODIFY 留空则包保留所选 Profile manifest 版本），裁决意图与证据能力对齐；被测 series 的源码身份由 ExpectedSourceManifest + 暂存输入通道另行证明（Codex 的三层区分成立）。 |
| ③ | Profile 严格匹配 + 放宽预案 | **成立** | 自上轮起闭合（伪探针前提 + 非劣开启条件），本版无改动，无新异议。 |
| ④ | 目标范围只跑相关模块 | **成立** | 撤销后范围不缩减的出口问题（Codex 上轮条件）由 M4 的"撤销后重验证按常规义务"覆盖：范围只增不减 + 撤销段推进 series + 常规义务重验证，无悬挂。 |
| ⑤ | 以测试结果检验 AI | **成立** | Codex 的条件（测试证据须来自所声称源码与可比输入）由 M2/M3 满足：source 身份证明 + 实际/发布 build.conf 分列 + unknown 即不可比；报告时点与 digest 绑定（N2/N5）补齐。 |
| ⑥ | Quickbuild 可加 Base CL、否则默认最新；实测 | **成立** | Tizen 侧"显式 base"如实落为"Profile 快照编号 + 个别包 commit 覆盖"；能力按 verified/unverified/unsupported 登记——"未证实"未被写成"不支持"（原裁决的潜在过头处已修正）。 |
| ⑦ | 超时后重试成功可发布，须审批人逐条确认（本版收窄确认范围） | **成立** | 收窄后仍满足"开发与审批都要知道发生过超时"的本意：当前 series 证据链上的 retried 逐条确认且绑定 (条目 id, 内容 digest)（内容变化即未确认），被取代轮次的重试仍在首屏**汇总列出**——知情面未缩小，缩小的只是与本次发布无关版本的逐条勾选负担。审批-核销间的新增/变化由核销复核 + gaps_changed 兜底。代价：被取代轮次上的系统性环境故障（如板子抖动）得到的审批关注更少——但它们仍显示在首屏，且当前证据链不受影响，取舍成立。 |

---

## 第一部分：HLD v2.4（GO）

### A. 处置落实核验

- M1–M5 与 N1–N9 逐条对到正文（§7.6.1 证据等级重写、ExpectedSourceManifest + 暂存通道、actual/published build.conf 分列、优化计划 inconclusive→撤销→提交即 reverted、运行时准入 E-PLAN-NO-CAPACITY、retried 收窄 + digest 绑定 + gaps_changed、登录超时固定 fail_safe、规则②取交不动点、验证资产净 diff 重算、Review final 不引用未生成报告、base_mismatch 归 image_failed_exhausted——本方上轮 K-01、external_timeout_min 缺省——K-02，均落实）。同步项补登（含 gaps_changed 的 ConsumeRejected/枚举同步）已在附录 B 第 7 组。
- **未采用项的理由评估**：①Quickbuild 脚本版本不按时间窗口视为可比——成立：时间窗口只降概率不是证据，且"读不到就忽略等于静默放行"；②不可比不能经人工确认满足 Bench 谓词——成立：与负责人"以测试结果为准"原则一致，人不能替测量补结论；③不新增 reverted_validating/failed 状态——成立：重验证已由规则①③与审批 CAS 强制，重复建态是冗余约束；④撤销后重验证失败按普通修复流程——成立：把仍可修复的业务 patch 直接 fail_safe 的替代方案代价更大。
- **记录更正一节**：三处更正与 v2.4 正文核对均准确（配额归还条件、Artifact 10 天表述、G' 描述以正文为准）。

### B. 改动面逐项核验

1. **§7.6.1 证据等级**：与实测记录逐条比对——"已证实"项（Profile 快照锁定、单包覆盖、Add、BUILD_NOTES 标记、全量清单读回、base 快照编号读回、发布 build.conf 摘要、Recent Builds 10、保留政策、≥3 并发父请求）各有 Q1/Q2/Q3/Q5/Q6/Q8 证据；"unverified"项（批量覆盖上限、Remove、暂存通道、按构建号读取、取消联动子构建、产镜像工程）在实测中确实未证实；build.conf 实际消费值不可得的边界如实标注。无过头、无过度保守。
2. **被测源码身份证明 + 实际输入证明**：ExpectedSourceManifest（snapshot + series + 逐包 base + expected tree）+ 已验证暂存输入通道 + 未验证拒绝非空 series（backend_source_input_unsupported）闭合；Quickbuild 首期退化为绝对测量、A/B 用本地后端的替代路径明文写出，不存在"不可用而未说明"。
3. **优化计划出口**：不可比→inconclusive（原因 comparison_unverifiable）→撤销；撤销段提交事务内即 reverted（判据 tree_digest == parent_tree，不依赖后续验证）；撤销后重验证 = 常规义务（失败走普通修复环或 fail_safe）；创建准入（优化环 ≥2、修复环 ≥1 剩余）保证任何已建计划必有撤销容量。逐状态走查无无出口、无双出口、无绕过。
4. **超时重试确认收窄 + gaps_changed**：确认面 = 当前证据链（release_evidence 各报告所在 task）的 retried，绑定 (id, digest)；核销复核失败 → 不核销 + release_failed(gaps_changed) → 冻结映射关闭、新建 Run。与"release_outcome 恒为执行后"的关系已登记 B-7（ConsumeRejected/枚举同步项，见下）。

### C. 组合场景复核

上轮组合场景在 v2.4 规则下重走：新增"读回不可比"分支使 bench_gate fail-closed → fail_safe（正确出口）；撤销后重验证失败走普通修复环（业务 patch 不被连坐）；范围增长不被撤销缩小；retried 收窄后审批首屏 = 当前链逐条 + 历史汇总。无无出口/双出口/静默放行。

### 问题清单（第一部分）

无（BLOCKER / MAJOR / MINOR / NIT 均无新发现）。

---

## 第二部分：01_Contract_Spec v0.14（GO）

### 上一轮处置核验

本方第十三轮零 issue GO，无待核条目；处置表 Z1–Z6 落文核验通过：阶段期限（phase + phase_deadline，提交时刻起算、重启不重置）✓；周期驱动只探测 + 持有者回收（retire_requested）✓；只探测拆为独立出向命令 ✓；launcher 经 cgroup 回收与按 cgroup 判静默 ✓；reconciliation worker 协议错误按 synthetic_worker_loss ✓；记录更正（Y2 的 pid 复用判据）与正文一致 ✓。

### 五条时间线 × 崩溃点 × 阶段期限走查（每格恰一出口）

1. **正常**：dispatch→consume（granted）→执行→outcome，phase 逐段推进。✓
2. **核销后发生前崩溃**：holder 更替重派（已核销先静默）→resumed→对账→proceed→执行→outcome；阶段期限到期（实例存活但 task 无进展）→retiring→launcher 回收→新实例恰一次恢复（CF-AUTH-20）。✓
3. **发生后崩溃**：对账 happened→released 映射；not_happened→原子许可；proceed 后 ACK 前/后失联均属 awaiting_outcome 到期分支（覆盖"许可之后失联"）。✓
4. **indeterminate**：锁存（换实例/换 epoch 不清除）；周期任务按 probe_interval 发 release_probe_dispatch；awaiting_probe 到期不 retiring（不误判失联）；not_happened + 持有者未静默 → retire_requested → 回收 → 静默后新 probe_seq 重探 → 负向映射恰一次（CF-AUTH-17c/17e）。✓
5. **实例存活但单 task 失联**：阶段期限 → retiring → 除 heartbeat 全拒 → cgroup.kill → reclaimed → 新 epoch 恢复。✓

**循环重启检查**：周期只探测与持有者回收不能形成循环——retiring 单向（旧实例 hello 被拒）、持有者回收一次到位、静默后负向映射即终局；re-probe 若 happened → released 映射（迟到落地被正确识别），若 indeterminate → 下一周期。无循环。

**只探测通道能否执行发布**：不能——ReleaseProbeDispatch 结构性不含 release_plan_ref 与发布内容（只含 probe_targets + fencing + probe_seq）；部署契约要求 probe 路径只构造只读 adapter 客户端、不加载写凭据原语；CF-AUTH-17f 断言篡改 kind=execute、复用旧 request_id、伪造旧 epoch、只探测后发 release_outcome 均被拒、FakePublisher 写计数恒为 0。闭合。

### 其余核验

CommandName=21、注册表、A0（含 ReleaseProbeDispatch、ReleaseDispatchPayload）、§5.1 文字面四处一致；静默判定改"租约 reclaimed ∧ 实例 cgroup 为空"覆盖 setsid 逃逸，CF-AUTH-09d 补前置、09e 反向例；§2.2(c) 残留措辞已指向 C-11a；全命令统一处理序与 hello 例外、retiring 仅受理 heartbeat 一致；contract_version 升 dev3 与破坏性声明一致。

### 问题清单（第二部分）

无（BLOCKER / MAJOR / MINOR / NIT 均无新发现；前轮已关闭条目 diff 复核无重开）。

### 同步项复核

v2.4 新增同步项（gaps_changed 的 ConsumeRejected 枚举落位、E-PLAN-NO-CAPACITY、backend_source_input_unsupported、comparison 三值、succeeded_with_gaps、E-SKILL-EMPTY-SERIES 等）已逐条核对均在 HLD v2.4 附录 B 第 7 组登记，不重复报告、不计入本部分结论。

---

## 交付备注

本文件为唯一提交内容；被审文档未改动。
