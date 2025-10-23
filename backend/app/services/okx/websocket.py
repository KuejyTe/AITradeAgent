import asyncio
import json
import logging
from typing import Optional, Callable, Dict, List, Any
from enum import Enum
import websockets
from websockets.client import WebSocketClientProtocol

from .auth import OKXAuth


logger = logging.getLogger(__name__)


class OKXWSChannel(Enum):
    """OKX WebSocket channels"""
    TICKERS = "tickers"
    CANDLES = "candles"
    BOOKS = "books"
    BOOKS5 = "books5"
    BOOKS_TBT = "books-l2-tbt"
    BOOKS50_TBT = "books50-l2-tbt"
    TRADES = "trades"
    ACCOUNT = "account"
    POSITIONS = "positions"
    ORDERS = "orders"
    ORDERS_ALGO = "orders-algo"
    LIQUIDATION_WARNING = "liquidation-warning"
    ACCOUNT_GREEKS = "account-greeks"


class OKXWebSocket:
    """
    OKX WebSocket client
    Handles WebSocket connections with automatic reconnection, subscriptions, and heartbeat
    """

    PUBLIC_WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
    PRIVATE_WS_URL = "wss://ws.okx.com:8443/ws/v5/private"
    BUSINESS_WS_URL = "wss://ws.okx.com:8443/ws/v5/business"

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        url: Optional[str] = None,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
        on_open: Optional[Callable] = None
    ):
        """
        Initialize WebSocket client

        Args:
            api_key: OKX API key (required for private channels)
            secret_key: OKX secret key (required for private channels)
            passphrase: OKX API passphrase (required for private channels)
            url: Custom WebSocket URL (overrides default)
            on_message: Callback for received messages
            on_error: Callback for errors
            on_close: Callback for connection close
            on_open: Callback for connection open
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

        self.auth = None
        if api_key and secret_key and passphrase:
            self.auth = OKXAuth(api_key, secret_key, passphrase)

        self.url = url or self.PUBLIC_WS_URL
        self.ws: Optional[WebSocketClientProtocol] = None
        self.subscriptions: List[Dict[str, Any]] = []

        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.on_open = on_open

        self._running = False
        self._reconnect = True
        self._reconnect_delay = 5
        self._ping_interval = 20
        self._ping_timeout = 10

    async def connect(self):
        """Connect to WebSocket"""
        self._running = True
        while self._running and self._reconnect:
            try:
                logger.info(f"Connecting to OKX WebSocket: {self.url}")
                async with websockets.connect(
                    self.url,
                    ping_interval=self._ping_interval,
                    ping_timeout=self._ping_timeout
                ) as websocket:
                    self.ws = websocket
                    logger.info("WebSocket connected")

                    if self.on_open:
                        await self.on_open()

                    if self.auth and self._requires_auth():
                        await self._login()

                    await self._resubscribe()

                    await self._receive_loop()

            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                if self.on_close:
                    await self.on_close()

                if self._reconnect and self._running:
                    logger.info(f"Reconnecting in {self._reconnect_delay} seconds...")
                    await asyncio.sleep(self._reconnect_delay)
                else:
                    break

            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if self.on_error:
                    await self.on_error(e)

                if self._reconnect and self._running:
                    logger.info(f"Reconnecting in {self._reconnect_delay} seconds...")
                    await asyncio.sleep(self._reconnect_delay)
                else:
                    break

    def _requires_auth(self) -> bool:
        """Check if current URL requires authentication"""
        return self.url == self.PRIVATE_WS_URL or self.url == self.BUSINESS_WS_URL

    async def _login(self):
        """Authenticate WebSocket connection"""
        if not self.auth:
            raise ValueError("Authentication credentials not provided")

        auth_params = self.auth.get_ws_auth_params()

        login_msg = {
            "op": "login",
            "args": [auth_params]
        }

        logger.info("Authenticating WebSocket connection")
        await self.ws.send(json.dumps(login_msg))

        response = await self.ws.recv()
        response_data = json.loads(response)

        if response_data.get('event') == 'login' and response_data.get('code') == '0':
            logger.info("WebSocket authentication successful")
        else:
            error_msg = response_data.get('msg', 'Unknown error')
            raise Exception(f"WebSocket authentication failed: {error_msg}")

    async def _resubscribe(self):
        """Resubscribe to all channels after reconnection"""
        if self.subscriptions:
            logger.info(f"Resubscribing to {len(self.subscriptions)} channels")
            for sub in self.subscriptions:
                await self._send_subscription(sub, subscribe=True)

    async def _receive_loop(self):
        """Main receive loop"""
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed in receive loop")
            raise

    async def _handle_message(self, message: str):
        """
        Handle received WebSocket message

        Args:
            message: Raw message string
        """
        try:
            data = json.loads(message)
            logger.debug(f"Received message: {data}")

            event = data.get('event')
            if event == 'error':
                error_msg = data.get('msg', 'Unknown error')
                logger.error(f"WebSocket error event: {error_msg}")
                if self.on_error:
                    await self.on_error(Exception(error_msg))

            elif event in ['subscribe', 'unsubscribe']:
                logger.info(f"Subscription {event}: {data}")

            elif self.on_message:
                await self.on_message(data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if self.on_error:
                await self.on_error(e)

    async def _send_subscription(self, args: Dict[str, Any], subscribe: bool = True):
        """
        Send subscription message

        Args:
            args: Subscription arguments
            subscribe: True to subscribe, False to unsubscribe
        """
        op = "subscribe" if subscribe else "unsubscribe"
        msg = {
            "op": op,
            "args": [args]
        }

        if self.ws and not self.ws.closed:
            await self.ws.send(json.dumps(msg))
            logger.info(f"{op.capitalize()}d to {args}")

    async def subscribe(self, channel: str, inst_id: Optional[str] = None, **kwargs):
        """
        Subscribe to a channel

        Args:
            channel: Channel name (e.g., "tickers", "candles1m")
            inst_id: Instrument ID (e.g., "BTC-USDT")
            **kwargs: Additional arguments
        """
        args = {"channel": channel}
        if inst_id:
            args["instId"] = inst_id
        args.update(kwargs)

        if args not in self.subscriptions:
            self.subscriptions.append(args)

        await self._send_subscription(args, subscribe=True)

    async def unsubscribe(self, channel: str, inst_id: Optional[str] = None, **kwargs):
        """
        Unsubscribe from a channel

        Args:
            channel: Channel name
            inst_id: Instrument ID
            **kwargs: Additional arguments
        """
        args = {"channel": channel}
        if inst_id:
            args["instId"] = inst_id
        args.update(kwargs)

        if args in self.subscriptions:
            self.subscriptions.remove(args)

        await self._send_subscription(args, subscribe=False)

    async def subscribe_tickers(self, inst_id: str):
        """Subscribe to ticker channel"""
        await self.subscribe(OKXWSChannel.TICKERS.value, inst_id=inst_id)

    async def subscribe_candles(self, inst_id: str, bar: str = "1m"):
        """
        Subscribe to candlestick channel

        Args:
            inst_id: Instrument ID
            bar: Bar size (1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, etc.)
        """
        channel = f"candle{bar}"
        await self.subscribe(channel, inst_id=inst_id)

    async def subscribe_books(self, inst_id: str, channel: str = "books"):
        """
        Subscribe to order book channel

        Args:
            inst_id: Instrument ID
            channel: Channel type (books, books5, books-l2-tbt, books50-l2-tbt)
        """
        await self.subscribe(channel, inst_id=inst_id)

    async def subscribe_trades(self, inst_id: str):
        """Subscribe to trades channel"""
        await self.subscribe(OKXWSChannel.TRADES.value, inst_id=inst_id)

    async def subscribe_account(self, ccy: Optional[str] = None):
        """
        Subscribe to account channel (requires authentication)

        Args:
            ccy: Currency
        """
        kwargs = {}
        if ccy:
            kwargs['ccy'] = ccy
        await self.subscribe(OKXWSChannel.ACCOUNT.value, **kwargs)

    async def subscribe_positions(self, inst_type: str, inst_id: Optional[str] = None):
        """
        Subscribe to positions channel (requires authentication)

        Args:
            inst_type: Instrument type (MARGIN, SWAP, FUTURES, OPTION)
            inst_id: Instrument ID
        """
        kwargs = {'instType': inst_type}
        if inst_id:
            kwargs['instId'] = inst_id
        await self.subscribe(OKXWSChannel.POSITIONS.value, **kwargs)

    async def subscribe_orders(self, inst_type: str, inst_id: Optional[str] = None):
        """
        Subscribe to orders channel (requires authentication)

        Args:
            inst_type: Instrument type
            inst_id: Instrument ID
        """
        kwargs = {'instType': inst_type}
        if inst_id:
            kwargs['instId'] = inst_id
        await self.subscribe(OKXWSChannel.ORDERS.value, **kwargs)

    async def unsubscribe_tickers(self, inst_id: str):
        """Unsubscribe from ticker channel"""
        await self.unsubscribe(OKXWSChannel.TICKERS.value, inst_id=inst_id)

    async def unsubscribe_candles(self, inst_id: str, bar: str = "1m"):
        """Unsubscribe from candlestick channel"""
        channel = f"candle{bar}"
        await self.unsubscribe(channel, inst_id=inst_id)

    async def unsubscribe_books(self, inst_id: str, channel: str = "books"):
        """Unsubscribe from order book channel"""
        await self.unsubscribe(channel, inst_id=inst_id)

    async def unsubscribe_trades(self, inst_id: str):
        """Unsubscribe from trades channel"""
        await self.unsubscribe(OKXWSChannel.TRADES.value, inst_id=inst_id)

    async def close(self):
        """Close WebSocket connection"""
        logger.info("Closing WebSocket connection")
        self._running = False
        self._reconnect = False

        if self.ws and not self.ws.closed:
            await self.ws.close()

    def set_reconnect(self, reconnect: bool):
        """
        Enable or disable automatic reconnection

        Args:
            reconnect: True to enable, False to disable
        """
        self._reconnect = reconnect

    def set_reconnect_delay(self, delay: int):
        """
        Set reconnection delay

        Args:
            delay: Delay in seconds
        """
        self._reconnect_delay = delay
