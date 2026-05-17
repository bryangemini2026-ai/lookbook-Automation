import { useState, useEffect } from 'react'
import { runCrawl, listJobs, type Job } from '../lib/api'
import { ShoppingBag, RefreshCw, ExternalLink, Star, TrendingUp } from 'lucide-react'
import Tooltip from '../components/common/Tooltip'

const CATEGORIES = ['상의', '하의', '아우터', '원피스', '신발']

interface CrawledProduct {
  platform: string
  product_id: string
  name: string
  brand: string
  price: number
  original_price: number
  discount_rate: number
  category: string
  image_url: string
  product_url: string
  affiliate_url: string
  ranking: number
  review_count: number
  rating: number
  tags: string[]
  season: string
  collected_at: string
  recommendation_reason?: string
}

export default function Crawling() {
  const [category, setCategory] = useState('상의')
  const [limit, setLimit] = useState(10)
  const [submitting, setSubmitting] = useState(false)
  const [crawlJobs, setCrawlJobs] = useState<Job[]>([])
  const [products, setProducts] = useState<CrawledProduct[]>([])

  const refresh = async () => {
    const { data } = await listJobs({ limit: 20 })
    setCrawlJobs(data.filter((j: Job) => j.type === 'crawl'))
  }

  useEffect(() => {
    refresh()
  }, [])

  const handleCrawl = async () => {
    setSubmitting(true)
    try {
      await runCrawl({ category, limit })
      setTimeout(refresh, 2000)
    } catch (err) {
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  // Mock products for display
  const mockProducts: CrawledProduct[] = [
    {
      platform: 'musinsa', product_id: 'MU001', name: '오버핏 블랙 자켓',
      brand: '무신사 스탠다드', price: 39900, original_price: 59900, discount_rate: 33,
      category: '아우터', image_url: '', product_url: '#', affiliate_url: '#',
      ranking: 1, review_count: 1250, rating: 4.8, tags: ['인기', '봄'],
      season: 'spring', collected_at: '2026-05-17', recommendation_reason: '무신사 랭킹 1위 · 리뷰 1,250개 · 33% 할인',
    },
    {
      platform: 'coupang', product_id: 'CP001', name: '로켓배송 기본 티셔츠',
      brand: '쿠팡 베이직', price: 12900, original_price: 19900, discount_rate: 35,
      category: '상의', image_url: '', product_url: '#', affiliate_url: '#',
      ranking: 2, review_count: 3400, rating: 4.7, tags: ['로켓배송', '기본'],
      season: 'spring', collected_at: '2026-05-17', recommendation_reason: '쿠팡 랭킹 2위 · 리뷰 3,400개 · 35% 할인',
    },
    {
      platform: 'musinsa', product_id: 'MU002', name: '슬림핏 데님 팬츠',
      brand: '디스이즈네버댓', price: 59000, original_price: 89000, discount_rate: 34,
      category: '하의', image_url: '', product_url: '#', affiliate_url: '#',
      ranking: 3, review_count: 890, rating: 4.9, tags: ['인기', '데님'],
      season: 'spring', collected_at: '2026-05-17', recommendation_reason: '무신사 랭킹 3위 · 평점 4.9 · 34% 할인',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <ShoppingBag size={24} />
        <h2 className="text-2xl font-bold">크롤링 에이전트</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Control Panel */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-gray-900 rounded-lg p-4 space-y-4">
            <h3 className="font-semibold">크롤링 설정</h3>

            <Tooltip text="수집할 의류 카테고리를 선택하세요" position="bottom">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">카테고리</label>
                <div className="grid grid-cols-2 gap-2">
                  {CATEGORIES.map(cat => (
                    <button
                      key={cat}
                      onClick={() => setCategory(cat)}
                      className={`px-3 py-2 rounded-lg text-sm border ${
                        category === cat
                          ? 'border-blue-500 bg-blue-600/20 text-blue-400'
                          : 'border-gray-700 text-gray-400 hover:border-gray-600'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>
            </Tooltip>

            <Tooltip text="카테고리당 수집할 상품 수" position="bottom">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">수집 수량</label>
                <select
                  value={limit}
                  onChange={e => setLimit(parseInt(e.target.value))}
                  className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm"
                >
                  <option value={5}>5개</option>
                  <option value={10}>10개</option>
                  <option value={20}>20개</option>
                  <option value={50}>50개</option>
                </select>
              </div>
            </Tooltip>

            <Tooltip text="무신사/쿠팡에서 인기 상품을 수집합니다" position="bottom">
              <button
                onClick={handleCrawl}
                disabled={submitting}
                className="w-full py-3 bg-green-600 hover:bg-green-500 disabled:bg-gray-700 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
              >
                <ShoppingBag size={18} />
                {submitting ? '수집 중...' : '크롤링 시작'}
              </button>
            </Tooltip>
          </div>

          {/* Recent Crawl Jobs */}
          <div className="bg-gray-900 rounded-lg p-4">
            <h3 className="font-semibold mb-3">최근 크롤링</h3>
            {crawlJobs.length === 0 ? (
              <p className="text-sm text-gray-500">아직 크롤링 기록이 없습니다</p>
            ) : (
              <div className="space-y-2">
                {crawlJobs.slice(0, 5).map(job => (
                  <div key={job.id} className="flex items-center gap-2 text-sm">
                    <div className={`w-2 h-2 rounded-full ${
                      job.status === 'completed' ? 'bg-green-500' :
                      job.status === 'running' ? 'bg-blue-500' : 'bg-gray-500'
                    }`} />
                    <span className="text-gray-400 font-mono text-xs">{job.id.slice(0, 8)}</span>
                    <span className="text-gray-500">{job.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Product List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">수집된 상품</h3>
            <Tooltip text="목록을 새로고침합니다">
              <button onClick={refresh} className="p-2 hover:bg-gray-800 rounded-lg">
                <RefreshCw size={16} />
              </button>
            </Tooltip>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mockProducts.map(product => (
              <Tooltip key={product.product_id} text={product.recommendation_reason} position="bottom">
                <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        product.platform === 'musinsa'
                          ? 'bg-orange-600/20 text-orange-400'
                          : 'bg-blue-600/20 text-blue-400'
                      }`}>
                        {product.platform}
                      </span>
                      <span className="text-xs text-gray-500 ml-2">#{product.ranking}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Star size={12} className="text-yellow-400" />
                      <span className="text-xs text-yellow-400">{product.rating}</span>
                    </div>
                  </div>

                  <h4 className="font-semibold text-sm mb-1">{product.name}</h4>
                  <p className="text-xs text-gray-500 mb-2">{product.brand}</p>

                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg font-bold text-white">{product.price.toLocaleString()}원</span>
                    {product.discount_rate > 0 && (
                      <>
                        <span className="text-sm text-gray-500 line-through">{product.original_price.toLocaleString()}원</span>
                        <span className="text-sm text-red-400 font-semibold">{product.discount_rate}%</span>
                      </>
                    )}
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">리뷰 {product.review_count.toLocaleString()}개</span>
                    <div className="flex gap-1">
                      {product.tags.slice(0, 3).map(tag => (
                        <span key={tag} className="text-xs px-1.5 py-0.5 bg-gray-800 rounded">{tag}</span>
                      ))}
                    </div>
                  </div>

                  {product.recommendation_reason && (
                    <div className="mt-3 px-3 py-2 bg-green-900/20 rounded-lg">
                      <div className="flex items-center gap-1 mb-1">
                        <TrendingUp size={12} className="text-green-400" />
                        <span className="text-xs text-green-400 font-semibold">추천 이유</span>
                      </div>
                      <p className="text-xs text-green-300">{product.recommendation_reason}</p>
                    </div>
                  )}
                </div>
              </Tooltip>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
