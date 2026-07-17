import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import axios from 'axios'
import Dashboard from './pages/Dashboard'
import TradeDetail from './pages/TradeDetail'
import ScanAnalytics from './pages/ScanAnalytics'
import HomeDashboard from './pages/HomeDashboard'
import Settings from './pages/Settings'
import Logs from './pages/Logs'
import FnoHistory from './pages/FnoHistory'
import FnoAnalysis from './pages/FnoAnalysis'

const FOTrading = lazy(() => import('./pages/FOTrading'))

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '⊞' },
  { to: '/', label: 'Recommendation Scanner', icon: '◈' },
  { to: '/fo-trading', label: 'F&O Trading', icon: '⚡' },
  { to: '/fno-history', label: 'F&O History', icon: '📜' },
  { to: '/settings', label: 'Settings', icon: '⚙' },
  { to: '/logs', label: 'Logs', icon: '📋' },
]

function Sidebar() {
  const [health, setHealth] = useState({ db: 'checking', error: null })

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
      <nav className="sidebar-nav" style={{ marginTop: '16px' }}>
        {NAV.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span style={{ fontSize: '1.1rem', width: 22, display: 'inline-block' }}>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
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
          v1.1.0 — Multi-Asset Terminal
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
          <Suspense fallback={<div className="loader-container"><div className="loader" /></div>}>
            <Routes>
              {/* Home Dashboard */}
              <Route path="/dashboard" element={<HomeDashboard />} />
              
              {/* Legacy Scanner (Must NOT break existing routes) */}
              <Route path="/" element={<Dashboard />} />
              <Route path="/recommendation/:id" element={<TradeDetail />} />
              <Route path="/analytics" element={<ScanAnalytics />} />
              <Route path="/analytics/:uuid" element={<ScanAnalytics />} />
              
              {/* F&O Module */}
              <Route path="/fo-trading" element={<FOTrading />} />
              <Route path="/fno-analysis/:symbol" element={<FnoAnalysis />} />
              <Route path="/fno-history" element={<FnoHistory />} />
              
              {/* Settings & Logs */}
              <Route path="/settings" element={<Settings />} />
              <Route path="/logs" element={<Logs />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </BrowserRouter>
  )
}
