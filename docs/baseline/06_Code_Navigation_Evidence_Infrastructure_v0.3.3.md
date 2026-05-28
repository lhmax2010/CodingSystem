# Code Navigation & Evidence Infrastructure 设计文档

**版本**：v0.3.3（Phase 1A 实施候选，Sprint 0 Spike Gate 启动版）
**状态**:**Draft / Spike Required**（必须在 Phase 1A Sprint 0 Spike Gate 中验证关键假设）
**关联文档**：
- 《Agent Team Contract v0.7.2》（文档 0）
- 《Compiler Agent v5.2-RC2.2》（文档 2）
- 《Benchmark Agent v5.2-RC2.3》（文档 3）

**文档目的**：定义 Coding System 中处理"代码导航 + 编译错误证据收集"的共享基础设施。该基础设施在 Phase 1A 主要服务 Compiler Agent，Phase 1B 起也为 Benchmark Agent 提供有限服务。

**版本历程**：
- v0.1：初版
- v0.2：ChatGPT review 反馈（clangd preferred / negative_facts / log_excerpt / Known Issues 治理）
- **v0.3（本版）**：ChatGPT + Kimi 联合 review 反馈，clangd 策略升级到 B++（高级用户 explicit_path override + stale 检测）、Benchmark 调用降级行为明确、CNEIConfig 抽出共享配置、Known Issues 初始数据准入标准

**v0.3 修订摘要**：

- ChatGPT 指出"explicit_path 应该是高级用户 override"——升级 clangd 策略为 **B++**（默认安全降级 + explicit_path override）
- Kimi 指出"compile_commands.json 可能 stale"——加 mtime 软检查 + `clangd_stale` flag
- Kimi 指出"配置位置应该是 CNEIConfig"——`compile_commands_source` 放 CNEI 11.1 config 层
- Kimi 指出"Benchmark 调用 CNEI 时 build_system=None 行为未明确"——加 `Benchmark integration` 章节
- ChatGPT 指出"架构图前面还写 optional"——全局措辞统一为 "preferred backend"
- Kimi 指出"negative_facts 缺 scope 字段"——加 `scope` 字段
- Kimi 指出"每种 error_type 的 negative checks 未预定义"——6.2 节加 mandatory_negative_checks 映射表
- Kimi 指出"Known Issues 初始数据无准入标准"——7.4 加准入标准

**v0.3 修订量**：约 4000-5000 字增量，核心架构不变。

**v0.3.1 修订摘要**（小修版，针对 ChatGPT + Kimi 的 RC2 review）：

- **ChatGPT 指出**：Phase 1A/1B/1.5 范围表中 clangd 行仍写"可选叠加"，与 4.3 节 B++ 策略冲突 —— Phase 矩阵 clangd 行重写为 "B++ conditional preferred backend"
- **ChatGPT 指出**：v0.3 加了 `clangd_stale` flag 但仅 emit warning，stale 时 clangd 仍标 high confidence —— **stale 时强制降级 confidence 到 medium + confidence_modifier = "stale_compile_commands"**（新增 4.3.2.1 节）
- **ChatGPT 指出**：版本号"v0.7"残留 —— 统一为 v0.7.2 引用

**v0.3.1 修订量**：< 500 字，纯一致性 + 一处安全策略强化（stale confidence 降级）。

**v0.3.2 修订摘要**（小修版）：

- **ChatGPT + Kimi 都指出**：v0.3.1 关联文档仍写 RC2，应该同步到 RC2.1 / RC2.2 —— 关联文档版本号统一更新到 v5.2-RC2.2

**v0.3.2 修订量**：< 100 字，纯版本号同步。

**v0.3.3 修订摘要**（小修版）：

- **Kimi 指出**：§4.3.2.1 stale 降级机制与 §4.3.5 Benchmark 集成的关系不清楚 —— Benchmark 调用 CNEI 时已经走 DegradedBackend 路径，stale 检测根本不会触发；需要明确说明本降级机制**仅服务于 Compiler Agent 路径**

**v0.3.3 修订量**：< 200 字，纯关系澄清。

---

## 0. 设计哲学

### 0.1 关键判断：不是 Code Graph，是 Evidence Collector

我们经过反复讨论后确认的核心判断：

> **Compiler Agent 真正需要的不是"完整代码知识图谱"，而是"针对当前编译错误的精准证据包"。**

对应的设计取舍：

- ❌ 不追求完整的 cross-file call graph（tree-sitter 做不到，clangd 也只在配置完整时才行）
- ❌ 不追求 Chromium-scale 全局索引（Phase 1A 范围）
- ❌ 不追求"所有 reference 100% 准确"（不可能，过度追求会让方案过重）
- ✅ 追求**针对单个 build error 收集足够 evidence 让 LLM 做出正确判断**
- ✅ 追求**best-effort + confidence 标注**（明确告诉 LLM 哪些是确定的、哪些是猜测的）
- ✅ 追求**build-system-aware**（不只看代码，也看 CMakeLists / spec / pkg-config）

### 0.2 命名说明

我们之前讨论中曾用过"Code Graph Infrastructure"这个词。**v0.1 正式命名为 Code Navigation & Evidence Infrastructure（CNEI）**，理由：

- "Code Graph"暗示全局图谱，与实际能力不符
- "Code Navigation"准确表达"能在代码里找到东西"
- "Evidence"准确表达"为某个具体问题收集证据"
- 两者组合反映了双层 API：底层导航 + 上层证据

下文统一用 **CNEI** 简称。

### 0.3 Cognitive Boundary 遵守

CNEI 是 Code/Tool 层组件，输出**确定性**结果（带 confidence 标注），不做模糊推理。**模糊推理交给 LLM**。

具体来说：

- ✅ "符号 `foo` 在文件 A 第 42 行定义" → 确定性事实
- ✅ "`foo` 的潜在 callers 有 X/Y/Z，置信度 0.85" → 带置信度的事实
- ❌ "这个错误可能是 ABI 不兼容导致" → 模糊推理，交给 LLM

---

## 1. 整体架构

### 1.1 分层结构

```
┌─────────────────────────────────────────────────────────┐
│  Compiler Agent / Benchmark Agent (consumer)            │
└─────────────────────────────────────────────────────────┘
                       ↓ uses
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Evidence Collector (high-level API)          │
│  - get_evidence_packet(error_event) -> EvidencePacket  │
└─────────────────────────────────────────────────────────┘
                       ↓ uses
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Code Navigation (mid-level API)              │
│  - find_definition(symbol)                              │
│  - find_references(symbol)  [best-effort]              │
│  - find_callers(symbol)     [best-effort]              │
│  - get_file_imports(file)                               │
└─────────────────────────────────────────────────────────┘
                       ↓ uses
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Backend Indexers (low-level)                 │
│  - tree-sitter (AST, multi-language)                   │
│  - universal-ctags (symbol candidates)                 │
│  - clangd / scip-clang (C/C++ semantic preferred backend, B++ strategy)      │
│  - ripgrep (fallback text search)                      │
│  - SQLite (cache + cross-reference store)              │
└─────────────────────────────────────────────────────────┘
                       ↓ uses
┌─────────────────────────────────────────────────────────┐
│  Layer 0: Build-System-Aware Collectors                │
│  - CompileCommandParser (compile_commands.json)        │
│  - CMakeContextCollector                                │
│  - PkgConfigCollector                                   │
│  - SpecFileCollector (Phase 1.5)                       │
│  - LinkCommandCollector                                 │
└─────────────────────────────────────────────────────────┘
```

### 1.2 各层职责

| 层 | 职责 | 输出特性 |
|---|---|---|
| **L0 Build-System** | 解析 build 配置和命令 | 确定性数据 |
| **L1 Backend Indexers** | 从代码生成索引 | 确定性数据 + 部分 best-effort |
| **L2 Code Navigation** | 提供导航 API | 带 confidence 的事实 |
| **L3 Evidence Collector** | 针对错误组装证据包 | 结构化 Evidence Packet |

### 1.3 Phase 1A vs 1B vs 1.5 范围（v0.3 修订）

| 能力 | Phase 1A | Phase 1B | Phase 1.5 |
|---|---|---|---|
| tree-sitter 多语言 AST | ✅ | ✅ | ✅ |
| universal-ctags 符号候选 | ✅ | ✅ | ✅ |
| ripgrep 兜底搜索 | ✅ | ✅ | ✅ |
| clangd C/C++ 语义 | **B++ conditional preferred backend**（auto + cmake_ninja + compile_commands.json 时启用；explicit_path override；否则降级，见 4.3.1）| Benchmark 调用默认降级（build_system=None 触发 Gate 4），仅用于辅助 impact scope；Compiler 任务继续走 Phase 1A 规则 | required / pre-indexed / shard |
| SQLite cache | ✅ | ✅ | ✅ |
| CompileCommandParser | ✅ | — | ✅ |
| CMakeContextCollector | ✅ | — | ✅ |
| PkgConfigCollector | ✅ | — | ✅ |
| LinkCommandCollector | ✅ | — | ✅ |
| SpecFileCollector | 接口预留 | — | ✅ 完整实现 |
| Evidence Packet for Compiler | ✅ | — | ✅ |
| Evidence Packet for Benchmark | — | 有限版本 | ✅ |
| Chromium-scale support | ❌ | ❌ | ✅ |
| Known Issues DB integration | ✅ | — | ✅ |

---

## 2. 核心数据结构

### 2.1 EvidencePacket

CNEI 对外最关键的产出。结构如下：

```json
{
  "evidence_id": "EP-CMP-000123-001",
  "task_id": "CMP-000123",
  "trigger": {
    "type": "compile_error",
    "error_type": "undefined_reference",
    "error_signature": "undefined reference to `InlineCostModel::estimate(BasicBlock*)'",
    "source_location": "src/pass/inline.cc:42",
    "build_target": "libcompiler",
    "build_system": "cmake_ninja"
  },
  "facts": {
    "symbol_definitions": [
      {
        "symbol": "InlineCostModel::estimate",
        "location": "include/pass/inline_cost.h:88",
        "confidence": "high",
        "source": "clangd"
      }
    ],
    "symbol_references": [
      {
        "symbol": "InlineCostModel",
        "location": "src/pass/inline.cc:42",
        "context": "InlineCostModel cost_model;",
        "confidence": "high"
      }
    ],
    "candidate_libraries": [
      {
        "name": "libcompiler_pass.a",
        "path": "build/lib/libcompiler_pass.a",
        "contains_symbol": true,
        "confidence": "high",
        "source": "nm -C"
      }
    ],
    "link_command": "g++ -o libcompiler ... -lcompiler_core (libcompiler_pass MISSING)",
    "cmake_target_link_libraries": [
      {
        "file": "src/CMakeLists.txt:15",
        "target": "libcompiler",
        "linked_libs": ["compiler_core"]
      }
    ],
    "include_paths": ["include/", "third_party/"],
    "pkg_config_results": []
  },
  "known_issue_matches": [
    {
      "issue_id": "tizen_undefined_reference_missing_link",
      "confidence": 0.78,
      "description": "符号在某 library 里存在但链接命令未包含",
      "suggested_fix_hint": "在 target_link_libraries 添加缺失的库",
      "anti_patterns": [
        "undefined reference 也可能是 C++ ABI mismatch（C++ name mangling 不一致）",
        "undefined reference 也可能是 visibility hidden",
        "undefined reference 也可能是 inline 但定义在 .cc 文件"
      ]
    }
  ],
  "negative_facts": [
    {
      "check": "nm -C build/lib/libcompiler_core.a | grep InlineCostModel::estimate",
      "result": "not_found",
      "confidence": "high",
      "scope": "build_artifacts",
      "implication": "symbol is not provided by currently linked library compiler_core"
    },
    {
      "check": "link command contains -lcompiler_pass",
      "result": "not_found",
      "confidence": "high",
      "scope": "build_config",
      "implication": "compiler_pass library is not linked despite symbol being defined there"
    },
    {
      "check": "compile_commands.json contains -D_GLIBCXX_USE_CXX11_ABI macro",
      "result": "not_found",
      "confidence": "medium",
      "scope": "build_config",
      "implication": "if default ABI mismatch, could cause undefined reference"
    }
  ],
  "log_excerpt": {
    "source": "logs/compile_raw.log",
    "line_range": [1820, 1845],
    "redacted": true,
    "char_count": 2876,
    "reason": "template_error_context",
    "content": "In file included from src/foo.cc:5:\n  In instantiation of 'class Foo<int>' ..."
  },
  "semantic_unavailable": false,
  "clangd_stale": false,
  "compile_commands_provenance": "auto_cmake_ninja",
  "degraded_reason": null,
  "ambiguous_facts": [
    {
      "fact": "InlineCostModel::estimate 可能有多个 overload",
      "candidates": [
        "InlineCostModel::estimate(BasicBlock*)",
        "InlineCostModel::estimate(Function*)"
      ],
      "confidence": "medium"
    }
  ],
  "collection_metadata": {
    "collected_at": "2026-04-22T10:02:15Z",
    "collectors_run": [
      "LogErrorParser",
      "CompileCommandCollector",
      "LinkCommandCollector",
      "SourceSymbolCollector",
      "CMakeContextCollector",
      "PkgConfigCollector",
      "KnownIssueMatcher"
    ],
    "collection_duration_ms": 320,
    "total_tokens_estimate": 1850
  },
  "schema": "evidence_packet.v1"
}
```

### 2.2 关键字段说明（v0.2 更新）

| 字段 | 含义 |
|---|---|
| `evidence_id` | 唯一标识，格式 `EP-{task_id}-{seq}` |
| `trigger` | 触发证据收集的事件，含完整定位信息 |
| `facts` | **正向**确定性事实（高置信度，来自工具）|
| `negative_facts` | **v0.2 新增**：**反向**事实，"没找到什么"（同样重要！）|
| `log_excerpt` | **v0.2 新增**：bounded + redacted 的原始日志片段（可选）|
| `semantic_unavailable` | **v0.2 新增**：clangd 不可用时为 true，告知 LLM 所有 C/C++ ref 仅为候选 |
| `clangd_stale` | **v0.3 新增**：clangd 启用但 compile_commands.json 可能 stale，结果可能不准 |
| `compile_commands_provenance` | **v0.3 新增**：clangd 启用/禁用的来源，枚举见 4.3.2 |
| `degraded_reason` | **v0.3 新增**：降级原因（auto_degraded / explicit_path_not_found / no_compile_commands_json 等）|
| `known_issue_matches` | 历史错误模式命中（含 anti_patterns）|
| `ambiguous_facts` | 不确定的信息（明确标注 medium/low confidence）|
| `collection_metadata` | 元数据，包括 token 估算（重要：让 Agent 决定是否能塞进 budget）|

#### 2.2.1 negative_facts 字段（v0.2 新增，v0.3 加 scope）

**v0.3 新增 scope 字段**：

negative_facts 的 check 在不同 scope 下含义不同。例如 "InlineCostModel 不在 libcompiler_core.a 里" 这个 check：

- 如果 scope = `build_artifacts`：在当前 build 产物里没找到。换个 build configuration（debug/release）可能就有
- 如果 scope = `source_code`：源代码里就没定义
- 如果 scope = `build_config`：build 配置（CMakeLists.txt / compile_commands.json）里没引用

`scope` 字段强制 collector 明确**negative fact 的有效范围**，避免 LLM 误推广。

**scope 枚举**：

| scope | 含义 | 例子 |
|---|---|---|
| `build_artifacts` | 当前 build 产物（.a, .so, .o 等）| nm/objdump 检查 |
| `source_code` | 源代码层（.h, .cc, .cpp）| ripgrep / clangd 搜索 |
| `build_config` | build 配置（CMakeLists.txt, compile_commands.json）| 解析 cmake 文件 |
| `environment` | 编译/运行环境（环境变量、sysroot、toolchain）| probe_env 检查 |



**为什么需要**（ChatGPT review 洞见）：

编译问题定位**不只是"找到了什么"**，**更重要的是"确认了什么没有"**。例如：

- "在 libcompiler_core.a 里找不到 InlineCostModel::estimate" —— 排除了某条修复路径
- "link command 没有包含 -lcompiler_pass" —— 锁定了真正问题
- "compile_commands.json 没有 -D_GLIBCXX_USE_CXX11_ABI" —— 排除了 ABI 假设

没有 negative facts，LLM 容易看到一个候选就下结论；有 negative facts，LLM 知道排除了什么。

**negative_facts 字段格式**：

```json
{
  "check": "具体的检查描述（最好是可复现的命令）",
  "result": "not_found / not_present / not_set / null",
  "confidence": "high / medium / low",
  "implication": "这意味着什么"
}
```

**用途**：
- 直接进入 ClineSR prompt，与 facts 并列
- LLM 看到 negative_facts 时能避免错误的修复方向

#### 2.2.2 log_excerpt 字段（v0.2 新增）

详细约束见 Compiler Agent v5.2-RC1 A5.2 节。CNEI 中：

- 由 `LogErrorParser` 或 `EvidenceCollector` 填充
- 必须经过 redaction filter
- 单 excerpt ≤ 3000 字符，整 packet ≤ 6000 字符
- 必须含 `source` / `line_range` / `reason`
- 同一个 Evidence Packet 最多 3 个 log_excerpt

#### 2.2.3 semantic_unavailable 字段（v0.2 新增）

```json
"semantic_unavailable": true | false
```

- `true`：clangd 不可用（compile_commands.json 不存在或 clangd 启动失败）
- `false`（默认）：clangd 提供了 high-confidence 数据

LLM 看到 `semantic_unavailable: true` 时：
- prompt 中包含明确提示
- 所有 C/C++ symbol references 视为 candidate（不是 truth）

### 2.3 Confidence 等级

```
high    → 来自精确工具（clangd/编译器自身），可作为决策依据
medium  → 来自启发式（tree-sitter + ctags 推断），需要 LLM 进一步判断
low     → 来自文本搜索（ripgrep），仅供参考
```

LLM 在使用 Evidence Packet 时**必须**根据 confidence 调整信任度。

### 2.4 Evidence Packet Size Budget

**硬约束**（来自 Team Contract v0.7.2 Section 5.6）：

- 单个 Evidence Packet 序列化后 token 数 ≤ `evidence_packet_max_tokens`（默认 4000）
- 超过则裁剪策略（按优先级保留）：
  1. trigger 字段（必保）
  2. high confidence facts
  3. known_issue_matches
  4. medium confidence facts
  5. low confidence facts（最先裁剪）
  6. ambiguous_facts

---

## 3. Layer 0：Build-System-Aware Collectors

### 3.1 设计意图

**核心洞察**：Tizen 项目里很多编译错误的根因**不在 .c/.cpp**，而在：

- CMakeLists.txt 的 target_link_libraries 缺失
- spec 文件的 BuildRequires 缺失
- pkg-config 找不到 .pc 文件
- linker command 中的 library order 错误
- include path 配置问题
- 条件编译 flag

**因此 Evidence Collector 必须看 build system，不只看代码。**

### 3.2 各 Collector 详细设计

#### 3.2.1 CompileCommandParser

**输入**：`compile_commands.json`（cmake 用 `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` 生成）

**输出**：每个源文件的完整编译命令、include path、defines、compiler flags

**用途**：
- 让 clangd 能精确解析
- 让 Evidence Packet 知道"这个文件实际是怎么编译的"
- 检测编译参数异常（比如某个文件缺少必要 -D 宏）

```python
class CompileCommandParser:
    def parse(self, compile_commands_path: str) -> Dict[str, CompileCommand]: ...
    def get_command_for_file(self, source_file: str) -> CompileCommand: ...
    def get_include_paths(self, source_file: str) -> List[str]: ...
    def get_defines(self, source_file: str) -> List[str]: ...
```

#### 3.2.2 LinkCommandCollector

**输入**：build 失败的链接命令（从 ninja/make verbose output 提取）

**输出**：解析后的链接命令结构

```json
{
  "linker": "g++",
  "output": "libcompiler",
  "objects": ["src/main.cc.o", "src/pass/inline.cc.o"],
  "libraries": ["compiler_core", "pthread"],
  "library_paths": ["/usr/lib", "build/lib"],
  "extra_flags": ["-O2", "-fPIC"]
}
```

**关键能力**：

- 解析链接命令找到所有被链接的库
- 检测明显缺失（比如 source 文件有 `extern "C"` 但没链对应库）
- 配合 `nm`/`objdump` 检查库是否包含特定符号

#### 3.2.3 CMakeContextCollector

**输入**：源文件路径

**输出**：影响该文件编译的所有 CMakeLists.txt 上下文

```json
{
  "source_file": "src/pass/inline.cc",
  "cmake_files": [
    {
      "path": "src/CMakeLists.txt",
      "relevant_targets": [
        {
          "name": "libcompiler",
          "type": "library",
          "sources": ["src/pass/inline.cc", "src/pass/loop.cc"],
          "link_libraries": ["compiler_core"],
          "include_directories": ["${PROJECT_SOURCE_DIR}/include"],
          "compile_options": ["-O2"]
        }
      ]
    },
    {
      "path": "CMakeLists.txt",
      "relevant_settings": {
        "CMAKE_CXX_STANDARD": "17",
        "BUILD_SHARED_LIBS": "ON"
      }
    }
  ]
}
```

**实现策略**：
- 不要求完整解析 cmake DSL（太复杂）
- 用 regex + tree-sitter 提取关键 directive（add_library / target_link_libraries / target_include_directories）
- 配合 cmake `--graphviz` 生成的依赖图作为参考

#### 3.2.4 PkgConfigCollector

**输入**：错误信息 / CMakeLists.txt 中的 pkg-config 引用

**输出**：

```json
{
  "queried_packages": ["glib-2.0", "dlog"],
  "results": [
    {
      "package": "glib-2.0",
      "found": true,
      "version": "2.66.0",
      "cflags": "-I/usr/include/glib-2.0 -I/usr/lib/glib-2.0/include",
      "libs": "-lglib-2.0"
    },
    {
      "package": "dlog",
      "found": false,
      "error": "Package 'dlog' not found"
    }
  ]
}
```

对 Tizen 项目特别有用：很多编译错误是 dlog / capi-base-common 等系统库 pkg-config 失败。

#### 3.2.5 SpecFileCollector（Phase 1A 接口预留，1.5 完整实现）

**Tizen 特化**。spec 文件控制 gbs 打包行为，但**也间接影响编译**（通过 BuildRequires、%configure 参数等）。

Phase 1A 只预留接口：

```python
class SpecFileCollector:
    def find_spec_files(self, repo_root: str) -> List[str]:
        """找到 packaging/*.spec"""
        ...
    def parse_build_requires(self, spec_file: str) -> List[str]:
        """提取 BuildRequires（Phase 1A 仅这一个方法）"""
        ...
    # Phase 1.5 扩展更多方法
```

Phase 1A 即使不实现完整解析，**收集 spec 文件 BuildRequires 列表是简单且有用的**——能帮 LLM 判断"是不是 BuildRequires 缺了某个包"。

### 3.3 Build-System Backend 矩阵

| Backend | Phase | 主要 Collector |
|---|---|---|
| cmake + ninja | 1A | CompileCommandParser, CMakeContextCollector, LinkCommandCollector |
| cmake + make | 1.5 | 同上 + make verbose parser |
| pure make | 1.5 | MakefileParser (新增) |
| gbs | 1.5 | SpecFileCollector + GbsContextCollector |

Phase 1A 只完整支持第一行。

---

## 4. Layer 1：Backend Indexers

### 4.1 tree-sitter

**用途**：

- 多语言 AST 解析（C/C++/Python/JS/Rust 等）
- 提取函数/类/变量 declaration
- 切分 source file 成 logical chunks
- **不用于**跨文件 reference resolution（tree-sitter 不擅长）

**集成方式**：

- Python: `tree-sitter` + `tree-sitter-c`/`tree-sitter-cpp` 等 language pack
- 索引结果存 SQLite

### 4.2 universal-ctags

**用途**：

- 快速生成全局符号表
- 提供"某 symbol name 可能在哪些位置"的候选列表
- 对 C/C++/Python/JS 等支持成熟

**集成方式**：

- 命令行调用 `ctags --output-format=json -R`
- 输出存 SQLite

**注意**：ctags 是**模糊的**（不解析 namespace / overload / template），结果是 candidate 不是 truth。

### 4.3 clangd / scip-clang（v0.3 修订：B++ 策略，C/C++ semantic preferred backend）

**用途**：C/C++ 精确语义查询。

**v0.3 策略升级到 B++**：

| | v0.2 原设计 | v0.3 修订（B++）|
|---|---|---|
| 默认行为 | "compile_commands.json 存在即启用" | **5-Gate 决策树**（见 4.3.1）|
| 高级用户控制 | 无 | **explicit_path override**（覆盖 build_system 检查）|
| Stale 检测 | 无 | **mtime 软检查**（stale 时仍启用 + warning）|
| 配置位置 | 散落 | **CNEIConfig**（共享配置层）|
| Benchmark 调用 | 未明确 | **build_system=None 时自动降级**（安全）|

**v0.3 修订理由**：

- **ChatGPT 指出**：Kimi 简化版把 `build_system != cmake_ninja` 放在 explicit_path 前面，导致用户显式指定路径也会被降级——过度保守
- **Kimi 指出**：compile_commands.json 可能 stale（cmake 上次跑过、CMakeLists.txt 后续修改）—— 需要软检查
- **Kimi 指出**：Benchmark Agent 调用 CNEI 时无 build_system —— 需要明确降级行为
- **Kimi 指出**：配置应放 CNEIConfig 让 Benchmark 也能用

#### 4.3.1 启用规则（v0.3 B++ 决策树）

5 个 Gate，自上而下：

```python
def select_backend_for_cpp(
    repo_root: str,
    build_system: Optional[str] = None,
    cnei_config: Optional[CNEIConfig] = None,
) -> Backend:
    """
    决策优先级（5 个 gate，自上而下）：
    1. 用户 disabled  → Degraded
    2. 用户 explicit_path 且文件存在 → Clangd（高级用户 override，跳过 build_system 检查）
    3. 用户 explicit_path 但文件不存在 → Degraded
    4. auto 模式 + build_system 不是 cmake_ninja → Degraded（安全默认，避免 gbs 陷阱）
    5. auto 模式 + 自动发现 compile_commands.json → Clangd（带 stale 软检查）
    """
    cfg = cnei_config or CNEIConfig.default()
    cc_source = cfg.clangd.compile_commands_source  # "auto" / "explicit_path" / "disabled"

    # Gate 1: 显式禁用
    if cc_source == "disabled":
        return DegradedBackend(
            reason="user_disabled",
            provenance="disabled",
        )

    # Gate 2/3: 显式路径（高级用户 override，绕过 build_system 检查）
    if cc_source == "explicit_path":
        path = cfg.clangd.compile_commands_path
        if path and Path(path).exists():
            # 信任高级用户决定，不做 stale 检查
            return ClangdBackend(
                path,
                provenance="explicit_path",
                stale_warning=False,
            )
        return DegradedBackend(
            reason="explicit_path_not_found",
            provenance="degraded",
        )

    # Gate 4: auto 模式 - build_system 安全默认
    # (Benchmark Agent 调用时 build_system=None,也走这条降级)
    if not build_system or build_system != "cmake_ninja":
        return DegradedBackend(
            reason=f"build_system_{build_system or 'unknown'}_not_cmake_ninja",
            provenance="auto_degraded",
        )

    # Gate 5: auto 模式 - 自动发现 compile_commands.json
    path = find_compile_commands_json(repo_root)
    if not path or not Path(path).exists():
        return DegradedBackend(
            reason="no_compile_commands_json",
            provenance="auto_degraded",
        )

    # 软检查 stale（不降级，仅 emit warning）
    stale_warning = False
    if _path_is_stale(path, repo_root):
        stale_warning = True
        emit_warning_event(
            "compile_commands.json may be stale (older than CMakeLists.txt); "
            "clangd results may be inaccurate. "
            "Consider running cmake to regenerate compile_commands.json."
        )

    return ClangdBackend(
        path,
        provenance="auto_cmake_ninja",
        stale_warning=stale_warning,
    )


def _path_is_stale(compile_commands_path: Path, repo_root: str) -> bool:
    """Stale 检测：compile_commands.json mtime 早于任何 CMakeLists.txt 视为可能 stale"""
    cc_mtime = compile_commands_path.stat().st_mtime
    try:
        max_cmake_mtime = max(
            f.stat().st_mtime
            for f in Path(repo_root).rglob("CMakeLists.txt")
        )
        return cc_mtime < max_cmake_mtime
    except ValueError:
        # 没有 CMakeLists.txt（不太可能，但保护一下）
        return False
```

#### 4.3.2 五种 provenance 状态

Evidence Packet 中 `compile_commands_provenance` 字段必填，枚举：

| Provenance | 含义 | clangd 是否启用 |
|---|---|---|
| `auto_cmake_ninja` | auto 模式自动发现，cmake/ninja 项目 | ✅ |
| `explicit_path` | 用户显式指定路径 | ✅ |
| `auto_degraded` | auto 模式但降级（build_system 不匹配或文件不存在）| ❌ |
| `disabled` | 用户显式禁用 | ❌ |
| `explicit_path_not_found` | 用户指定路径但文件不存在 | ❌ |

LLM 看到 provenance 后可以做相应的置信度调整。

#### 4.3.2.1 stale 时 confidence 降级（v0.3.1 新增）

**ChatGPT review 指出**：stale compilation database 给出的 high-confidence semantic result 是最危险的，会误导 LLM。仅 emit warning 不够，**必须降级 confidence**。

**规则**：当 `clangd_stale = true` 时（compile_commands.json mtime 早于任何 CMakeLists.txt mtime），由 clangd 提供的所有 semantic facts **必须**满足：

| 字段 | stale=false 时 | stale=true 时 |
|---|---|---|
| `confidence` | `high`（clangd 给出） | **降级到 `medium`** |
| `confidence_modifier` | （无） | **`stale_compile_commands`** |
| `source` | `clangd` | `clangd` |
| Evidence Packet 顶层 `clangd_stale` | `false` | **`true`** |

**实施约束**：

```python
class ClangdBackend:
    def find_definition(self, symbol, file, line):
        result = self._lsp_definition(symbol, file, line)
        # ★ v0.3.1：stale 时强制降 confidence
        confidence = "medium" if self.stale_warning else "high"
        return SymbolDefinition(
            symbol=symbol,
            location=result.location,
            confidence=confidence,
            confidence_modifier="stale_compile_commands" if self.stale_warning else None,
            source="clangd",
        )
```

**LLM prompt 处理**：

ClineSR 看到 `clangd_stale=true` 时，prompt 中包含明确提示：

> "compile_commands.json may be stale (older than CMakeLists.txt). 
> All clangd-provided semantic facts are downgraded to medium confidence. 
> Treat them as candidates pending verification with current build state. 
> Cross-reference with negative_facts and current build artifacts before drawing conclusions."

**Spike Gate 验证项**：

A18.1 Spike Gate 第 6 项扩展（Compiler 文档）：除验证 stale 检测正确触发，还需验证：

- [ ] stale=true 时，Evidence Packet 中所有 clangd 来源的 facts 都标 `confidence: medium`
- [ ] stale=true 时，所有 facts 都含 `confidence_modifier: "stale_compile_commands"`

**适用范围**（v0.3.3 新增澄清，Kimi review 反馈）：

> **本降级机制主要服务于 Compiler Agent 的 CNEI 调用路径**。
> 
> Benchmark Agent 调用 CNEI 时因 `build_system=None` 已经走 Gate 4 降级到 DegradedBackend（详见 §4.3.5 Benchmark Agent 集成），**clangd 根本未启用**，因此 stale 检测自然不会触发。Benchmark 路径的 Evidence Packet 直接标 `semantic_unavailable=true` + `compile_commands_provenance=auto_degraded`，与 stale 机制无关。

**适用矩阵**：

| Agent | clangd 是否启用 | stale 检测 | 降级 confidence |
|---|---|---|---|
| Compiler Agent（cmake_ninja + compile_commands.json）| ✅ 启用 | ✅ 触发 | ✅ medium |
| Compiler Agent（其他 build_system）| ❌ Gate 4 降级 | N/A | N/A |
| Benchmark Agent（任何 build_system，因为 build_system=None）| ❌ Gate 4 降级 | N/A | N/A |
| 任何 Agent（compile_commands.json 不存在）| ❌ Gate 5 降级 | N/A | N/A |

stale 机制仅在 clangd 实际启用时（auto_cmake_ninja / explicit_path 两种 provenance）才有意义。

#### 4.3.3 各场景行为汇总

| 场景 | 行为 | provenance |
|---|---|---|
| cmake/ninja + 新鲜 compile_commands.json | ✅ 用 clangd | `auto_cmake_ninja` |
| cmake/ninja + stale compile_commands.json | ✅ 用 clangd + stale warning + **facts 降级到 medium confidence** | `auto_cmake_ninja` (clangd_stale=true) |
| **gbs 项目 + 残留 compile_commands.json** | ❌ **降级**（避免陷阱）| `auto_degraded` |
| 用户 explicit_path（绕过 build_system 检查）| ✅ 用 clangd | `explicit_path` |
| 用户 disabled | ❌ 降级 | `disabled` |
| 没有 compile_commands.json | ❌ 降级 | `auto_degraded` |
| **Benchmark Agent 调用**（build_system=None）| ❌ **降级**（用 tree-sitter+ctags，对 benchmark 够用）| `auto_degraded` |

#### 4.3.4 降级后的 Evidence Packet 标记

无论哪种降级原因，Evidence Packet 必须包含：

```json
{
  "semantic_unavailable": true,
  "compile_commands_provenance": "auto_degraded | disabled | explicit_path_not_found",
  "degraded_reason": "build_system_gbs_not_cmake_ninja | no_compile_commands_json | ..."
}
```

ClineSR 看到 `semantic_unavailable: true` 时，prompt 中包含明确提示：
> "C++ semantic references are NOT available. All symbol references in this packet are CANDIDATES from text-based search (tree-sitter + ctags), NOT verified by compiler. Use with caution and prefer evidence from facts/negative_facts."

#### 4.3.5 Benchmark Agent 集成（v0.3 明确）

Benchmark Agent 在 B5.4 节调用 CNEI 时**不提供 build_system 参数**（因为 Benchmark 不编译）：

```python
# Benchmark Agent 内部（B5.4 集成点）
evidence = cnei.collect_evidence(
    repo_root=workspace,
    build_system=None,        # ★ 明确传 None
    cnei_config=task.cnei_config or CNEIConfig.default(),
)
# 结果：Gate 4 触发降级，返回 DegradedBackend(provenance="auto_degraded")
# Evidence Packet 中 semantic_unavailable=true
# Benchmark 用 tree-sitter + ctags 结果（对 benchmark 场景"辅助理解代码改动"够用）
```

**这是 by design**：

- Benchmark 不需要高置信度 C/C++ semantic references
- 跳过 clangd 启动节省开发板任务资源
- tree-sitter + ctags 的 medium confidence 对"找受影响函数"的辅助用途够用

#### 4.3.6 索引性能管理

- Phase 1A：clangd 在 task 开始时即时启动，索引等待时间在 budget 内
- 中等 repo（< 100 万行）：clangd 索引应 ≤ 5 分钟
- 大 repo（如 Chromium 2500 万行）：clangd 索引不可接受—— **Phase 1A 不支持 Chromium 规模**，Phase 1.5 预先索引 + shard 加载

#### 4.3.7 集成方式

- 启动 clangd 作为 LSP server（subprocess + jsonrpc）
- 通过 LSP API 查询：`textDocument/definition`、`textDocument/references`、`textDocument/hover`、`textDocument/documentSymbol`
- 备选：`scip-clang` 离线生成 SCIP 索引文件（速度慢但稳定，适合 CI 预生成）
- 失败处理：clangd 启动失败或查询超时（>10s）→ 自动降级到 ctags+tree-sitter，标 semantic_unavailable

#### 4.3.8 Spike 验证项

Phase 1A 实施前的 spike 必须验证：

- [ ] clangd 在选定 Tizen 真实 repo（cmake/ninja）上能正常启动并索引完成
- [ ] `textDocument/definition` 在 50 个抽样 symbol 上准确率 ≥ 90%
- [ ] `textDocument/references` 在 30 个抽样 symbol 上准确率 ≥ 85%
- [ ] clangd 内存占用 < 4GB for 100 万行 repo
- [ ] 启动 + 索引时间 < budget 允许范围（建议 < 5 分钟）
- [ ] **Stale 检测正确**：人工修改 CMakeLists.txt 后未跑 cmake，CNEI 应 emit stale warning
- [ ] **Gbs 陷阱避免**：在 gbs 项目中放置 stale compile_commands.json，CNEI 应降级到 `auto_degraded` 而不是 clangd

### 4.4 ripgrep（兜底）

**用途**：

- 当其他工具都找不到时的文本兜底搜索
- 查找字符串字面量、注释、文档
- 结果置信度 low

### 4.5 SQLite Cache

**用途**：

- 缓存 tree-sitter / ctags 索引结果
- 跨 task 复用（同一个 repo 多次查询不重复解析）
- 记录 file mtime + content hash，文件变更时增量更新

**Schema**（简化）：

```sql
CREATE TABLE files (
  path TEXT PRIMARY KEY,
  mtime INTEGER,
  content_hash TEXT,
  language TEXT,
  indexed_at INTEGER
);

CREATE TABLE symbols (
  name TEXT,
  kind TEXT,           -- function/class/variable/...
  file TEXT,
  line INTEGER,
  column INTEGER,
  signature TEXT,
  source TEXT,         -- 'tree-sitter' / 'ctags' / 'clangd'
  confidence TEXT,     -- 'high'/'medium'/'low'
  FOREIGN KEY (file) REFERENCES files(path)
);
CREATE INDEX idx_symbol_name ON symbols(name);
```

---

## 5. Layer 2：Code Navigation API

### 5.1 API 设计

```python
class CodeNavigationService:
    def find_definition(self, symbol: str, hint_file: Optional[str] = None) -> List[Definition]:
        """
        查找符号定义。
        - C/C++ 优先 clangd（high confidence）
        - 其他用 ctags + tree-sitter（medium confidence）
        """

    def find_references(self, symbol: str) -> List[Reference]:
        """
        查找符号引用。
        - best-effort，每个 reference 带 confidence
        - 不保证完整（特别是宏展开、template 实例化场景）
        """

    def find_callers(self, function_signature: str) -> List[Caller]:
        """
        查找函数调用点。
        - best-effort
        - 不保证 overload resolution 准确
        """

    def get_file_imports(self, file: str) -> ImportInfo:
        """
        提取 file 的 #include / import 列表。
        - 准确（基于 tree-sitter）
        """

    def get_symbol_context(self, location: Location, lines_before: int = 10, lines_after: int = 20) -> str:
        """
        获取符号位置的上下文代码片段。
        - 用于喂给 LLM
        """
```

### 5.2 返回值带 confidence

每个返回项必须含：

```python
@dataclass
class Definition:
    symbol: str
    file: str
    line: int
    column: int
    signature: Optional[str]
    confidence: str        # 'high' / 'medium' / 'low'
    source: str            # 'clangd' / 'ctags' / 'tree-sitter'
```

### 5.3 多源结果合并

当多个 backend 都返回结果时：

- clangd 结果优先（high）
- ctags 结果次（medium）
- ripgrep 结果最后（low）
- 同位置去重
- 在 Evidence Packet 中**保留多源**，让 LLM 能看到不一致情况

---

## 6. Layer 3：Evidence Collector

### 6.1 核心 API

```python
class EvidenceCollector:
    def collect_for_compile_error(
        self,
        error_event: StructuredErrorEvent,
        build_context: BuildContext,
        budget_tokens: int = 4000,
    ) -> EvidencePacket:
        """
        针对一个 structured compile error，组装 Evidence Packet。

        步骤：
        1. 根据 error_type 选择相关 Collectors
        2. 并行执行各 Collector
        3. 调用 Known Issues DB 匹配
        4. 合并、去重、按 confidence 排序
        5. 如果超过 budget_tokens，按优先级裁剪
        6. 输出 EvidencePacket
        """
```

### 6.2 错误类型 → Collector + Mandatory Negative Checks 映射（v0.3 扩展）

不同错误类型需要不同的 Collector 组合 + 必须的 negative checks。

**v0.3 修订**：增加 `mandatory_negative_checks` 列，确保不同 Collector 产出的 negative_facts 质量一致（Kimi 反馈）。

| Error Type | 触发的 Collector | Mandatory Negative Checks（必须包含的 negative_facts） |
|---|---|---|
| `undefined_reference` | LinkCommandCollector, SourceSymbolCollector, library scan (nm), CMakeContextCollector (target_link_libraries), KnownIssueMatcher | 1. nm 在所有链接库中找 symbol → 是否所有库都 not_found（scope: build_artifacts）<br>2. link command 是否包含候选库 → not_found（scope: build_config）<br>3. CMake target_link_libraries 是否包含候选库 → not_found（scope: build_config）|
| `undefined_symbol` | SourceSymbolCollector, HeaderIncludeCollector, PkgConfigCollector, KnownIssueMatcher | 1. 源代码中是否有 symbol 定义 → not_found（scope: source_code）<br>2. include path 是否包含候选 header → not_found（scope: build_config）<br>3. pkg-config 是否能解析候选包 → not_found（scope: environment）|
| `cannot_find_header` | HeaderIncludeCollector, CMakeContextCollector (include_directories), PkgConfigCollector, KnownIssueMatcher | 1. include_directories 是否包含 header 所在目录 → not_found（scope: build_config）<br>2. 系统 include 路径是否包含 → not_found（scope: environment）<br>3. pkg-config 是否能找到对应 .pc → not_found（scope: environment）|
| `type_mismatch` | SourceSymbolCollector (find_definition for type), tree-sitter (get_symbol_context), KnownIssueMatcher | 1. 调用处 type 定义和声明处是否一致 → mismatch（scope: source_code）<br>2. 是否存在 namespace 冲突 → present（scope: source_code）|
| `template_error` | SourceSymbolCollector, tree-sitter (template definition), KnownIssueMatcher | 1. template 实例化的所有类型是否满足约束 → constraint_not_met（scope: source_code）<br>2. template 特化是否存在 → not_found（scope: source_code）|
| `linker_order_error` | LinkCommandCollector (library order), KnownIssueMatcher | 1. link command 中库的相对顺序 → check_order_violation（scope: build_config）|

**实施约束**：

- 每个 Error Type 的 mandatory_negative_checks 必须由对应的 Collector 实际执行
- 如果某个 check 因为某种原因没执行（如 nm 不可用），negative_facts 中标记该 check 为 `executed: false`
- 缺失 mandatory check 不阻塞 Evidence Packet 生成，但 Evidence Packet 顶层加 warning："missing_mandatory_negative_checks: [check_name, ...]"

**为什么不强制完整**：Phase 1A 容错优先，但**有标记**让 LLM 知道证据不完整。

### 6.3 LogErrorParser（驱动入口）

**职责**：把原始 build log 解析成 structured error events。这是 Evidence Collector 的输入。

```python
class LogErrorParser:
    def parse(self, log_path: str, build_system: str) -> List[StructuredErrorEvent]:
        """
        从 build log 提取结构化错误事件。
        每个 event 含 error_type、source_location、related_symbols 等。
        """
```

**关键设计**：

- 不同 build system 用不同 parser（cmake_ninja_parser / make_parser / gbs_parser）
- 每个 parser 是 regex + heuristics 的组合
- 输出**至多 top-5 错误事件**（不全部提取，按优先级）
- 优先级：第一个 fatal error > 后续 cascading errors

### 6.4 StructuredErrorEvent

```json
{
  "event_id": "ERR-001",
  "error_type": "undefined_reference",
  "severity": "fatal",
  "raw_message": "undefined reference to `InlineCostModel::estimate(BasicBlock*)'",
  "source_location": {
    "file": "src/pass/inline.cc",
    "line": 42,
    "column": null
  },
  "related_symbols": ["InlineCostModel::estimate", "BasicBlock"],
  "build_target": "libcompiler",
  "compiler": "g++"
}
```

---

## 7. Known Issues DB

### 7.1 设计意图

**Tizen 是冷门 domain，LLM 知识有限。Known Issues DB 通过简单的"模式匹配 + 修复 hint"显著提升 Compiler Agent 准确率。**

不是 Memory Infrastructure 的替代——**是 Phase 1A 的最小可用版本，简单但有效**。

### 7.2 数据格式

YAML 文件，初始 20-30 条由团队提供：

```yaml
# known_issues.yaml

- id: tizen_cmake_missing_package_config
  description: "CMake 找不到 package configuration file"
  category: cmake_dependency
  match:
    error_regex: 'Could not find package configuration file "(\w+)Config\.cmake"'
    captures:
      - missing_package
  likely_causes:
    - "spec 文件缺少 BuildRequires"
    - "find_package 的 PATHS 不对"
    - "依赖包未安装到 staging 目录"
  evidence_to_collect:
    - SpecFileCollector
    - PkgConfigCollector
    - CMakeContextCollector
  suggested_fix_hints:
    - "在 spec 文件 BuildRequires 中加 ${missing_package}-devel"
    - "在 CMakeLists.txt 中添加 PATHS 提示"
  confidence_default: 0.78
  applicable_build_systems:
    - cmake_ninja
    - gbs

- id: tizen_undefined_reference_missing_link
  description: "符号存在但链接命令未包含对应 library"
  category: linker_error
  match:
    error_regex: 'undefined reference to `(.+)'"
    captures:
      - missing_symbol
  likely_causes:
    - "target_link_libraries 缺少必要 library"
    - "library order 错误"
    - "symbol 被 inline 但定义只在 .cc 文件"
  evidence_to_collect:
    - LinkCommandCollector
    - SourceSymbolCollector  # 找 symbol 定义在哪个 library
  suggested_fix_hints:
    - "添加缺失的 target_link_libraries"
    - "调整 library link order"
  confidence_default: 0.75
  applicable_build_systems:
    - cmake_ninja
    - cmake_make
    - gbs

# ... 更多条目
```

### 7.3 匹配机制

```python
class KnownIssueMatcher:
    def match(self, error_event: StructuredErrorEvent) -> List[KnownIssueMatch]:
        """
        将 structured error event 匹配到 Known Issues DB。
        - 用 error_regex 匹配 raw_message
        - 用 build_system 过滤
        - 返回所有匹配，按 confidence 排序
        """
```

返回值进入 Evidence Packet 的 `known_issue_matches` 字段。

### 7.4 数据治理（v0.2 完整重写，v0.3 加初始数据准入标准）

**v0.3 新增 7.4.0 节初始数据准入标准**（Kimi review 反馈）。

**v0.2 修订理由**：ChatGPT review 指出"Known Issues DB 没人管会变成历史经验垃圾桶，最后误导 LLM"。v0.2 加完整治理 schema。

#### 7.4.0 初始数据准入标准（v0.3 新增）

**问题**（Kimi 指出）：CNEI v0.2 说"初始 20-30 条由团队提供"，但没定义谁提供、什么时候、质量门槛。如果初始数据质量不高（缺 anti_patterns、owner 不明确），Known Issues DB 会变成"历史经验垃圾桶"。

**初始数据来源**：

- **谁提供**：Tizen build team + Compiler Agent 开发团队联合提供
- **什么时候**：**Phase 1A Sprint 0**（实施开始前）提交首版 known_issues.yaml
- **总量**：**20-30 条**（覆盖 Tizen 高频错误模式）
- **审核**：用户（你）+ 至少 1 个外部 AI（Claude/ChatGPT/Kimi）review

**单条 Known Issue 准入标准**（不满足则拒绝合并）：

| 准入项 | 要求 | 
|---|---|
| 验证案例 | 必须有至少 **1 个 Tizen 真实 repo 上的验证案例**（含 error log + 修复 patch）|
| anti_patterns | 必须有至少 **3 条 anti_patterns**（不能为空列表）|
| owner | 必须明确（联系 email，不能是空）|
| confidence_default | 初始值 **≤ 0.8**（避免盲目自信）|
| supported_error_types | 必须明确列出**适用的 error_type 枚举值**（不能是 catch-all）|
| supported_build_systems | 必须明确（cmake_ninja / cmake_make / gbs / make 至少之一）|
| validated_count | 初始 = 0 |
| false_positive_count | 初始 = 0 |
| status | 初始 = "active" |

**Phase 1A 治理工作流**：

```
准入审核（Phase 1A Sprint 0）
   ↓
合并到 data/known_issues.yaml
   ↓
Compiler Agent 实际运行（Phase 1A Sprint 1-N）
   ↓
trace 记录每次命中 + 用户是否真应用了 hint
   ↓
Phase 1A 末期人工 review（Sprint 6 / M1 验收前）
   ↓
更新 validated_count / false_positive_count
   ↓
满足条件的条目升级 confidence
   ↓
误报率高的条目降级或 deprecated
```

**自动降级规则**（与 7.4.1 governance schema 中 `auto_downgrade` 字段对应）：

- false_positive_rate > 0.3 且 validated_count >= 10 → confidence_default × 0.7
- false_positive_rate > 0.5 → status: under_review（停用 hint 但保留数据）
- 连续 3 个月无命中 → status: deprecated（不再 hint，但保留供研究）

#### 7.4.1 完整 governance schema（每条 Known Issue 必须有的字段）

```yaml
- id: tizen_undefined_reference_missing_link
  
  # 基本信息（必填）
  description: "符号存在但链接命令未包含对应 library"
  category: linker_error
  
  # 匹配规则（必填）
  match:
    error_regex: 'undefined reference to `(.+)'"
    captures:
      - missing_symbol
  
  # 适用范围（必填，避免过度匹配）
  applicable_build_systems:           # 必填，禁止留空
    - cmake_ninja
    - cmake_make
    - gbs
  
  # ★ v0.3 新增：明确支持/不支持的 error_type（避免跨类型乱匹配）
  supported_error_types:              # 必填
    - undefined_reference
  unsupported_error_types:            # 选填，建议列出"看起来像但不适用"
    - runtime_crash
    - test_failure
  applicable_toolchains:              # ★ v0.2 新增，必填
    - gcc
    - clang
  applicable_languages:               # ★ v0.2 新增
    - c
    - cpp
  
  # 证据要求（必填）
  evidence_requirements:              # ★ v0.2 新增（之前的 evidence_to_collect 升级）
    must_have:                        # 这些 evidence 必须存在才视为命中
      - link_command
      - symbol_definitions
    optional:
      - candidate_libraries
  
  # 修复建议（必填）
  likely_causes:
    - "target_link_libraries 缺少必要 library"
    - "library order 错误"
  suggested_fix_hints:
    - "添加缺失的 target_link_libraries"
    - "调整 library link order"
  suggested_fix_type:                 # ★ v0.2 新增
    - cmake_modification
    - link_command_modification
  
  # ★ v0.2 新增：anti_patterns（避免过度匹配）
  anti_patterns:
    - "undefined reference 也可能是 C++ ABI mismatch（_GLIBCXX_USE_CXX11_ABI）"
    - "undefined reference 也可能是 visibility hidden（attribute __visibility__）"
    - "undefined reference 也可能是 inline 函数定义只在 .cc 文件而非 .h"
    - "undefined reference 也可能是 C/C++ linkage 混用（extern \"C\"）"
    - "undefined reference 也可能是 template 实例化缺失"
  
  # Confidence 与统计
  confidence_default: 0.75            # 初始 confidence
  
  # ★ v0.2 新增：治理元数据
  owner: "tizen-build-team@samsung.com"
  created_at: "2026-03-15"
  updated_at: "2026-04-01"
  validated_count: 0                  # 命中后被人工确认正确的次数
  false_positive_count: 0             # 命中后被人工标记误报的次数
  last_validated_at: null
  status: "active"                    # active | deprecated | under_review
  
  # ★ v0.2 新增：自动降级机制
  auto_downgrade:
    threshold_false_positive_rate: 0.3   # 误报率超过 30% 自动降级 confidence
    threshold_min_validations: 10         # 至少 10 次验证后才计算误报率
```

#### 7.4.2 治理工作流

**新增条目**：

```
开发者 PR 提交新 Known Issue
  ↓
Lint 工具检查 schema 完整性（必填字段、anti_patterns 存在）
  ↓
团队 review（owner / 描述准确性 / 匹配规则合理性）
  ↓
合并到 data/known_issues.yaml
  ↓
初始 status: active, confidence_default 由提交者填
```

**生命周期管理**：

- 每次 Compiler Agent 完成 task：trace 中记录 known_issue_matches + 用户是否真的应用了 hint
- 定期任务（Phase 1.5 自动化，Phase 1A 人工）：
  - 计算每条 Known Issue 的 false_positive_rate
  - false_positive_rate > 0.3 且 validated_count >= 10 → 自动降级 confidence
  - false_positive_rate > 0.5 → 标记 status: under_review
  - 连续 3 个月无命中 → 标记 status: deprecated

#### 7.4.3 LLM 使用 Known Issues 的约束（v0.2 强化）

**重要**：Known Issues 是 hint，不是 truth。Cline prompt 中**必须**含以下提示：

```
Known Issue matches are HINTS based on historical patterns. They may be:
- Outdated (codebase evolved)
- Over-fitting (anti_patterns may apply)
- Wrong (false positives exist)

ALWAYS verify hints against current evidence (facts, negative_facts).
If anti_patterns apply, prefer current evidence over the hint.
```

#### 7.4.4 Phase 1.5 升级路径

Phase 1A 完成后，Known Issues DB 升级为 Memory Infrastructure：

- 自动从历史 trace 提取候选条目（基于"修复成功"模式）
- 团队 review 后合并到 known_issues.yaml
- 向量索引 + 语义匹配（不仅 regex）
- 跨 repo 共享（同公司多个产品）

但 Phase 1A 仍然只用简单 YAML + regex 匹配。

### 7.5 与 Cognitive Boundary 的关系

**Known Issues DB 不是 Memory，不会"自我修改"**。匹配结果作为 `prior_context` 传给 LLM，**LLM 仍然是最终决策者**：

- ✅ 命中后 hint 给 LLM："这可能是已知问题 X，历史修法是 Y"
- ❌ 不自动应用 fix
- ❌ 不绕过 LLM 直接 patch

这维持了 Cognitive Boundary 完整性。

---

## 8. 性能与规模约束

### 8.1 Phase 1A 性能目标

| 操作 | 目标 |
|---|---|
| 单次 Evidence Packet 生成 | < 2 秒 |
| 初次索引中等 repo（10万行）| < 60 秒 |
| 增量更新（10 个文件改动）| < 5 秒 |
| 单次 Known Issue 匹配 | < 100ms |

### 8.2 Phase 1A 规模约束

| 指标 | 上限 |
|---|---|
| Repo 代码行数 | 100 万行 |
| SQLite 索引大小 | < 500 MB |
| 内存占用 | < 2 GB |

**超出此规模 Phase 1A 不保证可用**，留 Phase 1.5 扩展到 Chromium 级别（2500 万行）。

### 8.3 Phase 1.5 扩展方向

- SCIP-clang 离线索引（避免 clangd 实时启动慢）
- Index sharding（按目录分片）
- Distributed cache（多开发者共享索引）

---

## 9. 与其他组件的集成

### 9.1 与 Compiler Agent 集成

Compiler Agent 状态机加一个新阶段：

```
... compile (failed) → summarize_log → parse_errors → collect_evidence → analyze (with evidence) → ...
                                            ↑
                                            ↓
                              StructuredErrorEvent[]
                                            ↓
                              EvidencePacket (per error)
                                            ↓
                              ClineSR analyze_compile_failure
                              (input.prior_context.evidence_packet_summary)
```

详见 Compiler Agent v5.2 文档。

### 9.2 与 Benchmark Agent 集成

Benchmark Agent 在 Phase 1B 只用到 CNEI 的有限部分：

- Symbol search（定位 benchmark 涉及的代码）
- File context（喂给 ClineSR 做 regression 分析）

**不用 Evidence Collector**（Benchmark 的"错误"性质不同，不适合 EvidencePacket 抽象）。

### 9.3 与 Memory Infrastructure 集成（Phase 1.5）

Phase 1.5 引入完整 Memory 后：

- Known Issues DB 升级为 Memory 的一部分
- Memory 通过 `prior_context.similar_failures` 字段输入给 LLM
- Memory 与 CNEI 共享底层 SQLite（不重复造数据库）

---

## 10. 代码骨架

### 10.1 目录结构

```
infrastructure/code_navigation_evidence/
├── __init__.py
├── service.py                        # 顶层服务入口
├── data_models.py                    # EvidencePacket, Confidence 等 dataclass
├── layer0_build_system/
│   ├── compile_command_parser.py
│   ├── cmake_context_collector.py
│   ├── link_command_collector.py
│   ├── pkg_config_collector.py
│   └── spec_file_collector.py
├── layer1_backends/
│   ├── tree_sitter_indexer.py
│   ├── ctags_indexer.py
│   ├── clangd_client.py
│   ├── ripgrep_client.py
│   └── sqlite_cache.py
├── layer2_navigation/
│   ├── navigation_service.py
│   └── result_merger.py
├── layer3_evidence/
│   ├── log_error_parser/
│   │   ├── base_parser.py
│   │   ├── cmake_ninja_parser.py
│   │   ├── make_parser.py            # Phase 1.5
│   │   └── gbs_parser.py             # Phase 1.5
│   ├── evidence_collector.py
│   └── error_type_router.py
├── known_issues/
│   ├── matcher.py
│   ├── loader.py
│   └── data/
│       └── known_issues.yaml         # 20-30 条初始数据
└── tests/
    └── ...
```

### 10.2 顶层 API

```python
# infrastructure/code_navigation_evidence/service.py

class CodeNavigationEvidenceService:
    """CNEI 顶层服务，Compiler Agent / Benchmark Agent 直接调用"""

    def __init__(self, config: CNEIConfig):
        self.cache = SqliteCache(config.cache_path)
        self.navigation = CodeNavigationService(self.cache, config)
        self.collector = EvidenceCollector(self.navigation, config)
        self.known_issues = KnownIssueMatcher(config.known_issues_path)

    def index_repo(self, repo_path: str, force_reindex: bool = False) -> IndexResult:
        """索引一个 repo"""

    def find_definition(self, symbol: str, hint_file: Optional[str] = None) -> List[Definition]:
        """转发到 navigation"""
        return self.navigation.find_definition(symbol, hint_file)

    def collect_evidence(
        self,
        error_event: StructuredErrorEvent,
        build_context: BuildContext,
        budget_tokens: int = 4000,
    ) -> EvidencePacket:
        """收集证据包"""
        evidence = self.collector.collect_for_compile_error(
            error_event, build_context, budget_tokens
        )
        # 增加 known issue 匹配
        evidence.known_issue_matches = self.known_issues.match(error_event)
        return evidence

    def parse_build_log(
        self,
        log_path: str,
        build_system: str = "cmake_ninja",
    ) -> List[StructuredErrorEvent]:
        """从 build log 提取 structured events"""
        parser = self.collector.log_parser_for(build_system)
        return parser.parse(log_path)
```

---

## 11. 配置（v0.3 修订）

### 11.1 CNEIConfig 完整定义

```yaml
# config/cnei.yaml
indexers:
  tree_sitter:
    enabled: true

  ctags:
    enabled: true

  clangd:
    # v0.3 新增：clangd 启用策略
    enabled: auto              # auto / always / never
    compile_commands_source: auto   # auto / explicit_path / disabled
    compile_commands_path: null     # 当 source=explicit_path 时使用
    startup_timeout_sec: 60        # clangd 启动超时
    query_timeout_sec: 10           # 单次 LSP 查询超时
    memory_limit_mb: 4096           # clangd 进程内存上限

  ripgrep:
    enabled: true

storage:
  sqlite_path: ".cnei_cache/index.sqlite"
  cache_retention_days: 30

evidence_packet:
  max_total_tokens: 4000           # 整 packet token 上限
  max_log_excerpt_chars: 3000     # 单 excerpt 字符上限
  max_log_excerpts_per_packet: 3  # 每 packet 最多 excerpt 数

known_issues:
  yaml_path: "data/known_issues.yaml"
  enable_auto_downgrade: true     # 启用 false_positive_rate 自动降级
```

### 11.2 配置传递路径

CNEI 是共享基础设施，配置传递路径如下：

```
TaskInput.payload.cnei_config (可选 override)
   ↓ Agent Controller 透传
CNEI Service initialization
   ↓ 合并默认 + override
Effective CNEIConfig
```

**Compiler Agent / Benchmark Agent 在 TaskInput 中通过可选字段 `cnei_config` override 默认配置**，不在 Agent 自己定义 CNEI 字段。

### 11.3 多 Agent 共享 CNEIConfig

`compile_commands_source` 等字段位于 CNEIConfig，**Benchmark Agent 调用 CNEI 时也使用同一套配置**。这避免了：

- Compiler 和 Benchmark 配置不一致
- 同一 repo 在不同 Agent 中得到不同行为
- 配置散落在多份 Agent 文档中

## 12. 测试策略

### 12.1 单元测试

- 每个 Collector 单独测
- 每个 Parser 用真实 build log fixture 测
- KnownIssueMatcher 用模拟 error event 测

### 12.2 集成测试

- 端到端：从真实 cmake/ninja 项目的失败 build log → Evidence Packet 输出
- 准确率测试：手工标注一组"理想 Evidence Packet"，自动测试匹配度
- 性能测试：中等规模 repo 索引 + 查询时延

### 12.3 测试 fixture

需要准备：

- 1 个小型 cmake/ninja toy 项目（含 5-10 种 deliberate compile errors）
- 1 个中等规模 Tizen 开源 repo（用于性能测试）
- 一组真实 Tizen 编译错误 log（用于回归测试）

---

## 13. 待决定事项（留给实施验证）

| 事项 | 决策时机 |
|---|---|
| clangd 启动 vs scip-clang 离线哪个更适合 Tizen 项目 | Sprint 1-2 POC |
| Evidence Packet schema 是否需要扩展更多字段 | Sprint 4-5 真实场景验证 |
| Known Issues DB 命中率多少算"有效" | Phase 1A 末验收 |
| SQLite vs 其他存储（lmdb / rocksdb）的性能取舍 | Sprint 7 性能压测 |

---

## 14. v0.1 → v1.0 升级条件

v0.1 → v1.0 升级需满足：

- Phase 1A 实施完成
- 至少 1 个真实 Tizen repo 验证通过
- Evidence Packet 准确率 ≥ 65%（人工评估）
- Known Issues DB 命中率 ≥ 30%（在 Tizen 错误日志上）
- 性能目标达到

---

**文档结束**
