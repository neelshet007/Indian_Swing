import React from 'react'
import MarketCard from '../../../components/MarketCard'
import TableCard from '../../../components/TableCard'

export default function MonitoringCard({ symbol, session }) {
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

      {/* VRP Indicators Section */}
      {indicators && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
          <h4 style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Volatility Risk Premium (VRP) Indicators</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>IV Percentile</div>
              <div style={{ fontSize: '1rem', fontWeight: '700', fontFamily: 'var(--font-mono)', color: 'var(--accent-blue-bright)', marginTop: '2px' }}>
                {indicators.ivPercentile.toFixed(1)}%
              </div>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>IV-RV Spread</div>
              <div style={{ fontSize: '1rem', fontWeight: '700', fontFamily: 'var(--font-mono)', color: 'var(--accent-green)', marginTop: '2px' }}>
                +{indicators.ivRvSpread.toFixed(2)}%
              </div>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Net GEX</div>
              <div style={{ fontSize: '1rem', fontWeight: '700', fontFamily: 'var(--font-mono)', color: indicators.dealerGex > 0 ? 'var(--accent-green)' : 'var(--accent-red)', marginTop: '2px' }}>
                {(indicators.dealerGex / 100000).toFixed(1)}L
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Regime Filter Validation */}
      {regimeResults && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
          <div style={{ display: 'flex', justifycontent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h4 style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Regime Filter Checklist</h4>
            <span style={{ fontSize: '0.72rem', fontWeight: '700', color: regimeResults.isAllowed ? 'var(--accent-green)' : 'var(--accent-amber)' }}>
              {regimeResults.isAllowed ? 'ALL FILTERS PASS' : 'FILTER BLOCKED'}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.72rem' }}>
            {Object.entries(regimeResults.filters).map(([key, f]) => (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', background: 'rgba(255,255,255,0.02)', borderRadius: '3px', borderLeft: `2px solid ${f.pass ? 'var(--accent-green)' : 'var(--accent-amber)'}` }}>
                <span style={{ color: 'var(--text-secondary)' }}>{key.replace(/([A-Z])/g, ' $1')}</span>
                <span style={{ fontWeight: '600', color: f.pass ? 'var(--text-primary)' : 'var(--accent-amber)' }}>{f.val}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Setup Summary Section */}
      {structure && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <h4 style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Recommended Setup</h4>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.8rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Index:</span><span>{symbol}</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Strategy:</span><span>{structure.vehicle}</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Expiry:</span><span>{marketData?.expiry}</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Expected Credit:</span><span className="text-green">₹ 2,300</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Max Risk:</span><span className="text-red">₹ 4,500</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Risk Reward:</span><span>1 : 0.51</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Win Probability:</span><span className="text-green">74%</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-muted)' }}>Position Size:</span><span>2 Lots</span></div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: '700', padding: '2px 8px', borderRadius: '3px', background: (!marketData?.validationPassed) ? 'rgba(239,68,68,0.15)' : regimeResults.isAllowed ? 'rgba(34,197,94,0.15)' : 'rgba(245,158,11,0.15)', color: (!marketData?.validationPassed) ? 'var(--accent-red)' : regimeResults.isAllowed ? 'var(--accent-green)' : 'var(--accent-amber)' }}>
              {(!marketData?.validationPassed) ? 'DATA UNTRUSTED' : regimeResults.isAllowed ? 'READY TO EXECUTE' : 'REGIME BLOCK'}
            </span>
            <a
              href={`/fno-analysis/${symbol}${session.recommendation_uuid ? `?rec_id=${session.recommendation_uuid}` : ''}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost"
              style={{ fontSize: '0.72rem', padding: '4px 10px', textDecoration: 'none', color: 'var(--accent-blue-bright)', borderColor: 'var(--border)' }}
            >
              View Complete Analysis
            </a>
          </div>
        </div>
      )}

    </div>
  )
}
