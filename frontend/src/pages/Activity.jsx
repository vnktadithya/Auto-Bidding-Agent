import { useState, useEffect } from 'react'

function Activity({ apiBase, showToast }) {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [stats, setStats] = useState({ total: 0, xCount: 0, linkedinCount: 0, todayCount: 0 })

  useEffect(() => {
    fetchNotifications()
    // Poll every 30 seconds for new activity
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchNotifications = async () => {
    try {
      const res = await fetch(`${apiBase}/notifications`)
      const data = await res.json()
      setNotifications(data.notifications || [])

      // Calculate stats
      const all = data.notifications || []
      const today = new Date().toISOString().split('T')[0]
      setStats({
        total: all.length,
        xCount: all.filter(n => n.platform === 'x').length,
        linkedinCount: all.filter(n => n.platform === 'linkedin').length,
        todayCount: all.filter(n => n.timestamp && n.timestamp.startsWith(today)).length
      })
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleTrigger = async () => {
    setTriggering(true)
    try {
      const res = await fetch(`${apiBase}/trigger`, { method: 'POST' })
      if (res.ok) {
        showToast('Bot triggered successfully!')
      } else {
        const err = await res.json()
        showToast(err.detail || 'Failed to trigger bot', 'error')
      }
    } catch (err) {
      showToast('Error triggering bot. Check your settings.', 'error')
    } finally {
      setTriggering(false)
    }
  }

  const formatTimestamp = (ts) => {
    if (!ts) return '—'
    // SQLite CURRENT_TIMESTAMP is UTC. We append ' UTC' to ensure JS treats it as such.
    const date = new Date(ts.includes('Z') || ts.includes('+') ? ts : ts + ' UTC')
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    })
  }

  const truncateUrl = (url) => {
    if (!url) return '—'
    if (url.length > 60) return url.slice(0, 60) + '...'
    return url
  }

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner" style={{ margin: '0 auto' }}></div>
        <p style={{ marginTop: '16px' }}>Loading activity log...</p>
      </div>
    )
  }

  const currentHour = new Date().getHours()
  const isBusinessHours = currentHour >= 9 && currentHour < 18

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          <div>
            <h2>📋 Activity Log</h2>
            <p>Track all automated bids posted by the bot.</p>
          </div>

          <button
            className={`btn btn-primary ${triggering ? 'loading' : ''}`}
            onClick={handleTrigger}
            disabled={triggering}
            style={{ padding: '10px 16px', fontSize: '0.9rem' }}
          >
            {triggering ? (
              <>
                <div className="spinner" style={{ width: '14px', height: '14px' }}></div>
                Triggering...
              </>
            ) : (
              <>🚀 Run Bot Now</>
            )}
          </button>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          background: isBusinessHours ? 'rgba(46, 213, 115, 0.1)' : 'rgba(255, 165, 2, 0.1)',
          border: `1px solid ${isBusinessHours ? 'rgba(46, 213, 115, 0.2)' : 'rgba(255, 165, 2, 0.2)'}`,
          borderRadius: '8px'
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isBusinessHours ? '#2ed573' : '#ffa502',
            boxShadow: `0 0 8px ${isBusinessHours ? '#2ed573' : '#ffa502'}`
          }}></div>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-color)', fontWeight: '500' }}>
            {isBusinessHours ? 'Business Hours: Active' : 'Outside Hours: Sleeping'}
          </span>
        </div>
      </div>

      {/* Stats Row */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-label">Total Bids Posted</div>
          <div className="stat-value">{stats.total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">X (Twitter)</div>
          <div className="stat-value" style={{ color: 'var(--x-color)', WebkitTextFillColor: 'var(--x-color)' }}>{stats.xCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">LinkedIn</div>
          <div className="stat-value" style={{ color: 'var(--linkedin-color)', WebkitTextFillColor: 'var(--linkedin-color)' }}>{stats.linkedinCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Today</div>
          <div className="stat-value">{stats.todayCount}</div>
        </div>
      </div>

      {/* Activity Table */}
      <div className="card">
        {notifications.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🤖</div>
            <h3>No Bids Posted Yet</h3>
            <p>When the bot posts bids, they will appear here with full details.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="activity-table">
              <thead>
                <tr>
                  <th>Platform</th>
                  <th>Post URL</th>
                  <th>Reply Posted</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {notifications.map((notif, i) => (
                  <tr key={i}>
                    <td>
                      <span className={`platform-badge ${notif.platform}`}>
                        {notif.platform === 'x' ? '𝕏' : 'in'} {notif.platform}
                      </span>
                    </td>
                    <td>
                      <a
                        href={notif.post_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="post-link"
                      >
                        {truncateUrl(notif.post_url)}
                      </a>
                    </td>
                    <td>
                      <div className="reply-text">
                        {notif.reply_text || <span style={{ color: 'var(--text-muted)' }}>No reply text logged</span>}
                      </div>
                    </td>
                    <td>
                      <span className="timestamp">{formatTimestamp(notif.timestamp)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}

export default Activity
