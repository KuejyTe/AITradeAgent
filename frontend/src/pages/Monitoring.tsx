import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import apiClient from '../services/api'

interface HealthChecks {
  database?: boolean
  redis?: boolean
  okx_api?: boolean
  websocket?: boolean
  [key: string]: boolean | undefined
}

interface DetailedHealth {
  status: string
  timestamp: string
  uptime_seconds?: number
  checks?: HealthChecks
}

type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'

interface LogEntry {
  id: string
  timestamp: string
  level: LogLevel
  source: string
  message: string
}

interface MetricsTracker {
  timestamp: number
  totalRequests: number
  errorRequests: number
  tradesBaseline: number
  lastStrategySignals: number
}

interface ParsedMetricsSummary {
  totalRequests: number
  errorRequests: number
  durationSum: number
  durationCount: number
  activeOrders: number | null
  websocketConnections: number | null
  tradesExecuted: number
  strategySignals: number
}

const INITIAL_LOGS: LogEntry[] = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    level: 'INFO',
    source: 'app',
    message: '系统启动完成，所有服务运行正常',
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 60_000).toISOString(),
    level: 'WARNING',
    source: 'strategy',
    message: '策略 Momentum-Alpha 信号强度低于预设阈值',
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 120_000).toISOString(),
    level: 'ERROR',
    source: 'trading',
    message: '订单提交失败：网络请求超时，已进入重试队列',
  },
]

const LEVEL_OPTIONS: LogLevel[] = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

const formatUptime = (seconds?: number) => {
  if (!seconds && seconds !== 0) {
    return '--'
  }
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return [
    days ? `${days}天` : null,
    hours ? `${hours}小时` : null,
    minutes ? `${minutes}分钟` : null,
  ]
    .filter(Boolean)
    .join(' ') || `${Math.round(seconds)}秒`
}

const formatTimestamp = (value?: string) => {
  if (!value) {
    return '--'
  }
  return new Date(value).toLocaleString()
}

const parsePrometheusMetrics = (payload: string): ParsedMetricsSummary => {
  const summary: ParsedMetricsSummary = {
    totalRequests: 0,
    errorRequests: 0,
    durationSum: 0,
    durationCount: 0,
    activeOrders: null,
    websocketConnections: null,
    tradesExecuted: 0,
    strategySignals: 0,
  }

  const lines = payload.split('\n')
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) {
      continue
    }

    const value = Number(trimmed.split(' ').pop())
    if (!Number.isFinite(value)) {
      continue
    }

    if (trimmed.startsWith('api_requests_total')) {
      summary.totalRequests += value
      const statusMatch = trimmed.match(/status="(\d{3})"/)
      if (statusMatch && !['2', '3'].includes(statusMatch[1][0])) {
        summary.errorRequests += value
      }
      continue
    }

    if (trimmed.startsWith('api_request_duration_seconds_sum')) {
      summary.durationSum += value
      continue
    }

    if (trimmed.startsWith('api_request_duration_seconds_count')) {
      summary.durationCount += value
      continue
    }

    if (trimmed.startsWith('active_orders_total')) {
      summary.activeOrders = (summary.activeOrders ?? 0) + value
      continue
    }

    if (trimmed.startsWith('websocket_connections_active')) {
      summary.websocketConnections = value
      continue
    }

    if (trimmed.startsWith('trades_executed_total')) {
      summary.tradesExecuted += value
      continue
    }

    if (trimmed.startsWith('strategy_signals_total')) {
      summary.strategySignals += value
    }
  }

  return summary
}

const Monitoring = () => {
  const [systemStatus, setSystemStatus] = useState<DetailedHealth | null>(null)
  const [healthLoading, setHealthLoading] = useState(false)
  const [healthError, setHealthError] = useState<string | null>(null)

  const [latencySeries, setLatencySeries] = useState<{ time: string; latency: number }[]>([])
  const [averageLatency, setAverageLatency] = useState<number>(0)
  const [qps, setQps] = useState<number>(0)
  const [errorRate, setErrorRate] = useState<number>(0)
  const [websocketConnectionsCount, setWebsocketConnectionsCount] = useState<number | null>(null)
  const [activeOrders, setActiveOrders] = useState<number>(0)
  const [tradesToday, setTradesToday] = useState<number>(0)
  const [strategyStatus, setStrategyStatus] = useState<'运行中' | '待机'>('待机')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const metricsTracker = useRef<MetricsTracker | null>(null)

  const [logs, setLogs] = useState<LogEntry[]>(INITIAL_LOGS)
  const [levelFilter, setLevelFilter] = useState<'ALL' | LogLevel>('ALL')
  const [searchTerm, setSearchTerm] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')

  const appendLog = useCallback(
    (level: LogLevel, source: string, message: string) => {
      setLogs((prev) => {
        const entry: LogEntry = {
          id: `${Date.now().toString(36)}-${Math.random().toString(16).slice(2, 8)}`,
          timestamp: new Date().toISOString(),
          level,
          source,
          message,
        }
        const next = [...prev, entry]
        return next.length > 200 ? next.slice(next.length - 200) : next
      })
    },
    [setLogs],
  )

  const loadSystemStatus = useCallback(async () => {
    setHealthLoading(true)
    try {
      const response = await apiClient.get<DetailedHealth>('/api/v1/health/detailed')
      setSystemStatus(response.data)
      setHealthError(null)
    } catch (error) {
      console.warn('[monitoring] failed to load health', error)
      setHealthError('无法获取系统健康状态')
      const reason = error instanceof Error ? error.message : String(error)
      appendLog('ERROR', 'api', `健康检查失败: ${reason}`)
    } finally {
      setHealthLoading(false)
    }
  }, [appendLog])

  const loadMetrics = useCallback(async () => {
    try {
      const response = await apiClient.get<string>('/api/v1/metrics', {
        responseType: 'text',
        transformResponse: (data) => data,
      })

      const summary = parsePrometheusMetrics(response.data)
      const now = Date.now()

      const latencyMs = summary.durationCount > 0 ? (summary.durationSum / summary.durationCount) * 1000 : 0
      setAverageLatency(latencyMs)

      setLatencySeries((prev) => {
        const next = [...prev, { time: new Date().toLocaleTimeString(), latency: Number(latencyMs.toFixed(2)) }]
        return next.length > 20 ? next.slice(next.length - 20) : next
      })

      if (summary.activeOrders !== null) {
        setActiveOrders(Math.round(summary.activeOrders))
      }
      if (summary.websocketConnections !== null) {
        setWebsocketConnectionsCount(Math.max(0, Math.round(summary.websocketConnections)))
      }

      if (!metricsTracker.current) {
        metricsTracker.current = {
          timestamp: now,
          totalRequests: summary.totalRequests,
          errorRequests: summary.errorRequests,
          tradesBaseline: summary.tradesExecuted,
          lastStrategySignals: summary.strategySignals,
        }
        setTradesToday(0)
        setQps(0)
        setErrorRate(summary.totalRequests > 0 ? (summary.errorRequests / summary.totalRequests) * 100 : 0)
        setStrategyStatus(summary.strategySignals > 0 ? '运行中' : '待机')
        return
      }

      const elapsedSeconds = (now - metricsTracker.current.timestamp) / 1000
      const deltaRequests = summary.totalRequests - metricsTracker.current.totalRequests
      const deltaErrors = summary.errorRequests - metricsTracker.current.errorRequests

      if (elapsedSeconds > 0 && deltaRequests >= 0) {
        setQps(deltaRequests / elapsedSeconds)
      }

      if (deltaRequests > 0 && deltaErrors >= 0) {
        setErrorRate((deltaErrors / deltaRequests) * 100)
      } else if (summary.totalRequests > 0) {
        setErrorRate((summary.errorRequests / summary.totalRequests) * 100)
      }

      setTradesToday(Math.max(0, summary.tradesExecuted - metricsTracker.current.tradesBaseline))

      const signalsDelta = summary.strategySignals - metricsTracker.current.lastStrategySignals
      setStrategyStatus(signalsDelta > 0 ? '运行中' : '待机')

      metricsTracker.current.totalRequests = summary.totalRequests
      metricsTracker.current.errorRequests = summary.errorRequests
      metricsTracker.current.timestamp = now
      metricsTracker.current.lastStrategySignals = summary.strategySignals
    } catch (error) {
      console.warn('[monitoring] failed to load metrics', error)
      const reason = error instanceof Error ? error.message : String(error)
      appendLog('WARNING', 'monitoring', `指标采集失败: ${reason}`)
    }
  }, [appendLog])

  useEffect(() => {
    void loadSystemStatus()
    void loadMetrics()
  }, [loadSystemStatus, loadMetrics])

  useEffect(() => {
    if (!autoRefresh) {
      return
    }
    const interval = window.setInterval(() => {
      void loadSystemStatus()
      void loadMetrics()
    }, 15000)
    return () => window.clearInterval(interval)
  }, [autoRefresh, loadMetrics, loadSystemStatus])

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (levelFilter !== 'ALL' && log.level !== levelFilter) {
        return false
      }
      if (searchTerm && !log.message.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false
      }
      const time = new Date(log.timestamp).getTime()
      if (startTime && time < new Date(startTime).getTime()) {
        return false
      }
      if (endTime && time > new Date(endTime).getTime()) {
        return false
      }
      return true
    })
  }, [logs, levelFilter, searchTerm, startTime, endTime])

  const recentErrors = useMemo(() => logs.filter((log) => log.level === 'ERROR').slice(0, 5), [logs])

  const handleExportLogs = () => {
    const blob = new Blob([JSON.stringify(filteredLogs, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `logs-${Date.now()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const toggleLevel = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setLevelFilter(event.target.value as typeof levelFilter)
  }

  const handleManualRefresh = () => {
    void loadSystemStatus()
    void loadMetrics()
  }

  return (
    <div className="monitoring-page">
      <header className="monitoring-header">
        <div>
          <h1>系统监控仪表板</h1>
          <p>实时监控日志、性能指标与交易运行状况</p>
        </div>
        <div className="monitoring-actions">
          <button type="button" onClick={handleManualRefresh} className="monitoring-button primary" disabled={healthLoading}>
            {healthLoading ? '刷新中...' : '立即刷新'}
          </button>
          <label className="monitoring-autorefresh">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(event) => setAutoRefresh(event.target.checked)}
            />
            自动刷新
          </label>
        </div>
      </header>

      <section className="monitoring-section">
        <h2>系统状态</h2>
        {healthError ? <div className="monitoring-alert">{healthError}</div> : null}
        <div className="monitoring-grid">
          <div className="monitoring-card">
            <span className="card-label">API 状态</span>
            <span className={`status-pill status-${systemStatus?.status ?? 'unknown'}`}>
              {systemStatus?.status ?? 'unknown'}
            </span>
            <small>最后更新时间：{formatTimestamp(systemStatus?.timestamp)}</small>
          </div>
          <div className="monitoring-card">
            <span className="card-label">系统运行时长</span>
            <span className="card-value">{formatUptime(systemStatus?.uptime_seconds)}</span>
            <small>自服务启动以来</small>
          </div>
          <div className="monitoring-card">
            <span className="card-label">数据库连接</span>
            <span className={`status-pill ${systemStatus?.checks?.database ? 'status-healthy' : 'status-degraded'}`}>
              {systemStatus?.checks?.database ? '在线' : '离线'}
            </span>
            <small>主数据库</small>
          </div>
          <div className="monitoring-card">
            <span className="card-label">Redis 缓存</span>
            <span className={`status-pill ${systemStatus?.checks?.redis ? 'status-healthy' : 'status-degraded'}`}>
              {systemStatus?.checks?.redis ? '在线' : '离线'}
            </span>
            <small>缓存层</small>
          </div>
          <div className="monitoring-card">
            <span className="card-label">WebSocket 连接</span>
            <span className="card-value">{websocketConnectionsCount ?? '--'}</span>
            <small>当前活跃连接数</small>
          </div>
          <div className="monitoring-card">
            <span className="card-label">OKX API</span>
            <span className={`status-pill ${systemStatus?.checks?.okx_api ? 'status-healthy' : 'status-degraded'}`}>
              {systemStatus?.checks?.okx_api ? '正常' : '异常'}
            </span>
            <small>交易所接口状态</small>
          </div>
        </div>
      </section>

      <section className="monitoring-section">
        <h2>性能指标</h2>
        <div className="performance-summary">
          <div className="summary-item">
            <span className="summary-label">平均响应时间</span>
            <span className="summary-value">{averageLatency.toFixed(2)} ms</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">请求 QPS</span>
            <span className="summary-value">{qps.toFixed(2)}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">错误率</span>
            <span className="summary-value">{errorRate.toFixed(2)}%</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">数据库查询性能</span>
            <span className="summary-value muted">--</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">内存使用</span>
            <span className="summary-value muted">--</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">CPU 使用率</span>
            <span className="summary-value muted">--</span>
          </div>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={latencySeries} margin={{ top: 10, right: 24, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e6e6e6" />
              <XAxis dataKey="time" minTickGap={24} />
              <YAxis unit="ms" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="latency" stroke="#3f8efc" dot={false} name="响应时间" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="monitoring-section">
        <h2>交易监控</h2>
        <div className="monitoring-grid trade-grid">
          <div className="monitoring-card">
            <span className="card-label">今日交易次数</span>
            <span className="card-value">{tradesToday}</span>
            <small>自页面加载起统计</small>
          </div>
          <div className="monitoring-card">
            <span className="card-label">今日成交金额</span>
            <span className="card-value muted">--</span>
            <small>待接入交易执行统计</small>
          </div>
          <div className="monitoring-card">
            <span className="card-label">策略运行状态</span>
            <span className={`status-pill ${strategyStatus === '运行中' ? 'status-healthy' : 'status-degraded'}`}>
              {strategyStatus}
            </span>
            <small>根据策略信号监测</small>
          </div>
          <div className="monitoring-card">
            <span className="card-label">活跃订单数</span>
            <span className="card-value">{activeOrders}</span>
            <small>当前挂单数量</small>
          </div>
        </div>
        <div className="monitoring-card">
          <span className="card-label">最近错误</span>
          {recentErrors.length === 0 ? (
            <p className="muted">暂无错误日志</p>
          ) : (
            <ul className="error-list">
              {recentErrors.map((log) => (
                <li key={log.id}>
                  <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                  <span className="error-message">{log.message}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="monitoring-section">
        <div className="section-header">
          <h2>日志查看器</h2>
          <button type="button" className="monitoring-button" onClick={handleExportLogs}>
            导出日志
          </button>
        </div>
        <div className="log-filters">
          <label>
            日志级别
            <select value={levelFilter} onChange={toggleLevel}>
              <option value="ALL">全部</option>
              {LEVEL_OPTIONS.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </label>
          <label>
            关键词
            <input type="text" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="搜索日志关键词" />
          </label>
          <label>
            开始时间
            <input type="datetime-local" value={startTime} onChange={(event) => setStartTime(event.target.value)} />
          </label>
          <label>
            结束时间
            <input type="datetime-local" value={endTime} onChange={(event) => setEndTime(event.target.value)} />
          </label>
        </div>
        <div className="log-table-wrapper">
          <table className="log-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>级别</th>
                <th>模块</th>
                <th>消息</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="muted">
                    无匹配日志
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td>{formatTimestamp(log.timestamp)}</td>
                    <td>
                      <span className={`log-level level-${log.level.toLowerCase()}`}>{log.level}</span>
                    </td>
                    <td>{log.source}</td>
                    <td>{log.message}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default Monitoring
