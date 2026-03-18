import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { login as apiLogin, register as apiRegister } from '../services/api'

export interface AuthUser {
  id: number
  email: string
  username: string
  role: 'artist' | 'company' | 'admin'
  stripe_onboarded?: boolean
}

interface AuthState {
  user: AuthUser | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (
    email: string,
    username: string,
    password: string,
    role: 'artist' | 'company',
    company_name?: string,
  ) => Promise<void>
  logout: () => void
  setUser: (user: AuthUser) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const { data } = await apiLogin(email, password)
        set({
          user: {
            id: data.user_id,
            email: data.email,
            username: data.username,
            role: data.role,
            stripe_onboarded: data.stripe_onboarded,
          },
          isAuthenticated: true,
        })
      },

      register: async (email, username, password, role, company_name) => {
        const { data } = await apiRegister(email, username, password, role, company_name)
        set({
          user: {
            id: data.user_id,
            email,
            username: data.username,
            role: data.role,
          },
          isAuthenticated: true,
        })
      },

      logout: () => set({ user: null, isAuthenticated: false }),

      setUser: (user) => set({ user, isAuthenticated: true }),
    }),
    { name: 'artlockr-auth' },
  ),
)
