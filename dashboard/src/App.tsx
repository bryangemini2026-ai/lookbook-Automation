import { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Image, List, Users, Sparkles, Settings,
  Play, ShoppingBag, Activity
} from 'lucide-react'
import { getVersion, type SystemVersion } from './lib/api'
import Tooltip from './components/common/Tooltip'
import Dashboard from './pages/Dashboard'
import Generate from './pages/Generate'
import Queue from './pages/Queue'
import Agents from './pages/Agents'
import Skills from './pages/Skills'
import SettingsPage from './pages/Settings'
import Pipeline from './pages/Pipeline'
import Crawling from './pages/Crawling'

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, tooltip: '시스템 현황, GPU 상태, 큐 통계를 한눈에 확인합니다' },
  { path: '/generate', label: 'Generate', icon: Image, tooltip: '프롬프트를 입력하고 룩북 이미지를 생성합니다' },
  { path: '/pipeline', label: 'Pipeline', icon: Play, tooltip: '6단계 룩북 파이프라인을 실행하고 관리합니다' },
  { path: '/crawling', label: 'Crawling', icon: ShoppingBag, tooltip: '무신사/쿠팡 인기 상품을 수집하고 관리합니다' },
  { path: '/queue', label: 'Queue', icon: List, tooltip: '생성 작업 목록과 진행 상태를 확인합니다' },
  { path: '/agents', label: 'Agents', icon: Users, tooltip: 'AI 에이전트를 등록, 수정, 삭제합니다' },
  { path: '/skills', label: 'Skills', icon: Sparkles, tooltip: '자동 추출된 스킬과 도구 시드를 관리합니다' },
  { path: '/settings', label: 'Settings', icon: Settings, tooltip: 'GPU 서버 제어, API 키, 시스템 설정을 관리합니다' },
]

export default function App() {
  const location = useLocation()
  const [version, setVersion] = useState<SystemVersion | null>(null)

  useEffect(() => {
    getVersion()
      .then(({ data }) => setVersion(data))
      .catch(() => {})
  }, [])

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <Tooltip text="AI 기반 패션 룩북 자동 생성 시스템" position="right">
            <h1 className="text-lg font-bold cursor-default">Lookbook AI</h1>
          </Tooltip>
          <p className="text-xs text-gray-500">SNS Automation</p>
        </div>
        <nav className="flex-1 p-2 overflow-y-auto">
          {NAV_ITEMS.map(({ path, label, icon: Icon, tooltip }) => (
            <Tooltip key={path} text={tooltip} position="right">
              <Link
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
            </Tooltip>
          ))}
        </nav>

        {/* Version Footer */}
        {version && (
          <Tooltip
            text={`커밋: ${version.commit} | 브랜치: ${version.branch}`}
            position="right"
          >
            <div className="p-3 border-t border-gray-800 cursor-default">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-xs font-mono text-gray-400">{version.version}</span>
              </div>
              <p className="text-[10px] text-gray-600 font-mono mt-1">
                {version.commit} · {version.branch}
              </p>
            </div>
          </Tooltip>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/generate" element={<Generate />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/crawling" element={<Crawling />} />
          <Route path="/queue" element={<Queue />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  )
}
