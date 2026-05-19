import axios from 'axios'

// In development, VITE_API_URL points directly to the backend (bypasses proxy).
// In production, falls back to relative /api (served by reverse proxy).
const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api'
const authClient = axios.create({ baseURL: BASE_URL })

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
}

export interface UserRead {
  id: string
  email: string
  created_at: string
}

export async function registerUser(email: string, password: string): Promise<TokenResponse> {
  const res = await authClient.post<TokenResponse>('/auth/register', { email, password })
  return res.data
}

export async function loginUser(email: string, password: string): Promise<TokenResponse> {
  const res = await authClient.post<TokenResponse>('/auth/login', { email, password })
  return res.data
}

export async function getCurrentUser(token: string): Promise<UserRead> {
  const res = await authClient.get<UserRead>('/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  })
  return res.data
}
