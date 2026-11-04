# HLD v2.5 第五轮定向复审处置表（→ v2.6）

裁决输入：Kimi **GO**（0 / 0 / 0 / 1 NIT）；Claude Code **GO**（0 BLOCKER / 0 MAJOR / 3 MINOR / 1 NIT）；Codex **NO-GO**（0 BLOCKER / 1 MAJOR / 2 MINOR）。合计 8 条意见，归并为 5 个独立问题，**全部采纳**（1 处部分采纳，理由写明）。

三家同时指向一处：v2.5 新加的段 purpose 推导规则没有互斥顺序。Codex 判为 MAJOR（Optimization 亲自撤销时会被当成新候选，再建一个计划，破坏确定性撤销与轮数上界），Claude Code 判为 MINOR 并补了"未决计划期间的非撤销段应拒绝"，Kimi 判为 NIT（初始段落入 repair）。按影响取 MAJOR。

---

## 负责人七项裁决

| # | 裁决 | Kimi | Claude Code | Codex | 本版处理 |
|---|------|------|-------------|-------|----------|
| ① | UT 与静态审查并行；超时必须出报告 | 成立 | 成立 | 成立 | 保留 |
| ② | Quickbuild 取最新并固定 | 成立 | 有条件成立：漏写 Profile 与构建根的版本差距；"失败更常见"是推断 | 有条件成立："未经推广"不应无条件标注 | 保留；代价说明按证据重写（R3） |
| ③ | Profile 严格匹配 + 小改动复用预案 | 成立 | 成立 | 成立 | 保留 |
| ④ | 目标模块与相关范围验证 | 成立 | 成立 | 成立 | 保留 |
| ⑤ | 以测试结果与多版本报告检验 AI | 成立 | 成立（purpose 优先级有缺口） | 成立（purpose 规则须修） | 保留；purpose 判定改为互斥顺序（R1） |
| ⑥ | Quickbuild 显式 base 与读回核对 | 成立 | 成立 | 成立（能力检查须按实际所需） | 保留；能力检查按实际所需（R2） |
| ⑦ | 重试成功可发布，审批人确认 | 成立 | 成立 | 成立 | 保留 |

---

## MAJOR

| # | 问题 | 来源 | 处置与采用方案 | 理由 |
|---|------|------|---------------|------|
| R1 | 段 purpose 推导规则不互斥：Optimization 在判定 neutral / loss / inconclusive 后亲自撤销，同时满足"优化节点提交 = candidate"与"回到父版本 = revert"，可能为撤销再建计划（准入不足时撤销还会被拒、计划卡死）；未决计划期间 Compiler / UT 的非撤销段被当作 repair 接受，等于允许了被禁止的 AI 修复；初始段的 purpose 未定义 | Codex H25-01（MAJOR）、CC H25-02（MINOR）、Kimi K-01（NIT） | **合并**：四步互斥判定——① 撤销优先，且只匹配**当前**未决计划的父版本（取 Codex，防止碰巧等于历史树）；② 未决计划期间不满足 ① 的提交一律拒绝 `E-CANDIDATE-NOT-REVERT`（取 CC）；③ 无未决计划时优化节点提交为 candidate 并做准入；④ 其余为 repair，开发者初始段为 initial（取 CC / Kimi）。删去"待验证计划的后续修复段归属该计划" | 撤销必须先于候选判定，否则确定性撤销与轮数上界都不成立 |

## MINOR / NIT

| # | 问题 | 来源 | 处置 |
|---|------|------|------|
| R2 | 可比性能力检查覆盖所有阈值 gate，误拒只用绝对指标（absolute SPEC）的非发布验证 | Codex H25-02；CC H25-04（措辞） | 采用。只有需要 A/B 的判定（relative SPEC、regression_pct、优化收益、必需的 Bench 发布证据）要求可比性能力；无法确定为 absolute-only 时按需要 A/B 处理。同时写明"可能面对非空 series"的路径语义，并声明 LocalGbsBackend 能力为 verified |
| R3 | "最新 Profile 快照"的代价说明：无条件标注"未经推广"不准确（latest 可能等于 reference，显式指定的快照可能已推广）；"失败更常见"是推断；漏写源码（Profile）与构建根（reference）版本差距拉大带来的环境性构建失败 | Codex H25-03、CC H25-01 | **采用两家措辞部分**：推广状态按证据显示；失败率标为设计推断；补写版本差距，失败时 Build / ImageReport 附两者编号。**未采用 CC 的"判为环境性失败（env_skew_suspected）即不产修复 patch"**：目前没有可确定的判据，CC 自己也写"待 P6 以真实数据确定"；在判据缺失时自动停止修复是一个无定义的判断，首期只提供证据、不设自动规则，P6 取得数据后再定 |
| R4 | base_mismatch 优先后，若 image_failed_exhausted 被路由到 terminal，未决计划使 terminal 成功被拒且没有出口 | CC H25-03 | 采用。terminal 命中时若有未决计划，以 `pending_plan_at_terminal` 按 fail_safe 关闭，计划在审计中记 abandoned |

## 下一轮建议

HLD 本轮除 purpose 规则外均为措辞与边界，purpose 规则已按两家方案合并成互斥顺序。建议随 01 v0.16 再做一次定向核对，只看 A23 所列改动。
