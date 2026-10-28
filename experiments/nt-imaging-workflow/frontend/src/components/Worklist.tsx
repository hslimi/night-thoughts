import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useEventStream } from '../live'
import type { DurableEvent, StreamEvent } from '../live'
import type { Run, Summary } from '../types'
import StatusBadge from './StatusBadge'
import NewRun from './NewRun'
import RunCards from './RunCards'

const statuses = ['', 'QUEUED', 'RUNNING', 'AWAITING_HUMAN_APPROVAL', 'APPROVED_DRAFT_EXPORTED', 'HUMAN_REJECTED', 'NEEDS_HUMAN_REVIEW', 'IMAGE_PREPARATION_FAILED', 'MODEL_OUTPUT_INVALID', 'QUARANTINED', 'CANCELLED', 'FAILED']
const activeStatuses = new Set(['INGESTED', 'PHI_SCREENING', 'PREPARING_IMAGE', 'IMAGE_READY', 'DRAFTING', 'REVISION_REQUESTED', 'RUNNING', 'DECISION_QUEUED'])
const actionableStatuses = new Set(['AWAITING_HUMAN_APPROVAL', 'NEEDS_HUMAN_REVIEW', 'FAILED', 'IMAGE_PREPARATION_FAILED', 'MODEL_OUTPUT_INVALID'])
const completedStatuses = new Set(['APPROVED_DRAFT_EXPORTED', 'HUMAN_REJECTED', 'CANCELLED'])

function lane(run: Run): string {
  if (run.status === 'QUEUED') return 'Queued'
  if (activeStatuses.has(run.status) || run.job_status === 'RUNNING') return 'Active'
  if (actionableStatuses.has(run.status)) return 'Action Required'
  if (completedStatuses.has(run.status)) return 'Completed'
  return run.status === 'QUARANTINED' ? 'Failed' : 'Action Required'
}

function age(timestamp: string | null): string {
  if (!timestamp) return 'no heartbeat'
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000))
  return seconds < 2 ? 'just now' : `${seconds}s ago`
}

export default function Worklist() {
  const [runs, setRuns] = useState<Run[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [activity, setActivity] = useState<DurableEvent[]>([])
  const [workerHeartbeat, setWorkerHeartbeat] = useState<string | null>(null)
  const [changedRun, setChangedRun] = useState('')
  const [follow, setFollow] = useState(false)
  const [status, setStatus] = useState('')
  const [mode, setMode] = useState('')
  const [modality, setModality] = useState('')
  const [model, setModel] = useState('')
  const [date, setDate] = useState('')
  const [source, setSource] = useState('')
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState('updated_desc')
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const navigate = useNavigate()
  const pageSize = 12
  const receivedEvent = useRef(false)

  const handleEvent = useCallback((event: StreamEvent) => {
    receivedEvent.current = true
    if (event.event_type === 'snapshot' || event.event_type === 'resync') {
      setRuns(event.payload.runs ?? [])
      if (event.payload.last_sequence) setActivity((current) => [...current].slice(-30))
      return
    }
    const durable = event as DurableEvent
    setActivity((current) => [...current, durable].slice(-30))
    if (durable.event_type.startsWith('WORKER_') || durable.event_type === 'heartbeat') {
      setWorkerHeartbeat(durable.timestamp_utc ?? new Date().toISOString())
    }
    if (!durable.run_id) return
    const snapshot = durable.payload.snapshot
    setRuns((current) => {
      const index = current.findIndex((run) => run.run_id === durable.run_id)
      if (index < 0 && !snapshot) return current
      const previous = index >= 0 ? current[index] : null
      const updated = {
        ...previous,
        ...snapshot,
        run_id: durable.run_id!,
        thread_id: durable.thread_id ?? previous?.thread_id ?? durable.run_id!,
        status: snapshot?.status ?? durable.run_status,
        current_node: durable.node_name ?? previous?.current_node,
        attempt: durable.attempt,
        revision: durable.revision,
        snapshot_updated_at: durable.timestamp_utc,
      } as Run
      if (index < 0) return [updated, ...current]
      const next = [...current]
      next[index] = updated
      return next
    })
    setChangedRun(durable.run_id)
    window.setTimeout(() => setChangedRun((current) => current === durable.run_id ? '' : current), 900)
  }, [])
  const { connection, lastPacketAt } = useEventStream('/api/events', handleEvent)

  useEffect(() => {
    Promise.all([api<Run[]>('/runs?page_size=100&sort=updated_desc'), api<Summary>('/dashboard/summary'), api<any>('/debug/overview')])
      .then(([runData, summaryData, debug]) => {
        if (!receivedEvent.current) setRuns(runData)
        setSummary(summaryData)
        setWorkerHeartbeat(debug.worker?.last_heartbeat ?? null)
        setError('')
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : 'Unable to load runs'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => runs.filter((run) =>
    (!status || run.status === status)
    && (!mode || run.inference_mode === mode)
    && (!modality || run.modality === modality)
    && (!model || [run.vision_model_id, run.text_model_id].includes(model))
    && (!date || run.snapshot_updated_at?.startsWith(date))
    && (!source || run.source_sha256 === source)
    && (!query || run.run_id.includes(query))
  ), [runs, status, mode, modality, model, date, source, query])
  const sorted = useMemo(() => [...filtered].sort((a, b) => {
    const left = a.snapshot_updated_at ?? ''
    const right = b.snapshot_updated_at ?? ''
    const result = left.localeCompare(right)
    return sort === 'updated_asc' ? result : -result
  }), [filtered, sort])
  const pages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const visible = sorted.slice((page - 1) * pageSize, page * pageSize)
  const queue = runs.filter((run) => run.status === 'QUEUED').sort((a, b) => (a.snapshot_updated_at ?? '').localeCompare(b.snapshot_updated_at ?? ''))
  const active = runs.filter((run) => lane(run) === 'Active')
  const actionable = runs.filter((run) => actionableStatuses.has(run.status)).length
  const failures = runs.filter((run) => ['FAILED', 'MODEL_OUTPUT_INVALID', 'IMAGE_PREPARATION_FAILED'].includes(run.status)).length
  const exports = runs.filter((run) => run.status === 'APPROVED_DRAFT_EXPORTED').length
  const cancelled = runs.filter((run) => run.status === 'CANCELLED').length

  useEffect(() => {
    if (!follow || !active.length || document.activeElement?.tagName === 'TEXTAREA') return
    const oldest = [...active].sort((a, b) => (a.snapshot_updated_at ?? '').localeCompare(b.snapshot_updated_at ?? ''))[0]
    if (oldest) navigate(`/runs/${oldest.run_id}`)
  }, [follow, active.map((run) => run.run_id).join(',')])

  return <main className="workspace">
    <div className="page-heading"><div><p className="eyebrow">LIVE IMAGING OPERATIONS</p><h1>Review worklist</h1><p>Real queue, node, model-call, and doctor-decision events.</p></div><div className="heading-actions"><span className={`live-badge ${connection.toLowerCase()}`} role="status"><span className="status-dot" />{connection}<small>{lastPacketAt ? ` · ${age(new Date(lastPacketAt).toISOString())}` : ''}</small></span><button className="button primary" onClick={() => setShowNew(true)}>New synthetic run</button></div></div>
    <div className="summary-grid six">
      <div className="summary-card"><span>Actionable</span><strong>{actionable}</strong><small>Doctor/operator action required</small></div>
      <div className="summary-card"><span>Active execution</span><strong>{active.length}</strong><small>{active[0]?.current_node?.replaceAll('_', ' ') ?? 'No active node'}</small></div>
      <div className="summary-card"><span>Queue depth</span><strong>{queue.length}</strong><small>Bounded work queue</small></div>
      <div className="summary-card"><span>Failures</span><strong>{failures}</strong><small>Preparation/model/service</small></div>
      <div className="summary-card"><span>Exports / cancelled</span><strong>{exports} / {cancelled}</strong><small>Completed and stopped runs</small></div>
      <div className="summary-card"><span>Worker heartbeat</span><strong className="environment-value">{age(workerHeartbeat)}</strong><small>{summary?.inference_mode ?? '—'} · {summary?.omlx_reachable ? 'oMLX reachable' : 'oMLX unavailable'}</small></div>
    </div>
    {summary?.mock_label && <div className="mock-banner">{summary.mock_label}</div>}
    <section className="panel live-controls"><label className="follow-toggle"><input type="checkbox" checked={follow} onChange={(event) => setFollow(event.target.checked)} />Follow live activity <span>Off by default; never interrupts decision entry.</span></label><Link className="button subtle" to="/debug">Open debugging center</Link></section>
    <section className="panel worklist-panel">
      <div className="filter-grid"><label>Status<select value={status} onChange={(event) => { setStatus(event.target.value); setPage(1) }}>{statuses.map((value) => <option key={value} value={value}>{value ? value.replaceAll('_', ' ').toLowerCase() : 'All statuses'}</option>)}</select></label><label>Inference<select value={mode} onChange={(event) => { setMode(event.target.value); setPage(1) }}><option value="">REAL + MOCK</option><option value="REAL">REAL</option><option value="MOCK">MOCK / FAULT</option></select></label><label>Modality<select value={modality} onChange={(event) => setModality(event.target.value)}><option value="">All supported</option><option value="XR">XR</option><option value="DX">DX</option><option value="CR">CR</option></select></label><label>Model<select value={model} onChange={(event) => setModel(event.target.value)}><option value="">All models</option><option value="MedMO-8B-Next">MedMO-8B-Next</option><option value="Qwen3.5-9B-MLX-4bit">Qwen3.5-9B-MLX-4bit</option></select></label><label>Date<input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label><label>Sort<select value={sort} onChange={(event) => setSort(event.target.value)}><option value="updated_desc">Newest first</option><option value="updated_asc">Oldest first</option></select></label></div>
      <div className="worklist-tools"><div className="status-distribution">{['Queued', 'Active', 'Action Required', 'Failed', 'Completed'].map((name) => <span key={name}>{name}<strong>{runs.filter((run) => lane(run) === name).length}</strong></span>)}</div><div className="worklist-search"><label className="search-field"><span className="sr-only">Search by run ID</span><input placeholder="Search opaque run ID…" value={query} onChange={(event) => setQuery(event.target.value)} /></label><label className="search-field"><span className="sr-only">Filter by source SHA-256</span><input placeholder="Source SHA-256…" value={source} onChange={(event) => setSource(event.target.value.trim())} /></label></div></div>
      {error && <div className="form-error" role="alert">{error}</div>}
      {loading ? <div className="empty-state"><span className="spinner" />Loading worklist…</div> : visible.length === 0 ? <div className="empty-state"><h3>No runs in this view</h3><p>Start a synthetic demonstration or change the filters.</p></div> : <><div className="table-wrap"><table><thead><tr><th>Run / lane</th><th>Status</th><th>Current node</th><th>Attempt / revision</th><th>Calls</th><th>Updated</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>{visible.map((run) => <tr key={run.run_id} className={changedRun === run.run_id ? 'row-changed' : ''}><td><code>{run.run_id}</code><small className="lane-label">{lane(run)}{run.status === 'QUEUED' ? ` · #${queue.findIndex((item) => item.run_id === run.run_id) + 1}` : ''}</small></td><td><StatusBadge status={run.status} /><span className={`mode-badge ${run.fault_profile && run.fault_profile !== 'none' ? 'mock' : run.inference_mode.toLowerCase()}`}>{run.fault_profile && run.fault_profile !== 'none' ? 'FAULT' : run.inference_mode}</span></td><td>{run.current_node?.replaceAll('_', ' ') ?? '—'}</td><td>{run.attempt} / {run.revision}</td><td>{run.model_calls} / {run.max_total_model_calls ?? 8}</td><td>{run.snapshot_updated_at ? new Date(run.snapshot_updated_at).toLocaleTimeString() : '—'}</td><td><Link className="row-action" to={`/runs/${run.run_id}`}>Open <span aria-hidden="true">→</span></Link></td></tr>)}</tbody></table></div><RunCards runs={visible} /></>}
      <div className="pagination"><button className="button subtle" disabled={page === 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>Previous</button><span>Page {page} / {pages} · {sorted.length} runs</span><button className="button subtle" disabled={page >= pages} onClick={() => setPage((value) => Math.min(pages, value + 1))}>Next</button></div>
    </section>
    <section className="panel activity-panel"><div className="panel-heading"><h2>Global live activity</h2><span>{connection === 'LIVE' ? 'Durable event stream' : 'Connection not live'}</span></div>{activity.length === 0 ? <p className="muted">Waiting for genuine application events.</p> : <div className="activity-feed">{[...activity].reverse().map((event) => <article key={event.event_id} className="activity-event"><span className="activity-time">{new Date(event.timestamp_utc).toLocaleTimeString()}</span><div><strong>{event.event_type.replaceAll('_', ' ')}</strong><p>{event.node_name ?? 'application'} · {event.run_id ? `${event.run_id.slice(0, 8)}…` : 'worker'} · attempt {event.attempt} / revision {event.revision}</p></div></article>)}</div>}</section>
    {showNew && <NewRun onClose={() => setShowNew(false)} onCreated={(runId) => { setShowNew(false); navigate(`/runs/${runId}`) }} />}
  </main>
}
