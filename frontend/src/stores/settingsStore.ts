import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/lib/api'

// Types
interface UserProfile {
  university?: string
  student_id?: string
  academic_year?: string
  major?: string
  personal_bio?: string
  current_courses?: string
  learning_style?: string
  experience_level?: string
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  timezone?: string
  email_notifications: boolean
  push_notifications: boolean
  workflow_notifications: boolean
  assignment_reminders: boolean
  default_ai_model?: string
  ai_response_style: string
  data_sharing_analytics: boolean
  public_profile: boolean
}

interface Integration {
  id: string
  service_name: string
  display_name: string
  is_connected: boolean
  connection_status: 'connected' | 'disconnected' | 'error' | 'testing'
  last_sync?: string
  connection_error?: string
}

interface CanvasConfig {
  active_canvas_id?: string
  canvas_instances: Array<{
    id: string
    name: string
    base_url: string
    is_active: boolean
  }>
}

interface SettingsState {
  // Data
  profile: UserProfile
  preferences: UserPreferences
  integrations: Integration[]
  canvasConfig: CanvasConfig

  // UI State
  loading: {
    profile: boolean
    preferences: boolean
    integrations: boolean
    saving: boolean
  }

  errors: {
    profile?: string
    preferences?: string
    integrations?: string
  }

  // Actions
  loadProfile: () => Promise<void>
  saveProfile: (profile: Partial<UserProfile>) => Promise<void>
  updateProfile: (profile: Partial<UserProfile>) => void

  loadPreferences: () => Promise<void>
  savePreferences: (preferences: Partial<UserPreferences>) => Promise<void>
  updatePreferences: (preferences: Partial<UserPreferences>) => void

  loadIntegrations: () => Promise<void>
  testIntegration: (serviceName: string, config: Record<string, string>) => Promise<boolean>
  saveIntegration: (serviceName: string, config: Record<string, string>) => Promise<void>
  toggleIntegration: (integrationId: string) => Promise<void>

  setActiveCanvas: (canvasId: string) => void
  addCanvasInstance: (instance: { name: string, base_url: string }) => void
  removeCanvasInstance: (instanceId: string) => void

  // Utility actions
  setLoading: (key: keyof SettingsState['loading'], value: boolean) => void
  setError: (key: keyof SettingsState['errors'], error?: string) => void
  clearErrors: () => void

  // Reset functions
  resetProfile: () => void
  resetPreferences: () => void
}

const defaultProfile: UserProfile = {
  university: '',
  student_id: '',
  academic_year: '',
  major: '',
  personal_bio: '',
  current_courses: '',
  learning_style: 'mixed',
  experience_level: 'intermediate'
}

const defaultPreferences: UserPreferences = {
  theme: 'system',
  language: 'en',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  email_notifications: true,
  push_notifications: true,
  workflow_notifications: true,
  assignment_reminders: true,
  default_ai_model: 'gpt-4',
  ai_response_style: 'detailed',
  data_sharing_analytics: false,
  public_profile: false
}

const defaultCanvasConfig: CanvasConfig = {
  active_canvas_id: undefined,
  canvas_instances: []
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      // Initial state
      profile: defaultProfile,
      preferences: defaultPreferences,
      integrations: [],
      canvasConfig: defaultCanvasConfig,

      loading: {
        profile: false,
        preferences: false,
        integrations: false,
        saving: false
      },

      errors: {},

      // Profile actions
      loadProfile: async () => {
        set(state => ({ loading: { ...state.loading, profile: true } }))
        get().setError('profile', undefined)

        try {
          const response = await api.get('/api/v1/settings/profile')
          set(state => ({
            profile: { ...defaultProfile, ...response.data },
            loading: { ...state.loading, profile: false }
          }))
        } catch (error: any) {
          get().setError('profile', error?.response?.data?.detail || 'Failed to load profile')
          set(state => ({ loading: { ...state.loading, profile: false } }))
        }
      },

      saveProfile: async (profileUpdate: Partial<UserProfile>) => {
        set(state => ({ loading: { ...state.loading, saving: true } }))
        get().setError('profile', undefined)

        try {
          const response = await api.put('/api/v1/settings/profile', profileUpdate)
          set(state => ({
            profile: { ...state.profile, ...response.data },
            loading: { ...state.loading, saving: false }
          }))
        } catch (error: any) {
          get().setError('profile', error?.response?.data?.detail || 'Failed to save profile')
          set(state => ({ loading: { ...state.loading, saving: false } }))
          throw error
        }
      },

      updateProfile: (profileUpdate: Partial<UserProfile>) => {
        set(state => ({
          profile: { ...state.profile, ...profileUpdate }
        }))
      },

      // Preferences actions
      loadPreferences: async () => {
        set(state => ({ loading: { ...state.loading, preferences: true } }))
        get().setError('preferences', undefined)

        try {
          const response = await api.get('/api/v1/settings/preferences')
          set(state => ({
            preferences: { ...defaultPreferences, ...response.data },
            loading: { ...state.loading, preferences: false }
          }))
        } catch (error: any) {
          get().setError('preferences', error?.response?.data?.detail || 'Failed to load preferences')
          set(state => ({ loading: { ...state.loading, preferences: false } }))
        }
      },

      savePreferences: async (preferencesUpdate: Partial<UserPreferences>) => {
        set(state => ({ loading: { ...state.loading, saving: true } }))
        get().setError('preferences', undefined)

        try {
          const response = await api.put('/api/v1/settings/preferences', preferencesUpdate)
          set(state => ({
            preferences: { ...state.preferences, ...response.data },
            loading: { ...state.loading, saving: false }
          }))
        } catch (error: any) {
          get().setError('preferences', error?.response?.data?.detail || 'Failed to save preferences')
          set(state => ({ loading: { ...state.loading, saving: false } }))
          throw error
        }
      },

      updatePreferences: (preferencesUpdate: Partial<UserPreferences>) => {
        set(state => ({
          preferences: { ...state.preferences, ...preferencesUpdate }
        }))
      },

      // Integration actions
      loadIntegrations: async () => {
        set(state => ({ loading: { ...state.loading, integrations: true } }))
        get().setError('integrations', undefined)

        try {
          const response = await api.get('/api/v1/settings/integrations')
          set(state => ({
            integrations: response.data,
            loading: { ...state.loading, integrations: false }
          }))
        } catch (error: any) {
          get().setError('integrations', error?.response?.data?.detail || 'Failed to load integrations')
          set(state => ({ loading: { ...state.loading, integrations: false } }))
        }
      },

      testIntegration: async (serviceName: string, config: Record<string, string>) => {
        try {
          const response = await api.post(`/api/v1/settings/integrations/${serviceName}/test`, config)
          return response.data.status === 'success'
        } catch (error) {
          return false
        }
      },

      saveIntegration: async (serviceName: string, config: Record<string, string>) => {
        set(state => ({ loading: { ...state.loading, saving: true } }))
        get().setError('integrations', undefined)

        try {
          await api.post('/api/v1/settings/integrations/setup', {
            service_name: serviceName,
            config
          })

          // Reload integrations to get updated state
          await get().loadIntegrations()

          set(state => ({ loading: { ...state.loading, saving: false } }))
        } catch (error: any) {
          get().setError('integrations', error?.response?.data?.detail || 'Failed to save integration')
          set(state => ({ loading: { ...state.loading, saving: false } }))
          throw error
        }
      },

      toggleIntegration: async (integrationId: string) => {
        try {
          await api.put(`/api/v1/settings/integrations/${integrationId}/toggle`)
          await get().loadIntegrations()
        } catch (error: any) {
          get().setError('integrations', error?.response?.data?.detail || 'Failed to toggle integration')
          throw error
        }
      },

      // Canvas configuration actions
      setActiveCanvas: (canvasId: string) => {
        set(state => ({
          canvasConfig: {
            ...state.canvasConfig,
            active_canvas_id: canvasId
          }
        }))
      },

      addCanvasInstance: (instance: { name: string, base_url: string }) => {
        const newInstance = {
          id: `canvas_${Date.now()}`,
          ...instance,
          is_active: false
        }

        set(state => ({
          canvasConfig: {
            ...state.canvasConfig,
            canvas_instances: [...state.canvasConfig.canvas_instances, newInstance]
          }
        }))
      },

      removeCanvasInstance: (instanceId: string) => {
        set(state => ({
          canvasConfig: {
            ...state.canvasConfig,
            canvas_instances: state.canvasConfig.canvas_instances.filter(
              instance => instance.id !== instanceId
            ),
            active_canvas_id: state.canvasConfig.active_canvas_id === instanceId
              ? undefined
              : state.canvasConfig.active_canvas_id
          }
        }))
      },

      // Utility actions
      setLoading: (key: keyof SettingsState['loading'], value: boolean) => {
        set(state => ({
          loading: { ...state.loading, [key]: value }
        }))
      },

      setError: (key: keyof SettingsState['errors'], error?: string) => {
        set(state => ({
          errors: { ...state.errors, [key]: error }
        }))
      },

      clearErrors: () => {
        set({ errors: {} })
      },

      // Reset functions
      resetProfile: () => {
        set({ profile: defaultProfile })
      },

      resetPreferences: () => {
        set({ preferences: defaultPreferences })
      }
    }),
    {
      name: 'settings-storage',
      partialize: (state) => ({
        preferences: state.preferences,
        canvasConfig: state.canvasConfig
      })
    }
  )
)