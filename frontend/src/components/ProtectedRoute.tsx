import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

/**
 * Renders <Outlet /> when the user is authenticated.
 * Redirects to /login if not. The `replace` flag prevents a back-button
 * loop between /login and the protected page.
 */
const ProtectedRoute = () => {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export default ProtectedRoute
