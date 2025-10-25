import logging
import uuid
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.strategies.signals import Signal, SignalType
from app.strategies.models import Account, OrderSide as StrategyOrderSide
from app.models.trading import Order, OrderStatus, OrderSide, OrderType
from app.services.trading.schemas import OrderParams, RiskCheckResult
from app.services.trading.order_manager import OrderManager
from app.services.trading.execution_risk import ExecutionRiskControl
from app.services.trading.order_tracker import OrderTracker

logger = logging.getLogger(__name__)


class TradeExecutor:
    """Executes trading signals and manages order lifecycle"""
    
    def __init__(
        self,
        okx_client,
        order_manager: OrderManager,
        risk_manager: ExecutionRiskControl,
        order_tracker: Optional[OrderTracker] = None
    ):
        self.okx_client = okx_client
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.order_tracker = order_tracker
        self.pending_orders = {}
    
    async def execute_signal(
        self,
        signal: Signal,
        account: Account,
        strategy_id: Optional[str] = None
    ) -> Order:
        """
        Execute a trading signal
        
        Args:
            signal: Trading signal
            account: Account state
            strategy_id: Strategy identifier
            
        Returns:
            Created Order object
            
        Raises:
            ValueError: If signal fails risk checks
        """
        logger.info(f"Executing signal: {signal.type} {signal.size} {signal.instrument_id} @ {signal.price}")
        
        # 1. Risk check
        risk_result = self.risk_manager.pre_trade_check(signal, account)
        if not risk_result.passed:
            logger.warning(f"Signal failed risk check: {risk_result.reason}")
            raise ValueError(f"Risk check failed: {risk_result.reason}")
        
        # Apply risk adjustments
        adjusted_size = risk_result.adjusted_size or signal.size
        if risk_result.warnings:
            for warning in risk_result.warnings:
                logger.warning(warning)
        
        # 2. Calculate order parameters
        order_params = self._signal_to_order_params(
            signal,
            adjusted_size,
            strategy_id
        )
        
        # 3. Submit order to exchange
        order = await self.place_order(order_params)
        
        return order
    
    def _signal_to_order_params(
        self,
        signal: Signal,
        size: Decimal,
        strategy_id: Optional[str] = None
    ) -> OrderParams:
        """
        Convert trading signal to order parameters
        
        Args:
            signal: Trading signal
            size: Adjusted order size
            strategy_id: Strategy identifier
            
        Returns:
            OrderParams object
        """
        # Map signal type to order side
        if signal.type == SignalType.BUY:
            side = OrderSide.BUY
        elif signal.type == SignalType.SELL:
            side = OrderSide.SELL
        elif signal.type == SignalType.CLOSE:
            # Determine side based on current position
            # For now, default to SELL
            side = OrderSide.SELL
        else:
            raise ValueError(f"Cannot execute signal type: {signal.type}")
        
        # Determine order type (for now, use market orders for simplicity)
        order_type = OrderType.MARKET
        price = None
        
        # Generate client order ID
        client_order_id = f"sig_{uuid.uuid4().hex[:16]}"
        
        return OrderParams(
            instrument_id=signal.instrument_id,
            side=side,
            order_type=order_type,
            size=size,
            price=price,
            trade_mode="cash",
            client_order_id=client_order_id,
            strategy_id=strategy_id,
            signal_id=str(signal.timestamp.timestamp()),
            metadata=signal.metadata
        )
    
    async def place_order(self, order_params: OrderParams) -> Order:
        """
        Place an order on the exchange
        
        Args:
            order_params: Order parameters
            
        Returns:
            Created Order object
            
        Raises:
            Exception: If order placement fails
        """
        logger.info(f"Placing order: {order_params.side} {order_params.size} {order_params.instrument_id}")
        
        # Validate order parameters
        risk_result = self.risk_manager.validate_order_params(order_params)
        if not risk_result.passed:
            logger.error(f"Order validation failed: {risk_result.reason}")
            raise ValueError(f"Order validation failed: {risk_result.reason}")
        
        # 1. Create order record in database
        order = self.order_manager.create_order(order_params)
        
        try:
            # 2. Submit order to exchange
            okx_params = {
                'inst_id': order_params.instrument_id,
                'td_mode': order_params.trade_mode,
                'side': order_params.side.value,
                'ord_type': order_params.order_type.value,
                'sz': str(order_params.size),
            }
            
            if order_params.price:
                okx_params['px'] = str(order_params.price)
            
            if order_params.client_order_id:
                okx_params['cl_ord_id'] = order_params.client_order_id
            
            if order_params.position_side:
                okx_params['pos_side'] = order_params.position_side.value
            
            if order_params.reduce_only:
                okx_params['reduce_only'] = True
            
            logger.debug(f"Submitting order to OKX: {okx_params}")
            
            result = await self.okx_client.trade.place_order(**okx_params)
            
            if result and len(result) > 0:
                order_result = result[0]
                exchange_order_id = order_result.get('ordId')
                s_code = order_result.get('sCode', '0')
                s_msg = order_result.get('sMsg', '')
                
                if s_code == '0' and exchange_order_id:
                    # Order successfully placed
                    logger.info(f"Order placed successfully: {exchange_order_id}")
                    
                    # Update order with exchange ID
                    order = self.order_manager.update_order_status(
                        order_id=order.id,
                        status=OrderStatus.LIVE,
                        exchange_order_id=exchange_order_id
                    )
                    
                    # Start tracking order
                    if self.order_tracker:
                        await self.order_tracker.start_tracking(
                            order_id=order.id,
                            exchange_order_id=exchange_order_id,
                            instrument_id=order_params.instrument_id
                        )
                    
                    self.pending_orders[order.id] = order
                else:
                    # Order failed
                    logger.error(f"Order failed: {s_code} - {s_msg}")
                    order = self.order_manager.update_order_status(
                        order_id=order.id,
                        status=OrderStatus.REJECTED,
                        error_code=s_code,
                        error_message=s_msg
                    )
                    raise Exception(f"Order rejected: {s_code} - {s_msg}")
            else:
                raise Exception("No response from exchange")
        
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            # Update order status to rejected
            order = self.order_manager.update_order_status(
                order_id=order.id,
                status=OrderStatus.REJECTED,
                error_message=str(e)
            )
            raise
        
        return order
    
    async def cancel_order(self, order_id: int) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Order ID
            
        Returns:
            True if cancellation successful
        """
        order = self.order_manager.get_order(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return False
        
        if order.status not in [OrderStatus.PENDING, OrderStatus.LIVE, OrderStatus.PARTIALLY_FILLED]:
            logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
            return False
        
        if not order.exchange_order_id:
            logger.error(f"Order {order_id} has no exchange order ID")
            # Just mark as cancelled locally
            self.order_manager.update_order_status(
                order_id=order_id,
                status=OrderStatus.CANCELLED
            )
            return True
        
        try:
            logger.info(f"Cancelling order {order_id} (exchange: {order.exchange_order_id})")
            
            result = await self.okx_client.trade.cancel_order(
                inst_id=order.instrument_id,
                ord_id=order.exchange_order_id
            )
            
            if result and len(result) > 0:
                cancel_result = result[0]
                s_code = cancel_result.get('sCode', '0')
                s_msg = cancel_result.get('sMsg', '')
                
                if s_code == '0':
                    logger.info(f"Order {order_id} cancelled successfully")
                    
                    # Update order status
                    self.order_manager.update_order_status(
                        order_id=order_id,
                        status=OrderStatus.CANCELLED
                    )
                    
                    # Stop tracking
                    if self.order_tracker and order.exchange_order_id:
                        self.order_tracker.stop_tracking(order.exchange_order_id)
                    
                    if order_id in self.pending_orders:
                        del self.pending_orders[order_id]
                    
                    return True
                else:
                    logger.error(f"Failed to cancel order: {s_code} - {s_msg}")
                    return False
            
            return False
        
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    async def modify_order(self, order_id: int, new_params: dict) -> Optional[Order]:
        """
        Modify an existing order
        
        Args:
            order_id: Order ID
            new_params: New order parameters (size, price)
            
        Returns:
            Updated Order object or None
        """
        order = self.order_manager.get_order(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return None
        
        if order.status not in [OrderStatus.LIVE, OrderStatus.PARTIALLY_FILLED]:
            logger.warning(f"Cannot modify order {order_id} with status {order.status}")
            return None
        
        if not order.exchange_order_id:
            logger.error(f"Order {order_id} has no exchange order ID")
            return None
        
        try:
            logger.info(f"Modifying order {order_id}")
            
            amend_params = {
                'inst_id': order.instrument_id,
                'ord_id': order.exchange_order_id,
            }
            
            if 'size' in new_params:
                amend_params['new_sz'] = str(new_params['size'])
            
            if 'price' in new_params:
                amend_params['new_px'] = str(new_params['price'])
            
            result = await self.okx_client.trade.amend_order(**amend_params)
            
            if result and len(result) > 0:
                amend_result = result[0]
                s_code = amend_result.get('sCode', '0')
                s_msg = amend_result.get('sMsg', '')
                
                if s_code == '0':
                    logger.info(f"Order {order_id} modified successfully")
                    
                    # Refresh order status
                    # Note: The actual update will come through order tracker
                    return order
                else:
                    logger.error(f"Failed to modify order: {s_code} - {s_msg}")
                    return None
            
            return None
        
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}")
            return None
