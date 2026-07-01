import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { createChart } from 'lightweight-charts'

function CandlestickChart({ symbol, rec }) {
  const chartRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !symbol) return

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 360,
      layout: {
        background: { color: '#141b2e' },
        textColor: '#8899b5',
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.04)' },
        horzLines: { color: 'rgba(255,255,255,0.04)' },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.08)' },
      timeScale: { borderColor: 'rgba(255,255,255,0.08)', timeVisible: true },
    })

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    axios.get(`/api/stocks/${symbol}/ohlcv`, { params: { days: 365 } })
      .then(({ data }) => {
        const candles = data.map(d => ({
          time: d.date,
          open: d.open, high: d.high, low: d.low, close: d.close,
        }))
        candleSeries.setData(candles)

        // Entry/stop/target markers
        if (rec && data.length > 0) {
          const lastDate = data[data.length - 1].date
          const priceLines = [
            { price: rec.entry_price, color: '#4f8ef7', lineWidth: 1, lineStyle: 2, title: `Entry ₹${rec.entry_price}` },
            { price: rec.stop_loss, color: '#ef4444', lineWidth: 1, lineStyle: 2, title: `Stop ₹${rec.stop_loss}` },
            { price: rec.target_1, color: '#22c55e', lineWidth: 1, lineStyle: 2, title: `T1 ₹${rec.target_1}` },
          ]
          priceLines.forEach(pl => candleSeries.createPriceLine(pl))
        }

        chart.timeScale().fitContent()
      })

    chartRef.current = chart
    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: containerRef.current?.clientWidth || 600 })
    })
    ro.observe(containerRef.current)

    return () => { chart.remove(); ro.disconnect() }
  }, [symbol, rec])

  return <div ref={containerRef} style={{ width: '100%', minHeight: 360 }} />
}

function RiskMeter({ risk }) {
  const cls = risk === 'LOW' ? 'low' : risk === 'MEDIUM' ? 'medium' : 'high'
  return (
    <div>
      <div className="info-label">Risk Level</div>
      <div className={`badge badge-${cls}`} style={{ marginTop: 4 }}>{risk}</div>
      <div className="risk-meter" style={{ marginTop: 8 }}>
        <div className={`risk-meter-fill risk-${cls}`} />
      </div>
    </div>
  )
}

export default function TradeDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [rec, setRec] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`/api/recommendations/${id}`)
      .then(({ data }) => setRec(data))
      .catch(() => navigate('/'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loader-container"><div className="loader" /></div>
  if (!rec) return null

  const symbol = rec.symbol
  const riskPct = rec.entry_price && rec.stop_loss
    ? ((rec.entry_price - rec.stop_loss) / rec.entry_price * 100).toFixed(2)
    : '—'

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn btn-ghost" style={{ marginBottom: 8, fontSize: '0.8rem' }} onClick={() => navigate('/')}>
            ← Back to Dashboard
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 className="page-title">{symbol?.replace('.NS', '')}</h1>
            <span className={`badge badge-${rec.direction?.toLowerCase()}`}>{rec.direction}</span>
            <span className={`badge badge-${rec.quality?.toLowerCase()}`}>{rec.quality}</span>
          </div>
          <div className="page-subtitle">{rec.company_name} — {rec.strategy_name}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Confidence</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: rec.confidence_score >= 0.75 ? 'var(--accent-green)' : rec.confidence_score >= 0.55 ? 'var(--accent-blue)' : 'var(--accent-amber)', fontFamily: 'var(--font-mono)' }}>
            {Math.round(rec.confidence_score * 100)}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Signal rank #{rec.rank}</div>
        </div>
      </div>

      <div className="detail-layout">
        <div className="detail-main">
          {/* Chart */}
          <div className="chart-container">
            <div className="chart-header">
              <h3>Price Chart — {symbol?.replace('.NS', '')}</h3>
              <div style={{ display: 'flex', gap: 16, fontSize: '0.75rem' }}>
                <span style={{ color: 'var(--accent-blue)' }}>— Entry</span>
                <span style={{ color: 'var(--accent-red)' }}>— Stop</span>
                <span style={{ color: 'var(--accent-green)' }}>— Target</span>
              </div>
            </div>
            <CandlestickChart symbol={symbol} rec={rec} />
          </div>

          {/* Trade Setup */}
          <div className="card section-pad">
            <h3 style={{ marginBottom: 16 }}>Trade Setup</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              {[
                { label: 'Entry Price', value: `₹${rec.entry_price?.toFixed(2)}`, color: 'var(--accent-blue-bright)' },
                { label: 'Stop Loss', value: `₹${rec.stop_loss?.toFixed(2)}`, color: 'var(--accent-red)' },
                { label: 'Target 1', value: `₹${rec.target_1?.toFixed(2)}`, color: 'var(--accent-green)' },
                { label: 'Target 2', value: rec.target_2 ? `₹${rec.target_2?.toFixed(2)}` : '—', color: 'var(--accent-cyan)' },
                { label: 'Risk/Reward', value: `${rec.risk_reward?.toFixed(2)}x`, color: 'var(--accent-purple)' },
                { label: 'Risk %', value: `${riskPct}%`, color: 'var(--accent-amber)' },
                { label: 'Hold Period', value: `${rec.holding_days} days`, color: 'var(--text-primary)' },
                { label: 'Scan Date', value: rec.scan_date, color: 'var(--text-secondary)' },
              ].map((item, i) => (
                <div key={i} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '12px 14px' }}>
                  <div className="info-label">{item.label}</div>
                  <div className="info-value" style={{ color: item.color }}>{item.value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Why this trade */}
          <div className="card section-pad">
            <h3 style={{ marginBottom: 14 }}>Why This Trade?</h3>
            {rec.reasons?.map((r, i) => (
              <div key={i} style={{
                display: 'flex', gap: 10, padding: '10px 0',
                borderBottom: i < rec.reasons.length - 1 ? '1px solid var(--border)' : 'none',
                fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5,
              }}>
                <span style={{ color: 'var(--accent-green)', fontWeight: 700, fontSize: '0.7rem', marginTop: 3 }}>✓</span>
                <span>{r}</span>
              </div>
            ))}
            {!rec.reasons?.length && (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No reasons available.</div>
            )}
          </div>

          {/* Historical Context */}
          {rec.historical_win_rate && (
            <div className="card section-pad">
              <h3 style={{ marginBottom: 14 }}>Historical Performance</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: 8, padding: 16 }}>
                  <div className="info-label">Win Rate (Similar Setups)</div>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-green)', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                    {(rec.historical_win_rate * 100).toFixed(0)}%
                  </div>
                </div>
                <div style={{ background: 'rgba(79,142,247,0.08)', border: '1px solid rgba(79,142,247,0.15)', borderRadius: 8, padding: 16 }}>
                  <div className="info-label">Historical Occurrences</div>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-blue-bright)', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                    {rec.historical_occurrences || '—'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="detail-sidebar">
          <div className="card section-pad">
            <h3 style={{ marginBottom: 14 }}>Risk Analysis</h3>
            <RiskMeter risk={rec.risk_level} />
            <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
              {rec.metadata && Object.entries({
                ATR: rec.metadata.atr ? `₹${rec.metadata.atr}` : null,
                RSI: rec.metadata.rsi ? `${rec.metadata.rsi}` : null,
                'EMA 50': rec.metadata.ema50 ? `₹${rec.metadata.ema50}` : null,
                'EMA 200': rec.metadata.ema200 ? `₹${rec.metadata.ema200}` : null,
                'Vol Ratio': rec.metadata.volume_ratio ? `${rec.metadata.volume_ratio}x avg` : null,
              }).filter(([, v]) => v).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.83rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                  <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card section-pad">
            <h3 style={{ marginBottom: 14 }}>Position Calculator</h3>
            <PositionCalc entry={rec.entry_price} stop={rec.stop_loss} />
          </div>

          <div className="card section-pad" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 10 }}>
              Replay this setup candle by candle
            </div>
            <button
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => {
                const sym = symbol?.replace('.NS', '')
                window.location.href = `/replay?symbol=${symbol}&strategy=${rec.strategy_name}`
              }}
            >
              ▶ Open Replay
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function PositionCalc({ entry, stop }) {
  const [capital, setCapital] = useState(100000)
  const [risk, setRisk] = useState(2)

  const riskAmt = capital * (risk / 100)
  const riskPerShare = entry && stop ? Math.abs(entry - stop) : 1
  const qty = Math.max(1, Math.floor(riskAmt / riskPerShare))
  const totalCost = qty * (entry || 0)

  return (
    <div>
      <div style={{ marginBottom: 10 }}>
        <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Capital (₹)</label>
        <input
          type="number"
          value={capital}
          onChange={e => setCapital(+e.target.value)}
          style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 6, padding: '6px 10px', fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}
        />
      </div>
      <div style={{ marginBottom: 12 }}>
        <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Risk per trade (%)</label>
        <input
          type="range" min={0.5} max={5} step={0.5}
          value={risk}
          onChange={e => setRisk(+e.target.value)}
          style={{ width: '100%' }}
        />
        <div style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', textAlign: 'right' }}>{risk}%</div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {[
          ['Risk Amount', `₹${riskAmt.toFixed(0)}`],
          ['Quantity', `${qty} shares`],
          ['Total Capital', `₹${totalCost.toFixed(0)}`],
        ].map(([l, v]) => (
          <div key={l} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.83rem', padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--text-muted)' }}>{l}</span>
            <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{v}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
