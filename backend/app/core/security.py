"""
安全相关功能：加密存储、API密钥管理
"""

from cryptography.fernet import Fernet
from typing import Dict, Optional
import base64
import os


class SecureStorage:
    """加密存储服务"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        初始化加密存储
        
        Args:
            encryption_key: 加密密钥，如果为None则从环境变量读取
        """
        if encryption_key is None:
            encryption_key = os.getenv("ENCRYPTION_KEY")
            if not encryption_key:
                # 如果环境变量也没有，生成一个新的
                encryption_key = self.generate_key()
                print(f"Generated new encryption key: {encryption_key}")
                print("Please save this key to your .env file as ENCRYPTION_KEY")
        
        self.cipher = Fernet(encryption_key.encode())
    
    def encrypt(self, data: str) -> str:
        """
        加密数据
        
        Args:
            data: 要加密的字符串
            
        Returns:
            加密后的字符串
        """
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的字符串
            
        Returns:
            解密后的原始字符串
        """
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    @staticmethod
    def generate_key() -> str:
        """
        生成新的加密密钥
        
        Returns:
            Base64编码的密钥字符串
        """
        return Fernet.generate_key().decode()


class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self, storage: SecureStorage):
        """
        初始化API密钥管理器
Args:
storage: SecureStorage实例
"""
self.storage = storage
self._cached_keys: Optional[Dict[str, str]] = None

def save_api_keys(
    self,
    api_key: str,
    secret_key: str,
    passphrase: str
) -> Dict[str, str]:
    """
    保存加密的API密钥
    
    Args:
        api_key: OKX API Key
        secret_key: OKX Secret Key
        passphrase: OKX Passphrase
        
    Returns:
        加密后的密钥字典
    """
    encrypted_keys = {
        "api_key": self.storage.encrypt(api_key),
        "secret_key": self.storage.encrypt(secret_key),
        "passphrase": self.storage.encrypt(passphrase)
    }
    
    # 这里应该保存到数据库或配置文件
    # 为了演示，我们只返回加密结果
    self._cached_keys = encrypted_keys
    
    return encrypted_keys

def get_api_keys(self) -> Dict[str, str]:
    """
    获取并解密API密钥
    
    Returns:
        解密后的密钥字典
    """
    if self._cached_keys is None:
        # 这里应该从数据库或配置文件读取
        # 为了演示，返回空字典
        return {}
    
    return {
        "api_key": self.storage.decrypt(self._cached_keys["api_key"]),
        "secret_key": self.storage.decrypt(self._cached_keys["secret_key"]),
        "passphrase": self.storage.decrypt(self._cached_keys["passphrase"])
    }

def validate_api_keys(self, api_key: str, secret_key: str, passphrase: str) -> bool:
    """
    验证API密钥格式
    
    Args:
        api_key: API Key
        secret_key: Secret Key
        passphrase: Passphrase
        
    Returns:
        是否有效
    """
    # 基础格式验证
    if not all([api_key, secret_key, passphrase]):
        return False
    
    # OKX API Key通常是32位字符
    if len(api_key) < 20:
        return False
        
    return True
class StrategyConfigManager:
"""策略配置管理器"""

def __init__(self, config_dir: str = "configs/strategies"):
    """
    初始化策略配置管理器
    
    Args:
        config_dir: 配置文件目录
    """
    self.config_dir = config_dir
    os.makedirs(config_dir, exist_ok=True)

def load_strategy_config(self, strategy_id: str) -> Dict:
    """
    加载策略配置
    
    Args:
        strategy_id: 策略ID
        
    Returns:
        策略配置字典
    """
    import json
    config_path = os.path.join(self.config_dir, f"{strategy_id}.json")
    
    if not os.path.exists(config_path):
        return self.get_default_config(strategy_id)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_strategy_config(self, strategy_id: str, config: Dict) -> bool:
    """
    保存策略配置
    
    Args:
        strategy_id: 策略ID
        config: 配置字典
        
    Returns:
        是否保存成功
    """
    import json
    
    if not self.validate_config(config):
        return False
    
    config_path = os.path.join(self.config_dir, f"{strategy_id}.json")
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return True

def validate_config(self, config: Dict) -> bool:
    """
    验证配置有效性
    
    Args:
        config: 配置字典
        
    Returns:
        是否有效
    """
    required_fields = ["strategy_type", "parameters"]
    return all(field in config for field in required_fields)

def get_default_config(self, strategy_type: str) -> Dict:
    """
    获取默认配置
    
    Args:
        strategy_type: 策略类型
        
    Returns:
        默认配置字典
    """
    defaults = {
        "sma_crossover": {
            "strategy_type": "sma_crossover",
            "version": "1.0",
            "parameters": {
                "fast_period": 10,
                "slow_period": 30,
                "instrument_id": "BTC-USDT",
                "timeframe": "1H"
            },
            "risk_management": {
                "max_
position_size": 1.0,
"stop_loss_pct": 0.05,
"take_profit_pct": 0.10,
"max_daily_loss": 0.10
},
"execution": {
"order_type": "limit",
"slippage_tolerance": 0.001
}
}
}

    return defaults.get(strategy_type,
{})
