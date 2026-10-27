import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { Run, Summary } from '../types'
import StatusBadge from './StatusBadge'
import NewRun from './NewRun'
import RunCards from './RunCards'

const statuses = ['', 'QUEUED', 'RUNNING', 'AWAITING_HUMAN_APPROVAL', 'APPROVED_DRAFT_EXPORTED', 'HUMAN_REJECTED', 'NEEDS_HUMAN_REVIEW', 'IMAGE_PREPARATION_FAILED', 'MODEL_OUTPUT_INVALID', 'QUARANTINED', 'CANCELLED', 'FAILED']

export default function Worklist() {
  const [runs, setRuns] = useState<Run[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
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
  const pageSize = 15
  const refresh = useCallback(async () => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize), sort })
    if (status) params.set('status', status)
    if (mode) params.set('inference_mode', mode)
    if (modality) params.set('modality', modality)
    if (model) params.set('model_id', model)
    if (date) params.set('date', date)
    if (source) params.set('source_sha256', source)
    if (query) params.set('q', query)
    try {
      const [runData, summaryData] = await Promise.all([api<Run[]>(`/runs?${params}`), api<Summary>('/dashboard/summary')])
      setRuns(runData); setSummary(summaryData); setError('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to load runs') }
    finally { setLoading(false) }
  }, [status, mode, modality, model, date, source, query, page, sort])
  useEffect(() => {
    const initial = setTimeout(() => void refresh(), 0)
    const timer = setInterval(() => void refresh(), 3000)
    return () => { clearTimeout(initial); clearInterval(timer) }
  }, [refresh])
  const visible = runs
  return <main className="workspace">
    <div className="page-heading"><div><p className="eyebrow">IMAGING OPERATIONS</p><h1>Review worklist</h1><p>Monitor real workflow history and prioritize drafts requiring action.</p></div><button className="button primary" onClick={() => setShowNew(true)}>New synthetic run</button></div>
    <div className="summary-grid six">
      <div className="summary-card"><span>Actionable</span><strong>{summary?.actionable ?? 0}</strong><small>Doctor/operator action required</small></div>
      <div className="summary-card"><span>Active execution</span><strong>{summary?.active_workers ?? 0}</strong><small>One-worker inference</small></div>
      <div className="summary-card"><span>Queue depth</span><strong>{summary?.queue_depth ?? 0}</strong><small>Bounded work queue</small></div>
      <div className="summary-card"><span>Failures</span><strong>{summary?.failures ?? 0}</strong><small>Preparation/model/service</small></div>
      <div className="summary-card"><span>Exports / cancelled</span><strong>{summary?.completed_exports ?? 0} / {summary?.cancelled ?? 0}</strong><small>Completed and stopped runs</small></div>
      <div className="summary-card"><span>Environment</span><strong className="environment-value">{summary?.inference_mode ?? '—'}</strong><small>{summary?.omlx_reachable ? 'oMLX reachable' : 'oMLX unavailable'} · {summary?.omlx_checked_at ? new Date(summary.omlx_checked_at).toLocaleTimeString() : '—'}</small></div>
    </div>
    {summary?.mock_label && <div className="mock-banner">{summary.mock_label}</div>}
    <section className="panel worklist-panel">
      <div className="filter-grid"><label>Status<select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}>{statuses.map((value) => <option key={value} value={value}>{value ? value.replaceAll('_', ' ').toLowerCase() : 'All statuses'}</option>)}</select></label><label>Inference<select value={mode} onChange={(e) => { setMode(e.target.value); setPage(1) }}><option value="">REAL + MOCK</option><option value="REAL">REAL</option><option value="MOCK">MOCK / FAULT</option></select></label><label>Modality<select value={modality} onChange={(e) => { setModality(e.target.value); setPage(1) }}><option value="">All supported</option><option value="XR">XR</option><option value="DX">DX</option><option value="CR">CR</option></select></label><label>Model<select value={model} onChange={(e) => { setModel(e.target.value); setPage(1) }}><option value="">All models</option><option value="MedMO-8B-Next">MedMO-8B-Next</option><option value="Qwen3.5-9B-MLX-4bit">Qwen3.5-9B-MLX-4bit</option></select></label><label>Date<input type="date" value={date} onChange={(e) => { setDate(e.target.value); setPage(1) }} /></label><label>Sort<select value={sort} onChange={(e) => setSort(e.target.value)}><option value="updated_desc">Newest first</option><option value="updated_asc">Oldest first</option></select></label></div>
      <div className="worklist-tools"><div className="status-distribution">{Object.entries(summary?.counts ?? {}).sort(([, a], [, b]) => b - a).map(([name, count]) => <span key={name}>{name.replaceAll('_', ' ')} <strong>{count}</strong></span>)}</div><div className="worklist-search"><label className="search-field"><span className="sr-only">Search by run ID</span><input placeholder="Search opaque run ID…" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1) }} /></label><label className="search-field"><span className="sr-only">Filter by source SHA-256</span><input placeholder="Source SHA-256…" value={source} onChange={(e) => { setSource(e.target.value.trim()); setPage(1) }} /></label></div></div>
      <div className="model-strip"><span>Vision: <strong>{summary?.vision_model_id ?? '—'}</strong></span><span>Text: <strong>{summary?.text_model_id ?? '—'}</strong></span><span>Worker heartbeat: <strong>{summary?.worker_heartbeat ? new Date(summary.worker_heartbeat).toLocaleString() : '—'}</strong></span><span>Synthetic/de-identified demonstrations</span></div>
      {error && <div className="form-error" role="alert">{error}<button className="text-button" onClick={() => void refresh()}>Retry</button></div>}
      {loading ? <div className="empty-state"><span className="spinner" />Loading worklist…</div> : visible.length === 0 ? <div className="empty-state"><h3>No runs in this view</h3><p>Start a synthetic demonstration or change the current filters.</p></div> : <><div className="table-wrap"><table><thead><tr><th>Run ID</th><th>Status</th><th>Mode</th><th>Attempt / revision</th><th>Updated</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>{visible.map((run) => <tr key={run.run_id}><td><code>{run.run_id}</code></td><td><StatusBadge status={run.status} /></td><td><span className={`mode-badge ${run.fault_profile && run.fault_profile !== 'none' ? 'mock' : run.inference_mode.toLowerCase()}`}>{run.fault_profile && run.fault_profile !== 'none' ? 'FAULT' : run.inference_mode}</span></td><td>{run.attempt} / {run.revision}</td><td>{run.snapshot_updated_at ? new Date(run.snapshot_updated_at).toLocaleTimeString() : '—'}</td><td><Link className="row-action" to={`/runs/${run.run_id}`}>Open <span aria-hidden="true">→</span></Link></td></tr>)}</tbody></table></div><RunCards runs={visible} /></>}
      <div className="pagination"><button className="button subtle" disabled={page === 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>Previous</button><span>Page {page} · {visible.length} shown</span><button className="button subtle" disabled={visible.length < pageSize} onClick={() => setPage((value) => value + 1)}>Next</button></div>
    </section>
    {showNew && <NewRun onClose={() => setShowNew(false)} onCreated={(runId) => { setShowNew(false); window.location.href = `/runs/${runId}` }} />}
  </main>
}
