import pytest
from unittest.mock import AsyncMock, patch
from app.services.okx.client import OKXClient
from app.services.okx.trade import OKXTrade


class TestOKXTrade:
    """Test OKX trading API"""

    @pytest.fixture
    def client(self):
        """Create test client with auth"""
        return OKXClient(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass"
        )

    @pytest.fixture
    def trade(self, client):
        """Create trade instance"""
        return OKXTrade(client)

    @pytest.mark.asyncio
    async def test_place_order(self, trade, client):
        """Test place order"""
        mock_response = [{
            "ordId": "123456",
            "clOrdId": "test123",
            "sCode": "0",
            "sMsg": "Order placed successfully"
        }]

        with patch.object(client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.place_order(
                inst_id="BTC-USDT",
                td_mode="cash",
                side="buy",
                ord_type="limit",
                sz="0.01",
                px="50000"
            )
            assert result == mock_response
            client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_place_multiple_orders(self, trade, client):
        """Test place multiple orders"""
        orders = [
            {
                "instId": "BTC-USDT",
                "tdMode": "cash",
                "side": "buy",
                "ordType": "limit",
                "sz": "0.01",
                "px": "50000"
            },
            {
                "instId": "ETH-USDT",
                "tdMode": "cash",
                "side": "buy",
                "ordType": "limit",
                "sz": "0.1",
                "px": "3000"
            }
        ]

        mock_response = [
            {"ordId": "123456", "sCode": "0"},
            {"ordId": "123457", "sCode": "0"}
        ]

        with patch.object(client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.place_multiple_orders(orders)
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_cancel_order_with_ord_id(self, trade, client):
        """Test cancel order with order ID"""
        mock_response = [{
            "ordId": "123456",
            "sCode": "0",
            "sMsg": "Order cancelled"
        }]

        with patch.object(client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.cancel_order(
                inst_id="BTC-USDT",
                ord_id="123456"
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_cancel_order_with_cl_ord_id(self, trade, client):
        """Test cancel order with client order ID"""
        mock_response = [{
            "clOrdId": "test123",
            "sCode": "0",
            "sMsg": "Order cancelled"
        }]

        with patch.object(client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.cancel_order(
                inst_id="BTC-USDT",
                cl_ord_id="test123"
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_cancel_order_without_id(self, trade):
        """Test cancel order without order ID raises error"""
        with pytest.raises(ValueError) as exc_info:
            await trade.cancel_order(inst_id="BTC-USDT")

        assert "Either ord_id or cl_ord_id must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cancel_multiple_orders(self, trade, client):
        """Test cancel multiple orders"""
        orders = [
            {"instId": "BTC-USDT", "ordId": "123456"},
            {"instId": "ETH-USDT", "ordId": "123457"}
        ]

        mock_response = [
            {"ordId": "123456", "sCode": "0"},
            {"ordId": "123457", "sCode": "0"}
        ]

        with patch.object(client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.cancel_multiple_orders(orders)
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_amend_order(self, trade, client):
        """Test amend order"""
        mock_response = [{
            "ordId": "123456",
            "sCode": "0",
            "sMsg": "Order amended"
        }]

        with patch.object(client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.amend_order(
                inst_id="BTC-USDT",
                ord_id="123456",
                new_sz="0.02",
                new_px="51000"
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_amend_order_without_id(self, trade):
        """Test amend order without order ID raises error"""
        with pytest.raises(ValueError) as exc_info:
            await trade.amend_order(inst_id="BTC-USDT", new_sz="0.02")

        assert "Either ord_id or cl_ord_id must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_order(self, trade, client):
        """Test get order"""
        mock_response = [{
            "ordId": "123456",
            "instId": "BTC-USDT",
            "state": "filled",
            "px": "50000",
            "sz": "0.01"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.get_order(
                inst_id="BTC-USDT",
                ord_id="123456"
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_order_without_id(self, trade):
        """Test get order without order ID raises error"""
        with pytest.raises(ValueError) as exc_info:
            await trade.get_order(inst_id="BTC-USDT")

        assert "Either ord_id or cl_ord_id must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_orders_pending(self, trade, client):
        """Test get pending orders"""
        mock_response = [
            {
                "ordId": "123456",
                "instId": "BTC-USDT",
                "state": "live",
                "px": "50000"
            }
        ]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.get_orders_pending()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_order_history(self, trade, client):
        """Test get order history"""
        mock_response = [
            {
                "ordId": "123456",
                "instId": "BTC-USDT",
                "state": "filled",
                "px": "50000"
            }
        ]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.get_order_history(inst_type="SPOT")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_fills(self, trade, client):
        """Test get fills"""
        mock_response = [
            {
                "ordId": "123456",
                "fillPx": "50000",
                "fillSz": "0.01",
                "side": "buy"
            }
        ]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.get_fills()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_close_positions(self, trade, client):
        """Test close positions"""
        mock_response = [{
            "instId": "BTC-USDT-SWAP",
            "sCode": "0",
            "sMsg": "Position closed"
        }]

        with patch.object(client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await trade.close_positions(
                inst_id="BTC-USDT-SWAP",
                mgn_mode="cross"
            )
            assert result == mock_response
