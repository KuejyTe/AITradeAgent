import { useMemo } from 'react'
import { useAccount } from '../../context/AccountContext'
import { PerformanceRange } from '../../types/account'
import { formatNumber, formatPercent, formatSigned } from '../../utils/format'

const RANGE_OPTIONS: { label: string; value: PerformanceRange }[] = [
  { label: '今日', value: 'TODAY' },
  { label: '本周', value: 'WEEK' },
  { label: '本月', value: 'MONTH' },
  { label: '本年', value: 'YEAR' },
  { label: '全部', value: 'ALL' },
]

const PerformanceStats: React.FC = () => {
  const { performance, performanceRange, refreshPerformance } = useAccount()

  const distribution = useMemo(
    () => [
      {
        title: '总收益率',
        value: performance ? formatPercent(performance.totalReturn) : '--',
        description: '账户总收益表现',
      },
      {
        title: '年化收益率',
        value: performance ? formatPercent(performance.annualizedReturn) : '--',
        description: '按年折算的收益率',
      },
      {
        title: '最大回撤',
        value: performance ? formatPercent(performance.maxDrawdown) : '--',
        description: '本周期内的最大回撤幅度',
      },
      {
        title: '夏普比率',
        value: performance ? formatNumber(performance.sharpeRatio, 2) : '--',
        description: '收益风险比评价指标',
      },
    ],
    [performance],
  )

  const tradeStats = useMemo(
    () => [
      {
        label: '总成交次数',
        value: performance ? formatNumber(performance.totalTrades, 0) : '--',
      },
      {
        label: '盈利次数',
        value: performance ? formatNumber(performance.winningTrades, 0) : '--',
      },
      {
        label: '亏损次数',
        value: performance ? formatNumber(performance.losingTrades, 0) : '--',
      },
      {
        label: '胜率',
        value: performance ? formatPercent(performance.winRate) : '--',
      },
      {
        label: '平均盈利',
        value: performance ? formatSigned(performance.averageWin) : '--',
      },
      {
        label: '平均亏损',
        value: performance ? formatSigned(performance.averageLoss) : '--',
      },
    ],
    [performance],
  )

  return (
    <section className="card performance-stats">
      <header className="card-header">
        <div>
          <h2>绩效统计</h2>
          <p>关键指标卡片展示策略表现</p>
        </div>
        <div className="range-switcher">
          {RANGE_OPTIONS.map((option) => (
            <button
              key={option.value}
              className={option.value === performanceRange ? 'active' : ''}
              onClick={() => {
                if (option.value !== performanceRange) {
                  void refreshPerformance(option.value)
                }
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      </header>

      <div className="metrics-grid">
        {distribution.map((metric) => (
          <div className="metric-card" key={metric.title}>
            <span className="metric-title">{metric.title}</span>
            <span className="metric-value large">{metric.value}</span>
            <span className="metric-subtitle">{metric.description}</span>
          </div>
        ))}
      </div>

      <div className="stats-grid">
        {tradeStats.map((stat) => (
          <div className="stat-item" key={stat.label}>
            <strong>{stat.value}</strong>
            <span>{stat.label}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

export default PerformanceStats
