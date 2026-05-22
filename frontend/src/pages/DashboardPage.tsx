import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Upload, MessageSquare, FileText, Sparkles,
  TrendingUp, Activity, ArrowRight, ShieldCheck, Play
} from 'lucide-react'
import { filesApi, chatApi } from '@/services/api'
import { useAuthStore } from '@/store'
import { formatBytes, formatRelativeTime } from '@/lib/utils'

export default function DashboardPage() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)

  // Fetch stats from files and chat queries
  const { data: filesData, isLoading: filesLoading } = useQuery({
    queryKey: ['files'],
    queryFn: () => filesApi.list(1, 100),
  })

  const { data: chatData, isLoading: chatLoading } = useQuery({
    queryKey: ['chats'],
    queryFn: () => chatApi.history(1),
  })

  const totalFiles = filesData?.total ?? 0
  const totalChats = chatData?.total ?? 0
  const recentFiles = filesData?.files?.slice(0, 3) ?? []

  // Count file types
  const pdfCount = filesData?.files?.filter(f => f.file_type === 'pdf').length ?? 0
  const mediaCount = filesData?.files?.filter(f => f.file_type === 'audio' || f.file_type === 'video').length ?? 0

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1 }
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      {/* Welcome Banner */}
      <motion.div
        variants={itemVariants}
        className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-violet-600/20 via-indigo-600/10 to-transparent border border-violet-500/20 p-6 md:p-8"
      >
        <div className="absolute right-8 top-1/2 -translate-y-1/2 w-48 h-48 bg-primary/10 rounded-full blur-3xl -z-10 pointer-events-none" />
        <div className="max-w-2xl space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/15 text-primary text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" /> Workspace Ready
          </div>
          <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight">
            Welcome back, <span className="gradient-text">{user?.full_name || user?.username || 'User'}</span>
          </h2>
          <p className="text-muted-foreground text-sm md:text-base max-w-md">
            Query your documents, transcribe media files, and extract insights instantly with your RAG-powered companion.
          </p>
        </div>
      </motion.div>

      {/* Metrics Section */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Uploaded Files', value: filesLoading ? '...' : totalFiles, icon: FileText, desc: `${pdfCount} PDF / ${mediaCount} Audio-Video`, color: 'text-violet-400 bg-violet-400/10 border-violet-400/20' },
          { label: 'AI Chat Sessions', value: chatLoading ? '...' : totalChats, icon: MessageSquare, desc: 'Interactive Q&A', color: 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20' },
          { label: 'PDF Documents', value: filesLoading ? '...' : pdfCount, icon: ShieldCheck, desc: 'Vector indexed text', color: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20' },
          { label: 'Audio & Video Files', value: filesLoading ? '...' : mediaCount, icon: Play, desc: 'Whisper transcripts ready', color: 'text-amber-400 bg-amber-400/10 border-amber-400/20' }
        ].map((stat, i) => {
          const Icon = stat.icon
          return (
            <div key={i} className="glass rounded-2xl p-5 hover:border-border/80 transition-all group">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground font-medium">{stat.label}</span>
                <div className={`p-2 rounded-xl border ${stat.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4 space-y-1">
                <span className="text-3xl font-bold tracking-tight">{stat.value}</span>
                <p className="text-xs text-muted-foreground">{stat.desc}</p>
              </div>
            </div>
          )
        })}
      </motion.div>

      {/* Quick Actions & Recent Files */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <motion.div variants={itemVariants} className="lg:col-span-1 space-y-4 flex flex-col justify-between">
          <div className="glass rounded-3xl p-6 space-y-4 h-full flex flex-col justify-between">
            <div>
              <h3 className="font-bold text-lg">Quick Actions</h3>
              <p className="text-xs text-muted-foreground">Perform tasks instantly</p>
            </div>
            <div className="space-y-3 my-4">
              <button
                onClick={() => navigate('/upload')}
                className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-all font-semibold text-sm group"
              >
                <span className="flex items-center gap-2">
                  <Upload className="w-4 h-4" /> Upload Files
                </span>
                <ArrowRight className="w-4 h-4 -translate-x-1 group-hover:translate-x-0 transition-transform" />
              </button>

              <button
                onClick={() => navigate('/chat')}
                className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-secondary border border-border/40 hover:bg-secondary/80 transition-all text-foreground font-semibold text-sm group"
              >
                <span className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-violet-400" /> Start AI Chat
                </span>
                <ArrowRight className="w-4 h-4 -translate-x-1 group-hover:translate-x-0 transition-transform" />
              </button>

              <button
                onClick={() => navigate('/files')}
                className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-secondary border border-border/40 hover:bg-secondary/80 transition-all text-foreground font-semibold text-sm group"
              >
                <span className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-400" /> View Repository
                </span>
                <ArrowRight className="w-4 h-4 -translate-x-1 group-hover:translate-x-0 transition-transform" />
              </button>
            </div>
            <div className="p-4 rounded-2xl border border-border/40 bg-card/30 flex items-center gap-3 text-xs text-muted-foreground">
              <Activity className="w-4 h-4 text-primary flex-shrink-0" />
              <span>Vector store indexes are created automatically in the background.</span>
            </div>
          </div>
        </motion.div>

        {/* Recent Files */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <div className="glass rounded-3xl p-6 h-full flex flex-col justify-between">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-lg">Recently Processed</h3>
                <p className="text-xs text-muted-foreground">Your latest uploads</p>
              </div>
              <button
                onClick={() => navigate('/files')}
                className="text-xs text-primary font-semibold flex items-center gap-1 hover:underline"
              >
                See All <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-3 flex-1">
              {filesLoading ? (
                [...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 rounded-2xl border border-border/30 bg-muted/40 animate-pulse" />
                ))
              ) : recentFiles.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                  <FileText className="w-8 h-8 opacity-40 mb-2" />
                  <p className="text-xs">No files available yet</p>
                </div>
              ) : (
                recentFiles.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 rounded-2xl border border-border/30 hover:border-border/80 transition-all bg-card/20"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={`p-2 rounded-xl flex-shrink-0 ${
                        file.file_type === 'pdf' ? 'bg-red-500/10 text-red-400' :
                        file.file_type === 'audio' ? 'bg-green-500/10 text-green-400' :
                        'bg-blue-500/10 text-blue-400'
                      }`}>
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-semibold text-sm truncate">{file.original_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatBytes(file.size_bytes)} • {formatRelativeTime(file.created_at)}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={() => navigate(`/chat?file=${file.id}`)}
                      disabled={file.status !== 'completed'}
                      className="px-3 py-1.5 rounded-xl border border-border/40 text-xs font-semibold hover:bg-secondary hover:text-foreground transition-all disabled:opacity-40"
                    >
                      Query AI
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}
