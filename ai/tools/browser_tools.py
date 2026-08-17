"""L1 浏览器 Tool 实现（需要 AgentContext.engine）。"""
from typing import Any, Dict, List


def _extract_elements(engine) -> List[Dict[str, Any]]:
    """从页面提取可交互元素（简化 DOM grounding）。"""
    elements = []
    script = """
    const nodes = document.querySelectorAll('input, button, a, select, textarea');
    return Array.from(nodes).slice(0, 50).map(el => ({
        tag: el.tagName.toLowerCase(),
        id: el.id || '',
        name: el.name || '',
        type: el.type || '',
        text: (el.innerText || el.value || '').trim().slice(0, 80),
        selector: el.id ? '#' + el.id : (el.name ? '[name="' + el.name + '"]' : el.tagName.toLowerCase())
    }));
    """
    try:
        raw = engine.execute_script(script)
        if isinstance(raw, list):
            elements = raw
    except Exception:
        pass
    return elements


def browser_open(engine, url: str) -> Dict[str, Any]:
    try:
        engine.open(url)
        return {"success": True, "url": url}
    except Exception as e:
        return {"success": False, "error": str(e)}


def browser_get_page_info(engine) -> Dict[str, Any]:
    try:
        return {
            "success": True,
            "title": engine.get_title(),
            "url": engine.get_current_url(),
            "elements": _extract_elements(engine),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def browser_click(engine, selector: str, by: str = "css") -> Dict[str, Any]:
    try:
        engine.click(selector, by=by)
        return {"success": True, "selector": selector}
    except Exception as e:
        return {"success": False, "error": str(e)}


def browser_input(engine, selector: str, text: str, by: str = "css") -> Dict[str, Any]:
    try:
        engine.input(selector, text, by=by)
        return {"success": True, "selector": selector}
    except Exception as e:
        return {"success": False, "error": str(e)}
