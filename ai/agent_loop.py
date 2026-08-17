import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai.context import AgentContext
from ai.llm_client import LLMClient, LLMResponse
from ai.skills.registry import SkillRegistry
from ai.tool_executor import ToolExecutor


@dataclass
class AgentResult:
    text: str
    session_id: str
    steps: int = 0
    trajectory: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True


class AgentLoop:
    """ReAct Agent 循环 — 四层记忆 + Function Calling。"""

    def __init__(
        self,
        ctx: AgentContext,
        llm: LLMClient,
        skills: SkillRegistry,
        include_browser: bool = False,
    ):
        self.ctx = ctx
        self.llm = llm
        self.skills = skills
        self.executor = ToolExecutor(ctx)
        self.include_browser = include_browser

    def run(self, user_message: str, session_id: Optional[str] = None) -> AgentResult:
        memory = self.ctx.memory
        sid = session_id or memory.start_session(title=user_message[:50])
        self.ctx.session_id = sid

        memory.append_working(sid, "user", user_message)
        context_block = memory.build_context_prompt(sid, user_message)
        system = self.skills.get_system_prompt()
        if context_block:
            system += f"\n\n# 记忆上下文\n{context_block}"

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system},
        ]
        for w in memory.get_working_context(sid):
            msg = {"role": w["role"], "content": w.get("content", "")}
            if w.get("tool_calls"):
                msg["tool_calls"] = w["tool_calls"]
            messages.append(msg)

        tools = self.executor.get_tools(include_browser=self.include_browser)
        steps = 0
        final_text = ""
        success = True

        while steps < self.ctx.max_steps:
            steps += 1
            resp: LLMResponse = self.llm.chat(messages, tools=tools)

            if resp.tool_calls:
                assistant_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": resp.content,
                    "tool_calls": resp.tool_calls,
                }
                messages.append(assistant_msg)
                memory.append_working(sid, "assistant", resp.content or "", resp.tool_calls)

                for tc in resp.tool_calls:
                    fn = tc["function"]
                    name = fn["name"]
                    args = ToolExecutor.parse_tool_arguments(fn.get("arguments", "{}"))
                    result = self.executor.execute(name, args)
                    if not result.get("success", True) and name != "validate_test_case":
                        success = False

                    result_str = json.dumps(result, ensure_ascii=False)
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc.get("id", name),
                        "content": result_str,
                    }
                    messages.append(tool_msg)
                    memory.append_working(sid, "tool", result_str)

                    if name == "validate_test_case" and result.get("valid"):
                        case = result.get("case", {})
                        staging = self.executor.execute("save_test_case_staging", {"case_dict": case})
                        if staging.get("success"):
                            memory.on_case_success(case)
                            final_text = f"用例校验通过并已保存 staging：{staging.get('path')}"
                            memory.save_episode(sid, final_text, self.ctx.trajectory, True)
                            return AgentResult(final_text, sid, steps, self.ctx.trajectory, True)

                continue

            final_text = resp.content or ""
            memory.append_working(sid, "assistant", final_text)
            break

        memory.save_episode(sid, final_text or user_message, self.ctx.trajectory, success)
        return AgentResult(final_text, sid, steps, self.ctx.trajectory, success)
