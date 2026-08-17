"""
Pytest 配置文件 - 核心 Fixture 和 Hooks

作者：孙文龙 | 许可证：MIT
"""
import os
import pytest
import allure
from datetime import datetime

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engine import Engine
from utils.config_loader import ConfigLoader
from utils.logger import get_logger


logger = get_logger('Conftest')


def pytest_configure(config):
    """Pytest 配置钩子"""
    # 注册 allure 自定义标记
    config.addinivalue_line(
        "markers", "smoke: 冒烟测试标记"
    )
    config.addinivalue_line(
        "markers", "regression: 回归测试标记"
    )


@pytest.fixture(scope="session")
def config():
    """
    会话级配置 Fixture
    加载全局配置，所有测试共享
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.yaml')
    return ConfigLoader(config_path).config


@pytest.fixture(scope="function")
def engine(request, config):
    """
    函数级浏览器引擎 Fixture
    每个测试用例自动启动和关闭浏览器
    """
    logger.info(f"启动引擎: {config.get('engine')} - {config.get('browser')}")

    # 初始化引擎
    eng = Engine.get_engine(config)
    eng.start()
    
    # 注入 CLI cookie（优先级低于用例中的 cookie 步骤）
    cli_cookies = config.get('cli_cookies', [])
    if cli_cookies:
        try:
            for cookie in cli_cookies:
                eng.set_cookie(
                    name=cookie['name'],
                    value=cookie['value'],
                    domain=cookie.get('domain'),
                    path=cookie.get('path', '/'),
                )
            logger.info(f"CLI Cookie 注入完成: {len(cli_cookies)} 个")
        except Exception as e:
            logger.warning(f"CLI Cookie 注入失败: {e}")

    yield eng

    # 测试结束后清理
    try:
        eng.quit()
        logger.info("引擎已关闭")
    except Exception as e:
        logger.warning(f"关闭引擎时出错: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试报告钩子 - 失败时自动截图并附加到 Allure
    """
    outcome = yield
    report = outcome.get_result()
    
    # 只在调用阶段且失败时执行
    if report.when == 'call' and report.failed:
        # 获取 engine fixture
        engine = item.funcargs.get('engine')
        if engine:
            try:
                # 生成截图文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_name = f"fail_{item.name}_{timestamp}.png"
                screenshot_path = os.path.join('screenshots', screenshot_name)
                
                # 确保目录存在
                os.makedirs('screenshots', exist_ok=True)
                
                # 截图
                engine.screenshot(screenshot_path)
                logger.error(f"测试失败，截图已保存: {screenshot_path}")
                
                # 附加到 Allure 报告
                if os.path.exists(screenshot_path):
                    with open(screenshot_path, 'rb') as f:
                        allure.attach(
                            f.read(),
                            name="失败截图",
                            attachment_type=allure.attachment_type.PNG
                        )
            except Exception as e:
                logger.error(f"截图失败: {e}")


def pytest_addoption(parser):
    """添加自定义命令行参数"""
    parser.addoption(
        "--data-file",
        action="store",
        default="data/test_data.json",
        help="指定测试数据文件路径"
    )


def load_test_data(file_path: str = None) -> list:
    """
    加载测试数据辅助函数
    供 pytest.mark.parametrize 使用

    Args:
        file_path: 数据文件路径 (相对于项目根目录)

    Returns:
        list: 测试数据列表 (已替换占位符)
    """
    import sys
    from drivers.data_driver import DataDriver
    from utils.config_loader import ConfigLoader

    # 优先使用传入的路径
    if file_path is None:
        # 从 sys.argv 解析 --data-file 参数
        data_file_from_argv = None
        for i, arg in enumerate(sys.argv):
            if arg in ('--data-file', '-d') and i + 1 < len(sys.argv):
                data_file_from_argv = sys.argv[i + 1]
                break
            elif arg.startswith('--data-file='):
                data_file_from_argv = arg.split('=', 1)[1]
                break

        # 确定最终使用的数据文件
        if data_file_from_argv:
            file_path = data_file_from_argv
        elif os.path.exists('data/_temp.json'):
            file_path = 'data/_temp.json'
        else:
            file_path = 'data/test_data.json'

    # 转换为绝对路径
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)

    driver = DataDriver(file_path)
    data = driver.load()

    # 加载配置用于占位符替换
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'settings.yaml')
    config = ConfigLoader(config_path).config

    # 替换所有数据行中的占位符
    context = {'base_url': config.get('base_url', '')}
    replaced_data = []
    for row in data:
        replaced_row = DataDriver.replace_placeholders(row, context)
        replaced_data.append(replaced_row)

    return replaced_data


def _auto_detect_by(selector: str, data: dict = None) -> tuple:
    """
    智能识别选择器类型并提取实际值
    
    返回: (by_type, actual_selector)
    """
    if data and data.get('by'):
        return data['by'], selector
    
    if selector.startswith('//'):
        return 'xpath', selector
    if selector.startswith('id='):
        return 'id', selector[3:]
    if selector.startswith('name='):
        return 'name', selector[5:]
    if selector.startswith('tag='):
        return 'tag_name', selector[4:]
    if selector.startswith('link='):
        return 'link_text', selector[5:]
    if selector.startswith('partial_link='):
        return 'partial_link_text', selector[13:]
    
    return 'css', selector


def execute_test_case(engine, data: dict, config: dict = None):
    """
    路由分发器 - 根据 type 字段执行不同的测试逻辑

    Args:
        engine: 浏览器引擎实例
        data: 测试数据字典
        config: 配置字典（用于判断 robust_mode）
    """
    test_type = data.get('type', '').lower()
    selector = data.get('selector', '')
    value = data.get('value', '')
    robust = config and config.get('robust_mode', False)
    by, selector = _auto_detect_by(selector, data)

    # 支持多步骤工作流
    if test_type == 'workflow':
        steps = data.get('steps', [])
        for i, step in enumerate(steps):
            step_type = step.get('type', '').lower()
            step_selector = step.get('selector', '')
            step_value = step.get('value', '')
            step_by, step_selector = _auto_detect_by(step_selector, step)

            if step_type == 'click':
                if robust:
                    engine.robust_click(step_selector, by=step_by)
                else:
                    engine.click(step_selector, by=step_by)
            elif step_type == 'input':
                if robust:
                    engine.robust_input(step_selector, step_value, by=step_by)
                else:
                    engine.input(step_selector, step_value, by=step_by)
            elif step_type == 'wait':
                engine.wait_for_element(step_selector, by=step_by, timeout=step.get('timeout', 10))
            elif step_type == 'wait_page':
                engine.wait_for_page_load(timeout=step.get('timeout', 10))
            elif step_type == 'cookie':
                # 设置Cookie
                engine.set_cookie(
                    name=step.get('name', step_selector),
                    value=step_value,
                    domain=step.get('domain'),
                    path=step.get('path', '/'),
                )
            elif step_type == 'open':
                engine.open(step_selector)
            else:
                raise ValueError(f"不支持的步骤类型: {step_type}")
        return

    if test_type == 'search':
        # 搜索测试
        # 支持从数据中读取 search_btn_selector 和 results_selector
        search_btn = data.get('search_btn_selector', '#search-btn')
        results_selector = data.get('results_selector', '#search-results')
        search_btn_by, search_btn = _auto_detect_by(search_btn, data)
        
        if robust:
            engine.robust_input(selector, value, by=by)
            engine.robust_click(search_btn, by=search_btn_by)
            engine.wait_for_element(results_selector, timeout=5)
        else:
            engine.input(selector, value, by=by)
            engine.click(search_btn, by=search_btn_by)
            engine.wait_for_element(results_selector, timeout=5)

    elif test_type == 'login':
        # 登录测试
        # selector 格式: username_selector,password_selector,login_button_selector
        # value 格式: username,password
        if ',' in selector:
            selectors = selector.split(',')
            values = value.split(',')
            by0, sel0 = _auto_detect_by(selectors[0])
            by1, sel1 = _auto_detect_by(selectors[1])
            by2, sel2 = _auto_detect_by(selectors[2])
            if robust:
                engine.robust_input(sel0, values[0], by=by0)
                engine.robust_input(sel1, values[1], by=by1)
                engine.robust_click(sel2, by=by2)
            else:
                engine.input(sel0, values[0], by=by0)
                engine.input(sel1, values[1], by=by1)
                engine.click(sel2, by=by2)
        else:
            # 兼容旧格式 - 优先从数据中读取选择器
            username_selector = data.get('username_selector', '#username')
            password_selector = data.get('password_selector', '#password')
            login_btn_selector = data.get('login_btn_selector', '#login-btn')
            
            username_by, username_selector = _auto_detect_by(username_selector)
            password_by, password_selector = _auto_detect_by(password_selector)
            login_btn_by, login_btn_selector = _auto_detect_by(login_btn_selector)
            
            values = value.split(',')
            if robust:
                engine.robust_input(username_selector, values[0], by=username_by)
                engine.robust_input(password_selector, values[1], by=password_by)
                engine.robust_click(login_btn_selector, by=login_btn_by)
            else:
                engine.input(username_selector, values[0], by=username_by)
                engine.input(password_selector, values[1], by=password_by)
                engine.click(login_btn_selector, by=login_btn_by)

        # 等待结果 - 优先使用 result_selector
        welcome_selector = data.get('result_selector', '#welcome-msg')
        try:
            engine.wait_for_element(welcome_selector, timeout=3)
        except:
            pass  # 可能是失败测试，等待错误提示

    elif test_type == 'nav':
        # 导航测试
        if robust:
            engine.robust_click(selector, by=by)
        else:
            engine.click(selector, by=by)
        engine.wait_for_element('body', timeout=5)

    elif test_type == 'click':
        # 通用点击测试
        if robust:
            engine.robust_click(selector, by=by)
        else:
            engine.click(selector, by=by)
        engine.wait_for_element('body', timeout=5)

    elif test_type == 'locator':
        # 八大定位元素测试
        by = data.get('by', 'css')
        value = data.get('value', '')

        if by in ('link_text', 'partial_link_text'):
            # 链接文本定位直接点击
            if robust:
                engine.robust_click(selector, by=by)
            else:
                engine.click(selector, by=by)
        elif by == 'tag_name':
            # Tag定位通常取第一个，这里做点击演示
            if robust:
                engine.robust_click(selector, by=by)
            else:
                engine.click(selector, by=by)
        else:
            # 其他定位输入文本
            if robust:
                engine.robust_input(selector, value, by=by)
            else:
                engine.input(selector, value, by=by)
        engine.wait_for_element('body', timeout=2)

    else:
        raise ValueError(f"不支持的测试类型: {test_type}")


def assert_test_result(engine, data: dict):
    """
    统一断言引擎 - 根据 expected_type 执行不同的断言逻辑
    
    Args:
        engine: 浏览器引擎实例
        data: 测试数据字典
    """
    expected_type = data.get('expected_type', '').lower()
    expected_value = data.get('expected_value', '')
    selector = data.get('selector', '')
    result_selector = data.get('result_selector', '')  # 新增：结果元素选择器
    
    if not expected_type or not expected_value:
        return  # 没有期望结果，跳过断言
    
    if expected_type == 'title':
        title = engine.get_title()
        assert expected_value in title, f"标题期望包含 '{expected_value}'，实际: '{title}'"
        
    elif expected_type == 'url':
        current_url = engine.get_current_url()
        assert expected_value in current_url, f"URL期望包含 '{expected_value}'，实际: '{current_url}'"
        
    elif expected_type == 'text':
        # 优先使用 result_selector，其次 selector，最后才尝试智能推断
        if result_selector:
            target_selector = result_selector
        elif selector and ',' not in selector:  # 如果是复合选择器则不使用
            target_selector = selector
        else:
            # 不再根据期望值智能推断，直接使用通用的 #result 或抛出异常
            target_selector = data.get('default_result_selector', '#result')
        
        text = engine.get_text(target_selector)
        assert expected_value in text, f"文本期望包含 '{expected_value}'，实际: '{text}'"
        
    elif expected_type == 'element':
        # 验证元素存在
        engine.wait_for_element(selector, timeout=5)
        
    elif expected_type == 'value':
        # 验证输入框的值
        by = data.get('by_result', data.get('by', 'css'))
        element = engine.find_element(selector, by=by)
        actual_value = element.get_attribute('value')
        assert expected_value in actual_value, f"输入值期望包含 '{expected_value}'，实际: '{actual_value}'"
        
    elif expected_type == 'click':
        # 验证点击操作成功（页面未报错）
        pass  # 点击已在 execute_test_case 中执行，此处仅标记通过
        
    else:
        raise ValueError(f"不支持的期望类型: {expected_type}")
