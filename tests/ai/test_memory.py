"""四层记忆模块测试。"""
from ai.memory.manager import MemoryManager


class TestMemoryFourLayers:
    def test_l1_working_buffer(self, memory_manager):
        sid = memory_manager.start_session("test")
        memory_manager.append_working(sid, "user", "hello")
        memory_manager.append_working(sid, "assistant", "hi")
        ctx = memory_manager.get_working_context(sid)
        assert len(ctx) == 2
        assert ctx[0]["role"] == "user"

    def test_l2_episode(self, memory_manager):
        sid = memory_manager.start_session("ep")
        eid = memory_manager.save_episode(sid, "登录用例修复", [{"tool": "heal"}], True)
        assert eid > 0
        found = memory_manager.find_similar_episodes("登录")
        assert len(found) >= 1

    def test_l3_semantic_and_selector(self, memory_manager):
        memory_manager.index_semantic("login case admin", source="doc")
        memory_manager.upsert_selector("localhost/login", "login_btn", "#login-btn", success=True)
        memory_manager.upsert_selector("localhost/login", "login_btn", "#login-btn", success=True)
        result = memory_manager.rag_search("login")
        assert len(result["chunks"]) >= 1
        assert result["selectors"][0]["success_count"] == 2

    def test_l3_stale_selector(self, memory_manager):
        memory_manager.upsert_selector("localhost", "btn", "#old", success=True)
        memory_manager.mark_selector_stale("localhost", "#old")
        sels = memory_manager.store.get_selectors("localhost")
        assert all(s["stale"] == 1 for s in sels if s["selector"] == "#old")

    def test_l4_skill_candidate(self, memory_manager):
        memory_manager.record_skill_candidate("case_login", "登录模式", success=True)
        memory_manager.record_skill_candidate("case_login", "登录模式", success=True)
        memory_manager.record_skill_candidate("case_login", "登录模式", success=True)
        cands = memory_manager.get_skill_candidates(min_success=3)
        assert any(c["pattern_name"] == "case_login" for c in cands)

    def test_on_case_success(self, memory_manager, sample_login_case):
        memory_manager.on_case_success(sample_login_case, "http://localhost:5000/login")
        chunks = memory_manager.store.search_chunks("TC_TEST")
        assert len(chunks) >= 1

    def test_build_context_prompt(self, memory_manager):
        sid = memory_manager.start_session("ctx")
        memory_manager.index_semantic("workflow 多步骤", source="test")
        memory_manager.save_episode(sid, "workflow 测试", [], True)
        prompt = memory_manager.build_context_prompt(sid, "workflow")
        assert "L2" in prompt or "L3" in prompt or "workflow" in prompt
