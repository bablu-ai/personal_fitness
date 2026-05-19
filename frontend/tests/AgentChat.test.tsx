import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock the api module so tests never hit the network
vi.mock('@/lib/api', () => ({
  agentApi: {
    chat: vi.fn(),
  },
}))

import AgentChat from '@/features/agent/AgentChat'
import { agentApi } from '@/lib/api'

const mockChat = agentApi.chat as ReturnType<typeof vi.fn>

beforeEach(() => {
  mockChat.mockReset()
  // jsdom doesn't implement scrollIntoView; stub it to prevent test errors
  window.HTMLElement.prototype.scrollIntoView = vi.fn()
})

async function sendMessage(text: string) {
  const user = userEvent.setup()
  render(<AgentChat />)
  const input = screen.getByPlaceholderText(/ask your longevity coach/i)
  await user.type(input, text)
  await user.click(screen.getByRole('button', { name: '' })) // Send button (icon only)
}

describe('MarkdownMessage rendering', () => {
  it('renders a bullet list with · glyphs', async () => {
    mockChat.mockResolvedValueOnce('- Item one\n- Item two\n- Item three')
    await sendMessage('test')
    expect(await screen.findAllByText('·')).toHaveLength(3)
    expect(screen.getByText('Item one')).toBeInTheDocument()
    expect(screen.getByText('Item two')).toBeInTheDocument()
    expect(screen.getByText('Item three')).toBeInTheDocument()
  })

  it('renders a numbered list with pill numbers', async () => {
    mockChat.mockResolvedValueOnce('1. First step\n2. Second step')
    await sendMessage('test')
    expect(await screen.findByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('First step')).toBeInTheDocument()
    expect(screen.getByText('Second step')).toBeInTheDocument()
  })

  it('renders ## heading as bold paragraph', async () => {
    mockChat.mockResolvedValueOnce('## Exercise Tips\nDo the warm-up first.')
    await sendMessage('test')
    expect(await screen.findByText('Exercise Tips')).toBeInTheDocument()
    expect(screen.getByText('Do the warm-up first.')).toBeInTheDocument()
  })

  it('renders blockquote with italic styling', async () => {
    mockChat.mockResolvedValueOnce('> Consistency beats intensity.')
    await sendMessage('test')
    expect(await screen.findByText('Consistency beats intensity.')).toBeInTheDocument()
  })

  it('renders **bold** inline text without asterisks', async () => {
    mockChat.mockResolvedValueOnce('Take **3g** of omega-3 daily.')
    await sendMessage('test')
    expect(await screen.findByText('3g')).toBeInTheDocument()
    // The asterisks must not appear in the rendered output
    expect(screen.queryByText(/\*\*3g\*\*/)).not.toBeInTheDocument()
  })

  it('renders mixed blocks: heading + bullets', async () => {
    mockChat.mockResolvedValueOnce('## This week\n- Zone 2 cardio\n- Band rows')
    await sendMessage('test')
    expect(await screen.findByText('This week')).toBeInTheDocument()
    expect(screen.getByText('Zone 2 cardio')).toBeInTheDocument()
    expect(screen.getByText('Band rows')).toBeInTheDocument()
  })

  it('renders plain text without markdown as a paragraph (no · glyphs)', async () => {
    mockChat.mockResolvedValueOnce('You are on track. Keep it up!')
    await sendMessage('test')
    expect(await screen.findByText('You are on track. Keep it up!')).toBeInTheDocument()
    expect(screen.queryByText('·')).not.toBeInTheDocument()
  })
})
