import { useState } from 'react'
import { useTodos } from '@/hooks/useTodos'
import { Skeleton } from '@/components/ui/Skeleton'
import PillarSection from './PillarSection'
import RotationWeekView from './RotationWeekView'
import ScreeningAlert from './ScreeningAlert'
import ReferenceTab from './ReferenceTab'
import TaskDetailDrawer from './TaskDetailDrawer'
import { formatDate, formatPillar } from '@/lib/utils'
import { cn } from '@/lib/utils'
import { PILLAR_META } from '@/constants'

interface Tab {
  id: string
  label: string
  emoji: string
}

const EXERCISE_TAB: Tab = { id: 'exercise', label: 'Exercise', emoji: '🏋️' }
const ALL_TAB:      Tab = { id: 'all',      label: 'All',      emoji: '📋' }
const SUPPLEMENTS_TAB: Tab = { id: 'supplements_necessary', label: 'Supps TODO', emoji: '💊' }
const REFERENCE_TAB: Tab = { id: 'reference', label: 'Reference', emoji: '📚' }

const pillarToTab = (pillar: string): Tab => {
  const meta = PILLAR_META[pillar]
  return {
    id: pillar,
    label: meta?.label ?? formatPillar(pillar),
    emoji: meta?.emoji ?? '•',
  }
}

const TodayPage = () => {
  const { todosByPillar, necessarySupplements, summary, isLoading, error, toggleTodo } = useTodos()
  const today = formatDate(new Date().toISOString())

  const pillars = Object.keys(todosByPillar)
  const tabs: Tab[] = [
    ALL_TAB,
    ...pillars.map(pillarToTab),
    SUPPLEMENTS_TAB,
    EXERCISE_TAB,
    REFERENCE_TAB,
  ]

  const [activeTab, setActiveTab] = useState<string>('all')
  const [detailTemplateId, setDetailTemplateId] = useState<string | null>(null)

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Could not load today's tasks. Make sure the backend is running and a plan has been uploaded.
      </div>
    )
  }

  const activePillar = activeTab !== 'all' && activeTab !== 'exercise' && activeTab !== 'reference'
    && activeTab !== 'supplements_necessary'
    ? activeTab
    : null

  return (
    <div>
      <ScreeningAlert />

      {/* Day header */}
      <div className="mb-4 p-4 rounded-xl bg-primary/5 border border-primary/10">
        <p className="text-xs text-muted-foreground uppercase tracking-wide">{today}</p>
        {summary && (
          <>
            <p className="text-2xl xs:text-3xl md:text-4xl font-bold text-primary mt-1">{summary.completion_pct}%</p>
            <p className="text-sm md:text-base text-muted-foreground">
              {summary.completed} of {summary.total} tasks complete
            </p>
            <div className="h-2 bg-muted rounded-full mt-2">
              <div
                className="h-2 bg-primary rounded-full transition-all duration-500"
                style={{ width: `${summary.completion_pct}%` }}
              />
            </div>
          </>
        )}
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-4 overflow-x-auto pb-1 scrollbar-none">
        {tabs.map(tab => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1.5 xs:px-3 md:px-3.5 md:py-2 rounded-full text-[11px] xs:text-xs md:text-[13px] font-medium whitespace-nowrap transition-all shrink-0',
              activeTab === tab.id
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground',
            )}
          >
            <span>{tab.emoji}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Exercise — weekly rotation grid */}
      {activeTab === 'exercise' && <RotationWeekView />}

      {/* Necessary supplements — uses the same persisted DailyTodo rows */}
      {activeTab === 'supplements_necessary' && (
        necessarySupplements.length > 0 ? (
          <PillarSection
            pillar="supplements"
            todos={necessarySupplements}
            onToggle={toggleTodo}
            onOpenDetail={setDetailTemplateId}
            defaultOpen
          />
        ) : (
          <div className="text-center py-16 text-muted-foreground">
            <p className="text-4xl mb-3">💊</p>
            <p className="font-medium">No necessary supplements for today</p>
          </div>
        )
      )}

      {/* Reference — read-only reference items */}
      {activeTab === 'reference' && <ReferenceTab />}

      {/* All pillars */}
      {activeTab === 'all' && (
        pillars.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <p className="text-4xl mb-3">📋</p>
            <p className="font-medium">No tasks for today</p>
            <p className="text-sm mt-1">Upload an Excel plan to get started.</p>
          </div>
        ) : (
          <div>
            {pillars.map(pillar => (
              <PillarSection
                key={pillar}
                pillar={pillar}
                todos={todosByPillar[pillar]}
                onToggle={toggleTodo}
                onOpenDetail={setDetailTemplateId}
                defaultOpen={pillar === 'brief_today'}
              />
            ))}
          </div>
        )
      )}

      {/* Individual pillar tab */}
      {activePillar && (
        todosByPillar[activePillar] ? (
          <PillarSection
            pillar={activePillar}
            todos={todosByPillar[activePillar]}
            onToggle={toggleTodo}
            onOpenDetail={setDetailTemplateId}
            defaultOpen
          />
        ) : (
          <div className="text-center py-16 text-muted-foreground">
            <p className="text-4xl mb-3">{PILLAR_META[activePillar]?.emoji ?? '📋'}</p>
            <p className="font-medium">No {formatPillar(activePillar)} tasks today</p>
          </div>
        )
      )}

      {/* Task detail bottom drawer */}
      <TaskDetailDrawer
        templateId={detailTemplateId}
        onClose={() => setDetailTemplateId(null)}
      />
    </div>
  )
}

export default TodayPage
