export type Decision = 'APPROVE' | 'REJECT' | 'REQUEST_CHANGES'
export type Run = {
  run_id: string
  thread_id: string
  status: string
  job_status?: string
  inference_mode: 'REAL' | 'MOCK'
  attempt: number
  revision: number
  model_calls: number
  max_attempts?: number
  max_total_model_calls?: number
  phi_status?: string
  modality_status?: string
  modality_source?: string
  contract_status?: string
  grounding_status?: string
  quality_status?: string
  current_node?: string
  sanitized_artifact_id?: string
  readiness_status?: string
  readiness_receipt_id?: string
  prepared_artifact_id?: string
  prepared_sha256?: string
  display_thumbnail_id?: string
  preparation_policy_version?: string
  preparation_operations?: string[]
  preparation_metrics?: Record<string, string | number | boolean>
  preparation_warnings?: string[]
  derived_phi_status?: string
  modality?: string
  source_format?: string
  fault_profile?: string | null
  demonstration_scenario?: string
  source_sha256?: string
  vision_model_id?: string
  text_model_id?: string
  prompt_version?: string
  policy_version?: string
  workflow_version?: string
  snapshot_updated_at?: string
  error?: { code: string; message: string; retryable: boolean } | null
  review_issues?: ReviewIssue[]
  human_decision?: { decision: Decision; reviewer_display_name: string; note: string; revision: number; timestamp: string } | null
  export_manifest?: ExportManifest | null
}
export type Finding = { label: string; status: string; anatomy?: string; description: string }
export type Draft = {
  technique: string
  comparison: string
  findings: Finding[]
  findings_text: string
  impression: string[]
  limitations: string[]
  draft_notice: string
}
export type ReviewIssue = { code: string; severity: string; message: string; stage: string; attempt?: number; revision?: number }
export type AuditEvent = { event_id: string; timestamp: string; node: string; event_type: string; attempt: number; reason_codes: string[]; event_hash: string }
export type ExportManifest = {
  created_at: string
  files: Record<string, string>
  hashes: Record<string, string>
  workflow_version: string
  prompt_version: string
  policy_version: string
  vision_model_id: string
  text_model_id: string
  source_sha256: string
  prepared_sha256: string
  readiness_receipt_id?: string
  preparation_policy_version?: string
  preparation_operations?: string[]
  preparation_metrics?: Record<string, string | number | boolean>
  preparation_warnings?: string[]
}
export type Summary = { counts: Record<string, number>; total: number; actionable: number; completed_exports: number; cancelled: number; failures: number; queue_depth: number; active_workers: number; worker_heartbeat?: string; omlx_reachable: boolean; omlx_checked_at: string; vision_model_id?: string; text_model_id?: string; inference_mode: string; mock_label?: string }
