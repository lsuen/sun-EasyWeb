"""钉钉机器人通知 — 测试报告推送。"""
import json
import os
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional


DEFAULT_WEBHOOK = (
    "https://oapi.dingtalk.com/robot/send"
    "?access_token=80002e7730e7e2ab3da45a23537d46c9ff317e1b9a5def9c174922b7f85bea4f"
)


def build_report_markdown(
    branch: str,
    passed: int,
    total: int,
    modules: List[str],
    extra: str = "",
) -> str:
    """构建含关键词「通知」「报告」的 Markdown 正文。"""
    status_label = "全部通过" if passed == total else "部分失败"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "## 通知：Easy-Web AI 模块测试报告",
        "",
        "---",
        "",
        "### 测试结果报告",
        "",
        f"- **状态**：{status_label}",
        f"- **分支**：`{branch}`",
        f"- **通过**：{passed}/{total}",
        f"- **时间**：{now}",
        "",
        "### 交付模块",
        "",
    ]
    for m in modules:
        lines.append(f"- {m}")
    lines.extend([
        "",
        "### 能力摘要",
        "",
        "- Function Calling + Agent Loop",
        "- 四层工程级记忆（SQLite）",
        "- Skill 可插拔（generate / diagnose / heal）",
        "- Chat 模式（`python -m ai.chat --mock`）",
        "",
        "---",
        "",
        "> Easy-Web AI 扩展层 MVP 落地完成",
    ])
    if extra:
        lines.extend(["", extra])
    return "\n".join(lines)


def send_dingtalk_markdown(
    text: str,
    title: str = "通知",
    webhook: Optional[str] = None,
    at_all: bool = False,
) -> Dict[str, Any]:
    """发送钉钉 markdown 消息。"""
    from utils.env_loader import load_project_env
    load_project_env()
    url = webhook or os.environ.get("DINGTALK_WEBHOOK", DEFAULT_WEBHOOK)
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text,
        },
        "at": {"isAtAll": at_all},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def notify_test_report(
    branch: str,
    passed: int,
    total: int,
    modules: Optional[List[str]] = None,
    webhook: Optional[str] = None,
) -> Dict[str, Any]:
    modules = modules or [
        "ai/memory — 四层记忆",
        "ai/tools — Function Calling",
        "ai/skills — Skill Registry",
        "ai/agent_loop — ReAct 循环",
        "ai/chat — Chat CLI",
    ]
    text = build_report_markdown(branch, passed, total, modules)
    return send_dingtalk_markdown(text, title="通知", webhook=webhook)
