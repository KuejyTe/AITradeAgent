"""
Example usage of the Trading Execution System

This file demonstrates how to use the trading execution components.
"""

import asyncio
from decimal import Decimal
from datetime import datetime, timedelta

from app.core.database import get_session_local
from app.core.config import settings
from app.services.okx.client import OKXClient
from app.services.okx.trade import OKXTrade
from app.services.okx.account import OKXAccount
from app.services.trading import (
    TradeExecutor,
    OrderManager,
    PositionManager,
    OrderTracker,
    ExecutionRiskControl,
    TradeRecorder,
    OrderParams,
)
from app.services.trading.execution_strategies import (
    MarketExecution,
    LimitExecution,
    TWAPExecution,
    IcebergExecution,
)
from app.models.trading import OrderSide, OrderType
from app.strategies.signals import Signal, SignalType
from app.strategies.models import Account


async def example_basic_order():
    """Example: Place a basic market order"""
    print("\n=== Example: Basic Market Order ===\n")
    
    # Initialize components
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    okx_client = OKXClient(
        api_key=settings.OKX_API_KEY,
        secret_key=settings.OKX_SECRET_KEY,
        passphrase=settings.OKX_PASSPHRASE,
    )
    okx_client.trade = OKXTrade(okx_client)
    
    order_manager = OrderManager(db)
    risk_control = ExecutionRiskControl()
    order_tracker = OrderTracker(okx_client, order_manager)
    
    executor = TradeExecutor(
        okx_client=okx_client,
        order_manager=order_manager,
        risk_manager=risk_control,
        order_tracker=order_tracker
    )
    
    # Create order parameters
    order_params = OrderParams(
        instrument_id="BTC-USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        size=Decimal("0.001"),  # Small size for testing
        trade_mode="cash"
    )
    
    try:
        # Place order
        order = await executor.place_order(order_params)
        print(f"Order placed: ID={order.id}, Status={order.status}")
        
        # Wait a bit for order to process
        await asyncio.sleep(3)
        
        # Check order status
        updated_order = order_manager.get_order(order.id)
        print(f"Order updated: Status={updated_order.status}, Filled={updated_order.filled_size}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        await okx_client.close()
        db.close()


async def example_signal_execution():
    """Example: Execute a trading signal"""
    print("\n=== Example: Signal Execution ===\n")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    okx_client = OKXClient(
        api_key=settings.OKX_API_KEY,
        secret_key=settings.OKX_SECRET_KEY,
        passphrase=settings.OKX_PASSPHRASE,
    )
    okx_client.trade = OKXTrade(okx_client)
    
    order_manager = OrderManager(db)
    risk_control = ExecutionRiskControl()
    
    executor = TradeExecutor(
        okx_client=okx_client,
        order_manager=order_manager,
        risk_manager=risk_control
    )
    
    # Create trading signal
    signal = Signal(
        type=SignalType.BUY,
        instrument_id="BTC-USDT",
        price=Decimal("50000"),
        size=Decimal("0.001"),
        confidence=0.85,
        metadata={"strategy": "example", "reason": "demo"}
    )
    
    # Create account state
    account = Account(
        balance=Decimal("10000"),
        equity=Decimal("10000"),
        available_balance=Decimal("10000"),
        positions=[],
        daily_pnl=Decimal("0"),
        total_pnl=Decimal("0"),
        margin_used=Decimal("0")
    )
    
    try:
        # Execute signal
        order = await executor.execute_signal(signal, account, strategy_id="example_strategy")
        print(f"Signal executed: Order ID={order.id}, Status={order.status}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        await okx_client.close()
        db.close()


async def example_limit_order_with_strategy():
    """Example: Use limit execution strategy with timeout"""
    print("\n=== Example: Limit Order Strategy ===\n")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    okx_client = OKXClient(
        api_key=settings.OKX_API_KEY,
        secret_key=settings.OKX_SECRET_KEY,
        passphrase=settings.OKX_PASSPHRASE,
    )
    okx_client.trade = OKXTrade(okx_client)
    
    order_manager = OrderManager(db)
    risk_control = ExecutionRiskControl()
    
    executor = TradeExecutor(
        okx_client=okx_client,
        order_manager=order_manager,
        risk_manager=risk_control
    )
    
    # Configure limit execution strategy
    limit_config = {
        'timeout': 30,  # 30 seconds timeout
        'fallback_to_market': True  # Fall back to market if not filled
    }
    
    limit_strategy = LimitExecution(executor, limit_config)
    
    # Create order parameters
    order_params = OrderParams(
        instrument_id="BTC-USDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        size=Decimal("0.001"),
        price=Decimal("48000"),  # Below market for testing timeout
        trade_mode="cash"
    )
    
    try:
        # Execute with strategy
        orders = await limit_strategy.execute(order_params)
        print(f"Limit strategy executed: {len(orders)} orders placed")
        for order in orders:
            print(f"  Order ID={order.id}, Type={order.order_type}, Status={order.status}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        await okx_client.close()
        db.close()


async def example_twap_execution():
    """Example: TWAP execution for large orders"""
    print("\n=== Example: TWAP Execution ===\n")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    okx_client = OKXClient(
        api_key=settings.OKX_API_KEY,
        secret_key=settings.OKX_SECRET_KEY,
        passphrase=settings.OKX_PASSPHRASE,
    )
    okx_client.trade = OKXTrade(okx_client)
    
    order_manager = OrderManager(db)
    risk_control = ExecutionRiskControl()
    
    executor = TradeExecutor(
        okx_client=okx_client,
        order_manager=order_manager,
        risk_manager=risk_control
    )
    
    # Configure TWAP strategy
    twap_config = {
        'duration': 60,  # 1 minute
        'num_slices': 5,  # 5 slices
        'use_limit_orders': False
    }
    
    twap_strategy = TWAPExecution(executor, twap_config)
    
    # Create order parameters for large order
    order_params = OrderParams(
        instrument_id="BTC-USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        size=Decimal("0.005"),  # Will be split into 5 orders
        trade_mode="cash"
    )
    
    try:
        # Execute TWAP
        print("Starting TWAP execution...")
        orders = await twap_strategy.execute(order_params)
        print(f"TWAP completed: {len(orders)} orders placed")
        
        for i, order in enumerate(orders):
            print(f"  Slice {i+1}: ID={order.id}, Size={order.size}, Status={order.status}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        await okx_client.close()
        db.close()


async def example_position_tracking():
    """Example: Track positions and PnL"""
    print("\n=== Example: Position Tracking ===\n")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    position_manager = PositionManager(db)
    
    try:
        # Get all positions
        positions = position_manager.get_all_positions()
        print(f"Total positions: {len(positions)}")
        
        for position in positions:
            print(f"\nPosition: {position.instrument_id}")
            print(f"  Side: {position.side}")
            print(f"  Size: {position.size}")
            print(f"  Entry: {position.entry_price}")
            print(f"  Current: {position.current_price}")
            print(f"  Unrealized PnL: {position.unrealized_pnl}")
            print(f"  Realized PnL: {position.realized_pnl}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        db.close()


async def example_performance_analysis():
    """Example: Analyze trading performance"""
    print("\n=== Example: Performance Analysis ===\n")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    trade_recorder = TradeRecorder(db)
    
    try:
        # Get performance for last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        metrics = trade_recorder.calculate_performance(
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"Performance Metrics ({start_date.date()} to {end_date.date()}):")
        print(f"  Total Trades: {metrics.total_trades}")
        print(f"  Winning Trades: {metrics.winning_trades}")
        print(f"  Losing Trades: {metrics.losing_trades}")
        print(f"  Win Rate: {metrics.win_rate:.2%}")
        print(f"  Total PnL: {metrics.total_pnl}")
        print(f"  Total Return: {metrics.total_return_pct:.2f}%")
        print(f"  Average Win: {metrics.average_win}")
        print(f"  Average Loss: {metrics.average_loss}")
        print(f"  Profit Factor: {metrics.profit_factor:.2f}")
        print(f"  Max Drawdown: {metrics.max_drawdown} ({metrics.max_drawdown_pct:.2f}%)")
        
        if metrics.sharpe_ratio:
            print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        if metrics.sortino_ratio:
            print(f"  Sortino Ratio: {metrics.sortino_ratio:.2f}")
        
        # Get trade statistics
        stats = trade_recorder.get_trade_statistics()
        print(f"\nTrade Statistics:")
        print(f"  Total Trades: {stats['total_trades']}")
        print(f"  Total Volume: ${stats['total_volume']:,.2f}")
        print(f"  Total Fees: ${stats['total_fees']:,.2f}")
        print(f"  Average Trade Size: {stats['avg_trade_size']:.4f}")
        print(f"  Instruments: {', '.join(stats['instruments'])}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        db.close()


async def main():
    """Run all examples"""
    print("=" * 60)
    print("Trading Execution System Examples")
    print("=" * 60)
    
    # Note: These examples require valid OKX credentials
    # Uncomment the examples you want to run
    
    # await example_basic_order()
    # await example_signal_execution()
    # await example_limit_order_with_strategy()
    # await example_twap_execution()
    await example_position_tracking()
    await example_performance_analysis()
    
    print("\n" + "=" * 60)
    print("Examples completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
