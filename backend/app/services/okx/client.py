import httpx
import logging
import asyncio
from typing import Dict, Optional, Any
from enum import Enum

from .auth import OKXAuth


logger = logging.getLogger(__name__)


class OKXEnvironment(Enum):
    """OKX API environment"""
    PRODUCTION = "production"
    DEMO = "demo"


class OKXError(Exception):
    """Base exception for OKX API errors"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"OKX API Error {code}: {message}")


class OKXRateLimitError(OKXError):
    """Rate limit exceeded error"""
    pass


class OKXClient:
    """
    Base OKX API client with common functionality
    Handles authentication, rate limiting, error handling, and logging
    """

    BASE_URLS = {
        OKXEnvironment.PRODUCTION: "https://www.okx.com",
        OKXEnvironment.DEMO: "https://www.okx.com"
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        passphrase: Optional[str] = None,
        environment: OKXEnvironment = OKXEnvironment.PRODUCTION,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize OKX client

        Args:
            api_key: OKX API key (optional for public endpoints)
            secret_key: OKX secret key (optional for public endpoints)
            passphrase: OKX API passphrase (optional for public endpoints)
            environment: API environment (production or demo)
            base_url: Custom base URL (overrides environment)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.environment = environment
        self.base_url = base_url or self.BASE_URLS[environment]
        self.timeout = timeout

        self.auth = None
        if api_key and secret_key and passphrase:
            self.auth = OKXAuth(api_key, secret_key, passphrase)

        self.client = httpx.AsyncClient(timeout=timeout)
        self._rate_limit_lock = asyncio.Lock()
        self._last_request_time = 0
        self._min_request_interval = 0.1

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def _rate_limit(self):
        """Rate limiting to prevent exceeding API limits"""
        async with self._rate_limit_lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last_request = current_time - self._last_request_time

            if time_since_last_request < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - time_since_last_request)

            self._last_request_time = asyncio.get_event_loop().time()

    def _handle_response(self, response_data: Dict[str, Any]) -> Any:
        """
        Handle API response and check for errors

        Args:
            response_data: Response data from API

        Returns:
            Response data if successful

        Raises:
            OKXError: If API returns an error
            OKXRateLimitError: If rate limit is exceeded
        """
        code = response_data.get('code', '0')

        if code == '0':
            return response_data.get('data', [])

        msg = response_data.get('msg', 'Unknown error')

        if code in ['50011', '50014']:
            raise OKXRateLimitError(code, msg)

        raise OKXError(code, msg)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        auth_required: bool = False
    ) -> Any:
        """
        Make HTTP request to OKX API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            auth_required: Whether authentication is required

        Returns:
            API response data

        Raises:
            OKXError: If API returns an error
            ValueError: If authentication is required but not configured
        """
        await self._rate_limit()

        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}

        body = ''
        if data:
            import json
            body = json.dumps(data)

        if auth_required:
            if not self.auth:
                raise ValueError("Authentication required but API credentials not provided")
            auth_headers = self.auth.get_headers(method, endpoint, body)
            headers.update(auth_headers)

        logger.debug(f"OKX API Request: {method} {url}")

        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                content=body if body else None,
                headers=headers
            )

            response.raise_for_status()
            response_data = response.json()

            logger.debug(f"OKX API Response: {response_data}")

            return self._handle_response(response_data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise OKXError('HTTP_ERROR', str(e))
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            raise OKXError('REQUEST_ERROR', str(e))
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            raise OKXError('UNKNOWN_ERROR', str(e))

    async def get(self, endpoint: str, params: Optional[Dict] = None, auth_required: bool = False) -> Any:
        """Make GET request"""
        return await self._request('GET', endpoint, params=params, auth_required=auth_required)

    async def post(self, endpoint: str, data: Optional[Dict] = None, auth_required: bool = False) -> Any:
        """Make POST request"""
        return await self._request('POST', endpoint, data=data, auth_required=auth_required)
