import { useAccount } from '../../context/AccountContext'
import { formatPercent } from '../../utils/format'

const RiskMonitor: React.FC = () => {
  const { risk, updateRiskAlert } = useAccount()

  if (!risk) {
    return null
  }

  return (
    <section className="card risk-monitor">
      <header className="card-header">
        <div>
          <h2>风险监控</h2>
          <p>实时监控风险敞口与风控规则触发情况</p>
        </div>
      </header>

      <div className="risk-grid">
        <div className="risk-metric">
          <span>当前风险敞口</span>
          <div className="progress large">
            <div className="progress-bar" style={{ width: `${Math.min(100, risk.currentExposure * 100)}%` }} />
          </div>
          <strong>{formatPercent(risk.currentExposure)}</strong>
          <small>上限 {formatPercent(risk.maxExposure)}</small>
        </div>
        <div className="risk-metric">
          <span>杠杆使用</span>
          <div className="progress large">
            <div className="progress-bar warning" style={{ width: `${Math.min(100, (risk.leverage / risk.maxLeverage) * 100)}%` }} />
          </div>
          <strong>{risk.leverage.toFixed(2)}x</strong>
          <small>最高 {risk.maxLeverage.toFixed(1)}x</small>
        </div>
        <div className="risk-metric">
          <span>保证金占用</span>
          <div className="progress large">
            <div className="progress-bar danger" style={{ width: `${Math.min(100, risk.marginUtilization * 100)}%` }} />
          </div>
          <strong>{formatPercent(risk.marginUtilization)}</strong>
          <small>关注线 60%</small>
        </div>
        <div className="risk-metric">
          <span>VaR (99%)</span>
          <div className="progress large">
            <div className="progress-bar" style={{ width: `${Math.min(100, risk.var * 100)}%` }} />
          </div>
          <strong>{formatPercent(risk.var)}</strong>
          <small>24 小时损失置信区间</small>
        </div>
      </div>

      <div className="risk-events">
        <h3>风控事件</h3>
        <ul>
          {risk.riskEvents.map((event) => (
            <li key={event.id} className={`severity-${event.severity}`}>
              <div>
                <strong>{event.rule}</strong>
                <span>{new Date(event.timestamp).toLocaleString()}</span>
              </div>
              <p>{event.details}</p>
            </li>
          ))}
        </ul>
      </div>

      <div className="risk-alerts">
        <h3>告警设置</h3>
        <ul>
          {risk.alerts.map((alert) => (
            <li key={alert.id}>
              <div>
                <strong>{alert.type.toUpperCase()}</strong>
                <p>{alert.description}</p>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={alert.enabled}
                  onChange={(event) => updateRiskAlert(alert.id, event.target.checked)}
                />
                <span className="slider" />
              </label>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}

export default RiskMonitor
