import { useState } from 'react'
import AssetChart from '../components/account/AssetChart'
import PerformanceStats from '../components/account/PerformanceStats'
import TradeAnalytics from '../components/account/TradeAnalytics'
import { useAccount } from '../context/AccountContext'
import { TradeFilters } from '../types/account'

const Performance: React.FC = () => {
  const { refreshTradeStats, loading, trades } = useAccount()
  const [filters, setFilters] = useState<TradeFilters>({})

  const symbols = ['ALL', ...new Set(trades.map((trade) => trade.symbol))]

  const applyFilters = async () => {
    await refreshTradeStats(filters)
  }

  const resetFilters = async () => {
    setFilters({})
    await refreshTradeStats({})
  }

  return (
    <div className="page performance">
      <PerformanceStats />
      <AssetChart />
      <section className="card">
        <header className="card-header">
          <div>
            <h2>交易绩效分析</h2>
            <p>通过多维度组合分析交易行为与策略效果</p>
          </div>
        </header>
        <div className="filters-row">
          <label>
            交易对
            <select
              value={filters.symbol ?? 'ALL'}
              onChange={(event) => setFilters((prev) => ({ ...prev, symbol: event.target.value === 'ALL' ? undefined : event.target.value }))}
            >
              {symbols.map((symbol) => (
                <option value={symbol} key={symbol}>
                  {symbol === 'ALL' ? '全部' : symbol}
                </option>
              ))}
            </select>
          </label>
          <label>
            起始日期
            <input
              type="date"
              value={filters.start ? filters.start.slice(0, 10) : ''}
              onChange={(event) => setFilters((prev) => ({ ...prev, start: event.target.value ? new Date(event.target.value).toISOString() : undefined }))}
            />
          </label>
          <label>
            结束日期
            <input
              type="date"
              value={filters.end ? filters.end.slice(0, 10) : ''}
              onChange={(event) => setFilters((prev) => ({ ...prev, end: event.target.value ? new Date(event.target.value).toISOString() : undefined }))}
            />
          </label>
          <div className="filters-actions">
            <button onClick={() => void applyFilters()} disabled={loading}>
              更新分析
            </button>
            <button className="secondary" onClick={() => void resetFilters()} disabled={loading}>
              重置
            </button>
          </div>
        </div>
      </section>
      <TradeAnalytics />
    </div>
  )
}

export default Performance
