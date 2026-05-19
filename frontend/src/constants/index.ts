// Pillar display metadata — purely cosmetic; actual pillars come from the Excel sheet names via backend
export const PILLAR_META: Record<string, { label: string; color: string; emoji: string }> = {
  // Generic names
  exercise:          { label: 'Exercise',          color: 'bg-blue-100 text-blue-800',    emoji: '🏃' },
  nutrition:         { label: 'Nutrition',          color: 'bg-green-100 text-green-800',  emoji: '🥗' },
  supplements:       { label: 'Supplements',        color: 'bg-purple-100 text-purple-800',emoji: '💊' },
  sleep:             { label: 'Sleep',              color: 'bg-indigo-100 text-indigo-800',emoji: '😴' },
  rest:              { label: 'Rest',               color: 'bg-orange-100 text-orange-800',emoji: '🧘' },
  // Workbook-specific pillar names (from Excel sheet names with numeric prefix stripped)
  brief_today:       { label: 'Brief Today',        color: 'bg-sky-100 text-sky-800',      emoji: '⚡' },
  sleep_recovery:    { label: 'Sleep & Recovery',   color: 'bg-indigo-100 text-indigo-800',emoji: '😴' },
  cognitive_social:  { label: 'Cognitive & Social', color: 'bg-rose-100 text-rose-800',    emoji: '🧠' },
  exercise_library:  { label: 'Exercise Library',   color: 'bg-blue-100 text-blue-800',    emoji: '🏋️' },
  blood_markers:     { label: 'Blood Markers',      color: 'bg-red-100 text-red-800',      emoji: '🩸' },
  screenings_safety: { label: 'Screenings',         color: 'bg-yellow-100 text-yellow-800',emoji: '🔍' },
}

export const DEFAULT_PILLAR_COLOR = 'bg-gray-100 text-gray-800'

export const API_BASE_URL = '/api'

export const QUERY_KEYS = {
  todayTodos:   ['todos', 'today'] as const,
  necessarySupplements: ['todos', 'supplements', 'necessary'] as const,
  todaySummary: ['todos', 'today', 'summary'] as const,
  todayBenefits:['benefits', 'today'] as const,
  dashDaily:    ['dashboard', 'daily'] as const,
  dashWeekly:   ['dashboard', 'weekly'] as const,
  dashMonthly:  ['dashboard', 'monthly'] as const,
  taskDetail:   (id: string) => ['tasks', id, 'detail'] as const,
  reference:    ['reference'] as const,
} as const
