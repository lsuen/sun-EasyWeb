"""OpenAI 兼容 LLM 客户端，支持 mock 模式。"""
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    content: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    finish_reason: str = "stop"


class LLMClient:
    """OpenAI Chat Completions 兼容客户端。"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", False)
        self.mock = config.get("mock", False)
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-4o-mini")
        self.temperature = config.get("temperature", 0.2)
        self.max_tokens = config.get("max_tokens", 4096)
        # api_key 优先来自 .env（经 ConfigLoader 合并），其次环境变量名兜底
        env_name = config.get("api_key_env", "LLM_API_KEY")
        self.api_key = config.get("api_key") or os.environ.get(env_name, "")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
    ) -> LLMResponse:
        if self.mock or not self.enabled:
            return self._mock_response(messages, tools)
        if not self.api_key:
            raise RuntimeError(
                "LLM 未配置 API Key，请在项目根目录 .env 中设置 LLM_API_KEY，或启用 mock 模式"
            )
        return self._real_chat(messages, tools)

    def _real_chat(self, messages: List[Dict], tools: Optional[List[Dict]]) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError("请安装 openai: pip install openai>=1.0.0") from e

        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })
        return LLMResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
        )

    def _mock_response(self, messages: List[Dict], tools: Optional[List[Dict]]) -> LLMResponse:
        """Mock：根据用户意图返回预设 tool_call 或文本。"""
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content") or ""
                break

        if "登录" in last_user or "login" in last_user.lower() or "生成" in last_user or "用例" in last_user:
            case = {
                "id": "AI_TC001",
                "name": "AI生成-管理员登录",
                "type": "login",
                "url": "${base_url}/login",
                "value": "admin,123456",
                "username_selector": "#username",
                "password_selector": "#password",
                "login_btn_selector": "#login-btn",
                "result_selector": ".welcome",
                "expected_type": "text",
                "expected_value": "admin",
                "priority": "P1",
                "description": "AI Chat 自动生成的登录用例",
            }
            return LLMResponse(
                content=None,
                tool_calls=[{
                    "id": "mock_call_1",
                    "type": "function",
                    "function": {
                        "name": "validate_test_case",
                        "arguments": json.dumps({"case_dict": case}, ensure_ascii=False),
                    },
                }],
                finish_reason="tool_calls",
            )

        if "selector" in last_user.lower() or "定位" in last_user or "修复" in last_user:
            return LLMResponse(
                content=None,
                tool_calls=[{
                    "id": "mock_call_2",
                    "type": "function",
                    "function": {
                        "name": "suggest_selector",
                        "arguments": json.dumps({
                            "dom_elements": [
                                {"tag": "input", "id": "username", "name": "username", "text": ""},
                                {"tag": "button", "id": "login-btn", "text": "登录"},
                            ],
                            "intent": "登录按钮",
                        }, ensure_ascii=False),
                    },
                }],
                finish_reason="tool_calls",
            )

        return LLMResponse(
            content=f"[Mock LLM] 已收到：{last_user[:100]}。可尝试说「生成登录用例」或「帮我定位登录按钮」。",
            finish_reason="stop",
        )
