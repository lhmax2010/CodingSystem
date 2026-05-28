# Demo & 验收剧本 v0.3（M1 / M2 验收）

**版本**：v0.3（针对 ChatGPT v0.2 review 修订，小修）

**v0.3 修订摘要**：

- ChatGPT 抓到：场景 2 输出中 "template error context" 是 typo，应为 "linker error context"（场景 2 是 undefined reference / linker 错误）
- ChatGPT 抓到：cmake 命令 `2>/dev/null` 吞 stderr 不利于现场 demo debug — 改用 `-S . -B build -G Ninja` 标准写法

**v0.2 修订摘要**（针对 ChatGPT + Kimi v0.1 review 修订）：
**状态**：Demo 准备模板
**适用对象**：M1 / M2 验收主持人（user）、Codex（准备演示环境）、外部观众（管理层 / 团队）

**v0.2 修订摘要**：

- ChatGPT 抓到："场景 7：可观测性总结" 不应叫场景，否则与 M1 验收"6 场景" 冲突 — 改名 "Closing"
- ChatGPT 抓到：场景 6 末尾说"刚才 5 个 demo 场景" 但实际是 6 个 — 修正
- ChatGPT 抓到：场景 2 用 `$ make`，但 Phase 1A baseline 是 cmake/ninja — 改为 `ninja -C build`
- ChatGPT 抓到：`--test-mode inject_raw_log` 不应进入产品 CLI — 改成 demo script 独立脚本
- Kimi 抓到：场景 2 用虚构 KI-007 — 改用真实 ID 占位 + 标注
- Kimi 抓到：场景 3 用 template error，但 A13 中 template_error 是 best-effort — 加替代方案
- Kimi 抓到：场景 7 用 mock incoming-handoff 需明确标注 — 加标注
**关联文档**：
- 《Compiler Agent v5.2-RC2.3》（文档 02，§A15 Demo 剧本基础）
- 《Benchmark Agent v5.2-RC2.4》（文档 03，§B13 Demo 剧本基础）
- 《开发计划 v2.1.1》（文档 05，§1.2 / §3.2 M1/M2 定义）

**文档目的**：把 M1 / M2 验收 Demo 的**具体逐步流程**写清楚，不只是"演示什么"，还要"怎么演示 + 怎么应对意外"。Codex 在 Phase 1A/1B 末期需要严格按此剧本准备演示环境。

---

## 0. Demo 通用原则

### 0.1 Demo 不是销售演示

- **诚实**：展示成功也展示失败，让观众理解系统能力边界
- **结构化**：每场景明确"输入 → 系统行为 → 输出"，便于跟读
- **可复现**：所有 Demo 命令脚本化，观众事后可自己跑

### 0.2 失败的处理

如果 Demo 过程中真的 fail（live demo 风险），按这个顺序处理：

1. **冷静说明**：「这个场景遇到了 X 问题，是 Y 原因，我们事后会展示 trace」
2. **跳到下一个场景**：不要现场调试
3. **事后用 backup 复现**：在 Q&A 阶段用预录视频或 backup 数据

### 0.3 Demo 前置 checklist

每场 Demo 开始前 30 分钟必做：

- [ ] 演示环境（Tizen repo / 开发板）状态正常
- [ ] backup 数据准备好（trace.json / artifact / video）
- [ ] 投屏 + 网络 + 字体大小测试通过
- [ ] Codex 完成预演（至少 1 次完整跑通）
- [ ] 失败回滚命令准备好（如清理 device lock）

---

## 1. Phase 1A Demo 剧本（M1 验收，30 分钟）

### 1.1 Demo 准备清单

#### 1.1.1 演示环境

| 项 | 准备内容 |
|---|---|
| **Tizen repo** | 选定 1 个 cmake/ninja project，< 100 万行（Phase 1A Spike 已选定） |
| **网络** | 内部 Slack + 演示室 wifi |
| **机器** | Codex 主机（x86 Linux 工作站）|

#### 1.1.2 数据准备

| 数据项 | 内容 | 数量 |
|---|---|---|
| **12 种典型编译错误案例** | 已经验证修复率的真实案例 | 12 个 |
| **Known Issues YAML** | Phase 1A Sprint 0 准备的初始数据 | 20-30 条 |
| **Trace samples** | 成功 / 失败 / 边界场景的完整 trace | 5-10 份 |

#### 1.1.3 Backup 资源

- 每个 Demo 场景预录的视频（用于 live demo fail 时回退）
- 完整 trace.json + events.jsonl（供 Q&A 时调出）
- ADR 记录（如 Sprint 0 Spike 期间有任何 partial 决策）

### 1.2 Demo 流程（30 分钟）

```
00:00-02:00  开场 + Phase 1A 目标回顾
02:00-05:00  场景 1: Happy path 编译成功
05:00-15:00  场景 2: 典型修复 happy path（最长 + 含 trace 展示）
15:00-20:00  场景 3: Bounded repair loop 触发
20:00-23:00  场景 4: not_fixable 边界
23:00-26:00  场景 5: Token Budget 触发
26:00-29:00  场景 6: Raw Data Detector 触发
29:00-30:00  Closing：可观测性总结（非正式场景）
```

**v0.2 澄清**：M1 验收**正式 demo 场景是 6 个**（场景 1-6），Closing 是收尾环节，不计入验收 6 场景。

之后 10-15 分钟 Q&A。

---

### 场景 1：Happy path 编译成功（3 分钟）

**目的**：展示系统正常情况下不打扰用户（被动 verify）。

**剧本**：

```
[屏幕显示] Tizen repo 终端
$ git log --oneline -5
（显示最近 5 个 commit，强调"正常代码状态"）

[切换] Codex 终端
$ ./scripts/run_compiler_agent.sh \
    --task-id DEMO-001 \
    --workspace ~/tizen-repo \
    --build-target libcompiler \
    --build-mode incremental

[输出预期]
[probe_env] PASS (build_system=cmake_ninja, env=clang-release)
[compile] PASS (exit=0, 0 errors)
[result] task_status=success
        compile_result.exit_code=0
        no patch needed
        token_usage_total=120 (well under budget 25000)

[Demo 讲解]
"系统识别出编译成功，task 直接 success 退出。
注意 token_usage 只有 120——因为编译成功，根本没调用 ClineSR。
这是 Cognitive Boundary 的体现：确定性结果不浪费 LLM token。"
```

**Q&A 预案**：
- Q："为什么不直接用 cmake build？"
- A："对，编译成功时系统的价值是 verify + report。失败时才是真正的价值点，看场景 2。"

---

### 场景 2：典型修复 happy path（10 分钟，**核心场景**）

**目的**：展示系统的核心价值——自动修复 undefined reference 类错误。

**剧本**：

```
[准备] 故意在代码中引入 undefined reference 错误
$ cd ~/tizen-repo
$ git checkout demo/undefined-reference-case
（事先准备的分支）

# v0.3 修订：用标准 cmake 写法，不吞 stderr（live demo 出错时能看原因）
$ cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
$ ninja -C build  # 让用户看到自然的错误，约 30 秒

[输出]
libcompiler/InlineCostModel.cc:42: error: 
  undefined reference to 'compiler_pass::estimate(...)'
ld: symbol lookup error

[切换] Codex 终端，跑 Compiler Agent
$ ./scripts/run_compiler_agent.sh \
    --task-id DEMO-002 \
    --workspace ~/tizen-repo \
    --build-target libcompiler \
    --build-mode incremental

[输出实时显示，时间约 90-120 秒]

[probe_env]   PASS in 1.2s
[compile]     FAIL in 23s (exit=2, 1 error)
[parse_log]   structured_errors.json with 1 error (type=undefined_reference)
[evidence]    EvidencePacket generated
              - 5 facts
              - 3 negative_facts
              - 1 log_excerpt (linker error context)
              - clangd: high confidence, auto_cmake_ninja
[known_issue] 1 match: tizen-ki-undef-ref-001  "missing target_link_libraries for compiler_pass"
                       (v0.2 占位 ID；实际 ID 以 Sprint 0 期间 team 协调产出的 known_issues.yaml 为准)
[cline:analyze] decision=fixable, root_cause=missing_link_library
[cline:patch]   suggestion_patch generated (5 lines)
[validate]      PASS
[apply]         APPLIED in isolated workspace (git worktree)
[verify_rebuild] PASS in 18s
[result]        task_status=success
                patch_generation_attempts=1
                token_usage_total=4250
                suggestion_patch.diff saved

[Demo 讲解]
"现在我们打开生成的 patch 看看："

$ cat docs/outputs/DEMO-002/suggestion_patch.diff
# CompilerAgent metadata:
#   task_id: DEMO-002
#   base_commit: abc123...
#   verified_in_isolated_workspace: true
#   verification: rebuild PASSED

diff --git a/CMakeLists.txt b/CMakeLists.txt
@@ -45,7 +45,7 @@ target_link_libraries(libcompiler
     compiler_core
+    compiler_pass
     ...

"5 行 patch，含验证 metadata。用户可以 git apply 后再 review。"

[trace 展示，2 分钟]
$ cat docs/outputs/DEMO-002/trace.json | jq '.events[]'

[强调显示]
- evidence_collection 阶段的 negative_facts（让观众理解"系统知道什么没找到"）
- known_issue_match 命中（让观众看到 institutional knowledge 的价值）
- token_usage（每个阶段的累计 token 数）
- bounded repair loop 的 patch_generation_attempts=1（没触发重试）

[Demo 讲解结尾]
"这是一个典型的 happy path：
1. 系统识别错误类型 → undefined_reference
2. 收集证据 → negative_facts 帮助 LLM 不乱猜
3. 命中 Known Issue → 借助历史经验加速
4. 生成 patch → 在 isolated workspace 验证 → 不污染用户代码
5. 给出 patch + verification 证明，由用户决定 apply

这就是我们承诺的 60% 自动修复成功率的来源。"
```

**Q&A 预案**：
- Q："如果 Known Issue 没匹配怎么办？"
- A："系统会用 EvidencePacket（facts + negative_facts）让 LLM 自己分析。Known Issue 是加速，不是必要。"
- Q："patch 要不要让我手动看？"
- A："必须的，Phase 1A 是 verify_only —— 我们生成 patch 但不替你 commit。"

---

### 场景 3：Bounded repair loop 触发（5 分钟）

**目的**：展示当第一次 patch 生成有问题时，系统能在 bounded retry 内 recover。

**剧本**：

```
[准备] 选一个第一次 patch 容易 fail 的案例
（事先在 Sprint 4/5 测试中找出的真实案例）

**v0.2 替代方案标注**：本场景预期用 template error（Compiler A13 #10 best-effort 项）演示 bounded repair loop。
如 Sprint 0 spike 或 Sprint 4 测试发现 template error 不在 Phase 1A 支持范围，**替换为 undefined_reference 的 context_line_mismatch 案例**（A13 #1 必须支持项，bounded repair 行为一致）。

$ ./scripts/run_compiler_agent.sh \
    --task-id DEMO-003 \
    --workspace ~/tizen-repo \
    --build-target libfoo

[输出实时显示]

[probe_env]    PASS
[compile]      FAIL (template instantiation error)
[parse_log]    structured_errors.json
[evidence]     EvidencePacket
[cline:analyze] decision=fixable, root_cause=missing_template_specialization
[cline:patch][1] suggestion_patch (12 lines)
[validate]     FAIL - reason=context_line_mismatch
              recoverable? YES (in RECOVERABLE_VALIDATION_ERRORS)
              triggering retry...
[cline:patch][2] suggestion_patch (10 lines, with previous_attempt_failure context)
[validate]     PASS
[apply]        APPLIED
[verify_rebuild] PASS
[result]       task_status=success
               patch_generation_attempts=2  ← 注意这里
               token_usage_total=6800

[Demo 讲解]
"这次系统经历了 bounded repair loop：
- 第一次 patch 的 diff 格式有问题（context lines 偏移）
- 系统识别这是 recoverable error
- 把失败信息传给 LLM，让它生成第二次 patch
- 这次成功了

但要注意 bounded：
- patch_generation 最多 2 次
- 第二次仍失败 → 直接 emit_failure，不会无限重试
- rebuild 失败更严格：1 次就 emit_failure

这是工程鲁棒性，不是多轮智能修复。Phase 1.5 才会引入多轮智能修复（Memory Infrastructure）。"
```

---

### 场景 4：not_fixable 边界（3 分钟）

**目的**：展示系统知道自己什么时候做不到，不会瞎猜。

**剧本**：

```
[准备] 故意构造一个超出 Phase 1A 范围的错误
（如 missing system library，需要安装包，不是改代码能解决的）

$ ./scripts/run_compiler_agent.sh \
    --task-id DEMO-004 \
    --workspace ~/tizen-repo

[输出实时显示]

[probe_env]    PASS
[compile]      FAIL
[parse_log]    structured_errors.json (cannot_find_header: linux/perf_event.h)
[evidence]     EvidencePacket
              - 0 known_issue matches
              - clangd: semantic_unavailable (file in /usr/include)
[cline:analyze] decision=not_fixable
              reason="system header missing; requires system package install"
[result]       task_status=failed
              failure_class=not_fixable
              token_usage_total=2100
              outgoing_handoff: { target: HUMAN, reason: "system_package_required" }

[Demo 讲解]
"系统识别这超出能力范围（安装系统包不是 Phase 1A 范围）：
- 不强行生成 patch
- 标 failure_class=not_fixable
- 产出 handoff 给 HUMAN，附明确原因

这避免了 LLM '幻觉 patch' —— 我们绝不会在没把握时硬产出错误 patch。"
```

---

### 场景 5：Token Budget 触发（3 分钟）

**目的**：展示系统的成本控制。

**剧本**：

```
[准备] 故意设置一个极低的 token budget
$ ./scripts/run_compiler_agent.sh \
    --task-id DEMO-005 \
    --workspace ~/tizen-repo \
    --max-tokens-per-task 200    # 极低 budget

[输出]

[probe_env]    PASS
[compile]      FAIL
[parse_log]    structured_errors.json
[evidence]     EvidencePacket (estimated 3500 tokens)
[budget_check] FAIL: cumulative_estimate 3500 > budget 200
[result]       task_status=failed
              failure_class=budget_exceeded
              stage=evidence_collection
              token_usage_total=180 (under cap, but next stage would exceed)

[Demo 讲解]
"系统在每个 stage 都做 budget check：
- 不是事后发现超支
- 而是在进入下一个 stage 前预估
- 这次 budget 太低，第一阶段就标 budget_exceeded

这保证了在生产环境，单个 task 不会无意中烧掉 100k tokens。"
```

---

### 场景 6：Raw Data Detector 触发（3 分钟）

**目的**：展示 Raw Log 硬约束的强制性。

**剧本**：

```
[准备] 用 demo 专用脚本演示 RawDataDetector 拦截行为
（这是 demo / 集成测试脚本，不是产品 CLI 功能）

**v0.2 重要修订**（ChatGPT 反馈）：

- 原版用 `run_compiler_agent.sh --test-mode inject_raw_log` 会在产品 CLI 留下危险入口
- v0.2 改为**独立 demo / 集成测试脚本**：`./scripts/demo_phase_1a_scenario_6_raw_data_detector_test.sh`
- 产品 CLI 不暴露 inject_raw_log 开关
- 该脚本通过测试 fixture + 直接调用 ClineAdapter 单元测试入口完成演示

$ ./scripts/demo_phase_1a_scenario_6_raw_data_detector_test.sh
# 内部行为：用一个 8000+ 字符的 raw log fixture 构造非法 prompt
# 直接调用 ClineAdapter.call_cline() 触发 RawDataDetector
# 不走完整 Compiler Agent 流程，仅演示 detector 行为

[输出]

[probe_env]    PASS
[compile]      FAIL
[cline:analyze] CALL BLOCKED
              RawDataDetector triggered:
              prompt contains 8000+ char raw log content
              not in EvidencePacket.log_excerpt structure
              raising RawDataLeakageError
[result]       task_status=failed
              failure_class=raw_data_leakage
              stage=analyze
              token_usage_total=850

[Demo 讲解]
"这是 Team Contract 5.6 的硬约束：
- raw log 不能直接进 LLM prompt
- 只有 bounded + redacted + source-linked 的 log_excerpt 可以
- 这次系统检测到违规，直接 emit_failure

这条约束影响：token 经济性、安全性、信号噪声比、可解释性。
即使是我们自己的代码也不能绕过这个约束。"
```

---

### Closing：可观测性总结（1 分钟，非正式场景）

```
[Demo 讲解]
"刚才 6 个 demo 场景（v0.2 修正），每一个都有完整 trace + events.jsonl：

$ ls docs/outputs/DEMO-*/
DEMO-001/  DEMO-002/  DEMO-003/  DEMO-004/  DEMO-005/  DEMO-006/
  ├── trace.json
  ├── events.jsonl
  ├── build_report.json
  ├── suggestion_patch.diff (if any)
  ├── failure_envelope.json (if any)
  └── handoffs/HO-*.json (if any)

每个失败都可以 root-cause，每个修复都可以回放。
这是 Phase 1A 的 dogfooding 基础。"
```

### 1.3 Phase 1A Q&A 预案（10 题）

| 编号 | 问题 | 答案要点 |
|---|---|---|
| Q1 | 60% 自动修复率怎么算出来的？ | **公式**: `verified_success_cases / in_scope_fixable_cases`。**分子**：bounded repair loop 内产出 patch 且通过 rebuild verification 的案例；**分母**：12 种 Phase 1A 真实错误案例中**属于 Phase 1A 支持范围**的。**明确排除**: missing system package / network / infra / flaky tests / unsupported build system (gbs/make) / user workspace dirty 等 |
| Q2 | 用户要不要手动 review 每个 patch？ | Phase 1A verify_only，强烈建议；Phase 2+ Coding Agent 加 PR 流程 |
| Q3 | 跟 ChatGPT 直接帮我修代码区别在哪？ | 我们做证据收集 + bounded retry + isolated workspace verify + trace；ChatGPT 是单轮对话，无验证、无约束 |
| Q4 | Token cost 算下来贵吗？ | 平均 task 5-10k tokens，约 $0.05-$0.15；远低于工程师 5 分钟时间成本 |
| Q5 | gbs 不支持，那 Tizen 不就用不了？ | Phase 1A 是 cmake/ninja 验证；Phase 1.5 加 gbs 支持；当前可以选 cmake/ninja module 试用 |
| Q6 | LLM 给的 patch 错了怎么办？ | isolated workspace 验证 + bounded retry + 用户最终决定 commit；错了不会污染主代码 |
| Q7 | Phase 1B 啥时候开始？ | Phase 1A M1 通过后 1 周内启动 Sprint 0B；不会和 Phase 1A 并行 |
| Q8 | 现在还支持哪些其他语言？ | Phase 1A 主要 C/C++；Python/Rust best-effort（CNEI 支持，但没 12 场景验证）|
| Q9 | 一次能跑多个 task 吗？ | 单 task 串行；Phase 1.5 加并行调度 |
| Q10 | 这套系统跟 Codex 是什么关系？ | Codex 是开发主体（写代码）；系统的 ClineSR 是运行时 LLM（修代码） |

### 1.4 Phase 1A M1 验收标准

Demo 演练通过后，正式 M1 验收要求：

- [ ] **12 种典型场景自动修复成功率 ≥ 60%**（核心 gate）
- [ ] Detection Success Rate / Evidence Usefulness Rate / Patch Generation Success Rate 收集（观察指标）
- [ ] 真实 Tizen repo 端到端跑通
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] Demo **6 个正式场景**顺利演示（场景 1-6；Closing 不计入验收）
- [ ] 内部 5-10 人 dogfooding 启动
- [ ] user + 至少 1 个外部 AI（Claude/ChatGPT/Kimi）通过 M1 验收

---

## 2. Phase 1B Demo 剧本（M2 验收，30 分钟）

### 2.1 Demo 准备清单

#### 2.1.1 演示环境

| 项 | 准备内容 |
|---|---|
| **Tizen 开发板** | 至少 2 块可用（DEMO-A / DEMO-B），SDK 已配置 |
| **Skill** | 至少 3 个示例 Skill 可用：python_loop_smoke_test（x86） + memory_alloc_perf（兼容） + video_player_startup（device） |
| **Baseline 数据** | 每个 Skill 的 baseline benchmark result（多次跑取 median） |
| **网络** | 内部 Slack + 演示室 wifi + 开发板 ssh 备用 |

#### 2.1.2 Backup 资源

- 预录视频（device hang 时回退）
- 完整 5 格式报告 sample（md + html + png + csv + json）
- DeviceLockManager log（用于场景 6）

### 2.2 Demo 流程（30 分钟）

```
00:00-02:00  开场 + Phase 1B 目标回顾 + 与 Phase 1A 联动概念
02:00-07:00  场景 1: 基本 benchmark 跑通（x86 + device）
07:00-12:00  场景 2: 5 种报告格式展示
12:00-17:00  场景 3: Regression 检测 + handoff
17:00-22:00  场景 4: 自动 rerun 触发（noise 注入）
22:00-25:00  场景 5: Skill Manifest violation 拦截
25:00-28:00  场景 6: Device Lock 冲突
28:00-30:00  场景 7: 与 Compiler Agent 串联
```

之后 10-15 分钟 Q&A。

---

### 场景 1：基本 benchmark 跑通（5 分钟）

**目的**：展示 Skill Runtime + Benchmark Agent 端到端跑通。

**剧本**：

```
$ ./scripts/run_benchmark_agent.sh \
    --task-id BMK-DEMO-001 \
    --skills video_player_startup@1.0.0 \
    --device-id DEMO-A \
    --baseline ~/baselines/video_player_baseline.json \
    --repeats 5 --warmup 1

[输出实时显示，约 90 秒]

[acquire_lock]      DEMO-A locked (pid=12345, heartbeat started)
[check_env]         PASS (thermal=normal, governor=performance)
[snapshot_env]      env captured (kernel=4.19, sdb=4.2.16)
[load_skill]        video_player_startup@1.0.0 loaded
                    manifest validated, static scan: 0 warnings
[run][warmup=1]     PASS (startup=423ms - discarded)
[run][repeat=1]     PASS (startup=387ms, memory=128MB)
[run][repeat=2]     PASS (startup=392ms, memory=126MB)
[run][repeat=3]     PASS (startup=389ms, memory=130MB)
[run][repeat=4]     PASS (startup=395ms, memory=127MB)
[run][repeat=5]     PASS (startup=388ms, memory=125MB)
[validate_result]   PASS (CV=0.9%, 5 samples)
[compare_baseline]  STABLE
                    startup_time_ms: 390 vs baseline 385 (+1.3%, within 5% threshold)
                    peak_memory_mb: 127 vs baseline 128 (-0.8%)
[summarize]         compressed
[cline:analyze]     narrative ready
[render_chart]      chart.png saved
[render_report]     md/html/csv/json saved
[release_lock]      DEMO-A released
[result]            task_status=success, regression=false

[Demo 讲解]
"刚才看到的是完整 benchmark 流程：
1. 锁开发板，避免抢板子
2. 检查 env 健康
3. 加载 Skill（Manifest 验证 + static scan）
4. 调度 warmup + 5 次 repeat
5. validate_result（CV 0.9% 合格）
6. compare_baseline（stable）
7. cline narrative + chart + 5 格式报告
8. 释放锁

注意 cline 只做 narrative，**不参与 rerun 决策**——
这是 Cognitive Boundary 在 Benchmark Agent 的体现。"
```

---

### 场景 2：5 种报告格式展示（5 分钟）

**目的**：展示 Benchmark Report Contract 的完整产出。

**剧本**：

```
$ ls docs/outputs/BMK-DEMO-001/reports/
benchmark_analysis.md       # 人读 narrative
benchmark_report.html       # 富文本 + 嵌入图表（static only，无外部 JS）
benchmark_chart.png         # 单独图表（PR 用）
benchmark_metrics.csv       # tabular 数据（Excel / pandas 可用）
benchmark_raw_result.json   # 结构化原始数据（API 集成用）

[Demo 操作]
# 1. md（人读）
$ cat docs/outputs/BMK-DEMO-001/reports/benchmark_analysis.md
# Benchmark Analysis: video_player_startup@1.0.0
... summary ...
## Results
| Metric | Current | Baseline | Delta | Status |
|---|---|---|---|---|
| startup_time_ms | 390 | 385 | +1.3% | STABLE |
| peak_memory_mb | 127 | 128 | -0.8% | STABLE |
## Narrative
The benchmark completed successfully with stable measurements.
CV across 5 samples: 0.9% (well within 5% threshold).
No regression detected against baseline.

# 2. html（在浏览器打开）
$ xdg-open docs/outputs/BMK-DEMO-001/reports/benchmark_report.html
[展示 static html，强调 no external JS]

# 3. csv（用 Excel/python 打开）
$ python -c "import pandas; print(pandas.read_csv('...metrics.csv'))"
[显示 tabular 数据]

# 4. json（API 集成）
$ jq '.metrics' ...raw_result.json
[显示结构化 schema]

[Demo 讲解]
"5 种格式是 Benchmark Report Contract 的硬要求：
- md 给人看（评审、Slack）
- html 给浏览器（分享链接）
- png 给 PR 附图（CI 自动评论）
- csv 给 Excel/pandas（统计分析）
- json 给 API（自动化集成）

注意 html 是 static only —— 没有外部 JS，没有 ajax，
PR comment 里嵌入也安全。"
```

---

### 场景 3：Regression 检测 + handoff（5 分钟）

**目的**：展示 cross-agent handoff。

**剧本**：

```
[准备] 跑一次故意 regression 的 benchmark
（开发板上事先 deploy 一个性能下降的 build）

$ ./scripts/run_benchmark_agent.sh \
    --task-id BMK-DEMO-002 \
    --skills video_player_startup@1.0.0 \
    --device-id DEMO-A \
    --baseline ~/baselines/video_player_baseline.json

[输出]

[run][repeat 1-5]   完成
[validate_result]   PASS (CV=1.2%)
[compare_baseline]  REGRESSION
                    startup_time_ms: 520 vs baseline 385 (+35%) > 5% threshold
                    BREACHED
[cline:analyze]     narrative + severity hint
                    severity=high (35% regression on critical metric)
[result]            task_status=success (benchmark ran fine), regression=true
                    outgoing_handoff:
                      target: CDN (Coding Agent)
                      reason: regression_detected
                      disambiguator: "skill:video_player_startup"  # v0.7.3 Phase 1B
                      summary: "video player startup +35% regression"

[Demo 操作]
$ cat docs/outputs/BMK-DEMO-002/handoffs/HO-*.json
[显示 handoff schema]

[Demo 讲解]
"Benchmark Agent 不修代码，但能识别 regression 并产出 handoff：
- target: CDN（Coding Agent，Phase 2 实施）
- reason: regression_detected
- disambiguator: skill:video_player_startup
  → 这是 v0.7.3 Phase 1B 启用的字段，
    支持 multi-Skill task 的多个 regression 独立路由
- summary: 一句话总结，让下游 Agent 知道发生了什么

Phase 1B 中 CDN 还没实施，handoff 落地后 user 手动处理。
Phase 2 实施 CDN 后会自动接管。"
```

---

### 场景 4：自动 rerun 触发（5 分钟）

**目的**：展示 rerun 决策由 Tool 层做出（Cognitive Boundary）。

**剧本**：

```
[准备] 在 device 上预先制造一些 noise
（如让 device 跑一个不相关的负载，导致第一次 benchmark 噪声大）

$ ./scripts/run_benchmark_agent.sh \
    --task-id BMK-DEMO-003 \
    --skills video_player_startup@1.0.0 \
    --device-id DEMO-A \
    --baseline ~/baselines/video_player_baseline.json \
    --max-retries 2

[输出]

[Round 1]
[run][repeats 1-5]  完成 (samples noisy)
[validate_result]   noise_detected, requires_rerun=true
                    triggering rerun (retries_left=1)
                    [→ skip ClineSR, go back to run]

[Round 2]
[run][repeats 1-5]  完成 (samples stable)
[validate_result]   PASS (CV=1.1%)
[compare_baseline]  STABLE
[cline:analyze]     narrative only
[result]            task_status=success

[Demo 讲解]
"关键点：rerun 决策是 Tool 层（validate_result）做出的，
不是 ClineSR 决定的。

这是 Cognitive Boundary 的硬约束：
- 'samples 噪声大需要重跑' 是确定性判断 → Tool 层
- '怎么解读 benchmark 结果' 才是 LLM 任务 → ClineSR

第一次 rerun 前 cline 根本没被调用，
这避免了 LLM 'manipulating retry' 的风险。
也节省 token：rerun 不烧 LLM token。"
```

---

### 场景 5：Skill Manifest violation 拦截（3 分钟）

**目的**：展示 Manifest enforcement。

**剧本**：

```
[准备] 创建一个故意违规的 Skill
$ cat my_skills/bad_skill/skill.yaml
skill_id: bad_skill
version: 1.0.0
description: "test violation"
target_platforms: [tizen_device]
required_permissions:
  - device.shell
  # 注意：没声明 device.app_launch
timeout_sec: 30
metrics:
  ...
cleanup_required: false

$ cat my_skills/bad_skill/skill.py
class BadSkill(BenchmarkSkill):
    def run(self, ctx):
        # 调用未声明权限的 API
        ctx.device.app_launch("com.samsung.test")
        ...

[运行]
$ ./scripts/run_benchmark_agent.sh \
    --task-id BMK-DEMO-004 \
    --skills bad_skill@1.0.0

[输出]

[load_skill]        bad_skill@1.0.0 loaded, manifest validated
[run][repeat=1]     SkillViolationError:
                    Skill 'bad_skill' called device.app_launch() but
                    required_permissions does not include 'device.app_launch'
[result]            task_status=failed
                    failure_class=skill_violation
                    stage=skill_runtime

[Demo 讲解]
"Manifest 是 runtime-enforced contract：
- Skill 声明需要什么权限 → SkillRuntime 检查
- 调用未声明的 API → 直接 SkillViolationError
- 不影响其他 Skill（multi-Skill task 中其他 Skill 继续）

这避免了用户在 Manifest 撒谎（说不需要权限但实际用了）。"

[另一个变种：高级用户的 trust_level]
"如果你的 Skill 是 trust_level=local（本地开发），
static scan warning 只是 warning。
但要注册到 team registry（trust_level=registered），
warning 必须清零。这是 §2.6 Skill Trust Model。"
```

---

### 场景 6：Device Lock 冲突（3 分钟）

**目的**：展示 DeviceLockManager 的故障恢复。

**剧本**：

```
[Terminal A] 先启动一个 task，会持有 lock
$ ./scripts/run_benchmark_agent.sh --task-id BMK-A --device-id DEMO-A &
[Terminal A] Task running, holds lock for DEMO-A...

[Terminal B] 同时启动另一个 task 抢同一开发板
$ ./scripts/run_benchmark_agent.sh --task-id BMK-B --device-id DEMO-A
[acquire_lock] FAIL
              device DEMO-A locked by another task (pid=12345)
              acquired=false, reason=locked_by_other
[result]      task_status=failed, failure_class=device_lock_failed

[Demo 讲解]
"DeviceLockManager 防止两个 task 同时抢一块板子，
否则 benchmark 数据会被互相污染。

来看故障恢复："

[强杀 Terminal A 的 Codex 进程]
$ kill -9 $(pgrep -f "task-id BMK-A")

[等 30 秒（心跳停止），然后另一个 Terminal C 尝试 acquire]
$ ./scripts/run_benchmark_agent.sh --task-id BMK-C --device-id DEMO-A
[acquire_lock] 
              ⚠️ Detected stale lock from pid 12345 (process not alive)
              force-releasing...
              acquired=true (preempted stale lock)
[run]         normal flow continues...
[result]      task_status=success

[Demo 讲解]
"看 DeviceLockManager 的故障恢复：
- 进程死了，下次 acquire 检测 PID 不存在
- 心跳超过 120 秒不更新 → stale → 抢占
- sdb 断开连接也会自动 release

这避免了'某个进程 crash 后开发板永久锁定'的常见问题。"
```

---

### 场景 7（收尾）：与 Compiler Agent 串联（2 分钟）

**目的**：展示 cross-agent handoff 完整链路。

**剧本**：

```
[准备] 用 Phase 1A 的修复 patch 跑一遍 Benchmark
"在场景 2（Compiler Agent）中我们生成了一个修复 patch。
现在我们 apply 它，跑 Benchmark 看 performance 影响。"

**v0.2 标注**（Kimi 反馈）：本场景的 `--incoming-handoff` 用的是 **mock handoff artifact**（事先准备）。
Phase 1B M2 验收时 Compiler Agent → Benchmark Agent 的真实自动 handoff 链路尚不存在
（需要 Orchestrator/LangGraph，Phase 2+ 实施）。
M2 验收**展示的是 handoff schema 兼容性**：Benchmark Agent 能解析 Compiler 产出的 handoff JSON 并正确响应。

$ git checkout demo/post-compiler-fix    # 包含 patch 的分支

$ ./scripts/run_benchmark_agent.sh \
    --task-id BMK-CROSS-001 \
    --skills python_loop_smoke_test@1.0.0 \
    --incoming-handoff ./demo_data/HO-from-compiler-DEMO-002.json  # mock handoff
    --baseline ~/baselines/python_loop_baseline.json

[输出]

[receive_handoff]   from CMP-DEMO-002, reason=performance_verify_requested
[load_skill]        python_loop_smoke_test@1.0.0
[run][repeats]      完成
[validate_result]   PASS
[compare_baseline]  STABLE (no regression introduced by patch)
[result]            task_status=success
                    cross_agent_chain: CMP-DEMO-002 → BMK-CROSS-001

[Demo 讲解]
"完整链路：
1. Compiler Agent 修复编译错误 → suggestion_patch
2. User apply patch（Phase 1A verify_only，user 决定）
3. Handoff to Benchmark Agent: performance_verify_requested
4. Benchmark Agent 跑 baseline 对比
5. 确认 patch 没引入 regression
6. cross_agent_chain 在 trace 中完整记录

这是 Coding System 的核心价值：
不是单点工具，是 cross-agent 自动化工作流。"
```

### 2.3 Phase 1B Q&A 预案（8 题）

| 编号 | 问题 | 答案要点 |
|---|---|---|
| Q1 | 一个 Skill 跑多久？ | 取决于 manifest timeout_sec；典型 30-300 秒 |
| Q2 | 开发板要不要 root？ | 不要；Skill API 设计避开了需要 root 的操作（如 drop_caches）|
| Q3 | 我要写自己的 Skill 难吗？ | Manifest YAML + Python 类继承；5 分钟快速开始（文档 07 §7）|
| Q4 | Skill 可以联网吗？ | 默认禁止；manifest 显式声明 `network: true` 后允许 |
| Q5 | Memory benchmark 准吗？ | depends on metric；推荐看 §6 metric noise policy 调参 |
| Q6 | Tizen 不同版本结果可比吗？ | environment_snapshot 记录所有 env 信息；不同版本 baseline 独立 |
| Q7 | 100 人推广时开发板够吗？ | Phase 1B 是 5-10 人；Phase 1.5 加 cross-host device pool 解决 |
| Q8 | 开发板坏了怎么办？ | DeviceLockManager 检测 sdb 断开自动 release；task 失败，user 换设备 |

### 2.4 Phase 1B M2 验收标准

- [ ] 至少 3 个 Skill 示例（startup / runtime / memory 三类）
- [ ] 5 种格式报告完整
- [ ] device lock 防止抢板子（场景 6 演示通过）
- [ ] 配合 Compiler Agent 完成 cross-agent handoff（场景 7 演示通过）
- [ ] Skill 框架 trust_level 三级机制可用
- [ ] Demo 7 场景顺利演示
- [ ] user + 至少 1 个外部 AI 通过 M2 验收

---

## 3. 验收维度（4 维度评分）

每次验收（M1 / M2）按 4 个维度评分：

| 维度 | 内容 | 通过线 |
|---|---|---|
| **功能** | 主流程跑通 + Demo 场景演示通过 | **6/6 正式场景**（M1，不含 Closing）/ **7/7 正式场景**（M2）|
| **质量** | UT 覆盖率 + 集成测试 + Bug 数量 | UT ≥ 80%，未解决 P0/P1 = 0 |
| **安全** | Raw Log 约束 / Secret Redaction / Workspace 隔离 | 6 + 8 项 check_gate.sh 通过 |
| **性能** | Token Budget / Task 时长 / 资源占用 | 90% task 在 budget 内 |

每个维度：
- **PASS**：通过
- **FAIL**：阻塞验收
- **待优化**：通过但有提升空间，列入下 Phase 改进计划

---

## 4. Demo 演练计划

### 4.1 Demo 前 1 周（M1）

- 完成所有 Demo 场景脚本化（`./scripts/demo_phase_1a_scenario_N.sh`）
- 实际跑通至少 3 次
- 录制 backup 视频

### 4.2 Demo 前 1 天

- 演示环境冻结（不要再 push 代码）
- backup 视频 + trace 准备就绪
- 演示者预演 1 次（不要现场试）

### 4.3 Demo 当天

- 提前 30 分钟到场
- 检查投屏 + 字体 + 网络
- 跑 happy path 场景 1 测试系统状态
- 准时开始

---

**文档结束**
