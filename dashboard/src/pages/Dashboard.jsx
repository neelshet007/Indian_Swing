import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import UniverseBadge from '../components/UniverseBadge'

function getConvictionClass(score) {
  if (score >= 0.75) return 'high'
  if (score >= 0.55) return 'medium'
  return 'low'
}

function RecCard({ rec, universes }) {
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
            {universes && universes.length > 0 && (
              <span style={{ marginLeft: 6 }}>
                <UniverseBadge universes={universes} size="tiny" />
              </span>
            )}
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
  const navigate = useNavigate()
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [currentScan, setCurrentScan] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [scanStatus, setScanStatus] = useState(null)
  const [badgeCache, setBadgeCache] = useState({})

  function formatDuration(start, end) {
    if (!start || !end) return null
    const diffMs = new Date(end) - new Date(start)
    const diffSec = Math.floor(diffMs / 1000)
    if (diffSec < 60) return `${diffSec}s`
    const mins = Math.floor(diffSec / 60)
    const secs = diffSec % 60
    return `${mins}m ${secs}s`
  }

  // Presentation-only: load NIFTY 500 badges for unique symbols
  const loadBadges = async (recs) => {
    const symbols = [...new Set(recs.map(r => r.symbol).filter(Boolean))]
    if (symbols.length === 0) return
    const badges = {}
    await Promise.all(
      symbols.map(async (sym) => {
        try {
          const res = await fetch(`/api/stocks/universe-badges?symbol=${sym}`)
          const json = await res.json()
          badges[sym] = json.universes || []
        } catch { badges[sym] = [] }
      })
    )
    setBadgeCache(prev => ({ ...prev, ...badges }))
  }

  const loadLatest = async () => {
    setLoading(true)
    setError(null)
    try {
      const scanRes = await axios.get('/api/scans/latest')
      const scan = scanRes.data
      setCurrentScan(scan)
      setSelectedDate(scan.scan_date)
      
      const recsRes = await axios.get(`/api/recommendations/${scan.scan_uuid}`)
      setRecommendations(recsRes.data)
      loadBadges(recsRes.data)

      setScanStatus({
        status: 'completed',
        total_stocks: scan.total_stocks,
        completed: scan.stocks_scanned,
        failed: scan.failed_stocks,
        errors: scan.errors || []
      })
    } catch (err) {
      if (err.response?.status === 404) {
        setCurrentScan(null)
        setRecommendations([])
        setScanStatus(null)
      } else {
        setError(err.response?.data?.detail || 'Failed to load latest scan.')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadScanForDate = async (dateStr) => {
    setLoading(true)
    setError(null)
    try {
      const scanRes = await axios.get(`/api/scans/date/${dateStr}`)
      const scan = scanRes.data
      setCurrentScan(scan)
      
      const recsRes = await axios.get(`/api/recommendations/${scan.scan_uuid}`)
      setRecommendations(recsRes.data)
      loadBadges(recsRes.data)

      setScanStatus({
        status: 'completed',
        total_stocks: scan.total_stocks,
        completed: scan.stocks_scanned,
        failed: scan.failed_stocks,
        errors: scan.errors || []
      })
    } catch (err) {
      if (err.response?.status === 404) {
        setCurrentScan(null)
        setRecommendations([])
        setScanStatus(null)
      } else {
        setError(err.response?.data?.detail || `Failed to load scan for ${dateStr}.`)
      }
    } finally {
      setLoading(false)
    }
  }

  const triggerScan = async (force = false) => {
    setScanning(true)
    setScanStatus({
      status: 'running',
      current_stage: 'Initializing Scan...',
      current_symbol: '',
      completed: 0,
      total_stocks: 0,
      failed: 0,
      errors: []
    })
    try {
      const { data } = await axios.post(`/api/scanner/run?scan_date=${selectedDate}&force_refresh=${force}`)
      if (data.status === 'completed') {
        setScanning(false)
        loadScanForDate(selectedDate)
        return
      }
      pollProgress(data.scan_date)
    } catch (err) {
      if (err.response?.status === 409) {
        pollProgress(selectedDate)
      } else {
        setError(err.response?.data?.detail || 'Failed to start scan.')
        setScanning(false)
      }
    }
  }

  const pollProgress = async (dateStr) => {
    try {
      const { data } = await axios.get('/api/scanner/progress')
      setScanStatus(data)
      if (data.status === 'running') {
        setTimeout(() => pollProgress(dateStr), 1000)
        return
      }
      setScanning(false)
      if (data.status === 'completed') {
        setSelectedDate(dateStr)
        if (data.scan_uuid) {
          const scanRes = await axios.get(`/api/scans/uuid/${data.scan_uuid}`)
          setCurrentScan(scanRes.data)
          const recsRes = await axios.get(`/api/recommendations/${data.scan_uuid}`)
          setRecommendations(recsRes.data)
        } else {
          loadScanForDate(dateStr)
        }
      }
    } catch (_err) {
      setScanning(false)
    }
  }

  useEffect(() => {
    loadLatest()
    
    const checkRunningScan = async () => {
      try {
        const { data } = await axios.get('/api/scanner/progress')
        if (data.status === 'running') {
          setScanning(true)
          setScanStatus(data)
          pollProgress(data.scan_date || selectedDate)
        }
      } catch (_err) {}
    }
    checkRunningScan()
  }, [])

  const handleDateChange = (e) => {
    const d = e.target.value
    setSelectedDate(d)
    loadScanForDate(d)
  }

  const isToday = selectedDate === new Date().toISOString().split('T')[0]

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Trading Terminal</h1>
          <div className="page-subtitle" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', flexWrap: 'wrap' }}>
            <span className={`badge badge-${isToday ? 'live' : 'historical'}`} style={{ textTransform: 'uppercase', fontWeight: 600, background: isToday ? 'rgba(34,197,94,0.1)' : 'rgba(59,130,246,0.1)', color: isToday ? 'var(--accent-green)' : 'var(--accent-blue-bright)' }}>
              {isToday ? 'Live Scan Mode' : 'Historical Replay Mode'}
            </span>
            <span className={`badge badge-${scanning ? 'running' : currentScan ? 'completed' : 'pending'}`} style={{ textTransform: 'uppercase', fontWeight: 600 }}>
              {scanning ? 'Scanning' : currentScan ? 'Cached Snapshot Available' : 'No Scan Available'}
            </span>
            <span style={{ color: 'var(--text-secondary)' }}>
              {scanning 
                ? 'Processing stock universe...' 
                : currentScan 
                  ? `Viewing scan from ${new Date(currentScan.completed_at).toLocaleTimeString()} (v${currentScan.strategy_version})` 
                  : `No scan session loaded for ${selectedDate}`
              }
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '2px' }}>Trading Date</span>
            <input 
              type="date" 
              value={selectedDate} 
              max={new Date().toISOString().split('T')[0]}
              onChange={handleDateChange} 
              className="input-field" 
              style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-card)', color: 'var(--text-primary)', outline: 'none' }}
            />
          </div>
          <button className="btn btn-ghost" onClick={loadLatest} style={{ marginTop: '16px' }}>Reset to Latest</button>
          {currentScan && !scanning && (
            <button 
              className="btn btn-ghost" 
              onClick={() => triggerScan(true)} 
              style={{ marginTop: '16px', color: 'var(--accent-red)', borderColor: 'rgba(239, 68, 68, 0.3)' }}
            >
              Force Rescan
            </button>
          )}
          <button 
            className={`btn btn-primary ${scanning ? 'pulse' : ''}`} 
            onClick={() => triggerScan(false)} 
            disabled={scanning}
            style={{ marginTop: '16px' }}
          >
            {scanning ? 'Scanning...' : currentScan ? 'Run New Scan' : 'Run Scan'}
          </button>
        </div>
      </div>

      {scanStatus && (
        <div style={{ margin: '0 32px 20px', padding: '16px', background: 'var(--bg-card)', borderRadius: '8px', border: '1px solid var(--border)' }}>
          {scanStatus.status === 'running' ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <div style={{ color: 'var(--accent-blue-bright)', fontWeight: 600 }}>
                  {scanStatus.current_stage} {scanStatus.current_symbol ? `- ${scanStatus.current_symbol}` : ''}
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  {scanStatus.completed} / {scanStatus.total_stocks} ({scanStatus.total_stocks > 0 ? Math.round((scanStatus.completed / scanStatus.total_stocks) * 100) : 0}%)
                </div>
              </div>
              <div style={{ width: '100%', height: '12px', background: 'var(--border)', borderRadius: '6px', overflow: 'hidden', display: 'flex' }}>
                <div style={{ height: '100%', background: 'var(--accent-green)', width: `${((scanStatus.completed - (scanStatus.failed || 0)) / (scanStatus.total_stocks || 1)) * 100}%`, transition: 'width 0.3s ease' }} />
                <div style={{ height: '100%', background: 'var(--accent-red)', width: `${((scanStatus.failed || 0) / (scanStatus.total_stocks || 1)) * 100}%`, transition: 'width 0.3s ease' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--accent-green)', fontWeight: 500 }}>Success: {scanStatus.completed - (scanStatus.failed || 0)}</span>
                <span style={{ color: 'var(--accent-red)', fontWeight: 500 }}>Failed: {scanStatus.failed || 0}</span>
              </div>
            </>
          ) : (
            <div>
              <div style={{ color: 'var(--accent-green)', fontWeight: 600, fontSize: '1.05rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-green)' }} />
                Scan Completed
              </div>
              <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                <div><strong>Scan Date:</strong> {selectedDate}</div>
                <div><strong>Scanned:</strong> {scanStatus.total_stocks || (currentScan?.total_stocks)} Stocks</div>
                <div><strong>Recommendations:</strong> {recommendations.length}</div>
                {currentScan && (
                  <>
                    <div><strong>Scan Completed At:</strong> {currentScan.completed_at ? new Date(currentScan.completed_at).toLocaleString() : 'N/A'}</div>
                    {currentScan.started_at && currentScan.completed_at && (
                      <div><strong>Duration:</strong> {formatDuration(currentScan.started_at, currentScan.completed_at)}</div>
                    )}
                  </>
                )}
              </div>
              {currentScan && currentScan.scan_uuid && (
                <div style={{ marginTop: '16px' }}>
                  <button 
                    className="btn btn-ghost" 
                    onClick={() => navigate(`/analytics/${currentScan.scan_uuid}`)}
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)' }}
                  >
                    View Full Analytics →
                  </button>
                </div>
              )}
            </div>
          )}

          {scanStatus.errors && scanStatus.errors.length > 0 && (() => {
            const inactiveWarnings = scanStatus.errors.filter(e => e.startsWith('[INACTIVE]'))
            const runtimeErrors = scanStatus.errors.filter(e => !e.startsWith('[INACTIVE]'))
            return (
              <>
                {runtimeErrors.length > 0 && (
                  <div style={{ marginTop: '12px', padding: '10px 12px', background: 'rgba(239, 68, 68, 0.08)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.25)', maxHeight: '140px', overflowY: 'auto' }}>
                    <div style={{ fontSize: '0.78rem', color: 'var(--accent-red)', fontWeight: 700, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-red)' }} />
                      Scan Errors ({runtimeErrors.length})
                    </div>
                    {runtimeErrors.map((err, idx) => (
                      <div key={`err-${idx}`} style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontFamily: 'monospace', padding: '1px 0' }}>• {err}</div>
                    ))}
                  </div>
                )}
                {inactiveWarnings.length > 0 && (
                  <div style={{ marginTop: '10px', padding: '10px 12px', background: 'rgba(245, 158, 11, 0.07)', borderRadius: '6px', border: '1px solid rgba(245, 158, 11, 0.2)', maxHeight: '140px', overflowY: 'auto' }}>
                    <div style={{ fontSize: '0.78rem', color: '#f59e0b', fontWeight: 700, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#f59e0b' }} />
                      Inactive / Delisted Stocks ({inactiveWarnings.length}) — Skipped
                    </div>
                    {inactiveWarnings.map((warn, idx) => (
                      <div key={`warn-${idx}`} style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'monospace', padding: '1px 0' }}>
                        {warn.replace('[INACTIVE] ', '')}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )
          })()}
        </div>
      )}

      {loading ? (
        <div className="loader-container"><div className="loader" /></div>
      ) : error ? (
        <div className="empty-state">
          <div className="empty-title">Unable to load scan</div>
          <div className="empty-sub">{error}</div>
        </div>
      ) : !currentScan ? (
        <div className="empty-state">
          <div className="empty-title">No Scan Completed Yet</div>
          <div className="empty-sub">No scan has been run for {selectedDate}. Please run a scan to evaluate the market.</div>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">No Recommendations Found</div>
          <div className="empty-sub">Scan was completed successfully for {selectedDate}, but no stocks met the strategy criteria.</div>
        </div>
      ) : (
        <div className="rec-grid">
          {recommendations.map((rec) => (
            <RecCard key={rec.id} rec={rec} universes={badgeCache[rec.symbol]} />
          ))}
        </div>
      )}
    </div>
  )
}
