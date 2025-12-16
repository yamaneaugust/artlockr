import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  name: string
  role: 'artist' | 'admin'
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User, token: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        // TODO: Replace with actual API call
        const mockUser: User = {
          id: '1',
          email,
          name: 'Test Artist',
          role: 'artist',
        }
        const mockToken = 'mock-jwt-token'

        set({
          user: mockUser,
          token: mockToken,
          isAuthenticated: true,
        })
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
      },

      setUser: (user: User, token: string) => {
        set({
          user,
          token,
          isAuthenticated: true,
        })
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)
