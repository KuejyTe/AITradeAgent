import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.trading import Position, Trade, PositionSide, OrderSide
from app.services.trading.schemas import PositionResponse


class PositionManager:
    """Manages positions and PnL calculations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.positions: Dict[str, Position] = {}
    
    def get_position(self, instrument_id: str) -> Optional[Position]:
        """
        Get current position for an instrument
        
        Args:
            instrument_id: Instrument ID
            
        Returns:
            Position object or None
        """
        # Check cache first
        if instrument_id in self.positions:
            return self.positions[instrument_id]
        
        # Query from database
        position = self.db_session.query(Position).filter(
            Position.instrument_id == instrument_id,
            Position.closed_at.is_(None)
        ).first()
        
        if position:
            self.positions[instrument_id] = position
        
        return position
    
    def update_position(self, trade: Trade) -> Position:
        """
        Update position based on a trade execution
        
        Args:
            trade: Trade object
            
        Returns:
            Updated or created Position object
        """
        position = self.get_position(trade.instrument_id)
        
        if not position:
            # Create new position
            position = self._create_position(trade)
        else:
            # Update existing position
            position = self._update_existing_position(position, trade)
        
        return position
    
    def _create_position(self, trade: Trade) -> Position:
        """Create new position from trade"""
        position_side = PositionSide.LONG if trade.side == OrderSide.BUY else PositionSide.SHORT
        
        position = Position(
            instrument_id=trade.instrument_id,
            side=position_side,
            size=trade.size,
            entry_price=trade.price,
            current_price=trade.price,
            average_price=trade.price,
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            margin_mode=trade.trade_mode,
            trade_mode=trade.trade_mode,
            strategy_id=trade.strategy_id,
            metadata=trade.metadata,
            opened_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        self.db_session.add(position)
        self.db_session.commit()
        self.db_session.refresh(position)
        
        self.positions[trade.instrument_id] = position
        return position
    
    def _update_existing_position(self, position: Position, trade: Trade) -> Position:
        """Update existing position with new trade"""
        # Determine if this is adding to or reducing position
        is_same_side = (
            (position.side == PositionSide.LONG and trade.side == OrderSide.BUY) or
            (position.side == PositionSide.SHORT and trade.side == OrderSide.SELL)
        )
        
        if is_same_side:
            # Adding to position
            total_cost = position.average_price * position.size + trade.price * trade.size
            new_size = position.size + trade.size
            position.average_price = total_cost / new_size if new_size > 0 else Decimal("0")
            position.size = new_size
        else:
            # Reducing position
            if trade.size >= position.size:
                # Closing or reversing position
                realized_pnl = self._calculate_realized_pnl(
                    position.side,
                    position.average_price,
                    trade.price,
                    position.size
                )
                position.realized_pnl += realized_pnl
                
                if trade.size > position.size:
                    # Reversing position
                    remaining_size = trade.size - position.size
                    position.side = PositionSide.LONG if trade.side == OrderSide.BUY else PositionSide.SHORT
                    position.size = remaining_size
                    position.average_price = trade.price
                    position.entry_price = trade.price
                else:
                    # Closing position
                    position.size = Decimal("0")
                    position.closed_at = datetime.now(timezone.utc)
                    # Remove from cache
                    if position.instrument_id in self.positions:
                        del self.positions[position.instrument_id]
            else:
                # Partially closing position
                realized_pnl = self._calculate_realized_pnl(
                    position.side,
                    position.average_price,
                    trade.price,
                    trade.size
                )
                position.realized_pnl += realized_pnl
                position.size -= trade.size
        
        position.current_price = trade.price
        position.updated_at = datetime.now(timezone.utc)
        
        self.db_session.commit()
        self.db_session.refresh(position)
        
        return position
    
    def _calculate_realized_pnl(
        self,
        position_side: PositionSide,
        entry_price: Decimal,
        exit_price: Decimal,
        size: Decimal
    ) -> Decimal:
        """Calculate realized PnL for a closed position"""
        if position_side == PositionSide.LONG:
            return (exit_price - entry_price) * size
        else:  # SHORT
            return (entry_price - exit_price) * size
    
    def calculate_pnl(self, position: Position, current_price: Decimal) -> Decimal:
        """
        Calculate unrealized PnL for a position
        
        Args:
            position: Position object
            current_price: Current market price
            
        Returns:
            Unrealized PnL
        """
        if position.side == PositionSide.LONG:
            unrealized_pnl = (current_price - position.average_price) * position.size
        else:  # SHORT
            unrealized_pnl = (position.average_price - current_price) * position.size
        
        return unrealized_pnl
    
    def update_position_price(self, instrument_id: str, current_price: Decimal) -> Optional[Position]:
        """
        Update position's current price and unrealized PnL
        
        Args:
            instrument_id: Instrument ID
            current_price: Current market price
            
        Returns:
            Updated Position or None
        """
        position = self.get_position(instrument_id)
        if not position:
            return None
        
        position.current_price = current_price
        position.unrealized_pnl = self.calculate_pnl(position, current_price)
        position.updated_at = datetime.now(timezone.utc)
        
        self.db_session.commit()
        self.db_session.refresh(position)
        
        return position
    
    def get_all_positions(self, include_closed: bool = False) -> List[Position]:
        """
        Get all positions
        
        Args:
            include_closed: Whether to include closed positions
            
        Returns:
            List of positions
        """
        query = self.db_session.query(Position)
        
        if not include_closed:
            query = query.filter(Position.closed_at.is_(None))
        
        return query.order_by(Position.opened_at.desc()).all()
    
    async def sync_positions_with_exchange(self, okx_account_client):
        """
        Synchronize positions with exchange
        
        Args:
            okx_account_client: OKX account client instance
        """
        try:
            # Get positions from exchange
            exchange_positions = await okx_account_client.get_positions()
            
            # Create a map of exchange positions
            exchange_pos_map = {}
            for pos_data in exchange_positions:
                inst_id = pos_data.get('instId')
                if inst_id:
                    exchange_pos_map[inst_id] = pos_data
            
            # Update our positions
            our_positions = self.get_all_positions()
            
            for position in our_positions:
                if position.instrument_id in exchange_pos_map:
                    pos_data = exchange_pos_map[position.instrument_id]
                    
                    # Update position details
                    exchange_size = Decimal(pos_data.get('pos', '0'))
                    current_price = Decimal(pos_data.get('last', position.current_price))
                    unrealized_pnl = Decimal(pos_data.get('upl', '0'))
                    
                    if abs(exchange_size) > 0:
                        position.size = abs(exchange_size)
                        position.current_price = current_price
                        position.unrealized_pnl = unrealized_pnl
                        position.updated_at = datetime.now(timezone.utc)
                        
                        self.db_session.commit()
                    else:
                        # Position closed on exchange
                        if not position.closed_at:
                            position.closed_at = datetime.now(timezone.utc)
                            position.size = Decimal("0")
                            self.db_session.commit()
                            
                            if position.instrument_id in self.positions:
                                del self.positions[position.instrument_id]
        
        except Exception as e:
            print(f"Error syncing positions with exchange: {str(e)}")
    
    def to_response(self, position: Position) -> PositionResponse:
        """
        Convert Position model to PositionResponse DTO
        
        Args:
            position: Position model
            
        Returns:
            PositionResponse DTO
        """
        metadata = None
        if position.metadata:
            if isinstance(position.metadata, dict):
                metadata = position.metadata
            elif isinstance(position.metadata, str):
                try:
                    metadata = json.loads(position.metadata)
                except Exception:
                    metadata = position.metadata
            else:
                metadata = position.metadata
        
        return PositionResponse(
            id=position.id,
            instrument_id=position.instrument_id,
            side=position.side,
            size=position.size,
            entry_price=position.entry_price,
            current_price=position.current_price,
            average_price=position.average_price,
            unrealized_pnl=position.unrealized_pnl,
            realized_pnl=position.realized_pnl,
            margin=position.margin,
            leverage=position.leverage,
            margin_mode=position.margin_mode,
            strategy_id=position.strategy_id,
            metadata=metadata,
            opened_at=position.opened_at,
            updated_at=position.updated_at,
            closed_at=position.closed_at,
        )
