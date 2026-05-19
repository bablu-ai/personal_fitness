import { useState } from 'react'

interface TimeInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

// HH:MM pattern (24-hour)
const TIME_PATTERN = /^([01]\d|2[0-3]):([0-5]\d)$/

const TimeInput = ({ value, onChange, placeholder }: TimeInputProps) => {
  const [touched, setTouched] = useState(false)
  const isInvalid = touched && value !== '' && !TIME_PATTERN.test(value)

  return (
    <div>
      <input
        type="time"
        value={value}
        onChange={e => onChange(e.target.value)}
        onBlur={() => setTouched(true)}
        placeholder={placeholder ?? '05:30'}
        pattern="[0-9]{2}:[0-9]{2}"
        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[44px]"
      />
      {isInvalid && (
        <p className="text-xs text-red-600 mt-1">Please enter a valid time (HH:MM, 24-hour).</p>
      )}
    </div>
  )
}

export default TimeInput
