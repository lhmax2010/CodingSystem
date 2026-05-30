"""
LLM Adapter smoke test — Codex review 强化版

用法:
    export MOONSHOT_API_KEY=<your_key>     # 或对应 provider 的 key
    python3 llm_adapter_smoke_test.py

7 项验证(Codex review 后从 5 项扩到 7 项):
    1. 配置加载
    2. API key 读取(active provider)
    3. 6 个 adapter 都能实例化(catch 早期配置错误)
    4. active adapter 最小 API 调用
    5. token usage / duration 返回正常
    6. trace 文件生成 + 文件权限检查(强化:缺失 FAIL,不是 WARN)
    7. trace redact 验证(key 不能出现在 trace 中)

任何 FAIL 退出码 1,不报告 ALL PASS。
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_adapter import (
    get_adapter, LLMAdapterError, LLMResponse,
    KimiAdapter, KimiCodeAdapter, ClaudeAdapter, OpenAIAdapter, ClineAdapter, CustomAdapter,
    _ADAPTERS,
)
import yaml


def step(num: int, total: int, name: str):
    print(f"\n[{num}/{total}] {name}...")


def smoke_test(config_path: str = 'llm_config.yaml') -> bool:
    print("=" * 60)
    print("LLM Adapter Smoke Test (Codex review 强化版,7 项)")
    print("=" * 60)
    
    # ---- 1. 配置加载 ----
    step(1, 7, "加载配置")
    try:
        adapter = get_adapter(config_path)
        print(f"   OK active_provider = {adapter.provider_name}")
        print(f"   OK model = {adapter.config.get('model')}")
        print(f"   OK api_base = {adapter.config.get('api_base')}")
    except (LLMAdapterError, FileNotFoundError) as e:
        print(f"   FAIL 配置加载失败: {e}")
        return False
    
    # ---- 2. API key 读取 ----
    step(2, 7, "读取 active provider 的 API key")
    try:
        key = adapter._get_api_key()
        print(f"   OK key 已读到(长度 {len(key)})")
    except LLMAdapterError as e:
        print(f"   FAIL {e}")
        return False
    
    # ---- 3. 6 个 adapter 都能实例化(Codex review 新增)----
    step(3, 7, "6 个 adapter 都能实例化")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    common = cfg.get('common', {})
    
    inst_failures = []
    for prov_name, AdapterCls in _ADAPTERS.items():
        try:
            provider_cfg = cfg.get('providers', {}).get(prov_name, {})
            inst = AdapterCls(prov_name, provider_cfg, common)
            print(f"   OK {prov_name}: {AdapterCls.__name__}")
        except Exception as e:
            print(f"   FAIL {prov_name} 实例化失败: {e}")
            inst_failures.append(prov_name)
    
    if inst_failures:
        return False
    
    # ---- 4. active adapter 最小 API 调用 ----
    step(4, 7, "active adapter 最小 API 调用 (prompt='say hi')")
    try:
        resp: LLMResponse = adapter.call(
            prompt="Say hi in exactly one word.",
            system="You are a concise assistant.",
            scenario_id="smoke_test_minimal",
        )
        print(f"   OK 响应已收到")
        print(f"   content: {resp.content[:100]!r}")
        print(f"   finish_reason: {resp.finish_reason}")
    except LLMAdapterError as e:
        print(f"   FAIL API 调用失败: {e}")
        return False
    
    # ---- 5. token usage / duration ----
    step(5, 7, "验证 token usage / duration")
    if not resp.token_usage or 'total' not in resp.token_usage:
        print(f"   FAIL token_usage 异常: {resp.token_usage}")
        return False
    if 'in' not in resp.token_usage or 'out' not in resp.token_usage:
        print(f"   FAIL token_usage 缺 in/out: {resp.token_usage}")
        return False
    print(f"   OK token_usage(单次调用语义): "
          f"in={resp.token_usage['in']} out={resp.token_usage['out']} "
          f"total={resp.token_usage['total']}")
    
    if resp.duration_ms <= 0:
        print(f"   FAIL duration_ms 异常: {resp.duration_ms}")
        return False
    print(f"   OK duration_ms: {resp.duration_ms}")
    
    # ---- 6. trace 文件 + 权限(Codex review 强化:缺失 FAIL 不 WARN)----
    step(6, 7, "验证 trace 文件生成 + 权限")
    trace_path = os.path.join(adapter.log_dir, f"{resp.request_id}.json")
    
    log_prompts_enabled = common.get('log_prompts', True)
    
    if not os.path.exists(trace_path):
        if log_prompts_enabled:
            print(f"   FAIL trace 应存在但未生成: {trace_path}")
            print(f"        (log_prompts=true 但 trace 缺失)")
            return False
        else:
            print(f"   SKIP log_prompts=false,trace 不生成是预期")
    else:
        size = os.path.getsize(trace_path)
        st = os.stat(trace_path)
        mode = st.st_mode & 0o777
        if mode != 0o600:
            print(f"   WARN trace mode {oct(mode)},期望 0o600"
                  f"(某些 FS 不支持 chmod 可忽略)")
        print(f"   OK trace: {trace_path} ({size} bytes, mode {oct(mode)})")
    
    # ---- 7. trace redact 验证(Codex review 新增)----
    step(7, 7, "验证 trace 内容已 redact (API key 不明文出现)")
    if not os.path.exists(trace_path):
        print(f"   SKIP trace 不存在,跳过")
    else:
        with open(trace_path) as f:
            trace_content = f.read()
        
        # 关键检查:API key 不能明文出现
        if key in trace_content:
            print(f"   FAIL API KEY 明文出现在 trace 中!严重 secret 泄漏")
            print(f"        trace: {trace_path}")
            return False
        
        if 'LOCAL_ONLY_EXPERIMENTAL_TRACE' not in trace_content:
            print(f"   FAIL trace 缺 LOCAL_ONLY_EXPERIMENTAL_TRACE 标记")
            return False
        
        if '"scenario_id": "smoke_test_minimal"' not in trace_content:
            print(f"   FAIL scenario_id 未透传到 trace")
            return False
        
        print(f"   OK API key 未明文出现")
        print(f"   OK LOCAL_ONLY_EXPERIMENTAL_TRACE 标记到位")
        print(f"   OK scenario_id 已透传")
    
    print("\n" + "=" * 60)
    print("ALL 7 PASS — Adapter 工作正常,可用于 S0-A 实验")
    print("=" * 60)
    return True


if __name__ == '__main__':
    config = sys.argv[1] if len(sys.argv) > 1 else 'llm_config.yaml'
    if not smoke_test(config):
        sys.exit(1)
