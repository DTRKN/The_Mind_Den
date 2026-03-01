import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Reminders from './pages/Reminders'
import History from './pages/History'
import Skills from './pages/Skills'

export default function App() {
  return (
    <div className="flex min-h-screen bg-[#0d0d14]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/reminders" element={<Reminders />} />
          <Route path="/history" element={<History />} />
          <Route path="/skills" element={<Skills />} />
        </Routes>
      </main>
    </div>
  )
}
