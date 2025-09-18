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

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const { refreshToken, clearAuth, setAuth } = useAuthStore.getState()

      if (refreshToken) {
        try {
          // Attempt to refresh the token
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken
          })

          const { user, access_token, refresh_token } = response.data
          setAuth(user, access_token, refresh_token)

          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, clear auth and redirect
          clearAuth()
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login'
          }
        }
      } else {
        // No refresh token, clear auth and redirect
        clearAuth()
        if (typeof window !== 'undefined') {
          window.location.href = '/auth/login'
        }
      }
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

  refresh: (refreshToken: string) => api.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),

  logout: () => api.post('/api/v1/auth/logout'),
}

// Settings API
export const settingsApi = {
  // Profile endpoints
  getProfile: () => api.get('/api/v1/settings/profile'),
  updateProfile: (data: any) => api.put('/api/v1/settings/profile', data),

  // Preferences endpoints
  getPreferences: () => api.get('/api/v1/settings/preferences'),
  updatePreferences: (data: any) => api.put('/api/v1/settings/preferences', data),

  // Account endpoints
  getAccount: () => api.get('/api/v1/settings/account'),
  updateAccount: (data: any) => api.put('/api/v1/settings/account', data),
  deleteAccount: () => api.delete('/api/v1/settings/account'),

  // Integrations endpoints
  getIntegrations: () => api.get('/api/v1/settings/integrations'),
  getAvailableIntegrations: () => api.get('/api/v1/settings/integrations/available'),
  getSyncStatus: () => api.get('/api/v1/settings/integrations/sync-status'),
  testIntegration: (serviceName: string, config: any) =>
    api.post(`/api/v1/settings/integrations/${serviceName}/test`, config),
  setupIntegration: (serviceName: string, config: any) =>
    api.post('/api/v1/settings/integrations/setup', { service_name: serviceName, config }),
  toggleIntegration: (integrationId: string) =>
    api.put(`/api/v1/settings/integrations/${integrationId}/toggle`),
  syncIntegration: (integrationId: string, fullSync?: boolean) =>
    api.post(`/api/v1/settings/integrations/${integrationId}/sync`, { full_sync: fullSync }),
  syncAllIntegrations: () => api.post('/api/v1/settings/integrations/sync'),

  // Data management endpoints
  exportData: () => api.get('/api/v1/settings/export', { responseType: 'blob' }),
  importData: (data: any) => api.post('/api/v1/settings/import', data),
  clearCache: () => api.post('/api/v1/settings/clear-cache'),

  // Context documents
  getContextDocuments: () => api.get('/api/v1/settings/context-documents'),
  uploadContextDocument: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/v1/settings/context-documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  deleteContextDocument: (documentId: string) =>
    api.delete(`/api/v1/settings/context-documents/${documentId}`)
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
