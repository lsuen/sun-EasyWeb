# Easy-Web

数据驱动的 Web 自动化测试框架，支持 Selenium / Playwright 双引擎一键切换，以 Excel / JSON 维护用例数据，内置测试网站、Allure 报告与 AI 辅助 Agent，开箱即用。

- 作者: 孙文龙 (lsuen)
- 许可证: MIT

## Easy-Web — Web UI Automation Testing Framework

Data-driven Web UI automation testing framework with dual engines (Selenium / Playwright).

- Data-driven test cases from Excel (.xlsx) or JSON
- Case types: search / login / nav / click / locator / workflow
- Allure reports with automatic failure screenshots
- AI-assisted case generation via `python -m ai.chat` (memory & skills built-in)
- Zero-cost setup: works with system Chrome, Playwright, or bundled test site
- License: MIT

**Keywords:** web automation, UI testing, Selenium, Playwright, data-driven testing, pytest, Allure, Excel, JSON, AI agent, LLM

## 特性

- 双引擎支持: Selenium / Playwright 通过配置文件切换，测试代码零改动
- 数据驱动: 支持 Excel (.xlsx) 与 JSON 两种用例格式，自动合并、统一解析
- 配置灵活: YAML 配置 + 环境变量覆盖 + 命令行参数，适配 CI / 多环境部署
- 完整日志: 控制台与文件双输出，失败自动截图
- 占位符替换: 支持 `${variable}` 语法动态注入配置值
- 鲁棒性增强: 三级防御链（原生点击 → JS 注入 → ActionChains），应对不稳定元素
- 智能选择器: 自动识别 xpath / css / id / name / tag / link 等定位方式
- 工作流支持: 多步骤业务流程编排（click / input / wait / cookie / open）
- Cookie 注入: 绕过登录、注入 token、多账号测试
- 报告: Allure 精美报告，失败截图自动嵌入
- AI 扩展: Chat 模式自然语言生成用例、四层记忆（SQLite 持久化）、可插拔 Skill

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备浏览器（二选一）

方式 A: 使用系统已安装的 Chrome，Selenium 4 会自动管理驱动，无需任何下载。

方式 B: 下载 Chrome for Testing 与 ChromeDriver 放入 `pkg/`，实现完全离线自治（推荐 CI 使用）。
下载地址与安装步骤见下文 [内置资源说明](#内置资源说明)。

### 3. 运行测试

```bash
# 跑全部用例（自动启动内置测试网站）
python main.py

# 只跑登录用例，无头模式，不生成报告
python main.py -t login --headless --no-report

# 查看完整参数
python main.py --help
```

首次运行请将 `.env.example` 复制为 `.env` 并按需填写。

## 内置资源说明

为保证仓库体积可控，二进制包并未全部纳入 Git：

| 目录 | 是否入库 | 说明 |
|------|---------|------|
| `pkg/UITestWebsite/` | 是 (约 17 MB) | 内置测试网站（Flask 打包，可离线启动） |
| `pkg/allurec/` | 是 (约 2 MB) | Allure 命令行工具（Windows 内置版） |
| `pkg/chrome-win64/` | 否 (约 400 MB) | Chrome for Testing 浏览器 |
| `pkg/chromedriver-win64/` | 否 (约 21 MB) | ChromeDriver |

`chrome-win64` 与 `chromedriver-win64` 体积过大，请按需自行下载后放入 `pkg/` 目录。
详细说明见 [CHROME_DOWNLOAD.txt](CHROME_DOWNLOAD.txt)。

### Chrome / ChromeDriver 下载

Chrome 与 ChromeDriver 必须版本一致。示例版本 147.0.7727.24：

```
https://storage.googleapis.com/chrome-for-testing-public/147.0.7727.24/win64/chrome-win64.zip
https://storage.googleapis.com/chrome-for-testing-public/147.0.7727.24/win64/chromedriver-win64.zip
```

其他渠道:

- Chrome for Testing 官方页: https://google.github.io/chrome-for-testing/
- ChromeDriver 官方页: https://chromedriver.chromium.org/downloads
- 国内镜像（推荐）:
  - 淘宝镜像: https://npmmirror.com/mirrors/chrome-for-testing
  - 腾讯云镜像: https://mirrors.cloud.tencent.com/npm/chrome-for-testing

解压后保持如下结构:

```
pkg/
├── chrome-win64/chrome.exe
├── chromedriver-win64/chromedriver.exe
├── UITestWebsite/UITestWebsite.exe
└── allurec/bin/allure.bat
```

### 不使用内置 Chrome 的三种方式

方式一: 在 `config/settings.yaml` 中留空相关路径，回退到系统浏览器:

```yaml
browser_path:          # 留空，使用系统默认 Chrome
driver_path:           # 留空，Selenium 自动管理驱动（Selenium Manager）
auto_start_website: false
base_url: https://www.example.com
```

方式二: 通过环境变量指向自备的浏览器与驱动:

```bash
export EASYWEB_BROWSER_PATH="/opt/chrome/chrome.exe"      # 浏览器路径
export EASYWEB_DRIVER_PATH="/opt/chrome/chromedriver.exe" # 驱动路径
export EASYWEB_WEBSITE_PATH="/opt/site/UITestWebsite.exe" # 测试网站路径
export EASYWEB_BASE_URL="https://www.example.com"          # 目标站点
export EASYWEB_HEADLESS="true"                             # 无头模式
```

Windows cmd:

```bat
set EASYWEB_BROWSER_PATH=D:\tools\chrome.exe
set EASYWEB_HEADLESS=true
```

方式三: 使用 Playwright 引擎管理浏览器（`playwright install chromium` 后 `engine: playwright`），
完全不需要 Chrome for Testing。

## 环境变量

敏感项与运行参数统一放入项目根目录 `.env`（复制自 `.env.example`），优先级高于 `config/settings.yaml`:

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | LLM API Key（AI 扩展启用时必填） | `sk-xxx` |
| `LLM_BASE_URL` | OpenAI 兼容服务地址（DeepSeek / Ollama / vLLM 可改） | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `gpt-4o-mini` |
| `LLM_EMBEDDING_MODEL` | 向量模型 | `text-embedding-3-small` |
| `LLM_ENABLED` | 是否启用 LLM（覆盖 YAML） | `false` |
| `LLM_MOCK` | Mock 模式，不调真实 API | `false` |
| `DINGTALK_WEBHOOK` | 钉钉机器人 Webhook（可选） | `https://oapi.dingtalk.com/robot/send?access_token=...` |
| `EASYWEB_BROWSER_PATH` | 覆盖浏览器路径 | 见上 |
| `EASYWEB_DRIVER_PATH` | 覆盖 ChromeDriver 路径 | 见上 |
| `EASYWEB_WEBSITE_PATH` | 覆盖测试网站路径 | 见上 |
| `EASYWEB_BASE_URL` | 覆盖测试基础 URL | `https://www.example.com` |
| `EASYWEB_HEADLESS` | 覆盖无头模式 | `true` |

## 命令行参数

运行 `python main.py --help` 查看完整列表。

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--config` | `-c` | 指定配置文件 | `python main.py -c config/prod.yaml` |
| `--test` | `-t` | 按类型过滤（search/login/nav/click/locator/workflow/all） | `python main.py -t login` |
| `--engine` | `-e` | 自动化引擎（selenium/playwright） | `python main.py -e playwright` |
| `--browser` | `-b` | 浏览器类型 | `python main.py -b chromium` |
| `--headless` | - | 无头模式 | `python main.py --headless` |
| `--no-website` | - | 不自动启动测试网站 | `python main.py --no-website` |
| `--no-report` | - | 不生成 Allure 报告 | `python main.py --no-report` |
| `--open-report` | - | 测试后打开报告（默认开启） | `python main.py --open-report` |
| `--keep-history` | - | 保留历史数据用于趋势分析 | `python main.py --keep-history` |
| `--data-file` | `-d` | 指定测试数据文件 | `python main.py -d data/test_data.json` |
| `--cookie` | `-C` | 注入 Cookie（可多次） | `python main.py -C "token=abc123"` |

常用组合:

```bash
python main.py -t login -e playwright        # 登录用例 + Playwright
python main.py -d data/my_test.json --headless
python main.py -C "session_id=xyz789" -C "user_role=admin"
python main.py -c config/ci.yaml --no-report
```

## 项目结构

```
Easy-Web/
├── config/settings.yaml         # 配置文件
├── data/
│   ├── test_data.json           # JSON 测试数据
│   ├── test_data_baidu.json     # 百度示例数据
│   └── ai/                      # AI 数据（staging、knowledge.db）
├── core/
│   ├── engine.py                # 引擎抽象层（工厂模式）
│   ├── selenium_engine.py       # Selenium 实现
│   └── playwright_engine.py     # Playwright 实现
├── drivers/
│   ├── data_driver.py           # 数据驱动层
│   └── test_runner.py           # 测试执行器
├── ai/                          # AI 扩展层
│   ├── memory/                  # 四层记忆
│   ├── tools/                   # Function Calling 工具
│   ├── skills/                  # 可插拔技能
│   ├── chat.py                  # Chat 入口
│   └── agent_loop.py            # Agent 循环
├── utils/
│   ├── logger.py                # 日志系统
│   ├── config_loader.py         # 配置加载器
│   └── env_loader.py            # .env / 环境变量合并
├── tests/                       # 单元测试（pytest）
│   ├── test_example.py
│   └── ai/
├── pkg/                         # 内置资源（部分需自行下载，见上）
│   ├── chrome-win64/            # Chrome for Testing（不入库）
│   ├── chromedriver-win64/      # ChromeDriver（不入库）
│   ├── UITestWebsite/           # 测试网站（入库）
│   └── allurec/                 # Allure 工具（入库）
├── scripts/ai/                  # AI 运行脚本
├── .doc/20260701doc/            # 架构与 AI 技术文档
├── main.py                      # 入口文件
└── requirements.txt             # 依赖列表
```

## 配置说明

编辑 `config/settings.yaml`:

```yaml
# 引擎与浏览器
engine: selenium              # selenium | playwright
browser: chrome

# 浏览器路径（留空则使用系统默认）
browser_path: pkg/chrome-win64/chrome.exe
driver_path: pkg/chromedriver-win64/chromedriver.exe
playwright_browser_path:

# 测试网站
base_url: http://localhost:5000
auto_start_website: false
website_path: pkg/UITestWebsite/UITestWebsite.exe
website_port: 5000

# 运行
headless: false
timeout: 10
window_size: 1280x720
log_level: INFO
robust_mode: true             # 三级防御链

# Allure（留空则用 pkg 内置版，再 fallback 到系统 PATH）
allure_path:

# LLM（AI 扩展，默认关闭；API Key 写入 .env）
llm:
  enabled: false
  base_url: https://api.openai.com/v1
  model: gpt-4o-mini
  embedding_model: text-embedding-3-small
  mock: false

# Agent / 记忆 / Skill
agent:
  mode: hybrid
  max_steps: 20
memory:
  db_path: data/ai/knowledge.db
skills:
  enabled:
    - generate_case
    - diagnose_failure
    - heal_selector

# 通知
notify:
  dingtalk:
    enabled: false
```

## 测试数据格式

框架采用统一字段规范，Excel 与 JSON 双格式，字段完全一致。
用例类型决定执行逻辑:

| 类型 | 说明 |
|------|------|
| `search` | 搜索测试：输入关键词 + 点击搜索按钮 |
| `login` | 登录测试：两种格式（分段选择器 / 逗号分隔组合） |
| `nav` | 导航测试：点击链接验证跳转 |
| `click` | 通用点击 |
| `locator` | 八大定位方式演示 |
| `workflow` | 多步骤业务流程编排 |

核心字段:

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 用例唯一标识 |
| `name` | 是 | 用例名称 |
| `type` | 是 | 用例类型（路由依据） |
| `url` | 是 | 测试页面地址，可用 `${base_url}` |
| `selector` | 可选 | 元素定位器，自动识别类型 |
| `by` | 否 | 显式指定定位方式 |
| `value` | 可选 | 输入/操作值，可为 `admin,123456` |
| `steps` | workflow 用 | 步骤数组 |
| `expected_type` | 是 | `title` / `text` / `url` / `element` |
| `expected_value` | 是 | 期望内容 |
| `priority` | 否 | `P0` / `P1` |

JSON 示例:

```json
[
    {
        "id": "TC001",
        "name": "搜索Selenium",
        "type": "search",
        "url": "${base_url}/",
        "selector": "#search-input",
        "value": "selenium",
        "expected_type": "title",
        "expected_value": "搜索",
        "priority": "P0"
    },
    {
        "id": "TC002",
        "name": "管理员登录",
        "type": "login",
        "url": "${base_url}/login",
        "selector": "#username,#password,#login-btn",
        "value": "admin,123456",
        "result_selector": ".welcome",
        "expected_type": "text",
        "expected_value": "admin",
        "priority": "P0"
    }
]
```

Excel 格式: 首行为字段表头，支持多 Sheet，框架自动合并。日常维护推荐 Excel，CI 集成推荐 JSON。

### 智能选择器识别

`selector` 前缀自动决定定位方式，也可用 `by` 显式指定:

```
// 开头        -> xpath
id= 开头       -> id
name= 开头     -> name
tag= 开头      -> tag_name
link= 开头     -> link_text
# 或 . 开头    -> css
```

### 工作流示例

```json
{
    "id": "WF001",
    "name": "完整登录流程",
    "type": "workflow",
    "url": "${base_url}/",
    "steps": [
        {"type": "click", "selector": "#login-link"},
        {"type": "wait", "selector": "#username", "timeout": 5},
        {"type": "input", "selector": "id=username", "value": "admin"},
        {"type": "input", "selector": "id=password", "value": "123456"},
        {"type": "click", "selector": "#login-btn"},
        {"type": "wait", "selector": "#welcome-msg", "timeout": 5}
    ],
    "expected_type": "text",
    "expected_value": "admin",
    "priority": "P0"
}
```

工作流步骤类型:

| 步骤 | 说明 |
|------|------|
| `click` | 点击元素 |
| `input` | 输入文本 |
| `wait` | 等待元素出现 |
| `wait_page` | 等待页面加载 |
| `cookie` | 设置 Cookie |
| `open` | 打开 URL |

### Cookie 注入

绕过登录、多账号权限测试。用例内的 cookie 步骤优先级高于 CLI 参数:

```bash
python main.py -C "token=abc123" -C "role=admin"
```

```json
{
    "id": "WF003",
    "type": "workflow",
    "url": "${base_url}/",
    "steps": [
        {"type": "cookie", "name": "session_id", "value": "abc123token", "domain": "localhost"},
        {"type": "open", "selector": "${base_url}/dashboard"},
        {"type": "wait_page", "timeout": 10},
        {"type": "wait", "selector": "#welcome-msg", "timeout": 5}
    ],
    "expected_type": "text",
    "expected_value": "admin"
}
```

## 测试网站

内置 `pkg/UITestWebsite`（离线 Flask 应用），覆盖常见 Web 自动化场景:

1. 首页搜索 `/` - 类似百度搜索
2. 用户登录 `/login` - 测试账号: admin/123456、test/test123、student/student123
3. 元素定位 `/elements` - 八大定位方式练习
4. iframe 演示 `/frames`
5. 弹窗演示 `/alerts`
6. 下拉框 `/dropdown`
7. 鼠标键盘 `/mouse-keyboard`
8. 多窗口 `/windows`

## 自定义用例

在 `tests/test_example.py` 添加测试函数并在 `main.py` 的 `test_funcs` 中注册:

```python
def test_my_feature(engine: Engine, data: dict):
    """自定义测试"""
    engine.open(data['url'])
    engine.click('#some-button')
    engine.input('#input-field', data['value'])
    text = engine.get_text('#result')
    assert data['expected'] in text
```

```python
test_funcs = {
    'search': test_example.test_search,
    'login': test_example.test_login,
    'my_test': test_example.test_my_feature,
}
```

运行: `python main.py -t my_test`

## 日志与报告

- 日志文件: `logs/` 目录，控制台与文件双输出
- 失败截图: `screenshots/` 目录自动保存
- Allure 报告: 测试完成后生成 `allure-report/`，失败截图自动嵌入

```bash
pkg\allurec\bin\allure open allure-report
```

## AI 扩展

AI 层基于微内核之上，提供 Chat 用例生成、四层记忆、Function Calling 与可插拔 Skill。

```bash
# Mock 模式（无需 API Key，生成用例到 staging）
python -m ai.chat --mock "帮我生成一个登录用例"

# 真实 LLM：复制 .env.example 为 .env 并配置 LLM_API_KEY / LLM_ENABLED=true
python -m ai.chat "帮我生成搜索用例"

# 运行 AI 模块测试
python -m pytest tests/ai/ -v
```

技术细节见 [.doc/20260701doc/04-AI使用说明.md](.doc/20260701doc/04-AI使用说明.md)。

## Agent / AI 编程工具接入

Easy-Web 无需图形界面即可运行，非常适合作为 AI Agent 的自动化工具箱:

1. 仓库内置 [AGENTS.md](AGENTS.md)，opencode / Claude Code / Cursor / Cline 等工具启动后
   自动读取项目约定，直接进入开发状态，无需人工引导。
2. 依赖极简（仅 selenium / playwright / openpyxl / pyyaml / pytest），clone 后一条命令即可运行。
3. Agent 可通过自然语言调用 `python -m ai.chat` 生成用例草稿，再交由 `main.py` 执行验证。
4. Skill 机制（generate_case / diagnose_failure / heal_selector）可让 Agent 动态加载专项能力。

```bash
git clone https://github.com/lsuen/sun-EasyWeb.git
cd sun-EasyWeb
pip install -r requirements.txt
python -m ai.chat --mock "帮我生成一个搜索用例"   # Agent 可自然语言驱动
python main.py -t search --headless               # 执行并自校验
```

## 引擎切换

修改配置一行即可切换引擎，两个引擎共享同一 API，测试代码零修改:

```yaml
engine: selenium    # 或 playwright
```

双引擎验证: 分别以两个引擎运行同一批用例，结果应完全一致，验证框架引擎无关性。
Playwright 需先执行 `playwright install` 安装浏览器。

## 贡献与反馈

欢迎提交 Issue 与 Pull Request。请遵循 AGENTS.md 中的开发约定（含测试）。

## License

[MIT](LICENSE)