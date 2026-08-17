"""Framework Tools 测试。"""
import json
import os

from ai.tools import framework_tools

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFrameworkTools:
    def test_validate_test_case_valid(self, sample_login_case):
        r = framework_tools.validate_test_case(sample_login_case)
        assert r["valid"] is True
        assert r["errors"] == []

    def test_validate_test_case_missing_fields(self):
        r = framework_tools.validate_test_case({"id": "X"})
        assert r["valid"] is False
        assert len(r["errors"]) >= 5

    def test_save_test_case_staging(self, sample_login_case, tmp_path, monkeypatch):
        staging = str(tmp_path / "staging")
        monkeypatch.setattr(framework_tools, "STAGING_DIR", staging)
        r = framework_tools.save_test_case_staging(sample_login_case)
        assert r["success"] is True
        assert os.path.exists(r["path"])
        with open(r["path"], encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["id"] == "TC_TEST"

    def test_suggest_selector_from_dom(self):
        dom = [
            {"tag": "input", "id": "username", "name": "username", "text": ""},
            {"tag": "input", "id": "password", "name": "password", "text": ""},
            {"tag": "button", "id": "login-btn", "text": "登录"},
        ]
        r = framework_tools.suggest_selector(dom, "登录按钮")
        assert r["success"] is True
        assert r["selector"] in ("login-btn", "#login-btn", "login-btn")

    def test_suggest_selector_no_hallucination(self):
        r = framework_tools.suggest_selector([], "不存在的元素")
        assert r["success"] is False

    def test_get_config(self, ai_config):
        r = framework_tools.get_config(ai_config)
        assert r["success"] is True
        assert r["config"]["base_url"] == "http://localhost:5000"

    def test_load_test_cases(self):
        r = framework_tools.load_test_cases("data/test_data.json")
        assert r["success"] is True
        assert r["count"] > 0

    def test_memory_search(self, memory_manager):
        memory_manager.index_semantic("search selenium test", source="case")
        r = framework_tools.memory_search(memory_manager, "search")
        assert r["success"] is True
        assert len(r["result"]["chunks"]) >= 1
