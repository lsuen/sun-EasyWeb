"""
测试执行器 - 运行数据驱动的测试用例
"""
import os
import time
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

from core.engine import Engine
from drivers.data_driver import DataDriver
from utils.logger import get_logger


class TestResult:
    """测试结果"""
    
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.start_time = None
        self.end_time = None
    
    def add_pass(self):
        self.passed += 1
    
    def add_fail(self, error: str):
        self.failed += 1
        self.errors.append(error)
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
    
    def summary(self) -> str:
        return (
            f"\n{'='*50}\n"
            f"测试执行报告\n"
            f"{'='*50}\n"
            f"总计: {self.total} | 通过: {self.passed} | 失败: {self.failed}\n"
            f"耗时: {self.duration:.2f} 秒\n"
            f"{'='*50}"
        )


class TestRunner:
    """测试执行器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger('TestRunner')
        self.result = TestResult()
        self.screenshot_dir = 'screenshots'
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def run(self, data_path: str, test_func: Callable, context: Optional[Dict[str, Any]] = None):
        """
        运行数据驱动测试
        
        Args:
            data_path: 数据文件路径 (Excel/JSON)
            test_func: 测试函数，接收 (engine, data_row) 参数
            context: 上下文变量，用于替换数据中的占位符
        """
        # 加载数据
        data_driver = DataDriver(data_path)
        data = data_driver.load()
        
        # 设置上下文
        if context is None:
            context = {'base_url': self.config.get('base_url', '')}
        
        # 初始化引擎
        engine = Engine.get_engine(self.config)
        
        self.result = TestResult()
        self.result.total = len(data)
        self.result.start_time = datetime.now()
        
        self.logger.info(f"开始执行测试: {len(data)} 条用例")
        self.logger.info(f"引擎: {self.config.get('engine')}, 浏览器: {self.config.get('browser')}")
        
        # 执行测试
        for index, row in enumerate(data, 1):
            # 替换占位符
            row = DataDriver.replace_placeholders(row, context)
            
            test_name = row.get('test_name', f'用例 {index}')
            self.logger.info(f"\n[{index}/{self.result.total}] 执行: {test_name}")
            
            try:
                engine.start()
                test_func(engine, row)
                engine.quit()
                self.result.add_pass()
                self.logger.info(f"✓ {test_name} 通过")
                
            except Exception as e:
                self.result.add_fail(f"{test_name}: {str(e)}")
                self.logger.error(f"✗ {test_name} 失败: {e}")
                
                # 失败时截图
                try:
                    screenshot_path = os.path.join(
                        self.screenshot_dir,
                        f"fail_{test_name}_{int(time.time())}.png"
                    )
                    engine.screenshot(screenshot_path)
                    self.logger.info(f"截图已保存: {screenshot_path}")
                except:
                    pass
                
                try:
                    engine.quit()
                except:
                    pass
        
        self.result.end_time = datetime.now()
        
        # 输出报告
        print(self.result.summary())
        
        if self.result.errors:
            self.logger.warning("\n失败用例:")
            for error in self.result.errors:
                self.logger.warning(f"  - {error}")
        
        return self.result
