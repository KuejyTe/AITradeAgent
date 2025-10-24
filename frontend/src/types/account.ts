export type Direction = 'LONG' | 'SHORT'
export type OrderSide = 'BUY' | 'SELL'
export type OrderType = 'LIMIT' | 'MARKET' | 'STOP' | 'STOP_LIMIT'
export type OrderStatus = 'FILLED' | 'PARTIALLY_FILLED' | 'CANCELED' | 'OPEN' | 'REJECTED'

export interface Balance {
  asset: string
  available: number
  hold: number
  usdValue: number
  allocation: number
}

export interface Position {
  symbol: string
  direction: Direction
  size: number
  entryPrice: number
  markPrice: number
  pnl: {
    value: number
    percentage: number
  }
  margin: number
  updatedAt: string
  strategy?: string
}

export interface Order {
  id: string
  timestamp: string
  symbol: string
  type: OrderType
  side: OrderSide
  price: number
  quantity: number
  filledQuantity: number
  status: OrderStatus
}

export interface Trade {
  id: string
  orderId: string
  timestamp: string
  symbol: string
  side: OrderSide
  price: number
  quantity: number
  fee: number
  strategy?: string
}

export interface PerformanceMetrics {
  totalReturn: number
  annualizedReturn: number
  maxDrawdown: number
  sharpeRatio: number
  winRate: number
  averageWin: number
  averageLoss: number
  totalTrades: number
  winningTrades: number
  losingTrades: number
  profitLossToday: number
  profitLossTotal: number
}

export type TimeRange = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL'
export type PerformanceRange = 'TODAY' | 'WEEK' | 'MONTH' | 'YEAR' | 'ALL'

export interface AssetHistoryPoint {
  timestamp: string
  total: number
  available: number
  btcPrice?: number
  event?: string
}

export interface PairStatistic {
  symbol: string
  trades: number
  pnl: number
  winRate: number
}

export interface ProfitBucket {
  range: string
  count: number
}

export interface HoldingBucket {
  bucket: string
  count: number
  avgPnl: number
}

export interface HeatmapCell {
  hour: number
  weekday: number
  trades: number
  pnl: number
}

export interface StrategyPerformance {
  strategy: string
  pnl: number
  winRate: number
  sharpe: number
  trades: number
}

export interface TradeStatistics {
  byPair: PairStatistic[]
  profitDistribution: ProfitBucket[]
  holdingDurations: HoldingBucket[]
  hourlyHeatmap: HeatmapCell[]
  strategyComparison: StrategyPerformance[]
  totals: {
    volume: number
    fees: number
  }
}

export interface Strategy {
  id: string
  name: string
  status: 'running' | 'stopped' | 'paused'
  pnl: number
  winRate: number
  trades: number
  description?: string
  lastUpdated: string
}

export interface RiskEvent {
  id: string
  timestamp: string
  rule: string
  severity: 'info' | 'warning' | 'critical'
  details: string
}

export interface RiskAlert {
  id: string
  type: string
  description: string
  threshold?: number
  enabled: boolean
}

export interface RiskMetrics {
  currentExposure: number
  maxExposure: number
  leverage: number
  maxLeverage: number
  marginUtilization: number
  var: number
  riskEvents: RiskEvent[]
  alerts: RiskAlert[]
}

export interface Notification {
  id: string
  category: 'order' | 'price' | 'strategy' | 'system'
  title: string
  message: string
  timestamp: string
  read: boolean
  severity: 'info' | 'success' | 'warning' | 'critical'
}

export interface OrderFilters {
  start?: string
  end?: string
  status?: OrderStatus | 'ALL'
  symbol?: string
  side?: OrderSide | 'ALL'
}

export interface TradeFilters {
  start?: string
  end?: string
  symbol?: string
  side?: OrderSide | 'ALL'
}

export interface AccountState {
  balance: Balance[]
  positions: Position[]
  orders: Order[]
  trades: Trade[]
  performance: PerformanceMetrics | null
  performanceRange: PerformanceRange
  assetHistory: AssetHistoryPoint[]
  assetHistoryRange: TimeRange
  tradeStats: TradeStatistics | null
  strategies: Strategy[]
  risk: RiskMetrics | null
  notifications: Notification[]
  loading: boolean
  error: string | null
  lastUpdated?: string
}

export interface AccountContextValue extends AccountState {
  refreshAll: () => Promise<void>
  refreshBalances: () => Promise<void>
  refreshPositions: () => Promise<void>
  refreshOrders: (filters?: OrderFilters) => Promise<void>
  refreshTrades: (filters?: TradeFilters) => Promise<void>
  refreshPerformance: (range: PerformanceRange) => Promise<void>
  refreshAssetHistory: (range: TimeRange) => Promise<void>
  refreshTradeStats: (filters?: TradeFilters) => Promise<void>
  toggleStrategyStatus: (strategyId: string) => Promise<void>
  markNotificationRead: (notificationId: string) => void
  clearNotifications: () => void
  updateRiskAlert: (alertId: string, enabled: boolean) => void
}
