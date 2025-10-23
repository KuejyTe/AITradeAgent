"""
数据采集服务完整集成示例

展示如何将所有组件集成到一个完整的系统中
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.services.okx.client import OKXClient
from app.services.data_collector import (
    MarketDataCollector,
    HistoricalDataCollector,
    DataCache,
    DataQualityMonitor,
    DataCollectorTasks,
    event_bus,
    EventType
)
from app.core.config import settings
from app.core.database import get_session_local, init_db


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCollectionSystem:
    """数据采集系统 - 集成所有组件"""

    def __init__(
        self,
        okx_api_key: Optional[str] = None,
        okx_secret_key: Optional[str] = None,
        okx_passphrase: Optional[str] = None
    ):
        """
        初始化数据采集系统

        Args:
            okx_api_key: OKX API Key
            okx_secret_key: OKX Secret Key
            okx_passphrase: OKX Passphrase
        """
        self.okx_client = OKXClient(
            api_key=okx_api_key or settings.OKX_API_KEY,
            secret_key=okx_secret_key or settings.OKX_SECRET_KEY,
            passphrase=okx_passphrase or settings.OKX_PASSPHRASE
        )

        SessionLocal = get_session_local()
        self.db_session = SessionLocal()

        self.cache: Optional[DataCache] = None
        if settings.DATA_COLLECTOR_CONFIG.get("cache_enabled"):
            self.cache = DataCache(redis_url=settings.REDIS_URL)

        self.collector: Optional[MarketDataCollector] = None
        self.historical_collector = HistoricalDataCollector(
            self.okx_client,
            self.db_session
        )
        self.monitor = DataQualityMonitor(self.db_session)
        self.tasks = DataCollectorTasks(self.okx_client, self.db_session)

        self._running = False

    async def start(self):
        """启动数据采集系统"""
        if self._running:
            logger.warning("System already running")
            return

        logger.info("Starting Data Collection System")

        if self.cache:
            await self.cache.connect()
            logger.info("Cache connected")

        await event_bus.start()
        logger.info("Event bus started")

        self._setup_event_handlers()

        self.collector = MarketDataCollector(
            self.okx_client,
            self.db_session,
            on_data_callback=self._handle_new_data
        )

        await self.collector.start()
        logger.info("WebSocket collector started")

        instruments = settings.DATA_COLLECTOR_CONFIG.get("instruments", [])
        candle_bars = settings.DATA_COLLECTOR_CONFIG.get("candle_bars", [])

        await self.collector.subscribe_ticker(instruments)
        logger.info(f"Subscribed to tickers: {instruments}")

        for bar in candle_bars:
            await self.collector.subscribe_candles(instruments, bar)
            logger.info(f"Subscribed to {bar} candles: {instruments}")

        if settings.DATA_COLLECTOR_CONFIG.get("enable_order_book"):
            await self.collector.subscribe_order_book(instruments)
            logger.info(f"Subscribed to order books: {instruments}")

        await self.tasks.start()
        logger.info("Background tasks started")

        self._running = True
        logger.info("Data Collection System started successfully")

    async def stop(self):
        """停止数据采集系统"""
        logger.info("Stopping Data Collection System")
        self._running = False

        if self.collector:
            await self.collector.stop()
            logger.info("WebSocket collector stopped")

        await self.tasks.stop()
        logger.info("Background tasks stopped")

        await event_bus.stop()
        logger.info("Event bus stopped")

        if self.cache:
            await self.cache.close()
            logger.info("Cache closed")

        self.db_session.close()
        logger.info("Database session closed")

        logger.info("Data Collection System stopped")

    def _setup_event_handlers(self):
        """设置事件处理器"""
        event_bus.subscribe(self._on_ticker_update, [EventType.TICKER_UPDATE])
        event_bus.subscribe(self._on_candle_update, [EventType.CANDLE_UPDATE])
        event_bus.subscribe(
            self._on_data_quality_alert,
            [EventType.DATA_QUALITY_ALERT]
        )
        event_bus.subscribe(
            self._on_anomaly_detected,
            [EventType.ANOMALY_DETECTED]
        )

    async def _handle_new_data(self, data: dict):
        """处理新到达的数据"""
        try:
            data_type = data.get('type')
            instrument_id = data.get('instrument_id')

            if data_type == 'ticker' and self.cache:
                ticker_data = data.get('data', {})
                await self.cache.set_ticker(instrument_id, ticker_data)
                await event_bus.publish_ticker_update(instrument_id, ticker_data)

            elif data_type == 'candle' and self.cache:
                bar = data.get('bar')
                candle_data = data.get('data', [])
                
                if len(candle_data) >= 9:
                    candle_dict = {
                        'ts': int(candle_data[0]),
                        'open': float(candle_data[1]),
                        'high': float(candle_data[2]),
                        'low': float(candle_data[3]),
                        'close': float(candle_data[4]),
                        'vol': float(candle_data[5])
                    }
                    await self.cache.push_candle(instrument_id, bar, candle_dict)
                    await event_bus.publish_candle_update(
                        instrument_id, bar, candle_dict
                    )

        except Exception as e:
            logger.error(f"Error handling new data: {e}", exc_info=True)

    async def _on_ticker_update(self, event):
        """处理行情更新事件"""
        data = event.data
        logger.debug(
            f"Ticker update: {data['instrument_id']} = "
            f"{data['ticker'].get('last', 'N/A')}"
        )

    async def _on_candle_update(self, event):
        """处理K线更新事件"""
        data = event.data
        logger.debug(
            f"Candle update: {data['instrument_id']} {data['bar']} = "
            f"{data['candle'].get('close', 'N/A')}"
        )

    async def _on_data_quality_alert(self, event):
        """处理数据质量告警事件"""
        data = event.data
        logger.warning(
            f"Data quality alert: {data['instrument_id']} - "
            f"{data['alert_type']}: {data['message']}"
        )

    async def _on_anomaly_detected(self, event):
        """处理异常检测事件"""
        data = event.data
        logger.warning(
            f"Anomaly detected: {data['instrument_id']} {data['bar']}"
        )

    async def get_system_status(self) -> dict:
        """获取系统状态"""
        status = {
            'running': self._running,
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'websocket_collector': self.collector is not None and self._running,
                'event_bus': event_bus._running,
                'cache': self.cache is not None and self.cache.redis_client is not None,
                'database': self.db_session is not None
            }
        }

        if self.cache:
            instruments = settings.DATA_COLLECTOR_CONFIG.get("instruments", [])
            cache_stats = {}
            for inst_id in instruments:
                cache_stats[inst_id] = await self.cache.get_cache_stats(inst_id)
            status['cache_stats'] = cache_stats

        return status

    async def sync_historical_data(
        self,
        instrument_id: str,
        bar: str,
        days: int = 7
    ) -> int:
        """
        同步历史数据

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            days: 回溯天数

        Returns:
            同步的K线数量
        """
        logger.info(f"Syncing historical data: {instrument_id} {bar} ({days} days)")
        
        count = await self.historical_collector.backfill_missing_data(
            instrument_id=instrument_id,
            bar=bar,
            lookback_days=days
        )
        
        logger.info(f"Synced {count} historical candles")
        return count

    async def check_data_quality(self, instrument_id: str, bar: str) -> dict:
        """
        检查数据质量

        Args:
            instrument_id: 交易对ID
            bar: K线周期

        Returns:
            质量检查结果
        """
        logger.info(f"Checking data quality: {instrument_id} {bar}")
        
        end_time = datetime.utcnow()
        start_time = datetime.utcnow() - timedelta(hours=24)
        
        completeness = self.monitor.check_data_completeness(
            instrument_id=instrument_id,
            bar=bar,
            timerange=(start_time, end_time)
        )
        
        anomalies = self.monitor.detect_anomalies(
            instrument_id=instrument_id,
            bar=bar,
            lookback_hours=24
        )
        
        result = {
            'completeness': completeness,
            'anomalies': anomalies
        }
        
        logger.info(f"Quality check complete: {result}")
        return result


async def main():
    """主函数"""
    logger.info("Initializing database...")
    init_db()
    
    system = DataCollectionSystem()
    
    try:
        await system.start()
        
        logger.info("System running. Press Ctrl+C to stop.")
        
        while True:
            await asyncio.sleep(60)
            
            status = await system.get_system_status()
            logger.info(f"System status: {status['components']}")
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"System error: {e}", exc_info=True)
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
