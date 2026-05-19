import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import QuestionScreen from '@/features/questionnaire/QuestionScreen'
import type { Question } from '@/features/questionnaire/types'

// Mock the questionnaire API so tests never hit the network
vi.mock('@/features/questionnaire/api/questionnaire', () => ({
  upsertAnswer: vi.fn().mockResolvedValue({}),
  createSession: vi.fn().mockResolvedValue({ id: 'test-session', status: 'in_progress', current_question_id: null, current_section: 1, completed_count: 0, total_questions: 40, created_at: '', updated_at: '' }),
  listSessions: vi.fn().mockResolvedValue([]),
  getSession: vi.fn().mockResolvedValue({ session: {}, answers: [] }),
  generateWorkbook: vi.fn().mockResolvedValue({ workbook_id: '1', xlsx_token: 'tok', plan_id: null }),
  getDownloadUrl: vi.fn().mockReturnValue('/api/questionnaire/download/tok'),
  setAuthToken: vi.fn(),
}))

const TEXT_QUESTION: Question = {
  id: 'q1_full_name', section: 1, number: 1, type: 'text',
  text: 'What is your full name?', required: true, placeholder: 'Enter your full name',
}

const SINGLE_CHOICE_QUESTION: Question = {
  id: 'q3_sex_at_birth', section: 1, number: 3, type: 'single_choice',
  text: 'Sex at birth', required: true,
  options: ['Male', 'Female', 'Intersex', 'Prefer not to say'],
}

const MULTI_CHOICE_QUESTION: Question = {
  id: 'q6_chronic_conditions', section: 2, number: 6, type: 'multi_choice',
  text: 'Do you have any diagnosed chronic conditions?', required: false,
  options: ['Hypertension', 'Diabetes', 'None', 'Other'],
  conditional: { triggerOption: 'Other', placeholder: 'Please describe', fieldId: 'q6_other' },
}

const CONDITIONAL_QUESTION: Question = {
  id: 'q7_medications', section: 2, number: 7, type: 'conditional_text',
  text: 'Are you taking any medications?', required: false,
  options: ['Yes', 'No'],
  conditional: { triggerOption: 'Yes', placeholder: 'Please specify', fieldId: 'q7_detail' },
}

const SINGLE_CHOICE_WITH_CONDITIONAL: Question = {
  id: 'q16_diet_type', section: 4, number: 16, type: 'single_choice',
  text: 'How would you describe your diet?', required: false,
  options: ['Standard', 'Vegetarian', 'Vegan', 'Other'],
  conditional: { triggerOption: 'Other', placeholder: 'Describe your diet', fieldId: 'q16_other' },
}

function renderQuestionScreen(
  question: Question,
  overrides?: Partial<Parameters<typeof QuestionScreen>[0]>,
) {
  const defaults = {
    question,
    questionIndex: question.number - 1,
    totalQuestions: 40,
    answer: '',
    onAnswerChange: vi.fn(),
    onNext: vi.fn().mockResolvedValue(undefined),
    onBack: vi.fn(),
    isFirstQuestion: false,
    isLastQuestion: false,
    isSaving: false,
    lastSaved: null,
  }
  return render(<QuestionScreen {...defaults} {...overrides} />)
}

describe('QuestionScreen — text input', () => {
  it('renders a textarea for text question type', () => {
    renderQuestionScreen(TEXT_QUESTION)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/enter your full name/i)).toBeInTheDocument()
  })

  it('shows the question text', () => {
    renderQuestionScreen(TEXT_QUESTION)
    expect(screen.getByText(/what is your full name/i)).toBeInTheDocument()
  })

  it('shows progress indicator', () => {
    renderQuestionScreen(TEXT_QUESTION)
    expect(screen.getByText('Q1 of 40')).toBeInTheDocument()
  })
})

describe('QuestionScreen — single_choice input', () => {
  it('renders option buttons as radio elements', () => {
    renderQuestionScreen(SINGLE_CHOICE_QUESTION)
    expect(screen.getByRole('radio', { name: 'Male' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Female' })).toBeInTheDocument()
  })

  it('calls onAnswerChange when an option is clicked', async () => {
    const user = userEvent.setup()
    const onAnswerChange = vi.fn()
    renderQuestionScreen(SINGLE_CHOICE_QUESTION, { onAnswerChange })
    await user.click(screen.getByRole('radio', { name: 'Male' }))
    expect(onAnswerChange).toHaveBeenCalledWith('q3_sex_at_birth', JSON.stringify('Male'))
  })
})

describe('QuestionScreen — multi_choice input', () => {
  it('renders checkboxes for multi_choice type', () => {
    renderQuestionScreen(MULTI_CHOICE_QUESTION)
    expect(screen.getByRole('checkbox', { name: /hypertension/i })).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /diabetes/i })).toBeInTheDocument()
  })

  it('allows multiple selections', async () => {
    const user = userEvent.setup()
    const onAnswerChange = vi.fn()
    renderQuestionScreen(MULTI_CHOICE_QUESTION, { onAnswerChange })
    await user.click(screen.getByRole('checkbox', { name: /hypertension/i }))
    await user.click(screen.getByRole('checkbox', { name: /diabetes/i }))
    // Should have been called twice
    expect(onAnswerChange).toHaveBeenCalledTimes(2)
  })

  it('shows detail textarea when answer includes trigger option', () => {
    // Simulate a controlled state where "Other" is already in the answer
    const answerWithOther = JSON.stringify({ choices: ['Other'], detail: '' })
    renderQuestionScreen(MULTI_CHOICE_QUESTION, { answer: answerWithOther })
    expect(screen.getByPlaceholderText(/please describe/i)).toBeInTheDocument()
  })

  it('does not show detail textarea when answer does not include trigger option', () => {
    const answerWithoutOther = JSON.stringify({ choices: ['Hypertension'], detail: '' })
    renderQuestionScreen(MULTI_CHOICE_QUESTION, { answer: answerWithoutOther })
    expect(screen.queryByPlaceholderText(/please describe/i)).not.toBeInTheDocument()
  })

  it('emits { choices, detail } JSON shape when trigger option is selected', async () => {
    const user = userEvent.setup()
    const onAnswerChange = vi.fn()
    renderQuestionScreen(MULTI_CHOICE_QUESTION, { onAnswerChange })
    await user.click(screen.getByRole('checkbox', { name: /other/i }))
    const lastCall = onAnswerChange.mock.calls[onAnswerChange.mock.calls.length - 1] as [string, string]
    const emitted = JSON.parse(lastCall[1]) as { choices: string[]; detail: string }
    expect(emitted).toMatchObject({ choices: ['Other'], detail: '' })
  })
})

describe('QuestionScreen — single_choice with conditional detail', () => {
  it('does not show detail textarea when trigger option is not selected', () => {
    renderQuestionScreen(SINGLE_CHOICE_WITH_CONDITIONAL)
    expect(screen.queryByPlaceholderText(/describe your diet/i)).not.toBeInTheDocument()
  })

  it('shows detail textarea when answer contains trigger option', () => {
    // Controlled state: "Other" is already selected
    const answerWithOther = JSON.stringify({ choice: 'Other', detail: '' })
    renderQuestionScreen(SINGLE_CHOICE_WITH_CONDITIONAL, { answer: answerWithOther })
    expect(screen.getByPlaceholderText(/describe your diet/i)).toBeInTheDocument()
  })

  it('does not show detail textarea when a non-trigger option is selected', () => {
    const answerOther = JSON.stringify({ choice: 'Vegan', detail: '' })
    renderQuestionScreen(SINGLE_CHOICE_WITH_CONDITIONAL, { answer: answerOther })
    expect(screen.queryByPlaceholderText(/describe your diet/i)).not.toBeInTheDocument()
  })

  it('emits { choice, detail } JSON shape when trigger option is selected', async () => {
    const user = userEvent.setup()
    const onAnswerChange = vi.fn()
    renderQuestionScreen(SINGLE_CHOICE_WITH_CONDITIONAL, { onAnswerChange })
    await user.click(screen.getByRole('radio', { name: 'Other' }))
    const lastCall = onAnswerChange.mock.calls[onAnswerChange.mock.calls.length - 1] as [string, string]
    const emitted = JSON.parse(lastCall[1]) as { choice: string; detail: string }
    expect(emitted).toMatchObject({ choice: 'Other', detail: '' })
  })
})

describe('QuestionScreen — required validation', () => {
  it('disables next navigation with an inline error when required question is unanswered', async () => {
    const user = userEvent.setup()
    const onNext = vi.fn()
    renderQuestionScreen(TEXT_QUESTION, { onNext, answer: '' })
    await user.click(screen.getByRole('button', { name: /next/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/please answer this question/i)
    expect(onNext).not.toHaveBeenCalled()
  })

  it('calls onNext when required question has an answer', async () => {
    const user = userEvent.setup()
    const onNext = vi.fn().mockResolvedValue(undefined)
    renderQuestionScreen(TEXT_QUESTION, {
      onNext,
      answer: JSON.stringify('John Doe'),
    })
    await user.click(screen.getByRole('button', { name: /next/i }))
    await waitFor(() => expect(onNext).toHaveBeenCalledOnce())
  })
})

describe('QuestionScreen — AUTO-SAVED indicator', () => {
  it('shows AUTO-SAVED text in the DOM when lastSaved is freshly set', async () => {
    const lastSaved = new Date()
    renderQuestionScreen(TEXT_QUESTION, { lastSaved })
    // Indicator is conditionally rendered — must be in the DOM when lastSaved is set
    expect(screen.getByText(/auto-saved/i)).toBeInTheDocument()
  })

  it('does NOT show AUTO-SAVED text when lastSaved is null', () => {
    renderQuestionScreen(TEXT_QUESTION, { lastSaved: null })
    // Indicator must be absent from the DOM — not just hidden
    expect(screen.queryByText(/auto-saved/i)).not.toBeInTheDocument()
  })
})

describe('QuestionScreen — conditional_text input', () => {
  it('renders Yes/No options', () => {
    renderQuestionScreen(CONDITIONAL_QUESTION)
    expect(screen.getByRole('radio', { name: 'Yes' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'No' })).toBeInTheDocument()
  })
})
