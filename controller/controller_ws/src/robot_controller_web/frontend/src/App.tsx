import { ModePanel } from './components/ModePanel'
import { JoystickPanel } from './components/JoystickPanel'
import './App.css'

export default function App() {
  return (
    <main className="app">
      <h1 className="app-title">Robot Controller</h1>
      <ModePanel />
      <JoystickPanel />
    </main>
  )
}
