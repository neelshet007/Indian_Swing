import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

function getConvictionClass(score) {
  if (score >= 0.75) return 'high'
  if (score >= 0.55) return 'medium'
  return 'low'
}

function RecCard({ rec }) {
  const navigate = useNavigate()
  const cls = getConvictionClass(rec.confidence_score)
  return (
    <div className={`rec-card conviction-${cls} fade-in`} onClick={() => navigate(`/recommendation/${rec.id}`)}>
      <div className="rec-card-header">
        <div>
          <div className="rec-symbol">
            {rec.symbol}
            <span style={{ marginLeft: 8, fontSize: '0.65rem', background: 'rgba(34,197,94,0.1)', color: 'var(--accent-green)', padding: '2px 6px', borderRadius: 3, fontWeight: 600 }}>
              {rec.action}
            </span>
          </div>
          <div className="rec-name">{rec.company_name}</div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>{rec.exchange} {rec.sector ? `- ${rec.sector}` : ''}</div>
        </div>
        <div className={`confidence-circle confidence-${cls}`}>{Math.round(rec.confidence_score * 100)}%</div>
      </div>

      <div className="rec-prices">
        <div className="price-item">
          <div className="price-label">Entry</div>
          <div className="price-value price-entry">Rs {rec.entry_price?.toFixed(2)}</div>
        </div>
        <div className="price-item">
          <div className="price-label">Stop</div>
          <div className="price-value price-stop">Rs {rec.stop_loss?.toFixed(2)}</div>
        </div>
        <div className="price-item">
          <div className="price-label">Target</div>
          <div className="price-value price-target">Rs {rec.target_1?.toFixed(2)}</div>
        </div>
      </div>

      <div className="rec-meta">
        <span className="meta-pill strategy">{rec.strategy_name}</span>
        <span className="meta-pill rr">RR {rec.risk_reward?.toFixed(1)}</span>
        <span className="meta-pill days">{rec.holding_days}d</span>
        <span className={`badge badge-${rec.quality?.toLowerCase()}`}>{rec.quality}</span>
      </div>

      {rec.reasons?.slice(0, 2).map((reason, index) => (
        <div key={`${rec.id}-${index}`} className="reason-item">
          <span className="reason-dot">•</span>
          <span>{reason}</span>
        </div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [snapshot, setSnapshot] = useState({ scan: null, recommendations: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [scanStatus, setScanStatus] = useState(null)

  const loadSnapshot = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axios.get('/api/recommendations/latest')
      setSnapshot(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load latest scan snapshot.')
    } finally {
      setLoading(false)
    }
  }

  const triggerScan = async () => {
    setScanning(true)
    await axios.post('/api/scanner/run')
    pollProgress()
  }

  const pollProgress = async () => {
    try {
      const { data } = await axios.get('/api/scanner/progress')
      setScanStatus(data)
      if (data.status === 'running') {
        setTimeout(pollProgress, 1000)
        return
      }
      setScanning(false)
      if (data.status === 'completed') {
        loadSnapshot()
      }
    } catch (_err) {
      setScanning(false)
    }
  }

  useEffect(() => {
    loadSnapshot()
  }, [])

  const scan = snapshot.scan
  const recommendations = snapshot.recommendations || []

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Latest Completed Scan</h1>
          <div className="page-subtitle">
            {scan
              ? `${scan.recommendations_created} recommendations from ${scan.stocks_scanned} scanned stocks`
              : 'No completed scan is available yet'}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost" onClick={loadSnapshot}>Refresh</button>
          <button className={`btn btn-primary ${scanning ? 'pulse' : ''}`} onClick={triggerScan} disabled={scanning}>
            {scanning ? 'Scanning...' : 'Run Scan'}
          </button>
        </div>
      </div>

      {scan && (
        <div style={{ margin: '0 32px 20px', padding: '16px', background: 'var(--bg-card)', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', gap: '18px', flexWrap: 'wrap', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            <div><strong>Scan Date:</strong> {scan.scan_date}</div>
            <div><strong>Market:</strong> {scan.market_status}</div>
            <div><strong>Scanned:</strong> {scan.stocks_scanned}/{scan.total_stocks}</div>
            <div><strong>Failed:</strong> {scan.failed_stocks}</div>
          </div>
          <div style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            <strong>Filter Summary:</strong> {Object.entries(scan.filter_summary || {}).map(([key, value]) => `${key} ${value}`).join(' • ') || 'No summary'}
          </div>
        </div>
      )}

      {scanStatus?.status === 'running' && (
        <div style={{ margin: '0 32px 20px', padding: '16px', background: 'var(--bg-card)', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ color: 'var(--accent-blue-bright)', fontWeight: 600 }}>
            {scanStatus.current_stage} {scanStatus.current_symbol ? `- ${scanStatus.current_symbol}` : ''}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 6 }}>
            Completed {scanStatus.completed} of {scanStatus.total_stocks} - Failed {scanStatus.failed}
          </div>
        </div>
      )}

      {loading ? (
        <div className="loader-container"><div className="loader" /></div>
      ) : error ? (
        <div className="empty-state">
          <div className="empty-title">Unable to load scan</div>
          <div className="empty-sub">{error}</div>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">No recommendations yet</div>
          <div className="empty-sub">Run a scan when you are ready to evaluate the latest market state.</div>
        </div>
      ) : (
        <div className="rec-grid">
          {recommendations.map((rec) => (
            <RecCard key={rec.id} rec={rec} />
          ))}
        </div>
      )}
    </div>
  )
}
