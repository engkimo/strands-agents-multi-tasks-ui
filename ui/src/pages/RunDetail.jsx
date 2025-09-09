import React, { useEffect, useState } from 'react'
import { getRun, streamRun, createRun, packagePR, adoptBest } from '../api.js'
import DiffView from '../components/DiffView.jsx'
import GraphFlow from '../components/GraphFlow.jsx'

export default function RunDetail({ runId }) {
  const [run, setRun] = useState(null)
  const [status, setStatus] = useState('loading')
  const [leftTool, setLeftTool] = useState('')
  const [rightTool, setRightTool] = useState('')
  const [actionMsg, setActionMsg] = useState('')
  const [prPreview, setPrPreview] = useState(null)
  const [liveLogs, setLiveLogs] = useState({}) // {tool: string}

  async function refresh() {
    const data = await getRun(runId)
    setRun(data)
    setStatus(data.status)
  }

  useEffect(() => {
    let es
    refresh()
      .then(() => {
        es = streamRun(runId, (evt) => {
          if (evt.data) {
            if (evt.type === 'log') {
              setLiveLogs((prev) => {
                const t = evt.data.tool
                const s = (prev[t] || '') + evt.data.text
                return { ...prev, [t]: s }
              })
            } else {
              setRun(evt.data)
              setStatus(evt.data.status)
            }
          }
        })
      })
    return () => {
      if (es) es.close()
    }
  }, [runId])

  if (!run) return <div>読み込み中…</div>

  // デフォルトの比較対象（OKな出力が2つ以上あれば最初の2つ）
  const okResults = (run.results || []).filter((r) => r.ok && (r.stdout ?? '').length > 0)
  const byTool = new Map((run.results || []).map((r) => [r.tool, r]))
  if (!leftTool || !rightTool) {
    if (okResults.length >= 2) {
      if (!leftTool) setLeftTool(okResults[0].tool)
      if (!rightTool) setRightTool(okResults[1].tool)
    } else if ((run.results || []).length >= 2) {
      if (!leftTool) setLeftTool(run.results[0].tool)
      if (!rightTool) setRightTool(run.results[1].tool)
    }
  }

  return (
    <div>
      <h2>Run {run.id}</h2>
      <div>状態: <b>{status}</b></div>
      <div>作成: {new Date(run.created_at).toLocaleString()}</div>
      <div>ツール: {run.tools.join(', ')}</div>
      {run.best_tool && (
        <div style={{ marginTop: 4 }}>ベスト: <b>{run.best_tool}</b>（score {run.best_score ?? '-'}）</div>
      )}
      <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button
          disabled={status === 'running'}
          onClick={async () => {
            setActionMsg('再実行中…')
            try {
              const newRun = await createRun({ prompt: run.prompt, tools: run.tools })
              window.location.hash = `#/runs/${newRun.id}`
            } catch (e) {
              setActionMsg(String(e))
            } finally {
              setTimeout(() => setActionMsg(''), 1500)
            }
          }}
        >再実行（全ツール）</button>
        <button
          disabled={status === 'running' || (run.results || []).filter((r) => r.ok === false).length === 0}
          onClick={async () => {
            const failed = (run.results || []).filter((r) => r.ok === false).map((r) => r.tool)
            if (failed.length === 0) return
            setActionMsg('再実行中…')
            try {
              const newRun = await createRun({ prompt: run.prompt, tools: failed })
              window.location.hash = `#/runs/${newRun.id}`
            } catch (e) {
              setActionMsg(String(e))
            } finally {
              setTimeout(() => setActionMsg(''), 1500)
            }
          }}
        >再実行（失敗のみ）</button>
        {actionMsg && <span style={{ color: '#6b7280' }}>{actionMsg}</span>}
      </div>

      <section style={{ marginTop: 16 }}>
        <GraphFlow run={run} liveLogs={liveLogs} />
      </section>

      <section style={{ marginTop: 16 }}>
        <h3>結果</h3>
        {run.results?.length ? (
          <div>
            {run.results.map((res) => (
              <details key={res.tool} style={{ marginBottom: 8 }} open>
                <summary>
                  <b>{res.tool}</b>{' '}
                  <StatusLabel res={res} />{' '}
                  — {res.duration_ms ?? '-'}ms {res.score != null ? `— score ${res.score}` : ''}
                </summary>
                <div style={{ display: 'flex', gap: 8 }}>
                  <pre style={{ flex: 1, background: res.ok ? '#f7f7f7' : '#fff5f5', padding: 8, overflowX: 'auto' }}>{res.stdout || ''}</pre>
                  {res.stderr && (
                    <pre style={{ flex: 1, background: '#fff5f5', padding: 8, overflowX: 'auto' }}>{res.stderr}</pre>
                  )}
                </div>
                <div style={{ marginTop: 6 }}>
                  <button
                    disabled={status === 'running'}
                    onClick={async () => {
                      setActionMsg('再実行中…')
                      try {
                        const newRun = await createRun({ prompt: run.prompt, tools: [res.tool] })
                        window.location.hash = `#/runs/${newRun.id}`
                      } catch (e) {
                        setActionMsg(String(e))
                      } finally {
                        setTimeout(() => setActionMsg(''), 1500)
                      }
                    }}
                  >このツールだけ再実行</button>
                  <button
                    style={{ marginLeft: 8 }}
                    disabled={status === 'running'}
                    onClick={async () => {
                      setActionMsg('採用中…')
                      try {
                        const updated = await adoptBest(run.id, res.tool)
                        setRun(updated)
                        setStatus(updated.status)
                        setActionMsg('採用しました')
                      } catch (e) {
                        setActionMsg(String(e))
                      } finally {
                        setTimeout(() => setActionMsg(''), 1500)
                      }
                    }}
                  >この結果を採用</button>
                </div>
              </details>
            ))}
          </div>
        ) : (
          <div>結果待ち…</div>
        )}
      </section>

      <section style={{ marginTop: 16 }}>
        <h3>差分ビュー</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
          <label>
            左: {' '}
            <select value={leftTool} onChange={(e) => setLeftTool(e.target.value)}>
              {(run.results || []).map((r) => (
                <option key={r.tool} value={r.tool}>{r.tool}</option>
              ))}
            </select>
          </label>
          <label>
            右: {' '}
            <select value={rightTool} onChange={(e) => setRightTool(e.target.value)}>
              {(run.results || []).map((r) => (
                <option key={r.tool} value={r.tool}>{r.tool}</option>
              ))}
            </select>
          </label>
        </div>
        <DiffView
          left={byTool.get(leftTool)}
          right={byTool.get(rightTool)}
          results={run.results || []}
        />
        <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
          <button
            disabled={status === 'running'}
            onClick={async () => {
              setActionMsg('PRパッケージ作成中…')
              try {
                const resp = await packagePR(run.id, { tool: leftTool, title: `Demo PR: ${run.prompt.slice(0, 40)}...` })
                setPrPreview(resp)
                setActionMsg('PRパッケージを作成しました')
              } catch (e) {
                setActionMsg(String(e))
              } finally {
                setTimeout(() => setActionMsg(''), 2000)
              }
            }}
          >PRパッケージ作成（左を採用）</button>
        </div>
        {prPreview && (
          <div style={{ marginTop: 12, border: '1px solid #e5e7eb', padding: 8, borderRadius: 6 }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>PRパッケージ（ローカル保存: {prPreview.dir}）</div>
            <details open>
              <summary>summary.md</summary>
              <pre style={{ whiteSpace: 'pre-wrap' }}>{prPreview.content?.summary_md || ''}</pre>
            </details>
            <details style={{ marginTop: 6 }}>
              <summary>review.md</summary>
              <pre style={{ whiteSpace: 'pre-wrap' }}>{prPreview.content?.review_md || ''}</pre>
            </details>
            {prPreview.content?.patch_text && (
              <details style={{ marginTop: 6 }}>
                <summary>patch.txt</summary>
                <pre style={{ whiteSpace: 'pre-wrap' }}>{prPreview.content?.patch_text || ''}</pre>
              </details>
            )}
          </div>
        )}
      </section>
    </div>
  )
}

function StatusLabel({ res }) {
  const txt = classify(res)
  const style = (() => {
    if (res.ok) return { background: '#dcfce7', color: '#166534' }
    if (txt.includes('timeout')) return { background: '#fff7ed', color: '#9a3412' }
    return { background: '#fee2e2', color: '#991b1b' }
  })()
  return (
    <span style={{ padding: '2px 6px', borderRadius: 4, fontSize: 12, ...style }}>{txt}</span>
  )
}

function classify(res) {
  if (res.ok) return 'OK'
  const stderr = (res.stderr || '').toLowerCase()
  if (stderr.includes('timeout')) return 'NG (timeout)'
  if (stderr.includes('command not found') || stderr.includes('not found')) return 'NG (not found)'
  if (res.exit_code != null) return `NG (exit ${res.exit_code})`
  return 'NG (error)'
}
