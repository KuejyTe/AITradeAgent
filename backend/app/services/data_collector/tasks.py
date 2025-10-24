import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.data_collector.historical_collector import HistoricalDataCollector
from app.services.data_collector.monitor import DataQualityMonitor
from app.models.market_data import Candle, Ticker, OrderBook
from app.core.config import settings


logger = logging.getLogger(__name__)


class DataCollectorTasks:
    """数据采集后台任务"""

    def __init__(self, okx_client, db_session: Session):
        """
        初始化后台任务

        Args:
            okx_client: OKX客户端实例
            db_session: 数据库会话
        """
        self.okx_client = okx_client
        self.db_session = db_session
        self.historical_collector = HistoricalDataCollector(okx_client, db_session)
        self.monitor = DataQualityMonitor(db_session)
        self._running = False
        self._tasks = []

    async def start(self):
        """启动所有后台任务"""
        if self._running:
            logger.warning("Tasks already running")
            return

        self._running = True
        logger.info("Starting background tasks")

        self._tasks = [
            asyncio.create_task(self._sync_historical_data_task()),
            asyncio.create_task(self._cleanup_old_data_task()),
            asyncio.create_task(self._data_quality_check_task())
        ]

    async def stop(self):
        """停止所有后台任务"""
        logger.info("Stopping background tasks")
        self._running = False

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _sync_historical_data_task(self):
        """定时同步历史数据任务"""
        while self._running:
            try:
                logger.info("Starting historical data sync")

                instruments = settings.DATA_COLLECTOR_CONFIG.get("instruments", [])
                candle_bars = settings.DATA_COLLECTOR_CONFIG.get("candle_bars", [])

                for instrument_id in instruments:
                    for bar in candle_bars:
                        try:
                            filled = await self.historical_collector.backfill_missing_data(
                                instrument_id=instrument_id,
                                bar=bar,
                                lookback_days=7
                            )
                            logger.info(
                                f"Backfilled {filled} candles for {instrument_id} {bar}"
                            )
                            await asyncio.sleep(1)

                        except Exception as e:
                            logger.error(
                                f"Error backfilling {instrument_id} {bar}: {e}"
                            )

                logger.info("Historical data sync completed")

                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in historical data sync task: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _cleanup_old_data_task(self):
        """定时清理过期数据任务"""
        while self._running:
            try:
                logger.info("Starting data cleanup")

                retention_days = settings.DATA_COLLECTOR_CONFIG.get("retention_days", 90)
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                cutoff_ts = int(cutoff_date.timestamp() * 1000)

                deleted_tickers = self.db_session.query(Ticker).filter(
                    Ticker.created_at < cutoff_date
                ).delete()

                deleted_candles = self.db_session.query(Candle).filter(
                    Candle.ts < cutoff_ts
                ).delete()

                deleted_orderbooks = self.db_session.query(OrderBook).filter(
                    OrderBook.created_at < cutoff_date
                ).delete()

                self.db_session.commit()

                logger.info(
                    f"Cleanup completed: "
                    f"{deleted_tickers} tickers, "
                    f"{deleted_candles} candles, "
                    f"{deleted_orderbooks} order books deleted"
                )

                await asyncio.sleep(86400)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}", exc_info=True)
                self.db_session.rollback()
                await asyncio.sleep(3600)

    async def _data_quality_check_task(self):
        """定时数据完整性检查任务"""
        while self._running:
            try:
                logger.info("Starting data quality check")

                instruments = settings.DATA_COLLECTOR_CONFIG.get("instruments", [])
                candle_bars = settings.DATA_COLLECTOR_CONFIG.get("candle_bars", [])

                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=24)

                for instrument_id in instruments:
                    for bar in candle_bars:
                        try:
                            completeness_result = self.monitor.check_data_completeness(
                                instrument_id=instrument_id,
                                bar=bar,
                                timerange=(start_time, end_time)
                            )

                            if completeness_result['status'] != 'pass':
                                logger.warning(
                                    f"Data completeness issue for {instrument_id} {bar}: "
                                    f"{completeness_result.get('completeness_ratio', 0):.2%}"
                                )

                            anomaly_result = self.monitor.detect_anomalies(
                                instrument_id=instrument_id,
                                bar=bar,
                                lookback_hours=24
                            )

                            if anomaly_result['status'] != 'pass':
                                logger.warning(
                                    f"Anomalies detected for {instrument_id} {bar}: "
                                    f"{anomaly_result.get('anomaly_count', 0)} anomalies"
                                )

                            await asyncio.sleep(1)

                        except Exception as e:
                            logger.error(
                                f"Error checking quality for {instrument_id} {bar}: {e}"
                            )

                logger.info("Data quality check completed")

                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in quality check task: {e}", exc_info=True)
                await asyncio.sleep(600)

    async def run_manual_sync(
        self,
        instrument_id: str,
        bar: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        手动触发历史数据同步

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            同步的K线数量
        """
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=7)
        if not end_time:
            end_time = datetime.utcnow()

        logger.info(
            f"Manual sync: {instrument_id} {bar} from {start_time} to {end_time}"
        )

        return await self.historical_collector.fetch_historical_candles(
            instrument_id=instrument_id,
            bar=bar,
            start_time=start_time,
            end_time=end_time
        )

    async def run_manual_quality_check(
        self,
        instrument_id: str,
        bar: str
    ) -> dict:
        """
        手动触发数据质量检查

        Args:
            instrument_id: 交易对ID
            bar: K线周期

        Returns:
            检查结果
        """
        logger.info(f"Manual quality check: {instrument_id} {bar}")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        completeness_result = self.monitor.check_data_completeness(
            instrument_id=instrument_id,
            bar=bar,
            timerange=(start_time, end_time)
        )

        anomaly_result = self.monitor.detect_anomalies(
            instrument_id=instrument_id,
            bar=bar,
            lookback_hours=24
        )

        return {
            "completeness": completeness_result,
            "anomalies": anomaly_result
        }
