# 数据采集服务 (Data Collector Service)

实时市场数据采集服务，通过WebSocket获取行情并存储到数据库。

## 功能特性

### 1. WebSocket 实时数据采集
- 实时行情 (Ticker) 订阅
- K线数据 (Candles) 订阅，支持多种时间周期
- 订单簿 (Order Book) 订阅
- 自动断线重连
- 数据自动保存到数据库

### 2. 历史数据采集
- REST API 历史K线数据获取
- 分批请求，避免API限制
- 智能回填缺失数据
- 检测并填补数据缺口

### 3. 数据处理管道
- 数据清洗：去除异常值
- 数据归一化：MinMax 和 Z-Score
- 技术指标计算：MA, EMA, MACD, RSI等
- 数据验证：检查数据完整性和有效性

### 4. 数据缓存
- Redis 缓存最新数据
- 滑动窗口缓存（如最近1000条K线）
- 快速查询接口
- 缓存统计信息

### 5. 数据质量监控
- 数据完整性检查
- 异常数据检测
- 数据统计信息
- 质量检查日志

### 6. 事件通知系统
- 观察者模式实现
- 支持多种事件类型
- 异步事件处理
- 供策略引擎订阅

### 7. 后台任务
- 定时同步历史数据
- 定时清理过期数据
- 定时数据完整性检查
- 手动触发同步和检查

## 目录结构

```
data_collector/
├── __init__.py                 # 模块导出
├── websocket_collector.py      # WebSocket实时数据采集器
├── historical_collector.py     # 历史数据采集器
├── pipeline.py                 # 数据处理管道
├── cache.py                    # Redis缓存服务
├── monitor.py                  # 数据质量监控
├── tasks.py                    # 后台任务
├── events.py                   # 事件通知系统
├── example.py                  # 使用示例
└── README.md                   # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

在 `config.py` 中配置：

```python
DATA_COLLECTOR_CONFIG = {
    "instruments": ["BTC-USDT", "ETH-USDT", "BNB-USDT"],
    "candle_bars": ["1m", "5m", "15m", "1H", "1D"],
    "enable_order_book": True,
    "cache_enabled": True,
    "retention_days": 90
}

REDIS_URL = "redis://localhost:6379"
DATABASE_URL = "sqlite:///./data.db"
```

### 3. WebSocket 实时数据采集

```python
from app.services.data_collector import MarketDataCollector

collector = MarketDataCollector(okx_client, db_session)
await collector.start()

# 订阅行情
await collector.subscribe_ticker(["BTC-USDT", "ETH-USDT"])

# 订阅K线
await collector.subscribe_candles(["BTC-USDT"], "1m")

# 订阅订单簿
await collector.subscribe_order_book(["BTC-USDT"])
```

### 4. 历史数据采集

```python
from app.services.data_collector import HistoricalDataCollector

collector = HistoricalDataCollector(okx_client, db_session)

# 获取历史K线
await collector.fetch_historical_candles(
    instrument_id="BTC-USDT",
    bar="1H",
    start_time=start_time,
    end_time=end_time
)

# 回填缺失数据
await collector.backfill_missing_data(
    instrument_id="BTC-USDT",
    bar="1H",
    lookback_days=30
)
```

### 5. 数据处理管道

```python
from app.services.data_collector import DataPipeline
from app.services.data_collector.pipeline import (
    DataCleaningProcessor,
    TechnicalIndicatorProcessor
)

pipeline = DataPipeline()
pipeline.add_processor(DataCleaningProcessor())
pipeline.add_processor(TechnicalIndicatorProcessor())

result = await pipeline.process(raw_data)
```

### 6. 数据缓存

```python
from app.services.data_collector import DataCache

cache = DataCache(redis_url="redis://localhost:6379")
await cache.connect()

# 缓存行情
await cache.set_ticker("BTC-USDT", ticker_data)

# 缓存K线
await cache.push_candle("BTC-USDT", "1m", candle_data)

# 获取缓存
ticker = await cache.get_ticker("BTC-USDT")
candles = await cache.get_candles("BTC-USDT", "1m", limit=100)
```

### 7. 事件订阅

```python
from app.services.data_collector import event_bus, EventType

async def on_ticker_update(event):
    print(f"新行情: {event.data}")

event_bus.subscribe(on_ticker_update, [EventType.TICKER_UPDATE])
await event_bus.start()
```

## API 端点

### 获取K线数据
```
GET /api/v1/market/candles
Parameters:
  - instrument_id: 交易对ID
  - bar: K线周期 (1m, 5m, 15m, 1H, 1D)
  - start_time: 开始时间 (可选)
  - end_time: 结束时间 (可选)
  - limit: 返回数量 (默认100)
```

### 获取最新行情
```
GET /api/v1/market/ticker
Parameters:
  - instrument_id: 交易对ID
```

### 获取交易对列表
```
GET /api/v1/market/instruments
```

### 获取数据统计
```
GET /api/v1/market/stats
Parameters:
  - instrument_id: 交易对ID
  - bar: K线周期 (可选)
  - lookback_hours: 回溯小时数 (默认24)
```

### 检查数据完整性
```
GET /api/v1/market/quality/completeness
Parameters:
  - instrument_id: 交易对ID
  - bar: K线周期
  - lookback_hours: 回溯小时数
```

### 检测异常数据
```
GET /api/v1/market/quality/anomalies
Parameters:
  - instrument_id: 交易对ID
  - bar: K线周期
  - lookback_hours: 回溯小时数
  - threshold: 异常值阈值
```

## 数据模型

### Ticker (行情)
- instrument_id: 交易对ID
- last: 最新成交价
- bid_px/ask_px: 买一价/卖一价
- vol_24h: 24小时成交量
- ts: 时间戳

### Candle (K线)
- instrument_id: 交易对ID
- bar: K线周期
- ts: K线开始时间戳
- open/high/low/close: 开高低收
- vol: 交易量
- confirm: 是否确认

### OrderBook (订单簿)
- instrument_id: 交易对ID
- asks: 卖单列表
- bids: 买单列表
- ts: 时间戳

## 技术指标

支持的技术指标：
- MA (Moving Average): 5, 10, 20, 50 周期
- EMA (Exponential Moving Average): 5, 10, 20 周期
- MACD (Moving Average Convergence Divergence)
- RSI (Relative Strength Index): 14 周期

## 配置选项

| 配置项 | 说明 | 默认值 |
|-------|------|--------|
| instruments | 要采集的交易对列表 | ["BTC-USDT", "ETH-USDT"] |
| candle_bars | K线周期列表 | ["1m", "5m", "15m", "1H", "1D"] |
| enable_order_book | 是否启用订单簿采集 | True |
| cache_enabled | 是否启用缓存 | True |
| retention_days | 数据保留天数 | 90 |

## 测试

运行测试：

```bash
pytest tests/test_data_collector.py -v
```

## 性能优化建议

1. **数据库优化**
   - 为 instrument_id, bar, ts 创建联合索引
   - 定期清理过期数据
   - 考虑使用时序数据库 (如 TimescaleDB)

2. **缓存优化**
   - 合理设置缓存过期时间
   - 使用Redis集群提高可用性
   - 控制滑动窗口大小

3. **采集优化**
   - 控制订阅数量，避免超过WebSocket限制
   - 合理设置历史数据批次大小
   - 使用连接池管理数据库连接

## 故障处理

### WebSocket断连
- 自动重连机制
- 重连后自动重新订阅
- 连接状态监控

### 数据缺失
- 自动检测数据缺口
- 定时任务自动回填
- 手动触发补充功能

### 异常数据
- 自动检测异常值
- 记录质量检查日志
- 告警通知机制

## 监控指标

建议监控的指标：
- WebSocket连接状态
- 数据接收速率
- 数据库写入性能
- 缓存命中率
- 数据完整性比率
- 异常数据比率

## 示例代码

查看 `example.py` 获取完整的使用示例。

## 许可证

MIT License
