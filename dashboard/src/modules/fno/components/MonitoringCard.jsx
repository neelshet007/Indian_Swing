import React from 'react'
import MarketCard from '../../../components/MarketCard'
import TableCard from '../../../components/TableCard'

export default function MonitoringCard({ symbol, session }) {
  // If the session isn't initialized or running yet, show a standby card
  if (!session || session.status === 'Stopped') {
    return (
      <div className="monitoring-session-card card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '700' }}>{symbol}</h3>
          <span className="badge-status inactive">STOPPED</span>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Monitoring session is idle. Start monitoring to activate the data feed.
        </div>
      </div>
    )
  }

  const { marketData, optionChain, connectionStatus, lastUpdate, latency, status } = session

  return (
    <div className="monitoring-session-card card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Session Header Status */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '800' }}>{symbol}</h3>
          <span className="badge-status watching" style={{ background: 'rgba(34, 197, 94, 0.12)', color: 'var(--accent-green)' }}>
            {status}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '12px', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
          <div>Feed: <span style={{ color: connectionStatus === 'Connected' ? 'var(--accent-green)' : 'var(--accent-red)' }}>{connectionStatus}</span></div>
          <div>Latency: <span style={{ color: 'var(--accent-blue-bright)' }}>{latency} ms</span></div>
          <div>Updated: <span style={{ fontFamily: 'var(--font-mono)' }}>{lastUpdate}</span></div>
        </div>
      </div>

      {/* Market Cards Ticker Row */}
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

      {/* Option Chain View */}
      {optionChain && marketData && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
          <h4 style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Option Chain Strikes</h4>
          <TableCard
            title={`${symbol} Strikes — Expiry: ${marketData.expiry}`}
            headers={['Calls LTP', 'Strike', 'Puts LTP']}
            data={optionChain.strikes.slice(3, 8)} // Show 5 main ATM strikes to keep layout compact
            renderRow={(row, idx) => {
              const isAtm = Math.abs(marketData.spotPrice - row.strike) < 25
              return (
                <tr key={idx} style={{ background: isAtm ? 'rgba(99, 155, 255, 0.05)' : 'transparent', fontSize: '0.78rem' }}>
                  <td className="text-green" style={{ padding: '6px 16px' }}>₹ {row.ce.ltp.toFixed(2)}</td>
                  <td style={{ textAlign: 'center', fontWeight: '700', padding: '6px 16px' }}>{row.strike}</td>
                  <td className="text-red" style={{ padding: '6px 16px' }}>₹ {row.pe.ltp.toFixed(2)}</td>
                </tr>
              )
            }}
          />
        </div>
      )}

      {/* Placeholder Details for strategy & risk */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
        <div>
          <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '700' }}>Strategy Engine</span>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>No Strategy Loaded</div>
        </div>
        <div>
          <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '700' }}>Risk Used</span>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>₹ 0.00 (0.0%)</div>
        </div>
      </div>

    </div>
  )
}
