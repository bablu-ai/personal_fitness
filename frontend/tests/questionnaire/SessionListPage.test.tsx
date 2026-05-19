import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import SessionListPage from '@/features/questionnaire/SessionListPage'
import type { QuestionnaireSession } from '@/features/questionnaire/types'

// Mock the questionnaire API
vi.mock('@/features/questionnaire/api/questionnaire', () => ({
  listSessions: vi.fn(),
  createSession: vi.fn(),
  getSession: vi.fn(),
  upsertAnswer: vi.fn(),
  generateWorkbook: vi.fn(),
  getDownloadUrl: vi.fn(),
  setAuthToken: vi.fn(),
}))

import { listSessions } from '@/features/questionnaire/api/questionnaire'
const mockListSessions = listSessions as ReturnType<typeof vi.fn>

function makeSession(overrides: Partial<QuestionnaireSession> = {}): QuestionnaireSession {
  return {
    id: 'sess-1',
    status: 'in_progress',
    current_question_id: 'q5_weight_kg',
    current_section: 1,
    completed_count: 5,
    total_questions: 40,
    created_at: '2026-05-17T10:00:00Z',
    updated_at: '2026-05-17T10:05:00Z',
    ...overrides,
  }
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <SessionListPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

beforeEach(() => {
  mockListSessions.mockReset()
})

describe('SessionListPage', () => {
  it('shows "Start New Questionnaire" button', async () => {
    mockListSessions.mockResolvedValue([])
    renderPage()
    expect(await screen.findByRole('link', { name: /start new questionnaire/i })).toBeInTheDocument()
  })

  it('shows a list of past sessions when sessions exist', async () => {
    mockListSessions.mockResolvedValue([
      makeSession({ id: 'sess-1', completed_count: 20 }),
      makeSession({ id: 'sess-2', status: 'plan_generated', completed_count: 40 }),
    ])
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('20/40 answered')).toBeInTheDocument()
    })
    expect(screen.getByText('40/40 answered')).toBeInTheDocument()
  })

  it('shows "Resume" link for in_progress sessions', async () => {
    mockListSessions.mockResolvedValue([makeSession({ status: 'in_progress' })])
    renderPage()
    expect(await screen.findByRole('link', { name: /resume/i })).toBeInTheDocument()
  })

  it('shows "View" link for completed/plan_generated sessions', async () => {
    mockListSessions.mockResolvedValue([makeSession({ status: 'plan_generated', completed_count: 40 })])
    renderPage()
    expect(await screen.findByRole('link', { name: /view/i })).toBeInTheDocument()
  })

  it('shows "In Progress" status badge', async () => {
    mockListSessions.mockResolvedValue([makeSession({ status: 'in_progress' })])
    renderPage()
    expect(await screen.findByText('In Progress')).toBeInTheDocument()
  })

  it('shows "Plan Ready" status badge for plan_generated sessions', async () => {
    mockListSessions.mockResolvedValue([makeSession({ status: 'plan_generated', completed_count: 40 })])
    renderPage()
    expect(await screen.findByText('Plan Ready')).toBeInTheDocument()
  })

  it('shows error message when API fails', async () => {
    mockListSessions.mockRejectedValue(new Error('Network error'))
    renderPage()
    expect(await screen.findByText(/could not load your sessions/i)).toBeInTheDocument()
  })

  it('shows empty state message when no sessions exist', async () => {
    mockListSessions.mockResolvedValue([])
    renderPage()
    expect(await screen.findByText(/no questionnaires yet/i)).toBeInTheDocument()
  })
})
