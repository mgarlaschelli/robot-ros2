import { useEffect, useRef, useState } from 'react'
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp } from 'lucide-react'
import { createJoystickSocket, type JoystickSocket } from '../api/client'
import './JoystickPanel.css'

interface Vec {
  lx: number
  az: number
}

const ZERO: Vec = { lx: 0, az: 0 }

// ROS convention: linear.x positive = forward, angular.z positive = left
const DIRECTIONS: { key: string; icon: React.ReactNode; vec: Vec; gridArea: string }[] = [
  { key: 'up',    icon: <ArrowUp    size={22} />, vec: { lx: 1,  az: 0  }, gridArea: 'up' },
  { key: 'down',  icon: <ArrowDown  size={22} />, vec: { lx: -1, az: 0  }, gridArea: 'down' },
  { key: 'left',  icon: <ArrowLeft  size={22} />, vec: { lx: 0,  az: 1  }, gridArea: 'left' },
  { key: 'right', icon: <ArrowRight size={22} />, vec: { lx: 0,  az: -1 }, gridArea: 'right' },
]

const DOT_RANGE = 36 // max pixel offset for joystick dot

export function JoystickPanel() {
  const socketRef = useRef<JoystickSocket | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [cmd, setCmd] = useState<Vec>(ZERO)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    socketRef.current = createJoystickSocket(() => setConnected(true))
    return () => {
      stopCommand()
      socketRef.current?.close()
    }
  }, [])

  function startCommand(vec: Vec) {
    setCmd(vec)
    socketRef.current?.send(vec.lx, vec.az)
    intervalRef.current = setInterval(() => {
      socketRef.current?.send(vec.lx, vec.az)
    }, 50) // 20 Hz
  }

  function stopCommand() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setCmd(ZERO)
    socketRef.current?.send(0, 0)
  }

  // Map cmd to pixel offset: forward = up, left = left
  const dotX = -cmd.az * DOT_RANGE
  const dotY = -cmd.lx * DOT_RANGE

  return (
    <section className="panel joystick-panel">
      <div className="panel-header">
        <span className="panel-label">Manual Control</span>
        <span className={`conn-badge ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? 'Connected' : 'Connecting...'}
        </span>
      </div>

      <div className="joystick-layout">
        {/* Visual joystick */}
        <div className="joystick-visual">
          <div className="joystick-pad">
            <div
              className="joystick-dot"
              style={{ transform: `translate(${dotX}px, ${dotY}px)` }}
            />
          </div>
        </div>

        {/* Arrow buttons */}
        <div className="arrow-grid">
          {DIRECTIONS.map(({ key, icon, vec, gridArea }) => (
            <button
              key={key}
              className={`arrow-btn ${cmd === vec ? 'active' : ''}`}
              style={{ gridArea }}
              onMouseDown={() => startCommand(vec)}
              onMouseUp={stopCommand}
              onMouseLeave={stopCommand}
              onTouchStart={(e) => { e.preventDefault(); startCommand(vec) }}
              onTouchEnd={stopCommand}
            >
              {icon}
            </button>
          ))}
          <div className="arrow-center" style={{ gridArea: 'center' }} />
        </div>
      </div>
    </section>
  )
}
