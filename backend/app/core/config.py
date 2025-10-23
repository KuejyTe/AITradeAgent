from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "AITradeAgent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # WebSocket
    WS_MESSAGE_QUEUE_SIZE: int = 100
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # OKX API Configuration
    OKX_API_KEY: Optional[str] = None
    OKX_SECRET_KEY: Optional[str] = None
    OKX_PASSPHRASE: Optional[str] = None
    OKX_API_BASE_URL: str = "https://www.okx.com"
    OKX_WS_PUBLIC_URL: str = "wss://ws.okx.com:8443/ws/v5/public"
    OKX_WS_PRIVATE_URL: str = "wss://ws.okx.com:8443/ws/v5/private"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # Data Collector Configuration
    DATA_COLLECTOR_CONFIG: dict = {
        "instruments": ["BTC-USDT", "ETH-USDT", "BNB-USDT"],
        "candle_bars": ["1m", "5m", "15m", "1H", "1D"],
        "enable_order_book": True,
        "cache_enabled": True,
        "retention_days": 90
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
