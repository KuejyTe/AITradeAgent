# OKX API Client

Complete Python implementation of OKX Exchange API including REST and WebSocket clients.

## Features

- ✅ REST API client with authentication
- ✅ WebSocket client with auto-reconnection
- ✅ Rate limiting and error handling
- ✅ Comprehensive market data endpoints
- ✅ Full trading functionality
- ✅ Account management
- ✅ Type hints and documentation

## Installation

The OKX client requires the following dependencies (already in requirements.txt):
- httpx
- websockets
- pydantic-settings

## Configuration

Add your OKX API credentials to `.env`:

```env
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
OKX_API_BASE_URL=https://www.okx.com
OKX_WS_PUBLIC_URL=wss://ws.okx.com:8443/ws/v5/public
OKX_WS_PRIVATE_URL=wss://ws.okx.com:8443/ws/v5/private
```

## Quick Start

### REST API

#### Market Data (No Authentication Required)

```python
from app.services.okx import OKXClient, OKXMarket

# Create client
client = OKXClient()
market = OKXMarket(client)

# Get ticker
ticker = await market.get_ticker("BTC-USDT")
print(f"BTC-USDT price: {ticker[0]['last']}")

# Get candlestick data
candles = await market.get_candles("BTC-USDT", bar="1H", limit=100)

# Get order book
order_book = await market.get_order_book("BTC-USDT", depth=20)

# Get recent trades
trades = await market.get_trades("BTC-USDT", limit=50)

# Get instrument information
instruments = await market.get_instruments("SPOT")

# Close client when done
await client.close()
```

#### Trading (Authentication Required)

```python
from app.services.okx import OKXClient, OKXTrade
from app.core.config import settings

# Create authenticated client
client = OKXClient(
    api_key=settings.OKX_API_KEY,
    secret_key=settings.OKX_SECRET_KEY,
    passphrase=settings.OKX_PASSPHRASE
)
trade = OKXTrade(client)

# Place a limit order
order = await trade.place_order(
    inst_id="BTC-USDT",
    td_mode="cash",
    side="buy",
    ord_type="limit",
    sz="0.01",
    px="50000"
)
print(f"Order placed: {order[0]['ordId']}")

# Get order status
order_status = await trade.get_order(
    inst_id="BTC-USDT",
    ord_id=order[0]['ordId']
)

# Cancel order
cancel_result = await trade.cancel_order(
    inst_id="BTC-USDT",
    ord_id=order[0]['ordId']
)

# Get pending orders
pending = await trade.get_orders_pending()

# Get order history
history = await trade.get_order_history(inst_type="SPOT")

await client.close()
```

#### Account Management

```python
from app.services.okx import OKXClient, OKXAccount

client = OKXClient(
    api_key=settings.OKX_API_KEY,
    secret_key=settings.OKX_SECRET_KEY,
    passphrase=settings.OKX_PASSPHRASE
)
account = OKXAccount(client)

# Get account balance
balance = await account.get_balance()
print(f"Total equity: {balance[0]['totalEq']}")

# Get specific currency balance
btc_balance = await account.get_balance(ccy="BTC")

# Get positions
positions = await account.get_positions()

# Get account configuration
config = await account.get_account_config()

# Get maximum buy/sell amount
max_size = await account.get_max_size(
    inst_id="BTC-USDT",
    td_mode="cash"
)

await client.close()
```

### WebSocket API

#### Public Channels (No Authentication)

```python
from app.services.okx import OKXWebSocket
import asyncio

async def on_message(data):
    """Handle incoming messages"""
    if 'data' in data:
        print(f"Received: {data}")

# Create WebSocket client
ws = OKXWebSocket(on_message=on_message)

# Subscribe to ticker
await ws.subscribe_tickers("BTC-USDT")

# Subscribe to candlesticks
await ws.subscribe_candles("BTC-USDT", bar="1m")

# Subscribe to order book
await ws.subscribe_books("BTC-USDT", channel="books5")

# Subscribe to trades
await ws.subscribe_trades("BTC-USDT")

# Connect (will run until closed)
asyncio.create_task(ws.connect())

# Later: unsubscribe
await ws.unsubscribe_tickers("BTC-USDT")

# Close connection
await ws.close()
```

#### Private Channels (Authentication Required)

```python
from app.services.okx import OKXWebSocket
from app.core.config import settings

async def on_message(data):
    """Handle account updates"""
    print(f"Account update: {data}")

# Create authenticated WebSocket client
ws = OKXWebSocket(
    api_key=settings.OKX_API_KEY,
    secret_key=settings.OKX_SECRET_KEY,
    passphrase=settings.OKX_PASSPHRASE,
    url="wss://ws.okx.com:8443/ws/v5/private",
    on_message=on_message
)

# Subscribe to account updates
await ws.subscribe_account()

# Subscribe to position updates
await ws.subscribe_positions("SWAP")

# Subscribe to order updates
await ws.subscribe_orders("SPOT")

# Connect
asyncio.create_task(ws.connect())
```

#### Advanced WebSocket Usage

```python
async def on_open():
    """Called when connection opens"""
    print("WebSocket connected")

async def on_close():
    """Called when connection closes"""
    print("WebSocket disconnected")

async def on_error(error):
    """Called on error"""
    print(f"WebSocket error: {error}")

ws = OKXWebSocket(
    on_message=on_message,
    on_open=on_open,
    on_close=on_close,
    on_error=on_error
)

# Configure reconnection
ws.set_reconnect(True)
ws.set_reconnect_delay(5)  # 5 seconds

# Connect
await ws.connect()
```

## Error Handling

```python
from app.services.okx import OKXClient, OKXError, OKXRateLimitError

client = OKXClient()

try:
    result = await client.get('/api/v5/market/ticker', params={'instId': 'BTC-USDT'})
except OKXRateLimitError as e:
    print(f"Rate limit exceeded: {e.code} - {e.message}")
    # Wait and retry
except OKXError as e:
    print(f"API error: {e.code} - {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Context Manager Usage

```python
# Automatically closes client
async with OKXClient() as client:
    market = OKXMarket(client)
    ticker = await market.get_ticker("BTC-USDT")
    print(ticker)
# Client is automatically closed here
```

## API Reference

### Market Data Methods

- `get_ticker(inst_id)` - Get ticker for single instrument
- `get_tickers(inst_type, uly)` - Get tickers for multiple instruments
- `get_candles(inst_id, bar, after, before, limit)` - Get candlestick data
- `get_order_book(inst_id, depth)` - Get order book
- `get_trades(inst_id, limit)` - Get recent trades
- `get_instruments(inst_type, uly, inst_id)` - Get instrument info
- `get_funding_rate(inst_id)` - Get funding rate
- `get_mark_price(inst_id, inst_type)` - Get mark price

### Trading Methods

- `place_order(...)` - Place a new order
- `place_multiple_orders(orders)` - Place multiple orders
- `cancel_order(inst_id, ord_id, cl_ord_id)` - Cancel an order
- `cancel_multiple_orders(orders)` - Cancel multiple orders
- `amend_order(...)` - Modify an existing order
- `get_order(inst_id, ord_id, cl_ord_id)` - Get order details
- `get_orders_pending(...)` - Get pending orders
- `get_order_history(...)` - Get order history
- `get_fills(...)` - Get transaction details
- `close_positions(...)` - Close all positions

### Account Methods

- `get_balance(ccy)` - Get account balance
- `get_positions(inst_type, inst_id)` - Get positions
- `get_account_config()` - Get account configuration
- `set_leverage(inst_id, lever, mgn_mode, pos_side)` - Set leverage
- `get_max_size(inst_id, td_mode, ...)` - Get maximum tradable amount
- `get_max_avail_size(inst_id, td_mode, ...)` - Get available amount
- `get_bills(...)` - Get bills/transactions
- `get_max_loan(inst_id, mgn_mode, mgn_ccy)` - Get max loan

### WebSocket Methods

- `subscribe_tickers(inst_id)` - Subscribe to ticker updates
- `subscribe_candles(inst_id, bar)` - Subscribe to candlestick updates
- `subscribe_books(inst_id, channel)` - Subscribe to order book
- `subscribe_trades(inst_id)` - Subscribe to trades
- `subscribe_account(ccy)` - Subscribe to account updates
- `subscribe_positions(inst_type, inst_id)` - Subscribe to positions
- `subscribe_orders(inst_type, inst_id)` - Subscribe to orders
- `unsubscribe_*()` - Corresponding unsubscribe methods

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_okx/ -v
```

## Documentation

- [OKX REST API Documentation](https://www.okx.com/docs-v5/en/#overview-rest-api)
- [OKX WebSocket API Documentation](https://www.okx.com/docs-v5/en/#overview-websocket)

## License

This implementation is part of the AITradeAgent project.
