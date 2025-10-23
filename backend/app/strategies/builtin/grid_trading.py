from decimal import Decimal
from typing import Dict, Any, Optional, List

from app.strategies.base import BaseStrategy
from app.strategies.signals import Signal, SignalType
from app.strategies.models import MarketData, Account, Order


class GridTradingStrategy(BaseStrategy):
    """
    Grid Trading Strategy.
    
    Places buy and sell orders at fixed price intervals (grids).
    Automatically buys on dips and sells on rises within a price range.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Get strategy parameters
        self.upper_price = Decimal(str(self.parameters.get("upper_price", 50000)))
        self.lower_price = Decimal(str(self.parameters.get("lower_price", 40000)))
        self.grid_count = self.parameters.get("grid_count", 10)
        self.order_size = Decimal(str(self.parameters.get("order_size", 0.01)))
        self.instrument = self.parameters.get("instrument", "BTC-USDT")
        
        # Validate parameters
        if self.upper_price <= self.lower_price:
            raise ValueError("Upper price must be greater than lower price")
        if self.grid_count < 2:
            raise ValueError("Grid count must be at least 2")
        
        # Calculate grid levels
        self.grid_step = (self.upper_price - self.lower_price) / Decimal(str(self.grid_count - 1))
        self.grid_levels = [
            self.lower_price + self.grid_step * Decimal(str(i))
            for i in range(self.grid_count)
        ]
        
        # Track grid positions
        self.active_levels: Dict[int, bool] = {i: False for i in range(self.grid_count)}
        self.filled_orders: List[Dict[str, Any]] = []
        self.last_price = None
    
    def analyze(self, market_data: MarketData) -> Optional[Signal]:
        """
        Analyze market data and generate grid trading signals.
        
        Args:
            market_data: Current market data
            
        Returns:
            Signal if price crosses a grid level, None otherwise
        """
        # Check if this is the right instrument
        if market_data.instrument_id != self.instrument:
            return None
        
        current_price = market_data.current_price
        
        # Check if price is within grid range
        if current_price < self.lower_price or current_price > self.upper_price:
            return None
        
        # Find the nearest grid level
        signal = None
        
        # If this is the first price update
        if self.last_price is None:
            self.last_price = current_price
            return None
        
        # Check if price crossed a grid level
        for i, level in enumerate(self.grid_levels):
            # Price crossed upward through a grid level
            if self.last_price < level <= current_price:
                # Sell at this level
                signal = self._create_sell_signal(market_data, level, i)
                break
            
            # Price crossed downward through a grid level
            elif self.last_price > level >= current_price:
                # Buy at this level
                signal = self._create_buy_signal(market_data, level, i)
                break
        
        self.last_price = current_price
        return signal
    
    def _create_buy_signal(self, market_data: MarketData, level: Decimal, level_index: int) -> Signal:
        """
        Create a buy signal at a grid level.
        
        Args:
            market_data: Current market data
            level: Grid price level
            level_index: Index of the grid level
            
        Returns:
            Buy signal
        """
        signal = Signal(
            type=SignalType.BUY,
            instrument_id=market_data.instrument_id,
            price=level,
            size=self.order_size,
            confidence=0.7,
            metadata={
                "grid_level": str(level),
                "grid_index": level_index,
                "strategy_type": "grid_trading"
            }
        )
        
        self.active_levels[level_index] = True
        return signal
    
    def _create_sell_signal(self, market_data: MarketData, level: Decimal, level_index: int) -> Signal:
        """
        Create a sell signal at a grid level.
        
        Args:
            market_data: Current market data
            level: Grid price level
            level_index: Index of the grid level
            
        Returns:
            Sell signal
        """
        signal = Signal(
            type=SignalType.SELL,
            instrument_id=market_data.instrument_id,
            price=level,
            size=self.order_size,
            confidence=0.7,
            metadata={
                "grid_level": str(level),
                "grid_index": level_index,
                "strategy_type": "grid_trading"
            }
        )
        
        self.active_levels[level_index] = True
        return signal
    
    def calculate_position_size(self, signal: Signal, account: Account) -> Decimal:
        """
        Calculate position size for grid orders.
        
        Args:
            signal: Trading signal
            account: Current account state
            
        Returns:
            Position size (fixed for grid trading)
        """
        # Grid trading uses fixed order sizes
        # But check if we have sufficient balance
        required_capital = signal.price * self.order_size
        
        if required_capital > account.available_balance:
            # Scale down the order size
            return account.available_balance / signal.price * Decimal("0.95")  # 95% to leave some buffer
        
        return self.order_size
    
    def on_order_filled(self, order: Order):
        """
        Track filled orders for profit calculation.
        
        Args:
            order: Filled order
        """
        grid_index = order.metadata.get("grid_index")
        
        if grid_index is not None:
            self.filled_orders.append({
                "order_id": order.id,
                "side": order.side.value,
                "price": order.price,
                "size": order.filled_size,
                "grid_index": grid_index,
                "timestamp": order.filled_at
            })
            
            # Mark this level as inactive for now
            self.active_levels[grid_index] = False
    
    def get_grid_status(self) -> Dict[str, Any]:
        """
        Get current grid status.
        
        Returns:
            Dictionary with grid information
        """
        return {
            "grid_levels": [str(level) for level in self.grid_levels],
            "active_levels": self.active_levels,
            "filled_orders_count": len(self.filled_orders),
            "last_price": str(self.last_price) if self.last_price else None
        }
    
    def on_start(self):
        """Initialize grid when strategy starts."""
        super().on_start()
        self.update_state("grid_status", self.get_grid_status())
    
    def on_stop(self):
        """Clean up when strategy stops."""
        super().on_stop()
        # Could implement logic to close all open positions here
