"""L2/L3 框架 Tool 实现（无 browser 依赖）。"""
import json
import os
import re
from typing import Any, Dict, List

from drivers.data_driver import DataDriver

REQUIRED_FIELDS = ["id", "name", "type", "url", "expected_type", "expected_value"]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGING_DIR = os.path.join(PROJECT_ROOT, "data", "ai", "staging")


def validate_test_case(case_dict: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    for field in REQUIRED_FIELDS:
        if not case_dict.get(field):
            errors.append(f"缺少必填字段: {field}")
    valid_types = {"search", "login", "nav", "click", "locator", "workflow"}
    if case_dict.get("type") and case_dict["type"] not in valid_types:
        errors.append(f"不支持的 type: {case_dict['type']}")
    return {"valid": len(errors) == 0, "errors": errors, "case": case_dict}


def save_test_case_staging(case_dict: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_test_case(case_dict)
    if not validation["valid"]:
        return {"success": False, "error": validation["errors"]}
    os.makedirs(STAGING_DIR, exist_ok=True)
    case_id = re.sub(r"[^\w\-]", "_", case_dict.get("id", "unknown"))
    path = os.path.join(STAGING_DIR, f"{case_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(case_dict, f, ensure_ascii=False, indent=2)
    return {"success": True, "path": path, "message": "已保存到 staging，需确认后合并到 data/"}


def load_test_cases(path: str) -> Dict[str, Any]:
    abs_path = path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)
    if not os.path.exists(abs_path):
        return {"success": False, "error": f"文件不存在: {path}"}
    driver = DataDriver(abs_path)
    data = driver.load()
    return {"success": True, "count": len(data), "cases": data}


def get_config(config: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["engine", "browser", "base_url", "headless", "timeout", "robust_mode"]
    return {"success": True, "config": {k: config.get(k) for k in keys}}


def suggest_selector(dom_elements: List[Dict], intent: str) -> Dict[str, Any]:
    """从真实 DOM 候选中推荐 selector，不编造。"""
    intent_lower = intent.lower()
    candidates = []
    for el in dom_elements:
        tag = (el.get("tag") or "").lower()
        el_id = el.get("id") or ""
        name = el.get("name") or ""
        text = (el.get("text") or "").strip()
        score = 0
        blob = f"{tag} {el_id} {name} {text}".lower()
        if "登录" in intent or "login" in intent_lower:
            if tag == "button" or tag == "input":
                score += 1
            if "login" in blob or "登录" in text:
                score += 3
        if "用户" in intent or "username" in intent_lower:
            if tag == "input" and ("user" in blob or "用户" in intent):
                score += 3
        if "密码" in intent or "password" in intent_lower:
            if tag == "input" and ("pass" in blob or "密码" in intent):
                score += 3
        if any(k in blob for k in intent_lower.split()):
            score += 2
        if score > 0:
            sel = el.get("selector") or (f"#{el_id}" if el_id else (f"[name='{name}']" if name else tag))
            by = "css"
            if el_id:
                by = "id"
                sel = el_id
            candidates.append({"selector": sel, "by": by, "score": score, "element": el})

    candidates.sort(key=lambda x: x["score"], reverse=True)
    if not candidates:
        return {
            "success": False,
            "error": "未在提供的 DOM 候选中找到匹配元素，请先用 browser_get_page_info 获取页面元素",
            "candidates": [],
        }
    best = candidates[0]
    return {
        "success": True,
        "selector": best["selector"],
        "by": best["by"],
        "candidates": candidates[:3],
        "intent": intent,
    }


def memory_search(memory, query: str) -> Dict[str, Any]:
    result = memory.rag_search(query)
    return {"success": True, "query": query, "result": result}
