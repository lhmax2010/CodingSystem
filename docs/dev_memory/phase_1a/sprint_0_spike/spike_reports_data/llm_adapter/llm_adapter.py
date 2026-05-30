"""
LLM Adapter 抽象层 — Coding System Phase 1A Sprint 0 S0-A Spike

设计意图:
  - S0-A 主脚本通过统一接口 LLMAdapter.call() 调 LLM,不感知具体 provider
  - 配置文件指定用哪个 provider,主脚本不动
  - 公司部署时可加 CompanyAdapter / 改 ClineAdapter,主脚本仍不动

接入指南见 README.md。

注意:
  - API key 永不写死,只从环境变量读
  - 所有 log 自动 redact key
  - temperature 默认 0(spike 要可复现)
  - 公司部署时,请 review 此文件是否符合公司安全/网络/合规要求
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional
import os
import json
import time
import uuid
import logging

try:
    import yaml
    import requests
except ImportError as e:
    raise RuntimeError(
        f"缺依赖: {e}. 请安装: pip install pyyaml requests"
    )


# ============================================================================
# 数据契约
# ============================================================================

@dataclass
class LLMResponse:
    """所有 adapter 必须返回这个统一格式。
    
    Note on token_usage field naming (Codex review 设计澄清):
    
      Adapter 层使用 *单次 LLM 调用* 语义:
        {'in': int, 'out': int, 'total': int}
      
      这与 Contract v0.7.3 §5 (task 级 budget tracking) 字段 *不同*:
        Contract 用 {'total_in', 'total_out', 'by_stage'} 表达整个 Compiler Agent
        task 跨多次 LLM 调用 + 跨 stage 的累计 budget。
      
      外层 Compiler Agent 实现时遵守此映射:
      
          # adapter 单次调用 → task budget 聚合
          contract_budget['total_in']  += response.token_usage['in']
          contract_budget['total_out'] += response.token_usage['out']
          contract_budget['by_stage'][stage]['in']  += response.token_usage['in']
          contract_budget['by_stage'][stage]['out'] += response.token_usage['out']
      
      理由:
        - adapter 不该越界做 task 级聚合(那是 Compiler Agent 的职责)
        - adapter 字段贴近 LLM API 行业标准(OpenAI/Anthropic/Kimi 原生字段都是单次 in/out)
        - Contract 的 by_stage 在单次调用层是死字段,强行对齐会导致语义错配
      
      详见: S0-A_Repair_Loop_Spike.md "token_usage 字段语义" 章节。
    """
    content: str                              # LLM 返回的主要内容(通常含 patch)
    raw_response: dict                        # 原始 JSON 响应(审计用)
    token_usage: dict = field(default_factory=dict)  # 单次调用 {'in', 'out', 'total'} - 见上方注释
    duration_ms: int = 0
    provider: str = ""
    model: str = ""
    request_id: str = ""
    finish_reason: Optional[str] = None       # stop / length / error


class LLMAdapterError(Exception):
    """所有 adapter 抛这个异常,不要抛各家 SDK 的特定异常。"""
    pass


# ============================================================================
# 抽象基类
# ============================================================================

class LLMAdapter(ABC):
    """所有 LLM provider adapter 实现此接口。"""

    def __init__(self, provider_name: str, provider_cfg: dict, common_cfg: dict):
        self.provider_name = provider_name
        self.config = provider_cfg
        self.common = common_cfg
        self._setup_logging()

    @abstractmethod
    def call(self, prompt: str, system: Optional[str] = None,
             scenario_id: Optional[str] = None) -> LLMResponse:
        """
        调 LLM 并返回统一格式 LLMResponse。
        
        Args:
            prompt: 用户 prompt
            system: 可选 system prompt
            scenario_id: 可选 A/B 测试场景标识(用于 trace,如 'A_with_negative_facts')
        
        Returns:
            LLMResponse 实例
        
        Raises:
            LLMAdapterError: 任何 LLM 调用错误(网络/认证/超时/响应格式异常)
        """
        pass

    # ---- 通用工具方法,子类直接用 ----

    def _get_api_key(self) -> str:
        """从环境变量读 API key,不写死。"""
        key_env = self.config.get('api_key_env')
        if not key_env:
            raise LLMAdapterError(
                f"provider '{self.provider_name}' 配置缺 api_key_env"
            )
        key = os.environ.get(key_env)
        if not key:
            raise LLMAdapterError(
                f"环境变量 {key_env} 未设置。"
                f"开发期请: export {key_env}=<your_key>"
            )
        return key

    def _gen_request_id(self) -> str:
        prefix = self.common.get('request_id_prefix', 's0a')
        return f"{prefix}-{uuid.uuid4().hex[:12]}"

    # Redact patterns(Codex review 强化):覆盖常见 secret 形态
    _REDACT_PATTERNS = [
        # API key 常见前缀
        (r'sk-ant-[a-zA-Z0-9_\-]{20,}', '[REDACTED:anthropic_key]'),
        (r'sk-[a-zA-Z0-9_\-]{20,}',     '[REDACTED:openai_or_kimi_key]'),
        # HTTP Authorization headers
        (r'(?i)Bearer\s+[a-zA-Z0-9_\-\.]{20,}',  '[REDACTED:bearer]'),
        (r'(?i)Basic\s+[A-Za-z0-9+/=]{20,}',      '[REDACTED:basic_auth]'),
        # JWT (header.payload.signature 三段 base64url)
        (r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}',
         '[REDACTED:jwt]'),
        # API key in key=value form
        (r"(?i)(api[_\-]?key|apikey|access[_\-]?token|secret)\s*[=:]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?",
         r'\1=[REDACTED]'),
        # 长 hex (≥32 chars,可能是 hash/key/token)
        (r'\b[a-fA-F0-9]{32,}\b', '[REDACTED:hex_token]'),
    ]

    def _redact(self, text: str) -> str:
        """log 输出前自动 redact API key 等敏感信息。
        
        覆盖:
        - OpenAI/Anthropic/Moonshot API key 前缀
        - HTTP Bearer/Basic auth header
        - JWT 三段式
        - key=value / apikey:xxx 形式
        - 长 hex token (≥32 字符)
        """
        if not self.common.get('redact_keys', True):
            return text
        import re
        for pattern, replacement in self._REDACT_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text

    def _setup_logging(self):
        """初始化 trace log 目录。
        
        Codex review 强化:
        - 目录权限 0700 (只 owner 可读写,防止其他用户读到 prompt/secret)
        - 这是 *local-only experimental trace*,不是 Contract trace/artifact
        - trace 文件不进 repo (依赖 .gitignore 排除 /tmp/coding-system-s0/)
        - 生产部署需另行配置(见 README "trace 章节生产 checklist")
        """
        log_dir = self.common.get('log_dir', '/tmp/coding-system-s0/llm_traces')
        os.makedirs(log_dir, exist_ok=True)
        # 强制目录权限 0700 (只 owner)
        try:
            os.chmod(log_dir, 0o700)
        except (OSError, PermissionError):
            pass  # 某些 FS 不支持 chmod (Windows / FAT) 时 silent
        self.log_dir = log_dir

    def _log_call(self, request_id: str, payload: dict, response: LLMResponse,
                  scenario_id: Optional[str] = None):
        """记录调用 trace 到磁盘。
        
        Codex review 强化:
        - 文件权限 0600 (防其他用户读)
        - trace 顶部加显式 LOCAL_ONLY_EXPERIMENTAL_TRACE 标记
        - 如 scenario_id = 'D_raw_log_truncated' (raw log baseline 变体),
          trace 额外加 'RAW_LOG_BASELINE_WARNING' 强提示,防止误传播到 repo
        - 所有内容过 _redact (key/jwt/bearer/hex/api_key= 都打码)
        """
        if not self.common.get('log_prompts', True):
            return
        trace_path = os.path.join(self.log_dir, f"{request_id}.json")
        
        trace = {
            '_NOTICE': 'LOCAL_ONLY_EXPERIMENTAL_TRACE — not a Contract trace; '
                       'do not commit to repo or include in artifacts',
            'request_id': request_id,
            'scenario_id': scenario_id,  # A_with_negative_facts / D_raw_log_truncated / etc
            'provider': self.provider_name,
            'model': self.config.get('model'),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'request': payload,
            'response': asdict(response),
        }
        
        # 变体 D (raw log baseline) 加强提示
        if scenario_id and 'raw_log' in scenario_id.lower():
            trace['_RAW_LOG_BASELINE_WARNING'] = (
                'This trace contains raw build log as part of A/B baseline. '
                'NEVER commit. NEVER share. Local audit only.'
            )
        
        trace_str = self._redact(json.dumps(trace, ensure_ascii=False, indent=2))
        with open(trace_path, 'w') as f:
            f.write(trace_str)
        try:
            os.chmod(trace_path, 0o600)
        except (OSError, PermissionError):
            pass

    # HTTP 状态码重试策略(Codex review 修复):
    # 重试: 429 (rate limit), 408 (timeout), 500/502/503/504 (transient server error)
    # 不重试: 401/403 (auth), 400/404/422 (client error - 重试无用)
    _RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}

    def _do_request_with_retry(self, method: str, url: str, **kwargs) -> dict:
        """带重试的 HTTP 请求。
        
        重试策略:
        - 网络异常(requests.RequestException) → 重试
        - HTTP 429/408/5xx → 重试(transient)
        - HTTP 401/403/400/404/422 → 不重试(永久错误,重试无用)
        - 重试间隔: backoff + jitter (避免雷暴效应)
        """
        import random

        retry_max = self.common.get('retry_max', 2)
        backoff = self.common.get('retry_backoff_sec', 5)
        timeout = self.config.get('timeout_sec', 60)

        for attempt in range(retry_max + 1):
            try:
                resp = requests.request(method, url, timeout=timeout, **kwargs)

                if resp.status_code < 400:
                    return resp.json()

                # HTTP 错误:判断是否重试
                if resp.status_code in self._RETRY_STATUS_CODES and attempt < retry_max:
                    # 加 jitter 避免多 client 同时重试
                    sleep_sec = backoff * (2 ** attempt) + random.uniform(0, backoff)
                    time.sleep(sleep_sec)
                    continue

                # 永久错误或重试次数用尽,直接抛
                raise LLMAdapterError(
                    f"HTTP {resp.status_code} (不重试或重试已用尽): "
                    f"{self._redact(resp.text[:500])}"
                )

            except (requests.Timeout, requests.ConnectionError) as e:
                # 网络层错误,可重试
                if attempt < retry_max:
                    sleep_sec = backoff * (2 ** attempt) + random.uniform(0, backoff)
                    time.sleep(sleep_sec)
                    continue
                raise LLMAdapterError(
                    f"调用 {self.provider_name} 网络失败"
                    f"(已重试 {retry_max} 次): {e}"
                )
            except (requests.RequestException, ValueError) as e:
                # 其他 requests 异常 / JSON 解析失败,不重试
                raise LLMAdapterError(
                    f"调用 {self.provider_name} 失败: {e}"
                )


# ============================================================================
# OpenAI-兼容 adapter(基类:Kimi / OpenAI / Custom 共用)
# ============================================================================

class _OpenAICompatibleAdapter(LLMAdapter):
    """
    OpenAI /v1/chat/completions 兼容协议的通用实现。
    Kimi / OpenAI / Custom 都基于这个。
    """

    def call(self, prompt: str, system: Optional[str] = None,
             scenario_id: Optional[str] = None) -> LLMResponse:
        """
        scenario_id: 可选,A/B 测试场景标识(透传到 trace,如 'A_with_negative_facts'
                     'D_raw_log_truncated')。raw_log_* 场景会触发 trace 加强警告。
        """
        request_id = self._gen_request_id()
        api_key = self._get_api_key()

        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})

        payload = {
            'model': self.config['model'],
            'messages': messages,
            'max_tokens': self.config.get('max_tokens', 4096),
            'temperature': self.config.get('temperature', 0.0),
        }

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        headers.update(self.config.get('extra_headers', {}))

        start = time.time()
        try:
            resp_json = self._do_request_with_retry(
                'POST',
                self.config['api_base'],
                headers=headers,
                json=payload,
            )
        except LLMAdapterError:
            raise

        duration_ms = int((time.time() - start) * 1000)

        # 解析响应(OpenAI 兼容格式)
        try:
            choice = resp_json['choices'][0]
            content = choice['message']['content']
            finish_reason = choice.get('finish_reason')
            usage = resp_json.get('usage', {})
            token_usage = {
                'in': usage.get('prompt_tokens', 0),
                'out': usage.get('completion_tokens', 0),
                'total': usage.get('total_tokens', 0),
            }
        except (KeyError, IndexError) as e:
            raise LLMAdapterError(
                f"{self.provider_name} 响应格式异常: {e}, raw: {resp_json}"
            )

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

        # redact 后的 payload 写 log
        log_payload = dict(payload)
        self._log_call(request_id, log_payload, response, scenario_id=scenario_id)
        return response


class KimiAdapter(_OpenAICompatibleAdapter):
    """Kimi (Moonshot AI) — OpenAI 兼容。"""
    pass


class OpenAIAdapter(_OpenAICompatibleAdapter):
    """OpenAI — 原生 chat completions。"""
    pass


class CustomAdapter(_OpenAICompatibleAdapter):
    """
    任意 OpenAI-兼容服务的兜底 adapter。
    公司 LLM 如果是 OpenAI 兼容协议,改 config 用这个即可,不必新写代码。
    """
    pass


# ============================================================================
# Anthropic Claude adapter
# ============================================================================

class ClaudeAdapter(LLMAdapter):
    """Anthropic /v1/messages — 协议与 OpenAI 不同。"""

    def call(self, prompt: str, system: Optional[str] = None,
             scenario_id: Optional[str] = None) -> LLMResponse:
        request_id = self._gen_request_id()
        api_key = self._get_api_key()

        payload = {
            'model': self.config['model'],
            'max_tokens': self.config.get('max_tokens', 4096),
            'temperature': self.config.get('temperature', 0.0),
            'messages': [{'role': 'user', 'content': prompt}],
        }
        if system:
            payload['system'] = system

        headers = {
            'x-api-key': api_key,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01',
        }
        headers.update(self.config.get('extra_headers', {}))

        start = time.time()
        resp_json = self._do_request_with_retry(
            'POST', self.config['api_base'], headers=headers, json=payload,
        )
        duration_ms = int((time.time() - start) * 1000)

        try:
            # Anthropic 返回 content 是 list[{type: text, text: ...}]
            content_blocks = resp_json['content']
            content = '\n'.join(b['text'] for b in content_blocks if b.get('type') == 'text')
            finish_reason = resp_json.get('stop_reason')
            usage = resp_json.get('usage', {})
            token_usage = {
                'in': usage.get('input_tokens', 0),
                'out': usage.get('output_tokens', 0),
                'total': usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
            }
        except (KeyError, IndexError, TypeError) as e:
            raise LLMAdapterError(
                f"Claude 响应格式异常: {e}, raw: {resp_json}"
            )

        response = LLMResponse(
            content=content, raw_response=resp_json,
            token_usage=token_usage, duration_ms=duration_ms,
            provider=self.provider_name, model=self.config['model'],
            request_id=request_id, finish_reason=finish_reason,
        )
        self._log_call(request_id, payload, response, scenario_id=scenario_id)
        return response


# ============================================================================
# Cline (公司内部 LLM) adapter — 部署期填充
# ============================================================================

class ClineAdapter(LLMAdapter):
    """
    公司 Cline LLM 接入位。

    部署时三种情况:
    (1) 公司 LLM 是 OpenAI 兼容协议:
        不必动此 adapter,改 llm_config.yaml 用 custom provider 即可。
    (2) 公司 LLM 是 Anthropic 兼容协议:
        改 config 用 claude provider 即可。
    (3) 公司 LLM 是私有协议:
        在下面实现 call() —— 1) 构造请求 2) 调用 endpoint 3) 解析响应
        4) 返回 LLMResponse(必须符合数据契约)
    """

    def call(self, prompt: str, system: Optional[str] = None,
             scenario_id: Optional[str] = None) -> LLMResponse:
        raise NotImplementedError(
            "ClineAdapter 未实现。公司部署 AI:\n"
            " 1) 如果公司 LLM 是 OpenAI/Anthropic 兼容,改 config 用 custom/claude provider\n"
            " 2) 如果是私有协议,实现本 adapter 的 call() 方法\n"
            " 详见 llm_adapter/README.md"
        )


# ============================================================================
# 工厂方法
# ============================================================================

_ADAPTERS = {
    'kimi': KimiAdapter,
    'claude': ClaudeAdapter,
    'openai': OpenAIAdapter,
    'cline': ClineAdapter,
    'custom': CustomAdapter,
}


def get_adapter(config_path: str = 'llm_config.yaml') -> LLMAdapter:
    """
    从配置文件读取 active_provider 并返回对应 adapter。
    
    Usage:
        adapter = get_adapter()
        response = adapter.call("修这个编译错误: ...")
        print(response.content)        # patch
        print(response.token_usage)    # {'in': ..., 'out': ..., 'total': ...}
    """
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    provider = cfg.get('active_provider')
    if not provider:
        raise LLMAdapterError("llm_config.yaml 缺 active_provider")

    if provider not in _ADAPTERS:
        raise LLMAdapterError(
            f"未知 provider '{provider}'. 支持: {list(_ADAPTERS.keys())}"
        )

    provider_cfg = cfg.get('providers', {}).get(provider)
    if not provider_cfg:
        raise LLMAdapterError(f"配置中缺 providers.{provider}")

    common_cfg = cfg.get('common', {})
    return _ADAPTERS[provider](provider, provider_cfg, common_cfg)


# ============================================================================
# 命令行入口(快速测试)
# ============================================================================

if __name__ == '__main__':
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'llm_config.yaml'
    adapter = get_adapter(config_path)
    print(f"Active provider: {adapter.provider_name}")
    print(f"Model: {adapter.config['model']}")
    print(f"测试调用 (say 'hello' 一下):")
    try:
        resp = adapter.call("Say hello in one word.")
        print(f"  Response: {resp.content[:200]}")
        print(f"  Tokens: in={resp.token_usage.get('in')} out={resp.token_usage.get('out')}")
        print(f"  Duration: {resp.duration_ms}ms")
        print(f"  Trace: {adapter.log_dir}/{resp.request_id}.json")
        print("OK")
    except LLMAdapterError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
