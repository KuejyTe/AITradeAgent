from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.market_data import Candle, Ticker
from app.services.data_collector.cache import DataCache
from app.services.data_collector.monitor import DataQualityMonitor
from app.core.config import settings
from app.core.database import get_db


router = APIRouter(prefix="/market", tags=["market_data"])


def get_cache():
    """缓存依赖注入"""
    if not settings.DATA_COLLECTOR_CONFIG.get("cache_enabled"):
        return None
    
    cache = DataCache(redis_url=settings.REDIS_URL)
    return cache


@router.get("/candles")
async def get_candles(
    instrument_id: str = Query(..., description="交易对ID，如 BTC-USDT"),
    bar: str = Query("1m", description="K线周期"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取K线数据
    
    支持的K线周期: 1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 12H, 1D, 1W
    """
    try:
        query = db.query(Candle).filter(
            Candle.instrument_id == instrument_id,
            Candle.bar == bar
        )
        
        if start_time:
            start_ts = int(start_time.timestamp() * 1000)
            query = query.filter(Candle.ts >= start_ts)
        
        if end_time:
            end_ts = int(end_time.timestamp() * 1000)
            query = query.filter(Candle.ts <= end_ts)
        
        candles = query.order_by(Candle.ts.desc()).limit(limit).all()
        
        return {
            "instrument_id": instrument_id,
            "bar": bar,
            "count": len(candles),
            "data": [
                {
                    "ts": candle.ts,
                    "timestamp": datetime.fromtimestamp(candle.ts / 1000).isoformat(),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "vol": candle.vol,
                    "vol_ccy": candle.vol_ccy,
                    "vol_ccy_quote": candle.vol_ccy_quote,
                    "confirm": candle.confirm
                }
                for candle in reversed(candles)
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker")
async def get_ticker(
    instrument_id: str = Query(..., description="交易对ID，如 BTC-USDT"),
    db: Session = Depends(get_db)
):
    """
    获取最新行情
    
    返回指定交易对的最新行情数据
    """
    try:
        ticker = db.query(Ticker).filter(
            Ticker.instrument_id == instrument_id
        ).order_by(Ticker.created_at.desc()).first()
        
        if not ticker:
            raise HTTPException(
                status_code=404,
                detail=f"No ticker data found for {instrument_id}"
            )
        
        return {
            "instrument_id": ticker.instrument_id,
            "last": ticker.last,
            "last_sz": ticker.last_sz,
            "ask_px": ticker.ask_px,
            "ask_sz": ticker.ask_sz,
            "bid_px": ticker.bid_px,
            "bid_sz": ticker.bid_sz,
            "open_24h": ticker.open_24h,
            "high_24h": ticker.high_24h,
            "low_24h": ticker.low_24h,
            "vol_ccy_24h": ticker.vol_ccy_24h,
            "vol_24h": ticker.vol_24h,
            "ts": ticker.ts,
            "timestamp": datetime.fromtimestamp(ticker.ts / 1000).isoformat() if ticker.ts else None,
            "created_at": ticker.created_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instruments")
async def get_instruments():
    """
    获取交易对列表
    
    返回系统支持的所有交易对
    """
    instruments = settings.DATA_COLLECTOR_CONFIG.get("instruments", [])
    candle_bars = settings.DATA_COLLECTOR_CONFIG.get("candle_bars", [])
    
    return {
        "instruments": instruments,
        "candle_bars": candle_bars,
        "count": len(instruments)
    }


@router.get("/stats")
async def get_market_stats(
    instrument_id: str = Query(..., description="交易对ID"),
    bar: Optional[str] = Query(None, description="K线周期"),
    lookback_hours: int = Query(24, ge=1, le=168, description="回溯小时数"),
    db: Session = Depends(get_db)
):
    """
    获取数据统计
    
    返回指定交易对的数据统计信息，包括价格统计、成交量统计等
    """
    try:
        monitor = DataQualityMonitor(db)
        stats = monitor.get_data_stats(
            instrument_id=instrument_id,
            bar=bar,
            lookback_hours=lookback_hours
        )
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/completeness")
async def check_data_completeness(
    instrument_id: str = Query(..., description="交易对ID"),
    bar: str = Query("1m", description="K线周期"),
    lookback_hours: int = Query(24, ge=1, le=168, description="回溯小时数"),
    db: Session = Depends(get_db)
):
    """
    检查数据完整性
    
    检查指定时间范围内的K线数据完整性
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        monitor = DataQualityMonitor(db)
        result = monitor.check_data_completeness(
            instrument_id=instrument_id,
            bar=bar,
            timerange=(start_time, end_time)
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/anomalies")
async def detect_anomalies(
    instrument_id: str = Query(..., description="交易对ID"),
    bar: str = Query("1m", description="K线周期"),
    lookback_hours: int = Query(24, ge=1, le=168, description="回溯小时数"),
    threshold: float = Query(3.0, ge=1.0, le=10.0, description="异常值阈值"),
    db: Session = Depends(get_db)
):
    """
    检测异常数据
    
    检测指定时间范围内的异常K线数据
    """
    try:
        monitor = DataQualityMonitor(db)
        result = monitor.detect_anomalies(
            instrument_id=instrument_id,
            bar=bar,
            lookback_hours=lookback_hours,
            threshold=threshold
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/logs")
async def get_quality_logs(
    instrument_id: Optional[str] = Query(None, description="交易对ID"),
    check_type: Optional[str] = Query(None, description="检查类型"),
    status: Optional[str] = Query(None, description="状态"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取质量检查日志
    
    返回数据质量检查的历史日志
    """
    try:
        monitor = DataQualityMonitor(db)
        logs = monitor.get_quality_logs(
            instrument_id=instrument_id,
            check_type=check_type,
            status=status,
            limit=limit
        )
        
        return {
            "count": len(logs),
            "logs": logs
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats(
    instrument_id: str = Query(..., description="交易对ID")
):
    """
    获取缓存统计信息
    
    返回指定交易对的缓存状态
    """
    try:
        cache = DataCache(redis_url=settings.REDIS_URL)
        await cache.connect()
        
        stats = await cache.get_cache_stats(instrument_id)
        
        await cache.close()
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear")
async def clear_cache(
    instrument_id: Optional[str] = Query(None, description="交易对ID，不提供则清除所有缓存")
):
    """
    清除缓存
    
    清除指定交易对或所有交易对的缓存数据
    """
    try:
        cache = DataCache(redis_url=settings.REDIS_URL)
        await cache.connect()
        
        await cache.clear_cache(instrument_id)
        
        await cache.close()
        
        return {
            "message": f"Cache cleared for {instrument_id}" if instrument_id else "All cache cleared"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
