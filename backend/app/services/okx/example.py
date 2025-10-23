"""
Example usage of OKX API client
This script demonstrates how to use the OKX REST and WebSocket clients
"""

import asyncio
from app.services.okx import OKXClient, OKXMarket, OKXAccount, OKXTrade, OKXWebSocket
from app.core.config import settings


async def example_market_data():
    """Example: Fetch market data (no authentication required)"""
    print("\n=== Market Data Example ===\n")

    async with OKXClient() as client:
        market = OKXMarket(client)

        print("1. Getting BTC-USDT ticker...")
        ticker = await market.get_ticker("BTC-USDT")
        if ticker:
            print(f"   Last price: {ticker[0].get('last')}")
            print(f"   24h Volume: {ticker[0].get('vol24h')}")

        print("\n2. Getting candlestick data (last 5 candles)...")
        candles = await market.get_candles("BTC-USDT", bar="1H", limit=5)
        if candles:
            for i, candle in enumerate(candles[:3]):
                print(f"   Candle {i+1}: O={candle[1]} H={candle[2]} L={candle[3]} C={candle[4]}")

        print("\n3. Getting order book...")
        order_book = await market.get_order_book("BTC-USDT", depth=5)
        if order_book:
            print(f"   Best ask: {order_book[0]['asks'][0] if order_book[0].get('asks') else 'N/A'}")
            print(f"   Best bid: {order_book[0]['bids'][0] if order_book[0].get('bids') else 'N/A'}")

        print("\n4. Getting recent trades...")
        trades = await market.get_trades("BTC-USDT", limit=3)
        if trades:
            for i, trade in enumerate(trades[:3]):
                print(f"   Trade {i+1}: Price={trade.get('px')} Size={trade.get('sz')} Side={trade.get('side')}")

        print("\n5. Getting SPOT instruments...")
        instruments = await market.get_instruments("SPOT", inst_id="BTC-USDT")
        if instruments:
            inst = instruments[0]
            print(f"   Instrument: {inst.get('instId')}")
            print(f"   Base currency: {inst.get('baseCcy')}")
            print(f"   Quote currency: {inst.get('quoteCcy')}")
            print(f"   Min size: {inst.get('minSz')}")


async def example_account_info():
    """Example: Fetch account information (requires authentication)"""
    print("\n=== Account Information Example ===\n")

    if not settings.OKX_API_KEY:
        print("⚠️  API credentials not configured. Skipping account examples.")
        return

    async with OKXClient(
        api_key=settings.OKX_API_KEY,
        secret_key=settings.OKX_SECRET_KEY,
        passphrase=settings.OKX_PASSPHRASE
    ) as client:
        account = OKXAccount(client)

        try:
            print("1. Getting account balance...")
            balance = await account.get_balance()
            if balance:
                print(f"   Total equity: {balance[0].get('totalEq', 'N/A')}")
                details = balance[0].get('details', [])
                for detail in details[:5]:
                    print(f"   {detail.get('ccy')}: Available={detail.get('availBal')} Frozen={detail.get('frozenBal')}")

            print("\n2. Getting account configuration...")
            config = await account.get_account_config()
            if config:
                print(f"   Account level: {config[0].get('acctLv')}")
                print(f"   Position mode: {config[0].get('posMode')}")

            print("\n3. Getting positions...")
            positions = await account.get_positions()
            if positions:
                print(f"   Number of open positions: {len(positions)}")
                for pos in positions[:3]:
                    print(f"   Position: {pos.get('instId')} Size={pos.get('pos')} PnL={pos.get('upl')}")
            else:
                print("   No open positions")

        except Exception as e:
            print(f"   Error: {e}")


async def example_trading():
    """Example: Trading operations (requires authentication)"""
    print("\n=== Trading Example ===\n")

    if not settings.OKX_API_KEY:
        print("⚠️  API credentials not configured. Skipping trading examples.")
        return

    async with OKXClient(
        api_key=settings.OKX_API_KEY,
        secret_key=settings.OKX_SECRET_KEY,
        passphrase=settings.OKX_PASSPHRASE
    ) as client:
        trade = OKXTrade(client)

        try:
            print("1. Getting pending orders...")
            pending_orders = await trade.get_orders_pending(inst_type="SPOT")
            if pending_orders:
                print(f"   Number of pending orders: {len(pending_orders)}")
                for order in pending_orders[:3]:
                    print(f"   Order: {order.get('instId')} {order.get('side')} {order.get('sz')}@{order.get('px')}")
            else:
                print("   No pending orders")

            print("\n2. Getting order history...")
            history = await trade.get_order_history(inst_type="SPOT", limit=5)
            if history:
                print(f"   Number of historical orders: {len(history)}")
                for order in history[:3]:
                    print(f"   Order: {order.get('instId')} {order.get('side')} State={order.get('state')}")
            else:
                print("   No order history")

            print("\n3. Getting fills...")
            fills = await trade.get_fills(inst_type="SPOT", limit=5)
            if fills:
                print(f"   Number of fills: {len(fills)}")
                for fill in fills[:3]:
                    print(f"   Fill: {fill.get('instId')} {fill.get('side')} {fill.get('fillSz')}@{fill.get('fillPx')}")
            else:
                print("   No recent fills")

        except Exception as e:
            print(f"   Error: {e}")


async def example_websocket():
    """Example: WebSocket real-time data"""
    print("\n=== WebSocket Example ===\n")

    message_count = 0
    max_messages = 10

    async def on_message(data):
        """Handle incoming WebSocket messages"""
        nonlocal message_count
        message_count += 1

        if 'arg' in data:
            channel = data['arg'].get('channel')
            inst_id = data['arg'].get('instId', '')
            print(f"Received message from {channel} {inst_id}")

            if 'data' in data and data['data']:
                item = data['data'][0]
                if channel == 'tickers':
                    print(f"  Ticker: Last={item.get('last')} Vol={item.get('vol24h')}")
                elif channel.startswith('candle'):
                    print(f"  Candle: O={item.get('o')} H={item.get('h')} L={item.get('l')} C={item.get('c')}")
                elif channel == 'trades':
                    print(f"  Trade: Price={item.get('px')} Size={item.get('sz')} Side={item.get('side')}")

        if message_count >= max_messages:
            print(f"\nReceived {max_messages} messages, closing connection...")
            await ws.close()

    async def on_open():
        print("WebSocket connected")

    async def on_close():
        print("WebSocket disconnected")

    async def on_error(error):
        print(f"WebSocket error: {error}")

    ws = OKXWebSocket(
        on_message=on_message,
        on_open=on_open,
        on_close=on_close,
        on_error=on_error
    )

    print("Subscribing to channels...")
    await ws.subscribe_tickers("BTC-USDT")
    await ws.subscribe_candles("BTC-USDT", bar="1m")
    await ws.subscribe_trades("BTC-USDT")

    print(f"Listening for {max_messages} messages...")
    await ws.connect()


async def main():
    """Run all examples"""
    print("=" * 60)
    print("OKX API Client Examples")
    print("=" * 60)

    try:
        await example_market_data()
        await example_account_info()
        await example_trading()
        await example_websocket()
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Examples completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
