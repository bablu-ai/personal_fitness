import { Brain, Heart, Shield, Activity, Star, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { BenefitScore } from '@/types'

const ICON_MAP: Record<string, React.ElementType> = {
  brain: Brain,
  heart: Heart,
  shield: Shield,
  activity: Activity,
  star: Star,
}

interface Props {
  scores: BenefitScore[]
}

const BenefitScoreCards = ({ scores }: Props) => {
  if (scores.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-4">
        Complete tasks today to see benefit scores.
      </p>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      {scores.map(score => {
        const Icon = ICON_MAP[score.icon ?? ''] ?? Zap
        const pct = score.score_pct

        return (
          <div key={score.outcome} className="rounded-xl border bg-card p-3">
            <div className="flex items-center gap-2 mb-2">
              <Icon size={16} className="text-primary flex-shrink-0" />
              <span className="text-xs font-medium text-foreground leading-tight">{score.label}</span>
            </div>
            <div className="flex items-end justify-between">
              <span className={cn('text-2xl font-bold', pct >= 80 ? 'text-green-600' : pct >= 50 ? 'text-yellow-600' : 'text-red-500')}>
                {pct}%
              </span>
            </div>
            <div className="h-1.5 bg-muted rounded-full mt-2">
              <div
                className={cn('h-1.5 rounded-full transition-all duration-500',
                  pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-400'
                )}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default BenefitScoreCards
