import axios, { AxiosError } from 'axios'
import { getToken } from '@/contexts/AuthContext'

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api'
const client = axios.create({ baseURL: BASE_URL })

client.interceptors.request.use(config => {
  const token = getToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface AdminQuestionnaireSession {
  id: string
  user_id: string
  user_email: string | null
  status: string
  completed_count: number
  total_questions: number
  questionnaire_version: number
  created_at: string
  updated_at: string
}

export interface AdminQuestionAnswer {
  question_id: string
  question_snapshot_id: string | null
  section_number: number
  question_number: number
  question_text: string
  question_type: string
  answer_json: string | null
  formatted_answer: string | null
  answered_at: string | null
}

export interface AdminQuestionnaireDetail {
  session: AdminQuestionnaireSession
  questions: AdminQuestionAnswer[]
}

const BASE = '/admin/questionnaires'

export const isForbidden = (error: unknown): boolean =>
  error instanceof AxiosError && error.response?.status === 403

export const listAdminQuestionnaireSessions = async (): Promise<AdminQuestionnaireSession[]> => {
  const res = await client.get<AdminQuestionnaireSession[]>(`${BASE}/sessions`)
  return res.data
}

export const getAdminQuestionnaireSession = async (
  sessionId: string,
): Promise<AdminQuestionnaireDetail> => {
  const res = await client.get<AdminQuestionnaireDetail>(`${BASE}/sessions/${sessionId}`)
  return res.data
}

export const downloadQuestionnaireExport = async (sessionId: string): Promise<void> => {
  const res = await client.get<Blob>(`${BASE}/sessions/${sessionId}/export.txt`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(res.data)
  const link = document.createElement('a')
  link.href = url
  link.download = `questionnaire_${sessionId}.txt`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
