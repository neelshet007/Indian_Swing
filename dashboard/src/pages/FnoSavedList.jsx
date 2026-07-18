import React, { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

export default function FnoSavedList() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  
  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [filterIndex, setFilterIndex] = useState('ALL')
  const [filterStrategy, setFilterStrategy] = useState('ALL')
  const [filterStatus, setFilterStatus] = useState('ALL')
  const [sortField, setSortField] = useState('timestamp') // 'timestamp' | 'quality_score'
  const [sortOrder, setSortOrder] = useState('desc') // 'asc' | 'desc'

  useEffect(() => {
    const fetchSaved = async () => {
      setLoading(true)
      try {
        const { data } = await axios.get('/api/fno/saved-recommendations')
        setItems(data)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchSaved()
  }, [])

  // Filtered & Sorted items
  const processedItems = useMemo(() => {
    let result = [...items]

    // Search query symbol, date, strategy
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(item => 
        item.symbol.toLowerCase().includes(q) ||
        item.strategy_type.toLowerCase().includes(q) ||
        item.scan_date.toLowerCase().includes(q)
      )
    }

    // Filter index
    if (filterIndex !== 'ALL') {
      result = result.filter(item => item.symbol.toUpperCase() === filterIndex.toUpperCase())
    }

    // Filter strategy
    if (filterStrategy !== 'ALL') {
      result = result.filter(item => item.strategy_type === filterStrategy)
    }

    // Filter status
    if (filterStatus !== 'ALL') {
      result = result.filter(item => item.status === filterStatus)
    }

    // Sort
    result.sort((a, b) => {
      let valA = a[sortField]
      let valB = b[sortField]
      
      if (sortField === 'timestamp') {
        valA = new Date(valA).getTime()
        valB = new Date(valB).getTime()
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1
      return 0
    })

    return result
  }, [items, searchQuery, filterIndex, filterStrategy, filterStatus, sortField, sortOrder])

  if (loading) {
    return <div className="loader-container"><div className="loader" /></div>
  }

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', color: 'var(--text-primary)' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#fff' }}>Saved Forensic Audit Records</h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Audit permanent records of strategy scans, Greeks, and EV metrics.</p>
        </div>
      </div>

      {/* Search & Filters Panel */}
      <div style={{ background: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1f2937', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
          
          {/* Search Input */}
          <div>
            <label style={{ display: 'block', fontSize: '0.66rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>Search symbol/strategy</label>
            <input 
              type="text" 
              placeholder="e.g. NIFTY, Condor..." 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{ width: '100%', padding: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid #1f2937', borderRadius: '4px', color: '#fff', fontSize: '0.74rem' }}
            />
          </div>

          {/* Index Filter */}
          <div>
            <label style={{ display: 'block', fontSize: '0.66rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>Index</label>
            <select 
              value={filterIndex}
              onChange={e => setFilterIndex(e.target.value)}
              style={{ width: '100%', padding: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid #1f2937', borderRadius: '4px', color: '#fff', fontSize: '0.74rem' }}
            >
              <option value="ALL">All Indices</option>
              <option value="NIFTY">NIFTY</option>
              <option value="BANKNIFTY">BANKNIFTY</option>
              <option value="FINNIFTY">FINNIFTY</option>
              <option value="MIDCPNIFTY">MIDCPNIFTY</option>
              <option value="SENSEX">SENSEX</option>
            </select>
          </div>

          {/* Strategy Filter */}
          <div>
            <label style={{ display: 'block', fontSize: '0.66rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>Strategy</label>
            <select 
              value={filterStrategy}
              onChange={e => setFilterStrategy(e.target.value)}
              style={{ width: '100%', padding: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid #1f2937', borderRadius: '4px', color: '#fff', fontSize: '0.74rem' }}
            >
              <option value="ALL">All Strategies</option>
              <option value="Iron Condor">Iron Condor</option>
              <option value="Iron Butterfly">Iron Butterfly</option>
              <option value="Put Credit Spread">Put Credit Spread</option>
              <option value="Call Credit Spread">Call Credit Spread</option>
              <option value="Broken Wing Butterfly">Broken Wing Butterfly</option>
              <option value="Calendar Spread">Calendar Spread</option>
              <option value="Diagonal Spread">Diagonal Spread</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label style={{ display: 'block', fontSize: '0.66rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>Status</label>
            <select 
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              style={{ width: '100%', padding: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid #1f2937', borderRadius: '4px', color: '#fff', fontSize: '0.74rem' }}
            >
              <option value="ALL">All Statuses</option>
              <option value="Pending">Pending</option>
              <option value="Paper Trade">Paper Trade</option>
              <option value="Live Trade">Live Trade</option>
              <option value="Won">Won</option>
              <option value="Lost">Lost</option>
              <option value="Cancelled">Cancelled</option>
              <option value="Expired">Expired</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <label style={{ display: 'block', fontSize: '0.66rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>Sort Field</label>
            <select 
              value={sortField}
              onChange={e => setSortField(e.target.value)}
              style={{ width: '100%', padding: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid #1f2937', borderRadius: '4px', color: '#fff', fontSize: '0.74rem' }}
            >
              <option value="timestamp">Scan Timestamp</option>
              <option value="quality_score">Quality Score</option>
            </select>
          </div>

        </div>
      </div>

      {/* Main Grid display */}
      {processedItems.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', color: 'var(--text-muted)' }}>
          No saved forensic recommendations found matching criteria.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
          {processedItems.map(item => (
            <div key={item.id} style={{ background: '#111827', border: '1px solid #1f2937', padding: '18px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: '800', color: 'var(--accent-blue-bright)' }}>{item.symbol} {item.strategy_type}</h3>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>Saved: {item.scan_date}</div>
                </div>
                <span style={{ 
                  fontSize: '0.66rem', 
                  padding: '2px 8px', 
                  borderRadius: '4px', 
                  fontWeight: '800', 
                  background: item.status === 'Won' ? 'rgba(34,197,94,0.15)' : (item.status === 'Lost' ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.08)'),
                  color: item.status === 'Won' ? 'var(--accent-green)' : (item.status === 'Lost' ? 'var(--accent-red)' : 'var(--text-secondary)')
                }}>
                  {item.status.toUpperCase()}
                </span>
              </div>

              {/* Stats Table */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.74rem', borderTop: '1px solid #1f2937', borderBottom: '1px solid #1f2937', padding: '8px 0' }}>
                <div>Expiry: <strong style={{ color: '#fff' }}>{item.expiry}</strong></div>
                <div>Quality Score: <strong style={{ color: 'var(--accent-blue-bright)' }}>{item.quality_score}/100</strong></div>
                <div>Net Credit: <strong style={{ color: 'var(--accent-green)' }}>₹ {item.net_credit.toLocaleString()}</strong></div>
                <div>Max Risk: <strong style={{ color: 'var(--accent-red)' }}>₹ {item.max_risk.toLocaleString()}</strong></div>
              </div>

              {/* User Notes Preview */}
              {item.user_notes && (
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 10px', borderRadius: '4px', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                  <strong>Notes:</strong> {item.user_notes.length > 60 ? `${item.user_notes.slice(0, 60)}...` : item.user_notes}
                </div>
              )}

              {/* Link Footer */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                <Link 
                  to={`/fno-saved/${item.id}`}
                  style={{ fontSize: '0.74rem', textDecoration: 'none', color: 'var(--accent-blue-bright)', fontWeight: '700' }}
                >
                  View Saved Forensic Report →
                </Link>
              </div>

            </div>
          ))}
        </div>
      )}

    </div>
  )
}
