export type Mode = 'STAND_BY' | 'PATROL' | 'MANUAL'

export async function getMode(): Promise<string> {
  const res = await fetch('/api/mode')
  if (!res.ok) return 'UNKNOWN'
  const data = await res.json() as { mode: string }
  return data.mode
}

export async function setMode(mode: Mode): Promise<void> {
  const res = await fetch('/api/mode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  })
  if (!res.ok) {
    let message = 'Request failed'
    try {
      const body = await res.json() as { detail?: string }
      if (body.detail) message = body.detail
    } catch { /* JSON parse failed, keep default */ }
    throw new Error(message)
  }
}

export interface JoystickSocket {
  send: (linearX: number, angularZ: number) => void
  close: () => void
}

export function createJoystickSocket(onOpen?: () => void): JoystickSocket {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${location.host}/ws/joystick`)
  ws.onopen = () => onOpen?.()
  return {
    send(linearX, angularZ) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ linear_x: linearX, angular_z: angularZ }))
      }
    },
    close() {
      ws.close()
    },
  }
}

export function createModeSocket(onMode: (mode: string) => void): () => void {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${location.host}/ws/mode`)
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data) as { mode?: string }
    if (data.mode) onMode(data.mode)
  }
  return () => ws.close()
}
