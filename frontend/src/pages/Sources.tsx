import { useState } from 'react'
import { Database, Loader2, Play, CheckCircle, AlertCircle } from 'lucide-react'
import { useSources, useCollectSource, useCollectAll } from '../api/sources'
import type { CollectResult } from '../types'
import Badge from '../components/ui/Badge'
import LoadingSpinner from '../components/ui/LoadingSpinner'

const TIER_1_SOURCES = new Set([
  'remoteok',
  'arbeitnow',
  'himalayas',
  'weworkremotely',
  'remotive',
])

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

export default function Sources() {
  const { data: sources, isLoading, error } = useSources()
  const collectSource = useCollectSource()
  const collectAll = useCollectAll()

  const [results, setResults] = useState<Record<string, CollectResult>>({})
  const [collectingSource, setCollectingSource] = useState<string | null>(null)
  const [collectAllResults, setCollectAllResults] = useState<CollectResult[] | null>(null)

  async function handleCollectSource(source: string) {
    setCollectingSource(source)
    try {
      const result = await collectSource.mutateAsync(source)
      setResults((prev) => ({ ...prev, [source]: result }))
    } finally {
      setCollectingSource(null)
    }
  }

  async function handleCollectAll() {
    setCollectAllResults(null)
    try {
      const allResults = await collectAll.mutateAsync()
      setCollectAllResults(allResults)
      const mapped: Record<string, CollectResult> = {}
      for (const r of allResults) {
        mapped[r.source] = r
      }
      setResults((prev) => ({ ...prev, ...mapped }))
    } catch {
      // Error handled by mutation state
    }
  }

  if (isLoading) return <LoadingSpinner />

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-red-500">
        <AlertCircle className="h-10 w-10 mb-3" />
        <p className="text-lg font-medium">Failed to load sources</p>
        <p className="text-sm text-gray-500 mt-1">
          {error instanceof Error ? error.message : 'Unknown error'}
        </p>
      </div>
    )
  }

  const totalFetched = collectAllResults?.reduce((sum, r) => sum + r.fetched, 0) ?? 0
  const totalInserted = collectAllResults?.reduce((sum, r) => sum + r.inserted, 0) ?? 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Database className="h-7 w-7 text-gray-700" />
          <h1 className="text-2xl font-bold text-gray-900">Data Sources</h1>
        </div>
        <button
          onClick={handleCollectAll}
          disabled={collectAll.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {collectAll.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Collect All
        </button>
      </div>

      {/* Collect All Results Banner */}
      {collectAllResults && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
          <div className="flex items-start gap-3">
            <CheckCircle className="h-5 w-5 text-emerald-600 mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold text-emerald-800">
                Collection complete: Fetched {totalFetched}, Inserted {totalInserted} new jobs
              </p>
              <ul className="mt-2 space-y-1 text-sm text-emerald-700">
                {collectAllResults.map((r) => (
                  <li key={r.source}>
                    <span className="font-medium">{capitalize(r.source)}</span>
                    {' -- '}Fetched {r.fetched}, Inserted {r.inserted}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {collectAll.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />
            <p className="text-sm font-medium text-red-800">
              Collection failed:{' '}
              {collectAll.error instanceof Error
                ? collectAll.error.message
                : 'Unknown error'}
            </p>
          </div>
        </div>
      )}

      {/* Source Cards Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sources?.map((source) => {
          const isTier1 = TIER_1_SOURCES.has(source)
          const result = results[source]
          const isCollecting = collectingSource === source

          return (
            <div
              key={source}
              className="rounded-xl bg-white p-5 shadow-sm border border-gray-100"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {capitalize(source)}
                  </h3>
                  {isTier1 ? (
                    <Badge className="bg-emerald-100 text-emerald-700">
                      Free API
                    </Badge>
                  ) : (
                    <Badge className="bg-amber-100 text-amber-700">
                      API Key
                    </Badge>
                  )}
                </div>

                <button
                  onClick={() => handleCollectSource(source)}
                  disabled={isCollecting || collectAll.isPending}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isCollecting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  Collect
                </button>
              </div>

              {result && (
                <p className="mt-3 text-sm font-medium text-emerald-600">
                  Fetched {result.fetched}, Inserted {result.inserted}
                </p>
              )}
            </div>
          )
        })}
      </div>

      {sources && sources.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <Database className="h-10 w-10 mx-auto mb-3 text-gray-300" />
          <p className="text-lg font-medium">No sources configured</p>
          <p className="text-sm mt-1">
            Check your backend configuration to register data sources.
          </p>
        </div>
      )}
    </div>
  )
}
