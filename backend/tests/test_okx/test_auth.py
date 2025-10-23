import pytest
from datetime import datetime
from app.services.okx.auth import OKXAuth


class TestOKXAuth:
    """Test OKX authentication"""

    def test_auth_initialization(self):
        """Test authentication initialization"""
        auth = OKXAuth(
            api_key="test_key",
            secret_key="test_secret",
            passphrase="test_pass"
        )

        assert auth.api_key == "test_key"
        assert auth.secret_key == "test_secret"
        assert auth.passphrase == "test_pass"

    def test_timestamp_format(self):
        """Test timestamp format"""
        auth = OKXAuth("key", "secret", "pass")
        timestamp = auth._get_timestamp()

        assert timestamp.endswith('Z')
        assert 'T' in timestamp
        assert len(timestamp.split('.')) == 2

    def test_signature_creation(self):
        """Test signature creation"""
        auth = OKXAuth("key", "secret", "pass")
        timestamp = "2023-01-01T00:00:00.000Z"
        signature = auth._create_signature(
            timestamp=timestamp,
            method="GET",
            request_path="/api/v5/account/balance"
        )

        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_signature_with_body(self):
        """Test signature with request body"""
        auth = OKXAuth("key", "secret", "pass")
        timestamp = "2023-01-01T00:00:00.000Z"
        body = '{"instId":"BTC-USDT","side":"buy"}'

        signature = auth._create_signature(
            timestamp=timestamp,
            method="POST",
            request_path="/api/v5/trade/order",
            body=body
        )

        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_get_headers(self):
        """Test header generation"""
        auth = OKXAuth("test_key", "test_secret", "test_pass")
        headers = auth.get_headers(
            method="GET",
            request_path="/api/v5/account/balance"
        )

        assert "OK-ACCESS-KEY" in headers
        assert "OK-ACCESS-SIGN" in headers
        assert "OK-ACCESS-TIMESTAMP" in headers
        assert "OK-ACCESS-PASSPHRASE" in headers
        assert "Content-Type" in headers

        assert headers["OK-ACCESS-KEY"] == "test_key"
        assert headers["OK-ACCESS-PASSPHRASE"] == "test_pass"
        assert headers["Content-Type"] == "application/json"

    def test_get_ws_auth_params(self):
        """Test WebSocket authentication parameters"""
        auth = OKXAuth("test_key", "test_secret", "test_pass")
        params = auth.get_ws_auth_params()

        assert "apiKey" in params
        assert "passphrase" in params
        assert "timestamp" in params
        assert "sign" in params

        assert params["apiKey"] == "test_key"
        assert params["passphrase"] == "test_pass"

    def test_signature_consistency(self):
        """Test that same input produces same signature"""
        auth = OKXAuth("key", "secret", "pass")
        timestamp = "2023-01-01T00:00:00.000Z"

        sig1 = auth._create_signature(timestamp, "GET", "/api/v5/test")
        sig2 = auth._create_signature(timestamp, "GET", "/api/v5/test")

        assert sig1 == sig2

    def test_signature_different_for_different_methods(self):
        """Test that different methods produce different signatures"""
        auth = OKXAuth("key", "secret", "pass")
        timestamp = "2023-01-01T00:00:00.000Z"
        path = "/api/v5/test"

        sig_get = auth._create_signature(timestamp, "GET", path)
        sig_post = auth._create_signature(timestamp, "POST", path)

        assert sig_get != sig_post
