import { create } from 'zustand'
import { AxiosError } from 'axios'
import { api } from '../lib/api'
import type { User, RegisterPayload, LoginPayload } from '../types/auth'

interface AuthState {
  user: User | null
  isLoading: boolean
  // Has the initial "am I already logged in?" check (fetchCurrentUser on
  // app load) finished? Needed so we don't flash a "logged out" UI for a
  // moment before we've actually checked — see App.tsx.
  isInitialized: boolean

  login: (data: LoginPayload) => Promise<void>
  register: (data: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
  fetchCurrentUser: () => Promise<void>
}

// Backend errors come back as { detail: "..." } (FastAPI's HTTPException
// shape) or, for Pydantic validation errors, { detail: [{ msg: "..." }, ...] }.
function extractErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  }
  return fallback
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  isInitialized: false,

  login: async (data) => {
    set({ isLoading: true })
    try {
      const response = await api.post('/auth/login', data)
      set({ user: response.data.user, isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw new Error(extractErrorMessage(error, 'Login failed'))
    }
  },

  register: async (data) => {
    set({ isLoading: true })
    try {
      await api.post('/auth/register', data)
      // The backend's /auth/register only creates the account — it doesn't
      // set the auth cookie. Log in immediately after with the same
      // credentials so the user doesn't have to submit them twice.
      const loginResponse = await api.post('/auth/login', {
        email: data.email,
        password: data.password,
      })
      set({ user: loginResponse.data.user, isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw new Error(extractErrorMessage(error, 'Registration failed'))
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      // Clear local state regardless of whether the request succeeded —
      // the user's intent is to be logged out either way.
      set({ user: null })
    }
  },

  fetchCurrentUser: async () => {
    try {
      const response = await api.get<User>('/auth/me')
      set({ user: response.data, isInitialized: true })
    } catch {
      // No valid cookie / not logged in — this is an expected outcome
      // on first load for anonymous visitors, not an error to surface.
      set({ user: null, isInitialized: true })
    }
  },
}))
