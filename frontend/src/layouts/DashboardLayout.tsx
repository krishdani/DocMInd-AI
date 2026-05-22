import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/Sidebar'
import TopBar from '@/components/TopBar'
import { useUIStore } from '@/store'
import { cn } from '@/lib/utils'

export default function DashboardLayout() {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar />
      <div
        className={cn(
          'flex flex-col flex-1 min-w-0 transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-16',
        )}
      >
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
