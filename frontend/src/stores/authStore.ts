import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  username: string
  first_name: string
  last_name: string
  is_active: boolean
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean

  // Actions
  setAuth: (user: User, accessToken: string, refreshToken: string) => void
  clearAuth: () => void
  updateUser: (user: Partial<User>) => void
  setLoading: (loading: boolean) => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      setAuth: (user, accessToken, refreshToken) => set({
        user,
        accessToken,
        refreshToken,
        isAuthenticated: true,
        isLoading: false,
      }),

      clearAuth: () => set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
      }),

      updateUser: (userData) => set((state) => ({
        user: state.user ? { ...state.user, ...userData } : null,
      })),

      setLoading: (loading) => set({ isLoading: loading }),

      checkAuth: async () => {
        const { accessToken, refreshToken, clearAuth, setAuth, setLoading } = get()

        if (!accessToken && !refreshToken) {
          clearAuth()
          return
        }

        if (!accessToken && refreshToken) {
          // Try to refresh the token
          setLoading(true)
          try {
            const { authApi } = await import('@/lib/api')
            const response = await authApi.refresh(refreshToken)
            const { user, access_token, refresh_token } = response.data
            setAuth(user, access_token, refresh_token)
          } catch (error) {
            clearAuth()
          } finally {
            setLoading(false)
          }
          return
        }

        if (accessToken) {
          // Validate current session
          setLoading(true)
          try {
            const { authApi } = await import('@/lib/api')
            const response = await authApi.getMe()
            set((state) => ({
              ...state,
              user: response.data,
              isAuthenticated: true,
              isLoading: false,
            }))
          } catch (error) {
            // Try refresh token if available
            if (refreshToken) {
              try {
                const { authApi } = await import('@/lib/api')
                const response = await authApi.refresh(refreshToken)
                const { user, access_token, refresh_token } = response.data
                setAuth(user, access_token, refresh_token)
              } catch (refreshError) {
                clearAuth()
              }
            } else {
              clearAuth()
            }
          } finally {
            setLoading(false)
          }
        }
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)