import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, X, CheckCircle2, AlertCircle, FileText, Music, Video, Loader2 } from 'lucide-react'
import { filesApi } from '@/services/api'
import { formatBytes, cn } from '@/lib/utils'
import type { UploadProgress } from '@/types'

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'audio/mpeg': ['.mp3'],
  'audio/wav': ['.wav'],
  'audio/ogg': ['.ogg'],
  'video/mp4': ['.mp4'],
  'video/quicktime': ['.mov'],
  'video/webm': ['.webm'],
  'video/x-msvideo': ['.avi'],
}

function FileIcon({ type }: { type: string }) {
  if (type.includes('pdf')) return <FileText className="w-8 h-8 text-red-400" />
  if (type.includes('audio')) return <Music className="w-8 h-8 text-green-400" />
  return <Video className="w-8 h-8 text-blue-400" />
}

export default function UploadPage() {
  const [uploads, setUploads] = useState<UploadProgress[]>([])

  const updateUpload = (idx: number, patch: Partial<UploadProgress>) =>
    setUploads((prev) => prev.map((u, i) => (i === idx ? { ...u, ...patch } : u)))

  const onDrop = useCallback(async (accepted: File[]) => {
    const newUploads: UploadProgress[] = accepted.map((f) => ({ file: f, progress: 0, status: 'uploading' }))
    setUploads((prev) => [...prev, ...newUploads])
    const startIdx = uploads.length

    await Promise.all(
      accepted.map(async (file, i) => {
        const idx = startIdx + i
        try {
          await filesApi.upload(file, (pct) => updateUpload(idx, { progress: pct }))
          updateUpload(idx, { status: 'done', progress: 100 })
        } catch (err: any) {
          updateUpload(idx, {
            status: 'error',
            error: err.response?.data?.detail ?? 'Upload failed',
          })
        }
      }),
    )
  }, [uploads.length])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: 500 * 1024 * 1024,
  })

  const removeUpload = (idx: number) => setUploads((prev) => prev.filter((_, i) => i !== idx))

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold">Upload Files</h2>
        <p className="text-muted-foreground mt-1">Upload PDFs, audio, or video files to analyze with AI.</p>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200',
          isDragActive
            ? 'border-primary bg-primary/5 scale-[1.01] dropzone-active'
            : 'border-border hover:border-primary/50 hover:bg-secondary/30',
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div className={cn(
            'w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-200',
            isDragActive ? 'bg-primary/20' : 'bg-secondary',
          )}>
            <Upload className={cn('w-8 h-8 transition-colors', isDragActive ? 'text-primary' : 'text-muted-foreground')} />
          </div>
          <div>
            <p className="text-lg font-semibold">
              {isDragActive ? 'Drop files here!' : 'Drag & drop files here'}
            </p>
            <p className="text-muted-foreground text-sm mt-1">or click to browse</p>
          </div>
          <div className="flex flex-wrap gap-2 justify-center">
            {['PDF', 'MP3', 'WAV', 'MP4', 'MOV', 'WEBM'].map((ext) => (
              <span key={ext} className="px-2.5 py-1 bg-secondary rounded-full text-xs font-medium text-muted-foreground">
                .{ext.toLowerCase()}
              </span>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">Max file size: 500MB</p>
        </div>
      </div>

      {/* Upload queue */}
      <AnimatePresence>
        {uploads.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
            <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">Upload Queue</h3>
            {uploads.map((u, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="glass rounded-xl p-4 flex items-center gap-4"
              >
                <FileIcon type={u.file.type} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{u.file.name}</p>
                  <p className="text-xs text-muted-foreground">{formatBytes(u.file.size)}</p>
                  {u.status === 'uploading' && (
                    <div className="mt-2">
                      <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-primary rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${u.progress}%` }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">{u.progress}%</p>
                    </div>
                  )}
                  {u.status === 'error' && (
                    <p className="text-xs text-destructive mt-1">{u.error}</p>
                  )}
                  {u.status === 'done' && (
                    <p className="text-xs text-green-400 mt-1">Processing queued…</p>
                  )}
                </div>
                <div className="flex-shrink-0">
                  {u.status === 'uploading' && <Loader2 className="w-5 h-5 text-primary animate-spin" />}
                  {u.status === 'done' && <CheckCircle2 className="w-5 h-5 text-green-400" />}
                  {u.status === 'error' && <AlertCircle className="w-5 h-5 text-destructive" />}
                  {u.status !== 'uploading' && (
                    <button onClick={() => removeUpload(i)} className="ml-2 text-muted-foreground hover:text-foreground">
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
