import { useState, useEffect } from 'react'
import './App.css'
import apiService from './services/api'

function App() {
  const [apiStatus, setApiStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const data = await apiService.healthCheck()
        setApiStatus(data)
      } catch (error) {
        setApiStatus({ status: 'error', message: 'Failed to connect to API' })
      } finally {
        setLoading(false)
      }
    }
    
    checkApiHealth()
  }, [])

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 AITradeAgent</h1>
        <p>AI-Powered Trading Agent Platform</p>
        
        <div className="status-card">
          <h2>System Status</h2>
          {loading ? (
            <p>Checking API connection...</p>
          ) : (
            <div>
              <p>
                API Status: <span className={apiStatus?.status === 'healthy' ? 'status-healthy' : 'status-error'}>
                  {apiStatus?.status || 'Unknown'}
                </span>
              </p>
              <p>{apiStatus?.message}</p>
            </div>
          )}
        </div>

        <div className="info-section">
          <h3>Features</h3>
          <ul>
            <li>Real-time market data analysis</li>
            <li>AI-powered trading strategies</li>
            <li>Portfolio management</li>
            <li>Risk assessment</li>
          </ul>
        </div>
      </header>
    </div>
  )
}

export default App
