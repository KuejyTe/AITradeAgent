from typing import Optional, List, Dict, Any
from .client import OKXClient


class OKXAccount:
    """
    OKX Account API
    Provides access to account-related endpoints (requires authentication)
    """

    def __init__(self, client: OKXClient):
        """
        Initialize account client

        Args:
            client: OKX base client instance
        """
        self.client = client

    async def get_balance(self, ccy: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get account balance

        Args:
            ccy: Single currency or multiple currencies (comma-separated)

        Returns:
            List of balance data
        """
        params = {}
        if ccy:
            params['ccy'] = ccy

        return await self.client.get('/api/v5/account/balance', params=params, auth_required=True)

    async def get_positions(
        self,
        inst_type: Optional[str] = None,
        inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get position information

        Args:
            inst_type: Instrument type (MARGIN, SWAP, FUTURES, OPTION)
            inst_id: Instrument ID

        Returns:
            List of position data
        """
        params = {}
        if inst_type:
            params['instType'] = inst_type
        if inst_id:
            params['instId'] = inst_id

        return await self.client.get('/api/v5/account/positions', params=params, auth_required=True)

    async def get_positions_history(
        self,
        inst_type: Optional[str] = None,
        inst_id: Optional[str] = None,
        mgnMode: Optional[str] = None,
        type: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get position history (last 3 months)

        Args:
            inst_type: Instrument type
            inst_id: Instrument ID
            mgnMode: Margin mode (cross, isolated)
            type: Position type
            after: Pagination - data after this timestamp
            before: Pagination - data before this timestamp
            limit: Number of results (max 100)

        Returns:
            List of position history
        """
        params = {'limit': str(limit)}
        if inst_type:
            params['instType'] = inst_type
        if inst_id:
            params['instId'] = inst_id
        if mgnMode:
            params['mgnMode'] = mgnMode
        if type:
            params['type'] = type
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/account/positions-history', params=params, auth_required=True)

    async def get_account_config(self) -> Dict[str, Any]:
        """
        Get account configuration

        Returns:
            Account configuration data
        """
        return await self.client.get('/api/v5/account/config', auth_required=True)

    async def set_position_mode(self, pos_mode: str) -> Dict[str, Any]:
        """
        Set position mode

        Args:
            pos_mode: Position mode (long_short_mode, net_mode)

        Returns:
            Response data
        """
        data = {'posMode': pos_mode}
        return await self.client.post('/api/v5/account/set-position-mode', data=data, auth_required=True)

    async def set_leverage(
        self,
        inst_id: str,
        lever: str,
        mgn_mode: str,
        pos_side: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set leverage

        Args:
            inst_id: Instrument ID
            lever: Leverage
            mgn_mode: Margin mode (cross, isolated)
            pos_side: Position side (long, short) - required in long/short mode

        Returns:
            Response data
        """
        data = {
            'instId': inst_id,
            'lever': lever,
            'mgnMode': mgn_mode
        }
        if pos_side:
            data['posSide'] = pos_side

        return await self.client.post('/api/v5/account/set-leverage', data=data, auth_required=True)

    async def get_max_size(
        self,
        inst_id: str,
        td_mode: str,
        ccy: Optional[str] = None,
        px: Optional[str] = None,
        leverage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get maximum buy/sell amount or open amount

        Args:
            inst_id: Instrument ID
            td_mode: Trade mode (cross, isolated, cash)
            ccy: Currency (for margin trading)
            px: Price
            leverage: Leverage

        Returns:
            Maximum size data
        """
        params = {
            'instId': inst_id,
            'tdMode': td_mode
        }
        if ccy:
            params['ccy'] = ccy
        if px:
            params['px'] = px
        if leverage:
            params['leverage'] = leverage

        return await self.client.get('/api/v5/account/max-size', params=params, auth_required=True)

    async def get_max_avail_size(
        self,
        inst_id: str,
        td_mode: str,
        ccy: Optional[str] = None,
        reduce_only: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get maximum available tradable amount

        Args:
            inst_id: Instrument ID
            td_mode: Trade mode (cross, isolated, cash)
            ccy: Currency
            reduce_only: Whether to reduce position only

        Returns:
            Maximum available size data
        """
        params = {
            'instId': inst_id,
            'tdMode': td_mode
        }
        if ccy:
            params['ccy'] = ccy
        if reduce_only is not None:
            params['reduceOnly'] = str(reduce_only).lower()

        return await self.client.get('/api/v5/account/max-avail-size', params=params, auth_required=True)

    async def get_account_position_risk(self, inst_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get account position risk

        Args:
            inst_type: Instrument type

        Returns:
            List of position risk data
        """
        params = {}
        if inst_type:
            params['instType'] = inst_type

        return await self.client.get('/api/v5/account/account-position-risk', params=params, auth_required=True)

    async def get_bills(
        self,
        inst_type: Optional[str] = None,
        ccy: Optional[str] = None,
        mgn_mode: Optional[str] = None,
        ct_type: Optional[str] = None,
        type: Optional[str] = None,
        sub_type: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get bills details (last 7 days)

        Args:
            inst_type: Instrument type
            ccy: Currency
            mgn_mode: Margin mode
            ct_type: Contract type
            type: Bill type
            sub_type: Bill sub type
            after: Pagination - data after this bill ID
            before: Pagination - data before this bill ID
            limit: Number of results (max 100)

        Returns:
            List of bills
        """
        params = {'limit': str(limit)}
        if inst_type:
            params['instType'] = inst_type
        if ccy:
            params['ccy'] = ccy
        if mgn_mode:
            params['mgnMode'] = mgn_mode
        if ct_type:
            params['ctType'] = ct_type
        if type:
            params['type'] = type
        if sub_type:
            params['subType'] = sub_type
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/account/bills', params=params, auth_required=True)

    async def get_bills_archive(
        self,
        inst_type: Optional[str] = None,
        ccy: Optional[str] = None,
        mgn_mode: Optional[str] = None,
        ct_type: Optional[str] = None,
        type: Optional[str] = None,
        sub_type: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get bills details (archived, last 3 months)

        Args:
            inst_type: Instrument type
            ccy: Currency
            mgn_mode: Margin mode
            ct_type: Contract type
            type: Bill type
            sub_type: Bill sub type
            after: Pagination - data after this bill ID
            before: Pagination - data before this bill ID
            limit: Number of results (max 100)

        Returns:
            List of archived bills
        """
        params = {'limit': str(limit)}
        if inst_type:
            params['instType'] = inst_type
        if ccy:
            params['ccy'] = ccy
        if mgn_mode:
            params['mgnMode'] = mgn_mode
        if ct_type:
            params['ctType'] = ct_type
        if type:
            params['type'] = type
        if sub_type:
            params['subType'] = sub_type
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/account/bills-archive', params=params, auth_required=True)

    async def get_interest_accrued(
        self,
        inst_id: Optional[str] = None,
        ccy: Optional[str] = None,
        mgn_mode: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get interest accrued data

        Args:
            inst_id: Instrument ID
            ccy: Currency
            mgn_mode: Margin mode
            after: Pagination - data after this timestamp
            before: Pagination - data before this timestamp
            limit: Number of results (max 100)

        Returns:
            List of interest accrued data
        """
        params = {'limit': str(limit)}
        if inst_id:
            params['instId'] = inst_id
        if ccy:
            params['ccy'] = ccy
        if mgn_mode:
            params['mgnMode'] = mgn_mode
        if after:
            params['after'] = after
        if before:
            params['before'] = before

        return await self.client.get('/api/v5/account/interest-accrued', params=params, auth_required=True)

    async def get_max_loan(
        self,
        inst_id: str,
        mgn_mode: str,
        mgn_ccy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get maximum loan amount

        Args:
            inst_id: Instrument ID
            mgn_mode: Margin mode (cross, isolated)
            mgn_ccy: Margin currency

        Returns:
            Maximum loan data
        """
        params = {
            'instId': inst_id,
            'mgnMode': mgn_mode
        }
        if mgn_ccy:
            params['mgnCcy'] = mgn_ccy

        return await self.client.get('/api/v5/account/max-loan', params=params, auth_required=True)
