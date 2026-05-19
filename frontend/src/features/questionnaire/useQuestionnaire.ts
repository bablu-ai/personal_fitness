import { useState, useEffect, useCallback, useRef } from 'react'
import { QUESTIONS } from './questionConfig'
import type { Question, QuestionnaireSession, GenerateResult } from './types'
import {
  createSession,
  getSession,
  upsertAnswer,
  generateWorkbook,
} from './api/questionnaire'

// ─── localStorage keys ────────────────────────────────────────────────────────
const SESSION_ID_KEY = 'questionnaire_session_id'

interface PendingSave {
  sessionId: string
  questionId: string
  answerJson: string
  sectionNumber: number
}

const PENDING_KEY = (sessionId: string) => `pending_saves_${sessionId}`

function readPending(sessionId: string): PendingSave[] {
  try {
    const raw = localStorage.getItem(PENDING_KEY(sessionId))
    return raw ? (JSON.parse(raw) as PendingSave[]) : []
  } catch {
    return []
  }
}

function writePending(sessionId: string, items: PendingSave[]): void {
  try {
    localStorage.setItem(PENDING_KEY(sessionId), JSON.stringify(items))
  } catch {
    // ignore if storage is full
  }
}

function clearPending(sessionId: string): void {
  try {
    localStorage.removeItem(PENDING_KEY(sessionId))
  } catch {
    // ignore
  }
}

// ─── hook types ───────────────────────────────────────────────────────────────
export interface UseQuestionnaireResult {
  // Navigation
  currentQuestion: Question
  currentQuestionIndex: number
  isFirstQuestion: boolean
  isLastQuestion: boolean
  isAtSectionStart: boolean
  goNext: () => Promise<void>
  goBack: () => void
  jumpTo: (index: number) => void

  // Answers (questionId → JSON string)
  answers: Record<string, string>
  setAnswer: (questionId: string, value: string) => void

  // Save state
  isSaving: boolean
  saveError: string | null
  lastSaved: Date | null

  // Session
  session: QuestionnaireSession | null
  sessionId: string | null

  // Generation
  generate: () => Promise<GenerateResult>
  isGenerating: boolean

  // Loading / error
  isLoading: boolean
  loadError: string | null
}

// ─── hook implementation ──────────────────────────────────────────────────────
export function useQuestionnaire(existingSessionId?: string): UseQuestionnaireResult {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [session, setSession] = useState<QuestionnaireSession | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(existingSessionId ?? null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  // Track whether the current index is at the start of a new section
  // (used by QuestionnairePage to show SectionOverviewScreen)
  const [isAtSectionStart, setIsAtSectionStart] = useState(true)

  // Ref to track if flush is already running to avoid duplicate flushes
  const flushingRef = useRef(false)

  // ── Flush pending localStorage saves ───────────────────────────────────────
  const flushPending = useCallback(async (sid: string) => {
    if (flushingRef.current) return
    flushingRef.current = true
    const pending = readPending(sid)
    if (pending.length === 0) {
      flushingRef.current = false
      return
    }
    const remaining: PendingSave[] = []
    for (const save of pending) {
      try {
        await upsertAnswer(save.sessionId, save.questionId, save.answerJson, save.sectionNumber)
      } catch {
        remaining.push(save)
      }
    }
    if (remaining.length === 0) {
      clearPending(sid)
    } else {
      writePending(sid, remaining)
    }
    flushingRef.current = false
  }, [])

  // ── Initialise session on mount ────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false

    const init = async () => {
      setIsLoading(true)
      setLoadError(null)

      try {
        // 1. Determine session ID to use
        const storedId = existingSessionId ?? localStorage.getItem(SESSION_ID_KEY)

        if (storedId) {
          // Resume existing session
          const detail = await getSession(storedId)
          if (cancelled) return

          setSession(detail.session)
          setSessionId(storedId)

          // Rebuild answers map from saved answers
          const answerMap: Record<string, string> = {}
          for (const a of detail.answers) {
            answerMap[a.question_id] = a.answer_json
          }
          setAnswers(answerMap)

          // Jump to saved position
          if (detail.session.current_question_id) {
            const idx = QUESTIONS.findIndex(q => q.id === detail.session.current_question_id)
            if (idx >= 0) {
              setCurrentQuestionIndex(idx)
              // If resuming mid-section, don't show section overview
              const q = QUESTIONS[idx]
              const isFirstOfSection = QUESTIONS.findIndex(qq => qq.section === q.section) === idx
              setIsAtSectionStart(isFirstOfSection)
            }
          }

          await flushPending(storedId)
        } else {
          // Create a new session
          const newSession = await createSession()
          if (cancelled) return

          setSession(newSession)
          setSessionId(newSession.id)
          localStorage.setItem(SESSION_ID_KEY, newSession.id)
          setCurrentQuestionIndex(0)
          setIsAtSectionStart(true)
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(err instanceof Error ? err.message : 'Failed to load session')
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void init()
    return () => { cancelled = true }
  }, [existingSessionId, flushPending])

  // ── Derived navigation state ───────────────────────────────────────────────
  const currentQuestion = QUESTIONS[currentQuestionIndex]
  const isFirstQuestion = currentQuestionIndex === 0
  const isLastQuestion  = currentQuestionIndex === QUESTIONS.length - 1

  // ── setAnswer ──────────────────────────────────────────────────────────────
  const setAnswer = useCallback((questionId: string, value: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }))
  }, [])

  // ── goNext ─────────────────────────────────────────────────────────────────
  const goNext = useCallback(async () => {
    if (isLastQuestion) return

    const q = QUESTIONS[currentQuestionIndex]
    const sid = sessionId

    if (sid) {
      const answerJson = answers[q.id] ?? '""'
      setIsSaving(true)
      setSaveError(null)
      try {
        await upsertAnswer(sid, q.id, answerJson, q.section)
        setLastSaved(new Date())
      } catch {
        // Queue to localStorage and continue
        const pending = readPending(sid)
        pending.push({ sessionId: sid, questionId: q.id, answerJson, sectionNumber: q.section })
        writePending(sid, pending)
        setSaveError('Save queued — will retry')
      } finally {
        setIsSaving(false)
      }
    }

    // Advance to next question
    const nextIndex = currentQuestionIndex + 1
    const nextQuestion = QUESTIONS[nextIndex]
    const currentSection = q.section
    const nextSection = nextQuestion.section

    const crossingBoundary = nextSection !== currentSection
    setIsAtSectionStart(crossingBoundary)
    setCurrentQuestionIndex(nextIndex)
  }, [currentQuestionIndex, answers, sessionId, isLastQuestion])

  // ── goBack ─────────────────────────────────────────────────────────────────
  const goBack = useCallback(() => {
    if (isFirstQuestion) return
    const prevIndex = currentQuestionIndex - 1
    setIsAtSectionStart(false) // back always returns to a question, not section overview
    setCurrentQuestionIndex(prevIndex)
  }, [currentQuestionIndex, isFirstQuestion])

  // ── jumpTo ─────────────────────────────────────────────────────────────────
  const jumpTo = useCallback((index: number) => {
    if (index < 0 || index >= QUESTIONS.length) return
    setIsAtSectionStart(false)
    setCurrentQuestionIndex(index)
  }, [])

  // ── generate ───────────────────────────────────────────────────────────────
  const generate = useCallback(async (): Promise<GenerateResult> => {
    if (!sessionId) throw new Error('No active session')
    setIsGenerating(true)
    try {
      const result = await generateWorkbook(sessionId)
      // Clear stored session ID so next visit starts fresh
      localStorage.removeItem(SESSION_ID_KEY)
      return result
    } finally {
      setIsGenerating(false)
    }
  }, [sessionId])

  return {
    currentQuestion,
    currentQuestionIndex,
    isFirstQuestion,
    isLastQuestion,
    isAtSectionStart,
    goNext,
    goBack,
    jumpTo,
    answers,
    setAnswer,
    isSaving,
    saveError,
    lastSaved,
    session,
    sessionId,
    generate,
    isGenerating,
    isLoading,
    loadError,
  }
}
