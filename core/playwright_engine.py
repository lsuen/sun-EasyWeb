"""
Playwright 引擎实现
"""
from typing import Optional, Dict, List, Any
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from core.engine import BaseEngine
from utils.logger import get_logger


class PlaywrightEngine(BaseEngine):
    """Playwright Web自动化引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger('PlaywrightEngine')
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None
    
    def start(self):
        """启动浏览器"""
        browser_type = self.config.get('browser', 'chromium').lower()
        self.logger.info(f"启动 {browser_type} 浏览器 (Playwright)...")
        
        self._playwright = sync_playwright().start()
        
        browser_mapping = {
            'chrome': 'chromium',
            'chromium': 'chromium',
            'firefox': 'firefox',
            'webkit': 'webkit',
        }
        browser_name = browser_mapping.get(browser_type, 'chromium')
        
        launch_options = {
            'headless': self.config.get('headless', False),
        }
        
        # 自定义浏览器路径
        browser_path = self.config.get('browser_path') or self.config.get('playwright_browser_path')
        if browser_path:
            launch_options['executable_path'] = browser_path
            self.logger.info(f"使用自定义浏览器路径: {browser_path}")
        
        if browser_name == 'chromium':
            self._browser = getattr(self._playwright, browser_name).launch(**launch_options)
        else:
            self._browser = getattr(self._playwright, browser_name).launch(**launch_options)
        
        self._context = self._browser.new_context(
            viewport={'width': 1280, 'height': 720} if self.config.get('window_size') else None
        )
        self.driver = self._context.new_page()
        self.logger.info(f"浏览器启动成功: {browser_name}")
    
    def quit(self):
        """关闭浏览器"""
        if self._browser:
            self.logger.info("关闭浏览器 (Playwright)...")
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self.driver = None
        self._browser = None
        self._playwright = None
    
    def open(self, url: str):
        """打开URL"""
        self.logger.info(f"打开URL: {url}")
        self.driver.goto(url)
    
    def click(self, selector: str, by: str = 'css'):
        """点击元素"""
        element = self._get_locator(selector, by)
        self.logger.info(f"点击元素: {selector}")
        element.click()
    
    def input(self, selector: str, text: str, by: str = 'css'):
        """输入文本"""
        element = self._get_locator(selector, by)
        self.logger.info(f"输入文本到 {selector}: {text[:50]}...")
        element.fill(text)
    
    def get_text(self, selector: str, by: str = 'css') -> str:
        """获取元素文本"""
        element = self._get_locator(selector, by)
        text = element.text_content()
        self.logger.debug(f"获取文本 {selector}: {text[:50]}")
        return text or ''
    
    def find_element(self, selector: str, by: str = 'css'):
        """查找元素 - 返回 Playwright Locator"""
        return self._get_locator(selector, by)
    
    def find_elements(self, selector: str, by: str = 'css') -> list:
        """查找多个元素"""
        locator = self._get_locator(selector, by)
        return locator.all()
    
    def get_title(self) -> str:
        """获取页面标题"""
        return self.driver.title()
    
    def get_current_url(self) -> str:
        """获取当前URL"""
        return self.driver.url
    
    def screenshot(self, filepath: str):
        """截图"""
        self.logger.info(f"截图保存到: {filepath}")
        self.driver.screenshot(path=filepath)
    
    def wait_for_element(self, selector: str, by: str = 'css', timeout: int = 10):
        """等待元素出现"""
        self.logger.debug(f"等待元素: {selector}")
        locator = self._get_locator(selector, by)
        locator.wait_for(state='visible', timeout=timeout * 1000)
        return locator
    
    def execute_script(self, script: str, *args) -> Any:
        """执行JavaScript"""
        self.logger.debug(f"执行JS: {script[:50]}...")
        return self.driver.evaluate(script, *args)
    
    def _get_locator(self, selector: str, by: str):
        """获取 Playwright Locator"""
        by_lower = by.lower()
        if by_lower == 'xpath':
            return self.driver.locator(f'xpath={selector}')
        elif by_lower == 'link_text' or by_lower == 'partial_link_text':
            # Playwright 使用 get_by_text 处理链接文本
            return self.driver.get_by_text(selector, exact=(by_lower == 'link_text'))
        elif by_lower == 'tag_name':
            # Playwright 使用 css 选择器匹配标签
            return self.driver.locator(selector)
        elif by_lower == 'text':
            return self.driver.get_by_text(selector)
        else:  # css, id, name, class 都用CSS选择器
            return self.driver.locator(selector)
