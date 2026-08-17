"""Agent Loop 集成测试（mock LLM）。"""
from ai.agent_loop import AgentLoop
from ai.context import AgentContext
from ai.llm_client import LLMClient
from ai.skills.registry import SkillRegistry
from ai.tool_executor import ToolExecutor


class TestAgentLoop:
    def test_mock_generate_login_case(self, memory_manager, ai_config, tmp_path, monkeypatch):
        from ai.tools import framework_tools
        staging = str(tmp_path / "staging")
        monkeypatch.setattr(framework_tools, "STAGING_DIR", staging)

        llm = LLMClient({"enabled": True, "mock": True})
        skills = SkillRegistry(enabled=ai_config["skills"]["enabled"])
        ctx = AgentContext(config=ai_config, memory=memory_manager, mode="hybrid")
        loop = AgentLoop(ctx, llm, skills, include_browser=False)

        result = loop.run("帮我生成一个登录用例")
        assert result.success is True
        assert "staging" in result.text.lower() or "TC" in result.text
        assert result.steps >= 1
        assert len(result.trajectory) >= 1

    def test_tool_executor_validate(self, memory_manager, ai_config):
        ctx = AgentContext(config=ai_config, memory=memory_manager)
        ex = ToolExecutor(ctx)
        r = ex.execute("validate_test_case", {
            "case_dict": {
                "id": "T1", "name": "n", "type": "click",
                "url": "http://x", "expected_type": "title", "expected_value": "x",
            }
        })
        assert r["valid"] is True

    def test_mock_suggest_selector_flow(self, memory_manager, ai_config):
        llm = LLMClient({"enabled": True, "mock": True})
        skills = SkillRegistry(enabled=["heal_selector"])
        ctx = AgentContext(config=ai_config, memory=memory_manager)
        loop = AgentLoop(ctx, llm, skills)
        result = loop.run("帮我定位登录按钮 selector")
        assert result.steps >= 1

    def test_llm_mock_text_response(self):
        llm = LLMClient({"enabled": True, "mock": True})
        r = llm.chat([{"role": "user", "content": "你好"}])
        assert r.content is not None
        assert "Mock" in r.content
