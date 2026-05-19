import { ArrowLeft, ArrowRight, User, Heart, Activity, Apple, Clock, Monitor, Info } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { SECTIONS } from './questionConfig'

const ICON_MAP: Record<string, LucideIcon> = {
  User,
  Heart,
  Activity,
  Apple,
  Clock,
  Monitor,
  Info,
}

interface SectionOverviewScreenProps {
  sectionNumber: number
  onContinue: () => void
  onBack: () => void
}

const SectionOverviewScreen = ({ sectionNumber, onContinue, onBack }: SectionOverviewScreenProps) => {
  const section = SECTIONS.find(s => s.number === sectionNumber)
  if (!section) return null

  const SectionIcon = ICON_MAP[section.iconName] ?? Info
  const completedSections = sectionNumber - 1

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top bar */}
      <div className="flex items-center px-4 pt-4 pb-2">
        <button
          type="button"
          onClick={onBack}
          aria-label="Go back"
          className="p-2 -ml-2 rounded-lg hover:bg-muted transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
        >
          <ArrowLeft size={20} />
        </button>
      </div>

      {/* Content — centered vertically */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
        {/* Section progress label */}
        <p className="text-sm text-muted-foreground mb-4">
          Section {sectionNumber} of {SECTIONS.length}
        </p>

        {/* Progress dots */}
        <div className="flex gap-2 mb-8" aria-label={`${completedSections} of ${SECTIONS.length} sections completed`}>
          {SECTIONS.map(s => (
            <span
              key={s.number}
              className={`h-2.5 w-2.5 rounded-full transition-colors ${
                s.number < sectionNumber
                  ? 'bg-primary'
                  : s.number === sectionNumber
                    ? 'bg-primary/60 ring-2 ring-primary/30'
                    : 'bg-muted'
              }`}
            />
          ))}
        </div>

        {/* Section icon */}
        <div className="rounded-full bg-primary/10 p-6 mb-6">
          <SectionIcon size={40} className="text-primary" />
        </div>

        {/* Section title */}
        <h1 className="text-2xl font-bold mb-2">{section.title}</h1>
        <p className="text-muted-foreground text-sm">
          {section.questionCount} questions · ~{section.estimatedMinutes} min
        </p>

        {/* Continue button */}
        <button
          type="button"
          onClick={onContinue}
          className="mt-10 flex items-center gap-2 bg-primary text-primary-foreground rounded-lg px-8 py-3 font-medium min-h-[44px] hover:bg-primary/90 transition-colors"
        >
          Continue
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  )
}

export default SectionOverviewScreen
