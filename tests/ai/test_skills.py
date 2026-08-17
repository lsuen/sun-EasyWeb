"""Skill Registry 测试。"""
from ai.skills.registry import SkillRegistry


class TestSkillRegistry:
    def test_load_builtin_skills(self):
        reg = SkillRegistry(enabled=["generate_case", "diagnose_failure", "heal_selector"])
        assert len(reg.skills) == 3
        names = {s["name"] for s in reg.skills}
        assert "generate_case" in names
        assert "heal_selector" in names

    def test_system_prompt_contains_rules(self):
        reg = SkillRegistry(enabled=["generate_case"])
        prompt = reg.get_system_prompt()
        assert "Easy-Web" in prompt
        assert "save_test_case_staging" in prompt
        assert "generate_case" in prompt

    def test_match_triggers(self):
        reg = SkillRegistry(enabled=["generate_case", "heal_selector"])
        matched = reg.match_triggers("生成用例")
        assert len(matched) >= 1

    def test_get_tool_names(self):
        reg = SkillRegistry(enabled=["generate_case", "heal_selector"])
        tools = reg.get_tool_names()
        assert "validate_test_case" in tools
        assert "suggest_selector" in tools
