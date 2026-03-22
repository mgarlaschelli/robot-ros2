import { useState } from 'react'
import { CameraOff } from 'lucide-react'
import './ModePanel.css'
import './JoystickPanel.css'
import './CameraPanel.css'

export function CameraPanel() {
  const [error, setError] = useState(false)

  return (
    <section className="panel camera-panel">
      <div className="panel-header">
        <span className="panel-label">Camera Feed</span>
        <span className={`conn-badge ${error ? 'disconnected' : 'connected'}`}>
          {error ? 'No Signal' : 'Live'}
        </span>
      </div>
      <div className="camera-viewport">
        {error ? (
          <div className="camera-error">
            <CameraOff size={40} />
            <span>Camera unavailable</span>
          </div>
        ) : (
          <img
            className="camera-feed"
            src="/api/camera/stream"
            alt="Robot camera feed"
            onError={() => setError(true)}
            onLoad={() => setError(false)}
          />
        )}
      </div>
    </section>
  )
}
