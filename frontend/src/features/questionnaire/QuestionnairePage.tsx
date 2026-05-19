import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Skeleton } from '@/components/ui/Skeleton'
import { QUESTIONS } from './questionConfig'
import { useQuestionnaire } from './useQuestionnaire'
import SectionOverviewScreen from './SectionOverviewScreen'
import QuestionScreen from './QuestionScreen'
import ReviewScreen from './ReviewScreen'
import GenerationScreen from './GenerationScreen'
import type { GenerateResult } from './types'

type PageView = 'section_overview' | 'question' | 'review' | 'generation'

/**
 * Top-level page for /workbook/new and /workbook/:sessionId.
 * Manages which sub-screen is shown, hiding the app's bottom nav
 * by rendering in a full-screen overlay (the nav check in App.tsx
 * already excludes /workbook/* routes).
 */
const QuestionnairePage = () => {
  const { sessionId: urlSessionId } = useParams<{ sessionId?: string }>()
  const existingId = urlSessionId === 'new' ? undefined : urlSessionId

  const {
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
    lastSaved,
    generate,
    isGenerating,
    isLoading,
    loadError,
  } = useQuestionnaire(existingId)

  // Generation screen state
  const [generationState, setGenerationState] = useState<'generating' | 'success' | 'error'>('generating')
  const [generationResult, setGenerationResult] = useState<GenerateResult | null>(null)
  const [generationError, setGenerationError] = useState<string | null>(null)

  // Always start as 'question'; derive initial view once loading finishes.
  // Initializing from isAtSectionStart is wrong — it defaults to true during async load,
  // which would flash the SectionOverview screen on every session resume.
  const [view, setView] = useState<PageView>('question')
  const didInitView = useRef(false)

  // Once the session finishes loading, set the correct initial view exactly once.
  useEffect(() => {
    if (isLoading || didInitView.current) return
    didInitView.current = true
    if (isAtSectionStart) {
      setView('section_overview')
    }
    // else leave as 'question' (already the default)
  }, [isLoading, isAtSectionStart])

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleSectionContinue = () => {
    setView('question')
  }

  const handleBack = () => {
    if (view === 'review') {
      setView('question')
      return
    }
    if (view === 'section_overview') {
      // Go back to previous question
      goBack()
      setView('question')
      return
    }
    // On question view: if first question, do nothing
    if (isFirstQuestion) return
    goBack()
    setView('question')
  }

  const handleNext = async () => {
    if (isLastQuestion) {
      // Save last answer then go to review
      await goNext()
      setView('review')
      return
    }
    await goNext()
    // After goNext, isAtSectionStart reflects new question
    // We need to check the next question's section vs current
    const nextIdx = currentQuestionIndex + 1
    if (nextIdx < QUESTIONS.length) {
      const nextQ = QUESTIONS[nextIdx]
      const currentSection = currentQuestion.section
      if (nextQ.section !== currentSection) {
        setView('section_overview')
      } else {
        setView('question')
      }
    }
  }

  const handleEditSection = (questionIndex: number) => {
    jumpTo(questionIndex)
    setView('question')
  }

  const handleGenerate = async () => {
    setView('generation')
    setGenerationState('generating')
    setGenerationError(null)
    try {
      const result = await generate()
      setGenerationResult(result)
      setGenerationState('success')
    } catch (err) {
      setGenerationError(err instanceof Error ? err.message : 'Generation failed')
      setGenerationState('error')
    }
  }

  const handleRetryGenerate = () => {
    void handleGenerate()
  }

  // ── Loading / error ────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col p-4 space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-2 w-full" />
        <Skeleton className="h-40" />
        <Skeleton className="h-14" />
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 text-center">
        <div>
          <p className="text-red-600 font-medium mb-2">Could not load session</p>
          <p className="text-sm text-muted-foreground">{loadError}</p>
        </div>
      </div>
    )
  }

  // ── Generation screen ──────────────────────────────────────────────────────
  if (view === 'generation') {
    return (
      <GenerationScreen
        state={generationState}
        result={generationResult}
        error={generationError}
        onRetry={handleRetryGenerate}
      />
    )
  }

  // ── Review screen ──────────────────────────────────────────────────────────
  if (view === 'review') {
    return (
      <ReviewScreen
        answers={answers}
        onGenerate={() => void handleGenerate()}
        onEditSection={handleEditSection}
        isGenerating={isGenerating}
      />
    )
  }

  // ── Section overview ───────────────────────────────────────────────────────
  if (view === 'section_overview') {
    return (
      <SectionOverviewScreen
        sectionNumber={currentQuestion.section}
        onContinue={handleSectionContinue}
        onBack={handleBack}
      />
    )
  }

  // ── Question screen ────────────────────────────────────────────────────────
  return (
    <QuestionScreen
      question={currentQuestion}
      questionIndex={currentQuestionIndex}
      totalQuestions={QUESTIONS.length}
      answer={answers[currentQuestion.id] ?? ''}
      onAnswerChange={setAnswer}
      onNext={handleNext}
      onBack={handleBack}
      isFirstQuestion={isFirstQuestion}
      isLastQuestion={isLastQuestion}
      isSaving={isSaving}
      lastSaved={lastSaved}
    />
  )
}

export default QuestionnairePage
