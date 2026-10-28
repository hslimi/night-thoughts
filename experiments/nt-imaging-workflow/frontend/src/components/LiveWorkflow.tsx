import { useEffect, useMemo, useRef, useState } from 'react'
import type { ConnectionState, DurableEvent } from '../live'
import type { Run } from '../types'
import StatusBadge from './StatusBadge'

const nodes = ['ingest_validate', 'phi_screen', 'modality_gate', 'imaging_readiness', 'derived_image_safety_check', 'generate_draft', 'deterministic_contract_gate', 'visual_consistency_review', 'text_quality_review', 'human_approval', 'export_approved_draft']
const terminalStatuses = new Set(['QUARANTINED', 'NEEDS_HUMAN_REVIEW', 'IMAGE_PREPARATION_FAILED', 'MODEL_OUTPUT_INVALID', 'FAILED', 'HUMAN_REJECTED', 'CANCELLED'])

type NodeState = 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'FAILED' | 'SKIPPED' | 'WAITING_FOR_HUMAN'

function elapsed(started: string | undefined, now: number): string {
  if (!started) return '—'
  const seconds = Math.max(0, Math.floor((now - new Date(started).getTime()) / 1000))
  return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${seconds % 60}s`
}

export default function LiveWorkflow({ run, events, connection }: { run: Run; events: DurableEvent[]; connection: ConnectionState }) {
  const [now, setNow] = useState(Date.now())
  const [selectedNode, setSelectedNode] = useState('')
  const timeline = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [])
  const nodeStates = useMemo(() => {
    const states: Record<string, NodeState> = Object.fromEntries(nodes.map((node) => [node, 'PENDING']))
    let active = ''
    for (const event of events) {
      const node = event.node_name
      if (!node || !nodes.includes(node)) continue
      if (event.event_type === 'NODE_STARTED') {
        if (active && states[active] === 'ACTIVE') states[active] = 'COMPLETED'
        states[node] = 'ACTIVE'
        active = node
      } else if (event.event_type === 'NODE_COMPLETED') {
        states[node] = 'COMPLETED'
        if (active === node) active = ''
      } else if (event.event_type === 'NODE_FAILED') {
        states[node] = 'FAILED'
        if (active === node) active = ''
      } else if (event.event_type === 'HUMAN_APPROVAL_REQUIRED') {
        states[node] = 'WAITING_FOR_HUMAN'
        active = node
      } else if (event.event_type === 'EXPORT_COMPLETED') {
        states[node] = 'COMPLETED'
      }
    }
    if (run.status === 'APPROVED_DRAFT_EXPORTED') nodes.forEach((node) => { states[node] = 'COMPLETED' })
    else if (terminalStatuses.has(run.status)) {
      const currentIndex = nodes.indexOf(run.current_node ?? '')
      nodes.forEach((node, index) => {
        if (states[node] === 'PENDING' && currentIndex >= 0 && index > currentIndex) states[node] = 'SKIPPED'
        if (states[node] === 'ACTIVE' && node === run.current_node) states[node] = 'FAILED'
      })
    }
    return states
  }, [events, run.status, run.current_node])
  const activeEvent = [...events].reverse().find((event) => event.event_type === 'NODE_STARTED' && nodeStates[event.node_name ?? ''] === 'ACTIVE')
  const selectedEvents = selectedNode ? events.filter((event) => event.node_name === selectedNode) : events
  const attempts = useMemo(() => {
    const values = new Map<number, { started?: DurableEvent; result?: DurableEvent; exhausted?: DurableEvent }>()
    events.forEach((event) => {
      if (!['ATTEMPT_STARTED', 'ATTEMPT_EXHAUSTED', 'RUN_FAILED', 'RUN_COMPLETED'].includes(event.event_type)) return
      const current = values.get(event.attempt) ?? {}
      if (event.event_type === 'ATTEMPT_STARTED') current.started = event
      else if (event.event_type === 'ATTEMPT_EXHAUSTED') current.exhausted = event
      else current.result = event
      values.set(event.attempt, current)
    })
    return [...values.entries()]
  }, [events])
  const modelCalls = useMemo(() => {
    const values = new Map<number, { started?: DurableEvent; finished?: DurableEvent }>()
    events.forEach((event) => {
      const sequence = event.model_call_sequence
      if (!sequence) return
      const current = values.get(sequence) ?? {}
      if (event.event_type === 'MODEL_CALL_STARTED') current.started = event
      if (['MODEL_CALL_COMPLETED', 'MODEL_CALL_FAILED'].includes(event.event_type)) current.finished = event
      values.set(sequence, current)
    })
    return [...values.entries()]
  }, [events])
  const revisions = useMemo(() => events.filter((event) => event.event_type.startsWith('REVISION_')), [events])
  const currentDraft = run.draft ?? [...events].reverse().find((event) => event.payload.snapshot?.draft)?.payload.snapshot?.draft
  const previousDraft = [...events].reverse().find((event) => event.event_type === 'HUMAN_APPROVAL_REQUIRED' && event.revision === Math.max(0, run.revision - 1))?.payload.snapshot?.draft

  useEffect(() => {
    const element = timeline.current
    if (!element) return
    const atBottom = element.scrollHeight - element.scrollTop - element.clientHeight < 48
    if (atBottom) element.scrollTop = element.scrollHeight
  }, [events.length, selectedNode])

  return <section className="live-workflow">
    <div className="panel"><div className="panel-heading"><div><p className="eyebrow">LIVE WORKFLOW</p><h2>{activeEvent ? activeEvent.node_name?.replaceAll('_', ' ') : run.status.replaceAll('_', ' ')}</h2></div><div className="live-stage-meta"><span className={`live-badge ${connection.toLowerCase()}`}>{connection}</span><strong>{activeEvent ? elapsed(activeEvent.timestamp_utc, now) : 'No active stage'}</strong></div></div>
      <div className="workflow-graph" aria-label="Live LangGraph workflow">{nodes.map((node, index) => {
        const state = nodeStates[node]
        const completedEdge = index > 0 && nodeStates[nodes[index - 1]] === 'COMPLETED'
        return <div className="graph-segment" key={node}>{index > 0 && <span className={`graph-edge ${completedEdge ? 'complete' : ''}`} aria-hidden="true">→</span>}<button className={`graph-node ${state.toLowerCase()} ${activeEvent?.node_name === node ? 'active-node' : ''}`} onClick={() => setSelectedNode(selectedNode === node ? '' : node)} aria-pressed={selectedNode === node}><span className="node-state-dot" /><strong>{node.replaceAll('_', ' ')}</strong><small>{state.replaceAll('_', ' ')}</small></button>{['generate_draft', 'deterministic_contract_gate', 'visual_consistency_review', 'text_quality_review'].includes(node) && <span className="loop-label">bounded retry</span>}{node === 'human_approval' && <span className="loop-label">revision loop</span>}</div>
      })}</div>
      <div className="gate-grid">{[['PHI screening', run.phi_status], ['Modality', run.modality_status], ['Imaging readiness', run.readiness_status], ['Derived image safety', run.derived_phi_status], ['Deterministic contract', run.contract_status], ['Visual consistency', run.grounding_status], ['Text quality', run.quality_status], ['Human review', run.status === 'AWAITING_HUMAN_APPROVAL' ? 'PENDING' : run.human_decision ? 'DECIDED' : 'PENDING']].map(([label, status]) => <div className="gate-card" key={label}><span>{label}</span><StatusBadge status={status} /></div>)}</div>
    </div>
    <div className="live-detail-grid">
      <div className="panel"><div className="panel-heading"><h2>{selectedNode || 'Chronological live timeline'}</h2><span>{selectedEvents.length} events</span></div><div className="live-timeline" ref={timeline}>{selectedEvents.map((event) => <article className={`timeline-event ${event.event_type === 'NODE_FAILED' || event.event_type === 'MODEL_CALL_FAILED' ? 'failed' : ''}`} key={event.event_id}><span className="timeline-time">{new Date(event.timestamp_utc).toLocaleTimeString()}</span><div><strong>{event.event_type.replaceAll('_', ' ')}</strong><p>{event.node_name ?? 'application'} · attempt {event.attempt} · revision {event.revision}{event.duration_ms !== undefined ? ` · ${event.duration_ms} ms` : ''}</p>{event.payload.error && <code>{event.payload.error.code}</code>}</div></article>)}</div></div>
      <aside className="live-section-stack">
        <div className="panel"><h2>Attempts</h2>{attempts.length === 0 ? <p className="muted">No drafting attempt has started.</p> : attempts.map(([attempt, value]) => <div className="compact-record" key={attempt}><strong>Attempt {attempt}</strong><p>{value.started ? new Date(value.started.timestamp_utc).toLocaleTimeString() : '—'} · {value.exhausted ? 'EXHAUSTED' : value.result?.event_type ?? 'IN PROGRESS'}</p>{value.exhausted && <p>{value.exhausted.payload.error?.code}</p>}</div>)}</div>
        <div className="panel"><h2>Model calls <span className="muted">({run.model_calls} completed)</span></h2>{modelCalls.length === 0 ? <p className="muted">No inference calls yet.</p> : modelCalls.map(([sequence, value]) => <div className="compact-record" key={sequence}><strong>#{sequence} · {value.started?.payload.stage ?? 'MODEL'}</strong><p>{value.started?.payload.model_id ?? '—'}</p><p>{value.finished ? value.finished.event_type === 'MODEL_CALL_COMPLETED' ? 'COMPLETED' : 'FAILED' : `RUNNING · ${elapsed(value.started?.timestamp_utc, now)}`}{value.finished?.duration_ms !== undefined ? ` · ${value.finished.duration_ms} ms` : ''}</p>{value.finished?.payload.output_sha256 && <code>{value.finished.payload.output_sha256}</code>}{value.finished?.payload.error_category && <p>{value.finished.payload.error_category}</p>}</div>)}</div>
      </aside>
    </div>
    <div className="panel"><div className="panel-heading"><h2>Revisions and draft comparison</h2><span>{run.revision} / 2 revisions</span></div>{revisions.length === 0 ? <p className="muted">No doctor-requested revision yet.</p> : <div className="revision-markers">{revisions.map((event) => <span key={event.event_id}>{event.event_type.replaceAll('_', ' ')} · revision {event.revision}</span>)}</div>}{run.revision > 0 && <div className="draft-diff"><section><h3>Previous draft</h3><p>{previousDraft?.findings_text ?? 'Previous findings unavailable'}</p><h3>Previous impression</h3><p>{previousDraft?.impression?.join(' ') ?? '—'}</p></section><section><h3>Current draft</h3><p>{currentDraft?.findings_text ?? 'Current draft is being generated'}</p><h3>Current impression</h3><p>{currentDraft?.impression?.join(' ') ?? '—'}</p></section></div>}{revisions.filter((event) => event.event_type === 'REVISION_REQUESTED').map((event) => <blockquote key={event.event_id}>{event.payload.note}</blockquote>)}</div>
  </section>
}
