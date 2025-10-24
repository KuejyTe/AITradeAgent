import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import numpy as np


logger = logging.getLogger(__name__)


class ProcessedData:
    """处理后的数据"""

    def __init__(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        self.data = data
        self.metadata = metadata or {}


class DataProcessor(ABC):
    """数据处理器基类"""

    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理数据

        Args:
            data: 原始数据

        Returns:
            处理后的数据
        """
        pass


class DataCleaningProcessor(DataProcessor):
    """数据清洗处理器 - 去除异常值"""

    def __init__(self, outlier_threshold: float = 3.0):
        """
        初始化数据清洗处理器

        Args:
            outlier_threshold: 异常值阈值（标准差倍数）
        """
        self.outlier_threshold = outlier_threshold

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗数据，移除异常值"""
        try:
            if 'candles' in data:
                candles = data['candles']
                if len(candles) > 0:
                    data['candles'] = self._remove_outliers(candles)

            return data

        except Exception as e:
            logger.error(f"Error in data cleaning: {e}")
            return data

    def _remove_outliers(self, candles: List[Dict]) -> List[Dict]:
        """使用标准差方法移除异常值"""
        if len(candles) < 3:
            return candles

        prices = [c.get('close', 0) for c in candles if c.get('close')]
        if not prices:
            return candles

        mean = np.mean(prices)
        std = np.std(prices)

        cleaned = []
        for candle in candles:
            close = candle.get('close', 0)
            if abs(close - mean) <= self.outlier_threshold * std:
                cleaned.append(candle)
            else:
                logger.warning(f"Removed outlier: {close} (mean: {mean}, std: {std})")

        return cleaned if cleaned else candles


class DataNormalizationProcessor(DataProcessor):
    """数据归一化处理器"""

    def __init__(self, method: str = 'minmax'):
        """
        初始化归一化处理器

        Args:
            method: 归一化方法 ('minmax' 或 'zscore')
        """
        self.method = method

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """归一化数据"""
        try:
            if 'candles' in data:
                candles = data['candles']
                if len(candles) > 0:
                    data['normalized_candles'] = self._normalize_candles(candles)

            return data

        except Exception as e:
            logger.error(f"Error in data normalization: {e}")
            return data

    def _normalize_candles(self, candles: List[Dict]) -> List[Dict]:
        """归一化K线数据"""
        if len(candles) < 2:
            return candles

        prices = [c.get('close', 0) for c in candles if c.get('close')]
        if not prices:
            return candles

        if self.method == 'minmax':
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price

            if price_range == 0:
                return candles

            normalized = []
            for candle in candles:
                normalized_candle = candle.copy()
                for key in ['open', 'high', 'low', 'close']:
                    if key in candle:
                        normalized_candle[f'normalized_{key}'] = (
                            (candle[key] - min_price) / price_range
                        )
                normalized.append(normalized_candle)

            return normalized

        elif self.method == 'zscore':
            mean = np.mean(prices)
            std = np.std(prices)

            if std == 0:
                return candles

            normalized = []
            for candle in candles:
                normalized_candle = candle.copy()
                for key in ['open', 'high', 'low', 'close']:
                    if key in candle:
                        normalized_candle[f'normalized_{key}'] = (
                            (candle[key] - mean) / std
                        )
                normalized.append(normalized_candle)

            return normalized

        return candles


class TechnicalIndicatorProcessor(DataProcessor):
    """技术指标计算处理器"""

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            if 'candles' in data:
                candles = data['candles']
                if len(candles) > 0:
                    data['indicators'] = self._calculate_indicators(candles)

            return data

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return data

    def _calculate_indicators(self, candles: List[Dict]) -> Dict[str, Any]:
        """计算技术指标"""
        if len(candles) < 2:
            return {}

        closes = np.array([c.get('close', 0) for c in candles if c.get('close')])
        if len(closes) == 0:
            return {}

        indicators = {}

        indicators['ma_5'] = self._calculate_ma(closes, 5)
        indicators['ma_10'] = self._calculate_ma(closes, 10)
        indicators['ma_20'] = self._calculate_ma(closes, 20)
        indicators['ma_50'] = self._calculate_ma(closes, 50)

        indicators['ema_5'] = self._calculate_ema(closes, 5)
        indicators['ema_10'] = self._calculate_ema(closes, 10)
        indicators['ema_20'] = self._calculate_ema(closes, 20)

        if len(closes) >= 14:
            indicators['rsi_14'] = self._calculate_rsi(closes, 14)

        macd_data = self._calculate_macd(closes)
        indicators.update(macd_data)

        return indicators

    def _calculate_ma(self, prices: np.ndarray, period: int) -> Optional[float]:
        """计算移动平均线"""
        if len(prices) < period:
            return None
        return float(np.mean(prices[-period:]))

    def _calculate_ema(self, prices: np.ndarray, period: int) -> Optional[float]:
        """计算指数移动平均线"""
        if len(prices) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return float(ema)

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> Optional[float]:
        """计算相对强弱指标"""
        if len(prices) < period + 1:
            return None

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    def _calculate_macd(
        self,
        prices: np.ndarray,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, Optional[float]]:
        """计算MACD指标"""
        if len(prices) < slow_period:
            return {'macd': None, 'macd_signal': None, 'macd_histogram': None}

        ema_fast = self._calculate_ema(prices, fast_period)
        ema_slow = self._calculate_ema(prices, slow_period)

        if ema_fast is None or ema_slow is None:
            return {'macd': None, 'macd_signal': None, 'macd_histogram': None}

        macd_line = ema_fast - ema_slow

        macd_values = []
        for i in range(slow_period, len(prices) + 1):
            ema_f = self._calculate_ema(prices[:i], fast_period)
            ema_s = self._calculate_ema(prices[:i], slow_period)
            if ema_f and ema_s:
                macd_values.append(ema_f - ema_s)

        if len(macd_values) < signal_period:
            signal_line = macd_line
        else:
            signal_line = self._calculate_ema(
                np.array(macd_values),
                signal_period
            )

        histogram = macd_line - (signal_line or 0)

        return {
            'macd': float(macd_line),
            'macd_signal': float(signal_line) if signal_line else None,
            'macd_histogram': float(histogram)
        }


class DataValidationProcessor(DataProcessor):
    """数据验证处理器"""

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据完整性和有效性"""
        try:
            validation_result = {
                'is_valid': True,
                'errors': []
            }

            if 'candles' in data:
                candles = data['candles']
                for idx, candle in enumerate(candles):
                    errors = self._validate_candle(candle, idx)
                    if errors:
                        validation_result['is_valid'] = False
                        validation_result['errors'].extend(errors)

            data['validation'] = validation_result
            return data

        except Exception as e:
            logger.error(f"Error in data validation: {e}")
            return data

    def _validate_candle(self, candle: Dict[str, Any], index: int) -> List[str]:
        """验证单个K线数据"""
        errors = []

        required_fields = ['open', 'high', 'low', 'close']
        for field in required_fields:
            if field not in candle or candle[field] is None:
                errors.append(f"Candle {index}: Missing {field}")

        if all(field in candle for field in required_fields):
            if candle['high'] < candle['low']:
                errors.append(f"Candle {index}: High < Low")

            if candle['high'] < candle['open'] or candle['high'] < candle['close']:
                errors.append(f"Candle {index}: High not highest")

            if candle['low'] > candle['open'] or candle['low'] > candle['close']:
                errors.append(f"Candle {index}: Low not lowest")

        return errors


class DataPipeline:
    """数据处理管道"""

    def __init__(self):
        self.processors: List[DataProcessor] = []

    def add_processor(self, processor: DataProcessor):
        """
        添加数据处理器

        Args:
            processor: 数据处理器实例
        """
        self.processors.append(processor)
        logger.info(f"Added processor: {processor.__class__.__name__}")

    async def process(self, raw_data: Dict[str, Any]) -> ProcessedData:
        """
        处理原始数据

        Args:
            raw_data: 原始数据

        Returns:
            处理后的数据
        """
        data = raw_data.copy()
        metadata = {
            'processors_applied': [],
            'processing_errors': []
        }

        for processor in self.processors:
            try:
                data = await processor.process(data)
                metadata['processors_applied'].append(
                    processor.__class__.__name__
                )
            except Exception as e:
                error_msg = f"Error in {processor.__class__.__name__}: {e}"
                logger.error(error_msg)
                metadata['processing_errors'].append(error_msg)

        return ProcessedData(data, metadata)

    def clear_processors(self):
        """清除所有处理器"""
        self.processors.clear()
