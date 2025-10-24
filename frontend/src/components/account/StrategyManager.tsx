import { useCallback } from 'react'
import { useAccount } from '../../context/AccountContext'
import { formatCurrency, formatPercent } from '../../utils/format'

const StrategyManager: React.FC = () => {
  const { strategies, toggleStrategyStatus } = useAccount()

  const handleEdit = useCallback((strategyId: string) => {
    window.alert(`打开策略 ${strategyId} 的配置面板`)
  }, [])

  return (
    <section className="card strategy-manager">
      <header className="card-header">
        <div>
          <h2>策略管理</h2>
          <p>查看 AI 策略状态、绩效与控制操作</p>
        </div>
      </header>

      <div className="strategy-grid">
        {strategies.map((strategy) => (
          <div className="strategy-card" key={strategy.id}>
            <div className="strategy-header">
              <div>
                <h3>{strategy.name}</h3>
                <p>{strategy.description}</p>
              </div>
              <span className={`status-badge status-${strategy.status}`}>
                {strategy.status === 'running' ? '运行中' : strategy.status === 'paused' ? '已暂停' : '已停止'}
              </span>
            </div>
            <div className="strategy-body">
              <div>
                <span>累计盈亏</span>
                <strong>{formatCurrency(strategy.pnl)}</strong>
              </div>
              <div>
                <span>胜率</span>
                <strong>{formatPercent(strategy.winRate)}</strong>
              </div>
              <div>
                <span>累计交易</span>
                <strong>{strategy.trades}</strong>
              </div>
            </div>
            <footer>
              <span>最近更新：{new Date(strategy.lastUpdated).toLocaleString()}</span>
              <div className="actions">
                <button className="secondary" onClick={() => handleEdit(strategy.id)}>
                  编辑配置
                </button>
                <button
                  className={strategy.status === 'running' ? 'danger' : 'primary'}
                  onClick={() => void toggleStrategyStatus(strategy.id)}
                >
                  {strategy.status === 'running' ? '停止' : '启动'}
                </button>
              </div>
            </footer>
          </div>
        ))}
      </div>
    </section>
  )
}

export default StrategyManager
