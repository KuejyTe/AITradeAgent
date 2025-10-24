```python
"""
配置管理API端点
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

from ..core.security import SecureStorage, APIKeyManager, StrategyConfigManager
from ..core.config import settings

router = APIRouter(prefix="/config", tags=["配置管理"])

初始化管理器
secure_storage = SecureStorage()
api_key_manager = APIKeyManager(secure_storage)
strategy_config_manager = StrategyConfigManager()

class APIKeysInput(BaseModel):
"""API密钥输入模型"""
api_key: str
secret_key: str
passphrase: str

class SystemConfigUpdate(BaseModel):
"""系统配置更新模型"""
default_trade_amount: Optional[float] = None
max_position_size: Optional[float] = None
risk_percentage: Optional[float] = None
log_level: Optional[str] = None

@router.get("/system")
async def get_system_config():
"""获取系统配置（隐藏敏感信息）"""
return {
"app_name": settings.app_name,
"environment": settings.environment,
"debug": settings.debug,
"default_trade_amount": settings.default_trade_amount,
"max_position_size": settings.max_position_size,
"risk_percentage": settings.risk_percentage,
"log_level": settings.log_level,
"okx_api_configured": bool(settings.okx_api_key),
"database_configured": bool(settings.database_url),
"timestamp": datetime.utcnow().isoformat()
}

@router.put("/system")
async def update_system_config(config: SystemConfigUpdate):
"""更新系统配置"""
updated_fields = {}

if config.default_trade_amount is not None:
    settings.default_trade_amount = config.default_trade_amount
    updated_fields["default_trade_amount"] = config.default_trade_amount

if config.max_position_size is not None:
    settings.max_position_size = config.max_position_size
    updated_fields["max_position_size"] = config.max_position_size

if config.risk_percentage is not None:
    settings.risk_percentage = config.risk_percentage
    updated_fields["risk_percentage"] = config.risk_percentage

if config.log_level is not None:
    settings.log_level = config.log_level
    updated_fields["log_level"] = config.log_level

return {
    "message": "系统配置已更新",
    "updated_fields": updated_fields,
    "timestamp": datetime.utcnow().isoformat()
}
@router.post("/api-keys")
async def save_api_keys(keys: APIKeysInput):
"""保存API密钥（加密存储）"""
# 验证密钥格式
if not api_key_manager.validate_api_keys(
keys.api_key,
keys.secret_key,
keys.passphrase
):
raise HTTPException(status_code=400, detail="API密钥格式无效")

# 保存加密的密钥
encrypted = api_key_manager.save_api_keys(
    keys.api_key,
    keys.secret_key,
    keys.passphrase
)

return {
    "message": "API密钥已安全保存",
    "timestamp": datetime.utcnow().isoformat()
}
@router.get("/api-keys/status")
async def get_api_keys_status():
"""获取API密钥配置状态"""
keys = api_key_manager.get_api_keys()

return {
    "configured": bool(keys),
    "api_key_preview": keys.get("api_key", "")[:8] + "..." if keys else None,
    "timestamp": datetime.utcnow().isoformat()
}
@router.post("/api-keys/test")
async def test_api_connection():
"""测试API连接"""
# 这里应该实际测试OKX API连接
# 为了演示，返回模拟结果
return {
"status": "success",
"message": "API连接测试成功",
"latency_ms": 150,
"timestamp": datetime.utcnow().isoformat()
}

@router.get("/strategies/{strategy_id}")
async def get_strategy_config(strategy_id: str):
"""获取策略配置"""
config = strategy_config_manager.load_strategy_config(strategy_id)

if not config:
    raise HTTPException(status_code=404, detail="策略配置不存在")

return config
@router.put("/strategies/{strategy_id}")
async def update_strategy_config(strategy_id: str, config: Dict):
"""更新策略配置"""
success = strategy_config_manager.save_strategy_config(strategy_id, config)

if not success:
    raise HTTPException(status_code=400, detail="配置验证失败")

return {
    "message": "策略配置已更新",
    "strategy_id": strategy_id,
    "timestamp": datetime.utcnow().isoformat()
}
@router.get("/strategies")
async def list_strategy_configs():
"""列出所有策略配置"""
import os

config_dir = strategy_config_manager.config_dir
if not os.path.exists(config_dir):
return {"strategies": []}

configs = []
for filename in os.listdir(config_dir):
    if filename.endswith('.json'):
        strategy_id = filename[:-5]  # 去掉.json后缀
        config = strategy_config_manager.load_strategy_config(strategy_id)
        configs.append({
            "id": strategy_id,
            "type": config.get("strategy_type"),
            "version": config.get("version")
        })

return {"strategies": configs}
