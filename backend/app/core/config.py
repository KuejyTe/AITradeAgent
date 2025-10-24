from pydantic_settings import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "AITradeAgent"
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    # 欧易API
    okx_api_key: str = Field("", env="OKX_API_KEY")
    okx_secret_key: str = Field("", env="OKX_SECRET_KEY")
    okx_passphrase: str = Field("", env="OKX_PASSPHRASE")
    okx_api_base_url: str = Field("https://www.okx.com", env="OKX_API_BASE_URL")
    okx_ws_public_url: str = Field("wss://ws.okx.com:8443/ws/v5/public", env="OKX_WS_PUBLIC_URL")
    okx_ws_private_url: str = Field("wss://ws.okx.com:8443/ws/v5/private", env="OKX_WS_PRIVATE_URL")
    
    # 数据库配置
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(20, env="DB_MAX_OVERFLOW")
    db_echo: bool = Field(False, env="DB_ECHO")
    
    # Redis配置（可选）
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    
    # 安全配置
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
    
    # 日志配置
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/app.log", env="LOG_FILE")
    
    # 交易配置
    default_trade_amount: float = Field(100, env="DEFAULT_TRADE_AMOUNT")
    max_position_size: float = Field(10000, env="MAX_POSITION_SIZE")
    risk_percentage: float = Field(0.02, env="RISK_PERCENTAGE")

    class Config:
        env_file = ".env"
    case_sensitive = False
    
    全局配置实例
    settings = Settings()
