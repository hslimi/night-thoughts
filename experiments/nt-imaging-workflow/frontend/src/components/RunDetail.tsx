import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import type { Draft, Run } from '../types'
import StatusBadge from './StatusBadge'
import ReviewWorkspace from './ReviewWorkspace'
import AuditTimeline from './AuditTimeline'
import ExportView from './ExportView'
import GraphInspector from './GraphInspector'

const tabs = ['Monitor', 'Doctor review', 'Local graph', 'Audit & provenance', 'Exports']
const steps = ['ingest_validate', 'phi_screen', 'modality_gate', 'imaging_readiness', 'derived_image_safety_check', 'generate_draft', 'deterministic_contract_gate', 'visual_consistency_review', 'text_quality_review', 'human_approval', 'export_approved_draft']

export default function RunDetail() {
  const { runId = '' } = useParams()
  const [run, setRun] = useState<Run | null>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [tab, setTab] = useState('Monitor')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const refresh = useCallback(async () => {
    try {
      const [current, report] = await Promise.all([
        api<Run>(`/runs/${runId}`),
        api<{ draft: Draft | null }>(`/runs/${runId}/draft`),
      ])
      setRun(current); setDraft(report.draft); setError('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to refresh run') }
  }, [runId])
  useEffect(() => {
    const initial = setTimeout(() => void refresh(), 0)
    const timer = setInterval(() => void refresh(), 3000)
    return () => { clearTimeout(initial); clearInterval(timer) }
  }, [refresh])
  async function action(kind: 'cancel' | 'retry') {
    setNotice(''); setError('')
    try {
      await api(`/runs/${runId}/${kind}`, { method: 'POST' })
      setNotice(kind === 'cancel' ? 'Cancellation recorded. Late worker responses cannot authorize export.' : 'Technical retry queued as a new run.')
      await refresh()
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Action failed') }
  }
  if (!run && !error) return <main className="workspace"><div className="empty-state"><span className="spinner" />Loading run…</div></main>
  if (!run) return <main className="workspace"><div className="form-error">{error}</div><Link to="/">Back to worklist</Link></main>
  const activeStep = run.current_node ?? (run.status === 'APPROVED_DRAFT_EXPORTED' ? 'export_approved_draft' : run.status === 'AWAITING_HUMAN_APPROVAL' ? 'human_approval' : '')
  return (
    <main className="workspace">
      <Link to="/" className="back-link">← Back to worklist</Link>
      <div className="run-heading"><div><p className="eyebrow">WORKFLOW MONITOR</p><div className="heading-status"><h1>{run.status.replaceAll('_', ' ')}</h1><StatusBadge status={run.fault_profile && run.fault_profile !== 'none' ? 'FAULT INJECTION' : run.inference_mode} /></div><code>{run.run_id}</code></div><div className="run-actions">{(['QUEUED', 'RUNNING', 'AWAITING_HUMAN_APPROVAL', 'INTERRUPTED'].includes(run.status) || ['QUEUED', 'RUNNING'].includes(run.job_status ?? '')) && <button className="button danger-outline" onClick={() => void action('cancel')}>Cancel run</button>}{run.status === 'FAILED' && run.error?.retryable && <button className="button subtle" onClick={() => void action('retry')}>Retry technical failure</button>}</div></div>
      {notice && <div className="success-banner" role="status">{notice}</div>}{error && <div className="form-error" role="alert">{error}</div>}
      <div className="run-meta-strip"><span>Attempt <strong>{run.attempt} / {run.max_attempts ?? 2}</strong></span><span>Revision <strong>{run.revision}</strong></span><span>Model calls <strong>{run.model_calls} / {run.max_total_model_calls ?? 8}</strong></span><span>Updated <strong>{run.snapshot_updated_at ? new Date(run.snapshot_updated_at).toLocaleTimeString() : '—'}</strong></span></div>
      <div className="tab-list" role="tablist">{tabs.map((name) => <button key={name} role="tab" aria-selected={tab === name} className={tab === name ? 'tab active' : 'tab'} onClick={() => setTab(name)}>{name}</button>)}</div>
      {tab === 'Monitor' && <section>
        <div className="panel"><h2>Workflow progression</h2><div className="workflow-steps">{steps.map((step, index) => { const currentIndex = steps.indexOf(activeStep); const complete = currentIndex > index || run.status === 'APPROVED_DRAFT_EXPORTED'; return <div className={`workflow-step ${complete ? 'complete' : ''} ${activeStep === step ? 'current' : ''}`} key={step}><span className="step-index">{complete ? '✓' : index + 1}</span><span>{step.replaceAll('_', ' ')}</span></div> })}</div></div>
        {run.error && <div className="panel failure-panel"><h2>Failure and recovery</h2><p><strong>{run.error.code}</strong> — {run.error.message}</p><p>{run.error.retryable ? 'A technical retry may be available. It creates a new run and cannot bypass clinical or workflow gates.' : 'This outcome cannot be overridden by doctor approval or technical retry.'}</p></div>}
        <div className="gate-grid">{[['PHI screening', run.phi_status], ['Modality', run.modality_status], ['Imaging readiness', run.readiness_status], ['Derived image safety', run.derived_phi_status], ['Deterministic contract', run.contract_status], ['Visual consistency', run.grounding_status], ['Text quality', run.quality_status], ['Human review', run.status === 'AWAITING_HUMAN_APPROVAL' ? 'PENDING' : run.human_decision ? 'DECIDED' : 'PENDING']].map(([label, status]) => <div className="gate-card" key={label}><span>{label}</span><StatusBadge status={status} /></div>)}</div>
        <div className="panel"><div className="panel-heading"><h2>Imaging Readiness Agent</h2><StatusBadge status={run.readiness_status} /></div><dl className="metadata-grid"><dt>Policy</dt><dd>{run.preparation_policy_version ?? '—'}</dd><dt>Operations</dt><dd>{(run.preparation_operations ?? []).join(' → ') || 'No preparation operations'}</dd><dt>Warnings</dt><dd>{(run.preparation_warnings ?? []).join('; ') || 'None'}</dd><dt>Receipt</dt><dd><code>{run.readiness_receipt_id ?? 'Legacy run / no receipt'}</code></dd></dl></div>
        <div className="panel"><h2>Provenance</h2><dl className="metadata-grid"><dt>Vision model</dt><dd>{run.vision_model_id ?? '—'}</dd><dt>Text model</dt><dd>{run.text_model_id ?? '—'}</dd><dt>Workflow</dt><dd>{run.workflow_version}</dd><dt>Prompt / policy</dt><dd>{run.prompt_version} / {run.policy_version}</dd><dt>Source SHA-256</dt><dd><code>{run.source_sha256}</code></dd><dt>Derived SHA-256</dt><dd><code>{run.prepared_sha256}</code></dd></dl></div>
      </section>}
      {tab === 'Doctor review' && <ReviewWorkspace run={run} draft={draft} onChanged={refresh} />}
      {tab === 'Local graph' && <GraphInspector run={run} />}
      {tab === 'Audit & provenance' && <AuditTimeline run={run} />}
      {tab === 'Exports' && <ExportView run={run} />}
    </main>
  )
}
