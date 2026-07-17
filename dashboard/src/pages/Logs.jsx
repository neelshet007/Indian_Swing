import React, { useMemo } from 'react'

export default function Logs() {
  const dummyLogs = useMemo(() => [
    { timestamp: '17:10:02.105', type: 'INFO', msg: 'System initialized on port 5173' },
    { timestamp: '17:10:04.223', type: 'INFO', msg: 'Database connection established: Connected' },
    { timestamp: '17:10:05.881', type: 'INFO', msg: 'Recommendation engine listener online' },
    { timestamp: '17:10:06.012', type: 'INFO', msg: 'F&O Sandbox feed synchronized' }
  ], [])

  return (
    <div className="logs-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">System Logs</h1>
          <div className="page-subtitle">Real-time log console for execution router and scanners</div>
        </div>
      </div>
      
      <div className="logs-container">
        <div className="console-panel">
          <div className="console-header">
            <span>stdout / stderr console</span>
            <span className="live-pill">LIVE</span>
          </div>
          <div className="console-body">
            {dummyLogs.map((log, idx) => (
              <div key={idx} className="console-line">
                <span className="line-time">[{log.timestamp}]</span>
                <span className={`line-type type-${log.type.toLowerCase()}`}>{log.type}</span>
                <span className="line-msg">{log.msg}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
