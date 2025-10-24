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
} from 'recharts'
import { useAccount } from '../../context/AccountContext'
import { TimeRange } from '../../types/account'
import { formatCurrency, formatDate } from '../../utils/format'

type RangeOption = {
  label: string
  value: TimeRange
}

const RANGE_OPTIONS: RangeOption[] = [
  { label: '1 天', value: '1D' },
  { label: '1 周', value: '1W' },
  { label: '1 月', value: '1M' },
  { label: '3 月', value: '3M' },
  { label: '半年', value: '6M' },
  { label: '1 年', value: '1Y' },
  { label: '全部', value: 'ALL' },
]

const AssetChart: React.FC = () => {
  const { assetHistory, assetHistoryRange, refreshAssetHistory } = useAccount()

  const chartData = useMemo(
    () =>
      assetHistory.map((point) => ({
        ...point,
        label: assetHistoryRange === '1D' ? new Date(point.timestamp).toLocaleTimeString('zh-CN', { hour12: false }) : formatDate(point.timestamp),
      })),
    [assetHistory, assetHistoryRange],
  )

  const events = useMemo(() => chartData.filter((item) => item.event), [chartData])

  return (
    <section className="card asset-chart">
      <header className="card-header">
        <div>
          <h2>资产趋势</h2>
          <p>资产净值变化与 BTC 价格对比</p>
        </div>
        <div className="range-switcher">
          {RANGE_OPTIONS.map((option) => (
            <button
              key={option.value}
              className={option.value === assetHistoryRange ? 'active' : ''}
              onClick={() => {
                if (option.value !== assetHistoryRange) {
                  void refreshAssetHistory(option.value)
                }
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      </header>

      <div className="chart-container">
        <ResponsiveContainer height={340}>
          <ComposedChart data={chartData} margin={{ top: 16, right: 32, bottom: 8, left: 0 }}>
            <defs>
              <linearGradient id="assetGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366F1" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#6366F1" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="availableGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22D3EE" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#22D3EE" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} interval="preserveStartEnd" minTickGap={20} />
            <YAxis
              yAxisId="asset"
              tickFormatter={(value: number) => `${Math.round(value / 1000)}k`}
              width={60}
            />
            <YAxis
              yAxisId="btc"
              orientation="right"
              tickFormatter={(value: number) => `$${Math.round(value / 1000)}k`}
              width={60}
            />
            <Tooltip
              formatter={(value: number, name: string) => {
                if (name === 'btcPrice') {
                  return [formatCurrency(value), 'BTC 价格']
                }
                if (name === 'available') {
                  return [formatCurrency(value), '可用资产']
                }
                return [formatCurrency(value), '总资产']
              }}
              labelFormatter={(label) => label}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="total"
              name="总资产"
              stroke="#6366F1"
              strokeWidth={2}
              yAxisId="asset"
              fill="url(#assetGradient)"
              activeDot={{ r: 5 }}
            />
            <Area
              type="monotone"
              dataKey="available"
              name="可用资产"
              stroke="#22D3EE"
              strokeWidth={2}
              yAxisId="asset"
              fill="url(#availableGradient)"
            />
            <Line
              type="monotone"
              dataKey="btcPrice"
              name="BTC 价格"
              stroke="#F97316"
              strokeWidth={2}
              yAxisId="btc"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {events.length ? (
        <div className="chart-events">
          <h3>关键事件</h3>
          <ul>
            {events.map((event) => (
              <li key={`${event.timestamp}-${event.event}`}>
                <span>{formatDate(event.timestamp)}</span>
                <span>{event.event}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  )
}

export default AssetChart
