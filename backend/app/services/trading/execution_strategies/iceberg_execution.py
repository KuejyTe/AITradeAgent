import asyncio
import logging
from typing import List
from decimal import Decimal

from app.models.trading import Order, OrderType, OrderStatus
from app.services.trading.schemas import OrderParams
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class IcebergExecution(ExecutionStrategy):
    """
    Iceberg order execution
    Only displays partial quantity, gradually releasing more as fills occur
    """
    
    def get_name(self) -> str:
        return "iceberg"
    
    async def execute(self, order_params: OrderParams) -> List[Order]:
        """
        Execute order using iceberg strategy
        
        Args:
            order_params: Order parameters
            
        Returns:
            List of created orders
        """
        visible_pct = Decimal(str(self.config.get('visible_pct', 0.1)))  # Default 10% visible
        max_refresh_time = self.config.get('max_refresh_time', 30)  # Seconds to wait before refreshing
        use_limit_orders = self.config.get('use_limit_orders', True)
        
        logger.info(
            f"Executing iceberg order: {order_params.side} {order_params.size} "
            f"{order_params.instrument_id} (visible: {visible_pct * 100}%)"
        )
        
        if not order_params.price and use_limit_orders:
            raise ValueError("Iceberg execution with limit orders requires a price")
        
        total_size = order_params.size
        filled_size = Decimal("0")
        orders = []
        
        while filled_size < total_size:
            remaining_size = total_size - filled_size
            
            # Calculate visible size (minimum of visible_pct or remaining)
            visible_size = min(remaining_size, total_size * visible_pct)
            
            # Ensure visible size meets minimum
            min_size = Decimal(str(self.config.get('min_visible_size', 0.001)))
            visible_size = max(visible_size, min_size)
            visible_size = min(visible_size, remaining_size)
            
            if visible_size <= 0:
                break
            
            logger.info(
                f"Placing iceberg slice: {visible_size} / {remaining_size} remaining"
            )
            
            # Create order parameters for this slice
            slice_params = OrderParams(
                instrument_id=order_params.instrument_id,
                side=order_params.side,
                order_type=OrderType.LIMIT if use_limit_orders else OrderType.MARKET,
                size=visible_size,
                price=order_params.price if use_limit_orders else None,
                trade_mode=order_params.trade_mode,
                position_side=order_params.position_side,
                reduce_only=order_params.reduce_only,
                strategy_id=order_params.strategy_id,
                metadata={
                    **order_params.metadata,
                    'iceberg_part': len(orders) + 1,
                    'iceberg_total_size': str(total_size),
                    'iceberg_filled': str(filled_size)
                }
            )
            
            try:
                # Place order
                order = await self.executor.place_order(slice_params)
                orders.append(order)
                
                # Wait for order to fill or timeout
                start_time = asyncio.get_event_loop().time()
                check_interval = 2  # Check every 2 seconds
                
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    
                    if elapsed >= max_refresh_time:
                        logger.info(f"Iceberg slice {order.id} timeout, refreshing")
                        # Cancel and place new order
                        await self.executor.cancel_order(order.id)
                        break
                    
                    # Check order status
                    order = self.executor.order_manager.get_order(order.id)
                    
                    if order.status == OrderStatus.FILLED:
                        logger.info(f"Iceberg slice {order.id} filled: {order.filled_size}")
                        filled_size += order.filled_size
                        break
                    elif order.status == OrderStatus.PARTIALLY_FILLED:
                        # Wait a bit more for full fill
                        if elapsed >= max_refresh_time / 2:
                            # Cancel and place new order for remaining
                            remaining_in_order = order.size - order.filled_size
                            if remaining_in_order > 0:
                                await self.executor.cancel_order(order.id)
                                filled_size += order.filled_size
                                break
                    elif order.status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                        logger.warning(f"Iceberg slice {order.id} {order.status}")
                        filled_size += order.filled_size
                        break
                    
                    await asyncio.sleep(check_interval)
            
            except Exception as e:
                logger.error(f"Error placing iceberg slice: {str(e)}")
                # Stop execution on error
                break
            
            # Small delay before next slice
            await asyncio.sleep(1)
        
        logger.info(
            f"Iceberg execution completed: {filled_size} / {total_size} filled "
            f"in {len(orders)} orders"
        )
        
        return orders
