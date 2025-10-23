from typing import Optional, List, Dict, Any
from .client import OKXClient


class OKXTrade:
    """
    OKX Trading API
    Provides access to trading endpoints (requires authentication)
    """

    def __init__(self, client: OKXClient):
        """
        Initialize trading client

        Args:
            client: OKX base client instance
        """
        self.client = client

    async def place_order(
        self,
        inst_id: str,
        td_mode: str,
        side: str,
        ord_type: str,
        sz: str,
        ccy: Optional[str] = None,
        cl_ord_id: Optional[str] = None,
        tag: Optional[str] = None,
        pos_side: Optional[str] = None,
        px: Optional[str] = None,
        reduce_only: Optional[bool] = None,
        tgt_ccy: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Place a new order

        Args:
            inst_id: Instrument ID (e.g., "BTC-USDT")
            td_mode: Trade mode (cash, cross, isolated)
            side: Order side (buy, sell)
            ord_type: Order type (market, limit, post_only, fok, ioc)
            sz: Quantity to buy or sell
            ccy: Currency (for margin trading)
            cl_ord_id: Client-supplied order ID
            tag: Order tag
            pos_side: Position side (long, short) - required in long/short mode
            px: Order price (required for limit orders)
            reduce_only: Whether to reduce position only
            tgt_ccy: Target currency (base_ccy, quote_ccy)
            **kwargs: Additional parameters

        Returns:
            Order response data
        """
        data = {
            'instId': inst_id,
            'tdMode': td_mode,
            'side': side,
            'ordType': ord_type,
            'sz': sz
        }

        if ccy:
            data['ccy'] = ccy
        if cl_ord_id:
            data['clOrdId'] = cl_ord_id
        if tag:
            data['tag'] = tag
        if pos_side:
            data['posSide'] = pos_side
        if px:
            data['px'] = px
        if reduce_only is not None:
            data['reduceOnly'] = reduce_only
        if tgt_ccy:
            data['tgtCcy'] = tgt_ccy

        data.update(kwargs)

        return await self.client.post('/api/v5/trade/order', data=data, auth_required=True)

    async def place_multiple_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Place multiple orders (up to 20 orders)

        Args:
            orders: List of order parameters

        Returns:
            List of order responses
        """
        data = orders
        return await self.client.post('/api/v5/trade/batch-orders', data=data, auth_required=True)

    async def cancel_order(
        self,
        inst_id: str,
        ord_id: Optional[str] = None,
        cl_ord_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an order

        Args:
            inst_id: Instrument ID
            ord_id: Order ID
            cl_ord_id: Client-supplied order ID

        Returns:
            Cancellation response
        """
        if not ord_id and not cl_ord_id:
            raise ValueError("Either ord_id or cl_ord_id must be provided")

        data = {'instId': inst_id}
        if ord_id:
            data['ordId'] = ord_id
        if cl_ord_id:
            data['clOrdId'] = cl_ord_id

        return await self.client.post('/api/v5/trade/cancel-order', data=data, auth_required=True)

    async def cancel_multiple_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cancel multiple orders (up to 20 orders)

        Args:
            orders: List of order cancellation parameters

        Returns:
            List of cancellation responses
        """
        data = orders
        return await self.client.post('/api/v5/trade/cancel-batch-orders', data=data, auth_required=True)

    async def amend_order(
        self,
        inst_id: str,
        ord_id: Optional[str] = None,
        cl_ord_id: Optional[str] = None,
        req_id: Optional[str] = None,
        new_sz: Optional[str] = None,
        new_px: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Amend an existing order

        Args:
            inst_id: Instrument ID
            ord_id: Order ID
            cl_ord_id: Client-supplied order ID
            req_id: Request ID
            new_sz: New quantity
            new_px: New price

        Returns:
            Amendment response
        """
        if not ord_id and not cl_ord_id:
            raise ValueError("Either ord_id or cl_ord_id must be provided")

        data = {'instId': inst_id}
        if ord_id:
            data['ordId'] = ord_id
        if cl_ord_id:
            data['clOrdId'] = cl_ord_id
        if req_id:
            data['reqId'] = req_id
        if new_sz:
            data['newSz'] = new_sz
        if new_px:
            data['newPx'] = new_px

        return await self.client.post('/api/v5/trade/amend-order', data=data, auth_required=True)

    async def amend_multiple_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Amend multiple orders (up to 20 orders)

        Args:
            orders: List of order amendment parameters

        Returns:
            List of amendment responses
        """
        data = orders
        return await self.client.post('/api/v5/trade/amend-batch-orders', data=data, auth_required=True)

    async def close_positions(
        self,
        inst_id: str,
        mgn_mode: str,
        pos_side: Optional[str] = None,
        ccy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close all positions for an instrument

        Args:
            inst_id: Instrument ID
            mgn_mode: Margin mode (cross, isolated)
            pos_side: Position side (long, short)
            ccy: Currency

        Returns:
            Response data
        """
        data = {
            'instId': inst_id,
            'mgnMode': mgn_mode
        }
        if pos_side:
            data['posSide'] = pos_side
        if ccy:
            data['ccy'] = ccy

        return await self.client.post('/api/v5/trade/close-position', data=data, auth_required=True)

    async def get_order(
        self,
        inst_id: str,
        ord_id: Optional[str] = None,
        cl_ord_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get order details

        Args:
            inst_id: Instrument ID
            ord_id: Order ID
            cl_ord_id: Client-supplied order ID

        Returns:
            Order details
        """
        if not ord_id and not cl_ord_id:
            raise ValueError("Either ord_id or cl_ord_id must be provided")

        params = {'instId': inst_id}
        if ord_id:
            params['ordId'] = ord_id
        if cl_ord_id:
            params['clOrdId'] = cl_ord_id

        return await self.client.get('/api/v5/trade/order', params=params, auth_required=True)

    async def get_orders_pending(
        self,
        inst_type: Optional[str] = None,
        uly: Optional[str] = None,
        inst_id: Optional[str] = None,
        ord_type: Optional[str] = None,
        state: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get pending orders

        Args:
            inst_type: Instrument type
            uly: Underlying
            inst_id: Instrument ID
            ord_type: Order type
            state: State (live, partially_filled)
            after: Pagination - data after this order ID
            before: Pagination - data before this order ID
            limit: Number of results (max 100)

        Returns:
            List of pending orders
        """
        params = {'limit': str(limit)}
        if inst_type:
            params['instType'] = inst_type
        if uly:
            params['uly'] = uly
        if inst_id:
            params['instId'] = inst_id
        if ord_type:
            params['ordType'] = ord_type
        if state:
            params['state'] = state
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/trade/orders-pending', params=params, auth_required=True)

    async def get_order_history(
        self,
        inst_type: str,
        uly: Optional[str] = None,
        inst_id: Optional[str] = None,
        ord_type: Optional[str] = None,
        state: Optional[str] = None,
        category: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get order history (last 7 days)

        Args:
            inst_type: Instrument type
            uly: Underlying
            inst_id: Instrument ID
            ord_type: Order type
            state: State (canceled, filled, mmp_canceled)
            category: Category
            after: Pagination - data after this order ID
            before: Pagination - data before this order ID
            limit: Number of results (max 100)

        Returns:
            List of historical orders
        """
        params = {
            'instType': inst_type,
            'limit': str(limit)
        }
        if uly:
            params['uly'] = uly
        if inst_id:
            params['instId'] = inst_id
        if ord_type:
            params['ordType'] = ord_type
        if state:
            params['state'] = state
        if category:
            params['category'] = category
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/trade/orders-history', params=params, auth_required=True)

    async def get_order_history_archive(
        self,
        inst_type: str,
        uly: Optional[str] = None,
        inst_id: Optional[str] = None,
        ord_type: Optional[str] = None,
        state: Optional[str] = None,
        category: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get order history archive (last 3 months)

        Args:
            inst_type: Instrument type
            uly: Underlying
            inst_id: Instrument ID
            ord_type: Order type
            state: State
            category: Category
            after: Pagination - data after this order ID
            before: Pagination - data before this order ID
            limit: Number of results (max 100)

        Returns:
            List of archived orders
        """
        params = {
            'instType': inst_type,
            'limit': str(limit)
        }
        if uly:
            params['uly'] = uly
        if inst_id:
            params['instId'] = inst_id
        if ord_type:
            params['ordType'] = ord_type
        if state:
            params['state'] = state
        if category:
            params['category'] = category
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/trade/orders-history-archive', params=params, auth_required=True)

    async def get_fills(
        self,
        inst_type: Optional[str] = None,
        uly: Optional[str] = None,
        inst_id: Optional[str] = None,
        ord_id: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transaction details (last 7 days)

        Args:
            inst_type: Instrument type
            uly: Underlying
            inst_id: Instrument ID
            ord_id: Order ID
            after: Pagination - data after this bill ID
            before: Pagination - data before this bill ID
            limit: Number of results (max 100)

        Returns:
            List of fills
        """
        params = {'limit': str(limit)}
        if inst_type:
            params['instType'] = inst_type
        if uly:
            params['uly'] = uly
        if inst_id:
            params['instId'] = inst_id
        if ord_id:
            params['ordId'] = ord_id
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/trade/fills', params=params, auth_required=True)

    async def get_fills_history(
        self,
        inst_type: str,
        uly: Optional[str] = None,
        inst_id: Optional[str] = None,
        ord_id: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transaction details history (last 3 months)

        Args:
            inst_type: Instrument type
            uly: Underlying
            inst_id: Instrument ID
            ord_id: Order ID
            after: Pagination - data after this bill ID
            before: Pagination - data before this bill ID
            limit: Number of results (max 100)

        Returns:
            List of historical fills
        """
        params = {
            'instType': inst_type,
            'limit': str(limit)
        }
        if uly:
            params['uly'] = uly
        if inst_id:
            params['instId'] = inst_id
        if ord_id:
            params['ordId'] = ord_id
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/trade/fills-history', params=params, auth_required=True)
