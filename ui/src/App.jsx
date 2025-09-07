import React, { useEffect, useState } from 'react'
import Runs from './pages/Runs.jsx'
import RunDetail from './pages/RunDetail.jsx'

function useHashRoute() {
  const [route, setRoute] = useState(() => window.location.hash.slice(1) || '/runs')
  useEffect(() => {
    const onChange = () => setRoute(window.location.hash.slice(1) || '/runs')
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return [route, setRoute]
}

export default function App() {
  const [route] = useHashRoute()
  let el
  if (route.startsWith('/runs/')) {
    const id = route.split('/')[2]
    el = <RunDetail runId={id} />
  } else {
    el = <Runs />
  }
  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', padding: 16 }}>
      <h1>Strands Agents Multi‑Tasks UI</h1>
      <nav style={{ marginBottom: 12 }}>
        <a href="#/runs">Runs</a>
      </nav>
      {el}
    </div>
  )
}

