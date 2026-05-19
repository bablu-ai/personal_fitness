import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import QuestionnairePage from '@/features/questionnaire/QuestionnairePage'
import { QUESTIONS } from '@/features/questionnaire/questionConfig'

// Mock the questionnaire API
vi.mock('@/features/questionnaire/api/questionnaire', () => ({
  createSession: vi.fn(),
  getSession: vi.fn(),
  upsertAnswer: vi.fn(),
  generateWorkbook: vi.fn(),
  listSessions: vi.fn(),
  getDownloadUrl: vi.fn(),
  setAuthToken: vi.fn(),
}))

import {
  createSession,
  getSession,
} from '@/features/questionnaire/api/questionnaire'

const mockCreateSession = createSession as ReturnType<typeof vi.fn>
const mockGetSession = getSession as ReturnType<typeof vi.fn>

const MOCK_SESSION = {
  id: 'sess-page-test',
  status: 'in_progress' as const,
  current_question_id: null,
  current_section: 1,
  completed_count: 0,
  total_questions: 40,
  created_at: '2026-05-17T10:00:00Z',
  updated_at: '2026-05-17T10:00:00Z',
}

function renderPage(path = '/workbook/new') {
  const routePath = path.startsWith('/workbook/') ? '/workbook/:sessionId' : '/workbook'
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={routePath} element={<QuestionnairePage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  mockCreateSession.mockResolvedValue(MOCK_SESSION)
})

afterEach(() => {
  localStorage.clear()
})

describe('QuestionnairePage — new session', () => {
  it('shows the first section overview on first load', async () => {
    renderPage('/workbook/new')
    // Loading skeleton visible first, then section overview
    await waitFor(() => {
      // Section 1 overview should appear, not a question screen
      expect(screen.queryByText('Q1 of 40')).not.toBeInTheDocument()
    })
  })
})

describe('QuestionnairePage — session resume', () => {
  it('shows the saved question directly without flashing SectionOverviewScreen', async () => {
    // Set up an existing session resumed mid-section (q3 = index 2, still section 1)
    localStorage.setItem('questionnaire_session_id', 'sess-resume')
    const resumedQuestion = QUESTIONS[2] // q3_sex_at_birth, section 1, not first of section
    mockGetSession.mockResolvedValue({
      session: {
        ...MOCK_SESSION,
        id: 'sess-resume',
        current_question_id: resumedQuestion.id,
      },
      answers: [],
    })

    renderPage('/workbook/new')

    // After loading, should show the question screen (Q3), not the section overview
    await waitFor(() => {
      expect(screen.getByText(`Q${resumedQuestion.number} of 40`)).toBeInTheDocument()
    })

    // The section overview "Continue" button must NOT be present
    expect(screen.queryByRole('button', { name: /continue/i })).not.toBeInTheDocument()
  })

  it('shows SectionOverviewScreen when resuming at the first question of a new section', async () => {
    // Find the first question of section 2
    const firstOfSection2 = QUESTIONS.find(q => q.section === 2)!
    localStorage.setItem('questionnaire_session_id', 'sess-resume-section')
    mockGetSession.mockResolvedValue({
      session: {
        ...MOCK_SESSION,
        id: 'sess-resume-section',
        current_question_id: firstOfSection2.id,
        current_section: 2,
      },
      answers: [],
    })

    renderPage('/workbook/new')

    // Should show the section overview, not the question screen
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /continue/i })).toBeInTheDocument()
    })
    expect(screen.queryByText(`Q${firstOfSection2.number} of 40`)).not.toBeInTheDocument()
  })
})
