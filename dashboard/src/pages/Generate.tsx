import { useState } from 'react'
import { createJob } from '../lib/api'

const WORKFLOWS = [
  { id: 'lookbook_portrait', label: 'Portrait' },
  { id: 'lookbook_full_body', label: 'Full Body' },
  { id: 'lookbook_flatlay', label: 'Flat Lay' },
  { id: 'lookbook_lifestyle', label: 'Lifestyle' },
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
      <div>
        <label className="block text-sm text-gray-400 mb-1">Prompt</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="fashion lookbook photo, studio lighting, model wearing..."
          className="w-full h-28 bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm resize-none focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Negative Prompt */}
      <div>
        <label className="block text-sm text-gray-400 mb-1">Negative Prompt</label>
        <input
          value={negative}
          onChange={(e) => setNegative(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Workflow */}
      <div>
        <label className="block text-sm text-gray-400 mb-1">Workflow</label>
        <div className="grid grid-cols-4 gap-2">
          {WORKFLOWS.map((w) => (
            <button
              key={w.id}
              onClick={() => setWorkflow(w.id)}
              className={`p-2 rounded-lg text-sm border ${
                workflow === w.id
                  ? 'border-blue-500 bg-blue-600/20 text-blue-400'
                  : 'border-gray-700 hover:border-gray-600 text-gray-400'
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>
      </div>

      {/* Options */}
      <div className="flex gap-6">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={upscale} onChange={(e) => setUpscale(e.target.checked)} />
          <span>Upscale 4x</span>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={makeReel} onChange={(e) => setMakeReel(e.target.checked)} />
          <span>Create Reel</span>
        </label>
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={submitting || !prompt.trim()}
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-semibold transition-colors"
      >
        {submitting ? 'Submitting...' : 'Generate'}
      </button>

      {lastJobId && (
        <p className="text-sm text-green-400">
          Job created: <span className="font-mono">{lastJobId.slice(0, 8)}</span>
        </p>
      )}
    </div>
  )
}
