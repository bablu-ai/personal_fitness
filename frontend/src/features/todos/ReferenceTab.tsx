import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, ExternalLink, Play } from 'lucide-react'
import { referenceApi } from '@/lib/api'
import { QUERY_KEYS, PILLAR_META, DEFAULT_PILLAR_COLOR } from '@/constants'
import { cn, formatPillar } from '@/lib/utils'
import type { TaskTemplate } from '@/types'

const ReferenceCard = ({ item }: { item: TaskTemplate }) => {
  const [expanded, setExpanded] = useState(false)
  const hasDetail = !!(item.why_mechanism || item.how_to || item.safety_notes || item.video_link || item.link)

  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => hasDetail && setExpanded(e => !e)}
        className={cn(
          'w-full flex items-start gap-3 p-3 text-left transition-colors',
          hasDetail ? 'hover:bg-accent/20 cursor-pointer' : 'cursor-default',
        )}
      >
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">{item.name}</p>
          {item.description && (
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{item.description}</p>
          )}
          <div className="flex flex-wrap gap-2 mt-1">
            {item.target_value && (
              <span className="text-xs text-muted-foreground">
                Target: {item.target_value} {item.unit ?? ''}
              </span>
            )}
            {item.timing && (
              <span className="text-xs text-muted-foreground">· {item.timing}</span>
            )}
          </div>
        </div>
        {hasDetail && (
          expanded
            ? <ChevronDown size={14} className="text-muted-foreground shrink-0 mt-0.5" />
            : <ChevronRight size={14} className="text-muted-foreground shrink-0 mt-0.5" />
        )}
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2.5 border-t bg-muted/20 pt-3">
          {item.why_mechanism && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-0.5">Why it works</p>
              <p className="text-xs leading-relaxed">{item.why_mechanism}</p>
            </div>
          )}
          {item.how_to && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-0.5">How to</p>
              <p className="text-xs leading-relaxed">{item.how_to}</p>
            </div>
          )}
          {item.safety_notes && (
            <p className="text-xs text-amber-700 bg-amber-50 rounded-lg p-2">{item.safety_notes}</p>
          )}
          <div className="flex gap-2 flex-wrap">
            {item.video_link && (
              <a
                href={item.video_link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
              >
                <Play size={11} /> Watch
              </a>
            )}
            {item.link && (
              <a
                href={item.link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:underline"
              >
                <ExternalLink size={11} /> Learn more
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const PillarGroup = ({ pillar, items }: { pillar: string; items: TaskTemplate[] }) => {
  const [open, setOpen] = useState(true)
  const meta = PILLAR_META[pillar]

  return (
    <section className="mb-4">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 mb-2 w-full text-left"
      >
        {open
          ? <ChevronDown size={13} className="text-muted-foreground" />
          : <ChevronRight size={13} className="text-muted-foreground" />
        }
        {meta?.emoji && <span>{meta.emoji}</span>}
        <span className={cn('text-xs font-semibold px-2 py-0.5 rounded-full', meta?.color ?? DEFAULT_PILLAR_COLOR)}>
          {meta?.label ?? formatPillar(pillar)}
        </span>
        <span className="text-xs text-muted-foreground ml-1">{items.length}</span>
      </button>

      {open && (
        <div className="space-y-1.5 pl-5">
          {items.map(item => (
            <ReferenceCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </section>
  )
}

const ReferenceTab = () => {
  const { data: items = [], isLoading, error } = useQuery({
    queryKey: QUERY_KEYS.reference,
    queryFn: referenceApi.getAll,
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map(i => <div key={i} className="h-16 bg-muted animate-pulse rounded-xl" />)}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Could not load reference items.
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <p className="text-4xl mb-3">📚</p>
        <p className="font-medium">No reference items yet</p>
        <p className="text-sm mt-1">Upload a plan with nutrition, sleep, or cognitive sheets.</p>
      </div>
    )
  }

  // Group by pillar
  const byPillar = items.reduce<Record<string, TaskTemplate[]>>((acc, item) => {
    if (!acc[item.pillar]) acc[item.pillar] = []
    acc[item.pillar].push(item)
    return acc
  }, {})

  return (
    <div>
      {Object.entries(byPillar).map(([pillar, pillarItems]) => (
        <PillarGroup key={pillar} pillar={pillar} items={pillarItems} />
      ))}
    </div>
  )
}

export default ReferenceTab
