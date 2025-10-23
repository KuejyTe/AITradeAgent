import React from 'react'

const Dashboard = () => {
  return (
    <div className="dashboard">
      <h1>Trading Dashboard</h1>
      <div className="dashboard-grid">
        <div className="card">
          <h3>Portfolio Value</h3>
          <p className="value">$0.00</p>
        </div>
        <div className="card">
          <h3>Active Trades</h3>
          <p className="value">0</p>
        </div>
        <div className="card">
          <h3>P&L Today</h3>
          <p className="value">$0.00</p>
        </div>
        <div className="card">
          <h3>Win Rate</h3>
          <p className="value">0%</p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
