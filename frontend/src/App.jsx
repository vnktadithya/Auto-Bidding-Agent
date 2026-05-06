import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import Settings from './pages/Settings'
import Activity from './pages/Activity'

const API_BASE = 'http://localhost:8000'

function App() {
  const [toast, setToast] = useState(null)

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }, [])

  return (
    <Router>
      <div className="app-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-brand">
            <div className="sidebar-brand-icon">⚡</div>
            <h1>
              AutoBid
              <span>Intelligent Bidding Bot</span>
            </h1>
          </div>

          <nav className="sidebar-nav">
            <NavLink
              to="/"
              end
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">⚙️</span>
              Configuration
            </NavLink>
            <NavLink
              to="/activity"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">📋</span>
              Activity Log
            </NavLink>
          </nav>

          <div className="sidebar-footer">
            <p><span className="status-dot online"></span>FastAPI Server Online</p>
          </div>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Settings apiBase={API_BASE} showToast={showToast} />} />
            <Route path="/activity" element={<Activity apiBase={API_BASE} showToast={showToast} />} />
          </Routes>
        </main>

        {/* Toast Notification */}
        {toast && (
          <div className={`toast ${toast.type}`}>
            {toast.type === 'success' ? '✅' : '❌'} {toast.message}
          </div>
        )}
      </div>
    </Router>
  )
}

export default App
