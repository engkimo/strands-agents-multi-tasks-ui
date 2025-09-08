import React, { useMemo, useState } from 'react'
import ReactFlow, { Background, Controls } from 'reactflow'
import 'reactflow/dist/style.css'

function statusColor(status) {
  switch (status) {
    case 'success':
      return '#16a34a'
    case 'error':
      return '#dc2626'
    case 'running':
      return '#2563eb'
    default:
      return '#6b7280'
  }
}

function nodeStatusFor(tool, run) {
  const res = (run.results || []).find((r) => r.tool === tool)
  if (!res) return run.status === 'running' ? 'running' : 'pending'
  return res.ok ? 'success' : 'error'
}

function nodeLabel(tool, run) {
  const res = (run.results || []).find((r) => r.tool === tool)
  if (!res) return `${tool} · pending`
  const dur = res.duration_ms != null ? `${res.duration_ms}ms` : '-'
  const score = res.score != null ? ` · s ${res.score}` : ''
  return `${tool} · ${res.ok ? 'OK' : 'NG'} · ${dur}${score}`
}

export default function GraphFlow({ run, liveLogs = {} }) {
  const [hover, setHover] = useState(null) // {tool, x, y}

  const layout = useMemo(() => {
    const tools = run.tools || []
    const spacingY = 110
    const startY = -((tools.length - 1) * spacingY) / 2
    const nodes = []
    const edges = []
    nodes.push({ id: 'in', position: { x: 0, y: 0 }, data: { label: 'Input' }, style: { background: '#e5e7eb', padding: 8, borderRadius: 8 } })
    tools.forEach((t, i) => {
      const status = nodeStatusFor(t, run)
      const y = startY + i * spacingY
      nodes.push({
        id: `tool-${t}`,
        position: { x: 320, y },
        data: { label: nodeLabel(t, run) },
        style: { padding: 8, borderLeft: `8px solid ${statusColor(status)}`, borderRadius: 8, background: '#fff' },
      })
      edges.push({ id: `e-in-${t}`, source: 'in', target: `tool-${t}` })
      edges.push({ id: `e-${t}-merge`, source: `tool-${t}`, target: 'merge' })
    })
    nodes.push({ id: 'merge', position: { x: 640, y: 0 }, data: { label: run.best_tool ? `Best: ${run.best_tool} · s ${run.best_score ?? '-'}` : 'Merge/Compare' }, style: { background: '#e5e7eb', padding: 8, borderRadius: 8 } })
    return { nodes, edges }
  }, [run])

  const resultsByTool = useMemo(() => {
    const m = new Map()
    ;(run.results || []).forEach((r) => m.set(r.tool, r))
    return m
  }, [run])

  const onNodeMouseEnter = (_, node) => {
    if (!node.id.startsWith('tool-')) return
    const tool = node.id.replace('tool-', '')
    setHover({ tool })
  }
  const onNodeMouseLeave = () => setHover(null)

  const hoverRes = hover ? resultsByTool.get(hover.tool) : null
  const liveText = hover ? (liveLogs[hover.tool] || '') : ''
  const finalText = hoverRes ? (hoverRes.stdout || '') : ''
  const hoverText = (liveText + finalText) ? (liveText + finalText).slice(0, 2000) : (run.status === 'running' ? '実行中…' : '未開始')

  return (
    <div style={{ height: 360, border: '1px solid #e5e7eb', borderRadius: 8 }}>
      <ReactFlow
        nodes={layout.nodes}
        edges={layout.edges}
        fitView
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>
      {hover && (
        <div style={{ marginTop: 8, padding: 8, background: '#f9fafb', borderTop: '1px solid #e5e7eb', height: 120, overflow: 'auto' }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>{hover.tool} のログ（抜粋）</div>
          <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{hoverText}</pre>
        </div>
      )}
    </div>
  )
}
