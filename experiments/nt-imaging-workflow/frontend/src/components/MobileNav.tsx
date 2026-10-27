import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useModalFocus } from './useModalFocus'

export default function MobileNav({ username, onLogout }: { username: string; onLogout: () => void }) {
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)
  const drawer = useModalFocus<HTMLElement>(open, close)
  return <>
    <button className="mobile-menu-button" aria-label="Open navigation" aria-expanded={open} aria-controls="mobile-navigation" onClick={() => setOpen(true)}>☰<span>Menu</span></button>
    {open && <div className="drawer-backdrop"><aside id="mobile-navigation" className="mobile-drawer" role="dialog" aria-modal="true" aria-label="Main navigation" ref={drawer}><div className="drawer-heading"><span>Nightthoughts</span><button className="modal-close" aria-label="Close navigation" onClick={close}>×</button></div><p className="eyebrow">SIGNED IN AS</p><p>{username}</p><Link to="/" onClick={close}>Review worklist</Link><p className="drawer-note">Research demonstration — AI-assisted drafts require qualified human review. Not for clinical use.</p><button className="button subtle full" onClick={() => { close(); onLogout() }}>Log out</button></aside></div>}
  </>
}
