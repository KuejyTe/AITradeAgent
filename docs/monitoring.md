# 监控与可观测性指南

本指南涵盖系统日志、性能指标、告警配置以及常见故障排查流程，帮助运维与开发团队快速定位问题、进行容量规划并确保系统稳定运行。

## 日志查看指南

### 日志分类

| 日志类别 | 文件位置 | 说明 |
| --- | --- | --- |
| 应用日志 | `logs/app.log` | 核心服务运行记录、启动信息、业务关键事件 |
| API 请求日志 | `logs/api.log` | 接口请求与响应日志，包含状态码、耗时、客户端 IP 等信息 |
| 交易日志 | `logs/trading.log` | 交易执行、委托、成交相关操作记录 |
| 策略日志 | `logs/strategy.log` | 策略调度、信号生成与策略异常 |
| 错误日志 | `logs/error.log` | 全局异常、关键错误信息，便于快速定位问题 |
| 审计日志 | `logs/config_audit.log` | 配置变更、敏感操作记录，用于审计追踪 |

所有日志均使用 JSON 结构化格式，便于接入 ELK/CloudWatch 等日志分析系统。日志默认采用按日轮转（`TimedRotatingFileHandler`）及大小轮转（`RotatingFileHandler`），可通过下述环境变量调整：

- `LOG_FILE_PATH`：主日志文件路径
- `LOG_MAX_SIZE`：单个日志文件最大体积（字节）
- `LOG_BACKUP_COUNT`：保留历史文件数量
- `LOG_ROTATION_WHEN` / `LOG_ROTATION_INTERVAL`：按时间轮转配置

### 日志清理

使用 `app.core.logging.cleanup_old_logs(days=30)` 可定期清理 30 天前的历史日志，可结合 Crontab 或定时任务执行。

## 监控指标说明

系统使用 Prometheus 导出以下核心指标（`/api/v1/metrics`）：

| 指标 | 类型 | 标签 | 说明 |
| --- | --- | --- | --- |
| `api_requests_total` | Counter | method, endpoint, status | API 请求总数，包含状态码维度 |
| `api_request_duration_seconds` | Histogram | method, endpoint | API 请求耗时直方图，用于计算 P95/P99 |
| `active_orders_total` | Gauge | — | 当前活跃订单数量 |
| `strategy_signals_total` | Counter | strategy, signal_type | 策略触发信号次数 |
| `trades_executed_total` | Counter | instrument, side | 已执行交易数目 |
| `websocket_connections_active` | Gauge | — | 活跃 WebSocket 连接数 |

前端监控面板会基于上述指标计算平均响应时间、QPS、错误率等指标。若需扩展指标，可在 `app/monitoring/metrics.py` 中添加。

## 告警配置说明

告警系统通过 `AlertManager` 管理规则与通知渠道，内置以下示例规则（位于 `app/monitoring/alerts.py`）：

- **高错误率**：`error_rate > 5%`
- **余额不足**：`balance < 100`
- **单笔大额亏损**：`|pnl| > 1000`

默认提供邮件与 Telegram 输出示例，可根据环境变量配置实际通知目标：

- `ALERT_EMAIL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

在生产环境中建议接入企业微信、钉钉或 PagerDuty 等渠道，可通过实现自定义 `AlertChannel` 完成。

## 故障排查手册

1. **API 请求慢或超时**
   - 检查 `api_request_duration_seconds` 直方图的 P95/P99 是否飙升
   - 查看 `logs/api.log`，定位慢请求路径与调用方
   - 若数据库瓶颈，查看慢查询日志或启用查询分析

2. **错误率升高**
   - 关注告警通知及 `logs/error.log`
   - 使用监控面板的“最近错误”列表快速定位模块
   - 检查外部依赖（OKX、Redis、数据库）健康状态

3. **交易延迟或失败**
   - 查看 `logs/trading.log` 与 `logs/strategy.log`
   - 确认 WebSocket 连接数是否异常，必要时重启推送服务
   - 对比 `active_orders_total` 与实际订单数量，排查订单同步问题

4. **系统不可用**
   - 访问 `/api/v1/health/detailed`，检查组件状态
   - 核对最近配置变更记录（`logs/config_audit.log`）
   - 若怀疑部署问题，确认 `.env` 配置、数据库迁移及依赖服务状态

## 最佳实践

- 将 Prometheus 指标接入 Grafana，构建自定义大屏
- 将结构化日志接入集中化日志平台，并建立关键字告警
- 定期回放告警流程，确保通知链路有效
- 对关键指标设置 SLO/SLA 并持续跟踪达成率
