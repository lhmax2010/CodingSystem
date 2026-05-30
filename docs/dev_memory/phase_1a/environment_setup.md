# Coding System Phase 1A 环境恢复指南

本文档记录 Phase 1A 开发所需的所有外部资源和环境配置,确保换机器、换人接手时能完整复现。

## 1. 验证基线代码库

### 1.1 主基线:pkgmgr-info(Sprint 0 全程使用)

```bash
# 克隆主验证基线
git clone "git://review.tizen.org/git/platform/core/appfw/pkgmgr-info" -b tizen
```

- 路径约定:`CodingSystem/codes/pkgmgr-info/`
- 行数:约 48,588 行 C/C++/CMake
- 构建:cmake + ninja(GBS x86_64 chroot)
- 已用于:Sprint 0 全部 9 个 gate

### 1.2 跨包验证补充包(S0-C 使用)

PM 提供的 4 个相关包,用于 S0-C 跨包最小验证:

```bash
git clone "git://review.tizen.org/git/platform/core/appfw/pkgmgr-info" -b tizen
git clone "git://review.tizen.org/git/platform/core/api/app-common" -b tizen
git clone "git://review.tizen.org/git/platform/core/api/common" -b tizen
git clone "git://review.tizen.org/git/platform/core/api/app-manager" -b tizen_10.0
```

- 路径约定:`CodingSystem/codes/<package_name>/`
- 用途:S0-C 跨包最小验证(从中选 2 个有真实依赖的做实验)
- 注意:`.gitignore` 中已 `/codes/` 排除,代码不进 repo

### 1.3 .gitignore 已包含的条目

```
/codes/                    # Tizen 包源码不进 repo
/tmp/                      # 临时工作区(Codex 解压 / 文件操作)
/tmp/coding-system-s0/     # raw log + LLM trace
.bak/                      # 备份目录
```

## 2. 工具链 + 构建环境

### 2.1 GBS(Tizen 构建工具)

- GBS 版本:与 Tizen 10.0 build farm 一致
- 配置文件路径:`/home/<user>/Toolchain/gbs_llvm.conf`
- 构建 profile:`profile.tizen_10.0`(native x86_64)

### 2.2 Clang 工具链

- 当前版本:Clang 21.1.1
- 路径:由 GBS chroot 提供
- compile_commands.json 生成:`cmake -GNinja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ...`

### 2.3 clangd

- 版本:跟随 Clang 21
- 用于 S0-03 验证语义级符号查找

### 2.4 其他依赖

```bash
# Python(用于 spike 脚本 + LLM Adapter)
python3 >= 3.9

# LLM Adapter 依赖
pip install pyyaml requests
```

## 3. LLM 接入

### 3.1 开发期(Kimi Code)

S0-A spike 默认使用 **Kimi Code**(Kimi 会员的 coding 体系):

```bash
export KIMI_CODE_API_KEY=<your_kimi_code_api_key>
```

API key 来源:**Kimi Code Console**(需要 Kimi 会员账户 + 启用 Kimi Code 额度)。
不要与 Moonshot Open Platform 的 API key 混淆(两个独立体系,key 不通用)。

**合规提醒**:Kimi Code 要求保持真实 User-Agent 标识,adapter 已设为 `Coding-Spike/1.0`,不要改成其他被授权客户端的标识(否则违反 Kimi Code 社区准则)。

quota 与日常 Kimi Code IDE/CLI 共享(每 5h 滚动窗口约 300-1200 requests)。

#### 备用:Moonshot Open Platform

如果将来想切换到 Moonshot Open Platform(pay-as-you-go,api.moonshot.ai/v1):

```bash
# 1. 在 llm_config.yaml 改 active_provider: kimi
# 2. 设置 MOONSHOT_API_KEY(来源 platform.moonshot.ai/.cn)
export MOONSHOT_API_KEY=<your_moonshot_api_key>
```

详见 `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/llm_adapter/README.md`。

### 3.2 公司部署期

按 LLM Adapter README 的"公司部署:接入步骤"章节,公司 AI 配置 `cline` 或 `custom` provider。

## 4. Codex Workspace 目录约定

```
CodingSystem/                      # Codex workspace = repo 根
├── docs/                          # repo 内文档
├── .gitignore                     # 包含 /codes/, /tmp/, /tmp/coding-system-s0/, .env
├── codes/                         # Tizen 包源码(被 .gitignore 排除,不进 repo)
│   ├── pkgmgr-info/               # branch: tizen
│   ├── app-common/                # branch: tizen
│   ├── common/                    # branch: tizen
│   └── app-manager/               # branch: tizen_10.0
└── tmp/                           # 临时工作区(被 .gitignore 排除,Codex 解压/操作用)

外部路径(在 CodingSystem 外):
/home/<user>/Toolchain/            # GBS 配置
└── gbs_llvm.conf
/tmp/coding-system-s0/             # raw log + LLM trace(被 .gitignore 排除)
├── *.log                          # raw build log(spike 期临时)
└── llm_traces/                    # LLM 调用 trace
    └── *.json                     # LOCAL_ONLY_EXPERIMENTAL_TRACE
```

## 5. 换环境复现步骤

新开发机或新人接手时:

1. **克隆 CodingSystem repo**:
   ```bash
   git clone <CodingSystem-repo-url>
   cd CodingSystem
   git checkout codex/sprint-0-main
   ```

2. **克隆 Tizen 验证包**(见 §1):
   ```bash
   cd CodingSystem
   mkdir -p codes && cd codes
   # 跑 §1.2 的 4 个 git clone(注意 pkgmgr-info 是 tizen branch,app-manager 是 tizen_10.0)
   ```

3. **配置 GBS + Clang**(见 §2)

4. **设置 LLM API key**(见 §3):
   ```bash
   # S0-A 默认 Kimi Code
   export KIMI_CODE_API_KEY=<key>
   ```

5. **跑 LLM Adapter smoke test 验证**:
   ```bash
   cd CodingSystem
   pip install pyyaml requests
   python3 docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/llm_adapter/llm_adapter_smoke_test.py \
       docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/llm_adapter/llm_config.yaml
   ```
   全部 PASS 表示环境就绪。

6. **读 Codex 加载顺序文档**(R6):
   - `docs/README.md`
   - `docs/baseline/` 全部
   - `docs/adr/`
   - `docs/design_changes/`(含 change_1/2/3)
   - `docs/dev_memory/`(含 sprint_0_memory + 9 个 spike 报告)
   - `docs/checkpoints.md`

可恢复到当前状态(Sprint 0 收官 + change_3 修正完成),准备进入 S0-A / S0-C。
