"""
配置加载器 - 支持YAML/JSON配置
"""
import os
import json
from typing import Dict, Any, Optional

from utils.logger import get_logger


class ConfigLoader:
    """配置加载器"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        'engine': 'selenium',
        'browser': 'chrome',
        'base_url': '',
        'headless': False,
        'timeout': 10,
        'window_size': None,
        'log_level': 'INFO',
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger('ConfigLoader')
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path and os.path.exists(config_path):
            self.load(config_path)
        elif config_path:
            self.logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        self.logger.info(f"加载配置文件: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                self.config.update(self._load_yaml(f))
            elif config_path.endswith('.json'):
                self.config.update(json.load(f))
            else:
                raise ValueError(f"不支持的配置格式: {config_path}")
        
        self.logger.info(f"配置加载成功: engine={self.config['engine']}, browser={self.config['browser']}")

        from utils.env_loader import apply_env_to_config
        self.config = apply_env_to_config(self.config)

        return self.config
    
    def _load_yaml(self, file) -> Dict[str, Any]:
        """加载YAML配置"""
        import yaml
        return yaml.safe_load(file) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        return self.config[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.config
    
    def update(self, updates: Dict[str, Any]):
        """更新配置"""
        self.config.update(updates)
        self.logger.debug(f"配置已更新: {list(updates.keys())}")
