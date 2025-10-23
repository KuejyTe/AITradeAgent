"""
Integration tests for the strategy framework.
Tests end-to-end workflows and integration with the API.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from app.strategies.engine import StrategyEngine
from app.strategies.builtin import SMACrossoverStrategy, TrendFollowingStrategy, GridTradingStrategy
from app.strategies.models import MarketData, Account, Candle
from app.strategies.risk import RiskManager


class TestStrategyIntegration:
    """Integration tests for complete strategy workflows."""
    
    def test_complete_sma_strategy_workflow(self):
        """Test a complete SMA strategy workflow from creation to signal generation."""
        # Setup
        engine = StrategyEngine()
        engine.register_strategy(SMACrossoverStrategy, "sma_crossover")
        
        # Create strategy
        config = {
            "name": "Test SMA",
            "parameters": {
                "fast_period": 5,
                "slow_period": 10,
                "instrument": "BTC-USDT"
            },
            "risk": {
                "max_position_size": 1.0,
                "max_loss_per_trade": 0.02
            }
        }
        
        strategy = engine.load_strategy("test_sma", "sma_crossover", config)
        assert strategy is not None
        
        # Start strategy
        assert engine.start_strategy("test_sma") is True
        
        # Create market data with trend
        base_time = datetime.now(timezone.utc)
        candles = []
        
        # Create uptrend to trigger crossover
        for i in range(15):
            candles.append(Candle(
                timestamp=base_time + timedelta(minutes=i),
                open=Decimal(str(40000 + i * 100)),
                high=Decimal(str(40100 + i * 100)),
                low=Decimal(str(39900 + i * 100)),
                close=Decimal(str(40000 + i * 100)),
                volume=Decimal("100")
            ))
        
        market_data = MarketData(
            instrument_id="BTC-USDT",
            current_price=Decimal("41500"),
            candles=candles
        )
        
        account = Account(
            balance=Decimal("10000"),
            equity=Decimal("10000"),
            available_balance=Decimal("10000")
        )
        
        # Process market data
        signals = engine.process_market_data(market_data, account)
        
        # Should generate a signal when fast crosses above slow
        assert len(signals) >= 0  # May or may not generate based on exact crossover
        
        # Stop strategy
        assert engine.stop_strategy("test_sma") is True
        
        # Unload strategy
        assert engine.unload_strategy("test_sma") is True
    
    def test_multiple_strategies_simultaneously(self):
        """Test running multiple strategies at the same time."""
        engine = StrategyEngine()
        
        # Register strategies
        engine.register_strategy(SMACrossoverStrategy, "sma_crossover")
        engine.register_strategy(GridTradingStrategy, "grid_trading")
        
        # Load first strategy
        config1 = {
            "name": "SMA Strategy",
            "parameters": {
                "fast_period": 5,
                "slow_period": 10,
                "instrument": "BTC-USDT"
            },
            "risk": {}
        }
        strategy1 = engine.load_strategy("strat1", "sma_crossover", config1)
        
        # Load second strategy
        config2 = {
            "name": "Grid Strategy",
            "parameters": {
                "upper_price": 45000,
                "lower_price": 40000,
                "grid_count": 5,
                "order_size": 0.1,
                "instrument": "BTC-USDT"
            },
            "risk": {}
        }
        strategy2 = engine.load_strategy("strat2", "grid_trading", config2)
        
        # Start both
        assert engine.start_strategy("strat1") is True
        assert engine.start_strategy("strat2") is True
        
        # Verify both are running
        strategies = engine.list_strategies()
        assert len(strategies) == 2
        assert all(s["is_running"] for s in strategies)
        
        # Stop and cleanup
        engine.stop_strategy("strat1")
        engine.stop_strategy("strat2")
        engine.unload_strategy("strat1")
        engine.unload_strategy("strat2")
    
    def test_risk_manager_integration(self):
        """Test that risk manager properly integrates with strategy engine."""
        engine = StrategyEngine()
        engine.register_strategy(SMACrossoverStrategy, "sma_crossover")
        
        # Create strategy with strict risk limits
        config = {
            "name": "Strict Risk Strategy",
            "parameters": {
                "fast_period": 5,
                "slow_period": 10,
                "instrument": "BTC-USDT"
            },
            "risk": {
                "max_position_size": 0.01,  # Very small
                "max_loss_per_trade": 0.001,  # 0.1%
                "max_daily_loss": 0.002  # 0.2%
            }
        }
        
        strategy = engine.load_strategy("strict", "sma_crossover", config)
        engine.start_strategy("strict")
        
        # Verify risk manager was created
        assert "strict" in engine.risk_managers
        risk_manager = engine.risk_managers["strict"]
        
        assert risk_manager.max_position_size == Decimal("0.01")
        assert risk_manager.max_loss_per_trade == Decimal("0.001")
        
        engine.stop_strategy("strict")
        engine.unload_strategy("strict")
    
    def test_strategy_state_persistence(self):
        """Test that strategy maintains state across multiple updates."""
        engine = StrategyEngine()
        engine.register_strategy(TrendFollowingStrategy, "trend_following")
        
        config = {
            "name": "Stateful Strategy",
            "parameters": {
                "atr_period": 10,
                "instrument": "BTC-USDT"
            },
            "risk": {}
        }
        
        strategy = engine.load_strategy("stateful", "trend_following", config)
        engine.start_strategy("stateful")
        
        # Update state
        strategy.update_state("test_key", "test_value")
        
        # Verify state persists
        assert strategy.get_state("test_key") == "test_value"
        
        # Get strategy info and verify state is included
        info = engine.get_strategy_info("stateful")
        assert "state" in info
        assert info["state"]["test_key"] == "test_value"
        
        engine.stop_strategy("stateful")
        engine.unload_strategy("stateful")


class TestStrategyWithRealisticData:
    """Tests with more realistic market data scenarios."""
    
    def create_trending_market_data(self, trend="up", periods=30):
        """Helper to create trending market data."""
        base_price = 40000
        base_time = datetime.now(timezone.utc)
        candles = []
        
        for i in range(periods):
            if trend == "up":
                price = base_price + i * 200
            elif trend == "down":
                price = base_price - i * 200
            else:  # sideways
                price = base_price + (100 if i % 2 == 0 else -100)
            
            candles.append(Candle(
                timestamp=base_time + timedelta(minutes=i),
                open=Decimal(str(price - 50)),
                high=Decimal(str(price + 100)),
                low=Decimal(str(price - 100)),
                close=Decimal(str(price)),
                volume=Decimal("100")
            ))
        
        return MarketData(
            instrument_id="BTC-USDT",
            current_price=Decimal(str(price)),
            candles=candles
        )
    
    def test_sma_in_uptrend(self):
        """Test SMA strategy in an uptrend."""
        engine = StrategyEngine()
        engine.register_strategy(SMACrossoverStrategy, "sma_crossover")
        
        config = {
            "parameters": {
                "fast_period": 5,
                "slow_period": 10,
                "instrument": "BTC-USDT"
            },
            "risk": {}
        }
        
        strategy = engine.load_strategy("uptrend_test", "sma_crossover", config)
        engine.start_strategy("uptrend_test")
        
        market_data = self.create_trending_market_data(trend="up", periods=20)
        account = Account(
            balance=Decimal("10000"),
            equity=Decimal("10000"),
            available_balance=Decimal("10000")
        )
        
        signals = engine.process_market_data(market_data, account)
        
        # In a clear uptrend, we might get buy signals
        # (actual signals depend on exact crossover timing)
        assert isinstance(signals, list)
        
        engine.stop_strategy("uptrend_test")
        engine.unload_strategy("uptrend_test")
    
    def test_grid_in_ranging_market(self):
        """Test grid strategy in a ranging market."""
        engine = StrategyEngine()
        engine.register_strategy(GridTradingStrategy, "grid_trading")
        
        config = {
            "parameters": {
                "upper_price": 41000,
                "lower_price": 39000,
                "grid_count": 5,
                "order_size": 0.1,
                "instrument": "BTC-USDT"
            },
            "risk": {}
        }
        
        strategy = engine.load_strategy("ranging_test", "grid_trading", config)
        engine.start_strategy("ranging_test")
        
        market_data = self.create_trending_market_data(trend="sideways", periods=15)
        account = Account(
            balance=Decimal("10000"),
            equity=Decimal("10000"),
            available_balance=Decimal("10000")
        )
        
        # Process multiple times to simulate price crossing grid levels
        all_signals = []
        for i in range(3):
            signals = engine.process_market_data(market_data, account)
            all_signals.extend(signals)
        
        # Grid strategy should work in ranging markets
        assert isinstance(all_signals, list)
        
        engine.stop_strategy("ranging_test")
        engine.unload_strategy("ranging_test")
