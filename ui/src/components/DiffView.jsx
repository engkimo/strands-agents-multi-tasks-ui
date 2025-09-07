import React, { useMemo, useState } from 'react'

// 1行内の単純差分をハイライト（共通prefix/suffixを保持し、中間を<mark>）
function highlightLineDiff(l = '', r = '') {
  if (l === r) {
    return {
      left: [<span key="l">{l}</span>],
      right: [<span key="r">{r}</span>],
      changed: false,
    }
  }
  let i = 0
  while (i < l.length && i < r.length && l[i] === r[i]) i++
  let j = 0
  while (
    j < l.length - i &&
    j < r.length - i &&
    l[l.length - 1 - j] === r[r.length - 1 - j]
  )
    j++

  const lpre = l.slice(0, i)
  const lmid = l.slice(i, l.length - j)
  const lpost = l.slice(l.length - j)
  const rpre = r.slice(0, i)
  const rmid = r.slice(i, r.length - j)
  const rpost = r.slice(r.length - j)
  return {
    left: [
      <span key="pre">{lpre}</span>,
      <mark key="mid" style={{ background: '#ffd9d0' }}>{lmid}</mark>,
      <span key="post">{lpost}</span>,
    ],
    right: [
      <span key="pre">{rpre}</span>,
      <mark key="mid" style={{ background: '#c8f7d2' }}>{rmid}</mark>,
      <span key="post">{rpost}</span>,
    ],
    changed: true,
  }
}

function normalize(s, { ignoreCase }) {
  if (!s) return ''
  return ignoreCase ? s.toLowerCase() : s
}

function wordDiffParts(aLine, bLine, opts) {
  const aRaw = (aLine || '').trim()
  const bRaw = (bLine || '').trim()
  const a = normalize(aRaw, opts)
  const b = normalize(bRaw, opts)
  const aTokensRaw = aRaw.length ? aRaw.split(/\s+/) : []
  const bTokensRaw = bRaw.length ? bRaw.split(/\s+/) : []
  const aTokens = a.length ? a.split(/\s+/) : []
  const bTokens = b.length ? b.split(/\s+/) : []

  const m = aTokens.length, n = bTokens.length
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0))
  for (let i = m - 1; i >= 0; i--) {
    for (let j = n - 1; j >= 0; j--) {
      if (aTokens[i] === bTokens[j]) dp[i][j] = dp[i + 1][j + 1] + 1
      else dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }
  const aOut = []
  const bOut = []
  let i = 0, j = 0
  while (i < m && j < n) {
    if (aTokens[i] === bTokens[j]) {
      aOut.push(<span key={`a-${i}-${j}`}>{aTokensRaw[i]}</span>)
      bOut.push(<span key={`b-${i}-${j}`}>{bTokensRaw[j]}</span>)
      i++; j++
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      aOut.push(<mark key={`a-del-${i}-${j}`} style={{ background: '#ffd9d0' }}>{aTokensRaw[i]}</mark>)
      i++
    } else {
      bOut.push(<mark key={`b-add-${i}-${j}`} style={{ background: '#c8f7d2' }}>{bTokensRaw[j]}</mark>)
      j++
    }
  }
  while (i < m) {
    aOut.push(<mark key={`a-del-${i}-${j}`} style={{ background: '#ffd9d0' }}>{aTokensRaw[i]}</mark>)
    i++
  }
  while (j < n) {
    bOut.push(<mark key={`b-add-${i}-${j}`} style={{ background: '#c8f7d2' }}>{bTokensRaw[j]}</mark>)
    j++
  }
  const left = []
  for (let k = 0; k < aOut.length; k++) {
    left.push(aOut[k])
    if (k !== aOut.length - 1) left.push(<span key={`as-${k}`}> </span>)
  }
  const right = []
  for (let k = 0; k < bOut.length; k++) {
    right.push(bOut[k])
    if (k !== bOut.length - 1) right.push(<span key={`bs-${k}`}> </span>)
  }
  const changed = a !== b
  return { left, right, changed }
}

function renderMarkdown(md) {
  if (!md) return ''
  let s = md.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  s = s.replace(/```([\s\S]*?)```/g, (m, p1) => `<pre><code>${p1.replace(/&/g, '&amp;')}</code></pre>`)
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>')
  s = s.replace(/^######\s*(.+)$/gm, '<h6>$1</h6>')
  s = s.replace(/^#####\s*(.+)$/gm, '<h5>$1</h5>')
  s = s.replace(/^####\s*(.+)$/gm, '<h4>$1</h4>')
  s = s.replace(/^###\s*(.+)$/gm, '<h3>$1</h3>')
  s = s.replace(/^##\s*(.+)$/gm, '<h2>$1</h2>')
  s = s.replace(/^#\s*(.+)$/gm, '<h1>$1</h1>')
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/\*(.+?)\*/g, '<em>$1</em>')
  s = s.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>')
  s = s.replace(/\n\n+/g, '</p><p>')
  s = `<p>${s}</p>`
  return s
}

// 任意の2出力を比較。props:
// - left, right: 個別のNodeResult（任意）
// - results: NodeResult[]（left/right未指定なら先頭2件のOKを比較）
export default function DiffView({ left, right, results }) {
  let a = left
  let b = right
  if (!a || !b) {
    const oks = results?.filter((r) => r.ok && (r.stdout ?? '').length > 0) || []
    if (oks.length < 2) return <div>差分表示には2つ以上の出力が必要です。</div>
    a = oks[0]
    b = oks[1]
  }
  const [mode, setMode] = useState('line')
  const [ignoreWs, setIgnoreWs] = useState(false)
  const [ignoreCase, setIgnoreCase] = useState(false)
  const [renderMode, setRenderMode] = useState('text')

  const leftLines = useMemo(() => (a.stdout || '').split('\n'), [a.stdout])
  const rightLines = useMemo(() => (b.stdout || '').split('\n'), [b.stdout])
  const max = Math.max(leftLines.length, rightLines.length)
  const opts = { ignoreCase }
  const rows = []
  for (let i = 0; i < max; i++) {
    let l = leftLines[i] ?? ''
    let r = rightLines[i] ?? ''
    const equalAfterNorm = (() => {
      let ln = l
      let rn = r
      if (ignoreWs) {
        ln = ln.replace(/\s+/g, ' ').trim()
        rn = rn.replace(/\s+/g, ' ').trim()
      }
      if (ignoreCase) {
        ln = ln.toLowerCase(); rn = rn.toLowerCase()
      }
      return ln === rn
    })()
    let lparts, rparts, changed
    if (mode === 'word' && !equalAfterNorm) {
      ;({ left: lparts, right: rparts, changed } = wordDiffParts(l, r, opts))
    } else {
      ;({ left: lparts, right: rparts, changed } = highlightLineDiff(l, r))
      if (!changed && !equalAfterNorm) changed = true
    }
    rows.push(
      <tr key={i} style={{ background: changed ? '#fffbe6' : 'transparent' }}>
        <td style={{ whiteSpace: 'pre-wrap', width: '50%' }}>{lparts}</td>
        <td style={{ whiteSpace: 'pre-wrap', width: '50%' }}>{rparts}</td>
      </tr>
    )
  }
  return (
    <div>
      <h3>差分（{a.tool} vs {b.tool}）</h3>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
        <label>
          粒度:
          <select value={mode} onChange={(e) => setMode(e.target.value)} style={{ marginLeft: 6 }}>
            <option value="line">行</option>
            <option value="word">単語</option>
          </select>
        </label>
        <label>
          <input type="checkbox" checked={ignoreWs} onChange={(e) => setIgnoreWs(e.target.checked)} /> 空白無視
        </label>
        <label>
          <input type="checkbox" checked={ignoreCase} onChange={(e) => setIgnoreCase(e.target.checked)} /> 大小無視
        </label>
        <label>
          表示:
          <select value={renderMode} onChange={(e) => setRenderMode(e.target.value)} style={{ marginLeft: 6 }}>
            <option value="text">テキスト</option>
            <option value="markdown">Markdown</option>
          </select>
        </label>
        <button onClick={() => navigator.clipboard?.writeText(a.stdout || '')}>左をコピー</button>
        <button onClick={() => navigator.clipboard?.writeText(b.stdout || '')}>右をコピー</button>
      </div>
      <table border="1" cellPadding="6" style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>{a.tool}</th>
            <th>{b.tool}</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      {renderMode === 'markdown' && (
        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>{a.tool}（Markdown表示）</div>
            <div className="md-render" dangerouslySetInnerHTML={{ __html: renderMarkdown(a.stdout || '') }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>{b.tool}（Markdown表示）</div>
            <div className="md-render" dangerouslySetInnerHTML={{ __html: renderMarkdown(b.stdout || '') }} />
          </div>
        </div>
      )}
    </div>
  )
}
