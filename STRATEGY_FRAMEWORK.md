# AI Trading Strategy Framework Documentation

## Overview

The AI Trading Strategy Framework provides a flexible and extensible system for developing, testing, and deploying automated trading strategies. The framework supports multiple strategy types, dynamic loading, risk management, and backtesting capabilities.

## Architecture

### Core Components

1. **BaseStrategy** - Abstract base class for all strategies
2. **StrategyEngine** - Manages strategy lifecycle and execution
3. **RiskManager** - Validates and adjusts signals based on risk parameters
4. **Backtester** - Framework for testing strategies on historical data

### Data Models

- **Signal** - Represents a trading signal (BUY, SELL, HOLD, CLOSE)
- **MarketData** - Contains current market information and historical candles
- **Account** - Represents account state including balance and positions
- **Order** - Represents a trading order
- **Position** - Represents an open position

## Creating Custom Strategies

### Step 1: Inherit from BaseStrategy

```python
from app.strategies.base import BaseStrategy
from app.strategies.signals import Signal, SignalType
from app.strategies.models import MarketData, Account

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        # Initialize your strategy parameters
        self.my_parameter = self.parameters.get("my_parameter", default_value)
    
    def analyze(self, market_data: MarketData) -> Signal:
        """
        Implement your strategy logic here.
        Return a Signal if a trading opportunity is found, None otherwise.
        """
        # Your analysis logic
        pass
    
    def calculate_position_size(self, signal: Signal, account: Account) -> Decimal:
        """
        Calculate the position size based on your risk management rules.
        """
        # Your position sizing logic
        pass
```

### Step 2: Register Your Strategy

```python
from app.strategies.engine import strategy_engine
from my_strategies import MyCustomStrategy

# Register the strategy
strategy_engine.register_strategy(MyCustomStrategy, "my_custom_strategy")
```

### Step 3: Configure and Load

Create a configuration file (JSON):

```json
{
  "strategy_type": "my_custom_strategy",
  "parameters": {
    "my_parameter": 42,
    "instrument": "BTC-USDT"
  },
  "risk": {
    "max_position_size": 1.0,
    "max_loss_per_trade": 0.02,
    "stop_loss_pct": 0.05
  }
}
```

## Built-in Strategies

### 1. SMA Crossover Strategy

A classic moving average crossover strategy that generates signals when fast and slow SMAs cross.

**Parameters:**
- `fast_period` (default: 10) - Fast SMA period
- `slow_period` (default: 30) - Slow SMA period
- `instrument` - Trading instrument

**Example Configuration:**
```json
{
  "strategy_type": "sma_crossover",
  "parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "instrument": "BTC-USDT"
  }
}
```

### 2. Trend Following Strategy

ATR-based breakout strategy with dynamic stop loss and take profit.

**Parameters:**
- `atr_period` (default: 14) - ATR calculation period
- `breakout_multiplier` (default: 2.0) - Breakout threshold multiplier
- `stop_loss_multiplier` (default: 2.0) - Stop loss distance in ATR multiples
- `take_profit_multiplier` (default: 3.0) - Take profit distance in ATR multiples
- `instrument` - Trading instrument

**Example Configuration:**
```json
{
  "strategy_type": "trend_following",
  "parameters": {
    "atr_period": 14,
    "stop_loss_multiplier": 2.0,
    "take_profit_multiplier": 3.0,
    "instrument": "BTC-USDT"
  }
}
```

### 3. Grid Trading Strategy

Places buy and sell orders at fixed price intervals.

**Parameters:**
- `upper_price` - Upper bound of the grid
- `lower_price` - Lower bound of the grid
- `grid_count` - Number of grid levels
- `order_size` - Size of each grid order
- `instrument` - Trading instrument

**Example Configuration:**
```json
{
  "strategy_type": "grid_trading",
  "parameters": {
    "upper_price": 50000,
    "lower_price": 40000,
    "grid_count": 10,
    "order_size": 0.01,
    "instrument": "BTC-USDT"
  }
}
```

## Risk Management

The RiskManager module provides several safety mechanisms:

### Risk Parameters

- `max_position_size` - Maximum size for a single position
- `max_loss_per_trade` - Maximum loss per trade as % of equity
- `max_daily_loss` - Maximum daily loss as % of equity
- `stop_loss_pct` - Default stop loss percentage
- `take_profit_pct` - Default take profit percentage
- `max_leverage` - Maximum allowed leverage
- `max_positions` - Maximum number of concurrent positions

### Risk Checks

1. **Daily Loss Limit** - Prevents trading if daily loss exceeds threshold
2. **Position Size Validation** - Ensures positions don't exceed limits
3. **Balance Check** - Validates sufficient capital is available
4. **Leverage Control** - Prevents excessive leverage
5. **Position Limit** - Controls number of concurrent positions

## API Endpoints

### Create Strategy

```http
POST /api/v1/strategies
Content-Type: application/json

{
  "name": "My Strategy",
  "strategy_type": "sma_crossover",
  "parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "instrument": "BTC-USDT"
  },
  "risk": {
    "max_position_size": 1.0,
    "max_loss_per_trade": 0.02
  }
}
```

### List All Strategies

```http
GET /api/v1/strategies
```

### Get Strategy Details

```http
GET /api/v1/strategies/{strategy_id}
```

### Update Strategy

```http
PUT /api/v1/strategies/{strategy_id}
Content-Type: application/json

{
  "name": "Updated Strategy Name",
  "parameters": {
    "fast_period": 15
  }
}
```

### Start Strategy

```http
POST /api/v1/strategies/{strategy_id}/start
```

### Stop Strategy

```http
POST /api/v1/strategies/{strategy_id}/stop
```

### Delete Strategy

```http
DELETE /api/v1/strategies/{strategy_id}
```

### Get Strategy Signals

```http
GET /api/v1/strategies/{strategy_id}/signals?limit=50
```

## Backtesting

The backtesting framework allows you to test strategies on historical data.

### Basic Usage

```python
from decimal import Decimal
from app.strategies.backtest import Backtester
from app.strategies.builtin import SMACrossoverStrategy

# Create strategy
config = {
    "parameters": {
        "fast_period": 10,
        "slow_period": 30,
        "instrument": "BTC-USDT"
    }
}
strategy = SMACrossoverStrategy(config)

# Create backtester
backtester = Backtester(
    strategy=strategy,
    initial_balance=Decimal("10000"),
    commission_rate=Decimal("0.001")  # 0.1% commission
)

# Run backtest
result = backtester.run(historical_data)

# View results
print(f"Total PnL: {result.total_pnl}")
print(f"Win Rate: {result.win_rate * 100}%")
print(f"Sharpe Ratio: {result.sharpe_ratio}")
print(f"Max Drawdown: {result.max_drawdown * 100}%")
```

### Performance Metrics

The backtester calculates the following metrics:

- **Total PnL** - Total profit and loss
- **Win Rate** - Percentage of winning trades
- **Profit Factor** - Ratio of gross profit to gross loss
- **Sharpe Ratio** - Risk-adjusted return metric
- **Max Drawdown** - Maximum peak-to-trough decline
- **Equity Curve** - Account equity over time
- **Trade History** - Detailed record of all trades

## Best Practices

### Strategy Development

1. **Start Simple** - Begin with simple logic and add complexity gradually
2. **Test Thoroughly** - Use backtesting to validate your strategy
3. **Risk Management** - Always implement proper risk controls
4. **Parameter Optimization** - Test different parameter combinations
5. **Market Conditions** - Consider different market environments

### Position Sizing

1. Use the `calculate_position_size` method to implement custom position sizing
2. Consider account balance, risk per trade, and signal confidence
3. Implement dynamic position sizing based on market volatility
4. Never risk more than 1-2% of your account on a single trade

### Signal Generation

1. Return `None` if no trading opportunity exists
2. Set appropriate confidence levels (0.0 to 1.0)
3. Include metadata for debugging and analysis
4. Validate signals before returning them

### State Management

Use the strategy's state management methods:

```python
# Store state
self.update_state("my_key", my_value)

# Retrieve state
value = self.get_state("my_key", default_value)
```

## Advanced Features

### Custom Callbacks

Override these methods for custom behavior:

```python
def on_start(self):
    """Called when strategy starts"""
    super().on_start()
    # Your initialization code

def on_stop(self):
    """Called when strategy stops"""
    super().on_stop()
    # Your cleanup code

def on_order_filled(self, order: Order):
    """Called when an order is filled"""
    # Your order handling code
```

### Multi-Instrument Strategies

To trade multiple instruments, check the `instrument_id` in your analyze method:

```python
def analyze(self, market_data: MarketData) -> Signal:
    if market_data.instrument_id not in self.instruments:
        return None
    # Your analysis for this instrument
```

### Dynamic Parameter Adjustment

You can adjust strategy parameters at runtime:

```python
def analyze(self, market_data: MarketData) -> Signal:
    # Adjust parameters based on market conditions
    if self.detect_high_volatility(market_data):
        self.parameters["stop_loss_pct"] = 0.08
    else:
        self.parameters["stop_loss_pct"] = 0.05
```

## Troubleshooting

### Common Issues

1. **Insufficient Balance** - Check that your position sizes don't exceed available balance
2. **Invalid Signals** - Ensure all signal fields are properly set
3. **Risk Rejection** - Verify risk parameters aren't too restrictive
4. **Missing Data** - Ensure market data includes required historical candles

### Logging

The framework uses Python's logging module. Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

See the `configs/` directory for example strategy configurations:

- `strategy_example.json` - SMA Crossover configuration
- `trend_following_example.json` - Trend Following configuration
- `grid_trading_example.json` - Grid Trading configuration

## Contributing

To contribute a new built-in strategy:

1. Create your strategy class in `backend/app/strategies/builtin/`
2. Add it to `backend/app/strategies/builtin/__init__.py`
3. Register it in `backend/app/api/strategies.py`
4. Create example configuration in `configs/`
5. Add documentation to this file

## License

See LICENSE file for details.
