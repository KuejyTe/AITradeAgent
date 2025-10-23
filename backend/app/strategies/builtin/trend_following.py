from decimal import Decimal
from typing import Dict, Any, Optional, List

from app.strategies.base import BaseStrategy
from app.strategies.signals import Signal, SignalType
from app.strategies.models import MarketData, Account, Candle, Order


class TrendFollowingStrategy(BaseStrategy):
    """
    Trend Following Strategy based on ATR (Average True Range) breakouts.
    
    This strategy identifies trends and enters positions on breakouts,
    using ATR for dynamic stop loss and take profit levels.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Get strategy parameters
        self.atr_period = self.parameters.get("atr_period", 14)
        self.breakout_multiplier = Decimal(str(self.parameters.get("breakout_multiplier", 2.0)))
        self.stop_loss_atr_multiplier = Decimal(str(self.parameters.get("stop_loss_multiplier", 2.0)))
        self.take_profit_atr_multiplier = Decimal(str(self.parameters.get("take_profit_multiplier", 3.0)))
        self.instrument = self.parameters.get("instrument", "BTC-USDT")
        
        # Internal state
        self.position_entry_price = None
        self.position_side = None
        self.stop_loss_price = None
        self.take_profit_price = None
    
    def analyze(self, market_data: MarketData) -> Optional[Signal]:
        """
        Analyze market data using trend following logic.
        
        Args:
            market_data: Market data with historical candles
            
        Returns:
            Signal if trend breakout detected, None otherwise
        """
        # Check if this is the right instrument
        if market_data.instrument_id != self.instrument:
            return None
        
        # Check if we have enough candles
        if len(market_data.candles) < self.atr_period + 1:
            return None
        
        # Calculate ATR
        atr = self._calculate_atr(market_data.candles, self.atr_period)
        if atr is None or atr == 0:
            return None
        
        # Check if we're in a position
        if self.position_entry_price is not None:
            # Check for exit signals
            signal = self._check_exit_conditions(market_data, atr)
            if signal:
                return signal
            return None
        
        # Look for entry signals
        return self._check_entry_conditions(market_data, atr)
    
    def _check_entry_conditions(self, market_data: MarketData, atr: Decimal) -> Optional[Signal]:
        """
        Check for entry conditions based on ATR breakout.
        
        Args:
            market_data: Current market data
            atr: Current ATR value
            
        Returns:
            Entry signal or None
        """
        candles = market_data.candles
        current_price = market_data.current_price
        
        # Get the highest high and lowest low over the lookback period
        lookback = min(20, len(candles))
        recent_candles = candles[-lookback:]
        
        highest_high = max(candle.high for candle in recent_candles)
        lowest_low = min(candle.low for candle in recent_candles)
        
        # Calculate breakout levels
        upper_breakout = highest_high
        lower_breakout = lowest_low
        
        # Check for bullish breakout
        if current_price > upper_breakout:
            confidence = min(0.6 + float((current_price - upper_breakout) / atr) * 0.1, 0.95)
            
            signal = Signal(
                type=SignalType.BUY,
                instrument_id=market_data.instrument_id,
                price=current_price,
                size=Decimal("1.0"),
                confidence=confidence,
                metadata={
                    "atr": str(atr),
                    "breakout_level": str(upper_breakout),
                    "stop_loss": str(current_price - atr * self.stop_loss_atr_multiplier),
                    "take_profit": str(current_price + atr * self.take_profit_atr_multiplier)
                }
            )
            
            # Update state
            self.position_entry_price = current_price
            self.position_side = SignalType.BUY
            self.stop_loss_price = current_price - atr * self.stop_loss_atr_multiplier
            self.take_profit_price = current_price + atr * self.take_profit_atr_multiplier
            
            return signal
        
        # Check for bearish breakout
        elif current_price < lower_breakout:
            confidence = min(0.6 + float((lower_breakout - current_price) / atr) * 0.1, 0.95)
            
            signal = Signal(
                type=SignalType.SELL,
                instrument_id=market_data.instrument_id,
                price=current_price,
                size=Decimal("1.0"),
                confidence=confidence,
                metadata={
                    "atr": str(atr),
                    "breakout_level": str(lower_breakout),
                    "stop_loss": str(current_price + atr * self.stop_loss_atr_multiplier),
                    "take_profit": str(current_price - atr * self.take_profit_atr_multiplier)
                }
            )
            
            # Update state
            self.position_entry_price = current_price
            self.position_side = SignalType.SELL
            self.stop_loss_price = current_price + atr * self.stop_loss_atr_multiplier
            self.take_profit_price = current_price - atr * self.take_profit_atr_multiplier
            
            return signal
        
        return None
    
    def _check_exit_conditions(self, market_data: MarketData, atr: Decimal) -> Optional[Signal]:
        """
        Check for exit conditions based on stop loss or take profit.
        
        Args:
            market_data: Current market data
            atr: Current ATR value
            
        Returns:
            Exit signal or None
        """
        current_price = market_data.current_price
        
        # Check stop loss and take profit
        should_exit = False
        exit_reason = ""
        
        if self.position_side == SignalType.BUY:
            if current_price <= self.stop_loss_price:
                should_exit = True
                exit_reason = "stop_loss"
            elif current_price >= self.take_profit_price:
                should_exit = True
                exit_reason = "take_profit"
        
        elif self.position_side == SignalType.SELL:
            if current_price >= self.stop_loss_price:
                should_exit = True
                exit_reason = "stop_loss"
            elif current_price <= self.take_profit_price:
                should_exit = True
                exit_reason = "take_profit"
        
        if should_exit:
            # Generate close signal
            signal = Signal(
                type=SignalType.CLOSE,
                instrument_id=market_data.instrument_id,
                price=current_price,
                size=Decimal("1.0"),
                confidence=0.9,
                metadata={
                    "exit_reason": exit_reason,
                    "entry_price": str(self.position_entry_price),
                    "pnl": str(current_price - self.position_entry_price) if self.position_side == SignalType.BUY else str(self.position_entry_price - current_price)
                }
            )
            
            # Reset position state
            self.position_entry_price = None
            self.position_side = None
            self.stop_loss_price = None
            self.take_profit_price = None
            
            return signal
        
        return None
    
    def calculate_position_size(self, signal: Signal, account: Account) -> Decimal:
        """
        Calculate position size based on ATR and account risk.
        
        Args:
            signal: Trading signal
            account: Current account state
            
        Returns:
            Position size
        """
        # Risk a fixed percentage of account per trade
        risk_percentage = Decimal("0.02")  # 2% risk per trade
        risk_amount = account.available_balance * risk_percentage
        
        # Get stop loss from metadata
        if "stop_loss" in signal.metadata:
            stop_loss = Decimal(signal.metadata["stop_loss"])
            price_risk = abs(signal.price - stop_loss)
            
            if price_risk > 0:
                size = risk_amount / price_risk
                return size
        
        # Fallback to simple calculation
        return account.available_balance * Decimal("0.1") / signal.price
    
    def _calculate_atr(self, candles: List[Candle], period: int) -> Optional[Decimal]:
        """
        Calculate Average True Range.
        
        Args:
            candles: List of candles
            period: ATR period
            
        Returns:
            ATR value or None if insufficient data
        """
        if len(candles) < period + 1:
            return None
        
        true_ranges = []
        
        for i in range(len(candles) - period, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i - 1].close if i > 0 else candles[i].open
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        if not true_ranges:
            return None
        
        atr = sum(true_ranges) / Decimal(str(len(true_ranges)))
        return atr
    
    def on_order_filled(self, order: Order):
        """
        Handle order filled callback.
        
        Args:
            order: Filled order
        """
        # Reset position tracking if this was a close order
        if order.metadata.get("exit_reason"):
            self.position_entry_price = None
            self.position_side = None
            self.stop_loss_price = None
            self.take_profit_price = None
