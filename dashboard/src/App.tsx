import { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Image, List, Users, Sparkles, Settings,
  Play, ShoppingBag, Activity, ChevronRight, Zap
} from 'lucide-react'
import { getVersion, type SystemVersion } from './lib/api'
import Dashboard from './pages/Dashboard'

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, description: '시스템 현황' },
  { path: '/generate', label: 'Generate', icon: Image, description: '이미지 생성' },
  { path: '/pipeline', label: 'Pipeline', icon: Play, description: '파이프라인' },
  { path: '/crawling', label: 'Crawling', icon: ShoppingBag, description: '상품 수집' },
  { path: '/queue', label: 'Queue', icon: List, description: '작업 큐' },
  { path: '/agents', label: 'Agents', icon: Users, description: 'AI 에이전트' },
  { path: '/skills', label: 'Skills', icon: Sparkles, description: '스킬 관리' },
  { path: '/settings', label: 'Settings', icon: Settings, description: '시스템 설정' },
]

export default function App() {
  const location = useLocation()
  const [version, setVersion] = useState<SystemVersion | null>(null)
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    getVersion()
      .then(({ data }) => setVersion(data))
      .catch(() => {})
  }, [])

  const currentNav = NAV_ITEMS.find(item => item.path === location.pathname) || NAV_ITEMS[0]

  return (
    <div className="flex h-screen" style={{ background: 'var(--color-surface-0)', color: 'var(--color-text-primary)' }}>
      {/* Sidebar */}
      <aside
        className="flex flex-col border-r transition-all duration-300"
        style={{
          width: collapsed ? '72px' : '240px',
          background: 'var(--color-surface-1)',
          borderColor: 'var(--color-border-subtle)',
        }}
      >
        {/* Logo */}
        <div className="p-4 border-b flex items-center gap-3" style={{ borderColor: 'var(--color-border-subtle)' }}>
          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--color-accent-blue), var(--color-accent-purple))' }}>
            <Zap size={20} className="text-white" />
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <h1 className="font-bold text-sm" style={{ color: 'var(--color-text-primary)' }}>Lookbook AI</h1>
              <p className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>SNS Automation</p>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg transition-colors"
            style={{ color: 'var(--color-text-muted)' }}
          >
            <ChevronRight size={16} className={`transition-transform ${collapsed ? '' : 'rotate-180'}`} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 overflow-y-auto">
          <div className="space-y-1">
            {NAV_ITEMS.map(({ path, label, icon: Icon, description }) => {
              const isActive = location.pathname === path
              return (
                <Link
                  key={path}
                  to={path}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative"
                  style={{
                    background: isActive ? 'rgba(33, 150, 243, 0.1)' : 'transparent',
                    color: isActive ? 'var(--color-accent-blue)' : 'var(--color-text-secondary)',
                  }}
                  title={collapsed ? `${label} - ${description}` : undefined}
                >
                  {isActive && (
                    <div
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full"
                      style={{ background: 'var(--color-accent-blue)' }}
                    />
                  )}
                  <Icon size={20} className="flex-shrink-0" />
                  {!collapsed && (
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-medium block">{label}</span>
                      <span className="text-[11px] block" style={{ color: 'var(--color-text-muted)' }}>{description}</span>
                    </div>
                  )}
                  {!collapsed && isActive && (
                    <ChevronRight size={14} style={{ color: 'var(--color-accent-blue)' }} />
                  )}
                </Link>
              )
            })}
          </div>
        </nav>

        {/* Version Footer */}
        {version && (
          <div className="p-3 border-t" style={{ borderColor: 'var(--color-border-subtle)' }}>
            <div className="flex items-center gap-2">
              <div className="status-dot status-dot-active" />
              {!collapsed && (
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-mono" style={{ color: 'var(--color-text-secondary)' }}>{version.version}</span>
                  <p className="text-[10px] font-mono truncate" style={{ color: 'var(--color-text-muted)' }}>
                    {version.commit} · {version.branch}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {/* Top Bar */}
        <header
          className="sticky top-0 z-10 px-6 py-4 border-b backdrop-blur-sm"
          style={{
            background: 'rgba(0, 0, 0, 0.8)',
            borderColor: 'var(--color-border-subtle)',
          }}
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                {currentNav.label}
              </h2>
              <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                {currentNav.description}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: 'var(--color-surface-2)' }}>
                <Activity size={14} style={{ color: 'var(--color-accent-green)' }} />
                <span className="text-xs font-mono" style={{ color: 'var(--color-text-secondary)' }}>
                  {version?.version || '...'}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="animate-fade-in">
          <Routes>
            <Route path="/" element={<Dashboard />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
