import React from 'react'

export default function MetricCard({ label, value, subValue, trend, status }) {
  let trendClass = ''
  if (trend === 'up') trendClass = 'text-green'
  else if (trend === 'down') trendClass = 'text-red'

  let statusClass = ''
  if (status === 'warning') statusClass = 'border-warning'
  else if (status === 'danger') statusClass = 'border-danger'

  return (
    <div className={`metric-card ${statusClass}`}>
      <span className="metric-label">{label}</span>
      <div className="metric-value-row">
        <span className="metric-value">{value}</span>
        {subValue && <span className={`metric-subvalue ${trendClass}`}>{subValue}</span>}
      </div>
    </div>
  )
}
