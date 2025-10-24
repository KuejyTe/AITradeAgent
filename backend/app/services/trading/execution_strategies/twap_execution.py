import asyncio
import logging
from typing import List
from decimal import Decimal
from datetime import datetime, timedelta

from app.models.trading import Order, OrderType
from app.services.trading.schemas import OrderParams
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class TWAPExecution(ExecutionStrategy):
    """
    Time-Weighted Average Price (TWAP) execution
    Splits large order into smaller time-based slices
    """
    
    def get_name(self) -> str:
        return "twap"
    
    async def execute(self, order_params: OrderParams) -> List[Order]:
        """
        Execute order using TWAP strategy
        
        Args:
            order_params: Order parameters
            
        Returns:
            List of created orders
        """
        duration = self.config.get('duration', 300)  # Default 5 minutes
        num_slices = self.config.get('num_slices', 10)  # Default 10 slices
        use_limit_orders = self.config.get('use_limit_orders', False)
        price_offset_pct = Decimal(str(self.config.get('price_offset_pct', 0.001)))  # 0.1%
        
        logger.info(
            f"Executing TWAP order: {order_params.side} {order_params.size} "
            f"{order_params.instrument_id} over {duration}s in {num_slices} slices"
        )
        
        # Calculate slice size and interval
        slice_sizes = self._split_size(order_params.size, num_slices)
        interval = duration / num_slices
        
        orders = []
        
        for i, slice_size in enumerate(slice_sizes):
            if slice_size <= 0:
                continue
            
            logger.info(f"Executing TWAP slice {i + 1}/{num_slices}: size={slice_size}")
            
            # Create order parameters for this slice
            slice_params = OrderParams(
                instrument_id=order_params.instrument_id,
                side=order_params.side,
                order_type=OrderType.LIMIT if use_limit_orders else OrderType.MARKET,
                size=slice_size,
                price=None,
                trade_mode=order_params.trade_mode,
                position_side=order_params.position_side,
                reduce_only=order_params.reduce_only,
                strategy_id=order_params.strategy_id,
                metadata={
                    **order_params.metadata,
                    'twap_slice': i + 1,
                    'twap_total_slices': num_slices
                }
            )
            
            # If using limit orders, set price with offset
            if use_limit_orders and order_params.price:
                if order_params.side.value == 'buy':
                    # For buy, set price slightly above to improve fill probability
                    slice_params.price = order_params.price * (Decimal("1") + price_offset_pct)
                else:
                    # For sell, set price slightly below
                    slice_params.price = order_params.price * (Decimal("1") - price_offset_pct)
            
            try:
                # Place order
                order = await self.executor.place_order(slice_params)
                orders.append(order)
            except Exception as e:
                logger.error(f"Error placing TWAP slice {i + 1}: {str(e)}")
                # Continue with remaining slices
            
            # Wait for next interval (except for last slice)
            if i < len(slice_sizes) - 1:
                await asyncio.sleep(interval)
        
        logger.info(f"TWAP execution completed: {len(orders)} orders placed")
        
        return orders
