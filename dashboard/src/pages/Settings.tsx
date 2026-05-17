import { useState, useEffect } from 'react'
import { getGpuStatus, startGpuServer, stopGpuServer, switchGpuServer } from '../lib/api'
import Tooltip from '../components/common/Tooltip'

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
        <h3 className="font-semibold text-lg">GPU 서버 제어</h3>

        <Tooltip text="현재 GPU 메모리 사용량, 온도, ComfyUI 서버 실행 상태를 표시합니다">
          <pre className="text-sm text-gray-300 bg-gray-950 rounded p-3 overflow-auto cursor-default">{gpu}</pre>
        </Tooltip>

        <div className="grid grid-cols-2 gap-4">
          {/* Image Server */}
          <Tooltip text="SDXL, Flux, IPAdapter 등 이미지 생성 전용 서버입니다. 포트 8188에서 실행됩니다">
            <div className="border border-gray-700 rounded-lg p-3 space-y-2">
              <h4 className="font-medium text-sm">이미지 서버 :8188</h4>
              <p className="text-xs text-gray-500">SDXL, Flux, 업스케일, 얼굴 보정</p>
              <div className="flex gap-2">
                <Tooltip text="이미지 서버를 시작합니다. GPU 6~7GB를 사용합니다">
                  <button
                    onClick={() => act(() => startGpuServer('image'))}
                    disabled={loading}
                    className="px-3 py-1.5 bg-green-700 hover:bg-green-600 rounded text-sm disabled:opacity-50"
                  >
                    시작
                  </button>
                </Tooltip>
                <Tooltip text="이미지 서버를 중지하고 GPU 메모리를 해제합니다">
                  <button
                    onClick={() => act(() => stopGpuServer('image'))}
                    disabled={loading}
                    className="px-3 py-1.5 bg-red-700 hover:bg-red-600 rounded text-sm disabled:opacity-50"
                  >
                    중지
                  </button>
                </Tooltip>
              </div>
            </div>
          </Tooltip>

          {/* Video Server */}
          <Tooltip text="AnimateDiff 등 비디오 생성 전용 서버입니다. 포트 8288에서 실행됩니다">
            <div className="border border-gray-700 rounded-lg p-3 space-y-2">
              <h4 className="font-medium text-sm">비디오 서버 :8288</h4>
              <p className="text-xs text-gray-500">AnimateDiff, 비디오 워크플로우</p>
              <div className="flex gap-2">
                <Tooltip text="비디오 서버를 시작합니다. 이미지 서버가 먼저 중지됩니다">
                  <button
                    onClick={() => act(() => startGpuServer('video'))}
                    disabled={loading}
                    className="px-3 py-1.5 bg-green-700 hover:bg-green-600 rounded text-sm disabled:opacity-50"
                  >
                    시작
                  </button>
                </Tooltip>
                <Tooltip text="비디오 서버를 중지하고 GPU 메모리를 해제합니다">
                  <button
                    onClick={() => act(() => stopGpuServer('video'))}
                    disabled={loading}
                    className="px-3 py-1.5 bg-red-700 hover:bg-red-600 rounded text-sm disabled:opacity-50"
                  >
                    중지
                  </button>
                </Tooltip>
              </div>
            </div>
          </Tooltip>
        </div>

        {/* Switch Buttons */}
        <div className="flex gap-2">
          <Tooltip text="비디오 서버를 중지하고 이미지 서버를 시작합니다. VRAM 자동 정리 포함">
            <button
              onClick={() => act(() => switchGpuServer('image'))}
              disabled={loading}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded text-sm disabled:opacity-50"
            >
              이미지로 전환
            </button>
          </Tooltip>
          <Tooltip text="이미지 서버를 중지하고 비디오 서버를 시작합니다. VRAM 자동 정리 포함">
            <button
              onClick={() => act(() => switchGpuServer('video'))}
              disabled={loading}
              className="px-4 py-2 bg-purple-700 hover:bg-purple-600 rounded text-sm disabled:opacity-50"
            >
              비디오로 전환
            </button>
          </Tooltip>
          <Tooltip text="GPU 상태 정보를 새로고침합니다">
            <button
              onClick={refresh}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm"
            >
              새로고침
            </button>
          </Tooltip>
        </div>

        <div className="text-xs text-gray-600 bg-gray-950 rounded p-3">
          <p>두 서버는 동시에 실행할 수 없습니다 (8GB VRAM 제한).</p>
          <p>전환 시 이전 서버가 자동으로 중지되고 VRAM이 정리됩니다.</p>
        </div>
      </section>
    </div>
  )
}
