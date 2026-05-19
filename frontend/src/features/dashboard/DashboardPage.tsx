import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FileSpreadsheet } from 'lucide-react'
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
      {/* Personalized plan CTA */}
      <div className="rounded-lg border bg-gradient-to-r from-primary/10 to-primary/5 p-4">
        <h3 className="font-semibold text-base mb-1">Your Personalized Plan</h3>
        <p className="text-sm text-muted-foreground mb-3">
          Answer 40 questions to get a plan tailored to your health, fitness, and lifestyle.
        </p>
        <Link
          to="/workbook"
          className="inline-flex items-center gap-2 bg-primary text-primary-foreground rounded-lg px-4 py-2 text-sm font-medium min-h-[44px]"
        >
          <FileSpreadsheet size={16} />
          Create My Workbook
        </Link>
      </div>

      {/* Benefit scores */}
      <section>
        <h2 className="text-sm md:text-base font-semibold text-foreground mb-3 md:mb-4">Today's Health Benefits</h2>
        {benefitsLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-20" />)}
          </div>
        ) : (
          <BenefitScoreCards scores={scores} />
        )}
      </section>

      {/* Completion history */}
      <section>
        <h2 className="text-sm md:text-base font-semibold text-foreground mb-3 md:mb-4">Completion History</h2>

        {/* View toggle */}
        <div className="flex gap-1 p-1 bg-muted rounded-lg mb-4">
          {(['daily', 'weekly', 'monthly'] as View[]).map(v => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`flex-1 text-xs md:text-sm py-1.5 md:py-2 rounded-md font-medium transition-colors min-h-[44px] ${
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
