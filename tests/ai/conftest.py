"""AI 模块测试 fixtures。"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)


@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test_knowledge.db")


@pytest.fixture
def memory_manager(tmp_db):
    from ai.memory.manager import MemoryManager
    return MemoryManager(tmp_db)


@pytest.fixture
def sample_login_case():
    return {
        "id": "TC_TEST",
        "name": "测试登录",
        "type": "login",
        "url": "${base_url}/login",
        "value": "admin,123456",
        "username_selector": "#username",
        "password_selector": "#password",
        "login_btn_selector": "#login-btn",
        "expected_type": "text",
        "expected_value": "admin",
    }


@pytest.fixture
def ai_config(tmp_db):
    return {
        "engine": "selenium",
        "base_url": "http://localhost:5000",
        "llm": {"enabled": True, "mock": True},
        "agent": {"mode": "hybrid", "max_steps": 10},
        "memory": {"db_path": tmp_db},
        "skills": {"enabled": ["generate_case", "diagnose_failure", "heal_selector"]},
    }
