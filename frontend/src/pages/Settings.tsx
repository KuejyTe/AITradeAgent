import { useEffect, useMemo, useState } from 'react'
import Editor from '@monaco-editor/react'
import './Settings.css'

const API_PREFIX = '/api/v1/config'

type ApiStatus = {
  configured: boolean
  api_key_preview?: string | null
  reason?: string
  updated_at?: string
}

type NotificationConfig = {
  price_alerts: boolean
  order_updates: boolean
  email?: string | null
  telegram?: {
    bot_token?: string | null
    chat_id?: string | null
  }
  wechat_webhook?: string | null
}

type SystemConfig = {
  app_name: string
  environment: string
  debug: boolean
  default_trade_amount: number
  max_position_size: number
  risk_percentage: number
  slippage_tolerance: number
  log_level: string
  okx_api_configured: boolean
  database_configured: boolean
  notifications: NotificationConfig
  last_updated?: string
}

type StrategyOption = {
  id: string
  label: string
}

const STRATEGY_OPTIONS: StrategyOption[] = [
  { id: 'sma_crossover', label: 'SMA Crossover' },
]

const defaultApiKeys = { api_key: '', secret_key: '', passphrase: '' }

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail || body.message || detail
    } catch (_) {
      // ignore JSON parse error
    }
    throw new Error(detail)
  }
  return response.json() as Promise<T>
}

export default function Settings(): JSX.Element {
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null)
  const [apiStatus, setApiStatus] = useState<ApiStatus>({ configured: false })
  const [apiKeys, setApiKeys] = useState(defaultApiKeys)
  const [savingApi, setSavingApi] = useState(false)
  const [savingSystem, setSavingSystem] = useState(false)
  const [testingApi, setTestingApi] = useState(false)
  const [strategyId, setStrategyId] = useState<string>('sma_crossover')
  const [strategyConfig, setStrategyConfig] = useState<string>('')
  const [strategySaving, setStrategySaving] = useState(false)
  const [strategyError, setStrategyError] = useState<string | null>(null)

  useEffect(() => {
    void loadInitialData()
  }, [])

  useEffect(() => {
    if (strategyId) {
      void loadStrategy(strategyId)
    }
  }, [strategyId])

  const riskPercentageDisplay = useMemo(() => {
    if (!systemConfig) return 0
    return Number((systemConfig.risk_percentage * 100).toFixed(2))
  }, [systemConfig])

  async function loadInitialData(): Promise<void> {
    try {
      const [config, status] = await Promise.all([
        fetchJSON<SystemConfig>(`${API_PREFIX}/system`),
        fetchJSON<ApiStatus>(`${API_PREFIX}/api-keys/status`),
      ])
      setSystemConfig(config)
      setApiStatus(status)
    } catch (error) {
      console.error(error)
      window.alert('加载系统配置失败，请稍后再试。')
    }
  }

  async function loadStrategy(id: string): Promise<void> {
    try {
      const config = await fetchJSON<Record<string, unknown>>(`${API_PREFIX}/strategies/${id}`)
      setStrategyError(null)
      setStrategyConfig(JSON.stringify(config, null, 2))
    } catch (error) {
      console.error(error)
      setStrategyError('加载策略配置失败')
    }
  }

  async function handleSaveApiKeys(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setSavingApi(true)
    try {
      await fetchJSON(`${API_PREFIX}/api-keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiKeys),
      })
      setApiKeys(defaultApiKeys)
      await loadInitialData()
      window.alert('API 密钥保存成功')
    } catch (error) {
      console.error(error)
      window.alert(`保存失败：${(error as Error).message}`)
    } finally {
      setSavingApi(false)
    }
  }

  async function handleTestConnection(): Promise<void> {
    setTestingApi(true)
    try {
      const result = await fetchJSON<{ message: string }>(`${API_PREFIX}/api-keys/test`, {
        method: 'POST',
      })
      window.alert(result.message || '测试成功')
    } catch (error) {
      console.error(error)
      window.alert(`测试失败：${(error as Error).message}`)
    } finally {
      setTestingApi(false)
    }
  }

  async function handleSaveSystem(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (!systemConfig) return
    setSavingSystem(true)
    const formData = new FormData(event.currentTarget)
    const payload = {
      default_trade_amount: Number(formData.get('default_trade_amount')),
      max_position_size: Number(formData.get('max_position_size')),
      risk_percentage: Number(formData.get('risk_percentage')) / 100,
      slippage_tolerance: Number(formData.get('slippage_tolerance')),
      log_level: String(formData.get('log_level')),
      notifications: {
        price_alerts: formData.get('price_alerts') === 'on',
        order_updates: formData.get('order_updates') === 'on',
        email: formData.get('email') || null,
        telegram: {
          bot_token: formData.get('telegram_bot_token') || null,
          chat_id: formData.get('telegram_chat_id') || null,
        },
        wechat_webhook: formData.get('wechat_webhook') || null,
      },
    }

    try {
      const updated = await fetchJSON<SystemConfig>(`${API_PREFIX}/system`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      setSystemConfig(updated)
      window.alert('系统配置已保存')
    } catch (error) {
      console.error(error)
      window.alert(`保存失败：${(error as Error).message}`)
    } finally {
      setSavingSystem(false)
    }
  }

  async function handleStrategySave(): Promise<void> {
    setStrategySaving(true)
    setStrategyError(null)
    try {
      const parsed = JSON.parse(strategyConfig)
      await fetchJSON(`${API_PREFIX}/strategies/${strategyId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsed),
      })
      window.alert('策略配置已保存')
    } catch (error) {
      console.error(error)
      setStrategyError((error as Error).message)
    } finally {
      setStrategySaving(false)
    }
  }

  async function handleStrategyReset(): Promise<void> {
    await loadStrategy(strategyId)
    window.alert('已加载默认配置')
  }

  const showApiConfigured = apiStatus.configured && apiStatus.api_key_preview

  return (
    <div className="settings-page">
      <h1>系统设置</h1>

      <section className="card">
        <header>
          <h2>API 配置</h2>
          <p>配置 OKX API 密钥。密钥将使用 ENCRYPTION_KEY 进行加密存储。</p>
        </header>

        {showApiConfigured ? (
          <p className="status success">
            已配置 API Key：<strong>{apiStatus.api_key_preview}</strong>
            {apiStatus.updated_at ? `（更新于 ${new Date(apiStatus.updated_at).toLocaleString()}）` : ''}
          </p>
        ) : (
          <p className="status warning">未检测到已保存的 API 密钥。</p>
        )}

        {apiStatus.reason && <p className="status warning">{apiStatus.reason}</p>}

        <form className="form-grid" onSubmit={handleSaveApiKeys}>
          <label>
            <span>API Key</span>
            <input
              required
              name="api_key"
              type="password"
              placeholder="输入 API Key"
              value={apiKeys.api_key}
              onChange={(event) => setApiKeys((prev) => ({ ...prev, api_key: event.target.value }))}
            />
          </label>

          <label>
            <span>Secret Key</span>
            <input
              required
              name="secret_key"
              type="password"
              placeholder="输入 Secret Key"
              value={apiKeys.secret_key}
              onChange={(event) => setApiKeys((prev) => ({ ...prev, secret_key: event.target.value }))}
            />
          </label>

          <label>
            <span>Passphrase</span>
            <input
              required
              name="passphrase"
              type="password"
              placeholder="输入 Passphrase"
              value={apiKeys.passphrase}
              onChange={(event) => setApiKeys((prev) => ({ ...prev, passphrase: event.target.value }))}
            />
          </label>

          <div className="actions">
            <button type="submit" disabled={savingApi}>
              {savingApi ? '保存中…' : '保存 API 密钥'}
            </button>
            <button type="button" onClick={handleTestConnection} disabled={testingApi || !apiStatus.configured}>
              {testingApi ? '测试中…' : '测试连接'}
            </button>
          </div>
        </form>

        <aside className="tips">
          <h3>安全提示</h3>
          <ul>
            <li>仅为 API Key 授予交易与读取权限，禁止提现权限。</li>
            <li>配置 IP 白名单限制访问来源。</li>
            <li>定期轮换 API Key 并在此处更新。</li>
            <li>不要在代码仓库中提交明文密钥。</li>
          </ul>
        </aside>
      </section>

      {systemConfig && (
        <section className="card">
          <header>
            <h2>交易与通知配置</h2>
            <p>调整默认资金参数与通知偏好。</p>
          </header>

          <form className="form-grid" onSubmit={handleSaveSystem}>
            <label>
              <span>默认交易金额 (USDT)</span>
              <input
                required
                min={1}
                step={1}
                name="default_trade_amount"
                type="number"
                defaultValue={systemConfig.default_trade_amount}
              />
            </label>

            <label>
              <span>最大持仓 (USDT)</span>
              <input
                required
                min={1}
                step={1}
                name="max_position_size"
                type="number"
                defaultValue={systemConfig.max_position_size}
              />
            </label>

            <label>
              <span>风险百分比 (%)</span>
              <input
                required
                min={0.01}
                max={100}
                step={0.01}
                name="risk_percentage"
                type="number"
                defaultValue={riskPercentageDisplay}
              />
            </label>

            <label>
              <span>滑点容忍度</span>
              <input
                required
                min={0}
                step={0.0001}
                name="slippage_tolerance"
                type="number"
                defaultValue={systemConfig.slippage_tolerance}
              />
            </label>

            <label>
              <span>日志级别</span>
              <select name="log_level" defaultValue={systemConfig.log_level}>
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
              </select>
            </label>

            <fieldset className="checkbox">
              <legend>通知设置</legend>
              <label className="inline">
                <input
                  type="checkbox"
                  name="price_alerts"
                  defaultChecked={systemConfig.notifications.price_alerts}
                />
                价格告警
              </label>
              <label className="inline">
                <input
                  type="checkbox"
                  name="order_updates"
                  defaultChecked={systemConfig.notifications.order_updates}
                />
                订单通知
              </label>
              <label>
                <span>通知邮箱</span>
                <input
                  name="email"
                  type="email"
                  placeholder="your@email.com"
                  defaultValue={systemConfig.notifications.email || ''}
                />
              </label>
              <label>
                <span>Telegram Bot Token</span>
                <input
                  name="telegram_bot_token"
                  defaultValue={systemConfig.notifications.telegram?.bot_token || ''}
                />
              </label>
              <label>
                <span>Telegram Chat ID</span>
                <input
                  name="telegram_chat_id"
                  defaultValue={systemConfig.notifications.telegram?.chat_id || ''}
                />
              </label>
              <label>
                <span>微信通知 Webhook</span>
                <input
                  name="wechat_webhook"
                  defaultValue={systemConfig.notifications.wechat_webhook || ''}
                />
              </label>
            </fieldset>

            <div className="actions">
              <button type="submit" disabled={savingSystem}>
                {savingSystem ? '保存中…' : '保存配置'}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="card">
        <header>
          <h2>策略配置编辑器</h2>
          <p>使用 JSON 编辑策略参数。保存前会执行服务器端校验。</p>
        </header>

        <div className="strategy-controls">
          <label>
            策略选择
            <select value={strategyId} onChange={(event) => setStrategyId(event.target.value)}>
              {STRATEGY_OPTIONS.map((strategy) => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.label}
                </option>
              ))}
            </select>
          </label>
          <div className="actions">
            <button type="button" onClick={handleStrategySave} disabled={strategySaving}>
              {strategySaving ? '保存中…' : '保存并应用'}
            </button>
            <button type="button" onClick={handleStrategyReset} disabled={strategySaving}>
              恢复默认配置
            </button>
          </div>
        </div>

        {strategyError && <p className="status warning">{strategyError}</p>}

        <div className="editor-container">
          <Editor
            height="400px"
            language="json"
            theme="vs-dark"
            value={strategyConfig}
            options={{ minimap: { enabled: false }, scrollBeyondLastLine: false }}
            onChange={(value) => setStrategyConfig(value ?? '')}
          />
        </div>
      </section>
    </div>
  )
}

