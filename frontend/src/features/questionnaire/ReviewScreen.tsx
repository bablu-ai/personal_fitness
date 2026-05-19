import { useState } from 'react'
import { ChevronDown, ChevronUp, Edit2, FileSpreadsheet } from 'lucide-react'
import { QUESTIONS, SECTIONS, FIRST_QUESTION_OF_SECTION } from './questionConfig'
import { cn } from '@/lib/utils'

interface ReviewScreenProps {
  answers: Record<string, string>
  onGenerate: () => void
  onEditSection: (sectionNumber: number) => void
  isGenerating: boolean
}

function formatAnswer(answerJson: string): string {
  if (!answerJson || answerJson === '""') return '—'
  try {
    const parsed: unknown = JSON.parse(answerJson)
    if (typeof parsed === 'string') return parsed || '—'
    if (Array.isArray(parsed)) {
      const arr = parsed as string[]
      return arr.length === 0 ? '—' : arr.join(', ')
    }
    if (parsed !== null && typeof parsed === 'object') {
      const cv = parsed as { choice?: string; detail?: string }
      const parts: string[] = []
      if (cv.choice) parts.push(cv.choice)
      if (cv.detail) parts.push(`(${cv.detail})`)
      return parts.length > 0 ? parts.join(' ') : '—'
    }
    return String(parsed)
  } catch {
    return answerJson || '—'
  }
}

const ReviewScreen = ({ answers, onGenerate, onEditSection, isGenerating }: ReviewScreenProps) => {
  const [expandedSections, setExpandedSections] = useState<Set<number>>(
    new Set(SECTIONS.map(s => s.number))
  )

  const answeredCount = QUESTIONS.filter(q => {
    const a = answers[q.id]
    return a && a !== '""' && a !== '[]'
  }).length

  const toggleSection = (num: number) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(num)) { next.delete(num) } else { next.add(num) }
      return next
    })
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 border-b">
        <h1 className="text-2xl font-bold mb-1">Review Your Answers</h1>
        <p className="text-sm text-muted-foreground">
          {answeredCount} of {QUESTIONS.length} answered
          {answeredCount < QUESTIONS.length && ` (${QUESTIONS.length - answeredCount} optional skipped)`}
        </p>
      </div>

      {/* Section accordions */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 pb-32">
        {SECTIONS.map(section => {
          const isExpanded = expandedSections.has(section.number)
          const sectionQs = QUESTIONS.filter(q => q.section === section.number)
          const firstQ = FIRST_QUESTION_OF_SECTION(section.number)

          return (
            <div key={section.number} className="rounded-lg border bg-card overflow-hidden">
              {/* Section header */}
              <div className="flex items-center justify-between px-4 py-3">
                <button
                  type="button"
                  onClick={() => toggleSection(section.number)}
                  className="flex items-center gap-2 flex-1 text-left min-h-[44px]"
                >
                  <span className="font-semibold text-sm">{section.title}</span>
                  {isExpanded ? <ChevronUp size={16} className="text-muted-foreground" /> : <ChevronDown size={16} className="text-muted-foreground" />}
                </button>
                <button
                  type="button"
                  onClick={() => onEditSection(firstQ.number - 1)}
                  aria-label={`Edit section ${section.title}`}
                  className="flex items-center gap-1 text-xs text-primary font-medium px-2 py-1 rounded hover:bg-primary/5 transition-colors min-h-[44px]"
                >
                  <Edit2 size={12} />
                  Edit
                </button>
              </div>

              {/* Questions list */}
              {isExpanded && (
                <div className="border-t divide-y">
                  {sectionQs.map(q => (
                    <div key={q.id} className="px-4 py-3">
                      <p className="text-xs text-muted-foreground mb-0.5 leading-snug">{q.text}</p>
                      <p className={cn(
                        'text-sm font-medium',
                        (!answers[q.id] || answers[q.id] === '""') ? 'text-muted-foreground italic' : 'text-foreground'
                      )}>
                        {formatAnswer(answers[q.id] ?? '')}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Sticky generate button */}
      <div className="fixed bottom-0 left-0 right-0 px-4 pb-8 pt-4 bg-background border-t">
        <button
          type="button"
          onClick={onGenerate}
          disabled={isGenerating}
          className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground rounded-lg px-6 py-3 font-semibold min-h-[52px] hover:bg-primary/90 transition-colors disabled:opacity-60"
        >
          <FileSpreadsheet size={20} />
          {isGenerating ? 'Generating…' : 'Generate My Workbook'}
        </button>
      </div>
    </div>
  )
}

export default ReviewScreen
