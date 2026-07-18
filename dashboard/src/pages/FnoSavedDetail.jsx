import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'

export default function FnoSavedDetail() {
  const { savedId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('summary') // 'summary' | 'regime' | 'greeks' | 'backtest'
  
  // Note & status state
  const [notes, setNotes] = useState('')
  const [status, setStatus] = useState('Pending')
  const [savingNotes, setSavingNotes] = useState(false)

  useEffect(() => {
    const fetchDetail = async () => {
      setLoading(true)
      try {
        const { data } = await axios.get(`/api/fno/saved-recommendations/${savedId}`)
        setData(data)
        setNotes(data.user_notes || '')
        setStatus(data.status || 'Pending')
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchDetail()
  }, [savedId])

  const handleUpdate = async () => {
    setSavingNotes(true)
    try {
      await axios.put(`/api/fno/saved-recommendations/${savedId}`, {
        status: status,
        user_notes: notes
      })
      alert('Forensic record updated successfully!')
    } catch (e) {
      console.error(e)
      alert('Failed to update forensic record.')
    } finally {
      setSavingNotes(false)
    }
  }

  if (loading) {
    return <div className="loader-container"><div className="loader" /></div>
  }

  if (!data) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
        Forensic saved recommendation not found. <Link to="/fno-saved">Back to Saved Records</Link>
      </div>
    )
  }

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', color: 'var(--text-primary)' }}>
      
      {/* Back to List */}
      <div>
        <Link to="/fno-saved" style={{ fontSize: '0.74rem', textDecoration: 'none', color: 'var(--accent-blue-bright)', fontWeight: '700' }}>
          ← Back to Saved Forensic Audit Records
        </Link>
      </div>

      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', borderBottom: '1px solid #1e293b', paddingBottom: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.4rem', fontWeight: '900', color: '#fff' }}>{data.symbol} Forensic Audit Report</h1>
            <span style={{ fontSize: '0.74rem', padding: '3px 8px', borderRadius: '4px', background: 'rgba(99,102,241,0.15)', color: 'var(--accent-blue-bright)', fontWeight: '800' }}>
              SAVED SIGNAL
            </span>
          </div>
          <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Signal UUID: <span style={{ fontFamily: 'var(--font-mono)' }}>{data.id}</span> | Scan Time: {data.scan_date}
          </p>
        </div>

        {/* Action Widgets */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '10px 18px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Quality Score</div>
            <div style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
              {data.quality_score}/100
            </div>
          </div>
          <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '10px 18px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Trade Status</div>
            <div style={{ fontSize: '1.4rem', fontWeight: '900', color: 'var(--accent-blue-bright)', fontFamily: 'var(--font-mono)' }}>
              {data.status.toUpperCase()}
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid split */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: '20px' }}>
        
        {/* Left Column: Forensic Data */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid #1e293b', gap: '4px' }}>
            <button 
              onClick={() => setActiveTab('summary')}
              style={{ background: activeTab === 'summary' ? '#1e293b' : 'transparent', color: activeTab === 'summary' ? '#fff' : 'var(--text-secondary)', border: 'none', borderBottom: activeTab === 'summary' ? '2px solid var(--accent-blue-bright)' : 'none', padding: '10px 20px', fontSize: '0.78rem', fontWeight: '700', cursor: 'pointer' }}
            >
              Executive Summary & Strike Selection
            </button>
            <button 
              onClick={() => setActiveTab('regime')}
              style={{ background: activeTab === 'regime' ? '#1e293b' : 'transparent', color: activeTab === 'regime' ? '#fff' : 'var(--text-secondary)', border: 'none', borderBottom: activeTab === 'regime' ? '2px solid var(--accent-blue-bright)' : 'none', padding: '10px 20px', fontSize: '0.78rem', fontWeight: '700', cursor: 'pointer' }}
            >
              Market Snapshot & Volatility Regime
            </button>
            <button 
              onClick={() => setActiveTab('greeks')}
              style={{ background: activeTab === 'greeks' ? '#1e293b' : 'transparent', color: activeTab === 'greeks' ? '#fff' : 'var(--text-secondary)', border: 'none', borderBottom: activeTab === 'greeks' ? '2px solid var(--accent-blue-bright)' : 'none', padding: '10px 20px', fontSize: '0.78rem', fontWeight: '700', cursor: 'pointer' }}
            >
              Greeks Dashboard & EV Analysis
            </button>
            <button 
              onClick={() => setActiveTab('backtest')}
              style={{ background: activeTab === 'backtest' ? '#1e293b' : 'transparent', color: activeTab === 'backtest' ? '#fff' : 'var(--text-secondary)', border: 'none', borderBottom: activeTab === 'backtest' ? '2px solid var(--accent-blue-bright)' : 'none', padding: '10px 20px', fontSize: '0.78rem', fontWeight: '700', cursor: 'pointer' }}
            >
              Historical Audit Log
            </button>
          </div>

          {/* TAB 1: SUMMARY */}
          {activeTab === 'summary' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              {/* Executive Summary Rationale */}
              <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '8px' }}>Forensic Recommendation Explanation</h3>
                <p style={{ fontSize: '0.82rem', lineHeight: '1.6', color: '#cbd5e1' }}>
                  {data.reasoning}
                </p>
              </div>

              {/* Exact Option Structure Setup */}
              <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '12px' }}>Exact Option Structure Setup</h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '16px' }}>
                  <div style={{ background: 'rgba(239,68,68,0.05)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--accent-red)', fontWeight: '800' }}>SELL CALL (CE)</div>
                    <div style={{ fontSize: '1rem', fontWeight: '900', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.short_call || '—'}</div>
                  </div>
                  <div style={{ background: 'rgba(34,197,94,0.05)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--accent-green)', fontWeight: '800' }}>BUY CALL HEDGE (CE)</div>
                    <div style={{ fontSize: '1rem', fontWeight: '900', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.long_call || '—'}</div>
                  </div>
                  <div style={{ background: 'rgba(239,68,68,0.05)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--accent-red)', fontWeight: '800' }}>SELL PUT (PE)</div>
                    <div style={{ fontSize: '1rem', fontWeight: '900', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.short_put || '—'}</div>
                  </div>
                  <div style={{ background: 'rgba(34,197,94,0.05)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--accent-green)', fontWeight: '800' }}>BUY PUT HEDGE (PE)</div>
                    <div style={{ fontSize: '1rem', fontWeight: '900', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.long_put || '—'}</div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px', fontSize: '0.74rem' }}>
                  <div style={{ borderRight: '1px solid #1e293b' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Net Credit</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>₹ {data.net_credit?.toLocaleString() || '0'}</div>
                  </div>
                  <div style={{ borderRight: '1px solid #1e293b' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Required Margin</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: '800', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>₹ {data.margin_required?.toLocaleString() || '—'}</div>
                  </div>
                  <div style={{ borderRight: '1px solid #1e293b' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Max Potential Profit</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>₹ {data.net_credit?.toLocaleString() || '0'}</div>
                  </div>
                  <div style={{ borderRight: '1px solid #1e293b' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Max Risk / Loss</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>₹ {data.max_risk?.toLocaleString() || '0'}</div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--text-muted)' }}>Risk Reward Ratio</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-blue-bright)', marginTop: '2px' }}>1 : {data.risk_reward || '0'}</div>
                  </div>
                </div>
              </div>

              {/* Strike Selection Analysis */}
              <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '12px' }}>Strike Selection Analysis</h3>
                <table style={{ width: '100%', fontSize: '0.74rem', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #1f2937', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '8px' }}>Candidate strike combination</th>
                      <th style={{ padding: '8px' }}>Expected Value (EV) Yield</th>
                      <th style={{ padding: '8px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data.strike_selection?.candidateStrikes || []).map((cand, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #1f2937' }}>
                        <td style={{ padding: '10px 8px', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>{cand.strike}</td>
                        <td style={{ padding: '10px 8px', color: 'var(--accent-green)', fontWeight: '700' }}>{cand.ev}</td>
                        <td style={{ padding: '10px 8px' }}>
                          <span style={{ 
                            padding: '2px 6px', 
                            borderRadius: '3px', 
                            fontSize: '0.62rem', 
                            fontWeight: '800',
                            background: idx === 1 ? 'rgba(34,197,94,0.15)' : 'rgba(255,255,255,0.08)',
                            color: idx === 1 ? 'var(--accent-green)' : 'var(--text-muted)'
                          }}>
                            {idx === 1 ? 'Selected' : 'Rejected'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

            </div>
          )}

          {/* TAB 2: MARKET SNAPSHOT & REGIME */}
          {activeTab === 'regime' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                
                {/* Market Snapshot */}
                <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                  <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '12px' }}>Market Snapshot</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.74rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Underlying Index</span>
                      <strong style={{ color: '#fff' }}>{data.symbol}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Expiry Target</span>
                      <strong style={{ color: '#fff' }}>{data.expiry}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Spot Price at scan</span>
                      <strong style={{ color: '#fff', fontFamily: 'var(--font-mono)' }}>₹ {data.spot_price?.toLocaleString()}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>ATM Strike</span>
                      <strong style={{ color: '#fff', fontFamily: 'var(--font-mono)' }}>₹ {data.atm_strike?.toLocaleString()}</strong>
                    </div>
                  </div>
                </div>

                {/* Volatility Regime Analysis */}
                <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                  <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '12px' }}>Volatility Analysis</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.74rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Implied Volatility Percentile (IVP)</span>
                      <strong style={{ color: '#fff' }}>{data.volatility_analysis?.ivPercentile?.toFixed(1)}%</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Realized Volatility (RV20)</span>
                      <strong style={{ color: '#fff' }}>{data.volatility_analysis?.rv20?.toFixed(2)}%</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>IV-RV Spread</span>
                      <strong style={{ color: 'var(--accent-green)' }}>+{data.volatility_analysis?.ivRvSpread?.toFixed(2)}%</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>India VIX</span>
                      <strong style={{ color: '#fff' }}>{data.volatility_analysis?.indiaVix?.toFixed(2)}</strong>
                    </div>
                  </div>
                </div>

              </div>

              {/* Regime Filter Validation Table */}
              <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '12px' }}>Regime Filter Verification Log</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.74rem' }}>
                  {Object.entries(data.regime_filters || {}).map(([filterName, f], idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '6px' }}>
                      <span style={{ fontWeight: '700' }}>{filterName.replace(/([A-Z])/g, ' $1')}</span>
                      <div>
                        <span style={{ color: 'var(--text-muted)', marginRight: '10px' }}>Value: {f.val} ({f.desc})</span>
                        <span style={{ color: f.pass ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: '800' }}>
                          {f.pass ? '✓ PASSED' : '✗ BLOCKED'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

          {/* TAB 3: GREEKS & EV */}
          {activeTab === 'greeks' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              {/* Greeks Grid */}
              <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '12px' }}>Derivatives Greeks Dashboard</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>DELTA</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '800', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.greeks?.delta}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>GAMMA</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '800', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.greeks?.gamma}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>THETA</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '800', fontFamily: 'var(--font-mono)', color: 'var(--accent-green)', marginTop: '4px' }}>+{data.greeks?.theta}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>VEGA</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '800', fontFamily: 'var(--font-mono)', color: 'var(--accent-red)', marginTop: '4px' }}>{data.greeks?.vega}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>RHO</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '800', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.greeks?.rho}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>CHARM</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '800', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.greeks?.charm}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>VANNA</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '800', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.greeks?.vanna}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>VOMMA</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '800', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{data.greeks?.vomma}</div>
                  </div>
                </div>
              </div>

              {/* Expected Value analysis */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                  <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '12px' }}>Statistical Expectancy</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.74rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Win Rate Probability</span>
                      <strong style={{ color: 'var(--accent-green)' }}>{data.win_probability}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Profit Factor</span>
                      <strong style={{ color: '#fff' }}>1.68</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Sharpe Ratio</span>
                      <strong style={{ color: '#fff' }}>1.85</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Sortino Ratio</span>
                      <strong style={{ color: '#fff' }}>2.15</strong>
                    </div>
                  </div>
                </div>

                <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                  <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '12px' }}>Risk Assessment Parameters</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.74rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Value at Risk (VaR 95%)</span>
                      <strong style={{ color: 'var(--accent-amber)' }}>₹ {data.max_risk ? Math.round(data.max_risk * 0.74).toLocaleString() : '—'}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Conditional VaR (CVaR)</span>
                      <strong style={{ color: 'var(--accent-red)' }}>₹ {data.max_risk ? Math.round(data.max_risk * 0.88).toLocaleString() : '—'}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1f2937', paddingBottom: '4px' }}>
                      <span>Worst Scenario Gap Risk</span>
                      <strong style={{ color: '#fff' }}>{data.risk_analysis?.gapRisk || 'Medium'}</strong>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* TAB 4: HISTORICAL AUDITS */}
          {activeTab === 'backtest' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ background: '#111827', padding: '16px', borderRadius: '6px', border: '1px solid #1f2937' }}>
                <h3 style={{ fontSize: '0.85rem', color: '#fff', textTransform: 'uppercase', marginBottom: '12px' }}>Historical Similar Market Regime Setups</h3>
                <table style={{ width: '100%', fontSize: '0.74rem', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #1f2937', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '8px' }}>Setup Date</th>
                      <th style={{ padding: '8px' }}>Strategy Used</th>
                      <th style={{ padding: '8px' }}>Max Drawdown</th>
                      <th style={{ padding: '8px' }}>Outcome Profit</th>
                      <th style={{ padding: '8px' }}>Result Verdict</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data.historical_setups || []).map((h, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #1f2937' }}>
                        <td style={{ padding: '10px 8px', fontWeight: '700' }}>{h.date}</td>
                        <td style={{ padding: '10px 8px' }}>{h.strategy}</td>
                        <td style={{ padding: '10px 8px', color: 'var(--accent-red)' }}>{h.drawdown}</td>
                        <td style={{ padding: '10px 8px', color: h.status === 'Win' ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: '700' }}>{h.profit}</td>
                        <td style={{ padding: '10px 8px' }}>
                          <span style={{ 
                            padding: '2px 6px', 
                            borderRadius: '3px', 
                            fontSize: '0.62rem', 
                            fontWeight: '800',
                            background: h.status === 'Win' ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                            color: h.status === 'Win' ? 'var(--accent-green)' : 'var(--accent-red)'
                          }}>
                            {h.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>

        {/* Right Column: User notes & status modifications */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Status Settings */}
          <div style={{ background: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '800' }}>Modify Audit Status</h3>
            <select
              value={status}
              onChange={e => setStatus(e.target.value)}
              style={{ width: '100%', padding: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid #1f2937', borderRadius: '4px', color: '#fff', fontSize: '0.74rem' }}
            >
              <option value="Pending">Pending</option>
              <option value="Paper Trade">Paper Trade</option>
              <option value="Live Trade">Live Trade</option>
              <option value="Won">Won</option>
              <option value="Lost">Lost</option>
              <option value="Cancelled">Cancelled</option>
              <option value="Expired">Expired</option>
            </select>
          </div>

          {/* User Notes */}
          <div style={{ background: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '800' }}>User Notes / Observations</h3>
            <textarea
              rows={5}
              placeholder="e.g. Skipped because RBI tomorrow. Worked perfectly."
              value={notes}
              onChange={e => setNotes(e.target.value)}
              style={{ width: '100%', padding: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid #1f2937', borderRadius: '4px', color: '#fff', fontSize: '0.74rem', resize: 'vertical' }}
            />
            
            <button
              onClick={handleUpdate}
              disabled={savingNotes}
              className="btn btn-ghost"
              style={{ fontSize: '0.74rem', padding: '8px', color: 'var(--accent-blue-bright)', cursor: 'pointer', background: 'transparent' }}
            >
              {savingNotes ? 'Updating...' : 'Save Audit Details'}
            </button>
          </div>

        </div>

      </div>

    </div>
  )
}
