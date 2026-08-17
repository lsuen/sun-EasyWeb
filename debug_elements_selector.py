"""
============================================================
  debug_elements_selector.py - 元素定位调试神器
============================================================
作者：孙文龙 | 许可证：MIT

【使用说明】
1. 运行方式：直接双击或在命令行执行 python debug_elements_selector.py
2. 核心功能：
   - 自动启动项目内置的 Chrome 浏览器（Debug 模式）
   - 自动连接 Selenium，无需手动配置驱动
   - 内置多种定位方式 Demo（ID, Name, Class, XPath, CSS 等）
   - 提供交互式循环，支持实时输入 URL 和定位器进行验证
3. 适用场景：
   - 编写测试用例前，快速验证 XPath 或 CSS 选择器是否有效
   - 调试页面元素定位问题
   - 学习 Selenium 八大定位方法

【注意事项】
- 脚本会自动寻找 pkg/chrome-win64/chrome.exe，请确保该文件存在。
- 如果 9222 端口被占用，脚本会尝试清理或提示。
- 运行前请确保测试网站 (pkg/UITestWebsite) 已启动，或手动输入其他 URL。
============================================================
"""
import os
import sys
import subprocess
import time
import signal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= 配置区 =================
# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Chrome 浏览器路径 (项目内置)
CHROME_PATH = os.path.join(PROJECT_ROOT, 'pkg', 'chrome-win64', 'chrome.exe')

# ChromeDriver 路径 (项目内置，虽然 debug 模式通常不需要，但保留以防万一)
DRIVER_PATH = os.path.join(PROJECT_ROOT, 'pkg', 'chromedriver-win64', 'chromedriver.exe')

# 调试端口
DEBUG_PORT = 9222

# 默认测试 URL (内置测试网站)
DEFAULT_URL = "http://localhost:5000"

# 等待超时时间 (秒)
WAIT_TIMEOUT = 5
# ==========================================


def start_chrome_debug():
    """启动 Chrome 远程调试模式"""
    print(f"\n正在启动 Chrome (Debug 模式: {DEBUG_PORT})...")
    
    # 检查 Chrome 是否存在
    if not os.path.exists(CHROME_PATH):
        print(f"错误: 找不到 Chrome 浏览器: {CHROME_PATH}")
        print("   请确保 pkg/chrome-win64/chrome.exe 存在。")
        sys.exit(1)
    
    # 构建启动命令
    # --no-first-run: 跳过首次运行向导
    # --no-default-browser-check: 不检查默认浏览器
    # --remote-debugging-port: 开启远程调试
    cmd = [
        CHROME_PATH,
        f'--remote-debugging-port={DEBUG_PORT}',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-background-timer-throttling'
    ]
    
    try:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        print(f"Chrome 已启动 (PID: {process.pid})")
        time.sleep(2)  # 等待浏览器初始化
        return process
    except Exception as e:
        print(f"启动 Chrome 失败: {e}")
        sys.exit(1)


def connect_browser():
    """连接 Selenium 到调试浏览器"""
    print(f"\n正在连接 Selenium 到 localhost:{DEBUG_PORT}...")
    
    options = Options()
    options.add_experimental_option('debuggerAddress', f'127.0.0.1:{DEBUG_PORT}')
    
    try:
        # 连接已运行的浏览器
        driver = webdriver.Chrome(options=options)
        print("Selenium 连接成功！")
        return driver
    except Exception as e:
        print(f"连接失败: {e}")
        print("   提示: 请确保没有其他程序占用 9222 端口，或稍等几秒重试。")
        sys.exit(1)


def run_demo(driver):
    """运行预设的定位 Demo"""
    print("\n" + "="*50)
    print("开始运行定位 Demo (基于内置测试网站)")
    print("="*50)
    
    # 打开默认页面
    print(f"\n打开页面: {DEFAULT_URL}")
    driver.get(DEFAULT_URL)
    time.sleep(1)
    
    demos = [
        ("ID 定位", By.ID, "search-input", "输入框"),
        ("Name 定位", By.NAME, "q", "搜索框 (如果存在)"),
        ("Class 定位", By.CLASS_NAME, "btn-submit", "提交按钮"),
        ("Tag 定位", By.TAG_NAME, "input", "第一个 Input"),
        ("XPath 定位", By.XPATH, "//input[@id='search-input']", "搜索输入框"),
        ("CSS 定位", By.CSS_SELECTOR, "#search-input", "搜索输入框"),
        ("Link Text", By.LINK_TEXT, "首页", "首页链接"),
        ("Partial Link", By.PARTIAL_LINK_TEXT, "登录", "登录链接"),
    ]
    
    for name, by, value, desc in demos:
        print(f"\n测试: {name} -> {value} ({desc})")
        try:
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((by, value))
            )
            print(f"   成功! 标签: {element.tag_name}, 文本: {element.text[:30] if element.text else '(无文本)'}")
        except Exception as e:
            print(f"   失败: {e}")
    
    print("\n" + "="*50)
    print("Demo 运行完毕！")
    print("="*50)


def interactive_loop(driver):
    """交互式定位测试循环"""
    print("\n进入交互模式 (输入 'quit' 或 'exit' 退出)")
    print("   格式: [URL] [定位类型] [定位值]")
    print("   示例: http://localhost:5000/login id username")
    print("   定位类型支持: id, name, class, tag, xpath, css, link, partial_link")
    
    while True:
        print("\n" + "-"*40)
        user_input = input("请输入: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("退出调试模式...")
            break
        
        if not user_input:
            continue
        
        parts = user_input.split()
        
        # 解析输入
        if len(parts) == 2:
            # 使用当前 URL
            url = driver.current_url
            loc_type, loc_value = parts
        elif len(parts) == 3:
            url, loc_type, loc_value = parts
        else:
            print("格式错误，请输入: [URL] [类型] [值]")
            continue
        
        # 映射定位类型
        type_map = {
            'id': By.ID,
            'name': By.NAME,
            'class': By.CLASS_NAME,
            'tag': By.TAG_NAME,
            'xpath': By.XPATH,
            'css': By.CSS_SELECTOR,
            'link': By.LINK_TEXT,
            'partial_link': By.PARTIAL_LINK_TEXT,
        }
        
        by = type_map.get(loc_type.lower())
        if not by:
            print(f"不支持的定位类型: {loc_type}")
            continue
        
        # 如果 URL 变了，先跳转
        if url != driver.current_url:
            print(f"跳转到: {url}")
            driver.get(url)
            time.sleep(1)
        
        # 执行定位
        print(f"正在定位: {loc_type} -> {loc_value}")
        try:
            element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((by, loc_value))
            )
            print(f"成功! 标签: {element.tag_name}, 文本: {element.text[:50] if element.text else '(无文本)'}")
            
            # 额外信息
            if element.tag_name == 'input':
                print(f"   值: {element.get_attribute('value')}")
            elif element.tag_name == 'a':
                print(f"   链接: {element.get_attribute('href')}")
                
        except Exception as e:
            print(f"失败: 未找到元素或超时")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  Easy-Web 元素定位调试工具")
    print("  Easy-Web 自动化测试框架 (MIT 许可证)")
    print("="*60)
    
    # 1. 启动 Chrome
    chrome_process = start_chrome_debug()
    driver = None
    
    try:
        # 2. 连接浏览器
        driver = connect_browser()
        
        # 3. 运行 Demo
        run_demo(driver)
        
        # 4. 进入交互模式
        interactive_loop(driver)
        
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        # 清理
        if driver:
            print("\n关闭 Selenium 连接...")
            driver.quit()
        
        if chrome_process:
            print("关闭 Chrome 进程...")
            try:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(chrome_process.pid)], 
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    os.killpg(os.getpgid(chrome_process.pid), signal.SIGTERM)
                chrome_process.wait(timeout=3)
            except:
                pass
        
        print("清理完成，再见！")


if __name__ == '__main__':
    # main()
    # start_chrome_debug()
    driver = connect_browser()
    
    # 打开测试页面
    driver.get('http://localhost:5000/')
    time.sleep(1)
    
    # todo 查找并点击元素 - 直接定位并点击
    # driver.find_element(By.ID, "login-btn").click()  # 通过ID点击登录按钮
    # driver.find_element(By.CSS_SELECTOR, "a[href='/']").click()  # 通过CSS点击链接
    # driver.find_element(By.XPATH, "//button[@class='submit']").click()  # 通过XPath点击
    
    time.sleep(1)
    
    # todo 查找并输入内容 - 直接定位并输入
    driver.find_element(By.ID, "search-input").send_keys("python")  # 输入用户名
    # driver.find_element(By.ID, "username").send_keys("admin")  # 输入用户名
    # driver.find_element(By.ID, "password").send_keys("123456")  # 输入密码
    # driver.find_element(By.NAME, "q").send_keys("搜索关键词")  # 通过Name输入
    # driver.find_element(By.CSS_SELECTOR, "#search-input").send_keys("测试内容")  # 通过CSS输入