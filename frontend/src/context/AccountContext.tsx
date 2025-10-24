import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
} from 'react'
import {
  AccountContextValue,
  AccountState,
  Balance,
  Notification,
  Order,
  OrderFilters,
  PerformanceRange,
  Position,
  RiskMetrics,
  Strategy,
  TimeRange,
  Trade,
  TradeFilters,
} from '../types/account'
import {
  acknowledgeNotification,
  getAccountBalance,
  getAssetHistory,
  getInitialAccountState,
  getNotifications,
  getOrderHistory,
  getPerformanceMetrics,
  getPositions,
  getRiskMetrics,
  getTradeHistory,
  getTradeStatistics,
  getStrategies,
  setRiskCache,
  updateStrategyStatus,
} from '../services/account'
import WebSocketClient from '../utils/websocket'

const initialState: AccountState = {
  balance: [],
  positions: [],
  orders: [],
  trades: [],
  performance: null,
  performanceRange: 'ALL',
  assetHistory: [],
  assetHistoryRange: '1M',
  tradeStats: null,
  strategies: [],
  risk: null,
  notifications: [],
  loading: false,
  error: null,
  lastUpdated: undefined,
}

type AccountAction =
  | { type: 'SET_STATE'; payload: Partial<AccountState> }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'UPSERT_BALANCES'; payload: Balance[] }
  | { type: 'UPSERT_POSITION'; payload: Position }
  | { type: 'UPSERT_ORDER'; payload: Order }
  | { type: 'UPSERT_TRADE'; payload: Trade }
  | { type: 'SET_RISK'; payload: RiskMetrics }
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'SET_NOTIFICATIONS'; payload: Notification[] }
  | { type: 'MARK_NOTIFICATION'; payload: { id: string; read: boolean } }
  | { type: 'SET_STRATEGIES'; payload: Strategy[] }

const accountReducer = (state: AccountState, action: AccountAction): AccountState => {
  switch (action.type) {
    case 'SET_STATE':
      return { ...state, ...action.payload }
    case 'SET_LOADING':
      return { ...state, loading: action.payload }
    case 'SET_ERROR':
      return { ...state, error: action.payload }
    case 'UPSERT_BALANCES':
      return {
        ...state,
        balance: action.payload,
        lastUpdated: new Date().toISOString(),
      }
    case 'UPSERT_POSITION': {
      const positions = [...state.positions]
      const index = positions.findIndex((position) => position.symbol === action.payload.symbol)
      if (index >= 0) {
        positions[index] = action.payload
      } else {
        positions.push(action.payload)
      }
      return {
        ...state,
        positions,
        lastUpdated: new Date().toISOString(),
      }
    }
    case 'UPSERT_ORDER': {
      const orders = [
        action.payload,
        ...state.orders.filter((order) => order.id !== action.payload.id),
      ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      return {
        ...state,
        orders,
        lastUpdated: new Date().toISOString(),
      }
    }
    case 'UPSERT_TRADE': {
      const trades = [
        action.payload,
        ...state.trades.filter((trade) => trade.id !== action.payload.id),
      ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      return {
        ...state,
        trades,
        lastUpdated: new Date().toISOString(),
      }
    }
    case 'SET_RISK':
      return { ...state, risk: action.payload, lastUpdated: new Date().toISOString() }
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [action.payload, ...state.notifications].slice(0, 50),
        lastUpdated: new Date().toISOString(),
      }
    case 'SET_NOTIFICATIONS':
      return { ...state, notifications: action.payload, lastUpdated: new Date().toISOString() }
    case 'MARK_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.map((notification) =>
          notification.id === action.payload.id
            ? { ...notification, read: action.payload.read }
            : notification,
        ),
        lastUpdated: new Date().toISOString(),
      }
    case 'SET_STRATEGIES':
      return { ...state, strategies: action.payload, lastUpdated: new Date().toISOString() }
    default:
      return state
  }
}

const AccountContext = createContext<AccountContextValue | undefined>(undefined)

type RealtimeMessage =
  | { type: 'balance_update'; payload: Balance[] }
  | { type: 'position_update'; payload: Position }
  | { type: 'order_update'; payload: Order }
  | { type: 'trade_update'; payload: Trade }
  | { type: 'risk_update'; payload: RiskMetrics }
  | { type: 'notification'; payload: Notification }

export const AccountProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(accountReducer, initialState)

  const setLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading })
  }, [])

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error })
  }, [])

  const loadInitialData = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getInitialAccountState()
      dispatch({
        type: 'SET_STATE',
        payload: {
          ...data,
          performanceRange: 'ALL',
          assetHistoryRange: '1M',
          loading: false,
          error: null,
          lastUpdated: new Date().toISOString(),
        },
      })
    } catch (error) {
      setError((error as Error)?.message ?? 'Failed to load account data')
    } finally {
      setLoading(false)
    }
  }, [setError, setLoading])

  useEffect(() => {
    void loadInitialData()
  }, [loadInitialData])

  const refreshBalances = useCallback(async () => {
    const balances = await getAccountBalance()
    dispatch({ type: 'UPSERT_BALANCES', payload: balances })
  }, [])

  const refreshPositions = useCallback(async () => {
    const positions = await getPositions()
    dispatch({ type: 'SET_STATE', payload: { positions, lastUpdated: new Date().toISOString() } })
  }, [])

  const refreshOrders = useCallback(async (filters?: OrderFilters) => {
    const orders = await getOrderHistory(filters)
    dispatch({ type: 'SET_STATE', payload: { orders, lastUpdated: new Date().toISOString() } })
  }, [])

  const refreshTrades = useCallback(async (filters?: TradeFilters) => {
    const trades = await getTradeHistory(filters)
    dispatch({ type: 'SET_STATE', payload: { trades, lastUpdated: new Date().toISOString() } })
  }, [])

  const refreshPerformance = useCallback(
    async (range: PerformanceRange) => {
      const performance = await getPerformanceMetrics(range)
      dispatch({
        type: 'SET_STATE',
        payload: { performance, performanceRange: range, lastUpdated: new Date().toISOString() },
      })
    },
    [],
  )

  const refreshAssetHistory = useCallback(
    async (range: TimeRange) => {
      const assetHistory = await getAssetHistory(range)
      dispatch({
        type: 'SET_STATE',
        payload: { assetHistory, assetHistoryRange: range, lastUpdated: new Date().toISOString() },
      })
    },
    [],
  )

  const refreshTradeStats = useCallback(async (filters?: TradeFilters) => {
    const tradeStats = await getTradeStatistics(filters)
    dispatch({ type: 'SET_STATE', payload: { tradeStats, lastUpdated: new Date().toISOString() } })
  }, [])

  const refreshStrategies = useCallback(async () => {
    const strategies = await getStrategies()
    dispatch({ type: 'SET_STRATEGIES', payload: strategies })
  }, [])

  const refreshRisk = useCallback(async () => {
    const risk = await getRiskMetrics()
    setRiskCache(risk)
    dispatch({ type: 'SET_RISK', payload: risk })
  }, [setRiskCache])

  const refreshNotifications = useCallback(async () => {
    const notifications = await getNotifications()
    dispatch({ type: 'SET_NOTIFICATIONS', payload: notifications })
  }, [])

  const refreshAll = useCallback(async () => {
    setLoading(true)
    try {
      await Promise.all([
        refreshBalances(),
        refreshPositions(),
        refreshOrders(),
        refreshTrades(),
        refreshPerformance(state.performanceRange),
        refreshAssetHistory(state.assetHistoryRange),
        refreshTradeStats(),
        refreshStrategies(),
        refreshRisk(),
        refreshNotifications(),
      ])
      setError(null)
      dispatch({ type: 'SET_STATE', payload: { lastUpdated: new Date().toISOString() } })
    } catch (error) {
      setError((error as Error)?.message ?? '刷新账户数据失败')
    } finally {
      setLoading(false)
    }
  }, [
    refreshAssetHistory,
    refreshBalances,
    refreshNotifications,
    refreshOrders,
    refreshPerformance,
    refreshPositions,
    refreshRisk,
    refreshStrategies,
    refreshTradeStats,
    refreshTrades,
    setError,
    setLoading,
    state.assetHistoryRange,
    state.performanceRange,
  ])

  const toggleStrategyStatus = useCallback(
    async (strategyId: string) => {
      const strategy = state.strategies.find((item) => item.id === strategyId)
      const nextStatus: Strategy['status'] = strategy?.status === 'running' ? 'stopped' : 'running'
      const updatedStrategies = await updateStrategyStatus(strategyId, nextStatus)
      dispatch({ type: 'SET_STRATEGIES', payload: updatedStrategies })
    },
    [state.strategies],
  )

  const markNotificationRead = useCallback(
    (notificationId: string) => {
      dispatch({ type: 'MARK_NOTIFICATION', payload: { id: notificationId, read: true } })
      void acknowledgeNotification(notificationId)
    },
    [],
  )

  const clearNotifications = useCallback(() => {
    dispatch({ type: 'SET_NOTIFICATIONS', payload: [] })
  }, [])

  const updateRiskAlert = useCallback(
    (alertId: string, enabled: boolean) => {
      if (!state.risk) return
      const nextRisk: RiskMetrics = {
        ...state.risk,
        alerts: state.risk.alerts.map((alert) =>
          alert.id === alertId
            ? {
                ...alert,
                enabled,
              }
            : alert,
        ),
      }
      setRiskCache(nextRisk)
      dispatch({ type: 'SET_RISK', payload: nextRisk })
    },
    [setRiskCache, state.risk],
  )

  const handleRealtimeMessage = useCallback(
    (message: RealtimeMessage) => {
      switch (message.type) {
        case 'balance_update':
          dispatch({ type: 'UPSERT_BALANCES', payload: message.payload })
          break
        case 'position_update':
          dispatch({ type: 'UPSERT_POSITION', payload: message.payload })
          break
        case 'order_update':
          dispatch({ type: 'UPSERT_ORDER', payload: message.payload })
          break
        case 'trade_update':
          dispatch({ type: 'UPSERT_TRADE', payload: message.payload })
          break
        case 'risk_update':
          setRiskCache(message.payload)
          dispatch({ type: 'SET_RISK', payload: message.payload })
          break
        case 'notification':
          dispatch({ type: 'ADD_NOTIFICATION', payload: message.payload })
          break
        default:
          break
      }
    },
    [setRiskCache],
  )

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL
    if (!wsUrl || typeof window === 'undefined') {
      return
    }
    const client = new WebSocketClient(wsUrl)
    client.on('message', (data) => {
      if (data && typeof data === 'object' && 'type' in data) {
        handleRealtimeMessage(data as RealtimeMessage)
      }
    })
    client.connect()

    return () => {
      client.disconnect()
    }
  }, [handleRealtimeMessage])

  const contextValue = useMemo<AccountContextValue>(
    () => ({
      ...state,
      refreshAll,
      refreshBalances,
      refreshPositions,
      refreshOrders,
      refreshTrades,
      refreshPerformance,
      refreshAssetHistory,
      refreshTradeStats,
      toggleStrategyStatus,
      markNotificationRead,
      clearNotifications,
      updateRiskAlert,
    }),
    [
      state,
      refreshAll,
      refreshAssetHistory,
      refreshBalances,
      refreshOrders,
      refreshPerformance,
      refreshPositions,
      refreshTradeStats,
      refreshTrades,
      toggleStrategyStatus,
      markNotificationRead,
      clearNotifications,
      updateRiskAlert,
    ],
  )

  return <AccountContext.Provider value={contextValue}>{children}</AccountContext.Provider>
}

export const useAccount = (): AccountContextValue => {
  const context = useContext(AccountContext)
  if (!context) {
    throw new Error('useAccount must be used within an AccountProvider')
  }
  return context
}
