import pytest
from unittest.mock import AsyncMock, patch
from app.services.okx.client import OKXClient
from app.services.okx.account import OKXAccount


class TestOKXAccount:
    """Test OKX account API"""

    @pytest.fixture
    def client(self):
        """Create test client with auth"""
        return OKXClient(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass"
        )

    @pytest.fixture
    def account(self, client):
        """Create account instance"""
        return OKXAccount(client)

    @pytest.mark.asyncio
    async def test_get_balance(self, account, client):
        """Test get balance"""
        mock_response = [{
            "totalEq": "100000",
            "details": [
                {"ccy": "USDT", "availBal": "50000", "frozenBal": "0"}
            ]
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await account.get_balance()
            assert result == mock_response
            client.get.assert_called_once_with(
                '/api/v5/account/balance',
                params={},
                auth_required=True
            )

    @pytest.mark.asyncio
    async def test_get_balance_with_currency(self, account, client):
        """Test get balance for specific currency"""
        mock_response = [{
            "details": [
                {"ccy": "BTC", "availBal": "1.5", "frozenBal": "0"}
            ]
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await account.get_balance(ccy="BTC")
            assert result == mock_response
            client.get.assert_called_once_with(
                '/api/v5/account/balance',
                params={'ccy': 'BTC'},
                auth_required=True
            )

    @pytest.mark.asyncio
    async def test_get_positions(self, account, client):
        """Test get positions"""
        mock_response = [{
            "instId": "BTC-USDT-SWAP",
            "pos": "10",
            "avgPx": "50000",
            "upl": "1000"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await account.get_positions()
            assert result == mock_response
            client.get.assert_called_once_with(
                '/api/v5/account/positions',
                params={},
                auth_required=True
            )

    @pytest.mark.asyncio
    async def test_get_account_config(self, account, client):
        """Test get account config"""
        mock_response = [{
            "acctLv": "2",
            "posMode": "long_short_mode",
            "autoLoan": False
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await account.get_account_config()
            assert result == mock_response
            client.get.assert_called_once_with(
                '/api/v5/account/config',
                auth_required=True
            )

    @pytest.mark.asyncio
    async def test_set_leverage(self, account, client):
        """Test set leverage"""
        mock_response = [{
            "instId": "BTC-USDT-SWAP",
            "lever": "10",
            "mgnMode": "cross"
        }]

        with patch.object(client, 'post', new_callable=AsyncMock, return_value=mock_response):
            result = await account.set_leverage(
                inst_id="BTC-USDT-SWAP",
                lever="10",
                mgn_mode="cross"
            )
            assert result == mock_response
            client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_max_size(self, account, client):
        """Test get max size"""
        mock_response = [{
            "instId": "BTC-USDT",
            "maxBuy": "100",
            "maxSell": "100"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await account.get_max_size(
                inst_id="BTC-USDT",
                td_mode="cross"
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_max_avail_size(self, account, client):
        """Test get max available size"""
        mock_response = [{
            "instId": "BTC-USDT",
            "availBuy": "50",
            "availSell": "50"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await account.get_max_avail_size(
                inst_id="BTC-USDT",
                td_mode="cash"
            )
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_bills(self, account, client):
        """Test get bills"""
        mock_response = [{
            "billId": "12345",
            "type": "1",
            "bal": "100",
            "balChg": "10"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await account.get_bills()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_max_loan(self, account, client):
        """Test get max loan"""
        mock_response = [{
            "instId": "BTC-USDT",
            "maxLoan": "1000",
            "ccy": "USDT"
        }]

        with patch.object(client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await account.get_max_loan(
                inst_id="BTC-USDT",
                mgn_mode="cross"
            )
            assert result == mock_response
