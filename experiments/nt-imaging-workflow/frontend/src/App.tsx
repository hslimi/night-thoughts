import { useCallback, useEffect, useState } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { api, logout } from './api'
import Login from './components/Login'
import Worklist from './components/Worklist'
import RunDetail from './components/RunDetail'
import MobileNav from './components/MobileNav'
import DebugCenter from './components/DebugCenter'

export default function App() {
  const [username, setUsername] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [sessionExpired, setSessionExpired] = useState(false)
  const navigate = useNavigate()
  const check = useCallback(async () => {
    try {
      const me = await api<{ username: string }>('/auth/me')
      setUsername(me.username)
    } catch {
      setUsername(null)
    } finally {
      setLoading(false)
    }
  }, [])
  useEffect(() => { void check() }, [check])
  useEffect(() => {
    const expire = () => { setSessionExpired(true); setUsername(null) }
    window.addEventListener('nt:session-expired', expire)
    return () => window.removeEventListener('nt:session-expired', expire)
  }, [])
  if (loading) return <main className="center-page"><div className="loading-card"><span className="spinner" />Loading secure console…</div></main>
  if (!username) return <Login sessionExpired={sessionExpired} onLogin={(name) => { setSessionExpired(false); setUsername(name); navigate('/') }} />
  return (
    <div className="app-shell">
      <header className="topbar">
        <a href="/" className="brand"><span className="brand-mark">N</span><span>Nightthoughts<small>Imaging Review Console</small></span></a>
        <div className="account"><span className="account-role">REVIEWER</span><span>{username}</span><button className="button subtle" onClick={() => { void logout().finally(() => setUsername(null)) }}>Log out</button></div>
        <MobileNav username={username} onLogout={() => { void logout().finally(() => setUsername(null)) }} />
      </header>
      <div className="research-banner"><strong>Research demonstration</strong><span>AI-assisted drafts require qualified human review. Not for clinical use.</span></div>
      <Routes>
        <Route path="/" element={<Worklist />} />
        <Route path="/runs/:runId" element={<RunDetail />} />
        <Route path="/debug" element={<DebugCenter />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <footer>Synthetic or authorized de-identified data only · Approval exports a research draft, not clinical sign-off.</footer>
    </div>
  )
}
