from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal

from app.strategies.signals import Signal
from app.strategies.models import MarketData, Account, Order


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    All custom strategies should inherit from this class and implement the abstract methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the strategy with configuration.
        
        Args:
            config: Dictionary containing strategy configuration parameters
        """
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.parameters = config.get("parameters", {})
        self.is_running = False
        self.state: Dict[str, Any] = {}
    
    @abstractmethod
    def analyze(self, market_data: MarketData) -> Optional[Signal]:
        """
        Analyze market data and generate trading signals.
        
        Args:
            market_data: Current market data including price, volume, and historical candles
            
        Returns:
            Signal object if a trading opportunity is identified, None otherwise
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Signal, account: Account) -> Decimal:
        """
        Calculate the position size for a given signal based on account state.
        
        Args:
            signal: The trading signal to execute
            account: Current account state with balance and positions
            
        Returns:
            Position size as a Decimal value
        """
        pass
    
    def validate_signal(self, signal: Signal) -> bool:
        """
        Validate the generated signal before execution.
        
        Args:
            signal: The signal to validate
            
        Returns:
            True if the signal is valid, False otherwise
        """
        if signal is None:
            return False
        
        if signal.size <= 0:
            return False
        
        if signal.confidence < 0 or signal.confidence > 1:
            return False
        
        if signal.price <= 0:
            return False
        
        return True
    
    def on_order_filled(self, order: Order):
        """
        Callback invoked when an order is filled.
        Can be overridden to implement custom logic.
        
        Args:
            order: The filled order
        """
        pass
    
    def on_start(self):
        """
        Callback invoked when the strategy starts.
        Can be overridden to perform initialization.
        """
        self.is_running = True
    
    def on_stop(self):
        """
        Callback invoked when the strategy stops.
        Can be overridden to perform cleanup.
        """
        self.is_running = False
    
    def update_state(self, key: str, value: Any):
        """
        Update strategy internal state.
        
        Args:
            key: State key
            value: State value
        """
        self.state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get strategy internal state.
        
        Args:
            key: State key
            default: Default value if key doesn't exist
            
        Returns:
            State value or default
        """
        return self.state.get(key, default)
