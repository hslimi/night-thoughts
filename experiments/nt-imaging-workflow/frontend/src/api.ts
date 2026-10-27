import type { Decision } from './types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function csrf(): string {
  return document.cookie.split('; ').find((part) => part.startsWith('__Host-nt_csrf='))?.split('=')[1] ?? ''
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.method && options.method !== 'GET') headers.set('X-CSRF-Token', csrf())
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const response = await fetch(`/api/v1${path}`, { ...options, headers, credentials: 'same-origin' })
  if (!response.ok) {
    if (response.status === 401 && !['/auth/login', '/auth/me'].includes(path)) window.dispatchEvent(new Event('nt:session-expired'))
    let message = 'The request could not be completed'
    try {
      const body = await response.json()
      message = body.error?.message ?? message
    } catch { /* response has no JSON error body */ }
    throw new ApiError(response.status, message)
  }
  return response.json() as Promise<T>
}

export const login = (username: string, password: string) => api<{ username: string; csrf_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
export const logout = () => api<{ status: string }>('/auth/logout', { method: 'POST' })
export const decide = (runId: string, decision: Decision, note: string) => api<{ run_id: string; status: string }>(`/runs/${runId}/decision`, { method: 'POST', body: JSON.stringify({ decision, note }) })
