from decimal import Decimal
from typing import Dict, Any, Optional

from app.strategies.signals import Signal, SignalType
from app.strategies.models import Account, Position, OrderSide


class RiskManager:
    """
    Risk management module for validating and adjusting trading signals.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize risk manager with configuration.
        
        Args:
            config: Dictionary containing risk management parameters
        """
        self.max_position_size = Decimal(str(config.get("max_position_size", 1.0)))
        self.max_loss_per_trade = Decimal(str(config.get("max_loss_per_trade", 0.02)))
        self.max_daily_loss = Decimal(str(config.get("max_daily_loss", 0.05)))
        self.stop_loss_pct = Decimal(str(config.get("stop_loss_pct", 0.05)))
        self.take_profit_pct = Decimal(str(config.get("take_profit_pct", 0.10)))
        self.max_leverage = Decimal(str(config.get("max_leverage", 1.0)))
        self.max_positions = config.get("max_positions", 5)
    
    def validate_signal(self, signal: Signal, account: Account) -> bool:
        """
        Validate if a signal meets risk management criteria.
        
        Args:
            signal: Trading signal to validate
            account: Current account state
            
        Returns:
            True if signal passes risk checks, False otherwise
        """
        # Check if daily loss limit is reached
        if account.daily_pnl < -abs(self.max_daily_loss * account.equity):
            return False
        
        # Check if position size exceeds maximum
        if signal.size > self.max_position_size:
            return False
        
        # Check if account has sufficient balance
        required_capital = signal.price * signal.size
        if required_capital > account.available_balance:
            return False
        
        # Check if maximum number of positions is reached
        if len(account.positions) >= self.max_positions and signal.type in [SignalType.BUY, SignalType.SELL]:
            # Allow only if closing an existing position
            has_opposite_position = any(
                pos.instrument_id == signal.instrument_id and
                ((pos.side == OrderSide.BUY and signal.type == SignalType.SELL) or
                 (pos.side == OrderSide.SELL and signal.type == SignalType.BUY))
                for pos in account.positions
            )
            if not has_opposite_position:
                return False
        
        # Check leverage
        total_exposure = sum(pos.size * pos.current_price for pos in account.positions)
        new_exposure = total_exposure + (signal.price * signal.size)
        leverage = new_exposure / account.equity if account.equity > 0 else Decimal("0")
        if leverage > self.max_leverage:
            return False
        
        return True
    
    def calculate_stop_loss(self, entry_price: Decimal, side: OrderSide) -> Decimal:
        """
        Calculate stop loss price based on entry price and side.
        
        Args:
            entry_price: Entry price of the position
            side: Order side (BUY or SELL)
            
        Returns:
            Stop loss price
        """
        if side == OrderSide.BUY:
            return entry_price * (Decimal("1") - self.stop_loss_pct)
        else:  # SELL
            return entry_price * (Decimal("1") + self.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price: Decimal, side: OrderSide) -> Decimal:
        """
        Calculate take profit price based on entry price and side.
        
        Args:
            entry_price: Entry price of the position
            side: Order side (BUY or SELL)
            
        Returns:
            Take profit price
        """
        if side == OrderSide.BUY:
            return entry_price * (Decimal("1") + self.take_profit_pct)
        else:  # SELL
            return entry_price * (Decimal("1") - self.take_profit_pct)
    
    def calculate_position_size(self, signal: Signal, account: Account) -> Decimal:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            signal: Trading signal
            account: Current account state
            
        Returns:
            Adjusted position size
        """
        # Calculate maximum position size based on risk per trade
        max_risk_amount = account.equity * self.max_loss_per_trade
        
        # Calculate position size based on stop loss
        price_risk = signal.price * self.stop_loss_pct
        if price_risk > 0:
            risk_based_size = max_risk_amount / price_risk
        else:
            risk_based_size = Decimal("0")
        
        # Take minimum of risk-based size, configured max size, and signal size
        position_size = min(risk_based_size, self.max_position_size, signal.size)
        
        # Ensure we don't exceed available balance
        max_affordable_size = account.available_balance / signal.price
        position_size = min(position_size, max_affordable_size)
        
        return max(position_size, Decimal("0"))
    
    def adjust_signal(self, signal: Signal, account: Account) -> Optional[Signal]:
        """
        Adjust signal parameters to meet risk management criteria.
        
        Args:
            signal: Original trading signal
            account: Current account state
            
        Returns:
            Adjusted signal or None if signal should be rejected
        """
        if not self.validate_signal(signal, account):
            # Try to adjust position size
            adjusted_size = self.calculate_position_size(signal, account)
            if adjusted_size > 0:
                signal.size = adjusted_size
                if self.validate_signal(signal, account):
                    return signal
            return None
        
        return signal
