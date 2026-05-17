import { useState, useEffect } from 'react'
import { listJobs, cancelJob, retryJob, type Job } from '../lib/api'
import { RefreshCw, X, RotateCcw } from 'lucide-react'
import Tooltip from '../components/common/Tooltip'

const STATUS_COLORS: Record<string, string> = {
  pending: 'text-yellow-400 bg-yellow-400/10',
  running: 'text-blue-400 bg-blue-400/10',
  completed: 'text-green-400 bg-green-400/10',
  failed: 'text-red-400 bg-red-400/10',
  cancelled: 'text-gray-400 bg-gray-400/10',
}

const STATUS_TOOLTIPS: Record<string, string> = {
  pending: 'GPU에서 실행을 기다리고 있습니다',
  running: '현재 GPU에서 생성 중입니다',
  completed: '생성이 완료되었습니다',
  failed: '생성 중 오류가 발생했습니다',
  cancelled: '사용자가 취소한 작업입니다',
}

const FILTER_OPTIONS = [
  { value: undefined, label: '전체', tooltip: '모든 작업을 표시합니다' },
  { value: 'pending', label: '대기', tooltip: '실행 대기 중인 작업만 표시합니다' },
  { value: 'running', label: '실행 중', tooltip: '현재 실행 중인 작업만 표시합니다' },
  { value: 'completed', label: '완료', tooltip: '완료된 작업만 표시합니다' },
  { value: 'failed', label: '실패', tooltip: '실패한 작업만 표시합니다' },
]

export default function Queue() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [filter, setFilter] = useState<string | undefined>()

  const refresh = async () => {
    const { data } = await listJobs({ limit: 50, status: filter })
    setJobs(data)
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 3000)
    return () => clearInterval(interval)
  }, [filter])

  const handleCancel = async (id: string) => {
    await cancelJob(id)
    refresh()
  }

  const handleRetry = async (id: string) => {
    await retryJob(id)
    refresh()
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">작업 큐</h2>
        <Tooltip text="작업 목록을 새로고침합니다">
          <button onClick={refresh} className="p-2 hover:bg-gray-800 rounded-lg">
            <RefreshCw size={18} />
          </button>
        </Tooltip>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {FILTER_OPTIONS.map(({ value, label, tooltip }) => (
          <Tooltip key={value ?? 'all'} text={tooltip}>
            <button
              onClick={() => setFilter(value)}
              className={`px-3 py-1 rounded-full text-sm border ${
                filter === value ? 'border-blue-500 text-blue-400' : 'border-gray-700 text-gray-400'
              }`}
            >
              {label}
            </button>
          </Tooltip>
        ))}
      </div>

      {/* Job List */}
      <div className="space-y-2">
        {jobs.length === 0 && (
          <p className="text-gray-500 text-sm py-8 text-center">작업이 없습니다</p>
        )}
        {jobs.map((job) => (
          <Tooltip key={job.id} text={`ID: ${job.id} | 워크플로우: ${job.workflow || 'default'}`} position="bottom">
            <div className="bg-gray-900 rounded-lg p-4 flex items-center gap-4">
              <Tooltip text={STATUS_TOOLTIPS[job.status] || job.status}>
                <span className={`px-2 py-1 rounded text-xs font-mono cursor-default ${STATUS_COLORS[job.status] ?? ''}`}>
                  {job.status}
                </span>
              </Tooltip>
              <div className="flex-1 min-w-0">
                <p className="text-sm truncate">{job.prompt || job.type}</p>
                <p className="text-xs text-gray-500 font-mono">{job.id.slice(0, 8)}</p>
              </div>
              {job.stage && (
                <Tooltip text={`현재 단계: ${job.stage}`}>
                  <span className="text-xs text-gray-500 cursor-default">{job.stage}</span>
                </Tooltip>
              )}
              <div className="flex gap-1">
                {(job.status === 'pending' || job.status === 'running') && (
                  <Tooltip text="이 작업을 취소합니다">
                    <button
                      onClick={() => handleCancel(job.id)}
                      className="p-1 hover:bg-gray-800 rounded"
                    >
                      <X size={16} className="text-red-400" />
                    </button>
                  </Tooltip>
                )}
                {job.status === 'failed' && (
                  <Tooltip text="이 작업을 다시 시도합니다">
                    <button
                      onClick={() => handleRetry(job.id)}
                      className="p-1 hover:bg-gray-800 rounded"
                    >
                      <RotateCcw size={16} className="text-blue-400" />
                    </button>
                  </Tooltip>
                )}
              </div>
            </div>
          </Tooltip>
        ))}
      </div>
    </div>
  )
}
