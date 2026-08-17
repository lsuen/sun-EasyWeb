"""Chat REPL — 本地辅助测试入口。"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_loader import ConfigLoader
from ai.context import AgentContext
from ai.llm_client import LLMClient
from ai.memory.manager import MemoryManager
from ai.skills.registry import SkillRegistry
from ai.agent_loop import AgentLoop


def _load_ai_config(config_path: str = "config/settings.yaml") -> dict:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = config_path if os.path.isabs(config_path) else os.path.join(root, config_path)
    return ConfigLoader(path).config


def run_chat(
    message: str = "",
    mock: bool = False,
    session_id: str = "",
    config_path: str = "config/settings.yaml",
    with_browser: bool = False,
) -> str:
    config = _load_ai_config(config_path)
    llm_cfg = dict(config.get("llm", {}))
    if mock:
        llm_cfg["mock"] = True
        llm_cfg["enabled"] = True

    mem_cfg = config.get("memory", {})
    db_path = mem_cfg.get("db_path", "data/ai/knowledge.db")
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path)

    memory = MemoryManager(db_path)
    llm = LLMClient(llm_cfg)
    skills_cfg = config.get("skills", {})
    skills = SkillRegistry(enabled=skills_cfg.get("enabled"))

    engine = None
    if with_browser:
        from core.engine import Engine
        engine = Engine.get_engine(config)
        engine.start()

    ctx = AgentContext(
        config=config,
        memory=memory,
        engine=engine,
        mode=config.get("agent", {}).get("mode", "hybrid"),
    )
    loop = AgentLoop(ctx, llm, skills, include_browser=with_browser)

    try:
        if message:
            result = loop.run(message, session_id or None)
            return result.text

        print("Easy-Web AI Chat（输入 quit 退出）")
        sid = session_id or memory.start_session("interactive")
        print(f"Session: {sid}\n")
        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见。")
                break
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("再见。")
                break
            result = loop.run(user_input, sid)
            print(result.text)
            print(f"[steps={result.steps} success={result.success}]\n")
        return ""
    finally:
        if engine:
            try:
                engine.quit()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="Easy-Web AI Chat 模式")
    parser.add_argument("message", nargs="?", default="", help="单次指令（省略则进入 REPL）")
    parser.add_argument("--mock", action="store_true", help="Mock LLM，无需 API Key")
    parser.add_argument("--session", default="", help="续聊 session ID")
    parser.add_argument("-c", "--config", default="config/settings.yaml")
    parser.add_argument("--with-browser", action="store_true", help="启动浏览器（L1 tools）")
    args = parser.parse_args()

    text = run_chat(
        message=args.message,
        mock=args.mock,
        session_id=args.session,
        config_path=args.config,
        with_browser=args.with_browser,
    )
    if text:
        print(text)


if __name__ == "__main__":
    main()
