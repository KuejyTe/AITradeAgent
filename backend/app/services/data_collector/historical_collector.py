import asyncio
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.services.okx.market import OKXMarket
from app.models.market_data import Candle


logger = logging.getLogger(__name__)


class HistoricalDataCollector:
    """历史数据采集器"""

    def __init__(self, okx_client, db_session: Session):
        """
        初始化历史数据采集器

        Args:
            okx_client: OKX客户端实例
            db_session: 数据库会话
        """
        self.okx_client = okx_client
        self.db_session = db_session
        self.market = OKXMarket(okx_client)

    async def fetch_historical_candles(
        self,
        instrument_id: str,
        bar: str,
        start_time: datetime,
        end_time: datetime,
        batch_size: int = 100
    ) -> int:
        """
        获取历史K线数据

        Args:
            instrument_id: 交易对ID，如 "BTC-USDT"
            bar: K线周期，如 "1m", "5m", "1H", "1D"
            start_time: 开始时间
            end_time: 结束时间
            batch_size: 每批次请求数量（最大100）

        Returns:
            保存的K线数量
        """
        logger.info(
            f"Fetching historical candles for {instrument_id} {bar} "
            f"from {start_time} to {end_time}"
        )

        total_saved = 0
        before_ts = int(end_time.timestamp() * 1000)
        start_ts = int(start_time.timestamp() * 1000)

        try:
            while before_ts > start_ts:
                candles = await self.market.get_history_candles(
                    inst_id=instrument_id,
                    bar=bar,
                    before=str(before_ts),
                    limit=batch_size
                )

                if not candles:
                    break

                saved_count = await self._save_candles(instrument_id, bar, candles)
                total_saved += saved_count

                oldest_ts = int(candles[-1][0])
                if oldest_ts <= start_ts:
                    break

                before_ts = oldest_ts
                await asyncio.sleep(0.5)

            logger.info(
                f"Fetched {total_saved} historical candles for {instrument_id} {bar}"
            )
            return total_saved

        except Exception as e:
            logger.error(f"Error fetching historical candles: {e}", exc_info=True)
            raise

    async def _save_candles(
        self,
        instrument_id: str,
        bar: str,
        candles: List[List]
    ) -> int:
        """
        保存K线数据到数据库

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            candles: K线数据列表

        Returns:
            保存的K线数量
        """
        saved_count = 0

        try:
            for candle_data in candles:
                if len(candle_data) < 9:
                    continue

                ts = int(candle_data[0])

                existing = self.db_session.query(Candle).filter_by(
                    instrument_id=instrument_id,
                    bar=bar,
                    ts=ts
                ).first()

                if not existing:
                    candle = Candle(
                        instrument_id=instrument_id,
                        bar=bar,
                        ts=ts,
                        open=float(candle_data[1]),
                        high=float(candle_data[2]),
                        low=float(candle_data[3]),
                        close=float(candle_data[4]),
                        vol=float(candle_data[5]),
                        vol_ccy=float(candle_data[6]),
                        vol_ccy_quote=float(candle_data[7]),
                        confirm=candle_data[8] == '1'
                    )
                    self.db_session.add(candle)
                    saved_count += 1

            self.db_session.commit()
            return saved_count

        except Exception as e:
            logger.error(f"Error saving candles: {e}", exc_info=True)
            self.db_session.rollback()
            return 0

    async def backfill_missing_data(
        self,
        instrument_id: str,
        bar: str,
        lookback_days: int = 90
    ) -> int:
        """
        补充缺失的历史数据

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            lookback_days: 回溯天数

        Returns:
            补充的K线数量
        """
        logger.info(f"Backfilling missing data for {instrument_id} {bar}")

        try:
            latest_candle = self.db_session.query(Candle).filter_by(
                instrument_id=instrument_id,
                bar=bar
            ).order_by(Candle.ts.desc()).first()

            if latest_candle:
                start_time = datetime.fromtimestamp(latest_candle.ts / 1000)
            else:
                start_time = datetime.utcnow() - timedelta(days=lookback_days)

            end_time = datetime.utcnow()

            return await self.fetch_historical_candles(
                instrument_id=instrument_id,
                bar=bar,
                start_time=start_time,
                end_time=end_time
            )

        except Exception as e:
            logger.error(f"Error backfilling data: {e}", exc_info=True)
            return 0

    async def get_missing_intervals(
        self,
        instrument_id: str,
        bar: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[tuple]:
        """
        检测缺失的时间区间

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            缺失的时间区间列表 [(start1, end1), (start2, end2), ...]
        """
        bar_intervals = {
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1H': 3600,
            '2H': 7200,
            '4H': 14400,
            '6H': 21600,
            '12H': 43200,
            '1D': 86400,
            '1W': 604800,
        }

        interval = bar_intervals.get(bar, 60)
        missing_intervals = []

        try:
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)

            candles = self.db_session.query(Candle).filter(
                Candle.instrument_id == instrument_id,
                Candle.bar == bar,
                Candle.ts >= start_ts,
                Candle.ts <= end_ts
            ).order_by(Candle.ts).all()

            if not candles:
                return [(start_time, end_time)]

            expected_ts = start_ts
            for candle in candles:
                if candle.ts > expected_ts:
                    gap_start = datetime.fromtimestamp(expected_ts / 1000)
                    gap_end = datetime.fromtimestamp(candle.ts / 1000)
                    missing_intervals.append((gap_start, gap_end))

                expected_ts = candle.ts + (interval * 1000)

            if expected_ts < end_ts:
                gap_start = datetime.fromtimestamp(expected_ts / 1000)
                missing_intervals.append((gap_start, end_time))

            return missing_intervals

        except Exception as e:
            logger.error(f"Error detecting missing intervals: {e}", exc_info=True)
            return []

    async def fill_missing_intervals(
        self,
        instrument_id: str,
        bar: str,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """
        填补缺失的时间区间

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            填补的K线数量
        """
        missing_intervals = await self.get_missing_intervals(
            instrument_id, bar, start_time, end_time
        )

        total_filled = 0
        for gap_start, gap_end in missing_intervals:
            filled = await self.fetch_historical_candles(
                instrument_id, bar, gap_start, gap_end
            )
            total_filled += filled
            await asyncio.sleep(0.5)

        logger.info(
            f"Filled {total_filled} candles in {len(missing_intervals)} intervals "
            f"for {instrument_id} {bar}"
        )
        return total_filled
