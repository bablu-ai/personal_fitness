import * as Checkbox from '@radix-ui/react-checkbox'
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MultiChoiceInputProps {
  options: string[]
  value: string[]
  onChange: (value: string[]) => void
  /** When set, selecting this option reveals an inline detail textarea */
  triggerOption?: string
  detailValue?: string
  detailPlaceholder?: string
  onDetailChange?: (detail: string) => void
}

const MultiChoiceInput = ({
  options,
  value,
  onChange,
  triggerOption,
  detailValue = '',
  detailPlaceholder = 'Please describe…',
  onDetailChange,
}: MultiChoiceInputProps) => {
  const toggle = (option: string) => {
    if (value.includes(option)) {
      onChange(value.filter(v => v !== option))
    } else {
      onChange([...value, option])
    }
  }

  return (
    <div className="space-y-2">
      {options.map(option => {
        const isChecked = value.includes(option)
        return (
          <div key={option}>
            <label
              className={cn(
                'flex items-center gap-3 w-full px-4 py-3 rounded-lg border text-sm font-medium transition-colors min-h-[56px] cursor-pointer',
                isChecked
                  ? 'border-primary bg-primary/5 text-primary'
                  : 'border-border bg-background text-foreground hover:border-primary/50 hover:bg-muted/40',
              )}
            >
              <Checkbox.Root
                checked={isChecked}
                onCheckedChange={() => toggle(option)}
                className="h-5 w-5 rounded border border-border data-[state=checked]:bg-primary data-[state=checked]:border-primary flex items-center justify-center flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <Checkbox.Indicator>
                  <Check size={12} className="text-primary-foreground" />
                </Checkbox.Indicator>
              </Checkbox.Root>
              <span>{option}</span>
            </label>

            {/* Inline detail textarea when this is the trigger option and it is checked */}
            {triggerOption === option && isChecked && onDetailChange && (
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
}

export default MultiChoiceInput
