# Design Change 3:Sprint 0 外部 Review 修正 + 补充 Spike

**触发**:Sprint 0 收官后,ChatGPT + Kimi 两轮独立外部 review(均拉取真实代码核对)
**日期**:2026-05-30
**决策者**:PM(user)+ Claude
**状态**:Approved,待 Codex 执行
**影响范围**:Sprint 0 定性 / 可审计性 / 进 Sprint 1 前置条件 / 开发计划

---

## 背景

Sprint 0 收官(8 个核心 gate 标记 PASS,checkpoint tag `checkpoint/phase_1a_sprint_0_spike_complete`)后,PM 请 ChatGPT 和 Kimi 做独立外部 review。两个 reviewer **都拉取了真实代码核对脚本**(不只读描述),结论高度一致,并暴露了 Claude 作为"设计者 + 把关者"的盲区。

本 change 记录两轮 review 的核心发现 + 据此决定的修正动作。

---

## 一、两轮 review 的一致结论(Claude 全部接受)

### 1. Sprint 0 验证范围被高估了(定性需降级)

**问题**:Sprint 0 收官表述为"8 gate 全 PASS,Phase 1A 核心技术假设全部验证"。这个表述高估了验证范围。

两个 reviewer 拉代码后一致指出:**Sprint 0 验的大多是"数据格式 + 流程形状",不是"系统在真实压力下能工作"**。

- Gate 1-4(compile_commands / clangd / LogErrorParser / —— 真实代码 + 真实工具):相对扎实
- Gate 5-8(EvidencePacket 性能 / RawDataDetector / KnownIssueMatcher / e2e):是 mock / dry run / synthetic 级别,"流程图验证"而非"生产可用验证"

**具体证据(reviewer 读脚本得出)**:
- **S0-05**:`generate_single_primary_packet()` 只读文件 + 拼 dict + `json.dumps()` 算字符数,**从未调用 clangd / tree-sitter / ctags / ripgrep**。4.4ms 是 JSON 序列化时间,不是真实证据收集时间。→ 应改称 "EvidencePacket schema + budget assembly spike PASS",不是 "generation performance PASS"
- **S0-08**:`run_compile_replay` 读预存的 /tmp 日志,LLM 入口 mocked,无 patch / apply / rebuild。→ 应改称 "pre-LLM pipeline dry run",不是 "end-to-end"
- **S0-06**:synthetic 数据,RawDataDetector 未集成到 ClineAdapter 入口。→ "threshold semantics PASS,adapter-boundary enforcement 未验证"
- **S0-07**:5 条 KI,负例围绕这 5 条手工构造。→ "scope-first matcher 机制 PASS,误报率未统计性验证"
- **S0-09**:只覆盖 CMakeLists mtime stale。→ "CMakeLists mtime downgrade PASS,完整 build config freshness 未验证"

**修正定性表述**(写入 sprint_0_memory):
> Sprint 0 验证了 CNEI **修复前(pre-repair)证据管线**的若干关键机制在单包受控 spike 条件下可行。**未**验证:自动修复系统的核心闭环(LLM 修复 / patch 生成应用 / worktree 隔离 / bounded repair)、跨包规模化能力、真实 patch 成功率。

### 2. 最致命的未验证假设:LLM 修复准确率

**两个 reviewer 都点爆**:整个系统建立在"LLM 看 EvidencePacket 比看原始日志修得更准"这个假设上,而这个假设 **Sprint 0 从头到尾没有验证**。

Sprint 0 验的是"前半段管线"(失败 → 解析 → 收集证据 → 组装 packet),后半段"LLM 真的修代码"完全没碰。后半段才是系统的核心价值和最高风险。

风险:可能花数月把 CNEI 做漂亮,最后发现 LLM 看了 EvidencePacket 还是修不对,或 token 省了但准确率不如直接塞日志 → 整个设计根基动摇。

### 3. 可审计性缺口:S0-01~S0-04 产物不在当前 checkpoint

**ChatGPT 拉代码发现(Kimi 未发现,Claude 也未发现)**:

当前 `codex/sprint-0-main` 和 checkpoint tag 下的 `spike_reports/` **只有 spike_05~09**,**没有 spike_01~04**。`spike_reports_data/` 同样只有 S0-05~S0-09。

`sprint_0_memory.md` 自己承认:S0-01~S0-04 报告被后续设计变更 supersede,数据只能从历史 commit 恢复。

**后果**:Sprint 0 价值最高的证据(S0-03 clangd 50/50、27/30;S0-04 LogErrorParser 5 类 + 41→1 token 数据)**不在 checkpoint 里**。外部 reviewer / 审计 / 接手者 checkout tag 无法复核前 4 个 gate。对外说"9 gate 全 PASS"但前 4 个证据缺失,可审计性是断的。

### 4. primary/cascade 只验了单根因同符号场景

当前 S0-05/S0-08 的 primary/cascade 是 mock:第一个 error 当 primary,同 type name 后续当 cascade。**没有**多 primary / 交错根因 / 跨文件依赖 / linker+compiler 混合 / ninja 并行乱序。这是未来最易暴雷的算法点(已在 CNEI v0.3.5 标为 Sprint 2b 强需求,本 change 补充对其局限的明确记录)。

### 5. token 数据口径

26x 是"删 typedef → 41 同符号 cascade"的 controlled minimal-primary 场景;9x 是含完整 EvidencePacket 的单 case。**都不能当生产普遍值**。典型独立错误场景约 2-4x。对外汇报必须注明场景限定。

### 6. 其他一致建议(纳入后续,非进 Sprint 1 阻塞)

- clangd 样本窄(单 48K 小包),需补模板重 / 宏密集 / 链接复杂 / 跨包的包
- 错误 taxonomy 对"日常 C/C++ 推广"不够(reviewer 列了 20+ 高频类型,如 overload_resolution / ambiguous_call / const_qualifier / cxx_standard_mismatch / duplicate_symbol 等)+ Tizen 特有(dlog 宏 / handle 转换宏 / __TIZEN_DEPRECATED_API)
- RawDataDetector 需 adapter 边界强制 + secret/path/env redaction + 最终序列化后再检测
- negative_facts 需强制带 scope / searched_paths / check_status / freshness,防"错误否定"
- stale 检测需扩展(toolchain file / included .cmake / generated header / sysroot / pkg-config)
- 缺 adversarial / 红队验证(故意构造多根因、misleading KI、超长分散 log、危险 patch)

### 7. 设计方向获得肯定(两个 reviewer 都认可)

- CNEI 做按需 Evidence Collector 而非完整 code graph:方向对(但跨包迁移需补 migration intelligence / package dependency graph)
- negative_facts 防幻觉:好机制
- Raw Log 不入库的边界意识、EvidencePacket schema、KnownIssue scope guard、stale confidence downgrade、工程纪律(trace/checkpoint):被评价为"见过的 AI 驱动系统里最严谨的"

reviewer 原话:"Sprint 0 不是失败,是 spike 起点有价值;但验证强度配不上设计的复杂度。现在不是庆祝 8 gate PASS 的时候,是补验核心假设的时候。"

---

## 二、决定的修正动作

### 动作 A:补充 spike(进 Sprint 1 前必须完成)

**S0-A:Repair Loop Spike(修复闭环 + LLM 修复准确率)** —— 见独立任务定义 `S0-A_Repair_Loop_Spike.md`
- 验证 worktree 隔离 / patch 生成 / patch validate / apply / 1 次 rebuild / bounded repair 失败路径 / failure envelope / cleanup
- **真调 LLM**(不再 mock),A/B 测试:
  - A/B-1:有 negative_facts vs 无 → 验证 negative_facts 价值
  - A/B-2:EvidencePacket vs 直接塞原始日志 → 验证"比单技能工作流强"的根基
- 指标:patch 编译通过率 + 人工 review 语义正确率

**S0-C:跨包最小验证** —— 见独立任务定义 `S0-C_Cross_Package_Spike.md`
- 2 个有依赖的 Tizen 包(A 改头文件 → B 编译失败)
- 验证 CNEI 能否在 B 的证据里引用 A 的符号定义
- 验证"跨包联动"设计可行性(立项卖点的最小证据)

(S0-D clangd 多包样本:推荐但非阻塞,可与 Sprint 1 并行)

### 动作 B:修复可审计性(立刻,非 spike)

补 `docs/dev_memory/phase_1a/sprint_0_spike/artifact_manifest.json`,记录 9 个 gate 每个的:
- report path / script path / result path
- source commit(若已 supersede,指向历史 commit)
- SHA256
- 是否 retained / superseded / historical-only
- raw log location policy

并为 S0-01~S0-04 补 frozen copy 到 `frozen_artifacts/s0_01~04/`(从历史 commit 恢复最终报告 + 脚本 + 结果)。

### 动作 C:文档定性修正

- `sprint_0_memory.md`:定性降级为"pre-repair pipeline 机制验证"(见上方修正表述)
- S0-08 报告:改称/加注 "pre-LLM pipeline dry run"
- token 口径:统一注明 26x = controlled minimal-primary,9x = 单 case,非生产普遍值
- Gate 8 cascade 口径精确化:41 error = 1 primary + 38 same-symbol cascade + 2 too-many-errors(不是"39 个 cascade")

### 动作 D:checkpoint 处理

- **保留** `checkpoint/phase_1a_sprint_0_spike_complete` tag(它确是 pre-repair 机制验证完成点)
- 修正完成后打新 tag `checkpoint/phase_1a_sprint_0_remediated`,标明已修审计 + 降级定性 + 待补 S0-A/S0-C

---

## 三、进入 Sprint 1 的新前置条件

```
进 Sprint 1(写 Compiler Agent 产品代码)前必须:
  [ ] S0-A Repair Loop Spike PASS(尤其 LLM 修复准确率 A/B 有结论)
  [ ] S0-C 跨包最小验证 PASS
  [ ] 可审计性修复(artifact_manifest + frozen_artifacts)
  [ ] Sprint 0 定性修正完成
推荐但非阻塞:
  [ ] S0-D clangd 多包样本(可与 Sprint 1 并行)
```

---

## 四、影响 / 回滚 / 待确认

- **影响 Phase**:Sprint 0(补充)+ 进 Sprint 1 时机推迟
- **影响 checkpoint**:不撤销现有 tag,新增 remediated tag
- **是否返工**:否。已完成的 Gate 1-9 spike 不返工,只补缺失的验证 + 修审计 + 改表述
- **待确认**:S0-A 真调 LLM 用哪个模型(Claude / Codex / GPT-4)由 PM 提供环境;A/B 测试的"直接塞日志"baseline 需 PM 确认 token 上限口径

---

## 五、命名说明(避免混淆)

- **S0-A / S0-C**:本 change 新增的 Phase 1A 根基补验 spike(修复闭环 / 跨包)
- **S0-10 Scale Spike**:之前已规划的 OS 级规模化 spike(gbs/chroot/scip-clang),属 Phase 1.5,仍未启动,与 S0-A/S0-C 不同
- 三者都不冲突,S0-10 保留给 Scale Spike
