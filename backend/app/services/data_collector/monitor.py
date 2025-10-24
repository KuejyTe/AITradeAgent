import logging
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.market_data import Candle, Ticker, DataQualityLog


logger = logging.getLogger(__name__)


class DataQualityMonitor:
    """数据质量监控"""

    def __init__(self, db_session: Session):
        """
        初始化数据质量监控器

        Args:
            db_session: 数据库会话
        """
        self.db_session = db_session

    def check_data_completeness(
        self,
        instrument_id: str,
        bar: str,
        timerange: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """
        检查数据完整性

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            timerange: 时间范围 (start_time, end_time)

        Returns:
            完整性检查结果
        """
        start_time, end_time = timerange
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)

        try:
            candles = self.db_session.query(Candle).filter(
                Candle.instrument_id == instrument_id,
                Candle.bar == bar,
                Candle.ts >= start_ts,
                Candle.ts <= end_ts
            ).order_by(Candle.ts).all()

            bar_intervals = {
                '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800,
                '1H': 3600, '2H': 7200, '4H': 14400, '6H': 21600,
                '12H': 43200, '1D': 86400, '1W': 604800
            }

            interval_seconds = bar_intervals.get(bar, 60)
            expected_count = int((end_ts - start_ts) / (interval_seconds * 1000))
            actual_count = len(candles)

            missing_intervals = []
            if candles:
                expected_ts = start_ts
                for candle in candles:
                    if candle.ts > expected_ts:
                        missing_intervals.append({
                            'start': expected_ts,
                            'end': candle.ts,
                            'duration_minutes': (candle.ts - expected_ts) / (60 * 1000)
                        })
                    expected_ts = candle.ts + (interval_seconds * 1000)

                if expected_ts < end_ts:
                    missing_intervals.append({
                        'start': expected_ts,
                        'end': end_ts,
                        'duration_minutes': (end_ts - expected_ts) / (60 * 1000)
                    })

            completeness_ratio = actual_count / expected_count if expected_count > 0 else 0

            result = {
                'instrument_id': instrument_id,
                'bar': bar,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'expected_count': expected_count,
                'actual_count': actual_count,
                'completeness_ratio': completeness_ratio,
                'missing_intervals': len(missing_intervals),
                'missing_details': missing_intervals[:10],
                'status': 'pass' if completeness_ratio >= 0.95 else 'warning' if completeness_ratio >= 0.8 else 'error'
            }

            self._log_check_result(
                instrument_id=instrument_id,
                check_type='completeness',
                status=result['status'],
                message=f"Completeness: {completeness_ratio:.2%}",
                details=result
            )

            return result

        except Exception as e:
            logger.error(f"Error checking data completeness: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def detect_anomalies(
        self,
        instrument_id: str,
        bar: str,
        lookback_hours: int = 24,
        threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        检测异常数据

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            lookback_hours: 回溯小时数
            threshold: 异常值阈值（标准差倍数）

        Returns:
            异常检测结果
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=lookback_hours)
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)

            candles = self.db_session.query(Candle).filter(
                Candle.instrument_id == instrument_id,
                Candle.bar == bar,
                Candle.ts >= start_ts,
                Candle.ts <= end_ts
            ).order_by(Candle.ts).all()

            if len(candles) < 10:
                return {
                    'status': 'insufficient_data',
                    'message': 'Not enough data for anomaly detection'
                }

            prices = [c.close for c in candles]
            mean_price = sum(prices) / len(prices)
            variance = sum((x - mean_price) ** 2 for x in prices) / len(prices)
            std_dev = variance ** 0.5

            anomalies = []
            for candle in candles:
                price_anomalies = []

                for field in ['open', 'high', 'low', 'close']:
                    value = getattr(candle, field)
                    z_score = abs((value - mean_price) / std_dev) if std_dev > 0 else 0

                    if z_score > threshold:
                        price_anomalies.append({
                            'field': field,
                            'value': value,
                            'z_score': z_score,
                            'mean': mean_price,
                            'std_dev': std_dev
                        })

                if candle.high < candle.low:
                    price_anomalies.append({
                        'field': 'validation',
                        'error': 'high < low',
                        'high': candle.high,
                        'low': candle.low
                    })

                if candle.high < candle.open or candle.high < candle.close:
                    price_anomalies.append({
                        'field': 'validation',
                        'error': 'high not highest'
                    })

                if candle.low > candle.open or candle.low > candle.close:
                    price_anomalies.append({
                        'field': 'validation',
                        'error': 'low not lowest'
                    })

                if price_anomalies:
                    anomalies.append({
                        'ts': candle.ts,
                        'timestamp': datetime.fromtimestamp(candle.ts / 1000).isoformat(),
                        'anomalies': price_anomalies
                    })

            result = {
                'instrument_id': instrument_id,
                'bar': bar,
                'lookback_hours': lookback_hours,
                'total_candles': len(candles),
                'anomaly_count': len(anomalies),
                'anomaly_ratio': len(anomalies) / len(candles) if candles else 0,
                'anomalies': anomalies[:20],
                'status': 'pass' if len(anomalies) == 0 else 'warning' if len(anomalies) < len(candles) * 0.05 else 'error'
            }

            self._log_check_result(
                instrument_id=instrument_id,
                check_type='anomaly_detection',
                status=result['status'],
                message=f"Found {len(anomalies)} anomalies",
                details=result
            )

            return result

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_data_stats(
        self,
        instrument_id: str,
        bar: Optional[str] = None,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        获取数据统计信息

        Args:
            instrument_id: 交易对ID
            bar: K线周期（可选）
            lookback_hours: 回溯小时数

        Returns:
            数据统计信息
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=lookback_hours)

            stats = {
                'instrument_id': instrument_id,
                'lookback_hours': lookback_hours,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }

            ticker_count = self.db_session.query(func.count(Ticker.id)).filter(
                Ticker.instrument_id == instrument_id,
                Ticker.created_at >= start_time
            ).scalar()

            stats['ticker_count'] = ticker_count

            if bar:
                candle_stats = self._get_candle_stats(
                    instrument_id, bar, start_time, end_time
                )
                stats['candle_stats'] = candle_stats
            else:
                bars = ['1m', '5m', '15m', '1H', '1D']
                all_candle_stats = {}
                for b in bars:
                    all_candle_stats[b] = self._get_candle_stats(
                        instrument_id, b, start_time, end_time
                    )
                stats['candle_stats'] = all_candle_stats

            return stats

        except Exception as e:
            logger.error(f"Error getting data stats: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def _get_candle_stats(
        self,
        instrument_id: str,
        bar: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """获取K线统计信息"""
        try:
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)

            candles = self.db_session.query(Candle).filter(
                Candle.instrument_id == instrument_id,
                Candle.bar == bar,
                Candle.ts >= start_ts,
                Candle.ts <= end_ts
            ).all()

            if not candles:
                return {
                    'count': 0,
                    'status': 'no_data'
                }

            prices = [c.close for c in candles]
            volumes = [c.vol for c in candles if c.vol]

            stats = {
                'count': len(candles),
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'first_price': candles[0].close,
                'last_price': candles[-1].close,
                'price_change': candles[-1].close - candles[0].close,
                'price_change_pct': ((candles[-1].close - candles[0].close) / candles[0].close * 100) if candles[0].close > 0 else 0
            }

            if volumes:
                stats['total_volume'] = sum(volumes)
                stats['avg_volume'] = sum(volumes) / len(volumes)
                stats['max_volume'] = max(volumes)

            return stats

        except Exception as e:
            logger.error(f"Error getting candle stats: {e}")
            return {'status': 'error', 'message': str(e)}

    def _log_check_result(
        self,
        instrument_id: str,
        check_type: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """记录检查结果到数据库"""
        try:
            log_entry = DataQualityLog(
                instrument_id=instrument_id,
                check_type=check_type,
                status=status,
                message=message,
                details=json.dumps(details) if details else None
            )
            self.db_session.add(log_entry)
            self.db_session.commit()
        except Exception as e:
            logger.error(f"Error logging check result: {e}")
            self.db_session.rollback()

    def get_quality_logs(
        self,
        instrument_id: Optional[str] = None,
        check_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取质量检查日志

        Args:
            instrument_id: 交易对ID（可选）
            check_type: 检查类型（可选）
            status: 状态（可选）
            limit: 返回数量限制

        Returns:
            质量检查日志列表
        """
        try:
            query = self.db_session.query(DataQualityLog)

            if instrument_id:
                query = query.filter(DataQualityLog.instrument_id == instrument_id)
            if check_type:
                query = query.filter(DataQualityLog.check_type == check_type)
            if status:
                query = query.filter(DataQualityLog.status == status)

            logs = query.order_by(DataQualityLog.created_at.desc()).limit(limit).all()

            return [
                {
                    'id': log.id,
                    'instrument_id': log.instrument_id,
                    'check_type': log.check_type,
                    'status': log.status,
                    'message': log.message,
                    'details': json.loads(log.details) if log.details else None,
                    'created_at': log.created_at.isoformat()
                }
                for log in logs
            ]

        except Exception as e:
            logger.error(f"Error getting quality logs: {e}")
            return []
