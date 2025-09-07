import React, { useEffect, useState } from 'react'
import { listRuns, createRun, TOOL_OPTIONS } from '../api.js'

export default function Runs() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(false)
  const [prompt, setPrompt] = useState('副業向けの新しい開発者ツールのアイデアを5つ')
  const [tools, setTools] = useState(new Set(TOOL_OPTIONS))
  const [error, setError] = useState('')

  async function refresh() {
    try {
      const data = await listRuns()
      setRuns(data)
    } catch (e) {
      setError(String(e))
    }
  }

  useEffect(() => { refresh() }, [])

  const toggleTool = (t) => {
    setTools((prev) => {
      const next = new Set(prev)
      if (next.has(t)) next.delete(t)
      else next.add(t)
      return next
    })
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = { prompt, tools: Array.from(tools) }
      const run = await createRun(payload)
      window.location.hash = `#/runs/${run.id}`
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <section style={{ marginBottom: 16 }}>
        <h2>新規実行</h2>
        <form onSubmit={onSubmit}>
          <div>
            <label>プロンプト</label>
            <br />
            <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={3} style={{ width: '100%' }} />
          </div>
          <div style={{ marginTop: 8 }}>
            {TOOL_OPTIONS.map((t) => (
              <label key={t} style={{ marginRight: 12 }}>
                <input type="checkbox" checked={tools.has(t)} onChange={() => toggleTool(t)} /> {t}
              </label>
            ))}
          </div>
          <button type="submit" disabled={loading || tools.size === 0} style={{ marginTop: 8 }}>実行</button>
          {error && <div style={{ color: 'crimson' }}>{error}</div>}
        </form>
      </section>

      <section>
        <h2>実行一覧</h2>
        <button onClick={refresh}>更新</button>
        <table border="1" cellPadding="6" style={{ marginTop: 8, width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>状態</th>
              <th>作成時刻</th>
              <th>ツール</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id}>
                <td><a href={`#/runs/${r.id}`}>{r.id.slice(0, 8)}…</a></td>
                <td>{r.status}</td>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td>{r.tools.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}

