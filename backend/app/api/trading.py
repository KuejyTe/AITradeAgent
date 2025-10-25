from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.core.config import settings
from app.core.security import APIKeyManager, SecureStorage
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
    OrderResponse,
    TradeResponse,
    PositionResponse,
    PerformanceMetrics,
)
from app.models.trading import OrderStatus, OrderSide

router = APIRouter(prefix="/trading", tags=["trading"])


def _resolve_okx_credentials() -> tuple[Optional[str], Optional[str], Optional[str]]:
    if all(
        (
            settings.OKX_API_KEY,
            settings.OKX_SECRET_KEY,
            settings.OKX_PASSPHRASE,
        )
    ):
        return settings.OKX_API_KEY, settings.OKX_SECRET_KEY, settings.OKX_PASSPHRASE

    try:
        storage = SecureStorage()
        manager = APIKeyManager(storage)
        stored = manager.get_api_keys()
    except ValueError:
        stored = {}

    if stored:
        return (
            stored.get("api_key"),
            stored.get("secret_key"),
            stored.get("passphrase"),
        )

    return None, None, None


def get_okx_client():
    """Get OKX client instance"""
    api_key, secret_key, passphrase = _resolve_okx_credentials()
    return OKXClient(
        api_key=api_key,
        secret_key=secret_key,
        passphrase=passphrase,
    )


def get_trade_executor(db: Session = Depends(get_db)):
    """Get TradeExecutor instance"""
    okx_client = get_okx_client()
    okx_client.trade = OKXTrade(okx_client)
    okx_client.account = OKXAccount(okx_client)
    
    order_manager = OrderManager(db)
    risk_control = ExecutionRiskControl()
    order_tracker = OrderTracker(okx_client, order_manager)
    
    return TradeExecutor(
        okx_client=okx_client,
        order_manager=order_manager,
        risk_manager=risk_control,
        order_tracker=order_tracker
    )


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order_params: OrderParams,
    executor: TradeExecutor = Depends(get_trade_executor)
):
    """
    Create and place a new order
    
    Args:
        order_params: Order parameters
        
    Returns:
        Created order details
    """
    try:
        order = await executor.place_order(order_params)
        return executor.order_manager.to_response(order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    instrument_id: Optional[str] = None,
    status: Optional[str] = None,
    side: Optional[str] = None,
    strategy_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get orders with optional filters
    
    Args:
        instrument_id: Filter by instrument
        status: Filter by status
        side: Filter by side (buy/sell)
        strategy_id: Filter by strategy
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum results
        offset: Pagination offset
        
    Returns:
        List of orders
    """
    order_manager = OrderManager(db)
    
    filters = {}
    if instrument_id:
        filters['instrument_id'] = instrument_id
    if status:
        filters['status'] = OrderStatus(status)
    if side:
        filters['side'] = OrderSide(side)
    if strategy_id:
        filters['strategy_id'] = strategy_id
    if start_date:
        filters['start_date'] = start_date
    if end_date:
        filters['end_date'] = end_date
    
    orders = order_manager.get_order_history(filters, limit=limit, offset=offset)
    return [order_manager.to_response(order) for order in orders]


@router.get("/orders/active", response_model=List[OrderResponse])
async def get_active_orders(
    instrument_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all active orders
    
    Args:
        instrument_id: Filter by instrument
        
    Returns:
        List of active orders
    """
    order_manager = OrderManager(db)
    orders = order_manager.get_active_orders(instrument_id)
    return [order_manager.to_response(order) for order in orders]


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """
    Get order details by ID
    
    Args:
        order_id: Order ID
        
    Returns:
        Order details
    """
    order_manager = OrderManager(db)
    order = order_manager.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order_manager.to_response(order)


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: int,
    executor: TradeExecutor = Depends(get_trade_executor)
):
    """
    Cancel an order
    
    Args:
        order_id: Order ID
        
    Returns:
        Cancellation status
    """
    try:
        success = await executor.cancel_order(order_id)
        if success:
            return {"status": "success", "message": f"Order {order_id} cancelled"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel order")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    include_closed: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all positions
    
    Args:
        include_closed: Include closed positions
        
    Returns:
        List of positions
    """
    position_manager = PositionManager(db)
    positions = position_manager.get_all_positions(include_closed)
    return [position_manager.to_response(pos) for pos in positions]


@router.get("/positions/{instrument_id}", response_model=PositionResponse)
async def get_position(
    instrument_id: str,
    db: Session = Depends(get_db)
):
    """
    Get position for an instrument
    
    Args:
        instrument_id: Instrument ID
        
    Returns:
        Position details
    """
    position_manager = PositionManager(db)
    position = position_manager.get_position(instrument_id)
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    return position_manager.to_response(position)


@router.post("/positions/sync")
async def sync_positions(
    executor: TradeExecutor = Depends(get_trade_executor),
    db: Session = Depends(get_db)
):
    """
    Synchronize positions with exchange
    
    Returns:
        Sync status
    """
    try:
        position_manager = PositionManager(db)
        await position_manager.sync_positions_with_exchange(executor.okx_client.account)
        return {"status": "success", "message": "Positions synchronized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    instrument_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    strategy_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get trade executions
    
    Args:
        instrument_id: Filter by instrument
        start_date: Filter by start date
        end_date: Filter by end date
        strategy_id: Filter by strategy
        limit: Maximum results
        offset: Pagination offset
        
    Returns:
        List of trades
    """
    trade_recorder = TradeRecorder(db)
    trades = trade_recorder.get_trades(
        instrument_id=instrument_id,
        start_date=start_date,
        end_date=end_date,
        strategy_id=strategy_id,
        limit=limit,
        offset=offset
    )
    return [trade_recorder.to_response(trade) for trade in trades]


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    instrument_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get trading performance metrics
    
    Args:
        start_date: Start date (default: 30 days ago)
        end_date: End date (default: now)
        instrument_id: Filter by instrument
        strategy_id: Filter by strategy
        
    Returns:
        Performance metrics
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    trade_recorder = TradeRecorder(db)
    metrics = trade_recorder.calculate_performance(
        start_date=start_date,
        end_date=end_date,
        instrument_id=instrument_id,
        strategy_id=strategy_id
    )
    
    return metrics


@router.get("/statistics")
async def get_statistics(
    instrument_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get trade statistics
    
    Args:
        instrument_id: Filter by instrument
        strategy_id: Filter by strategy
        
    Returns:
        Trade statistics
    """
    trade_recorder = TradeRecorder(db)
    stats = trade_recorder.get_trade_statistics(
        instrument_id=instrument_id,
        strategy_id=strategy_id
    )
    
    return stats
