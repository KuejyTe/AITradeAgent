import { useMemo, useState } from 'react'
import { useAccount } from '../context/AccountContext'
import { OrderFilters, OrderStatus } from '../types/account'
import { downloadCSV } from '../utils/export'
import { formatCurrency, formatDateTime, formatNumber } from '../utils/format'

const PAGE_SIZE = 10

const STATUS_LABELS: Record<OrderStatus | 'OPEN', string> = {
  FILLED: '已成交',
  PARTIALLY_FILLED: '部分成交',
  CANCELED: '已取消',
  OPEN: '未成交',
  REJECTED: '已拒绝',
}

const TYPE_LABELS = {
  LIMIT: '限价',
  MARKET: '市价',
  STOP: '止损',
  STOP_LIMIT: '止损限价',
}

const SIDE_LABELS = {
  BUY: '买入',
  SELL: '卖出',
}

const OrderHistory: React.FC = () => {
  const { orders, refreshOrders, loading } = useAccount()
  const [filters, setFilters] = useState<OrderFilters>({ status: 'ALL' })
  const [currentPage, setCurrentPage] = useState(1)

  const symbols = useMemo(() => ['ALL', ...new Set(orders.map((order) => order.symbol))], [orders])

  const sortedOrders = useMemo(
    () =>
      [...orders].sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
      ),
    [orders],
  )

  const totalPages = Math.max(1, Math.ceil(sortedOrders.length / PAGE_SIZE))
  const paginatedOrders = sortedOrders.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const applyFilters = async () => {
    setCurrentPage(1)
    await refreshOrders(filters)
  }

  const resetFilters = async () => {
    const defaultFilters: OrderFilters = { status: 'ALL' }
    setFilters(defaultFilters)
    setCurrentPage(1)
    await refreshOrders(defaultFilters)
  }

  const quickSelect = async (days: number) => {
    const start = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString()
    const nextFilters = { ...filters, start }
    setFilters(nextFilters)
    setCurrentPage(1)
    await refreshOrders(nextFilters)
  }

  const exportCsv = () => {
    downloadCSV(
      `order-history-${Date.now()}.csv`,
      sortedOrders.map((order) => ({
        时间: formatDateTime(order.timestamp),
        交易对: order.symbol,
        类型: TYPE_LABELS[order.type],
        方向: SIDE_LABELS[order.side],
        价格: order.price,
        数量: order.quantity,
        成交数量: order.filledQuantity,
        状态: STATUS_LABELS[order.status] ?? order.status,
      })),
    )
  }

  return (
    <div className="page order-history">
      <section className="card">
        <header className="card-header">
          <div>
            <h2>订单历史</h2>
            <p>支持多条件过滤、分页与导出</p>
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
            状态
            <select
              value={filters.status ?? 'ALL'}
              onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value as OrderFilters['status'] }))}
            >
              <option value="ALL">全部</option>
              <option value="FILLED">已成交</option>
              <option value="PARTIALLY_FILLED">部分成交</option>
              <option value="OPEN">未成交</option>
              <option value="CANCELED">已取消</option>
              <option value="REJECTED">已拒绝</option>
            </select>
          </label>
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
              onChange={(event) => setFilters((prev) => ({ ...prev, side: event.target.value === 'ALL' ? undefined : (event.target.value as OrderFilters['side']) }))}
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

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>交易对</th>
                <th>类型</th>
                <th>方向</th>
                <th>价格</th>
                <th>数量</th>
                <th>成交数量</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {paginatedOrders.map((order) => (
                <tr key={order.id}>
                  <td>{formatDateTime(order.timestamp)}</td>
                  <td>{order.symbol}</td>
                  <td>{TYPE_LABELS[order.type]}</td>
                  <td>{SIDE_LABELS[order.side]}</td>
                  <td>{formatCurrency(order.price)}</td>
                  <td>{formatNumber(order.quantity)}</td>
                  <td>{formatNumber(order.filledQuantity)}</td>
                  <td>
                    <span className={`status-badge status-${order.status.toLowerCase()}`}>
                      {STATUS_LABELS[order.status] ?? order.status}
                    </span>
                  </td>
                  <td>
                    <button className="link-button" onClick={() => window.alert(`查看订单 ${order.id} 详情`)}>
                      查看详情
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

export default OrderHistory
