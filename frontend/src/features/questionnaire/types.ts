export type QuestionType =
  | 'text'
  | 'date'
  | 'number'
  | 'single_choice'
  | 'multi_choice'
  | 'time'
  | 'conditional_text'

export interface Question {
  id: string
  section: number
  number: number
  type: QuestionType
  text: string
  options?: string[]
  required: boolean
  placeholder?: string
  conditional?: {
    triggerOption: string
    placeholder: string
    fieldId: string
  }
  validation?: { min?: number; max?: number }
}

export interface SectionMeta {
  number: number
  title: string
  questionCount: number
  iconName: string
  estimatedMinutes: number
}

export interface QuestionnaireSession {
  id: string
  status: 'in_progress' | 'completed' | 'generating' | 'plan_generated' | 'failed'
  current_question_id: string | null
  current_section: number
  completed_count: number
  total_questions: number
  created_at: string
  updated_at: string
}

export interface SessionAnswer {
  id: string
  question_id: string
  section_number: number
  answer_json: string
  answered_at: string
}

export interface SessionDetail {
  session: QuestionnaireSession
  answers: SessionAnswer[]
}

export interface GenerateResult {
  workbook_id: string
  xlsx_token: string
  plan_id: string | null
}
