import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.okx.client import OKXClient, OKXError, OKXRateLimitError, OKXEnvironment


class TestOKXClient:
    """Test OKX client"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return OKXClient(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass"
        )

    @pytest.fixture
    def client_no_auth(self):
        """Create test client without authentication"""
        return OKXClient()

    def test_client_initialization(self, client):
        """Test client initialization"""
        assert client.api_key == "test_key"
        assert client.secret_key == "test_secret"
        assert client.passphrase == "test_pass"
        assert client.auth is not None

    def test_client_initialization_no_auth(self, client_no_auth):
        """Test client initialization without auth"""
        assert client_no_auth.api_key is None
        assert client_no_auth.secret_key is None
        assert client_no_auth.passphrase is None
        assert client_no_auth.auth is None

    def test_environment_urls(self):
        """Test environment URLs"""
        prod_client = OKXClient(environment=OKXEnvironment.PRODUCTION)
        assert prod_client.base_url == "https://www.okx.com"

        demo_client = OKXClient(environment=OKXEnvironment.DEMO)
        assert demo_client.base_url == "https://www.okx.com"

    def test_custom_base_url(self):
        """Test custom base URL"""
        custom_url = "https://custom.okx.com"
        client = OKXClient(base_url=custom_url)
        assert client.base_url == custom_url

    def test_handle_response_success(self, client):
        """Test successful response handling"""
        response = {
            "code": "0",
            "data": [{"test": "data"}],
            "msg": ""
        }

        result = client._handle_response(response)
        assert result == [{"test": "data"}]

    def test_handle_response_error(self, client):
        """Test error response handling"""
        response = {
            "code": "50000",
            "data": [],
            "msg": "Test error"
        }

        with pytest.raises(OKXError) as exc_info:
            client._handle_response(response)

        assert exc_info.value.code == "50000"
        assert exc_info.value.message == "Test error"

    def test_handle_response_rate_limit(self, client):
        """Test rate limit error handling"""
        response = {
            "code": "50011",
            "data": [],
            "msg": "Rate limit exceeded"
        }

        with pytest.raises(OKXRateLimitError) as exc_info:
            client._handle_response(response)

        assert exc_info.value.code == "50011"

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test client close"""
        with patch.object(client.client, 'aclose', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_requires_auth_without_credentials(self, client_no_auth):
        """Test request requiring auth without credentials"""
        with pytest.raises(ValueError) as exc_info:
            await client_no_auth._request(
                method="GET",
                endpoint="/api/v5/account/balance",
                auth_required=True
            )

        assert "Authentication required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        async with OKXClient() as client:
            assert client is not None
            assert client.client is not None
