import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useQuestionnaire } from '@/features/questionnaire/useQuestionnaire'
import { QUESTIONS } from '@/features/questionnaire/questionConfig'

// Mock API
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
  upsertAnswer,
  getSession,
} from '@/features/questionnaire/api/questionnaire'

const mockCreateSession = createSession as ReturnType<typeof vi.fn>
const mockUpsertAnswer  = upsertAnswer  as ReturnType<typeof vi.fn>
const mockGetSession    = getSession    as ReturnType<typeof vi.fn>

const MOCK_SESSION = {
  id: 'sess-abc',
  status: 'in_progress' as const,
  current_question_id: null,
  current_section: 1,
  completed_count: 0,
  total_questions: 40,
  created_at: '2026-05-17T10:00:00Z',
  updated_at: '2026-05-17T10:00:00Z',
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  mockCreateSession.mockResolvedValue(MOCK_SESSION)
  mockUpsertAnswer.mockResolvedValue({ id: 'ans-1', question_id: 'q1_full_name', section_number: 1, answer_json: '"John"', answered_at: '' })
})

afterEach(() => {
  localStorage.clear()
})

describe('useQuestionnaire — initialization', () => {
  it('starts at question index 0 for a new session', async () => {
    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.currentQuestionIndex).toBe(0)
    expect(result.current.currentQuestion.id).toBe(QUESTIONS[0].id)
  })

  it('sets isAtSectionStart to true on first load', async () => {
    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.isAtSectionStart).toBe(true)
  })
})

describe('useQuestionnaire — navigation', () => {
  it('goNext advances the question index', async () => {
    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(async () => {
      await result.current.goNext()
    })

    expect(result.current.currentQuestionIndex).toBe(1)
  })

  it('goBack decrements the question index', async () => {
    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    // Advance first
    await act(async () => { await result.current.goNext() })
    expect(result.current.currentQuestionIndex).toBe(1)

    // Then go back
    act(() => { result.current.goBack() })
    expect(result.current.currentQuestionIndex).toBe(0)
  })

  it('goBack does nothing when at the first question', async () => {
    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    act(() => { result.current.goBack() })
    expect(result.current.currentQuestionIndex).toBe(0)
  })

  it('goNext on the last question of section 1 sets isAtSectionStart=true for section 2', async () => {
    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    // Advance through all 5 section-1 questions (indices 0–4)
    // After index 4 → index 5 (section 2 starts)
    for (let i = 0; i < 5; i++) {
      // eslint-disable-next-line no-await-in-loop
      await act(async () => { await result.current.goNext() })
    }

    expect(result.current.currentQuestionIndex).toBe(5)
    expect(result.current.isAtSectionStart).toBe(true)
    expect(result.current.currentQuestion.section).toBe(2)
  })

  it('goNext within the same section keeps isAtSectionStart=false', async () => {
    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    // First goNext within section 1 (index 0 → 1)
    await act(async () => { await result.current.goNext() })

    expect(result.current.isAtSectionStart).toBe(false)
    expect(result.current.currentQuestion.section).toBe(1)
  })
})

describe('useQuestionnaire — answer management', () => {
  it('setAnswer updates the answers map', async () => {
    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    act(() => { result.current.setAnswer('q1_full_name', JSON.stringify('Alice')) })

    expect(result.current.answers['q1_full_name']).toBe(JSON.stringify('Alice'))
  })
})

describe('useQuestionnaire — failed save queues to pending', () => {
  it('queues the answer to localStorage when upsertAnswer fails', async () => {
    mockUpsertAnswer.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    act(() => { result.current.setAnswer('q1_full_name', JSON.stringify('Bob')) })

    await act(async () => { await result.current.goNext() })

    // Pending saves should be in localStorage
    const pending = localStorage.getItem('pending_saves_sess-abc')
    expect(pending).toBeTruthy()
    const parsed = JSON.parse(pending!) as unknown[]
    expect(parsed).toHaveLength(1)
  })

  it('still advances index even when save fails', async () => {
    mockUpsertAnswer.mockRejectedValue(new Error('offline'))

    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(async () => { await result.current.goNext() })

    expect(result.current.currentQuestionIndex).toBe(1)
  })
})

describe('useQuestionnaire — session resume', () => {
  it('restores answers from an existing session', async () => {
    localStorage.setItem('questionnaire_session_id', 'sess-existing')
    mockGetSession.mockResolvedValue({
      session: { ...MOCK_SESSION, id: 'sess-existing', current_question_id: 'q3_sex_at_birth' },
      answers: [
        { id: 'a1', question_id: 'q1_full_name', section_number: 1, answer_json: '"Alice"', answered_at: '' },
        { id: 'a2', question_id: 'q2_date_of_birth', section_number: 1, answer_json: '"1980-01-01"', answered_at: '' },
      ],
    })

    const { result } = renderHook(() => useQuestionnaire())
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.answers['q1_full_name']).toBe('"Alice"')
    expect(result.current.answers['q2_date_of_birth']).toBe('"1980-01-01"')
  })
})
