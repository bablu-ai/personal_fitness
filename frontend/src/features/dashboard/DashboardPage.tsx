import { useState } from 'react'
import { useDashboard } from '@/hooks/useDashboard'
import { useBenefits } from '@/hooks/useBenefits'
import { Skeleton } from '@/components/ui/Skeleton'
import { DailyTable, WeeklyTable, MonthlyTable } from './CompletionTable'
import BenefitScoreCards from './BenefitScoreCards'

type View = 'daily' | 'weekly' | 'monthly'

const DashboardPage = () => {
  const [view, setView] = useState<View>('daily')
  const { daily, weekly, monthly, isLoading } = useDashboard()
  const { scores, isLoading: benefitsLoading } = useBenefits()

  return (
    <div className="space-y-6">
      {/* Benefit scores */}
      <section>
        <h2 className="text-sm font-semibold text-foreground mb-3">Today's Health Benefits</h2>
        {benefitsLoading ? (
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-20" />)}
          </div>
        ) : (
          <BenefitScoreCards scores={scores} />
        )}
      </section>

      {/* Completion history */}
      <section>
        <h2 className="text-sm font-semibold text-foreground mb-3">Completion History</h2>

        {/* View toggle */}
        <div className="flex gap-1 p-1 bg-muted rounded-lg mb-4">
          {(['daily', 'weekly', 'monthly'] as View[]).map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`flex-1 text-xs py-1.5 rounded-md font-medium transition-colors min-h-[44px] ${
                view === v ? 'bg-white text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>

        {isLoading ? (
          <Skeleton className="h-48 w-full" />
        ) : (
          <div className="rounded-lg border bg-card">
            {view === 'daily'   && <DailyTable rows={daily} />}
            {view === 'weekly'  && <WeeklyTable rows={weekly} />}
            {view === 'monthly' && <MonthlyTable rows={monthly} />}
          </div>
        )}
      </section>
    </div>
  )
}

export default DashboardPage
