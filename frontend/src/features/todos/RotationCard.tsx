import { useState } from 'react'
import { CheckCircle, Circle, Dumbbell, CalendarDays } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useRotation } from '@/hooks/useRotation'

const RotationCard = () => {
  const { rotation, isLoading, toggleComplete, setStartDate, isSettingStartDate } = useRotation()
  const [startInput, setStartInput] = useState('')

  if (isLoading) {
    return <div className="h-24 rounded-xl bg-muted animate-pulse" />
  }

  // No rotation configured — show date picker to set start date
  if (!rotation) {
    return (
      <div className="rounded-xl border border-dashed border-border p-6 text-center space-y-4">
        <Dumbbell size={32} className="mx-auto text-muted-foreground" />
        <p className="text-sm font-medium">Set your 30-Day Rotation Start Date</p>
        <p className="text-xs text-muted-foreground">
          The rotation cycles through 30 workout days. Pick a start date to begin.
        </p>
        <div className="flex gap-2 justify-center">
          <input
            type="date"
            value={startInput}
            onChange={e => setStartInput(e.target.value)}
            className="rounded-lg border border-border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            type="button"
            disabled={!startInput || isSettingStartDate}
            onClick={() => startInput && setStartDate(startInput)}
            className={cn(
              'rounded-lg px-4 py-1.5 text-sm font-medium transition-colors',
              'bg-primary text-primary-foreground hover:bg-primary/90',
              'disabled:opacity-50 disabled:cursor-not-allowed',
            )}
          >
            {isSettingStartDate ? 'Saving…' : 'Start'}
          </button>
        </div>
      </div>
    )
  }

  const { day_number, block_name, sets, reps, duration, notes, completed_today, rotation_start_date } = rotation

  return (
    <div className={cn(
      'rounded-xl border p-4 transition-colors',
      completed_today ? 'border-green-200 bg-green-50' : 'border-border bg-card',
    )}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Day {day_number} of 30
            </span>
            {rotation_start_date && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <CalendarDays size={10} />
                started {rotation_start_date}
              </span>
            )}
          </div>
          <p className={cn('font-semibold text-base', completed_today && 'line-through text-muted-foreground')}>
            {block_name}
          </p>
        </div>
        <button
          type="button"
          onClick={() => toggleComplete(day_number, !completed_today)}
          className="shrink-0 mt-0.5"
          aria-label={completed_today ? 'Mark incomplete' : 'Mark complete'}
        >
          {completed_today
            ? <CheckCircle size={22} className="text-green-500" />
            : <Circle size={22} className="text-muted-foreground hover:text-primary transition-colors" />
          }
        </button>
      </div>

      {/* Details */}
      <div className="flex flex-wrap gap-3 mt-3">
        {sets && (
          <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
            {sets} sets
          </span>
        )}
        {reps && (
          <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
            {reps} reps
          </span>
        )}
        {duration && (
          <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
            {duration}
          </span>
        )}
      </div>

      {notes && (
        <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{notes}</p>
      )}

      {/* Change start date link */}
      <details className="mt-3">
        <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
          Change start date
        </summary>
        <div className="flex gap-2 mt-2">
          <input
            type="date"
            defaultValue={rotation_start_date ?? ''}
            onChange={e => setStartInput(e.target.value)}
            className="rounded-lg border border-border px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <button
            type="button"
            onClick={() => startInput && setStartDate(startInput)}
            className="rounded-lg px-3 py-1 text-xs font-medium bg-primary text-primary-foreground hover:bg-primary/90"
          >
            Save
          </button>
        </div>
      </details>
    </div>
  )
}

export default RotationCard
