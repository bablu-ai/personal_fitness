import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileSpreadsheet, PlusCircle, ArrowRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/Skeleton'
import { listSessions } from './api/questionnaire'
import type { QuestionnaireSession } from './types'
import { cn } from '@/lib/utils'

const STATUS_LABEL: Record<QuestionnaireSession['status'], string> = {
  in_progress:    'In Progress',
  completed:      'Completed',
  generating:     'Generating',
  plan_generated: 'Plan Ready',
  failed:         'Failed',
}

const STATUS_COLORS: Record<QuestionnaireSession['status'], string> = {
  in_progress:    'bg-amber-100 text-amber-700',
  completed:      'bg-blue-100 text-blue-700',
  generating:     'bg-blue-100 text-blue-700',
  plan_generated: 'bg-green-100 text-green-700',
  failed:         'bg-red-100 text-red-700',
}

const SessionListPage = () => {
  const { data: sessions, isLoading, error } = useQuery({
    queryKey: ['questionnaire-sessions'],
    queryFn: listSessions,
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-primary/10 p-2">
          <FileSpreadsheet size={24} className="text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-bold">My Longevity Workbook</h1>
          <p className="text-sm text-muted-foreground">Answer 40 questions to get your personalized plan</p>
        </div>
      </div>

      {/* Primary CTA */}
      <Link
        to="/workbook/new"
        className="flex items-center justify-between w-full rounded-lg bg-primary text-primary-foreground px-5 py-4 font-semibold text-sm min-h-[60px] hover:bg-primary/90 transition-colors"
      >
        <span className="flex items-center gap-2">
          <PlusCircle size={20} />
          Start New Questionnaire
        </span>
        <ArrowRight size={18} />
      </Link>

      {/* Past sessions */}
      {isLoading && (
        <div className="space-y-3">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Could not load your sessions. Make sure you are connected and try again.
        </div>
      )}

      {sessions && sessions.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
            Previous Sessions
          </h2>
          <div className="space-y-3">
            {sessions.map(session => (
              <div
                key={session.id}
                className="rounded-lg border bg-card p-4 flex items-center justify-between gap-3"
              >
                {/* Left: meta */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className={cn('text-xs font-medium px-2 py-0.5 rounded-full', STATUS_COLORS[session.status])}>
                      {STATUS_LABEL[session.status]}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {session.completed_count}/{session.total_questions} answered
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {new Date(session.updated_at).toLocaleDateString('en-US', {
                      month: 'short', day: 'numeric', year: 'numeric',
                    })}
                  </p>
                </div>

                {/* Right: action */}
                {session.status === 'in_progress' ? (
                  <Link
                    to={`/workbook/${session.id}`}
                    className="text-sm font-medium text-primary flex items-center gap-1 min-h-[44px] px-2"
                  >
                    Resume <ArrowRight size={14} />
                  </Link>
                ) : (
                  <Link
                    to={`/workbook/${session.id}`}
                    className="text-sm font-medium text-muted-foreground flex items-center gap-1 min-h-[44px] px-2"
                  >
                    View <ArrowRight size={14} />
                  </Link>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {sessions && sessions.length === 0 && (
        <p className="text-sm text-center text-muted-foreground py-8">
          No questionnaires yet — start your first one above.
        </p>
      )}
    </div>
  )
}

export default SessionListPage
