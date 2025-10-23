# OKX API Integration - Quick Start Guide

## Installation

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```env
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
```

## Verification

Run the verification script to ensure everything is working:
```bash
python verify_okx_integration.py
```

Run the test suite:
```bash
pytest tests/test_okx/ -v
```

## Basic Usage

### 1. Get Market Data (No Authentication Required)

```python
import asyncio
from app.services.okx import OKXClient, OKXMarket

async def get_market_data():
    async with OKXClient() as client:
        market = OKXMarket(client)
        
        # Get ticker
        ticker = await market.get_ticker("BTC-USDT")
        print(f"BTC-USDT Price: {ticker[0]['last']}")
        
        # Get candlestick data
        candles = await market.get_candles("BTC-USDT", bar="1H", limit=10)
        print(f"Latest candles: {len(candles)} candles")
        
        # Get order book
        order_book = await market.get_order_book("BTC-USDT", depth=10)
        print(f"Order book: {len(order_book[0]['asks'])} asks, {len(order_book[0]['bids'])} bids")

asyncio.run(get_market_data())
```

### 2. Check Account Balance (Authentication Required)

```python
import asyncio
from app.services.okx import OKXClient, OKXAccount
from app.core.config import settings

async def check_balance():
    async with OKXClient(
        api_key=settings.OKX_API_KEY,
        secret_key=settings.OKX_SECRET_KEY,
        passphrase=settings.OKX_PASSPHRASE
    ) as client:
        account = OKXAccount(client)
        
        # Get balance
        balance = await account.get_balance()
        print(f"Total Equity: {balance[0].get('totalEq', 'N/A')}")
        
        # Get positions
        positions = await account.get_positions()
        print(f"Open positions: {len(positions)}")

asyncio.run(check_balance())
```

### 3. Place a Trade (Authentication Required)

```python
import asyncio
from app.services.okx import OKXClient, OKXTrade
from app.core.config import settings

async def place_trade():
    async with OKXClient(
        api_key=settings.OKX_API_KEY,
        secret_key=settings.OKX_SECRET_KEY,
        passphrase=settings.OKX_PASSPHRASE
    ) as client:
        trade = OKXTrade(client)
        
        # Place a limit order
        order = await trade.place_order(
            inst_id="BTC-USDT",
            td_mode="cash",
            side="buy",
            ord_type="limit",
            sz="0.001",  # Small amount for testing
            px="50000"   # Price
        )
        
        if order:
            print(f"Order placed successfully!")
            print(f"Order ID: {order[0].get('ordId')}")
            
            # Check order status
            order_status = await trade.get_order(
                inst_id="BTC-USDT",
                ord_id=order[0]['ordId']
            )
            print(f"Order status: {order_status[0].get('state')}")

# asyncio.run(place_trade())  # Uncomment to run
```

### 4. WebSocket Real-time Data

```python
import asyncio
from app.services.okx import OKXWebSocket

async def stream_market_data():
    message_count = 0
    
    async def on_message(data):
        nonlocal message_count
        message_count += 1
        
        if 'data' in data and data['data']:
            channel = data['arg'].get('channel')
            item = data['data'][0]
            
            if channel == 'tickers':
                print(f"Ticker Update: {item.get('instId')} - Price: {item.get('last')}")
            elif channel == 'trades':
                print(f"Trade: {item.get('side')} {item.get('sz')} @ {item.get('px')}")
        
        # Stop after 10 messages
        if message_count >= 10:
            await ws.close()
    
    ws = OKXWebSocket(on_message=on_message)
    
    # Subscribe to channels
    await ws.subscribe_tickers("BTC-USDT")
    await ws.subscribe_trades("BTC-USDT")
    
    # Connect and listen
    await ws.connect()

asyncio.run(stream_market_data())
```

## Example Scripts

Run the comprehensive example:
```bash
cd backend/app/services/okx
python example.py
```

This will demonstrate:
- Market data fetching
- Account information retrieval
- Trading operations
- WebSocket streaming

## Documentation

For detailed documentation, see:
- `backend/app/services/okx/README.md` - Complete API documentation
- `OKX_INTEGRATION_SUMMARY.md` - Implementation summary
- Test files in `backend/tests/test_okx/` - Usage examples

## API Endpoints

### Market Data (Public)
- Get ticker/tickers
- Get candlesticks
- Get order book
- Get trades
- Get instruments
- Get funding rates

### Account (Private)
- Get balance
- Get positions
- Get account config
- Set leverage
- Get max tradable size

### Trading (Private)
- Place/cancel orders
- Batch operations
- Modify orders
- Query orders
- Get order history
- Get fills

### WebSocket
- Public: tickers, candles, books, trades
- Private: account, positions, orders

## Error Handling

```python
from app.services.okx.client import OKXError, OKXRateLimitError

try:
    result = await market.get_ticker("BTC-USDT")
except OKXRateLimitError as e:
    print(f"Rate limit: {e.code} - {e.message}")
except OKXError as e:
    print(f"API error: {e.code} - {e.message}")
```

## Support

For issues or questions:
1. Check the API documentation: https://www.okx.com/docs-v5/en/
2. Review test files for usage examples
3. Check the README.md for detailed information
