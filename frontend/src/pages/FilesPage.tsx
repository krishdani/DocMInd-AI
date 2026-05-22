import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Trash2, MessageSquare, BookOpen, RefreshCw, CheckCircle2,
  Clock, AlertCircle, FileText, Music, Video, Loader2
} from 'lucide-react'
import { filesApi } from '@/services/api'
import { formatBytes, formatRelativeTime, cn } from '@/lib/utils'
import type { UploadedFile } from '@/types'

function StatusBadge({ status }: { status: string }) {
  const config = {
    completed: { icon: CheckCircle2, color: 'text-green-400 bg-green-400/10 border-green-400/20' },
    processing: { icon: Loader2, color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20' },
    pending: { icon: Clock, color: 'text-blue-400 bg-blue-400/10 border-blue-400/20' },
    failed: { icon: AlertCircle, color: 'text-red-400 bg-red-400/10 border-red-400/20' },
  }
  const c = config[status as keyof typeof config] ?? config.pending
  const Icon = c.icon
  return (
    <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border', c.color)}>
      <Icon className={cn('w-3 h-3', status === 'processing' && 'animate-spin')} />
      {status}
    </span>
  )
}

function FileTypeIcon({ type }: { type: string }) {
  if (type === 'pdf') return <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center"><FileText className="w-5 h-5 text-red-400" /></div>
  if (type === 'audio') return <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center"><Music className="w-5 h-5 text-green-400" /></div>
  return <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center"><Video className="w-5 h-5 text-blue-400" /></div>
}

export default function FilesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['files'],
    queryFn: () => filesApi.list(1, 50),
    refetchInterval: (query) =>
      query.state.data?.files.some((f: any) => f.status === 'processing' || f.status === 'pending') ? 3000 : false,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => filesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] })
      setDeleteId(null)
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-3 animate-fade-in">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="glass rounded-xl p-4 h-20 skeleton" />
        ))}
      </div>
    )
  }

  const files = data?.files ?? []

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">My Files</h2>
          <p className="text-muted-foreground mt-1">{files.length} file{files.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['files'] })}
          className="flex items-center gap-2 px-4 py-2 glass rounded-lg hover:bg-secondary transition-colors text-sm"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {files.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="font-semibold text-lg">No files yet</h3>
          <p className="text-muted-foreground text-sm mt-1">Upload your first file to get started.</p>
          <button onClick={() => navigate('/upload')}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors">
            Upload Files
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {files.map((file) => (
              <motion.div
                key={file.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="glass rounded-xl p-4 flex items-center gap-4 hover:border-border transition-all"
              >
                <FileTypeIcon type={file.file_type} />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-medium text-sm truncate">{file.original_name}</p>
                    <StatusBadge status={file.status} />
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span>{formatBytes(file.size_bytes)}</span>
                    <span>•</span>
                    <span className="capitalize">{file.file_type}</span>
                    <span>•</span>
                    <span>{formatRelativeTime(file.created_at)}</span>
                  </div>
                  {file.error_message && (
                    <p className="text-xs text-destructive mt-1 truncate">{file.error_message}</p>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {file.status === 'completed' && (
                    <>
                      <button
                        onClick={() => navigate(`/chat?file=${file.id}`)}
                        className="p-2 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-primary"
                        title="Chat about this file"
                      >
                        <MessageSquare className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => navigate(`/summary/${file.id}`)}
                        className="p-2 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-primary"
                        title="View summary"
                      >
                        <BookOpen className="w-4 h-4" />
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => setDeleteId(file.id)}
                    className="p-2 rounded-lg hover:bg-destructive/10 transition-colors text-muted-foreground hover:text-destructive"
                    title="Delete file"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Delete confirm modal */}
      <AnimatePresence>
        {deleteId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setDeleteId(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass rounded-2xl p-6 max-w-sm w-full space-y-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="font-bold text-lg">Delete File?</h3>
              <p className="text-muted-foreground text-sm">
                This will permanently delete the file and all its AI-generated data. This cannot be undone.
              </p>
              <div className="flex gap-3">
                <button onClick={() => setDeleteId(null)}
                  className="flex-1 py-2 rounded-lg border border-border hover:bg-secondary transition-colors text-sm">
                  Cancel
                </button>
                <button
                  onClick={() => deleteMutation.mutate(deleteId)}
                  disabled={deleteMutation.isPending}
                  className="flex-1 py-2 rounded-lg bg-destructive hover:bg-destructive/90 text-destructive-foreground text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {deleteMutation.isPending ? 'Deleting…' : 'Delete'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
