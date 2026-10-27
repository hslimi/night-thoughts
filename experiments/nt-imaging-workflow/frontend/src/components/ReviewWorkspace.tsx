import { useCallback, useEffect, useState } from 'react'
import { api, decide } from '../api'
import type { Decision, Draft, ReviewIssue, Run } from '../types'
import StatusBadge from './StatusBadge'
import ImageInspector from './ImageInspector'
import { useModalFocus } from './useModalFocus'

export default function ReviewWorkspace({ run, draft, onChanged }: { run: Run; draft: Draft | null; onChanged: () => Promise<void> }) {
  const [note, setNote] = useState('')
  const [imageMode, setImageMode] = useState<'source' | 'prepared'>('prepared')
  const [pending, setPending] = useState<Decision | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<{ decision: Decision; reviewer: string; note: string; revision: number; resulting_state: string; decided_at: string }[]>([])
  const eligible = run.status === 'AWAITING_HUMAN_APPROVAL' && !!draft
  useEffect(() => {
    api<{ decisions: typeof history }>(`/runs/${run.run_id}/reviews`).then((result) => setHistory(result.decisions)).catch(() => setHistory([]))
  }, [run.run_id, run.revision, run.snapshot_updated_at])
  const close = useCallback(() => setPending(null), [])
  const dialog = useModalFocus<HTMLElement>(pending !== null, close)

  async function confirm() {
    if (!pending || busy) return
    setBusy(true); setError('')
    try {
      await decide(run.run_id, pending, note)
      setPending(null); setNote('')
      await onChanged()
    } catch (reason) {
      setError(reason instanceof Error ? `${reason.message}. The run may have changed; refresh and review again.` : 'Decision failed')
      setPending(null)
    } finally { setBusy(false) }
  }

  if (!draft) return <div className="empty-state panel"><h2>No reviewable draft</h2><p>A draft appears here only after every model-assisted gate passes and the graph interrupts for doctor review.</p></div>
  return <section className="review-layout">
    <div className="image-panel panel"><div className="panel-heading"><h2>Source and prepared image</h2><span>Immutable artifact lineage</span></div>{run.prepared_artifact_id ? <><div className="comparison-mobile"><div className="segmented-control" aria-label="Image version"><button className={imageMode === 'source' ? 'active' : ''} onClick={() => setImageMode('source')}>Source</button><button className={imageMode === 'prepared' ? 'active' : ''} onClick={() => setImageMode('prepared')}>Prepared</button></div><ImageInspector src={`/api/v1/runs/${run.run_id}/${imageMode === 'source' ? 'source-preview' : 'image'}`} label={imageMode === 'source' ? 'PHI-screened source preview' : 'Prepared model input'} /></div><div className="comparison-desktop"><div><h3>PHI-screened source</h3><ImageInspector src={`/api/v1/runs/${run.run_id}/source-preview`} label="PHI-screened source preview" /></div><div><h3>Prepared model input</h3><ImageInspector src={`/api/v1/runs/${run.run_id}/image`} label="Prepared model input" /></div></div></> : <p>No derived image is available.</p>}</div>
    <div className="panel preparation-panel"><div className="panel-heading"><h2>Imaging Readiness Agent</h2><StatusBadge status={run.readiness_status} /></div><dl className="metadata-grid"><dt>Policy</dt><dd>{run.preparation_policy_version}</dd><dt>Operations</dt><dd>{(run.preparation_operations ?? []).join(' → ') || 'No receipt (legacy run)'}</dd><dt>Dimensions</dt><dd>{run.preparation_metrics?.prepared_width} × {run.preparation_metrics?.prepared_height}</dd><dt>Intensity range</dt><dd>{run.preparation_metrics?.intensity_min} – {run.preparation_metrics?.intensity_max}</dd><dt>p01 / p99</dt><dd>{run.preparation_metrics?.intensity_p01} / {run.preparation_metrics?.intensity_p99}</dd><dt>Source hash</dt><dd><code>{run.source_sha256}</code></dd><dt>Prepared hash</dt><dd><code>{run.prepared_sha256}</code></dd><dt>Warnings</dt><dd>{(run.preparation_warnings ?? []).join('; ') || 'None'}</dd></dl><a href={`/api/v1/runs/${run.run_id}/preparation-receipt`} target="_blank" rel="noreferrer">Open preparation receipt</a></div>
    <div className="draft-panel panel"><div className="panel-heading"><h2>Structured draft</h2><span>Revision {run.revision}</span></div><h3>Technique</h3><p>{draft.technique}</p><h3>Comparison</h3><p>{draft.comparison}</p><h3>Findings</h3><p>{draft.findings_text}</p><ul>{draft.findings.map((finding, index) => <li key={index}><strong>{finding.label} · {finding.status}</strong><p>{finding.description}</p></li>)}</ul><h3>Impression</h3><ul>{draft.impression.map((item, index) => <li key={index}>{item}</li>)}</ul><h3>Limitations</h3><ul>{draft.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul><div className="draft-notice">{draft.draft_notice}</div></div>
    <aside className="review-sidebar">
      <div className="panel"><h2>Independent reviews</h2><div className="review-status"><span>Visual consistency</span><StatusBadge status={run.grounding_status} /></div><div className="review-status"><span>Text quality</span><StatusBadge status={run.quality_status} /></div>{run.review_issues && run.review_issues.length > 0 && <div className="issue-list">{run.review_issues.slice(-8).map((issue: ReviewIssue, index) => <div className="issue" key={index}><strong>{issue.stage} · {issue.code}</strong><p>{issue.message}</p></div>)}</div>}</div>
      <div className="panel revision-history"><h2>Decision and revision history</h2>{history.length === 0 ? <p className="muted">No doctor decisions recorded yet.</p> : history.map((item, index) => <div className="issue" key={`${item.decided_at}-${index}`}><strong>Revision {item.revision} · {item.decision.replaceAll('_', ' ')}</strong><p>{item.note || 'No note required for approval.'}</p><p>{item.reviewer} · {new Date(item.decided_at).toLocaleString()} · {item.resulting_state.replaceAll('_', ' ')}</p></div>)}</div>
      <div className="panel decision-panel"><h2>Doctor decision</h2><p>Approval exports a research demonstration draft. It is not radiologist sign-off.</p><label htmlFor="decision-note">Review note <span>(required for rejection/change requests)</span></label><textarea id="decision-note" value={note} onChange={(event) => setNote(event.target.value)} maxLength={1000} placeholder="Concise operational feedback…" />{error && <div className="form-error" role="alert">{error}</div>}<div className="decision-actions"><button className="button primary full" disabled={!eligible || busy} onClick={() => setPending('APPROVE')}>Approve export</button><button className="button secondary full" disabled={!eligible || !note.trim() || busy} onClick={() => setPending('REQUEST_CHANGES')}>Request changes</button><button className="button danger-outline full" disabled={!eligible || !note.trim() || busy} onClick={() => setPending('REJECT')}>Reject draft</button></div>{!eligible && <p className="muted">Decisions are available only while the graph is awaiting human approval.</p>}</div>
    </aside>
    {pending && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title" ref={dialog}><p className="eyebrow">CONFIRM DOCTOR DECISION</p><h2 id="confirm-title">{pending === 'APPROVE' ? 'Approve research-draft export?' : pending === 'REJECT' ? 'Reject this draft?' : 'Request a bounded revision?'}</h2><p>{pending === 'APPROVE' ? 'The export node will independently recheck every gate and your approval before writing JSON, Markdown, and manifest files.' : pending === 'REJECT' ? 'The run will terminate without an export. This decision is recorded in the audit history.' : 'The graph will start a new bounded revision cycle, resetting downstream review statuses. Your note will guide the next draft.'}</p><div className="modal-actions"><button className="button subtle" disabled={busy} onClick={close}>Go back</button><button className="button primary" disabled={busy} onClick={() => void confirm()}>{busy ? 'Submitting…' : 'Confirm decision'}</button></div></section></div>}
  </section>
}
