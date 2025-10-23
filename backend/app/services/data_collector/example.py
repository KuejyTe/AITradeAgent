"""
数据采集服务使用示例

此文件展示如何使用数据采集服务的各个组件
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.okx.client import OKXClient
from app.services.data_collector import (
    MarketDataCollector,
    HistoricalDataCollector,
    DataPipeline,
    DataCache,
    DataQualityMonitor,
    DataCollectorTasks,
    EventBus,
    EventType,
    event_bus
)
from app.services.data_collector.pipeline import (
    DataCleaningProcessor,
    DataNormalizationProcessor,
    TechnicalIndicatorProcessor,
    DataValidationProcessor
)
from app.core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_websocket_collector():
    """示例：使用WebSocket采集实时数据"""
    logger.info("=== WebSocket数据采集示例 ===")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    
    okx_client = OKXClient()
    
    collector = MarketDataCollector(okx_client, db_session)
    
    await collector.start()
    
    await collector.subscribe_ticker(["BTC-USDT", "ETH-USDT"])
    
    await collector.subscribe_candles(["BTC-USDT"], "1m")
    
    await collector.subscribe_order_book(["BTC-USDT"])
    
    logger.info("数据采集已启动，按Ctrl+C停止...")
    
    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        await collector.stop()
        db_session.close()


async def example_historical_collector():
    """示例：采集历史数据"""
    logger.info("=== 历史数据采集示例 ===")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    
    okx_client = OKXClient()
    
    collector = HistoricalDataCollector(okx_client, db_session)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)
    
    saved_count = await collector.fetch_historical_candles(
        instrument_id="BTC-USDT",
        bar="1H",
        start_time=start_time,
        end_time=end_time
    )
    
    logger.info(f"保存了 {saved_count} 条历史K线数据")
    
    filled_count = await collector.backfill_missing_data(
        instrument_id="BTC-USDT",
        bar="1H",
        lookback_days=30
    )
    
    logger.info(f"回填了 {filled_count} 条缺失数据")
    
    db_session.close()


async def example_data_pipeline():
    """示例：使用数据处理管道"""
    logger.info("=== 数据处理管道示例 ===")
    
    pipeline = DataPipeline()
    
    pipeline.add_processor(DataCleaningProcessor(outlier_threshold=3.0))
    pipeline.add_processor(DataNormalizationProcessor(method='minmax'))
    pipeline.add_processor(TechnicalIndicatorProcessor())
    pipeline.add_processor(DataValidationProcessor())
    
    test_data = {
        'candles': [
            {'ts': i * 60000, 'open': 50000 + i * 10, 'high': 50010 + i * 10,
             'low': 49990 + i * 10, 'close': 50005 + i * 10, 'vol': 100}
            for i in range(100)
        ]
    }
    
    result = await pipeline.process(test_data)
    
    logger.info(f"应用的处理器: {result.metadata['processors_applied']}")
    
    if 'indicators' in result.data:
        indicators = result.data['indicators']
        logger.info(f"技术指标: MA_20={indicators.get('ma_20')}, "
                   f"RSI_14={indicators.get('rsi_14')}, "
                   f"MACD={indicators.get('macd')}")
    
    if 'validation' in result.data:
        validation = result.data['validation']
        logger.info(f"数据验证: {validation['is_valid']}, "
                   f"错误数: {len(validation['errors'])}")


async def example_data_cache():
    """示例：使用数据缓存"""
    logger.info("=== 数据缓存示例 ===")
    
    cache = DataCache(redis_url=settings.REDIS_URL)
    await cache.connect()
    
    ticker_data = {
        'last': 50000,
        'bid_px': 49999,
        'ask_px': 50001,
        'vol_24h': 1000000
    }
    await cache.set_ticker("BTC-USDT", ticker_data)
    logger.info("已缓存ticker数据")
    
    cached_ticker = await cache.get_ticker("BTC-USDT")
    logger.info(f"从缓存读取ticker: {cached_ticker}")
    
    for i in range(10):
        candle_data = {
            'ts': i * 60000,
            'open': 50000 + i,
            'high': 50010 + i,
            'low': 49990 + i,
            'close': 50005 + i,
            'vol': 100
        }
        await cache.push_candle("BTC-USDT", "1m", candle_data)
    
    logger.info("已缓存10条K线数据")
    
    cached_candles = await cache.get_candles("BTC-USDT", "1m", limit=5)
    logger.info(f"从缓存读取K线: {len(cached_candles)} 条")
    
    stats = await cache.get_cache_stats("BTC-USDT")
    logger.info(f"缓存统计: {stats}")
    
    await cache.close()


async def example_data_quality_monitor():
    """示例：数据质量监控"""
    logger.info("=== 数据质量监控示例 ===")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    
    monitor = DataQualityMonitor(db_session)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    completeness_result = monitor.check_data_completeness(
        instrument_id="BTC-USDT",
        bar="1H",
        timerange=(start_time, end_time)
    )
    
    logger.info(f"数据完整性: {completeness_result['status']}, "
               f"完整率: {completeness_result.get('completeness_ratio', 0):.2%}")
    
    anomaly_result = monitor.detect_anomalies(
        instrument_id="BTC-USDT",
        bar="1H",
        lookback_hours=24
    )
    
    logger.info(f"异常检测: {anomaly_result['status']}, "
               f"异常数量: {anomaly_result.get('anomaly_count', 0)}")
    
    stats = monitor.get_data_stats(
        instrument_id="BTC-USDT",
        bar="1H",
        lookback_hours=24
    )
    
    logger.info(f"数据统计: {stats}")
    
    db_session.close()


async def example_event_system():
    """示例：事件通知系统"""
    logger.info("=== 事件通知系统示例 ===")
    
    async def on_ticker_update(event):
        data = event.data
        logger.info(f"收到Ticker更新: {data['instrument_id']}")
    
    async def on_candle_update(event):
        data = event.data
        logger.info(f"收到K线更新: {data['instrument_id']} {data['bar']}")
    
    async def on_quality_alert(event):
        data = event.data
        logger.warning(f"数据质量告警: {data['instrument_id']} - {data['message']}")
    
    event_bus.subscribe(on_ticker_update, [EventType.TICKER_UPDATE])
    event_bus.subscribe(on_candle_update, [EventType.CANDLE_UPDATE])
    event_bus.subscribe(on_quality_alert, [EventType.DATA_QUALITY_ALERT])
    
    await event_bus.start()
    
    await event_bus.publish_ticker_update(
        instrument_id="BTC-USDT",
        ticker_data={'last': 50000}
    )
    
    await event_bus.publish_candle_update(
        instrument_id="BTC-USDT",
        bar="1m",
        candle_data={'close': 50005}
    )
    
    await event_bus.publish_data_quality_alert(
        instrument_id="BTC-USDT",
        alert_type="completeness",
        message="数据完整性低于95%",
        details={'completeness_ratio': 0.85}
    )
    
    await asyncio.sleep(1)
    
    await event_bus.stop()


async def example_background_tasks():
    """示例：后台任务"""
    logger.info("=== 后台任务示例 ===")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    
    okx_client = OKXClient()
    
    tasks = DataCollectorTasks(okx_client, db_session)
    
    result = await tasks.run_manual_sync(
        instrument_id="BTC-USDT",
        bar="1H",
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    
    logger.info(f"手动同步完成: {result} 条K线")
    
    quality_result = await tasks.run_manual_quality_check(
        instrument_id="BTC-USDT",
        bar="1H"
    )
    
    logger.info(f"质量检查完成: {quality_result}")
    
    db_session.close()


async def example_complete_workflow():
    """示例：完整的数据采集工作流"""
    logger.info("=== 完整工作流示例 ===")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    
    okx_client = OKXClient()
    
    cache = DataCache(redis_url=settings.REDIS_URL)
    await cache.connect()
    
    async def on_data_received(data):
        """数据回调函数"""
        if data['type'] == 'candle':
            await cache.push_candle(
                data['instrument_id'],
                data['bar'],
                {
                    'ts': data['data'][0],
                    'close': float(data['data'][4])
                }
            )
            logger.info(f"缓存K线: {data['instrument_id']} {data['bar']}")
    
    collector = MarketDataCollector(
        okx_client,
        db_session,
        on_data_callback=on_data_received
    )
    
    await event_bus.start()
    
    await collector.start()
    await collector.subscribe_candles(["BTC-USDT"], "1m")
    
    logger.info("等待数据...")
    await asyncio.sleep(60)
    
    await collector.stop()
    await event_bus.stop()
    await cache.close()
    db_session.close()
    
    logger.info("工作流完成")


async def main():
    """主函数"""
    print("选择要运行的示例:")
    print("1. WebSocket实时数据采集")
    print("2. 历史数据采集")
    print("3. 数据处理管道")
    print("4. 数据缓存")
    print("5. 数据质量监控")
    print("6. 事件通知系统")
    print("7. 后台任务")
    print("8. 完整工作流")
    
    choice = input("请输入选项 (1-8): ")
    
    examples = {
        '1': example_websocket_collector,
        '2': example_historical_collector,
        '3': example_data_pipeline,
        '4': example_data_cache,
        '5': example_data_quality_monitor,
        '6': example_event_system,
        '7': example_background_tasks,
        '8': example_complete_workflow
    }
    
    if choice in examples:
        await examples[choice]()
    else:
        logger.error("无效选项")


if __name__ == "__main__":
    asyncio.run(main())
