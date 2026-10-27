import { useState } from 'react'
import { login } from '../api'

export default function Login({ onLogin, sessionExpired = false }: { onLogin: (username: string) => void; sessionExpired?: boolean }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true); setError('')
    try {
      const result = await login(username, password)
      onLogin(result.username)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Invalid username or password')
    } finally { setBusy(false) }
  }
  return <main className="login-page"><section className="login-story"><div className="brand login-brand"><span className="brand-mark">N</span><span>Nightthoughts<small>Imaging Review Console</small></span></div><div className="story-copy"><p className="eyebrow">GOVERNED LOCAL INFERENCE</p><h1>Clinical workflow.<br />Human control.</h1><p>Review structured drafts, inspect independent gates, and make the final export decision on a stateful local imaging workflow.</p></div><div className="story-points"><span>Deterministic policy</span><span>Local oMLX inference</span><span>Complete audit trail</span></div></section><section className="login-panel"><form className="login-form" onSubmit={submit}><p className="eyebrow">SECURE REVIEWER ACCESS</p><h2>Welcome back</h2><p className="muted">Sign in with your provisioned doctor account.</p><label htmlFor="username">Username</label><input id="username" name="username" type="text" inputMode="text" autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} /><label htmlFor="password">Password</label><div className="password-field"><input id="password" name="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} aria-describedby={error ? 'login-error' : undefined} /><button className="password-toggle" type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword((value) => !value)}>{showPassword ? 'Hide' : 'Show'}</button></div>{sessionExpired && <div className="session-notice" role="status">Your session expired. Sign in again to continue.</div>}{error && <div className="form-error" id="login-error" role="alert">{error}</div>}<button className="button primary full" disabled={busy || !username || !password}>{busy ? <><span className="spinner" />Signing in…</> : 'Sign in securely'}</button><div className="login-notice"><strong>Research demonstration</strong><p>AI-assisted drafts require qualified human review. Not for clinical use. Use synthetic or authorized de-identified data only.</p></div></form></section></main>
}
