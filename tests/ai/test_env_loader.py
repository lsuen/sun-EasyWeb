"""env_loader 模块测试。"""
import os

from utils.env_loader import apply_env_to_config, load_project_env, _load_env_fallback


class TestEnvLoader:
    def test_apply_env_overrides_llm(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "sk-test-key")
        monkeypatch.setenv("LLM_BASE_URL", "https://api.example.com/v1")
        monkeypatch.setenv("LLM_MODEL", "test-model")
        monkeypatch.setenv("LLM_ENABLED", "true")
        monkeypatch.setenv("LLM_MOCK", "false")

        config = apply_env_to_config({"llm": {"enabled": False, "model": "gpt-4o-mini"}})
        assert config["llm"]["api_key"] == "sk-test-key"
        assert config["llm"]["base_url"] == "https://api.example.com/v1"
        assert config["llm"]["model"] == "test-model"
        assert config["llm"]["enabled"] is True
        assert config["llm"]["mock"] is False

    def test_apply_env_dingtalk(self, monkeypatch):
        monkeypatch.setenv("DINGTALK_WEBHOOK", "https://example.com/hook")
        config = apply_env_to_config({})
        assert config["notify"]["dingtalk"]["webhook"] == "https://example.com/hook"

    def test_config_loader_merges_env(self, monkeypatch, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("LLM_API_KEY=sk-from-dotenv\nLLM_ENABLED=true\n", encoding="utf-8")
        _load_env_fallback(str(env_file))

        from utils.config_loader import ConfigLoader
        yaml_path = tmp_path / "settings.yaml"
        yaml_path.write_text("llm:\n  enabled: false\n  mock: false\n", encoding="utf-8")
        cfg = ConfigLoader(str(yaml_path)).config
        assert cfg["llm"]["api_key"] == "sk-from-dotenv"
        assert cfg["llm"]["enabled"] is True

    def test_llm_client_reads_merged_api_key(self, monkeypatch):
        from ai.llm_client import LLMClient
        client = LLMClient({"enabled": True, "mock": False, "api_key": "sk-merged"})
        assert client.api_key == "sk-merged"

    def test_apply_env_runtime_overrides(self, monkeypatch):
        monkeypatch.setenv("EASYWEB_BROWSER_PATH", "/opt/chrome/chrome")
        monkeypatch.setenv("EASYWEB_DRIVER_PATH", "/opt/chrome/chromedriver")
        monkeypatch.setenv("EASYWEB_WEBSITE_PATH", "/opt/site/app")
        monkeypatch.setenv("EASYWEB_BASE_URL", "https://app.example.com")
        monkeypatch.delenv("EASYWEB_HEADLESS", raising=False)

        config = apply_env_to_config({"browser_path": "old", "headless": False})
        assert config["browser_path"] == "/opt/chrome/chrome"
        assert config["driver_path"] == "/opt/chrome/chromedriver"
        assert config["website_path"] == "/opt/site/app"
        assert config["base_url"] == "https://app.example.com"
        assert config["headless"] is False

    def test_apply_env_headless(self, monkeypatch):
        monkeypatch.setenv("EASYWEB_HEADLESS", "true")
        config = apply_env_to_config({"headless": False})
        assert config["headless"] is True
