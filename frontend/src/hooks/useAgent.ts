import { useState } from 'react'
import { agentApi } from '@/lib/api'

export const useAgent = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = async (message: string): Promise<string> => {
    setIsLoading(true)
    setError(null)
    try {
      return await agentApi.chat(message)
    } catch {
      const msg = 'Could not reach the AI coach. Please try again.'
      setError(msg)
      return msg
    } finally {
      setIsLoading(false)
    }
  }

  return { sendMessage, isLoading, error }
}
