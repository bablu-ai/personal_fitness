import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReviewScreen from '@/features/questionnaire/ReviewScreen'
import { SECTIONS } from '@/features/questionnaire/questionConfig'

function renderReview(overrides?: Partial<Parameters<typeof ReviewScreen>[0]>) {
  const defaults = {
    answers: {},
    onGenerate: vi.fn(),
    onEditSection: vi.fn(),
    isGenerating: false,
  }
  return render(<ReviewScreen {...defaults} {...overrides} />)
}

describe('ReviewScreen', () => {
  it('shows all 7 section titles', () => {
    renderReview()
    for (const section of SECTIONS) {
      expect(screen.getByText(section.title)).toBeInTheDocument()
    }
  })

  it('shows "Generate My Workbook" button', () => {
    renderReview()
    expect(screen.getByRole('button', { name: /generate my workbook/i })).toBeInTheDocument()
  })

  it('shows answered count', () => {
    const answers: Record<string, string> = {
      q1_full_name: '"Alice"',
      q2_date_of_birth: '"1990-01-01"',
    }
    renderReview({ answers })
    expect(screen.getByText(/2 of 40 answered/i)).toBeInTheDocument()
  })

  it('calls onGenerate when button is clicked', async () => {
    const user = userEvent.setup()
    const onGenerate = vi.fn()
    renderReview({ onGenerate })
    await user.click(screen.getByRole('button', { name: /generate my workbook/i }))
    expect(onGenerate).toHaveBeenCalledOnce()
  })

  it('disables generate button while generating', () => {
    renderReview({ isGenerating: true })
    const btn = screen.getByRole('button', { name: /generating/i })
    expect(btn).toBeDisabled()
  })

  it('calls onEditSection with the correct index when Edit is clicked', async () => {
    const user = userEvent.setup()
    const onEditSection = vi.fn()
    renderReview({ onEditSection })

    // Section 2 is "Health & Medical" — first question index = 5 (0-based)
    const healthSection = screen.getByText('Health & Medical').closest('div')!
    const editBtn = within(healthSection).getByRole('button', { name: /edit section health & medical/i })
    await user.click(editBtn)
    // First question of section 2 is q6 (index 5)
    expect(onEditSection).toHaveBeenCalledWith(5)
  })

  it('renders formatted answers for answered questions', () => {
    const answers = { q1_full_name: '"Alice Smith"' }
    renderReview({ answers })
    expect(screen.getByText('Alice Smith')).toBeInTheDocument()
  })

  it('renders dash for unanswered questions', () => {
    renderReview({ answers: {} })
    // Multiple "—" chars should appear (one per unanswered question visible)
    const dashes = screen.getAllByText('—')
    expect(dashes.length).toBeGreaterThan(0)
  })

  it('toggles section collapse when header is clicked', async () => {
    const user = userEvent.setup()
    renderReview()
    // Sections start expanded — Q1 should be visible
    expect(screen.getByText(/what is your full name/i)).toBeInTheDocument()
    // The toggle button contains only the section title span + chevron icon
    // Use getAllByRole and pick the one whose accessible name is exactly the title
    const toggleBtns = screen.getAllByRole('button', { name: /personal information/i })
    // The toggle button comes before the Edit button in the DOM
    const toggleBtn = toggleBtns.find(
      btn => !btn.getAttribute('aria-label')?.startsWith('Edit')
    )!
    await user.click(toggleBtn)
    // After collapse the question text should be gone
    expect(screen.queryByText(/what is your full name/i)).not.toBeInTheDocument()
  })
})
