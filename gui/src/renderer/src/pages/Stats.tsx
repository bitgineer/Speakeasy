/**
 * Stats Page
 * 
 * Shows transcription statistics and analytics.
 */

import { useEffect, useState, useMemo } from 'react'
import { useHistoryStore } from '../store'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  color?: string
}

function StatCard({ title, value, subtitle, icon, color = 'accent' }: StatCardProps): JSX.Element {
  const colorClasses = {
    accent: 'text-[var(--color-accent)]',
    success: 'text-[var(--color-success)]',
    warning: 'text-[var(--color-warning)]',
    info: 'text-[var(--color-info)]'
  }
  
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--color-text-muted)] font-medium">{title}</p>
          <p className={`text-3xl font-bold mt-2 ${colorClasses[color as keyof typeof colorClasses]}`}>{value}</p>
          {subtitle && (
            <p className="text-xs text-[var(--color-text-muted)] mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-[var(--color-bg-tertiary)] ${colorClasses[color as keyof typeof colorClasses]}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}

function formatDuration(ms: number): string {
  if (ms === 0) return '0s'
  
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    return `${days}d ${hours % 24}h`
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

function formatDate(dateString: string | null): string {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export default function Stats(): JSX.Element {
  const { stats, items, fetchStats, fetchHistory, isLoading } = useHistoryStore()
  const [refreshing, setRefreshing] = useState(false)
  
  useEffect(() => {
    fetchStats()
    // Also fetch some history items for word count estimation
    fetchHistory()
  }, [fetchStats, fetchHistory])
  
  const handleRefresh = async () => {
    setRefreshing(true)
    await Promise.all([fetchStats(), fetchHistory()])
    setRefreshing(false)
  }
  
  // Calculate additional stats from items (word counts, records)
  // Note: Activity counts (today/week/month) now come from backend stats API
  const extendedStats = useMemo(() => {
    if (!items.length) {
      return {
        totalWords: 0,
        avgWordsPerTranscription: 0,
        avgDuration: 0,
        longestTranscription: null as typeof items[0] | null,
        shortestTranscription: null as typeof items[0] | null
      }
    }
    
    const totalWords = items.reduce((acc, item) => {
      return acc + item.text.split(/\s+/).filter(Boolean).length
    }, 0)
    
    const avgWordsPerTranscription = Math.round(totalWords / items.length)
    
    const totalDuration = items.reduce((acc, item) => acc + item.duration_ms, 0)
    const avgDuration = Math.round(totalDuration / items.length)
    
    const sortedByLength = [...items].sort((a, b) => b.text.length - a.text.length)
    const longestTranscription = sortedByLength[0] || null
    const shortestTranscription = sortedByLength[sortedByLength.length - 1] || null
    
    return {
      totalWords,
      avgWordsPerTranscription,
      avgDuration,
      longestTranscription,
      shortestTranscription
    }
  }, [items])
  
  if (isLoading && !stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
      </div>
    )
  }
  
  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Statistics</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Overview of your transcription activity</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] rounded-lg transition-colors border border-[var(--color-border)] disabled:opacity-50"
        >
          <svg 
            className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
      
      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Total Transcriptions"
          value={stats?.total_count ?? 0}
          subtitle="All time"
          color="accent"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />
        
        <StatCard
          title="Total Recording Time"
          value={formatDuration(stats?.total_duration_ms ?? 0)}
          subtitle="Combined duration"
          color="success"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        
        <StatCard
          title="Words Transcribed"
          value={extendedStats.totalWords.toLocaleString()}
          subtitle={`~${extendedStats.avgWordsPerTranscription} per transcription`}
          color="info"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
          }
        />
        
        <StatCard
          title="Avg. Duration"
          value={formatDuration(extendedStats.avgDuration)}
          subtitle="Per transcription"
          color="warning"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          }
        />
      </div>
      
      {/* Activity Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Recent Activity */}
        <section className="card p-5">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Recent Activity</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2 border-b border-[var(--color-border)]">
              <span className="text-sm text-[var(--color-text-secondary)]">Today</span>
              <span className="text-lg font-semibold text-[var(--color-accent)]">{stats?.today_count ?? 0}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-[var(--color-border)]">
              <span className="text-sm text-[var(--color-text-secondary)]">This Week</span>
              <span className="text-lg font-semibold text-[var(--color-accent)]">{stats?.this_week_count ?? 0}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-[var(--color-text-secondary)]">This Month</span>
              <span className="text-lg font-semibold text-[var(--color-accent)]">{stats?.this_month_count ?? 0}</span>
            </div>
          </div>
        </section>
        
        {/* Timeline */}
        <section className="card p-5">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Timeline</h2>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-[var(--color-success-muted)] flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-[var(--color-success)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-[var(--color-text-secondary)]">First Transcription</p>
                <p className="text-xs text-[var(--color-text-muted)]">{formatDate(stats?.first_transcription ?? null)}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-[var(--color-info-muted)] flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-[var(--color-info)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-[var(--color-text-secondary)]">Latest Transcription</p>
                <p className="text-xs text-[var(--color-text-muted)]">{formatDate(stats?.last_transcription ?? null)}</p>
              </div>
            </div>
          </div>
        </section>
      </div>
      
      {/* Records Section */}
      {(extendedStats.longestTranscription || extendedStats.shortestTranscription) && (
        <section className="card p-5">
          <h2 className="text-base font-medium mb-4 text-[var(--color-text-primary)]">Records</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {extendedStats.longestTranscription && (
              <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-4 border border-[var(--color-border)]">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-4 h-4 text-[var(--color-success)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                  <span className="text-sm font-medium text-[var(--color-text-secondary)]">Longest Transcription</span>
                </div>
                <p className="text-2xl font-bold text-[var(--color-success)]">
                  {extendedStats.longestTranscription.text.split(/\s+/).filter(Boolean).length} words
                </p>
                <p className="text-xs text-[var(--color-text-muted)] mt-1 line-clamp-2">
                  "{extendedStats.longestTranscription.text.slice(0, 100)}..."
                </p>
              </div>
            )}
            
            {extendedStats.shortestTranscription && extendedStats.shortestTranscription !== extendedStats.longestTranscription && (
              <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-4 border border-[var(--color-border)]">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-4 h-4 text-[var(--color-warning)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                  <span className="text-sm font-medium text-[var(--color-text-secondary)]">Shortest Transcription</span>
                </div>
                <p className="text-2xl font-bold text-[var(--color-warning)]">
                  {extendedStats.shortestTranscription.text.split(/\s+/).filter(Boolean).length} words
                </p>
                <p className="text-xs text-[var(--color-text-muted)] mt-1 line-clamp-2">
                  "{extendedStats.shortestTranscription.text}"
                </p>
              </div>
            )}
          </div>
        </section>
      )}
      
      {/* Empty State */}
      {(!stats || stats.total_count === 0) && (
        <div className="card p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 text-[var(--color-text-disabled)]">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-[var(--color-text-secondary)] mb-1">No data yet</h3>
          <p className="text-[var(--color-text-muted)] text-sm">
            Start transcribing to see your statistics here
          </p>
        </div>
      )}
    </div>
  )
}
