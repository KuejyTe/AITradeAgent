import asyncio
import logging
from typing import List
from decimal import Decimal

from app.models.trading import Order, OrderType, OrderStatus
from app.services.trading.schemas import OrderParams
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class LimitExecution(ExecutionStrategy):
    """Execute order using limit order with timeout"""
    
    def get_name(self) -> str:
        return "limit"
    
    async def execute(self, order_params: OrderParams) -> List[Order]:
        """
        Execute order as limit order with timeout
        
        Args:
            order_params: Order parameters
            
        Returns:
            List containing created order(s)
        """
        timeout = self.config.get('timeout', 60)  # Default 60 seconds
        fallback_to_market = self.config.get('fallback_to_market', True)
        
        logger.info(
            f"Executing limit order: {order_params.side} {order_params.size} "
            f"{order_params.instrument_id} @ {order_params.price} (timeout: {timeout}s)"
        )
        
        # Force limit order type
        order_params.order_type = OrderType.LIMIT
        
        if not order_params.price:
            raise ValueError("Limit execution requires a price")
        
        # Place limit order
        order = await self.executor.place_order(order_params)
        
        # Wait for fill or timeout
        start_time = asyncio.get_event_loop().time()
        check_interval = 2  # Check every 2 seconds
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if elapsed >= timeout:
                logger.warning(f"Limit order {order.id} timed out after {timeout}s")
                
                # Cancel the limit order
                cancelled = await self.executor.cancel_order(order.id)
                
                if cancelled and fallback_to_market:
                    logger.info(f"Falling back to market order for {order.id}")
                    
                    # Get remaining size
                    order = self.executor.order_manager.get_order(order.id)
                    remaining_size = order.size - order.filled_size
                    
                    if remaining_size > 0:
                        # Place market order for remaining size
                        market_params = OrderParams(
                            instrument_id=order_params.instrument_id,
                            side=order_params.side,
                            order_type=OrderType.MARKET,
                            size=remaining_size,
                            trade_mode=order_params.trade_mode,
                            position_side=order_params.position_side,
                            reduce_only=order_params.reduce_only,
                            strategy_id=order_params.strategy_id,
                            metadata=order_params.metadata
                        )
                        
                        market_order = await self.executor.place_order(market_params)
                        return [order, market_order]
                
                break
            
            # Check order status
            order = self.executor.order_manager.get_order(order.id)
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                logger.info(f"Limit order {order.id} completed with status: {order.status}")
                break
            
            await asyncio.sleep(check_interval)
        
        return [order]
