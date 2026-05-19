import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TodoItem from '@/features/todos/TodoItem'
import type { DailyTodo } from '@/types'

const baseTodo: DailyTodo = {
  id: 'todo-1',
  date: '2026-05-16',
  completed: false,
  completed_at: null,
  actual_value: null,
  notes: null,
  template: {
    id: 'tmpl-1',
    pillar: 'supplements',
    name: 'Omega-3',
    description: 'Take with food',
    schedule: 'daily',
    timing: 'Morning',
    target_value: '2g',
    unit: 'g',
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
}

describe('TodoItem', () => {
  it('renders task name and description', () => {
    render(<TodoItem todo={baseTodo} onToggle={vi.fn()} />)
    expect(screen.getByText('Omega-3')).toBeInTheDocument()
    expect(screen.getByText('Take with food')).toBeInTheDocument()
  })

  it('calls onToggle when checkbox is clicked', async () => {
    const user = userEvent.setup()
    const onToggle = vi.fn()
    render(<TodoItem todo={baseTodo} onToggle={onToggle} />)
    await user.click(screen.getByRole('button', { name: /mark complete/i }))
    expect(onToggle).toHaveBeenCalledWith('todo-1', true)
  })

  it('calls onToggle with false when completed todo checkbox is clicked', async () => {
    const user = userEvent.setup()
    const onToggle = vi.fn()
    render(<TodoItem todo={{ ...baseTodo, completed: true }} onToggle={onToggle} />)
    await user.click(screen.getByRole('button', { name: /mark incomplete/i }))
    expect(onToggle).toHaveBeenCalledWith('todo-1', false)
  })

  it('shows detail chevron when onOpenDetail is provided', () => {
    render(<TodoItem todo={baseTodo} onToggle={vi.fn()} onOpenDetail={vi.fn()} />)
    expect(screen.getByRole('button', { name: /view task detail/i })).toBeInTheDocument()
  })

  it('hides detail chevron when onOpenDetail is not provided', () => {
    render(<TodoItem todo={baseTodo} onToggle={vi.fn()} />)
    expect(screen.queryByRole('button', { name: /view task detail/i })).not.toBeInTheDocument()
  })

  it('calls onOpenDetail with template id when chevron clicked', async () => {
    const user = userEvent.setup()
    const onOpenDetail = vi.fn()
    render(<TodoItem todo={baseTodo} onToggle={vi.fn()} onOpenDetail={onOpenDetail} />)
    await user.click(screen.getByRole('button', { name: /view task detail/i }))
    expect(onOpenDetail).toHaveBeenCalledWith('tmpl-1')
  })

  it('applies line-through style when completed', () => {
    render(<TodoItem todo={{ ...baseTodo, completed: true }} onToggle={vi.fn()} />)
    const nameEl = screen.getByText('Omega-3')
    expect(nameEl).toHaveClass('line-through')
  })

  it('shows target value and timing', () => {
    render(<TodoItem todo={baseTodo} onToggle={vi.fn()} />)
    expect(screen.getByText(/2g/)).toBeInTheDocument()
    expect(screen.getByText(/morning/i)).toBeInTheDocument()
  })

  it('renders must marker as a compact badge', () => {
    render(
      <TodoItem
        todo={{
          ...baseTodo,
          template: { ...baseTodo.template, name: '(must) Upper back' },
        }}
        onToggle={vi.fn()}
      />,
    )
    expect(screen.getByText('Must')).toBeInTheDocument()
    expect(screen.getByText('Upper back')).toBeInTheDocument()
    expect(screen.queryByText('(must) Upper back')).not.toBeInTheDocument()
  })
})
