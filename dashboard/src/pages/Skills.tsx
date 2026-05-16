import { useState, useEffect } from 'react'
import { listSkills, listToolSeeds, getDecisions, type Skill, type ToolSeed } from '../lib/api'
import { Sparkles, Wrench, BookOpen, FileText } from 'lucide-react'

type Tab = 'skills' | 'tools' | 'decisions'

export default function Skills() {
  const [tab, setTab] = useState<Tab>('tools')
  const [skills, setSkills] = useState<Skill[]>([])
  const [tools, setTools] = useState<ToolSeed[]>([])
  const [decisions, setDecisions] = useState('')

  useEffect(() => {
    listSkills().then(({ data }) => setSkills(data))
    listToolSeeds().then(({ data }) => setTools(data))
    getDecisions().then(({ data }) => setDecisions(data.content))
  }, [])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Sparkles size={24} />
        <h2 className="text-2xl font-bold">Skills & Tools</h2>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-800 pb-2">
        {[
          { id: 'tools' as Tab, label: 'Tool Seeds', icon: Wrench, count: tools.length },
          { id: 'skills' as Tab, label: 'Distilled Skills', icon: Sparkles, count: skills.length },
          { id: 'decisions' as Tab, label: 'Decision Log', icon: FileText },
        ].map(({ id, label, icon: Icon, count }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm transition-colors ${
              tab === id
                ? 'bg-gray-900 text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            <Icon size={14} />
            {label}
            {count !== undefined && (
              <span className="ml-1 px-1.5 py-0.5 bg-gray-800 rounded-full text-xs">{count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tool Seeds Tab */}
      {tab === 'tools' && (
        <div className="space-y-3">
          {tools.length === 0 ? (
            <div className="bg-gray-900 rounded-lg p-8 text-center">
              <Wrench size={32} className="mx-auto text-gray-600 mb-3" />
              <p className="text-gray-500">아직 등록된 Tool Seed가 없습니다</p>
              <p className="text-xs text-gray-600 mt-1">worker/tool-seeds/ 폴더에 .md + .py 파일을 추가하세요</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {tools.map((tool) => (
                <div key={`${tool.agent}-${tool.name}`} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-semibold font-mono text-sm">{tool.name}</h4>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-600/20 text-blue-400">
                        {tool.agent}
                      </span>
                    </div>
                    <div className="flex gap-1">
                      {tool.has_doc && (
                        <span className="text-xs px-1.5 py-0.5 bg-green-600/20 text-green-400 rounded">doc</span>
                      )}
                      {tool.has_code && (
                        <span className="text-xs px-1.5 py-0.5 bg-purple-600/20 text-purple-400 rounded">py</span>
                      )}
                    </div>
                  </div>
                  {tool.purpose && (
                    <p className="text-xs text-gray-400">{tool.purpose}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Distilled Skills Tab */}
      {tab === 'skills' && (
        <div className="space-y-3">
          {skills.length === 0 ? (
            <div className="bg-gray-900 rounded-lg p-8 text-center">
              <Sparkles size={32} className="mx-auto text-gray-600 mb-3" />
              <p className="text-gray-500">아직 추출된 스킬이 없습니다</p>
              <p className="text-xs text-gray-600 mt-1">작업이 완료되면 자동으로 패턴이 추출됩니다</p>
            </div>
          ) : (
            skills.map((skill) => (
              <div key={skill.name} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles size={14} className="text-yellow-400" />
                  <h4 className="font-semibold font-mono text-sm">{skill.name}</h4>
                  <span className="text-xs px-2 py-0.5 bg-yellow-600/20 text-yellow-400 rounded-full">{skill.type}</span>
                </div>
                {skill.description && (
                  <p className="text-xs text-gray-400">{skill.description}</p>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Decision Log Tab */}
      {tab === 'decisions' && (
        <div className="bg-gray-900 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen size={16} className="text-gray-400" />
            <h3 className="font-semibold text-sm text-gray-400">Decision Log</h3>
          </div>
          <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono bg-gray-950 rounded p-4 max-h-96 overflow-auto">
            {decisions || 'No decisions recorded yet.'}
          </pre>
        </div>
      )}
    </div>
  )
}
