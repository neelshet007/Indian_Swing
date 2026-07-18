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
      {structure && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Header & Switcher */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recommended Setup</h4>
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

          {/* Rejection Alert Banner */}
          {(structure.decision === 'REJECT' || structure.verdict?.includes('REJECT')) && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.12)',
              border: '2px solid var(--accent-red)',
              padding: '16px',
              borderRadius: '8px',
              color: 'var(--accent-red)',
              fontWeight: '800',
              textAlign: 'center',
              fontSize: '1rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 15px rgba(239, 68, 68, 0.15)'
            }}>
              <span style={{ fontSize: '1.6rem' }}>🚨</span>
              <div style={{ letterSpacing: '0.05em' }}>THIS TRADE IS TO BE REJECTED - DO NOT PLACE ORDER</div>
              <div style={{ fontSize: '0.75rem', fontWeight: '500', color: 'var(--text-secondary)' }}>
                This strategy setup does not meet safety or economic clearance criteria. Reject directly.
              </div>
            </div>
          )}

          {/* Trade Quality Score Widget */}
          <div style={{ background: 'rgba(0,0,0,0.15)', padding: '14px', borderRadius: '6px', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Trade Quality Score</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: '800', fontFamily: 'var(--font-mono)' }}>
                  {structure.trade_quality_score || 0}/100
                </span>
                <span style={{ color: 'var(--accent-amber)', fontSize: '0.95rem' }}>
                  {structure.stars || '★☆☆☆☆'}
                </span>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Proprietary Verdict</div>
              <div style={{ fontSize: '1rem', fontWeight: '800', color: (structure.trade_quality_score || 0) >= 60 ? 'var(--accent-green)' : 'var(--accent-red)', marginTop: '4px' }}>
                {structure.verdict || 'No Trade Today'}
              </div>
            </div>
          </div>

          {/* BEGINNER MODE */}
          {viewMode === 'beginner' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              
              {/* Executive Summary */}
              <div style={{ background: 'rgba(99, 155, 255, 0.04)', padding: '12px 14px', borderRadius: '6px', border: '1px solid rgba(99,155,255,0.1)', fontSize: '0.78rem', lineHeight: '1.4' }}>
                <div style={{ fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>Executive Decision Summary</div>
                <div style={{ color: 'var(--text-secondary)' }}>{structure.executive_summary}</div>
                {(structure.trade_quality_score || 0) < 60 && (
                  <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px dashed var(--border)', color: 'var(--accent-amber)' }}>
                    💡 <strong>Suggested alternative:</strong> {structure.alternative_strategy}
                  </div>
                )}
              </div>

              {/* Visual Order Sequence Flow */}
              {structure.shortCall > 0 && (
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: '700' }}>VISUAL ORDER FLOW SEQUENCE</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
                    <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '8px', borderRadius: '4px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.62rem', color: 'var(--accent-red)', fontWeight: '800' }}>1. SELL (CE)</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: '700', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{structure.shortCall}</div>
                    </div>
                    <div style={{ background: 'rgba(34, 197, 94, 0.08)', border: '1px solid rgba(34, 197, 94, 0.2)', padding: '8px', borderRadius: '4px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.62rem', color: 'var(--accent-green)', fontWeight: '800' }}>2. BUY (CE)</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: '700', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{structure.longCall}</div>
                    </div>
                    <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '8px', borderRadius: '4px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.62rem', color: 'var(--accent-red)', fontWeight: '800' }}>3. SELL (PE)</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: '700', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{structure.shortPut}</div>
                    </div>
                    <div style={{ background: 'rgba(34, 197, 94, 0.08)', border: '1px solid rgba(34, 197, 94, 0.2)', padding: '8px', borderRadius: '4px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.62rem', color: 'var(--accent-green)', fontWeight: '800' }}>4. BUY (PE)</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: '700', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{structure.longPut}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Pros & Cons list */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.72rem' }}>
                <div style={{ background: 'rgba(34,197,94,0.03)', padding: '10px', borderRadius: '4px', border: '1px solid rgba(34,197,94,0.1)' }}>
                  <div style={{ fontWeight: '700', color: 'var(--accent-green)', marginBottom: '6px' }}>✓ ADVANTAGES</div>
                  {structure.pros?.map((p, i) => <div key={i} style={{ color: 'var(--text-secondary)', marginBottom: '3px' }}>• {p}</div>)}
                  {(!structure.pros || structure.pros.length === 0) && <div style={{ color: 'var(--text-muted)' }}>None identified.</div>}
                </div>
                <div style={{ background: 'rgba(239,68,68,0.03)', padding: '10px', borderRadius: '4px', border: '1px solid rgba(239,68,68,0.1)' }}>
                  <div style={{ fontWeight: '700', color: 'var(--accent-red)', marginBottom: '6px' }}>✗ DISADVANTAGES</div>
                  {structure.cons?.map((c, i) => <div key={i} style={{ color: 'var(--text-secondary)', marginBottom: '3px' }}>• {c}</div>)}
                  {(!structure.cons || structure.cons.length === 0) && <div style={{ color: 'var(--text-muted)' }}>None identified.</div>}
                </div>
              </div>

              {/* Order Summary & Risks */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', background: 'rgba(255,255,255,0.01)', padding: '14px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                <div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>MAXIMUM RISK</div>
                  <div className="text-red" style={{ fontSize: '1.15rem', fontWeight: '800', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                    ₹ {structure.maxRisk.toLocaleString()}
                  </div>
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '2px' }}>Worst case loss if market breaks margins</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>MAXIMUM PROFIT</div>
                  <div className="text-green" style={{ fontSize: '1.15rem', fontWeight: '800', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                    ₹ {structure.expectedCredit.toLocaleString()}
                  </div>
                  <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '2px' }}>Premium received at entry</div>
                </div>
                <div style={{ borderTop: '1px solid var(--border)', paddingTop: '8px', marginTop: '4px' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>MARGIN REQUIRED</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: '700', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                    ₹ {structure.marginRequired?.toLocaleString() || '0'}
                  </div>
                </div>
                <div style={{ borderTop: '1px solid var(--border)', paddingTop: '8px', marginTop: '4px' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>CAPITAL REQUIRED</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: '700', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                    ₹ {structure.capitalRequired?.toLocaleString() || '0'}
                  </div>
                </div>
              </div>

              {/* Entry & Exit Guidelines */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.72rem' }}>
                <div style={{ background: 'rgba(34,197,94,0.03)', padding: '10px', borderRadius: '4px', border: '1px solid rgba(34,197,94,0.1)' }}>
                  <div style={{ fontWeight: '700', color: 'var(--accent-green)', marginBottom: '4px' }}>✓ WHEN TO ENTER</div>
                  <div style={{ color: 'var(--text-secondary)' }}>• Status shows READY</div>
                  <div style={{ color: 'var(--text-secondary)' }}>• Price stays near recommendation</div>
                </div>
                <div style={{ background: 'rgba(239,68,68,0.03)', padding: '10px', borderRadius: '4px', border: '1px solid rgba(239,68,68,0.1)' }}>
                  <div style={{ fontWeight: '700', color: 'var(--accent-red)', marginBottom: '4px' }}>⚠ WHEN TO EXIT</div>
                  <div style={{ color: 'var(--text-secondary)' }}>• Hit 55% profit target</div>
                  <div style={{ color: 'var(--text-secondary)' }}>• Reach stop loss limit</div>
                </div>
              </div>

              {/* Educational Mode */}
              <div>
                <button 
                  onClick={() => setShowEdu(!showEdu)} 
                  className="btn btn-ghost" 
                  style={{ width: '100%', fontSize: '0.75rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px' }}
                >
                  💡 {showEdu ? 'Hide Explanation' : 'Why am I doing this? (Explain in Simple Terms)'}
                </button>
                {showEdu && (
                  <div style={{ background: 'rgba(0,0,0,0.15)', padding: '14px', borderRadius: '6px', marginTop: '8px', fontSize: '0.76rem', display: 'flex', flexDirection: 'column', gap: '10px', border: '1px solid var(--border)' }}>
                    <div>
                      <strong>Why Sell options?</strong> We sell option premiums far away from the current spot to collect decay (theta decay) as time passes, acting like an insurance writer.
                    </div>
                    <div>
                      <strong>Why Buy wings?</strong> We buy cheaper, further-out options to cap our maximum loss, protecting our capital from sharp, unexpected overnight market runs.
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', borderTop: '1px solid var(--border)', paddingTop: '8px', marginTop: '4px' }}>
                      <div>
                        <span className="text-green">📈 Market Rises</span>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Profits as long as it stays under {structure.shortCall}. Capped risk above it.</div>
                      </div>
                      <div>
                        <span className="text-red">📉 Market Falls</span>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Profits as long as it stays above {structure.shortPut}. Capped risk below it.</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

            </div>
          )}

          {/* PROFESSIONAL MODE */}
          {viewMode === 'professional' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Index Symbol:</span><span>{symbol}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Vehicle Structure:</span><span>{structure.vehicle}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Expiry target:</span><span>{marketData?.expiry}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Expected Credit:</span><span className="text-green">₹ {structure.expectedCredit.toLocaleString()}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Max Risk/Loss:</span><span className="text-red">₹ {structure.maxRisk.toLocaleString()}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Risk Reward:</span><span>1 : {structure.riskReward}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Win Probability:</span><span className="text-green">{structure.winProbability}%</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Position Size:</span><span>{structure.positionSize} Lots</span></div>
              </div>

              {/* Greeks Summary */}
              {selectedStrikes && (
                <div style={{ background: 'rgba(0,0,0,0.15)', padding: '10px', borderRadius: '4px', fontSize: '0.72rem' }}>
                  <div style={{ fontWeight: '700', marginBottom: '6px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Greeks Profile</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div>Call Short Delta: <span style={{ color: 'var(--accent-blue-bright)', fontFamily: 'var(--font-mono)' }}>{selectedStrikes.shortCallDelta?.toFixed(3)}</span></div>
                    <div>Put Short Delta: <span style={{ color: 'var(--accent-blue-bright)', fontFamily: 'var(--font-mono)' }}>{selectedStrikes.shortPutDelta?.toFixed(3)}</span></div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Live Option Chain Highlight Panel */}
          {optionChain?.strikes && (
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '12px 16px', borderRadius: '6px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: '700', textTransform: 'uppercase' }}>
                Option Chain & Strategy Selection
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', fontSize: '0.72rem', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '4px' }}>CE LTP</th>
                      <th style={{ padding: '4px', textAlign: 'center' }}>Strike</th>
                      <th style={{ padding: '4px', textAlign: 'right' }}>PE LTP</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const middleIdx = Math.floor(optionChain.strikes.length / 2)
                      const slice = optionChain.strikes.slice(Math.max(0, middleIdx - 3), Math.min(optionChain.strikes.length, middleIdx + 4))
                      return slice.map((row, idx) => {
                        const isShortCall = row.strike === selectedStrikes?.shortCall
                        const isShortPut = row.strike === selectedStrikes?.shortPut
                        const isLongCall = row.strike === selectedStrikes?.longCall
                        const isLongPut = row.strike === selectedStrikes?.longPut
                        
                        let highlightStyle = {}
                        if (isShortCall || isShortPut) {
                          highlightStyle = { background: 'rgba(99, 155, 255, 0.15)', fontWeight: '700' }
                        } else if (isLongCall || isLongPut) {
                          highlightStyle = { background: 'rgba(255, 255, 255, 0.05)' }
                        }

                        return (
                          <tr key={idx} style={{ ...highlightStyle, borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                            <td style={{ padding: '5px 4px', color: 'var(--accent-green)' }}>
                              ₹ {row.ce?.ltp?.toFixed(1) || '—'}
                              {isShortCall && <span style={{ marginLeft: '4px', fontSize: '0.55rem', background: 'var(--accent-blue-bright)', color: '#000', padding: '1px 3px', borderRadius: '2px', fontWeight: 'bold' }}>SELL</span>}
                              {isLongCall && <span style={{ marginLeft: '4px', fontSize: '0.55rem', background: 'rgba(255,255,255,0.1)', color: 'var(--text-secondary)', padding: '1px 3px', borderRadius: '2px' }}>BUY</span>}
                            </td>
                            <td style={{ padding: '5px 4px', textAlign: 'center', fontWeight: '700', borderLeft: '1px solid var(--border)', borderRight: '1px solid var(--border)' }}>
                              {row.strike}
                            </td>
                            <td style={{ padding: '5px 4px', textAlign: 'right', color: 'var(--accent-red)' }}>
                              {isLongPut && <span style={{ marginRight: '4px', fontSize: '0.55rem', background: 'rgba(255,255,255,0.1)', color: 'var(--text-secondary)', padding: '1px 3px', borderRadius: '2px' }}>BUY</span>}
                              {isShortPut && <span style={{ marginRight: '4px', fontSize: '0.55rem', background: 'var(--accent-blue-bright)', color: '#000', padding: '1px 3px', borderRadius: '2px', fontWeight: 'bold' }}>SELL</span>}
                              ₹ {row.pe?.ltp?.toFixed(1) || '—'}
                            </td>
                          </tr>
                        )
                      })
                    })()}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Validation Checklist Panel */}
          <div style={{ background: 'rgba(0,0,0,0.15)', padding: '12px 16px', borderRadius: '6px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: '700', textTransform: 'uppercase' }}>Trade Quality Confirmation Checklist</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.72rem' }}>
              <div><span className="text-green">✓</span> Correct Expiry Target</div>
              <div><span className="text-green">✓</span> Correct Lot Size (2)</div>
              <div><span className="text-green">✓</span> Margin Available</div>
              <div style={{ color: marketData?.validationPassed ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                <span>{marketData?.validationPassed ? '✓' : '✗'}</span> Recommendation {marketData?.validationPassed ? 'Valid' : 'Invalid'}
              </div>
            </div>
          </div>

          {/* Action Footer */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border)', paddingTop: '14px', marginTop: '4px' }}>
            <div>
              <span style={{ fontSize: '0.72rem', fontWeight: '800', padding: '3px 8px', borderRadius: '3px', background: (structure.trade_quality_score || 0) < 60 ? 'rgba(239,68,68,0.15)' : 'rgba(34,197,94,0.15)', color: (structure.trade_quality_score || 0) < 60 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                {structure.decision || 'REJECT'}
              </span>
              <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {statusExplanations[structure.status || 'READY']}
              </div>
            </div>
            <a
              href={`/fno-analysis/${symbol}${session.recommendation_uuid ? `?rec_id=${session.recommendation_uuid}` : ''}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost"
              style={{ fontSize: '0.72rem', padding: '6px 12px', textDecoration: 'none', color: 'var(--accent-blue-bright)', borderColor: 'var(--border)' }}
            >
              View Complete Analysis
            </a>
          </div>

        </div>
      )}

    </div>
  )
}
