import { useLocation } from 'react-router-dom'
import { Menu, Sun, Moon, Bell } from 'lucide-react'
import { useUIStore, useAuthStore } from '@/store'

const ROUTE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/upload': 'Upload Files',
  '/chat': 'AI Chat',
  '/files': 'My Files',
}

export default function TopBar() {
  const { toggleSidebar, toggleTheme, theme } = useUIStore()
  const user = useAuthStore((s) => s.user)
  const { pathname } = useLocation()

  const title = ROUTE_TITLES[pathname] ?? pathname.split('/')[1] ?? 'DocuMind AI'

  return (
    <header className="h-16 glass border-b border-border/50 flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="text-lg font-semibold capitalize">{title}</h1>
      </div>

      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Notifications (placeholder) */}
        <button className="p-2 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-primary rounded-full" />
        </button>

        {/* User badge */}
        <div className="flex items-center gap-2 ml-2 pl-2 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <span className="text-xs font-bold text-white">
              {user?.username?.[0]?.toUpperCase() ?? 'U'}
            </span>
          </div>
          <span className="text-sm font-medium hidden sm:block">{user?.username}</span>
        </div>
      </div>
    </header>
  )
}
