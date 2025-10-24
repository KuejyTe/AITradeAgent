import {
  AssetHistoryPoint,
  Balance,
  Notification,
  Order,
  OrderFilters,
  PerformanceMetrics,
  PerformanceRange,
  Position,
  RiskMetrics,
  Strategy,
  TimeRange,
  Trade,
  TradeFilters,
  TradeStatistics,
} from '../types/account'

const now = new Date()
const HOURS = 60 * 60 * 1000
const DAYS = 24 * HOURS

const hoursAgo = (hours: number) => new Date(now.getTime() - hours * HOURS).toISOString()
const daysAgo = (days: number) => new Date(now.getTime() - days * DAYS).toISOString()

export const mockBalances: Balance[] = [
  { asset: 'USDT', available: 18000, hold: 2500, usdValue: 20500, allocation: 0.26 },
  { asset: 'BTC', available: 0.85, hold: 0.1, usdValue: 29000, allocation: 0.29 },
  { asset: 'ETH', available: 12.5, hold: 1.4, usdValue: 25000, allocation: 0.22 },
  { asset: 'SOL', available: 320, hold: 40, usdValue: 12000, allocation: 0.13 },
  { asset: 'USDC', available: 8000, hold: 0, usdValue: 8000, allocation: 0.1 },
]

export const mockPositions: Position[] = [
  {
    symbol: 'BTC/USDT',
    direction: 'LONG',
    size: 0.75,
    entryPrice: 36800,
    markPrice: 38250,
    pnl: { value: 1087.5, percentage: 0.0427 },
    margin: 9200,
    strategy: 'AI Momentum',
    updatedAt: hoursAgo(2),
  },
  {
    symbol: 'ETH/USDT',
    direction: 'SHORT',
    size: 8.5,
    entryPrice: 2680,
    markPrice: 2595,
    pnl: { value: 722.5, percentage: 0.0338 },
    margin: 5200,
    strategy: 'Mean Reversion',
    updatedAt: hoursAgo(4),
  },
  {
    symbol: 'SOL/USDT',
    direction: 'LONG',
    size: 250,
    entryPrice: 58.4,
    markPrice: 62.1,
    pnl: { value: 925, percentage: 0.0635 },
    margin: 3600,
    strategy: 'AI Momentum',
    updatedAt: hoursAgo(1),
  },
]

const baseOrders: Order[] = [
  {
    id: 'ORD-20240301-001',
    timestamp: hoursAgo(2),
    symbol: 'BTC/USDT',
    type: 'LIMIT',
    side: 'BUY',
    price: 38000,
    quantity: 0.6,
    filledQuantity: 0.6,
    status: 'FILLED',
  },
  {
    id: 'ORD-20240301-002',
    timestamp: hoursAgo(5),
    symbol: 'ETH/USDT',
    type: 'MARKET',
    side: 'SELL',
    price: 2620,
    quantity: 5,
    filledQuantity: 5,
    status: 'FILLED',
  },
  {
    id: 'ORD-20240229-003',
    timestamp: hoursAgo(18),
    symbol: 'SOL/USDT',
    type: 'LIMIT',
    side: 'BUY',
    price: 60.5,
    quantity: 200,
    filledQuantity: 150,
    status: 'PARTIALLY_FILLED',
  },
  {
    id: 'ORD-20240228-004',
    timestamp: daysAgo(1),
    symbol: 'BTC/USDT',
    type: 'STOP',
    side: 'SELL',
    price: 35200,
    quantity: 0.4,
    filledQuantity: 0,
    status: 'CANCELED',
  },
  {
    id: 'ORD-20240228-005',
    timestamp: daysAgo(2),
    symbol: 'ETH/USDT',
    type: 'LIMIT',
    side: 'BUY',
    price: 2550,
    quantity: 4,
    filledQuantity: 4,
    status: 'FILLED',
  },
  {
    id: 'ORD-20240227-006',
    timestamp: daysAgo(3),
    symbol: 'SOL/USDT',
    type: 'MARKET',
    side: 'SELL',
    price: 59.2,
    quantity: 100,
    filledQuantity: 100,
    status: 'FILLED',
  },
  {
    id: 'ORD-20240225-007',
    timestamp: daysAgo(5),
    symbol: 'BTC/USDT',
    type: 'LIMIT',
    side: 'SELL',
    price: 39400,
    quantity: 0.3,
    filledQuantity: 0,
    status: 'OPEN',
  },
  {
    id: 'ORD-20240222-008',
    timestamp: daysAgo(8),
    symbol: 'SOL/USDT',
    type: 'LIMIT',
    side: 'BUY',
    price: 56.8,
    quantity: 180,
    filledQuantity: 180,
    status: 'FILLED',
  },
  {
    id: 'ORD-20240218-009',
    timestamp: daysAgo(12),
    symbol: 'BTC/USDT',
    type: 'MARKET',
    side: 'BUY',
    price: 37250,
    quantity: 0.5,
    filledQuantity: 0.5,
    status: 'FILLED',
  },
  {
    id: 'ORD-20240210-010',
    timestamp: daysAgo(20),
    symbol: 'ETH/USDT',
    type: 'LIMIT',
    side: 'SELL',
    price: 2785,
    quantity: 3,
    filledQuantity: 0,
    status: 'CANCELED',
  },
  {
    id: 'ORD-20240121-011',
    timestamp: daysAgo(39),
    symbol: 'SOL/USDT',
    type: 'STOP_LIMIT',
    side: 'SELL',
    price: 54.2,
    quantity: 200,
    filledQuantity: 200,
    status: 'FILLED',
  },
  {
    id: 'ORD-20231228-012',
    timestamp: daysAgo(82),
    symbol: 'BTC/USDT',
    type: 'LIMIT',
    side: 'BUY',
    price: 34800,
    quantity: 0.8,
    filledQuantity: 0.8,
    status: 'FILLED',
  },
]

const baseTrades: Trade[] = [
  {
    id: 'TRD-6001',
    orderId: 'ORD-20240301-001',
    timestamp: hoursAgo(2),
    symbol: 'BTC/USDT',
    side: 'BUY',
    price: 37980,
    quantity: 0.6,
    fee: 5.2,
    strategy: 'AI Momentum',
  },
  {
    id: 'TRD-6002',
    orderId: 'ORD-20240301-002',
    timestamp: hoursAgo(5),
    symbol: 'ETH/USDT',
    side: 'SELL',
    price: 2624,
    quantity: 5,
    fee: 3.8,
    strategy: 'Mean Reversion',
  },
  {
    id: 'TRD-6003',
    orderId: 'ORD-20240229-003',
    timestamp: hoursAgo(18),
    symbol: 'SOL/USDT',
    side: 'BUY',
    price: 60.2,
    quantity: 150,
    fee: 4.1,
    strategy: 'AI Momentum',
  },
  {
    id: 'TRD-6004',
    orderId: 'ORD-20240228-005',
    timestamp: daysAgo(2),
    symbol: 'ETH/USDT',
    side: 'BUY',
    price: 2548,
    quantity: 4,
    fee: 2.7,
    strategy: 'AI Momentum',
  },
  {
    id: 'TRD-6005',
    orderId: 'ORD-20240227-006',
    timestamp: daysAgo(3),
    symbol: 'SOL/USDT',
    side: 'SELL',
    price: 59.3,
    quantity: 100,
    fee: 2.9,
    strategy: 'Scalper',
  },
  {
    id: 'TRD-6006',
    orderId: 'ORD-20240222-008',
    timestamp: daysAgo(8),
    symbol: 'SOL/USDT',
    side: 'BUY',
    price: 56.8,
    quantity: 180,
    fee: 4.8,
    strategy: 'AI Momentum',
  },
  {
    id: 'TRD-6007',
    orderId: 'ORD-20240218-009',
    timestamp: daysAgo(12),
    symbol: 'BTC/USDT',
    side: 'BUY',
    price: 37280,
    quantity: 0.5,
    fee: 4.2,
    strategy: 'Mean Reversion',
  },
  {
    id: 'TRD-6008',
    orderId: 'ORD-20240210-010',
    timestamp: daysAgo(20),
    symbol: 'ETH/USDT',
    side: 'SELL',
    price: 2780,
    quantity: 3,
    fee: 2.5,
    strategy: 'Scalper',
  },
  {
    id: 'TRD-6009',
    orderId: 'ORD-20240121-011',
    timestamp: daysAgo(39),
    symbol: 'SOL/USDT',
    side: 'SELL',
    price: 54.3,
    quantity: 200,
    fee: 5.4,
    strategy: 'AI Momentum',
  },
  {
    id: 'TRD-6010',
    orderId: 'ORD-20231228-012',
    timestamp: daysAgo(82),
    symbol: 'BTC/USDT',
    side: 'BUY',
    price: 34820,
    quantity: 0.8,
    fee: 5.6,
    strategy: 'AI Momentum',
  },
]

const performanceByRange: Record<PerformanceRange, PerformanceMetrics> = {
  TODAY: {
    totalReturn: 0.017,
    annualizedReturn: 0.42,
    maxDrawdown: 0.04,
    sharpeRatio: 2.8,
    winRate: 0.68,
    averageWin: 420,
    averageLoss: -260,
    totalTrades: 6,
    winningTrades: 4,
    losingTrades: 2,
    profitLossToday: 540,
    profitLossTotal: 39680,
  },
  WEEK: {
    totalReturn: 0.036,
    annualizedReturn: 0.38,
    maxDrawdown: 0.07,
    sharpeRatio: 2.45,
    winRate: 0.66,
    averageWin: 480,
    averageLoss: -310,
    totalTrades: 24,
    winningTrades: 16,
    losingTrades: 8,
    profitLossToday: 540,
    profitLossTotal: 39680,
  },
  MONTH: {
    totalReturn: 0.078,
    annualizedReturn: 0.41,
    maxDrawdown: 0.11,
    sharpeRatio: 2.32,
    winRate: 0.63,
    averageWin: 510,
    averageLoss: -340,
    totalTrades: 92,
    winningTrades: 58,
    losingTrades: 34,
    profitLossToday: 540,
    profitLossTotal: 39680,
  },
  YEAR: {
    totalReturn: 0.312,
    annualizedReturn: 0.43,
    maxDrawdown: 0.18,
    sharpeRatio: 2.58,
    winRate: 0.64,
    averageWin: 495,
    averageLoss: -330,
    totalTrades: 860,
    winningTrades: 552,
    losingTrades: 308,
    profitLossToday: 540,
    profitLossTotal: 39680,
  },
  ALL: {
    totalReturn: 0.412,
    annualizedReturn: 0.37,
    maxDrawdown: 0.21,
    sharpeRatio: 2.34,
    winRate: 0.61,
    averageWin: 470,
    averageLoss: -320,
    totalTrades: 1350,
    winningTrades: 824,
    losingTrades: 526,
    profitLossToday: 540,
    profitLossTotal: 39680,
  },
}

const mockTradeStatistics: TradeStatistics = {
  byPair: [
    { symbol: 'BTC/USDT', trades: 420, pnl: 16800, winRate: 0.64 },
    { symbol: 'ETH/USDT', trades: 360, pnl: 13200, winRate: 0.61 },
    { symbol: 'SOL/USDT', trades: 210, pnl: 9800, winRate: 0.66 },
    { symbol: 'BNB/USDT', trades: 140, pnl: 6200, winRate: 0.58 },
  ],
  profitDistribution: [
    { range: '< -5%', count: 42 },
    { range: '-5% ~ 0%', count: 148 },
    { range: '0% ~ 5%', count: 286 },
    { range: '5% ~ 10%', count: 178 },
    { range: '> 10%', count: 64 },
  ],
  holdingDurations: [
    { bucket: '< 1h', count: 168, avgPnl: 0.014 },
    { bucket: '1h - 4h', count: 214, avgPnl: 0.022 },
    { bucket: '4h - 24h', count: 180, avgPnl: 0.028 },
    { bucket: '> 24h', count: 128, avgPnl: 0.034 },
  ],
  hourlyHeatmap: Array.from({ length: 7 * 24 }).map((_, index) => {
    const weekday = Math.floor(index / 24)
    const hour = index % 24
    const baseline = Math.sin((hour / 24) * Math.PI * 2) * 8 + 12
    const weekendAdjust = weekday === 0 || weekday === 6 ? 0.6 : 1
    const trades = Math.max(2, Math.round((baseline + weekday * 1.5) * weekendAdjust))
    const pnl = Number(((trades * 35 - 220) / 1000).toFixed(3))
    return { weekday, hour, trades, pnl }
  }),
  strategyComparison: [
    { strategy: 'AI Momentum', pnl: 19800, winRate: 0.66, sharpe: 2.8, trades: 520 },
    { strategy: 'Mean Reversion', pnl: 12800, winRate: 0.58, sharpe: 2.2, trades: 360 },
    { strategy: 'Scalper', pnl: 6200, winRate: 0.63, sharpe: 1.9, trades: 240 },
    { strategy: 'Grid Bot', pnl: 3400, winRate: 0.55, sharpe: 1.5, trades: 180 },
  ],
  totals: {
    volume: 18_600_000,
    fees: 11_240,
  },
}

export const mockStrategies: Strategy[] = [
  {
    id: 'strat-001',
    name: 'AI Momentum',
    status: 'running',
    pnl: 19800,
    winRate: 0.66,
    trades: 520,
    description: 'Deep learning momentum strategy focusing on BTC and SOL.',
    lastUpdated: hoursAgo(1),
  },
  {
    id: 'strat-002',
    name: 'Mean Reversion',
    status: 'paused',
    pnl: 12800,
    winRate: 0.58,
    trades: 360,
    description: 'Short-term mean reversion on ETH perpetuals.',
    lastUpdated: hoursAgo(7),
  },
  {
    id: 'strat-003',
    name: 'Scalper',
    status: 'stopped',
    pnl: 6200,
    winRate: 0.63,
    trades: 240,
    description: 'High frequency scalping strategy on major pairs.',
    lastUpdated: daysAgo(2),
  },
]

export const mockRiskMetrics: RiskMetrics = {
  currentExposure: 0.46,
  maxExposure: 0.75,
  leverage: 4.2,
  maxLeverage: 8,
  marginUtilization: 0.38,
  var: 0.062,
  riskEvents: [
    {
      id: 'risk-evt-001',
      timestamp: hoursAgo(3),
      rule: 'BTC drawdown > 3%',
      severity: 'warning',
      details: 'BTC price dipped 3.5% within 30 minutes. Positions hedged automatically.',
    },
    {
      id: 'risk-evt-002',
      timestamp: daysAgo(1),
      rule: 'Leverage limit breach',
      severity: 'info',
      details: 'SOL leverage reached 5.5x during breakout and was reduced to 4x.',
    },
  ],
  alerts: [
    { id: 'alert-001', type: 'price', description: 'BTC drawdown exceeds 5%', threshold: 0.05, enabled: true },
    { id: 'alert-002', type: 'margin', description: 'Margin utilization exceeds 60%', threshold: 0.6, enabled: true },
    { id: 'alert-003', type: 'strategy', description: 'Strategy drawdown exceeds 12%', threshold: 0.12, enabled: false },
  ],
}

export const mockNotifications: Notification[] = [
  {
    id: 'notif-001',
    category: 'order',
    title: '订单已成交',
    message: 'BTC/USDT 限价买单 0.6 BTC @ 38,000 已完全成交。',
    timestamp: hoursAgo(2),
    read: false,
    severity: 'success',
  },
  {
    id: 'notif-002',
    category: 'price',
    title: '价格告警',
    message: 'ETH/USDT 价格在 30 分钟内上涨 2.5%。',
    timestamp: hoursAgo(5),
    read: false,
    severity: 'warning',
  },
  {
    id: 'notif-003',
    category: 'strategy',
    title: '策略状态更新',
    message: 'AI Momentum 策略今日收益率 +1.7%。',
    timestamp: hoursAgo(8),
    read: true,
    severity: 'info',
  },
  {
    id: 'notif-004',
    category: 'system',
    title: '系统公告',
    message: '系统将在周末进行维护，预计停机 1 小时。',
    timestamp: daysAgo(1),
    read: true,
    severity: 'info',
  },
]

const withinRange = (timestamp: string, filters?: { start?: string; end?: string }) => {
  if (!filters) return true
  const value = new Date(timestamp).getTime()
  if (filters.start) {
    const start = new Date(filters.start).getTime()
    if (value < start) return false
  }
  if (filters.end) {
    const end = new Date(filters.end).getTime()
    if (value > end) return false
  }
  return true
}

export const getMockOrders = (filters?: OrderFilters): Order[] => {
  return baseOrders.filter((order) => {
    if (filters?.status && filters.status !== 'ALL' && order.status !== filters.status) {
      return false
    }
    if (filters?.symbol && filters.symbol !== 'ALL' && order.symbol !== filters.symbol) {
      return false
    }
    if (filters?.side && filters.side !== 'ALL' && order.side !== filters.side) {
      return false
    }
    if (!withinRange(order.timestamp, filters)) {
      return false
    }
    return true
  })
}

export const getMockTrades = (filters?: TradeFilters): Trade[] => {
  return baseTrades.filter((trade) => {
    if (filters?.symbol && filters.symbol !== 'ALL' && trade.symbol !== filters.symbol) {
      return false
    }
    if (filters?.side && filters.side !== 'ALL' && trade.side !== filters.side) {
      return false
    }
    if (!withinRange(trade.timestamp, filters)) {
      return false
    }
    return true
  })
}

export const getMockPerformance = (range: PerformanceRange): PerformanceMetrics => {
  return performanceByRange[range] ?? performanceByRange.ALL
}

const rangeDurations: Record<TimeRange, number> = {
  '1D': 1,
  '1W': 7,
  '1M': 30,
  '3M': 90,
  '6M': 180,
  '1Y': 365,
  ALL: 365,
}

export const getMockAssetHistory = (range: TimeRange): AssetHistoryPoint[] => {
  const limit = rangeDurations[range]
  const points: AssetHistoryPoint[] = []
  const step = range === '1D' ? HOURS : DAYS
  const totalPoints = range === '1D' ? 24 : limit
  for (let i = totalPoints - 1; i >= 0; i -= 1) {
    const timestamp = new Date(now.getTime() - i * step).toISOString()
    const trend = Math.sin((totalPoints - i) / (range === '1D' ? 4 : 8)) * 1200
    const seasonal = Math.cos(i / (range === '1D' ? 4 : 12)) * 600
    const drift = (totalPoints - i) * (range === '1D' ? 18 : 45)
    const total = 42000 + trend + seasonal + drift
    const available = total * 0.42 + Math.sin(i / 3) * 250
    const btcPrice = 39000 + Math.sin(i / 6) * 1800
    const event = i % (range === '1D' ? 12 : 28) === 0 && i !== 0 ? '重要事件' : undefined
    points.push({ timestamp, total: Number(total.toFixed(2)), available: Number(available.toFixed(2)), btcPrice: Number(btcPrice.toFixed(2)), event })
  }
  return points
}

export const getMockTradeStatistics = (_filters?: TradeFilters): TradeStatistics => mockTradeStatistics
