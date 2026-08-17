"""Skill 注册表 — L4 程序记忆加载与合并。"""
import os
import re
from typing import Any, Dict, List, Optional

SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class SkillRegistry:
    """扫描 ai/skills/*/SKILL.md，合并 tools 与 system prompt。"""

    def __init__(self, enabled: Optional[List[str]] = None):
        self.enabled_names = set(enabled or [])
        self.skills: List[Dict[str, Any]] = []
        self._load_all()

    def _load_all(self) -> None:
        for name in os.listdir(SKILLS_DIR):
            skill_dir = os.path.join(SKILLS_DIR, name)
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if not os.path.isdir(skill_dir) or not os.path.exists(skill_md):
                continue
            meta, body = self._parse_skill_md(skill_md)
            meta["name"] = meta.get("name", name)
            meta["body"] = body.strip()
            if self.enabled_names and meta["name"] not in self.enabled_names:
                meta["enabled"] = False
            else:
                meta.setdefault("enabled", True)
            if meta.get("enabled", True):
                self.skills.append(meta)

    @staticmethod
    def _parse_skill_md(path: str) -> tuple:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                meta = SkillRegistry._parse_frontmatter(parts[1])
                return meta, parts[2]
        return {}, content

    @staticmethod
    def _parse_frontmatter(text: str) -> Dict[str, Any]:
        try:
            import yaml
            data = yaml.safe_load(text.strip())
            return data if isinstance(data, dict) else {}
        except Exception:
            meta: Dict[str, Any] = {}
            for line in text.strip().splitlines():
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if val.startswith("[") and val.endswith("]"):
                    items = re.findall(r"[\w_\u4e00-\u9fff]+", val)
                    meta[key] = items
                elif val.lower() in ("true", "false"):
                    meta[key] = val.lower() == "true"
                else:
                    meta[key] = val
            return meta

    def get_system_prompt(self) -> str:
        parts = [
            "你是 Easy-Web 测试助手，帮助用户生成/校验/修复 Web 自动化测试用例。",
            "规则：selector 必须来自 browser_get_page_info 或 suggest_selector，禁止编造。",
            "用例必须符合标准字段：id, name, type, url, expected_type, expected_value。",
            "保存用例使用 save_test_case_staging，不直接写 data/。",
        ]
        for s in self.skills:
            parts.append(f"\n## Skill: {s['name']}\n{s.get('body', '')}")
        return "\n".join(parts)

    def get_tool_names(self) -> List[str]:
        names = set()
        for s in self.skills:
            for t in s.get("tools", []):
                names.add(t)
        return list(names)

    def match_triggers(self, event: str) -> List[Dict[str, Any]]:
        matched = []
        for s in self.skills:
            triggers = s.get("triggers", [])
            if event in triggers or any(event in t for t in triggers):
                matched.append(s)
        return matched
