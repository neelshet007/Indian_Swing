import React, { useState, useEffect } from 'react'
import axios from 'axios'

export default function HistoricalScan() {
  const [activeTab, setActiveTab] = useState('scans')
  const [progress, setProgress] = useState(null)
  const [scans, setScans] = useState([])
  const [trades, setTrades] = useState([])
  const [report, setReport] = useState(null)
  const [selectedScan, setSelectedScan] = useState(null)
  const [selectedScanRecs, setSelectedScanRecs] = useState([])
  const [loadingRecs, setLoadingRecs] = useState(false)
  const [isResuming, setIsResuming] = useState(false)

  // Fetch status, report, and scans/trades list
  const fetchData = async () => {
    try {
      const progRes = await axios.get('/api/historical/progress')
      setProgress(progRes.data)

      const scansRes = await axios.get('/api/historical/scans')
      setScans(scansRes.data)

      const tradesRes = await axios.get('/api/historical/paper-trades')
      setTrades(tradesRes.data)

      const reportRes = await axios.get('/api/historical/report')
      setReport(reportRes.data)
    } catch (err) {
      console.error('Error fetching historical scanner data:', err)
    }
  }

  // Auto-poll progress while active/running
  useEffect(() => {
    fetchData()
    const interval = setInterval(() => {
      fetchData()
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // Handle Resume action
  const handleResume = async () => {
    setIsResuming(true)
    try {
      await axios.post('/api/historical/resume')
      fetchData()
    } catch (err) {
      alert('Failed to resume scan: ' + (err.response?.data?.detail || err.message))
    } finally {
      setIsResuming(false)
    }
  }

  // Load recommendations for explorer
  const handleViewRecommendations = async (scan) => {
    setSelectedScan(scan)
    setLoadingRecs(true)
    try {
      const res = await axios.get(`/api/historical/scans/${scan.scan_uuid}/recommendations`)
      setSelectedScanRecs(res.data)
    } catch (err) {
      console.error('Error loading recommendations:', err)
    } finally {
      setLoadingRecs(false)
    }
  }

  const handleDownloadExcel = () => {
    window.open('/api/historical/export', '_blank')
  }

  // Calculate progress percentage
  const progressPct = progress?.total_days > 0 
    ? Math.round((progress.completed_days / progress.total_days) * 100) 
    : 0

  return (
    <div style={{ padding: '32px', maxWidth: '1600px', margin: '0 auto' }}>
      
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 className="page-title" style={{ fontSize: '2rem', fontWeight: 700 }}>Historical Scan Terminal</h1>
          <p className="page-subtitle" style={{ color: 'var(--text-secondary)' }}>Automated historical scanning and backtesting replication platform</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button 
            onClick={handleDownloadExcel}
            className="card-hover"
            style={{
              background: 'linear-gradient(135deg, #107c41, #1f9a55)',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              color: '#fff',
              padding: '10px 20px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            📊 Download Excel Journal
          </button>
          {progress?.status === 'paused' && (
            <button 
              onClick={handleResume}
              disabled={isResuming}
              className="card-hover"
              style={{
                background: 'var(--accent-blue)',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                color: '#fff',
                padding: '10px 20px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              {isResuming ? 'Resuming...' : '▶ Resume Historical Scan'}
            </button>
          )}
        </div>
      </div>

      {/* Live Progress Bar Card */}
      {progress && progress.status === 'active' && (
        <div className="card" style={{ padding: '24px', marginBottom: '24px', border: '1px solid var(--border-accent)' }}>
          <h3 style={{ marginBottom: '12px', color: 'var(--accent-blue-bright)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="status-dot" style={{ background: 'var(--accent-blue)', boxShadow: '0 0 10px var(--accent-blue)' }} />
            Historical Scan Running...
          </h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.88rem' }}>
            <span>Progress: {progress.completed_days} / {progress.total_days} Trading Days ({progressPct}%)</span>
            <span>ETA: {progress.eta_minutes} Minutes</span>
          </div>
          {/* Progress Bar Container */}
          <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '6px', height: '12px', overflow: 'hidden', marginBottom: '16px' }}>
            <div style={{ width: `${progressPct}%`, background: 'linear-gradient(90deg, var(--accent-blue), var(--accent-purple))', height: '100%', transition: 'width 0.4s ease' }} />
          </div>

          {/* Detailed Scanner Status */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', fontSize: '0.85rem' }}>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-secondary)' }}>Current Trading Day</div>
              <strong style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>{progress.current_date || 'Initializing...'}</strong>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-secondary)' }}>Active Symbol Scanning</div>
              <strong style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>{progress.current_symbol || 'N/A'}</strong>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-secondary)' }}>Today's Recommendations</div>
              <strong style={{ fontSize: '1.1rem', color: 'var(--accent-amber)' }}>{progress.recommendations_today}</strong>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-secondary)' }}>Paper Trades Created</div>
              <strong style={{ fontSize: '1.1rem', color: 'var(--accent-blue-bright)' }}>{progress.paper_trades_created}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Performance Summary Metrics Card */}
      {report && report.total_trades > 0 && (
        <div className="card" style={{ padding: '24px', marginBottom: '24px' }}>
          <h3 style={{ marginBottom: '16px', color: 'var(--text-primary)' }}>Performance Summary Metrics</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            <div style={{ padding: '12px', borderLeft: '3px solid var(--accent-blue)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Total Completed Trades</div>
              <div style={{ fontSize: '1.4rem', fontWeight: '700' }}>{report.total_trades}</div>
            </div>
            <div style={{ padding: '12px', borderLeft: '3px solid var(--accent-green)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Win Rate</div>
              <div style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-green)' }}>{report.win_rate}%</div>
            </div>
            <div style={{ padding: '12px', borderLeft: '3px solid var(--accent-red)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Loss Rate</div>
              <div style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-red)' }}>{report.loss_rate}%</div>
            </div>
            <div style={{ padding: '12px', borderLeft: '3px solid var(--accent-amber)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Profit Factor</div>
              <div style={{ fontSize: '1.4rem', fontWeight: '700' }}>{report.profit_factor}</div>
            </div>
            <div style={{ padding: '12px', borderLeft: '3px solid var(--accent-purple)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Maximum Drawdown</div>
              <div style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-red)' }}>{report.max_drawdown}%</div>
            </div>
            <div style={{ padding: '12px', borderLeft: '3px solid var(--accent-cyan)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>CAGR</div>
              <div style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-green)' }}>{report.cagr}%</div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs Selector */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: '20px', gap: '8px' }}>
        <button
          onClick={() => setActiveTab('scans')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'scans' ? '2px solid var(--accent-blue)' : '2px solid transparent',
            color: activeTab === 'scans' ? 'var(--accent-blue-bright)' : 'var(--text-secondary)',
            padding: '10px 16px',
            fontSize: '0.95rem',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          📅 Completed Daily Scans ({scans.length})
        </button>
        <button
          onClick={() => setActiveTab('trades')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'trades' ? '2px solid var(--accent-blue)' : '2px solid transparent',
            color: activeTab === 'trades' ? 'var(--accent-blue-bright)' : 'var(--text-secondary)',
            padding: '10px 16px',
            fontSize: '0.95rem',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          💼 Paper Trade Explorer ({trades.length})
        </button>
      </div>

      {/* Tab Contents: Daily Scans Table */}
      {activeTab === 'scans' && (
        <div className="card" style={{ padding: '16px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '12px 8px' }}>Scan Date</th>
                <th style={{ padding: '12px 8px' }}>Status</th>
                <th style={{ padding: '12px 8px' }}>Stocks Scanned</th>
                <th style={{ padding: '12px 8px' }}>Recommendations</th>
                <th style={{ padding: '12px 8px' }}>Active Trades</th>
                <th style={{ padding: '12px 8px' }}>Closed Trades</th>
                <th style={{ padding: '12px 8px' }}>Duration</th>
                <th style={{ padding: '12px 8px' }}>Version</th>
                <th style={{ padding: '12px 8px' }}>Provider</th>
                <th style={{ padding: '12px 8px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((scan) => (
                <tr key={scan.scan_uuid} style={{ borderBottom: '1px solid var(--border)' }} className="table-row-hover">
                  <td style={{ padding: '12px 8px', fontWeight: '600' }}>{scan.scan_date}</td>
                  <td style={{ padding: '12px 8px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      background: scan.status === 'completed' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                      color: scan.status === 'completed' ? 'var(--accent-green)' : 'var(--accent-red)'
                    }}>
                      {scan.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '12px 8px' }}>{scan.stocks_scanned}</td>
                  <td style={{ padding: '12px 8px', color: 'var(--accent-amber)', fontWeight: '600' }}>{scan.recommendations_count}</td>
                  <td style={{ padding: '12px 8px', color: 'var(--accent-blue-bright)' }}>{scan.active_trades}</td>
                  <td style={{ padding: '12px 8px', color: 'var(--accent-green)' }}>{scan.closed_trades}</td>
                  <td style={{ padding: '12px 8px' }}>{scan.duration_seconds}s</td>
                  <td style={{ padding: '12px 8px' }}>v{scan.strategy_version}</td>
                  <td style={{ padding: '12px 8px', color: 'var(--text-secondary)' }}>{scan.data_provider}</td>
                  <td style={{ padding: '12px 8px' }}>
                    <button 
                      onClick={() => handleViewRecommendations(scan)}
                      style={{
                        background: 'rgba(255,255,255,0.06)',
                        border: 'none',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        padding: '6px 12px',
                        fontSize: '0.8rem',
                        cursor: 'pointer'
                      }}
                      className="card-hover"
                    >
                      🔍 View Recommendations
                    </button>
                  </td>
                </tr>
              ))}
              {scans.length === 0 && (
                <tr>
                  <td colSpan="10" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No completed scans found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab Contents: Paper Trades Explorer */}
      {activeTab === 'trades' && (
        <div className="card" style={{ padding: '16px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '12px 8px' }}>Symbol</th>
                <th style={{ padding: '12px 8px' }}>Status</th>
                <th style={{ padding: '12px 8px' }}>Entry Date</th>
                <th style={{ padding: '12px 8px' }}>Entry Price</th>
                <th style={{ padding: '12px 8px' }}>Exit Date</th>
                <th style={{ padding: '12px 8px' }}>Exit Price</th>
                <th style={{ padding: '12px 8px' }}>Return %</th>
                <th style={{ padding: '12px 8px' }}>R Multiple</th>
                <th style={{ padding: '12px 8px' }}>MFE</th>
                <th style={{ padding: '12px 8px' }}>MAE</th>
                <th style={{ padding: '12px 8px' }}>Holding Period</th>
                <th style={{ padding: '12px 8px' }}>Exit Reason</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px 8px', fontWeight: '600' }}>{t.symbol}</td>
                  <td style={{ padding: '12px 8px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      background: t.status === 'Closed' ? 'rgba(255,255,255,0.06)' : 'rgba(79,142,247,0.1)',
                      color: t.status === 'Closed' ? 'var(--text-secondary)' : 'var(--accent-blue-bright)'
                    }}>
                      {t.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px 8px' }}>{t.entry_date || 'N/A'}</td>
                  <td style={{ padding: '12px 8px' }}>{t.entry_price ? `₹${t.entry_price.toFixed(2)}` : 'N/A'}</td>
                  <td style={{ padding: '12px 8px' }}>{t.exit_date || 'N/A'}</td>
                  <td style={{ padding: '12px 8px' }}>{t.exit_price ? `₹${t.exit_price.toFixed(2)}` : 'N/A'}</td>
                  <td style={{ 
                    padding: '12px 8px', 
                    fontWeight: '600',
                    color: t.pnl > 0 ? 'var(--accent-green)' : (t.pnl < 0 ? 'var(--accent-red)' : 'inherit')
                  }}>
                    {t.pnl !== null ? `${t.pnl > 0 ? '+' : ''}${t.pnl.toFixed(2)}%` : 'N/A'}
                  </td>
                  <td style={{ 
                    padding: '12px 8px',
                    fontWeight: '600',
                    color: t.r_multiple > 0 ? 'var(--accent-green)' : (t.r_multiple < 0 ? 'var(--accent-red)' : 'inherit')
                  }}>
                    {t.r_multiple !== null ? `${t.r_multiple > 0 ? '+' : ''}${t.r_multiple.toFixed(2)}R` : 'N/A'}
                  </td>
                  <td style={{ padding: '12px 8px', color: 'var(--accent-green)' }}>{t.max_favorable_excursion ? `${t.max_favorable_excursion.toFixed(1)}%` : '0%'}</td>
                  <td style={{ padding: '12px 8px', color: 'var(--accent-red)' }}>{t.max_adverse_excursion ? `${t.max_adverse_excursion.toFixed(1)}%` : '0%'}</td>
                  <td style={{ padding: '12px 8px' }}>{t.holding_days !== null ? `${t.holding_days} days` : 'N/A'}</td>
                  <td style={{ padding: '12px 8px', color: 'var(--text-secondary)' }}>{t.exit_reason || 'N/A'}</td>
                </tr>
              ))}
              {trades.length === 0 && (
                <tr>
                  <td colSpan="12" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No paper trades recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Recommendation Snapshot Explorer Modal */}
      {selectedScan && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          zIndex: 1000,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '40px'
        }}>
          <div className="card" style={{
            width: '100%',
            maxWidth: '1200px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            border: '1px solid var(--border-accent)'
          }}>
            {/* Modal Header */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem' }}>Scan Recommendation Explorer</h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Historical Date: {selectedScan.scan_date} | Strategy: sivcs_vcp | UUID: {selectedScan.scan_uuid}</p>
              </div>
              <button 
                onClick={() => setSelectedScan(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  fontSize: '1.5rem',
                  cursor: 'pointer'
                }}
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
              {loadingRecs ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>Loading recommendations...</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                      <th style={{ padding: '10px 8px' }}>Symbol</th>
                      <th style={{ padding: '10px 8px' }}>Company Name</th>
                      <th style={{ padding: '10px 8px' }}>Entry</th>
                      <th style={{ padding: '10px 8px' }}>Stop Loss</th>
                      <th style={{ padding: '10px 8px' }}>Target</th>
                      <th style={{ padding: '10px 8px' }}>Risk/Reward</th>
                      <th style={{ padding: '10px 8px' }}>Score</th>
                      <th style={{ padding: '10px 8px' }}>Stage</th>
                      <th style={{ padding: '10px 8px' }}>RS</th>
                      <th style={{ padding: '10px 8px' }}>VCP</th>
                      <th style={{ padding: '10px 8px' }}>Breakout</th>
                      <th style={{ padding: '10px 8px' }}>Setup Reasoning</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedScanRecs.map((rec) => (
                      <tr key={rec.recommendation_uuid} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '12px 8px', fontWeight: '600' }}>{rec.symbol}</td>
                        <td style={{ padding: '12px 8px' }}>{rec.company_name}</td>
                        <td style={{ padding: '12px 8px' }}>₹{rec.entry_price.toFixed(2)}</td>
                        <td style={{ padding: '12px 8px' }}>₹{rec.stop_loss.toFixed(2)}</td>
                        <td style={{ padding: '12px 8px' }}>₹{rec.target_price.toFixed(2)}</td>
                        <td style={{ padding: '12px 8px' }}>{rec.risk_reward.toFixed(2)}</td>
                        <td style={{ padding: '12px 8px', fontWeight: '600', color: 'var(--accent-blue-bright)' }}>{(rec.confidence_score * 100).toFixed(0)}%</td>
                        <td style={{ padding: '12px 8px' }}>
                          <span style={{ color: rec.stage === 'PASS' ? 'var(--accent-green)' : 'var(--accent-red)' }}>{rec.stage}</span>
                        </td>
                        <td style={{ padding: '12px 8px' }}>
                          <span style={{ color: rec.relative_strength === 'PASS' ? 'var(--accent-green)' : 'var(--accent-red)' }}>{rec.relative_strength}</span>
                        </td>
                        <td style={{ padding: '12px 8px' }}>
                          <span style={{ color: rec.vcp_status === 'PASS' ? 'var(--accent-green)' : 'var(--accent-red)' }}>{rec.vcp_status}</span>
                        </td>
                        <td style={{ padding: '12px 8px' }}>
                          <span style={{ color: rec.breakout_status === 'PASS' ? 'var(--accent-green)' : 'var(--accent-red)' }}>{rec.breakout_status}</span>
                        </td>
                        <td style={{ padding: '12px 8px', maxWidth: '300px', whiteSpace: 'normal', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                          {rec.reasons.join(', ')}
                        </td>
                      </tr>
                    ))}
                    {selectedScanRecs.length === 0 && (
                      <tr>
                        <td colSpan="12" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                          No recommendations generated for this day (empty scan).
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              )}
            </div>
            
            {/* Modal Footer */}
            <div style={{ padding: '16px 24px', background: 'rgba(255,255,255,0.02)', borderTop: '1px solid var(--border)', textAlign: 'right' }}>
              <button 
                onClick={() => setSelectedScan(null)}
                style={{
                  background: 'var(--accent-blue)',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#fff',
                  padding: '8px 16px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Close Snapshot
              </button>
            </div>
          </div>
        </div>
      )}
      
    </div>
  )
}
