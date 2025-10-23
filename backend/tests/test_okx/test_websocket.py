import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.okx.websocket import OKXWebSocket, OKXWSChannel


class TestOKXWebSocket:
    """Test OKX WebSocket client"""

    @pytest.fixture
    def ws_client(self):
        """Create WebSocket client"""
        return OKXWebSocket(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass"
        )

    @pytest.fixture
    def ws_client_no_auth(self):
        """Create WebSocket client without auth"""
        return OKXWebSocket()

    def test_websocket_initialization(self, ws_client):
        """Test WebSocket initialization"""
        assert ws_client.api_key == "test_key"
        assert ws_client.secret_key == "test_secret"
        assert ws_client.passphrase == "test_pass"
        assert ws_client.auth is not None
        assert ws_client.url == OKXWebSocket.PUBLIC_WS_URL

    def test_websocket_initialization_no_auth(self, ws_client_no_auth):
        """Test WebSocket initialization without auth"""
        assert ws_client_no_auth.api_key is None
        assert ws_client_no_auth.auth is None

    def test_custom_url(self):
        """Test custom WebSocket URL"""
        custom_url = "wss://custom.okx.com/ws"
        ws = OKXWebSocket(url=custom_url)
        assert ws.url == custom_url

    def test_requires_auth_public(self, ws_client):
        """Test requires auth for public URL"""
        ws_client.url = OKXWebSocket.PUBLIC_WS_URL
        assert not ws_client._requires_auth()

    def test_requires_auth_private(self, ws_client):
        """Test requires auth for private URL"""
        ws_client.url = OKXWebSocket.PRIVATE_WS_URL
        assert ws_client._requires_auth()

    def test_requires_auth_business(self, ws_client):
        """Test requires auth for business URL"""
        ws_client.url = OKXWebSocket.BUSINESS_WS_URL
        assert ws_client._requires_auth()

    @pytest.mark.asyncio
    async def test_handle_message_success(self, ws_client):
        """Test message handling"""
        message_received = []

        async def on_message(data):
            message_received.append(data)

        ws_client.on_message = on_message

        test_message = json.dumps({
            "arg": {"channel": "tickers", "instId": "BTC-USDT"},
            "data": [{"last": "50000"}]
        })

        await ws_client._handle_message(test_message)

        assert len(message_received) == 1
        assert message_received[0]["data"][0]["last"] == "50000"

    @pytest.mark.asyncio
    async def test_handle_message_error_event(self, ws_client):
        """Test handling error event"""
        error_received = []

        async def on_error(error):
            error_received.append(error)

        ws_client.on_error = on_error

        test_message = json.dumps({
            "event": "error",
            "msg": "Test error",
            "code": "50000"
        })

        await ws_client._handle_message(test_message)

        assert len(error_received) == 1

    @pytest.mark.asyncio
    async def test_handle_message_subscribe_event(self, ws_client):
        """Test handling subscribe event"""
        test_message = json.dumps({
            "event": "subscribe",
            "arg": {"channel": "tickers", "instId": "BTC-USDT"}
        })

        await ws_client._handle_message(test_message)

    @pytest.mark.asyncio
    async def test_handle_message_invalid_json(self, ws_client):
        """Test handling invalid JSON"""
        await ws_client._handle_message("invalid json")

    @pytest.mark.asyncio
    async def test_subscribe_tickers(self, ws_client):
        """Test subscribe to tickers"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        await ws_client.subscribe_tickers("BTC-USDT")

        assert {"channel": "tickers", "instId": "BTC-USDT"} in ws_client.subscriptions
        ws_client.ws.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_candles(self, ws_client):
        """Test subscribe to candles"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        await ws_client.subscribe_candles("BTC-USDT", bar="1m")

        assert {"channel": "candle1m", "instId": "BTC-USDT"} in ws_client.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_books(self, ws_client):
        """Test subscribe to order books"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        await ws_client.subscribe_books("BTC-USDT", channel="books5")

        assert {"channel": "books5", "instId": "BTC-USDT"} in ws_client.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_trades(self, ws_client):
        """Test subscribe to trades"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        await ws_client.subscribe_trades("BTC-USDT")

        assert {"channel": "trades", "instId": "BTC-USDT"} in ws_client.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_account(self, ws_client):
        """Test subscribe to account"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        await ws_client.subscribe_account()

        assert {"channel": "account"} in ws_client.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_positions(self, ws_client):
        """Test subscribe to positions"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        await ws_client.subscribe_positions("SWAP")

        assert {"channel": "positions", "instType": "SWAP"} in ws_client.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_orders(self, ws_client):
        """Test subscribe to orders"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        await ws_client.subscribe_orders("SPOT", inst_id="BTC-USDT")

        assert {"channel": "orders", "instType": "SPOT", "instId": "BTC-USDT"} in ws_client.subscriptions

    @pytest.mark.asyncio
    async def test_unsubscribe_tickers(self, ws_client):
        """Test unsubscribe from tickers"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        sub = {"channel": "tickers", "instId": "BTC-USDT"}
        ws_client.subscriptions.append(sub)

        await ws_client.unsubscribe_tickers("BTC-USDT")

        assert sub not in ws_client.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_duplicate(self, ws_client):
        """Test that duplicate subscriptions are not added"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        await ws_client.subscribe_tickers("BTC-USDT")
        await ws_client.subscribe_tickers("BTC-USDT")

        ticker_subs = [s for s in ws_client.subscriptions if s.get("channel") == "tickers"]
        assert len(ticker_subs) == 1

    @pytest.mark.asyncio
    async def test_close(self, ws_client):
        """Test close WebSocket"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False
        ws_client._running = True

        await ws_client.close()

        assert not ws_client._running
        assert not ws_client._reconnect
        ws_client.ws.close.assert_called_once()

    def test_set_reconnect(self, ws_client):
        """Test set reconnect"""
        ws_client.set_reconnect(False)
        assert not ws_client._reconnect

        ws_client.set_reconnect(True)
        assert ws_client._reconnect

    def test_set_reconnect_delay(self, ws_client):
        """Test set reconnect delay"""
        ws_client.set_reconnect_delay(10)
        assert ws_client._reconnect_delay == 10

    def test_callbacks_initialization(self):
        """Test callback initialization"""
        on_message = MagicMock()
        on_error = MagicMock()
        on_close = MagicMock()
        on_open = MagicMock()

        ws = OKXWebSocket(
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        assert ws.on_message == on_message
        assert ws.on_error == on_error
        assert ws.on_close == on_close
        assert ws.on_open == on_open

    @pytest.mark.asyncio
    async def test_send_subscription(self, ws_client):
        """Test send subscription message"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        args = {"channel": "tickers", "instId": "BTC-USDT"}
        await ws_client._send_subscription(args, subscribe=True)

        ws_client.ws.send.assert_called_once()
        call_args = ws_client.ws.send.call_args[0][0]
        message = json.loads(call_args)

        assert message["op"] == "subscribe"
        assert message["args"] == [args]

    @pytest.mark.asyncio
    async def test_send_unsubscription(self, ws_client):
        """Test send unsubscription message"""
        ws_client.ws = AsyncMock()
        ws_client.ws.closed = False

        args = {"channel": "tickers", "instId": "BTC-USDT"}
        await ws_client._send_subscription(args, subscribe=False)

        ws_client.ws.send.assert_called_once()
        call_args = ws_client.ws.send.call_args[0][0]
        message = json.loads(call_args)

        assert message["op"] == "unsubscribe"
