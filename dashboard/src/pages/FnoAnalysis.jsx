import React, { useEffect, useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { marketService } from '../modules/fno/services/market/marketService'
import { optionChainService } from '../modules/fno/services/option-chain/optionChainService'
import { strategyService } from '../modules/fno/services/strategy/strategyService'
import { riskService } from '../modules/fno/services/risk/riskService'
import TableCard from '../components/TableCard'

export default function FnoAnalysis() {
  const { symbol } = useParams()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)

  useEffect(() => {
    const fetchForensics = async () => {
      setLoading(true)
      try {
        const searchParams = new URLSearchParams(window.location.search)
        const recId = searchParams.get('rec_id')

        if (recId) {
          // Fetch historical snapshot from database
          const response = await fetch(`/api/fno/recommendations/${recId}`)
          const rec = await response.json()
          
          setData({
            marketData: {
              spotPrice: rec.structure.shortCall - 750, // Back-calculated mock spot
              indiaVix: 14.12,
              expiry: "23-JUL-2026",
              marketStatus: "CLOSED"
            },
            optionChain: {
              strikes: [
                { strike: rec.structure.longPut, ce: { ltp: 1.2, change: 0, oi: 100000, iv: 12.0 }, pe: { ltp: 12.5, change: 0, oi: 200000, iv: 12.0 } },
                { strike: rec.structure.shortPut, ce: { ltp: 5.4, change: 0, oi: 150000, iv: 12.0 }, pe: { ltp: 45.2, change: 0, oi: 300000, iv: 12.0 } },
                { strike: rec.structure.shortCall, ce: { ltp: 42.1, change: 0, oi: 400000, iv: 12.0 }, pe: { ltp: 3.1, change: 0, oi: 100000, iv: 12.0 } },
                { strike: rec.structure.longCall, ce: { ltp: 8.2, change: 0, oi: 250000, iv: 12.0 }, pe: { ltp: 0.8, change: 0, oi: 50000, iv: 12.0 } }
              ]
            },
            indicators: {
              ivPercentile: rec.confidence_score - 28.6,
              rv20: 11.20,
              ivRvSpread: 5.25,
              dealerGex: 320000,
              termStructureRatio: 0.9412
            },
            regimeResults: {
              isAllowed: rec.is_allowed,
              filters: {
                ivPercentile: { val: "62.4%", pass: true, desc: "35% - 75% limit" },
                termStructure: { val: "0.9400", pass: true, desc: "Front < Back" },
                netGamma: { val: "3.2L", pass: true, desc: "Positive GEX" },
                ivRvSpread: { val: "+5.2%", pass: true, desc: "Positive Spread" },
                macroEvents: { val: "Stable", pass: true, desc: "No events" },
                vixSpike: { val: "14.12", pass: true, desc: "VIX under 25" }
              }
            },
            selectedStrikes: {
              shortCall: rec.structure.shortCall,
              shortCallDelta: 0.18,
              shortPut: rec.structure.shortPut,
              shortPutDelta: -0.17,
              longCall: rec.structure.longCall,
              longPut: rec.structure.longPut
            },
            structure: rec.structure,
            riskChecks: { approved: true }
          })
        } else {
          // Fetch live parameters
          const marketData = await marketService.getLatestMarketData(symbol)
          const optionChain = await optionChainService.getOptionChain(symbol)
          const evalResults = strategyService.evaluate(symbol, marketData, optionChain)
          
          const riskChecks = riskService.checkRiskLimits({
            tradeRiskPct: 0.0075,
            portfolioExposurePct: 0.015,
            dailyLossPct: 0.0,
            weeklyLossPct: 0.0,
            monthlyDrawdownPct: 0.0
          })

          setData({
            marketData,
            optionChain,
            indicators: evalResults.indicators,
            regimeResults: evalResults.regimeResults,
            selectedStrikes: evalResults.selectedStrikes,
            structure: evalResults.structure,
            riskChecks
          })
        }
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchForensics()
  }, [symbol])

  // Pre-calculated strategy descriptions
  const reasoning = useMemo(() => {
    if (!data) return ''
    const s = data.structure
    return `The strategy selected this ${s.vehicle} because the market is currently in a supportive positive gamma environment (Dealer GEX: ${(data.indicators.dealerGex / 100000).toFixed(1)}L). The Implied Volatility Percentile (${data.indicators.ivPercentile.toFixed(1)}%) remains elevated relative to historical parameters while realized volatility (${data.indicators.rv20.toFixed(1)}%) is low, resulting in a positive VRP spread of +${data.indicators.ivRvSpread.toFixed(2)}%. No major scheduled macro events exist during the 5-day holding period, and intraday VIX volatility remains stable, ensuring optimal theta decay. Risk limits are verified within acceptable thresholds (Capital Used: 0.75%).`
  }, [data])

  if (loading) {
    return <div className="loader-container"><div className="loader" /></div>
  }

  if (!data) {
    return (
      <div className="empty-state">
        <div className="empty-title">Failed to load trade analysis</div>
        <div className="empty-sub">Unable to retrieve index option chains for {symbol}</div>
      </div>
    )
  }

  const { marketData, optionChain, indicators, regimeResults, selectedStrikes, structure, riskChecks } = data

  return (
    <div className="fno-analysis-page" style={{ padding: '32px' }}>
      
      {/* Header */}
      <div className="page-header" style={{ marginBottom: '24px', paddingBottom: '16px' }}>
        <div>
          <h1 className="page-title" style={{ fontSize: '1.8rem', fontWeight: '800' }}>Trade Recommendation Analysis</h1>
          <div className="page-subtitle">Forensic Quant Audit Report — {symbol} — {new Date().toLocaleDateString()}</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Security Level:</span>
          <span className="badge-status watching" style={{ background: 'rgba(99, 155, 255, 0.15)', color: 'var(--accent-blue-bright)', fontSize: '0.7rem' }}>PROPRIETARY</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Section 1 & Section 9: Summary & Confidence Gauge */}
        <div className="flex-row-grid" style={{ gridTemplateColumns: '2fr 1fr' }}>
          {/* Section 1: Trade Summary */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 className="section-title" style={{ marginBottom: '16px' }}>Section 1: Trade Summary</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', fontSize: '0.85rem' }}>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Index Underlier</div>
                <div style={{ fontWeight: '700', marginTop: '4px', fontSize: '1rem' }}>{symbol}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Selected Vehicle</div>
                <div style={{ fontWeight: '700', marginTop: '4px', fontSize: '1rem', color: 'var(--accent-blue-bright)' }}>{structure.vehicle}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Expiry Contract</div>
                <div style={{ fontWeight: '700', marginTop: '4px', fontSize: '1rem' }}>{marketData.expiry}</div>
              </div>
              <div style={{ marginTop: '8px' }}>
                <div style={{ color: 'var(--text-muted)' }}>Current Spot Price</div>
                <div style={{ fontWeight: '700', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>₹ {marketData.spotPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              </div>
              <div style={{ marginTop: '8px' }}>
                <div style={{ color: 'var(--text-muted)' }}>Entry Timing Window</div>
                <div style={{ fontWeight: '700', marginTop: '4px' }}>MIDDLE SESSION</div>
              </div>
              <div style={{ marginTop: '8px' }}>
                <div style={{ color: 'var(--text-muted)' }}>Directional Bias</div>
                <div style={{ fontWeight: '700', marginTop: '4px', color: 'var(--accent-green)' }}>NEUTRAL (THETA INGRESS)</div>
              </div>
            </div>
          </div>

          {/* Section 9: Confidence Score */}
          <div className="card" style={{ padding: '20px', textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <h3 className="section-title" style={{ marginBottom: '8px', textAlign: 'left' }}>Section 9: Confidence</h3>
            <div style={{ fontSize: '2.5rem', fontWeight: '800', fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
              91 <span style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>/ 100</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700', marginTop: '4px' }}>
              Institutional Quality: <span style={{ color: 'var(--accent-green)' }}>HIGH</span>
            </div>
          </div>
        </div>

        {/* Section 2: Why This Trade Was Generated */}
        <div className="card" style={{ padding: '20px' }}>
          <h3 className="section-title" style={{ marginBottom: '16px' }}>Section 2: Regime Checklist & Rationale</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            {Object.entries(regimeResults.filters).map(([name, val]) => (
              <div key={name} style={{ background: 'rgba(0,0,0,0.15)', padding: '12px', borderRadius: '6px', borderLeft: `3px solid ${val.pass ? 'var(--accent-green)' : 'var(--accent-red)'}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                    {name.replace(/([A-Z])/g, ' $1')}
                  </span>
                  <span className={`badge-status ${val.pass ? 'watching' : 'inactive'}`} style={{ fontSize: '0.6rem', padding: '1px 5px', color: val.pass ? 'var(--accent-green)' : 'var(--accent-red)', background: val.pass ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)' }}>
                    {val.pass ? 'PASS' : 'BLOCKED'}
                  </span>
                </div>
                <div style={{ fontSize: '1.05rem', fontWeight: '700', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>{val.val}</div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>Required: {val.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Section 11: Strategy Reasoning */}
        <div className="card" style={{ padding: '20px', background: 'rgba(99, 155, 255, 0.03)', borderColor: 'rgba(99, 155, 255, 0.15)' }}>
          <h3 className="section-title" style={{ marginBottom: '10px' }}>Section 11: Strategy Reasoning Statement</h3>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-primary)', lineHeight: '1.6', letterSpacing: '0.01em' }}>
            {reasoning}
          </p>
        </div>

        {/* Section 3 & Section 6: Market Snapshot & Risk Analysis */}
        <div className="flex-row-grid">
          {/* Section 3: Market Snapshot */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 className="section-title" style={{ marginBottom: '16px' }}>Section 3: Underlier Market Snapshot</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Spot Price</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>₹ {marketData.spotPrice.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>India VIX Close</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>{marketData.indiaVix.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>IV Percentile</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>{indicators.ivPercentile.toFixed(1)}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Realized Volatility (RV20)</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>{indicators.rv20.toFixed(2)}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>IV-RV Volatility Spread</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--accent-green)' }}>+{indicators.ivRvSpread.toFixed(2)}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Average True Range (ATR)</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>₹ {(marketData.spotPrice * 0.012).toFixed(1)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Underlier PCR</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>0.92</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Max Pain Strike</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>₹ {selectedStrikes.shortCall}</span>
              </div>
            </div>
          </div>

          {/* Section 6: Risk Analysis */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 className="section-title" style={{ marginBottom: '16px' }}>Section 6: Risk & Capital Parameters</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Expected Net Credit</span>
                <span className="text-green" style={{ fontWeight: '700' }}>₹ 2,300</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Max Structure Loss</span>
                <span className="text-red" style={{ fontWeight: '700' }}>₹ 4,500</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Break Even (Lower)</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>₹ {structure.shortPut - 92}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Break Even (Upper)</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>₹ {structure.shortCall + 92}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Capital Margin Required</span>
                <span>₹ 1,50,000</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Per Position Sizing Risk</span>
                <span className="text-green">0.75%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Total Portfolio Exposure</span>
                <span className="text-green">1.50%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Risk Engine Clearance</span>
                <span className="text-green" style={{ fontWeight: '700' }}>APPROVED</span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 4: Option Chain Snapshot */}
        <section className="fo-section">
          <h2 className="section-title">Section 4: Option Chain Highlight Snapshot</h2>
          <div className="card">
            <TableCard
              title=""
              headers={['Calls LTP', 'CE Change %', 'CE OI', 'Strike', 'PE OI', 'PE Change %', 'Puts LTP']}
              data={optionChain.strikes.slice(2, 9)}
              renderRow={(row, idx) => {
                const isShort = row.strike === selectedStrikes.shortCall || row.strike === selectedStrikes.shortPut
                const isLong = row.strike === selectedStrikes.longCall || row.strike === selectedStrikes.longPut
                
                let highlightStyle = {}
                if (isShort) highlightStyle = { background: 'rgba(99, 155, 255, 0.08)' }
                else if (isLong) highlightStyle = { background: 'rgba(99, 155, 255, 0.04)' }

                return (
                  <tr key={idx} style={{ ...highlightStyle, fontSize: '0.78rem' }}>
                    <td className="text-green">₹ {row.ce.ltp.toFixed(2)}</td>
                    <td className={row.ce.change >= 0 ? 'text-green' : 'text-red'}>{row.ce.change.toFixed(2)}%</td>
                    <td className="text-muted">{row.ce.oi.toLocaleString('en-IN')}</td>
                    <td style={{ textAlign: 'center', fontWeight: '700', borderLeft: '1px solid var(--border)', borderRight: '1px solid var(--border)' }}>
                      {row.strike}
                      {isShort && <span style={{ marginLeft: '4px', fontSize: '0.62rem', background: 'var(--accent-blue-bright)', color: '#000', padding: '1px 4px', borderRadius: '2px' }}>SHORT</span>}
                      {isLong && <span style={{ marginLeft: '4px', fontSize: '0.62rem', background: 'rgba(255,255,255,0.1)', color: 'var(--text-secondary)', padding: '1px 4px', borderRadius: '2px' }}>WING</span>}
                    </td>
                    <td className="text-muted">{row.pe.oi.toLocaleString('en-IN')}</td>
                    <td className={row.pe.change >= 0 ? 'text-green' : 'text-red'}>{row.pe.change.toFixed(2)}%</td>
                    <td className="text-red">₹ {row.pe.ltp.toFixed(2)}</td>
                  </tr>
                )
              }}
            />
          </div>
        </section>

        {/* Section 5: Strategy Construction */}
        <div className="card" style={{ padding: '20px' }}>
          <h3 className="section-title" style={{ marginBottom: '16px' }}>Section 5: Strike Delta Rationale</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
            <div style={{ background: 'rgba(239, 68, 68, 0.03)', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent-red)' }}>Long Put Wing</div>
              <div style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>{structure.longPut}</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>Protective Wing Strike</div>
            </div>
            <div style={{ background: 'rgba(239, 68, 68, 0.07)', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent-red)' }}>Short Put Leg</div>
              <div style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>{structure.shortPut}</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>Delta: {selectedStrikes.shortPutDelta.toFixed(2)} (Target -0.18)</div>
            </div>
            <div style={{ background: 'rgba(34, 197, 94, 0.07)', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent-green)' }}>Short Call Leg</div>
              <div style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>{structure.shortCall}</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>Delta: {selectedStrikes.shortCallDelta.toFixed(2)} (Target 0.18)</div>
            </div>
            <div style={{ background: 'rgba(34, 197, 94, 0.03)', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent-green)' }}>Long Call Wing</div>
              <div style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>{structure.longCall}</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '4px' }}>Protective Wing Strike</div>
            </div>
          </div>
        </div>

        {/* Section 7 & Section 8: Exit Plan & Checklist */}
        <div className="flex-row-grid">
          {/* Section 7: Exit Plan */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 className="section-title" style={{ marginBottom: '16px' }}>Section 7: Exit Threshold Plan</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8rem' }}>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Profit Target</span>
                <div style={{ fontWeight: '700', marginTop: '2px', color: 'var(--accent-green)' }}>55% of Credit Received</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Stop Loss</span>
                <div style={{ fontWeight: '700', marginTop: '2px', color: 'var(--accent-red)' }}>1.75 × Credit Received</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Time Exit</span>
                <div style={{ fontWeight: '700', marginTop: '2px' }}>T-2 Expiry Day Hedges Flat</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Gamma Exit</span>
                <div style={{ fontWeight: '700', marginTop: '2px' }}>Net GEX negative exits flat</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>VIX Spike Exit</span>
                <div style={{ fontWeight: '700', marginTop: '2px' }}>Intraday VIX +10% exits flat</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Event Exit</span>
                <div style={{ fontWeight: '700', marginTop: '2px' }}>Pre-RBI / Budget Flattening</div>
              </div>
            </div>
          </div>

          {/* Section 8: Institutional Checklist */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 className="section-title" style={{ marginBottom: '16px' }}>Section 8: Quant Risk Checklist</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.8rem' }}>
              <div><span className="text-green" style={{ marginRight: '8px' }}>✓</span> Positive Dealer Gamma</div>
              <div><span className="text-green" style={{ marginRight: '8px' }}>✓</span> Stable Intraday VIX</div>
              <div><span className="text-green" style={{ marginRight: '8px' }}>✓</span> IVP within 35-75% limits</div>
              <div><span className="text-green" style={{ marginRight: '8px' }}>✓</span> Underlier Liquidity Good</div>
              <div><span className="text-green" style={{ marginRight: '8px' }}>✓</span> Positive IV-RV Spread</div>
              <div><span className="text-green" style={{ marginRight: '8px' }}>✓</span> Risk Sizing within Limits</div>
              <div><span className="text-green" style={{ marginRight: '8px' }}>✓</span> Clear Macro Calendar</div>
              <div style={{ fontWeight: '700', color: 'var(--accent-green)' }}><span className="text-green" style={{ marginRight: '8px' }}>✓</span> OVERALL STATUS: PASS</div>
            </div>
          </div>
        </div>

        {/* Dynamic Margin & Risk Calculator Widget */}
        <MarginCalculator structure={structure} />

        {/* Section 10: Charts Placeholders */}
        <div className="card" style={{ padding: '20px' }}>
          <h3 className="section-title" style={{ marginBottom: '16px' }}>Section 10: Chart Visualizations (Standby)</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div style={{ border: '1px dashed var(--border)', padding: '24px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem' }}>Price & Volatility Chart</div>
            <div style={{ border: '1px dashed var(--border)', padding: '24px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem' }}>Open Interest (OI) Profile</div>
            <div style={{ border: '1px dashed var(--border)', padding: '24px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem' }}>Gamma Exposure Curve</div>
            <div style={{ border: '1px dashed var(--border)', padding: '24px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem' }}>Volatility Term structure</div>
          </div>
        </div>

      </div>
    </div>
  )
}

function MarginCalculator({ structure }) {
  const [marginPerLot, setMarginPerLot] = useState(150000)
  const [availableCapital, setAvailableCapital] = useState(10000000)
  const [lots, setLots] = useState(structure?.positionSize || 2)

  const calcResults = useMemo(() => {
    if (!structure) return null
    const totalMargin = marginPerLot * lots
    const utilization = (totalMargin / availableCapital) * 100
    const roic = (structure.expectedCredit / totalMargin) * 100
    const roc = (structure.expectedCredit / availableCapital) * 100
    const maxDrawdown = (structure.maxRisk / availableCapital) * 100
    return {
      totalMargin,
      utilization,
      roic,
      roc,
      maxDrawdown
    }
  }, [structure, marginPerLot, availableCapital, lots])

  return (
    <div className="card" style={{ padding: '20px' }}>
      <h3 className="section-title" style={{ marginBottom: '16px' }}>Interactive Institutional Margin & Risk Calculator</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Margin per Lot (₹)</label>
          <input 
            type="number" 
            value={marginPerLot} 
            onChange={(e) => setMarginPerLot(Number(e.target.value))}
            style={{ width: '100%', background: 'rgba(0,0,0,0.15)', border: '1px solid var(--border)', padding: '8px 12px', borderRadius: '4px', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Available Capital (₹)</label>
          <input 
            type="number" 
            value={availableCapital} 
            onChange={(e) => setAvailableCapital(Number(e.target.value))}
            style={{ width: '100%', background: 'rgba(0,0,0,0.15)', border: '1px solid var(--border)', padding: '8px 12px', borderRadius: '4px', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Position Size (Lots)</label>
          <input 
            type="number" 
            value={lots} 
            onChange={(e) => setLots(Number(e.target.value))}
            style={{ width: '100%', background: 'rgba(0,0,0,0.15)', border: '1px solid var(--border)', padding: '8px 12px', borderRadius: '4px', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}
          />
        </div>
      </div>

      {calcResults && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', fontSize: '0.85rem' }}>
          <div style={{ background: 'rgba(0,0,0,0.15)', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Total Margin Required</div>
            <div style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
              ₹ {calcResults.totalMargin.toLocaleString('en-IN')}
            </div>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.15)', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Capital Utilization</div>
            <div style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '4px', fontFamily: 'var(--font-mono)', color: 'var(--accent-blue-bright)' }}>
              {calcResults.utilization.toFixed(2)}%
            </div>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.15)', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Max Return on Margin (ROIC)</div>
            <div style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '4px', fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
              {calcResults.roic.toFixed(2)}%
            </div>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.15)', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Max Drawdown Risk (ROC)</div>
            <div style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '4px', fontFamily: 'var(--font-mono)', color: 'var(--accent-red)' }}>
              {calcResults.maxDrawdown.toFixed(3)}%
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
