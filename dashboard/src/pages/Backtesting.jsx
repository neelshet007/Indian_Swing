import { useState } from 'react'
import axios from 'axios'

const STRATEGIES = ['EMABreakout', 'RSICrossover', 'VolumeBreakout']

function MetricCard({ label, value, color, sub }) {
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, padding: '16px 20px' }}>
      <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: color || 'var(--text-primary)', margin: '4px 0 2px' }}>{value}</div>
      {sub && <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{sub}</div>}
    </div>
  )
}

export default function Backtesting() {
  const [form, setForm] = useState({
    strategy_names: ['EMABreakout'],
    symbols: 'RELIANCE.NS,TCS.NS,HDFCBANK.NS,INFY.NS,ICICIBANK.NS',
    start_date: '2020-01-01',
    end_date: new Date().toISOString().split('T')[0],
    initial_capital: 1000000,
    max_positions: 5,
    risk_per_trade_pct: 2,
    use_trailing_stop: false,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const run = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axios.post('/api/backtest/run', {
        ...form,
        symbols: form.symbols.split(',').map(s => s.trim()),
      })
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const toggleStrategy = (s) => {
    setForm(f => ({
      ...f,
      strategy_names: f.strategy_names.includes(s)
        ? f.strategy_names.filter(x => x !== s)
        : [...f.strategy_names, s]
    }))
  }

  const m = result?.metrics || {}
  const isPos = v => v > 0
  const pct = v => `${v > 0 ? '+' : ''}${v}%`

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Backtesting Engine</h1>
          <div className="page-subtitle">Portfolio-level multi-strategy backtesting with institutional metrics</div>
        </div>
      </div>

      <div style={{ padding: '24px 32px', display: 'grid', gridTemplateColumns: '300px 1fr', gap: 24 }}>
        {/* Config Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card section-pad">
            <h3 style={{ marginBottom: 14 }}>Configuration</h3>

            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Strategies</label>
              {STRATEGIES.map(s => (
                <label key={s} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <input
                    type="checkbox"
                    checked={form.strategy_names.includes(s)}
                    onChange={() => toggleStrategy(s)}
                    style={{ accentColor: 'var(--accent-blue)' }}
                  />
                  {s}
                </label>
              ))}
            </div>

            {[
              { label: 'Symbols (comma-sep)', key: 'symbols', type: 'textarea' },
              { label: 'Start Date', key: 'start_date', type: 'date' },
              { label: 'End Date', key: 'end_date', type: 'date' },
              { label: 'Initial Capital (₹)', key: 'initial_capital', type: 'number' },
              { label: 'Max Positions', key: 'max_positions', type: 'number' },
              { label: 'Risk per Trade (%)', key: 'risk_per_trade_pct', type: 'number' },
            ].map(({ label, key, type }) => (
              <div key={key} style={{ marginBottom: 10 }}>
                <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>{label}</label>
                {type === 'textarea' ? (
                  <textarea
                    value={form[key]}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                    rows={3}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 6, padding: '6px 10px', fontSize: '0.8rem', resize: 'vertical', fontFamily: 'var(--font-mono)' }}
                  />
                ) : (
                  <input
                    type={type}
                    value={form[key]}
                    onChange={e => setForm(f => ({ ...f, [key]: type === 'number' ? +e.target.value : e.target.value }))}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 6, padding: '6px 10px', fontSize: '0.83rem', fontFamily: type === 'number' ? 'var(--font-mono)' : 'var(--font-sans)' }}
                  />
                )}
              </div>
            ))}

            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.83rem', color: 'var(--text-secondary)', cursor: 'pointer', marginBottom: 16 }}>
              <input type="checkbox" checked={form.use_trailing_stop} onChange={e => setForm(f => ({ ...f, use_trailing_stop: e.target.checked }))} style={{ accentColor: 'var(--accent-blue)' }} />
              Trailing Stop Loss
            </label>

            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={run} disabled={loading}>
              {loading ? <><span className="pulse">⟳</span> Running...</> : '▶ Run Backtest'}
            </button>

            {error && <div style={{ color: 'var(--accent-red)', fontSize: '0.8rem', marginTop: 8 }}>{error}</div>}
          </div>
        </div>

        {/* Results */}
        <div>
          {!result && !loading ? (
            <div className="empty-state">
              <div className="empty-icon">📈</div>
              <div className="empty-title">Configure and run a backtest</div>
              <div className="empty-sub">Results will appear here with full institutional metrics</div>
            </div>
          ) : loading ? (
            <div className="loader-container"><div className="loader" /></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Key metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                <MetricCard label="Total Return" value={pct(m.total_return_pct)} color={isPos(m.total_return_pct) ? 'var(--accent-green)' : 'var(--accent-red)'} />
                <MetricCard label="CAGR" value={pct(m.cagr)} color={isPos(m.cagr) ? 'var(--accent-green)' : 'var(--accent-red)'} />
                <MetricCard label="Sharpe Ratio" value={m.sharpe_ratio?.toFixed(2)} color={m.sharpe_ratio > 1 ? 'var(--accent-green)' : 'var(--accent-amber)'} />
                <MetricCard label="Max Drawdown" value={`${m.max_drawdown_pct?.toFixed(2)}%`} color="var(--accent-red)" />
                <MetricCard label="Win Rate" value={`${m.win_rate?.toFixed(1)}%`} color={m.win_rate > 50 ? 'var(--accent-green)' : 'var(--accent-amber)'} />
                <MetricCard label="Total Trades" value={m.total_trades} />
                <MetricCard label="Expectancy" value={`${m.expectancy?.toFixed(2)}%`} color={isPos(m.expectancy) ? 'var(--accent-green)' : 'var(--accent-red)'} />
                <MetricCard label="Profit Factor" value={m.profit_factor === Infinity ? '∞' : m.profit_factor?.toFixed(2)} color="var(--accent-purple)" />
              </div>

              {/* Strategy breakdown */}
              {result.strategy_breakdown && Object.keys(result.strategy_breakdown).length > 0 && (
                <div className="card">
                  <div className="chart-header"><h3>Strategy Breakdown</h3></div>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Strategy</th><th>Trades</th><th>Win Rate</th><th>Avg Return</th><th>Total P&L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(result.strategy_breakdown).map(([name, stats]) => (
                        <tr key={name}>
                          <td><span className="meta-pill strategy">{name}</span></td>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>{stats.total_trades}</td>
                          <td style={{ color: stats.win_rate > 50 ? 'var(--accent-green)' : 'var(--accent-amber)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{stats.win_rate}%</td>
                          <td style={{ color: stats.avg_return_pct > 0 ? 'var(--accent-green)' : 'var(--accent-red)', fontFamily: 'var(--font-mono)' }}>{stats.avg_return_pct > 0 ? '+' : ''}{stats.avg_return_pct}%</td>
                          <td style={{ color: stats.total_pnl > 0 ? 'var(--accent-green)' : 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                            {stats.total_pnl > 0 ? '+' : ''}₹{stats.total_pnl.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Trade log */}
              {result.trades?.length > 0 && (
                <div className="card">
                  <div className="chart-header"><h3>Trade Log ({result.trade_count} trades)</h3></div>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Symbol</th><th>Strategy</th><th>Entry</th><th>Exit</th>
                          <th>P&L</th><th>Return</th><th>Days</th><th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.trades.slice(0, 100).map((t, i) => (
                          <tr key={i}>
                            <td style={{ fontWeight: 600 }}>{t.symbol?.replace('.NS', '')}</td>
                            <td><span className="meta-pill strategy" style={{ fontSize: '0.65rem' }}>{t.strategy}</span></td>
                            <td style={{ fontFamily: 'var(--font-mono)' }}>₹{t.entry_price}</td>
                            <td style={{ fontFamily: 'var(--font-mono)' }}>{t.exit_price ? `₹${t.exit_price}` : '—'}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: t.net_pnl > 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                              {t.net_pnl > 0 ? '+' : ''}₹{t.net_pnl?.toFixed(0)}
                            </td>
                            <td style={{ fontFamily: 'var(--font-mono)', color: t.return_pct > 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                              {t.return_pct > 0 ? '+' : ''}{t.return_pct?.toFixed(2)}%
                            </td>
                            <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{t.holding_days}d</td>
                            <td>
                              <span className={`badge ${t.status?.includes('TARGET') ? 'badge-strong' : t.status?.includes('STOP') ? 'badge-high' : 'badge-moderate'}`} style={{ fontSize: '0.62rem' }}>
                                {t.status?.replace('CLOSED_', '')}
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
          )}
        </div>
      </div>
    </div>
  )
}
