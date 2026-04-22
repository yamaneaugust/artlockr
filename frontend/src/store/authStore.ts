import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { login as apiLogin, register as apiRegister } from '../services/api'

export interface AuthUser {
  id: number
  email: string
  username: string
  role: 'artist' | 'company' | 'admin'
  stripe_onboarded?: boolean
  company_name?: string
}

interface LocalAccount {
  id: number
  email: string
  username: string
  password: string
  role: 'artist' | 'company'
  company_name?: string
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

const ACCOUNTS_KEY = 'artlock-accounts'

function loadAccounts(): LocalAccount[] {
  try {
    const raw = localStorage.getItem(ACCOUNTS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveAccounts(accounts: LocalAccount[]): void {
  localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts))
}

async function hashPassword(password: string): Promise<string> {
  const data = new TextEncoder().encode(password)
  const buf = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

function isBackendUnreachable(err: unknown): boolean {
  const e = err as { code?: string; response?: { status?: number }; message?: string }
  if (e?.response?.status !== undefined) return false
  return true
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      login: async (email, password) => {
        try {
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
          return
        } catch (err) {
          if (!isBackendUnreachable(err)) throw err
        }

        const accounts = loadAccounts()
        const hashed = await hashPassword(password)
        const match = accounts.find(
          (a) => a.email.toLowerCase() === email.toLowerCase() && a.password === hashed,
        )
        if (!match) {
          throw {
            response: { data: { detail: 'Invalid email or password' } },
          }
        }
        set({
          user: {
            id: match.id,
            email: match.email,
            username: match.username,
            role: match.role,
            company_name: match.company_name,
          },
          isAuthenticated: true,
        })
      },

      register: async (email, username, password, role, company_name) => {
        try {
          const { data } = await apiRegister(email, username, password, role, company_name)
          set({
            user: {
              id: data.user_id,
              email,
              username: data.username,
              role: data.role,
              company_name,
            },
            isAuthenticated: true,
          })
          return
        } catch (err) {
          if (!isBackendUnreachable(err)) throw err
        }

        const accounts = loadAccounts()
        if (accounts.some((a) => a.email.toLowerCase() === email.toLowerCase())) {
          throw { response: { data: { detail: 'Email already registered' } } }
        }
        if (accounts.some((a) => a.username.toLowerCase() === username.toLowerCase())) {
          throw { response: { data: { detail: 'Username taken' } } }
        }
        const hashed = await hashPassword(password)
        const id = Date.now()
        const newAccount: LocalAccount = {
          id,
          email,
          username,
          password: hashed,
          role,
          company_name,
        }
        accounts.push(newAccount)
        saveAccounts(accounts)
        set({
          user: { id, email, username, role, company_name },
          isAuthenticated: true,
        })
      },

      logout: () => set({ user: null, isAuthenticated: false }),

      setUser: (user) => set({ user, isAuthenticated: true }),
    }),
    { name: 'artlock-auth' },
  ),
)
