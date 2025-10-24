import asyncio
import logging
from typing import Dict, Callable, Optional, Any
from decimal import Decimal

from app.services.trading.order_manager import OrderManager
from app.models.trading import OrderStatus

logger = logging.getLogger(__name__)


class OrderTracker:
    """Tracks order status updates via WebSocket and polling"""
    
    def __init__(self, okx_client, order_manager: OrderManager):
        self.okx_client = okx_client
        self.order_manager = order_manager
        self.tracked_orders: Dict[str, Dict[str, Any]] = {}
        self.callbacks: Dict[str, list[Callable]] = {}
        self.polling_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_tracking(
        self,
        order_id: int,
        exchange_order_id: str,
        instrument_id: str,
        callback: Optional[Callable] = None
    ):
        """
        Start tracking an order
        
        Args:
            order_id: Internal order ID
            exchange_order_id: Exchange order ID
            instrument_id: Instrument ID
            callback: Optional callback function for updates
        """
        if exchange_order_id in self.tracked_orders:
            logger.warning(f"Order {exchange_order_id} is already being tracked")
            return
        
        self.tracked_orders[exchange_order_id] = {
            'order_id': order_id,
            'exchange_order_id': exchange_order_id,
            'instrument_id': instrument_id,
        }
        
        if callback:
            if exchange_order_id not in self.callbacks:
                self.callbacks[exchange_order_id] = []
            self.callbacks[exchange_order_id].append(callback)
        
        # Start polling task
        task = asyncio.create_task(self._poll_order_status(exchange_order_id, instrument_id))
        self.polling_tasks[exchange_order_id] = task
        
        logger.info(f"Started tracking order {exchange_order_id}")
    
    async def _poll_order_status(self, exchange_order_id: str, instrument_id: str):
        """
        Poll order status from exchange
        
        Args:
            exchange_order_id: Exchange order ID
            instrument_id: Instrument ID
        """
        try:
            max_attempts = 60  # Poll for up to 5 minutes
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    # Query order status from exchange
                    order_data = await self.okx_client.trade.get_order(
                        inst_id=instrument_id,
                        ord_id=exchange_order_id
                    )
                    
                    if order_data and len(order_data) > 0:
                        await self.on_order_update(order_data[0])
                        
                        # Check if order is in terminal state
                        state = order_data[0].get('state', '')
                        if state in ['filled', 'canceled', 'mmp_canceled']:
                            break
                    
                    await asyncio.sleep(5)  # Poll every 5 seconds
                    attempt += 1
                
                except Exception as e:
                    logger.error(f"Error polling order {exchange_order_id}: {str(e)}")
                    await asyncio.sleep(5)
                    attempt += 1
        
        finally:
            # Clean up
            if exchange_order_id in self.polling_tasks:
                del self.polling_tasks[exchange_order_id]
    
    async def on_order_update(self, order_data: Dict[str, Any]):
        """
        Handle order update event
        
        Args:
            order_data: Order data from exchange
        """
        try:
            exchange_order_id = order_data.get('ordId')
            if not exchange_order_id or exchange_order_id not in self.tracked_orders:
                return
            
            tracked_info = self.tracked_orders[exchange_order_id]
            order_id = tracked_info['order_id']
            
            # Map exchange status to our status
            exchange_status = order_data.get('state', '')
            status_mapping = {
                'live': OrderStatus.LIVE,
                'partially_filled': OrderStatus.PARTIALLY_FILLED,
                'filled': OrderStatus.FILLED,
                'canceled': OrderStatus.CANCELLED,
                'mmp_canceled': OrderStatus.CANCELLED,
            }
            
            new_status = status_mapping.get(exchange_status)
            if not new_status:
                logger.warning(f"Unknown exchange status: {exchange_status}")
                return
            
            # Extract order details
            filled_size = Decimal(order_data.get('accFillSz', '0'))
            avg_price = Decimal(order_data.get('avgPx', '0')) if order_data.get('avgPx') else None
            
            # Update order in database
            order = self.order_manager.update_order_status(
                order_id=order_id,
                status=new_status,
                filled_size=filled_size,
                average_price=avg_price,
                exchange_order_id=exchange_order_id
            )
            
            logger.info(f"Order {exchange_order_id} updated: {new_status}, filled: {filled_size}")
            
            # Execute callbacks
            if exchange_order_id in self.callbacks:
                for callback in self.callbacks[exchange_order_id]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(order, order_data)
                        else:
                            callback(order, order_data)
                    except Exception as e:
                        logger.error(f"Error executing callback: {str(e)}")
            
            # Clean up if order is in terminal state
            if new_status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                self.stop_tracking(exchange_order_id)
        
        except Exception as e:
            logger.error(f"Error handling order update: {str(e)}")
    
    def stop_tracking(self, exchange_order_id: str):
        """
        Stop tracking an order
        
        Args:
            exchange_order_id: Exchange order ID
        """
        if exchange_order_id in self.tracked_orders:
            del self.tracked_orders[exchange_order_id]
        
        if exchange_order_id in self.callbacks:
            del self.callbacks[exchange_order_id]
        
        if exchange_order_id in self.polling_tasks:
            task = self.polling_tasks[exchange_order_id]
            if not task.done():
                task.cancel()
            del self.polling_tasks[exchange_order_id]
        
        logger.info(f"Stopped tracking order {exchange_order_id}")
    
    def stop_all_tracking(self):
        """Stop tracking all orders"""
        order_ids = list(self.tracked_orders.keys())
        for exchange_order_id in order_ids:
            self.stop_tracking(exchange_order_id)
    
    def is_tracking(self, exchange_order_id: str) -> bool:
        """Check if an order is being tracked"""
        return exchange_order_id in self.tracked_orders
