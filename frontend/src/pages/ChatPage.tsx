import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, FileText, Plus, ExternalLink, Clock } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useChatStore } from '@/store'
import { chatApi, filesApi } from '@/services/api'
import { formatRelativeTime, formatTimestamp, cn } from '@/lib/utils'
import type { Source } from '@/types'

// Typing indicator
function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
        <Sparkles className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="flex gap-1 items-center h-6">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  )
}

// Source citation chip
function SourceChip({ source, onSeek }: { source: Source; onSeek?: (t: number) => void }) {
  return (
    <button
      onClick={() => source.start_time != null && onSeek?.(source.start_time)}
      className="inline-flex items-center gap-1.5 px-2 py-1 bg-primary/10 border border-primary/20 rounded-full text-xs text-primary hover:bg-primary/20 transition-colors"
    >
      {source.start_time != null ? (
        <><Clock className="w-3 h-3" />{formatTimestamp(source.start_time)}</>
      ) : (
        <><FileText className="w-3 h-3" />{source.file_name}</>
      )}
    </button>
  )
}

export default function ChatPage() {
  const { chatId } = useParams()
  const navigate = useNavigate()
  const { messages, isStreaming, selectedFileIds, addMessage, appendToken, setStreaming, setActiveChatId, clearMessages } = useChatStore()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { data: filesData } = useQuery({
    queryKey: ['files'],
    queryFn: () => filesApi.list(1, 50),
  })

  const { data: sessionData } = useQuery({
    queryKey: ['chat-session', chatId],
    queryFn: () => chatApi.session(Number(chatId)),
    enabled: !!chatId,
  })

  // Load existing session messages
  useEffect(() => {
    if (sessionData && chatId) {
      clearMessages()
      sessionData.messages.forEach((m) => addMessage(m as any))
      setActiveChatId(Number(chatId))
    }
  }, [sessionData])

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  const sendMessage = async () => {
    const question = input.trim()
    if (!question || isStreaming) return
    setInput('')

    // Optimistic user message
    addMessage({
      id: Date.now(),
      chat_id: 0,
      role: 'user',
      content: question,
      created_at: new Date().toISOString(),
    })

    // Placeholder assistant message for streaming
    addMessage({
      id: Date.now() + 1,
      chat_id: 0,
      role: 'assistant',
      content: '',
      sources: [],
      created_at: new Date().toISOString(),
    })

    setStreaming(true)
    try {
      const res = await chatApi.streamQuery({
        question,
        file_ids: selectedFileIds,
        chat_id: chatId ? Number(chatId) : undefined,
      })

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value)
        const lines = text.split('\n').filter((l) => l.startsWith('data: '))
        for (const line of lines) {
          try {
            const json = JSON.parse(line.slice(6))
            if (json.type === 'token') appendToken(json.content)
            if (json.type === 'done' && json.chat_id && !chatId) {
              navigate(`/chat/${json.chat_id}`, { replace: true })
            }
          } catch {}
        }
      }
    } finally {
      setStreaming(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const completedFiles = filesData?.files.filter((f) => f.status === 'completed') ?? []

  return (
    <div className="flex h-full gap-4 -m-6">
      {/* File selector sidebar */}
      <div className="w-64 flex-shrink-0 border-r border-border/50 p-4 space-y-3 overflow-y-auto">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Context Files</h3>
          <span className="text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded-full">
            {selectedFileIds.length} selected
          </span>
        </div>
        {completedFiles.length === 0 ? (
          <p className="text-xs text-muted-foreground">No processed files yet. Upload some first!</p>
        ) : (
          completedFiles.map((f) => {
            const selected = selectedFileIds.includes(f.id)
            return (
              <button
                key={f.id}
                onClick={() => useChatStore.getState().toggleFileId(f.id)}
                className={cn(
                  'w-full text-left px-3 py-2.5 rounded-lg border transition-all text-sm',
                  selected
                    ? 'bg-primary/15 border-primary/40 text-primary'
                    : 'border-border hover:border-border/80 hover:bg-secondary/50',
                )}
              >
                <p className="font-medium truncate">{f.original_name}</p>
                <p className="text-xs text-muted-foreground capitalize mt-0.5">{f.file_type}</p>
              </button>
            )
          })
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto py-6 px-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center glow">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold gradient-text">Ask DocuMind AI</h2>
                <p className="text-muted-foreground mt-2 text-sm max-w-sm">
                  Select files from the sidebar, then ask anything about your documents, audio, or video.
                </p>
              </div>
            </div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}
              >
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center flex-shrink-0 mt-1">
                    <Sparkles className="w-3.5 h-3.5 text-white" />
                  </div>
                )}
                <div className={cn('max-w-[75%] space-y-2', msg.role === 'user' ? 'items-end' : 'items-start')}>
                  <div className={cn('px-4 py-3 text-sm leading-relaxed', msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai')}>
                    {msg.content || (isStreaming && i === messages.length - 1 && msg.role === 'assistant' ? <TypingIndicator /> : '')}
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 px-1">
                      {msg.sources.map((s, si) => (
                        <SourceChip key={si} source={s} />
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isStreaming && messages[messages.length - 1]?.content === '' && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-border/50">
          <div className="flex gap-3 items-end glass rounded-2xl p-3">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your files… (Shift+Enter for new line)"
              rows={1}
              disabled={isStreaming}
              className="flex-1 bg-transparent resize-none outline-none text-sm leading-relaxed max-h-32 disabled:opacity-50"
              style={{ minHeight: '24px' }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isStreaming}
              className="w-9 h-9 rounded-xl bg-primary hover:bg-primary/90 text-white flex items-center justify-center flex-shrink-0 transition-all disabled:opacity-40 disabled:cursor-not-allowed glow"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">
            DocuMind AI can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  )
}
