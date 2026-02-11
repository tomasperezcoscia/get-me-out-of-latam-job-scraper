import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  ExternalLink,
  FileText,
  ShieldCheck,
  Send,
  MapPin,
  Clock,
  Globe,
  StickyNote,
  Tag,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Loader2,
  BookOpen,
  CheckCircle2,
  Circle,
} from 'lucide-react'
import { useJob, useUpdateJobStatus } from '../api/jobs'
import { useApplicationByJob } from '../api/applications'
import { useAnalyzeSkillGaps, useLearningItems, useToggleLearningItem } from '../api/ai'
import type { JobStatus, LearningItem } from '../types'
import { formatDate, relativeTime, scoreColor, cn } from '../lib/utils'
import Badge from '../components/ui/Badge'
import ScoreIndicator from '../components/ui/ScoreIndicator'
import SalaryRange from '../components/ui/SalaryRange'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import CoverLetterModal from '../components/ai/CoverLetterModal'
import ATSCheckModal from '../components/ai/ATSCheckModal'
import ApplyWizard from '../components/ai/ApplyWizard'

const JOB_STATUSES: JobStatus[] = [
  'new',
  'reviewed',
  'applied',
  'rejected',
  'interview',
  'offer',
]

type TabId = 'description' | 'learn'

export default function JobDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: job, isLoading, isError } = useJob(id ?? '')
  const updateStatus = useUpdateJobStatus()

  const [showCoverLetter, setShowCoverLetter] = useState(false)
  const [showATSCheck, setShowATSCheck] = useState(false)
  const [showApplyWizard, setShowApplyWizard] = useState(false)
  const [activeTab, setActiveTab] = useState<TabId>('description')
  const [coverLetterExpanded, setCoverLetterExpanded] = useState(false)
  const [copied, setCopied] = useState(false)

  const isApplied = job?.status === 'applied'
  const { data: application } = useApplicationByJob(id ?? '', isApplied)

  const { data: learningItems } = useLearningItems(id ?? '')
  const analyzeGaps = useAnalyzeSkillGaps()
  const toggleItem = useToggleLearningItem()

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (isError || !job) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Job not found</h2>
        <p className="text-gray-500 mb-6">
          The job you are looking for does not exist or has been removed.
        </p>
        <Link
          to="/jobs"
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Jobs
        </Link>
      </div>
    )
  }

  function handleStatusChange(e: React.ChangeEvent<HTMLSelectElement>) {
    if (!job) return
    updateStatus.mutate({ id: job.id, status: e.target.value })
  }

  const handleCopyCoverLetter = async () => {
    if (!application?.cover_letter) return
    await navigator.clipboard.writeText(application.cover_letter)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleAnalyzeGaps = () => {
    analyzeGaps.mutate(job.id)
  }

  // Group learning items by category
  const grouped: Record<string, LearningItem[]> = {}
  for (const item of learningItems ?? []) {
    if (!grouped[item.category]) grouped[item.category] = []
    grouped[item.category].push(item)
  }
  const totalItems = learningItems?.length ?? 0
  const knownItems = learningItems?.filter((i) => i.is_known).length ?? 0

  return (
    <>
      <div className="flex gap-6">
        {/* Left column -- full job details */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-xl shadow-sm p-6">
            {/* Back link */}
            <Link
              to="/jobs"
              className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-4"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Jobs
            </Link>

            {/* Header */}
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-1">{job.title}</h1>
              <p className="text-lg text-gray-700 font-medium">{job.company}</p>

              <div className="flex flex-wrap items-center gap-3 mt-3 text-sm text-gray-500">
                {job.location && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {job.location}
                  </span>
                )}
                {job.is_remote && (
                  <span className="inline-flex items-center gap-1">
                    <Globe className="h-3.5 w-3.5" />
                    Remote
                  </span>
                )}
                {job.posted_at && (
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    Posted {relativeTime(job.posted_at)}
                    <span className="text-gray-400">({formatDate(job.posted_at)})</span>
                  </span>
                )}
              </div>
            </div>

            {/* Tags */}
            {job.tags && job.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-6">
                {job.tags.map((tag) => (
                  <Badge key={tag} className="bg-blue-50 text-blue-700">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}

            {/* Tabs */}
            <div className="flex border-b mb-6">
              <button
                onClick={() => setActiveTab('description')}
                className={cn(
                  'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
                  activeTab === 'description'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                )}
              >
                Description
              </button>
              <button
                onClick={() => setActiveTab('learn')}
                className={cn(
                  'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-2',
                  activeTab === 'learn'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                )}
              >
                <BookOpen className="h-3.5 w-3.5" />
                Need to Learn
                {totalItems > 0 && (
                  <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                    {knownItems}/{totalItems}
                  </span>
                )}
              </button>
            </div>

            {/* Tab content: Description */}
            {activeTab === 'description' && (
              <>
                <section className="mb-8">
                  <h2 className="text-lg font-semibold text-gray-900 mb-3">Description</h2>
                  <div
                    className="prose max-w-none text-gray-700"
                    dangerouslySetInnerHTML={{ __html: job.description }}
                  />
                </section>

                {job.requirements && (
                  <section className="mb-8">
                    <h2 className="text-lg font-semibold text-gray-900 mb-3">Requirements</h2>
                    <div
                      className="prose max-w-none text-gray-700"
                      dangerouslySetInnerHTML={{ __html: job.requirements }}
                    />
                  </section>
                )}
              </>
            )}

            {/* Tab content: Need to Learn */}
            {activeTab === 'learn' && (
              <div>
                {totalItems === 0 && !analyzeGaps.isPending && (
                  <div className="text-center py-12">
                    <BookOpen className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-sm text-gray-500 mb-4">
                      Analyze this job to identify skills you may need to learn or deepen.
                    </p>
                    <button
                      onClick={handleAnalyzeGaps}
                      disabled={analyzeGaps.isPending}
                      className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
                    >
                      Analyze Skill Gaps
                    </button>
                    {analyzeGaps.isError && (
                      <div className="mt-3 bg-red-50 text-red-700 rounded-lg p-3 text-sm">
                        {analyzeGaps.error?.message || 'Failed to analyze skill gaps'}
                      </div>
                    )}
                  </div>
                )}

                {analyzeGaps.isPending && (
                  <div className="flex flex-col items-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-gray-400 mb-3" />
                    <p className="text-sm text-gray-500">Analyzing skill gaps with Claude...</p>
                  </div>
                )}

                {totalItems > 0 && (
                  <div className="space-y-6">
                    {/* Progress bar */}
                    <div>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-gray-600">Skills covered</span>
                        <span className="font-medium">{knownItems} of {totalItems}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${totalItems > 0 ? (knownItems / totalItems) * 100 : 0}%` }}
                        />
                      </div>
                    </div>

                    {/* Grouped items */}
                    {Object.entries(grouped).map(([category, items]) => (
                      <div key={category}>
                        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
                          {category}
                        </h3>
                        <div className="space-y-1">
                          {items.map((item) => (
                            <label
                              key={item.id}
                              className={cn(
                                'flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors',
                                item.is_known ? 'bg-green-50' : 'bg-gray-50 hover:bg-gray-100'
                              )}
                            >
                              <button
                                onClick={() =>
                                  toggleItem.mutate({ itemId: item.id, isKnown: !item.is_known })
                                }
                                className="mt-0.5 shrink-0"
                              >
                                {item.is_known ? (
                                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                                ) : (
                                  <Circle className="h-5 w-5 text-gray-300" />
                                )}
                              </button>
                              <div className="min-w-0">
                                <p className={cn(
                                  'text-sm font-medium',
                                  item.is_known ? 'text-green-700 line-through' : 'text-gray-900'
                                )}>
                                  {item.skill}
                                </p>
                                <p className={cn(
                                  'text-xs',
                                  item.is_known ? 'text-green-600 line-through' : 'text-gray-500'
                                )}>
                                  {item.detail}
                                </p>
                              </div>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}

                    {/* Re-analyze button */}
                    <button
                      onClick={handleAnalyzeGaps}
                      disabled={analyzeGaps.isPending}
                      className="text-sm text-gray-500 hover:text-gray-700 underline"
                    >
                      Re-analyze skill gaps
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar */}
        <div className="w-80 shrink-0">
          <div className="sticky top-6 space-y-4">
            {/* Score card */}
            <div className="bg-white rounded-xl shadow-sm p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
                Match Score
              </h3>
              <div className="flex items-center gap-3">
                <ScoreIndicator score={job.match_score} size="lg" />
                <div>
                  <p className={cn('text-2xl font-bold', scoreColor(job.match_score))}>
                    {job.match_score !== null ? Math.round(job.match_score) : '--'}
                  </p>
                  <p className="text-xs text-gray-400">out of 100</p>
                </div>
              </div>
            </div>

            {/* Salary card */}
            <div className="bg-white rounded-xl shadow-sm p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
                Salary
              </h3>
              <SalaryRange
                min={job.salary_min}
                max={job.salary_max}
                currency={job.salary_currency}
              />
            </div>

            {/* Status selector */}
            <div className="bg-white rounded-xl shadow-sm p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
                Status
              </h3>
              <select
                value={job.status}
                onChange={handleStatusChange}
                disabled={updateStatus.isPending}
                className={cn(
                  'w-full rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium',
                  'focus:outline-none focus:ring-2 focus:ring-gray-900/10',
                  'disabled:opacity-60 disabled:cursor-not-allowed',
                  'capitalize'
                )}
              >
                {JOB_STATUSES.map((s) => (
                  <option key={s} value={s} className="capitalize">
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Cover Letter Sent (for applied jobs) */}
            {isApplied && application?.cover_letter && (
              <div className="bg-white rounded-xl shadow-sm p-4">
                <button
                  onClick={() => setCoverLetterExpanded(!coverLetterExpanded)}
                  className="flex items-center justify-between w-full"
                >
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    <FileText className="h-3 w-3 inline mr-1" />
                    Cover Letter Sent
                  </h3>
                  {coverLetterExpanded ? (
                    <ChevronUp className="h-4 w-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-gray-400" />
                  )}
                </button>
                {coverLetterExpanded && (
                  <div className="mt-3">
                    <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto">
                      {application.cover_letter}
                    </div>
                    <button
                      onClick={handleCopyCoverLetter}
                      className="flex items-center gap-1.5 mt-2 text-xs text-gray-500 hover:text-gray-700"
                    >
                      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                      {copied ? 'Copied!' : 'Copy to clipboard'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Tags */}
            {job.tags && job.tags.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm p-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
                  <Tag className="h-3 w-3 inline mr-1" />
                  Tags
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {job.tags.map((tag) => (
                    <Badge key={tag} className="bg-gray-100 text-gray-700">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Source */}
            {job.source && (
              <div className="bg-white rounded-xl shadow-sm p-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
                  Source
                </h3>
                <Badge className="bg-indigo-50 text-indigo-700">{job.source}</Badge>
                {job.scraped_at && (
                  <p className="text-xs text-gray-400 mt-2">
                    Scraped {relativeTime(job.scraped_at)}
                  </p>
                )}
              </div>
            )}

            {/* Action buttons */}
            <div className="bg-white rounded-xl shadow-sm p-4 space-y-2">
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800 transition-colors"
              >
                <ExternalLink className="h-4 w-4" />
                Open Job URL
              </a>

              <button
                type="button"
                onClick={() => setShowCoverLetter(true)}
                className="flex items-center justify-center gap-2 w-full rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <FileText className="h-4 w-4" />
                Generate Cover Letter
              </button>

              <button
                type="button"
                onClick={() => setShowATSCheck(true)}
                className="flex items-center justify-center gap-2 w-full rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <ShieldCheck className="h-4 w-4" />
                ATS Check
              </button>

              <button
                type="button"
                onClick={() => setShowApplyWizard(true)}
                className="flex items-center justify-center gap-2 w-full rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <Send className="h-4 w-4" />
                Apply
              </button>
            </div>

            {/* Notes */}
            {job.notes && (
              <div className="bg-white rounded-xl shadow-sm p-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
                  <StickyNote className="h-3 w-3 inline mr-1" />
                  Notes
                </h3>
                <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700 whitespace-pre-wrap">
                  {job.notes}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI modals */}
      <CoverLetterModal
        open={showCoverLetter}
        onClose={() => setShowCoverLetter(false)}
        jobId={job.id}
        jobTitle={`${job.title} at ${job.company}`}
      />

      <ATSCheckModal
        open={showATSCheck}
        onClose={() => setShowATSCheck(false)}
        jobId={job.id}
        jobTitle={`${job.title} at ${job.company}`}
      />

      <ApplyWizard
        open={showApplyWizard}
        onClose={() => setShowApplyWizard(false)}
        jobId={job.id}
        jobTitle={`${job.title} at ${job.company}`}
      />
    </>
  )
}
