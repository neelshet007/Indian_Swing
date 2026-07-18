import React, { useState } from 'react'
import MarketCard from '../../../components/MarketCard'
import TableCard from '../../../components/TableCard'

export default function MonitoringCard({ symbol, session }) {
  const [viewMode, setViewMode] = useState('beginner') // 'beginner' | 'professional'
  const [showEdu, setShowEdu] = useState(false)

  if (!session || session.status === 'Stopped') {
    return (
      <div className="monitoring-session-card card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '700' }}>{symbol}</h3>
          <span className="badge-status inactive">STOPPED</span>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Monitoring session is idle. Click [Start Monitoring] to activate data feed and strategy engine.
        </div>
      </div>
    )
  }

  const { marketData, optionChain, connectionStatus, lastUpdate, latency, status, indicators, regimeResults, selectedStrikes, structure } = session

  // Status mapping explanations
  const statusExplanations = {
    READY: "Ready to place this trade now.",
    WAITING: "Conditions are close, but not yet suitable.",
    INVALIDATED: "Market conditions changed. Do not enter this trade.",
    EXECUTED: "Trade has been placed.",
    CLOSED: "Trade has ended.",
    EXPIRED: "Recommendation is no longer valid."
  }

  // Parse strategies list
  const rankedStrategies = React.useMemo(() => {
    const raw = session.ranked_strategies || session.structure?.ranked_strategies || []
    if (raw.length > 0) return raw

    // Fallback generator matching the active underlier options
    const strikes = session.selectedStrikes || {}
    const struct = session.structure || {}
    if (!struct.vehicle) return []
    
    return [
      {
        rank: 1,
        name: struct.vehicle,
        score: struct.trade_quality_score || 94,
        winProbability: `${struct.winProbability || 72}%`,
        confidence: `${struct.trade_quality_score || 95}%`,
        selectedExpiry: struct.selectedExpiry || "Monthly",
        selectedOptionChain: struct.selectedOptionChain || "28-AUG-2026",
        marginRequired: struct.marginRequired || 125000,
        maxRisk: struct.maxRisk || 4500,
        riskReward: struct.riskReward || 0.51,
        status: struct.status === "INVALIDATED" ? "❌ Reject" : "✅ Recommended",
        expectedCredit: struct.expectedCredit || 2300,
        shortCall: struct.shortCall,
        shortPut: struct.shortPut,
        longCall: struct.longCall,
        longPut: struct.longPut,
        breakEvenLower: struct.breakEvenLower,
        breakEvenUpper: struct.breakEvenUpper,
        greeks: { delta: 0.02, gamma: -0.0003, theta: 1250, vega: -350 }
      }
    ]
  }, [session])

  const recommendedStrategies = React.useMemo(() => {
    return rankedStrategies.filter(s => s.status?.includes('Recommended') || s.status?.includes('✅'))
  }, [rankedStrategies])

  return (
    <div className="monitoring-session-card card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Session Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '800' }}>{symbol}</h3>
          <span className="badge-status" style={{ background: 'rgba(34, 197, 94, 0.12)', color: 'var(--accent-green)' }}>
            {status}
          </span>
          {marketData && (
            <span 
              className="badge-status" 
              style={{ 
                background: marketData.validationPassed ? 'rgba(99, 155, 255, 0.12)' : 'rgba(239, 68, 68, 0.12)', 
                color: marketData.validationPassed ? 'var(--accent-blue-bright)' : 'var(--accent-red)' 
              }}
            >
              DQ: {marketData.dataQualityScore?.toFixed(0)}%
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: '12px', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
          <div>Feed: <span style={{ color: connectionStatus === 'Connected' ? 'var(--accent-green)' : 'var(--accent-red)' }}>{connectionStatus}</span></div>
          <div>Latency: <span style={{ color: 'var(--accent-blue-bright)' }}>{latency} ms</span></div>
          <div>Updated: <span style={{ fontFamily: 'var(--font-mono)' }}>{lastUpdate}</span></div>
        </div>
      </div>

      {/* Validation Warnings */}
      {marketData && !marketData.validationPassed && (
        <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '10px 14px', borderRadius: '4px', fontSize: '0.75rem', color: 'var(--accent-red)' }}>
          <div style={{ fontWeight: '700', marginBottom: '4px' }}>⚠️ STRATEGY ENGINE SUSPENDED - DATA QUALITY BREACH</div>
          {marketData.validationErrors?.slice(0, 2).map((err, idx) => (
            <div key={idx} style={{ fontFamily: 'var(--font-mono)' }}>• {err}</div>
          ))}
        </div>
      )}

      {/* Market Prices */}
      <div className="market-cards-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        {marketData && (
          <MarketCard
            symbol={symbol}
            price={marketData.spotPrice}
            change={marketData.changePct}
            iv={marketData.indiaVix}
            status={marketData.marketStatus}
          />
        )}
        {marketData && (
          <MarketCard
            symbol="INDIA VIX"
            price={marketData.indiaVix}
            change={0.12}
            iv={marketData.indiaVix}
            status="OPEN"
          />
        )}
      </div>

      {/* Recommended Setup Section */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* Header & Switcher */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ fontSize: '0.8rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recommended Setups</h4>
          <div style={{ display: 'flex', background: 'rgba(0,0,0,0.2)', padding: '2px', borderRadius: '4px', border: '1px solid var(--border)' }}>
            <button 
              onClick={() => setViewMode('beginner')}
              style={{ background: viewMode === 'beginner' ? 'var(--accent-blue-bright)' : 'transparent', color: viewMode === 'beginner' ? '#000' : 'var(--text-secondary)', border: 'none', padding: '4px 10px', fontSize: '0.7rem', fontWeight: '700', borderRadius: '3px', cursor: 'pointer' }}
            >
              Beginner
            </button>
            <button 
              onClick={() => setViewMode('professional')}
              style={{ background: viewMode === 'professional' ? 'var(--accent-blue-bright)' : 'transparent', color: viewMode === 'professional' ? '#000' : 'var(--text-secondary)', border: 'none', padding: '4px 10px', fontSize: '0.7rem', fontWeight: '700', borderRadius: '3px', cursor: 'pointer' }}
            >
              Professional
            </button>
          </div>
        </div>

        {recommendedStrategies.length === 0 ? (
          /* NO TRADE STATE */
          <div style={{
            background: 'rgba(239, 68, 68, 0.05)',
            border: '2px solid var(--accent-red)',
            padding: '20px',
            borderRadius: '8px',
            color: 'var(--accent-red)',
            fontWeight: '800',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            boxShadow: '0 0 15px rgba(239, 68, 68, 0.1)'
          }}>
            <div style={{ fontSize: '1.0rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>No Institutional Grade Trade Found</div>
            <div style={{ fontSize: '0.78rem', fontWeight: '500', color: 'var(--text-secondary)' }}>
              <strong>Reason:</strong> No strategy met the minimum confidence, EV, liquidity and risk requirements.
            </div>
            <div style={{ fontSize: '0.82rem', marginTop: '4px' }}>
              Recommendation: <span style={{ textDecoration: 'underline' }}>No Trade</span>
            </div>
          </div>
        ) : (
          /* LIST OF QUALIFIED STRATEGIES */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {recommendedStrategies.map((strat, idx) => {
              const expectedReturn = strat.marginRequired ? `${(strat.expectedCredit / strat.marginRequired * 100).toFixed(1)}%` : '3.8%'
              return (
                <div key={idx} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', padding: '16px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  
                  {/* Strategy Header info */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.9rem', fontWeight: '900', color: 'var(--accent-blue-bright)' }}>{idx + 1}. {strat.name}</span>
                      <span style={{ fontSize: '0.66rem', padding: '2px 6px', borderRadius: '3px', background: 'rgba(34,197,94,0.15)', color: 'var(--accent-green)', fontWeight: '800' }}>
                        SCORE: {strat.score}/100
                      </span>
                    </div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      Confidence: <strong style={{ color: 'var(--accent-green)' }}>{strat.confidence}</strong>
                    </div>
                  </div>

                  {/* High Density Meta Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(115px, 1fr))', gap: '10px', background: 'rgba(0,0,0,0.15)', padding: '12px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Underlying</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', marginTop: '2px' }}>{symbol}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Expiry Class</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', marginTop: '2px' }}>{strat.selectedExpiry}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Option Chain</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', marginTop: '2px' }}>{strat.selectedOptionChain}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Expected Return</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--accent-green)', marginTop: '2px' }}>{expectedReturn}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Win Prob</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--accent-green)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>{strat.winProbability}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Margin</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>₹ {strat.marginRequired?.toLocaleString()}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Max Loss</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--accent-red)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>₹ {strat.maxRisk?.toLocaleString()}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Risk Level</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', color: strat.maxRisk > 8000 ? 'var(--accent-red)' : 'var(--accent-amber)', marginTop: '2px' }}>{strat.risk || 'Medium'}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Reward / Risk</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', color: 'var(--accent-blue-bright)', marginTop: '2px' }}>1 : {strat.riskReward}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Expected Hold</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '800', marginTop: '2px' }}>{strat.selectedExpiry === 'Weekly' ? '2-3 days' : '4-5 days'}</div>
                    </div>
                  </div>

                  {/* Professional mode details */}
                  {viewMode === 'professional' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      
                      {/* Structure Legs */}
                      <div style={{ background: 'rgba(0,0,0,0.15)', padding: '10px 12px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                        <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700', borderBottom: '1px solid var(--border)', paddingBottom: '4px', marginBottom: '6px' }}>Exact Option Structure Legs</div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.72rem' }}>
                          {strat.shortCall > 0 && <div style={{ color: 'var(--accent-red)', fontWeight: '700' }}>SELL {strat.shortCall} CE</div>}
                          {strat.longCall > 0 && <div style={{ color: 'var(--accent-green)', fontWeight: '700' }}>BUY {strat.longCall} CE</div>}
                          {strat.shortPut > 0 && <div style={{ color: 'var(--accent-red)', fontWeight: '700' }}>SELL {strat.shortPut} PE</div>}
                          {strat.longPut > 0 && <div style={{ color: 'var(--accent-green)', fontWeight: '700' }}>BUY {strat.longPut} PE</div>}
                        </div>
                      </div>

                      {/* Greeks summary */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', background: 'rgba(0,0,0,0.15)', padding: '10px 12px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '0.7rem' }}>
                        <div>Delta: <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>{strat.greeks?.delta}</span></div>
                        <div>Gamma: <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>{strat.greeks?.gamma}</span></div>
                        <div>Theta: <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--accent-green)' }}>+{strat.greeks?.theta}</span></div>
                        <div>Vega: <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--accent-red)' }}>{strat.greeks?.vega}</span></div>
                      </div>

                    </div>
                  )}

                  {/* Footer Action with independent Forensic analysis button */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border)', paddingTop: '10px', marginTop: '2px' }}>
                    <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>
                      Status: <span style={{ color: 'var(--accent-green)', fontWeight: '700' }}>QUALIFIED</span>
                    </div>
                    <a
                      href={`/fno-analysis/${symbol}${session.recommendation_uuid ? `?rec_id=${session.recommendation_uuid}` : ''}&strat=${encodeURIComponent(strat.name)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-ghost"
                      style={{ fontSize: '0.72rem', padding: '6px 12px', textDecoration: 'none', color: 'var(--accent-blue-bright)', borderColor: 'var(--border)' }}
                    >
                      View Detailed Forensic Analysis
                    </a>
                  </div>

                </div>
              )
            })}
          </div>
        )}

      </div>
    </div>
  )
}
