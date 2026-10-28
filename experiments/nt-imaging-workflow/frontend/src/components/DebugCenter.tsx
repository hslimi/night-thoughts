import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useEventStream } from '../live'
import type { DurableEvent, StreamEvent } from '../live'
import type { Run } from '../types'
import StatusBadge from './StatusBadge'

const tabs = ['Overview', 'Run inspector', 'Trace waterfall', 'Logs', 'Diagnostics']

type Overview = {
  application_version: string
  instance_id: string
  code_fingerprint: string
  data_fingerprint: string
  workflow_version: string
  inference_mode: string
  vision_model_id?: string
  text_model_id?: string
  database_fingerprint: string
  worker?: { worker_id: string; status: string; last_heartbeat: string; pid: number }
  worker_heartbeat_age_seconds?: number
  queue_depth: number
  active_job?: { job_id: string; run_id: string; status: string }
  sse_connection_count: number
  last_event_sequence: number
}
type Inspection = { state: Run; events: DurableEvent[]; model_calls: any[]; job?: any; retry_eligible: boolean; cancel_eligible: boolean; event_gaps: number[] }
type Trace = { events: DurableEvent[]; queue_wait_ms?: number; human_wait_ms?: number; total_node_duration_ms: number }

export default function DebugCenter() {
  const [tab, setTab] = useState('Overview')
  const [overview, setOverview] = useState<Overview | null>(null)
  const [runs, setRuns] = useState<Run[]>([])
  const [runId, setRunId] = useState('')
  const [inspection, setInspection] = useState<Inspection | null>(null)
  const [trace, setTrace] = useState<Trace | null>(null)
  const [diagnostics, setDiagnostics] = useState<any>(null)
  const [logs, setLogs] = useState<DurableEvent[]>([])
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const handleEvent = useCallback((event: StreamEvent) => {
    if (event.event_type === 'snapshot' || event.event_type === 'resync') return
    const durable = event as DurableEvent
    if (durable.event_type.startsWith('WORKER_') || durable.event_type === 'heartbeat') {
      setOverview((current) => current ? { ...current, worker_heartbeat_age_seconds: 0, last_event_sequence: durable.sequence } : current)
    }
  }, [])
  const { connection } = useEventStream('/api/events', handleEvent)

  useEffect(() => {
    Promise.all([api<Overview>('/debug/overview'), api<Run[]>('/runs?page_size=100'), api<any>('/debug/diagnostics')])
      .then(([current, runData, checks]) => {
        setOverview(current)
        setRuns(runData)
        setDiagnostics(checks)
        if (!runId && runData[0]) setRunId(runData[0].run_id)
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : 'Debug data unavailable'))
  }, [])
  useEffect(() => {
    if (!runId) return
    Promise.all([api<Inspection>(`/debug/runs/${runId}`), api<Trace>(`/debug/runs/${runId}/trace`), api<{ events: DurableEvent[] }>(`/debug/logs?run=${runId}`)])
      .then(([current, traceData, logData]) => { setInspection(current); setTrace(traceData); setLogs(logData.events); setError('') })
      .catch((reason) => setError(reason instanceof Error ? reason.message : 'Run inspection unavailable'))
  }, [runId])
  const filteredLogs = useMemo(() => logs.filter((event) => !query || JSON.stringify(event).toLowerCase().includes(query.toLowerCase())), [logs, query])
  const firstTimestamp = trace?.events[0] ? new Date(trace.events[0].timestamp_utc).getTime() : 0

  return <main className="workspace debug-workspace">
    <Link to="/" className="back-link">← Back to worklist</Link>
    <div className="page-heading"><div><p className="eyebrow">OPERATOR DEBUGGING CENTER</p><h1>Execution diagnostics</h1><p>Safe local evidence for queue, graph, model calls, and runtime identity.</p></div><span className={`live-badge ${connection.toLowerCase()}`}>{connection}</span></div>
    {error && <div className="form-error" role="alert">{error}</div>}
    <div className="tab-list" role="tablist">{tabs.map((name) => <button key={name} role="tab" aria-selected={tab === name} className={tab === name ? 'tab active' : 'tab'} onClick={() => setTab(name)}>{name}</button>)}</div>
    {tab === 'Overview' && <section><div className="summary-grid four">{overview && <>
      <div className="summary-card"><span>Application / workflow</span><strong>v{overview.application_version}</strong><small>{overview.workflow_version} · {overview.inference_mode}</small></div>
      <div className="summary-card"><span>Worker</span><strong>{overview.worker?.status ?? 'NO HEARTBEAT'}</strong><small>{overview.worker_heartbeat_age_seconds ?? '—'}s ago · PID {overview.worker?.pid ?? '—'}</small></div>
      <div className="summary-card"><span>Queue / active job</span><strong>{overview.queue_depth} / {overview.active_job ? 1 : 0}</strong><small>{overview.active_job?.run_id ?? 'No active job'}</small></div>
      <div className="summary-card"><span>SSE / event sequence</span><strong>{overview.sse_connection_count} / {overview.last_event_sequence}</strong><small>Authenticated live connections</small></div>
    </>}</div>{overview && <div className="panel"><h2>Canonical runtime identity</h2><dl className="metadata-grid"><dt>Instance ID</dt><dd><code>{overview.instance_id}</code></dd><dt>Code fingerprint</dt><dd><code>{overview.code_fingerprint}</code></dd><dt>Database fingerprint</dt><dd><code>{overview.database_fingerprint}</code></dd><dt>Data-root fingerprint</dt><dd><code>{overview.data_fingerprint}</code></dd><dt>Vision / text models</dt><dd>{overview.vision_model_id} / {overview.text_model_id}</dd></dl></div>}</section>}
    {tab === 'Run inspector' && <section><div className="panel"><label>Run to inspect<select value={runId} onChange={(event) => setRunId(event.target.value)}>{runs.map((run) => <option key={run.run_id} value={run.run_id}>{run.run_id} · {run.status}</option>)}</select></label></div>{inspection && <><div className="debug-two-column"><div className="panel"><div className="panel-heading"><h2>Typed run state</h2><StatusBadge status={inspection.state.status} /></div><dl className="metadata-grid"><dt>Thread</dt><dd><code>{inspection.state.thread_id}</code></dd><dt>Current / previous node</dt><dd>{inspection.state.current_node} / {inspection.events.at(-2)?.node_name ?? '—'}</dd><dt>Attempt / revision</dt><dd>{inspection.state.attempt} / {inspection.state.revision}</dd><dt>Retry eligible</dt><dd>{inspection.retry_eligible ? 'Yes' : 'No'}</dd><dt>Cancel eligible</dt><dd>{inspection.cancel_eligible ? 'Yes' : 'No'}</dd><dt>Event gaps</dt><dd>{inspection.event_gaps.length ? inspection.event_gaps.join(', ') : 'None'}</dd></dl></div><div className="panel"><h2>Gate results</h2><dl className="metadata-grid"><dt>PHI / modality</dt><dd>{inspection.state.phi_status} / {inspection.state.modality_status}</dd><dt>Readiness / derived safety</dt><dd>{inspection.state.readiness_status} / {inspection.state.derived_phi_status}</dd><dt>Contract / visual / quality</dt><dd>{inspection.state.contract_status} / {inspection.state.grounding_status} / {inspection.state.quality_status}</dd><dt>Preparation receipt</dt><dd><code>{inspection.state.readiness_receipt_id ?? '—'}</code></dd><dt>Prepared hash</dt><dd><code>{inspection.state.prepared_sha256}</code></dd></dl></div></div><div className="panel"><h2>Job and model-call receipts</h2><p>Job {inspection.job?.job_id} · {inspection.job?.status} · heartbeat {inspection.job?.heartbeat_at ?? '—'}</p><div className="receipt-list">{inspection.model_calls.map((call, index) => <article className="receipt" key={index}><strong>{call.stage} · {call.status}</strong><p>{call.model_id} · {call.latency_ms} ms</p><code>{call.output_sha256}</code></article>)}</div></div></>}</section>}
    {tab === 'Trace waterfall' && <section>{trace && <div className="panel"><div className="panel-heading"><h2>Trace waterfall</h2><span>Queue {trace.queue_wait_ms ?? '—'} ms · human wait {trace.human_wait_ms ?? '—'} ms · nodes {trace.total_node_duration_ms} ms</span></div><div className="trace-waterfall">{trace.events.filter((event) => event.duration_ms !== undefined).map((event) => { const start = firstTimestamp ? new Date(event.timestamp_utc).getTime() - firstTimestamp : 0; const width = Math.max(1, Math.min(100, (event.duration_ms ?? 0) / Math.max(1, trace.total_node_duration_ms) * 100)); return <article className="trace-row" key={event.event_id}><span>{event.node_name}<small>{event.event_type}</small></span><div className="trace-track"><div className={`trace-bar ${event.event_type.includes('FAILED') ? 'failed' : ''}`} style={{ marginLeft: `${Math.min(85, start / Math.max(1, trace.total_node_duration_ms) * 100)}%`, width: `${width}%` }} /></div><code>{event.duration_ms} ms</code></article>})}</div></div>}</section>}
    {tab === 'Logs' && <section className="panel"><div className="panel-heading"><h2>Structured local logs</h2><label>Safe search<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Run, node, error, model-call ID…" /></label></div><p className="muted">No credentials, raw DICOM metadata, full prompts, or patient identifiers.</p><div className="live-timeline debug-logs">{filteredLogs.map((event) => <article className="timeline-event" key={event.event_id}><span className="timeline-time">{new Date(event.timestamp_utc).toLocaleTimeString()}</span><div><strong>{event.event_type}</strong><p>{event.run_id} · {event.job_id ?? 'no job'} · {event.node_name} · attempt {event.attempt} · revision {event.revision}</p><code>{event.event_id}</code></div></article>)}</div></section>}
    {tab === 'Diagnostics' && <section><div className="panel"><div className="panel-heading"><h2>Deployment diagnostics</h2><a className="button secondary" href={`/api/v1/debug/support-bundle${runId ? `?run=${runId}` : ''}`} download>Download sanitized support bundle</a></div>{diagnostics?.alerts?.length ? <div className="alert-list">{diagnostics.alerts.map((alert: any) => <div className="form-error" key={alert.code}><strong>{alert.code}</strong> — {alert.message}</div>)}</div> : <div className="success-banner">No stale-state alerts are active.</div>}<div className="diagnostic-grid">{Object.entries(diagnostics?.checks ?? {}).map(([name, value]: [string, any]) => <div className="gate-card" key={name}><span>{name.replaceAll('_', ' ')}</span><StatusBadge status={value.status} /><small>{value.error_category ?? ''}</small></div>)}</div></div></section>}
  </main>
}
