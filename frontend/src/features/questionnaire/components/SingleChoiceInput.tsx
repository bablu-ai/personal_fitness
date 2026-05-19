import { cn } from '@/lib/utils'

interface SingleChoiceInputProps {
  options: string[]
  value: string
  onChange: (value: string) => void
  /** When set, selecting this option reveals an inline detail textarea */
  triggerOption?: string
  detailValue?: string
  detailPlaceholder?: string
  onDetailChange?: (detail: string) => void
}

const SingleChoiceInput = ({
  options,
  value,
  onChange,
  triggerOption,
  detailValue = '',
  detailPlaceholder = 'Please describe…',
  onDetailChange,
}: SingleChoiceInputProps) => (
  <div className="space-y-2" role="radiogroup">
    {options.map(option => {
      const isSelected = value === option
      return (
        <div key={option}>
          <button
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => onChange(isSelected ? '' : option)}
            className={cn(
              'w-full text-left px-4 py-3 rounded-lg border text-sm font-medium transition-colors min-h-[56px]',
              isSelected
                ? 'border-primary bg-primary/5 text-primary'
                : 'border-border bg-background text-foreground hover:border-primary/50 hover:bg-muted/40',
            )}
          >
            {option}
          </button>

          {/* Inline detail textarea when this is the trigger option and it is selected */}
          {triggerOption === option && isSelected && onDetailChange && (
            <textarea
              className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm min-h-[80px] resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder={detailPlaceholder}
              value={detailValue}
              onChange={e => onDetailChange(e.target.value)}
              aria-label={detailPlaceholder}
            />
          )}
        </div>
      )
    })}
  </div>
)

export default SingleChoiceInput
