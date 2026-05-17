import { useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useScreenings } from '@/hooks/useScreenings'
import type { Screening } from '@/types'

const frequencyLabel = (months: number | null) => {
  if (!months) return ''
  if (months === 1) return 'monthly'
  if (months === 3) return 'quarterly'
  if (months === 6) return 'biannual'
  if (months === 12) return 'annual'
  if (months % 12 === 0) return `every ${months / 12} years`
  return `every ${months} months`
}

const dueBadge = (s: Screening) => {
  if (s.due_in_days === null) return null
  if (s.due_in_days < 0)
    return <span className="text-xs font-semibold text-red-600">Overdue by {Math.abs(s.due_in_days)}d</span>
  if (s.due_in_days === 0)
    return <span className="text-xs font-semibold text-orange-500">Due today</span>
  return <span className="text-xs text-amber-600">Due in {s.due_in_days}d</span>
}

const ScreeningAlert = () => {
  const { dueScreenings, isLoading, markDone } = useScreenings()
  const [expanded, setExpanded] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  if (isLoading || dismissed || dueScreenings.length === 0) return null

  const overdueCount = dueScreenings.filter(s => s.is_overdue).length
  const shown = expanded ? dueScreenings : dueScreenings.slice(0, 2)

  return (
    <div className={cn(
      'rounded-xl border p-3 mb-4',
      overdueCount > 0
        ? 'border-red-200 bg-red-50'
        : 'border-amber-200 bg-amber-50',
    )}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertTriangle size={15} className={overdueCount > 0 ? 'text-red-500' : 'text-amber-500'} />
          <span className="text-sm font-semibold">
            {overdueCount > 0
              ? `${overdueCount} screening${overdueCount > 1 ? 's' : ''} overdue`
              : `${dueScreenings.length} screening${dueScreenings.length > 1 ? 's' : ''} due soon`}
          </span>
        </div>
        <button type="button" onClick={() => setDismissed(true)} aria-label="Dismiss">
          <X size={14} className="text-muted-foreground hover:text-foreground" />
        </button>
      </div>

      {/* Items */}
      <ul className="mt-2 space-y-2">
        {shown.map(s => (
          <li key={s.id} className="flex items-start justify-between gap-2 text-sm">
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{s.name}</p>
              <div className="flex items-center gap-2 flex-wrap">
                {dueBadge(s)}
                {s.frequency_months && (
                  <span className="text-xs text-muted-foreground capitalize">
                    {frequencyLabel(s.frequency_months)}
                  </span>
                )}
                {s.last_done_date && (
                  <span className="text-xs text-muted-foreground">last: {s.last_done_date}</span>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={() => markDone(s.id)}
              className="shrink-0 flex items-center gap-1 text-xs px-2 py-1 rounded-lg bg-white border border-border hover:bg-green-50 hover:border-green-300 transition-colors"
            >
              <CheckCircle2 size={12} />
              Done
            </button>
          </li>
        ))}
      </ul>

      {/* Show more / less */}
      {dueScreenings.length > 2 && (
        <button
          type="button"
          onClick={() => setExpanded(e => !e)}
          className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          {expanded
            ? <><ChevronUp size={12} /> Show less</>
            : <><ChevronDown size={12} /> Show {dueScreenings.length - 2} more</>}
        </button>
      )}
    </div>
  )
}

export default ScreeningAlert
