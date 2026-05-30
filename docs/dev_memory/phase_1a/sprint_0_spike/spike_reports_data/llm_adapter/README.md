# LLM Adapter 接入指南

本目录提供 Coding System 调 LLM 的抽象层。开发期默认用 Kimi(Moonshot),公司部署到生产环境时,公司 AI 按本文档接入公司 LLM。

## 目录

- [架构概览](#架构概览)
- [开发期使用(Kimi)](#开发期使用kimi)
- [公司部署:接入步骤](#公司部署接入步骤)
- [安全 / 审计 / 合规](#安全--审计--合规)
- [FAQ](#faq)

---

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│  S0-A spike 脚本 / 未来 Compiler Agent              │
│  只调用统一接口 LLMAdapter.call(prompt) → LLMResponse │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  get_adapter()  │   工厂方法,读 llm_config.yaml
              │  ←  active_provider
              └────────┬────────┘
                       │
       ┌───────┬───────┼───────┬────────┬───────────┐
       ▼       ▼       ▼       ▼        ▼           ▼
   KimiAdapter ClaudeAdapter OpenAIAdapter CustomAdapter ClineAdapter
                                          ↑ OpenAI 兼容  ↑ 公司私有协议
                                                          (部署时实现)
```

**核心好处**:
- 主代码只依赖 `LLMAdapter` 抽象,换 provider 不动一行代码
- 配置文件控制所有 provider 参数(endpoint / model / key 来源)
- API key 永不写死,只从环境变量读
- 所有调用自动记录 trace(redact 后),用于审计

---

## 开发期使用(Kimi Code)

S0-A spike 默认用 **Kimi Code**(Kimi 会员的 coding 体系),用你 Kimi Code Console 创建的 API key。

### 两个独立的 Kimi 体系(重要,别混)

| | Kimi Code(active_provider=kimi_code,开发期用) | Moonshot Open Platform(active_provider=kimi,备用) |
|---|---|---|
| 注册 | Kimi 会员 + Kimi Code Console | platform.moonshot.ai/.cn |
| key | sk-... ~72 字符 | sk-... |
| endpoint | api.kimi.com/coding/v1/chat/completions | api.moonshot.ai/v1/chat/completions |
| 模型 | kimi-for-coding | kimi-k2.6 |
| 计费 | Kimi 会员 Kimi Code 额度 | pay-as-you-go |
| env 变量 | KIMI_CODE_API_KEY | MOONSHOT_API_KEY |

**两套 key 不通用**!Kimi Code 的 key 发给 Moonshot Open Platform 会 401,反之亦然。

### 安装依赖

```bash
pip install pyyaml requests
```

### 配置 API key

```bash
# Kimi Code(默认)
export KIMI_CODE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 如果将来切到 Moonshot Open Platform,改 active_provider 为 kimi 并设:
# export MOONSHOT_API_KEY=sk-yyyyyyyyyy
```

### Kimi Code 合规要求

Kimi Code 社区准则明确:
- **必须保持真实 User-Agent 标识**(adapter 已设为 `Coding-Spike/1.0`)
- 不能伪装成其他被授权客户端(如 Claude Code / Roo Code)
- 否则可能导致会员权益暂停

quota 与日常 Kimi Code IDE/CLI **共享**(每 5h 滚动窗口约 300-1200 requests)。S0-A 12 次调用占比极低。

### 快速测试

```bash
cd llm_adapter/
python3 llm_adapter.py llm_config.yaml
```

期望输出:
```
Active provider: kimi
Model: kimi-k2.6
测试调用 (say 'hello' 一下):
  Response: hello
  Tokens: in=10 out=2
  Duration: 1234ms
  Trace: /tmp/coding-system-s0/llm_traces/s0a-xxxxxxxxxxxx.json
OK
```

### 在 S0-A spike 脚本中使用

```python
from llm_adapter import get_adapter

adapter = get_adapter('llm_adapter/llm_config.yaml')
response = adapter.call(
    prompt="修这个编译错误: ...",
    system="你是 C/C++ 编译错误修复专家",
    scenario_id="A_with_negative_facts",  # 可选,A/B 测试场景标识
)
print(response.content)           # patch
print(response.token_usage)       # {'in': N, 'out': M, 'total': T} - 见下方字段语义
print(response.duration_ms)
print(response.request_id)        # 用此 ID 找 trace
```

### token_usage 字段语义(重要,避免外层调用混乱)

Adapter 返回的 `LLMResponse.token_usage` 使用**单次 LLM 调用**语义:

```python
{'in': int, 'out': int, 'total': int}
```

**这与 Contract v0.7.3 §5(task 级 budget tracking)的字段不同**。Contract 用 `total_in / total_out / by_stage`,表达整个 Compiler Agent task 跨多次 LLM 调用 + 跨 stage 的累计 budget。

**外层 Compiler Agent 实现时遵守此映射**:

```python
# adapter 单次调用 → Compiler Agent task budget 聚合
contract_budget['total_in']  += response.token_usage['in']
contract_budget['total_out'] += response.token_usage['out']
contract_budget['by_stage'][current_stage]['in']  += response.token_usage['in']
contract_budget['by_stage'][current_stage]['out'] += response.token_usage['out']
```

**设计理由**:
- adapter 不该越界做 task 级聚合(那是 Compiler Agent 的职责)
- adapter 字段贴近 LLM API 行业标准(OpenAI/Anthropic/Kimi 原生字段都是单次 in/out)
- Contract 的 by_stage 在单次调用层是死字段,强行对齐会导致语义错配

---

## 公司部署:接入步骤

公司 AI 部署到生产环境时,按以下步骤接入公司 LLM。

### 步骤 0:确认公司 LLM 协议类型

打开公司 LLM 平台的 API 文档,确认其协议:

| 协议 | 判断方法 | 走哪个 adapter |
|---|---|---|
| OpenAI 兼容 | 文档说"OpenAI compatible" 或 endpoint 是 `.../v1/chat/completions` | **`custom` provider**(改 config 即可,**不动代码**) |
| Anthropic 兼容 | 文档说"Anthropic compatible" 或 endpoint 是 `.../v1/messages` | `claude` provider(改 config) |
| 公司私有协议 | 都不是,有自己的请求/响应格式 | **`cline` provider**(实现 ClineAdapter.call) |

### 步骤 1(简单情况):公司 LLM 是 OpenAI 兼容

**最常见情况,改 config 文件即可,不必动代码。**

编辑 `llm_config.yaml`:

```yaml
active_provider: custom    # 改为 custom

providers:
  custom:
    api_base: https://your-company-llm.internal/v1/chat/completions  # 公司 endpoint
    model: your-company-model-id                                      # 公司模型 ID
    api_key_env: COMPANY_LLM_API_KEY                                  # 环境变量名
    max_tokens: 4096
    temperature: 0.0
    timeout_sec: 60
    extra_headers:                                                    # 如有公司特定 header
      X-Company-Tenant: my-tenant
```

设置环境变量:
```bash
export COMPANY_LLM_API_KEY=<your_company_key>
```

验证:
```bash
python3 llm_adapter.py llm_config.yaml
```

应该看到"OK"。**到这一步就结束了。**

### 步骤 2(简单情况):公司 LLM 是 Anthropic 兼容

类似步骤 1,改为 `active_provider: claude`,然后改 `providers.claude.api_base` 为公司 endpoint。

### 步骤 3(复杂情况):公司 LLM 是私有协议

如果公司 LLM 协议**完全私有**(不是 OpenAI 或 Anthropic 兼容),需要在 `llm_adapter.py` 中实现 `ClineAdapter.call()`。

#### 3.1 模板代码

```python
class ClineAdapter(LLMAdapter):
    def call(self, prompt, system=None):
        request_id = self._gen_request_id()
        api_key = self._get_api_key()
        
        # ====== 1. 构造公司协议的请求 ======
        payload = {
            # 按公司 API 文档填字段
            'your_company_prompt_field': prompt,
            'your_company_system_field': system,
            'your_company_model_field': self.config['model'],
            # 等等
        }
        headers = {
            'YourCompanyAuthHeader': api_key,
            'Content-Type': 'application/json',
        }
        headers.update(self.config.get('extra_headers', {}))
        
        # ====== 2. 调公司 endpoint ======
        start = time.time()
        resp_json = self._do_request_with_retry(
            'POST', self.config['api_base'], headers=headers, json=payload,
        )
        duration_ms = int((time.time() - start) * 1000)
        
        # ====== 3. 解析公司协议的响应 ======
        try:
            content = resp_json['your_company_response_field']
            token_usage = {
                'in': resp_json.get('your_in_token_field', 0),
                'out': resp_json.get('your_out_token_field', 0),
                'total': resp_json.get('your_total_token_field', 0),
            }
            finish_reason = resp_json.get('your_finish_field')
        except (KeyError, TypeError) as e:
            raise LLMAdapterError(f"公司 LLM 响应格式异常: {e}")
        
        # ====== 4. 返回统一格式 LLMResponse ======
        response = LLMResponse(
            content=content,
            raw_response=resp_json,
            token_usage=token_usage,
            duration_ms=duration_ms,
            provider=self.provider_name,
            model=self.config['model'],
            request_id=request_id,
            finish_reason=finish_reason,
        )
        self._log_call(request_id, payload, response)
        return response
```

#### 3.2 配置文件

```yaml
active_provider: cline

providers:
  cline:
    api_base: https://company-cline.internal/api/...
    model: company-model-v1
    api_key_env: CLINE_API_KEY
    auth_method: api_key                # 公司认证方式
    max_tokens: 4096
    temperature: 0.0
    timeout_sec: 60
    extra_headers:
      X-Custom-Header: value
```

#### 3.3 验证

```bash
export CLINE_API_KEY=...
python3 llm_adapter.py
```

---

## 安全 / 审计 / 合规

### API key 安全

- **永不写死在代码或 config 文件**:只从环境变量读
- **永不 commit 到 git**:`.env` 文件加入 `.gitignore`(项目根目录 `.gitignore` 已含)
- log 自动 redact 以下 secret pattern(Codex review 强化):
  - OpenAI/Anthropic/Moonshot API key 前缀(`sk-...`, `sk-ant-...`)
  - HTTP `Bearer ...` / `Basic ...` 认证头
  - JWT 三段式(`eyJ...`)
  - key=value 形式(`api_key=...`, `secret=...`)
  - 长 hex token(≥32 字符 hash/key)

### 审计 trace

每次调 LLM 自动写一份 trace 到 `common.log_dir`(默认 `/tmp/coding-system-s0/llm_traces/`):

```json
{
  "request_id": "s0a-abc123",
  "provider": "kimi",
  "model": "kimi-k2.6",
  "timestamp": "2026-05-30T...",
  "request": { ... 完整 prompt },
  "response": { ... 含 token_usage / duration_ms }
}
```

**重要标识**:trace 文件顶部强制带 `LOCAL_ONLY_EXPERIMENTAL_TRACE` 标记,明确**不是 Contract trace/artifact,不进 repo,只供本地审计**。

**raw log baseline 警告(变体 D)**:当 `scenario_id` 包含 `raw_log` 时(如 S0-A A/B 测试变体 D),trace 会额外加 `_RAW_LOG_BASELINE_WARNING` 字段,提醒该 trace 含 raw build log,绝不能 commit 或分享。

**生产部署最小 checklist**(Codex review 强化):
- [ ] `log_dir` 改为安全位置(不在 `/tmp`,避免丢失或被其他用户读)
- [ ] log 目录权限严格 `0700`(代码默认 chmod,但生产要额外验证)
- [ ] trace 文件权限严格 `0600`(代码默认 chmod)
- [ ] 定期清理过期 trace(建议保留 ≤ 7 天)
- [ ] secret scan 流水线集成(防 trace 误进 git)
- [ ] raw log scan(grep `RAW_LOG_BASELINE_WARNING`,确保此类 trace 永不外传)
- [ ] 考虑关 `log_prompts: false`(若公司合规要求 prompt 不落盘)
- [ ] 若公司有审计系统,改为同时上报到公司 audit log,而非只本地

### 合规检查清单(公司部署前)

公司 AI 部署前请逐项检查:

- [ ] **API key 不在代码 / config / log 出现明文**
- [ ] **trace 目录权限收紧**(只 owner 可读)
- [ ] **endpoint 用公司内网 / VPN,不直连外网**
- [ ] **temperature=0 是否符合复现性要求**(如不需要,可调高)
- [ ] **max_tokens 上限**符合公司 token budget 控制
- [ ] **retry 策略**(默认 2 次)是否符合公司 SLA
- [ ] **timeout**(默认 60 秒)是否符合公司 SLA
- [ ] **extra_headers** 是否包含必需的 tenant / tracing header
- [ ] **是否需要加 audit log 上报公司日志系统**
- [ ] **是否需要 PII / 敏感信息检测**(在 _redact 加规则)

---

## FAQ

**Q: 我可以不用 OpenAI / Anthropic / Kimi 中的任何一个吗?**
A: 可以。如果公司有自己的 LLM,按"步骤 3"实现 ClineAdapter,或如果公司 LLM 是 OpenAI 兼容协议,直接用 `custom` provider 改 config。

**Q: 一次实验中需要切换多个 provider 怎么办(比如 A 用 Kimi,B 用 Claude)?**
A: spike 脚本中可以直接传 config_path:
```python
kimi = get_adapter('llm_config_kimi.yaml')
claude = get_adapter('llm_config_claude.yaml')
```

**Q: 如何禁用 trace log(为了快)?**
A: 设置 `common.log_prompts: false`。

**Q: 如何调试响应解析问题?**
A: 看 trace 文件,里面有完整 raw_response,可以人工核对。

**Q: 这个 adapter 支持流式(streaming)吗?**
A: 当前版本不支持(spike 阶段不需要)。如果生产需要,改 `call()` 加 `stream=True` 处理。

**Q: 支持多轮对话吗?**
A: 当前 `call(prompt, system)` 只支持单轮。多轮需扩接口为 `call(messages: list)`。spike 阶段单轮够用。

**Q: API key 怎么管理才合规?**
A: 公司部署期建议用 Secret Manager(如 HashiCorp Vault / AWS Secrets Manager / 公司内部 secret 平台),不要用 plain env var。可以在 `_get_api_key` 加 fallback 逻辑:先查 Secret Manager,fail 再查 env。
