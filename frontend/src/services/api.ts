import axios from 'axios'
import type {
  TokenResponse, User, FileListResponse, UploadedFile,
  ChatHistoryResponse, ChatSession, Summary,
  TimestampSearchResponse,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// ── Token management ─────────────────────────────────────────────────────────
export const tokenStore = {
  get: () => localStorage.getItem('access_token'),
  set: (t: string) => localStorage.setItem('access_token', t),
  getRefresh: () => localStorage.getItem('refresh_token'),
  setRefresh: (t: string) => localStorage.setItem('refresh_token', t),
  clear: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },
}

// Request interceptor: attach Bearer token
api.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor: auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = tokenStore.getRefresh()
      if (refresh) {
        try {
          const { data } = await axios.post<TokenResponse>('/api/auth/refresh', {
            refresh_token: refresh,
          })
          tokenStore.set(data.access_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          tokenStore.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(err)
  },
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post<TokenResponse>('/auth/register', data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>('/auth/login', data).then((r) => r.data),

  me: () => api.get<User>('/auth/me').then((r) => r.data),
}

// ── Files ─────────────────────────────────────────────────────────────────────
export const filesApi = {
  list: (page = 1, pageSize = 20) =>
    api.get<FileListResponse>('/files', { params: { page, page_size: pageSize } }).then((r) => r.data),

  upload: (file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<UploadedFile>('/files/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    }).then((r) => r.data)
  },

  get: (id: number) => api.get<UploadedFile>(`/files/${id}`).then((r) => r.data),

  delete: (id: number) => api.delete(`/files/${id}`),

  mediaUrl: (id: number) => `/api/media/stream/${id}`,
}

// ── Chat ──────────────────────────────────────────────────────────────────────
export const chatApi = {
  history: (page = 1) =>
    api.get<ChatHistoryResponse>('/chat/history', { params: { page } }).then((r) => r.data),

  session: (id: number) =>
    api.get<ChatSession>(`/chat/history/${id}`).then((r) => r.data),

  /** Returns an EventSource-like ReadableStream for SSE streaming */
  streamQuery: (body: {
    question: string
    file_ids: number[]
    chat_id?: number
  }): Promise<Response> => {
    const token = tokenStore.get()
    return fetch('/api/chat/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ ...body, stream: true }),
    })
  },
}

// ── Summary ───────────────────────────────────────────────────────────────────
export const summaryApi = {
  get: (fileId: number) =>
    api.get<Summary>(`/summary/${fileId}`).then((r) => r.data),
}

// ── Timestamps ────────────────────────────────────────────────────────────────
export const timestampApi = {
  search: (body: { query: string; file_id: number; top_k?: number }) =>
    api.post<TimestampSearchResponse>('/timestamps/search', body).then((r) => r.data),
}

export default api
