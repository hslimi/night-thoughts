import { Link } from 'react-router-dom'
import type { Run } from '../types'
import StatusBadge from './StatusBadge'

export default function RunCards({ runs }: { runs: Run[] }) {
  return <div className="run-cards">{runs.map((run) => <article className="run-card" key={run.run_id}><div className="run-card-heading"><StatusBadge status={run.status} /><span className={`mode-badge ${run.fault_profile && run.fault_profile !== 'none' ? 'mock' : run.inference_mode.toLowerCase()}`}>{run.fault_profile && run.fault_profile !== 'none' ? 'FAULT' : run.inference_mode}</span></div><code>{run.run_id}</code><dl><div><dt>Required action</dt><dd>{run.status === 'AWAITING_HUMAN_APPROVAL' ? 'Doctor review' : ['FAILED', 'NEEDS_HUMAN_REVIEW', 'IMAGE_PREPARATION_FAILED', 'MODEL_OUTPUT_INVALID'].includes(run.status) ? 'Operator review' : 'None'}</dd></div><div><dt>Attempt</dt><dd>{run.attempt}</dd></div><div><dt>Revision</dt><dd>{run.revision}</dd></div><div><dt>Updated</dt><dd>{run.snapshot_updated_at ? new Date(run.snapshot_updated_at).toLocaleString() : '—'}</dd></div></dl><Link className="button secondary full" to={`/runs/${run.run_id}`}>Open run <span aria-hidden="true">→</span></Link></article>)}</div>
}
