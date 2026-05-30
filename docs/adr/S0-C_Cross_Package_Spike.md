# S0-C:跨包最小验证 Spike

**类型**:Sprint 0 补充 spike（进 Sprint 1 前必须 PASS）
**前置**:Sprint 0 S0-01~S0-09 已完成
**触发来源**:change_3（外部 review 指出"扛规模/跨包"是立项卖点但 Sprint 0 零验证）
**预估工时**:2 天

---

## 目标

Sprint 0 全程在**单个包**（pkgmgr-info）上验证。但这个系统**立项的根本卖点**是"比单技能 Skill Workflow 更能扛规模、能处理跨包联动"（单技能工作流只能处理单个 RPM 包）。

跨包能力 Sprint 0 **完全没验证**。S0-C 做一个**最小验证**：证明 CNEI 至少能处理"包 A 的改动导致包 B 编译失败"这一最基本的跨包场景。

**这不是 OS 级规模化验证**（那是 S0-10 Scale Spike，验 gbs/chroot/scip-clang，属 Phase 1.5）。S0-C 只验"两个包之间的最小跨包联动",回答"跨包符号引用这条路通不通"。

---

## 验证基线

找 **2 个有真实依赖关系的 Tizen 包**：
- 包 A（provider）：提供 public header / 库，被 B 依赖
- 包 B（consumer）：include 了 A 的 header / 链接 A 的库

候选方向（PM 或 build team 协助定位，Codex 在当前可拉取的 Tizen repo 里找）：
- pkgmgr-info 本身依赖一些基础库（如 capi-base-common / dlog / glib），可作为 provider-consumer 关系的素材
- 或找两个已知有依赖的 appfw 层包

如果当前公开 Tizen repo 拉不到合适的有依赖包对，**停下来报告**，由 PM 提供包对，不要硬凑。

---

## 验证场景

制造一个真实的跨包失败（不改业务逻辑，模拟真实开发场景）：

```
场景：包 A 的 public header 改了一个被 B 使用的符号
  （比如改了一个函数签名 / 删了一个 typedef / 改了一个 struct 字段）
  → 重新编译包 B → B 失败（因为 B 用的还是旧接口）
```

然后验证 CNEI 在处理 **B 的编译错误**时：

### 核心验证点

1. **跨包符号引用**：B 报错说找不到 / 用错了某个符号，CNEI 能否定位到这个符号**定义在包 A**（而不是只在 B 的范围里找，找不到就报 negative_fact）？
2. **provenance 标注**：CNEI 的 fact 能否标明"这个符号来自包 A（外部包）"？
3. **跨包 negative_fact**：如果 CNEI 只能看 B 的范围（看不到 A），它的 negative_fact 是否诚实标注"未检查外部包 A"（scope 限定），而不是错误地断言"符号不存在"？
4. **EvidencePacket 完整性**:给 B 的错误生成的 EvidencePacket，是否包含足够信息让 LLM 理解"这是 A 改了接口导致的"，而不是误导 LLM 去改 B？

### 重点观察 primary/cascade 跨包形态

如果 A 改一个符号导致 B 里多处失败，这是**跨包的 primary/cascade**：
- primary 根因在包 A（接口变更）
- cascade 表现在包 B（多处引用失败）
- 观察:当前的 primary/cascade 启发式（单 build 内"第一个 error"）在跨包场景下表现如何？大概率会失效（因为 primary 根因根本不在 B 的编译错误里，而在 A 的改动里）。**如实记录这个局限** —— 这正好印证 ADR-001 里 failure_causality_graph 跨包因果的必要性。

---

## 验收标准

- [ ] 找到 2 个真实有依赖的 Tizen 包（或 PM 提供）
- [ ] 成功制造 A 改动 → B 失败的真实场景
- [ ] 记录 CNEI 处理 B 错误时：
  - 能否定位符号来自 A（能 / 不能 / 部分）
  - provenance 是否标注外部包来源
  - 跨包 negative_fact 是否诚实（scope 限定，不瞎断言）
  - EvidencePacket 是否足以让 LLM 理解跨包根因
- [ ] 明确记录当前单 build primary/cascade 启发式在跨包场景的表现（大概率失效，如实记录）
- [ ] 给出结论：CNEI 当前的跨包能力到什么程度？距离"处理跨包联动"还差什么？（这是 ADR-001 Layer 0/1 规模化设计的真实输入）

---

## 重要约束

- 不改业务逻辑，只模拟真实接口变更场景
- raw log 只放 /tmp
- 不污染主代码（worktree 隔离）
- **如果当前 CNEI（Phase 1A Live 模式）跨包能力不足，如实报告"不足"**，不要为了 PASS 硬凑。这个 spike 的价值就是"诚实测出跨包能力的边界",为 Phase 1.5 规模化设计提供真实输入。
- 不自己判 PASS,报告数据 PM 确认。

---

## 产物

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/spike_C_cross_package.md`
- `spike_reports_data/spike_C_cross_package.py`
- `spike_reports_data/spike_C_cross_package_results.json`

---

## 为什么需要这个 spike

立项 PPT 和 ADR-001 都把"扛规模、跨包"作为 Coding System 优于单技能 Skill Workflow 的核心卖点。但 Sprint 0 的所有证据都在单包上。**如果不做哪怕一个最小跨包验证就进 Sprint 1，等于在"未验证核心卖点"的情况下投入大规模开发**。S0-C 用最小成本（2 个包）回答"跨包这条路到底通不通、通到什么程度"。
