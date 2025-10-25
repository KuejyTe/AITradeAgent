import json
import logging
from typing import Optional, List, Dict, Any
from datetime import timedelta
import redis.asyncio as redis


logger = logging.getLogger(__name__)


class DataCache:
    """数据缓存服务 - 使用Redis"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600
    ):
        """
        初始化数据缓存

        Args:
            redis_url: Redis连接URL
            default_ttl: 默认过期时间（秒）
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """连接到Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def set_ticker(
        self,
        instrument_id: str,
        ticker_data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        缓存最新行情数据

        Args:
            instrument_id: 交易对ID
            ticker_data: 行情数据
            ttl: 过期时间（秒），None使用默认值
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return

        try:
            key = f"ticker:{instrument_id}"
            value = json.dumps(ticker_data)
            await self.redis_client.set(
                key,
                value,
                ex=ttl or self.default_ttl
            )
            logger.debug(f"Cached ticker for {instrument_id}")
        except Exception as e:
            logger.error(f"Error caching ticker: {e}")

    async def get_ticker(self, instrument_id: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的行情数据

        Args:
            instrument_id: 交易对ID

        Returns:
            行情数据，如果不存在返回None
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return None

        try:
            key = f"ticker:{instrument_id}"
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting ticker from cache: {e}")
            return None

    async def push_candle(
        self,
        instrument_id: str,
        bar: str,
        candle_data: Dict[str, Any],
        max_length: int = 1000
    ):
        """
        添加K线到滑动窗口缓存

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            candle_data: K线数据
            max_length: 滑动窗口最大长度
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return

        try:
            key = f"candles:{instrument_id}:{bar}"
            value = json.dumps(candle_data)

            await self.redis_client.lpush(key, value)
            await self.redis_client.ltrim(key, 0, max_length - 1)

            logger.debug(f"Pushed candle to cache: {instrument_id} {bar}")
        except Exception as e:
            logger.error(f"Error pushing candle to cache: {e}")

    async def get_candles(
        self,
        instrument_id: str,
        bar: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取缓存的K线数据

        Args:
            instrument_id: 交易对ID
            bar: K线周期
            limit: 获取数量

        Returns:
            K线数据列表
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return []

        try:
            key = f"candles:{instrument_id}:{bar}"
            values = await self.redis_client.lrange(key, 0, limit - 1)

            candles = []
            for value in values:
                try:
                    candles.append(json.loads(value))
                except json.JSONDecodeError:
                    continue

            return candles
        except Exception as e:
            logger.error(f"Error getting candles from cache: {e}")
            return []

    async def set_order_book(
        self,
        instrument_id: str,
        order_book_data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        缓存订单簿数据

        Args:
            instrument_id: 交易对ID
            order_book_data: 订单簿数据
            ttl: 过期时间（秒）
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return

        try:
            key = f"orderbook:{instrument_id}"
            value = json.dumps(order_book_data)
            await self.redis_client.set(
                key,
                value,
                ex=ttl or 60
            )
            logger.debug(f"Cached order book for {instrument_id}")
        except Exception as e:
            logger.error(f"Error caching order book: {e}")

    async def get_order_book(self, instrument_id: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的订单簿数据

        Args:
            instrument_id: 交易对ID

        Returns:
            订单簿数据
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return None

        try:
            key = f"orderbook:{instrument_id}"
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting order book from cache: {e}")
            return None

    async def get_cache_stats(self, instrument_id: str) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Args:
            instrument_id: 交易对ID

        Returns:
            缓存统计信息
        """
        if not self.redis_client:
            return {}

        try:
            stats = {}

            ticker_key = f"ticker:{instrument_id}"
            ticker_exists = await self.redis_client.exists(ticker_key)
            stats['ticker_cached'] = bool(ticker_exists)

            orderbook_key = f"orderbook:{instrument_id}"
            orderbook_exists = await self.redis_client.exists(orderbook_key)
            stats['orderbook_cached'] = bool(orderbook_exists)

            bars = ['1m', '5m', '15m', '1H', '1D']
            candle_stats = {}
            for bar in bars:
                candles_key = f"candles:{instrument_id}:{bar}"
                count = await self.redis_client.llen(candles_key)
                candle_stats[bar] = count

            stats['candle_counts'] = candle_stats

            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    async def clear_cache(self, instrument_id: Optional[str] = None):
        """
        清除缓存

        Args:
            instrument_id: 交易对ID，如果为None则清除所有缓存
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return

        try:
            if instrument_id:
                pattern = f"*:{instrument_id}*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                logger.info(f"Cleared cache for {instrument_id}")
            else:
                await self.redis_client.flushdb()
                logger.info("Cleared all cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    async def set_with_expiry(
        self,
        key: str,
        value: Any,
        ttl: int
    ):
        """
        设置带过期时间的键值对

        Args:
            key: 键
            value: 值
            ttl: 过期时间（秒）
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.redis_client.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Error setting key with expiry: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """
        获取键的值

        Args:
            key: 键

        Returns:
            值，如果不存在返回None
        """
        if not self.redis_client:
            logger.warning("Redis client not connected")
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Error getting key: {e}")
            return None
