import { useState, useEffect } from 'react'
import { runPipeline, getPipelineStatus, listJobs, type Job } from '../lib/api'
import { Play, RefreshCw, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react'
import Tooltip from '../components/common/Tooltip'

const STEPS = [
  { id: 2, name: '이미지 생성', desc: 'ZIT+ZIB로 3프레임 생성', color: 'blue' },
  { id: 3, name: '영상 생성', desc: 'Sulphur-2 I2V 변환', color: 'purple' },
  { id: 4, name: '편집', desc: 'FFmpeg BGM/자막 삽입', color: 'pink' },
  { id: 5, name: '업로드', desc: 'YouTube 임시등록', color: 'green' },
  { id: 6, name: '분석', desc: '성과 데이터 수집', color: 'yellow' },
]

export default function Pipeline() {
  const [productName, setProductName] = useState('')
  const [productBrand, setProductBrand] = useState('')
  const [productPrice, setProductPrice] = useState('')
  const [productUrl, setProductUrl] = useState('')
  const [startStep, setStartStep] = useState(2)
  const [submitting, setSubmitting] = useState(false)
  const [pipelineJobs, setPipelineJobs] = useState<Job[]>([])
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const [jobDetail, setJobDetail] = useState<Record<string, unknown> | null>(null)

  const refresh = async () => {
    const { data } = await listJobs({ limit: 20 })
    setPipelineJobs(data.filter((j: Job) => j.type === 'lookbook_pipeline'))
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (selectedJob) {
      getPipelineStatus(selectedJob).then(({ data }) => setJobDetail(data)).catch(() => {})
    }
  }, [selectedJob])

  const handleRun = async () => {
    if (!productName.trim()) return
    setSubmitting(true)
    try {
      const product: Record<string, unknown> = {
        name: productName.trim(),
        brand: productBrand.trim(),
        price: parseInt(productPrice) || 0,
        platform: 'manual',
        season: 'spring',
      }
      if (productUrl.trim()) product.product_url = productUrl.trim()

      const { data } = await runPipeline({ product, start_step: startStep })
      setSelectedJob(data.job_id)
      setProductName('')
      setProductBrand('')
      setProductPrice('')
      setProductUrl('')
    } catch (err) {
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  const statusIcon = (status?: string) => {
    switch (status) {
      case 'approved':
      case 'published':
      case 'completed':
        return <CheckCircle size={16} className="text-green-400" />
      case 'pending':
      case 'running':
        return <Loader2 size={16} className="text-blue-400 animate-spin" />
      case 'max_retries':
      case 'failed':
        return <XCircle size={16} className="text-red-400" />
      default:
        return <Clock size={16} className="text-gray-500" />
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Play size={24} />
        <h2 className="text-2xl font-bold">룩북 파이프라인</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-gray-900 rounded-lg p-4 space-y-4">
            <h3 className="font-semibold">상품 정보 입력</h3>

            <Tooltip text="크롤링에서 수집된 상품명 또는 수동 입력" position="bottom">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">상품명 *</label>
                <input
                  value={productName}
                  onChange={e => setProductName(e.target.value)}
                  placeholder="예: 블랙 오버핏 자켓"
                  className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm"
                />
              </div>
            </Tooltip>

            <Tooltip text="브랜드명을 입력하세요" position="bottom">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">브랜드</label>
                <input
                  value={productBrand}
                  onChange={e => setProductBrand(e.target.value)}
                  placeholder="예: 무신사 스탠다드"
                  className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm"
                />
              </div>
            </Tooltip>

            <div className="grid grid-cols-2 gap-3">
              <Tooltip text="상품 가격 (원)" position="bottom">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">가격</label>
                  <input
                    value={productPrice}
                    onChange={e => setProductPrice(e.target.value)}
                    placeholder="39900"
                    type="number"
                    className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm"
                  />
                </div>
              </Tooltip>
              <Tooltip text="파이프라인 시작 단계" position="bottom">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">시작 단계</label>
                  <select
                    value={startStep}
                    onChange={e => setStartStep(parseInt(e.target.value))}
                    className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm"
                  >
                    {STEPS.map(s => (
                      <option key={s.id} value={s.id}>STEP {s.id}: {s.name}</option>
                    ))}
                  </select>
                </div>
              </Tooltip>
            </div>

            <Tooltip text="상품 URL (어필리에이트 링크 포함)" position="bottom">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">상품 URL</label>
                <input
                  value={productUrl}
                  onChange={e => setProductUrl(e.target.value)}
                  placeholder="https://www.musinsa.com/products/..."
                  className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm"
                />
              </div>
            </Tooltip>

            <Tooltip text="파이프라인을 시작합니다. Telegram에서 승인이 필요합니다">
              <button
                onClick={handleRun}
                disabled={submitting || !productName.trim()}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
              >
                <Play size={18} />
                {submitting ? '시작 중...' : '파이프라인 시작'}
              </button>
            </Tooltip>
          </div>

          {/* Pipeline Steps Info */}
          <div className="bg-gray-900 rounded-lg p-4">
            <h3 className="font-semibold mb-3">파이프라인 단계</h3>
            <div className="space-y-2">
              {STEPS.map(step => (
                <Tooltip key={step.id} text={step.desc} position="bottom">
                  <div className="flex items-center gap-3 px-3 py-2 bg-gray-950 rounded-lg">
                    <div className={`w-8 h-8 rounded-full bg-${step.color}-600/20 text-${step.color}-400 flex items-center justify-center text-xs font-bold`}>
                      {step.id}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{step.name}</p>
                      <p className="text-xs text-gray-500">{step.desc}</p>
                    </div>
                  </div>
                </Tooltip>
              ))}
            </div>
          </div>
        </div>

        {/* Status Panel */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">파이프라인 상태</h3>
            <button onClick={refresh} className="p-2 hover:bg-gray-800 rounded-lg">
              <RefreshCw size={16} />
            </button>
          </div>

          {/* Job List */}
          <div className="space-y-2">
            {pipelineJobs.length === 0 ? (
              <div className="bg-gray-900 rounded-lg p-8 text-center">
                <Play size={32} className="mx-auto text-gray-600 mb-3" />
                <p className="text-gray-500">실행된 파이프라인이 없습니다</p>
                <p className="text-xs text-gray-600 mt-1">상품 정보를 입력하고 파이프라인을 시작하세요</p>
              </div>
            ) : (
              pipelineJobs.map(job => (
                <Tooltip key={job.id} text={`ID: ${job.id}`} position="bottom">
                  <div
                    onClick={() => setSelectedJob(job.id)}
                    className={`bg-gray-900 rounded-lg p-4 cursor-pointer border transition-colors ${
                      selectedJob === job.id ? 'border-blue-500' : 'border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {statusIcon(job.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm truncate">{job.prompt || job.type}</p>
                        <p className="text-xs text-gray-500 font-mono">{job.id.slice(0, 8)}</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${
                        job.status === 'completed' ? 'bg-green-600/20 text-green-400' :
                        job.status === 'running' ? 'bg-blue-600/20 text-blue-400' :
                        job.status === 'failed' ? 'bg-red-600/20 text-red-400' :
                        'bg-gray-600/20 text-gray-400'
                      }`}>
                        {job.status}
                      </span>
                    </div>

                    {/* Step Progress */}
                    {job.stage && (
                      <div className="mt-3 flex gap-1">
                        {STEPS.map(step => (
                          <div
                            key={step.id}
                            className={`flex-1 h-1 rounded-full ${
                              job.stage === step.name ? 'bg-blue-500' :
                              parseInt(job.stage || '0') > step.id ? 'bg-green-500' :
                              'bg-gray-700'
                            }`}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </Tooltip>
              ))
            )}
          </div>

          {/* Job Detail */}
          {selectedJob && jobDetail && (
            <div className="bg-gray-900 rounded-lg p-4">
              <h4 className="font-semibold mb-3">작업 상세</h4>
              <pre className="text-xs text-gray-300 bg-gray-950 rounded p-3 overflow-auto max-h-64">
                {JSON.stringify(jobDetail, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
