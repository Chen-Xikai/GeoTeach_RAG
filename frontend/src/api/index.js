import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 系统API
export const systemApi = {
  health: () => api.get('/system/health'),
  status: () => api.get('/system/status')
}

// 文档管理API
export const documentsApi = {
  list: (category) => api.get('/documents', { params: { category } }),
  importFile: (file, category = 'textbook') => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/documents/import', formData, {
      params: { category },
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  importAll: () => api.post('/documents/import-all'),
  stats: () => api.get('/documents/stats'),
  delete: (source) => api.post('/documents/delete', { source }),
  // 待审核文件API
  pending: () => api.get('/documents/pending'),
  approve: (pendingId) => api.post('/documents/approve', { pending_id: pendingId, approved: true }),
  reject: (pendingId) => api.post('/documents/approve', { pending_id: pendingId, approved: false }),
  // 同步和重建API
  sync: (category) => api.post('/documents/sync', null, { params: { category } }),
  rebuild: (category) => api.post('/documents/rebuild', null, { params: { category } }),
  orphans: () => api.get('/documents/orphans'),
  cleanOrphans: () => api.post('/documents/clean-orphans')
}

// 教材目录API
export const catalogApi = {
  getLevels: () => api.get('/catalog/levels'),
  getGrades: (level) => api.get('/catalog/grades', { params: { level } }),
  getChapters: (level, grade, semester) => api.get('/catalog/chapters', { 
    params: { level, grade, semester } 
  })
}

// 内容生成API
export const generateApi = {
  speechDraft: (data) => api.post('/generate/speech-draft', data),
  lectureDraft: (data) => api.post('/generate/lecture-draft', data),
  lessonPlan: (data) => api.post('/generate/lesson-plan', data),
  studyPlan: (data) => api.post('/generate/study-plan', data)
}

// 搜索API
export const searchApi = {
  search: (query, nResults = 5, category) => api.post('/search', { 
    query, 
    n_results: nResults, 
    category 
  })
}

// 问答API
export const qaApi = {
  ask: (question) => api.post('/qa', { question })
}

export default api
