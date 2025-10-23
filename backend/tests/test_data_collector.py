import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.data_collector import (
    MarketDataCollector,
    HistoricalDataCollector,
    DataPipeline,
    DataCache,
    DataQualityMonitor,
    EventBus,
    EventType
)
from app.services.data_collector.pipeline import (
    DataCleaningProcessor,
    DataNormalizationProcessor,
    TechnicalIndicatorProcessor,
    DataValidationProcessor
)


@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def mock_okx_client():
    """模拟OKX客户端"""
    client = Mock()
    client.api_key = "test_key"
    client.secret_key = "test_secret"
    client.passphrase = "test_pass"
    return client


@pytest.mark.asyncio
async def test_market_data_collector_initialization(mock_okx_client, mock_db_session):
    """测试市场数据采集器初始化"""
    collector = MarketDataCollector(mock_okx_client, mock_db_session)
    
    assert collector.okx_client == mock_okx_client
    assert collector.db_session == mock_db_session
    assert collector.subscriptions == {}
    assert collector.ws is None


@pytest.mark.asyncio
async def test_historical_collector_initialization(mock_okx_client, mock_db_session):
    """测试历史数据采集器初始化"""
    collector = HistoricalDataCollector(mock_okx_client, mock_db_session)
    
    assert collector.okx_client == mock_okx_client
    assert collector.db_session == mock_db_session
    assert collector.market is not None


@pytest.mark.asyncio
async def test_data_pipeline():
    """测试数据处理管道"""
    pipeline = DataPipeline()
    
    pipeline.add_processor(DataCleaningProcessor())
    pipeline.add_processor(DataValidationProcessor())
    
    assert len(pipeline.processors) == 2
    
    test_data = {
        'candles': [
            {'open': 100, 'high': 105, 'low': 95, 'close': 102, 'vol': 1000},
            {'open': 102, 'high': 108, 'low': 100, 'close': 105, 'vol': 1200}
        ]
    }
    
    result = await pipeline.process(test_data)
    
    assert result.data is not None
    assert result.metadata is not None
    assert len(result.metadata['processors_applied']) == 2


def test_data_cleaning_processor():
    """测试数据清洗处理器"""
    processor = DataCleaningProcessor(outlier_threshold=3.0)
    
    candles = [
        {'close': 100},
        {'close': 101},
        {'close': 102},
        {'close': 1000},  # 异常值
        {'close': 103}
    ]
    
    cleaned = processor._remove_outliers(candles)
    
    assert len(cleaned) < len(candles)


def test_technical_indicator_processor():
    """测试技术指标处理器"""
    processor = TechnicalIndicatorProcessor()
    
    import numpy as np
    prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])
    
    ma_5 = processor._calculate_ma(prices, 5)
    assert ma_5 is not None
    
    ema_5 = processor._calculate_ema(prices, 5)
    assert ema_5 is not None
    
    rsi = processor._calculate_rsi(prices, 10)
    assert rsi is not None
    assert 0 <= rsi <= 100


@pytest.mark.asyncio
async def test_event_bus():
    """测试事件总线"""
    event_bus = EventBus()
    
    received_events = []
    
    async def event_handler(event):
        received_events.append(event)
    
    event_bus.subscribe(event_handler, [EventType.TICKER_UPDATE])
    
    await event_bus.start()
    
    await event_bus.publish_ticker_update(
        instrument_id="BTC-USDT",
        ticker_data={'last': 50000}
    )
    
    await asyncio.sleep(0.1)
    
    assert len(received_events) > 0
    assert received_events[0].event_type == EventType.TICKER_UPDATE
    
    await event_bus.stop()


@pytest.mark.asyncio
async def test_data_cache_connection():
    """测试数据缓存连接"""
    with patch('redis.asyncio.from_url') as mock_redis:
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_redis.return_value = mock_client
        
        cache = DataCache(redis_url="redis://localhost:6379")
        await cache.connect()
        
        assert cache.redis_client is not None
        mock_client.ping.assert_called_once()


def test_data_quality_monitor_initialization(mock_db_session):
    """测试数据质量监控器初始化"""
    monitor = DataQualityMonitor(mock_db_session)
    
    assert monitor.db_session == mock_db_session


def test_data_validation_processor():
    """测试数据验证处理器"""
    processor = DataValidationProcessor()
    
    valid_candle = {'open': 100, 'high': 105, 'low': 95, 'close': 102}
    errors = processor._validate_candle(valid_candle, 0)
    assert len(errors) == 0
    
    invalid_candle = {'open': 100, 'high': 95, 'low': 105, 'close': 102}
    errors = processor._validate_candle(invalid_candle, 0)
    assert len(errors) > 0


def test_macd_calculation():
    """测试MACD指标计算"""
    processor = TechnicalIndicatorProcessor()
    
    import numpy as np
    prices = np.array([i + 100 for i in range(50)])
    
    macd_data = processor._calculate_macd(prices)
    
    assert 'macd' in macd_data
    assert 'macd_signal' in macd_data
    assert 'macd_histogram' in macd_data
    
    if macd_data['macd'] is not None:
        assert isinstance(macd_data['macd'], float)


@pytest.mark.asyncio
async def test_data_normalization_processor():
    """测试数据归一化处理器"""
    processor = DataNormalizationProcessor(method='minmax')
    
    test_data = {
        'candles': [
            {'open': 100, 'high': 105, 'low': 95, 'close': 102},
            {'open': 102, 'high': 108, 'low': 98, 'close': 106},
            {'open': 106, 'high': 112, 'low': 104, 'close': 110}
        ]
    }
    
    result = await processor.process(test_data)
    
    assert 'normalized_candles' in result
    assert len(result['normalized_candles']) == 3
    
    first_normalized = result['normalized_candles'][0]
    assert 'normalized_close' in first_normalized


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
