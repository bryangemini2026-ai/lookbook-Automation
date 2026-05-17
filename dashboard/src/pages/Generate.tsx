import { useState } from 'react'
import { createJob } from '../lib/api'
import Tooltip from '../components/common/Tooltip'

const WORKFLOWS = [
  { id: 'lookbook_portrait', label: 'Portrait', tooltip: '인물 중심 룩북 사진. 상반신, 스튜디오 조명' },
  { id: 'lookbook_full_body', label: 'Full Body', tooltip: '전신 룩북 사진. 전체 스타일링 확인' },
  { id: 'lookbook_flatlay', label: 'Flat Lay', tooltip: '플랫레이 촬영. 옷을 평평하게 펼쳐서 촬영' },
  { id: 'lookbook_lifestyle', label: 'Lifestyle', tooltip: '라이프스타일 촬영. 자연스러운 배경과 분위기' },
]

export default function Generate() {
  const [prompt, setPrompt] = useState('')
  const [negative, setNegative] = useState('low quality, blurry, deformed')
  const [workflow, setWorkflow] = useState('lookbook_portrait')
  const [upscale, setUpscale] = useState(true)
  const [makeReel, setMakeReel] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [lastJobId, setLastJobId] = useState('')

  const handleSubmit = async () => {
    if (!prompt.trim()) return
    setSubmitting(true)
    try {
      const { data } = await createJob({
        prompt: prompt.trim(),
        negative_prompt: negative.trim(),
        workflow,
        upscale,
        make_reel: makeReel,
        platforms: ['instagram'],
        params: { steps: 25, cfg: 7.0, width: 1024, height: 1024, seed: -1 },
      })
      setLastJobId(data.id)
      setPrompt('')
    } catch (err) {
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <h2 className="text-2xl font-bold">Generate Lookbook</h2>

      {/* Prompt */}
      <Tooltip text="생성할 룩북 이미지를 설명하세요. 스타일, 조명, 배경 등을 포함하면 더 좋은 결과를 얻습니다" position="bottom">
        <div>
          <label className="block text-sm text-gray-400 mb-1">프롬프트</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="fashion lookbook photo, studio lighting, model wearing black dress, minimalist background..."
            className="w-full h-28 bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm resize-none focus:border-blue-500 focus:outline-none"
          />
        </div>
      </Tooltip>

      {/* Negative Prompt */}
      <Tooltip text="이미지에서 제외할 요소를 입력하세요. 저품질, 번짐, 왜곡 등을 방지합니다" position="bottom">
        <div>
          <label className="block text-sm text-gray-400 mb-1">네거티브 프롬프트</label>
          <input
            value={negative}
            onChange={(e) => setNegative(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
      </Tooltip>

      {/* Workflow */}
      <div>
        <label className="block text-sm text-gray-400 mb-1">워크플로우</label>
        <div className="grid grid-cols-4 gap-2">
          {WORKFLOWS.map((w) => (
            <Tooltip key={w.id} text={w.tooltip} position="bottom">
              <button
                onClick={() => setWorkflow(w.id)}
                className={`p-2 rounded-lg text-sm border w-full ${
                  workflow === w.id
                    ? 'border-blue-500 bg-blue-600/20 text-blue-400'
                    : 'border-gray-700 hover:border-gray-600 text-gray-400'
                }`}
              >
                {w.label}
              </button>
            </Tooltip>
          ))}
        </div>
      </div>

      {/* Options */}
      <div className="flex gap-6">
        <Tooltip text="이미지를 4배 확대하여 고해상도로 만듭니다. VRAM 2GB 추가 사용" position="bottom">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={upscale} onChange={(e) => setUpscale(e.target.checked)} />
            <span>4x 업스케일</span>
          </label>
        </Tooltip>
        <Tooltip text="생성된 이미지로 짧은 릴 비디오를 만듭니다. 줌/팬 효과 적용" position="bottom">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={makeReel} onChange={(e) => setMakeReel(e.target.checked)} />
            <span>릴 비디오 생성</span>
          </label>
        </Tooltip>
      </div>

      {/* Submit */}
      <Tooltip text="작업을 큐에 추가합니다. GPU 서버가 자동으로 시작됩니다" position="bottom">
        <button
          onClick={handleSubmit}
          disabled={submitting || !prompt.trim()}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-semibold transition-colors"
        >
          {submitting ? '제출 중...' : '생성하기'}
        </button>
      </Tooltip>

      {lastJobId && (
        <p className="text-sm text-green-400">
          작업 생성 완료: <span className="font-mono">{lastJobId.slice(0, 8)}</span>
        </p>
      )}
    </div>
  )
}
