import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import axios from 'axios'
import { createChart, CandlestickSeries } from 'lightweight-charts'

function ReplayChart({ candles, signal }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const seriesRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return
    if (!chartRef.current) {
      const chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height: 300,
        layout: { background: { color: '#0f1629' }, textColor: '#8899b5' },
        grid: { vertLines: { color: 'rgba(255,255,255,0.03)' }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
        rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)' },
        timeScale: { borderColor: 'rgba(255,255,255,0.06)', timeVisible: true },
      })
      const series = chart.addSeries(CandlestickSeries, {
        upColor: '#22c55e', downColor: '#ef4444',
        borderVisible: false, wickUpColor: '#22c55e', wickDownColor: '#ef4444',
      })
      chartRef.current = chart
      seriesRef.current = series
    }
  }, [])

  useEffect(() => {
    if (!seriesRef.current || !candles?.length) return
    const data = candles.map(c => ({ time: c.date, open: c.open, high: c.high, low: c.low, close: c.close }))
    seriesRef.current.setData(data)
    chartRef.current.timeScale().scrollToRealTime()

    if (signal) {
      ['entry', 'stop', 'target_1'].forEach(k => {
        if (signal[k]) {
          try {
            seriesRef.current.createPriceLine({
              price: signal[k],
              color: k === 'entry' ? '#4f8ef7' : k === 'stop' ? '#ef4444' : '#22c55e',
              lineWidth: 1, lineStyle: 2,
              title: k === 'entry' ? `Entry` : k === 'stop' ? 'Stop' : 'T1',
            })
          } catch (_) {}
        }
      })
    }
  }, [candles, signal])

  return <div ref={containerRef} style={{ width: '100%' }} />
}

export default function ReplayPage() {
  const [searchParams] = useSearchParams()
  const [symbol, setSymbol] = useState(searchParams.get('symbol') || 'RELIANCE.NS')
  const [strategy, setStrategy] = useState(searchParams.get('strategy') || 'EMABreakout')
  const [startDate, setStartDate] = useState('2023-01-01')
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0])

  const [sessionId, setSessionId] = useState(null)
  const [state, setState] = useState(null)
  const [loading, setLoading] = useState(false)
  const [strategies, setStrategies] = useState([])
  const [playing, setPlaying] = useState(false)
  const playRef = useRef(null)

  useEffect(() => {
    axios.get('/api/strategies/').then(({ data }) => setStrategies(data.map(s => s.name))).catch(() => {})
  }, [])

  const createSession = async () => {
    setLoading(true)
    try {
      const { data } = await axios.post('/api/replay/sessions', {
        symbol, strategy_name: strategy, start_date: startDate, end_date: endDate
      })
      setSessionId(data.session_id)
      setState(data.state)
    } catch (e) {
      alert('Failed to create replay session: ' + (e.response?.data?.detail || e.message))
    } finally {
      setLoading(false)
    }
  }

  const step = async (dir = 'forward', steps = 1) => {
    if (!sessionId) return
    try {
      const { data } = await axios.post(`/api/replay/sessions/${sessionId}/${dir}`, null, { params: { steps } })
      setState(data)
      if (data.is_complete && playing) stopPlay()
    } catch (e) { console.error(e) }
  }

  const restart = async () => {
    if (!sessionId) return
    const { data } = await axios.post(`/api/replay/sessions/${sessionId}/restart`)
    setState(data)
    stopPlay()
  }

  const startPlay = (speed = 1) => {
    setPlaying(true)
    playRef.current = setInterval(() => step('forward', 1), 1200 / speed)
  }

  const stopPlay = () => {
    setPlaying(false)
    if (playRef.current) { clearInterval(playRef.current); playRef.current = null }
  }

  const togglePlay = () => playing ? stopPlay() : startPlay()

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Replay Engine</h1>
          <div className="page-subtitle">Candle-by-candle simulation — no lookahead bias</div>
        </div>
      </div>

      <div style={{ padding: '20px 32px', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr auto', gap: 12, borderBottom: '1px solid var(--border)' }}>
        <div>
          <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Symbol</label>
          <input
            value={symbol}
            onChange={e => setSymbol(e.target.value.toUpperCase())}
            style={{ width: '100%', background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 6, padding: '7px 10px', fontSize: '0.85rem' }}
            placeholder="RELIANCE.NS"
          />
        </div>
        <div>
          <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Strategy</label>
          <select
            value={strategy}
            onChange={e => setStrategy(e.target.value)}
            style={{ width: '100%', background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 6, padding: '7px 10px', fontSize: '0.85rem' }}
          >
            {strategies.map(s => <option key={s} value={s}>{s}</option>)}
            {!strategies.length && <option value="EMABreakout">EMABreakout</option>}
          </select>
        </div>
        <div>
          <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Start Date</label>
          <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
            style={{ width: '100%', background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 6, padding: '7px 10px', fontSize: '0.85rem' }} />
        </div>
        <div>
          <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>End Date</label>
          <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
            style={{ width: '100%', background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 6, padding: '7px 10px', fontSize: '0.85rem' }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button className="btn btn-primary" onClick={createSession} disabled={loading}>
            {loading ? '⟳' : '▶'} Load
          </button>
        </div>
      </div>

      {!state ? (
        <div className="empty-state">
          <div className="empty-icon">▶</div>
          <div className="empty-title">Configure and load a replay session</div>
          <div className="empty-sub">Select a symbol, strategy, and date range then click Load</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 0 }}>
          <div>
            <div className="chart-container" style={{ borderRadius: 0, border: 'none', borderBottom: '1px solid var(--border)' }}>
              <div className="chart-header">
                <h3>{symbol?.replace('.NS', '')} — {state.current_date}</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  Candle {state.current_index + 1} / {state.total_candles}
                </span>
              </div>
              <ReplayChart candles={state.candles?.[0]} signal={state.signal} />
            </div>

            <div className="replay-panel">
              <div className="replay-progress">
                <div className="progress-bar" onClick={e => {
                  const pct = e.nativeEvent.offsetX / e.currentTarget.clientWidth
                  const idx = Math.round(pct * state.total_candles)
                  axios.post(`/api/replay/sessions/${sessionId}/forward`, null, { params: { steps: idx - state.current_index } })
                    .then(({ data }) => setState(data))
                }}>
                  <div className="progress-fill" style={{ width: `${state.progress_pct}%` }} />
                </div>
                <div className="progress-label">{state.progress_pct}% complete — {state.current_date}</div>
              </div>
              <div className="replay-controls" style={{ marginTop: 12 }}>
                <button className="btn btn-ghost" onClick={restart} title="Restart">⏮</button>
                <button className="btn btn-ghost" onClick={() => step('backward')} title="Previous">◀</button>
                <button
                  className={`btn ${playing ? 'btn-danger' : 'btn-primary'}`}
                  onClick={togglePlay}
                  style={{ minWidth: 80, justifyContent: 'center' }}
                >
                  {playing ? '⏸ Pause' : '▶ Play'}
                </button>
                <button className="btn btn-ghost" onClick={() => step('forward')} title="Next">▶</button>
                <button className="btn btn-ghost" onClick={() => startPlay(3)} title="2x speed">2x</button>
                <button className="btn btn-ghost" onClick={() => startPlay(6)} title="5x speed">5x</button>
                {state.is_complete && (
                  <span style={{ color: 'var(--accent-green)', fontSize: '0.8rem', fontWeight: 600 }}>✓ Replay complete</span>
                )}
              </div>
            </div>
          </div>

          <div style={{ borderLeft: '1px solid var(--border)', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
            {state.signal ? (
              <div style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: 10, padding: 16 }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-green)', letterSpacing: '0.1em', marginBottom: 10 }}>
                  ● Signal Active
                </div>
                {[
                  ['Entry', `₹${state.signal.entry}`, 'var(--accent-blue-bright)'],
                  ['Stop', `₹${state.signal.stop}`, 'var(--accent-red)'],
                  ['Target', `₹${state.signal.target_1}`, 'var(--accent-green)'],
                  ['R/R', `${state.signal.risk_reward}x`, 'var(--accent-purple)'],
                  ['Confidence', `${Math.round(state.signal.confidence * 100)}%`, 'var(--text-primary)'],
                ].map(([l, v, c]) => (
                  <div key={l} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.83rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>{l}</span>
                    <span style={{ color: c, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{v}</span>
                  </div>
                ))}
                {state.signal.reasons?.slice(0, 2).map((r, i) => (
                  <div key={i} style={{ fontSize: '0.73rem', color: 'var(--text-secondary)', marginTop: 6, lineHeight: 1.4 }}>• {r}</div>
                ))}
              </div>
            ) : (
              <div style={{ background: 'rgba(255,255,255,0.02)', borderRadius: 10, padding: 16, textAlign: 'center' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No signal on this candle</div>
              </div>
            )}

            <div>
              <h4 style={{ marginBottom: 10 }}>Indicators</h4>
              {Object.entries(state.indicators || {}).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>{k.toUpperCase()}</span>
                  <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
                    {typeof v === 'number' && v > 100 ? `₹${v}` : v}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
