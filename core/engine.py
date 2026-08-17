"""
引擎抽象层 - 定义统一的Web自动化接口

作者：孙文龙 | 许可证：MIT
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from utils.logger import get_logger


class BaseEngine(ABC):
    """Web自动化引擎基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver = None
        self.logger = get_logger(self.__class__.__name__)
        
    @abstractmethod
    def start(self):
        """启动浏览器"""
        pass
    
    @abstractmethod
    def quit(self):
        """关闭浏览器"""
        pass
    
    @abstractmethod
    def open(self, url: str):
        """打开URL"""
        pass
    
    @abstractmethod
    def click(self, selector: str, by: str = 'css'):
        """点击元素"""
        pass
    
    @abstractmethod
    def input(self, selector: str, text: str, by: str = 'css'):
        """输入文本"""
        pass
    
    @abstractmethod
    def get_text(self, selector: str, by: str = 'css') -> str:
        """获取元素文本"""
        pass
    
    @abstractmethod
    def find_element(self, selector: str, by: str = 'css'):
        """查找元素"""
        pass
    
    @abstractmethod
    def find_elements(self, selector: str, by: str = 'css') -> list:
        """查找多个元素"""
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """获取页面标题"""
        pass
    
    @abstractmethod
    def get_current_url(self) -> str:
        """获取当前URL"""
        pass
    
    @abstractmethod
    def screenshot(self, filepath: str):
        """截图"""
        pass
    
    @abstractmethod
    def wait_for_element(self, selector: str, by: str = 'css', timeout: int = 10):
        """等待元素出现"""
        pass
    
    def execute_script(self, script: str, *args) -> Any:
        """执行JavaScript"""
        self.logger.warning(f"execute_script not implemented for {self.__class__.__name__}")
        return None

    def set_cookie(self, name: str, value: str, domain: str = None, path: str = '/', expiry: int = None):
        """设置Cookie"""
        self.logger.warning(f"set_cookie not implemented for {self.__class__.__name__}")
        return None

    def wait_for_page_load(self, timeout: int = 10):
        """等待页面加载完成"""
        self.logger.warning(f"wait_for_page_load not implemented for {self.__class__.__name__}")
        return None


class Engine:
    """引擎工厂类"""
    
    _engines = {
        'selenium': None,  # 延迟导入
        'playwright': None,
    }
    
    @classmethod
    def get_engine(cls, config: Dict[str, Any]) -> BaseEngine:
        """根据配置获取引擎实例"""
        engine_type = config.get('engine', 'selenium').lower()
        
        if engine_type == 'selenium':
            from core.selenium_engine import SeleniumEngine
            return SeleniumEngine(config)
        elif engine_type == 'playwright':
            from core.playwright_engine import PlaywrightEngine
            return PlaywrightEngine(config)
        else:
            raise ValueError(f"不支持的引擎类型: {engine_type}")
