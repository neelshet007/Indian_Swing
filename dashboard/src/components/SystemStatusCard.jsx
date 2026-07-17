import React from 'react'

export default function SystemStatusCard({ name, status, message }) {
  const getStatusColor = (s) => {
    switch (s?.toLowerCase()) {
      case 'green':
      case 'ok':
      case 'active':
      case 'online':
        return 'status-green'
      case 'yellow':
      case 'warning':
      case 'degarded':
        return 'status-yellow'
      case 'red':
      case 'error':
      case 'critical':
      case 'offline':
        return 'status-red'
      default:
        return 'status-muted'
    }
  }

  return (
    <div className="system-status-card">
      <div className="system-status-header">
        <span className="system-name">{name}</span>
        <div className={`status-dot-indicator ${getStatusColor(status)}`} />
      </div>
      <div className="system-status-message">{message}</div>
    </div>
  )
}
