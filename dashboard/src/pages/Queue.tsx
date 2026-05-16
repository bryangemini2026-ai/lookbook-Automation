import { useState, useEffect } from 'react'
import { listJobs, cancelJob, retryJob, type Job } from '../lib/api'
import { RefreshCw, X, RotateCcw } from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  pending: 'text-yellow-400 bg-yellow-400/10',
  running: 'text-blue-400 bg-blue-400/10',
  completed: 'text-green-400 bg-green-400/10',
  failed: 'text-red-400 bg-red-400/10',
  cancelled: 'text-gray-400 bg-gray-400/10',
}

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
        <h2 className="text-2xl font-bold">Job Queue</h2>
        <button onClick={refresh} className="p-2 hover:bg-gray-800 rounded-lg">
          <RefreshCw size={18} />
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {[undefined, 'pending', 'running', 'completed', 'failed'].map((s) => (
          <button
            key={s ?? 'all'}
            onClick={() => setFilter(s)}
            className={`px-3 py-1 rounded-full text-sm border ${
              filter === s ? 'border-blue-500 text-blue-400' : 'border-gray-700 text-gray-400'
            }`}
          >
            {s ?? 'All'}
          </button>
        ))}
      </div>

      {/* Job List */}
      <div className="space-y-2">
        {jobs.length === 0 && (
          <p className="text-gray-500 text-sm py-8 text-center">No jobs found</p>
        )}
        {jobs.map((job) => (
          <div key={job.id} className="bg-gray-900 rounded-lg p-4 flex items-center gap-4">
            <span className={`px-2 py-1 rounded text-xs font-mono ${STATUS_COLORS[job.status] ?? ''}`}>
              {job.status}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate">{job.prompt || job.type}</p>
              <p className="text-xs text-gray-500 font-mono">{job.id.slice(0, 8)}</p>
            </div>
            {job.stage && (
              <span className="text-xs text-gray-500">{job.stage}</span>
            )}
            <div className="flex gap-1">
              {(job.status === 'pending' || job.status === 'running') && (
                <button
                  onClick={() => handleCancel(job.id)}
                  className="p-1 hover:bg-gray-800 rounded"
                  title="Cancel"
                >
                  <X size={16} className="text-red-400" />
                </button>
              )}
              {job.status === 'failed' && (
                <button
                  onClick={() => handleRetry(job.id)}
                  className="p-1 hover:bg-gray-800 rounded"
                  title="Retry"
                >
                  <RotateCcw size={16} className="text-blue-400" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
