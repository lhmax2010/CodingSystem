# Benchmark Skill 框架设计 v0.2.1

**版本**：v0.2.1（Phase 1B 实施候选，针对 ChatGPT + Kimi v0.2 review 小修）
**状态**：Implementation Candidate（与 Benchmark Agent v5.2-RC2.3 同步成熟度）
**关联文档**：
- 《Agent Team Contract v0.7.2》（文档 00）—— 特别是 5a / 8.3.1 节
- 《Benchmark Agent v5.2-RC2.3》（文档 03）—— 特别是 B5.1 / B7
- 《CNEI v0.3.3》（文档 06）

**文档目的**：完整规范 Benchmark Agent 的 **用户扩展机制 Skill** —— Manifest schema、Implementation 接口、Runtime 调度、Sandbox guardrails、示例 Skill 集、用户编写指南。这是 Phase 1B 实施 Skill 体系的完整设计基线。

**版本历程**：
- v0.1：初版
- v0.2：ChatGPT + Kimi 联合 review 修订（sandbox 诚实化 / ctx.exec API / metric schema / artifact 机制 / device_state_dirty）
- **v0.2.1（本版）**：ChatGPT + Kimi v0.2 review 小修（Trust Model / device path resolution / artifact name 安全 / Trust Model registered Skill 禁 high_risk / 兼容性投资动机）

**v0.2 修订摘要**（针对 v0.1 review 反馈）：

| # | 反馈来源 | 修订内容 |
|---|---|---|
| 1 | Kimi | **Sandbox 表述诚实化**：Phase 1B 不引入 monkey patch，承认 best-effort policy enforcement |
| 2 | Kimi | **allowed_commands 用精确匹配**（shlex + canonical path），禁 startswith；推荐 `ctx.device.exec(argv=[...])` |
| 3 | Kimi | **timeout 语义统一**：明确 timeout_sec 是单次 setup+run+teardown 的 timeout |
| 4 | Kimi | **3 个示例 Skill 修正**：cpu_microbench 改名 + file_io 去 drop_caches + memory_alloc 参数化 |
| 5 | ChatGPT | **5 个示例补 `ctx.workspace.write` / `ctx.env.get` 用法展示** |
| 6 | Kimi | **metric schema 增强**：加 aggregation / max_cv_percent / outlier_policy / min_samples per-metric |
| 7 | Kimi | **artifact 机制统一**：manifest declared + RunResult.artifacts 命名空间规则 |
| 8 | Kimi | **platform-specific permissions 预留**：v0.2 新增 `required_permissions_by_platform` 选填字段 |
| 9 | Kimi | **"不影响其他 Skill"加 device_state_dirty 条件**：destructive / cleanup_failed 时后续 Skill 必须重 check env |

**v0.2.1 修订摘要**（小修版，针对 v0.2 review）：

| # | 反馈来源 | 修订内容 |
|---|---|---|
| 1 | ChatGPT | **新增 Skill Trust Model**：local/dev / registered/team-shared / untrusted external 三级信任，registered 必须 static scan warning 清零，untrusted external Phase 1B 不支持（§2.6 新增） |
| 2 | ChatGPT + Kimi | **device 命令 canonical path 在 device 侧解析**：host 命令用 shutil.which，device 命令通过 DeviceAdapter `command -v` 解析（§5.4.2 修订） |
| 3 | ChatGPT | **registered Skill 默认禁 high_risk shell**：除非 manifest 显式声明 `allow_high_risk_shell: true`（§2.1 + §5.4 修订） |
| 4 | ChatGPT | **Artifact name 安全规则**：禁 slash / 绝对路径 / path traversal（§5.9 新增） |
| 5 | Kimi | **§5.9 Artifact 冲突规则澄清**：manifest vs ctx.artifacts.save vs RunResult.artifacts 三者关系明确（§5.9 修订） |
| 6 | Kimi | **§7.4 加"未来兼容性投资"动机说明**：缓解"反正不强制"心理 |
| 7 | ChatGPT | **workspace_file_io 命名加 "_smoke" 强调定位**：避免误用作存储 benchmark |

**v0.2.1 修订量**：< 2000 字，纯实施细节小修。

**关于 sandbox 的关键决定**（v0.2 重要架构判断）：

> v0.2 **明确不引入 monkey patch / import hook**。
> Phase 1B 是 **best-effort policy enforcement**，不是真 sandbox。
> 真正的隔离在 Phase 1.5 通过**容器化**实现。
> 100 人内部场景**假设用户合作**，不做防御性运行。

理由：
- monkey patch 容易被绕过（`importlib.reload` / `__import__` 直接 / `os.popen` 等），做了反而给"安全错觉"
- 真正的隔离需要容器（Phase 1.5 计划），不要走两次
- Phase 1B 焦点是**验证 Manifest contract 设计是否对 + Skill 写起来是否顺**，不是验证安全边界

---

## 0. 设计哲学

### 0.1 关键判断：Skill 是用户扩展，不是框架代码

> **Benchmark Agent 内部 Tool 是 Agent 开发者写的固定流程；Skill 是 Agent 用户（Tizen 开发者）写的具体测试场景。**

这就像 pytest 框架 vs 用户写的 test case：

| 对照 | pytest | Benchmark Agent |
|---|---|---|
| 框架 | pytest core | Benchmark Agent + Tool 层 |
| 用户扩展 | `test_*.py` | `skill.yaml + skill.py` |
| 框架职责 | 调度、收集、断言、报告 | 调度、warmup/repeat、统计、报告 |
| 用户职责 | 写测试 case | 写 benchmark 场景 |

### 0.2 Cognitive Boundary 在 Skill 中的体现

- **Skill 不参与 LLM 决策**：Skill 是确定性执行单元，不调 ClineSR
- **Skill 输出数据**，LLM 看 **Skill Card**（精简摘要）+ benchmark 结果，**不看 Skill 源代码**
- **Skill Manifest 是 contract**：runtime 强制 enforce，不是说明文档

### 0.3 user-authored but runtime-restricted

继承 Team Contract 8.3.1：

- **用户可以写**：业务逻辑、复杂指标采集、错误处理
- **必须通过受控 SDK**：`ctx.device.shell()` / `ctx.workspace.read()` / 等
- **不允许直接调底层**：`subprocess.run()` / `os.system()` / `open(<abs_path>)` / `requests.get()` 等

---

## 1. Skill 三要素总览

每个 Skill 由 3 部分组成：

```
my_skill/
├── skill.yaml          # Manifest: runtime-enforced contract
├── skill.py            # Implementation: 业务逻辑代码
└── （Skill Card 自动从 skill.yaml 生成，无独立文件）
```

| 要素 | 谁写 | 谁读 | 角色 |
|---|---|---|---|
| **Manifest** | 用户 | Runtime 强制 enforce + Skill Card 生成器 | **Contract** |
| **Implementation** | 用户 | SkillRuntime 执行 | **Code** |
| **Card** | 自动生成 | ClineSR | **LLM-friendly 摘要** |

---

## 2. Manifest（skill.yaml）完整规范

### 2.1 Manifest schema 完整字段

```yaml
# ============================================================
# 必填字段（缺失则 Skill 加载失败）
# ============================================================

# 全局唯一 ID，规则：小写字母 + 数字 + 下划线，不超过 64 字符
skill_id: video_player_startup

# 版本号，遵循 semver
version: 1.0.0

# 简短描述（≤ 200 字符，给 user + LLM 看）
description: "测量 Tizen 视频播放器冷启动时间"

# 详细描述（可选，markdown 格式）
detailed_description: |
  本 Skill 测量 Tizen 设备上 video player 应用的冷启动时间。
  流程：
  1. 强制关闭已运行的 player
  2. 清理 cache
  3. 通过 sdb shell 启动 player
  4. 等待 player.started 事件
  5. 记录启动耗时

# 支持平台（至少一个）
target_platforms:
  - x86            # 在 x86 工作站执行
  - tizen_device   # 在 Tizen 开发板执行
  # 也可以两个都填，但 Skill 必须根据 ctx.platform 适配

# 必需权限（runtime 强制 enforce）
# v0.2 简单方案：全局权限（适用所有 target_platforms）
required_permissions:
  - device.shell           # 在开发板 shell
  - device.push            # 推文件到开发板
  - device.pull            # 从开发板拉文件
  - device.app_launch      # 启动 Tizen 应用
  - device.app_terminate   # 终止 Tizen 应用
  - host.shell             # 在 host 执行 shell（用于 build 阶段）
  - host.read_workspace    # 读 workspace
  - host.write_workspace   # 写 workspace
  # network 默认禁用，需显式声明:
  # - network              # 允许 ctx.network.fetch()

# v0.2 选填新增：platform-specific 权限（覆盖 required_permissions）
# 当一个 Skill 同时支持多平台、但不同平台需要不同权限时使用
# 如果声明此字段，runtime 优先使用此字段；否则 fallback 到 required_permissions
# Phase 1B 简单实现：runtime 读取，但 LSP enforcement 与 required_permissions 等价
# Phase 1.5 增强：根据实际 platform 自动选择权限子集
# required_permissions_by_platform:
#   x86:
#     - host.shell
#     - host.read_workspace
#   tizen_device:
#     - device.shell
#     - device.push
#     - device.pull

# 单次完整执行（setup + run + teardown）的 timeout（秒）
# v0.2 修订：明确 timeout_sec 是单次 setup+run+teardown 的总和，不是仅 run()
# 总 Skill 执行时间 = timeout_sec * (warmup_repeats + repeats) + overhead
# SkillRuntime 在每次 repeat 的 setup+run+teardown 整体上 enforce 这个 timeout
timeout_sec: 300

# 指标 schema（必填，runtime 校验 run() 输出）
# v0.2 增强：每个 metric 可声明 noise policy，让 Validity Contract 可 per-metric 调优
metrics:
  startup_time_ms:
    type: number          # number / integer / boolean
    unit: ms              # ms / s / mb / kb / percent / count 等
    lower_is_better: true # true / false
    threshold_regression_percent: 5.0  # 此 metric 的 regression 阈值
    description: "从启动命令到 player.started 事件的耗时"
    # v0.2 新增：noise policy（选填，覆盖 Benchmark Validity Contract 默认值）
    aggregation: median        # median / mean / min / max（默认 median）
    max_cv_percent: 5.0        # 高于此值 emit variance_flag（默认 5%）
    outlier_policy: iqr        # iqr / zscore / none（默认 iqr）
    min_samples: 5             # 少于此值 result_invalid（默认 5）
  peak_memory_mb:
    type: number
    unit: mb
    lower_is_better: true
    threshold_regression_percent: 3.0
    description: "启动期间峰值内存"
    # memory 类型 metric 通常波动小，可配置更紧 max_cv
    aggregation: median
    max_cv_percent: 2.0        # 比时间指标更紧
    outlier_policy: iqr
    min_samples: 5

# ============================================================
# 选填字段
# ============================================================

# Trust Model（v0.2.1 新增）
# local：本地开发，static scan warning 不阻止
# registered：团队共享，必须 static scan 清零
trust_level: local          # local / registered

# 是否允许 ctx.device.shell(..., high_risk=True)（v0.2.1 新增）
# 仅当 trust_level=registered 且本字段=true 时，registered Skill 可用 high_risk shell
# trust_level=local 时此字段被忽略（local 总是允许 high_risk shell）
allow_high_risk_shell: false

# 测试统计参数（如不填走 Benchmark Validity Contract 默认值）
warmup_repeats: 1        # 默认 1
repeats: 5               # 默认 5
retries: 0               # 默认 0（区别于 Benchmark Agent 的 rerun）

# 副作用声明（用于审计 + destructive action 强制声明）
side_effects:
  - launch_app           # 启动应用
  - terminate_app        # 终止应用
  - clear_cache          # 清空应用 cache
  # destructive actions（需显式声明，否则 hard fail）:
  # - reboot_device      # 重启设备
  # - format_storage     # 格式化存储
  # - flash_firmware     # 刷固件

# Artifact 产出（runtime 拉取并落 artifact）
artifacts:
  - name: logcat
    type: log
    pull_from: "/tmp/logcat_{repeat_idx}.log"  # device 路径
    on: "always"          # always / on_failure / on_success
  - name: perf_report
    type: data
    pull_from: "/tmp/perf_{repeat_idx}.data"
    on: "always"

# 清理是否必须（runtime 保证 teardown 执行）
cleanup_required: true

# 网络默认禁用（如需要需显式声明 + 在 required_permissions 中加 network）
network: false

# 命令 allowlist（如填则 ctx.device.shell() / ctx.host.shell() 调用这些命令外的会被 block）
allowed_commands:
  - "/usr/bin/sdb"
  - "/usr/bin/dlogutil"
  - "/usr/bin/app_launcher"
  - "am"                      # Tizen Activity Manager
  - "pkgcmd"
  - "rm"                      # 受限 rm（只允许 ctx.workspace 范围内）

# 命令 denylist（兜底防护）
denied_commands:
  - "rm -rf /"
  - "dd if=/dev/zero of=/dev/sda"
  - "mkfs.*"
  - "fdisk"

# Python 依赖（runtime 在 sandbox 中安装）
dependencies:
  - "numpy>=1.24,<2.0"
  - "pyyaml>=6.0,<7.0"

# Metadata（信息性）
metadata:
  author: "tizen-perf-team@samsung.com"
  created_at: "2026-04-15"
  tags:
    - startup
    - video
    - critical
```

### 2.2 Manifest 字段必填性

| 字段 | 必填 | 备注 |
|---|---|---|
| `skill_id` | ✅ | 全局唯一 |
| `version` | ✅ | semver |
| `description` | ✅ | ≤ 200 字符 |
| `target_platforms` | ✅ | 至少一个 |
| `required_permissions` | ✅ | 可空数组但字段必须存在 |
| `timeout_sec` | ✅ | > 0；语义为**单次 setup+run+teardown 总耗时** |
| `metrics` | ✅ | 至少一个 metric |
| `metrics.*.aggregation` | 选填 | v0.2 新增；默认 median |
| `metrics.*.max_cv_percent` | 选填 | v0.2 新增；默认 5.0 |
| `metrics.*.outlier_policy` | 选填 | v0.2 新增；默认 iqr |
| `metrics.*.min_samples` | 选填 | v0.2 新增；默认 5 |
| `cleanup_required` | ✅ | true / false |
| `required_permissions_by_platform` | 选填 | v0.2 新增；覆盖 required_permissions |
| `trust_level` | 选填 | v0.2.1 新增；默认 `local`；可选 `registered` |
| `allow_high_risk_shell` | 选填 | v0.2.1 新增；默认 `false`；仅 `trust_level=registered` 时有意义 |
| 其他 | 选填 | 见 schema |

### 2.3 destructive side_effects 强制声明

以下 side_effect 必须**显式声明**在 manifest 中，否则 runtime 在 setup 阶段就阻止 Skill 加载：

- `reboot_device`
- `format_storage`
- `flash_firmware`
- `factory_reset`

声明后，runtime 在执行前 emit warning event 到 trace（让 PM 能审计 destructive 操作）。

### 2.4 Manifest 强制 enforce 规则

| Manifest 声明 | Runtime 行为 |
|---|---|
| `timeout_sec` | 超时强制 SIGKILL |
| `required_permissions` | ctx API 调用前检查 |
| `allowed_commands` | `ctx.*.shell(cmd)` 中校验 cmd 首词 |
| `denied_commands` | 同上反向校验 |
| `network: false` | `ctx.network.*` 调用直接抛 `SkillViolationError` |
| `metrics` | `run() return RunResult(metrics=...)` 中 keys 必须匹配 schema |
| `cleanup_required: true` | 即使 run() 抛异常 teardown 仍执行 |
| `side_effects` 含 destructive | 执行前 warning event |

**违反 Manifest 声明触发 `SkillViolationError`**，转成 `skill_violation` FailureEnvelope，**不影响其他 Skill**。

### 2.5 Skill Card 自动生成

Skill Card 由 `SkillCardGenerator` 从 Manifest 自动提取，**不含 Python 源码**。

```text
Skill: video_player_startup (v1.0.0)
Purpose: 测量 Tizen 视频播放器冷启动时间
Platform: tizen_device
Inputs: implicit (test_video.mp4 in workspace, app pre-installed)
Outputs:
  - startup_time_ms (number, ms, lower is better, regression threshold 5%)
  - peak_memory_mb (number, mb, lower is better, regression threshold 3%)
Side effects: launch_app, terminate_app, clear_cache (cleanup required)
Stats: warmup=1, repeats=5
Network: disabled
Timeout: 300s
```

ClineSR 在分析 benchmark 结果时只看到 Card，**绝不看完整 manifest 或 .skill.py 源码**（避免 token 爆炸 + 安全风险）。

### 2.6 Skill Trust Model（v0.2.1 新增）

**ChatGPT review 反馈**：Phase 1B sandbox 是 best-effort，会有用户觉得"反正不强制，我直接 subprocess 算了"。需要一个治理机制弥补 sandbox 不足：**通过 Skill 注册门槛形成"团队共享必须规范"的软约束**。

**三级 Trust Model**：

| Trust Level | 适用场景 | static scan 处理 | high_risk shell 处理 | SkillRegistry 注册 |
|---|---|---|---|---|
| **`local`**（默认） | 个人开发 / 本地调试 | warning，不阻止运行 | 允许 | 不可注册到 team registry |
| **`registered`** | 团队共享，正式 benchmark | **必须清零所有 warning** | **默认禁止**（除非 manifest 声明 `allow_high_risk_shell: true`）| 注册到 team registry |
| **`untrusted_external`** | 外部 Skill / 第三方提供 | **Phase 1B 不支持** | N/A | N/A，Phase 1.5 容器化后再支持 |

**关键判断**：

- Phase 1B 不引入真 sandbox，但通过 **trust level 治理** 弥补
- 个人开发友好（local 宽松）
- 团队正式 Skill 必须规范（registered 严格）
- 外部不可信 Skill 推迟到 Phase 1.5 容器化后再支持

**Manifest 中声明 trust_level**：

```yaml
# 在 skill.yaml 中（选填，默认 local）
trust_level: registered      # local / registered
allow_high_risk_shell: false # 仅 registered 需要时为 true（默认 false）
```

**SkillRegistry 注册流程**（v0.2.1 新增）：

```
$ benchmark-agent register-skill my_skills/video_player_startup/
  Validating manifest... ✓
  Running static scan...
    ✓ No subprocess usage
    ✓ No direct file open()
    ✓ No requests/urllib usage
  Validating high_risk shell declarations...
    ✓ All ctx.device.shell calls have high_risk=True (and manifest allows)
  Skill registered successfully as 'video_player_startup@1.0.0'
```

**static scan 不清零 → 注册失败**：

```
$ benchmark-agent register-skill my_skills/bad_skill/
  Running static scan...
    ✗ Line 23: direct use of subprocess.run() detected
    ✗ Line 45: open() with absolute path '/etc/config'
  ERROR: Cannot register skill with 2 static scan warnings.
  Fix the warnings or use `--trust-level local` for local-only use.
```

**与 §5.0 sandbox 表述的关系**：

- §5.0 说 Phase 1B 是 best-effort，**这是 runtime 层面**
- §2.6 Trust Model 是**治理层面**，通过注册门槛强制 registered Skill 规范
- 两层结合：runtime 不强制 + 注册强制 = 内部 100 人场景的实用安全边界

**Phase 1.5 演化**：

- `untrusted_external` 在 Phase 1.5 容器化后开放
- 容器内 + 静态扫描清零 + manifest 声明 → 即使是外部 Skill 也能跑

---

## 3. Implementation（skill.py）规范

### 3.1 基类与接口

```python
# benchmark_skill_sdk（框架提供的 SDK）
from benchmark_skill_sdk import BenchmarkSkill, SkillContext, RunResult

class BenchmarkSkill(ABC):
    """所有用户 Skill 必须继承这个基类。"""
    
    @abstractmethod
    def setup(self, ctx: SkillContext) -> None:
        """单次 run 前的准备工作。
        
        每次 repeat 前调用一次。失败时 teardown 仍会执行。
        允许的操作受 manifest required_permissions 限制。
        """
        ...
    
    @abstractmethod
    def run(self, ctx: SkillContext) -> RunResult:
        """实际测量。
        
        返回的 metrics 必须匹配 manifest metrics schema。
        run 不应该自己做 warmup / repeat，由 SkillRuntime 调度。
        """
        ...
    
    @abstractmethod
    def teardown(self, ctx: SkillContext) -> None:
        """清理。
        
        如果 manifest cleanup_required=true，即使 run/setup 抛异常也会执行。
        """
        ...
    
    # 可选钩子（默认空实现）
    def on_warmup_complete(self, ctx: SkillContext) -> None:
        """warmup 全部完成后调用一次（在 repeats 开始前）。可用于额外校准。"""
        pass
    
    def on_repeats_complete(self, ctx: SkillContext, results: list[RunResult]) -> None:
        """所有 repeats 完成后调用一次。可用于自定义聚合。"""
        pass
```

### 3.2 RunResult 结构

```python
@dataclass
class RunResult:
    metrics: dict[str, float | int | bool]  # 必须匹配 manifest metrics keys
    extras: dict[str, Any] = field(default_factory=dict)  # 选填：额外数据，不参与 regression 判定
    artifacts: list[Path] = field(default_factory=list)   # 选填：本次 repeat 产出的 artifact 路径
```

**约束**：

- `metrics` 的 keys **必须**与 manifest `metrics` 声明完全一致（runtime 校验）
- `extras` 可放调试信息（如 backtrace / 时间戳分段），但不进入 regression 判定
- `artifacts` 中的 Path 必须在 `ctx.workspace.artifact_dir`（runtime 检查）

### 3.3 完整示例：video_player_startup

```python
# my_skills/video_player_startup/skill.py

from benchmark_skill_sdk import BenchmarkSkill, SkillContext, RunResult

class VideoPlayerStartupSkill(BenchmarkSkill):
    """对应 skill.yaml 中声明的 skill_id=video_player_startup"""
    
    def setup(self, ctx: SkillContext) -> None:
        # 强制关闭已运行的 player
        ctx.device.app_terminate("com.samsung.videoplayer")
        
        # 清理 cache
        ctx.device.shell("pkgcmd -c -t app -n com.samsung.videoplayer")
        
        # 推送测试视频到设备
        ctx.device.push(
            local_path=ctx.workspace.path / "test_video.mp4",
            remote_path="/tmp/test_video.mp4"
        )
        
        # 等待系统稳定
        ctx.sleep(2.0)
    
    def run(self, ctx: SkillContext) -> RunResult:
        start_ts = ctx.now_ms()
        
        # 启动 player
        ctx.device.app_launch(
            app_id="com.samsung.videoplayer",
            args={"video": "/tmp/test_video.mp4"}
        )
        
        # 等待 player.started 事件（带超时）
        ctx.device.wait_for_event(
            event_pattern="video_player.started",
            timeout_sec=10
        )
        
        elapsed_ms = ctx.now_ms() - start_ts
        
        # 采集峰值内存
        peak_memory_kb = int(ctx.device.shell(
            "cat /proc/$(pidof video_player)/status | grep VmPeak | awk '{print $2}'"
        ).strip())
        peak_memory_mb = peak_memory_kb / 1024
        
        return RunResult(
            metrics={
                "startup_time_ms": elapsed_ms,
                "peak_memory_mb": peak_memory_mb,
            },
            extras={
                "video_size_bytes": (ctx.workspace.path / "test_video.mp4").stat().st_size,
            }
        )
    
    def teardown(self, ctx: SkillContext) -> None:
        # 即使 run 失败也要清理
        ctx.device.app_terminate("com.samsung.videoplayer")
        ctx.device.shell("rm -f /tmp/test_video.mp4")
```

### 3.4 不允许的写法

```python
# ❌ 禁止：直接调 subprocess
import subprocess
def run(self, ctx):
    subprocess.run(["sdb", "shell", "echo", "hi"])  # SkillViolationError

# ❌ 禁止：直接 open 绝对路径
def setup(self, ctx):
    with open("/etc/hostname") as f:  # SkillViolationError
        data = f.read()

# ❌ 禁止：直接 requests
import requests
def run(self, ctx):
    requests.get("http://example.com")  # network not declared → SkillViolationError

# ❌ 禁止：直接 os.system
import os
def setup(self, ctx):
    os.system("rm -rf /tmp/something")  # SkillViolationError

# ✅ 允许：通过 ctx 受控 API
def run(self, ctx):
    output = ctx.device.shell("echo hi")
    data = ctx.workspace.read("config.yaml")
```

---

## 4. SkillContext 受控 API 完整列表

### 4.1 ctx.device.*（开发板操作）

```python
class DeviceAPI:
    def exec(self, argv: list[str], timeout_sec: int = 30) -> str:
        """在开发板执行命令（推荐方式，v0.2 新增）。
        
        - argv 是命令的参数列表，不走 shell 解析
        - argv[0] 必须在 manifest allowed_commands 中（精确匹配 canonical path）
        - 需要 manifest required_permissions 含 device.shell
        - 自动记录到 trace（risk_level=low）
        - 返回 stdout 字符串
        
        示例:
            ctx.device.exec(["am", "start", "com.samsung.videoplayer"])
            ctx.device.exec(["rm", "-f", "/tmp/test_video.mp4"])
        """
        ...
    
    def shell(self, cmd: str, timeout_sec: int = 30, high_risk: bool = False) -> str:
        """在开发板执行 shell 命令（v0.2 标 high_risk 必填）。
        
        - 仅在 pipeline / redirect / 复杂 shell 表达式时使用
        - high_risk=True 是必填，否则抛 SkillViolationError
        - 自动记录到 trace（risk_level=high）
        - 命令本身的安全性由用户负责（denylist 兜底）
        
        示例:
            ctx.device.shell(
                "cat /proc/$(pidof video_player)/status | grep VmPeak",
                high_risk=True
            )
        """
        ...
    
    def push(self, local_path: Path, remote_path: str) -> None:
        """推文件到开发板。需要 device.push 权限。"""
        ...
    
    def pull(self, remote_path: str, local_path: Path) -> None:
        """从开发板拉文件。需要 device.pull 权限。"""
        ...
    
    def app_launch(self, app_id: str, args: dict = None) -> None:
        """启动 Tizen 应用。需要 device.app_launch 权限。"""
        ...
    
    def app_terminate(self, app_id: str) -> None:
        """终止 Tizen 应用。需要 device.app_terminate 权限。"""
        ...
    
    def wait_for_event(self, event_pattern: str, timeout_sec: int) -> dict:
        """等待 dlog 中匹配 event_pattern 的事件。"""
        ...
    
    def dlog(self, filter_tag: str = None, since_ts: float = None) -> str:
        """读取 dlog（Tizen 系统日志）。"""
        ...
    
    def pkgcmd(self, action: str, *args) -> str:
        """Tizen 包管理（install / uninstall / clear）。"""
        ...
    
    def check_thermal_state(self) -> dict:
        """查询 thermal_state（normal / warm / hot / critical）。"""
        ...
    
    def get_cpu_governor(self) -> str:
        """查询当前 CPU governor。"""
        ...
```

### 4.2 ctx.host.*（x86 host 操作）

```python
class HostAPI:
    def exec(self, argv: list[str], timeout_sec: int = 30, cwd: Path = None) -> str:
        """在 host 执行命令（推荐方式，v0.2 新增）。
        
        - argv 是命令的参数列表，不走 shell 解析
        - 同 device.exec 的安全规则
        - cwd 必须在 ctx.workspace 范围内
        """
        ...
    
    def shell(self, cmd: str, timeout_sec: int = 30, cwd: Path = None, high_risk: bool = False) -> str:
        """在 host 执行 shell 命令（v0.2 high_risk 必填）。"""
        ...
    
    def get_cpu_load(self) -> float:
        """查询 host 1 分钟 load average。"""
        ...
    
    def get_available_memory_mb(self) -> int:
        ...
```

### 4.3 ctx.workspace.*（workspace 文件操作）

```python
class WorkspaceAPI:
    path: Path  # ctx.workspace.path = workspace 根目录（只读 attribute）
    artifact_dir: Path  # ctx.workspace.artifact_dir = artifact 存放目录
    
    def read(self, relative_path: str) -> str:
        """读 workspace 内文件（路径必须是相对路径）。需要 host.read_workspace 权限。"""
        ...
    
    def write(self, relative_path: str, content: str) -> None:
        """写 workspace 内文件。需要 host.write_workspace 权限。"""
        ...
    
    def glob(self, pattern: str) -> list[Path]:
        """workspace 内 glob 匹配。"""
        ...
```

### 4.4 ctx.artifacts.*（产出 artifact）

```python
class ArtifactAPI:
    def save(self, name: str, data: bytes | str, content_type: str = "application/octet-stream") -> None:
        """保存 artifact 到 ctx.workspace.artifact_dir/{name}。
        
        会自动经过 redaction filter（Contract 8.5）。
        """
        ...
    
    def save_json(self, name: str, data: dict) -> None:
        """同上，但自动 json.dumps。"""
        ...
```

### 4.5 ctx.network.*（仅 manifest network=true 时可用）

```python
class NetworkAPI:
    def fetch(self, url: str, timeout_sec: int = 30) -> bytes:
        """HTTP GET。仅在 manifest network=true 时可用。"""
        ...
```

### 4.6 ctx.env.*（环境变量，自动 redact）

```python
class EnvAPI:
    def get(self, name: str, default: str = None) -> str:
        """读环境变量。值会自动经过 redaction（敏感字段返回 [REDACTED]）。
        
        实际不敏感的字段（如 PATH）正常返回。
        """
        ...
```

### 4.7 ctx 顶层属性 / 方法

```python
class SkillContext:
    task_id: str             # 当前 task ID
    skill_id: str            # 当前 Skill ID
    repeat_idx: int          # 当前是第几次 repeat（warmup 阶段为 -1）
    platform: str            # "x86" | "tizen_device"
    
    device: DeviceAPI        # 仅 platform == tizen_device 时可用
    host: HostAPI
    workspace: WorkspaceAPI
    artifacts: ArtifactAPI
    network: NetworkAPI      # 仅 manifest network=true 时可用
    env: EnvAPI
    
    def now_ms(self) -> float:
        """当前时间戳（ms 精度）。"""
        ...
    
    def sleep(self, seconds: float) -> None:
        """睡眠（自动响应 timeout）。"""
        ...
    
    def emit_progress(self, message: str) -> None:
        """报告进度（写 trace event）。"""
        ...
```

---

## 5. Sandbox Guardrails 完整规范（v0.2 重写：承认 Phase 1B 是 best-effort）

### 5.0 Phase 1B 安全边界承诺（v0.2 关键澄清）

**v0.1 表述的问题**：原文档说"调用 ctx 之外的底层 → 进程在 sandbox namespace 中失败"，但 Phase 1B 没有真正的 sandbox namespace，这个承诺**做不到**。

**v0.2 诚实表述**：

> **Phase 1B Skill Runtime 是 best-effort policy enforcement，不是真 sandbox。**
> 
> - **能可靠 enforce 的**：Manifest validate（加载时）/ Output validate（运行后）/ Timeout（SIGKILL）/ ctx API 内部的权限检查 / 命令 allowlist
> - **best-effort（不保证拦截）**：用户直接 `import subprocess; subprocess.run(...)` / 直接 `open("/etc/...")` / 直接 `requests.get(...)` 等绕过 ctx API 的底层调用
> - **不适用于运行不可信 Skill**：本机制假设 100 人内部场景，用户合作而非对抗
> 
> 真正的隔离在 **Phase 1.5 通过容器化实现**（每个 Skill 在独立容器内，bind mount workspace + network namespace + cgroup limit）。

**为什么 Phase 1B 不引入 monkey patch / import hook**：

1. **monkey patch 可被绕过**：`importlib.reload(subprocess)` / `os.popen` / `ctypes` 调底层 syscall / 各种间接路径
2. **真正隔离需要 OS-level mechanism**（namespace / cgroup / seccomp），不是用户态 hook
3. **做不彻底反而给"安全错觉"**：用户以为 Phase 1B 安全了，写出不规范代码，到 Phase 1.5 容器化后再大量返工
4. **Phase 1B 目标是验证 Manifest contract 设计**，不是验证安全边界

**static scan 的作用**（v0.2 重新定位）：

- **不是安全 enforce**，是**代码 review 工具**
- 提前告诉用户"你这里直接用了 subprocess，请改用 ctx.device.exec"
- emit warning event 到 trace，user 可以在 review_packet 看到
- Phase 1.5 容器化后，static scan 仍然保留作为开发体验工具

### 5.1 Guardrails 实施层次（v0.2 修订）

```
Skill 代码
   ↓
[Static Scan]（加载时，best-effort 代码 review 工具）
   ↓ emit warning event，不阻止加载
[Manifest Validate]（加载时，强制 enforce）
   ↓ 缺字段 / 字段非法 → 拒绝加载（hard fail）
[SkillRuntime: ctx API 内部检查]（运行时，强制 enforce）
   ↓ ctx API 调用必经过权限 / allowlist 检查
[底层 API 直接调用]（运行时，best-effort，Phase 1.5 容器化加强）
   ⚠️ Phase 1B 不保证拦截；Phase 1.5 通过容器化 enforce
[Timeout]（运行时，强制 enforce）
   ↓ 超时 → SIGKILL
[Output Validate]（运行后，强制 enforce）
   ↓ metrics 不匹配 manifest → SkillViolationError
```

### 5.2 Static Scan（best-effort）

加载 `skill.py` 前用 AST 扫描，检测以下模式（emit warning，不阻止）：

| 模式 | 检测方式 |
|---|---|
| `subprocess.run / Popen / call` | AST 找 `Call` 节点，func 名是 subprocess 的方法 |
| `os.system` | 同上 |
| `open(<abs_path>)` 调用 | AST 找 `Call(func=open)`，参数是绝对路径常量 |
| `requests.get / post` | AST 找 requests 模块的 `Call` |
| `urllib.request.urlopen` | 同上 |
| `socket.*` | AST 找 socket 模块 `Call` |

**实施约束**（避免误报）：

- 区分 `Import` 和 `Call`：`import subprocess` 不报警，只 `subprocess.run(...)` 报警
- 注释 / docstring 中的代码不报警
- 测试 dir / `if __name__ == "__main__":` 块不报警

**Phase 1B 是 warning，Phase 1.5 升级为 block**（Contract 8.3.1.1）。

### 5.3 Manifest Validate（加载时强制）

由 `SkillManifestValidator` 实施：

| 校验项 | 失败处理 |
|---|---|
| skill_id 重复 | 拒绝注册第二个 |
| skill_id 格式非法 | 拒绝加载 |
| version 非 semver | 拒绝加载 |
| target_platforms 为空 | 拒绝加载 |
| metrics 为空 | 拒绝加载 |
| metric 的 type / unit 非法 | 拒绝加载 |
| destructive side_effect 未声明 | 加载成功，但执行 destructive 操作时 hard fail |
| `cleanup_required: true` 但 Implementation 没实现 `teardown` | 拒绝加载 |

### 5.4 Runtime Permission Enforcement（v0.2 修订：精确匹配 + 推荐 exec API）

#### 5.4.1 推荐用 `ctx.device.exec(argv=[...])` 替代 shell（v0.2 新增）

**Kimi 反馈**：v0.1 设计中 `ctx.device.shell(cmd)` 接收 shell 字符串，安全 / 准确度都不够：

- `cmd.split()[0]` 拿首词不能处理 pipeline（`cat file | grep ...`）
- `startswith` 匹配可被 `/usr/bin/sdb-malicious` 绕过
- `&&` / `;` 等可串接危险命令
- shell 解析规则复杂，难以可靠校验

**v0.2 新增 `ctx.device.exec(argv=[...])` API**（推荐用法）：

```python
# ✅ 推荐：用 exec，argv 是列表
ctx.device.exec(["rm", "-f", "/tmp/test_video.mp4"])
ctx.device.exec(["am", "start", "com.samsung.videoplayer"])
ctx.device.exec(["pidof", "video_player"])

# ⚠️ 仍保留但弱化：shell 字符串
# 仅在 pipeline / redirect / 复杂表达式时使用
ctx.device.shell(
    "cat /proc/$(pidof video_player)/status | grep VmPeak",
    high_risk=True  # v0.2 必填：明确这是 shell 字符串、含 expansion
)
```

**强制规则**（v0.2）：

- `ctx.device.exec(argv=[...])` 是**默认推荐**
- `ctx.device.shell(cmd)` **要求 `high_risk=True` 参数**，否则拒绝调用
- shell 字符串的命令首词通过 `shlex.split(cmd)[0]` 解析，**只用于审计 trace**，不用于安全决策
- 安全决策（allowed_commands 匹配）只在 exec 路径精确做

#### 5.4.2 精确匹配规则（v0.2 修订）

**v0.1 问题**：`startswith` 匹配会被 `/usr/bin/sdb-malicious` 绕过。

**v0.2 规则**：

```python
# DeviceAPI.exec 内部
def exec(self, argv: list[str], ...):
    # 1. 权限检查
    if "device.shell" not in self._manifest.required_permissions:
        raise SkillViolationError(...)
    
    # 2. argv[0] 精确匹配 allowed_commands
    executable = argv[0]
    
    # 解析到 canonical executable path
    try:
        canonical = shutil.which(executable)  # 查 PATH，得到完整路径
        if not canonical:
            raise SkillViolationError(f"Executable not found: {executable}")
        canonical = str(Path(canonical).resolve())  # 解析符号链接
    except Exception as e:
        raise SkillViolationError(f"Cannot resolve executable {executable}: {e}")
    
    # 精确匹配，不允许 startswith
    if self._manifest.allowed_commands:
        if canonical not in self._manifest.allowed_commands_resolved:
            raise SkillViolationError(
                f"Command '{canonical}' not in allowed_commands (must be exact match)"
            )
    
    # 3. denylist 用 regex 匹配整个 argv
    full_cmd_str = shlex.join(argv)
    for denied_pattern in self._manifest.denied_commands:
        if re.match(denied_pattern, full_cmd_str):
            raise SkillViolationError(
                f"Command matches denied pattern '{denied_pattern}'"
            )
    
    # 4. 记录到 trace（argv 直接落，不需要解析）
    self._trace_writer.emit(
        stage="skill_runtime", event_type="skill_invoked",
        name=f"device.exec({argv[0]})",
        result_summary=f"argv={argv}",
    )
    
    # 5. 实际执行（直接传 argv 给 subprocess，不走 shell 解析）
    return self._device_adapter.run_argv(argv, ...)


# DeviceAPI.shell 内部
def shell(self, cmd: str, high_risk: bool = False, ...):
    if not high_risk:
        raise SkillViolationError(
            "ctx.device.shell() requires high_risk=True. Use ctx.device.exec(argv=[...]) instead."
        )
    
    # ★ v0.2.1 新增：trust_level + allow_high_risk_shell 联动校验
    if self._manifest.trust_level == "registered":
        if not self._manifest.allow_high_risk_shell:
            raise SkillViolationError(
                f"Registered Skill '{self._manifest.skill_id}' calls high_risk shell, "
                f"but manifest.allow_high_risk_shell=false. "
                f"Either set allow_high_risk_shell=true in manifest, or refactor to use exec()."
            )
    # trust_level=local 时不做 allow_high_risk_shell 检查（本地开发自由）
    
    # 1. 权限检查（同上）
    
    # 2. 解析 cmd 首词（仅用于 trace 标记，不用于安全决策）
    try:
        cmd_head = shlex.split(cmd)[0] if cmd else ""
    except ValueError:
        cmd_head = "<unparseable>"
    
    # 3. shell 模式不能用 allowed_commands enforce（解析复杂）
    # 但仍可用 denylist regex 兜底
    for denied_pattern in self._manifest.denied_commands:
        if re.search(denied_pattern, cmd):
            raise SkillViolationError(...)
    
    # 4. trace 标记为 high_risk
    self._trace_writer.emit(
        stage="skill_runtime", event_type="skill_invoked",
        name=f"device.shell(high_risk:{cmd_head})",
        result_summary=cmd[:200],
    )
    
    # 5. 执行（走 shell）
    return self._device_adapter.run_command(cmd, ...)
```

**Manifest allowed_commands 解析（v0.2.1 修订：host/device 分离）**：

**ChatGPT + Kimi 都指出**：原版 `shutil.which()` 是在 **host 侧**解析 PATH，但 `ctx.device.exec()` 是在 **device 侧**执行。如果 host 和 device 的 PATH 或文件系统布局不同，canonical path 匹配会失败或匹配错误路径。

**v0.2.1 修订：host / device 两套独立解析**：

```python
class SkillManifestValidator:
    def _resolve_allowed_commands(self, manifest, host_adapter, device_adapter=None):
        """v0.2.1: 分别在 host 侧和 device 侧解析 canonical paths。
        
        allowed_commands 是 Manifest 中的字符串列表（用户写法）。
        解析结果分两个字段:
          allowed_commands_resolved_host: list[str]    # host 侧 canonical paths
          allowed_commands_resolved_device: list[str]  # device 侧 canonical paths
        ctx.host.exec / ctx.device.exec 各用对应字段做匹配。
        """
        # ---- host 侧解析（沿用 v0.2 逻辑）----
        manifest.allowed_commands_resolved_host = []
        for cmd in manifest.allowed_commands:
            try:
                path = shutil.which(cmd) if not cmd.startswith("/") else cmd
                if not path or not Path(path).exists():
                    emit_warning(f"Manifest allowed_command '{cmd}' not found on host PATH")
                    continue
                manifest.allowed_commands_resolved_host.append(str(Path(path).resolve()))
            except Exception as e:
                emit_warning(f"Failed to resolve '{cmd}' on host: {e}")
        
        # ---- device 侧解析（v0.2.1 新增）----
        if device_adapter is not None:
            manifest.allowed_commands_resolved_device = []
            for cmd in manifest.allowed_commands:
                try:
                    # 用 device shell 的 'command -v' 解析（POSIX 标准，比 which 可移植）
                    # 注意：这里 device_adapter.run_command 是 SkillRuntime 内部 API，
                    # 不走 ctx.device.shell 的 high_risk 校验（这是 manifest 加载阶段）
                    result = device_adapter.run_command(
                        f"command -v {shlex.quote(cmd)}",
                        timeout_sec=5
                    )
                    path = result.stdout.strip()
                    if not path:
                        emit_warning(f"Manifest allowed_command '{cmd}' not found on device PATH")
                        continue
                    # 注意：不在 device 侧 resolve symlinks（device shell 可能没有 realpath/readlink -f）
                    # 直接用 'command -v' 的输出作为 canonical reference
                    manifest.allowed_commands_resolved_device.append(path)
                except Exception as e:
                    emit_warning(f"Failed to resolve '{cmd}' on device: {e}")


# DeviceAPI.exec 内部使用 device 侧 resolved
def exec(self, argv: list[str], ...):
    executable = argv[0]
    
    # v0.2.1: 用 device 侧 resolve 后的 canonical path 做精确匹配
    # 如果 argv[0] 不是绝对路径，先在 device 上 resolve
    if not executable.startswith("/"):
        resolved = self._device_adapter.resolve_executable(executable)
        if not resolved:
            raise SkillViolationError(f"Executable '{executable}' not found on device")
        executable_canonical = resolved
    else:
        executable_canonical = executable
    
    if self._manifest.allowed_commands:
        if executable_canonical not in self._manifest.allowed_commands_resolved_device:
            raise SkillViolationError(
                f"Command '{executable_canonical}' not in allowed_commands_resolved_device. "
                f"Allowed: {self._manifest.allowed_commands_resolved_device}"
            )
    # ... 其余流程同 v0.2
```

**v0.2.1 关键变化**：

| 项 | v0.2 | v0.2.1 |
|---|---|---|
| host 侧解析 | shutil.which() | shutil.which()（不变）|
| device 侧解析 | 没有，错误用 host shutil.which | **DeviceAdapter `command -v`** |
| `allowed_commands_resolved` | 单一字段 | 拆为 `_host` + `_device` 两个字段 |
| ctx.host.exec 匹配 | resolved | resolved_host |
| ctx.device.exec 匹配 | resolved | resolved_device |
| symlink 解析 | host 上 `Path.resolve()` | host 上 resolve；device 上不 resolve（用 `command -v` 输出）|

**性能说明**：device 侧 `command -v` 调用在 Skill 加载阶段一次性完成（不在每次 exec 调用），对运行时性能无影响。

**Spike Gate 验证项**（v0.2.1 加入 Phase 1B Spike）：

- [ ] device-side allowed_commands 解析在选定 Tizen 开发板上正常工作
- [ ] host PATH 与 device PATH 不同的命令（如 `am` / `pkgcmd`）能被正确解析

#### 5.4.3 trace 中所有命令都标 risk 等级（v0.2 新增）

每条 ctx API 调用 trace event 含字段：

```json
{
  "event_type": "skill_invoked",
  "name": "device.exec(am)",
  "risk_level": "low | medium | high",
  "argv": ["am", "start", "com.samsung.videoplayer"],
  ...
}
```

- `low`：用 exec + 命令在 allowed_commands 中
- `medium`：用 exec 但 allowed_commands 为空（无白名单）
- `high`：用 shell + high_risk=True

### 5.5 Timeout & Resource Enforcement

- `timeout_sec`：整个 Skill 执行（warmup + 所有 repeats + teardown）超时
- 由 SkillRuntime 在子进程级别 enforce：`signal.alarm` + 兜底 `os.kill(pid, SIGKILL)`
- 内存：当前 Phase 1B 不强制；Phase 1.5 容器化后可加 cgroup limit

### 5.6 Workspace Isolation

`ctx.workspace.read(relative_path)` 内部：

```python
def read(self, relative_path: str) -> str:
    # 拒绝绝对路径
    if Path(relative_path).is_absolute():
        raise SkillViolationError(f"Absolute path not allowed: {relative_path}")
    
    # 拒绝路径越界（含 ..）
    full_path = (self._workspace_root / relative_path).resolve()
    if not str(full_path).startswith(str(self._workspace_root)):
        raise SkillViolationError(f"Path traversal not allowed: {relative_path}")
    
    return full_path.read_text()
```

### 5.7 Network Gating

```python
class NetworkAPI:
    def __init__(self, manifest):
        self._allowed = manifest.network == True
    
    def fetch(self, url):
        if not self._allowed:
            raise SkillViolationError(
                "Skill manifest network=false, ctx.network.fetch() not allowed"
            )
        # 实际执行（Phase 1.5 容器化后会用 network namespace block 底层 socket）
        ...
```

### 5.8 Output Validation

`run()` 返回后，SkillRuntime 校验 `RunResult.metrics`：

```python
def _validate_run_result(self, result: RunResult, manifest: SkillManifest):
    declared_keys = set(manifest.metrics.keys())
    actual_keys = set(result.metrics.keys())
    
    # 1. 不能有未声明的 metric
    extra = actual_keys - declared_keys
    if extra:
        raise SkillViolationError(
            f"Skill returned undeclared metrics: {extra}"
        )
    
    # 2. 不能少声明的 metric
    missing = declared_keys - actual_keys
    if missing:
        raise SkillViolationError(
            f"Skill missing declared metrics: {missing}"
        )
    
    # 3. 类型检查
    for k, v in result.metrics.items():
        expected_type = manifest.metrics[k].type
        if not isinstance(v, _TYPE_MAP[expected_type]):
            raise SkillViolationError(
                f"Metric {k} has wrong type: expected {expected_type}, got {type(v)}"
            )
```

### 5.9 Artifact 机制统一（v0.2 新增，Kimi 反馈）

**问题**：v0.1 中有两套 artifact：

- **Manifest declared**：`manifest.artifacts[].pull_from` 让 runtime 自动从 device pull
- **RunResult.artifacts**：Skill 主动产出的 artifact 路径列表

如果两套同时存在，命名冲突和重复就会发生。

**v0.2 统一规则**：

| 来源 | 谁负责 | 命名空间 |
|---|---|---|
| Manifest `artifacts[]` | SkillRuntime 自动 pull/copy | `artifacts/{task_id}/skills/{skill_id}/repeat_{N}/{manifest_artifact_name}` |
| `RunResult.artifacts` | Skill 主动 save | `artifacts/{task_id}/skills/{skill_id}/repeat_{N}/{filename}` |
| `ctx.artifacts.save(name, ...)` | Skill 显式调 API | `artifacts/{task_id}/skills/{skill_id}/repeat_{N}/{name}` |

**所有 artifact 必须在 `ctx.workspace.artifact_dir` namespace 下**，路径形如：

```
artifacts/{task_id}/skills/{skill_id}/repeat_{N}/
├── logcat.log              ← manifest declared (auto-pulled)
├── perf_report.data        ← manifest declared (auto-pulled)
├── my_extra_dump.txt       ← Skill 主动 save 的
└── ...
```

**冲突解决**（v0.2.1 修订：明确三方关系，Kimi 反馈）：

Kimi 指出 v0.2 文档"manifest declared 和 RunResult 同名 → RunResult 优先"有歧义，因为 `ctx.artifacts.save()` 和 `RunResult.artifacts` 本质上是同一来源（都是 Skill 代码主动产出）。

**v0.2.1 明确三类来源的冲突规则**：

| 来源对 | 冲突处理 |
|---|---|
| **Manifest declared `artifacts[]`** vs **RunResult.artifacts / ctx.artifacts.save()** | Skill 代码（主动产出）**优先**，emit warning 到 trace |
| **RunResult.artifacts** vs **ctx.artifacts.save() 同名** | **抛 `SkillViolationError`**（视为 Skill 代码 bug，不允许）|
| 多个 repeat 间 | 不冲突（path 中含 `repeat_{N}`）|

**理由**：RunResult.artifacts 和 ctx.artifacts.save 都是 Skill 代码控制，同名说明 Skill 内部逻辑混乱，应该是 bug。Manifest declared vs Skill 代码冲突时，Skill 代码可能基于运行时信息生成更精确的 artifact，优先级更高。

**Artifact 命名安全规则**（v0.2.1 新增，ChatGPT 反馈）：

```python
# SkillRuntime 在所有 artifact name 注册前检查
ARTIFACT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

def _validate_artifact_name(name: str):
    if not name:
        raise SkillViolationError("Artifact name must not be empty")
    if len(name) > 200:
        raise SkillViolationError(f"Artifact name too long: {len(name)} > 200")
    if not ARTIFACT_NAME_PATTERN.match(name):
        raise SkillViolationError(
            f"Artifact name '{name}' contains invalid characters. "
            f"Allowed: [a-zA-Z0-9._-]+"
        )
    if ".." in name or name.startswith("."):
        raise SkillViolationError(
            f"Artifact name '{name}' is suspicious (path traversal / hidden file)"
        )
    if name.startswith("/") or "/" in name or "\\\\" in name:
        raise SkillViolationError(
            f"Artifact name must not contain path separators"
        )
```

**应用范围**：

- Manifest `artifacts[].name`：加载时校验
- `RunResult.artifacts` 中每个 Path 的 basename：返回时校验
- `ctx.artifacts.save(name, ...)`：调用时校验

任何不合规的 name 抛 `SkillViolationError`，且不影响其他 Skill。

**实施约束**：

- SkillRuntime 在 `execute()` 末尾收集所有 artifact，统一记录到 `SkillExecutionResult.artifacts`
- ArtifactManager 对所有 artifact 自动 redaction（Contract 8.5）
- artifact_dir 的 namespace 由 SkillRuntime 创建，Skill 不能跳出

### 5.10 device_state_dirty 状态（v0.2 新增，Kimi 反馈）

**问题**：v0.1 说"Skill violation 不影响其他 Skill"。但在 device benchmark 场景，一个 Skill 失败可能让 device 处于 dirty 状态（app 没 kill 干净 / cache 没清 / 系统设置改了 / 占用了 CPU/GPU）。

**v0.2 引入 device_state_dirty 状态**：

```python
@dataclass
class SkillExecutionResult:
    skill_id: str
    skill_version: str
    samples: list[RunResult]
    warmup_samples: list[RunResult]
    artifacts: list[Path]
    failure: SkillFailure | None
    duration_sec: float
    
    # ★ v0.2 新增字段
    device_state_dirty: bool = False    # True 表示后续 Skill 必须重 check_env
    dirty_reason: str | None = None     # 例如 "cleanup_failed" / "destructive_side_effect"
```

**触发 `device_state_dirty = True` 的情况**：

| 情况 | 标记原因 |
|---|---|
| `teardown()` 抛异常 | `cleanup_failed` |
| `cleanup_required: true` 但 teardown 未执行（被 SIGKILL）| `cleanup_skipped` |
| Manifest 声明 destructive side_effect（reboot/format/flash）| `destructive_side_effect` |
| Skill 执行超时 + 没机会 teardown | `timeout_no_cleanup` |
| `SkillRuntime` 检测到 ctx API 修改了系统设置（governor / thermal_policy 等，Phase 1.5）| `system_state_changed` |

**Benchmark Controller 的处理**（B8.2 集成约束）：

```python
# Benchmark Controller 处理 multi-Skill task 时
for skill in skills:
    result = skill_runtime.execute(skill, ...)
    
    if result.device_state_dirty:
        self.trace_writer.emit(
            stage="skill_runtime", event_type="warning",
            name="device_state_dirty",
            result_summary=f"reason={result.dirty_reason}",
        )
        
        # 后续 Skill 必须重新 check_benchmark_env
        env_result = self.tool_invoker.invoke("check_benchmark_env", {...})
        if not env_result.healthy:
            # 整个 task 失败（避免错误的 benchmark 数据）
            return self._build_failed_result(
                task,
                failure_class="device_state_dirty",
                stage="skill_runtime",
                message=f"Device state dirty after {result.skill_id}: {result.dirty_reason}"
            )
```

**v0.2 修订原文**：

> ~~"Skill violation 不影响其他 Skill"~~（v0.1）
> 
> "**默认不影响其他 Skill**。但如果 Skill 触发 `device_state_dirty=True`（cleanup_failed / destructive / timeout 等），**后续 Skill 必须暂停或重新 check_benchmark_env**。如果 check_env 不通过，整个 task 失败。" （v0.2）

---

## 6. 示例 Skill 集（Phase 1B 必交 3-5 个）

### 6.1 示例 1：python_loop_smoke_test（v0.2 改名，x86 上的 framework smoke test）

**v0.2 修订**：Kimi 指出原 `cpu_microbench` 其实测的是 Python interpreter overhead，不是真正的 CPU 性能。改名为 `python_loop_smoke_test`，定位是"框架冒烟测试"，不是性能 benchmark。

```yaml
# my_skills/python_loop_smoke_test/skill.yaml
skill_id: python_loop_smoke_test
version: 1.0.0
description: "框架冒烟测试：跑一个简单 Python 循环验证 Skill 框架本身可用"

target_platforms:
  - x86

required_permissions: []          # 完全不需要任何权限

timeout_sec: 60

metrics:
  loop_duration_ms:
    type: number
    unit: ms
    lower_is_better: true
    threshold_regression_percent: 30.0    # 宽松，因为是 smoke test
    aggregation: median
    max_cv_percent: 10.0                  # 宽松（Python interpreter 有自然波动）
    outlier_policy: iqr
    min_samples: 3

cleanup_required: false
network: false
```

```python
# my_skills/python_loop_smoke_test/skill.py
import math
from benchmark_skill_sdk import BenchmarkSkill, RunResult

class PythonLoopSmokeTest(BenchmarkSkill):
    """Smoke test: verify Skill framework can execute a Skill end-to-end.
    
    This is NOT a real CPU benchmark. The result reflects Python interpreter overhead,
    not system CPU performance.
    """
    
    def setup(self, ctx): pass
    
    def run(self, ctx):
        start = ctx.now_ms()
        # 简单的 Python 循环（注：测的是 Python interpreter，不是 CPU）
        for _ in range(1_000_000):
            math.atan(1.0) * 4.0
        elapsed = ctx.now_ms() - start
        return RunResult(metrics={"loop_duration_ms": elapsed})
    
    def teardown(self, ctx): pass
```

### 6.2 示例 2：memory_alloc_perf（v0.2 参数化，兼容平台）

**v0.2 修订**：Kimi 指出原默认值 `100MB * 10 = 1GB` 在开发板上太重。v0.2 用 `ctx.env.get()` 读环境变量做参数化，**默认值降到 32MB * 5 = 160MB**。

```yaml
skill_id: memory_alloc_perf
version: 1.0.0
description: "测量大块内存分配 / 释放的吞吐率（参数化）"

target_platforms:
  - x86
  - tizen_device

required_permissions:
  - host.shell        # x86 上可能用
  - device.shell      # device 上可能用

timeout_sec: 120

metrics:
  alloc_throughput_mb_per_sec:
    type: number
    unit: mb
    lower_is_better: false
    threshold_regression_percent: 5.0
    aggregation: median
    max_cv_percent: 8.0
  free_throughput_mb_per_sec:
    type: number
    unit: mb
    lower_is_better: false
    threshold_regression_percent: 5.0
    aggregation: median
    max_cv_percent: 8.0

cleanup_required: false
```

```python
import ctypes
from benchmark_skill_sdk import BenchmarkSkill, RunResult

class MemoryAllocPerfSkill(BenchmarkSkill):
    """v0.2: 参数化版本，默认值适合开发板。
    
    Environment variables:
        BENCH_ALLOC_SIZE_MB (default: 32): 单块分配大小
        BENCH_ALLOC_ITER   (default: 5): 分配次数
    """
    
    def setup(self, ctx):
        # v0.2 演示：用 ctx.env.get() 读环境变量做参数化
        # 默认值适合开发板（160MB 总），x86 上可通过 env 覆盖到更大
        self._size_mb = int(ctx.env.get("BENCH_ALLOC_SIZE_MB", "32"))
        self._iterations = int(ctx.env.get("BENCH_ALLOC_ITER", "5"))
        ctx.emit_progress(f"alloc test: {self._size_mb}MB * {self._iterations}")
    
    def run(self, ctx):
        size_bytes = self._size_mb * 1024 * 1024
        
        start = ctx.now_ms()
        buffers = []
        for _ in range(self._iterations):
            buffers.append((ctypes.c_byte * size_bytes)())
        alloc_ms = ctx.now_ms() - start
        
        start = ctx.now_ms()
        buffers.clear()
        free_ms = ctx.now_ms() - start
        
        total_mb = self._size_mb * self._iterations
        return RunResult(metrics={
            "alloc_throughput_mb_per_sec": total_mb / (alloc_ms / 1000),
            "free_throughput_mb_per_sec": total_mb / (free_ms / 1000),
        })
    
    def teardown(self, ctx): pass
```

### 6.3 示例 3：video_player_startup（v0.2 改用 ctx.device.exec，Tizen device）

**v0.2 修订**：原 §3.3 中用 `ctx.device.shell("cat /proc/$(pidof video_player)/status | grep VmPeak | awk ...")`，这是 pipeline + command substitution + 多命令，依赖 `cat / pidof / grep / awk` 全在 allowed_commands。v0.2 改用 `ctx.device.exec` + 解析逻辑放 Python 端。

```yaml
skill_id: video_player_startup
version: 1.0.0
description: "测量 Tizen 视频播放器冷启动时间"

target_platforms:
  - tizen_device

required_permissions:
  - device.shell           # 含 exec
  - device.push
  - device.app_launch
  - device.app_terminate

allowed_commands:
  # v0.2 用精确 canonical path
  - /usr/bin/am             # Tizen Activity Manager
  - /usr/bin/pidof
  - /usr/bin/cat            # 仅用于读 /proc/<pid>/status

timeout_sec: 300

side_effects:
  - launch_app
  - terminate_app
  - clear_cache

metrics:
  startup_time_ms:
    type: number
    unit: ms
    lower_is_better: true
    threshold_regression_percent: 5.0
    aggregation: median
    max_cv_percent: 5.0
  peak_memory_mb:
    type: number
    unit: mb
    lower_is_better: true
    threshold_regression_percent: 3.0
    aggregation: median
    max_cv_percent: 2.0

cleanup_required: true
```

```python
from benchmark_skill_sdk import BenchmarkSkill, RunResult

class VideoPlayerStartupSkill(BenchmarkSkill):
    """v0.2: 用 ctx.device.exec(argv) 替代 shell pipeline."""
    
    APP_ID = "com.samsung.videoplayer"
    
    def setup(self, ctx):
        # v0.2: 用 exec API（受控）
        ctx.device.app_terminate(self.APP_ID)
        ctx.device.exec(["pkgcmd", "-c", "-t", "app", "-n", self.APP_ID])
        
        ctx.device.push(
            local_path=ctx.workspace.path / "test_video.mp4",
            remote_path="/tmp/test_video.mp4"
        )
        ctx.sleep(2.0)
    
    def run(self, ctx):
        start_ts = ctx.now_ms()
        ctx.device.app_launch(
            app_id=self.APP_ID,
            args={"video": "/tmp/test_video.mp4"}
        )
        ctx.device.wait_for_event(
            event_pattern="video_player.started",
            timeout_sec=10
        )
        elapsed_ms = ctx.now_ms() - start_ts
        
        # v0.2: 用 exec 替代 shell pipeline
        # 第一步：pidof
        pid_output = ctx.device.exec(["pidof", "video_player"]).strip()
        if not pid_output:
            raise RuntimeError("video_player not running")
        pid = pid_output.split()[0]
        
        # 第二步：cat /proc/<pid>/status，解析在 Python 端
        status_output = ctx.device.exec(["cat", f"/proc/{pid}/status"])
        peak_memory_kb = self._parse_vmpeak(status_output)
        peak_memory_mb = peak_memory_kb / 1024
        
        return RunResult(
            metrics={
                "startup_time_ms": elapsed_ms,
                "peak_memory_mb": peak_memory_mb,
            },
            extras={
                "video_size_bytes": (ctx.workspace.path / "test_video.mp4").stat().st_size,
                "pid": pid,
            }
        )
    
    def teardown(self, ctx):
        ctx.device.app_terminate(self.APP_ID)
        # v0.2: 用 exec 替代 shell
        ctx.device.exec(["rm", "-f", "/tmp/test_video.mp4"])
    
    @staticmethod
    def _parse_vmpeak(status_output: str) -> int:
        """从 /proc/<pid>/status 输出解析 VmPeak 行（KB）."""
        for line in status_output.splitlines():
            if line.startswith("VmPeak:"):
                # 'VmPeak:    123456 kB'
                return int(line.split()[1])
        raise RuntimeError("VmPeak not found in /proc/.../status")
```

**v0.2 改动点**：

- 用 `ctx.device.exec([...])` 替代所有 `ctx.device.shell("...")` 字符串
- 解析 `/proc/<pid>/status` 的逻辑从 shell pipeline（cat | grep | awk）移到 Python 端
- allowed_commands 用 canonical path（`/usr/bin/am` 而不是 `am`）

### 6.4 示例 4：workspace_file_io_smoke（v0.2.1 改名，去掉 root 依赖）

**v0.2.1 改名说明**（ChatGPT 反馈）：原 `file_io_throughput` / v0.2 `workspace_file_io` 测的是"warm cache I/O"（不 drop cache），不是真正的存储吞吐 benchmark。改名加 `_smoke` 后缀强调这是冒烟测试，不是性能 benchmark，避免被误用做存储性能评估。

**v0.2 修订**：
- ChatGPT + Kimi 都指出：原版用 `sync && echo 3 > /proc/sys/vm/drop_caches` 需要 root，全局影响系统状态
- 原版用 `/tmp` 全局路径而不是 workspace
- v0.2 改为只在 workspace 内读写，不 drop_caches，不影响全局系统状态
- 演示 `ctx.workspace.write()` 受控 API 用法
- 改名为 `workspace_file_io`，定位是"workspace 内文件读写吞吐"，不是"系统 file I/O"

```yaml
skill_id: workspace_file_io_smoke
version: 1.0.0
description: "测量 workspace 内大文件顺序写 / 读吞吐（不影响全局系统状态）"

target_platforms:
  - x86
  - tizen_device

required_permissions:
  - host.shell                  # 仅用于 dd（限定在 workspace 内）
  - host.read_workspace
  - host.write_workspace

allowed_commands:
  - /bin/dd                     # 仅用于生成测试数据（限定在 workspace 内）

timeout_sec: 180

metrics:
  write_mb_per_sec:
    type: number
    unit: mb
    lower_is_better: false
    threshold_regression_percent: 5.0
    aggregation: median
    max_cv_percent: 10.0           # I/O 波动比较大
  read_mb_per_sec:
    type: number
    unit: mb
    lower_is_better: false
    threshold_regression_percent: 5.0
    aggregation: median
    max_cv_percent: 10.0

cleanup_required: true
```

```python
import shutil
from benchmark_skill_sdk import BenchmarkSkill, RunResult

class WorkspaceFileIoSmokeSkill(BenchmarkSkill):
    """v0.2: 限定在 workspace 内，不需要 root，不影响全局系统状态.
    
    注：因为不 drop OS cache，重复读取会越来越快（hit page cache）。
    所以本 Skill 的 read 测的是"warm cache read"，不是 cold disk read。
    Phase 1.5 容器化后可在容器内 drop cache，避免对 host 全局影响。
    """
    
    FILE_SIZE_MB = 100   # v0.2 降低规模（兼顾 Tizen device）
    
    def setup(self, ctx):
        # v0.2: 用 ctx.host.exec + workspace 路径，不写 /tmp
        input_path = ctx.workspace.path / "bench_input.bin"
        # dd 限定 of= 在 workspace 内，count 限定大小
        ctx.host.exec([
            "dd",
            "if=/dev/urandom",
            f"of={input_path}",
            "bs=1M",
            f"count={self.FILE_SIZE_MB}",
        ], timeout_sec=120)
    
    def run(self, ctx):
        input_path = ctx.workspace.path / "bench_input.bin"
        output_path = ctx.workspace.path / "bench_output.bin"
        
        # 写：用 Python shutil（简单可移植），测的是 user-space 拷贝吞吐
        start = ctx.now_ms()
        shutil.copy(str(input_path), str(output_path))
        write_ms = ctx.now_ms() - start
        
        # 读：用 Python，逐 chunk 读，避免 1 次读 100MB 占内存
        start = ctx.now_ms()
        chunk = 4 * 1024 * 1024  # 4MB chunk
        with open(output_path, "rb") as f:
            while f.read(chunk):
                pass
        read_ms = ctx.now_ms() - start
        
        return RunResult(metrics={
            "write_mb_per_sec": self.FILE_SIZE_MB / (write_ms / 1000),
            "read_mb_per_sec": self.FILE_SIZE_MB / (read_ms / 1000),
        })
    
    def teardown(self, ctx):
        # v0.2: 不用 shell rm，让 SkillRuntime 在 task 结束时自动清理 workspace
        # （或用 ctx.workspace 内文件操作，但当前 API 还没暴露 delete）
        # 实际清理: workspace 在 task 结束时被 SkillRuntime 整体清理
        pass
```

**v0.2 改动点汇总**：

| 项 | v0.1 | v0.2 |
|---|---|---|
| 文件位置 | `/tmp/bench_input.bin` | `ctx.workspace.path / "bench_input.bin"` |
| 文件大小 | 500MB | 100MB（兼顾 Tizen device）|
| cache drop | `echo 3 > /proc/sys/vm/drop_caches` | 不做（接受 warm cache 测量）|
| 读方法 | shell `cat > /dev/null` | Python 4MB chunk 循环读 |
| 测试语义 | "cold disk read" | "warm cache read"（明确说明）|
| root 依赖 | 是 | 否 |

### 6.5 示例 5：browser_load_time（Tizen device，复杂）

```yaml
skill_id: browser_load_time
version: 1.0.0
description: "测量 Tizen 内置浏览器加载本地页面的耗时（DOMContentLoaded）"
target_platforms:
  - tizen_device
required_permissions:
  - device.shell
  - device.push
  - device.app_launch
  - device.app_terminate
timeout_sec: 300
side_effects:
  - launch_app
  - terminate_app
metrics:
  dom_content_loaded_ms:
    type: number
    unit: ms
    lower_is_better: true
    threshold_regression_percent: 5.0
  fully_loaded_ms:
    type: number
    unit: ms
    lower_is_better: true
    threshold_regression_percent: 5.0
cleanup_required: true
artifacts:
  - name: dlog
    type: log
    pull_from: "/tmp/browser_dlog_{repeat_idx}.log"
    on: "always"
```

```python
class BrowserLoadTimeSkill(BenchmarkSkill):
    """v0.2: 用 ctx.device.exec + ctx.env.get 演示"""
    
    APP_ID = "com.samsung.browser"
    
    def setup(self, ctx):
        # v0.2: 演示 ctx.env.get 用法，URL 可通过环境变量覆盖
        self._url = ctx.env.get(
            "BENCH_BROWSER_URL",
            "file:///tmp/test_page.html"
        )
        
        ctx.device.app_terminate(self.APP_ID)
        ctx.device.push(
            local_path=ctx.workspace.path / "test_page.html",
            remote_path="/tmp/test_page.html"
        )
    
    def run(self, ctx):
        # v0.2: 用 exec 替代 shell
        ctx.device.exec(["dlogutil", "-c"])  # 清 dlog
        
        start = ctx.now_ms()
        ctx.device.app_launch(
            self.APP_ID,
            args={"url": self._url}
        )
        
        ctx.device.wait_for_event("DOMContentLoaded", timeout_sec=30)
        dom_ms = ctx.now_ms() - start
        
        ctx.device.wait_for_event("page.fully_loaded", timeout_sec=30)
        load_ms = ctx.now_ms() - start
        
        # 保存 dlog 作为 artifact（用 manifest declared，runtime 自动 pull）
        # 或手动 pull（v0.2: 二选一，见 §5.9 artifact 机制）
        ctx.device.pull(
            remote_path="/var/log/dlog/main.log",
            local_path=ctx.workspace.artifact_dir / f"browser_dlog_{ctx.repeat_idx}.log"
        )
        
        return RunResult(metrics={
            "dom_content_loaded_ms": dom_ms,
            "fully_loaded_ms": load_ms,
        })
    
    def teardown(self, ctx):
        ctx.device.app_terminate(self.APP_ID)
        # v0.2: 用 exec 替代 shell
        ctx.device.exec(["rm", "-f", "/tmp/test_page.html"])
```

---

## 7. Skill 编写指南（给最终用户的）

### 7.1 5 分钟快速开始

1. 在你 repo 任意位置创建 `my_skills/<skill_id>/` 目录
2. 写 `skill.yaml`（至少 skill_id / version / description / target_platforms / required_permissions / timeout_sec / metrics / cleanup_required）
3. 写 `skill.py`（继承 `BenchmarkSkill`，实现 setup / run / teardown）
4. 命令行运行验证：
   ```bash
   benchmark-agent lint-skill my_skills/<skill_id>/
   ```
5. 提交 benchmark task：
   ```bash
   benchmark-agent run --skill <skill_id>@1.0.0 --baseline <BMK-id>
   ```

### 7.2 Manifest 字段速查表

| 何时用 | 字段 |
|---|---|
| 任何 Skill | skill_id / version / description / target_platforms / required_permissions / timeout_sec / metrics / cleanup_required |
| Skill 跑得慢 | 增大 timeout_sec |
| 噪声大 | 增大 repeats、warmup_repeats |
| Skill 改 device | side_effects + （reboot/format 等）destructive 必须列出 |
| Skill 用工具 | allowed_commands |
| Skill 要联网 | network: true + required_permissions 加 network |

### 7.3 Context API 速查表（v0.2 更新）

| 想做 | 推荐用法（v0.2） | 不推荐 |
|---|---|---|
| 在设备上执行命令 | `ctx.device.exec(argv=[...])` | ~~`ctx.device.shell(cmd)`~~（仅 pipeline 时用，需 high_risk=True） |
| 启动 Tizen 应用 | `ctx.device.app_launch(app_id)` | - |
| 推/拉文件 | `ctx.device.push() / pull()` | - |
| 等 dlog 事件 | `ctx.device.wait_for_event(pattern)` | - |
| 在 host 执行命令 | `ctx.host.exec(argv=[...])` | ~~`ctx.host.shell(cmd)`~~（仅 pipeline 时用） |
| 读 workspace 文件 | `ctx.workspace.read("relative/path")` | 直接 `open()` 绝对路径 |
| 写 workspace 文件 | `ctx.workspace.write("relative/path", content)` | 直接 `open()` 写 |
| 保存 artifact | `ctx.artifacts.save(name, data)` 或 manifest `artifacts[]` 声明 | - |
| 读环境变量 / 参数化 | `ctx.env.get("KEY", default)` | 直接 `os.environ[]` |
| 计时 | `ctx.now_ms()` | `time.time() * 1000` |
| 睡眠 | `ctx.sleep(seconds)` | `time.sleep()` |
| HTTP 请求（仅 manifest `network: true`）| `ctx.network.fetch(url)` | 直接 `requests.get()` |

### 7.4 常见陷阱（v0.2 修订）

1. **忘了 `cleanup_required: true`**：teardown 不执行，下次 repeat 状态污染
2. **metrics 输出和 manifest 声明不一致**：runtime 拒绝结果
3. **直接 import subprocess**（v0.2.1 强化"未来兼容性投资"动机，Kimi 反馈）：
   - Phase 1B 是 best-effort，static scan emit warning，但**调用本身不一定失败**
   - **但请仍然用 `ctx.device.exec`，理由**：
     - **兼容性投资**：Phase 1.5 容器化后，subprocess 等绕过 ctx API 的代码会 **hard fail**，到时候批量返工成本高
     - **团队治理**：如果你的 Skill 想加入 team registry（trust_level=registered），static scan warning **必须清零**（见 §2.6），即 Phase 1B 也注册不了
     - **审计可见性**：通过 ctx API 的调用都进 trace，便于复现和 debug；直接 subprocess 看不到
   - **建议**：哪怕 Phase 1B 是 best-effort，也把 ctx API 当作硬约束使用——这是 Phase 1.5 兼容性的投资
4. **`open("/etc/...")` 读绝对路径**：v0.2 同上——best-effort，不保证拦截，但应使用 `ctx.workspace.read` 替代
5. **忘了在 `required_permissions` 中声明权限**：调用对应 ctx API 时报错
6. **`run()` 内部自己做 warmup/repeat**：会和 SkillRuntime 调度冲突，应该删除
7. **v0.2 新增**：`ctx.device.shell(cmd)` **必须传 `high_risk=True`**，否则抛 SkillViolationError；推荐用 `ctx.device.exec(argv=[...])` 替代
8. **v0.2 新增**：`allowed_commands` 用**精确 canonical path**（`/usr/bin/am`），不再支持 startswith 模糊匹配
9. **v0.2 新增**：destructive side_effect（reboot/format/flash）必须在 manifest 显式声明，否则 hard fail
10. **v0.2 新增**：teardown 失败或被 SIGKILL 会触发 `device_state_dirty=True`，后续 Skill 会被 check_env 拦截

### 7.5 调试技巧

- `benchmark-agent lint-skill <dir>`：本地校验 Manifest + 静态扫描
- `benchmark-agent dry-run --skill <id>`：跑 1 次 repeat 看输出
- `ctx.emit_progress("checkpoint A")`：在关键位置打 trace 标记
- 看 `trace.json` 的 `skill_invoked` events 找问题

---

## 8. SkillRuntime 集成接口（给 Benchmark Agent 用）

### 8.1 顶层 API

```python
class SkillRuntime:
    def __init__(self, config: SkillRuntimeConfig):
        ...
    
    def load_skill(self, skill_dir: Path) -> LoadedSkill:
        """加载 Skill：解析 manifest + static scan + 校验 Implementation。
        
        Returns LoadedSkill 实例。失败抛 SkillLoadError。
        """
        ...
    
    def execute(
        self,
        skill: LoadedSkill,
        ctx_factory: Callable[[int], SkillContext],
        warmup_repeats: int,
        repeats: int,
    ) -> SkillExecutionResult:
        """完整执行 Skill：warmup → repeats → teardown。
        
        Manifest 中的 warmup_repeats/repeats 优先；如未声明，使用入参。
        
        Returns SkillExecutionResult，含每次 repeat 的 RunResult 列表 + 失败信息。
        """
        ...
```

### 8.2 SkillExecutionResult

```python
@dataclass
class SkillExecutionResult:
    skill_id: str
    skill_version: str
    samples: list[RunResult]                  # 长度 == repeats
    warmup_samples: list[RunResult]           # 长度 == warmup_repeats（丢弃，仅审计用）
    artifacts: list[Path]                     # 所有 repeat 产出的 artifact 路径
    failure: SkillFailure | None              # None 表示成功
    duration_sec: float
```

### 8.3 SkillFailure 类型

```python
@dataclass
class SkillFailure:
    failure_class: str  # "skill_violation" | "skill_failed" | "skill_timeout"
    stage: str          # "load" | "manifest_validate" | "setup" | "run" | "teardown"
    repeat_idx: int     # -1 if not in repeat
    message: str
    detail: dict        # 细节（违规权限、超时秒数等）
```

### 8.4 Benchmark Agent 调用示例

```python
# Benchmark Agent 内部（Compiler 中 B8.2 已有示例）
runtime = SkillRuntime(config=task.cnei_config.skill_runtime_config)

loaded = runtime.load_skill(Path("my_skills/video_player_startup"))

result = runtime.execute(
    skill=loaded,
    ctx_factory=lambda repeat_idx: SkillContext(
        task_id=task.task_id,
        skill_id=loaded.skill_id,
        repeat_idx=repeat_idx,
        platform=task.payload.device_config.backend,
        device=device_adapter,
        host=host_adapter,
        workspace=workspace_manager.get_workspace_api(task.task_id),
        ...
    ),
    warmup_repeats=loaded.manifest.warmup_repeats,
    repeats=loaded.manifest.repeats,
)

if result.failure:
    # 转成 FailureEnvelope
    ...
else:
    # samples 进入 ValidateResult / CompareBaseline 流程
    ...
```

---

## 9. Phase 1.5 升级路径（v0.2 重写）

### 9.0 关键决定：Phase 1B 不引入 monkey patch（v0.2 明确）

**v0.2 文档头已说明**：Phase 1B 是 best-effort policy enforcement，**不引入** Python monkey patch / import hook。

**理由**（重申）：

1. monkey patch 可被绕过（`importlib.reload(subprocess)` / `os.popen` / `ctypes` 调底层 syscall / 各种间接路径）
2. 真正隔离需要 OS-level mechanism（namespace / cgroup / seccomp）
3. 做不彻底反而给"安全错觉"，导致用户写出不规范代码到 Phase 1.5 大量返工
4. 100 人内部场景假设用户合作，不做防御性运行

### 9.1 Static Scan: warning → block（Phase 1.5）

Phase 1B 是 warning（emit event 但不阻止加载），Phase 1.5 升级为 block：

- `subprocess.run / Popen / call` → **加载时拒绝**
- `os.system` → 加载时拒绝
- `open(<abs_path>)` 直接读写 → 加载时拒绝
- `requests.* / urllib.request.urlopen` 等网络 → 加载时拒绝

但 static scan **本质仍是代码 review 工具**，不是安全机制。真正的隔离靠 9.2。

### 9.2 容器化 Skill 执行（Phase 1.5 真正的隔离）

**Phase 1.5 引入 Docker / Podman 容器**——这是 Phase 1B 没有、Phase 1.5 才有的核心安全机制：

| 隔离维度 | Phase 1B（best-effort）| Phase 1.5（容器化）|
|---|---|---|
| 文件系统 | ctx.workspace 路径检查 | **bind mount workspace 到容器，host 文件系统不可见** |
| 网络 | ctx.network gating | **network namespace，未声明 network=true 的 Skill 无网络** |
| 进程 | Python 进程 | **PID namespace，看不到 host 其他进程** |
| 命令执行 | allowed_commands 匹配 | 仍保留 + **容器内只装 allowed_commands 列出的工具** |
| 系统设置修改 | trace 警告 | **read-only system mount，无法修改 governor/thermal/sysctl** |
| 资源 | timeout | timeout + **cgroup CPU / memory limit** |

**关键点**：即使 Skill 用 `subprocess.run("rm -rf /")`，在容器里执行也只能影响 容器内（被 bind mount + read-only 隔离），不会损坏 host。

**升级策略**（不破坏 v0.2 API）：

- v0.2 Skill 代码**完全不需要改**（仍然用 `ctx.device.exec` / `ctx.workspace.write` 等）
- v0.2 用户**习惯了用 ctx API**，Phase 1.5 容器化后体验一致
- 没用过 ctx API 的"坏 Skill"会在 Phase 1.5 加载时直接被 static scan block

### 9.3 device_state_dirty 在 Phase 1.5 的演化

Phase 1B：device_state_dirty 仅靠 SkillRuntime 标记（best-effort）。

Phase 1.5 增强：

- Skill 容器执行结束后，自动 snapshot device 状态（thermal / governor / processes）
- 与 baseline snapshot 比较，差异超阈值标 dirty
- 不依赖 Skill 自己声明 cleanup_failed

### 9.4 Skill Marketplace（Phase 2+ 远景）

容器化让 Skill 可以真正"安全运行不可信代码"，因此 Phase 2+ 可以考虑：

- 团队内部共享 Skill
- 版本管理 + 依赖管理
- 自动安全审计 + 容器镜像签名

---

## 10. 测试覆盖要求

### 10.1 SkillRuntime 单元测试

- [ ] Manifest validate：所有必填字段 + 字段非法 + destructive 未声明 + cleanup_required 与 teardown 不匹配
- [ ] Static scan：subprocess / os.system / open(abs) / requests / urllib 各 1 个测试
- [ ] Permission enforce：required_permissions 缺失时调用对应 ctx API 抛 SkillViolationError
- [ ] Allowlist/denylist：命令首词匹配 / 不匹配
- [ ] Workspace isolation：相对路径正常 / 绝对路径拒绝 / 路径越界（含 ..）拒绝
- [ ] Network gating：network=true / network=false 调用 ctx.network.fetch
- [ ] Output validate：metrics keys 多 / 少 / 类型错误
- [ ] Cleanup：run 抛异常时 teardown 仍执行
- [ ] Timeout：超时 SIGKILL

### 10.2 集成测试

- [ ] 5 个示例 Skill 在 x86 上全部跑通
- [ ] video_player_startup + browser_load_time 在 Tizen device 上跑通
- [ ] Skill failure 转成 `skill_violation` / `skill_failed` / `skill_timeout` FailureEnvelope
- [ ] cleanup_required: true 测试场景

### 10.3 覆盖率要求

- UT 覆盖率 ≥ 80%（同 Compiler Agent）
- 5 个示例 Skill 必须有端到端测试

---

**文档结束**
