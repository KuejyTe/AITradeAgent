import hmac
import base64
import hashlib
from datetime import datetime, timezone
from typing import Dict, Optional


class OKXAuth:
    """
    OKX API authentication handler
    Implements HMAC SHA256 signature algorithm for OKX API requests
    """

    def __init__(self, api_key: str, secret_key: str, passphrase: str):
        """
        Initialize OKX authentication

        Args:
            api_key: OKX API key
            secret_key: OKX secret key
            passphrase: OKX API passphrase
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def _get_timestamp(self) -> str:
        """Get current ISO 8601 timestamp"""
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def _create_signature(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """
        Create HMAC SHA256 signature for OKX API

        Args:
            timestamp: ISO 8601 timestamp
            method: HTTP method (GET, POST, etc.)
            request_path: API endpoint path
            body: Request body (empty string for GET requests)

        Returns:
            Base64 encoded signature
        """
        message = timestamp + method.upper() + request_path + body
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf8'),
            bytes(message, encoding='utf8'),
            digestmod=hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()

    def get_headers(self, method: str, request_path: str, body: str = '') -> Dict[str, str]:
        """
        Generate authentication headers for OKX API request

        Args:
            method: HTTP method (GET, POST, etc.)
            request_path: API endpoint path
            body: Request body (empty string for GET requests)

        Returns:
            Dictionary of authentication headers
        """
        timestamp = self._get_timestamp()
        signature = self._create_signature(timestamp, method, request_path, body)

        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }

    def get_ws_auth_params(self) -> Dict[str, str]:
        """
        Generate authentication parameters for WebSocket connection

        Returns:
            Dictionary of authentication parameters for WebSocket
        """
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        message = timestamp + 'GET' + '/users/self/verify'
        signature = self._create_signature(timestamp, 'GET', '/users/self/verify')

        return {
            'apiKey': self.api_key,
            'passphrase': self.passphrase,
            'timestamp': timestamp,
            'sign': signature
        }
