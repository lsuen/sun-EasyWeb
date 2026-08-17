"""四层工程级记忆管理器。"""
import json
import uuid
from typing import Any, Dict, List, Optional

from ai.memory.store import MemoryStore


class MemoryManager:
    """
    L1 Working  — 当前会话上下文
    L2 Episodic — 历史 session 轨迹
    L3 Semantic — RAG chunks + selector_registry
    L4 Procedural — skill_candidates（晋升到 skills/）
    """

    def __init__(self, db_path: str):
        self.store = MemoryStore(db_path)

    def start_session(self, title: str = "", session_id: Optional[str] = None) -> str:
        sid = session_id or str(uuid.uuid4())
        self.store.create_session(sid, title)
        return sid

    # --- L1 ---
    def append_working(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict]] = None,
    ) -> None:
        self.store.append_working(session_id, role, content, tool_calls)

    def get_working_context(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self.store.get_working(session_id, limit)

    def build_context_prompt(self, session_id: str, user_query: str, top_k: int = 5) -> str:
        """合并 L1 + L3 retrieve，供 Agent Loop 注入。"""
        parts = []
        episodes = self.store.find_episodes(user_query, top_k=2)
        if episodes:
            parts.append("## 相似历史情景 (L2)")
            for ep in episodes:
                parts.append(f"- {ep['summary']} (success={ep['success']})")
        chunks = self.store.search_chunks(user_query, top_k=top_k)
        if chunks:
            parts.append("## 语义记忆检索 (L3)")
            for c in chunks:
                parts.append(f"- [{c['source']}] {c['content'][:200]}")
        selectors = self.store.get_selectors(user_query)
        if selectors:
            parts.append("## 已知 Selector (L3)")
            for s in selectors[:5]:
                parts.append(
                    f"- {s['element_role']}: {s['selector']} (by={s['by_type']}, ok={s['success_count']})"
                )
        return "\n".join(parts)

    # --- L2 ---
    def save_episode(
        self,
        session_id: str,
        summary: str,
        trajectory: List[Dict],
        success: bool,
    ) -> int:
        return self.store.save_episode(session_id, summary, trajectory, success)

    def find_similar_episodes(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.store.find_episodes(query, top_k)

    # --- L3 ---
    def index_semantic(self, content: str, source: str = "", metadata: Optional[Dict] = None) -> int:
        return self.store.add_chunk(content, source, metadata)

    def rag_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        chunks = self.store.search_chunks(query, top_k)
        selectors = self.store.get_selectors(query)
        return {"chunks": chunks, "selectors": selectors}

    def upsert_selector(
        self,
        url_pattern: str,
        element_role: str,
        selector: str,
        by_type: str = "css",
        success: bool = True,
    ) -> None:
        self.store.upsert_selector(url_pattern, element_role, selector, by_type, success)

    def mark_selector_stale(self, url_pattern: str, selector: str) -> None:
        self.store.mark_selector_stale(url_pattern, selector)

    # --- L4 ---
    def record_skill_candidate(self, pattern_name: str, description: str = "", success: bool = True) -> None:
        self.store.record_skill_candidate(pattern_name, description, success)

    def get_skill_candidates(self, min_success: int = 3) -> List[Dict[str, Any]]:
        return self.store.get_skill_candidates(min_success)

    def on_case_success(self, case: Dict[str, Any], url: str = "") -> None:
        """用例成功后写入 L3 + L4 候选。"""
        summary = f"{case.get('type')}:{case.get('name')} @ {url or case.get('url', '')}"
        self.index_semantic(json_dumps_safe(case), source="test_case", metadata={"id": case.get("id")})
        if case.get("selector"):
            self.upsert_selector(url or case.get("url", ""), case.get("type", "element"), case["selector"])
        self.record_skill_candidate(f"case_{case.get('type')}", summary, success=True)


def json_dumps_safe(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)
