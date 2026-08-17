"""notify 模块测试。"""
from ai.notify import build_report_markdown


class TestNotify:
    def test_markdown_contains_keywords(self):
        text = build_report_markdown("feat/ai-chat-memory", 10, 10, ["memory", "tools"])
        assert "通知" in text
        assert "报告" in text
        assert "全部通过" in text

    def test_markdown_branch(self):
        text = build_report_markdown("feat/ai-chat-memory", 5, 5, [])
        assert "feat/ai-chat-memory" in text
