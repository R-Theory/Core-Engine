import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const { accessToken } = useAuthStore.getState()
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, clear auth state
      useAuthStore.getState().clearAuth()
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (email: string, password: string) => {
    // Backend expects OAuth2PasswordRequestForm (form-encoded), not JSON
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    return api.post('/api/v1/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  
  register: (data: {
    email: string
    username: string
    password: string
    first_name: string
    last_name: string
  }) => api.post('/api/v1/auth/register', data),
  
  getMe: () => api.get('/api/v1/auth/me'),
}

// Courses API
export const coursesApi = {
  getCourses: () => api.get('/api/v1/courses'),
  getCourse: (id: string) => api.get(`/api/v1/courses/${id}`),
  createCourse: (data: any) => api.post('/api/v1/courses', data),
  updateCourse: (id: string, data: any) => api.put(`/api/v1/courses/${id}`, data),
  deleteCourse: (id: string) => api.delete(`/api/v1/courses/${id}`),
  getLiveMap: (id: string) => api.get(`/api/v1/courses/${id}/live-map`),
}

// Assignments API
export const assignmentsApi = {
  getAssignments: (params?: any) => api.get('/api/v1/assignments', { params }),
  createAssignment: (data: any) => api.post('/api/v1/assignments', data),
  updateAssignment: (id: string, data: any) => api.put(`/api/v1/assignments/${id}`, data),
  deleteAssignment: (id: string) => api.delete(`/api/v1/assignments/${id}`),
}

// Resources API
export const resourcesApi = {
  getResources: (params?: any) => api.get('/api/v1/resources', { params }),
  createResource: (data: any) => api.post('/api/v1/resources', data),
  uploadFile: (formData: FormData) => api.post('/api/v1/resources/upload', formData),
  updateResource: (id: string, data: any) => api.put(`/api/v1/resources/${id}`, data),
  deleteResource: (id: string) => api.delete(`/api/v1/resources/${id}`),
  searchResources: (query: string) => api.get(`/api/v1/resources/search/fulltext?q=${query}`),
}

// Workflows API
export const workflowsApi = {
  getWorkflows: () => api.get('/api/v1/workflows'),
  createWorkflow: (data: any) => api.post('/api/v1/workflows', data),
  updateWorkflow: (id: string, data: any) => api.put(`/api/v1/workflows/${id}`, data),
  deleteWorkflow: (id: string) => api.delete(`/api/v1/workflows/${id}`),
  executeWorkflow: (id: string, params?: any) => api.post(`/api/v1/workflows/${id}/execute`, { params }),
  getExecutions: (id: string) => api.get(`/api/v1/workflows/${id}/executions`),
}

// Plugins API
export const pluginsApi = {
  getPlugins: () => api.get('/api/v1/plugins'),
  installPlugin: (data: any) => api.post('/api/v1/plugins', data),
  updateConfig: (id: string, data: any) => api.put(`/api/v1/plugins/${id}/config`, data),
  activatePlugin: (id: string) => api.post(`/api/v1/plugins/${id}/activate`),
  deactivatePlugin: (id: string) => api.post(`/api/v1/plugins/${id}/deactivate`),
  executeAction: (id: string, data: any) => api.post(`/api/v1/plugins/${id}/execute`, data),
}

// AI Agents API
export const agentsApi = {
  getAgents: () => api.get('/api/v1/agents'),
  getAgent: (name: string) => api.get(`/api/v1/agents/${name}`),
  interact: (name: string, data: any) => api.post(`/api/v1/agents/${name}/interact`, data),
  batchInteract: (requests: any[]) => api.post('/api/v1/agents/batch-interact', { requests }),
}
