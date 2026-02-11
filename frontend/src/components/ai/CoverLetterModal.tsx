import { useState } from 'react'
import { Loader2, Copy, Check, FileText } from 'lucide-react'
import { useGenerateCoverLetter } from '../../api/ai'
import Modal from '../ui/Modal'

interface CoverLetterModalProps {
  open: boolean
  onClose: () => void
  jobId: string
  jobTitle: string
}

export default function CoverLetterModal({ open, onClose, jobId, jobTitle }: CoverLetterModalProps) {
  const [coverLetter, setCoverLetter] = useState('')
  const [copied, setCopied] = useState(false)
  const generate = useGenerateCoverLetter()

  const handleGenerate = () => {
    generate.mutate(jobId, {
      onSuccess: (data) => setCoverLetter(data.cover_letter),
    })
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(coverLetter)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleClose = () => {
    setCoverLetter('')
    generate.reset()
    onClose()
  }

  return (
    <Modal open={open} onClose={handleClose} title="Generate Cover Letter">
      <p className="text-sm text-gray-500 mb-4">{jobTitle}</p>

      {!coverLetter && !generate.isPending && (
        <div className="text-center py-8">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500 mb-4">
            Generate a personalized cover letter using AI
          </p>
          <button
            onClick={handleGenerate}
            className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
          >
            Generate Cover Letter
          </button>
        </div>
      )}

      {generate.isPending && (
        <div className="flex flex-col items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mb-3" />
          <p className="text-sm text-gray-500">Generating with Claude...</p>
        </div>
      )}

      {generate.isError && (
        <div className="bg-red-50 text-red-700 rounded-lg p-3 text-sm mb-4">
          {generate.error?.message || 'Failed to generate cover letter'}
        </div>
      )}

      {coverLetter && (
        <div>
          <textarea
            value={coverLetter}
            onChange={(e) => setCoverLetter(e.target.value)}
            rows={14}
            className="w-full border rounded-lg p-3 text-sm font-mono resize-y focus:outline-none focus:ring-2 focus:ring-gray-900"
          />
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copied ? 'Copied!' : 'Copy to Clipboard'}
            </button>
            <button
              onClick={handleGenerate}
              disabled={generate.isPending}
              className="px-4 py-2 border rounded-lg text-sm font-medium hover:bg-gray-50"
            >
              Regenerate
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}
