import React from 'react'

function statusFor(tool, run) {
  const res = (run.results || []).find((r) => r.tool === tool)
  if (res) return res.ok ? 'success' : 'error'
  return run.status === 'running' ? 'running' : 'pending'
}

function color(status) {
  switch (status) {
    case 'success':
      return '#d1fae5' // green-100
    case 'error':
      return '#fee2e2' // red-100
    case 'running':
      return '#dbeafe' // blue-100
    default:
      return '#f3f4f6' // gray-100
  }
}

function badge(status) {
  switch (status) {
    case 'success':
      return '✓'
    case 'error':
      return '✕'
    case 'running':
      return '…'
    default:
      return '•'
  }
}

export default function Graph({ run }) {
  const nodes = (run.tools || []).map((t) => {
    const st = statusFor(t, run)
    const res = (run.results || []).find((r) => r.tool === t)
    const subtitle = res
      ? `${res.ok ? 'OK' : 'NG'} ${res.duration_ms ?? '-'}ms${res.score != null ? ` • score ${res.score}` : ''}`
      : run.status === 'running' ? 'running' : 'pending'
    return { tool: t, status: st, subtitle }
  })

  return (
    <div>
      <h3>グラフ（簡易）</h3>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ padding: '6px 8px', background: '#e5e7eb', borderRadius: 8 }}>Input</div>
        <span style={{ color: '#9ca3af' }}>→ fan-out →</span>
        {nodes.map((n) => (
          <div key={n.tool} style={{ padding: 8, borderRadius: 8, background: color(n.status), minWidth: 140 }}>
            <div style={{ fontWeight: 600 }}>
              {badge(n.status)} {n.tool}
            </div>
            <div style={{ fontSize: 12, color: '#374151' }}>{n.subtitle}</div>
          </div>
        ))}
        <span style={{ color: '#9ca3af' }}>→ fan-in →</span>
        <div style={{ padding: '6px 8px', background: color(run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'running'), borderRadius: 8 }}>
          {run.best_tool ? `Best: ${run.best_tool} (score ${run.best_score ?? '-'})` : 'Merge/Compare'}
        </div>
      </div>
    </div>
  )
}
