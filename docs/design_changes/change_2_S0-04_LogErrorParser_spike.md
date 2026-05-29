# Design Change 2:S0-04 LogErrorParser Spike 沉淀

**触发**:Sprint 0 S0-04 LogErrorParser 覆盖度 spike
**日期**:2026-05-29
**决策者**:PM(user)+ Claude
**状态**:Approved & Applied
**影响范围**:CNEI / 开发计划 / 对外材料

---

## 背景

S0-04 spike 跑了三组实验(基础类型覆盖 / 级联错误 / 多轮检查 + token 评估)。结果产出**远超 spike 验机制本身**的设计输入,需要正式沉淀到 baseline,作为 Sprint 1+ 实现 LogErrorParser 的强需求。

完整 spike 数据见 `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports/spike_04_log_parser.md`。

---

## S0-04 PASS 依据

| 修正后标准 | 实测 | 判断 |
|---|---|---|
| 5 类错误真实样本(不造假) | 5/5 类全覆盖,共 30 个真实样本 | ✅ |
| parser 在样本上 deterministic | 3 次解析 SHA 一致 | ✅ |
| 明确 LLD vs GNU ld 格式差异 | 已记录(LLD `ld.lld: error: undefined symbol: X >>> referenced by Y.o`) | ✅ |
| 守住 Raw Log 硬约束 | raw log 只放 /tmp,bounded evidence 入库 | ✅ |
| 不造假数据 | 全部真实日常开发场景触发 | ✅ |

**S0-04 PASS**。

**重要纠正**:Claude 在 S0-04 初期判断"libc++/LLD 专属错误现在 Tizen 触发不了 → 5 类完整覆盖推 Sprint 2",这是**过度悲观的判断**。Codex 用真实日常开发场景(漏链库 / 改 header 不同步 / 模板参数写错)成功触发了全 5 类,**5 类错误是 C/C++ 通用大类,日常开发就有,不依赖 LLD/libc++ 迁移**。PM 的判断正确,Claude 在场景理解上有偏差,已纠正。

---

## 4 个设计输入(必须沉淀)

### 设计输入 1:LogErrorParser taxonomy 扩充(高优,Sprint 1+ 强需求)

S0-04 实验 2 暴露:当前 5 类 taxonomy **没覆盖 `unknown_type_name`** —— 这是 typedef/header 删除场景的最常见 cascade 错误(实验 2 里 41 个 error 有 39 个是这个)。

**taxonomy 扩充**(Sprint 1+ 实现 LogErrorParser 时必须包含):

| 错误类型 | 优先级 | 来源 | 备注 |
|---|---|---|---|
| `cannot_find_header` | P0(已有) | 5 类原始 | |
| `undefined_reference` | P0(已有) | 5 类原始 | 注意 LLD 格式 |
| `undefined_symbol` | P0(已有) | 5 类原始 | 运行时 / dlopen |
| `type_mismatch` | P0(已有) | 5 类原始 | |
| `template_error` | P0(已有) | 5 类原始 | |
| **`unknown_type_name`** | **P0(新增)** | **S0-04 实验 2** | typedef/struct 找不到,是 cascade 主力形态 |
| `redefinition` | P1(新增) | 通用 C/C++ | 重复定义 |
| `incomplete_type` | P1(新增) | 通用 C/C++ | 前向声明但用了完整类型 |
| `linker_script_error` | P2(新增) | LLD 迁移 | LLD 专属 |
| `version_script_error` | P2(新增) | LLD 迁移 | LLD 专属 |

**改动**:CNEI v0.3.4 → v0.3.5(§6 LogErrorParser 章节扩充 taxonomy + §6.2 补 mandatory_negative_checks 映射)

### 设计输入 2:single-build primary/cascade 识别(强需求,Sprint 1+ 必须做)

**实证数据(S0-04 实验 2 + 实验 3)**:

```
场景:删一个 typedef → build 产出 41 个 error
真实 primary:1 个(被删的 typedef)
cascade:39 个(全是 unknown_type_name)
primary 位置:第 1 个 compiler error

token 消耗对比:
  raw log:           8,960 tokens(Skill Workflow baseline)
  全 error packets:  8,679 tokens(无 primary 识别)
  primary 1 packet:    340 tokens(有 primary 识别)

primary 识别带来 26x token 缩减
```

**判定**:必须做,理由:

1. **硬数据支撑**:26x token 节省是 CNEI 立项价值的核心实证证据
2. **硬约束保护**:不识别 primary,EvidencePacket < 4000 tokens 硬约束(Contract v0.7.3 §5.6)被打破(实验 2 全 error packets 已 8679 tokens)
3. **算法可行**:S0-04 数据显示 primary **通常就是第一个 compiler error**(不是 linker error),启发式不复杂:
   - 优先处理"第一个 compiler error"作为 primary 候选
   - 后续 error 如引用 primary 里的 symbol/type → 标记为 cascade
4. **架构呼应**:ADR-001 Layer 0 的 `failure_causality_graph`(跨 RPM primary/cascade)依赖单 build 内的 primary/cascade 识别能力作为基础

**Sprint 1+ 实现要求**:

```
LogErrorParser 必须输出:
  primary_errors: [List of error events,通常 1 个]
  cascade_errors: [List of error events with reference to primary_id]
  
  cascade 判定规则(初版启发式,可在 Sprint 1+ 细化):
    - 第一个 compiler error 默认为 primary 候选
    - 后续 error 包含 primary 里的 symbol/type name → cascade
    - 不在 cascade 关系里的独立 error → 另起一个 primary
  
EvidencePacket 生成策略:
  默认:对 primary 生成 1 个 EvidencePacket(含 cascade 摘要,如"39 个相同形态的 unknown_type_name")
  例外:用户/Compiler Agent 明确要求逐个分析 → 多个 EvidencePacket(但要警告 token 消耗)
```

**改动**:CNEI v0.3.5 §2(EvidencePacket schema 加 primary/cascade 字段)+ §6.3(LogErrorParser 加 primary/cascade 识别逻辑)

### 设计输入 3:LLD 错误格式正式记录

S0-04 实验 1.5 + 实验 1.2 实证了 LLD 和 GNU ld 的错误格式**完全不同**:

```
GNU ld:
  foo.o: In function `bar()':
  foo.cc:42: undefined reference to `baz()'

LLD:
  ld.lld: error: undefined symbol: baz()
  >>> referenced by foo.cc:42 (path/to/foo.cc:42)
  >>>               foo.o:(bar())
```

**LogErrorParser 必须显式支持两种格式**(不能只认 GNU ld)。这条本来在 ADR-001 / S0-10 已经隐含,但 S0-04 实证后要写进 CNEI baseline 的 LogErrorParser 章节,作为 Sprint 1+ 实现的硬要求。

**改动**:CNEI v0.3.5 §6.3 加 LLD 格式样例 + 解析规则

### 设计输入 4:实证 token 数据写入对外材料

26x token 缩减是**硬数据**,可用于:

- 给总部的 PPT(`coding_system_rationale.html`)——目前用的是理论估算"< 4000 tokens"和"一个数量级缩减",可更新为实证 26x
- ADR-001 / CNEI v0.4 设计动机的支撑数据
- Coding System vs Skill Workflow 对比的核心证据

**改动**(可选,非阻塞):后续给总部展示时,把 26x 实证数据加进 PPT。这条不进 baseline,但记录在此供 PM 后续使用。

---

## S0-04 Sprint 0 标准明确化(替代之前的"过度悲观"判断)

```
S0-04 Sprint 0 标准(明确化,non-regression):
  
  机制验证(Sprint 0 PASS 条件):
    - 5 类错误真实样本(不造假),来源不限 LLD/libc++ 迁移
    - 真实样本可通过"日常 C/C++ 开发场景"触发(漏链库 / 改 header 不同步 / 模板用错等)
    - parser 在已采集真实样本上 deterministic + 解析准确
    - 明确记录 LLD vs GNU ld 格式差异
    - 守住 Raw Log 硬约束(raw log 只放 /tmp,bounded evidence 入库)
  
  深度规模化(Sprint 2 LogErrorParser 正式实现前置):
    - 50 份历史日志覆盖(Tizen-specific build farm 数据)
    - taxonomy 扩充到 10+ 类(含 unknown_type_name / redefinition / incomplete_type / 
      linker_script_error / version_script_error)
    - LLD/libc++ 迁移真实启动后的样本补充(template_error/type_mismatch 在 libc++ 下的形态)
    - single-build primary/cascade 识别算法的真实数据训练 + 调优
```

---

## 改动汇总

| 文档 | 旧 → 新 | 改了什么 |
|---|---|---|
| CNEI | v0.3.4 → **v0.3.5** | taxonomy 扩充(§6.1) + primary/cascade 识别(§2.2.5 + §6.3) + LLD 格式样例(§6.3) |
| 开发计划 | v2.1.3 → **v2.1.4** | S0-04 标准明确化 + Sprint 2 LogErrorParser 前置条件 + 关联文档版本同步 |
| MAIN_PROMPT | v2.3 → **v2.4** | 关联文档版本同步 |

---

## 影响的 Phase / 模块 / 接口

| 设计输入 | 影响 Phase | 影响模块 | 影响接口 |
|---|---|---|---|
| 1 taxonomy 扩充 | Sprint 1+ | LogErrorParser | error_type 枚举 |
| 2 primary/cascade | Sprint 1+ | LogErrorParser / EvidencePacket | EvidencePacket schema(加 primary/cascade 字段) |
| 3 LLD 格式 | Sprint 1+ | LogErrorParser | regex/解析规则 |
| 4 实证数据 | 对外材料 | PPT / 文档 | (非 baseline) |

## 是否影响已完成的 checkpoint

否。本次变更是 spike 数据沉淀,尚无 LogErrorParser 代码实现。

## 是否需要回滚或返工

否。沉淀的是 Sprint 1+ 实现 LogErrorParser 的需求,不影响 Sprint 0 spike 已完成部分。

## 待 Codex 确认

无待确认项。S0-04 PASS,Codex 可继续 S0-05。
