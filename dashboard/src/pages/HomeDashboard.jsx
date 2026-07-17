import React from 'react'
import { useNavigate } from 'react-router-dom'

export default function HomeDashboard() {
  const navigate = useNavigate()

  return (
    <div className="home-dashboard">
      <div className="page-header">
        <div>
          <h1 className="page-title">Institutional Trading Hub</h1>
          <div className="page-subtitle">SwingIQ Multi-Asset Execution Terminal</div>
        </div>
      </div>
      
      <div className="dashboard-welcome-grid">
        <div className="welcome-card" onClick={() => navigate('/')}>
          <div className="welcome-card-header">
            <span className="welcome-icon">◈</span>
            <h3>Recommendation Scanner</h3>
          </div>
          <p>Production equity swing trading engine. Evaluates underlying stocks, displays scanner analytics, entry, targets, and active trade recommendations.</p>
          <span className="welcome-action-link">Open Scanner Terminal →</span>
        </div>

        <div className="welcome-card" onClick={() => navigate('/fo-trading')}>
          <div className="welcome-card-header">
            <span className="welcome-icon">⚡</span>
            <h3>F&O Trading</h3>
          </div>
          <p>Indian Index F&O execution module. Real-time options tracking, market regimes, dynamic risk thresholds, and algorithmic options strategies.</p>
          <span className="welcome-action-link">Open F&O Dashboard →</span>
        </div>
      </div>
    </div>
  )
}
