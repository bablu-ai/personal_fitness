import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TaskDetailDrawer from './TaskDetailDrawer'

vi.mock('@/lib/api', () => ({
  todosApi: {
    getDetail: vi.fn().mockResolvedValue({
      id: 'tmpl-1',
      pillar: 'supplements',
      name: 'Omega-3',
      description: 'Anti-inflammatory fatty acids',
      why_mechanism: 'Reduces inflammation via EPA/DHA pathways',
      how_to: 'Take with a fatty meal',
      safety_notes: 'May thin blood at high doses',
      video_link: 'https://example.com/video',
      link: null,
      source_key: 'omega3',
      target_value: '2g',
      unit: 'g',
      timing: 'Morning',
      schedule: 'daily',
      benefit_tags: null,
      is_reference: false,
      extra_metadata: null,
      related_exercises: [],
    }),
  },
}))

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>
)

describe('TaskDetailDrawer', () => {
  it('is not visible when templateId is null', () => {
    render(<TaskDetailDrawer templateId={null} onClose={vi.fn()} />, { wrapper })
    const drawer = screen.getByRole('dialog', { hidden: true })
    expect(drawer).toHaveClass('translate-y-full')
  })

  it('is visible when templateId is provided', () => {
    render(<TaskDetailDrawer templateId="tmpl-1" onClose={vi.fn()} />, { wrapper })
    const drawer = screen.getByRole('dialog')
    expect(drawer).toHaveClass('translate-y-0')
  })

  it('calls onClose when backdrop is clicked', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(<TaskDetailDrawer templateId="tmpl-1" onClose={onClose} />, { wrapper })
    const backdrop = document.querySelector('[aria-hidden="true"]') as HTMLElement
    await user.click(backdrop)
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose when Escape is pressed', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(<TaskDetailDrawer templateId="tmpl-1" onClose={onClose} />, { wrapper })
    await user.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose when X button is clicked', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(<TaskDetailDrawer templateId="tmpl-1" onClose={onClose} />, { wrapper })
    await user.click(screen.getByRole('button', { name: /close/i }))
    expect(onClose).toHaveBeenCalled()
  })
})
