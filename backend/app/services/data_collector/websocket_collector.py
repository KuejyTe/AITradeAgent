import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.okx.websocket import OKXWebSocket
from app.models.market_data import Ticker, Candle, OrderBook


logger = logging.getLogger(__name__)


class MarketDataCollector:
    """实时市场数据采集器"""

    def __init__(
        self,
        okx_client,
        db_session: Session,
        on_data_callback: Optional[Callable] = None
    ):
        """
        初始化市场数据采集器

        Args:
            okx_client: OKX客户端实例
            db_session: 数据库会话
            on_data_callback: 数据到达时的回调函数
        """
        self.okx_client = okx_client
        self.db_session = db_session
        self.on_data_callback = on_data_callback
        self.subscriptions = {}
        self.ws: Optional[OKXWebSocket] = None
        self._running = False

    async def start(self):
        """启动数据收集"""
        if self._running:
            logger.warning("MarketDataCollector is already running")
            return

        self._running = True
        logger.info("Starting MarketDataCollector")

        self.ws = OKXWebSocket(
            api_key=self.okx_client.api_key if hasattr(self.okx_client, 'api_key') else None,
            secret_key=self.okx_client.secret_key if hasattr(self.okx_client, 'secret_key') else None,
            passphrase=self.okx_client.passphrase if hasattr(self.okx_client, 'passphrase') else None,
            on_message=self._handle_message,
            on_error=self._handle_error,
            on_close=self._handle_close,
            on_open=self._handle_open
        )

        try:
            await self.ws.connect()
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            self._running = False
            raise

    async def stop(self):
        """停止数据收集"""
        logger.info("Stopping MarketDataCollector")
        self._running = False

        if self.ws:
            await self.ws.close()

    async def subscribe_ticker(self, instrument_ids: List[str]):
        """
        订阅实时行情

        Args:
            instrument_ids: 交易对列表，如 ["BTC-USDT", "ETH-USDT"]
        """
        if not self.ws:
            raise RuntimeError("WebSocket not initialized. Call start() first")

        for inst_id in instrument_ids:
            await self.ws.subscribe_tickers(inst_id)
            self.subscriptions[f"ticker_{inst_id}"] = {
                "type": "ticker",
                "instrument_id": inst_id
            }
            logger.info(f"Subscribed to ticker: {inst_id}")

    async def subscribe_candles(self, instrument_ids: List[str], bar: str):
        """
        订阅K线数据

        Args:
            instrument_ids: 交易对列表
            bar: K线周期，如 "1m", "5m", "15m", "1H", "1D"
        """
        if not self.ws:
            raise RuntimeError("WebSocket not initialized. Call start() first")

        for inst_id in instrument_ids:
            await self.ws.subscribe_candles(inst_id, bar)
            self.subscriptions[f"candle_{inst_id}_{bar}"] = {
                "type": "candle",
                "instrument_id": inst_id,
                "bar": bar
            }
            logger.info(f"Subscribed to candles: {inst_id} {bar}")

    async def subscribe_order_book(self, instrument_ids: List[str]):
        """
        订阅订单簿

        Args:
            instrument_ids: 交易对列表
        """
        if not self.ws:
            raise RuntimeError("WebSocket not initialized. Call start() first")

        for inst_id in instrument_ids:
            await self.ws.subscribe_books(inst_id, channel="books5")
            self.subscriptions[f"books_{inst_id}"] = {
                "type": "books",
                "instrument_id": inst_id
            }
            logger.info(f"Subscribed to order book: {inst_id}")

    async def _handle_open(self):
        """WebSocket连接打开时的处理"""
        logger.info("WebSocket connection opened")

    async def _handle_close(self):
        """WebSocket连接关闭时的处理"""
        logger.warning("WebSocket connection closed")

    async def _handle_error(self, error: Exception):
        """WebSocket错误处理"""
        logger.error(f"WebSocket error: {error}")

    async def _handle_message(self, data: Dict[str, Any]):
        """
        处理接收到的WebSocket消息

        Args:
            data: 接收到的消息数据
        """
        try:
            if 'arg' not in data or 'data' not in data:
                return

            channel = data['arg'].get('channel', '')
            inst_id = data['arg'].get('instId', '')

            if channel == 'tickers':
                await self.on_ticker_update(data['data'], inst_id)
            elif channel.startswith('candle'):
                await self.on_candle_update(data['data'], inst_id, channel)
            elif 'books' in channel:
                await self.on_order_book_update(data['data'], inst_id)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    async def on_ticker_update(self, data: List[Dict], instrument_id: str):
        """
        处理行情更新

        Args:
            data: 行情数据列表
            instrument_id: 交易对ID
        """
        try:
            for item in data:
                ticker = Ticker(
                    instrument_id=instrument_id,
                    last=float(item.get('last', 0)),
                    last_sz=float(item.get('lastSz', 0)),
                    ask_px=float(item.get('askPx', 0)),
                    ask_sz=float(item.get('askSz', 0)),
                    bid_px=float(item.get('bidPx', 0)),
                    bid_sz=float(item.get('bidSz', 0)),
                    open_24h=float(item.get('open24h', 0)),
                    high_24h=float(item.get('high24h', 0)),
                    low_24h=float(item.get('low24h', 0)),
                    vol_ccy_24h=float(item.get('volCcy24h', 0)),
                    vol_24h=float(item.get('vol24h', 0)),
                    ts=int(item.get('ts', 0))
                )

                self.db_session.add(ticker)
                self.db_session.commit()

                logger.debug(f"Saved ticker for {instrument_id}: {ticker.last}")

                if self.on_data_callback:
                    await self.on_data_callback({
                        'type': 'ticker',
                        'instrument_id': instrument_id,
                        'data': item
                    })

        except Exception as e:
            logger.error(f"Error saving ticker: {e}", exc_info=True)
            self.db_session.rollback()

    async def on_candle_update(self, data: List[List], instrument_id: str, channel: str):
        """
        处理K线更新

        Args:
            data: K线数据列表
            instrument_id: 交易对ID
            channel: 频道名称，如 "candle1m"
        """
        try:
            bar = channel.replace('candle', '')

            for item in data:
                if len(item) < 9:
                    continue

                ts = int(item[0])
                candle = Candle(
                    instrument_id=instrument_id,
                    bar=bar,
                    ts=ts,
                    open=float(item[1]),
                    high=float(item[2]),
                    low=float(item[3]),
                    close=float(item[4]),
                    vol=float(item[5]),
                    vol_ccy=float(item[6]),
                    vol_ccy_quote=float(item[7]),
                    confirm=item[8] == '1'
                )

                # 使用upsert策略：如果存在相同的记录则更新
                existing = self.db_session.query(Candle).filter_by(
                    instrument_id=instrument_id,
                    bar=bar,
                    ts=ts
                ).first()

                if existing:
                    existing.open = candle.open
                    existing.high = candle.high
                    existing.low = candle.low
                    existing.close = candle.close
                    existing.vol = candle.vol
                    existing.vol_ccy = candle.vol_ccy
                    existing.vol_ccy_quote = candle.vol_ccy_quote
                    existing.confirm = candle.confirm
                else:
                    self.db_session.add(candle)

                self.db_session.commit()

                logger.debug(f"Saved candle for {instrument_id} {bar}: {candle.close}")

                if self.on_data_callback:
                    await self.on_data_callback({
                        'type': 'candle',
                        'instrument_id': instrument_id,
                        'bar': bar,
                        'data': item
                    })

        except Exception as e:
            logger.error(f"Error saving candle: {e}", exc_info=True)
            self.db_session.rollback()

    async def on_order_book_update(self, data: List[Dict], instrument_id: str):
        """
        处理订单簿更新

        Args:
            data: 订单簿数据列表
            instrument_id: 交易对ID
        """
        try:
            for item in data:
                order_book = OrderBook(
                    instrument_id=instrument_id,
                    asks=json.dumps(item.get('asks', [])),
                    bids=json.dumps(item.get('bids', [])),
                    ts=int(item.get('ts', 0))
                )

                self.db_session.add(order_book)
                self.db_session.commit()

                logger.debug(f"Saved order book for {instrument_id}")

                if self.on_data_callback:
                    await self.on_data_callback({
                        'type': 'order_book',
                        'instrument_id': instrument_id,
                        'data': item
                    })

        except Exception as e:
            logger.error(f"Error saving order book: {e}", exc_info=True)
            self.db_session.rollback()
