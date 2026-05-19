import { useRef, useEffect } from 'react'

interface TextInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  multiline?: boolean
}

const TextInput = ({ value, onChange, placeholder, multiline = true }: TextInputProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea as content grows
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [value])

  if (!multiline) {
    return (
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[44px]"
      />
    )
  }

  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      rows={3}
      className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none min-h-[100px]"
    />
  )
}

export default TextInput
