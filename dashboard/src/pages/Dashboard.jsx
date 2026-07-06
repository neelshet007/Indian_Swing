import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

function getConvictionClass(score) {
  if (score >= 0.75) return 'high'
  if (score >= 0.55) return 'medium'
  return 'low'
}

function ConfidenceBadge({ score }) {
  const cls = getConvictionClass(score)
  return (
    <div className="confidence-badge">
      <div className={`confidence-circle confidence-${cls}`}>
        {Math.round(score * 100)}%
      </div>
      <div className="confidence-label">{cls === 'high' ? 'Strong' : cls === 'medium' ? 'Moderate' : 'Weak'}</div>
    </div>
  )
}

function RecCard({ rec }) {
  const navigate = useNavigate()
  const cls = getConvictionClass(rec.confidence_score)

  return (
    <div
      className={`rec-card conviction-${cls} fade-in`}
      onClick={() => navigate(`/recommendation/${rec.id}`)}
    >
      <div className="rec-card-header">
        <div>
          <div className="rec-symbol">
            {rec.symbol?.replace('.NS', '')}
            <span style={{ marginLeft: 8, fontSize: '0.65rem', background: 'rgba(34,197,94,0.1)', color: 'var(--accent-green)', padding: '2px 6px', borderRadius: 3, fontWeight: 600 }}>
              {rec.direction}
            </span>
          </div>
          <div className="rec-name">{rec.company_name}</div>
          {rec.sector && (
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>{rec.sector}</div>
          )}
        </div>
        <ConfidenceBadge score={rec.confidence_score} />
      </div>

      <div className="rec-prices">
        <div className="price-item">
          <div className="price-label">Entry</div>
          <div className="price-value price-entry">₹{rec.entry_price?.toFixed(2)}</div>
        </div>
        <div className="price-item">
          <div className="price-label">Stop</div>
          <div className="price-value price-stop">₹{rec.stop_loss?.toFixed(2)}</div>
        </div>
        <div className="price-item">
          <div className="price-label">Target</div>
          <div className="price-value price-target">₹{rec.target_1?.toFixed(2)}</div>
        </div>
      </div>

      <div className="rec-meta">
        <span className="meta-pill strategy">{rec.strategy_name}</span>
        <span className="meta-pill rr">RR {rec.risk_reward?.toFixed(1)}</span>
        <span className="meta-pill days">{rec.holding_days}d hold</span>
        <span className={`badge badge-${rec.quality?.toLowerCase()}`}>{rec.quality}</span>
        <span className={`badge badge-${rec.risk_level?.toLowerCase()}`}>{rec.risk_level} risk</span>
      </div>

      {rec.reasons?.length > 0 && (
        <div className="rec-reasons">
          {rec.reasons.slice(0, 2).map((r, i) => (
            <div key={i} className="reason-item">
              <span className="reason-dot">•</span>
              <span>{r}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function StatsBar({ recs }) {
  const strong = recs.filter(r => r.confidence_score >= 0.75).length
  const avgRR = recs.length ? (recs.reduce((s, r) => s + (r.risk_reward || 0), 0) / recs.length).toFixed(2) : '—'
  const strategies = [...new Set(recs.map(r => r.strategy_name))].length

  return (
    <div className="stats-row">
      <div className="stat-card">
        <div className="stat-label">Opportunities</div>
        <div className="stat-value" style={{ color: 'var(--accent-blue-bright)' }}>{recs.length}</div>
        <div className="stat-change">Today's scan</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">High Conviction</div>
        <div className="stat-value stat-up">{strong}</div>
        <div className="stat-change">Score ≥ 75%</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Avg Risk/Reward</div>
        <div className="stat-value" style={{ color: 'var(--accent-purple)' }}>{avgRR}x</div>
        <div className="stat-change">Across all signals</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Strategies Active</div>
        <div className="stat-value" style={{ color: 'var(--accent-cyan)' }}>{strategies}</div>
        <div className="stat-change">Signal sources</div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [recs, setRecs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all')
  const [scanning, setScanning] = useState(false)
  const [scanDate, setScanDate] = useState('')
  const [scanStatus, setScanStatus] = useState(null)
  const [scanSummary, setScanSummary] = useState(null)

  const fetchRecs = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {}
      if (scanDate) params.scan_date = scanDate
      const { data } = await axios.get('/api/recommendations/', { params })
      setRecs(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load recommendations. Is the API running?')
    } finally {
      setLoading(false)
    }
  }

  const triggerScan = async () => {
    setScanning(true)
    setScanStatus({ current_stage: "Starting..." })
    setScanSummary(null)
    try {
      const response = await axios.post('/api/scanner/run', null, {
        params: scanDate ? { scan_date: scanDate } : {}
      })
      if (response.data.status === 'error') {
         alert(response.data.detail)
         setScanning(false)
         return
      }
      pollProgress()
    } catch (e) {
      alert('Scan failed: ' + (e.response?.data?.detail || e.message))
      setScanning(false)
    }
  }

  const pollProgress = async () => {
    try {
      const { data } = await axios.get('/api/scanner/progress')
      
      if (data.current_stage !== "Idle" && data.current_stage !== "Completed") {
        setScanStatus(data)
        setTimeout(pollProgress, 500) // Poll twice a second for real-time updates
      } else if (data.current_stage === "Completed") {
        setScanning(false)
        setScanStatus(null)
        setScanSummary(`Scan finished! Found recommendations.`)
        fetchRecs()
        
        // Reset state on server to Idle so next scan can trigger properly
        // (FastAPI will eventually handle this properly on next /run)
      } else {
        // Idle
        setScanning(false)
        setScanStatus(null)
      }
    } catch (e) {
      console.error("Polling error", e)
      setScanning(false)
      setScanStatus(null)
    }
  }

  useEffect(() => { fetchRecs() }, [scanDate])

  const filtered = filter === 'all' ? recs
    : filter === 'strong' ? recs.filter(r => r.confidence_score >= 0.75)
    : filter === 'medium' ? recs.filter(r => r.confidence_score >= 0.55 && r.confidence_score < 0.75)
    : recs.filter(r => r.quality === filter.toUpperCase())

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Today's Opportunities</h1>
          <div className="page-subtitle">
            {recs.length > 0
              ? `${recs.length} signals across ${[...new Set(recs.map(r => r.strategy_name))].length} strategies — ranked by conviction`
              : 'Run a scan to discover trading opportunities'}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <input
            type="date"
            value={scanDate}
            onChange={e => setScanDate(e.target.value)}
            style={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              color: 'var(--text-primary)', borderRadius: 6, padding: '7px 12px',
              fontSize: '0.85rem', fontFamily: 'var(--font-sans)'
            }}
          />
          <button className="btn btn-ghost" onClick={fetchRecs}>↻ Refresh</button>
          <button
            className={`btn btn-primary ${scanning ? 'pulse' : ''}`}
            onClick={triggerScan}
            disabled={scanning}
          >
            {scanning 
              ? '⟳ Scanning...'
              : '▶ Run Scan'}
          </button>
        </div>
      </div>

      {scanSummary && (
        <div style={{ padding: '0 32px 12px', color: 'var(--accent-green)', fontWeight: 500 }}>
          ✓ {scanSummary}
        </div>
      )}

      {scanStatus && scanStatus.total_stocks > 0 && (
        <div style={{ margin: '0 32px 20px', padding: '16px', background: 'var(--bg-card)', borderRadius: '8px', border: '1px solid var(--border)' }}>
           <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: 'var(--text-primary)' }}>Scan Progress</h3>
           <div style={{ display: 'flex', gap: '20px', fontSize: '0.9rem', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
             <div><strong>Total:</strong> {scanStatus.total_stocks}</div>
             <div><strong style={{ color: 'var(--accent-green)' }}>Completed:</strong> {scanStatus.completed}</div>
             <div><strong style={{ color: 'var(--accent-red)' }}>Failed:</strong> {scanStatus.failed}</div>
             <div><strong>Remaining:</strong> {scanStatus.remaining}</div>
           </div>
           
           <div style={{ marginTop: '16px', background: 'var(--bg)', padding: '12px', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--accent-blue-bright)' }}>
                 Processing: {scanStatus.current_symbol}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                 Stage: {scanStatus.current_stage}
              </div>
           </div>
        </div>
      )}

      {recs.length > 0 && <StatsBar recs={recs} />}

      <div style={{ padding: '0 32px 12px', display: 'flex', gap: 8 }}>
        {['all', 'strong', 'medium'].map(f => (
          <button
            key={f}
            className={`btn btn-ghost ${filter === f ? 'btn-primary' : ''}`}
            style={{ textTransform: 'capitalize', fontSize: '0.8rem', padding: '5px 14px' }}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All Signals' : f === 'strong' ? '🟢 High Conviction' : '🔵 Moderate'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loader-container"><div className="loader" /></div>
      ) : error ? (
        <div className="empty-state">
          <div className="empty-icon">⚠</div>
          <div className="empty-title">Unable to load data</div>
          <div className="empty-sub">{error}</div>
          <button className="btn btn-primary" style={{ marginTop: 20 }} onClick={fetchRecs}>Retry</button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <div className="empty-title">No recommendations yet</div>
          <div className="empty-sub">Run a market scan to discover swing trading opportunities</div>
          <button className="btn btn-primary" style={{ marginTop: 20 }} onClick={triggerScan}>
            Run Scan Now
          </button>
        </div>
      ) : (
        <div className="rec-grid">
          {filtered.map((rec, i) => (
            <RecCard key={rec.id || i} rec={rec} />
          ))}
        </div>
      )}
    </div>
  )
}
