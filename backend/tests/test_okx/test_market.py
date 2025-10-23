import pytest
from unittest.mock import AsyncMock, patch
from app.services.okx.client import OKXClient
from app.services.okx.market import OKXMarket


class TestOKXMarket:
    """Test OKX market data API"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return OKXClient()

    @pytest.fixture
    def market(self, client):
        """Create market instance"""
        return OKXMarket(client)

    @pytest.mark.asyncio
    async def test_get_ticker(self, market, client):
        """Test get ticker"""
        mock_response = [{
            "instId": "BTC-USDT",
            "last": "50000",
            "lastSz": "0.1"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await market.get_ticker("BTC-USDT")
            assert result == mock_response
            client.get.assert_called_once_with(
                '/api/v5/market/ticker',
                params={'instId': 'BTC-USDT'}
            )

    @pytest.mark.asyncio
    async def test_get_tickers(self, market, client):
        """Test get tickers"""
        mock_response = [
            {"instId": "BTC-USDT", "last": "50000"},
            {"instId": "ETH-USDT", "last": "3000"}
        ]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await market.get_tickers("SPOT")
            assert result == mock_response
            client.get.assert_called_once_with(
                '/api/v5/market/tickers',
                params={'instType': 'SPOT'}
            )

    @pytest.mark.asyncio
    async def test_get_candles(self, market, client):
        """Test get candles"""
        mock_response = [
            ["1609459200000", "29000", "29200", "28800", "29100", "100", "2900000", "2900000", "1"]
        ]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await market.get_candles("BTC-USDT", bar="1m", limit=100)
            assert result == mock_response
            client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_book(self, market, client):
        """Test get order book"""
        mock_response = [{
            "asks": [["50000", "1.5", "0", "2"]],
            "bids": [["49999", "2.0", "0", "3"]],
            "ts": "1609459200000"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await market.get_order_book("BTC-USDT", depth=400)
            assert result == mock_response
            client.get.assert_called_once_with(
                '/api/v5/market/books',
                params={'instId': 'BTC-USDT', 'sz': '400'}
            )

    @pytest.mark.asyncio
    async def test_get_trades(self, market, client):
        """Test get trades"""
        mock_response = [
            {
                "instId": "BTC-USDT",
                "tradeId": "12345",
                "px": "50000",
                "sz": "0.1",
                "side": "buy",
                "ts": "1609459200000"
            }
        ]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await market.get_trades("BTC-USDT", limit=100)
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_instruments(self, market, client):
        """Test get instruments"""
        mock_response = [
            {
                "instId": "BTC-USDT",
                "instType": "SPOT",
                "baseCcy": "BTC",
                "quoteCcy": "USDT"
            }
        ]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await market.get_instruments("SPOT")
            assert result == mock_response
            client.get.assert_called_once_with(
                '/api/v5/public/instruments',
                params={'instType': 'SPOT'}
            )

    @pytest.mark.asyncio
    async def test_get_funding_rate(self, market, client):
        """Test get funding rate"""
        mock_response = [{
            "instId": "BTC-USDT-SWAP",
            "fundingRate": "0.0001",
            "fundingTime": "1609459200000"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await market.get_funding_rate("BTC-USDT-SWAP")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_mark_price(self, market, client):
        """Test get mark price"""
        mock_response = [{
            "instId": "BTC-USDT-SWAP",
            "markPx": "50000",
            "ts": "1609459200000"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await market.get_mark_price("BTC-USDT-SWAP", "SWAP")
            assert result == mock_response
