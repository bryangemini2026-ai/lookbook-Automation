import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Image, List, Users, Sparkles, Settings } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Generate from './pages/Generate'
import Queue from './pages/Queue'
import Agents from './pages/Agents'
import Skills from './pages/Skills'
import SettingsPage from './pages/Settings'

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/generate', label: 'Generate', icon: Image },
  { path: '/queue', label: 'Queue', icon: List },
  { path: '/agents', label: 'Agents', icon: Users },
  { path: '/skills', label: 'Skills', icon: Sparkles },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function App() {
  const location = useLocation()

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-bold">Lookbook AI</h1>
          <p className="text-xs text-gray-500">SNS Automation</p>
        </div>
        <nav className="flex-1 p-2">
          {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg mb-1 transition-colors ${
                location.pathname === path
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'hover:bg-gray-800 text-gray-400'
              }`}
            >
              <Icon size={18} />
              <span className="text-sm">{label}</span>
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/generate" element={<Generate />} />
          <Route path="/queue" element={<Queue />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  )
}
