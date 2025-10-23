import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.trading import Order, OrderStatus, OrderSide
from app.services.trading.schemas import OrderParams, OrderResponse


class OrderManager:
    """Manages order lifecycle and database operations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.active_orders: Dict[int, Order] = {}
    
    def create_order(self, order_params: OrderParams) -> Order:
        """
        Create a new order record in database
        
        Args:
            order_params: Order parameters
            
        Returns:
            Created Order object
        """
        order = Order(
            client_order_id=order_params.client_order_id,
            instrument_id=order_params.instrument_id,
            side=order_params.side,
            order_type=order_params.order_type,
            price=order_params.price,
            size=order_params.size,
            filled_size=Decimal("0"),
            status=OrderStatus.PENDING,
            trade_mode=order_params.trade_mode,
            position_side=order_params.position_side,
            reduce_only=order_params.reduce_only,
            strategy_id=order_params.strategy_id,
            signal_id=order_params.signal_id,
            metadata=json.dumps(order_params.metadata) if order_params.metadata else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.db_session.add(order)
        self.db_session.commit()
        self.db_session.refresh(order)
        
        # Cache active order
        self.active_orders[order.id] = order
        
        return order
    
    def update_order_status(
        self,
        order_id: int,
        status: OrderStatus,
        filled_size: Optional[Decimal] = None,
        average_price: Optional[Decimal] = None,
        exchange_order_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Order:
        """
        Update order status and related fields
        
        Args:
            order_id: Order ID
            status: New order status
            filled_size: Filled size (if applicable)
            average_price: Average fill price (if applicable)
            exchange_order_id: Exchange order ID
            error_code: Error code (if failed)
            error_message: Error message (if failed)
            
        Returns:
            Updated Order object
        """
        order = self.db_session.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        order.status = status
        order.updated_at = datetime.utcnow()
        
        if filled_size is not None:
            order.filled_size = filled_size
        
        if average_price is not None:
            order.average_price = average_price
        
        if exchange_order_id is not None:
            order.exchange_order_id = exchange_order_id
        
        if error_code is not None:
            order.error_code = error_code
        
        if error_message is not None:
            order.error_message = error_message
        
        if status == OrderStatus.FILLED:
            order.filled_at = datetime.utcnow()
        elif status == OrderStatus.CANCELLED:
            order.cancelled_at = datetime.utcnow()
        
        self.db_session.commit()
        self.db_session.refresh(order)
        
        # Update cache
        if order.id in self.active_orders:
            if status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                # Remove from active orders
                del self.active_orders[order.id]
            else:
                self.active_orders[order.id] = order
        
        return order
    
    def get_order(self, order_id: int) -> Optional[Order]:
        """
        Get order by ID
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object or None
        """
        return self.db_session.query(Order).filter(Order.id == order_id).first()
    
    def get_order_by_exchange_id(self, exchange_order_id: str) -> Optional[Order]:
        """
        Get order by exchange order ID
        
        Args:
            exchange_order_id: Exchange order ID
            
        Returns:
            Order object or None
        """
        return self.db_session.query(Order).filter(
            Order.exchange_order_id == exchange_order_id
        ).first()
    
    def get_order_by_client_id(self, client_order_id: str) -> Optional[Order]:
        """
        Get order by client order ID
        
        Args:
            client_order_id: Client order ID
            
        Returns:
            Order object or None
        """
        return self.db_session.query(Order).filter(
            Order.client_order_id == client_order_id
        ).first()
    
    def get_active_orders(self, instrument_id: Optional[str] = None) -> List[Order]:
        """
        Get all active orders (pending, live, partially filled)
        
        Args:
            instrument_id: Filter by instrument ID (optional)
            
        Returns:
            List of active orders
        """
        query = self.db_session.query(Order).filter(
            Order.status.in_([
                OrderStatus.PENDING,
                OrderStatus.LIVE,
                OrderStatus.PARTIALLY_FILLED
            ])
        )
        
        if instrument_id:
            query = query.filter(Order.instrument_id == instrument_id)
        
        return query.order_by(Order.created_at.desc()).all()
    
    def get_order_history(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Order]:
        """
        Get historical orders with filters
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of orders
        """
        query = self.db_session.query(Order)
        
        if filters:
            if 'instrument_id' in filters:
                query = query.filter(Order.instrument_id == filters['instrument_id'])
            
            if 'status' in filters:
                if isinstance(filters['status'], list):
                    query = query.filter(Order.status.in_(filters['status']))
                else:
                    query = query.filter(Order.status == filters['status'])
            
            if 'side' in filters:
                query = query.filter(Order.side == filters['side'])
            
            if 'strategy_id' in filters:
                query = query.filter(Order.strategy_id == filters['strategy_id'])
            
            if 'start_date' in filters:
                query = query.filter(Order.created_at >= filters['start_date'])
            
            if 'end_date' in filters:
                query = query.filter(Order.created_at <= filters['end_date'])
        
        return query.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()
    
    async def sync_orders_with_exchange(self, okx_trade_client):
        """
        Synchronize order status with exchange
        
        Args:
            okx_trade_client: OKX trade client instance
        """
        active_orders = self.get_active_orders()
        
        for order in active_orders:
            try:
                if order.exchange_order_id:
                    # Query order status from exchange
                    exchange_order = await okx_trade_client.get_order(
                        inst_id=order.instrument_id,
                        ord_id=order.exchange_order_id
                    )
                    
                    if exchange_order and len(exchange_order) > 0:
                        order_data = exchange_order[0]
                        
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
                        if new_status and new_status != order.status:
                            filled_size = Decimal(order_data.get('accFillSz', '0'))
                            avg_price = Decimal(order_data.get('avgPx', '0')) if order_data.get('avgPx') else None
                            
                            self.update_order_status(
                                order_id=order.id,
                                status=new_status,
                                filled_size=filled_size,
                                average_price=avg_price
                            )
            
            except Exception as e:
                # Log error but continue processing other orders
                print(f"Error syncing order {order.id}: {str(e)}")
                continue
    
    def to_response(self, order: Order) -> OrderResponse:
        """
        Convert Order model to OrderResponse DTO
        
        Args:
            order: Order model
            
        Returns:
            OrderResponse DTO
        """
        metadata = None
        if order.metadata:
            try:
                metadata = json.loads(order.metadata)
            except:
                pass
        
        return OrderResponse(
            id=order.id,
            client_order_id=order.client_order_id,
            exchange_order_id=order.exchange_order_id,
            instrument_id=order.instrument_id,
            side=order.side,
            order_type=order.order_type,
            price=order.price,
            size=order.size,
            filled_size=order.filled_size,
            average_price=order.average_price,
            status=order.status,
            trade_mode=order.trade_mode,
            position_side=order.position_side,
            reduce_only=order.reduce_only,
            strategy_id=order.strategy_id,
            signal_id=order.signal_id,
            metadata=metadata,
            created_at=order.created_at,
            updated_at=order.updated_at,
            filled_at=order.filled_at,
            cancelled_at=order.cancelled_at,
            error_code=order.error_code,
            error_message=order.error_message,
        )
