import { useState } from 'react'
import { Loader2, CheckCircle2, XCircle, SkipForward, Rocket } from 'lucide-react'
import { useMassApply, useMassApplyProgress } from '../../api/applications'
import type { Job, MassApplyJobResult } from '../../types'
import Modal from '../ui/Modal'
import ScoreIndicator from '../ui/ScoreIndicator'

interface MassApplyModalProps {
  open: boolean
  onClose: () => void
  jobs: Job[]
  onDone: () => void
}

type Phase = 'confirm' | 'processing' | 'summary'

function ResultIcon({ status }: { status: MassApplyJobResult['status'] }) {
  if (status === 'done') return <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
  if (status === 'failed') return <XCircle className="h-4 w-4 text-red-500 shrink-0" />
  return <SkipForward className="h-4 w-4 text-gray-400 shrink-0" />
}

export default function MassApplyModal({ open, onClose, jobs, onDone }: MassApplyModalProps) {
  const [phase, setPhase] = useState<Phase>('confirm')
  const [taskId, setTaskId] = useState<string | null>(null)

  const massApply = useMassApply()
  const { data: progress } = useMassApplyProgress(taskId)

  const isProcessing = phase === 'processing'
  const isDone = progress?.done ?? false

  // Move to summary when done
  if (isProcessing && isDone) {
    setPhase('summary')
  }

  const handleStart = () => {
    const ids = jobs.map((j) => j.id)
    massApply.mutate(ids, {
      onSuccess: (data) => {
        setTaskId(data.task_id)
        setPhase('processing')
      },
    })
  }

  const handleClose = () => {
    if (phase === 'summary') onDone()
    setPhase('confirm')
    setTaskId(null)
    massApply.reset()
    onClose()
  }

  const processed = (progress?.completed ?? 0) + (progress?.failed ?? 0)
  const total = progress?.total ?? jobs.length
  const pct = total > 0 ? Math.round((processed / total) * 100) : 0

  return (
    <Modal open={open} onClose={handleClose} title="Mass Apply">
      {/* Confirm Phase */}
      {phase === 'confirm' && (
        <div>
          <p className="text-sm text-gray-500 mb-4">
            Apply to {jobs.length} job{jobs.length !== 1 ? 's' : ''} with AI-generated cover letters.
            This will run in the background.
          </p>

          <div className="max-h-60 overflow-y-auto border rounded-lg divide-y">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center gap-3 px-3 py-2">
                <ScoreIndicator score={job.match_score} size="sm" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{job.title}</p>
                  <p className="text-xs text-gray-500 truncate">{job.company}</p>
                </div>
              </div>
            ))}
          </div>

          {massApply.isError && (
            <div className="mt-3 bg-red-50 text-red-700 rounded-lg p-3 text-sm">
              {massApply.error?.message || 'Failed to start mass apply'}
            </div>
          )}

          <div className="flex gap-2 mt-4">
            <button
              onClick={handleStart}
              disabled={massApply.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-60"
            >
              {massApply.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Rocket className="h-4 w-4" />
              )}
              Start Mass Apply
            </button>
            <button
              onClick={handleClose}
              className="px-4 py-2 border rounded-lg text-sm font-medium hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Processing Phase */}
      {phase === 'processing' && (
        <div>
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-600">
                {progress?.current_job || 'Starting...'}
              </span>
              <span className="font-medium">{processed}/{total}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gray-900 h-2 rounded-full transition-all duration-300"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>

          <div className="max-h-60 overflow-y-auto border rounded-lg divide-y">
            {progress?.results.map((r, i) => (
              <div key={i} className="flex items-center gap-2 px-3 py-2 text-sm">
                <ResultIcon status={r.status} />
                <span className="flex-1 truncate">{r.job_title}</span>
                {r.error && (
                  <span className="text-xs text-red-500 truncate max-w-[200px]">{r.error}</span>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 mt-4 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Processing... Do not close this dialog.
          </div>
        </div>
      )}

      {/* Summary Phase */}
      {phase === 'summary' && progress && (
        <div>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-green-700">
                {progress.results.filter((r) => r.status === 'done').length}
              </p>
              <p className="text-xs text-green-600">Applied</p>
            </div>
            <div className="bg-red-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-red-700">{progress.failed}</p>
              <p className="text-xs text-red-600">Failed</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-gray-700">
                {progress.results.filter((r) => r.status === 'skipped').length}
              </p>
              <p className="text-xs text-gray-600">Skipped</p>
            </div>
          </div>

          <div className="max-h-48 overflow-y-auto border rounded-lg divide-y">
            {progress.results.map((r, i) => (
              <div key={i} className="flex items-center gap-2 px-3 py-2 text-sm">
                <ResultIcon status={r.status} />
                <span className="flex-1 truncate">{r.job_title}</span>
              </div>
            ))}
          </div>

          <button
            onClick={handleClose}
            className="mt-4 w-full px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
          >
            Done
          </button>
        </div>
      )}
    </Modal>
  )
}
