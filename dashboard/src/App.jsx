import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import axios from 'axios'
import Dashboard from './pages/Dashboard'
import TradeDetail from './pages/TradeDetail'
import Backtesting from './pages/Backtesting'
import ReplayPage from './pages/ReplayPage'
import Stocks from './pages/Stocks'

const NAV = [
  { to: '/', label: 'Recommendations', icon: '◈', section: 'ANALYSIS' },
  { to: '/stocks', label: 'Universe', icon: '⊞', section: 'ANALYSIS' },
  { to: '/backtesting', label: 'Backtesting', icon: '⟳', section: 'RESEARCH' },
  { to: '/replay', label: 'Replay', icon: '▶', section: 'RESEARCH' },
]

function Sidebar() {
  const [health, setHealth] = useState({ db: 'checking', error: null })
  const sections = [...new Set(NAV.map(n => n.section))]

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const { data } = await axios.get('/api/health')
        setHealth({ db: data.db, error: data.error })
      } catch (e) {
        setHealth({ db: 'disconnected', error: 'API unreachable' })
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">SwingIQ</div>
        <div className="logo-sub">Indian Equity Platform</div>
      </div>
      <nav className="sidebar-nav">
        {sections.map(section => (
          <div key={section}>
            <div className="nav-section-label">{section}</div>
            {NAV.filter(n => n.section === section).map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              >
                <span style={{ fontSize: '1rem', width: 18 }}>{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div style={{ fontSize: '0.75rem', color: health.db === 'connected' ? 'var(--accent-green)' : 'var(--accent-red)' }}>
          <span className="status-dot" style={{ background: health.db === 'connected' ? 'var(--accent-green)' : 'var(--accent-red)' }} />
          {health.db === 'connected' ? 'DB Connected' : 'DB Disconnected'}
        </div>
        {health.error && (
          <div style={{ fontSize: '0.65rem', color: 'var(--accent-red)', marginTop: 4, lineHeight: 1.3, wordBreak: 'break-word' }}>
            {health.error}
          </div>
        )}
        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 8 }}>
          v1.0.0 — Indian Equities
        </div>
      </div>
    </aside>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/recommendation/:id" element={<TradeDetail />} />
            <Route path="/stocks" element={<Stocks />} />
            <Route path="/backtesting" element={<Backtesting />} />
            <Route path="/replay" element={<ReplayPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
