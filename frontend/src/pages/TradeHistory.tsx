import { useMemo, useState } from 'react'
import { useAccount } from '../context/AccountContext'
import { TradeFilters } from '../types/account'
import { downloadCSV } from '../utils/export'
import { formatCurrency, formatDateTime, formatNumber } from '../utils/format'

const PAGE_SIZE = 12

const SIDE_LABELS = {
  BUY: '买入',
  SELL: '卖出',
}

const TradeHistory: React.FC = () => {
  const { trades, refreshTrades, tradeStats, loading } = useAccount()
  const [filters, setFilters] = useState<TradeFilters>({})
  const [currentPage, setCurrentPage] = useState(1)

  const symbols = useMemo(() => ['ALL', ...new Set(trades.map((trade) => trade.symbol))], [trades])

  const sortedTrades = useMemo(
    () =>
      [...trades].sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
      ),
    [trades],
  )

  const totalPages = Math.max(1, Math.ceil(sortedTrades.length / PAGE_SIZE))
  const paginatedTrades = sortedTrades.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const applyFilters = async () => {
    setCurrentPage(1)
    await refreshTrades(filters)
  }

  const resetFilters = async () => {
    setFilters({})
    setCurrentPage(1)
    await refreshTrades({})
  }

  const quickSelect = async (days: number) => {
    const start = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString()
    const nextFilters = { ...filters, start }
    setFilters(nextFilters)
    setCurrentPage(1)
    await refreshTrades(nextFilters)
  }

  const exportCsv = () => {
    downloadCSV(
      `trade-history-${Date.now()}.csv`,
      sortedTrades.map((trade) => ({
        成交时间: formatDateTime(trade.timestamp),
        交易对: trade.symbol,
        方向: SIDE_LABELS[trade.side],
        成交价格: trade.price,
        成交数量: trade.quantity,
        手续费: trade.fee,
        关联订单: trade.orderId,
      })),
    )
  }

  return (
    <div className="page trade-history">
      <section className="card">
        <header className="card-header">
          <div>
            <h2>成交记录</h2>
            <p>明细查询、统计汇总与 CSV 导出</p>
          </div>
          <div className="card-actions">
            <button className="secondary" onClick={() => void quickSelect(7)}>
              最近 7 天
            </button>
            <button className="secondary" onClick={() => void quickSelect(30)}>
              最近 30 天
            </button>
            <button onClick={exportCsv}>导出 CSV</button>
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
            方向
            <select
              value={filters.side ?? 'ALL'}
              onChange={(event) => setFilters((prev) => ({ ...prev, side: event.target.value === 'ALL' ? undefined : (event.target.value as TradeFilters['side']) }))}
            >
              <option value="ALL">全部</option>
              <option value="BUY">买入</option>
              <option value="SELL">卖出</option>
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
              应用筛选
            </button>
            <button className="secondary" onClick={() => void resetFilters()} disabled={loading}>
              重置
            </button>
          </div>
        </div>

        <div className="stats-row">
          <div>
            <span>总成交额</span>
            <strong>{formatCurrency(tradeStats?.totals.volume ?? 0)}</strong>
          </div>
          <div>
            <span>累计手续费</span>
            <strong>{formatCurrency(tradeStats?.totals.fees ?? 0)}</strong>
          </div>
          <div>
            <span>成交笔数</span>
            <strong>{sortedTrades.length}</strong>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>成交时间</th>
                <th>交易对</th>
                <th>方向</th>
                <th>成交价格</th>
                <th>成交数量</th>
                <th>手续费</th>
                <th>关联订单</th>
              </tr>
            </thead>
            <tbody>
              {paginatedTrades.map((trade) => (
                <tr key={trade.id}>
                  <td>{formatDateTime(trade.timestamp)}</td>
                  <td>{trade.symbol}</td>
                  <td>{SIDE_LABELS[trade.side]}</td>
                  <td>{formatCurrency(trade.price)}</td>
                  <td>{formatNumber(trade.quantity)}</td>
                  <td>{formatCurrency(trade.fee)}</td>
                  <td>
                    <button className="link-button" onClick={() => window.alert(`查看订单 ${trade.orderId}`)}>
                      {trade.orderId}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <footer className="pagination">
          <button onClick={() => setCurrentPage((page) => Math.max(1, page - 1))} disabled={currentPage === 1}>
            上一页
          </button>
          <span>
            第 {currentPage} / {totalPages} 页
          </span>
          <button onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))} disabled={currentPage === totalPages}>
            下一页
          </button>
        </footer>
      </section>
    </div>
  )
}

export default TradeHistory
