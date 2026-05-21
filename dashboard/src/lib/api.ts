// Types
export interface SystemVersion {
  version: string
  commit: string
  branch: string
}

export interface GPUStatus {
  temperature: number
  usage: number
  server: 'image' | 'video'
  status: 'active' | 'idle' | 'error'
}

export interface QueueStatus {
  pending: number
  processing: number
  completed: number
  total: number
}

export interface PipelineStatus {
  currentStage: 'generate' | 'upscale' | 'video' | 'sns' | 'idle'
  activeJob: string | null
  timeElapsed: number
  stages: {
    name: string
    status: 'completed' | 'active' | 'pending'
  }[]
}

export interface DashboardStats {
  totalJobs: number
  successRate: number
  avgGenerationTime: number
  activeAgents: number
}

export interface RecentActivity {
  id: string
  jobName: string
  status: 'completed' | 'processing' | 'pending' | 'error'
  timestamp: string
  type: 'image' | 'video' | 'reel'
}

export interface AgentInfo {
  id: string
  name: string
  role: string
  status: 'active' | 'idle' | 'error'
  lastActive: string
}

// Mock data
const mockVersion: SystemVersion = {
  version: 'v0.0.8',
  commit: 'abc1234',
  branch: 'main',
}

const mockGPUStatus: GPUStatus = {
  temperature: 65,
  usage: 45,
  server: 'image',
  status: 'active',
}

const mockQueueStatus: QueueStatus = {
  pending: 12,
  processing: 3,
  completed: 156,
  total: 171,
}

const mockPipelineStatus: PipelineStatus = {
  currentStage: 'generate',
  activeJob: 'Summer Collection Look #23',
  timeElapsed: 125,
  stages: [
    { name: 'Generate', status: 'completed' },
    { name: 'Upscale', status: 'active' },
    { name: 'Video', status: 'pending' },
    { name: 'SNS', status: 'pending' },
  ],
}

const mockDashboardStats: DashboardStats = {
  totalJobs: 1247,
  successRate: 94.5,
  avgGenerationTime: 45,
  activeAgents: 4,
}

const mockRecentActivity: RecentActivity[] = [
  {
    id: '1',
    jobName: 'Summer Collection Look #23',
    status: 'processing',
    timestamp: '2 minutes ago',
    type: 'image',
  },
  {
    id: '2',
    jobName: 'Casual Outfit Preview',
    status: 'completed',
    timestamp: '15 minutes ago',
    type: 'video',
  },
  {
    id: '3',
    jobName: 'Street Style Reel',
    status: 'completed',
    timestamp: '1 hour ago',
    type: 'reel',
  },
  {
    id: '4',
    jobName: 'Evening Wear Look #12',
    status: 'error',
    timestamp: '2 hours ago',
    type: 'image',
  },
  {
    id: '5',
    jobName: 'Sportswear Collection',
    status: 'pending',
    timestamp: '3 hours ago',
    type: 'video',
  },
]

const mockAgents: AgentInfo[] = [
  {
    id: '1',
    name: 'Persona Agent',
    role: '캐릭터 페르소나 생성',
    status: 'active',
    lastActive: '5 minutes ago',
  },
  {
    id: '2',
    name: 'Image Generator',
    role: '이미지 생성 전문',
    status: 'active',
    lastActive: '2 minutes ago',
  },
  {
    id: '3',
    name: 'Video Creator',
    role: '영상 생성 전문',
    status: 'idle',
    lastActive: '1 hour ago',
  },
  {
    id: '4',
    name: 'SNS Publisher',
    role: 'SNS 자동 포스팅',
    status: 'active',
    lastActive: '10 minutes ago',
  },
  {
    id: '5',
    name: 'Trend Analyzer',
    role: '트렌드 분석 및 브리핑',
    status: 'idle',
    lastActive: '3 hours ago',
  },
]

// API functions with simulated delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export async function getVersion(): Promise<{ data: SystemVersion }> {
  await delay(100)
  return { data: mockVersion }
}

export async function getGPUStatus(): Promise<{ data: GPUStatus }> {
  await delay(150)
  return { data: mockGPUStatus }
}

export async function getQueueStatus(): Promise<{ data: QueueStatus }> {
  await delay(100)
  return { data: mockQueueStatus }
}

export async function getPipelineStatus(): Promise<{ data: PipelineStatus }> {
  await delay(200)
  return { data: mockPipelineStatus }
}

export async function getDashboardStats(): Promise<{ data: DashboardStats }> {
  await delay(100)
  return { data: mockDashboardStats }
}

export async function getRecentActivity(): Promise<{ data: RecentActivity[] }> {
  await delay(150)
  return { data: mockRecentActivity }
}

export async function getAgents(): Promise<{ data: AgentInfo[] }> {
  await delay(100)
  return { data: mockAgents }
}
