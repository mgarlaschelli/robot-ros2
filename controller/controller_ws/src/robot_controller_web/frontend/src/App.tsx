import { ModePanel } from './components/ModePanel'
import { CameraPanel } from './components/CameraPanel'
import { JoystickPanel } from './components/JoystickPanel'
import './App.css'

export default function App() {
  return (
    <main className="app">
      <h1 className="app-title">Robot Controller</h1>
      <div className="app-layout">
        <div className="app-left">
          <CameraPanel />
        </div>
        <div className="app-right">
          <ModePanel />
          <JoystickPanel />
        </div>
      </div>
    </main>
  )
}
