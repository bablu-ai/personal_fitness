import { ChevronRight, Clock, Target } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { DailyTodo } from '@/types'

interface Props {
  todo: DailyTodo
  onToggle: (id: string, completed: boolean) => void
  onOpenDetail?: (templateId: string) => void
}

const TodoItem = ({ todo, onToggle, onOpenDetail }: Props) => {
  const { template } = todo
  const isMust = template.name.toLowerCase().startsWith('(must)')
  const displayName = isMust ? template.name.replace(/^\(must\)\s*/i, '') : template.name

  return (
    <div
      className={cn(
        'flex items-stretch rounded-lg border transition-all',
        todo.completed
          ? 'bg-muted/50 border-muted opacity-70'
          : 'bg-white border-border',
      )}
    >
      {/* Zone 1: checkbox — independent tap target */}
      <button
        type="button"
        onClick={() => onToggle(todo.id, !todo.completed)}
        aria-label={todo.completed ? 'Mark incomplete' : 'Mark complete'}
        className="flex-shrink-0 flex items-center justify-center w-11 min-h-[44px] rounded-l-lg hover:bg-accent/40 transition-colors"
      >
        <span
          className={cn(
            'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
            todo.completed ? 'bg-primary border-primary' : 'border-muted-foreground',
          )}
        >
          {todo.completed && (
            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          )}
        </span>
      </button>

      {/* Zone 2: content — tap to toggle (same as checkbox for convenience) */}
      <button
        type="button"
        onClick={() => onToggle(todo.id, !todo.completed)}
        className="flex-1 min-w-0 text-left py-2.5 pr-1"
      >
        <div className="flex items-center gap-1.5 min-w-0">
          {isMust && (
            <span className="shrink-0 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase leading-none text-amber-800">
              Must
            </span>
          )}
          <p className={cn('min-w-0 text-sm font-medium leading-snug', todo.completed && 'line-through text-muted-foreground')}>
            {displayName}
          </p>
        </div>
        {template.description && (
          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{template.description}</p>
        )}
        <div className="flex flex-wrap gap-2 mt-1">
          {template.target_value && (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Target size={11} />
              {template.target_value} {template.unit ?? ''}
            </span>
          )}
          {template.timing && (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Clock size={11} />
              {template.timing}
            </span>
          )}
        </div>
      </button>

      {/* Zone 3: detail chevron — only shown when detail is available */}
      {onOpenDetail && (
        <button
          type="button"
          onClick={() => onOpenDetail(template.id)}
          aria-label="View task detail"
          className="flex-shrink-0 flex items-center justify-center w-9 rounded-r-lg hover:bg-accent/40 transition-colors"
        >
          <ChevronRight size={15} className="text-muted-foreground" />
        </button>
      )}
    </div>
  )
}

export default TodoItem
