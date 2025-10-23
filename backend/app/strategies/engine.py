import logging
from typing import Dict, List, Type, Optional, Any
from datetime import datetime, timezone
from decimal import Decimal

from app.strategies.base import BaseStrategy
from app.strategies.signals import Signal, SignalType
from app.strategies.models import MarketData, Account, Order, OrderStatus
from app.strategies.risk import RiskManager


logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    Main strategy engine for managing and executing trading strategies.
    """
    
    def __init__(self):
        """Initialize the strategy engine."""
        self.strategies: Dict[str, Type[BaseStrategy]] = {}
        self.running_strategies: Dict[str, BaseStrategy] = {}
        self.risk_managers: Dict[str, RiskManager] = {}
        self.signals_history: List[Signal] = []
        self.orders_history: List[Order] = []
    
    def register_strategy(self, strategy_class: Type[BaseStrategy], name: Optional[str] = None):
        """
        Register a strategy class for later instantiation.
        
        Args:
            strategy_class: The strategy class to register
            name: Optional name for the strategy (defaults to class name)
        """
        strategy_name = name or strategy_class.__name__
        self.strategies[strategy_name] = strategy_class
        logger.info(f"Registered strategy: {strategy_name}")
    
    def load_strategy(self, strategy_id: str, strategy_type: str, config: Dict[str, Any]) -> Optional[BaseStrategy]:
        """
        Load and instantiate a strategy.
        
        Args:
            strategy_id: Unique identifier for this strategy instance
            strategy_type: Type of strategy to load (must be registered)
            config: Configuration dictionary for the strategy
            
        Returns:
            Instantiated strategy or None if strategy type not found
        """
        if strategy_type not in self.strategies:
            logger.error(f"Strategy type '{strategy_type}' not registered")
            return None
        
        try:
            strategy_class = self.strategies[strategy_type]
            strategy = strategy_class(config)
            self.running_strategies[strategy_id] = strategy
            
            # Initialize risk manager for this strategy
            risk_config = config.get("risk", {})
            self.risk_managers[strategy_id] = RiskManager(risk_config)
            
            logger.info(f"Loaded strategy '{strategy_id}' of type '{strategy_type}'")
            return strategy
        except Exception as e:
            logger.error(f"Failed to load strategy '{strategy_id}': {str(e)}")
            return None
    
    def start_strategy(self, strategy_id: str) -> bool:
        """
        Start a loaded strategy.
        
        Args:
            strategy_id: ID of the strategy to start
            
        Returns:
            True if strategy started successfully, False otherwise
        """
        if strategy_id not in self.running_strategies:
            logger.error(f"Strategy '{strategy_id}' not found")
            return False
        
        try:
            strategy = self.running_strategies[strategy_id]
            strategy.on_start()
            logger.info(f"Started strategy: {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start strategy '{strategy_id}': {str(e)}")
            return False
    
    def stop_strategy(self, strategy_id: str) -> bool:
        """
        Stop a running strategy.
        
        Args:
            strategy_id: ID of the strategy to stop
            
        Returns:
            True if strategy stopped successfully, False otherwise
        """
        if strategy_id not in self.running_strategies:
            logger.error(f"Strategy '{strategy_id}' not found")
            return False
        
        try:
            strategy = self.running_strategies[strategy_id]
            strategy.on_stop()
            logger.info(f"Stopped strategy: {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop strategy '{strategy_id}': {str(e)}")
            return False
    
    def unload_strategy(self, strategy_id: str) -> bool:
        """
        Unload a strategy from the engine.
        
        Args:
            strategy_id: ID of the strategy to unload
            
        Returns:
            True if strategy unloaded successfully, False otherwise
        """
        if strategy_id in self.running_strategies:
            self.stop_strategy(strategy_id)
            del self.running_strategies[strategy_id]
            if strategy_id in self.risk_managers:
                del self.risk_managers[strategy_id]
            logger.info(f"Unloaded strategy: {strategy_id}")
            return True
        return False
    
    def process_market_data(self, market_data: MarketData, account: Account) -> List[Signal]:
        """
        Process market data through all running strategies.
        
        Args:
            market_data: Current market data
            account: Current account state
            
        Returns:
            List of generated signals
        """
        signals = []
        
        for strategy_id, strategy in self.running_strategies.items():
            if not strategy.is_running:
                continue
            
            try:
                signal = strategy.analyze(market_data)
                
                if signal is not None:
                    # Validate signal
                    if not strategy.validate_signal(signal):
                        logger.warning(f"Strategy '{strategy_id}' generated invalid signal")
                        continue
                    
                    # Apply risk management
                    risk_manager = self.risk_managers.get(strategy_id)
                    if risk_manager:
                        adjusted_signal = risk_manager.adjust_signal(signal, account)
                        if adjusted_signal is None:
                            logger.warning(f"Signal from '{strategy_id}' rejected by risk manager")
                            continue
                        signal = adjusted_signal
                    
                    # Calculate position size using strategy
                    signal.size = strategy.calculate_position_size(signal, account)
                    
                    # Add metadata
                    signal.metadata["strategy_id"] = strategy_id
                    signal.metadata["strategy_name"] = strategy.name
                    
                    signals.append(signal)
                    self.signals_history.append(signal)
                    
                    logger.info(f"Strategy '{strategy_id}' generated signal: {signal.type.value} {signal.instrument_id}")
            
            except Exception as e:
                logger.error(f"Error processing market data in strategy '{strategy_id}': {str(e)}")
        
        return signals
    
    def execute_signals(self, signals: List[Signal]) -> List[Order]:
        """
        Convert signals into orders for execution.
        
        Args:
            signals: List of trading signals
            
        Returns:
            List of orders to be executed
        """
        orders = []
        
        for signal in signals:
            try:
                order = self._signal_to_order(signal)
                orders.append(order)
                self.orders_history.append(order)
                logger.info(f"Created order from signal: {order.id}")
            except Exception as e:
                logger.error(f"Failed to create order from signal: {str(e)}")
        
        return orders
    
    def on_order_filled(self, order: Order):
        """
        Notify strategies when an order is filled.
        
        Args:
            order: The filled order
        """
        strategy_id = order.metadata.get("strategy_id")
        
        if strategy_id and strategy_id in self.running_strategies:
            try:
                strategy = self.running_strategies[strategy_id]
                strategy.on_order_filled(order)
            except Exception as e:
                logger.error(f"Error in order filled callback for strategy '{strategy_id}': {str(e)}")
    
    def get_strategy_info(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a strategy.
        
        Args:
            strategy_id: ID of the strategy
            
        Returns:
            Dictionary with strategy information or None if not found
        """
        if strategy_id not in self.running_strategies:
            return None
        
        strategy = self.running_strategies[strategy_id]
        
        return {
            "id": strategy_id,
            "name": strategy.name,
            "type": strategy.__class__.__name__,
            "is_running": strategy.is_running,
            "config": strategy.config,
            "parameters": strategy.parameters,
            "state": strategy.state
        }
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """
        List all loaded strategies.
        
        Returns:
            List of strategy information dictionaries
        """
        return [
            self.get_strategy_info(strategy_id)
            for strategy_id in self.running_strategies.keys()
        ]
    
    def _signal_to_order(self, signal: Signal) -> Order:
        """
        Convert a signal to an order.
        
        Args:
            signal: Trading signal
            
        Returns:
            Order object
        """
        from app.strategies.models import OrderSide, OrderType
        
        # Map signal type to order side
        if signal.type == SignalType.BUY:
            side = OrderSide.BUY
        elif signal.type == SignalType.SELL:
            side = OrderSide.SELL
        elif signal.type == SignalType.CLOSE:
            # Determine side based on existing position
            side = OrderSide.SELL  # Default to sell
        else:
            raise ValueError(f"Cannot convert signal type {signal.type} to order")
        
        order = Order(
            id=f"order_{datetime.now(timezone.utc).timestamp()}",
            instrument_id=signal.instrument_id,
            side=side,
            order_type=OrderType.MARKET,
            price=signal.price,
            size=signal.size,
            status=OrderStatus.PENDING,
            metadata=signal.metadata
        )
        
        return order


# Global strategy engine instance
strategy_engine = StrategyEngine()
