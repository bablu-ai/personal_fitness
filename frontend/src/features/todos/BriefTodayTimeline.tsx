import type { DailyTodo } from '@/types'
import TodoItem from './TodoItem'

interface Props {
  todos: DailyTodo[]
  onToggle: (id: string, completed: boolean) => void
  onOpenDetail?: (templateId: string) => void
}

// Extract an integer hour from timing strings like "7:00 AM", "Morning", "6-7 AM", "Evening"
const timingToHour = (timing: string | null): number => {
  if (!timing) return 25  // no timing → sort last

  const s = timing.trim().toLowerCase()

  // Named periods
  if (s.includes('morning') || s.includes('wake'))  return 7
  if (s.includes('midday') || s.includes('noon'))   return 12
  if (s.includes('afternoon'))                       return 14
  if (s.includes('evening'))                         return 18
  if (s.includes('night') || s.includes('bedtime')) return 21
  if (s.includes('bed'))                             return 22

  // "HH:MM AM/PM" or "H:MM AM/PM"
  const clockMatch = s.match(/(\d{1,2})(?::(\d{2}))?\s*(am|pm)?/)
  if (clockMatch) {
    let hour = parseInt(clockMatch[1], 10)
    const ampm = clockMatch[3]
    if (ampm === 'pm' && hour !== 12) hour += 12
    if (ampm === 'am' && hour === 12) hour = 0
    return hour
  }

  return 25
}

// Format hour back to a readable label
const hourLabel = (hour: number): string => {
  if (hour === 25) return 'Anytime'
  const h = hour % 12 || 12
  return `${h}:00 ${hour < 12 ? 'AM' : 'PM'}`
}

const BriefTodayTimeline = ({ todos, onToggle, onOpenDetail }: Props) => {
  // Group todos by hour
  const groups = new Map<number, DailyTodo[]>()
  for (const todo of todos) {
    const hour = timingToHour(todo.template.timing)
    if (!groups.has(hour)) groups.set(hour, [])
    groups.get(hour)!.push(todo)
  }

  const sortedHours = [...groups.keys()].sort((a, b) => a - b)

  return (
    <div className="space-y-4">
      {sortedHours.map(hour => (
        <div key={hour} className="flex gap-3">
          {/* Time gutter */}
          <div className="w-16 shrink-0 pt-2.5 text-right">
            <span className="text-[11px] font-medium text-muted-foreground">{hourLabel(hour)}</span>
          </div>

          {/* Vertical line + items */}
          <div className="flex gap-2 flex-1">
            <div className="flex flex-col items-center">
              <div className="w-2 h-2 rounded-full bg-primary mt-3 shrink-0" />
              {groups.get(hour)!.length > 1 && (
                <div className="w-px flex-1 bg-border mt-1" />
              )}
            </div>
            <div className="flex-1 space-y-1.5 pb-1">
              {groups.get(hour)!.map(todo => (
                <TodoItem
                  key={todo.id}
                  todo={todo}
                  onToggle={onToggle}
                  onOpenDetail={onOpenDetail}
                />
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default BriefTodayTimeline
