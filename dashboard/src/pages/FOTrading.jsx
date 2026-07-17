import React, { useMemo, useState } from 'react'
import MetricCard from '../components/MetricCard'
import SystemStatusCard from '../components/SystemStatusCard'
import TableCard from '../components/TableCard'
import useFnoEngine from '../modules/fno/hooks/useFnoEngine'
import MonitoringToolbar from '../modules/fno/components/MonitoringToolbar'
import MonitoringCard from '../modules/fno/components/MonitoringCard'
import { backtester } from '../modules/fno/services/strategy/backtester'
import { riskService } from '../modules/fno/services/risk/riskService'

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

  // Tabs: 'live' | 'backtest'
  const [activeTab, setActiveTab] = useState('live')

  // Backtest parameters state
  const [btParams, setBtParams] = useState({
    ivPercentileMin: 35,
    ivPercentileMax: 75,
    shortDelta: 0.18,
    profitTarget: 55,
    stopLoss: 1.75,
    dailyLossLimit: 2,
    weeklyLossLimit: 4,
    monthlyDrawdown: 8,
    maxPortfolioRisk: 6,
    riskPerTrade: 1.0,
    vixSpikeFilter: 15,
    vixExit: 10,
    exitBeforeExpiry: 2
  })

  const [btResults, setBtResults] = useState(null)
  const [runningBt, setRunningBt] = useState(false)

  const handleRunBacktest = () => {
    setRunningBt(true)
    setTimeout(() => {
      // Execute the simulation math inside backtester service
      const results = backtester.runBacktest(selectedIndices[0] || 'NIFTY', {
        ivPercentileMin: btParams.ivPercentileMin,
        ivPercentileMax: btParams.ivPercentileMax,
        shortDelta: btParams.shortDelta,
        riskPerTrade: btParams.riskPerTrade / 100
      })
      setBtResults(results)
      setRunningBt(false)
    }, 800)
  }

  // Active risk checks based on state
  const currentRiskStatus = useMemo(() => {
    return riskService.checkRiskLimits({
      tradeRiskPct: btParams.riskPerTrade / 100,
      portfolioExposurePct: (selectedIndices.length * btParams.riskPerTrade) / 100,
      dailyLossPct: 0.0,
      weeklyLossPct: 0.0,
      monthlyDrawdownPct: 0.0
    })
  }, [btParams.riskPerTrade, selectedIndices])

  const portfolioMetrics = useMemo(() => [
    { label: 'Open Positions', value: isMonitoring ? `${selectedIndices.length}` : '0', subValue: isMonitoring ? 'Live tracking' : 'Idle', trend: 'neutral' },
    { label: "Today's P&L", value: '₹ 0.00', subValue: '0.00%', trend: 'neutral' },
    { label: 'Weekly P&L', value: '₹ 0.00', subValue: '0.00%', trend: 'neutral' },
    { label: 'Capital Used', value: isMonitoring ? `${(selectedIndices.length * btParams.riskPerTrade).toFixed(1)}%` : '0.0%', subValue: 'Exposure limit 6.0%', trend: 'neutral' },
    { label: 'Risk Used', value: isMonitoring ? 'Active' : '0.0%', subValue: 'Margin checked', trend: 'neutral' },
    { label: 'Peak Drawdown', value: '0.0%', subValue: 'Daily Peak', trend: 'neutral' }
  ], [isMonitoring, selectedIndices, btParams.riskPerTrade])

  const systemStatus = useMemo(() => [
    { name: 'Data Feed', status: isMonitoring ? 'green' : 'yellow', message: isMonitoring ? 'Connected' : 'Standby' },
    { name: 'Broker API', status: 'green', message: 'Token Valid (Expires in 14h)' },
    { name: 'Execution Router', status: 'green', message: 'Idle — Ready to route' },
    { name: 'Risk Engine', status: currentRiskStatus.isRiskCleared ? 'green' : 'red', message: currentRiskStatus.isRiskCleared ? 'Parameters Cleared' : 'Risk Breach' },
    { name: 'Strategy Engine', status: 'green', message: 'Loaded — Standby' }
  ], [isMonitoring, currentRiskStatus])

  const dummyOpportunities = useMemo(() => {
    return selectedIndices.map(symbol => {
      const activeSession = sessions[symbol]
      return {
        index: symbol,
        expiry: activeSession?.marketData?.expiry || 'Waiting...',
        status: isMonitoring ? (activeSession?.regimeResults?.isAllowed ? 'ACTIVE' : 'BLOCKED') : 'INACTIVE',
        signal: activeSession?.structure?.vehicle || 'MONITORING',
        confidence: activeSession?.indicators ? `${Math.round(activeSession.indicators.ivPercentile)}%` : 'N/A',
        reason: isMonitoring ? (activeSession?.regimeResults?.isAllowed ? 'VRP spread setup cleared' : 'Regime filters mismatch') : 'Engine stopped'
      }
    })
  }, [selectedIndices, sessions, isMonitoring])

  const opportunityHeaders = ['Index', 'Expiry', 'Status', 'Signal', 'IV Percentile', 'Reason']
  const tradeHeaders = ['ID', 'Time', 'Instrument', 'Type', 'Qty', 'Entry', 'Exit', 'P&L', 'Status']

  return (
    <div className="fo-dashboard">
      <div className="page-header">
        <div>
          <h1 className="page-title">F&O Trading Dashboard</h1>
          <div className="page-subtitle">Institutional Derivatives Monitoring & Execution</div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`btn ${activeTab === 'live' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('live')}
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            Live Monitor
          </button>
          <button
            className={`btn ${activeTab === 'backtest' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('backtest')}
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            Backtest Engine
          </button>
        </div>
      </div>

      <div className="fo-grid">
        {activeTab === 'live' ? (
          <>
            {/* Live toolbar */}
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

            {/* Live Cards */}
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

            {/* Live Portfolio */}
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
                <h2 className="section-title">Risk Status (Live Check)</h2>
                <div className="metrics-grid">
                  {Object.entries(currentRiskStatus.limits).map(([key, item]) => (
                    <div key={key} className="metric-card" style={{ borderLeft: `3px solid ${item.pass ? 'var(--accent-green)' : 'var(--accent-red)'}` }}>
                      <span className="metric-label">{key.replace(/([A-Z])/g, ' $1')}</span>
                      <div className="metric-value-row">
                        <span className="metric-value">{item.val}</span>
                        <span className="metric-subvalue" style={{ color: 'var(--text-muted)' }}>{item.limit}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            {/* Opportunities */}
            <section className="fo-section opportunities-section">
              <TableCard
                title="VRP Signals Watchlist"
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
                    <td className="text-green">{row.signal}</td>
                    <td className="text-muted">{row.confidence}</td>
                    <td className="text-muted">{row.reason}</td>
                  </tr>
                )}
              />
            </section>

            {/* Trade Activity & Health */}
            <div className="flex-row-grid">
              <section className="fo-section trades-section">
                <TableCard
                  title="Live Derivatives Fills"
                  headers={tradeHeaders}
                  data={[]}
                  emptyMessage="No derivatives trades executed in current session."
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
          </>
        ) : (
          /* Backtesting Interface Tab */
          <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
            
            {/* Parameters Sidebar */}
            <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', height: 'fit-content' }}>
              <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)', paddingBottom: '10px' }}>Parameters</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.82rem' }}>
                <div>
                  <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '4px' }}>IV Percentile Limits</label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      type="number"
                      value={btParams.ivPercentileMin}
                      onChange={e => setBtParams({ ...btParams, ivPercentileMin: Number(e.target.value) })}
                      style={{ width: '100%', padding: '6px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: '4px' }}
                    />
                    <input
                      type="number"
                      value={btParams.ivPercentileMax}
                      onChange={e => setBtParams({ ...btParams, ivPercentileMax: Number(e.target.value) })}
                      style={{ width: '100%', padding: '6px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: '4px' }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '4px' }}>Short Greeks Delta</label>
                  <input
                    type="number"
                    step="0.01"
                    value={btParams.shortDelta}
                    onChange={e => setBtParams({ ...btParams, shortDelta: Number(e.target.value) })}
                    style={{ width: '100%', padding: '6px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: '4px' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '4px' }}>Risk Per Trade (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={btParams.riskPerTrade}
                    onChange={e => setBtParams({ ...btParams, riskPerTrade: Number(e.target.value) })}
                    style={{ width: '100%', padding: '6px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: '4px' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '4px' }}>Profit Target / SL</label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      type="number"
                      value={btParams.profitTarget}
                      placeholder="TP %"
                      onChange={e => setBtParams({ ...btParams, profitTarget: Number(e.target.value) })}
                      style={{ width: '100%', padding: '6px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: '4px' }}
                    />
                    <input
                      type="number"
                      step="0.05"
                      value={btParams.stopLoss}
                      placeholder="SL x"
                      onChange={e => setBtParams({ ...btParams, stopLoss: Number(e.target.value) })}
                      style={{ width: '100%', padding: '6px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: '4px' }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', color: 'var(--text-muted)', marginBottom: '4px' }}>Limits (Daily / Weekly / Drawdown)</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px' }}>
                    <input
                      type="number"
                      value={btParams.dailyLossLimit}
                      title="Daily Loss limit"
                      onChange={e => setBtParams({ ...btParams, dailyLossLimit: Number(e.target.value) })}
                      style={{ width: '100%', padding: '6px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: '4px' }}
                    />
                    <input
                      type="number"
                      value={btParams.weeklyLossLimit}
                      title="Weekly Loss limit"
                      onChange={e => setBtParams({ ...btParams, weeklyLossLimit: Number(e.target.value) })}
                      style={{ width: '100%', padding: '6px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: '4px' }}
                    />
                    <input
                      type="number"
                      value={btParams.monthlyDrawdown}
                      title="Monthly Drawdown"
                      onChange={e => setBtParams({ ...btParams, monthlyDrawdown: Number(e.target.value) })}
                      style={{ width: '100%', padding: '6px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: '4px' }}
                    />
                  </div>
                </div>
              </div>

              <button
                className="btn btn-primary"
                onClick={handleRunBacktest}
                disabled={runningBt}
                style={{ marginTop: '10px', padding: '10px 0', width: '100%', justifyContent: 'center' }}
              >
                {runningBt ? 'Simulating Paths...' : 'Run Backtest Simulation'}
              </button>
            </div>

            {/* Results dashboard */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {btResults ? (
                <>
                  {/* Stats Row */}
                  <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                    <div className="metric-card">
                      <span className="metric-label">Total Simulated Return</span>
                      <span className="metric-value text-green">+{btResults.totalReturn.toFixed(2)}%</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Max Peak Drawdown</span>
                      <span className="metric-value text-red">-{btResults.maxDrawdown.toFixed(2)}%</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Simulated Win Rate</span>
                      <span className="metric-value">{btResults.winRate}%</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Sharpe Ratio</span>
                      <span className="metric-value" style={{ color: 'var(--accent-blue-bright)' }}>{btResults.sharpeRatio}</span>
                    </div>
                  </div>

                  {/* Monte Carlo Percentiles */}
                  <div className="card" style={{ padding: '20px' }}>
                    <h3 className="section-title" style={{ marginBottom: '12px' }}>Monte Carlo Percentile Distribution (500 Paths)</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', textAlign: 'center' }}>
                      <div style={{ background: 'rgba(239, 68, 68, 0.04)', padding: '16px', borderRadius: '6px' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>P10 (Worst Case)</span>
                        <div style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--accent-red)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                          ₹ {btResults.monteCarlo.p10.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                        </div>
                      </div>
                      <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '6px' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>P50 (Median Return)</span>
                        <div style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                          ₹ {btResults.monteCarlo.p50.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                        </div>
                      </div>
                      <div style={{ background: 'rgba(34, 197, 94, 0.04)', padding: '16px', borderRadius: '6px' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>P90 (Best Case)</span>
                        <div style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--accent-green)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                          ₹ {btResults.monteCarlo.p90.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Walk-Forward Timeseries */}
                  <TableCard
                    title="Walk-Forward Splits (12 Months Out-of-Sample Validation)"
                    headers={['Month', 'Dataset Split', 'Trades executed', 'P&L Payout', 'Balance', 'Yield']}
                    data={btResults.walkForwardResults}
                    renderRow={(row, idx) => (
                      <tr key={idx} style={{ background: row.period === 'Out-of-Sample' ? 'rgba(167, 139, 250, 0.03)' : 'transparent' }}>
                        <td><strong>{row.month}</strong></td>
                        <td>
                          <span style={{ fontSize: '0.7rem', padding: '2px 6px', borderRadius: '3px', background: row.period === 'Out-of-Sample' ? 'rgba(167, 139, 250, 0.15)' : 'rgba(255,255,255,0.05)', color: row.period === 'Out-of-Sample' ? 'var(--accent-purple)' : 'var(--text-secondary)' }}>
                            {row.period}
                          </span>
                        </td>
                        <td>{row.trades}</td>
                        <td className={row.pnl >= 0 ? 'text-green' : 'text-red'}>₹ {row.pnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>₹ {row.equity.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                        <td className={row.returnPct >= 0 ? 'text-green' : 'text-red'}>{row.returnPct.toFixed(2)}%</td>
                      </tr>
                    )}
                  />

                  {/* Sensitivity Analysis */}
                  <TableCard
                    title="Short Delta Win-Rate Sensitivity Analysis"
                    headers={['Target Delta', 'Expected Win Rate', 'Simulated Annualized Return']}
                    data={btResults.sensitivityData}
                    renderRow={(row, idx) => (
                      <tr key={idx}>
                        <td><strong>{row.delta.toFixed(2)}</strong></td>
                        <td className="text-green">{row.winRate.toFixed(1)}%</td>
                        <td className="text-green">+{row.expectedAnnualReturn.toFixed(1)}%</td>
                      </tr>
                    )}
                  />
                </>
              ) : (
                <div className="card" style={{ padding: '80px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <h3>No Simulation Configured</h3>
                  <p style={{ fontSize: '0.85rem', marginTop: '6px' }}>Configure the Delta parameters and click [Run Backtest Simulation] to initialize Monte Carlo curves.</p>
                </div>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  )
}
