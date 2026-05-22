import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, ChatMessage, UploadedFile } from '@/types'
import { tokenStore } from '@/services/api'

// ── Auth Store ────────────────────────────────────────────────────────────────
interface AuthState {
  user: User | null
  isAuthenticated: boolean
  setUser: (user: User | null) => void
  setTokens: (access: string, refresh: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setTokens: (access, refresh) => {
        tokenStore.set(access)
        tokenStore.setRefresh(refresh)
        set({ isAuthenticated: true })
      },
      logout: () => {
        tokenStore.clear()
        set({ user: null, isAuthenticated: false })
      },
    }),
    { name: 'auth-store', partialize: (s) => ({ isAuthenticated: s.isAuthenticated }) },
  ),
)

// ── Chat Store ────────────────────────────────────────────────────────────────
interface ChatState {
  activeChatId: number | null
  messages: ChatMessage[]
  isStreaming: boolean
  selectedFileIds: number[]
  setActiveChatId: (id: number | null) => void
  addMessage: (msg: ChatMessage) => void
  appendToken: (token: string) => void
  setStreaming: (v: boolean) => void
  clearMessages: () => void
  toggleFileId: (id: number) => void
  setSelectedFileIds: (ids: number[]) => void
}

export const useChatStore = create<ChatState>((set) => ({
  activeChatId: null,
  messages: [],
  isStreaming: false,
  selectedFileIds: [],
  setActiveChatId: (id) => set({ activeChatId: id }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  appendToken: (token) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content: last.content + token }
      }
      return { messages: msgs }
    }),
  setStreaming: (v) => set({ isStreaming: v }),
  clearMessages: () => set({ messages: [], activeChatId: null }),
  toggleFileId: (id) =>
    set((s) => ({
      selectedFileIds: s.selectedFileIds.includes(id)
        ? s.selectedFileIds.filter((x) => x !== id)
        : [...s.selectedFileIds, id],
    })),
  setSelectedFileIds: (ids) => set({ selectedFileIds: ids }),
}))

// ── UI Store ──────────────────────────────────────────────────────────────────
interface UIState {
  sidebarOpen: boolean
  theme: 'dark' | 'light'
  toggleSidebar: () => void
  setSidebarOpen: (v: boolean) => void
  toggleTheme: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'dark',
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setSidebarOpen: (v) => set({ sidebarOpen: v }),
      toggleTheme: () => {
        set((s) => {
          const next = s.theme === 'dark' ? 'light' : 'dark'
          document.documentElement.className = next
          return { theme: next }
        })
      },
    }),
    { name: 'ui-store' },
  ),
)
