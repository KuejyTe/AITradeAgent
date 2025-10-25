import json
from typing import List, Optional, Dict
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.trading import Trade, Position, OrderSide
from app.services.trading.schemas import TradeResponse, PerformanceMetrics


class TradeRecorder:
    """Records and analyzes trade executions"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def record_trade(
        self,
        order_id: int,
        trade_id: str,
        instrument_id: str,
        side: OrderSide,
        price: Decimal,
        size: Decimal,
        fee: Decimal = Decimal("0"),
        fee_currency: Optional[str] = None,
        executed_at: Optional[datetime] = None,
        **kwargs
    ) -> Trade:
        """
        Record a trade execution
        
        Args:
            order_id: Internal order ID
            trade_id: Exchange trade ID
            instrument_id: Instrument ID
            side: Order side
            price: Execution price
            size: Execution size
            fee: Trade fee
            fee_currency: Fee currency
            executed_at: Execution timestamp
            **kwargs: Additional trade data
            
        Returns:
            Created Trade object
        """
        trade = Trade(
            trade_id=trade_id,
            order_id=order_id,
            exchange_order_id=kwargs.get('exchange_order_id'),
            instrument_id=instrument_id,
            side=side,
            price=price,
            size=size,
            fee=fee,
            fee_currency=fee_currency,
            liquidity=kwargs.get('liquidity'),
            trade_mode=kwargs.get('trade_mode'),
            position_side=kwargs.get('position_side'),
            strategy_id=kwargs.get('strategy_id'),
            metadata=kwargs.get('metadata') if kwargs.get('metadata') else None,
            executed_at=executed_at or datetime.now(timezone.utc),
        )
        
        self.db_session.add(trade)
        self.db_session.commit()
        self.db_session.refresh(trade)
        
        return trade
    
    def get_trades(
        self,
        instrument_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Trade]:
        """
        Get trades with filters
        
        Args:
            instrument_id: Filter by instrument
            start_date: Start date filter
            end_date: End date filter
            strategy_id: Filter by strategy
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of Trade objects
        """
        query = self.db_session.query(Trade)
        
        if instrument_id:
            query = query.filter(Trade.instrument_id == instrument_id)
        
        if start_date:
            query = query.filter(Trade.executed_at >= start_date)
        
        if end_date:
            query = query.filter(Trade.executed_at <= end_date)
        
        if strategy_id:
            query = query.filter(Trade.strategy_id == strategy_id)
        
        return query.order_by(Trade.executed_at.desc()).limit(limit).offset(offset).all()
    
    def calculate_performance(
        self,
        start_date: datetime,
        end_date: datetime,
        instrument_id: Optional[str] = None,
        strategy_id: Optional[str] = None
    ) -> PerformanceMetrics:
        """
        Calculate trading performance metrics
        
        Args:
            start_date: Start date
            end_date: End date
            instrument_id: Filter by instrument
            strategy_id: Filter by strategy
            
        Returns:
            PerformanceMetrics object
        """
        # Get closed positions in the date range
        positions_query = self.db_session.query(Position).filter(
            and_(
                Position.closed_at.isnot(None),
                Position.closed_at >= start_date,
                Position.closed_at <= end_date
            )
        )
        
        if instrument_id:
            positions_query = positions_query.filter(Position.instrument_id == instrument_id)
        
        if strategy_id:
            positions_query = positions_query.filter(Position.strategy_id == strategy_id)
        
        positions = positions_query.all()
        
        # Calculate metrics
        total_trades = len(positions)
        winning_trades = sum(1 for p in positions if p.realized_pnl > 0)
        losing_trades = sum(1 for p in positions if p.realized_pnl < 0)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        total_pnl = sum(p.realized_pnl for p in positions)
        
        winning_pnls = [p.realized_pnl for p in positions if p.realized_pnl > 0]
        losing_pnls = [p.realized_pnl for p in positions if p.realized_pnl < 0]
        
        average_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else Decimal("0")
        average_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else Decimal("0")
        
        # Profit factor
        gross_profit = sum(winning_pnls) if winning_pnls else Decimal("0")
        gross_loss = abs(sum(losing_pnls)) if losing_pnls else Decimal("0")
        profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else 0.0
        
        # Calculate max drawdown
        max_drawdown, max_drawdown_pct = self._calculate_max_drawdown(positions)
        
        # Calculate return percentage (simplified - assumes initial capital)
        # In a real system, you'd track capital over time
        initial_capital = Decimal("10000")  # Placeholder
        total_return_pct = float(total_pnl / initial_capital * 100) if initial_capital > 0 else 0.0
        
        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio(positions)
        
        # Calculate Sortino ratio
        sortino_ratio = self._calculate_sortino_ratio(positions)
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_return_pct=total_return_pct,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            start_date=start_date,
            end_date=end_date
        )
    
    def _calculate_max_drawdown(self, positions: List[Position]) -> tuple[Decimal, float]:
        """Calculate maximum drawdown"""
        if not positions:
            return Decimal("0"), 0.0
        
        # Sort by close date
        sorted_positions = sorted(positions, key=lambda p: p.closed_at)
        
        # Calculate cumulative PnL
        cumulative_pnl = Decimal("0")
        peak_pnl = Decimal("0")
        max_drawdown = Decimal("0")
        
        for position in sorted_positions:
            cumulative_pnl += position.realized_pnl
            peak_pnl = max(peak_pnl, cumulative_pnl)
            drawdown = peak_pnl - cumulative_pnl
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate percentage
        max_drawdown_pct = float(max_drawdown / peak_pnl * 100) if peak_pnl > 0 else 0.0
        
        return max_drawdown, max_drawdown_pct
    
    def _calculate_sharpe_ratio(self, positions: List[Position]) -> Optional[float]:
        """Calculate Sharpe ratio"""
        if not positions or len(positions) < 2:
            return None
        
        returns = [float(p.realized_pnl) for p in positions]
        
        # Calculate mean and std
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return None
        
        # Assuming risk-free rate of 0 for simplicity
        sharpe_ratio = mean_return / std_dev
        
        # Annualize (assuming daily returns)
        sharpe_ratio_annual = sharpe_ratio * (252 ** 0.5)
        
        return sharpe_ratio_annual
    
    def _calculate_sortino_ratio(self, positions: List[Position]) -> Optional[float]:
        """Calculate Sortino ratio (penalizes only downside volatility)"""
        if not positions or len(positions) < 2:
            return None
        
        returns = [float(p.realized_pnl) for p in positions]
        
        # Calculate mean
        mean_return = sum(returns) / len(returns)
        
        # Calculate downside deviation
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return None
        
        downside_variance = sum(r ** 2 for r in negative_returns) / len(negative_returns)
        downside_deviation = downside_variance ** 0.5
        
        if downside_deviation == 0:
            return None
        
        # Assuming risk-free rate of 0
        sortino_ratio = mean_return / downside_deviation
        
        # Annualize
        sortino_ratio_annual = sortino_ratio * (252 ** 0.5)
        
        return sortino_ratio_annual
    
    def get_trade_statistics(
        self,
        instrument_id: Optional[str] = None,
        strategy_id: Optional[str] = None
    ) -> dict:
        """
        Get trade statistics
        
        Args:
            instrument_id: Filter by instrument
            strategy_id: Filter by strategy
            
        Returns:
            Dictionary of statistics
        """
        query = self.db_session.query(Trade)
        
        if instrument_id:
            query = query.filter(Trade.instrument_id == instrument_id)
        
        if strategy_id:
            query = query.filter(Trade.strategy_id == strategy_id)
        
        total_trades = query.count()
        
        if total_trades == 0:
            return {
                'total_trades': 0,
                'total_volume': 0,
                'total_fees': 0,
                'avg_trade_size': 0,
                'instruments': []
            }
        
        # Aggregate statistics
        total_volume = query.with_entities(
            func.sum(Trade.price * Trade.size)
        ).scalar() or Decimal("0")
        
        total_fees = query.with_entities(
            func.sum(Trade.fee)
        ).scalar() or Decimal("0")
        
        avg_trade_size = query.with_entities(
            func.avg(Trade.size)
        ).scalar() or Decimal("0")
        
        # Get unique instruments
        instruments = query.with_entities(Trade.instrument_id).distinct().all()
        instruments = [i[0] for i in instruments]
        
        return {
            'total_trades': total_trades,
            'total_volume': float(total_volume),
            'total_fees': float(total_fees),
            'avg_trade_size': float(avg_trade_size),
            'instruments': instruments
        }
    
    def to_response(self, trade: Trade) -> TradeResponse:
        """
        Convert Trade model to TradeResponse DTO
        
        Args:
            trade: Trade model
            
        Returns:
            TradeResponse DTO
        """
        metadata = None
        if trade.metadata:
            if isinstance(trade.metadata, dict):
                metadata = trade.metadata
            elif isinstance(trade.metadata, str):
                try:
                    metadata = json.loads(trade.metadata)
                except Exception:
                    metadata = trade.metadata
            else:
                metadata = trade.metadata
        
        return TradeResponse(
            id=trade.id,
            trade_id=trade.trade_id,
            order_id=trade.order_id,
            exchange_order_id=trade.exchange_order_id,
            instrument_id=trade.instrument_id,
            side=trade.side,
            price=trade.price,
            size=trade.size,
            fee=trade.fee,
            fee_currency=trade.fee_currency,
            liquidity=trade.liquidity,
            trade_mode=trade.trade_mode,
            position_side=trade.position_side,
            strategy_id=trade.strategy_id,
            metadata=metadata,
            executed_at=trade.executed_at,
            created_at=trade.created_at
        )
