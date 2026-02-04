import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string, full_name?: string) =>
    api.post('/auth/register', { email, password, full_name }),
  me: () => api.get('/auth/me'),
}

// Projects API
export const projectsApi = {
  list: (params?: { page?: number; search?: string; status?: number }) =>
    api.get('/projects', { params }),
  get: (id: number) => api.get(`/projects/${id}`),
  create: (data: { name: string; description?: string; latitude?: number; longitude?: number }) =>
    api.post('/projects', data),
  update: (id: number, data: Partial<{ name: string; description: string }>) =>
    api.patch(`/projects/${id}`, data),
  delete: (id: number) => api.delete(`/projects/${id}`),
}

// Images API
export const imagesApi = {
  list: (projectId: number) => api.get(`/projects/${projectId}/images`),
  upload: (projectId: number, files: File[]) => {
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    return api.post(`/projects/${projectId}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  delete: (projectId: number, imageId: number) =>
    api.delete(`/projects/${projectId}/images/${imageId}`),
}

// Analysis API
export const analysisApi = {
  start: (projectId: number) => api.post(`/projects/${projectId}/analysis/start`),
  status: (projectId: number) => api.get(`/projects/${projectId}/analysis/status`),
  cancel: (projectId: number) => api.post(`/projects/${projectId}/analysis/cancel`),
  results: (projectId: number) => api.get(`/projects/${projectId}/analysis/results`),
}

// Types
export interface User {
  id: number
  email: string
  full_name?: string
  is_active: boolean
}

export interface Project {
  id: number
  name: string
  description?: string
  status: number
  status_name: string
  image_count: number
  pci_score?: number
  results?: Record<string, unknown>
  created_at: string
  updated_at?: string
}

export interface Image {
  id: number
  project_id: number
  original_filename: string
  url: string
  size_bytes: number
  processed: boolean
  created_at: string
}

export interface AnalysisStatus {
  task_id: string
  status: string
  progress: number
  message: string
  result?: Record<string, unknown>
}
