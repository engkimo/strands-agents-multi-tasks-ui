const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function listRuns() {
  const res = await fetch(`${API_BASE}/runs`)
  if (!res.ok) throw new Error('failed to list runs')
  return await res.json()
}

export async function getRun(id) {
  const res = await fetch(`${API_BASE}/runs/${id}`)
  if (!res.ok) throw new Error('run not found')
  return await res.json()
}

export async function createRun({ prompt, tools }) {
  const res = await fetch(`${API_BASE}/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, tools }),
  })
  if (!res.ok) throw new Error('failed to create run')
  return await res.json()
}

export function streamRun(id, onEvent) {
  const url = `${API_BASE}/stream/runs/${id}`
  const es = new EventSource(url)
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      onEvent({ type: 'message', data })
    } catch (err) {
      // ignore
    }
  }
  es.addEventListener('status', (e) => {
    try {
      const data = JSON.parse(e.data)
      onEvent({ type: 'status', data })
    } catch {}
  })
  es.addEventListener('done', (e) => {
    try {
      const data = JSON.parse(e.data)
      onEvent({ type: 'done', data })
    } catch {}
  })
  es.addEventListener('node', (e) => {
    try {
      const data = JSON.parse(e.data)
      onEvent({ type: 'node', data })
    } catch {}
  })
  return es
}

export const TOOL_OPTIONS = [
  'claude_code',
  'codex_cli',
  'gemini_cli',
  'spec_kit',
]

export async function packagePR(id, { tool, title } = {}) {
  const res = await fetch(`${API_BASE}/runs/${id}/package_pr`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool, title }),
  })
  if (!res.ok) throw new Error('failed to package PR')
  return await res.json()
}
