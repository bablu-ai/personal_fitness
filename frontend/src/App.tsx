import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { CheckSquare, BarChart2, Upload, MessageCircle, FileSpreadsheet } from 'lucide-react'
import { cn } from '@/lib/utils'
import { AuthProvider } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import TodayPage from '@/features/todos/TodayPage'
import DashboardPage from '@/features/dashboard/DashboardPage'
import UploadPage from '@/features/upload/UploadPage'
import AgentChat from '@/features/agent/AgentChat'
import LoginPage from '@/features/auth/LoginPage'
import RegisterPage from '@/features/auth/RegisterPage'
import SessionListPage from '@/features/questionnaire/SessionListPage'
import QuestionnairePage from '@/features/questionnaire/QuestionnairePage'
import AdminQuestionnairesPage from '@/features/admin/AdminQuestionnairesPage'

const NAV_ITEMS = [
  { to: '/',          label: 'Today',    Icon: CheckSquare },
  { to: '/dashboard', label: 'Dashboard', Icon: BarChart2 },
  { to: '/upload',    label: 'Upload',   Icon: Upload },
  { to: '/coach',     label: 'Coach',    Icon: MessageCircle },
  { to: '/workbook',  label: 'Workbook', Icon: FileSpreadsheet },
]

// Routes where the bottom nav is hidden (auth pages + active questionnaire flow)
const NO_NAV_PREFIXES = ['/login', '/register', '/workbook/new', '/workbook/', '/admin/']

const AppShell = () => {
  const location = useLocation()
  const isAdminRoute = location.pathname.startsWith('/admin/')
  const hideNav = NO_NAV_PREFIXES.some(prefix => {
    // Exact match for /workbook (session list shows nav); hide for /workbook/:id
    if (prefix === '/workbook/') {
      return location.pathname.startsWith('/workbook/') && location.pathname !== '/workbook/'
    }
    return location.pathname === prefix || location.pathname.startsWith(prefix)
  })

  return (
    <div className={cn(
      'min-h-screen bg-background flex flex-col mx-auto',
      isAdminRoute ? 'max-w-7xl' : 'max-w-2xl lg:max-w-3xl xl:max-w-4xl',
    )}>
      {!hideNav && (
        <header className="sticky top-0 z-10 bg-white border-b px-4 py-3">
          <h1 className="text-lg font-semibold text-primary">Longevity Daily</h1>
        </header>
      )}

      <main className={cn(
        'flex-1 overflow-y-auto px-4 md:px-6 lg:px-8',
        hideNav ? '' : 'pb-24 md:pb-20 pt-4',
      )}>
        <Routes>
          {/* Public routes */}
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/"          element={<TodayPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/upload"    element={<UploadPage />} />
            <Route path="/coach"     element={<AgentChat />} />
            <Route path="/workbook"         element={<SessionListPage />} />
            <Route path="/workbook/:sessionId" element={<QuestionnairePage />} />
            <Route path="/admin/questionnaires" element={<AdminQuestionnairesPage />} />
          </Route>
        </Routes>
      </main>

      {!hideNav && (
        <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-2xl lg:max-w-3xl xl:max-w-4xl bg-white border-t flex safe-bottom">
          {NAV_ITEMS.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                cn(
                  'flex-1 flex flex-col items-center gap-1 py-2 text-xs font-medium transition-colors',
                  'min-h-[44px] justify-center',
                  isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground',
                )
              }
            >
              <Icon size={20} />
              {label}
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  )
}

const App = () => (
  <AuthProvider>
    <AppShell />
  </AuthProvider>
)

export default App
