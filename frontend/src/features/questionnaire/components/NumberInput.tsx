interface NumberInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  min?: number
  max?: number
}

const NumberInput = ({ value, onChange, placeholder, min, max }: NumberInputProps) => (
  <input
    type="number"
    inputMode="numeric"
    value={value}
    onChange={e => onChange(e.target.value)}
    placeholder={placeholder}
    min={min}
    max={max}
    className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[44px]"
  />
)

export default NumberInput
