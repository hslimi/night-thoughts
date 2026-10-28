import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { useEventStream } from '../live'
import type { DurableEvent, StreamEvent } from '../live'
import type { Draft, Run } from '../types'
import StatusBadge from './StatusBadge'
import ReviewWorkspace from './ReviewWorkspace'
import AuditTimeline from './AuditTimeline'
import ExportView from './ExportView'
import GraphInspector from './GraphInspector'
import LiveWorkflow from './LiveWorkflow'

const tabs = ['Monitor', 'Doctor review', 'Local graph', 'Audit & provenance', 'Exports']

export default function RunDetail() {
  const { runId = '' } = useParams()
  const [run, setRun] = useState<Run | null>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [events, setEvents] = useState<DurableEvent[]>([])
  const [tab, setTab] = useState('Monitor')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const receivedEvent = useRef(false)
  const refresh = useCallback(async (force = false) => {
    if (receivedEvent.current && !force) return
    try {
      const [current, report, inspector] = await Promise.all([
        api<Run>(`/runs/${runId}`),
        api<{ draft: Draft | null }>(`/runs/${runId}/draft`),
        api<{ events: DurableEvent[] }>(`/debug/runs/${runId}`),
      ])
      setRun(current)
      setDraft(report.draft)
      setEvents(inspector.events)
      setError('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to refresh run') }
  }, [runId])
  useEffect(() => { void refresh() }, [refresh])

  const handleEvent = useCallback((event: StreamEvent) => {
    receivedEvent.current = true
    if (event.event_type === 'snapshot' || event.event_type === 'resync') {
      const current = event.payload.run as Run | undefined
      if (current) {
        setRun(current)
        setDraft(current.draft ?? null)
      }
      if (event.event_type === 'resync') void refresh(true)
      return
    }
    const durable = event as DurableEvent
    if (durable.run_id !== runId) return
    setEvents((current) => current.some((item) => item.event_id === durable.event_id) ? current : [...current, durable])
    const snapshot = durable.payload.snapshot
    setRun((previous) => ({
      ...previous,
      ...snapshot,
      run_id: durable.run_id!,
      thread_id: durable.thread_id ?? previous?.thread_id ?? durable.run_id!,
      status: snapshot?.status ?? durable.run_status,
      current_node: durable.node_name ?? previous?.current_node,
      attempt: durable.attempt,
      revision: durable.revision,
      snapshot_updated_at: durable.timestamp_utc,
    }) as Run)
    if (snapshot?.draft !== undefined) setDraft(snapshot.draft)
  }, [runId, refresh])
  const { connection, lastPacketAt } = useEventStream(`/api/runs/${runId}/events`, handleEvent)

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
  return <main className="workspace">
    <Link to="/" className="back-link">← Back to worklist</Link>
    <div className="run-heading"><div><p className="eyebrow">LIVE WORKFLOW MONITOR</p><div className="heading-status"><h1>{run.status.replaceAll('_', ' ')}</h1><StatusBadge status={run.fault_profile && run.fault_profile !== 'none' ? 'FAULT INJECTION' : run.inference_mode} /></div><code>{run.run_id}</code></div><div className="run-actions">{(['QUEUED', 'RUNNING', 'AWAITING_HUMAN_APPROVAL', 'INTERRUPTED'].includes(run.status) || ['QUEUED', 'RUNNING'].includes(run.job_status ?? '')) && <button className="button danger-outline" onClick={() => void action('cancel')}>Cancel run</button>}{run.status === 'FAILED' && run.error?.retryable && <button className="button subtle" onClick={() => void action('retry')}>Retry technical failure</button>}</div></div>
    {notice && <div className="success-banner" role="status">{notice}</div>}{error && <div className="form-error" role="alert">{error}</div>}
    <div className="run-meta-strip"><span className={`live-badge ${connection.toLowerCase()}`}>{connection}</span><span>Attempt <strong>{run.attempt} / {run.max_attempts ?? 2}</strong></span><span>Revision <strong>{run.revision}</strong></span><span>Model calls <strong>{run.model_calls} / {run.max_total_model_calls ?? 8}</strong></span><span>Packet <strong>{lastPacketAt ? new Date(lastPacketAt).toLocaleTimeString() : '—'}</strong></span></div>
    <div className="tab-list" role="tablist">{tabs.map((name) => <button key={name} role="tab" aria-selected={tab === name} className={tab === name ? 'tab active' : 'tab'} onClick={() => setTab(name)}>{name}</button>)}</div>
    {tab === 'Monitor' && <><LiveWorkflow run={run} events={events} connection={connection} />{run.error && <div className="panel failure-panel"><h2>Failure and recovery</h2><p><strong>{run.error.code}</strong> — {run.error.message}</p><p>{run.error.retryable ? 'A technical retry may be available. It cannot bypass clinical or workflow gates.' : 'This outcome cannot be overridden by doctor approval or technical retry.'}</p></div>}<div className="panel"><div className="panel-heading"><h2>Imaging Readiness Agent</h2><StatusBadge status={run.readiness_status} /></div><dl className="metadata-grid"><dt>Policy</dt><dd>{run.preparation_policy_version ?? '—'}</dd><dt>Operations</dt><dd>{(run.preparation_operations ?? []).join(' → ') || 'No preparation operations'}</dd><dt>Warnings</dt><dd>{(run.preparation_warnings ?? []).join('; ') || 'None'}</dd><dt>Receipt</dt><dd><code>{run.readiness_receipt_id ?? 'Legacy run / no receipt'}</code></dd></dl></div><div className="panel"><h2>Provenance</h2><dl className="metadata-grid"><dt>Vision model</dt><dd>{run.vision_model_id ?? '—'}</dd><dt>Text model</dt><dd>{run.text_model_id ?? '—'}</dd><dt>Workflow</dt><dd>{run.workflow_version}</dd><dt>Prompt / policy</dt><dd>{run.prompt_version} / {run.policy_version}</dd><dt>Source SHA-256</dt><dd><code>{run.source_sha256}</code></dd><dt>Derived SHA-256</dt><dd><code>{run.prepared_sha256}</code></dd></dl></div></>}
    {tab === 'Doctor review' && <ReviewWorkspace run={run} draft={draft} onChanged={refresh} />}
    {tab === 'Local graph' && <GraphInspector run={run} />}
    {tab === 'Audit & provenance' && <AuditTimeline run={run} />}
    {tab === 'Exports' && <ExportView run={run} />}
  </main>
}
