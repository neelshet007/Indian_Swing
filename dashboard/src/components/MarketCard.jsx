import React from 'react'

export default function MarketCard({ symbol, price, change, iv, status }) {
  const isPositive = change >= 0
  const changeFormatted = (isPositive ? '+' : '') + change.toFixed(2) + '%'
  const colorClass = isPositive ? 'text-green' : 'text-red'

  return (
    <div className="market-card">
      <div className="market-card-header">
        <span className="market-symbol">{symbol}</span>
        <span className={`market-status-badge ${status.toLowerCase()}`}>{status}</span>
      </div>
      <div className="market-price-row">
        <span className="market-price">{price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        <span className={`market-change ${colorClass}`}>{changeFormatted}</span>
      </div>
      <div className="market-details">
        <div className="market-detail-item">
          <span className="label">IV</span>
          <span className="value iv-value">{iv.toFixed(1)}%</span>
        </div>
      </div>
    </div>
  )
}
