import { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
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
  const sections = [...new Set(NAV.map(n => n.section))]
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
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span className="status-dot" />
          API Connected
        </div>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 4 }}>
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
