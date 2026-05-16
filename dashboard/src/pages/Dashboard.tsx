import { useState, useEffect } from 'react'
import { getGpuStatus, getQueueStatus, type QueueStatus } from '../lib/api'

export default function Dashboard() {
  const [gpu, setGpu] = useState('')
  const [queue, setQueue] = useState<QueueStatus>({ pending: 0, running: 0, failed: 0 })

  const refresh = async () => {
    try {
      const [gpuRes, queueRes] = await Promise.all([getGpuStatus(), getQueueStatus()])
      setGpu(gpuRes.data.output)
      setQueue(queueRes.data)
    } catch {
      setGpu('Gateway unreachable')
    }
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>

      {/* Queue Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 rounded-lg p-4">
          <p className="text-sm text-gray-400">Pending</p>
          <p className="text-3xl font-bold text-yellow-400">{queue.pending}</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-4">
          <p className="text-sm text-gray-400">Running</p>
          <p className="text-3xl font-bold text-blue-400">{queue.running}</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-4">
          <p className="text-sm text-gray-400">Failed</p>
          <p className="text-3xl font-bold text-red-400">{queue.failed}</p>
        </div>
      </div>

      {/* GPU Status */}
      <div className="bg-gray-900 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">GPU Status</h3>
          <button onClick={refresh} className="text-sm text-blue-400 hover:text-blue-300">
            Refresh
          </button>
        </div>
        <pre className="text-sm text-gray-300 bg-gray-950 rounded p-3 overflow-auto">{gpu}</pre>
      </div>
    </div>
  )
}
