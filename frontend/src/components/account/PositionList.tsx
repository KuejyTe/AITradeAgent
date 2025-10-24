import { useMemo, useState } from 'react'
import { useAccount } from '../../context/AccountContext'
import { formatCurrency, formatNumber, formatPercent, formatSigned, getPnlClassName } from '../../utils/format'

const PositionList: React.FC = () => {
  const { positions } = useAccount()
  const [directionFilter, setDirectionFilter] = useState<'ALL' | 'LONG' | 'SHORT'>('ALL')
  const [strategyFilter, setStrategyFilter] = useState<string>('ALL')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortField, setSortField] = useState<'pnlValue' | 'pnlPercent' | 'margin' | 'symbol'>('pnlValue')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  const strategies = useMemo(() => ['ALL', ...new Set(positions.map((item) => item.strategy).filter(Boolean) as string[])], [positions])

  const filtered = useMemo(() => {
    return positions
      .filter((position) =>
        directionFilter === 'ALL' ? true : position.direction === directionFilter,
      )
      .filter((position) =>
        strategyFilter === 'ALL' ? true : position.strategy === strategyFilter,
      )
      .filter((position) =>
        searchTerm
          ? position.symbol.toLowerCase().includes(searchTerm.toLowerCase())
          : true,
      )
  }, [positions, directionFilter, strategyFilter, searchTerm])

  const sortedPositions = useMemo(() => {
    const sorted = [...filtered]
    sorted.sort((a, b) => {
      let valueA: number | string
      let valueB: number | string

      switch (sortField) {
        case 'symbol':
          valueA = a.symbol
          valueB = b.symbol
          if (sortDirection === 'asc') {
            return valueA.localeCompare(valueB)
          }
          return valueB.localeCompare(valueA)
        case 'margin':
          valueA = a.margin
          valueB = b.margin
          break
        case 'pnlPercent':
          valueA = a.pnl.percentage
          valueB = b.pnl.percentage
          break
        case 'pnlValue':
        default:
          valueA = a.pnl.value
          valueB = b.pnl.value
          break
      }

      const numA = typeof valueA === 'number' ? valueA : 0
      const numB = typeof valueB === 'number' ? valueB : 0
      return sortDirection === 'asc' ? numA - numB : numB - numA
    })
    return sorted
  }, [filtered, sortField, sortDirection])

  const handleSort = (field: 'pnlValue' | 'pnlPercent' | 'margin' | 'symbol') => {
    setSortField(field)
    setSortDirection((prev) => (field === sortField ? (prev === 'asc' ? 'desc' : 'asc') : 'desc'))
  }

  const handleClosePosition = (symbol: string) => {
    window.alert(`平仓指令已提交：${symbol}`)
  }

  const handleViewDetail = (symbol: string) => {
    window.alert(`查看持仓详情：${symbol}`)
  }

  return (
    <section className="card position-list">
      <header className="card-header">
        <div>
          <h2>当前持仓</h2>
          <p>支持筛选与排序，实时掌握盈亏情况</p>
        </div>
        <div className="filters">
          <select value={directionFilter} onChange={(event) => setDirectionFilter(event.target.value as typeof directionFilter)}>
            <option value="ALL">全部方向</option>
            <option value="LONG">多头</option>
            <option value="SHORT">空头</option>
          </select>
          <select value={strategyFilter} onChange={(event) => setStrategyFilter(event.target.value)}>
            {strategies.map((strategy) => (
              <option value={strategy} key={strategy}>
                {strategy === 'ALL' ? '全部策略' : strategy}
              </option>
            ))}
          </select>
          <input
            type="search"
            placeholder="搜索交易对"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </div>
      </header>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('symbol')}>交易对</th>
              <th>方向</th>
              <th>持仓量</th>
              <th>开仓均价</th>
              <th>当前价格</th>
              <th onClick={() => handleSort('pnlValue')}>未实现盈亏</th>
              <th onClick={() => handleSort('pnlPercent')}>盈亏%</th>
              <th onClick={() => handleSort('margin')}>已用保证金</th>
              <th>策略</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {sortedPositions.map((position) => (
              <tr key={position.symbol}>
                <td>
                  <button type="button" className="link-button" onClick={() => handleViewDetail(position.symbol)}>
                    {position.symbol}
                  </button>
                </td>
                <td>
                  <span className={`tag ${position.direction === 'LONG' ? 'tag-long' : 'tag-short'}`}>
                    {position.direction === 'LONG' ? '多' : '空'}
                  </span>
                </td>
                <td>{formatNumber(position.size)}</td>
                <td>{formatCurrency(position.entryPrice)}</td>
                <td>{formatCurrency(position.markPrice)}</td>
                <td className={getPnlClassName(position.pnl.value)}>{formatSigned(position.pnl.value)}</td>
                <td className={getPnlClassName(position.pnl.percentage)}>{formatPercent(position.pnl.percentage)}</td>
                <td>{formatCurrency(position.margin)}</td>
                <td>{position.strategy ?? '—'}</td>
                <td className="actions">
                  <button className="danger" onClick={() => handleClosePosition(position.symbol)}>
                    平仓
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default PositionList
