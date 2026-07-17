import React from 'react'

export default function TableCard({ title, headers, data, emptyMessage = 'No data available', renderRow }) {
  return (
    <div className="table-card">
      <div className="table-card-header">
        <h3 className="table-card-title">{title}</h3>
      </div>
      <div className="table-card-body">
        {data.length === 0 ? (
          <div className="table-empty-state">{emptyMessage}</div>
        ) : (
          <div className="table-responsive">
            <table className="terminal-table">
              <thead>
                <tr>
                  {headers.map((h, i) => (
                    <th key={i}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, index) => renderRow ? renderRow(row, index) : (
                  <tr key={index}>
                    {Object.values(row).map((val, cellIdx) => (
                      <td key={cellIdx}>{val}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
