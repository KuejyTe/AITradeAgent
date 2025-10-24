import { useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import AccountDashboard from './pages/AccountDashboard'
import OrderHistory from './pages/OrderHistory'
import TradeHistory from './pages/TradeHistory'
import Performance from './pages/Performance'
import Monitoring from './pages/Monitoring'
import { useAccount } from './context/AccountContext'
import { apiService } from './services/api'

const App = () => {
  const { loading, error, refreshAll, lastUpdated } = useAccount()
  const [apiStatus, setApiStatus] = useState<'healthy' | 'degraded' | 'error' | 'unknown'>('unknown')
  const [apiMessage, setApiMessage] = useState<string>('正在检测接口连接...')

  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const status = await apiService.healthCheck()
        setApiStatus(status?.status === 'healthy' ? 'healthy' : 'degraded')
        setApiMessage(status?.message ?? 'API 已联通')
      } catch (healthError) {
        console.warn('[app] health check failed', healthError)
        setApiStatus('error')
        setApiMessage('无法连接后端 API，正在使用模拟数据')
      }
    }

    void checkApiHealth()
  }, [])

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand">
          <span className="brand-logo">🤖</span>
          <div>
            <h2>AITradeAgent</h2>
            <p>智能交易账户中心</p>
          </div>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/account" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            账户总览
          </NavLink>
          <NavLink to="/orders" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            订单历史
          </NavLink>
          <NavLink to="/trades" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            成交记录
          </NavLink>
          <NavLink to="/performance" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            绩效分析
          </NavLink>
          <NavLink to="/monitoring" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            系统监控
          </NavLink>
        </nav>
        <div className="sidebar-status">
          <div className={`status-dot status-${apiStatus}`} />
          <div>
            <strong>API 状态</strong>
            <p>{apiMessage}</p>
          </div>
        </div>
        <button className="refresh-button" onClick={() => void refreshAll()} disabled={loading}>
          {loading ? '同步中...' : '立即刷新'}
        </button>
      </aside>
      <div className="app-content">
        <header className="app-header">
          <div>
            <h1>账户管理中心</h1>
            <p>实时掌握资产、订单、策略与风险信息</p>
          </div>
          <div className="header-extra">
            <span className="last-updated">
              最后更新：{lastUpdated ? new Date(lastUpdated).toLocaleString() : '初始化中'}
            </span>
            {error ? <span className="error-badge">{error}</span> : null}
          </div>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Navigate to="/account" replace />} />
            <Route path="/account" element={<AccountDashboard />} />
            <Route path="/orders" element={<OrderHistory />} />
            <Route path="/trades" element={<TradeHistory />} />
            <Route path="/performance" element={<Performance />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="*" element={<Navigate to="/account" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App
