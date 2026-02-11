import { useState } from 'react'
import { Loader2, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { useATSCheck } from '../../api/ai'
import type { ATSResult } from '../../types'
import Modal from '../ui/Modal'

interface ATSCheckModalProps {
  open: boolean
  onClose: () => void
  jobId: string
  jobTitle: string
}

export default function ATSCheckModal({ open, onClose, jobId, jobTitle }: ATSCheckModalProps) {
  const [resumeText, setResumeText] = useState('')
  const [result, setResult] = useState<ATSResult | null>(null)
  const atsCheck = useATSCheck()

  const handleCheck = () => {
    atsCheck.mutate(
      { jobId, resumeText },
      { onSuccess: (data) => setResult(data) },
    )
  }

  const handleClose = () => {
    setResult(null)
    atsCheck.reset()
    onClose()
  }

  return (
    <Modal open={open} onClose={handleClose} title="ATS Compatibility Check">
      <p className="text-sm text-gray-500 mb-4">{jobTitle}</p>

      {!result && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Paste your resume text
          </label>
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            rows={10}
            placeholder="Paste your resume content here..."
            className="w-full border rounded-lg p-3 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-gray-900"
          />
          <button
            onClick={handleCheck}
            disabled={!resumeText.trim() || atsCheck.isPending}
            className="mt-3 flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
          >
            {atsCheck.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Run ATS Check
          </button>
        </div>
      )}

      {atsCheck.isError && (
        <div className="bg-red-50 text-red-700 rounded-lg p-3 text-sm mt-3">
          {atsCheck.error?.message || 'ATS check failed'}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {/* Score */}
          <div className="flex items-center gap-3">
            <div
              className={`text-3xl font-bold ${
                (result.ats_score ?? 0) >= 70
                  ? 'text-emerald-600'
                  : (result.ats_score ?? 0) >= 40
                    ? 'text-amber-500'
                    : 'text-red-500'
              }`}
            >
              {result.ats_score ?? 'N/A'}
            </div>
            <span className="text-sm text-gray-500">ATS Score</span>
          </div>

          {/* Present Keywords */}
          {result.present_keywords?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 flex items-center gap-1 mb-2">
                <CheckCircle className="h-4 w-4 text-emerald-500" />
                Present Keywords
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {result.present_keywords.map((kw) => (
                  <span key={kw} className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-xs">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Missing Keywords */}
          {result.missing_keywords?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 flex items-center gap-1 mb-2">
                <XCircle className="h-4 w-4 text-red-500" />
                Missing Keywords
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {result.missing_keywords.map((kw) => (
                  <span key={kw} className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Suggestions */}
          {result.suggestions?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 flex items-center gap-1 mb-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Suggestions
              </h4>
              <ul className="space-y-1">
                {result.suggestions.map((s, i) => (
                  <li key={i} className="text-sm text-gray-600 pl-5 relative before:content-[''] before:absolute before:left-1.5 before:top-2 before:h-1 before:w-1 before:rounded-full before:bg-gray-400">
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={() => { setResult(null); atsCheck.reset() }}
            className="mt-2 px-4 py-2 border rounded-lg text-sm font-medium hover:bg-gray-50"
          >
            Check Again
          </button>
        </div>
      )}
    </Modal>
  )
}
