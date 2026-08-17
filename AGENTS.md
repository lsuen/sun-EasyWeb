# AGENTS.md

本文件面向 AI 编程工具（opencode / Claude Code / Cursor / Cline 等），
帮助 Agent 快速理解 Easy-Web 项目并正确接入。

## 项目概述

Easy-Web 是一个数据驱动的 Web 自动化测试框架：

- 双引擎: Selenium / Playwright，通过 `config/settings.yaml` 的 `engine` 字段切换
- 数据驱动: `data/*.json` 或 Excel 定义用例，`main.py` 读取执行
- AI 扩展: `python -m ai.chat` 支持自然语言生成用例，含四层记忆与 Skill
- 报告: pytest + Allure，`--no-report` 可跳过

## 常用命令

```bash
pip install -r requirements.txt   # 安装依赖
python main.py -t search          # 按类型跑用例（search/login/nav/click/locator/workflow/all）
python main.py --help             # 查看全部 CLI 参数
python -m pytest tests/ -q        # 跑单元测试（重点 tests/ai/）
python -m ai.chat --mock "帮我生成一个登录用例"   # AI Chat（mock 模式无需 API Key）
```

环境变量优先级高于 YAML：LLM_*（AI 配置）、EASYWEB_*（浏览器/网站路径、无头模式）、DINGTALK_WEBHOOK。
敏感项写入根目录 `.env`（复制自 `.env.example`）。

## 关键约定

- 用例核心字段: `id` / `name` / `type` / `url` / `selector` / `value` / `expected_type` / `expected_value`
- 用例类型: search / login / nav / click / locator / workflow（workflow 用 `steps` 数组编排）
- 定位器自动识别: `//` 开头为 xpath，`#`/`.` 开头为 css，`id=`/`name=`/`tag=`/`link=` 为对应方式
- `pkg/chrome-win64/` 与 `pkg/chromedriver-win64/` 体积过大不入库，需按 CHROME_DOWNLOAD.txt 下载
- 默认 `engine: selenium`，可用 `-e playwright` 覆盖

## 架构

```
main.py (入口) -> ConfigLoader / env_loader -> Engine 工厂
    -> SeleniumEngine / PlaywrightEngine -> DataDriver / test_runner -> pytest -> Allure
AI 层: ai/chat.py -> agent_loop -> memory(L1-L4, SQLite) -> tools -> skills
```

## 开发约定

- Python 3.10+，新功能必须补充 `tests/` 下的单元测试
- 代码注释使用中文，逻辑分离，禁止硬编码路径/密钥
- 提交信息格式: `<type>: <中文描述>`（feat/fix/refactor/doc/test/chore）
