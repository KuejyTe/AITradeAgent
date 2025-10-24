import { useMemo } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
} from 'recharts'
import { useAccount } from '../../context/AccountContext'
import { formatCurrency, formatPercent } from '../../utils/format'

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const TradeAnalytics: React.FC = () => {
  const { tradeStats } = useAccount()

  const heatmap = useMemo(() => {
    if (!tradeStats) return { matrix: [], max: 0 }
    const maxTrades = Math.max(...tradeStats.hourlyHeatmap.map((item) => item.trades))
    const matrix = WEEKDAYS.map((_, weekday) =>
      Array.from({ length: 24 }).map((__, hour) =>
        tradeStats.hourlyHeatmap.find((cell) => cell.weekday === weekday && cell.hour === hour) ?? {
          weekday,
          hour,
          trades: 0,
          pnl: 0,
        },
      ),
    )
    return { matrix, max: maxTrades }
  }, [tradeStats])

  if (!tradeStats) {
    return null
  }

  const getHeatColor = (value: number) => {
    if (!heatmap.max) return 'var(--color-surface)' as string
    const ratio = Math.min(1, value / heatmap.max)
    const hue = 200 - ratio * 140
    const lightness = 90 - ratio * 45
    return `hsl(${hue}, 80%, ${lightness}%)`
  }

  return (
    <section className="card trade-analytics">
      <header className="card-header">
        <div>
          <h2>交易分析</h2>
          <p>多维度洞察交易绩效与时段表现</p>
        </div>
        <div className="card-highlight">
          <span>累计成交额</span>
          <strong>{formatCurrency(tradeStats.totals.volume)}</strong>
        </div>
      </header>

      <div className="analytics-grid">
        <div className="chart-card">
          <h3>按交易对分组统计</h3>
          <ResponsiveContainer height={260}>
            <ComposedChart data={tradeStats.byPair} margin={{ top: 16, right: 16, bottom: 8, left: -8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="symbol" />
              <YAxis yAxisId="left" tickFormatter={(value: number) => `${value}`} width={50} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(value: number) => formatPercent(value)} width={60} />
              <Tooltip
                formatter={(value: number, name: string) =>
                  name === 'winRate' ? [formatPercent(value), '胜率'] : [formatCurrency(value), '累计盈亏']
                }
              />
              <Legend />
              <Bar dataKey="pnl" name="累计盈亏" fill="#6366F1" radius={[4, 4, 0, 0]} yAxisId="left" />
              <Line type="monotone" dataKey="winRate" name="胜率" stroke="#F97316" strokeWidth={2} yAxisId="right" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>盈亏分布直方图</h3>
          <ResponsiveContainer height={260}>
            <BarChart data={tradeStats.profitDistribution} margin={{ top: 16, right: 16, bottom: 8, left: -8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="range" />
              <YAxis allowDecimals={false} />
              <Tooltip formatter={(value: number) => [value, '交易次数']} />
              <Bar dataKey="count" name="交易次数" fill="#22D3EE" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>持仓时间分析</h3>
          <ResponsiveContainer height={260}>
            <ComposedChart data={tradeStats.holdingDurations} margin={{ top: 16, right: 16, bottom: 8, left: -8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="bucket" />
              <YAxis yAxisId="left" allowDecimals={false} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(value: number) => formatPercent(value)} width={60} />
              <Tooltip
                formatter={(value: number, name: string) =>
                  name === 'avgPnl' ? [formatPercent(value), '平均收益率'] : [value, '交易次数']
                }
              />
              <Legend />
              <Bar dataKey="count" name="交易次数" fill="#10B981" yAxisId="left" radius={[4, 4, 0, 0]} />
              <Line type="monotone" dataKey="avgPnl" name="平均收益率" stroke="#F472B6" strokeWidth={2} yAxisId="right" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>交易时段热力图</h3>
          <div className="heatmap">
            <div className="heatmap-header">
              <span />
              {Array.from({ length: 24 }).map((_, hour) => (
                <span key={hour}>{hour}</span>
              ))}
            </div>
            {heatmap.matrix.map((row, weekday) => (
              <div className="heatmap-row" key={WEEKDAYS[weekday]}>
                <span className="heatmap-label">{WEEKDAYS[weekday]}</span>
                {row.map((cell) => (
                  <button
                    type="button"
                    className="heatmap-cell"
                    key={`${cell.weekday}-${cell.hour}`}
                    title={`${WEEKDAYS[cell.weekday]} ${cell.hour}:00\n成交次数：${cell.trades}\n平均盈亏：${formatCurrency(cell.pnl)}`}
                    style={{ background: getHeatColor(cell.trades) }}
                  >
                    <span>{cell.trades}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div className="chart-card">
          <h3>策略效果对比</h3>
          <ResponsiveContainer height={260}>
            <ComposedChart data={tradeStats.strategyComparison} margin={{ top: 16, right: 16, bottom: 8, left: -8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="strategy" />
              <YAxis yAxisId="left" tickFormatter={(value: number) => `${Math.round(value / 1000)}k`} width={60} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(value: number) => formatPercent(value)} width={60} />
              <Tooltip
                formatter={(value: number, name: string) =>
                  name === 'winRate'
                    ? [formatPercent(value), '胜率']
                    : name === 'sharpe'
                      ? [value.toFixed(2), '夏普比率']
                      : [formatCurrency(value), '累计盈亏']
                }
              />
              <Legend />
              <Bar dataKey="pnl" name="累计盈亏" fill="#A855F7" yAxisId="left" radius={[4, 4, 0, 0]} />
              <Line type="monotone" dataKey="winRate" name="胜率" stroke="#F97316" strokeWidth={2} yAxisId="right" />
              <Line type="monotone" dataKey="sharpe" name="夏普比率" stroke="#22D3EE" strokeWidth={2} yAxisId="right" strokeDasharray="4 4" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <footer className="card-footer">
        <div>
          <span>累计手续费</span>
          <strong>{formatCurrency(tradeStats.totals.fees)}</strong>
        </div>
        <div>
          <span>策略数量</span>
          <strong>{tradeStats.strategyComparison.length}</strong>
        </div>
      </footer>
    </section>
  )
}

export default TradeAnalytics
