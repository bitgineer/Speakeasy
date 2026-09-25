/**
 * Stats Page
 *
 * Shows transcription statistics and analytics.
 */

import { useEffect, useState, useMemo, type ReactNode } from 'react'
import {
  ArrowDown,
  ArrowUp,
  BarChart3,
  Check,
  Clock,
  FileText,
  Languages,
  RefreshCw,
  Zap
} from 'lucide-react'
import { useHistoryStore } from '../store'
import { Button } from '../components/ui/button'

type StatTone = 'accent' | 'success' | 'warning'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  tone: StatTone
  icon: ReactNode
}

function StatCard({ title, value, subtitle, tone, icon }: StatCardProps): JSX.Element {
  return (
    <article className="card stat-card">
      <div>
        <p className="stat-label">{title}</p>
        <p className="stat-value" data-tone={tone}>
          {value}
        </p>
        {subtitle && <p className="stat-subtitle">{subtitle}</p>}
      </div>
      <span className="stat-icon" data-tone={tone} aria-hidden="true">
        {icon}
      </span>
    </article>
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
        longestTranscription: null as (typeof items)[0] | null,
        shortestTranscription: null as (typeof items)[0] | null
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
      <div className="workspace stat-loading">
        <span className="spinner animate-spin" role="status" aria-label="Loading statistics" />
      </div>
    )
  }

  return (
    <div className="workspace">
      <header className="page-head">
        <div>
          <p className="eyebrow">Activity / overview</p>
          <h1>Statistics</h1>
          <p className="page-subtitle">Overview of your transcription activity.</p>
        </div>
        <div className="page-actions">
          <Button variant="secondary" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw
              size={14}
              className={refreshing ? 'animate-spin' : undefined}
              aria-hidden="true"
            />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
      </header>

      <div className="stat-grid">
        <StatCard
          title="Total transcriptions"
          value={stats?.total_count ?? 0}
          subtitle="All time"
          tone="accent"
          icon={<FileText size={18} strokeWidth={1.75} />}
        />
        <StatCard
          title="Total recording time"
          value={formatDuration(stats?.total_duration_ms ?? 0)}
          subtitle="Combined duration"
          tone="success"
          icon={<Clock size={18} strokeWidth={1.75} />}
        />
        <StatCard
          title="Words transcribed"
          value={extendedStats.totalWords.toLocaleString()}
          subtitle={`~${extendedStats.avgWordsPerTranscription} per transcription`}
          tone="accent"
          icon={<Languages size={18} strokeWidth={1.75} />}
        />
        <StatCard
          title="Average duration"
          value={formatDuration(extendedStats.avgDuration)}
          subtitle="Per transcription"
          tone="warning"
          icon={<Zap size={18} strokeWidth={1.75} />}
        />
      </div>

      <div className="stat-panels">
        <section className="card stat-panel" aria-labelledby="activity-title">
          <h2 id="activity-title">Recent activity</h2>
          <dl className="stat-rows">
            <div className="stat-row">
              <dt>Today</dt>
              <dd>{stats?.today_count ?? 0}</dd>
            </div>
            <div className="stat-row">
              <dt>This week</dt>
              <dd>{stats?.this_week_count ?? 0}</dd>
            </div>
            <div className="stat-row">
              <dt>This month</dt>
              <dd>{stats?.this_month_count ?? 0}</dd>
            </div>
          </dl>
        </section>

        <section className="card stat-panel" aria-labelledby="timeline-title">
          <h2 id="timeline-title">Timeline</h2>
          <div className="stat-entries">
            <div className="stat-entry">
              <span className="stat-icon" data-tone="success" aria-hidden="true">
                <Clock size={15} strokeWidth={2} />
              </span>
              <div>
                <p className="stat-entry-label">First transcription</p>
                <p className="stat-entry-meta">{formatDate(stats?.first_transcription ?? null)}</p>
              </div>
            </div>
            <div className="stat-entry">
              <span className="stat-icon" data-tone="accent" aria-hidden="true">
                <Check size={15} strokeWidth={2} />
              </span>
              <div>
                <p className="stat-entry-label">Latest transcription</p>
                <p className="stat-entry-meta">{formatDate(stats?.last_transcription ?? null)}</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      {(extendedStats.longestTranscription || extendedStats.shortestTranscription) && (
        <section className="card stat-panel" aria-labelledby="records-title">
          <h2 id="records-title">Records</h2>
          <div className="stat-record-grid">
            {extendedStats.longestTranscription && (
              <article className="stat-record">
                <p className="stat-label">
                  <ArrowUp size={14} strokeWidth={2} aria-hidden="true" />
                  Longest transcription
                </p>
                <p className="stat-record-value" data-tone="success">
                  {extendedStats.longestTranscription.text.split(/\s+/).filter(Boolean).length} words
                </p>
                <p className="stat-record-quote">
                  &ldquo;{extendedStats.longestTranscription.text.slice(0, 100)}...&rdquo;
                </p>
              </article>
            )}

            {extendedStats.shortestTranscription &&
              extendedStats.shortestTranscription !== extendedStats.longestTranscription && (
                <article className="stat-record">
                  <p className="stat-label">
                    <ArrowDown size={14} strokeWidth={2} aria-hidden="true" />
                    Shortest transcription
                  </p>
                  <p className="stat-record-value" data-tone="warning">
                    {extendedStats.shortestTranscription.text.split(/\s+/).filter(Boolean).length}{' '}
                    words
                  </p>
                  <p className="stat-record-quote">
                    &ldquo;{extendedStats.shortestTranscription.text}&rdquo;
                  </p>
                </article>
              )}
          </div>
        </section>
      )}

      {(!stats || stats.total_count === 0) && (
        <div className="card empty-state empty-state-centered">
          <BarChart3 className="empty-state-icon" size={40} strokeWidth={1.25} aria-hidden="true" />
          <h3>No data yet</h3>
          <p>Start transcribing to see your statistics here.</p>
        </div>
      )}
    </div>
  )
}
