import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：FormData 请求自动移除 Content-Type（让浏览器设置 boundary）
api.interceptors.request.use(config => {
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  return config
})

api.interceptors.response.use(
  response => {
    const data = response.data
    if (data.status === 'error') {
      ElMessage.error(data.message || '操作失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  error => {
    console.error('API Error:', error)
    ElMessage.error(error.message || '网络错误')
    return Promise.reject(error)
  }
)

// 系统
export const systemApi = {
  health: () => api.get('/system/health'),
  status: () => api.get('/system/status')
}

// 认证
export const authApi = {
  login: (password) => api.post('/auth/login', { password }),
  check: () => api.get('/auth/check')
}

// 配置
export const configApi = {
  get: () => api.get('/config'),
  update: (data) => api.put('/config', data),
  templates: () => api.get('/config/templates'),
  getChunk: () => api.get('/config/chunk'),
  updateChunk: (data) => api.put('/config/chunk', data)
}

// 教材目录
export const catalogApi = {
  getLevels: () => api.get('/catalog/levels'),
  getGrades: (level) => api.get(`/catalog/grades?level=${encodeURIComponent(level)}`),
  getChapters: (level, grade, semester) => {
    const params = new URLSearchParams({ level })
    if (grade) params.append('grade', grade)
    if (semester) params.append('semester', semester)
    return api.get(`/catalog/chapters?${params.toString()}`)
  }
}

// 文档
export const documentsApi = {
  list: (source = 'all') => api.get(`/documents?source=${source}`),
  upload: (files) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    return api.post('/documents/upload', formData, { timeout: 300000 })
  },
  importFiles: (files) => api.post('/documents/import', { files }),
  batchImport: (files) => api.post('/documents/batch-import', { files }),
  delete: (filePath) => api.delete(`/documents/${encodeURIComponent(filePath)}`),
  batchDelete: (files) => api.post('/documents/batch-delete', { files }),
  deleteAll: () => api.post('/documents/delete-all'),
  updateFile: (filePath) => api.post('/documents/update', { file_path: filePath }),
  sync: (source = 'all') => api.post('/documents/sync', { source }),
  rebuild: (source = 'all') => api.post('/documents/rebuild', { source }),
  cleanOrphans: () => api.post('/documents/clean-orphans'),
  orphans: () => api.get('/documents/orphans'),
  stats: () => api.get('/documents/stats'),
  detail: (source) => api.get(`/documents/detail?source=${encodeURIComponent(source)}`),
  chunks: (source) => api.get(`/documents/chunks?source=${encodeURIComponent(source)}`),
  pending: () => api.get('/documents/pending'),
  approve: (pendingId) => api.post(`/documents/approve/${pendingId}`),
  reject: (pendingId) => api.post(`/documents/reject/${pendingId}`),
  importFile: (file, category, fileType = 'other', chunkSize = 500, chunkOverlap = 50) => {
    const formData = new FormData()
    formData.append('file', file)
    if (category) formData.append('category', category)
    formData.append('file_type', fileType)
    formData.append('chunk_size', chunkSize)
    formData.append('chunk_overlap', chunkOverlap)
    return api.post('/documents/import-file', formData, { timeout: 300000 })
  },
  updateFileType: (source, fileType) => api.put('/documents/update-file-type', { source, file_type: fileType }),
  crawlWeb: (url, fileType = 'web_page', category = 'web_page') => api.post('/documents/crawl-web', { url, file_type: fileType, category })
}

// 搜索
export const searchApi = {
  search: (query, nResults = 5, category = null) => {
    const params = { query, n_results: nResults }
    if (category) params.category = category
    return api.post('/search', params)
  }
}

// 内容生成
export const generateApi = {
  speechDraft: (data) => api.post('/generate/speech-draft', data),
  lectureDraft: (data) => api.post('/generate/lecture-draft', data),
  lessonPlan: (data) => api.post('/generate/lesson-plan', data),
  studyPlan: (data) => api.post('/generate/study-plan', data)
}

// 智能问答
export const qaApi = {
  ask: (question, mode = 'teacher') => api.post('/qa', { question, mode })
}

// 服务管理
export const servicesApi = {
  start: (service) => api.post('/services/start', { service }),
  stop: (service) => api.post('/services/stop', { service })
}

export function createWebSocket(onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws`
  
  const ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('WebSocket connected')
  }
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (onMessage) {
        onMessage(data)
      }
    } catch (e) {
      console.error('WebSocket message parse error:', e)
    }
  }
  
  ws.onclose = () => {
    console.log('WebSocket disconnected')
    setTimeout(() => {
      console.log('WebSocket reconnecting...')
      createWebSocket(onMessage)
    }, 3000)
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
  
  return ws
}

export default api
