"""SQLite 持久化 — 四层记忆数据存储。"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


class MemoryStore:
    """四层记忆的 SQLite 后端。"""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        title TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS working_buffer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT,
        tool_calls TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    );

    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        summary TEXT,
        trajectory_json TEXT,
        success INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS semantic_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        content TEXT NOT NULL,
        metadata_json TEXT,
        weight REAL DEFAULT 1.0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS selector_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url_pattern TEXT NOT NULL,
        element_role TEXT NOT NULL,
        selector TEXT NOT NULL,
        by_type TEXT DEFAULT 'css',
        success_count INTEGER DEFAULT 0,
        fail_count INTEGER DEFAULT 0,
        stale INTEGER DEFAULT 0,
        updated_at TEXT NOT NULL,
        UNIQUE(url_pattern, element_role, selector)
    );

    CREATE TABLE IF NOT EXISTS skill_candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_name TEXT NOT NULL,
        description TEXT,
        success_count INTEGER DEFAULT 0,
        confidence REAL DEFAULT 0.0,
        promoted INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(self.SCHEMA)

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat() + "Z"

    # --- sessions ---
    def create_session(self, session_id: str, title: str = "") -> None:
        now = self._now()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, title, now, now),
            )

    def touch_session(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (self._now(), session_id),
            )

    # --- L1 working ---
    def append_working(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict]] = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO working_buffer (session_id, role, content, tool_calls, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    session_id,
                    role,
                    content,
                    json.dumps(tool_calls or [], ensure_ascii=False),
                    self._now(),
                ),
            )
        self.touch_session(session_id)

    def get_working(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content, tool_calls, created_at FROM working_buffer "
                "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        result = []
        for row in reversed(rows):
            item = {"role": row["role"], "content": row["content"] or ""}
            if row["tool_calls"]:
                item["tool_calls"] = json.loads(row["tool_calls"])
            result.append(item)
        return result

    def clear_working(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM working_buffer WHERE session_id = ?", (session_id,))

    # --- L2 episodic ---
    def save_episode(
        self,
        session_id: str,
        summary: str,
        trajectory: List[Dict],
        success: bool,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO episodes (session_id, summary, trajectory_json, success, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    session_id,
                    summary,
                    json.dumps(trajectory, ensure_ascii=False),
                    1 if success else 0,
                    self._now(),
                ),
            )
            return cur.lastrowid

    def find_episodes(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        like = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT summary, trajectory_json, success, created_at FROM episodes "
                "WHERE summary LIKE ? ORDER BY id DESC LIMIT ?",
                (like, top_k),
            ).fetchall()
        return [dict(r) for r in rows]

    # --- L3 semantic ---
    def add_chunk(
        self,
        content: str,
        source: str = "",
        metadata: Optional[Dict] = None,
        weight: float = 1.0,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO semantic_chunks (source, content, metadata_json, weight, created_at) VALUES (?, ?, ?, ?, ?)",
                (source, content, json.dumps(metadata or {}), weight, self._now()),
            )
            return cur.lastrowid

    def search_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        like = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT source, content, metadata_json, weight FROM semantic_chunks "
                "WHERE content LIKE ? ORDER BY weight DESC, id DESC LIMIT ?",
                (like, top_k),
            ).fetchall()
        return [dict(r) for r in rows]

    def upsert_selector(
        self,
        url_pattern: str,
        element_role: str,
        selector: str,
        by_type: str = "css",
        success: bool = True,
    ) -> None:
        now = self._now()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, success_count, fail_count FROM selector_registry "
                "WHERE url_pattern = ? AND element_role = ? AND selector = ?",
                (url_pattern, element_role, selector),
            ).fetchone()
            if row:
                if success:
                    conn.execute(
                        "UPDATE selector_registry SET success_count = success_count + 1, stale = 0, updated_at = ? WHERE id = ?",
                        (now, row["id"]),
                    )
                else:
                    conn.execute(
                        "UPDATE selector_registry SET fail_count = fail_count + 1, updated_at = ? WHERE id = ?",
                        (now, row["id"]),
                    )
            else:
                sc = 1 if success else 0
                fc = 0 if success else 1
                conn.execute(
                    "INSERT INTO selector_registry "
                    "(url_pattern, element_role, selector, by_type, success_count, fail_count, stale, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                    (url_pattern, element_role, selector, by_type, sc, fc, now),
                )

    def get_selectors(self, url_pattern: str, element_role: str = "") -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if element_role:
                rows = conn.execute(
                    "SELECT * FROM selector_registry WHERE url_pattern LIKE ? AND element_role = ? AND stale = 0 "
                    "ORDER BY success_count DESC",
                    (f"%{url_pattern}%", element_role),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM selector_registry WHERE url_pattern LIKE ? AND stale = 0 "
                    "ORDER BY success_count DESC",
                    (f"%{url_pattern}%",),
                ).fetchall()
        return [dict(r) for r in rows]

    def mark_selector_stale(self, url_pattern: str, selector: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE selector_registry SET stale = 1, updated_at = ? WHERE url_pattern LIKE ? AND selector = ?",
                (self._now(), f"%{url_pattern}%", selector),
            )

    # --- L4 procedural candidates ---
    def record_skill_candidate(
        self,
        pattern_name: str,
        description: str = "",
        success: bool = True,
    ) -> None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, success_count FROM skill_candidates WHERE pattern_name = ? AND promoted = 0",
                (pattern_name,),
            ).fetchone()
            if row and success:
                conn.execute(
                    "UPDATE skill_candidates SET success_count = success_count + 1 WHERE id = ?",
                    (row["id"],),
                )
            elif not row:
                conn.execute(
                    "INSERT INTO skill_candidates (pattern_name, description, success_count, confidence, promoted, created_at) "
                    "VALUES (?, ?, ?, ?, 0, ?)",
                    (pattern_name, description, 1 if success else 0, 0.5, self._now()),
                )

    def get_skill_candidates(self, min_success: int = 3) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM skill_candidates WHERE promoted = 0 AND success_count >= ? ORDER BY success_count DESC",
                (min_success,),
            ).fetchall()
        return [dict(r) for r in rows]
