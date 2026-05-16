import { useState, useEffect } from 'react'
import { listAgents, getAgent, type Agent } from '../lib/api'
import { Users, Wrench, ChevronRight, Plus, Pencil, Trash2, X, Save } from 'lucide-react'
import { api } from '../lib/api'

const EMPTY_AGENT: AgentForm = {
  id: '', name: '', role: '', emoji: '🤖', color: '#6366f1',
  specialty: '', tagline: '', persona: '', tools: [], status: 'active',
}

interface AgentForm {
  id: string
  name: string
  role: string
  emoji: string
  color: string
  specialty: string
  tagline: string
  persona: string
  tools: string[]
  status: string
}

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selected, setSelected] = useState<Agent | null>(null)
  const [editing, setEditing] = useState<AgentForm | null>(null)
  const [isNew, setIsNew] = useState(false)
  const [toolInput, setToolInput] = useState('')

  const refresh = () => {
    listAgents().then(({ data }) => {
      setAgents(data)
      if (selected) {
        const updated = data.find((a: Agent) => a.id === selected.id)
        if (updated) setSelected(updated)
        else setSelected(null)
      }
    })
  }

  useEffect(() => { refresh() }, [])

  const selectAgent = async (id: string) => {
    const { data } = await getAgent(id)
    setSelected(data)
    setEditing(null)
    setIsNew(false)
  }

  const startNew = () => {
    setIsNew(true)
    setEditing({ ...EMPTY_AGENT })
    setSelected(null)
  }

  const startEdit = () => {
    if (!selected) return
    setIsNew(false)
    setEditing({ ...selected, tools: [...selected.tools] })
  }

  const cancelEdit = () => {
    setEditing(null)
    setIsNew(false)
  }

  const saveAgent = async () => {
    if (!editing || !editing.id || !editing.name || !editing.role) return
    try {
      if (isNew) {
        await api.post('/agents/', editing)
      } else {
        await api.put(`/agents/${editing.id}`, editing)
      }
      setEditing(null)
      setIsNew(false)
      refresh()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Save failed')
    }
  }

  const deleteAgent = async (id: string) => {
    if (!confirm(`Delete agent '${id}'?`)) return
    await api.delete(`/agents/${id}`)
    setSelected(null)
    refresh()
  }

  const addTool = () => {
    if (!editing || !toolInput.trim()) return
    if (!editing.tools.includes(toolInput.trim())) {
      setEditing({ ...editing, tools: [...editing.tools, toolInput.trim()] })
    }
    setToolInput('')
  }

  const removeTool = (tool: string) => {
    if (!editing) return
    setEditing({ ...editing, tools: editing.tools.filter(t => t !== tool) })
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users size={24} />
          <h2 className="text-2xl font-bold">Agent Team</h2>
          <span className="text-sm text-gray-500">({agents.length})</span>
        </div>
        <button
          onClick={startNew}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm"
        >
          <Plus size={16} />
          Add Agent
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent List */}
        <div className="lg:col-span-1 space-y-2">
          {agents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => selectAgent(agent.id)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                selected?.id === agent.id
                  ? 'border-blue-500 bg-blue-600/10'
                  : 'border-gray-800 bg-gray-900 hover:border-gray-700'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{agent.emoji}</span>
                <div className="flex-1 min-w-0">
                  <span className="font-semibold text-sm">{agent.name}</span>
                  <p className="text-xs text-gray-500 truncate">{agent.role}</p>
                </div>
                <ChevronRight size={14} className="text-gray-600" />
              </div>
            </button>
          ))}
        </div>

        {/* Detail / Edit Panel */}
        <div className="lg:col-span-2">
          {/* Edit Mode */}
          {editing ? (
            <div className="bg-gray-900 rounded-lg p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-lg">{isNew ? 'New Agent' : 'Edit Agent'}</h3>
                <button onClick={cancelEdit} className="p-1 hover:bg-gray-800 rounded">
                  <X size={18} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">ID (unique)</label>
                  <input value={editing.id} onChange={e => setEditing({...editing, id: e.target.value})}
                    disabled={!isNew}
                    className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm disabled:opacity-50" />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Name</label>
                  <input value={editing.name} onChange={e => setEditing({...editing, name: e.target.value})}
                    className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Role</label>
                  <input value={editing.role} onChange={e => setEditing({...editing, role: e.target.value})}
                    className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm" />
                </div>
                <div className="flex gap-3">
                  <div className="w-20">
                    <label className="text-xs text-gray-400 mb-1 block">Emoji</label>
                    <input value={editing.emoji} onChange={e => setEditing({...editing, emoji: e.target.value})}
                      className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm text-center" />
                  </div>
                  <div className="flex-1">
                    <label className="text-xs text-gray-400 mb-1 block">Color</label>
                    <div className="flex gap-2">
                      <input type="color" value={editing.color} onChange={e => setEditing({...editing, color: e.target.value})}
                        className="w-10 h-10 bg-gray-950 border border-gray-700 rounded cursor-pointer" />
                      <input value={editing.color} onChange={e => setEditing({...editing, color: e.target.value})}
                        className="flex-1 bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm font-mono" />
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-400 mb-1 block">Specialty</label>
                <input value={editing.specialty} onChange={e => setEditing({...editing, specialty: e.target.value})}
                  className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm" />
              </div>

              <div>
                <label className="text-xs text-gray-400 mb-1 block">Tagline</label>
                <input value={editing.tagline} onChange={e => setEditing({...editing, tagline: e.target.value})}
                  className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm" />
              </div>

              <div>
                <label className="text-xs text-gray-400 mb-1 block">Persona</label>
                <textarea value={editing.persona} onChange={e => setEditing({...editing, persona: e.target.value})}
                  rows={3}
                  className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm resize-none" />
              </div>

              {/* Tools */}
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Tools</label>
                <div className="flex flex-wrap gap-1 mb-2">
                  {editing.tools.map(tool => (
                    <span key={tool} className="flex items-center gap-1 px-2 py-1 bg-gray-800 rounded text-xs font-mono">
                      {tool}
                      <button onClick={() => removeTool(tool)} className="hover:text-red-400">
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input value={toolInput} onChange={e => setToolInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addTool())}
                    placeholder="tool_name"
                    className="flex-1 bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm font-mono" />
                  <button onClick={addTool} className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm">
                    Add
                  </button>
                </div>
              </div>

              {/* Status */}
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Status</label>
                <select value={editing.status} onChange={e => setEditing({...editing, status: e.target.value})}
                  className="bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm">
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              <div className="flex gap-2 pt-2">
                <button onClick={saveAgent}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold">
                  <Save size={16} />
                  {isNew ? 'Create' : 'Save'}
                </button>
                <button onClick={cancelEdit}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm">
                  Cancel
                </button>
              </div>
            </div>
          ) : selected ? (
            /* Detail View */
            <div className="bg-gray-900 rounded-lg p-6 space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-5xl">{selected.emoji}</span>
                  <div>
                    <h3 className="text-xl font-bold">{selected.name}</h3>
                    <p className="text-sm" style={{ color: selected.color }}>{selected.role}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={startEdit}
                    className="flex items-center gap-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm">
                    <Pencil size={14} />
                    Edit
                  </button>
                  <button onClick={() => deleteAgent(selected.id)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-red-800/50 hover:bg-red-700/50 rounded text-sm text-red-300">
                    <Trash2 size={14} />
                    Delete
                  </button>
                </div>
              </div>

              <p className="text-xs text-gray-500">{selected.specialty}</p>

              <div className="bg-gray-950 rounded-lg p-4">
                <p className="text-sm text-gray-300 italic">"{selected.tagline}"</p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Persona</h4>
                <p className="text-sm text-gray-300 bg-gray-950 rounded-lg p-4">{selected.persona}</p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider flex items-center gap-2">
                  <Wrench size={14} />
                  Tools ({selected.tools.length})
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {selected.tools.map((tool) => (
                    <div key={tool} className="flex items-center gap-2 px-3 py-2 bg-gray-950 rounded-lg border border-gray-800">
                      <div className="w-2 h-2 rounded-full bg-green-500" />
                      <span className="text-sm font-mono">{tool}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <span className={`px-2 py-0.5 rounded-full text-xs ${
                  selected.status === 'active' ? 'bg-green-600/20 text-green-400' : 'bg-gray-600/20 text-gray-400'
                }`}>
                  {selected.status}
                </span>
                <span className="text-xs text-gray-600 font-mono">{selected.id}</span>
              </div>
            </div>
          ) : (
            <div className="bg-gray-900 rounded-lg p-12 flex flex-col items-center justify-center gap-3">
              <Users size={40} className="text-gray-700" />
              <p className="text-gray-500">에이전트를 선택하거나 새 에이전트를 등록하세요</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
