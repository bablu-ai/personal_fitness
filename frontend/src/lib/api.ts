import axios from 'axios'
import type {
  DailyTodo, DaySummary, BenefitScoresResponse,
  DailyRow, WeeklyRow, MonthlyRow,
  UploadResponse, IngestResponse, TodoUpdateRequest,
  RotationDay, RotationWeekDay, Screening,
  TaskDetailOut, TaskTemplate,
} from '@/types'

// In development, VITE_API_URL points directly to the backend (bypasses proxy).
// In production, falls back to relative /api (served by reverse proxy).
const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api'
const client = axios.create({ baseURL: BASE_URL })

export const todosApi = {
  getToday: (): Promise<DailyTodo[]> =>
    client.get('/todos/today').then(r => r.data),

  getNecessarySupplements: (): Promise<DailyTodo[]> =>
    client.get('/todos/supplements/necessary').then(r => r.data),

  getTodaySummary: (): Promise<DaySummary> =>
    client.get(`/todos/${new Date().toISOString().split('T')[0]}/summary`).then(r => r.data),

  update: (id: string, body: TodoUpdateRequest): Promise<DailyTodo> =>
    client.patch(`/todos/${id}`, body).then(r => r.data),

  getDetail: (templateId: string): Promise<TaskDetailOut> =>
    client.get(`/tasks/${templateId}/detail`).then(r => r.data),
}

export const referenceApi = {
  getAll: (): Promise<TaskTemplate[]> =>
    client.get('/reference').then(r => r.data),
}

export const benefitsApi = {
  getToday: (): Promise<BenefitScoresResponse> =>
    client.get('/benefits/today').then(r => r.data),
}

export const dashboardApi = {
  getDaily: (days = 30): Promise<DailyRow[]> =>
    client.get('/dashboard/daily', { params: { days } }).then(r => r.data),

  getWeekly: (weeks = 12): Promise<WeeklyRow[]> =>
    client.get('/dashboard/weekly', { params: { weeks } }).then(r => r.data),

  getMonthly: (months = 6): Promise<MonthlyRow[]> =>
    client.get('/dashboard/monthly', { params: { months } }).then(r => r.data),
}

export const uploadApi = {
  uploadPlan: (file: File, rotationStartDate?: string): Promise<UploadResponse> => {
    const form = new FormData()
    form.append('file', file)
    if (rotationStartDate) form.append('rotation_start_date', rotationStartDate)
    return client.post('/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
}

export const agentApi = {
  chat: (message: string): Promise<string> =>
    client.post('/agent/chat', { message }).then(r => r.data.reply),

  ingest: (file: File, rotationStartDate?: string): Promise<IngestResponse> => {
    const form = new FormData()
    form.append('file', file)
    if (rotationStartDate) form.append('rotation_start_date', rotationStartDate)
    return client.post('/agent/ingest', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
}

export const rotationApi = {
  getToday: (): Promise<RotationDay | null> =>
    client.get('/rotation/today').then(r => r.data),

  getWeek: (weekStart?: string): Promise<RotationWeekDay[]> =>
    client.get('/rotation/week', { params: weekStart ? { week_start: weekStart } : {} }).then(r => r.data),

  setStartDate: (date: string): Promise<void> =>
    client.patch('/rotation/start', { rotation_start_date: date }).then(r => r.data),

  markCompleted: (dayNumber: number, completed: boolean, targetDate?: string): Promise<void> =>
    client.patch('/rotation/complete', {
      day_number: dayNumber,
      completed,
      ...(targetDate ? { target_date: targetDate } : {}),
    }).then(r => r.data),
}

export const screeningsApi = {
  getDue: (): Promise<Screening[]> =>
    client.get('/screenings/due').then(r => r.data),

  getAll: (): Promise<Screening[]> =>
    client.get('/screenings').then(r => r.data),

  markDone: (id: string, completedDate?: string, notes?: string): Promise<Screening> =>
    client.post(`/screenings/${id}/done`, { completed_date: completedDate, notes }).then(r => r.data),
}
