import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  X, Play, ShieldAlert, BookOpen, Lightbulb,
  Target, Dumbbell, AlertTriangle, TrendingUp, Settings,
} from 'lucide-react'
import { todosApi } from '@/lib/api'
import { QUERY_KEYS } from '@/constants'
import { cn } from '@/lib/utils'
import type { Exercise } from '@/types'

interface Props {
  templateId: string | null
  onClose: () => void
}

// ── Text rendering helpers ────────────────────────────────────────────────

/** Split multi-line or bullet text into a visual list. Single lines render as a paragraph. */
const BulletText = ({ text, className }: { text: string; className?: string }) => {
  const lines = text.split(/\n+/).map(l => l.trim()).filter(Boolean)
  if (lines.length <= 1) {
    return <p className={cn('text-sm md:text-base leading-relaxed', className)}>{text}</p>
  }
  return (
    <ul className={cn('space-y-1.5', className)}>
      {lines.map((line, i) => (
        <li key={i} className="flex gap-2 text-sm md:text-base leading-relaxed">
          <span className="text-primary shrink-0 mt-0.5 font-bold">·</span>
          <span>{line.replace(/^[-•*·]\s*/, '')}</span>
        </li>
      ))}
    </ul>
  )
}

/** Numbered steps for how-to instructions — detects "1." "2." prefixes or just numbers lines. */
const StepText = ({ text, className }: { text: string; className?: string }) => {
  const lines = text.split(/\n+/).map(l => l.trim()).filter(Boolean)
  if (lines.length <= 1) {
    return <p className={cn('text-sm md:text-base leading-relaxed', className)}>{text}</p>
  }
  const isNumbered = lines[0].match(/^\d+[.)]\s/)
  if (isNumbered) {
    return (
      <ol className={cn('space-y-1.5 list-none', className)}>
        {lines.map((line, i) => (
          <li key={i} className="flex gap-2.5 text-sm md:text-base leading-relaxed">
            <span className="shrink-0 w-5 h-5 rounded-full bg-primary/10 text-primary text-[11px] font-bold flex items-center justify-center mt-0.5">
              {i + 1}
            </span>
            <span>{line.replace(/^\d+[.)]\s*/, '')}</span>
          </li>
        ))}
      </ol>
    )
  }
  return <BulletText text={text} className={className} />
}

// ── Section wrapper ───────────────────────────────────────────────────────

interface SectionProps {
  icon: React.ReactNode
  label: string
  color?: string
  children: React.ReactNode
}
const Section = ({ icon, label, color = 'text-muted-foreground', children }: SectionProps) => (
  <div className="mb-4">
    <div className={cn('flex items-center gap-1.5 mb-2 text-xs md:text-[13px] font-semibold uppercase tracking-wide', color)}>
      {icon}
      {label}
    </div>
    {children}
  </div>
)

// ── Extra metadata — well-known keys get dedicated display ────────────────

const KNOWN_KEYS: Record<string, { label: string; icon: React.ReactNode; style: string }> = {
  'setup':               { label: 'Setup',              icon: <Settings size={11} />,     style: 'text-slate-600' },
  'starting position':   { label: 'Starting position',  icon: <Settings size={11} />,     style: 'text-slate-600' },
  'core/bracing cue':    { label: 'Core & bracing cue', icon: <ShieldAlert size={11} />,  style: 'text-amber-600' },
  'common mistakes':     { label: 'Common mistakes',    icon: <AlertTriangle size={11} />, style: 'text-red-600' },
  'week 2 progression':  { label: 'Week 2 progression', icon: <TrendingUp size={11} />,   style: 'text-green-600' },
  'week 2 increase':     { label: 'Week 2 progression', icon: <TrendingUp size={11} />,   style: 'text-green-600' },
  'week_1':              { label: 'Week 1',             icon: <Target size={11} />,       style: 'text-primary' },
  'week_2':              { label: 'Week 2',             icon: <TrendingUp size={11} />,   style: 'text-green-600' },
  'progression':         { label: 'Progression',        icon: <TrendingUp size={11} />,   style: 'text-green-600' },
  'track':               { label: 'Track',              icon: <Target size={11} />,       style: 'text-primary' },
  'primary muscles':     { label: 'Muscles targeted',   icon: <Dumbbell size={11} />,     style: 'text-blue-600' },
  'muscles targeted':    { label: 'Muscles targeted',   icon: <Dumbbell size={11} />,     style: 'text-blue-600' },
}

// Keys to suppress from the "additional info" fallback (already shown elsewhere)
const SUPPRESSED_KEYS = new Set([
  'category', 'priority', 'week 1 easy start', 'if behind schedule', 'target duration',
  'must', 'exercise_names',
])

const ExtraMetadata = ({ meta }: { meta: Record<string, string> }) => {
  const known: Array<{ key: string; value: string; def: typeof KNOWN_KEYS[string] }> = []
  const rest: Array<[string, string]> = []

  for (const [k, v] of Object.entries(meta)) {
    const lower = k.toLowerCase()
    if (SUPPRESSED_KEYS.has(lower)) continue
    const def = KNOWN_KEYS[lower]
    if (def) {
      known.push({ key: k, value: v, def })
    } else {
      rest.push([k, v])
    }
  }

  if (known.length === 0 && rest.length === 0) return null

  return (
    <>
      {known.map(({ key, value, def }) => (
        <Section key={key} icon={def.icon} label={def.label} color={def.style}>
          <BulletText text={value} />
        </Section>
      ))}

      {rest.length > 0 && (
        <div className="mt-2 pt-3 border-t">
          <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-2">Additional info</p>
          <div className="space-y-1.5">
            {rest.map(([k, v]) => (
              <div key={k} className="flex gap-2 text-xs">
                <span className="text-muted-foreground font-medium shrink-0 min-w-[90px] md:min-w-[110px]">{k}:</span>
                <span className="text-foreground">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

// ── Exercise card — one per exercise in a workout block ───────────────────

const ExerciseCard = ({ ex }: { ex: Exercise }) => (
  <div className="rounded-lg border bg-muted/20 p-2.5 space-y-1.5">
    {/* Name + category badge */}
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-sm font-semibold">{ex.name}</span>
      {ex.category && (
        <span className="text-[10px] font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
          {ex.category}
        </span>
      )}
    </div>

    {/* Week 1 dosage */}
    {ex.week1_dosage && (
      <p className="flex items-center gap-1 text-xs font-semibold text-primary">
        <Target size={10} className="shrink-0" />
        {ex.week1_dosage}
      </p>
    )}

    {/* Setup */}
    {ex.setup && (
      <div className="flex items-start gap-1.5 text-xs md:text-sm text-muted-foreground">
        <Settings size={10} className="shrink-0 mt-0.5" />
        <span><span className="font-medium">Setup: </span>{ex.setup}</span>
      </div>
    )}

    {/* Starting position */}
    {ex.starting_position && (
      <p className="text-xs md:text-sm text-muted-foreground pl-4">{ex.starting_position}</p>
    )}

    {/* Step-by-step how-to */}
    {ex.how_to && <StepText text={ex.how_to} className="text-muted-foreground" />}

    {/* Bracing cue */}
    {ex.bracing_cue && (
      <div className="flex items-start gap-1.5 text-xs bg-amber-50 text-amber-800 rounded px-2 py-1.5">
        <ShieldAlert size={10} className="shrink-0 mt-0.5" />
        <span><span className="font-semibold">Brace: </span>{ex.bracing_cue}</span>
      </div>
    )}

    {/* Common mistakes */}
    {ex.common_mistakes && (
      <div className="flex items-start gap-1.5 text-xs bg-red-50 text-red-800 rounded px-2 py-1.5">
        <AlertTriangle size={10} className="shrink-0 mt-0.5" />
        <span><span className="font-semibold">Avoid: </span>{ex.common_mistakes}</span>
      </div>
    )}

    {/* Safety */}
    {ex.safety_notes && (
      <p className="text-xs text-amber-700 border border-amber-200 rounded px-2 py-1">
        {ex.safety_notes}
      </p>
    )}

    {/* Why it matters */}
    {ex.why_it_matters && (
      <p className="text-xs text-muted-foreground italic border-t pt-1.5">{ex.why_it_matters}</p>
    )}

    {/* Video / GIF links */}
    {(ex.video_link || ex.gif_link) && (
      <div className="flex gap-2 pt-0.5">
        {ex.video_link && (
          <a
            href={ex.video_link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-red-500 font-medium hover:underline"
          >
            <Play size={10} fill="currentColor" /> Watch demo
          </a>
        )}
        {ex.gif_link && (
          <a
            href={ex.gif_link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-muted-foreground font-medium hover:underline"
          >
            View GIF
          </a>
        )}
      </div>
    )}
  </div>
)

// ── Main drawer ───────────────────────────────────────────────────────────

const TaskDetailDrawer = ({ templateId, onClose }: Props) => {
  const { data: detail, isLoading } = useQuery({
    queryKey: QUERY_KEYS.taskDetail(templateId ?? ''),
    queryFn: () => todosApi.getDetail(templateId!),
    enabled: !!templateId,
  })

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  const isOpen = !!templateId

  // Merge why_mechanism into description for display — both are "why" content
  const whyText = detail
    ? [detail.why_mechanism, detail.description].filter(Boolean).join('\n\n')
    : null

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          'fixed inset-0 bg-black/40 z-40 transition-opacity duration-200',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none',
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Task detail"
        className={cn(
          'fixed bottom-0 left-0 right-0 md:left-1/2 md:-translate-x-1/2 md:w-[620px] lg:w-[680px] z-50 bg-background rounded-t-2xl md:rounded-t-3xl shadow-2xl',
          'transition-transform duration-300 max-h-[85dvh] flex flex-col',
          isOpen ? 'translate-y-0' : 'translate-y-full',
        )}
      >
        {/* Drag handle */}
        <div className="flex justify-center pt-3 pb-1 shrink-0">
          <div className="w-10 h-1 rounded-full bg-muted-foreground/30" />
        </div>

        {/* Header */}
        <div className="flex items-start justify-between px-5 pt-2 pb-3 border-b shrink-0">
          <div className="flex-1 pr-3">
            {isLoading && <div className="h-5 w-48 bg-muted animate-pulse rounded mt-1" />}
            {detail && (
              <>
                {/* Timing + pillar badges */}
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  {detail.timing && (
                    <span className="text-xs font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                      {detail.timing}
                    </span>
                  )}
                  <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                    {detail.pillar.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {detail.name.toLowerCase().startsWith('(must)') && (
                    <span className="shrink-0 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase leading-none text-amber-800">
                      Must
                    </span>
                  )}
                  <h2 className="text-base font-semibold leading-snug">
                    {detail.name.replace(/^\(must\)\s*/i, '')}
                  </h2>
                </div>
              </>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="p-1.5 rounded-lg hover:bg-muted transition-colors shrink-0"
          >
            <X size={18} />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto px-4 md:px-5 pt-3 pb-8 flex-1">
          {isLoading && (
            <div className="space-y-3">
              {[80, 60, 90, 70].map((w, i) => (
                <div key={i} className={`h-4 bg-muted animate-pulse rounded`} style={{ width: `${w}%` }} />
              ))}
            </div>
          )}

          {detail && (
            <>
              {/* Target / dosage / sets-reps — shown prominently */}
              {detail.target_value && (
                <div className="flex items-center gap-2 mb-5">
                  <Target size={14} className="text-primary shrink-0" />
                  <span className="text-sm font-semibold text-primary">
                    {detail.target_value}
                    {detail.unit ? ` ${detail.unit}` : ''}
                  </span>
                </div>
              )}

              {/* Why — description is the "why" content from the spreadsheet */}
              {whyText && (
                <Section icon={<Lightbulb size={11} />} label="Why" color="text-yellow-700">
                  <BulletText text={whyText} />
                </Section>
              )}

              {/* How to — rendered as numbered steps when multi-line */}
              {detail.how_to && (
                <Section icon={<BookOpen size={11} />} label="How to" color="text-blue-700">
                  <StepText text={detail.how_to} />
                </Section>
              )}

              {/* Safety notes */}
              {detail.safety_notes && (
                <Section icon={<ShieldAlert size={11} />} label="Safety / pain rule" color="text-amber-700">
                  <div className="bg-amber-50 border border-amber-100 rounded-lg p-3">
                    <BulletText text={detail.safety_notes} className="text-amber-800" />
                  </div>
                </Section>
              )}

              {/* Rich extra_metadata fields */}
              {detail.extra_metadata && Object.keys(detail.extra_metadata).length > 0 && (
                <ExtraMetadata meta={detail.extra_metadata as Record<string, string>} />
              )}

              {/* Video + reference links */}
              {(detail.video_link || detail.link) && (
                <div className="flex flex-wrap gap-2 mb-5">
                  {detail.video_link && (
                    <a
                      href={detail.video_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded-full transition-colors"
                    >
                      <Play size={12} fill="white" /> Watch demo
                    </a>
                  )}
                  {detail.link && (
                    <a
                      href={detail.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground bg-muted px-3 py-1.5 rounded-full hover:bg-muted/80 transition-colors"
                    >
                      View GIF / reference
                    </a>
                  )}
                </div>
              )}

              {/* Exercises — populated for workout blocks from exercise_library */}
              {detail.exercises.length > 0 && (
                <Section icon={<Dumbbell size={11} />} label="Exercises" color="text-violet-700">
                  <div className="space-y-2.5">
                    {detail.exercises.map((ex: Exercise, i: number) => (
                      <ExerciseCard key={i} ex={ex} />
                    ))}
                  </div>
                </Section>
              )}

              {/* Source key — subtle footer */}
              {detail.source_key && (
                <p className="text-[10px] text-muted-foreground border-t pt-3 mt-2">
                  Source: {detail.source_key}
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </>
  )
}

export default TaskDetailDrawer
