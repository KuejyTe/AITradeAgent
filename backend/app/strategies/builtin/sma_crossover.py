from decimal import Decimal
from typing import Dict, Any, Optional, List

from app.strategies.base import BaseStrategy
from app.strategies.signals import Signal, SignalType
from app.strategies.models import MarketData, Account, Candle


class SMACrossoverStrategy(BaseStrategy):
    """
    Simple Moving Average (SMA) Crossover Strategy.
    
    Generates buy signals when the fast SMA crosses above the slow SMA,
    and sell signals when the fast SMA crosses below the slow SMA.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Get strategy parameters
        self.fast_period = self.parameters.get("fast_period", 10)
        self.slow_period = self.parameters.get("slow_period", 30)
        self.instrument = self.parameters.get("instrument", "BTC-USDT")
        
        # Validate parameters
        if self.fast_period >= self.slow_period:
            raise ValueError("Fast period must be less than slow period")
        
        # Internal state
        self.last_signal = None
    
    def analyze(self, market_data: MarketData) -> Optional[Signal]:
        """
        Analyze market data using SMA crossover logic.
        
        Args:
            market_data: Market data with historical candles
            
        Returns:
            Signal if crossover detected, None otherwise
        """
        # Check if this is the right instrument
        if market_data.instrument_id != self.instrument:
            return None
        
        # Check if we have enough candles
        if len(market_data.candles) < self.slow_period:
            return None
        
        # Calculate SMAs
        fast_sma = self._calculate_sma(market_data.candles, self.fast_period)
        slow_sma = self._calculate_sma(market_data.candles, self.slow_period)
        
        if fast_sma is None or slow_sma is None:
            return None
        
        # Get previous SMAs for crossover detection
        prev_fast_sma = self._calculate_sma(market_data.candles[:-1], self.fast_period)
        prev_slow_sma = self._calculate_sma(market_data.candles[:-1], self.slow_period)
        
        if prev_fast_sma is None or prev_slow_sma is None:
            return None
        
        # Detect crossover
        signal_type = None
        confidence = 0.0
        
        # Bullish crossover: fast crosses above slow
        if prev_fast_sma <= prev_slow_sma and fast_sma > slow_sma:
            signal_type = SignalType.BUY
            # Calculate confidence based on the strength of the crossover
            crossover_strength = abs(fast_sma - slow_sma) / slow_sma
            confidence = min(0.5 + float(crossover_strength) * 10, 1.0)
        
        # Bearish crossover: fast crosses below slow
        elif prev_fast_sma >= prev_slow_sma and fast_sma < slow_sma:
            signal_type = SignalType.SELL
            crossover_strength = abs(fast_sma - slow_sma) / slow_sma
            confidence = min(0.5 + float(crossover_strength) * 10, 1.0)
        
        # No crossover
        else:
            return None
        
        # Create signal
        signal = Signal(
            type=signal_type,
            instrument_id=market_data.instrument_id,
            price=market_data.current_price,
            size=Decimal("1.0"),  # Will be adjusted by risk manager
            confidence=confidence,
            metadata={
                "fast_sma": str(fast_sma),
                "slow_sma": str(slow_sma),
                "fast_period": self.fast_period,
                "slow_period": self.slow_period
            }
        )
        
        self.last_signal = signal_type
        return signal
    
    def calculate_position_size(self, signal: Signal, account: Account) -> Decimal:
        """
        Calculate position size based on account balance and signal confidence.
        
        Args:
            signal: Trading signal
            account: Current account state
            
        Returns:
            Position size
        """
        # Use a percentage of available balance based on confidence
        risk_percentage = Decimal(str(0.1 * signal.confidence))  # Max 10% of balance
        max_capital = account.available_balance * risk_percentage
        
        # Calculate size based on price
        size = max_capital / signal.price
        
        return size
    
    def _calculate_sma(self, candles: List[Candle], period: int) -> Optional[Decimal]:
        """
        Calculate Simple Moving Average for the given period.
        
        Args:
            candles: List of candles
            period: SMA period
            
        Returns:
            SMA value or None if insufficient data
        """
        if len(candles) < period:
            return None
        
        # Use the most recent 'period' candles
        recent_candles = candles[-period:]
        
        # Calculate average of close prices
        total = sum(candle.close for candle in recent_candles)
        sma = total / Decimal(str(period))
        
        return sma
