import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// ── Types ──

export interface Job {
  id: string
  status: string
  type: string
  prompt?: string
  workflow?: string
  params?: string
  result_urls?: string
  error?: string
  stage?: string
  created_at?: string
  updated_at?: string
}

export interface QueueStatus {
  pending: number
  running: number
  failed: number
}

export interface GpuStatus {
  output: string
}

export interface Agent {
  id: string
  name: string
  role: string
  emoji: string
  color: string
  specialty: string
  tagline: string
  persona: string
  tools: string[]
  status: string
}

export interface Skill {
  name: string
  description: string
  path?: string
  type: string
}

export interface ToolSeed {
  name: string
  agent: string
  purpose: string
  has_doc: boolean
  has_code: boolean
}

export interface SystemVersion {
  version: string
  timestamp: string
  sha: string
  commit: string
  branch: string
  server_time: string
}

export interface PipelineStatus {
  job_id: string
  status: string
  steps?: Record<string, unknown>
}

export interface Product {
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
}

// ── Jobs ──

export const createJob = (data: Record<string, unknown>) => api.post('/jobs/', data)
export const listJobs = (params?: { limit?: number; status?: string }) => api.get<Job[]>('/jobs/', { params })
export const getJob = (id: string) => api.get<Job>(`/jobs/${id}`)
export const cancelJob = (id: string) => api.delete(`/jobs/${id}`)
export const retryJob = (id: string) => api.post(`/jobs/${id}/retry`)

// ── GPU Control ──

export const getGpuStatus = () => api.get<GpuStatus>('/control/gpu/status')
export const startGpuServer = (server: 'image' | 'video') => api.post(`/control/gpu/start/${server}`)
export const stopGpuServer = (server: 'image' | 'video') => api.post(`/control/gpu/stop/${server}`)
export const switchGpuServer = (target: 'image' | 'video') => api.post(`/control/gpu/switch/${target}`)
export const getQueueStatus = () => api.get<QueueStatus>('/control/queue')

// ── Agents ──

export const listAgents = () => api.get<Agent[]>('/agents/')
export const getAgent = (id: string) => api.get<Agent>(`/agents/${id}`)
export const createAgent = (data: Partial<Agent>) => api.post('/agents/', data)
export const updateAgent = (id: string, data: Partial<Agent>) => api.put(`/agents/${id}`, data)
export const deleteAgent = (id: string) => api.delete(`/agents/${id}`)
export const getAgentTools = (id: string) => api.get<ToolSeed[]>(`/agents/${id}/tools`)

// ── Skills ──

export const listSkills = () => api.get<Skill[]>('/skills/')
export const listToolSeeds = () => api.get<ToolSeed[]>('/skills/tool-seeds')
export const listAgentToolSeeds = (agentId: string) => api.get<ToolSeed[]>(`/skills/tool-seeds/${agentId}`)
export const getDecisions = () => api.get<{ content: string }>('/skills/decisions')

// ── System ──

export const getVersion = () => api.get<SystemVersion>('/system/version')

// ── Pipeline ──

export const runPipeline = (data: {
  product?: Record<string, unknown>
  start_step?: number
  max_retries?: number
}) => api.post('/pipeline/run', data)

export const runCrawl = (data: { category?: string; limit?: number }) =>
  api.post('/pipeline/crawl', data)

export const getPipelineStatus = (jobId: string) =>
  api.get<PipelineStatus>(`/pipeline/status/${jobId}`)

export const approvePipeline = (jobId: string) =>
  api.post(`/pipeline/approve/${jobId}`)

export const retryPipeline = (jobId: string) =>
  api.post(`/pipeline/retry/${jobId}`)

export const editPipeline = (jobId: string, editText: string) =>
  api.post(`/pipeline/edit/${jobId}`, null, { params: { edit_text: editText } })
