import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { cn, formatPillar } from '@/lib/utils'
import { PILLAR_META, DEFAULT_PILLAR_COLOR } from '@/constants'
import type { DailyTodo } from '@/types'
import TodoItem from './TodoItem'
import BriefTodayTimeline from './BriefTodayTimeline'

interface Props {
  pillar: string
  todos: DailyTodo[]
  onToggle: (id: string, completed: boolean) => void
  onOpenDetail?: (templateId: string) => void
  defaultOpen?: boolean
}

const PillarSection = ({ pillar, todos, onToggle, onOpenDetail, defaultOpen = false }: Props) => {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const meta = PILLAR_META[pillar]
  const completed = todos.filter(t => t.completed).length
  const pct = todos.length ? Math.round((completed / todos.length) * 100) : 0

  return (
    <section className="mb-3 border border-border rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-muted/30 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isOpen
            ? <ChevronDown size={14} className="text-muted-foreground" />
            : <ChevronRight size={14} className="text-muted-foreground" />
          }
          {meta?.emoji && <span className="text-base">{meta.emoji}</span>}
          <span className={cn('text-xs font-semibold px-2 py-0.5 rounded-full', meta?.color ?? DEFAULT_PILLAR_COLOR)}>
            {meta?.label ?? formatPillar(pillar)}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-16 h-1.5 bg-muted rounded-full">
            <div
              className="h-1.5 bg-primary rounded-full transition-all duration-300"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground min-w-[60px] text-right">
            {completed}/{todos.length} · {pct}%
          </span>
        </div>
      </button>

      {isOpen && (
        <div className="p-3">
          {pillar === 'brief_today' ? (
            <BriefTodayTimeline todos={todos} onToggle={onToggle} onOpenDetail={onOpenDetail} />
          ) : (
            <div className="flex flex-col gap-2">
              {todos.map(todo => (
                <TodoItem key={todo.id} todo={todo} onToggle={onToggle} onOpenDetail={onOpenDetail} />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export default PillarSection
