# S0-A:Repair Loop Spike（修复闭环 + LLM 修复准确率）

**类型**:Sprint 0 补充 spike（进 Sprint 1 前必须 PASS）
**前置**:Sprint 0 S0-01~S0-09 已完成
**触发来源**:change_3（ChatGPT + Kimi 外部 review 暴露的最致命未验证假设）
**预估工时**:3-4 天

---

## 目标

验证整个系统**最核心、风险最高、但 Sprint 0 完全没碰**的部分：**LLM 真的能不能修对 + 修复闭环能不能安全跑通**。

Sprint 0 验证了"失败 → 解析 → 收集证据 → 组装 EvidencePacket"的前半段管线。S0-A 验证后半段：**EvidencePacket → LLM 生成 patch → 验证 → 应用 → rebuild → bounded repair**，并用 A/B 测试回答两个根基问题：
1. negative_facts 到底有没有用？
2. 喂 EvidencePacket 比直接塞原始日志，LLM 修得更准吗？（"比单技能工作流强"的根基）

**这不是 mock。这次必须真调 LLM、真生成 patch、真 apply、真 rebuild。**

---

## 验证基线

- 用 Sprint 0 的 pkgmgr-info（已验证可构建）
- 准备 3 个真实错误（来自 S0-04 的真实触发场景，不造假）：
  - E1：missing include dir（漏配 include path）
  - E2：missing target_link_libraries（漏链库）
  - E3：typedef/header signature drift（改 header 调用方没同步 —— 即 S0-04 的级联场景）

---

## Part 1:修复闭环机制验证（Repair Loop）

对每个错误，跑完整闭环并记录：

```
1. git worktree 创建（隔离，不碰主代码）
2. build → fail
3. LogErrorParser 解析（用 Sprint 0 已验证的能力）
4. EvidenceCollector 收集证据 → EvidencePacket
5. RawDataDetector 检查（Sprint 0 已验证）
6. 真调 LLM，给 EvidencePacket，让它生成 patch
7. patch validate（格式 / 是否在 worktree 内 / 是否超 max_patch_lines）
8. patch apply 到 worktree
9. rebuild（1 次 verification，超时 verify_timeout_sec=300）
10. 判定：rebuild 通过 = 修复成功；失败 = 进 bounded repair 或 fail-safe
11. 生成 trace.json / events.jsonl / failure envelope（如失败）
12. worktree cleanup
```

### 必须专门测的失败路径（这是 bounded repair 的核心，不能只测 happy path）

| 失败场景 | 期望行为 |
|---|---|
| patch 1 格式错误（无法 parse）| 不 apply，记录，允许第 2 次 patch generation |
| patch apply 冲突 | 记录冲突，允许 1 次 repair |
| rebuild 失败（patch 没修对）| 收集新错误，允许第 2 次 patch（这是 bounded repair 的第 2 次） |
| 第 2 次 patch 后 rebuild 仍失败 | **不允许第 3 次**，fail-safe，emit failure envelope（验证 bounded repair 上限：最多 2 patch + 1 rebuild）|
| 目标不是 git repo | emit contract_violation（按 Compiler Agent v5.2-RC2.3）|
| worktree 有未提交改动 | fail-safe，不强行操作 |

### Part 1 验收标准

- [ ] 3 个错误的完整闭环都能跑通（不要求都修对，要求流程安全跑完）
- [ ] worktree 隔离生效：主代码全程无改动（用 `git status` 主仓库验证）
- [ ] bounded repair 上限严格生效：第 2 次失败后不会有第 3 次 patch
- [ ] 所有失败路径都正确进入 fail-safe / failure envelope，不会无限重试、不会污染主代码
- [ ] trace / events 完整可追溯
- [ ] cleanup 后 worktree 被正确清理

---

## Part 2:LLM 修复准确率 A/B 测试（验根基假设）

这是 S0-A 最高价值的部分。用上面 3 个错误（E1/E2/E3），做两组对照实验。

### A/B 测试 1:negative_facts 有没有用

对每个错误，构造两个 prompt 变体喂给同一个 LLM：
- **变体 A**：完整 EvidencePacket（含 negative_facts）
- **变体 B**：EvidencePacket 去掉 negative_facts（只留 facts + log_excerpt）

观察：
- 哪个变体生成的 patch 编译通过率高？
- 哪个变体的 patch 语义更正确（人工 review）？
- 变体 B（无 negative_facts）是否出现更多"瞎猜原因"的幻觉（比如 undefined_reference 错误，B 去猜 namespace 而 A 直接定位到缺库）？

### A/B 测试 2:EvidencePacket vs 直接塞日志（验"比单技能工作流强"）

对每个错误，构造两个 prompt 变体：
- **变体 C**：EvidencePacket（我们的方案）
- **变体 D**：直接把原始 build log（截断到相近 token 量级）塞给 LLM（模拟单技能 Skill Workflow）

观察：
- **修复准确率**：C vs D，哪个 patch 编译通过率高 / 语义正确率高？
- **token 消耗**：C vs D 各用多少 token？
- **关键结论**：C 是否在"更少 token"的同时"修得更准或相当"？如果 C token 少但修得更差，这是对整个设计的警告信号，必须报告。

### Part 2 验收标准

- [ ] 每个错误 × 4 个变体（A/B/C/D）都真调了 LLM，记录 patch
- [ ] 每个 patch 都做了：编译通过性测试 + 人工语义 review
- [ ] 输出对比表：变体 × 错误 → (编译通过? / 语义正确? / token 数)
- [ ] 给出明确结论：
  - negative_facts 是否提升准确率（A vs B）
  - EvidencePacket 是否在更省 token 下保持/提升准确率（C vs D）
- [ ] 如果结论是负面的（negative_facts 没用 / EvidencePacket 不如塞日志），**如实报告**，不粉饰 —— 这种负面结论对项目方向极其重要

---

## 重要约束

- **真调 LLM**：用 PM 提供的模型环境（Claude / Codex / GPT-4，PM 指定）。这次不允许 mock LLM。
- **不污染主代码**：所有操作在 git worktree，主仓库全程 `git status` clean。
- **raw log 只放 /tmp**：A/B 测试 2 的"直接塞日志"变体 D，日志内容只在运行时构造，不提交 repo；报告里只记 token 数和结论。
- **patch 内容可入库**（作为产物），但要 bounded（符合 max_patch_lines）。
- **人工语义 review 必须做**：编译通过 ≠ 修对了（可能编译过但逻辑错）。每个 patch 要人工判断"这是不是正确的修复"。
- **不自己判 PASS**：跑完报告数据，PM 确认。

---

## 产物

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/spike_A_repair_loop.md`
- `spike_reports_data/spike_A_repair_loop.py`（闭环脚本）
- `spike_reports_data/spike_A_ab_test_results.json`（A/B 对比数据）
- `spike_reports_data/spike_A_patches/`（生成的 patch，bounded）
- A/B 测试的 prompt 变体记录（去敏后）

---

## 为什么这个 spike 优先级最高

整个系统的价值主张是"用 EvidencePacket 让 LLM 修得又准又省 token"。Sprint 0 验了"能造出 EvidencePacket"，但**没验"LLM 拿着它真能修对"**。如果这个假设不成立，CNEI 再漂亮也是空中楼阁。S0-A 直接回答这个生死问题 —— 应该在投入 Sprint 1 大规模开发**之前**回答。
