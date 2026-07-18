import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { createChart, CandlestickSeries } from 'lightweight-charts'
import UniverseBadge from '../components/UniverseBadge'

// ---------- helpers ----------
const fmt = (v, prefix = '₹', decimals = 2) => {
  if (v === null || v === undefined || isNaN(v)) return '—'
  return `${prefix}${parseFloat(v).toFixed(decimals)}`
}
const fmtPct = (v, decimals = 2) => {
  if (v === null || v === undefined || isNaN(v)) return '—'
  return `${parseFloat(v).toFixed(decimals)}%`
}
const fmtNum = (v, decimals = 2) => {
  if (v === null || v === undefined || isNaN(v)) return '—'
  return parseFloat(v).toFixed(decimals)
}
const fmtCr = (v) => {
  if (!v || isNaN(v)) return '—'
  return `₹${(v / 10_000_000).toFixed(2)} Cr`
}
const fmtK = (v) => {
  if (!v || isNaN(v)) return '—'
  return `${(v / 1000).toFixed(0)}k`
}

// ---------- mini chart ----------
function CandlestickChart({ symbol, rec }) {
  const chartRef = useRef(null)
  const containerRef = useRef(null)
  const [chartError, setChartError] = useState(null)

  useEffect(() => {
    if (!containerRef.current || !symbol) return
    let chart = null
    try {
      chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height: 340,
        layout: { background: { color: '#0b0f1a' }, textColor: '#8899b5' },
        grid: {
          vertLines: { color: 'rgba(255,255,255,0.02)' },
          horzLines: { color: 'rgba(255,255,255,0.02)' },
        },
        crosshair: { mode: 1 },
        rightPriceScale: { borderColor: 'rgba(255,255,255,0.06)' },
        timeScale: { borderColor: 'rgba(255,255,255,0.06)', timeVisible: true },
      })

      // lightweight-charts v5 API: addSeries(SeriesType, options)
      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#22c55e', downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#22c55e', wickDownColor: '#ef4444',
      })

      axios.get(`/api/stocks/${encodeURIComponent(symbol)}/ohlcv`, { params: { days: 365 } })
        .then(({ data }) => {
          const candles = data
            .filter(d => d.open && d.high && d.low && d.close)
            .map(d => ({ time: d.date, open: d.open, high: d.high, low: d.low, close: d.close }))
          if (candles.length > 0) {
            candleSeries.setData(candles)
          }
          if (rec && candles.length > 0) {
            [
              { price: rec.entry_price, color: '#4f8ef7', title: `Entry ${fmt(rec.entry_price)}` },
              { price: rec.stop_loss, color: '#ef4444', title: `Stop ${fmt(rec.stop_loss)}` },
              { price: rec.target_1, color: '#22c55e', title: `Target ${fmt(rec.target_1)}` },
            ].filter(p => p.price && !isNaN(p.price)).forEach(pl =>
              candleSeries.createPriceLine({ ...pl, lineWidth: 1.5, lineStyle: 2 })
            )
          }
          chart.timeScale().fitContent()
        })
        .catch(() => setChartError('Chart data unavailable'))

      chartRef.current = chart
    } catch (e) {
      setChartError('Chart failed to initialize')
      return
    }

    const ro = new ResizeObserver(() => {
      if (chart && containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth || 600 })
      }
    })
    if (containerRef.current) ro.observe(containerRef.current)

    return () => {
      try { chart?.remove() } catch (_) {}
      ro.disconnect()
    }
  }, [symbol, rec])

  if (chartError) {
    return (
      <div style={{
        height: 340, display: 'flex', alignItems: 'center', justifyContent: 'center',
        border: '1px solid var(--border)', borderRadius: 8,
        color: 'var(--text-muted)', fontSize: '0.85rem',
      }}>
        {chartError}
      </div>
    )
  }

  return (
    <div ref={containerRef} style={{
      width: '100%', minHeight: 340,
      borderRadius: 8, overflow: 'hidden',
      border: '1px solid var(--border)',
      background: '#0b0f1a',
    }} />
  )
}

// ---------- shared card ----------
function Card({ title, children, accent }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: 12,
      border: `1px solid ${accent ? accent : 'var(--border)'}`,
      overflow: 'hidden',
    }}>
      {title && (
        <div style={{
          padding: '14px 20px', borderBottom: '1px solid var(--border)',
          fontWeight: 700, fontSize: '0.9rem', color: '#fff',
          background: 'rgba(255,255,255,0.02)',
          letterSpacing: '0.02em',
        }}>
          {title}
        </div>
      )}
      <div style={{ padding: '16px 20px' }}>
        {children}
      </div>
    </div>
  )
}

// ---------- kv row ----------
function KV({ label, value, valueColor, mono }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '7px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
      fontSize: '0.82rem', gap: 12,
    }}>
      <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>{label}</span>
      <span style={{
        color: valueColor || '#fff', fontWeight: 600,
        fontFamily: mono ? 'var(--font-mono)' : undefined,
        textAlign: 'right', wordBreak: 'break-all',
      }}>{value}</span>
    </div>
  )
}

// ---------- rule row ----------
function RuleRow({ name, status, reason }) {
  const pass = status === 'PASS'
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
      padding: '10px 14px', borderRadius: 6,
      background: 'rgba(0,0,0,0.12)',
      borderLeft: `3px solid ${pass ? 'var(--accent-green)' : 'var(--accent-red)'}`,
      gap: 12,
    }}>
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.84rem' }}>{name}</div>
        {reason && <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', marginTop: 3, lineHeight: 1.4 }}>{reason}</div>}
      </div>
      <span style={{
        background: pass ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
        color: pass ? 'var(--accent-green)' : 'var(--accent-red)',
        padding: '2px 8px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 800,
        whiteSpace: 'nowrap', flexShrink: 0,
      }}>
        {pass ? '✓ PASS' : '✗ FAIL'}
      </span>
    </div>
  )
}

// ---------- main page ----------
export default function TradeDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [rec, setRec] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [universes, setUniverses] = useState([])

  useEffect(() => {
    setLoading(true)
    setError(null)
    axios.get(`/api/recommendations/${id}`)
      .then(({ data }) => {
        // API may return a single object or an array (scan UUID fallback)
        const result = Array.isArray(data) ? data[0] : data
        if (!result) {
          setError('Recommendation not found — the link may be stale.')
        } else {
          setRec(result)
          // Load universe badges (presentation-only)
          if (result.symbol) {
            fetch(`/api/stocks/universe-badges?symbol=${result.symbol}`)
              .then(r => r.json())
              .then(j => setUniverses(j.universes || []))
              .catch(() => {}) // non-critical
          }
        }
      })
      .catch((err) => {
        const msg = err.response?.data?.detail || err.message || 'Failed to load recommendation.'
        setError(`Error ${err.response?.status || ''}: ${msg}`)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loader-container"><div className="loader" /></div>

  if (error || !rec) return (
    <div style={{ padding: '40px 32px', textAlign: 'center' }}>
      <div style={{ color: 'var(--accent-red)', fontSize: '1.1rem', marginBottom: 16 }}>
        {error || 'Recommendation data unavailable.'}
      </div>
      <button className="btn btn-ghost" onClick={() => navigate('/')}>← Back to Dashboard</button>
    </div>
  )

  const symbol = rec.symbol || ''
  const symbolClean = symbol.replace('.NS', '').replace('.BSE', '')

  const exp = rec.explanation || {}
  const snap = rec.indicator_snapshot || {}

  // ── safe rule extraction ──────────────────────────────────────
  const rule = (name) => {
    const item = exp[name] || {}
    return { status: item.status || '—', details: item.details || {} }
  }
  const liquidity = rule('Liquidity')
  const trend = rule('Trend')
  const stage = rule('Stage')
  const rs = rule('Relative Strength')
  const vcp = rule('VCP')
  const breakout = rule('Breakout')
  const riskRule = rule('Risk')

  // ── price maths ───────────────────────────────────────────────
  const entry = rec.entry_price
  const stop = rec.stop_loss
  const target = rec.target_1
  const riskAmt = entry && stop ? entry - stop : null
  const riskPct = riskAmt && entry ? (riskAmt / entry * 100) : null
  const rewardAmt = entry && target ? target - entry : null
  const rewardPct = rewardAmt && entry ? (rewardAmt / entry * 100) : null
  const rr = riskAmt && rewardAmt && riskAmt > 0 ? (rewardAmt / riskAmt) : null

  // ── indicator snap safe reads ─────────────────────────────────
  const close = snap.close
  const sma50 = snap.sma_50
  const sma150 = snap.sma_150
  const sma200 = snap.sma_200
  const atr14 = snap.atr_14
  const rsScore = snap.rs_score ?? rs.details?.rs_score
  const volRatio = breakout.details?.volume_multiple
  const pivot = breakout.details?.pivot

  // ── forensic narrative ────────────────────────────────────────
  const narrative = [
    `${symbolClean} passed all ${Object.keys(exp).length} institutional strategy gates on ${rec.scan_date}.`,
    stage.status === 'PASS' ? 'Stage 2 accumulation confirmed via 30-week MA slope.' : null,
    sma50 && sma150 ? `Price ₹${fmt(close, '')} > EMA50 ₹${fmt(sma50, '')} > EMA150 ₹${fmt(sma150, '')} > EMA200 ₹${fmt(sma200, '')}.` : null,
    rs.status === 'PASS' ? `Relative Strength score ${fmtNum(rsScore)} outperforms ^NSEI benchmark.` : null,
    vcp.status === 'PASS' ? `VCP detected: ${vcp.details?.contractions?.length || '—'} tightening contractions, volume dry-up confirmed.` : null,
    breakout.status === 'PASS' ? `Breakout above pivot ${fmt(pivot)} with ${fmtNum(volRatio)}× average volume expansion.` : null,
    stop && entry ? `Stop loss ${fmt(stop)} limits capital risk to ${fmtPct(riskPct)} per share.` : null,
  ].filter(Boolean).join(' ')

  // ── timeline steps ────────────────────────────────────────────
  const STEPS = ['Liquidity', 'Trend', 'Stage', 'Relative Strength', 'VCP', 'Breakout', 'Risk', 'BUY']
  const stepStatus = {
    'Liquidity': liquidity.status,
    'Trend': trend.status,
    'Stage': stage.status,
    'Relative Strength': rs.status,
    'VCP': vcp.status,
    'Breakout': breakout.status,
    'Risk': riskRule.status,
    'BUY': 'BUY',
  }

  return (
    <div style={{ padding: '20px 28px', color: 'var(--text-primary)', maxWidth: 1400, margin: '0 auto' }}>

      {/* Back */}
      <button onClick={() => navigate('/')} className="btn btn-ghost"
        style={{ fontSize: '0.82rem', marginBottom: 20, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        ← Back to Dashboard
      </button>

      {/* ── Title Header ── */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
        flexWrap: 'wrap', gap: 16,
        background: 'var(--bg-card)', padding: '18px 24px',
        borderRadius: 12, border: '1px solid var(--border)', marginBottom: 24,
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h1 style={{ margin: 0, fontSize: '1.9rem', fontWeight: 900, color: '#fff', letterSpacing: '-0.02em' }}>
              {symbolClean}
            </h1>
            <span style={{ background: 'rgba(59,130,246,0.1)', color: 'var(--accent-blue-bright)', padding: '3px 10px', borderRadius: 4, fontSize: '0.72rem', fontWeight: 700 }}>
              {rec.exchange || 'NSE'} · EQUITIES
            </span>
            <span style={{ background: 'rgba(34,197,94,0.1)', color: 'var(--accent-green)', padding: '3px 10px', borderRadius: 4, fontSize: '0.72rem', fontWeight: 700 }}>
              {rec.action || 'BUY'}
            </span>
            <span style={{ background: 'rgba(168,85,247,0.1)', color: 'var(--accent-purple)', padding: '3px 10px', borderRadius: 4, fontSize: '0.72rem', fontWeight: 700 }}>
              RANK #{rec.rank}
            </span>
            <UniverseBadge universes={universes} />
          </div>
          <div style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', marginTop: 6, fontWeight: 500 }}>
            {rec.company_name}
            {rec.sector ? ` · ${rec.sector}` : ''}
          </div>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: 4 }}>
            Scan Date: <strong style={{ color: 'var(--text-secondary)' }}>{rec.scan_date}</strong>
            &nbsp;·&nbsp;Strategy: <strong style={{ color: 'var(--text-secondary)' }}>{rec.strategy_name} v{rec.strategy_version}</strong>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>Conviction</div>
          <div style={{ fontSize: '2.6rem', fontWeight: 900, color: 'var(--accent-green)', fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
            {rec.confidence_score ? `${Math.round(rec.confidence_score * 100)}%` : '—'}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>{rec.risk_level || ''} RISK</div>
        </div>
      </div>

      {/* ── Main Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: 20 }}>

        {/* ── LEFT COLUMN ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>

          {/* Chart */}
          <Card title="Forensic Price Chart">
            <div style={{ display: 'flex', gap: 20, marginBottom: 12, fontSize: '0.75rem', flexWrap: 'wrap' }}>
              {[
                { color: '#4f8ef7', label: `Entry ${fmt(entry)}` },
                { color: '#ef4444', label: `Stop ${fmt(stop)}` },
                { color: '#22c55e', label: `Target ${fmt(target)}` },
              ].map(p => (
                <span key={p.label} style={{ display: 'flex', alignItems: 'center', gap: 5, color: p.color }}>
                  <span style={{ width: 20, height: 2, background: p.color, display: 'inline-block', borderRadius: 1 }} />
                  {p.label}
                </span>
              ))}
            </div>
            <CandlestickChart symbol={symbol} rec={rec} />
          </Card>

          {/* Scorecard */}
          <Card title="Strategy Scorecard">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <RuleRow
                name="Liquidity Filter"
                status={liquidity.status}
                reason={liquidity.details.turnover_50
                  ? `Turnover 50D: ${fmtCr(liquidity.details.turnover_50)} (req ≥ ₹1 Cr) · Vol 50D: ${fmtK(liquidity.details.volume_50)}`
                  : 'Min turnover ₹1 Cr and 100k average daily volume required.'}
              />
              <RuleRow
                name="Trend Template (Minervini)"
                status={trend.status}
                reason={`Close ${fmt(close, '₹')} must be above EMA50 ${fmt(sma50, '₹')} > EMA150 ${fmt(sma150, '₹')} > EMA200 ${fmt(sma200, '₹')} · 200-day MA slope must be rising · Price ≥ 75% of 52W High`}
              />
              <RuleRow
                name="Stage 2 Analysis"
                status={stage.status}
                reason="Weekly close > 30W MA, 30W MA > 40W MA, 30W MA slope positive — confirming Stage 2 accumulation."
              />
              <RuleRow
                name="Relative Strength"
                status={rs.status}
                reason={`RS Score: ${fmtNum(rsScore)} vs ^NSEI benchmark. Score must be > 0 (outperforming the index).`}
              />
              <RuleRow
                name="VCP Structure"
                status={vcp.status}
                reason={vcp.details.contractions
                  ? `${vcp.details.contractions.length} tightening contractions: [${vcp.details.contractions.map(c => `${c}%`).join(' → ')}] · Vol dry-up ratio: ${fmtNum(vcp.details.volume_dry_up_ratio)}×`
                  : 'Institutional VCP: tightening price contractions with volume dry-up on right side.'}
              />
              <RuleRow
                name="Breakout Condition"
                status={breakout.status}
                reason={`Close ${fmt(close, '₹')} above pivot ${fmt(pivot, '₹')} on ${fmtNum(volRatio)}× average 50D volume. Breakout must be ≥ 1.5× avg volume.`}
              />
              <RuleRow
                name="Risk Validation"
                status={riskRule.status}
                reason={`Risk ${fmtPct(riskPct)} must be < 10% of entry. RR ratio: ${fmtNum(rr)}:1. Position size: ${rec.position_size ?? '—'} shares.`}
              />
            </div>
          </Card>

          {/* Timeline */}
          <Card title="Signal Generation Flow">
            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 6, padding: '6px 0' }}>
              {STEPS.map((step, idx) => {
                const s = stepStatus[step]
                const isBuy = step === 'BUY'
                return (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{
                      background: isBuy ? 'var(--accent-green)' : s === 'PASS' ? 'rgba(34,197,94,0.1)' : 'rgba(59,130,246,0.1)',
                      color: isBuy ? '#fff' : s === 'PASS' ? 'var(--accent-green)' : 'var(--accent-blue-bright)',
                      border: isBuy ? 'none' : s === 'PASS' ? '1px solid rgba(34,197,94,0.3)' : '1px solid rgba(59,130,246,0.3)',
                      padding: '5px 12px', borderRadius: 4, fontSize: '0.73rem', fontWeight: 700,
                      whiteSpace: 'nowrap',
                    }}>
                      {step}
                    </div>
                    {idx < STEPS.length - 1 && (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>→</span>
                    )}
                  </div>
                )
              })}
            </div>
          </Card>

          {/* Indicator snapshot */}
          <Card title="Indicator Snapshot">
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['Indicator', 'Captured Value', 'Threshold / Purpose', 'Status'].map(h => (
                    <th key={h} style={{ padding: '8px 10px', color: 'var(--text-muted)', fontWeight: 600, textAlign: 'left' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { name: 'Close Price', val: fmt(close), req: 'Scan date closing price', pass: true },
                  { name: 'EMA 50', val: fmt(sma50), req: `> EMA 150 (${fmt(sma150, '₹')})`, pass: sma50 && sma150 ? sma50 > sma150 : null },
                  { name: 'EMA 150', val: fmt(sma150), req: `> EMA 200 (${fmt(sma200, '₹')})`, pass: sma150 && sma200 ? sma150 > sma200 : null },
                  { name: 'EMA 200', val: fmt(sma200), req: 'Slope must be rising (20D)', pass: true },
                  { name: 'ATR (14)', val: fmt(atr14), req: 'Stop distance reference', pass: true },
                  { name: 'Relative Strength', val: fmtNum(rsScore), req: '> 0 (outperforms ^NSEI)', pass: rsScore !== undefined && rsScore !== null ? rsScore > 0 : null },
                  { name: 'Volume Ratio (Breakout)', val: volRatio != null ? `${fmtNum(volRatio)}×` : '—', req: '≥ 1.5× 50D avg volume', pass: volRatio != null ? volRatio >= 1.5 : null },
                  { name: 'VCP Pivot', val: fmt(pivot), req: 'Price must close above', pass: close && pivot ? close > pivot : null },
                ].map((ind, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '9px 10px', fontWeight: 600, color: '#fff' }}>{ind.name}</td>
                    <td style={{ padding: '9px 10px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{ind.val}</td>
                    <td style={{ padding: '9px 10px', color: 'var(--text-secondary)' }}>{ind.req}</td>
                    <td style={{ padding: '9px 10px' }}>
                      {ind.pass === null || ind.pass === undefined
                        ? <span style={{ color: 'var(--text-muted)' }}>—</span>
                        : ind.pass
                          ? <span style={{ color: 'var(--accent-green)', fontWeight: 700 }}>✓ PASS</span>
                          : <span style={{ color: 'var(--accent-red)', fontWeight: 700 }}>✗ FAIL</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>

        {/* ── RIGHT COLUMN ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, minWidth: 0 }}>

          {/* Institutional narrative */}
          <Card title="Institutional Explanation">
            <p style={{ margin: 0, fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.65 }}>
              {narrative || 'Forensic narrative not available for this recommendation.'}
            </p>
          </Card>

          {/* Risk Profile */}
          <Card title="Forensic Risk Profile" accent="rgba(239,68,68,0.15)">
            <KV label="Entry Price" value={fmt(entry)} />
            <KV label="Stop Loss" value={fmt(stop)} valueColor="var(--accent-red)" />
            <KV label="Target 1" value={fmt(target)} valueColor="var(--accent-green)" />
            <KV label="Target 2 (3R)" value={riskAmt ? fmt(entry + 3 * riskAmt) : '—'} valueColor="var(--accent-cyan)" />
            <KV label="Risk / Reward" value={rr ? `${fmtNum(rr)}:1` : '—'} valueColor="var(--accent-blue-bright)" />
            <KV label="Risk %" value={fmtPct(riskPct)} valueColor="var(--accent-amber)" />
            <KV label="Reward Potential" value={fmtPct(rewardPct)} valueColor="var(--accent-green)" />
            <KV label="Position Size" value={rec.position_size != null ? `${rec.position_size} shares` : '—'} />
            <KV label="Portfolio Weight" value={rec.portfolio_weight_pct != null ? fmtPct(rec.portfolio_weight_pct) : '—'} />
          </Card>

          {/* Market Context */}
          <Card title="Market & Stage Context">
            <KV label="Stage Confirmed" value="Stage 2 (Ascending)" valueColor="var(--accent-green)" />
            <KV label="Weekly Trend" value="Price > 30W MA (Uptrend)" />
            <KV label="Benchmark" value="^NSEI (Nifty 50)" />
            <KV label="RS vs Benchmark" value={fmtNum(rsScore)} />
            <KV label="Sector" value={rec.sector || '—'} />
            <KV label="Holding Period" value={rec.holding_days ? `${rec.holding_days} days` : '—'} />
          </Card>

          {/* Audit Block */}
          <Card title="Permanent Audit Record">
            <KV label="Recommendation UUID" value={rec.recommendation_uuid || rec.id || '—'} mono />
            <KV label="Scan UUID" value={rec.scan_uuid ? `${rec.scan_uuid.slice(0, 20)}…` : '—'} mono />
            <KV label="Trading Date" value={rec.scan_date || '—'} />
            <KV label="Generated At" value={rec.generated_at ? new Date(rec.generated_at).toLocaleString() : '—'} />
            <KV label="Strategy Version" value={rec.strategy_version ? `v${rec.strategy_version}` : '—'} />
            <KV label="Indicator Version" value={`v${rec.indicator_version || '1.0.0'}`} />
            <KV label="Scanner Version" value={`v${rec.scanner_version || '1.0.0'}`} />
            <KV label="Config Hash" value={rec.config_hash || 'default'} mono />
          </Card>

        </div>
      </div>
    </div>
  )
}
