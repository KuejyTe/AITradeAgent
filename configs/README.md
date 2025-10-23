# Strategy Configuration Examples

This directory contains example configuration files for various trading strategies.

## Available Strategy Configurations

### 1. SMA Crossover Strategy (`strategy_example.json`)

Classic moving average crossover strategy that generates buy signals when a fast-moving average crosses above a slow-moving average, and sell signals when it crosses below.

**Use Case:** Trending markets with clear directional movements.

**Key Parameters:**
- `fast_period`: Period for the fast moving average (default: 10)
- `slow_period`: Period for the slow moving average (default: 30)

### 2. Trend Following Strategy (`trend_following_example.json`)

ATR-based breakout strategy that identifies strong trends and enters positions with dynamic stop-loss and take-profit levels.

**Use Case:** Markets with strong momentum and clear breakouts.

**Key Parameters:**
- `atr_period`: Period for ATR calculation (default: 14)
- `stop_loss_multiplier`: Stop loss distance in ATR multiples (default: 2.0)
- `take_profit_multiplier`: Take profit distance in ATR multiples (default: 3.0)

### 3. Grid Trading Strategy (`grid_trading_example.json`)

Places buy and sell orders at fixed price intervals, ideal for ranging markets.

**Use Case:** Sideways/ranging markets with predictable oscillations.

**Key Parameters:**
- `upper_price`: Upper bound of the trading grid
- `lower_price`: Lower bound of the trading grid
- `grid_count`: Number of grid levels (default: 10)
- `order_size`: Size of each grid order

## Risk Parameters

All strategies support the following risk management parameters:

- `max_position_size`: Maximum position size in base currency
- `max_loss_per_trade`: Maximum loss per trade as % of equity (e.g., 0.02 = 2%)
- `max_daily_loss`: Maximum daily loss as % of equity (e.g., 0.05 = 5%)
- `stop_loss_pct`: Default stop loss percentage (e.g., 0.05 = 5%)
- `take_profit_pct`: Default take profit percentage (e.g., 0.10 = 10%)
- `max_leverage`: Maximum allowed leverage (e.g., 2.0 = 2x)
- `max_positions`: Maximum number of concurrent positions

## Usage

### Via API

Use the configuration files with the strategies API:

```bash
# Create a strategy using configuration
curl -X POST http://localhost:8000/api/v1/strategies \
  -H "Content-Type: application/json" \
  -d @configs/strategy_example.json
```

### Via Python

```python
import json
from app.strategies.engine import strategy_engine
from app.strategies.builtin import SMACrossoverStrategy

# Load configuration
with open('configs/strategy_example.json', 'r') as f:
    config = json.load(f)

# Register and load strategy
strategy_engine.register_strategy(SMACrossoverStrategy, "sma_crossover")
strategy = strategy_engine.load_strategy(
    strategy_id="my_strategy_1",
    strategy_type=config["strategy_type"],
    config={
        "name": "My SMA Strategy",
        "parameters": config["parameters"],
        "risk": config["risk"]
    }
)

# Start the strategy
strategy_engine.start_strategy("my_strategy_1")
```

## Customization

Feel free to modify these configuration files to suit your trading style:

1. Adjust timeframes (periods) based on your trading horizon
2. Modify risk parameters based on your risk tolerance
3. Change instrument symbols to trade different assets
4. Experiment with different parameter combinations

## Testing

Before deploying a strategy with real capital, always:

1. **Backtest** - Test on historical data
2. **Paper Trade** - Test with virtual money in live conditions
3. **Start Small** - Begin with minimal position sizes
4. **Monitor Closely** - Watch performance and adjust parameters as needed

## Best Practices

### Position Sizing
- Never risk more than 1-2% of your account per trade
- Adjust position sizes based on market volatility
- Consider correlation between multiple positions

### Risk Management
- Always use stop losses
- Set realistic take profit targets
- Don't trade when daily loss limit is reached
- Limit the number of concurrent positions

### Strategy Selection
- **Trending Markets**: Use SMA Crossover or Trend Following
- **Ranging Markets**: Use Grid Trading
- **High Volatility**: Reduce position sizes and widen stops
- **Low Volatility**: Consider grid trading strategies

## Support

For questions or issues with strategy configuration, please refer to:
- Main documentation: `STRATEGY_FRAMEWORK.md`
- API documentation: `http://localhost:8000/docs` (when server is running)
