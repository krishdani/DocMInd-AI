import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ArrowLeft, BookOpen, List, Target, Clock, Download, MessageSquare, Loader2 } from 'lucide-react'
import { summaryApi, filesApi, timestampApi } from '@/services/api'
import { useState } from 'react'
import { formatTimestamp, cn } from '@/lib/utils'

function SectionCard({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-5 h-5 text-primary" />
        <h3 className="font-semibold">{title}</h3>
      </div>
      {children}
    </motion.div>
  )
}

export default function SummaryPage() {
  const { fileId } = useParams<{ fileId: string }>()
  const navigate = useNavigate()
  const [tsQuery, setTsQuery] = useState('')
  const [tsResults, setTsResults] = useState<any[]>([])
  const [tsLoading, setTsLoading] = useState(false)

  const { data: file } = useQuery({
    queryKey: ['file', fileId],
    queryFn: () => filesApi.get(Number(fileId)),
    enabled: !!fileId,
  })

  const { data: summary, isLoading } = useQuery({
    queryKey: ['summary', fileId],
    queryFn: () => summaryApi.get(Number(fileId)),
    enabled: !!fileId,
  })

  const searchTimestamps = async () => {
    if (!tsQuery.trim() || !fileId) return
    setTsLoading(true)
    try {
      const res = await timestampApi.search({ query: tsQuery, file_id: Number(fileId) })
      setTsResults(res.results)
    } finally {
      setTsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <span className="ml-3 text-muted-foreground">Generating summary…</span>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/files')}
          className="p-2 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-2xl font-bold">Summary</h2>
          <p className="text-muted-foreground text-sm">{file?.original_name}</p>
        </div>
        <div className="ml-auto flex gap-2">
          <button
            onClick={() => navigate(`/chat`)}
            className="flex items-center gap-2 px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 rounded-lg text-sm transition-colors"
          >
            <MessageSquare className="w-4 h-4" /> Chat About This
          </button>
        </div>
      </div>

      {summary ? (
        <div className="space-y-4">
          {/* Short summary */}
          {summary.short_summary && (
            <SectionCard title="Quick Summary" icon={BookOpen}>
              <p className="text-foreground/90 leading-relaxed">{summary.short_summary}</p>
            </SectionCard>
          )}

          {/* Detailed summary */}
          {summary.detailed_summary && (
            <SectionCard title="Detailed Summary" icon={BookOpen}>
              <p className="text-foreground/80 leading-relaxed whitespace-pre-wrap">{summary.detailed_summary}</p>
            </SectionCard>
          )}

          {/* Bullet points */}
          {summary.bullet_points && summary.bullet_points.length > 0 && (
            <SectionCard title="Key Points" icon={List}>
              <ul className="space-y-2">
                {summary.bullet_points.map((point, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="w-5 h-5 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center flex-shrink-0 mt-0.5">{i + 1}</span>
                    {point}
                  </li>
                ))}
              </ul>
            </SectionCard>
          )}

          {/* Key topics with timestamps */}
          {summary.key_topics && summary.key_topics.length > 0 && (
            <SectionCard title="Key Topics" icon={Target}>
              <div className="grid sm:grid-cols-2 gap-3">
                {summary.key_topics.map((topic, i) => (
                  <div key={i} className="p-3 bg-secondary/50 rounded-xl border border-border/50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm">{topic.topic}</span>
                      <span className="text-xs text-muted-foreground">
                        {Math.round(topic.confidence * 100)}%
                      </span>
                    </div>
                    {topic.start_time != null && (
                      <span className="inline-flex items-center gap-1 text-xs text-primary">
                        <Clock className="w-3 h-3" />{formatTimestamp(topic.start_time)}
                      </span>
                    )}
                    {topic.snippet && <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{topic.snippet}</p>}
                  </div>
                ))}
              </div>
            </SectionCard>
          )}

          {/* Timestamp search (audio/video) */}
          {file?.file_type !== 'pdf' && (
            <SectionCard title="Find in Transcript" icon={Clock}>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder='e.g. "Where was React discussed?"'
                  value={tsQuery}
                  onChange={(e) => setTsQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && searchTimestamps()}
                  className="flex-1 px-4 py-2.5 bg-input border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
                <button
                  onClick={searchTimestamps}
                  disabled={tsLoading}
                  className="px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  {tsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
                </button>
              </div>
              {tsResults.length > 0 && (
                <div className="mt-4 space-y-2">
                  {tsResults.map((r, i) => (
                    <div key={i} className="p-3 bg-secondary/50 rounded-xl border border-border/50">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-primary">
                          {formatTimestamp(r.start_time)} – {formatTimestamp(r.end_time)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {Math.round(r.confidence * 100)}% match
                        </span>
                      </div>
                      <p className="text-sm text-foreground/80 line-clamp-3">{r.snippet}</p>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>
          )}
        </div>
      ) : (
        <div className="glass rounded-2xl p-12 text-center">
          <p className="text-muted-foreground">Could not generate summary. Make sure the file is fully processed.</p>
        </div>
      )}
    </div>
  )
}
