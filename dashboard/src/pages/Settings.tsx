import { useState, useEffect } from 'react'
import { getGpuStatus, startGpuServer, stopGpuServer, switchGpuServer } from '../lib/api'

export default function SettingsPage() {
  const [gpu, setGpu] = useState('')
  const [loading, setLoading] = useState(false)

  const refresh = async () => {
    const { data } = await getGpuStatus()
    setGpu(data.output)
  }

  useEffect(() => { refresh() }, [])

  const act = async (fn: () => Promise<unknown>) => {
    setLoading(true)
    try {
      await fn()
      setTimeout(refresh, 3000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <h2 className="text-2xl font-bold">Settings</h2>

      {/* GPU Control */}
      <section className="bg-gray-900 rounded-lg p-4 space-y-4">
        <h3 className="font-semibold text-lg">GPU Server Control</h3>

        <pre className="text-sm text-gray-300 bg-gray-950 rounded p-3 overflow-auto">{gpu}</pre>

        <div className="grid grid-cols-2 gap-4">
          {/* Image Server */}
          <div className="border border-gray-700 rounded-lg p-3 space-y-2">
            <h4 className="font-medium text-sm">Image Server :8188</h4>
            <div className="flex gap-2">
              <button
                onClick={() => act(() => startGpuServer('image'))}
                disabled={loading}
                className="px-3 py-1.5 bg-green-700 hover:bg-green-600 rounded text-sm disabled:opacity-50"
              >
                Start
              </button>
              <button
                onClick={() => act(() => stopGpuServer('image'))}
                disabled={loading}
                className="px-3 py-1.5 bg-red-700 hover:bg-red-600 rounded text-sm disabled:opacity-50"
              >
                Stop
              </button>
            </div>
          </div>

          {/* Video Server */}
          <div className="border border-gray-700 rounded-lg p-3 space-y-2">
            <h4 className="font-medium text-sm">Video Server :8288</h4>
            <div className="flex gap-2">
              <button
                onClick={() => act(() => startGpuServer('video'))}
                disabled={loading}
                className="px-3 py-1.5 bg-green-700 hover:bg-green-600 rounded text-sm disabled:opacity-50"
              >
                Start
              </button>
              <button
                onClick={() => act(() => stopGpuServer('video'))}
                disabled={loading}
                className="px-3 py-1.5 bg-red-700 hover:bg-red-600 rounded text-sm disabled:opacity-50"
              >
                Stop
              </button>
            </div>
          </div>
        </div>

        {/* Switch Buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => act(() => switchGpuServer('image'))}
            disabled={loading}
            className="px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded text-sm disabled:opacity-50"
          >
            Switch to Image
          </button>
          <button
            onClick={() => act(() => switchGpuServer('video'))}
            disabled={loading}
            className="px-4 py-2 bg-purple-700 hover:bg-purple-600 rounded text-sm disabled:opacity-50"
          >
            Switch to Video
          </button>
          <button
            onClick={refresh}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm"
          >
            Refresh
          </button>
        </div>
      </section>
    </div>
  )
}
