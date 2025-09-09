import React, { useEffect, useState } from 'react'
import { listRuns, createRun, TOOL_OPTIONS, recommendTools } from '../api.js'

export default function Runs() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(false)
  const DEMO_PROMPT = '副業向けの新しい開発者ツールのアイデアを5つ'
  const [prompt, setPrompt] = useState(DEMO_PROMPT)
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

  const onDemoRun = async () => {
    setLoading(true)
    setError('')
    try {
      const run = await createRun({ prompt: DEMO_PROMPT, tools: TOOL_OPTIONS })
      window.location.hash = `#/runs/${run.id}`
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  const onRecommend = async () => {
    setLoading(true)
    setError('')
    try {
      const resp = await recommendTools(prompt)
      const set = new Set(resp.tools || [])
      if (set.size > 0) setTools(set)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <section style={{ marginBottom: 12 }}>
        <details>
          <summary style={{ cursor: 'pointer' }}>使い方（チュートリアル）</summary>
          <ol style={{ marginTop: 8 }}>
            <li>ツールを選び、プロンプトを入力して「実行」。</li>
            <li>Run詳細でグラフ（状態/時間）→ 各ノードのI/O/ログを確認。</li>
            <li>差分ビューで2出力を比較（行/単語・空白/大小無視・Markdown）。</li>
            <li>ベストを参考に「PRパッケージ作成（左を採用）」でsummary/review/patchを確認。</li>
          </ol>
        </details>
      </section>
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
            <button type="button" disabled={loading} onClick={onRecommend} style={{ marginLeft: 8 }}>推奨ツール選択</button>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button type="submit" disabled={loading || tools.size === 0}>実行</button>
            <button type="button" disabled={loading} onClick={onDemoRun}>デモ実行（3ツール一括）</button>
          </div>
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
              <th>ベスト</th>
              <th>ツール</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id}>
                <td><a href={`#/runs/${r.id}`}>{r.id.slice(0, 8)}…</a></td>
                <td>{r.status}</td>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td>{r.best_tool ? <span style={{ background:'#e0f2fe', padding:'2px 6px', borderRadius:4 }}>{r.best_tool}</span> : '-'}</td>
                <td>{r.tools.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
