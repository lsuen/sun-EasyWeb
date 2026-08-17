"""项目 .env 加载与配置合并。"""
import os
from typing import Any, Dict, Optional


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_project_env(env_file: Optional[str] = None) -> bool:
    """
    加载项目根目录 .env 到 os.environ。
    优先使用 python-dotenv；未安装时回退到简易解析。
    """
    root = get_project_root()
    path = env_file or os.path.join(root, ".env")
    if not os.path.exists(path):
        return False

    try:
        from dotenv import load_dotenv
        return load_dotenv(path, override=False)
    except ImportError:
        return _load_env_fallback(path)


def _load_env_fallback(path: str) -> bool:
    loaded = False
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
                loaded = True
    return loaded


def _env_bool(name: str) -> Optional[bool]:
    val = os.environ.get(name)
    if val is None or val == "":
        return None
    return val.strip().lower() in ("1", "true", "yes", "on")


def _env_float(name: str) -> Optional[float]:
    val = os.environ.get(name)
    if val is None or val == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _env_int(name: str) -> Optional[int]:
    val = os.environ.get(name)
    if val is None or val == "":
        return None
    try:
        return int(val)
    except ValueError:
        return None


def apply_env_to_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 .env / 环境变量合并进配置。
    YAML 提供默认值，.env 覆盖 LLM 与通知等敏感项。
    """
    load_project_env()

    llm = dict(config.get("llm") or {})
    env_map_str = {
        "LLM_API_KEY": "api_key",
        "LLM_BASE_URL": "base_url",
        "LLM_MODEL": "model",
        "LLM_EMBEDDING_MODEL": "embedding_model",
    }
    for env_name, key in env_map_str.items():
        val = os.environ.get(env_name)
        if val:
            llm[key] = val

    for env_name, key in (("LLM_ENABLED", "enabled"), ("LLM_MOCK", "mock")):
        parsed = _env_bool(env_name)
        if parsed is not None:
            llm[key] = parsed

    temp = _env_float("LLM_TEMPERATURE")
    if temp is not None:
        llm["temperature"] = temp
    max_tokens = _env_int("LLM_MAX_TOKENS")
    if max_tokens is not None:
        llm["max_tokens"] = max_tokens

    config["llm"] = llm

    notify = dict(config.get("notify") or {})
    dingtalk = dict(notify.get("dingtalk") or {})
    webhook = os.environ.get("DINGTALK_WEBHOOK")
    if webhook:
        dingtalk["webhook"] = webhook
    notify["dingtalk"] = dingtalk
    config["notify"] = notify

    # 运行路径/URL 覆盖：便于 CI 与多环境部署，无需修改配置文件
    for env_name, key in {
        "EASYWEB_BROWSER_PATH": "browser_path",
        "EASYWEB_DRIVER_PATH": "driver_path",
        "EASYWEB_WEBSITE_PATH": "website_path",
        "EASYWEB_BASE_URL": "base_url",
    }.items():
        val = os.environ.get(env_name)
        if val:
            config[key] = val

    headless = _env_bool("EASYWEB_HEADLESS")
    if headless is not None:
        config["headless"] = headless

    return config
