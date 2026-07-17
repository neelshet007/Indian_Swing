import React from 'react'

const INDICES = ['NIFTY', 'BANKNIFTY', 'SENSEX', 'FINNIFTY', 'MIDCPNIFTY']

export default function MonitoringToolbar({
  monitoringMode,
  selectedIndices,
  isMonitoring,
  startMonitoring,
  stopMonitoring,
  changeMode,
  selectSingleIndex,
  toggleMultiIndex
}) {
  return (
    <div className="monitoring-toolbar" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* Row 1: Mode Selector and Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Monitoring Mode:</span>
          <div style={{ display: 'flex', gap: '16px' }}>
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', cursor: 'pointer' }}>
              <input
                type="radio"
                name="monitoring-mode"
                value="single"
                checked={monitoringMode === 'single'}
                onChange={() => changeMode('single')}
                disabled={isMonitoring}
                style={{ cursor: 'pointer' }}
              />
              Single Index
            </label>
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', cursor: 'pointer' }}>
              <input
                type="radio"
                name="monitoring-mode"
                value="multi"
                checked={monitoringMode === 'multi'}
                onChange={() => changeMode('multi')}
                disabled={isMonitoring}
                style={{ cursor: 'pointer' }}
              />
              Multi Index
            </label>
          </div>
        </div>

        {/* Start / Stop Controls */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className={`btn btn-primary ${isMonitoring ? 'pulse' : ''}`}
            onClick={startMonitoring}
            disabled={isMonitoring}
            style={{ padding: '8px 20px', fontSize: '0.85rem', background: isMonitoring ? 'rgba(79, 142, 247, 0.2)' : 'var(--accent-blue)' }}
          >
            Start Monitoring
          </button>
          <button
            className="btn btn-ghost"
            onClick={stopMonitoring}
            disabled={!isMonitoring}
            style={{ padding: '8px 20px', fontSize: '0.85rem', color: !isMonitoring ? 'var(--text-muted)' : 'var(--accent-red)', borderColor: !isMonitoring ? 'var(--border)' : 'rgba(239, 68, 68, 0.4)' }}
          >
            Stop Monitoring
          </button>
        </div>
      </div>

      {/* Row 2: Index Selector */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px', display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
          {monitoringMode === 'single' ? 'Select Index:' : 'Select Indices:'}
        </span>
        
        {monitoringMode === 'single' ? (
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {INDICES.map(symbol => {
              const active = selectedIndices.includes(symbol)
              return (
                <button
                  key={symbol}
                  className={`btn ${active ? 'btn-primary' : 'btn-ghost'}`}
                  disabled={isMonitoring}
                  onClick={() => selectSingleIndex(symbol)}
                  style={{ padding: '6px 14px', borderRadius: '4px', fontSize: '0.8rem' }}
                >
                  {symbol}
                </button>
              )
            })}
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            {INDICES.map(symbol => {
              const checked = selectedIndices.includes(symbol)
              return (
                <label key={symbol} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', cursor: isMonitoring ? 'not-allowed' : 'pointer', opacity: isMonitoring ? 0.7 : 1 }}>
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={isMonitoring}
                    onChange={() => toggleMultiIndex(symbol)}
                    style={{ cursor: isMonitoring ? 'not-allowed' : 'pointer' }}
                  />
                  {symbol}
                </label>
              )
            })}
          </div>
        )}
      </div>

    </div>
  )
}
