import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import type { Run } from './types'

export type ConnectionState = 'LIVE' | 'RECONNECTING' | 'OFFLINE'
export type DurableEvent = {
  sequence: number
  event_id: string
  run_id?: string
  thread_id?: string
  job_id?: string
  run_sequence?: number
  event_type: string
  run_status: string
  node_name?: string
  attempt: number
  revision: number
  model_call_sequence?: number
  timestamp_utc: string
  duration_ms?: number
  workflow_version: string
  inference_mode: string
  payload: Record<string, any> & { snapshot?: Run }
}
export type StreamEvent = DurableEvent | { event_type: 'snapshot' | 'resync'; payload: Record<string, any>; sequence?: number }

export function useEventStream(path: string, onEvent: (event: StreamEvent) => void, enabled = true) {
  const [connection, setConnection] = useState<ConnectionState>('RECONNECTING')
  const [lastPacketAt, setLastPacketAt] = useState<number | null>(null)
  const handler = useRef(onEvent)
  handler.current = onEvent

  useEffect(() => {
    if (!enabled) return
    let source: EventSource | null = null
    let fallback: ReturnType<typeof setInterval> | null = null
    const receive = (type: string, data: string, sequence?: number) => {
      const parsed = JSON.parse(data)
      if (type === 'session-expired') {
        setConnection('OFFLINE')
        window.dispatchEvent(new Event('nt:session-expired'))
        source?.close()
        return
      }
      setLastPacketAt(Date.now())
      setConnection('LIVE')
      if (type === 'snapshot' || type === 'resync') {
        handler.current({ event_type: type, payload: parsed, sequence })
      } else {
        handler.current({ ...parsed, event_type: type, sequence: sequence ?? parsed.sequence } as StreamEvent)
      }
    }
    if (typeof EventSource === 'undefined') {
      setConnection('OFFLINE')
      const poll = async () => {
        try {
          if (path === '/api/events') {
            const runs = await api<Run[]>('/runs')
            handler.current({ event_type: 'snapshot', payload: { runs, last_sequence: 0 } })
          } else {
            const runId = path.split('/')[3]
            const result = await api<{ run: Run; events: DurableEvent[] }>(`/runs/${runId}/events`)
            handler.current({ event_type: 'snapshot', payload: { run: result.run, last_sequence: 0 } })
            result.events.forEach((event) => handler.current(event))
          }
        } catch { /* bounded fallback remains offline */ }
      }
      void poll()
      fallback = setInterval(() => void poll(), 10_000)
    } else {
      source = new EventSource(path)
      source.onopen = () => setConnection('RECONNECTING')
      source.onerror = () => setConnection('RECONNECTING')
      source.onmessage = (message) => receive(message.type || 'message', message.data, message.lastEventId ? Number(message.lastEventId) : undefined)
      const types = ['snapshot', 'resync', 'RUN_CREATED', 'RUN_QUEUED', 'RUN_STARTED', 'NODE_STARTED', 'NODE_PROGRESS', 'NODE_COMPLETED', 'NODE_FAILED', 'GATE_RESULT', 'PREPARATION_STARTED', 'PREPARATION_OPERATION_COMPLETED', 'PREPARATION_COMPLETED', 'DERIVED_SAFETY_RESULT', 'MODEL_CALL_STARTED', 'MODEL_CALL_COMPLETED', 'MODEL_CALL_FAILED', 'ATTEMPT_STARTED', 'ATTEMPT_EXHAUSTED', 'REVISION_REQUESTED', 'REVISION_STARTED', 'REVISION_COMPLETED', 'HUMAN_APPROVAL_REQUIRED', 'HUMAN_DECISION_RECORDED', 'EXPORT_STARTED', 'EXPORT_COMPLETED', 'RUN_CANCELLED', 'RUN_FAILED', 'RUN_COMPLETED', 'WORKER_HEARTBEAT', 'WORKER_STARTED', 'WORKER_STOPPED', 'TECHNICAL_RETRY_REQUESTED', 'heartbeat', 'session-expired']
      types.forEach((type) => source!.addEventListener(type, (event) => receive(type, (event as MessageEvent).data, (event as MessageEvent).lastEventId ? Number((event as MessageEvent).lastEventId) : undefined)))
    }
    return () => {
      source?.close()
      if (fallback) clearInterval(fallback)
    }
  }, [path, enabled])

  useEffect(() => {
    const timer = setInterval(() => {
      if (!lastPacketAt) return
      const age = Date.now() - lastPacketAt
      if (age > 35_000) setConnection('OFFLINE')
      else if (age > 12_000) setConnection('RECONNECTING')
    }, 5_000)
    return () => clearInterval(timer)
  }, [lastPacketAt])

  return { connection, lastPacketAt }
}
