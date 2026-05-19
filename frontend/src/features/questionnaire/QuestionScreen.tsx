import { useState, useEffect } from 'react'
import { ArrowLeft, ArrowRight, CheckCircle } from 'lucide-react'
import type { Question } from './types'
import { SECTIONS } from './questionConfig'
import SingleChoiceInput from './components/SingleChoiceInput'
import MultiChoiceInput from './components/MultiChoiceInput'
import TextInput from './components/TextInput'
import NumberInput from './components/NumberInput'
import TimeInput from './components/TimeInput'
import ConditionalInput from './components/ConditionalInput'
import type { ConditionalValue } from './components/ConditionalInput'

interface QuestionScreenProps {
  question: Question
  questionIndex: number
  totalQuestions: number
  answer: string
  onAnswerChange: (questionId: string, value: string) => void
  onNext: () => Promise<void>
  onBack: () => void
  isFirstQuestion: boolean
  isLastQuestion: boolean
  isSaving: boolean
  lastSaved: Date | null
}

// ── Answer value types ────────────────────────────────────────────────────────

/** Used for single_choice questions that have a conditional detail field */
interface SingleWithDetail {
  choice: string
  detail: string
}

/** Used for multi_choice questions that have a conditional detail field */
interface MultiWithDetail {
  choices: string[]
  detail: string
}

// ── Parse helpers ─────────────────────────────────────────────────────────────

function parseSingleAnswer(raw: string): string {
  if (!raw || raw === '""') return ''
  try {
    const parsed: unknown = JSON.parse(raw)
    if (typeof parsed === 'string') return parsed
    // May be SingleWithDetail if the question has a conditional
    if (parsed !== null && typeof parsed === 'object' && 'choice' in parsed) {
      return (parsed as SingleWithDetail).choice
    }
    return ''
  } catch {
    return raw
  }
}

function parseSingleDetail(raw: string): string {
  if (!raw || raw === '""') return ''
  try {
    const parsed: unknown = JSON.parse(raw)
    if (parsed !== null && typeof parsed === 'object' && 'detail' in parsed) {
      return (parsed as SingleWithDetail).detail
    }
    return ''
  } catch {
    return ''
  }
}

function parseMultiChoiceAnswer(raw: string): string[] {
  if (!raw || raw === '""') return []
  try {
    const parsed: unknown = JSON.parse(raw)
    if (Array.isArray(parsed)) return parsed as string[]
    // May be MultiWithDetail if the question has a conditional
    if (parsed !== null && typeof parsed === 'object' && 'choices' in parsed) {
      const mwd = parsed as MultiWithDetail
      return Array.isArray(mwd.choices) ? mwd.choices : []
    }
    return []
  } catch {
    return []
  }
}

function parseMultiDetail(raw: string): string {
  if (!raw || raw === '""') return ''
  try {
    const parsed: unknown = JSON.parse(raw)
    if (parsed !== null && typeof parsed === 'object' && 'detail' in parsed) {
      return (parsed as MultiWithDetail).detail
    }
    return ''
  } catch {
    return ''
  }
}

function parseConditionalAnswer(raw: string): ConditionalValue {
  if (!raw || raw === '""') return { choice: '', detail: '' }
  try {
    const parsed = JSON.parse(raw) as ConditionalValue
    return { choice: parsed.choice ?? '', detail: parsed.detail ?? '' }
  } catch {
    return { choice: '', detail: '' }
  }
}

const QuestionScreen = ({
  question,
  questionIndex,
  totalQuestions,
  answer,
  onAnswerChange,
  onNext,
  onBack,
  isFirstQuestion,
  isLastQuestion,
  isSaving,
  lastSaved,
}: QuestionScreenProps) => {
  const [showRequired, setShowRequired] = useState(false)
  const [showSaved, setShowSaved] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const section = SECTIONS.find(s => s.number === question.section)
  const progressPct = ((questionIndex + 1) / totalQuestions) * 100

  // Show "AUTO-SAVED" indicator for 2 seconds after lastSaved changes
  useEffect(() => {
    if (!lastSaved) return
    setShowSaved(true)
    const timer = setTimeout(() => setShowSaved(false), 2000)
    return () => clearTimeout(timer)
  }, [lastSaved])

  const isEmpty = (val: string): boolean => {
    if (!val || val === '""') return true
    try {
      const parsed: unknown = JSON.parse(val)
      if (typeof parsed === 'string') return parsed.trim() === ''
      if (Array.isArray(parsed)) return parsed.length === 0
      if (parsed !== null && typeof parsed === 'object') {
        // Handles ConditionalValue, SingleWithDetail, MultiWithDetail
        if ('choice' in parsed) return (parsed as ConditionalValue).choice === ''
        if ('choices' in parsed) return (parsed as MultiWithDetail).choices.length === 0
      }
      return false
    } catch {
      return val.trim() === ''
    }
  }

  const handleNext = async () => {
    if (question.required && isEmpty(answer)) {
      setShowRequired(true)
      return
    }
    setShowRequired(false)
    setIsSubmitting(true)
    try {
      await onNext()
    } finally {
      setIsSubmitting(false)
    }
  }

  // ── Answer change helpers ──────────────────────────────────────────────────
  const handleSingleChange = (val: string) => {
    setShowRequired(false)
    if (question.conditional) {
      // Preserve existing detail, update choice; clear detail if deselected
      const currentDetail = parseSingleDetail(answer)
      const detail = val === '' ? '' : currentDetail
      onAnswerChange(question.id, JSON.stringify({ choice: val, detail } satisfies SingleWithDetail))
    } else {
      onAnswerChange(question.id, JSON.stringify(val))
    }
  }

  const handleSingleDetailChange = (detail: string) => {
    const choice = parseSingleAnswer(answer)
    onAnswerChange(question.id, JSON.stringify({ choice, detail } satisfies SingleWithDetail))
  }

  const handleMultiChange = (vals: string[]) => {
    setShowRequired(false)
    if (question.conditional) {
      const triggerSelected = vals.includes(question.conditional.triggerOption)
      const currentDetail = parseMultiDetail(answer)
      const detail = triggerSelected ? currentDetail : ''
      onAnswerChange(question.id, JSON.stringify({ choices: vals, detail } satisfies MultiWithDetail))
    } else {
      onAnswerChange(question.id, JSON.stringify(vals))
    }
  }

  const handleMultiDetailChange = (detail: string) => {
    const choices = parseMultiChoiceAnswer(answer)
    onAnswerChange(question.id, JSON.stringify({ choices, detail } satisfies MultiWithDetail))
  }

  const handleTextChange = (val: string) => {
    setShowRequired(false)
    onAnswerChange(question.id, JSON.stringify(val))
  }

  const handleConditionalChange = (val: ConditionalValue) => {
    setShowRequired(false)
    onAnswerChange(question.id, JSON.stringify(val))
  }

  // ── Render input by type ───────────────────────────────────────────────────
  const renderInput = () => {
    switch (question.type) {
      case 'single_choice':
        return (
          <SingleChoiceInput
            options={question.options ?? []}
            value={parseSingleAnswer(answer)}
            onChange={handleSingleChange}
            triggerOption={question.conditional?.triggerOption}
            detailValue={parseSingleDetail(answer)}
            detailPlaceholder={question.conditional?.placeholder}
            onDetailChange={question.conditional ? handleSingleDetailChange : undefined}
          />
        )

      case 'multi_choice':
        return (
          <MultiChoiceInput
            options={question.options ?? []}
            value={parseMultiChoiceAnswer(answer)}
            onChange={handleMultiChange}
            triggerOption={question.conditional?.triggerOption}
            detailValue={parseMultiDetail(answer)}
            detailPlaceholder={question.conditional?.placeholder}
            onDetailChange={question.conditional ? handleMultiDetailChange : undefined}
          />
        )

      case 'text':
      case 'date':
        return (
          <TextInput
            value={parseSingleAnswer(answer)}
            onChange={handleTextChange}
            placeholder={question.placeholder}
            multiline={question.type === 'text'}
          />
        )

      case 'number':
        return (
          <NumberInput
            value={parseSingleAnswer(answer)}
            onChange={handleTextChange}
            placeholder={question.placeholder}
            min={question.validation?.min}
            max={question.validation?.max}
          />
        )

      case 'time':
        return (
          <TimeInput
            value={parseSingleAnswer(answer)}
            onChange={handleTextChange}
            placeholder={question.placeholder}
          />
        )

      case 'conditional_text':
        return (
          <ConditionalInput
            options={question.options ?? []}
            triggerOption={question.conditional?.triggerOption ?? 'Yes'}
            detailPlaceholder={question.conditional?.placeholder ?? ''}
            value={parseConditionalAnswer(answer)}
            onChange={handleConditionalChange}
          />
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <button
          type="button"
          onClick={onBack}
          disabled={isFirstQuestion}
          aria-label="Go back"
          className="p-2 -ml-2 rounded-lg hover:bg-muted transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center disabled:opacity-40"
        >
          <ArrowLeft size={20} />
        </button>

        <span className="text-sm font-medium text-muted-foreground">
          Q{question.number} of {totalQuestions}
        </span>

        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full max-w-[120px] truncate">
          {section?.title ?? ''}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-muted mx-4 rounded-full overflow-hidden">
        <div
          className="h-1 bg-primary rounded-full transition-all duration-300"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Question + input */}
      <div className="flex-1 px-4 pt-6 pb-4 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-6 leading-snug">{question.text}</h2>

        {renderInput()}

        {showRequired && (
          <p role="alert" className="text-sm text-red-600 mt-3">
            Please answer this question to continue.
          </p>
        )}
      </div>

      {/* Bottom action bar */}
      <div className="px-4 pb-8 pt-2 flex items-center justify-between border-t bg-background">
        {showSaved ? (
          <span
            className="text-xs text-green-600 flex items-center gap-1"
            aria-live="polite"
          >
            <CheckCircle size={12} />
            AUTO-SAVED
          </span>
        ) : (
          <span aria-hidden="true" />
        )}

        <button
          type="button"
          onClick={() => void handleNext()}
          disabled={isSubmitting || isSaving}
          className="flex items-center gap-2 bg-primary text-primary-foreground rounded-lg px-6 py-2 font-medium min-h-[44px] hover:bg-primary/90 transition-colors disabled:opacity-60"
        >
          {isLastQuestion ? 'Review' : 'Next'}
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  )
}

export default QuestionScreen
