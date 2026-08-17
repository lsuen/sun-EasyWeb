"""OpenAI Function Calling Tool Schema 定义。"""
from typing import List, Dict

FRAMEWORK_TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "validate_test_case",
            "description": "校验测试用例是否符合 Easy-Web 标准字段规范",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_dict": {
                        "type": "object",
                        "description": "测试用例字典，含 id/name/type/url/expected_type/expected_value 等",
                    }
                },
                "required": ["case_dict"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_test_case_staging",
            "description": "将通过校验的用例保存到 staging 目录（待用户确认，不直接写入正式 data/）",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_dict": {"type": "object", "description": "测试用例字典"},
                },
                "required": ["case_dict"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_test_cases",
            "description": "加载指定路径的测试用例 JSON/Excel",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对项目根的数据文件路径"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_config",
            "description": "获取当前框架配置（base_url、engine 等）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_selector",
            "description": "从 DOM 元素候选列表中推荐 selector（禁止编造不存在的元素）",
            "parameters": {
                "type": "object",
                "properties": {
                    "dom_elements": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "browser_get_page_info 返回的元素列表",
                    },
                    "intent": {"type": "string", "description": "目标元素描述，如「登录按钮」"},
                },
                "required": ["dom_elements", "intent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_search",
            "description": "检索四层记忆中的语义/情景/selector 信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
]

BROWSER_TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "browser_open",
            "description": "打开 URL",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_get_page_info",
            "description": "获取当前页面 title、url 及可交互元素列表（用于 grounding）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "点击元素",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "by": {"type": "string", "default": "css"},
                },
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_input",
            "description": "向输入框输入文本",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "text": {"type": "string"},
                    "by": {"type": "string", "default": "css"},
                },
                "required": ["selector", "text"],
            },
        },
    },
]


def get_all_tools(include_browser: bool = False) -> List[Dict]:
    tools = list(FRAMEWORK_TOOLS)
    if include_browser:
        tools.extend(BROWSER_TOOLS)
    return tools
