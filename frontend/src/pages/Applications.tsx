import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Send,
  MessageSquare,
  Video,
  Code,
  Trophy,
  XCircle,
  ExternalLink,
  StickyNote,
  ChevronDown,
  ChevronUp,
  Loader2,
} from 'lucide-react'
import { useApplicationsPipeline, useUpdateApplication } from '../api/applications'
import type { ApplicationWithJob, ApplicationStatusType } from '../types'
import { formatDate, relativeTime, cn } from '../lib/utils'
import Badge from '../components/ui/Badge'
import ScoreIndicator from '../components/ui/ScoreIndicator'
import LoadingSpinner from '../components/ui/LoadingSpinner'

const COLUMNS: { key: ApplicationStatusType; label: string; icon: typeof Send; color: string }[] = [
  { key: 'applied', label: 'Applied', icon: Send, color: 'border-blue-400' },
  { key: 'responded', label: 'Responded', icon: MessageSquare, color: 'border-purple-400' },
  { key: 'interviewing', label: 'Interviewing', icon: Video, color: 'border-amber-400' },
  { key: 'technical_test', label: 'Tech Test', icon: Code, color: 'border-orange-400' },
  { key: 'offer', label: 'Offer', icon: Trophy, color: 'border-emerald-400' },
  { key: 'rejected', label: 'Rejected', icon: XCircle, color: 'border-red-400' },
]

function appStatusColor(status: string): string {
  const map: Record<string, string> = {
    applied: 'bg-blue-100 text-blue-800',
    responded: 'bg-purple-100 text-purple-800',
    interviewing: 'bg-amber-100 text-amber-800',
    technical_test: 'bg-orange-100 text-orange-800',
    offer: 'bg-emerald-100 text-emerald-800',
    rejected: 'bg-red-100 text-red-800',
  }
  return map[status] || 'bg-gray-100 text-gray-800'
}

interface AppCardProps {
  app: ApplicationWithJob
  onStatusChange: (id: string, status: string) => void
  isUpdating: boolean
}

function AppCard({ app, onStatusChange, isUpdating }: AppCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [notes, setNotes] = useState(app.notes || '')
  const [showNotes, setShowNotes] = useState(false)
  const updateApp = useUpdateApplication()

  const saveNotes = () => {
    updateApp.mutate({ id: app.id, notes })
    setShowNotes(false)
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-3 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start gap-2">
        <ScoreIndicator score={app.job_score} size="sm" />
        <div className="flex-1 min-w-0">
          <Link
            to={`/jobs/${app.job_id}`}
            className="text-sm font-medium text-gray-900 hover:text-indigo-600 line-clamp-2"
          >
            {app.job_title}
          </Link>
          <p className="text-xs text-gray-500 truncate">{app.job_company}</p>
        </div>
      </div>

      <div className="mt-2 flex items-center gap-2 text-xs text-gray-400">
        <span>Applied {relativeTime(app.applied_at)}</span>
      </div>

      {/* Status selector */}
      <div className="mt-2">
        <select
          value={app.status}
          onChange={(e) => onStatusChange(app.id, e.target.value)}
          disabled={isUpdating}
          className={cn(
            'w-full rounded border border-gray-200 px-2 py-1 text-xs font-medium',
            'focus:outline-none focus:ring-1 focus:ring-gray-300',
            'disabled:opacity-60',
          )}
        >
          {COLUMNS.map((col) => (
            <option key={col.key} value={col.key}>
              {col.label}
            </option>
          ))}
        </select>
      </div>

      {/* Quick actions */}
      <div className="mt-2 flex items-center gap-1">
        <a
          href={app.job_url}
          target="_blank"
          rel="noopener noreferrer"
          className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
          title="Open job URL"
        >
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
        <button
          onClick={() => setShowNotes(!showNotes)}
          className={cn(
            'p-1 rounded hover:bg-gray-100',
            app.notes ? 'text-amber-500' : 'text-gray-400 hover:text-gray-600'
          )}
          title="Notes"
        >
          <StickyNote className="h-3.5 w-3.5" />
        </button>
        {app.cover_letter && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
            title="Cover letter"
          >
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        )}
      </div>

      {/* Notes editor */}
      {showNotes && (
        <div className="mt-2">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add notes about this application..."
            rows={3}
            className="w-full text-xs border rounded-lg p-2 focus:outline-none focus:ring-1 focus:ring-gray-300 resize-none"
          />
          <div className="flex justify-end gap-1 mt-1">
            <button
              onClick={() => setShowNotes(false)}
              className="px-2 py-0.5 text-xs text-gray-500 hover:text-gray-700"
            >
              Cancel
            </button>
            <button
              onClick={saveNotes}
              disabled={updateApp.isPending}
              className="px-2 py-0.5 text-xs bg-gray-900 text-white rounded hover:bg-gray-800 disabled:opacity-60"
            >
              {updateApp.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Save'}
            </button>
          </div>
        </div>
      )}

      {/* Expanded cover letter */}
      {expanded && app.cover_letter && (
        <div className="mt-2 rounded bg-gray-50 p-2 text-xs text-gray-600 whitespace-pre-wrap max-h-32 overflow-y-auto">
          {app.cover_letter}
        </div>
      )}
    </div>
  )
}

export default function Applications() {
  const { data: apps, isLoading, error } = useApplicationsPipeline()
  const updateApp = useUpdateApplication()

  const handleStatusChange = (id: string, status: string) => {
    updateApp.mutate({ id, status })
  }

  if (isLoading) return <LoadingSpinner />

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-red-500">
        <p className="text-lg font-medium">Failed to load applications</p>
      </div>
    )
  }

  const allApps = apps ?? []

  // Group by status
  const grouped: Record<string, ApplicationWithJob[]> = {}
  for (const col of COLUMNS) {
    grouped[col.key] = []
  }
  for (const app of allApps) {
    if (grouped[app.status]) {
      grouped[app.status].push(app)
    } else {
      grouped['applied'].push(app)
    }
  }

  if (allApps.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Send className="h-7 w-7 text-gray-700" />
          <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
        </div>
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Send className="h-12 w-12 text-gray-300 mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-1">No applications yet</h2>
          <p className="text-sm text-gray-500 mb-4">
            Apply to jobs from the{' '}
            <Link to="/jobs" className="text-indigo-600 hover:underline">Jobs page</Link>
            {' '}to start tracking them here.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Send className="h-7 w-7 text-gray-700" />
          <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
          <Badge className="bg-gray-100 text-gray-700">{allApps.length}</Badge>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-6 gap-3">
        {COLUMNS.map((col) => {
          const Icon = col.icon
          const count = grouped[col.key].length
          return (
            <div
              key={col.key}
              className={cn(
                'rounded-lg bg-white border-t-4 p-3 shadow-sm',
                col.color,
              )}
            >
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-gray-500" />
                <span className="text-xs font-medium text-gray-500 uppercase">{col.label}</span>
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-1">{count}</p>
            </div>
          )
        })}
      </div>

      {/* Pipeline columns */}
      <div className="grid grid-cols-6 gap-3 items-start">
        {COLUMNS.map((col) => {
          const Icon = col.icon
          const items = grouped[col.key]
          return (
            <div key={col.key} className="space-y-2">
              <div className={cn(
                'flex items-center gap-2 px-2 py-1.5 rounded-lg border-l-4',
                col.color,
                'bg-gray-50',
              )}>
                <Icon className="h-4 w-4 text-gray-600" />
                <span className="text-sm font-semibold text-gray-700">{col.label}</span>
                {items.length > 0 && (
                  <Badge className={appStatusColor(col.key)}>{items.length}</Badge>
                )}
              </div>
              <div className="space-y-2">
                {items.map((app) => (
                  <AppCard
                    key={app.id}
                    app={app}
                    onStatusChange={handleStatusChange}
                    isUpdating={updateApp.isPending}
                  />
                ))}
                {items.length === 0 && (
                  <div className="text-center py-6 text-xs text-gray-400">
                    No applications
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
