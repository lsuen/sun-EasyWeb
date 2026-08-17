"""Tool 分发执行器 — Function Calling 落地。"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai.context import AgentContext
from ai.tools import framework_tools, browser_tools
from ai.tools.schemas import get_all_tools

LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "logs",
    "ai",
)


class ToolExecutor:
    """注册并执行 Agent Tools。"""

    BROWSER_TOOL_NAMES = {
        "browser_open",
        "browser_get_page_info",
        "browser_click",
        "browser_input",
    }

    def __init__(self, ctx: AgentContext):
        self.ctx = ctx
        os.makedirs(LOG_DIR, exist_ok=True)

    def get_tools(self, include_browser: bool = False) -> List[Dict]:
        return get_all_tools(include_browser=include_browser)

    def execute(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        mode = self.ctx.mode
        if name in self.BROWSER_TOOL_NAMES and mode == "assist" and not self.ctx.engine:
            return {"success": False, "error": f"assist 模式未启用 browser，无法调用 {name}"}
        if name in self.BROWSER_TOOL_NAMES and not self.ctx.engine:
            return {"success": False, "error": "未初始化 browser engine，请使用 --with-browser"}

        try:
            result = self._dispatch(name, arguments)
        except Exception as e:
            result = {"success": False, "error": str(e)}

        self.ctx.record_step(name, arguments, result)
        self._log_tool_call(name, arguments, result)
        return result

    def _dispatch(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "validate_test_case":
            return framework_tools.validate_test_case(arguments.get("case_dict", arguments))
        if name == "save_test_case_staging":
            return framework_tools.save_test_case_staging(arguments.get("case_dict", arguments))
        if name == "load_test_cases":
            return framework_tools.load_test_cases(arguments["path"])
        if name == "get_config":
            return framework_tools.get_config(self.ctx.config)
        if name == "suggest_selector":
            return framework_tools.suggest_selector(
                arguments.get("dom_elements", []),
                arguments.get("intent", ""),
            )
        if name == "memory_search":
            return framework_tools.memory_search(self.ctx.memory, arguments.get("query", ""))

        eng = self.ctx.engine
        if name == "browser_open":
            return browser_tools.browser_open(eng, arguments["url"])
        if name == "browser_get_page_info":
            return browser_tools.browser_get_page_info(eng)
        if name == "browser_click":
            return browser_tools.browser_click(eng, arguments["selector"], arguments.get("by", "css"))
        if name == "browser_input":
            return browser_tools.browser_input(
                eng, arguments["selector"], arguments["text"], arguments.get("by", "css")
            )

        return {"success": False, "error": f"未知 tool: {name}"}

    def _log_tool_call(self, name: str, args: Dict, result: Dict) -> None:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(LOG_DIR, f"tool_{ts}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"tool": name, "args": args, "result": result}, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    @staticmethod
    def parse_tool_arguments(raw: str) -> Dict[str, Any]:
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
