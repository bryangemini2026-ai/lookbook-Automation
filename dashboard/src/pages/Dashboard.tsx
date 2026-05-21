import { useState, useEffect } from 'react'
import {
  Activity, Cpu, Clock, Users, TrendingUp, CheckCircle,
  AlertCircle, Image, Video, Film
} from 'lucide-react'
import StatusIndicator from '../components/StatusIndicator'
import ProgressBar from '../components/ProgressBar'
import CircularProgress from '../components/CircularProgress'
import {
  getGPUStatus, getQueueStatus, getPipelineStatus,
  getDashboardStats, getRecentActivity, getAgents,
  type GPUStatus, type QueueStatus, type PipelineStatus,
  type DashboardStats, type RecentActivity, type AgentInfo
} from '../lib/api'

export default function Dashboard() {
  const [gpu, setGpu] = useState<GPUStatus | null>(null)
  const [queue, setQueue] = useState<QueueStatus | null>(null)
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activity, setActivity] = useState<RecentActivity[]>([])
  const [agents, setAgents] = useState<AgentInfo[]>([])

  useEffect(() => {
    const fetchData = async () => {
      const [gpuRes, queueRes, pipelineRes, statsRes, activityRes, agentsRes] =
        await Promise.all([
          getGPUStatus(),
          getQueueStatus(),
          getPipelineStatus(),
          getDashboardStats(),
          getRecentActivity(),
          getAgents(),
        ])

      setGpu(gpuRes.data)
      setQueue(queueRes.data)
      setPipeline(pipelineRes.data)
      setStats(statsRes.data)
      setActivity(activityRes.data)
      setAgents(agentsRes.data)
    }

    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
        return 'green'
      case 'processing':
        return 'blue'
      case 'pending':
        return 'yellow'
      case 'error':
        return 'red'
      default:
        return 'blue'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <Image size={16} />
      case 'video':
        return <Video size={16} />
      case 'reel':
        return <Film size={16} />
      default:
        return <Activity size={16} />
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Status Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* GPU Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Cpu size={18} style={{ color: 'var(--color-accent-blue)' }} />
              <h3 className="text-sm font-semibold">GPU Status</h3>
            </div>
            {gpu && (
              <StatusIndicator
                status={gpu.status}
                size="sm"
                showLabel={false}
              />
            )}
          </div>
          {gpu && (
            <div className="flex items-center gap-4">
              <CircularProgress
                value={gpu.usage}
                size={64}
                strokeWidth={4}
                color={gpu.usage > 80 ? 'red' : gpu.usage > 50 ? 'yellow' : 'green'}
              />
              <div className="flex-1">
                <div className="text-2xl font-bold">{gpu.usage}%</div>
                <div className="text-small" style={{ color: 'var(--color-text-muted)' }}>
                  {gpu.temperature}°C · {gpu.server === 'image' ? 'Image Server' : 'Video Server'}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Queue Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity size={18} style={{ color: 'var(--color-accent-green)' }} />
              <h3 className="text-sm font-semibold">Queue Status</h3>
            </div>
            {queue && (
              <StatusIndicator
                status={queue.processing > 0 ? 'processing' : 'idle'}
                size="sm"
                showLabel={false}
              />
            )}
          </div>
          {queue && (
            <div className="space-y-3">
              <div className="flex justify-between text-small">
                <span style={{ color: 'var(--color-text-muted)' }}>Pending</span>
                <span className="font-mono">{queue.pending}</span>
              </div>
              <div className="flex justify-between text-small">
                <span style={{ color: 'var(--color-text-muted)' }}>Processing</span>
                <span className="font-mono" style={{ color: 'var(--color-accent-blue)' }}>
                  {queue.processing}
                </span>
              </div>
              <div className="flex justify-between text-small">
                <span style={{ color: 'var(--color-text-muted)' }}>Completed Today</span>
                <span className="font-mono" style={{ color: 'var(--color-accent-green)' }}>
                  {queue.completed}
                </span>
              </div>
              <ProgressBar
                value={queue.completed}
                max={queue.total}
                showPercentage={false}
                size="sm"
                color="green"
              />
            </div>
          )}
        </div>

        {/* Pipeline Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Clock size={18} style={{ color: 'var(--color-accent-yellow)' }} />
              <h3 className="text-sm font-semibold">Pipeline Status</h3>
            </div>
            {pipeline && (
              <StatusIndicator
                status={pipeline.currentStage === 'idle' ? 'idle' : 'processing'}
                size="sm"
                showLabel={false}
              />
            )}
          </div>
          {pipeline && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-small" style={{ color: 'var(--color-text-muted)' }}>
                  Active Job:
                </span>
                <span className="text-small font-medium truncate">
                  {pipeline.activeJob || 'None'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-small" style={{ color: 'var(--color-text-muted)' }}>
                  Time:
                </span>
                <span className="font-mono text-small">
                  {formatTime(pipeline.timeElapsed)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {pipeline.stages.map((stage, index) => (
                  <div
                    key={stage.name}
                    className="flex items-center gap-1"
                  >
                    <div
                      className={`w-2 h-2 rounded-full ${
                        stage.status === 'completed'
                          ? 'bg-[var(--color-accent-green)]'
                          : stage.status === 'active'
                          ? 'bg-[var(--color-accent-blue)] animate-pulse'
                          : 'bg-[var(--color-surface-3)]'
                      }`}
                    />
                    <span
                      className="text-[10px]"
                      style={{
                        color:
                          stage.status === 'active'
                            ? 'var(--color-text-primary)'
                            : 'var(--color-text-muted)',
                      }}
                    >
                      {stage.name}
                    </span>
                    {index < pipeline.stages.length - 1 && (
                      <div className="w-4 h-px" style={{ background: 'var(--color-surface-3)' }} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp size={16} style={{ color: 'var(--color-accent-blue)' }} />
              <span className="text-small" style={{ color: 'var(--color-text-muted)' }}>
                Total Jobs
              </span>
            </div>
            <div className="text-2xl font-bold">{stats.totalJobs.toLocaleString()}</div>
          </div>
          <div className="card">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle size={16} style={{ color: 'var(--color-accent-green)' }} />
              <span className="text-small" style={{ color: 'var(--color-text-muted)' }}>
                Success Rate
              </span>
            </div>
            <div className="text-2xl font-bold" style={{ color: 'var(--color-accent-green)' }}>
              {stats.successRate}%
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-2 mb-2">
              <Clock size={16} style={{ color: 'var(--color-accent-yellow)' }} />
              <span className="text-small" style={{ color: 'var(--color-text-muted)' }}>
                Avg Time
              </span>
            </div>
            <div className="text-2xl font-bold">{stats.avgGenerationTime}s</div>
          </div>
          <div className="card">
            <div className="flex items-center gap-2 mb-2">
              <Users size={16} style={{ color: 'var(--color-accent-purple)' }} />
              <span className="text-small" style={{ color: 'var(--color-text-muted)' }}>
                Active Agents
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold">{stats.activeAgents}</div>
              <StatusIndicator status="active" size="sm" showLabel={false} />
            </div>
          </div>
        </div>
      )}

      {/* Activity Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Recent Activity */}
        <div className="card md:col-span-2">
          <h3 className="text-sm font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {activity.map((item) => (
              <div
                key={item.id}
                className="flex items-center gap-3 p-3 rounded-lg transition-colors"
                style={{ background: 'var(--color-surface-2)' }}
              >
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: 'var(--color-surface-3)' }}
                >
                  {getTypeIcon(item.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-small font-medium truncate">{item.jobName}</div>
                  <div className="text-caption" style={{ color: 'var(--color-text-muted)' }}>
                    {item.timestamp}
                  </div>
                </div>
                <StatusIndicator
                  status={item.status}
                  size="sm"
                  showLabel={false}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Agent Status */}
        <div className="card">
          <h3 className="text-sm font-semibold mb-4">Agent Status</h3>
          <div className="space-y-3">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="flex items-center gap-3 p-3 rounded-lg transition-colors"
                style={{ background: 'var(--color-surface-2)' }}
              >
                <StatusIndicator
                  status={agent.status}
                  size="sm"
                  showLabel={false}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-small font-medium">{agent.name}</div>
                  <div className="text-caption" style={{ color: 'var(--color-text-muted)' }}>
                    {agent.role}
                  </div>
                </div>
                <div className="text-caption" style={{ color: 'var(--color-text-muted)' }}>
                  {agent.lastActive}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
