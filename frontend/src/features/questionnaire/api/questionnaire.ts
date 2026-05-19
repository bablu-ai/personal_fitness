import axios from 'axios'
import type { QuestionnaireSession, SessionDetail, SessionAnswer, GenerateResult } from '../types'

// Token injected at runtime via setAuthToken() called from AuthContext.
// The interceptor below attaches it to every request on this client.
// TODO[SECURITY]: replace with httpOnly cookie + silent refresh in Phase 2.
let _authToken: string | null = null

export const setAuthToken = (token: string | null): void => {
  _authToken = token
}

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api'

const client = axios.create({ baseURL: BASE_URL })

client.interceptors.request.use(config => {
  if (_authToken) {
    config.headers = config.headers ?? {}
    config.headers['Authorization'] = `Bearer ${_authToken}`
  }
  return config
})

const BASE = '/questionnaire'

export const createSession = async (): Promise<QuestionnaireSession> => {
  const res = await client.post<QuestionnaireSession>(`${BASE}/sessions`)
  return res.data
}

export const listSessions = async (): Promise<QuestionnaireSession[]> => {
  const res = await client.get<QuestionnaireSession[]>(`${BASE}/sessions`)
  return res.data
}

export const getSession = async (id: string): Promise<SessionDetail> => {
  const res = await client.get<SessionDetail>(`${BASE}/sessions/${id}`)
  return res.data
}

export const upsertAnswer = async (
  sessionId: string,
  questionId: string,
  answerJson: string,
  sectionNumber: number,
): Promise<SessionAnswer> => {
  const res = await client.put<SessionAnswer>(
    `${BASE}/sessions/${sessionId}/answers`,
    { question_id: questionId, answer_json: answerJson, section_number: sectionNumber },
  )
  return res.data
}

export const generateWorkbook = async (sessionId: string): Promise<GenerateResult> => {
  const res = await client.post<GenerateResult>(`${BASE}/sessions/${sessionId}/generate`)
  return res.data
}

export const getDownloadUrl = (token: string): string =>
  `${BASE_URL}${BASE}/download/${token}`
