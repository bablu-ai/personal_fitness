import { cn } from '@/lib/utils'

interface ConditionalValue {
  choice: string
  detail: string
}

interface ConditionalInputProps {
  options: string[]
  triggerOption: string
  detailPlaceholder: string
  value: ConditionalValue
  onChange: (value: ConditionalValue) => void
}

/**
 * Renders a Yes/No (or similar 2-option) choice.
 * When `triggerOption` is selected, a text area expands below.
 * Saves both choice + detail as a combined object.
 */
const ConditionalInput = ({
  options,
  triggerOption,
  detailPlaceholder,
  value,
  onChange,
}: ConditionalInputProps) => {
  const showDetail = value.choice === triggerOption

  const handleChoiceClick = (option: string) => {
    const nextChoice = value.choice === option ? '' : option
    // Clear detail when deselecting or changing away from trigger
    const nextDetail = nextChoice === triggerOption ? value.detail : ''
    onChange({ choice: nextChoice, detail: nextDetail })
  }

  return (
    <div className="space-y-2">
      <div className="space-y-2" role="radiogroup">
        {options.map(option => {
          const isSelected = value.choice === option
          return (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={isSelected}
              onClick={() => handleChoiceClick(option)}
              className={cn(
                'w-full text-left px-4 py-3 rounded-lg border text-sm font-medium transition-colors min-h-[56px]',
                isSelected
                  ? 'border-primary bg-primary/5 text-primary'
                  : 'border-border bg-background text-foreground hover:border-primary/50 hover:bg-muted/40',
              )}
            >
              {option}
            </button>
          )
        })}
      </div>

      {/* Expanding detail field — CSS transition for smooth reveal */}
      <div
        className={cn(
          'overflow-hidden transition-all duration-300',
          showDetail ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0',
        )}
        aria-hidden={!showDetail}
      >
        <textarea
          value={value.detail}
          onChange={e => onChange({ choice: value.choice, detail: e.target.value })}
          placeholder={detailPlaceholder}
          rows={3}
          tabIndex={showDetail ? 0 : -1}
          className="w-full mt-2 rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none min-h-[80px]"
        />
      </div>
    </div>
  )
}

export default ConditionalInput
export type { ConditionalValue }
