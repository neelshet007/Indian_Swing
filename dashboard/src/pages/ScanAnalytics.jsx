import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'

const amrcStages = ['Universe', 'Universe Filter', 'Market Regime Filter', 'Quality Filter', 'Momentum Ranking', 'Relative Strength', 'Trend Filter', 'Volatility Filter', 'Volume Confirmation', 'Entry Trigger', 'BUY']
const vcpStages = ['Universe', 'Market Filter', 'Sector Filter', 'Liquidity', 'Trend', 'Stage', 'Relative Strength', 'VCP', 'Breakout', 'Risk', 'BUY']

function Card({ title, children, noPad = false }) {
  return (
    <div style={{ background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
      {title && <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', fontWeight: 700, fontSize: '0.9rem', color: '#fff', background: 'rgba(255,255,255,0.02)' }}>{title}</div>}
      <div style={{ padding: noPad ? 0 : '16px 20px' }}>{children}</div>
    </div>
  )
}

function Metric({ label, value, color }) {
  return (
    <div style={{ flex: 1, minWidth: 140, padding: '16px 20px', background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)' }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: '1.8rem', fontWeight: 800, color: color || '#fff', fontFamily: 'var(--font-mono)' }}>{value}</div>
    </div>
  )
}

function FunnelRow({ stage, pass, fail, total, onClick, active }) {
  const pct = total > 0 ? (pass / total * 100) : 0
  return (
    <div 
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 16, padding: '12px 16px', 
        borderBottom: '1px solid rgba(255,255,255,0.04)', cursor: 'pointer',
        background: active ? 'rgba(255,255,255,0.06)' : 'transparent',
        transition: 'background 0.2s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.04)'}
      onMouseLeave={e => e.currentTarget.style.background = active ? 'rgba(255,255,255,0.06)' : 'transparent'}
    >
      <div style={{ width: 140, fontWeight: 600, color: '#fff', fontSize: '0.85rem' }}>{stage}</div>
      <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', height: 8, borderRadius: 4, overflow: 'hidden', display: 'flex' }}>
        <div style={{ width: `${pct}%`, background: 'var(--accent-green)', transition: 'width 0.5s' }} />
        <div style={{ width: `${100 - pct}%`, background: 'var(--accent-red)', opacity: 0.8, transition: 'width 0.5s' }} />
      </div>
      <div style={{ width: 220, display: 'flex', gap: 16, fontSize: '0.8rem', fontFamily: 'var(--font-mono)', textAlign: 'right' }}>
        <div style={{ width: 80, color: 'var(--accent-green)' }}>{pass} PASS</div>
        <div style={{ width: 80, color: 'var(--accent-red)' }}>{fail} FAIL</div>
        <div style={{ width: 50, color: 'var(--text-secondary)' }}>{pct.toFixed(1)}%</div>
      </div>
    </div>
  )
}

export default function ScanAnalytics() {
  const { uuid } = useParams()
  const navigate = useNavigate()
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [scan, setScan] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [history, setHistory] = useState([])
  
  const [activeStage, setActiveStage] = useState('Trend')
  const [search, setSearch] = useState('')

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true)
      try {
        let targetUuid = uuid
        if (!targetUuid) {
          const latestRes = await axios.get('/api/scans/latest')
          targetUuid = latestRes.data.scan_uuid
        }

        const [scanRes, anRes, histRes] = await Promise.all([
          axios.get(`/api/scans/uuid/${targetUuid}`),
          axios.get(`/api/scans/${targetUuid}/analytics`),
          axios.get('/api/scans/history/summary')
        ])

        setScan(scanRes.data)
        if (anRes.data.error) {
          setError(anRes.data.error)
        } else {
          setAnalytics(anRes.data)
          // Default to first stage with failures if possible
          const funnel = anRes.data.funnel || {}
          const currentStages = scanRes.data?.strategy_name === 'amrc' ? amrcStages : vcpStages
          const firstFail = currentStages.find(s => funnel[s] && funnel[s].fail > 0)
          setActiveStage(firstFail || (scanRes.data?.strategy_name === 'amrc' ? 'Universe Filter' : 'Trend'))
        }
        
        // Reverse history for chron order in charts
        setHistory([...histRes.data].reverse())
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load analytics')
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [uuid])

  if (loading) return <div className="loader-container"><div className="loader" /></div>

  if (error) return (
    <div style={{ padding: '40px 32px', textAlign: 'center' }}>
      <div style={{ color: 'var(--accent-red)', fontSize: '1.1rem', marginBottom: 16 }}>{error}</div>
      <button className="btn btn-ghost" onClick={() => navigate('/')}>← Back to Dashboard</button>
    </div>
  )

  if (!analytics || !scan) return null

  const { funnel, failure_reasons, stock_journeys, pipeline_health } = analytics

  // Process drill down
  const stageStats = funnel[activeStage] || { pass: 0, fail: 0 }
  
  // Search filter for all stocks
  const filteredJourneys = Object.entries(stock_journeys).filter(([sym]) => sym.toLowerCase().includes(search.toLowerCase()))

  return (
    <div style={{ padding: '24px 32px', color: 'var(--text-primary)', maxWidth: 1600, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: '0 0 8px 0', fontSize: '1.8rem', fontWeight: 800, color: '#fff' }}>Institutional Analytics</h1>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Scan Date: <strong style={{ color: '#fff' }}>{scan.scan_date}</strong> · Strategy: <strong style={{ color: '#fff' }}>{scan.strategy_name} v{scan.strategy_version}</strong> · {scan.scan_uuid}
          </div>
        </div>
        <button className="btn btn-ghost" onClick={() => navigate('/')}>← Back to Dashboard</button>
      </div>

      {/* Top Metrics */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Metric label="Universe" value={pipeline_health.total_stocks} />
        <Metric label="Recommendations" value={scan.recommendations_created} color="var(--accent-green)" />
        <Metric label="Data Load Errors" value={pipeline_health.failed_data_load} color={pipeline_health.failed_data_load > 0 ? 'var(--accent-red)' : 'var(--text-muted)'} />
        <Metric label="Success Rate" value={`${((scan.recommendations_created / pipeline_health.total_stocks) * 100).toFixed(1)}%`} color="var(--accent-blue-bright)" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 3fr) minmax(0, 2fr)', gap: 24 }}>
        
        {/* Funnel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <Card title="Strategy Funnel (Click Stage to Drill Down)" noPad>
            <div style={{ padding: '8px 0' }}>
              {(scan?.strategy_name === 'amrc' ? amrcStages : vcpStages).map(stage => {
                if (!funnel[stage] && stage !== 'Universe') return null
                
                let pass = 0, fail = 0, total = 0
                if (stage === 'Universe') {
                  pass = funnel.Universe?.pass || pipeline_health.total_stocks
                  fail = 0
                  total = pass
                } else if (stage === 'BUY') {
                  pass = funnel.BUY?.pass || scan.recommendations_created
                  fail = 0
                  total = pass
                } else {
                  pass = funnel[stage].pass
                  fail = funnel[stage].fail
                  total = pass + fail
                }

                return (
                  <FunnelRow 
                    key={stage} stage={stage} pass={pass} fail={fail} total={total}
                    active={activeStage === stage}
                    onClick={() => setActiveStage(stage)}
                  />
                )
              })}
            </div>
          </Card>

          {/* Historical Chart */}
          <Card title="Historical Recommendations (30 Days)">
            <div style={{ height: 260, width: '100%', marginTop: 10 }}>
              <ResponsiveContainer>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="scan_date" stroke="var(--text-muted)" fontSize={11} tickMargin={10} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} tickFormatter={v => Math.round(v)} />
                  <RechartsTooltip 
                    contentStyle={{ background: '#0b0f1a', border: '1px solid var(--border)', borderRadius: 8 }}
                    itemStyle={{ color: '#fff', fontSize: '0.8rem', fontWeight: 600 }}
                    labelStyle={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: 4 }}
                  />
                  <Line type="monotone" dataKey="recommendations" name="BUY Signals" stroke="var(--accent-green)" strokeWidth={2} dot={{ r: 4, fill: '#0b0f1a', strokeWidth: 2 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Drill Down & Failures */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          
          <Card title={`Failure Reasons: ${activeStage}`}>
            {(!failure_reasons[activeStage] || Object.keys(failure_reasons[activeStage]).length === 0) ? (
              <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No failures recorded for this stage.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {Object.entries(failure_reasons[activeStage])
                  .sort((a,b) => b[1] - a[1])
                  .map(([reason, count]) => (
                  <div key={reason} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ flex: 1, fontSize: '0.82rem', color: '#fff' }}>{reason}</div>
                    <div style={{ width: 50, textAlign: 'right', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-red)' }}>{count}</div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Stock Journeys" noPad>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
              <input 
                type="text" 
                placeholder="Search symbol..." 
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{ 
                  width: '100%', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)', 
                  padding: '8px 12px', borderRadius: 6, color: '#fff', fontSize: '0.85rem' 
                }}
              />
            </div>
            <div style={{ maxHeight: 400, overflowY: 'auto' }}>
              {filteredJourneys.length === 0 ? (
                <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>No stocks match search.</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                  <thead>
                    <tr style={{ background: 'rgba(255,255,255,0.02)' }}>
                      <th style={{ padding: '10px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600 }}>Symbol</th>
                      <th style={{ padding: '10px 16px', textAlign: 'right', color: 'var(--text-muted)', fontWeight: 600 }}>Outcome</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredJourneys.slice(0, 100).map(([sym, j]) => {
                      const isBuy = j.stages.BUY === 'PASS'
                      return (
                        <tr key={sym} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                          <td style={{ padding: '10px 16px', fontWeight: 600, color: '#fff' }}>{sym}</td>
                          <td style={{ padding: '10px 16px', textAlign: 'right' }}>
                            {isBuy ? (
                              <span style={{ color: 'var(--accent-green)', fontWeight: 700 }}>BUY</span>
                            ) : (
                              <span style={{ color: 'var(--accent-red)' }}>Failed at {j.failed_at || 'Data'}</span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </Card>
        </div>

      </div>
    </div>
  )
}
