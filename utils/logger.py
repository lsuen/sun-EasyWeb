"""
日志系统 - 控制台+文件双输出
"""
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


class Logger:
    """日志管理器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str = 'EasyWeb', log_dir: str = 'logs', 
                   level: str = 'INFO', max_bytes: int = 10 * 1024 * 1024, 
                   backup_count: int = 5):
        """获取或创建日志器"""
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # 避免重复添加handler
        if logger.handlers:
            return logger
        
        # 日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 日志文件名
        log_file = os.path.join(log_dir, f'{name}_{datetime.now().strftime("%Y%m%d")}.log')
        
        # 格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件Handler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 控制台Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        cls._loggers[name] = logger
        return logger


def get_logger(name: str = 'EasyWeb') -> logging.Logger:
    """快捷获取日志器"""
    return Logger.get_logger(name)
