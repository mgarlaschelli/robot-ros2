import { useEffect, useRef, useState } from 'react'
import { Gamepad2, Loader2, PauseCircle, Radar } from 'lucide-react'
import { createModeSocket, getMode, setMode, type Mode } from '../api/client'
import './ModePanel.css'

const MODES: Mode[] = ['STAND_BY', 'PATROL', 'MANUAL']

const MODE_LABELS: Record<Mode, string> = {
  STAND_BY: 'Stand By',
  PATROL: 'Patrol',
  MANUAL: 'Manual',
}

const MODE_ICONS: Record<Mode, React.ReactNode> = {
  STAND_BY: <PauseCircle size={18} />,
  PATROL:   <Radar size={18} />,
  MANUAL:   <Gamepad2 size={18} />,
}

const MODE_COLORS: Record<Mode, string> = {
  STAND_BY: 'mode-standby',
  PATROL: 'mode-patrol',
  MANUAL: 'mode-manual',
}

export function ModePanel() {
  const [current, setCurrent] = useState<string>('...')
  const [loading, setLoading] = useState<Mode | null>(null)
  const [error, setError] = useState<string | null>(null)
  const errorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    // Fetch the current mode immediately (robot may not re-publish on connect)
    getMode().then(setCurrent)
    const cleanup = createModeSocket(setCurrent)
    return cleanup
  }, [])

  function showError(msg: string) {
    setError(msg)
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
    errorTimerRef.current = setTimeout(() => setError(null), 4000)
  }

  async function handleClick(mode: Mode) {
    if (loading) return
    setError(null)
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
    setLoading(mode)
    try {
      await setMode(mode)
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Failed to set mode')
    } finally {
      setLoading(null)
    }
  }

  return (
    <section className="panel mode-panel">
      <div className="panel-header">
        <span className="panel-label">Operating Mode</span>
        <span className={`mode-badge ${MODES.includes(current as Mode) ? MODE_COLORS[current as Mode] : ''}`}>
          {current}
        </span>
      </div>

      <div className="mode-buttons">
        {MODES.map((mode) => (
          <button
            key={mode}
            className={`mode-btn ${MODE_COLORS[mode]} ${current === mode ? 'active' : ''}`}
            disabled={loading !== null}
            onClick={() => handleClick(mode)}
          >
            {loading === mode
            ? <Loader2 size={18} className="spin" />
            : MODE_ICONS[mode]}
          {loading === mode ? 'Loading…' : MODE_LABELS[mode]}
          </button>
        ))}
      </div>

      {error && <p className="error-msg">{error}</p>}
    </section>
  )
}
