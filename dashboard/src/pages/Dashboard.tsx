import { useState, useEffect } from 'react'
import { getGpuStatus, getQueueStatus, type QueueStatus } from '../lib/api'
import Tooltip from '../components/common/Tooltip'

export default function Dashboard() {
  const [gpu, setGpu] = useState('')
  const [queue, setQueue] = useState<QueueStatus>({ pending: 0, running: 0, failed: 0 })

  const refresh = async () => {
    try {
      const [gpuRes, queueRes] = await Promise.all([getGpuStatus(), getQueueStatus()])
      setGpu(gpuRes.data.output)
      setQueue(queueRes.data)
    } catch {
      setGpu('Gateway 연결 실패')
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
        <Tooltip text="실행을 기다리고 있는 작업 수입니다">
          <div className="bg-gray-900 rounded-lg p-4 cursor-default">
            <p className="text-sm text-gray-400">Pending</p>
            <p className="text-3xl font-bold text-yellow-400">{queue.pending}</p>
            <p className="text-xs text-gray-600 mt-1">대기 중</p>
          </div>
        </Tooltip>
        <Tooltip text="현재 GPU에서 실행 중인 작업 수입니다">
          <div className="bg-gray-900 rounded-lg p-4 cursor-default">
            <p className="text-sm text-gray-400">Running</p>
            <p className="text-3xl font-bold text-blue-400">{queue.running}</p>
            <p className="text-xs text-gray-600 mt-1">실행 중</p>
          </div>
        </Tooltip>
        <Tooltip text="실패한 작업 수입니다. 재시도가 필요할 수 있습니다">
          <div className="bg-gray-900 rounded-lg p-4 cursor-default">
            <p className="text-sm text-gray-400">Failed</p>
            <p className="text-3xl font-bold text-red-400">{queue.failed}</p>
            <p className="text-xs text-gray-600 mt-1">실패</p>
          </div>
        </Tooltip>
      </div>

      {/* GPU Status */}
      <Tooltip text="GPU 메모리 사용량, 온도, ComfyUI 서버 상태를 표시합니다">
        <div className="bg-gray-900 rounded-lg p-4 cursor-default">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">GPU Status</h3>
            <button onClick={refresh} className="text-sm text-blue-400 hover:text-blue-300">
              새로고침
            </button>
          </div>
          <pre className="text-sm text-gray-300 bg-gray-950 rounded p-3 overflow-auto">{gpu}</pre>
        </div>
      </Tooltip>
    </div>
  )
}
