import { useState, useCallback, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Search, Rocket } from 'lucide-react'
import { useJobs } from '../api/jobs'
import { useDebounce } from '../hooks/useDebounce'
import { useJobSelection } from '../hooks/useJobSelection'
import { relativeTime, statusColor } from '../lib/utils'
import type { JobFilters } from '../types'
import Badge from '../components/ui/Badge'
import ScoreIndicator from '../components/ui/ScoreIndicator'
import SalaryRange from '../components/ui/SalaryRange'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import EmptyState from '../components/ui/EmptyState'
import Pagination from '../components/ui/Pagination'
import MassApplyModal from '../components/ai/MassApplyModal'

const STATUSES = ['new', 'reviewed', 'applied', 'rejected', 'interview', 'offer'] as const

const SOURCES = [
  'remoteok',
  'arbeitnow',
  'himalayas',
  'weworkremotely',
  'remotive',
  'jooble',
  'adzuna',
  'serpapi',
] as const

const PAGE_SIZE = 20

export default function Jobs() {
  const [searchParams, setSearchParams] = useSearchParams()

  // Derive initial state from URL search params
  const [search, setSearch] = useState(searchParams.get('search') ?? '')
  const [status, setStatus] = useState(searchParams.get('status') ?? '')
  const [source, setSource] = useState(searchParams.get('source') ?? '')
  const [minScore, setMinScore] = useState(searchParams.get('min_score') ?? '')
  const [minSalary, setMinSalary] = useState(searchParams.get('min_salary') ?? '')
  const [skip, setSkip] = useState(Number(searchParams.get('skip') ?? 0))
  const [showMassApply, setShowMassApply] = useState(false)

  const debouncedSearch = useDebounce(search, 300)
  const { selected, toggle, selectAll, clearAll, isSelected, count } = useJobSelection()

  // Build filters object
  const filters: JobFilters = {
    skip,
    limit: PAGE_SIZE,
    ...(debouncedSearch && { search: debouncedSearch }),
    ...(status && { status }),
    ...(source && { source }),
    ...(minScore && { min_score: Number(minScore) }),
    ...(minSalary && { min_salary: Number(minSalary) }),
  }

  const { data, isLoading } = useJobs(filters)

  // Sync filters to URL search params
  useEffect(() => {
    const params = new URLSearchParams()
    if (debouncedSearch) params.set('search', debouncedSearch)
    if (status) params.set('status', status)
    if (source) params.set('source', source)
    if (minScore) params.set('min_score', minScore)
    if (minSalary) params.set('min_salary', minSalary)
    if (skip > 0) params.set('skip', String(skip))
    setSearchParams(params, { replace: true })
  }, [debouncedSearch, status, source, minScore, minSalary, skip, setSearchParams])

  // Reset to first page when filters change
  const handleFilterChange = useCallback(() => {
    setSkip(0)
  }, [])

  const jobs = data?.items ?? []
  const total = data?.total ?? 0
  const pageJobIds = jobs.map((j) => j.id)
  const allPageSelected = pageJobIds.length > 0 && pageJobIds.every((id) => isSelected(id))

  const handleSelectAllPage = () => {
    if (allPageSelected) {
      clearAll()
    } else {
      selectAll(pageJobIds)
    }
  }

  const selectedJobs = jobs.filter((j) => selected.has(j.id))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
        {total > 0 && (
          <Badge className="bg-gray-200 text-gray-700">{total}</Badge>
        )}
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search */}
          <div className="relative lg:col-span-2">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                handleFilterChange()
              }}
              placeholder="Search jobs..."
              className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Status */}
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value)
              handleFilterChange()
            }}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>

          {/* Source */}
          <select
            value={source}
            onChange={(e) => {
              setSource(e.target.value)
              handleFilterChange()
            }}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Sources</option>
            {SOURCES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>

          {/* Min Score & Min Salary in a single row on smallest breakpoints */}
          <div className="flex gap-2">
            <input
              type="number"
              value={minScore}
              onChange={(e) => {
                setMinScore(e.target.value)
                handleFilterChange()
              }}
              placeholder="Min score"
              step={5}
              min={0}
              max={100}
              className="w-1/2 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="number"
              value={minSalary}
              onChange={(e) => {
                setMinSalary(e.target.value)
                handleFilterChange()
              }}
              placeholder="Min salary"
              step={10000}
              min={0}
              className="w-1/2 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Job List */}
      {isLoading ? (
        <LoadingSpinner />
      ) : jobs.length === 0 ? (
        <EmptyState title="No jobs found" message="Try adjusting your filters." />
      ) : (
        <div className="space-y-3">
          {/* Select all row */}
          <div className="flex items-center gap-3 px-2">
            <input
              type="checkbox"
              checked={allPageSelected}
              onChange={handleSelectAllPage}
              className="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-gray-900"
            />
            <span className="text-xs text-gray-500">
              {allPageSelected ? 'Deselect all on page' : 'Select all on page'}
            </span>
          </div>

          {jobs.map((job) => (
            <div
              key={job.id}
              className="flex items-center gap-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
            >
              {/* Checkbox */}
              <div className="pl-4 py-4">
                <input
                  type="checkbox"
                  checked={isSelected(job.id)}
                  onChange={(e) => {
                    e.stopPropagation()
                    toggle(job.id)
                  }}
                  className="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-gray-900"
                />
              </div>

              {/* Job card content (link) */}
              <Link
                to={`/jobs/${job.id}`}
                className="flex-1 flex items-center gap-4 p-4 pl-0 min-w-0"
              >
                {/* Score */}
                <ScoreIndicator score={job.match_score} size="md" />

                {/* Main info */}
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-gray-900 truncate">
                      {job.title}
                    </span>
                    <span className="text-gray-500 text-sm truncate">
                      {job.company}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <SalaryRange
                      min={job.salary_min}
                      max={job.salary_max}
                      currency={job.salary_currency}
                    />

                    {job.source && (
                      <Badge className="bg-gray-100 text-gray-600">
                        {job.source}
                      </Badge>
                    )}

                    <Badge className={statusColor(job.status)}>
                      {job.status}
                    </Badge>

                    {job.tags?.slice(0, 3).map((tag) => (
                      <Badge key={tag} className="bg-blue-50 text-blue-700">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Timestamp */}
                <span className="text-xs text-gray-400 whitespace-nowrap shrink-0">
                  {relativeTime(job.posted_at ?? job.scraped_at)}
                </span>
              </Link>
            </div>
          ))}

          <Pagination
            total={total}
            skip={skip}
            limit={PAGE_SIZE}
            onChange={setSkip}
          />
        </div>
      )}

      {/* Floating action bar */}
      {count > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-gray-900 text-white rounded-xl shadow-2xl px-6 py-3 flex items-center gap-4">
          <span className="text-sm font-medium">
            {count} job{count !== 1 ? 's' : ''} selected
          </span>
          <button
            onClick={() => setShowMassApply(true)}
            className="flex items-center gap-2 px-4 py-2 bg-white text-gray-900 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors"
          >
            <Rocket className="h-4 w-4" />
            Mass Apply
          </button>
          <button
            onClick={clearAll}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Clear
          </button>
        </div>
      )}

      {/* Mass Apply Modal */}
      <MassApplyModal
        open={showMassApply}
        onClose={() => setShowMassApply(false)}
        jobs={selectedJobs.length > 0 ? selectedJobs : Array.from(selected).map((id) => jobs.find((j) => j.id === id)).filter(Boolean) as typeof jobs}
        onDone={() => {
          clearAll()
          // Data will auto-refresh via TanStack Query invalidation
        }}
      />
    </div>
  )
}
