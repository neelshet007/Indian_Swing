import React from 'react'

export default function Settings() {
  return (
    <div className="settings-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Terminal Settings</h1>
          <div className="page-subtitle">Configure API integrations, execution params, and local system configurations</div>
        </div>
      </div>
      
      <div className="settings-container">
        <div className="settings-card">
          <h3>System Settings</h3>
          <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
            Settings module configurations will be available in future releases.
          </div>
        </div>
      </div>
    </div>
  )
}
