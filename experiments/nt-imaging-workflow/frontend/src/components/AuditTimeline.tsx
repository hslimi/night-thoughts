import { useEffect, useState } from 'react'
import { api } from '../api'
import type { AuditEvent, Run } from '../types'

export default function AuditTimeline({ run }: { run: Run }) {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [error, setError] = useState('')
  useEffect(() => {
    api<{ events: AuditEvent[] }>(`/runs/${run.run_id}/audit`).then((result) => setEvents(result.events)).catch((reason) => setError(reason instanceof Error ? reason.message : 'Audit unavailable'))
  }, [run.run_id])
  return <section className="audit-layout"><div className="panel"><h2>Chronological audit</h2>{error && <div className="form-error">{error}</div>}{events.length === 0 ? <p className="muted">No audit events are available for this run.</p> : <div className="audit-timeline">{events.map((event) => <article className="audit-event" key={event.event_id}><span className="audit-node">{event.node}</span><div><h3>{event.event_type.replaceAll('_', ' ')}</h3><p>{new Date(event.timestamp).toLocaleString()} · attempt {event.attempt}</p>{event.reason_codes.length > 0 && <p>{event.reason_codes.join(', ')}</p>}<code>{event.event_hash}</code></div></article>)}</div>}</div><aside className="panel"><h2>Provenance</h2><dl className="metadata-grid"><dt>Workflow</dt><dd>{run.workflow_version}</dd><dt>Prompt</dt><dd>{run.prompt_version}</dd><dt>Policy</dt><dd>{run.policy_version}</dd><dt>Vision model</dt><dd>{run.vision_model_id}</dd><dt>Text model</dt><dd>{run.text_model_id}</dd><dt>Input hash</dt><dd><code>{run.source_sha256}</code></dd><dt>Derived hash</dt><dd><code>{run.prepared_sha256}</code></dd></dl><p className="muted">Events form a tamper-evident demonstration chain, not an immutable ledger. No hidden model reasoning is stored or displayed.</p></aside></section>
}
