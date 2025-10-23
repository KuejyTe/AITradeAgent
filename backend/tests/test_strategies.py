import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from app.strategies.base import BaseStrategy
from app.strategies.signals import Signal, SignalType
from app.strategies.models import (
    MarketData, Account, Order, Position, Candle,
    OrderSide, OrderStatus, OrderType
)
from app.strategies.risk import RiskManager
from app.strategies.engine import StrategyEngine
from app.strategies.builtin import SMACrossoverStrategy, TrendFollowingStrategy, GridTradingStrategy


class TestSignals:
    """Test signal models."""
    
    def test_signal_creation(self):
        signal = Signal(
            type=SignalType.BUY,
            instrument_id="BTC-USDT",
            price=Decimal("50000"),
            size=Decimal("0.1"),
            confidence=0.8
        )
        
        assert signal.type == SignalType.BUY
        assert signal.instrument_id == "BTC-USDT"
        assert signal.price == Decimal("50000")
        assert signal.size == Decimal("0.1")
        assert signal.confidence == 0.8


class TestRiskManager:
    """Test risk management functionality."""
    
    def test_validate_signal(self):
        config = {
            "max_position_size": 1.0,
            "max_loss_per_trade": 0.02,
            "max_daily_loss": 0.05
        }
        risk_manager = RiskManager(config)
        
        account = Account(
            balance=Decimal("10000"),
            equity=Decimal("10000"),
            available_balance=Decimal("10000"),
            daily_pnl=Decimal("0")
        )
        
        signal = Signal(
            type=SignalType.BUY,
            instrument_id="BTC-USDT",
            price=Decimal("50000"),
            size=Decimal("0.1"),
            confidence=0.8
        )
        
        assert risk_manager.validate_signal(signal, account) is True
    
    def test_daily_loss_limit(self):
        config = {
            "max_position_size": 1.0,
            "max_loss_per_trade": 0.02,
            "max_daily_loss": 0.05
        }
        risk_manager = RiskManager(config)
        
        account = Account(
            balance=Decimal("9000"),
            equity=Decimal("9000"),
            available_balance=Decimal("9000"),
            daily_pnl=Decimal("-1000")  # 10% loss
        )
        
        signal = Signal(
            type=SignalType.BUY,
            instrument_id="BTC-USDT",
            price=Decimal("50000"),
            size=Decimal("0.1"),
            confidence=0.8
        )
        
        # Should reject due to daily loss limit
        assert risk_manager.validate_signal(signal, account) is False
    
    def test_calculate_stop_loss(self):
        config = {"stop_loss_pct": 0.05}
        risk_manager = RiskManager(config)
        
        entry_price = Decimal("50000")
        stop_loss_buy = risk_manager.calculate_stop_loss(entry_price, OrderSide.BUY)
        stop_loss_sell = risk_manager.calculate_stop_loss(entry_price, OrderSide.SELL)
        
        assert stop_loss_buy == Decimal("47500")  # 5% below
        assert stop_loss_sell == Decimal("52500")  # 5% above


class TestStrategyEngine:
    """Test strategy engine functionality."""
    
    def test_register_strategy(self):
        engine = StrategyEngine()
        engine.register_strategy(SMACrossoverStrategy, "sma_crossover")
        
        assert "sma_crossover" in engine.strategies
    
    def test_load_strategy(self):
        engine = StrategyEngine()
        engine.register_strategy(SMACrossoverStrategy, "sma_crossover")
        
        config = {
            "name": "Test SMA Strategy",
            "parameters": {
                "fast_period": 10,
                "slow_period": 30,
                "instrument": "BTC-USDT"
            },
            "risk": {}
        }
        
        strategy = engine.load_strategy("test_strategy_1", "sma_crossover", config)
        
        assert strategy is not None
        assert strategy.name == "Test SMA Strategy"
    
    def test_start_stop_strategy(self):
        engine = StrategyEngine()
        engine.register_strategy(SMACrossoverStrategy, "sma_crossover")
        
        config = {
            "name": "Test Strategy",
            "parameters": {
                "fast_period": 10,
                "slow_period": 30,
                "instrument": "BTC-USDT"
            },
            "risk": {}
        }
        
        engine.load_strategy("test_strategy_2", "sma_crossover", config)
        
        # Start strategy
        assert engine.start_strategy("test_strategy_2") is True
        strategy = engine.running_strategies["test_strategy_2"]
        assert strategy.is_running is True
        
        # Stop strategy
        assert engine.stop_strategy("test_strategy_2") is True
        assert strategy.is_running is False


class TestSMACrossoverStrategy:
    """Test SMA Crossover strategy."""
    
    def test_strategy_initialization(self):
        config = {
            "parameters": {
                "fast_period": 10,
                "slow_period": 30,
                "instrument": "BTC-USDT"
            }
        }
        
        strategy = SMACrossoverStrategy(config)
        
        assert strategy.fast_period == 10
        assert strategy.slow_period == 30
        assert strategy.instrument == "BTC-USDT"
    
    def test_insufficient_data(self):
        config = {
            "parameters": {
                "fast_period": 10,
                "slow_period": 30,
                "instrument": "BTC-USDT"
            }
        }
        
        strategy = SMACrossoverStrategy(config)
        
        # Create market data with insufficient candles
        candles = [
            Candle(
                timestamp=datetime.now(timezone.utc),
                open=Decimal("50000"),
                high=Decimal("51000"),
                low=Decimal("49000"),
                close=Decimal("50500"),
                volume=Decimal("100")
            )
            for _ in range(5)
        ]
        
        market_data = MarketData(
            instrument_id="BTC-USDT",
            current_price=Decimal("50500"),
            candles=candles
        )
        
        signal = strategy.analyze(market_data)
        assert signal is None


class TestTrendFollowingStrategy:
    """Test Trend Following strategy."""
    
    def test_strategy_initialization(self):
        config = {
            "parameters": {
                "atr_period": 14,
                "instrument": "BTC-USDT"
            }
        }
        
        strategy = TrendFollowingStrategy(config)
        
        assert strategy.atr_period == 14
        assert strategy.instrument == "BTC-USDT"


class TestGridTradingStrategy:
    """Test Grid Trading strategy."""
    
    def test_strategy_initialization(self):
        config = {
            "parameters": {
                "upper_price": 50000,
                "lower_price": 40000,
                "grid_count": 10,
                "order_size": 0.01,
                "instrument": "BTC-USDT"
            }
        }
        
        strategy = GridTradingStrategy(config)
        
        assert strategy.upper_price == Decimal("50000")
        assert strategy.lower_price == Decimal("40000")
        assert strategy.grid_count == 10
        assert len(strategy.grid_levels) == 10
    
    def test_grid_levels_calculation(self):
        config = {
            "parameters": {
                "upper_price": 50000,
                "lower_price": 40000,
                "grid_count": 11,
                "order_size": 0.01,
                "instrument": "BTC-USDT"
            }
        }
        
        strategy = GridTradingStrategy(config)
        
        # With 11 levels between 40000 and 50000, step should be 1000
        assert strategy.grid_step == Decimal("1000")
        assert strategy.grid_levels[0] == Decimal("40000")
        assert strategy.grid_levels[-1] == Decimal("50000")
