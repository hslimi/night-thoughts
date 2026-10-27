export default function StatusBadge({ status }: { status?: string }) {
  const value = status ?? 'PENDING'
  const tone = value.includes('PASS') || value === 'APPROVED_DRAFT_EXPORTED' || value === 'CLEAR' || value === 'SUPPORTED' ? 'success' : value.includes('FAIL') || value === 'QUARANTINED' || value === 'CANCELLED' ? 'danger' : value.includes('REVIEW') || value.includes('QUEUED') || value === 'REVISION_REQUESTED' ? 'warning' : 'neutral'
  return <span className={`status-badge ${tone}`}><span className="status-dot" />{value.replaceAll('_', ' ')}</span>
}
