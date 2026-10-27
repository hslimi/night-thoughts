import { useEffect, useState } from 'react'
import { api } from '../api'
import type { AuditEvent, Run } from '../types'

export type InspectorData = {
  current_node: string
  completed_nodes: string[]
  pending_nodes: string[]
  failed_edge?: { code: string; message: string } | null
  attempt: number
  revision: number
  node_events: AuditEvent[]
  model_calls: { stage: string; model_id: string; latency_ms: number; status: string; output_sha256?: string; created_at: string }[]
  observability: string
}

export default function GraphInspector({ run }: { run: Run }) {
  const [data, setData] = useState<InspectorData | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    api<InspectorData>(`/runs/${run.run_id}/graph-inspector`).then(setData).catch((reason) => setError(reason instanceof Error ? reason.message : 'Inspector unavailable'))
  }, [run.run_id])
  if (error) return <div className="form-error">{error}</div>
  if (!data) return <div className="empty-state panel"><span className="spinner" />Loading local graph inspector…</div>
  return <section className="inspector-layout"><div className="panel"><div className="panel-heading"><h2>Local graph inspector</h2><span>{data.observability}</span></div><dl className="metadata-grid"><dt>Current node</dt><dd><strong>{data.current_node}</strong></dd><dt>Attempt / revision</dt><dd>{data.attempt} / {data.revision}</dd><dt>Checkpoint thread</dt><dd><code>{run.thread_id}</code></dd><dt>Failed edge</dt><dd>{data.failed_edge?.code ?? 'None'}</dd></dl><div className="inspector-columns"><div><h3>Completed nodes</h3><ul>{data.completed_nodes.map((node) => <li key={node}>{node}</li>)}</ul></div><div><h3>Pending nodes</h3><ul>{data.pending_nodes.map((node) => <li key={node}>{node}</li>)}</ul></div></div><h3>Node events</h3><div className="audit-timeline">{data.node_events.map((event, index) => { const previous = index > 0 ? new Date(data.node_events[index - 1].timestamp).getTime() : null; const duration = previous ? `${new Date(event.timestamp).getTime() - previous} ms` : '—'; return <article className="audit-event" key={event.event_id}><span className="audit-node">{event.node}</span><div><h3>{event.event_type.replaceAll('_', ' ')}</h3><p>{new Date(event.timestamp).toLocaleString()} · +{duration}</p><code>{event.event_hash}</code></div></article>})}</div></div><aside className="panel"><h2>Model-call receipts</h2>{data.model_calls.length === 0 ? <p className="muted">No inference calls occurred.</p> : <div className="receipt-list">{data.model_calls.map((call, index) => <article className="receipt" key={index}><strong>{call.stage}</strong><p>{call.model_id}</p><p>{call.latency_ms} ms · {call.status}</p><p>{new Date(call.created_at).toLocaleString()}</p><code>{call.output_sha256}</code></article>)}</div>}<h3>Preparation</h3><dl className="metadata-grid"><dt>Status</dt><dd>{run.readiness_status}</dd><dt>Policy</dt><dd>{run.preparation_policy_version}</dd><dt>Receipt</dt><dd>{run.readiness_receipt_id ?? 'Legacy run'}</dd><dt>Warnings</dt><dd>{(run.preparation_warnings ?? []).join('; ') || 'None'}</dd></dl></aside></section>
}
