import AccountOverview from '../components/account/AccountOverview'
import AssetChart from '../components/account/AssetChart'
import BalanceList from '../components/account/BalanceList'
import NotificationCenter from '../components/account/NotificationCenter'
import PerformanceStats from '../components/account/PerformanceStats'
import PositionList from '../components/account/PositionList'
import RiskMonitor from '../components/account/RiskMonitor'
import StrategyManager from '../components/account/StrategyManager'
import TradeAnalytics from '../components/account/TradeAnalytics'
import { useAccount } from '../context/AccountContext'

const AccountDashboard: React.FC = () => {
  const { loading } = useAccount()

  return (
    <div className="page account-dashboard">
      {loading ? <div className="page-loading">数据同步中...</div> : null}
      <div className="dashboard-grid">
        <AccountOverview />
        <BalanceList />
        <PositionList />
      </div>
      <div className="dashboard-grid two-columns">
        <AssetChart />
        <PerformanceStats />
      </div>
      <TradeAnalytics />
      <div className="dashboard-grid two-columns">
        <StrategyManager />
        <RiskMonitor />
      </div>
      <NotificationCenter />
    </div>
  )
}

export default AccountDashboard
