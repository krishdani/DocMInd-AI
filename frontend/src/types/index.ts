// All TypeScript types shared across the frontend

export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  role: 'user' | 'admin'
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export type FileType = 'pdf' | 'audio' | 'video'
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface UploadedFile {
  id: number
  uuid: string
  original_name: string
  file_type: FileType
  mime_type?: string
  size_bytes: number
  duration_seconds?: number
  status: ProcessingStatus
  error_message?: string
  created_at: string
  updated_at: string
}

export interface FileListResponse {
  files: UploadedFile[]
  total: number
  page: number
  page_size: number
}

export interface Source {
  file_id: number
  file_name: string
  chunk_index: number
  score: number
  snippet: string
  start_time?: number
  end_time?: number
}

export interface ChatMessage {
  id: number
  chat_id: number
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  tokens_used?: number
  created_at: string
}

export interface ChatSession {
  id: number
  title?: string
  file_ids: number[]
  created_at: string
  updated_at: string
  messages: ChatMessage[]
}

export interface ChatHistoryResponse {
  sessions: ChatSession[]
  total: number
}

export interface KeyTopic {
  topic: string
  confidence: number
  start_time?: number
  end_time?: number
  snippet?: string
}

export interface Summary {
  id: number
  file_id: number
  short_summary?: string
  detailed_summary?: string
  bullet_points?: string[]
  key_topics?: KeyTopic[]
  word_count?: number
  created_at: string
}

export interface TimestampResult {
  start_time: number
  end_time: number
  snippet: string
  confidence: number
  chunk_index: number
}

export interface TimestampSearchResponse {
  query: string
  file_id: number
  results: TimestampResult[]
}

// UI state types
export interface UploadProgress {
  file: File
  progress: number
  status: 'uploading' | 'done' | 'error'
  error?: string
}

export interface StreamToken {
  type: 'token' | 'done'
  content?: string
  chat_id?: number
  sources?: Source[]
}
