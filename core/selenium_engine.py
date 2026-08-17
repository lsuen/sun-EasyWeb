"""
Selenium 引擎实现
"""
import os
import time
from typing import Optional, Dict, List, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException

from core.engine import BaseEngine
from utils.logger import get_logger


class SeleniumEngine(BaseEngine):
    """Selenium Web自动化引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger('SeleniumEngine')
    
    def start(self):
        """启动浏览器"""
        browser = self.config.get('browser', 'chrome').lower()
        self.logger.info(f"启动 {browser} 浏览器...")
        
        if browser == 'chrome':
            options = webdriver.ChromeOptions()
            if self.config.get('headless', False):
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
            if self.config.get('window_size'):
                options.add_argument(f'--window-size={self.config["window_size"]}')
            
            # 自定义浏览器路径
            browser_path = self.config.get('browser_path')
            if browser_path and os.path.exists(browser_path):
                options.binary_location = browser_path
                self.logger.info(f"使用自定义浏览器路径: {browser_path}")
            
            # 创建 Service
            driver_path = self.config.get('driver_path')
            if driver_path and os.path.exists(driver_path):
                service = ChromeService(executable_path=driver_path)
                self.logger.info(f"使用自定义 ChromeDriver: {driver_path}")
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.logger.info("使用系统自动检测的 ChromeDriver")
                self.driver = webdriver.Chrome(options=options)
                
        elif browser == 'firefox':
            options = webdriver.FirefoxOptions()
            if self.config.get('headless', False):
                options.add_argument('--headless')
            
            # 自定义浏览器路径
            browser_path = self.config.get('browser_path')
            if browser_path and os.path.exists(browser_path):
                options.binary_location = browser_path
                self.logger.info(f"使用自定义浏览器路径: {browser_path}")
            
            # 自定义驱动路径
            driver_path = self.config.get('driver_path')
            if driver_path and os.path.exists(driver_path):
                service = FirefoxService(executable_path=driver_path)
                self.driver = webdriver.Firefox(service=service, options=options)
            else:
                self.driver = webdriver.Firefox(options=options)
        else:
            raise ValueError(f"不支持的浏览器: {browser}")
        
        self.driver.set_page_load_timeout(self.config.get('timeout', 10))
        self.logger.info(f"浏览器启动成功: {self.driver.capabilities.get('browserName')} "
                        f"v{self.driver.capabilities.get('browserVersion')}")
    
    def quit(self):
        """关闭浏览器"""
        if self.driver:
            self.logger.info("关闭浏览器...")
            self.driver.quit()
            self.driver = None
    
    def open(self, url: str):
        """打开URL"""
        self.logger.info(f"打开URL: {url}")
        self.driver.get(url)
    
    def click(self, selector: str, by: str = 'css'):
        """点击元素"""
        element = self.find_element(selector, by)
        self.logger.info(f"点击元素: {selector}")
        element.click()
    
    def input(self, selector: str, text: str, by: str = 'css'):
        """输入文本"""
        element = self.find_element(selector, by)
        self.logger.info(f"输入文本到 {selector}: {text[:50]}...")
        element.clear()
        element.send_keys(text)
    
    def get_text(self, selector: str, by: str = 'css') -> str:
        """获取元素文本"""
        element = self.find_element(selector, by)
        text = element.text
        self.logger.debug(f"获取文本 {selector}: {text[:50]}")
        return text
    
    def find_element(self, selector: str, by: str = 'css'):
        """查找元素"""
        by_mapping = self._get_by_mapping(by)
        try:
            return self.driver.find_element(by=by_mapping, value=selector)
        except Exception as e:
            # 简化错误日志
            msg = str(e).split('Stacktrace:')[0].strip() if 'Stacktrace:' in str(e) else str(e)
            self.logger.error(f"查找元素失败: {selector} by {by}: {msg}")
            raise
    
    def find_elements(self, selector: str, by: str = 'css') -> list:
        """查找多个元素"""
        by_mapping = self._get_by_mapping(by)
        return self.driver.find_elements(by=by_mapping, value=selector)
    
    def get_title(self) -> str:
        """获取页面标题"""
        return self.driver.title
    
    def get_current_url(self) -> str:
        """获取当前URL"""
        return self.driver.current_url
    
    def screenshot(self, filepath: str):
        """截图"""
        self.logger.info(f"截图保存到: {filepath}")
        self.driver.save_screenshot(filepath)
    
    def wait_for_element(self, selector: str, by: str = 'css', timeout: int = 10):
        """等待元素出现"""
        by_mapping = self._get_by_mapping(by)
        self.logger.debug(f"等待元素: {selector}")
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by_mapping, selector))
        )
    
    def execute_script(self, script: str, *args) -> Any:
        """执行JavaScript"""
        self.logger.debug(f"执行JS: {script[:50]}...")
        return self.driver.execute_script(script, *args)

    def set_cookie(self, name: str, value: str, domain: str = None, path: str = '/', expiry: int = None):
        """
        设置Cookie
        
        Args:
            name: Cookie名称
            value: Cookie值
            domain: 域名（可选）
            path: 路径（默认 /）
            expiry: 过期时间戳（可选）
        """
        self.logger.info(f"设置Cookie: {name}={value[:20]}...")
        cookie = {
            'name': name,
            'value': value,
            'path': path,
        }
        if domain:
            cookie['domain'] = domain
        if expiry:
            cookie['expiry'] = expiry
        
        try:
            self.driver.add_cookie(cookie)
            self.logger.debug(f"Cookie设置成功: {name}")
        except Exception as e:
            self.logger.error(f"Cookie设置失败: {e}")
            raise

    def wait_for_page_load(self, timeout: int = 10):
        """
        等待页面加载完成
        
        Args:
            timeout: 超时时间（秒）
        """
        self.logger.debug(f"等待页面加载完成 (timeout={timeout}s)")
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            self.logger.debug("页面加载完成")
        except TimeoutException:
            self.logger.warning(f"页面加载超时 (timeout={timeout}s)")

    def robust_click(self, selector: str, by: str = 'css', retries: int = 3):
        """
        鲁棒性点击 - 三级防御链

        Level 1: 原生 click()
        Level 2: JavaScript 点击
        Level 3: ActionChains 模拟操作

        Args:
            selector: 元素定位器
            by: 定位方式
            retries: 每级重试次数
        """
        self.logger.info(f"鲁棒性点击: {selector}")
        last_exception = None

        # Level 1: 原生点击
        for attempt in range(retries):
            try:
                element = self.find_element(selector, by)
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((self._get_by_mapping(by), selector))
                )
                element.click()
                self.logger.debug(f"Level 1 原生点击成功 (尝试 {attempt + 1})")
                return
            except (WebDriverException, StaleElementReferenceException) as e:
                last_exception = e
                self.logger.debug(f"Level 1 失败 (尝试 {attempt + 1}): {type(e).__name__}")

        # Level 2: JavaScript 点击
        js_code = "arguments[0].click();"
        self.logger.info(f"Fallback: JS注入点击")
        for attempt in range(retries):
            try:
                element = self.find_element(selector, by)
                self.driver.execute_script(js_code, element)
                self.logger.info(f"Level 2 JS点击成功")
                return
            except WebDriverException as e:
                last_exception = e
                self.logger.debug(f"Level 2 失败 (尝试 {attempt + 1}): {type(e).__name__}")
                time.sleep(0.3)

        # Level 3: ActionChains
        self.logger.info(f"Fallback: ActionChains模拟点击")
        for attempt in range(retries):
            try:
                element = self.find_element(selector, by)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((self._get_by_mapping(by), selector))
                )
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()
                self.logger.info(f"Level 3 ActionChains成功")
                return
            except (WebDriverException, StaleElementReferenceException) as e:
                last_exception = e
                self.logger.debug(f"Level 3 失败 (尝试 {attempt + 1}): {type(e).__name__}")
                time.sleep(0.3)

        self.logger.error(f"鲁棒性点击全部失败: {selector}")
        raise last_exception

    def robust_input(self, selector: str, text: str, by: str = 'css', retries: int = 3):
        """
        鲁棒性输入 - 三级防御链

        Level 1: clear() + send_keys()
        Level 2: JS 设置 value + 触发事件
        Level 3: ActionChains 模拟键盘输入

        Args:
            selector: 元素定位器
            text: 输入的文本
            by: 定位方式
            retries: 每级重试次数
        """
        self.logger.info(f"鲁棒性输入到 {selector}: {text[:50]}...")
        last_exception = None

        # Level 1: 原生输入
        for attempt in range(retries):
            try:
                element = self.find_element(selector, by)
                WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((self._get_by_mapping(by), selector))
                )
                element.clear()
                element.send_keys(text)
                self.logger.debug(f"Level 1 原生输入成功 (尝试 {attempt + 1})")
                return
            except (WebDriverException, StaleElementReferenceException) as e:
                last_exception = e
                self.logger.debug(f"Level 1 输入失败 (尝试 {attempt + 1}): {type(e).__name__}")

        # Level 2: JS 设置值
        js_code = (
            "arguments[0].value = arguments[1]; "
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true})); "
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));"
        )
        self.logger.info(f"Fallback: JS注入输入 - 代码: {js_code}")
        for attempt in range(retries):
            try:
                element = self.find_element(selector, by)
                self.driver.execute_script(js_code, element, text)
                self.logger.info(f"Level 2 JS输入成功 (尝试 {attempt + 1})")
                return
            except WebDriverException as e:
                last_exception = e
                self.logger.debug(f"Level 2 输入失败 (尝试 {attempt + 1}): {type(e).__name__}")
                time.sleep(0.3)

        # Level 3: ActionChains 模拟键盘
        self.logger.info(f"Fallback: ActionChains模拟输入")
        for attempt in range(retries):
            try:
                element = self.find_element(selector, by)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((self._get_by_mapping(by), selector))
                )
                actions = ActionChains(self.driver)
                actions.click(element).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL)
                actions.send_keys(Keys.DELETE).send_keys(text).perform()
                self.logger.info(f"Level 3 ActionChains输入成功 (尝试 {attempt + 1})")
                return
            except (WebDriverException, StaleElementReferenceException) as e:
                last_exception = e
                self.logger.debug(f"Level 3 输入失败 (尝试 {attempt + 1}): {type(e).__name__}")
                time.sleep(0.3)

        self.logger.error(f"鲁棒性输入全部失败: {selector}")
        raise last_exception

    @staticmethod
    def _get_by_mapping(by: str) -> By:
        """获取By映射"""
        mapping = {
            'css': By.CSS_SELECTOR,
            'xpath': By.XPATH,
            'id': By.ID,
            'name': By.NAME,
            'class': By.CLASS_NAME,
            'tag_name': By.TAG_NAME,
            'link_text': By.LINK_TEXT,
            'partial_link_text': By.PARTIAL_LINK_TEXT,
        }
        return mapping.get(by.lower(), By.CSS_SELECTOR)
