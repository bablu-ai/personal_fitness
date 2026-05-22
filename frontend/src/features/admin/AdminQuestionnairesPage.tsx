import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Search, ShieldAlert } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  downloadQuestionnaireExport,
  getAdminQuestionnaireSession,
  isForbidden,
  listAdminQuestionnaireSessions,
  type AdminQuestionnaireSession,
} from './api/adminQuestionnaires'

const STATUS_OPTIONS = ['all', 'in_progress', 'completed', 'generating', 'plan_generated', 'failed']

const formatDateTime = (value: string): string =>
  new Date(value).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })

const userLabel = (session: AdminQuestionnaireSession): string =>
  session.user_email || session.user_id

const AdminQuestionnairesPage = () => {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')
  const [dateFilter, setDateFilter] = useState('')
  const [exporting, setExporting] = useState(false)

  const sessionsQuery = useQuery({
    queryKey: ['admin-questionnaire-sessions'],
    queryFn: listAdminQuestionnaireSessions,
  })

  const detailQuery = useQuery({
    queryKey: ['admin-questionnaire-session', selectedId],
    queryFn: () => getAdminQuestionnaireSession(selectedId as string),
    enabled: Boolean(selectedId),
  })

  const filteredSessions = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return (sessionsQuery.data ?? []).filter(session => {
      const matchesSearch = !needle || userLabel(session).toLowerCase().includes(needle)
      const matchesStatus = status === 'all' || session.status === status
      const matchesDate = !dateFilter || session.created_at.slice(0, 10) === dateFilter
      return matchesSearch && matchesStatus && matchesDate
    })
  }, [dateFilter, search, sessionsQuery.data, status])

  const forbidden = isForbidden(sessionsQuery.error) || isForbidden(detailQuery.error)

  const handleExport = async () => {
    if (!selectedId) return
    setExporting(true)
    try {
      await downloadQuestionnaireExport(selectedId)
    } finally {
      setExporting(false)
    }
  }

  if (forbidden) {
    return (
      <div className="mx-auto max-w-3xl py-8">
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-800">
          <div className="flex items-center gap-2 font-semibold">
            <ShieldAlert size={18} />
            Not authorized
          </div>
          <p className="mt-2 text-sm">Your account is not listed in backend ADMIN_EMAILS.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5 py-4 lg:max-w-none">
      <div>
        <h1 className="text-2xl font-bold">Questionnaire Admin</h1>
        <p className="text-sm text-muted-foreground">
          Review completed and in-progress questionnaires, then export exact question and answer text.
        </p>
      </div>

      {sessionsQuery.error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Could not load questionnaire sessions.
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
        <section className="space-y-3">
          <div className="grid gap-2 rounded-lg border bg-card p-3">
            <label className="relative block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
              <input
                value={search}
                onChange={event => setSearch(event.target.value)}
                placeholder="Search user email"
                className="h-10 w-full rounded-md border bg-background pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary/30"
              />
            </label>
            <div className="grid grid-cols-2 gap-2">
              <select
                value={status}
                onChange={event => setStatus(event.target.value)}
                className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary/30"
              >
                {STATUS_OPTIONS.map(option => (
                  <option key={option} value={option}>
                    {option === 'all' ? 'All status' : option.replace('_', ' ')}
                  </option>
                ))}
              </select>
              <input
                type="date"
                value={dateFilter}
                onChange={event => setDateFilter(event.target.value)}
                className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>

          <div className="overflow-hidden rounded-lg border bg-card">
            {sessionsQuery.isLoading && (
              <div className="p-4 text-sm text-muted-foreground">Loading sessions...</div>
            )}
            {!sessionsQuery.isLoading && filteredSessions.length === 0 && (
              <div className="p-4 text-sm text-muted-foreground">No sessions match the filters.</div>
            )}
            {filteredSessions.map(session => (
              <button
                key={session.id}
                type="button"
                onClick={() => setSelectedId(session.id)}
                className={cn(
                  'block w-full border-b px-3 py-3 text-left last:border-b-0 hover:bg-muted/40',
                  selectedId === session.id && 'bg-primary/10',
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-semibold">{userLabel(session)}</span>
                  <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium">
                    {session.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
                  <span>{session.completed_count}/{session.total_questions} answered</span>
                  <span>{formatDateTime(session.updated_at)}</span>
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="min-h-[460px] rounded-lg border bg-card">
          {!selectedId && (
            <div className="p-6 text-sm text-muted-foreground">Select a questionnaire session to review it.</div>
          )}

          {selectedId && detailQuery.isLoading && (
            <div className="p-6 text-sm text-muted-foreground">Loading questionnaire...</div>
          )}

          {detailQuery.data && (
            <div className="divide-y">
              <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold">{userLabel(detailQuery.data.session)}</h2>
                  <p className="text-xs text-muted-foreground">
                    Created {formatDateTime(detailQuery.data.session.created_at)} · Version {detailQuery.data.session.questionnaire_version}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleExport}
                  disabled={exporting}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                >
                  <Download size={16} />
                  {exporting ? 'Exporting' : 'Export text'}
                </button>
              </div>

              <div className="max-h-[70vh] overflow-y-auto">
                {detailQuery.data.questions.map(item => (
                  <article key={item.question_id} className="p-4">
                    <div className="flex gap-3">
                      <div className="shrink-0 rounded-md bg-muted px-2 py-1 text-xs font-bold">
                        Q{item.question_number}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold leading-6">{item.question_text}</p>
                        <p className="mt-2 whitespace-pre-wrap rounded-md bg-muted/60 p-3 text-sm">
                          {item.formatted_answer || <span className="text-muted-foreground">No answer</span>}
                        </p>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default AdminQuestionnairesPage
