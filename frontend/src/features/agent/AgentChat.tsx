import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { agentApi } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

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
    <div className="flex flex-col h-[calc(100vh-9rem)]">
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
                  className="text-left text-sm text-primary border border-primary/20 rounded-lg px-3 py-2 hover:bg-primary/5 transition-colors min-h-[44px]"
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
              'max-w-[85%] rounded-2xl px-4 py-2.5 text-sm',
              msg.role === 'user'
                ? 'bg-primary text-primary-foreground rounded-br-sm'
                : 'bg-muted text-foreground rounded-bl-sm',
            )}>
              {msg.content}
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
          className="flex-1 text-sm border rounded-full px-4 py-2.5 min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
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
