import { useMemo } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { useAccount } from '../../context/AccountContext'
import { formatCurrency, formatPercent, formatSigned } from '../../utils/format'

const PIE_COLORS = ['#6366F1', '#22D3EE', '#F97316', '#10B981', '#F472B6', '#A855F7']

const AccountOverview: React.FC = () => {
  const { balance, performance } = useAccount()

  const summary = useMemo(() => {
    const totals = balance.reduce(
      (acc, item) => {
        const available = typeof item.available === 'number' ? item.available : 0
        const hold = typeof item.hold === 'number' ? item.hold : 0
        const usdValue = typeof item.usdValue === 'number' ? item.usdValue : 0
        acc.available += available
        acc.frozen += hold
        acc.totalUsd += usdValue
        return acc
      },
      { available: 0, frozen: 0, totalUsd: 0 },
    )

    return {
      ...totals,
      pnlToday: performance?.profitLossToday ?? 0,
      pnlTotal: performance?.profitLossTotal ?? 0,
      totalReturn: performance?.totalReturn ?? 0,
    }
  }, [balance, performance])

  const pieData = useMemo(
    () =>
      balance.map((item) => ({
        name: item.asset,
        value: item.usdValue,
        allocation: item.allocation,
      })),
    [balance],
  )

  return (
    <section className="card account-overview">
      <header className="card-header">
        <div>
          <h2>账户概览</h2>
          <p>资产分布与盈亏情况一目了然</p>
        </div>
        <div className="highlight-metric">
          <span className="metric-label">账户总资产</span>
          <strong className="metric-value">{formatCurrency(summary.totalUsd)}</strong>
        </div>
      </header>

      <div className="overview-grid">
        <div className="metrics-grid">
          <div className="metric-card">
            <span className="metric-title">可用余额</span>
            <span className="metric-value">{formatCurrency(summary.available)}</span>
            <span className="metric-subtitle">占比 {formatPercent(summary.available / (summary.totalUsd || 1))}</span>
          </div>
          <div className="metric-card">
            <span className="metric-title">冻结资产</span>
            <span className="metric-value">{formatCurrency(summary.frozen)}</span>
            <span className="metric-subtitle">占比 {formatPercent(summary.frozen / (summary.totalUsd || 1))}</span>
          </div>
          <div className="metric-card">
            <span className="metric-title">今日盈亏</span>
            <span className={`metric-value ${summary.pnlToday >= 0 ? 'pnl-positive' : 'pnl-negative'}`}>
              {formatSigned(summary.pnlToday)}
            </span>
            <span className="metric-subtitle">实时监控策略表现</span>
          </div>
          <div className="metric-card">
            <span className="metric-title">累计盈亏</span>
            <span className={`metric-value ${summary.pnlTotal >= 0 ? 'pnl-positive' : 'pnl-negative'}`}>
              {formatSigned(summary.pnlTotal)}
            </span>
            <span className="metric-subtitle">总收益率 {formatPercent(summary.totalReturn)}</span>
          </div>
        </div>

        <div className="pie-wrapper">
          <h3>资产分布</h3>
          <ResponsiveContainer height={260}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                innerRadius={70}
                outerRadius={100}
                paddingAngle={4}
              >
                {pieData.map((entry, index) => (
                  <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, _name, payload) => [
                  formatCurrency(value),
                  `${payload.payload.name} · ${formatPercent(payload.payload.allocation ?? value / summary.totalUsd)}`,
                ]}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="pie-legend">
            {pieData.map((item, index) => (
              <div className="legend-item" key={item.name}>
                <span className="legend-dot" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                <span>{item.name}</span>
                <strong>{formatPercent(item.allocation ?? item.value / (summary.totalUsd || 1))}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

export default AccountOverview
