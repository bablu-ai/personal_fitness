import { Routes, Route, NavLink } from 'react-router-dom'
import { CheckSquare, BarChart2, Upload, MessageCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import TodayPage from '@/features/todos/TodayPage'
import DashboardPage from '@/features/dashboard/DashboardPage'
import UploadPage from '@/features/upload/UploadPage'
import AgentChat from '@/features/agent/AgentChat'

const NAV_ITEMS = [
  { to: '/',          label: 'Today',     Icon: CheckSquare },
  { to: '/dashboard', label: 'Dashboard', Icon: BarChart2 },
  { to: '/upload',    label: 'Upload',    Icon: Upload },
  { to: '/coach',     label: 'Coach',     Icon: MessageCircle },
]

const App = () => (
  <div className="min-h-screen bg-background flex flex-col max-w-2xl mx-auto">
    <header className="sticky top-0 z-10 bg-white border-b px-4 py-3">
      <h1 className="text-lg font-semibold text-primary">Longevity Daily</h1>
    </header>

    <main className="flex-1 overflow-y-auto pb-20 px-4 pt-4">
      <Routes>
        <Route path="/"          element={<TodayPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/upload"    element={<UploadPage />} />
        <Route path="/coach"     element={<AgentChat />} />
      </Routes>
    </main>

    <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-2xl bg-white border-t flex">
      {NAV_ITEMS.map(({ to, label, Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            cn(
              'flex-1 flex flex-col items-center gap-1 py-2 text-xs font-medium transition-colors',
              'min-h-[44px] justify-center',  // 44px touch target per CONSTITUTION.md
              isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground',
            )
          }
        >
          <Icon size={20} />
          {label}
        </NavLink>
      ))}
    </nav>
  </div>
)

export default App
