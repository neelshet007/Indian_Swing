import React, { useMemo } from 'react'
import MetricCard from '../components/MetricCard'
import SystemStatusCard from '../components/SystemStatusCard'
import TableCard from '../components/TableCard'
import useFnoEngine from '../modules/fno/hooks/useFnoEngine'
import MonitoringToolbar from '../modules/fno/components/MonitoringToolbar'
import MonitoringCard from '../modules/fno/components/MonitoringCard'

export default function FOTrading() {
  const {
    monitoringMode,
    selectedIndices,
    isMonitoring,
    sessions,
    startMonitoring,
    stopMonitoring,
    changeMode,
    selectSingleIndex,
    toggleMultiIndex
  } = useFnoEngine()

  const portfolioMetrics = useMemo(() => [
    { label: 'Open Positions', value: '0', subValue: 'No Active Exposure', trend: 'neutral' },
    { label: "Today's P&L", value: '₹ 0.00', subValue: '0.00%', trend: 'neutral' },
    { label: 'Weekly P&L', value: '₹ 0.00', subValue: '0.00%', trend: 'neutral' },
    { label: 'Capital Used', value: '₹ 0.00', subValue: '0.0% utilization', trend: 'neutral' },
    { label: 'Risk Used', value: '0.0%', subValue: '₹ 0.00 Max Risk', trend: 'neutral' },
    { label: 'Peak Drawdown', value: '0.0%', subValue: 'Daily Peak', trend: 'neutral' }
  ], [])

  const riskMetrics = useMemo(() => [
    { label: 'Portfolio Risk', value: 'LOW', subValue: 'Within parameters', trend: 'neutral' },
    { label: 'Daily Limit', value: '₹ 50,000', subValue: '₹ 50,000 remaining', trend: 'neutral' },
    { label: 'Weekly Limit', value: '₹ 1,50,000', subValue: '₹ 1,50,000 remaining', trend: 'neutral' },
    { label: 'Max Drawdown Limit', value: '2.5%', subValue: '₹ 2,50,000 hard stop', trend: 'neutral' }
  ], [])

  const systemStatus = useMemo(() => [
    { name: 'Data Feed', status: isMonitoring ? 'green' : 'yellow', message: isMonitoring ? 'Active' : 'Standby' },
    { name: 'Broker API', status: 'green', message: 'Token Valid (Expires in 14h)' },
    { name: 'Execution Router', status: 'green', message: 'Idle — Ready to route' },
    { name: 'Risk Engine', status: 'green', message: 'Active — Live margin check' },
    { name: 'Strategy Engine', status: 'green', message: 'Loaded' }
  ], [isMonitoring])

  const dummyOpportunities = useMemo(() => {
    return selectedIndices.map(symbol => ({
      index: symbol,
      expiry: sessions[symbol]?.marketData?.expiry || 'Waiting...',
      status: isMonitoring ? 'WATCHING' : 'INACTIVE',
      signal: 'MONITORING',
      confidence: 'N/A',
      reason: isMonitoring ? 'Analyzing ticks & volatility spreads' : 'Engine stopped'
    }))
  }, [selectedIndices, sessions, isMonitoring])

  const opportunityHeaders = ['Index', 'Expiry', 'Status', 'Signal', 'Confidence', 'Reason']
  const tradeHeaders = ['ID', 'Time', 'Instrument', 'Type', 'Qty', 'Entry', 'Exit', 'P&L', 'Status']

  return (
    <div className="fo-dashboard">
      <div className="page-header">
        <div>
          <h1 className="page-title">F&O Trading Dashboard</h1>
          <div className="page-subtitle">Institutional Index Options Monitoring</div>
        </div>
        <div className="dashboard-status-indicator">
          <span className={isMonitoring ? 'live-pulse' : 'status-dot-indicator status-yellow'} />
          <span className="status-text">Monitoring: {isMonitoring ? 'RUNNING' : 'STOPPED'}</span>
        </div>
      </div>

      <div className="fo-grid">
        {/* Toolbar controls */}
        <MonitoringToolbar
          monitoringMode={monitoringMode}
          selectedIndices={selectedIndices}
          isMonitoring={isMonitoring}
          startMonitoring={startMonitoring}
          stopMonitoring={stopMonitoring}
          changeMode={changeMode}
          selectSingleIndex={selectSingleIndex}
          toggleMultiIndex={toggleMultiIndex}
        />

        {/* Monitoring Cards Grid */}
        <section className="fo-section">
          <h2 className="section-title">Active Index Monitoring</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
            {selectedIndices.map(symbol => (
              <MonitoringCard
                key={symbol}
                symbol={symbol}
                session={sessions[symbol] || { status: 'Stopped' }}
              />
            ))}
          </div>
        </section>

        {/* Portfolio & Risk */}
        <div className="flex-row-grid">
          <section className="fo-section portfolio-section">
            <h2 className="section-title">Portfolio Overview</h2>
            <div className="metrics-grid">
              {portfolioMetrics.map((metric, idx) => (
                <MetricCard key={idx} {...metric} />
              ))}
            </div>
          </section>

          <section className="fo-section risk-section">
            <h2 className="section-title">Risk Status</h2>
            <div className="metrics-grid">
              {riskMetrics.map((metric, idx) => (
                <MetricCard key={idx} {...metric} />
              ))}
            </div>
          </section>
        </div>

        {/* Opportunities */}
        <section className="fo-section opportunities-section">
          <TableCard
            title="Derivatives Watchlist"
            headers={opportunityHeaders}
            data={dummyOpportunities}
            renderRow={(row, idx) => (
              <tr key={idx}>
                <td><strong>{row.index}</strong></td>
                <td>{row.expiry}</td>
                <td>
                  <span className={`badge-status ${row.status.toLowerCase()}`}>
                    {row.status}
                  </span>
                </td>
                <td>{row.signal}</td>
                <td className="text-muted">{row.confidence}</td>
                <td className="text-muted">{row.reason}</td>
              </tr>
            )}
          />
        </section>

        {/* Trade Activity & System Health */}
        <div className="flex-row-grid">
          <section className="fo-section trades-section">
            <TableCard
              title="Recent Derivatives Trades"
              headers={tradeHeaders}
              data={[]}
              emptyMessage="No derivatives trades executed today."
            />
          </section>

          <section className="fo-section health-section">
            <h2 className="section-title">System Health</h2>
            <div className="system-health-grid">
              {systemStatus.map((sys, idx) => (
                <SystemStatusCard key={idx} {...sys} />
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
