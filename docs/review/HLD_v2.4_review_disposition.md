# HLD v2.4 第四轮三方评审处置表（→ v2.5）

裁决输入：Kimi **GO**（0 / 0 / 0 / 0）；Codex **GO**（0 BLOCKER / 0 MAJOR / 1 MINOR）；Claude Code **GO**（0 BLOCKER / 0 MAJOR / 4 MINOR / 1 NIT）。HLD 部分**三家首次一致 GO**。合计 6 条意见，归并为 5 个独立问题，**全部采纳**。上一轮处置表的全部条目三家均核验落实；四处未采用评审方方案的取舍理由，三家均判成立（Claude Code 对其中两处本方方案明确撤回）。

---

## 负责人七项裁决：评审方意见与本版处理

| # | 裁决 | Kimi | Codex | Claude Code | 本版处理 |
|---|------|------|-------|-------------|----------|
| ① | UT 与静态审查并行；超时必须出报告、不得当通过 | 成立 | 成立 | 成立 | 保留，无改动 |
| ② | Quickbuild 默认取最新，在 Run 启动时解析固定 | 成立 | 有条件成立 | 有条件成立 | **保留"取最新并固定"**。校正依据：Quickbuild 表单的缺省其实是滚动的 Ref. Snapshot（reference），"最新 Profile 快照"是本系统的选择，二者不是同一回事；代价（快照未经推广）写入正文并在审批首屏注明（Q1） |
| ③ | Profile 严格匹配 + 小改动复用预案 | 成立 | 成立 | 成立 | 保留，无改动 |
| ④ | 每个 Run 必须有目标模块，只跑相关模块 | 成立 | 成立 | 成立 | 保留，无改动 |
| ⑤ | 以每轮测试结果与多版本对比报告检验 AI | 成立 | 成立 | 成立 | 保留，无改动 |
| ⑥ | Quickbuild 可加 Base CL，否则默认最新 | 成立 | 成立 | 有条件成立 | 保留；"按构建号读取"一项证据等级写得过保守，已校正（Q1） |
| ⑦ | 超时后重试成功可发布，须审批人确认（v2.4 收窄范围） | 成立 | 成立 | 成立（附精度缺口） | 保留；证据链边界补上 ci_plan、Review 与提供基线的内部构建（Q3） |

---

## MINOR / NIT

| # | 问题 | 来源 | 处置与采用方案 | 理由 |
|---|------|------|---------------|------|
| Q1 | 证据等级两处与调查不符：①把"最新 Profile 快照"说成 Quickbuild 的缺省（实测缺省为 Ref. Snapshot），并给出"落后量等于快照发布间隔"这一没有依据的上界；②"按构建号读取"整体标为未证实，实际按已知构建号读取已做过；③由一个样本未产镜像推出整个配置不产镜像 | Codex H24-01、CC H24-01 | **合并采用**：缺省与本系统选择分开写，首屏注明"快照未经 reference 推广"（取 CC 的代价说明）；删去落后量上界，无证据时标 unknown（取 Codex）；已知构建号读取标已证实，按构建号扫描与按配置过滤（构建号跨配置交错，取 CC）标 unverified；镜像能力改为"样本未产镜像、其他组合未证实"（取 Codex） | 两家指向同一事实错误，各补一侧细节 |
| Q2 | 首期 Quickbuild 实际只能做空 series 构建与绝对测量，但拒绝发生在 RPM 阶段之后的运行时、节点 status 未定；风险表与分期未写明 | CC H24-02 | **采用 CC**：§4.2.6 增后端能力的加载期检查（构建暂存输入或可比性未验证而流水线需要相应能力 → 拒绝加载）；运行时防御返回 image_failed_exhausted(backend_source_input_unsupported)、不进修复环；R15 与 P6 gate 写明 Quickbuild 在能力未验证时的角色 | 配置错误在加载期暴露，不浪费一次 RPM 构建 |
| Q3 | retried 证据链只按 release_evidence 划定，漏掉 ci_plan、Review 与提供基线的 sys.baseline_build；"broker 返回 release_failed(gaps_changed)"与核销拒绝协议不符（broker 只在实际执行后发 outcome） | CC H24-03 | **采用 CC**：证据链 = 以当前 series 分派的全部 task ∪ 提供基线的 sys.baseline_build task（其重试并入本 Run 清单）；核销复核失败改为 ConsumeRejected(gaps_changed) + 编排 ledger 级 release_failed 映射 | 被批准的发布计划本身来自一次超时重试，审批人应当知道 |
| Q4 | 段 purpose 若由提交方自报，Optimization 可把候选报成 repair 绕过计划与收益验证；存在未决计划时 base_mismatch 与确定性撤销各给一个出口 | CC H24-04 | **采用 CC**：purpose 由编排推导（优化节点提交 = candidate；回到计划父版本的确定性撤销 = revert；其余 = repair）；base_mismatch 优先，直接 fail_safe、不产撤销段，未决计划在审计中记 abandoned | 收益必须实测证明是 D18 的核心，不能留自报口子 |
| Q5 | 准入拒绝后 campaign 模式返回哪个 status 未定 | CC H24-05 | 采用。per_patch → no_further_gain；campaign 按当前 series 有无净变更选 no_further_gain / no_gain_found | — |

---

## 记录更正（上一轮处置表 HLD_v2.3_review_disposition.md）

- **负责人裁决②**："这正是 Quickbuild 自身不指定版本时的行为（实测已证实）"不准确。实测的表单缺省是 `BUILD_REFERENCE=Ref. Snapshot`（滚动 reference）；"最新可用 Profile 快照"是 CodingSystem 自己的选择，二者等价性未证实（Codex、Claude Code 指出）。
- **M1**：其中"按构建号逐个匹配标记（按构建号读取为推断方案）"的证据等级写得过保守，按已知构建号读取单个构建已有样本证据，未证实的是顺序扫描与按配置过滤（Codex、Claude Code 指出）。

## 下一轮建议

HLD 部分三家已一致 GO，本轮只处理了 MINOR / NIT，均为证据措辞与边界补全，不改架构。建议 **HLD 不再单独起一轮全面评审**，在 01 的下一轮复审中顺带核对本版改动（A22）即可。
