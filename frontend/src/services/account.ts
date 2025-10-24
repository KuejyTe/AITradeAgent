import apiClient from './api'
import {
  AccountState,
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
import {
  getMockAssetHistory,
  getMockOrders,
  getMockPerformance,
  getMockTradeStatistics,
  getMockTrades,
  mockBalances,
  mockNotifications,
  mockPositions,
  mockRiskMetrics,
  mockStrategies,
} from './mockData'

let strategyCache = mockStrategies.map((strategy) => ({ ...strategy }))
let riskCache: RiskMetrics = JSON.parse(JSON.stringify(mockRiskMetrics))

const safeRequest = async <T>(request: () => Promise<T>, fallback: () => T): Promise<T> => {
  try {
    const data = await request()
    return data
  } catch (error) {
    console.warn('[account-service] Falling back to mock data:', (error as Error)?.message ?? error)
    return fallback()
  }
}

export const getAccountBalance = (): Promise<Balance[]> =>
  safeRequest(async () => {
    const response = await apiClient.get<Balance[]>('/api/v1/account/balance')
    return response.data
  }, () => mockBalances)

export const getPositions = (): Promise<Position[]> =>
  safeRequest(async () => {
    const response = await apiClient.get<Position[]>('/api/v1/account/positions')
    return response.data
  }, () => mockPositions)

export const getOrderHistory = (filters?: OrderFilters): Promise<Order[]> =>
  safeRequest(async () => {
    const response = await apiClient.get<Order[]>('/api/v1/account/orders', {
      params: filters,
    })
    return response.data
  }, () => getMockOrders(filters))

export const getTradeHistory = (filters?: TradeFilters): Promise<Trade[]> =>
  safeRequest(async () => {
    const response = await apiClient.get<Trade[]>('/api/v1/account/trades', {
      params: filters,
    })
    return response.data
  }, () => getMockTrades(filters))

export const getPerformanceMetrics = (range: PerformanceRange): Promise<PerformanceMetrics> =>
  safeRequest(async () => {
    const response = await apiClient.get<PerformanceMetrics>('/api/v1/account/performance', {
      params: { range },
    })
    return response.data
  }, () => getMockPerformance(range))

export const getAssetHistory = (range: TimeRange): Promise<AssetHistoryPoint[]> =>
  safeRequest(async () => {
    const response = await apiClient.get<AssetHistoryPoint[]>('/api/v1/account/asset-history', {
      params: { range },
    })
    return response.data
  }, () => getMockAssetHistory(range))

export const getTradeStatistics = (filters?: TradeFilters): Promise<TradeStatistics> =>
  safeRequest(async () => {
    const response = await apiClient.get<TradeStatistics>('/api/v1/account/trade-stats', {
      params: filters,
    })
    return response.data
  }, () => getMockTradeStatistics(filters))

export const getStrategies = (): Promise<Strategy[]> =>
  safeRequest(async () => {
    const response = await apiClient.get<Strategy[]>('/api/v1/strategies')
    strategyCache = response.data
    return response.data
  }, () => strategyCache)

export const updateStrategyStatus = (strategyId: string, status: Strategy['status']): Promise<Strategy[]> =>
  safeRequest(async () => {
    const response = await apiClient.post<Strategy[]>(`/api/v1/strategies/${strategyId}/status`, { status })
    strategyCache = response.data
    return response.data
  }, () => {
    strategyCache = strategyCache.map((strategy) =>
      strategy.id === strategyId
        ? {
            ...strategy,
            status,
            lastUpdated: new Date().toISOString(),
          }
        : strategy,
    )
    return strategyCache
  })

export const getRiskMetrics = (): Promise<RiskMetrics> =>
  safeRequest(async () => {
    const response = await apiClient.get<RiskMetrics>('/api/v1/risk/metrics')
    riskCache = response.data
    return response.data
  }, () => JSON.parse(JSON.stringify(riskCache)))

export const setRiskCache = (nextRisk: RiskMetrics): void => {
  riskCache = JSON.parse(JSON.stringify(nextRisk))
}

export const getNotifications = (): Promise<Notification[]> =>
  safeRequest(async () => {
    const response = await apiClient.get<Notification[]>('/api/v1/notifications')
    return response.data
  }, () => mockNotifications)

export const acknowledgeNotification = (notificationId: string): Promise<void> =>
  safeRequest(async () => {
    await apiClient.post(`/api/v1/notifications/${notificationId}/read`)
  }, () => undefined)

export const getInitialAccountState = async (): Promise<Pick<AccountState, 'balance' | 'positions' | 'orders' | 'trades' | 'performance' | 'assetHistory' | 'tradeStats' | 'strategies' | 'risk' | 'notifications'>> => {
  const [balance, positions, orders, trades, performance, assetHistory, tradeStats, strategies, risk, notifications] =
    await Promise.all([
      getAccountBalance(),
      getPositions(),
      getOrderHistory(),
      getTradeHistory(),
      getPerformanceMetrics('ALL'),
      getAssetHistory('1M'),
      getTradeStatistics(),
      getStrategies(),
      getRiskMetrics(),
      getNotifications(),
    ])

  return { balance, positions, orders, trades, performance, assetHistory, tradeStats, strategies, risk, notifications }
}
