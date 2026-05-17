import { useState } from 'react'
import { ChevronLeft, ChevronRight, CheckCircle, Circle, Clock, AlertCircle } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rotationApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { RotationWeekDay } from '@/types'

const DAY_ABBR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const addDays = (dateStr: string, n: number) => {
  const d = new Date(dateStr)
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0]
}

const getMondayOfWeek = (dateStr?: string) => {
  const d = dateStr ? new Date(dateStr) : new Date()
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  return d.toISOString().split('T')[0]
}

const formatMonthRange = (monday: string) => {
  const start = new Date(monday)
  const end = new Date(monday)
  end.setDate(end.getDate() + 6)
  const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' }
  return `${start.toLocaleDateString('en-US', opts)} – ${end.toLocaleDateString('en-US', opts)}`
}

interface DetailChipProps { label: string; value: string; color?: string }
const DetailChip = ({ label, value, color = 'bg-blue-50 text-blue-700' }: DetailChipProps) => (
  <div className={cn('rounded-lg p-2.5 flex flex-col gap-0.5', color)}>
    <span className="text-[10px] font-semibold uppercase tracking-wide opacity-70">{label}</span>
    <span className="text-xs font-medium leading-snug">{value}</span>
  </div>
)

interface TimeBudgetChipProps { label: string; minutes: string | null }
const TimeBudgetChip = ({ label, minutes }: TimeBudgetChipProps) => {
  if (!minutes) return null
  return (
    <div className="flex flex-col items-center bg-slate-50 border border-slate-200 rounded-lg px-2 py-1.5 min-w-[60px]">
      <span className="text-[10px] text-muted-foreground font-medium leading-tight text-center">{label}</span>
      <span className="text-sm font-bold text-slate-800">{minutes}<span className="text-[10px] font-normal"> min</span></span>
    </div>
  )
}

const ExerciseList = ({ label, value, color }: { label: string; value: string | null; color: string }) => {
  if (!value) return null
  const items = value.split(',').map(s => s.trim()).filter(Boolean)
  return (
    <div className={cn('rounded-lg p-3', color)}>
      <p className="text-[10px] font-semibold uppercase tracking-wide opacity-70 mb-1.5">{label}</p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex gap-1.5 text-xs font-medium">
            <span className="opacity-50 shrink-0">·</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

const RotationWeekView = () => {
  const [weekMonday, setWeekMonday] = useState(() => getMondayOfWeek())
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const weekKey = ['rotation', 'week', weekMonday] as const
  const { data: days = [], isLoading } = useQuery({
    queryKey: weekKey,
    queryFn: () => rotationApi.getWeek(weekMonday),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ day, date, completed }: { day: number; date: string; completed: boolean }) =>
      rotationApi.markCompleted(day, completed, date),
    onMutate: async ({ day, date, completed }) => {
      await queryClient.cancelQueries({ queryKey: weekKey })
      const prev = queryClient.getQueryData<RotationWeekDay[]>(weekKey)
      queryClient.setQueryData<RotationWeekDay[]>(weekKey, old =>
        old?.map(d =>
          d.calendar_date === date && d.rotation_day_number === day
            ? { ...d, completed }
            : d
        ) ?? []
      )
      return { prev }
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(weekKey, ctx.prev)
    },
  })

  const prevWeek = () => setWeekMonday(d => addDays(d, -7))
  const nextWeek = () => setWeekMonday(d => addDays(d, 7))

  const selected = days.find(d => d.calendar_date === selectedDate) ?? null

  // v4 data detected when time-budget or exercise-list fields are populated
  const isV4 = selected
    ? !!(selected.morning_time || selected.warm_up_min || selected.priority_exercises)
    : false

  const fits60ok = selected?.fits_60
    ? /^(yes|✓|true|1)$/i.test(selected.fits_60.trim())
    : null

  return (
    <div className="space-y-4">
      {/* Week navigation */}
      <div className="flex items-center justify-between">
        <button type="button" onClick={prevWeek} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
          <ChevronLeft size={18} />
        </button>
        <span className="text-sm font-medium">{formatMonthRange(weekMonday)}</span>
        <button type="button" onClick={nextWeek} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
          <ChevronRight size={18} />
        </button>
      </div>

      {/* 7-day grid */}
      {isLoading ? (
        <div className="grid grid-cols-7 gap-1">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="h-20 rounded-lg bg-muted animate-pulse" />
          ))}
        </div>
      ) : days.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground text-sm">
          No rotation set. Upload your workbook and set a start date.
        </div>
      ) : (
        <div className="grid grid-cols-7 gap-1">
          {days.map((d, i) => (
            <button
              key={d.calendar_date}
              type="button"
              onClick={() => setSelectedDate(prev => prev === d.calendar_date ? null : d.calendar_date)}
              className={cn(
                'flex flex-col items-center gap-1 p-2 rounded-xl border text-center transition-all min-h-[80px]',
                d.is_today
                  ? 'border-primary bg-primary/5 ring-1 ring-primary'
                  : 'border-border hover:border-primary/30 hover:bg-accent/20',
                selectedDate === d.calendar_date && 'border-primary bg-primary/10',
                d.completed && 'bg-green-50 border-green-200',
              )}
            >
              <span className="text-[10px] font-medium text-muted-foreground">{DAY_ABBR[i]}</span>
              <span className={cn('text-xs font-bold', d.is_today && 'text-primary')}>
                {new Date(d.calendar_date).getDate()}
              </span>
              <span className="text-[9px] text-muted-foreground leading-tight">
                D{d.rotation_day_number}
              </span>
              <span className="text-[9px] leading-tight line-clamp-2 text-center">
                {d.block_name.length > 10 ? d.block_name.slice(0, 9) + '…' : d.block_name}
              </span>
              {d.completed && <CheckCircle size={10} className="text-green-500 shrink-0" />}
            </button>
          ))}
        </div>
      )}

      {/* Selected day detail panel */}
      {selected && (
        <div className={cn(
          'rounded-xl border p-4 transition-colors space-y-4',
          selected.completed ? 'border-green-200 bg-green-50' : 'border-border',
        )}>
          {/* Title + complete toggle */}
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs text-muted-foreground mb-1">
                {selected.day_of_week},{' '}
                {new Date(selected.calendar_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                {' · '}Day {selected.rotation_day_number} of 30
              </p>
              <p className={cn('font-semibold text-base', selected.completed && 'line-through text-muted-foreground')}>
                {selected.block_name}
              </p>
              {/* morning_time — v4 only */}
              {selected.morning_time && (
                <p className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
                  <Clock size={11} />
                  {selected.morning_time}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={() => toggleMutation.mutate({
                day: selected.rotation_day_number,
                date: selected.calendar_date,
                completed: !selected.completed,
              })}
              aria-label={selected.completed ? 'Mark incomplete' : 'Mark complete'}
            >
              {selected.completed
                ? <CheckCircle size={22} className="text-green-500" />
                : <Circle size={22} className="text-muted-foreground hover:text-primary transition-colors" />
              }
            </button>
          </div>

          {/* === V4 LAYOUT === */}
          {isV4 && (
            <>
              {/* Time budget strip */}
              {(selected.warm_up_min || selected.upper_back_core_min || selected.secondary_min ||
                selected.cool_down_min || selected.total_min) && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                    Time budget
                  </p>
                  <div className="flex flex-wrap gap-1.5 items-start">
                    <TimeBudgetChip label="Warm-up" minutes={selected.warm_up_min} />
                    <TimeBudgetChip label="Upper back+core" minutes={selected.upper_back_core_min} />
                    <TimeBudgetChip label="Secondary" minutes={selected.secondary_min} />
                    <TimeBudgetChip label="Cool-down" minutes={selected.cool_down_min} />
                    {selected.total_min && (
                      <div className="flex flex-col items-center bg-primary/10 border border-primary/20 rounded-lg px-2 py-1.5 min-w-[60px]">
                        <span className="text-[10px] text-primary font-medium leading-tight">Total</span>
                        <span className="text-sm font-bold text-primary">
                          {selected.total_min}<span className="text-[10px] font-normal"> min</span>
                        </span>
                      </div>
                    )}
                    {/* Fits 60? badge */}
                    {selected.fits_60 && (
                      <div className={cn(
                        'flex items-center gap-1 rounded-lg px-2 py-1.5 border text-xs font-semibold',
                        fits60ok
                          ? 'bg-green-50 border-green-200 text-green-700'
                          : 'bg-amber-50 border-amber-200 text-amber-700',
                      )}>
                        {fits60ok
                          ? <CheckCircle size={11} />
                          : <AlertCircle size={11} />
                        }
                        Fits 60 min
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Exercise lists */}
              {(selected.priority_exercises || selected.secondary_exercises) && (
                <div className="space-y-2">
                  <ExerciseList
                    label="Priority exercises"
                    value={selected.priority_exercises}
                    color="bg-blue-50 text-blue-800"
                  />
                  <ExerciseList
                    label="Secondary exercises"
                    value={selected.secondary_exercises}
                    color="bg-indigo-50 text-indigo-800"
                  />
                </div>
              )}

              {/* Week rule */}
              {selected.week_rule && (
                <div className="bg-orange-50 border border-orange-100 rounded-lg px-3 py-2">
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-orange-700 mb-0.5">Week rule</p>
                  <p className="text-xs text-orange-900 font-medium">{selected.week_rule}</p>
                </div>
              )}
            </>
          )}

          {/* === V3 LAYOUT (fallback when v4 fields are null) === */}
          {!isV4 && (
            <>
              {/* Volume chips */}
              {(selected.sets || selected.reps || selected.duration || selected.intensity_cap) && (
                <div className="flex flex-wrap gap-2">
                  {selected.sets && (
                    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                      {selected.sets} sets
                    </span>
                  )}
                  {selected.reps && (
                    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                      {selected.reps} reps
                    </span>
                  )}
                  {selected.duration && (
                    <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
                      {selected.duration}
                    </span>
                  )}
                  {selected.intensity_cap && (
                    <span className="text-xs bg-orange-50 text-orange-700 px-2 py-0.5 rounded-full font-medium">
                      RPE {selected.intensity_cap}
                    </span>
                  )}
                </div>
              )}

              {/* Workout structure grid */}
              {(selected.warm_up || selected.priority_block || selected.secondary_block ||
                selected.cardio_steps || selected.cool_down || selected.nutrition_focus) && (
                <div className="grid grid-cols-2 gap-2">
                  {selected.warm_up && (
                    <DetailChip label="Warm-up" value={selected.warm_up} color="bg-yellow-50 text-yellow-800" />
                  )}
                  {selected.priority_block && (
                    <DetailChip label="Priority block" value={selected.priority_block} color="bg-blue-50 text-blue-800" />
                  )}
                  {selected.secondary_block && (
                    <DetailChip label="Secondary block" value={selected.secondary_block} color="bg-indigo-50 text-indigo-800" />
                  )}
                  {selected.cardio_steps && (
                    <DetailChip label="Cardio / steps" value={selected.cardio_steps} color="bg-green-50 text-green-800" />
                  )}
                  {selected.cool_down && (
                    <DetailChip label="Cool-down" value={selected.cool_down} color="bg-teal-50 text-teal-800" />
                  )}
                  {selected.nutrition_focus && (
                    <DetailChip label="Nutrition focus" value={selected.nutrition_focus} color="bg-rose-50 text-rose-800" />
                  )}
                </div>
              )}
            </>
          )}

          {/* Notes (shown in both v3 and v4) */}
          {selected.notes && (
            <p className="text-xs text-muted-foreground border-t pt-3">{selected.notes}</p>
          )}
        </div>
      )}
    </div>
  )
}

export default RotationWeekView
