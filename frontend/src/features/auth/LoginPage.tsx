import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { isAxiosError } from 'axios'

const LoginPage = () => {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)
    try {
      await login(email, password)
      navigate('/', { replace: true })
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 401) {
        setError('Invalid email or password.')
      } else {
        setError('Could not sign in. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold text-primary mb-1">Longevity Daily</h1>
        <p className="text-muted-foreground text-sm mb-8">Sign in to your account</p>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[44px]"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[44px]"
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-red-600 rounded-lg bg-red-50 px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary text-primary-foreground rounded-lg px-4 font-medium min-h-[44px] transition-opacity disabled:opacity-60"
          >
            {isLoading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p className="mt-6 text-sm text-center text-muted-foreground">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-primary font-medium hover:underline">
            Register →
          </Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
