import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore, useUIStore } from '@/store'
import { authApi } from '@/services/api'
import DashboardLayout from '@/layouts/DashboardLayout'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import UploadPage from '@/pages/UploadPage'
import ChatPage from '@/pages/ChatPage'
import FilesPage from '@/pages/FilesPage'
import SummaryPage from '@/pages/SummaryPage'
import DashboardPage from '@/pages/DashboardPage'
import { Toaster } from '@/components/ui/toaster'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const { isAuthenticated, setUser, theme } = useAuthStore((s) => ({
    isAuthenticated: s.isAuthenticated,
    setUser: s.setUser,
    theme: undefined,
  }))
  const uiTheme = useUIStore((s) => s.theme)

  // Apply saved theme
  useEffect(() => {
    document.documentElement.className = uiTheme
  }, [uiTheme])

  // Bootstrap: fetch current user if token exists
  useEffect(() => {
    if (isAuthenticated) {
      authApi.me().then(setUser).catch(() => useAuthStore.getState().logout())
    }
  }, [isAuthenticated])

  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="chat/:chatId" element={<ChatPage />} />
          <Route path="files" element={<FilesPage />} />
          <Route path="summary/:fileId" element={<SummaryPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
    </>
  )
}
