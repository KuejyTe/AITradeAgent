from typing import Optional, List, Dict, Any
from .client import OKXClient


class OKXMarket:
    """
    OKX Market Data API
    Provides access to public market data endpoints
    """

    def __init__(self, client: OKXClient):
        """
        Initialize market data client

        Args:
            client: OKX base client instance
        """
        self.client = client

    async def get_ticker(self, inst_id: str) -> Dict[str, Any]:
        """
        Get ticker information for a specific instrument

        Args:
            inst_id: Instrument ID (e.g., "BTC-USDT")

        Returns:
            Ticker data
        """
        params = {'instId': inst_id}
        return await self.client.get('/api/v5/market/ticker', params=params)

    async def get_tickers(self, inst_type: str, uly: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get ticker information for multiple instruments

        Args:
            inst_type: Instrument type (SPOT, SWAP, FUTURES, OPTION)
            uly: Underlying (e.g., "BTC-USD")

        Returns:
            List of ticker data
        """
        params = {'instType': inst_type}
        if uly:
            params['uly'] = uly
        return await self.client.get('/api/v5/market/tickers', params=params)

    async def get_candles(
        self,
        inst_id: str,
        bar: str = '1m',
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[List[str]]:
        """
        Get candlestick data

        Args:
            inst_id: Instrument ID (e.g., "BTC-USDT")
            bar: Bar size (1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 12H, 1D, 1W, 1M, 3M)
            after: Pagination - data after this timestamp
            before: Pagination - data before this timestamp
            limit: Number of results (max 300)

        Returns:
            List of candlestick data [timestamp, open, high, low, close, volume, volumeCcy, volumeCcyQuote, confirm]
        """
        params = {
            'instId': inst_id,
            'bar': bar,
            'limit': str(limit)
        }
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/market/candles', params=params)

    async def get_history_candles(
        self,
        inst_id: str,
        bar: str = '1m',
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[List[str]]:
        """
        Get candlestick history data (last 3 months)

        Args:
            inst_id: Instrument ID
            bar: Bar size
            after: Pagination - data after this timestamp
            before: Pagination - data before this timestamp
            limit: Number of results (max 100)

        Returns:
            List of candlestick data
        """
        params = {
            'instId': inst_id,
            'bar': bar,
            'limit': str(limit)
        }
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/market/history-candles', params=params)

    async def get_order_book(self, inst_id: str, depth: int = 400) -> Dict[str, Any]:
        """
        Get order book data

        Args:
            inst_id: Instrument ID
            depth: Order book depth (1-400)

        Returns:
            Order book data with asks and bids
        """
        params = {
            'instId': inst_id,
            'sz': str(depth)
        }
        return await self.client.get('/api/v5/market/books', params=params)

    async def get_trades(self, inst_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent trades

        Args:
            inst_id: Instrument ID
            limit: Number of results (max 500)

        Returns:
            List of recent trades
        """
        params = {
            'instId': inst_id,
            'limit': str(limit)
        }
        return await self.client.get('/api/v5/market/trades', params=params)

    async def get_history_trades(
        self,
        inst_id: str,
        type: str = '1',
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical trades

        Args:
            inst_id: Instrument ID
            type: Pagination type (1: tradeId, 2: timestamp)
            after: Pagination - data after this value
            before: Pagination - data before this value
            limit: Number of results (max 100)

        Returns:
            List of historical trades
        """
        params = {
            'instId': inst_id,
            'type': type,
            'limit': str(limit)
        }
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/market/history-trades', params=params)

    async def get_instruments(
        self,
        inst_type: str,
        uly: Optional[str] = None,
        inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get instrument information

        Args:
            inst_type: Instrument type (SPOT, MARGIN, SWAP, FUTURES, OPTION)
            uly: Underlying (e.g., "BTC-USD")
            inst_id: Instrument ID

        Returns:
            List of instrument information
        """
        params = {'instType': inst_type}
        if uly:
            params['uly'] = uly
        if inst_id:
            params['instId'] = inst_id

        return await self.client.get('/api/v5/public/instruments', params=params)

    async def get_funding_rate(self, inst_id: str) -> Dict[str, Any]:
        """
        Get funding rate (for perpetual swaps)

        Args:
            inst_id: Instrument ID

        Returns:
            Funding rate data
        """
        params = {'instId': inst_id}
        return await self.client.get('/api/v5/public/funding-rate', params=params)

    async def get_funding_rate_history(
        self,
        inst_id: str,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get funding rate history

        Args:
            inst_id: Instrument ID
            after: Pagination - data after this timestamp
            before: Pagination - data before this timestamp
            limit: Number of results (max 100)

        Returns:
            List of funding rate history
        """
        params = {
            'instId': inst_id,
            'limit': str(limit)
        }
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/public/funding-rate-history', params=params)

    async def get_index_tickers(
        self,
        inst_id: Optional[str] = None,
        quote_ccy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get index tickers

        Args:
            inst_id: Instrument ID
            quote_ccy: Quote currency

        Returns:
            List of index tickers
        """
        params = {}
        if inst_id:
            params['instId'] = inst_id
        if quote_ccy:
            params['quoteCcy'] = quote_ccy

        return await self.client.get('/api/v5/market/index-tickers', params=params)

    async def get_mark_price(self, inst_id: str, inst_type: str) -> Dict[str, Any]:
        """
        Get mark price

        Args:
            inst_id: Instrument ID
            inst_type: Instrument type

        Returns:
            Mark price data
        """
        params = {
            'instId': inst_id,
            'instType': inst_type
        }
        return await self.client.get('/api/v5/public/mark-price', params=params)
