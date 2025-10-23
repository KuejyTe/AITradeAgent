# Strategy Framework - Quick Start Guide

This guide will help you get started with the AI Trading Strategy Framework in minutes.

## Prerequisites

- Python 3.8+
- FastAPI backend running
- Basic understanding of trading concepts

## Quick Start

### 1. Start the Backend Server

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Create Your First Strategy

Using the API, create a simple SMA crossover strategy:

```bash
curl -X POST http://localhost:8000/api/v1/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Strategy",
    "strategy_type": "sma_crossover",
    "parameters": {
      "fast_period": 10,
      "slow_period": 30,
      "instrument": "BTC-USDT"
    },
    "risk": {
      "max_position_size": 0.1,
      "max_loss_per_trade": 0.02,
      "max_daily_loss": 0.05
    }
  }'
```

Response:
```json
{
  "message": "Strategy created successfully",
  "strategy_id": "sma_crossover_1234567890.123"
}
```

### 3. Start the Strategy

```bash
curl -X POST http://localhost:8000/api/v1/strategies/{strategy_id}/start
```

### 4. Monitor Your Strategy

List all strategies:
```bash
curl http://localhost:8000/api/v1/strategies
```

Get strategy details:
```bash
curl http://localhost:8000/api/v1/strategies/{strategy_id}
```

View generated signals:
```bash
curl http://localhost:8000/api/v1/strategies/{strategy_id}/signals
```

### 5. Stop the Strategy

```bash
curl -X POST http://localhost:8000/api/v1/strategies/{strategy_id}/stop
```

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation where you can test all endpoints directly from your browser.

## Example: Complete Workflow

Here's a complete example using Python:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. Create a strategy
response = requests.post(f"{BASE_URL}/strategies", json={
    "name": "BTC Trend Following",
    "strategy_type": "trend_following",
    "parameters": {
        "atr_period": 14,
        "stop_loss_multiplier": 2.0,
        "take_profit_multiplier": 3.0,
        "instrument": "BTC-USDT"
    },
    "risk": {
        "max_position_size": 0.5,
        "max_loss_per_trade": 0.02,
        "max_daily_loss": 0.05
    }
})

strategy_id = response.json()["strategy_id"]
print(f"Created strategy: {strategy_id}")

# 2. Start the strategy
requests.post(f"{BASE_URL}/strategies/{strategy_id}/start")
print("Strategy started")

# 3. Check strategy status
response = requests.get(f"{BASE_URL}/strategies/{strategy_id}")
strategy = response.json()
print(f"Strategy is running: {strategy['is_running']}")

# 4. View signals (after some time)
response = requests.get(f"{BASE_URL}/strategies/{strategy_id}/signals")
signals = response.json()
print(f"Generated {len(signals['signals'])} signals")

# 5. Stop the strategy when done
requests.post(f"{BASE_URL}/strategies/{strategy_id}/stop")
print("Strategy stopped")
```

## Built-in Strategies Overview

### SMA Crossover
- **Best for**: Trending markets
- **Signals**: Generated on moving average crossovers
- **Parameters**: fast_period, slow_period

### Trend Following
- **Best for**: Strong momentum markets
- **Signals**: Generated on ATR-based breakouts
- **Parameters**: atr_period, stop_loss_multiplier, take_profit_multiplier

### Grid Trading
- **Best for**: Ranging/sideways markets
- **Signals**: Generated at fixed price levels
- **Parameters**: upper_price, lower_price, grid_count, order_size

## Testing with Backtesting

Before running a strategy live, test it on historical data:

```python
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from app.strategies.backtest import Backtester
from app.strategies.builtin import SMACrossoverStrategy
from app.strategies.models import MarketData, Candle

# Create strategy
config = {
    "parameters": {
        "fast_period": 10,
        "slow_period": 30,
        "instrument": "BTC-USDT"
    }
}
strategy = SMACrossoverStrategy(config)

# Prepare historical data (you would load real data here)
historical_data = []  # List of MarketData objects

# Run backtest
backtester = Backtester(
    strategy=strategy,
    initial_balance=Decimal("10000"),
    commission_rate=Decimal("0.001")
)

result = backtester.run(historical_data)

# View results
print(f"Initial Balance: {result.initial_balance}")
print(f"Final Balance: {result.final_balance}")
print(f"Total PnL: {result.total_pnl}")
print(f"Win Rate: {result.win_rate * 100}%")
print(f"Sharpe Ratio: {result.sharpe_ratio}")
print(f"Max Drawdown: {result.max_drawdown * 100}%")
print(f"Total Trades: {result.total_trades}")
```

## Creating a Custom Strategy

Create a new file `my_custom_strategy.py`:

```python
from decimal import Decimal
from typing import Optional
from app.strategies.base import BaseStrategy
from app.strategies.signals import Signal, SignalType
from app.strategies.models import MarketData, Account

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        # Your parameters
        self.threshold = Decimal(str(self.parameters.get("threshold", 0.02)))
    
    def analyze(self, market_data: MarketData) -> Optional[Signal]:
        # Your trading logic
        if not market_data.candles:
            return None
        
        current_price = market_data.current_price
        # Example: Buy when price increases by threshold
        if len(market_data.candles) >= 2:
            prev_price = market_data.candles[-2].close
            price_change = (current_price - prev_price) / prev_price
            
            if price_change > self.threshold:
                return Signal(
                    type=SignalType.BUY,
                    instrument_id=market_data.instrument_id,
                    price=current_price,
                    size=Decimal("1.0"),
                    confidence=0.7
                )
        
        return None
    
    def calculate_position_size(self, signal: Signal, account: Account) -> Decimal:
        # Risk 2% of account balance
        risk_amount = account.available_balance * Decimal("0.02")
        return risk_amount / signal.price
```

Register and use it:

```python
from app.strategies.engine import strategy_engine
from my_custom_strategy import MyCustomStrategy

# Register
strategy_engine.register_strategy(MyCustomStrategy, "my_custom")

# Load
config = {
    "name": "My Custom Strategy",
    "parameters": {"threshold": 0.02, "instrument": "BTC-USDT"},
    "risk": {"max_position_size": 1.0}
}
strategy_engine.load_strategy("custom_1", "my_custom", config)
strategy_engine.start_strategy("custom_1")
```

## Best Practices

1. **Start Small**: Begin with small position sizes
2. **Test First**: Always backtest before going live
3. **Monitor Actively**: Watch your strategies, especially initially
4. **Risk Management**: Never disable risk controls
5. **Diversify**: Don't put all capital in one strategy
6. **Keep Learning**: Analyze performance and adjust parameters

## Common Issues

### Strategy Not Generating Signals
- Check if market data includes enough historical candles
- Verify the instrument ID matches your market data
- Review strategy parameters (periods might be too large)

### Risk Manager Rejecting Signals
- Check available account balance
- Verify daily loss limit hasn't been reached
- Ensure position size is within limits

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify you're in the correct directory
- Check Python path includes the `backend` directory

## Next Steps

- Read the full documentation: `STRATEGY_FRAMEWORK.md`
- Explore example configurations: `configs/`
- Check the API documentation: `http://localhost:8000/docs`
- Join the community (if available) for support and discussions

## Resources

- **Full Documentation**: STRATEGY_FRAMEWORK.md
- **API Reference**: http://localhost:8000/docs
- **Example Configs**: configs/
- **Tests**: backend/tests/test_strategies.py

Happy Trading! 🚀
