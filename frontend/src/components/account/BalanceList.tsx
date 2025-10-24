import { useMemo, useState } from 'react'
import { useAccount } from '../../context/AccountContext'
import { formatCurrency, formatNumber, formatPercent } from '../../utils/format'

type SortField = 'asset' | 'available' | 'hold' | 'usdValue' | 'allocation'

type SortDirection = 'asc' | 'desc'

const BalanceList: React.FC = () => {
  const { balance } = useAccount()
  const [sortField, setSortField] = useState<SortField>('usdValue')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const totalUsdValue = useMemo(() => balance.reduce((acc, item) => acc + (item.usdValue ?? 0), 0), [balance])

  const sortedBalances = useMemo(() => {
    const sorted = [...balance]
    sorted.sort((a, b) => {
      const valueA = a[sortField]
      const valueB = b[sortField]

      if (typeof valueA === 'string' && typeof valueB === 'string') {
        return sortDirection === 'asc' ? valueA.localeCompare(valueB) : valueB.localeCompare(valueA)
      }

      const numA = typeof valueA === 'number' ? valueA : 0
      const numB = typeof valueB === 'number' ? valueB : 0
      return sortDirection === 'asc' ? numA - numB : numB - numA
    })
    return sorted
  }, [balance, sortField, sortDirection])

  const handleSort = (field: SortField) => {
    setSortField(field)
    setSortDirection((prev) => (field === sortField ? (prev === 'asc' ? 'desc' : 'asc') : 'desc'))
  }

  const handleAction = (asset: string, type: 'deposit' | 'withdraw') => {
    const message = type === 'deposit' ? `即将跳转到 ${asset} 的充值页面` : `即将跳转到 ${asset} 的提现页面`
    window.alert(message)
  }

  return (
    <section className="card balance-list">
      <header className="card-header">
        <div>
          <h2>余额列表</h2>
          <p>各币种可用及冻结资金明细</p>
        </div>
        <div className="card-highlight">
          <span>资产折合 USD</span>
          <strong>{formatCurrency(totalUsdValue)}</strong>
        </div>
      </header>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('asset')}>币种</th>
              <th onClick={() => handleSort('available')}>可用余额</th>
              <th onClick={() => handleSort('hold')}>冻结余额</th>
              <th onClick={() => handleSort('usdValue')}>USD 估值</th>
              <th onClick={() => handleSort('allocation')}>资产占比</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {sortedBalances.map((item) => {
              const allocation = item.allocation ?? item.usdValue / (totalUsdValue || 1)
              return (
                <tr key={item.asset}>
                  <td>{item.asset}</td>
                  <td>{formatNumber(item.available)}</td>
                  <td>{formatNumber(item.hold)}</td>
                  <td>{formatCurrency(item.usdValue)}</td>
                  <td>
                    <div className="progress">
                      <div className="progress-bar" style={{ width: `${Math.min(100, allocation * 100).toFixed(1)}%` }} />
                      <span>{formatPercent(allocation)}</span>
                    </div>
                  </td>
                  <td className="actions">
                    <button onClick={() => handleAction(item.asset, 'deposit')}>充值</button>
                    <button className="secondary" onClick={() => handleAction(item.asset, 'withdraw')}>
                      提现
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default BalanceList
