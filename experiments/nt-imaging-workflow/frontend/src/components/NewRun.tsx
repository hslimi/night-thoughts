import { useState } from 'react'
import { api } from '../api'
import { useModalFocus } from './useModalFocus'

export default function NewRun({ onClose, onCreated }: { onClose: () => void; onCreated: (runId: string) => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const dialog = useModalFocus<HTMLElement>(true, onClose)
  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!file || busy) return
    setBusy(true); setError('')
    const body = new FormData()
    body.append('file', file)
    body.append('modality', 'XR')
    body.append('confirmed', 'true')
    try {
      const result = await api<{ run_id: string }>('/runs', { method: 'POST', body })
      onCreated(result.run_id)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Upload failed'); setBusy(false) }
  }
  return <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="new-run-title" ref={dialog}><button className="modal-close" onClick={onClose} aria-label="Close">×</button><p className="eyebrow">NEW DEMONSTRATION</p><h2 id="new-run-title">Submit one synthetic artifact</h2><p>PNG, JPEG, or constrained single-frame CR/DX DICOM. The original filename is not propagated.</p><form onSubmit={submit}><label htmlFor="artifact">Input file</label><input id="artifact" type="file" accept=".png,.jpg,.jpeg,.dcm" required onChange={(event) => setFile(event.target.files?.[0] ?? null)} /><label htmlFor="modality">Modality declaration</label><select id="modality" value="XR" disabled><option>XR — chest radiograph</option></select><label className="check-label"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} required />I confirm this is synthetic or authorized de-identified data.</label>{error && <div className="form-error" role="alert">{error}</div>}<div className="modal-actions"><button type="button" className="button subtle" disabled={busy} onClick={onClose}>Cancel</button><button className="button primary" disabled={busy || !file || !confirmed}>{busy ? 'Uploading…' : 'Create run'}</button></div></form></section></div>
}
