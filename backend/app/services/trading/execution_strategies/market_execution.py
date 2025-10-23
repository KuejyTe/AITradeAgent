import logging
from typing import List

from app.models.trading import Order, OrderType
from app.services.trading.schemas import OrderParams
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class MarketExecution(ExecutionStrategy):
    """Execute order immediately at market price"""
    
    def get_name(self) -> str:
        return "market"
    
    async def execute(self, order_params: OrderParams) -> List[Order]:
        """
        Execute order as market order
        
        Args:
            order_params: Order parameters
            
        Returns:
            List containing single created order
        """
        logger.info(f"Executing market order: {order_params.side} {order_params.size} {order_params.instrument_id}")
        
        # Force market order type
        order_params.order_type = OrderType.MARKET
        order_params.price = None  # Market orders don't have price
        
        # Place order
        order = await self.executor.place_order(order_params)
        
        return [order]
