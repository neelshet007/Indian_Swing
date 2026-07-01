import { useState, useEffect } from 'react'
import axios from 'axios'

export default function Stocks() {
  const [stocks, setStocks] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sector, setSector] = useState('')

  useEffect(() => {
    setLoading(true)
    axios.get('/api/stocks/', { params: { limit: 500 } })
      .then(({ data }) => setStocks(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const sectors = [...new Set(stocks.map(s => s.sector).filter(Boolean))].sort()
  const filtered = stocks.filter(s => {
    const q = search.toLowerCase()
    const matchSearch = !q || s.symbol?.toLowerCase().includes(q) || s.name?.toLowerCase().includes(q)
    const matchSector = !sector || s.sector === sector
    return matchSearch && matchSector
  })

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Stock Universe</h1>
          <div className="page-subtitle">{stocks.length} stocks loaded — {stocks.filter(s => s.is_active).length} active</div>
        </div>
      </div>

      <div style={{ padding: '16px 32px', display: 'flex', gap: 12 }}>
        <input
          placeholder="Search symbol or company..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ flex: 1, background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 8, padding: '8px 14px', fontSize: '0.85rem' }}
        />
        <select
          value={sector}
          onChange={e => setSector(e.target.value)}
          style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 8, padding: '8px 14px', fontSize: '0.85rem' }}
        >
          <option value="">All Sectors</option>
          {sectors.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="loader-container"><div className="loader" /></div>
      ) : (
        <div style={{ padding: '0 32px 32px' }}>
          <div className="card">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th><th>Company Name</th><th>Sector</th><th>Industry</th><th>Cap</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 200).map((s, i) => (
                  <tr key={s.id || i}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-blue-bright)' }}>
                      {s.symbol?.replace('.NS', '')}
                    </td>
                    <td style={{ color: 'var(--text-primary)' }}>{s.name}</td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{s.sector || '—'}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{s.industry || '—'}</td>
                    <td>
                      {s.market_cap_category && (
                        <span className={`badge ${s.market_cap_category === 'large' ? 'badge-strong' : s.market_cap_category === 'mid' ? 'badge-moderate' : 'badge-weak'}`}>
                          {s.market_cap_category}
                        </span>
                      )}
                    </td>
                    <td>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.78rem' }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.is_active ? 'var(--accent-green)' : 'var(--text-muted)', display: 'inline-block' }} />
                        <span style={{ color: 'var(--text-muted)' }}>{s.is_active ? 'Active' : 'Inactive'}</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="empty-state">
                <div className="empty-title">No stocks match your search</div>
              </div>
            )}
            {filtered.length > 200 && (
              <div style={{ padding: '12px 16px', fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                Showing 200 of {filtered.length} results. Refine your search to see more.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
