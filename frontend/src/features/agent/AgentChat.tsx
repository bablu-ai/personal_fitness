import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { agentApi } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

// ── Inline markdown renderer ─────────────────────────────────────────────────
// JSX auto-escapes all content — no dangerouslySetInnerHTML needed (OWASP LLM05 safe)

type TextBlock = { type: 'h2' | 'h3' | 'p' | 'blockquote'; text: string }
type ListBlock = { type: 'ul' | 'ol'; items: string[] }
type DividerBlock = { type: 'divider' }
type BlockNode = TextBlock | ListBlock | DividerBlock

function renderInline(text: string, keyPrefix: string) {
  // Handles **bold**, *em*, `code` — splits on marker boundaries
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g)
  return parts.map((part, i) => {
    const k = `${keyPrefix}-${i}`
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={k}>{part.slice(2, -2)}</strong>
    if (part.startsWith('*') && part.endsWith('*'))
      return <em key={k}>{part.slice(1, -1)}</em>
    if (part.startsWith('`') && part.endsWith('`'))
      return <code key={k} className="font-mono text-xs bg-background/60 rounded px-1">{part.slice(1, -1)}</code>
    return part
  })
}

function parseMarkdown(raw: string): BlockNode[] {
  const blocks: BlockNode[] = []
  const lines = raw.split('\n')
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    if (line.trim() === '') { i++; continue }

    if (line.startsWith('## ')) {
      blocks.push({ type: 'h2', text: line.slice(3).trim() })
      i++; continue
    }
    if (line.startsWith('### ')) {
      blocks.push({ type: 'h3', text: line.slice(4).trim() })
      i++; continue
    }
    if (line.startsWith('> ')) {
      blocks.push({ type: 'blockquote', text: line.slice(2).trim() })
      i++; continue
    }
    if (line.startsWith('---')) {
      blocks.push({ type: 'divider' })
      i++; continue
    }

    // Bullet list: lines starting with "- " or "* "
    if (/^[-*] /.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        items.push(lines[i].replace(/^[-*] /, '').trim())
        i++
      }
      blocks.push({ type: 'ul', items })
      continue
    }

    // Numbered list: lines starting with "1. " etc.
    if (/^\d+\. /.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\. /, '').trim())
        i++
      }
      blocks.push({ type: 'ol', items })
      continue
    }

    blocks.push({ type: 'p', text: line.trim() })
    i++
  }

  return blocks
}

const MarkdownMessage = ({ text }: { text: string }) => {
  const blocks = parseMarkdown(text)
  return (
    <div className="space-y-1.5">
      {blocks.map((block, bi) => {
        const k = `b${bi}`
        if (block.type === 'h2')
          return <p key={k} className="font-semibold text-sm mt-1">{renderInline(block.text, k)}</p>
        if (block.type === 'h3')
          return <p key={k} className="font-medium text-sm mt-0.5">{renderInline(block.text, k)}</p>
        if (block.type === 'blockquote')
          return (
            <p key={k} className="border-l-2 border-primary/40 pl-2 text-muted-foreground italic text-sm">
              {renderInline(block.text, k)}
            </p>
          )
        if (block.type === 'divider')
          return <hr key={k} className="border-muted-foreground/20 my-1" />
        if (block.type === 'ul')
          return (
            <ul key={k} className="space-y-0.5">
              {block.items.map((item, ii) => (
                <li key={ii} className="flex gap-1.5 items-start">
                  <span className="text-primary mt-0.5 flex-shrink-0 text-xs">·</span>
                  <span>{renderInline(item, `${k}-i${ii}`)}</span>
                </li>
              ))}
            </ul>
          )
        if (block.type === 'ol')
          return (
            <ol key={k} className="space-y-0.5">
              {block.items.map((item, ii) => (
                <li key={ii} className="flex gap-1.5 items-start">
                  <span className="flex-shrink-0 w-4 h-4 rounded-full bg-primary/15 text-primary text-[10px] font-semibold flex items-center justify-center mt-0.5">{ii + 1}</span>
                  <span>{renderInline(item, `${k}-i${ii}`)}</span>
                </li>
              ))}
            </ol>
          )
        // type === 'p'
        return <p key={k}>{renderInline((block as TextBlock).text, k)}</p>
      })}
    </div>
  )
}

// ── Chat component ────────────────────────────────────────────────────────────

const STARTER_PROMPTS = [
  "Why is my dementia score low today?",
  "Explain the benefits of zone 2 cardio",
  "What should I prioritize this week?",
]

const AgentChat = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text: string) => {
    if (!text.trim() || isLoading) return
    const userMsg: Message = { role: 'user', content: text.trim() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)
    try {
      const reply = await agentApi.chat(text.trim())
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-9rem)] md:h-[calc(100vh-8rem)] lg:h-[calc(100vh-7rem)]">
      <div className="flex-1 overflow-y-auto space-y-3 pb-2">
        {messages.length === 0 && (
          <div className="pt-4">
            <div className="flex items-center gap-2 mb-4">
              <Bot size={20} className="text-primary" />
              <p className="text-sm font-medium">Longevity Coach</p>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Ask me about your tasks, benefit scores, or longevity strategies.
            </p>
            <div className="flex flex-col gap-2">
              {STARTER_PROMPTS.map(prompt => (
                <button
                  key={prompt}
                  onClick={() => send(prompt)}
                  className="text-left text-sm md:text-base text-primary border border-primary/20 rounded-lg px-3 py-2 md:px-4 md:py-3 hover:bg-primary/5 transition-colors min-h-[44px]"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={cn('flex gap-2', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
            {msg.role === 'assistant' && <Bot size={16} className="text-primary mt-1 flex-shrink-0" />}
            <div className={cn(
              'max-w-[85%] sm:max-w-[75%] md:max-w-[65%] lg:max-w-[55%] rounded-2xl px-4 py-2.5 text-sm md:text-base',
              msg.role === 'user'
                ? 'bg-primary text-primary-foreground rounded-br-sm'
                : 'bg-muted text-foreground rounded-bl-sm',
            )}>
              {msg.role === 'assistant'
                ? <MarkdownMessage text={msg.content} />
                : msg.content
              }
            </div>
            {msg.role === 'user' && <User size={16} className="text-muted-foreground mt-1 flex-shrink-0" />}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-2">
            <Bot size={16} className="text-primary mt-1" />
            <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-2.5">
              <span className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <span key={i} className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={e => { e.preventDefault(); send(input) }}
        className="flex gap-2 pt-2 border-t"
      >
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask your longevity coach…"
          disabled={isLoading}
          className="flex-1 text-sm md:text-base border rounded-full px-4 py-2.5 min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="w-11 h-11 rounded-full bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-40 hover:bg-primary/90 transition-colors flex-shrink-0"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  )
}

export default AgentChat
