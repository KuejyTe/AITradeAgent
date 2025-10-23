from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.strategies.engine import strategy_engine
from app.strategies.builtin import (
    SMACrossoverStrategy,
    TrendFollowingStrategy,
    GridTradingStrategy
)


router = APIRouter(prefix="/strategies", tags=["strategies"])


# Register built-in strategies
strategy_engine.register_strategy(SMACrossoverStrategy, "sma_crossover")
strategy_engine.register_strategy(TrendFollowingStrategy, "trend_following")
strategy_engine.register_strategy(GridTradingStrategy, "grid_trading")


# Pydantic models for request/response
class StrategyCreate(BaseModel):
    name: str
    strategy_type: str = Field(..., description="Type of strategy (sma_crossover, trend_following, grid_trading)")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk: Dict[str, Any] = Field(default_factory=dict)


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None


class StrategyResponse(BaseModel):
    id: str
    name: str
    type: str
    is_running: bool
    config: Dict[str, Any]
    parameters: Dict[str, Any]
    state: Dict[str, Any]


class StrategyListResponse(BaseModel):
    strategies: List[StrategyResponse]
    total: int


class MessageResponse(BaseModel):
    message: str
    strategy_id: Optional[str] = None


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(strategy: StrategyCreate):
    """
    Create a new strategy instance.
    
    Args:
        strategy: Strategy configuration
        
    Returns:
        Success message with strategy ID
    """
    # Generate unique strategy ID
    strategy_id = f"{strategy.strategy_type}_{datetime.utcnow().timestamp()}"
    
    # Prepare config
    config = {
        "name": strategy.name,
        "parameters": strategy.parameters,
        "risk": strategy.risk
    }
    
    # Load strategy
    loaded_strategy = strategy_engine.load_strategy(
        strategy_id=strategy_id,
        strategy_type=strategy.strategy_type,
        config=config
    )
    
    if loaded_strategy is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strategy type '{strategy.strategy_type}' not found"
        )
    
    return MessageResponse(
        message="Strategy created successfully",
        strategy_id=strategy_id
    )


@router.get("", response_model=StrategyListResponse)
async def list_strategies():
    """
    List all loaded strategies.
    
    Returns:
        List of all strategies with their details
    """
    strategies_info = strategy_engine.list_strategies()
    
    strategies = [
        StrategyResponse(
            id=info["id"],
            name=info["name"],
            type=info["type"],
            is_running=info["is_running"],
            config=info["config"],
            parameters=info["parameters"],
            state=info["state"]
        )
        for info in strategies_info
    ]
    
    return StrategyListResponse(
        strategies=strategies,
        total=len(strategies)
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: str):
    """
    Get details of a specific strategy.
    
    Args:
        strategy_id: Unique strategy identifier
        
    Returns:
        Strategy details
    """
    info = strategy_engine.get_strategy_info(strategy_id)
    
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found"
        )
    
    return StrategyResponse(
        id=info["id"],
        name=info["name"],
        type=info["type"],
        is_running=info["is_running"],
        config=info["config"],
        parameters=info["parameters"],
        state=info["state"]
    )


@router.put("/{strategy_id}", response_model=MessageResponse)
async def update_strategy(strategy_id: str, update: StrategyUpdate):
    """
    Update strategy configuration.
    
    Args:
        strategy_id: Unique strategy identifier
        update: Updated configuration
        
    Returns:
        Success message
    """
    info = strategy_engine.get_strategy_info(strategy_id)
    
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found"
        )
    
    # Get the strategy instance
    strategy = strategy_engine.running_strategies.get(strategy_id)
    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found"
        )
    
    # Update configuration
    if update.name:
        strategy.name = update.name
        strategy.config["name"] = update.name
    
    if update.parameters:
        strategy.parameters.update(update.parameters)
        strategy.config["parameters"] = strategy.parameters
    
    if update.risk:
        strategy.config["risk"] = update.risk
        # Update risk manager
        from app.strategies.risk import RiskManager
        strategy_engine.risk_managers[strategy_id] = RiskManager(update.risk)
    
    return MessageResponse(
        message="Strategy updated successfully",
        strategy_id=strategy_id
    )


@router.delete("/{strategy_id}", response_model=MessageResponse)
async def delete_strategy(strategy_id: str):
    """
    Delete a strategy.
    
    Args:
        strategy_id: Unique strategy identifier
        
    Returns:
        Success message
    """
    success = strategy_engine.unload_strategy(strategy_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found"
        )
    
    return MessageResponse(
        message="Strategy deleted successfully",
        strategy_id=strategy_id
    )


@router.post("/{strategy_id}/start", response_model=MessageResponse)
async def start_strategy(strategy_id: str):
    """
    Start a strategy.
    
    Args:
        strategy_id: Unique strategy identifier
        
    Returns:
        Success message
    """
    success = strategy_engine.start_strategy(strategy_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found or failed to start"
        )
    
    return MessageResponse(
        message="Strategy started successfully",
        strategy_id=strategy_id
    )


@router.post("/{strategy_id}/stop", response_model=MessageResponse)
async def stop_strategy(strategy_id: str):
    """
    Stop a strategy.
    
    Args:
        strategy_id: Unique strategy identifier
        
    Returns:
        Success message
    """
    success = strategy_engine.stop_strategy(strategy_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found or failed to stop"
        )
    
    return MessageResponse(
        message="Strategy stopped successfully",
        strategy_id=strategy_id
    )


@router.get("/{strategy_id}/signals", response_model=Dict[str, Any])
async def get_strategy_signals(strategy_id: str, limit: int = 50):
    """
    Get recent signals generated by a strategy.
    
    Args:
        strategy_id: Unique strategy identifier
        limit: Maximum number of signals to return
        
    Returns:
        List of recent signals
    """
    if strategy_id not in strategy_engine.running_strategies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found"
        )
    
    # Filter signals by strategy_id
    strategy_signals = [
        {
            "type": signal.type.value,
            "instrument_id": signal.instrument_id,
            "price": str(signal.price),
            "size": str(signal.size),
            "confidence": signal.confidence,
            "timestamp": signal.timestamp.isoformat(),
            "metadata": signal.metadata
        }
        for signal in strategy_engine.signals_history
        if signal.metadata.get("strategy_id") == strategy_id
    ][-limit:]
    
    return {
        "strategy_id": strategy_id,
        "signals": strategy_signals,
        "total": len(strategy_signals)
    }
