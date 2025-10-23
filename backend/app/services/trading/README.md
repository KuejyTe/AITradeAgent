# Trading Execution Service

Complete trading execution system with order management, risk control, and execution tracking.

## Architecture

```
Trading Execution System
├── TradeExecutor          # Main execution engine
├── OrderManager           # Order lifecycle management
├── PositionManager        # Position tracking and PnL
├── OrderTracker           # Real-time order status tracking
├── ExecutionRiskControl   # Pre-trade and execution risk checks
├── TradeRecorder          # Trade history and performance analytics
└── ExecutionStrategies    # Various execution algorithms
    ├── MarketExecution    # Immediate market order execution
    ├── LimitExecution     # Limit order with timeout
    ├── TWAPExecution      # Time-weighted average price
    └── IcebergExecution   # Hidden size execution
```

## Components

### 1. TradeExecutor

Main component for executing trading signals and managing the order lifecycle.

**Features:**
- Execute trading signals with risk validation
- Place, cancel, and modify orders
- Automatic order tracking
- Error handling and recovery

**Usage:**
```python
from app.services.trading import TradeExecutor, OrderManager, ExecutionRiskControl, OrderTracker
from app.services.okx.client import OKXClient
from app.services.okx.trade import OKXTrade

# Initialize components
okx_client = OKXClient(api_key="...", secret_key="...", passphrase="...")
okx_client.trade = OKXTrade(okx_client)

order_manager = OrderManager(db_session)
risk_control = ExecutionRiskControl()
order_tracker = OrderTracker(okx_client, order_manager)

executor = TradeExecutor(
    okx_client=okx_client,
    order_manager=order_manager,
    risk_manager=risk_control,
    order_tracker=order_tracker
)

# Execute a signal
order = await executor.execute_signal(signal, account, strategy_id="my_strategy")
```

### 2. OrderManager

Manages order database operations and lifecycle.

**Features:**
- Create and track orders
- Update order status
- Query order history
- Synchronize with exchange

**Usage:**
```python
from app.services.trading import OrderManager, OrderParams
from app.models.trading import OrderSide, OrderType

order_manager = OrderManager(db_session)

# Create an order
order_params = OrderParams(
    instrument_id="BTC-USDT",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    size=Decimal("0.1"),
    price=Decimal("50000"),
    trade_mode="cash"
)

order = order_manager.create_order(order_params)

# Get active orders
active_orders = order_manager.get_active_orders("BTC-USDT")

# Get order history
history = order_manager.get_order_history(
    filters={"instrument_id": "BTC-USDT", "status": OrderStatus.FILLED},
    limit=100
)
```

### 3. PositionManager

Tracks positions and calculates PnL.

**Features:**
- Real-time position tracking
- Automatic PnL calculation
- Position updates from trades
- Exchange synchronization

**Usage:**
```python
from app.services.trading import PositionManager

position_manager = PositionManager(db_session)

# Get current position
position = position_manager.get_position("BTC-USDT")

# Update position from trade
updated_position = position_manager.update_position(trade)

# Calculate unrealized PnL
pnl = position_manager.calculate_pnl(position, current_price)

# Get all positions
positions = position_manager.get_all_positions()
```

### 4. OrderTracker

Real-time order status tracking.

**Features:**
- WebSocket and polling-based tracking
- Automatic status updates
- Callback support
- Multi-order tracking

**Usage:**
```python
from app.services.trading import OrderTracker

order_tracker = OrderTracker(okx_client, order_manager)

# Start tracking
async def on_update(order, order_data):
    print(f"Order {order.id} updated: {order.status}")

await order_tracker.start_tracking(
    order_id=order.id,
    exchange_order_id="12345",
    instrument_id="BTC-USDT",
    callback=on_update
)

# Stop tracking
order_tracker.stop_tracking("12345")
```

### 5. ExecutionRiskControl

Pre-trade and execution risk checks.

**Features:**
- Account balance validation
- Position size limits
- Price reasonability checks
- Daily loss limits
- Order parameter validation

**Configuration:**
```python
risk_config = {
    'max_order_size': 10.0,
    'min_order_size': 0.001,
    'max_order_value': 10000.0,
    'max_price_deviation': 0.05,  # 5%
    'max_daily_loss': 0.1,  # 10%
    'max_position_value_pct': 0.5,  # 50%
}

risk_control = ExecutionRiskControl(risk_config)

# Pre-trade check
result = risk_control.pre_trade_check(signal, account)
if not result.passed:
    print(f"Risk check failed: {result.reason}")
```

### 6. TradeRecorder

Records and analyzes trade performance.

**Features:**
- Trade execution recording
- Performance metrics calculation
- Trade statistics
- Sharpe and Sortino ratios
- Maximum drawdown analysis

**Usage:**
```python
from app.services.trading import TradeRecorder

trade_recorder = TradeRecorder(db_session)

# Record a trade
trade = trade_recorder.record_trade(
    order_id=order.id,
    trade_id="t123456",
    instrument_id="BTC-USDT",
    side=OrderSide.BUY,
    price=Decimal("50000"),
    size=Decimal("0.1"),
    fee=Decimal("0.1"),
    fee_currency="USDT"
)

# Calculate performance
metrics = trade_recorder.calculate_performance(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

print(f"Win rate: {metrics.win_rate:.2%}")
print(f"Total PnL: {metrics.total_pnl}")
print(f"Sharpe Ratio: {metrics.sharpe_ratio}")
```

### 7. Execution Strategies

Different execution algorithms for various order types.

#### MarketExecution
Immediate execution at market price.

```python
from app.services.trading.execution_strategies import MarketExecution

strategy = MarketExecution(executor)
orders = await strategy.execute(order_params)
```

#### LimitExecution
Limit order with timeout and optional fallback to market.

```python
from app.services.trading.execution_strategies import LimitExecution

config = {
    'timeout': 60,  # seconds
    'fallback_to_market': True
}

strategy = LimitExecution(executor, config)
orders = await strategy.execute(order_params)
```

#### TWAPExecution
Time-Weighted Average Price - splits large orders over time.

```python
from app.services.trading.execution_strategies import TWAPExecution

config = {
    'duration': 300,  # 5 minutes
    'num_slices': 10,
    'use_limit_orders': False
}

strategy = TWAPExecution(executor, config)
orders = await strategy.execute(order_params)
```

#### IcebergExecution
Hides order size by only showing partial quantity.

```python
from app.services.trading.execution_strategies import IcebergExecution

config = {
    'visible_pct': 0.1,  # 10% visible
    'max_refresh_time': 30,
    'use_limit_orders': True
}

strategy = IcebergExecution(executor, config)
orders = await strategy.execute(order_params)
```

## API Endpoints

### Orders

```
POST   /api/v1/trading/orders           Create new order
GET    /api/v1/trading/orders           List orders with filters
GET    /api/v1/trading/orders/active    Get active orders
GET    /api/v1/trading/orders/{id}      Get order details
DELETE /api/v1/trading/orders/{id}      Cancel order
```

### Positions

```
GET    /api/v1/trading/positions              List all positions
GET    /api/v1/trading/positions/{instrument} Get specific position
POST   /api/v1/trading/positions/sync         Sync with exchange
```

### Trades

```
GET    /api/v1/trading/trades        List trade executions
GET    /api/v1/trading/performance   Get performance metrics
GET    /api/v1/trading/statistics    Get trade statistics
```

## Database Models

### Order
- ID and tracking IDs (client, exchange)
- Instrument and order details
- Status and fill information
- Timestamps and metadata

### Trade
- Trade execution details
- Price, size, and fees
- Liquidity (maker/taker)
- Strategy linkage

### Position
- Current position details
- Entry and current prices
- Unrealized and realized PnL
- Margin and leverage

### ExecutionEvent
- Event type tracking
- Order/Trade/Position links
- Event data and timestamps

## Event System

The trading system emits events for:
- Order creation
- Order status changes
- Order fills
- Order cancellations
- Position opens/closes
- Risk check failures

Events are stored in the `execution_events` table for auditing and analysis.

## Security Measures

1. **Order Signing**: All orders are signed using OKX authentication
2. **Risk Validation**: Pre-trade risk checks on all orders
3. **Audit Logging**: All executions logged to database
4. **Error Handling**: Comprehensive error recovery
5. **Rate Limiting**: Built-in OKX API rate limiting

## Testing

### Unit Tests
```bash
pytest tests/test_trading_executor.py
pytest tests/test_order_manager.py
pytest tests/test_position_manager.py
```

### Integration Tests
```bash
pytest tests/integration/test_trading_flow.py
```

### Mock Trading
Set `ENVIRONMENT=demo` in config to use OKX demo environment.

## Configuration

Required environment variables:
```
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
DATABASE_URL=postgresql://user:pass@localhost/db
```

## Monitoring

Key metrics to monitor:
- Order fill rate
- Average execution time
- Order rejection rate
- Slippage
- Trading fees
- PnL tracking
- Risk check pass/fail rate

## Error Handling

All components implement robust error handling:
- Automatic retry on network errors
- Order status reconciliation
- Position synchronization
- Graceful degradation

## Best Practices

1. Always use risk checks before execution
2. Track orders with OrderTracker
3. Regularly sync positions with exchange
4. Monitor performance metrics
5. Use appropriate execution strategy for order size
6. Maintain sufficient balance for orders
7. Set reasonable timeout values
8. Log all trading activities

## Limitations

- Maximum 20 orders per batch operation (OKX limit)
- Order size limits per instrument
- Rate limits on API calls
- WebSocket connection limits

## Support

For issues or questions:
- Check logs in `backend/logs/trading.log`
- Review execution_events table
- Check order error_message field
- Monitor OrderTracker status
