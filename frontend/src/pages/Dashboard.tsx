import { Link } from 'react-router-dom'
import { Briefcase, Sparkles, Send, DollarSign, Play, Target, Loader2 } from 'lucide-react'
import { useStats } from '../api/stats'
import { useJobs } from '../api/jobs'
import { useCollectAll } from '../api/sources'
import { useScoreJobs } from '../api/ai'
import { formatSalary } from '../lib/utils'
import ScoreIndicator from '../components/ui/ScoreIndicator'
import SalaryRange from '../components/ui/SalaryRange'
import LoadingSpinner from '../components/ui/LoadingSpinner'

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useStats()
  const { data: topJobs, isLoading: topJobsLoading } = useJobs({
    status: 'new',
    limit: 5,
  })

  const collectAll = useCollectAll()
  const scoreJobs = useScoreJobs()

  if (statsLoading) return <LoadingSpinner />

  const totalJobs = stats?.total_jobs ?? 0
  const newJobs = stats?.by_status?.new ?? 0
  const applied = stats?.by_status?.applied ?? 0
  const avgSalary = stats?.avg_salary_min
    ? formatSalary(stats.avg_salary_min, null)
    : '--'

  const cards = [
    { label: 'Total Jobs', value: totalJobs, icon: Briefcase, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'New Jobs', value: newJobs, icon: Sparkles, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Applied', value: applied, icon: Send, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Avg Salary', value: avgSalary, icon: DollarSign, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  ]

  // Source breakdown sorted by count descending
  const sourceEntries = stats?.by_source
    ? Object.entries(stats.by_source).sort((a, b) => b[1] - a[1])
    : []
  const maxSourceCount = sourceEntries.length > 0 ? sourceEntries[0][1] : 1

  // Top matches from the new jobs query, sorted by match_score
  const topMatches = (topJobs?.items ?? [])
    .slice()
    .sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <div
              key={card.label}
              className="bg-white rounded-xl shadow-sm p-5 flex items-center gap-4"
            >
              <div className={`${card.bg} ${card.color} p-3 rounded-lg`}>
                <Icon className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              </div>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Source Breakdown */}
        <div className="bg-white rounded-xl shadow-sm p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sources</h2>
          {sourceEntries.length === 0 ? (
            <p className="text-sm text-gray-400">No data yet.</p>
          ) : (
            <div className="space-y-3">
              {sourceEntries.map(([source, count]) => (
                <div key={source} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700 font-medium capitalize">{source}</span>
                    <span className="text-gray-500">{count}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all duration-300"
                      style={{ width: `${(count / maxSourceCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Matches */}
        <div className="bg-white rounded-xl shadow-sm p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Matches</h2>
          {topJobsLoading ? (
            <LoadingSpinner />
          ) : topMatches.length === 0 ? (
            <p className="text-sm text-gray-400">
              No scored jobs yet. Run scoring to see matches.
            </p>
          ) : (
            <div className="space-y-2">
              {topMatches.map((job) => (
                <Link
                  key={job.id}
                  to={`/jobs/${job.id}`}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <ScoreIndicator score={job.match_score} size="sm" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">
                      {job.title}
                    </p>
                    <p className="text-xs text-gray-500 truncate">{job.company}</p>
                  </div>
                  <SalaryRange
                    min={job.salary_min}
                    max={job.salary_max}
                    currency={job.salary_currency}
                  />
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-sm p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => collectAll.mutate()}
            disabled={collectAll.isPending}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            {collectAll.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {collectAll.isPending ? 'Collecting...' : 'Collect All'}
          </button>
          <button
            onClick={() => scoreJobs.mutate()}
            disabled={scoreJobs.isPending}
            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            {scoreJobs.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Target className="h-4 w-4" />
            )}
            {scoreJobs.isPending ? 'Scoring...' : 'Score Unscored'}
          </button>
        </div>
        {collectAll.isSuccess && (
          <p className="mt-3 text-sm text-green-600">
            Collection complete -- {collectAll.data.reduce((s, r) => s + r.inserted, 0)} new
            jobs inserted.
          </p>
        )}
        {collectAll.isError && (
          <p className="mt-3 text-sm text-red-600">
            Collection failed. Check server logs.
          </p>
        )}
        {scoreJobs.isSuccess && (
          <p className="mt-3 text-sm text-green-600">
            Scored {scoreJobs.data.scored} jobs.
          </p>
        )}
        {scoreJobs.isError && (
          <p className="mt-3 text-sm text-red-600">
            Scoring failed. Check server logs.
          </p>
        )}
      </div>
    </div>
  )
}
