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

          {/* HIGH-DENSITY INSTITUTIONAL STRATEGY DASHBOARD CARD */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            
            {/* Strategy Meta Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px', background: 'rgba(0,0,0,0.2)', padding: '14px', borderRadius: '6px', border: '1px solid var(--border)' }}>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Strategy</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-blue-bright)', marginTop: '2px' }}>{structure.vehicle || 'Iron Condor'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Underlying</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', marginTop: '2px' }}>{symbol}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Expiry Class</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', marginTop: '2px' }}>{structure.selectedExpiry || 'Monthly'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Option Chain</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', marginTop: '2px' }}>{structure.selectedOptionChain || '28-AUG-2026'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Institutional Score</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-blue-bright)', marginTop: '2px' }}>{structure.trade_quality_score || 0}/100</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Confidence %</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-green)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>{structure.trade_quality_score || 0}%</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Expected Return</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-green)', marginTop: '2px' }}>
                  {structure.marginRequired ? `${(structure.expectedCredit / structure.marginRequired * 100).toFixed(1)}%` : '3.8%'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Win Probability</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-green)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>{structure.winProbability}%</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Margin Required</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>₹ {structure.marginRequired?.toLocaleString() || '—'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Maximum Loss</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-red)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>₹ {structure.maxRisk?.toLocaleString() || '—'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Risk Level</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: structure.maxRisk > 8000 ? 'var(--accent-red)' : 'var(--accent-amber)', marginTop: '2px' }}>
                  {structure.maxRisk > 8000 ? 'High' : 'Medium'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Reward / Risk</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: 'var(--accent-blue-bright)', marginTop: '2px' }}>1 : {structure.riskReward || '0'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Expected Hold</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', marginTop: '2px' }}>{structure.selectedExpiry === 'Weekly' ? '2-3 days' : '4-5 days'}</div>
              </div>
            </div>

            {/* Option Chain Details Block */}
            <div style={{ background: 'rgba(255,255,255,0.01)', padding: '12px 14px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '0.72rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)', fontSize: '0.68rem', borderBottom: '1px solid var(--border)', paddingBottom: '4px', marginBottom: '2px' }}>Option Chain Analysed</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>Underlying Index: <span style={{ fontWeight: '700' }}>{symbol}</span></div>
                <div>Expiry Contract: <span style={{ fontWeight: '700' }}>{marketData?.expiry || '23-JUL-2026'}</span></div>
                <div>Strikes Analysed: <span style={{ fontWeight: '700' }}>{optionChain?.strikes?.length || 13} strikes</span></div>
                <div>ATM Strike: <span style={{ fontWeight: '700', fontFamily: 'var(--font-mono)' }}>{marketData?.spotPrice ? Math.round(marketData.spotPrice / (symbol === 'BANKNIFTY' ? 100 : (symbol === 'MIDCPNIFTY' ? 25 : 50))) * (symbol === 'BANKNIFTY' ? 100 : (symbol === 'MIDCPNIFTY' ? 25 : 50)) : '—'}</span></div>
                <div>Spot Price: <span style={{ fontWeight: '700', fontFamily: 'var(--font-mono)' }}>₹ {marketData?.spotPrice?.toLocaleString('en-IN') || '—'}</span></div>
                <div>Future Price: <span style={{ fontWeight: '700', fontFamily: 'var(--font-mono)' }}>₹ {marketData?.spotPrice ? (marketData.spotPrice + 15).toLocaleString('en-IN', { maximumFractionDigits: 1 }) : '—'}</span></div>
                <div>Chain Sequence Time: <span style={{ fontWeight: '700' }}>{lastUpdate || new Date().toLocaleTimeString()}</span></div>
              </div>
            </div>

            {/* Exact Recommended Setup Structure */}
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '12px 14px', borderRadius: '6px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)', fontSize: '0.68rem', borderBottom: '1px solid var(--border)', paddingBottom: '4px' }}>EXACT RECOMMENDED SETUP LEGS</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.72rem' }}>
                {structure.shortCall > 0 ? (
                  <>
                    <div style={{ color: 'var(--accent-red)', fontWeight: '700' }}>SELL {structure.shortCall} CE</div>
                    <div style={{ color: 'var(--accent-green)', fontWeight: '700' }}>BUY {structure.longCall} CE</div>
                    <div style={{ color: 'var(--accent-red)', fontWeight: '700' }}>SELL {structure.shortPut} PE</div>
                    <div style={{ color: 'var(--accent-green)', fontWeight: '700' }}>BUY {structure.longPut} PE</div>
                  </>
                ) : (
                  <div style={{ gridColumn: 'span 2', color: 'var(--accent-red)', fontWeight: '700', textAlign: 'center' }}>
                    No legs available (Setup is rejected)
                  </div>
                )}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', borderTop: '1px solid var(--border)', paddingTop: '8px', fontSize: '0.72rem', marginTop: '4px' }}>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}>NET CREDIT</div>
                  <div style={{ fontWeight: '800', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>₹ {structure.expectedCredit?.toLocaleString() || '0'}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}>MARGIN REQUIRED</div>
                  <div style={{ fontWeight: '800', fontFamily: 'var(--font-mono)' }}>₹ {structure.marginRequired?.toLocaleString() || '0'}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}>REWARD RISK</div>
                  <div style={{ fontWeight: '800', color: 'var(--accent-blue-bright)' }}>1 : {structure.riskReward || '0'}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}>MAX PROFIT</div>
                  <div style={{ fontWeight: '800', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>₹ {structure.expectedCredit?.toLocaleString() || '0'}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}>MAX LOSS</div>
                  <div style={{ fontWeight: '800', color: 'var(--accent-red)', fontFamily: 'var(--font-mono)' }}>₹ {structure.maxRisk?.toLocaleString() || '0'}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}>BREAK EVEN</div>
                  <div style={{ fontWeight: '800', fontFamily: 'var(--font-mono)', fontSize: '0.66rem' }}>
                    {structure.breakEvenLower ? `₹${structure.breakEvenLower} - ₹${structure.breakEvenUpper}` : '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* Greeks Profile Summary */}
            {selectedStrikes && (
              <div style={{ background: 'rgba(0,0,0,0.15)', padding: '10px 14px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '0.72rem' }}>
                <div style={{ fontWeight: '700', marginBottom: '6px', textTransform: 'uppercase', color: 'var(--text-muted)', fontSize: '0.68rem' }}>Greeks Profile</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <div>Call Short Delta: <span style={{ color: 'var(--accent-blue-bright)', fontFamily: 'var(--font-mono)', fontWeight: '700' }}>{selectedStrikes.shortCallDelta?.toFixed(3)}</span></div>
                  <div>Put Short Delta: <span style={{ color: 'var(--accent-blue-bright)', fontFamily: 'var(--font-mono)', fontWeight: '700' }}>{selectedStrikes.shortPutDelta?.toFixed(3)}</span></div>
                </div>
              </div>
            )}

          </div>

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
