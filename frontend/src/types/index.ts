export interface RelatedExercise {
  id: string
  name: string
  how_to: string | null
  video_link: string | null
  safety_notes: string | null
  target_value: string | null
}

export interface Exercise {
  name: string
  category: string | null
  setup: string | null
  starting_position: string | null
  how_to: string | null
  bracing_cue: string | null
  common_mistakes: string | null
  week1_dosage: string | null
  safety_notes: string | null
  why_it_matters: string | null
  video_link: string | null
  gif_link: string | null
}

export interface TaskTemplate {
  id: string
  pillar: string
  name: string
  description: string | null
  schedule: string | null
  timing: string | null
  target_value: string | null
  unit: string | null
  benefit_tags: string | null
  source_key: string | null
  link: string | null
  video_link: string | null
  safety_notes: string | null
  how_to: string | null
  why_mechanism: string | null
  is_reference: boolean
  extra_metadata: Record<string, string> | null
}

export interface TaskDetailOut extends TaskTemplate {
  related_exercises: RelatedExercise[]
  exercises: Exercise[]
}

export interface DailyTodo {
  id: string
  date: string
  completed: boolean
  completed_at: string | null
  actual_value: string | null
  notes: string | null
  template: TaskTemplate
}

export interface DaySummary {
  date: string
  total: number
  completed: number
  completion_pct: number
  by_pillar: Record<string, { total: number; completed: number; pct: number }>
}

export interface BenefitScore {
  outcome: string
  label: string
  score_pct: number
  icon: string | null
}

export interface BenefitScoresResponse {
  date: string
  scores: BenefitScore[]
}

export interface DailyRow {
  date: string
  total: number
  completed: number
  completion_pct: number
}

export interface WeeklyRow {
  week_start: string
  total: number
  completed: number
  completion_pct: number
  days_tracked: number
}

export interface MonthlyRow {
  month: string
  total: number
  completed: number
  completion_pct: number
  days_tracked: number
}

export interface UploadResponse {
  plan: { id: string; name: string; uploaded_at: string; is_active: boolean }
  tasks_imported: number
  pillars_found: string[]
  rotation_days_imported: number
}

export interface IngestResponse {
  plan_id: string
  plan_name: string
  tasks_imported: number
  rotation_days_imported: number
  screenings_imported: number
  todos_prefilled: number
  pillars_found: string[]
}

export interface TodoUpdateRequest {
  completed: boolean
  actual_value?: string | null
  notes?: string | null
}

export interface RotationDay {
  day_number: number
  week_number: number | null
  block_name: string
  // v3 fields
  warm_up: string | null
  priority_block: string | null
  secondary_block: string | null
  cardio_steps: string | null
  cool_down: string | null
  nutrition_focus: string | null
  intensity_cap: string | null
  source_key: string | null
  sets: string | null
  reps: string | null
  duration: string | null
  notes: string | null
  // v4 time-budget fields
  morning_time: string | null
  warm_up_min: string | null
  upper_back_core_min: string | null
  secondary_min: string | null
  cool_down_min: string | null
  total_min: string | null
  fits_60: string | null
  priority_exercises: string | null
  secondary_exercises: string | null
  week_rule: string | null
  completed_today: boolean
  rotation_start_date: string | null
}

export interface RotationWeekDay {
  calendar_date: string
  day_of_week: string
  rotation_day_number: number
  block_name: string
  // v3 fields
  warm_up: string | null
  priority_block: string | null
  secondary_block: string | null
  cardio_steps: string | null
  cool_down: string | null
  nutrition_focus: string | null
  intensity_cap: string | null
  sets: string | null
  reps: string | null
  duration: string | null
  notes: string | null
  // v4 time-budget fields
  morning_time: string | null
  warm_up_min: string | null
  upper_back_core_min: string | null
  secondary_min: string | null
  cool_down_min: string | null
  total_min: string | null
  fits_60: string | null
  priority_exercises: string | null
  secondary_exercises: string | null
  week_rule: string | null
  completed: boolean
  is_today: boolean
}

export interface Screening {
  id: string
  pillar: string
  name: string
  description: string | null
  frequency_months: number | null
  target_value: string | null
  last_done_date: string | null
  next_due_date: string | null
  is_overdue: boolean
  due_in_days: number | null
}
