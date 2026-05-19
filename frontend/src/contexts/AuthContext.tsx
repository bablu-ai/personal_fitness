import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { ReactNode } from 'react'
import { loginUser, registerUser } from '@/api/auth'
import { setAuthToken } from '@/features/questionnaire/api/questionnaire'

// TODO[SECURITY]: In Phase 2, store token in memory only and use httpOnly cookie
// for the refresh token. Remove sessionStorage mirror entirely.
let _token: string | null = null

const SESSION_KEY = 'longevity_auth'

interface StoredSession {
  userId: string
  email: string
  accessToken: string
}

function readSession(): StoredSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (!raw) return null
    return JSON.parse(raw) as StoredSession
  } catch {
    return null
  }
}

function writeSession(s: StoredSession): void {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(s))
  } catch {
    // sessionStorage may be unavailable in some browser contexts
  }
}

function clearSession(): void {
  try {
    sessionStorage.removeItem(SESSION_KEY)
  } catch {
    // ignore
  }
}

interface AuthState {
  userId: string | null
  email: string | null
  accessToken: string | null
  isAuthenticated: boolean
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [state, setState] = useState<AuthState>(() => {
    // Restore session from sessionStorage on first render
    const stored = readSession()
    if (stored) {
      _token = stored.accessToken
      setAuthToken(stored.accessToken)
      return {
        userId: stored.userId,
        email: stored.email,
        accessToken: stored.accessToken,
        isAuthenticated: true,
      }
    }
    return { userId: null, email: null, accessToken: null, isAuthenticated: false }
  })

  // Sync module-level variable whenever state changes
  useEffect(() => {
    _token = state.accessToken
    setAuthToken(state.accessToken)
  }, [state.accessToken])

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    const res = await loginUser(email, password)
    const stored: StoredSession = {
      userId: res.user_id,
      email,
      accessToken: res.access_token,
    }
    writeSession(stored)
    setState({
      userId: res.user_id,
      email,
      accessToken: res.access_token,
      isAuthenticated: true,
    })
  }, [])

  const register = useCallback(async (email: string, password: string): Promise<void> => {
    const res = await registerUser(email, password)
    const stored: StoredSession = {
      userId: res.user_id,
      email,
      accessToken: res.access_token,
    }
    writeSession(stored)
    setState({
      userId: res.user_id,
      email,
      accessToken: res.access_token,
      isAuthenticated: true,
    })
  }, [])

  const logout = useCallback((): void => {
    _token = null
    setAuthToken(null)
    clearSession()
    setState({ userId: null, email: null, accessToken: null, isAuthenticated: false })
  }, [])

  const value: AuthContextValue = { ...state, login, register, logout }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// Export the raw token accessor for non-React code that needs the bearer token
export const getToken = (): string | null => _token
