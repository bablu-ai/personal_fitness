import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import BriefTodayTimeline from '@/features/todos/BriefTodayTimeline'
import type { DailyTodo } from '@/types'

const makeTodo = (id: string, name: string, timing: string | null): DailyTodo => ({
  id,
  date: '2026-05-16',
  completed: false,
  completed_at: null,
  actual_value: null,
  notes: null,
  template: {
    id: `tmpl-${id}`,
    pillar: 'brief_today',
    name,
    description: null,
    schedule: 'daily',
    timing,
    target_value: null,
    unit: null,
    benefit_tags: null,
    source_key: null,
    link: null,
    video_link: null,
    safety_notes: null,
    how_to: null,
    why_mechanism: null,
    is_reference: false,
    extra_metadata: null,
  },
})

describe('BriefTodayTimeline', () => {
  it('renders all todo names', () => {
    const todos = [
      makeTodo('1', 'Morning Walk', '7:00 AM'),
      makeTodo('2', 'Supplement', 'Evening'),
    ]
    render(<BriefTodayTimeline todos={todos} onToggle={vi.fn()} />)
    expect(screen.getByText('Morning Walk')).toBeInTheDocument()
    expect(screen.getByText('Supplement')).toBeInTheDocument()
  })

  it('renders time gutter labels', () => {
    const todos = [makeTodo('1', 'Morning Walk', '7:00 AM')]
    render(<BriefTodayTimeline todos={todos} onToggle={vi.fn()} />)
    // Label appears in both the gutter and the todo's timing chip
    expect(screen.getAllByText('7:00 AM').length).toBeGreaterThanOrEqual(1)
  })

  it('groups todos with same timing in one slot', () => {
    const todos = [
      makeTodo('1', 'Task A', 'Morning'),
      makeTodo('2', 'Task B', 'Morning'),
    ]
    render(<BriefTodayTimeline todos={todos} onToggle={vi.fn()} />)
    // Only one gutter label for the group (the gutter span has a specific class)
    const gutterLabels = document.querySelectorAll('.text-\\[11px\\]')
    expect(gutterLabels).toHaveLength(1)
  })

  it('shows Anytime label for todos with no timing', () => {
    const todos = [makeTodo('1', 'No-time task', null)]
    render(<BriefTodayTimeline todos={todos} onToggle={vi.fn()} />)
    expect(screen.getByText('Anytime')).toBeInTheDocument()
  })

  it('renders empty with no todos', () => {
    const { container } = render(<BriefTodayTimeline todos={[]} onToggle={vi.fn()} />)
    expect(container.firstChild).toBeEmptyDOMElement()
  })
})
